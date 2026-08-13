# protocols — Day 23

## Q1: How would you approach designing a communication architecture for a medical device where a central controller needs to communicate with multiple sensor modules, some requiring deterministic real-time response and others generating high-volume data, while keeping the system modular and testable?

**Answer:** I'd start by separating the requirements for each sensor class rather than trying to find one protocol that does everything. For deterministic, safety-critical sensors, I'd look at protocols with bounded latency guarantees — CAN-FD is often a good fit because the arbitration mechanism provides priority-based access with predictable worst-case timing. For high-volume data, I'd consider a higher-bandwidth point-to-point link like SPI or USB, or a dedicated data channel that doesn't compete with control traffic.

The key architectural decision is whether to use a single shared bus or separate physical channels. A single bus simplifies cabling and connector design but forces you to do worst-case bus utilization analysis that includes both the deterministic and high-volume traffic. If the high-volume data would consume more than roughly 30–40% of bus bandwidth, I'd lean toward separating it onto its own channel so the control traffic isn't affected by data bursts.

For modularity, I'd define a protocol abstraction layer at the firmware level — each sensor module presents a standard interface (init, read, write, configure, status) regardless of the underlying transport. This lets you swap physical interfaces without touching application code. For testability, I'd build a hardware-in-the-loop test fixture that can inject faults (bus errors, missing acknowledgments, corrupted frames) and verify that the system degrades safely. I'd also include a debug mode that logs all bus traffic with timestamps, which is invaluable when intermittent issues appear during integration.

**Possible follow-ups:**
- How would you decide whether to use a single bus or separate channels for control and data traffic?
- What metrics would you use to validate that the deterministic latency requirement is actually met?

---

## Q2: You're debugging a system where a USB 2.0 device enumerates correctly on most hosts but fails on a specific embedded host controller. The device uses a composite descriptor with both HID and vendor-specific interfaces. How would you approach this?

**Answer:** I'd approach this systematically, starting with the most common causes of host-specific enumeration failures. First, I'd capture the full enumeration traffic with a USB protocol analyzer on both a working host and the failing host to compare the exact sequence of control transfers. The difference often reveals whether the issue is in the descriptor content, timing, or host behavior.

Common culprits include: the device responding too slowly to control transfers (the embedded host may have a shorter timeout), the device not handling a specific standard request that the host sends (some hosts probe for optional features), or the composite descriptor structure being slightly non-standard. I'd also check whether the device properly handles bus reset and re-enumeration, since some embedded hosts reset the bus more aggressively.

If the analyzer shows the host is requesting a descriptor the device isn't prepared to serve — for example, a device qualifier descriptor or a particular string descriptor index — I'd fix the firmware to respond correctly to all standard requests, even ones the device doesn't strictly need. I'd also verify that the device handles zero-length packets correctly and that the configuration descriptor's total length field is accurate. Finally, I'd test with the embedded host's specific USB stack documentation in hand, since some stacks have known quirks around composite devices.

**Possible follow-ups:**
- What specific standard requests might an embedded host send that a desktop host doesn't?
- How would you verify that the device handles bus resets gracefully?

---

## Q3: How would you approach implementing a deterministic scheduling scheme for a mixed-protocol medical device that uses I2C for sensor reads, SPI for high-speed data logging, and UART for a user interface, all on a single microcontroller running Zephyr RTOS?

**Answer:** I'd approach this by first classifying each communication channel by its timing requirements. The I2C sensor reads likely have a required sampling rate with bounded jitter; the SPI data logging is high-throughput but may tolerate some buffering; the UART user interface is event-driven with no hard real-time constraint.

In Zephyr, I'd use a combination of RTOS primitives: a high-priority thread for the I2C sensor reads driven by a hardware timer or a sensor's data-ready interrupt, a medium-priority thread for SPI logging that drains a DMA buffer, and a low-priority thread for UART handling. The key is to avoid blocking the high-priority thread on lower-priority work — I'd use interrupt-driven or DMA-based transfers with semaphores to signal completion, rather than polling or busy-waiting.

For the I2C reads specifically, I'd consider whether clock stretching by the sensor could cause priority inversion. If a sensor stretches the clock, the I2C peripheral is occupied and the thread waiting on it blocks. I'd design the scheduling so that the I2C transaction has a bounded timeout, and if a sensor fails to respond, the system logs the error and continues with the next sample rather than hanging indefinitely.

I'd also use Zephyr's priority-based preemptive scheduling carefully — making sure that interrupt handlers do minimal work and defer processing to threads, and that shared resources (like the SPI peripheral if it's also used for other purposes) are protected with mutexes or the Zephyr equivalent. Finally, I'd add a watchdog that monitors the health of each communication thread, so that if any channel stops making progress, the system can take a safe action.

**Possible follow-ups:**
- How would you handle the case where an I2C sensor's clock stretching blocks the bus for longer than your timeout?
- What Zephyr-specific mechanisms would you use to ensure the SPI logging thread doesn't starve the UART thread?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single RS-485 bus for a medical device system with 24 sensor nodes distributed along a 200-meter cable run. The system needs to poll each sensor every 50 ms, and each sensor responds with 32 bytes of data. The engineer argues that at 115200 baud, the bus can handle the throughput. How would you guide the team to evaluate this approach?

**Answer:** I'd guide the team to work through the actual timing budget rather than just the raw throughput calculation. Let's do the math: at 115200 baud, each byte takes approximately 87 microseconds (10 bits per byte including start and stop bits). A 32-byte response takes about 2.8 milliseconds. With 24 sensors, that's about 67 milliseconds of pure data transmission per poll cycle — already exceeding the 50 ms budget before accounting for any overhead.

But the real issue is the overhead the engineer hasn't considered. Each poll requires a request frame from the master (at least a few bytes), plus turn-around time for the bus to switch direction in half-duplex mode. RS-485 transceivers have driver enable/disable times, and you need to account for propagation delay on a 200-meter cable — roughly 1 microsecond per 200 meters, but the bigger factor is the turn-around time, which is typically 10–100 microseconds per direction switch depending on the transceiver. With 24 sensors, that's 48 direction switches per poll cycle. Even at 50 microseconds each, that's 2.4 milliseconds of overhead — manageable, but it adds up.

The more significant concern is that the 50 ms poll interval is a hard requirement, and the calculation shows the bus is already near capacity with zero margin for retries, error handling, or any additional traffic. I'd guide the team to consider: what happens when a sensor doesn't respond and needs a retry? What about a broadcast command or a firmware update? The system has no headroom.

I'd suggest the team evaluate alternatives: increasing the baud rate (though this reduces noise immunity on a long run), splitting the sensors across two buses, or using a protocol like CAN-FD that handles multi-node communication more efficiently. I'd also ask the engineer to produce a worst-case timing analysis that includes all overhead, not just the raw data bytes, and to identify what margin remains for error handling.

**Possible follow-ups:**
- What baud rate would you consider acceptable for a 200-meter RS-485 run, and why?
- How would you handle the scenario where one sensor consistently fails to respond within the poll window?

---

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** I'd approach this in two phases: first, address the immediate technical issue and get the project back on track; second, use it as a learning opportunity to prevent similar issues in the future.

For the immediate issue, I'd first ensure the compliance testing failure is fully understood — was it a protocol conformance issue, an EMC-related problem, or something else? I'd work with the engineer to reproduce the failure, identify the root cause, and develop a fix. The priority is to get the fix implemented and re-testing scheduled as quickly as possible, while keeping the regulatory body informed of the situation and the corrective action plan.

For the second phase, I'd have a private conversation with the engineer to understand how the error occurred — was it a misunderstanding of the protocol specification, a lack of test coverage, or pressure to meet a deadline? I'd focus on the process gaps rather than blaming the individual. The key question is: why didn't our existing verification process catch this before compliance testing? If the answer is that we relied too heavily on the engineer's self-testing, then we need to add independent verification — for example, a peer review of the protocol implementation against the spec, or a protocol conformance test using a commercial test tool.

I'd also review whether our design review process adequately covers communication protocol implementations, and whether we need to add protocol-specific checklists. The goal is to turn the schedule delay into a process improvement that prevents recurrence, while being supportive of the junior engineer — they need to learn from this without feeling that one mistake defines their career.

**Possible follow-ups:**
- How would you communicate this delay to project stakeholders and the regulatory body?
- What specific process changes would you propose to catch protocol implementation errors earlier in the development cycle?