# medical-devices — Day 46

## Q1: How would you approach verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during a firmware update, given that the device must remain safe and functional if the update fails?

**Answer:** This is fundamentally about designing for update resilience and then verifying it systematically. First, I'd ensure the firmware architecture itself supports safe recovery — typically through a dual-bank or A/B partition scheme where the device boots from the last-known-good image if the new image fails validation. The bootloader should verify integrity (checksum or signature) before committing to the new image, and the application should have a fallback path that restores the previous version if the update doesn't complete or fails self-test on first boot.

For verification, I'd structure testing in layers. At the unit level, I'd test the bootloader's decision logic: what happens when the image header is corrupt, when the checksum fails, when the flash write is interrupted mid-block, and when power is lost at various points during the update. At the integration level, I'd simulate partial writes and corrupted sectors using debug hooks or fault injection to confirm the device rolls back correctly. At the system level, I'd perform power-loss testing at random points during actual update transfers — this is where you often find timing windows you didn't anticipate.

Critically, I'd verify that during any failure mode, the device either continues operating on the old firmware or enters a safe state — it must never become completely non-functional or present corrupted data as valid. For a medical device, I'd also confirm that the update failure doesn't disrupt any ongoing monitoring function if the device is in use during the update attempt. Finally, I'd document all of this in the software test plan per IEC 62304, including traceability from each failure mode to its verification test.

**Possible follow-ups:** How would you handle the case where the device loses power during the update and the old image is also partially corrupted? What role would a watchdog timer play in this recovery strategy?

---

## Q2: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory is full, given that the device must continue monitoring and displaying physiological data in real time?

**Answer:** The key design principle here is that data logging must never interfere with the real-time monitoring function — they should be decoupled architecturally, with logging running as a lower-priority task that can fail or stall without affecting the monitoring path. The test strategy needs to verify both that monitoring continues uninterrupted and that the device handles the full-memory condition gracefully.

I'd start by defining what "full" means in the context of the device's memory architecture — is it a dedicated flash partition for logs, a shared filesystem, or circular buffer? The expected behavior should be specified in the requirements: does the device overwrite oldest data, stop logging and alert the user, or compress existing data? That behavior needs to be verified against the requirement.

For testing, I'd use a combination of approaches. First, I'd fill the memory through normal operation or by writing test data directly to the flash to reach the boundary condition deterministically. Then I'd verify: the monitoring display continues updating without gaps or delays, alarms still trigger correctly, and the device provides the specified user notification (visual indicator, message, or alarm) that logging has stopped or data is being overwritten. I'd also test the transition point — what happens when the last block is written — and confirm there's no crash, watchdog reset, or data corruption in previously stored records.

I'd also test recovery: what happens when memory is cleared or the device is reset — does logging resume correctly? And I'd verify that the real-time clock timestamps on new entries remain accurate after the full condition is resolved. For a medical device, I'd also consider whether the loss of logging capability creates a safety risk — if so, the risk assessment should have identified this and the test plan should verify the corresponding risk controls.

**Possible follow-ups:** How would you test the boundary condition where memory becomes full while a high-priority alarm is simultaneously occurring? What user notification would you consider appropriate for a home-use device versus a hospital device?

---

## Q3: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using a proprietary protocol with a simple checksum, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** The clinical requirement here is clear: data loss must be detectable, and the display must indicate staleness. A simple checksum alone doesn't satisfy that — it can detect corruption within a received packet, but it can't detect a packet that was never received. So the real question isn't whether to use a proprietary protocol, but what mechanisms are needed to meet the clinical requirement regardless of protocol choice.

I'd frame the discussion around what the protocol needs to provide: sequence numbers or timestamps to detect gaps in transmission, a timeout mechanism on the display side to detect when data stops arriving, and a clear staleness indicator. The proprietary protocol with a checksum could work if it includes sequence numbers and the display implements a timeout — but I'd ask whether the firmware engineer has considered what happens when packets are lost in bursts, or when the link degrades but doesn't drop completely.

I'd also raise the question of whether a standards-based protocol (like Bluetooth or a well-documented RF protocol) might be more appropriate given the regulatory landscape — proprietary protocols can be harder to validate for coexistence and may complicate the IEC 60601-1-2 wireless coexistence assessment. However, I wouldn't dismiss the proprietary approach outright if it has adequate mechanisms and the team can demonstrate reliable performance through testing.

The decision should be driven by a risk assessment: what's the clinical impact of undetected data loss? For a monitoring device, stale data could lead to delayed intervention. I'd want to see the failure modes analyzed and the protocol design mapped against them. If the proprietary protocol with sequence numbers and a staleness timeout adequately addresses the risks, and the team can verify it under realistic RF conditions, it may be acceptable. But I'd push for the display to clearly indicate "no data received for X seconds" rather than showing the last value without context — that's the critical safety feature regardless of protocol choice.

**Possible follow-ups:** How would you verify that the staleness indication works correctly under real-world RF interference conditions? What testing would you require to demonstrate that the proprietary protocol is reliable enough for a medical device?

---

## Q4: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The shared ADC and multiplexer introduces a specific risk: cross-channel interference and timing-dependent errors. When the multiplexer switches between channels, the ADC needs settling time, and if the firmware doesn't account for that, you can get inaccurate readings on one or both channels. Also, if the sensors have different output impedances or drive capabilities, the multiplexer's on-resistance and leakage can affect accuracy differently on each channel.

I'd structure the verification plan around several key areas. First, accuracy verification for each channel independently — using calibrated references for temperature and pressure, measuring across the full specified range and at multiple points, and confirming the device meets its accuracy specification for each parameter when measured alone.

Second, and more critically, simultaneous accuracy testing — this is where the shared ADC creates risk. I'd verify that when both sensors are active and being sampled in sequence, each channel still meets its accuracy specification. This means testing at various combinations of temperature and pressure values, including extremes, to ensure the multiplexer switching and ADC settling don't introduce cross-channel errors.

Third, I'd test timing-related behavior: sampling rate, channel switching frequency, and whether the firmware correctly sequences acquisitions. I'd also verify that the device handles the case where one sensor is at its extreme range while the other is at its mid-range — this is where multiplexer leakage or settling issues are most likely to appear.

I'd also include repeatability and drift testing over time, since the shared ADC can introduce temperature-dependent drift in the reference or the multiplexer. And I'd verify the calibration approach — if the device uses per-channel calibration factors, I'd confirm they're correctly applied regardless of sampling order.

Finally, I'd want to review the firmware's sampling algorithm to understand what settling time is implemented between channel switches, and verify through testing that this is adequate across the operating temperature range of the device — the ADC's settling characteristics can change with temperature.

**Possible follow-ups:** How would you determine the appropriate settling time between channel switches, and how would you verify it's adequate across the device's operating temperature range? What would you do if you discovered that the two sensors have significantly different output impedances?

---

## Q5: You're leading a project where a field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that requires immediate attention given the patient safety implications. I'd approach it as a structured investigation following the principles of root cause analysis and corrective action, while also considering the regulatory obligations for medical device reporting.

First, I'd ensure patient safety is addressed immediately — that means confirming whether the device should be pulled from use, whether patients need clinical follow-up, and whether there's a pattern that suggests a broader risk. I'd work with the clinical team and quality department to assess the severity and determine if a field safety corrective action or recall is warranted. I'd also check regulatory reporting requirements — depending on the jurisdiction, skin irritation from a patient-contacting device may be a reportable adverse event.

For the technical investigation, I'd gather all available information: the specific complaints, photos or clinical documentation of the irritation, lot numbers and manufacturing dates of the affected devices, and any environmental factors (cleaning agents, patient skin conditions, duration of contact). I'd then examine the silicone material itself — was there a change in the raw material supplier, a formulation change, or a manufacturing process variation that could have affected the material's biocompatibility? I'd review the material certifications and any incoming inspection records for the affected lots.

I'd also consider whether the issue is related to the device design rather than the material — for example, is the pad occlusive, trapping moisture against the skin? Is there a mechanical irritation component from the pad's shape or edge finish? Is there a residue from manufacturing (mold release agents, cleaning solvents) that wasn't fully removed?

The investigation would include testing: reviewing the ISO 10993 biocompatibility documentation for the material, potentially conducting additional testing on retained samples from the affected lots, and comparing against samples from unaffected lots. I'd also consider whether the issue is specific to certain patient populations or usage conditions.

Once the root cause is identified, I'd implement corrective actions — which could range from material substitution, process changes, design modifications, or updated instructions for use. I'd verify the effectiveness of the corrective action through appropriate testing and monitoring of field performance after implementation. Throughout the process, I'd document everything in the complaint handling system and ensure traceability to the risk management file, updating the risk assessment if the investigation reveals hazards not previously identified.

**Possible follow-ups:** How would you determine whether this complaint requires a field safety corrective action (FSCA) versus a less urgent response? What information would you need from the field to help narrow down whether this is a material issue, a manufacturing issue, or a usage issue?