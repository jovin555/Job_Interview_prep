# protocols — Day 8

## Q1: How would you approach designing a USB 2.0 device descriptor hierarchy for a medical device that must be recognized as a human interface device (HID) for simple data reporting, while also supporting a vendor-specific bulk endpoint for firmware updates?

**Answer:** The descriptor hierarchy is the fundamental contract between device and host, so getting it right is critical for reliable enumeration. I'd start with the device descriptor, which declares the device class. For a composite device that presents both HID and vendor-specific interfaces, I'd set `bDeviceClass` to 0x00 (defined at interface level) rather than specifying a single class, then define each interface separately.

The configuration descriptor would contain two interface descriptors. The first interface would be HID class (0x03), with one interrupt IN endpoint for periodic sensor data reporting. The HID report descriptor would define the data format — for a medical device, I'd keep the report structure simple and well-documented, using a fixed-size report that includes a sequence counter to detect missed packets.

The second interface would be vendor-specific (0xFF), with a bulk IN endpoint and a bulk OUT endpoint for firmware updates. Bulk transfers are appropriate here because firmware updates are not time-critical but need error-free delivery via the built-in CRC and retry mechanism.

I'd pay careful attention to endpoint descriptor ordering — the host expects endpoints to appear in ascending order within each interface. I'd also ensure the string descriptors are present for manufacturer, product, and serial number, as some operating systems rely on these for driver matching. The serial number is particularly important for medical devices that need to maintain patient data association across sessions.

**Possible follow-ups:** How would you handle the case where the HID report descriptor needs to change between firmware versions? What considerations would you have for the interrupt endpoint's polling interval in a medical context?

---

## Q2: You're designing an RS-485 network for a medical device system where 16 sensor nodes are distributed along a 200-meter cable run, and the system must support half-duplex communication with a maximum node-to-node latency of 2 milliseconds. How would you approach termination resistor selection and placement?

**Answer:** For a 200-meter RS-485 network, proper termination is essential to prevent signal reflections that cause data corruption. I'd start by characterizing the cable — typical twisted-pair cable for RS-485 has a characteristic impedance around 120 ohms, so I'd use 120-ohm termination resistors.

For placement, the standard approach is a single termination resistor at each end of the main bus — not at every node. With 16 nodes distributed along 200 meters, I'd place one 120-ohm resistor at the physical start of the bus (near the master/controller) and another at the farthest physical end. Stub lengths from the main bus to each node should be kept as short as possible — ideally under 0.3 meters at higher data rates, though for slower rates (say 115.2 kbps or below) stubs up to a few meters might be acceptable.

The 2-millisecond latency requirement influences the data rate. RS-485 latency is dominated by propagation delay (roughly 5-6 ns per meter for typical cable, so about 1 microsecond for 200 meters round-trip) plus transceiver switching time and firmware overhead. A 2 ms budget is generous for most applications, but I'd still calculate the worst-case: 200 meters × 5.5 ns/m × 2 (round trip) = 2.2 µs propagation, plus transceiver turn-around time (typically 100-200 ns for modern parts), plus UART framing time. At 115.2 kbps, a single byte takes about 87 µs, so a short message of 8-10 bytes would be under 1 ms total — well within budget.

I'd also consider fail-safe biasing. With termination resistors pulling the differential pair toward common-mode, a failsafe bias network (pull-up on A, pull-down on B) ensures the receiver sees a valid logic state when no driver is active. The bias resistor values need to be calculated so that the voltage across A-B exceeds the receiver's input threshold (typically 200 mV) even with the termination resistors loading the bus.

**Possible follow-ups:** How would you calculate the exact bias resistor values given 120-ohm termination at both ends? What happens if one of the termination resistors fails open?

---

## Q3: In a CAN-FD network for a medical device, you need to ensure that a high-priority safety-critical message is never delayed by more than 500 microseconds. How would you approach guaranteeing this timing requirement?

**Answer:** Guaranteeing deterministic timing on CAN-FD requires a systematic approach combining protocol-level configuration, message scheduling, and worst-case analysis.

First, I'd assign the safety-critical message the lowest possible CAN-ID (highest priority in the arbitration scheme). In CAN-FD, the arbitration phase uses standard CAN arbitration, so a message with ID 0x001 will always win arbitration against any higher-numbered ID. I'd reserve the lowest IDs exclusively for safety-critical messages.

Second, I'd analyze the worst-case latency using the standard CAN response time formula: worst-case latency = queuing jitter + transmission time + blocking time from lower-priority messages. The critical component is the blocking time — the longest time the bus could be busy with a lower-priority message when our high-priority message arrives. I'd ensure that no single lower-priority message exceeds, say, 200 µs of bus time, leaving 300 µs for our message's transmission and queuing.

Third, I'd consider the CAN-FD data phase bit rate. Using a higher bit rate in the data phase (e.g., 2-5 Mbps) reduces the transmission time for the data payload. For a safety-critical message with minimal data (say 8 bytes), the data phase at 5 Mbps takes about 13 µs, plus the arbitration phase at 500 kbps (about 50 µs for the header). Total transmission time would be roughly 60-70 µs.

Fourth, I'd implement a protocol-level mechanism to prevent bus flooding. I'd limit the number of consecutive lower-priority messages that can be transmitted without a gap, or use a time-triggered slot for the safety-critical message if the system architecture allows.

Finally, I'd verify the design with a CAN bus analysis tool that can measure actual message latencies under worst-case load conditions, including the scenario where all nodes transmit simultaneously. If testing reveals violations, I'd consider increasing the arbitration bit rate, reducing the maximum data payload of lower-priority messages, or implementing a dedicated safety-critical bus segment.

**Possible follow-ups:** How would you handle the case where a bus-off condition on one node could delay the safety-critical message? What role does the E2E CRC in CAN-FD play in ensuring data integrity for this message?

---

## Q4: You're debugging a system where an SPI bus communicates with three sensors on separate chip selects. The bus works correctly at 1 MHz but produces corrupted data at 10 MHz. How would you approach this?

**Answer:** This is a classic signal integrity problem that becomes apparent at higher frequencies. I'd approach it systematically, starting with the most likely causes.

First, I'd examine the physical layout. At 10 MHz, the signal wavelength is about 30 meters in FR4, so we're not dealing with transmission line effects yet, but we are dealing with capacitive loading and signal degradation. I'd check the total bus capacitance — each sensor's input capacitance plus PCB trace capacitance. If the total exceeds the SPI master's drive capability, the rising/falling edges will slow down, potentially violating setup/hold times at the sensors. A quick calculation: if each sensor has 10 pF input capacitance and traces add another 10 pF, three sensors give 40 pF total. Many SPI masters can drive up to 50-100 pF at 10 MHz, but it depends on the specific part.

Second, I'd use an oscilloscope to probe the SPI signals at the farthest sensor. I'd look for:
- Slowed edges (rise/fall times approaching or exceeding 10% of the bit period, which at 10 MHz is 100 ns)
- Ringing or overshoot on the clock line
- Data line transitions occurring too close to the clock edge
- Differences in signal quality between the three chip select lines

Third, I'd check the clock polarity and phase settings. If one sensor requires a different mode than the others, and the firmware is switching modes between transactions, there could be a timing issue where the clock doesn't stabilize before data is clocked. I'd verify that the mode switching is correct and that there's adequate idle time between chip select assertions.

Fourth, I'd examine the chip select timing. At higher speeds, the setup time between chip select assertion and the first clock edge becomes critical. Some sensors require tens of nanoseconds of CS-to-clock setup time. If the firmware doesn't account for this, the first bit might be sampled incorrectly.

Fifth, I'd consider the PCB layout — specifically, whether the SPI traces are routed with different lengths. At 10 MHz, a 1-inch difference in trace length introduces about 150 ps of skew, which is usually negligible, but if one sensor is on a separate board connected by a long cable, the added delay could be significant.

Finally, I'd try reducing the clock speed incrementally (5 MHz, 3 MHz) to find the threshold where corruption begins, which helps isolate whether it's a capacitive loading issue or a timing violation specific to a particular sensor.

**Possible follow-ups:** If you find that one specific sensor is causing the problem, how would you determine whether it's a hardware issue (input capacitance) or a firmware issue (timing configuration)? How would you modify the design to support 10 MHz operation?

---

## Q5: Imagine you're leading a design review where a firmware engineer proposes using a single UART with a software-based protocol multiplexer to communicate with four different sensors, each with different baud rates and protocols. The hardware engineer argues this is unreliable and wants four separate UART peripherals. How would you guide the team to a decision?

**Answer:** This is a classic engineering trade-off between simplicity and reliability, and as the lead, I'd guide the team through a structured decision-making process rather than imposing a solution.

First, I'd acknowledge both perspectives as valid. The firmware engineer's approach is elegant in terms of hardware cost and PCB space — one UART, one set of TX/RX traces. The hardware engineer's concern about reliability is legitimate, especially in a medical device where data integrity is critical.

I'd then ask the team to evaluate the proposal against specific criteria:

**Timing analysis:** With a single UART, the firmware must time-multiplex between four sensors. If each sensor requires polling at a specific interval, we need to calculate whether the aggregate bandwidth and timing constraints can be met. For example, if Sensor A runs at 115200 baud and needs 100 bytes every 10 ms, that's about 8.7 ms of bus time per transaction. If Sensor B also needs similar bandwidth, there's no room for the other two. I'd ask the firmware engineer to produce a worst-case timing diagram showing the polling schedule.

**Protocol compatibility:** If the sensors use different protocols (e.g., Modbus RTU, proprietary binary, ASCII), the multiplexer must handle each correctly. Some protocols have strict timing requirements — for example, Modbus RTU requires a 3.5-character silence between messages. Switching between protocols on the same UART introduces risk of misinterpreting leftover bytes or violating timing windows.

**Failure modes:** What happens if one sensor fails and holds the line in a constant state (e.g., stuck low)? With a shared UART, that failure blocks communication with all four sensors. With separate UARTs, only the failed sensor is affected. In a medical device, this graceful degradation could be a safety requirement.

**Baud rate switching:** Changing baud rates on the fly requires the UART to reconfigure, which takes time and introduces a window where incoming data could be misinterpreted. Some microcontrollers also have limitations on how quickly the baud rate generator can be updated.

After this analysis, I'd propose a middle ground if the timing works: use two UARTs instead of four, grouping sensors with compatible baud rates and protocols. This reduces hardware cost while providing some isolation. If the timing analysis shows the single-UART approach is feasible, I'd still require a hardware-level failsafe — perhaps a buffer or mux that can isolate a failing sensor — and a documented risk assessment for the design review.

The final decision would be based on the specific timing requirements, the criticality of each sensor's data, and the acceptable failure modes for the medical device. I'd document the rationale so the team understands why the decision was made.

**Possible follow-ups:** How would you test the reliability of the multiplexer approach during development? What would you include in the risk management file (per ISO 14971) for this design decision?