# medical-devices — Day 14

## Q1: How would you approach designing a battery charging circuit for a medical device where the battery must remain in-circuit while the device is connected to mains power and actively monitoring a patient?

**Answer:** The key constraint here is that the device must continue operating safely during charging, which means the charging circuit cannot introduce noise into the patient-monitoring analog front-end, and the power path must be designed so that a charger fault cannot compromise patient safety. I would start by defining the power architecture: a linear charger for lower noise but higher thermal dissipation, versus a switching charger for efficiency but with the added complexity of filtering. For a medical device, I'd likely lean toward a switching charger with careful layout and filtering, since the efficiency matters for thermal management inside a sealed enclosure, but I'd isolate the switching node and inductor away from the sensitive analog section, possibly with a shield or ground guard.

The critical design decision is the power path topology. A diode-OR configuration is simple but wastes power and creates a voltage drop. A FET-based ideal diode or a dedicated power-path IC is better, but I need to verify the transition behavior — when mains is disconnected, there must be no glitch or dropout that could reset the microcontroller or interrupt monitoring. I'd specify a power-path controller with break-before-make switching and sufficient hold-up capacitance to ride through the transition.

For safety, I'd consider what happens if the charger fails short or the battery is removed while on mains. The device should still operate from mains power, and the patient-connected circuits must maintain their isolation and leakage current limits. I'd also include battery temperature monitoring (NTC) for charge termination, and I'd verify that the charging current doesn't cause the battery temperature to rise to a level that could affect adjacent patient-contacting components. Finally, I'd review the charging profile against the battery manufacturer's specifications and implement appropriate charge termination — typically CC-CV with a termination current threshold — and I'd ensure that the firmware can detect and report charger faults.

**Possible follow-ups:**
- How would you verify that the charging circuit doesn't introduce noise into the patient monitoring function?
- What failure modes would you consider for the power path during the transition between mains and battery operation?

---

## Q2: During a design review for a medical device that uses a motor for an infusion pump, the firmware engineer proposes using a brushless DC motor with sensorless control, while the hardware engineer recommends a brushed DC motor with an encoder. How would you approach this trade-off?

**Answer:** This is a classic reliability-versus-complexity trade-off that needs to be grounded in the specific clinical requirements. I'd start by asking what the motor actually needs to do: what accuracy is required for the delivery rate, what is the operating duty cycle, what is the expected lifetime in cycles, and what happens on a motor fault? For an infusion pump, delivery accuracy is safety-critical, so the motor control scheme must provide deterministic, verifiable performance.

A brushed DC motor with an encoder is simpler to control, easier to characterize, and the encoder provides direct feedback that can be used for occlusion detection and delivery verification. The downsides are brush wear over time, which limits lifetime, and the potential for brush arcing to generate EMI. A sensorless BLDC motor eliminates brush wear and can be more efficient, but sensorless control relies on back-EMF sensing, which is challenging at low speeds and under varying load — exactly the conditions an infusion pump might encounter during occlusion or at low flow rates. The startup behavior of sensorless BLDC is also a concern; if the motor stalls or fails to start, the firmware needs to detect this reliably.

I would approach this by defining the requirements first: delivery accuracy over the full flow-rate range, occlusion detection response time, and expected device lifetime. If the clinical requirements demand high accuracy at very low flow rates, the sensorless approach becomes risky. If the device has a short service life and the flow rates are moderate, sensorless BLDC could be acceptable. I'd also consider a middle ground: a BLDC motor with a Hall sensor or a low-resolution encoder, which gives the reliability benefits of BLDC without the startup and low-speed challenges of sensorless control.

For a medical device, I'd also think about the failure modes. A brushed motor failure tends to be gradual (brush wear), which can be monitored. A sensorless BLDC failure might be sudden and harder to diagnose. I'd want to see a fault tree or FMEA comparing the two approaches before making a decision.

**Possible follow-ups:**
- How would you verify that the motor control algorithm meets the delivery accuracy requirements across the full operating range?
- What additional risk controls would you consider for the motor system regardless of which approach is chosen?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must operate correctly across a wide temperature range, when the device uses both analog sensors and digital communication?

**Answer:** I'd start by defining the operating temperature range from the requirements — this might come from the intended environment (home vs. hospital), the IEC 60601-1 requirements for normal and single-fault conditions, and the storage/transport conditions. The test plan needs to cover three aspects: performance verification (does the device meet its accuracy specifications across temperature?), safety verification (do leakage currents and other safety parameters remain within limits?), and reliability (does the device survive thermal cycling without degradation?).

For the analog sensors, I'd characterize the temperature sensitivity of the sensor itself, the signal conditioning circuitry, and the ADC reference. The key question is whether the device has any temperature compensation in firmware or hardware. If not, the test plan needs to establish the baseline drift and verify it's within the accuracy budget. I'd design a test matrix that sweeps temperature in controlled steps — for example, 5°C increments from the minimum to maximum operating temperature — with sufficient soak time at each step to ensure thermal equilibrium. At each temperature, I'd verify the sensor readings against a reference standard and record the error.

For the digital communication, temperature can affect timing margins, especially for high-speed interfaces. I'd verify that communication remains reliable across the temperature range, including at the extremes where timing margins are tightest. This might involve running a continuous communication test with error checking while the device is at temperature.

I'd also include thermal cycling tests to catch intermittent failures — solder joint cracks, connector issues, or component drift that only appears after thermal stress. The cycling profile should reflect the expected use pattern: for a home-use device, this might be daily temperature swings; for a device that's transported, it might include more extreme transitions.

Finally, I'd consider the test equipment itself. The temperature chamber needs to be large enough for the device and any test fixtures, and I need to ensure that the measurement equipment either operates at temperature or that I can route signals out of the chamber without affecting the measurements. I'd also document the test setup carefully so that the verification results are reproducible and traceable.

**Possible follow-ups:**
- How would you determine the appropriate soak time at each temperature step?
- What would you do if the device meets its accuracy specification at room temperature but fails at the temperature extremes?

---

## Q4: How would you approach verifying that a medical device's firmware correctly handles a watchdog timer reset, given that the device logs physiological data that must not be corrupted or lost?

**Answer:** The core concern is data integrity across a reset event — the device must not lose data that was already acquired, and it must not write corrupted data during the reset sequence. I'd start by reviewing the firmware architecture to understand how data is buffered and written to non-volatile storage. The key questions are: how much data can be buffered in RAM, how frequently is data written to flash or other non-volatile storage, and what happens to the buffer when a reset occurs?

The design should use a write-ahead logging approach or a double-buffer scheme where data is written to non-volatile storage in a way that is atomic — either the entire record is written or none of it is. I'd verify that the firmware handles the case where a reset occurs mid-write, and that the recovery process on startup can detect and discard partial records without corrupting the rest of the log.

For testing, I'd design a fault injection approach where I trigger watchdog resets at various points in the data acquisition and logging cycle. This could be done by intentionally causing a watchdog timeout through a test hook in the firmware, or by using a debugger to halt the CPU and force a reset. I'd run the device in a continuous monitoring mode with known test data, trigger resets at random intervals, and then verify after each reset that the logged data is complete and uncorrupted.

I'd also test the edge cases: a reset during the initialization of the storage subsystem, a reset when the storage is nearly full, and a reset during a garbage collection or wear-leveling operation if the device uses flash with such features. The recovery process on startup should be verified — does the device resume logging automatically, and does it handle the case where the storage is in an inconsistent state?

Finally, I'd verify the timing: how long does it take for the device to restart and resume monitoring after a watchdog reset? This is critical for a patient monitoring device, where a prolonged gap in monitoring could be clinically significant. The device should either resume monitoring quickly or alert the user that monitoring was interrupted.

**Possible follow-ups:**
- How would you verify that the watchdog timer itself is configured correctly and will actually fire when the firmware hangs?
- What would you do if the recovery process on startup takes longer than the clinically acceptable gap in monitoring?

---

## Q5: You're leading a project where a supplier delivers a batch of PCBs for a medical device, and incoming inspection reveals that the solder mask thickness on the high-voltage isolation area is below the specification. The supplier claims it's within manufacturing tolerance and the boards will pass hi-pot testing. How would you handle this situation?

**Answer:** This is a situation where I need to balance technical risk, regulatory requirements, and the supplier relationship, but the decision must be driven by patient safety and compliance. Solder mask thickness in the isolation area is not just a manufacturing preference — it's a design parameter that contributes to the creepage and clearance protection provided by the PCB. If the solder mask is thinner than specified, the effective insulation between the high-voltage and patient-connected circuits could be compromised, even if the boards pass hi-pot testing at the moment of test.

I would not accept the supplier's claim at face value. The first step is to understand the specification: was the solder mask thickness a design requirement that was communicated to the supplier, or was it an internal design assumption that was never formally specified? If it wasn't in the procurement specification, the supplier may not have been obligated to meet it, and the issue is a gap in our design transfer documentation. If it was specified, then the supplier has a non-conformance that needs to be addressed through the corrective action process.

Regardless of the contractual situation, I would assess the technical risk. The solder mask contributes to the isolation between circuits, but the primary isolation is provided by the physical distance (creepage and clearance) and the PCB substrate material. I'd review the design to understand how much margin exists: if the creepage distance is well above the required minimum, the solder mask may be a secondary protection, and the reduced thickness might be acceptable. If the design relies on the solder mask as part of the isolation system, then the reduced thickness is a safety issue.

I would also consider the long-term reliability. Solder mask that is thinner than specified may be more susceptible to damage during handling, assembly, or in the field, which could reduce the isolation protection over time. Even if the boards pass hi-pot testing now, they might not meet the requirements after thermal cycling, vibration, or contamination.

My approach would be to: (1) quarantine the affected batch, (2) review the design documentation to understand the solder mask requirement and its role in safety, (3) perform additional testing on the affected boards — including hi-pot testing, but also thermal cycling and possibly a more detailed inspection of the isolation area — and (4) engage with the supplier to understand the root cause of the variation. If the risk assessment shows that the boards are safe and compliant, I might accept the batch with a documented deviation and a corrective action plan from the supplier. If there's any doubt about safety or compliance, I would reject the batch and work with the supplier to correct the process.

The key principle is that the decision must be documented, risk-based, and traceable. I would involve the quality team and ensure that the decision is recorded in the design history file, with the rationale clearly stated.

**Possible follow-ups:**
- How would you determine whether the solder mask thickness is actually critical to the safety of the device, or whether it's a cosmetic issue?
- What additional testing would you require before accepting the batch, and how would you document the decision?