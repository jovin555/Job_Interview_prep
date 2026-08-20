# protocols — Day 30

## Q1: How would you approach designing a protocol conversion gateway between a legacy RS-485 network using a proprietary binary protocol and a modern CAN-FD network, where the gateway must handle different data rates, message priorities, and error handling semantics between the two sides?

**Answer:** The core challenge here is that you're bridging two fundamentally different communication paradigms, not just translating bytes. RS-485 is typically a polled, master-slave, half-duplex bus with no inherent prioritization, while CAN-FD is multi-master with message-based arbitration and priority built into the identifier. I'd start by clearly documenting the data flow requirements: which messages are periodic, which are event-driven, and which are safety-critical on each side.

For the gateway architecture, I'd use a dual-interface design with independent RX/TX buffers for each side, decoupled by a shared memory region or message queue. This prevents back-pressure on one bus from stalling the other. The translation layer needs a mapping table that defines how legacy message types map to CAN-FD identifiers, and critically, how priority is assigned. Since RS-485 has no native priority, I'd need to define a priority scheme based on message content and latency requirements — for example, alarm conditions from the legacy side should map to high-priority CAN-FD identifiers.

Error handling is where most gateways fail. The two buses have different error semantics: RS-485 might use CRC or checksum validation with retries, while CAN-FD has hardware-level error detection and automatic retransmission. The gateway needs a defined policy for what happens when a message is corrupted on one side — does it retry, drop, or flag it? I'd implement a status reporting mechanism so the system knows when the gateway is experiencing degraded operation. I'd also consider adding a watchdog or health-check mechanism between the gateway and both networks, so a failure on either side is detected and reported rather than silently causing data loss.

**Possible follow-ups:** How would you handle a situation where the legacy protocol has no concept of message priority, but the CAN-FD side requires it for arbitration? What happens if the gateway itself fails — how would you design for fail-safe operation?

---

## Q2: You're debugging a system where a USB 2.0 device enumerates correctly on most hosts but fails on a specific embedded host controller. The device uses a composite descriptor with both HID and vendor-specific interfaces. How would you approach isolating whether the problem is in the descriptor configuration, the host controller driver, or the device firmware?

**Answer:** I'd approach this systematically, starting with the most likely and easiest-to-test causes. First, I'd capture the enumeration traffic on both a working host and the failing host using a USB protocol analyzer or by enabling verbose USB logging in the host's kernel or driver stack. Comparing the two traces often reveals exactly where the enumeration diverges — whether the host stops requesting descriptors at a certain point, or the device fails to respond to a specific request.

Next, I'd examine the descriptor configuration itself. Composite devices are a common source of enumeration issues because the order and structure of interface descriptors, endpoint descriptors, and string descriptors must be exactly correct. Some embedded hosts are stricter about descriptor formatting than desktop operating systems. I'd check things like: are the interface numbers sequential and correctly referenced in the configuration descriptor? Are endpoint addresses unique and correctly specified? Is the HID descriptor properly formed? Are there any vendor-specific descriptors that the embedded host might not understand?

I'd also look at timing. Embedded hosts often have tighter timeouts for device responses. If the device firmware takes too long to respond to a control transfer — for example, because it's busy initializing something — a desktop host might wait longer than an embedded host. I'd check the device's response time to standard requests like GET_DESCRIPTOR and SET_CONFIGURATION.

If the descriptors look correct, I'd then isolate whether it's a host driver issue by testing the device against a different embedded host or by using a USB analyzer to verify the device is responding correctly at the protocol level. If the device responds correctly but the host still fails, it's likely a host-side driver limitation. In that case, I might simplify the descriptor set — for example, making the vendor-specific interface optional or using a single interface with multiple alternate settings — to improve compatibility.

**Possible follow-ups:** What specific descriptor fields would you examine first when debugging enumeration failures? How would you approach making the device more tolerant of hosts that send unexpected or out-of-order requests?

---

## Q3: How would you approach implementing a deterministic scheduling scheme for a medical device that uses I2C for sensor reads, SPI for high-speed data logging, and UART for a user interface, all on a single microcontroller running Zephyr RTOS?

**Answer:** The key is to recognize that each protocol has different timing characteristics and criticality levels, and the scheduler needs to respect those differences. I'd start by defining the timing requirements for each interface: what's the maximum acceptable latency for a sensor read, how much data needs to be logged per second, and what's the expected response time for user interface commands.

In Zephyr, I'd structure this using a combination of RTOS primitives: threads with different priorities, semaphores or message queues for data passing, and hardware timers for precise scheduling. The I2C sensor reads would typically go in a high-priority thread with a periodic timer, since sensor data freshness is often critical in medical devices. The SPI logging could be a lower-priority thread that processes data from a queue — it's high-throughput but can tolerate some buffering. The UART interface would be event-driven, waking on interrupts when data arrives.

The critical design decision is how to handle contention. If I2C and SPI share the same bus or if the SPI logging is time-consuming, I'd need to ensure that a long SPI transaction doesn't delay a time-critical I2C read. One approach is to use Zephyr's priority-based preemptive scheduling: the I2C thread runs at a higher priority and can preempt the SPI thread mid-transaction. However, this requires careful handling of shared resources — if both interfaces use the same DMA controller or if the SPI transaction is in the middle of a chip-select assertion, preemption could cause protocol violations.

I'd also consider using Zephyr's hardware synchronization primitives, like mutexes with priority inheritance, to prevent priority inversion when multiple threads access shared peripherals. For the SPI logging, I might use double-buffering with DMA so that data can continue transferring while the CPU handles other tasks. The UART interface would use interrupt-driven RX with a ring buffer, and the processing thread would be lower priority since user interface commands are typically less time-critical than sensor data.

Finally, I'd add instrumentation to measure actual timing — how long each transaction takes, how often scheduling deadlines are missed — and use that data to tune priorities and buffer sizes. In a medical device, you'd also want to document the worst-case timing analysis to demonstrate that all deadlines are met under all operating conditions.

**Possible follow-ups:** How would you handle the case where a sensor read occasionally takes longer than expected due to clock stretching on the I2C bus? How would you verify that your scheduling scheme meets all timing requirements under worst-case conditions?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single CAN-FD bus for a medical device that carries both a safety-critical control message requiring delivery within 2 ms and high-volume telemetry data from multiple sensors. The engineer argues that CAN-FD's higher data rate in the data phase eliminates any bandwidth concerns. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging that CAN-FD does offer significantly higher data throughput than classic CAN, but then guide the team to look beyond raw bandwidth. The critical distinction is between throughput and determinism. The safety-critical message doesn't just need enough bandwidth — it needs guaranteed delivery within 2 ms regardless of what else is happening on the bus.

I'd walk the team through a structured analysis. First, calculate the worst-case bus utilization including all messages: the safety-critical message, all telemetry messages at their maximum rates, and any overhead like error frames or retransmissions. CAN-FD's arbitration phase still runs at the classic CAN bit rate, so the arbitration overhead doesn't benefit from the faster data phase. The question is whether the total utilization leaves enough idle time for the safety-critical message to always win arbitration when it needs to transmit.

Next, I'd examine the priority structure. In CAN-FD, the message identifier determines arbitration priority. The safety-critical message must have the highest priority — but that alone doesn't guarantee 2 ms delivery if lower-priority messages are long and the bus is busy. I'd ask the engineer to calculate the worst-case blocking time: the longest time the safety-critical message might wait for the bus to become idle, considering the longest possible lower-priority message and any error conditions.

I'd also raise the question of what happens under fault conditions. If a sensor node malfunctions and starts transmitting garbage or continuously asserting the bus, how does that affect the safety-critical message? CAN's error handling will eventually shut down a faulty node, but during that process, the bus might be disrupted. The design needs to consider whether the 2 ms requirement holds under these degraded conditions.

Finally, I'd suggest the team consider whether separating the safety-critical traffic onto a dedicated bus or using a different architecture might be simpler to validate. Sometimes the complexity of proving deterministic delivery on a shared bus isn't worth the cost savings of a single bus. The decision should be based on a documented analysis, not just a bandwidth calculation.

**Possible follow-ups:** How would you calculate the worst-case blocking time for the safety-critical message? What additional measures might you recommend if the analysis shows the 2 ms requirement can't be guaranteed?

---

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** The first priority is to address the immediate technical issue — the protocol error needs to be understood and fixed. I'd start by having the engineer walk me through their implementation and the test failure, not to assign blame but to understand the root cause. Was it a misunderstanding of the protocol specification, a misinterpretation of the requirements, or a subtle implementation bug? I'd work with them to develop a fix and a verification plan, and I'd also assess whether the error affects any other parts of the system or any other communication interfaces.

Once the technical path forward is clear, I'd address the process and team aspects. The schedule delay is real, and the project needs to recover. I'd work with the project manager to reassess the timeline, identify what can be parallelized or descoped, and communicate the impact to stakeholders. I'd also make sure the engineer understands that this is a learning opportunity, not a career-defining failure — but I'd also expect them to take ownership of the fix and the lessons learned.

Looking forward, I'd ask what process gaps allowed this error to go undetected until compliance testing. Was there insufficient review of the protocol implementation? Were the test cases inadequate? Should there have been earlier integration testing with the actual hardware? I'd lead a post-mortem to identify improvements — perhaps adding protocol conformance testing earlier in the development cycle, implementing more rigorous code reviews for communication protocol code, or creating a checklist for protocol implementation that includes edge cases like timing, error handling, and bus contention.

Finally, I'd think about how to prevent similar issues in the future. This might mean improving the design review process, adding simulation or hardware-in-the-loop testing earlier, or providing additional training for the junior engineer on the specific protocol. The goal is to turn a painful experience into a process improvement that benefits the whole team.

**Possible follow-ups:** How would you balance holding the engineer accountable with maintaining their motivation and confidence? What specific process changes would you propose to catch protocol implementation errors earlier in the development cycle?