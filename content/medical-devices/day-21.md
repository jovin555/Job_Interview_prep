# medical-devices — Day 21

## Q1: How would you approach designing the patient leakage current measurement path for a medical device that has multiple BF-type applied parts, where the device must meet IEC 60601-1 leakage current limits under both normal and single-fault conditions?

**Answer:** The key challenge with multiple BF applied parts is that leakage current can flow between applied parts, not just from each applied part to earth or from applied part to mains. I would start by identifying all patient-connected circuits and classifying each applied part according to IEC 60601-1 definitions, then map out all possible leakage paths: from each applied part to earth, between applied parts, and from each applied part to mains under normal and single-fault conditions.

For the measurement setup, I would use the measuring device (MD) specified in IEC 60601-1, which simulates the patient's body impedance. Each applied part needs to be tested individually while the others are connected to the patient terminals of the measuring device. The critical consideration is that the measurement configuration must reflect the worst-case clinical use scenario — for example, if the device is used with multiple sensors on the same patient simultaneously, the test must account for current flowing between those sensors.

From a design perspective, I would focus on the input protection circuitry and the isolation barrier. Each applied part input should have its own current-limiting impedance, and the isolation between applied parts needs to be sufficient to prevent hazardous current from flowing between them. I would also consider the Y-capacitor placement across the isolation barrier — these are often the main contributors to patient leakage current at mains frequency. If measurements exceed limits, I would look at reducing Y-capacitance, improving the isolation barrier design, or adding additional impedance in series with the patient connections.

Finally, I would ensure the test plan covers all required conditions: normal condition, single-fault conditions (such as one mains conductor interrupted), and the appropriate frequency range — leakage current limits apply not just at 50/60 Hz but also at higher frequencies, where the measuring device's frequency response matters.

**Possible follow-ups:** How would you determine whether a particular applied part is BF or CF type, and how does that classification affect the leakage current limits? What design changes would you consider if patient leakage current is marginally above the limit?

---

## Q2: How would you approach developing a design verification test plan for a medical device that must meet both IEC 60601-1 general safety requirements and a particular standard (e.g., IEC 60601-2-25 for monitoring devices), when the two standards have overlapping but not identical requirements?

**Answer:** The first step is to perform a thorough standards gap analysis. I would create a requirements matrix that maps every clause from the general standard, the particular standard, and any applicable collateral standards (like IEC 60601-1-2 for EMC) to identify where requirements overlap, where they conflict, and where the particular standard supersedes or adds to the general standard. This matrix becomes the foundation for the test plan.

For overlapping requirements, the general principle is that the more stringent requirement applies, but I would verify this against the specific wording — sometimes the particular standard modifies the test method rather than just the limit. For example, a particular standard might specify a different test setup or measurement procedure for the same parameter. I would document these decisions in the test plan with clear traceability to both standards.

The test plan itself would be organized by test category (safety, EMC, performance, environmental) rather than by standard, so that tests covering similar aspects are grouped together. Each test case would reference the specific clause from each applicable standard and note whether the test is identical across standards, combined, or separate. Where the particular standard requires additional tests not in the general standard — such as specific performance tests for the device's measurement accuracy — I would ensure these are included with appropriate pass/fail criteria.

I would also consider the sequence of testing. Some tests can be combined (e.g., performing leakage current measurements at the same time as functional tests), while others must be performed separately because they require different test setups or because one test might damage the device and affect subsequent results. The plan should also account for test sample allocation — some tests are destructive, so multiple samples may be needed.

**Possible follow-ups:** How would you handle a situation where the particular standard and general standard have conflicting requirements that cannot both be met? How would you document the rationale for test exclusions or deviations in the verification report?

---

## Q3: How would you approach investigating a field complaint where a medical device's patient-contacting temperature sensor is reading approximately 2°C higher than the reference thermometer used by clinical staff, but the device passes its calibration check when returned to the manufacturer?

**Answer:** This is a classic "cannot reproduce" field complaint, and the investigation needs to be systematic. I would start by gathering all available information: the specific devices involved, usage conditions, patient populations, and the exact discrepancy observed. The fact that the device passes calibration in the lab suggests either the issue is environmental, usage-related, or intermittent.

First, I would examine the measurement chain — the sensor, analog front-end, ADC, and firmware processing. A 2°C offset could come from several sources: sensor self-heating (the sensor's own power dissipation raising the measured temperature), poor thermal coupling between the sensor and the patient's skin, ambient temperature effects on the reference junction or signal conditioning, or a firmware offset error that only manifests under certain conditions.

I would look at the clinical usage pattern. If the sensor is held against the skin, the applied pressure and contact area affect thermal coupling. If the device is used in a cold environment, the sensor might be measuring a combination of skin temperature and ambient temperature. I would also check whether the reference thermometer used by clinical staff was itself calibrated — this is a common source of apparent discrepancies.

For the investigation, I would set up a controlled test that replicates the clinical usage conditions as closely as possible, including the same sensor placement method, ambient temperature range, and measurement duration. I would also review the firmware algorithm for any temperature compensation or filtering that might introduce offset under certain conditions. If the issue is intermittent, I would consider adding temporary data logging to capture the raw sensor readings and intermediate processing values during clinical use.

The corrective action might involve improving sensor thermal coupling, adding a calibration offset that accounts for the clinical use environment, or updating the user instructions to specify proper sensor placement. I would also review the risk management file to see if this failure mode was anticipated and whether the risk controls are adequate.

**Possible follow-ups:** How would you determine whether this is a single-device issue or a systemic issue affecting the product line? What role would the post-market surveillance process play in identifying this type of issue earlier?

---

## Q4: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a sensor that intermittently provides valid but erroneous readings — for example, a pressure sensor that occasionally reports a spike that is within the valid range but physiologically impossible?

**Answer:** This is fundamentally a test design problem that requires understanding both the sensor characteristics and the physiological signal being measured. I would start by characterizing the failure mode: what does "intermittent" mean in terms of frequency and duration? What is the magnitude of the spike relative to the normal signal? Is the spike isolated or does it affect multiple consecutive samples?

The test strategy would combine several approaches. First, I would use fault injection at the firmware level — creating test hooks that allow injecting specific sensor values or patterns into the data stream to verify the device's response. This allows deterministic testing of the detection and handling logic without relying on actual sensor faults occurring naturally.

Second, I would use recorded real-world data. If we have captured sensor data from clinical use or field testing that contains these artifacts, we can replay that data through the firmware in a test harness to verify the device responds correctly. This is particularly valuable because it tests with realistic signal characteristics.

Third, I would develop a set of synthetic test waveforms that represent the range of possible erroneous readings — isolated spikes, bursts of erroneous values, gradual drift that stays within valid range but is physiologically impossible, and readings that are valid for the sensor but inconsistent with other physiological parameters. The test cases would cover both detection (does the device identify the reading as erroneous?) and response (does the device ignore the reading, flag it, alarm, or take other action?).

The key design question is what the device should do when it detects an erroneous reading. The response depends on the clinical context — for a monitoring device, the safest approach might be to flag the reading as suspect and continue monitoring, while for a device that controls therapy, the response might need to be more conservative. The test plan must verify that the response is appropriate for each failure scenario.

I would also include tests for the boundary conditions: readings that are marginally within the physiologically plausible range, readings that are valid for the sensor but inconsistent with the patient's condition, and situations where the erroneous readings occur during a genuine physiological event. The goal is to verify that the device neither misses genuine events nor generates excessive false alarms.

**Possible follow-ups:** How would you determine the threshold between a reading that should be rejected as erroneous versus one that should trigger an alarm? How would you verify that the error handling logic itself doesn't introduce new failure modes?

---

## Q5: You're leading a project where the quality manager and the firmware lead disagree on the appropriate software safety classification under IEC 62304 for a medical device that monitors patient physiology and provides alerts, but does not directly control therapy. The quality manager argues for Class B, while the firmware lead argues for Class A. How would you handle this disagreement?

**Answer:** This is a decision that has significant implications for the development process, documentation requirements, and testing rigor, so it's important to resolve it based on the standard's requirements rather than on schedule or effort considerations. I would start by bringing the team back to the IEC 62304 classification criteria, which are based on the potential harm to the patient if the software fails or behaves incorrectly.

The key question is: could a software failure lead to patient harm? For a monitoring device that provides alerts, the answer depends on whether the alerts are the primary risk control measure. If the device is the sole mechanism for detecting a critical condition and alerting clinical staff, then a software failure that prevents or delays an alert could result in patient harm. This would suggest Class B at minimum, and potentially Class C if the software directly controls therapy or is the sole risk control for a hazardous situation.

I would facilitate a structured discussion where each person presents their rationale based on the standard's definitions and the device's intended use. The firmware lead's argument for Class A would need to demonstrate that a software failure cannot contribute to patient harm — which is difficult to argue for a monitoring device, since a failure could result in missed or delayed alerts. The quality manager's argument for Class B is likely more defensible, as it acknowledges that software failures could contribute to hazardous situations even if the software doesn't directly control therapy.

I would also consider the risk management file — the hazard analysis should identify the software functions that are risk control measures. If the alerting function is identified as a risk control measure in the risk management file, that directly supports a higher classification. The classification should be consistent between the risk management file and the software development plan.

If the disagreement persists, I would suggest consulting with a notified body or regulatory consultant who has experience with IEC 62304 classifications for similar devices. The decision should be documented with clear rationale in the software development plan, and I would ensure that the classification is reviewed as part of the design review process. It's also worth noting that the classification can be revisited if the device design changes — for example, if the device adds a therapy control function in the future, the classification would need to be reassessed.

**Possible follow-ups:** How would you document the classification decision and rationale in the software development plan? What would you do if the team reaches a consensus on Class B but the schedule impact is significant?