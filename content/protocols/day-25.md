# protocols — Day 25

## Q1: How would you approach designing a fail-safe mechanism for a CAN-FD network where a sensor node must never transmit stale data after the main controller has lost communication, but the node itself continues to operate normally?

**Answer:** The core challenge here is distinguishing "controller is gone" from "controller is temporarily busy," while ensuring the sensor node doesn't act on outdated information. I'd approach this with a layered strategy.

First, at the protocol level, I'd implement a heartbeat or watchdog mechanism: the controller periodically broadcasts a liveness message with a sequence number and timestamp. Each sensor node monitors this heartbeat and, if it misses a configurable number of consecutive heartbeats (typically 2–3 to avoid false positives from transient bus errors), it transitions to a defined safe state. The timeout window must be carefully chosen—long enough to tolerate legitimate bus congestion or retransmissions, but short enough that stale data is never used beyond a clinically acceptable latency.

Second, I'd add data freshness validation at the application layer. Every sensor reading includes a timestamp or monotonically increasing sequence number. The receiving side (whether the controller or another node) validates that the data is within an acceptable age window before acting on it. This protects against scenarios where the heartbeat mechanism itself fails or where a node resumes transmitting after a partial failure.

Third, I'd define explicit safe-state behavior for each node. This isn't just "stop transmitting"—it's "what should the node do with its actuators or outputs?" For a sensor node, the safe state might be to continue sampling locally but buffer data, or to power down non-essential circuitry. For an actuator node, it might mean holding the last valid command or reverting to a default safe output. This decision should be documented in the risk management file, because the safe state itself can introduce new hazards.

Finally, I'd consider whether the CAN-FD controller's error handling features can help. For example, if the node detects bus-off conditions or excessive error frames, that's a strong signal of a broader communication failure, and the node should enter its safe state rather than continuing to attempt transmission.

**Possible follow-ups:** How would you determine the appropriate heartbeat timeout value? What if the sensor node itself is the one that fails—how does the controller detect that?

---

## Q2: You're debugging a system where a USB 2.0 device works correctly on most hosts but fails to enumerate on a specific laptop. The device uses a composite descriptor with a HID interface and a vendor-specific bulk interface. How would you approach isolating whether the problem is in the descriptor configuration, the host controller driver, or the device firmware?

**Answer:** I'd approach this systematically, starting with the most likely and most easily testable causes before diving into deeper investigation.

First, I'd capture the full enumeration traffic using a USB protocol analyzer or, if available, the host's USB debug logs (e.g., Wireshark with USBPcap on Windows, or usbmon on Linux). This tells me exactly where enumeration fails: does the host send a GET_DESCRIPTOR request that goes unanswered? Does the device respond with a stall? Does the host reject a descriptor value? This immediately narrows the problem space.

Second, I'd check the descriptor configuration against the USB 2.0 specification, particularly the composite device rules. Common issues include: incorrect interface association descriptors (IADs) for composite devices, mismatched endpoint descriptors (e.g., wrong wMaxPacketSize for full-speed vs. high-speed), or a configuration descriptor that exceeds the host's maximum supported size. I'd also verify that the device correctly handles the initial 64-byte GET_DESCRIPTOR request that hosts use to fetch the device descriptor before the full configuration.

Third, I'd test the device on multiple hosts to characterize the failure pattern. If it fails on one specific laptop but works on others, I'd check whether that laptop has a different USB host controller vendor (Intel, AMD, Renesas, etc.) or a different OS version. Some host controllers are stricter about certain behaviors—for example, requiring the device to respond to a SET_ADDRESS request within a specific time window, or handling remote wakeup signaling differently.

Fourth, I'd add debug output to the device firmware to log which requests it receives and how it responds. This helps determine whether the device is even seeing the enumeration requests, or whether the host is giving up before sending them.

If the issue turns out to be host-specific, I'd look at whether the host has outdated USB drivers or a known issue with composite devices. If it's a firmware issue, I'd focus on timing—some hosts are sensitive to how quickly the device responds to control transfers, especially during the initial enumeration sequence.

**Possible follow-ups:** How would you handle a situation where the device enumerates but the HID interface works while the bulk interface doesn't? What role does the device descriptor's bMaxPacketSize0 field play in enumeration compatibility?

---

## Q3: How would you approach implementing a protocol conversion layer between a legacy RS-485 network using a proprietary binary protocol and a modern CAN-FD network, where the gateway must handle different data rates, message priorities, and error handling semantics between the two sides?

**Answer:** This is fundamentally a gateway design problem, and I'd approach it by separating concerns: the physical/electrical interface, the protocol parsing, the data model, and the priority/error mapping.

At the physical layer, the gateway needs independent transceivers for each bus—RS-485 transceivers with appropriate termination and fail-safe biasing on one side, CAN-FD transceivers on the other. These are electrically incompatible, so isolation (galvanic or at least careful grounding) is important, especially in a medical environment where leakage current and ground potential differences matter.

At the protocol layer, I'd implement a clean abstraction: each side has a driver that handles its native framing, addressing, and error detection. The core of the gateway is a translation table that maps legacy message types to CAN-FD message IDs, and vice versa. This table should be data-driven (e.g., a configuration file or lookup table) rather than hardcoded, so it can be updated without firmware changes.

The tricky part is semantic mapping. RS-485 is typically polled or event-driven with no inherent prioritization, while CAN-FD has built-in arbitration based on message IDs. I'd need to decide how to map the legacy protocol's message types onto CAN-FD priorities. Safety-critical messages (e.g., alarm conditions, patient data) should get lower CAN-FD IDs (higher priority), while routine telemetry gets higher IDs. This mapping should be documented and reviewed against the system's risk analysis.

Error handling is another key difference. RS-485 has no built-in error detection beyond what the protocol adds (e.g., CRC), while CAN-FD has hardware CRC and error confinement. The gateway must decide how to handle a message that's valid on one side but fails validation on the other. For example, if a legacy node sends a message with a bad CRC, should the gateway forward it anyway (with a flag) or drop it? In a medical context, I'd lean toward dropping invalid messages and logging the event, but this decision needs to be made with the clinical risk in mind.

Finally, I'd implement buffering and flow control. The two buses may operate at very different rates—a legacy RS-485 network at 9600 baud versus CAN-FD at 1 Mbps in the arbitration phase and 5 Mbps in the data phase. The gateway needs sufficient buffering to handle bursts, and a strategy for what to do when buffers overflow (drop oldest, drop newest, or block the faster side). For a medical device, I'd want to avoid dropping safety-critical messages, so I might implement priority-based buffer management.

**Possible follow-ups:** How would you handle the timing mismatch if a legacy node expects a response within a specific time window but the CAN-FD side introduces variable latency? How would you test the gateway's behavior under fault conditions on either bus?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single SPI bus with four slaves, each on an independent chip select, to connect a high-resolution ADC, a flash memory for data logging, a real-time clock, and a temperature sensor in a battery-powered medical device. The engineer argues that SPI's high data rate and simple architecture make it the obvious choice. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging that SPI is a reasonable default for this application—it's fast, simple, and well-understood. But I'd guide the team to evaluate the proposal against the specific requirements of a battery-powered medical device, rather than accepting it on general merits.

First, I'd ask about the data rate requirements for each slave. The ADC might need continuous high-speed sampling, the flash memory needs high throughput for logging, but the RTC and temperature sensor are likely polled infrequently. SPI's advantage is that each slave gets the full bus bandwidth when its chip select is asserted, so the ADC and flash can run at high speed without contention. But I'd ask whether the bus actually needs to run at, say, 10 MHz, or whether 1–2 MHz would suffice—lower clock rates reduce EMI and power consumption, which matters in a battery-powered device.

Second, I'd raise the issue of interrupt handling and latency. SPI is typically master-initiated, so the MCU must poll or use interrupts to know when a slave has data ready. For the ADC, this might mean continuous sampling with DMA, which is fine. But for the RTC and temperature sensor, the MCU needs to initiate transactions periodically. I'd ask whether the firmware architecture can handle this without missing time-critical events, and whether the RTC needs to generate alarms that wake the MCU from sleep—if so, a separate interrupt line from the RTC to the MCU is needed, which is an additional pin.

Third, I'd discuss the physical layer. Four slaves on independent chip selects means four CS lines plus MISO, MOSI, and SCK—seven signals total. On a small PCB, this is manageable, but I'd ask about trace routing and whether the MISO line has any contention risk. I'd also ask about the ADC's analog performance: SPI clock edges can couple into the analog front-end, so the layout needs to keep the SPI traces away from sensitive analog traces, and the ADC's sampling timing must be carefully synchronized with the SPI transactions.

Fourth, I'd raise power consumption. SPI peripherals on the MCU and slaves consume power even when idle if the bus is left active. I'd ask whether the design can power down the slaves or disable the SPI peripheral between transactions, and whether the flash memory's standby current is acceptable.

Finally, I'd ask about failure modes. If one slave holds MISO low or fails to release the bus, it can corrupt transactions with other slaves. I'd ask whether the firmware has timeout and error-recovery mechanisms, and whether the design review should consider a different architecture—for example, using I2C for the low-speed devices (RTC, temperature sensor) and reserving SPI for the high-speed ADC and flash. This hybrid approach might reduce pin count and simplify the firmware.

**Possible follow-ups:** How would you decide whether the hybrid I2C/SPI approach is worth the added complexity? What specific questions would you ask the junior engineer about the ADC's sampling requirements before approving the design?

---

## Q5: How would you approach developing a communication protocol test plan for a medical device that uses multiple interfaces (I2C, SPI, UART, and USB), where the test plan must verify both normal operation and fault tolerance, and the results need to be documented for regulatory submission?

**Answer:** I'd structure the test plan around three layers: protocol conformance, fault injection, and long-duration reliability. Each layer addresses a different risk, and all three need to be documented with traceability to the device's requirements and risk analysis.

At the protocol conformance layer, I'd verify that each interface correctly implements its protocol specification. For I2C, this means checking addressing, ACK/NACK behavior, clock stretching, and multi-master arbitration if applicable. For SPI, I'd verify clock polarity/phase settings, chip select timing, and data integrity across the full range of supported clock rates. For UART, I'd check baud rate accuracy, framing, parity, and flow control. For USB, I'd verify descriptor correctness, endpoint behavior, and enumeration across multiple host controllers and operating systems. These tests should be automated where possible—for example, using a protocol analyzer or a test fixture that can generate and verify traffic.

At the fault injection layer, I'd systematically introduce failures and verify that the device responds safely. This includes: disconnecting and reconnecting each interface mid-transaction; shorting signal lines to power or ground; introducing noise or interference (e.g., ESD events, RF interference); corrupting data (e.g., bit errors, CRC failures); and simulating device failures (e.g., a sensor that stops responding, a host that resets mid-transfer). For each fault, I'd verify that the device detects the condition, enters a defined safe state, and recovers appropriately when the fault is removed. The expected behavior for each fault should be defined in advance, based on the risk analysis—for example, a sensor read failure might trigger a retry, while a communication bus failure might trigger a system alarm.

At the long-duration reliability layer, I'd run the device continuously for extended periods (days to weeks) while monitoring for intermittent failures. This is where subtle issues like bus capacitance drift, thermal effects on timing, or firmware memory leaks often surface. I'd instrument the device to log all communication errors, retries, and resets, and I'd review these logs regularly to identify patterns.

For regulatory documentation, I'd create a traceability matrix linking each test case to the specific requirement it verifies and the associated risk control measure. Each test case would include: the test setup, the procedure, the pass/fail criteria, the observed results, and any deviations or anomalies. This documentation needs to be complete and auditable, because a regulatory reviewer will likely sample test cases and verify that the results are consistent with the device's design description.

**Possible follow-ups:** How would you prioritize which fault injection tests to run first, given limited time and budget? How would you handle a situation where a fault injection test reveals a previously unknown failure mode that wasn't addressed in the risk analysis?