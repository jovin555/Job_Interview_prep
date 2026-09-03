# medical-devices — Day 44

## Q1: How would you approach verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during a firmware update, given that the device must remain safe and functional if the update fails?

**Answer:** This is fundamentally about designing for update resilience and then verifying that design through fault injection. First, I'd want to understand the update architecture: is there a dual-bank or A/B partition scheme, a bootloader with a fallback image, or a recovery mode? The verification strategy depends heavily on the architecture in place.

For the test approach, I'd start by mapping the failure modes: power loss at various points during the write sequence, corrupted image data (bit flips, truncated files), interrupted erase operations, and partial writes to the metadata or header region. Each of these needs to be injected deliberately during testing.

The key principle is that the device must always have a known-good boot path. If the update mechanism uses a flag or pointer to select the active image, I'd verify that the flag is only updated after the new image passes integrity checks (CRC or signature verification). I'd test that a corrupted image is rejected and the previous image remains bootable.

For the actual test strategy, I'd use fault injection at multiple levels: corrupting the image file before transfer, interrupting power at specific points during the write (using a controllable power supply), and directly manipulating the flash contents via a debug interface to simulate partial writes. Each test case should verify not just that the device boots, but that it boots into the correct image and that the failed update is properly reported or logged.

I'd also verify the behavior after multiple consecutive failed update attempts — the device should not enter a state where it repeatedly attempts to apply a bad image or where the recovery mechanism itself becomes exhausted. Finally, I'd confirm that any user-visible indication of update failure is clear and that the device returns to normal operation without requiring service intervention.

**Possible follow-ups:** How would you verify that the bootloader itself is protected against corruption? What criteria would you use to determine whether a failed update should trigger an automatic rollback versus requiring user intervention?

---

## Q2: How would you approach selecting materials for a patient-contacting sensor housing that must meet both biocompatibility (ISO 10993) and mechanical durability requirements?

**Answer:** This requires balancing two distinct sets of requirements that sometimes conflict. Biocompatibility is about the biological response to material contact, while mechanical durability is about the material's ability to withstand the physical demands of use — flexing, cleaning, temperature cycling, and so on.

My approach would start with a clear definition of the contact duration and type, since ISO 10993 testing requirements scale with contact duration (limited, prolonged, or long-term) and contact type (surface, external communicating, or implant). A sensor housing that contacts skin for days at a time has different requirements than one that contacts mucosal tissue briefly.

For material selection, I'd create a shortlist of candidates that have established biocompatibility data — materials already used in similar approved devices are a strong starting point because they come with existing biological evaluation data. Common candidates include medical-grade silicones, certain polycarbonates, ABS, or stainless steels, depending on the application.

The key is to consider the entire lifecycle: the material must maintain biocompatibility after exposure to cleaning agents, sterilization methods, and environmental conditions. A material that passes ISO 10993 testing in its virgin state might fail after repeated exposure to disinfectants that cause degradation or leaching. So I'd want to see biocompatibility data on aged or conditioned samples, not just fresh material.

For mechanical durability, I'd evaluate the specific stresses the housing will face — flexural fatigue if it bends, impact resistance if dropped, abrasion resistance if it contacts skin or clothing. I'd also consider the manufacturing process: can the material be molded or formed to the required tolerances without introducing defects that compromise either biocompatibility or mechanical performance?

The practical approach is to work with material suppliers who can provide both biocompatibility documentation and mechanical property data, and to design a verification plan that tests the finished part — not just the raw material — under simulated use conditions. This might include accelerated aging, cleaning cycle testing, and mechanical stress testing, followed by biocompatibility testing on the conditioned parts if there's any question about material stability.

**Possible follow-ups:** How would you handle a situation where the most biocompatible material has insufficient mechanical durability for the application? What role does the manufacturing process play in biocompatibility, and how would you verify that?

---

## Q3: You're the lead engineer on a medical device project. During a design review, the clinical team requests a change that would improve usability but would require a significant hardware revision and delay the regulatory submission by three months. How would you evaluate and respond to this request?

**Answer:** The first step is to understand the request thoroughly rather than reacting to the schedule impact. I'd ask the clinical team to articulate the specific usability problem they're trying to solve, the patient safety implications if it's not addressed, and the evidence behind their request — is this based on observed user errors, workflow inefficiencies, or hypothetical concerns?

With that context, I'd evaluate the request against several criteria. The most important is patient safety: does the current design create a risk of user error that could harm a patient? If so, this isn't really optional — it's a risk control measure that needs to be addressed regardless of schedule. If it's purely a convenience or preference issue, the risk assessment is different.

I'd also consider the regulatory implications of the change. A hardware revision that affects the device's safety-related functions would likely require additional verification testing and potentially a new regulatory submission or a supplement to the existing one. But I'd also consider the cost of not making the change: if the usability issue leads to field complaints, post-market surveillance findings, or worse, patient harm, the regulatory and reputational cost could be far higher than a three-month delay.

My approach would be to facilitate a structured discussion with the clinical team, regulatory affairs, and quality assurance. I'd ask whether the change can be scoped to a subset of the hardware — for example, can it be implemented in a future revision while the current design proceeds? Can a software workaround or labeling change mitigate the usability issue in the interim? Is there a way to validate the proposed change with a small user study before committing to the full hardware revision?

If the change is genuinely necessary for safety, I'd advocate for making it and adjusting the schedule accordingly, while working with regulatory affairs to understand whether the submission timeline can be partially decoupled — for example, submitting the current design while preparing the revision as a follow-up. If the change is desirable but not safety-critical, I'd propose documenting it as a design input for the next revision while proceeding with the current timeline.

The key is to avoid treating this as a binary decision between "accept the delay" and "reject the request." Instead, I'd look for options that address the clinical concern while managing the regulatory and schedule impact.

**Possible follow-ups:** How would you determine whether a usability issue rises to the level of a patient safety concern? What role should human factors engineering and usability testing play in evaluating this type of request?

---

## Q4: How would you approach developing a software test plan for a medical device that uses machine learning for diagnostic decision support, given that IEC 62304 doesn't explicitly address AI/ML?

**Answer:** This is an area where the regulatory landscape is still evolving, so the approach needs to combine the rigor of IEC 62304 with additional considerations specific to machine learning. The fundamental challenge is that ML models are typically developed through training on datasets rather than being explicitly programmed, which means traditional requirements-based testing doesn't map cleanly to the model's behavior.

My starting point would be to apply IEC 62304's risk-based framework to the extent possible. The software safety classification still applies — a diagnostic decision support system that influences clinical decisions would likely be Class B or C depending on the severity of harm if the output is wrong. The software development lifecycle requirements — documentation, configuration management, verification, and validation — still apply to the surrounding software infrastructure.

For the ML component specifically, I'd structure the test plan around several layers. First, the training and validation data: I'd want to verify that the dataset is representative of the intended patient population, that it's properly labeled, and that there's no unintended bias. This isn't a traditional software test, but it's critical to the model's performance.

Second, model performance testing: this goes beyond traditional accuracy metrics. I'd want to see performance characterized across patient subgroups, across the range of input signal quality the device might encounter, and across the boundary conditions where the model's confidence is lowest. Confusion matrices, precision-recall curves, and calibration analysis are more informative than a single accuracy number.

Third, the integration between the ML model and the surrounding software: how does the system handle model outputs that are uncertain or contradictory? How does it behave when the input data is corrupted or out of distribution? These are testable behaviors that fit within the IEC 62304 framework.

Fourth, I'd address the challenge of test oracles. For traditional software, you have a specification that defines expected behavior. For ML, the "specification" is statistical — the model is expected to perform within certain bounds on unseen data. So the test plan needs to include a held-out test set that wasn't used in training, and the acceptance criteria should be defined in terms of performance bounds on that test set.

Finally, I'd consider the post-market phase. ML models can degrade over time if the deployment environment shifts from the training distribution. The test plan should include provisions for ongoing monitoring of model performance in the field and criteria for when the model needs to be retrained or recalled.

The honest answer is that this is an area of active regulatory discussion, so I'd also engage with notified bodies or regulatory consultants early to understand current expectations and to document the rationale behind the testing approach in the design history file.

**Possible follow-ups:** How would you define acceptance criteria for an ML model when there's no single "correct" answer for many inputs? How would you handle the challenge of verifying that the model doesn't exhibit unintended bias across patient demographics?

---

## Q5: How would you approach designing a test strategy for verifying that a medical device's wireless communication (e.g., Bluetooth Low Energy) meets both the IEC 60601-1-2 immunity requirements and the wireless coexistence requirements for a hospital environment?

**Answer:** This requires addressing two distinct but related sets of concerns: the device's immunity to external electromagnetic interference (as defined by IEC 60601-1-2) and its ability to operate reliably in the presence of other wireless devices that share the spectrum (coexistence).

For the IEC 60601-1-2 immunity side, the wireless module is tested as part of the overall device. The key question is whether the wireless communication is safety-related — for example, if the device transmits physiological data to a monitoring station, loss of that data could have clinical consequences. If so, the immunity testing needs to verify not just that the device survives the test, but that the wireless link maintains its required performance during exposure to the test fields.

I'd structure the test strategy around the specific immunity tests in IEC 60601-1-2: radiated RF, conducted RF, ESD, and magnetic fields. For each test, I'd define pass criteria that go beyond basic functionality — for example, measuring packet error rate or data latency during the RF exposure rather than just confirming the device doesn't reset. This requires setting up the wireless link to a companion device and monitoring link quality throughout the immunity test.

For coexistence, the concern is different: the device must operate reliably in a hospital environment with Wi-Fi, other Bluetooth devices, ZigBee, and potentially other wireless systems. The test strategy would include both laboratory testing and, ideally, real-world assessment. In the lab, I'd test the device against representative interferers — for example, a Wi-Fi network operating on adjacent channels, multiple Bluetooth devices, and other common hospital wireless systems. The key metrics are packet error rate, latency, and reconnection time after interference.

I'd also consider the protocol-level mitigations: does the Bluetooth stack implement adaptive frequency hopping, retransmission, and channel assessment? How does the device handle a congested spectrum? These features need to be verified under controlled interference conditions.

One important aspect is defining what "acceptable performance" means. For a monitoring device, occasional packet loss might be acceptable if the device can detect and indicate data gaps, but prolonged loss of connectivity would be a safety issue. The test strategy should verify that the device's behavior under interference matches the risk assessment — for example, if the risk analysis says the device must alert the user within X seconds of losing the wireless link, the test should verify that alert behavior under interference conditions.

Finally, I'd coordinate with the radio regulatory testing (FCC, ISED, or CE) since the wireless module must also meet spectrum regulations. The immunity and coexistence testing is complementary to the radio certification, and the test plans should be coordinated to avoid redundant testing while ensuring complete coverage.

**Possible follow-ups:** How would you define the performance criteria for the wireless link during immunity testing — what level of packet loss or latency would be acceptable? How would you approach testing coexistence in a real hospital environment given the variability of wireless conditions?