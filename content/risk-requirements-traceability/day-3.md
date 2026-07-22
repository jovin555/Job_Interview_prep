# risk-requirements-traceability — Day 3

## Q1: How would you approach linking risk control measures back to specific requirements in a system requirements specification (SRS) for a medical device?

**Answer:** I would establish a bidirectional traceability scheme where each risk control measure identified during the ISO 14971 risk management process is explicitly mapped to one or more requirements in the SRS. The approach starts during hazard analysis: when a risk control measure is selected (e.g., redundant pressure sensors, watchdog timer, isolation barrier), I would create a corresponding safety requirement in the SRS with a unique identifier. That requirement would reference the originating hazard ID and risk control number from the risk management file.

Conversely, every safety-related requirement in the SRS should be traceable back to a specific hazard and risk control decision. This prevents orphan requirements that add complexity without a documented safety rationale. I would capture these links in a traceability matrix that includes columns for: hazard ID, risk control measure, SRS requirement ID, design element implementing the control, and verification method. The key is that the traceability isn't just a post-hoc exercise — it should be maintained as requirements and risk controls evolve together during design reviews.

**Possible follow-ups:** How would you handle a situation where a single risk control measure maps to multiple requirements across different subsystems (hardware, firmware, mechanical)? What if a risk control is implemented purely in firmware — how does that change the traceability approach?

---

## Q2: During a design verification phase, you discover that a risk control requirement was verified as "pass" using a bench test, but the risk management file specifies that the control should be verified under simulated fault conditions. How would you address this discrepancy?

**Answer:** This is a serious gap because the verification activity doesn't match the risk control intent, which means the residual risk evaluation may be invalid. I would first flag the discrepancy immediately — it should not be closed as "pass" without resolution. The first step is to convene a small cross-functional discussion with the test engineer, the design engineer responsible for that control, and the risk management lead to understand why the bench test was chosen instead of the fault-condition test.

There are a few possible paths forward. If the bench test actually demonstrates the control's effectiveness under the relevant fault conditions (perhaps the bench setup inadvertently simulated those conditions), we might document that rationale and update the risk management file to reflect the actual verification method. If not, we need to either design a proper fault-condition test or, if that's impractical, reassess whether the risk control is adequate based on available evidence. This might involve updating the risk estimation (occurrence or detection ratings) and potentially adding a secondary control. The key principle is that the verification evidence must match what the risk analysis assumed — otherwise the residual risk is unsubstantiated.

**Possible follow-ups:** What documentation would you update to close this loop? How would you ensure this doesn't happen systematically across the project?

---

## Q3: How would you design a traceability matrix that captures the relationship between DFMEA failure modes and system-level requirements, particularly when a single failure mode could affect multiple requirements?

**Answer:** I would structure the matrix with a many-to-many relationship model rather than a simple one-to-one mapping. The DFMEA typically identifies failure modes at the function level (e.g., "pressure sensor output drifts high"), and each failure mode can degrade or nullify several system requirements (e.g., accuracy requirement, alarm activation requirement, data logging requirement). Conversely, a single requirement might be threatened by multiple failure modes.

The matrix columns would include: DFMEA function ID, failure mode, effect(s) on system behavior, severity rating, affected SRS requirement IDs, and whether existing risk controls are already captured as requirements. I would also add a column for "requirement criticality" — if a requirement is affected by multiple high-severity failure modes with inadequate controls, that requirement becomes a priority for design hardening or additional verification.

A practical technique is to use a requirements management tool that supports linking, but even a spreadsheet can work if the team maintains discipline. The important thing is that when a DFMEA action item generates a new risk control, that control gets added as a requirement and linked back to the specific failure mode. This closes the loop: the DFMEA drives new requirements, and the traceability matrix shows which failure modes each requirement addresses.

**Possible follow-ups:** How would you handle a DFMEA that identifies a failure mode with no corresponding requirement in the SRS — is that always a problem? What if the failure mode is considered "accepted risk" with no controls?

---

## Q4: (Behavioral) Imagine you're leading a project where the regulatory affairs team insists that every risk control measure must be directly verifiable by a single, unambiguous test, while the hardware team argues that some controls (e.g., component derating, PCB creepage distances) are inherently design-rule-based and can't be verified by a functional test. How would you resolve this disagreement?

**Answer:** I would start by acknowledging that both perspectives have merit. The regulatory team's concern is valid — if a risk control can't be verified, how do we demonstrate its effectiveness to a notified body? The hardware team is also correct that certain design practices (like following IPC-2221B for creepage or using derating guidelines per MIL-STD-975) are preventive controls verified by design review and inspection, not by functional test.

My approach would be to categorize risk controls into three verification types: (1) design rules verified by inspection/review (e.g., creepage distances, component ratings), (2) functional tests verified by bench or system-level testing (e.g., overcurrent protection trips at specified threshold), and (3) analysis-based verification (e.g., thermal simulation showing junction temperatures stay within limits). I would work with both teams to map each risk control to the appropriate verification type, documenting the rationale in the risk management file.

For the design-rule controls, I would propose that the verification evidence includes: the design rule standard referenced, the specific requirement (e.g., "minimum 8mm creepage between primary and secondary"), a screenshot or pointer to the PCB layout showing compliance, and the design review sign-off. This satisfies the regulatory need for objective evidence while respecting that not everything needs a functional test. The key is to agree on what constitutes acceptable evidence for each control type early in the project, documented in the verification and validation plan.

**Possible follow-ups:** How would you handle a situation where a notified body auditor challenges the adequacy of design-review-based verification for a critical safety control? What if the hardware team later changes a component and the creepage distance decreases — how do you maintain traceability?

---

## Q5: How would you approach creating a traceability scheme that connects system-level hazards (from ISO 14971) through to subsystem-level requirements and then to component-level design elements, in a system with multiple PCBA modules and firmware components?

**Answer:** I would use a hierarchical traceability model with three levels. At Level 1 (system), hazards are identified and linked to system-level safety requirements in the SRS. For example, a hazard like "overheating due to motor stall" generates a system requirement: "The system shall detect motor stall within 100ms and reduce motor current to < 100mA."

At Level 2 (subsystem), these system requirements decompose into subsystem requirements. The motor stall detection requirement might split into: a firmware requirement for stall detection algorithm, a hardware requirement for current sense circuit accuracy, and a power management requirement for current limiting response time. Each of these traces back to the parent system requirement and ultimately to the hazard.

At Level 3 (component/implementation), design elements (specific ICs, firmware modules, PCB traces) are linked to the subsystem requirements they fulfill. The current sense resistor value, the ADC sampling rate in firmware, and the MOSFET gate drive circuit all trace up to the current sense accuracy requirement.

The traceability matrix would use a parent-child numbering scheme (e.g., SRS-042 → HW-042-1, FW-042-1, PM-042-1) so that impact analysis is straightforward — if a component changes, you can see which subsystem and system requirements are affected. I would also include a column for "verification method" at each level: system-level hazards are verified by system validation testing, subsystem requirements by integration testing, and component-level by unit tests or inspection. This layered approach ensures that when a notified body asks "how do you know this hazard is controlled?", you can trace from hazard → system requirement → subsystem requirement → design element → verification evidence.

**Possible follow-ups:** How would you handle a situation where a single component (e.g., a microcontroller) implements requirements from multiple subsystems — how do you avoid traceability becoming unmanageably complex? What tools or methods would you use to maintain this hierarchy as requirements change during development?