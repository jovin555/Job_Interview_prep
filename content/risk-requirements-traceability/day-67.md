# risk-requirements-traceability — Day 67

## Q1: How would you approach tracing a risk control measure that is implemented as a *combination* of a hardware interlock and a firmware acknowledgment — for example, a relay that physically removes power from a heater unless firmware continuously asserts an enable signal — when the hardware and firmware teams each own half of the control and neither team's requirements document references the other?

**Answer:** The core problem is that the control is a *contract* between two subsystems, and a contract that lives in neither party's document is effectively unowned. The right fix is to elevate the control to a single system-level requirement that states the safety intent and the interface behavior, then let each team derive their own lower-level requirement from it.

Concretely, I would:

1. **Define one system-level safety requirement** that captures the integrated behavior — e.g., "the heater shall be de-energized within a bounded time unless a valid enable signal is continuously present." This is the requirement that traces to the hazard and to the risk control measure in the risk file.
2. **Derive two child requirements** from it: a hardware requirement (the relay's default state, the de-energize path, the timing of the physical cutoff) and a firmware requirement (the enable signal's period, duty, or heartbeat semantics, and what "continuously present" means at the interface).
3. **Cross-reference both children back to the parent** and to each other, so neither document is complete without the other. The parent is the single point of truth; the children are the implementation split.
4. **Define the interface explicitly** — signal name, polarity, timing, failure mode (what happens if the enable line is stuck high, stuck low, or floating). This is where an ICD earns its keep: the interface itself is part of the risk control, so it needs its own definition and its own verification.
5. **Verify at the system level** for the integrated behavior, and at the module level for each half. A hardware-only test proves the relay drops out when the enable is removed; a firmware-only test proves the enable is asserted correctly; neither alone proves the *combination* works, so the system test is the one that actually closes the risk control.

The key insight is that "hardware owns half, firmware owns half" is a documentation problem, not a design problem. The design is fine; the traceability is broken because nobody wrote down the contract. Fix the contract first, then the traceability falls out of it.

**Possible follow-ups:**
- If the two teams use different requirement numbering schemes, how do you keep the cross-references stable as both documents evolve?
- What happens to the traceability when the interface definition changes — say, the enable signal polarity is inverted — and only one team updates their document?

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a *timing requirement* — for example, "the system shall remove power from the heating element within 500 ms of detecting an over-temperature condition" — when the timing depends on a chain of hardware and firmware elements, each with its own latency, and the 500 ms budget is allocated across them?

**Answer:** A timing requirement that spans a chain is really a *budget*, and the traceability has to follow the budget, not just the endpoints. If you only trace "hazard → 500 ms requirement → system test," you've hidden all the places where the budget can be blown.

I would approach it in layers:

1. **Decompose the budget explicitly.** Break the 500 ms into the contributing latencies: sensor response time, analog signal conditioning, ADC conversion, firmware detection and decision, output driver actuation, and relay/contactor mechanical release. Each gets an allocated slice with its own margin. The allocation itself is a design artifact and should be traceable.
2. **Create a child requirement per element.** Each slice becomes a requirement on the responsible subsystem — e.g., "the firmware shall assert the cutoff output within X ms of the ADC flag being set." Each child traces up to the parent timing requirement and down to its own verification.
3. **Verify each slice and the total.** Each element's latency is verified individually (often by measurement or analysis), and the *sum* is verified at the system level under worst-case conditions — because the worst case is rarely the sum of the typicals. Temperature, supply voltage, clock tolerance, and component aging all shift the individual latencies, and the system test has to exercise the combination.
4. **Trace the budget to the risk file.** The risk control measure is "remove power within 500 ms"; the budget allocation is the evidence that the control is achievable with margin. If any slice grows during development, the traceability should make it obvious that the parent requirement is now at risk.

The trap here is treating the 500 ms as a single testable number. It is testable, but it's only *verifiable* if you can show where the time goes and that no single element can consume the whole budget. The traceability matrix should make the allocation visible, not just the endpoint.

**Possible follow-ups:**
- How would you handle a situation where one element's measured latency exceeds its allocated slice but the total still passes?
- If the timing budget is verified by analysis rather than test for some elements, how do you keep that consistent with the risk file's evidence expectations?

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls are owned by different teams and were added at different times in the project?

**Answer:** Redundant controls are a classic traceability trap because the risk file credits them as a *pair*, but the requirements and tests treat them as separate items. The scheme has to preserve both views: the individual control and the combined effect.

I would structure it as:

1. **One hazard, one risk control measure entry, two implementation paths.** The risk file should record the control as a single measure with a stated independence assumption, then reference both implementations. If the risk analysis credits both, the independence claim is itself a safety argument that needs evidence — shared power, shared clock, shared sensor, or shared firmware all break it.
2. **Two sets of derived requirements**, one per implementation, each tracing up to the same risk control measure. Each team owns their own requirement, but both point to the same parent.
3. **A combined verification activity** that demonstrates the *pair* behaves as the risk analysis assumes — including the failure of one path. If the risk analysis says "either control alone is sufficient," the test should show that; if it says "both are needed," the test should show that too. The independence claim needs its own verification, often by analysis or fault injection.
4. **A note in the traceability matrix** that flags the redundancy and the independence assumption, so an auditor or a new engineer can see why two requirements exist for one hazard and what would invalidate the credit.

The "added at different times" part is the real risk: the second control was likely added later, possibly by a different team, and the first team may not know it exists. The traceability scheme should make the pairing explicit so that a change to either control triggers a review of the other — because removing one half of a redundant pair silently changes the safety argument.

**Possible follow-ups:**
- How would you verify the independence assumption if the two controls share a common power rail?
- If one of the redundant controls is later removed for cost reasons, what does the traceability scheme need to show to justify the change?

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity's acceptance criterion is stated as "the control functions as designed" rather than as a measurable pass/fail threshold?

**Answer:** "Functions as designed" is not an acceptance criterion — it's a placeholder that defers the real question. The verification activity exists to produce objective evidence that the control mitigates the hazard, and that requires a measurable threshold tied to the risk analysis.

I would treat this as a requirements-quality defect and fix it at the source:

1. **Go back to the risk analysis.** The risk control measure was credited with reducing a hazard to an acceptable level. That credit implies a *performance* — a trip point, a response time, a detection threshold, a coverage. The acceptance criterion should be derived from that performance, not from the design's intent.
2. **Restate the criterion measurably.** Instead of "the control functions as designed," write something like "the output is de-energized within X ms of the fault condition being applied, with the fault applied at the worst-case point in the operating cycle." The number comes from the risk analysis and the design margin, not from convenience.
3. **Define the fault condition explicitly.** A measurable criterion is meaningless without a defined stimulus. The test procedure should state how the fault is injected, at what severity, and under what operating conditions — because "the control works" under nominal conditions says nothing about whether it works under the conditions the risk analysis actually cares about.
4. **Re-verify.** If the existing test only demonstrated "functions as designed," it likely didn't stress the failure condition. The traceability link stays, but the verification activity needs to be rewritten and re-run.

The broader point is that traceability without measurable acceptance criteria is a paper exercise. The link from risk control to verification is only meaningful if the verification can *fail* — and it can only fail if the criterion is a number, a state, or a bounded behavior, not a judgment.

**Possible follow-ups:**
- How would you handle a control where the "performance" is inherently qualitative — say, a labeling or instructional control?
- If the original test passed under the vague criterion, do you need to re-run it, or can you argue the design is unchanged?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is the failure mode that traceability is supposed to prevent, and it happens when the links are treated as an administrative artifact rather than a shared understanding. The matrix is complete, but the *reason* for the control has been dropped somewhere between the risk file and the test bench.

I would handle it in three moves:

1. **Make the intent visible in every artifact.** The requirement should carry a short rationale that references the hazard and the risk control measure — not just a number. The test procedure should state what failure condition it is exercising and why. When the intent is written down at each step, the next person doesn't have to reconstruct it from the risk file.
2. **Bring the authors together on the specific control.** Not a general process meeting — a focused review of this control, with the risk analyst, the systems engineer, and the test engineer in the same room, walking the chain from hazard to test. The goal is to confirm that the test actually exercises the failure condition the risk analysis identified, and that the requirement's acceptance criterion is derived from the risk control's performance, not from the design's convenience.
3. **Fix the process, not just the instance.** If this happened once, it will happen again. The root cause is usually that the risk analysis is treated as a separate document owned by a separate person, and the requirements and test authors never see it. The fix is to make the risk control measure's intent a required field in the requirement and the test — a one-line rationale that forces the author to look it up.

The behavioral dimension is that this is not a blame situation. The systems engineer and test engineer did their jobs; the process didn't connect them to the risk analysis. The right response is to close the gap without making anyone defensive, because the next project will have the same structural problem unless the process changes.

**Possible follow-ups:**
- How would you audit for this class of problem across the whole matrix, rather than fixing it one control at a time?
- If the test engineer pushes back and says the test passes and the matrix is complete, how do you make the case that something is actually wrong?