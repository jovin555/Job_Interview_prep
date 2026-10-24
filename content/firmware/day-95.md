# firmware — Day 95

## Q1: How would you approach designing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core problem is that an edge on a GPIO line is not the same thing as valid data being available — the line is a hint, not a guarantee. I'd treat the interrupt as a trigger to *check*, not a trigger to *act*, and layer validation on top of it.

The first layer is at the ISR: keep it minimal. On the edge, don't read the data payload in the ISR at all — just timestamp the event, increment a counter, and signal a deferred context (a work item, a semaphore, or a thread notification). This keeps interrupt latency bounded regardless of what the peripheral is doing and gives you a place to do the expensive validation.

The second layer is validation in the deferred context. Before accepting the sample, confirm the peripheral's own status register actually reports data-ready, and validate the payload — length, CRC or checksum, and range plausibility. A spurious edge will typically fail one of these checks: the status bit won't be set, or the payload will be stale/garbage. If validation fails, discard the sample and count it as a rejected event rather than treating it as an error condition.

The third layer is rate limiting and debouncing. If glitches are physically plausible (long cable, noisy environment, slow edge), I'd consider a small time window after an accepted sample during which further edges are ignored — but only if the sensor's real data rate makes that safe. I'd also look at the hardware side: a Schmitt-trigger input, a small RC filter, or a pull resistor can eliminate many glitches before firmware ever sees them, and that's usually cheaper and more robust than handling them in software.

The key design principle is that the firmware must be correct even if the edge signal is unreliable — the edge is an optimization for latency, and the status register plus payload validation is the source of truth. I'd also make the rejected-event count observable (a diagnostic counter, a log entry at low rate) so that if glitch rates rise in the field, you find out before it becomes a data-integrity problem.

**Possible follow-ups:**
- If the glitch rate is high enough that rejected events dominate, how would you decide whether to fix it in hardware or keep absorbing it in firmware?
- How would you distinguish a spurious edge from a genuine data-ready event that arrives while you're still processing the previous one?

## Q2: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the first instinct should be to suspect that attaching the debugger changes timing, power state, or memory layout — not that the debugger is "fixing" anything. I'd work through the likely mechanisms systematically.

The most common cause is timing. A debugger halts the core at breakpoints and single-steps, which stretches out every operation and can mask a race condition, a missing delay, or a peripheral that needed more settling time than the code allowed. If the failure is a race, the debugger's slowdown hides it. I'd look for shared state without proper synchronization, ISR/main-loop interactions, and any place where the code assumes an operation completes faster than it actually does.

The second common cause is that the debugger changes the power and clock state. Many debug probes hold the device out of deep sleep, keep a clock running, or prevent a low-power mode from being entered. If the bug only appears when the device actually sleeps, the debugger is masking it by keeping it awake. I'd check whether the failure correlates with sleep entry, clock gating, or a regulator state change.

The third is memory layout and initialization. Debug builds and debugger-attached runs can differ in stack usage, heap placement, and uninitialized-memory contents. A bug that depends on a particular garbage value in RAM, or on a stack overflow that only manifests with a different stack depth, can appear or disappear based on build and attach state.

My practical approach: first, reproduce standalone with instrumentation that doesn't halt the core — GPIO toggles, a ring buffer of timestamped events in RAM that I can dump after the fact, or a serial log at low rate. Second, compare the two builds' map files and stack usage. Third, if I suspect timing, deliberately slow the standalone build (add NOPs, lower the clock) to see if the failure follows the timing change. Fourth, use the debugger's ability to *watch* without halting where possible — data watchpoints that log rather than break, or trace output if the MCU supports it.

The mindset is: the debugger is a variable, not a tool that reveals truth. The standalone behavior is the real behavior, and the debugger-attached behavior is the anomaly to explain.

**Possible follow-ups:**
- How would you build in-flight instrumentation that survives a crash so you can see what happened without a debugger attached?
- If the bug only reproduces once every several hours, how would you structure your investigation so you're not just waiting?

## Q3: How would you approach deciding whether a piece of firmware logic belongs in an interrupt service routine versus a deferred context such as a work queue or a thread?

**Answer:** The default should be that ISRs do the minimum necessary to acknowledge the hardware and hand off work; almost everything else belongs in a deferred context. The decision comes down to a few concrete criteria.

The first criterion is latency requirement. If the logic must complete within a hard deadline measured in microseconds — clearing a status flag before the next event arrives, capturing a timestamp, reading a FIFO before it overflows — it may need to be in the ISR. But "must happen fast" and "must happen in the ISR" are different things; often the fast part is a single register read and the rest can be deferred.

The second is duration and blocking behavior. Anything that can block — taking a mutex, waiting on a semaphore, doing a flash write, calling into a driver that might sleep — cannot be in an ISR at all. Anything that takes more than a few microseconds of CPU time should be deferred, because ISR duration directly adds to interrupt latency for every other interrupt in the system, including higher-priority ones.

The third is reentrancy and shared state. ISR code runs in a context that can preempt anything, so any data it touches must be safe against concurrent access. Deferring to a thread lets you use normal synchronization primitives and keeps the concurrency model simple.

The fourth is priority and scheduling. A work queue or a dedicated thread lets you assign a priority to the deferred work and let the scheduler arbitrate between it and other tasks. In an ISR, you have no such control — you're at whatever priority the interrupt controller assigned.

A practical pattern I'd use: the ISR captures the event (timestamp, status, maybe a byte or a pointer to a buffer), signals a deferred context, and returns. The deferred context does parsing, validation, state machine transitions, logging, and anything that touches shared data structures. If the deferred work is latency-sensitive, I'd use a high-priority thread or a dedicated work queue rather than the system work queue, so it isn't stuck behind unrelated work.

The one thing I'd watch for is the case where deferring adds unacceptable latency — for example, a control loop that must respond within a few microseconds. In that case the "ISR" is really the control loop itself, and the design should reflect that: keep it tiny, make it deterministic, and push everything else out.

**Possible follow-ups:**
- How would you measure whether an ISR is taking too long, and what would you do if it is?
- What's the difference between a work queue and a dedicated thread for deferred work, and when would you choose one over the other?

## Q4: How would you approach designing a firmware module that must survive a brownout — where the supply voltage sags briefly but doesn't fully drop — without corrupting persistent state or producing a spurious reset?

**Answer:** A brownout is dangerous precisely because it's ambiguous: the supply is low enough that the MCU may be operating out of spec, but not low enough to trigger a clean reset. The design goal is to detect the condition early, get into a safe state before the MCU's behavior becomes undefined, and make sure persistent state is either fully committed or not touched at all.

The first line of defense is hardware-assisted detection. Most modern MCUs have a brownout detector (BOD) or a programmable voltage detector (PVD) that can generate an interrupt at a threshold above the MCU's minimum operating voltage. I'd configure it to fire an interrupt with enough margin that firmware has time to react — the threshold has to be chosen so that the interrupt fires while the core is still reliably executing, not after. If the part doesn't have one, an external supervisor IC or an ADC monitoring the supply rail can serve the same purpose.

The second line is the response to that interrupt. The ISR should be minimal and non-allocating: set a flag, stop any in-progress flash or EEPROM write if the hardware allows it, and put outputs into a safe state (disable actuators, park motors, signal the host if possible). It should *not* try to do a graceful shutdown with logging and cleanup — there may not be enough energy left for that, and a half-completed flash write is worse than no write.

The third line is persistent-state discipline. The rule is that any persistent write must be atomic from the perspective of a reader after reset. That means either a journaling scheme (write to a scratch area, then commit with a single small write that's the "valid" marker), a double-buffered scheme with a sequence number and CRC, or a filesystem that provides atomic rename semantics. On boot, the firmware validates the persistent state and falls back to the last known-good copy if the current one is incomplete or fails CRC. This is the same discipline you'd use for power-loss tolerance generally — brownout is just one cause of an interrupted write.

The fourth line is reset behavior. If the brownout is severe enough that the BOD resets the device, the reset cause register should be read and logged so the event is visible. A spurious reset that nobody notices is a reliability problem hiding in plain sight. I'd also make sure the boot path is robust to being entered from a brownout — re-initialize peripherals from scratch rather than assuming any state survived, and don't trust RAM contents unless the retention domain is explicitly designed for it.

The overall principle: assume the supply can sag at any moment, design persistent writes to be atomic, and use the earliest available warning to get to a safe state rather than trying to finish what you were doing.

**Possible follow-ups:**
- How would you test brownout behavior without a programmable supply, and what would you look for in the results?
- If the MCU has no brownout detector, what's your fallback strategy and what are its limitations?

## Q5: You're leading a firmware team that is transitioning from a bare-metal approach to using Zephyr RTOS for a new medical device. Two senior engineers disagree: one wants to port the existing bare-metal drivers directly into Zephyr as custom drivers, while the other wants to rewrite them using Zephyr's native driver model. How would you guide the team to a decision?

**Answer:** I'd start by reframing the disagreement — it's not "port vs. rewrite" as a binary, it's a question of which drivers benefit from the native model and which are better served by a thin custom layer, and that depends on the driver and the risk profile. My job as lead is to make that trade-off explicit and drive it to a decision the team owns, not to pick a side.

First, I'd get both engineers to articulate the criteria they're actually optimizing for. The "port directly" argument usually rests on schedule, proven behavior, and avoiding regression in code that's already been validated — which matters a lot in a medical device where the existing driver may have regulatory history. The "rewrite native" argument usually rests on maintainability, getting power management and device tree integration for free, and not fighting the RTOS's assumptions. Both are legitimate; the question is which criteria dominate for each driver.

Second, I'd categorize the drivers. A simple sensor driver with a clean register interface is a good candidate for the native model — the boilerplate is well-understood, the device tree integration pays off, and the risk of regression is low. A complex driver with tight timing, unusual hardware sequencing, or validated safety behavior is a candidate for a thin custom layer that keeps the proven logic intact and only adapts the RTOS-facing parts (init, power hooks, API surface). The native model doesn't require you to throw away working logic — you can wrap it.

Third, I'd set a decision rule and a review gate. For each driver, the owner writes a short note: what the native model buys us, what the port risks, and which we're choosing. That forces the discussion onto specifics instead of abstractions. I'd also make sure the team agrees on what "done" means for a driver in the new architecture — device tree binding, power management hooks, error handling conventions — so the choice doesn't become a backdoor for skipping integration work.

Fourth, I'd protect the schedule by sequencing: pick one or two representative drivers, do them both ways if the team can afford it, and let the results inform the rest. A small pilot is cheaper than a philosophical argument.

Finally, I'd make clear that the decision is revisitable. If a "port directly" driver turns out to fight the RTOS at every turn, we revisit; if a "rewrite native" driver turns out to be a schedule sink, we revisit. The goal is a coherent architecture, not winning the argument.

**Possible follow-ups:**
- How would you handle it if the engineer who "lost" the argument is the one who has to implement the chosen approach?
- What would you do if the pilot showed the native model was clearly better but the schedule couldn't absorb the rewrite for the remaining drivers?