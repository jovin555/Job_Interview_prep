# risk-requirements-traceability — Day 22

## Q1: How would you approach establishing traceability for a risk control measure that is implemented through a combination of hardware and firmware, where the hardware team documents the control in their design specification and the firmware team documents their portion in a software requirements document — but neither document references the other, and the risk management file treats the control as a single integrated measure?

**Answer:** The core problem here is that the risk management file treats the control as one logical measure, but the implementation artifacts are split across two engineering domains with no cross-references. I would start by creating a single "risk control implementation record" — a small document or section in the risk management file that explicitly decomposes the integrated control into its hardware and firmware contributions, and defines the interface between them. For example, if the control is an over-temperature shutdown, the record would state: "Hardware portion: temperature sensor and analog comparator that asserts an interrupt line when temperature exceeds X. Firmware portion: upon receiving the interrupt, firmware shall disable the motor drive output within Y ms." This record becomes the anchor point that both teams reference.

Next, I would require each team to add a cross-reference in their own documents. The hardware design specification would note "implements hardware portion of risk control RC-014 (see risk management file §3.2)" and the software requirements document would note "implements firmware portion of risk control RC-014 (see risk management file §3.2)". This creates bidirectional traceability without forcing either team to adopt the other's document structure or numbering scheme.

For verification, I would define three levels: (1) hardware verification of the comparator trip point and interrupt assertion, (2) firmware verification of the response logic (e.g., interrupt handler disables output within timing budget), and (3) system-level verification that the integrated control actually prevents the hazard — for example, applying heat and confirming the motor stops. All three levels trace back to the same risk control record. The key principle is that the risk management file owns the logical control, and the engineering documents own the implementation — but they must explicitly reference each other so an auditor can follow the complete path.

**Possible follow-ups:**
- What if the hardware and firmware teams use different tools for requirements management (e.g., one uses a database, the other uses documents)? How would you maintain the cross-references?
- How would you handle a situation where the hardware portion of the control is revised (e.g., a different comparator with a different threshold) — what needs to be updated and in what order?

---

## Q2: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading — for example, rejecting readings that change by more than a specified rate between consecutive samples — needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** The key question is whether the risk control's effectiveness depends on characteristics that differ between the development board and production hardware. For a plausibility check on sensor readings, I would consider three factors. First, does the control depend on the actual sensor and its signal chain? If the plausibility check operates on digital values that have already been converted by the ADC, then the sensor's analog characteristics — noise, offset, response time — could affect whether the check behaves correctly in the real system. A development board with a different sensor or different analog front-end might not exercise the same failure modes.

Second, does the control depend on timing that could be affected by the hardware? For example, if the check involves a timeout or a rate calculation, the system clock and interrupt latency on production hardware could differ from the development board. Third, does the control interact with other hardware that isn't present on the development board — for example, a watchdog timer, a power management IC, or a communication bus?

If the plausibility check is purely algorithmic — operating on values that are injected via test software, with no dependence on the analog chain or hardware timing — then development-board testing might be sufficient, provided the microcontroller is identical and the firmware binary is the same. However, I would still recommend at least a limited verification on production hardware to confirm that the firmware runs correctly in the target environment, even if the full fault-injection matrix is done on the development board.

The regulatory principle is that verification should demonstrate the control works in the context in which it will be used. If there's any reasonable argument that the production environment could affect the control's behavior, then production-hardware testing is warranted. When in doubt, I would err toward production-representative hardware for at least a subset of tests, and document the rationale for whatever level of testing is chosen.

**Possible follow-ups:**
- What specific test cases would you run on the development board versus the production hardware?
- How would you document the rationale for your testing approach in the verification plan so an auditor understands why development-board testing was acceptable for certain cases?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** This is one of the more challenging traceability scenarios because the hazard is mitigated by a *sequence* of actions across nodes, and no single node's requirement set tells the complete story. I would approach this by first defining the hazard-to-control path at the system level, then decomposing it into node-level contributions.

The first step is to document the coordinated control as a system-level sequence or state machine in the risk management file. For example: "Hazard H-017 (motor overspeed) is mitigated by: (1) Node A detects abnormal speed via its sensor and broadcasts a fault message on the bus; (2) Node B receives the fault message and disables its motor drive output within 50 ms; (3) Node C logs the event and alerts the operator." This sequence definition becomes the anchor — it's the single source of truth for how the control works across nodes.

Next, I would decompose this into per-node requirements. Node A gets a requirement to detect the condition and broadcast the fault message with a specified format and timing. Node B gets a requirement to receive the fault message, validate it, and disable the output within the timing budget. Node C gets a requirement to log and alert. Each of these node-level requirements traces up to the system-level control sequence, which traces up to the hazard.

For the traceability matrix, I would use a hierarchical structure: hazard → system-level control sequence → per-node requirements → per-node verification. The system-level control sequence is the critical linking element — without it, the matrix would show individual node requirements with no indication of how they combine to mitigate the hazard.

For verification, I would include both node-level tests (e.g., Node B correctly disables its output when it receives a fault message) and a system-level integration test that exercises the full sequence (e.g., inject a fault at Node A and verify the motor stops within the timing budget). The system-level test is essential because it verifies the coordination — bus timing, message validation, and the overall sequence — which node-level tests cannot capture.

**Possible follow-ups:**
- How would you handle a situation where the bus communication itself is part of the risk control — for example, if a fault message is corrupted or delayed, is there a fallback mechanism?
- What if different nodes are developed by different teams with different requirement management tools — how would you maintain the cross-node traceability?

---

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification test, but the test was written to verify a *different* requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a common and dangerous gap — the traceability matrix looks complete because there's a link between the risk control and a test, but the test doesn't actually demonstrate that the control works under the conditions that matter. The first step is to recognize that a traceability link is only meaningful if the verification activity actually exercises the failure condition the control is meant to mitigate.

I would start by reviewing the risk analysis to identify the specific failure condition and the control's intended behavior. Then I would compare that against what the test actually does. If the test only exercises nominal conditions, then it's not providing evidence that the control works — it's just showing that the system doesn't malfunction when nothing goes wrong. That's necessary but not sufficient.

The fix is to write a dedicated verification test that specifically stresses the failure condition. For example, if the risk control is an overcurrent protection circuit, the test should inject an overcurrent condition and verify the protection activates. If the risk control is a firmware-based plausibility check, the test should inject sensor readings that violate the plausibility criteria and verify the check rejects them.

I would also update the traceability matrix to distinguish between tests that *incidentally* exercise a control under nominal conditions and tests that *specifically* stress the failure condition. This might mean adding a column for "failure condition exercised" or creating separate traceability links for the dedicated test. The key is that the verification evidence must demonstrate the control's effectiveness under the conditions identified in the risk analysis — not just that the system happens to pass a test that touches the control's code path.

If the original test was already executed and passed, I would document that it provides partial evidence (nominal operation) but does not satisfy the verification requirement for the risk control. The dedicated test would need to be added to the verification plan, executed, and documented before the risk control can be considered verified.

**Possible follow-ups:**
- How would you handle this if the dedicated test requires additional test fixtures or equipment that aren't currently available?
- What if the risk analysis doesn't clearly specify the failure conditions — how would you determine what conditions the test should stress?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by similarity" — meaning the team is relying on test results from a previous product that used a similar component or design. The quality manager argues that similarity is not acceptable evidence for risk controls, because the previous product wasn't tested under the same conditions. The systems engineer argues that the components are identical, the design is nearly the same, and re-running the tests would waste time and money. How would you resolve this disagreement?

**Answer:** I would start by acknowledging that both sides have legitimate points. The systems engineer is right that re-running tests for identical components in nearly identical designs can be wasteful, and the quality manager is right that "similar" is not the same as "identical" — especially for risk controls where the consequences of a failure are severe.

My approach would be to establish clear criteria for when verification by similarity is acceptable, rather than treating it as an all-or-nothing question. I would propose a structured assessment with specific questions: Are the components identical (same manufacturer, same part number, same revision)? Is the application context the same — same voltage, current, temperature range, and environmental conditions? Is the interface to the component the same — same circuit topology, same firmware interaction, same loading? Were the original tests performed under conditions that are representative of the current product's use? Is there documented evidence of the original test results, including the test method and pass criteria?

If the answer to all of these is yes, then verification by similarity might be defensible — but it needs to be documented as a formal analysis, not just a casual assertion. I would ask the systems engineer to write up a similarity assessment that addresses each of these criteria, references the original test evidence, and explains why the previous test results are valid for the current product. This assessment would be reviewed by the quality manager and the engineering team.

If there's any doubt — for example, the component is identical but the PCB layout around it changed, or the firmware interaction is different — then I would require at least a subset of tests to be re-run on the current hardware. The cost of re-running a few targeted tests is usually far less than the cost of discovering a risk control failure after release.

I would also frame this as a risk-based decision. The question isn't just "can we use similarity?" — it's "what is the residual risk if the similarity assessment is wrong, and is that risk acceptable?" For risk controls that mitigate severe hazards, I would lean toward requiring actual testing unless the similarity case is exceptionally strong.

**Possible follow-ups:**
- What specific criteria would you include in the similarity assessment document?
- How would you handle a situation where the previous product's test results are incomplete or poorly documented?