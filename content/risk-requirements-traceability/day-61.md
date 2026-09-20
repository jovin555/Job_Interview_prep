# risk-requirements-traceability — Day 61

## Q1: How would you approach deciding whether a risk control measure should be traced to a design requirement, a design element, or both — and what practical difference does that distinction make in a traceability matrix?

**Answer:** The distinction comes down to *what kind of thing you're asserting* and *what you can verify against it*. A design requirement is a statement of intent — "the system shall limit motor current to X under fault conditions." A design element is the concrete realization — a specific comparator stage, a firmware current-limit routine, a fuse. A risk control measure is the *reason* the requirement exists: it's the mitigation that reduces a hazard's risk to an acceptable level.

In practice, I'd trace a risk control measure to a design requirement when the control is expressed as behavior the system must exhibit and I need a measurable acceptance criterion to verify against. I'd trace it to a design element when the control is realized structurally — a creepage distance, a component derating, a mechanical interlock — where there's no meaningful "behavioral requirement" to write, but there is a physical artifact whose properties I can inspect or analyze. Many controls need both: the requirement captures *what must be true*, the design element captures *where it lives*, and the verification activity attaches to whichever of the two gives the most objective evidence.

The practical difference in the matrix is auditability. If a control is traced only to a design element, an auditor can see it exists but can't easily see what it's supposed to *do* or how you proved it does it. If it's traced only to a requirement, you can see the intent but not the physical realization, which makes impact analysis painful — when someone changes that comparator, you can't quickly see which hazards are affected. Tracing to both gives you a bidirectional path: hazard → risk control → requirement → design element → verification, and back. That's what makes the matrix useful during change control, not just during the initial audit.

**Possible follow-ups:**
- If a design element implements several requirements, how do you avoid the matrix becoming a many-to-many tangle that nobody can read?
- When a design element is changed but the requirement stays the same, what does your traceability process require you to re-examine?

## Q2: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity's acceptance criterion is stated as "the control functions as designed" rather than as a measurable pass/fail threshold?

**Answer:** "Functions as designed" is not an acceptance criterion — it's a placeholder that defers the real question. The first thing I'd do is go back to the risk analysis and ask: what does this control actually need to achieve to reduce the risk to an acceptable level? That gives you the *intent*. Then I'd ask what observable, measurable behavior demonstrates that intent. The acceptance criterion should be a threshold, a range, a timing bound, or a state transition — something a tester can pass or fail without exercising judgment.

For example, if the control is "the system shall disable the motor output on over-temperature," the criterion isn't "the motor disables." It's "the motor output is disabled within N milliseconds of the temperature sensor crossing the trip threshold, and remains disabled until the temperature falls below the reset threshold." That's testable, and it also forces you to think about the failure condition — the thing the control is meant to mitigate — rather than just the happy path.

If the requirement genuinely can't be reduced to a numeric threshold — say, a firmware state machine guard — then the criterion should at least be a defined sequence of inputs and expected state transitions, with the pass condition being that the system never enters the forbidden state. That's still objective. The key is that "as designed" pushes the judgment into the tester's head, where it can't be audited or reproduced. I'd treat any acceptance criterion phrased that way as a gap to close before the verification is considered complete.

**Possible follow-ups:**
- What if the design team argues that the control's behavior is too complex to reduce to a single threshold — how would you structure the criterion then?
- How would you handle a situation where the acceptance criterion is measurable but the test procedure doesn't actually measure it?

## Q3: How would you approach establishing traceability for a risk control measure that is implemented as a redundant channel — for example, a primary sensor path and an independent secondary path whose agreement is checked — where the control's effectiveness depends on the *independence* of the two channels rather than on either channel alone?

**Answer:** This is a case where the risk control isn't the primary channel or the secondary channel — it's the *disagreement detection* plus the *independence* that makes the detection meaningful. So the traceability has to capture three things: the comparison logic (the control itself), the two channels (the design elements), and the independence argument (the rationale that the channels can't fail the same way).

I'd start by writing a requirement for the control at the system level: "the system shall detect disagreement between the primary and secondary sensor paths and transition to a safe state within a bounded time." That's the behavioral requirement, and it's what the verification test attaches to. Then I'd trace that requirement to both channel design elements, and I'd add a separate traceability link — or a dedicated section in the risk management file — for the independence claim. Independence isn't a requirement you can test directly; it's an argument supported by evidence: separate power domains, separate signal paths, different sensor technologies, different firmware tasks, no shared failure modes. That evidence might be analysis, inspection, or a combination, and it needs its own verification activity even though it's not a pass/fail test.

The trap here is tracing the control only to the comparison logic and forgetting the independence. If both channels share a regulator and that regulator fails, the "redundancy" is gone and the control doesn't mitigate the hazard at all. So the matrix has to make the independence visible, and the verification plan has to include something that demonstrates it — even if that something is a design review with explicit criteria about shared failure modes, rather than a bench test.

**Possible follow-ups:**
- How would you verify independence if the two channels use the same sensor part number but different physical instances?
- If a common-cause failure is identified after the fact, how does that flow back through your traceability to affect the risk control's validity?

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity's test procedure was written against an earlier revision of the requirement, so the test still passes but no longer exercises the current acceptance criteria?

**Answer:** This is a configuration-control failure as much as a traceability failure. The link exists, the test passes, and the matrix looks complete — but the evidence no longer supports the requirement it's linked to. The first step is to confirm the mismatch: pull the requirement's current revision, pull the test procedure's revision, and compare the acceptance criteria. If they've diverged, the test result is stale and can't be used as verification evidence for the current requirement.

The fix is to re-baseline the test procedure against the current requirement, re-run it, and re-link the evidence to the correct revision. But the more important question is *how this happened* — because if it happened once, it's probably happened elsewhere. I'd want to know whether the requirement changed after the test was written and nobody propagated the change, or whether the test was written against a draft and never updated. Either way, the root cause is usually that requirements and test procedures aren't being versioned together, or that there's no trigger that flags "this requirement changed, here are the tests that need review."

The systemic fix is to make the traceability matrix revision-aware — each link should point to a specific revision of the requirement and a specific revision of the test, not just to the requirement ID. Then a requirement change automatically surfaces the affected tests as "needs review," and you can't accidentally rely on stale evidence. I'd also add a check in the verification review process: before a test is accepted as evidence, confirm the test procedure revision is current against the requirement revision.

**Possible follow-ups:**
- How would you audit the rest of the matrix to find other stale links without re-running every test?
- If the requirement changed in a way that makes the old test still partially valid, how would you decide whether to re-run or supplement?

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has built a traceability matrix that links every risk control measure to a verification activity, and the matrix is complete and passes audit. However, a test engineer privately tells you that several of the linked tests were written by copying a similar test from a previous project and adjusting the labels, and that nobody has confirmed the tests actually exercise the failure conditions in this project's risk analysis. The systems engineer argues the matrix is compliant and the tests pass, so there's no problem. How would you handle this?

**Answer:** The matrix being complete and the tests passing is exactly the problem — it's a false sense of assurance. The purpose of traceability isn't to produce a document that passes audit; it's to give you confidence that the risks you identified are actually mitigated. If the tests don't exercise the failure conditions, the matrix is documenting a link that doesn't exist in reality, and that's worse than an obvious gap because it's hidden.

I'd start by taking the test engineer's concern seriously and quietly — not as an accusation, but as a technical question. I'd pick a few of the flagged tests and walk through them against the risk analysis: what failure condition is this control supposed to mitigate, and does this test actually create that condition? If the answer is no, that's objective evidence, not opinion. I'd document the specific mismatches and bring them to the systems engineer with the evidence rather than the claim.

The conversation with the systems engineer needs to reframe what "compliant" means. A matrix that links a control to a test that doesn't stress the failure condition isn't compliant in any meaningful sense — it's a documentation artifact that would fail a technical review, even if it passes a checklist audit. I'd propose a targeted re-review: for each risk control, confirm the test actually reproduces the failure condition the control mitigates. That's a bounded effort, not a full re-test, and it either confirms the concern or resolves it.

The harder part is the cultural one. The test engineer came to me privately, which means they didn't feel safe raising it openly — that's a signal worth paying attention to. I'd want to make it clear that raising this kind of concern is valued, and that "the matrix passes audit" is never a sufficient answer to "does this test actually prove the control works." If the team learns that copying tests and relabeling them is acceptable as long as the matrix looks complete, the traceability process has failed regardless of what the documents say.

**Possible follow-ups:**
- How would you handle it if the systems engineer's manager pushes back and says re-reviewing the tests will blow the schedule?
- What would you change in the process to prevent "copy and relabel" from happening in the first place?