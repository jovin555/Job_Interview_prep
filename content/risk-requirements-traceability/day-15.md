# risk-requirements-traceability — Day 15

## Q1: How would you approach handling a situation where a risk control measure is implemented as a combination of hardware and firmware, but the hardware and firmware teams have each created their own separate traceability matrices that don't reference each other, and neither matrix alone shows the complete path from hazard to verification?

**Answer:** The first step is to recognize that this is a systems-level integration problem, not a documentation problem. Separate traceability matrices for hardware and firmware are common, but for a risk control that spans both domains, neither matrix is complete on its own. I would start by identifying the specific risk control measures that span the hardware/firmware boundary — for example, a hardware sensor detecting a fault condition and firmware deciding on the response. For each such control, I would map the full chain: system-level hazard → risk control measure → hardware element (sensor, comparator, etc.) → firmware element (decision logic, timeout, state machine) → verification activities on each side.

The key is to establish a "bridge" document or a shared section in the system-level traceability matrix that explicitly links the hardware and firmware artifacts. This could be as simple as adding cross-reference columns: the hardware matrix references the firmware requirement ID and vice versa. More robustly, I would create a system-level view that shows the complete chain for each cross-domain risk control, even if the detailed requirements remain in the separate documents. This system-level view becomes the authoritative reference for auditors and reviewers.

I would also verify that the verification activities on each side are complementary. The hardware test might verify that the sensor produces the correct fault signal under fault conditions, while the firmware test verifies that the decision logic responds correctly to that signal. But neither test alone proves the integrated control works — so I would ensure there's also a system-level integration test that exercises the complete chain. The traceability matrix should show this three-tier verification approach: hardware-level, firmware-level, and system-level.

Finally, I would review the interface specification between hardware and firmware — the exact signal, its electrical characteristics, timing, and protocol — to ensure both teams are working from the same definition. If the interface spec is ambiguous, that's a risk in itself.

**Possible follow-ups:**
- How would you handle the situation where the hardware and firmware teams use different requirement numbering schemes, making cross-referencing error-prone?
- Who should own the system-level traceability view — the systems engineer, the risk manager, or someone else?

---

## Q2: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** This is fundamentally a question about whether the development board is representative of the production hardware for the specific failure modes the risk control is meant to mitigate. I would start by analyzing what the plausibility check actually depends on. If the check is purely algorithmic — for example, rejecting readings that change by more than X% between consecutive samples — and the algorithm runs entirely within the microcontroller's firmware, then a development board with the same microcontroller might be sufficient, provided the firmware binary is identical and the sensor input is simulated realistically.

However, there are several factors that could make production hardware necessary. First, the sensor interface: if the plausibility check depends on the actual analog characteristics of the sensor signal — noise levels, slew rates, offset voltages — then the development board's sensor interface must match the production design. A development board with a different sensor, different analog front-end, or different PCB layout could produce signal characteristics that don't exercise the plausibility check the way the production hardware would.

Second, timing: if the plausibility check involves timing constraints — for example, rejecting readings that arrive too quickly or too slowly — then the production hardware's clock configuration, interrupt latency, and bus timing must be representative. A development board might have different oscillator characteristics or different peripheral configurations.

Third, the risk analysis itself: I would review the hazard analysis to understand what failure scenario the plausibility check is mitigating. If the hazard is a sensor that drifts out of specification due to component aging or environmental stress, then the verification should ideally use production-representative hardware with the actual sensor, because the failure mode is in the sensor, not the firmware logic.

My general approach would be to document the rationale for the verification method choice in the verification plan. If I can justify that the development board is representative for the specific failure modes being tested, and the risk analysis supports that justification, then development-board testing may be acceptable. But if there's any doubt, or if the risk severity is high, I would err on the side of production hardware. The key is that the decision must be based on technical analysis, not convenience.

**Possible follow-ups:**
- What if the production hardware isn't available yet because the firmware development is happening in parallel with hardware bring-up — how would you handle the schedule pressure?
- How would you document the rationale for using a development board so that an auditor would accept it?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** Distributed architectures introduce a layer of complexity because the risk control isn't a single element — it's a coordinated behavior across multiple nodes, and the coordination itself is part of the control. I would approach this in three layers.

First, at the system level, I would define the hazard and the overall risk control strategy. For example, if the hazard is "motor continues running when it shouldn't," the risk control might be "all nodes must agree that a stop command has been issued before the motor node disables power." This system-level control statement becomes the anchor for traceability.

Second, I would decompose the control into per-node responsibilities. Each node's contribution becomes a requirement in that node's firmware or hardware specification. For example, the sensor node must detect the stop condition and broadcast it; the motor node must receive the broadcast, validate it, and act on it; a third node might provide a heartbeat or watchdog function. Each of these per-node requirements traces up to the system-level control.

Third, and this is the critical part, I would capture the coordination requirements separately. The bus protocol, message timing, timeout behavior, and error handling are themselves part of the risk control. These coordination requirements might live in an interface control document or a system-level requirements document, and they need their own traceability links. For example, "the motor node shall act on a stop command within 50ms of receiving it" is a coordination requirement that must be verified at the system level, not just at the node level.

For verification, I would ensure there are three tiers: node-level tests (each node responds correctly to simulated inputs), integration tests (two or more nodes communicating over the bus), and system-level tests (the complete distributed system under fault conditions). The traceability matrix should show which tier verifies each requirement. A common gap is that node-level tests pass but the coordination fails — for example, the motor node responds correctly to a stop command when tested in isolation, but the sensor node's message doesn't arrive in time under bus loading. The traceability scheme should make these gaps visible.

Finally, I would pay special attention to failure modes that are unique to distributed systems: bus contention, message loss, node failure, and timing skew. These are often identified in the DFMEA as new failure modes that don't exist in a single-processor design, and each needs its own risk control and traceability path.

**Possible follow-ups:**
- How would you handle the situation where different nodes are developed by different teams, each with their own requirements document and numbering scheme?
- What if the bus protocol itself is a potential source of hazards — how would you trace protocol-level risk controls?

---

## Q4: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by analysis" — for example, a worst-case timing analysis or a thermal derating calculation — rather than physical tests. The quality manager argues that analysis is not objective evidence and demands physical testing for all risk controls. The systems engineer argues that some controls, like timing margins or thermal derating, can only be practically verified by analysis, and that physical testing would be impractical or impossible. How would you resolve this disagreement?

**Answer:** I would start by acknowledging that both sides have legitimate points. The quality manager is right that physical testing provides the strongest objective evidence, but the systems engineer is also right that some risk controls are inherently analytical — you can't physically test a worst-case timing margin without creating the exact worst-case conditions, which may be impractical or even impossible. The resolution isn't to pick one side but to establish criteria for when analysis is acceptable.

I would propose a framework with three categories. First, controls that must be verified by physical test — these are typically functional safety controls where the failure mode is directly testable, like "the device shall shut down within 100ms of detecting over-temperature." Second, controls that can be verified by analysis alone — these are typically design-margin controls where the analysis method is well-established and validated, like component derating calculations. Third, controls that need a combination — analysis to establish the design margin, plus a physical test to confirm the analysis assumptions are correct.

For the specific case of worst-case timing analysis, I would argue that the analysis is valid if the analysis method itself has been validated — for example, if the timing model has been correlated against measured data from similar designs. But I would also ask whether a physical test could at least partially validate the analysis. For example, you might not be able to test the absolute worst-case timing, but you could test a representative worst-case scenario and compare it to the analysis prediction. If they correlate, the analysis gains credibility.

I would also involve the risk management team, because the decision about verification rigor should be proportional to risk. For a high-severity hazard, I would lean toward requiring physical testing even if it's difficult. For a low-severity hazard, analysis might be sufficient. The key is to document the rationale for each decision so that an auditor can understand why analysis was accepted for one control and physical testing required for another.

Finally, I would suggest a compromise: the systems engineer provides a written justification for each analysis-based verification, including the analysis method, assumptions, and validation evidence. The quality manager reviews these justifications and either accepts them or identifies specific concerns. This turns the disagreement into a structured review process rather than a binary argument.

**Possible follow-ups:**
- What if the quality manager still refuses to accept any analysis-based verification, even with justification — how would you escalate or resolve this?
- How would you determine whether a particular analysis method is "validated" enough to be considered objective evidence?

---

## Q5: How would you approach establishing traceability for risk control measures that are implemented through design margins and derating — for example, selecting a component with a voltage rating well above the maximum expected stress — when these controls don't map cleanly to a functional requirement or a test?

**Answer:** Design margin and derating controls are challenging because they're not functional behaviors — they're properties of the design itself. You can't write a test that exercises a derating margin the way you'd test a functional requirement. But they are legitimate risk controls, and they need to be traceable.

My approach would be to treat these as design constraints rather than functional requirements. In the SRS, I would capture them as non-functional requirements with measurable acceptance criteria. For example, instead of "the input capacitor shall be rated for at least 50V," the requirement might be "all components on the 12V rail shall be derated to at least 80% of their rated voltage under worst-case conditions." This is measurable — you can verify it by analysis — and it's traceable to the risk control.

The traceability path would be: hazard → risk control (component derating to prevent overvoltage failure) → design requirement (derating rule) → design element (specific component selection) → verification activity (derating calculation or design review). The verification activity for a derating control is typically an analysis — a calculation showing that the selected component's rating exceeds the worst-case stress by the required margin. This analysis should be documented as a verification artifact, just like a test report.

I would also consider whether a physical test adds value. For example, you might not be able to test the derating margin directly, but you could test the component under worst-case stress conditions to confirm it operates correctly. This doesn't prove the derating margin, but it validates the component's behavior at the stress level. In some cases, this is worth doing for high-risk components.

The key is to make the traceability explicit and auditable. The risk management file should identify the derating control and reference the design requirement. The design requirement should reference the specific components or component classes. The verification analysis should show the calculation. This chain gives an auditor confidence that the control was intentional, implemented, and verified — even though the verification is analytical rather than physical.

One common pitfall is that derating rules are applied informally — "we always derate capacitors by 50%" — without being documented as requirements. This makes them invisible to the traceability system. I would ensure that all derating rules are explicitly captured as design requirements, with clear acceptance criteria, so they can be traced and verified.

**Possible follow-ups:**
- How would you handle a situation where a derating rule conflicts with another design constraint, such as size or cost?
- How would you verify that derating rules are actually followed in the final design, given that component substitutions sometimes happen during manufacturing?