# risk-requirements-traceability — Day 25

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a combination of hardware and firmware, where the hardware team documents the control in their design specification and the firmware team documents their portion in a software requirements document — but neither document references the other, and the risk management file treats the control as a single integrated measure?

**Answer:** The core issue here is that the risk management file treats the control as one integrated measure, but the engineering artifacts treat it as two separate pieces. I would start by creating a single "integration point" in the traceability scheme — a shared identifier or reference that both the hardware and firmware documents must cite. This could be a risk control ID from the risk management file (e.g., RC-014) that both teams are required to reference in their respective documents.

The key is to establish the link at the right level of abstraction. I would define the integrated control as a system-level requirement in the SRS — something like "The system shall detect over-temperature and disable the motor within X ms" — and then trace that system requirement down to both the hardware design element (the sensor and comparator circuit) and the firmware requirement (the response logic). The hardware design spec and the software requirements document would each reference the same system-level requirement ID, creating an implicit link between them.

I would also add explicit cross-references: the hardware document should note "this circuit provides the detection function for system requirement SR-042 / risk control RC-014, which is completed by firmware requirement FW-118," and vice versa. This creates a bidirectional link that survives even if the two teams never directly coordinate on document structure.

Finally, I would verify the traceability chain end-to-end: hazard → risk control → system requirement → hardware design element + firmware requirement → verification activities. The verification plan should include both a hardware-level test (does the comparator trip at the right threshold?) and a firmware-level test (does the firmware respond correctly to the interrupt?), plus a system-level test that exercises the complete chain. Each verification activity should trace back to the same risk control ID.

**Possible follow-ups:** How would you handle the situation where the hardware and firmware teams use different numbering schemes and refuse to adopt a common one? What if the risk management file is updated to change the control's behavior — how would you propagate that change through both documents?

---

## Q2: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading — for example, rejecting readings that change by more than a specified rate between consecutive samples — needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** The decision hinges on what the verification is actually trying to demonstrate. For a firmware-based plausibility check, there are two distinct aspects: the logic of the check itself (does the algorithm correctly identify implausible readings?) and the integration of that check with the real hardware (does the sensor interface, ADC, and timing behave as expected on production hardware?).

For the logic itself, a development board with the same microcontroller is often sufficient — you can inject test vectors, simulate sensor readings, and verify the algorithm's decision boundaries. This is essentially a software unit test, and the development board provides the correct instruction set, timing, and register behavior.

However, for the integration aspects, production-representative hardware becomes important. The plausibility check depends on the actual sensor's output characteristics, the ADC's resolution and noise floor, and the real-world sampling timing. A development board may have a different sensor, different analog front-end, or different clock configuration. The risk is that the plausibility check's thresholds were tuned based on expected sensor behavior, and if the real hardware has different noise characteristics or timing jitter, the check might reject valid readings or accept implausible ones.

My approach would be to split the verification into two tiers: (1) algorithm-level testing on the development board, covering the decision logic, boundary conditions, and edge cases; and (2) integration testing on production-representative hardware, covering the actual sensor-to-firmware path with realistic signal conditions. The integration test doesn't need to re-verify every algorithm branch — it needs to demonstrate that the check works correctly with the real hardware's characteristics.

If the risk analysis identifies this control as the primary mitigation for a high-severity hazard, I would lean toward requiring production-hardware verification. If it's a secondary control or the hazard severity is lower, development-board testing of the logic plus a nominal-condition check on production hardware might be defensible — but I would document the rationale for that decision in the verification plan.

**Possible follow-ups:** What specific aspects of the production hardware could cause the plausibility check to behave differently than on the development board? How would you decide whether the verification needs to include fault injection (e.g., physically forcing a sensor to produce an implausible reading)?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** This is one of the more challenging traceability scenarios because the risk control doesn't live in any single subsystem — it emerges from the coordinated behavior of multiple nodes. The first step is to define the control at the system level in the SRS, not at the individual node level. The system requirement should state the complete behavior: "Upon detection of fault condition X on Node A, Node A shall broadcast a shutdown command, and Nodes B and C shall enter safe state within Y ms."

From there, I would decompose the system-level requirement into node-specific requirements. Each node's firmware requirements document would contain its portion of the behavior — Node A's requirement to detect and broadcast, Nodes B and C's requirements to receive and respond. Each node-level requirement would trace up to the same system-level requirement and the same risk control ID.

The tricky part is the communication bus. The risk control depends on the bus functioning correctly — messages must be transmitted, received, and acted upon within the specified timing. This means the bus protocol itself becomes part of the risk control chain. I would add a requirement for the communication protocol's behavior under fault conditions (e.g., message timeout handling, retry logic, bus error detection) and trace that to the same risk control.

For verification, I would need both node-level tests and a system-level integration test. The node-level tests verify each node's individual behavior — Node A detects the fault and sends the command; Nodes B and C respond to the command. The system-level test verifies the complete chain: inject a fault at Node A, observe that all nodes enter safe state within the specified timing. The system-level test is essential because it exercises the bus timing, message ordering, and coordinated response that can't be verified at the node level.

I would also consider failure modes of the bus itself. What if the shutdown command is corrupted or lost? The risk analysis should address this — perhaps with a redundant command, a heartbeat mechanism, or a fail-safe timeout on the receiving nodes. Each of these additional controls would need its own traceability path.

**Possible follow-ups:** How would you handle the situation where the bus communication timing is critical to the risk control, but the bus is also used for non-safety-critical traffic? How would you verify that the coordinated response timing is met under worst-case bus loading?

---

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification test, but the test was written to verify a *different* requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a common gap in traceability — the link exists on paper, but the test doesn't actually provide meaningful evidence that the control works. The first step is to recognize that a traceability link is only as good as the verification activity it points to. A test that exercises the control under nominal conditions is not adequate evidence for a control whose purpose is to mitigate a fault condition.

I would start by reviewing the test procedure against the risk control's failure condition. The question to ask is: "If this control were completely broken, would this test detect it?" If the answer is no — because the test never creates the fault condition the control is meant to detect — then the test is not providing the required evidence.

The fix is to modify the test or add a new one that actually stresses the failure condition. For example, if the control is an over-temperature shutdown, the test needs to create an over-temperature condition (or simulate it at the sensor input) and verify the shutdown occurs. This might require fault injection — physically forcing the fault, or using test hooks to inject a simulated fault signal.

There's also a documentation aspect. The traceability matrix should distinguish between tests that provide primary evidence for a control and tests that merely exercise the control incidentally. I would update the matrix to clearly identify which test is the primary verification for each risk control, and ensure that test actually stresses the failure condition.

If modifying the test isn't feasible — for example, if the fault condition is dangerous to create or requires specialized equipment — I would look for alternative verification methods. Analysis (e.g., worst-case timing analysis, fault tree analysis) might be acceptable for some controls, but the rationale needs to be documented and the analysis needs to be rigorous enough to provide equivalent confidence.

Finally, I would review other traceability links in the matrix with the same critical eye. If this one slipped through, others might have the same issue. A systematic review of all risk control verification activities — asking "would this test detect a broken control?" — is a worthwhile investment.

**Possible follow-ups:** How would you handle the situation where the test engineer argues that adding fault injection to the test is too complex and the nominal-condition test is "good enough"? What if the fault condition is physically dangerous to create in a test environment?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by analysis" — for example, a worst-case timing analysis or a thermal derating calculation — rather than physical tests. The quality manager argues that analysis is not objective evidence and demands physical testing for all risk controls. The systems engineer argues that some controls, like timing margins or thermal derating, can only be practically verified by analysis, and that physical testing would be impractical or impossible. How would you resolve this disagreement?

**Answer:** I would start by acknowledging that both sides have valid points. The quality manager is right that physical testing provides the strongest evidence, and there's a risk that "verification by analysis" becomes a rubber stamp if the analysis isn't rigorous. The systems engineer is also right that some controls — like thermal derating or worst-case timing — are genuinely difficult or impossible to verify by physical test alone. You can't easily create a worst-case timing scenario on a test bench, and you can't physically stress a component to its derating limit without risking damage.

The resolution is to evaluate each verification-by-analysis case on its merits, rather than making a blanket decision. I would propose a structured review of each analysis-based verification with three questions:

First, what is the nature of the control? Some controls are inherently analytical — a derating calculation is a design decision, not a functional behavior. For these, analysis is the appropriate verification method, and the question is whether the analysis is rigorous enough. I would ask to see the analysis methodology, the assumptions, the input data, and the margin calculations. If the analysis is well-documented and uses conservative assumptions, it can be valid evidence.

Second, is there a way to partially verify the control by test? For example, a worst-case timing analysis might be verified by measuring actual timing on the hardware under nominal conditions, then using analysis to extend to worst-case. A thermal derating calculation might be supported by a thermal test at the system level that measures actual temperatures, even if it doesn't stress components to their absolute limits. This hybrid approach — test where feasible, analysis to extend — often provides the best evidence.

Third, what is the risk if the analysis is wrong? For a high-severity hazard where the control is the primary mitigation, I would lean toward requiring some form of physical evidence, even if it's indirect. For lower-severity hazards, a well-documented analysis might be sufficient.

I would also propose a middle ground: the quality manager might accept analysis-based verification if it's accompanied by a documented rationale for why physical testing is impractical, and if the analysis is independently reviewed. This addresses the quality manager's concern about rigor while acknowledging the systems engineer's practical constraints.

The key is to avoid an either/or debate and instead create a framework for evaluating each case. I would bring both parties together, walk through the specific controls in question, and apply the framework to reach a consensus on each one.

**Possible follow-ups:** How would you handle the situation where the quality manager agrees to accept analysis but only if it's "independently verified" — and the systems engineer argues that the analysis is already internally reviewed and independent verification would add weeks to the schedule? What criteria would you use to decide whether a particular analysis is rigorous enough to serve as verification evidence?