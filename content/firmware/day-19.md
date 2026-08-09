# firmware — Day 19

## Q1: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core principle here is that the firmware must distinguish between "no data available" and "invalid data," and both must be handled without ever presenting a fabricated value to the clinician. I'd structure this in layers. First, at the driver level, I'd validate every read: check the CRC or checksum, verify the data is within the sensor's specified operating range, and flag any transaction-level errors (e.g., NACK, timeout). If a read fails validation, I would not propagate the raw value upward. Instead, I'd mark that sample as invalid and increment a consecutive-failure counter.

At the application layer, I'd implement a data-quality state machine. For a single invalid sample, the device should continue displaying the last known-good value but indicate a "data stale" or "sensor communication error" condition — not silently keep showing old data as if it were current. If consecutive failures exceed a threshold (e.g., 3–5 samples), the device should transition to a degraded mode: clearly display an alarm or "sensor fault" message, stop using that parameter in any clinical decision logic, and log the event. The key is that the clinician must never see a value that wasn't actually measured. I'd also ensure that any derived calculations (e.g., trends, averages) exclude invalid samples and that the display timestamp reflects when the last valid sample was actually acquired.

For the validation logic itself, I'd make it configurable per sensor type — some sensors have tighter tolerances than others — and I'd ensure the thresholds are documented and traceable to the sensor datasheet or clinical requirements. Finally, I'd add a self-test or diagnostic mode that can inject known-good and known-bad data to verify the validation and degradation logic works correctly during development and manufacturing test.

**Possible follow-ups:**
- How would you handle a sensor that returns valid-looking but clinically implausible data (e.g., a heart rate of 400 bpm) that passes the sensor's own CRC check?
- What would you do if the sensor recovers after a fault — how would you decide when to resume normal operation and clear the alarm?

---

## Q2: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** This is a classic priority-inversion and blocking problem. The first thing I'd recognize is that a 100 ms blocking operation in a lower-priority task will absolutely starve a 1 ms sensor task if they share a CPU core, regardless of priority — the lower-priority task simply won't be preempted while it's blocked inside the flash driver. So the solution has to eliminate the blocking, not just adjust priorities.

The standard approach is to move the flash erase operation out of the task context entirely. On most modern MCUs, the flash controller can perform an erase in the background while the CPU continues executing from RAM. I'd structure this as: the lower-priority task submits the erase request to a flash driver that initiates the erase and returns immediately, then the task blocks on a semaphore or event that the flash-complete interrupt signals. The sensor task continues running at 1 ms without interruption. If the MCU doesn't support background flash erase, the alternative is to perform the erase in small chunks (e.g., page-by-page) with the task yielding between chunks, but that's less ideal because it extends the total erase time and still introduces some scheduling jitter.

I'd also check whether the flash driver in Zephyr already supports asynchronous operations — the Zephyr flash API has an asynchronous mode with a callback or pollable status. If so, I'd use that rather than writing a custom driver. Additionally, I'd consider whether the sensor data during the erase window can be buffered — if the sensor task can queue samples in RAM during the erase, the system can tolerate a brief interruption, but that's a fallback, not the primary design. Finally, I'd verify the interrupt latency budget: the flash-complete interrupt must be serviced promptly, and I'd ensure no other ISR disables interrupts for longer than the sensor task's deadline allows.

**Possible follow-ups:**
- What if the MCU's flash controller cannot erase in the background — how would you redesign the approach?
- How would you verify that the sensor task never misses its 1 ms deadline during the erase operation?

---

## Q3: How would you approach implementing a firmware module that must handle a burst of data from a sensor at high speed (e.g., 1000 samples at 10 kHz) while the rest of the system is running normal operations, without dropping any samples?

**Answer:** The key constraint here is that 1000 samples at 10 kHz means the entire burst lasts 100 ms, and samples arrive every 100 µs. The firmware must be able to consume each sample within that 100 µs window, or buffer them for later processing. I'd start by analyzing the data path: where does the data come from (SPI, I2C, ADC, DMA), and what processing is required before the sample is considered "captured"?

For a high-rate burst like this, I would almost certainly use DMA to move samples from the peripheral into a RAM buffer, rather than interrupt-driven or polling reads. At 10 kHz, an interrupt per sample would consume significant CPU time and risk missing samples if any other interrupt has higher priority or if the ISR takes too long. With DMA, the peripheral writes directly to a double-buffered region in RAM, and the CPU is only interrupted when a buffer fills (e.g., every 100 samples at 10 kHz, which is every 10 ms). That gives the CPU a comfortable window to process the filled buffer while DMA fills the other.

I'd design the buffer as a ping-pong or circular DMA buffer. The ISR that fires on buffer-full should do minimal work — just swap the active buffer pointer and signal a task (via a semaphore or event) that a buffer is ready for processing. The actual processing (e.g., scaling, filtering, storing to flash or sending over a link) happens in a task context. I'd also verify that the total RAM for the burst (1000 samples × bytes per sample) fits within the available memory, and if not, I'd process in chunks as the burst arrives rather than trying to store the entire burst before processing.

One subtlety: if the sensor is on SPI, I'd need to ensure the SPI clock is fast enough to transfer each sample within the 100 µs period, including any inter-sample gaps. I'd calculate the worst-case transfer time and confirm there's margin. I'd also consider whether the sensor requires a "start burst" command and whether the firmware needs to respond within a tight window to initiate the burst — that's often the trickiest part because it's a one-shot timing requirement.

**Possible follow-ups:**
- How would you decide between DMA and interrupt-driven capture for this scenario?
- What would you do if the processing of a filled buffer occasionally takes longer than the time to fill the next buffer?

---

## Q4: You're reviewing a colleague's firmware code that implements a state machine for a medical device's operational modes (idle, calibration, active monitoring, error). The state machine is implemented as a single switch-case inside a 200-line function, with state transitions scattered across multiple modules via global state variables. How would you approach refactoring this for maintainability and safety?

**Answer:** I'd approach this refactoring with the goal of making the state machine's behavior explicit, centralized, and auditable — which is critical for a medical device where you need to demonstrate that every possible transition is safe and intentional. The first step would be to document the current behavior: I'd map out all states, all events that can trigger transitions, and all actions taken on entry, exit, and during each state. This documentation becomes the specification against which the refactored code is verified.

For the refactored design, I'd use a table-driven state machine rather than a nested switch-case. The table would list, for each state and event, the next state and the action function to call. This makes the entire transition matrix visible in one place, which is much easier to review and verify against the requirements. Each state's behavior would be encapsulated in its own module or set of functions — entry, exit, and event-handling functions — rather than having logic scattered across the codebase. I'd also eliminate the global state variables; the state machine would own its current state, and any module that needs to query or influence the state would do so through a defined API (e.g., `sm_get_state()`, `sm_post_event()`).

For safety, I'd add assertions or validation checks that reject invalid transitions — if an event arrives that isn't valid in the current state, the state machine should log it and either ignore it or transition to an error state, depending on the severity. I'd also ensure that the error state is handled explicitly: what happens when the device enters error mode, how it recovers, and whether any transitions out of error are allowed. Finally, I'd write unit tests that exercise every state-event pair in the table, including invalid transitions, to verify the refactored code matches the documented behavior exactly.

**Possible follow-ups:**
- How would you handle state-specific data — for example, calibration parameters that only exist in the calibration state?
- What would you do if the existing code has undocumented transitions that appear to be bugs but are relied upon by other modules?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** I'd start by reframing the debate away from "polling vs. interrupts" as a matter of preference and toward the specific requirements of the protocol and the system. The right answer depends on the data rate, the timing requirements, the CPU load, and the consequences of missing an event. So the first step is to gather the facts: what's the maximum message rate, what's the worst-case latency the protocol can tolerate, how much CPU time is available for communication handling, and are there other time-critical tasks running concurrently?

Once we have those numbers, I'd ask each engineer to articulate their concern in terms of the requirements. The polling advocate is right that polling is often simpler to reason about — there's no reentrancy, no ISR-context issues, and the timing is deterministic. But polling only works if the CPU can afford to check the peripheral frequently enough to meet the latency requirement, and if the polling loop doesn't starve other tasks. The interrupt advocate is right that interrupts provide responsiveness, but they introduce complexity: shared data between ISR and task contexts, priority inversion, and the need to carefully budget interrupt latency.

I'd also consider a third option that often resolves the tension: DMA with interrupt-on-completion, or a hybrid where the peripheral's status is polled but the actual data transfer is handled by DMA. This gives the responsiveness of interrupts without the per-byte CPU overhead. If the protocol is truly low-rate (e.g., a few messages per second), polling might be perfectly adequate and simpler. If it's high-rate or has strict latency bounds, interrupts or DMA are likely necessary.

To make the decision concrete, I'd ask the team to prototype both approaches — or at least do a back-of-the-envelope calculation of worst-case CPU utilization and latency for each — and then evaluate against the requirements. I'd also emphasize that the decision should be documented with the rationale, so future maintainers understand why the choice was made. If the disagreement persists, I'd make the call based on the data, but I'd ensure both engineers feel their concerns were heard and addressed in the final design.

**Possible follow-ups:**
- How would you handle the situation where the two engineers continue to disagree even after seeing the data?
- What if the requirements change later (e.g., the protocol's data rate increases) — how would you ensure the chosen approach can adapt?