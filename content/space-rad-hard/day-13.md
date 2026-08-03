# space-rad-hard — Day 13

## Q1: How would you approach designing a radiation-tolerant power sequencing scheme for a multi-rail space-deployed system (e.g., 3.3V, 1.8V, 1.2V) where the FPGA and ADC require specific power-up ordering?

**Answer:** Power sequencing in a space environment adds complexity because the sequencing controller itself must be radiation-tolerant, and the failure modes of the sequencer (e.g., SEFI causing it to stop or mis-sequence) must be considered. My approach would start by determining the actual sequencing requirements from the FPGA and ADC datasheets — many modern FPGAs require core voltage to ramp before or simultaneously with I/O voltage to avoid latch-up or excessive current draw, while ADCs often need analog and digital supplies to track within a specified window.

For the sequencing implementation, I would prefer a hardware-based approach using RC delays or dedicated sequencer ICs with programmable timing, rather than relying on firmware, because the sequencer must operate correctly even if the main processor is not running or has been reset by a single-event event. If using a dedicated sequencer IC, I would verify its radiation tolerance or add redundancy — for example, using two sequencers in a cross-strapped configuration where either one can complete the sequence. I would also add undervoltage lockout (UVLO) on each rail so that if a rail fails to reach its threshold, the system halts rather than attempting to operate in an undefined state.

For the sequencing itself, I would design for a controlled ramp: enable the 3.3V I/O rail first (or last, depending on the FPGA requirement), then 1.8V, then 1.2V core, with delays between rails to allow each to stabilize. I would also consider using a "power-good" signal from each regulator as a handshake rather than fixed delays, since regulator startup time can vary with temperature and radiation-induced degradation. Finally, I would add a hardware-based reset release that only asserts when all rails are within tolerance, ensuring the FPGA and ADC see valid supply levels before initialization begins.

**Possible follow-ups:**
- How would you handle the case where one rail fails to reach its target voltage during sequencing — should the system retry, latch off, or attempt partial operation?
- What radiation effects on the sequencer itself would you be most concerned about, and how would you test for them?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA with internal block RAM for critical telemetry storage. The designer has implemented SEC-DED ECC on the block RAM but has not implemented scrubbing. How would you evaluate this approach, and what would you recommend?

**Answer:** SEC-DED ECC on block RAM is a good first step, but without scrubbing, the protection degrades over time. The key issue is that SEC-DED can correct single-bit errors but only detect double-bit errors. If a second single-bit upset occurs in the same word before the first is corrected, the ECC will detect a double-bit error and may trigger a system fault or data loss. The probability of this happening increases with mission duration and radiation environment severity.

I would evaluate the approach by first quantifying the expected upset rate: estimate the SEU cross-section of the block RAM from the FPGA's radiation data, multiply by the expected particle flux in the mission orbit, and calculate the mean time between upsets (MTBU) for a single word. If the MTBU is significantly longer than the mission duration, scrubbing may be unnecessary. However, for most LEO or MEO missions, the MTBU for a single word is typically much shorter than the mission duration, so scrubbing is recommended.

For scrubbing, I would implement a background process that periodically reads all block RAM locations, corrects any single-bit errors, and writes the corrected data back. The scrub rate should be fast enough that the probability of two upsets in the same word before scrubbing is negligible — typically this means scrubbing the entire memory at least once per hour, but the exact rate depends on the upset rate. I would also consider whether the scrubber itself is radiation-tolerant: if the scrubber is implemented in the FPGA fabric, it could be upset by an SEU, so I would consider using TMR on the scrubber state machine or implementing scrubbing in external logic. Finally, I would ensure that the ECC check-and-correct logic is itself protected, since a single-event transient in the ECC logic could corrupt data during a write.

**Possible follow-ups:**
- How would you handle the trade-off between scrub rate and power consumption, given that scrubbing requires reading and writing all memory locations?
- What would you do if the block RAM is too large to scrub frequently enough, and would you consider using external radiation-hardened SRAM instead?

---

## Q3: How would you approach designing a fault-tolerant analog-to-digital conversion subsystem for a space-deployed system that must maintain measurement accuracy over a multi-year mission, considering both TID and single-event effects?

**Answer:** The analog front-end and ADC are often the most sensitive parts of a space system because radiation affects both the analog components (e.g., offset drift, gain error, noise) and the digital interface (e.g., SEUs in the ADC's digital logic, corrupted conversion results). My approach would be to design for accuracy degradation over the mission, not just at beginning of life.

For TID effects, I would select components with known radiation tolerance — either qualified rad-hard parts or COTS parts with test data showing acceptable TID performance. For precision analog components like voltage references and op-amps, I would pay particular attention to ELDRS (enhanced low-dose-rate sensitivity), which can cause significantly more degradation at space dose rates than at accelerated test rates. I would derate the specifications: for example, if the system requires 0.1% accuracy at end of life, I would design for 0.05% at beginning of life to allow for radiation-induced drift.

For single-event effects, I would focus on the ADC's digital interface: a single-event transient in the ADC's internal state machine could cause it to output a corrupted conversion result or hang the serial interface. I would add error detection on the digital side — for example, using CRC on the serial data, or reading each conversion twice and comparing. For critical measurements, I would consider using two independent ADC channels and voting on the results, or using a watchdog timer on the ADC's serial interface to detect and recover from hangs.

I would also consider the reference voltage: a single-event transient on the reference could cause a one-shot error in all conversions during that period. Using a reference with a large output capacitor can help filter transients, but the capacitor itself must be radiation-tolerant (e.g., ceramic, not tantalum). Finally, I would design the PCB layout to minimize noise coupling from digital circuits into the analog front-end, using proper grounding and shielding, since radiation-induced noise in the digital domain can couple into the analog path.

**Possible follow-ups:**
- How would you verify that the ADC's accuracy meets requirements after radiation exposure — would you use in-flight calibration, and if so, how would you implement it?
- What would you do if a COTS ADC you want to use has no radiation data — how would you qualify it with limited budget?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a COTS DC-DC converter to generate a 3.3V rail for digital logic. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, but your digital load (an FPGA) has an absolute maximum rating of 3.6V. A junior engineer argues this is acceptable because there is 130 mV of margin. How would you handle this disagreement?

**Answer:** I would acknowledge the engineer's point that 130 mV of margin exists, but I would explain that this margin is insufficient when considering the full range of operating conditions and failure modes. The datasheet's 3.47V maximum is likely specified under nominal conditions — but in a space environment, we need to consider worst-case conditions including temperature extremes, radiation-induced degradation of the converter's feedback circuitry, and load transients that can cause output voltage spikes.

I would walk through the analysis: first, check the converter's output voltage specification across the full operating temperature range (e.g., -55°C to +125°C for space), which may widen the tolerance. Second, consider radiation effects — TID can cause the voltage reference in the converter to drift, potentially increasing the output voltage over the mission. Third, consider transient response: when the FPGA switches between low-power and high-power states, the converter's output may overshoot, and this overshoot could exceed the 3.6V absolute maximum even if the steady-state voltage is within spec.

I would also point out that the FPGA's absolute maximum rating is not a "recommended operating condition" — operating near the absolute maximum for extended periods can accelerate aging and reduce reliability, even if it doesn't cause immediate failure. The recommended operating range is typically narrower, and we should design to stay within that range with margin.

My recommendation would be to either: (1) select a converter with tighter output voltage tolerance, (2) add a post-regulator (e.g., an LDO) to ensure the FPGA sees a stable 3.3V, or (3) add a voltage supervisor that shuts down the rail if it exceeds a safe threshold. I would also suggest reviewing the converter's radiation data to understand how its output voltage may drift over the mission. The key principle is that we design for worst-case conditions, not nominal conditions, and we maintain margin to the absolute maximum rating, not just to the recommended operating range.

**Possible follow-ups:**
- How would you quantify the radiation-induced drift of the converter's output voltage if the datasheet has no radiation data?
- Would you consider adding a crowbar circuit or other protection to prevent overvoltage damage to the FPGA?

---

## Q5: How would you approach designing a test plan to verify that a space-deployed system can recover from a single-event functional interrupt (SEFI) that causes the main microcontroller to stop executing code?

**Answer:** A SEFI is one of the most challenging failure modes because the microcontroller stops executing code entirely, and the recovery mechanism must work without any help from the microcontroller itself. My test plan would focus on three areas: (1) detecting the SEFI, (2) recovering from it, and (3) verifying that the system returns to a known-good state.

For detection, I would test the watchdog timer: the watchdog should be independent of the main microcontroller (e.g., an external watchdog IC or a second microcontroller) and should reset the system if the main controller stops toggling its heartbeat. I would test the watchdog under various conditions: normal operation, a simulated hang (e.g., an infinite loop in firmware), and a complete loss of clock. I would also test the watchdog's response time — it should reset the system quickly enough to prevent data corruption but slowly enough to avoid false resets during normal operation.

For recovery, I would test the reset and boot sequence: after a watchdog reset, the system should reinitialize all peripherals, reload configuration from non-volatile memory, and resume normal operation. I would verify that the boot sequence is robust — for example, if the bootloader itself is corrupted, the system should have a fallback (e.g., a redundant bootloader in a separate flash sector). I would also test recovery from a SEFI that occurs during a critical operation, such as a write to non-volatile memory, to ensure the system doesn't corrupt data during the reset.

For the test plan itself, I would use a combination of fault injection and radiation testing. In fault injection, I would use a debug interface (e.g., JTAG) to force the microcontroller into a hung state and verify that the watchdog recovers it. In radiation testing, I would expose the system to a particle beam and monitor for SEFIs, verifying that each SEFI is detected and recovered. I would also test the system's behavior after multiple SEFIs in quick succession, since a SEFI during the recovery process could cause a more complex failure. Finally, I would verify that the system's telemetry records the SEFI event, so that ground operators can diagnose the cause and assess the system's health.

**Possible follow-ups:**
- How would you test the watchdog timer's behavior if the microcontroller's clock is corrupted by a single-event transient — would the watchdog still fire?
- What metrics would you use to determine whether the recovery is successful, and how would you measure them during radiation testing?