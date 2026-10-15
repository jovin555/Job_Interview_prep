# firmware — Day 86

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt rate is high enough that servicing every interrupt individually would consume an unreasonable share of CPU time?

**Answer:** The first step is to quantify the problem rather than assume it: measure the actual interrupt rate, the worst-case ISR execution time, and the resulting CPU utilization. If servicing every interrupt individually is genuinely too expensive, there are several established strategies, and the right one depends on what the data actually needs.

The most common approach is to decouple the interrupt from the work. Keep the ISR minimal — ideally just acknowledging the interrupt and moving data into a hardware FIFO, DMA buffer, or a lock-free ring buffer — and let a deferred context (a thread, work queue, or bottom-half) do the heavier processing. This converts a per-interrupt cost into a per-batch cost.

If the peripheral supports DMA, that's usually the strongest lever: configure DMA to move data into a buffer and generate an interrupt only on a half-transfer or full-transfer boundary, so the CPU is interrupted once per buffer rather than once per byte or sample. This is the standard pattern for continuous high-rate acquisition.

If the interrupt rate is high but the data is not all equally important, another option is to coalesce or drop: for example, only interrupt on a threshold crossing or on a status change rather than on every sample, and let the application poll a counter or timestamp when it needs the detail. That trades latency for CPU headroom, which is often acceptable for monitoring rather than control.

A few pitfalls to watch: don't just move the work to a lower-priority thread and assume the problem is solved — if the aggregate work still exceeds the available CPU, you've only changed where the backlog accumulates. Also be careful with interrupt priority and nesting: a high-rate ISR that blocks a lower-priority but more time-critical ISR can cause worse problems than the one you were trying to fix. And if you use DMA, make sure the buffer sizing and the half/full interrupt thresholds are chosen so that the deferred context can always keep up with the arrival rate.

**Possible follow-ups:**
- How would you decide between a DMA-based approach and a simple ring buffer with a deferred thread, if the peripheral doesn't support DMA?
- What would you do if, after deferring the work, you find the deferred context still can't keep up during bursts?

## Q2: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core issue is that an edge-triggered signal is a claim about the world, and glitches mean the claim is sometimes false. The firmware has to be robust to that without either missing real events or acting on fake ones.

The first line of defense is to treat the edge as a hint, not as proof. When the ISR fires, don't immediately consume data; instead, verify that the peripheral actually has valid data ready by reading its status register or a data-valid flag. If the flag isn't set, the edge was spurious — acknowledge and return. This is cheap and catches most glitches.

The second line of defense is debouncing or filtering in the time domain. If the signal is known to be noisy, a short hardware or software debounce (e.g., re-check the line after a few microseconds, or require the level to be stable for a minimum window) can reject glitches that are shorter than the real signal's minimum pulse width. The key is to know the real signal's minimum valid pulse width from the datasheet and set the filter window below that.

The third consideration is what happens if a real edge is missed because the ISR was already busy or the signal was masked. A robust design doesn't rely solely on edges: it also periodically polls the data-ready status as a backstop, so a missed edge doesn't mean lost data. This is especially important if the peripheral's data-ready line can be asserted while interrupts are disabled.

Finally, think about the failure mode. If a spurious edge causes the ISR to read a register that isn't ready, you might get stale or garbage data. So the read path should validate the data (range check, CRC, or a sequence counter) before it's used. That way, even if a glitch slips through the edge filter, the data validation catches it.

**Possible follow-ups:**
- How would you choose the debounce window if the datasheet doesn't specify a minimum pulse width?
- What would you do if the glitch rate is high enough that the ISR itself becomes a significant CPU load even though most edges are spurious?

## Q3: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** Stack sizing is one of those things where "it works in testing" is not the same as "it's correct," because stack overflow often manifests as corruption somewhere else rather than a clean fault. So the approach has to combine estimation, measurement, and margin.

Start with estimation. For each thread, enumerate the call depth: the thread entry function, the functions it calls, and the deepest chain of calls it can reach. Add the local variable footprint at each level, plus the context saved on entry to each function (registers, return address, alignment). Don't forget interrupt stack usage if the thread can be interrupted — on many architectures the ISR uses the current thread's stack, so the worst-case ISR depth has to be included in the thread's budget. Also account for any library calls (printf-style formatting, floating point, crypto) that have large internal stack frames.

Then measure. Zephyr provides stack analysis hooks — the `k_thread_stack_space_get` API and the `CONFIG_THREAD_STACK_INFO` / `CONFIG_INIT_STACKS` options let you fill the stack with a known pattern and then check the high-water mark. Run the system through its worst-case paths — not just the happy path — and record the maximum stack usage per thread. The high-water mark tells you what was actually used, but it only tells you about the paths you exercised.

Then add margin. A common rule of thumb is 25–50% headroom over the measured high-water mark, but the right number depends on how confident you are that you've exercised all paths. For a medical device, I'd lean toward the higher end and document the reasoning.

Finally, verify continuously. Enable stack sentinel checking (`CONFIG_THREAD_STACK_SENTINEL`) or MPU-based stack guarding (`CONFIG_MPU_STACK_GUARD`) so that an overflow faults immediately rather than corrupting adjacent memory. And re-check the high-water marks after any significant change to the code, because a new library call or a deeper error path can quietly push usage up.

**Possible follow-ups:**
- How would you handle a thread whose worst-case stack usage is hard to bound because it calls into a third-party library?
- What's the trade-off between using a larger stack and using a separate interrupt stack on architectures that support it?

## Q4: A junior engineer has written a driver that works reliably on the bench but uses a fixed `k_sleep` delay to wait for a peripheral to become ready after each command, rather than checking a status register or using an interrupt. How would you guide them?

**Answer:** I'd start by acknowledging that the code works and that the instinct behind it — "wait long enough and it'll be ready" — is understandable, especially when the datasheet gives a typical timing. The goal isn't to tell them they're wrong; it's to help them see why the approach is fragile and what the better pattern is.

The first point is correctness under variation. A fixed delay is only safe if the worst-case readiness time is known and bounded, and if the delay is set above that worst case. But worst-case timing varies with temperature, supply voltage, part-to-part variation, and sometimes with the specific command. A delay tuned on the bench may be too short on a cold unit or too long on a warm one. The datasheet's "typical" number is not a guarantee; the maximum is what matters, and even that may not cover all conditions.

The second point is efficiency. A `k_sleep` blocks the thread for the full delay even when the peripheral is ready much sooner. In a system with other work to do, that's wasted time and, in a real-time system, potentially missed deadlines. Polling a status register with a bounded timeout, or using an interrupt or a semaphore signaled by the peripheral's ready line, lets the thread proceed as soon as the peripheral is actually ready.

The third point is diagnosability. If the peripheral never becomes ready — because it's failed, because the bus is stuck, or because the command was malformed — a fixed delay just proceeds and the failure shows up later as a confusing symptom. A status check with a timeout produces a clear error at the point of failure.

I'd suggest a concrete refactor: replace the fixed delay with a bounded poll of the status register (with a timeout), or better, use the peripheral's ready interrupt to signal a semaphore. If the hardware doesn't provide a ready signal, a bounded poll is the fallback. And I'd frame it as a general principle: "wait for the condition, not for a guess about how long the condition takes."

**Possible follow-ups:**
- How would you choose the timeout value for the bounded poll, and what would you do if the timeout expires?
- What would you do if the peripheral's ready signal is not exposed on the hardware and the only option is polling?

## Q5: How would you approach a situation where you discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules?

**Answer:** The first thing is to resist the urge to either hide it or immediately rip everything up. The right response is to make the problem visible, quantify it, and then decide deliberately whether to fix it now, work around it, or accept it — with the trade-offs documented.

I'd start by writing down what the actual problem is, in concrete terms: what breaks, under what conditions, and how often. "The early decision to use a single shared buffer for all sensor data means that adding the second sensor type requires touching every module that reads the buffer" is a much more useful statement than "the architecture is wrong." Quantifying the impact — how many modules, how much rework, what's the risk of not fixing it — turns a vague worry into a decision.

Then I'd assess the options honestly. Option one is to fix it properly now: estimate the rework, the risk of introducing regressions, and the schedule impact. Option two is to work around it: add an abstraction layer or a shim that contains the damage, so new code doesn't inherit the problem, and migrate incrementally. Option three is to accept it and document it, if the cost of fixing exceeds the cost of living with it — but that decision needs to be explicit, not accidental.

For a medical device, the risk calculus matters: if the design decision creates a safety or compliance concern, "accept it" may not be on the table. If it's a maintainability concern, the trade-off is more about schedule and future cost.

I'd bring the analysis to the team and the relevant stakeholders rather than deciding alone, because the decision affects people outside my immediate work. And I'd be clear about my own role in the original decision — owning it rather than framing it as something that "happened." The goal is to solve the problem, not to assign blame, but acknowledging the origin builds trust and makes it easier for others to raise similar issues early next time.

**Possible follow-ups:**
- How would you decide between a full refactor and an incremental migration, if the schedule is tight?
- What would you do if the team decides to accept the problem, but you believe it's a safety concern?