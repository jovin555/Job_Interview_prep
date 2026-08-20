# tools — Day 30

## Q1: How would you approach setting up a Zephyr RTOS project to support runtime calibration of an analog sensor front-end, where the calibration coefficients need to be stored in flash and survive firmware updates?

**Answer:** I'd structure this around three concerns: where calibration data lives, how it's protected during updates, and how the application accesses it consistently.

For storage, I'd partition the flash into separate regions — one for the application image and one or more dedicated areas for calibration data. The key is that the calibration partition must be outside the region the bootloader or update mechanism erases or rewrites during a firmware update. In Zephyr, this typically means defining a fixed-partition in the devicetree with a label like `storage_partition`, and using the Flash Circular Buffer (FCB) or NVS (Non-Volatile Storage) subsystem on top of it. NVS is a good default because it handles wear leveling, CRC checks, and atomic writes, which matter for a medical device where a corrupt calibration value could affect measurement accuracy.

For the update path, I'd make sure the OTA or DFU process explicitly preserves the storage partition. If using MCUboot, the swap or overwrite operation only touches the image slots, not the storage partition, as long as the partition layout is correct. I'd also add a version field to the calibration record structure so the firmware can detect if the format has changed between releases and handle migration or re-calibration gracefully.

For runtime access, I'd create a small abstraction layer — a calibration manager module — that loads coefficients into RAM at boot, provides thread-safe read access to the application, and handles writes when a calibration procedure completes. The write path should include a two-step commit: write the new values, verify them by reading back, then mark the record as valid. This prevents a power loss mid-write from leaving a partially-updated calibration.

I'd also add a fallback behavior: if the stored calibration fails CRC validation, the device should log the event, use factory default coefficients, and flag that recalibration is required — rather than silently operating with bad data.

**Possible follow-ups:**
- How would you handle the case where a firmware update changes the calibration algorithm or the number of coefficients stored?
- How would you test the power-loss-during-write scenario to verify the NVS implementation is robust?

---

## Q2: How would you approach using a logic analyzer to debug a USB 2.0 device that enumerates correctly on some hosts but fails on others, where the failure is intermittent and appears to be timing-related?

**Answer:** USB 2.0 enumeration is a well-defined sequence — reset, device descriptor request, address assignment, configuration — so the first step is to capture the full transaction stream on both a host where it works and a host where it fails, and compare them. I'd use a logic analyzer with USB 2.0 protocol decoding capability, sampling at a rate that captures the 480 Mbps signaling if it's high-speed, or at least 24 MHz for full-speed. The key is to trigger on the reset condition or the first SETUP packet so the capture starts at the beginning of enumeration.

I'd look at several specific things. First, timing margins: measure the time between the host sending a SETUP packet and the device responding with an ACK, and compare that against the USB specification's response time limits. Second, check the device descriptor response — is the device returning the correct number of bytes, and is the bMaxPacketSize0 field consistent with what the host expects? A common issue is a device that advertises 64-byte packets but actually responds with fewer, which some hosts tolerate and others don't. Third, look at the reset signaling: the host drives SE0 for at least 10 ms, and the device should respond with a chirp sequence if it's high-speed capable. Timing variations in the chirp handshake can cause some hosts to fall back to full-speed while others fail entirely.

I'd also check the electrical side in parallel — using an oscilloscope to look at the D+ and D- rise/fall times and the differential voltage levels, because a marginal signal can cause bit errors that manifest as timing-related failures. A logic analyzer tells you the protocol-level behavior, but if the physical layer is marginal, you might see CRC errors or bit-stuffing violations in the capture.

If the captures show the device is slow to respond on the failing host, I'd look at the firmware's USB interrupt handling — maybe the interrupt priority is too low, or the endpoint FIFO isn't being serviced quickly enough under certain host polling patterns. I'd also check whether the device is doing anything during enumeration that could block the USB stack, like waiting on a sensor read or a flash write.

**Possible follow-ups:**
- How would you distinguish between a host controller timing issue and a device firmware timing issue from the captured data?
- What specific USB 2.0 specification timing parameters would you measure, and what are the acceptable ranges?

---

## Q3: How would you approach setting up a constraint management system in Cadence Allegro for a mixed-signal PCB that has both high-speed digital interfaces (USB 2.0, SPI at 20 MHz) and sensitive analog sensor inputs?

**Answer:** The core principle is that constraints should be organized by signal class and physical domain, not scattered across individual nets. I'd start in the Constraint Manager by defining net classes — for example, `USB_DIFF`, `SPI_HIGH_SPEED`, `ANALOG_SENSOR`, `POWER`, and `GENERAL_DIGITAL`. Each class gets its own set of physical and spacing constraints.

For the high-speed digital classes, I'd set up the electrical constraints first: impedance targets (90 ohms differential for USB 2.0), propagation delay limits, and relative propagation delay for length matching within a bus. For USB, I'd also define the differential pair properties — the primary and return net — and set the coupling parameters like line spacing and gap. For SPI at 20 MHz, the critical constraints are usually total trace length (to limit round-trip delay) and matching between clock and data lines, so I'd set a relative propagation delay window, say ±0.5 ns, between the clock and each data line.

For the analog sensor class, the constraints are different — I'd focus on spacing rules to keep analog traces away from switching digital signals. I'd set a larger spacing requirement between the `ANALOG_SENSOR` class and the `SPI_HIGH_SPEED` or `USB_DIFF` classes, and I'd also restrict which layers analog traces can route on, keeping them away from planes that carry switching noise. I might also set a maximum parallel length rule between analog and digital nets to limit capacitive coupling.

For power nets, I'd set width and copper weight constraints based on current requirements, and I'd define via constraints — minimum via size, and possibly via-in-pad rules if the design uses them.

The verification step is critical. After routing, I'd run the Constraint Manager's analysis tools: DRC to check physical and spacing rules, and the signal integrity tools (like the embedded SI analysis or export to HyperLynx) to verify impedance and timing. I'd also generate a report showing constraint compliance per net class, and review it as part of the design review checklist.

One thing I'd emphasize: the constraint file itself should be version-controlled and reviewed just like the schematic. A wrong impedance target or a missing length-matching rule can silently produce a board that fails in the lab, and it's much cheaper to catch it in the constraint review than after fabrication.

**Possible follow-ups:**
- How would you handle a conflict where meeting the analog spacing rules forces the digital traces to be longer than the timing budget allows?
- How would you document the constraint decisions so a future engineer understands why specific values were chosen?

---

## Q4: How would you approach using a spectrum analyzer with a near-field probe to determine whether a radiated emissions failure at 320 MHz is coming from a 40 MHz clock's 8th harmonic or from a switching regulator's switching frequency harmonic?

**Answer:** The first step is to identify all potential sources that could produce energy at 320 MHz. A 40 MHz clock's 8th harmonic is one candidate. For a switching regulator, I'd need to know the switching frequency — if it's, say, 2 MHz, then 320 MHz would be the 160th harmonic, which is less likely to be significant unless there's a resonance or a very fast edge; if it's 10 MHz, then it's the 32nd harmonic. So I'd start by listing all clocks and switching frequencies in the design and computing which harmonics land at or near 320 MHz.

Next, I'd use the near-field probe to physically locate the source. I'd start with a broad scan of the board using a small loop probe (for magnetic field) and a monopole or E-field probe (for electric field), moving systematically across the board while watching the spectrum analyzer tuned to 320 MHz with a narrow span, say ±5 MHz, and a resolution bandwidth of around 100 kHz. The goal is to find the hot spots — the locations where the amplitude peaks. If the peak is near the 40 MHz crystal or oscillator, that points to the clock. If it's near the switching regulator's inductor or the MOSFET switching node, that points to the regulator.

To confirm the hypothesis, I'd use a few techniques. First, I'd check the harmonic spacing: if the emission at 320 MHz is part of a series of peaks spaced 40 MHz apart (280, 320, 360), that strongly suggests the 40 MHz clock. If the peaks are spaced at the regulator's switching frequency, that points to the regulator. Second, I'd try to disable or change the source — for example, if the firmware can temporarily stop the SPI peripheral that uses the 40 MHz clock, and the 320 MHz peak disappears, that confirms the clock. Similarly, if the regulator can be put into a different mode or its switching frequency changed slightly, and the emission shifts accordingly, that confirms the regulator.

I'd also use the near-field probe to trace the coupling path. Even if the source is the 40 MHz clock, the radiation might be from a long trace or cable that's acting as an antenna, not from the clock itself. Moving the probe along the trace and observing where the amplitude is highest helps identify whether the issue is the source or the unintentional antenna.

Finally, I'd correlate the near-field measurements with the far-field failure — the near-field probe tells you where the energy is on the board, but the far-field test tells you how it radiates. If the near-field hot spot is near a connector or cable, the fix might be filtering or shielding at that interface rather than at the source.

**Possible follow-ups:**
- How would you determine whether the emission is common-mode or differential-mode, and how would that change your mitigation approach?
- What if the 40 MHz clock and the switching regulator are physically close together — how would you separate their contributions?

---

## Q5: (Behavioral) Imagine you are leading a design review for a medical device PCB, and you discover that the firmware team has been using a different version of the I2C protocol than what the hardware actually implements — the firmware is expecting 7-bit addressing with a specific register map, but the hardware uses 10-bit addressing with a different register layout. The integration testing is scheduled to start in two days, and both teams are confident their implementation is correct. How would you handle this situation?

**Answer:** The first thing I'd do is verify the discrepancy myself rather than relying on either team's assertion. I'd pull the hardware schematic and the firmware source, and trace the actual I2C address configuration — checking the address pins on the sensor, the device datasheet, and the firmware's address definition and register access code. I'd also check the hardware's register map against what the firmware is reading and writing. The goal is to have a definitive, evidence-based statement of what the hardware does and what the firmware expects, so the discussion is grounded in facts, not confidence.

Once I've confirmed the mismatch, I'd bring both teams together in a short, focused meeting. I'd present the evidence clearly — here's the hardware configuration, here's what the firmware is doing, here's where they diverge. I'd frame it as a system-level integration issue, not a blame issue. The question isn't whose fault it is; it's what the correct behavior should be and how we get there with minimal risk.

Then I'd evaluate the options. The first question is: which implementation is actually correct for the hardware? If the hardware is already in fabrication and the address pins are strapped for 10-bit addressing, then the firmware needs to change. If the hardware can be modified — for example, if the address pins can be re-strapped with different resistors — that might be faster than a firmware change, but it depends on the board revision and whether the change is feasible without a new fabrication run.

I'd also assess the risk of each fix. Changing the firmware's I2C address and register map is contained to the firmware codebase, but it requires re-testing the sensor communication thoroughly. Changing the hardware requires either a board rework or a new fabrication, which has schedule implications. I'd also check whether the sensor's register map is actually different or if the firmware is just using the wrong address — sometimes the register map is the same and only the address differs, which simplifies the fix.

Given the two-day timeline, I'd prioritize the fastest safe fix. If the firmware change is straightforward — updating the address constant and any register definitions — I'd have the firmware team make that change immediately, with a focused test plan to verify communication on the actual hardware. I'd also have the hardware team double-check whether the address pins can be reworked as a backup option.

Finally, I'd use this as a process improvement opportunity. After the immediate issue is resolved, I'd ask why the mismatch wasn't caught earlier — was there no interface control document (ICD) between the teams? Was the hardware design reviewed against the firmware's assumptions? I'd propose adding a formal interface review step to the project plan, where hardware and firmware teams jointly review the I2C address, register map, and protocol details before the PCB goes to fabrication. This is a classic integration failure that's much cheaper to catch in a design review than in the lab.

**Possible follow-ups:**
- How would you handle the situation if the firmware team insists their implementation is correct because it works on the evaluation board?
- What would you do if the hardware cannot be changed and the firmware change is more complex than expected — how would you communicate the schedule impact to management?