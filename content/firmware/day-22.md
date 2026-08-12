# firmware — Day 22

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental issue is that a blocking flash erase in a lower-priority task can stall the entire system, including the 1 kHz sensor task, because the flash controller is typically shared and the erase operation monopolizes the bus. I'd approach this in layers:

First, I'd check whether the flash erase can be moved to a dedicated low-priority thread and whether the flash driver supports asynchronous or interrupt-driven operations. Many modern MCUs allow flash operations to proceed while the CPU continues executing from cache or RAM, so the erase doesn't need to block the CPU — only the flash bus. If the flash controller supports it, I'd use the asynchronous API so the erase runs in the background and the sensor task never sees a stall.

If the hardware doesn't support asynchronous flash operations, the next option is to break the erase into smaller chunks — erase page-by-page or sector-by-sector rather than the full 100 ms in one call. This lets the scheduler interleave the erase with the sensor task. The trade-off is that the erase takes longer overall, but the 1 ms deadline is preserved.

Third, I'd verify the sensor task's actual worst-case execution time. If the sensor read itself takes, say, 200 µs, then even with the flash erase blocking for 100 ms, the sensor task would miss its deadline by a huge margin. But if the sensor read is only 50 µs and the task has some slack, I might be able to use a higher-priority interrupt-driven approach for the sensor read itself, bypassing the RTOS scheduler entirely for the critical data capture.

Finally, I'd consider whether the sensor data can be buffered. If the sensor produces data continuously and the 1 ms read is just sampling, a DMA-based approach could capture data into a buffer without CPU involvement during the flash erase, and the sensor task would only need to process the buffered data after the erase completes. This decouples the timing-critical data acquisition from the flash operation.

The key principle is to identify the actual resource conflict — is it the CPU, the flash bus, or the scheduler — and address that specific bottleneck rather than just increasing the sensor task's priority.

**Possible follow-ups:**
- How would you determine whether the flash erase is actually blocking the CPU or just the flash bus on your specific MCU?
- What if the sensor data must be processed in real-time (not just captured) — how would that change your approach?

---

## Q2: You're reviewing a colleague's firmware code that implements a state machine for a medical device's operational modes (idle, calibration, active monitoring, error). The state machine is implemented as a single switch-case inside a 200-line function, with state transitions scattered across multiple modules via global state variables. How would you approach refactoring this for maintainability and safety?

**Answer:** This is a classic case where the state machine has outgrown its original structure. The core problems are: (1) the state variable is global, so any module can modify it without going through defined transition logic; (2) the switch-case function is likely handling both state actions and transition logic, making it hard to reason about; and (3) there's no central place to enforce valid transitions or add guards.

I'd refactor this in stages, being careful not to change behavior while restructuring:

First, I'd create a single module that owns the state variable — making it `static` and exposing only controlled accessor functions. This immediately prevents arbitrary external modification. The accessor functions would be the only way to request a state change, and they'd go through a central transition table.

Second, I'd separate the state machine into two concerns: the state action (what happens while in a state) and the transition logic (what triggers a move to another state). The 200-line switch-case would be split into per-state handler functions, each responsible for its own action and for returning the next state based on events. This makes each state's behavior testable in isolation.

Third, I'd introduce a transition table that explicitly defines which transitions are valid. For a medical device, this is critical — you don't want an unexpected transition from "calibration" directly to "active monitoring" without going through a validation step. The table would include guard conditions (e.g., "calibration complete" flag must be set) and would log any invalid transition attempts for debugging.

Finally, I'd add unit tests around the state machine. Since the state machine is now a self-contained module with a defined interface, I can test every valid and invalid transition without needing the full device hardware. This is especially important for a medical device where you need to demonstrate that the state machine behaves correctly under all conditions.

The key is to make the refactoring incremental — each step should leave the code in a working state, and the behavior should be verified against the original implementation before moving to the next step.

**Possible follow-ups:**
- How would you handle the case where a state transition needs to trigger actions in multiple modules (e.g., starting a motor and enabling a sensor)?
- What testing strategy would you use to verify the refactored state machine matches the original behavior?

---

## Q3: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core requirement is that invalid data must never reach the display, but the device must also continue operating and communicate the degraded state appropriately. I'd design this in layers:

First, at the driver level, I'd validate every sensor reading before it enters the system. This includes checking the CRC or checksum, verifying the data is within the sensor's specified range, and checking for consistency with recent readings (e.g., a sudden jump that's physiologically impossible). Any reading that fails validation is flagged as invalid and not propagated upward.

Second, at the application level, I'd implement a data quality policy. The policy defines what happens when invalid data is received: for a single invalid reading, the system might hold the last valid reading and display it with a "data stale" indicator; for consecutive invalid readings, the system might transition to a "sensor fault" state and alert the clinician. The exact thresholds depend on the clinical use case — for a continuous monitoring device, a few seconds of stale data might be acceptable, but for a device detecting critical events, even a single missed reading could be significant.

Third, I'd implement a voting or redundancy scheme if the sensor data is critical. For example, if the device has multiple sensors measuring the same parameter, the firmware could compare readings and only display data that agrees across sensors. If only one sensor is available, the firmware would apply stricter validation and more conservative hold-over policies.

Fourth, I'd ensure the display logic is separate from the data acquisition logic. The display module should only receive validated, quality-checked data through a defined interface. It should never directly access the sensor driver. This separation ensures that a bug in the display code can't cause a false reading to appear.

Finally, I'd implement comprehensive logging of all invalid data events. This is important for both debugging and for regulatory compliance — if there's ever a question about whether the device displayed a false reading, the log provides an audit trail of what data was received, why it was rejected, and what the device did in response.

The key principle is defense in depth: validation at multiple layers, clear policies for handling invalid data, and a clean separation between data acquisition, validation, and display.

**Possible follow-ups:**
- How would you determine the appropriate threshold for when to declare a sensor fault versus continuing with stale data?
- How would you handle the case where the sensor returns data that passes validation but is still physiologically implausible (e.g., a heart rate of 400 bpm)?

---

## Q4: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** This pattern — correct at power-on, then gradual drift and noise — points to a thermal or power-related issue rather than a firmware logic bug. I'd approach this systematically:

First, I'd characterize the problem precisely. Is the drift monotonic (always increasing) or random? Does it correlate with battery voltage, device temperature, or time since power-on? I'd add temporary debug logging to capture ADC readings, battery voltage, and temperature (if a sensor is available) over the 30-minute window. This data would help narrow down the root cause.

Second, I'd suspect the switching regulator. As the battery discharges, the regulator's input voltage drops, and its output ripple or noise characteristics can change. If the ADC's reference voltage is derived from the same regulator, the readings would drift as the reference drifts. I'd check whether the ADC reference is independent of the switching regulator output, and whether the regulator's output is stable over the battery's discharge curve.

Third, I'd consider thermal effects. After 30 minutes, the device has reached thermal equilibrium. Components like the ADC, the voltage reference, or the regulator can have temperature coefficients that cause drift. I'd check the datasheets for the temperature coefficients and calculate whether the observed drift is consistent with the expected temperature rise. I'd also check whether any component is being heated by adjacent circuitry — for example, a regulator placed too close to the ADC or reference.

Fourth, I'd look at the PCB layout. The switching regulator's inductor and switching node can couple noise into the ADC's analog input or reference traces. This coupling might be present from the start but only becomes noticeable as the battery voltage drops and the regulator's duty cycle changes. I'd review the layout for proper ground separation between the analog and digital sections, and check that the ADC's analog input traces are shielded from the switching node.

Fifth, I'd verify the firmware's ADC configuration. Is the ADC sampling time long enough for the source impedance? Is the ADC reference configured correctly? Is there any averaging or filtering that might mask early noise but become ineffective as the noise increases? I'd also check whether the ADC is being read while the switching regulator is actively switching — if the ADC conversion coincides with the regulator's switching transient, the reading could be corrupted.

Finally, I'd consider whether the issue is actually in the sensor or signal chain rather than the ADC itself. If the sensor's output impedance changes with temperature, or if a coupling capacitor is drifting, the readings would change even with a perfect ADC.

The key is to gather data first, form hypotheses based on the data, and then test each hypothesis in a controlled way — for example, by powering the device from a bench supply at a fixed voltage to eliminate the battery discharge variable, or by using a thermal chamber to control temperature.

**Possible follow-ups:**
- How would you isolate whether the drift is in the ADC reference, the sensor, or the signal conditioning circuitry?
- What specific measurements would you take to confirm or rule out the switching regulator as the source of the noise?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** This is a classic engineering trade-off, and the right answer depends on the specific requirements of the system. My role as the lead is to guide the team toward a data-driven decision rather than letting it become a matter of personal preference.

First, I'd establish the requirements. What are the timing constraints for the communication protocol? What's the worst-case latency that's acceptable? What's the data rate? How often does data arrive — is it periodic, bursty, or event-driven? What's the CPU load budget? These requirements should be written down and agreed upon before evaluating approaches.

Second, I'd ask each engineer to articulate the specific risks they're concerned about. The polling advocate is likely worried about interrupt latency variability, priority inversion, or missed interrupts under load. The interrupt advocate is likely worried about CPU waste from polling, or the inability to meet latency requirements with a polling loop. Understanding the specific concerns helps us evaluate whether they're real risks for this particular system.

Third, I'd suggest a hybrid approach as a middle ground. For example, a polling approach with a hardware timer that guarantees a minimum polling frequency, combined with an interrupt for exceptional conditions (e.g., buffer overflow or error). Or an interrupt-driven approach where the ISR only sets a flag and defers processing to a task, keeping the ISR minimal. This often resolves the tension by giving each side what they need: predictability from the polling side and responsiveness from the interrupt side.

Fourth, I'd propose a structured evaluation. If the team can't agree, I'd suggest implementing a prototype of each approach and measuring the key metrics: worst-case latency, CPU utilization, and code complexity. The measurements would be done under realistic load conditions, not just idle. This turns the debate from opinion into data.

Finally, I'd consider the broader context: maintainability, testability, and the team's familiarity with each approach. For a medical device, the approach that's easier to verify and validate might be preferred even if it's slightly less efficient. The approach that the team can maintain confidently over the product's lifetime is often the right choice.

The key is to keep the discussion focused on the system's requirements and measurable outcomes, not on personal preferences or past experiences with similar systems.

**Possible follow-ups:**
- What specific metrics would you use to compare the two approaches in a prototype?
- How would you handle the situation where the measurements show both approaches meet the requirements, but the team still can't agree?