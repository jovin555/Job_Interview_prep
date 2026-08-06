# space-rad-hard — Day 16

## Q1: How would you approach designing a radiation-tolerant mixed-signal PCB layout for a space-deployed system that has both precision analog sensor inputs and high-speed digital interfaces, given that single-event transients (SETs) on the analog side and switching noise from the digital side can both degrade measurement accuracy?

**Answer:** The core challenge is that radiation effects and conventional noise coupling interact — an SET on a sensitive analog node can be amplified by poor grounding, and digital switching noise can mask or mimic radiation-induced transients. My approach would start with a clean layer stack-up: a dedicated solid ground plane adjacent to the analog layer, and a separate ground region for digital, joined at a single star point near the ADC or the system's analog reference. I'd partition the board physically — analog front-end, ADC, digital processing, and power conversion each in their own zones — with guard rings around sensitive analog traces and no digital traces routed over analog ground regions.

For the analog path specifically, I'd add common-mode filtering at the input connectors, use differential routing where the sensor allows, and place bypass capacitors close to every active device. I'd also consider adding series resistance or ferrite beads on analog supply pins to isolate the analog rail from digital switching transients. On the digital side, I'd control impedance for high-speed traces, keep return paths short, and avoid routing high-speed lines parallel to analog traces for any significant length.

For radiation-specific concerns, I'd add RC filtering on analog inputs sized to reject SETs of expected duration without compromising the signal bandwidth — this is a trade-off between noise immunity and measurement response time. I'd also place transient suppression on any line that leaves the board, since those are entry points for both ESD and radiation-induced currents. Finally, I'd verify the layout with a design review checklist that covers both MIL-STD-461-style EMI practices and radiation-aware layout rules, and I'd plan for prototype testing that includes both electrical noise characterization and, if feasible, exposure testing to validate SET behavior.

**Possible follow-ups:** How would you size the RC filter on an analog input to reject SETs without degrading the measurement bandwidth? What specific layout rules would you apply to the ADC's reference and ground pins?

---

## Q2: How would you approach selecting a radiation-tolerant real-time clock (RTC) for a space-deployed system that must maintain accurate timekeeping across a multi-year mission, given that most commercial RTCs have no radiation characterization?

**Answer:** This is a classic COTS-versus-rad-hard trade-off. First, I'd define the actual requirements: what accuracy is needed, what's the acceptable drift, and what happens if the RTC loses time — is it a mission-critical function or a convenience feature? If the RTC is truly mission-critical, I'd look for a qualified part first, but the reality is that few rad-hard RTCs exist, so I'd likely need a mitigation strategy around a commercial part.

My approach would be to treat the RTC as a known weak point and design around it. I'd select a commercial RTC with a simple, well-understood interface (I²C is typical) and low power consumption, then implement a firmware-based supervision layer. This would include periodic read-back and validation of the time registers, a checksum or parity scheme on the time data, and a mechanism to detect and correct corrupted values. I'd also implement a redundant time source — for example, a second RTC or a free-running timer in the microcontroller that can serve as a coarse time reference if the primary RTC fails.

For the crystal oscillator, which is often the most radiation-sensitive part, I'd select a crystal with good TID tolerance and add a temperature compensation scheme if accuracy matters. I'd also consider using the microcontroller's own oscillator as a backup timebase, accepting that drift will be higher but that the system can still maintain approximate time. The key is to design for graceful degradation: the system should detect RTC failure, log the event, and switch to a degraded timekeeping mode rather than losing time entirely.

For qualification, I'd review any available radiation data on the specific part, consider a low-cost proton testing campaign if budget allows, and at minimum do a literature search for similar parts from the same family or manufacturer. I'd also derate the RTC's supply voltage and operating temperature to reduce stress and improve reliability margins.

**Possible follow-ups:** How would you handle the situation where the RTC's time registers are corrupted by an SEU but the part itself continues to function? What accuracy degradation would you accept in the backup timekeeping mode?

---

## Q3: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA with internal block RAM for critical telemetry storage. The designer has implemented SEC-DED ECC on the block RAM but has not implemented scrubbing. How would you evaluate this approach, and what would you recommend?

**Answer:** SEC-DED ECC is a good foundation, but without scrubbing, the protection is incomplete. The issue is that ECC can correct single-bit errors when data is read, but it cannot prevent the accumulation of errors over time. If multiple bits in the same word are upset before the data is read, the ECC will detect an uncorrectable error — and in a telemetry storage application, that could mean corrupted or lost data.

My evaluation would start by quantifying the risk: what's the expected SEU rate in the block RAM, how often is the telemetry data written and read, and what's the mission duration? If the data is written once and read infrequently, the accumulation risk is higher than if the data is continuously refreshed. I'd also consider the block RAM's physical layout — whether adjacent bits are likely to be upset by a single particle strike, which could defeat SEC-DED.

My recommendation would be to add scrubbing — a background process that reads each memory location, corrects any single-bit errors, and writes the corrected value back. This prevents error accumulation and keeps the memory in a known-good state. The scrub rate should be fast enough to correct errors before a second upset occurs in the same word, which depends on the expected SEU rate and the memory size. I'd also consider implementing a "read-disturb" approach where the scrub reads the data, corrects it, and writes it back, rather than just reading — since the write-back is what actually clears the upset.

If scrubbing in firmware is impractical due to processor load, I'd consider using the FPGA's built-in scrubbing features if available, or implementing a dedicated scrub controller in the FPGA fabric. I'd also add a mechanism to log corrected errors, since the error rate is valuable telemetry for assessing the radiation environment and the health of the memory.

**Possible follow-ups:** How would you determine the required scrub rate for a given memory size and expected SEU rate? What would you do if the scrub process itself is interrupted by a higher-priority event?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a COTS DC-DC converter to generate a 3.3V rail for digital logic. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, but your digital load (an FPGA) has an absolute maximum rating of 3.6V. A junior engineer argues this is acceptable because there is 130 mV of margin. How would you handle this disagreement?

**Answer:** I'd acknowledge the engineer's point that 130 mV appears to be margin, but I'd explain that this is insufficient for a space application for several reasons. First, the datasheet's worst-case specification is based on the manufacturer's test conditions, which may not cover all operating conditions in space — including radiation-induced parameter shifts, temperature extremes, and aging effects. Second, the absolute maximum rating on the FPGA is not a recommended operating condition; it's the limit beyond which damage may occur. Operating near that limit, even if technically within spec, leaves no room for transients, load steps, or radiation-induced voltage spikes.

I'd also point out that the DC-DC converter's output voltage can be affected by radiation — total ionizing dose can shift the reference voltage and feedback circuitry, potentially pushing the output above the datasheet's pre-radiation worst-case. Additionally, the converter's transient response to load changes could cause overshoot that exceeds the steady-state specification. In a space system, you need margin for all of these effects, not just the nominal worst-case.

My recommendation would be to add margin by either selecting a converter with tighter output tolerance, adding a post-regulator (such as an LDO) to clean up the output, or adjusting the feedback divider to set the nominal output voltage lower — for example, targeting 3.3V ±2% instead of the converter's full tolerance. I'd also add output voltage monitoring with a supervisor that can flag or shut down the rail if it drifts out of the acceptable range. The key principle is that in space systems, you design for the worst-case combination of all effects, not just the datasheet's worst-case specification.

I'd frame this as a learning opportunity for the junior engineer: the margin analysis should consider radiation effects, aging, temperature, load transients, and measurement uncertainty — not just the datasheet numbers. I'd also encourage them to calculate the actual system-level margin, including the FPGA's recommended operating range (which is typically tighter than the absolute maximum), and to consider what happens if the converter's output drifts upward over the mission lifetime.

**Possible follow-ups:** How would you quantify the radiation-induced drift on a COTS DC-DC converter's output voltage without radiation test data? What would you do if the only available converter has a similar margin issue but is otherwise the best fit for the application?

---

## Q5: How would you approach designing a fault-tolerant boot sequence for a space-deployed system that uses an external configuration memory (flash) for an SRAM-based FPGA, given that the configuration memory can experience single-event upsets?

**Answer:** The boot sequence is one of the most critical phases in a space system because a failure here can leave the system in an unknown or unrecoverable state. My approach would be to design a multi-layered boot strategy that can detect and recover from configuration memory corruption at every stage.

First, I'd add error detection on the configuration bitstream itself. Most FPGAs support CRC checking during configuration — I'd enable that and verify the CRC after each configuration attempt. If the CRC fails, the system should automatically retry with a different copy of the bitstream. This means storing multiple copies of the configuration in the flash — at least two, ideally three — with each copy having its own CRC or checksum. The boot controller would try the primary copy, verify the CRC, and if it fails, fall back to the backup copies.

Second, I'd implement a "golden" versus "update" partition scheme. The golden bitstream is a known-good, minimal configuration that is never overwritten in the field. The update partition holds the operational bitstream and can be refreshed or corrected. If the update partition becomes corrupted, the system can boot from golden and then attempt to repair or re-download the update partition. This is a common pattern in spacecraft software and FPGA configuration management.

Third, I'd add a watchdog-based recovery mechanism. If the FPGA fails to configure within a timeout, or if the configuration succeeds but the system doesn't become responsive (e.g., no heartbeat from the FPGA), the watchdog should trigger a reconfiguration attempt. This could be a hardware watchdog that resets the configuration controller, or a more sophisticated scheme where the configuration controller itself has a watchdog.

Fourth, I'd consider scrubbing the configuration memory during operation. Once the FPGA is configured, a scrubber can periodically read the configuration memory, check for upsets, and correct them — either by rewriting the affected frames or by reconfiguring the entire device. This prevents the accumulation of configuration errors that could eventually cause a functional failure.

Finally, I'd design the boot controller itself to be radiation-tolerant — using a rad-hard microcontroller or a simple state machine implemented in a rad-hard CPLD — since it's the single point of failure for the entire boot process. The boot controller should also log boot attempts and failures, so that ground operators can diagnose issues and potentially upload new bitstreams.

The key trade-off is between boot time, complexity, and fault tolerance. More copies and more verification steps increase boot time and code complexity, but they also increase the probability of successful configuration. I'd analyze the expected SEU rate in the configuration memory, the boot time budget, and the mission criticality to find the right balance.

**Possible follow-ups:** How would you handle the situation where all copies of the bitstream are corrupted? What role would a rad-hard CPLD play in the boot sequence, and how would you implement the boot state machine in it?