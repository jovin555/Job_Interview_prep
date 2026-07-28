# risk-requirements-traceability — Day 7

## Q1: How would you approach establishing traceability between risk control measures and requirements when the risk analysis identifies a control that spans multiple subsystems (e.g., hardware, firmware, and mechanical), and each subsystem team maintains its own separate requirements document?

**Answer:** This is a common challenge in complex medical devices where risk controls cut across engineering disciplines. I would approach this by first recognizing that a single risk control measure often decomposes into multiple design requirements—one per subsystem—and the traceability scheme needs to capture that decomposition explicitly.

My approach would be to create a "risk control decomposition" step in the risk management process. When a risk control measure is identified (e.g., "prevent over-pressurization of the patient circuit"), I would work with each subsystem lead to identify what each subsystem must contribute. The hardware team might need a pressure relief valve with specific cracking pressure; the firmware team might need a software-based pressure monitoring algorithm with a timeout; the mechanical team might need a specific tubing burst rating.

Each of these contributions becomes a derived requirement in the respective subsystem's requirements document, and each derived requirement traces back to the same parent risk control measure in the risk management file. The traceability matrix would then show a one-to-many relationship: one risk control measure maps to multiple subsystem requirements.

To maintain coherence across documents, I would use a common identifier scheme—for example, RCM-042 (risk control measure 42) would appear as "Derived from RCM-042" in the header or notes field of each subsystem requirement. This way, anyone reviewing the hardware requirements can see which risk control drove that requirement, and anyone reviewing the risk management file can see which subsystems are involved.

The key challenge is keeping these cross-references synchronized as requirements change. I would schedule regular cross-discipline traceability reviews, especially after any design change, to verify that all subsystems still have appropriate requirements derived from each shared risk control.

**Possible follow-ups:**
- How would you handle a situation where two subsystems have conflicting interpretations of what the risk control measure requires?
- What if one subsystem team argues that their contribution is "design implementation" rather than a requirement—how would you decide whether it belongs in the requirements document?

---

## Q2: How would you approach verifying that a risk control measure implemented as a hardware-based watchdog timer (monitoring a firmware heartbeat and asserting a system reset if the heartbeat stops) is correctly traced through requirements and adequately tested?

**Answer:** This is a good example of a risk control that involves both hardware and firmware working together, so the traceability and verification need to cover both the individual components and their interaction.

First, I would ensure the traceability captures three levels: the system-level risk control measure (e.g., "detect firmware lockup and reset the system within 100ms"), the derived hardware requirement (e.g., "the watchdog timer shall have a timeout period of 150ms ± 10%"), and the derived firmware requirement (e.g., "the firmware shall toggle the watchdog input pin at intervals not exceeding 100ms").

For verification, I would design tests that cover three scenarios: nominal operation (firmware healthy, watchdog should not reset), fault injection (firmware stops toggling, watchdog should reset), and boundary conditions (firmware toggles at exactly the maximum interval, watchdog should not falsely trigger). The hardware requirement for timeout accuracy would be verified by measuring the actual timeout period across temperature and voltage variations, while the firmware requirement would be verified by code inspection and by injecting deliberate delays to confirm the watchdog resets as expected.

A critical point is that the verification test must stress the system under the fault conditions identified in the risk analysis. If the risk analysis says "firmware lockup due to infinite loop," the test should simulate that specific failure mode—not just stop the heartbeat signal externally, but actually cause the firmware to enter an infinite loop (e.g., by corrupting a function pointer or disabling interrupts) to ensure the watchdog mechanism works end-to-end.

I would also ensure the traceability matrix links each verification activity back to the specific requirement it tests, and that the risk management file documents which verification results demonstrate that the risk control is effective.

**Possible follow-ups:**
- How would you handle a situation where the watchdog timer passes all functional tests but fails during EMC testing—would that be a traceability gap or a separate issue?
- What if the firmware team wants to change the heartbeat interval during development—how would you manage the traceability impact?

---

## Q3: How would you approach determining whether a requirement in the SRS is truly a "safety requirement" derived from risk management, versus a "performance requirement" that exists for functional reasons, and how would you decide which traceability links are necessary for each type?

**Answer:** This is a nuanced distinction that often causes confusion in medical device development. My approach would be to classify requirements into three categories based on their origin and purpose, rather than a binary safety-versus-performance split.

First, requirements that directly implement a risk control measure are clearly safety requirements and must have bidirectional traceability to the risk management file. These are non-negotiable—if the risk analysis says "the device shall shut down within 500ms of detecting over-temperature," that requirement must be traceable to the hazard it mitigates.

Second, requirements that are not themselves risk controls but are necessary preconditions for a risk control to work effectively. For example, "the temperature sensor shall have an accuracy of ±1°C" might not be a risk control itself, but if the over-temperature shutdown depends on accurate sensing, this requirement has an indirect safety significance. I would trace these as "supporting requirements" linked to the risk control measure, with a note explaining the dependency.

Third, purely functional or performance requirements with no safety significance—for example, "the device shall display the time in 24-hour format." These do not need risk traceability, but they should still be traced to design elements and verification tests for completeness.

The decision framework I would use is: if removing or changing this requirement could increase the probability or severity of a hazardous situation, it needs risk traceability. If not, it's a functional requirement. I would document this rationale in the requirements management plan so the team has clear criteria.

For the traceability matrix, I would use a column or tag indicating "safety-related" versus "functional," so reviewers can quickly identify which requirements have risk implications. This also helps during design reviews—safety-related requirements should get additional scrutiny and may require different verification rigor.

**Possible follow-ups:**
- What if a requirement starts as purely functional but later becomes safety-related due to a design change—how would you handle the traceability update?
- How would you handle a requirement that is borderline—for example, a battery life requirement that, if not met, could cause the device to fail during a critical procedure?

---

## Q4: How would you approach creating a traceability scheme that captures the evolution of risk control measures and their associated requirements across multiple design iterations, given that both the risk analysis and the requirements specification are living documents?

**Answer:** This is a practical challenge that many teams underestimate. The key insight is that traceability is not a one-time mapping exercise—it's a configuration management problem. My approach would be to treat traceability links as versioned artifacts, just like requirements and risk analyses.

I would establish a baseline at each major design review (e.g., concept review, design input review, design output review). At each baseline, I would capture a snapshot of the traceability matrix showing which version of each requirement links to which version of each risk control measure. This creates an audit trail that shows how the traceability evolved.

For managing changes between baselines, I would use a change impact analysis process. When a requirement changes, the traceability matrix should flag all linked risk control measures for review—does the change affect the effectiveness of the risk control? Conversely, when a risk control measure is modified (e.g., severity rating changes, or a new control is added), the matrix should flag all linked requirements for potential update.

I would use a simple status field for each traceability link: "current" (both sides are up to date), "pending review" (one side changed, the other needs assessment), or "superseded" (the link was valid in a previous baseline but no longer applies). This allows the team to see at a glance which links need attention.

For the traceability matrix itself, I would include columns for: requirement ID and version, risk control measure ID and version, link type (direct implementation, supporting, verification), link status, and a notes field for rationale. The matrix should be maintained in a tool that supports versioning—even a spreadsheet with proper change tracking can work for smaller projects.

The most important practice is to never delete a traceability link without documenting why. If a risk control measure is removed because the hazard was re-evaluated and found to be acceptable, the link should be marked as "superseded" with a reference to the risk management decision, not simply deleted. This preserves the audit trail for regulatory review.

**Possible follow-ups:**
- How would you handle a situation where the risk analysis is updated but the requirements team is too busy to update the traceability matrix immediately—what controls would you put in place?
- What if the traceability matrix becomes so complex with version history that it's difficult to use for day-to-day work—how would you simplify it?

---

## Q5: (Behavioral) Imagine you're leading a project where the risk management team has completed a thorough hazard analysis and identified several risk control measures, but the systems engineer responsible for the SRS argues that risk control measures should not appear as separate requirements in the SRS because they are "implementation details" that constrain design freedom. The quality manager insists they must be in the SRS for traceability. How would you resolve this disagreement?

**Answer:** This is a classic tension between design flexibility and regulatory traceability, and I would address it by finding a middle ground that satisfies both concerns without compromising either.

First, I would acknowledge the systems engineer's valid concern: if every risk control measure is written as a prescriptive requirement (e.g., "the firmware shall implement a 200ms timeout on sensor readings"), it does constrain the design team's ability to find better solutions. However, I would also point out that risk control measures are not optional design choices—they are regulatory commitments that the device must meet to be safe.

My proposed resolution would be to distinguish between the "what" and the "how" in the SRS. The SRS should capture the safety requirement at a functional level—for example, "the device shall detect loss of sensor signal and enter a safe state within 200ms." This states the required behavior without prescribing the implementation (timeout, plausibility check, hardware comparator, etc.). The specific implementation details (e.g., "a 200ms software timeout using Timer1") belong in the design specification or the risk management file, not the SRS.

This approach satisfies both parties: the quality manager gets traceability because the functional safety requirement is in the SRS and links to the risk control measure, and the systems engineer preserves design freedom because the implementation is left to the design team. The risk management file would document the chosen implementation and why it's effective, but that detail doesn't constrain the SRS.

If the disagreement persists, I would facilitate a small working session with both parties to walk through a concrete example from the project. We would take one risk control measure and draft it as a functional requirement, then discuss whether that level of detail is acceptable. Often, seeing a real example helps people move from abstract positions to practical agreement.

I would also document the decision in the project's requirements management plan, so future disagreements can be resolved by referring to the established convention rather than re-litigating the same issue.

**Possible follow-ups:**
- What if the quality manager insists that without the implementation detail in the SRS, the traceability is incomplete because you can't verify "a 200ms timeout" from a requirement that just says "enter safe state within 200ms"?
- How would you handle a situation where the risk control measure is inherently implementation-specific—for example, a hardware-based analog comparator with specific threshold voltages that can't be stated as a functional requirement?