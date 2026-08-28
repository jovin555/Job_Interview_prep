# firmware — Day 38

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental issue here is that a blocking flash operation in any task will stall the entire system if it runs at a priority that can preempt the sensor task, or if it holds a resource the sensor task needs. The first principle is to never perform flash erase operations synchronously in a task that shares CPU time with a hard real-time task. I'd structure this in layers.

First, I'd move the flash erase operation out of the task context entirely. Most modern MCUs have a flash controller that can operate with interrupts enabled, or at minimum, the erase operation can be broken into a state machine that yields between sectors or pages. If the flash peripheral supports it, I'd use the interrupt or DMA-based flash programming capability so the CPU isn't blocked.

If the flash controller on the target MCU genuinely blocks the CPU during erase, then I need to design around that hardware limitation. One approach is to use a dedicated lower-priority task that performs the erase, but accept that during the erase window, the sensor task will miss deadlines. That's usually unacceptable for a 1 ms sensor read. A better approach is to buffer sensor data during the erase window — if the sensor task can write to a sufficiently large buffer (e.g., a DMA double-buffer) and the data is processed after the erase completes, you can tolerate the gap. This requires understanding the sensor's data rate and whether the application can tolerate a processing backlog.

Another option is to use Zephyr's flash API with its asynchronous operations if available, or to offload the erase to a separate core if the MCU is multi-core. In practice, I'd also look at whether the erase can be scheduled during a known idle period — for example, if the sensor task only needs data during active measurement windows, the erase could be deferred to a period when the sensor isn't sampling.

Finally, I'd verify the actual timing. Flash erase times are often quoted as worst-case, and the real time might be shorter. I'd measure the actual blocking time and see if the sensor task can tolerate it with proper buffering. The key is to make the blocking behavior explicit and bounded, rather than hoping it doesn't collide with a sensor read.

**Possible follow-ups:**
- How would you handle the case where the sensor data buffer overflows during the erase window?
- What Zephyr kernel configuration options would you examine to ensure the scheduler behaves predictably during this scenario?

---

## Q2: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** This pattern — correct at power-on, then gradual drift and noise — points to a thermal or aging effect rather than a software logic bug. I'd approach this systematically, starting with the hardware domain since the symptom is analog in nature.

First, I'd check whether the issue is actually in the ADC reference or the input path. A common cause is the voltage reference drifting as the board heats up. If the reference is derived from the battery through the switching regulator, the regulator's output may drift with temperature, or its ripple may increase as components heat. I'd measure the regulator output and the ADC reference voltage at power-on and again after 30 minutes, using a bench supply to isolate the battery from the equation.

Second, I'd look at the ADC's sampling behavior. If the ADC uses an internal reference and the firmware configures sampling time or acquisition time, thermal drift in the ADC's internal circuits could cause gain error. I'd check whether the firmware periodically recalibrates the ADC — many MCU ADCs have a calibration routine that should be run periodically, not just at startup.

Third, I'd examine the firmware's data processing. If the readings drift slowly, the issue could be in the firmware's offset or gain correction algorithm. For example, if the firmware applies a calibration factor that was computed at manufacturing time, and the analog front-end drifts, the correction becomes invalid. I'd check whether the firmware has any self-calibration or auto-zero capability.

Fourth, I'd consider the battery itself. As the battery discharges, its internal resistance increases, which can affect the regulator's input voltage and cause the output to become noisier. This is especially true if the regulator is a boost converter operating near its minimum input voltage. I'd log the battery voltage over time and correlate it with the ADC drift.

Finally, I'd use a thermal camera or thermocouple to identify hot spots on the board. A component that's dissipating excessive power — like a linear regulator or a series resistor — could be heating nearby analog components. I'd also check the PCB layout for thermal coupling between the switching regulator's inductor and the analog front-end.

In firmware, I'd add diagnostic logging that captures the raw ADC values, the computed reference voltage, and the battery voltage at regular intervals, so I can correlate the drift with system state rather than guessing.

**Possible follow-ups:**
- How would you distinguish between a reference drift and a gain error in the ADC?
- What firmware-side mitigations could you implement if the hardware issue can't be fully resolved?

---

## Q3: You're reviewing a colleague's firmware code that implements a state machine for a medical device's operational modes (idle, calibration, active monitoring, error). The state machine is implemented as a single switch-case inside a 200-line function, with state transitions scattered across multiple modules via global state variables. How would you approach refactoring this for maintainability and safety?

**Answer:** This is a classic case where the code works but is structurally fragile, and in a medical device, that fragility is a safety concern. The core problems are: the state machine logic is centralized in one large function, making it hard to reason about; state transitions are scattered, so it's difficult to verify that all transitions are valid; and global state variables create hidden coupling between modules.

I'd approach the refactoring in stages, with the goal of making the state machine explicit and verifiable without changing behavior.

First, I'd define the state machine formally. I'd enumerate all states, all events that can trigger transitions, and all valid transitions. This becomes a state transition table — either in code or in a document that's reviewed with the team. For a medical device, this table is also valuable for the design history file and for risk analysis, since it lets you systematically check that no invalid transition is possible.

Second, I'd restructure the code so that the state machine is a single module with a well-defined interface. The module would expose functions like `sm_handle_event(event_t event)` and `sm_get_state(void)`. All state transitions would go through this module — no other module can directly modify the state variable. This eliminates the scattered global writes.

Third, I'd replace the monolithic switch-case with a table-driven approach. A table of `{current_state, event, next_state, action}` entries is more maintainable and easier to verify than a nested switch. It also makes it trivial to add a debug assertion that catches invalid transitions — if an event arrives that isn't valid for the current state, the system can log it and enter a safe error state rather than silently ignoring it.

Fourth, I'd consider what happens on invalid transitions. In a medical device, the safety requirement is that the device must never enter an undefined state. So the state machine should have a defined response to unexpected events — typically entering an error state that requires explicit recovery, rather than ignoring the event.

Finally, I'd add unit tests that exercise every valid transition and every invalid event. The test matrix comes directly from the state transition table, so it's easy to verify completeness. I'd also add a runtime assertion in the state machine that fires on invalid transitions during development, so issues are caught early.

The key principle is that a state machine in a medical device should be auditable — you should be able to trace every possible path through the system and verify that it leads to a safe state.

**Possible follow-ups:**
- How would you handle the case where a state transition needs to trigger actions in multiple modules?
- What would you do if the existing code has implicit transitions that aren't documented anywhere?

---

## Q4: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** In a medical monitoring context, the fundamental requirement is that the displayed value must be trustworthy — it's better to show "no data" or an error indicator than to show a plausible but wrong number. So the design philosophy is: validate aggressively, degrade gracefully, and never fabricate data.

I'd structure the module in layers. The lowest layer handles raw communication with the sensor — reading bytes, checking CRCs, and detecting bus-level errors. This layer should never interpret the data; it just reports whether the transaction succeeded and returns the raw bytes.

The next layer performs plausibility checks on the data. This includes range checks (is the value within the sensor's specified operating range?), rate-of-change checks (did the value jump by an implausible amount since the last reading?), and cross-checks if there are redundant sensors. For a medical device, these checks should be derived from the clinical requirements — for example, a heart rate that changes by 50 BPM in one second is physiologically implausible and should be flagged.

The key design decision is what happens when data fails validation. I'd distinguish between transient errors (a single CRC failure) and persistent errors (the sensor has been returning invalid data for N consecutive readings). For transient errors, the module should retain the last valid reading and indicate that it's stale — perhaps with a timestamp or a "data age" indicator. For persistent errors, the module should transition to a degraded state where the display shows "sensor error" or similar, and the system should alert the clinician.

Critically, the module must never extrapolate or fill in missing data. If the last valid reading was 5 seconds ago, the display should show that reading with an indicator that it's not current, not silently display it as if it were live. The clinician needs to know the data's freshness.

I'd also implement a hysteresis mechanism to prevent rapid toggling between valid and invalid states. For example, if the sensor returns one bad reading, you might not immediately alarm — but if it returns three bad readings in a row, you escalate. This prevents nuisance alarms while still catching real failures.

Finally, I'd make sure the module's behavior is fully specified in the requirements and traceable to the risk analysis. The failure modes — what happens when the sensor fails, what the display shows, what alarms are triggered — should be documented and tested, because in a medical device, the failure behavior is as important as the normal behavior.

**Possible follow-ups:**
- How would you decide on the threshold for declaring a sensor "failed" versus "temporarily noisy"?
- How would you handle the case where the sensor returns values that are within range but clearly wrong (e.g., a temperature sensor reading 25°C when the patient is febrile)?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** This is a classic engineering trade-off, and the right answer depends on the specific requirements of the protocol and the system. My role as the lead is to make sure the decision is based on data and requirements, not on personal preference or dogma.

First, I'd establish the protocol's requirements. What's the maximum latency for receiving a message? What's the minimum time between messages? What's the maximum message size? Is the protocol time-critical, or is it best-effort? These numbers determine whether polling can meet the requirements at all. If the protocol requires response within 10 µs and the main loop runs at 1 kHz, polling is simply not viable.

Second, I'd quantify the CPU cost of each approach. Polling has a predictable CPU cost — it's a fixed overhead per loop iteration, regardless of whether data arrives. Interrupts have a variable cost — near-zero when idle, but potentially high when data arrives in bursts. I'd ask both engineers to estimate the worst-case CPU utilization for their approach, given the protocol's data rate. If the polling overhead is, say, 5% of CPU, that might be acceptable. If it's 40%, that's a problem.

Third, I'd consider the system's other real-time requirements. If there's a 1 kHz control loop, the polling approach might introduce jitter if the polling code runs in the main loop. But interrupts can also introduce jitter if the ISR is too long. The question is which approach better isolates the control loop from the communication traffic.

Fourth, I'd look at the failure modes. Polling is more predictable — if the main loop is running, the protocol is being serviced. Interrupts can be lost if the interrupt priority is too low or if the ISR is too long. But polling can miss data if the main loop is delayed by other tasks. I'd ask the team to identify the failure modes and their consequences for the specific protocol.

Finally, I'd suggest a hybrid approach if both engineers have valid points. For example, use interrupts to signal that data is available, but do the actual processing in a task or the main loop. This gives responsiveness without putting complex logic in an ISR. Or use polling with a timeout — poll for a short period, then yield to other tasks.

The decision should be documented with the rationale, including the requirements that drove it. If the requirements change later, the decision can be revisited. I'd also suggest prototyping both approaches if time permits — a quick benchmark can settle arguments that would otherwise go in circles.

**Possible follow-ups:**
- How would you handle the situation where the two engineers continue to disagree after you've made a decision?
- What metrics would you use to evaluate which approach actually performs better in practice?