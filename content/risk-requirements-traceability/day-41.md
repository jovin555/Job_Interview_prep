# risk-requirements-traceability — Day 41

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a hardware analog circuit with a trim potentiometer that must be calibrated during manufacturing — where the calibration setting itself is part of the risk control, and the verification test must confirm both the circuit function and the calibration tolerance?

**Answer:** This is a case where the risk control has two distinct aspects that need separate traceability paths: the circuit design itself and the manufacturing calibration process. I'd start by decomposing the control into its constituent elements in the risk management file — the analog circuit provides the detection function, but the calibration setting determines whether the trip point is actually within the safe range. These are different types of requirements: the circuit function is a design requirement, while the calibration tolerance is a manufacturing requirement.

For the design portion, I'd trace the circuit's functional requirement (e.g., "the comparator shall assert an output when the monitored voltage exceeds X volts ± tolerance") to the schematic and to a verification test that measures the trip point across the specified temperature range. For the calibration portion, I'd create a separate requirement in the manufacturing specification (e.g., "the trim potentiometer shall be set such that the trip point is within X volts of the nominal value") and trace that to a production test procedure.

The key challenge is that the verification test for the design can't be performed independently of the calibration — the circuit won't meet its tolerance without the trim being set correctly. So I'd structure the verification in two stages: first, a design verification test that uses a calibrated reference unit or a precisely set trim to validate the circuit's inherent behavior across temperature and component variation; second, a production verification that confirms the calibration process reliably lands within tolerance. The traceability matrix would show the risk control linking to both the design requirement and the manufacturing requirement, with separate verification activities for each.

I'd also consider whether the calibration tolerance itself needs to be derived from the risk analysis — the acceptable trip point range should come from the hazard analysis, not be chosen arbitrarily. That derivation should be documented so the link from hazard → risk control → calibration tolerance → verification is explicit.

**Possible follow-ups:**
- How would you handle the situation where the design verification test uses a precisely calibrated trim, but production units are calibrated using a different method (e.g., automated vs. manual)?
- What if the trim potentiometer drifts over time — how would you trace that failure mode back to the risk analysis?

---

## Q2: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a safety mechanism that can be bypassed or overridden by a clinician — for example, a "disable alarm" button on a patient monitoring device — and the override itself introduces a new hazard?

**Answer:** This is a classic case where the risk control creates a secondary risk that must itself be managed. The traceability scheme needs to capture not just the primary control (the alarm) but also the override mechanism and the mitigations for the override-induced hazard.

I'd structure this as a chain: the original hazard (e.g., undetected patient deterioration) is mitigated by the alarm system. The alarm system introduces a new hazard (alarm fatigue or nuisance alarms leading clinicians to disable alarms), which is mitigated by the override design — for example, requiring a confirmation step, limiting the override duration, or providing a visual indicator that the alarm is disabled. Each link in this chain needs its own traceability.

For the override itself, I'd create requirements that capture both the functional behavior (e.g., "the user shall be able to disable the audible alarm for a maximum of 5 minutes") and the safety behavior (e.g., "a visual indicator shall be displayed whenever the audible alarm is disabled"). The risk analysis would document the new hazard introduced by the override and the rationale for why the mitigation (limited duration, visual indicator) reduces the risk to an acceptable level.

The traceability matrix would show: original hazard → alarm control → alarm requirements → alarm verification; then override hazard → override mitigations → override requirements → override verification. The two chains are linked because the override requirements exist only because the alarm control exists — that dependency should be explicit in the traceability documentation.

I'd also consider whether the override needs a separate risk control measure in the risk management file, or whether it's part of the same control. I'd argue for treating it as a separate control with its own hazard link, because the failure modes are different — the alarm can fail to detect, while the override can fail to re-engage or fail to indicate its status. These need different verification approaches.

**Possible follow-ups:**
- How would you verify that the override mechanism itself doesn't introduce an unacceptable risk — for example, if the clinician forgets to re-enable the alarm?
- How would you trace the override's visual indicator requirement to a verification test that confirms it's visible under all lighting conditions?

---

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a software unit test that runs on a host PC (not the target hardware), and the risk control involves timing behavior that depends on the microcontroller's clock speed and interrupt latency?

**Answer:** This is a gap between the verification environment and the operational environment. A host-PC unit test can verify the logic of the timing algorithm — for example, that the timeout value is computed correctly or that the state machine transitions as expected — but it cannot verify that the timing behavior is correct on the actual hardware, because clock speed, interrupt latency, and other hardware-dependent factors are different.

My approach would be to treat this as two separate verification activities with different purposes. The host-PC unit test verifies the software logic: the algorithm correctly implements the intended timing behavior given the inputs. That's valuable and should be traced to the software requirement. But the risk control's effectiveness depends on the actual timing on the target hardware — for example, if the control requires a response within 10ms of a fault condition, the unit test can't prove the hardware will meet that.

So I'd add a second verification activity on the target hardware: either a hardware-in-the-loop test that exercises the actual timing path, or a test on the production-representative board that measures the response time under worst-case conditions. The traceability matrix would show the risk control linking to both the unit test (for logic verification) and the hardware test (for timing verification), with the hardware test being the one that provides evidence for the risk control's effectiveness.

I'd also examine whether the timing requirement itself is properly specified. If the risk analysis says "the system shall respond within X ms," that requirement needs to be traced to a verification method that can actually measure X ms on the target hardware. If the unit test is the only verification, the requirement is effectively unverified.

One practical consideration: the unit test might be useful for regression testing — catching logic changes that break the timing algorithm — even if it can't verify the actual timing. So I'd keep it in the traceability matrix, but clearly labeled as a logic test, not a timing verification.

**Possible follow-ups:**
- How would you determine whether the host-PC unit test provides any useful evidence for the risk control, or whether it should be removed from the traceability matrix entirely?
- What if the timing requirement has a wide tolerance (e.g., "respond within 100ms ± 50ms") — would that change your approach?

---

## Q4: How would you approach determining whether a risk control measure that is implemented as a hardware fuse (one-time, non-resettable) needs to be verified on every production unit, or whether verification on a sample basis is sufficient?

**Answer:** This is a question about verification strategy for a control that is inherently destructive to test — you can't verify a fuse on every unit without destroying every unit. The answer depends on what aspect of the fuse is being verified and what failure modes are credible.

First, I'd separate the verification into distinct aspects: the fuse's rating (does it open at the specified current?), the fuse's mounting (is it correctly soldered and connected?), and the circuit's behavior around the fuse (does the circuit actually limit current to the fuse's rating, and does the system respond correctly when the fuse opens?). These have very different verification needs.

The fuse's rating is verified by the component manufacturer — I'd rely on their datasheet and any incoming inspection or lot qualification. The circuit's current-limiting behavior is a design characteristic that should be verified during design verification, not on every production unit — a sample-based test during design validation is appropriate. The fuse's mounting is a manufacturing quality issue — this can be verified on every unit through visual inspection, automated optical inspection, or electrical continuity testing that doesn't require blowing the fuse.

The key question is whether there's a credible failure mode where the fuse is incorrectly installed or connected in a way that defeats the protection. If the fuse is a through-hole component with clear polarity and orientation markings, the risk of misinstallation might be low enough that sample-based verification is acceptable. If it's a surface-mount fuse that could be incorrectly placed or have poor solder joints, you might want 100% inspection.

I'd also consider whether the fuse's function can be verified indirectly on every unit — for example, by measuring the resistance of the fuse (a blown fuse has infinite resistance, but a correctly installed fuse has near-zero resistance) or by verifying that the circuit draws the expected current under nominal conditions. These tests don't destroy the fuse but provide evidence that the fuse is present and correctly connected.

The risk analysis should drive this decision: if the fuse is the sole protection against a high-severity hazard, the verification strategy needs to be more rigorous. If it's a secondary protection with other controls in place, sample-based verification might be justified. The decision and its rationale should be documented in the verification plan.

**Possible follow-ups:**
- How would you handle a situation where the fuse is the only protection against a catastrophic failure, but testing every unit would be impractical?
- What evidence would you need from the fuse manufacturer to justify relying on their datasheet rather than testing the fuse yourself?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that the verification activities are all scheduled for the very end of the project, after all design work is complete. The program manager argues that this is efficient because it avoids rework — the design is finalized before testing begins. The quality manager argues that late verification means design errors are discovered too late, causing expensive rework and schedule delays. How would you resolve this disagreement?

**Answer:** I'd start by acknowledging that both perspectives have merit. The program manager is right that testing a moving target is inefficient — if the design is still changing, test results become obsolete quickly. The quality manager is right that discovering a fundamental design flaw at the end of the project is far more expensive than catching it early. The disagreement isn't really about whether to verify — it's about when and how to stage verification to balance these competing concerns.

My approach would be to reframe the conversation around risk and information value. Not all verification activities are equal: some tests provide information that's critical early in the design (e.g., does the power supply deliver the right voltages? does the sensor interface work?), while others can only be meaningfully performed once the design is stable (e.g., full system-level EMC testing). I'd propose a tiered verification strategy:

- **Early verification** for high-risk design elements — things where a failure would fundamentally change the architecture. For example, if a risk control depends on a particular sensor's response time, verifying that early prevents a costly redesign.
- **Incremental verification** as subsystems stabilize — module-level tests that can be performed as each board or firmware module is completed.
- **Final verification** for system-level tests that require the complete, integrated product.

I'd work with the systems engineer to categorize the verification activities in the traceability matrix by when they can meaningfully be performed, and with the program manager to understand the schedule constraints. The goal is to identify which tests, if delayed to the end, would create the highest risk of discovering a fundamental problem too late.

I'd also raise the point that verification isn't just about finding defects — it's about building confidence incrementally. If the team waits until the end to verify risk controls, they're making a bet that the design is correct without any evidence. That bet might pay off, but if it doesn't, the cost is much higher than the "rework" the program manager is trying to avoid — it could mean missing the regulatory submission deadline or shipping a product with an unverified safety mechanism.

The resolution would be a compromise: early verification for the highest-risk controls, incremental verification as subsystems complete, and final verification for system-level controls. I'd document the rationale for each test's timing in the verification plan so the decision is transparent and defensible.

**Possible follow-ups:**
- How would you identify which risk controls need early verification versus which can wait until the end?
- What if the program manager insists that early verification will delay the design work — how would you respond?