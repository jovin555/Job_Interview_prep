# risk-requirements-traceability — Day 71

## Q1: How would you approach tracing a risk control measure that is implemented as a *latency budget* distributed across a chain of hardware and firmware elements — for example, "the system shall de-energize the output within a bounded time after a fault is detected" — when no single element owns the whole timing requirement?

**Answer:** The core problem is that a single end-to-end timing requirement is really a *budget* that must be decomposed and then re-aggregated for verification. I would start by treating the overall bound as a system-level safety requirement and then allocating it across the detection-to-response chain: sensor/condition detection latency, signal conditioning and comparator propagation, interrupt latency and firmware scheduling jitter, decision logic execution, and finally the actuator or power-switch turn-off time. Each allocation becomes a derived requirement owned by the responsible element, with its own margin so the sum of worst-case values stays inside the overall bound.

The traceability scheme then has to capture two distinct relationships: the vertical link from the system-level hazard and its risk control down to each allocated sub-requirement, and the horizontal link showing that the allocations are mutually consistent (i.e., they add up). I would document the budget explicitly — a table or timing diagram showing each contributor, its worst-case value, and the remaining margin — and make that budget a controlled artifact referenced by both the system requirement and the individual element requirements. Verification is then layered: each element verifies its own allocation (often by analysis or bench measurement), and a final system-level test verifies the aggregate under worst-case conditions, because individual element compliance does not guarantee the sum holds when latencies interact.

**Possible follow-ups:**
- How would you handle the case where one element's worst-case latency can only be established by analysis rather than measurement?
- If a later design change increases one element's latency, how would your traceability scheme surface the impact on the overall bound?

## Q2: How would you approach establishing traceability when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls were added at different times by different teams?

**Answer:** Redundancy creates a traceability trap: because the hazard is covered, it's tempting to trace only one control and treat the second as a bonus. But if the risk analysis *credits* both — for example, claiming a lower residual risk because two independent means exist — then both must be traceable, and critically, the *independence* claim itself must be traceable, because that's what justifies the credit.

I would structure it so the hazard links to a single "risk control" entry that explicitly states the redundancy intent, and that entry fans out to two implementation branches, each with its own requirement, design element, and verification activity. The independence assumption gets its own verification: a common-cause analysis or a documented argument showing the two controls don't share a power rail, clock, sensor, or firmware path that could fail both at once. Because the controls were added at different times, I'd also reconcile the numbering and ownership — assign a single parent identifier for the redundant control and cross-reference both teams' artifacts to it, so neither branch can be changed or removed without the change control process flagging the impact on the shared hazard.

**Possible follow-ups:**
- How would you detect that a later change to one control has silently broken the independence assumption?
- If one of the two controls is removed during a cost reduction, what has to be re-evaluated in the risk file?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *manual* test with no automated logging — the operator toggles a signal and observes an LED — and the risk file treats it as objective evidence?

**Answer:** The concern isn't that manual tests are inherently invalid — many legitimate verification activities are manual — it's whether the evidence produced is *objective, reproducible, and traceable to the specific failure condition*. A test where an operator toggles a signal and watches an LED can be perfectly valid, but only if the procedure defines the exact stimulus, the exact expected response, the pass/fail criterion, and a way to record what actually happened (who ran it, on what unit, at what revision, with what result).

So I would not reflexively reject it; I'd assess whether the evidence meets that bar. If the acceptance criterion is subjective ("the LED lights up") and there's no record beyond a checkbox, the evidence is weak — especially for a safety control whose failure condition is subtle. In that case I'd strengthen it: define a measurable criterion, add instrumentation or a logged capture where feasible, and require the record to include the unit serial number and firmware/hardware revision. Where the control's failure mode is genuinely binary and easily observed, a well-documented manual test may be acceptable, but I'd want the rationale for that decision recorded rather than assumed. The key is that the *method* should match the *criticality* of the control, and the traceability should point to evidence that a third party could audit and reproduce.

**Possible follow-ups:**
- How would you decide which manual tests are acceptable as-is versus which need instrumentation?
- What minimum information should a manual test record contain to count as objective evidence?

## Q4: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is the classic "traceable but not connected" failure — the matrix is complete, but the *meaning* has been dropped at each handoff. The links prove the documents reference each other; they don't prove anyone understood why the control exists. I'd treat it as a process problem first and a document problem second.

My approach would be to make the risk analysis the *source* that the other artifacts are derived from, rather than a parallel document that happens to share identifiers. Practically, that means the risk control entry should carry a short statement of the hazard, the failure condition being mitigated, and the intended effect — and the derived requirement and test should each restate enough of that intent that a reader can tell whether they're actually addressing it. I'd then run a focused review where the systems engineer, test engineer, and the person who owns the risk analysis sit down together and walk the chain for the highest-severity controls, confirming that the requirement captures the control's intent and that the test actually stresses the failure condition. For the longer term, I'd build the intent statement into the templates and make "does this requirement/test reflect the risk control's intent?" an explicit review criterion, so the connection is maintained by the process rather than by individual diligence.

**Possible follow-ups:**
- How would you prioritize which controls to review first if you can't review them all?
- What would you change in the templates to prevent this from recurring?

## Q5: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** This is essentially the same structural problem as redundant controls generally, but the "added at different times by different teams" aspect adds a change-control dimension. I'd establish a single parent risk control entry in the risk management file that names the hazard, states that mitigation is redundant, and records the independence rationale. From that parent, two child branches trace to each team's requirement, design element, and verification activity. The parent identifier is the anchor that both teams' artifacts reference, so the redundancy is visible in one place even though the implementations live in separate documents.

The timing issue matters because the second control was likely added later, possibly without revisiting the first team's assumptions. So I'd verify that the independence claim still holds given how each control was actually built — shared resources, common firmware, common power — and record that check. I'd also make sure the change-control process treats the parent as a controlled item: modifying or removing either branch should trigger a review of the redundancy credit and the independence argument. The goal is that no one can quietly weaken one control and leave the risk file still claiming the benefit of two.

**Possible follow-ups:**
- How would you verify independence when both controls ultimately run on the same microcontroller?
- If the two teams use different numbering schemes, how would you keep the parent-child links unambiguous?