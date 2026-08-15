# medical-devices — Day 25

## Q1: How would you approach designing the electrical safety test strategy for a medical device that has multiple applied parts with different patient protection classifications (e.g., one BF-type and one CF-type applied part)?

**Answer:** The first step is to confirm the applied part classifications by reviewing the intended use and the pathways through which each part contacts the patient. A CF-type part has the most stringent leakage current limits because it's intended for direct cardiac contact, while BF-type parts allow slightly higher leakage. Once classifications are confirmed, I'd map out the test matrix required by IEC 60601-1, which includes normal condition (NC) and single-fault condition (SFC) tests for each applied part, measured individually and then with all applied parts connected simultaneously to simulate realistic use.

For the test setup, I'd use a measuring device (MD) that meets the input impedance and frequency response requirements of the standard. The key nuance is that when you have multiple applied parts, you need to test leakage between each applied part and earth, between each applied part and the other applied parts, and between all applied parts tied together and earth. This ensures you're capturing the worst-case current path.

I would also consider the polarity of the mains supply — both normal and reversed polarity need to be tested — and the position of the device's power switch (on/off, and in standby if applicable). For SFC testing, I'd systematically open or short each protective component (e.g., one ground conductor at a time, one Y-capacitor at a time) to find the worst-case leakage path. The test plan should be documented in advance with pass/fail criteria tied directly to the applicable limits from Table 2 of IEC 60601-1 (or the relevant tables for the device's classification).

One practical consideration: if the device has a patient cable that can be disconnected, I'd test with the cable in both the connected and disconnected states, because the cable itself can act as an antenna or create additional leakage paths. I'd also verify that the test equipment is properly calibrated and that the measurement setup doesn't introduce parasitic paths that would give false readings.

**Possible follow-ups:**
- How would you determine whether a particular applied part should be classified as BF or CF during the design phase?
- What would you do if the device passes individual applied part tests but fails when all applied parts are tested simultaneously?

---

## Q2: How would you approach verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory is full, given that the device must continue monitoring and displaying physiological data in real time?

**Answer:** This is fundamentally a question about graceful degradation and ensuring that a non-critical function (data logging) never compromises a safety-critical function (real-time monitoring and display). The first step is to define the expected behavior in the firmware requirements: when storage is full, the device should continue monitoring and displaying data without interruption, and the logging function should either stop gracefully, overwrite the oldest data (circular buffer), or alert the user — depending on the clinical requirements.

For verification, I'd structure the test strategy in layers. At the unit level, I'd test the storage management module in isolation: fill the memory to exactly 100%, then attempt writes and verify the defined behavior occurs (e.g., the write is rejected with an error code, or the oldest data is overwritten). I'd also test boundary conditions — 99%, 99.9%, and 100% full — because that's where off-by-one errors typically hide.

At the integration level, I'd verify that the logging module correctly communicates the full condition to the alarm/notification system and that the monitoring path is completely unaffected. This means running the device with a full memory while simultaneously injecting physiological signals and verifying that the display updates at the required rate with correct values.

At the system level, I'd run a long-duration test where the device operates continuously until memory fills, then continues operating for an extended period (e.g., 24-48 hours) to confirm no memory leaks, no performance degradation, and no unexpected resets. I'd also test the behavior when the user clears the log or replaces the storage medium, to verify the device returns to normal logging without requiring a reboot.

A critical aspect is fault injection: I'd simulate write failures (not just a full condition, but actual write errors) to verify the firmware handles the error path correctly. This could be done by using a test harness that intercepts the storage API calls and returns error codes, or by using a debugger to set breakpoints and modify return values. The key is to verify that the error handling doesn't introduce any timing delays that could affect the real-time monitoring loop.

Finally, I'd review the risk management file to confirm that the hazard of data loss (or inability to log) has been assessed, and that the risk control measures (e.g., user notification, circular buffer) are verified and validated.

**Possible follow-ups:**
- How would you decide between a circular buffer and a "stop logging and alert the user" approach?
- What testing would you do to verify that the firmware doesn't have a memory leak during extended operation?

---

## Q3: During a design review for a medical device that uses an external AC-DC power adapter, the firmware engineer proposes adding a "low battery" warning that triggers at 15% remaining capacity, while the clinical team wants the warning at 25% to give users more time to connect mains power. The battery chemistry's discharge curve is relatively flat until the last 10%, making voltage-based estimation unreliable below 20%. How would you approach this trade-off?

**Answer:** This is a classic tension between clinical usability and technical feasibility. The first thing I'd do is separate the two questions: what the user needs to know, and what the system can reliably measure. The clinical team's concern is legitimate — if the device dies during a procedure, that's a patient safety issue. But a warning at 25% that's based on unreliable estimation could be worse than a warning at 15% that's accurate, because a false "low battery" warning can cause alarm fatigue or unnecessary interruption of care.

I'd approach this by examining what battery state-of-charge information is actually available. If the device uses a simple voltage-based fuel gauge, the accuracy at 25% might be ±10% or worse, which means the warning could trigger anywhere from 15% to 35% actual capacity. That's not a reliable basis for a clinical alarm. If we add a coulomb-counting fuel gauge IC, we can improve accuracy to perhaps ±3-5%, which would make a 25% threshold meaningful.

The decision then becomes a trade-off between hardware cost/complexity and clinical requirements. If the device already has the I2C bus available and the cost increase is acceptable, adding a proper fuel gauge IC is the cleanest solution. If we're constrained to voltage-based estimation, I'd propose a compromise: keep the warning threshold at 25% but implement it as a two-stage alert — an informational "battery low" at 25% that's advisory, and a more urgent "battery critically low" at 10-15% that's based on a more conservative estimate. The informational alert would be designed to be non-intrusive (e.g., a visual indicator rather than an audible alarm), so that if it's slightly early, it doesn't cause unnecessary alarm.

I'd also consider whether the device can measure actual discharge current and use that to improve the estimate. If the device has a current sense resistor or a battery monitor IC, we can use coulomb counting to get a more accurate state-of-charge. If not, we could implement a discharge-rate compensation algorithm that adjusts the voltage-based estimate based on the known load profile.

Regardless of the approach, I'd require that the firmware team provide data on the accuracy of the estimation method across the operating temperature range and load conditions, and that the verification plan includes testing at the threshold boundaries to confirm the warning triggers reliably and consistently. The final decision would be documented in the risk management file, with the residual risk of unexpected battery depletion assessed against the benefit of the warning.

**Possible follow-ups:**
- How would you verify the accuracy of the battery fuel gauge across the device's operating temperature range?
- What would you do if the clinical team insists on a 25% threshold but the hardware team says a fuel gauge IC can't be added without a board spin?

---

## Q4: How would you approach developing a design verification test plan for a medical device that must measure and display a physiological parameter with a specified accuracy, when the reference measurement method requires specialized test equipment that is only available at an external laboratory?

**Answer:** The first step is to clarify what the external laboratory can provide and what the constraints are — how long the equipment is available, whether we can bring the device to the lab, or whether we need to ship the device and have lab personnel run the test. This determines whether we can do a full verification at the external lab or whether we need a hybrid approach.

I'd structure the verification in two phases. Phase one is an internal characterization using whatever test equipment we have available — even if it's not the gold standard, it can give us confidence that the device is in the right ballpark and identify any gross errors before we spend money and time at the external lab. This internal testing would use a calibrated reference that's traceable to a national standard, even if its accuracy is lower than the external lab's equipment. The goal is to catch obvious issues early.

Phase two is the formal verification at the external lab. Before going, I'd develop a detailed test protocol that specifies: the exact test points (e.g., specific physiological values across the measurement range), the number of repetitions, the environmental conditions, the data recording method, and the acceptance criteria. I'd also include a pre-test checklist to confirm the device is properly calibrated and configured before the formal measurements begin.

A key consideration is whether the external lab's equipment can be used to test multiple devices or multiple configurations in one visit. If so, I'd plan to bring multiple units (e.g., a pre-production unit and a final unit) to maximize the value of the lab time. I'd also bring spare batteries, cables, and any accessories that might be needed.

If the external lab is in a different location and we can't be present during testing, I'd work with the lab to define a clear test procedure that their technicians can follow, including photographs or videos of the setup, and I'd request that they record raw data (not just pass/fail results) so we can analyze the results ourselves. I'd also ask for calibration certificates for their equipment to confirm traceability.

Another approach is to use a transfer standard: if we have a portable reference device that's been calibrated against the external lab's equipment, we can use it for internal testing and then periodically re-calibrate it at the external lab. This gives us ongoing verification capability without requiring the external lab for every test.

Finally, I'd ensure that the verification results are documented with enough detail to support the design history file — including the test equipment identification, calibration dates, environmental conditions, and any deviations from the test protocol. The traceability from the verification results back to the design input requirements is critical for regulatory submission.

**Possible follow-ups:**
- How would you handle a situation where the external lab's equipment is only available for a limited window and the device isn't quite ready for formal verification?
- What would you do if the external lab's results show the device is out of specification, but your internal testing suggested it was within spec?

---

## Q5: You're leading a project where a field complaint reports that a medical device's patient-contacting temperature probe is reading approximately 2°C higher than a reference thermometer used by clinical staff, but the device passes its calibration check when returned to the manufacturer. How would you approach the investigation and corrective action process?

**Answer:** This is a classic "it works in the lab but not in the field" scenario, and the first principle is to resist the temptation to dismiss the complaint as user error. A 2°C discrepancy is clinically significant for a temperature measurement, and the fact that the device passes calibration doesn't mean there isn't a real problem — it means the problem may be environmental, usage-related, or intermittent.

I'd structure the investigation in four phases. First, gather all available information from the field: the exact clinical context (was the probe in continuous contact with the patient? was it used in a room with a radiant warmer? was there a drape or blanket between the probe and skin?), the reference thermometer's calibration status, and whether the discrepancy was consistent or intermittent. I'd also check if there were any other complaints from the same facility or with the same lot number of probes.

Second, I'd replicate the conditions. If the device passes calibration in a controlled lab environment, I'd try to reproduce the field conditions — for example, testing the probe with simulated skin contact at different pressures, with different types of coupling gel, or in the presence of external heat sources. I'd also test the probe's response time, because a slow-responding probe might read low initially but could read high if it's being compared to a fast-responding reference during a dynamic temperature change.

Third, I'd examine the probe's construction and the signal chain. A 2°C offset could be caused by a thermistor that's slightly out of tolerance at a specific temperature range, a poor thermal contact between the thermistor and the probe tip, or a self-heating effect where the excitation current causes the thermistor to warm up. I'd review the probe's calibration data across the full temperature range, not just at the calibration points, and I'd test multiple probes from the same lot to see if the issue is systematic or isolated.

Fourth, I'd consider the clinical use case. If the probe is used in a neonatal or pediatric setting, the measurement site and the way the probe is secured can significantly affect readings. I'd work with the clinical team to understand the exact placement procedure and compare it to the instructions for use. If there's a discrepancy between how the device is intended to be used and how it's actually being used, that's a usability issue that needs to be addressed through labeling, training, or design changes.

For the corrective action process, I'd document the investigation in the complaint handling system and determine whether this is an isolated incident or part of a trend. If it's isolated, the corrective action might be limited to retraining or a labeling update. If it's a trend, I'd initiate a formal corrective and preventive action (CAPA) and consider whether a design change is needed — for example, a different thermistor with tighter tolerance, a redesigned probe tip with better thermal contact, or a firmware change to compensate for self-heating.

Throughout the investigation, I'd keep the risk management file updated, because a temperature measurement error of 2°C could have clinical consequences depending on how the measurement is used. The investigation would also inform whether the device's calibration procedure needs to be updated to catch this type of issue during manufacturing.

**Possible follow-ups:**
- How would you determine whether this is an isolated incident or part of a broader trend?
- What would you do if the investigation reveals that the discrepancy is caused by a known limitation of the sensor technology, and a design fix would require a significant hardware revision?