# space-rad-hard — Day 39

## Q1: How would you approach designing a fault-tolerant analog multiplexing scheme for a space-deployed system where a single-event transient (SET) on the mux select lines could route the wrong sensor channel to a precision ADC, potentially causing an incorrect control action?

**Answer:** This is a classic case where a single point of failure in the digital control path can corrupt an otherwise sound analog measurement chain. My approach would start with a risk assessment: what is the consequence of routing the wrong channel? If the wrong sensor reading could trigger an incorrect control action — say, commanding a heater or valve based on a false temperature — then this needs to be treated as a safety-critical path, not just a data-integrity issue.

At the architecture level, I would consider several complementary mitigations. First, I'd look at whether the mux select lines can be encoded with redundancy — for example, using a Gray-code or Hamming-distance-2 encoding so that a single-bit upset in the select word produces an invalid code rather than a valid-but-wrong channel. The firmware or a hardware decoder can then reject invalid codes and either hold the last known-good channel or default to a safe state. Second, I'd add a validation step after the conversion: if the system knows the expected range of each sensor, a plausibility check on the measured value can flag a likely wrong-channel reading. This requires the firmware to know which channel it *intended* to select and to verify the result is consistent with that expectation.

Third, I would consider adding a second level of protection at the system level — for example, a hardware interlock that prevents the actuator from responding to a single out-of-range reading, requiring either two consecutive consistent readings or a voting scheme across redundant measurements. This is particularly important in life-support or propulsion-type applications where a single spurious command could be dangerous.

Finally, I would look at the physical implementation: keeping the mux select lines short, properly terminated, and routed away from noisy digital traces reduces the probability of an SET coupling into them in the first place. If the mux itself is a COTS part with no radiation characterization, I would also consider whether a rad-hard or at least radiation-tested mux is warranted, or whether the system can tolerate occasional wrong-channel readings through the validation logic.

**Possible follow-ups:**
- How would you distinguish between a wrong-channel reading caused by an SET on the select lines versus a genuine sensor fault or an SET on the analog signal path itself?
- What if the system cannot afford the latency of a second conversion to confirm a reading — how would you handle that trade-off?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." How would you handle this disagreement?

**Answer:** I would acknowledge the engineer's point that the power level is modest, but I would reframe the discussion around what "risk" actually means in a space environment. The concern with an uncharacterized COTS regulator isn't just whether it can deliver 50mA — it's whether the part will behave correctly over the mission lifetime under total ionizing dose, whether it can survive single-event effects without latching up or producing output transients, and whether its parameters (output voltage, dropout, quiescent current) will drift outside specification. A low-power rail is not inherently low-risk; it's just low-current.

I would walk through the specific failure modes. A linear regulator is susceptible to TID-induced parameter drift — the bandgap reference can shift, causing the output voltage to move outside the tolerance required by the ADC or op-amp it feeds. More critically, a single-event latch-up in the regulator could create a low-impedance path from the input bus to ground, potentially dragging down the entire rail or even the upstream power bus. Even if the current is only 50mA in normal operation, a latch-up could draw far more and persist until power is cycled.

I would also point out that the absence of radiation data is not neutral — it's an unknown risk that must be either characterized, mitigated, or avoided. The options are: (1) select a part with existing radiation test data, (2) budget for radiation testing of this specific part, (3) add protection circuitry such as a current limiter or latch-up detection that can isolate the regulator, or (4) accept the risk through a formal risk assessment that documents why the consequences are tolerable. What I would *not* accept is dismissing the risk based on the low current alone.

I would also ask the engineer to consider what the analog rail feeds. If it's a precision reference or sensor bias supply, even small radiation-induced drift could degrade measurement accuracy over the mission. If it's a housekeeping rail, the consequences might be more tolerable. The criticality of the load matters as much as the current level.

**Possible follow-ups:**
- What specific radiation tests would you recommend for this regulator if the team decided to qualify it rather than replace it?
- How would you document the risk acceptance decision if the program decided to proceed with the COTS part anyway?

---

## Q3: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental requirement here is that the system must remain recoverable even if an update is corrupted mid-transfer or if the flash becomes partially corrupted by radiation. I would design the update strategy around three principles: redundancy, validation, and atomicity.

For redundancy, I would use at least two copies of the bootloader and ideally two banks of application firmware — a "golden" image that is known-good and a "working" image that can be updated. The bootloader should be stored in radiation-tolerant memory (or at least protected with strong ECC and periodic scrubbing) and should be immutable during normal operation — it should never be overwritten by an update process. The golden application image provides a fallback if the working image fails validation.

For validation, every update would include a checksum or cryptographic hash that is verified before the new image is committed. The bootloader would verify the integrity of the application image at every boot, not just after an update. If the working image fails validation, the bootloader falls back to the golden image. This catches both corrupted updates and radiation-induced bit flips in the stored firmware.

For atomicity, the update process should be designed so that a power loss or SEFI at any point leaves the system in a known state — either the old image is still intact, or the new image is fully written and validated. This typically means writing the new image to a separate flash region, validating it, and then atomically switching a pointer or flag that selects which image boots. The switch itself should be protected — for example, written twice with a checksum, or stored in a separate radiation-tolerant memory.

I would also consider adding a recovery mechanism for the case where both images are corrupted — for example, a hardware strap or command interface that forces the bootloader into a minimal recovery mode that can accept a new image over a serial or command link. This is a last resort, but it prevents a permanently bricked system.

Finally, I would think about the update trigger itself. The command to initiate an update should require authentication and should be robust against corrupted command streams — for example, a two-command sequence with a timeout, or a command that includes a nonce to prevent replay. The update process should also be resumable, so that a transient interruption doesn't require restarting from scratch.

**Possible follow-ups:**
- How would you handle the case where the golden image itself becomes corrupted over a long mission?
- What trade-offs would you consider between using external flash versus the microcontroller's internal flash for the application image?

---

## Q4: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** Clock distribution is one of those areas where a single failure can corrupt the entire system's timing, so I would approach it with redundancy and monitoring in mind. The first decision is the clock source: a single crystal oscillator is a single point of failure, so I would consider using two oscillators with a redundancy switch, or a PLL-based solution that can lock to either source. The switchover needs to be glitchless — a momentary clock dropout can cause FPGAs to lose lock, ADCs to produce garbage samples, and state machines to misbehave.

For the distribution network itself, I would use a dedicated clock buffer or fan-out chip rather than routing the clock through multiple devices. Each FPGA and ADC should receive its own buffered clock signal, with proper termination and impedance matching to avoid reflections and signal integrity issues. The trace lengths should be matched to minimize skew, and the clock traces should be routed away from noisy digital signals and protected from single-event transients that could couple into them.

For synchronized sampling, I would consider whether the system needs true simultaneous sampling or just known phase alignment. If the ADCs have a sample-clock input, they can all sample on the same edge of the distributed clock. If they use internal PLLs, I would add a synchronization pulse that resets all the PLLs to a known phase relationship after power-up or after any clock disturbance.

I would also add clock monitoring: a watchdog that detects clock loss or frequency drift and can trigger a failover to the redundant source or at least flag the fault. In a radiation environment, the clock buffer itself can experience single-event transients that cause a brief glitch on the output. If the glitch is short enough, the downstream PLLs may ride through it; if not, the system needs to detect and recover. This argues for monitoring at the point of use — for example, each FPGA can monitor its own clock input and report anomalies.

Finally, I would think about the failure modes of the oscillators themselves. A crystal oscillator can experience frequency shifts under TID, and a PLL can lose lock due to an SET. The system should be able to detect a loss-of-lock condition and reacquire, and the design should specify the maximum acceptable clock interruption that the system can tolerate without a reset.

**Possible follow-ups:**
- How would you verify that all ADCs are truly sampling synchronously after a clock switchover event?
- What would you do if the clock buffer itself is a COTS part with no radiation data — how would you qualify it or mitigate the risk?

---

## Q5: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS microcontroller for housekeeping. The microcontroller has a built-in watchdog timer that the firmware enables during initialization. The designer argues that the internal watchdog is sufficient and no external watchdog is needed. How would you handle this disagreement?

**Answer:** I would start by acknowledging that the internal watchdog is a reasonable first line of defense, but I would then walk through why it may not be sufficient in a radiation environment. The key issue is that the internal watchdog shares the same silicon as the processor it's supposed to monitor. A single-event functional interrupt (SEFI) that disrupts the processor core may also disrupt the watchdog timer — for example, if the SEFI corrupts the watchdog's configuration registers, disables the timer, or causes the clock feeding it to fail. In that case, the watchdog becomes part of the failure rather than a recovery mechanism.

I would also point out that an internal watchdog can be defeated by certain failure modes. If the processor hangs in a loop that continues to service the watchdog — for example, an interrupt handler that keeps resetting the timer while the main control loop is dead — the watchdog will never trigger. This is a well-known limitation of software-serviced watchdogs, and it's particularly relevant in radiation environments where a single upset can corrupt the program counter or interrupt vector table.

An external watchdog, by contrast, is physically separate from the processor. It has its own clock, its own power supply (ideally), and its own logic. It can be designed to require a specific sequence or pattern of pulses rather than a simple "kick," which makes it much harder for a corrupted processor to accidentally service it. It can also be designed to monitor not just the processor's heartbeat but also the health of the system — for example, by requiring the processor to toggle a GPIO in a specific pattern that the main control loop generates, rather than an interrupt handler.

I would also raise the question of what happens during a watchdog timeout. If the internal watchdog resets the processor but the reset signal is also corrupted by the same SEFI, the reset may not be clean. An external watchdog can provide a clean, well-characterized reset pulse and can also be used to power-cycle the processor if a simple reset is insufficient — for example, in the case of a latch-up that requires removing power to clear.

That said, I would not dismiss the internal watchdog entirely. The right answer is usually a layered approach: the internal watchdog provides fast recovery for minor upsets, while the external watchdog provides a backstop for more severe failures. The external watchdog should be independent — separate power domain, separate clock, and a service mechanism that the main control loop must actively drive.

**Possible follow-ups:**
- How would you design the external watchdog's service mechanism to be robust against a processor that is executing corrupted code?
- What would you do if the system has strict power constraints and adding an external watchdog IC is seen as an unacceptable overhead?