# firmware — Day 20

## Q1: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** This symptom pattern — stable at power-on, degrading over time — points me toward thermal effects, reference drift, or power supply degradation rather than a purely digital logic issue. I'd approach it systematically:

First, I'd characterize the failure precisely. I'd log the raw ADC codes (not the converted engineering units) alongside timestamps, ambient temperature, and battery voltage to understand whether the drift is monotonic, cyclic, or correlated with any other observable. This data separates "the ADC reference is drifting" from "the signal path is picking up noise" from "the supply rail is degrading."

Next, I'd look at the voltage reference. If the ADC uses an internal reference, I'd check whether the reference has a temperature coefficient that explains the drift magnitude. I'd also verify whether the reference input has adequate decoupling — a marginal bypass capacitor can cause the reference to drift as the board heats up and capacitor characteristics change.

For the switching regulator angle, I'd examine the ripple and transient response on the analog supply rail. A switching regulator's output ripple can increase as components heat up — particularly the output capacitor if it's a ceramic type with DC-bias derating, or if the inductor's saturation characteristics shift with temperature. I'd use a scope with a differential probe to measure the actual rail noise at the ADC's supply pin, not just at the regulator output, because the PCB trace impedance between them matters.

I'd also check the ADC's sampling capacitor and input path. If the source impedance is too high relative to the ADC's sampling time, the readings can become inaccurate — and this effect can worsen as the board heats and the source's output impedance changes. Adding a buffer amplifier or increasing the sampling time in firmware might resolve it.

Finally, I'd consider firmware-level mitigation: implementing a periodic self-calibration routine that measures a known reference voltage and applies a correction factor, or switching to a ratiometric measurement approach if the sensor allows it. But I'd only do this after understanding the root cause — masking the symptom without knowing the mechanism risks hiding a safety-relevant failure in a medical device.

**Possible follow-ups:**
- How would you distinguish between the ADC reference drifting versus the input signal path degrading?
- What specific measurements would you take to confirm or rule out the switching regulator as the cause?

---

## Q2: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core requirement here is that we must never present invalid data as valid — the failure mode we're designing against is "false confidence," not just "missing data." I'd structure this in layers:

**Layer 1: Detection.** Every reading goes through a validation pipeline before it's considered usable. This includes protocol-level checks (CRC, framing, address verification), range checks (is the value physiologically plausible?), rate-of-change checks (did the value jump more than is physically possible between samples?), and consistency checks (does it agree with correlated parameters?). Each check has defined thresholds based on clinical requirements, not arbitrary engineering guesses.

**Layer 2: Classification.** Not all invalid data is equal. A single CRC failure might be a transient glitch; a persistent out-of-range value might indicate sensor failure. I'd classify failures as transient, intermittent, or persistent, and track the recent history of failures to distinguish between these.

**Layer 3: Response.** The response depends on the classification and the clinical context:
- For a transient failure (single bad sample), I'd discard that sample and continue with the next one, but I'd flag that a discard occurred.
- For intermittent failures, I'd consider whether to use the last valid reading with a "data stale" indicator, or to show "no data" — this is a clinical decision that needs input from the medical team.
- For persistent failure, the device must enter a defined degraded mode: clearly display that the parameter is unavailable, trigger an alarm, and follow the device's fault-handling protocol.

**Layer 4: User interface.** The clinician must never see a value that isn't backed by valid data. If we're displaying a held value, it must be visually distinct (e.g., dashed outline, different color, "stale" indicator). If we're showing "no data," that must be unambiguous. The UI design needs clinical input to ensure the presentation is clear in practice.

**Layer 5: Logging and traceability.** Every validation failure, classification decision, and display action is logged with timestamps. In a medical device, we need to be able to reconstruct exactly what happened during an adverse event — including what the device displayed and why.

I'd also emphasize that the validation thresholds and response logic need to be documented in the requirements and traceable to clinical input. This isn't just an engineering decision — it's a patient-safety decision that needs multidisciplinary review.

**Possible follow-ups:**
- How would you decide between displaying the last valid reading versus showing "no data" when a sensor becomes intermittent?
- What validation checks would you prioritize if you could only implement three?

---

## Q3: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 2 ms, but a lower-priority task occasionally needs to perform a flash write that can block for up to 50 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental problem is that a blocking flash operation in one task can starve a higher-priority task, which violates the priority model. I'd approach this by eliminating the blocking from the critical path rather than trying to schedule around it.

First, I'd check whether the flash write can be moved off the lower-priority task's critical path entirely. Options include:
- Using a dedicated flash-writer thread that receives data via a queue and performs the write asynchronously. The lower-priority task just enqueues the data and returns immediately.
- Using DMA for the flash write if the flash controller supports it, so the CPU isn't blocked during the transfer.
- Using the flash controller's "write while read" capability if the MCU supports it, allowing code to execute from RAM or a different flash bank during the write.

If the flash operation genuinely must block (e.g., the flash controller requires the CPU to be stalled during the erase), then I'd look at the timing more carefully. A 50 ms block is 25 sensor periods — that's not acceptable if the sensor data is time-critical. In that case, I'd consider:
- Buffering sensor data during the flash operation. If the sensor task can write to a buffer that's large enough to hold 50 ms of data (at 2 ms period, that's 25 samples), the sensor task can continue capturing data while the flash write proceeds. The sensor task would need to be designed to handle the buffer being full — either by dropping the oldest data (with a flag) or by signaling an overflow condition.
- Splitting the flash write into smaller chunks. Some flash controllers allow partial-page writes or sector-erase operations that can be interrupted and resumed. This trades complexity for reduced blocking time.
- Using a cooperative approach where the flash task yields periodically during the write, allowing the sensor task to run between chunks. This requires the flash driver to support interruptible operations.

I'd also examine whether the 2 ms sensor period is a hard real-time requirement or a soft one. If the sensor data is used for a control loop, missing a sample might be acceptable if the controller can handle it. If it's for waveform capture, missing samples corrupts the data. This distinction drives how much complexity I'd invest in the solution.

Finally, I'd verify the actual worst-case blocking time empirically. Flash write times in datasheets are often nominal — the actual time can vary with temperature, voltage, and the number of program/erase cycles. I'd measure the real worst case and design for that, not the datasheet value.

**Possible follow-ups:**
- How would you decide between buffering sensor data versus using a dedicated flash-writer thread?
- What happens if the sensor data buffer overflows during a long flash operation?

---

## Q4: You're reviewing a colleague's firmware code that implements a state machine for a medical device's operational modes (idle, calibration, active monitoring, error). The state machine is implemented as a single switch-case inside a 200-line function, with state transitions scattered across multiple modules via global state variables. How would you approach refactoring this for maintainability and safety?

**Answer:** This is a safety-critical refactoring, so my approach would be incremental and verification-driven rather than a rewrite. The current design has several problems: the state machine logic is centralized but the state transitions are scattered, global state variables create hidden dependencies, and a 200-line switch-case is difficult to reason about for correctness.

I'd start by documenting the current behavior. I'd map out all the states, events, transitions, and actions from the existing code — including the scattered transitions. This becomes the specification for the refactored version. I'd also identify any implicit states or transitions that exist only through the interaction of global variables, which are often the source of subtle bugs.

For the refactored design, I'd use a table-driven state machine with explicit transition tables. Each state has a defined set of events it can handle, with a transition table mapping (state, event) → (next state, action). This makes all transitions visible in one place and eliminates the scattered global variable writes. The table-driven approach also makes it easier to verify completeness — I can check that every (state, event) combination has a defined response, including invalid or unexpected events.

I'd also encapsulate the state machine in a module with a clean interface: an `event_t` input, a `state_t` output, and a set of action callbacks. No other module should be able to directly modify the state — all transitions go through the state machine module. This eliminates the global variable problem.

For the actions, I'd separate them from the transition logic. Each transition can trigger one or more actions (entering a state, exiting a state, or responding to an event). These actions are function pointers in the transition table, which keeps the table readable and the actions testable in isolation.

The refactoring process would be: extract the state machine into its own module with the table-driven design, then migrate the scattered transitions one at a time, testing after each migration. I'd maintain a test harness that exercises all documented transitions and verifies that the refactored behavior matches the original. For a medical device, I'd also want the refactored state machine to be reviewed against the requirements to ensure no behavior was lost or changed.

One important consideration: the refactored state machine should be deterministic and fail-safe. If an unexpected event occurs in a given state, the device should transition to a defined error state rather than silently ignoring the event or falling through to undefined behavior.

**Possible follow-ups:**
- How would you verify that the refactored state machine behaves identically to the original?
- What would you do if you discovered the original state machine had a bug during the refactoring process?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to use a polling approach or an interrupt-driven approach for a critical communication protocol. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** This is a classic engineering trade-off, and the right answer depends on the specific requirements — not on which approach is "better" in general. My role as the lead is to structure the decision-making process so the team evaluates the options against the actual constraints rather than arguing from preference.

First, I'd establish the requirements that matter for this decision. For a communication protocol, the key questions are:
- What is the worst-case latency we can tolerate for receiving a message?
- What is the worst-case latency for responding to a message?
- What is the message arrival pattern — periodic, bursty, or sporadic?
- What else is the CPU doing while the communication is happening?
- What are the power constraints? (Interrupt-driven can allow the CPU to sleep between events; polling requires the CPU to be active.)
- What is the failure mode if we miss a message or respond too late?

With these requirements defined, I'd ask the team to evaluate both approaches against them. Polling is genuinely simpler — no interrupt context, no shared-data synchronization, no priority inversion concerns. It's predictable in the sense that the worst-case latency is bounded by the polling period. But it has a cost: the CPU is busy polling even when there's no data, and the polling period must be short enough to meet the latency requirement, which can waste CPU cycles.

Interrupt-driven is more responsive — the CPU only spends time on communication when there's actual data. But it introduces complexity: interrupt context, shared data between ISR and main context, potential for missed interrupts if the ISR is too long, and priority interactions with other interrupts in the system.

I'd also ask the team to consider a hybrid approach: interrupt-driven reception (to avoid missing data) with polling for transmission (which is typically less time-critical and easier to handle in the main loop). This is often the right answer for communication protocols.

To move the decision forward, I'd suggest a structured evaluation: have each engineer write up their proposed design with the specific requirements mapped to how their approach meets them, including worst-case timing analysis. Then we'd review both designs as a team, looking for gaps or assumptions. If both approaches genuinely meet the requirements, I'd lean toward the simpler one — but "simpler" needs to be defined in terms of maintainability, testability, and risk, not just code size.

If the disagreement persists after the evaluation, I'd propose a prototype or simulation to measure the actual worst-case latencies under realistic conditions. Data beats opinion. I'd also make sure the decision is documented with the rationale, so future engineers understand why the choice was made.

**Possible follow-ups:**
- What specific requirements would make you choose polling over interrupts, and vice versa?
- How would you handle the shared-data synchronization if you chose an interrupt-driven approach?