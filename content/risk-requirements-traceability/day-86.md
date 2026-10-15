# risk-requirements-traceability — Day 86

## Q1: How would you approach tracing a risk control measure that is implemented as a *user-facing procedural control* — for example, a label instructing the operator to verify a connection before energizing — where the "implementation" is a printed instruction and the "verification" is a usability study rather than a bench test?

**Answer:** The key insight is that a procedural control is still a risk control, and it needs the same traceability discipline as a hardware or firmware control — but the *evidence type* is different. I'd start by making sure the risk management file captures the control in a form that names the human action, the failure it mitigates, and the assumptions about the user (training level, environment, time pressure). From there, the "requirement" that implements it is typically a usability or labeling requirement in the SRS — something like "the label shall be legible at the specified viewing distance and shall state the pre-energization check" — with measurable acceptance criteria, because "the label is clear" is not verifiable.

The verification activity is then a usability study or human-factors evaluation with a defined protocol: representative users, representative conditions, and pass/fail criteria tied to whether the user actually performs the check. The traceability link runs hazard → risk control → labeling/usability requirement → usability study protocol → result. The important part is that the acceptance criteria are written *before* the study, not reverse-engineered from whatever the study happened to show.

I'd also flag the residual-risk implication: procedural controls are generally considered less effective than design controls because they depend on human behavior, so the risk analysis should reflect that in the effectiveness credit. If the control is load-bearing for a high-severity hazard, that's a signal to push back toward a design solution.

**Possible follow-ups:**
- How would you handle a situation where the usability study shows the label works for trained users but not for the intended untrained user population?
- If the label is later revised for a cosmetic reason, how do you decide whether the usability study needs to be repeated?

## Q2: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *supplier-provided test report* for a purchased component (e.g., a certified relay or an off-the-shelf power module), rather than a test your own team performed?

**Answer:** Supplier evidence can be legitimate, but it has to be evaluated against the *specific* claim you're making, not accepted because the part is certified. I'd work through it in layers.

First, what exactly is the risk control claiming? If the control is "the relay opens under fault current within X ms," the supplier report needs to demonstrate that behavior under conditions that match your application — same coil drive, same load characteristics, same ambient range. A generic datasheet endurance curve is not the same as a test report for your operating point.

Second, what's the provenance and scope of the report? Is it a third-party certification (which carries its own standards and test conditions), an internal supplier qualification report, or a marketing document? Is the report for the exact part number and revision you're using, or a family representative? Is the test setup described well enough that you can judge applicability?

Third, if the supplier evidence doesn't fully cover your claim, you have a few options: supplement it with your own testing at the system level, add analysis to bridge the gap (with the assumptions documented), or treat the supplier evidence as partial and add a design margin argument. Whichever path you take, the traceability entry should record *what* the supplier evidence covers, *what* it doesn't, and *how* the residual gap is addressed. That way an auditor or reviewer can see the reasoning rather than just a link to a PDF.

**Possible follow-ups:**
- How would you handle a supplier that refuses to share the underlying test data and only provides a pass/fail certificate?
- If the supplier changes the part's internal construction without changing the part number, how does that affect your traceability?

## Q3: How would you approach tracing a risk control measure whose effectiveness depends on a *sequence* of events rather than a single action — for example, a control that requires the system to detect a fault, log it, notify the user, and then enter a safe state, where each step is owned by a different subsystem?

**Answer:** This is where a flat "control → test" link breaks down, because the control is really a *behavior* that emerges from a chain of subsystem actions, and no single subsystem owns the whole thing. I'd handle it by decomposing the control into its constituent steps and treating the sequence itself as a first-class requirement.

Concretely: the risk management file names the control and the hazard. The SRS contains a system-level requirement that describes the end-to-end behavior — detect, log, notify, safe-state — with a bounded time budget and a defined safe state. That system-level requirement then allocates to subsystem requirements: the detection subsystem owns the detection threshold and latency, the logging subsystem owns the persistence guarantee, the HMI subsystem owns the notification, the actuation subsystem owns the safe-state transition. Each of those is separately traceable to its own verification activity.

Then there's a *second* layer of traceability: an integration test that exercises the whole sequence end-to-end, including the handoffs between subsystems. That integration test is what actually verifies the risk control as a control, because it's the only test that can catch a sequencing bug — for example, the safe state being entered before the log is written, or the notification being suppressed because the fault handler preempted the HMI task. The subsystem tests verify the pieces; the integration test verifies the sequence.

I'd also make sure the timing budget is allocated explicitly across the steps, so that if one subsystem's latency grows during development, you can see whether the overall control still meets its bound.

**Possible follow-ups:**
- How would you verify the sequence under fault conditions where one of the steps itself fails — for example, the logging subsystem is unavailable?
- If the sequence is implemented across two microcontrollers communicating over a bus, how does that change your integration test strategy?

## Q4: How would you approach establishing traceability between risk control measures and requirements when the same risk control measure is implemented differently across multiple product variants or hardware revisions?

**Answer:** The cleanest approach is to separate the *control intent* from the *implementation* and trace both. The control intent — "the hazard of over-temperature is mitigated by removing power from the heater within a bounded time" — is variant-independent and lives in the risk management file. Each variant then has its own implementation requirement and its own verification activity, both traced back to the same control intent.

In practice this means the traceability matrix has a fan-out at the control level: one risk control, multiple implementation requirements, multiple verification activities, one per variant. That's fine as long as the matrix makes the fan-out explicit and each branch has its own acceptance criteria. The danger is when teams try to force a single requirement to cover all variants — that usually produces a vague requirement that can't be verified on any specific variant.

I'd also add a variant/revision attribute to the traceability records so that a coverage report can be run per variant. If variant B is missing a verification activity for a control that variant A has verified, that gap should show up immediately rather than being masked by variant A's coverage.

One more thing: when variants share a common SRS, the shared requirements should be written at the level of the control intent, and the variant-specific implementation details should live in variant-specific documents. Mixing the two produces a document that's simultaneously too vague for one variant and too specific for another.

**Possible follow-ups:**
- How would you handle a situation where a variant is added late in the project and the risk analysis hasn't been updated to reflect its implementation?
- If two variants use the same component but different firmware, how do you decide whether the hardware verification can be reused?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is a documentation-integrity problem disguised as a traceability problem, and it's more common than people admit. The links are technically present, so a coverage report would show green — but the control isn't actually being verified in the sense that matters, because nobody downstream understands *why* the requirement exists or *what failure* the test is supposed to provoke.

My first move would be to stop treating this as a process failure and start treating it as a communication failure. The systems engineer and test engineer aren't being lazy; they're working from documents that don't carry the intent forward. So the fix has to be structural, not just "go read the risk file."

Concretely, I'd do three things. First, for the specific controls in question, I'd sit down with the systems engineer, the test engineer, and whoever owns the risk analysis entry, and walk through each control end-to-end: what hazard, what failure mode, what does the control actually do, what would a test look like that would *fail* if the control were absent. That conversation usually surfaces whether the existing test is adequate or needs to be rewritten.

Second, I'd change the artifact templates so that the intent travels with the requirement. A requirement derived from a risk control should carry a short "safety rationale" field that names the hazard and the failure mode — not a full risk analysis, just enough that a reader understands why the requirement exists. Similarly, the test procedure should state the failure condition it's designed to provoke, not just the pass criterion.

Third, I'd add a lightweight review gate: before a verification activity is accepted as covering a risk control, someone who understands the risk analysis should confirm that the test actually exercises the failure condition. That's a five-minute review per control, and it catches exactly this class of problem.

The broader point I'd make to the team is that traceability is not the goal — it's a proxy for the goal, which is that the control actually works and someone can prove it. Links that don't carry intent are worse than no links, because they create false confidence.

**Possible follow-ups:**
- How would you roll this out without turning it into a bureaucratic burden that slows the team down?
- If you find this problem on a project that's already in design verification, how do you prioritize which controls to re-examine first?