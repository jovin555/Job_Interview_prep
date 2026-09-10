# risk-requirements-traceability — Day 51

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a mechanical interlock (e.g., a physical shield that prevents a connector from being mated while power is applied), where the "verification" is partly dimensional inspection and partly functional testing?

**Answer:** Mechanical risk controls are a good test of whether a traceability scheme is genuinely method-agnostic or whether it has quietly been built around electrical/firmware testing. The key is to treat the control as a single risk control measure with multiple verification activities, each tied to a distinct aspect of the control's effectiveness, rather than trying to force one test to cover everything.

I'd start by decomposing the control into its verifiable claims. A mechanical interlock typically asserts at least two things: (1) a geometric claim — the shield physically blocks mating in the energized state, which is a dimensional/assembly property; and (2) a functional claim — the interlock prevents the hazardous condition (e.g., live mating) under realistic use, including foreseeable misuse like forcing the connector. The geometric claim is naturally verified by inspection or dimensional measurement against the drawing; the functional claim is verified by test, ideally including a deliberate attempt to defeat the interlock.

In the traceability matrix, I'd link the single risk control measure to both verification activities, with each row stating what aspect of the control it verifies and the acceptance criterion. The risk management file references the control; the matrix shows the control is covered by inspection *and* test; the inspection record and test report are the objective evidence. The important discipline is that the inspection must have a defined acceptance criterion (a tolerance, a drawing callout, a go/no-go gauge) — "someone looked at it" is not a verification activity. If the inspection criterion is vague, that's the gap to fix, not the choice of method.

I'd also make sure the functional test is written to stress the failure condition, not just confirm the interlock exists. A test that mates the connector with power off and confirms it seats properly proves nothing about the hazard; the test needs to attempt the hazardous action and confirm the interlock prevents it.

**Possible follow-ups:**
- If the mechanical interlock is verified by dimensional inspection on a sample basis rather than every unit, how would you justify that in the risk management file?
- How would you handle a situation where the mechanical interlock can be defeated by a determined user, and the risk analysis assumed it could not?

## Q2: How would you approach deciding whether a risk control measure should be traced to a design requirement, a design element, or both — and what practical difference does that distinction make in a traceability matrix?

**Answer:** This distinction matters because it determines what a gap in the matrix actually means and who owns closing it. A design requirement is a statement of what the system shall do or be; a design element is the concrete artifact — a circuit block, a firmware module, a mechanical part, a parameter value — that realizes it. A risk control measure can be traced to one, the other, or both, and the right answer depends on whether the control is expressed as a behavioral obligation or as a physical/structural property.

For a behavioral control — "the system shall disable the motor output within a specified time of detecting a fault" — the natural trace is risk control → design requirement → design element (the firmware module implementing the timeout) → verification. The requirement is the traceable unit because it's testable and it carries the acceptance criterion.

For a structural control — a creepage distance, a component derating margin, a shielding geometry — there may be no meaningful "requirement" in the behavioral sense; the control *is* the design element plus its constraint. Here the trace is risk control → design element (with the constraint documented as a design rule or a drawing callout) → verification by inspection or analysis. Forcing a behavioral requirement onto a structural control produces a requirement that says "the board shall have adequate creepage," which is untestable and adds noise.

The practical difference in the matrix: for behavioral controls, a missing requirement link is a real gap — the control has no testable expression. For structural controls, a missing requirement link may be fine, but a missing *design element* link or a missing *acceptance criterion* is the gap. So the matrix should record the link type, not just the existence of a link, so that reviewers can tell whether a gap is meaningful. I'd also make sure the risk management file states which type each control is, so the traceability expectation is set at the point the control is defined rather than argued about later.

**Possible follow-ups:**
- How would you handle a control that is partly behavioral and partly structural — for example, a firmware watchdog that depends on a hardware clock source with a specified tolerance?
- If a structural control has no requirement, how do you ensure it doesn't silently disappear when the design is revised?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity's acceptance criterion is stated as "the control functions as designed" rather than as a measurable pass/fail threshold?

**Answer:** This is one of the most common and most damaging traceability defects, because the matrix looks complete — every control has a verification link — but the link carries no objective evidence. "Functions as designed" is not an acceptance criterion; it's a restatement of the requirement and it delegates the actual judgment to whoever runs the test, which means the result isn't reproducible and isn't auditable.

My approach is to treat it as a requirements-quality problem rather than a traceability problem. The fix is to go back to the risk analysis and ask: what observable, measurable condition demonstrates that this control mitigates the hazard? That question usually yields a threshold — a trip point and tolerance, a maximum response time, a minimum margin, a pass/fail state transition. If the risk analysis itself doesn't support deriving a threshold, that's the deeper issue: the control was specified too vaguely to be verifiable, and the risk management file needs to be tightened before the test can be.

Once the threshold exists, I'd update the verification activity to state the criterion explicitly, the test method, the conditions under which it's exercised (including the fault condition the control is meant to mitigate), and the evidence to be recorded. Then the matrix link becomes meaningful: control → requirement (with the threshold) → test (with the same threshold) → evidence.

I'd also check whether the vague criterion is a symptom of a broader pattern. If several verification activities say "as designed," it usually means the requirements were written at too high a level and the test authors had nothing concrete to test against. In that case the fix is upstream — tighten the SRS acceptance criteria — rather than patching each test individually.

**Possible follow-ups:**
- How would you handle a control where the "measurable" criterion is inherently statistical — for example, a control that must work with high reliability but cannot be tested to failure on every unit?
- If the risk analysis genuinely cannot yield a threshold, what does that tell you about the control's suitability?

## Q4: (Behavioral) Imagine you're leading a project where the risk management team insists that every risk control measure must be traced to a *single* verification activity, arguing that multiple links per control make the matrix unreadable and hard to audit. The test lead argues that several controls genuinely require multiple verification activities — for example, a control verified partly by analysis and partly by test. How would you resolve this disagreement?

**Answer:** I'd start by separating the two concerns that are being conflated: matrix readability and traceability completeness. The risk management team's concern is legitimate — a matrix where every control fans out to five links with no structure is hard to audit and easy to misread. But the solution to readability is structure, not artificially collapsing links. Forcing one verification activity per control would either drop real verification coverage or force unrelated checks into a single test procedure, which is worse for auditability, not better.

I'd propose a matrix structure that keeps the one-to-many relationship but makes it legible: group the verification activities under each control, label each with its method (test, analysis, inspection, review) and the specific aspect of the control it verifies, and add a coverage column that shows whether the control's full claim is covered. That way an auditor can see at a glance that a control has, say, an analysis link for the timing margin and a test link for the fault response, and that together they cover the control. The matrix stays readable because the fan-out is organized, not because it's been suppressed.

I'd also address the underlying worry directly: if the risk management team is concerned that multiple links make it hard to tell whether a control is *fully* verified, the answer is an explicit coverage statement per control — "verified by analysis (timing margin) and test (fault response); no residual unverified aspects" — rather than a single link. That gives them the auditability they want without losing coverage.

If after that there's still disagreement, I'd escalate to the quality/regulatory function, because the question of whether a control can be verified by a single activity is ultimately a regulatory-evidence question, not a project-preference question. But I'd expect the structured-matrix proposal to resolve it, because it gives both sides what they actually need.

**Possible follow-ups:**
- How would you handle a control where the multiple verification activities are owned by different teams and there's no single person accountable for the control's overall coverage?
- If the matrix tooling can't represent one-to-many links cleanly, how would you work around that without losing traceability?

## Q5: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system includes a safety-related parameter that is set at manufacturing time (e.g., a calibration value or a configuration constant) and the parameter value itself is the control?

**Answer:** This is a case where the control isn't a behavior or a structure but a *value*, and the traceability scheme has to capture the value's provenance, its acceptable range, and the evidence that each unit carries a value in range. The failure mode is subtle: the design is correct, the firmware is correct, but a unit ships with a parameter outside the range the risk analysis assumed, and the control is silently ineffective.

I'd structure the trace to treat the parameter as a design element with three linked aspects. First, the risk analysis defines the control and the acceptable range — this is the source of truth for what "in range" means and why. Second, a requirement (or a design constraint, depending on how behavioral it is) states that the parameter shall be set within that range and how it is set — the calibration procedure, the configuration mechanism, the storage location. Third, a verification activity confirms both that the mechanism works (the parameter can be set and is retained) and that production units actually carry in-range values — which is typically a manufacturing test with a defined sampling or 100% inspection strategy, plus a design verification test on representative units.

The traceability matrix then shows: risk control → parameter range (from risk analysis) → requirement/constraint (setting mechanism and range) → design element (the parameter storage and the code that consumes it) → verification (design verification test) → production control (manufacturing test with acceptance criterion). The production control link is the one that's often missing in traceability schemes built only around design verification, and it's exactly the link that matters for a manufacturing-set parameter.

I'd also make sure the parameter's range is treated as a controlled item: if the risk analysis range and the manufacturing test limit ever diverge, that's a traceability break that needs to be caught. And I'd check whether the parameter can be changed after manufacturing — if it can, the trace needs to extend to whatever controls that change, because the control's effectiveness depends on the value staying in range over the product's life.

**Possible follow-ups:**
- How would you handle a parameter whose acceptable range is derived from a calculation rather than from direct testing, and how would that affect the verification link?
- If the parameter is stored in non-volatile memory that could be corrupted in the field, how would you trace the control's continued effectiveness after shipment?