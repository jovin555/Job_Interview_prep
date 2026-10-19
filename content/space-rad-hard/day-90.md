# space-rad-hard — Day 90

## Q1: How would you approach designing a radiation-tolerant analog-to-digital conversion subsystem where the ADC's voltage reference is a COTS part with no radiation data, and the measurement must hold accuracy over a multi-year mission?

**Answer:** The voltage reference is often the accuracy bottleneck in a precision measurement chain, and a COTS reference with no radiation data is a real risk because references are typically bandgap or buried-Zener topologies whose behavior under TID and ELDRS is not predictable from the datasheet. I'd start by characterizing the risk rather than assuming it: what accuracy does the measurement actually need, and how much of the error budget can the reference consume? Then I'd treat the reference as a component that must be either qualified, compensated, or replaced.

The first lever is architecture. If the reference is only used for ratiometric measurements, I can drive the ADC from the same reference that excites the sensor, so reference drift cancels in the ratio — that removes a large class of TID-induced error without needing a rad-hard part. If the measurement is absolute, I'd look at whether a rad-hard reference is available at acceptable cost, or whether I can periodically recalibrate against a known internal standard.

The second lever is monitoring. I'd add a way to observe the reference over life — for example, a second reference of a different technology, or a precision divider off a stable rail, so the system can detect drift and flag it rather than silently reporting wrong values. If the mission allows, a calibration command from the ground can re-baseline the reading.

The third lever is margin. I'd derate the reference's specified initial accuracy and tempco, add an allowance for TID-induced drift based on the closest comparable data I can find (similar topology, similar process), and confirm the resulting error budget still meets the requirement. If it doesn't, the reference has to change — no amount of calibration routine fixes a reference that has drifted outside the correction range.

**Possible follow-ups:** How would you structure the calibration routine so it can distinguish reference drift from sensor drift? What would you do if the only rad-hard reference available has worse initial accuracy than the COTS part?

## Q2: How would you approach designing a fault-tolerant power distribution scheme for a payload with multiple loads of different criticality, where a single-event latch-up (SEL) in any one load must not take down the rest of the system?

**Answer:** The core principle is that a latch-up is a local fault and must be contained locally — the distribution architecture should make it structurally impossible for one load's fault to propagate upstream. I'd start by classifying loads by criticality and current draw, because the protection strategy follows from that.

For each load, I'd put a current-limiting switch or eFuse on its own branch, sized so that the trip threshold is above the load's worst-case inrush but below the level at which the branch could drag the upstream rail down. The switch needs to latch off on overcurrent and report the fault, so the system can decide whether to retry. Retry policy should differ by criticality: a housekeeping load might get an automatic retry after a delay, while a load whose failure mode is dangerous might stay off until commanded.

Upstream of the branches, I'd make sure the primary rail has enough bulk capacitance and a source impedance low enough that a branch trip doesn't cause a transient that resets other loads. I'd also consider whether the branches should be grouped on separate upstream converters or fuses, so a fault that defeats one layer of protection doesn't take out everything on that converter.

The other half of the design is observability. Each branch should report current and fault status so the system can distinguish "load latched and was isolated" from "load is drawing more than expected but hasn't tripped" — the latter is an early warning. And the fault handling should be tested: I'd want a way to inject an overcurrent on each branch during ground test and confirm the rest of the system rides through.

**Possible follow-ups:** How would you size the trip threshold when a load has a large capacitive inrush? What's the trade-off between latching off and auto-retry for a critical load?

## Q3: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** The argument has a category error in it: TMR on the digital side protects against upsets in the digital logic, but it does nothing for a single-event transient that corrupts the analog signal before it's ever digitized. If the analog chain produces a wrong value, TMR will faithfully vote on three copies of the wrong value. Redundancy downstream cannot recover information that was never correct upstream.

So I'd separate the question into two: what failure modes does the analog chain have, and what does the control loop need in order to be safe when one of them occurs? On the failure-mode side, the relevant effects are SETs in the amplifier and in the ADC's sample-and-hold, drift in the sensor and reference over TID, and single-point failures in the signal path. On the control-loop side, the question is whether a single bad sample can cause a dangerous action, or whether the loop's own filtering and rate limiting absorb it.

From there the mitigation can be proportionate. If the loop is slow relative to the SET duration, a median filter or a plausibility check on the digitized value may be enough — a single spurious sample gets rejected. If the measurement is time-critical and can't simply be retried, then I'd look at a second signal path, or at minimum a second ADC channel sampling the same node so the two can be compared. And I'd want an independent way to detect that the analog chain has failed — for example, a test signal injected periodically, or a comparison against a redundant sensor.

The conversation with the engineer is worth having carefully, because the underlying instinct — "the digital side is protected, so we're fine" — is common and worth correcting with a concrete failure story rather than an assertion.

**Possible follow-ups:** How would you decide between filtering a bad sample and adding a second signal path? What would you inject as a test signal, and how often?

## Q4: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt (SEFI) that leaves the processor still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** The hard part of this scenario is that the usual recovery mechanism — a watchdog that looks for a missing heartbeat — is defeated, because the heartbeat is still there. So the test plan has to verify recovery from a failure that the primary detector can't see, which means the test has to exercise the secondary detection path specifically.

I'd start by defining what "recovered" means in observable terms: the control loop is executing, the outputs are in a safe state or have been re-driven correctly, and the system has logged the event. Then I'd build a way to induce the failure on the bench without radiation. The cleanest approach is usually a debug hook or a test build that deliberately parks the processor in a state where it toggles the heartbeat GPIO from a timer interrupt but stops servicing the control loop — that reproduces the failure mode exactly, and it's repeatable.

With that in place, the test cases are: does the secondary detector fire; how long does it take; does the recovery sequence bring the loop back correctly; and does the system behave safely during the interval between failure and recovery. I'd run it many times, including at temperature extremes and at the edges of the supply range, because the timing of the detector relative to the failure may shift.

I'd also test the detector's own failure modes — what happens if the secondary detector itself is upset, and does the system fail safe or fail silent? And I'd verify that the recovery doesn't itself cause a hazard, for example by driving outputs to a default state that's wrong for the current operating condition.

**Possible follow-ups:** What secondary detection mechanism would you use when the heartbeat is unreliable? How would you bound the worst-case recovery time, and how does that bound feed back into the control-loop design?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is make sure I actually understand the proposal and the analysis behind it, because "under-margined" is my judgment and it needs to be testable. I'd ask the engineer to walk through the assumptions — what radiation environment they assumed, what data they based the part behavior on, and where the margin sits. Often the disagreement turns out to be about a specific assumption rather than the whole design, and naming that assumption makes the conversation concrete.

Then I'd separate the technical question from the decision. The technical question is: given the stated environment and the available data, what's the worst case, and does the design survive it? If we disagree on the data, that's resolvable — we can look at the same source together, or ask for a second opinion. If we disagree on the environment, that's a requirements question and needs to go back to whoever owns the requirement. If we disagree on what "survives" means, that's a risk-acceptance question, and it belongs to the person accountable for the system, not to either of us in the room.

I'd be explicit that the goal of the review is to find the failure, not to win. I'd ask the engineer what evidence would change their mind, and I'd say what would change mine — that keeps it honest. If after that we still disagree, I'd document both positions, the assumption each rests on, and escalate the risk decision rather than overruling on authority. And I'd follow up afterward so the engineer knows the disagreement was about the design, not about them.

**Possible follow-ups:** What would you do if the engineer's analysis is correct but the requirement itself is wrong? How do you make sure a junior engineer feels able to push back on you in the next review?