# tools — Day 11

## Q1: How would you approach setting up an output job configuration in Altium Designer to streamline the release of fabrication and assembly files for a medical device PCB?

**Answer:** I'd start by defining the complete set of deliverables needed for a medical device release — that typically includes Gerber/ODB++ files, drill files, pick-and-place data, a Bill of Materials, and a fabrication drawing with stack-up and impedance requirements. In Altium Designer, I'd create a single Output Job file that consolidates all of these outputs, rather than generating them ad hoc from the PCB editor each time.

The key is to configure each output with the correct format and options for the target manufacturer. For example, Gerber files should use the RS-274X format with the appropriate precision (at least 2:5 or higher for fine-pitch parts), and I'd ensure the drill files are set to the same origin and units as the Gerbers. For the BOM, I'd configure the output to include manufacturer part numbers, supplier links, and any custom parameters that procurement needs — this is especially important for medical devices where component traceability is critical.

I'd also set up the output job to generate a PDF of the schematic and assembly drawings, since those are needed for the design history file (DHF) in a regulated environment. Once the output job is configured, I'd validate it by generating all outputs and reviewing them in a Gerber viewer (like Gerbv or the manufacturer's tool) before sending to the board house. Finally, I'd save the output job as part of the project so it's version-controlled and reproducible — every release should generate identical output formats, which matters for both regulatory audits and manufacturing consistency.

**Possible follow-ups:**
- How would you handle the case where different board houses require different output formats (e.g., one wants Gerber, another wants ODB++)?
- What specific checks would you perform on the generated fabrication files before submitting them?

---

## Q2: How would you approach using a spectrum analyzer with a near-field probe to identify the root cause of a radiated emissions failure at a specific frequency, say 120 MHz, during pre-compliance testing of a medical device?

**Answer:** I'd approach this systematically, starting with the assumption that 120 MHz is likely a harmonic of a lower-frequency clock or data signal — for example, a 30 MHz clock's 4th harmonic, a 40 MHz clock's 3rd harmonic, or a 60 MHz clock's 2nd harmonic. First, I'd set up the spectrum analyzer with the near-field probe and configure it to center on 120 MHz with a wide enough span (say 100–140 MHz) to see the emission and its surrounding spectrum. I'd use a resolution bandwidth of around 120 kHz, which matches the CISPR bandwidth for that frequency range, and a peak detector.

Then I'd begin the physical hunt: starting from the power input connector and working inward, I'd move the near-field probe across the board systematically, watching for the amplitude to peak. The key is to use both the H-field (loop) probe to find current paths and the E-field (rod) probe to find voltage nodes — they'll point to different parts of the problem. When I find a hot spot, I'd narrow the span to see if the emission is narrowband (indicating a clock harmonic) or broadband (indicating a data bus or switching noise).

Once I've localized the source, I'd determine the coupling path. For example, if the 120 MHz emission is strongest near a long trace carrying a 30 MHz clock, the trace is likely acting as an antenna. I'd then check whether the issue is poor return current path, inadequate decoupling, or a cable acting as an antenna. The fix depends on the root cause: series termination for ringing, better decoupling, a ground plane cut, or ferrite on an offending cable. I'd verify the fix by re-measuring with the probe, then confirm with a full pre-compliance scan.

**Possible follow-ups:**
- How would you distinguish between a differential-mode and common-mode emission when using near-field probes?
- What if the emission only appears when the device is in a specific operating mode — how would you narrow down the source then?

---

## Q3: How would you approach configuring a Zephyr RTOS project using the west build system for a medical device that needs to support multiple hardware revisions with different sensor configurations?

**Answer:** I'd use Zephyr's devicetree and Kconfig systems to manage the hardware variations cleanly. The core idea is to keep the application code hardware-agnostic and push all board-specific details into devicetree overlays and Kconfig fragments.

First, I'd create a base board definition for the common hardware — the MCU, power management, and core peripherals. Then, for each hardware revision, I'd create a devicetree overlay file that describes the differences: which sensors are present, their I2C addresses, interrupt pins, and any GPIO differences. For example, if revision A has a pressure sensor at I2C address 0x28 and revision B uses a different sensor at 0x29, those differences live entirely in the overlay files.

For build configuration, I'd use Kconfig fragments to set revision-specific options — for instance, which sensor driver to enable or what calibration constants to use. The west build command would then look something like `west build -b my_board -d build_rev_a -- -DOVERLAY_CONFIG=overlay-rev-a.conf -DDTC_OVERLAY_FILE=boards/my_board_rev_a.overlay`. I'd also set up a small build script or CMake wrapper that makes it easy to select the revision without remembering the exact flags.

The key benefit is that the application code reads from the devicetree API (e.g., `DEVICE_DT_GET`), so it doesn't care which sensor is actually present — it just uses the devicetree node label. This makes testing easier because you can build for any revision from the same source tree, and it makes the design history file cleaner because the hardware-software mapping is explicit and reviewable.

**Possible follow-ups:**
- How would you handle a hardware revision that changes the pin muxing of a shared peripheral, like moving an I2C bus to different pins?
- How would you verify that the correct overlay was applied during the build?

---

## Q4: How would you approach debugging a UART communication issue where the device intermittently sends corrupted data, but only when the system is under load — for example, when a motor is running in a medical device?

**Answer:** I'd start by characterizing the failure — is it bit-level corruption, missing bytes, or framing errors? That distinction points to different root causes. I'd use a logic analyzer to capture the UART TX line and compare the actual waveform against the expected protocol. If the corruption is bit-level, I'd look at the timing: measure the bit width and check for jitter or edge distortion. If bytes are missing or framing errors occur, that suggests a firmware issue like interrupt starvation or a buffer overrun.

Since the problem correlates with the motor running, I'd suspect one of three things: electrical noise coupling into the UART lines, ground bounce or power supply sag affecting the transceiver, or firmware timing issues where the motor control code is blocking UART handling.

For the electrical path, I'd use an oscilloscope with a ground spring (not a long ground lead) to probe the UART lines directly, looking for noise spikes that coincide with motor commutation events. I'd also probe the power rails — if the motor causes the 3.3V rail to droop or ring, that could corrupt the UART levels. I'd check whether the UART lines are routed near the motor drive traces on the PCB, and whether there's adequate decoupling on the motor driver supply.

For the firmware path, I'd review the interrupt priorities and timing — if the motor control uses a high-priority interrupt that runs frequently, it could delay UART character transmission beyond the acceptable window. I'd also check whether the UART driver uses DMA or interrupt-driven TX, and whether the TX buffer can be starved during motor operation.

The systematic approach is to isolate variables: run the motor with the UART disconnected (does the corruption still occur on a loopback?), run the UART without the motor (does it work cleanly?), then combine them and probe at each stage. This separates electrical coupling from firmware timing issues.

**Possible follow-ups:**
- How would you determine whether the issue is on the TX side or the RX side of the UART link?
- What specific oscilloscope settings would you use to capture intermittent noise correlated with motor commutation?

---

## Q5: (Behavioral) Imagine you are leading the bring-up of a new medical device prototype, and you discover that the MPLAB IDE project configuration has a critical issue — the compiler optimization level is set to `-O2` instead of the `-O0` that was used during development and testing. The firmware has been running for several days of testing, and the team is about to start formal verification. A junior engineer set up the project and is confident the optimization level doesn't matter because "the code works fine." How would you handle this situation?

**Answer:** I'd approach this carefully, because there are two distinct issues: the technical risk of the optimization level change, and the team dynamic with the junior engineer.

On the technical side, I'd explain that changing compiler optimization can expose latent bugs — timing-sensitive code, volatile access, or undefined behavior can behave differently at `-O2` versus `-O0`. In a medical device, this is exactly the kind of change that could cause intermittent failures during formal verification, which is far more costly to address than catching it now. I'd also point out that the verification results from the `-O2` build can't be directly compared to the development results from `-O0` — the test evidence wouldn't be consistent, which matters for regulatory documentation.

On the team dynamic side, I'd acknowledge the junior engineer's confidence and avoid making it personal. I'd frame it as a process question: "The code may work fine, but the question is whether we can prove it works fine." I'd suggest a concrete experiment — build at both optimization levels and run the full test suite on each, comparing results. If the tests pass at both levels, we still need to decide which one to standardize on, and I'd recommend `-O0` for the verification phase to match the development environment, then potentially re-verify at `-O2` later if we want the performance benefit.

I'd also use this as a teaching moment about configuration management — the project settings should be documented, reviewed, and controlled, especially for a medical device where the design history file needs to capture exactly how the firmware was built. I'd propose adding a build configuration checklist to the bring-up process so this kind of discrepancy is caught earlier in the future.

**Possible follow-ups:**
- What if the junior engineer pushes back and says the `-O2` build is actually more representative of the final product, since that's what will be shipped?
- How would you document this issue and the resolution in the project's design history file?