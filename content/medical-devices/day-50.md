# medical-devices — Day 50

## Q1: How would you approach verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during normal operation, given that the device must continue monitoring and displaying physiological data in real time?

**Answer:** I'd start by recognizing that non-volatile memory corruption during normal operation presents two distinct concerns: data integrity (preserving logged physiological data) and functional continuity (maintaining real-time monitoring). These need to be addressed separately because the priorities differ — a monitoring failure is an immediate patient safety issue, while data loss may be a longer-term clinical or regulatory concern.

For the monitoring function, the firmware architecture should isolate the real-time monitoring path from any dependency on non-volatile memory. If monitoring requires configuration parameters stored in flash, those should be cached in RAM at boot, so a mid-operation flash corruption doesn't affect the active monitoring loop. The firmware should also detect corruption events — typically through CRC or checksum verification on read-back, or by using a redundant/dual-bank flash layout where a corrupted bank triggers a rollback to a known-good image.

For the logged data, I'd design a strategy that includes: write-ahead logging or a journaling approach so a corruption event doesn't destroy previously valid records; periodic integrity checks rather than only checking at write time; and a defined behavior when corruption is detected — for example, quarantining the corrupted region, continuing to log to a fresh region, and raising an alarm or status indicator so the issue is visible to the user.

The test strategy would then verify each of these behaviors: injecting corruption into specific memory regions (via a test backdoor or fault injection at the driver level), confirming the monitoring function is unaffected, confirming that previously stored data remains retrievable, and confirming that the device generates the appropriate alert. I'd also test the boundary conditions — corruption during an active write, corruption spanning multiple sectors, and corruption that affects the boot image versus only data regions.

**Possible follow-ups:**
- How would you decide whether the device should continue operating normally, enter a degraded mode, or shut down when corruption is detected?
- How would you verify that the corruption-detection mechanism itself doesn't consume enough CPU time to affect real-time monitoring performance?

---

## Q2: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using a proprietary protocol with a simple checksum, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** The core issue here is that a simple checksum detects bit errors but doesn't address the clinical requirement of detecting missing or stale data. These are different failure modes: corruption (bits flipped in transit) versus loss (packets never arrive or arrive too late to be clinically useful). The clinical team's requirement is fundamentally about data freshness and continuity, not just bit-level integrity.

I'd approach this by first clarifying the clinical requirements precisely: what does "stale" mean in terms of time for this particular physiological parameter? What's the acceptable latency between data acquisition and display? What should the display unit do when data is stale — show a warning, blank the value, sound an alarm? These answers drive the technical design.

With those requirements defined, I'd evaluate the proposed protocol against them. A proprietary protocol with a simple checksum can be extended to include sequence numbers and timestamps, which would allow the receiver to detect missing packets and calculate data age. The question then becomes whether the existing proposal already includes these fields or whether they need to be added. If the protocol lacks them, the fix is relatively straightforward — add a sequence counter and timestamp to each packet, and have the receiver track expected sequence numbers and flag gaps.

The broader trade-off is between protocol simplicity and clinical safety requirements. In a medical device, the protocol design should be driven by the risk analysis: what's the clinical consequence of undetected data loss? For a monitoring device, missing a transient event (like a brief arrhythmia or a pressure spike) could have serious consequences, so the protocol needs to make loss detectable. I'd also consider whether an acknowledged protocol is needed — if the display unit must confirm receipt, that adds complexity and latency but provides stronger guarantees. For a one-way monitoring link, sequence numbers with a staleness indicator on the display may be sufficient, but this should be confirmed through the risk management process.

I'd also raise the question of whether using a standard protocol (like Bluetooth Low Energy with its built-in link-layer acknowledgment and sequence numbering) might be more appropriate than a proprietary protocol, given that standard protocols have been more thoroughly vetted for reliability and may simplify regulatory review.

**Possible follow-ups:**
- How would you verify that the staleness indication meets the clinical team's requirements during design verification?
- What if the wireless link is inherently lossy (e.g., the patient moves and the link drops)? How would you handle the trade-off between retransmission latency and real-time display requirements?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The key challenge here is that sharing an ADC and multiplexer creates coupling between the two measurement channels — settling time, crosstalk, and multiplexer switching artifacts can affect one channel's accuracy while the other is being sampled. The test plan needs to verify not just each channel's accuracy in isolation, but their accuracy when operating together in the intended sequence.

I'd structure the test plan in layers. First, baseline accuracy testing for each channel independently — temperature alone, pressure alone — using calibrated references traceable to known standards. This establishes that each channel meets its specification under ideal conditions.

Second, I'd test simultaneous operation: both sensors active, sampling in the same sequence as the firmware will use in normal operation. This is where coupling effects would surface. I'd specifically test worst-case scenarios: a large step change on one channel (e.g., pressure suddenly changes from low to high) while the other channel is measuring a steady-state value. This would reveal settling time issues or crosstalk through the multiplexer.

Third, I'd test across the operating range and environmental conditions — temperature accuracy at the extremes of the pressure range and vice versa, since the device's self-heating or environmental temperature could affect the pressure sensor's accuracy.

I'd also consider the timing aspects: the test plan should verify that the measurement update rate meets the clinical requirement for both parameters, since sharing an ADC means the sampling rate per channel is reduced compared to dedicated ADCs. If the device needs to detect rapid pressure changes while also monitoring temperature, the multiplexer sequence and settling time become critical.

Finally, I'd include fault injection testing — what happens if one sensor fails or produces an out-of-range signal? Does that affect the other channel's accuracy? The test plan should verify that the firmware correctly handles a fault on one channel without corrupting measurements on the other.

**Possible follow-ups:**
- How would you determine the appropriate settling time for the multiplexer between switching channels, and how would you verify it's sufficient?
- How would you handle the situation where the two sensors have different optimal ADC settings (e.g., different gain or sampling rates)?

---

## Q4: You're leading a project where a field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that touches on biocompatibility, clinical safety, and potentially the device's design history file. I'd approach it as a structured investigation following a formal root-cause analysis process, likely an 8D or similar methodology, because the implications could range from a material lot issue to a fundamental design flaw.

First, I'd ensure patient safety is addressed immediately. That means working with the clinical team and regulatory affairs to determine whether the device should be recalled, whether usage should be restricted, or whether the issue is isolated enough to continue use with enhanced monitoring. This decision would be based on the severity of the irritation, the number of reports relative to devices in the field, and whether there's a pattern suggesting a systemic issue. I'd also ensure that all complaints are collected and documented consistently so we have accurate data on the scope.

Next, I'd begin the technical investigation. The key questions are: Is this a material problem, a manufacturing problem, or a design problem? I'd want to examine the affected sensor pads — both returned units and retained samples from the same manufacturing lots. I'd look at the material composition and whether it matches the specification, check for manufacturing process variations (curing time, temperature, contamination), and review the material's biocompatibility testing history. I'd also consider whether the issue is related to patient factors — for example, prolonged contact time, skin sensitivity, or interaction with other substances like cleaning agents.

I'd also review the design history file to understand what biocompatibility testing was originally performed, what the intended use and contact duration were, and whether the current field usage matches those assumptions. If the device is being used for longer continuous contact than originally validated, that could explain the issue even if the material itself hasn't changed.

Once the root cause is identified — or while the investigation is ongoing — I'd work with the quality team to determine the appropriate corrective action. This could range from a supplier material change, a manufacturing process adjustment, a design change to the sensor pad material or geometry, or a labeling change with updated usage instructions. The corrective action would need to be verified through appropriate testing (biocompatibility re-testing if the material changes, design verification if the design changes) and would need to go through the organization's change control process.

Throughout this process, I'd keep the regulatory implications in mind. Depending on the severity and scope, this could require a field safety corrective action (FSCA), notification to regulatory authorities, and updates to the clinical evaluation and risk management files. The investigation findings would also feed back into the risk management process to determine whether the hazard was previously identified and whether the risk controls were adequate.

**Possible follow-ups:**
- How would you determine whether this is an isolated issue or a systemic problem requiring a recall?
- How would you communicate with the affected clinical sites during the investigation without causing undue alarm or making premature statements about the cause?

---

## Q5: How would you approach verifying that a medical device's firmware meets IEC 62304 requirements for a Class C software safety classification?

**Answer:** For Class C software — where a software failure could result in death or serious injury — IEC 62304 requires the most rigorous development and verification approach. I'd start by confirming that the classification is correct through the risk management process, since that determines the entire scope of activities. If the software directly controls therapy delivery or makes safety-critical decisions without independent hardware protection, Class C is appropriate.

The verification strategy would span the full development lifecycle, not just testing. First, I'd ensure the software requirements are traceable to system requirements and that each software requirement has clear, testable acceptance criteria. This traceability matrix is the backbone of the verification effort — every requirement must map to a test, and every test must map to a requirement.

For the development process itself, I'd verify that the team followed the required practices: coding standards, peer reviews of all code changes, and static analysis to identify potential defects early. The depth of documentation and review rigor increases with the safety class, so I'd confirm that the design documentation — software architecture, detailed design, and interface descriptions — is complete and consistent with the implementation.

For testing, I'd structure it in layers. Unit testing would verify individual functions and modules, with coverage analysis to ensure that critical code paths are exercised — for Class C, modified condition/decision coverage (MC/DC) is typically expected for the most safety-critical functions. Integration testing would verify that modules interact correctly, particularly at interfaces where data is passed between safety-critical and non-critical functions. System testing would verify the software against its requirements in the context of the complete device, including hardware-software interaction.

I'd also include fault injection testing as part of the verification — deliberately introducing failures (sensor faults, memory corruption, timing violations) to verify that the software's error handling behaves as specified. For Class C, the software must detect and respond to faults in a way that maintains safety, and this needs to be demonstrated through testing, not just argued in documentation.

Finally, I'd verify that the release criteria are met: all identified defects are resolved or have documented risk acceptance, all verification activities are complete with results recorded, and the software version is uniquely identified and traceable to the design history file. The verification evidence would be reviewed as part of the design review process, and any gaps would need to be addressed before the software is released for clinical use.

**Possible follow-ups:**
- How would you determine the appropriate level of code coverage for Class C software, and how would you justify that decision to a regulatory auditor?
- How would you handle a situation where a defect is found during system testing that requires a significant architectural change to the software?