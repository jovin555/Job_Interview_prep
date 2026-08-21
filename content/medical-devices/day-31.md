# medical-devices — Day 31

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a sensor that intermittently provides valid but erroneous readings — for example, a pressure sensor that occasionally reports a spike that is within the valid range but physiologically impossible?

**Answer:** I'd approach this from three angles: detection, response, and verification.

First, detection. The firmware needs a plausibility layer that goes beyond simple range checking. A spike that's within the absolute valid range but physiologically impossible suggests the need for rate-of-change limits or context-aware validation — for example, comparing a new reading against a moving average or against the previous reading with a maximum allowable delta. The key design question is where to place this logic: in the sensor driver, in a dedicated signal-validation module, or in the application layer. I'd argue for a dedicated validation module so it can be unit-tested independently and reused across sensor types.

Second, response. Once an erroneous reading is detected, the firmware must decide what to do. Options include discarding the reading and holding the last valid value, flagging the data as suspect, or triggering a sensor re-initialization if the pattern suggests a hardware fault. The response must be defined in the requirements — you can't leave it to developer discretion. For a monitoring device, the critical principle is that the device must not generate false alarms based on a single spurious reading, but it also must not mask a genuine deterioration in the patient's condition. So the response should be graduated: discard and continue, then if the pattern persists, escalate to an alarm or a sensor-fault indication.

Third, verification. The test strategy needs to inject these intermittent erroneous readings in a controlled way. I'd use a fault-injection approach at the driver level — either through a test harness that can corrupt readings, or through a hardware signal generator that can produce realistic sensor outputs with superimposed spikes. The test matrix should cover: single isolated spikes, bursts of spikes, spikes at different points in the physiological waveform (e.g., at the peak vs. the trough of a respiratory cycle), and spikes that occur simultaneously with genuine alarm conditions to verify the device still detects the real event. Each test case should have a defined expected outcome, and the results should be traceable back to the requirements.

**Possible follow-ups:** How would you determine the threshold for rate-of-change limits without causing false positives on genuine physiological events? How would you verify that the validation logic itself doesn't introduce a delay that affects alarm response time?

---

## Q2: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The shared ADC and multiplexer introduces a coupling risk that I'd want to address explicitly in the test plan. The core concern is cross-channel interference — when the multiplexer switches from the pressure channel to the temperature channel, residual charge or settling time on the ADC input could affect the measurement accuracy, particularly if the two sensors have very different output impedances or signal levels.

I'd structure the test plan around three layers. First, individual channel accuracy: verify each sensor's accuracy independently, with the other channel either disconnected or held at a known fixed value. This establishes the baseline accuracy for each parameter. Second, cross-channel interaction: verify accuracy with both channels active and the non-measured channel driven to its worst-case value — for example, maximum pressure while measuring temperature, and vice versa. This is where settling time and multiplexer crosstalk issues would surface. Third, simultaneous accuracy: verify that both parameters meet their specified accuracy when measured in rapid succession, as they would be in normal operation.

For the test methodology, I'd use a matrix of test points across each sensor's operating range, but critically, I'd also test at the extremes of the other channel. The test equipment needs to provide independent reference measurements for both parameters simultaneously — for example, a calibrated pressure source and a calibrated temperature source in the same environmental chamber. The data logging needs to capture both the device's reported values and the reference values with synchronized timestamps, so you can correlate any errors with the measurement sequence.

I'd also include a specific test for multiplexer settling: a test case where the pressure channel is at its maximum value and the temperature channel is at its minimum, then immediately switching to measure temperature — this is the worst-case scenario for settling time. The test plan should specify the acceptable error under this condition, which may need to be tighter than the individual channel accuracy if the clinical use case requires rapid alternating measurements.

**Possible follow-ups:** How would you determine whether any observed cross-channel error is due to the multiplexer, the ADC, or the sensor interface circuitry? What would you do if the test reveals that the settling time is insufficient for the required accuracy?

---

## Q3: How would you approach selecting and qualifying a replacement component for a medical device when the original part is discontinued by the manufacturer?

**Answer:** This is a situation that triggers a formal change management process, not just a component swap. I'd approach it in phases: assessment, qualification, and implementation.

In the assessment phase, I'd first document the original component's role in the device and its criticality. Is it a safety-critical component — for example, part of the isolation barrier, a sensor that directly affects patient monitoring, or a power supply component that affects leakage current? Or is it a non-critical component like a bypass capacitor? This determines the depth of qualification required. I'd also review the component's specifications against the design requirements, not just against the original part's datasheet. The question isn't "is the replacement equivalent to the original?" but "does the replacement meet the design requirements that the original was selected to satisfy?"

Next, I'd evaluate the replacement candidate across several dimensions: electrical specifications (with attention to parameters that might not be on the front page of the datasheet — like temperature coefficients, long-term drift, or transient response), mechanical compatibility (footprint, height, thermal characteristics), and environmental ratings. I'd also look at the supplier's manufacturing history and quality systems — for a medical device, you need confidence in the supplier's change control and traceability.

The qualification phase depends on the component's criticality. For a non-critical component, a review of specifications and a limited verification test might suffice. For a safety-critical component, I'd expect to run a more extensive verification program: bench testing across the operating temperature range, accelerated life testing if the component affects long-term reliability, and potentially re-running some of the device-level safety tests if the component is part of a safety mechanism. For example, if the replacement is a different optocoupler in the isolation barrier, I'd want to re-verify creepage and clearance, dielectric strength, and possibly patient leakage current.

Finally, the implementation phase involves updating the design documentation, the risk management file (to assess whether the new component introduces any new hazards or changes the effectiveness of existing risk controls), and the design history file. I'd also consider whether the change requires regulatory notification — depending on the jurisdiction and the nature of the change, a supplement or notification to the regulatory body may be required.

**Possible follow-ups:** How would you decide whether the replacement component requires re-running full IEC 60601-1 safety testing or just targeted verification? How would you handle a situation where the only available replacement has slightly worse specifications but is still within the design requirements?

---

## Q4: During IEC 60601-1 leakage current testing, you measure elevated patient leakage current on a BF-type applied part. How would you approach diagnosing and resolving this?

**Answer:** I'd approach this systematically, starting with understanding the measurement setup and then isolating the source of the leakage path.

First, I'd verify the test setup. Leakage current measurements are highly sensitive to test configuration — the measuring device (MD) network, the applied part connections, the grounding configuration, and the orientation of the mains plug can all affect the reading. I'd confirm that the test was performed according to the standard's requirements, including the correct measuring instrument and the correct connection of the applied part to the MD network. I'd also check whether the measurement was taken under normal condition or single-fault condition, as the acceptable limits differ.

If the setup is correct, I'd then work to isolate the leakage path. Patient leakage current can flow through several paths: capacitive coupling across the isolation barrier, leakage through the power supply, leakage through the signal conditioning circuitry, or leakage through the applied part's own components. I'd use a process of elimination — disconnecting or disabling sections of the circuit to identify where the leakage is entering the patient circuit. For example, I might disconnect the applied part from the signal conditioning circuitry and measure leakage directly at the applied part connector, or I might power the device from an isolation transformer to see if the leakage is coming from the mains side.

Common causes I'd look for include: inadequate creepage or clearance between the patient circuit and mains or secondary circuits, a missing or incorrectly placed Y-capacitor, a component (like an optocoupler or isolation amplifier) with higher than expected coupling capacitance, or a PCB layout issue where a high-voltage trace runs too close to a patient-circuit trace. I'd also check the grounding strategy — sometimes a floating patient circuit can couple more leakage than a referenced one, depending on the design.

Once the source is identified, the resolution depends on the root cause. If it's a layout issue, the fix might be a PCB revision with increased spacing or a guard trace. If it's a component issue, it might require selecting a component with lower coupling capacitance or adding a shielding element. If it's a design architecture issue, it might require rethinking the isolation strategy — for example, adding an additional isolation barrier or changing the grounding configuration.

I'd also update the risk management file to document the finding and the corrective action, and I'd consider whether the issue could affect other products or designs in the same family.

**Possible follow-ups:** How would you distinguish between capacitive leakage and resistive leakage in your diagnosis? What would you do if the leakage current is only slightly above the limit and the fix requires a significant design change?

---

## Q5: You're leading a project where a field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that requires immediate attention, and I'd approach it with patient safety as the primary concern while following a structured investigation process.

First, I'd assess the immediate risk. If there's a pattern of skin irritation across multiple patients, I'd need to determine whether this is an isolated issue or a systemic problem. I'd work with the clinical team and the quality organization to evaluate whether the device should be temporarily removed from use or whether the risk can be managed with additional precautions. This decision would be based on the severity of the irritation, the patient population, and whether there's a clear alternative. This is a risk management decision, not just an engineering decision, so I'd involve the appropriate stakeholders.

Then I'd begin the investigation. The complaint mentions the silicone sensor pad, so I'd look at several potential causes: a change in the silicone material formulation (either by the supplier or a change in the raw material source), a change in the manufacturing process (like a change in curing time or temperature), a contamination issue (residue from cleaning agents or mold release agents), or a design issue that was always present but is only now being reported. I'd review the device history records for the affected lot(s), including incoming material certificates, manufacturing records, and any process changes. I'd also request the affected devices back for analysis — looking at the pad material, testing for residual chemicals, and comparing against retained samples from earlier production runs.

I'd also consider the clinical context. Is the irritation a reaction to the material itself, or could it be related to how the device is being used — for example, prolonged contact time, interaction with other products used on the skin, or a change in patient population? I'd work with the clinical team to gather more details about the affected patients and the conditions of use.

The corrective action would depend on the root cause. If it's a material change, I'd work with the supplier to identify the change and determine whether the new material meets the original biocompatibility requirements. If it's a process issue, I'd implement corrective actions in manufacturing. If it's a design issue, I'd need to evaluate design changes, which could include material selection, pad geometry, or surface treatment. Any corrective action would be verified — including re-running relevant ISO 10993 biocompatibility testing if the material or process changed — and then validated before implementation.

Throughout this process, I'd ensure that all findings are documented in the complaint handling system and that any regulatory reporting obligations are met. If the investigation reveals a systemic issue, a field safety corrective action (FSCA) might be necessary, which would involve notifying the regulatory authorities and potentially the users.

**Possible follow-ups:** How would you determine whether the skin irritation is a material toxicity issue versus a mechanical irritation issue? How would you communicate with the clinical sites during the investigation without causing unnecessary alarm?