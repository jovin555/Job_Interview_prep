# medical-devices — Day 39

## Q1: How would you approach verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during a firmware update, given that the device must remain safe and functional if the update fails?

**Answer:** This is fundamentally about designing for update resilience and then verifying that design through targeted testing. From a design perspective, I'd expect the firmware architecture to include several layers of protection: a bootloader that is separate from the application image, at least two image slots (A/B partitioning) so a failed update doesn't brick the device, and a mechanism to mark an image as "valid" only after it boots successfully and passes self-checks. The bootloader should also have a recovery path — for example, falling back to the last-known-good image or entering a recovery mode that accepts a new update.

For verification, I'd structure the test strategy around fault injection at the memory level. This means simulating corruption at different points in the update process: corrupted header, corrupted payload, corrupted checksum, and corruption that occurs mid-write. The key is to verify not just that the device detects the corruption, but that it behaves safely afterward — it should revert to the previous image, maintain patient monitoring if that's the device's function, and clearly indicate that the update failed rather than silently continuing with a compromised image.

I'd also test the edge cases: power loss during the update, update interrupted by a reset, and storage that becomes full mid-update. The device should handle all of these without entering an unsafe state. For a medical device, the verification plan would need to document the expected behavior for each failure mode and tie it back to the risk analysis — for example, if a failed update could result in the device not monitoring a patient, that's a hazard that needs a risk control measure and corresponding verification evidence.

**Possible follow-ups:** How would you verify that the bootloader itself is protected against corruption? What criteria would you use to determine whether a device should revert to the previous image versus entering a recovery mode?

---

## Q2: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using a proprietary protocol with a simple checksum, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** The core issue here is that a simple checksum detects corruption but doesn't address the clinical requirement of detecting data loss or staleness. These are different problems. A checksum tells you that the data you received is intact, but it doesn't tell you whether you're missing data that was never received. The clinical requirement is about data continuity and freshness — the display needs to know whether the data it's showing reflects the current state of the patient.

I'd approach this by separating the concerns. The protocol needs three things: error detection (which the checksum provides), sequence numbering or timestamps (to detect gaps in the data stream), and a freshness indicator (such as a maximum age threshold for displayed data). The sequence number is the critical addition — without it, the display unit can't distinguish between "the last packet I received was valid" and "the last packet I received is the most recent data." The staleness indication would then be implemented on the display side: if no valid packet with a newer sequence number arrives within a defined interval, the display marks the data as stale.

Rather than debating the protocol in the abstract, I'd frame the discussion around the clinical use case. What's the maximum acceptable delay between data acquisition and display? What happens if data is lost — does the clinician need to know immediately, or is it acceptable to show a gap? These requirements should drive the protocol design. If the proprietary protocol can be extended with sequence numbers and a timeout mechanism, that might be acceptable. If not, a standard protocol with built-in acknowledgment or sequence tracking might be more appropriate. The key is that the clinical requirement — detectable data loss and staleness indication — is non-negotiable, and the protocol choice must serve that requirement.

**Possible follow-ups:** How would you determine the maximum acceptable data staleness for this device? What testing would you do to verify that the staleness indication works correctly under real-world wireless conditions?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The shared ADC and multiplexer introduces a coupling between the two measurement channels that wouldn't exist if they were independent. The verification plan needs to address both the individual accuracy of each channel and the interaction between them.

First, I'd establish the accuracy requirements for each parameter independently — what's the allowable error for temperature, and what's the allowable error for pressure? These come from the clinical requirements and are typically documented in the design inputs. Then I'd design tests that verify each channel meets its specification when the other channel is in a known state.

The interaction testing is where this gets interesting. The multiplexer means that the ADC is time-shared, so I'd want to test scenarios where both sensors are active and producing signals simultaneously. Key concerns include: settling time after switching between channels (does the ADC have enough time to settle before sampling?), crosstalk between channels (does a large signal on one channel affect the reading on the other?), and the effect of multiplexer switching on the ADC's reference or input circuitry.

I'd structure the test plan in layers. First, static accuracy tests: known temperature with known pressure, verifying each channel independently. Second, dynamic interaction tests: varying one parameter while holding the other constant, and verifying that the measured value of the constant parameter doesn't drift. Third, worst-case tests: both parameters at extremes simultaneously, and both parameters changing rapidly. Finally, I'd include a test that mimics the actual clinical use pattern — for example, if the device measures temperature continuously and pressure periodically, I'd verify that the periodic pressure measurement doesn't introduce artifacts into the temperature reading.

The test equipment would need to provide independent, traceable references for both parameters — for example, a calibrated temperature source and a calibrated pressure source that can be controlled independently. The test plan should also document the expected accuracy for each test point and the acceptance criteria, so that failures can be clearly distinguished from test setup issues.

**Possible follow-ups:** How would you determine the settling time requirements for the multiplexer? What would you do if the interaction testing revealed crosstalk between the channels that exceeded the accuracy budget?

---

## Q4: You're leading a project where a field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that touches on both patient safety and regulatory obligations, so I'd approach it with a structured investigation that follows the principles of a formal corrective action process.

First, I'd establish the facts. How many patients are affected, and what's the severity of the irritation? Is this a new issue or has it been occurring since the product launched? Are there common factors among the affected patients — skin type, duration of contact, concurrent medications, or environmental conditions? I'd want to gather the clinical details from the field, including photographs if available, and any information about how the device was used.

In parallel, I'd begin the technical investigation. The silicone material itself would need to be examined — was there a change in the material formulation, the curing process, or the supplier? I'd review the biocompatibility testing that was done during development (ISO 10993) to understand what was tested and whether the current material matches what was tested. I'd also consider whether the issue could be mechanical rather than chemical — for example, the pad's surface texture or adhesive causing friction irritation, or the pad trapping moisture against the skin.

The investigation would need to determine whether this is a design issue, a manufacturing issue, or a use issue. If the material formulation changed, that points to a supplier or manufacturing problem. If the material is unchanged but the complaint rate is increasing, it could be a use issue or a change in the patient population. I'd also check whether there have been similar complaints in the past that were handled differently — this is important for understanding whether the issue is new or was previously underreported.

Once the root cause is established, the corrective action would depend on the findings. This could range from a supplier corrective action for material changes, to a design change for the pad geometry, to updated instructions for use. Given the patient safety aspect, I'd also assess whether this requires a field safety corrective action — for example, recalling affected lots or issuing a safety notice to users. The regulatory reporting requirements would need to be considered, as skin irritation from a patient-contacting device is a reportable adverse event in most jurisdictions.

Throughout this process, I'd keep the investigation team focused on facts rather than assumptions, document every step for the design history file and regulatory records, and communicate transparently with the clinical users who reported the issue.

**Possible follow-ups:** How would you determine whether this requires a field safety corrective action versus a less urgent corrective action? What would you do if the investigation revealed that the silicone material was changed by the supplier without your organization's approval?

---

## Q5: How would you approach verifying that a medical device's firmware meets IEC 62304 requirements for a Class C software safety classification?

**Answer:** Class C is the highest software safety classification under IEC 62304, reserved for software that can contribute to a hazardous situation. The verification approach needs to be comprehensive and documented, with clear traceability from requirements through implementation to testing.

The foundation is the software development plan, which must describe the development lifecycle, the verification activities, and the acceptance criteria. For Class C, the standard requires more rigorous documentation and more extensive testing than for Class B or Class A. I'd start by confirming that the software requirements specification is complete and unambiguous, with each requirement traceable to a system-level requirement and to the risk analysis. Every safety-related requirement needs to be identified as such, and the verification activities need to demonstrate that each safety-related requirement is correctly implemented.

For the verification itself, I'd structure it in layers. Unit testing verifies that individual functions or modules behave correctly — for Class C, this typically requires a high level of coverage, including statement coverage and branch coverage, with the coverage measured and documented. Integration testing verifies that modules interact correctly, particularly at interfaces where data is passed between safety-critical and non-safety-critical components. System testing verifies that the software as a whole meets its requirements when running on the target hardware.

Beyond functional testing, Class C requires additional verification activities. Static analysis should be performed to identify potential defects that might not be caught by dynamic testing — things like uninitialized variables, buffer overflows, or race conditions. The standard also requires that the software architecture be designed to minimize the risk of errors — for example, by partitioning safety-critical functions from non-critical functions, and by using defensive programming techniques.

The verification evidence needs to be documented in a way that a reviewer can follow. Each test case should reference the requirement it verifies, the expected result, the actual result, and the pass/fail determination. Defects found during testing need to be tracked to closure, with an analysis of whether the defect affects other parts of the software. Finally, the verification activities need to be completed before the software is released, and the release criteria should be defined in advance — for example, zero open critical defects, all safety-related requirements verified, and all verification activities documented.

For a Class C device, the verification effort is substantial, but it's proportionate to the risk. The goal is to provide objective evidence that the software is safe and effective for its intended use, and that evidence needs to withstand scrutiny from both internal reviewers and regulatory auditors.

**Possible follow-ups:** How would you determine the appropriate level of test coverage for Class C software? How would you handle a situation where a safety-related requirement is found to be untestable during verification?