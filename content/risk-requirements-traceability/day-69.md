# risk-requirements-traceability — Day 69

## Q1: How would you approach tracing a risk control measure that is implemented as a *latency budget* distributed across a chain of hardware and firmware elements — for example, "the system shall de-energize the output within a bounded time after a fault is detected" — when no single element owns the whole timing requirement?

**Answer:** The core problem is that a single system-level timing requirement is satisfied only by the *sum* of latencies contributed by several elements, and no individual element's requirements document can state the whole thing. The approach is to decompose the budget explicitly rather than leave it implicit.

First, I would allocate the total budget across the chain as a set of sub-requirements, each owned by one element — sensor detection latency, signal conditioning/sampling latency, firmware detection and decision latency, and actuator/relay de-energization latency. Each sub-requirement gets a numeric allocation with margin, and the allocations must sum to less than the total budget (never equal to it — you want headroom for the elements you haven't thought of). This turns one unowned requirement into several owned ones.

Second, I would make the decomposition itself a traceable artifact: the system-level timing requirement traces down to each sub-requirement, and each sub-requirement traces to its own verification activity. The system-level verification then confirms the *end-to-end* timing, not just the sum of the parts — because latencies can interact (e.g., a firmware task that only runs on a scheduler tick adds quantization that isn't visible in any single element's spec).

Third, I would be explicit about the assumptions that make the budget valid: worst-case clock accuracy, interrupt latency, task scheduling jitter, and component tolerances. Those assumptions belong in the traceability record, because if any of them changes, the budget allocation may no longer hold.

The key insight is that a distributed timing requirement is a *system* property, so it needs both a system-level verification (end-to-end measurement under worst-case conditions) and element-level verifications (each element meets its allocation). Neither alone is sufficient.

**Possible follow-ups:**
- How would you handle the case where the end-to-end test passes but one element is over its allocation, compensated by another element being under?
- What would you do if the firmware latency is highly variable depending on what else the scheduler is doing at the moment of the fault?

## Q2: How would you approach establishing traceability when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls were added at different times by different teams?

**Answer:** Redundant controls are one of the trickier traceability cases because the risk analysis credits *both* controls, which means the risk reduction claim depends on the controls being genuinely independent — and independence is a property that no single control's documentation captures.

I would start by making the redundancy itself an explicit, traceable entity. Rather than tracing hazard → control A and hazard → control B as two unrelated links, I would create a traceability record that says "hazard H is mitigated by the combination of control A and control B, and the credited risk reduction depends on their independence." That record is the anchor; both controls trace to it, and it traces to the hazard.

Then I would address the independence claim directly, because that's where the real risk lies. Independence can be compromised by shared elements — a shared power rail, a shared sensor, a shared microcontroller, a shared clock, a shared firmware module. I would document the independence argument explicitly (what each control depends on, and evidence that those dependencies don't overlap) and trace it to a verification activity that actually tests the independence claim, not just each control in isolation. A common failure mode is that each control is tested alone and passes, but nobody ever tests the scenario where a single fault disables both.

For the "added at different times by different teams" aspect, I would treat that as a documentation-integration problem: the later control's requirements and verification need to be retro-linked to the same hazard entry, and the independence argument needs to be re-examined whenever either control changes. A change to control A can invalidate the independence assumption for control B, so the traceability scheme needs a mechanism to flag that.

**Possible follow-ups:**
- How would you verify independence if the two controls share a microcontroller but use different peripherals?
- If one control is later removed, how would you re-evaluate whether the remaining control still provides adequate risk reduction?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *manual* test with no automated logging — the operator toggles a signal and observes an LED — and the risk file treats it as objective evidence?

**Answer:** The concern here isn't that manual testing is inherently invalid — it's that "objective evidence" requires the result to be *recorded in a way that can be independently examined*, and "the operator saw the LED come on" often doesn't meet that bar. The question is whether the evidence is reproducible, attributable, and specific enough to demonstrate the control actually worked.

My approach would be to strengthen the test rather than reject it outright. First, I'd ask what the test is actually trying to demonstrate: that the control activates under the specified fault condition, and that it produces the specified effect. If the observable is an LED, the test procedure should specify exactly what the operator must observe (which LED, what state, for how long, under what input conditions), and the record should capture the operator's identity, the date, the unit serial number, the test setup, and the observed result. That converts an informal observation into a documented, attributable record.

Second, I'd look for ways to add instrumentation without over-engineering: a multimeter reading, a scope capture, a photo, or a log from a debug port. Even a simple measurement turns "I saw it" into a recorded value. If the control's effect is genuinely binary and the LED is the only observable, then the procedure needs to be written so the pass/fail criterion is unambiguous and the record is complete.

Third, I'd consider whether the manual test is the *only* evidence or whether it's corroborating other evidence. If the risk file relies solely on a manual observation for a safety-critical control, that's a gap worth closing with a more instrumented test or an automated one. If it's one of several verification activities, the manual test may be acceptable as long as its limitations are documented.

The principle is that "objective evidence" is about the quality of the record and the specificity of the criterion, not about whether a human was involved.

**Possible follow-ups:**
- How would you decide whether a manual test is acceptable as the *sole* evidence for a given risk control?
- What would you do if the operator's observation is inherently subjective — for example, judging whether an LED is "bright enough"?

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented redundantly — the same hazard is mitigated by two independent controls — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** This is closely related to the redundancy case, but the emphasis here is on the *organizational* dimension: two teams, two timelines, one hazard. The traceability scheme has to work across team boundaries and across time, which means it can't rely on either team's local conventions.

I would establish a single hazard-centric anchor record that both teams' controls trace to. That record lives at the system level (not in either team's document set) and states the hazard, the credited risk reduction, and the independence assumption. Each team's control then traces *up* to that anchor, and the anchor traces *down* to both controls and to the verification activities for each. This makes the redundancy visible in one place rather than split across two documents.

For the "added at different times" problem, I would treat the anchor record as a living artifact with a change history. When the second control is added, the anchor is updated to reflect the new redundancy claim, and the independence argument is re-examined. When either control changes, the anchor is flagged for review. This is important because a change to one control can invalidate the independence assumption that justifies crediting both.

I would also make sure the verification activities for the two controls are linked to each other, not just to their own requirements — because the *combination* needs to be verified, not just each control individually. A test that exercises control A alone and a test that exercises control B alone can both pass while the combination fails (e.g., if they interfere with each other, or if a single fault disables both).

Finally, I would define ownership of the anchor record explicitly. If it's nobody's job, it will drift. Typically the systems or risk management function owns it, with both teams contributing.

**Possible follow-ups:**
- How would you handle the case where the two teams use different requirement numbering schemes and different tooling?
- What would you do if the independence assumption turns out to be invalid — for example, both controls depend on the same power rail?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is the "traceability theater" problem — the links are technically present, but the *meaning* that should flow along them has been lost. The matrix passes a mechanical audit while the actual safety intent is invisible to the people implementing and testing it. I would treat this as a process and communication problem, not just a documentation problem.

First, I would not frame it as anyone's fault. The systems engineer and test engineer each did their job as defined; the gap is that the process didn't require them to engage with the risk analysis entry. Blaming individuals would make people defensive and hide the real issue.

Second, I would make the risk intent *visible* in the artifacts people actually work from. The requirement in the SRS should carry a reference to the hazard and risk control it implements, and ideally a short statement of the safety intent — not just the functional behavior. The test procedure should reference the same hazard and state what failure condition it is exercising. This way, the intent travels with the artifact rather than living only in the risk file.

Third, I would change the review process so that the risk analysis entry is actually read by the people writing the requirement and the test. A practical mechanism is to include the risk control's failure condition in the design review checklist and the test review checklist, so reviewers are prompted to ask "does this requirement/test actually address the hazard?" rather than just "do the numbers match?"

Fourth, I would run a targeted audit across the existing matrix to find other cases where the same pattern occurs — links present but intent lost — and fix them systematically rather than one at a time.

The underlying principle is that traceability is only meaningful if the *content* flows along the links, not just the identifiers. A matrix that links requirement numbers without linking intent is a compliance artifact, not a safety artifact.

**Possible follow-ups:**
- How would you measure whether the fix actually worked, rather than just assuming it did?
- What would you do if the systems engineer pushes back, arguing that adding safety intent to the SRS "clutters" it with information that belongs in the risk file?