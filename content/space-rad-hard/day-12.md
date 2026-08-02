# space-rad-hard — Day 12

## Q1: How would you approach designing a radiation-tolerant ADC front-end for a space-deployed system that must maintain measurement accuracy over a multi-year mission, considering both TID and single-event effects?

**Answer:** I'd approach this from three angles: component selection, circuit architecture, and calibration strategy.

For component selection, I'd look for ADCs with known radiation characterization—ideally on a QML list or with published TID and SEL test data. If forced to use a COTS part, I'd review its process technology (e.g., CMOS vs. bipolar) since that affects ELDRS susceptibility, and I'd derate operating conditions conservatively. For the voltage reference, I'd prioritize parts with low TID-induced drift and would consider using a reference with built-in temperature compensation.

For circuit architecture, I'd add input protection against single-event transients (SETs)—for example, RC filtering on analog inputs sized to reject transients without compromising the signal bandwidth. I'd also consider using a differential input stage to reject common-mode noise. For the digital interface, I'd implement error checking on the data lines (CRC or parity) and design the interface so that a single-event upset in the ADC's digital logic can't corrupt the host's bus.

For calibration, I'd build in a periodic self-calibration routine using an internal or external precision reference. This addresses TID-induced gain and offset drift over the mission. I'd also store calibration coefficients in radiation-tolerant memory (or in multiple copies with voting) and re-derive them if corruption is detected.

The key trade-off is between using a fully qualified rad-hard ADC (higher cost, lower performance, long lead time) versus a COTS part with mitigation (lower cost, better performance, but more design effort and residual risk). I'd make that decision based on the mission's accuracy requirements and the criticality of the measurement.

**Possible follow-ups:**
- How would you handle the case where the ADC's digital supply rail experiences a single-event latch-up (SEL) that causes a temporary overcurrent?
- What specific test data would you require from the ADC manufacturer before accepting a COTS part for this application?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA with internal block RAM for critical telemetry storage. The designer has implemented SEC-DED ECC on the block RAM but has not implemented scrubbing. How would you evaluate this approach, and what would you recommend?

**Answer:** SEC-DED ECC is a good foundation, but without scrubbing, there's a critical gap: the ECC can correct single-bit errors when data is read, but it cannot detect or correct errors that accumulate in memory cells that are never read. Over time, multiple single-bit upsets can accumulate in the same word, eventually creating a multi-bit error that SEC-DED cannot correct—and worse, the ECC logic itself might miscorrect, turning a correctable error into a corrupted word.

I'd recommend implementing a scrubbing routine that periodically reads every word in the block RAM, corrects any single-bit errors, and writes the corrected value back. The scrub rate should be fast enough that the probability of two upsets in the same word before scrubbing is acceptably low—this is a function of the expected upset rate and the scrub interval.

I'd also consider the interaction between scrubbing and the rest of the system. Scrubbing consumes memory bandwidth and may conflict with normal read/write operations, so I'd design the scrubber to run in the background during idle cycles or use a dual-port memory configuration where one port is dedicated to scrubbing.

One additional consideration: the ECC check bits themselves are stored in the block RAM and are also susceptible to upsets. A scrub routine that reads the data, corrects it, and rewrites both data and check bits handles this naturally. But if the scrubber only reads and corrects on-the-fly without rewriting, the check bits could remain corrupted.

Finally, I'd verify that the FPGA's block RAM ECC implementation actually protects the entire memory array—some implementations only protect certain regions or have limitations on how ECC is enabled.

**Possible follow-ups:**
- How would you determine the appropriate scrub interval for a given orbit and expected upset rate?
- What would you do if the scrubber itself is implemented in the FPGA fabric and is susceptible to configuration upsets?

---

## Q3: How would you approach designing a fault-tolerant boot sequence for a space-deployed system that uses an external configuration memory (flash) for an SRAM-based FPGA, given that the configuration memory can experience single-event upsets?

**Answer:** The boot sequence is a critical vulnerability because a corrupted configuration bitstream can cause the FPGA to fail entirely or, worse, configure into an unknown state that could damage other hardware. I'd design the boot sequence with multiple layers of protection.

First, I'd use a configuration memory that has some radiation tolerance—either a rad-hard flash or a COTS part with known SEE characteristics. I'd also store multiple copies of the bitstream (at least two, ideally three) in different memory regions. The boot controller would verify each copy using a checksum or CRC before loading it.

Second, I'd implement a "golden" vs. "update" image approach. The golden image is a minimal, known-good configuration that was validated before launch and is stored in a protected region. The update image is the full operational configuration. If the update image fails verification, the system falls back to the golden image, which can at least maintain safe operation or enable a recovery procedure.

Third, I'd design the boot controller itself to be radiation-tolerant—either implemented in a rad-hard CPLD or using a microcontroller with watchdog protection. The boot controller should have its own independent clock and power, so a failure in the FPGA or configuration memory doesn't prevent recovery.

Fourth, I'd add a mechanism for remote reconfiguration. If the system detects a corrupted configuration, it should be able to request a new bitstream from the ground or from another processor on the spacecraft. This requires a reliable communication path and a protocol for verifying the integrity of the new bitstream before loading it.

Finally, I'd test the entire boot sequence under radiation—at least with proton or heavy-ion testing—to verify that the boot controller and configuration memory behave as expected under SEE conditions.

**Possible follow-ups:**
- How would you handle the case where the boot controller itself experiences a single-event functional interrupt (SEFI) during the boot process?
- What are the trade-offs between storing the bitstream in parallel NOR flash versus serial SPI flash?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a COTS DC-DC converter to generate a 3.3V rail for digital logic. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, but your digital load (an FPGA) has an absolute maximum rating of 3.6V. A junior engineer argues this is acceptable because there is 130 mV of margin. How would you handle this disagreement?

**Answer:** I'd acknowledge the engineer's point that 130 mV of margin exists, but I'd explain that this margin may not be sufficient when you consider the full context of the space environment and the complete operating envelope.

First, I'd point out that the datasheet's worst-case specification likely assumes nominal input voltage, nominal load, and nominal temperature. In a space environment, the input voltage can vary significantly (e.g., during bus transients), the load can change dynamically, and the temperature range is much wider than commercial applications. Each of these factors can push the output voltage higher than the datasheet's worst-case value.

Second, I'd consider radiation effects. The DC-DC converter's internal reference or feedback circuitry could experience TID-induced drift, causing the output voltage to shift over the mission. A single-event transient (SET) on the feedback pin could cause a temporary output voltage spike. These effects are not captured in the datasheet.

Third, I'd look at the load's absolute maximum rating more carefully. The 3.6V rating is likely an absolute maximum that should never be exceeded, even momentarily. If the FPGA's I/O cells are connected to other components with lower voltage ratings, those components might be the limiting factor. I'd also check whether the FPGA's absolute maximum rating applies to all pins or only certain pins—some pins may have lower ratings.

Fourth, I'd consider the measurement uncertainty. How accurately do we know the actual output voltage? The converter's output voltage tolerance, the accuracy of the measurement equipment, and the voltage drop across the PCB traces all contribute to uncertainty.

My recommendation would be to add a post-regulation stage—either a low-dropout regulator (LDO) or a more precise DC-DC converter—to tighten the output voltage tolerance. Alternatively, I'd add a voltage supervisor that monitors the 3.3V rail and generates a reset or shutdown signal if the voltage exceeds a safe threshold. I'd also recommend reviewing the converter's radiation data (or testing it if no data exists) to understand how the output voltage behaves under TID and SEE.

The key principle is that in space systems, we design for worst-case conditions plus margin, not for nominal conditions plus a small buffer. The cost of a voltage excursion that damages the FPGA is far higher than the cost of adding a post-regulator.

**Possible follow-ups:**
- How would you determine the actual worst-case output voltage of the converter, given that the datasheet doesn't cover radiation effects?
- What would you do if the FPGA's absolute maximum rating is 3.6V but the converter's output can reach 3.5V under a single-event transient?

---

## Q5: How would you approach designing a test plan to verify that a space-deployed system can recover from a single-event functional interrupt (SEFI) that causes the main microcontroller to stop executing code?

**Answer:** I'd design a multi-level test plan that covers both the hardware recovery mechanisms and the firmware recovery logic, and I'd test at multiple stages from unit-level to system-level.

At the hardware level, I'd verify that the watchdog timer (or equivalent) can reset the microcontroller under all conditions. This includes testing with the microcontroller in various states—normal operation, halted, stuck in an infinite loop, or with the clock corrupted. I'd also verify that the reset signal actually reaches the microcontroller's reset pin and that the power supply remains stable during the reset sequence. If the SEFI causes a latch-up condition, I'd test the current-limiting and power-cycling circuitry separately.

At the firmware level, I'd verify that the boot sequence after a watchdog reset is robust. This includes checking that the firmware can detect that a reset occurred (e.g., via a reset cause register), that it can restore critical state from non-volatile memory, and that it can re-initialize peripherals correctly. I'd also test the firmware's ability to detect and recover from a SEFI that doesn't trigger the watchdog—for example, a SEFI that causes the microcontroller to execute incorrect instructions but still service the watchdog.

For radiation testing, I'd use a particle accelerator (proton or heavy-ion) to expose the microcontroller to SEEs while it's running representative software. I'd monitor for SEFIs and verify that the recovery mechanisms work as designed. I'd also test the system's behavior during the SEFI itself—for example, does the system produce any unsafe outputs while the microcontroller is not executing code correctly?

At the system level, I'd test the recovery sequence end-to-end: SEFI occurs, watchdog resets the microcontroller, firmware boots, system re-initializes, and returns to normal operation. I'd verify that any external devices (sensors, actuators, communication links) are properly re-synchronized after recovery.

I'd also include fault injection testing—using debug interfaces or test modes to simulate SEFIs in a controlled manner—to complement the radiation testing. This allows for more repeatable and targeted testing of specific failure scenarios.

Finally, I'd document the expected recovery time and any data loss or degradation that occurs during the SEFI and recovery, so that the system operators know what to expect.

**Possible follow-ups:**
- How would you verify that the system doesn't produce unsafe outputs during the window between the SEFI occurring and the watchdog reset taking effect?
- What would you do if the radiation testing reveals that the watchdog timer itself is susceptible to SEFIs?