# tools — Day 37

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** For a medical device, the build process itself becomes part of the design history file, so reproducibility and traceability are the primary drivers. I'd start by establishing a clean, version-controlled build environment — this means pinning the Zephyr SDK, toolchain, and all dependencies to specific versions, ideally using a container or a dedicated build machine that's itself under configuration control. The `west` build system supports manifests that lock the Zephyr kernel and module versions, so I'd commit the manifest file and ensure that `west update` always produces the same tree.

For the build itself, I'd create a scripted pipeline that: checks out the exact source revision, runs `west build` with a fixed configuration, captures the resulting binary, and generates a SHA-256 checksum. The output artifacts should include not just the firmware image but also the build log, the exact configuration used (`.config` file), the manifest lock file, and a report of the toolchain versions. These get stored together with a release tag in version control. For regulatory traceability, I'd also want the build to fail if there are uncommitted changes or if the working tree doesn't match the tagged revision — you never want to discover later that the binary you tested doesn't match the source you released.

One additional consideration is making the build deterministic — for example, disabling timestamp embedding or ensuring the build path is consistent, so that rebuilding the same revision produces a byte-identical binary. This gives you confidence that the artifact you tested is exactly what was released.

**Possible follow-ups:** How would you handle signing or encryption of the firmware image in this pipeline? What would you do if you needed to reproduce a build from six months ago?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize the noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** The first step is to establish a baseline measurement of the noise at the analog sensor's output or power pin while the switching regulator is operating. I'd use a high-bandwidth oscilloscope with sufficient vertical resolution — ideally 12-bit or higher — and a low-noise front end. For probing, I'd use a passive probe with a ground spring rather than the long ground lead, because the lead inductance will pick up radiated noise and corrupt the measurement. If the signal is very small, an active probe or a differential probe might be necessary.

To separate coupling mechanisms, I'd take a structured approach. First, I'd measure the noise at the sensor's supply pin and output with the regulator running, then with the regulator disabled but the rest of the system powered — this tells me whether the noise is actually coming from the regulator. Next, I'd look at the frequency content: switching regulator noise appears at the switching frequency and its harmonics, so I'd use FFT on the oscilloscope to confirm the spectral signature matches.

To distinguish conducted versus radiated coupling, I'd try a few experiments. For conducted coupling, I'd add a ferrite bead or increase the filtering on the supply line temporarily and see if the noise at the sensor changes. For radiated coupling, I'd move a near-field probe around the board to see if there are hotspots near the regulator's inductor or switching node. For ground-plane coupling, I'd measure the voltage difference between two ground points on the board using a differential probe — if there's significant ground bounce, that's a strong indicator. The key is to change one variable at a time and observe the effect at the sensor, rather than trying to infer the mechanism from a single measurement.

**Possible follow-ups:** How would you determine whether the noise is common-mode or differential-mode? What oscilloscope settings would you use to capture intermittent noise events?

---

## Q3: How would you approach setting up a hierarchical schematic design in Altium Designer for a complex mixed-signal medical device that has multiple identical sensor channels, and how would you ensure that design changes propagate correctly to all instances?

**Answer:** Hierarchical design is the right approach when you have repeated blocks, because it lets you define the circuit once and instantiate it multiple times. In Altium, I'd create a sheet symbol for the sensor front-end block, with clearly defined ports for power, ground, the sensor input, the ADC output, and any control signals. The underlying child sheet contains the actual circuitry — the signal conditioning, filtering, and ADC interface.

For multiple identical channels, I'd use the multi-channel feature, which allows you to place the same sheet symbol multiple times and have Altium automatically handle the channel designators (for example, `CH1_U1`, `CH2_U1`). This is cleaner than manually copying the schematic because the design intent is explicit — the channels are identical by definition, not just by coincidence.

The critical part is managing changes. When you edit the child sheet, all instances update automatically, which is the main advantage. However, you need to be careful about things that differ between channels — for example, if channel 1 has a different sensor variant or a different address strap. I'd handle that by making those differences explicit through parameters on the sheet symbol, or by using a variant design if the differences are more extensive. For propagation, I'd run a full ERC after any change to catch issues like unconnected ports or mismatched net names, and I'd verify that the netlist generated for each channel is correct before moving to layout.

**Possible follow-ups:** How would you handle a situation where one channel needs a slightly different filter cutoff than the others? How would you ensure the PCB layout team knows which components belong to which channel?

---

## Q4: How would you approach setting up a Git-based version control workflow for a KiCad project that includes schematic files, PCB layout, 3D models, and a Bill of Materials, ensuring that design reviews and releases are properly tracked?

**Answer:** KiCad's file format is text-based, which makes it well-suited for Git, but there are some nuances. The schematic and PCB files are human-readable (or at least diffable), but the 3D models and any binary footprint libraries are not. I'd structure the repository so that the KiCad project files, schematic, PCB, and the generated BOM are all under version control, while the 3D models are either stored in a separate repository or referenced from a shared library location — you don't want to bloat the repo with large binary files that change frequently.

For the workflow itself, I'd use feature branches for design changes, with the main branch representing the last reviewed and approved state. Each significant change — a new component, a routing change, a constraint update — gets its own branch and pull request, so that reviews are focused and traceable. The commit messages should reference the design change request or issue number, which gives you traceability back to the requirement.

For releases, I'd tag the repository with a version number that matches the design revision (for example, `rev-b` or `v1.2`). The release tag should point to a commit where the schematic, PCB, and BOM are all in sync. I'd also generate the fabrication files (Gerbers, drill files, BOM) as part of the release process and store them alongside the tag, rather than regenerating them later — this ensures the exact files sent to the board house are preserved. One thing I'd emphasize is that the BOM should be generated from the schematic, not maintained separately, so that it can't drift out of sync with the design.

**Possible follow-ups:** How would you handle binary footprint libraries in this workflow? What would you do if two engineers were working on the same PCB layout simultaneously?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first priority is to de-escalate the situation and get everyone focused on the facts rather than defending their position. I'd call a meeting with both teams and start by acknowledging that this kind of discrepancy is common in complex systems — it's not about blame, it's about finding the truth. I'd ask each team to walk through their implementation with the actual documentation in hand: the firmware team shows the datasheet section they used for the register map and addressing, and the hardware team shows the schematic and the actual device variant that was placed on the board.

The key is to verify against the physical hardware, not just the documentation. I'd have someone read the I2C address pins on the actual PCB — they're strapped to specific voltages, so we can determine definitively what address the device will respond to. Similarly, I'd check the device variant marked on the component against the datasheet to confirm the register map. This usually resolves the discrepancy quickly because the hardware is what it is — the firmware can be changed, but the PCB is already fabricated.

Once we've established the facts, I'd assess the impact. If the hardware is correct and the firmware needs to change, I'd work with the firmware team to estimate the effort — changing the address and register map is usually a localized change, not a rewrite. I'd also check whether there's a way to make the firmware support both configurations temporarily, so that testing can start while the correct version is finalized. If the hardware is wrong, that's a bigger problem, but I'd still want to know immediately so we can plan around it.

Finally, I'd use this as a process improvement opportunity. The root cause is almost always a communication gap — the hardware team assumed one thing, the firmware team assumed another, and nobody verified the interface specification. I'd suggest adding an interface control document (ICD) review as a formal checkpoint before PCB fabrication, so that both teams sign off on the protocol details. But that's for the future — right now, the focus is on getting the facts, fixing the issue, and keeping the schedule as intact as possible.

**Possible follow-ups:** What if the firmware team's version is actually the one that matches the requirements document, and the hardware team made the error? How would you handle the schedule pressure if the fix requires a PCB revision?