# space-rad-hard — Day 86

## Q1: How would you approach designing a radiation-tolerant analog-to-digital conversion subsystem where the ADC's voltage reference is a COTS part with no radiation data, and the measurement must hold accuracy over a multi-year mission?

**Answer:** The reference is often the weakest link in a precision measurement chain, so I'd treat it as a first-class risk item rather than an afterthought. With no radiation data, I can't assume the part behaves — I have to either characterize it, bound its behavior analytically, or design around it.

First, I'd quantify what accuracy the measurement actually needs and how much of the error budget the reference is allowed to consume. A reference that drifts with TID or shows enhanced low-dose-rate sensitivity (ELDRS) will shift the entire transfer function, and unlike offset or gain errors in the ADC itself, a reference shift is common-mode across all channels — you can't calibrate it out per-channel unless you have an independent, radiation-stable way to measure the reference itself.

Options I'd weigh:
- **Characterize it.** Even a limited low-dose-rate test at a facility, or a biased anneal test, gives far more confidence than a datasheet with no radiation section. If budget is tight, I'd test a small sample at the expected mission dose and look specifically for ELDRS signature (degradation that's worse at low dose rate than high).
- **Design for ratiometric operation.** If the ADC and the sensor excitation share the same reference, reference drift cancels to first order in a ratiometric measurement. That's often the cheapest mitigation and doesn't require a rad-hard reference at all.
- **Add an independent monitor.** A radiation-stable bandgap or a second reference on a different process node, cross-checked periodically, lets firmware detect and compensate for reference drift — but only if the monitor itself is trustworthy.
- **Choose a reference with a known-good process.** Some references are built on processes with published TID data even if the specific part isn't characterized; that's weaker evidence than part-level data but better than nothing.

I'd also consider the reference's transient behavior: a single-event transient on the reference output can inject a spurious reading into a control loop, so I'd add filtering and, if the measurement is time-critical, a plausibility check in firmware that rejects readings inconsistent with the previous sample and the physical rate of change of the measurand.

**Possible follow-ups:**
- How would you distinguish a reference drift from an ADC gain drift if both are present?
- If you can't test the reference at all, what's your fallback architecture?

## Q2: How would you approach designing a fault-tolerant power distribution scheme for a payload with multiple loads of different criticality, where a single-event latch-up (SEL) in any one load must not take down the rest of the system?

**Answer:** The core principle is that a SEL is a local fault and must be contained locally — the distribution architecture should never let one load's fault propagate upstream or sideways. I'd start by classifying loads by criticality and current profile, because the protection strategy differs for a 50 mA sensor versus a 3 A FPGA rail.

For each load or load group, I'd put a current-limited switch (an eFuse or a rad-tolerant load switch with programmable current limit and latch-off) between the bus and the load. The switch does three things: limits inrush at power-up, trips on overcurrent within a defined time, and can be commanded off and back on by the controller to attempt recovery. The trip threshold and response time have to be chosen so that a legitimate transient — inrush, a motor start, a capacitor charging — doesn't nuisance-trip, but a genuine latch-up is caught before it drags the rail down.

Layering matters:
- **Per-load protection** contains the fault.
- **Per-rail protection** (a second tier) catches the case where a load switch fails short or the fault is on the rail itself.
- **Upstream bus protection** (a third tier) protects the primary 28V bus and the rest of the spacecraft.

I'd also think about the recovery policy. A latch-up typically clears when power is removed, so the controller should be able to cycle the affected load switch, verify the load comes back within spec, and if it doesn't, leave it off and report the fault rather than repeatedly retrying into a hard short. Retry policy needs a backoff and a retry limit — infinite retries into a persistent fault just waste power and generate heat.

Finally, I'd make sure the fault detection and reporting path is independent of the load being protected, so a fault in the load can't blind the telemetry that would tell ground what happened.

**Possible follow-ups:**
- How would you size the current-limit threshold and trip time for a load with a large capacitive inrush?
- What happens if the load switch itself latches up?

## Q3: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** The argument conflates two different things: TMR protects against upsets in digital logic, but it does nothing for a single-event transient that corrupts the analog signal before it ever reaches the ADC. If the analog front-end produces a wrong voltage, the ADC faithfully digitizes the wrong voltage, and TMR downstream just replicates the wrong answer three times. Redundancy downstream of a single point of failure doesn't remove the single point of failure.

I'd walk through the failure modes the analog chain is actually exposed to:
- **SET in the amplifier** — a transient on the output that lasts microseconds to milliseconds, potentially long enough to be sampled.
- **SET in the ADC's sample-and-hold or reference** — a corrupted conversion.
- **TID drift** in the amplifier's offset, gain, or bias current over the mission.
- **Single-event latch-up** in the amplifier or ADC, which could drag the supply or produce a stuck output.

Then I'd ask what the control loop does with a corrupted measurement. If the loop has a slow time constant and the transient is short, a plausibility filter (rate-of-change limit, median-of-three, comparison against a redundant but non-identical sensor) may be sufficient. If the measurement is fast and safety-critical, I'd want genuine diversity — a second sensor on a different principle, or a second signal chain with a different amplifier topology — and a voting or cross-check scheme that compares the two before the value reaches the control law.

The key point I'd make in the review: redundancy has to be placed where the fault occurs, not where it's convenient. Digital TMR is necessary but not sufficient; the analog front-end needs its own protection strategy, and the two have to be designed together.

**Possible follow-ups:**
- How would you implement a plausibility filter without adding unacceptable latency to the control loop?
- What's the difference between redundancy and diversity, and why does it matter here?

## Q4: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt (SEFI) that leaves the processor still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** This is the hard case for watchdog design, because the usual "is the heartbeat toggling?" check passes even though the processor is functionally dead. The test plan has to reproduce that specific failure mode without a particle beam, and then verify the recovery mechanism actually catches it.

First, I'd define what "functionally dead but heartbeat alive" looks like in this system. It could be a corrupted program counter stuck in a tight loop that happens to include the heartbeat toggle, a corrupted stack pointer causing the control task to never run while an interrupt still fires the heartbeat, or a corrupted state variable that makes the control law a no-op. Each has a different signature.

To reproduce it on the bench, I'd use fault injection at the firmware level: a debug hook or a test build that deliberately corrupts the relevant state — for example, forces the control task to skip its update while leaving the heartbeat ISR running. That's not the same as a real SEFI, but it exercises the recovery path, which is what I actually need to verify.

Then I'd verify the recovery mechanism catches it. A simple heartbeat watchdog won't, so the design needs something more: a **task-level liveness check** where the control task must post a completion flag that the watchdog monitors, or a **challenge-response** where the watchdog asks the processor to compute something non-trivial and checks the answer, or a **cross-check** against an independent monitor that watches the actual output (e.g., the DAC output hasn't changed when it should have). The test plan should confirm that each of these mechanisms fires under the injected fault and that the recovery — reset, task restart, or safe-state entry — actually happens.

I'd also test the recovery itself: does the system come back to a known-good state, does it re-initialize the control loop safely, and does it log the event so ground can see it happened? A recovery that silently reboots without telemetry is almost as bad as no recovery.

**Possible follow-ups:**
- How would you test the case where the recovery mechanism itself is affected by the SEFI?
- What's the trade-off between a fast watchdog timeout and false trips during normal operation?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves respect — the goal isn't to win the argument, it's to get the right answer for the mission. If I come in with "this is wrong," I lose the room and probably the engineer's engagement for the rest of the project.

I'd start by asking questions rather than making assertions. "Walk me through how you arrived at this margin — what radiation environment did you assume, and what's the basis for the part's tolerance?" Often the gap is a missing input rather than a wrong calculation: the engineer may not have had the mission dose profile, or may have assumed a datasheet number that doesn't apply at low dose rate. Making that visible is more persuasive than telling them they're wrong.

If the disagreement is about a judgment call — how much margin is enough — I'd try to make it concrete. What's the consequence if the margin is consumed? Is it a degraded measurement, a latch-up, a loss of function? What's the cost of adding margin (BOM, board area, schedule)? Framing it as a risk trade-off rather than a correctness question usually moves the conversation forward.

If we still disagree after that, I'd escalate the decision to the appropriate forum — a formal risk review, or the systems lead — rather than let it stall. And I'd document the decision and the rationale, whichever way it goes, so that if the assumption turns out to be wrong we know why we made the call.

Throughout, I'd keep the tone collaborative: "help me understand," "what would change your mind," "what's the failure mode we're protecting against." The engineer's confidence is an asset if it's channeled into rigor; my job is to make sure the rigor is there, not to shut them down.

**Possible follow-ups:**
- What if the engineer is right and you're wrong — how do you make sure you'd recognize that?
- How do you handle it if the schedule pressure makes the "more margin" option infeasible?