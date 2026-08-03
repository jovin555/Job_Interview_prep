# firmware — Day 13

## Q1: How would you approach designing a firmware architecture for a device that must support multiple sensor types (e.g., digital, analog, and resistive) on the same PCB, where each sensor has different sampling rate requirements and accuracy needs?

**Answer:** I'd start by separating the sensor abstraction from the hardware specifics. Each sensor type would get a driver layer that exposes a common interface — something like `init()`, `read()`, `self_test()`, and `set_power_state()` — so the application layer doesn't care whether it's talking to an I2C digital sensor, an ADC channel, or a resistive divider. Behind that interface, each driver handles its own specifics: the digital sensor might use DMA-triggered I2C reads, the analog sensor would need ADC configuration with proper settling time and possibly oversampling, and the resistive sensor would require excitation control and ratiometric measurement.

For the different sampling rates, I'd assign each sensor a dedicated thread or use a timer-driven scheduler that triggers reads at the required intervals. The key is to avoid a monolithic "read everything" loop that forces all sensors to the slowest common rate. Instead, each sensor's driver would be called on its own schedule, with data placed into a per-sensor buffer or published to a central data hub.

Accuracy considerations would drive the analog front-end design: proper anti-aliasing filters, correct ADC reference selection, and calibration routines. For the resistive sensor, I'd use a ratiometric measurement with the ADC reference tied to the excitation voltage to eliminate supply variation errors. For the digital sensor, I'd verify the timing requirements in the datasheet — particularly settling times after configuration changes — and ensure the driver respects them.

The architecture would also include a self-test path for each sensor type, since medical devices typically require periodic verification that sensors are functioning within specification. This might be a known reference voltage for the ADC channel, a loopback register read for the digital sensor, or a known resistance for the resistive channel.

**Possible follow-ups:** How would you handle sensor calibration data storage and retrieval? How would you ensure that a slow sensor (e.g., one requiring 100 ms settling) doesn't block reads of a fast sensor?

---

## Q2: You're debugging a firmware issue where a device's real-time clock (RTC) drifts significantly when the device is in low-power mode, but is accurate when running normally. The device uses an external 32.768 kHz crystal. How would you approach this?

**Answer:** This is a classic symptom of the crystal oscillator running in an unstable or marginal condition during low-power mode. The first thing I'd check is whether the low-power mode changes the oscillator configuration — some MCUs switch to a different oscillator path or reduce the drive level in sleep modes. I'd review the RTC and oscillator configuration registers to confirm the same crystal and drive settings are active in both modes.

Next, I'd look at the crystal's load capacitance. If the oscillator is running marginally, it can still produce a clock signal but with frequency error. In low-power mode, if the MCU reduces the oscillator drive current, the crystal might not be driven hard enough to maintain its specified frequency. I'd check the datasheet for the recommended drive level and compare it against what's configured.

I'd also examine the PCB layout and component values — the load capacitors and any series resistor. If the crystal is operating outside its specified load capacitance range, the frequency will shift. This could be verified by measuring the actual oscillation frequency with a frequency counter or by using the MCU's clock output feature to bring the RTC clock out to a pin for measurement.

Another angle is temperature. If the device is in low-power mode for extended periods, the thermal environment might differ from normal operation. A crystal's frequency vs. temperature curve is parabolic, so if the device is running cooler or warmer in low-power mode, drift would appear. I'd check whether the drift is consistent or varies with ambient conditions.

Finally, I'd verify the firmware isn't doing something unexpected — like periodically waking and briefly running at a different clock speed, which could cause the RTC to accumulate error if the firmware is compensating for the wrong oscillator frequency. I'd add a diagnostic that logs the RTC value against a known reference (like a timer running from the main oscillator) to characterize when the drift occurs.

**Possible follow-ups:** How would you determine whether the issue is hardware or firmware? What if the drift only appears after the device has been in low-power mode for several hours?

---

## Q3: How would you approach implementing a firmware module that must handle a burst of data from a sensor at high speed (e.g., 1000 samples at 10 kHz) while the rest of the system is running normal operations, without dropping any samples?

**Answer:** The core challenge is ensuring that no samples are lost during the burst while other tasks continue. I'd use a double-buffering approach: the sensor writes into one buffer while the application processes the other. The sensor side would be interrupt-driven or DMA-based, so the CPU isn't spending cycles polling for each sample.

For a 10 kHz sampling rate, that's 100 µs between samples. If the sensor communicates over SPI or I2C, I'd use DMA to transfer each sample into the buffer without CPU intervention. The DMA completion interrupt would simply toggle which buffer is active and signal the processing task. This gives the CPU the full 100 µs between samples to handle other work.

The buffer sizing needs to account for worst-case processing latency. If the processing task can be delayed by up to 50 ms due to higher-priority work, then at 10 kHz that's 500 samples that could accumulate. I'd size each buffer to handle this worst case, plus margin. The key is to measure or estimate the maximum latency the processing task can experience and size accordingly.

I'd also consider using a circular buffer with a producer-consumer pattern rather than strict double-buffering, since it handles variable processing delays more gracefully. The producer (DMA or ISR) writes samples with a write index, and the consumer reads with a read index. If the consumer falls behind, the circular buffer provides a clear indication of overflow, which is better than silently dropping data.

For the processing side, I'd ensure the consumer task is designed to process samples in bulk rather than one at a time — this reduces context-switch overhead and lets the CPU stay ahead of the producer. If the processing involves any non-trivial computation, I'd consider whether it can be done incrementally (e.g., computing a running average) rather than requiring all samples to be stored before processing begins.

Finally, I'd add a diagnostic counter for dropped samples. Even with careful design, it's important to know if the system is losing data, especially in a medical device where data integrity is critical. The counter would be logged or exposed for monitoring.

**Possible follow-ups:** How would you choose between DMA and interrupt-driven transfer for this scenario? What if the sensor data needs to be processed in real-time (e.g., for a feedback loop) rather than just stored?

---

## Q4: A junior engineer on your team has implemented a firmware module that uses a timer interrupt to generate a 1 ms tick for a software timer system. The module works correctly in testing, but you notice that the ISR disables interrupts for the entire duration of the ISR, which includes calling a callback function that can take up to 200 µs to execute. How would you guide them?

**Answer:** I'd start by acknowledging that the module works, but explain why the current approach is problematic. Disabling interrupts for 200 µs means that any other interrupt — including potentially critical ones like a UART receive or a sensor data-ready signal — will be delayed. In a medical device, this could mean missed sensor samples or delayed response to a fault condition.

The fundamental issue is that the ISR is doing too much work. A timer ISR should be as short as possible — typically just setting a flag, incrementing a counter, or signaling a semaphore. The actual callback execution should happen in thread context, not in interrupt context. I'd guide them toward a deferred processing pattern: the ISR sets a flag or posts to a queue, and a lower-priority thread handles the callback execution.

I'd also point out that if the callback takes up to 200 µs, it's likely doing something that shouldn't be in an ISR at all — perhaps I/O operations, complex calculations, or even blocking calls. These belong in thread context where they can be preempted by more critical work if needed.

If the timer tick needs to be precise, I'd suggest measuring the actual jitter introduced by the current approach. With interrupts disabled for 200 µs, the tick timing will vary depending on when the callback runs relative to the timer interrupt. This could affect any time-sensitive operations in the system.

I'd also discuss the alternative of using the RTOS tick directly if they're using Zephyr — the kernel's tick handling is already optimized for this, and software timers can be created with `k_timer` without needing a custom ISR. This would eliminate the problem entirely and reduce maintenance burden.

Finally, I'd emphasize the importance of measuring interrupt latency in the system. Just because it works in testing doesn't mean it will work when other interrupts are active. A simple test would be to enable all system interrupts and measure the maximum latency of a known interrupt source.

**Possible follow-ups:** How would you measure the actual interrupt latency impact? What if the callback must run at a precise time relative to the timer tick?

---

## Q5: How would you approach designing a firmware module that must handle graceful degradation when a critical sensor fails during operation, specifically for a device that monitors multiple physiological parameters where losing one parameter affects clinical decisions?

**Answer:** I'd start by defining what "graceful degradation" means for this specific device, in collaboration with clinical input. For each sensor, there's a difference between "data is temporarily unavailable" and "data is known to be invalid." The firmware needs to distinguish between these and communicate the distinction clearly to the user.

The architecture would have three layers: detection, response, and communication. Detection involves monitoring each sensor for failure modes — no response on the bus, out-of-range values, values that change impossibly fast, or values that stay frozen for too long. I'd implement a health status per sensor that tracks these conditions and assigns a confidence level.

The response layer determines what the device does when a sensor fails. For a non-critical sensor, the device might continue full operation with a warning. For a critical sensor, the device might need to switch to a reduced-functionality mode — for example, if a secondary parameter is lost, the device continues monitoring the primary parameters but clearly indicates the missing data. The response should be defined in a failure mode matrix that considers which combinations of sensor failures are safe to continue with.

The communication layer ensures the user and any connected systems know the device's state. This means a clear visual indicator (e.g., a warning icon or color change), an audible alert if appropriate, and a structured message on any connected interface (e.g., a status word that indicates which parameters are valid). The key is that the user should never have to guess whether a displayed value is trustworthy.

I'd also think about recovery. The firmware should periodically attempt to re-establish communication with the failed sensor — perhaps with a backoff strategy to avoid hammering a bus that might be electrically faulted. When the sensor recovers, the device should verify data validity before resuming normal operation, and the user should be informed of the recovery.

For implementation, I'd use a state machine per sensor with states like `healthy`, `suspect`, `failed`, and `recovering`. Transitions between states would be based on the detection criteria, and each state would have defined behavior for data display, alerts, and system operation. This makes the degradation logic explicit and testable.

Finally, I'd ensure the degradation logic itself is tested — not just the happy path. This means fault injection testing where each sensor is made to fail in various ways, and the device's response is verified against the failure mode matrix.

**Possible follow-ups:** How would you handle the case where a sensor intermittently fails and recovers — would you require a minimum stable period before declaring it healthy again? How would you prioritize which parameters to continue monitoring if multiple sensors fail simultaneously?