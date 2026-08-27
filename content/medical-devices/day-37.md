# medical-devices — Day 37

## Q1: How would you approach verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during a firmware update, given that the device must remain safe and functional if the update fails?

**Answer:** This is fundamentally about designing for update robustness and then verifying that design through fault injection. First, I'd ensure the firmware architecture supports safe updates from the ground up: a bootloader that validates the new image before committing to it, dual-bank or A/B partitioning so a valid previous version remains bootable, and a status flag mechanism that tracks update state across power cycles. The bootloader should verify integrity (checksum or signature) and version compatibility before switching active images.

For verification, I'd build a fault injection test matrix that covers the realistic failure modes: power loss at various points during the write (erase, partial write, full write, metadata update), corrupted image data (bit flips in the payload, truncated image, wrong version), and interruption during the bootloader's validation phase. Each test case verifies three things: the device boots into a known-good state, no patient data is lost or corrupted, and the device either completes the update on retry or falls back to the previous version with an appropriate user notification.

I'd also verify the recovery path — if the device falls back to the old version, does it handle the case where the user attempts the update again? And critically, for a medical device, I'd confirm that the monitoring function remains available throughout — the device shouldn't be "bricked" or in a degraded safety state during or after a failed update. This maps directly to risk control measures identified in the ISO 14971 analysis: update failure is a hazard with potential for device unavailability, and the verification evidence must demonstrate the risk controls are effective.

**Possible follow-ups:** How would you decide between dual-bank and single-bank-with-recovery approaches? What role does the IEC 62304 software configuration management process play in ensuring update integrity?

---

## Q2: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory is full, given that the device must continue monitoring and displaying physiological data in real time?

**Answer:** The key design principle is that data logging must never interfere with the real-time monitoring function — logging is a secondary task that must degrade gracefully. I'd start by reviewing the firmware architecture to confirm that the logging subsystem operates independently from the monitoring path, likely with a dedicated task or interrupt priority that ensures logging failures can't block sensor acquisition or alarm generation.

For the test strategy, I'd create scenarios that fill the non-volatile memory in realistic ways: normal operation until full, rapid logging of high-frequency data, and a combination where the device is logging multiple parameters simultaneously. The critical test assertions are: monitoring continues without interruption (verified by checking that sensor sampling rates and alarm latencies remain within specification), the user is notified that storage is full (per the usability requirements), and no data corruption occurs in the already-stored data.

I'd also test the boundary conditions — what happens when the memory fills mid-write, and what happens when the user clears or offloads data while the device is actively monitoring. The device should handle both gracefully without requiring a reboot or losing buffered data. For a medical device, I'd also verify the behavior is consistent with the risk management file — if data loss is possible when storage is full, that risk must be documented, mitigated (e.g., overwrite oldest data with a flag, or stop logging but continue monitoring), and communicated to the user through the alarm or notification system.

**Possible follow-ups:** How would you decide between overwriting oldest data versus stopping logging when storage is full? How would you verify that the notification to the user is effective under IEC 60601-1-6 usability requirements?

---

## Q3: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using a proprietary protocol with a simple checksum, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** The clinical requirement here is non-negotiable — if the display unit can't detect data loss or indicate staleness, clinicians may act on outdated information, which is a patient safety issue. The question is how to meet that requirement with appropriate engineering rigor rather than over-engineering the solution.

I'd start by clarifying the clinical requirements precisely: what does "data loss detectable" mean in practice? Is it sufficient to detect that a packet was lost, or does the system need to recover the data? What staleness threshold triggers an alert — 1 second, 5 seconds, 30 seconds? These answers drive the protocol design.

A simple checksum alone is insufficient because it only detects corruption, not loss. At minimum, the protocol needs sequence numbers to detect missing packets and a timestamp or heartbeat mechanism to detect staleness. The question is whether to use a standard protocol (like Bluetooth with its built-in sequence numbering and connection supervision timeout) or a proprietary protocol with these features added. I'd lean toward a standard protocol if it meets the requirements, because it's better documented, has existing test tools, and is easier to verify. If a proprietary protocol is necessary (e.g., for latency or power constraints), I'd require it to include: sequence numbers, a timestamp field, a heartbeat or periodic status message, and a defined behavior when the display unit detects a gap or timeout.

For verification, I'd design tests that inject packet loss, delay, and reordering at the RF level (using a test fixture that can attenuate or block signals) and verify the display unit correctly indicates staleness within the required time. I'd also test the recovery path — when the link re-establishes, does the display unit correctly resume displaying current data and clear the stale indicator? This is a risk control measure under ISO 14971, so the verification evidence must be documented in the risk management file.

**Possible follow-ups:** How would you determine the acceptable staleness threshold from a clinical perspective? What testing would you do to verify the display unit's stale data indicator is effective in a real clinical environment?

---

## Q4: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The shared ADC and multiplexer introduces a coupling risk — the measurement of one parameter could be affected by the other, either through multiplexer crosstalk, settling time issues, or reference voltage loading. The test plan needs to specifically address this coupling, not just verify each channel independently.

I'd structure the plan in layers. First, verify each channel independently against a known reference — temperature against a calibrated thermometer, pressure against a calibrated manometer — across the full operating range and temperature range. This establishes baseline accuracy for each channel.

Second, verify simultaneous operation: both sensors active, measuring at their full update rate, with the ADC multiplexing between them. The key test is to hold one parameter at a fixed value while sweeping the other across its range, and verify the fixed parameter's reading doesn't shift beyond its accuracy specification. For example, hold pressure constant while sweeping temperature, and verify the pressure reading stays within spec — this catches multiplexer settling issues, crosstalk, or thermal coupling through the PCB.

Third, I'd test the dynamic case — both parameters changing simultaneously at their maximum rates — to verify the ADC can keep up without dropping samples or introducing latency that affects accuracy. I'd also include tests for the multiplexer switching behavior: verify that the settling time is adequate for the ADC's resolution, and that adjacent channel leakage is within the ADC's specifications.

Finally, I'd verify the calibration approach — if the two channels share a reference, a drift in that reference affects both, so the test plan should include a reference accuracy check over time and temperature. The test results need to demonstrate that the combined error budget (sensor, ADC, multiplexer, reference, firmware processing) meets the overall system accuracy requirement for each parameter.

**Possible follow-ups:** How would you determine whether any observed cross-channel error is acceptable or requires a design change? How would you handle the case where the two sensors have different optimal ADC sampling rates?

---

## Q5: You're leading a project where a field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that requires immediate attention because it involves patient safety and potential biological compatibility issues. I'd approach it as a structured investigation following the principles of a formal corrective action process, while also addressing the immediate patient safety concerns.

First, I'd ensure the immediate risk is assessed — are the reported cases isolated or widespread? Is the irritation mild or severe? Do we need to consider a field safety notice or recall? This requires coordination with the quality and regulatory teams to determine the severity classification and any reporting obligations.

For the investigation itself, I'd use a root cause analysis framework, likely 8D or similar. The investigation would branch into several parallel tracks. First, characterize the complaint: how many patients affected, what severity, what common factors (device lot, manufacturing date, usage duration, patient skin type)? Second, examine the material: was the silicone formulation changed? Was there a supplier change or process variation? Third, review the biocompatibility evidence: what ISO 10993 testing was done originally, and does the current material match what was tested? Fourth, consider usage factors: could the irritation be caused by something other than the material itself — adhesive residue, cleaning agents, moisture trapped under the pad?

I'd also consider whether this is a design issue versus a manufacturing issue. If the material is unchanged and the biocompatibility testing was adequate, the cause might be in manufacturing (e.g., a mold release agent residue, incomplete curing) or in the clinical use environment. If the material was changed, the corrective action might involve reverting to the original formulation or conducting additional biocompatibility testing.

The corrective action would depend on the root cause, but would likely include: material or process changes, updated incoming inspection or process controls, revised biocompatibility testing (possibly including more sensitive test methods), and updated labeling or instructions for use if the issue is related to usage. Throughout, I'd document everything in the complaint handling and corrective action system, and ensure the investigation findings feed back into the risk management file — this is a hazard that wasn't adequately anticipated, so the risk assessment needs updating.

**Possible follow-ups:** How would you determine whether this complaint requires reporting to regulatory authorities as a field safety corrective action? How would you balance the speed of the investigation with the need for thoroughness when patients are potentially affected?