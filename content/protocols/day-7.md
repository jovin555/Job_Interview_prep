# Protocols — Day 7

## Q1: You're designing a medical device that uses USB 2.0 for both charging and data transfer. During compliance testing, the device fails enumeration on certain host controllers. How would you approach debugging this?

**Answer:** I'd approach this systematically, starting with the most common causes of enumeration failures. First, I'd capture USB traffic with a USB protocol analyzer (or logic analyzer with USB decoding) on both a working and failing host to compare the enumeration sequence. I'd look specifically at:
- Whether the host detects the device's connection (D+/D- line state changes)
- Whether the device responds to the default address (0x00) with the correct device descriptor
- Whether any control transfers are timing out or returning STALL

Common causes I'd investigate in parallel:
1. **VBUS detection timing** — Some hosts are strict about how quickly the device must assert D+ pull-up after VBUS rises. If the device's firmware waits too long to enable the pull-up, enumeration may fail on hosts with tighter timing windows.
2. **Descriptor issues** — A malformed device descriptor (e.g., incorrect bMaxPacketSize0 for full-speed, or mismatched string descriptor indices) can cause some host controllers to abort enumeration while others tolerate it.
3. **Power sequencing** — If the device draws more than 100mA before being configured, some hosts will reset the port. I'd verify the inrush current profile with an oscilloscope on VBUS.
4. **Crystal/clock accuracy** — USB requires ±0.25% accuracy for full-speed. I'd measure the actual clock frequency and jitter on the failing hosts.

I'd also check whether the failure correlates with specific host controller vendors (e.g., Intel vs. ASMedia vs. VIA), which would point toward a timing or descriptor compliance issue rather than a hardware fault.

**Possible follow-ups:** How would you differentiate between a hardware-level issue (like signal integrity) and a firmware-level issue (like descriptor formatting) during this debug? What tools would you use to verify the clock accuracy requirement?

---

## Q2: In a CAN-FD network for a medical device with multiple nodes, you need to ensure that a high-priority safety-critical message is never delayed by more than 500 microseconds. How would you approach guaranteeing this timing requirement?

**Answer:** I'd approach this as a combination of network design, message scheduling analysis, and verification. The key is understanding that CAN-FD's arbitration mechanism gives priority to messages with lower identifier values, but worst-case latency still depends on bus load and message timing.

First, I'd perform a **worst-case response time analysis** for the safety-critical message. This involves calculating:
- The longest possible time the message could wait for an ongoing lower-priority message to complete (blocking time)
- The queuing delay from higher-priority messages
- The transmission time itself (which depends on the data phase bit rate and payload size)

For a 500µs requirement, I'd consider:
1. **Assigning the lowest identifier** (highest priority) to the safety-critical message — this ensures it always wins arbitration.
2. **Limiting the maximum payload size** of lower-priority messages to bound blocking time. For example, if a lower-priority message can be 64 bytes at a 2 Mbps data phase, that's roughly 300µs of blocking time alone.
3. **Using the higher data phase bit rate** (e.g., 5 Mbps) to minimize transmission time for the safety-critical message.
4. **Implementing a time-triggered or scheduled transmission** — if the message is periodic, I'd schedule it at a known offset from the bus idle state to avoid arbitration entirely.

I'd also consider whether the 500µs requirement includes software processing time (interrupt latency, CAN controller FIFO depth) or is purely the bus-level delay. If it's end-to-end, I'd need to account for the microcontroller's CAN peripheral latency and any protocol stack overhead.

Finally, I'd verify the analysis with a CAN bus monitor during integration testing, injecting worst-case traffic patterns (all other nodes transmitting at maximum rate) while measuring the safety-critical message's actual latency.

**Possible follow-ups:** How would you handle the case where adding a new node to the network could violate the timing guarantee? What's the trade-off between using a higher data phase bit rate and maintaining signal integrity on a physically long bus?

---

## Q3: How would you approach selecting between RS-422 and RS-485 for a medical device that needs to communicate with multiple sensors distributed across a patient monitoring system?

**Answer:** The fundamental difference is that RS-422 is designed for point-to-multipoint (one driver, up to 10 receivers) while RS-485 supports true multi-drop (multiple drivers and receivers on the same bus). For a patient monitoring system with multiple sensors, I'd evaluate based on the communication architecture:

**Choose RS-485 when:**
- Sensors need to initiate communication (e.g., alarm conditions, data ready interrupts)
- The system requires bidirectional communication where any node can transmit
- More than 10 devices need to share the bus
- The bus topology is truly distributed (daisy-chain or multi-drop)

**Choose RS-422 when:**
- The central controller is always the talker, and sensors only listen (e.g., polling-based system)
- Simpler driver enable control is desired (no half-duplex turn-around timing)
- The system has fewer than 10 sensors
- Higher data rates are needed over longer distances (RS-422 typically supports higher rates due to simpler termination requirements)

For a medical device, I'd also consider:
- **Fault tolerance** — RS-485's fail-safe biasing can detect open/short circuits, which is valuable for patient safety
- **Galvanic isolation** — Both support isolation, but RS-485's common-mode range (-7V to +12V) is wider, which helps in noisy hospital environments
- **Cable count** — RS-485 requires only one twisted pair for half-duplex; RS-422 typically needs two pairs (one for transmit, one for receive) unless using a 4-wire configuration

In practice, I'd lean toward RS-485 for most multi-sensor medical systems because the bidirectional capability simplifies the protocol design (sensors can asynchronously report critical events) and the larger node count provides headroom for future expansion. However, if the system uses a strict polling protocol and has fewer than 10 sensors, RS-422's simpler driver control might reduce firmware complexity.

**Possible follow-ups:** How would you handle the half-duplex turn-around timing in RS-485 to avoid bus contention? What fail-safe biasing network would you recommend for a medical RS-485 bus?

---

## Q4: You're debugging a UART communication issue where a medical sensor occasionally sends framing errors after several hours of continuous operation. How would you approach this?

**Answer:** Intermittent framing errors after extended operation suggest a problem that develops over time rather than a static configuration issue. I'd approach this systematically:

**1. Characterize the failure pattern:**
- Log the timestamps of framing errors to see if they correlate with temperature changes, vibration, or other environmental factors
- Check if the error rate increases over time (suggesting a thermal drift issue)
- Determine if errors occur on specific byte values (suggesting a bit timing issue near certain data patterns)

**2. Investigate clock sources:**
- Measure the baud rate accuracy of both transmitter and receiver over temperature using an oscilloscope or frequency counter
- Check if the microcontroller's internal oscillator is being used — these can drift significantly with temperature, while external crystals are more stable
- Verify that both sides are using the same baud rate configuration (including parity, stop bits)

**3. Examine signal integrity:**
- Probe the UART lines with an oscilloscope during normal operation and when errors occur
- Look for edge jitter, ringing, or noise that could cause the receiver to sample at the wrong point
- Check for ground potential differences between devices, especially if they're on separate PCBs or powered from different supplies

**4. Consider software timing issues:**
- If using interrupt-driven UART, verify that the interrupt service routine completes before the next byte arrives (especially at higher baud rates)
- Check if other high-priority interrupts are blocking UART reception, causing missed start bits
- Verify that the receive buffer isn't overflowing, which could cause framing errors on subsequent bytes

**5. Temperature cycling test:**
- If the issue is thermal, I'd run the device in a temperature chamber while monitoring UART errors
- This would confirm whether the root cause is clock drift or component aging

For a medical device, I'd also consider whether the framing errors could be caused by electromagnetic interference from nearby equipment (e.g., MRI, electrosurgical units) that operates intermittently.

**Possible follow-ups:** If you find the framing errors are caused by clock drift from the microcontroller's internal oscillator, what solutions would you consider? How would you implement a robust UART protocol that can recover from occasional framing errors without losing data?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single UART with a software-based protocol multiplexer to communicate with four different sensors, each with different baud rates and protocols. The hardware engineer argues this is unreliable and wants four separate UART peripherals. How would you guide the team to a decision?

**Answer:** I'd frame this as a trade-off analysis that considers reliability, development complexity, cost, and the specific requirements of the medical device. I'd guide the team through these evaluation criteria:

**1. Timing analysis of the software multiplexer approach:**
- Calculate the worst-case latency for each sensor given the baud rates and message sizes
- Determine if the microcontroller can service all four sensors without missing bytes (considering interrupt latency, other tasks, and the highest baud rate)
- For example, if one sensor runs at 115200 baud, a new byte arrives every ~87µs — the firmware must respond within that window or risk buffer overrun

**2. Protocol compatibility:**
- Can the sensors be configured to use the same baud rate? If not, the multiplexer must reconfigure the UART between each sensor transaction, adding overhead and complexity
- Are the sensors polled or do they transmit asynchronously? Asynchronous transmission from multiple sensors on a single UART would cause data collisions

**3. Reliability and fault isolation:**
- With separate UARTs, a failure in one sensor's communication doesn't affect others
- With a multiplexer, a bug in the protocol handling for one sensor could corrupt data for all sensors
- In a medical device, fault isolation is critical for safety — the multiplexer approach creates a single point of failure

**4. Development and testing effort:**
- The multiplexer approach requires custom protocol parsing, state machines, and extensive testing for all edge cases
- Four separate UARTs use more hardware resources but leverage well-tested peripheral drivers and simpler code

**5. Practical compromise:**
- If the microcontroller has enough UART peripherals, I'd recommend using separate UARTs for sensors that transmit asynchronously or have incompatible baud rates
- For sensors that are polled and can share a baud rate, a multiplexer might be acceptable with careful timing analysis and a watchdog timer to detect communication failures
- Alternatively, consider using an I2C or SPI bus for some sensors if they support it, reducing the number of UARTs needed

I'd ask the junior engineer to produce a timing analysis showing worst-case latency and buffer requirements, and ask the hardware engineer to quantify the cost and PCB area impact of four UARTs. The final decision should be documented with the rationale, including a risk assessment for the medical device context.

**Possible follow-ups:** What specific timing analysis would you ask the junior engineer to produce? How would you implement a watchdog mechanism to detect if the software multiplexer has failed?