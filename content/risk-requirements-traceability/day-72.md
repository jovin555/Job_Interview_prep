# risk-requirements-traceability — Day 72

## Q1: How would you approach tracing a risk control measure that is implemented as a *latency budget* distributed across a chain of hardware and firmware elements — for example, "the system shall de-energize the output within a bounded time after a fault is detected" — when no single element owns the whole timing requirement?

**Answer:** The core problem is that the risk control is an *emergent* property of a chain, not a property of any one element, so a traceability matrix that only links "requirement → test" at the system level will hide the fact that the budget is silently over-allocated or that one element's latency was never characterized.

My approach would be to decompose the end-to-end timing requirement into an explicit *latency budget allocation* that lives in the requirements hierarchy, not just in a spreadsheet. Concretely:

1. **Model the chain as a sequence of stages.** For a fault-to-de-energize path, that is typically: sensor/condition detection → signal conditioning and comparator propagation → interrupt assertion → firmware ISR entry and debounce → decision logic → output driver turn-off → physical de-energization (relay release, FET discharge). Each stage gets a named owner and a worst-case latency figure with a stated basis (datasheet max, measured, or analysis).

2. **Allocate the budget with margin.** The system-level requirement (e.g., a bounded time) is split into per-stage sub-requirements, each with its own acceptance criterion. The sum of worst-case stage latencies plus a defined margin must be less than the system bound. If it isn't, the requirement is not achievable and that is a design issue to surface early, not a test-time surprise.

3. **Trace each sub-requirement to its own verification.** Hardware stages get characterized by measurement or datasheet analysis; firmware stages get verified with timing instrumentation on target; the output stage gets verified with a scope or logic analyzer. Each sub-requirement has a bidirectional link: up to the system timing requirement, and up to the risk control measure it contributes to.

4. **Verify the composite at system level.** Even with all sub-requirements verified, you still need an end-to-end test that injects the fault condition and measures the actual de-energization time on production-representative hardware, because the chain can have interactions (interrupt latency under load, scheduler jitter) that no single-stage test captures.

5. **Keep the allocation under configuration control.** If any stage's latency changes — a firmware change, a different driver, a slower relay — the allocation must be revisited, and the traceability matrix should make it obvious which system requirement is affected.

The key discipline is that the *budget* is a first-class artifact. Without it, the traceability matrix shows a green link from requirement to test, but nobody can answer "what is the worst-case end-to-end latency and where does it come from?"

**Possible follow-ups:**
- How would you handle a stage whose worst-case latency is not well characterized — for example, firmware interrupt latency that depends on what else the scheduler is doing?
- If the end-to-end test passes but one stage's measured latency exceeds its allocated sub-requirement, how would you treat that in the verification record?

## Q2: How would you approach establishing traceability when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls were added at different times by different teams?

**Answer:** Redundancy is where traceability most often quietly breaks, because the risk analysis credits two controls but the requirements and verification artifacts were written independently and may not acknowledge each other. The failure mode I would guard against is a matrix that shows two green links to two passing tests, while nobody has verified that the two controls are actually *independent* — which is the property the risk credit depends on.

My approach:

1. **Make the redundancy explicit in the risk file.** The risk control measure should be documented as a single measure with two implementation channels, each with its own hazard-mitigation contribution, and an explicit statement of the independence assumption (e.g., "channel A and channel B do not share a power rail, clock, or firmware image"). If the independence assumption is not stated, it cannot be verified.

2. **Trace each channel separately, then trace the pair.** Each channel gets its own requirement(s), design element(s), and verification activity. Then add a *cross-link* or a dedicated "redundancy requirement" that captures the independence property itself — for example, "the two channels shall not share a common power source" — with its own verification (inspection of the schematic, or a fault-injection test that disables one channel and confirms the other still mitigates the hazard).

3. **Reconcile the two teams' artifacts.** Because the controls were added at different times, the numbering schemes and document structures likely differ. I would not force a renumbering; instead I would add a mapping layer — a traceability record that references both artifacts by their own identifiers and points to the shared risk control measure. The mapping is the artifact that makes the redundancy auditable.

4. **Verify the hazard is mitigated with either channel alone.** A common gap is that the system-level test exercises both channels together and passes, but never demonstrates that each channel independently mitigates the hazard. I would require a fault-injection test per channel: disable channel A, confirm channel B mitigates; disable channel B, confirm channel A mitigates. This is what actually justifies the redundancy credit.

5. **Check for common-cause failures.** Independence is an assumption that must be challenged. Shared connectors, shared firmware, shared calibration constants, or a common mode of the sensor can all break it. If a common cause exists, the risk analysis credit is overstated and the traceability should reflect that — either the credit is reduced or an additional control is added.

The practical outcome is that the traceability matrix has three kinds of links for a redundant control: channel A → its verification, channel B → its verification, and the redundancy/independence requirement → its verification. Missing the third link is the most common audit finding.

**Possible follow-ups:**
- How would you verify independence when the two channels share a microcontroller but use different peripherals?
- If a common-cause failure is identified after both channels are already built, how would you handle the traceability and risk-file updates?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *manual* test with no automated logging — the operator toggles a signal and observes an LED — and the risk file treats it as objective evidence?

**Answer:** The issue is not that manual tests are inherently invalid — many legitimate verification activities are manual — but that "operator observes an LED" produces evidence that is hard to reproduce, hard to audit, and easy to misinterpret. The question I would ask is: does the evidence actually demonstrate the acceptance criterion, and can a third party reconstruct what happened?

My approach would be to assess the test against three criteria and then decide whether to strengthen it, replace it, or accept it with justification:

1. **Is the acceptance criterion measurable?** If the requirement says "the control shall de-energize the output within a bounded time," then "the LED went out" is not a measurement of that criterion — it is a qualitative observation. The test needs an instrument (scope, logic analyzer, current probe) that captures the actual timing or state transition. If the requirement is genuinely binary and the LED is a direct, unambiguous indicator of the state under test, then observation may be adequate — but that needs to be argued explicitly, not assumed.

2. **Is the evidence reproducible and attributable?** A manual test with no logging produces a pass/fail assertion in a report, but no raw data. For a risk control, I would want at minimum: a written procedure with the exact steps, the equipment used and its calibration status, the pass/fail criterion stated numerically, and a record of the observed result. Ideally, the test is instrumented so the evidence is a capture file rather than a human observation.

3. **Does the test actually stress the failure condition?** This is the deeper question. A manual toggle test often exercises the control under nominal conditions — the operator applies a clean signal and watches the output. If the risk analysis specifies the control must operate under a fault condition (e.g., sensor out of range, supply droop), the manual test may not exercise that condition at all, regardless of how it is logged.

If the test fails any of these, I would treat it as a verification gap and either upgrade the test (add instrumentation, add fault injection, tighten the acceptance criterion) or, if the control genuinely cannot be tested more rigorously, document the rationale and the residual uncertainty in the risk file. What I would not do is leave a manual observation as the sole evidence for a risk control without an explicit justification for why that level of evidence is sufficient.

**Possible follow-ups:**
- How would you decide when a manual test is acceptable versus when instrumentation is required?
- If the manual test was already executed and the product is near release, how would you handle the gap without invalidating the whole verification campaign?

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** This is a variant of the redundancy problem, but the emphasis here is on the *organizational* dimension: two teams, two timelines, two sets of artifacts, and a risk file that treats the control as one thing. The traceability scheme has to bridge that without forcing either team to renumber or restructure their documents.

I would structure the scheme around a **risk control measure as the anchor entity**, with the following links:

- **Risk control measure → hazard(s) it mitigates** (from the risk analysis).
- **Risk control measure → implementation channel A** (owned by team A, referenced by team A's requirement ID).
- **Risk control measure → implementation channel B** (owned by team B, referenced by team B's requirement ID).
- **Risk control measure → independence requirement** (the property that justifies crediting both channels).
- **Each channel → its verification activity** (owned by whichever team or the test team).
- **Independence requirement → its verification activity** (often a fault-injection or inspection test).

The anchor entity is what makes the scheme work when the two teams use different numbering. Neither team has to adopt the other's identifiers; the traceability record holds both and points to the shared risk control measure. This is essentially a mapping layer, and it should be maintained as a controlled artifact, not a spreadsheet that drifts.

Two practical points:

1. **Timing matters.** If channel A was added early and channel B was added later (perhaps in response to a residual risk finding), the risk file entry for the control should record *when* each channel was added and *why*. This matters for audit and for understanding whether the redundancy was a deliberate design choice or a retrofit. A retrofit redundancy is more likely to have hidden common-cause dependencies.

2. **Ownership of the composite verification.** Someone has to own the end-to-end test that demonstrates the hazard is mitigated with either channel alone. If both teams assume the other owns it, it will not get done. I would assign that explicitly — typically to the systems or test function — and make it a named deliverable in the verification plan.

The scheme should also support gap analysis: a query that asks "which risk control measures have fewer than two verified implementation channels?" should return the redundant controls that are not actually redundant in practice.

**Possible follow-ups:**
- How would you handle a situation where channel B was added as a retrofit and shares a component with channel A that was not originally intended to be shared?
- If the two teams disagree about which channel is "primary" and which is "backup," how does that affect the traceability and the verification strategy?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is the classic "traceability without traceability" problem: the matrix is complete, the audit would pass, but the safety intent has been lost because the people who wrote the requirement and the test never understood *why* the control exists. The links are syntactic, not semantic. I would treat this as a process failure, not a documentation failure, and address it at both levels.

**Immediate actions:**

1. **Reconstruct the intent for the affected controls.** For each risk control measure in this state, I would bring the systems engineer, the test engineer, and the risk analyst into a short working session and walk the chain: hazard → risk control measure → requirement → test. The goal is not to rewrite everything, but to confirm that the requirement actually captures the control's intent and that the test actually exercises the failure condition the control mitigates. Where it doesn't, that is a real gap to fix.

2. **Check whether the test actually stresses the failure condition.** This is the most likely place for a real defect. A test written without knowledge of the risk analysis often exercises the requirement under nominal conditions and passes, while never touching the fault condition the control exists to handle. If that is the case, the test needs to be rewritten, not just re-linked.

3. **Check whether the requirement is complete.** A requirement written without the risk context may omit the failure condition, the timing bound, or the operating modes in which the control must function. If so, the requirement needs to be revised and the change propagated.

**Systemic actions:**

4. **Change the authoring workflow so the risk context travels with the requirement.** The most effective fix is to make the risk control measure ID and a one-line statement of the hazard a mandatory field in the requirement record, and to require the test author to reference the same. This is a tooling and template change, not a training change — it makes the intent visible at the point of authoring rather than requiring someone to go read the risk file.

5. **Add a semantic review step to the design review process.** A traceability review that only checks that links exist is insufficient. The review should include a spot-check where a reviewer reads the risk control measure, then reads the requirement and the test, and asks: "does this test actually demonstrate this control mitigates this hazard?" If the reviewer cannot answer yes from the documents alone, the chain is broken.

6. **Consider whether the risk analysis itself is being treated as a living document.** If the risk file is written once and then frozen while requirements and tests evolve, this problem will recur. The risk analysis should be revisited whenever requirements change, and the traceability scheme should make it obvious when a requirement has changed without a corresponding risk review.

The behavioral dimension is that this situation usually reflects a team that has been told to "do traceability" without being told *why*. The fix is partly mechanical (templates, tooling, review checklists) and partly cultural (making the risk analysis a document people actually read, not a compliance artifact). I would be careful not to frame it as blame — the systems engineer and test engineer were doing their jobs as defined — but I would be clear that the current state is not acceptable for a safety-related control and that the process needs to change so it does not recur.

**Possible follow-ups:**
- How would you prioritize which controls to re-examine first, given that you may have limited time before a design review or audit?
- If the re-examination reveals that a test does not actually stress the failure condition, how would you handle the schedule impact of rewriting and re-running it?