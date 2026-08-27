# protocols — Day 37

## Q1: How would you approach designing a USB 2.0 device descriptor hierarchy for a medical device that must be recognized as a human interface device (HID) for simple data reporting, while also supporting a vendor-specific bulk endpoint for firmware updates?

**Answer:** I'd start by clarifying the enumeration requirements and the host-side software stack, because the descriptor strategy depends on whether the host will use standard HID drivers or require a custom driver anyway. The cleanest approach for this dual-role device is a composite device with two interfaces: one HID interface for the data reporting path, and one vendor-specific interface with a bulk endpoint pair for firmware updates.

For the HID interface, I'd keep the descriptor minimal — a single endpoint (interrupt IN) with a report descriptor that matches exactly what the host application expects. The interrupt endpoint is appropriate for periodic sensor data because it guarantees polling intervals and works with the standard OS HID class driver without requiring custom driver installation.

For the firmware update interface, I'd use a vendor-specific class with bulk endpoints. Bulk transfers are ideal here because they have error detection and retry built into the protocol, which matters when a corrupted firmware image could brick the device. I'd also consider whether the firmware update interface should be present at all times or only during update mode — some devices use a dual-configuration approach where the default configuration exposes only HID, and a second configuration adds the vendor interface. That reduces the attack surface and simplifies certification, but it requires the host to issue a SetConfiguration request to switch modes.

A key detail is the order of interfaces in the configuration descriptor. Windows, for example, can be sensitive to interface ordering and will load drivers based on the first matching interface. I'd also pay attention to string descriptors — they should be stable and well-formed because some host stacks are picky about malformed strings during enumeration.

For robustness across hosts, I'd test against multiple operating systems and host controllers early in development, because descriptor issues often manifest as enumeration failures on specific hosts rather than on the development machine.

**Possible follow-ups:**
- How would you handle the case where the host needs to know whether the device is in update mode before it can issue the appropriate SetConfiguration request?
- What are the trade-offs between using a dual-configuration approach versus keeping both interfaces in a single configuration?

---

## Q2: In a CAN-FD network for a medical device, you need to ensure that a high-priority safety-critical message is never delayed by more than 500 microseconds. How would you approach guaranteeing this timing requirement?

**Answer:** I'd approach this as a worst-case timing analysis problem rather than a typical-case one. The first step is to understand the CAN-FD arbitration mechanism: even with a high-priority message ID, the message can be delayed by any lower-priority frame that has already started arbitration. So the worst-case latency is bounded by the longest lower-priority frame that can win arbitration just before the safety-critical message becomes ready to transmit.

I'd start by building a complete message schedule: every message on the bus, its period, its DLC, whether it uses the arbitration phase or data phase bit rate, and its priority. From there, I'd calculate the worst-case queuing delay using established CAN response-time analysis — the formula accounts for the blocking time from the longest lower-priority message, plus interference from higher-priority messages that may be queued ahead.

If the analysis shows the 500-microsecond bound is violated, I'd look at several levers. First, I'd check whether the safety-critical message can use a shorter DLC — CAN-FD allows payloads up to 64 bytes, but a shorter payload reduces transmission time. Second, I'd examine the data phase bit rate; CAN-FD's higher data rate only applies after arbitration, so increasing it directly reduces the time window where lower-priority frames occupy the bus. Third, I'd consider whether any lower-priority messages can be restructured — for example, splitting a large telemetry message into smaller frames reduces blocking time.

I'd also consider whether the safety-critical message should be transmitted on a dedicated bus segment. In medical devices, it's sometimes worth the extra cost of a separate CAN-FD channel for safety-critical traffic, isolating it from high-volume telemetry entirely. This is a system architecture decision that should be made early, because retrofitting it later is expensive.

Finally, I'd verify the analysis empirically. I'd use a CAN bus analyzer to capture traffic under worst-case conditions — all nodes transmitting at maximum rate — and measure the actual latency of the safety-critical message. The measurement should confirm the analysis and provide evidence for the regulatory file.

**Possible follow-ups:**
- How would you handle the case where a node in the error-passive state affects the timing analysis?
- What margin would you build into the 500-microsecond requirement, and why?

---

## Q3: You're debugging an RS-485 network where 16 sensor nodes communicate with a central controller over a 200-meter cable run. The system works during bench testing but experiences intermittent data corruption when installed in the field near industrial equipment. How would you approach this?

**Answer:** I'd treat this as an electromagnetic interference problem until proven otherwise, because the symptom — works on the bench, fails in the field near industrial equipment — strongly suggests coupling from external noise sources. My approach would be systematic, starting with observation and then isolating the coupling path.

First, I'd characterize the failure. I'd use a scope or logic analyzer to capture the actual waveforms on the bus during a corruption event. I'm looking for: common-mode voltage excursions beyond the transceiver's rating, ringing or overshoot on the edges, or noise spikes that coincide with the corruption. I'd also check whether the corruption correlates with specific equipment turning on or off — industrial motors, variable frequency drives, and switching power supplies are common culprits.

The most likely culprits in this scenario are: inadequate common-mode rejection due to missing or improper grounding, lack of proper termination, or missing fail-safe biasing. Let me walk through each.

Grounding is the big one. RS-485 is differential, but the transceivers still need a common-mode reference between nodes. If the nodes are powered from different supplies or the cable shield is grounded at multiple points with a ground potential difference, the common-mode voltage can exceed the transceiver's input range — typically −7V to +12V. I'd check the ground scheme: ideally, the shield should be grounded at one end (or via a capacitor at the other end for high-frequency noise), and all nodes should share a common ground reference. If the nodes are isolated, I'd verify the isolation rating is adequate for the expected ground potential difference.

I'd also verify termination. At 200 meters, the cable should be terminated at both ends with a resistor matching the cable's characteristic impedance — typically 120 ohms. Missing termination causes reflections that manifest as data corruption, especially at higher baud rates. I'd check whether the termination is present and correctly placed at the physical ends of the cable, not just somewhere in the middle.

Fail-safe biasing is another common issue. When no node is driving the bus, the differential voltage can float into the undefined region between the transceiver's logic thresholds. If the receiver doesn't have built-in fail-safe biasing, the bus needs external bias resistors to hold the idle state above the threshold. In a noisy environment, marginal fail-safe biasing makes the receiver more susceptible to noise-induced false bits.

If the hardware checks out, I'd look at the firmware. I'd verify that the protocol has adequate error detection — a CRC or checksum on every frame — and that the application handles corrupted frames gracefully by discarding them and requesting retransmission. I'd also check the turn-around timing: in half-duplex RS-485, the transmitter must release the bus before the next node starts driving, and if the timing is marginal, noise can cause collisions.

Finally, I'd consider adding common-mode chokes on the cable near the transceivers, or using transceivers with higher common-mode rejection. But I'd only do this after confirming the root cause, because adding components without understanding the failure mechanism risks masking the problem rather than fixing it.

**Possible follow-ups:**
- How would you determine whether the issue is common-mode noise versus differential-mode noise?
- What changes would you make to the protocol layer to make the system more robust to intermittent corruption?

---

## Q4: How would you approach selecting between interrupt transfers and isochronous transfers for a USB 2.0 medical device that streams real-time sensor data to a host computer?

**Answer:** The selection comes down to the data's tolerance for loss versus its tolerance for latency, and I'd frame the decision around the medical device's safety requirements.

Isochronous transfers guarantee bandwidth and bounded latency — the host reserves bandwidth for the endpoint during configuration, and the device gets a guaranteed slot in each frame or microframe. However, isochronous transfers have no error detection or retry. If a packet is corrupted, it's simply dropped. This makes isochronous transfers suitable for data where freshness matters more than completeness — for example, a continuous waveform display where a dropped sample causes a brief glitch but the next sample arrives on time.

Interrupt transfers, despite the name, are actually polled by the host at a guaranteed interval. They do include error detection — the host checks the CRC and can request retransmission of corrupted packets. The trade-off is that retransmission introduces latency variability. For a medical device, this matters if the data is used for real-time control or alarm generation, where a delayed packet could be worse than a dropped one.

My decision framework would be: if the data is used for monitoring or display, and occasional dropped samples are acceptable, isochronous is the right choice because it provides deterministic timing. If the data must be complete — for example, if it's used for post-processing, or if a missing sample could cause a false alarm — I'd use interrupt transfers with a buffering strategy on the host side to smooth out latency variation.

There's also a hybrid approach worth considering: use an isochronous endpoint for the real-time stream and a bulk or interrupt endpoint for a secondary path that carries a lower-rate "heartbeat" or status channel. This gives you the determinism of isochronous for the primary data and a reliable path for critical status information.

For a medical device, I'd also think about what happens when the host is busy. Isochronous endpoints have reserved bandwidth, so they're less affected by other bus traffic. Interrupt endpoints can experience increased latency if the bus is congested. If the sensor data is safety-relevant, I'd lean toward isochronous with a protocol-level sequence number so the host can detect gaps, combined with an alarm mechanism if gaps exceed a threshold.

**Possible follow-ups:**
- How would you handle the case where the host application needs to detect that it has missed sensor samples?
- What are the implications for the device's power consumption when using isochronous versus interrupt transfers?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single UART with a software-based protocol multiplexer to communicate with four different sensors, each with different baud rates and protocols. The hardware engineer argues this is unreliable and wants four separate UART peripherals. How would you guide the team to a decision?

**Answer:** I'd frame this as a requirements-driven decision rather than a personal preference, and I'd structure the discussion around three questions: what are the timing requirements for each sensor, what is the failure mode if the multiplexer introduces latency, and what is the development and testing cost of each approach.

First, I'd ask the junior engineer to walk through the multiplexer design in detail. A software multiplexer on a single UART means the UART must be reconfigured — baud rate, parity, stop bits — each time the master switches to a different sensor. That reconfiguration takes time, and during that window, the UART can't communicate. I'd ask: what's the worst-case latency for each sensor if the multiplexer is busy with another sensor's transaction? If any sensor has a real-time requirement — for example, a sensor that must be polled every 10 milliseconds — the multiplexer might not meet that deadline if another sensor's transaction takes 8 milliseconds.

I'd also ask about the protocol handling. Different sensors with different protocols means the firmware needs to parse and generate multiple frame formats. The multiplexer becomes a state machine that must handle partial frames, timeouts, and protocol-specific error conditions. This is significantly more complex than four independent UART drivers, and the complexity increases the risk of subtle bugs — especially around edge cases like a sensor responding late or not at all.

The hardware engineer's concern about reliability is valid, but I'd push back on the assumption that four UARTs are automatically more reliable. Four UARTs mean four interrupt handlers, four DMA channels (if used), and four sets of pin assignments. The firmware complexity shifts from protocol multiplexing to concurrent state management. Both approaches have complexity; the question is which complexity is easier to manage and test.

My guidance would be to evaluate the actual requirements first. If the sensors have modest data rates and no tight timing constraints, a single UART with a well-designed multiplexer can work — many industrial devices do exactly this. The key is that the multiplexer must be designed as a proper state machine with clear transaction boundaries, timeouts, and error handling, and it must be tested thoroughly. If any sensor has a hard real-time requirement, or if the combined traffic approaches the UART's bandwidth, I'd lean toward separate UARTs.

I'd also raise a middle-ground option: use two UARTs, grouping sensors by baud rate or timing requirements. This reduces pin count compared to four UARTs while providing more headroom than a single multiplexed UART.

Finally, I'd ask the team to consider the testing burden. A multiplexer needs extensive testing for interleaving scenarios, timeout handling, and protocol switching. Four independent UARTs are easier to test in isolation but harder to test for concurrent behavior. The decision should factor in the team's ability to test thoroughly under the project's schedule.

I'd summarize the decision criteria: timing requirements, data rates, protocol complexity, available pins, and testing resources. The team should make the call based on those criteria, not on intuition about which approach "feels" more reliable.

**Possible follow-ups:**
- How would you structure the testing plan for the software multiplexer approach if the team decides to go that route?
- What criteria would you use to decide that the multiplexer approach is no longer viable as requirements evolve?