# medical-devices — Day 23

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a sensor that intermittently provides valid but erroneous readings — for example, a pressure sensor that occasionally reports a spike that is within the valid range but physiologically impossible?

**Answer:** I'd start by recognizing that this is fundamentally a signal-validation problem that spans both firmware and clinical requirements. The first step would be to define what "physiologically impossible" means quantitatively — this requires input from clinical stakeholders to establish rate-of-change limits, plausible ranges, and duration constraints. For example, a pressure reading that jumps 50 mmHg in 100 ms might be physiologically impossible even if each individual value is within the absolute range.

For the test strategy itself, I'd structure it in layers. First, unit-level testing of the validation algorithm using synthetic data — scripted sequences that include known artifacts (spikes, dropouts, plateaus) and verify the firmware correctly flags or rejects them. This is deterministic and repeatable. Second, hardware-in-the-loop testing where I inject signals at the sensor interface using a function generator or a sensor simulator to produce the artifact patterns. This verifies the entire signal chain, including the analog front-end and ADC. Third, system-level testing where the device runs continuously with a simulated physiological signal that has superimposed artifacts, verifying that the device's behavior — alarms, data logging, display — remains correct over extended periods.

A key design consideration is what the firmware should do when it detects an erroneous reading. The options range from ignoring the sample and holding the last valid value, to flagging the data as suspect, to generating a technical alarm. The right choice depends on the clinical risk: if the parameter is safety-critical, the device should probably indicate that data quality is degraded rather than silently displaying a potentially false value. I'd also want to verify that the validation logic itself doesn't introduce new failure modes — for example, a filter that's too aggressive could mask a genuine rapid deterioration.

Finally, I'd document the test cases in the design verification plan with clear pass/fail criteria, and trace them back to the software requirements. The test cases should be reviewed by both firmware and clinical personnel to ensure they reflect realistic artifact patterns.

**Possible follow-ups:** How would you determine the threshold for what constitutes a "physiologically impossible" reading? What would you do if the validation algorithm itself introduces latency that delays detection of a genuine event?

---

## Q2: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The critical concern here is cross-channel interference and the timing of multiplexed sampling. When two sensors share an ADC, the measurement of one channel can be affected by the settling time of the multiplexer, the charge injection from switching, or crosstalk through the shared signal path. The test plan needs to verify that the specified accuracy is maintained for both parameters when they're being measured in the actual operating sequence, not just when each channel is tested in isolation.

I'd structure the test plan around several key scenarios. First, static accuracy testing: apply known temperature and pressure references simultaneously and verify both readings are within specification. This establishes the baseline. Second, dynamic interaction testing: hold one parameter constant while varying the other rapidly, and verify that the constant parameter's reading doesn't drift or shift due to the changing channel. For example, if pressure is varying quickly, does the temperature reading stay stable? Third, worst-case timing testing: verify accuracy when the multiplexer is switching at its maximum rate, since settling time is often the limiting factor. Fourth, I'd include a test where both parameters are varying simultaneously within their expected clinical ranges, to verify that the system maintains accuracy under realistic operating conditions.

I'd also want to verify the calibration approach. If the two sensors have different offset or gain characteristics, the firmware must apply the correct calibration coefficients to each channel. A test case should verify that calibration values aren't accidentally cross-applied between channels.

For the test equipment, I'd use a calibrated temperature source (e.g., a dry block or water bath) and a pressure calibrator, both with accuracy significantly better than the device under test. The test setup should allow both references to be applied simultaneously. I'd also include a test where one sensor is disconnected or shorted to verify that a fault on one channel doesn't corrupt the measurement on the other channel — this is particularly important for medical devices where a single-point failure shouldn't compromise all monitoring functions.

**Possible follow-ups:** How would you determine the minimum settling time required between channel switches? What would you do if the test reveals that the accuracy specification can't be met when both channels are actively sampling?

---

## Q3: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using an unacknowledged broadcast protocol to simplify the design, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** I'd frame this as a risk-based decision rather than a purely technical one. The clinical requirement — that data loss be detectable and staleness be indicated — is driven by patient safety. If the display shows data that's actually old, a clinician might make a decision based on outdated information. So the question isn't whether to meet the requirement, but how to meet it with an appropriate level of design complexity.

An unacknowledged broadcast protocol can still meet the clinical requirement if it includes mechanisms for detecting data loss and staleness. For example, the transmitter could include a sequence number in each packet, and the receiver could detect gaps in the sequence. The receiver could also use a timeout — if no packet is received within a defined interval, it flags the data as stale. These mechanisms don't require acknowledgments or retransmissions; they just require the receiver to monitor the health of the data stream.

The trade-off is between the simplicity of broadcast versus the reliability of acknowledged communication. Broadcast is simpler, has lower latency, and avoids the complexity of managing retransmissions and acknowledgments. However, it doesn't guarantee delivery — packets can be lost without the transmitter knowing. For a monitoring application where the data is also stored locally on the transmitting device, this might be acceptable: the display might show a brief gap, but the data isn't lost permanently.

I'd approach this by asking the clinical team to define the acceptable data loss rate and the maximum staleness interval. If, for example, a 1-second gap in displayed data is acceptable as long as the display clearly indicates the gap, then broadcast with sequence numbers and a staleness timeout could work. If the clinical team requires that every data point be delivered reliably, then we'd need an acknowledged protocol with retransmission.

I'd also consider the failure modes. With broadcast, the receiver can detect a lost packet but can't request a retransmission. If the link is marginal, the display might show frequent gaps, which could be alarming to clinicians. An acknowledged protocol would be more robust but adds latency and complexity. A middle-ground option is a hybrid approach: broadcast for normal operation, with a periodic health-check message that confirms the link is alive.

Ultimately, I'd document the decision in the risk management file, linking the clinical requirement to the specific protocol mechanism that satisfies it, and verify through testing that the mechanism works under realistic RF conditions.

**Possible follow-ups:** How would you test that the staleness indication works correctly under real-world RF interference? What would you do if the clinical team requires a maximum data loss rate that the wireless link can't reliably achieve?

---

## Q4: How would you approach developing a design verification test plan for a medical device that must operate correctly during and after exposure to a defibrillation pulse, given that the device is intended for use in a hospital environment where defibrillation may occur?

**Answer:** This is a critical safety scenario because a defibrillation pulse is a high-energy event — typically several kilovolts and tens of joules — that can couple into nearby medical devices through patient leads, cables, or even radiated coupling. The device must not only survive the pulse but also continue to operate correctly afterward, and it must not present a hazard to the patient or clinician during the event.

I'd start by reviewing the applicable standard — IEC 60601-1 and the relevant particular standards typically have specific requirements for defibrillation-proof applied parts. The test plan would need to verify two things: that the device survives the pulse without damage, and that it recovers to normal operation within a specified time.

For the test setup, I'd use a defibrillation pulse generator that produces the standardized waveform specified in the standard. The device under test would be connected to a patient simulator or a test load that mimics the patient's impedance. The test would apply the pulse to the patient connections in various configurations — for example, with the device powered on, with the device in monitoring mode, and with the device connected to a patient simulator.

The key measurements are: the voltage and current at the device's input during the pulse (to verify that the protection circuitry limits the energy reaching the internal electronics), the device's behavior immediately after the pulse (does it reset? does it recover to normal operation?), and the device's ongoing accuracy after the pulse (are the measurements still within specification?).

I'd also test the device's response to multiple pulses, since a patient may receive more than one defibrillation attempt. And I'd verify that the device doesn't present a hazard during the pulse — for example, that it doesn't create a path for the defibrillation current to flow through the operator or other connected equipment.

A critical aspect is the recovery time. The standard may specify that the device must return to normal operation within a certain time after the pulse — for example, within 10 seconds. The test plan should measure this recovery time and verify it's within the specified limit.

I'd also include a test where the device is connected to a patient simulator that's also connected to the defibrillator, to verify that the device correctly continues to monitor the simulated patient after the pulse. This is a more realistic scenario than testing the device in isolation.

**Possible follow-ups:** How would you verify that the device's protection circuitry doesn't degrade the normal measurement accuracy? What would you do if the device passes the defibrillation test but takes longer than the specified time to recover?

---

## Q5: You're leading a project where a field complaint reports that a medical device's rechargeable battery is swelling after 6-12 months of use in a hospital setting. The device is used for continuous patient monitoring and the battery is not user-replaceable. How would you approach the investigation and corrective action process?

**Answer:** Battery swelling is a serious safety concern — it can indicate internal short circuits, overcharging, or thermal runaway, and it can physically deform the device enclosure, potentially exposing internal components or creating fire risk. The first priority is patient and user safety, so I'd start by assessing the immediate risk and determining whether any field action is needed.

The first step would be to gather data from the returned devices. I'd want to examine the swollen batteries — visually inspect them, measure their dimensions, check for signs of leakage or venting, and if possible, perform electrical testing to characterize the failure. I'd also review the device's charge/discharge history if the firmware logs that data — how many charge cycles, what depth of discharge, what temperatures the battery experienced. This data can help determine whether the swelling is due to overcharging, excessive cycling, high-temperature exposure, or a manufacturing defect in the battery cells.

I'd also review the battery charging and management design. Is the charging algorithm correctly implemented? Are the voltage and current limits within the battery manufacturer's specifications? Is there a temperature sensor on the battery, and is the charging algorithm using it correctly? A common cause of swelling is charging at temperatures outside the battery's specified range, or charging to a voltage that's slightly too high.

The investigation should follow a structured root-cause analysis process — I'd use an 8D or similar framework. I'd assemble a cross-functional team including hardware, firmware, quality, and the battery supplier. The supplier should be involved early, since the issue may be related to the cell manufacturing process.

In parallel with the investigation, I'd assess the field risk. How many devices are affected? What's the severity of the swelling — is it cosmetic, or does it deform the enclosure? Is there any evidence of thermal events or fires? Based on this assessment, I'd determine whether a field safety corrective action (FSCA) is needed — for example, replacing the affected devices or issuing a safety notice to users. Even if the swelling is contained and doesn't pose an immediate hazard, the risk of thermal runaway over time might warrant a recall or replacement program.

Once the root cause is identified, I'd implement corrective actions. These might include changes to the charging algorithm, adding a more robust battery protection circuit, changing the battery supplier or cell chemistry, or adding a battery health monitoring feature that alerts users when the battery is degrading. I'd also update the risk management file to reflect the new hazard and the risk control measures.

Finally, I'd verify the corrective action through testing — accelerated life testing of the revised design, verification that the charging algorithm changes prevent the failure mode, and validation that the device still meets its performance specifications.

**Possible follow-ups:** How would you determine whether a field safety corrective action is needed while the root cause investigation is still ongoing? What would you do if the battery supplier is unable to identify a manufacturing defect and the failure appears to be related to how the device is used in the hospital?