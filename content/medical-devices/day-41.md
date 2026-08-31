# medical-devices — Day 41

## Q1: How would you approach verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during a firmware update, given that the device must remain safe and functional if the update fails?

**Answer:** The core principle here is that a firmware update must never leave the device in an unbootable or unsafe state, especially for a medical device that may be actively monitoring a patient. I would start by designing the update architecture with redundancy and atomicity in mind. The most common approach is a dual-bank or A/B partition scheme, where the device boots from one bank while the other is being written. If the update fails partway through, the device can fall back to the previous known-good image. The bootloader needs to validate the new image before committing to it — typically using a CRC or cryptographic hash — and only then update the boot flag. If validation fails, the bootloader should automatically revert to the previous bank and log the event.

Beyond the boot architecture, I would verify the behavior through fault injection testing. This means deliberately corrupting the update image at various points — during the transfer, during the write to flash, and after the write but before the boot flag is set — and confirming that the device either completes the update safely or reverts to the previous version without losing patient monitoring functionality. I would also test what happens if power is lost mid-update, since that's a realistic scenario in a home environment. The device should be designed so that a power loss during the update window doesn't brick it — the bootloader should be able to detect an incomplete update and either retry or revert. Finally, I would verify that the device logs the failed update attempt and any relevant diagnostic information, so that field issues can be investigated without requiring the device to be returned to the manufacturer.

**Possible follow-ups:**
- How would you handle the case where the device has only a single flash bank and cannot support A/B partitioning due to cost or space constraints?
- What level of validation would you require for the update image itself — CRC, cryptographic signature, or both — and why?

---

## Q2: During IEC 60601-1 testing, your medical device fails the patient leakage current test under normal condition (NC) with a measurement of 120 µA on a BF-type applied part, where the limit is 100 µA. How would you approach diagnosing and resolving this?

**Answer:** The first step is to understand exactly where the leakage path is. I would start by reviewing the measurement setup to confirm the test was performed correctly — the measurement instrument, the applied part configuration, and the mains polarity. Sometimes a marginal failure like this can be influenced by test setup details, so I'd want to rule that out before changing the design.

Assuming the measurement is valid, I would systematically isolate the leakage sources. The main contributors to patient leakage current are typically: capacitive coupling across the isolation barrier, leakage through Y-capacitors or other components between the patient circuit and mains, and leakage through the power supply itself. I would measure the leakage contribution of each subsystem independently — disconnect the applied part from the rest of the circuit and measure leakage from the power supply alone, then add back sections one at a time. This helps identify whether the problem is in the power supply, the isolation barrier, or the applied part circuitry itself.

Common fixes include reducing the value of Y-capacitors across the isolation barrier, improving the layout to reduce parasitic capacitance between primary and secondary sides, or adding a guard trace or shield around the patient circuit. Sometimes the issue is that the isolation barrier's creepage and clearance are adequate but the PCB layout creates a parallel capacitive path — for example, a primary-side trace running close to a patient-side trace on adjacent layers. In that case, the fix is a layout change rather than a component change. I would also check whether the applied part has any components connected to earth or to the secondary ground that could be creating an unintended path. Once the fix is implemented, I would re-run the full leakage current test suite, not just the failing condition, because changes to the isolation barrier can affect other measurements like touch current or earth leakage.

**Possible follow-ups:**
- How would you decide whether to fix this with a component change versus a PCB layout change, given that the device is already in the test lab?
- What single-fault conditions would you also need to re-test after making changes to the isolation barrier?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The key challenge here is that sharing an ADC and multiplexer introduces coupling and timing interactions between the two measurement channels. The test plan needs to verify not just that each channel meets its accuracy specification in isolation, but that they meet it when operating simultaneously and when the input conditions are changing.

I would structure the test plan in layers. First, baseline accuracy testing for each channel independently — temperature alone, pressure alone — using calibrated reference standards. This establishes the intrinsic accuracy of each channel. Second, cross-channel interaction testing: measure temperature while the pressure channel is driven with a worst-case signal, and vice versa. This catches issues like multiplexer crosstalk, charge injection, or settling time problems where one channel's signal affects the other. Third, simultaneous accuracy testing: apply known temperature and pressure inputs at the same time and verify both readings are within specification. This is the condition that most closely matches real-world use.

I would also test the multiplexer switching behavior specifically — for example, how quickly the ADC settles after switching between channels, and whether the firmware's sampling sequence introduces any systematic error. If the firmware samples temperature and pressure at different rates, I'd verify that the timing doesn't create aliasing or missed samples. Temperature sensors are often slow-moving, while pressure can change rapidly, so the test plan should include dynamic pressure changes while temperature is being measured to ensure the multiplexer switching doesn't introduce artifacts. Finally, I would include a test where both inputs are at the extremes of their ranges simultaneously — for example, high temperature and high pressure — since the ADC's input range and the multiplexer's linearity may degrade at the edges.

**Possible follow-ups:**
- How would you determine the appropriate settling time for the multiplexer, and how would you verify it in the test plan?
- What would you do if the cross-channel interaction testing revealed that the pressure channel's signal was affecting the temperature reading by more than the allowed error budget?

---

## Q4: You're leading a project where a field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint because it involves direct patient harm, so I would treat it as a potential safety issue and escalate it appropriately. The first priority is patient safety — I would work with the clinical team and regulatory affairs to determine whether the device should be recalled, whether use should be restricted, or whether the investigation can proceed while the device remains in use. This decision would be based on the severity of the irritation, the number of patients affected, and whether there's a pattern that suggests a systemic issue versus an isolated incident.

For the technical investigation, I would approach it systematically. The possible root causes fall into several categories: material-related (the silicone itself or a contaminant), manufacturing-related (residue from a cleaning or molding process), design-related (the pad's geometry causing friction or pressure), or use-related (interaction with a cleaning agent or patient skin condition). I would start by examining the affected pads — both returned units and retained samples from the same manufacturing lots — using appropriate analytical techniques to check for material composition, surface contaminants, or manufacturing residues. I would also review the manufacturing records for the affected lots to see if there were any process deviations. At the same time, I would gather clinical details from the complaint reports — the severity, the time to onset, whether the irritation was localized to the contact area, and whether any patients had pre-existing skin conditions.

I would also review the biocompatibility testing that was done during development — specifically the ISO 10993 testing for the pad material — to see if the testing covered the actual conditions of use, including prolonged skin contact and potential interaction with cleaning agents. If the investigation points to a material or manufacturing issue, the corrective action might involve changing the material formulation, modifying the manufacturing process, or adding a cleaning step. If it points to a use-related issue, the corrective action might involve updating the instructions for use or changing the pad's design. Throughout the process, I would document everything in the complaint handling system and coordinate with regulatory affairs on any reporting obligations, since skin irritation on a patient-contacting part may be a reportable adverse event.

**Possible follow-ups:**
- How would you determine whether this complaint requires a field safety corrective action (FSCA) versus a less urgent corrective action?
- What would you do if the investigation found that the silicone material itself was biocompatible, but the irritation was caused by a reaction between the pad and a specific cleaning agent used by some patients?

---

## Q5: How would you approach creating a clinical evaluation report (CER) for a novel medical device that has no substantially equivalent predicate device on the market?

**Answer:** A CER for a novel device is more challenging because you can't rely on equivalence to an existing device to establish clinical safety and performance. The approach needs to be built on a thorough understanding of the device's intended use, the clinical condition it addresses, and the available scientific literature.

I would start by clearly defining the device's intended purpose, target population, and clinical claims. This drives everything else in the CER. Next, I would conduct a systematic literature search covering the clinical condition, the technology or mechanism of action, and any related devices or therapies. Even if there's no equivalent device, there may be literature on the underlying technology — for example, if the device uses a novel sensor for respiratory monitoring, there may be studies on that sensing modality in other contexts. The literature search needs to be documented with clear inclusion and exclusion criteria, search terms, and databases used, so that the CER is defensible in a regulatory submission.

Since there's no predicate, the CER will likely need to rely more heavily on clinical investigation data — either from a clinical study conducted for this device or from well-documented case studies. I would work with the clinical team to determine what clinical evidence is needed and whether a formal clinical study is required. The CER should also reference the device's design verification and validation data, particularly any bench testing that demonstrates performance relevant to clinical outcomes. For example, if the device measures a physiological parameter, the accuracy data from design verification is directly relevant to clinical safety and performance.

The structure of the CER should follow the relevant guidance — typically MEDDEV 2.7/1 or the equivalent — and should include a critical evaluation of the literature, not just a summary. This means assessing the quality and relevance of each study, identifying gaps in the evidence, and discussing how those gaps are addressed. The conclusion should state whether the clinical evidence is sufficient to support the device's safety and performance for its intended use, and should identify any residual uncertainties and how they will be managed — for example, through post-market clinical follow-up. For a novel device, the CER is often a living document that gets updated as more clinical data becomes available.

**Possible follow-ups:**
- How would you determine whether a clinical study is required, versus relying on literature and bench data alone?
- How would you handle the situation where the literature search reveals studies on the technology but none that directly address the device's intended use?