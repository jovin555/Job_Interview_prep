# medical-devices — Day 27

## Q1: How would you approach designing the patient leakage current measurement path for a medical device that has multiple BF-type applied parts, where the device must meet IEC 60601-1 leakage current limits under both normal and single-fault conditions?

**Answer:** The first step is to clearly define the applied part configuration and the measurement setup per IEC 60601-1. With multiple BF-type applied parts, the key question is whether they are electrically isolated from each other or share a common internal circuit. If they share a common circuit, the worst-case leakage path is typically measured from all applied parts tied together to ground. If they are isolated, each applied part must be measured individually, and the measurement network (MD — measuring device) must be connected between each applied part and earth.

I would start by reviewing the circuit topology to identify all paths from the applied parts to earth or to other conductive parts — this includes the power supply, any isolation barriers, and any internal shielding. The design should incorporate a single-point earth connection and maintain adequate creepage and clearance between the patient circuits and any secondary circuits. For the measurement strategy, I would use the MD specified in IEC 60601-1 (typically the RC network with the appropriate frequency response) and measure under normal conditions and under each single-fault condition — for example, one mains conductor interrupted, or a protective earth connection interrupted.

A critical design consideration is that the leakage current from multiple applied parts can sum if they share a common return path. I would ensure that the patient circuit ground is a dedicated trace or plane that doesn't share current with any other circuit. I would also verify that any Y-capacitors between the patient circuit and earth are properly valued — too large a capacitance can increase leakage current at mains frequency. During design verification, I would run the leakage tests with all applied parts connected simultaneously, as well as with each applied part individually, to confirm the worst-case configuration.

**Possible follow-ups:**
- How would you determine whether the multiple BF applied parts should be treated as one combined applied part or as separate applied parts for the purpose of leakage current testing?
- What design changes would you consider if the measured patient leakage current is marginally above the limit under single-fault conditions?

---

## Q2: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The key challenge here is that sharing an ADC and multiplexer introduces potential cross-talk and timing interactions between the two measurement channels. I would structure the test plan around three layers: individual channel accuracy, cross-channel isolation, and simultaneous measurement performance.

For individual channel accuracy, I would test each sensor channel independently against a reference standard — for temperature, a calibrated thermometer or precision RTD simulator; for pressure, a calibrated pressure source or manometer. This establishes the baseline accuracy of each channel without interference.

For cross-channel isolation, I would test scenarios where one channel is at an extreme value while the other is at a different extreme, and verify that the measurement of each channel is not affected by the other. For example, with the temperature sensor at 42°C and the pressure sensor at a low pressure, I would verify that the temperature reading doesn't shift when the pressure channel is switched. This is particularly important if the multiplexer has any charge injection or if the ADC has insufficient settling time between channel switches.

For simultaneous measurement, I would verify that the device can maintain specified accuracy for both parameters when they are being sampled in rapid succession — this tests the settling time, the ADC sampling rate, and the firmware's ability to process both channels without introducing timing jitter. I would also test at the extremes of the specified operating range for both parameters simultaneously, since the device may behave differently when both channels are near their limits.

I would also include a test for the multiplexer switching sequence — for example, if the firmware alternates between channels, I would verify that the first sample after a channel switch is either discarded or given sufficient settling time. Finally, I would document the test setup, including the reference standards and their calibration status, and ensure traceability to national standards.

**Possible follow-ups:**
- How would you determine the required settling time for the ADC after a multiplexer channel switch, and how would you verify it in the test plan?
- What would you do if the test reveals that the two channels interfere with each other when sampled in rapid succession?

---

## Q3: How would you approach verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory is full, given that the device must continue monitoring and displaying physiological data in real time?

**Answer:** This is a critical scenario because the device's primary function — real-time monitoring and display — must not be compromised by a secondary function like data logging. I would approach this by first defining the expected behavior clearly: the device must continue monitoring and displaying data without interruption, and it must handle the full-memory condition in a way that is safe, predictable, and visible to the user.

The verification strategy would include both firmware-level testing and system-level testing. At the firmware level, I would verify that the data logging task properly detects the full condition and handles it gracefully — for example, by stopping further writes, preserving the existing data, and setting a flag that the UI can use to notify the user. I would verify that the logging task does not block or starve the monitoring task, and that the real-time display continues to update at the required rate.

At the system level, I would test the device with a nearly full memory — for example, by pre-filling the memory with test data — and then run the device in monitoring mode for an extended period. I would verify that the display continues to update, alarms still function, and the device does not reset or enter an undefined state. I would also verify that the user is notified of the full condition, either through a visual indicator or a message, and that the notification is clear enough for a clinician to understand that logging has stopped.

I would also test the behavior when the user attempts to download or clear the logged data while the device is in monitoring mode — this is a common real-world scenario, and the firmware must handle it without disrupting monitoring. Finally, I would verify the behavior across power cycles — the device should remember that memory is full and continue to operate correctly on restart, without attempting to overwrite existing data.

**Possible follow-ups:**
- What design choices would you consider for the data logging architecture to minimize the risk of memory-full conditions in the first place?
- How would you verify that the user notification for a full memory condition meets the usability requirements of IEC 60601-1-6?

---

## Q4: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using an unacknowledged broadcast protocol to simplify the design, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** The core tension here is between design simplicity and clinical safety requirements. The clinical requirement — that data loss be detectable and staleness be indicated — is not optional; it's a patient-safety consideration. If the display unit shows data that is actually stale, a clinician could make a decision based on outdated information. So the question is not whether to meet the requirement, but how to meet it with the least complexity.

An unacknowledged broadcast protocol can still meet the clinical requirement if it includes a sequence number and a timestamp in each packet. The display unit can then detect gaps in the sequence numbers, indicating lost packets, and can monitor the time since the last received packet to determine staleness. If the display unit doesn't receive a packet within a defined timeout, it can indicate "data stale" or "connection lost" to the user. This approach doesn't require acknowledgements or retransmissions, so it keeps the protocol simple while still meeting the clinical requirement.

However, I would also consider the failure modes of this approach. If the wireless link is congested or the display unit is out of range, the display unit will show a stale-data indication, which is safe but may cause unnecessary alarms or clinical workflow disruption. I would discuss with the clinical team what the acceptable timeout is — for example, for a continuous monitoring parameter like heart rate, a 2-second timeout might be appropriate, while for a parameter that changes slowly, a longer timeout might be acceptable.

I would also consider whether the data loss detection should trigger an audible alarm or just a visual indication. This depends on the clinical context — if the device is used in a setting where the clinician is actively watching the display, a visual indication may be sufficient. If the device is used in a setting where the clinician may not be watching continuously, an audible alarm may be needed.

In the design review, I would facilitate a discussion between the firmware engineer and the clinical team to clarify the exact requirements — what constitutes "stale," what the user should see, and what actions the user should take. I would then work with the firmware engineer to implement the minimal protocol changes needed to meet those requirements, and document the design decision in the risk management file.

**Possible follow-ups:**
- How would you determine the appropriate timeout for declaring data stale, and how would you verify that the timeout is clinically acceptable?
- What additional testing would you recommend for the wireless link to ensure that data loss is detected reliably in a hospital environment with potential RF interference?

---

## Q5: You're leading a project where a field complaint reports that a medical device's rechargeable battery is swelling after 6-12 months of use in a hospital setting. The device is used for continuous patient monitoring and the battery is not user-replaceable. How would you approach the investigation and corrective action process?

**Answer:** Battery swelling is a serious safety concern — it can indicate internal cell damage, overcharging, or a manufacturing defect, and it carries a risk of fire or rupture. The first priority is patient and user safety, so I would immediately assess the risk and determine whether the device should be recalled, whether usage should be restricted, or whether the issue can be managed with a software update or other mitigation.

The investigation would follow a structured root-cause analysis. I would start by collecting all available data: the number of complaints, the affected serial numbers or lot numbers, the battery manufacturer and batch, the charging patterns in the affected devices, and the environmental conditions (temperature, humidity) in the hospitals where the devices are used. I would also retrieve and examine the affected devices — if possible, I would perform a teardown and inspect the battery, the charging circuit, and the battery management system.

The root-cause analysis would consider several hypotheses: overcharging due to a firmware bug in the charging algorithm, over-discharging due to a firmware bug in the low-battery cutoff, a hardware fault in the charging circuit (e.g., a failed FET or sense resistor), a manufacturing defect in the battery cells, or an environmental factor like high ambient temperature. I would also consider whether the battery is being subjected to mechanical stress — for example, if the battery compartment is too tight or if the device is being dropped.

I would work with the battery supplier to understand their manufacturing process and any known issues with the specific cell chemistry. I would also review the charging profile — voltage, current, and temperature limits — against the battery manufacturer's specifications. If the investigation points to a firmware issue, I would develop and validate a firmware update. If it points to a hardware issue, I would assess whether a hardware revision is needed and whether the affected devices need to be replaced.

Throughout the investigation, I would document everything in the complaint handling system and the risk management file. If the risk is determined to be unacceptable, I would initiate a field safety corrective action (FSCA) — this could involve replacing the battery in affected devices, issuing a firmware update, or recalling the device. I would also communicate with the regulatory authorities as required, and with the hospitals using the device, providing clear guidance on how to identify a swollen battery and what to do if one is found.

**Possible follow-ups:**
- How would you prioritize the investigation steps if the complaint volume is increasing rapidly and you need to make a preliminary risk assessment within 24 hours?
- What criteria would you use to decide between a firmware update, a hardware revision, and a full recall as the corrective action?