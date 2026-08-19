# medical-devices — Day 29

## Q1: How would you approach verifying that a medical device's firmware correctly handles a situation where a sensor is disconnected or shorted during patient monitoring, given that the device must continue monitoring other parameters and must not generate false alarms?

**Answer:** I'd approach this as a structured fault-handling verification problem with three layers: detection, response, and recovery.

**Detection layer:** First, I'd work with the firmware team to understand what detection mechanisms exist for each sensor input. For a disconnected sensor, you typically rely on open-circuit detection — often implemented via a bias resistor that pulls the input to a known voltage when the sensor is absent. For a shorted sensor, you'd look for out-of-range readings or a signal that's stuck at a rail. The key question is whether the detection is robust across the full range of failure modes, including partial disconnections (intermittent contact) and short-to-ground versus short-to-supply.

**Response layer:** Once a fault is detected, the firmware must decide what to do. For a multi-parameter monitor, the critical requirement is that a fault on one channel doesn't compromise the others. I'd verify that the faulted channel is clearly flagged (e.g., "sensor off" or "check sensor" message) while the remaining channels continue normal monitoring and alarm functionality. I'd also check that the fault doesn't trigger a false alarm on the faulted channel itself — the device should distinguish between "no data" and "dangerous data."

**Recovery layer:** The device must handle sensor reconnection gracefully. I'd verify that when the sensor is restored, the device resumes normal operation without requiring a power cycle, and that there's a defined stabilization period before the data is considered valid again — you don't want a transient reading during reconnection to trigger a false alarm.

For the test strategy, I'd develop a fault injection test matrix that covers each sensor channel, each fault type (open, short-to-ground, short-to-supply, intermittent), and each device state (normal monitoring, alarm active, menu navigation). I'd use a combination of hardware fault injection (switching circuits to simulate disconnection) and firmware-level fault injection (forcing the driver to report a fault condition). The test would verify both the device's displayed status and the alarm behavior.

**Possible follow-ups:**
- How would you determine whether a "sensor off" indication should be considered an alarm or just a status message under IEC 60601-1-8?
- How would you handle the case where a sensor is disconnected and reconnected rapidly multiple times — could this cause a race condition in the firmware?

---

## Q2: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** This is a classic mixed-signal verification challenge because the shared ADC and multiplexer introduce potential cross-channel interference and timing constraints that don't exist with independent signal chains.

**Step 1 — Understand the signal chain and specifications.** I'd start by mapping the complete signal path for each sensor: sensor → conditioning circuit → multiplexer → ADC → firmware processing → displayed value. I'd document the accuracy specification for each parameter (e.g., ±0.1°C for temperature, ±2% for pressure) and identify where in the chain errors could be introduced — offset, gain error, noise, crosstalk, settling time, and multiplexer switching artifacts.

**Step 2 — Identify the key risk areas.** With a shared ADC, the main risks are: (a) insufficient settling time after multiplexer switching, especially if one channel has high source impedance; (b) crosstalk between channels through the multiplexer's off-channel leakage or charge injection; (c) ADC reference errors that affect both channels simultaneously; and (d) firmware timing issues where the sampling rate or channel sequencing affects accuracy.

**Step 3 — Design the test matrix.** I'd structure the verification into three tiers:

- **Tier 1 — Individual channel accuracy:** Test each channel independently against a reference standard (e.g., a calibrated temperature bath and a precision pressure calibrator) across the full operating range. This establishes baseline accuracy without cross-channel effects.

- **Tier 2 — Simultaneous accuracy with stable inputs:** Apply known, stable temperature and pressure inputs simultaneously and verify that both readings remain within specification. This catches gross crosstalk or settling issues.

- **Tier 3 — Simultaneous accuracy with dynamic inputs:** This is where the shared-ADC risks really surface. I'd vary one parameter rapidly (e.g., pressure transients) while holding the other stable (e.g., temperature), and verify that the stable channel doesn't show artifacts. I'd also test the reverse scenario. This is the test that would catch multiplexer settling or crosstalk problems.

**Step 4 — Address the "simultaneously" requirement.** I'd clarify with the design team what "simultaneously" means in practice — is it truly simultaneous sampling, or is it interleaved sampling with a defined maximum time skew? If the device displays both values continuously, the verification should confirm that the displayed values are consistent with the actual conditions at the time of display, accounting for any sampling skew.

**Step 5 — Include boundary and environmental conditions.** I'd repeat key tests at temperature extremes and at the edges of the input ranges, since multiplexer leakage and ADC errors often worsen at extremes.

**Possible follow-ups:**
- How would you determine the required settling time for the multiplexer, and how would you verify it's adequate?
- What would you do if you discovered that the pressure channel's accuracy was within spec when tested alone but failed when the temperature channel was actively being sampled?

---

## Q3: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device is in a "suspended" or "paused" state (e.g., during patient transport or a temporary procedure) and a critical alarm condition occurs?

**Answer:** This is fundamentally a question about alarm state management and the priority of patient safety over user convenience. I'd approach it by first understanding the intended clinical use of the "suspended" state, then designing tests around the alarm behavior in that state.

**Step 1 — Clarify the clinical intent.** I'd start by reviewing the usability specification and clinical input to understand why the suspended state exists. Is it to silence nuisance alarms during transport? To allow temporary disconnection of sensors during a procedure? The intended use determines what the correct behavior should be. For example, if the device is in transport mode, the clinical team may want alarms to continue but perhaps at a different volume or routing. If the device is paused for a procedure, some alarms might legitimately be suppressed — but critical alarms (e.g., apnea, arrhythmia) should generally never be suppressed.

**Step 2 — Define the alarm behavior in the suspended state.** Working with the clinical team and the firmware team, I'd document the expected behavior for each alarm priority level:
- **High-priority alarms** (e.g., apnea, no pulse): Should these always sound, even in suspended mode? Typically yes, because these represent immediate threats.
- **Medium-priority alarms** (e.g., borderline vital signs): May be suppressed or delayed in suspended mode, but should be logged and presented when the device resumes normal operation.
- **Low-priority/technical alarms** (e.g., low battery, sensor disconnect): May be suppressed in suspended mode.

**Step 3 — Design the test matrix.** I'd create a matrix that crosses each alarm condition with each device state (normal, suspended, resuming). For each combination, I'd verify:
- Whether the alarm is presented (audible/visual) or suppressed
- Whether the alarm is logged with a timestamp
- Whether the alarm condition is re-evaluated when the device resumes normal operation
- Whether the suspended state itself is clearly indicated to the user (e.g., a persistent visual indicator)

**Step 4 — Test the transition edges.** The most likely failure modes are at the transitions: entering suspended mode while an alarm is already active, and exiting suspended mode when a critical condition has developed during the suspension. I'd specifically test:
- Entering suspended mode with an active high-priority alarm — does the alarm continue or get suppressed?
- Exiting suspended mode when a critical condition developed during suspension — is the alarm presented immediately, or is there a delay?
- What happens if the user attempts to enter suspended mode while a high-priority alarm is sounding — is this allowed, or is it blocked?

**Step 5 — Include usability and human factors considerations.** I'd also verify that the suspended state is visually distinct and that the user cannot accidentally leave the device in suspended mode indefinitely. Some devices implement a maximum suspension time or require periodic confirmation.

**Possible follow-ups:**
- How would you determine whether a particular alarm should be suppressed during the suspended state — what criteria would you use?
- How would you handle the case where the device is in suspended mode and the battery reaches a critically low level?

---

## Q4: During a design review for a medical device that uses an optical sensor to measure blood oxygen saturation (SpO2), the firmware engineer proposes using an adaptive filtering algorithm to reduce motion artifacts. The algorithm is complex and difficult to verify deterministically. How would you approach evaluating this proposal?

**Answer:** This is a common tension in medical device development — the desire for better performance through sophisticated signal processing versus the regulatory and verification burden that comes with complexity. I'd approach this as a structured evaluation rather than a simple accept/reject decision.

**Step 1 — Understand the clinical problem and the performance gap.** I'd start by asking what specific motion artifact scenario is causing the problem. Is it patient movement during monitoring? Is it a home-use device where the patient is ambulatory? Understanding the clinical context helps determine whether the adaptive filter is truly necessary or whether a simpler solution (e.g., better sensor placement, a hardware-based approach, or a simpler fixed filter) could achieve acceptable performance.

**Step 2 — Assess the regulatory and verification implications.** Under IEC 62304, the software safety classification and the complexity of the algorithm directly affect the required verification effort. An adaptive algorithm that changes its behavior based on input data is inherently more difficult to verify than a fixed filter because the state space is much larger. I'd ask the firmware engineer to articulate:
- How the algorithm's behavior can be characterized across the full range of expected inputs
- Whether the algorithm can be configured to operate in a deterministic mode for verification purposes
- What the failure modes are — specifically, can the algorithm produce a plausible but incorrect SpO2 reading that would mislead clinicians?

**Step 3 — Evaluate the risk-benefit trade-off.** I'd work with the team to quantify the benefit (reduced false alarms, improved accuracy during motion) and the risk (increased verification effort, potential for undetected algorithm errors, longer development time). If the device is intended for continuous monitoring in a hospital setting where motion artifacts are common, the benefit might justify the complexity. If the device is for spot-check measurements where the patient can be instructed to remain still, a simpler approach might be sufficient.

**Step 4 — Consider alternative approaches.** I'd ask whether there are simpler alternatives that could achieve most of the benefit:
- A fixed high-pass or low-pass filter tuned to the expected artifact frequency range
- A hardware-based approach (e.g., better optical shielding, accelerometer-based motion detection to gate the readings)
- A "quality metric" approach where the device detects motion and displays a "low signal quality" message rather than attempting to filter out the artifact

**Step 5 — If the adaptive algorithm is justified, define the verification strategy.** If we proceed with the adaptive filter, I'd require:
- A clear specification of the algorithm's behavior, including the adaptation rules and the range of filter parameters
- A test corpus of recorded physiological signals with known ground truth (e.g., recorded SpO2 waveforms with simultaneous motion reference from an accelerometer)
- A defined set of test scenarios covering the expected range of motion artifacts
- A mechanism to detect when the algorithm is producing unreliable output (e.g., a confidence metric that can be displayed to the user)

**Step 6 — Document the decision.** Regardless of the outcome, I'd ensure the decision and its rationale are documented in the design history file, including the risk assessment and the verification strategy.

**Possible follow-ups:**
- How would you define the acceptance criteria for the adaptive filter's performance — what would "good enough" look like?
- If the algorithm is too complex to fully verify, would you consider a hybrid approach where the adaptive filter is used but a simpler algorithm runs in parallel as a safety check?

---

## Q5: You're leading a project where a field complaint reports that a medical device's patient-contacting temperature probe is reading approximately 2°C higher than a reference thermometer used by clinical staff, but the device passes its calibration check when returned to the manufacturer. How would you approach the investigation and corrective action process?

**Answer:** This is a classic "it works in the lab but not in the field" scenario, and it requires a systematic investigation that considers the full context of use rather than just the device's internal calibration. I'd structure this as a formal investigation following a root-cause analysis methodology.

**Step 1 — Gather detailed field information.** Before drawing any conclusions, I'd collect as much information as possible about the reported discrepancy:
- How was the comparison performed? Was the reference thermometer calibrated? What was its accuracy specification?
- Where was the probe placed on the patient, and what was the ambient temperature?
- Was the discrepancy consistent across multiple readings, or intermittent?
- Were there multiple devices affected, or just one?
- What was the clinical context — was the patient febrile, was there local inflammation, was the probe in contact with a warming blanket?

**Step 2 — Evaluate the measurement methodology.** A common cause of "device error" is actually a comparison methodology issue. The reference thermometer may measure a different physiological site (e.g., oral vs. skin temperature), or the two devices may have different response times. I'd ask whether the clinical staff followed the device's instructions for use regarding probe placement and stabilization time. A 2°C difference could easily be explained by comparing a skin-surface probe to an oral or core temperature reading.

**Step 3 — Examine the device's calibration and performance.** The fact that the device passes its calibration check when returned is important but not conclusive. I'd review what the calibration check actually verifies — does it test the full measurement chain (sensor, signal conditioning, ADC, firmware) or just a portion? I'd also consider:
- Was the probe cable or connector damaged in the field?
- Could the probe have been exposed to conditions that affected its accuracy (e.g., sterilization cycles, cleaning agents, physical damage)?
- Is there a known drift mechanism for this sensor type that might not be caught by the calibration check?

**Step 4 — Consider environmental factors.** The device may be sensitive to ambient temperature, electromagnetic interference, or other environmental conditions that aren't present in the manufacturing calibration environment. I'd ask whether the discrepancy correlates with any environmental factors.

**Step 5 — Conduct a controlled comparison.** If the device passes its calibration check, I'd arrange for a controlled comparison using a calibrated reference thermometer under conditions that mimic the clinical environment. This might involve testing the device on a thermal phantom (a heated surface that simulates body temperature) rather than a live patient, to eliminate patient variability.

**Step 6 — Determine the corrective action.** Depending on the findings, the corrective action could range from:
- **No device change needed** — if the issue was a comparison methodology problem, the corrective action would be clinical education (e.g., updating instructions for use, training materials)
- **Device modification** — if a genuine accuracy issue is found, this could involve firmware changes (e.g., calibration offset adjustment), hardware changes (e.g., improved sensor shielding), or changes to the calibration procedure
- **Process change** — if the issue relates to how the device is stored, handled, or maintained in the field

**Step 7 — Document and close out.** I'd document the investigation findings, the root cause determination, and the corrective action in the CAPA system, and verify the effectiveness of the corrective action before closing the complaint.

**Possible follow-ups:**
- How would you determine whether this is an isolated incident or a systemic issue that might affect other devices in the field?
- What would you do if the investigation revealed that the device's accuracy specification was adequate for its intended use, but the clinical staff were using it in a way that was outside the intended use?