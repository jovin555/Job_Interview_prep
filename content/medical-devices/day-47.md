# medical-devices — Day 47

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during normal operation, given that the device must continue monitoring and displaying physiological data in real time?

**Answer:** I'd start by defining what "corrupted" means for this specific system — whether it's a single-bit error, a page-level failure, or a complete filesystem/partition corruption — because the mitigation strategy differs significantly for each case. The key architectural principle is that safety-critical monitoring functions should never depend on non-volatile memory being available; the device must have a defined behavior when storage fails.

First, I'd want to understand the firmware architecture: does the monitoring loop read from or write to non-volatile memory as part of its critical path, or is storage access isolated to a separate logging task? If storage is on the critical path, that's a design issue that needs addressing before testing. The ideal architecture has the monitoring function operating independently, with data logging occurring asynchronously — so a storage failure degrades logging capability but not patient monitoring.

For the test strategy itself, I'd use fault injection at multiple levels. At the driver level, I'd inject read/write failures to verify the firmware handles error codes gracefully. At the memory level, I'd use hardware fault injection or a debugger to corrupt specific memory locations and observe system behavior. At the system level, I'd simulate scenarios like a full filesystem, a corrupted file header, or a failed write during a power event.

The critical test cases would verify: (1) the monitoring display continues updating in real time without interruption, (2) no false alarms are generated as a result of the storage failure, (3) the device provides some indication to the user that logging has been compromised (if appropriate for the clinical use case), and (4) when storage is restored or recovered, the device handles the transition cleanly without a reset or data inconsistency.

I'd also test the recovery path — what happens when the device reboots with corrupted storage, and whether the device can detect and quarantine corrupted data rather than displaying potentially invalid historical information.

**Possible follow-ups:** How would you determine whether the device should continue operating with degraded logging or enter a safe state? What fault injection tools or methods would you use to corrupt non-volatile memory in a controlled, repeatable way during testing?

---

## Q2: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using a proprietary protocol with a simple checksum, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** This is fundamentally a risk management question, not just a protocol selection question. The clinical requirement is clear: data loss must be detectable, and stale data must be indicated. The question is what level of detection and indication is appropriate for the clinical risk.

I'd start by asking what the data is used for. If it's continuous waveform monitoring where a clinician is watching in real time, a brief dropout might be acceptable if the display clearly indicates "no data" during the gap. If the data is being used for trend analysis or clinical decision-making after the fact, the requirements are different — you might need to timestamp data and flag gaps in the recorded stream.

The proprietary protocol with a simple checksum can detect corruption but not necessarily loss — a dropped packet is simply absent, and the receiver can't distinguish between "no data sent" and "data lost." The minimum viable approach would be to add sequence numbers to each packet so the receiver can detect gaps, and a timeout mechanism so the display unit can indicate when data hasn't been received within an expected interval.

However, I'd push back on a purely proprietary approach unless there's a strong justification. Standard protocols like Bluetooth Low Energy with acknowledged writes, or a UDP-based approach with sequence numbers and a heartbeat, provide well-understood mechanisms for detecting loss. The trade-off is complexity versus control — a proprietary protocol might be simpler to implement but harder to verify, and you lose the ecosystem of testing tools and established patterns that come with standard protocols.

I'd also consider the IEC 60601-1-2 implications. Wireless links in medical devices need to demonstrate immunity to interference and coexistence with other wireless devices in the environment. A proprietary protocol may not have the same level of interference mitigation as a standard protocol with frequency hopping or adaptive retransmission.

My approach would be to define the clinical requirements first — maximum acceptable data gap, required time-to-indicate-staleness, and whether data integrity checking needs to be end-to-end or per-hop — then evaluate protocol options against those requirements. If the proprietary protocol meets the requirements and the team can demonstrate that through verification, it's viable. But I'd want to see a clear risk assessment showing why a standard protocol isn't suitable.

**Possible follow-ups:** How would you verify that the staleness indication is timely and accurate under real-world wireless conditions? What if the proprietary protocol is already implemented and working in a predicate device — how would that affect your evaluation?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The shared ADC and multiplexer introduces a specific failure mode: crosstalk or settling-time issues between channels. When the multiplexer switches from the pressure channel to the temperature channel, the ADC needs sufficient settling time before sampling, or the reading will be contaminated by residual charge from the previous channel. This is particularly relevant if the two sensors have very different output impedances or signal levels.

I'd structure the test plan around three layers: individual channel accuracy, cross-channel isolation, and simultaneous accuracy under realistic operating conditions.

For individual channel accuracy, I'd test each channel against a reference standard across the full specified range and temperature range of the device. This verifies the basic calibration and linearity of each sensor path independently.

For cross-channel isolation, I'd apply a known stimulus to one channel while monitoring the other. The critical test is to apply a full-scale signal on the pressure channel while measuring a low-level signal on the temperature channel, and vice versa. This reveals settling-time issues, charge injection from the multiplexer, or coupling through the shared ADC input. I'd also test at different multiplexer switching rates to find any frequency-dependent effects.

For simultaneous accuracy, I'd need to verify that the device meets its accuracy specification when both channels are actively measuring — not just when one is being tested while the other is idle. This requires test equipment that can provide controlled temperature and pressure simultaneously, which may mean using a environmental chamber with a pressure port, or a calibrated pressure source inside a temperature-controlled enclosure.

I'd also consider the timing aspects. If the device reports temperature and pressure at different rates, or if the multiplexer gives one channel priority, I need to verify that the measurement timing doesn't introduce errors. For example, if the pressure channel is sampled more frequently, does the temperature reading still meet its accuracy specification?

Finally, I'd include a test for the multiplexer switching sequence itself — verifying that the firmware correctly sequences the channels, allows adequate settling time, and doesn't accidentally read the wrong channel due to a configuration error.

**Possible follow-ups:** How would you determine the required settling time between channel switches, and how would you verify that the firmware implements it correctly? What if the two sensors have significantly different output impedances — how would that affect your test approach?

---

## Q4: You're leading a project where a field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that potentially involves both patient safety and regulatory obligations, so I'd approach it with a structured investigation following the principles of ISO 14971 and typical corrective and preventive action (CAPA) processes.

First, I'd ensure patient safety is addressed immediately. If there's evidence of a pattern — multiple patients affected — I'd recommend a field action assessment, which might include quarantining remaining inventory, issuing clinical guidance, or recalling the product, depending on the severity of the irritation. This decision would involve the full cross-functional team including quality, regulatory, and clinical affairs.

For the investigation itself, I'd start by gathering all available data: the number of complaints, the severity and nature of the irritation, the patient population affected, and any common factors (lot numbers, manufacturing dates, usage patterns, cleaning procedures). I'd also review the complaint records to determine if this is truly a new issue or if there were earlier, less severe reports that weren't recognized as a pattern.

The technical investigation would branch into several hypotheses. Material-related causes would include a change in the silicone formulation by the supplier, a contamination issue during manufacturing, or a problem with the curing process. Design-related causes might include the pad geometry creating pressure points or occlusion, or an interaction between the pad material and cleaning agents used in the clinical environment. Usage-related causes could include extended wear time beyond what the device was designed for, or a change in how the device is being used in the field.

I'd want to obtain affected and unaffected samples for analysis — comparing the silicone material properties, checking for residual chemicals, and reviewing the manufacturing records for any process deviations. I'd also review the biocompatibility testing that was done during development to understand what was originally validated and whether the current material matches what was tested.

The corrective action would depend on the root cause. If it's a supplier material change, the fix might be reverting to the original formulation or qualifying a new supplier. If it's a design issue, it might require a pad redesign with different material or geometry. If it's a usage issue, it might be a labeling change or clinical education.

Throughout this process, I'd be documenting everything for the design history file and coordinating with regulatory affairs to determine if a field safety corrective action (FSCA) or regulatory notification is required. The key is to balance thoroughness with speed — patient safety is the priority, but I also need to avoid overreacting to what might be an isolated issue.

**Possible follow-ups:** How would you determine whether this requires a field safety corrective action (FSCA) versus a less urgent corrective action? What if the investigation reveals that the silicone material formulation was changed by the supplier without notification — how would you handle that?

---

## Q5: How would you approach verifying that a medical device's firmware meets IEC 62304 requirements for a Class C software safety classification?

**Answer:** Class C is the highest software safety classification under IEC 62304, reserved for software that can contribute to a hazardous situation. The verification approach needs to be commensurate with that risk level, and I'd structure it around the standard's key requirements: software development planning, requirements analysis, architectural design, unit implementation and verification, integration and integration testing, and system testing.

The foundation is traceability. Every software requirement must trace to a system requirement that traces to a risk control measure or a clinical/user need. Every unit, integration test, and system test must trace back to software requirements. If there's a gap in traceability, that's a finding that needs resolution before the software can be considered complete.

For unit-level verification, I'd expect a combination of code reviews and unit testing. For Class C, the standard requires that each software unit be verified — typically through code reviews, static analysis, and unit tests that exercise both normal and abnormal inputs. I'd want to see evidence that boundary conditions, error handling, and exception paths are tested, not just the happy path.

At the integration level, I'd focus on the interfaces between software units and between software and hardware. This is where timing issues, resource contention, and communication protocol errors often surface. I'd expect integration tests that verify the software components work together correctly under both normal and fault conditions.

For system-level testing, the verification needs to demonstrate that the software, as integrated into the complete device, meets its requirements and that risk control measures implemented in software are effective. This includes testing under abnormal conditions — sensor failures, communication errors, power interruptions — to verify the software responds safely.

Beyond the testing itself, I'd verify the supporting processes: configuration management (can you reproduce the exact software version that was tested?), problem resolution (are all known defects documented with risk assessments?), and change control (are changes properly assessed for impact and re-verified?).

One aspect that's often underestimated is the maintenance phase. IEC 62304 applies throughout the software lifecycle, so I'd verify that there's a process for handling software changes after release, including regression testing and impact assessment for each change.

I'd also want to see the software architecture documentation — for Class C, the standard requires a detailed architecture description showing how the software is decomposed into units and how data flows between them. This isn't just documentation for its own sake; it's the basis for the traceability and for assessing the impact of any change.

**Possible follow-ups:** How would you determine whether a specific software component should be classified as Class A, B, or C under IEC 62304? What would you do if you discovered that a software unit that should have been classified as Class C was developed and verified as Class B?