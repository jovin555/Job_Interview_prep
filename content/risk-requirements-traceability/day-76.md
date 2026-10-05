# risk-requirements-traceability — Day 76

## Q1: How would you approach tracing a risk control measure whose effectiveness depends on a *sequence* of events rather than a single action — for example, a control that requires the system to detect a fault, log it, notify the user, and then enter a safe state, where each step is owned by a different subsystem?

**Answer:** The core problem with sequence-based controls is that a traceability matrix built around single requirements will show full coverage while the *ordering and completion* of the sequence goes unverified. I'd treat the sequence itself as a first-class requirement rather than as an emergent property of four independent ones.

Concretely, I'd do four things. First, decompose the control into its constituent steps and give each step its own requirement with a measurable acceptance criterion — detection latency, log persistence, notification behavior, safe-state entry condition — so each subsystem owns a traceable, verifiable piece. Second, add a *composite* requirement at the system level that captures the sequence semantics: the ordering, the fact that later steps must not proceed if an earlier step fails, and the total time budget from fault to safe state. That composite requirement is what the risk analysis actually credits, so it needs its own verification activity — typically an end-to-end fault-injection test that exercises the whole chain, not four isolated unit tests.

Third, I'd make the traceability matrix show both the vertical links (hazard → composite control → step requirements → design elements → tests) and the horizontal dependency between steps, so a reviewer can see that step 3 depends on step 2 completing. A simple way is a state machine or sequence diagram in the architecture documentation, referenced from the composite requirement, so the ordering is explicit and reviewable rather than buried in firmware logic.

Fourth, I'd watch for the failure mode where each subsystem verifies its own step in isolation and everyone declares victory — the classic "all green, sequence broken" outcome. The end-to-end test is the only artifact that can catch a missing handoff, a race between subsystems, or a step that silently no-ops under fault conditions. I'd also make sure the safe-state entry is verified under the *fault* condition, not just nominal, because that's the whole point of the control.

**Possible follow-ups:**
- If the end-to-end test is expensive or requires a full system build, how would you decide when in the project it must be run versus relying on subsystem tests?
- How would you handle a case where the sequence is implemented across two microcontrollers with a shared bus, and the ordering guarantee depends on bus timing?

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a *user-facing procedural control* — for example, a label instructing the operator to verify a connection before energizing — where the "implementation" is a printed instruction and the "verification" is a usability study rather than a bench test?

**Answer:** Procedural controls are the ones teams most often under-document, because they don't live in hardware or firmware and there's no obvious place to put them in a requirements database. But ISO 14971 treats them as legitimate risk controls — usually lower in the hierarchy than design controls, and only acceptable when design controls are impractical — so they still need to be traceable and verified.

I'd start by making the control explicit in the risk management file with a clear statement of what the user must do, under what conditions, and what hazard it mitigates. Then I'd create a requirement that captures the *information* the user needs and the *form* it takes — a label, an IFU instruction, a software prompt — with measurable acceptance criteria where possible: legibility at a specified distance, comprehension by a representative user population, correct action taken in a simulated scenario.

The verification activity for a procedural control is typically a usability or human-factors study, sometimes supplemented by a comprehension test or a formative/summative evaluation. That's legitimate objective evidence, but it has to be designed to actually stress the failure mode: if the hazard is "user energizes without checking the connection," the study has to put a representative user in a realistic situation and observe whether they check. A study that just asks "did you read the label?" proves nothing.

In the traceability matrix I'd link hazard → procedural control → information requirement → label/IFU artifact → usability study protocol and report. I'd also flag the residual risk explicitly, because procedural controls are inherently less reliable than design controls — users forget, misread, or skip steps — and the risk file should reflect that the control reduces but does not eliminate the hazard. If the residual risk is still unacceptable, the answer is to add a design control, not to write a stronger label.

**Possible follow-ups:**
- How would you decide whether a procedural control is acceptable at all, versus insisting on a design control?
- If the label is translated into multiple languages, how does that affect the verification activity and the traceability links?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *supplier-provided test report* for a purchased component (e.g., a certified relay or an off-the-shelf power module), rather than a test your own team performed?

**Answer:** Supplier test reports can be valid objective evidence, but only if you've done the work to establish that the report actually covers your use case. The trap is treating "the supplier tested it" as equivalent to "we verified our risk control," when the supplier's test conditions, tolerances, and failure criteria may not match yours.

I'd work through it in layers. First, confirm the component is being used within the supplier's specified operating envelope — voltage, current, temperature, switching cycles, mounting, environmental conditions. If your application pushes outside that envelope, the supplier report doesn't cover you and you need your own testing or a derating analysis. Second, check that the supplier's test actually exercises the failure mode your risk analysis credits. A relay datasheet might report contact resistance and endurance at rated load, but if your hazard is "relay fails to open under fault current," you need evidence specific to that condition — which may be in the datasheet, in a separate qualification report, or may not exist at all.

Third, verify the supplier's quality system and the traceability of the specific lot or part number. A report for a generic part family isn't the same as a report for the exact variant you're using, especially if the supplier has multiple grades or the part has been revised. I'd want the report to reference the specific part number and revision, and ideally the supplier's change notification process, so a silent revision doesn't invalidate your evidence.

In the traceability matrix, I'd link the risk control to the supplier report as the verification artifact, but with a note documenting the applicability assessment — what conditions the report covers, what it doesn't, and what additional evidence (if any) your team generated. If the gap is significant, the honest answer is to run your own verification on the production-representative assembly, because the risk control's effectiveness in *your* system is what the risk file is claiming.

**Possible follow-ups:**
- How would you handle a supplier that refuses to share the underlying test data and only provides a pass/fail certificate?
- If the component is later second-sourced, what does that do to your traceability and verification evidence?

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** Redundant controls are a case where the traceability matrix has to represent *logical* structure, not just links. If you draw two independent paths from hazard to verification, a reviewer can't tell whether the controls are genuinely independent or whether they share a common failure mode — and the risk credit depends entirely on that independence.

I'd structure it in three parts. First, a single hazard-level entry in the risk file that names both controls and states explicitly that the risk reduction credit assumes independence. Second, a separate requirement and verification path for each control, owned by its respective team, so each is individually traceable and verifiable. Third, and most importantly, a *common-cause* analysis that examines whether the two controls share anything — power rail, clock, sensor, communication bus, firmware module, manufacturing process — that could cause both to fail together. If they do share something, the independence assumption is weakened and the risk credit may need to be reduced or the shared element itself needs a control.

The "added at different times" aspect is a real risk to the scheme. The later control may have been designed without knowledge of the earlier one, so the two might overlap in ways nobody intended, or the later one might actually depend on the earlier one in a way that breaks independence. I'd want a design review that brings both teams together specifically to walk the common-cause analysis, and I'd record the outcome in the risk file so the independence claim is documented rather than assumed.

In the matrix, I'd show the hazard with two outgoing links, each labeled with the control ID and the team that owns it, and a separate row or annotation for the common-cause analysis. That way an auditor can see at a glance that redundancy was claimed, that both paths were verified, and that independence was assessed rather than presumed.

**Possible follow-ups:**
- If the common-cause analysis reveals a shared element, how would you decide whether to add a control on that element or to reduce the risk credit for redundancy?
- How would you handle a situation where the two controls were added by different teams but the risk analysis was written before either existed?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is the failure mode that a traceability matrix is supposed to prevent, and it's the most dangerous kind because the matrix looks complete. The links are real — the IDs match, the coverage report is green — but the *meaning* has been lost. The requirement may be technically correct but written without understanding why it exists, and the test may pass without actually exercising the failure condition the control is meant to mitigate.

My first move would be to stop treating this as a documentation problem and treat it as a communication problem. The fix isn't to add more links; it's to get the three people — systems engineer, test engineer, and whoever owns the risk analysis entry — in a room together with the hazard in front of them. I'd walk through the hazard, the control, the requirement, and the test as a single narrative, and ask each person to explain in their own words what the control is for and how their artifact contributes to it. The gaps usually surface immediately: the test engineer realizes the test doesn't actually stress the fault condition, or the systems engineer realizes the requirement was written to a different interpretation of the control.

Once the intent is clear, I'd fix the artifacts, not just the links. The requirement may need to be rewritten to state the safety intent explicitly — not just "the system shall disable the motor output within 100 ms of a fault signal" but a note or parent requirement that ties it to the hazard. The test may need to be redesigned to inject the actual fault condition rather than a nominal signal. And the risk file entry may need to be updated if the control as implemented doesn't match what was originally credited.

Then I'd address the systemic cause. If this happened once, it's a communication gap on one control. If it's happening across multiple controls, the process is broken — likely because the risk analysis is treated as a separate document that gets written once and filed, rather than as a living input to requirements and verification. I'd want to change the workflow so that risk analysis entries are reviewed jointly by systems, test, and quality at the point where requirements are derived, and so that verification plans are reviewed against the risk file, not just against the SRS. That's a heavier process, but it's cheaper than discovering at audit — or worse, in the field — that a safety control was never actually verified.

**Possible follow-ups:**
- How would you handle the situation if the test engineer's test genuinely can't be redesigned to stress the fault condition without significant cost or schedule impact?
- If you find this pattern across many controls, how would you prioritize which ones to fix first?