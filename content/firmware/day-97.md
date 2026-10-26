# firmware — Day 97

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt rate is high enough that servicing every interrupt individually would consume an unreasonable share of CPU time?

**Answer:** The first step is to quantify the problem rather than assume it: measure the actual interrupt rate, the worst-case ISR execution time, and the resulting CPU utilization. If servicing every interrupt would consume, say, more than a few percent of CPU in a system with other real-time obligations, the architecture needs to change. The standard approaches, in rough order of preference:

1. **DMA with completion or half-transfer interrupts.** For any peripheral that moves data (ADC, SPI, UART, I2S), let the DMA engine do the per-sample work and interrupt only on buffer half-full/full. This converts an interrupt-per-sample problem into an interrupt-per-block problem, and the CPU cost scales with block size rather than sample rate. This is usually the right answer for streaming data.

2. **Interrupt coalescing / rate limiting.** If the peripheral itself generates the interrupt (e.g., a GPIO edge or a status-change line), configure the peripheral to assert the interrupt less often — many peripherals have FIFO thresholds or "interrupt after N events" settings. Where the hardware doesn't support it, a small amount of ISR-side batching (read all pending status bits, clear them in one write, process as a batch) reduces the per-event overhead.

3. **Move work out of the ISR.** Keep the ISR to the absolute minimum — acknowledge the source, capture a timestamp or counter, and signal a deferred context (a thread, work queue, or bottom-half). The ISR cost then becomes roughly constant regardless of how much processing each event needs. This doesn't reduce the interrupt *rate*, but it reduces the per-interrupt cost, which is often the actual bottleneck.

4. **Polling under a timer, as a deliberate trade.** If the event rate is high and the latency tolerance is loose, a periodic timer that polls the peripheral's status/FIFO can be cheaper and more predictable than an interrupt storm. This is a legitimate design choice when the data is not latency-critical — but it must be a conscious decision, not a fallback.

The key judgment is separating *event rate* from *work per event*. High event rate with trivial work per event → DMA or coalescing. Low event rate with heavy work per event → defer to a thread. High rate *and* heavy work → the architecture is wrong and the data path needs to be restructured (DMA into a ring buffer, processing decoupled from acquisition). I'd also instrument the system to confirm the fix: measure ISR entry counts, ISR duration, and CPU idle time before and after, so the change is validated rather than assumed.

**Possible follow-ups:**
- How would you decide the DMA block size, and what happens if the consumer thread can't keep up with the producer?
- What are the failure modes of interrupt coalescing in a system where missing a single event is unacceptable?

## Q2: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the debugger's presence changes several things simultaneously, so the first job is to figure out *which* change is masking the bug. The usual suspects:

- **Timing.** A debugger slows execution, adds latency between instructions, and can change interrupt arrival relative to code execution. A race condition, a missing volatile, or an ISR/main-loop interaction that only fails at full speed will often disappear under a debugger. This is the most common cause.
- **Power state.** With a debugger attached, the device may not enter the same low-power modes (debug logic keeps clocks running), so a bug tied to sleep/wake transitions or to a peripheral being powered down is masked.
- **Initialization order.** Some debug probes hold the core in reset or halt at a breakpoint before `main`, changing the order in which peripherals come out of reset.
- **Memory layout / optimization.** Debug builds are often `-O0` with different stack usage and different code placement; a stack overflow or an uninitialized-variable bug can vanish when optimization changes.
- **Watchdog.** The debugger may pause or disable the watchdog, hiding a watchdog-related reset.

My approach: first, reproduce the failure *without* the debugger using non-intrusive instrumentation — GPIO toggles, a ring-buffer event log in RAM, a UART trace, or a logic analyzer on the bus. Capture what the device was doing in the moments before the misbehavior. Second, compare the standalone build against the debug build: same optimization level, same linker script, same clock configuration, so the only variable is the debugger. Third, if the bug correlates with timing, deliberately perturb timing in the standalone build (add small delays, change task priorities, vary the interrupt load) to see whether the failure follows the timing change — that confirms a race rather than a logic error. Fourth, review the code for the classic causes: missing `volatile` on shared variables, missing memory barriers, ISR/thread shared state without proper synchronization, and assumptions about peripheral readiness that only hold when execution is slow.

The discipline is to make the invisible visible without changing the thing you're measuring. A debugger is a poor observation tool for timing-sensitive bugs precisely because it perturbs the system; the goal is to replace it with instrumentation that doesn't.

**Possible follow-ups:**
- How would you design an in-RAM event log that survives a crash and can be read out afterward?
- If the bug only appears at full speed, how do you decide whether it's a race or a genuine logic error that the debugger's timing happens to avoid?

## Q3: How would you approach deciding whether a piece of firmware logic belongs in an interrupt service routine versus a deferred context such as a work queue or a thread?

**Answer:** The decision comes down to a few concrete criteria, applied in order:

1. **Latency requirement.** What is the actual deadline for handling the event? If the hardware requires an acknowledge within microseconds (clearing a status flag before the next event arrives, or latching data before it's overwritten), that part *must* be in the ISR. Everything else can be deferred. The ISR should do the minimum the hardware demands and nothing more.

2. **Duration and blocking behavior.** An ISR must be short and must never block. Any operation that can take an unbounded or long time — flash writes, bus transactions with clock stretching, waiting on a mutex, dynamic allocation, logging to a slow medium — belongs in a deferred context. A useful rule of thumb: if the ISR's worst-case execution time can't be bounded tightly and justified against the system's interrupt latency budget, it's too long.

3. **Shared-state and reentrancy.** Code that touches data structures shared with threads, or that needs to take a lock, is much easier to reason about in a thread context where blocking is allowed. Pushing that logic into an ISR forces lock-free designs and priority-inversion reasoning that are easy to get wrong.

4. **Priority and ordering.** Deferred contexts let you assign a priority to the work, so a low-importance event doesn't preempt a high-importance one. In an ISR, everything runs at interrupt priority, which can starve more important work.

The standard pattern is a two-stage split: the ISR acknowledges the hardware, captures the minimum state (a timestamp, a count, a pointer to a filled buffer), and signals a deferred context via a semaphore, event flag, or message queue. The deferred context does the parsing, validation, logging, and state-machine transitions. In Zephyr terms, that's typically an ISR plus a `k_work` item or a dedicated thread; the choice between work queue and thread depends on whether the work needs its own priority and stack or can share the system workqueue.

The judgment call is where to draw the line. I'd err toward putting *less* in the ISR than feels natural, because ISR bugs are the hardest to debug and the most damaging to real-time behavior. The cost of deferral is a small latency and some context-switch overhead; the cost of an overlong ISR is missed deadlines, jitter, and subtle races. For a medical device with a hard real-time loop, that trade almost always favors deferral.

**Possible follow-ups:**
- When would you choose a dedicated thread over the system workqueue for deferred work?
- How would you bound the latency introduced by deferral, and how would you verify it meets the system's timing requirements?

## Q4: A junior engineer has written a driver that works reliably on the bench but uses a fixed `k_sleep` delay to wait for a peripheral to become ready after each command, rather than checking a status register or using an interrupt. How would you guide them?

**Answer:** I'd start by acknowledging what's right about their instinct: a fixed delay is simple, deterministic-looking, and easy to reason about, and on the bench it works. The conversation is about why it's fragile in production, not about whether they were wrong to try it.

The core problems with fixed delays:

- **They're tuned to one condition.** The datasheet's "typical" readiness time is not the worst case across temperature, voltage, and part-to-part variation. A delay that works on one board at room temperature may be too short on a cold board or a slow part, and too long everywhere else — wasting time and power.
- **They hide failures.** If the peripheral never becomes ready (a stuck bus, a dead part, a wrong configuration), a fixed delay just proceeds and the driver reads garbage or hangs later, far from the actual cause. A status check turns that into a clean, localized error.
- **They don't compose.** In a system with other tasks, a blocking delay in a high-priority thread starves everything below it. The delay's cost is paid by the whole system, not just the driver.

The better pattern depends on the context. If the driver runs in a thread, poll the status register with a *bounded* timeout — check the ready bit, and if it's not set within a worst-case budget derived from the datasheet, return an error rather than sleeping blindly. If the peripheral can signal readiness with an interrupt, use it and block on a semaphore with a timeout, which is both efficient and gives you a clean error path. If the driver runs in an ISR or a context where blocking isn't allowed, the readiness check has to be non-blocking and the state machine has to handle "not ready yet" as a normal state.

I'd also point out the general principle: a delay is a guess about the hardware, and guesses should be replaced by observations wherever the hardware lets you observe. The status register *is* the observation. The delay is only acceptable when there is genuinely no way to observe readiness — and even then it should be a documented worst-case value with a comment explaining why, not a round number.

I'd guide them by having them add the status check themselves and then test it under adverse conditions — slow the clock, vary the supply, or use a part known to be at the slow end of the spec — so they see the fixed delay fail and the status check hold. Demonstrating the failure mode is more persuasive than asserting it.

**Possible follow-ups:**
- How would you derive the worst-case timeout value from a datasheet that only gives typical and maximum readiness times?
- What would you do if the peripheral's status register itself is unreliable or doesn't have a ready bit?

## Q5: How would you approach designing a watchdog strategy for a device that must distinguish between a genuine firmware hang and a legitimate but slow operation, without simply extending the timeout until the watchdog becomes meaningless?

**Answer:** The trap to avoid is treating the watchdog as a single timer with a single timeout that gets stretched whenever a slow operation appears. That path leads to a watchdog that's so long it no longer detects the failures it exists to catch. The better approach is to make the watchdog *supervise progress*, not just *elapsed time*.

The key ideas:

1. **Kick from a meaningful place.** The watchdog should be kicked by evidence that the system is healthy, not by a timer that fires regardless of what the rest of the firmware is doing. A common anti-pattern is kicking in the main loop's idle path, which proves only that the loop is spinning — not that the tasks doing real work are alive. Better: each critical task or subsystem reports liveness (a counter, a timestamp, a flag), and a supervisor checks that all of them have reported within their individual deadlines before kicking the watchdog. If any subsystem is silent, the watchdog is not kicked and the device resets.

2. **Per-subsystem deadlines, not one global timeout.** A slow flash erase is legitimate for the flash subsystem but not for the sensor task. Giving each subsystem its own deadline lets the watchdog be tight where it should be tight and lenient where the operation genuinely takes time — without loosening the whole system.

3. **Windowed watchdogs where available.** A windowed watchdog requires the kick to arrive within a window — not too early, not too late. This catches the failure mode where a runaway loop happens to kick the watchdog too frequently, which a simple timeout watchdog misses entirely. Many MCUs support this; it's worth using when the hardware offers it.

4. **Explicit "long operation" handling.** For a genuinely long operation (a flash erase, a calibration routine), the right pattern is not to extend the global timeout but to have the operation *report progress* — the erase routine updates a progress counter as it proceeds, and the supervisor treats forward progress as liveness. If the erase stalls, the counter stops and the watchdog fires. This distinguishes "slow but working" from "hung" without weakening the watchdog.

5. **Debug-mode bypass, carefully.** Watchdogs often need to be paused under a debugger, or development becomes impossible. That bypass must be clearly scoped to debug builds and must never ship in production firmware — and it should be verified in the release build configuration, not assumed.

The design principle is that the watchdog's job is to answer "is the system making progress?" A timeout answers "has time passed?" — which is a weaker and easily gamed question. The extra work of per-subsystem liveness reporting pays for itself in a watchdog that actually catches the failures it's meant to catch, while still allowing legitimate slow operations to complete.

**Possible follow-ups:**
- How would you test that the watchdog actually fires when a subsystem hangs, without waiting for a real failure in the field?
- What's the risk of a supervisor that itself hangs, and how would you protect against it?