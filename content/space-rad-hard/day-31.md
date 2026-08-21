# space-rad-hard — Day 31

## Q1: How would you approach designing a radiation-tolerant data acquisition system where a single-event transient (SET) on the ADC's input multiplexer could cause a spurious reading that triggers an incorrect control action?

**Answer:** The first step is to recognize that an SET on the analog front-end is fundamentally different from a digital SEU—it's a transient analog disturbance that can propagate through the signal chain before any digital voting can catch it. My approach would be multi-layered:

**At the analog level:** I'd add filtering appropriate to the signal bandwidth. For slow-moving sensor signals, a simple RC low-pass filter at the ADC input with a time constant longer than the expected SET duration (typically nanoseconds to microseconds) can attenuate most transients. For faster signals, I'd consider a sample-and-hold architecture where the sampling window is short relative to the expected SET duration, reducing the probability of sampling during a transient.

**At the conversion level:** I'd implement redundant sampling—take multiple consecutive samples and use median or majority voting rather than a single sample. This is particularly effective because SETs are typically single-event phenomena; the probability of two independent SETs corrupting two consecutive samples is extremely low. The trade-off is reduced effective sampling rate, which must be weighed against the system's bandwidth requirements.

**At the system level:** I'd add plausibility checking in firmware. For each reading, compare against the previous value and a rate-of-change limit derived from the physical system's maximum slew rate. If a reading exceeds this limit, flag it as suspect and either re-sample or hold the previous valid value. This is especially important in control loops where a spurious reading could command an actuator to an unsafe position.

**At the output stage:** For critical control outputs, I'd add a rate limiter or a "safe value" hold that prevents any single reading from causing a large, instantaneous change in the output. This provides a final layer of protection even if a transient slips through the earlier stages.

The key design principle is defense in depth—no single mitigation is sufficient, and the layers must be designed to be independent so that a failure in one doesn't compromise the others.

**Possible follow-ups:**
- How would you determine the appropriate time constant for the input filter without degrading the signal you're trying to measure?
- How would you handle the trade-off between redundant sampling and the system's required update rate?

---

## Q2: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." How would you handle this disagreement?

**Answer:** I'd approach this as a risk assessment discussion rather than simply overriding the engineer's decision. The core issue isn't the voltage or current—it's that we have no data on how this part behaves under radiation, and the analog rail's integrity directly affects measurement accuracy across the mission.

I'd start by acknowledging the engineer's practical perspective: a low-power, low-voltage rail seems benign, and using a COTS part saves cost and schedule. Then I'd walk through the specific radiation concerns:

**TID effects:** Many linear regulators show parametric drift with total dose—output voltage shifts, dropout voltage increases, and quiescent current rises. For an analog rail, even a 1-2% drift in output voltage could degrade ADC reference accuracy or sensor bias points, potentially violating the measurement error budget.

**ELDRS concern:** Bipolar linear regulators are particularly susceptible to enhanced low-dose-rate sensitivity (ELDRS). Testing at high dose rate can significantly underestimate degradation at the low dose rates seen in space. Without radiation data, we can't bound this risk.

**Single-event effects:** A single-event transient on the regulator output could couple directly into the analog signal chain, causing a spurious reading. A single-event latch-up could cause a hard failure of the rail.

I'd then propose a path forward that addresses the engineer's concerns about cost and schedule:
- First, check if there's a radiation-qualified equivalent from a known vendor—even if it costs more, the qualification data may be worth it.
- If budget is truly constrained, propose a limited radiation test campaign (even a single TID test at a relevant dose rate, plus a basic SEE test) to characterize the part.
- As an interim mitigation, add output filtering and a voltage supervisor that can detect and respond to transient or permanent failures.

The goal is to move from "we don't know" to "we know enough to make an informed decision," rather than accepting risk by default.

**Possible follow-ups:**
- What specific radiation tests would you prioritize if you could only afford one test on this regulator?
- How would you quantify the risk of using this part without testing, and how would you present that risk to program management?

---

## Q3: How would you approach designing a fault-tolerant communication protocol between two FPGAs over a high-speed serial link, where single-event upsets can corrupt both the data payload and the link synchronization state?

**Answer:** This requires addressing two distinct failure domains: data corruption and link-level state corruption. My approach would be:

**Data integrity layer:** At minimum, I'd use a CRC or checksum on every packet. For critical data, I'd add sequence numbers and a retransmission mechanism at the protocol level, even if the physical layer doesn't provide it. The key is that the receiving FPGA must be able to detect corruption and request retransmission, or the sender must periodically send redundant copies.

**Link synchronization protection:** The more challenging problem is when an SEU corrupts the link's synchronization state—for example, the receiver's clock-data recovery (CDR) circuit locks onto the wrong phase, or the frame alignment state machine enters an invalid state. I'd address this with:

- **Periodic sync patterns:** Insert known sync words or training sequences at regular intervals. The receiver can use these to verify alignment and re-synchronize if needed.
- **State machine protection:** Implement the frame alignment state machine with error detection—if the receiver detects an invalid number of consecutive errors, it should force a re-synchronization rather than remaining in a stuck state.
- **Watchdog on link health:** Monitor link-level statistics (bit error rate, sync loss count) and trigger a full link reset if thresholds are exceeded.

**Protocol-level recovery:** The protocol should define a recovery sequence that both ends can initiate. This might include a "link reset" command that forces both FPGAs to re-initialize the link state machines, followed by a re-synchronization handshake.

**Redundancy options:** For truly critical links, I'd consider redundant physical channels with automatic failover, or a scheme where the same data is sent over two independent links and compared at the receiver. This is expensive but provides the strongest guarantee.

**Testing approach:** I'd develop fault-injection tests that corrupt specific bits in the data stream and in the link control state to verify that the recovery mechanisms work as designed. This is essential because link-level faults are often the hardest to reproduce and debug.

**Possible follow-ups:**
- How would you choose between a custom protocol and a standard one like SpaceWire or GigaSpace?
- What metrics would you use to monitor link health, and at what thresholds would you trigger a reset?

---

## Q4: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental requirement is that the system must remain recoverable even if an update fails or the update process itself is corrupted. My approach would be built around several key principles:

**Dual-bank architecture:** The most robust approach is to have two independent flash banks—one containing the current "known good" firmware and one for the new update. The bootloader always boots from the known-good bank unless explicitly commanded otherwise. Only after the new firmware passes validation (CRC check, version check, possibly a self-test) is it promoted to the active bank. This ensures that a corrupted update never leaves the system without a bootable image.

**Bootloader protection:** The bootloader itself must be in a separate, write-protected region of flash that cannot be modified by the application. This is the "root of trust" that guarantees the system can always boot and accept a new update.

**Update validation:** Before committing an update, the system should verify:
- The complete image CRC matches the expected value
- The image is internally consistent (e.g., checksums on individual sections)
- The version is compatible with the current hardware and bootloader

**Atomic commit:** The commit process should be atomic—either the new firmware is fully validated and promoted, or the system continues using the old firmware. There should be no intermediate state where the system is running partially-updated code.

**Recovery from failed update:** If the system fails to boot from the new image (e.g., watchdog timeout during initialization), the bootloader should automatically fall back to the known-good image. This requires the bootloader to have a "boot attempt counter" that increments on each failed boot and triggers fallback after a threshold.

**Radiation-specific considerations:** Since the flash itself is susceptible to SEUs, I'd add periodic scrubbing of the active firmware image—reading it back and checking CRCs, with the ability to repair corrupted sectors from a redundant copy if available. For the update process itself, I'd use error-correcting codes on the transmitted data and verify each sector after writing before moving to the next.

**Ground command safety:** The update command from ground should include multiple levels of confirmation (e.g., a two-command sequence with a time window) to prevent a single corrupted command from triggering an update.

**Possible follow-ups:**
- How would you handle the case where the bootloader itself is corrupted by radiation?
- What would you do if the system only has a single flash bank and you can't add a second one?

---

## Q5: How would you approach designing a test plan to verify that a space-deployed system can recover from a single-event functional interrupt (SEFI) that causes the main microcontroller to stop executing code, when you cannot inject actual radiation events during ground testing?

**Answer:** Since we can't create real radiation events in most ground test environments, the approach must be to simulate the *effects* of a SEFI through controlled fault injection. The goal is to verify that the recovery mechanisms work correctly when the processor stops executing, regardless of the root cause.

**Fault injection methods:**

- **Hardware breakpoint/watchdog trigger:** Use the debug interface (JTAG/SWD) to halt the processor at a specific point, simulating a hang. This tests whether the watchdog correctly detects the halt and resets the system.
- **Forced reset via test point:** Add a test header that allows an external signal to assert the reset line, simulating a SEFI-induced reset.
- **Clock manipulation:** Temporarily stop or glitch the processor clock to simulate a clock-related SEFI. This is more realistic for certain SEFI types.
- **Software fault injection:** For testing the recovery *software* (not the hardware watchdog), inject a deliberate jump to an invalid address or a software trap that simulates a corrupted program counter.

**Test scenarios to cover:**

1. **Processor halt during normal operation:** Verify the watchdog times out and resets the system, and that the system re-initializes correctly.
2. **Processor halt during critical operation:** For example, during a write to external memory or during a control loop update. Verify that the system recovers without corrupting critical data.
3. **Processor halt with watchdog disabled:** Some SEFIs might disable the watchdog as part of the failure. Test whether the external watchdog (if present) catches this.
4. **Recovery time measurement:** Measure the time from fault injection to full system recovery. This should be within the mission's allowable downtime.
5. **Post-recovery state verification:** After recovery, verify that the system returns to a known-good state—no corrupted data, correct configuration, proper re-initialization of peripherals.

**Test infrastructure:** I'd build a test harness that can:
- Inject faults at controlled times (e.g., synchronized with specific code execution points)
- Monitor the system's state (watchdog output, reset line, status LEDs, telemetry)
- Automatically log recovery times and any anomalies

**Limitations to acknowledge:** Ground testing can't fully replicate the random, unpredictable nature of radiation events. The test plan should therefore focus on verifying the *mechanisms* work, not on statistical coverage of all possible fault scenarios. I'd also recommend adding flight software telemetry that records watchdog resets and recovery events, so the system's behavior in orbit can be correlated with ground test results.

**Possible follow-ups:**
- How would you verify that the system recovers to a *safe* state, not just a running state, after a SEFI?
- What would you do if the recovery mechanism itself (e.g., the watchdog) is also affected by radiation?