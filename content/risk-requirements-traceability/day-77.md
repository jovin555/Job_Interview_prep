# risk-requirements-traceability — Day 77

## Q1: How would you approach tracing a risk control measure whose effectiveness depends on a *sequence* of events rather than a single action — for example, a control that requires the system to detect a fault, log it, notify the user, and then enter a safe state, where each step is owned by a different subsystem?

**Answer:** The key insight is that a sequence-based control is not one control — it is a control *chain*, and traceability has to be established at two levels simultaneously: the chain as a whole, and each link in it.

At the chain level, I would create a single risk control entry in the risk management file that describes the *end-to-end* behavior and the hazard it mitigates, with a measurable acceptance criterion for the whole sequence (e.g., "from fault detection to safe state within a bounded time, with the fault logged and the user notified before the safe state is entered"). This entry is the anchor that everything else traces back to.

At the link level, I would decompose the chain into its constituent steps and treat each step as a derived requirement with its own owner, its own acceptance criterion, and its own verification activity. Each derived requirement traces *up* to the chain-level control, and the chain-level control traces *down* to each step. This makes the ownership boundaries explicit: the detection step belongs to the sensor subsystem, the logging step to the data subsystem, the notification step to the UI subsystem, and the safe-state transition to the actuator or power subsystem.

The critical part is the *interfaces between steps* — the handoffs. A sequence control fails most often not because any single step is broken, but because the handoff between steps is ambiguous: does "detect" mean the raw threshold crossing, or the debounced and confirmed detection? Does "notify" mean the message was queued, or that it was rendered on the display? I would capture each handoff as an interface requirement (or an ICD entry) with a defined signal, timing, and state, and trace that interface to both the producing and consuming steps. Without this, each team can pass its own test while the chain as a whole fails.

For verification, I would require both per-step verification (each subsystem proves its step works in isolation) and an end-to-end sequence verification (the whole chain is exercised with a realistic fault injection, and the timing and ordering of all four steps is measured). The end-to-end test is the one that actually demonstrates the risk control, and it should be traced to the chain-level control entry, not to any single step.

**Possible follow-ups:**
- If the end-to-end test fails but every per-step test passes, how would you localize the failure?
- How would you handle a case where one step in the chain is implemented by a third-party subsystem you don't control?

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a *user-facing procedural control* — for example, a label instructing the operator to verify a connection before energizing — where the "implementation" is a printed instruction and the "verification" is a usability study rather than a bench test?

**Answer:** Procedural controls are the ones most often under-traced, because they don't fit the "requirement → design element → test" pattern that engineers are used to. But they are still risk controls, and they still need the same discipline — just with different artifact types.

The first thing I would do is make the control *explicit and measurable* in the risk management file. "The operator verifies the connection before energizing" is not measurable. A measurable version would be something like: "The operator is presented with an instruction to verify the connection, and the instruction is comprehensible and actionable under the intended use conditions." That gives the control an acceptance criterion that a usability study can actually evaluate.

The implementation artifact is the label or instruction itself — its content, its placement, its legibility, its language, and its symbols. I would trace the control to that artifact as the design element, and I would treat the label's content and placement as design requirements with their own review criteria (e.g., symbol comprehension, reading distance, contrast under expected lighting). This is where a lot of teams stop, and it's not enough — a legible label that says the wrong thing, or says the right thing in the wrong place, is not an effective control.

The verification activity is the usability study or human factors evaluation, and it needs to be designed to actually stress the failure mode the control is meant to mitigate: does the operator, under realistic conditions (time pressure, gloves, poor lighting, distraction), actually perform the verification? The study protocol should be traced to the control's acceptance criterion, and the results should be recorded as objective evidence — not "the label was reviewed and deemed adequate," but "N representative users were observed, and the verification step was performed in X% of trials."

I would also trace the control to the *training and labeling requirements* in the instructions for use, and to any residual risk evaluation that assumes the operator will perform the step. If the residual risk assessment credits the procedural control, then the usability evidence has to be strong enough to justify that credit — otherwise the residual risk is understated.

**Possible follow-ups:**
- How would you handle a case where the usability study shows the control is effective for trained users but not for untrained ones?
- What would you do if the label cannot be made comprehensible without changing the device's physical design?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *supplier-provided test report* for a purchased component (e.g., a certified relay or an off-the-shelf power module), rather than a test your own team performed?

**Answer:** Supplier test reports can be legitimate verification evidence, but only if you can demonstrate that the report actually covers *your* risk control's failure condition, under *your* operating conditions, on a component that is *equivalent* to what you're using. The default assumption should be that a generic supplier report does not automatically satisfy your specific control — it has to be evaluated against your acceptance criteria.

The first step is to read the supplier report against the risk control requirement, not against the datasheet. Datasheets describe typical and guaranteed performance; test reports describe what was actually tested, under what conditions, with what sample size, and with what acceptance criteria. I would check: does the report exercise the failure mode my control is meant to mitigate? Does it test at the extremes of my operating envelope (temperature, voltage, load, duty cycle)? Is the test setup representative of how the component is used in my design (e.g., a relay tested at a different contact load, or a power module tested with a different input filter)? Is the sample size and test duration sufficient to support the reliability claim?

If the report covers the failure condition but not my operating extremes, I have three options: (a) supplement the supplier report with my own testing at the extremes, (b) perform an analysis (e.g., derating calculation, worst-case tolerance analysis) to show that the supplier's tested conditions bound my operating conditions, or (c) treat the supplier report as partial evidence and add a design review or incoming inspection step to close the gap. The choice depends on the criticality of the control and the strength of the analysis.

I would also verify the *provenance* of the report: is it from the actual manufacturer, or from a distributor? Is it for the exact part number and revision I'm using, or a similar one? Is it current, or has the part been redesigned since? If the part has a revision history, I need to confirm the report applies to the revision I'm buying.

Finally, I would document the *rationale* for accepting the supplier report as verification evidence — not just file the PDF. The rationale should state what the report covers, what it doesn't, and how any gaps are addressed. This is what an auditor will look for: not the existence of a report, but the reasoning that connects it to the risk control.

**Possible follow-ups:**
- How would you handle a supplier that refuses to share the full test report and only provides a certificate of compliance?
- If the supplier report is for a "similar" part rather than the exact one, what additional evidence would you require?

## Q4: How would you approach establishing traceability between risk control measures and requirements when the same risk control measure is implemented differently across multiple product variants or hardware revisions?

**Answer:** The core problem here is that the risk control is a *hazard-level* concept, but the implementation is a *variant-level* concept, and the two don't map one-to-one. The traceability scheme has to preserve the hazard-level identity of the control while allowing the implementation to diverge.

I would structure this as a two-layer traceability model. At the top layer, there is a single risk control entry in the risk management file that describes the control in terms of the hazard it mitigates and the *functional* behavior it must achieve — independent of how it's implemented. For example: "The system shall prevent the heater from being energized unless the enclosure is closed." That entry is variant-agnostic and is the anchor for all variants.

At the second layer, each variant has its own implementation requirement(s) that satisfy the top-layer control. Variant A might implement it with a hardware interlock switch in series with the heater relay; Variant B might implement it with a magnetic sensor read by firmware that gates the relay drive. Each variant's implementation requirement traces *up* to the same top-layer control, and the top-layer control traces *down* to all variant implementations.

The verification layer then has to be handled carefully. Each variant's implementation needs its own verification activity, because the failure modes are different (a stuck interlock switch vs. a sensor misread vs. a firmware logic error). But the *acceptance criterion* for each variant's verification should be derived from the top-layer control's functional requirement, not from the variant's implementation. This ensures that all variants are held to the same hazard-mitigation standard, even though the tests are different.

I would also maintain a variant matrix that shows, for each risk control, which variants implement it and how. This makes gaps visible: if a new variant is introduced and no implementation is listed, the matrix flags it. And if a variant is discontinued, the matrix shows which controls lose an implementation path.

The tricky case is when a variant implements the control *partially* — for example, a low-cost variant that relies on a procedural control instead of a hardware interlock. In that case, the residual risk evaluation has to be done per-variant, because the effectiveness of the control is different. The top-layer control entry should note that the control's effectiveness is variant-dependent, and the risk management file should carry separate residual risk evaluations for each variant.

**Possible follow-ups:**
- How would you handle a variant that is added late in the project, after the risk management file has been baselined?
- If a variant's implementation is found to be ineffective during verification, how would you trace the impact back to the risk analysis?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is a traceability failure that a matrix alone will never catch, because the matrix shows the links as present and complete. The problem isn't missing links — it's that the links are *semantically empty*. The requirement and the test were written to satisfy a numbering scheme, not to satisfy the hazard. I would treat this as a process problem first and a document problem second.

My first move would be to stop treating the traceability matrix as the deliverable and start treating the *risk analysis entry* as the source of truth that every downstream artifact must be able to explain. I would run a focused review — not a full audit — where, for a sample of risk controls (starting with the highest-severity ones), the systems engineer and the test engineer each have to verbally explain, without looking at the matrix, what hazard the control mitigates, what failure condition it's meant to detect or prevent, and how their requirement or test exercises that condition. If they can't, the link is broken regardless of what the matrix says.

For the controls where the intent has been lost, I would re-derive the requirement and the test from the risk analysis entry, not patch the existing ones. That means: read the hazard, read the failure mode, read the control's intended effect, and then ask "what does the system actually need to do, and how would we prove it does that?" The rewritten requirement and test then get re-traced, and the review is repeated until the engineers can explain the intent without the matrix.

The deeper fix is to change how requirements and tests are authored. I would make the risk analysis entry a mandatory input to the requirement-writing and test-writing process — not a document that gets referenced after the fact. Practically, that means the requirement template includes a field for "risk control ID and hazard," and the test template includes a field for "failure condition exercised." If those fields are blank, the artifact isn't complete. This forces the author to engage with the risk analysis at the moment of writing, rather than discovering it during an audit.

I would also address the organizational cause: the systems engineer and test engineer were working in silos, each optimizing for their own deliverable. I would set up a short, recurring cross-functional review — risk engineer, systems engineer, test engineer — where a handful of controls are walked through end-to-end each session. The goal isn't to re-verify everything; it's to build the habit of shared ownership of the control's intent. Over time, this catches intent loss early, when it's cheap to fix, instead of at audit when it's expensive.

**Possible follow-ups:**
- How would you handle a case where the systems engineer and test engineer disagree about what the risk control actually requires?
- If you only have time to re-derive a subset of the controls, how would you prioritize which ones to fix first?