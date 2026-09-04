# medical-devices — Day 45

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during a firmware update, given that the device must remain safe and functional if the update fails?

**Answer:** The core principle here is that a firmware update is a period of elevated risk — the device is in an indeterminate state, and the consequences of failure depend heavily on the device's role. My approach would start with a failure modes analysis: what happens if power is lost mid-write, if the image is corrupted in transit, or if the new image is incompatible with the hardware? The architecture should support a recovery path that doesn't require the user to return the device to the manufacturer.

First, I'd design for atomicity and rollback. The standard approach is a dual-bank or A/B partition scheme where the device boots from the last-known-good image while the new image is written to the inactive bank. A bootloader with a validity check — CRC or cryptographic signature verification — determines which bank to boot. If the new image fails validation, the bootloader falls back to the previous version. This needs to be tested under fault injection: interrupting the update at various points, corrupting the image mid-transfer, and simulating power loss during the flash write cycle.

Second, I'd verify the behavior during the update itself. The device should communicate its state clearly — for example, an LED indicator or display message that an update is in progress — and it should handle the case where the update fails gracefully. For a medical device, this might mean reverting to the previous version and alerting the user that the update was unsuccessful, rather than entering an undefined state.

Third, I'd test the post-update verification. After a successful update, the device should confirm the new image is valid and that critical safety functions still operate correctly. This might include a self-test routine that exercises the monitoring functions before returning to normal operation.

The test strategy would combine automated fault injection at the firmware level with hardware-level testing — for example, using a programmable power supply to cut power at precise moments during the flash write. Each test case would map back to a specific failure mode identified in the risk analysis, with pass/fail criteria defined in advance.

**Possible follow-ups:** How would you handle the case where the device is in the middle of patient monitoring when an update is initiated? What mechanisms would you use to ensure the bootloader itself is protected from corruption?

---

## Q2: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The key challenge here is that sharing an ADC and multiplexer introduces coupling mechanisms that wouldn't exist with independent signal chains — settling time, crosstalk between channels, and multiplexer switching transients can all affect accuracy. The test plan needs to verify not just that each channel meets its specification in isolation, but that both meet specification when operating together under realistic conditions.

I'd structure the test plan around several layers. First, baseline accuracy testing: each channel is characterized against a reference standard across the full measurement range, with the other channel held at a fixed value. This establishes the individual channel performance. Second, simultaneous operation testing: both sensors are driven with known inputs that span their operating ranges, and I'd verify that the measured values remain within specification for both channels. This catches issues like insufficient settling time when the multiplexer switches between channels, or crosstalk through the shared ADC input.

Third, I'd test dynamic scenarios. For example, if the pressure sensor is experiencing a rapid transient while the temperature sensor is measuring a slowly varying signal, does the pressure transient bleed into the temperature reading? This is particularly relevant in a medical device where one parameter might change quickly while the other is used for a critical decision. I'd also test worst-case switching patterns — for instance, alternating between the extremes of each channel's range to maximize settling time demands.

Fourth, I'd include environmental testing. Temperature and pressure sensors often have different environmental sensitivities, and the shared signal chain might behave differently across the device's operating temperature range. Testing at temperature extremes, with both sensors active, would verify that accuracy is maintained.

Finally, I'd ensure the test plan includes enough statistical power — multiple units, repeated measurements — to distinguish between random variation and systematic errors. The acceptance criteria should be tied directly to the device's accuracy specifications, with appropriate margins for measurement uncertainty in the test equipment itself.

**Possible follow-ups:** What specific test equipment would you use to generate reference temperature and pressure inputs simultaneously? How would you determine whether observed errors are due to the sensors themselves versus the shared signal chain?

---

## Q3: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using a proprietary protocol with a simple checksum, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** This is fundamentally a risk management question dressed up as a protocol design question. The clinical requirement — detecting data loss and indicating staleness — exists because the physiological data is being used for clinical decisions, and acting on stale or incomplete data could be harmful. The firmware engineer's proposal for a simple checksum addresses random bit errors but doesn't address the broader failure modes: lost packets, out-of-order delivery, or a link that's completely down.

I'd start by clarifying the clinical use case. What decisions are being made based on this data? How quickly does data become clinically irrelevant? What's the consequence of the display showing data that's actually 30 seconds old? The answers to these questions define the requirements: maximum acceptable data latency, how quickly staleness must be indicated, and what the display should show when data is unavailable.

On the protocol side, I'd argue that the proprietary protocol with a simple checksum is insufficient for several reasons. A checksum detects corruption but not loss — if a packet never arrives, there's nothing to checksum. The protocol needs sequence numbers to detect missing packets, and it needs a timeout mechanism to detect a completely failed link. The display unit needs to track the last received data timestamp and indicate staleness when that timestamp exceeds a clinically defined threshold.

However, I'd also push back on the assumption that a full standards-based protocol is necessarily required. The right answer depends on the environment and the criticality. A simple protocol with sequence numbers, acknowledgments, and a staleness timeout might be perfectly adequate — and it has the advantage of being simple enough to verify deterministically. The key is that the protocol design must trace back to the clinical requirements, not be driven by implementation convenience.

I'd also raise the question of what happens when the link fails entirely. Does the display unit have its own alarm capability? Does it need to alert clinical staff that monitoring has been interrupted? This is a safety function that needs to be designed and tested, not an afterthought.

**Possible follow-ups:** How would you verify that the staleness indication itself is reliable and timely? What happens if the wireless link fails during a critical event — how does the system ensure the clinician is aware?

---

## Q4: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory is full, given that the device must continue monitoring and displaying physiological data in real time?

**Answer:** The fundamental tension here is between two competing requirements: the device must not lose the ability to record physiological data that may be needed for clinical decisions, but it also must not let data logging interfere with the real-time monitoring function. The test strategy needs to verify both the behavior when memory is full and the transition into that state.

I'd start by defining the expected behavior clearly. What should the device do when memory is full? The options typically include: overwriting the oldest data (circular buffer), stopping logging but continuing to monitor with a clear user indication, or attempting to offload data to an external system. Each approach has different clinical implications. For example, if the data is used for retrospective analysis, silently overwriting old data might be unacceptable. If the data is only needed for immediate display, stopping logging with a clear alert might be fine.

The test strategy would cover several scenarios. First, the transition into the full state: I'd fill the memory to capacity and verify that the device behaves as specified — the appropriate alert is raised, monitoring continues uninterrupted, and no data corruption occurs at the boundary. Second, sustained operation in the full state: the device should continue monitoring and displaying data indefinitely, with the logging status clearly indicated. Third, recovery: when space becomes available (for example, after data is offloaded or the user clears the log), logging should resume correctly without gaps or duplication.

I'd also test edge cases around the memory-full condition. What happens if the device is logging data when the last block of memory is written? Is the write atomic — could a partial write corrupt the file system? What happens if the device is reset while in the memory-full state? Does it recover correctly on reboot?

Fault injection would be important here. I'd simulate the memory-full condition directly — for example, by pre-filling the memory or by using a test hook to force the file system to report full — rather than waiting for the device to naturally fill up over days of operation. This allows deterministic testing of the boundary conditions.

Finally, I'd verify that the user interface correctly reflects the state. If the device is supposed to indicate that logging has stopped, that indication needs to be tested under realistic conditions — for example, is it visible to a clinician who is focused on the monitoring display rather than a status icon?

**Possible follow-ups:** How would you decide between a circular buffer approach versus stopping logging with an alert? What data integrity checks would you include to verify that data written before the memory-full condition is not corrupted?

---

## Q5: You're leading a project where a field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that touches on patient safety, biocompatibility, and potentially the device's regulatory standing. My approach would follow a structured investigation process, starting with patient safety as the immediate priority.

The first step is to assess the severity and scope. How many patients are affected? What's the nature and severity of the irritation — mild redness or more serious reactions? Are there any patterns — specific patient populations, specific lots of sensor pads, specific usage conditions? This information determines whether immediate action is needed, such as a field safety notice or recall, or whether the investigation can proceed more deliberately. I'd work with the clinical team and regulatory affairs to make this assessment quickly.

The technical investigation would proceed in parallel. I'd start by examining the materials and manufacturing process. The silicone material itself might have changed — perhaps a supplier changed a raw material source, or a processing parameter shifted. I'd review the material certifications and any incoming inspection records. I'd also consider whether the issue is with the material itself or with something on the surface — residual mold release agent, cleaning agents used by the hospital, or interaction with other substances the pad contacts.

I'd also look at the usage conditions. Is the irritation related to how long the pad is in contact with the skin? Is it a mechanical issue — friction or pressure — rather than a chemical reaction? Are there differences between how the device is used in different facilities? This might require talking to the clinical sites where the complaints originated.

The investigation would be documented following the corrective and preventive action (CAPA) process. I'd establish a cross-functional team including clinical affairs, quality, manufacturing, and possibly the material supplier. We'd define the investigation protocol, collect and analyze data, and determine the root cause before deciding on corrective actions.

If the root cause points to a material or manufacturing issue, the corrective action might involve changing the material formulation, adjusting the manufacturing process, or adding a cleaning step. If it's a usage issue, the corrective action might involve updated instructions for use or clinician training. Either way, the fix would need to be verified — including biocompatibility testing if the material changes — and the risk management file would need to be updated to reflect the new hazard and control measures.

Throughout this process, I'd maintain clear communication with the regulatory authorities as required, and with the clinical sites that reported the complaints. Transparency is critical when patient safety is involved.

**Possible follow-ups:** How would you determine whether this requires a field safety corrective action (FSCA) versus a less urgent corrective action? What biocompatibility testing would you consider if the root cause points to the silicone material itself?