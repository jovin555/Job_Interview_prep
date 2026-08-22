# risk-requirements-traceability — Day 32

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a combination of hardware and firmware, where the hardware team documents the control in their design specification and the firmware team documents their portion in a software requirements document — but neither document references the other, and the risk management file treats the control as a single integrated measure?

**Answer:** The core issue here is that the risk management file treats the control as one logical measure, but the implementation artifacts are split across two engineering domains with independent document hierarchies. I would start by creating a single "integration point" in the traceability scheme — a shared identifier or link record that both the hardware and firmware documents can reference. This could be a risk control ID that appears in both documents, or a small integration matrix that maps the single risk control ID to the specific hardware design element and the specific firmware requirement.

The key principle is that the traceability must be bidirectional: from the hazard → risk control → hardware element + firmware requirement → verification activities. I would establish a convention where the hardware design specification includes a section that explicitly references the risk control ID and states "firmware portion documented in [firmware document reference]," and vice versa. This creates the cross-reference that's currently missing.

For verification, I would ensure there are three levels: a hardware-level test that verifies the sensor/comparator function, a firmware-level test that verifies the response logic, and a system-level test that verifies the integrated behavior. Each test should reference the same risk control ID, so the complete path is visible even though the artifacts live in different documents.

**Possible follow-ups:**
- How would you handle the situation where the hardware and firmware teams use different numbering schemes for their documents?
- What would you do if the system-level verification test is scheduled much later than the subsystem tests, and you need interim evidence that the control is likely to work?

---

## Q2: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading — for example, rejecting readings that change by more than a specified rate between consecutive samples — needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** The decision hinges on what aspects of the control's behavior could differ between the development board and production hardware. For a plausibility check, the critical factors are: the timing characteristics of the sensor interface, the actual sensor output behavior under fault conditions, and any interactions with other firmware tasks or interrupts that could affect sampling intervals.

If the plausibility check is purely algorithmic — comparing consecutive values against a rate limit — and the timing is controlled by a timer that behaves identically on both platforms, then a development board with the same microcontroller might be sufficient for unit-level verification. However, I would be cautious: the development board likely uses a different sensor or a simulated sensor input, so the verification wouldn't exercise the real sensor's failure modes. For example, a real sensor might fail by holding its last value, by outputting a rail voltage, or by producing intermittent glitches — each of which stresses the plausibility check differently.

My approach would be to use a risk-based analysis: identify what could differ between the two platforms that would affect the control's ability to mitigate the hazard. If the hazard involves a specific sensor failure mode that can only be reproduced with the actual sensor and signal conditioning circuitry, then production-representative hardware is necessary. I would also consider whether the firmware's timing behavior — interrupt latency, task scheduling, ADC sampling jitter — could vary between platforms in a way that affects the plausibility check's thresholds. If there's any doubt, I would err toward production-representative hardware, because the cost of a false pass is a potential patient safety issue.

**Possible follow-ups:**
- What specific test cases would you design to stress the plausibility check's failure detection capability?
- How would you document the rationale for choosing one platform over the other in the verification plan?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** This is one of the more challenging traceability scenarios because the risk control doesn't live in any single subsystem — it emerges from the coordinated behavior of multiple nodes. I would approach this in three layers.

First, at the system level, I would define the risk control as a system-level behavior with its own identifier, and document the sequence of actions across nodes that constitute the control. For example, if the hazard is "motor overspeed," the control might be: Node A detects the anomaly and broadcasts a shutdown command, Node B receives it and disables the motor driver, and Node C logs the event and alerts the operator. The system-level requirement would capture this end-to-end behavior.

Second, I would decompose this into per-node requirements, each traced to the system-level control. Each node's requirement would specify its role in the coordinated action — what it detects, what message it sends, what action it takes upon receiving a message, and the timing constraints. These per-node requirements would live in each subsystem's requirements document, but each would carry the system-level risk control ID as a traceability link.

Third, for verification, I would need both subsystem-level tests (each node performs its role correctly) and system-level tests (the coordinated behavior works end-to-end, including fault injection on the bus — e.g., a lost message, a corrupted message, or a node that fails to respond). The system-level test is essential because the hazard is mitigated by the coordination, not by any single node. I would also include timing analysis as part of verification, since the coordination likely has latency requirements that are critical to the control's effectiveness.

The traceability matrix would show: hazard → system-level risk control → per-node requirements → per-node verification + system-level integration verification. This makes it clear that no single node's verification is sufficient to close the loop.

**Possible follow-ups:**
- How would you handle the situation where one node's firmware is updated and the timing characteristics change, potentially affecting the coordinated control?
- What would you do if the bus communication itself is not deterministic, making worst-case latency difficult to bound?

---

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification test, but the test was written to verify a *different* requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a common gap in traceability — the link exists on paper, but the test doesn't provide meaningful evidence that the control works under the conditions that matter. My first step would be to analyze the test procedure against the risk control's failure condition to document the specific gap: what fault is injected, what conditions are stressed, and what pass/fail criteria are used. This analysis would be shared with the team so everyone understands why the existing test is insufficient.

Then I would determine what additional testing is needed. The key question is whether the existing test can be modified to include the fault condition, or whether a new test is required. In many cases, the existing test can be extended — for example, adding a fault injection step before the nominal behavior is checked. If a new test is needed, I would write it to explicitly target the failure condition: inject the fault, verify the control responds as designed, and verify the system reaches a safe state.

I would also update the traceability matrix to distinguish between "incidental coverage" and "intentional coverage." The link to the existing test would be marked as partial or supplementary, and the new test would be the primary verification. This prevents the same gap from being overlooked in future reviews. Finally, I would review other risk controls to check whether any other tests have the same issue — where the traceability link exists but the test doesn't actually stress the failure condition. This systemic check is important because the same mistake often repeats across multiple controls.

**Possible follow-ups:**
- How would you prioritize which risk controls to audit for this type of gap, given limited time?
- What documentation would you update to ensure the gap and its resolution are captured for regulatory review?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by similarity" — meaning the team is relying on test results from a previous product that used a similar component or design. The quality manager argues that similarity is not acceptable evidence for risk controls, because the previous product wasn't tested under the same conditions. The systems engineer argues that the components are identical, the design is nearly the same, and re-running the tests would waste time and money. How would you resolve this disagreement?

**Answer:** I would start by acknowledging that both sides have legitimate concerns. The systems engineer is right that re-running identical tests on an unchanged design can be wasteful, and the quality manager is right that similarity arguments can be overused and may not hold up under regulatory scrutiny. The goal is to find a principled way to decide when similarity is acceptable and when it isn't.

My approach would be to establish objective criteria for when verification by similarity is defensible. I would ask the systems engineer to document, for each similarity-based verification, a formal analysis covering: (1) the exact component or design element being relied upon, (2) the specific conditions under which the previous product was tested, (3) the conditions relevant to the current product's risk control, and (4) a comparison showing the conditions are equivalent or that differences don't affect the risk control's function. This analysis would be reviewed by the quality manager and the engineering team.

For cases where the analysis shows genuine equivalence — for example, the same component, same circuit topology, same operating conditions, and the previous test exercised the same failure condition — I would accept the similarity argument but document it as a formal "verification by analysis" rather than leaving it as an informal assumption. For cases where there are meaningful differences — different PCB layout, different surrounding components, different operating environment, or the previous test didn't stress the same failure mode — I would require new testing.

I would also consider the risk level: for high-severity hazards, I would be more conservative and require actual testing even if the similarity argument seems strong, because the cost of a false pass is too high. For lower-severity risks, similarity with documented analysis might be acceptable. The key is that the decision is based on documented evidence and risk-based reasoning, not on schedule pressure or a blanket rule.

**Possible follow-ups:**
- How would you handle a situation where the previous product's test data is incomplete or the test conditions weren't well documented?
- What would you do if the quality manager still disagrees after the similarity analysis is presented?