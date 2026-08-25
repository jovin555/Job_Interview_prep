# protocols — Day 35

## Q1: How would you approach designing a fail-safe mechanism for a CAN-FD network where a sensor node must never transmit stale data after the main controller has lost communication, but the node itself continues to operate normally?

**Answer:** The core challenge here is distinguishing "controller is temporarily busy" from "controller is gone or unreachable," and ensuring the sensor node defaults to a safe state rather than continuing to publish data that may be acted upon incorrectly.

My approach would start with a heartbeat or watchdog mechanism at the application layer, layered on top of the CAN-FD transport. The main controller would periodically transmit a dedicated heartbeat message with a monotonically increasing sequence number. The sensor node tracks the time since the last valid heartbeat. If no heartbeat arrives within a defined timeout window — typically set to at least three times the nominal heartbeat period to tolerate jitter and bus retransmissions — the node transitions to a fail-safe state.

The critical design decision is what "fail-safe" means for the specific device. For a medical sensor node, this might mean: stop transmitting measurement data, latch the last known-good output to a safe value, assert a hardware signal to place an actuator in a safe position, and log the event locally. The node should also attempt re-synchronization — for example, entering a "seeking" mode where it listens for a new heartbeat or a specific wake-up command before resuming normal operation.

I would also consider a two-level timeout scheme. A short timeout detects a transient communication glitch and triggers a "degraded" mode where the node continues sampling but flags data as unvalidated. A longer timeout triggers full fail-safe shutdown. This prevents unnecessary system downtime from brief bus errors while still guaranteeing that stale data is never presented as fresh.

On the firmware side, I would implement this as a state machine with explicit transitions: Normal → Heartbeat Missed → Degraded → Fail-Safe, with hysteresis to prevent oscillation. The state machine should be independent of the main data acquisition task, ideally running from a timer interrupt or a dedicated RTOS thread with higher priority. I would also add a hardware watchdog that forces the node into a known state if the firmware itself hangs.

For the CAN-FD layer specifically, I would use a dedicated message ID for the heartbeat with the highest priority in the arbitration field, so it is never delayed behind lower-priority telemetry. The heartbeat should also carry a freshness counter or timestamp, and the node should verify that the counter is advancing — a repeated counter value is as suspicious as a missing one.

**Possible follow-ups:**
- How would you choose the heartbeat timeout value, and what factors would influence that decision?
- What happens when the controller recovers — how does the node re-synchronize without risking a burst of stale data being transmitted?

---

## Q2: You're debugging a system where an SPI bus communicates with three sensors on separate chip selects. The bus works correctly at 1 MHz but produces corrupted data at 10 MHz. How would you approach this?

**Answer:** This is a classic signal-integrity-versus-timing problem, and I would approach it systematically rather than guessing. The fact that it works at 1 MHz but fails at 10 MHz narrows the possibilities considerably — it's unlikely to be a logic error or protocol configuration issue, since those would typically fail at both speeds.

First, I would verify the basics: confirm that all three sensors actually support 10 MHz operation per their datasheets, and check that the microcontroller's SPI peripheral is configured correctly for the higher clock rate — including clock polarity and phase settings, which can interact with propagation delays differently at higher speeds.

Next, I would use an oscilloscope to probe the actual signals at the failing slave's pins, not just at the master. I'm looking for several specific things:

1. **Signal integrity:** Rise/fall times, ringing, overshoot, and undershoot on SCK, MOSI, and MISO. At 10 MHz, the bit period is 100 ns, so if the PCB traces have excessive capacitance or the pull-ups/pull-downs are too strong, the edges can become too slow or ring badly. I would check whether the MISO line from the sensor is driving against a weak pull-up or has a long stub.

2. **Setup/hold timing:** Even if the signals look clean, the sensor may need more setup time than the master provides at 10 MHz. I would check the sensor's datasheet for minimum SCK high/low times and data setup/hold requirements, then compare against the master's actual timing. If the master's SCK duty cycle is asymmetric, that can eat into the margin.

3. **Per-slave differences:** I would test each sensor individually at 10 MHz. If only one sensor fails, the problem is likely specific to that sensor's PCB trace routing, its input capacitance, or its MISO driver characteristics. If all three fail, the problem is more likely in the common bus — the master's drive strength, the SCK routing, or a shared trace that acts as a stub.

4. **Chip select behavior:** At higher speeds, the timing of chip select assertion/deassertion relative to SCK becomes more critical. If the chip select is asserted too late or deasserted too early relative to the first/last clock edge, the sensor may miss or corrupt the transaction. I would check the CS setup and hold times against the datasheet.

If the signals look clean and timing margins are adequate, I would then suspect a subtle issue like ground bounce or crosstalk between adjacent traces — particularly if the SPI bus runs parallel to other high-speed signals. In that case, I would look at the PCB layout and consider whether the return current path is clean, whether there's adequate ground stitching near the SPI traces, and whether series termination resistors (typically 22–33 Ω) are present near the master to dampen reflections.

Finally, I would consider whether the sensor's MISO output drive strength is configurable. Some sensors have programmable drive strength, and at 10 MHz a weak driver may not be able to charge the trace capacitance fast enough. Reducing the trace length, adding a series resistor near the sensor, or adjusting the drive strength setting could resolve it.

**Possible follow-ups:**
- What specific timing parameters would you measure on the oscilloscope to determine whether it's a setup or hold time violation?
- How would you decide between fixing the PCB layout versus reducing the SPI clock rate versus adding series termination resistors?

---

## Q3: How would you approach selecting between RS-422 and RS-485 for a medical device that needs to communicate with multiple sensors distributed across a patient monitoring system?

**Answer:** The first step is to clarify the actual system requirements, because RS-422 and RS-485 are electrically similar but have different strengths. Both use differential signaling, which gives good common-mode noise rejection — important in a clinical environment with electrosurgical equipment, motors, and other interference sources. But the key difference is topology: RS-422 is typically point-to-point or multi-drop with one driver and multiple receivers, while RS-485 supports multi-point with multiple drivers and receivers on the same bus.

For a patient monitoring system with multiple sensors, I would first ask: do the sensors need to transmit data back to the central unit, or do they only receive commands? If the sensors only receive (e.g., a display unit receiving data from a single central source), RS-422 could work. But in almost any real patient monitoring scenario, sensors need to send data back — so RS-485's multi-point capability with multiple drivers is the natural fit.

However, I would not make the decision on topology alone. I would evaluate:

1. **Number of nodes and cable length:** RS-485 supports up to 32 unit loads on a standard bus (more with reduced loading or repeaters), and can run hundreds of meters at lower baud rates. RS-422 is typically limited to one driver and up to 10 receivers. If the system has more than a few sensors, RS-485 wins.

2. **Duplex requirements:** RS-422 is typically full-duplex (separate transmit and receive pairs), while RS-485 is often half-duplex (shared pair with direction control). If the sensors need to send data while simultaneously receiving commands, full-duplex RS-422 per sensor might be simpler — but that requires a separate pair per sensor, which multiplies cabling. RS-485 half-duplex with a polled protocol is usually more practical for a multi-sensor system.

3. **Data rate vs. cable length:** Both standards have a trade-off between baud rate and cable length. For a patient monitoring system, the data rates are typically modest (tens of kilobits per second), so cable length is rarely a limiting factor. But I would still calculate the worst-case bit time versus round-trip propagation delay to ensure the protocol's timing (e.g., turn-around time in half-duplex) is feasible.

4. **Fault tolerance and fail-safe:** RS-485 has well-defined fail-safe biasing requirements to ensure receivers output a defined state when the bus is idle or open. This is critical in a medical device — a floating bus could be interpreted as a valid data bit and cause a sensor to act on garbage. I would ensure the bus has proper fail-safe biasing and termination.

5. **Isolation:** In a medical device with patient contact, galvanic isolation between the communication bus and the patient-connected circuitry is often required to meet leakage current limits. Both RS-422 and RS-485 can be isolated with digital isolators or optocouplers, but the choice affects how many isolation channels are needed — full-duplex RS-422 needs more channels than half-duplex RS-485.

In practice, for a multi-sensor patient monitoring system, I would likely choose RS-485 with a half-duplex, polled protocol — the master requests data from each sensor in turn, and sensors respond. This gives a single twisted-pair cable, multi-drop capability, good noise immunity, and well-understood fail-safe behavior. I would use RS-422 only if the system had a single sensor or if full-duplex operation was a hard requirement that couldn't be met with a separate control channel.

**Possible follow-ups:**
- How would you handle the half-duplex turn-around timing in RS-485 to avoid collisions when the master polls multiple sensors?
- What fail-safe biasing scheme would you use, and how would you calculate the resistor values?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single UART with a software-based protocol multiplexer to communicate with four different sensors, each with different baud rates and protocols. The hardware engineer argues this is unreliable and wants four separate UART peripherals. How would you guide the team to a decision?

**Answer:** I would frame this as a structured trade-off analysis rather than taking sides. The junior engineer's proposal has a legitimate appeal — it saves pins, PCB area, and cost. But the hardware engineer's concern about reliability is also valid, and in a medical device, reliability isn't just a nice-to-have — it's a regulatory requirement.

I would start by asking the team to quantify the actual requirements. What are the data rates, message sizes, and update frequencies for each sensor? What is the worst-case total bandwidth demand? What latency is acceptable for each sensor's data? This immediately tells us whether a single UART is even feasible from a throughput perspective. If the combined load exceeds, say, 50–60% of the UART's capacity, I would lean toward separate UARTs regardless of the software complexity.

Next, I would examine the "software-based protocol multiplexer" proposal more carefully. The key question is: what does the multiplexer actually do? If it's just a round-robin scheduler that reads from each sensor in turn, that's straightforward but introduces latency — each sensor waits while others are being serviced. If the sensors have different baud rates, the multiplexer must reconfigure the UART peripheral between each transaction, which adds overhead and creates windows where the UART is unavailable. If any sensor sends unsolicited data (rather than responding to polls), the multiplexer must handle asynchronous arrivals, which significantly complicates the design.

I would also probe the failure modes. What happens if one sensor's protocol gets stuck — does it block the other three? How do you handle a sensor that sends a malformed frame — does the multiplexer recover gracefully, or does it hang? In a medical device, a single sensor failure should not take down the entire communication subsystem. With four separate UARTs, each sensor is isolated; with a multiplexer, they share a single point of failure.

However, I would not dismiss the multiplexer outright. If the sensors are all polled, have modest data rates, and the total load is well within the UART's capacity, a multiplexer can be perfectly reliable — many industrial devices do exactly this. The decision hinges on the specific requirements and the team's ability to implement and test the multiplexer rigorously.

My guidance would be: start with the requirements, not the preferences. If the throughput and latency analysis shows the multiplexer is feasible, I would ask the junior engineer to produce a detailed design — including the scheduling algorithm, error handling, timeout behavior, and how they would test it under fault conditions. I would also ask the hardware engineer to quantify the cost of four UARTs: is it really a problem, or just a preference for simplicity? If the microcontroller has four UART peripherals available and the pin count is acceptable, the hardware engineer's approach is lower-risk and should be the default. The burden of proof should be on the multiplexer proposal to demonstrate that the savings justify the added complexity and risk.

In a medical device, I would likely end up recommending separate UARTs unless there's a compelling reason — such as a severe pin or cost constraint — because the reliability and testability benefits outweigh the marginal cost. But I would present this as a data-driven decision, not a veto.

**Possible follow-ups:**
- What specific criteria would you use to decide whether the multiplexer approach is acceptable?
- How would you structure the testing to verify the multiplexer's reliability under fault conditions?

---

## Q5: How would you approach developing a communication protocol test plan for a medical device that uses multiple interfaces (I2C, SPI, UART, and USB), where the test plan must verify both normal operation and fault tolerance, and the results need to be documented for regulatory submission?

**Answer:** A communication protocol test plan for a medical device has two distinct goals: proving the device works as intended, and proving it fails safely. Both need to be documented rigorously because the results will be part of the regulatory submission — likely referenced in the design verification section of the design history file.

I would structure the test plan in layers, starting with protocol conformance and moving up to system-level behavior.

**Layer 1: Protocol conformance testing.** For each interface, I would verify that the device correctly implements the protocol specification. For I2C, this means addressing, ACK/NACK behavior, clock stretching (if supported), and multi-master arbitration (if applicable). For SPI, it means clock polarity/phase modes, chip select timing, and data framing. For UART, it means baud rate accuracy, framing, parity, and break detection. For USB, it means descriptor correctness, enumeration, and endpoint behavior. I would use protocol analyzers or bus sniffers to capture traffic and compare against the expected behavior. This layer is largely automated and produces objective pass/fail results.

**Layer 2: Functional communication testing.** This verifies that data is correctly exchanged end-to-end. For each interface, I would define test cases that exercise normal operation: reading each sensor, writing configuration registers, streaming data, and handling the maximum expected message rates. I would also test boundary conditions — minimum and maximum message sizes, maximum bus load, and worst-case timing. The key is to verify not just that bytes are transferred, but that the application correctly interprets the data.

**Layer 3: Fault injection and robustness testing.** This is where the test plan gets interesting for a medical device. I would systematically inject faults and verify the device responds safely. Examples include: disconnecting a sensor mid-transaction, shorting bus lines, holding a line low (simulating a stuck device), sending malformed frames, exceeding the maximum message length, and simulating a slave that fails to respond. For each fault, I would verify that the device detects the error, enters a defined error state, and recovers appropriately — either by retrying, resetting the interface, or alerting the user. Critically, I would verify that no fault causes the device to present corrupted data as valid.

**Layer 4: Extended duration and environmental testing.** Intermittent failures often only appear after hours of operation or under specific environmental conditions. I would run continuous communication tests for extended periods — typically 72 hours or more — while monitoring for bit errors, missed messages, or hangs. I would also test at temperature extremes and under electrical noise injection (e.g., ESD, radiated immunity) to verify the communication links remain robust.

For regulatory documentation, I would create a traceability matrix linking each test case to the specific requirement it verifies — whether from the protocol specification, the system requirements, or the risk management file. Each test case would include: objective, setup, procedure, pass/fail criteria, results, and any deviations. I would also document the test equipment (analyzers, oscilloscopes, fault injectors) and its calibration status.

One important consideration: the test plan should be written before the implementation is complete, so that testability is designed in from the start. For example, the firmware should expose test hooks — such as the ability to inject a fake sensor failure or log protocol errors — so that fault injection doesn't require physical manipulation of the bus.

**Possible follow-ups:**
- How would you prioritize which fault conditions to test, given that you can't test every possible failure mode?
- How would you handle a test failure discovered late in the process — what documentation and corrective action process would you follow?