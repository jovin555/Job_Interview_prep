# risk-requirements-traceability — Day 40

## Q1: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a design review whose criteria don't explicitly mention the risk control's failure condition — so the review could pass without anyone actually assessing whether the control works?

**Answer:** This is a classic traceability gap where the link exists on paper but the evidence doesn't actually demonstrate the control's effectiveness. I'd start by examining the design review checklist or criteria to confirm the gap — specifically, whether the review questions address the failure condition the risk control is meant to mitigate, or whether they only cover nominal design aspects like component selection and general layout.

If the criteria don't cover the failure condition, I'd treat this as a verification adequacy problem, not just a documentation problem. The first question is whether a design review is even the right verification method for this particular control. Some risk controls — like component derating, creepage distances, or thermal management strategies — are legitimately verified by design review or analysis, because the "test" is really an expert assessment of whether the design implements the control correctly. But for the review to count as objective evidence, the review criteria must explicitly require the reviewer to assess the specific failure mode and the control's ability to mitigate it.

I'd work with the design review owner to add explicit criteria — for example, "Verify that the over-temperature detection circuit's trip point is within the specified tolerance band given worst-case component tolerances" or "Confirm that the firmware's plausibility check rejects readings that change by more than X% between consecutive samples." The criteria should reference the specific hazard and failure condition from the risk analysis, not just general design quality.

If the control is something that genuinely can't be adequately assessed by review — for example, a timing-dependent behavior that depends on interrupt latency — I'd recommend adding a physical test or analysis to the verification plan instead of relying on the review alone. The key principle is that the verification method must be capable of detecting failure of the control, and the evidence must show that the specific failure condition was considered.

**Possible follow-ups:**
- How would you determine whether a design review is an appropriate verification method for a given risk control, versus when a physical test is required?
- If you add new criteria to the design review, how would you ensure the review actually enforces them rather than just having them on the checklist?

---

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a hardware analog circuit with a trim potentiometer that must be calibrated during manufacturing — where the calibration setting itself is part of the risk control, and the verification test must confirm both the circuit function and the calibration tolerance?

**Answer:** This is an interesting case because the risk control has two distinct aspects: the circuit design itself (the analog comparator, the hysteresis network, the reference voltage) and the manufacturing calibration that sets the operating point. Both need to be traced, but they're verified at different stages and by different activities.

I'd structure the traceability in layers. First, the risk control measure in the risk management file would reference the design requirement — for example, "The over-temperature detection circuit shall assert an interrupt when the sensed temperature exceeds 42°C ± 2°C." That requirement traces down to the circuit design (component values, topology) and to the calibration specification (the trim pot setting range, the calibration procedure, and the acceptance tolerance).

For verification, I'd distinguish between design verification and production verification. Design verification — done on a representative unit during development — would confirm that the circuit, with the trim pot adjusted across its intended range, can meet the tolerance spec. This might involve testing at multiple trim settings, across temperature, and with worst-case component tolerances to confirm the adjustment range is sufficient. That's a design-level activity.

Production verification is different. Every unit gets calibrated during manufacturing, and the calibration process itself must confirm that the final setting is within the acceptable range. The production test would measure the actual trip point (or a proxy measurement) and verify it falls within the specified tolerance. This is a manufacturing test, but it's still verification of the risk control — so it needs to be traced back to the same risk control measure.

The traceability scheme would therefore have the risk control linked to two verification activities: the design verification test (confirming the circuit can be calibrated to meet spec across its adjustment range) and the production test (confirming each unit is actually calibrated within tolerance). The risk management file should reference both, because they verify different aspects of the same control.

One thing I'd watch for is whether the calibration tolerance is actually derived from the risk analysis — meaning the acceptable range is tied to the hazard being mitigated, not just what's convenient to manufacture. The traceability should show that the calibration spec exists because of the risk control, not as an independent manufacturing preference.

**Possible follow-ups:**
- How would you handle a situation where the trim pot's adjustment range is too narrow to compensate for worst-case component tolerances, and some units can't be calibrated within spec?
- Would you require the production calibration test to measure the actual trip point, or is verifying the trim pot setting (e.g., voltage at the wiper) sufficient?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a safety mechanism that can be bypassed or overridden by a clinician — for example, a "disable alarm" button on a patient monitoring device — and the override itself introduces a new hazard?

**Answer:** This is a case where the risk analysis needs to consider not just the primary hazard but also the hazard created by the override itself. The traceability scheme has to capture both the original risk control and the new risk introduced by the override mechanism.

First, I'd make sure the risk analysis actually addresses the override as a distinct hazard scenario. The "disable alarm" button is a risk control for one hazard (e.g., nuisance alarms causing clinician fatigue and missed real alarms), but it introduces a new hazard (e.g., a real alarm being silenced when it shouldn't be). The risk management file should have a separate hazard entry for the override scenario, with its own risk controls — for example, a visual indicator that alarms are disabled, an automatic re-enable after a timeout, or a limit on how long the override can remain active.

For traceability, I'd create two parallel paths. The first path traces the original hazard → the override mechanism as a risk control → the requirements that implement the override (e.g., "The device shall provide a means to temporarily silence audible alarms") → verification that the override works as intended. The second path traces the new hazard (alarm disabled when it shouldn't be) → the risk controls that mitigate that hazard (e.g., visual indicator, timeout, re-enable logic) → the requirements for those controls → verification of those requirements.

The tricky part is that both paths share some of the same design elements — the button, the alarm state machine, the display. So the traceability matrix needs to show that a single design element can serve multiple purposes, and that each purpose has its own verification. For example, the button's physical function is verified by one test, but the timeout behavior that limits the override duration is verified by a different test.

I'd also make sure the verification for the override-related controls includes testing the failure scenarios — for example, what happens if the clinician disables the alarm and then a real alarm condition occurs? Does the visual indicator change? Does the alarm re-enable after the timeout? Does the system log the override event? These are the scenarios that the risk analysis identified, and the tests need to exercise them.

**Possible follow-ups:**
- How would you handle the case where the override is implemented in firmware, but the "alarm disabled" indicator is a hardware LED — and the two are verified by different teams?
- How would you trace the override-related requirements if the override behavior differs between operating modes (e.g., normal mode vs. standby mode)?

---

## Q4: How would you approach determining whether a risk control measure that is implemented as a hardware fuse (one-time, non-resettable) needs to be verified on every production unit, or whether verification on a sample basis is sufficient?

**Answer:** This is fundamentally a question about the nature of the risk control and the failure modes that could make it ineffective. A fuse is a passive component — its function is to open the circuit when current exceeds a threshold. The question is: what could go wrong that would prevent it from doing its job?

There are really two aspects to consider. First, is the fuse correctly selected and rated for the application? That's a design question — is the current rating appropriate, does it have adequate interrupting capacity, is it coordinated with the rest of the protection scheme? This is verified during design verification, typically by fault injection testing where you actually force the overcurrent condition and confirm the fuse opens within the specified time. This is done on a representative unit, not on every production unit, because it's testing the design, not the manufacturing process.

Second, is the fuse correctly installed and connected in each production unit? This is a manufacturing quality question. A fuse can be the right part but poorly soldered, or the wrong part could be placed by mistake, or a solder bridge could bypass it entirely. These are manufacturing defects that could defeat the risk control. The question is whether 100% inspection is needed or whether sampling is acceptable.

My approach would be to look at the risk analysis to understand the severity and probability of the hazard the fuse mitigates. If the fuse is protecting against a high-severity hazard — for example, preventing a fire in a medical device — then the consequences of a manufacturing defect are severe, and I'd lean toward 100% verification. But the verification method matters too. If the fuse can be verified by a simple continuity test or a visual inspection that's reliable and fast, 100% verification is practical. If the verification requires actually blowing the fuse — which destroys it — then 100% verification is impossible, and you're relying on process controls and sampling.

In practice, I'd consider a combination approach. The design is verified once during development with fault injection. Production verification might include a continuity check on every unit (confirming the fuse is present and not open), plus a sample-based destructive test where fuses are actually blown to confirm they meet spec. The sampling rate would be justified by the risk analysis and by the manufacturing process capability — for example, if the fuse placement is done by a pick-and-place machine with vision inspection, the risk of misplacement is lower than with manual assembly.

The key is that the decision must be documented and justified in the risk management file, showing that the verification strategy is commensurate with the risk and that the sampling plan (if used) is statistically sound.

**Possible follow-ups:**
- How would you justify a sampling plan to a regulator or auditor who expects 100% verification of safety-critical components?
- What if the fuse is in a location that makes post-assembly testing impossible — how would you approach verifying it?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are scheduled for the very end of the project, after all design work is complete. The program manager argues this is efficient because it avoids rework — the design is finalized before testing begins. The quality manager argues that late verification means design errors are discovered too late, causing expensive rework and schedule delays. How would you resolve this disagreement?

**Answer:** I'd start by acknowledging that both perspectives have merit. The program manager is right that testing a moving target is wasteful — if the design is still changing, test results become invalid and tests need to be redone. The quality manager is right that discovering a fundamental design flaw at the end of the project is the most expensive possible outcome. The resolution isn't to pick one side but to recognize that different types of verification have different optimal timing.

I'd propose a phased verification approach. Some verification activities are inherently design-dependent and should wait until the design is stable — for example, EMC testing, full system-level functional testing, or formal qualification testing. These are expensive and sensitive to design changes, so running them early is wasteful. But other verification activities can and should happen earlier — for example, unit-level testing of firmware modules, bench testing of critical analog circuits, or design reviews that assess whether the design approach is sound. These catch problems while they're still cheap to fix.

The key is to identify which risk controls are most likely to have design issues and which verification activities are most likely to catch those issues early. For example, if a risk control depends on a tight timing margin, a worst-case timing analysis early in the design phase is much more valuable than waiting for full system testing. If a risk control depends on a sensor's accuracy, a bench test with the actual sensor early in the project can validate the approach before the full system is integrated.

I'd also look at the risk analysis to prioritize. High-severity hazards with risk controls that are complex or novel should have earlier verification. Lower-severity hazards with well-understood controls can wait for later verification. This isn't about doing all verification early — it's about doing the right verification at the right time.

I'd bring the two managers together with this framework and ask them to agree on which verification activities are "design-critical" and should happen early, versus which are "qualification" activities that can wait. The goal is a verification plan that catches design errors early enough to fix them cheaply, while avoiding the waste of testing an unstable design.

**Possible follow-ups:**
- How would you handle a situation where the program manager agrees to early verification in principle, but the budget and resources are only allocated for the end-of-project testing?
- What specific verification activities would you insist on doing early, and how would you justify each one to the program manager?