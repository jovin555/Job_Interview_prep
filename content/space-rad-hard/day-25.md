# space-rad-hard — Day 25

## Q1: How would you approach designing a radiation-tolerant power distribution architecture for a satellite payload that must survive a single-event latch-up (SEL) on any single load without losing the entire system?

**Answer:** The core principle is to contain the fault at the lowest possible level so that a latch-up in one load cannot propagate to the rest of the payload. I would start by partitioning the power distribution into independently protected domains, typically per functional block or per voltage rail. Each domain would have its own current-limiting element — a foldback current limiter, a positive-temperature-coefficient (PTC) device, or an electronic circuit-breaker — sized to allow normal inrush and steady-state current but to trip quickly when a latch-up signature (sudden, sustained overcurrent) appears.

The key design decisions are the trip threshold and the recovery strategy. The threshold must be set high enough to avoid nuisance trips during normal operation and power-up inrush, but low enough to protect the load and the bus. For recovery, I would consider whether the system can tolerate an automatic retry (e.g., a timed power-cycle of the affected domain) or whether it requires a command from the ground or a higher-level controller. In a safety-critical system, I would likely implement a hybrid: automatic retry with a limited number of attempts, then a persistent latch-off that requires explicit command to reset, to avoid a stuck latch-up causing repeated stress.

I would also add a bulk input filter and a fast-acting crowbar or clamp on the main bus to handle the transient energy during a latch-up event, and ensure that the current-limiting element itself is radiation-tolerant, since a commercial part may have its own SEL susceptibility. Finally, I would verify the design with fault injection testing — simulating a latch-up on each domain and confirming that the rest of the payload continues to operate normally.

**Possible follow-ups:** How would you choose between a foldback current limiter and an electronic circuit breaker for this application? What failure modes of the current-limiting element itself would you need to consider?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS DC-DC converter for the 3.3V rail. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, and the FPGA's absolute maximum rating is 3.6V. A junior engineer argues that the 130 mV margin is acceptable because "the FPGA will never actually see 3.47V in practice — the converter will typically output 3.3V." How would you handle this disagreement?

**Answer:** I would acknowledge that the engineer's point about typical operation is technically correct, but I would explain that the design must be evaluated at worst-case conditions, not typical conditions, because the system must survive all specified operating environments. The 130 mV margin is not a safety margin — it is the difference between the converter's worst-case output and the FPGA's absolute maximum rating, and it leaves no room for additional factors.

I would walk through the analysis systematically. First, the converter's 3.47V maximum is itself a worst-case figure that assumes specific input voltage, load current, temperature, and component tolerances. But there are additional contributors: the output voltage can be affected by load transients, by the tolerance of the feedback resistor divider, by radiation-induced drift in the converter's reference or error amplifier, and by the PCB trace resistance between the converter output and the FPGA input. Each of these can add tens of millivolts. Second, the FPGA's absolute maximum rating is not a recommended operating condition — it is the limit beyond which damage may occur, and operating near it for extended periods can accelerate aging or cause latent damage.

I would also note that the converter's output voltage is not the only stress on the FPGA's power pins. The FPGA's absolute maximum rating applies to the voltage at the die, not at the converter output, so any voltage drop between the two (or any ringing on the rail due to fast load transients) must be accounted for. If the margin is already thin at the converter output, there is no room for these effects.

My recommendation would be to either select a converter with tighter output tolerance, add a post-regulator or a precision voltage supervisor that can shut down the rail if it exceeds a safe threshold, or derate the FPGA's operating voltage range to leave a more comfortable margin. I would also suggest measuring the actual rail voltage at the FPGA pins under worst-case load and temperature conditions during qualification testing, rather than relying on datasheet calculations alone.

**Possible follow-ups:** What if the converter's output voltage is within spec but the FPGA's absolute maximum rating is exceeded only during a transient, such as a load step? How would you assess that risk?

---

## Q3: How would you approach designing a fault-tolerant boot sequence for a space-deployed system that uses an SRAM-based FPGA with external configuration memory (flash), where both the FPGA configuration bitstream and the flash memory are susceptible to single-event upsets?

**Answer:** The boot sequence needs to handle two distinct failure modes: a corrupted bitstream stored in flash, and a bitstream that is valid when read but becomes corrupted during configuration or while the FPGA is operating. I would design the boot sequence with multiple layers of protection.

First, the bitstream in flash should be protected with error detection and correction. I would store a checksum or CRC alongside the bitstream, and ideally a redundant copy of the bitstream in a separate flash region or a separate device. During boot, the configuration controller (which could be a rad-hard microcontroller or a state machine in a rad-hard CPLD) would read the bitstream, verify the CRC, and if it fails, fall back to the redundant copy. If both copies fail, the system would enter a safe state and report the error rather than attempting to operate with a corrupted configuration.

Second, the configuration process itself should be monitored. The FPGA's configuration status pins (e.g., DONE, INIT_B) should be checked after configuration completes. If the FPGA fails to configure, the controller should attempt a reconfiguration, possibly with a different bitstream copy or after a power-cycle to clear any latch-up in the FPGA.

Third, once the FPGA is operating, the configuration memory (the SRAM cells that define the logic and routing) can still be upset by single-event effects. This requires a scrubbing mechanism — either continuous or periodic readback of the configuration memory, comparing against a golden copy, and rewriting any corrupted frames. The golden copy should be stored in a radiation-tolerant memory (e.g., rad-hard PROM or a protected flash region with ECC).

I would also consider the boot time budget. Scrubbing and verification take time, and the system may need to reach a safe state quickly after power-on. The boot sequence should prioritize getting the system into a known-safe configuration first, then perform full verification and scrubbing in the background.

Finally, I would design the boot controller itself to be fault-tolerant, since it is the single point of failure for the entire boot process. This could mean using a rad-hard microcontroller, implementing a watchdog that can reset the boot controller, or using a simple state machine in a rad-hard CPLD that is less susceptible to upsets.

**Possible follow-ups:** How would you decide between continuous scrubbing and periodic scrubbing? What are the trade-offs in terms of power, time, and fault coverage?

---

## Q4: How would you approach designing a radiation-tolerant analog front-end for a space-deployed system that must maintain measurement accuracy over a multi-year mission, considering both total ionizing dose (TID) and single-event transient (SET) effects?

**Answer:** The analog front-end is particularly challenging because radiation affects both the DC accuracy (through TID-induced drift in references, amplifiers, and ADC parameters) and the instantaneous accuracy (through SETs that cause spurious voltage spikes or bit errors). I would approach this in three layers: component selection, circuit design, and system-level mitigation.

For component selection, I would prioritize parts with known radiation behavior — either qualified rad-hard parts or COTS parts with published radiation test data. For precision components like voltage references and operational amplifiers, I would look for data on TID-induced drift and on SET susceptibility. If no data exists, I would either select a different part or plan for additional testing. I would also derate components per standard guidelines (e.g., MIL-STD-975 or ECSS) to account for parameter shifts over the mission.

For circuit design, I would focus on minimizing the impact of SETs. This includes adding filtering at the analog input (e.g., an RC low-pass filter with a cutoff frequency appropriate for the signal bandwidth) to attenuate short transients, and using differential signaling where possible to reject common-mode noise. I would also consider redundancy at the circuit level — for example, using two ADC channels with independent references and comparing their outputs, or using a voting scheme if three channels are available. For the reference, I would use a precision reference with a buffer amplifier, and I would add a capacitor at the reference output to hold the voltage during a transient.

For system-level mitigation, I would implement software-based techniques. This includes averaging or median filtering of ADC samples to reject single-sample spikes, and using plausibility checks — for example, if a reading changes by more than a physically possible amount between consecutive samples, it is likely corrupted and should be discarded or re-sampled. I would also implement periodic calibration using an internal reference or a known input to detect and correct for TID-induced drift.

Finally, I would design the PCB layout carefully to minimize noise coupling — keeping the analog and digital grounds separate, using guard rings around sensitive analog traces, and placing decoupling capacitors close to the analog components. The layout is just as important as the component selection for maintaining accuracy in a radiation environment.

**Possible follow-ups:** How would you distinguish between a SET-induced error and a genuine signal change in your plausibility checking? What if the signal itself is fast-changing?

---

## Q5: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS microcontroller for housekeeping. The microcontroller has a built-in watchdog timer that the firmware enables during initialization. The designer argues that the internal watchdog is sufficient and no external watchdog is needed. How would you handle this disagreement?

**Answer:** I would start by acknowledging that the internal watchdog is a useful first line of defense, but I would explain that it has fundamental limitations in a radiation environment. The internal watchdog is implemented in the same silicon as the microcontroller, so a single-event effect that disrupts the microcontroller's core — such as a single-event functional interrupt (SEFI) — can also disrupt the watchdog circuitry itself. If the watchdog shares the same clock domain or the same reset logic as the CPU, a fault that halts the CPU may also halt the watchdog, or the watchdog may continue to be serviced by an interrupt handler even though the main application is corrupted.

I would also point out that the internal watchdog is typically a simple timer that resets the microcontroller if it is not serviced within a timeout period. It does not distinguish between a healthy system that is temporarily busy and a corrupted system that is still servicing the watchdog in a tight loop. In a radiation environment, a more robust approach is needed.

My recommendation would be to add an external watchdog — a separate IC or a simple circuit in a rad-hard CPLD — that is independent of the microcontroller's clock, power, and reset circuitry. The external watchdog should be serviced by the main application loop, not by an interrupt handler, so that a fault in the interrupt system will cause a timeout. The external watchdog should also have a longer timeout than the internal one, to allow the system to recover from transient faults without unnecessary resets.

I would also consider a more sophisticated approach: a "heartbeat" signal from the microcontroller that must toggle at a specific rate, with the external watchdog monitoring both the presence and the rate of the heartbeat. This catches the case where the microcontroller is still running but executing corrupted code that happens to service the watchdog. Additionally, I would ensure that the external watchdog's reset output is connected to the microcontroller's reset pin through a properly designed reset circuit, and that the watchdog itself is radiation-tolerant.

Finally, I would frame this as a defense-in-depth issue. The internal watchdog is not wrong to include — it provides a fast, local recovery mechanism — but it should not be the only mechanism. The external watchdog provides an independent layer of protection that covers failure modes the internal watchdog cannot.

**Possible follow-ups:** How would you design the external watchdog's timeout period to balance fast recovery against false resets? What if the microcontroller has a low-power sleep mode — how would you handle watchdog servicing during sleep?