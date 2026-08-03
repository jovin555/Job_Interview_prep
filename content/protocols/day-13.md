# protocols — Day 13

## Q1: How would you approach implementing a protocol abstraction layer for a medical device that needs to support multiple physical interfaces (I2C, SPI, UART, CAN-FD) for different sensor modules, while keeping the application code independent of the specific transport?

**Answer:** I'd structure this around a layered architecture with clear separation between the application, a transport-agnostic protocol layer, and the physical drivers. At the top, the application would interact with a unified API—something like `sensor_read(device_id, register, &data, len)`—that doesn't expose whether the underlying transport is I2C or SPI. Below that, a protocol layer would handle device addressing, packet framing, and any transport-specific semantics like I2C register addressing versus SPI command/response sequences. The bottom layer would be thin hardware abstraction drivers that implement a common interface (init, read, write, transaction) for each physical bus.

Key design decisions would include: defining a transaction model that works across all transports—for example, a "write then read" pattern that maps naturally to I2C combined transactions, SPI full-duplex exchanges, and UART request/response frames; handling error reporting consistently (timeouts, NACKs, CRC failures) so the application can implement uniform retry and fault-handling logic; and deciding where protocol state lives—whether each sensor module gets its own driver instance with its own state, or whether there's a shared dispatcher. For a medical device, I'd also want a configuration table that maps each logical sensor to its physical transport, so changing a sensor from I2C to SPI during design iterations doesn't require application code changes.

One important consideration is that a single abstraction layer can hide differences that matter for timing or determinism. For example, a CAN-FD message is inherently packet-based with priority arbitration, while I2C is a bus transaction with clock stretching. So the abstraction needs to expose timing characteristics—like worst-case transaction duration or whether a transport supports asynchronous notifications—even if the basic read/write API is uniform. I'd also include a mechanism for transport-specific configuration (baud rates, clock polarity, addressing mode) that can be set at initialization without polluting the application interface.

**Possible follow-ups:**
- How would you handle a sensor that requires transport-specific features, like I2C clock stretching or SPI dual/quad modes, within this abstraction?
- How would you test the abstraction layer to ensure the application behaves identically regardless of which transport is underneath?

---

## Q2: You're debugging a system where a UART link between a microcontroller and a wireless module works reliably at 9600 baud but produces frequent framing errors at 115200 baud. The link is approximately 10 centimeters on the same PCB. How would you approach this?

**Answer:** Since the distance is short and the link is on the same PCB, I'd first rule out signal integrity issues like ringing or crosstalk, which are less likely at 10 cm but still possible if the trace runs near a switching regulator or a clock line. The more likely culprit is baud rate mismatch or clock tolerance. At 115200 baud, each bit is about 8.7 microseconds, so a combined transmitter/receiver clock error of even 2–3% can push the sampling point outside the bit window, especially toward the stop bit. At 9600 baud, the bit time is 10 times longer, so the same absolute error is proportionally much smaller.

I'd start by measuring the actual baud rate on both sides with an oscilloscope or logic analyzer—checking the microcontroller's UART output against the wireless module's expected rate. Common causes include: an inaccurate system clock (e.g., using the internal RC oscillator instead of a crystal, or a crystal with the wrong load capacitance); a UART peripheral configured with the wrong baud rate divisor due to a firmware bug; or the wireless module's UART being configured for a different rate than documented. I'd also check whether the microcontroller's clock source changes between low-power and active modes—some devices switch to a less accurate oscillator in sleep, which could cause marginal timing at higher baud rates.

If the clock sources check out, I'd look at the electrical signal quality. Even at 10 cm, a poorly terminated trace with high edge rates can cause ringing that crosses the receiver's threshold multiple times, and at higher baud rates the receiver samples more frequently, making it more sensitive to such glitches. I'd check the rise/fall times and look for overshoot. Adding a small series resistor near the driver or adjusting the drive strength setting on the microcontroller's GPIO could help. I'd also verify the receiver's sampling point—some UARTs sample at 16x or 8x the baud rate, and if the signal has slow edges, the sampling point might land during a transition.

Finally, I'd consider whether the wireless module's UART has a different tolerance specification than the microcontroller's. Some modules specify ±1% or ±2% baud rate tolerance, and if both sides are at the edge of their tolerance in opposite directions, the combined error can exceed the limit. In that case, I might recommend using a more accurate clock source or reducing the baud rate to a value within both devices' combined tolerance.

**Possible follow-ups:**
- How would you determine whether the issue is clock tolerance versus signal integrity without an oscilloscope?
- If you found the wireless module's UART was actually running at 115200 ±3%, how would you decide between changing the microcontroller's clock source versus lowering the baud rate?

---

## Q3: How would you approach designing a CAN-FD network for a medical device where a safety-critical message must be delivered with bounded latency, but the network also carries lower-priority telemetry that can be delayed without harm?

**Answer:** I'd approach this by first establishing the timing requirements quantitatively: the worst-case latency for the safety-critical message, the maximum acceptable jitter, and the expected load from telemetry traffic. Then I'd design the network to guarantee the safety-critical message's timing through a combination of protocol features and system-level design choices.

At the protocol level, CAN-FD's arbitration mechanism already provides priority-based access—the safety-critical message would be assigned the lowest identifier value on the bus, ensuring it wins arbitration against any lower-priority frame. But priority alone doesn't guarantee bounded latency if the bus is saturated or if there are multiple high-priority messages. I'd need to analyze the worst-case queuing delay: the time to finish transmitting the longest currently-in-progress frame (a 64-byte CAN-FD frame at the arbitration bit rate), plus the arbitration time for any higher-priority messages that might be queued simultaneously.

To make the analysis tractable, I'd consider several design levers. First, I'd separate the safety-critical traffic onto its own CAN-FD network if the telemetry load is high enough to threaten the latency bound—this is a common pattern in medical devices where a dedicated bus for safety functions simplifies verification. Second, I'd limit the maximum frame size for lower-priority messages, since a long telemetry frame that's already started when the safety message arrives will delay it. Third, I'd consider using the CAN-FD data phase at a higher bit rate to shorten all frame transmission times, which reduces the blocking time from any single frame.

I'd also look at the application layer: the safety-critical message should be transmitted on a periodic or event-driven basis with a dedicated transmit buffer that's never blocked by lower-priority traffic. Many CAN controllers have multiple transmit mailboxes with priority ordering, so I'd configure the safety-critical message in the highest-priority mailbox. I'd also implement a timeout or watchdog mechanism at the receiver so that if the safety message doesn't arrive within its bound, the system enters a safe state—this is essential for a medical device regardless of how confident we are in the timing analysis.

Finally, I'd verify the design through both analysis and testing: a worst-case response-time calculation using established CAN schedulability analysis, followed by bus-load testing with a logic analyzer to confirm actual latencies under maximum telemetry load. For a medical device, this analysis would be documented as part of the design verification evidence.

**Possible follow-ups:**
- How would you handle the case where a lower-priority node has a faulty transceiver that continuously transmits, blocking the bus?
- What bus-off recovery strategy would you implement for the node transmitting the safety-critical message?

---

## Q4: You're designing a USB 2.0 device for a medical application that must enumerate reliably across a wide range of host controllers, including older PCs and embedded hosts. How would you approach the device descriptor configuration to maximize compatibility?

**Answer:** I'd approach this by focusing on the descriptor hierarchy and the enumeration sequence, since compatibility issues often stem from subtle deviations in how descriptors are structured or how the device responds during the control transfers. The key principle is to be as conservative and standards-compliant as possible, while also being tolerant of host-side quirks.

Starting with the device descriptor, I'd set the `bcdUSB` field to 0x0200 to indicate USB 2.0 capability, but I'd be careful about the `bMaxPacketSize0` field—for full-speed devices, 64 bytes is the maximum, but some older hosts have issues with endpoints that use the maximum. I'd consider using 8 or 16 bytes for control endpoint 0 if the device's control transfers are small, as this is more conservative and matches what many legacy devices do. The `idVendor` and `idProduct` fields must be properly assigned, and I'd set `bcdDevice` to a value that can be incremented for firmware revisions.

For the configuration descriptor, I'd keep the structure simple and avoid optional descriptors that aren't strictly necessary. The `wTotalLength` field must be accurate, and I'd ensure the configuration descriptor, interface descriptor, and endpoint descriptors are all consistent. I'd use one interface with one or two endpoints for the primary function, and I'd avoid multiple interfaces unless the device truly needs them—some hosts have quirks with composite devices. For endpoint descriptors, I'd use reasonable maximum packet sizes: 64 bytes for bulk endpoints at full speed, and I'd set `bInterval` appropriately for interrupt endpoints (1–255 ms range for full speed).

I'd also pay attention to the string descriptors. Some hosts expect a string descriptor for the manufacturer, product, and serial number, but if the device doesn't have a serial number, I'd set `iSerialNumber` to 0 rather than providing an empty string. If I do provide a serial number, it should be unique per device—some hosts use it for driver binding and device identification. I'd use ASCII strings in English to avoid issues with Unicode handling on embedded hosts.

During enumeration, I'd implement the standard control transfer sequence carefully: respond to GET_DESCRIPTOR requests with the exact requested length, handle SET_ADDRESS correctly (some devices have bugs here), and respond to SET_CONFIGURATION by actually configuring the device. I'd also handle standard requests like GET_STATUS, SET_FEATURE, and CLEAR_FEATURE properly, even if the device doesn't use them, because hosts may send them during enumeration. For robustness, I'd implement a stall response for unsupported requests rather than ignoring them, and I'd ensure the device can recover from a stalled endpoint.

Finally, I'd test against a range of hosts: different versions of Windows, Linux with different USB stacks, macOS, and embedded hosts like those found in medical monitors. I'd use a USB protocol analyzer to capture the enumeration sequence on each host and compare them, looking for differences in how hosts request descriptors or handle timing. This testing is essential because even a fully compliant device can fail on a host with a buggy or non-standard implementation.

**Possible follow-ups:**
- How would you handle a host that requests the device descriptor with a length shorter than 18 bytes during the initial enumeration?
- What would you do if you found that a specific host controller requires the device to respond to a GET_DESCRIPTOR request for the configuration descriptor before SET_ADDRESS?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single RS-485 bus for a medical device system with 24 sensor nodes distributed along a 200-meter cable run. The system needs to poll each sensor every 50 ms, and each sensor responds with 32 bytes of data. The engineer argues that at 115200 baud, the bus can handle the throughput. How would you guide the team to evaluate this approach?

**Answer:** I'd guide the team to evaluate this from three angles: throughput, timing, and electrical robustness—and I'd start by acknowledging that the engineer's throughput calculation might be correct on paper, but the real question is whether the system can meet its timing and reliability requirements in practice.

First, let's check the throughput math. At 115200 baud with 8 data bits, no parity, 1 stop bit, each byte takes 10 bit times, so 32 bytes of data takes about 2.78 ms to transmit. But we also need to account for the polling command from the master (say 8 bytes, about 0.69 ms), the inter-frame gaps, and the turn-around time for the half-duplex bus—the master must stop transmitting, the sensor must detect the end of the command, and the transceiver must switch from transmit to receive mode. A typical turn-around time might be 100–200 microseconds per transition, and we have two transitions per poll cycle (master to sensor, sensor back to master). So each poll cycle is roughly 0.69 + 0.2 + 2.78 + 0.2 = about 3.9 ms. Polling 24 sensors sequentially gives about 93 ms per full cycle, which exceeds the 50 ms requirement. So the throughput calculation needs to include protocol overhead, not just the raw data rate.

But even if we could meet the timing, I'd raise the question of whether a single bus is the right architecture for a medical device. With 24 nodes on a 200-meter run, we have several concerns: stub lengths must be kept short (ideally under 0.3 meters at 115200 baud, though this is more critical at higher speeds); termination resistors are needed at both ends, and the value depends on the cable's characteristic impedance; and fail-safe biasing is needed to ensure the bus has a defined state when no node is transmitting. The common-mode voltage range of RS-485 transceivers is −7 V to +12 V, and in an industrial or hospital environment, ground potential differences between nodes could approach this limit, so we'd need to consider isolation or careful grounding.

I'd also ask about fault tolerance. If one sensor node fails with its transceiver stuck in transmit mode, it could take down the entire bus, affecting all 24 sensors. For a medical device, this might be unacceptable—we'd want to consider segmenting the bus into smaller groups, using a star topology with a hub, or providing redundant paths. The single-bus approach is simple and cost-effective, but the team needs to explicitly evaluate the failure modes and their impact on patient safety.

Finally, I'd suggest the team consider alternatives: using multiple RS-485 buses (e.g., four buses with six sensors each) to reduce per-bus load and improve fault isolation, or using CAN-FD, which provides built-in arbitration, error detection, and multi-master capability, though it requires different transceivers and a different protocol stack. The decision should be driven by the system requirements—latency, reliability, maintainability, and cost—not just by whether the raw throughput fits.

**Possible follow-ups:**
- How would you calculate the maximum stub length for this RS-485 network at 115200 baud, and what would you recommend if the physical layout makes short stubs impractical?
- What fail-safe biasing scheme would you recommend for this network, and how would you verify it works under all conditions, including when all nodes are silent?