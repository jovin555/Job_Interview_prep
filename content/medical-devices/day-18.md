# medical-devices — Day 18

## Q1: How would you approach verifying that a medical device's firmware correctly handles a situation where a sensor is disconnected or shorted during patient monitoring, given that the device must continue monitoring other parameters and must not generate false alarms?

**Answer:** I'd approach this as a combination of fault detection design and verification strategy. First, I'd ensure the firmware architecture explicitly distinguishes between "sensor absent" (disconnected), "sensor fault" (shorted or out-of-range), and "physiological event" (valid but abnormal reading). Each state should have defined behavior: a disconnected sensor should trigger a technical alarm with a distinct priority, while a shorted sensor might be treated differently depending on whether the short produces a plausible-but-wrong reading.

For verification, I'd build a test matrix that covers: open circuit, short to ground, short to supply, short between signal lines, and intermittent connections. I'd use a combination of hardware fault injection (relay or MOSFET-based switching on the sensor lines) and firmware-level simulation where the ADC input is forced to specific values. The key is verifying not just that the device detects the fault, but that it continues monitoring other parameters correctly, logs the fault appropriately, and doesn't enter an undefined state. I'd also test recovery — when the sensor is reconnected, the device should resume normal monitoring without requiring a power cycle, and the data stream should show a clear discontinuity marker so clinicians know there's a gap.

For a multi-parameter device, I'd pay particular attention to whether a fault on one sensor could affect the signal conditioning or power supply of another sensor — for example, a shorted sensor pulling down a shared reference voltage. That's a hardware concern that firmware fault detection alone can't address, so I'd want cross-checks between the analog front-end design and the firmware detection thresholds.

**Possible follow-ups:** How would you determine the appropriate alarm priority for a sensor fault versus a physiological alarm? How would you verify that the device doesn't miss a genuine physiological event that occurs simultaneously with a sensor fault?

---

## Q2: How would you approach designing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The shared ADC and multiplexer introduces a coupling risk — the settling time of one channel can affect the accuracy of the next channel if the multiplexer switches too quickly. I'd start by defining the accuracy requirements for each parameter independently, then identify the worst-case timing scenario: for example, if the pressure sensor has a high source impedance and the temperature sensor has a large DC offset, the multiplexer might need a longer settling time to avoid crosstalk.

The test plan would have three layers. First, individual channel accuracy testing — verify each sensor's accuracy against a reference standard while the other channel is idle. Second, simultaneous operation testing — run both channels at their normal sampling rates and verify accuracy is maintained. Third, worst-case stress testing — deliberately create conditions that maximize crosstalk, such as driving one sensor to its extreme range while measuring the other at its most sensitive range.

I'd also include a test for multiplexer switching artifacts: verify that the firmware's settling time configuration is adequate by measuring the ADC reading at various points during the settling window. If the firmware uses a fixed settling delay, I'd test across the full temperature range of the device, since settling time can vary with temperature. Finally, I'd verify that the calibration coefficients for each sensor are correctly applied regardless of which channel was sampled previously — this catches bugs where calibration data gets associated with the wrong channel.

**Possible follow-ups:** How would you determine the minimum settling time required for the multiplexer? How would you handle the situation where the two sensors require different ADC gain settings?

---

## Q3: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using an unacknowledged broadcast protocol to simplify the design, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** This is a classic reliability-versus-simplicity trade-off, and the clinical requirement should drive the decision. An unacknowledged broadcast protocol can be acceptable if the design includes mechanisms to detect data loss and indicate staleness — but the firmware engineer's proposal needs to address how the display unit knows the data is stale. Simply broadcasting without any sequence numbers or timestamps would make it impossible to distinguish between "no new data because the patient is stable" and "no new data because the link is down."

I'd propose a middle ground: keep the broadcast protocol for efficiency, but add a sequence number to each packet and have the display unit track the expected sequence. If packets are missed, the display unit can indicate "data gap" or "signal degraded." Additionally, I'd require the transmitter to send a periodic "heartbeat" or status packet even when physiological data hasn't changed, so the display unit can distinguish between a silent but functional link and a failed link. The display unit should also have a timeout — if no packets are received for a defined interval, it should display a "connection lost" alarm rather than showing stale data as if it were current.

The key design input here is the clinical risk: if stale data is displayed without indication, a clinician might make a decision based on outdated information. So the design verification would include testing the staleness indication under various packet loss scenarios — random loss, burst loss, and complete link failure — to confirm the display always indicates the data's freshness status.

**Possible follow-ups:** How would you determine the acceptable timeout duration before the display shows "connection lost"? How would you verify that the staleness indication itself doesn't create alarm fatigue?

---

## Q4: How would you approach developing a design verification test plan for a medical device that must operate correctly during and after exposure to a defibrillation pulse, given that the device is intended for use in a hospital environment where defibrillation may occur?

**Answer:** This is governed by IEC 60601-2-series particular standards for devices that may be subjected to defibrillation — the key requirement is that the device must survive the defibrillation pulse and return to normal operation within a specified recovery time, without presenting a hazard to the patient or operator. I'd start by identifying which particular standard applies to the device type, since the test setup and pass/fail criteria differ.

The test plan would include: (1) verifying that the device's input protection circuitry (e.g., spark gaps, series resistors, clamping diodes) limits the energy that reaches the sensitive electronics; (2) testing the device's behavior during the defibrillation pulse — it should not present a shock hazard or create a path for the defibrillation energy to reach the patient through the device; (3) verifying recovery — after the pulse, the device should resume monitoring within the specified time, and any data recorded during the event should be clearly marked as potentially corrupted.

For the actual test, I'd use a defibrillation pulse generator that produces the standardized waveform (typically 5 kV, with specific energy and timing characteristics) and apply it to the patient connections. I'd test with the device powered on and monitoring, and also with the device in various states (e.g., battery-powered, mains-powered, in alarm condition). The pass criteria would include: no damage to the device, no unsafe leakage current after the pulse, and recovery to normal operation within the specified time.

I'd also include a test where the defibrillation pulse is applied while the device is connected to a patient simulator, to verify that the device doesn't misinterpret the defibrillation pulse as a physiological signal and generate false alarms. This is a common failure mode — the device sees a large transient and triggers an alarm, which could distract clinical staff during a critical moment.

**Possible follow-ups:** How would you verify that the device's recovery time is clinically acceptable? How would you handle the situation where the device's input protection circuitry degrades the normal sensor signal quality?

---

## Q5: You're leading a project where a supplier has delivered a batch of PCBs for a medical device, and incoming inspection reveals that the solder mask on the high-voltage isolation area has minor voids that don't affect the dielectric strength but could allow moisture ingress over time. The supplier claims the boards are acceptable and that the voids are within IPC-A-600 Class 2 limits, but the device is intended for a home environment where it may be exposed to humidity. How would you handle this situation?

**Answer:** This is a risk-based decision that requires balancing the supplier's claim of IPC compliance against the device's intended use environment and the potential long-term failure mode. The key question is whether the solder mask voids create an unacceptable risk of moisture ingress leading to creepage or clearance reduction, which could cause a safety hazard over the device's service life.

I'd start by assessing the actual risk: the voids are in the high-voltage isolation area, so the concern is that moisture could create a conductive path across the isolation barrier. Even if the boards pass hi-pot testing now, the question is whether they would continue to pass after exposure to humidity and thermal cycling over several years. I'd request the supplier's data on the void distribution and size, and I'd also review the IPC-A-600 acceptance criteria to confirm whether the voids truly meet Class 2 limits — sometimes suppliers interpret the standard loosely.

If the risk is genuinely low, I might accept the boards with a documented deviation and add a risk control measure: for example, applying additional conformal coating over the isolation area, or adding a humidity soak test to the design verification plan to confirm the boards maintain dielectric strength under worst-case humidity conditions. However, if the voids are in a critical area where the isolation distance is already marginal, I'd reject the batch and require the supplier to rework or re-fabricate.

The decision should be documented in the risk management file, with the rationale for acceptance or rejection, and the residual risk assessed. I'd also update the supplier's quality agreement to include more stringent solder mask inspection criteria for future batches, since this is a recurring risk that should be controlled at the source rather than detected at incoming inspection.

**Possible follow-ups:** How would you determine whether the voids are acceptable under the device's specific isolation requirements versus the general IPC Class 2 criteria? How would you handle the situation if the supplier refuses to rework the boards and the project schedule is at risk?