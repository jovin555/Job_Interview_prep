# tools — Day 43

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** For a medical device, the build process itself becomes part of the design history file, so reproducibility and traceability are paramount. I'd start by establishing a single source of truth for the toolchain — pinning the Zephyr SDK version, the west workspace manifest, and all Python dependencies using a requirements file or container image. The west manifest should reference specific commit SHAs for Zephyr and any modules, never floating branches. 

For the build itself, I'd use a CI system (Jenkins, GitLab CI, or similar) that runs on every commit and produces a build artifact with a unique build ID. The build script would capture the git commit hash, the west manifest hash, toolchain versions, and environment variables into a build manifest file that gets embedded into the firmware image itself — for example, as a string in a dedicated flash section. This way, you can read the build metadata back from a physical device later.

For release builds specifically, I'd require a clean build from a tagged commit, with the tag signed and the build performed in a controlled environment. The output artifacts would include the binary, a checksum file, the build manifest, and a link to the CI log — all archived together. I'd also configure the build to fail on warnings and to produce deterministic builds where possible (fixed timestamps, no absolute paths), so two builds from the same commit produce byte-identical binaries. This makes verification much simpler and gives regulators confidence in the process.

**Possible follow-ups:** How would you handle the case where a bug is found in a released build — what information would you need to reproduce it? How would you manage Zephyr module updates without breaking the auditable build?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** I'd approach this systematically, starting with time-domain measurements to correlate the noise with the switching events. First, I'd use one channel to probe the switching node of the regulator (through a low-capacitance probe or a proper differential probe) to establish the switching frequency and timing. Simultaneously, I'd probe the analog sensor output or its supply rail using a high-impedance active probe or a passive probe with a ground spring — never the long ground lead, which would pick up noise that isn't really there.

The key measurement is the correlation: does the noise on the analog signal occur exactly at the switching edges, or is it delayed? If it's synchronous with the switching edges, I'd look at the coupling path. To distinguish conducted from radiated coupling, I'd use a few techniques. First, I'd check the power supply rail at the sensor with a wide bandwidth — if the noise amplitude on the rail matches what's seen at the sensor output, it's likely conducted through the supply. Second, I'd temporarily lift or reroute the ground connection — if the noise changes dramatically, ground coupling is likely. Third, I'd move a near-field probe around the board to see if there are localized radiating structures between the regulator and the sensor.

For ground plane coupling specifically, I'd look at the voltage difference between two points on the ground plane using a differential probe — if there's significant high-frequency voltage gradient across the ground plane between the regulator and the sensor, that's a strong indicator of ground bounce or inadequate return paths. I'd also check whether the noise appears on the sensor's reference or shield connections. The measurement setup matters enormously here — using a ground spring, keeping probe loops small, and understanding the probe's bandwidth limitations are all critical to getting trustworthy data.

**Possible follow-ups:** How would you set up the oscilloscope's trigger to capture intermittent noise events? What bandwidth would you need on the scope and probes to see switching noise on a 2 MHz regulator?

---

## Q3: How would you approach setting up a component library management strategy in KiCad for a medical device project that needs to maintain strict revision control and regulatory traceability, given that KiCad's library format is file-based rather than database-driven?

**Answer:** KiCad's file-based libraries actually work well for revision control if you structure them properly. The key principle is that every component — schematic symbol, footprint, and 3D model — must be traceable to a specific revision of a specific datasheet or manufacturer specification. 

I'd organize the library as a separate Git repository, or as a dedicated directory within the project repository, with a clear folder structure: one folder per component family or per manufacturer, with symbol libraries (.kicad_sym), footprint libraries (.kicad_mod), and 3D models (.step or .wrl) co-located. Each component would have a naming convention that includes the manufacturer part number and a revision suffix — for example, `SENSOR-PRESSURE-ABC123-REV2`. 

The critical piece is the accompanying metadata. I'd maintain a CSV or YAML file in the library that records, for each component: the manufacturer part number, the datasheet revision and date, the date the component was added or updated, and a link to the datasheet file stored in the repository. This metadata file gets reviewed and committed alongside any library changes. When a component changes — say the manufacturer releases a new datasheet revision — the component gets a new revision suffix, and the old one remains in the library for historical builds. This way, you can always rebuild an old design with the exact components that were used at the time.

For the project itself, I'd reference the library at a specific commit SHA in the project's documentation, and I'd use KiCad's cache files to ensure that the schematic and PCB contain the exact component definitions used at design time. Before any release, I'd verify that the library commit matches the documented SHA and that no uncommitted changes exist.

**Possible follow-ups:** How would you handle a component that becomes obsolete mid-project — what's your process for managing the transition? How would you ensure that the 3D model matches the actual component footprint?

---

## Q4: How would you approach setting up a hardware-in-the-loop (HIL) test environment for a medical device that needs to verify firmware behavior against simulated sensor inputs, and what are the key considerations for making the tests meaningful and repeatable?

**Answer:** A HIL environment for a medical device needs to bridge the gap between pure software simulation and full hardware testing. The core idea is that the real firmware runs on the real microcontroller, but the sensors and actuators are replaced by simulated versions that respond deterministically to the firmware's actions.

I'd start by defining the interface boundary carefully. For a device with pressure sensors and motor control, for example, the HIL setup would need to simulate the sensor outputs (perhaps with a DAC or a programmable resistor network) and measure the motor drive signals (PWM duty cycle, direction pins). The simulation host — typically a PC running a real-time simulation model — would compute the expected sensor values based on the motor commands and the simulated patient physiology, then drive the analog or digital inputs accordingly.

The key considerations for meaningful tests are determinism and timing fidelity. The HIL loop must close fast enough that the firmware can't distinguish the simulated sensors from real ones — this often means the simulation needs to run on a real-time target or at least with bounded latency. I'd also want the ability to inject faults: sensor disconnection, out-of-range values, intermittent communication errors, and power supply dips. These fault injection tests are often where the most valuable findings come from.

For repeatability, every test run should start from a known state — I'd power-cycle the device, reset the simulation model, and verify that the initial conditions match the test definition. The test script should log both the simulated inputs and the firmware's responses with timestamps, so you can replay any test and compare results. Finally, I'd make the test definitions version-controlled alongside the firmware, so you can trace which tests were run against which firmware revision.

**Possible follow-ups:** How would you handle the timing synchronization between the simulation host and the real-time firmware? What would you do if the HIL tests pass but the device fails in real-world testing?

---

## Q5: (Behavioral) Imagine you are leading a project where a junior engineer has been tasked with setting up the automated firmware test environment for a medical device. On the day before a critical regression test run, you discover that the engineer has configured the test script to skip the safety-critical test cases because they were failing intermittently, and the engineer is confident this is acceptable because "the failures are just timing issues in the test harness, not real bugs." The test results will be used for a regulatory submission milestone. How would you handle this situation?

**Answer:** This situation has two distinct problems that need addressing: the immediate technical decision and the underlying process issue. The first thing I'd do is stop the test run — we cannot proceed with a regression test that excludes safety-critical cases, regardless of the reason. The regulatory submission requires evidence that those tests were executed and passed, and skipping them would invalidate the entire run.

I'd then sit down with the engineer to understand the intermittent failures. The fact that they're "timing issues in the test harness" is a hypothesis, not a conclusion — and even if it's true, it means the test harness itself is not fit for purpose and needs to be fixed, not worked around. I'd ask the engineer to walk me through the failure logs and their analysis. If the failures are genuinely in the harness — say, a race condition in the test script or a timing margin that's too tight — then we need to fix the harness and re-validate it. If the failures are actually in the firmware, then skipping the tests would have hidden a real defect in a safety-critical system.

For the immediate path forward, I'd propose that we delay the regression run by a day or two to properly investigate. If that's not possible, we could run the full suite including the failing tests, document the failures, and investigate them as part of the regression — but we cannot claim a clean pass. The regulatory submission can proceed with documented failures and a clear corrective action plan, but it cannot proceed with tests that were silently skipped.

After resolving the immediate issue, I'd address the process gap. The engineer made a judgment call that should have been escalated — they likely didn't appreciate the regulatory implications of skipping safety-critical tests. I'd use this as a teaching moment about the difference between development testing and verification testing, and about the importance of surfacing problems rather than working around them. I'd also review the test environment's configuration management to ensure that test scripts are reviewed before use in regulatory-critical runs.

**Possible follow-ups:** How would you handle the situation if the engineer had already run the tests and submitted the results before you discovered the issue? What changes would you make to the test environment's review process to prevent this from happening again?