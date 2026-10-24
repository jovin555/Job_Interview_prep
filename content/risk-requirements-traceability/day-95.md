# risk-requirements-traceability — Day 95

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a *firmware-based rate limiter on an actuator command* — for example, firmware that clamps the commanded speed of a motor to a maximum rate of change — when the risk analysis credits the limiter as a control against a hazardous overspeed condition, but the firmware requirements only describe the clamping behavior functionally and never reference the hazard?

**Answer:** The core problem here is that the requirement exists and is testable, but the *safety intent* has been stripped out — so the traceability link is technically present but semantically empty. A reviewer or auditor following the chain from hazard to verification would see a functional requirement about clamping and a test that confirms clamping, but nothing that connects the two back to the overspeed hazard. That's a gap even though every box is ticked.

My approach would be to fix this at the requirement level rather than papering over it in the matrix. First, I'd add an explicit safety-annotated requirement — something like "the firmware shall limit the rate of change of the motor speed command to no more than [X] units per [Y] ms to prevent hazardous overspeed" — and link it bidirectionally to the specific hazard and risk control entry in the risk management file. The existing functional requirement can remain as the implementation-level requirement, but it should be traced *upward* to the safety requirement so the hierarchy is explicit: hazard → risk control → safety requirement → functional/derived requirement → design element → verification.

Second, I'd check whether the verification test actually exercises the failure condition. A test that confirms the limiter clamps under nominal command changes is necessary but not sufficient — the test should also demonstrate that without the limiter (or with it disabled), the commanded rate would exceed the hazardous threshold, so the test is capable of detecting the failure. That's the "test the test" discipline: if you can't make it fail by removing the control, you haven't proven the control is doing anything.

Third, I'd address the root cause so it doesn't recur: add a review checklist item or a template field in the firmware requirements document that requires the author to state the hazard/risk-control reference whenever a requirement implements a safety function. The traceability matrix is downstream of the documents — if the documents don't carry the intent, the matrix can't invent it.

**Possible follow-ups:**
- If the firmware team pushes back and says adding safety language to every requirement clutters the SRS, how would you decide which requirements get the safety annotation versus which stay purely functional?
- How would you verify that the rate limiter's *maximum rate* value itself is correct — i.e., that the chosen threshold actually keeps the system below the hazardous overspeed condition with adequate margin?

## Q2: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *design review* whose checklist was written for a different purpose — for example, a general "power supply design review" checklist — and the risk control's specific failure condition is never explicitly assessed during the review?

**Answer:** This is a common and subtle failure mode: the traceability matrix shows a link, the review happened, the review passed, so on paper the control is verified. But the review was never *designed* to assess that particular failure condition, so the evidence is essentially coincidental. If the control were wrong, the review would still have passed — which means the verification activity has no diagnostic power for this control.

My first step would be to read the review checklist against the risk control's failure condition and confirm the gap concretely — not just assert it. I'd want to be able to say "the checklist covers input/output voltage margins and thermal derating, but nothing about the [specific failure mode], so a reviewer following the checklist would never be prompted to assess it." That makes the conversation factual rather than a matter of opinion.

Then I'd treat it as a verification-planning problem rather than a "the review is invalid" problem. Options, roughly in order of preference:

1. **Amend the review scope** — add a review item or a supplementary review record specifically targeting the risk control's failure condition, with explicit acceptance criteria. This preserves the existing review as evidence for what it *does* cover and adds targeted evidence for the gap. It's usually the least disruptive fix and keeps the review as a legitimate verification method.
2. **Supplement with analysis or test** — if the failure condition is better assessed by calculation (e.g., worst-case tolerance stack-up) or by a bench test, add that as an additional verification activity linked to the same control. A control can legitimately have multiple verification activities.
3. **Re-scope the traceability link** — if the review genuinely doesn't verify the control, remove the link and replace it with the correct activity. Leaving a false link in place is worse than having a gap, because it hides the gap.

I'd also want to fix the process so this doesn't recur: when a risk control is traced to a design review, the review record should explicitly state which risk control(s) it verifies and what the pass criteria are for each. A generic review checklist is fine for general design quality, but risk-control verification needs its own explicit criteria.

**Possible follow-ups:**
- How would you decide whether a design review is an acceptable verification method for a given risk control at all, versus insisting on test or analysis?
- If the review has already been signed off and the design is frozen, what's the least disruptive way to close the gap without reopening the whole review?

## Q3: How would you approach establishing traceability when a single risk control measure is implemented as a *distributed control loop* — for example, a temperature control where a hardware sensor, a firmware PID loop, and a hardware power switch each contribute to keeping a heating element within a safe range — and the risk analysis treats the whole loop as one control?

**Answer:** The challenge here is that the risk analysis is correctly treating the loop as one control — because the *emergent* behavior of the loop is what mitigates the hazard, not any single element — but the traceability artifacts are naturally organized by component and by discipline. If you trace only at the component level, you lose the fact that the control depends on all three elements working together, and you can end up with a situation where each element is individually verified but the integrated loop behavior is never verified as a whole.

My approach would be to model the control at two levels and link them explicitly:

**Level 1 — the control as a system-level requirement.** Create a single system requirement that describes the control's *behavior and acceptance criteria* at the loop level: e.g., "the system shall maintain the heating element temperature within [safe range] under [specified load and ambient conditions], and shall remove power if temperature exceeds [threshold] within [time]." This requirement is what traces to the hazard and to the risk control entry. It's the "one control, one requirement" anchor.

**Level 2 — the allocated sub-requirements.** Decompose that system requirement into allocated requirements for each element: the sensor's accuracy and response time, the firmware PID loop's update rate and output limits, the power switch's response time and fail-safe behavior. Each allocated requirement traces *up* to the system-level control requirement, and each traces *down* to its design element and its own verification. This is classic requirement allocation, and it's what makes the distributed nature explicit rather than implicit.

**Verification at both levels.** Each element gets verified against its allocated requirement (sensor characterization, firmware unit/integration test, power switch timing test), *and* the integrated loop gets verified against the system-level requirement under representative conditions — including fault injection, like a sensor that reads low or a firmware loop that stalls, to confirm the loop still achieves the safe outcome. The integrated test is the one that actually verifies the risk control; the element tests are necessary but not sufficient.

The key discipline is that the traceability matrix must show the *roll-up*: hazard → risk control → system-level control requirement → allocated requirements (one row per element) → element verification, plus the integrated verification linked to the system-level requirement. Without the roll-up, you have three verified components and no evidence the control works as a control.

**Possible follow-ups:**
- How would you handle the case where the integrated loop test is expensive or slow (e.g., requires a thermal chamber and long soak times), and the team wants to rely on element-level verification plus analysis?
- If the PID loop's tuning parameters are changed late in development, how would you assess the traceability impact — which verification activities need to be re-run?

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system includes a *safety-related parameter set at manufacturing time* — for example, a maximum output current limit stored in non-volatile memory during production — where the parameter value itself is the control, and the value can differ between units?

**Answer:** This is a case where the control isn't a circuit or a piece of code — it's a *value*, and the value is established by a manufacturing process rather than by design. That means the traceability has to span design, manufacturing, and verification, and the usual "requirement → design element → test" chain doesn't quite fit. The risk is that the parameter gets treated as a manufacturing detail and falls out of the risk traceability entirely, so nobody verifies that the value written in production actually corresponds to the value the risk analysis assumed.

I'd structure it in three linked pieces:

**1. The parameter as a design requirement with a specified range.** The risk analysis credits a control like "output current limited to no more than [X]." That becomes a design requirement: "the maximum output current shall not exceed [X] under any operating condition." The firmware/hardware design must enforce a limit, and the *setpoint* for that limit is a configurable parameter. The requirement should specify the allowable range for the parameter and the rationale (e.g., derived from the risk analysis with margin), not just a nominal value.

**2. The parameter as a manufacturing control with its own specification.** The manufacturing process that writes the value needs its own controlled specification: what value or range is written, how it's verified after writing, what the tolerance is, and what happens if the write fails or the value is out of range. This is where the traceability extends into the production traveler or test record. The link is: risk control → design requirement (parameter range) → manufacturing specification (value to write + verification method) → production test record (evidence the value was written and verified on this unit).

**3. Verification at two levels.** Design verification confirms that the *mechanism* enforces the limit correctly across the allowable parameter range — e.g., inject a range of parameter values and confirm the output current is limited accordingly, including at the extremes of the allowed range. Production verification confirms that *each unit* has a parameter value within the allowed range, with objective evidence (a recorded measurement, not just a pass/fail flag). The design verification proves the mechanism is sound; the production verification proves each unit is configured correctly.

The subtle point I'd want to get right is the *unit-to-unit variation*. If the parameter can legitimately differ between units (e.g., calibrated per unit), then the risk analysis has to be valid across the whole allowed range, and the design verification has to cover the range, not just a nominal value. If the parameter is supposed to be identical across units, then any unit-to-unit variation is a nonconformity and the production verification needs to catch it. Either way, the traceability has to make clear which case applies.

**Possible follow-ups:**
- How would you handle a parameter that is set at manufacturing time but can also be changed later via a service port — does that change the traceability and verification approach?
- If a production test record shows a parameter value at the edge of the allowed range, how would you assess whether that unit's risk control is still effective?

## Q5: (Behavioral) Imagine you're leading a project where the traceability matrix is complete and passes audit — every risk control measure links to a requirement and a verification activity — but a test engineer privately tells you that several of the linked tests were written by copying a similar test from a previous project and adjusting the labels, and nobody has confirmed the tests actually exercise this project's failure conditions. The systems engineer argues the matrix is compliant and the tests pass, so there's no problem. How would you handle this?

**Answer:** The systems engineer is technically correct that the matrix is compliant and the tests pass — but that's exactly the problem. A traceability matrix that links to tests which don't exercise the failure condition is worse than a matrix with visible gaps, because it creates false confidence. The audit will pass, the product will ship, and the control may not actually work. I'd treat this as a quality-of-evidence issue, not a paperwork issue, and I'd want to handle it carefully because the test engineer came to me privately and I don't want to expose them or discourage future candor.

My approach would be:

**First, verify the claim myself before acting on it.** I'd pick two or three of the flagged tests and walk through them against the risk analysis entry — does the test setup actually create the failure condition the control is meant to mitigate? Does the pass criterion distinguish "control worked" from "control didn't need to work"? I want to confirm the concern is real and understand its scope before I raise it, both so I'm not acting on hearsay and so I can speak concretely when I do.

**Second, reframe the conversation away from "compliance" and toward "does the control work."** The systems engineer's position is defensible only if the goal is audit compliance. I'd make the case that the goal is a safe product, and that a test which can't fail when the control is removed provides no evidence the control functions. I'd propose a concrete, bounded exercise: take the flagged tests and, for each, ask "if I disabled this control, would this test fail?" If the answer is no, the test needs to be revised or supplemented. That's an objective criterion that doesn't require anyone to concede fault — it's just a gap analysis.

**Third, scope the remediation pragmatically.** Not every flagged test necessarily needs to be rewritten from scratch — some may be salvageable by adding a fault-injection step or tightening the pass criterion. I'd prioritize by risk: controls mitigating the highest-severity hazards get addressed first, and I'd want the revised tests to include a "test the test" step (confirm the test fails with the control disabled) so we have evidence the test is capable of detecting the failure. I'd also want to understand *why* the tests were copied — was it schedule pressure, lack of a test-design template, unfamiliarity with the failure conditions? — because that determines whether this is a one-time cleanup or a process fix.

**Fourth, fix the process so it doesn't recur.** The root cause is that test design was decoupled from the risk analysis — the test author had a template and a requirement number, but not the failure condition. I'd add a step where the test author reviews the risk analysis entry for each control they're verifying and documents how the test creates the failure condition, and I'd add a review gate where someone checks that the test can actually fail. That's a small process change that catches this class of problem early.

**Finally, on the interpersonal side:** I'd avoid framing this as the systems engineer being wrong or the test engineer being right. The matrix did its job — it surfaced the links. The issue is that the *content* behind the links wasn't validated. I'd frame the remediation as strengthening the evidence, not fixing a failure, and I'd make sure the test engineer isn't singled out. The goal is a team that surfaces these issues early, not one that hides them.

**Possible follow-ups:**
- How would you handle it if the systems engineer escalates and argues that re-running tests will blow the schedule, and the program manager sides with them?
- What would you do if, after reviewing the flagged tests, you found that one of them actually does exercise the failure condition adequately — how would you handle the test engineer's credibility going forward?