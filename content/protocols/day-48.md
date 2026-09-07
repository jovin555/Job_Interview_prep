# protocols — Day 48

## Q1: How would you approach designing a bus architecture for a medical device where one sensor module requires deterministic, low-latency communication (e.g., a pressure sensor used in a closed-loop control application) while another module generates high-volume telemetry that can tolerate delay, and both need to coexist on the same physical network?

**Answer:** I'd start by separating the requirements into what I call "hard real-time" versus "soft real-time" traffic, then evaluate whether a single shared bus can honestly satisfy both. For the deterministic sensor, the key parameters are worst-case latency, jitter, and guaranteed delivery — not average throughput. For the telemetry, the concern is sustained bandwidth and buffer management.

If I'm considering CAN-FD, the arbitration mechanism inherently prioritizes lower identifier values, so I could assign the safety-critical pressure messages the lowest IDs and verify through worst-case response-time analysis that even under maximum bus loading from telemetry, the critical message meets its deadline. This analysis must account for the arbitration phase bit rate, the data phase bit rate, and the maximum number of bits a higher-priority message could occupy.

However, I'd also question whether mixing both traffic classes on one bus is the right call at all. A cleaner architecture might use separate physical channels — for example, a dedicated point-to-point link for the control loop and a shared bus for telemetry. This avoids the complexity of proving worst-case timing on a shared medium and simplifies the safety case. The trade-off is additional cabling, connectors, and board space.

If a single bus is unavoidable, I'd implement a time-triggered or schedule-based approach where the deterministic sensor gets a guaranteed time slot, and telemetry fills the remaining bandwidth. This requires careful clock synchronization and protocol design, but it makes the timing analysis much more tractable than pure event-driven arbitration. I'd also build in a bus load monitor that can detect when utilization approaches the analyzed limit and trigger an alarm or degrade telemetry gracefully.

**Possible follow-ups:** How would you verify your worst-case latency analysis for the deterministic message? What happens to the telemetry data if the bus becomes congested — should it be dropped, buffered, or rate-limited?

---

## Q2: You're debugging a system where a UART link between a microcontroller and a wireless module works reliably at 9600 baud but produces frequent framing errors at 115200 baud. The link is approximately 10 centimeters on the same PCB. How would you approach this?

**Answer:** Since the distance is very short and on the same PCB, I'd first rule out signal integrity issues like reflections or crosstalk — at 10 centimeters, those are unlikely to be the primary cause at 115200 baud. The more probable culprit is clock accuracy and baud rate tolerance.

At 115200 baud, each bit is approximately 8.68 microseconds. If the microcontroller is using an internal RC oscillator with, say, ±2% accuracy, that's about ±173 nanoseconds per bit — which alone might be acceptable. But the real question is the combined error budget across both the transmitter and receiver, plus any asymmetry in the oscillator. UART typically tolerates about ±3-5% total error depending on the number of bits per frame and where sampling occurs within each bit.

I'd check what clock source each device is actually using. If the wireless module has a crystal oscillator but the microcontroller is running from an internal RC, I'd measure the actual baud rate on a scope or logic analyzer rather than trusting the configured value. Temperature drift could also be a factor if the system has been running for a while and heating up.

I'd also examine the framing error pattern — are errors occurring consistently at a particular byte position, or randomly? If they're consistent, it suggests a systematic clock offset. If random, I'd look at noise coupling from the wireless module's RF section during transmission, which could corrupt the receive signal at higher bit rates where the sampling window is narrower.

The fix might be switching the microcontroller to a higher-accuracy clock source, adjusting the UART baud rate generator to minimize error, or if the module supports it, using a synchronized baud rate configuration. I'd also verify the actual signal levels and edge rates with an oscilloscope to ensure the waveform is clean at the higher data rate.

**Possible follow-ups:** How would you determine whether the problem is clock accuracy versus noise? What if the framing errors only occur when the wireless module is actively transmitting?

---

## Q3: How would you approach implementing a protocol conversion gateway between a legacy RS-485 network using a proprietary binary protocol and a modern CAN-FD network, where the gateway must handle different data rates, message priorities, and error handling semantics between the two sides?

**Answer:** I'd approach this as a system design problem with three layers: the physical interface layer, the protocol translation layer, and the application semantics layer.

At the physical layer, the gateway needs independent transceivers for each bus — RS-485 transceivers with appropriate termination and fail-safe biasing on one side, and CAN-FD transceivers on the other. The gateway microcontroller needs sufficient buffering because the data rates and message sizes differ significantly between the two networks.

The protocol translation layer is where the real complexity lives. The legacy RS-485 protocol likely has its own framing, addressing, and checksum scheme, while CAN-FD has identifiers, DLC encoding, and CRC. I'd map legacy message types to CAN-FD identifiers, preserving priority semantics — if the legacy protocol has message priorities, those need to map to CAN-FD arbitration IDs in a way that preserves the relative ordering. This mapping needs to be documented and reviewed carefully because it's a common source of subtle bugs.

The error handling semantics are particularly tricky. RS-485 has no inherent error detection — that's typically in the protocol layer with checksums and retries. CAN-FD has hardware CRC and error confinement. The gateway must decide how to translate errors: if a legacy node fails to acknowledge, does the gateway generate a CAN-FD error frame? If a CAN-FD message is rejected due to CRC failure, how does that propagate back to the legacy side? I'd design a clear error propagation policy that doesn't silently drop messages on either side.

I'd also consider timing. The gateway introduces latency, and if the legacy protocol has timeouts, the gateway must respond quickly enough to avoid triggering them. This might require careful interrupt handling and DMA to minimize processing delay. For safety-critical medical applications, I'd also add health monitoring — the gateway should be able to detect if either bus is degraded and report its own status.

Finally, I'd build a test harness that simulates both sides, allowing me to verify message translation correctness, timing behavior, and error handling before integration with the actual devices.

**Possible follow-ups:** How would you handle a situation where a message is successfully received on the RS-485 side but cannot be transmitted on the CAN-FD side due to bus-off or arbitration loss? What metrics would you monitor to assess gateway health?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single I2C bus at 400 kHz with clock stretching enabled to connect a real-time pressure sensor and a high-volume data logger in a medical device. The pressure sensor requires deterministic read intervals, and the data logger can stretch the clock for up to 5 milliseconds during writes. How would you guide the team to evaluate this approach?

**Answer:** I'd guide the team to evaluate this proposal by first quantifying the conflict between the two requirements. The pressure sensor needs deterministic read intervals — meaning the time between read requests must be bounded and predictable. The data logger can stretch the clock for up to 5 milliseconds during writes, which means during that stretch, the entire I2C bus is held — no other device can communicate. If a pressure sensor read is attempted during a data logger write stretch, the read will be delayed by up to 5 milliseconds, which likely violates the determinism requirement.

I'd ask the junior engineer to calculate the worst-case bus occupancy: how often does the data logger write, and for how long? If it writes frequently, the bus could be unavailable for a significant fraction of the time. Even if the average utilization looks acceptable, the worst-case delay for the pressure sensor read is what matters for determinism.

I'd also raise the issue of clock stretching as a fault-containment concern. If the data logger's firmware crashes while it's stretching the clock, the entire bus hangs indefinitely. In a medical device, this creates a single point of failure. I'd ask what watchdog or timeout mechanism would detect and recover from a stuck bus.

The better architecture might be to put the pressure sensor on its own I2C bus (or use a different interface like SPI) so its timing is independent of the data logger's behavior. Alternatively, if both must share the bus, I'd require the data logger to buffer its writes and only write during scheduled windows that don't conflict with pressure sensor reads — but this adds complexity and still doesn't fully eliminate the risk of a stuck bus.

I'd also challenge the assumption that I2C is the right choice for the data logger at all. If it's generating high-volume data, SPI might be more appropriate since it has no clock stretching, no arbitration, and can run at higher speeds. The design review should question whether the bus topology is being driven by convenience rather than requirements.

**Possible follow-ups:** What specific analysis would you require before approving a shared-bus design? How would you test for the worst-case timing scenario?

---

## Q5: How would you approach developing a communication protocol test plan for a medical device that uses multiple interfaces (I2C, SPI, UART, and USB), where the test plan must verify both normal operation and fault tolerance, and the results need to be documented for regulatory submission?

**Answer:** I'd structure the test plan around three pillars: protocol conformance testing, fault injection testing, and extended duration reliability testing — with each pillar producing documented evidence suitable for a regulatory submission.

For protocol conformance, I'd use protocol analyzers and test equipment to verify that each interface operates within its specification. For I2C, this means checking addressing, ACK/NACK behavior, clock stretching limits, and bus timing at the configured speed. For SPI, I'd verify clock polarity and phase settings, chip select timing, and data integrity across all slaves. For UART, I'd check baud rate accuracy, framing, parity, and flow control behavior. For USB, I'd use a USB protocol analyzer to verify descriptor correctness, endpoint behavior, and enumeration compliance across multiple host controllers.

For fault tolerance, I'd systematically inject faults and verify the device responds safely. This includes: disconnecting and reconnecting each interface mid-communication; shorting signal lines to power and ground; introducing noise on the bus (using coupling equipment); forcing protocol violations (e.g., invalid I2C addresses, SPI frames with wrong CPOL/CPHA); and simulating slave device failures (e.g., a sensor that stops ACKing). For each fault, I'd document the device's response — it should detect the fault, enter a safe state, and either recover automatically or alert the user, depending on the severity.

For extended duration testing, I'd run the device continuously for days or weeks while monitoring for intermittent failures. This is where subtle issues like clock drift, buffer overflows, or memory leaks often surface. I'd log all communication errors, even those that are automatically recovered, because the pattern of errors can reveal root causes.

For regulatory documentation, I'd organize results in a traceability matrix that links each test case to the specific requirement it verifies. Each test case would include the test setup, procedure, pass/fail criteria, raw data, and conclusion. I'd also document any deviations or anomalies and their resolution. The key is that the test plan is defined before testing begins — not after — so the evidence is objective and complete.

**Possible follow-ups:** How would you prioritize which fault conditions to test when time is limited? How would you handle a fault injection test that causes the device to enter an unsafe state?