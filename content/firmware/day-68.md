# firmware — Day 68

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** The first step is to quantify the problem rather than assume it: measure the actual interrupt rate, the worst-case ISR execution time, and the CPU headroom left for everything else. If the ISR is genuinely the bottleneck, there are a few standard levers, and the right one depends on what the peripheral actually needs.

The most common fix is to make the ISR do the absolute minimum — acknowledge the interrupt, move a word or a pointer into a buffer, and return — and push all real work into a deferred context (a work queue, a bottom-half thread, or a task notification). This keeps interrupt latency bounded and lets the scheduler decide when the heavier processing runs. If even the minimal ISR is too expensive at the peak rate, the next lever is DMA: let the peripheral write directly into memory and only interrupt on a half-buffer or full-buffer boundary, which collapses thousands of per-sample interrupts into a handful of block interrupts. That is usually the correct answer for streaming peripherals like ADCs, SPI slaves, or UARTs at high baud.

If the rate is still too high — for example, a sensor that genuinely produces data faster than the CPU can consume it — then the design itself is wrong and the honest answer is to reduce the data rate at the source (decimate, average, or configure the peripheral for a lower output rate), or to accept that some samples will be dropped and design the algorithm to tolerate that. A firmware engineer should be willing to say "we cannot service this rate with this CPU, here are the options" rather than silently dropping data.

A secondary consideration is interrupt priority and nesting. If the fast peripheral is high priority and preempts everything, it can starve lower-priority interrupts and cause subtle timing failures elsewhere. Setting priorities so that the fast ISR is short and high-priority, while slower work is deferred to lower-priority contexts, keeps the whole system predictable.

**Possible follow-ups:**
- How would you measure the actual ISR execution time and interrupt rate on a running target without perturbing the system?
- If DMA is not available on that peripheral, what other techniques could reduce the effective interrupt rate?

## Q2: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core issue is that an edge on a GPIO line is a claim, not a fact — the peripheral is asserting "data is ready," but electrical noise, a slow-rising signal, or a marginal pull-up can produce an edge that does not correspond to a real event. The firmware has to treat the edge as a hint and validate the data before acting on it.

The first line of defense is at the hardware/configuration level: enable a small digital filter or debounce on the input if the MCU supports it, or add an RC filter externally. This is often the cheapest and most reliable fix, and it should be considered before adding software complexity. If the glitch is a genuine electrical issue, no amount of software will fully compensate.

In firmware, the pattern is: on the edge, do not immediately read and trust the data. Instead, read the peripheral's own status register or a validity flag, and only accept the sample if the peripheral confirms it has new data. Many sensors expose a "data ready" bit or a status register that is authoritative; the GPIO edge is just a wake-up. If the peripheral has no such flag, then validate the data itself — check a CRC, a range, or a sequence number — and discard samples that fail. A spurious edge then produces a discarded sample rather than a corrupted reading.

There is also a timing angle: if the glitch occurs during a known noisy window (for example, right after a motor or radio turns on), the firmware can mask or ignore the input during that window, or re-read after a short settling delay. This is a form of temporal filtering that complements the electrical filtering.

Finally, the design should make the failure observable. If spurious edges are being discarded, that should be counted and logged, because a rising count is a signal that the hardware is marginal and needs attention — it is not something to silently swallow.

**Possible follow-ups:**
- How would you distinguish a spurious edge from a genuine but very short data-ready pulse?
- If the peripheral has no status register and no CRC, what other validation could you apply to the sample?

## Q3: How would you approach deciding what belongs in a bootloader versus what belongs in the application, for a device that must support field updates?

**Answer:** The guiding principle is that the bootloader should be as small, simple, and hard to break as possible, because it is the one piece of code that must always work — if it fails, the device is bricked and there is no recovery path. Everything that can be moved into the application should be, because the application is what gets updated and what is allowed to have bugs.

Concretely, the bootloader's job is narrow: verify the integrity of the application image (CRC, signature, or hash), decide which bank to boot, jump to the application, and provide a minimal recovery path if the application is invalid. It should not contain business logic, communication stacks beyond what is strictly needed to receive an update, or anything that changes frequently. The smaller the bootloader, the easier it is to audit and the less likely it is to need updating itself.

The application owns everything else: the update protocol, the decision to initiate an update, the download and staging of the new image, and the request to the bootloader to switch banks. A common pattern is that the application downloads the new image into the inactive bank, validates it, sets a flag, and then triggers a reset; the bootloader reads the flag, verifies the new image, and boots it. If verification fails, the bootloader falls back to the known-good bank.

There are gray areas. Communication drivers are a classic one: the bootloader needs *some* way to receive an image if the application is corrupt, but duplicating the full application's comms stack into the bootloader bloats it and creates two copies to maintain. The usual resolution is a minimal, dedicated recovery channel in the bootloader (often a simple UART or USB DFU path) that is separate from the application's normal comms, and is only used when the application cannot boot.

The other consideration is security. If the device requires a secure boot chain, the root of trust and signature verification must live in the bootloader, because the application cannot be trusted to verify itself. That is a case where the bootloader legitimately grows, but it should still be kept as minimal as the security requirements allow.

**Possible follow-ups:**
- How would you handle the case where the bootloader itself needs to be updated?
- What would you put in the bootloader to support recovery if the application is corrupt and the normal comms channel is unavailable?

## Q4: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** Stack sizing is one of those areas where "it works in testing" is not evidence of correctness, because stack overflow often manifests as corruption of an adjacent thread's stack or a hard fault far from the actual cause. The approach should be empirical, not guessed.

The starting point is to understand what actually consumes stack: local variables (especially large buffers and structs passed by value), the call depth of the deepest path through the code, and the context-save overhead of the architecture (which can be significant on Cortex-M with FPU context). Interrupt handlers that run on the thread's stack — which is common on some configurations — also add to the peak. A thread that calls into a library with deep call chains, or that uses `printf`-style formatting, can consume far more than the naive estimate.

The practical method is to start with a generous estimate, then measure. Zephyr provides stack analysis tooling: the `k_thread_stack_space_get()` API returns the unused stack, and the kernel can be configured to paint the stack with a known pattern so that high-water-mark analysis is possible. Running the system through its worst-case paths — not just the happy path — and then reading the high-water mark gives a real number. The rule of thumb is to leave a safety margin (often 25–50% of the observed peak) for paths that were not exercised, and to re-measure after any significant change.

For verification, the strongest approach is to enable stack sentinel checking (`CONFIG_STACK_SENTINEL`) and stack overflow detection in development builds, so that an overflow is caught immediately rather than corrupting memory silently. In production, the sentinel may be disabled for performance, but the sizing should have been validated in development with it enabled. Some teams also add a periodic check that the high-water mark has not moved beyond a threshold, and log or assert if it does — this catches regressions introduced by later code changes.

The honest answer is that stack sizing is never "done" — it is a property that must be re-validated whenever the code changes, and the tooling should make that re-validation cheap.

**Possible follow-ups:**
- How would you handle a thread whose worst-case stack usage depends on data received at runtime, such as a parser with variable-depth recursion?
- What is the difference between stack sentinel checking and stack overflow detection in Zephyr, and when would you use each?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it relies on a global variable to communicate between two threads without any synchronization. They argue that the variable is just a flag and "it's only one byte, so it's atomic." How would you guide them?

**Answer:** The first thing is to take the concern seriously and not dismiss it as pedantry — the engineer's intuition is partly right (a single-byte write is often atomic at the hardware level on many architectures), but the conclusion is wrong for reasons that are worth walking through carefully, because understanding *why* is what makes the lesson stick.

The key points to explain are: first, atomicity of the write is not the same as visibility. Without a memory barrier or a volatile-qualified access, the compiler is free to cache the value in a register, reorder the read relative to other operations, or eliminate the read entirely if it believes the value cannot change. The thread may never see the update, even though the write happened. Second, even with `volatile`, the compiler is prevented from optimizing the access away, but the CPU and memory system can still reorder — `volatile` is not a synchronization primitive. Third, the flag is almost certainly not the only shared state: the flag usually signals that *other* data is ready, and that data is not atomic, so the flag alone does not make the communication safe.

The constructive path is to show the correct alternatives and let the engineer choose based on the situation. For a simple flag between an ISR and a thread, a `k_sem` or `k_event` is the idiomatic Zephyr answer, and it is not expensive. For a flag between two threads, an atomic variable (`atomic_t` with `atomic_set`/`atomic_get`) or a mutex-protected flag is appropriate. For a producer/consumer pattern, a `k_msgq` or `k_fifo` is usually the right abstraction because it carries the data along with the signal, eliminating the separate flag entirely.

The teaching approach matters here. Rather than just rewriting the code, it is more effective to ask the engineer to explain what happens if the compiler caches the flag, or if the thread is preempted between reading the flag and reading the data. Walking through a concrete interleaving usually makes the problem obvious without a lecture. Then the fix is a shared decision, and the engineer owns it.

Finally, this is a good opportunity to introduce a team convention: shared state between threads should always go through a documented synchronization primitive, and code review should flag raw globals used for cross-thread communication. That turns a one-off correction into a durable practice.

**Possible follow-ups:**
- How would you explain the difference between `volatile` and a memory barrier to an engineer who has only used `volatile` for register access?
- If the flag is only ever written by one thread and read by another, is a mutex overkill, and what would you use instead?