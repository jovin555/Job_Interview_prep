# firmware — Day 32

## Q1: How would you approach designing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core principle here is that the firmware must be the last line of defense against a false reading reaching the clinician — the sensor can fail in ways that are undetectable at the hardware level, so the software needs a layered validation strategy.

First, I'd establish a clear data validation pipeline with distinct stages. At the lowest level, I'd validate the raw data integrity — checking CRC or checksum on every frame, verifying that the data length matches expectations, and confirming the sensor's status/error registers are clean. If any of these fail, the sample is discarded immediately and counted as a communication error.

Next, I'd apply plausibility checks at the application level. This includes range checking against both hard limits (from the sensor datasheet) and soft limits (from the patient population and clinical context). For example, a pressure reading of −5 mmHg might be physically impossible, while a reading of 300 mmHg might be possible but clinically alarming. I'd also look at rate-of-change limits — a physiological parameter shouldn't jump by an implausible amount between consecutive samples unless there's a real event.

For handling invalid samples, I'd use a combination of short-term and long-term strategies. In the short term, I'd hold the last valid reading and flag it as "stale" if no valid data arrives within a timeout window. For longer outages, I'd transition the device to a degraded mode where the display clearly indicates the parameter is unavailable rather than showing a potentially incorrect value. The key is that the clinician must never see a number that looks valid but isn't — it's better to show "—" or "sensor error" than a wrong value.

I'd also implement a voting or redundancy scheme if the system has multiple sensors measuring the same parameter. For instance, if two sensors disagree beyond a tolerance, the firmware should flag the discrepancy rather than blindly averaging them.

Finally, all invalid-data events should be logged with timestamps for post-event analysis. This supports both debugging and regulatory requirements — if there's a pattern of failures, the log helps identify whether it's a sensor degradation issue, an EMI problem, or a firmware bug.

**Possible follow-ups:**
- How would you decide between holding the last valid reading versus displaying "no data" when a sample is invalid?
- How would you handle a sensor that returns valid-looking but systematically biased data (e.g., a slow drift that stays within range)?

---

## Q2: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** This symptom pattern — correct at power-on, then gradual degradation — points me toward thermal effects, power supply stability, or a firmware state issue rather than a hard failure. I'd approach this systematically.

First, I'd characterize the problem precisely. I'd log the ADC readings, the raw counts, the reference voltage, and the battery voltage over time to see if the drift is monotonic, periodic, or random. I'd also check whether the noise correlates with the switching regulator's operation — for example, whether it gets worse when the battery voltage drops below a certain threshold.

The most likely culprits I'd investigate in parallel:

1. **Thermal drift in the ADC reference or the sensor itself.** The switching regulator and other components heat up over time, which can shift the reference voltage. I'd check the ADC's datasheet for the temperature coefficient of the internal reference and compare it against the observed drift. If the internal reference is marginal, I'd consider switching to an external precision reference.

2. **Power supply noise coupling into the ADC input.** As the battery discharges, the switching regulator's duty cycle changes, which can alter the ripple characteristics. I'd use an oscilloscope to measure the supply rail and the ADC input pin at various battery voltages, looking for noise that correlates with the ADC readings. I'd also check the ADC's power supply rejection ratio (PSRR) specification.

3. **Ground bounce or layout issues.** If the ADC's analog ground and the switching regulator's ground share a return path, the regulator's switching current can create voltage offsets that grow as the load changes. This is a hardware issue, but the firmware can sometimes mitigate it by sampling at a different point in the switching cycle.

4. **Firmware state issues.** I'd check whether the ADC is being configured identically at startup and after 30 minutes. For example, if a low-power mode or clock change alters the ADC's sampling time or reference selection, that could explain the drift. I'd also verify that no other peripheral is interfering with the ADC's power or clock.

I'd also consider whether the battery voltage itself is the issue. If the ADC is using the battery as its reference (which is sometimes done to save cost), the readings will drift as the battery discharges. The fix would be to use a stable reference or to compensate in firmware by measuring the battery voltage and applying a correction factor.

For the firmware-side mitigation, I'd implement periodic self-calibration — for example, measuring an internal bandgap reference or a known voltage and applying a correction factor to subsequent readings. This can compensate for both thermal drift and supply variation.

**Possible follow-ups:**
- How would you distinguish between a reference voltage drift and a sensor drift in your debugging?
- If the root cause turns out to be a hardware layout issue, how would you work with the hardware team to address it while also providing a firmware workaround?

---

## Q3: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** I want to be careful here because this question overlaps with one I've already addressed, but I'll take a different angle — focusing on the architectural patterns and the distinction between data validation and clinical decision support.

The fundamental design principle is that the firmware should separate "measurement" from "presentation." The measurement layer acquires raw data and applies validation rules. The presentation layer decides what to display based on the validated data and the device's current state. This separation ensures that a sensor glitch doesn't propagate directly to the user interface.

For the validation layer, I'd implement a three-tier approach:

**Tier 1 — Frame-level validation:** Every sensor reading comes with some form of integrity check (CRC, checksum, or protocol-level acknowledgment). I'd validate this before the data enters the processing pipeline. Failed frames are dropped and counted.

**Tier 2 — Sample-level validation:** Each individual reading is checked against:
- Absolute range limits (from the sensor datasheet and clinical requirements)
- Rate-of-change limits (a physiological signal can't change faster than physics allows)
- Cross-channel consistency (if multiple parameters are related, they should move together)

**Tier 3 — Trend-level validation:** Over a sliding window, I'd look for patterns that indicate sensor degradation — for example, increasing variance, repeated CRC failures, or a slow drift toward a range boundary. This catches failures that individual samples don't reveal.

For the presentation layer, I'd define explicit display states:
- **Valid:** The reading passes all validation and is current.
- **Stale:** The last valid reading is older than a threshold, but the sensor is still communicating.
- **Invalid:** The sensor is returning data that fails validation.
- **Absent:** The sensor is not communicating at all.

Each state has a defined display behavior. For "stale," I'd show the last valid value with a timestamp and a visual indicator that it's not current. For "invalid" and "absent," I'd show a clear error message rather than a number. The key is that the clinician always knows the confidence level of what they're seeing.

I'd also implement a "sensor health" metric that tracks the ratio of valid to invalid samples over time. This can trigger a maintenance alert before the sensor completely fails, which is especially important in a medical device where unexpected downtime has clinical consequences.

**Possible follow-ups:**
- How would you handle a sensor that returns valid-looking data that is systematically wrong (e.g., a calibration drift)?
- How would you test this validation logic to ensure it handles edge cases correctly?

---

## Q4: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** This is a classic engineering trade-off, and the right answer depends on the specific requirements of the system. My role as the lead is to guide the team toward a data-driven decision rather than letting it become a matter of personal preference.

First, I'd establish the system's actual requirements. What are the timing constraints? What's the maximum acceptable latency for receiving a message? What's the worst-case CPU load from other tasks? What's the message rate and size? These numbers should come from the system requirements, not from either engineer's preference.

Next, I'd have both engineers quantify their approaches against these requirements. For the polling approach, I'd ask: What's the worst-case latency if the CPU is busy with a higher-priority task when a message arrives? How much CPU time is wasted on polling when no message is present? For the interrupt approach, I'd ask: What's the worst-case interrupt latency? How long can interrupts be disabled by other parts of the system? What's the risk of interrupt priority inversion?

I'd also consider the system's overall architecture. If the device is a simple sensor node with a single communication port and minimal other activity, polling might be perfectly adequate and simpler to verify. If it's a multi-interface device with real-time control loops, interrupts (or DMA) might be necessary to ensure the communication doesn't starve other functions.

A key consideration is the "predictability" argument. Polling is predictable in the sense that the timing is deterministic — you know exactly when the communication is checked. But it's not predictable in the sense of responsiveness — you can't guarantee when a message will be processed. Interrupts provide responsiveness but introduce timing variability. The question is which property matters more for the system's requirements.

I'd also look at the broader system context. If the device is a medical monitor that must respond to a clinician's command within a defined time, that's a hard requirement that might favor interrupts. If the communication is for configuration updates that can tolerate some latency, polling might be fine.

Finally, I'd ask both engineers to consider the maintainability and testability of their approaches. A polling loop is easier to trace and debug. An interrupt-driven approach requires careful handling of shared data and reentrancy. If the team is more experienced with one pattern, that's a factor — but not the deciding one.

My goal is to get the team to agree on the evaluation criteria first, then evaluate both approaches against those criteria. If the requirements genuinely allow either approach, I'd lean toward the simpler one (polling) and add a note in the design document about when it might need to be revisited.

**Possible follow-ups:**
- What if the requirements genuinely support both approaches — how would you make the final call?
- How would you handle a situation where one engineer refuses to accept the decision?

---

## Q5: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** This is a fundamental RTOS scheduling problem — a high-priority periodic task being blocked by a lower-priority task's long-running operation. The first thing to recognize is that this isn't really a priority inversion problem in the classic sense; it's a blocking problem. The flash erase blocks the CPU (or at least the bus), so even the highest-priority task can't run.

I'd approach this with several layers of mitigation:

**Layer 1 — Eliminate the blocking at the source.** The flash erase is blocking because the CPU is waiting for the erase to complete. Many flash controllers support a "program/erase suspend" feature that allows the CPU to pause the erase operation, service an interrupt, and then resume. If the flash device supports this, I'd use it — the sensor task's interrupt can suspend the erase, read the sensor, and then let the erase continue. This is the cleanest solution because it doesn't require any architectural changes.

**Layer 2 — Move the flash operation off the critical path.** If the flash controller doesn't support suspend, I'd look at whether the erase can be deferred or broken into smaller chunks. Some flash devices allow partial-page or partial-sector erases, which would reduce the blocking time. Alternatively, I could use a background task to perform the erase in small steps, checking between each step whether the sensor task needs to run.

**Layer 3 — Use DMA or a dedicated flash controller.** If the MCU has a DMA controller that can handle the flash erase without CPU involvement, I'd offload the operation entirely. The CPU would only need to set up the DMA transfer and then handle the completion interrupt. This frees the CPU to service the sensor task during the erase.

**Layer 4 — Buffer the sensor data.** If none of the above are possible, I'd add a buffer between the sensor and the processing task. The sensor task would write to a DMA buffer or a hardware FIFO, and the processing task would read from it when the CPU is available. The buffer needs to be large enough to hold 100 ms of data (100 samples at 1 kHz), which is usually feasible. The key is that the sensor data isn't lost — it's just delayed.

**Layer 5 — Reconsider the scheduling.** If the flash erase is truly unavoidable and blocking, I'd look at whether the sensor task's deadline is hard or soft. If it's hard (e.g., the sensor data is used for a control loop), then the flash erase must be scheduled around the sensor task's timing. If it's soft (e.g., the data is for logging), then a brief delay might be acceptable.

I'd also consider using Zephyr's threaded interrupts or the `CONFIG_ISR_OFFLOAD` feature to handle the sensor read in an interrupt context rather than a task context. This would bypass the scheduler entirely and ensure the sensor is read even if the scheduler is blocked.

Finally, I'd instrument the system to measure the actual worst-case blocking time and verify that the chosen solution meets the timing requirements. This isn't a "set it and forget it" decision — I'd want to see the actual behavior under load.

**Possible follow-ups:**
- How would you decide between buffering the sensor data versus suspending the flash erase?
- What if the flash erase is a firmware update that must not be interrupted — how would that change your approach?