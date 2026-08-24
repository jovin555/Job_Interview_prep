# tools — Day 34

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** For a medical device, the build process itself becomes part of the design history file, so reproducibility and traceability are the primary goals. I'd start by establishing a single source of truth for the toolchain — pinning the Zephyr SDK version, the west workspace manifest, and all tool versions (compiler, CMake, Python dependencies) in a way that can be exactly reproduced. The west manifest file is key here: it should reference specific commit SHAs for Zephyr and all modules, not branches or tags that can move.

For the build itself, I'd use a containerized build environment (e.g., Docker) so that the build host's OS updates or library changes can never silently alter the output. The build script would be a single entry point that: checks out the exact manifest, applies any local patches, builds the firmware, and then generates a build report containing the git SHA of the source tree, the manifest SHA, toolchain versions, build timestamp, and a hash of the output binary.

For regulatory traceability, I'd tag the source tree at the exact commit that produced each release binary, and store the binary, the build report, and the source tag together as a release artifact set. The build should be deterministic — using `-ffile-prefix-map` or equivalent to strip host-specific paths, and disabling any timestamp-based features that would make two builds of the same source produce different binaries. I'd also generate a SBOM (software bill of materials) from the Zephyr module list, since regulatory reviewers increasingly expect visibility into third-party components.

Finally, I'd set up the release process so that only a designated person (or CI pipeline with proper access controls) can create a release build, and the output is automatically archived to a controlled location with checksums recorded. This prevents the common problem of "which build did we actually test?" during verification.

**Possible follow-ups:**
- How would you handle the case where a bug is found in a released build — what's your process for reproducing the exact build to verify the fix?
- What information would you include in the build report to satisfy a regulatory auditor's traceability requirements?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize the noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** The first step is to set up simultaneous measurement of the switching node, the regulator output, and the analog sensor's output or reference voltage — a mixed-signal oscilloscope with at least four channels is ideal for this. I'd use short-ground-spring probes (not the long clip leads) to minimize probe-induced artifacts, and I'd measure at the actual IC pins rather than at test points, since the PCB trace between them can change what you see.

To determine the coupling path, I'd use a systematic elimination approach. First, I'd measure the sensor output with the regulator running normally, then with the regulator disabled (powering the sensor from a bench supply instead) to confirm the noise is actually coming from the regulator. Next, I'd look at the timing correlation: the noise on the sensor should align with the switching edges of the regulator. If the noise appears at the switching frequency and its harmonics, it's coupled from the regulator.

To distinguish conducted vs. radiated vs. ground-plane coupling: I'd probe the ground voltage at the sensor's ground pin relative to the regulator's ground — if there's significant high-frequency voltage difference between the two ground points, that suggests ground-plane coupling or conducted noise through the shared ground impedance. I'd also measure the noise on the power rail at the sensor's supply pin; if the ripple is present there, it's conducted through the power distribution. If the noise is present but the power and ground at the sensor are clean, then radiated coupling (magnetic field from the inductor, or electric field from the switching node) is the likely path — I'd confirm by moving a small shielded loop probe near the inductor and switching node while watching the sensor output.

A useful technique is to temporarily add a ferrite bead or RC filter on the sensor's supply — if the noise drops significantly, it's conducted. If it doesn't change, the coupling is likely radiated or through the ground plane. I'd also check whether the noise amplitude scales with load current on the regulator, which would point to the inductor's magnetic field or ground bounce from higher di/dt.

**Possible follow-ups:**
- How would you use the oscilloscope's FFT function to help identify the coupling mechanism?
- What would you do differently if the noise only appears when the system is under load (e.g., a motor running)?

---

## Q3: How would you approach setting up a hierarchical schematic design in Altium Designer for a complex mixed-signal medical device that has multiple identical sensor channels, and how would you ensure that design changes propagate correctly to all instances?

**Answer:** For a design with multiple identical channels, I'd use Altium's multi-channel design feature within a hierarchical structure. The approach is to create a single "sensor channel" schematic sheet as a child sheet, then instantiate it multiple times in a parent sheet using repeat port syntax like `REPEAT(Channel, 1, 4)`. This gives you four identical channels without copying and pasting the schematic — which is the source of most copy-paste errors.

The key benefit is that any change to the child sheet automatically propagates to all instances. For example, if I need to change a filter capacitor value or add a pull-up resistor, I edit the child sheet once, and all four channels update. This is critical for medical devices where consistency between channels matters for both performance and documentation.

For component designators, Altium automatically assigns unique designators to each instance (e.g., R1_1, R1_2, R1_3, R1_4 for the same resistor in each channel). I'd configure the designator format in the project options to make it clear which instance each component belongs to, which helps during PCB layout and debugging.

For the PCB layout, I'd use the "channel offset" feature to place the four channels as repeated blocks — this lets me lay out one channel, then replicate the placement and routing to the other three with the same relative coordinates. This ensures consistent performance across channels and makes the layout review much easier.

One thing I'd be careful about is the net naming: Altium handles the channel-specific net names automatically (e.g., `Channel1_Sensor_Out`, `Channel2_Sensor_Out`), but I'd verify the net naming scheme is clear before generating the netlist. I'd also set up the project's variant system early if different channels might have different component values in different product variants — this is common in medical devices where you might have a "standard" and "high-sensitivity" configuration.

**Possible follow-ups:**
- How would you handle a situation where one channel needs a slightly different component value than the others?
- How would you verify that all four channels are actually identical in the final PCB layout?

---

## Q4: How would you approach setting up a Git-based version control workflow for a KiCad project that includes schematic files, PCB layout, 3D models, and a Bill of Materials, ensuring that design reviews and releases are properly tracked?

**Answer:** KiCad's file format is text-based (S-expression format for schematics and PCBs), which makes it well-suited for Git, but there are some specific considerations. First, I'd establish a repository structure that separates the KiCad design files from generated artifacts: the source files (`.kicad_sch`, `.kicad_pcb`, `.kicad_pro`, libraries) go in the repo, while generated files (Gerbers, drill files, PDFs, BOM exports) are either gitignored or stored in a separate release directory that's tagged but not committed on every change.

For the KiCad-specific setup, I'd configure the project to use relative paths for library references (in the `.kicad_pro` file, set the library paths to relative), so the project is portable across machines. I'd also ensure that the schematic and PCB libraries are versioned in the same repo — this is critical because if someone updates a footprint in the library, the PCB file needs to be regenerated, and you need to be able to trace which library version produced which PCB.

For the workflow itself, I'd use feature branches for significant design changes, with the main branch always representing a known-good state. Before merging, I'd run the ERC and DRC and require that they pass with zero errors (or documented, approved waivers). For design reviews, I'd use GitLab/GitHub merge requests with the diff view — since KiCad files are text, reviewers can see exactly what changed in the schematic or PCB, which is much more effective than reviewing screenshots.

For releases, I'd tag the commit with a version number (e.g., `v1.2.0`) and then generate the fabrication files from that exact tag. The BOM is a special case: I'd generate it from the schematic using a script (rather than manually maintaining it), so it's always in sync with the design. The BOM generation script itself would be versioned in the repo.

One important detail: KiCad's PCB file can change formatting between versions, so I'd pin the KiCad version in the project documentation and ideally use a container or a specific CI environment for generating release artifacts. This prevents the situation where someone opens the project in a newer KiCad version, saves it, and the diff becomes unreadable due to format changes.

**Possible follow-ups:**
- How would you handle binary files like 3D models that don't diff well in Git?
- What would you do if you needed to revert a PCB change that was already sent to fabrication?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting a specific register map with a particular bit ordering, but the hardware's sensor uses a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first thing I'd do is stop the discussion about who's "right" and focus on establishing the facts. I'd call a short meeting with both teams and ask them to bring their source of truth: the firmware team brings the sensor datasheet section they based their register map on, and the hardware team brings the schematic showing how the sensor is connected and the exact sensor part number and variant. The goal is to determine whether this is a documentation error, a firmware implementation error, a hardware configuration error (e.g., address pins strapped differently), or a genuine misunderstanding of the protocol.

Once we've identified the discrepancy, I'd assess the impact. If the firmware can be fixed by changing a register map or bit-ordering in a driver file, that's a low-risk change that can be done in a day with proper review. If the hardware is actually wired incorrectly (e.g., the address pins are strapped for a different address than the firmware expects), that's a more serious problem — but it might still be fixable in firmware if the sensor supports multiple addresses, or if the firmware can be configured to use the address the hardware actually implements.

The key decision point is whether to delay integration testing or proceed with a known workaround. I'd evaluate the risk: if the fix is purely in firmware and can be verified on the bench before integration testing, I'd allow the firmware team to make the change, but I'd require a written summary of the discrepancy, the fix, and the verification performed. This documentation becomes part of the design history file. If the fix requires a hardware change (e.g., a rework on the PCB), I'd delay integration testing rather than proceed with a known-bad configuration — testing against incorrect hardware would produce misleading results and waste everyone's time.

I'd also use this as a process improvement opportunity: the root cause is almost always a communication gap between hardware and firmware teams — often because they're referencing different revisions of the datasheet or because the interface control document (ICD) wasn't maintained. After resolving the immediate issue, I'd propose creating or updating a formal interface document that specifies the I2C address, register map, bit ordering, and timing requirements, and make it the single reference for both teams.

**Possible follow-ups:**
- How would you handle the situation if the firmware team insists their implementation is correct because it works on the evaluation board?
- What would you do if the hardware team says the PCB is already in fabrication and cannot be changed?