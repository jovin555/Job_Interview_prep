# risk-requirements-traceability — Day 79

## Q1: How would you approach tracing a risk control measure that is implemented as a *user-facing procedural control* — for example, a label instructing the operator to verify a connection before energizing — where the "implementation" is a printed instruction and the "verification" is a usability study rather than a bench test?

**Answer:** The key insight is that a procedural control is still a risk control, and ISO 14971 treats it as the weakest form of control because its effectiveness depends on human behavior rather than deterministic system behavior. So the traceability chain has to be built differently from a hardware or firmware control, but it still has to be complete.

I would start by making the control explicit in the risk management file as a distinct risk control measure with its own identifier, and stating clearly that it is a *procedural* control — not an inherent-safety or protective-measure control. That classification matters because it drives what counts as acceptable verification evidence. From there, the traceability chain runs: hazard → risk control measure (procedural) → the artifact that implements it (the label, the IFU section, the training material) → the verification activity (usability study, human factors validation, or a comprehension test with representative users) → the acceptance criterion (e.g., a defined proportion of representative users correctly perform the step without prompting).

The important discipline is that the "design element" here is a document or label, not a circuit, so the traceability matrix needs a column or link type that captures document-controlled artifacts. If the traceability tool only supports requirement-to-test links, procedural controls tend to fall through the cracks. I would also make sure the usability study protocol explicitly references the risk control ID and the failure condition it mitigates — otherwise you get a study that exercises the label but never demonstrates that the label prevents the hazardous situation.

One more point: because procedural controls are fragile, I would want the risk file to show that the residual risk after the procedural control is still acceptable, and that the control isn't being credited more than it deserves. That's a risk-management judgment, but it directly affects how much verification rigor the traceability link needs to carry.

**Possible follow-ups:**
- If the usability study shows that a meaningful fraction of users skip the step, how would you decide whether to strengthen the label, add a hardware interlock, or accept the residual risk?
- How would you trace a procedural control that is delivered through training rather than a label — where the "implementation" is a training module and the "verification" is a competency assessment?

## Q2: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *supplier-provided test report* for a purchased component (e.g., a certified relay or an off-the-shelf power module), rather than a test your own team performed?

**Answer:** Supplier test reports can be legitimate verification evidence, but only if you can demonstrate that the report actually covers the failure condition your risk analysis is relying on, under conditions representative of your application. The traceability link alone is not enough — the link has to be *substantiated*.

My approach would be to treat the supplier report as a candidate verification artifact and then run it through a gap check. First, what exactly did the supplier test? A relay datasheet might report contact endurance at a rated load, but if your risk control depends on the relay opening reliably under a specific fault current and a specific ambient temperature, the supplier's nominal test may not cover that. Second, what is the supplier's qualification basis — is it a recognized third-party certification, an internal test to a published standard, or a one-off characterization? Third, is the component used within the supplier's specified operating envelope, or are you relying on margin beyond it?

If the report covers the failure condition and the application conditions, I would document the link with a clear rationale: the report ID, the specific test conditions, and a statement of why those conditions bound your application. If it doesn't cover the condition, the options are to supplement with your own test, to add analysis that bounds the gap, or to reclassify the control as not fully verified and address the residual risk. What I would not do is leave a bare link from the risk control to a supplier report with no rationale, because that is exactly the kind of link that passes an audit but fails a technical review.

There's also a supply-chain dimension: if the supplier changes the component or the test basis, the verification evidence can silently become invalid. So I would want the traceability to reference a specific supplier document revision, and to have a change-control trigger that re-opens the verification if that revision changes.

**Possible follow-ups:**
- How would you handle a supplier report that is marked proprietary and cannot be included in your DHF, but is the only evidence you have?
- If the supplier's test was performed on a different variant of the component than the one you are using, what would you need to establish before accepting the report as verification?

## Q3: How would you approach tracing a risk control measure whose effectiveness depends on a *sequence* of events rather than a single action — for example, a control that requires the system to detect a fault, log it, notify the user, and then enter a safe state, where each step is owned by a different subsystem?

**Answer:** This is a case where the risk control is really a *composite* control, and the traceability has to reflect that structure rather than pretending it is a single atomic measure. If you trace it as one link from hazard to one verification activity, you lose the ability to see which step is verified by what, and you lose the ability to detect when one step's requirement changes without the others.

I would decompose the composite control into its constituent steps in the risk management file, each with its own sub-identifier, while keeping a parent identifier that represents the overall control. The parent is what the risk analysis credits; the children are what the requirements and verification activities attach to. That gives you a two-level traceability structure: hazard → parent control → child steps → requirements → verification activities. Each child step gets its own measurable acceptance criterion — detection latency, log persistence, notification behavior, safe-state entry time — and its own verification activity owned by the relevant subsystem team.

The critical part is verifying the *sequence*, not just the individual steps. Each step can pass in isolation while the sequence fails — for example, the fault is detected and logged, but the notification is sent before the safe state is entered, or the safe state is entered but the log write is lost because power was removed first. So there needs to be at least one integration-level verification activity that exercises the full sequence end-to-end and confirms the ordering and the timing budget across steps. That integration test is the verification of the parent control; the per-step tests are the verification of the children.

I would also make sure the interface between steps is captured — if step 2 hands off to step 3 via a message or a shared flag, that interface is where sequence failures hide, and it should be documented in an ICD or equivalent so the traceability has something concrete to point at.

**Possible follow-ups:**
- If the integration test for the sequence is expensive to run repeatedly, how would you decide which regression tests are sufficient to protect the sequence during later design changes?
- How would you handle a composite control where one step is implemented by a third-party subsystem you don't control?

## Q4: How would you approach establishing traceability between risk control measures and requirements when the same risk control measure is implemented differently across multiple product variants or hardware revisions?

**Answer:** The trap here is to create a separate traceability matrix per variant and then lose the ability to see that they are all mitigating the same hazard. The better structure is to anchor the traceability on the *hazard and the risk control measure* as the stable elements, and treat the variant-specific implementations as branches beneath that anchor.

Concretely, I would keep a single risk management file where the risk control measure has one identifier and one statement of intent — what hazardous situation it mitigates and what the required effect is. Then, for each variant, I would create variant-specific requirements that implement that intent, each with its own requirement ID and its own verification activity. The traceability matrix then shows: hazard → risk control measure (common) → variant A requirement → variant A verification, and hazard → risk control measure (common) → variant B requirement → variant B verification. The common node is what lets you audit coverage across the product family; the variant nodes are what let you verify each implementation.

The discipline that makes this work is that the risk control measure's statement of intent has to be written at a level that is genuinely common — if variant A uses a hardware watchdog and variant B uses a firmware watchdog, the common statement is something like "the system shall detect a loss of firmware liveness and force a safe state within a bounded time," not "a hardware watchdog shall reset the MCU." If the common statement is written at the implementation level, it will only fit one variant and the structure collapses.

I would also want a variant-comparison view — a report that shows, for each risk control measure, which variants implement it and whether each variant's verification is complete. That view is what catches the case where a new variant is added and one control is implemented but never verified, because the common node exists but the new branch is empty.

**Possible follow-ups:**
- If a new variant is added that implements a control in a way that is materially different from any existing variant, how would you decide whether the existing verification evidence can be leveraged?
- How would you handle a variant where a risk control measure is intentionally *not* implemented because the hazard doesn't exist in that configuration — how do you document that absence without leaving a gap in the matrix?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is the classic failure mode of traceability done as a documentation exercise rather than as a communication tool. The links are technically present, so an audit might pass, but the control is not actually understood by the people implementing and verifying it — which means the verification may be testing the letter of the requirement while missing the failure condition the control exists to mitigate.

My first move would be to treat this as a process problem, not a blame problem. The systems engineer and test engineer didn't read the risk analysis because nothing in their workflow required them to, and the documents they were handed probably didn't make the safety intent visible. So I would start by making the intent visible: for each risk control measure, the SRS requirement should carry a reference to the risk control ID and a short statement of the hazardous situation it mitigates, and the verification activity should carry the same reference plus the failure condition it must exercise. That way the intent travels with the requirement and the test, rather than living only in the risk file.

Second, I would run a focused review of the affected controls — not the whole matrix, just the ones where the intent gap is suspected — with the systems engineer, the test engineer, and someone who owns the risk analysis in the room together. The goal is to confirm, for each control, that the requirement actually implements the intent and that the test actually stresses the failure condition. Where it doesn't, the test gets rewritten or the requirement gets corrected, and the change is captured.

Third, I would look at the root cause in the process. If requirements are being written from a template or a previous project without the risk analysis open, that's the systemic issue. The fix is usually to make the risk control ID a mandatory field in the requirement template and to include a traceability check in the design review checklist — so the gap is caught at review time rather than at audit time.

The behavioral dimension is that this can easily become a finger-pointing exercise between systems and test. I would frame it as "the process let this happen, and we're going to fix the process and the affected controls together," which keeps the focus on the outcome rather than on who dropped the ball.

**Possible follow-ups:**
- How would you prioritize which controls to review first if there are too many to review all at once?
- If the review finds that a test does not actually stress the failure condition, how would you handle the fact that the control may have been "verified" for some time without real evidence?