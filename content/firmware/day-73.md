# firmware — Day 73

## Q1: How would you approach implementing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** The first step is to recognize the symptom for what it is: the interrupt rate exceeds the CPU's ability to complete the ISR before the next edge arrives, so the system spends most of its time in interrupt context and either drops events, starves lower-priority work, or both. The fix is almost never "make the ISR faster" alone — it's about reducing the number of interrupts the CPU has to take, and moving work out of interrupt context.

Concretely, I'd work through a hierarchy of options:

1. **Reduce interrupt frequency at the source.** If the peripheral supports it, switch from per-sample or per-byte interrupts to a FIFO/watermark threshold, so one interrupt covers many data items. Many ADCs, UARTs, and SPI peripherals have configurable FIFO trigger levels — raising the threshold directly cuts interrupt load.
2. **Move to DMA.** If the data is a continuous stream, DMA is the right answer: the peripheral writes into a buffer without CPU involvement, and you take one interrupt per buffer half or per buffer completion rather than per item. This is the standard pattern for high-rate acquisition.
3. **Split the ISR into top-half and bottom-half.** Keep the ISR minimal — acknowledge the interrupt, capture the minimum state, and defer processing to a work queue, a thread, or a software-triggered task. In Zephyr this maps naturally to an ISR that signals a thread via a semaphore or message queue, or posts to a work queue.
4. **Prioritize and budget.** If multiple interrupts compete, assign priorities so the time-critical one preempts, and measure actual ISR execution time against the interrupt period to confirm there's headroom. If the measured worst-case ISR time exceeds the period, no amount of cleverness in the ISR will save you — the architecture has to change.

The key diagnostic is to measure, not guess: instrument the ISR entry/exit, count interrupts per second, and compute the fraction of CPU time spent in interrupt context. If that fraction is approaching or exceeding the budget, the design needs restructuring, not micro-optimization.

**Possible follow-ups:**
- How would you decide between raising a FIFO threshold and moving to DMA for a given peripheral?
- What would you do if the peripheral has no FIFO and no DMA support, and the interrupt rate is genuinely too high?

## Q2: How would you approach designing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core problem is that an edge-triggered signal is a claim about the world ("data is ready"), and a glitch is a false claim. The firmware has to be robust to the signal being wrong, not just to the signal being late.

I'd approach it in layers:

1. **Validate the data, not just the edge.** The most reliable defense is to treat the edge as a hint rather than a guarantee. After the edge fires, read the peripheral's own status register or a validity flag before consuming data. If the peripheral exposes a "data ready" bit or a CRC/checksum, use it. This turns a spurious edge into a no-op rather than a bad read.
2. **Debounce in hardware or firmware.** If the signal is genuinely noisy, a small RC filter or a Schmitt-trigger input can clean it up at the source. In firmware, a short debounce window (ignore edges within N microseconds of the last accepted edge) can suppress glitches, but this must be tuned against the real minimum inter-event time so you don't drop legitimate events.
3. **Design the consumer to be idempotent.** If a spurious edge causes the ISR to run and read stale data, the downstream logic should be able to detect that the data hasn't changed or isn't new — for example, by checking a sequence counter or timestamp. This makes the system tolerant of extra edges.
4. **Consider level-triggered or polling as an alternative.** If the signal is unreliable, a level-triggered interrupt (interrupt while data-ready is asserted) or a periodic poll of the status register may be more robust than edge-triggering, at the cost of some latency or CPU overhead. The trade-off depends on how time-critical the data is.

The general principle: don't let a single unreliable signal be the sole gate on a critical data path. Validate at the point of consumption, and make the system's correctness independent of the signal being perfect.

**Possible follow-ups:**
- How would you distinguish a glitch from a legitimate edge that arrives very close to the previous one?
- If the peripheral has no status register or validity flag, what other validation could you apply?

## Q3: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic "heisenbug" pattern, and the debugger's presence is itself a clue. Attaching a debugger changes several things: it may halt the CPU at breakpoints, it may slow execution, it may change the power state, and it may alter timing. The fact that the bug disappears with the debugger attached strongly suggests a timing-sensitive or race-condition issue, or something related to the debug interface itself.

I'd approach it systematically:

1. **Characterize the difference.** Is the debugger halting the CPU, or just attached and running? Does the bug disappear with the debugger merely connected (no breakpoints), or only when halted? This narrows whether the effect is timing-related or electrical/interface-related.
2. **Look for timing-sensitive code.** Race conditions between ISRs and threads, missing synchronization, or code that relies on a particular execution speed are prime suspects. The debugger's slowdown can mask a race by changing the window in which it occurs.
3. **Check for debug-interface side effects.** On some MCUs, the debug peripheral shares pins or clock resources with other functions. Attaching the debugger can change pin states, disable low-power modes, or affect the clock tree. If the bug is in a low-power path or a pin-muxed peripheral, the debugger may be inadvertently "fixing" it.
4. **Use non-intrusive instrumentation.** Instead of a debugger, use GPIO toggles, a spare UART, or a trace buffer to observe behavior without halting the CPU. This lets you see what's happening in the standalone case.
5. **Reproduce with the debugger attached but not halting.** If you can attach without halting (e.g., SWD in a non-intrusive mode), you can compare behavior directly. If the bug still disappears, the debugger's presence itself is the variable.

The key is to stop treating the debugger as a neutral observer — it's an active participant that changes the system. The fix is usually to find the timing or state dependency that the debugger is masking, and address that directly.

**Possible follow-ups:**
- How would you use a trace buffer or GPIO toggles to observe a timing-sensitive bug without a debugger?
- What kinds of bugs are most commonly masked by a debugger's slowdown?

## Q4: How would you approach deciding what belongs in a bootloader versus what belongs in the application, for a device that must support field updates?

**Answer:** The bootloader/application split is a design decision with long-term consequences, because the bootloader is the one piece of code that's hardest to change in the field — if the bootloader is broken, you may have no way to recover the device. So the guiding principle is: keep the bootloader as small, simple, and stable as possible, and put everything that might need to change into the application.

Concretely, I'd draw the line like this:

**In the bootloader:**
- The minimum code to initialize the hardware needed to receive and validate an update (clock, flash controller, the communication interface used for updates).
- The logic to select which image to boot (e.g., dual-bank selection, rollback decision).
- Image validation: CRC or cryptographic signature check before jumping to the application.
- A recovery path: if no valid image exists, stay in the bootloader and wait for an update.
- A way to enter the bootloader from the application (e.g., a magic value in a known RAM location or a flash flag), so the application can request an update without a physical button.

**In the application:**
- Everything else: the actual product functionality, the update client that downloads the image, the decision of when to apply an update, user-facing update UI, logging, etc.
- The application is responsible for fetching the image, verifying it (or handing it to the bootloader for verification), and then triggering a reboot into the bootloader to apply it.

The rationale is that the bootloader should be a fixed, trusted anchor. If you put update logic, communication stacks, or product features in the bootloader, you enlarge the attack surface and the chance that a bug in the bootloader bricks the device. Keeping it minimal means it can be thoroughly reviewed and tested once, and then left alone.

A related decision is whether the bootloader should be updatable at all. For most medical or safety-critical devices, the answer is no — or only via a carefully controlled, physically-present service path — because an interrupted bootloader update is the one scenario that can truly brick the device.

**Possible follow-ups:**
- How would you handle the case where the bootloader itself needs a bug fix in the field?
- What's the minimum set of validation checks the bootloader should perform before jumping to the application?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** This is a common and understandable misconception, and the right response is to correct it precisely rather than just say "that's wrong." `volatile` tells the compiler that the variable's value may change at any time outside the current flow of control, so it must not cache the value in a register or optimize away reads and writes. That's necessary but not sufficient for synchronization.

The gaps are:

1. **Atomicity.** `volatile` does not make a read-modify-write atomic. If the ISR and the thread both do `counter++`, the operation is a load, an increment, and a store, and an interrupt between the load and the store can lose an update. `volatile` doesn't prevent that.
2. **Memory ordering.** `volatile` does not establish ordering with respect to other memory accesses. On a multicore or a system with a weakly-ordered memory model, or even on a single core with compiler reordering, the compiler or CPU may reorder accesses around the volatile one. Synchronization requires an ordering guarantee, which `volatile` doesn't provide.
3. **Compiler and CPU reordering.** The compiler is free to reorder non-volatile accesses around volatile ones in ways that break the intended protocol. A proper synchronization primitive (atomic, mutex, semaphore, memory barrier) constrains this.

The correct guidance is to use the right tool for the job:

- For a simple flag or counter shared between an ISR and a thread, use an atomic type (e.g., `atomic_t` in Zephyr, or C11 `_Atomic`) with the appropriate memory ordering.
- For passing data, use a proper synchronization primitive: a semaphore, a message queue, or a lock-free ring buffer with correct memory barriers.
- If the shared data is more than a single word, a lock or a queue is almost always the right answer — `volatile` on a struct does nothing useful for concurrency.

I'd frame it as: "`volatile` is about the compiler not optimizing the access; synchronization is about the CPU and compiler not reordering or interleaving accesses. They're different problems, and you need both." Then I'd point them at the specific primitive that fits their use case and ask them to rework the module with it, and review the change together.

**Possible follow-ups:**
- Can you give an example where `volatile` alone produces a wrong result but an atomic does not?
- When is `volatile` actually the right tool — for example, for a memory-mapped register?