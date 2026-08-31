# tools — Day 41

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** For a medical device, the build process itself becomes part of the design history file, so reproducibility and traceability are the primary goals. I'd start by establishing a single source of truth for the toolchain — pinning the exact Zephyr SDK version, the west workspace manifest, and the compiler version, ideally using a container or a dedicated build machine so that "it works on my machine" is eliminated as a variable. The west manifest file is critical here because it locks the Zephyr kernel version and all module revisions to specific commits.

Next, I'd define a formal release procedure that produces a complete artifact set: the firmware binary, the ELF file with debug symbols, a checksum manifest, the exact source tree state (git commit hash), the toolchain versions, and the build configuration (prj.conf, device tree overlays, and any Kconfig fragments). For regulatory traceability, I'd tag the release in version control and generate a build report that documents all of this. The build should be scripted end-to-end — no manual steps that could introduce variation.

I'd also separate the production build from development builds. The production build should have deterministic settings: optimization level fixed, debug information stripped or retained as a separate artifact, and any test or debug features compiled out via Kconfig. The build script should fail on warnings, and ideally the same script is run in CI so there's an automated record of every build attempt. Finally, I'd archive the artifacts in a controlled location with access logging, since the regulatory body may want to trace exactly what was shipped to what was built.

**Possible follow-ups:**
- How would you handle the case where a field-returned device needs to be matched to a specific firmware build?
- What role would signed firmware images play in this process, and where would key management fit?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** I'd approach this as a systematic isolation problem. First, I'd set up the oscilloscope to capture both domains simultaneously — using a high-impedance or active probe on the analog sensor output and a standard passive probe with a ground spring (not a long ground lead) on the switching node of the regulator. The goal is to correlate the noise on the sensor output with the switching events. I'd trigger on the switching node's rising edge and average multiple acquisitions to extract the noise signature that's coherent with the switching frequency, separating it from random noise.

To determine the coupling path, I'd run a series of controlled experiments. For conducted coupling, I'd check the power supply rails — probe the regulator output and the sensor's supply pin with the same trigger, looking for ripple that correlates with the switching events. If the noise appears on the supply rail, I'd add a low-ESR capacitor or a ferrite bead temporarily to see if the sensor noise changes. For radiated coupling, I'd use a near-field probe connected to the oscilloscope's spectrum analysis capability, scanning over the regulator's inductor and the sensor's traces to find the radiating element. For ground-plane coupling, I'd measure the voltage difference between two ground points on the board using a differential probe — if there's a measurable ground bounce at the switching frequency, that's a strong indicator.

The key discriminator is time alignment. If the noise on the sensor output appears simultaneously with the switching transient, it's likely radiated or through the ground plane. If it appears after a delay consistent with the power supply's propagation, it's likely conducted. I'd also try disabling the regulator and powering the sensor from a clean bench supply — if the noise disappears, it's coupled from the regulator; if it persists, it's coming from elsewhere.

**Possible follow-ups:**
- How would you use the oscilloscope's FFT function to help identify the coupling mechanism?
- What modifications would you try first if you determined the coupling was through the ground plane?

---

## Q3: How would you approach setting up a hierarchical schematic design in Altium Designer for a complex mixed-signal medical device that has multiple identical sensor channels, and how would you ensure that design changes propagate correctly to all instances?

**Answer:** Hierarchical design is the right approach for repeated channels, and Altium's multi-channel feature is specifically designed for this. I'd start by creating a single "sensor front-end" sheet that contains the complete signal chain — the sensor connector, conditioning circuitry, ADC, and any local filtering. I'd define the sheet as a device sheet or a multi-channel block, and then instantiate it multiple times in the top-level schematic. The key is to use the Repeat() directive properly so Altium generates unique designators for each instance (e.g., U1A, U1B, U1C) automatically.

For design changes to propagate correctly, the critical rule is that all channel-specific components must live inside the repeated sheet, and all differences between channels must be handled through parameters or variants, not by editing individual instances. If a channel needs a different resistor value, I'd use a parameter passed into the sheet rather than editing one instance directly — editing an instance breaks the "single source" property and creates a maintenance nightmare. I'd also use Altium's project variants if channels need to be populated differently for different product configurations.

Before committing to the multi-channel approach, I'd verify the net naming and cross-sheet references are set up correctly — Altium has specific rules for how ports and net labels work across repeated sheets. I'd run the ERC early and often, and I'd use the "Update PCB" process to confirm that all instances appear correctly in the layout. For review purposes, I'd generate a cross-reference report that shows which components belong to which channel, making it easy for a reviewer to verify that all instances are identical.

**Possible follow-ups:**
- How would you handle a situation where one channel needs a slightly different filter cutoff frequency than the others?
- What are the common pitfalls when using the Repeat() directive that you'd watch out for?

---

## Q4: How would you approach using a logic analyzer to debug a CAN-FD bus where a node intermittently enters bus-off state after several hours of operation, but only when the system is under vibration?

**Answer:** This is a classic intermittent fault that requires correlating multiple signals over a long time window. I'd set up the logic analyzer to capture the CAN-FD bus lines (CANH and CANL, or the digital RX/TX signals at the transceiver) along with a few additional channels — the microcontroller's error status pin if available, a vibration sensor or accelerometer, and possibly the power supply rail. The goal is to capture the events leading up to the bus-off condition, not just the bus-off itself.

I'd configure the logic analyzer with a deep memory buffer and a pre-trigger capture so I can see what happened in the seconds before the bus-off. The CAN protocol decoder would be essential — I'd look for error frames, bit errors, stuff errors, or CRC errors that precede the bus-off. The key question is whether the errors are localized to one node (suggesting a hardware issue on that node) or distributed across the bus (suggesting a physical layer problem like a loose connector or cable issue).

Since the failure is vibration-related, I'd look for a correlation between the vibration signal and the error frames. If errors occur only during vibration events, I'd suspect a mechanical issue — a loose connector, a cracked solder joint, or a harness that's rubbing against something. I'd also check the bit timing: if the transceiver's clock is drifting under vibration (e.g., a crystal that's sensitive to mechanical stress), the bit sampling point could shift, causing bit errors. I'd use the logic analyzer's timing measurements to check the actual bit rate and compare it to the configured rate.

If the logic analyzer can't capture long enough, I'd add a CAN bus analyzer with error logging capability and run it for extended periods, but the logic analyzer gives the best time-correlated view of the actual bus signals.

**Possible follow-ups:**
- How would you distinguish between a transceiver issue and a microcontroller issue in this scenario?
- What would you do if the failure doesn't reproduce with the logic analyzer connected?

---

## Q5: (Behavioral) Imagine you are leading a project where a junior engineer has been tasked with setting up the automated firmware test environment for a medical device. On the day before a critical regression test run, you discover that the engineer has configured the test script to skip the safety-critical test cases because they were failing intermittently, and the engineer is confident this is acceptable because "the failures are just timing issues in the test harness, not real bugs." The test results will be used for a regulatory submission milestone. How would you handle this situation?

**Answer:** This is a serious situation because it touches on both engineering integrity and regulatory compliance. My first priority is to stop the test run from proceeding with the modified script — I would not allow a regression test for a regulatory milestone to run with safety-critical cases skipped, regardless of the engineer's confidence. I'd immediately inform the engineer that the test run is on hold and that we need to discuss the situation.

I'd then sit down with the engineer to understand their reasoning. It's possible they're right that the failures are test-harness artifacts, but that's a hypothesis that needs to be proven, not assumed. I'd ask them to show me the specific failures and the evidence that they're harness-related. If the failures are intermittent, that's even more reason to investigate — intermittent failures in safety-critical tests are exactly the kind of thing that needs root-cause analysis, not skipping. I'd also point out that for a regulatory submission, the test results need to be complete and accurate; a test run with skipped cases would be a red flag in an audit.

The immediate action would be to restore the full test suite and run it, accepting that some cases may fail. If the failures are real, we need to know that now, not after the submission. I'd then lead a root-cause investigation into the intermittent failures, using the test logs and any debug output to determine whether it's a harness issue or a firmware issue. If it turns out to be a harness issue, we fix the harness and document the fix. If it's a firmware issue, we've caught it before the submission — which is exactly what regression testing is for.

I'd also use this as a coaching moment. The engineer's instinct to make the tests pass is understandable, but skipping tests to get a green run is never acceptable, especially in a regulated environment. I'd explain the regulatory context — that the test results are evidence, and manipulating evidence, even unintentionally, undermines the entire submission. I'd document the incident and the resolution in the project records, because transparency is critical in a regulated environment.

**Possible follow-ups:**
- How would you handle this if the engineer had already run the test and reported the results to management before you discovered the issue?
- What would you do to prevent this kind of situation from happening again in the future?