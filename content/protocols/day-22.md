# protocols — Day 22

## Q1: How would you approach designing a fail-safe mechanism for a UART-based communication link in a medical device where a sensor must never be left in an unknown state if the main controller resets or loses power mid-transaction?

**Answer:** The core concern here is that a partial or interrupted UART transaction could leave the sensor in an indeterminate configuration state. I'd approach this from three angles: protocol design, hardware state, and recovery strategy.

At the protocol level, I'd structure every transaction as atomic — meaning the sensor should only act on a complete, validated message. This means including a message length field, a checksum or CRC, and a message type identifier so the sensor can distinguish between "complete command received" and "partial garbage." The sensor firmware should be written to ignore any message that doesn't pass validation, rather than acting on partial data.

For the hardware state, I'd consider whether the sensor has a reset pin that the main controller can assert. If so, a hardware watchdog or a dedicated GPIO can force the sensor into a known idle state whenever the controller boots or detects a fault. If the sensor has non-volatile configuration memory, I'd also think about whether a partial write could corrupt it — in that case, a double-buffer or write-verify approach in the sensor firmware would be appropriate.

For recovery, I'd implement a handshake at the application layer: after controller reset, it sends a "sync" or "query status" message and waits for an acknowledgment before proceeding with normal operation. This ensures both sides agree on the current state before any critical commands are sent. I'd also consider whether the sensor should have its own timeout — if it hasn't received a valid message within a defined window, it should revert to a safe default state rather than holding whatever configuration it had.

**Possible follow-ups:** How would you handle the case where the sensor itself is the one that resets unexpectedly? What role would a hardware watchdog timer play in this design?

---

## Q2: You're debugging a system where an SPI bus with multiple slaves works reliably at 4 MHz but produces intermittent bit errors at 8 MHz, even though all devices are rated for 10 MHz. The PCB traces are short and well-matched. How would you approach this?

**Answer:** When a bus works at a lower frequency but fails at a higher one, and the devices are rated for the higher speed, the issue is almost always in the signal integrity domain rather than the protocol domain. I'd start by looking at the signal edges and timing margins.

First, I'd check the rise and fall times of the clock and data lines using an oscilloscope. At higher frequencies, if the rise time is too slow relative to the bit period, the signal may not reach valid logic thresholds before the sampling point. This can happen if the drive strength of the master's GPIO pins is too weak, or if there's excessive capacitance on the bus — even short traces can accumulate significant capacitance if there are multiple slave inputs, vias, or ESD protection devices.

Second, I'd examine the clock phase and setup/hold timing. At 8 MHz, the bit period is 125 ns. If the master's clock polarity or phase settings are marginal, or if there's clock skew between the master and a particular slave, the data might be sampled too close to the clock edge. I'd verify the actual timing against each slave's datasheet requirements, not just the master's configuration.

Third, I'd look at crosstalk and ground bounce. Even with short traces, if the SPI lines run parallel to other switching signals, or if there's a shared return path with high di/dt, the noise margin can be consumed at higher frequencies. I'd probe the signals referenced to the correct ground point and look for ringing or overshoot on the edges.

Finally, I'd consider whether the issue is specific to one slave or all slaves. If it's one slave, I'd suspect that device's input capacitance or its MISO drive characteristics. If it's all slaves, the problem is more likely in the master's output drive or the bus topology itself.

**Possible follow-ups:** How would you determine whether the issue is setup time, hold time, or signal integrity? What measurements would you take to isolate the root cause?

---

## Q3: How would you approach selecting between I2C and SPI for a new sensor interface in a battery-powered medical device where the sensor is on a separate PCB connected by a 15-centimeter flex cable, and the sensor must wake from sleep periodically to take a measurement?

**Answer:** This is a classic trade-off between bus complexity, power consumption, and cable robustness. I'd start by listing the requirements: the sensor needs to wake periodically, take a measurement, and transmit the data. The flex cable introduces capacitance and potential noise coupling, and the device is battery-powered, so every microamp matters.

I2C has the advantage of only needing two wires (SDA and SCL) plus ground, which reduces flex cable complexity and cost. It also has built-in addressing, so multiple devices can share the bus. However, I2C's open-drain architecture requires pull-up resistors, and the bus capacitance on a 15-centimeter flex cable can be significant — especially if the cable has any shielding or if the traces are wide. Higher capacitance means slower rise times, which limits the achievable clock speed or requires stronger pull-ups that consume more power. I'd need to calculate the total bus capacitance and verify it stays within the I2C specification.

SPI, on the other hand, uses push-pull drivers, which are more robust against capacitance and can operate at higher speeds. It also has lower power consumption during active communication because there are no pull-up resistors constantly sinking current. However, SPI typically requires four wires (MOSI, MISO, SCK, CS), which adds to the flex cable's cost and complexity. For a single sensor, the extra wires might be acceptable, but if the cable needs to flex repeatedly, more conductors mean more fatigue risk.

For a battery-powered device, the sleep current matters more than the active current in many cases. I2C's pull-up resistors draw current whenever the bus is idle at a high level — this is typically microamps, but it's continuous. SPI's push-pull drivers draw no current when idle. However, the sensor's own sleep current will likely dominate, so this may not be the deciding factor.

I'd also consider the wake-up mechanism. With I2C, the master can wake the sensor using an address match or a dedicated interrupt line. With SPI, the chip select line can serve as a wake signal. Both work, but I'd check the sensor's datasheet for its recommended wake-up sequence.

Ultimately, I'd lean toward I2C if the flex cable is short enough to keep bus capacitance manageable and the data rate requirement is modest (which it usually is for periodic sensor readings). I'd lean toward SPI if the cable is longer, if I need higher data rates, or if I want to avoid the continuous pull-up current. I'd also consider whether the sensor has an interrupt output that can wake the main controller, which would allow the bus to stay idle longer.

**Possible follow-ups:** How would you calculate the maximum allowable bus capacitance for the flex cable at your target I2C speed? What if the sensor only supports I2C — how would you mitigate the cable capacitance issue?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single CAN-FD bus for a medical device that carries both a safety-critical control message requiring delivery within 2 ms and high-volume telemetry data from multiple sensors. The engineer argues that CAN-FD's higher data rate in the data phase eliminates any bandwidth concerns. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging that CAN-FD does offer higher data throughput in the data phase, but I'd steer the discussion toward the distinction between bandwidth and determinism. The safety-critical message's 2 ms deadline isn't just about total bus throughput — it's about worst-case latency, which depends on arbitration, message priority, and the maximum time any lower-priority message can occupy the bus.

I'd guide the team to construct a worst-case timing analysis. This means calculating the maximum frame length for the highest-priority message, including the arbitration phase at the nominal bit rate and the data phase at the faster bit rate. Then, I'd calculate the blocking time — the longest time a lower-priority message can hold the bus before the safety-critical message can win arbitration. This includes the longest possible frame on the bus, plus any inter-frame spacing and error frames.

I'd also raise the question of whether the telemetry data can be segmented or prioritized. If the telemetry messages are long, they could block the bus for a significant time. Options include reducing the telemetry payload size, using shorter data phase bit rates for telemetry, or assigning the safety-critical message the highest priority so it always wins arbitration. But even with highest priority, the safety-critical message must wait for any in-progress frame to complete — so the worst-case blocking time is the longest frame on the bus.

I'd also ask the team to consider error handling. CAN-FD has error frames and retransmission, which can add latency. If the bus is heavily loaded, the probability of errors and retransmissions increases, which could push the worst-case latency beyond 2 ms. The team should analyze whether the bus utilization leaves enough margin for error recovery.

Finally, I'd suggest a practical validation approach: simulate or prototype the bus with the actual message set and measure worst-case latency under realistic conditions, including error injection. This would confirm whether the 2 ms deadline is met with margin.

**Possible follow-ups:** How would you calculate the worst-case blocking time for the safety-critical message? What bus utilization threshold would you consider acceptable for this system?

---

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** I'd approach this in three phases: immediate response, root-cause analysis, and process improvement.

In the immediate response, my priority is to understand the scope of the issue and communicate transparently with stakeholders. I'd work with the junior engineer to identify exactly what was implemented incorrectly — whether it's a protocol violation, a timing issue, or a misinterpretation of the specification. I'd then assess the impact: does this affect safety, functionality, or just compliance? Depending on the severity, I might need to escalate to management and the regulatory body to discuss the path forward.

For the root-cause analysis, I'd use a structured method like 5 Whys or a fishbone diagram to understand why the error wasn't caught earlier. Was the protocol specification ambiguous? Did the engineer lack access to the right reference documents? Were the test procedures inadequate? Was there a gap in the design review process? I'd be careful not to place blame on the individual — the goal is to find systemic weaknesses that allowed the error to slip through.

For process improvement, I'd look at where the verification and validation process failed. This might mean adding protocol conformance checks earlier in the development cycle, creating a checklist for design reviews that specifically covers communication protocol requirements, or implementing automated protocol testing that runs continuously during development rather than only at the end. I'd also consider whether the junior engineer needs additional training or mentorship on the specific protocol and on the regulatory requirements.

Finally, I'd use this as a coaching opportunity. I'd sit down with the junior engineer, review the error together, and help them understand not just what went wrong but how to prevent similar issues in the future. The goal is to turn a costly mistake into a learning experience that strengthens the team's overall capability.

**Possible follow-ups:** How would you balance the need to meet the regulatory deadline with the need to fix the issue properly? What changes would you make to the design review process to catch similar issues earlier?