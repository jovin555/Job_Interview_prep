# protocols — Day 31

## Q1: You're designing a medical device where a central controller needs to communicate with several sensor modules over a shared bus. Some sensors require deterministic, low-latency response, while others generate high-volume data that can tolerate delay. How would you approach selecting between I2C, SPI, UART, RS-485, and CAN-FD for this architecture?

**Answer:** I'd start by separating the requirements into hard constraints and preferences. The safety-critical, deterministic sensors need bounded latency — that immediately rules out I2C in most cases, since clock stretching by any slave can hold the bus indefinitely, and there's no built-in prioritization. SPI can work if the master controls scheduling, but it requires dedicated chip selects and careful management of the bus; it also doesn't scale well beyond a handful of devices. UART is point-to-point unless you add RS-485, which gives multi-drop capability but requires a master-polled or token-based scheme for determinism.

CAN-FD is often the strongest candidate for mixed criticality because it has built-in message prioritization through arbitration, and the data phase can run at higher bit rates for the high-volume telemetry. The arbitration phase guarantees that the highest-priority message wins access with bounded latency, assuming you've done the bus load analysis. For a medical device, I'd also consider whether the system needs to be electrically isolated, what cable lengths are involved, and whether power can be delivered over the same bus.

The methodology I'd apply: list every message, its size, required period or latency, and criticality. Calculate worst-case bus utilization for each candidate protocol. Then evaluate secondary factors — EMI susceptibility, connector pin count, cost, and the team's familiarity. I'd also think about failure modes: what happens when a node malfunctions and drives the bus? CAN-FD has robust error handling and can isolate a faulty node; RS-485 needs careful fail-safe biasing and termination to avoid a stuck bus.

**Possible follow-ups:**
- How would you handle the case where one sensor node needs deterministic response but is physically located far from the controller, requiring a longer cable run?
- What bus utilization threshold would you consider the maximum for a CAN-FD network carrying a safety-critical message, and why?

---

## Q2: You're debugging a system where an RS-485 network works reliably at 9600 baud but experiences intermittent corruption at 115200 baud. The cable run is approximately 150 meters with 12 nodes. How would you approach isolating the root cause?

**Answer:** I'd approach this systematically, starting with the physical layer since the symptom is baud-rate-dependent. At 115200 baud, the bit time is about 8.7 microseconds, which means signal reflections and timing margins become much more critical than at 9600 baud.

First, I'd verify termination. For a 150-meter cable with 12 nodes, you need termination resistors at both physical ends of the bus, matched to the cable's characteristic impedance — typically 120 ohms for twisted-pair. I'd check whether the terminations are actually at the ends or somewhere in the middle, and whether the resistor values are correct. I'd also look at stub lengths: each node's connection to the main bus should be as short as possible. At 115200 baud, a stub longer than about 1-2 meters can cause reflections that corrupt the signal.

Next, I'd check the transceiver's fail-safe biasing. Without proper bias resistors, the bus can float into an undefined state when no driver is active, and at higher baud rates the receiver might misinterpret noise as data. I'd verify the bias network provides adequate noise margin.

I'd also examine the driver's slew rate and whether the transceivers are rated for the data rate. Some transceivers have limited slew rates that work fine at low baud but produce non-ideal waveforms at higher rates. I'd use an oscilloscope to look at the signal at the farthest node — checking rise times, ringing, and whether the signal crosses the receiver's threshold cleanly.

Finally, I'd check the firmware's timing: at higher baud rates, the turn-around time between transmit and receive modes becomes more critical. If the driver isn't disabled quickly enough after the last byte, or the receiver isn't enabled soon enough, you can lose the first few bits of a response.

**Possible follow-ups:**
- How would you determine whether the issue is reflections versus marginal receiver thresholds?
- What would you look for on an oscilloscope to distinguish a termination problem from a fail-safe biasing problem?

---

## Q3: How would you approach implementing a deterministic scheduling scheme for a medical device that uses I2C for sensor reads, SPI for high-speed data logging, and UART for a user interface, all on a single microcontroller running Zephyr RTOS?

**Answer:** I'd start by defining the timing requirements for each interface. The I2C sensor reads likely have a required sampling rate and freshness constraint — the data must be read at a consistent interval. The SPI data logging needs to keep up with the sensor data without dropping samples. The UART user interface is typically lower priority and can tolerate some latency.

In Zephyr, I'd structure this using threads with priorities and a synchronization mechanism. The I2C sensor read thread would run at the highest priority with a period determined by the sensor's required sampling rate. It would use a kernel timer or a periodic wakeup to trigger each read. The SPI logging thread would run at a slightly lower priority, consuming data from a queue or ring buffer that the sensor thread populates. The UART thread would run at the lowest priority, handling user commands and status updates.

The key is to avoid blocking the sensor thread on lower-priority work. I'd use Zephyr's asynchronous or interrupt-driven APIs where possible, or at least ensure that the sensor thread only performs the I2C transaction and then signals other threads. For the I2C bus itself, I'd need to handle clock stretching from the sensor — if a sensor can stretch the clock, that could block the bus and delay other transactions. I'd consider whether the I2C bus needs a mutex to prevent concurrent access from multiple threads.

For the SPI logging, I'd use DMA if available to minimize CPU involvement. The UART interface would use interrupt-driven or DMA-based transmission to avoid blocking.

I'd also think about what happens under fault conditions: if the I2C bus hangs, the sensor thread could block indefinitely. I'd implement a timeout on I2C transactions and a recovery mechanism — perhaps toggling the bus or resetting the sensor. The watchdog timer would monitor the overall system health.

**Possible follow-ups:**
- How would you handle the case where an I2C sensor occasionally clock-stretches for longer than expected, potentially delaying the SPI logging?
- How would you prioritize the threads if the UART interface needs to respond to a user command within a specific time window?

---

## Q4: You're designing a USB 2.0 device for a medical application that must support both isochronous transfers for real-time sensor streaming and bulk transfers for reliable data logging, without one starving the other. How would you approach the endpoint configuration and firmware architecture?

**Answer:** I'd start by understanding the bandwidth requirements for each transfer type. USB 2.0 full-speed provides 1 MB/s total bandwidth, while high-speed provides 53 MB/s. Isochronous transfers have guaranteed bandwidth but no error retry — if a packet is corrupted, it's dropped. Bulk transfers have no guaranteed bandwidth but provide error checking and retry.

For the endpoint configuration, I'd allocate the isochronous endpoint first, reserving the bandwidth it needs. The USB specification requires that isochronous endpoints declare their bandwidth during enumeration, and the host controller reserves that bandwidth. I'd calculate the worst-case isochronous bandwidth needed for the sensor data, including overhead for the packet header and any scheduling gaps. The remaining bandwidth is available for bulk transfers.

The key design decision is how much isochronous bandwidth to reserve. If I reserve too much, bulk transfers starve. If I reserve too little, the sensor data might not fit in each frame or microframe. I'd look at the sensor's data rate and choose an isochronous packet size and interval that comfortably fits the data with some margin, but not so much that bulk transfers are severely limited.

In firmware, I'd use separate buffers for each endpoint. The isochronous path would use a double-buffering scheme — while one buffer is being transmitted, the next is being filled. The bulk path would use a queue or ring buffer that can accumulate data during periods of high isochronous activity. The host software would need to handle the variable throughput of bulk transfers.

I'd also consider the failure modes: if the host stops polling the isochronous endpoint, the device needs to decide whether to drop data or stall. For a medical device, dropping data might be acceptable for real-time monitoring but not for the data log. I'd implement a policy where the isochronous stream always takes priority, and the bulk log accumulates data with a watermark to signal if the host is falling behind.

**Possible follow-ups:**
- How would you calculate the maximum isochronous packet size for a given sensor data rate at full-speed versus high-speed?
- What would you do if the host controller doesn't provide the full isochronous bandwidth that was reserved during enumeration?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single CAN-FD bus for a medical device that carries both a safety-critical control message requiring delivery within 2 ms and high-volume telemetry from multiple sensors. The engineer argues that CAN-FD's higher data rate in the data phase eliminates any bandwidth concerns. How would you guide the team to evaluate this approach?

**Answer:** I'd acknowledge that CAN-FD's higher data phase rate does increase throughput, but I'd guide the team to recognize that the arbitration phase still operates at the classical CAN bit rate, and that's where the latency for the safety-critical message is determined. The data phase rate doesn't help if the bus is congested during arbitration.

I'd walk through the analysis: first, identify every message on the bus, its size, period, and priority. Then calculate the worst-case queuing delay for the safety-critical message — this is the time it could wait behind lower-priority messages that have already started transmitting. The CAN protocol is non-preemptive, so if a low-priority message has started arbitration, the high-priority message must wait for it to complete.

The key question is whether the worst-case latency for the safety-critical message meets the 2 ms requirement. This depends on the longest message on the bus, the arbitration bit rate, and the bus load. Even with CAN-FD's faster data phase, a long telemetry message at the arbitration bit rate could occupy the bus for a significant time.

I'd also raise the issue of error handling: if a node enters the bus-off state or generates error frames, that adds to the worst-case latency. The team should analyze the error recovery behavior and whether a burst of errors could push the safety-critical message past its deadline.

I'd guide the team to consider alternatives: separating the safety-critical traffic onto a dedicated bus, or using time-triggered scheduling (like TTCAN or a schedule table) to guarantee the slot for the critical message. I'd also ask whether the telemetry could be reduced or batched to lower bus utilization.

Finally, I'd emphasize that the analysis needs to be documented — for a medical device, the timing analysis becomes part of the regulatory submission, and the team needs to demonstrate that the worst-case latency meets the requirement with margin.

**Possible follow-ups:**
- How would you calculate the worst-case latency for the safety-critical message, and what margin would you consider acceptable?
- What would you do if the analysis shows the 2 ms requirement can't be met with the current message set?