# firmware — Day 90

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt rate is high enough that servicing every interrupt individually would consume an unreasonable share of CPU time?

**Answer:** The first step is to quantify the problem rather than assume it: measure the actual interrupt rate, the per-ISR cost (entry/exit overhead plus the work done), and the resulting CPU utilization. If servicing every interrupt would consume, say, more than a few percent of CPU in a system with other real-time obligations, the design needs to change. There are several standard strategies, and the right one depends on the peripheral and the data characteristics.

The most common approach is to move bulk data with DMA and let the ISR fire only on a block-complete or half-transfer event rather than per byte or per sample. This amortizes interrupt overhead across many samples and is the natural fit for streaming peripherals like ADCs, SPI sensors, or UARTs. The ISR then just signals a consumer (a thread or work queue) that a buffer is ready, and the actual processing happens in deferred context.

If DMA isn't available or appropriate, the next lever is to reduce the interrupt rate at the source: configure the peripheral's FIFO or watermark so it interrupts only when a meaningful amount of data has accumulated, rather than on every sample. Many peripherals support this natively.

A third option is interrupt coalescing in software — the ISR does the minimum possible work (e.g., sets a flag or pushes a timestamp) and defers everything else, so the ISR itself is short even if it fires often. This doesn't reduce the interrupt count but reduces the cost per interrupt, which may be enough.

The key trade-off is latency versus overhead. Batching always adds some latency between data arrival and processing, so you have to confirm the application can tolerate it — for a control loop, that latency budget may be tight; for logging or telemetry, it's usually fine. I'd also watch for the failure mode where the ISR is short but still fires so often that context-switch overhead alone dominates; at that point the only real fix is reducing the event rate, not optimizing the handler.

**Possible follow-ups:** How would you decide between half-transfer and full-transfer DMA interrupts for a streaming ADC? What would you do if the peripheral has no FIFO and no DMA support at all?

## Q2: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core principle is that the edge is a hint, not proof — the firmware should never treat the interrupt itself as evidence that valid data exists. The ISR should do the minimum: record that an edge occurred (a counter, a timestamp, a flag) and defer the actual read to a thread or work queue. The deferred handler then validates the data before using it.

Validation depends on what the peripheral offers. If there's a status register with a "data ready" or "valid" bit, read it and only proceed if it's set — a spurious edge will typically show up as "no data ready" and can be discarded. If the data has a checksum or CRC, verify it. If the data has a plausible range or a sequence number, check that too. The point is to have at least one independent confirmation beyond the edge itself.

For the glitch specifically, I'd also look at the hardware side: is there a pull-up or pull-down that keeps the line in a defined state when idle? Is there any debounce or filtering available in the GPIO or peripheral configuration? Some MCUs let you configure input filtering or a minimum pulse width, which can reject very short glitches in hardware before they ever reach the interrupt controller. That's often cleaner than handling them in software.

I'd also instrument the system to count edges versus valid reads, so that if the glitch rate changes (e.g., due to a noisy environment or a marginal connection), it's visible rather than silently degrading. And I'd make sure the ISR clears the interrupt flag properly — a missed clear can cause the ISR to re-enter immediately, which looks like a glitch storm but is actually a firmware bug.

**Possible follow-ups:** What would you do if the peripheral has no status register and no checksum, so the only signal is the edge itself? How would you distinguish a genuine glitch from a marginal electrical connection that's producing real but unreliable edges?

## Q3: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** Stack sizing is one of those things where "it works in testing" is not the same as "it's correct," because stack overflows often manifest as corruption elsewhere rather than a clean crash. I'd approach it in layers.

First, establish a baseline analytically: estimate the worst-case call depth for each thread, including interrupt nesting if the thread can be preempted by ISRs that use the same stack (on some architectures ISRs use the current thread's stack, which is a critical detail). Add space for local variables, saved context, and any library calls — printf-family functions and floating-point operations are notorious stack hogs. This gives a starting number, not a final one.

Second, measure empirically. Zephyr provides stack usage analysis — `CONFIG_THREAD_ANALYZER` and the `k_thread_stack_space_get()` API let you query high-water marks at runtime. I'd run the system through its full range of operating modes, including error paths and rare branches, and record the worst-case usage per thread. The error paths matter most because they're the least exercised and often the deepest.

Third, add margin. A common rule is 25–50% headroom over the measured worst case, more for threads that call into libraries or handle variable-size data. The margin accounts for the fact that measurement only covers what you exercised.

Fourth, enable stack sentinel checking (`CONFIG_THREAD_STACK_INFO` with canaries) and, if available, MPU-based stack guards so that an overflow traps immediately rather than silently corrupting adjacent memory. In development, I'd also consider filling stacks with a known pattern and checking it periodically.

The verification step is what separates "probably enough" from "correct": the high-water measurement across all modes, plus the sentinel/guard, plus a deliberate stress test that exercises the deepest paths. If I can't exercise a path, I size that thread conservatively and document why.

**Possible follow-ups:** How does interrupt stack usage factor into thread stack sizing on your architecture? What would you do if a thread's measured high-water mark keeps creeping up release over release?

## Q4: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the first instinct — "the debugger changes timing" — is usually right but too vague to act on. I'd break it into categories of what the debugger actually changes and test each.

The most common cause is timing. With a debugger attached, the CPU runs slower, breakpoints add delays, and the debugger may halt peripherals. That can mask a race condition, a setup/hold violation on an external bus, or a peripheral that needs a delay before it's ready. To test this, I'd add instrumentation that doesn't require halting — GPIO toggles or a spare UART logging timestamps — and compare the standalone behavior against the debugger-attached behavior at the same points. If the standalone version is simply running faster and hitting a race, the fix is usually proper synchronization or a wait-for-ready check rather than a delay.

The second category is debugger side effects on hardware state. Some debuggers hold peripherals in reset, disable watchdogs, or change clock configuration when attached. If the device misbehaves standalone, I'd check whether the watchdog is being serviced correctly, whether low-power modes are being entered (the debugger often prevents sleep), and whether any peripheral initialization depends on the debugger being present. A common one: the debugger keeps the core from entering deep sleep, so a wake-up bug only appears standalone.

The third category is code generation differences — optimization level, or code that relies on undefined behavior that happens to work one way with the debugger's timing. Running the standalone build with the same optimization settings as the debug build (and vice versa) can isolate this.

I'd also check whether the "misbehavior" is actually a reset, a hang, or wrong data — each points somewhere different. Capturing a fault log or a post-mortem snapshot on the standalone device is often the fastest way to see what actually happened rather than inferring it.

**Possible follow-ups:** How would you capture diagnostic information from a device that misbehaves only when no debugger is attached? What's the first thing you'd check if the misbehavior correlates with the device entering low-power mode?

## Q5: How would you approach a situation where you discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules?

**Answer:** The first thing is to be honest and early about it — the worst outcome is letting it surface during integration or, worse, after release. I'd start by quantifying the problem precisely: what specifically is failing, what's the cost of the current design in terms of defects, schedule, or risk, and what would the rework actually involve. "Significant problems" needs to become a concrete list so the decision is based on evidence rather than a vague sense of unease.

Then I'd lay out the options honestly. There's usually a spectrum: a full refactor, a partial refactor that isolates the problem area behind a cleaner interface, a workaround that contains the damage without fixing the root cause, or accepting the cost and shipping with the known limitation documented. Each has a different cost and risk profile, and the right choice depends on where the project is, what the regulatory or safety implications are, and what the team can realistically absorb.

I'd bring this to the relevant stakeholders — project lead, quality/regulatory if it's a medical device, and the engineers who'd do the work — with a clear recommendation rather than just a problem statement. For a medical device especially, a design decision that affects safety or traceability can't be quietly worked around; it needs to go through the change control process.

If the decision is to do the rework, I'd sequence it to reduce risk: introduce the new interface or abstraction first, migrate modules one at a time behind it, and keep the system testable at each step. If the decision is to contain rather than fix, I'd make sure the limitation is documented, tested around, and captured as technical debt with a plan — not just forgotten.

The behavioral piece is owning it without being defensive. A design decision that looked right early and turned out wrong is normal engineering; what matters is surfacing it clearly and driving a decision rather than hoping it goes away.

**Possible follow-ups:** How would you decide between a full refactor and a containment workaround when the schedule is tight? How would you communicate the risk to a stakeholder who isn't technical?