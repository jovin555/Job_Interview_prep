# tools — Day 8

## Q1: How would you approach using LTSpice to simulate the effect of power supply ripple on a precision analog sensor front-end, and how would you correlate those simulations with real oscilloscope measurements?

**Answer:** I would start by building a simulation model that includes the power supply output (with a realistic ripple source — a sine wave or a piecewise linear approximation of the switching noise from the actual converter), the LDO or filter stage, and the analog front-end circuit. The key is to model the PSRR (power supply rejection ratio) of the op-amp or ADC correctly, using the manufacturer's SPICE model or a behavioral PSRR block if the model isn't available. I'd run an AC sweep from the ripple frequency (typically the switching frequency of the buck converter, e.g., 1–2 MHz) up through harmonics to see how much ripple couples through to the output.

For correlation with real measurements, I would use an oscilloscope with a low-noise front-end and a 1:1 probe (or a 50-ohm feed-through termination if the signal path allows) to measure the ripple at the power rail directly, then move the probe to the analog output. The critical technique is to use a ground spring instead of the long ground lead to avoid picking up radiated noise. I'd compare the amplitude and frequency content of the measured ripple at the output with the simulation prediction. If they diverge significantly, I'd look for unmodeled parasitics — for example, the PCB trace inductance between the LDO output and the op-amp supply pin, or the ESL/ESR of the decoupling capacitors that weren't included in the simulation. I'd then add those parasitics to the simulation and re-run to see if the match improves.

**Possible follow-ups:** How would you model the decoupling capacitor's non-ideal behavior (ESR, ESL) in LTSpice? What would you do if the measured ripple at the analog output is 10× higher than the simulation predicts?

---

## Q2: How would you approach setting up a differential pair routing constraint in Cadence Allegro for a CAN-FD bus running at 5 Mbps on a mixed-signal medical device PCB?

**Answer:** I would start in the Constraint Manager by defining a physical constraint set for the differential pair. For CAN-FD at 5 Mbps, the typical target impedance is 120 ohms differential (matching the characteristic impedance of the twisted-pair cable the bus is designed for). I'd set the line width and spacing based on the PCB stack-up — for a standard 4-layer board with 1 oz copper and a prepreg thickness of around 4–5 mils between the top layer and the reference plane, that might be something like 8 mil trace width with 8 mil spacing, but I'd verify with the impedance calculator in Allegro (or a separate field solver like Polar Si9000) to hit 120 ohms.

I'd also set a length matching constraint — typically ±5 mm is sufficient for CAN-FD at this speed, since the bit time is 200 ns and propagation delay differences of a few hundred picoseconds are negligible. I'd create a relative propagation delay constraint for the pair, and then use the interactive length tuning tool to add serpentine routing if needed. For a medical device, I'd also add a clearance constraint to keep the differential pair away from noisy digital traces (like a high-speed SPI bus or a switching converter output) by at least 3× the trace width, and ensure the pair has a continuous reference plane underneath with no splits. Finally, I'd run a DRC check specifically for the differential pair to catch any violations before sending the design to fabrication.

**Possible follow-ups:** How would you handle routing the CAN-FD differential pair through a connector that has a different impedance? What would you do if the stack-up forces you to route the pair on an inner layer instead of the top layer?

---

## Q3: How would you approach using a logic analyzer to debug a UART communication issue where the device intermittently sends corrupted data, but only when the system is under load (e.g., when the motor is running in a medical device)?

**Answer:** I would start by setting up the logic analyzer to capture the UART TX and RX lines, along with a few other signals that indicate system state — for example, a GPIO that toggles when the motor is active, the power supply rail for the UART transceiver, and maybe a clock signal from the microcontroller. I'd set the trigger condition to capture on the motor-active signal going high, with a pre-trigger buffer of maybe 10% to see the state just before the motor starts.

Once I capture a corruption event, I'd look at the UART waveform in the protocol decoder view. The first thing I'd check is the baud rate accuracy — if the corrupted bytes have incorrect stop bit timing or framing errors, it suggests the baud rate is drifting under load, possibly due to clock source instability or power supply droop. I'd measure the bit width of the corrupted bytes and compare it to the expected 104 µs (for 9600 baud) or whatever the configured rate is.

If the timing looks correct but the data is wrong, I'd look at the voltage levels on the UART lines. I'd overlay the analog waveform (if the logic analyzer has analog capability) or use an oscilloscope simultaneously to check for ringing, undershoot, or noise on the UART lines during motor operation. The motor driver can inject significant switching noise into the ground plane, which can cause the UART transceiver to misinterpret logic levels. I'd also check whether the UART ground reference is shared with the motor return path — if so, that's a layout issue that needs to be fixed by separating the analog/digital ground from the high-current ground.

**Possible follow-ups:** How would you distinguish between a firmware timing issue (e.g., the UART interrupt being blocked by a higher-priority motor control interrupt) and a hardware noise issue? What modifications would you make to the trigger setup if the corruption happens only once every few hours?

---

## Q4: How would you approach using a Segger J-Link debugger to capture a crash dump from a Zephyr RTOS-based system that has entered a hard fault, without modifying the firmware to add debug print statements?

**Answer:** I would use the J-Link's real-time memory access capabilities combined with the Zephyr crash handler's default behavior. Zephyr's fault handler typically saves the CPU register state (stack pointer, program counter, link register, and fault status registers) to a known memory location or to the current stack before entering an infinite loop or resetting. I would configure the J-Link to halt the CPU on the hard fault by setting the appropriate debug exception control register (e.g., the Debug Fault Control Register on Cortex-M devices) to halt on hard fault events.

Once the fault occurs and the CPU halts, I would use J-Link Commander (or a script via the J-Link SDK) to read the saved register context from the stack. The key is to know the stack pointer value at the time of the fault — I can read the current PSP (Process Stack Pointer) or MSP (Main Stack Pointer) depending on which mode the CPU was in. From there, I can walk the stack to extract the return address (which tells me which function was executing) and the stacked registers (R0–R3, R12, LR, PC, xPSR). I'd also read the CPU's fault status registers (CFSR, HFSR, BFAR, MMAR) to determine the exact fault type — whether it's a bus fault, usage fault, or memory management fault, and whether it was caused by an invalid memory access or an undefined instruction.

For a more automated approach, I would write a J-Link script that halts on the fault, reads the relevant memory regions, and outputs the crash context in a format that can be parsed by a script to resolve addresses to function names using the ELF file's symbol table. This avoids needing to modify the firmware at all — the debugger handles everything externally.

**Possible follow-ups:** How would you handle the case where the fault handler itself overwrites the stack before the debugger can read it? What if the device resets immediately after the fault before the J-Link can halt?

---

## Q5: (Behavioral) Imagine you are leading the bring-up of a new medical device prototype, and you discover that the Altium Designer project has a critical issue — the schematic symbol for the main microcontroller has incorrect pin assignments for the JTAG/SWD interface, meaning the debugger cannot connect to the target. The PCB has already been fabricated, and the project is on a tight schedule. The junior engineer who created the symbol is confident the pinout is correct based on a preliminary datasheet revision. How would you handle this situation?

**Answer:** First, I would verify the pin assignment discrepancy myself by comparing the schematic symbol against the latest official datasheet and the manufacturer's reference design — not the preliminary revision the junior engineer used. I'd document the specific pins that are wrong and take screenshots of both the symbol and the datasheet for clarity. This isn't about assigning blame; it's about establishing facts.

Once I've confirmed the error, I would call a brief, focused meeting with the junior engineer and the project lead (if separate from myself). I'd start by acknowledging that preliminary datasheets can be ambiguous and that this kind of issue is exactly why we do design reviews and prototype bring-up testing. I'd show the discrepancy and ask the junior engineer to walk through their reasoning — partly to understand if there was a misinterpretation I can correct for future work, and partly to give them a chance to identify the error themselves.

For the immediate fix, I would evaluate the options: (a) if the wrong pins are connected to ground or power, we might be able to cut traces and bodge-wire to the correct JTAG/SWD pins if they're accessible on the PCB; (b) if the pins are connected to other components, we might need to design a small adapter board that sits between the debugger and the target connector; (c) if the microcontroller has an alternative debug interface (e.g., SWD instead of JTAG, or a different pin mux option), we might be able to reconfigure the firmware to use a different set of pins. I'd present these options to the team with estimated time and risk for each, and let the project lead decide based on schedule constraints.

After the immediate crisis is resolved, I would implement a process change: for future projects, all critical pin assignments (debug interfaces, power, crystal oscillator) must be cross-checked against the official datasheet by a second engineer before the schematic is released for layout. This turns the error into a learning opportunity rather than a punitive event.

**Possible follow-ups:** What would you do if the junior engineer becomes defensive and insists their pinout is correct, even after you've shown the datasheet evidence? How would you handle the situation if the only fix requires a PCB respin that will delay the project by three weeks?