# protocols — Day 9

## Q1: You're designing a medical device that uses I2C to communicate with four different sensors on a single bus. During prototype testing, you find that the bus occasionally locks up after several hours of operation. How would you approach debugging this?

**Answer:** I'd approach this systematically, starting with the most common causes of I2C bus lockups in multi-device systems.

First, I'd examine the bus with an oscilloscope or logic analyzer during the lockup condition. I'd look for:
- **Clock stretching issues**: A slave device holding SCL low indefinitely, which is a common failure mode. I'd check if any sensor's datasheet specifies a maximum clock stretch time and whether my firmware implements a timeout.
- **Bus contention**: If a slave drives SDA low and never releases it, often due to a glitch corrupting the slave's internal state machine. I'd check if the master's I2C peripheral has a bus timeout feature that can generate a stop condition and reset the bus.
- **Voltage levels**: With four devices, bus capacitance could be approaching the 400 pF limit for fast-mode (400 kHz). Excessive capacitance can slow rise times, causing marginal timing that degrades over temperature or voltage drift. I'd measure the actual rise time and verify pull-up resistor values are appropriate for the total bus capacitance.

Second, I'd add defensive firmware measures: a watchdog timer that monitors bus activity and issues a series of clock pulses followed by a stop condition to reset hung slaves, or a bus recovery routine that toggles SCL nine times while monitoring SDA to force slaves to release the bus.

Third, I'd check the PCB layout for crosstalk or noise coupling onto the I2C lines, especially if the bus runs near switching power supplies or other high-frequency signals.

**Possible follow-ups:** How would you calculate the appropriate pull-up resistor value for a bus with 400 pF total capacitance operating at 400 kHz? What would you do if a particular sensor is known to occasionally stretch the clock for longer than your timeout period?

---

## Q2: How would you approach selecting between interrupt transfers and isochronous transfers for a USB 2.0 medical device that streams real-time sensor data to a host computer?

**Answer:** This decision hinges on whether the application can tolerate occasional data loss and what latency guarantees are needed.

**Interrupt transfers** are appropriate when:
- Data delivery must be guaranteed (the host controller will retry failed transactions)
- The data rate is relatively low (up to 64 bytes per transaction at 1 ms intervals for full-speed, or up to 1024 bytes at 125 µs intervals for high-speed)
- The polling interval can be bounded, giving predictable latency
- Typical use cases: periodic sensor readings, status updates, button presses

**Isochronous transfers** are appropriate when:
- Data must arrive at precise time intervals (e.g., audio streaming, video)
- Some data loss is acceptable (no retry mechanism — if a packet is corrupted, it's simply dropped)
- Higher bandwidth is needed (up to 1023 bytes per transaction at 1 ms intervals for full-speed)
- The application can tolerate occasional missing samples through interpolation or error concealment

For a medical device streaming real-time sensor data, I'd lean toward **interrupt transfers** if the data rate fits within the bandwidth limits, because guaranteed delivery is critical — losing a sensor reading could affect patient monitoring. However, if the sensor generates data at a high rate (e.g., continuous waveform capture at several kHz sampling), isochronous might be necessary for bandwidth, and I'd add error detection and recovery at the application layer.

I'd also consider a composite device approach: use interrupt endpoints for critical status/alarm data and isochronous endpoints for high-bandwidth waveform data, with appropriate error handling for each.

**Possible follow-ups:** How would you handle the case where your sensor data rate exceeds the maximum interrupt transfer bandwidth? What endpoint descriptor fields would you need to configure differently between interrupt and isochronous endpoints?

---

## Q3: In a CAN-FD network for a medical device, you need to ensure that a high-priority safety-critical message is never delayed by more than 500 microseconds. How would you approach guaranteeing this timing requirement?

**Answer:** This requires a combination of network design, message scheduling, and verification. I'd approach it in several layers:

**1. Network topology and bit rate selection:**
- Choose the arbitration phase bit rate (typically 125 kbps to 1 Mbps) based on bus length — longer buses require lower bit rates due to propagation delay. For a 500 µs deadline, I'd target a data phase bit rate of at least 2-5 Mbps to minimize message transmission time.
- Keep the bus length short and node count manageable to reduce propagation delays and arbitration time.

**2. Message prioritization:**
- Assign the safety-critical message the lowest CAN-ID value (highest priority) in the network. This ensures it wins arbitration against any other message.
- Ensure no other message can block it — even a lower-priority message that has already started transmission can delay the high-priority message by at most one full message time (worst-case: a 64-byte data frame at the arbitration bit rate).

**3. Worst-case latency calculation:**
- Calculate the maximum time the high-priority message could be delayed: one longest lower-priority message transmission time (if one started just before the high-priority message was queued) plus the high-priority message's own transmission time.
- Verify this worst-case latency is under 500 µs. If not, consider increasing the arbitration bit rate, reducing maximum data payload size, or using CAN-FD's faster data phase.

**4. Implementation safeguards:**
- Use CAN-FD's E2E CRC for the safety-critical message to detect corruption.
- Implement a transmission deadline monitor in firmware — if the message isn't sent within a threshold, trigger an error state.
- Consider using CAN-FD's "transmit timestamp" feature (if available) to measure actual queuing delays during testing.

**5. Verification:**
- Use a CAN bus analyzer to capture bus traffic under worst-case load conditions (all nodes transmitting at maximum rate) and measure the actual latency of the high-priority message.
- Perform fault injection testing (e.g., bus errors, node failures) to ensure the timing guarantee holds under abnormal conditions.

**Possible follow-ups:** How would you handle the case where a lower-priority message with a large payload is already being transmitted when the high-priority message is queued? What if you need to add more nodes later — how would you re-verify the timing guarantee?

---

## Q4: You're debugging an RS-485 network where 16 sensor nodes communicate with a central controller over a 200-meter cable run. The system works during bench testing but experiences intermittent data corruption when installed in the field near industrial equipment. How would you approach this?

**Answer:** This sounds like a classic electromagnetic interference (EMI) problem, common when RS-485 networks are deployed in electrically noisy environments. I'd approach it systematically:

**1. Verify termination and biasing:**
- First, confirm termination resistors are correctly placed — one at each end of the main cable run, matching the cable's characteristic impedance (typically 120 Ω). Incorrect termination causes reflections that manifest as data corruption, especially with longer cables.
- Check for fail-safe biasing resistors that pull the differential lines to a known state when no driver is active. Without proper biasing, noise can be interpreted as valid data during bus idle periods.

**2. Examine the grounding scheme:**
- RS-485 requires a common ground reference between nodes. In noisy environments, ground potential differences can exceed the transceiver's common-mode voltage range (±7V for standard transceivers, up to ±12V for extended-range types).
- I'd check if a third wire for signal ground is used, or if the network relies on earth ground through each device's power supply. I'd recommend adding a signal ground wire and using isolated transceivers if ground loops are a concern.

**3. Check cable and routing:**
- Verify that shielded twisted-pair cable is used, with the shield grounded at one end only (to avoid ground loops).
- Ensure the cable is routed away from sources of interference — motors, variable frequency drives, switching power supplies. If it must cross such equipment, do so at right angles.
- Check that stub lengths (connections from the main trunk to each node) are as short as possible — ideally under a few inches. Long stubs create impedance mismatches and reflections.

**4. Add protection and margin:**
- Consider transceivers with higher common-mode rejection and wider common-mode range (e.g., ±15V or ±20V).
- Add transient voltage suppression (TVS) diodes at each node to clamp voltage spikes from nearby equipment.
- If the corruption persists, reduce the bit rate — RS-485 can operate at higher speeds, but lower rates (e.g., 115.2 kbps instead of 1 Mbps) provide more noise margin.

**5. Diagnostic approach:**
- Use a differential probe and oscilloscope to capture the actual signal at the farthest node during corruption events. Look for ringing, overshoot, or common-mode noise riding on the differential signal.
- Compare the signal at the controller end versus the far end to identify where degradation occurs.

**Possible follow-ups:** How would you determine the correct value for fail-safe biasing resistors? What would you look for on the oscilloscope to distinguish between reflection-related corruption and common-mode noise corruption?

---

## Q5: Imagine you're leading a design review where a firmware engineer proposes using a single UART with a software-based protocol multiplexer to communicate with four different sensors, each with different baud rates and protocols. The hardware engineer argues this is unreliable and wants four separate UART peripherals. How would you guide the team to a decision?

**Answer:** This is a classic trade-off between hardware simplicity and software complexity, with reliability implications. I'd guide the team through a structured evaluation:

**1. First, clarify the requirements:**
- What are the data rate and latency requirements for each sensor? If any sensor requires real-time streaming or has tight timing constraints, a shared UART with software multiplexing may introduce unacceptable latency.
- What is the update frequency for each sensor? If sensors are polled infrequently (e.g., once per second), multiplexing is more feasible than if they all stream continuously.
- Are the sensors' native protocols compatible with a single UART? If they use different framing, parity, or start/stop bit configurations, the multiplexer would need to reconfigure the UART between each sensor, adding complexity and potential for errors.

**2. Evaluate the software multiplexer approach:**
- The firmware engineer's proposal would require: (a) a hardware multiplexer (e.g., analog switch) to route the single UART TX/RX to the appropriate sensor, (b) firmware to reconfigure the UART baud rate and settings between each sensor transaction, and (c) a scheduling algorithm to ensure all sensors are serviced within their timing requirements.
- Risks include: timing jitter from reconfiguration overhead, potential for missed sensor data if a transaction takes longer than expected, and increased firmware complexity that could introduce bugs.
- The approach could work if sensors are polled sequentially at low rates and the baud rate differences are modest (e.g., 9600 vs 19200 baud), but becomes riskier with large baud rate disparities or real-time requirements.

**3. Evaluate the four-UART approach:**
- This provides deterministic, independent communication paths — each sensor gets dedicated hardware with no scheduling conflicts.
- The hardware cost is higher (more pins, potentially a larger microcontroller), and PCB routing is more complex.
- Firmware is simpler and more reliable — each sensor's driver runs independently without multiplexing logic.

**4. Consider a middle ground:**
- Could two UARTs suffice, grouping sensors with similar baud rates and timing requirements?
- Could a UART with a higher baud rate handle multiple low-speed sensors through a multiplexer, while a second dedicated UART handles a high-speed or real-time sensor?

**5. Decision framework:**
- I'd ask the team to create a simple table: for each sensor, list baud rate, data volume per transaction, required update interval, and protocol complexity. Then calculate the worst-case latency for the multiplexed approach.
- If the multiplexed approach can meet all timing requirements with at least 50% margin, it may be acceptable — but I'd recommend adding a hardware watchdog or timeout to detect if the multiplexer gets stuck.
- If any sensor has tight real-time requirements or the multiplexed approach has less than 50% margin, I'd recommend at least two dedicated UARTs.

Ultimately, for a medical device where reliability is paramount, I'd lean toward the hardware engineer's position — separate UARTs provide simpler, more deterministic behavior. But I'd ask the firmware engineer to prototype the multiplexer approach on a development board to gather real timing data, then make the final decision based on measured results rather than theoretical estimates.

**Possible follow-ups:** How would you handle the situation where the firmware engineer has already invested significant time in the multiplexer approach and is resistant to changing? What criteria would you use to determine whether the multiplexer approach is "reliable enough" for a medical device?