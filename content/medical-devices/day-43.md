# medical-devices — Day 43

## Q1: How would you approach verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during a firmware update, given that the device must remain safe and functional if the update fails?

**Answer:** This is fundamentally a question about designing for update resilience, and the verification strategy should flow directly from the design architecture. First, I'd want to understand the update mechanism itself — specifically whether the device uses a dual-bank or A/B partition scheme, or a single-bank with a bootloader that can recover from a corrupted application image. The verification approach depends heavily on that architecture.

For a medical device, the key principle is that the device must never be left in a state where it cannot at least enter a safe mode. My approach would be to build a fault injection test matrix that covers the failure points in the update sequence: interruption of power during the erase phase, during the write phase, during the verification/checksum phase, and during the bootloader's handoff to the new application. I'd also test corruption at different stages — for example, corrupting the vector table, the application header, or random sectors within the image.

The test strategy would include both automated and manual elements. On the automated side, I'd use a test harness that can simulate power loss at precise moments during the update, and that can inject bit errors into the flash contents before the device reboots. On the manual side, I'd verify the user-visible behavior: does the device indicate that the update failed? Does it retry automatically, or does it require user intervention? Does it revert to the previous known-good version?

Critically, I'd verify that the device's safety functions are not compromised during the update failure. For example, if the device is a patient monitor, it should still be able to detect and alarm on critical physiological events even if the update failed and it's running in a degraded mode. This means the verification plan needs to include functional safety testing in the post-failure state, not just checking that the device can recover its firmware.

I'd also verify the integrity-checking mechanism itself — whether it's a CRC, SHA hash, or digital signature — by testing edge cases like a valid checksum with corrupted data (which shouldn't be possible with a strong hash, but the test should confirm the detection mechanism actually catches corruption). Finally, I'd document all of this in the software verification traceability matrix, linking each test case back to the specific requirement for update failure handling.

**Possible follow-ups:** How would you decide between automatic rollback versus requiring service intervention after a failed update? What level of user indication would you require during the update process itself?

---

## Q2: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory is full, given that the device must continue monitoring and displaying physiological data in real time?

**Answer:** The core tension here is between the device's primary function — continuous real-time monitoring — and its secondary function of logging data for later review. The design intent should be that logging is a non-critical function that must never interfere with monitoring, and the test strategy should verify that this priority is maintained under memory-full conditions.

My approach would start by understanding the logging architecture: is data written to a ring buffer that overwrites oldest entries, or does logging stop when full? Is there a separate partition for critical event logs versus routine waveform data? The answers to these questions shape what "correct behavior" means for the test.

The test strategy would cover several scenarios. First, I'd test the nominal case: fill the memory to capacity and verify that the device continues monitoring and displaying data without interruption, and that the user is notified that logging has stopped or is overwriting old data. Second, I'd test the transition point — the moment when memory transitions from not-full to full — to ensure there's no glitch in the monitoring function. Third, I'd test what happens when the user attempts to retrieve or export logged data while the memory is full, to ensure that operation doesn't cause a fault.

I'd also test the interaction between memory-full conditions and other events. For example, if a critical alarm occurs while memory is full, is the alarm event still captured in a protected area of memory? If the device is reset while memory is full, does it boot correctly and handle the full condition gracefully on startup?

From a verification perspective, I'd want to test with realistic data volumes, not just fill the memory with dummy data. The logging format and data rates matter — for example, if the device logs at different rates for different parameters, the memory-full condition might be reached differently than a simple linear fill would suggest. I'd also verify that the memory-full handling doesn't introduce timing jitter into the monitoring loop, which could be tested by measuring interrupt latency or task scheduling during the memory-full condition.

Finally, I'd verify the user interface behavior: the device should clearly indicate that logging is unavailable, and this indication should be tested under different ambient conditions (e.g., in a dimly lit room where the display might be harder to read) and for users with different levels of technical expertise.

**Possible follow-ups:** How would you handle the trade-off between overwriting old data versus stopping logging entirely? What information would you preserve in the user interface to help clinicians understand the gap in logged data?

---

## Q3: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using a proprietary protocol with a simple checksum, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** This is a situation where the clinical requirement should drive the technical solution, not the other way around. The clinical team is asking for two specific capabilities: detection of data loss and indication of staleness. A proprietary protocol with a simple checksum can detect corruption, but it doesn't inherently provide detection of missing data — a dropped packet is simply absent, and the receiving end can't distinguish between "no data was sent" and "data was sent but lost."

My approach would be to reframe the discussion around the actual requirements rather than the specific protocol choice. The key questions are: what is the maximum acceptable latency between data acquisition and display? What is the clinical consequence of stale data? How long can the display show old data before it becomes misleading?

Once those requirements are clear, the technical solution becomes more obvious. The protocol needs sequence numbers or timestamps so the receiver can detect gaps. It needs a timeout mechanism so the display can determine that data has stopped arriving. And it needs a clear staleness indicator — for example, a visual change or message that appears after a defined period without fresh data.

Regarding the proprietary protocol with a simple checksum, I'd raise several concerns. First, proprietary protocols are harder to validate and maintain over the device's lifetime, especially if the wireless module is ever replaced. Second, a simple checksum may not be sufficient for detecting all realistic corruption patterns — a CRC or cryptographic hash provides stronger integrity assurance. Third, the protocol needs to handle not just corruption but also packet loss, reordering, and duplication, which a checksum alone doesn't address.

I'd suggest the team evaluate established protocols that already provide the needed features — for example, Bluetooth Low Energy with its link-layer acknowledgment and sequence numbering, or a higher-level protocol that includes message framing, sequence numbers, and acknowledgment. These protocols have been extensively tested and their failure modes are well understood, which is valuable for a medical device where the verification burden is significant.

If the team still wants to use a proprietary protocol, I'd require that it include sequence numbers, timestamps, and a defined staleness detection mechanism, and that the verification plan specifically tests packet loss, reordering, and delayed delivery scenarios. The clinical requirement for staleness indication should be traced through the design to a specific technical mechanism, and that mechanism should be tested under realistic wireless conditions.

**Possible follow-ups:** How would you determine the appropriate timeout duration for declaring data stale? What would you do if the clinical team's requirement for staleness detection conflicts with the wireless protocol's power consumption characteristics?

---

## Q4: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The shared ADC and multiplexer introduce a coupling between the two measurement channels that wouldn't exist if each sensor had its own dedicated ADC. The verification plan needs to specifically test for cross-channel interference, settling time issues, and the impact of multiplexer switching on measurement accuracy.

My approach would start by understanding the measurement architecture in detail: the ADC resolution and sampling rate, the multiplexer switching sequence, the settling time between channel switches, and the signal conditioning for each sensor. The key risk is that switching between channels can cause artifacts — for example, if the pressure sensor has a higher output impedance than the temperature sensor, the ADC input might not fully settle before sampling, causing the temperature reading to be affected by the previous pressure measurement.

The test plan would include several categories of testing. First, I'd test each channel independently for accuracy against a reference standard, with the other channel disconnected or held at a fixed value. This establishes the baseline accuracy for each parameter. Second, I'd test both channels simultaneously with known inputs to verify that accuracy is maintained when both sensors are active. Third, I'd test the transition between channels — for example, rapidly changing the pressure input while measuring temperature, to verify that the temperature reading isn't affected by the pressure change.

I'd also test the multiplexer timing directly. If the firmware controls the switching sequence, I'd verify that the settling time between channels is adequate for the ADC's resolution. This might involve measuring the ADC input voltage during the switching transient, or testing with worst-case sensor impedances.

For the accuracy verification, I'd use a matrix approach: vary temperature across its specified range while holding pressure at several fixed values, then vary pressure while holding temperature at several fixed values. This tests for interaction effects that might not appear when each parameter is tested independently. I'd also test at the extremes of the operating range, where settling time and cross-channel effects are often worst.

Finally, I'd consider the clinical context. If the temperature and pressure measurements are used together in a calculation or decision, I'd verify the combined accuracy — for example, if the device calculates a derived parameter from both measurements, the error in that derived parameter should be within specification even when both inputs are at their worst-case combination.

**Possible follow-ups:** How would you determine the required settling time between multiplexer channel switches? What would you do if you discovered that the two sensors have significantly different output impedances, and how would that affect your test approach?

---

## Q5: You're leading a project where a field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that potentially involves patient safety, so my first priority would be to ensure patient safety while gathering enough information to understand the scope of the problem. I'd approach this as a structured investigation following the principles of root cause analysis and corrective action, consistent with how medical device manufacturers handle field complaints.

The first step would be to assess immediate risk. I'd want to know: how many patients are affected? What is the severity of the irritation? Is it a temporary rash that resolves when the device is removed, or is it more serious? Are there any patterns — for example, does it occur with a specific lot of sensor pads, or with a specific device configuration? Based on this initial assessment, I'd determine whether a field safety corrective action is needed, such as a recall or a safety notice to users, or whether the investigation can proceed without immediate action.

Next, I'd assemble a cross-functional team including clinical affairs, quality, regulatory, and engineering. The clinical team would help characterize the skin reaction and determine whether it's an allergic response, a mechanical irritation, or something else. The quality team would help trace the affected sensor pads back to their manufacturing lots and review the incoming material specifications. The engineering team would examine the sensor pad design and materials.

The investigation would have several parallel tracks. One track would examine the material itself — is the silicone formulation consistent with the specification? Were there any changes in the raw material supplier or processing parameters that could have introduced a contaminant or changed the material's properties? Another track would examine the manufacturing process — was there any deviation in curing time, temperature, or cleaning procedures that could have left residual chemicals on the pad surface? A third track would examine the clinical usage — are the affected patients using the device in a way that could cause irritation, such as prolonged contact without repositioning, or is there something about the patient population (e.g., neonates with sensitive skin) that makes them more susceptible?

I'd also review the biocompatibility testing that was done during development. The sensor pad should have been tested per ISO 10993 for cytotoxicity, sensitization, and irritation. I'd want to verify that the testing was done on the final material formulation and that the test methods were appropriate for the intended contact duration. If there's any gap between the tested material and the production material, that would be a key finding.

Once the root cause is identified, I'd develop a corrective action plan. This might involve changing the material formulation, modifying the manufacturing process, adding a cleaning step, or changing the clinical instructions for use. The corrective action would need to be verified — for example, by repeating the biocompatibility testing on the revised material, or by conducting a clinical evaluation with the revised sensor pad.

Throughout this process, I'd keep the regulatory and quality teams informed, since this type of complaint may need to be reported to regulatory authorities depending on the severity and the jurisdiction. I'd also document the entire investigation in the complaint handling system, following the requirements of ISO 13485 and the applicable regulatory framework.

**Possible follow-ups:** How would you determine whether this complaint needs to be reported to regulatory authorities as a field safety corrective action? What information would you gather from the clinical sites to help characterize the skin irritation, and how would you ensure that information is collected consistently across sites?