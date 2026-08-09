# protocols — Day 19

## Q1: How would you approach designing a bus arbitration scheme for a multi-master I2C system where two microcontrollers need to share access to a single EEPROM and a set of sensors, with the requirement that no data corruption occurs during arbitration?

**Answer:** I'd start by leveraging I2C's built-in arbitration mechanism rather than trying to implement a software-level lock on top of it. I2C arbitration is deterministic at the bit level — when two masters drive the bus simultaneously, the one driving a recessive (high) bit while the other drives a dominant (low) bit loses arbitration and must back off. The key design decision is structuring the message identifiers so that arbitration resolves predictably.

First, I'd assign each master a unique address prefix as the first byte(s) of every transaction. This ensures that when both masters attempt to access the bus simultaneously, arbitration resolves cleanly without partial data corruption. The master with the lower address wins, and the loser detects the arbitration loss via the ACK/NACK mechanism and retries after a randomized backoff.

Second, I'd think carefully about clock stretching. If one master is slower or needs more time to process, it can stretch the clock to hold the bus. Both masters need to support this properly, and the firmware must handle the case where the other master is stretching for an extended period.

Third, I'd consider whether true multi-master is actually necessary. If the two microcontrollers are on the same PCB and can communicate via a simpler mechanism (like a dedicated GPIO handshake line or a shared mailbox in memory), that might be more deterministic and easier to debug. Multi-master I2C adds complexity in arbitration, error recovery, and bus fault handling that may not be justified.

Finally, I'd implement a bus recovery mechanism. If a master detects a bus hang (e.g., SDA held low by a slave that never releases it), it should be able to toggle SCL to release the stuck slave, then re-initiate the transaction. This is especially important in medical devices where a hung bus could delay critical data.

**Possible follow-ups:**
- How would you handle the case where a master loses arbitration but has already partially written data to a slave?
- What happens if one master is in a low-power state and misses an arbitration event — how would you ensure it doesn't corrupt the bus when it wakes up?

---

## Q2: You're debugging a system where an RS-485 network works reliably at 9600 baud but experiences intermittent corruption at 115200 baud. The cable run is approximately 150 meters with 12 nodes. How would you approach this?

**Answer:** This is a classic symptom of signal integrity issues that only manifest at higher data rates. I'd approach it systematically, starting with the most likely causes.

First, I'd check termination. At 115200 baud over 150 meters, the cable is electrically long relative to the bit period. Proper termination (typically 120 ohms at both ends) becomes critical. If termination is missing or incorrect, reflections will cause ringing and data corruption. I'd verify the termination resistors are present, correctly valued, and placed at the physical ends of the bus — not just at the nearest nodes.

Second, I'd examine stub lengths. At 115200 baud, the bit time is approximately 8.7 microseconds. Stubs longer than about 0.3 meters (roughly λ/10 for the signal's rise time) can cause reflections that corrupt data. With 12 nodes, there could be significant stubs if the wiring isn't daisy-chained properly. I'd check the physical topology and consider whether stubs need to be shortened or eliminated.

Third, I'd look at the transceiver's slew rate. Many RS-485 transceivers have a slew-rate-limited mode for lower data rates (e.g., up to 250 kbps) that reduces EMI but also limits edge rates. If the transceivers are in a slow-slew mode, the edges at 115200 baud might be too slow, causing bit sampling errors. I'd check the transceiver datasheet and ensure the slew-rate setting matches the intended data rate.

Fourth, I'd verify the common-mode voltage range. At 150 meters, ground potential differences between nodes can be significant. If the transceivers don't have adequate common-mode rejection, or if there's no proper grounding strategy, the receiver might see voltages outside its input range. I'd check whether fail-safe biasing is present and correctly valued.

Finally, I'd use an oscilloscope to look at the actual waveforms at the farthest node — checking eye diagrams, rise/fall times, and any ringing or overshoot. This would confirm whether the issue is reflection-related, slew-rate-related, or something else.

**Possible follow-ups:**
- How would you determine the maximum practical data rate for a given cable length and node count?
- What role does fail-safe biasing play in this scenario, and how would you verify it's correct?

---

## Q3: How would you approach implementing end-to-end data integrity protection for a CAN-FD message carrying a safety-critical payload, beyond what the controller's built-in CRC provides?

**Answer:** CAN-FD's built-in CRC is strong — the 17-bit or 21-bit CRC provides excellent protection against bit errors in the frame. However, for safety-critical medical applications, end-to-end protection is about more than just detecting bit flips. It's about ensuring the data is authentic, current, and complete.

I'd approach this in layers. First, I'd add an application-layer sequence counter to each safety-critical message. This detects lost or duplicated messages — something the CRC alone can't catch. The receiver can track the expected sequence number and flag any gaps or duplicates.

Second, I'd add a timestamp or time-since-last-message field. For safety-critical data, freshness is as important as correctness. If a message is delayed or the sender is stalled, the receiver needs to know that the data is stale and take appropriate action (e.g., enter a safe state).

Third, I'd consider a message counter and CRC combination at the application layer. While the CAN-FD controller CRC protects the frame during transmission, an application-layer CRC over the payload provides defense-in-depth — it catches any corruption that might occur in the controller's FIFO, in the SPI interface between the MCU and the CAN transceiver, or in the MCU's memory.

Fourth, I'd think about authentication. If the safety-critical message could be spoofed or injected by a faulty node, a simple CRC won't help. I'd consider a lightweight authentication mechanism — even a simple XOR-based checksum with a rolling key can detect accidental corruption from a faulty node, though it won't protect against deliberate tampering.

Finally, I'd design the receiver to handle failures gracefully. If a sequence gap is detected, or the CRC fails, the receiver should enter a defined safe state and log the event for post-incident analysis. The response to a detected error is as important as the detection mechanism itself.

**Possible follow-ups:**
- How would you handle the trade-off between adding application-layer protection and the added latency and bandwidth overhead?
- What happens if the sequence counter itself gets corrupted — how would you recover synchronization?

---

## Q4: How would you approach designing a USB 2.0 device that must support both isochronous transfers for real-time sensor streaming and bulk transfers for reliable data logging, without one starving the other?

**Answer:** USB 2.0's bandwidth allocation rules actually help here — isochronous transfers get reserved bandwidth during enumeration, and bulk transfers use whatever remains. But the challenge is ensuring the isochronous stream doesn't consume so much bandwidth that bulk transfers stall indefinitely, or that bulk transfers don't introduce jitter into the isochronous stream.

I'd start by calculating the bandwidth budget. USB 2.0 provides 480 Mbps, but the practical per-frame bandwidth is limited by protocol overhead. For a full-speed device (12 Mbps), a frame is 1 ms and the maximum isochronous payload is 1023 bytes per frame. For high-speed (480 Mbps), a microframe is 125 µs with a maximum isochronous payload of 3072 bytes per microframe. I'd calculate the required isochronous bandwidth for the sensor stream, then determine what remains for bulk transfers.

Next, I'd think about the isochronous endpoint configuration. The key decision is the packet size and the number of transactions per frame. Larger packets mean fewer transactions and less overhead, but they also mean more data buffering and potentially higher latency. I'd choose a packet size that matches the sensor's natural data rate — for example, if the sensor produces 1 kB of data every 10 ms, I'd use a 1 kB isochronous packet once per 10 ms rather than 100-byte packets every 1 ms.

For the bulk endpoint, I'd implement a flow-control mechanism in firmware. The bulk endpoint should only send data when there's a full buffer ready, and it should yield to the isochronous endpoint's scheduling. On the host side, I'd ensure the host controller driver prioritizes isochronous transfers appropriately — most host controllers do this automatically.

I'd also consider using a separate configuration or alternate setting for the isochronous endpoint. USB allows alternate settings that change the isochronous bandwidth allocation without re-enumerating. This lets the host dynamically adjust the streaming rate based on the application's needs.

Finally, I'd test thoroughly with a USB analyzer to verify that isochronous packets arrive on time and that bulk transfers complete without excessive delay. I'd also test with a busy host — one that's also handling other USB devices — to ensure the isochronous stream isn't disrupted by host-side scheduling issues.

**Possible follow-ups:**
- How would you handle the case where the host can't allocate enough bandwidth for the isochronous endpoint during enumeration?
- What happens if the sensor produces data faster than the isochronous endpoint can transmit — how would you handle buffer overflow?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single UART with a software-based protocol multiplexer to communicate with four different sensors, each with different baud rates and protocols. The hardware engineer argues this is unreliable and wants four separate UART peripherals. How would you guide the team to a decision?

**Answer:** I'd frame this as a structured decision rather than a debate, and I'd start by clarifying the actual requirements. The core question isn't "can we do it with one UART?" — it's "what are the reliability, latency, and determinism requirements for each sensor, and what's the cost of failure?"

First, I'd ask the team to map out the requirements for each sensor: data rate, latency tolerance, whether the sensor initiates communication or responds to polls, and the criticality of each data stream. If one sensor is safety-critical and another is low-priority telemetry, they have very different requirements.

Second, I'd analyze the single-UART approach. A software multiplexer on a single UART means the MCU must reconfigure the baud rate and protocol state machine each time it switches between sensors. This introduces switching overhead, and more importantly, it means the MCU can only talk to one sensor at a time. If a sensor needs to send an asynchronous alert while the MCU is mid-transaction with another sensor, that alert will be delayed or lost. The multiplexer also adds complexity — more code paths, more state, more potential for bugs.

Third, I'd consider the failure modes. With a single UART, a bug in the multiplexer could corrupt communication with all four sensors. With separate UARTs, a failure is isolated to one sensor. In a medical device, this isolation is valuable — it limits the blast radius of a firmware bug.

Fourth, I'd look at the MCU's resources. Does the MCU actually have four UART peripherals available? If yes, the hardware engineer's approach is simpler and more robust. If not, the team needs to weigh the cost of a larger MCU against the complexity of the multiplexer.

My guidance would be: if the MCU has enough UART peripherals, use them. The hardware cost is minimal, and the firmware is simpler and more reliable. If the MCU doesn't have enough UARTs, then the multiplexer approach is viable, but I'd require the junior engineer to document the switching protocol, handle the case where a sensor is mid-transmission during a switch, and implement a watchdog to detect a stuck multiplexer.

I'd also suggest a middle ground: use dedicated UARTs for the safety-critical or high-bandwidth sensors, and share a single UART for the low-priority ones. This balances hardware cost against reliability.

**Possible follow-ups:**
- How would you handle the case where one of the four sensors needs to send an unsolicited alert while the multiplexer is busy with another sensor?
- What testing would you require to validate the multiplexer approach before committing to it?