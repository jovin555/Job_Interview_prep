# firmware — Day 27

## Q1: You're debugging a firmware issue where a device communicates with a sensor over I2C, and the sensor occasionally fails to acknowledge its address — but only after the device has been running for several hours. The bus works fine on a bench setup. How would you approach this?

**Answer:** I'd treat this as a classic "intermittent fault that appears only after extended operation" problem, which usually points to something degrading over time rather than a logic error. My first step would be to instrument the system to capture the failure context — I'd add logging around every I2C transaction that records the bus state, the number of consecutive NACKs, the time since power-on, and any other relevant system state (e.g., battery voltage, temperature, which other peripherals were active). The goal is to find a correlation: does the failure happen after a specific number of transactions, at a specific temperature, or when another peripheral is active?

In parallel, I'd look at the hardware side. A sensor that starts NACKing after hours of operation often has a marginal power supply — perhaps a decoupling capacitor that's undersized, or a voltage regulator that drifts as it heats up. I'd check the sensor's supply voltage and the I2C pull-up voltages with an oscilloscope during extended operation, looking for droop or noise that develops over time. I'd also verify that the pull-up resistors are correctly sized for the total bus capacitance, and that no other device on the bus is misbehaving and holding the line.

On the firmware side, I'd review the I2C error handling. A common issue is that after a NACK, the bus isn't properly recovered — the master may need to send a stop condition or toggle SCL to release a stuck slave. If the error path doesn't fully reset the bus state, the first NACK can cascade into persistent failures. I'd also check whether the sensor has a timeout or watchdog feature that might be triggering after extended operation, and whether the firmware is correctly handling the sensor's "busy" state.

Finally, I'd consider whether the issue is actually a clock-stretching problem that only manifests under certain timing conditions. If the sensor stretches the clock for longer than the master's timeout, the master may abort the transaction. This could be temperature-dependent if the sensor's internal oscillator drifts. I'd verify the I2C timing configuration against the sensor's worst-case specifications.

**Possible follow-ups:** How would you distinguish between a sensor-side fault and a bus-level fault (e.g., a marginal pull-up or a bad trace)? What changes would you make to the I2C error handler to make the system more resilient to transient NACKs?

---

## Q2: How would you approach designing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core principle here is that the firmware must be designed around the assumption that sensor data will be imperfect, and the system must have a clear, defensible policy for what constitutes "valid" data and what happens when data doesn't meet that bar. I'd structure the solution in layers.

First, at the data acquisition layer, I'd validate every reading before it enters the processing pipeline. This means checking the CRC or checksum, verifying the data is within the sensor's specified range, and checking for any protocol-level errors. I'd also look at the data's plausibility in context — for example, a sudden jump from 70 bpm to 180 bpm in one sample might be physiologically possible, but a jump to 500 bpm is not. This contextual validation requires understanding the clinical domain and the sensor's expected behavior.

Second, I'd implement a data quality state machine. Instead of treating each reading as independent, I'd track the recent history of readings and their validity. A single invalid reading might be flagged as "suspect" but not immediately acted upon; multiple consecutive invalid readings would escalate the state to "degraded" or "sensor failure." The key is that the clinician must never see a value that hasn't been validated, and the system must clearly indicate when it's operating in a degraded mode.

Third, I'd design the display and alarm logic around this state machine. If a reading is suspect, the system should either hold the last valid reading (with a clear "stale data" indicator) or display "no data" rather than showing a potentially false value. Alarms should only trigger based on validated data, and the system should have a defined behavior for what happens when data quality degrades — for example, an audible alert that the sensor signal is lost, rather than a false high/low alarm.

Finally, I'd ensure that all of this logic is testable and traceable. The validation rules, the state machine transitions, and the display behavior should be documented and covered by unit tests. In a medical device, this logic would also need to be reviewed against the risk management file — what are the failure modes, and how does the system mitigate each one?

**Possible follow-ups:** How would you handle a sensor that returns a valid CRC but a physiologically impossible value? How would you decide between holding the last valid reading versus displaying "no data"?

---

## Q3: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental issue is that a blocking flash erase in a lower-priority task can starve a higher-priority task if the scheduler can't preempt the blocking operation. In Zephyr, the flash driver typically blocks the calling thread for the duration of the erase, which means the 1 ms sensor task would miss its deadline. I'd approach this by removing the blocking operation from the critical path entirely.

The cleanest solution is to move the flash erase to a dedicated low-priority thread and use a non-blocking or asynchronous flash API if the hardware and driver support it. Some flash controllers have a "program/erase complete" interrupt, which allows the thread to initiate the erase and then sleep until the operation completes. This way, the flash thread is blocked, but the scheduler can still run the sensor task. If the flash driver doesn't support async operations, I'd consider using a separate thread with a lower priority than the sensor task — the sensor task would preempt the flash thread during the erase, and the flash thread would resume when the sensor task completes.

Another approach is to use a DMA-based flash controller if available, which offloads the actual memory transfer from the CPU. However, the erase operation itself is often a hardware state machine that still blocks the bus, so DMA may not help for erases specifically.

I'd also look at whether the flash erase can be deferred or batched. If the lower-priority task is logging data, I'd use a RAM buffer to accumulate log entries and only write to flash when a sufficient amount of data has been collected. This reduces the frequency of erases and allows them to be scheduled during times when the sensor task has slack. I'd also consider using a double-buffering scheme where one buffer is being written to flash while the other is accumulating new data.

Finally, I'd verify the actual timing budget. A 1 ms sensor task with, say, 200 µs of processing time leaves 800 µs of slack per period. If the flash erase blocks for 100 ms, the sensor task would miss roughly 100 cycles. The question is whether that's acceptable for the application — in a medical device, it likely isn't, so the design must guarantee that the sensor task always meets its deadline. I'd use Zephyr's priority-based preemptive scheduling to ensure the sensor task is always runnable, and I'd carefully size the flash thread's stack and priority to avoid priority inversion.

**Possible follow-ups:** How would you handle the case where the flash erase must happen at a specific time (e.g., to persist critical data immediately)? How would you verify that the sensor task never misses its deadline under worst-case conditions?

---

## Q4: You're reviewing a colleague's firmware code that implements a communication protocol using a single large interrupt service routine that handles both byte-level reception and complete message parsing. The ISR disables interrupts for the entire duration, which can be up to 300 µs for a long message. The system also has a 1 kHz control loop that must meet strict timing. How would you approach this situation?

**Answer:** This is a classic case of doing too much work in an interrupt context. The ISR is violating the fundamental principle that interrupt handlers should be as short as possible and should never perform blocking or time-consuming operations. A 300 µs ISR will cause jitter in the 1 kHz control loop — potentially missing its deadline entirely — and it also risks losing other interrupts that arrive during that window.

I'd start by quantifying the problem. I'd measure the actual worst-case ISR duration and the control loop's timing margin. If the control loop has, say, 500 µs of slack per period, a 300 µs ISR could push it over the edge. I'd also check whether the ISR is masking other critical interrupts, such as the timer interrupt that drives the control loop.

The fix is to restructure the design so that the ISR only handles byte-level reception — copying each byte into a ring buffer — and defers message parsing to a lower-priority context, such as a thread or a cooperative task. The ISR should be short enough that it doesn't meaningfully affect the control loop's timing. Message parsing, which involves state machines, validation, and potentially calling application callbacks, should happen in a thread that can be preempted by the control loop.

I'd also look at whether the ISR is using the right peripheral features. For example, if the UART supports DMA, I'd configure it to receive the entire message into a buffer without CPU intervention, and only generate an interrupt when the message is complete. This would reduce the ISR to a single "message received" event, which is nearly instantaneous. If DMA isn't available, I'd at least use the UART's FIFO to batch bytes and reduce interrupt frequency.

Finally, I'd work with the colleague to establish coding guidelines for ISR usage — maximum duration, no blocking calls, no function calls that aren't guaranteed to be short — and I'd suggest adding a runtime assertion or a debug counter that flags when an ISR exceeds a threshold duration. This turns a latent timing problem into a visible one during development.

**Possible follow-ups:** How would you decide between using DMA versus interrupt-driven reception for this protocol? How would you handle the case where the message parser needs to access shared data that the control loop also uses?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** My approach would be to reframe the discussion away from "polling vs. interrupts" as a binary choice and toward a structured analysis of the system's actual requirements. Both approaches have legitimate trade-offs, and the right answer depends on the specific timing constraints, the processor's load, and the consequences of missing a deadline.

First, I'd ask the team to define the protocol's hard requirements: What is the maximum latency between a byte arriving and it being processed? What is the minimum time between bytes (i.e., the fastest the sender can transmit)? What happens if a byte is missed — is there a retry mechanism, or is data lost? These requirements should come from the system specification, not from either engineer's preference.

Second, I'd ask for a quantitative analysis of both approaches. For polling, the team would need to calculate the worst-case polling interval and show that it's shorter than the minimum time between bytes. For interrupts, they'd need to analyze the worst-case interrupt latency — including time spent in other ISRs — and show that it's within the protocol's tolerance. I'd also ask them to consider the CPU load: polling at a high frequency can consume significant CPU time, while interrupts have overhead per event.

Third, I'd consider the broader system context. If the CPU is heavily loaded with other tasks, polling might be impractical. If the protocol is bursty — long periods of silence followed by rapid data — interrupts are more efficient. If the protocol has very tight timing, polling might be more deterministic because it avoids interrupt latency variability. I'd also look at whether the hardware supports DMA, which could be a third option that offloads the CPU entirely.

Finally, I'd suggest a decision framework: if the polling interval can be made short enough to meet the latency requirement with a comfortable margin, and the CPU load is acceptable, polling is simpler and easier to verify. If the protocol is event-driven with long idle periods, or if the CPU load from polling is too high, interrupts are the better choice. If neither approach clearly wins, I'd recommend prototyping both and measuring the actual worst-case behavior under realistic conditions.

The key is to make the decision based on data and requirements, not on either engineer's prior experience or preference. I'd also make sure both engineers feel heard — their concerns are valid, and the analysis should address them explicitly.

**Possible follow-ups:** How would you handle the situation where the two engineers continue to disagree after the analysis? What metrics would you use to evaluate the prototype implementations?