# firmware — Day 72

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** The core problem is that the arrival rate of events exceeds the service rate of the ISR, so the CPU spends an unsustainable fraction of its time in interrupt context and starves everything else. The first step is to quantify the actual rates: measure the interrupt frequency, the worst-case ISR execution time, and the resulting CPU utilization. If the ISR is consuming more than a modest fraction of the budget, no amount of clever coding inside the ISR will fix it — the architecture has to change.

The standard approach is to move work out of the ISR and into a deferred context. The ISR should do the absolute minimum: capture the data or acknowledge the condition, push it into a lock-free queue or ring buffer, and return. A thread or work queue then drains that buffer at its own pace. This decouples the arrival rate from the service rate, as long as the buffer is large enough to absorb bursts and the average service rate keeps up.

If the average rate genuinely exceeds what the CPU can handle even with deferral, then the options narrow. One is DMA: let the peripheral write directly to memory without per-event CPU involvement, and only interrupt on a block boundary or a half-buffer watermark. This is the right answer for streaming peripherals like ADCs, SPI slaves, or UARTs at high baud. Another is to reduce the event rate at the source — configure the peripheral to batch, use a FIFO, or lower the sample rate if the application allows. A third is to accept that the CPU is undersized and either move to a faster part or offload to a co-processor or FPGA.

The key insight is that "the ISR is too slow" is usually a symptom of doing too much in the ISR, not of the ISR itself being inherently slow. Deferral and DMA are the two levers that almost always apply.

**Possible follow-ups:**
- How would you size the ring buffer between the ISR and the deferred thread, and what would you do if the buffer overflows?
- What are the trade-offs between using a Zephyr work queue versus a dedicated thread for the deferred processing?

## Q2: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The first thing to establish is what "spurious edge" actually means in this system. Is the glitch a genuine electrical artifact — a short pulse that doesn't meet the peripheral's timing spec — or is it a real edge that the peripheral asserts before its data is actually valid? Those are different problems with different fixes.

If the glitch is electrical, the right fix is usually at the hardware or peripheral-configuration level: add a debounce filter in the GPIO peripheral if it supports one, add an RC filter on the board, or configure the interrupt to require the signal to be stable for a minimum number of clock cycles. Many MCU GPIO blocks have a programmable glitch filter for exactly this reason. Fixing it in firmware by ignoring edges is a band-aid; fixing it at the source is more robust.

If the glitch is a real edge but the data isn't ready yet, then the firmware needs a validation step. The pattern is: on the edge, don't immediately read the data. Instead, check the peripheral's own status register or a data-ready bit, and only proceed if it confirms valid data. If the peripheral doesn't have such a bit, then the firmware needs its own validity check — a CRC, a range check, a sequence number, or a minimum settling delay measured from the edge.

A defensive pattern that works well here is to treat every edge as a candidate, not a certainty. The ISR timestamps the edge and pushes a "candidate event" to a deferred context. The deferred context then validates: is the data plausible? Does it pass CRC? Is it within the expected range? If not, discard it and log the event. This keeps the ISR short and puts the validation logic where it can be tested and instrumented.

The important thing is not to silently swallow glitches. If they're happening, they're a signal that something is wrong — either the hardware is marginal, the peripheral is misconfigured, or the source is noisy. Logging the rate of discarded events gives you the data to decide whether to fix it in hardware, in configuration, or in firmware.

**Possible follow-ups:**
- How would you distinguish between a glitch that's an electrical artifact and one that's a real edge with premature data?
- If the peripheral has no status register and no CRC, what validation strategies would you fall back on?

## Q3: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the first instinct should be to suspect that attaching the debugger changes the system's timing, power state, or both. The debugger doesn't just observe — it halts the core, keeps clocks running, may hold certain peripherals in a known state, and often disables low-power modes. Any of those can mask the bug.

The first step is to characterize the difference. Does the misbehavior correlate with a specific operation — a flash write, a low-power transition, a wireless transmission, a peripheral init? Does it happen at a particular time after boot? Does it happen more often at temperature extremes or at low battery? The goal is to narrow the window before reaching for more invasive tools.

The next step is to replace the debugger with non-intrusive instrumentation. A GPIO pin toggled at key points, captured on a scope or logic analyzer, gives you timing information without halting the core. A UART log at a low baud rate is less intrusive than a debugger but still changes timing; a RAM-based circular log that's dumped after the fact is even less intrusive. If the device has an SWO or trace pin, that's often the best option — it gives you instruction-level visibility without halting.

A common root cause in this category is that the debugger keeps the core out of a low-power state, so a bug in the sleep/wake sequence never manifests. Another is that the debugger holds a peripheral in reset or prevents a clock from gating, masking a race. A third is that the debugger's halt changes the timing of an interrupt relative to a main-loop operation, hiding a race condition.

Once you have a hypothesis, the way to confirm it is to reproduce the failure without the debugger, then add instrumentation incrementally until you can see the failure mode. If the bug disappears when you add instrumentation, that itself is a clue — it means the bug is timing-sensitive, and you should be looking at races, not logic errors.

**Possible follow-ups:**
- What specific low-power or clock-gating behaviors would you check first if you suspected the debugger was masking a sleep-related bug?
- How would you use a RAM-based log to capture the state leading up to a failure without changing the timing enough to hide it?

## Q4: How would you approach deciding what belongs in a bootloader versus what belongs in the application, for a device that must support field updates?

**Answer:** The guiding principle is that the bootloader should be as small and as simple as possible, because it's the one piece of code that must never fail — if it does, the device is bricked. Everything that can live in the application should live in the application, because the application can be updated, and a bug in the application is recoverable.

What must live in the bootloader: the code that decides which image to boot, the code that verifies an image's integrity before booting it, the code that performs the actual flash write of a new image, and the code that handles rollback if the new image fails to validate. It also needs a minimal communication path to receive a new image — but that path should be as simple as possible, ideally a single well-tested transport rather than a full protocol stack.

What should live in the application: everything else. The application is responsible for deciding when to accept an update, downloading the image (possibly over a complex wireless stack), staging it, and then triggering a reboot into the bootloader to apply it. The application can also do pre-validation — checking the image's signature, version, and compatibility — before handing it to the bootloader, so the bootloader only has to do the final integrity check.

The boundary is usually drawn at the point where the bootloader must make a decision that affects whether the device boots. Anything that influences that decision — image validity, rollback state, boot flags — must be in the bootloader or in a shared, carefully-versioned data structure. Anything that doesn't — user interface, logging, network stack — belongs in the application.

A practical consideration is that the bootloader and application must agree on the flash layout, the image format, and the metadata structure. That contract should be versioned and documented, because changing it later means either a bootloader update (which is risky) or a compatibility shim.

**Possible follow-ups:**
- How would you handle a situation where the bootloader itself needs to be updated in the field?
- What metadata would you store alongside each image, and where would you store it so that a power loss mid-update doesn't corrupt the boot decision?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** The first thing is to acknowledge what's correct in their reasoning: `volatile` does prevent the compiler from caching the variable in a register or optimizing away accesses, and for a single flag that's written by an ISR and read by a thread, that's often enough to make the code *appear* to work. The problem is that it's not enough to make it *correct*, and the gap between "works in testing" and "correct" is exactly where intermittent field failures live.

The key teaching point is that `volatile` says nothing about atomicity or ordering. If the shared data is more than a single word — a struct, a buffer, a multi-byte counter — then the thread can observe a partially-updated value, because the ISR can preempt between the writes. Even for a single word, `volatile` doesn't guarantee that the compiler won't reorder other memory accesses around it, which matters if the flag is meant to signal that other data is ready. And on some architectures, a plain load or store of a word is atomic, but on others it isn't, and `volatile` doesn't change that.

The right pattern depends on what's being shared. For a single flag or counter, an atomic type with explicit acquire/release semantics is the correct tool — in Zephyr, that's `atomic_t` with `atomic_set` and `atomic_get`, or a `k_sem` if the thread needs to block. For a buffer of data, the pattern is a lock-free ring buffer with a single producer and single consumer, using atomics for the head and tail indices and memory barriers to enforce ordering. For anything more complex, a mutex or a message queue is the right answer, though a mutex can't be taken from an ISR, so the ISR side has to use a different mechanism.

The way to guide them is to walk through a concrete failure scenario: "Imagine the ISR writes a 32-bit value and the thread reads it. On this architecture, is that atomic? What if the ISR fires between the two halves of a 64-bit write? What if the compiler reorders the flag check before the data read?" Once they see the failure mode, the fix is usually obvious. The goal isn't to make them afraid of `volatile` — it's to make them reach for the right tool for the job.

**Possible follow-ups:**
- How would you explain the difference between `volatile` and `atomic` to someone who's only worked on single-core systems?
- What's the correct pattern for a single-producer, single-consumer ring buffer between an ISR and a thread, and where do memory barriers fit in?