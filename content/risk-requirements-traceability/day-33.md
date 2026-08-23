# risk-requirements-traceability — Day 33

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a hardware analog circuit with a trim potentiometer that must be calibrated during manufacturing — where the calibration setting itself is part of the risk control, and the verification test must confirm both the circuit function and the calibration tolerance?

**Answer:** This is a good example of a risk control that spans design, manufacturing, and verification — and it highlights why traceability can't stop at the engineering lab. I'd approach it in layers.

First, in the risk management file, I'd document the control clearly: the analog circuit provides the protection (e.g., a current limit or voltage threshold), and the trim pot sets the operating point within a specified tolerance. The hazard, the control, and the failure condition (e.g., "if the threshold drifts outside X%, the protection may not engage") all need to be linked.

Second, in the SRS, I'd capture the functional requirement — "the circuit shall trip at voltage V ± tolerance" — as a verifiable requirement with measurable acceptance criteria. The calibration tolerance itself should be part of that requirement, not buried in a manufacturing work instruction, because it directly affects whether the risk control performs its intended function.

Third, I'd think about the verification strategy carefully. There are really two things being verified: (a) the circuit design is correct — that with the trim pot set to the nominal value, the circuit trips at the right point; and (b) the manufacturing process can consistently set the trim pot within tolerance. These are different questions. Design verification would typically use a sample of units across the expected range of component tolerances to confirm the circuit works. Production verification — whether every unit or a sample — would confirm the calibration process actually lands within the specified tolerance.

For traceability, I'd create a chain: hazard → risk control measure → SRS requirement (including calibration tolerance) → design specification (circuit schematic, trim pot selection, calibration procedure) → verification test (both design-level and production-level) → test results. The key is that the calibration tolerance appears in both the requirement and the verification acceptance criteria, so there's no gap between "the design should work" and "the manufacturing process can actually produce it."

One thing I'd watch for is the difference between verifying the circuit function and verifying the calibration process. A common gap is testing the circuit on a bench with a carefully adjusted trim pot, but never confirming that the production calibration procedure reliably lands within tolerance across multiple units and operators.

**Possible follow-ups:**
- How would you handle a situation where the calibration tolerance is achievable in the lab but not consistently achievable on the production line?
- Would you require 100% verification of the calibration on every production unit, or would sampling be acceptable, and how would you justify that decision?

---

## Q2: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a safety mechanism that can be bypassed or overridden by a clinician — for example, a "disable alarm" button on a patient monitoring device — and the override itself introduces a new hazard?

**Answer:** This is a classic case where the risk control measure creates a secondary risk, and the traceability scheme has to capture both the original hazard and the new one introduced by the override.

I'd start by treating the override as a distinct risk control measure in its own right — not just a feature. The risk analysis should identify: (a) the original hazard the alarm mitigates, (b) the override as a deliberate user action that temporarily disables the alarm, and (c) the new hazard that arises when the alarm is disabled (e.g., a critical condition goes unnoticed). Each of these needs its own hazard analysis entry, and the traceability must connect them.

In the SRS, I'd capture requirements for both the alarm function and the override behavior. For example: "The device shall provide a means for the clinician to temporarily silence the alarm" and "When the alarm is silenced, the device shall display a persistent visual indicator." The second requirement is critical because it's the risk control for the new hazard — the visual indicator mitigates the risk that the clinician forgets the alarm is disabled.

For traceability, I'd create a chain that shows: original hazard → alarm as risk control → override feature → new hazard (alarm disabled) → visual indicator as secondary risk control → verification test for the indicator. The key is that the override doesn't just trace back to the original hazard — it also traces forward to the new hazard it creates.

I'd also think about the verification strategy. The test for the override should verify not just that the alarm can be silenced, but that the visual indicator appears, that it persists for the duration of the override, and that the alarm re-arms appropriately (e.g., after a timeout or when the condition clears). The test should also verify the behavior when the override is active and a new alarm condition occurs — does the device re-alarm, or does it stay silent?

One subtle point: the override itself is a user-accessible control, so the risk analysis should consider misuse — for example, a clinician silencing the alarm and then leaving the patient unattended. The traceability should capture whether the design includes mitigations for that misuse scenario (e.g., a maximum silence duration, or an audible re-alert after a timeout).

**Possible follow-ups:**
- How would you handle a situation where the clinician override is a physical switch rather than a software button, and the switch position isn't visible to the software?
- What if the override is intended to be used only in specific clinical scenarios — how would you capture that in the requirements without over-constraining the design?

---

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a software unit test that runs on a host PC (not the target hardware), and the risk control involves timing behavior that depends on the microcontroller's clock speed and interrupt latency?

**Answer:** This is a common tension between the convenience of host-based testing and the fidelity of target-hardware testing. The key question is: what aspect of the risk control are we actually verifying?

If the risk control involves timing behavior — say, a timeout that must trigger within a certain window, or a response that must occur before a hardware fault propagates — then a host-PC test may not be representative. The host PC has a different CPU, different clock speed, different interrupt handling, and different compiler optimizations. A test that passes on the host might fail on the target, or vice versa.

My approach would be to first clarify what the risk analysis actually requires. If the risk control's effectiveness depends on absolute timing (e.g., "the motor must be disabled within 50ms of the fault condition"), then the verification needs to demonstrate that timing on the actual hardware. A host-based unit test can verify the logic — that the timeout is implemented correctly, that the state transitions are right, that the code path is exercised — but it can't verify the timing.

I'd propose a two-tier approach. Tier one: host-based unit tests to verify the logic and code coverage. Tier two: target-hardware tests to verify the timing behavior. The traceability would show both activities linked to the same risk control, with the target-hardware test being the primary evidence for the timing requirement.

If the risk analysis specifies a timing tolerance, I'd also want to understand the margin. For example, if the requirement is "disable within 50ms" and the design targets 10ms, there's more margin than if the design targets 45ms. The verification approach might differ based on that margin — a larger margin might allow for analysis (e.g., worst-case execution time calculation) supplemented by a single target-hardware confirmation, while a tight margin would demand more extensive testing across conditions.

I'd also consider whether the host-based test could be misleading. If the host test passes but the target fails due to timing, that's a false sense of security. I'd want the traceability to clearly indicate which verification activities are host-based (logic verification) and which are target-based (timing verification), so reviewers don't mistakenly treat the host test as sufficient evidence for the timing requirement.

**Possible follow-ups:**
- How would you determine whether the timing margin is sufficient to rely on analysis rather than extensive target-hardware testing?
- What if the target hardware isn't available yet — how would you structure the verification plan to allow host-based testing to proceed while flagging the timing verification as pending?

---

## Q4: How would you approach determining whether a risk control measure that is implemented as a hardware fuse (one-time, non-resettable) needs to be verified on every production unit, or whether verification on a sample basis is sufficient?

**Answer:** This is a question about production verification strategy, and the answer depends on what we're actually trying to verify. A fuse is a passive component — its function is determined by its design (the current rating, the trip curve) and its manufacturing quality. There are really two different questions: (1) is the fuse correctly selected and rated for the application, and (2) is the fuse that's installed in each unit the correct part, correctly installed?

For the first question — fuse selection and rating — that's a design verification activity. It should be verified during design verification, typically by testing a sample of fuses across the expected range of operating conditions (current, temperature, aging). This is where you'd confirm that the fuse actually trips at the specified current within the specified time. This doesn't need to be repeated on every production unit because it's a property of the design, not of the individual unit.

For the second question — correct part, correct installation — that's a production quality question. The risk is that the wrong fuse is installed, or that the fuse is damaged during assembly (e.g., by heat from soldering), or that the fuse holder has a poor connection. This is typically addressed by incoming inspection (verifying the correct part number and lot), process controls (soldering profile, inspection after assembly), and possibly sample-based testing.

The key consideration is the failure mode. A fuse is a one-time device — you can't test it by actually blowing it on every unit, because then you'd have to replace it. So 100% functional testing of the fuse isn't practical. Instead, you'd verify the fuse's presence and correct installation (visual inspection, continuity check) on every unit, and rely on design verification plus incoming inspection for the fuse's electrical characteristics.

I'd also think about the risk analysis. If the fuse is the sole protection against a hazardous condition — say, overcurrent that could cause a fire — then the consequence of a fuse failure is severe, and I'd want stronger evidence. That might mean 100% inspection of the fuse installation, tighter incoming inspection (e.g., verifying the date code and lot), and possibly sample-based destructive testing to confirm the fuse's actual trip characteristics match the datasheet.

The traceability would show: hazard → fuse as risk control → design verification (fuse selection and rating) → production verification (incoming inspection, installation inspection, sample testing). The acceptance criteria for each level would be different, and the risk analysis would justify the sampling plan based on the severity and the confidence in the manufacturing process.

**Possible follow-ups:**
- How would you handle a situation where the fuse is soldered directly to the PCB rather than in a holder, making post-assembly inspection more difficult?
- What evidence would you need to justify moving from 100% inspection to sample-based inspection of the fuse installation?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that the verification activities are all scheduled for the very end of the project, after all design work is complete. The program manager argues that this is efficient because it avoids rework — the design is finalized before testing begins. The quality manager argues that late verification means design errors are discovered too late, causing expensive rework and schedule delays. How would you resolve this disagreement?

**Answer:** I'd start by acknowledging that both perspectives have merit. The program manager is right that testing a moving target is wasteful — if the design is still changing, test results become obsolete quickly. The quality manager is right that discovering a fundamental design flaw at the end of the project is the most expensive possible outcome. The resolution isn't to pick one side but to find a middle path.

I'd propose a staged verification approach. Not everything needs to be tested at the end, and not everything can be tested early. Some verification activities are inherently early — design reviews, simulations, analysis of the architecture. Some are inherently late — final system-level tests on production-representative hardware. The key is to identify which risk controls carry the most uncertainty and which failures would be most expensive to discover late, and prioritize those for earlier verification.

For example, if a risk control depends on a novel circuit topology or a component that's never been used this way, I'd want a breadboard or early prototype test to validate the approach before committing to the full design. If a risk control depends on firmware timing, I'd want that verified on early hardware as soon as it's available. But if a risk control is a well-understood, standard approach — say, a common protection circuit — then verifying it late might be acceptable because the risk of discovering a fundamental flaw is low.

I'd also look at the dependencies. Some verification activities can't happen until the design is complete — you can't test the final PCB layout until the PCB exists. But many can happen incrementally. I'd work with the team to map out which risk controls can be verified at each stage — concept, prototype, engineering sample, production-representative — and build a verification plan that spreads the work across the project rather than concentrating it at the end.

The conversation with the program manager and quality manager would focus on risk, not just schedule. I'd frame it as: what's the cost of discovering a problem at each stage, and what's the probability of a problem existing? Early verification makes sense where the cost of late discovery is high and the probability of a problem is non-trivial. Late verification is acceptable where the design is well-understood and the cost of early testing would be wasted effort.

I'd also propose a mechanism for the program manager to see the value: a risk register that tracks which risk controls have been verified and which are still open. That way, the schedule impact of late verification is visible, and we can make informed decisions about where to invest early testing effort.

**Possible follow-ups:**
- How would you handle a situation where the program manager agrees with staged verification in principle, but the budget only allows for one round of prototype hardware?
- What criteria would you use to decide which risk controls absolutely must be verified early versus which can wait until the end?