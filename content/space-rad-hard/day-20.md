# space-rad-hard — Day 20

## Q1: How would you approach designing a fault-tolerant telemetry and command interface for a space-deployed system where the main processor communicates with a ground station through a rad-hard transceiver, and single-event upsets can corrupt both the uplink command stream and the downlink telemetry?

**Answer:** I'd approach this as a layered reliability problem, addressing it at the protocol, data, and hardware levels simultaneously. At the protocol level, I'd implement a command-response scheme with sequence numbers, timeouts, and retransmission rather than a fire-and-forget approach. Every command would include a CRC or checksum, and the system would reject any command that fails validation—never partially execute a corrupted command. For the downlink, I'd add forward error correction (FEC) such as Reed-Solomon or convolutional coding to allow the ground station to recover from bit errors without retransmission, since uplink bandwidth is typically more constrained than downlink.

At the data level, I'd structure telemetry frames with explicit frame sync words, length fields, and CRC protection. Critical telemetry—such as health and safety data—would be sent redundantly, either by repeating it in consecutive frames or by using a higher-priority channel. I'd also design the telemetry format so that a corrupted frame can be detected and discarded without corrupting the parsing state of subsequent frames.

At the hardware level, I'd consider using a separate watchdog or supervisor that monitors the communication interface. If the transceiver itself is susceptible to single-event latch-up or functional interrupts, I'd include current limiting and the ability to power-cycle the transceiver independently. I'd also consider using two independent communication paths if the mission requires high availability—for example, a primary RF link and a backup, or redundant transceivers with cross-strapping.

Finally, I'd design the ground interface to be tolerant of stale data. The flight software should timestamp every telemetry packet and include a sequence counter, so the ground station can detect gaps or out-of-order data and distinguish between a communication glitch and an actual onboard fault.

**Possible follow-ups:** How would you handle a situation where the ground station sends a command that passes CRC but is logically invalid—for example, a command to set a parameter out of range? What trade-offs would you consider between adding FEC overhead and reducing the telemetry data rate?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS microcontroller for housekeeping. The microcontroller has a built-in watchdog timer that the firmware enables during initialization. The designer argues that the internal watchdog is sufficient and no external watchdog is needed. How would you evaluate this approach?

**Answer:** I'd push back on relying solely on the internal watchdog, even though it's a reasonable starting point. The fundamental issue is that a watchdog is only useful if it can reliably detect and recover from all failure modes—and an internal watchdog shares the same silicon, the same power supply, and the same clock domain as the processor it's supposed to monitor. A single-event functional interrupt (SEFI) that corrupts the processor's core logic could also corrupt the watchdog's configuration registers, disable it, or cause it to generate spurious resets. Similarly, a single-event transient on the clock tree could affect both the processor and the watchdog simultaneously.

If the internal watchdog is the only protection, I'd want to see evidence that it has been radiation-tested or that the specific failure modes have been analyzed. For a COTS microcontroller with no radiation data, that's unlikely. I'd recommend adding an external watchdog—ideally a simple, radiation-tolerant or at least radiation-characterized part—that operates independently of the processor's clock and power domain. The external watchdog should be configured to require a specific "heartbeat" sequence rather than a simple toggle, so that a processor stuck in a loop that happens to toggle a GPIO won't accidentally clear it.

I'd also consider using two watchdogs with different mechanisms—for example, one that requires a periodic I²C write and one that requires a specific GPIO pattern—to protect against a single point of failure. The key principle is diversity: the recovery mechanism should not share failure modes with the system it's protecting.

**Possible follow-ups:** How would you test that the external watchdog actually recovers the system from a SEFI, given that you can't inject radiation events during ground testing? What if the external watchdog itself is a COTS part with no radiation characterization—how would you qualify it?

---

## Q3: How would you approach designing a radiation-tolerant analog-to-digital conversion subsystem for a space-deployed system that must maintain measurement accuracy over a multi-year mission, considering both total ionizing dose (TID) and single-event transient (SET) effects?

**Answer:** I'd start by recognizing that the ADC itself is only one part of the chain—the reference, the input conditioning circuitry, and the digital interface all contribute to accuracy and all have radiation concerns. For TID, the primary effects are leakage currents and threshold voltage shifts in the analog front-end, which can cause offset drift and gain error. I'd select components with known TID tolerance, and I'd derate the operating conditions—for example, running the ADC at a lower reference voltage or reducing the input range to leave margin for drift.

For the voltage reference, I'd choose a radiation-hardened or at least radiation-characterized part, since reference drift directly translates to measurement error. I'd also consider using a ratiometric measurement approach where the sensor excitation and the ADC reference come from the same source, which cancels out reference drift to first order.

For single-event transients, the concern is that a particle strike can cause a temporary glitch on the analog input or inside the ADC's comparator, producing a spurious conversion result. I'd mitigate this at multiple levels. At the circuit level, I'd add filtering on the analog input—for example, a low-pass filter with a time constant longer than the expected SET duration—to attenuate transients before they reach the ADC. At the system level, I'd oversample and average multiple conversions, or use a median filter to reject outliers. If the ADC has a "busy" or "data ready" output, I'd also consider whether a SET could corrupt the conversion timing, and I'd add a timeout or re-synchronization mechanism.

I'd also pay attention to the digital interface. A SET on the ADC's serial interface could corrupt the data as it's read out, so I'd add CRC or parity checking on the data transfer, or at least validate that the data is within a plausible range. Finally, I'd design the firmware to detect and reject out-of-range readings—for example, by comparing each reading to the previous value and flagging any jump that exceeds a physically plausible slew rate.

**Possible follow-ups:** How would you choose between a precision ADC with a serial interface and a simpler one with a parallel interface, from a radiation perspective? How would you handle the case where the ADC's reference input itself is susceptible to single-event transients?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a COTS DC-DC converter to generate a 3.3V rail for digital logic. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, and the FPGA's absolute maximum rating is 3.6V. A junior engineer argues that the 130 mV margin is acceptable because "the FPGA will never actually see 3.47V in practice." How would you handle this disagreement?

**Answer:** I'd acknowledge that the engineer has a point about the margin being small but real, but I'd reframe the discussion around worst-case analysis and the cost of being wrong. The datasheet specification of 3.47V is the manufacturer's guarantee under worst-case conditions—that includes temperature extremes, input voltage variation, load transients, and component aging. The FPGA's absolute maximum rating of 3.6V is the limit beyond which damage can occur, and it's not a recommended operating condition—it's a survival limit. Operating at 3.47V means the FPGA is at 96% of its absolute maximum, which leaves very little headroom for any transient overshoot, such as during load steps or power-up.

I'd also point out that the datasheet values are statistical—the converter might produce 3.47V under worst-case conditions, but it could also produce slightly more due to manufacturing variation or unforeseen operating conditions. The 130 mV margin is not a safety factor; it's the difference between the worst-case spec and the absolute limit, and it doesn't account for measurement error, PCB voltage drop, or the fact that the FPGA's absolute maximum rating itself has some uncertainty.

My recommendation would be to add margin by either selecting a converter with a tighter output tolerance, adding a post-regulator, or using a converter with an adjustable output that can be set to a lower nominal voltage. I'd also consider adding a voltage supervisor that monitors the 3.3V rail and asserts a reset if it exceeds a safe threshold—this protects the FPGA even if the converter drifts out of spec. The key principle is that we should design to the datasheet worst-case, not to our expectation of typical behavior, because in a space environment we can't afford to be wrong.

**Possible follow-ups:** How would you determine what an acceptable margin actually is—is there a rule of thumb or a standard you'd reference? What if the converter's worst-case output is only 3.4V—would that change your assessment?

---

## Q5: How would you approach designing a test plan to verify that a space-deployed system can recover from a single-event functional interrupt (SEFI) that causes the main microcontroller to stop executing code, when you cannot inject actual radiation events during ground testing?

**Answer:** Since we can't use a particle accelerator for every test, I'd design a test plan that simulates SEFI-like conditions at the system level and verifies that the recovery mechanisms work as intended. The goal is to prove that the system can detect a hung processor, recover it, and return to normal operation without external intervention.

The first step is to identify all the ways a SEFI could manifest—a processor that stops executing, one that executes corrupted instructions, one that's stuck in an infinite loop, or one that's toggling a "heartbeat" GPIO but not actually doing useful work. For each failure mode, I'd design a test that simulates it. For example, I could use a debug interface (JTAG or SWD) to halt the processor mid-execution, corrupt its program counter, or force it into a tight loop. I could also use a test harness that injects a fault into the memory bus or the clock to simulate a transient.

For each simulated fault, I'd verify that the watchdog or recovery mechanism detects the failure within the expected timeout, asserts a reset, and that the system boots back into a known-good state. I'd also verify that the system doesn't just reset—it must recover to a state where it can resume its mission functions, which might mean re-initializing peripherals, re-synchronizing communication, and validating that no data was corrupted.

I'd also test the recovery path under realistic conditions—for example, with the system in the middle of a critical operation, or with the communication bus active, to ensure that the recovery doesn't leave the system in a degraded state. Finally, I'd include fault-injection testing at the firmware level, where I deliberately corrupt a memory location or a register to simulate a single-event upset, and verify that the error-handling code catches it.

The key is to be systematic: enumerate the failure modes, design a test for each, and document the expected recovery behavior. This gives confidence that the system will recover from a real SEFI, even though we can't reproduce the exact radiation event on the ground.

**Possible follow-ups:** How would you test the case where the processor is executing corrupted code but still appears to be "alive" to the watchdog—for example, it's toggling the heartbeat but not doing useful work? How would you verify that the system returns to a safe state after recovery, rather than just resuming from where it left off?