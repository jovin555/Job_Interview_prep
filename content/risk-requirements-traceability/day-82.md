# risk-requirements-traceability — Day 82

## Q1: How would you approach tracing a risk control measure that is implemented as a *combination of a hardware interlock and a firmware acknowledgment* — for example, a relay that physically removes power from a heater unless firmware continuously asserts an enable signal — when the hardware and firmware teams each own half of the control and neither team's requirements document references the other?

**Answer:** The core problem is that the control is a *contract between two subsystems*, and neither subsystem's document expresses the contract. The right fix is to make the contract itself a first-class, owned artifact rather than an implicit assumption split across two teams.

I'd start by defining a single system-level requirement that states the control's safety intent and its observable behavior — something like "the heater shall be de-energized unless the firmware asserts an enable signal within the watchdog window." That requirement lives in the SRS and is the anchor that both teams trace to. From there, I'd decompose it into two interface-level requirements: one on the hardware side (the relay driver de-energizes when the enable line is not asserted within the window) and one on the firmware side (the firmware asserts the enable line at the required rate under all operating modes). Both of those child requirements trace up to the same parent, so the matrix shows the control as a single integrated measure with two implementation legs.

The key discipline is the *interface*: the enable signal's polarity, timing window, and failure behavior (what happens if the line floats, or if the firmware hangs) need to be captured in an interface control document, not left to each team's interpretation. The ICD is where the two halves meet, and it should be referenced by both the hardware design spec and the firmware requirements doc.

For verification, I'd insist on at least one integrated test that exercises the whole chain — fault injected, firmware stops asserting, relay drops out — because verifying each half in isolation can pass while the combination fails (e.g., a floating enable line that the hardware happens to read as "asserted"). The traceability matrix then shows: hazard → system requirement → hardware requirement + firmware requirement → ICD → integrated verification. That's the only structure that survives an audit question like "show me where this control is fully specified and fully verified."

**Possible follow-ups:**
- If the two teams use different numbering schemes, how do you keep the matrix readable without forcing a renumbering that would invalidate existing test records?
- What would you do if the integrated test reveals the control works, but only because of an undocumented timing coincidence between the two halves?

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a *timing requirement* — for example, "the system shall remove power from the heating element within 500 ms of detecting an over-temperature condition" — when the timing depends on a chain of hardware and firmware elements, each with its own latency, and the 500 ms budget is allocated across them?

**Answer:** A timing requirement that spans a chain is really a *budget*, and the traceability problem is that no single element owns the whole number. The approach is to decompose the budget explicitly and trace each allocation to the element that owns it.

First, I'd break the 500 ms into its constituent latencies: sensor response time, analog front-end settling, ADC conversion, firmware detection and decision logic, output driver turn-off, and relay or FET drop-out. Each of those gets a sub-requirement with its own allocated budget, and each sub-requirement traces up to the parent 500 ms requirement. The sum of the allocations, plus margin, must be less than or equal to the total — and that sum should be documented as an explicit calculation, not left implicit.

The subtlety is that some of these latencies are *worst-case* and some are *typical*, and the budget only holds if you use worst-case for every element. So the sub-requirements need to specify worst-case values, and the verification for each element needs to demonstrate the worst case, not the nominal. A firmware detection routine that takes 10 ms typically but 80 ms under heavy interrupt load is a different risk than one that's bounded at 20 ms.

For traceability, I'd want the matrix to show the parent timing requirement, the allocation table, each child requirement, and the verification activity for each child — plus one end-to-end test that measures the total from fault injection to power removal. The end-to-end test is what actually proves the budget; the per-element tests prove the allocations. If any element's measured worst case exceeds its allocation, the budget is broken and either that element needs margin added or the total needs to be revisited.

**Possible follow-ups:**
- How would you handle a case where the end-to-end test passes but one element's measured latency exceeds its allocated budget, because another element came in under budget?
- Where would you document the allocation table so it stays synchronized with the individual element requirements as they change?

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** Redundant controls are a common source of traceability confusion because the risk analysis treats them as a pair, but the engineering artifacts treat them as two separate things added at two separate times. The scheme needs to represent both the *pair* and the *individuals*.

I'd start by giving the risk control measure a single identifier in the risk management file that represents the *combined* mitigation — the hazard is mitigated by control A *and* control B, and the residual risk assessment assumes both are present. That identifier is the anchor. Then each individual control gets its own requirement (or set of requirements) in the SRS, and each of those traces up to the shared risk control identifier. So the matrix shows a many-to-one relationship: two requirements, one risk control.

The independence claim is the part that needs its own traceability. If the risk analysis credits both controls because they're independent, then the *independence* is itself a claim that needs to be verified — shared power rails, shared sensors, shared firmware modules, or a common cause failure can silently break it. I'd add a verification activity specifically for the independence claim, and trace it to the risk control identifier alongside the individual control verifications.

The "added at different times" issue is mostly a documentation hygiene problem: the earlier control may have been written before the risk analysis was updated to credit both. The fix is to reconcile the risk management file against the SRS and make sure the shared identifier exists and both requirements point to it. If the two controls were added by different teams, I'd also want a single owner for the combined control — someone accountable for the pair, not just for their half — because otherwise nobody notices if one half is later modified in a way that breaks the independence assumption.

**Possible follow-ups:**
- If the two controls share a common element (e.g., the same power rail), how does that change what the risk analysis can claim about redundancy?
- How would you handle a situation where one of the two controls is later removed or downgraded — what does the traceability scheme need to force you to re-examine?

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *manual* test with no automated logging — the operator toggles a signal and observes an LED — and the risk file treats it as objective evidence?

**Answer:** The issue isn't that manual tests are inherently invalid — plenty of legitimate verification is manual — it's that "operator observes an LED" produces evidence that is hard to audit, hard to reproduce, and easy to mis-record. The question I'd ask is: does the evidence actually demonstrate the control works, and can someone else independently confirm that from the record?

I'd start by looking at what the test is actually trying to prove. If the control's acceptance criterion is a measurable threshold — a trip point, a timing bound, a state transition — then an LED observation is probably insufficient because it doesn't capture the measurement. In that case the test needs an instrument: a scope, a data logger, a logic analyzer, or at minimum a timestamped record of the stimulus and response. The LED can stay as a convenience indicator, but the objective evidence needs to be the measurement.

If the control's acceptance criterion is genuinely binary and observable — "the relay opens when the fault is applied" — then a manual test can be acceptable, but the record needs to be strong enough to survive audit: the exact procedure, the equipment used and its calibration status, the pass/fail criterion stated explicitly, the operator's identity and date, and ideally a photo or video of the setup and result. The point is that the evidence should let a reviewer reconstruct what happened without having to trust the operator's memory.

The deeper question is whether the risk file is treating the manual test as *equivalent* to an automated test when it isn't. Manual tests have higher variability and lower repeatability, so for a control where the margin is tight or the failure mode is subtle, I'd push for instrumentation. For a control where the behavior is unambiguous and the margin is large, a well-documented manual test is defensible. The traceability matrix should record the test method honestly, so a reviewer can see it's manual and judge accordingly — not hide it behind a generic "verified" link.

**Possible follow-ups:**
- How would you decide whether a given manual test needs to be upgraded to an instrumented test, versus documented more rigorously as-is?
- If the manual test was already performed and the record is thin, what would you do — re-run it, or supplement it with analysis?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is the classic failure mode of traceability done as a documentation exercise rather than as a communication tool. The links are technically present, so an automated coverage check would pass — but the *meaning* has been lost, which means the requirement and the test may not actually address the hazard the control was meant to mitigate.

My first move would be to bring the three people together — the systems engineer, the test engineer, and whoever owns the risk analysis entry — and walk through the control from hazard to verification as a group. The goal isn't to assign blame; it's to surface the gap. In most cases, the requirement will turn out to be *close* but not quite right (it describes the function but not the failure condition), and the test will turn out to exercise the function under nominal conditions rather than the fault condition. That's a fixable problem once it's visible.

The structural fix is to change how the artifacts are written so the intent travels with them. Every requirement derived from a risk control should carry a reference to the risk control identifier and a one-line statement of the hazard it mitigates — not just a number, but the actual safety intent. Every verification activity should state the failure condition it's designed to detect, so a reviewer can see whether the test actually stresses that condition. And the risk analysis entry should be a living document that the systems and test engineers are expected to read, not a file that only the quality team opens.

I'd also add a review gate: before a verification activity is considered complete, someone who understands the hazard — not just the requirement — should confirm the test exercises the failure condition. That's a lightweight check that catches this class of problem early, before it becomes an audit finding.

The behavioral part is that I'd frame this as a process gap, not an individual failure. The systems engineer and test engineer were each doing their job as defined; the process didn't require them to read the risk analysis. Fixing the process is more durable than fixing the individuals.

**Possible follow-ups:**
- How would you retrofit this intent-carrying approach onto a project that's already mid-verification, without invalidating completed test records?
- If the risk analysis entry itself is vague about the failure condition, where do you start — fixing the risk analysis, or fixing the requirement?