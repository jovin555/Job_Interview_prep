# firmware — Day 21

## Q1: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** This symptom pattern — stable at power-on, degrading over time — points me toward thermal drift or a power-supply issue that develops as the system warms up. I'd start by ruling out the simplest causes before diving into complex theories.

First, I'd check whether the ADC reference voltage is stable. If the reference is derived from the battery rail through the switching regulator, the regulator's output may drift as components heat up, or ripple may increase as the load changes. I'd put a scope on the ADC reference pin and the analog supply rail, measuring both at power-on and again after 30 minutes, looking for changes in DC level, ripple amplitude, or switching noise.

Second, I'd check the ADC itself. Many MCU ADCs have internal reference options, and some references have significant temperature coefficients. If the device is in an enclosure that heats up, the internal reference could be drifting. I'd compare readings against a known stable external reference to isolate whether the drift is in the sensor, the ADC, or the reference.

Third, I'd look at the sensor's excitation or bias circuitry. If the sensor is resistive (like a thermistor or strain gauge), the excitation voltage may be drifting, which would directly affect the reading. I'd measure the excitation voltage over time.

I'd also consider firmware factors: is the ADC sampling at the same point in the switching regulator's ripple cycle? If the regulator's switching frequency drifts with temperature, the sampling point relative to the ripple could shift, introducing noise. I'd check whether the ADC sampling is synchronized to the regulator's switching frequency or whether I need to add more averaging or filtering.

Finally, I'd examine the PCB layout for thermal effects — for example, a ground plane that develops a voltage gradient as current draw increases, or a decoupling capacitor that degrades as it heats. I'd use a thermal camera if available to identify hot spots near the analog front end.

The key is to gather data methodically: measure the same signals at multiple time points, correlate changes with temperature, and isolate the analog chain stage by stage.

**Possible follow-ups:**
- How would you distinguish between the ADC reference drifting versus the sensor signal itself drifting?
- What firmware-side mitigations could you apply while the hardware investigation is ongoing?

---

## Q2: How would you approach designing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core requirement is that the device must never present invalid data as valid — the risk is a clinician making a decision based on a false reading. So the design philosophy is "when in doubt, don't display a number; display the state."

I'd structure the module in layers. The lowest layer handles raw communication with the sensor — sending commands, receiving responses, checking CRCs, and detecting bus-level errors. This layer never interprets data; it just reports success or failure with the raw payload.

The next layer applies validation rules. These come from the sensor's datasheet and the clinical requirements: valid ranges for each parameter, expected rates of change between consecutive readings, and plausibility checks (e.g., a heart rate that jumps from 70 to 200 in one sample is suspect). I'd also apply redundancy checks if the sensor provides any — for example, a checksum or duplicate measurement.

The decision layer then determines what to present to the user. If a single reading fails validation, I'd flag it as suspect and either retry immediately or hold the last valid reading with a "data stale" indicator. If multiple consecutive readings fail, I'd transition to a "sensor fault" state and display an explicit error message rather than a number. The key is that the display always reflects the device's confidence in the data: a valid number, a stale number with a warning, or no number with an error.

I'd also implement a voting or averaging scheme where appropriate. For example, if the sensor provides multiple samples per second, I could require two consecutive valid readings before updating the display, or use a median filter to reject outliers. This trades a small amount of latency for significantly higher confidence.

Finally, I'd ensure that the fault state is self-clearing — when the sensor recovers, the device should automatically return to normal operation, but only after confirming several consecutive valid readings. And I'd log all invalid-data events with timestamps for post-market surveillance, since this is exactly the kind of data that matters for regulatory reporting.

**Possible follow-ups:**
- How would you handle the case where the sensor returns data that passes range checks but is still clinically implausible?
- What would you do if the sensor's error rate is low but non-zero — how would you decide whether to retry, hold last value, or display an error?

---

## Q3: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 2 ms, but a lower-priority task occasionally needs to perform a flash write that can block for up to 50 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental problem is that a blocking flash operation in a lower-priority task can starve a higher-priority task if the RTOS scheduler can't preempt the blocking operation. The first principle is that the flash write must never block the sensor task.

I'd start by examining whether the flash write can be made non-blocking. Many MCU flash controllers support programming via a background mechanism — you start the write and poll or interrupt when it completes. If the hardware supports it, I'd use an interrupt-driven approach where the flash write runs in the background and the lower-priority task waits on a semaphore that's signaled on completion. This way, the sensor task can preempt the lower-priority task at any point.

If the flash controller doesn't support background operation, I'd look at whether the write can be deferred or batched. For example, if the lower-priority task is logging data, I could buffer the data in RAM and write to flash in smaller chunks that fit within the sensor task's idle time. Or I could use a double-buffering scheme where one buffer is being written to flash while the other is being filled.

Another option is to move the flash write to an even lower priority or to a dedicated task that runs only when the sensor task is not active. But this only works if the sensor task has guaranteed idle periods — which isn't the case with a strict 2 ms period.

I'd also consider whether the flash write can be split into smaller operations. If the flash page size is large, I might write only the changed bytes rather than the full page, reducing the blocking time. Some flash controllers allow partial-page programming, which can reduce the write time significantly.

If none of these options work, I'd need to reconsider the architecture. For example, could the sensor data be buffered in a DMA ring buffer so that the sensor task doesn't need to run every 2 ms — it could run every 10 ms and process a batch of 5 samples? This would create a larger scheduling window for the flash write.

Finally, I'd verify the actual worst-case blocking time empirically. Datasheet write times are often optimistic; I'd measure the real flash write time on the target hardware and confirm that the chosen approach meets the timing budget with margin.

**Possible follow-ups:**
- What if the flash controller doesn't support non-blocking writes — how would you handle the blocking time?
- How would you verify that the sensor task never misses its 2 ms deadline under worst-case conditions?

---

## Q4: You're reviewing a colleague's firmware code that implements a state machine for a medical device's operational modes (idle, calibration, active monitoring, error). The state machine is implemented as a single switch-case inside a 200-line function, with state transitions scattered across multiple modules via global state variables. How would you approach refactoring this for maintainability and safety?

**Answer:** This is a classic case where the code works but is structurally fragile — the kind of thing that becomes dangerous as features are added. I'd approach the refactoring in stages, prioritizing safety and testability.

First, I'd establish a safety baseline. Before changing anything, I'd make sure there are tests that exercise the current behavior — even if they're just manual test scripts. For a medical device, I'd want to document the expected state transitions and the conditions that trigger them, so I have a specification to refactor against.

The core problem is that state transitions are scattered and implicit. I'd centralize them. The standard pattern is a table-driven state machine: a table that maps (current state, event) to (next state, action). This makes all transitions visible in one place, which is critical for safety review. The table can be a static const array in C, which also means it can be placed in flash to avoid accidental corruption.

I'd also encapsulate the state variable. Instead of a global that any module can read or write, I'd create a state machine module with an API: `sm_handle_event(event_t event)` and `sm_get_state(void)`. All state transitions go through this module, and the state variable is static — no external module can modify it directly. This prevents the "scattered transitions" problem by construction.

For the actions, I'd extract each action into its own function rather than inline code in the switch-case. This makes each action testable in isolation and keeps the state machine logic clean. The action functions should be pure — they take inputs and produce outputs, with no hidden global state.

I'd also think about what events the state machine needs. Rather than having modules call the state machine with arbitrary events, I'd define a fixed set of events that are meaningful at the system level: `EVT_POWER_ON`, `EVT_CALIBRATION_REQUESTED`, `EVT_CALIBRATION_COMPLETE`, `EVT_SENSOR_FAULT`, `EVT_SENSOR_RECOVERED`, and so on. This forces the team to think about what events actually drive the system, rather than exposing internal implementation details.

Finally, I'd add defensive checks. The state machine should reject invalid transitions — if an event arrives that isn't valid in the current state, it should be logged and ignored (or trigger an error state, depending on the safety requirements). This catches bugs early rather than letting the system drift into an undefined state.

The refactoring should be done incrementally: first add the state machine module alongside the existing code, then migrate one transition at a time, running tests after each migration. This reduces the risk of introducing regressions.

**Possible follow-ups:**
- How would you handle the case where an action function needs to trigger a state transition — wouldn't that create circular dependencies?
- How would you test the refactored state machine to ensure it behaves identically to the original?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** This is a classic engineering trade-off, and the right answer depends on the specific requirements — not on which approach is "better" in the abstract. My role as the lead is to make sure the decision is based on data, not preference.

I'd start by framing the decision criteria. For a critical communication protocol, the key questions are: What's the worst-case latency we can tolerate for receiving a message? What's the maximum data rate? How much CPU time can we afford to spend on communication? What's the interrupt latency budget on our specific MCU? And critically — what happens if we miss a message? Is it a retry, or is it a safety event?

I'd ask both engineers to write down their proposed architecture in terms of concrete numbers: worst-case polling interval, worst-case interrupt latency, CPU utilization, and memory footprint. Then we'd evaluate both against the requirements. This turns a philosophical debate into an engineering comparison.

There are also hybrid approaches worth considering. For example, we could use interrupt-driven reception to wake the system and set a flag, but then process the data in the main loop — this gives responsiveness without putting complex processing in the interrupt context. Or we could use DMA with a ring buffer, where the DMA controller handles the data transfer and interrupts only when a complete message is received. This is often the best of both worlds: low CPU overhead, high responsiveness, and no risk of dropping data.

I'd also consider the team's experience and the maintainability of the code. If the team has deep experience with polling and the timing requirements are loose enough, polling might be the pragmatic choice. If the protocol is complex and timing-critical, interrupts might be necessary. But I'd push back on "simpler" as a justification — a polling loop with complex state handling can be harder to maintain than a well-structured interrupt handler.

Finally, I'd suggest a prototype. If the timing requirements are tight enough that the choice matters, we should build a minimal proof-of-concept for both approaches and measure the actual performance on the target hardware. Datasheet numbers are rarely accurate enough for this kind of decision — we need real measurements.

The key is to make the decision based on requirements and data, not on who argues more persuasively. As the lead, I'd facilitate that process and make sure both engineers feel heard, even if their preferred approach isn't chosen.

**Possible follow-ups:**
- What if the prototype shows that both approaches meet the requirements — how would you make the final call?
- How would you handle the situation where one engineer strongly disagrees with the final decision?