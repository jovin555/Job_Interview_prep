# firmware — Day 78

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** The first step is to quantify the problem rather than assume it. I'd measure the actual interrupt rate, the worst-case ISR execution time, and the CPU headroom left for everything else. If the ISR is genuinely the bottleneck, the root cause is almost always that the ISR is doing too much work — parsing, buffering, or decision-making that belongs in a deferred context.

The standard remedy is to split the ISR into a minimal "capture" portion and a deferred "process" portion. The ISR does only what is timing-critical and cannot be deferred: reading the peripheral's data register, acknowledging the interrupt, and pushing the raw data into a lock-free ring buffer or a Zephyr `k_fifo`/`k_msgq`. Everything else — validation, scaling, state transitions, logging — moves to a thread or work queue that drains the buffer at its own pace.

If the interrupt rate is so high that even the minimal ISR plus the deferred drain cannot keep up, then interrupts are the wrong mechanism entirely. That's when I'd look at DMA: let the peripheral write directly into a buffer without CPU involvement per sample, and generate a single interrupt per block or per half-buffer. This converts an N-interrupts-per-second problem into an N/blocksize problem. For truly continuous high-rate streams, a circular DMA buffer with half-transfer and full-transfer interrupts is the classic pattern.

There's also a hardware angle worth checking: sometimes the "interrupt storm" is actually a misconfigured peripheral — an edge/level setting that re-triggers, or a status flag that isn't being cleared properly, so the ISR fires repeatedly for a single event. Before redesigning the software architecture, I'd confirm the interrupt count matches the expected event count.

**Possible follow-ups:**
- How would you size the ring buffer between the ISR and the deferred thread, and what happens when it overflows?
- What are the trade-offs between a work queue and a dedicated thread for the deferred processing?

## Q2: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the debugger's presence is itself a clue. Attaching a debugger changes several things: it may halt the core at breakpoints, it slows execution, it can mask timing-sensitive races, and it often disables or alters low-power modes. So the first hypothesis is usually a timing or race condition that the debugger's overhead happens to hide.

I'd start by characterizing the difference. Does the misbehavior correlate with a specific operation — a flash write, a sleep entry, a communication burst? Does it happen at a particular temperature or supply voltage? I'd add non-intrusive instrumentation: a GPIO toggled at key points, a trace buffer in RAM that survives until the fault, or a UART log at low baud so it doesn't perturb timing much. The goal is to observe the standalone behavior without the debugger's side effects.

A very common root cause is that the debugger keeps a clock or peripheral alive that the standalone firmware assumes is running, or conversely that the debugger prevents the core from entering a low-power state where a wake-up source is misconfigured. Another frequent culprit is uninitialized memory: with a debugger attached, the tool may zero RAM or the timing may let a variable get set before use; standalone, that variable holds garbage. I'd check the startup code and any variables that aren't explicitly initialized.

I'd also look at whether the debugger changes the reset behavior — some debug configurations hold the core in a different state at reset, which can mask a startup-order bug. Reproducing the fault standalone with a logic analyzer or a scope on the relevant signals is often the fastest way to see what's actually happening.

**Possible follow-ups:**
- How would you capture a trace of the failure if the device resets before you can read anything out?
- What startup-code issues commonly cause behavior that differs between debug and standalone runs?

## Q3: How would you approach implementing a firmware module that must timestamp events with millisecond resolution across a device that sleeps for long periods, where the timestamp must remain monotonic and must not be corrupted by the sleep/wake transition?

**Answer:** The core challenge is that the high-resolution timer you'd normally use for millisecond timing is often stopped or gated during deep sleep, while a low-power counter (like an RTC) keeps running but at coarser resolution. So the design usually combines two time bases: a fine-grained tick for millisecond resolution while awake, and a coarse but always-on counter for tracking elapsed time across sleep.

The standard approach is to maintain a monotonic software time base built from a hardware counter that does not stop in sleep. Many MCUs have a low-power timer or RTC that can be configured to count at a known rate and to keep running in the deepest sleep mode the application uses. If that counter's resolution is sufficient (or can be prescaled to give millisecond ticks), it becomes the single source of truth and the problem largely disappears. If it isn't fine enough, I'd use it as the "seconds" base and a separate high-speed timer as the "sub-second" base, then stitch them together carefully at each wake.

The stitching is where corruption creeps in. On wake, the fine timer has lost time, so I need to read the coarse counter, compute how much time elapsed during sleep, and advance the software time base by that amount — atomically, before any other code can read the timestamp. I'd protect the update with a critical section or a lock so a reader never sees a half-updated value. I'd also handle counter rollover explicitly, since a 32-bit counter at millisecond resolution wraps in about 49 days, and a device that sleeps for long periods will hit that.

For monotonicity, I'd never let the time base move backward — if a read of the coarse counter ever appears to go backward (due to a race or a counter reset), I'd clamp rather than trust it. And I'd store the time base in a way that survives a reset if the requirement is truly monotonic across power cycles, which usually means persisting it to non-volatile memory with a write strategy that tolerates power loss mid-write.

**Possible follow-ups:**
- How would you verify that the timestamp stays monotonic across thousands of sleep/wake cycles?
- What would you do if the only always-on counter has resolution coarser than the required millisecond precision?

## Q4: A junior engineer has written a driver that works reliably on the bench but uses a fixed `k_sleep` delay to wait for a peripheral to become ready after each command, rather than checking a status register or using an interrupt. How would you guide them?

**Answer:** I'd start by acknowledging that the code works and that fixed delays are genuinely simpler to reason about — that's a real virtue, and I don't want to dismiss it. Then I'd walk through where the approach breaks down, using concrete scenarios rather than abstract principles.

The first issue is that a fixed delay is a guess about the worst case. It's correct only if the peripheral is always ready within that time, under every condition — temperature, supply voltage, part-to-part variation, and aging. If the datasheet's maximum is longer than the delay, the driver fails intermittently and the failure is hard to reproduce. If the delay is much longer than typical, the driver wastes time on every command, which matters in a system with a real-time loop or a power budget. Either way, the delay encodes an assumption that isn't checked.

The second issue is that a blocking `k_sleep` in a high-priority thread stalls everything else at that priority. In a system with a control loop or other time-sensitive work, that's a scheduling hazard even if the delay is short.

The better pattern depends on the peripheral. If it exposes a status register or a ready bit, poll that with a timeout — the loop exits as soon as the device is ready, and the timeout bounds the worst case. If the peripheral can generate an interrupt, use it and block the thread on a semaphore or a Zephyr `k_poll`/`k_sem` with a timeout, so the thread sleeps until the event rather than guessing. Either way, the code becomes event-driven and the timing assumption is replaced by an actual check.

I'd frame it as: the fixed delay is a bet that the peripheral is always fast enough; polling or interrupts replace the bet with a measurement. I'd suggest they add a timeout to the polling version so a stuck peripheral doesn't hang the driver forever, and I'd point out that the same timeout logic makes the failure mode observable rather than silent.

**Possible follow-ups:**
- How would you decide between polling a status register and using an interrupt for a given peripheral?
- What would you do if the peripheral has no status register and no interrupt, only a fixed timing requirement?

## Q5: How would you approach a situation where you discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules?

**Answer:** The first thing I'd do is resist the urge to either hide it or immediately propose a rewrite. I'd quantify the problem: what specifically is failing or becoming unmaintainable, how much rework is actually required, and what the cost of not changing is — in defects, in schedule risk, in future feature velocity. A design decision that's merely inelegant is different from one that's causing real defects or blocking a requirement.

Then I'd lay out the options honestly. One option is to fix it properly now, accepting the rework. Another is to contain it — introduce an abstraction layer or adapter so the problematic decision is isolated and new code doesn't depend on it, then migrate incrementally. A third is to document it as known debt and defer, which is legitimate only if the cost of deferral is genuinely lower than the cost of fixing now, and if the risk is understood and accepted by the people who own the schedule.

I'd bring this to the team and stakeholders early, with the trade-offs laid out, rather than making the call unilaterally or waiting until it becomes a crisis. The conversation is easier when it's framed as "here's the problem, here are the options, here's what I recommend and why" rather than "I made a mistake." Owning the decision matters, but the goal is to get the right outcome for the project, not to protect anyone's ego.

If the decision is to fix it, I'd sequence the work to keep the system shippable throughout — migrate module by module behind an interface, with tests at each step, rather than a big-bang rewrite that leaves the codebase broken for weeks. If the decision is to defer, I'd make sure the debt is visible: a written record of what the decision was, why it's a problem, and what would trigger revisiting it.

**Possible follow-ups:**
- How would you decide whether to fix it now versus contain and defer?
- How would you keep the team's confidence if the rework affects their modules?