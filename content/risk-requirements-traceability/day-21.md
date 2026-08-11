# risk-requirements-traceability — Day 21

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a combination of hardware and firmware, where the hardware team documents the control in their design specification and the firmware team documents their portion in a software requirements document — but neither document references the other, and the risk management file treats the control as a single integrated measure?

**Answer:** The core problem here is that the risk management file treats the control as one logical measure, but the implementation is split across two engineering disciplines that maintain separate documentation silos. I would start by creating a single "risk control implementation" record in the risk management file that explicitly lists both the hardware and firmware portions as sub-elements of the same control. This record would include a clear description of how the two portions interact — for example, the hardware sensor detects a condition and asserts an interrupt, and the firmware responds by taking a specific action. 

Next, I would establish cross-references in both directions: the hardware design specification would reference the risk control ID and note that the firmware portion is documented in the software requirements document (with the specific requirement ID), and the software requirements document would do the same in reverse. This creates a bidirectional link between the two documents without requiring them to be merged. 

For verification, I would require three levels of evidence: (1) hardware-level verification that the sensor/comparator actually asserts its output under the fault condition, (2) firmware-level verification that the response logic correctly acts on the interrupt, and (3) system-level verification that the complete chain works end-to-end. The system-level test is essential because it proves the integration — the hardware portion could work perfectly in isolation, and the firmware could work perfectly in isolation, but the interface between them (e.g., interrupt polarity, timing, debounce) could still be wrong. Each level of verification would be traced to the corresponding sub-element in the risk control record, and the system-level test would be traced to the control as a whole.

**Possible follow-ups:** How would you handle the situation where the hardware and firmware teams use different numbering schemes for their documents? What if the firmware portion is updated in a later revision — how would you ensure the traceability remains current?

---

## Q2: How would you approach determining whether a risk control measure that is implemented as a firmware-based plausibility check on a sensor reading — for example, rejecting readings that change by more than a specified rate between consecutive samples — needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** The key question is whether the development board is representative of the production hardware in all aspects that could affect the risk control's behavior. For a firmware-based plausibility check, I would consider three categories of differences: the microcontroller itself, the sensor interface, and the electrical environment.

If the development board uses the same microcontroller with the same clock configuration, the same sensor part number, and the same interface (e.g., I2C or SPI), then the firmware logic itself will behave identically. However, I would still be cautious about timing-related behavior — the production PCB may have different trace lengths, different decoupling, or different pull-up values that could affect signal integrity and therefore the timing of sensor readings. A plausibility check that relies on sampling rate or interrupt timing could be affected by these differences.

I would also consider whether the plausibility check interacts with any hardware features that differ between the boards — for example, if the production hardware has a hardware watchdog or a different power supply architecture that could cause resets or glitches, the firmware behavior could differ.

My approach would be to use the development board for early firmware development and initial verification of the algorithm logic, but I would require final verification on production-representative hardware. The risk management file should specify this requirement explicitly. If the project team wants to justify using only the development board, they would need to provide a documented analysis showing that the differences between the boards cannot affect the control's behavior — and that analysis would need to be reviewed and accepted by the quality function. In practice, for a medical device, I would err on the side of requiring production-hardware verification because the cost of a missed failure is high and the analysis to prove equivalence is often more expensive than simply running the test.

**Possible follow-ups:** What specific aspects of the production hardware would you check to determine if the development board is representative? How would you document the rationale if you decided the development board was sufficient?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a distributed architecture — multiple microcontrollers, each running separate firmware, communicating over a shared bus — and a single hazard is mitigated by coordinated actions across multiple nodes?

**Answer:** This is a challenging scenario because the hazard is mitigated by a chain of actions that spans multiple nodes, and each node has its own firmware and potentially its own requirements document. The risk is that each node's requirements trace to the hazard individually, but the coordination between nodes — which is where failures are most likely — is not captured anywhere.

I would structure the traceability in layers. At the top level, the hazard in the risk management file links to a single "coordinated risk control" record that describes the complete mitigation chain: Node A detects a condition, sends a message on the bus, Node B receives the message and takes an action, and Node C (if involved) does something else. This record would include a sequence diagram or state machine showing the expected interaction.

Below that, I would create individual requirements for each node's portion of the control. Each node's requirement would trace up to the coordinated risk control record, not directly to the hazard. This is important because it makes the coordination explicit — if Node A's requirement is verified but Node B's is not, the traceability shows that the coordinated control is incomplete.

For the bus communication itself, I would add a requirement that specifies the message format, timing, and error handling for the specific message used in this control. This requirement would be traced to the coordinated control record as well. The verification strategy would include: (1) node-level tests for each node's individual behavior, (2) an integration test that exercises the full chain across the bus, and (3) a fault-injection test that verifies the system behavior when the bus communication fails (e.g., message lost, corrupted, or delayed). The integration test is the critical piece — it's the only test that proves the coordination actually works.

I would also consider whether the bus itself introduces new hazards — for example, if the bus is shared with other traffic, could a high-priority message from another subsystem delay the risk control message? This would need to be addressed in the risk analysis and reflected in the verification approach.

**Possible follow-ups:** How would you handle the situation where different nodes are developed by different teams with different release schedules? How would you verify the timing requirements of the coordinated response?

---

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification test, but the test was written to verify a *different* requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a common and dangerous gap because the traceability matrix looks complete — there's a link from the risk control to a test, and the test passes — but the test provides no real evidence that the control works. The first step is to recognize that a traceability link is only meaningful if the verification activity actually exercises the failure condition the control is meant to mitigate.

I would start by reviewing the test procedure against the risk control's failure condition. The key question is: does the test create the conditions that would cause the hazard if the control were absent? For example, if the control is an over-temperature shutdown, the test must actually drive the temperature above the threshold — not just run the system at nominal temperature and observe that it doesn't overheat.

If the test doesn't stress the failure condition, I would flag this as a traceability gap and require a new or modified test. The existing test can remain for verifying the nominal requirement it was originally written for, but it cannot serve as verification for the risk control. I would document the discrepancy in the verification traceability matrix, noting that the original link was invalid and the reason why.

In terms of process improvement, this situation suggests that the test plan was written without a clear understanding of the risk control's failure condition. I would recommend that, for each risk control, the verification plan explicitly state: (1) the failure condition the control mitigates, (2) how the test will create that failure condition, and (3) what observable outcome demonstrates the control worked. This three-part description should be reviewed by someone who understands the risk analysis before the test is executed.

I would also consider whether the test environment can actually create the failure condition — sometimes the test rig doesn't have the capability to inject faults (e.g., no way to simulate a sensor failure). In that case, I would need to either enhance the test rig or use a different verification method, such as fault injection at the firmware level or analysis combined with partial testing.

**Possible follow-ups:** How would you handle the situation where creating the actual failure condition is dangerous or impractical (e.g., a fire hazard)? What alternative verification methods would you consider?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by similarity" — meaning the team is relying on test results from a previous product that used a similar component or design. The quality manager argues that similarity is not acceptable evidence for risk controls, because the previous product wasn't tested under the same conditions. The systems engineer argues that the components are identical, the design is nearly the same, and re-running the tests would waste time and money. How would you resolve this disagreement?

**Answer:** I would start by acknowledging that both sides have valid points. The systems engineer is right that re-running tests for identical components in identical configurations can be wasteful, and the quality manager is right that similarity is often used as a shortcut without proper justification. The resolution is not to pick a side but to establish clear criteria for when similarity is acceptable.

I would propose a structured approach. First, I would ask the systems engineer to document, for each "verification by similarity" item: (1) the specific component or design element being relied upon, (2) the previous product it was verified on, (3) the test conditions used in the previous verification, and (4) a comparison of those conditions to the current product's requirements. This documentation would need to show that the component is identical (same part number, same manufacturer, same revision), that the surrounding design is the same in all aspects that could affect the risk control's behavior (e.g., same decoupling, same layout topology, same operating conditions), and that the previous test was performed under conditions that meet or exceed the current requirements.

Second, I would bring in the quality manager to review this documentation and agree on the acceptance criteria for similarity. For example, we might agree that similarity is acceptable for passive components with well-understood failure modes, but not for active components or for controls that depend on timing or interaction with firmware.

Third, for any item where the documentation is insufficient or the quality manager has legitimate concerns, I would require the test to be re-run. The cost of re-running a test is usually much lower than the cost of a field failure in a medical device.

I would also suggest a middle-ground option: for some items, we might run a reduced test — for example, a functional check rather than a full qualification test — to confirm that the component behaves as expected in the new design. This gives the quality manager objective evidence without the full cost of a complete test campaign.

Finally, I would document the decision and the rationale for each item in the verification traceability matrix, so that the basis for each verification activity is transparent and auditable.

**Possible follow-ups:** What specific criteria would you propose for determining when similarity is acceptable? How would you handle a situation where the previous test data exists but is incomplete or poorly documented?