# firmware — Day 53

## Q1: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** Stack sizing in Zephyr is a mix of static analysis, measurement, and margin discipline. I'd start by understanding what each thread actually does: its call depth, the size of local buffers, whether it calls into subsystems that have their own stack footprints (logging, printf-family functions, filesystem, network stack), and whether it can be preempted mid-call in a way that adds nesting. A thread that only toggles a GPIO needs far less than one that parses a protocol and calls into a crypto library.

For a first estimate, I'd reason about worst-case call depth rather than typical depth, because stacks overflow at the worst moment, not the average one. Then I'd measure. Zephyr gives you tools for this: `CONFIG_THREAD_ANALYZER` with runtime stats, and the `k_thread_stack_space_get()` API, which reports high-water mark usage. I'd run the system through its heaviest realistic workload — worst-case message sizes, deepest error paths, all logging enabled — and record the peak usage per thread. The key insight is that you must exercise the *unusual* paths, because the deepest stack usage often comes from error handling and logging, not the happy path.

Once I have measured peaks, I'd add margin. The amount depends on risk: for a medical device I'd want generous headroom because an overflow is a safety issue, not just a crash. I'd also enable stack sentinel / stack canary checking (`CONFIG_STACK_SENTINEL`, `CONFIG_HW_STACK_PROTECTION`) so an overflow faults deterministically instead of silently corrupting adjacent memory. And I'd treat stack sizing as something to re-verify whenever a thread's code changes, not a one-time decision — a new log statement or a deeper call chain can quietly blow the budget.

**Possible follow-ups:**
- How would you handle a thread whose stack usage is highly variable depending on input, where the worst case is hard to trigger in testing?
- What's the difference between measuring stack usage with the thread analyzer versus a sentinel, and when would you use each?

## Q2: How would you approach deciding whether a given piece of firmware logic belongs in an interrupt service routine versus a deferred context (thread, work queue, or bottom-half), and what criteria would drive that split?

**Answer:** The guiding principle is that an ISR should do the minimum needed to acknowledge the hardware and hand off work, because it runs at high priority and blocks everything at or below its priority level. The longer an ISR runs, the more you hurt interrupt latency and jitter for the rest of the system.

So my criteria for what stays in the ISR: clearing the interrupt flag, reading a hardware register or FIFO into a small buffer, timestamping if needed, and signaling a deferred context. That's it. Anything that involves parsing, decision-making, blocking calls, dynamic allocation, or I/O to another peripheral should be deferred. A concrete rule of thumb: if the work could take longer than a few microseconds, or if it might ever block, it doesn't belong in the ISR.

For the deferred side, the choice between a thread, a work queue, or a bottom-half depends on the timing requirement and the context. A work queue is lightweight and runs in the system workqueue thread context, which is fine for non-urgent housekeeping. A dedicated thread with an appropriate priority is better when the work has real-time deadlines or needs to block on something (a mutex, a semaphore, a bus transaction). In Zephyr, `k_work` and its delayable/queueable variants cover a lot of cases, but if the deferred work needs its own stack and priority, a dedicated thread is cleaner.

The other thing I'd watch for is the handoff mechanism itself. A semaphore or a message queue from ISR to thread is the standard pattern, but you have to use the ISR-safe variants (`k_sem_give` is ISR-safe, but `k_sem_take` is not). And you need to think about what happens if the ISR fires again before the thread has consumed the previous signal — do you coalesce, queue, or drop? That decision is often more important than the ISR/deferred split itself.

**Possible follow-ups:**
- If an ISR needs to signal a thread but the thread might be busy, how would you avoid losing events without unbounded buffering?
- How would you measure whether your ISR execution time is actually within budget on the target hardware?

## Q3: You're implementing a peripheral driver that must move a continuous stream of data where per-transfer interrupts would consume too much CPU, but the buffer is too small to hold an entire acquisition. How would you approach configuring DMA for this?

**Answer:** This is the classic "ping-pong" or double-buffering problem, and the answer is to use DMA in a circular or dual-buffer mode so that the CPU is only interrupted when a buffer boundary is crossed, not per transfer.

The structure I'd use: two (or more) buffers of a size that balances latency against interrupt overhead. DMA fills buffer A while the CPU processes buffer B. When DMA finishes A, it raises an interrupt (or a half-transfer/transfer-complete pair of interrupts), the driver swaps roles, and processing continues on the newly filled buffer while DMA fills the other. This way the interrupt rate is tied to buffer size, not sample rate — a 10 kHz stream into 1 KB buffers generates interrupts at a manageable rate instead of 10,000 per second.

Key configuration considerations: the DMA channel needs to be set up for circular mode if the hardware supports it, or the driver must re-arm the transfer in the completion ISR. The buffer size should be chosen so that the CPU can process one buffer in less time than it takes DMA to fill the other — otherwise you get overrun regardless of how clever the buffering is. I'd also think about cache coherency if the MCU has a data cache: DMA writes to memory that the CPU may have cached, so you need cache invalidation on the buffer before reading it, or the buffer must be placed in non-cacheable memory. Getting this wrong produces the maddening symptom of data that looks correct in the debugger but is stale in the running code.

Finally, I'd handle the overrun case explicitly. If the CPU falls behind, the DMA will either overwrite unprocessed data or the hardware will flag an overrun. The driver should detect this and report it rather than silently dropping samples, because in a data acquisition context a dropped sample is a correctness problem, not just a performance one.

**Possible follow-ups:**
- How would you decide the buffer size, and what would you measure to confirm it's adequate?
- What changes if the DMA and CPU share a cache, and how would you verify coherency is handled correctly?

## Q4: A junior engineer has written a peripheral driver that works reliably on the bench but uses busy-wait loops to poll a status register until the peripheral is ready. They argue it's simpler and more deterministic than interrupt-driven code. How would you guide them toward a better approach without dismissing their concern about determinism?

**Answer:** I'd start by acknowledging that their instinct isn't wrong — busy-waiting *is* simple and *is* deterministic in the sense that the timing is predictable. The problem isn't the determinism, it's the cost: a busy-wait burns CPU cycles that could be doing other work, and in a system with multiple threads or real-time deadlines, that's a resource contention problem, not just an efficiency one. So I'd frame the conversation around what the busy-wait is *preventing* the rest of the system from doing, rather than around "polling is bad."

Then I'd look at the specific case. If the wait is genuinely short — a few microseconds for a register to settle — a bounded busy-wait is sometimes the right answer, and I'd say so. The issue is when the wait is unbounded or long: waiting for a peripheral that might take milliseconds, or worse, might never become ready if something is wrong. An unbounded busy-wait is a hang waiting to happen, and in a medical device that's a safety concern.

For the fix, I'd steer toward a pattern that preserves determinism while freeing the CPU: either an interrupt-driven completion (the peripheral signals when ready, the driver's ISR or a deferred handler proceeds), or a bounded poll with a timeout that returns an error rather than spinning forever. If the concern is that interrupt-driven code is harder to reason about, I'd point out that a bounded poll with a timeout is actually *more* deterministic than an unbounded one, because its worst-case execution time is known. And I'd offer to pair on converting one driver as a template, so they can see the pattern rather than just being told to change it.

The meta-point I'd want to land: the goal isn't "always use interrupts," it's "never let the CPU spin on something that might not happen." That framing usually gets buy-in because it's about correctness, not style.

**Possible follow-ups:**
- How would you decide the timeout value for a bounded poll, and what should the driver do when it expires?
- If the peripheral's ready time is genuinely sub-microsecond, would you still push for interrupts, and why or why not?

## Q5: How would you approach a situation where a firmware feature you own is blocked because a hardware change you depend on keeps slipping, and the schedule pressure is to ship the firmware anyway?

**Answer:** The first thing I'd do is separate the technical question from the schedule question, because they get tangled and the tangle is what causes bad decisions. Technically: what exactly does the firmware depend on, and is there a way to make progress that doesn't require the final hardware? Often there is — a hardware abstraction layer, a mock or simulation of the missing piece, or a bench setup that approximates the real behavior. If I can decouple the firmware from the specific hardware revision, I can develop and test most of the feature now and integrate when the hardware lands. That's usually the highest-value move, because it converts a blocked dependency into a smaller integration task.

If the dependency genuinely can't be decoupled, I'd want to be explicit about what "ship anyway" would mean. Shipping firmware that hasn't been validated against the hardware it's supposed to run on isn't shipping a feature — it's shipping risk, and in a regulated context that risk has a name and a paper trail. So I'd push back on the framing, but constructively: rather than just saying "we can't," I'd bring options. Can we ship a reduced version of the feature that doesn't depend on the missing hardware? Can we ship with the feature disabled and enable it in a follow-up once hardware is validated? Can we get a partial hardware revision or a dev board that covers most of the dependency?

I'd also make sure the schedule risk is visible to the people who own the decision. If the hardware slip is the real cause of the schedule pressure, that needs to be on the record, not absorbed silently by the firmware team. The worst outcome is shipping something unvalidated and having the failure attributed to firmware later. So I'd document the dependency, the validation gap, and the options, and push the decision to the level where the trade-off can actually be made — while continuing to make whatever progress is genuinely possible in the meantime.

**Possible follow-ups:**
- How would you build a mock or simulation of missing hardware without it becoming a maintenance burden or diverging from the real thing?
- If leadership decides to ship without full hardware validation, how would you document the residual risk so it's traceable?