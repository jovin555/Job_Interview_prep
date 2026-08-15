# tools — Day 25

## Q1: How would you approach setting up a Zephyr RTOS project to support runtime calibration of an analog sensor front-end, where the calibration coefficients need to be stored in flash and survive firmware updates?

**Answer:** I'd structure this around three concerns: where calibration data lives, how it's accessed, and how it survives the update process.

For storage, I'd use Zephyr's settings subsystem (or a dedicated flash partition via the Flash Map API) rather than embedding calibration in the firmware image itself. This keeps calibration data separate from code, so a firmware update doesn't overwrite it. I'd define a dedicated flash partition for calibration data, separate from the boot partition and the application slot.

For access, I'd create a small calibration management module that provides a clean API — something like `calib_load()`, `calib_save()`, and `calib_get_channel_coefficient()`. The module would handle the flash read/write operations, including wear leveling considerations if calibration is updated frequently. I'd also include a checksum or CRC over the calibration block so the system can detect corruption and fall back to factory defaults.

For the update path, I'd make sure the bootloader (MCUboot, if used) is configured to preserve the calibration partition during swap operations. I'd also add a version field to the calibration data structure so the firmware can detect format mismatches after an update and trigger a re-calibration if needed.

A key design decision is whether calibration happens in the factory only, or in the field. If field calibration is supported, I'd add a "calibration mode" to the firmware that disables safety-critical functions while calibration is in progress, and I'd require a validation step before new coefficients are committed to flash.

**Possible follow-ups:**
- How would you handle the case where a firmware update changes the calibration data format?
- What considerations would you have for storing calibration data in a device that must meet IEC 60601 requirements?

---

## Q2: How would you approach using a spectrum analyzer with a near-field probe to determine whether a radiated emissions failure at 320 MHz is coming from a 40 MHz clock's 8th harmonic or from a switching regulator's switching frequency harmonic?

**Answer:** The first step is to identify all potential sources that could produce energy at 320 MHz. A 40 MHz clock's 8th harmonic is one candidate; a switching regulator at, say, 2 MHz would need its 160th harmonic, which is less likely to be a strong contributor unless there's a specific coupling path. But I wouldn't assume — I'd verify.

My approach would be:

1. **Measure the fundamental frequencies.** Use the near-field probe to locate the 40 MHz clock source and confirm its fundamental. Then locate the switching regulator and measure its fundamental switching frequency. This gives me the exact harmonic relationships.

2. **Use a spectrum analyzer with a wide enough span and narrow RBW.** I'd set the center frequency to 320 MHz with a span of maybe 50–100 MHz to see the emission's shape and whether there are adjacent harmonics visible. A narrow RBW (around 100–120 kHz for a peak measurement) helps resolve the signal.

3. **Check for harmonic spacing.** If I see emissions at 320 MHz, 360 MHz, and 400 MHz, that spacing of 40 MHz strongly suggests the clock. If I see a series of emissions spaced by the regulator's fundamental frequency, that points to the regulator.

4. **Use time-domain correlation.** If the analyzer has a zero-span mode, I can set it to 320 MHz and observe the emission's time behavior. If the emission appears only when the clock is active (e.g., during specific operations), that's a strong clue. I could also temporarily disable the clock or the regulator (if the design allows) to see if the emission disappears.

5. **Probe the specific traces.** I'd move the near-field probe along the clock trace and the regulator's output trace, measuring the amplitude at 320 MHz at each location. The source with the strongest coupling to the emission frequency is the likely culprit.

6. **Confirm with a current probe or differential measurement.** If I have access to a current probe, I can measure the common-mode current on the cable or the power input, which is often the actual radiation path.

The key is not to jump to conclusions based on harmonic math alone — the coupling path and the actual energy distribution matter more than the theoretical harmonic relationship.

**Possible follow-ups:**
- What if both sources are active simultaneously and you can't disable either one?
- How would you use a preamplifier or a different probe type to improve your measurement sensitivity?

---

## Q3: How would you approach setting up a Git-based workflow for a firmware project that needs to support multiple hardware revisions, where each revision has different sensor configurations and pin mappings, while maintaining a single codebase and ensuring that the correct configuration is built for each revision?

**Answer:** I'd use a combination of Kconfig (Zephyr's configuration system) and device tree overlays to handle hardware variation, with Git branches or tags used only for release management, not for maintaining divergent code paths.

The core principle is: **one codebase, multiple configurations**. The application code should be written against abstract interfaces (e.g., sensor APIs), and the hardware-specific details should live in configuration files.

My approach:

1. **Device tree overlays per hardware revision.** I'd create a `boards/` directory with overlay files like `revision_a.overlay`, `revision_b.overlay`, etc. Each overlay defines the specific sensor instances, their addresses, and pin mappings for that revision. The build system selects the overlay based on a Kconfig option or a build-time variable.

2. **Kconfig options for hardware selection.** I'd add a Kconfig option like `CONFIG_HW_REVISION` that selects which overlay and which driver configurations get used. This keeps the selection explicit and auditable.

3. **Driver abstraction.** The application code calls generic sensor APIs (e.g., `sensor_sample_fetch()`, `sensor_channel_get()`). The actual driver instances are defined in the device tree, so the application doesn't care whether a sensor is on I2C or SPI, or which address it uses.

4. **Build scripts or CMake presets.** I'd provide build scripts or CMake presets that map a hardware revision name to the correct overlay and Kconfig fragment. For example, `west build -b my_board -- -DCONFIG_HW_REVISION=rev_b`.

5. **Git workflow.** The main branch contains all revisions. Each release is tagged (e.g., `v1.2.0-rev_a`, `v1.2.0-rev_b` or a single tag with a manifest of supported revisions). If a hardware revision is discontinued, I'd remove its overlay in a dedicated commit rather than branching.

6. **CI verification.** I'd set up CI to build all supported hardware revisions on every commit, so a change that breaks one revision is caught immediately.

The key trade-off is between code simplicity and configuration complexity. The device tree approach keeps the code clean but requires discipline in maintaining overlays. The alternative — `#ifdef` in code — quickly becomes unmaintainable as the number of revisions grows.

**Possible follow-ups:**
- How would you handle a hardware revision that requires a different sensor driver entirely, not just a different address?
- How would you ensure that a firmware build for revision A never accidentally runs on revision B hardware?

---

## Q4: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first thing I'd do is stop the clock on the "who's right" debate and focus on getting the facts verified. Both teams being confident doesn't matter — what matters is what the hardware actually does and what the firmware actually expects.

My approach:

1. **Get the authoritative sources on the table.** I'd ask the hardware team to produce the schematic page showing the sensor's address pins and the datasheet section for the I2C addressing mode. I'd ask the firmware team to show me the exact register read/write sequences they're using and the device tree or configuration where the address is defined. The goal is to compare the two against the sensor's datasheet, not against each other's claims.

2. **Verify against the datasheet, not against memory.** In my experience, these mismatches usually come from one team reading a preliminary datasheet revision or misinterpreting a register description. The sensor's official datasheet is the ground truth. I'd have both teams point to the specific page that supports their interpretation.

3. **Assess the actual impact.** If the hardware is truly 10-bit and the firmware is 7-bit, the device won't respond at all — that's a hard failure, not an intermittent one. But there's a subtler possibility: the sensor might support both 7-bit and 10-bit modes, and the address pins might be strapped for one mode while the firmware uses the other. In that case, the fix might be as simple as changing a device tree entry or a `#define`.

4. **Determine the fastest safe path to resolution.** If the hardware is correct and the firmware is wrong, the fix is a firmware change — which is quick if it's just an address or register map change. If the hardware is wrong (e.g., address pins strapped incorrectly), that's a PCB rework or a firmware workaround if the sensor supports multiple addresses. I'd evaluate both options against the two-day deadline.

5. **Make the call and document it.** Once the facts are clear, I'd make a decision and communicate it clearly to both teams. I'd also document the discrepancy and the resolution in the project's issue tracker, because this kind of interface mismatch is exactly what a requirements traceability matrix is supposed to catch.

6. **Prevent recurrence.** After the immediate issue is resolved, I'd review how the interface specification was communicated between teams. Was there an ICD (Interface Control Document)? Was it reviewed? This is a process gap, not just a technical one.

The key is to remain neutral and fact-focused. If I take sides based on which team I trust more, I risk alienating the other team and missing the actual root cause.

**Possible follow-ups:**
- What if the hardware team insists the PCB is correct and the firmware team insists their code is correct, and neither will budge?
- How would you handle this if the sensor's datasheet is ambiguous about the addressing mode?

---

## Q5: How would you approach setting up a Segger J-Link debugger to capture a real-time trace of a Zephyr RTOS-based system's thread scheduling behavior without halting the CPU or modifying the firmware?

**Answer:** The key constraint here is "without halting the CPU" — that rules out traditional breakpoint-based debugging and points toward trace-based debugging. The J-Link supports two relevant technologies: ETM (Embedded Trace Macrocell) for instruction trace and ITM (Instrumentation Trace Macrocell) for software-generated trace data. For thread scheduling behavior, I'd use a combination of both.

My approach:

1. **Check target support.** First, I'd verify that the target microcontroller supports ETM or at least ITM, and that the J-Link model I have supports the required trace interface (J-Trace models support ETM; standard J-Link models typically support ITM but not full ETM). If the target doesn't support hardware trace, I'd need to fall back to a software-based approach.

2. **Configure ITM for RTOS-aware tracing.** Zephyr has built-in support for tracing via ITM (the `CONFIG_TRACING` and `CONFIG_TRACING_ITM` options). This enables the RTOS to emit trace events (thread switches, thread creation, semaphore operations) through the ITM stimulus ports. I'd enable these in the build configuration.

3. **Set up the J-Link trace capture.** Using J-Link Commander or the Ozone debugger, I'd configure the trace capture:
   - Enable ITM stimulus ports for the RTOS trace events.
   - Set the trace clock and SWO (Single Wire Output) pin configuration to match the target's debug header.
   - Configure the trace buffer size and capture mode (streaming to host or on-target buffer).

4. **Use Ozone's RTOS-aware trace view.** Ozone can decode Zephyr's trace events and display thread scheduling in a timeline view, showing when each thread runs, when it blocks, and what the RTOS was doing at each point. This gives me the scheduling behavior without any breakpoints or code modifications.

5. **Correlate with system events.** If I need to correlate scheduling with external events (e.g., a sensor interrupt), I'd use the ITM's timestamp feature and also capture GPIO toggles or other hardware events through the trace system.

6. **Fallback if hardware trace isn't available.** If the target lacks ETM/ITM support, I'd use Zephyr's software tracing (e.g., `CONFIG_TRACING_CTF` for CTF format) and capture to a RAM buffer, then dump the buffer after the fact. This does require some firmware modification, but it's minimal and doesn't halt the CPU during normal operation.

The main trade-off is between trace depth and trace fidelity. Full ETM gives instruction-level detail but requires more bandwidth and a J-Trace probe. ITM-based tracing gives RTOS-level events with much lower overhead and works with a standard J-Link.

**Possible follow-ups:**
- How would you handle the case where the trace buffer overflows during a long capture?
- What if the target microcontroller doesn't have a dedicated SWO pin routed on the PCB — how would you work around that?