# firmware — Day 17

## Q1: How would you approach designing a firmware architecture for a device that must support both deterministic real-time control (e.g., a 1 kHz motor control loop) and non-real-time tasks like configuration management and data logging, where the non-real-time tasks must never cause jitter in the control loop?

**Answer:** The core principle is strict temporal isolation between the real-time path and everything else. I would start by identifying the hard real-time requirements — in this case, the 1 kHz control loop — and treat that as the system's heartbeat. The control loop should run at the highest priority, either as an ISR driven by a hardware timer or as the highest-priority RTOS task with a dedicated stack.

For the non-real-time tasks, the key is to ensure they can never block or delay the control loop. This means:
- **No shared resources without priority inheritance or careful locking:** If the control loop needs to share data with logging or configuration tasks, use a lock-free mechanism like a single-writer/single-reader ring buffer, or a mutex with priority ceiling/inheritance so a lower-priority task holding the lock can't stall the control task indefinitely.
- **Deferred processing:** Any work that isn't time-critical — formatting log entries, writing to flash, parsing configuration — should be queued and processed in lower-priority tasks. The control loop should only do the minimum: read sensors, compute the control output, write to the actuator.
- **Careful interrupt budgeting:** If the control loop runs from a timer ISR, the ISR must be short. Any heavy computation should be moved to a task that's triggered by the ISR, not done inside it.
- **Stack sizing and memory allocation:** The control task's stack must be sized to avoid overflow, and it should avoid dynamic memory allocation entirely — allocate everything statically at build time.

I'd also add a monitoring mechanism: a task that tracks the control loop's worst-case execution time and flags if it ever approaches the 1 ms budget, so we catch jitter early in development rather than in the field.

**Possible follow-ups:**
- How would you handle a situation where the control loop occasionally needs to perform a long operation, like a sensor recalibration that takes 5 ms?
- What metrics would you collect to verify that the non-real-time tasks aren't introducing jitter?

---

## Q2: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** This pattern — correct at power-on, degrading over time — points to a thermal or power-related issue rather than a logic bug. I'd approach it systematically:

1. **Reproduce and characterize:** First, I'd confirm the failure is repeatable and measure the time-to-failure precisely. I'd also check whether the drift is gradual or sudden, and whether it correlates with any other observable event (e.g., battery voltage drop, regulator switching frequency change).

2. **Check the power supply first:** Since the device is battery-powered with a switching regulator, I'd probe the ADC's reference voltage and the regulator's output with an oscilloscope, both at power-on and after 30 minutes. Switching regulators can drift with temperature, and if the ADC reference is derived from the regulator output, that drift directly corrupts readings. I'd also check for ripple — a regulator that becomes unstable as it heats up can inject noise into the analog supply.

3. **Thermal effects:** Components heating up can change their characteristics. I'd use a thermal camera or thermocouple to check whether specific components (the regulator, the ADC, the sensor) are getting hot. A decoupling capacitor with poor temperature stability, or a solder joint that's marginal, can cause exactly this kind of intermittent behavior.

4. **Battery state:** If the battery is discharging, its internal resistance rises, which can cause the regulator's input voltage to sag under load. I'd check whether the regulator is dropping out of regulation as the battery depletes.

5. **Firmware side:** I'd also review the ADC configuration — is the sampling time long enough for the source impedance? Is the reference voltage configured correctly? But given the time-dependent nature, I'd focus on hardware first.

The key discipline is to measure, not guess. I'd instrument the system to log the raw ADC values, the regulator output, and the battery voltage over time, so I can correlate the failure with the actual root cause rather than chasing symptoms.

**Possible follow-ups:**
- What if the readings are fine on a bench supply but noisy on battery — how does that change your approach?
- How would you use the ADC's built-in self-test or a known reference channel to help isolate the problem?

---

## Q3: How would you approach implementing a firmware module that must handle graceful degradation when a critical sensor fails during operation, specifically for a device that monitors multiple physiological parameters where losing one parameter affects clinical decisions?

**Answer:** This is fundamentally a risk-management and user-interface design problem as much as a firmware problem. The firmware must ensure that the device never presents a false or misleading reading to the clinician, and that the loss of one parameter is communicated clearly and acted upon safely.

My approach would be:

1. **Define failure modes explicitly:** For each sensor, I'd enumerate the possible failure modes — no response, out-of-range values, CRC errors, values that change impossibly fast, values that are frozen — and define a detection strategy for each. This should be documented in the requirements and tied to the risk analysis (e.g., ISO 14971-style thinking, even if not formally required).

2. **Data validation at the driver level:** Each sensor driver should validate raw data before it enters the system. Invalid data should be flagged, not silently passed up. I'd use a status enum (e.g., `VALID`, `STALE`, `INVALID`, `SENSOR_ABSENT`) rather than a boolean, so the rest of the system knows *how* the data is bad, not just that it is.

3. **State machine for degradation:** The device should have a defined set of operational states — full operation, reduced operation (one parameter lost), and critical failure (too many parameters lost). Transitions between states should be explicit and logged. The clinical decision logic should be aware of which parameters are available.

4. **User interface:** The clinician must be informed immediately and unambiguously. This means a visual indicator (e.g., a specific icon or color), an audible alarm if appropriate, and a message that states which parameter is unavailable and what the device is doing about it. The device should never display a stale value as if it were current — it should show "no data" or a similar explicit indicator.

5. **Safe fallback behavior:** Depending on the clinical context, losing a parameter might mean the device should continue monitoring other parameters, or it might mean the device should enter a more conservative alarm threshold. This needs to be defined with clinical input, not just engineering judgment.

6. **Testing:** I'd build a fault-injection test harness that can simulate each failure mode and verify the device's response — both the internal state transitions and the user-facing behavior.

The key principle is that graceful degradation is not just about keeping the device running; it's about keeping the *clinical decision-making* safe and transparent.

**Possible follow-ups:**
- How would you handle a sensor that intermittently fails and recovers — how do you prevent the device from rapidly cycling between states?
- How would you involve clinicians in defining what "reduced operation" should look like?

---

## Q4: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 2 ms, but a lower-priority task occasionally needs to perform a flash write that can block for up to 50 ms. How would you approach this scheduling conflict?

**Answer:** This is a classic priority-inversion and blocking problem. The flash write is the fundamental issue — it's a long, uninterruptible operation that will stall the CPU or at least the calling task. The goal is to ensure the 2 ms sensor task never misses its deadline because of the flash write.

My approach would be:

1. **Move the flash write out of the critical path entirely.** The lower-priority task should not perform the flash write synchronously. Instead, it should prepare the data and hand it off to a dedicated flash-writer task or a driver that manages the write asynchronously.

2. **Use Zephyr's flash API with asynchronous semantics where possible.** Zephyr's flash driver API has a synchronous `flash_write()` call, but on many platforms you can use DMA or a background operation. If the hardware supports it, I'd configure the flash write to use DMA so the CPU isn't blocked. If not, I'd consider whether the flash write can be broken into smaller chunks with the sensor task running between them — though this depends on the flash part's page-erase behavior.

3. **If the write must block, use a dedicated lower-priority task and buffer the sensor data.** The sensor task writes to a ring buffer (which is fast and non-blocking), and the flash-writer task drains the buffer and writes to flash. The sensor task's 2 ms deadline is met because it never waits on the flash. The risk is buffer overflow if the sensor produces data faster than the flash can drain it — so I'd size the buffer based on the worst-case flash write time and sensor data rate, and I'd add a mechanism to drop or compress data if the buffer fills (with a clear indication that data was lost).

4. **Consider interrupt priority and preemption.** If the sensor task is truly time-critical, I might consider running the sensor read from a high-priority interrupt or a very high-priority thread that can preempt the flash write. On many MCUs, the flash controller will stall the CPU during a write, so this may not help — but if the flash write is on a separate bus or can be paused, it might.

5. **Verify with timing analysis.** I'd measure the worst-case latency of the sensor task under load, including the flash-write scenario, and verify it against the 2 ms budget. I'd also check whether the flash write affects interrupt latency — on some parts, the flash controller blocks instruction fetch, which can delay ISR entry.

The key design principle is to decouple the time-critical path from the long-blocking operation, and to make the buffering and data-loss behavior explicit and observable.

**Possible follow-ups:**
- What if the sensor data rate is so high that you can't buffer enough data for the worst-case flash write?
- How would you handle the case where the flash write itself fails and needs to be retried?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** This is a classic design trade-off, and the right answer depends on the specific protocol and the team's context. My role as the lead is to facilitate a decision based on evidence, not to impose my preference.

First, I'd ask both engineers to articulate the concrete requirements that matter for this protocol: How many states and transitions are there? How likely is the protocol to change? Who will maintain this code long-term? What are the failure modes we're most worried about — missing a transition, adding a new state, or debugging a runtime issue?

Then I'd frame the trade-off honestly:
- **State machine (explicit switch-case or nested ifs):** More readable for a small-to-medium number of states. Easier to trace through with a debugger. But it can become unwieldy as states grow, and adding a new state often requires touching multiple places.
- **Table-driven:** The transition table is data, not code, which makes it easy to add states or transitions without modifying logic. It's also easier to validate — you can write a test that walks the table and checks for invalid transitions. The downside is that it's more abstract; debugging a runtime issue requires understanding the table format, and complex actions (e.g., "on entering this state, start a timer and send a specific message") can be awkward to express in a table.

I'd also suggest a middle path: a hybrid where the core state machine is table-driven for the transition logic, but the actions associated with each state are implemented as functions referenced by the table. This gives you the maintainability of the table with the debuggability of explicit code.

Finally, I'd propose a concrete decision process: have each engineer prototype a small but representative portion of the protocol using their preferred approach, then review both side by side. The team evaluates them against criteria we agree on upfront — readability, testability, ease of adding a new state, and debugging experience. This turns a philosophical debate into an evidence-based decision.

The key is to make the decision about the problem, not about personal preference, and to ensure whoever "loses" the debate still feels their concerns were heard and addressed.

**Possible follow-ups:**
- What if the two engineers continue to disagree after seeing the prototypes — how do you break the tie?
- How would you ensure the chosen approach is documented and enforced so future contributors follow it consistently?