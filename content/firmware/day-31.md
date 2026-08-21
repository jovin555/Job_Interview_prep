# firmware — Day 31

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental issue is that a blocking flash operation in any task will stall the scheduler if it runs at a priority that prevents the sensor task from preempting it. The first thing I'd examine is whether the flash erase truly must block the calling thread, or whether the flash controller supports asynchronous operations. Many modern MCUs allow you to issue an erase command and poll a status register or receive an interrupt when complete, rather than stalling the CPU. If the flash controller supports this, I'd restructure the lower-priority task to issue the erase command, then yield or block on a semaphore that gets signaled from the flash-complete interrupt. That way, the sensor task continues to run at its 1 ms cadence while the erase proceeds in the background.

If the flash controller genuinely blocks the CPU (some older or simpler parts do), then the answer changes. I'd look at whether the erase can be deferred to a time when the sensor task isn't actively sampling — for example, during a known idle window. If that's not possible, I'd consider whether the sensor data can be buffered during the erase window and processed afterward, but that only works if the buffer can absorb 100 ms of data without overflow. For a 1 kHz sampling rate, that's 100 samples, which is usually feasible with a small ring buffer. The key is to make the trade-off explicit: either you accept a brief gap in processing (but not in acquisition, if DMA is used) or you find a way to make the erase non-blocking.

I'd also question whether the flash erase needs to happen at that priority level at all. If the lower-priority task is doing housekeeping, I'd consider moving the erase to an even lower-priority idle task, or breaking the erase into smaller chunks if the flash supports partial-page or sector-level operations with shorter block times. Finally, I'd verify the actual worst-case blocking time on the specific hardware — datasheet values are often optimistic, and the real number depends on the flash state, temperature, and whether a write buffer needs to be flushed first.

**Possible follow-ups:**
- How would you handle the case where the sensor task must not miss a single sample, even during the erase window?
- What Zephyr kernel primitives would you use to coordinate the flash operation with the sensor task, and how would you configure their priorities?

---

## Q2: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** This pattern — correct at power-on, then degrading over time — points to a thermal or power-supply issue rather than a firmware logic bug. The first thing I'd do is check whether the ADC reference voltage is stable. If the reference is derived from the battery rail or from a regulator that drifts with temperature or load, the readings will shift even if the input signal is constant. I'd measure the reference voltage at the ADC pins with an oscilloscope or precision multimeter at power-on and again after 30 minutes, while also monitoring the switching regulator's output for ripple or droop.

Next, I'd look at the ADC's sampling time and input impedance. If the source impedance is high and the sampling capacitor isn't fully charged, the readings can be sensitive to temperature-dependent leakage currents in the input path. Over time, as the board warms up, leakage in protection diodes, capacitors, or the PCB itself can increase and pull the input voltage. I'd check whether the input path has a proper buffer amplifier or whether the sampling time is configured long enough for the worst-case source impedance.

I'd also suspect the switching regulator itself. As the battery discharges, the regulator's duty cycle changes, and if the inductor or output capacitor is marginal, ripple can increase. That ripple can couple into the ADC reference or the analog input path. I'd look at the ripple on the analog supply rail with a scope, especially under load, and check whether the ADC's power supply pin has adequate decoupling. A common fix is to add a low-dropout regulator (LDO) for the analog section, separate from the switching regulator, or to add a ferrite bead and additional filtering between the switching supply and the analog rail.

Finally, I'd check for firmware-related causes: is the ADC being sampled at the same point in the switching regulator's PWM cycle? If the sampling coincides with the switch transition, the reading will capture the ripple peak. I'd consider synchronizing the ADC conversion to a quiet period in the switching cycle, or averaging multiple samples to reject the ripple. I'd also verify that the ADC's internal temperature sensor (if present) isn't being used as a reference, and that the firmware isn't inadvertently changing the ADC configuration over time — for example, a register being corrupted by a memory overwrite that only manifests after enough heap fragmentation.

**Possible follow-ups:**
- How would you distinguish between a reference drift and a signal-path drift in your measurements?
- What specific measurements would you take to confirm or rule out the switching regulator as the root cause?

---

## Q3: You're reviewing a colleague's firmware code that implements a communication protocol using a single large interrupt service routine that handles both byte-level reception and complete message parsing. The ISR disables interrupts for the entire duration, which can be up to 300 µs for a long message. The system also has a 1 kHz control loop that must meet strict timing. How would you approach this situation?

**Answer:** This is a classic interrupt-latency problem. The ISR is doing too much work — it's combining the time-critical byte reception with the non-time-critical message parsing, and in doing so it's starving the control loop. The first principle I'd apply is that an ISR should do the minimum work necessary to service the hardware and defer everything else. For a UART, that means copying received bytes into a ring buffer and clearing the interrupt flag. Message parsing — checking framing, validating checksums, extracting fields — should happen in a lower-priority task or in the main loop.

The 300 µs of interrupt-disabled time is almost certainly unacceptable for a 1 kHz control loop, which has a 1 ms period. Even if the control loop is interrupt-driven, a 300 µs stall means the loop can't meet its timing budget. I'd restructure the code so the UART ISR only handles byte reception — copying into a DMA buffer or a ring buffer — and then signals a task (via a semaphore or event flag) that a complete message may be available. The parsing task runs at a priority below the control loop, so it can't interfere with the timing-critical work.

I'd also consider whether DMA could offload the byte reception entirely. If the UART supports DMA, the peripheral can receive a full message into a buffer without CPU intervention, and the ISR only fires when the transfer completes. That reduces the ISR work to a single buffer handoff. The trade-off is that DMA requires careful buffer management — you need to know the maximum message length and handle partial transfers — but it's often the cleanest solution for this kind of problem.

Beyond the restructuring, I'd also question the 300 µs number itself. Even parsing a moderately complex message shouldn't take that long on a modern MCU. If it does, the parsing code may be inefficient — for example, using dynamic memory allocation or doing blocking I/O inside the parser. I'd profile the parsing code to see where the time goes and optimize the hot paths. But the fundamental fix is architectural: separate the interrupt context from the processing context, and ensure the control loop always has priority over protocol handling.

**Possible follow-ups:**
- How would you handle the case where the UART receive buffer overflows while the parsing task is busy?
- What Zephyr RTOS primitives would you use to signal the parsing task from the ISR, and what constraints apply to ISR-safe calls?

---

## Q4: You're implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician. How would you approach this?

**Answer:** The core requirement is that the system must fail safe — it's better to show no reading or an explicit error than to show a plausible but incorrect value. The first layer of defense is at the sensor interface level. I'd validate every read: check the CRC or checksum, verify the data length, and confirm the sensor's status register indicates valid data. If any of these checks fail, I'd discard the sample and increment an error counter rather than passing the data up the stack.

The second layer is plausibility checking at the application level. Even if the sensor reports valid data, the value might be physiologically impossible — for example, a heart rate of 500 bpm or a temperature of 45°C. I'd define acceptable ranges based on the clinical context and the sensor's specifications, and reject values outside those ranges. I'd also look at rate-of-change: a sudden jump from 70 to 140 bpm in one sample might be real, but a jump from 70 to 400 is almost certainly an artifact. The key is to define these checks in collaboration with clinical experts, because the thresholds depend on the specific parameter and the patient population.

The third layer is how the system responds to invalid data. For a single bad sample, I'd typically hold the last valid reading and flag the data as stale. For repeated failures, I'd escalate: after N consecutive invalid reads, I'd transition the device to a degraded mode that clearly indicates the sensor is unreliable, rather than continuing to display potentially incorrect values. The clinician must never see a value that looks valid but isn't — so the display should show "sensor error" or a similar explicit message, not the last known value without qualification.

I'd also design the error handling to be transparent in the logs. Every invalid read should be recorded with a reason code (CRC failure, out of range, rate-of-change violation) so that during post-event analysis, the clinical team can understand what happened. This is especially important for a medical device, where the data may be used for treatment decisions. Finally, I'd make sure the invalid-data handling is tested — not just with simulated bad data, but with fault injection at the driver level to verify that the system behaves correctly under realistic failure modes.

**Possible follow-ups:**
- How would you decide between holding the last valid reading versus showing an error state after a single invalid sample?
- How would you handle the case where the sensor recovers after a period of invalid data — would you require a re-qualification period before displaying readings again?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** The first thing I'd do is reframe the discussion away from "which is better" and toward "what are the specific requirements and constraints of this protocol?" Both patterns are valid tools, and the right choice depends on factors like the number of states, the complexity of transitions, how often the protocol is likely to change, and the team's familiarity with each approach.

I'd start by asking the team to map out the protocol's structure. If the protocol has a small number of states (say, fewer than 10) with relatively simple transitions, a hand-coded state machine is often more readable and easier to trace during debugging. If the protocol has dozens of states with many conditional transitions, a table-driven approach can be more maintainable because the transition logic is data rather than code — you can add a new state or transition by editing a table entry instead of modifying control flow.

I'd also consider the testing and verification requirements. For a medical device, the protocol logic will need to be verified against the specification. A table-driven approach can make it easier to enumerate all transitions and verify completeness — you can write a test that walks the table and checks that every state/event combination is handled. A hand-coded state machine can be harder to verify exhaustively, especially if transitions are scattered across multiple functions.

Rather than making the decision purely on technical merits, I'd also consider the team's long-term maintenance burden. If the protocol is likely to evolve — new message types, new states, new error conditions — the table-driven approach may be more resilient to change. But if the protocol is stable and the team is more comfortable with explicit state machines, the readability benefit may outweigh the extensibility advantage.

I'd propose a pragmatic path: have the team prototype a small but representative portion of the protocol in both styles, then evaluate them against criteria we agree on upfront — readability, testability, ease of adding a new state, and debugging experience. This turns a theoretical debate into an evidence-based decision. I'd also make sure the decision is documented, including the rationale, so that future maintainers understand why the chosen approach was selected. If the team still can't agree, I'd make the call based on the criteria, but I'd make it clear that the goal is a maintainable, verifiable implementation — not a personal preference.

**Possible follow-ups:**
- What specific criteria would you use to evaluate the two prototypes, and how would you weight them?
- How would you handle the situation where one engineer strongly prefers their approach and resists the decision even after the evaluation?