# tools — Day 27

## Q1: How would you approach setting up a Zephyr RTOS project to support runtime calibration of an analog sensor front-end, where the calibration coefficients need to be stored in flash and survive firmware updates?

**Answer:** I'd structure this around three concerns: the calibration data model, the flash storage strategy, and the update mechanism.

For the data model, I'd define a dedicated calibration structure with versioning, a checksum or CRC, and metadata like timestamp and calibration source. This structure would be stored in a dedicated flash partition, separate from the firmware image partition, so that a firmware update doesn't overwrite it. In Zephyr, I'd use the settings subsystem or a custom flash partition with a simple read/write driver — the settings subsystem is attractive because it handles wear leveling, atomic writes, and key-value storage out of the box.

For surviving firmware updates, the key is partition layout. I'd define a fixed flash partition for calibration data using the devicetree or the partition manager, ensuring the firmware update process (whether via MCUboot or a custom bootloader) never touches that partition. The application would read calibration at boot, validate the checksum, and fall back to factory defaults if invalid.

For the runtime calibration flow, I'd implement a calibration thread or a set of shell commands that let a technician apply a known reference, compute the coefficients, and write them to flash. The write should be atomic — write to a scratch area first, verify, then commit — to avoid corruption if power is lost mid-write. I'd also add a "factory reset" option to restore defaults.

One subtlety: if the device has multiple hardware revisions with different analog front-ends, the calibration structure should include a hardware revision field so the firmware can detect if calibration data was written for a different revision and reject it.

**Possible follow-ups:**
- How would you handle the case where the flash write fails mid-operation due to power loss?
- How would you ensure that calibration data is not accidentally corrupted by a firmware update that changes the structure layout?

---

## Q2: Walk me through your process for using a spectrum analyzer with a near-field probe to identify whether a radiated emissions failure at a specific frequency is coming from a switching regulator's fundamental or harmonic, versus a digital clock harmonic, and how you would confirm your hypothesis.

**Answer:** The first step is to identify all potential sources that could produce energy at the failing frequency. I'd list the switching regulator frequencies and their harmonics, and the digital clock frequencies and their harmonics. For example, if the failure is at 150 MHz, I'd check whether a 25 MHz clock's 6th harmonic or a 500 kHz regulator's 300th harmonic lands there — though regulator harmonics at that order are usually weak, so I'd weight the candidates by plausibility.

Next, I'd use the near-field probe to spatially map the emission. I'd move the probe across the board, focusing on the areas around the regulator, the clock oscillator, and the traces connecting them. The emission pattern often tells you the source: a regulator tends to radiate from its switching loop and the inductor, while a clock radiates from the trace and its return path. I'd note the amplitude at each location and look for the strongest hotspot.

To discriminate between candidates, I'd use a few techniques. First, I'd check if the emission is narrowband or broadband — clock harmonics are typically very narrow, while regulator emissions can be broader with sidebands. Second, I'd try to correlate with the time domain: using a near-field probe connected to an oscilloscope, I could look at the waveform and see if the period matches the clock or the switching frequency. Third, I could temporarily disable or change the clock frequency (if the firmware allows it) and see if the emission moves proportionally — if it does, it's clock-related. Similarly, I could change the regulator's switching frequency via a resistor or feedback network and observe the shift.

Finally, I'd confirm by measuring the actual signal on the suspected trace with an oscilloscope, using a proper probe technique (ground spring, not the long ground lead) to verify the frequency content matches the emission. If the trace shows the expected harmonic and the emission disappears when the source is disabled, that's confirmation.

**Possible follow-ups:**
- How would you distinguish between a clock harmonic and a regulator harmonic that happen to coincide at the same frequency?
- What probe positioning mistakes would you watch out for when using a near-field probe?

---

## Q3: How would you approach setting up a differential pair routing constraint in Cadence Allegro for a USB 2.0 interface on a mixed-signal medical device PCB, and how would you verify that the constraints are actually met in the final layout?

**Answer:** I'd start by defining the electrical requirements from the USB 2.0 specification: 90 ohms differential impedance, and appropriate length matching between D+ and D− (typically within a few mils for USB 2.0, though the spec is more forgiving than high-speed serial standards). I'd also consider the stackup — the dielectric material, layer thickness, and copper weight determine the trace width and spacing needed to hit 90 ohms, so I'd work with the fab house to confirm the stackup before setting constraints.

In Allegro, I'd use the Constraint Manager to create a physical constraint set for the USB pair: set the differential pair impedance target, define the line width and spacing, and set the coupling parameters (gap between the pair). I'd also create a spacing constraint set for the pair-to-other-nets clearance, since the pair needs isolation from adjacent signals to maintain impedance and reduce crosstalk. For the electrical constraints, I'd set the phase tolerance (length matching within the pair) and, if needed, total length targets for the pair relative to the connector or the transceiver.

Once the constraints are set, I'd route the pair and then verify in several ways. First, I'd run the DRC in Allegro to check for violations. Second, I'd use the impedance analysis tool (if available in the toolset) to calculate the actual impedance along the routed pair, accounting for the real geometry — this catches issues like the pair separating around vias or at the connector. Third, I'd visually inspect the pair in the layout to ensure it stays coupled and doesn't diverge unnecessarily. Finally, I'd review the length matching report to confirm the phase tolerance is met.

For a medical device, I'd also document the constraint set and the verification results as part of the design file, since the design history file needs to show that the design meets its requirements.

**Possible follow-ups:**
- How would you handle the transition from the differential pair to the USB connector pins, where the pair has to spread out?
- What would you do if the fab house reports that the actual impedance is off by a few ohms after fabrication?

---

## Q4: How would you approach using a Segger J-Link debugger to capture a real-time trace of a Zephyr RTOS-based system's thread scheduling behavior without halting the CPU or modifying the firmware?

**Answer:** The key constraint is non-intrusiveness — I don't want to halt the CPU or add instrumentation that changes timing. The J-Link's trace capability (via the ETM or ITM on Cortex-M targets) is the right tool here, but it requires hardware support: the target must have trace pins (SWO for ITM, or the full trace port for ETM) and the debugger must support the trace interface.

For thread scheduling behavior specifically, I'd use a combination of two approaches. First, the ITM (Instrumentation Trace Macrocell) can be used to capture software events — but that requires firmware to write to the ITM stimulus registers, which counts as modifying the firmware. If the firmware already has trace support built in (some RTOSes, including Zephyr, have tracing hooks that can be enabled at build time), then I could use that. But the question says "without modifying the firmware," so I'd need a different approach.

The alternative is to use the ETM (Embedded Trace Macrocell) to capture the instruction trace, then correlate that with the RTOS's thread control block (TCB) addresses. The ETM gives a cycle-accurate instruction stream, and by knowing the addresses of the RTOS's context-switch code (e.g., the PendSV handler in Zephyr), I can identify when context switches occur and which thread is being switched to by examining the register values in the trace. This is complex but fully non-intrusive.

In practice, I'd use the J-Link's trace software (J-Trace or the trace features in Ozone) to capture the ETM stream. I'd set up the trace to capture a window of execution, then post-process the trace to identify context-switch points. The RTOS-aware trace decoding in tools like Ozone can map the instruction trace to thread names if the debugger has the symbol table and the RTOS awareness plugin.

If the target doesn't support ETM, a simpler approach is to use the SWO pin with ITM — but again, that requires firmware support. In that case, I'd have to accept that some firmware modification is needed, or I'd use a logic analyzer on the GPIO pins if the firmware already toggles a pin on context switch (which some RTOS configurations do for profiling).

The practical answer is: check what trace hardware the target supports, use ETM if available, and be prepared to fall back to a hybrid approach if the target is limited.

**Possible follow-ups:**
- What are the limitations of using ETM trace for RTOS analysis compared to using the RTOS's built-in tracing?
- How would you handle a target that doesn't have trace pins broken out on the PCB?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first priority is to establish ground truth rather than let the two teams argue about who's right. I'd call a short, focused meeting with both teams and ask them to bring their authoritative references: the hardware team brings the sensor datasheet and the schematic showing the address pins and register map, and the firmware team brings the driver code and the datasheet they used to write it. The goal is to compare both against the same source of truth — the component datasheet — not against each other's assumptions.

If the datasheet confirms the hardware implementation is correct (10-bit addressing, the hardware register map), then the firmware needs to be fixed. The question is how to do that in two days. I'd assess the scope: is it just the address format, or does the register map differ significantly? If it's a small change, the firmware team can update the driver and we can run a focused integration test on the affected functionality. If it's a large change, we need to be honest about the schedule impact and communicate that to stakeholders early, rather than pretending we'll make the deadline.

I'd also want to understand how this discrepancy happened — was there a requirements document that was ambiguous, or did the teams not share the datasheet early enough? That's a process issue to address after the immediate problem is solved, but it's important to prevent recurrence.

During the meeting, I'd keep the tone constructive. The goal isn't to assign blame but to get the device working correctly. I'd acknowledge that both teams made reasonable assumptions based on the information they had, and the real issue is that the information wasn't shared early enough. After the immediate fix, I'd propose adding a protocol review step to the design process — a formal check where the hardware and firmware teams review the interface specification together before the PCB is sent to fabrication.

For the immediate two-day window, I'd also consider a workaround: if the hardware has a way to switch to 7-bit addressing (e.g., via a strap option or a register write), that might be faster than rewriting the firmware. But I wouldn't compromise the design just to meet the schedule — a medical device needs to be correct, not just on time.

**Possible follow-ups:**
- How would you decide whether to fix the firmware or change the hardware, given the two-day deadline?
- What would you do if the firmware team insists their implementation is correct and the hardware team is wrong, even after reviewing the datasheet together?