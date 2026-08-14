# risk-requirements-traceability — Day 24

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a combination of hardware and firmware, where the hardware team documents the control in their design specification and the firmware team documents their portion in a software requirements document — but neither document references the other, and the risk management file treats the control as a single integrated measure?

**Answer:** The core issue here is that the risk management file treats the control as one integrated measure, but the design documentation has fragmented it across two disciplines with no cross-references. I would start by creating a single "risk control implementation" record in the risk management file that explicitly lists every design element contributing to the control — the hardware sensor, the firmware decision logic, and the hardware actuator — with pointers to the specific sections of the hardware design spec and the software requirements document. This record becomes the bridge between the two documents.

Next, I would add bidirectional cross-references: in the hardware design specification, a note stating "this comparator circuit implements risk control RC-042, see firmware requirement SW-118 for the response logic"; and in the software requirements document, a corresponding note referencing the hardware element. This ensures that anyone reviewing either document can find the complete implementation.

For verification, I would establish a two-tier approach. Tier one verifies each element at its own level — the comparator trips at the specified threshold, and the firmware responds within the specified time. Tier two verifies the integrated behavior end-to-end, injecting a fault at the sensor and confirming the complete chain works. Both tiers trace back to the same risk control record. The key principle is that the risk management file owns the integrated view, while the design documents own the implementation details — and the cross-references make the connections explicit rather than implicit.

**Possible follow-ups:**
- How would you handle the situation where the hardware and firmware teams use different numbering schemes for their documents?
- What would you do if the integrated verification test fails but both component-level tests pass?

---

## Q2: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading — for example, rejecting readings that change by more than a specified rate between consecutive samples — needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** The decision hinges on what could differ between the development board and production hardware that might affect the plausibility check's behavior. For a pure firmware algorithm, the logic itself is identical regardless of hardware. However, the plausibility check is only meaningful if the sensor data reaching it is realistic — and that depends on the analog front-end, the sensor interface, the ADC configuration, and the electrical environment.

I would ask three questions. First, does the production hardware have any differences in the sensor interface — different component values, different layout, different grounding — that could affect the signal characteristics the firmware sees? Second, are there any timing differences — different clock speeds, different interrupt priorities, different bus speeds — that could affect when samples arrive? Third, does the plausibility check interact with any hardware-specific behavior, such as ADC saturation, noise levels, or power supply transients?

If the answer to all three is no, then development board testing of the algorithm logic is sufficient for the firmware portion. But I would still require a production-hardware test that exercises the complete chain — sensor, analog front-end, ADC, and firmware — to confirm that the plausibility check behaves correctly with real-world signal characteristics. The development board test proves the logic is correct; the production hardware test proves the logic works with the actual hardware. For a medical device, I would typically require both, with the production hardware test being the formal verification evidence.

**Possible follow-ups:**
- What specific test cases would you design for the development board versus the production hardware?
- How would you document the rationale for using a development board for part of the verification?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** The challenge with distributed architectures is that the hazard mitigation is emergent — it only exists when multiple nodes act in coordination. A traceability scheme that treats each node's contribution as an independent control would miss the critical dependency between them.

I would structure the traceability in three layers. At the top, the hazard links to a single integrated risk control measure that describes the coordinated response — for example, "upon detection of over-temperature on Node A, Node A broadcasts a shutdown command, and Nodes B and C must enter safe state within 100ms." This is the system-level control.

At the middle layer, I would decompose this into per-node responsibilities, each documented as a requirement in that node's firmware requirements document. Node A has the requirement to detect and broadcast; Nodes B and C have requirements to receive and respond. Each of these traces up to the integrated control.

At the bottom layer, I would add interface-level requirements — the bus protocol, message format, timing requirements, and error handling — that ensure the coordination actually works. These interface requirements are often the weakest link because they live between the nodes rather than within any single one.

For verification, I would require both per-node testing (each node correctly performs its individual role) and system-level integration testing (the coordinated response actually happens within the specified time when a fault is injected). The traceability matrix must show the complete path: hazard → integrated control → per-node requirements → per-node verification → system integration verification. The critical addition is the timing requirement — the coordination only works if the response happens within the specified window, so the verification must measure timing, not just functional correctness.

**Possible follow-ups:**
- How would you handle the case where one node's firmware is updated and the timing changes?
- What if the bus itself is the failure mode — how would you trace a control that depends on the communication channel being available?

---

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification test, but the test was written to verify a *different* requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a common and dangerous gap — the traceability matrix looks complete because there's a link, but the link is meaningless because the test doesn't exercise the failure condition. The first step is to recognize that a traceability link is only valid if the verification activity actually stresses the condition the control is designed to mitigate. A test that passes under nominal conditions provides no evidence that the control works when it's needed.

I would start by reviewing the test procedure against the risk control's failure condition. The question is: does the test inject the fault, simulate the failure, or otherwise create the conditions the control is designed to detect? If not, the traceability link should be flagged as invalid, and the test should be marked as "does not verify this control."

Then I would work with the verification engineer to design a proper test. This means understanding the failure condition from the risk analysis — what exactly is the hazard scenario, what sensor reading or system state triggers the control, and what is the expected response? The test needs to create those conditions and confirm the control responds correctly.

I would also update the traceability matrix to distinguish between "incidental exercise" and "deliberate verification." A test that happens to run the code path under nominal conditions is useful for regression but is not verification of the risk control. The matrix should clearly show which tests are the primary verification evidence for each control, and which are supplementary.

Finally, I would review other traceability links with the same scrutiny — if one link was invalid, others might be too. This is a systematic gap, not an isolated incident. The review should check every risk control to confirm its verification test actually stresses the failure condition.

**Possible follow-ups:**
- How would you handle the situation where the proper test is significantly more complex or expensive to run?
- What documentation would you create to record that the original test was inadequate?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by analysis" — for example, a worst-case timing analysis or a thermal derating calculation — rather than physical tests. The quality manager argues that analysis is not objective evidence and demands physical testing for all risk controls. The systems engineer argues that some controls, like timing margins or thermal derating, can only be practically verified by analysis, and that physical testing would be impractical or impossible. How would you resolve this disagreement?

**Answer:** I would start by acknowledging that both sides have legitimate points. The quality manager is right that physical testing provides the strongest evidence, but the systems engineer is also right that some controls — like worst-case timing margins or thermal derating — are genuinely difficult or impossible to verify by physical test alone. The question isn't whether analysis is acceptable, but whether the analysis is rigorous enough to serve as objective evidence.

I would propose a framework for evaluating each "verification by analysis" activity. First, is the analysis based on validated models? For example, a thermal simulation is only credible if the model has been correlated against physical measurements. Second, are the assumptions and inputs documented and conservative? A worst-case timing analysis is only meaningful if the input parameters represent genuine worst-case conditions. Third, is there any physical evidence that partially validates the analysis — even a single temperature measurement, a spot timing check, or a bench test at one operating point?

Based on this framework, I would categorize the analysis-based verifications into three groups. The first group is analysis that is well-supported by validated models and conservative assumptions — this can serve as the primary verification evidence, possibly supplemented by a limited physical spot-check. The second group is analysis that has some support but significant uncertainty — this needs additional physical testing to close the gap. The third group is analysis that is essentially unvalidated — this cannot serve as verification evidence, and physical testing is required.

I would then work with both the quality manager and the systems engineer to agree on the categorization and the required evidence for each control. The key is to move from a binary argument — "analysis is acceptable" versus "analysis is not acceptable" — to a risk-based discussion about what level of evidence is appropriate for each specific control. For a medical device, the criticality of the hazard should drive the evidence requirements. A timing analysis for a control that prevents a life-threatening condition warrants more scrutiny than one for a nuisance alarm.

**Possible follow-ups:**
- How would you handle a situation where the analysis is well-done but the physical spot-check fails?
- What criteria would you use to determine when analysis alone is sufficient versus when physical testing is mandatory?