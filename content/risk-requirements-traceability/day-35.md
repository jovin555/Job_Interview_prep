# risk-requirements-traceability — Day 35

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a combination of hardware and firmware, where the hardware team documents the control in their design specification and the firmware team documents their portion in a software requirements document — but neither document references the other, and the risk management file treats the control as a single integrated measure?

**Answer:** The core problem here is that the risk management file treats the control as one logical measure, but the implementation artifacts are split across two engineering disciplines with separate documentation trees. I would start by creating a single "integration point" in the risk management file — a row or entry that explicitly lists both the hardware element and the firmware element as constituent parts of one control. That entry would reference both the hardware design specification and the software requirements document, even if the two documents use different numbering schemes.

The key is to establish a mapping table that translates between the two numbering systems. For example, if the hardware spec calls the comparator circuit "HW-ANLG-014" and the software requirements document calls the response logic "SW-REQ-227," the risk management file should have a column that lists both identifiers side by side. This mapping doesn't need to be elaborate — a simple cross-reference table works — but it must be maintained as the documents evolve.

I would also flag this as a process gap. The fact that neither document references the other suggests the teams aren't coordinating on shared controls. I'd propose a review checkpoint where any risk control that spans multiple subsystems gets a cross-reference check before the documents are baselined. This is less about the specific traceability artifact and more about preventing the same gap from recurring.

**Possible follow-ups:**
- How would you handle the situation where the hardware and firmware teams use different revision control systems, making it difficult to know which versions of each document correspond to each other?
- What level of detail would you expect in the risk management file's description of the control — enough to understand the full chain, or just enough to point to the right documents?

---

## Q2: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading — for example, rejecting readings that change by more than a specified rate between consecutive samples — needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** The decision hinges on what aspects of the control's behavior could differ between the development board and production hardware. For a plausibility check, the critical question is whether the timing and sampling behavior are affected by the specific hardware implementation. If the check operates on data that arrives over a bus with timing characteristics that depend on the final PCB layout, trace lengths, or interrupt load from other peripherals, then development-board testing may not be representative.

I would break the verification into layers. The algorithmic logic — the rate-of-change calculation itself, the threshold comparison, the action taken when the check fails — can be verified on a development board or even in a host-based unit test, because that logic is deterministic and independent of the physical hardware. But the integration aspects — actual sensor sampling rates, interrupt latency, bus timing, and interaction with other firmware tasks — need to be verified on production-representative hardware.

The risk analysis should guide this decision. If the hazard is mitigated by the plausibility check catching a sensor that has failed in a specific way, then the verification needs to demonstrate that the check actually catches that failure mode in the real system. A development board with the same microcontroller but different sensor wiring, different power supply characteristics, or different firmware load may not reproduce the same failure signature.

I would also consider whether the plausibility check's parameters (the rate threshold, the sampling window) are hardware-dependent. If those parameters were chosen based on the physical characteristics of the sensor and its interface — which they usually are — then the verification should confirm the check works with the actual sensor on the actual hardware.

**Possible follow-ups:**
- What if the development board uses the same microcontroller but a different sensor — would that change your assessment?
- How would you document the rationale for choosing development-board testing versus production-hardware testing in the verification plan?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** This is one of the more challenging traceability scenarios because the control doesn't live in any single subsystem — it emerges from the coordinated behavior of multiple nodes. The first step is to define the control at the system level in the risk management file, describing the complete chain: what each node contributes, what messages are exchanged, and what the overall behavior is when the control activates.

From there, I would decompose the system-level control into per-node responsibilities. Each node's contribution becomes a requirement in that node's own requirements document, with a traceability link back to the system-level risk control. The key is to make the decomposition explicit — the risk management file should show how the system-level control maps to node-specific requirements, and each node's requirements should reference the shared control identifier.

The communication protocol becomes a critical piece of the traceability chain. If the control depends on Node A detecting a condition and sending a message to Node B, which then takes action, the message format, timing, and semantics need to be captured in the interface control document. That ICD entry should also trace back to the same risk control identifier.

For verification, I would expect both node-level tests (each node responds correctly to the relevant inputs) and system-level tests (the coordinated behavior works end-to-end over the actual bus). The traceability matrix should show both levels — the node-level tests verify the individual contributions, and the system-level test verifies the integrated control.

One practical concern is maintaining consistency across multiple documents. I would establish a shared risk control identifier scheme that all teams use — for example, "RC-014" appears in the risk management file, in each node's requirements, in the ICD, and in the test plans. This makes it possible to trace the control through the entire development lifecycle even though the artifacts are distributed.

**Possible follow-ups:**
- How would you handle a situation where one node's firmware is developed by a third-party vendor who uses their own requirements format?
- What if the bus communication itself introduces a failure mode — for example, a message is lost or corrupted — and that failure mode is part of the hazard scenario?

---

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification test, but the test was written to verify a *different* requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a common gap in traceability — the link exists on paper, but the test doesn't actually demonstrate that the control works when it's needed. The first step is to recognize that a traceability link is only meaningful if the verification activity actually exercises the control's failure condition. A test that passes under nominal conditions tells you nothing about whether the control will work when the hazard scenario occurs.

I would start by reviewing the risk analysis to identify the specific failure conditions the control is meant to mitigate. Then I would compare those conditions against what the test actually does. If the test doesn't inject the fault, simulate the failure, or otherwise stress the control's activation conditions, then the traceability link is invalid — the test may verify something else, but it doesn't verify the risk control.

The fix is to either modify the existing test to include the fault injection, or create a separate test specifically for the risk control. I would document the discrepancy in the verification gap analysis, explaining why the existing test is insufficient and what new test activity is needed. This documentation is important for the regulatory file — it shows that the gap was identified and addressed, rather than discovered later during an audit.

I would also look at why this happened. If the test was written to verify a different requirement and the risk control was added as an afterthought, that suggests the traceability was built after the fact rather than during test planning. A better process would be to identify risk controls early and ensure each one has a dedicated verification activity designed around its failure conditions.

**Possible follow-ups:**
- How would you prioritize which risk controls need new tests versus which can be adequately covered by modifying existing tests?
- What would you do if the schedule doesn't allow time to create new tests before the verification deadline?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by similarity" — meaning the team is relying on test results from a previous product that used a similar component or design. The quality manager argues that similarity is not acceptable evidence for risk controls, because the previous product wasn't tested under the same conditions. The systems engineer argues that the components are identical, the design is nearly the same, and re-running the tests would waste time and money. How would you resolve this disagreement?

**Answer:** I would start by acknowledging that both sides have legitimate points. The systems engineer is right that re-running tests for identical components can be wasteful, and the quality manager is right that similarity arguments are often overused and can hide real differences. The resolution isn't to pick a side but to establish clear criteria for when similarity is acceptable.

I would propose a structured assessment for each "verification by similarity" entry. The assessment would compare the previous product and the current product across several dimensions: the specific component or design element in question, the conditions under which the previous test was run, the conditions relevant to the current product's risk analysis, and any differences in surrounding circuitry, firmware, or operating environment. If the comparison shows that the relevant conditions are truly equivalent, similarity can be justified — but the justification needs to be documented, not just asserted.

For cases where the comparison reveals meaningful differences — even small ones — I would require at least a targeted test on the current product. The test doesn't need to replicate the full previous test campaign; it needs to cover the specific conditions that differ and the failure modes the risk control is meant to mitigate.

I would also involve the quality manager in defining the acceptance criteria for similarity. If they agree upfront on what constitutes a valid similarity argument, the review process becomes much smoother. The goal is to move from a binary "similarity is always acceptable" versus "similarity is never acceptable" to a nuanced, documented assessment that everyone can support.

**Possible follow-ups:**
- What specific criteria would you propose for determining when similarity is acceptable?
- How would you handle a situation where the previous test data exists but was collected under a different regulatory standard or quality system?