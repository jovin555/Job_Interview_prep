# tools — Day 42

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** The core requirement here is reproducibility and traceability — anyone should be able to rebuild the exact binary that was released, and the process should leave an audit trail. I'd start by establishing a single source of truth for the build: a version-controlled repository where the Zephyr application code, the Zephyr version (pinned via west manifest), and all configuration files (prj.conf, device tree overlays, and any custom board definitions) are committed together. The west manifest is critical because Zephyr modules evolve independently; pinning the manifest ensures the exact Zephyr tree, HALs, and any third-party modules are locked.

For the build itself, I'd use a containerized build environment — Docker or a similar approach — so that the toolchain, Zephyr SDK version, and host dependencies are identical regardless of which machine runs the build. The build script should be a single entry point that takes a build configuration name (e.g., production, development) and produces a deterministic output. I'd enable Zephyr's build reproducibility features where possible, such as disabling timestamps in the binary or recording the build metadata separately.

For auditability, each release build should be tagged in version control, and the build process should generate a manifest artifact that includes: the git commit hashes of the application and all west modules, the toolchain version, the build configuration, and a checksum of the output binary. This manifest becomes part of the design history file. I'd also configure the build to embed version information in the firmware itself — a build ID string or similar — so the running device can report exactly which build it's running, which is invaluable for field debugging.

Finally, I'd separate the release build from the development build. The release build should be a clean build (no incremental artifacts), run in the containerized environment, and produce a binary that goes through a formal sign-off. The development build can be more flexible, but it should never be used for regulatory submissions.

**Possible follow-ups:**
- How would you handle the case where a bug is found in a released version and you need to rebuild an older release — what would you need to have in place?
- How would you verify that the containerized build environment itself hasn't changed in a way that affects the output?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** The first step is to set up the measurement correctly. I'd use a mixed-signal oscilloscope with at least four analog channels and a logic probe. The switching regulator's switching node (the inductor side of the high-side FET) is the primary noise source, so I'd probe that with a 10x passive probe using a ground spring rather than the long ground lead — the ground lead acts as an antenna and will pick up noise that isn't really there. The analog sensor output would be probed with a differential or active probe if available, since single-ended probing at the sensor can be misleading if there's ground bounce.

I'd trigger the scope on the switching node's rising edge and look at the sensor output in the time domain, using averaging to see the deterministic coupling and then switching to single-shot or persistence mode to see the random component. The key measurement is the timing correlation: if the noise on the sensor output occurs exactly at the switching edges, that's strong evidence of coupling from the switcher.

To distinguish conducted vs. radiated vs. ground-plane coupling, I'd use a systematic approach. First, I'd check conducted coupling by measuring the noise on the power supply rail at the sensor's supply pin — if the ripple there correlates with the sensor noise, it's likely conducted through the shared supply. I'd also measure the voltage difference between the sensor's ground pin and the regulator's ground pin using a differential probe — if there's a significant high-frequency voltage difference, that points to ground-plane coupling or ground bounce.

For radiated coupling, I'd use a near-field probe connected to a spectrum analyzer or the scope's FFT function. I'd probe around the PCB to see if there's a radiated field at the switching frequency that could be coupling into the sensor's traces or the sensor itself. A useful test is to temporarily lift or shield the sensor input trace — if the noise changes dramatically, it's likely radiated coupling into that trace.

To confirm the dominant path, I'd do targeted experiments: add a ferrite bead or RC filter on the sensor's supply (if conducted, this helps), add a small capacitor at the sensor's input (if radiated into the trace, this helps), or improve the ground connection between the two sections (if ground bounce, this helps). The experiment that changes the noise the most identifies the dominant path.

**Possible follow-ups:**
- How would you use the scope's FFT function to identify the frequency content of the coupling, and what would you look for?
- How would you set up a differential measurement of ground bounce without introducing measurement artifacts?

---

## Q3: How would you approach setting up a hierarchical schematic design in Altium Designer for a complex mixed-signal medical device that has multiple identical sensor channels, and how would you ensure that design changes propagate correctly to all instances?

**Answer:** Hierarchical design in Altium is the right approach when you have repeated blocks, and the key is to use the multi-channel feature properly rather than just copying sheets. I'd start by creating a single "sensor channel" sheet that contains the complete analog front-end — the sensor interface, signal conditioning, ADC, and any local filtering. This sheet becomes a child sheet referenced by the parent sheet. In the parent, I'd place multiple sheet symbols pointing to that same child sheet, and Altium's multi-channel feature will automatically instantiate it multiple times.

The critical part is the net naming and bus structure. Each channel needs its own set of nets — for example, the ADC output for channel 1 must not short to channel 2's output. Altium handles this with the `Repeat()` function in the parent sheet. For a bus of ADC outputs, I'd use a net label like `ADC_DATA[0..3]` on the parent and connect each channel's output using `Repeat(ADC_DATA, 0, 3)` on the sheet symbol. This creates unique nets per channel instance automatically.

For design changes, the beauty of multi-channel is that you edit the child sheet once and all instances update. But I'd be careful about component designators — Altium assigns unique designators per instance (e.g., R1_1, R1_2, R1_3, R1_4), which is what you want for the BOM and assembly. I'd verify this in the BOM generation to ensure each instance's components appear separately.

I'd also use the "Channel Offset" feature if the channels need slightly different configurations — for example, different gain settings via a resistor value. Rather than creating separate sheets, I'd use a variant or a parameter that can be overridden per channel instance. If the differences are more structural, I might create two child sheets (e.g., "sensor_channel_type_A" and "sensor_channel_type_B") and reference both from the parent.

Before committing to the design, I'd run the ERC to catch net connectivity issues, and I'd use the cross-probe feature to verify that the PCB layout matches the schematic hierarchy. I'd also generate a PDF of the full hierarchy for design review, making sure the reviewers understand the multi-channel structure.

**Possible follow-ups:**
- How would you handle a situation where one channel needs a different component value than the others — would you use variants, parameters, or a separate sheet?
- How would you verify in the PCB layout that the four channels are actually routed consistently with each other?

---

## Q4: How would you approach setting up a Git-based version control workflow for a KiCad project that includes schematic files, PCB layout, 3D models, and a Bill of Materials, ensuring that design reviews and releases are properly tracked?

**Answer:** KiCad's file format is text-based, which makes it well-suited for Git, but there are some specific considerations. The first step is to establish a repository structure — I'd keep the KiCad project files (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`) at the root, with subdirectories for libraries (symbols, footprints, 3D models) and documentation. The 3D models are typically binary (`.step`, `.wrl`) and can be large, so I'd consider whether they belong in the same repo or a separate one — for a medical device, I'd keep them in the same repo for traceability, but I'd be mindful of repo size.

For the KiCad files themselves, I'd configure Git to handle the file format properly. KiCad files are human-readable text, but they can have long lines and the diff can be noisy. I'd set up a `.gitattributes` file to mark KiCad files appropriately, and I'd consider using a tool like `kicad-diff` or the KiCad CLI to generate meaningful diffs for design review — a raw text diff of a schematic file is often hard to read because net coordinates and UUIDs change even for small moves.

The workflow I'd use is: the `main` branch always represents the current released or release-candidate state. Feature branches are used for design changes — for example, "add ESD protection to sensor input" or "update decoupling on MCU power." Each branch should have a clear scope, and the commit messages should reference the change request or issue number. Before merging, the branch goes through a design review — I'd use GitLab or GitHub's merge request features, attaching screenshots of the schematic and PCB for visual review, since reviewers can't easily open the KiCad files in the MR interface.

For releases, I'd tag the commit with a version number (e.g., `v1.2.0`) and create a release artifact that includes the Gerbers, BOM, and a PDF of the schematic. The tag is the point of truth — anyone can check out that tag and regenerate the exact files that were sent to fabrication. I'd also maintain a `CHANGELOG.md` that documents what changed between releases.

One important detail: KiCad's backup files (`.kicad_orig`, `*-backups/`) should be in `.gitignore` — they're not meant for version control and will clutter the repo. Similarly, the `fp-lib-table` and `sym-lib-table` files should be committed, but the cache files (`.kicad_sch-bak`) should not.

**Possible follow-ups:**
- How would you handle a situation where two engineers are working on the same PCB file simultaneously — how would you manage merge conflicts?
- How would you integrate the KiCad project with your issue tracking system to ensure traceability from change request to design change?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first thing I'd do is stop the blame game — the goal is to get to a working system, not to determine whose fault it is. I'd call a short meeting with the leads from both teams, and I'd bring the actual hardware schematic and the firmware source code to the table. The key is to establish facts from the documentation, not from anyone's opinion.

I'd start by walking through the hardware: the schematic shows how the address pins are strapped, and the sensor datasheet defines whether it supports 7-bit or 10-bit addressing. Then I'd walk through the firmware: the I2C driver configuration and the register map definitions. The discrepancy should be immediately visible — either the address pins are strapped for a different address than the firmware uses, or the register map in the firmware header doesn't match the datasheet.

Once the discrepancy is confirmed, I'd assess the options. The critical question is: what can be changed in two days? Firmware changes are typically faster — changing the I2C address in the driver or updating the register map is a code change that can be done and tested relatively quickly. Hardware changes are not possible if the PCB is already fabricated — you'd need a board re-spin, which is weeks away. So the likely path is a firmware fix, unless the hardware has a fundamental issue that can't be worked around in software.

I'd also check whether there's a hardware workaround — for example, if the address pins are strapped via solder jumpers, they might be reconfigurable on the existing boards. But I wouldn't count on that without verifying the board assembly.

The next step is to define the fix and the verification plan. I'd have the firmware team make the change, and I'd work with both teams to define a quick integration test that specifically exercises the I2C communication — reading a known register and verifying the value. This test should be run on the actual hardware, not just on an evaluation board, because the eval board may have different address strapping.

Finally, I'd use this as a process improvement opportunity. The root cause is that the hardware and firmware teams didn't have a shared interface control document (ICD) for the I2C bus — the address and register map should have been defined in a single document that both teams referenced. I'd propose creating ICDs for all communication interfaces going forward, and I'd make sure the ICD is reviewed by both teams before hardware is finalized.

**Possible follow-ups:**
- How would you handle the situation if the firmware team insists that their code is correct because it works on the evaluation board?
- What would you do if the only fix requires a hardware change and the project timeline cannot absorb a board re-spin?