# risk-requirements-traceability — Day 13

## Q1: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a design review rather than a test — and the design review criteria don't explicitly mention the risk control's failure condition?

**Answer:** This is a common gap when design reviews are used as verification evidence. The first step is to assess whether the design review actually provides objective evidence that the risk control mitigates the hazard — not just that the design exists, but that the specific failure condition is addressed. I'd examine the review checklist and minutes to see if the failure mode was explicitly discussed. If it wasn't, the review doesn't constitute adequate verification for that risk control.

The fix is to strengthen the design review criteria so they explicitly reference the risk control's failure condition. For example, if the risk control is a hardware-based overcurrent limiter, the review checklist should include a specific item like "verify that the current-limiting circuit activates before component damage occurs, under worst-case load conditions." This turns the review from a general design assessment into a targeted verification activity.

I'd also consider whether a design review alone is sufficient for this particular control. For some controls — like component derating or creepage distances — analysis and review are the appropriate verification methods. For others, a functional test is necessary. The key question is: does the review provide objective evidence that the control works as intended, or does it only confirm the design intent? If it's only design intent, I'd supplement with analysis (e.g., calculations, simulation) or a targeted test.

Finally, I'd document this decision in the traceability matrix, noting the verification method as "design review + analysis" and referencing the specific review records and analysis documents as evidence.

**Possible follow-ups:**
- How would you decide whether a design review is sufficient verification for a given risk control, versus requiring a functional test?
- What would you do if the design review already happened and the records don't show the failure condition was discussed — would you re-run the review or accept it with a gap analysis?

---

## Q2: How would you approach establishing traceability for risk control measures that are implemented through component selection and derating — for example, choosing a capacitor with a voltage rating well above the maximum expected stress — when these controls don't map cleanly to a functional requirement or a test?

**Answer:** Component derating and selection-based controls are a special category because they're verified through analysis and design rules rather than functional tests. The key is to make these controls explicit rather than implicit. I'd start by documenting the derating policy as a design requirement — for example, "all capacitors shall be derated to at least 50% of maximum rated voltage under worst-case operating conditions." This gives the control a traceable requirement that can be linked to the hazard it mitigates.

For the traceability scheme, I'd create a link from the hazard → risk control measure → design requirement (the derating rule) → verification activity (design review or analysis). The verification evidence would be the design review records showing that component selections were checked against the derating policy, or a derating analysis document that calculates stress levels for each critical component.

The challenge is that these controls are often applied across many components, so I'd structure the traceability at the policy level rather than component-by-component. The risk management file would reference the derating policy as the risk control, and the design review would verify compliance with that policy. If a specific component is critical to a particular hazard — say, a capacitor that prevents a dangerous voltage transient — I'd create a component-specific requirement and trace that individually.

I'd also make sure the design review checklist explicitly includes derating verification, so the review records provide objective evidence. Without that, the control exists only in the designer's intent, which isn't verifiable.

**Possible follow-ups:**
- How would you handle a situation where the derating policy is followed for most components, but one component is exempted for performance reasons — how would you trace that decision?
- Would you treat derating-based controls differently in the risk management file versus the SRS?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** This is where traceability gets genuinely difficult, because the risk control isn't a single requirement or a single test — it's an emergent property of the system. I'd approach this in layers.

First, I'd define the system-level hazard and the system-level risk control at the top layer. For example, "hazard: motor overspeed" → "risk control: coordinated shutdown of motor drive when any node detects a fault condition." This system-level control would be traced to a system-level requirement that captures the coordinated behavior.

Second, I'd decompose the control into node-level requirements. Each microcontroller gets a requirement for its specific role — one node detects the fault, another node executes the shutdown, a third node provides a heartbeat that indicates health. Each of these node-level requirements traces up to the system-level control.

Third, I'd address the coordination mechanism itself. The communication protocol between nodes becomes a critical element — for example, a requirement that "fault messages shall be transmitted within X ms and shall be prioritized over routine traffic." This protocol requirement is often where traceability breaks down, because it's neither purely hardware nor purely firmware — it's an interface requirement.

For verification, I'd need both node-level tests (each node responds correctly to a fault message) and system-level tests (a fault injected at one node results in coordinated shutdown across the system). The system-level test is essential because it verifies the emergent behavior — timing, message ordering, and fail-safe behavior if the bus is congested.

Finally, I'd pay special attention to failure modes of the coordination itself — what happens if the fault message is lost, or if a node is unresponsive? These need their own risk controls and traceability, because the coordination mechanism introduces new failure modes.

**Possible follow-ups:**
- How would you handle traceability for the communication protocol itself — is it a requirement, a design element, or both?
- What if the nodes are developed by different teams with separate requirements documents — how would you maintain traceability across those boundaries?

---

## Q4: How would you approach determining whether a risk control measure that is implemented as a combination of hardware and firmware — for example, a hardware sensor detecting an over-temperature condition and firmware deciding to shut down a motor — should be verified as a complete system, or whether separate hardware and firmware verification is sufficient?

**Answer:** The short answer is that you need both, but they serve different purposes. Separate hardware and firmware verification establishes that each element works correctly in isolation — the sensor actually detects the temperature threshold, and the firmware actually executes the shutdown sequence when given the appropriate input. This is necessary but not sufficient.

The system-level verification is essential because it exercises the interface between hardware and firmware — the signal path, timing, and interpretation of the sensor output. A classic failure mode is that the hardware works correctly and the firmware works correctly, but the firmware misinterprets the hardware signal — for example, an analog sensor output that's slightly out of the expected range, or a digital signal with marginal timing that the firmware samples incorrectly.

I'd structure the verification in three layers. First, hardware-level verification: the sensor detects the over-temperature condition and produces the correct output signal. Second, firmware-level verification: the firmware, when presented with the sensor signal (possibly simulated), executes the correct shutdown sequence. Third, system-level verification: the actual sensor, connected to the actual firmware, produces a shutdown when the temperature exceeds the threshold.

The system-level test is where you catch integration issues — signal integrity, noise, timing margins, and firmware timing relative to hardware behavior. It's also where you verify the end-to-end response time, which is often a critical parameter for the risk control.

That said, I'd also consider the risk analysis. If the hazard requires a fast response time, the system-level test is non-negotiable. If the hazard is less time-critical, separate verification might be acceptable, but I'd still want at least one system-level test to confirm the integration.

**Possible follow-ups:**
- How would you handle a situation where the system-level test is difficult to perform — for example, the over-temperature condition is hard to create safely in a test environment?
- What if the hardware and firmware teams have different verification schedules — how would you sequence the verification activities?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by inspection" — meaning someone looked at the design and declared it acceptable. The quality manager argues that inspection is not objective evidence and demands that all risk controls be verified by test. The systems engineer argues that some controls, like component derating or PCB layout rules, can only be verified by inspection, and that requiring tests would be impractical and unnecessary. How would you resolve this disagreement?

**Answer:** I'd start by acknowledging that both sides have valid points. The quality manager is right that inspection can be subjective and may not provide the rigor needed for safety-critical controls. The systems engineer is right that some controls — like creepage distances or component derating — are inherently design-rule-based and can't be meaningfully tested in a functional sense.

The resolution is to distinguish between different types of verification evidence and make each type rigorous in its own way. For design-rule-based controls, I'd propose converting "inspection" into "structured analysis with documented criteria." Instead of someone looking at the design and declaring it acceptable, we'd create a checklist with specific, measurable criteria — for example, "verify that the creepage distance between mains and SELV circuits meets or exceeds the value specified in the standard, measured on the actual PCB layout." The reviewer would document the measurement and the pass/fail result against the specific criterion.

This turns inspection into a form of analysis — it's still not a functional test, but it's objective, repeatable, and documented. The key is that the criteria must be specific enough that two different reviewers would reach the same conclusion.

For controls that genuinely require functional testing — like a watchdog timer or an overcurrent limiter — I'd insist on tests. The distinction is whether the control's effectiveness can be demonstrated through analysis of the design, or whether it requires observing the system's behavior under fault conditions.

I'd also propose a middle path: for some controls, a combination of analysis and a limited functional test. For example, for a derating-based control, the analysis verifies the component selection, and a functional test at worst-case conditions verifies that the component actually survives the stress. This gives the quality manager objective evidence while acknowledging the systems engineer's point about practicality.

Finally, I'd document the verification strategy in the verification plan, clearly stating which method applies to each control and why. This turns the disagreement into a documented, defensible decision.

**Possible follow-ups:**
- How would you handle a situation where the quality manager still insists on functional tests for design-rule-based controls, even after you've proposed structured analysis?
- What criteria would you use to decide whether a control can be verified by analysis versus requiring a functional test?