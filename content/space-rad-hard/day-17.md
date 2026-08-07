# space-rad-hard — Day 17

## Q1: How would you approach designing a radiation-tolerant watchdog and reset management scheme for a system where the main microcontroller can experience single-event functional interrupts (SEFIs) that halt execution, but where a simple external watchdog timeout might not be sufficient because the processor can also hang in a state where it continues toggling a "heartbeat" GPIO?

**Answer:** The key insight is that a heartbeat-based watchdog only proves that *some* code path is executing — it doesn't prove that the *correct* code path is executing. In a radiation environment, a SEFI can corrupt the program counter, stack pointer, or interrupt controller state in ways that leave a periodic GPIO toggle running while the actual application logic is dead. I would approach this with a layered strategy:

First, I'd use a windowed watchdog rather than a simple timeout watchdog. A windowed watchdog requires the heartbeat to occur *within* a specific time window — not too early and not too late. This catches both "stuck" states (no heartbeat) and "runaway" states (heartbeat too fast, e.g., a corrupted loop that executes the toggle repeatedly). The window parameters should be derived from the worst-case execution time of the main control loop, with margin.

Second, I'd add a *qualitative* heartbeat: instead of just toggling a GPIO, the firmware should write a sequence of distinct values (e.g., a pseudo-random or incrementing pattern) to a register or memory location that the external watchdog monitors. If the watchdog sees the same value repeated or a value out of sequence, it resets the system. This catches the case where the processor is stuck in a tight loop that happens to include the GPIO toggle.

Third, I'd implement a *software* watchdog hierarchy inside the firmware: a low-priority task that checks the health of higher-priority tasks by verifying they've updated their own "alive" flags within their expected periods. If a task hasn't run, the health monitor can attempt a controlled recovery (e.g., reinitialize that task's state) before escalating to a full system reset.

Finally, I'd make the reset path itself robust: the watchdog should drive a dedicated reset IC with a manual reset input, not just the microcontroller's reset pin. The reset IC should have a guaranteed minimum reset pulse width and should also reset any external peripherals that might be in a corrupted state. I'd also consider having the watchdog power-cycle the system rather than just assert reset, because some SEFI states (e.g., latch-up in internal logic) may not clear with a simple reset.

**Possible follow-ups:** How would you choose the watchdog timeout window to avoid false resets during normal operation? What if the watchdog itself is a COTS part with no radiation characterization — how would you mitigate that risk?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS microcontroller for housekeeping. The microcontroller has a built-in watchdog timer that the firmware enables during initialization. The designer argues that the internal watchdog is sufficient and no external watchdog is needed. How would you evaluate this approach?

**Answer:** I would push back on relying solely on the internal watchdog, and here's why: the internal watchdog shares the same silicon, the same power supply, and the same clock domain as the processor it's supposed to monitor. A single-event effect that corrupts the processor core — for example, a SEFI that disrupts the clock generation or the power distribution inside the chip — is very likely to also disable or corrupt the watchdog. The whole point of a watchdog in a radiation environment is *diversity*: an independent, external mechanism that can recover the system even when the primary processor is completely non-functional.

That said, I wouldn't dismiss the internal watchdog entirely. It can be useful as a *first line* of defense for catching software hangs (e.g., infinite loops, deadlocks) that don't involve hardware corruption. But I would treat it as complementary, not sufficient.

My recommendation would be:
- Keep the internal watchdog enabled as a fast-response mechanism for software faults.
- Add an external watchdog with a *longer* timeout than the internal one. The external watchdog serves as the final safety net: if the internal watchdog fails to fire (because it's also corrupted) or if the processor is in a state where it can't service either watchdog, the external one will eventually reset the system.
- Use a windowed external watchdog if possible, to catch both "no heartbeat" and "heartbeat too fast" conditions.
- Ensure the external watchdog has its own independent clock source (e.g., a separate oscillator) and its own power supply filtering, so it's not vulnerable to the same single-event effects as the microcontroller.
- Consider having the external watchdog drive a power-cycle circuit (e.g., a load switch on the microcontroller's supply) rather than just a reset pin, because some SEFI states require a full power cycle to clear.

The cost of an external watchdog is small — a few dollars and a few square millimeters of board area — compared to the cost of losing a mission because the processor locked up and the internal watchdog was also dead.

**Possible follow-ups:** How would you test that the external watchdog actually recovers the system from a SEFI, given that you can't easily inject a SEFI in ground testing? What if the external watchdog itself is a COTS part with no radiation data — how would you qualify it?

---

## Q3: How would you approach designing a fault-tolerant boot sequence for a space-deployed system that uses a radiation-hardened FPGA with external configuration memory (flash), where the flash can experience single-event upsets that corrupt the configuration bitstream?

**Answer:** The boot sequence is one of the most critical phases in a space system because a failure here can leave the system in an unrecoverable state. I'd approach this with a multi-layered strategy:

**Layer 1: Configuration memory protection.** The flash storing the bitstream should have error detection and correction. If the flash has built-in ECC, use it. If not, I'd add a checksum or CRC over the entire bitstream. The FPGA configuration logic should verify this checksum after loading and before releasing the FPGA from configuration mode. If the checksum fails, the FPGA should not start, and the system should retry.

**Layer 2: Redundant configuration copies.** Store at least two, ideally three, copies of the bitstream in the flash, each with its own checksum. The boot controller (which could be a small CPLD or the system microcontroller) should attempt to load copy A; if the checksum fails, it falls back to copy B, then copy C. If all copies fail, the system should signal a fault and enter a safe state rather than repeatedly retrying.

**Layer 3: Scrubbing during operation.** After successful configuration, the configuration memory of an SRAM-based FPGA remains vulnerable to SEUs. I'd implement a scrubber — either in the FPGA fabric itself or in an external controller — that continuously reads back the configuration frames and compares them against a golden copy. When a mismatch is found, the scrubber rewrites just that frame. The scrub rate should be fast enough to correct errors before they accumulate to a point where the design's functionality is compromised.

**Layer 4: Reconfiguration on failure.** If the FPGA detects a configuration error that can't be corrected by scrubbing (e.g., a multi-bit upset in a critical frame), it should signal the boot controller, which then initiates a full reconfiguration from the flash. This reconfiguration should be a *controlled* process: the system should first bring any connected peripherals into a safe state, then reconfigure, then verify the new configuration, then resume operation.

**Layer 5: Boot controller robustness.** The boot controller itself must be radiation-tolerant. If it's a CPLD, it should be a rad-hard or at least radiation-characterized part. If it's the system microcontroller, it needs its own watchdog and recovery mechanism, because a corrupted boot controller means the FPGA can never be configured.

One additional consideration: the flash itself can experience upsets *during* the configuration read. So the checksum verification should be done on the data as it's loaded, not just on the stored data. Some FPGAs support this natively; if not, the boot controller can read the bitstream, compute the checksum, and only then present it to the FPGA.

**Possible follow-ups:** How would you choose between scrubbing from an external controller versus a soft scrubber implemented in the FPGA fabric? What if the flash is also used for storing telemetry or other data — how would you partition it to avoid conflicts?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA and a COTS DC-DC converter. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, and the FPGA's absolute maximum rating is 3.6V. A junior engineer argues that the 130 mV margin is acceptable because "the FPGA will never actually see 3.47V in practice." How would you handle this disagreement?

**Answer:** I would acknowledge the engineer's point that the worst-case condition may be unlikely, but I would firmly push back on accepting the design as-is. Here's my reasoning:

First, the 130 mV margin is not a safety margin — it's the difference between two *datasheet* limits. The FPGA's absolute maximum rating of 3.6V is not a "recommended operating condition"; it's the limit beyond which damage *may* occur. The converter's 3.47V maximum is a *guaranteed* limit under worst-case conditions (e.g., minimum input voltage, maximum load, worst-case temperature, part-to-part variation). When you stack these worst cases, you're already at 3.47V. Now add any transient overshoot during load steps, any noise coupling from switching, any measurement error in your own monitoring circuitry — and you can easily exceed 3.6V.

Second, in a space environment, you have additional factors that the datasheet doesn't cover: total ionizing dose can shift the converter's reference voltage and feedback network, potentially increasing the output voltage beyond the pre-radiation worst case. Single-event transients on the feedback pin can cause output voltage spikes. These effects are not captured in the COTS datasheet at all.

Third, the cost of a failure is catastrophic: a damaged FPGA in a space system is unrecoverable. The cost of mitigation is small. I would recommend one or more of the following:
- Add a voltage supervisor that monitors the 3.3V rail and asserts a reset or disconnects the load if the voltage exceeds a safe threshold (e.g., 3.5V).
- Add a series element (e.g., a small LDO or a load switch with current limiting) between the converter and the FPGA to guarantee the voltage stays within the FPGA's recommended operating range.
- Add output voltage clamping (e.g., a shunt regulator or TVS diode) to absorb transient overshoots.
- Re-evaluate the converter selection: is there a part with tighter output voltage tolerance, or one that's radiation-characterized?

I would also frame this as a *risk management* discussion, not a personal criticism. The question isn't "will it fail?" — it's "what is the probability of failure, what is the consequence, and is the mitigation cost justified?" In a space system, the consequence is mission loss, so even a low-probability risk deserves serious mitigation if the cost is reasonable.

**Possible follow-ups:** How would you quantify the risk of the output voltage exceeding 3.6V, given that you don't have radiation data for the converter? What if the only available mitigation adds significant board area and mass — how would you trade that off against the risk?

---

## Q5: How would you approach designing a test plan to verify that a space-deployed system can recover from a single-event functional interrupt (SEFI) that causes the main microcontroller to stop executing code, when you cannot inject actual radiation events during ground testing?

**Answer:** Since you can't reproduce a true SEFI on the ground, the goal of the test plan is to *simulate* the observable symptoms of a SEFI and verify that the recovery mechanisms respond correctly. I'd structure the plan around three categories: fault injection, recovery verification, and stress testing.

**Fault injection:** The most direct approach is to force the microcontroller into a state that mimics a SEFI. Methods include:
- **Halt the core:** Use a debugger (JTAG/SWD) to halt the CPU mid-execution, then disconnect the debugger and verify that the watchdog eventually resets the system.
- **Corrupt the program counter:** Use the debugger to set the PC to an invalid address (e.g., 0xFFFFFFFF) and verify the system recovers.
- **Corrupt memory:** Use the debugger to write garbage values into critical RAM locations (stack pointer, interrupt vector table, task control blocks) and verify the system detects the corruption and recovers.
- **Disable interrupts:** Temporarily disable all interrupts in software (simulating a SEFI that corrupts the interrupt controller) and verify the watchdog still fires.
- **Brown-out simulation:** Drop the supply voltage below the reset threshold briefly, then restore it, to verify the power-on reset sequence works correctly.

For each injection, the test should verify: (a) the system detects the fault (if detection is expected), (b) the recovery mechanism triggers within the expected time, (c) the system returns to a known-good state, and (d) any critical data or state is either preserved or safely reinitialized.

**Recovery verification:** After each fault injection, verify not just that the system resets, but that it *resumes correct operation*. This means checking that all peripherals are reinitialized, communication links are re-established, and the system returns to its normal operating mode within a specified time. I'd also verify that the system doesn't get stuck in a reset loop — e.g., if the fault persists (because the underlying cause is still present), the system should eventually enter a safe state rather than cycling forever.

**Stress testing:** Run the system for extended periods (days to weeks) with the watchdog enabled and the system operating normally, to verify there are no false resets due to watchdog timeouts during legitimate long-duration operations. This is especially important if the watchdog window is tight.

**Additional considerations:**
- Document the exact procedure for each fault injection so tests are repeatable.
- Use a logic analyzer or a separate monitoring system to timestamp the fault injection, the watchdog timeout, and the system recovery, so you can measure recovery time.
- If the system has multiple recovery mechanisms (internal watchdog, external watchdog, power-cycle), test each one individually and in combination.
- Finally, I'd review the test results against the system's fault recovery requirements (e.g., "system shall recover within 100 ms of a SEFI") and identify any gaps.

**Possible follow-ups:** How would you test recovery from a SEFI that corrupts the external watchdog itself, rather than the main processor? How would you verify that the recovery sequence doesn't leave any peripherals in an inconsistent state?