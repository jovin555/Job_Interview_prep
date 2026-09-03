# tools — Day 44

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** For a medical device, the build process itself is part of the design history file, so it needs to be reproducible and auditable. I'd start by establishing a single source of truth for the build environment — this typically means containerizing the toolchain (e.g., Docker with a pinned Zephyr SDK version, west version, and all Python dependencies) so that builds are identical regardless of which machine runs them. The west workspace itself should be locked to specific revisions of Zephyr and all modules, not floating on `main`.

For the build configuration, I'd use Zephyr's built-in `west build` with a dedicated `prj.conf` for production, and I'd ensure that all build-time options that affect safety-critical behavior are explicitly set rather than relying on defaults. The build script should capture metadata — git commit hash, build timestamp, toolchain versions, and a manifest of all west modules — and embed this into the firmware image itself, typically via a generated header file that gets compiled in. This way, the binary can be traced back to the exact source state.

For regulatory traceability, every release build should be tagged in git, and the build artifacts (firmware binary, hex file, map file, and a build report) should be archived with checksums. The build process should be scripted and run in a clean environment each time, with the script itself under version control and reviewed. I'd also set up a two-person rule for release builds — one person triggers the build, another verifies the artifacts against the recorded checksums and confirms the embedded metadata matches the intended release.

**Possible follow-ups:**
- How would you handle the case where a bug is found in a released version and you need to rebuild from an older tag?
- What build-time configuration options would you consider safety-critical and require explicit review before changing?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** This is a classic mixed-signal debugging scenario. I'd start by establishing a baseline — measure the analog sensor output with the switching regulator disabled (powered from a bench supply instead) to see the noise floor without the switcher running. Then I'd enable the regulator and measure the same signal to quantify the added noise. The key is to capture both time-domain waveforms and frequency-domain content simultaneously, which is where a mixed-signal oscilloscope with FFT capability becomes valuable.

To determine the coupling path, I'd use a structured approach. First, check for conducted coupling by probing the power supply rail at the sensor's supply pin with a wide bandwidth — if you see switching ripple at the regulator's frequency that correlates with the sensor noise, that suggests inadequate filtering or poor power supply rejection. Use a differential probe or measure across the rail to avoid ground bounce artifacts.

For ground plane coupling, I'd probe between different ground points on the board — if you measure significant voltage differences between the regulator's ground return and the sensor's ground reference, that indicates ground bounce or an inadequate return path. This is often revealed by placing the ground spring tip directly at the sensor's ground pin and the probe tip at the regulator's ground.

For radiated coupling, I'd use a near-field probe connected to a spectrum analyzer while the scope monitors the sensor output — if you can locate a radiating structure (e.g., the inductor or a long trace) that, when shielded or moved, changes the sensor noise, that confirms radiated coupling. A useful technique is to temporarily place a small grounded copper shield over suspect components to see if the noise changes.

To separate these paths more rigorously, I'd make targeted modifications: add a ferrite bead or pi-filter to the sensor supply to test conducted coupling; add a small capacitor between the sensor ground and the regulator ground to test ground coupling; or re-route a suspect trace to test radiated coupling. Each change that reduces the noise confirms that path. The scope's FFT helps identify the specific frequencies involved — the fundamental switching frequency and its harmonics — which you can then correlate with the coupling path.

**Possible follow-ups:**
- How would you set up the oscilloscope's trigger and acquisition to capture intermittent noise events?
- What probe techniques would you use to avoid introducing measurement artifacts when probing sensitive analog nodes?

---

## Q3: How would you approach setting up a hierarchical schematic design in Altium Designer for a complex mixed-signal medical device that has multiple identical sensor channels, and how would you ensure that design changes propagate correctly to all instances?

**Answer:** For a design with multiple identical channels, hierarchical design with device sheets is the right approach because it gives you true reuse — you design the channel once and instantiate it multiple times, and changes propagate to all instances automatically. I'd start by identifying the boundaries of the repeated block: for a sensor channel, this would include the sensor connector, signal conditioning (amplifier, filter), ADC interface, and any local decoupling. The key is to define clean interfaces at the sheet boundaries — power nets, ground, the digital bus (I2C or SPI), and any control signals — and to use named nets or harness connectors for these interfaces rather than global nets, which can create hidden dependencies.

In Altium, I'd create the channel as a device sheet with clearly defined sheet entries, then instantiate it multiple times in the top-level schematic. For the repeated channels, I'd use the multi-channel feature where Altium automatically handles the channel designators (e.g., Channel_1, Channel_2, etc.). The critical part is setting up the net labeling correctly — Altium's multi-channel feature will automatically append the channel identifier to nets that need to be unique per channel, but you need to be deliberate about which nets are per-channel and which are shared globally.

For design changes, the beauty of device sheets is that editing the underlying sheet updates all instances. However, I'd still implement a review process: before committing a change to the shared sheet, I'd verify that the change is appropriate for all channels and doesn't break the interface contract. I'd also use Altium's parameter management to handle any per-channel variations — for example, if channel 3 needs a different gain setting, I'd use a parameter that can be overridden per instance rather than creating a separate sheet. Finally, I'd run a full ERC after any change and visually inspect the updated PCB layout to confirm the propagation happened as expected, particularly checking that component designators and net names updated correctly across all instances.

**Possible follow-ups:**
- How would you handle a situation where one channel needs a slightly different component value than the others?
- What are the trade-offs between using device sheets versus a flat design with copy-paste for a design with only two or three repeated channels?

---

## Q4: How would you approach using a logic analyzer to debug a SPI bus where the master device intermittently fails to receive data from a slave, but only after the system has been running for several hours and the temperature inside the enclosure has risen?

**Answer:** This sounds like a temperature-dependent timing or signal integrity issue, so I'd approach it as a systematic investigation rather than jumping to conclusions. First, I'd set up the logic analyzer to capture the full SPI transaction — MOSI, MISO, SCLK, and CS — with sufficient sampling rate to see timing details, not just protocol-level decode. I'd configure the analyzer to trigger on the failure condition, which might be a missing response or a specific error pattern from the master.

Since the failure is temperature-dependent, I'd want to reproduce it in a controlled way. I'd instrument the system with a thermocouple near the SPI devices and the master to correlate temperature with failure onset. Then I'd run the system until the failure occurs while continuously logging SPI traffic. The key measurements I'd look for: (1) setup and hold time violations relative to the slave's datasheet requirements — as temperature rises, propagation delays change and timing margins can erode; (2) signal integrity issues like ringing or slow edges on SCLK or MISO that get worse with temperature; (3) CS timing issues — maybe the master is releasing CS too early or the slave needs more time to drive MISO.

If the logic analyzer shows clean protocol-level data but the master still fails, I'd suspect a marginal timing issue that's below the analyzer's resolution. In that case, I'd switch to an oscilloscope with high bandwidth to look at the actual signal edges — rise times, overshoot, and the exact timing relationship between SCLK edges and MISO transitions. I'd also check whether the slave's power supply is drooping at temperature, which could affect its output drive strength.

A useful technique is to deliberately stress the timing margins: if the SPI clock is programmable, I'd slow it down to see if the failure disappears (confirming a timing issue) or persists (suggesting something else like a firmware state machine issue or a marginal logic level). I'd also check the slave's datasheet for temperature-dependent parameters like output hold time or clock-to-output delay, and compare those against the measured margins.

**Possible follow-ups:**
- How would you distinguish between a timing margin issue and a firmware logic error that only manifests at temperature?
- What specific measurements would you take to determine if the issue is on the master side or the slave side?

---

## Q5: (Behavioral) Imagine you are leading a project where a junior engineer has been tasked with setting up the automated firmware test environment for a medical device. On the day before a critical regression test run, you discover that the engineer has configured the test script to skip the safety-critical test cases because they were failing intermittently, and the engineer is confident this is acceptable because "the failures are just timing issues in the test harness, not real bugs." The test results will be used for a regulatory submission milestone. How would you handle this situation?

**Answer:** This is a situation where I need to address both the immediate technical problem and the underlying judgment issue, while also protecting the regulatory integrity of the project. The first priority is to stop the test run from proceeding with the safety-critical cases skipped — for a medical device, skipping safety tests to get a green result is never acceptable, regardless of the reason. I would immediately halt the test setup and explain clearly, without blame, that for regulatory purposes, we cannot submit results from a test run that excluded safety-critical cases — the submission would be invalid, and if discovered, it would damage the company's credibility with regulators.

Then I'd work with the engineer to understand the intermittent failures. The fact that they're calling them "timing issues in the test harness" is a hypothesis, not a conclusion. I'd ask the engineer to walk me through the failure data — what exactly fails, how often, and under what conditions. If the failures are genuinely in the test harness (e.g., a synchronization issue between the test script and the device), then the fix is to correct the harness, not skip the tests. If the failures are actually in the device firmware, then skipping them would have hidden a real bug. The distinction matters enormously.

I'd also use this as a coaching moment. The engineer's instinct to get a green run is understandable, but the approach was wrong — the right response to intermittent failures is to investigate them, not work around them. I'd explain that in medical device development, an intermittent failure is often more important than a consistent one because it suggests a marginal design that could manifest in the field. I'd also review the test configuration to ensure no other tests were modified or skipped without proper review.

For the immediate path forward, I'd work with the engineer to either fix the harness issue or properly characterize the device failure, and I'd be transparent with management that the test run needs to be delayed until the issue is resolved. I'd also document the incident — not as a disciplinary matter, but as a learning opportunity in the project's lessons learned, and I'd review our test environment setup process to see if we need better guardrails to prevent this kind of configuration drift in the future.

**Possible follow-ups:**
- How would you handle the situation if the engineer had already run the tests and submitted the results before you discovered the issue?
- What preventive measures would you put in place to ensure this doesn't happen again in future test campaigns?