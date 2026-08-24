# risk-requirements-traceability — Day 34

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a hardware analog circuit with a trim potentiometer that must be calibrated during manufacturing — where the calibration setting itself is part of the risk control, and the verification test must confirm both the circuit function and the calibration tolerance?

**Answer:** This is a good example of a risk control that spans design, manufacturing, and verification — and it highlights why traceability can't stop at the engineering lab. I'd approach it in layers.

First, I'd make sure the risk management file clearly states *what* the control is: the analog circuit provides the detection/trip function, but the calibration setting determines *where* that trip point actually sits. Both elements are part of the control, and both need to be traced.

At the requirements level, I'd expect to see:
- A system-level requirement for the trip point (e.g., "the device shall assert a fault signal when the monitored parameter exceeds X ± tolerance").
- A derived hardware requirement for the circuit design, including the nominal component values and the trim range.
- A manufacturing requirement or specification for the calibration procedure, including the acceptance tolerance and the measurement method used during calibration.

For verification, I'd distinguish between design verification and production verification. During design verification, you'd test the circuit across its full trim range — including corner cases — to confirm the design can actually be calibrated to meet the specification. You'd also test the *uncalibrated* worst-case behavior to understand what happens if calibration drifts or is performed incorrectly. That's a fault condition that should be in the risk analysis.

For production, the calibration step itself becomes a verification activity. The question is whether it's a 100% inspection or a sample-based check. For a safety-related trip point, I'd lean toward 100% calibration verification on every unit, because the calibration is what makes the risk control effective — you can't rely on statistical sampling for a control that's adjusted per-unit.

The traceability link I'd want to see is: hazard → risk control (analog trip circuit + calibration) → design requirement (circuit function) → design verification (trip point across trim range) → manufacturing requirement (calibration procedure) → production verification (calibrated trip point on each unit). The calibration tolerance in the manufacturing spec should trace back to the tolerance analysis that justified the risk control's effectiveness.

One subtlety: the calibration procedure itself can introduce errors. I'd want the risk analysis to consider what happens if the calibration is wrong — for example, if the technician sets the trim to the wrong value, or if the measurement equipment used during calibration is out of tolerance. That might drive a requirement for calibration equipment accuracy or for a post-calibration verification step.

**Possible follow-ups:**
- How would you handle a situation where the design verification tests the circuit across the full trim range, but the production calibration only checks a single point?
- What if the trim potentiometer is replaced with a digital potentiometer controlled by firmware — how does that change the traceability approach?

---

## Q2: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a safety mechanism that can be bypassed or overridden by a clinician — for example, a "disable alarm" button on a patient monitoring device — and the override itself introduces a new hazard?

**Answer:** This is a classic case where the risk control creates a secondary risk, and the traceability scheme has to capture both the primary control and the new hazard it introduces.

I'd start by making sure the risk analysis itself is complete. The "disable alarm" function is a risk control for one hazard — say, alarm fatigue or nuisance alarms that cause clinicians to ignore warnings. But the override introduces a new hazard: the alarm is disabled when a real patient event occurs. That secondary hazard needs its own risk analysis entry, with its own risk control measures.

For traceability, I'd structure it as a chain rather than a single link:
- Primary hazard → risk control (alarm disable function) → requirement (the button exists and works as specified) → verification (the button disables the alarm).
- Secondary hazard (alarm disabled during real event) → risk control(s) for *that* hazard → requirements → verification.

The risk controls for the secondary hazard might include: a visual indicator showing the alarm is disabled, an automatic re-enable after a timeout, an audible "alarm disabled" reminder, or a limit on how long the alarm can be silenced. Each of these is a separate requirement with its own verification.

The tricky part is that the same user interface element — the disable button — is now traced to two different risk control measures in two different hazard chains. I'd want the traceability matrix to show both paths clearly, so a reviewer can see that the button is not just a feature but a risk control with its own secondary risk assessment.

I'd also want to verify the *interaction* between the primary and secondary controls. For example, if the alarm is disabled and a patient event occurs, does the visual indicator change? Does the system log the event? These interaction behaviors should be traced to the secondary hazard's risk controls.

One thing I'd watch for: the override behavior might differ across operating modes. In normal mode, the disable might last 5 minutes; in a "monitoring paused" mode, it might behave differently. Each mode-specific behavior needs its own traceability, because the risk profile changes with the mode.

**Possible follow-ups:**
- How would you verify that the override's visual indicator actually alerts the clinician, given that "alerting" is hard to test objectively?
- What if the clinician override is implemented in firmware, but the alarm itself is a hardware circuit — how does that split affect your traceability approach?

---

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a software unit test that runs on a host PC (not the target hardware), and the risk control involves timing behavior that depends on the microcontroller's clock speed and interrupt latency?

**Answer:** This is a common gap in embedded systems verification. A host-PC unit test can verify the *logic* of the risk control — the algorithm, the state transitions, the decision tree — but it cannot verify the *timing* behavior that depends on the actual hardware.

I'd start by separating the risk control into its constituent properties. If the control is "the firmware shall disable the motor within 50ms of detecting an over-temperature condition," there are really two things being verified: (1) the firmware correctly detects the condition and initiates the shutdown sequence, and (2) the shutdown actually completes within 50ms on the target hardware. The host-PC test can verify the first property, but not the second.

My approach would be to treat the host-PC test as *one* verification activity, not the complete verification. I'd want to see:
- A unit-level test on the host PC that verifies the detection logic and the decision path — this is valuable because it's fast, repeatable, and can cover many edge cases.
- A target-hardware test that measures the actual timing — from sensor input to motor disable — including worst-case interrupt latency, clock speed effects, and any other hardware-dependent delays.

The traceability matrix should show both activities linked to the same risk control, with the host-PC test covering the logical behavior and the target-hardware test covering the timing requirement. If the requirement is written as a timing requirement, the host-PC test alone is insufficient.

I'd also consider whether the timing analysis needs to be more than a single measurement. Interrupt latency can vary depending on what else is running, so I'd want to know if the test exercises the worst-case scenario — for example, with the highest-priority interrupt firing at the same time, or with the bus saturated. If the risk analysis specifies a worst-case timing requirement, the verification should include a worst-case test, not just a nominal one.

One more consideration: the host-PC test might use a simulated clock or a mock interrupt mechanism. That's fine for logic verification, but I'd want the test documentation to clearly state what is and isn't being verified, so the traceability matrix doesn't imply more coverage than actually exists.

**Possible follow-ups:**
- How would you decide whether the timing requirement needs to be verified on every production unit, or whether a design-level timing analysis plus a sample test is sufficient?
- What if the timing margin is large enough that the host-PC test, combined with a static timing analysis, gives you confidence without a target-hardware test?

---

## Q4: How would you approach determining whether a risk control measure that is implemented as a hardware fuse (one-time, non-resettable) needs to be verified on every production unit, or whether verification on a sample basis is sufficient?

**Answer:** This is a question about the difference between design verification and production quality control, and it hinges on what failure mode you're protecting against.

First, I'd clarify what "verification" means in this context. There are really two different questions:
1. Does the fuse design correctly protect against the hazard? (Design verification)
2. Is the fuse correctly installed and functional on each production unit? (Production verification)

For the first question, design verification is clearly required. You'd test the fuse's trip characteristics, its current rating, its response time, and its behavior under fault conditions. This is done once on representative units, not on every production unit — because you're verifying the design, not the manufacturing process.

For the second question, the answer depends on what can go wrong in production. A fuse can be:
- Wrongly installed (wrong value, wrong orientation).
- Damaged during assembly (e.g., by heat from soldering or mechanical stress).
- Defective from the manufacturer (though this is usually covered by incoming inspection).

If the fuse is a through-hole component that's hand-soldered, the risk of wrong installation is higher, and you might want 100% verification. If it's a surface-mount fuse placed by a pick-and-place machine with automated optical inspection, the risk is lower, and sample-based verification might be acceptable.

But there's a deeper issue: a fuse is a one-time device. You can't test it by actually blowing it on every unit, because then you'd have to replace it. So "verification" on production units usually means:
- Visual inspection (correct part, correct placement).
- Electrical continuity check (the fuse is intact and connected).
- Possibly a resistance measurement to confirm it's the right value.

You can't verify the trip point on every unit without destroying the fuse. So the question becomes: what is the acceptable risk that a fuse is incorrectly installed or defective, and what level of inspection gives you confidence?

I'd approach this by looking at the risk analysis. If the fuse is the *only* risk control for a high-severity hazard, I'd lean toward 100% inspection — visual and continuity — because the consequence of a missing or wrong fuse is severe. If the fuse is one of multiple independent controls, or if the hazard severity is lower, sample-based verification might be justified.

I'd also consider the manufacturing process capability. If the fuse placement is automated and the process has a proven track record, sample-based verification with a defined AQL (acceptable quality level) might be defensible. But I'd want that decision documented in the risk management file, with justification.

One more thing: the fuse's one-time nature means you should also consider what happens *after* the fuse blows in the field. Is there a way for the user to know the fuse has blown? Is there a service procedure? That's a separate risk consideration, but it affects the overall risk profile.

**Possible follow-ups:**
- How would you document the justification for sample-based verification in the risk management file?
- What if the fuse is soldered directly to the PCB and can't be visually inspected after assembly — how does that change your approach?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that the verification activities are all scheduled for the very end of the project, after all design work is complete. The program manager argues that this is efficient because it avoids rework — the design is finalized before testing begins. The quality manager argues that late verification means design errors are discovered too late, causing expensive rework and schedule delays. How would you resolve this disagreement?

**Answer:** I'd start by acknowledging that both sides have a legitimate point. The program manager is right that testing a moving target wastes effort — if the design is still changing, test results become invalid and have to be redone. The quality manager is right that discovering a fundamental design flaw at the end of the project is the most expensive possible outcome. The disagreement isn't really about whether to verify — it's about *when* and *at what level*.

My approach would be to reframe the conversation around the *type* of verification, not just the timing. Not all verification has to happen at the end. I'd propose a tiered verification strategy:

1. **Early, low-fidelity verification:** As soon as requirements are drafted, I'd want to verify that they're testable and that the verification methods are feasible. This is a desk-check, not a test — but it catches problems like requirements that can't be measured or tests that can't be performed with the available equipment.

2. **Mid-project verification:** As design elements are completed — a PCB layout, a firmware module, a mechanical enclosure — I'd want to verify those elements in isolation. A bench test of a sensor interface board, a unit test of a firmware module, a tolerance analysis of a power supply. These catch design errors while they're still cheap to fix.

3. **Integration verification:** As subsystems come together, I'd want to verify interfaces and interactions. This is where timing issues, communication protocol problems, and electromagnetic interference often surface.

4. **Final system verification:** This is the formal, documented verification against the full requirements set — the one that goes in the design history file.

The key insight is that the *formal* verification campaign can still be at the end, but the *informal* verification — the design reviews, the bench tests, the simulations, the unit tests — should be distributed throughout the project. The traceability matrix should reflect this: it should show not just the final verification activity, but also the intermediate checks that build confidence along the way.

I'd also propose a risk-based approach to scheduling. For high-severity risk controls, I'd want early verification of the fundamental approach — even if it's a rough prototype test — because the cost of discovering a flaw late is highest for these. For lower-risk requirements, end-of-project verification is more acceptable.

In practice, I'd call a meeting with both the program manager and the quality manager, present this tiered approach, and ask them to agree on which verification activities need to happen early. I'd frame it as a way to reduce overall project risk — the program manager gets a stable design phase, and the quality manager gets early detection of critical issues. I'd also suggest a simple tracking mechanism: a "verification readiness" checklist that identifies which requirements have been verified at each stage, so progress is visible and neither side feels like the other is ignoring their concerns.

The goal isn't to declare one side right — it's to find a structure that gives both sides what they actually need: a stable design process and early detection of critical flaws.

**Possible follow-ups:**
- How would you handle a situation where the program manager agrees to early verification in principle, but then pushes back when it actually adds time to the schedule?
- What criteria would you use to decide which risk controls need early verification versus which can wait until the end?