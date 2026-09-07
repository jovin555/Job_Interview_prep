# medical-devices — Day 48

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during normal operation, given that the device must continue monitoring and displaying physiological data in real time?

**Answer:** The core challenge here is that memory corruption is a single-fault condition that could affect both the monitoring function and the device's ability to recover. I'd structure the strategy around three layers: detection, containment, and recovery.

First, detection. I'd want to understand what corruption mechanisms are credible — bit flips from cosmic rays or EMI, incomplete writes due to power loss, or wear-leveling failures in flash. The firmware should use error-detecting codes (CRC or ECC where available) on critical data structures, and I'd verify that these detection mechanisms actually trigger under fault injection. This means testing with deliberately corrupted memory contents — flipping bits in configuration blocks, calibration data, and logged patient data — and confirming the device flags the corruption appropriately.

Second, containment. The device must continue real-time monitoring even if non-volatile memory is unavailable. I'd verify that the firmware separates the real-time monitoring path from any non-volatile memory access — for example, that a stuck or failing flash interface doesn't block the sensor sampling loop. This might involve testing with the memory interface physically disconnected or held in a busy state, and confirming that monitoring and alarm functions continue on their own priority schedule.

Third, recovery. The device needs a defined path back to a known-good state. I'd test scenarios where the device detects corruption at startup versus mid-operation. For mid-operation corruption, the device should ideally revert to safe default configuration while preserving the ability to monitor, and clearly indicate to the clinician that a configuration fault has occurred. For startup corruption, I'd verify the device can fall back to a redundant firmware image or factory defaults rather than becoming bricked.

The test plan would combine unit-level tests for the memory management module, integration tests with fault injection at the driver level, and system-level tests where corruption is induced while the device is actively monitoring a simulated patient. Throughout, I'd track that the device never loses the real-time monitoring function and that any alarms triggered during the fault are accurate and timely.

**Possible follow-ups:** How would you decide which data structures are critical enough to warrant error detection versus which can tolerate corruption? What role would a watchdog timer play in this recovery strategy?

---

## Q2: During a design review for a medical device that monitors fetal and maternal heart rates during labor, the firmware engineer proposes implementing heart rate variability (HRV) analysis as a software feature to detect fetal distress earlier than current methods. The algorithm is novel and has not been clinically validated. How would you approach evaluating this proposal?

**Answer:** This is fundamentally a question about scope, evidence, and risk. The proposal has two distinct aspects: the technical implementation of HRV analysis, and the clinical claim that it can detect fetal distress earlier. These need to be evaluated separately.

From a regulatory perspective, if the device is going to present HRV-derived information as an indicator of fetal distress, that's a new intended use that likely requires clinical validation — you can't just add it as a software feature. The firmware engineer may be proposing something that changes the device's risk classification or requires a clinical trial. I'd want to clarify whether this is intended as a research feature, a screening tool with clear limitations, or a diagnostic claim, because each has very different regulatory implications.

From a technical standpoint, HRV analysis on fetal heart rate data is challenging. Fetal heart rate traces are noisy, subject to signal dropout from fetal movement, and the beat-to-beat intervals are derived from Doppler ultrasound or ECG, each with different accuracy characteristics. I'd ask the firmware engineer to demonstrate that the underlying data quality supports the analysis — for example, what's the expected beat-detection accuracy, and how does the algorithm handle missing or ectopic beats? A novel algorithm that hasn't been validated against annotated clinical databases would need a rigorous verification approach, including testing against reference datasets with known ground truth.

I'd also consider the user interface and alarm implications. If HRV analysis generates new alerts, what's the false alarm rate? In a labor ward, false alarms cause stress for both patients and staff, and alarm fatigue is a real patient safety issue. The feature would need to go through usability engineering to understand how clinicians interpret and act on the information.

My approach would be to scope this as a potential future enhancement rather than a feature for the current development cycle, unless the clinical team can articulate a clear use case and the regulatory path is understood. I'd suggest the firmware engineer document the algorithm's theoretical basis, identify validation datasets, and propose a retrospective analysis to establish preliminary evidence before any prospective clinical use is considered.

**Possible follow-ups:** How would you handle the situation where the firmware engineer has already implemented the feature and it's working in the lab? What criteria would you use to decide whether this feature changes the device's risk classification under IEC 62304?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure uterine contraction pressure during labor, where the sensor is a pressure transducer in contact with the patient's abdomen and the device must maintain specified accuracy across a range of patient body habitus (e.g., BMI from 18 to 45)?

**Answer:** The challenge here is that the measurement accuracy depends on both the sensor's electrical performance and the mechanical coupling between the sensor and the patient — and the coupling varies significantly with body habitus. A design verification plan needs to address both the sensor system in isolation and the system as it would perform clinically.

I'd start by defining what "specified accuracy" means in this context. For uterine contraction monitoring, the clinically relevant parameters are the amplitude and frequency of contractions, and the baseline tone. The device specification should state accuracy limits for these parameters, not just raw pressure readings. I'd work with the clinical team to understand what accuracy is clinically meaningful — for example, is ±10% of peak amplitude acceptable, or does the device need to track relative changes rather than absolute values?

For the sensor system itself, I'd verify the pressure transducer's accuracy across the specified measurement range using a calibrated pressure source. This would include temperature effects, since the sensor may warm up during use, and long-term drift over the expected duration of monitoring. I'd also test the signal conditioning chain — amplification, filtering, and digitization — to ensure the electronics don't introduce error.

The harder part is verifying performance across body habitus. Since we can't test on real patients across the full BMI range in a design verification lab, I'd use a combination of approaches. First, a mechanical phantom or test fixture that simulates different tissue thicknesses and stiffnesses, allowing us to characterize how the sensor's coupling changes. Second, a clinical validation study with a representative patient population, where the device's readings are compared to a reference method — typically an intrauterine pressure catheter, which is the gold standard but invasive. The clinical study would need ethics approval and careful patient recruitment to ensure coverage across the BMI range.

I'd also consider whether the device needs to compensate for coupling variations. If the sensor output depends on tissue properties, the firmware might need to calibrate or normalize the signal based on some measurable parameter — for example, the baseline pressure or the signal quality. This would need to be designed in from the start, not added after testing reveals problems.

The verification plan would therefore have three tiers: bench testing of the sensor and electronics, phantom testing across simulated body habitus, and clinical validation with a reference method. Each tier has different pass/fail criteria, and the traceability from clinical requirements to bench test specifications needs to be documented in the design history file.

**Possible follow-ups:** How would you handle a situation where the phantom testing shows acceptable accuracy but the clinical validation reveals BMI-dependent bias? What reference standard would you use for the clinical validation, and how would you address its limitations?

---

## Q4: You're leading a project where a field complaint reports that a medical device's patient-contacting temperature probe is reading approximately 2°C higher than a reference thermometer used by clinical staff, but the device passes its calibration check when returned to the manufacturer. How would you approach the investigation and corrective action process?

**Answer:** This is a classic "it works in the lab but not in the field" scenario, and the key insight is that the device passing calibration at the manufacturer doesn't mean it's performing correctly in clinical use. The investigation needs to focus on understanding the conditions of use that differ from the calibration environment.

I'd start by gathering as much information as possible about the clinical context. Where was the probe placed — skin surface, axillary, oral? What was the patient's condition — was there poor perfusion, edema, or localized inflammation that could affect readings? How was the reference thermometer used — was it calibrated, and was it measuring the same physiological site? A 2°C discrepancy could be a device problem, a measurement technique problem, or a reference standard problem.

The fact that the device passes calibration suggests the electronics and sensor are functioning within specification. This points toward a use-related or environmental factor. One common issue is poor thermal coupling — if the probe isn't making good contact with the patient, it may be measuring a combination of skin temperature and ambient temperature, which could read higher or lower depending on conditions. Another possibility is that the probe is being affected by its own self-heating, or that the reference thermometer was measuring a different site with a genuinely different temperature.

I'd also examine the device's clinical use instructions. Is there a settling time requirement that staff might not be following? Is the probe designed for a specific placement that's not being used consistently? I'd want to observe the device being used in the clinical environment, if possible, to understand the actual use conditions.

From a corrective action perspective, I'd approach this as a potential use-error or usability issue rather than assuming a hardware defect. The investigation would follow a structured root-cause analysis — I'd convene a team including clinical representatives, the field service engineer, and the design engineer, and use a fishbone diagram to systematically explore patient factors, device factors, environmental factors, and procedural factors. If the root cause turns out to be usability-related, the corrective action might involve revised instructions, additional training, or a design change to make correct placement more intuitive.

If we can't reproduce the issue and can't identify a root cause from the field data, I'd consider whether to deploy additional data logging capability to capture more information during clinical use, or to conduct a focused clinical observation study. The key principle is that we don't close the complaint just because the device passes bench testing — we need to understand why the clinical reading was discrepant.

**Possible follow-ups:** How would you handle a situation where the clinical staff are confident in their measurement technique and insist the device is faulty? What would you do if the investigation suggests the reference thermometer was the source of error, but the clinical team disputes this?

---

## Q5: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's real-time clock (RTC) battery is depleted, given that the device logs time-stamped physiological data that may be used for clinical decision-making?

**Answer:** The RTC battery depletion scenario is interesting because it's not a sudden failure — it's a gradual degradation that the device should ideally anticipate. The test strategy needs to cover both the detection of the low-battery condition and the behavior when the RTC actually loses power.

First, I'd want to understand the device's requirements for time-stamped data. If the data is used for clinical decision-making, the timestamps need to be trustworthy. The device should have a defined behavior when it can no longer maintain accurate time — it shouldn't silently log data with incorrect timestamps. I'd expect the device to either flag data as having uncertain timestamps, or to prompt the user to set the time when power is restored.

For the test strategy, I'd start with the RTC low-battery warning. The firmware should detect when the RTC battery voltage drops below a threshold and alert the user — typically through a visual indicator or a message on the display. I'd test that this warning appears at the correct voltage threshold, that it's persistent (not a one-time message that can be missed), and that it doesn't interfere with the device's monitoring functions.

Next, I'd test the behavior when the RTC battery is fully depleted. This could happen while the device is on mains power — in which case the main system clock might still be running — or while the device is completely powered off. The critical question is what happens to the RTC's time and date when power is lost. Most RTCs will reset to a default time or stop counting, and the device needs to detect this condition when it next powers up.

I'd test the power-up sequence with a depleted RTC battery. The device should recognize that the RTC time is invalid — for example, by checking a "clock integrity" flag or by validating that the time is within a plausible range. The device should then prompt the user to set the correct time before resuming normal operation, or should clearly mark any logged data as having uncertain timestamps until the time is set.

For the data logging aspect, I'd verify that data logged before the RTC failure retains its original timestamps, and that data logged after the failure — but before the user resets the time — is either not logged, logged with a clear "time not set" flag, or logged with a relative time reference that can be reconciled later. The worst case would be silently logging data with incorrect absolute timestamps, which could mislead clinical decision-making.

I'd also test the transition when the RTC battery is replaced. The device should handle this gracefully — ideally the main battery or a supercapacitor maintains the RTC during the battery swap, or the device clearly indicates that time needs to be reset. The test plan would include fault injection to simulate RTC battery failure at various points in the device's operation — during startup, during active monitoring, and during data download — to verify consistent behavior.

**Possible follow-ups:** How would you verify that the device's time-stamping is accurate after the RTC battery is replaced and the time is reset? What design changes might you consider to make the device more resilient to RTC battery depletion in the first place?