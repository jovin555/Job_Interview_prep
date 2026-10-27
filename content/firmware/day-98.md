# firmware — Day 98

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt rate is high enough that servicing every interrupt individually would consume an unreasonable share of CPU time?

**Answer:** The first step is to quantify the problem rather than assume it: measure the actual ISR entry/exit cost plus the work done per interrupt, multiply by the interrupt rate, and compare that against the CPU budget. If the ISR is genuinely eating too much time, there are several levers, and the right one depends on what the peripheral actually needs.

The most common fix is to reduce the number of interrupts rather than make each one faster. If the peripheral supports it, switch to a FIFO or burst mode so one interrupt covers many samples or bytes instead of one. If the peripheral has a DMA engine, move the data movement entirely to DMA and use a "half-transfer" and "transfer-complete" interrupt pair — that converts N per-sample interrupts into two per buffer, and the CPU only touches the data when a block is ready. For a receive path where the peripheral can't buffer, a common pattern is to keep the ISR minimal — read the data register, push into a lock-free ring buffer, clear the flag — and defer all processing to a thread or work queue. That doesn't reduce the interrupt count, but it shrinks the per-interrupt cost dramatically.

If the interrupt rate is fundamentally too high even with a minimal ISR, the next question is whether the peripheral can be reconfigured: lower the sample rate, use a hardware filter or decimation stage, or aggregate in the peripheral itself. Sometimes the honest answer is that the hardware configuration is wrong for the job and the fix is at the board or peripheral-configuration level, not in software.

I'd also watch for the failure mode where the ISR is doing more than it needs to — logging, formatting, calling into a driver layer that takes a mutex, or doing floating-point math. Those are the classic culprits, and moving them out is usually the highest-leverage change. Throughout, I'd instrument: count interrupts per second, measure ISR duration with a GPIO toggle or a cycle counter, and confirm the fix actually moved the number before declaring victory.

**Possible follow-ups:**
- How would you decide between DMA and a larger peripheral FIFO if both are available?
- What would you do if the interrupt rate is high but bursty, so the average CPU load looks fine while the worst case is not?

## Q2: How would you approach designing a watchdog strategy for a device that must distinguish between a genuine firmware hang and a legitimate but slow operation, without simply extending the timeout until the watchdog becomes meaningless?

**Answer:** The core principle is that the watchdog should be kicked by evidence that the system is healthy, not by the passage of time in a loop. If the only thing that kicks the watchdog is "the main loop reached the top again," then a slow operation that blocks the loop looks identical to a hang, and the temptation is to keep raising the timeout until the watchdog stops catching anything real.

A better structure is a multi-source or "check-in" watchdog. Each subsystem that must prove liveness registers a check-in — a sensor task, a comms task, a control loop — and the watchdog is only kicked when all registered check-ins have reported within their expected windows. A slow flash erase in one subsystem then doesn't starve the others, and a genuinely stuck subsystem stops checking in and trips the watchdog. This is the pattern behind windowed watchdogs and the "watchdog petting" schemes in larger RTOSes; the important part is that the kick condition is a conjunction of independent liveness signals, not a single loop counter.

For the legitimate-but-slow operation specifically, the right move is to make the slow operation *cooperate* with the watchdog rather than fight it. Options include: breaking the operation into chunks with a check-in between chunks; running it in a context that is allowed to report "I'm in a long operation, expect me late" via a separate progress channel; or, if the hardware supports it, using a windowed watchdog where the kick must arrive within a window — too early is also a fault, which catches the case where a task is spinning and kicking too fast. The key is that the watchdog still has a bounded, meaningful timeout; the slow operation is accommodated by design, not by inflating the timeout.

I'd also make sure the watchdog is not disabled in production, that the reset cause is logged and readable after reboot, and that there's a clear policy for what happens on a watchdog reset in a medical context — typically a safe state and an audible/visual indication, not a silent retry loop.

**Possible follow-ups:**
- How would you handle a subsystem that legitimately has a very long worst-case latency, longer than any reasonable watchdog window?
- What are the trade-offs of a windowed watchdog versus an independent (non-windowed) one in an embedded medical device?

## Q3: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the debugger's presence changes several things at once, so the first job is to figure out *which* change is masking the bug. The usual suspects are timing, memory layout, and power state.

Timing is the most common. With a debugger attached, the core may be halted at breakpoints, single-stepping slows execution, and the debug probe itself can add latency to bus accesses. That can hide a race condition, a setup/hold violation on an external bus, or a peripheral that needs a delay the code doesn't actually provide. A good first experiment is to run standalone but add a deliberate, controlled delay or a GPIO toggle at suspect points to see if the failure reappears — if slowing the code down makes it fail, it's likely a timing or race issue, not a logic bug.

Memory layout is the second suspect. Attaching a debugger can change where the stack and heap land, which can mask a stack overflow or an out-of-bounds write that happens to land in harmless memory when the debugger is present. Checking the stack high-water marks, enabling stack canaries or MPU-based stack guards, and comparing the memory map with and without the debugger is worthwhile.

Power state is the third. Debuggers often keep certain clocks or debug peripherals alive, which can prevent the device from entering the low-power state where the bug lives. If the failure only happens standalone, I'd check whether the device is actually reaching the sleep mode I think it is, and whether a wake-up source or a clock that's gated in sleep is behaving differently.

Practically, I'd move toward standalone observability: a ring buffer or flash log of state transitions and error codes that survives the failure, a GPIO or spare UART as a poor-man's trace, and if available, a hardware trace unit (ETM/SWO) that doesn't perturb timing the way a breakpoint does. The goal is to reproduce the failure with instrumentation that doesn't change the thing being measured.

**Possible follow-ups:**
- How would you distinguish a race condition from a timing-margin problem when both look like "works with debugger, fails without"?
- What would you log to a persistent buffer to make a standalone failure diagnosable after the fact?

## Q4: A junior engineer has written a driver that works reliably on the bench but uses a fixed `k_sleep` delay to wait for a peripheral to become ready after each command, rather than checking a status register or using an interrupt. How would you guide them?

**Answer:** I'd start by acknowledging what's right about their instinct: a fixed delay is simple, deterministic in the sense that it's easy to reason about, and it does work on the bench. The conversation is not "this is wrong," it's "here's what this costs you and where it breaks."

The first issue is that a fixed delay is a guess about the worst case, and worst cases move. The peripheral's ready time may depend on temperature, supply voltage, part-to-part variation, or the specific command — so a delay tuned on one board can be marginal on another, and the failure mode is intermittent and hard to attribute. The second issue is that `k_sleep` in a thread yields the CPU, which is fine, but a busy-wait delay blocks it entirely; either way, the delay is dead time that scales with how often the command is issued. The third is that a fixed delay hides the real signal: if the peripheral is ready early, you're wasting time; if it's late, you fail silently.

The better pattern is to wait on the actual condition with a bounded timeout: poll the status register with a short yield between polls, or better, use the peripheral's interrupt or a completion semaphore, and always with a timeout so a stuck peripheral produces an error rather than a hang. In Zephyr that's typically a `k_sem_take` with a timeout, or a `k_poll` on the relevant event, with the ISR giving the semaphore. The timeout value should come from the datasheet's worst case plus margin, and the code should handle the timeout path explicitly — log it, return an error, and let the caller decide whether to retry or degrade.

I'd frame it as a progression: fixed delay → bounded poll → interrupt/semaphore with timeout. Each step is a small change, and the junior engineer can see the benefit at each step. I'd also point out that the timeout path is where the real robustness lives, and that a driver without a timeout path is a driver that can hang the device.

**Possible follow-ups:**
- How would you choose the timeout value, and what would you do if the datasheet doesn't specify a worst case?
- What's the difference between a `k_sleep`-based poll and a semaphore-based wait in terms of CPU usage and latency?

## Q5: How would you approach a situation where you discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules?

**Answer:** The first thing I'd do is resist the urge to either panic-fix or quietly work around it. The decision to change an early architectural choice late in a project is a risk trade, and it needs to be made with data, not adrenaline.

I'd start by characterizing the problem precisely: what specifically is failing, how often, and what's the cost of *not* changing it — field failures, regulatory risk, maintenance burden, or just schedule pain. Then I'd scope the rework honestly: which modules are affected, what the change actually touches, and what the test and validation impact is. In a regulated medical context, a late change to a core design decision also has a documentation and verification cost, so that has to be in the estimate.

With that in hand, I'd lay out the options rather than presenting a single "we must rewrite" or "we must live with it." Typically there are three: fix it properly now (highest cost, highest confidence), contain it with a targeted workaround and schedule the proper fix for the next revision (lower immediate cost, carries known debt), or defer and accept the risk with a documented rationale. I'd bring the trade-off to the people who own the schedule and the risk — the project lead, and in a medical context the quality/regulatory owner — rather than deciding unilaterally, because the right answer depends on factors outside firmware.

If the decision is to change it, I'd do it incrementally: introduce the new abstraction alongside the old one, migrate modules one at a time behind tests, and keep the system shippable at each step. That's slower than a big-bang rewrite but far less likely to produce a late-project regression that nobody can diagnose. If the decision is to contain it, I'd make the workaround explicit and documented — a known-issue entry, a test that pins the behavior, and a clear owner for the eventual fix — so it doesn't quietly become permanent.

The honest reflection afterward is about why the decision looked right early and what signal was missed, and whether the process had a checkpoint where it could have been caught sooner. That's the part that prevents the next one.

**Possible follow-ups:**
- How would you decide whether a late architectural change is worth the schedule risk in a regulated medical device?
- What would you do if the people who own the schedule disagree with your assessment of the risk?