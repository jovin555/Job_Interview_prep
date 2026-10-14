# risk-requirements-traceability — Day 85

## Q1: How would you approach tracing a risk control measure that is implemented as a *combination of a hardware interlock and a firmware acknowledgment* — for example, a relay that physically removes power from a heater unless firmware continuously asserts an enable signal — when the hardware and firmware teams each own half of the control and neither team's requirements document references the other?

**Answer:** The core problem here is that the control is a *contract* between two subsystems, and that contract has no single owner. The right fix is to make the contract itself a first-class artifact rather than leaving it implicit in two separate documents.

I would start by defining an interface-level requirement that describes the *combined* behavior: "The heater shall be de-energized unless the firmware asserts the enable signal within the required window, and the relay shall default to the de-energized state on loss of the enable signal." That requirement lives at the system level, not in either team's document, and it is the thing the risk file traces to. From there, each team derives their own sub-requirements — the hardware team owns "the relay shall de-energize within X ms of the enable signal being removed," the firmware team owns "the firmware shall assert the enable signal only while all preconditions are satisfied" — and both sub-requirements trace *up* to the system-level contract.

The traceability matrix then has a clear shape: hazard → system-level risk control → interface requirement → hardware sub-requirement and firmware sub-requirement → verification activities for each. The key discipline is that the interface requirement is the anchor; without it, each team's document is internally consistent but the *integration* is unverified. I would also make sure the verification plan includes an integration test that exercises the combined behavior — for example, removing the enable signal and confirming the relay drops out — because neither team's unit-level test can prove the contract holds.

**Possible follow-ups:**
- Who owns the interface requirement — systems engineering, or one of the two subsystem teams?
- How would you handle a change to the relay's dropout time if only the hardware team's document is updated?

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a *timing requirement* — for example, "the system shall remove power from the heating element within 500 ms of detecting an over-temperature condition" — when the timing depends on a chain of hardware and firmware elements, each with its own latency, and the 500 ms budget is allocated across them?

**Answer:** A timing requirement like this is really a *budget*, and the traceability challenge is that no single element owns the whole number. The approach I would take is to decompose the budget explicitly and trace each allocation to its owner.

First, break the 500 ms into the contributing latencies: sensor response time, analog signal conditioning, ADC conversion, firmware detection and decision logic, relay driver response, and relay mechanical dropout. Each of these becomes a sub-requirement with its own allocated budget and its own verification activity. The system-level requirement traces down to each allocation, and each allocation traces to a verification — a datasheet analysis for the sensor, a bench measurement for the analog chain, a timing test for the firmware path, and so on.

The critical discipline is that the *sum* of the allocations must be less than the system-level budget with margin, and that margin itself should be documented. If the allocations add up to 480 ms against a 500 ms budget, that 20 ms is the design margin, and it needs to be justified — for example, against component tolerance and temperature variation. I would also insist on an end-to-end integration test that measures the actual total latency under worst-case conditions, because the sum of individually-verified latencies is not the same as the verified system latency when there are interactions (interrupt latency, bus contention, scheduling jitter).

**Possible follow-ups:**
- How would you verify the firmware's contribution to the latency without instrumenting the production firmware?
- What happens to the traceability if one element's latency turns out to be higher than allocated during verification?

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** Redundant controls are a common source of traceability confusion because the risk file treats them as a *pair* while the engineering artifacts treat them as two separate things. The scheme needs to preserve both views.

I would model the risk control measure as a single entry in the risk file with two *implementing* controls beneath it, each traced to its own requirement and its own verification activity. The traceability matrix then shows: hazard → risk control measure → control A (requirement, design element, verification) and control B (requirement, design element, verification). The risk file's claim of redundancy is only valid if the two controls are genuinely independent, so I would also add an explicit *independence* argument to the risk file — for example, they don't share a power rail, a microcontroller, or a common failure mode — and trace that argument to whatever analysis or test supports it.

The "added at different times" aspect matters because the second control may have been added without re-examining the first. I would treat the pair as a single logical control for the purposes of residual risk evaluation, and make sure the verification plan covers both the individual function of each control *and* the scenario where one has failed and the other is expected to carry the mitigation alone. That last test is often missing, and it's the one that actually proves the redundancy claim.

**Possible follow-ups:**
- How would you verify the independence of the two controls, as opposed to just their individual function?
- If one control is later removed, how does the traceability scheme make the impact on residual risk visible?

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *manual* test with no automated logging — the operator toggles a signal and observes an LED — and the risk file treats it as objective evidence?

**Answer:** The issue isn't that manual tests are inherently invalid — many legitimate verification activities are manual — it's that the *evidence* produced by this test is weak. "The operator observed the LED" is a subjective observation with no record of the actual signal timing, no measurement of the response, and no way to demonstrate that the test was performed under the specified conditions. For a risk control measure, that's usually not sufficient objective evidence.

I would first ask what the test is actually trying to prove. If the risk control is "the system shall de-energize the output within X ms of a fault," then an LED observation can't verify the timing at all — it can only confirm that *something* happened. In that case the test needs to be redesigned to capture the relevant measurement: an oscilloscope trace, a logic analyzer capture, or a firmware-instrumented timestamp, with the acceptance criterion stated as a measurable threshold.

If the control genuinely is binary — for example, "the interlock shall prevent the connector from being mated while power is applied" — then a manual test may be acceptable, but the *evidence* still needs to be objective: a documented procedure with defined pass/fail criteria, a record of the test conditions, and a signed result. The distinction I would draw is between a manual test with objective acceptance criteria and a manual test with subjective observation. The former can be valid evidence; the latter generally cannot, and I would push to either strengthen the test or replace it with an instrumented one.

**Possible follow-ups:**
- How would you decide which manual tests are acceptable as-is and which need to be instrumented?
- What would you do if instrumenting the test is impractical because the signal is internal to a potted assembly?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is a classic case where the traceability matrix is *structurally* complete but *semantically* empty — the links exist, but the people who created them didn't share an understanding of what the control is for. The first thing I would do is resist the temptation to treat it as a documentation problem. It's a communication problem, and fixing the documents without fixing the communication will just produce the same situation again on the next project.

My approach would be to bring the three parties — risk, systems, and test — into the same room and walk through the control together. I'd start from the hazard and the risk analysis entry, and ask the systems engineer to explain how their requirement implements the control, and the test engineer to explain how their test proves the requirement is met. If either of them can't articulate the link to the hazard, that's the gap to close. Often the requirement is functionally correct but doesn't capture the *safety intent* — for example, it says "the motor shall be disabled within 100 ms of a fault" without saying *why*, and the test verifies the timing but not the fault detection path.

Once the intent is clear, I would update the artifacts so the intent is visible: the requirement should reference the risk control it implements, the test should reference the failure condition it's designed to exercise, and the risk file should reference both. But the more important fix is process — I would introduce a lightweight review step where risk, systems, and test jointly review new risk control measures before they're baselined, so the intent is shared from the start rather than reconstructed after the fact.

**Possible follow-ups:**
- How would you handle it if the systems engineer insists the requirement is fine and the test engineer insists the test is fine, and neither sees a problem?
- What would you change in the traceability tooling to make this kind of gap more visible earlier?