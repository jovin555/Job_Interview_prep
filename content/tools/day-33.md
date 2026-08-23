# tools — Day 33

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** For a medical device, the build process itself becomes part of the design history file, so reproducibility and traceability are the primary concerns. I'd start by defining a single source of truth for the build: a version-controlled Zephyr workspace using `west` with a locked manifest file that pins the exact Zephyr version, module revisions, and toolchain versions. The manifest should be tagged to match firmware releases.

For the build itself, I'd use a containerized build environment (e.g., Docker) that includes the exact toolchain, SDK, and dependencies — this eliminates "works on my machine" issues and ensures the same inputs always produce the same outputs. The build script would capture metadata automatically: git commit hash, manifest revision, build timestamp, compiler version, and any Kconfig options that differ from defaults. This metadata gets embedded in the firmware image itself, so you can always identify what's running on a device in the field.

For release artifacts, I'd generate a build manifest file alongside the binary that records all of this information, plus checksums (SHA-256) of the firmware image. This manifest becomes part of the regulatory submission. I'd also configure the build to produce a bill of materials from the Zephyr configuration — essentially the list of enabled subsystems, drivers, and their versions — which helps with vulnerability tracking and change impact analysis.

Finally, I'd set up a release tagging strategy in Git: release candidates get tags like `v1.2.0-rc1`, and only builds from signed tags are considered releasable. The CI pipeline would enforce that release builds come from clean checkouts, not dirty working trees.

**Possible follow-ups:**
- How would you handle the case where a field issue requires rebuilding an older firmware version — how do you ensure you can reproduce that exact build?
- What information would you include in the embedded version string, and how would you expose it to the application layer?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize the noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** This is a classic mixed-signal debugging scenario. I'd start by establishing a baseline: power up the board with the switching regulator disabled (if possible) and measure the analog sensor output noise floor. Then enable the regulator and measure again — the difference tells you how much noise is being injected.

To characterize the coupling path, I'd use a systematic approach. First, I'd probe the switching node of the regulator with a proper probe — ideally a tip-and-barrel or a short ground spring, not the long ground lead, which acts as an antenna and picks up radiated noise that isn't really there. I'd measure the ripple at the regulator output, then move to the analog sensor's supply pin to see how much of that ripple actually arrives. The attenuation (or amplification) between these points tells you about the impedance of the power distribution path.

To distinguish conducted vs. radiated coupling, I'd use a few techniques. For conducted coupling, I'd look at the noise on the supply rail and ground at the sensor — if the noise frequency and amplitude correlate with the regulator's switching frequency and its harmonics, it's likely conducted through the power or ground path. I'd also check whether the noise appears on the sensor's output even when the sensor inputs are shorted — that suggests supply or ground coupling rather than signal-path coupling.

For radiated coupling, I'd use a near-field probe (H-field loop) to sniff around the board and see if the noise is being radiated from the regulator's inductor or switching loop and picked up by sensitive traces. I'd also try moving a ground plane or shield between the regulator and the sensor area to see if the coupling changes.

For ground-plane coupling specifically, I'd probe the ground at multiple points across the board with the scope set to high sensitivity (e.g., 10–20 mV/div) and look for voltage gradients. If there's significant noise between two ground points, that indicates ground bounce or inadequate ground plane continuity. I might also use a differential probe across two ground points to measure the actual ground noise without introducing measurement artifacts.

The key is to correlate time-domain measurements with the regulator's switching events — using the scope's trigger on the switching node and averaging to extract the noise signature that's synchronized with the switching, versus the noise that's random or asynchronous.

**Possible follow-ups:**
- How would you determine whether the noise is primarily from the switching node's high dv/dt or from the inductor's AC ripple current?
- What modifications would you try first if the coupling is primarily through the ground plane?

---

## Q3: How would you approach setting up a component library management strategy in KiCad for a medical device project that needs to maintain strict revision control and regulatory traceability, given that KiCad's library format is file-based rather than database-driven?

**Answer:** KiCad's file-based libraries actually lend themselves well to version control, which is the foundation of regulatory traceability. I'd structure the libraries as a separate Git repository — or a dedicated directory within the project repo — with a clear folder hierarchy: one folder for schematic symbols, one for footprints, one for 3D models, and one for the symbol-to-footprint mapping tables.

The critical piece is establishing a naming convention that encodes part information and revision. For example, a symbol file might be named `SENSOR_TMP117_REV1.kicad_sym`, and the footprint `SENSOR_TMP117_REV1.kicad_mod`. When a component changes — say the manufacturer updates the package or the electrical characteristics — you create a new revision rather than overwriting the existing one. This gives you an audit trail: you can always trace which revision of a symbol was used in a specific board revision.

For traceability, I'd maintain a component metadata file — a CSV or YAML file — that maps each library component to its manufacturer part number, datasheet revision, and the date it was added or modified. This file lives in the same repo and gets reviewed alongside any library changes. The metadata should also include the approval status (e.g., "approved for use in Class II devices") and any restrictions.

I'd also set up a review workflow: library changes go through a pull request process with at least one other engineer reviewing the change. The commit message must reference the change reason (e.g., "Updated to fix footprint pad size per manufacturer PCN"). This creates a complete history that satisfies audit requirements.

For the project itself, I'd use KiCad's ability to reference libraries by relative path, so the project doesn't depend on absolute paths that break on different machines. The library repo gets pulled as a submodule or dependency, and the project's `fp-lib-table` and `sym-lib-table` files are version-controlled to ensure everyone uses the same library revisions.

**Possible follow-ups:**
- How would you handle the situation where a component is used across multiple projects, and one project needs a different revision than another?
- What would you include in the component metadata to support regulatory audits without making the process so heavy that engineers bypass it?

---

## Q4: How would you approach using a logic analyzer to debug an I2C bus where the slave device occasionally fails to acknowledge (NACKs) a read transaction, but only after the system has been running for several hours — and the failure disappears when you connect the logic analyzer?

**Possible follow-ups:**
- How would you determine whether the NACK is coming from the slave not recognizing its address, or from the slave being busy and unable to respond?
- What changes would you make to the firmware to help diagnose this issue in the field?

**Answer:** This is a frustrating class of problem because the measurement tool itself changes the behavior — the added capacitance of the logic analyzer probes can alter signal timing just enough to mask the issue. I'd approach this in stages.

First, I'd set up the logic analyzer to capture continuously with a deep buffer, triggering on the NACK condition. I'd configure the decode for I2C and capture the entire transaction — address byte, register pointer, and read data — so I can see exactly where the NACK occurs. I'd also capture a known-good transaction for comparison.

Since the failure disappears with the analyzer attached, I'd suspect a marginal timing or voltage issue. The analyzer's probe capacitance (typically 5–10 pF per channel) can slow the signal edges, which might actually help marginal signals meet setup/hold times. So I'd try using a lower-capacitance probing approach — perhaps a single probe on the SDA line only, or using a differential probe if available.

I'd also look at the bus pull-up resistors. If the pull-ups are too weak (high resistance), the rise time might be marginal, and the added capacitance of the analyzer could actually help by slowing the edge further — which would explain why the failure disappears. I'd measure the rise time on both SCL and SDA with the scope (using a 10x probe with a ground spring) and compare against the I2C spec for the bus speed being used.

For the "after several hours" aspect, I'd suspect temperature drift or a marginal solder joint that expands with heat. I'd use a thermal camera or thermocouple to check the temperature of the slave device and nearby components. I'd also check whether the slave's supply voltage is drooping under load — a marginal regulator that degrades as it heats up could cause the slave to brown out intermittently.

In firmware, I'd add a retry mechanism with logging: when a NACK occurs, log the transaction details, the number of retries, and the system state (temperature sensor reading, supply voltage if monitored, uptime). This gives field data that can correlate the failure with environmental conditions.

Finally, I'd consider whether the slave is actually entering a low-power or busy state after extended operation — some sensors have internal state machines that can get stuck if a previous transaction was interrupted. A watchdog or periodic reset of the slave might be appropriate.

---

## Q5: (Behavioral) Imagine you are leading a project where a junior engineer has been tasked with setting up the lab test equipment for an upcoming thermal validation test of a sealed medical device enclosure. On the day before the test, you discover that the engineer has configured the thermocouple data acquisition system with the wrong sampling rate — it's set to sample once per minute, but the test protocol requires sampling at least once per second to capture transient thermal behavior during the worst-case power dissipation scenario. The engineer is confident that once per minute is sufficient because "the temperature changes slowly." The test chamber is booked for tomorrow, and rescheduling would delay the project by two weeks. How would you handle this situation?

**Answer:** This is a situation where I need to address both the immediate technical issue and the underlying judgment gap, without damaging the engineer's confidence or the team's momentum.

First, I'd acknowledge the engineer's reasoning — it's true that the bulk temperature changes slowly in a sealed enclosure. But I'd explain that the test isn't just about steady-state temperature; it's about capturing the transient response, particularly the thermal overshoot when the device switches to its highest power mode. At one sample per minute, you might miss a critical peak that occurs and decays within seconds, which would invalidate the thermal validation. I'd show them the test protocol requirement and walk through why it exists — this turns it into a learning moment rather than a correction.

Then I'd assess whether we can fix it in time. Changing the sampling rate on the DAQ is typically a configuration change that takes minutes, not hours. I'd have the engineer make the change immediately and then verify the configuration with a quick test — maybe a heat gun or a soldering iron tip near one thermocouple to confirm the system is capturing fast transients. This verification step is important because it validates the entire setup, not just the sampling rate.

I'd also use this as an opportunity to review the rest of the test setup — channel mapping, thermocouple placement, calibration status — so we're confident the whole system is correct before the expensive chamber time. This is a "trust but verify" moment: I'd have the engineer walk me through their entire configuration and explain their choices, which both confirms the setup and builds their understanding.

After the test, I'd have a debrief conversation about the importance of reading and following test protocols exactly, and about asking questions when a protocol requirement seems unnecessary. I'd frame it as: "If you think a requirement is wrong, that's worth raising — but you need to raise it before the test, not after, and you need to understand the rationale before deciding it's unnecessary."

**Possible follow-ups:**
- How would you handle the situation if the engineer had also configured the wrong thermocouple types, and the error wasn't caught until after the test?
- What would you do to prevent this type of configuration error from happening again in future test campaigns?