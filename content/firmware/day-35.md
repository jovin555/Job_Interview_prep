# firmware — Day 35

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental issue is that a blocking flash operation in any task will stall the scheduler if it disables interrupts or occupies the CPU, regardless of priority. My first step would be to check whether the flash controller supports asynchronous or interrupt-driven erase operations — many modern MCU flash peripherals can signal completion via interrupt, allowing the task to sleep while the erase proceeds in the background. If the hardware supports this, I'd restructure the lower-priority task to initiate the erase, then block on a semaphore or event that the flash-complete ISR signals. The high-priority sensor task would never be blocked because the CPU is free during the erase.

If the flash controller only supports blocking operations, I'd look at whether the erase can be broken into smaller page or sector operations with yields between them, trading total erase time for scheduler responsiveness. Another option is to use Zephyr's flash driver with a dedicated thread that performs the erase at a priority below the sensor task — but this only works if the erase operation itself doesn't disable interrupts globally. I'd also verify the actual worst-case blocking time on the specific hardware, since datasheet values often assume ideal conditions. Finally, I'd consider whether the sensor data could be buffered during the erase window — if the sensor task can tolerate a short burst of missed samples by reading from a FIFO afterward, that changes the analysis entirely. The key is to measure the real blocking behavior, understand the hardware capabilities, and then design around the constraint rather than assuming priority scheduling alone will solve it.

**Possible follow-ups:**
- How would you verify that the flash erase actually releases the CPU, rather than assuming it does from the datasheet?
- What if the sensor data absolutely cannot be missed for even one sample — how does that change your approach?

---

## Q2: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** This pattern — correct at power-on, degrading over time — points me toward thermal effects, reference drift, or a power supply issue that develops as the system reaches thermal equilibrium. I'd start by ruling out the simplest causes: is the ADC reference voltage stable? Many internal references drift significantly with temperature, and after 30 minutes the board may have warmed up by 10–20°C. I'd log the raw ADC codes alongside the die temperature sensor (if available) and the battery voltage to see if the noise correlates with any of these.

Next, I'd look at the switching regulator. As the battery discharges, the regulator's input voltage drops, and its ripple characteristics can change. I'd put a scope on the ADC's supply pin and reference pin to check for increased ripple or droop over time. A common issue is that the regulator's loop compensation was tuned for a specific load range, and as the system's current draw changes with temperature (e.g., a display backlight or radio drawing more current), the regulator becomes less stable. I'd also check whether the ADC's sampling time is marginal — if the input source impedance is high and the sampling capacitor doesn't fully charge, small changes in temperature can push it over the edge.

I'd also consider ground bounce or layout issues that only manifest when certain peripherals are active. The fact that it's battery-powered is significant — battery impedance is higher than a bench supply, so any transient current draw creates larger voltage dips. I'd compare the noise signature on battery versus bench supply to isolate whether it's a supply impedance issue or something else. Finally, I'd check for firmware causes: is the ADC being sampled at the same rate, or does the sampling interval drift? Is there a DMA configuration that could be corrupted over time? I'd add diagnostic logging of raw values, timestamps, and system state to correlate the onset of noise with any other system events.

**Possible follow-ups:**
- What specific measurements would you take with an oscilloscope to distinguish between reference drift and supply noise?
- How would you determine whether the issue is thermal or related to battery discharge state?

---

## Q3: You're implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician. How would you approach this?

**Answer:** The core principle is that in a medical monitoring context, the system must fail safe — it's better to show no reading or an explicit error than to display a plausible but incorrect value. I'd structure the handling in layers. First, at the protocol level, I'd validate every sensor frame: check the CRC, verify the frame length, and confirm the sensor address. Any frame that fails these checks is discarded entirely — never partially parsed.

Second, at the data level, I'd apply plausibility checks based on the physiological range of the parameter being measured. For example, if the sensor reports a heart rate of 400 bpm, that's physiologically impossible regardless of what the sensor claims. I'd define both hard limits (values outside a range that can never be valid) and rate-of-change limits (a value that jumps 50 units in one sample when the maximum physiological rate of change is 5 units per sample). Values that fail these checks are flagged as invalid.

Third, I'd implement a validation policy that determines how many consecutive invalid readings are required before the system changes state. A single bad sample might be treated as "suspect" — displayed with a quality indicator or held for confirmation — while multiple consecutive failures trigger an explicit "sensor error" state. The key design decision is the hysteresis: too aggressive and you display stale data; too lenient and you risk showing a false reading. I'd also distinguish between "no data" (sensor silent) and "invalid data" (sensor responding with garbage) — they have different clinical implications.

Finally, I'd ensure the invalid-data handling is itself tested: the firmware should have a well-defined behavior for every failure mode, and that behavior should be documented in the risk analysis. The display logic should never assume the sensor is correct — it should always render the validated, filtered value with an appropriate confidence indicator.

**Possible follow-ups:**
- How would you decide between showing the last valid reading versus showing "no data" when a sensor starts returning invalid values?
- How would you handle a sensor that returns valid-looking but systematically wrong data (e.g., a calibration drift)?

---

## Q4: You're reviewing a colleague's firmware code that implements a communication protocol using a single large interrupt service routine that handles both byte-level reception and complete message parsing. The ISR disables interrupts for the entire duration, which can be up to 300 µs for a long message. The system also has a 1 kHz control loop that must meet strict timing. How would you approach this situation?

**Answer:** This is a classic violation of the principle that ISRs should be as short as possible and never perform protocol-level processing. A 300 µs interrupt-disabled window is almost certainly going to cause jitter or missed deadlines in a 1 kHz control loop — that's 30% of the loop period spent with interrupts off. I'd approach this as a design review rather than just a code fix.

The first point I'd make is that the ISR should do the minimum necessary: copy received bytes into a DMA buffer or a ring buffer, set a flag, and return. Message parsing — frame synchronization, CRC checking, extracting fields — belongs in a thread or task context where it can be preempted and where blocking operations are acceptable. The byte-level reception might not even need an ISR at all if the UART supports DMA; the DMA controller can move bytes into memory without CPU involvement, and the ISR only fires when a complete message is received.

I'd also question the 300 µs figure itself. If parsing a message takes that long, the parsing algorithm may be inefficient — perhaps it's doing per-byte processing that could be done on complete frames, or it's using blocking calls inside the ISR. I'd ask the colleague to profile where the time is actually spent. If the protocol is complex, a state machine parser that processes one byte at a time should take microseconds per byte, not hundreds of microseconds per message.

The broader design question is about interrupt latency budgeting. I'd work with the team to establish a budget: the control loop needs to run every 1 ms with bounded jitter, so the maximum acceptable interrupt-disabled time might be, say, 10–20 µs. Any ISR that exceeds this needs to be restructured. I'd also check whether the control loop itself is interrupt-driven or timer-driven, and whether it has priority over the communication ISR. If the control loop is a timer ISR at higher priority, the communication ISR's long execution would still delay it — priority doesn't help if the lower-priority ISR has already disabled interrupts.

Finally, I'd suggest adding instrumentation: measure the actual worst-case interrupt-disabled time in the system and verify it against the budget. This turns the discussion from opinion into data.

**Possible follow-ups:**
- How would you convince the colleague that their approach is problematic if the system appears to work in testing?
- What specific refactoring steps would you propose to split the ISR into byte-level and message-level processing?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** I'd frame this as a design decision that should be driven by the specific characteristics of the protocol and the team's long-term maintenance constraints, not by personal preference. My approach would be to facilitate a structured comparison rather than picking a side.

First, I'd ask both engineers to articulate the concrete requirements: How many states does the protocol have? How many transitions? Are there many conditional paths based on message content, or is the flow relatively linear? How often is the protocol expected to change? Who will maintain this code in two years? These questions matter because the two approaches have different strengths. A hand-coded state machine is often more readable for small-to-medium protocols with clear states and simple transitions — you can see the logic flow directly in the code. A table-driven approach shines when there are many states and transitions, because the table makes the complete state space visible in one place and adding a new transition is a data change rather than a code change.

Second, I'd suggest we look at the failure modes. In a medical device, we need to verify that every state transition is valid and that invalid transitions are handled safely. A table-driven approach can make this verification easier because the transition table can be reviewed as data — you can check for missing entries, ambiguous transitions, or unreachable states. But it can also obscure the logic if the table is large and the action functions are scattered. A state machine makes the control flow explicit but can become a tangle of nested conditionals if the protocol is complex.

Third, I'd propose a practical experiment: have each engineer implement a small prototype of the most complex part of the protocol using their preferred approach, then compare them on readability, testability, and how easy they are to extend. This grounds the discussion in the actual problem rather than abstract arguments. I'd also consider a hybrid approach — a state machine where the transition logic is table-driven, or a table where the actions are clearly named functions — which often captures the best of both.

Finally, I'd emphasize that whichever approach we choose, the critical requirements are the same: the implementation must be testable, the state space must be auditable for safety, and the code must be maintainable by engineers who weren't involved in the original design. If both approaches meet those criteria, then the decision is about team preference and long-term maintainability — and I'd let the team make that call with a clear timeline for the decision.

**Possible follow-ups:**
- What specific criteria would you use to evaluate the two prototypes?
- How would you handle the situation if one engineer strongly prefers their approach and resists the team's decision?