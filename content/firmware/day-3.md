# firmware — Day 3

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must run every 2 ms, but occasionally a lower-priority task needs to perform a flash write that blocks for up to 50 ms. How would you approach this scheduling conflict?

**Answer:** This is a classic priority inversion and deadline-miss scenario. I'd approach it by first analyzing whether the 2 ms sensor task truly needs hard real-time guarantees or if occasional jitter is acceptable. If it's a medical sensor capturing physiological signals, even a single missed sample could be problematic.

The flash write blocking is the core issue. I'd restructure the design so the flash write doesn't happen synchronously in the low-priority task's main thread. Instead, I'd use a workqueue approach: the low-priority task prepares the data buffer and submits a work item to a system workqueue. The actual flash write happens asynchronously, and the sensor task continues unimpeded. Zephyr's delayed workqueue can also handle the timing if writes need to be batched.

If the flash write absolutely must happen synchronously (e.g., for power-loss safety), I'd consider using a dual-bank approach where we write to a shadow bank while the sensor task reads from the active bank, then atomically swap. Alternatively, I'd evaluate whether the flash controller supports a "write while read" mode, or if we can use a small RAM buffer that gets flushed during idle periods.

The key trade-off is between data integrity guarantees and real-time performance. In a medical device, I'd lean toward the workqueue approach with a power-fail detection circuit that triggers an emergency flush of the workqueue buffer to a dedicated non-volatile area.

**Possible follow-ups:**
- How would you handle the case where the workqueue itself gets backed up because sensor data is arriving faster than flash can absorb it?
- What Zephyr kernel configuration options would you check or modify to support this approach?

## Q2: You're debugging a firmware crash that only occurs after the device has been running for 12+ hours. The crash is a hard fault, and you have a JTAG debugger available but cannot reproduce the issue in less than 8 hours. How would you approach this?

**Answer:** This sounds like a classic memory corruption or stack overflow that accumulates over time. I'd start by narrowing the search space without waiting for the full 12-hour cycle.

First, I'd instrument the firmware to add diagnostic hooks that don't change timing significantly. I'd enable the MPU (Memory Protection Unit) if the microcontroller supports it, configured to trap accesses to unused memory regions and to guard stack boundaries. This can catch stack overflows immediately rather than letting them corrupt adjacent data.

Second, I'd add a simple "canary" pattern at the boundaries of critical data structures and task stacks. I'd write a low-priority background task that periodically checks these canaries and logs the last-known-good values to a circular buffer in RAM. If a crash occurs, the debugger can inspect the buffer to see which canary failed and roughly when.

Third, I'd use the debugger's hardware breakpoint and watchpoint capabilities strategically. I'd set watchpoints on memory regions that are frequently corrupted in similar systems — often DMA buffer descriptors, heap metadata, or the RTOS's internal task control block list. If the watchpoint triggers, I can examine the call stack to see who wrote there.

Finally, I'd try to accelerate reproduction. If the crash correlates with a specific operation count rather than wall-clock time, I could write a test script that exercises that operation at maximum rate. If it's temperature-related, I could use a heat gun to stress the device. If it's memory-fragmentation-related, I could deliberately fragment the heap by allocating and freeing varying-sized blocks in a loop.

The systematic approach is: instrument to catch the failure earlier, use hardware debug features to trap the exact moment of corruption, and attempt to accelerate the failure mode without changing the root cause.

**Possible follow-ups:**
- What if the crash corrupts the diagnostic buffer itself before you can read it?
- How would you distinguish between a stack overflow and a heap corruption in this scenario?

## Q3: You need to implement a circular buffer for a data acquisition system that captures sensor samples at 10 kHz and processes them in bursts. The buffer must be shared between an ISR (writing) and a task (reading). How would you design this in embedded C, and what pitfalls would you watch for?

**Answer:** I'd implement a lock-free circular buffer using a single-producer, single-consumer pattern, which avoids the overhead of mutexes in the ISR. The key design elements:

- Use volatile-qualified head and tail pointers (or indices) that are only modified by one side each: the ISR advances the write index, the task advances the read index.
- The buffer size should be a power of two to allow efficient masking instead of modulo operations.
- Use memory barriers (or compiler barriers like `__DSB()` on ARM) to ensure the data is written before the index is updated, preventing the consumer from reading stale data.

Pitfalls to watch for:
1. **Wrap-around ambiguity**: A completely full buffer looks identical to an empty one if head == tail. I'd either leave one slot always empty, or use a separate "full" flag.
2. **Cache coherency**: On Cortex-M7 or higher with cache, the ISR and task might see different views of memory. I'd either disable caching on the buffer region or use cache maintenance operations.
3. **Compiler optimization**: Without proper volatile and barrier usage, the compiler might reorder the index update before the data write, or cache the index in a register. I'd use `volatile` on the indices and consider `__atomic` built-ins if available.
4. **ISR nesting**: If a higher-priority interrupt can preempt this ISR and also write to the buffer, the single-producer assumption breaks. I'd either disable nesting for this ISR or use a double-buffer scheme.

For the 10 kHz rate, I'd calculate the worst-case burst size and size the buffer to absorb it, then add headroom. I'd also consider using DMA to move data from the peripheral directly into the buffer, reducing ISR overhead.

**Possible follow-ups:**
- How would you modify this design if you had multiple consumers (e.g., one for logging, one for real-time processing)?
- What if the buffer needs to be accessed from both regular and interrupt context on a dual-core MCU?

## Q4: You're reviewing a colleague's firmware code that uses a large number of global variables to share state between modules. The code works correctly in testing but is difficult to maintain and test. How would you approach refactoring this without introducing regressions?

**Answer:** This is a common situation in firmware that evolved from prototypes. I'd approach it as a gradual refactoring with safety nets, not a big-bang rewrite.

First, I'd establish a characterization test suite. Before changing any code, I'd write tests that exercise the current behavior at the module boundaries — logging inputs and outputs, checking state transitions. On a microcontroller, this might mean creating a test harness that runs on the host PC with mocked hardware, or using the debugger to capture state snapshots during normal operation.

Then I'd prioritize the refactoring based on dependency analysis. I'd map out which globals are read/written by which modules. The most dangerous globals are those written by multiple modules — they create hidden coupling. I'd start by encapsulating those behind accessor functions, even if the accessors are trivial at first. This breaks the direct dependency and gives me a place to add assertions or logging later.

For each global, I'd ask: does this represent a system-wide resource (like a hardware register) or module-internal state? System-wide resources might legitimately be singletons, but module-internal state should move into a struct that's passed to the module's functions. I'd introduce an initialization function that allocates or returns a pointer to the state struct, then thread that pointer through the call chain.

The key technique is "strangler pattern": I'd add the new encapsulated interface alongside the old globals, migrate callers one by one, and only remove the globals after all callers are migrated. Each migration step should be small enough to review and test independently.

I'd also add compiler warnings or static analysis rules to flag new global variables, preventing the pattern from recurring. In a medical device context, I'd argue that globals make it harder to trace data flow during a root-cause investigation, which is a safety concern.

**Possible follow-ups:**
- How would you handle a global that's accessed from both main-loop code and an ISR during the refactoring?
- What if the team is under schedule pressure and doesn't want to invest in refactoring now?

## Q5: A junior engineer on your team has implemented a watchdog timer that kicks in the main loop, but the device occasionally resets during a lengthy calibration routine that takes 3 seconds. The engineer proposes increasing the watchdog timeout to 5 seconds. How would you guide them?

**Answer:** I'd start by acknowledging that their proposed fix would work, but I'd frame it as a conversation about design intent versus expediency. Increasing the timeout treats the symptom, not the root cause — the real issue is that a 3-second blocking operation exists in a system that should remain responsive.

I'd walk through the alternatives with them:

1. **Restructure the calibration routine** to be incremental — break it into smaller steps that each take <100 ms, and kick the watchdog between steps. This keeps the watchdog responsive to actual hangs. Many calibration algorithms can be paused and resumed if the hardware state is saved between steps.

2. **Use a cooperative multitasking approach** — if we're not using an RTOS, we can still structure the calibration as a state machine that yields control back to the main loop periodically. The main loop kicks the watchdog and checks if calibration should continue.

3. **Move calibration to a lower-priority context** — if using an RTOS, the calibration could run in a task that yields periodically, while a higher-priority task handles watchdog kicking and safety monitoring.

4. **Use a two-stage watchdog** — a short timeout (e.g., 500 ms) for the main loop, and a longer timeout for the calibration phase, with explicit entry/exit notifications to the watchdog driver.

I'd also ask the engineer to consider: what happens if the calibration routine hangs at the 4-second mark? With a 5-second timeout, we'd wait another second before resetting. With a restructured approach, we'd detect the hang within 100 ms. In a medical device, that difference matters.

Finally, I'd suggest we document the decision in the design history file, explaining why we chose the restructured approach over simply extending the timeout, as part of our risk management documentation.

**Possible follow-ups:**
- What if the calibration routine cannot be broken into smaller steps because it requires continuous hardware access?
- How would you test that the restructured calibration still produces correct results?