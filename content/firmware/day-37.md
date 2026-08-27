# firmware — Day 37

## Q1: How would you approach designing a power management subsystem in Zephyr RTOS for a battery-powered medical device that must wake periodically to sample a sensor, process the data, and transmit results wirelessly, while ensuring no sensor readings are missed during the transition between sleep and active states?

**Answer:** The core challenge here is coordinating the timing between the device's sleep/wake cycle and the sensor's own power-up and stabilization requirements. I'd start by mapping out the timing budget: how long the sensor needs to stabilize after power-up, how long the ADC or communication interface needs to settle, and how long the wireless transmission takes. Once I have that, I'd structure the system around Zephyr's power management subsystem, using the PM state machine to define distinct states — typically a deep sleep state and an active state, possibly with an intermediate "sensor warm-up" state.

The key design decision is where the sensor power domain sits relative to the MCU's sleep state. If the sensor can be powered from a GPIO-controlled rail, I'd sequence it carefully: wake the MCU on a timer, power up the sensor rail, wait for stabilization, then sample. But the risk is that the MCU goes back to sleep too early or the sensor isn't ready. A more robust approach is to use a two-stage wake: the RTC wakes the MCU, the MCU powers the sensor and enters a low-power wait state (like WFI or a light sleep) while the sensor stabilizes, then a sensor-ready interrupt or a short timer wakes the MCU for the actual sample. This avoids busy-waiting during stabilization and keeps power consumption low.

For Zephyr specifically, I'd use the power management subsystem's `pm_state` callbacks to manage the transition, and I'd be careful about which peripherals are retained versus powered off. The RTC must stay alive, and the sensor's power GPIO must be in a known state. I'd also consider using Zephyr's `sys_suspend` hooks to save and restore any volatile sensor configuration. The critical validation is to measure the actual wake-to-sample latency on hardware — datasheet timings are rarely exact, and the stabilization time can drift with temperature and battery voltage.

**Possible follow-ups:**
- How would you handle the case where the sensor's stabilization time varies with temperature or battery voltage?
- What Zephyr kernel configuration options would you need to enable to support this power scheme, and how would you verify that the system actually enters the intended low-power state?

---

## Q2: You're reviewing a colleague's firmware code that implements a state machine for a medical device's operational modes (idle, calibration, active monitoring, error). The state machine is implemented as a single switch-case inside a 200-line function, with state transitions scattered across multiple modules via global state variables. How would you approach refactoring this for maintainability and safety?

**Answer:** The first concern is safety: with global state variables and scattered transitions, it's very hard to prove that the device can't enter an invalid state or make an illegal transition — which is a serious problem for a medical device where state determines what the device is allowed to do (e.g., you must not enter active monitoring from calibration without completing a validation step). I'd approach this refactoring in stages rather than rewriting everything at once.

First, I'd centralize the state variable — make it a single, module-private variable with accessor functions, so all transitions go through one place. This immediately gives us a choke point where we can add validation. Next, I'd replace the monolithic switch-case with a table-driven state machine: a table of valid transitions (current state, event, guard condition, next state, action). This makes the state machine's behavior explicit and auditable — you can literally read off every possible transition from the table, which is invaluable for a safety review.

The guard conditions are where the safety logic lives. For example, a transition from "calibration" to "active monitoring" might require a guard that calibration completed successfully. I'd also add a default handler for invalid events that logs the error and transitions to the error state rather than silently ignoring it. For the scattered transitions across modules, I'd replace direct state manipulation with event posting — modules send events to the state machine rather than changing state themselves. This decouples the modules and makes the state machine the single source of truth.

Finally, I'd add unit tests that exercise every transition in the table, including invalid ones, to verify the guards work as intended. For a medical device, this refactoring isn't just about code quality — it's about making the state logic verifiable for regulatory purposes.

**Possible follow-ups:**
- How would you handle the case where an event arrives that is valid in the current state but the guard condition fails — should the device log, ignore, or transition to an error state?
- How would you document the state machine for a regulatory submission (e.g., as part of a design history file)?

---

## Q3: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The fundamental requirement is that the device must fail safe — it's better to show no reading or an explicit error than to show a plausible but wrong value. I'd approach this with a layered validation strategy.

At the lowest layer, I'd validate the raw data integrity: check the CRC or checksum on every read, and verify that the data length matches expectations. If the CRC fails, the entire sample is discarded — no partial data is used. Next, I'd apply plausibility checks at the signal level: is the value within the physiological range for this parameter? For example, a heart rate of 400 bpm or a temperature of 50°C is physically impossible. These limits should come from the clinical requirements, not be chosen arbitrarily.

The third layer is temporal validation: a single out-of-range sample might be noise, but a sustained pattern indicates a real problem. I'd use a combination of hysteresis and persistence checks — for instance, require N consecutive valid samples before updating the displayed value, or require M consecutive invalid samples before declaring the sensor failed. This prevents a single glitch from causing a false alarm while also preventing a genuinely failing sensor from being masked.

The key architectural decision is how the display layer handles invalid data. The display should never interpolate or "smooth over" missing data in a way that could mislead. Instead, it should show the last valid reading with a timestamp and a "data stale" indicator, or show an explicit "sensor error" state. In a medical context, the clinician needs to know the data is not current — a stale reading that looks current is dangerous. I'd also implement a separate error flag that propagates through the system so that any downstream logic (alarms, trend analysis) knows the data quality status.

Finally, I'd add a diagnostic counter for invalid reads — not just for debugging, but because a rising rate of CRC failures might indicate a hardware problem (e.g., a loose connection or EMI) that needs attention before it becomes a complete failure.

**Possible follow-ups:**
- How would you decide between showing the last valid reading with a "stale" indicator versus showing "no data" — what factors would influence that decision?
- How would you handle the case where the sensor recovers after a period of invalid data — should the device require a re-validation or re-calibration before resuming normal display?

---

## Q4: How would you approach debugging a firmware issue where a device's flash write operations occasionally corrupt data in an unrelated memory region, and the corruption is intermittent and only occurs when the device is under heavy load?

**Answer:** This is a classic symptom of a memory corruption bug — something is writing outside its intended bounds, and the flash write is either the victim or the trigger. The "under heavy load" clue suggests a timing-dependent or stack-depth-dependent issue. I'd approach this systematically.

First, I'd try to characterize the corruption: which memory region gets corrupted, what pattern of data appears there, and whether it correlates with a specific flash operation or a specific code path. I'd add a memory guard — fill the region around the suspected corruption area with a known pattern (like 0xAA) and check it periodically to catch the corruption as early as possible. This narrows down where the write is coming from.

The most likely culprits are: a buffer overflow in a driver (e.g., writing past the end of a DMA buffer), a stack overflow in a task or ISR, or a race condition where two tasks write to the same memory without synchronization. Given the flash write context, I'd also check whether the flash driver is using DMA and whether the DMA descriptor or buffer is properly aligned and sized. A common bug is a DMA transfer that writes more bytes than the buffer holds, especially if the length calculation has an off-by-one error that only manifests with certain data sizes.

I'd also look at the interrupt context. If the flash write is interrupt-driven and a higher-priority ISR fires during the write, does that ISR use any memory that overlaps? I'd use the debugger to set a hardware watchpoint on the corrupted address — this is the most direct approach. The watchpoint will trigger the moment the bad write happens, and the call stack will show exactly which code did it. If the corruption is truly intermittent, I'd leave the watchpoint running and let the system run until it triggers.

If the watchpoint approach isn't feasible, I'd use static analysis tools to look for buffer overflows and out-of-bounds array accesses, and I'd review the flash driver's error handling — does it check for write completion before releasing the buffer? Finally, I'd examine the linker script to confirm that the flash buffer region and the corrupted region aren't adjacent in a way that suggests a single overflow from one into the other.

**Possible follow-ups:**
- How would you distinguish between a stack overflow and a buffer overflow as the root cause?
- What role would you expect the RTOS to play in this scenario — could the scheduler be involved, and how would you check?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** The first thing I'd do is reframe the discussion away from "which is better" and toward "what are the actual requirements and constraints of this specific system." Both approaches are valid tools, and the right choice depends on the timing budget, the CPU load, the message rate, and the consequences of missing a message.

I'd start by asking the team to define the hard requirements: what is the worst-case latency for receiving a message? What is the maximum CPU utilization we can tolerate? What happens if a byte is missed — is it retried, or is it a safety issue? Once we have those numbers, we can evaluate both approaches against them.

For a polling approach, the key question is whether the polling interval can be made short enough to meet the latency requirement without starving other tasks. If the protocol has a low message rate and the CPU has spare cycles, polling can be perfectly adequate and has the advantage of being deterministic — you know exactly when the peripheral is checked, and there's no risk of interrupt priority inversion. The downside is that polling wastes CPU cycles and can miss short-duration events if the poll interval is too long.

For an interrupt-driven approach, the key questions are: what is the worst-case interrupt latency, and can the ISR complete within the required time without disabling interrupts too long? Interrupts are more responsive and efficient for low-duty-cycle traffic, but they introduce complexity — priority ordering, nested interrupts, and the risk of ISR overruns. In a real-time system with a 1 kHz control loop, an ISR that runs too long can cause jitter in the control loop, which is often worse than a slightly higher average latency.

I'd also suggest a hybrid approach as a third option: use interrupts to signal that data is available, but do the actual processing in a task context (e.g., using a semaphore or message queue). This gives the responsiveness of interrupts with the safety of deferred processing. The ISR stays short — just enough to move bytes into a buffer and signal the task — and the task does the protocol parsing with normal scheduling.

Rather than deciding by debate, I'd propose we prototype both approaches with the actual hardware and measure: worst-case latency, CPU utilization, and interrupt disable time. The data will settle the argument far better than opinion. I'd also make sure we document the decision and the rationale, so future engineers understand why we chose one approach over the other.

**Possible follow-ups:**
- How would you handle the situation where the measurements show that both approaches meet the requirements — what other factors would you consider?
- How would you ensure that the chosen approach is robust to future changes, such as a higher message rate or a new sensor added to the system?