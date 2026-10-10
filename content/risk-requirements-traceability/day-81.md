# risk-requirements-traceability — Day 81

## Q1: How would you approach tracing a risk control measure whose effectiveness depends on a *sequence* of events rather than a single action — for example, a control that requires the system to detect a fault, log it, notify the user, and then enter a safe state, where each step is owned by a different subsystem?

**Answer:** The core problem here is that the risk control is not any one of the four steps — it's the *end-to-end behavior* that the sequence completes correctly and within a bounded time. If you trace only to the individual steps, you can have every step pass its own verification while the composite control is broken (e.g., the fault is detected but the notification blocks the safe-state transition, or the log write stalls on a full filesystem and the safe state never happens).

My approach would be to model the control as a first-class requirement in its own right — something like "the system shall transition to the safe state within T after fault detection, and shall have logged and notified the user" — and then decompose it into sub-requirements, one per subsystem, each with its own measurable acceptance criterion and its own traceability link back to the parent control. The parent requirement is what traces to the hazard in the risk management file; the children trace to the parent, not directly to the hazard. That gives you a two-level traceability structure where the composite behavior is explicitly owned by someone (typically systems engineering) rather than falling into the gap between subsystem teams.

For verification, I'd want both per-step tests and an integration test that exercises the full sequence under fault injection, because the failure modes of interest are almost always in the *handoffs* — the interface between detection and logging, or between notification and the safe-state transition. I'd also want the timing budget allocated explicitly across the steps, so that each subsystem knows its slice and the integration test can check the total.

**Possible follow-ups:**
- If the notification step is allowed to be asynchronous (fire-and-forget), how does that change where you put the acceptance criterion for the composite control?
- How would you handle a case where one of the steps is owned by a third-party subsystem whose requirements document you don't control?

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a *user-facing procedural control* — for example, a label instructing the operator to verify a connection before energizing — where the "implementation" is a printed instruction and the "verification" is a usability study rather than a bench test?

**Answer:** Procedural controls are the ones most likely to fall out of a traceability matrix entirely, because they don't map to a design element in the usual sense — there's no schematic net, no firmware function, no mechanical part. But they are still risk controls under ISO 14971, and they still need to be traced from hazard through to verification.

The way I'd handle it is to treat the *label content and placement* as the design element, and the *usability study or human-factors validation* as the verification activity. The requirement would be written in terms of the observable behavior you need from the user — for example, "the operator shall be able to identify the correct connection state before energizing, with a specified comprehension rate under the intended use environment" — rather than "a label shall be affixed." That makes the requirement measurable and gives the usability study something concrete to verify against.

The traceability chain then runs: hazard → risk control (procedural) → requirement (user comprehension / behavior) → design element (label artwork, placement, IFU text) → verification (formative and summative usability testing). I'd also want a link to the risk management file noting that this is a *procedural* control, because procedural controls are generally considered weaker than design controls — they depend on human reliability — and the residual risk evaluation needs to reflect that. If the hazard severity is high, a procedural control alone is usually not acceptable, and the traceability should show what other controls exist.

**Possible follow-ups:**
- How would you verify a procedural control if the intended user population is small or hard to recruit for a usability study?
- What would you do if the usability study showed the label was misunderstood by a significant fraction of users — does that invalidate the risk control, or does it just trigger a redesign?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *supplier-provided test report* for a purchased component (e.g., a certified relay or an off-the-shelf power module), rather than a test your own team performed?

**Answer:** The first thing I'd want to establish is whether the supplier's test report actually covers the *failure condition* the risk control is meant to mitigate, in *your* application's operating conditions — not just the component's rated conditions. A relay certified to a generic standard may have been tested at a different load, different ambient, different cycle count, or different mounting orientation than your design uses. The report is evidence, but it's evidence about the component, not necessarily about your risk control.

So I'd treat the supplier report as one input to the verification, and I'd want to document the *applicability argument* explicitly: what the supplier tested, what your application requires, and why the two are equivalent (or where they diverge and what you did about it). If there's a gap — say, the supplier tested at 25°C but your application runs at 70°C — then the supplier report alone is not sufficient verification, and you need either your own test at the application conditions or a documented analysis showing the derating is adequate.

In the traceability matrix, I'd link the risk control to the supplier report *plus* the applicability justification, and I'd make sure the justification is a controlled document, not a note in someone's email. If the supplier report is the sole evidence, I'd want a clear statement in the risk management file that the control's verification relies on supplier data, with the rationale and any limitations. That's the kind of thing a reviewer or auditor will probe, so it's better to be explicit about it up front.

**Possible follow-ups:**
- How would you handle a supplier that refuses to share the full test report, offering only a certificate of compliance?
- If the supplier report is in a language or format that your quality system doesn't normally accept, what would you do?

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** The trap here is that the traceability matrix ends up showing two controls pointing at the same hazard, and it's easy to lose track of the fact that the risk analysis is crediting *both* — which means the residual risk calculation depends on both being present and independent. If one of them is later removed or weakened, the residual risk changes, and the traceability needs to make that visible.

I'd structure it so the hazard has two distinct risk control entries in the risk management file, each with its own risk control ID, and each traced independently through its own requirements and verification. The key addition is an explicit *independence* argument — a note or a linked analysis explaining why the two controls are considered independent (different failure modes, different physical principles, different power domains, etc.). That independence claim is itself something that needs to be verified, because if the two controls share a common cause of failure — same power rail, same sensor, same firmware task — then the risk analysis is over-crediting them.

For the "added at different times by different teams" problem, I'd want a single owner for the hazard-level traceability — typically systems engineering or the risk manager — who is responsible for keeping the two control paths consistent. Each team owns its own control's requirements and verification, but the hazard-level view is owned centrally. That way, when one team changes their control, the central owner can check whether the independence argument still holds and whether the residual risk evaluation needs to be revisited.

**Possible follow-ups:**
- How would you verify the independence claim if the two controls are implemented in the same firmware image running on the same microcontroller?
- If one of the two controls is later found to be ineffective, what's the process for updating the risk analysis and the traceability matrix?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is the classic failure mode of traceability done as a documentation exercise rather than as a communication tool — the links are technically present, so the matrix "passes," but the people who wrote the requirement and the test don't actually know *why* the control exists. That's a real risk, because a requirement written without understanding the hazard it mitigates is likely to be either over- or under-specified, and a test written without understanding the failure condition is likely to test the wrong thing.

My first move would be to not treat this as a compliance problem to be fixed by adding more links, but as a communication problem to be fixed by getting the three people in a room together — the systems engineer, the test engineer, and whoever owns the risk analysis entry — and walking through the hazard, the control, the requirement, and the test as a single narrative. The goal is to confirm that the requirement actually captures the control's intent, and that the test actually stresses the failure condition the control is meant to mitigate. If either is off, that's a real finding, not just a documentation gap.

Once we've done that for this one control, I'd want to understand whether it's a one-off or a systemic pattern. If it's systemic, the fix is process-level: make the risk analysis entry a required input to requirement authoring and test authoring, not just a downstream reference. That could mean a short "risk control intent" summary attached to each safety-related requirement, or a review step where the test engineer has to state in the test procedure which failure condition they're exercising. The traceability matrix is the index; the intent has to live in the artifacts themselves.

**Possible follow-ups:**
- How would you scale this approach if there are dozens or hundreds of safety-related requirements, rather than a handful?
- If the systems engineer pushes back and says the requirement is fine as written and the test is fine as written, and the only issue is that nobody read the risk analysis, how would you respond?