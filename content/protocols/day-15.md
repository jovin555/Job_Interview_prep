# protocols — Day 15

## Q1: How would you approach designing a power-over-data-line scheme for an RS-485 bus in a medical sensor network, where remote nodes need to be powered from the same cable without compromising signal integrity?

**Answer:** Power-over-data-line for RS-485 is an attractive option in medical sensor networks because it eliminates separate power cabling, reduces connector complexity, and simplifies sterilization and cable management. However, it introduces several challenges that need careful consideration.

First, I'd evaluate whether the application truly needs power-over-data or whether a separate power pair in the same cable would be simpler. If power-over-data is required, the fundamental issue is that RS-485 is a differential, balanced signaling scheme, and injecting DC power onto the same conductors changes the common-mode voltage and can degrade the differential signal.

The standard approach is to use a center-tapped transformer or inductor-based injection at each end. The DC power is applied to the center tap of the transformer, and the AC data signal passes through the transformer windings. This keeps the DC and AC paths separated while sharing the same physical conductors. The inductors need to have sufficient impedance at the data frequency to prevent the power supply from loading the signal, but low enough DC resistance to minimize voltage drop over the cable run.

Key design considerations include:

- **Cable selection**: The cable's characteristic impedance, DC resistance, and capacitance all matter. A higher-resistance cable will have more voltage drop, which affects both the power delivery and the common-mode voltage seen by the transceivers.
- **Common-mode voltage range**: RS-485 transceivers typically have a common-mode range of -7V to +12V. Injecting power onto the line shifts the common-mode voltage, and you need to ensure the transceivers still operate within their specified range.
- **Fault isolation**: In a medical device, you need to consider what happens if a node shorts the bus or if the cable is damaged. Power injection circuits should have current limiting and fault detection.
- **EMI/EMC**: The power injection network can affect the radiated emissions profile of the system. The transformer or inductor approach helps, but you may need additional filtering.

For a medical device, I'd also consider isolation requirements. If the bus is powered from the same supply as the sensor nodes, you need to think about patient leakage current paths and whether galvanic isolation is required between the bus and the patient-connected portions of the system.

**Possible follow-ups:**
- How would you determine the maximum number of nodes and cable length for a given power budget?
- What happens to the data signal when a node is hot-plugged onto the bus, and how would you handle that?

---

## Q2: You're debugging a system where a UART peripheral on a microcontroller occasionally generates a framing error during reception, but only when the device is operating at elevated temperature. The baud rate is 115200 and the clock source is an internal RC oscillator. How would you approach this?

**Answer:** This is a classic temperature-dependent timing issue. The key clue is that the problem appears only at elevated temperature, which strongly suggests a clock accuracy or drift problem rather than a signal integrity issue.

The first thing I'd check is the accuracy specification of the internal RC oscillator across temperature. Many microcontrollers specify their internal RC oscillator accuracy as ±1-3% at room temperature, but this can degrade to ±5% or worse over the full temperature range. At 115200 baud, the UART receiver typically tolerates about ±2-3% bit-time error before framing errors occur, depending on the oversampling ratio and the number of bits per frame.

I'd approach this systematically:

1. **Verify the clock source**: Check the datasheet for the RC oscillator's temperature coefficient. If it's marginal, the fix is to switch to an external crystal or ceramic resonator, which has much better temperature stability (typically ±10-50 ppm).

2. **Measure the actual baud rate**: Use a logic analyzer or oscilloscope to measure the actual bit timing at both room temperature and elevated temperature. This confirms whether the clock is drifting.

3. **Check the UART configuration**: Verify the oversampling setting. Some UARTs support 16x or 8x oversampling. Higher oversampling gives better tolerance to clock mismatch. Also check if the UART has a fractional baud rate generator that could be misconfigured.

4. **Consider the receiver tolerance**: The UART receiver's tolerance to baud rate mismatch depends on the number of bits per frame. A frame with 8 data bits, no parity, and 1 stop bit has a total of 10 bit periods. The receiver samples each bit at the midpoint, so the cumulative timing error over the frame is what matters. If the transmitter and receiver clocks are both drifting in opposite directions, the error compounds.

5. **Look at the system-level design**: If the device is battery-powered and the temperature rise is self-induced (e.g., from the processor or power circuitry), the thermal design might need attention. But the more robust fix is to use a more accurate clock source.

For a medical device, this is particularly important because intermittent communication failures can have clinical consequences. I'd recommend using an external crystal for the UART clock if the internal oscillator doesn't meet the required accuracy across the operating temperature range. I'd also add a self-test or diagnostic that monitors for framing errors and can alert the system to potential clock issues.

**Possible follow-ups:**
- How would you determine the maximum acceptable baud rate error for a given UART configuration?
- What other temperature-dependent factors could cause framing errors, and how would you distinguish them from clock drift?

---

## Q3: How would you approach implementing a deterministic scheduling scheme for a mixed-protocol medical device that uses I2C for sensor reads, SPI for high-speed data logging, and UART for a user interface, all on a single microcontroller running Zephyr RTOS?

**Answer:** This is fundamentally a real-time scheduling problem. The challenge is that each protocol has different timing characteristics and priorities, and they share a single CPU and potentially shared resources like DMA channels or interrupt controllers.

My approach would start with a requirements analysis:

1. **Characterize each protocol's timing requirements**:
   - I2C sensor reads: typically periodic, with latency requirements in the milliseconds range. I2C is relatively slow (100-400 kHz), so each transaction takes a predictable amount of time.
   - SPI data logging: potentially high-throughput, but may be bursty. The critical requirement is often sustained throughput rather than low latency.
   - UART user interface: typically event-driven, with low data rates but potentially strict latency requirements for user feedback.

2. **Map these to Zephyr's scheduling primitives**:
   - For periodic I2C reads, I'd use a kernel timer or a dedicated thread with a sleep interval. The thread priority should reflect the criticality of the sensor data.
   - For SPI logging, I'd consider using DMA to offload the CPU and avoid blocking the scheduler. Zephyr supports DMA-based SPI transfers, which can be queued.
   - For UART, I'd use interrupt-driven or DMA-based reception with a ring buffer, and a thread that processes incoming commands.

3. **Identify shared resources and contention points**:
   - If the I2C and SPI peripherals share a DMA controller, you need to ensure that high-priority transfers aren't blocked by lower-priority ones.
   - Interrupt priorities need to be configured so that time-critical protocol handling isn't preempted by less critical work.
   - If any protocol uses a shared bus (e.g., multiple I2C devices), you need to manage bus access to avoid conflicts.

4. **Use Zephyr's synchronization primitives**:
   - Mutexes or semaphores to protect shared resources.
   - Message queues to decouple protocol handling from application logic.
   - Condition variables or events to signal completion of asynchronous operations.

5. **Consider the power implications**: In a battery-powered device, you want to minimize the time the CPU is active. This means batching I2C reads, using DMA for SPI, and putting the CPU to sleep when possible. Zephyr's power management framework can help here.

6. **Validate the design**: I'd create a timing analysis that shows worst-case latency for each protocol under all combinations of activity. This might involve calculating the maximum time the I2C bus is held, the maximum SPI transfer time, and the UART interrupt service time, then verifying that the sum of all worst-case times fits within the required deadlines.

For a medical device, I'd also add monitoring and diagnostic capabilities — for example, tracking missed deadlines, bus errors, or buffer overruns — so that any scheduling issue is visible during testing and in the field.

**Possible follow-ups:**
- How would you decide between using a dedicated thread per protocol versus a single event-loop architecture?
- How would you handle the case where an I2C sensor holds the bus with clock stretching for longer than expected?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single CAN-FD bus to connect a central controller to three sensor modules, each with its own microcontroller, in a medical device. The engineer argues that CAN-FD's higher data rate eliminates the need for careful bus utilization analysis. How would you guide the team to evaluate this approach?

**Answer:** This is a common misconception about CAN-FD. While CAN-FD does offer higher data rates in the data phase (up to 8 Mbps in some implementations, compared to 1 Mbps for classic CAN), the arbitration phase is still limited to 1 Mbps, and the overall bus utilization depends on many factors beyond raw bit rate.

I'd guide the team through a structured evaluation:

1. **Clarify the actual requirements**: What is the message set? What are the periodicity, size, and deadline for each message? What is the worst-case latency requirement for safety-critical messages? What happens if a message is delayed or lost?

2. **Calculate the actual bus load**: CAN-FD's efficiency depends on the ratio of arbitration phase to data phase. For short messages, the overhead of the arbitration phase dominates, and the effective throughput gain over classic CAN is modest. For example, a 64-byte message at 8 Mbps data phase might only achieve 2-3x the throughput of classic CAN, not 8x, because the arbitration phase and inter-frame spacing still consume time.

3. **Consider the error handling**: CAN-FD has more complex error handling than classic CAN. If a node detects an error, it can trigger an error frame, which forces the bus to re-arbitrate. Under high bus load, this can lead to error storms that degrade performance significantly.

4. **Think about the network topology**: The physical layer for CAN-FD at high data rates is more demanding. The maximum bus length decreases as the data phase bit rate increases. At 8 Mbps, the maximum stub length is very short, and the bus length is limited to a few meters. In a medical device with three sensor modules, this might be acceptable, but it needs to be verified.

5. **Evaluate the determinism requirements**: CAN-FD uses the same priority-based arbitration as classic CAN, so higher-priority messages always win arbitration. However, the worst-case latency for a given message depends on the maximum blocking time from lower-priority messages and the error recovery time. This needs to be analyzed using real-time scheduling theory (e.g., response-time analysis for CAN).

6. **Consider the implementation complexity**: CAN-FD requires more sophisticated transceivers and controllers. The firmware for handling CAN-FD's flexible data rate switching, E2E CRC, and error handling is more complex than classic CAN.

My guidance would be: don't assume CAN-FD solves the problem. Do the analysis. Calculate the worst-case bus load, the worst-case latency for each message, and the impact of errors. If the analysis shows the bus is under 50-60% load with margin for errors, the approach is viable. If not, consider alternatives like using two buses, reducing message sizes, or using a different protocol.

For a medical device, I'd also emphasize the importance of documenting the analysis and the assumptions behind it, as this will be part of the design history file and may be reviewed during regulatory audits.

**Possible follow-ups:**
- How would you calculate the worst-case latency for a high-priority message on a CAN-FD bus?
- What are the key differences between classic CAN and CAN-FD that affect bus utilization analysis?

---

## Q5: How would you approach developing a protocol conformance test plan for a medical device that uses multiple communication interfaces (I2C, SPI, UART, and USB), where the test plan needs to verify both protocol correctness and robustness against real-world fault conditions?

**Answer:** A protocol conformance test plan for a medical device needs to address two distinct aspects: verifying that the implementation correctly follows the protocol specifications, and verifying that it behaves safely and predictably under fault conditions. Both are critical for regulatory compliance and patient safety.

My approach would be structured in layers:

**Layer 1: Protocol-level conformance testing**
- For each protocol, I'd create test cases that verify the implementation against the relevant specification. For I2C, this includes addressing, ACK/NACK behavior, clock stretching, repeated starts, and bus arbitration. For SPI, it includes clock polarity/phase modes, chip select timing, and data framing. For UART, it includes baud rate accuracy, framing, parity, and break conditions. For USB, it includes enumeration, descriptor parsing, endpoint behavior, and suspend/resume.
- These tests should be automated where possible, using test equipment that can generate and analyze protocol traffic. For example, a logic analyzer for I2C/SPI/UART, and a USB protocol analyzer for USB.

**Layer 2: Fault injection testing**
- This is where you verify robustness. I'd systematically inject faults and verify the device responds safely:
  - **Electrical faults**: Short circuits on data lines, open connections, voltage spikes, ground bounce, and common-mode voltage shifts.
  - **Protocol faults**: Malformed frames, incorrect addresses, unexpected NACKs, missing ACKs, clock stretching beyond the timeout, and bus contention.
  - **Timing faults**: Delayed responses, premature responses, and baud rate mismatch.
  - **Power faults**: Brownouts, power glitches, and power loss during communication.
- For each fault, I'd define the expected behavior: the device should either recover gracefully, enter a safe state, or generate an appropriate error indication. It should never hang, corrupt data, or behave unpredictably.

**Layer 3: Stress and endurance testing**
- Long-duration testing to catch intermittent issues. This includes running the device for extended periods (hours to days) while monitoring for communication errors, memory leaks, or resource exhaustion.
- Temperature and humidity cycling to verify that protocol behavior is stable across environmental conditions.

**Layer 4: System-level integration testing**
- Testing the interaction between protocols. For example, what happens when a UART command arrives while an I2C transaction is in progress? What happens if the USB host disconnects during a firmware update over SPI?

For a medical device, I'd also emphasize traceability: each test case should be linked to a requirement, and the test results should be documented in the design history file. The test plan should be reviewed and approved before execution, and any failures should be tracked through a formal corrective action process.

I'd also recommend building testability into the firmware design — for example, adding debug hooks that allow test software to inject faults or monitor internal state. This makes the testing more efficient and thorough.

**Possible follow-ups:**
- How would you prioritize which fault conditions to test, given limited time and resources?
- How would you handle a situation where a fault injection test reveals a bug that only occurs intermittently?