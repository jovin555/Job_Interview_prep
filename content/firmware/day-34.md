# firmware — Day 34

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental issue is that a blocking flash operation in one thread can stall the entire system if it runs at a priority that prevents the sensor task from preempting it. My first step would be to examine whether the flash erase can be moved out of the lower-priority task's critical path entirely. Many flash controllers support asynchronous erase operations — you can issue the erase command and poll for completion, or better, use an interrupt to signal completion. That way, the lower-priority task can initiate the erase and then block on a semaphore or event, allowing the scheduler to run the 1 ms sensor task normally.

If the flash hardware only supports synchronous blocking erases, I'd look at whether the erase can be deferred or batched — for example, accumulating data in RAM and performing the erase during a period when the sensor task's data isn't critical, or splitting the erase into smaller sector operations that each block for a shorter duration. Another option is to use Zephyr's flash API with a dedicated low-priority thread that performs the erase, accepting that the sensor task will preempt it — but this only works if the flash peripheral itself doesn't require exclusive CPU ownership during the erase, which is often the case since the flash controller handles the erase autonomously once commanded.

The key design principle is to never let a long-blocking operation run in a thread that the real-time task can't preempt. I'd also verify the actual worst-case blocking time on the specific flash part — datasheet erase times are often conservative, and understanding the real timing helps make an informed trade-off. Finally, I'd instrument the system to measure worst-case scheduling latency during flash operations to confirm the sensor task meets its deadline under all conditions.

**Possible follow-ups:**
- How would you handle the case where the flash erase must happen atomically — for example, if a power loss mid-erase would corrupt the filesystem?
- Would your approach change if the sensor task's deadline were 500 µs instead of 1 ms?

---

## Q2: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** This pattern — correct at power-on, degrading over time — points to a thermal or power-supply issue rather than a firmware logic bug. My approach would be systematic. First, I'd confirm the symptom is reproducible and characterize it: does the drift correlate with board temperature, battery voltage, or time since power-on? I'd log ADC readings alongside battery voltage and, if possible, a temperature sensor reading to see what changes together.

On the hardware side, I'd suspect the switching regulator's output drifting as it heats up, or the battery voltage dropping below the regulator's dropout threshold, causing ripple or noise to couple into the ADC reference or analog front end. I'd check the ADC reference voltage — if it's derived from the battery or an unregulated rail, drift in the supply directly affects readings. I'd also look at the PCB layout: is the analog ground plane properly separated from the switching regulator's ground return? Thermal expansion or component drift in the regulator's feedback network could also cause the output voltage to shift.

On the firmware side, I'd verify that the ADC is configured for the correct reference and sampling time, and that the ADC's internal calibration isn't being invalidated by temperature changes. Some MCUs have temperature-dependent ADC gain errors that require periodic recalibration. I'd also check whether the firmware is doing anything that changes over time — for example, a DMA buffer that slowly fills and causes the ADC to sample at the wrong moment, or a power-management feature that changes clock settings after a timeout period.

The most productive next step would be to capture the ADC readings, supply voltage, and temperature simultaneously over the 30-minute window to identify which variable correlates with the degradation. That data would direct the fix — whether it's a hardware change (better decoupling, regulator adjustment, layout fix) or a firmware change (periodic ADC recalibration, different sampling strategy).

**Possible follow-ups:**
- What if the ADC readings are fine on a bench supply but drift on battery — how does that change your diagnosis?
- How would you determine whether the issue is the ADC reference or the input signal path?

---

## Q3: You're implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician. How would you approach this?

**Answer:** The core requirement is that invalid data must never be presented as valid — the system must either display a trustworthy value or clearly indicate that the reading is unavailable. I'd design the data validation as a multi-layer pipeline. At the lowest level, I'd check the communication integrity: CRC or checksum verification, frame format validation, and timing checks (e.g., the sensor responded within the expected window). Next, I'd apply plausibility checks: is the value within the physiological range for that parameter? Does it change at a rate consistent with the measurement? For example, a heart rate that jumps from 70 to 200 bpm in one sample might be valid, but a jump to 400 bpm is not.

The key design decision is what happens when a reading fails validation. The system should have a defined state machine: a single invalid reading might be retried or flagged as suspect, but the display should show the last valid reading with an indicator that it's stale, or show "no data" — never a fabricated value. After a configurable number of consecutive failures, the system should escalate to an alarm state, alerting the clinician that the sensor is unreliable. This is where the medical context matters: the risk of a false reading (showing a normal value when the patient is actually deteriorating) must be weighed against the risk of a false alarm (showing "no data" when the patient is fine). The validation thresholds and escalation logic should be documented and reviewed with clinical input.

I'd also implement a logging mechanism that records every invalid reading and the reason for rejection, which is essential for post-market surveillance and for debugging sensor issues in the field. Finally, I'd make the validation logic testable — unit tests with simulated valid and invalid data patterns, including boundary cases, to verify the state machine behaves correctly under all conditions.

**Possible follow-ups:**
- How would you decide between retrying the sensor read versus immediately flagging the reading as invalid?
- How would you handle a sensor that returns plausible but systematically biased readings (e.g., consistently 10% high)?

---

## Q4: You're reviewing a colleague's firmware code that implements a communication protocol using a single large interrupt service routine that handles both byte-level reception and complete message parsing. The ISR disables interrupts for the entire duration, which can be up to 300 µs for a long message. The system also has a 1 kHz control loop that must meet strict timing. How would you approach this situation?

**Answer:** This is a classic violation of the principle that ISRs should be as short as possible and never perform complex processing. A 300 µs interrupt-disabled window will almost certainly cause the 1 kHz control loop to miss its deadline, since 300 µs is nearly a third of the 1 ms period. The fix is to restructure the design so the ISR does the minimum necessary — typically just moving bytes from the peripheral into a buffer — and defers message parsing to a lower-priority context.

The standard pattern is a two-stage approach: the ISR handles byte-level reception (or DMA transfers complete blocks of bytes) and signals a thread via a semaphore or event flag. The thread then performs message parsing, validation, and dispatch. This way, the ISR's execution time is bounded by the time to copy a few bytes and set a flag — typically a few microseconds. If the protocol has strict timing requirements for responses, the parsing thread can be prioritized appropriately, but it still runs in thread context where it can be preempted by the control loop if needed.

I'd also consider whether DMA could offload the byte-level reception entirely — the DMA controller moves bytes into a ring buffer without CPU involvement, and the ISR only fires when a complete message is received or the buffer is full. This reduces interrupt overhead to near zero. The trade-off is added complexity in managing the DMA buffer and handling partial messages, but for a protocol with well-defined frame boundaries, it's often worth it.

In reviewing the colleague's code, I'd first quantify the actual impact — measure the worst-case interrupt latency and whether the control loop is actually missing deadlines. If the system is currently meeting timing, the fix might be lower priority, but the design is fragile and will break as features are added. I'd recommend the restructure as a correctness and maintainability improvement, not just a performance fix.

**Possible follow-ups:**
- How would you handle the case where the protocol requires a response within 500 µs of receiving a message?
- What if the MCU doesn't have a DMA controller — how would you structure the ISR to minimize interrupt-disabled time?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** The first thing I'd do is reframe the discussion away from "polling versus interrupts" as an either/or choice and toward the actual requirements: what are the protocol's timing constraints, what is the worst-case latency the system can tolerate, and what are the consequences of missing a deadline? The right answer depends on the specific protocol and system context, not on a general preference.

I'd ask the team to quantify the requirements. For example: what is the maximum time between a message arriving and the system needing to respond? What is the message rate and size? What else is the CPU doing during that time? If the protocol has a tight response deadline (say, 100 µs) and the CPU is busy with other tasks, polling might not be feasible — the main loop could be in a long computation when the message arrives. Conversely, if the deadline is loose (say, 10 ms) and the CPU is mostly idle, polling could be simpler and perfectly adequate.

I'd also challenge the assumption that polling is inherently more predictable. Polling introduces jitter because the response time depends on where the main loop is when the event occurs. Interrupts, if properly designed with short ISRs, can actually provide more deterministic response times. The real predictability concern with interrupts is priority inversion and ISR overrun, which are design issues that can be addressed.

My recommendation would be to make the decision based on measured or estimated worst-case timing, not intuition. I'd suggest the team prototype both approaches or at least do a timing analysis for each, then evaluate against the requirements. If both approaches meet the requirements, I'd lean toward the simpler one for maintainability, but I'd document the decision and the reasoning. If there's genuine uncertainty, I'd suggest a hybrid: use interrupts for the critical event detection (e.g., message arrival) but poll for less time-sensitive operations. The key is that the decision should be data-driven and documented, not based on which engineer argues more persuasively.

**Possible follow-ups:**
- How would you handle the situation where one engineer refuses to accept the data-driven decision and continues to advocate for their preferred approach?
- What metrics would you collect to validate that the chosen approach meets the timing requirements in production?