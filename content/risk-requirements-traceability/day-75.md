# risk-requirements-traceability — Day 75

## Q1: How would you approach tracing a risk control measure that is implemented as a *user-facing procedural control* — for example, a label instructing the operator to verify a connection before energizing — where the "implementation" is a printed instruction and the "verification" is a usability study rather than a bench test?

**Answer:** Procedural controls are the weakest tier in the risk control hierarchy and should only be relied on when design controls (inherent safety, guards, interlocks) cannot reduce risk adequately — but when they are used, they still need a complete traceability chain, just with different artifact types than a hardware or firmware control.

The chain I would build looks like this: hazard → risk control measure (in the risk management file, explicitly labelled as a procedural/information-for-safety control) → a requirement in the SRS or labelling specification that states the *content and placement* of the instruction in measurable terms (e.g., "the label shall be legible at a viewing distance of X under Y lux," "the instruction shall precede the connection step in the IFU") → a design element (the label artwork, the IFU section) → a verification activity. The verification activity here is typically a usability engineering study or a human-factors validation, not a functional test, and the acceptance criterion should be tied to the risk analysis — e.g., the proportion of representative users who perform the step correctly, or the absence of use errors that lead to the hazardous situation.

The key discipline is that the requirement must be written so it can actually be verified. "The label shall warn the user" is not verifiable; "the label shall contain the following text at a minimum font height of X mm, positioned within Y mm of the connector" is. I would also make sure the risk file does not credit the procedural control with more risk reduction than the usability evidence supports — procedural controls are usually assigned a high probability of occurrence in the risk estimation matrix precisely because users skip steps.

**Possible follow-ups:**
- How would you handle a situation where the usability study shows the instruction is followed correctly by trained users but not by untrained ones, and the device is intended for both?
- If the label artwork changes during a design iteration, how would you ensure the traceability links to the verification evidence are updated rather than silently orphaned?

## Q2: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *supplier-provided test report* for a purchased component (e.g., a certified relay or an off-the-shelf power module), rather than a test your own team performed?

**Answer:** Supplier evidence can be legitimate verification evidence, but only if you can demonstrate that the supplier's test conditions bound the conditions your device will actually see, and that the component is used within the supplier's specified ratings. The traceability link should point to the supplier report *plus* a documented justification of applicability — not just to the report number.

The reasoning: a supplier report verifies the component against the supplier's specification, not against your risk control's failure condition. If your risk analysis says the relay must open within a bounded time under a specific fault current, and the supplier's report only characterizes nominal switching, the report does not verify your control. So the first step is to compare the supplier's test conditions against the conditions in your risk analysis and your derating calculations. If they match or bound them, the report can be accepted as verification evidence, with a note in the traceability matrix explaining the applicability argument. If they don't, you need either additional testing at the component or subsystem level, or a design change to bring the application inside the supplier's characterized envelope.

I would also check whether the supplier report is traceable to a specific component revision or lot, because a report for revision A does not verify revision B. And I would keep the supplier report in the DHF as a controlled document, not as a loose PDF, so the link is auditable.

**Possible follow-ups:**
- How would you handle a supplier that refuses to share the underlying test data and only provides a pass/fail certificate?
- If the component is later second-sourced, how would you decide whether the existing supplier evidence still applies?

## Q3: How would you approach establishing traceability for a risk control measure that is implemented as a *combination of a hardware interlock and a firmware acknowledgment* — for example, a relay that physically removes power from a heater unless firmware continuously asserts an enable signal — when the hardware and firmware teams each own half of the control and neither team's requirements document references the other?

**Answer:** This is a classic "split control" problem, and the fix is to treat the control as a single system-level entity in the risk file, then decompose it into two *linked* requirements — one hardware, one firmware — that each carry an explicit cross-reference to the other and to the shared risk control ID.

Concretely, I would introduce a system-level requirement that describes the control as a whole (e.g., "the system shall remove power from the heater within a bounded time if the firmware enable signal is not continuously asserted"), and then derive two child requirements: a hardware requirement for the relay and its drive circuit, and a firmware requirement for the enable-signal generation and its timing. Both children reference the parent, and the parent references the risk control ID. The traceability matrix then shows the full path from hazard through the parent requirement to both children and to their respective verification activities.

The verification strategy also needs to be explicit about the interface between the two halves. A hardware-only test that drives the enable signal from a bench supply verifies the relay path but not the firmware's ability to generate the signal under fault conditions; a firmware-only test on a development board verifies the logic but not the relay's actual behavior. So I would require at least one integrated test that exercises the complete path — fault injected at the sensor, firmware response, relay de-energization, measured at the heater — in addition to the unit-level tests. The integrated test is the one that actually verifies the risk control; the unit tests are supporting evidence.

**Possible follow-ups:**
- If the firmware enable signal is generated by a watchdog peripheral rather than by application code, how does that change the ownership boundary and the verification approach?
- How would you handle a late change to the relay part number that alters its dropout time, given that the firmware timing requirement was written against the original part?

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** Redundant controls are one of the cases where a naive traceability matrix breaks down, because the matrix wants a one-to-one or one-to-many mapping and redundancy is inherently many-to-one at the hazard level. The scheme I would use is to give the hazard a single risk control *entry* in the risk file that explicitly lists both controls as a set, with a note that the risk reduction credit assumes both are present and independent. Then each control gets its own requirement(s) and its own verification activity, but both requirements carry a cross-reference to the shared risk control ID and to each other.

The independence claim is the part that most often goes unverified. If the risk analysis credits both controls, it is implicitly claiming that a single failure cannot defeat both. That claim needs its own verification activity — typically a common-cause failure analysis or a design review specifically examining shared power, shared clock, shared sensor, shared firmware, or shared connector. Without that, the redundancy is nominal, not real, and the risk file is overstating the risk reduction.

The "added at different times" aspect is a configuration-management problem more than a traceability problem. I would make sure both controls are captured under the same risk control ID in the current revision of the risk file, and that the traceability matrix reflects the current state, not the state at the time each control was added. If the two controls were added by different teams, I would also check that the interface between them is documented — for example, if both controls act on the same output, what happens if they disagree?

**Possible follow-ups:**
- How would you verify the independence claim if the two controls share a common power rail but are otherwise separate?
- If one of the two controls is later removed for cost reasons, how would you re-evaluate the residual risk and update the traceability links?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is the failure mode that traceability is supposed to prevent, and it happens when traceability is treated as a documentation exercise rather than as a shared understanding. The links are technically present, but the semantic content — *why* the control exists and *what failure condition* it must mitigate — has not propagated.

My first move would be to stop treating this as a paperwork problem and treat it as a communication problem. I would bring the systems engineer, the test engineer, and the risk analyst into the same room with the specific risk control entry, and walk through it together: what is the hazardous situation, what is the failure condition the control must detect or prevent, what does the requirement actually say, and what does the test actually do. In most cases, the gap becomes obvious within a few minutes of that conversation, and the fix is either to rewrite the requirement so it carries the safety intent explicitly, or to rewrite the test so it exercises the failure condition rather than just the nominal function.

Structurally, I would then make two changes to prevent recurrence. First, every safety-derived requirement should carry a short "safety intent" note or a direct reference to the risk control ID in its text, not just in the traceability matrix — so anyone reading the requirement in isolation understands why it exists. Second, the test procedure should include the failure condition it is meant to exercise, again in the procedure itself, not just in the matrix. The matrix is a navigation aid; the intent has to live in the artifacts.

I would also add a review gate: before a verification activity is accepted as evidence for a risk control, someone who has read the risk analysis entry — ideally the risk analyst or a systems engineer acting as a reviewer — should confirm that the test actually stresses the failure condition. That is a small process change, but it catches exactly this class of problem.

**Possible follow-ups:**
- How would you handle the situation if the test engineer pushes back, arguing that rewriting the test is out of scope because the test already passes and the schedule is tight?
- If you find this pattern across many controls rather than just one, how would you decide whether to fix them individually or to pause and rework the traceability process as a whole?