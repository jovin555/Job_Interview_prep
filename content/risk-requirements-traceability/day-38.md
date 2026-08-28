# risk-requirements-traceability — Day 38

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a combination of hardware and firmware, where the hardware team documents the control in their design specification and the firmware team documents their portion in a software requirements document — but neither document references the other, and the risk management file treats the control as a single integrated measure?

**Answer:** The core problem here is that the risk management file treats the control as one logical measure, but the implementation is split across two engineering disciplines that maintain separate documentation silos. I'd approach this by creating a single "risk control implementation" record in the risk management file that explicitly decomposes the control into its hardware and firmware contributions, each with its own traceability path.

First, I'd define the integrated control's behavior at the system level — what hazard it mitigates, what the intended response is, and what failure of the control looks like. Then I'd work with both teams to identify the specific design elements that implement each portion: the hardware team's comparator circuit, threshold setting, and interrupt path; the firmware team's interrupt handler, decision logic, and output disable mechanism.

The key artifact would be a bidirectional mapping table that shows: (1) the risk control measure ID from the risk management file, (2) the hardware design specification section that implements the hardware portion, (3) the software requirements document section that implements the firmware portion, and (4) a note explaining how the two portions interact to achieve the integrated control. This table would live in the risk management file and be referenced from both engineering documents.

For verification, I'd insist on three levels of evidence: hardware-level testing of the sensor/comparator portion, firmware-level testing of the decision/response logic, and a system-level test that exercises the complete chain from sensor stimulus through to the final safe state. Each level would trace back to the appropriate portion of the integrated control record.

The critical point is that neither engineering document needs to fully describe the other discipline's work — but both need to reference the integrated control ID, and the risk management file needs to be the single source of truth that ties them together.

**Possible follow-ups:**
- How would you handle the situation where the hardware and firmware teams use different numbering schemes for their documents?
- What would you do if the system-level verification test reveals a timing issue between the hardware detection and the firmware response that neither team's individual testing caught?

---

## Q2: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading — for example, rejecting readings that change by more than a specified rate between consecutive samples — needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** The decision hinges on what aspects of the control's behavior could differ between the development board and production hardware. I'd start by analyzing the risk control to identify which of its characteristics are purely firmware-logic-dependent versus which depend on the hardware environment.

For a plausibility check on sensor readings, the key question is whether the timing behavior matters. If the check is based on comparing consecutive samples and the sampling rate is determined by a timer that's configured identically on both platforms, then the logic itself can be adequately verified on a development board. However, if the check involves interrupt latency, timing jitter, or interaction with other hardware peripherals that could affect when samples are taken or processed, then production-representative hardware becomes necessary.

I'd also consider the sensor interface itself. If the plausibility check is designed to catch sensor failures — like a stuck-at fault or a short circuit — then the verification needs to demonstrate that the firmware correctly identifies these failure modes when presented with realistic sensor signals. A development board with a signal generator might be able to simulate these conditions, but the electrical characteristics of the actual sensor interface could affect how the failure manifests.

My general approach would be: verify the pure logic on the development board (unit-level testing with simulated inputs), then verify the integrated behavior on production hardware (system-level testing with realistic fault injection). The risk management file should document the rationale for this split, explaining which aspects of the control are platform-independent and which require production-representative verification.

If there's any doubt about whether the hardware environment could affect the control's behavior, I'd err on the side of production hardware testing — the cost of a test is typically far less than the cost of discovering a risk control failure after release.

**Possible follow-ups:**
- What specific aspects of the hardware environment could affect a firmware-based plausibility check?
- How would you document the rationale for using a development board in the verification evidence?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** This is one of the more challenging traceability scenarios because the risk control doesn't live in any single subsystem — it emerges from the coordinated behavior of multiple nodes. I'd approach this by first defining the "coordinated control" as a distinct entity in the traceability scheme, separate from the individual node-level contributions.

The first step would be to document the end-to-end control flow at the system level: which node detects the hazardous condition, what message is sent over the bus, which other nodes receive it, what actions each node takes, and what the overall safe state looks like. This becomes the system-level risk control requirement.

From there, I'd decompose this into per-node requirements. Each node's contribution — whether it's the detecting node's sensing and message generation, or a responding node's message reception and action — becomes a requirement in that node's own requirements document. Each of these node-level requirements traces up to the system-level risk control, and the system-level control traces up to the hazard in the risk management file.

The critical piece is the interface between nodes. The bus message format, timing requirements, and failure behavior (what happens if a message is lost or corrupted) need to be captured in an interface control document, and that ICD needs to be referenced from both the system-level risk control and the node-level requirements. This is where many distributed traceability schemes break down — the interface itself is part of the risk control, but it doesn't belong to any single node's requirements document.

For verification, I'd require three levels of evidence: (1) each node's individual contribution verified against its node-level requirement, (2) the communication protocol verified against the ICD — including fault injection for lost or corrupted messages, and (3) a system-level test that exercises the complete chain from hazard detection through bus communication to coordinated response. The system-level test is non-negotiable because it's the only way to demonstrate that the coordinated control actually works as intended.

**Possible follow-ups:**
- How would you handle the situation where one node's firmware is updated and the message format changes, but the other nodes aren't updated?
- What would you do if the system-level verification test reveals that the coordinated response is too slow to meet the risk control's timing requirement?

---

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification test, but the test was written to verify a *different* requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a common and dangerous gap because the traceability matrix looks complete — there's a link between the risk control and a test, and the test passes — but the evidence is meaningless for the risk control. I'd approach this by first confirming the gap through a careful review of the test procedure against the risk control's failure condition.

The key question is: does the test actually create the conditions that the risk control is designed to detect and respond to? If the test only exercises the system under nominal conditions, it's not providing any evidence that the control works when it's needed. I'd document this as a traceability gap and flag it for immediate correction.

My approach would be to work with the verification engineer to either modify the existing test to include the fault condition, or create a new test specifically for the risk control. The new or modified test needs to: (1) create the specific fault condition identified in the risk analysis, (2) verify that the control detects the condition, and (3) verify that the control produces the correct response — not just that the system continues to operate normally.

I'd also review other traceability links with the same scrutiny. If this test was incorrectly linked to a risk control, there may be other similar issues in the matrix. I'd recommend a systematic review of all risk control-to-test links, focusing on whether each test actually stresses the failure condition the control is meant to mitigate, rather than just checking that the link exists.

Finally, I'd update the traceability matrix to reflect the corrected test assignment and document the gap and its resolution in the design history file. The lesson here is that traceability is not just about having links — it's about having links that represent meaningful evidence.

**Possible follow-ups:**
- How would you distinguish between a test that "incidentally exercises" a risk control versus one that genuinely verifies it?
- What would you do if the corrected test reveals that the risk control doesn't actually work as designed?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by similarity" — meaning the team is relying on test results from a previous product that used a similar component or design. The quality manager argues that similarity is not acceptable evidence for risk controls, because the previous product wasn't tested under the same conditions. The systems engineer argues that the components are identical, the design is nearly the same, and re-running the tests would waste time and money. How would you resolve this disagreement?

**Answer:** I'd start by acknowledging that both parties have valid concerns. The systems engineer is right that re-running identical tests on identical components can be wasteful, and the quality manager is right that similarity arguments are often used to justify shortcuts that compromise safety evidence. The resolution lies in establishing clear criteria for when similarity is acceptable — and then applying those criteria rigorously.

My approach would be to facilitate a structured assessment of each "verification by similarity" case rather than making a blanket decision. For each risk control, I'd ask: (1) Is the component or design truly identical, or just similar? (2) Are the operating conditions — voltage, temperature, loading, environmental stress — the same between the previous product and this one? (3) Was the previous test actually verifying the same risk control under the same failure conditions? (4) Has anything changed in the system context that could affect the component's behavior — for example, a different power supply, a different firmware version, or a different mechanical layout?

If the answers to all four questions are genuinely "yes," then similarity might be defensible — but I'd still want documented evidence of the previous test results, the rationale for why they apply, and a review by someone independent of both the original test and the current project. If any answer is "no" or uncertain, the test needs to be re-run.

I'd also propose a middle ground: rather than re-running the full test suite, we could run a reduced set of confirmation tests on the current product — for example, testing the risk control under the most critical fault conditions — while relying on similarity for the less critical aspects. This addresses the quality manager's concern about objective evidence while respecting the systems engineer's concern about wasted effort.

The key is to move the conversation from "similarity is always acceptable" versus "similarity is never acceptable" to "here are the specific criteria for when similarity provides adequate evidence, and here's how we'll apply them to each case." I'd document the criteria and the assessment results in the design history file so the decision is transparent and auditable.

**Possible follow-ups:**
- What specific criteria would you use to determine whether "identical" components in a similar design can rely on previous test results?
- How would you handle a situation where the previous test results exist but were generated under a different regulatory standard or quality system?