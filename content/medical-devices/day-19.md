# medical-devices — Day 19

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where a sensor provides valid but out-of-range physiological readings (e.g., a heart rate of 240 bpm or a temperature of 42°C)?

**Answer:** I'd approach this as a three-layer problem: detection, response, and verification.

First, I'd clarify the requirements. The device needs a defined behavior for out-of-range readings — is it an alarm condition, a "measurement invalid" flag, or a combination? This should be documented in the software requirements specification (SRS) and traceable to the risk management file, since out-of-range readings often relate to patient safety hazards.

For the test strategy, I'd use a combination of unit, integration, and system-level tests:

- **Unit level:** Test the firmware functions that classify readings as valid, out-of-range, or invalid. This includes boundary testing at the exact thresholds, just above/below, and values that are clearly out of range. I'd also test the hysteresis behavior if the device uses it to prevent alarm chatter.
- **Integration level:** Inject simulated sensor data at the firmware interface — not just the raw ADC values, but also the processed values after calibration and filtering. This verifies that the classification logic works correctly with the actual data path.
- **System level:** Use a signal generator or sensor simulator connected to the actual hardware to produce out-of-range physiological signals. This verifies the entire chain from sensor input to display/alarm output.

A critical aspect is testing the *transition* behavior — what happens when the reading goes from normal to out-of-range, and then back to normal. The device should enter the alarm state correctly and clear it appropriately without false triggers or missed events. I'd also test edge cases like a reading that jumps directly from normal to far out-of-range, skipping intermediate values.

Finally, I'd verify that the out-of-range handling doesn't interfere with other device functions — for example, if one parameter is out of range, the device should still monitor and display other parameters correctly. This is particularly important for multi-parameter monitors where a single sensor failure shouldn't compromise overall functionality.

**Possible follow-ups:**
- How would you determine the appropriate thresholds for "out-of-range" — are these clinical decisions or engineering decisions?
- How would you test the device's behavior when the out-of-range reading is intermittent rather than sustained?

---

## Q2: During a design review for a medical device that uses a rechargeable battery, the firmware engineer proposes implementing a battery fuel gauge using voltage-based estimation, while the hardware engineer recommends adding a dedicated coulomb-counting fuel gauge IC. How would you approach this trade-off?

**Answer:** This is a classic trade-off between simplicity and accuracy, and the right answer depends heavily on the device's requirements and use case.

I'd start by asking what the fuel gauge is actually used for. Is it to display remaining battery percentage to the user, to trigger a low-battery alarm, or to estimate remaining operating time? The accuracy requirements differ significantly for each use case. For a medical device, the low-battery alarm is typically safety-critical — the user needs sufficient warning to complete the current procedure or safely power down.

Voltage-based estimation is simpler and cheaper — no additional hardware, just firmware using the ADC to measure battery voltage and map it to a state-of-charge curve. However, it has well-known limitations: the voltage-to-charge relationship is non-linear, especially for Li-ion batteries, and it's affected by load current, temperature, and battery age. Under varying load conditions — which are common in medical devices with motors, wireless communication, or sensors that draw different currents — voltage-based estimation can be off by 20-30% or more. This could mean the device reports 30% remaining when it actually has 10%, which is a safety concern.

Coulomb counting measures the actual charge flowing in and out of the battery, which is much more accurate under varying loads. The downside is additional hardware cost, PCB area, and complexity. Modern fuel gauge ICs also handle battery aging, temperature compensation, and self-discharge, which are difficult to do accurately with voltage-based methods.

My approach would be to evaluate the requirements first:

- What is the minimum acceptable accuracy for the remaining-capacity display?
- How much warning time does the user need before the battery is depleted?
- What is the load profile — constant or highly variable?
- What is the operating temperature range?

If the device has a relatively constant load and the low-battery alarm is set conservatively (e.g., alarm at 20% when the device can operate for 2 hours at 10%), voltage-based estimation might be acceptable. But if the load varies significantly — say, a motor that draws 10x the average current — or if the device must provide accurate remaining-time estimates, I'd lean toward the coulomb-counting IC.

I'd also consider a hybrid approach: use voltage-based estimation as a backup or calibration check, with coulomb counting as the primary method. Many fuel gauge ICs actually use both — coulomb counting for short-term accuracy and voltage-based correction for long-term drift.

For a medical device, I'd also consider the failure modes. If the fuel gauge IC fails, does the device have a fallback? Can the firmware detect a failed fuel gauge and switch to voltage-based estimation? This redundancy consideration is important for safety-critical functions.

**Possible follow-ups:**
- How would you validate the fuel gauge accuracy across the device's operating temperature range and battery aging?
- What information would you need from the battery manufacturer to implement either approach correctly?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure and display a physiological parameter with a specified accuracy, when the reference measurement method requires specialized test equipment that is only available at an external laboratory?

**Answer:** This is a common challenge in medical device development, and I'd approach it by breaking the verification into layers that can be tested locally versus those that require the external lab.

First, I'd identify exactly what the external lab provides. Is it a calibrated reference instrument, a tissue phantom, or a clinical-grade measurement system? Understanding what makes it special — calibration traceability, clinical relevance, or measurement precision — helps determine what can be tested locally.

For the local testing, I'd focus on what I can verify without the reference equipment:

- **Sensor characterization:** Test the sensor itself against a local reference that has known accuracy. For example, if the device measures temperature, I can use a calibrated thermocouple or a precision temperature source that's traceable to a national standard. This verifies the sensor and analog front-end.
- **Signal processing verification:** Inject known electrical signals at the sensor interface — for example, a precision voltage source or waveform generator — and verify that the firmware correctly processes, calibrates, and displays the value. This tests the digital signal chain without needing the physiological reference.
- **Repeatability and stability:** Measure the device's output repeatedly under controlled conditions to verify precision (repeatability), even if absolute accuracy can't be verified locally.

For the external lab testing, I'd plan a focused verification that specifically addresses the accuracy requirement. This might involve:

- Sending the device to the lab with a detailed test protocol that specifies the measurement points, environmental conditions, and acceptance criteria.
- Running a small number of devices (e.g., 3-5) through the external test to establish accuracy, then using local testing to verify that production units meet the same specification through correlation.

A key technique is establishing a correlation between local test methods and the external reference. For example, if the external lab uses a calibrated pressure source, I might use a local pressure standard that's been cross-calibrated against the same reference. This allows me to verify the device's accuracy locally with reasonable confidence, while the external lab provides the final authoritative verification.

I'd also consider whether the external test can be done earlier in the development cycle — for example, during design validation rather than design verification. This might allow me to identify accuracy issues before committing to the final design.

Finally, I'd document the rationale for the test strategy in the verification plan, including why certain tests are done locally and others externally, and how the results together demonstrate that the accuracy requirement is met.

**Possible follow-ups:**
- How would you handle a situation where the external lab's results don't match your local test results?
- How would you determine how many devices to send to the external lab for statistically meaningful results?

---

## Q4: You're leading a project where a supplier has delivered a batch of PCBs for a medical device, and incoming inspection reveals that the via fill material on a critical high-voltage isolation area is not fully cured. The supplier claims the boards will pass hi-pot testing and that the issue is cosmetic. How would you handle this situation?

**Answer:** This is a situation where I'd need to balance technical evidence, regulatory requirements, and the supplier relationship — but the decision itself should be driven by data and risk assessment, not by the supplier's assurance.

First, I'd verify the inspection finding. Is the incomplete curing confirmed by multiple inspection methods — visual inspection, cross-sectioning, or thermal analysis? I'd want to understand the extent of the issue: is it isolated to a few boards or systemic across the batch? This determines whether we're dealing with a sample issue or a process problem.

Next, I'd assess the technical impact. The supplier's claim that the boards will pass hi-pot testing is relevant but insufficient. The via fill material in a high-voltage isolation area serves multiple purposes: dielectric strength, moisture resistance, and mechanical integrity. Even if the boards pass hi-pot testing today, incomplete curing could lead to:

- **Moisture ingress over time:** Uncured or partially cured material is more porous and can absorb moisture, which degrades dielectric strength over time. This is particularly concerning for a medical device used in a home environment with potential humidity exposure.
- **Reduced mechanical strength:** The via fill provides structural support. Incomplete curing could lead to cracking or delamination under thermal cycling or mechanical stress.
- **Long-term reliability:** The device is expected to operate for years. A material property that's marginally acceptable at delivery may degrade unacceptably over the product's lifetime.

I'd also consider the regulatory implications. The design history file and risk management documentation likely specify the via fill material and its properties as part of the isolation barrier design. If the delivered boards don't meet the specified material properties, the device doesn't conform to its own design specification — regardless of whether it passes a particular test.

My approach would be:

1. **Quarantine the batch** and prevent any boards from being used in production or testing.
2. **Request additional data from the supplier:** Their process validation records, cure profile documentation, and any test data they have on the affected batch. I'd also ask for their definition of "fully cured" and how they verify it.
3. **Conduct additional testing on sample boards:** Hi-pot testing is necessary but not sufficient. I'd also consider insulation resistance testing, moisture absorption testing, or accelerated aging to assess long-term reliability.
4. **Evaluate the risk:** Using the risk management framework, I'd assess the probability and severity of failure if these boards were used. For a high-voltage isolation area in a medical device, the severity of failure is potentially life-threatening, so the risk tolerance is very low.
5. **Make a decision based on evidence:** If the testing demonstrates that the boards meet all relevant specifications — including long-term reliability — I might accept the batch with documented justification. But if there's any doubt, I'd reject the batch and require the supplier to correct their process.

Throughout this, I'd document everything in the non-conformance and corrective action system. The supplier's claim that the issue is "cosmetic" is an opinion; my job is to verify it with data and ensure the device meets its safety requirements.

**Possible follow-ups:**
- How would you verify that the incomplete curing doesn't affect long-term reliability without waiting years for real-time data?
- What would you do if the supplier refuses to accept the rejection and the schedule impact is significant?

---

## Q5: How would you approach developing a post-market surveillance plan for a medical device that includes both active monitoring of field performance and a mechanism for identifying emerging safety signals that weren't anticipated during the design phase?

**Answer:** A robust post-market surveillance (PMS) plan needs to be systematic, proactive, and designed to detect both known and unknown failure modes. I'd structure it around three complementary activities: passive surveillance, active surveillance, and signal detection.

**Passive surveillance** is the baseline — capturing complaints, adverse events, and service reports that come in through normal channels. This includes customer support calls, field service reports, and regulatory reporting. The key is ensuring that all relevant information is captured consistently and coded in a way that allows for trend analysis. I'd establish clear criteria for what constitutes a reportable event and ensure the team is trained to recognize and document them.

**Active surveillance** involves deliberately seeking out information about device performance rather than waiting for it to arrive. This could include:

- **Periodic surveys** of clinical users to gather feedback on usability, reliability, and any issues they've observed but haven't formally reported.
- **Analysis of service and repair data** — looking for patterns in failure rates, replacement parts, or firmware updates.
- **Review of literature and competitor information** — monitoring for similar devices with known issues that might indicate a problem with our device.
- **Analysis of device usage data** — if the device logs operational data, reviewing it for anomalies that might indicate emerging problems.

**Signal detection** is the analytical process of identifying patterns that suggest a safety issue. This involves:

- **Trend analysis:** Tracking complaint rates, failure rates, and other metrics over time. I'd establish baseline rates and statistical control limits to identify when a metric exceeds expected variation.
- **Stratified analysis:** Breaking down data by device version, manufacturing date, usage environment, or patient population to identify sub-groups with higher-than-expected risk.
- **Cross-correlation:** Looking for relationships between seemingly unrelated events — for example, a specific combination of error codes that appears before a particular failure mode.

For identifying *unanticipated* safety signals, I'd focus on creating an environment where unusual observations are captured and investigated rather than dismissed. This means:

- Encouraging field staff to report anomalies even if they don't meet formal reporting criteria.
- Regularly reviewing all complaints — not just serious ones — for patterns.
- Using a structured process for evaluating potential signals, such as a safety review committee that meets periodically to review PMS data.

The PMS plan should also define how findings feed back into the quality system. If a signal is identified, there should be a clear pathway to escalate it — whether that's a formal investigation, a risk assessment update, or a field safety corrective action.

Finally, I'd ensure the PMS plan is documented in the post-market surveillance report and updated regularly based on what we learn. The plan itself should be a living document that evolves as the device matures and as new information becomes available.

**Possible follow-ups:**
- How would you determine the appropriate sample size or data collection period for detecting a low-frequency but serious safety signal?
- How would you distinguish between a genuine safety signal and random variation in complaint data?