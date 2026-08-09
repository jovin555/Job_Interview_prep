# tools — Day 19

## Q1: How would you approach setting up a Zephyr RTOS project to support both a production build and a development build with different sensor configurations, where the development build includes additional debug logging and a mock sensor driver, without maintaining two separate codebases?

**Answer:** I'd use Zephyr's Kconfig and devicetree overlay system to handle this cleanly. The core approach is to keep the production configuration as the base, then layer development-specific settings on top using overlays and a separate build directory.

First, I'd define the sensor configuration in the devicetree. If the production hardware uses a real sensor on, say, I2C0, that node stays in the base devicetree. For the development build, I'd create a devicetree overlay that either replaces the sensor node with a mock/virtual device or adds a second node that the mock driver binds to. Zephyr's devicetree overlays are applied on top of the base tree, so I can swap or augment hardware descriptions without touching the base files.

For the debug logging and mock driver selection, I'd use Kconfig. The production build gets `CONFIG_LOG_LEVEL_WRN` or similar, while the development build enables `CONFIG_LOG_DBG` and `CONFIG_MOCK_SENSOR=y`. The mock driver itself can be implemented as a separate driver file that's only compiled when that Kconfig symbol is enabled, using `if MOCK_SENSOR` guards in the CMakeLists.txt.

The key is to use Zephyr's `west build` with different build directories and `-d` flags. I'd set up two build configurations — one for production and one for development — each with its own `.conf` file and overlay. The application code stays identical; it just calls the sensor API, and the build system resolves which driver gets linked in. This keeps a single codebase, and the production build is guaranteed to not include any debug code because it's compiled out at the Kconfig level.

I'd also add a CI check that builds both configurations to catch any drift between them, and I'd tag releases in Git so the exact production build can be reproduced.

**Possible follow-ups:**
- How would you handle the case where the mock sensor needs to simulate specific failure modes or edge cases that the real sensor can't produce?
- What if the development build needs a different linker script or memory layout — how would you manage that within the same project?

---

## Q2: How would you approach using a spectrum analyzer with a near-field probe to determine whether a radiated emissions failure at a specific frequency is coming from a switching regulator's fundamental frequency or from a harmonic of a digital clock, and how would you confirm your hypothesis?

**Answer:** The first step is to identify all potential sources that could produce energy at the failing frequency. I'd list the switching regulator frequencies, the digital clock frequencies, and their harmonics. For example, if the failure is at 100 MHz, I'd check whether a 25 MHz clock's 4th harmonic or a 500 kHz regulator's 200th harmonic is more plausible — though the latter is unlikely due to roll-off.

Next, I'd use the near-field probe to physically locate the source. I'd start with a broad scan of the board using a small loop probe, moving it systematically across the board while watching the spectrum analyzer at the failing frequency. The probe will show a strong amplitude peak when it's directly over the source. Switching regulators typically radiate from the inductor and the switching node (the trace connecting the switch to the inductor), while digital clocks radiate from the clock trace, the oscillator, and any long parallel traces that carry the clock signal.

To differentiate between the two, I'd look at the spectral signature. A switching regulator often produces a broad cluster of energy around the fundamental with sidebands related to the control loop, while a digital clock produces a narrow peak at the fundamental and clean harmonics. I'd also check the waveform shape — if I can connect a high-impedance probe to the suspected source, a clock will show a square wave, while a regulator switching node will show a trapezoidal waveform with ringing.

To confirm the hypothesis, I'd do a controlled experiment. If I suspect the regulator, I could temporarily disable it (if the board allows) or change its switching frequency slightly and see if the emission moves accordingly. If I suspect the clock, I could slow the clock down or change its frequency via firmware and observe the emission shift. A cleaner method is to use the spectrum analyzer's frequency span to check if the failing frequency is exactly an integer multiple of the suspected source — if it's a harmonic, the ratio will be exact.

Finally, I'd check for coupling paths. The source might be the regulator, but the radiation could be from a long trace or cable that's acting as an antenna. I'd use the near-field probe to trace the energy path from the source to the radiating element, which tells me whether the fix should be at the source (better decoupling, snubbing) or at the antenna (shielding, filtering, layout changes).

**Possible follow-ups:**
- How would you distinguish between the fundamental of a very fast clock and a harmonic of a slower clock when they're at the same frequency?
- What near-field probe characteristics (loop size, shield) would you choose for this investigation, and why?

---

## Q3: How would you approach setting up a multi-board bring-up test plan for a system with a main processor board, a sensor board, and a power distribution board, where the boards are connected via board-to-board connectors?

**Answer:** I'd structure the bring-up in stages, starting with the power board in isolation, then adding boards one at a time, and only integrating the full system once each stage is verified. The goal is to isolate failures to a single board or interface rather than debugging a fully assembled system where faults could be anywhere.

**Stage 1: Power distribution board alone.** I'd verify all output voltages, current limits, and ripple at no load and with a resistive load. I'd check power-on sequencing if the system requires it, and I'd measure inrush current. This is also the time to verify that the board-to-board connector pinouts match the mechanical keying and that there are no shorts between adjacent pins.

**Stage 2: Power board + processor board.** Before connecting, I'd verify the processor board's power inputs with a multimeter to ensure no shorts. Then I'd connect it and check that the processor's core voltage, I/O voltage, and any analog supplies are within spec. I'd then attempt to program the processor via JTAG/SWD — this confirms the debug interface is functional. I'd run a minimal firmware that toggles an LED or UART to confirm the processor is executing.

**Stage 3: Power board + processor board + sensor board.** I'd first check the sensor board's power rails and any reference voltages. Then I'd verify the communication interface (I2C, SPI, or whatever the sensor uses) by scanning for the sensor's address or reading its ID register. I'd check that the sensor's interrupt or data-ready lines are functioning. If the sensor has an analog output, I'd verify the ADC reads a known value (e.g., with the sensor in a known state or with a test input).

**Stage 4: Full system integration.** With all boards connected, I'd run a system-level test that exercises the complete data path — sensor reading, processing, and any output (display, wireless, etc.). I'd also run a soak test to check for thermal issues and intermittent failures.

Throughout this process, I'd document each test step with expected values and pass/fail criteria in a test plan document. I'd also use a current-limited bench supply during initial power-up to protect against shorts. For the board-to-board connectors specifically, I'd use a continuity test before first power-up to verify that no pins are bent or misaligned, and I'd visually inspect the connectors under magnification.

**Possible follow-ups:**
- How would you handle a situation where the sensor board works when connected directly to the processor board but fails when the power board is in the loop?
- What test equipment would you have on the bench for this bring-up, and how would you set it up?

---

## Q4: How would you approach using a logic analyzer to debug a UART communication issue where the device intermittently sends corrupted data, but only when the system is under load — for example, when a motor is running in a medical device?

**Answer:** I'd approach this in two parallel tracks: capturing the actual corruption with the logic analyzer, and correlating it with the system load to understand the root cause.

First, I'd set up the logic analyzer to capture the UART TX and RX lines, plus a few additional channels that indicate system state — for example, a GPIO that the firmware toggles when the motor driver is active, or the motor PWM signal itself. I'd also capture the power supply rail if the logic analyzer has analog inputs, or use a separate oscilloscope channel for that. The key is to have a time-correlated view of the UART data, the motor activity, and the power state.

I'd configure the logic analyzer with a deep buffer and trigger on the UART TX line, capturing a long window around the corruption event. UART corruption under load often falls into a few categories: bit timing errors (the baud rate drifts because the clock is affected by supply voltage), signal integrity issues (noise on the line), or firmware issues (the UART peripheral is being starved or the interrupt is delayed).

When I capture the corrupted frame, I'd look at the waveform in detail. If the bit widths are stretched or compressed, that points to a clock or timing issue — possibly the microcontroller's oscillator is sensitive to supply voltage droop when the motor draws current. If the bit widths are correct but the data is wrong, that points to a firmware issue — perhaps the TX buffer is being overwritten, or the UART interrupt is being preempted by a higher-priority motor control interrupt, causing the firmware to miss a transmit complete event.

I'd also look at the power rail on the oscilloscope simultaneously. If I see voltage droop or ripple correlated with the corruption, that's a strong signal that the issue is power-related. I'd then check whether the UART's baud rate generator is sensitive to supply voltage — some microcontrollers use an internal oscillator that drifts with voltage.

To confirm the root cause, I'd run controlled experiments. If I suspect power, I could add bulk capacitance to the supply and see if the corruption disappears. If I suspect firmware, I could temporarily disable the motor control interrupt and see if the corruption stops. If I suspect signal integrity, I'd check the UART line's rise/fall times and look for ringing or crosstalk from the motor wires.

The logic analyzer is essential here because it gives me the exact bit-level timing and data, which lets me distinguish between these failure modes. Without it, I'd be guessing based on symptoms.

**Possible follow-ups:**
- How would you distinguish between a firmware timing issue and a hardware signal integrity issue if the bit widths look correct but the data is wrong?
- What sampling rate would you set on the logic analyzer for a 115200 baud UART, and why?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different register map for a sensor than what the hardware actually implements — the firmware is reading from register addresses that don't exist on the hardware's sensor variant, but the firmware team says their code works on the evaluation board. The PCB is already in fabrication, and the project is on a tight schedule. How would you handle this situation?

**Answer:** The first thing I'd do is verify the discrepancy myself rather than relying on either team's assertion. I'd pull the sensor's datasheet for the exact part number on the BOM, and I'd compare the register map against the firmware's header file or driver code. I'd also check the evaluation board's sensor variant — it's entirely possible the eval board uses a different variant or a newer revision that has the registers the firmware expects, while the production part is older or different.

Once I've confirmed the mismatch, I'd assess the impact. The key question is whether the firmware's register accesses will cause a functional failure or just a benign read of an invalid address. Some sensors return 0xFF or a default value for undefined registers, which might mean the firmware gets wrong data but doesn't crash. Others might behave unpredictably. I'd also check whether the firmware writes to any registers that don't exist — a write to an undefined register could put the sensor into an unknown state.

With that assessment, I'd lay out the options to the team. The cleanest fix is to change the firmware to use the correct register map — this is usually a matter of updating the driver, and it doesn't require any hardware changes. The risk is that the firmware team's code was tested against the eval board, so the fix needs to be re-tested against the actual sensor. I'd also check if the sensor variant on the PCB can be swapped to match the eval board — if the package is the same and the pinout is compatible, that might be a one-line BOM change, but it depends on availability and whether the electrical characteristics are otherwise identical.

I'd then call a short meeting with both teams to present the evidence and the options. I'd frame it as a factual issue, not a blame issue — the goal is to find the fastest safe path forward. I'd ask the firmware team to estimate the effort to update the driver, and I'd ask the hardware team to check if a sensor variant swap is feasible. I'd also flag the process gap: the firmware team tested on an eval board, but there was no mechanism to verify that the eval board's sensor matched the production BOM. That's a lesson for the next project, but right now the priority is the schedule.

My decision would depend on the timeline. If the firmware fix is straightforward and the sensor behavior is well-documented, I'd go with that — it's the lowest-risk change because it doesn't affect the fabricated PCB. I'd have the firmware team make the change and then run a focused test on the actual sensor once the boards arrive, using a bench setup with the sensor on a breakout if possible. I'd also update the integration test plan to include a register readback check that verifies the sensor is responding correctly before any functional testing proceeds.

**Possible follow-ups:**
- How would you handle the situation if the firmware team pushes back and insists the eval board behavior is the correct reference, and the hardware team should have used the newer sensor variant?
- What process changes would you propose after this incident to prevent the same class of problem in future projects?