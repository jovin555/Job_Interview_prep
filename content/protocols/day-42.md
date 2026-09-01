# protocols — Day 42

## Q1: How would you approach designing a clock stretching strategy for an I2C bus in a medical sensor device where one slave device needs more time to process a read request than the master's timeout allows?

**Answer:** The first step is to understand the actual timing requirements of the slave — how long it needs to stretch the clock, whether it stretches only during certain operations (e.g., after a write to a configuration register, or during an internal ADC conversion), and whether the stretch duration is consistent or varies with operating conditions like temperature or supply voltage. I'd check the slave datasheet for the maximum clock stretch specification and compare it against the master's timeout configuration.

If the slave's stretch requirement exceeds the master's timeout, I'd look at several options. One is to see if the master's I2C peripheral has a configurable timeout that can be extended — many microcontrollers allow this, though sometimes at the cost of reduced error-detection capability. Another is to restructure the communication sequence: instead of issuing a read immediately after the write that triggers the internal processing, the master could poll a status register until the slave indicates data is ready. This avoids relying on clock stretching altogether. A third option is to reduce the bus speed, which gives the slave more time relative to the bit clock, though this doesn't help if the stretch itself exceeds the master's absolute timeout.

For a medical device, I'd also think about failure behavior. If the slave stretches beyond the timeout, the master should treat it as a bus error, release the bus, and retry with a bounded number of attempts. The system should log the event and, if it persists, transition to a safe state — for example, alerting the user or switching to a redundant measurement path. I'd also verify the timeout behavior during design verification testing, since clock stretching interactions can be subtle and may only appear under specific timing conditions.

**Possible follow-ups:** How would you determine whether to fix this in firmware versus changing the hardware design? What are the safety implications if the slave never releases the clock line?

---

## Q2: How would you approach selecting between USB 2.0 interrupt transfers and bulk transfers for a medical device that streams real-time sensor data to a host computer, with a requirement that no data be lost?

**Answer:** The key distinction is that interrupt transfers guarantee a maximum latency — the host polls the endpoint at a configured interval — but they don't guarantee bandwidth. Bulk transfers guarantee delivery through error checking and retransmission, but they have no latency guarantee and can be starved by other bus traffic. For a medical device with a no-data-loss requirement, I'd first quantify the actual data rate and the acceptable latency.

If the sensor data rate is modest — say, a few kilobytes per second — interrupt transfers with a short polling interval can work well, because the host will poll frequently enough that the endpoint buffer never overflows. The no-data-loss requirement is satisfied as long as the device firmware ensures the endpoint buffer is serviced before the next poll, and the host reads the data promptly. However, if the data rate is high or bursty, interrupt transfers become risky because the host's polling interval may not keep up with the device's production rate.

Bulk transfers, by contrast, provide error-free delivery through CRC checking and retransmission, which is attractive for a medical device. The trade-off is latency: if the host is busy with other bulk traffic, the sensor data could be delayed. For real-time monitoring, that delay might be unacceptable. A common approach is to use both: a bulk endpoint for guaranteed delivery of logged data, and an interrupt endpoint for time-sensitive status or alarm information. The firmware would need to manage the buffering and prioritization between the two.

I'd also consider whether the "no data lost" requirement applies to the streaming path or to the overall record. If the host application can tolerate a small gap in the real-time stream as long as the data is later recovered from a local log, then a combination of interrupt streaming plus bulk transfer of the complete log could satisfy both real-time and completeness requirements.

**Possible follow-ups:** How would you determine the maximum polling interval for an interrupt endpoint given your data rate? What happens if the host is a hub with multiple devices sharing the bus?

---

## Q3: In a CAN-FD network for a medical device, you need to ensure that a high-priority safety-critical message is never delayed by more than 500 microseconds. How would you approach guaranteeing this timing requirement?

**Answer:** I'd start by building a worst-case timing model of the entire network. This includes the arbitration phase bit rate, the data phase bit rate, the maximum message lengths (including stuff bits), and the number and priority of all other messages on the bus. The worst-case latency for a high-priority message is the time it must wait for the longest lower-priority message currently in transmission, plus the arbitration time, plus the transmission time of the message itself.

The first thing I'd check is whether the 500-microsecond budget is even feasible given the bus configuration. For example, if the arbitration phase is at 500 kbit/s and a lower-priority message can be up to 112 bits in the worst case (including stuff bits), that's over 200 microseconds just for one message to finish. If there's a possibility of a second lower-priority message winning arbitration before the high-priority one, the delay grows. I'd need to ensure that the high-priority message has the lowest CAN ID on the bus, so it always wins arbitration once the bus is free.

Beyond priority, I'd look at the message scheduling. If the high-priority message is periodic, I'd verify that its period plus worst-case jitter stays within the 500-microsecond window. I'd also consider whether the data phase bit rate can be increased to reduce transmission time — CAN-FD allows a faster data phase, which helps. Another option is to reduce the payload size of lower-priority messages or increase their periods to reduce bus utilization.

For verification, I'd use a logic analyzer or CAN bus analyzer to measure actual message latencies under worst-case conditions — all nodes transmitting at maximum rate, with the lower-priority messages deliberately flooding the bus. I'd also simulate the network using a CAN timing analysis tool to confirm the worst-case calculation. For a medical device, this analysis would be documented as part of the design verification evidence, showing that the timing requirement is met with margin.

**Possible follow-ups:** How would you handle the case where a lower-priority node is in an error state and continuously retransmitting? What margin would you consider acceptable for the 500-microsecond requirement?

---

## Q4: How would you approach calculating pull-up resistor values for an I2C bus that must support both standard-mode (100 kHz) and fast-mode (400 kHz) operation, with multiple devices on the bus?

**Answer:** The pull-up resistor value is bounded by two constraints: the minimum resistance is set by the maximum allowable sink current of the devices on the bus (typically 3 mA for standard-mode and fast-mode, per the I2C specification), and the maximum resistance is set by the required rise time for the bus speed. For fast-mode, the maximum rise time is 300 nanoseconds; for standard-mode, it's 1000 nanoseconds.

The rise time is determined by the RC time constant of the pull-up resistor and the total bus capacitance. So the first step is to estimate the total bus capacitance — the sum of each device's pin capacitance, the trace capacitance, and any connector or cable capacitance. A typical estimate might be 10–20 pF per device plus trace capacitance. Once I have the total capacitance, I can calculate the maximum pull-up resistance for each mode: for fast-mode, R_max ≈ 300 ns / (0.8473 × C_total), accounting for the 30%–70% rise time definition.

The minimum resistance is set by the sink current: R_min = V_CC / I_sink_max, where I_sink_max is typically 3 mA. For a 3.3 V bus, that gives R_min ≈ 1.1 kΩ. The chosen value must be between R_min and the smaller of the two R_max values (fast-mode will give the tighter constraint). I'd also consider the supply voltage — if the bus is 5 V, the minimum resistance is higher.

In practice, I'd pick a standard value that gives margin on both sides. For example, with a total capacitance of 100 pF and a 3.3 V supply, the fast-mode R_max would be around 3.5 kΩ, so a 2.2 kΩ or 2.7 kΩ resistor would be a reasonable choice. I'd also consider whether the bus needs to operate at both speeds with the same pull-ups — it does, so the fast-mode constraint governs. Finally, I'd verify the actual rise time on the bench with an oscilloscope, measuring at the farthest device on the bus, since capacitance estimates can be off.

**Possible follow-ups:** How would the calculation change if the bus operates at 1.8 V instead of 3.3 V? What if one device on the bus has a much higher pin capacitance than the others?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single RS-485 bus for a medical device system with 24 sensor nodes distributed along a 200-meter cable run. The system needs to poll each sensor every 50 ms, and each sensor responds with 32 bytes of data. The engineer argues that at 115200 baud, the bus can handle the throughput. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging that the raw throughput calculation is a useful first check, but it's not sufficient. Let's work through it: 24 sensors polled every 50 ms means 480 polls per second. Each poll involves a request (say 8 bytes) and a response (32 bytes), plus protocol overhead — addressing, CRC, and inter-frame gaps. At 115200 baud, one byte takes about 87 microseconds, so 40 bytes of payload is roughly 3.5 milliseconds per transaction. With 480 transactions per second, that's about 1.68 seconds of bus time per second — which already exceeds the available bandwidth. So the throughput argument fails on its own terms.

But even if the numbers were within budget, there are additional concerns. First, the 50 ms polling period means each sensor must be polled every 50 ms, and with 24 sensors, the per-sensor time budget is about 2 milliseconds. The transaction time alone — request, response, turnaround — likely exceeds that. Second, RS-485 is half-duplex, so each transaction requires the bus to turn around from transmit to receive mode. The driver enable/disable time and the master's turnaround delay add overhead and can cause collisions if not managed carefully. Third, at 200 meters and 115200 baud, signal integrity becomes a concern — termination, stub lengths, and grounding all matter.

I'd guide the team to consider alternatives. One option is to increase the baud rate — RS-485 can run at higher speeds over shorter distances, but at 200 meters, the maximum reliable rate is limited. Another is to split the sensors across two or more buses, each with its own controller port. A third is to have the sensors report asynchronously rather than being polled, though that introduces collision risk. I'd also ask whether all 24 sensors need to be polled at the same rate — if some can tolerate a longer interval, the bus load drops significantly.

Finally, I'd emphasize that for a medical device, the analysis needs to be documented — the worst-case latency for each sensor, the bus utilization under normal and fault conditions, and the behavior when a sensor fails to respond. The design review should focus on whether the architecture meets the clinical requirements with adequate margin, not just whether it passes a back-of-envelope throughput calculation.

**Possible follow-ups:** How would you handle the case where one sensor fails to respond — should the master retry immediately or move on? What baud rate and bus configuration would you recommend for this scenario?