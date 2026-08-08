# space-rad-hard — Day 18

## Q1: How would you approach designing a fault-tolerant configuration management scheme for an SRAM-based FPGA in a space-deployed system, where the configuration bitstream is stored in external flash memory that is also susceptible to single-event upsets?

**Answer:** The fundamental challenge here is that both the configuration storage and the configuration logic are vulnerable, so I'd approach this as a layered defense problem rather than relying on any single mitigation.

First, I'd protect the stored bitstream in flash. The most practical approach is to store multiple copies of the configuration bitstream — typically three copies — and implement a voting scheme at the controller level. Each copy should have its own error detection code, such as a CRC or ECC checksum, so the controller can validate a copy before attempting configuration. If one copy fails validation, the controller falls back to another. This handles the case where a single-event upset corrupts one stored image.

Second, I'd consider scrubbing the flash contents periodically. Even if the flash isn't being read for configuration, upsets can accumulate over time. A background task could read each copy, verify the checksum, and rewrite any corrupted sectors. This requires that the flash supports sector-level erase and rewrite without disrupting the FPGA operation, which is feasible if the FPGA is already configured and running.

Third, I'd address the configuration process itself. The FPGA should be configured from a verified image, and after configuration completes, the controller should verify that configuration succeeded — either by reading back the configuration CRC from the FPGA (if supported) or by checking a status signal. If configuration fails, the controller should retry with a different stored image, and if all images fail, it should power-cycle the FPGA and retry.

Finally, I'd think about the configuration clock and interface. Single-event transients on the configuration interface can corrupt the bitstream during loading, so I'd use a slower configuration clock than the maximum rated speed to reduce setup/hold violations, and I'd consider adding error detection during the configuration process itself if the FPGA supports it.

The key trade-off is between the number of stored copies, the scrubbing frequency, and the available flash capacity and controller bandwidth. Three copies is a reasonable starting point, but the exact number should be driven by the expected upset rate, the mission duration, and the criticality of rapid reconfiguration.

**Possible follow-ups:** How would you handle the case where the flash itself experiences a single-event functional interrupt (SEFI) and stops responding to read commands? What if the controller that manages configuration is itself the device that experiences an upset?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA and a COTS DC-DC converter. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, and the FPGA's absolute maximum rating is 3.6V. A junior engineer argues that the 130 mV margin is acceptable because "the FPGA will never actually see 3.47V in practice." How would you handle this disagreement?

**Answer:** I'd start by acknowledging that the engineer has a point about typical operating conditions, but I'd reframe the discussion around worst-case analysis and the consequences of exceeding an absolute maximum rating.

The absolute maximum rating is not a recommendation — it's a limit beyond which damage may occur, and it's not a guarantee that the device will function correctly even if it survives. In a space environment, we have to consider worst-case conditions across the entire mission: the converter's output can drift with total ionizing dose, temperature extremes, load transients, and aging. The 3.47V specification is itself a worst-case number, but it's the converter's worst case, not necessarily the system's worst case. What happens if the converter's output overshoots during a load transient? What about the voltage drop across the PCB trace between the converter and the FPGA? The FPGA sees the voltage at its pins, not at the converter's output.

I'd also point out that 130 mV is only about 3.6% margin, and in radiation-hardened design, we typically derate components well below their absolute maximum ratings — often to 80% or less of the rated maximum. The margin here is not just about the steady-state voltage; it's about the combination of all possible contributions: converter tolerance, load transient response, radiation-induced parameter shifts, and measurement uncertainty.

If the engineer still pushes back, I'd suggest a practical compromise: add a voltage supervisor or monitor on the 3.3V rail that can detect an overvoltage condition and take action, such as asserting a reset or shutting down the load. This doesn't fix the root cause, but it provides a safety net. The better solution is to select a converter with tighter output tolerance or add a post-regulator, even if it costs some efficiency.

The key principle is that in space systems, we design for the worst case, not the typical case, because we can't send a technician to fix a failed board.

**Possible follow-ups:** How would you quantify the risk if the FPGA is operated at 3.5V for an extended period? What derating guidelines would you apply to the FPGA's core voltage?

---

## Q3: How would you approach designing a radiation-tolerant analog front-end for a space-deployed system that must maintain measurement accuracy over a multi-year mission, considering both total ionizing dose (TID) and single-event transient (SET) effects?

**Answer:** This is a two-part problem: TID causes gradual parameter degradation, while SETs cause instantaneous, transient errors. The design approach for each is quite different.

For TID effects, the primary concern is that component parameters shift over time — op-amp offset voltage and bias current drift, voltage reference output voltage changes, ADC gain and offset errors increase, and leakage currents rise. The mitigation strategy is threefold: select components with known radiation tolerance, derate the specifications, and design the circuit to be tolerant of parameter shifts.

For example, if I'm using an op-amp in a precision amplifier stage, I'd look at the datasheet's radiation data — if available — and derate the operating conditions so that even with worst-case TID-induced drift, the circuit still meets its accuracy requirement. I'd also design the circuit with adjustable calibration: a calibration DAC or trim potentiometer that can be adjusted in-flight to compensate for drift. This requires a calibration routine that runs periodically, using a known reference voltage to measure and correct the gain and offset errors.

For the voltage reference, I'd select a part with good radiation data and low temperature coefficient, and I'd consider using a ratiometric measurement approach where the ADC reference is derived from the same source as the sensor excitation, so that reference drift cancels out.

For SET effects, the concern is that a single heavy ion can cause a transient voltage spike at the ADC input, producing a corrupted sample. The mitigation is primarily in the digital domain: oversampling and filtering. If the system can tolerate the latency, I'd sample at a higher rate than needed and apply a median filter or a moving average to reject outliers. A median filter is particularly effective at rejecting single-sample transients because a single corrupted sample will be the outlier in a window of valid samples.

I'd also consider adding a small RC low-pass filter at the ADC input to limit the bandwidth and reduce the amplitude of SET-induced transients, though this trades off against the signal bandwidth. The cutoff frequency should be chosen based on the signal of interest and the expected SET pulse width.

Finally, I'd think about the ADC itself. Some ADCs have built-in digital filters or can be configured for repeated conversions with averaging. If the ADC has a "busy" or "data ready" signal, I'd use it to ensure that the firmware only reads valid conversion results.

The overall approach is to design for graceful degradation: the system should maintain accuracy within specification for the mission duration, and when a transient occurs, it should reject the corrupted sample rather than acting on it.

**Possible follow-ups:** How would you determine the appropriate oversampling ratio and filter window size? How would you handle the trade-off between SET rejection and signal bandwidth?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS microcontroller for housekeeping. The microcontroller has a built-in watchdog timer that the firmware enables during initialization. The designer argues that the internal watchdog is sufficient and no external watchdog is needed. How would you evaluate this approach?

**Answer:** I'd begin by acknowledging that the internal watchdog is better than nothing, but I'd raise several concerns that make it insufficient as the sole protection mechanism in a space environment.

First, the internal watchdog shares the same silicon and the same power supply as the microcontroller. If a single-event effect causes a power supply disturbance or a latch-up condition, the internal watchdog may be affected in the same way as the processor core. The whole point of a watchdog is to provide an independent recovery path, and an internal watchdog is not truly independent.

Second, the internal watchdog's clock source is typically derived from the same oscillator as the CPU. If the oscillator fails or drifts due to TID, the watchdog timing will be affected. An external watchdog with its own oscillator provides a truly independent timing reference.

Third, there's the failure mode where the microcontroller enters a state where it continues toggling the watchdog "kick" signal but is no longer executing the main application correctly. This can happen if an upset corrupts the interrupt vector table or the main loop's state, but the interrupt service routine that kicks the watchdog is still running. An external watchdog with a longer timeout — or one that requires a more complex "challenge-response" sequence — can detect this condition, whereas a simple internal watchdog cannot.

Fourth, the internal watchdog is typically disabled by default and must be enabled by firmware. If the firmware fails to enable it during initialization due to an upset, the watchdog provides no protection at all. An external watchdog, by contrast, can be designed to be active from power-on, before the firmware even starts.

That said, I wouldn't completely dismiss the internal watchdog. It can be useful as a first line of defense, especially for detecting hard hangs. My recommendation would be to use both: the internal watchdog for fast detection of simple hangs, and an external watchdog with a longer timeout and independent clock for detecting more subtle failures. The external watchdog should also have a manual reset capability so that ground commands can force a system reset if needed.

I'd also ask the designer to consider what happens during a single-event latch-up (SEL). If the microcontroller latches up, the watchdog — internal or external — may not be able to reset it because the latch-up holds the device in a high-current state. In that case, the power supply's current-limiting circuit needs to detect the overcurrent condition and cycle power to the device. The watchdog can't do this alone.

**Possible follow-ups:** How would you design the external watchdog circuit to be independent of the microcontroller's power supply? What timeout values would you choose for the internal and external watchdogs?

---

## Q5: How would you approach designing a test plan to verify that a space-deployed system can recover from a single-event functional interrupt (SEFI) that causes the main microcontroller to stop executing code, when you cannot inject actual radiation events during ground testing?

**Answer:** Since we can't create real single-event effects in a ground test, the goal is to simulate the observable symptoms of a SEFI and verify that the system's recovery mechanisms work correctly. The test plan should focus on three aspects: fault injection, recovery verification, and stress testing.

For fault injection, I'd use a combination of approaches. The most direct method is to use the microcontroller's debug interface — JTAG or SWD — to halt the CPU, corrupt the program counter, or modify memory contents to simulate the effects of an upset. This can be automated to inject faults at random points during execution. Another approach is to use a hardware fault injection tool that can force signals on the bus or toggle reset lines. For firmware-level testing, I'd add a test hook — a special debug command or a test mode — that allows the test software to deliberately corrupt a known memory location or trigger a software reset.

The key is to inject faults at various points in the execution flow: during initialization, during normal operation, during a critical control loop, and during communication with other subsystems. Each fault injection should be followed by a verification that the system recovers within the expected time and that no data corruption or unsafe state occurs.

For recovery verification, I'd define clear pass/fail criteria. The system should detect the fault within a specified time, initiate recovery, and return to normal operation within a specified time. I'd also verify that the recovery process doesn't leave any subsystems in an inconsistent state — for example, if the microcontroller was in the middle of a communication transaction when the fault occurred, the recovery should not leave the communication bus in a locked state.

For stress testing, I'd run the system for extended periods with repeated fault injections to ensure that the recovery mechanism is reliable and doesn't degrade over time. I'd also test recovery under worst-case conditions: at temperature extremes, at minimum and maximum supply voltage, and with other subsystems actively communicating.

One important consideration is that the test should verify not just that the system recovers, but that it recovers correctly. For example, if the microcontroller was controlling a motor when the fault occurred, the recovery should ensure the motor is in a safe state before resuming normal operation. This requires careful design of the recovery sequence in firmware.

Finally, I'd document the test results and use them to refine the recovery mechanism. If the system fails to recover from a particular fault injection, that's a finding that needs to be addressed — either by improving the watchdog or recovery logic, or by adding additional fault detection mechanisms.

**Possible follow-ups:** How would you verify that the recovery mechanism itself hasn't been corrupted by the fault? How would you test the interaction between the watchdog and the power supply's current-limiting circuit during a simulated latch-up condition?