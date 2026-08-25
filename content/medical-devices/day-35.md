# medical-devices — Day 35

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during a firmware update, given that the device must remain safe and functional if the update fails?

**Answer:** I'd approach this from a layered strategy that combines fault injection testing, power-loss testing, and verification of the recovery mechanism itself.

First, I'd want to understand the firmware update architecture — specifically, whether there's a bootloader with rollback capability, dual-bank flash, or a recovery partition. The test strategy depends heavily on this architecture. For a medical device, the key safety requirement is that a failed update must never leave the device in a state where it can't deliver its safety-critical function, or if it can't, it must fail into a known safe state.

The test plan would include several categories:

**Fault injection during update:** I'd inject errors at various points in the update process — corrupted image headers, bit flips in the payload, CRC mismatches, truncated transfers, and invalid signatures. The device should detect each of these and either retry, revert to the previous known-good image, or enter a recovery mode — but never become bricked.

**Power-loss testing:** This is critical for battery-powered or mains-powered devices where a user could disconnect power mid-update. I'd test power removal at every stage of the update — during erase, during write, during verification, and during the bootloader's handoff to the new image. The device must recover gracefully on next power-up.

**Verification of the rollback mechanism:** If the device has dual-bank flash, I'd verify that the bootloader correctly selects the known-good image when the new image fails validation. This includes testing the bootloader's own integrity — if the bootloader itself is corrupted, is there a recovery path?

**Post-update functional verification:** After a successful update, the device should run a self-test to confirm the new firmware is functional, not just that the flash contents match. This might include checking that critical peripherals initialize correctly and that the device can enter its normal operating mode.

I'd also want to verify that the update process itself is safe — for example, if the device is monitoring a patient during an update, does it continue monitoring until the actual reset occurs? Is there a timeout that returns to the old firmware if the new one fails to boot?

The test results would feed into the risk management file, since failed updates are a foreseeable hazard that needs a risk control measure with verified effectiveness.

**Possible follow-ups:**
- How would you determine whether a dual-bank flash architecture or a single-bank with external recovery is more appropriate for a given device?
- How would you test the scenario where the device loses power during the bootloader's flash erase operation, which is typically the most vulnerable window?

---

## Q2: During a design review for a medical device that uses a rechargeable battery, the firmware engineer proposes implementing a battery fuel gauge using voltage-based estimation with periodic open-circuit voltage (OCV) correction, while the hardware engineer recommends adding a dedicated coulomb-counting fuel gauge IC. The device must provide accurate remaining capacity information to clinicians, and the battery is not user-replaceable. How would you approach this trade-off?

**Answer:** This is a classic trade-off between cost/complexity and accuracy, and in a medical device, the accuracy requirement is driven by the clinical use case — specifically, what decisions clinicians will make based on the remaining capacity information.

First, I'd clarify the actual requirement. Is the fuel gauge providing a rough "low battery" warning, or is it providing a percentage that clinicians use to decide whether to connect the patient to mains power or move them to another device? The accuracy requirement should be derived from the clinical risk assessment, not from what's convenient to implement.

For voltage-based estimation with OCV correction: this approach is simpler and cheaper, but it has well-known limitations. The battery's voltage under load varies with temperature, load current, and battery age. The OCV correction only works when the battery is at rest — which may be rare in a continuously monitoring device. For a device that's always drawing current, the OCV correction may never actually occur, leaving the gauge to rely on loaded voltage measurements that can be misleading, especially with flat discharge curves common in Li-ion chemistries.

For a coulomb-counting IC: this gives much better accuracy during dynamic load conditions because it integrates current over time. However, it requires accurate initial conditions and periodic recalibration, because coulomb counting drifts over time due to measurement offset errors. The IC also adds cost and board space, and it needs careful selection of the sense resistor and calibration.

My approach would be to look at the actual discharge profile of the specific battery under the device's expected load patterns. If the device has a relatively constant load, voltage-based estimation with temperature compensation might be adequate. If the load varies significantly — which is common in devices with wireless transmission, motors, or high-power sensors — coulomb counting is likely necessary.

I'd also consider the battery's aging behavior. A fuel gauge that's accurate for a new battery but becomes unreliable after 200 charge cycles is a safety concern for a device with a non-user-replaceable battery. Coulomb-counting ICs typically have better aging compensation, especially those that track battery impedance.

In practice, I'd likely recommend a hybrid approach: a coulomb-counting IC with voltage-based correction when the device enters a low-power or rest state. This gives the accuracy needed for dynamic loads while providing periodic recalibration. But the decision should be driven by the clinical requirements and the risk assessment — if the consequence of an inaccurate gauge is a device that dies mid-monitoring without warning, the added cost of the dedicated IC is justified.

**Possible follow-ups:**
- How would you verify the accuracy of the fuel gauge over the battery's full service life, given that accelerated aging tests don't perfectly replicate real-world usage patterns?
- What information would you want from the battery manufacturer to make this decision?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The key challenge here is that sharing an ADC and multiplexer introduces potential cross-channel interference and timing-dependent errors that wouldn't exist with independent signal chains. The test plan needs to verify not just that each channel meets its accuracy spec in isolation, but that both channels meet their specs when operating together under realistic conditions.

I'd structure the test plan around several layers:

**Channel isolation testing:** The multiplexer should provide adequate isolation between channels, but I'd verify this by driving one channel to its full-scale extreme while measuring the other channel's output. For example, if the pressure sensor is at maximum pressure while the temperature sensor is at minimum temperature, does the temperature reading shift? This tests for crosstalk through the multiplexer's on-resistance, leakage currents, or charge injection.

**Settling time verification:** When the multiplexer switches between channels, the ADC needs adequate settling time before sampling. I'd test with worst-case source impedances and worst-case signal differences between channels — for example, switching from a high-voltage channel to a low-voltage channel and verifying the ADC reading is accurate within the specified settling time. This is particularly important if the firmware is controlling the multiplexer timing.

**Simultaneous accuracy testing:** I'd set up a test where both sensors are exposed to known reference conditions simultaneously — for example, a temperature-controlled chamber with a calibrated pressure source. The device should read both parameters within spec while both are changing, not just at steady state. This catches issues where the multiplexer switching rate or ADC sampling rate creates aliasing or missed samples.

**Timing and synchronization testing:** If the device uses the measurements for time-critical functions — like calculating a derived parameter from both temperature and pressure — I'd verify that the samples are properly time-aligned. If the pressure reading is taken 10 ms before the temperature reading, does that introduce unacceptable error in the derived value?

**Cross-channel fault testing:** I'd also test fault conditions — what happens if one sensor fails or shorts? Does it affect the other channel's readings? The multiplexer should isolate faults, but I'd verify this explicitly.

I'd also want to review the firmware's sampling sequence. If the firmware alternates between channels, is there a deterministic pattern that allows the settling time to be calculated? Or does the firmware use a priority-based scheme where one channel could starve the other? The test plan should include scenarios that stress the firmware's scheduling.

Finally, I'd include long-duration testing to catch drift or intermittent issues — running the device for extended periods with both sensors active and periodically checking accuracy against references.

**Possible follow-ups:**
- How would you determine the acceptable settling time for the multiplexer, and how would you verify that the firmware provides enough time?
- What would you do if the test revealed that the two channels meet their individual accuracy specs but fail when both are active simultaneously?

---

## Q4: How would you approach verifying that a medical device's wireless communication module meets both the IEC 60601-1-2 immunity requirements and the radio spectrum regulatory requirements (e.g., FCC, ISED) for the markets where it will be sold?

**Answer:** This requires a coordinated approach because the two sets of requirements are tested differently and sometimes have conflicting implications for the design.

First, I'd map out the applicable requirements. IEC 60601-1-2 has immunity requirements that apply to the device as a whole, including the wireless module — the device must maintain basic safety and essential performance when exposed to radiated RF fields, ESD, and other electromagnetic phenomena. The radio spectrum regulations (FCC Part 15 in the US, ISED RSS in Canada, and equivalent regulations in other markets) govern the intentional emissions from the wireless module — its frequency, power, bandwidth, and spurious emissions.

The key distinction is that IEC 60601-1-2 immunity testing is about how the device responds to external electromagnetic energy, while radio spectrum testing is about what the device itself emits. They're tested separately but the results are interrelated — for example, a wireless module that's susceptible to interference might fail immunity testing, while a module with poor filtering might emit spurious signals that fail radio spectrum testing.

For the immunity side, I'd ensure the wireless module is included in the device-level IEC 60601-1-2 testing. This means the device is tested with the wireless module operating — typically in its normal mode — while exposed to the required immunity levels. The critical question is whether the device maintains essential performance during wireless transmission. For example, if the device transmits patient data while exposed to a 10 V/m radiated field, does the transmission remain reliable, or does the module's receiver desensitize and lose data?

For the radio spectrum side, I'd work with a test lab that can perform the required measurements — conducted and radiated emissions, frequency stability, occupied bandwidth, and spurious emissions. The module itself may already be certified (e.g., modular approval), which simplifies things, but I'd still need to verify that the integration into the device doesn't degrade the module's performance — for example, the device's antenna placement or PCB layout could affect the module's emissions.

I'd also consider coexistence testing. In a hospital environment, the device will operate alongside other wireless devices — Wi-Fi, Bluetooth, other medical telemetry. IEC 60601-1-2 doesn't explicitly require coexistence testing, but it's good practice to verify that the device's wireless link remains reliable in the presence of other signals in the same frequency band.

One practical approach is to do pre-compliance testing early in the design cycle — using a spectrum analyzer to check the module's emissions in the device, and using a nearby transmitter to check the device's immunity while the wireless link is active. This catches issues before the formal testing, which is expensive and time-consuming.

Finally, I'd document all of this in the design history file — the test plans, results, and any design changes made to address failures. The regulatory submission will need evidence that both sets of requirements are met.

**Possible follow-ups:**
- How would you handle a situation where the wireless module passes its standalone certification but fails when integrated into the device?
- What specific aspects of the device's design would you review to ensure the wireless module's antenna performance isn't degraded by the device's enclosure or PCB layout?

---

## Q5: You're leading a project where a field complaint reports that a medical device's patient-contacting temperature probe is reading approximately 2°C higher than a reference thermometer used by clinical staff, but the device passes its calibration check when returned to the manufacturer. How would you approach the investigation and corrective action process?

**Answer:** This is a classic "it works in the lab but not in the field" scenario, and it requires a systematic investigation that considers the entire measurement chain — not just the device's internal calibration.

First, I'd want to understand the clinical context of the complaint. How was the reference thermometer used? Was it the same type of thermometer, or a different technology? Was it measuring the same anatomical site? In temperature measurement, the measurement site matters enormously — a skin probe will read differently from an oral or rectal thermometer, and even two skin probes at slightly different locations can read differently. The first question is whether this is a device malfunction or a measurement methodology discrepancy.

Second, I'd examine the device's calibration procedure. If the device passes its calibration check at the manufacturer, that tells me the sensor and signal chain are within spec under the manufacturer's calibration conditions. But the calibration check might use a different reference method than the clinical use — for example, a dry block calibrator versus actual patient contact. The discrepancy might be in how the device is calibrated versus how it's used.

Third, I'd look at the device's usage conditions. Is the probe being used with a cover or sheath that could insulate it? Is it being applied with sufficient pressure for good thermal contact? Is the device being used in an environment with different ambient temperature than the calibration conditions? Any of these could cause a consistent offset.

Fourth, I'd consider the possibility of a systematic error that the calibration check doesn't catch. For example, if the device's firmware applies a correction factor based on ambient temperature, and the ambient temperature sensor is inaccurate, the correction could be wrong in the field but appear correct in the lab if the lab temperature is different.

I'd also want to look at the device's history — is this an isolated complaint or part of a pattern? Are other devices showing similar discrepancies? Is there a batch-specific issue with the sensor or the calibration process?

The investigation would follow a structured approach:

1. **Gather data:** Collect the complaint details, the device's usage history, and any logged data from the device.
2. **Reproduce the issue:** Try to reproduce the discrepancy under controlled conditions that mimic the field usage — different ambient temperatures, different probe covers, different application methods.
3. **Analyze the measurement chain:** Review the sensor's characteristics, the signal conditioning, the ADC, and the firmware's calibration and correction algorithms.
4. **Compare with the reference:** Understand exactly how the clinical staff's reference thermometer works and whether it's traceable to a standard.
5. **Determine root cause:** Based on the evidence, determine whether this is a device defect, a usage issue, a calibration methodology issue, or a measurement methodology discrepancy.

If it turns out to be a device issue, I'd follow the corrective action process — which might involve a design change, a calibration procedure change, or a field action depending on the severity. If it's a usage issue, the corrective action might be updated instructions or training. If it's a measurement methodology discrepancy, the resolution might be to clarify the device's intended use and limitations.

Throughout this, I'd be documenting everything for the post-market surveillance file and considering whether the issue needs to be reported to regulatory authorities based on the risk assessment.

**Possible follow-ups:**
- How would you determine whether this complaint requires a field safety corrective action (FSCA) or can be resolved with a labeling change?
- What data would you want to collect from the field before deciding on a corrective action?