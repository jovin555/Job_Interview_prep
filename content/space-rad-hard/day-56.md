# space-rad-hard — Day 56

## Q1: How would you approach designing a latch-up protection scheme for a mixed-signal board where the sensitive analog front-end and the digital processing section share a common 3.3V rail, and a single-event latch-up in either section could drag the whole rail down?

**Answer:** The core problem is that a shared rail turns any single latch-up into a common-mode failure, so the first design decision is whether the two sections genuinely need to share a rail. If the analog front-end has tight noise requirements anyway, splitting into separate regulated rails — even if derived from the same upstream converter — is usually justified on signal-integrity grounds alone, and it gives you independent current limiting for free. Where a shared rail is unavoidable, I would treat protection as a layered scheme rather than a single device.

At the device level, the standard approach is a current-limiting switch or eFuse per load branch, sized so that the trip threshold sits above the branch's worst-case transient demand but below the level at which the rail collapses. The response time matters as much as the threshold: a slow-blow limit that takes milliseconds to act may already have dragged the rail below the brownout threshold of the other section. For the analog front-end specifically, I would also look at whether the process itself is latch-up resistant — epitaxial substrates and guard rings around I/O and power structures raise the holding current substantially — and derate the supply to the low end of the acceptable range, since latch-up susceptibility rises with supply voltage.

At the rail level, I would add a bulk hold-up capacitance sized to ride through the interval between latch-up onset and the protection tripping, so the digital section doesn't reset while the analog branch is being isolated. And I would make sure the protection is self-recovering or at least remotely resettable, because a latching protection scheme that requires a full power cycle is a mission risk in itself.

The other half of the answer is detection. You want the system to know a latch-up happened, not just survive it — a current-sense flag or a rail-monitor comparator feeding the housekeeping telemetry lets you characterize the event rate over the mission and decide whether the mitigation is actually working.

**Possible follow-ups:**
- How would you choose the trip threshold and response time, given that you also have to survive the inrush of the analog section's decoupling network at power-up?
- If the analog and digital sections must share a rail for architectural reasons, how would you partition the decoupling so a latch-up in one section doesn't starve the other?

## Q2: How would you approach derating and part selection for a space-deployed board, and how does derating interact with the radiation tolerance you're trying to achieve?

**Answer:** Derating and radiation tolerance are usually treated as separate workstreams, but they interact in ways that matter. Derating is the practice of operating a part below its rated stress — voltage, current, power, junction temperature, and often frequency — to buy margin against parameter drift, wear-out mechanisms, and the statistical spread of the manufacturer's limits. In a space context you're derating against a datasheet that was characterized at room temperature and often at sea level, so the derating factors have to account for the fact that the part will see vacuum, wide temperature swings, and a radiation field the manufacturer never tested.

The interaction with radiation is the interesting part. Total ionizing dose degrades parameters gradually — leakage currents rise, transconductance falls, reference voltages drift, timing margins shrink. A part that's derated to 50% of its voltage rating has more headroom to absorb that drift before it falls out of spec than one running at 90%. Similarly, derating junction temperature gives you margin against the increased leakage that TID produces, which itself adds to the thermal load. So derating isn't just a reliability practice layered on top of radiation tolerance — it's one of the mechanisms by which you tolerate radiation.

For part selection, the practical sequence is: define the radiation environment and the mission dose with margin, then look for parts with either a QML listing or published radiation test data covering the relevant environment. Where neither exists, you're into a qualification program — test the part, or accept the risk with a documented rationale. Derating factors should be applied on top of whatever the radiation data shows, not instead of it. And I'd want the derating analysis to be traceable: for each critical part, what's the applied stress, what's the rated stress, what's the derating factor, and what's the justification. That traceability is what makes the design reviewable and what makes it possible to revisit the decision if the mission profile changes.

**Possible follow-ups:**
- How would you handle a part where the radiation data exists but was taken at a different dose rate than your mission will see?
- Where would you draw the line between derating a COTS part and simply selecting a more expensive rad-hard equivalent?

## Q3: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** The argument conflates two different failure domains. TMR on the digital side protects against upsets in the logic that processes the measurement — it does nothing for an upset that corrupts the measurement before it ever reaches the logic. If the analog front-end produces a wrong value, TMR will faithfully replicate and vote on the wrong value. Redundancy downstream of a single point of failure doesn't remove the single point of failure.

So the first thing I'd want to establish is what the analog chain's actual failure modes are and how they propagate. A single-event transient on the amplifier or the ADC's sample-and-hold can produce a spurious reading that lasts one conversion cycle; whether that matters depends on the control loop's bandwidth and whether it has any filtering or plausibility checking. A TID-induced drift in the amplifier's offset or the ADC's reference is a slower, systematic error that TMR can't see at all. And a latch-up in the analog section is a hard failure that takes the whole chain down regardless of what the digital side does.

The right response isn't necessarily "add TMR to the analog side" — analog TMR is expensive and awkward. It's more often a combination of: rate-of-change or plausibility limits on the measurement before it's used, so a single spurious sample can't drive the actuator; a redundant or diverse second measurement path where the consequence of a wrong reading is severe; and a hold-last-good or safe-state behavior when the measurement fails its checks. That gives you fault tolerance without triplicating the analog chain.

I'd also want to push back gently on the framing. "The digital side has TMR" is a statement about one mitigation, not about the system's overall fault tolerance. The useful question is: for each credible failure mode, what detects it and what contains it? If the answer for the analog chain is "nothing," that's the gap to close — and it may be closable more cheaply than the engineer assumes.

**Possible follow-ups:**
- How would you set plausibility limits without also rejecting legitimate fast transients in the measured signal?
- If the measurement is safety-critical, how would you decide between a diverse second sensor and a redundant identical one?

## Q4: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt that puts the main processor into a state where it's still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** This is the hard case for watchdog design, because the obvious detection mechanism — "is the heartbeat still toggling?" — is exactly the thing that's lying to you. The processor is alive enough to keep the GPIO moving but not alive enough to do its job. So the test plan has to verify recovery from a failure mode that the primary detector can't see.

The first step is to define what "not executing the control loop" means observably. If the control loop has a periodic output — a DAC update, a PWM duty cycle change, a bus transaction — then the absence of that output is the real signature, and the test needs to check for it rather than for the heartbeat. That usually means the watchdog has to be fed by the control loop itself, not by a timer interrupt or a background task. A watchdog fed by anything other than the thing you actually care about is a watchdog that can be fooled.

For the test itself, since you can't inject radiation on the bench, you simulate the failure mode in firmware: put the processor into a state where it's still servicing the heartbeat but has stopped updating the control output, and verify that the system detects it and recovers within the required time. That's a fault-injection test, and it should cover the range of ways the processor can end up in that state — a corrupted loop counter, a stuck state machine, a task that's been starved, a peripheral that's stopped responding. Each one is a slightly different failure and may need a slightly different detection path.

Then you verify the recovery itself: does the system return to a known-good state, does it re-initialize the control loop correctly, does it log the event, and does it do all of that within the time budget the mission allows? And you verify the recovery is repeatable — a system that recovers once but leaves itself in a degraded state after the second event isn't actually fault-tolerant.

The other thing I'd want in the plan is a check that the detection doesn't false-trigger during normal operation, including during the transients that happen at power-up, mode changes, and fault recovery. A watchdog that resets the system every time the control loop legitimately pauses is worse than no watchdog.

**Possible follow-ups:**
- How would you structure the fault-injection tests so they cover the failure modes you can't easily reproduce in firmware?
- If the control loop's output is not directly observable from outside the processor, how would you build the detection path?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing is to separate the technical question from the interpersonal one. The engineer has done real work, which means they've thought about the problem and probably have reasons for their choice that aren't obvious from the outside. My job in the review is to understand those reasons before I decide whether I disagree with the conclusion or just with the margin.

So I'd start by asking them to walk me through the analysis — what environment they assumed, what the part's data says, how they arrived at the margin they have. Often the disagreement turns out to be about an assumption rather than about the engineering: they assumed a dose rate, or a temperature range, or a derating factor that I think is optimistic. That's a much easier conversation than "your design is wrong," because it's about a specific input that can be checked.

If the disagreement survives that, I'd try to make it concrete rather than abstract. "Under-margined" is a judgment; "the part's TID data shows it going out of spec at 30 krad and the mission dose with margin is 40 krad" is a fact that can be verified. Where I can, I'd point to the specific data or the specific analysis that drives my concern, and I'd be open to being shown that I'm wrong — sometimes the engineer has data I don't.

If we still disagree after that, the decision has to be made, and it should be made on the basis of risk rather than seniority. What's the consequence if the margin is insufficient? Is it a degraded measurement, a lost function, a mission failure? What's the cost of adding margin — a more expensive part, a redesign, a schedule slip? Those are the terms the decision should be argued in, and they're terms where a junior engineer can legitimately win the argument if the consequence is low and the cost is high.

Throughout, the tone matters. The goal is to make it safe for the engineer to have done the work and still be wrong, because that's how you get people to bring you their real analysis instead of a defensible-looking version of it. If the review becomes adversarial, the next design review will have less information in it, not more.

**Possible follow-ups:**
- What would you do if the engineer's analysis is correct but the schedule doesn't allow the change you think is needed?
- How would you document the decision so that it's clear what was decided, why, and who owns the residual risk?