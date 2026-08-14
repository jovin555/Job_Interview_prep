# space-rad-hard — Day 24

## Q1: How would you approach designing a fault-tolerant analog output stage for a space-deployed system where a single-event transient (SET) on a DAC's reference voltage could cause a momentary but dangerous output spike to an actuator?

**Answer:** I'd approach this by first characterizing the failure path: an SET on the reference voltage directly modulates the DAC output, and if that output feeds an actuator without any filtering or limiting, a transient could translate into a physical response. The design strategy would be layered.

First, at the reference level, I'd use a reference with known radiation tolerance and add filtering—a low-pass filter on the reference output to attenuate fast transients, since SETs are typically short-duration events. The filter time constant needs to be slow enough to suppress the transient but fast enough not to degrade the DAC's settling time for legitimate updates.

Second, at the output stage, I'd add a hardware rate limiter or slew-rate limiter on the actuator drive signal. This ensures that even if the DAC output spikes, the actuator cannot respond fast enough to cause damage. For a motor or valve, this is often acceptable because the mechanical response is inherently slower than the electrical transient.

Third, I'd consider a windowed comparator or analog watchdog that monitors the output against expected bounds and triggers a shutdown or hold state if the output exceeds a safe envelope. This is particularly important for life-safety or mission-critical actuators where even a brief spike is unacceptable.

Finally, in firmware, I'd implement output validation—writing to the DAC only through a routine that checks the commanded value against rate and magnitude limits, and reading back the DAC output for verification. The combination of analog filtering, output limiting, and firmware validation provides defense in depth. The key trade-off is between transient suppression and system responsiveness, so I'd work with the systems engineer to define what transient duration and magnitude are actually dangerous before selecting filter values.

**Possible follow-ups:**
- How would you choose between an analog hardware limiter versus a firmware-based approach for output protection?
- What if the actuator requires fast response—how would you balance transient protection with performance requirements?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA and a COTS precision voltage reference for an ADC. The reference's datasheet specifies initial accuracy of ±0.1% and temperature drift of ±20 ppm/°C, but has no radiation data. The designer argues that because the reference is "precision" and the system has a calibration routine, radiation-induced drift can be calibrated out. How would you evaluate this approach?

**Answer:** I'd push back on the assumption that calibration can fully compensate for radiation-induced drift. Calibration is effective for systematic, predictable errors—like initial offset or temperature drift that follows a known curve. But radiation effects on a voltage reference are not necessarily monotonic or predictable. Total ionizing dose can cause gradual parametric shifts, but single-event transients can cause sudden, temporary jumps, and in some cases, latent damage can cause abrupt permanent shifts. A calibration routine performed at power-up or on a schedule cannot correct for a transient that occurs mid-measurement, and it cannot correct for a permanent shift if the calibration is not re-run after the event.

I'd also question the assumption that a "precision" part is inherently more radiation-tolerant. Precision and radiation tolerance are orthogonal properties. Some precision references use architectures—like buried zener diodes or chopper-stabilized amplifiers—that may have different radiation responses than bandgap references. Without test data, we're guessing.

My recommendation would be to either: (1) obtain radiation test data for the specific part, even if limited—a single heavy-ion or TID test run can reveal gross failure modes; (2) select a reference with known radiation characterization, even if it means accepting slightly worse initial accuracy; or (3) design the system to be tolerant of reference drift by using ratiometric measurement techniques where the reference error cancels out, or by including a second, known-good reference for periodic cross-calibration.

If the designer insists on using the COTS part, I'd require a risk assessment that quantifies the impact of reference drift on the specific measurements, and I'd add monitoring—for example, measuring the reference voltage against an internal bandgap or a second reference—to detect when drift has exceeded acceptable bounds.

**Possible follow-ups:**
- What ratiometric measurement techniques would you consider to reduce sensitivity to reference drift?
- How would you design a cross-calibration scheme with a second reference without adding significant cost or complexity?

---

## Q3: How would you approach designing a fault-tolerant boot sequence for a space-deployed system that uses an SRAM-based FPGA with external configuration memory (flash), where both the FPGA configuration bitstream and the flash memory are susceptible to single-event upsets?

**Answer:** The boot sequence needs to handle two distinct failure modes: the flash memory containing a corrupted bitstream, and the FPGA configuration SRAM being corrupted during or after loading. I'd design the boot sequence with multiple layers of protection.

First, the bitstream itself should be stored with error detection—typically a CRC or ECC appended to the configuration data. Before loading, the boot controller (which could be a rad-hard microcontroller or a CPLD) verifies the CRC of the bitstream in flash. If the CRC fails, it falls back to a redundant copy of the bitstream stored in a different memory region or a different device.

Second, during configuration, the FPGA's built-in configuration CRC checking—if available—should be enabled. Many SRAM FPGAs can continuously or periodically verify the configuration memory against an expected CRC. If a mismatch is detected, the FPGA can signal an error and trigger a reconfiguration.

Third, after configuration, the system should periodically scrub the configuration memory—reading back the configuration frames and correcting single-bit upsets or reloading if multiple-bit upsets are detected. Scrubbing can be done by the FPGA itself if it supports partial reconfiguration, or by an external controller that reloads the full bitstream.

Fourth, the boot controller itself needs protection. If it's a microcontroller, it should have its own watchdog and error-handling. If it's a CPLD, it's likely more radiation-tolerant but still needs a defined state machine that handles all possible failure paths.

Finally, I'd design the boot sequence to be observable—logging boot attempts, CRC failures, and reconfiguration events to telemetry so that ground operators can diagnose issues. The key principle is that no single point of failure should prevent the system from eventually reaching a known-good configuration state.

**Possible follow-ups:**
- How would you decide between continuous scrubbing versus periodic full reconfiguration?
- What happens if both copies of the bitstream in flash are corrupted—how would you handle that scenario?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA and a COTS DC-DC converter. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, and the FPGA's absolute maximum rating is 3.6V. A junior engineer argues that the 130 mV margin is acceptable because "the FPGA will never actually see 3.47V in practice—the converter will typically output 3.3V, and the FPGA's absolute maximum rating already includes some safety margin." How would you handle this disagreement?

**Answer:** I'd acknowledge that the engineer's reasoning has some surface validity—typical operating conditions are indeed below the worst-case specification, and absolute maximum ratings do include some margin. However, I'd explain that this reasoning is flawed for space applications for several reasons.

First, absolute maximum ratings are not "recommended operating conditions"—they are stress limits. Exceeding them, even briefly, can cause latent damage that may not manifest immediately but could reduce the device's lifetime or cause failure years into the mission. We cannot accept any design that operates at or near an absolute maximum rating under any specified condition.

Second, the worst-case conditions in the datasheet—such as maximum input voltage, minimum load, and temperature extremes—are not theoretical. In a space environment, the converter's input voltage can vary significantly, and load conditions change as subsystems power up and down. The system must be designed to meet specifications across the entire operating envelope, not just at nominal conditions.

Third, there are transient conditions to consider. During load steps or power-up, the converter's output can overshoot beyond the steady-state specification. The 3.47V maximum might be a steady-state limit, but transient overshoot could push the output even higher. We need to verify the converter's transient response and ensure that overshoot is accounted for.

Fourth, radiation effects can shift the converter's output voltage over mission life. Total ionizing dose can cause reference drift or changes in feedback loop parameters, potentially pushing the output voltage higher than the fresh part's worst-case specification.

My recommendation would be to either: (1) select a converter with a tighter output voltage specification that provides more margin; (2) add a post-regulator or voltage clamp to ensure the FPGA supply never exceeds a safe limit; or (3) perform additional characterization—including radiation testing—to better understand the converter's actual worst-case behavior. But I would not accept the design as-is based on the argument that "it will probably be fine."

**Possible follow-ups:**
- What level of margin would you consider acceptable between the converter's maximum output and the FPGA's absolute maximum rating?
- How would you verify the converter's transient response under worst-case load conditions?

---

## Q5: How would you approach designing a test plan to verify that a space-deployed system can recover from a single-event functional interrupt (SEFI) that causes the main microcontroller to stop executing code, when you cannot inject actual radiation events during ground testing?

**Answer:** Since we can't create real radiation events in most ground test environments, the test plan needs to simulate the effects of a SEFI through other means. The goal is to verify that the recovery mechanisms—watchdog timers, reset logic, boot sequence—work correctly when the processor stops executing code or enters an undefined state.

The first approach is fault injection through debug interfaces. If the microcontroller has a JTAG or SWD port, I can halt execution, corrupt the program counter, or modify memory contents to simulate the effects of a SEFI. This tests whether the watchdog timer fires and whether the reset sequence properly reinitializes the system.

The second approach is to use the watchdog timer itself as the fault injection mechanism. I can write test firmware that deliberately stops servicing the watchdog, or enters an infinite loop, to verify that the watchdog resets the system within the expected timeout. This tests the basic recovery path.

The third approach is to simulate the electrical effects of a SEFI. For example, I can use a test point to momentarily short the reset line, or use a function generator to inject a glitch into the clock or power supply, to verify that the reset circuitry responds correctly.

The fourth approach is software-based fault injection at the application level. I can write test harnesses that corrupt critical data structures, flip bits in RAM, or corrupt the stack pointer, then verify that error detection mechanisms catch the fault and trigger recovery.

For each test, I'd define pass criteria: the system must recover within a specified time, return to a known-good state, and either resume normal operation or enter a safe state with telemetry indicating the fault. I'd also test recovery from multiple consecutive faults to ensure the recovery mechanism itself isn't damaged or exhausted.

Finally, I'd document the test coverage and any gaps—for example, we can't easily simulate a SEFI that corrupts the watchdog timer itself, so we rely on the external watchdog as a backup. The test plan should explicitly acknowledge these limitations and describe how the design mitigates them.

**Possible follow-ups:**
- How would you test recovery from a SEFI that corrupts the processor's configuration registers rather than just halting execution?
- What telemetry would you add to the system to help diagnose SEFI events during actual mission operation?