# risk-requirements-traceability — Day 55

## Q1: How would you approach tracing a risk control measure that is implemented as a mechanical interlock — for example, a physical shield that prevents a connector from being mated while power is applied — where the "verification" is partly dimensional inspection and partly functional testing?

**Answer:** The key insight is that a mechanical interlock is a *composite* control with two distinct failure modes that need separate verification: (1) the geometry is wrong, so the shield physically doesn't block the connector, and (2) the geometry is right but the interlock can be defeated in practice (e.g., a user can apply force and bypass it, or the shield can be removed with a common tool). These map to different verification methods.

I would decompose the single risk control measure into two derived requirements in the SRS: a dimensional/geometric requirement (e.g., "the shield shall prevent mating of connector J1 while the power switch is in the ON position") and a functional/robustness requirement (e.g., "the interlock shall withstand a specified insertion force without allowing contact"). The dimensional requirement is verified by inspection — but inspection must be against a *measurable* criterion (a drawing with tolerances, a go/no-go gauge), not a subjective "looks correct." The functional requirement is verified by test — applying the specified force and confirming no electrical contact occurs.

In the traceability matrix, I'd link the risk control measure to *both* derived requirements, and each derived requirement to its own verification activity. This makes the composite nature explicit and prevents the common failure where someone verifies only the dimensional aspect and assumes the functional aspect is covered. I'd also capture the tooling assumption: if the interlock is only effective when a specific fastener is used, that becomes a manufacturing/process control that needs its own traceability link, because the control's effectiveness depends on it.

**Possible follow-ups:**
- If the dimensional inspection is done on a sample basis rather than every unit, how would you justify that in the risk management file?
- How would you trace the manufacturing process control (e.g., torque specification for the shield fastener) back to the risk control measure?

## Q2: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity's acceptance criterion is stated as "the control functions as designed" rather than as a measurable pass/fail threshold?

**Answer:** "Functions as designed" is not an acceptance criterion — it's a placeholder that defers the real question. The problem is that it makes the verification activity unfalsifiable: any observed behavior can be argued to match "the design," and there's no objective evidence that the control actually mitigates the hazard under the conditions the risk analysis specifies.

My approach would be to work backward from the risk analysis. The risk control measure exists to reduce a specific hazard under specific conditions. So the acceptance criterion must be derived from: (a) the hazard being mitigated, (b) the failure condition the control is meant to detect or prevent, and (c) the boundary conditions (worst-case supply, temperature, timing, sensor drift) under which the control must still work. From those, I'd write a criterion with a measurable threshold and a defined test condition — for example, "with the input held at X, the output shall transition to the safe state within T milliseconds, across the specified supply and temperature range."

I'd also distinguish between the *pass/fail threshold* and the *test method*. The threshold is what the control must achieve; the method is how you stress it. Both need to be explicit. If the team genuinely doesn't know the right threshold yet, that's a signal the risk analysis is incomplete — the control's required performance hasn't been derived — and the fix is to go back to the risk analysis, not to paper over it with vague language.

In practice, I'd flag every "functions as designed" criterion in the traceability matrix as a gap, because it breaks the chain from hazard to objective evidence. The matrix can be structurally complete (every control has a linked test) while being substantively empty (the test proves nothing). That distinction is exactly what a good audit or design review should catch.

**Possible follow-ups:**
- How would you handle a case where the risk analysis itself doesn't specify a quantitative threshold for the control's performance?
- If a test engineer argues that a qualitative criterion is appropriate for a control whose failure mode is inherently subjective (e.g., a user-interface warning), how would you make it objective?

## Q3: How would you approach establishing traceability for a risk control measure that is implemented as a redundant channel — for example, a primary sensor path and an independent secondary path whose agreement is checked — where the control's effectiveness depends on the independence of the two channels rather than on either channel alone?

**Answer:** This is a case where the control's *effectiveness* is a property of the relationship between two elements, not of either element individually. That means the traceability scheme has to capture three things: the two channels, the comparison/agreement logic, and — critically — the *independence* claim, which is the actual risk control.

The independence claim is the part most often lost. If both channels share a power rail, a reference voltage, a clock, or a microcontroller, they are not truly independent, and a common-cause failure can defeat both simultaneously. So the risk control measure should be decomposed into derived requirements that make the independence explicit: separate power domains, separate references, separate signal paths, no shared firmware that could fail both channels at once. Each of those derived requirements needs its own verification — and some of them (e.g., "the two channels do not share a ground return") are verified by inspection or analysis of the schematic and layout, not by a functional test.

The functional test then verifies the *agreement logic*: inject a fault into one channel and confirm the system detects the disagreement and takes the safe action. But that test alone doesn't prove independence — it only proves the comparison works. So the traceability matrix needs both: the functional test for the comparison logic, and the design-analysis/inspection activities for the independence requirements.

I'd also add a common-cause failure analysis (often folded into the DFMEA) that explicitly asks "what single failure could defeat both channels?" and traces any resulting design changes back to the risk control. Without that, the redundancy looks good on paper but may not actually reduce risk.

**Possible follow-ups:**
- How would you verify that two channels are truly independent when they share a single microcontroller but use separate ADC inputs?
- If a common-cause failure analysis identifies a shared component that can't be eliminated, how would you document the residual risk?

## Q4: How would you approach deciding whether a risk control measure should be traced to a design requirement, a design element, or both — and what practical difference does that distinction make in a traceability matrix?

**Answer:** The distinction matters because requirements and design elements answer different questions, and conflating them creates gaps that are hard to see.

A *design requirement* states what the system must do or achieve — it's a statement of intent with a measurable criterion. A *design element* is the specific implementation that satisfies the requirement — a circuit block, a firmware module, a mechanical feature. The risk control measure is the *why*: the hazard it mitigates.

In a well-formed traceability matrix, the chain runs: hazard → risk control measure → design requirement(s) → design element(s) → verification activity. Each link answers a different audit question. If you trace only to design elements, you can show that something was built, but not that it was *required* to behave a certain way — so you can't tell whether the element actually satisfies the control's intent. If you trace only to requirements, you can show intent, but not that any specific implementation exists to fulfill it.

The practical difference shows up in two scenarios. First, when a design element changes (e.g., a component is substituted), you need to know which requirements it was satisfying so you can re-verify. Second, when a requirement changes, you need to know which design elements are affected. Tracing to both makes both impact analyses possible.

For risk controls specifically, I'd insist on tracing to the requirement *and* the design element, because the risk management file needs to demonstrate that the control is both specified and implemented. A control that exists only as a design element (someone built a comparator, but no requirement says it must trip at a specific threshold) is a latent gap — it works today but has no defined behavior to verify against.

**Possible follow-ups:**
- How would you handle a case where a single design element satisfies multiple risk control requirements?
- If a design element is shared across two product variants but only one variant has the associated risk control requirement, how would you trace that?

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has built a traceability matrix that links every risk control measure to a verification activity, and the matrix is complete and passes audit. However, a test engineer privately tells you that several of the linked tests were written by copying a similar test from a previous project and adjusting the labels, and that nobody has confirmed the tests actually exercise the failure conditions in this project's risk analysis. The systems engineer argues the matrix is compliant and the tests pass, so there's no problem. How would you handle this?

**Answer:** The systems engineer is technically correct that the matrix is compliant, and that's exactly the problem — the matrix is measuring the wrong thing. A traceability matrix proves that links *exist*; it doesn't prove the links are *meaningful*. If the tests were copied and relabeled without confirming they exercise this project's failure conditions, then the matrix is structurally complete but substantively hollow, and the audit would pass while the actual risk controls remain unverified.

My first step would be to treat the test engineer's disclosure as a serious signal, not a rumor to be managed. I'd ask them to identify specifically which tests they're concerned about and why — what failure condition does the risk analysis specify, and what does the test actually do? That gives me concrete examples rather than a general allegation.

Then I'd bring the systems engineer and the test engineer together, not to adjudicate blame but to walk through a couple of the flagged tests against the risk analysis. The goal is to make the gap visible to everyone: here is the failure condition the control is meant to mitigate, here is what the test actually does, and here is the difference. Once the gap is concrete, the "the matrix is compliant" argument tends to lose its force, because the question shifts from "is the matrix complete?" to "does the matrix mean anything?"

For the fix, I'd propose a targeted review: for each risk control measure, confirm that the linked verification activity actually stresses the failure condition, not just the nominal function. Where it doesn't, either rewrite the test or add a new one. I'd also want to understand *why* the copy-and-relabel happened — usually it's schedule pressure or a lack of clarity about what the test was supposed to prove — because if I don't address the root cause, the same thing will happen on the next project.

Finally, I'd be careful not to frame this as a compliance failure. The matrix did its job — it surfaced a link. The issue is that the link was never validated. That's a process gap, and the fix is to add a validation step to the traceability workflow: not just "does every control have a linked test?" but "has someone confirmed the test exercises the failure condition?" That's a review activity, and it belongs in the design review process, not just in the matrix.

**Possible follow-ups:**
- How would you handle the situation if the systems engineer continues to insist the matrix is sufficient and refuses to support the review?
- What would you change in the traceability process to prevent copied-and-relabeled tests from passing review in the future?