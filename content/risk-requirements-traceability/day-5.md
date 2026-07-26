# risk-requirements-traceability — Day 5

## Q1: How would you approach determining the appropriate level of granularity for requirements in a risk-traceability context, particularly when a single risk control measure might map to multiple design requirements or vice versa?

**Answer:** The granularity question is fundamentally about balancing traceability clarity against maintenance burden. I'd start by establishing a principle: requirements should be written at the level where they can be unambiguously verified. For risk control measures, this means each requirement should correspond to a single, testable design decision or behavior.

When a single risk control measure maps to multiple design requirements, I'd document that explicitly in the risk management file. For example, a risk control like "prevent over-temperature condition" might decompose into a hardware requirement for a thermal cutoff circuit, a firmware requirement for temperature monitoring with a shutdown threshold, and a mechanical requirement for heatsink sizing. Each gets its own requirement ID in the SRS, and the traceability matrix links all three back to the same risk control ID in the risk management file.

Conversely, when multiple risk controls map to a single requirement, that's a red flag that the requirement may be too broad or that the risk controls aren't truly independent. I'd examine whether the requirement can be split, or whether the risk controls are actually different aspects of the same design feature.

The key is bidirectional traceability: from each risk control in the DFMEA or hazard analysis, you should be able to find the corresponding requirement(s) in the SRS, and from each requirement, you should be able to see which risk control(s) it implements. If a requirement has no risk control linkage, it's either not safety-critical (which is fine) or it's a gap in the risk analysis.

**Possible follow-ups:** How would you handle a situation where a risk control measure is implemented partly in hardware and partly in firmware, and the verification methods differ significantly between the two? What criteria would you use to decide whether to write one combined requirement or two separate ones?

---

## Q2: During a design verification campaign, you discover that a risk control requirement was verified using a nominal-condition test, but the risk analysis specifies that the control must be verified under worst-case fault conditions. How would you address this discrepancy?

**Answer:** This is a serious gap because the verification doesn't actually demonstrate that the risk control works under the conditions it was designed for. I'd treat this as a non-conformance that needs immediate attention.

First, I'd document the discrepancy formally in the design history file, noting exactly which risk control, which requirement, and which test method are involved. Then I'd convene a small team including the test engineer, the design engineer responsible for that subsystem, and a risk management representative to assess the situation.

The assessment would answer two questions: (1) Does the existing test result provide any useful information about performance under fault conditions? Sometimes a nominal test can partially validate a design, even if it doesn't fully cover the fault scenario. (2) What would it take to create a proper fault-condition test? This might involve modifying test fixtures, creating fault injection hardware, or developing new firmware test modes.

If the fault-condition test is feasible within the project timeline, I'd create a corrective action plan: update the test protocol, execute the new test, and document results. If it's not feasible, I'd need to evaluate whether the risk control can be verified by analysis instead—for example, a worst-case circuit simulation or a tolerance analysis that demonstrates the control will work under fault conditions. This would need to be documented as a verification by analysis rather than by test, with clear justification.

In either case, the risk management file should be updated to reflect the actual verification method used, and the residual risk should be re-evaluated if the verification approach changed.

**Possible follow-ups:** What if the fault-condition test would require hardware modifications that delay the project by several months? How would you balance regulatory compliance against schedule pressure? What alternative verification strategies might be acceptable to a notified body?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures implemented in firmware (e.g., software-based timeouts, plausibility checks, state machine guards) back to system-level hazards, given that firmware requirements often change more frequently than hardware requirements during development?

**Answer:** Firmware's inherent flexibility is both an advantage and a challenge for traceability. The advantage is that we can iterate quickly; the challenge is that traceability documentation can become stale if not maintained alongside code changes.

I'd structure the traceability scheme with a clear separation between the *intent* of a firmware-based risk control and its *implementation*. The intent—what the firmware must do to mitigate a hazard—gets captured as a stable, version-controlled requirement in the SRS, with a unique ID that links to the risk management file. The implementation details (specific timeout values, state machine transitions, threshold comparisons) are documented in the firmware design specification or in code comments, but the traceability chain goes through the SRS requirement, not through the code itself.

For example, a hazard like "motor continues running after sensor failure" might lead to a risk control: "firmware shall disable motor within 200ms of detecting invalid sensor data." This becomes a requirement in the SRS with ID REQ-042. The traceability matrix links REQ-042 to the hazard in the risk management file. During development, the firmware team might implement this as a watchdog timer with a 150ms timeout, then later change it to a 180ms timeout after testing—but REQ-042 remains unchanged as long as the 200ms upper bound is respected.

To handle the frequency of firmware changes, I'd implement a lightweight change-impact process: whenever a firmware requirement or its implementation changes, the firmware lead checks whether the change affects any risk control measure. If it does, the traceability matrix and risk management file are updated as part of the same change request. This prevents traceability from becoming a separate, after-the-fact documentation activity.

**Possible follow-ups:** How would you handle a firmware change that reduces a timeout from 200ms to 50ms—does that require re-verification of the risk control? What about a change that increases it to 250ms, which would violate the original requirement?

---

## Q4: How would you approach integrating risk traceability into the design review process, so that reviewers can easily assess whether risk controls are properly traced through to requirements and verification activities?

**Answer:** I'd design the design review package to include a risk-traceability view as a standard artifact, not as an afterthought. The goal is to make it easy for reviewers to answer three questions for each risk control: (1) Is there a requirement that implements this control? (2) Is there a verification activity that tests this requirement? (3) Does the verification method actually stress the system under the fault conditions identified in the risk analysis?

Practically, I'd create a risk-traceability matrix that's structured as a table with columns for: hazard ID, risk control ID, SRS requirement ID(s), verification method, verification result (once available), and any notes about assumptions or limitations. This matrix would be included in the design review binder alongside the SRS, architecture diagrams, and test plans.

During the review, I'd walk through a few representative examples to demonstrate the traceability chain—for instance, picking a high-severity hazard and showing how it flows through to a specific test case. This helps reviewers understand the traceability scheme and spot gaps more effectively than if they had to cross-reference multiple documents.

I'd also include a "traceability coverage" metric in the review checklist: are there any risk controls with no corresponding requirements? Any requirements with no verification? Any verification activities that don't match the risk control's intended operating conditions? These become action items for the design team before the review can be closed.

For complex systems with multiple subsystems, I'd use color-coding or visual indicators in the matrix to show which subsystem owns each requirement, making it easier for reviewers to focus on their area of expertise.

**Possible follow-ups:** How would you handle a design review where the risk-traceability matrix is complete, but several reviewers argue that the verification methods are inadequate for the severity of the hazards? How would you facilitate that discussion and drive it to resolution?

---

## Q5: (Behavioral) Imagine you're leading a project where the quality assurance manager insists that every single requirement in the SRS—including non-functional requirements like "the device shall operate at 5V ± 10%"—must be traced to a risk control measure, arguing that otherwise there's no justification for the requirement's existence. The systems engineer disagrees, saying that many requirements are design decisions or performance targets, not risk controls. How would you resolve this disagreement?

**Answer:** I'd start by acknowledging both perspectives have merit. The QA manager is correctly focused on ensuring that every requirement has a purpose and isn't arbitrary. The systems engineer is correctly recognizing that not all requirements are safety-critical—some exist for performance, usability, manufacturability, or cost reasons.

I'd propose a middle ground: we categorize requirements into two tiers. Tier 1 requirements are those that implement risk control measures or are otherwise safety-critical—these must have explicit traceability to the risk management file. Tier 2 requirements are all others—performance targets, design preferences, interface standards—and they don't need risk traceability, but they should still have a brief justification documented (e.g., "derived from system performance budget," "required for compatibility with existing test equipment").

To implement this, I'd add a "risk-related" flag or a "traceability type" field to the requirements management tool. During the design review, we'd verify that all Tier 1 requirements have proper risk traceability, and that Tier 2 requirements have at least a brief rationale. This satisfies the QA manager's concern about arbitrary requirements while avoiding the overhead of forcing every "5V ± 10%" requirement to link to a hazard analysis.

I'd also facilitate a discussion about what "justification" means for non-safety requirements. For example, "the device shall operate at 5V ± 10%" might be justified by the power supply design budget, the battery voltage range, or the input voltage tolerance of downstream components—none of which are risk controls, but all of which are valid design reasons. Documenting that rationale in a comment field or a design decision log would address the QA manager's underlying concern without forcing artificial risk traceability.

**Possible follow-ups:** What if the QA manager continues to insist that all requirements must have risk traceability, citing a regulatory auditor who previously flagged a similar issue at their previous company? How would you handle that escalation?