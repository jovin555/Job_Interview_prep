# risk-requirements-traceability — Day 78

## Q1: How would you approach tracing a risk control measure that is implemented as a *combination of a hardware interlock and a firmware acknowledgment* — for example, a relay that physically removes power from a heater unless firmware continuously asserts an enable signal — when the hardware and firmware teams each own half of the control and neither team's requirements document references the other?

**Answer:** The core problem is that the control is a *handshake*, not two independent features, so tracing it as two separate requirements in two separate documents will always leave a gap at the boundary. I'd start by treating the handshake itself as a first-class system-level requirement — something like "the heater shall be de-energized unless the firmware asserts a periodic enable signal within the watchdog window" — and give that requirement its own identifier in the SRS. That system requirement is the anchor that both teams trace up to.

From there, I'd decompose it into two derived requirements: a hardware requirement describing the relay drive logic, the default-de-energized state, and the timeout behavior of the enable path; and a firmware requirement describing the assertion cadence, the conditions under which the firmware stops asserting, and the failure behavior. Each derived requirement carries a reference back to the parent system requirement, so the traceability path is hazard → system requirement → hardware derived requirement and firmware derived requirement → verification activities.

The critical part is the interface. I'd capture the electrical and timing contract between the two halves in an interface control document — signal levels, assertion period, maximum tolerable gap, what happens on the hardware side if the signal stops, what the firmware guarantees about jitter. The ICD becomes the shared reference that both requirements documents point to, which is what prevents the "neither document references the other" problem.

For verification, I'd insist on at least one integrated test that exercises the handshake end-to-end — deliberately stopping the firmware assertion and confirming the relay drops out within the specified time — in addition to the separate hardware and firmware unit-level tests. The unit tests prove each half works; only the integrated test proves the *control* works.

**Possible follow-ups:**
- If the hardware team changes the relay driver's default state during a redesign, how would your traceability scheme surface the impact on the firmware requirement?
- How would you decide whether the handshake timing belongs in the ICD, the system requirement, or both?

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a *timing requirement* — for example, "the system shall remove power from the heating element within 500 ms of detecting an over-temperature condition" — when the timing depends on a chain of hardware and firmware elements, each with its own latency, and the 500 ms budget is allocated across them?

**Answer:** A timing requirement like this is really a *budget*, and the traceability challenge is that no single element owns the whole number. I'd start by decomposing the 500 ms into an allocated budget across the chain — sensor response time, signal conditioning and ADC conversion, firmware detection and decision latency, output driver response, and relay or switch actuation time. Each allocation becomes a derived requirement owned by the responsible element, and each carries a reference back to the parent timing requirement.

The key discipline is that the allocations must sum to less than the total with margin, and that margin should be explicit rather than implicit. If the allocations add up to 480 ms with 20 ms of margin, that margin is itself a design decision that should be documented and justified — it's the buffer that absorbs unit-to-unit variation, temperature effects, and component tolerance.

For traceability, I'd want each allocated latency to be verifiable at its own level — a bench measurement of the sensor response, a firmware timing measurement of the detection path, a characterization of the driver — and then a system-level test that measures the end-to-end time under worst-case conditions. The system-level test is what actually verifies the requirement; the element-level measurements are what let you diagnose *where* the budget is being consumed if the system test fails.

One thing I'd be careful about: the worst-case condition for a timing budget is often not the nominal operating point. Low supply voltage, cold temperature, or a heavily loaded processor can each stretch a different element in the chain, so the verification plan needs to identify which corner cases stress which element and test accordingly.

**Possible follow-ups:**
- How would you handle a situation where the system-level test passes at nominal but the sum of the element-level worst cases exceeds the budget?
- If a component vendor changes a part with a different propagation delay, how would your traceability scheme flag the affected allocations?

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** The first thing I'd want to establish is whether the risk analysis is crediting the two controls as *independent* — because if it is, then independence is itself a claim that needs to be traced and verified, not just assumed. Two controls that share a power supply, a common sensor, or a common firmware module are not independent, and the traceability scheme should make that visible.

Structurally, I'd create a single risk control entry in the risk management file that references both implementations, and then trace each implementation to its own requirement and its own verification activity. The risk control entry is the parent; the two implementations are children. That way the matrix shows one hazard mitigated by two paths, rather than two unrelated controls that happen to point at the same hazard.

Because the two controls were added at different times by different teams, I'd expect the documentation to be inconsistent — different numbering, different levels of detail, possibly different assumptions about the operating envelope. I'd normalize them by requiring each to state the same things: what failure condition it detects, what action it takes, what its coverage is, and what it assumes about the other control. The "what it assumes about the other control" field is the one that usually exposes hidden coupling.

For verification, I'd want each control verified independently — including a test that disables the other control and confirms this one still functions — plus a test that confirms the two together achieve the claimed risk reduction. The independence claim is what makes the redundancy meaningful, so it deserves its own verification evidence.

**Possible follow-ups:**
- How would you handle a situation where the two controls turn out to share a common element, undermining the independence claim?
- If one control was added later as a corrective action after a field issue, how would you document the relationship between the original control and the added one?

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *manual* test with no automated logging — the operator toggles a signal and observes an LED — and the risk file treats it as objective evidence?

**Answer:** The traceability link exists, but the *quality* of the evidence is the issue. A manual test with no logging can be legitimate objective evidence if it's controlled properly — the problem is that "operator toggles a signal and observes an LED" as described doesn't demonstrate that the observation was accurate, repeatable, or tied to a specific acceptance criterion.

I'd start by asking what the test is actually supposed to prove. If the risk control is "the system shall indicate a fault condition via a visual indicator," then observing the LED is directly relevant — but the test procedure still needs a measurable acceptance criterion (the LED illuminates within X ms of the fault, at a specified brightness or color) and a record of what was observed. If the risk control is something else and the LED is just a proxy, then the test may not be verifying the control at all.

Assuming the test is legitimate but under-documented, I'd strengthen it rather than replace it. That means: a written procedure with explicit steps and acceptance criteria, a record of the actual observation (a photo, a signed checklist, or better, an instrumented measurement), and a note of the equipment and setup used. For a risk control, I'd also want to know whether the test was performed on production-representative hardware and whether it exercised the failure condition rather than just the nominal path.

Where practical, I'd push to add instrumentation — a scope capture, a logic analyzer trace, or a firmware log — because that converts a subjective observation into a recorded measurement. But I wouldn't insist on automation for its own sake; a well-controlled manual test with a clear procedure and a recorded result can be perfectly valid evidence. The failure mode to avoid is a test that passes because the operator expected it to pass, with nothing in the record to distinguish that from a genuine verification.

**Possible follow-ups:**
- How would you decide whether a manual test needs to be repeated by a second operator to be considered objective evidence?
- If the LED observation is the only evidence for a risk control, what additional evidence would you want before accepting it?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is a documentation-integrity problem disguised as a traceability problem. The links are technically present, so a coverage check would pass — but the traceability isn't doing its job, because the people writing the requirement and the test don't understand *why* the control exists. That's exactly the situation where a control can be implemented and verified in a way that satisfies the letter of the requirement but misses the hazard it was meant to mitigate.

I'd start by not treating this as anyone's fault. It's a process gap: the workflow allowed requirements and tests to be authored without a mandatory review of the risk analysis entry. Blaming the systems engineer or the test engineer would just make people defensive and hide the next instance.

The fix has two parts. First, a short-term correction: for each affected control, I'd bring the systems engineer, the test engineer, and whoever owns the risk analysis entry into the same conversation, walk through the hazard and the intended control, and confirm that the requirement and the test actually reflect that intent. Where they don't, I'd revise them — and I'd expect some of them not to, because the intent was never communicated.

Second, a process change to prevent recurrence. The most effective lever is usually to make the risk analysis entry a required input to both requirement authoring and test authoring — not just a downstream reference. Practically, that could mean a review checklist item, a required field in the requirements tool that links to the risk entry and must be acknowledged, or a joint review at the point where a risk control is first decomposed into requirements. I'd also want the traceability review to check not just that links exist but that the linked artifacts are *consistent* — a reviewer should be able to read the hazard, the requirement, and the test in sequence and see a coherent story.

I'd measure success by spot-checking: pick a few controls at random and ask the requirement author and test author to explain, without looking, what hazard the control mitigates. If they can, the intent survived. If they can't, the process still isn't working.

**Possible follow-ups:**
- How would you handle a situation where the test engineer, after reading the risk analysis, concludes the existing test is inadequate and needs to be rewritten late in the project?
- What would you do if the risk analysis entry itself is vague about the intended control, so there's no clear intent to communicate?