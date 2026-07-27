# risk-requirements-traceability — Day 6

## Q1: How would you approach determining whether a risk control measure should be implemented in hardware, firmware, or as a procedural/user-level control, and how would you trace that decision through the requirements and verification artifacts?

**Answer:** The choice of implementation layer for a risk control measure should follow the ISO 14971 hierarchy of risk control options: inherent safety by design first, then protective measures, then information for safety. I would start by evaluating whether the hazard can be eliminated through design (e.g., physical isolation, mechanical interlock) before considering active electronic controls. If an active control is needed, I'd assess the trade-offs: hardware controls (e.g., hardware watchdog timers, analog comparators, redundant sensors) are generally more deterministic and harder to defeat but add cost and board space; firmware controls (e.g., software timeouts, plausibility checks, state machine guards) are more flexible and easier to update but require careful analysis of single-point failures in the software itself. Procedural controls (e.g., user training, warning labels) are the least reliable and should only be used when engineering controls are infeasible.

Once the implementation layer is chosen, I would document the decision in the risk management file with a clear rationale. The risk control measure would then be captured as a derived requirement in the SRS, with a trace link back to the hazard it mitigates. The verification strategy would depend on the layer: hardware controls might be verified by fault injection testing or worst-case analysis; firmware controls by unit testing, integration testing, and fault injection; procedural controls by usability testing or inspection. The traceability matrix would capture the chain: hazard → risk control measure → derived requirement → design element (specific circuit, firmware module, or procedure) → verification activity → verification result. This ensures that if the implementation layer changes during development, the traceability makes the impact clear and forces re-verification.

**Possible follow-ups:**
- How would you handle a situation where a firmware-based risk control measure could be defeated by a single hardware failure (e.g., a clock failure that stops the watchdog timer from incrementing)?
- What criteria would you use to decide whether a risk control measure should be implemented as a separate hardware circuit versus integrated into an existing microcontroller?

---

## Q2: During a design verification campaign, you find that a risk control requirement was verified using simulation only, but the risk management file specifies that the control must be verified on production-representative hardware. How would you address this discrepancy?

**Answer:** This is a gap between what was planned in the risk management file and what was actually executed in verification. My first step would be to assess the severity of the discrepancy: is the simulation model sufficiently accurate to demonstrate the control's effectiveness under the relevant fault conditions, or does the risk analysis specifically require hardware testing because of factors like component tolerances, parasitic effects, or timing uncertainties that simulation cannot capture? I would review the simulation fidelity—what was modeled, what was abstracted, and whether the fault conditions were injected correctly.

If the simulation is deemed insufficient, I would initiate a corrective action: either repeat the verification on actual hardware, or formally update the risk management file to accept simulation as the verification method, with documented justification. This justification would need to explain why simulation provides equivalent confidence—for example, if the control is a purely digital logic function with no analog dependencies, and the simulation used timing-accurate models with worst-case process corners. I would then update the traceability matrix to reflect the actual verification method used and the rationale for any deviation from the original plan. The key principle is that the traceability must reflect what was actually done, not what was planned, and any deviation must be documented with a risk-based justification.

**Possible follow-ups:**
- What if the hardware needed for verification won't be available until after the regulatory submission deadline—how would you prioritize which risk controls absolutely require hardware testing?
- How would you distinguish between a simulation that is "good enough" and one that introduces unacceptable risk?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements across multiple design iterations, given that requirements and risk analyses evolve as the design matures?

**Answer:** The key challenge is maintaining bidirectional traceability as both the SRS and the risk management file change over time. I would establish a version-controlled traceability matrix from the start, where each requirement and each risk control measure has a unique identifier that persists across revisions. When a requirement changes, I would assess whether the change affects any linked risk control measures—for example, if a timing requirement is relaxed, does that affect a firmware-based timeout that was designed to mitigate a specific hazard? Conversely, when a risk analysis identifies a new hazard or modifies a risk control measure, I would check whether existing requirements still adequately capture the control.

I would use a change impact analysis process: any proposed change to a requirement or risk control measure triggers a review of all linked artifacts. The traceability matrix would include a "change history" column or a separate change log that records what changed, when, and why, along with the re-verification status. For iterative development, I would also flag requirements and risk controls that are still in draft or under review, so the traceability matrix clearly distinguishes between "baselined" and "in-progress" items. At each design review, the traceability matrix would be updated and reviewed for completeness—no orphaned requirements, no risk controls without verification links, and no verification activities without corresponding risk control requirements. This approach ensures that traceability is a living artifact that evolves with the design, not a static document that becomes obsolete after the first revision.

**Possible follow-ups:**
- How would you handle a situation where a risk control measure is removed during development because the hazard is re-evaluated as acceptable—what happens to the linked requirements and verification artifacts?
- What tool features would you look for to support version-controlled traceability across design iterations?

---

## Q4: (Behavioral) Imagine you're leading a project where the hardware team has identified a risk control measure that requires a firmware-implemented plausibility check on a sensor reading. The firmware lead argues that the check should be documented as a firmware requirement in the SRS, while the hardware lead insists it should remain only in the risk management file to avoid "cluttering" the SRS with implementation details. How would you resolve this disagreement?

**Answer:** I would start by acknowledging both perspectives: the firmware lead wants clear, traceable requirements that the firmware team can implement and verify against, while the hardware lead is concerned about the SRS becoming bloated with low-level implementation details that don't belong at the system level. The resolution lies in understanding what level of abstraction the SRS should capture.

I would propose a compromise: the risk control measure itself—"the system shall detect a sensor fault and enter a safe state within 200ms"—belongs in the SRS as a derived requirement, because it describes a system-level behavior that is verifiable at the system level. The specific implementation detail—"the firmware shall implement a plausibility check comparing sensor A to sensor B with a tolerance of ±10%"—would be documented in the firmware requirements specification (a lower-level document) or in the design description, with a trace link from the SRS requirement. This way, the SRS remains at the right level of abstraction while still capturing all risk control measures as verifiable requirements. The traceability matrix would show: hazard → risk control measure (in risk file) → system-level derived requirement (in SRS) → firmware requirement (in firmware spec) → verification activity.

I would facilitate a meeting with both leads to agree on this layered approach and document the decision in the project's requirements management plan. If the disagreement persists, I would escalate to the systems engineer or project manager to make a final call, but I would frame the discussion around the principle that risk control measures must be verifiable, and the SRS is the appropriate place for verifiable system-level requirements.

**Possible follow-ups:**
- What if the firmware lead argues that without the implementation detail in the SRS, the verification team won't know what to test—how would you address that concern?
- How would you handle a similar disagreement if the project uses a single SRS document with no separate subsystem-level specifications?

---

## Q5: How would you approach verifying that a risk control measure implemented as a hardware-based analog comparator (e.g., monitoring a voltage rail and asserting a reset if it drops below a threshold) is correctly traced through to the system-level hazard it mitigates, and that the verification test adequately covers the failure scenario?

**Answer:** For a hardware-based analog comparator used as a risk control measure, the traceability chain would be: system-level hazard (e.g., "undervoltage condition causes motor controller to operate outside safe limits") → risk control measure (e.g., "undervoltage detection circuit shall assert system reset when Vcc drops below 4.5V for more than 10ms") → derived requirement in SRS (e.g., "the system shall detect an undervoltage condition on the 5V rail and enter a safe state within 50ms") → design element (the comparator circuit with its reference voltage, hysteresis, and debounce filter) → verification activity.

The verification test must cover the specific failure scenario identified in the risk analysis. This means testing not just nominal operation (e.g., slowly reducing the voltage and observing the reset threshold) but also the fault conditions that the risk analysis assumes could occur. For example, if the risk analysis assumes that a regulator failure could cause the 5V rail to drop rapidly, the verification test should include a fast transient below the threshold to ensure the comparator responds within the required time. The test should also cover edge cases: what happens at the exact threshold voltage (hysteresis margin), what happens with noise on the rail (debounce filter effectiveness), and what happens if the comparator's own reference voltage drifts with temperature.

To ensure adequate traceability, I would document in the verification procedure which specific risk scenario each test step addresses, and cross-reference the test results back to the risk control measure in the risk management file. If the verification test passes but only under nominal conditions, that's a gap—the test must stress the system under the conditions that the risk analysis identified as credible failure scenarios. The traceability matrix would capture this by linking each verification test to the specific failure mode and fault condition it exercises.

**Possible follow-ups:**
- How would you verify a risk control measure that relies on component derating (e.g., using a capacitor rated for twice the expected voltage)—can this be verified by test, or does it require analysis?
- What would you do if the verification test reveals that the comparator's response time is 15ms under worst-case conditions, but the risk analysis assumed a 10ms response time—how would you assess whether this is acceptable?