# risk-requirements-traceability — Day 87

## Q1: How would you approach tracing a risk control measure that is implemented as a *combination of a hardware interlock and a firmware acknowledgment* — for example, a relay that physically removes power from a heater unless firmware continuously asserts an enable signal — when the hardware and firmware teams each own half of the control and neither team's requirements document references the other?

**Answer:** The core problem is that the control is a *contract* between two subsystems, and that contract has no owner. The right fix is to make the interface itself a first-class, traceable artifact rather than leaving each half implicit in its own document.

I would start by defining the control at the system level as a single risk control measure with a clear statement of the hazard it mitigates and the failure condition it must survive — for example, "loss of the enable signal, for any reason, must de-energize the heater." From there I would decompose it into two explicit sub-requirements: a hardware requirement describing the relay's default-de-energized behavior and its response to loss of the enable line, and a firmware requirement describing the conditions under which the enable is asserted and the maximum interval between assertions. Critically, both sub-requirements would carry a reference to the *same* parent risk control ID, so the traceability matrix shows them converging on one hazard rather than appearing as two unrelated items.

The interface between them — signal polarity, timing, what "continuously asserted" means numerically, and what happens on a stuck-at fault — belongs in an interface control document (ICD), and that ICD is what both teams trace to. That way, if the firmware team changes the assertion interval, the change is visible against the ICD and therefore against the risk control, not buried in a firmware spec nobody on the hardware side reads.

For verification, I would insist on at least one integrated test that exercises the *combination* — not just a hardware test of the relay and a firmware test of the assertion logic in isolation. The failure mode that matters most here is a single-point failure that defeats both halves at once (for example, a shared power rail or a shared clock), so the verification should also demonstrate that the two halves are genuinely independent, or explicitly document where they are not.

**Possible follow-ups:**
- If the two teams use different requirement numbering schemes, how do you keep the shared parent risk control ID stable across both documents?
- How would you verify the "continuously asserted" timing requirement without over-constraining the firmware design?

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a *timing requirement* — for example, "the system shall remove power from the heating element within 500 ms of detecting an over-temperature condition" — when the timing depends on a chain of hardware and firmware elements, each with its own latency, and the 500 ms budget is allocated across them?

**Answer:** A timing requirement like this is really a budget, and the traceability challenge is that no single element owns the whole number. If you trace the 500 ms only to the top-level requirement, you lose the ability to detect when one element in the chain quietly consumes more of the budget than it was allocated.

I would decompose the 500 ms into an explicit allocation across the chain — sensor response time, signal conditioning and ADC conversion, firmware detection and decision latency, and the actuator/relay response — and make each allocation a derived requirement owned by the responsible subsystem. Each derived requirement traces up to the parent timing requirement and down to its own verification activity. The parent requirement then has a verification that is either an integrated end-to-end test or a documented budget analysis that sums the verified element latencies, depending on what the risk file calls for.

The subtlety is worst-case versus typical. A budget built from typical latencies will pass on the bench and fail in the field. So each element's allocation should be specified as a worst-case bound, and the verification for each element should demonstrate that bound under the conditions that stress it — temperature extremes, supply variation, interrupt loading, and so on. If an element's worst-case latency can only be established by analysis rather than test, that is acceptable, but it needs to be stated as such with its assumptions, and the assumptions need to be traceable too.

I would also keep the budget visible as a single table in the traceability matrix, so that any change to one element's latency immediately shows how much margin remains. That turns the matrix from a compliance artifact into a design tool.

**Possible follow-ups:**
- How would you handle a situation where the integrated end-to-end test passes but one element's individual worst-case bound was never actually verified?
- If a later design change reduces the margin to near zero, what would you do before shipping?

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** Redundancy is where traceability most often quietly breaks down, because the risk analysis credits two controls while the documentation treats them as two unrelated features. The scheme needs to make the *pairing* explicit and, just as importantly, make the *independence claim* explicit, because that claim is what the risk reduction actually rests on.

I would model the hazard as the top-level node, with both risk control measures tracing to it, and a clear note in the risk file that the two are credited jointly. Each control then traces down through its own requirements and verification activities as normal. The key addition is a third traceability thread: an independence argument. That argument states what the two controls do *not* share — separate power domains, separate sensing paths, separate firmware tasks, separate clock sources — and it needs its own verification, because if the two controls share a common element, the redundancy credit is partly or wholly invalid.

Because the controls were added at different times by different teams, I would expect inconsistencies in naming, numbering, and assumptions. Rather than forcing a rewrite, I would add a cross-reference layer that maps both controls to the shared hazard ID and to the independence argument, and I would schedule a review specifically to confirm that the assumptions each team made about the other are still true. Redundancy added late is a common source of stale assumptions — one team may believe the other provides a watchdog that it does not.

Finally, I would make sure the verification plan tests the *combination*, including the case where one control has already failed. A redundant pair that has only ever been tested with both healthy has not really been verified as redundant.

**Possible follow-ups:**
- How would you document a partial loss of independence — for example, the two controls share a power rail but nothing else?
- If one of the two controls is later removed for cost reasons, what has to change in the traceability scheme?

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *manual* test with no automated logging — the operator toggles a signal and observes an LED — and the risk file treats it as objective evidence?

**Answer:** The traceability link exists, but the *quality* of the evidence behind it is weak, and that is the real issue. A manual observation can be legitimate objective evidence if it is controlled, but "the operator toggled a signal and saw the LED" as written is not — it has no defined pass/fail threshold, no record of the actual conditions, and no way to distinguish a genuine pass from an operator who expected to see the LED and did.

I would not necessarily replace the manual test — sometimes a manual test is the honest way to exercise a control, and automating it may cost more than it is worth. Instead I would tighten it until it produces defensible evidence. That means: a written procedure with explicit preconditions and a measurable acceptance criterion (not "LED illuminates" but "the output is de-energized within the specified time, confirmed by [instrument]"), a record of the actual measured result rather than a checkbox, and identification of the unit, firmware revision, and setup used. If the control's failure condition is subtle, I would add a deliberate negative check — confirm the test *fails* when the control is disabled — so the test is shown to be capable of detecting the failure.

Where the control is safety-critical and the manual method is inherently ambiguous, I would push to add instrumentation, even something as simple as a scope capture or a logged timestamp, so the evidence is objective rather than observational. The traceability matrix entry stays the same; what changes is that the verification activity now actually supports the claim being made about it.

**Possible follow-ups:**
- How would you decide which manual tests are worth automating and which are not?
- If the manual test was already used to close out a verification campaign, what would you do about the existing evidence?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is the failure mode that traceability is supposed to prevent, and it is more common than a missing link, because a missing link is visible and this one is not. The matrix looks complete, so it passes review, but nobody downstream understands *why* the requirement exists — which means the first time someone proposes simplifying or removing it, there is no argument against it.

My first move would be to treat it as a communication problem before a documentation problem. I would bring the systems engineer, the test engineer, and whoever owns the risk analysis entry into the same conversation, and walk the chain end to end out loud: here is the hazard, here is the control, here is the requirement that implements it, here is the test that verifies it. The goal is not to assign blame but to make the intent visible to the people who need it. In most cases the fix is small — a sentence in the requirement stating the hazard it mitigates, and a sentence in the test procedure stating the failure condition it is meant to detect.

Structurally, I would change the template so this cannot recur: every requirement derived from a risk control carries a reference to the risk control ID and a one-line statement of the hazard, and every verification activity carries the same reference plus the failure condition it must be capable of detecting. That way the intent travels with the artifact instead of living only in the risk file.

I would also add a lightweight review step — not a new gate, just a check during existing design reviews — where someone confirms that the requirement and the test still reflect the risk analysis entry, especially after changes. The point is to catch drift early, because intent decays quietly as documents are edited by people who never saw the original reasoning.

**Possible follow-ups:**
- How would you handle it if the risk analysis entry itself is vague and does not clearly state the hazard?
- What would you do if the test engineer, after reading the risk analysis, concludes the existing test does not actually exercise the failure condition?