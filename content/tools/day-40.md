# tools — Day 40

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** For a medical device, the build process itself becomes part of the design history file, so reproducibility and traceability are the primary goals. I'd start by defining a single source of truth for the build: a version-controlled Zephyr workspace using west, with the manifest file pinned to specific Zephyr revision and all application code in the same repository. The manifest should reference exact commit hashes, not branches, so that a build performed six months later produces identical output.

For the build itself, I'd use a containerized build environment — Docker or a similar approach — to ensure that the toolchain, Zephyr version, and host dependencies are frozen. The container image would be versioned and stored alongside the project. This eliminates the "works on my machine" problem and makes the build environment itself auditable.

The build script would generate a manifest file as part of the output, containing: the git commit hashes of the application and Zephyr, the container image hash, the west manifest content, the exact CMake configuration, and a checksum of the resulting binary. This manifest gets stored alongside the firmware artifact. I'd also configure the build to embed build metadata into the firmware itself — a version string, build timestamp, and git hash — readable at runtime.

For release management, I'd use signed git tags for each release candidate, and the release process would require that the build is performed from a clean checkout of that tag. The final binary would be hashed and the hash recorded in the release documentation. I'd also set up a CI pipeline that automatically builds from any tagged commit and archives the artifacts with their manifests, so there's a clear chain from source to binary.

**Possible follow-ups:**
- How would you handle the case where a bug is found in a released version and you need to rebuild it months later, but the toolchain has moved on?
- What build metadata would you consider essential to embed in the firmware itself versus keeping only in the external manifest?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** This is a classic mixed-signal debugging scenario. I'd start by establishing a baseline: measure the analog sensor output with the switching regulator disabled (powered from a bench supply instead) to see the noise floor. Then enable the regulator and measure the same point to quantify the added noise. This tells you the magnitude of the problem before you start chasing mechanisms.

To determine the coupling path, I'd use a systematic approach. First, for conducted coupling: probe the power rail at the sensor's supply pin with the oscilloscope using a short ground spring (not the long ground lead, which acts as an antenna). Look for switching-frequency ripple and its harmonics. Also probe the ground at the sensor and at the regulator — if you see switching noise on the ground at the sensor location, that suggests ground-plane coupling or shared return paths.

For radiated coupling: use a near-field probe connected to the oscilloscope (or spectrum analyzer) and scan over the sensor's signal traces and components while the regulator is running. If you find hot spots of radiated energy near the sensor input, that points to radiated coupling. You can also try shielding the sensor area with a grounded copper foil — if the noise drops significantly, radiation is a major contributor.

For ground-plane coupling specifically: measure the voltage difference between two ground points — one near the regulator and one near the sensor — using a differential probe. If there's significant high-frequency voltage between these points, the ground plane has impedance issues, likely from a poor return path or a split in the plane. I'd also check whether the analog and digital grounds are connected at multiple points or if there's a slot or gap in the plane under the signal path.

A useful discriminating test: if the noise is primarily at the switching frequency and its harmonics, it's likely conducted or ground-coupled. If the noise is broadband or appears at frequencies not related to the switching frequency, radiation or coupling through the air is more likely. I'd also correlate the noise with the regulator's switching node — trigger the oscilloscope on the switching node and average the sensor output to see the time-correlated coupling.

**Possible follow-ups:**
- How would you distinguish between noise coupling through the ground plane versus through the power distribution network?
- What modifications would you consider to mitigate each type of coupling once identified?

---

## Q3: How would you approach setting up a component library management strategy in KiCad for a medical device project that needs to maintain strict revision control and regulatory traceability, given that KiCad's library format is file-based rather than database-driven?

**Answer:** KiCad's file-based libraries actually work well for revision control if you structure them properly. The key is treating library files as first-class project artifacts with the same rigor as schematics and PCB files. I'd start by creating a dedicated libraries repository (or a libraries folder in the main project repo) with a clear directory structure: separate folders for schematic symbols, footprints, and 3D models, with each component's files grouped together.

For traceability, each component symbol and footprint should have a revision field in its properties, and I'd establish a naming convention that includes the component part number and revision — for example, a symbol named `SENSOR_PRESSURE_ABC123_R2`. The datasheet and any manufacturer documentation would be stored in a linked documents folder, referenced from the symbol properties. This creates an audit trail from the schematic symbol to the physical component.

I'd use git for version control, with the library files tracked alongside the project. Each component change gets a commit message describing what changed and why, referencing the design change notice or engineering change order. For release, I'd tag the library repository and record that tag in the project's release documentation, so you can always reconstruct exactly which library versions were used for a given design release.

For KiCad specifically, I'd configure the project to use the library table (fp-lib-table and sym-lib-table) to point to the version-controlled library paths, rather than copying libraries into each project. This ensures everyone uses the same library version. I'd also run the KiCad ERC and DRC with library checks enabled to catch mismatches between symbols and footprints early.

One additional practice: before any component is used in a design, it should go through a review process — someone other than the creator verifies the symbol pins match the datasheet, the footprint matches the manufacturer's recommended land pattern, and the 3D model is correct. This review is documented in the commit history.

**Possible follow-ups:**
- How would you handle a component that needs to be updated mid-project — for example, a manufacturer changes the package slightly?
- How would you ensure that a designer doesn't accidentally use an unapproved or outdated library component?

---

## Q4: How would you approach setting up a hardware-in-the-loop (HIL) test environment for a medical device that needs to verify firmware behavior against simulated sensor inputs, and what are the key considerations for making the tests meaningful and repeatable?

**Answer:** A HIL environment for a medical device needs to bridge the gap between pure software simulation and full hardware testing. The core idea is to replace real sensors with controllable simulators that can inject known, repeatable signals while the actual firmware runs on the real microcontroller.

I'd start by defining the interface boundary: which signals are simulated and which are real. For a medical device with analog sensors, I'd use a precision DAC or programmable signal generator to produce the sensor output waveforms, feeding them into the same signal-conditioning path the real sensor would use. For digital sensors (I2C, SPI), I'd use a second microcontroller or an FPGA to emulate the sensor's register map and communication protocol. The key is that the firmware cannot tell the difference between the simulated sensor and the real one — it sees the same electrical interface.

The test harness needs to be synchronized with the firmware under test. I'd use a test controller (a PC running Python or a dedicated test script) that orchestrates the scenario: it commands the sensor simulator to produce specific values, triggers the device under test, and captures the firmware's response — either through a debug interface, a test output pin, or the device's own communication interface.

For repeatability, the test environment must be deterministic. This means: fixed power-up sequence, controlled timing of stimulus injection, and no reliance on wall-clock timing in the test scripts. I'd also record all stimulus and response data with timestamps so failures can be reproduced and analyzed.

For a medical device, I'd also build in fault injection capabilities: simulate sensor out-of-range values, open circuits, short circuits, and intermittent communication failures. This is where HIL really shines — you can safely test the firmware's response to conditions that would be difficult or unsafe to create with real sensors. The test results should be logged with pass/fail criteria defined in advance, and the whole setup should be documented so it can be audited as part of the verification evidence.

**Possible follow-ups:**
- How would you verify that the HIL environment itself is correctly simulating the sensor — how do you know the simulation is faithful?
- How would you handle testing the firmware's response to sensor failure modes that are hard to simulate electrically?

---

## Q5: (Behavioral) Imagine you are leading a project where a junior engineer has been tasked with setting up the automated firmware test environment for a medical device. On the day before a critical regression test run, you discover that the engineer has configured the test script to skip the safety-critical test cases because they were failing intermittently, and the engineer is confident this is acceptable because "the failures are just timing issues in the test harness, not real bugs." The test results will be used for a regulatory submission milestone. How would you handle this situation?

**Answer:** This situation has two distinct problems that need addressing: the immediate technical decision and the underlying process issue. The immediate concern is that skipping safety-critical tests is never acceptable for a regulatory submission — regardless of the cause of the failures. The test results would be incomplete, and if the intermittent failures are real bugs, they'd be hidden from the submission evidence.

My first step would be to stop the test run and have a direct conversation with the engineer. I'd want to understand what they observed — what exactly was failing, how often, and what evidence they had that it was a harness issue rather than a firmware issue. I'd ask to see the failure logs and any analysis they'd done. The goal here is not to assign blame but to understand the technical situation fully.

Then I'd bring in the right people to assess the failures: if the engineer's analysis is sound and the failures are indeed harness-related, we still can't just skip the tests — we need to fix the harness and re-run. If the failures might be real firmware bugs, we need to investigate before any submission. Either way, the tests must run and pass with documented evidence.

For the immediate path forward, I'd propose: (1) restore the full test suite immediately, (2) run the tests to reproduce the intermittent failures, (3) capture detailed logs and waveforms to characterize the failures, (4) convene a quick triage with the firmware and hardware teams to determine root cause, and (5) fix the issue — whether it's in the harness or the firmware — before re-running the full suite. If the schedule slips, that's a consequence we need to manage with the project stakeholders, not by reducing test coverage.

The second part is the process lesson. I'd have a follow-up conversation with the engineer about why modifying test scripts to skip cases is never acceptable without explicit approval from the project lead and quality assurance. I'd also review the test environment's change control — there should be a mechanism where test script modifications are reviewed and approved, not made unilaterally. This might mean adding a code review step for test scripts, or requiring that any test exclusions be documented and approved in writing.

Finally, I'd document the incident and the resolution as part of the project's quality records. The key message to the team is that we don't hide intermittent failures — we investigate them, because intermittent failures in a medical device are often the most dangerous kind.

**Possible follow-ups:**
- How would you handle the situation if the engineer had already run the tests with the skipped cases and the results were already submitted to the regulatory body?
- What process changes would you implement to prevent this from happening again, while still encouraging junior engineers to raise concerns about flaky tests?