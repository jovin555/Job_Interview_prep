# firmware — Day 45

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** This is a classic priority-inversion-plus-blocking problem. The first principle is that no task should ever block for 100 ms in a system with a 1 ms deadline — that's not a scheduling problem, it's an architecture problem. I'd start by questioning the assumption that the flash erase must block the calling task at all.

The standard approach is to move flash operations out of the blocking path entirely. Most modern MCU flash controllers have a command-completion interrupt or status flag. I'd structure the flash driver as a state machine: issue the erase command, then return control to the scheduler. The completion interrupt (or a polling loop in a very low-priority task) handles the "erase done" transition. The lower-priority task that requested the erase would block on a semaphore or wait on a completion callback, but critically, it would block *itself* — not the CPU — so the 1 ms sensor task continues to run uninterrupted.

If the flash controller truly blocks the CPU (some older parts stall the core during erase), then the answer changes: I'd need to check whether the sensor task can tolerate the worst-case latency, and if not, I'd look at alternatives — buffering sensor data in a way that tolerates the gap, using a dual-bank flash arrangement where reads come from one bank while erasing the other, or moving the sensor task's timing-critical portion into an ISR or a higher-priority context that runs before the flash operation stalls the core. I'd also verify the actual worst-case erase time on the specific silicon rather than trusting the datasheet's typical number.

The deeper point is that the scheduler configuration is secondary. The right answer is to design the flash subsystem so it doesn't need 100 ms of uninterrupted CPU time in the first place.

**Possible follow-ups:**
- How would you handle the case where the flash erase must be atomic — for example, if a power loss mid-erase could corrupt the filesystem?
- What Zephyr-specific mechanisms (e.g., work queues, threads with priority ceilings) would you use to implement the non-blocking flash driver?

---

## Q2: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** I'd treat this as a thermal or power-integrity problem first, not a firmware problem, because the time constant (30 minutes) strongly suggests something heating up. The switching regulator's components — inductor, MOSFETs, sense resistors — drift with temperature. If the regulator's output voltage or ripple characteristics change as it warms, the ADC's reference voltage or the sensor's supply could be drifting.

My first step would be to instrument the system: measure the actual regulator output voltage, the ADC reference voltage, and the sensor supply at the point of measurement, both at power-on and after the drift appears. I'd also check the board temperature. If the supply rails are stable, then I'd look at the ADC itself — is the reference drifting, or is the input path (e.g., an op-amp or filter network) the culprit?

On the firmware side, I'd check whether the ADC is configured for continuous sampling or single-shot, and whether the sampling time is adequate. A common issue is that as the battery discharges (even from 100% to 70%), the regulator's input voltage drops, and if the regulator is near dropout, its ripple increases. That would explain why the issue appears after time — not because of thermal drift in the ADC, but because the battery voltage has sagged under load.

I'd also look at the firmware's ADC calibration routine. Many MCUs have an internal calibration that should be re-run periodically, especially if the temperature changes. If the device is warming up internally, the ADC's gain error can drift. Re-running calibration at intervals, or at least checking whether the calibration registers have drifted, would be a diagnostic step.

Finally, I'd check the grounding and layout — if the ADC's analog ground and the switching regulator's ground share a return path, the noise will scale with load current, which changes over time as the battery sags. But that's a hardware fix; from a firmware perspective, I'd focus on what I can measure and log to confirm or rule out each hypothesis.

**Possible follow-ups:**
- How would you distinguish between the ADC reference drifting versus the input signal itself drifting?
- What would you log in firmware to help diagnose this in the field, given limited storage?

---

## Q3: You're implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician. How would you approach this?

**Answer:** The core requirement is that the system must fail safe — it's better to show "no data" or an error state than to show a plausible-but-wrong value. I'd design the data path with multiple layers of validation.

First, at the protocol level: every sensor read should include a CRC or checksum verification. If the CRC fails, that sample is discarded — not corrected, not retried indefinitely, just discarded and counted. I'd track consecutive failures and, if they exceed a threshold, transition the sensor channel to a "degraded" state rather than continuing to attempt reads in a tight loop.

Second, at the signal level: each parameter should have a plausibility range based on physiology, not just the sensor's raw range. For example, a heart rate of 450 bpm or a temperature of 20°C is physiologically impossible even if the sensor reports it. I'd implement rate-of-change limits as well — a value that jumps by an implausible amount between consecutive samples is suspect even if each individual value is in range.

Third, at the display level: the clinician should never see a single validated sample as ground truth. I'd require a minimum number of consecutive valid samples before updating the displayed value, and I'd display a confidence indicator or "signal quality" metric. If the sensor is intermittent, the display should show the last known good value with a timestamp and a "data stale" warning, rather than a fresh-looking value that might be wrong.

Finally, I'd think about what happens on the boundary: if the sensor recovers, how does the system transition back to normal operation? I'd require a stabilization period — several consecutive valid samples — before clearing the degraded state, to avoid flickering between normal and error states.

The key design principle is that the firmware's job is not just to read the sensor, but to decide what information is trustworthy enough to present. That decision logic should be explicit, testable, and documented, because it's safety-critical.

**Possible follow-ups:**
- How would you handle the case where the sensor returns values that pass CRC and plausibility checks but are still wrong (e.g., a sensor that's drifted out of calibration)?
- How would you test this module to prove it never displays a false reading?

---

## Q4: You're reviewing a colleague's firmware code that implements a communication protocol using a single large interrupt service routine that handles both byte-level reception and complete message parsing. The ISR disables interrupts for the entire duration, which can be up to 300 µs for a long message. The system also has a 1 kHz control loop that must meet strict timing. How would you approach this situation?

**Answer:** This is a textbook case of doing too much work in interrupt context. A 300 µs interrupt disable window on a system with a 1 kHz control loop is catastrophic — the control loop has a 1 ms period, so a 300 µs stall is 30% of the entire budget, and that's before considering any other interrupts.

The fundamental principle is that ISRs should be as short as possible — ideally, they should only move data between hardware and a buffer, and defer all processing to thread context. I'd restructure this in two stages.

First, the byte-level reception should stay in the ISR but do the minimum: read the byte from the UART peripheral, write it to a DMA buffer or a ring buffer, and clear the interrupt flag. That's maybe 10-20 instructions. If the UART supports DMA, even better — the DMA controller handles byte reception entirely, and the ISR only fires when a complete message (or a timeout) occurs.

Second, message parsing moves to a dedicated task or work queue. The ISR signals that a message is available (via a semaphore or a flag), and the parsing task runs at a priority below the control loop. Parsing a 300 µs message in thread context is fine — it might delay a lower-priority task, but it won't threaten the control loop's deadline.

I'd also check whether the colleague's approach of disabling interrupts for the entire ISR is even necessary. Most modern MCUs support nested interrupts with priority levels, so the ISR could enable higher-priority interrupts (like the control loop timer) while it's running. But that's a band-aid — the real fix is moving the work out of the ISR.

In terms of guiding the colleague, I'd frame it around the system's timing requirements: the control loop's 1 kHz deadline is a hard constraint, and the communication protocol's latency requirement is likely much softer. The ISR design should respect that hierarchy. I'd also point out that debugging a 300 µs ISR is much harder than debugging a parsing task, because you can't easily set breakpoints or log from interrupt context.

**Possible follow-ups:**
- How would you handle the case where the communication protocol requires a response within a tight deadline (e.g., an ACK within 500 µs)?
- What tools or techniques would you use to measure the actual worst-case ISR latency in the current implementation?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** I'd start by reframing the question: this isn't about which pattern is "better" in the abstract, but about which is better for *this specific protocol* and *this team's ability to maintain it over the product's lifetime*. Both patterns are valid; the decision should be driven by the protocol's characteristics and the team's constraints.

First, I'd ask the engineers to map out the protocol's actual complexity. How many states are there? How many transitions? Are the transitions mostly linear (A→B→C→D) or are there many conditional branches, loops, and exception paths? A protocol with 5 states and 10 transitions is fine as a hand-coded state machine. A protocol with 30 states and 200 transitions — especially one that's likely to grow — will become unmaintainable as a switch-case, and a table-driven approach will win.

Second, I'd consider the failure modes. In a medical device, the protocol's behavior under unexpected inputs is safety-critical. A hand-coded state machine makes it easy to add explicit error handling per state, but it's also easy to miss a transition. A table-driven approach makes it easy to verify completeness — you can write a test that walks every transition in the table — but it can obscure the logic if the table is data-driven and hard to trace.

Third, I'd think about the team. If the protocol will be maintained by engineers who weren't involved in the original design, a table-driven approach with a clear format and documentation might be easier to extend without understanding the full context. But if the team is small and the protocol is stable, a state machine might be simpler to reason about.

Rather than deciding for them, I'd structure a decision process: have each engineer prototype a small but representative slice of the protocol using their preferred approach, then evaluate both against concrete criteria — readability (can a new engineer trace a specific scenario?), testability (how easy is it to write exhaustive transition tests?), and extensibility (how hard is it to add a new state or transition?). I'd also ask them to consider the regulatory context: in a medical device, the protocol logic will need to be verified and validated, so whichever approach makes that verification easier — through traceability and test coverage — should win.

If the disagreement persists, I'd make a call based on the protocol's expected evolution. If the protocol is likely to change frequently (e.g., new features, new sensor types), I'd lean toward the table-driven approach because it centralizes the transition logic. If the protocol is stable and the priority is debuggability in the field, I'd lean toward the state machine. But the key is that the decision is made on evidence, not preference.

**Possible follow-ups:**
- How would you ensure that whichever approach is chosen, the protocol logic is testable in a way that satisfies medical device regulatory requirements?
- What if one engineer has significantly more experience with their preferred pattern — how would you weigh that against the technical merits?