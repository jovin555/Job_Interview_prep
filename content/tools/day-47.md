# tools — Day 47

## Q1: How would you approach setting up a repeatable firmware build and release process for a medical device that uses Zephyr RTOS, where you need to produce auditable artifacts for regulatory purposes?

**Answer:** For a medical device, the build process itself is part of the design history file, so reproducibility and traceability are the primary drivers. I'd start by establishing a single source of truth for the toolchain — pinning the Zephyr SDK version, the west workspace manifest, and all tool versions in a way that can be exactly reproduced months or years later. The west manifest file is key here; it should reference specific commit SHAs for Zephyr and all modules, not branches or tags that could move.

For the build itself, I'd use a containerized build environment so that the build host's OS updates or library changes can't silently alter the output. The build script would capture metadata as part of the artifact: the git commit hash of the application code, the west manifest SHA, the toolchain version, the exact build configuration (via the generated `.config` file from Kconfig), and a timestamp. This metadata should be embedded in the firmware image itself, not just stored alongside it, so you can identify what's running on a device in the field.

For regulatory traceability, I'd generate a build manifest that maps the firmware binary to the specific source revision, configuration, and toolchain. This manifest, along with the binary, gets stored in a release management system with a unique version identifier. The process should also produce a checksum or hash of the binary so that the released artifact can be verified against what was actually tested. I'd also make sure the build is deterministic — meaning the same inputs always produce the same binary — which requires attention to things like build paths, timestamps embedded in the build, and any generated files that might vary between builds.

Finally, I'd separate the development build process from the release build process. Development builds can use the latest code and debug options, but release builds should only be produced from tagged, reviewed commits through the controlled pipeline. This prevents someone from accidentally shipping a binary that wasn't built through the auditable process.

**Possible follow-ups:** How would you handle the case where a field-returned device needs to be matched to its exact firmware build? What metadata would you consider essential to embed in the firmware image itself?

---

## Q2: How would you approach using a mixed-signal oscilloscope to characterize noise coupling between a switching regulator and a precision analog sensor on the same PCB, and how would you determine whether the coupling is conducted, radiated, or through the ground plane?

**Answer:** This is a classic mixed-signal debugging scenario where the measurement setup is as important as the measurement itself. I'd start by establishing a clean trigger source — typically the switching node of the regulator — and then look at the analog sensor output or its supply rail in the time domain, synchronized to that trigger. The key is to see whether noise events on the sensor correlate with specific switching edges.

To determine the coupling path, I'd use a structured elimination approach. First, I'd measure at multiple points simultaneously: the switching node, the input and output of the regulator, the analog supply rail after any filtering, the sensor output, and the ground reference at both the regulator and the sensor. Using multiple channels with proper probing technique — short ground springs on passive probes, not long ground leads — is essential to avoid measuring the probe's own pickup.

For conducted coupling, I'd look for noise on the supply rail that correlates with switching, and I'd check whether adding a ferrite bead or additional filtering at the point of load changes the sensor noise. For radiated coupling, I'd use a near-field probe to sniff around the board while the system is running, looking for field strength near the regulator, the sensor traces, or the traces between them. For ground-plane coupling, I'd probe the voltage difference between two ground points — one near the regulator and one near the sensor — using a differential measurement, since a single-ended probe referenced to the same ground point won't reveal ground bounce.

A useful technique is to temporarily modify the board — cutting a trace, lifting a component, or adding a jumper — to isolate a suspected coupling path. For example, if I suspect ground coupling, I might separate the analog and digital ground sections and measure the noise with them connected at different points. If I suspect radiated coupling, I might shield the sensor or its traces with copper tape and see if the noise changes.

I'd also use the oscilloscope's FFT function to look at the frequency content of the noise. Switching regulator noise tends to appear at the switching frequency and its harmonics, while ground bounce often shows up as broadband noise with a different spectral signature. Correlating the frequency domain with the time domain helps confirm the mechanism.

**Possible follow-ups:** How would you distinguish between noise coupling through the ground plane versus coupling through the shared power supply impedance? What probing technique would you use to measure a small differential voltage across a ground plane without introducing measurement error?

---

## Q3: How would you approach setting up a component library management strategy in KiCad for a medical device project that needs to maintain strict revision control and regulatory traceability, given that KiCad's library format is file-based rather than database-driven?

**Answer:** KiCad's file-based library system actually lends itself well to version control, but it requires deliberate structure and discipline. The key principle is that the library itself must be treated as a controlled artifact, not something individual engineers modify casually on their local machines.

I'd start by establishing a shared library repository, separate from any individual project, that is version-controlled with Git. The repository would contain schematic symbols, footprints, and 3D models, each with a clear directory structure. The critical part is the review process: changes to any library component go through a pull request, and the change is documented with a reason — for example, "updated footprint pad size to match manufacturer recommendation" or "corrected pin assignment for the ADC." This creates an audit trail of why a component changed, which is essential for regulatory traceability.

For medical device work, I'd add a traceability layer that links each library component to its source documentation. This could be a field in the symbol or footprint properties that references the manufacturer part number, the datasheet revision, and the date the component was validated. When a component is used in a design, that information flows into the BOM and the design files, so you can always trace a component on a board back to its original specification.

Within a project, I'd use KiCad's library tables to point to the shared repository, not to local copies. This ensures everyone uses the same component definitions. For release builds, I'd tag the library repository at the same time as the project repository, so you can always reconstruct the exact library state that was used for a particular design release.

One important consideration is that KiCad libraries are text files, which means they can be diffed and reviewed in Git. But they can also be corrupted or edited in ways that don't show up clearly in a diff. I'd use KiCad's built-in validation tools — the symbol and footprint checkers — as part of the CI process to catch issues before they reach the shared library.

**Possible follow-ups:** How would you handle a situation where a component needs to be updated in the shared library while a design using the old version is already in fabrication? What metadata would you store in the library components to support regulatory traceability?

---

## Q4: How would you approach setting up a hardware-in-the-loop (HIL) test environment for a medical device that needs to verify firmware behavior against simulated sensor inputs, and what are the key considerations for making the tests meaningful and repeatable?

**Answer:** A HIL test environment for a medical device needs to bridge the gap between pure software simulation and full hardware testing. The goal is to exercise the real firmware on the real microcontroller while controlling the sensor inputs deterministically, so you can verify behavior under conditions that would be difficult or unsafe to create with real sensors.

The first decision is the interface between the simulator and the device under test. For a device with analog sensors, I'd use a precision DAC or a programmable signal generator to produce the sensor signals, with careful attention to output impedance and noise — the simulator shouldn't introduce artifacts that the real sensor wouldn't produce. For digital sensors, I'd use a microcontroller or FPGA to emulate the sensor's protocol behavior, which gives you the ability to inject protocol errors, timing violations, and edge cases that would be hard to create with a real sensor.

The key to meaningful HIL testing is the test harness design. I'd structure the tests around scenarios, not just individual inputs. For example, in a device that monitors physiological parameters, a test scenario might be "simulate a gradual signal drift over 30 minutes followed by a sudden drop," which exercises both the filtering algorithms and the alarm thresholds. Each scenario needs a defined pass/fail criterion that is objective and measurable — not "the device behaves reasonably" but "the device generates an alarm within 2 seconds of the signal crossing the threshold."

Repeatability requires controlling everything that could vary between runs. This includes the timing of the simulated inputs, the initial state of the device, and the ambient conditions. I'd use a test sequencer that runs the same scenario multiple times and checks for consistency, not just a single pass. For a medical device, I'd also want to verify that the device handles the transition between simulated and real inputs correctly — for example, when you disconnect the simulator and connect a real sensor, the device shouldn't glitch or reset.

Another important consideration is fault injection. A HIL environment should be able to simulate sensor failures — open circuits, short circuits, out-of-range values, intermittent connections — to verify that the firmware handles these gracefully. This is where the HIL environment provides value that you can't get from bench testing with real sensors, because you can't easily make a real sensor fail in a controlled, repeatable way.

Finally, I'd make sure the HIL test results are captured in a way that supports regulatory submission. Each test run should produce a log that ties the test scenario, the device configuration, the firmware version, and the pass/fail result together in a single auditable record.

**Possible follow-ups:** How would you verify that the HIL simulator is accurately representing the real sensor's behavior? What types of fault injection would you consider essential for a medical device's HIL test suite?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first thing I'd do is stop the discussion about whose implementation is "correct" and focus on establishing the facts. Both teams are confident, which tells me that each side has been working from some reference — a datasheet, an application note, an evaluation board, or a previous project — and the references don't match. I'd call a meeting with both teams and ask each to bring their reference documentation: the hardware team's schematic and the sensor datasheet section showing the addressing mode, and the firmware team's driver code and the reference they used to write it.

In that meeting, I'd put the documents side by side and walk through the discrepancy systematically. The goal isn't to assign blame but to identify where the divergence happened. It might be that the hardware team selected a different sensor variant than the firmware team assumed, or that the firmware team's driver was copied from a different project and the address configuration was never updated. Once we identify the source of the divergence, we can determine what actually needs to change.

With integration testing in two days, I'd then assess the options pragmatically. If the hardware is already fabricated and the sensor variant is fixed, then the firmware needs to be updated to match — that's the only option if the hardware can't be changed. If the hardware is still in fabrication or the sensor can be swapped, there might be more flexibility, but I'd be cautious about changing hardware at this stage because it could introduce new issues.

I'd also consider whether there's a way to make the system work with both configurations temporarily. For example, if the firmware can be written to auto-detect the addressing mode during initialization, that might buy time for integration testing to proceed while the permanent fix is implemented. But I'd be careful about adding complexity at the last minute — a temporary workaround that isn't fully tested can be worse than delaying integration.

The key leadership aspect here is managing the teams' confidence without dismissing their work. I'd acknowledge that both teams did what they believed was correct based on their references, and the issue is a communication gap, not incompetence. I'd also make sure the fix is documented thoroughly, so the same class of problem doesn't recur. After the immediate issue is resolved, I'd suggest a process improvement — perhaps a formal interface control document that specifies the exact protocol parameters, addressing modes, and register maps, signed off by both teams before hardware design and firmware development proceed independently.

**Possible follow-ups:** How would you handle the situation if the firmware team's approach is actually more correct for the intended clinical use, but the hardware is already in fabrication? What process changes would you recommend to prevent this class of issue in future projects?