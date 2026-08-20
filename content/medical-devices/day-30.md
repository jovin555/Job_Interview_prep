# medical-devices — Day 30

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's real-time clock (RTC) battery is depleted, given that the device logs time-stamped physiological data that may be used for clinical decision-making?

**Answer:** The core concern here is data integrity and clinical traceability — if the RTC loses time, the device must not silently log data with incorrect timestamps, because that could lead to incorrect clinical decisions. My approach would start with defining the expected behavior at the requirements level: when the RTC battery is depleted, the device should detect the loss of time validity, flag the data as having unreliable timestamps, and prompt the user to set the time before resuming normal logging.

For the test strategy, I'd structure it around several layers. First, firmware-level testing using fault injection — simulating RTC battery failure by disconnecting the backup supply or corrupting the RTC registers, then verifying that the device enters the defined error state. This would include testing the power-up sequence with a depleted RTC battery, since that's a common failure point: the device boots, reads the RTC, and gets a default date (like 2000-01-01) without realizing it's invalid.

Second, I'd test the data integrity aspects: verify that data logged during the "time unknown" period is either not timestamped, timestamped with a flag indicating uncertainty, or held in a buffer until the time is set. The key is that the device must not backfill timestamps incorrectly once the user sets the time — that would corrupt the chronological ordering of the data.

Third, I'd include integration testing with the clinical display or reporting system to verify that the "time invalid" flag propagates correctly and that the system handles the data appropriately — for example, by excluding it from trend analysis or clearly marking it as having uncertain timing.

Finally, I'd test the user interaction: when the RTC battery is depleted, the device should prompt the user to set the time, and I'd verify that the prompt is clear, that the user can complete the process, and that the device resumes correct timestamping afterward. This would include edge cases like the user setting an incorrect time or the device being used in a different timezone.

**Possible follow-ups:**
- How would you handle the case where the device has already logged data with incorrect timestamps before the RTC failure was detected?
- What if the device is used in a home environment where the user may not notice the time-setting prompt?

---

## Q2: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using a proprietary protocol with a simple checksum, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** The fundamental issue here is that a simple checksum detects random bit errors but doesn't address the clinical requirement for detecting data loss or staleness. The clinical team's requirement isn't just about data integrity — it's about knowing when the data they're viewing is current and reliable. A checksum alone can't tell you that a packet was never received.

I'd approach this by first clarifying the clinical requirements: what does "detectable data loss" mean in practice? Is it acceptable to detect that a packet was lost within a certain time window? What's the maximum acceptable staleness before the display must alert the clinician? These parameters need to be defined before choosing a protocol.

From a technical standpoint, I'd recommend adding a sequence number to each packet and a timestamp or time-since-last-packet indicator. The sequence number allows the receiver to detect missing packets, and the display unit can track the time since the last valid packet was received. If that time exceeds a threshold, the display shows a "data stale" indicator. This doesn't require a complex protocol — it can be done with a simple addition to the existing packet structure.

I'd also consider the trade-offs of the proprietary protocol versus a standard one. A proprietary protocol with a checksum might be simpler to implement, but it puts the burden on the team to get the error detection right. A standard protocol like Bluetooth with its built-in error handling might be more robust, but it adds complexity and potentially higher power consumption. The key is to match the protocol's capabilities to the clinical requirements, not to minimize implementation effort.

Finally, I'd want to verify the solution through testing: simulate packet loss at various rates, verify that the display unit correctly indicates staleness, and confirm that the system recovers gracefully when the link is restored. This testing should be part of the design verification plan.

**Possible follow-ups:**
- How would you determine the appropriate staleness threshold for the display indicator?
- What if the proprietary protocol is already implemented and working — how would you justify the additional work to add sequence numbers?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The key challenge here is that sharing an ADC and multiplexer introduces potential cross-talk and timing issues that could affect accuracy. The test plan needs to verify not just that each sensor is accurate in isolation, but that they remain accurate when operating together through the shared signal chain.

I'd start by defining the accuracy requirements for each parameter from the design inputs — for example, temperature might need ±0.1°C accuracy while pressure needs ±2% of reading. These become the pass/fail criteria for the test.

The test plan would include several categories. First, baseline accuracy testing: measure each sensor against a reference standard while the other channel is idle. This establishes the individual accuracy. Second, simultaneous operation testing: run both sensors at their full sampling rate and verify that each maintains accuracy while the other is actively being sampled. This catches issues like multiplexer settling time, charge injection, or crosstalk between channels.

Third, I'd include worst-case timing tests: verify accuracy when the multiplexer is switching rapidly between channels, and when one sensor is at its extreme range while the other is at its opposite extreme. This tests for any interaction between the channels. Fourth, I'd test with realistic signal conditions — for example, a slowly varying temperature with a rapidly changing pressure, which is what the device might actually see in clinical use.

I'd also want to include a test for the ADC's common-mode rejection and any reference voltage stability issues, since both channels share the same reference. If the reference drifts with temperature, both measurements would be affected, and the test plan should include temperature cycling to catch this.

Finally, I'd consider whether the test plan needs to include statistical analysis — for example, testing multiple units to establish that the accuracy is consistent across the production population, not just on a single golden unit.

**Possible follow-ups:**
- How would you determine the appropriate sample size for the accuracy testing?
- What would you do if the simultaneous operation test reveals that one sensor's accuracy degrades when the other is active?

---

## Q4: You're leading a project where a field complaint reports that a medical device's patient-contacting temperature probe is reading approximately 2°C higher than a reference thermometer used by clinical staff, but the device passes its calibration check when returned to the manufacturer. How would you approach the investigation and corrective action process?

**Answer:** This is a classic "it works in the lab but not in the field" situation, and the first step is to resist the assumption that the device is fine just because it passes calibration. The fact that the device reads correctly in the lab but incorrectly in the field suggests an environmental or usage factor that isn't reproduced during calibration.

I'd structure the investigation in several phases. First, gather as much information as possible from the field: How many devices are affected? Is it isolated to one clinical site or widespread? What are the environmental conditions — ambient temperature, humidity, patient population? Is the discrepancy consistent (always 2°C high) or variable? Are there any patterns related to how the probe is used — for example, is it left in place for extended periods, or is it used intermittently?

Second, I'd examine the calibration procedure itself. The lab calibration likely uses a controlled temperature source, like a water bath or dry block, at specific set points. If the field discrepancy only appears at certain temperatures or under certain conditions, the calibration might not cover the full clinical range. I'd also look at how the calibration is performed — is the probe allowed to fully stabilize? Is the reference thermometer calibrated and traceable?

Third, I'd consider clinical usage factors. The 2°C offset could be caused by poor thermal contact between the probe and the patient — for example, if the probe isn't properly insulated from ambient air, or if it's being used with a cover or sheath that adds thermal resistance. It could also be a placement issue — the probe might be measuring skin temperature rather than core temperature, and the clinical staff's reference thermometer might be measuring a different site.

Fourth, I'd investigate the device's signal chain more deeply. Even though the device passes calibration, there could be a subtle issue like self-heating of the probe electronics, or a thermal coupling issue between the sensor and the housing that only manifests when the probe is in contact with a warm surface for extended periods.

For corrective action, I'd want to reproduce the field condition in the lab — for example, by simulating the clinical use scenario with a thermal phantom that mimics the patient interface. If we can reproduce the offset, we can then determine whether it's a design issue, a calibration issue, or a usage issue, and take appropriate action. This might involve updating the calibration procedure, modifying the probe design, or providing additional clinical guidance on proper placement.

**Possible follow-ups:**
- How would you determine whether the issue is a design flaw versus a user error?
- What would you do if you can't reproduce the 2°C offset in the lab?

---

## Q5: How would you approach developing a post-market surveillance plan for a medical device that includes both active monitoring of field performance and a mechanism for identifying emerging safety signals that weren't anticipated during the design phase?

**Answer:** A post-market surveillance plan needs to be proactive, not just reactive. The traditional approach of waiting for complaints to come in is insufficient — you need to actively seek out information about how the device is performing in the field and look for patterns that might indicate emerging safety issues.

I'd structure the plan around several complementary data sources. First, the obvious one: complaint handling. This includes not just complaints that come through the customer support line, but also complaints that might be captured through other channels — sales representatives, clinical training staff, or distributor feedback. The plan should define how these channels feed into the complaint system.

Second, active surveillance through clinical engagement. This could include periodic surveys of clinical users, structured interviews with key opinion leaders, or site visits to observe the device in actual use. The goal is to capture issues that users might not formally complain about — for example, a nurse might mention that the device is "a bit finicky" in a conversation, which could indicate a usability issue that hasn't risen to the level of a complaint.

Third, I'd include analysis of service and repair data. If the device is being returned for repair more frequently than expected, or if certain components are failing at a higher rate, that could indicate a design issue that hasn't yet manifested as a safety problem. This requires tracking not just the fact of the repair, but the root cause and the component involved.

Fourth, I'd look at indirect data sources: literature surveillance for similar devices, competitor recalls or safety notices, and changes in clinical practice that might affect how the device is used. For example, if a new clinical guideline recommends longer monitoring periods, that might stress the device in ways that weren't anticipated during design.

For identifying emerging safety signals, I'd establish a systematic review process. This would include regular trending of complaint data — looking for increases in frequency or severity, or new failure modes that haven't been seen before. I'd also define trigger criteria: for example, if a particular failure mode appears in more than a certain number of devices, or if there's a cluster of similar complaints within a short time period, that triggers a deeper investigation.

Finally, the plan needs to define how findings feed back into the design process. If the surveillance identifies a new hazard or a change in risk level, that information should flow back into the risk management file and potentially trigger a design change or updated instructions for use.

**Possible follow-ups:**
- How would you determine the appropriate frequency for reviewing surveillance data?
- What would you do if the surveillance data reveals a potential safety signal that doesn't meet the threshold for a formal recall?