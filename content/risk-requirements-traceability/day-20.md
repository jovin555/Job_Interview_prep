# risk-requirements-traceability — Day 20

## Q1: How would you approach establishing traceability for a risk control measure that is implemented through a combination of hardware and firmware, where the hardware team documents the control in their design specification and the firmware team documents their portion in a software requirements document — but neither document references the other, and the risk management file treats the control as a single integrated measure?

**Answer:** The core problem here is that the risk management file treats the control as one integrated measure, but the engineering artifacts treat it as two separate pieces with no cross-references. I'd start by creating a single "risk control implementation" record in the risk management file that explicitly decomposes the control into its hardware and firmware contributions, with each contribution linked to the relevant design document and specific requirement/design element number. This decomposition record becomes the bridge between the two engineering documents.

Next, I'd add bidirectional cross-references: the hardware design specification should note that the comparator output feeds a firmware response (referencing the software requirements document and specific requirement ID), and the software requirements document should reference the hardware signal it responds to. Even if the teams maintain separate documents, the traceability matrix can link them through the risk control ID as the common key.

For verification, I'd map each contribution to its appropriate verification activity — the hardware comparator's trip point to a hardware test, the firmware response time to a software test — and then add a system-level test that exercises the integrated control end-to-end. The system-level test is essential because it validates the interface between the two contributions, which neither subsystem test can catch. The traceability matrix would then show: hazard → risk control → hardware contribution → hardware requirement → hardware test, and the same for firmware, plus the integrated system test.

**Possible follow-ups:** How would you handle the situation where the hardware and firmware teams use different numbering schemes for their requirements? What if the system-level test is impractical to run in all fault conditions — how would you justify relying on subsystem tests plus a single integrated test?

---

## Q2: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** The key question is whether the plausibility check's behavior could be affected by differences between the development board and production hardware. I'd start by analyzing what the plausibility check actually depends on: the sensor interface (ADC characteristics, sampling timing), the firmware execution environment (clock speed, interrupt latency), and the specific failure modes the check is meant to detect.

If the check is purely algorithmic — for example, comparing consecutive readings and rejecting changes above a threshold — and the sensor input is injected via a test signal rather than relying on the actual sensor, then a development board with the same microcontroller might be sufficient, provided the clock configuration and ADC setup match production. However, if the check depends on timing characteristics that could vary with the production board's layout, power supply behavior, or sensor interface, then production-representative hardware becomes necessary.

I'd also consider the risk context. For a risk control measure that mitigates a serious hazard, the verification evidence needs to be defensible to regulators. A development board test might be acceptable if accompanied by an analysis showing that the board differences don't affect the control's behavior — for example, a timing analysis demonstrating that the plausibility check's time window is insensitive to the expected variation in ADC sampling jitter. But if there's any reasonable doubt, I'd err toward production hardware, because the cost of re-verification after a regulatory finding is far higher than the cost of running the test on the right hardware initially.

A practical middle ground is to run the algorithm-level tests on the development board (covering the logic thoroughly) and then run a smaller set of confirmation tests on production hardware to validate that the implementation behaves as expected in the real environment.

**Possible follow-ups:** What specific board differences would you look for when making this assessment? How would you document the rationale for using a development board if you chose that route?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** This is one of the more challenging traceability scenarios because the risk control doesn't live in any single subsystem — it emerges from the interaction between nodes. I'd approach this in three layers.

First, at the system level, I'd define the risk control as a system-level behavior with a clear description of the coordination mechanism: which node detects the condition, what message is sent, which node(s) act on it, and what the expected timing and behavior are. This system-level definition becomes the anchor in the risk management file.

Second, I'd decompose the control into per-node contributions. Each node's firmware requirements document would contain its specific piece — for example, Node A's requirement to detect the fault and broadcast a specific message, Node B's requirement to receive that message and shut down its motor within a specified time. Each of these per-node requirements traces to the system-level risk control.

Third, I'd add interface-level traceability. The communication protocol — message format, timing, error handling — needs its own requirements, typically in an interface control document or the bus protocol specification. These interface requirements are critical because the coordination can fail not because any single node misbehaves, but because the interface between them is wrong.

For verification, I'd use a combination of node-level tests (each node's contribution tested in isolation) and system-level tests (the full coordinated behavior tested across the bus). The system-level test is non-negotiable here because it's the only way to demonstrate that the coordination actually works — including timing, message delivery, and failure handling. I'd also include fault-injection tests on the bus itself, such as message corruption or loss, to verify the system degrades safely.

The traceability matrix would show: hazard → system-level risk control → per-node requirements → per-node tests, plus → interface requirements → interface tests, plus → system-level integration test. This layered approach makes gaps visible — if a node's contribution isn't traced to a test, or if the interface requirements aren't traced to verification, the gap analysis will flag it.

**Possible follow-ups:** How would you handle the situation where different nodes are developed by different teams with different requirement management tools? How would you verify the timing aspects of the coordinated response?

---

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification test, but the test was written to verify a *different* requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a common and dangerous gap because the traceability matrix looks complete — the risk control is linked to a test, and the test passes — but the evidence is meaningless for the risk control. The first step is to recognize that a traceability link is only valid if the test actually exercises the failure condition the control mitigates. I'd start by reviewing the test procedure against the risk control's intended function, specifically asking: does this test create the fault condition, or does it just run the system normally?

If the test doesn't stress the failure condition, I'd flag it as a traceability gap and initiate a correction. The options are: (1) modify the existing test to include the fault condition, (2) create a new test specifically for the risk control, or (3) if the existing test genuinely can't be modified, document why and create a separate verification activity. I'd also review other risk controls traced to the same test to see if they have the same problem — this often reveals a systemic issue where tests were mapped to requirements based on requirement numbers rather than actual test content.

Beyond fixing the immediate gap, I'd look at the root cause. How did this happen? Was the traceability matrix built by someone who didn't understand the test content? Was there a review step that should have caught it? I'd strengthen the review process — for example, requiring that each risk-control-to-test link include a brief description of how the test stresses the failure condition, not just a test ID number. This makes the link self-documenting and reviewable.

Finally, I'd document the discrepancy and the correction in the design history file, because this is exactly the kind of issue a regulatory auditor would probe. The documentation should show that the gap was identified, analyzed, and corrected, with evidence that the risk control is now properly verified.

**Possible follow-ups:** How would you prevent this from happening in the first place on future projects? What if the test engineer argues that modifying the test to include the fault condition would invalidate other verification results linked to that test?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by analysis" — for example, a worst-case timing analysis or a thermal derating calculation — rather than physical tests. The quality manager argues that analysis is not objective evidence and demands physical testing for all risk controls. The systems engineer argues that some controls, like timing margins or thermal derating, can only be practically verified by analysis, and that physical testing would be impractical or impossible. How would you resolve this disagreement?

**Answer:** I'd start by acknowledging that both sides have legitimate points. The quality manager is right that physical testing provides the strongest evidence, but the systems engineer is also right that some controls are inherently analytical — you can't physically test a worst-case timing margin in a way that covers all combinations, and thermal derating is fundamentally a calculation-based verification. The goal isn't to pick a winner but to find a defensible position that satisfies both the regulatory requirements and engineering practicality.

My approach would be to facilitate a structured discussion around three questions. First, what does the relevant standard actually require? IEC 60601 and ISO 14971 don't mandate physical testing for every control — they require objective evidence, and analysis can be objective evidence if it's properly documented, uses valid methods, and has appropriate assumptions and margins. Second, what is the risk severity? For a control mitigating a serious hazard, I'd want stronger evidence — possibly a combination of analysis and a targeted physical test that validates the analysis's key assumptions. Third, what are the limitations of each approach? Analysis is only as good as its assumptions and models; physical testing only covers the specific conditions tested.

I'd propose a risk-based framework: for each "verification by analysis" activity, we'd assess whether the analysis is sufficient on its own, or whether a physical test is needed to validate the analysis or cover conditions the analysis can't address. For example, a worst-case timing analysis might be acceptable if it's based on measured component parameters and includes sufficient margin, but I'd want a physical test to confirm the system doesn't miss a critical deadline under representative loading. For thermal derating, the analysis might be sufficient if the thermal model has been validated against measurements on a similar design.

I'd also suggest a practical compromise: run a limited set of physical tests that validate the analysis's key assumptions, rather than attempting to physically test every condition. This gives the quality manager physical evidence while respecting the systems engineer's point that exhaustive physical testing is impractical. The key is documenting the rationale — why analysis is appropriate for this control, what assumptions it makes, and what physical evidence supports those assumptions.

If we still couldn't agree, I'd escalate to the regulatory affairs or quality assurance director with a clear summary of both positions and a recommendation, because ultimately this is a compliance judgment that needs a decision from someone with authority over the quality system.

**Possible follow-ups:** How would you decide which analyses are acceptable on their own versus which need physical test validation? What if the quality manager insists that the standard explicitly requires physical testing for all risk controls — how would you verify that claim?