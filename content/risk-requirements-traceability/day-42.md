# risk-requirements-traceability — Day 42

## Q1: How would you approach handling a situation where a risk control measure is implemented in firmware, but the firmware requirements document doesn't explicitly state the safety intent — it only describes the functional behavior (e.g., "the system shall disable the motor output within 100ms of receiving a fault signal") without referencing the hazard it mitigates?

**Answer:** The core issue here is that the firmware requirement describes *what* the system does but not *why* it exists. That's a traceability gap even if the functional behavior is correct. I'd approach this in three steps.

First, I'd assess whether the safety intent is captured anywhere else — perhaps in the risk management file, a system-level requirement, or a design note. If the hazard-to-control link exists at the system level, the firmware requirement may be acceptable as a derived requirement, but it should still carry a reference back to the originating risk control so that anyone reading the firmware document understands its safety significance.

Second, I'd add a traceability attribute to the firmware requirement — either a comment field, a cross-reference in the requirement ID, or a column in the traceability matrix — that links it to the specific hazard and risk control measure. This doesn't necessarily mean rewriting the requirement; it means making the link explicit and auditable.

Third, I'd verify that the verification activity for this requirement actually stresses the failure condition, not just the nominal behavior. A test that confirms the motor disables within 100ms of a fault signal is good, but it must also confirm what happens if the fault signal never arrives, or if the firmware is in a state where it can't process the interrupt. The safety intent should drive the test design, not just the requirement text.

The key principle is that traceability isn't just about matching numbers — it's about preserving the *rationale* behind design decisions. If someone reads the firmware requirement in isolation five years later, they should be able to understand why that 100ms timing matters.

**Possible follow-ups:** How would you handle this if the firmware team is resistant to adding safety-related annotations to their requirements, arguing it's "systems engineering's job"? What if the firmware requirement is correct but the verification test only checks nominal timing, not the fault condition?

---

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a combination of a hardware analog comparator and a firmware response, where the hardware and firmware teams maintain separate requirements documents with different numbering schemes, and neither document references the other?

**Answer:** This is a common failure point in mixed-signal systems — the hazard is mitigated by the *interaction* of hardware and firmware, but each team documents only their own piece. I'd approach this by creating a "system-level integration requirement" that sits above both the hardware and firmware requirements and explicitly describes the combined behavior.

The integration requirement would state something like: "When the analog comparator detects an over-voltage condition on the power rail, the system shall disable the motor output within 50ms." This requirement lives in the system requirements specification, not in either team's document. It references both the hardware requirement (comparator threshold and output behavior) and the firmware requirement (interrupt handling and output disable logic) as derived requirements.

For the traceability scheme, I'd use a three-level structure:
- **Level 1 (system):** The integration requirement, linked to the hazard in the risk management file.
- **Level 2 (subsystem):** The hardware requirement (comparator behavior) and the firmware requirement (response behavior), each linked to the Level 1 requirement.
- **Level 3 (verification):** Tests that exercise the combined behavior — ideally a system-level test that injects an over-voltage condition and confirms the motor disables within the specified time.

The numbering scheme mismatch is a practical problem, not a conceptual one. I'd maintain a mapping table in the traceability matrix that translates between the two schemes, and I'd ensure the system-level requirement uses its own numbering that both teams can reference. The key is that the integration requirement becomes the single point of truth for the combined behavior — neither team's document needs to reference the other's directly, because both reference the system requirement.

For verification, I'd insist on at least one system-level test that exercises the full chain — sensor, comparator, interrupt, firmware response — rather than relying solely on separate hardware and firmware tests. The separate tests are necessary but not sufficient, because they can't catch integration issues like interrupt latency, signal integrity on the comparator output, or firmware initialization timing.

**Possible follow-ups:** How would you handle the case where the hardware and firmware teams have already written their requirements and resist adding a new system-level requirement late in the project? What if the system-level test is difficult to design because the over-voltage condition is hard to inject safely?

---

## Q3: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading — for example, rejecting readings that change by more than a specified rate between consecutive samples — needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** The answer depends on what aspects of the control are being verified and what could differ between the development board and production hardware. I'd break the verification into layers.

For the *logic* of the plausibility check — the algorithm that compares consecutive samples and decides whether to reject a reading — a development board with the same microcontroller is likely sufficient, provided the firmware is identical and the sensor input is simulated or injected. The logic itself doesn't depend on the specific PCB layout or the exact sensor model.

However, for the *timing* behavior — how quickly the check responds, whether it can be interrupted by other tasks, whether the sampling rate is stable — production hardware matters. The development board may have different interrupt latency, different clock configuration, or different bus loading than the production PCB. If the plausibility check has a timing component (e.g., "reject readings that change by more than X% within Y milliseconds"), the timing must be verified on hardware that matches the production configuration.

There's also the question of the *sensor interface*. If the plausibility check depends on the actual sensor's output characteristics — noise levels, settling time, sampling artifacts — then testing with a simulated sensor on a development board won't capture real-world behavior. In that case, I'd want at least one verification on production-representative hardware with the actual sensor, even if the bulk of the logic testing happens on the development board.

My general approach would be:
1. Verify the algorithm logic on the development board (or even on a host PC) — this covers the decision-making logic.
2. Verify the timing behavior on production-representative hardware — this covers the real-time constraints.
3. Verify the end-to-end behavior with the actual sensor on production hardware — this covers the interface and integration.

If the risk analysis identifies the plausibility check as a primary risk control (meaning its failure alone could lead to the hazard), I'd lean toward requiring production-hardware verification. If it's a secondary control with other independent protections, development-board testing might be acceptable for the logic portion, with a system-level test on production hardware covering the integration.

**Possible follow-ups:** How would you document the rationale for accepting development-board testing for part of the verification? What if the production hardware isn't available until late in the project — how would you structure the verification to allow early logic testing without delaying the overall campaign?

---

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** This is one of the harder traceability problems because the hazard isn't mitigated by any single node — it's mitigated by the *coordination* between nodes, and that coordination introduces failure modes that don't exist in a single-processor system. I'd approach this in four steps.

First, I'd identify the coordination points. For each hazard, I'd map out which nodes are involved, what information they need to share, and what actions each node must take. This often reveals that the risk control isn't just "Node A does X and Node B does Y" — it's "Node A detects the condition, communicates it to Node B over the bus, and Node B takes action within a specified time." The communication itself is part of the control.

Second, I'd create a system-level requirement that describes the coordinated behavior — something like "When any node detects a fault condition, all nodes shall enter safe state within 100ms of the fault being broadcast on the bus." This requirement sits above the individual node requirements and captures the end-to-end behavior. It's the requirement that maps to the hazard in the risk management file.

Third, I'd trace downward to the individual node requirements. Each node's firmware requirements should include its role in the coordination — the detecting node's requirement to broadcast the fault, the receiving node's requirement to process the broadcast and take action, and any timing requirements for each step. These are derived requirements that trace up to the system-level coordination requirement.

Fourth, I'd pay special attention to the bus communication itself. The risk control depends on the bus being available and the messages being delivered correctly. This means the traceability scheme should include requirements for bus health monitoring, message timeouts, and failure detection — because if the bus fails, the coordination fails, and the risk control fails. These are often overlooked because they're "infrastructure" rather than "safety" requirements.

For verification, I'd insist on system-level tests that exercise the full coordination path — inject a fault at one node, confirm the broadcast, confirm the receiving node's response, and measure the end-to-end timing. Testing each node in isolation is necessary but insufficient, because it can't catch issues like bus contention, message priority inversion, or a node that misses a broadcast because it's busy with another task.

The traceability matrix for this kind of system gets complex, so I'd use a hierarchical structure: hazard → system-level coordination requirement → per-node derived requirements → per-node verification → system-level integration verification. Each level references the next, and the matrix makes it possible to answer the question "if this node's firmware changes, which hazards could be affected?"

**Possible follow-ups:** How would you handle the case where the bus communication itself introduces a new hazard (e.g., a corrupted message causes a node to take an unsafe action)? How would you trace a risk control that requires a specific message to be sent at a specific rate, when the bus scheduling is handled by a real-time operating system?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a comprehensive traceability matrix linking every requirement to a risk control measure and a verification test. However, during a design review, the test lead points out that several verification tests are testing the wrong thing — for example, a test labeled "verifies overcurrent protection" is actually testing nominal current draw. The systems engineer insists the traceability matrix is correct because the requirement numbers match. How would you resolve this disagreement?

**Answer:** The systems engineer is technically correct that the numbers match, but the test lead has identified a substantive problem — the traceability matrix is structurally complete but semantically wrong. The requirement numbers align, but the test doesn't actually verify the requirement. I'd approach this by separating the two issues: the traceability structure and the test content.

First, I'd acknowledge the systems engineer's point — the matrix is internally consistent, and the requirement-to-test links are correctly recorded. That's not the issue. The issue is that the test procedure itself doesn't exercise the requirement's acceptance criteria. The matrix can be perfectly correct and still be useless if the tests don't test what they claim to test.

Second, I'd ask the test lead to walk through the specific test and identify what it actually verifies versus what the requirement demands. For the overcurrent example, the requirement likely specifies a trip threshold and a response time — the test should inject an overcurrent condition and confirm the protection activates. If the test only measures nominal current draw, it's not verifying the requirement, regardless of what the matrix says.

Third, I'd facilitate a joint review of the affected tests — not just the one example, but all tests where the test lead suspects a mismatch. The goal is to identify the scope of the problem: is it one test, several tests, or a systematic issue with how tests were written? This matters because the fix is different for a single error versus a pattern.

Fourth, I'd work with the team to correct the tests, not just the matrix. The matrix should be updated to reflect reality — either the test is corrected to actually verify the requirement, or the requirement is re-examined to confirm it's testable as written. In some cases, the test might be fine but the requirement is ambiguous or untestable, and the requirement needs to be revised.

Finally, I'd use this as a learning opportunity. The fact that the matrix was structurally complete but semantically wrong suggests the team may have been focused on filling in the matrix rather than ensuring the tests were meaningful. I'd suggest adding a peer review step where the test lead and the requirements owner jointly review each test against its requirement before the test is executed — not after.

The key principle is that traceability is a means to an end, not an end in itself. The goal is to ensure that every risk control is actually verified — the matrix is just the tool that makes the gaps visible. If the matrix says everything is covered but the tests don't test what they claim, the matrix is giving false confidence.

**Possible follow-ups:** How would you handle this if the systems engineer continues to resist, arguing that the test lead is "moving the goalposts" and that the tests were reviewed and approved earlier in the project? What if the affected tests are already in the verification report and the project is about to submit to a regulatory body — how would you handle the disclosure?