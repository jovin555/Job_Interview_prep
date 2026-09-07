# tools — Day 48

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** For a medical device, the build process itself becomes part of the design history file, so reproducibility and traceability are the primary drivers. I'd start by establishing a single source of truth for the toolchain — pinning the Zephyr SDK version, the west workspace manifest, and all tool versions in the repository so that a build performed six months from now produces byte-identical output. The west manifest should reference specific commit SHAs for Zephyr and any modules, not floating branches or tags that could move.

For the build itself, I'd use a containerized build environment (Docker or similar) so that the build doesn't depend on whatever happens to be installed on a particular engineer's machine. The container definition itself gets version-controlled and reviewed. The build script would invoke west build with a fixed configuration, then generate a build manifest that records: the git commit of the application code, the west manifest SHA, the container image hash, the Zephyr version, the compiler version, and a hash of the resulting binary. That manifest gets stored alongside the binary as the auditable artifact.

For regulatory traceability, I'd tag releases in git with a signed tag, and the release process would require that the binary hash in the release notes matches the hash produced by the build. I'd also set up the build to fail on warnings, so that the output is deterministic and doesn't depend on compiler warning state. Finally, I'd separate the production build from development builds — the production build would disable debug features, enable appropriate optimization, and include only the code paths intended for the released device, while development builds could add logging and test hooks without affecting the release configuration.

**Possible follow-ups:**
- How would you handle the case where a field issue requires rebuilding an older firmware version that was built with a now-obsolete toolchain?
- What metadata would you embed in the firmware image itself to support post-market traceability?

---

## Q2: How would you approach using a logic analyzer to debug a USB 2.0 device that enumerates correctly on some hosts but fails on others, where the failure is intermittent and appears to be timing-related?

**Answer:** This kind of host-dependent, intermittent enumeration failure usually points to timing margins being marginal rather than a protocol-level logic error. I'd start by capturing the full enumeration sequence on a host where the device fails, using a logic analyzer with USB 2.0 protocol decoding. The key is to capture from the very first attach event — the device connecting to the bus — through the full enumeration sequence, including the host sending SETUP packets and the device responding.

I'd look specifically at the timing of the device's responses to host requests. USB has defined timeouts — for example, the device must respond to a SETUP packet within a certain window, and the host may retry or give up if responses come too late. I'd measure the time from the end of the host's token packet to the start of the device's response, and compare that against the USB specification limits. If the device is consistently responding near the edge of the timeout window, that explains why some hosts — which may have slightly different timer implementations or polling intervals — succeed while others fail.

I'd also check the timing of the device's chirp sequence during reset, since that's where speed negotiation happens. If the device is slow to assert chirp or the chirp timing is marginal, some hosts may interpret it as a full-speed device while others correctly detect high-speed. I'd also look at the frame timing — whether the device is sending SOF responses or other periodic traffic that could collide with host polling.

If the timing measurements show marginal margins, I'd investigate the firmware's USB interrupt handling — perhaps the USB interrupt priority is too low and gets delayed by other activity, or the endpoint buffer management has a race condition. I'd also check the hardware side: the D+ pull-up resistor value, the crystal accuracy, and whether the VBUS decoupling is adequate. The fix might be in firmware (optimizing the interrupt path), in hardware (adjusting pull-up or adding decoupling), or in configuration (ensuring the device descriptor fields are consistent with what the host expects).

**Possible follow-ups:**
- How would you distinguish between a firmware timing issue and a hardware signal integrity issue when the logic analyzer shows clean digital transitions?
- What specific USB descriptor fields would you check if the device enumerates but the host rejects a particular configuration?

---

## Q3: How would you approach setting up a component library management strategy in KiCad for a medical device project that needs to maintain strict revision control and regulatory traceability, given that KiCad's library format is file-based rather than database-driven?

**Answer:** KiCad's file-based libraries actually fit well with git-based revision control, which is what you want for regulatory traceability anyway. The key is to treat the libraries as first-class project artifacts, not as loose files that live on individual engineer's machines. I'd structure the libraries as a separate repository — or a clearly separated directory within the project repository — containing the schematic symbol libraries (.kicad_sym), footprint libraries (.kicad_mod), and 3D models (.step or .wrl files).

For traceability, each component needs a unique identifier that ties the schematic symbol to its footprint, its 3D model, and its datasheet. KiCad's field system supports this — I'd add custom fields to each symbol for the manufacturer part number, the datasheet URL or file path, and a component ID that maps to the Bill of Materials. The critical part is that the symbol and footprint must be linked through the footprint field in the symbol, and that link must be verified during the design review.

For revision control, I'd use git with a clear branching strategy. The library repository would have a main branch that represents the released state, and changes go through pull requests with review. Each component change gets a commit message that references the change request or design decision that motivated it. When a component is used in a design, the design's schematic file records which version of the library was used — KiCad stores the library nickname and the symbol name, so as long as the library is versioned, you can trace which component definition was used in a particular design release.

I'd also set up automated checks in the CI pipeline: verify that every symbol in the schematic has a corresponding footprint, that the footprint has a 3D model, and that the BOM generation succeeds. For medical devices, I'd add a manual review step where a second engineer verifies that the symbol pinout matches the datasheet before a component is approved for use in the library. This is especially important for components like microcontrollers where a pin mapping error could be catastrophic.

**Possible follow-ups:**
- How would you handle a component that needs a footprint variation — for example, the same part number available in different package sizes?
- What would you do if you needed to use a component that isn't yet in the approved library and the project timeline is tight?

---

## Q4: How would you approach using a mixed-signal oscilloscope to characterize the noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** This is a classic mixed-signal debugging scenario, and the approach needs to be systematic because the three coupling mechanisms — conducted, radiated, and ground — require different mitigation strategies. I'd start by setting up the oscilloscope to capture both domains simultaneously: one channel on the switching regulator's output or switching node, and another channel on the analog sensor's output or supply pin. The goal is to see whether noise events on the regulator correlate in time with noise on the sensor.

The first test is to determine if the coupling is conducted through the power supply. I'd measure the noise on the sensor's supply pin while the regulator is switching, then insert additional filtering — for example, a ferrite bead or an LC filter — between the regulator output and the sensor supply. If the noise on the sensor output drops significantly, the coupling is primarily conducted through the power rail. If it doesn't change, the coupling is likely through another path.

For radiated coupling, I'd use a near-field probe connected to the oscilloscope's input, or use the scope's FFT function to look at the frequency content of the noise. If the noise frequency matches the switching frequency or its harmonics, and the amplitude changes when I move a ground plane or shield between the regulator and the sensor, that suggests radiated coupling. I'd also try moving the sensor's input leads or changing the probe position to see if the coupling is spatial.

For ground plane coupling, the key measurement is the voltage difference between different points on the ground plane. I'd use two probes in differential mode — or a differential probe — to measure the voltage between the sensor's ground reference point and the regulator's ground return point. If there's a significant voltage difference at the switching frequency, that indicates ground bounce or ground plane impedance issues. I'd also look at where the sensor's ground connection is relative to the regulator's ground return — if they share a section of the ground plane, the regulator's return current can modulate the sensor's ground reference.

The most important measurement is the time-correlation between the switching event and the noise on the sensor. If the noise appears exactly at the switching edge, that tells you the coupling is synchronous with the switching action. If it appears with a delay, it might be coupling through a slower path like thermal effects or a control loop interaction. I'd also vary the load on the regulator — changing the load current changes the di/dt and can help identify whether the coupling scales with current slew rate.

**Possible follow-ups:**
- How would you use the oscilloscope's FFT function to identify the specific harmonic of the switching frequency that's causing the most interference?
- What modifications would you try first if the measurements suggest ground plane coupling is the dominant path?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first priority is to stop the clock on assumptions and get the facts on the table in a way that doesn't put either team on the defensive. I'd call a meeting with both teams' leads and the engineers who made the respective decisions, and I'd frame it as a discovery session, not a blame session. The goal is to determine which implementation is actually correct for the hardware that's in hand — not which team followed the right process.

I'd start by asking both teams to show their evidence. The firmware team should be able to point to the sensor datasheet and the register map they implemented against. The hardware team should be able to show the schematic and the actual device variant that was selected and placed on the board. In many cases, this kind of discrepancy comes from a documentation mismatch — perhaps the hardware team used a different sensor variant than the firmware team assumed, or the datasheet was updated between when the hardware was designed and when the firmware was written.

Once we've established which implementation matches the actual hardware, the decision becomes clearer. If the hardware is correct for the device that's physically on the board, then the firmware needs to change — but I'd want to understand the scope of that change. If it's just an address and register map change, that might be a one-day fix. If the firmware was built around a fundamentally different data model, it could be more involved. Conversely, if the hardware has the wrong sensor variant or the address pins are strapped incorrectly, that's a hardware change that might require a board respin — which is a much bigger schedule impact.

The key leadership move here is to avoid letting the two teams dig into their positions. I'd redirect the conversation from "who is right" to "what does the hardware on the bench actually require, and what's the fastest safe path to get there?" I'd also make sure the decision is documented — a short memo capturing the discrepancy, the evidence, the decision, and the rationale — so that the same issue doesn't resurface during the next integration cycle. Finally, I'd use this as a process improvement opportunity: the fact that this discrepancy survived until two days before integration suggests the interface control document or the hardware-firmware handoff process needs strengthening.

**Possible follow-ups:**
- How would you handle the situation if the firmware change is more extensive than can be completed in two days, and the integration test date is fixed?
- What specific documentation or process changes would you propose to prevent this class of hardware-firmware interface mismatch in future projects?