# medical-devices — Day 22

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a sensor that intermittently provides valid but erroneous readings — for example, a pressure sensor that occasionally reports a spike that is within the valid range but physiologically impossible?

**Answer:** I'd approach this as a multi-layered verification problem. First, I'd want to understand the failure mode precisely — is the spike a single-sample glitch, a short burst, or a sustained offset? That determines what kind of detection logic is appropriate and how to test it.

For the test strategy itself, I'd structure it in three tiers. The first tier is fault injection at the firmware level: I'd create a test harness that can inject synthetic sensor data into the firmware's input buffer, bypassing the actual hardware. This lets me deterministically inject known spike patterns — single-sample outliers, multi-sample plateaus, ramps that are too fast to be physiological — and verify the firmware's response. The key here is that the injected values must be within the valid ADC range but fail physiological plausibility checks, which is exactly the boundary condition we're concerned about.

The second tier is hardware-in-the-loop testing. I'd use a signal generator or a programmable sensor simulator to feed actual electrical signals into the ADC front-end. This catches issues that pure firmware injection misses, such as how the analog filtering interacts with the detection algorithm. For example, a spike that's filtered by the analog front-end might look different at the firmware level than a raw digital injection would suggest.

The third tier is long-duration soak testing with recorded real-world data. If we have captured sensor traces from clinical or field use, I'd replay those through the device to verify that the detection logic doesn't produce false alarms on genuine physiological signals while still catching the anomalous patterns.

A critical part of the strategy is defining what "correctly handles" means before writing any tests. The requirements should specify: does the device ignore the spike entirely, flag it as suspect data, trigger an alarm, or log it for later review? The test plan needs to verify each of those behaviors independently. I'd also include tests for the edge cases — what happens when the spike occurs simultaneously with a genuine alarm condition, or when the sensor recovers and immediately reports a valid but extreme reading?

Finally, I'd document the traceability from each test case back to the specific requirement and the risk analysis entry that identified this failure mode, so the verification evidence directly supports the safety case.

**Possible follow-ups:**
- How would you determine the threshold between "physiologically plausible" and "physiologically impossible" for a given parameter, and who should be involved in setting that threshold?
- How would you handle the situation where the detection algorithm itself introduces a small delay in processing valid data, potentially affecting the device's real-time response?

---

## Q2: How would you approach selecting and qualifying a replacement component for a medical device when the original part is discontinued by the manufacturer?

**Answer:** This is a situation that requires a structured, risk-based approach because the component change can affect safety, performance, and regulatory status. I'd start by forming a cross-functional team — hardware, firmware, quality, regulatory, and possibly clinical representation — because the impact assessment spans all those domains.

The first step is to understand exactly why the original component is being discontinued and what the end-of-life timeline looks like. Is there a last-time-buy opportunity? How much inventory can we secure to bridge the transition? This affects whether we have the luxury of a gradual qualification or need to accelerate.

Next, I'd do a thorough comparison of the replacement candidate against the original. This goes beyond the datasheet — I'd look at electrical characteristics, thermal behavior, timing parameters, package footprint, and any subtle differences in how the part behaves under stress conditions. For a medical device, I'd pay particular attention to parameters that affect safety or accuracy: for an analog front-end, that might be input offset voltage drift over temperature; for a power component, it might be switching characteristics that affect EMI.

The qualification plan would then be scaled based on the risk assessment. If the replacement is a drop-in equivalent from the same manufacturer with identical specifications, the testing might be limited to design verification — confirming the device still meets its specified performance. If the replacement has any meaningful differences, I'd expand the testing to include the full design verification suite, plus any additional tests specifically targeting the changed characteristics. For example, if the new part has slightly different input capacitance, I'd want to verify that the analog front-end's frequency response and noise performance are unchanged.

I'd also consider whether the change affects the regulatory submission. Depending on the jurisdiction and the nature of the change, this could range from a notification to a supplemental submission. The regulatory team needs to be involved early to determine the appropriate path.

Finally, I'd update the risk management file. The component change introduces new potential failure modes or changes the likelihood of existing ones, so the risk analysis needs to be revisited. I'd document the entire qualification process in the design history file, including the rationale for accepting the replacement, the test evidence, and the regulatory assessment.

**Possible follow-ups:**
- How would you handle the situation where the only available replacement component has slightly worse temperature stability than the original, and the device's accuracy specification is already tight?
- What documentation would you expect to produce as evidence of the component qualification for a regulatory audit?

---

## Q3: During IEC 60601-1 testing, your medical device fails the earth leakage current test with a measurement exceeding the 500 µA limit for permanently installed equipment. How would you approach diagnosing and resolving this?

**Answer:** I'd approach this systematically, starting with understanding the measurement setup and then isolating the leakage path. The first thing I'd verify is that the test was performed correctly — the measurement circuit, the applied mains voltage, and the equipment classification all affect the result. It's worth confirming that the test setup matches the standard's requirements before diving into the device design.

Assuming the test setup is correct, I'd work through the potential leakage paths in order of likelihood. The most common contributors to elevated earth leakage are: capacitive coupling between the primary and secondary sides of the power supply, Y-capacitors that are too large, inadequate isolation in the mains input circuitry, or a fault in the protective earth connection itself.

I'd start by measuring the leakage current with the device in different configurations — power supply connected but load disconnected, different combinations of applied parts connected, and so on. This helps isolate whether the leakage is coming from the power supply stage or from downstream circuitry. I'd also measure the leakage at different points in the circuit to identify where the current is entering the earth path.

If the leakage is primarily capacitive coupling from the mains side, the solution typically involves reducing the Y-capacitor values or improving the isolation barrier. However, there's a trade-off here — reducing Y-capacitors can increase conducted emissions, so I'd need to verify that any fix doesn't push the device out of compliance on the EMC side. This is a classic case where the safety and EMC requirements pull in opposite directions, and the design needs to find the balance point.

If the issue is in the protective earth connection — for example, a high-resistance connection that's causing voltage to develop on the chassis — the fix is mechanical: improving the earth bonding, checking the grounding points, or adding additional earth connections.

I'd also consider whether the device's internal layout is contributing. For example, if high-voltage traces run too close to the earth plane or to signal traces that connect to earth, the coupling could be higher than necessary. A layout review might reveal opportunities to increase spacing or add shielding.

Once I've identified the root cause and implemented a fix, I'd re-run the full leakage current test suite — not just the failing test — to confirm that the fix doesn't introduce new issues. I'd also review the risk management file to see if the leakage path was identified as a potential hazard, and update the documentation accordingly.

**Possible follow-ups:**
- How would you determine whether the elevated leakage is a design issue versus a manufacturing defect, and what would you do differently in each case?
- If reducing Y-capacitor values to fix the leakage causes the device to fail conducted emissions, how would you resolve that conflict?

---

## Q4: How would you approach developing a design history file (DHF) for a medical device that is an evolution of a previously cleared device, rather than a completely new product?

**Answer:** I'd approach this by first understanding exactly what changed between the previous device and the new version, because that determines the scope of the DHF work. The DHF for an evolution should leverage the existing documentation where possible, but it must clearly capture the deltas and demonstrate that the changes don't introduce new risks or compromise the original safety and performance.

The first step is a thorough gap analysis. I'd review the previous device's DHF — design inputs, design outputs, verification and validation evidence, risk management file, and design reviews — and map each element against the new device's requirements. For elements that are unchanged, I can reference the existing documentation. For elements that are affected by the change, I need to update or supplement them.

The design inputs are where I'd start. I'd review the original input specifications and identify which ones are still valid, which need to be revised, and which are new. For example, if the evolution adds a new sensor or changes the user interface, those changes flow through the entire DHF. I'd also check whether any regulatory requirements have changed since the original clearance — standards get updated, and the new device may need to meet a newer edition of IEC 60601 or a particular standard.

The risk management file is particularly important for an evolution. I'd review the original hazard analysis and determine whether the changes introduce new hazards, change the likelihood or severity of existing hazards, or affect the effectiveness of existing risk control measures. The risk analysis needs to be updated to reflect the new device's design, and any new risk control measures need to be verified and validated.

For verification and validation, I'd assess which tests need to be repeated. Some tests can be justified as unaffected by the change — for example, if the change is purely in firmware and doesn't touch the power supply, the power supply safety tests might not need to be repeated. But I'd be conservative here; it's often easier to re-run a test than to defend a rationale for why it wasn't needed. The key is that the DHF must contain sufficient evidence to demonstrate that the new device meets all its requirements.

I'd also pay attention to the design transfer documentation. If the manufacturing process changes — new test fixtures, different assembly procedures — those need to be captured. And I'd ensure that the design review records reflect the evolution process, including the reviews that specifically evaluated the changes.

Finally, I'd structure the DHF so that a reviewer can clearly see what's new versus what's carried over. A traceability matrix that maps each design input to its verification evidence, and each hazard to its risk control measure, is essential for demonstrating completeness.

**Possible follow-ups:**
- How would you decide which verification tests from the original device can be leveraged versus which need to be repeated?
- How would you handle a situation where the original DHF is incomplete or poorly organized, and you need to rely on it for the evolution?

---

## Q5: You're the lead engineer on a medical device project. During a design review, the quality manager insists that a new risk control measure must be added to address a hazard with an estimated risk level that the team considers negligible. The schedule impact would be significant. How would you handle this situation?

**Answer:** I'd start by recognizing that this is a disagreement about risk acceptability, not a personality conflict, and it needs to be resolved through the formal risk management process rather than through debate or authority. The ISO 14971 framework provides the structure for this, and both the quality manager and the engineering team should be working within that framework.

The first step is to ensure we're all looking at the same data. I'd ask the quality manager to walk through their risk assessment — what hazard are they concerned about, what's the sequence of events leading to harm, what severity and probability estimates did they use, and what's their basis for those estimates? Often, disagreements about risk acceptability stem from different assumptions about the probability of the initiating event or the effectiveness of existing controls. Getting those assumptions out on the table is essential.

If the disagreement is about the probability estimate, I'd look for data to inform the discussion. This could include field data from similar devices, published literature, or even a simple fault tree analysis to understand the chain of events. If the disagreement is about severity, I'd involve clinical input — the clinical team can provide perspective on how the hazard would actually manifest in a patient.

If the disagreement persists after reviewing the data, I'd escalate it through the formal risk management process. Most organizations have a defined mechanism for risk acceptability decisions — often a risk management board or a designated individual with the authority to accept or reject residual risk. I'd prepare a summary of both positions, the supporting evidence, and the trade-offs, and present it for a formal decision. The key is that this decision needs to be documented in the risk management file, regardless of the outcome.

I'd also consider whether there's a middle path. Sometimes a risk control measure can be implemented in a lighter-weight way than initially proposed — for example, a software-based check instead of a hardware change, or a labeling/warning approach instead of a design change. If the quality manager's concern is legitimate but the full implementation is disproportionate, a scaled-down measure might satisfy both parties.

Throughout this, I'd keep the focus on patient safety and regulatory compliance. The schedule impact is real, but it shouldn't be the deciding factor if the risk is genuinely unacceptable. Conversely, if the risk is genuinely negligible, the quality manager should be able to accept that with proper documentation. The goal is a defensible, documented decision that everyone can support.

**Possible follow-ups:**
- What would you do if the quality manager refuses to accept the team's risk assessment even after the formal escalation process?
- How would you document the disagreement and its resolution in the risk management file to satisfy a regulatory auditor?