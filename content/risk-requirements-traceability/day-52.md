# risk-requirements-traceability — Day 52

## Q1: How would you approach tracing a risk control measure that is implemented as a mechanical interlock — for example, a physical shield that prevents a connector from being mated while power is applied — where the "verification" is partly dimensional inspection and partly functional testing?

**Answer:** The key insight is that a mechanical interlock is a control whose effectiveness depends on two distinct properties: geometry (does the shield physically block the connector in the energized state?) and behavior (does the interlock prevent the hazardous event under the range of real-world manipulations?). Those two properties need different verification methods, and both need to be traced back to the same risk control measure.

I would start by decomposing the single risk control measure into the sub-requirements that make it work. Typically that yields something like: a dimensional requirement (shield travel, clearances, material strength), a functional requirement (the interlock prevents mating while power is present, and permits it when power is removed), and possibly a durability requirement (the interlock continues to function after N cycles). Each of these becomes a traceable requirement in the SRS or the mechanical design specification, and each is linked upward to the same risk control ID in the risk management file.

For verification, the dimensional requirements are naturally verified by inspection or measurement against a drawing with tolerances — that is legitimate objective evidence as long as the acceptance criteria are numeric and the inspection is documented against a controlled drawing revision. The functional requirement is verified by test: apply power, attempt to mate the connector, confirm it cannot be mated; remove power, confirm it can. I would also want a test that exercises the failure condition the control is meant to mitigate — for example, attempting to defeat the interlock by applying force, or verifying that the interlock still blocks mating when the connector is partially inserted. A test that only confirms "the shield is present" does not demonstrate the control works.

The traceability matrix then shows one risk control measure fanning out to multiple requirements, each with its own verification activity, and all of them rolling back up to the hazard. The important discipline is that the risk management file references the control as a single integrated measure, while the traceability matrix shows the decomposition — otherwise an auditor sees a control "verified" by a dimensional check and reasonably asks whether anyone ever tested that it actually prevents the hazardous event.

**Possible follow-ups:**
- If the dimensional inspection is performed by the manufacturer rather than the design team, how do you ensure the inspection records are adequate objective evidence for the design history file?
- How would you handle a situation where the functional test passes on a prototype but the production unit uses a different material or tolerance that could affect interlock strength?

## Q2: How would you approach deciding whether a risk control measure should be traced to a design requirement, a design element, or both — and what practical difference does that distinction make in a traceability matrix?

**Answer:** The distinction matters because requirements and design elements answer different questions, and conflating them is one of the most common sources of traceability gaps.

A design requirement is a statement of what the system must do or how well it must do it — it is verifiable and it has an acceptance criterion. A design element is the physical or logical thing that implements the requirement — a specific circuit block, a firmware module, a mechanical part, a PCB layout feature. A risk control measure is the risk-management construct that says "this hazard is mitigated by this means."

In practice, a risk control measure almost always needs to be traced to at least one design requirement, because that is what makes it verifiable. If a control is implemented through component derating, for example, the requirement might be "the capacitor voltage rating shall be at least twice the maximum expected stress," and the design element is the specific capacitor and its placement. The requirement gives you something to verify; the design element gives you something to inspect or analyze.

Tracing to a design element as well is useful when the control's effectiveness depends on how the element is realized — for example, creepage distance depends on PCB layout, not just on a requirement statement. In those cases the traceability matrix should show the requirement, the design element that satisfies it, and the verification activity, so that a change to the layout triggers a review of whether the control is still satisfied.

The practical difference in the matrix is that requirement-to-verification links support verification coverage reporting, while requirement-to-design-element links support change impact analysis. A matrix that only has requirement-to-test links will tell you whether everything was tested, but it won't tell you what needs re-verification when a design element changes. A matrix that only has requirement-to-design links will tell you what implements what, but not whether it was proven. You need both, and the risk control measure is the anchor that ties them together.

**Possible follow-ups:**
- How would you handle a risk control measure that is implemented by a design element with no corresponding requirement — for example, a layout rule that emerged from experience rather than from a stated requirement?
- In a tool like a requirements management system, would you model the design element as an object with its own ID, or as an attribute of the requirement?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity's acceptance criterion is stated as "the control functions as designed" rather than as a measurable pass/fail threshold?

**Answer:** An acceptance criterion of "functions as designed" is not a criterion — it is a placeholder that defers the real question to whoever happens to be running the test. It creates two problems: the test cannot fail in a reproducible way, and the resulting evidence is subjective, which is exactly what verification is supposed to avoid.

The first step is to go back to the risk analysis and ask what the control is actually supposed to achieve. A risk control measure exists to reduce the probability or severity of a hazardous event, and that reduction has to be expressible in observable terms. For a firmware plausibility check, the observable might be "the system rejects a sensor reading that changes by more than the configured rate between consecutive samples, and enters the specified fault state within the specified time." For a hardware comparator, it might be "the output asserts when the input exceeds the trip threshold, and de-asserts when the input falls below the reset threshold, within the stated tolerance band." Each of those is measurable.

Once the observable behavior is defined, the acceptance criterion becomes a numeric threshold with a tolerance, and the test procedure specifies how the stimulus is applied, what is measured, and what constitutes pass or fail. If the control has multiple aspects — trip point and reset point, for example — the criterion needs to cover each one, because a test that only checks the trip point does not demonstrate the control works across its intended range.

If the team genuinely cannot define a measurable criterion, that is a signal that the control itself is not well specified, and the right response is to revisit the risk control measure rather than to paper over it with vague language. In some cases the control is real but the verification method is analysis or inspection rather than test — that is acceptable, but the analysis still needs defined inputs, a defined method, and a defined pass criterion.

I would also add a review gate: any verification activity whose acceptance criterion cannot be evaluated by someone other than its author should be flagged during the verification plan review, before testing starts, because fixing it then is far cheaper than defending it during an audit.

**Possible follow-ups:**
- How would you handle a control where the "designed" behavior is itself ambiguous because the design specification and the risk analysis disagree on what the control should do?
- If the acceptance criterion is measurable but the measurement requires equipment the lab doesn't have, how would you decide between acquiring the equipment and using an alternative verification method?

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system includes a safety-related parameter that is set at manufacturing time — for example, a calibration value or a configuration constant — and the parameter value itself is the control?

**Answer:** This is a case where the control is not a circuit or a piece of code but a value, and the traceability has to cover three things: the parameter's specification, the process that sets it, and the verification that it was set correctly on the unit that ships.

The first link is from the risk control measure to a requirement that defines the parameter: its nominal value, its acceptable range, its units, and the consequence of it being outside range. That requirement is what makes the control verifiable — without a stated range, "the calibration value is correct" is not checkable.

The second link is from the requirement to the manufacturing process that establishes the value. That might be a calibration procedure, a firmware configuration step, or a one-time programming operation. The process itself becomes a controlled document, and the traceability matrix should show the requirement flowing into the process specification, not just into a test. This is where a lot of traceability schemes break down, because the matrix is built around design artifacts and the manufacturing process lives in a different document set.

The third link is from the process to the verification activity. For a parameter set at manufacturing time, verification typically has two layers: a process verification that confirms the calibration or programming step is capable and repeatable, and a unit-level verification that confirms each shipped unit has a value within range. The unit-level check might be a functional test that exercises the parameter indirectly, or a direct readback of the stored value. Either way, the acceptance criterion is the range from the requirement, and the record of the value is retained as part of the device history record.

There is also a change-control dimension: if the parameter range is ever widened or narrowed, that change has to propagate back to the risk analysis, because the control's effectiveness depends on the range. I would want the traceability matrix to make that propagation visible, so that a change to the parameter specification triggers a review of the risk control measure and the manufacturing process, not just the requirement.

**Possible follow-ups:**
- How would you handle a parameter that is set by the clinician at installation rather than at manufacturing — does the traceability scheme change?
- If the parameter is stored in non-volatile memory and can be changed through a service port, how does that affect the verification strategy?

## Q5: (Behavioral) Imagine you're leading a project where the risk management team insists that every risk control measure must be traced to a *single* verification activity, arguing that multiple links per control make the matrix unreadable and hard to audit. The test lead argues that several controls genuinely require multiple verification activities — for example, a control verified partly by analysis and partly by test. How would you resolve this disagreement?

**Answer:** Both positions contain something true, and the resolution is to separate the readability concern from the traceability requirement rather than treating them as a trade-off.

The risk management team is right that a matrix where every control has an arbitrary number of links becomes hard to audit — but the problem they are describing is a presentation problem, not a data model problem. The underlying traceability data should capture every legitimate link, because the links are what demonstrate the control is fully verified. The view that gets shown to an auditor can be a summary that rolls up multiple verification activities into a single "verification status" per control, with the detail available on drill-down. That gives the auditor a clean top-level view and gives the engineering team the complete picture.

The test lead is right that some controls genuinely require multiple verification methods. A control that has a hardware portion and a firmware portion, or a control whose effectiveness depends on both a design margin and a functional behavior, cannot be fully verified by a single activity. Forcing it into one link would either hide a real verification gap or force the team to write a composite test that is harder to execute and harder to defend.

So my approach would be to agree on the principle that every risk control measure must have complete verification coverage, and then agree on the presentation convention: the top-level matrix shows one row per control with a status, and the detailed matrix shows all the links. I would also want the team to agree on what counts as a legitimate additional link — for example, an analysis that establishes a design margin is a legitimate verification activity, but a test that happens to exercise the control as a side effect is not, because it doesn't stress the failure condition.

The conversation is easier if we frame it around what the auditor will actually ask. The auditor will ask "how do you know this control works?" The answer needs to be complete, and it needs to be traceable. Whether that answer is one activity or three is a consequence of the control, not a formatting choice.

**Possible follow-ups:**
- How would you handle a control where the risk management team and the test lead disagree about whether a particular activity counts as verification at all — for example, a design review?
- If the tool being used for the traceability matrix only supports one verification link per requirement, how would you work around that limitation without losing information?