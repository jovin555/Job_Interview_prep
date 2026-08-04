# risk-requirements-traceability — Day 14

## Q1: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity was written to verify a different requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a classic "false traceability" problem — the link exists on paper, but the evidence doesn't actually demonstrate the control works. My approach would be to first verify my understanding of the gap by reviewing the risk control's failure condition as documented in the risk management file, then comparing it against the test procedure's stimulus and pass/fail criteria. If the test doesn't inject the fault or stress the condition the control is designed to mitigate, the trace link is invalid regardless of whether the requirement numbers match.

I would then work with the verification engineer to determine what additional testing is needed. The key question is whether the existing test can be modified to include the fault injection, or whether a separate test is required. For example, if the risk control is a hardware overcurrent protection circuit, a nominal current draw test doesn't demonstrate the protection trips at the specified threshold — you need a test that forces an overcurrent condition and verifies the response.

I would document the discrepancy in the verification traceability matrix, flag it as a gap, and ensure the corrective action is tracked. I'd also review other trace links in the same area to check for similar issues — if one link was made incorrectly, others may have the same problem. Finally, I would update the verification planning process to require that each test explicitly state which failure condition it exercises, not just which requirement number it maps to.

**Possible follow-ups:**
- How would you distinguish between a test that "incidentally exercises" a control versus one that genuinely verifies it, when the control is always active during normal operation?
- What would you do if the schedule doesn't allow time to develop and execute a new fault-injection test before the design freeze?

---

## Q2: How would you approach establishing traceability for risk control measures that are implemented through design margins and derating — for example, selecting a component with a voltage rating well above the maximum expected stress — when these controls don't map cleanly to a functional requirement or a test?

**Answer:** Design-margin and derating controls are legitimate risk control measures, but they require a different traceability approach than functional controls. The key is to recognize that these are verified by analysis rather than by dynamic test, and the traceability artifacts need to reflect that distinction.

My approach would be to document the derating requirement explicitly in the SRS as a design constraint — for example, "all components shall be derated to at least 80% of their maximum rated voltage under worst-case operating conditions." This gives the control a traceable requirement identity. The risk management file would reference this requirement as the implementation of the risk control.

For verification, the appropriate activity is a design analysis — typically a derating calculation or stress analysis — documented in a report that shows each component's applied stress versus its rating, with the derating margin calculated. This analysis report becomes the verification artifact, and the trace link goes from the risk control → SRS requirement → design analysis report. The analysis must be performed by someone with appropriate expertise and must reference the specific components and their datasheet ratings.

The critical point is that "verification by inspection" is acceptable here, but it must be a rigorous, documented analysis — not just someone looking at the schematic and declaring it fine. The analysis needs clear acceptance criteria (the derating margin), a defined method (how stress was calculated), and objective evidence (the calculation results). I would also ensure the analysis covers worst-case conditions, including tolerances, temperature effects, and transient stresses, not just nominal operating points.

**Possible follow-ups:**
- How would you handle a derating control where the analysis shows the margin is adequate at nominal conditions but marginal under worst-case temperature?
- How would you ensure that a derating analysis remains valid when a component is substituted during manufacturing?

---

## Q3: How would you approach verifying that a risk control measure implemented as a firmware-based plausibility check — for example, rejecting sensor readings that change by more than a specified rate between consecutive samples — is correctly traced through to the system-level hazard it mitigates, and that the verification test adequately covers the failure scenario?

**Answer:** The first step is to trace the chain from the system-level hazard through to the firmware requirement. The hazard might be something like "incorrect therapy delivery due to sensor malfunction." The risk control is the plausibility check that detects the malfunction and triggers a safe state. The firmware requirement would specify the exact algorithm — the sampling rate, the maximum allowable change between samples, and the response when the check fails.

For verification, I would want to see three levels of testing. First, unit-level testing of the plausibility check algorithm itself — feeding it valid and invalid data sequences and confirming it accepts or rejects correctly. Second, integration testing where the check is exercised with the actual sensor interface — confirming that realistic sensor noise doesn't cause false rejections, and that genuine fault conditions (sensor short, sensor open, stuck-at-value) are detected. Third, system-level testing where the full hazard scenario is simulated — for example, injecting a sensor fault during operation and confirming the device enters the safe state.

The critical aspect is that the verification must test the failure scenario, not just nominal operation. A test that feeds valid data and confirms the check passes doesn't demonstrate the control works — you need fault injection. For a plausibility check, this means generating data sequences that violate the plausibility criteria and confirming the check responds correctly. I would also examine the boundary conditions — what happens with data that is exactly at the threshold, or just beyond it — since these are where implementation errors often hide.

Finally, I would ensure the traceability is bidirectional: the hazard links to the risk control, the risk control links to the firmware requirement, and the firmware requirement links to the verification test. Each link should be reviewed to confirm it's meaningful, not just present.

**Possible follow-ups:**
- How would you handle a situation where the plausibility check threshold is a tuning parameter that might change during development?
- What would you do if the sensor data rate is too slow to detect a fast-developing fault within the required response time?

---

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has multiple operating modes — for example, normal mode, standby mode, and fault mode — and a single risk control measure behaves differently in each mode?

**Answer:** This is a common source of traceability gaps because a single risk control can have mode-dependent behavior, and the requirements and verification activities often don't capture that nuance. My approach would be to treat each mode-specific behavior as a distinct traceable element, even if they share a common requirement parent.

The first step is to analyze the risk control across all operating modes and document, for each mode, what the control does, what triggers it, and what the expected response is. This analysis should be captured in the risk management file. Then, in the SRS, I would structure the requirements to reflect the mode-dependence — either as separate requirements per mode, or as a single requirement with explicit mode-specific clauses. The key is that the requirement text must unambiguously state which behavior applies in which mode.

For traceability, each mode-specific behavior needs its own verification activity. A test that verifies the control in normal mode does not verify it in fault mode — the device may enter fault mode through a different path, and the control may respond differently. The traceability matrix should therefore have separate links: risk control → requirement (mode-specific clause) → verification test (mode-specific scenario).

I would also pay attention to mode transitions. The risk control may behave differently during a transition than in a steady state — for example, a plausibility check might need to be suppressed during startup when sensor readings are settling. These transition behaviors need their own requirements and verification, and they're often where gaps appear. Finally, I would ensure the verification plan explicitly covers each mode and each transition, and that the traceability matrix clearly shows which mode each test exercises.

**Possible follow-ups:**
- How would you handle a risk control that is active in normal mode but intentionally disabled in maintenance mode — how would you document and verify that this is safe?
- How would you ensure that mode-dependent risk control behavior is captured in the DFMEA, not just in the requirements?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by analysis" — for example, a thermal simulation or a derating calculation — rather than physical tests. The quality manager argues that analysis is not objective evidence and demands physical testing for all risk controls. The systems engineer argues that some controls, like thermal derating or worst-case timing analysis, can only be practically verified by analysis, and that physical testing would be impractical or impossible. How would you resolve this disagreement?

**Answer:** I would start by acknowledging that both parties have valid points. The quality manager is right that analysis can be misused — an analysis that isn't properly validated, or that makes unrealistic assumptions, isn't objective evidence. The systems engineer is also right that some controls genuinely can't be verified by physical test — you can't easily create a worst-case thermal environment in a lab, and some timing margins are impractical to test directly.

My approach would be to establish clear criteria for when analysis is acceptable as verification evidence, and when physical testing is required. I would convene a discussion with both parties to agree on these criteria upfront. The criteria might include: the analysis must be performed using validated tools or methods; the analysis inputs must be traceable to datasheet values or measured data; the analysis must include sensitivity studies showing how results vary with input tolerances; and the analysis must be independently reviewed.

For controls where analysis is the primary verification, I would look for opportunities to supplement with targeted physical testing. For example, a thermal derating analysis might be supplemented with a thermocouple measurement at one or two critical points to validate the analysis model. This gives the quality manager physical evidence while acknowledging that full worst-case testing isn't practical.

I would also ensure that the distinction between verification methods is explicit in the traceability matrix — each risk control should show not just that it's verified, but how it's verified, and the rationale for choosing that method. If the quality manager still has concerns, I would offer to have an independent technical expert review the analysis to provide additional confidence. The goal is to reach a defensible position: the verification evidence, whether test or analysis, must be sufficient to demonstrate the control works under the conditions identified in the risk analysis.

**Possible follow-ups:**
- How would you handle a situation where the analysis is well-done but the quality manager still insists on physical testing because "the regulator expects tests"?
- What criteria would you use to decide whether a particular risk control absolutely requires physical testing versus analysis?