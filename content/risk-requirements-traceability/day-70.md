# risk-requirements-traceability — Day 70

## Q1: How would you approach tracing a risk control measure that is implemented as a *combination* of a hardware interlock and a firmware acknowledgment — for example, a relay that physically removes power from a heater unless firmware continuously asserts an enable signal — when the hardware and firmware teams each own half of the control and neither team's requirements document references the other?

**Answer:** The core problem is that the control is a *loop*, not two independent features, so tracing it as two separate requirements in two separate documents will always leave a gap at the boundary. I'd start by defining the control at the system level as a single, named risk control measure with its own identifier in the risk management file, and give it a system-level requirement that describes the *integrated behavior* — "power to the heater shall be removed unless a valid enable signal is continuously asserted" — including the failure condition it mitigates and the timing/continuity expectation. That system requirement becomes the parent node.

From there I'd decompose it into two child requirements: one in the hardware requirements document (the relay de-energizes when the enable signal is absent or invalid) and one in the firmware requirements document (the firmware asserts the enable signal only while all preconditions are satisfied, and de-asserts on fault). Each child requirement carries a cross-reference back to the parent system requirement ID, and the parent carries forward references to both children. The key discipline is that the *interface* between them — signal polarity, voltage levels, update rate, what "continuously asserted" means in time — must be captured in an interface control document, because that's exactly where the two teams' assumptions can silently diverge.

For verification, I would not accept two isolated tests as sufficient. Each half can be unit-verified (relay drops out when the signal is removed; firmware de-asserts on fault), but the risk control as a whole needs an integration test that exercises the failure condition end-to-end: inject a fault, confirm the firmware de-asserts, and confirm the relay actually removes power within the required time. The traceability matrix should show the system-level control linked to both child requirements *and* to the integration test, so an auditor can see the whole path in one place rather than reconstructing it across two documents.

**Possible follow-ups:**
- If the two teams use different requirement numbering schemes, how would you keep the cross-references stable as both documents evolve?
- What would you do if the integration test passes but the two unit tests were never formally linked to the parent control?

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a *timing requirement* — for example, "the system shall remove power from the heating element within 500 ms of detecting an over-temperature condition" — when the timing depends on a chain of hardware and firmware elements, each with its own latency, and the 500 ms budget is allocated across them?

**Answer:** A timing requirement like this is really a *budget*, and the traceability challenge is that no single element owns the whole number. I'd treat the 500 ms as a system-level requirement derived directly from the risk control, then decompose it into an allocated budget across the chain: sensor response time, analog signal conditioning/filter delay, ADC conversion and interrupt latency, firmware detection and decision logic, and the actuator/relay drop-out time. Each allocation becomes a child requirement with its own measurable limit, and each child traces back to the parent 500 ms requirement.

The important part is that the allocations must *sum with margin* to less than the total — if the individual worst-case latencies add up to more than 500 ms, the control doesn't actually meet its intent even though every element "passes" its own spec. So I'd want a worst-case timing analysis (often verification by analysis) that shows the sum, plus a system-level test that measures the real end-to-end time under the fault condition. The analysis covers the budget arithmetic; the test confirms the real system behaves as analyzed, since interrupt latency and scheduling jitter are hard to predict purely on paper.

In the traceability matrix, the parent timing requirement links to each allocated child requirement, to the timing analysis, and to the end-to-end test. That way, if any element's latency changes later — a slower sensor, a heavier firmware task — the matrix shows exactly which allocations and which verification evidence are affected.

**Possible follow-ups:**
- How would you handle it if the end-to-end test passes but the sum of the individual worst-case allocations exceeds the budget?
- Where would you draw the line between what the timing analysis must cover and what the physical test must cover?

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** The trap here is that the risk analysis credits *both* controls for reducing risk, which implicitly assumes they are independent — but if they were added at different times by different teams, that independence may never have been verified, and the traceability may only reflect one of them. I'd start by making the redundancy explicit at the risk management level: the hazard links to a single risk control *concept*, which then links to two distinct control implementations, each with its own requirement and its own verification. The matrix should show the hazard fanning out to two controls, not a single control that happens to have two implementations buried in it.

Then I'd focus on the independence claim, because that's what the risk credit depends on. I'd want evidence that the two controls don't share a common failure mode — common power rail, common sensor, common firmware task, common clock — because if they do, a single fault could disable both and the redundancy is illusory. That's often a design-review or analysis activity rather than a test, and it should be traced as its own verification of the independence assumption.

Practically, since the controls were added at different times, I'd reconcile the two requirement sets against the current risk analysis to confirm both are still valid and neither has drifted, then link both to the shared hazard and to a combined verification that demonstrates the hazard is mitigated even if one control fails. The combined test is what actually proves the redundancy, as opposed to two separate tests that each prove one control works in isolation.

**Possible follow-ups:**
- How would you verify the independence of the two controls if they share a common power supply?
- If one control was added late and never formally risk-analyzed, how would you bring it into the traceability scheme?

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *manual* test with no automated logging — the operator toggles a signal and observes an LED — and the risk file treats it as objective evidence?

**Answer:** The concern isn't that manual testing is inherently invalid — plenty of legitimate verification is manual — it's that "operator observes an LED" produces weak, hard-to-audit evidence and is prone to subjectivity and human error. So I'd first ask what the test is actually trying to demonstrate and whether the observation is adequate to demonstrate it. If the control's acceptance criterion is a timing or threshold behavior, an LED glance almost certainly can't capture it, and the test needs instrumentation. If it's a simple presence/absence of a state, a manual test *can* be acceptable, but it still needs to be controlled.

To make it defensible, I'd require a written procedure with explicit steps, the exact expected observation, and pass/fail criteria stated measurably rather than as "LED lights up." I'd add a record of who ran it, when, on what unit, and with what setup, so the evidence is traceable and repeatable. Where feasible, I'd instrument the test — a scope, a logic analyzer, or a data logger — so the result is captured as a measurement rather than a human impression, and I'd note in the test record why the method chosen is sufficient for the risk being controlled.

If the control is safety-significant and the manual observation is the *only* evidence, I'd push to strengthen it, because a single subjective observation is a weak foundation for a risk control. The goal is that an auditor or a future engineer can look at the record and independently judge whether the control was actually demonstrated, not just that someone said it worked.

**Possible follow-ups:**
- How would you decide when a manual observation is acceptable versus when instrumentation is required?
- What would you put in the test record to make a manual test auditable?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is the classic "traceability without understanding" failure — the matrix is complete, but the *why* behind the control never made it into the requirement or the test, so the links are structurally correct and semantically empty. I'd treat it as a process problem, not a blame problem, and start by getting the three people in a room with the risk analysis entry in front of them, walking through the hazard, the control, the requirement, and the test together to see where the intent dropped out.

The likely root cause is that each document was written against its own template without a shared reference to the risk control's intent. So the fix is structural: require that any requirement derived from a risk control carries a short statement of the hazard it mitigates and the failure condition it must handle, and that the verification test's acceptance criteria explicitly reference that failure condition. That way the intent travels with the requirement instead of living only in the risk file.

I'd also add a lightweight review gate — when a risk control is decomposed into requirements and tests, someone checks that the test actually stresses the failure condition, not just the nominal function. And I'd use this instance as a concrete example in a team discussion about why traceability exists: it's not to satisfy an auditor, it's to make sure the person writing the test understands what they're proving. Done well, this turns a paper exercise into a shared understanding, which is the whole point.

**Possible follow-ups:**
- How would you catch this kind of intent loss earlier, before the verification plan is written?
- If the test passes but clearly doesn't exercise the failure condition, what's your immediate next step?