# risk-requirements-traceability — Day 28

## Q1: How would you approach handling a situation where a risk control measure is traced to a verification test, but the test was written to verify a *different* requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a common failure mode in traceability — the link exists on paper, but the verification intent doesn't match the risk control's purpose. My first step would be to confirm the discrepancy by reviewing the test procedure against the risk control's failure condition. The key question is: does the test actually inject or simulate the fault condition that the control is designed to mitigate, or does it just exercise the system under normal operation? If the test only runs nominal conditions, then the traceability link is misleading — it gives the appearance of coverage without providing objective evidence that the control works when it needs to.

I would then work with the verification engineer to either modify the existing test to include the fault injection, or create a separate test specifically for the risk control. The modified or new test needs to demonstrate two things: first, that the control activates when the fault condition occurs, and second, that the system reaches or maintains a safe state as a result. I would also update the traceability matrix to reflect the corrected link, and I would review other links in the matrix with the same scrutiny — if one link was misleading, others might be too. Finally, I would document the discrepancy and the resolution in the design history file, since this is exactly the kind of issue that a regulatory auditor would want to see handled systematically.

**Possible follow-ups:**
- How would you determine whether the existing test can be modified or whether a new test is required?
- What would you do if the verification engineer argues that the nominal-condition test is sufficient because the risk control is "designed to work" and the fault condition is covered by design margin?

---

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a combination of hardware and firmware, where the hardware team documents the control in their design specification and the firmware team documents their portion in a software requirements document — but neither document references the other, and the risk management file treats the control as a single integrated measure?

**Answer:** The core problem here is that the risk management file treats the control as one integrated measure, but the implementation is split across two engineering disciplines that maintain separate documentation. The traceability will be incomplete unless there's a way to connect the hardware and firmware portions back to the single risk control entry.

My approach would be to introduce a linking mechanism at the system level. I would create a traceability artifact — perhaps a table or a section in the risk management file — that identifies the integrated risk control and then explicitly maps it to the specific hardware design element and the specific firmware requirement. The hardware design specification and the software requirements document would each need a reference back to the risk control identifier, even if they use different numbering schemes. This could be as simple as adding a "Related Risk Control" field to each document, or as formal as creating an interface control document that captures the interaction between the hardware and firmware portions.

The critical part is defining the boundary between the two portions. For example, if a hardware comparator detects an over-voltage condition and asserts an interrupt, and firmware responds by disabling a power output, then the hardware spec should reference the risk control ID for the detection and interrupt assertion, and the software requirements should reference the same ID for the response behavior. The verification activities would then also need to be linked — ideally with a system-level test that exercises the full chain from sensor through comparator through firmware to the safe state, plus potentially separate hardware and firmware tests for their respective portions.

I would also flag this as a process improvement opportunity. The fact that the two teams didn't cross-reference each other's documents suggests a gap in the document control process. I would propose adding a checklist item or a design review gate that specifically asks whether risk controls spanning multiple disciplines have cross-references in all affected documents.

**Possible follow-ups:**
- How would you handle the situation if the hardware and firmware teams use different risk control identifiers or don't have a common numbering scheme?
- What verification strategy would you propose for the integrated control — separate tests, a system-level test, or both?

---

## Q3: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading — for example, rejecting readings that change by more than a specified rate between consecutive samples — needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** The key question is whether the risk control's behavior depends on characteristics that differ between the development board and the production hardware. For a firmware-based plausibility check, the relevant characteristics would include the microcontroller's clock speed, interrupt latency, ADC sampling behavior, and the timing of the firmware's execution. If the development board uses the same microcontroller at the same clock speed, and the firmware is identical, then the plausibility check's logic and timing behavior should be representative.

However, there are factors that might not be captured on a development board. The sensor itself — its analog output characteristics, noise profile, and response time — could differ between the development board and the production hardware. The plausibility check operates on sensor readings, so if the sensor interface or the analog front-end differs, the test might not be representative. Also, the production hardware might have different power supply characteristics, grounding, or electromagnetic interference that could affect sensor readings and thus the plausibility check's behavior.

My approach would be to analyze what the risk control actually depends on. If the plausibility check is purely computational — it takes a digital value and applies a rate-of-change limit — then testing on a development board with the same microcontroller and the same firmware should be sufficient, provided the test injects realistic sensor data. But if the check's behavior could be affected by the analog front-end, noise, or timing variations in the production system, then verification on production-representative hardware would be necessary.

I would also consider the risk analysis. If the hazard is severe and the plausibility check is a primary risk control, I would lean toward testing on production hardware, or at least on a test setup that includes the production sensor and analog front-end. The cost of a false confidence in the control's effectiveness is too high in a medical device context. If the check is a secondary control or the hazard is less severe, development board testing might be acceptable, but I would document the rationale for that decision.

**Possible follow-ups:**
- What specific aspects of the production hardware would you examine to determine whether development-board testing is representative?
- How would you document the rationale for your choice of test platform in the verification plan?

---

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** This is one of the more challenging traceability scenarios because the risk control doesn't live in a single subsystem — it's an emergent property of the system's distributed behavior. The traceability scheme needs to capture not just the individual contributions of each node, but also the coordination between them.

My approach would start at the system level. The hazard and its risk control would be documented in the risk management file as a single integrated control. From there, I would decompose the control into the specific responsibilities of each node — for example, Node A detects a fault condition and broadcasts a shutdown command, Node B receives the command and disables its motor output, and Node C logs the event and alerts the user. Each of these responsibilities would need to be traced to the appropriate subsystem requirement: Node A's detection logic in its firmware requirements, Node B's response in its firmware requirements, and so on.

The coordination aspect is the tricky part. The traceability scheme needs to capture the interaction — the message format, the timing requirements, the acknowledgment mechanism, and the failure behavior if a node doesn't respond. This is where an interface control document becomes essential. The ICD would define the protocol for the shutdown command, including message format, timing, and expected behavior. The traceability matrix would then link the risk control to the ICD, and the ICD to the individual node requirements.

For verification, I would expect to see both node-level tests — each node's portion of the control verified in isolation — and a system-level test that exercises the full chain: fault injection at Node A, message transmission, response at Node B, and confirmation that the safe state is achieved. The system-level test is critical because it verifies the coordination, which is the part most likely to fail. The traceability matrix would show the risk control linked to both the node-level and system-level verification activities.

I would also consider failure modes in the coordination itself. What happens if the bus is congested and the shutdown command is delayed? What if a node is in a fault state and can't process the command? These would be additional risk considerations, and the traceability scheme would need to account for them — either as additional risk controls or as part of the verification conditions for the primary control.

**Possible follow-ups:**
- How would you handle the situation where different nodes are developed by different teams with separate requirements documents?
- What system-level test approach would you use to verify the coordinated response across all nodes?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by inspection" — meaning someone looked at the design and declared it acceptable. The quality manager argues that inspection is not objective evidence and demands that all risk controls be verified by test. The systems engineer argues that some controls, like component derating or PCB layout rules, can only be verified by inspection, and that requiring tests would be impractical and unnecessary. How would you resolve this disagreement?

**Answer:** I would start by acknowledging that both parties have valid points. The quality manager is right that inspection can be subjective and doesn't provide the same level of objective evidence as a test with measurable pass/fail criteria. But the systems engineer is also right that some risk controls — like component derating or PCB creepage distances — are inherently design-rule-based and can't be meaningfully verified by a functional test. You can't "test" a creepage distance; you can only measure it or inspect the layout against the standard.

My approach would be to distinguish between different types of verification evidence and establish criteria for when each type is acceptable. For controls that are design-rule-based, inspection can be valid evidence if it's structured properly — meaning there's a defined checklist, the inspection criteria are objective and measurable, the inspector has the appropriate expertise, and the results are documented. For example, verifying a creepage distance isn't just "someone looked at it" — it's measuring the distance on the PCB layout and comparing it against the IEC 60601 requirement. That's a measurable, objective activity, even if it's called "inspection."

For controls that are functional — where the control is supposed to do something in response to a condition — I would agree with the quality manager that testing is required. A functional risk control that's only verified by inspection doesn't provide evidence that the control actually works. The inspection might confirm the circuit exists, but it doesn't confirm the circuit behaves correctly under fault conditions.

I would propose a middle path: categorize the risk controls into those that can be adequately verified by structured inspection (with defined criteria and documentation) and those that require functional testing. For the inspection-based verifications, I would work with the systems engineer to formalize the inspection criteria — turning "someone looked at it" into a documented checklist with specific measurements or comparisons. For the functional controls, I would work with the verification team to develop appropriate tests. I would also document the rationale for each verification method in the traceability matrix, so the decision is transparent and defensible.

**Possible follow-ups:**
- How would you determine which risk controls are suitable for inspection-based verification versus functional testing?
- What would you do if the quality manager still insists that all risk controls must have a functional test, even after you've formalized the inspection criteria?