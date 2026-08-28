# tools — Day 38

## Q1: How would you approach setting up a Zephyr RTOS project to support both a production build and a development build with different sensor configurations, where the development build includes additional debug logging and a mock sensor driver, without maintaining two separate codebases?

**Answer:** I'd use Zephyr's Kconfig and devicetree overlay system to handle this cleanly. The core approach is to keep the production configuration as the default in the base project files, then create a separate overlay directory for development that adds debug features and swaps in mock drivers.

Concretely, I'd structure it like this: the base `prj.conf` and base devicetree `.dts` contain the production sensor configuration. For development, I'd create a `boards/` overlay file (e.g., `app.overlay`) that redefines the sensor node to use a mock driver compatible with the same API, and a `prj_dev.conf` that enables `CONFIG_LOG`, `CONFIG_ASSERT`, and any debug shell or tracing features. The mock driver would implement the same sensor driver API — same init, read, and configuration functions — so the application layer doesn't change.

With the west build system, I'd define two build configurations, either using CMake presets or a simple script that invokes west with different `-d` build directories and `-DOVERLAY_CONFIG` / `-DDTC_OVERLAY_FILE` flags. For example: `west build -d build/prod -b <board> .` for production, and `west build -d build/dev -b <board> . -DOVERLAY_CONFIG=prj_dev.conf -DDTC_OVERLAY_FILE=boards/dev.overlay` for development.

The key design principle is that the mock driver must be a drop-in replacement — same return codes, same data formats, same timing behavior as much as practical. If the mock behaves differently from the real sensor, you'll debug issues in development that don't exist in production, or worse, miss issues that do. I'd also make sure the devicetree node for the sensor is structured so that the driver binding is the only thing that changes between configurations, not the sensor's register map or communication protocol.

For CI, I'd have both configurations built automatically on every commit so that development-only changes don't accidentally break the production build, and vice versa.

**Possible follow-ups:**
- How would you ensure that the mock sensor driver doesn't accidentally get included in the production build?
- How would you handle the case where the development build needs a different sensor communication bus (e.g., I2C vs. SPI) than production?

---

## Q2: How would you approach using a logic analyzer to debug a USB 2.0 device that enumerates correctly on some hosts but fails on others, where the failure is intermittent and appears to be timing-related?

**Answer:** USB enumeration timing failures that are host-dependent are classic symptoms of marginal signal integrity or timing margins. I'd approach this systematically.

First, I'd capture the full enumeration sequence on both a host that works and a host that fails, using a logic analyzer with USB 2.0 protocol decoding. The key is to capture from the very first connect event — the device's D+ pull-up assertion — through the full enumeration sequence: reset, SETUP packets, device descriptor requests, configuration, etc. I'd compare the two captures side-by-side, looking for differences in timing, packet retries, or where the sequence diverges.

Common things I'd look for: the device's response time to a SETUP packet (the device has a fixed time budget to respond), the timing of the device's pull-up assertion relative to VBUS application, and whether the device is sending any NAKs or STALLs that might indicate it's not ready. I'd also check for bit stuffing errors or CRC failures that might indicate marginal signal quality.

If the logic analyzer shows the device is responding but the host gives up, I'd look at the host's timeout behavior — some hosts are more lenient than others. If the device is slow to respond, the issue might be in firmware — for example, the USB interrupt handler being delayed by other higher-priority interrupts, or the device not being fully initialized before it asserts the pull-up.

I'd also use an oscilloscope with differential probes on D+/D- to check signal quality — rise times, eye diagram, and voltage levels — because a logic analyzer can decode the protocol but won't show you analog signal integrity issues. A marginal signal might decode fine on one host's receiver but fail on another with tighter thresholds.

Finally, I'd check the device's power supply — if the device is bus-powered, inrush current during connect can cause VBUS droop on some hosts, which can cause enumeration failures. A scope capture of VBUS during connect would reveal this.

**Possible follow-ups:**
- How would you distinguish between a firmware timing issue and a hardware signal integrity issue from the logic analyzer capture alone?
- What specific USB 2.0 timing parameters would you measure to quantify the margin?

---

## Q3: How would you approach setting up a component library management strategy in KiCad for a medical device project that needs to maintain strict revision control and regulatory traceability, given that KiCad's library format is file-based rather than database-driven?

**Answer:** KiCad's file-based library format actually lends itself well to version control, which is the backbone of regulatory traceability. The key is to treat the libraries as first-class project artifacts, not as an afterthought.

I'd structure the libraries as a separate repository (or a dedicated directory tree within the project repo) with a clear hierarchy: a `symbols/` directory for schematic symbols, `footprints/` for footprint libraries, and `3d_models/` for mechanical models. Each component would have its own subdirectory containing the symbol file, footprint file, 3D model, and a metadata file (e.g., a simple text or YAML file) that records the component's part number, manufacturer, datasheet revision, and any approval status.

For revision control, I'd use Git with a strict branching and tagging strategy. Each component gets its own commit history, and when a component is approved for use in a medical device, I'd tag that specific version. The schematic and PCB files would reference the library version explicitly — either by storing the library path relative to the project and pinning the library repo to a specific commit, or by embedding the component revision in the symbol's properties (e.g., a custom field like `REV` or `APPROVED_REV`).

For regulatory traceability, the critical piece is the audit trail. Every change to a component — whether it's a footprint correction, a symbol pin rename, or a datasheet revision update — needs to be tracked with a change description and a reference to the design change notice or engineering change order. I'd enforce this through a commit message convention and, if possible, a pre-commit hook that requires a change reference.

I'd also set up a clear approval workflow: components start as "engineering preview," move to "design validation" after initial testing, and finally to "released" after formal verification. The library metadata file would track this status, and only released components would be used in the final design.

One practical consideration: KiCad's library tables (sym-lib-table and fp-lib-table) need to be consistent across all users. I'd commit these files and use relative paths so that the project is portable across machines. For multi-user environments, I'd use a central Git server and enforce that all library changes go through pull requests with review.

**Possible follow-ups:**
- How would you handle a component that needs a footprint change after it's already been used in a released design?
- How would you ensure that the schematic and PCB both reference the same component revision?

---

## Q4: Walk me through your process for using LTSpice to simulate the effect of power supply ripple on a precision analog sensor front-end, and how you would correlate those simulations with real oscilloscope measurements.

**Answer:** The goal here is to understand how much of the power supply noise couples into the sensor's output, and whether the front-end's power supply rejection is adequate for the required measurement accuracy.

In LTSpice, I'd start with a model of the power supply — typically a buck converter or LDO — and the analog front-end circuit. For the power supply, I'd simulate the actual ripple at the output, including the switching frequency component and any ringing. For the front-end, I'd include the sensor's equivalent output impedance, the amplifier's PSRR model, and the ADC's reference input if it's powered from the same rail.

The simulation approach: I'd run a transient analysis with the power supply model producing realistic ripple, and measure the resulting noise at the ADC input. I'd also run a separate AC analysis to characterize the front-end's PSRR as a function of frequency — this tells me which frequencies of power supply noise are most problematic. The key is to model the power supply's output impedance correctly, because the coupling path is often through the supply impedance rather than directly through the amplifier's PSRR.

For correlating with real measurements, I'd set up the actual hardware on the bench with the same power supply topology. I'd use an oscilloscope with a low-noise differential probe to measure the power supply ripple at the front-end's supply pin, and simultaneously measure the ADC input or the amplifier output. The key is to measure both signals on the same time base so I can see the correlation — does the noise at the ADC input occur at the same frequency and phase as the supply ripple?

I'd also use the oscilloscope's FFT function to compare the frequency content of the measured noise with the simulation's predicted spectrum. If the dominant frequencies match, the simulation model is capturing the right coupling mechanism. If they don't match, I'd look for additional coupling paths — for example, ground bounce, magnetic coupling from the inductor, or noise coupling through the PCB layout that wasn't modeled in the simulation.

One important detail: the oscilloscope's own noise floor and probe grounding can corrupt the measurement. I'd use a ground spring instead of the long ground lead, and I'd verify that the measured noise floor is below the signal I'm trying to measure. If the scope's noise floor is too high, I'd use a low-noise amplifier or a spectrum analyzer instead.

**Possible follow-ups:**
- How would you model the amplifier's PSRR in LTSpice if the manufacturer doesn't provide a SPICE model?
- How would you distinguish between power supply ripple coupling through the supply pin versus coupling through the ground plane?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** This is a high-pressure situation, but the first thing I'd do is resist the urge to assign blame or force a quick decision. The immediate priority is to get the facts on the table and understand the actual discrepancy, not to determine whose "fault" it is.

I'd call a meeting with both teams' leads and the engineers who own the respective implementations. The goal is to get both sides to present their understanding of the interface — the firmware team shows their I2C driver code, the address constants, and the register map they're using; the hardware team shows the schematic, the device's datasheet, and the address strapping. I'd have both teams walk through a concrete example: a specific read transaction, from the firmware's perspective and from the hardware's perspective, step by step.

The key is to establish ground truth from the hardware's datasheet — that's the authoritative source for the device's addressing and register layout. If the hardware team selected a sensor that uses 10-bit addressing, that's a fact we can verify from the datasheet. Similarly, if the firmware team is using a register map from a different sensor variant, that's also verifiable.

Once we've established the facts, I'd assess the options. The most likely resolution is that the firmware needs to be updated to match the hardware — changing firmware is typically faster and cheaper than re-spinning a PCB. But I'd also check whether the hardware can be adapted — for example, if the address pins can be re-strapped with a bodge wire, or if the sensor has a configuration register that can switch between 7-bit and 10-bit addressing modes.

I'd also assess the risk of each option. Changing the firmware to use 10-bit addressing is a code change, but it needs to be verified against the actual hardware. Changing the hardware with a bodge wire is a physical change that needs to be validated for reliability, especially in a medical device where solder joints and wire modifications have regulatory implications.

Given the two-day timeline, I'd prioritize getting a working integration as quickly as possible, but I'd also document the discrepancy formally — this is exactly the kind of issue that needs to be captured in the design history file for regulatory purposes. I'd have the firmware team make the minimal change to match the hardware, then run a focused integration test on the specific I2C transactions that were failing, before the full test suite.

Finally, I'd use this as a process improvement opportunity. The root cause is almost certainly a communication gap during the design phase — the hardware team selected a sensor variant without confirming the interface details with firmware, or the firmware team assumed a register map from a previous project. I'd recommend adding an interface control document (ICD) review as a formal milestone in future projects, where both teams sign off on the exact protocol details before hardware goes to fabrication.

**Possible follow-ups:**
- How would you handle the situation if the firmware team insists their implementation is correct because it works on an evaluation board?
- What would you do if the hardware cannot be changed and the firmware change is more complex than expected, pushing the timeline past the integration testing date?