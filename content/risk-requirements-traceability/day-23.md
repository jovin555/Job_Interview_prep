# risk-requirements-traceability — Day 23

## Q1: How would you approach establishing traceability for a risk control measure that is implemented through a combination of hardware and firmware, where the hardware team documents the control in their design specification and the firmware team documents their portion in a software requirements document — but neither document references the other, and the risk management file treats the control as a single integrated measure?

**Answer:** The core problem here is that the risk management file treats the control as one logical measure, but the implementation is split across two engineering disciplines that maintain separate documentation. The first step would be to define a single, unambiguous identifier for the integrated risk control measure in the risk management file — something like "RCM-014: Over-temperature motor shutdown." That identifier becomes the anchor point.

Next, I would work with both teams to ensure that each document references that shared identifier. The hardware design specification should state something like "Implements portion of RCM-014: temperature sensor and comparator circuit," and the software requirements document should state "Implements portion of RCM-014: firmware response to over-temperature interrupt." This creates a bidirectional link: from the risk management file down to each discipline's document, and from each document back up to the risk control.

The critical piece is that neither document alone tells the complete story. The hardware spec shows the sensing and detection, the software spec shows the response, but only the risk management file shows the full hazard-to-control-to-verification path. So I would also create a traceability matrix that explicitly shows the integrated control as a single row, with columns for the hardware design element, the firmware requirement, and the verification activities for each portion plus the integrated system-level test. The matrix makes the integration explicit rather than relying on cross-references that might not exist.

Finally, I would review the verification strategy. The hardware portion might be verified by a bench test that injects a temperature signal at the comparator input. The firmware portion might be verified by a unit test that simulates the interrupt. But the integrated control — the actual hazard mitigation — needs a system-level test that exercises the real sensor, the real comparator, the real interrupt path, and the real firmware response together. That system-level test is what proves the control works as an integrated measure, not just as separate pieces.

**Possible follow-ups:**
- How would you handle the situation where the hardware and firmware teams use different numbering schemes for their documents, making cross-referencing difficult?
- What would you do if the system-level verification test reveals that the integrated control works, but the hardware and firmware portions each pass their own tests while failing when integrated?

---

## Q2: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading — for example, rejecting readings that change by more than a specified rate between consecutive samples — needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** This is fundamentally a question about what the verification is actually proving. The plausibility check has two aspects: the logic of the algorithm itself, and the integration of that logic with the real hardware environment. For the algorithmic logic — does the rate-of-change check correctly reject readings that exceed the threshold, does it correctly accept readings within the threshold, does it handle edge cases like the first sample after boot — a development board with the same microcontroller is generally sufficient. The logic is deterministic and doesn't depend on the specific PCB layout or the specific sensor.

However, there are integration aspects that may only be observable on production hardware. For example, the actual sensor's noise characteristics, the ADC reference voltage accuracy, the sampling timing jitter, and the electrical environment can all affect the raw readings that feed into the plausibility check. If the check's threshold is tight relative to the sensor's real-world noise floor, a development board with a different sensor or different analog front-end might not expose issues that would appear on production hardware.

My approach would be to start with a risk-based assessment. What is the hazard being mitigated? If the plausibility check is preventing a dangerous condition — say, a motor running at an unsafe speed due to a faulty speed sensor — then the consequences of a false acceptance or false rejection are significant. In that case, I would want at least a subset of verification on production-representative hardware, particularly to characterize the sensor noise and confirm the threshold provides adequate margin.

I would also consider what the regulatory or quality standard requires. In medical device development, the verification should be performed on production-equivalent units unless there's a documented rationale for why a development board is representative. The rationale would need to address the specific differences — sensor model, analog front-end, power supply decoupling, grounding — and explain why those differences don't affect the plausibility check's behavior.

A practical middle ground is to do algorithmic testing on the development board for coverage of the logic branches, then do a focused integration test on production hardware that exercises the check with real sensor signals, including edge cases like a sensor that is drifting out of specification or a sensor that fails intermittently.

**Possible follow-ups:**
- What specific characteristics of the production hardware would you document in the rationale for why a development board is or isn't sufficient?
- How would you handle the situation where the plausibility check passes on the development board but fails intermittently on production hardware?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** Distributed architectures create a special challenge because the hazard mitigation is emergent — it only exists when multiple nodes behave correctly and in coordination. The traceability scheme has to capture both the individual node contributions and the coordinated behavior.

I would start by decomposing the hazard and its mitigation into layers. At the top is the system-level hazard, say "motor overspeed due to loss of communication between the control node and the motor node." The risk control measure might be "motor node shall enter safe state (motor off) if no valid command received within 100ms." This control has two parts: the control node must send periodic commands, and the motor node must monitor for command timeout and respond. Each part maps to a different microcontroller and different firmware.

For the traceability scheme, I would create a hierarchy. At the system level, the risk control measure links to the hazard. Below that, the control decomposes into per-node responsibilities — "control node shall transmit command at 10Hz minimum" and "motor node shall disable motor output if no valid command within 100ms." Each of these maps to a requirement in the respective node's firmware requirements document. Then each node's requirement maps to its verification activity — a unit test or integration test on that node.

But the critical piece is the coordination test. The individual node tests prove each node does its part, but they don't prove the coordinated behavior works. I would add a system-level verification activity that exercises the full chain: control node stops transmitting, motor node detects the timeout, motor output is disabled. This test is traced to the system-level risk control measure, not just to the individual node requirements.

For the shared bus, I would also consider whether the bus itself introduces failure modes that affect the control. For example, if the bus is congested and the command message is delayed beyond the 100ms timeout, the motor node would falsely enter safe state. That's a different hazard — nuisance shutdown — and might need its own risk analysis. The traceability scheme should capture the bus as an element in the architecture, with its own interface requirements and verification.

The key principle is that the traceability matrix must show the complete path: hazard → integrated risk control → decomposed node responsibilities → individual node requirements → individual node verification, plus a separate link from the integrated control to the system-level coordination test. If the matrix only shows the individual node links, it looks complete but misses the emergent behavior that actually mitigates the hazard.

**Possible follow-ups:**
- How would you handle the situation where the coordination test passes, but one of the individual node tests fails — does that invalidate the risk control verification?
- How would you document the bus communication protocol requirements in a way that supports traceability to the risk control?

---

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification test, but the test was written to verify a *different* requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a common and dangerous gap because the traceability matrix looks complete — there's a link from the risk control to a test, and the test passes — but the test provides no real evidence that the control works. The first step is to recognize that a passing test under nominal conditions is not verification of a risk control; it's just a functional test that happens to exercise the system in a state where the control isn't needed.

My approach would be to examine the test procedure in detail and compare it against the failure condition identified in the risk analysis. The risk analysis should specify the fault scenario — what condition triggers the control, what the control is supposed to do, and what the safe state looks like. The test needs to create that fault condition and observe the control's response. If the test doesn't do that, it's not verifying the control.

I would then work with the verification engineer to either modify the existing test or create a new test that specifically stresses the failure condition. For example, if the risk control is an overcurrent protection circuit, the test needs to actually drive an overcurrent condition and verify the output is disabled. If the risk control is a firmware timeout, the test needs to simulate the missing input and verify the timeout behavior.

There's also a documentation aspect. The traceability matrix should distinguish between a test that *incidentally* exercises a control under nominal conditions and a test that *specifically* verifies the control under fault conditions. I would annotate the traceability link to indicate the type of verification — "fault injection test" versus "nominal functional test" — so that reviewers can immediately see whether the verification is adequate.

If the test was already executed and passed, I would flag it as a gap in the verification record. The test result is valid for the requirement it was originally written to verify, but it cannot be claimed as evidence for the risk control. The risk control remains unverified until a proper fault-condition test is executed. This might delay the verification campaign, but it's the only way to have confidence that the control actually works when needed.

**Possible follow-ups:**
- How would you communicate this gap to the project manager who is under schedule pressure and sees a "passing" test in the traceability matrix?
- What criteria would you use to determine whether a test "adequately stresses" the failure condition versus just nominally exercising the system?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a comprehensive traceability matrix linking every requirement to a risk control measure and a verification test. However, during a design review, the test lead points out that several verification tests are testing the wrong thing — for example, a test labeled "verifies overcurrent protection" is actually testing nominal current draw. The systems engineer insists the traceability matrix is correct because the requirement numbers match. How would you resolve this disagreement?

**Answer:** The systems engineer is technically correct that the requirement numbers match, but the test lead is raising a substantive quality issue that the matrix can't capture. The matrix is a tool for tracking relationships, not a substitute for technical judgment about whether those relationships are meaningful. I would acknowledge both perspectives and then focus the discussion on the substance of the issue.

First, I would ask the test lead to walk through the specific test procedure and explain what it actually exercises versus what the requirement demands. This isn't about challenging the systems engineer — it's about getting the technical facts on the table. If the test is indeed only measuring nominal current draw, then it cannot provide evidence that the overcurrent protection works. The requirement number matching is necessary but not sufficient.

Then I would ask the systems engineer to explain what they believe the test verifies. It's possible they reviewed the test and believed it was adequate, or it's possible they never looked beyond the requirement number match. Either way, the discussion should be about the technical adequacy of the test, not about who is right.

If the test is genuinely inadequate, the resolution is to modify the test to actually stress the fault condition, or to add a new test that does. This might require additional test time and resources, so I would work with the project manager to assess the schedule impact. But the alternative — accepting a test that doesn't verify the control — is not acceptable for a risk control measure, especially in a medical device context where the consequences of a failure could be serious.

I would also use this as an opportunity to improve the review process. The traceability matrix should include a column for the verification method and a brief description of the test approach, so that reviewers can quickly assess whether the test is appropriate. I might also suggest that the test lead and systems engineer jointly review the test procedures against the risk analysis during the design review, rather than relying solely on the matrix.

The key is to keep the discussion focused on the technical question — does this test provide evidence that the risk control works? — and not let it become a conflict between the systems engineer's ownership of the matrix and the test lead's ownership of the tests. Both are needed: the matrix provides the structure, and the test provides the evidence.

**Possible follow-ups:**
- How would you handle the situation where the test lead is correct, but fixing the test would delay the verification campaign by several weeks?
- What changes would you make to the design review process to catch this type of issue earlier in the development cycle?