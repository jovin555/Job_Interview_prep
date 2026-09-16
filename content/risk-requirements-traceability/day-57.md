# risk-requirements-traceability — Day 57

## Q1: How would you approach tracing a risk control measure that is implemented as a hardware watchdog timer monitoring a firmware heartbeat, when the hardware and firmware teams each document their portions in separate specifications with no cross-references?

**Answer:** The core problem is that the control is a *loop*, not a component: hardware provides the timer and reset path, firmware provides the periodic heartbeat, and the mitigation only exists if both halves behave as assumed. A traceability scheme that documents each half in isolation can show full coverage on both sides while the integrated behavior is never actually traced or verified.

My approach would be to introduce an explicit system-level "risk control element" that owns the control as a single entity, and have both the hardware and firmware specifications point *up* to it rather than to each other. Concretely:

- In the risk management file, define the control once, with its hazard, its safety intent, and its assumed failure behavior (e.g., "if the heartbeat stops, the watchdog asserts reset within a bounded time").
- Create a system-level requirement that captures the *integrated* behavior and its measurable acceptance criteria — heartbeat period, timeout window, reset behavior, and what state the system must be in after reset. This is the requirement that traces to the hazard.
- Derive two child requirements from it: one in the hardware spec (timer timeout range, reset assertion behavior, independence from the monitored firmware) and one in the firmware spec (heartbeat generation, period tolerance, what the heartbeat must *not* depend on). Each child traces to the parent system requirement, and the parent traces to the hazard and to the verification activity.
- The verification activity must exercise the *loop*, not the halves: force the heartbeat to stop and confirm the reset occurs within the specified window. Separate hardware and firmware tests can exist as supporting evidence, but they don't substitute for the integrated test.

The key discipline is that the traceability matrix should show a single unbroken path from hazard → system requirement → hardware child + firmware child → integrated verification. If the matrix only shows hazard → hardware spec and hazard → firmware spec as two independent chains, that's the gap to fix.

**Possible follow-ups:**
- How would you verify that the watchdog is genuinely independent of the firmware it monitors — for example, that it isn't clocked or reset by the same resource the firmware could corrupt?
- If the integrated test passes but the hardware and firmware child requirements have no individual verification, is that acceptable, or would you still require each half to be verified separately?

## Q2: How would you approach deciding whether a risk control measure should be traced to a design requirement, a design element, or both — and what practical difference does that distinction make in a traceability matrix?

**Answer:** The distinction matters because requirements and design elements answer different questions, and conflating them is a common source of traceability that looks complete but isn't auditable.

A *design requirement* states what the system shall do, in measurable terms, with an acceptance criterion — it's the thing you verify against. A *design element* is the physical or logical realization — a specific circuit block, a firmware module, a mechanical feature, a component choice. A risk control measure often needs both links, but for different purposes:

- The requirement link answers "what must be true for the hazard to be mitigated, and how do we know?" It's what verification traces to.
- The design element link answers "where in the design is this actually implemented, and if this element changes, what risk controls are affected?" It's what change impact analysis traces to.

The practical difference shows up in two places. First, verification: you can only verify against a requirement with a measurable criterion, so a control traced only to a design element has no objective pass/fail — it's a design description, not a verifiable control. Second, change control: if a control is traced only to a requirement, a design change that silently removes the implementation may not be caught until verification fails late; if it's traced to the design element, the change impact analysis flags it immediately.

So my default is: every risk control measure should trace to at least one design requirement (for verification) and, where the implementation is non-obvious or change-sensitive, also to the design element(s) that realize it. In the matrix I'd keep these as distinct columns or link types, because collapsing them into one "traces to" column loses the ability to run either a coverage check (every control has a verifiable requirement) or an impact check (every affected design element maps back to its controls).

**Possible follow-ups:**
- For a control implemented purely through component derating, there may be no functional requirement — how would you represent that in the matrix without inventing a requirement that doesn't really exist?
- How would you handle a case where one design element implements several risk control measures, and a change to that element affects all of them?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity's acceptance criterion is stated as "the control functions as designed" rather than as a measurable pass/fail threshold?

**Answer:** "Functions as designed" is not an acceptance criterion — it's a placeholder that makes the verification unverifiable. It fails the basic test of objective evidence: two competent engineers running the same test could reach different conclusions, and an auditor has nothing to check the result against. The traceability link exists on paper but carries no real assurance.

My approach would be to treat this as a requirements defect, not a test defect, and fix it at the source:

- Go back to the risk analysis and ask what the control is actually supposed to achieve — what failure condition it mitigates, and what observable behavior proves it worked. That gives the safety intent.
- Convert that intent into a measurable criterion: a threshold, a timing bound, a state transition, a tolerance band, or a defined output under a defined input. If the control is analog, that means specifying trip point and reset point with tolerances; if it's a state machine guard, it means specifying the exact transition that must be blocked and the conditions under which it must be allowed.
- Where the criterion genuinely can't be reduced to a single number — for example, an emergent system behavior — decompose it into a set of observable conditions that together demonstrate the behavior, each with its own pass/fail.
- Update the verification procedure to state the criterion explicitly, and re-run or re-review the test against it. If the original test can't demonstrate the criterion, that's a real gap, not a documentation fix.

The broader point I'd make in an interview: a traceability matrix that links controls to verification activities is only as strong as the acceptance criteria in those activities. Coverage counts can look perfect while every criterion is vague. So part of any traceability review should be sampling the acceptance criteria themselves, not just checking that links exist.

**Possible follow-ups:**
- How would you handle a control where the "measurable" criterion depends on a manufacturing calibration, so the pass/fail threshold varies unit to unit?
- If you find this pattern across many verification activities, would you fix them individually or introduce a standard template for acceptance criteria — and what would that template require?

## Q4: How would you approach establishing traceability for a risk control measure that is implemented as a redundant channel — for example, a primary sensor path and an independent secondary path whose agreement is checked — where the control's effectiveness depends on the independence of the two channels rather than on either channel alone?

**Answer:** This is a case where the control's safety property is a *relationship* between two elements, not a property of either element, so a traceability scheme built around individual components will miss the thing that actually matters. The matrix can show both channels fully traced and verified while the independence assumption — the whole basis of the mitigation — is never captured or tested.

I'd handle it in three layers:

- **Capture the independence claim as an explicit requirement.** The risk analysis assumes the two channels don't share a common cause of failure. That assumption is itself a requirement: no shared power rail, no shared clock, no shared sensor die, no shared firmware routine that could fail both paths together, no shared connector. Each of those becomes a verifiable sub-requirement with its own acceptance criterion (e.g., separate regulator, separate reference, separate ADC channel with independent timing).
- **Trace the agreement logic separately from the channels.** The comparison/agreement function is a third element — it decides what happens when the channels disagree. It needs its own requirement and its own verification, including the disagreement case, not just the "both agree" case.
- **Verify the failure modes, not just the happy path.** The verification must include: one channel drifting out of specification while the other stays valid; one channel failing outright; and a common-cause stress that could affect both. The last one is the hardest and is exactly what the independence requirement is meant to protect against.

In the matrix, I'd represent this as one system-level risk control with three linked requirements (channel A integrity, channel B integrity, independence) plus the agreement logic, and a verification activity that explicitly covers the disagreement and common-cause scenarios. The independence requirement is the one most likely to be forgotten, so I'd make it a named, separately traced item rather than an implicit assumption buried in a design note.

**Possible follow-ups:**
- How would you verify independence without being able to physically inject a common-cause fault into both channels simultaneously?
- If the two channels share a microcontroller but use separate sensor front-ends, does that still count as independent — and how would you document the residual common-cause risk?

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has built a traceability matrix that links every risk control measure to a verification activity, and the matrix is complete and passes audit. However, a test engineer privately tells you that several of the linked tests were written by copying a similar test from a previous project and adjusting the labels, and that nobody has confirmed the tests actually exercise the failure conditions in this project's risk analysis. The systems engineer argues the matrix is compliant and the tests pass, so there's no problem. How would you handle this?

**Answer:** The systems engineer is right that the matrix is compliant and the tests pass, and wrong that there's no problem. What's been described is traceability that satisfies the *form* of the requirement — every control has a linked verification — while defeating its *purpose*, which is to demonstrate that each control actually mitigates its hazard under the conditions the risk analysis identified. A copied test with adjusted labels is a link that exists on paper and provides no assurance in practice. This is exactly the kind of gap that passes an audit and fails in the field, so I'd treat it as a real finding, not a documentation nit.

How I'd handle it, roughly in order:

- **Don't start by accusing anyone.** The test engineer came forward privately, which suggests they're uncomfortable but not trying to cause trouble. I'd thank them, confirm I understand the specific tests involved, and avoid putting them in an exposed position before I've verified the concern myself.
- **Verify the concern directly.** I'd pull the risk analysis for the affected controls, read the failure conditions each control is meant to mitigate, and read the linked test procedures. If the tests don't stress those conditions, that's objective and I can act on it without relying on the private conversation. If some do and some don't, I need the real scope before deciding how big this is.
- **Separate the two issues.** One is the specific tests that don't exercise the failure conditions — those need to be rewritten or replaced, and the affected controls re-verified. The other is the *process* that allowed copied tests to be linked without review — that's the systemic issue and the one more likely to recur.
- **Bring the systems engineer in as a partner, not a defendant.** The matrix being "complete" is a real achievement and I'd acknowledge it. The conversation is about what the links are supposed to prove, not about whether the matrix is wrong. Framing it as "the matrix is doing its job; the tests underneath it aren't yet" keeps it constructive.
- **Fix the process, not just the tests.** The root cause is usually that verification activities are linked to controls by whoever builds the matrix, without a check that the test actually exercises the failure condition. A lightweight review step — the person who wrote the risk analysis signs off that the linked test stresses the identified failure mode — catches this class of problem before it reaches audit.
- **Escalate appropriately if needed.** If the scope turns out to be large, or if there's pressure to leave it alone because the audit passed, that's a quality and regulatory issue that needs to go up the chain. I wouldn't sit on it.

The thing I'd want to avoid is treating "the audit passed" as the goal. The goal is that the controls work. A matrix that passes audit while the tests underneath it don't exercise the failure conditions is a liability, and the earlier it's caught the cheaper it is to fix.

**Possible follow-ups:**
- How would you decide whether the affected controls need full re-verification or whether a targeted test of the specific failure condition is sufficient?
- If the systems engineer pushes back and argues that re-opening the tests will delay the project and that the audit already passed, how would you handle that disagreement?