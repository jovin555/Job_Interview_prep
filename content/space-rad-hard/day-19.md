# space-rad-hard — Day 19

## Q1: How would you approach designing a radiation-tolerant voltage supervisor and reset generation circuit for a system where the main processor can experience single-event functional interrupts (SEFIs) that halt execution, but the processor's internal watchdog may also be affected by radiation?

**Answer:** The fundamental issue here is that any reset mechanism that shares the same silicon as the processor is vulnerable to the same radiation effects. I would design a layered reset architecture with diversity at each level.

First, I'd use an external, radiation-hardened voltage supervisor with a manual reset input, separate from the processor. This provides a guaranteed reset path that doesn't depend on the processor's internal logic. The supervisor should have a well-defined reset threshold with hysteresis to prevent oscillation during power transients, and its reset output should be debounced and glitch-filtered.

Second, I'd add an external watchdog timer as a separate IC, ideally with a different process technology or at least a different manufacturer than the processor, to reduce common-mode failure risk. The watchdog should be fed by a heartbeat signal that the firmware must toggle through a sequence — not just a simple GPIO toggle, because a processor stuck in a tight loop could still toggle a GPIO. The sequence could be a specific pattern written to a register or a series of addresses accessed in a particular order.

Third, I'd implement a "reset chain" in firmware: the processor's boot code checks a non-volatile reset counter. If the system has reset more than a threshold number of times within a short window, the firmware enters a safe mode that disables non-essential peripherals and runs at reduced functionality, rather than repeatedly attempting full operation.

Finally, I'd consider a hardware-based "heartbeat monitor" using a small CPLD or discrete logic that monitors multiple signals from the processor — not just one heartbeat line but also bus activity or a combination of GPIOs — to detect a hung state more reliably than a single watchdog.

The key design principle is diversity: different failure modes require different detection mechanisms, and no single component should be a single point of failure for system recovery.

**Possible follow-ups:**
- How would you choose between an internal watchdog, external watchdog, and a combination of both?
- What failure modes would you specifically test for in the reset generation circuit during radiation testing?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS microcontroller for housekeeping. The microcontroller has a built-in watchdog timer that the firmware enables during initialization. The designer argues that the internal watchdog is sufficient and no external watchdog is needed. How would you evaluate this approach?

**Answer:** I would push back on this approach, but I'd frame my concerns constructively. The internal watchdog is a useful first line of defense, but it has fundamental limitations in a radiation environment.

First, the internal watchdog shares the same silicon as the processor core. A single-event effect that disrupts the watchdog's timer circuitry, its configuration registers, or the clock source it depends on could disable it or cause it to malfunction. If the watchdog's configuration register gets upset and disables the watchdog, the processor could hang with no recovery path.

Second, a single-event functional interrupt (SEFI) can cause the processor to enter a state where it continues executing code — including toggling the watchdog heartbeat — but the code is corrupted or executing from the wrong location. The internal watchdog would see the heartbeat and assume everything is fine.

Third, the internal watchdog's timeout period is often limited to a narrow range, and it may not be adjustable to accommodate different operational modes (e.g., a low-power sleep mode vs. active processing).

My recommendation would be to use an external watchdog as a mandatory complement, not a replacement. The external watchdog should have:
- A longer, programmable timeout period
- A windowed mode that detects both too-frequent and too-infrequent heartbeats
- A separate clock source (e.g., its own oscillator) so it doesn't depend on the processor's clock
- A manual reset input for testability

I'd also recommend that the external watchdog's heartbeat be driven by a firmware task that runs at a controlled rate, not just a bare-metal GPIO toggle, so that a stuck interrupt handler or a corrupted scheduler doesn't accidentally keep the watchdog satisfied.

The cost of an external watchdog is trivial compared to the cost of a mission failure due to an unrecoverable processor hang.

**Possible follow-ups:**
- What if the designer argues that the external watchdog adds too much board space and power for a small satellite?
- How would you verify that the external watchdog actually resets the processor under a simulated SEFI condition?

---

## Q3: How would you approach designing a fault-tolerant boot sequence for a space-deployed system that uses an SRAM-based FPGA with external configuration memory (flash), where both the FPGA configuration bitstream and the flash memory are susceptible to single-event upsets?

**Answer:** This is a multi-layered problem because you have two distinct failure modes: the flash can experience bit flips that corrupt the stored bitstream, and the FPGA's SRAM configuration cells can be upset after loading. The boot sequence needs to handle both.

For the flash corruption issue, I'd start with error detection and correction on the stored bitstream. The simplest approach is to store a CRC or checksum alongside the bitstream and verify it before loading. For stronger protection, I'd use an error-correcting code (ECC) — either SEC-DED on the flash data or a redundant copy of the bitstream. A common approach is to store two or three copies of the bitstream in different flash regions and use a majority vote or fallback chain during boot.

The boot sequence itself should be a state machine with explicit error handling:
1. The configuration controller (which could be a CPLD, a radiation-hardened microcontroller, or the FPGA's own configuration logic) reads the first bitstream copy.
2. It verifies the CRC or ECC before initiating configuration. If the check fails, it moves to the next copy.
3. If all copies fail verification, the system enters a "safe mode" where it signals an error and waits for a command from the ground or a higher-level controller — it should not attempt to load a corrupted bitstream.
4. After successful configuration, the FPGA's configuration CRC checker (if available) should be enabled to detect post-configuration upsets in the configuration memory.

For the post-configuration upsets, I'd implement a scrubbing mechanism. This could be:
- **Blind scrubbing:** The configuration controller continuously re-reads the bitstream from flash and rewrites it to the FPGA, regardless of whether an error is detected. This is simple but consumes power and can interfere with operation.
- **Readback scrubbing:** The controller periodically reads back the FPGA's configuration memory, compares it to the golden copy, and corrects any discrepancies. This is more efficient but requires the FPGA to support configuration readback.

The boot controller itself needs to be radiation-tolerant — if it's a COTS microcontroller, it needs its own watchdog and error recovery. I'd also consider using a CPLD or a simple state machine implemented in radiation-hardened logic for the boot controller, since it's a critical single point of failure.

Finally, I'd design the boot sequence to be restartable: if the FPGA fails to configure or fails post-configuration verification, the system should be able to power-cycle the FPGA and retry, with a limited number of retries before entering safe mode.

**Possible follow-ups:**
- How would you choose between blind scrubbing and readback scrubbing for a system with limited power budget?
- What happens if the flash itself is corrupted during the mission and all copies are bad?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA and a COTS DC-DC converter. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, and the FPGA's absolute maximum rating is 3.6V. A junior engineer argues that the 130 mV margin is acceptable because "the FPGA will never actually see 3.47V in practice." How would you handle this disagreement?

**Answer:** I would treat this as a teaching moment about worst-case analysis and design margin, not just a technical disagreement. The engineer's argument is based on an assumption that the worst-case conditions won't occur, which is exactly the kind of thinking that leads to field failures.

I'd walk through the analysis systematically. The 3.47V maximum is the converter's specified limit under worst-case conditions — which includes maximum input voltage, minimum load, maximum temperature, and part-to-part variation. The FPGA's 3.6V absolute maximum is the limit beyond which damage can occur, not the recommended operating range. The actual recommended operating range for the FPGA core voltage is typically much tighter, say 3.3V ±5% (3.135V to 3.465V). So the real question is whether the converter's output can stay within the FPGA's recommended range, not just below the absolute maximum.

I'd also point out that the 130 mV margin is not a static number. It shrinks when you consider:
- Load transients: when the FPGA switches between low-power and high-power states, the converter's output can overshoot or undershoot.
- Temperature drift: both the converter's reference and the FPGA's threshold voltages drift with temperature.
- Aging: component parameters drift over the mission lifetime.
- Radiation effects: TID can cause shifts in the converter's reference voltage and the FPGA's input thresholds.
- Measurement error: the actual voltage at the FPGA's power pin may differ from the voltage measured at the converter's output due to PCB trace resistance and inductance.

The correct approach is to perform a worst-case analysis that includes all of these factors, and then add margin on top of that. If the analysis shows that the converter's output can exceed the FPGA's recommended range under any credible combination of conditions, the design needs to change — either by adding a post-regulator, using a different converter, or adding a load that keeps the converter in a more favorable operating region.

I'd also suggest a practical test: measure the converter's output voltage across the full input voltage range, load range, and temperature range during design verification. If the measured values approach the FPGA's limits, that's a red flag even if the analysis says it's technically within spec.

The key message to the engineer: in space systems, you design for the worst case, not the typical case, because you can't send a technician to fix a board that fails in orbit.

**Possible follow-ups:**
- What if the engineer responds that the FPGA's absolute maximum rating is 3.6V and the converter's maximum is 3.47V, so there's still 130 mV of margin even in the worst case?
- How would you quantify the additional margin needed for radiation-induced parameter drift?

---

## Q5: How would you approach designing a test plan to verify that a space-deployed system can recover from a single-event functional interrupt (SEFI) that causes the main microcontroller to stop executing code, when you cannot inject actual radiation events during ground testing?

**Answer:** Since you can't create real radiation events in a typical lab, the test plan needs to simulate the *effects* of a SEFI through fault injection at multiple levels. The goal is to verify that the recovery mechanisms work, not to test the radiation susceptibility of the components — that's a separate radiation test at a particle accelerator.

I'd structure the test plan in four layers:

**Layer 1: Firmware-level fault injection.** The most direct approach is to add test hooks in the firmware that can simulate a hang or a corrupted state. For example:
- A test command that puts the processor into an infinite loop with interrupts disabled, simulating a SEFI that halts execution.
- A test command that corrupts the watchdog heartbeat sequence, simulating a processor that's executing but not functioning correctly.
- A test command that jumps to an invalid memory address, simulating a corrupted program counter.

Each of these tests verifies that the watchdog or external supervisor detects the fault and resets the system, and that the boot sequence completes successfully.

**Layer 2: Hardware-level fault injection.** To test the reset generation circuitry itself, I'd use a function generator or a relay to force the reset line low, simulating a supervisor timeout. I'd also test the power-on reset behavior by cycling power with controlled rise times and verifying that the system initializes correctly.

**Layer 3: Bus-level fault injection.** If the system has multiple processors or peripherals on a shared bus, I'd inject bus errors — such as stuck lines, corrupted data, or spurious interrupts — to verify that the system can detect and recover from a bus-level fault without requiring a full reset.

**Layer 4: System-level fault injection.** The most realistic simulation is to use a debugger or JTAG interface to halt the processor mid-execution, corrupt a register or memory location, and then release it. This simulates a single-event upset in the processor's internal state. I'd also test recovery from a "brownout" condition by momentarily dropping the supply voltage below the reset threshold.

For each test, I'd define pass criteria: the system must reset within a specified time, boot successfully, and resume normal operation without operator intervention. I'd also verify that the system logs the reset event with a timestamp and a reset cause code, so that post-mission analysis can distinguish between expected resets and unexpected ones.

Finally, I'd document the test coverage and identify any gaps — for example, faults that can't be simulated with the available test equipment — and note those as residual risks that need to be addressed through radiation testing or design analysis.

**Possible follow-ups:**
- How would you verify that the system's recovery time meets the mission requirements?
- What would you do if a fault injection test reveals that the system does not recover reliably?