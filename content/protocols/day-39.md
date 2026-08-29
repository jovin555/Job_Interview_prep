# protocols — Day 39

## Q1: How would you approach designing a USB 2.0 device that must support selective suspend while maintaining a periodic sensor data stream, given that the host may enter suspend mode at any time?

**Answer:** The first step is to understand that USB selective suspend is a host-initiated state, not something the device controls. The device must be designed to respond correctly when the host suspends the bus, but the real design question is what happens to the sensor data during that suspended period.

I would approach this by first defining the system-level requirement: does the sensor data need to be continuously captured during suspend, or is it acceptable to pause acquisition? If continuous capture is required, the device needs local buffering or storage. The firmware architecture would use a suspend/resume callback mechanism — in Zephyr RTOS, for example, you'd register USB device suspend and resume handlers. On suspend, the application layer would be notified so it can decide whether to keep the sensor powered and buffer data, or enter a lower-power state itself.

For the USB configuration itself, I'd ensure the device descriptor correctly advertises remote wakeup capability if the device needs to wake the host. The configuration descriptor should include the bmAttributes field with the remote wakeup bit set. The firmware must handle the resume interrupt and re-establish any state that was lost during suspend — for example, re-initializing the isochronous or interrupt endpoint scheduling.

A critical detail is that during suspend, the device must draw no more than the suspend current limit (typically 2.5 mA for unconfigured, 500 µA for suspended high-power devices). This means the firmware must actively manage power — shutting down non-essential peripherals, potentially reducing sensor sampling rate, and ensuring the USB transceiver is in its low-power state. The sensor itself might need to be powered from a separate rail that can be switched off, or the firmware might need to use a lower-power sensor mode during suspend.

I would also consider whether the device should signal a remote wakeup when its internal buffer approaches capacity, or whether it should simply discard data and log an overrun condition. That decision depends on the medical application's data integrity requirements.

**Possible follow-ups:** How would you handle the case where the host never resumes, but the device needs to continue monitoring? What are the implications for battery life if the device stays in suspend for extended periods?

---

## Q2: You're debugging a system where an RS-485 network with 16 nodes works reliably at 9600 baud but experiences intermittent corruption at 115200 baud over a 150-meter cable run. How would you approach isolating the root cause?

**Answer:** This is a classic symptom of a system that's marginal at higher data rates, and I'd approach it systematically rather than jumping to a single fix.

First, I'd characterize the failure more precisely. Is the corruption random single-bit errors, or is it burst errors affecting multiple bytes? Are certain nodes more affected than others? Does the failure correlate with specific cable segments or node positions? This data helps narrow the cause.

The most likely culprits at higher baud rates are signal integrity issues. At 115200 baud over 150 meters, the bit time is about 8.7 microseconds, and the cable's propagation delay becomes significant. I'd check the termination resistors first — are they properly matched to the cable's characteristic impedance, and are they placed at both physical ends of the bus? Incorrect or missing termination causes reflections that manifest as bit errors at higher rates.

Next, I'd examine the fail-safe biasing. At higher baud rates, the time between driver enable and the first valid data bit is shorter, so if the bus isn't properly biased to a known idle state, the receiver might interpret noise as data. I'd verify the bias resistors are sized correctly for the number of nodes on the bus — more nodes mean lower differential impedance, which requires stronger biasing.

I'd also look at the driver enable timing in firmware. Half-duplex RS-485 requires the transmitter to be enabled, data sent, then disabled before the next node responds. If the turn-around time is too tight at 115200 baud, the bus might still be settling when the next driver takes over, causing collisions or undefined bus states.

Finally, I'd use an oscilloscope to look at the actual waveforms at the farthest node — checking rise/fall times, overshoot, and whether the signal crosses the receiver threshold cleanly. I'd also check the common-mode voltage range, especially if the network spans areas with different ground potentials.

**Possible follow-ups:** How would you decide between fixing the hardware versus reducing the baud rate? What measurements would you take to confirm the root cause before making changes?

---

## Q3: How would you approach implementing a protocol conversion gateway between a legacy RS-485 network using a proprietary binary protocol and a modern CAN-FD network, where the gateway must handle different data rates, message priorities, and error handling semantics between the two sides?

**Answer:** A protocol gateway is essentially a real-time translation problem with three distinct concerns: data mapping, timing/priority translation, and error handling.

The first step is to create a complete mapping document between the two protocols. This isn't just field-to-field mapping — it's understanding the semantic meaning of each message. A legacy RS-485 message might combine multiple data items in a single frame, while CAN-FD messages are typically more granular. I'd define which CAN-FD message IDs correspond to which RS-485 message types, and how the data fields map. This mapping becomes the requirements document for the gateway firmware.

For timing and priority, the gateway needs to handle the mismatch between the two sides. RS-485 is typically polled or time-slotted, while CAN-FD is event-driven with priority arbitration. The gateway must translate the priority semantics — a high-priority alarm on the RS-485 side should map to a high-priority CAN-FD message ID. But the gateway also needs to handle rate mismatches: if the RS-485 side sends data faster than the CAN-FD side can transmit, the gateway needs buffering with a defined overflow policy.

The error handling is where I'd spend significant design effort. The two protocols have fundamentally different error models. RS-485 has no built-in error detection — that's typically at the application layer with checksums. CAN-FD has CRC and error confinement built in. The gateway must decide how to handle errors on each side independently: if the RS-485 side has a checksum error, does the gateway discard the message, request a retransmission, or forward an error indication to the CAN-FD side? If the CAN-FD side has a bus-off condition, how does the gateway behave — does it buffer data, enter a fail-safe state, or alert the RS-485 side?

I'd also consider the gateway's own failure modes. The gateway is a single point of failure, so it needs a watchdog, a defined startup sequence, and a fail-safe state that's safe for the medical application. The firmware architecture would use separate tasks or state machines for each protocol side, communicating through a well-defined queue or mailbox structure, so that a failure on one side doesn't corrupt the other.

**Possible follow-ups:** How would you handle the case where the same data item is represented differently on the two sides — for example, different units or scaling factors? How would you test the gateway to verify the translation is correct?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single SPI bus with four slaves, each on an independent chip select, to connect a high-resolution ADC, a flash memory for data logging, a real-time clock, and a temperature sensor in a battery-powered medical device. The engineer argues that SPI's high data rate and simple architecture make it the obvious choice. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging that SPI is a reasonable default choice for this set of peripherals — it's simple, fast, and each device gets its own chip select, which avoids the address conflicts you'd have with I2C. But I'd guide the team to evaluate the decision against the actual system requirements rather than accepting it on general merits.

The first question I'd raise is about power consumption. This is a battery-powered medical device, and SPI typically requires all devices to be powered and their clocks running during communication. I'd ask the engineer to analyze the duty cycle: how often does each peripheral need to be accessed? The ADC might need continuous sampling, but the temperature sensor might only need reading once per minute. For infrequent accesses, I2C might allow lower-power operation because devices can be put to sleep and woken individually.

The second question is about signal integrity and layout. Four devices on one SPI bus means four sets of traces, and the ADC is high-resolution — likely 16-bit or higher. I'd ask the engineer to consider whether the SPI clock and data lines running past the flash memory and RTC could couple noise into the ADC's analog input or reference. In a mixed-signal design, I might recommend a separate SPI bus for the ADC, or at least careful layout with the ADC isolated from the digital noise sources.

The third consideration is firmware complexity. With four devices on one bus, the firmware needs to manage chip selects carefully, especially if any device requires different clock polarity or phase settings. I'd ask the engineer to check the datasheets — if the ADC requires SPI mode 0 and the flash requires mode 3, the firmware needs to reconfigure the SPI peripheral between accesses, which adds complexity and potential for errors.

Finally, I'd ask about failure modes. If one device on the bus fails and holds MISO low, it corrupts communication with all other devices. Is that acceptable for the medical application? Would separate buses or a different protocol provide better fault isolation?

The goal isn't to reject the proposal — it's to ensure the team has considered the full design space and can justify the choice with data rather than convenience.

**Possible follow-ups:** How would you decide between one shared bus versus multiple dedicated buses for this set of peripherals? What specific measurements or analysis would you want to see before approving the design?

---

## Q5: How would you approach developing a communication protocol test plan for a medical device that uses multiple interfaces (I2C, SPI, UART, and USB), where the test plan must verify both normal operation and fault tolerance, and the results need to be documented for regulatory submission?

**Answer:** A protocol test plan for a medical device has two audiences: the engineering team that needs to find bugs, and the regulatory reviewers who need evidence that the device is safe and reliable. The test plan needs to serve both.

I'd structure the test plan in layers. The first layer is protocol conformance — verifying that each interface implements the protocol correctly according to its specification. For I2C, this means checking addressing, ACK/NACK behavior, clock stretching, and multi-master arbitration. For SPI, it's clock polarity/phase modes, chip select timing, and data framing. For UART, it's baud rate accuracy, framing, parity, and break conditions. For USB, it's descriptor correctness, endpoint behavior, and enumeration compliance. This layer uses protocol analyzers and test fixtures to verify the device behaves as specified.

The second layer is functional testing — verifying that the data transmitted over each interface is correct and complete. This means sending known test patterns and verifying the received data matches, checking that sensor readings are accurately transmitted, and verifying that commands are correctly parsed and executed. This layer also includes timing verification — measuring latency, throughput, and response times against requirements.

The third layer is fault tolerance testing. This is where I'd focus significant effort because intermittent faults are the most dangerous in medical devices. For each interface, I'd define a fault injection matrix: what happens if a wire is shorted, if a device fails to respond, if data is corrupted, if the bus is held low, if a device is hot-plugged, if power is interrupted mid-transaction. The device must handle each fault gracefully — either recovering automatically, entering a defined safe state, or alerting the user — without ever putting the patient at risk.

For regulatory documentation, I'd organize the test plan to map directly to the device's requirements and risk analysis. Each test case would reference the specific requirement it verifies and the associated risk control measure. The test results would include pass/fail criteria, actual measured values, and any anomalies observed. I'd also include a traceability matrix linking each requirement to its test cases.

A critical aspect is test repeatability. The test procedures need to be documented precisely enough that a different engineer could reproduce them. This means specifying test equipment, setup diagrams, test data, and pass/fail criteria in detail. For fault injection, I'd use controlled methods — for example, a test fixture that can insert resistance, capacitance, or shorts into specific lines — rather than ad-hoc methods that can't be reproduced.

**Possible follow-ups:** How would you prioritize which fault conditions to test, given that you can't test every possible failure? How would you handle a test failure that's traced to a firmware bug — what's the process for documenting the fix and re-testing?