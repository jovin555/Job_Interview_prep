# medical-devices — Day 40

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during a firmware update, given that the device must remain safe and functional if the update fails?

**Answer:** The core requirement here is that a failed or interrupted firmware update must never leave the device in a state where it cannot deliver its safety-critical function. I'd start by designing the firmware architecture to support this from the ground up, using a dual-bank or A/B partition scheme where the currently running firmware image remains intact and bootable while the new image is written to the alternate bank. The bootloader would be the first line of defense — it needs to validate the new image's integrity (checksum, signature, version compatibility) before committing to it, and it must have a fallback mechanism to boot the previous known-good image if validation fails or if the new image fails to start within a timeout period.

For the test strategy, I'd structure it around fault injection at multiple levels. First, I'd test the update process itself under normal conditions to establish a baseline. Then I'd inject faults: power loss at various points during the write (beginning, middle, end of each sector write), corrupted data in the transfer stream, wrong image version, image with invalid signature, and partial writes to the metadata that tracks which bank is active. Each test would verify that the device either completes the update successfully or rolls back to the previous image and continues normal operation.

I'd also test the scenario where the update appears to succeed but the new firmware is actually defective — for example, it boots but crashes shortly after. The bootloader should detect repeated boot failures and automatically revert. This requires a boot counter or watchdog-based mechanism that increments on each boot attempt and triggers rollback after a threshold.

Finally, I'd verify that the device's safety-critical monitoring functions remain operational throughout the update process. In a medical device, you can't just stop monitoring while the update installs — so the test plan would need to confirm that the update process itself doesn't interfere with real-time monitoring, or that the device enters a defined safe state with appropriate alarms if monitoring must be interrupted.

**Possible follow-ups:**
- How would you verify that the rollback mechanism itself doesn't introduce new failure modes?
- What happens if the device loses power during the bootloader's rollback operation — how would you test for that?

---

## Q2: You're leading a project where a supplier has delivered a batch of PCBs for a medical device, and incoming inspection reveals that the via fill material on a critical high-voltage isolation area is not fully cured. The supplier claims the boards will pass hi-pot testing and that the issue is cosmetic. How would you handle this situation?

**Answer:** This is fundamentally a risk management decision, not just a quality inspection call. The supplier's claim that the boards will pass hi-pot testing addresses only one aspect of the risk — the immediate dielectric strength. But the concern with uncured via fill material is that it may not be a static condition. The material could continue to cure or degrade over time, potentially changing its dielectric properties, absorbing moisture, or allowing conductive migration in the presence of humidity and voltage stress. In a medical device, you have to consider the entire service life, not just the as-shipped condition.

My first step would be to formally document the non-conformance and quarantine the affected lot so no boards enter production. Then I'd want to understand the scope of the issue — is this a process deviation on one batch, or does it indicate a systemic problem with the supplier's manufacturing process? I'd request the supplier's process records, including cure profiles, material lot traceability, and any in-process inspection data.

I would not accept the supplier's "cosmetic" characterization without independent verification. I'd want to understand what testing would provide confidence: accelerated aging or humidity exposure testing on sample boards, cross-sectioning to assess the actual cure state, and possibly extended hi-pot testing under elevated humidity conditions. The key question is whether the uncured material creates a latent failure mode that could manifest months or years later.

I'd also consider the regulatory context. The design history file and risk management file should document the rationale for the acceptance decision. If we accept the boards based on engineering judgment, that decision needs to be traceable and defensible. If there's any reasonable doubt about long-term reliability, the conservative path is to reject the lot and require the supplier to correct their process. The cost of a field failure in a medical device — both in patient risk and regulatory impact — far outweighs the cost of scrapping a batch of PCBs.

**Possible follow-ups:**
- What specific tests or analyses would you request from the supplier to support their claim?
- How would you document this decision in the risk management file?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The key challenge here is that sharing an ADC and multiplexer introduces coupling mechanisms that can affect both measurements — you're not testing two independent channels, you're testing an integrated acquisition system. I'd start by clearly defining the accuracy requirements for each parameter and understanding the error budget: what portion of the total error is allocated to the sensor itself, the analog front-end, the ADC quantization, and the multiplexer switching.

The test plan needs to address both static and dynamic accuracy. For static accuracy, I'd test each channel individually against known references — a calibrated temperature source and a calibrated pressure source — to verify that each meets its specified accuracy when the other channel is idle. But the more interesting tests are the interaction tests. I'd want to verify that switching between channels doesn't introduce settling errors — for example, if the pressure sensor has a higher output impedance than the temperature sensor, the ADC input might not fully settle within the allocated acquisition time after switching. This could be tested by measuring both channels at various switching rates and comparing against the single-channel baseline.

I'd also test for crosstalk: does a large signal on one channel affect the other? For example, if the pressure sensor outputs a large voltage swing, does it couple into the temperature measurement through the multiplexer's off-channel leakage or through shared reference or power supply paths? This could be tested by holding one channel at an extreme value while sweeping the other and checking for correlated errors.

Another important consideration is timing. If the device must display both parameters simultaneously, the test plan should verify that the acquisition sequence — the order and timing of channel sampling — doesn't introduce unacceptable latency or skew between the two measurements. For physiological monitoring, this could matter if the two parameters are used together in an algorithm (for example, calculating a derived value from both).

Finally, I'd include environmental testing — temperature and humidity variation — since the shared analog path may have different temperature coefficients for each channel. The test plan should verify accuracy across the full operating temperature range, not just at room temperature.

**Possible follow-ups:**
- How would you determine whether to test the two channels simultaneously or sequentially?
- What would you do if the interaction testing reveals that the multiplexer settling time is causing errors on one channel?

---

## Q4: How would you approach verifying that a medical device's firmware meets IEC 62304 requirements for a Class C software safety classification?

**Answer:** Class C is the highest software safety classification under IEC 62304 — it applies when a software failure could contribute to a hazardous situation that could result in death or serious injury. The verification approach has to be commensurate with that risk level, and it's really about demonstrating rigor and traceability throughout the entire software development lifecycle, not just at the testing stage.

I'd start by confirming that the classification is correct and documented, with a clear rationale linking the software's role to the hazard analysis. The classification drives everything downstream — the required development activities, documentation, and verification depth.

For verification specifically, I'd structure the approach around the traceability chain: software requirements → software architecture → detailed design → code → tests. Every safety-related requirement must be traceable to design elements and to verification activities. The test plan would include unit testing with coverage analysis (statement, branch, and MC/DC coverage for safety-critical modules), integration testing to verify interfaces between modules, and system-level testing against the software requirements.

For a Class C device, the testing needs to be more rigorous than just functional testing. I'd include static analysis to detect coding defects, and I'd expect the team to use defensive programming practices — checking all return values, validating inputs, handling edge cases explicitly. The test plan should also include negative testing: what happens when inputs are out of range, when timing constraints are violated, when resources are exhausted?

I'd also emphasize the importance of the software architecture in making the system verifiable. If safety-critical functions are isolated from non-critical functions, you can apply more rigorous verification to the critical subset without the same burden on the entire codebase. This is a design decision that makes verification feasible.

Finally, the verification activities need to be documented with objective evidence — test procedures, results, defect tracking, and resolution records. For Class C, there's an expectation that the software is essentially proven to meet its requirements through a combination of analysis and testing, and the documentation needs to demonstrate that to a regulatory auditor.

**Possible follow-ups:**
- How would you determine the appropriate level of code coverage for a Class C device?
- What role does the software architecture play in making a Class C device verifiable?

---

## Q5: You're leading a project where a field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that requires immediate attention because it involves patient safety and potential biological incompatibility. My first priority would be to assess the severity and scope — how many patients are affected, what's the nature and severity of the irritation, and whether there's a pattern that suggests a root cause. I'd want to determine if this is an isolated issue with a specific lot or a systemic problem with the design or material.

The immediate actions would be to quarantine any remaining inventory of the affected lot, notify the appropriate internal stakeholders (quality, regulatory, clinical affairs), and ensure that the complaint handling process is activated per the company's procedures. If the irritation is severe or widespread, this could escalate to a field safety corrective action, so I'd want to gather information quickly to inform that decision.

For the investigation itself, I'd approach it from multiple angles. First, I'd examine the material — the silicone formulation, the manufacturing process, and any changes that might have occurred. This includes reviewing the material's biocompatibility testing per ISO 10993 — was the material tested for skin sensitization and irritation? Were the test methods appropriate for the intended contact duration and body site? I'd also check if there were any process changes at the supplier, any batch-to-batch variation in material composition, or any evidence of contamination or improper curing.

Second, I'd look at the clinical use conditions. Is the irritation related to how the device is used — for example, prolonged contact, interaction with cleaning agents, or occlusion of the skin? Could the issue be with a specific patient population or skin type? I'd want to understand if the affected patients share any common characteristics.

Third, I'd consider whether this is a design issue that could affect all devices, not just a specific lot. If the material selection or the design of the sensor pad is inherently problematic, then even a clean lot could produce the same issue. This would require a design change, not just a manufacturing correction.

The corrective action process would follow a structured root cause investigation — something like an 8D or CAPA process. The key is to identify the actual root cause through evidence, not just correlation, and then implement corrective actions that address that root cause. The corrective action might be a material change, a process change, a design change, or a combination. Whatever the action, it needs to be verified and validated before implementation, and the risk management file needs to be updated to reflect the new hazard and the risk control measures.

Throughout this process, communication is critical — with the affected patients and clinicians, with regulatory authorities if required, and internally with the team. The investigation needs to be thorough and documented, because this type of complaint will likely be scrutinized by regulators.

**Possible follow-ups:**
- How would you determine whether this requires a field safety corrective action (FSCA)?
- What information would you need from the field to support the root cause investigation?