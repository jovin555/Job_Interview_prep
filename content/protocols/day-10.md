# protocols — Day 10

## Q1: How would you approach designing a multi-master I2C system where two microcontrollers need to share access to a single EEPROM and a set of sensors, with the requirement that no data corruption occurs during arbitration?

**Answer:** Multi-master I2C is fundamentally about respecting arbitration and ensuring that the bus state is always well-defined. My approach would start at the protocol level: both masters must use the same bus speed and support standard arbitration, where the master that pulls SDA low wins. The key design decisions are:

- **Address allocation:** Ensure no two devices share an address, and consider using separate address ranges for each master's "preferred" transactions to reduce contention.
- **Clock synchronization:** Both masters must synchronize their clocks — I2C does this automatically via the wired-AND of SCL, but it requires that neither master uses clock stretching in a way that could deadlock the other.
- **Bus arbitration handling:** Firmware must handle the "lost arbitration" condition gracefully. When a master loses arbitration, it should immediately release the bus and retry after a backoff period. The retry logic should include a random or pseudo-random delay to avoid both masters retrying simultaneously and colliding repeatedly.
- **Error detection:** Add a CRC or checksum to the data payload at the application layer, because while I2C arbitration prevents corruption at the bit level, it doesn't guarantee that a partially transmitted message isn't misinterpreted as valid by a slave.
- **Bus lockup protection:** Implement a timeout on SCL being low (clock stretching watchdog) and a bus-busy timeout in firmware, so a stuck slave or a glitch doesn't hang the system permanently.

For a medical device, I would also consider whether multi-master is truly necessary. Often a single master with a simple polling scheme or a master/slave arrangement with a dedicated "request" line is simpler and more deterministic. If multi-master is unavoidable, I'd document the arbitration behavior in the firmware architecture and add a hardware bus monitor (a third device or a logic analyzer hook) during validation to confirm arbitration works under worst-case timing.

**Possible follow-ups:**
- What happens if one master holds the bus for a long time (e.g., a large EEPROM write)? How would you prevent the other master from timing out?
- How would you test that arbitration works correctly under simultaneous start conditions?

---

## Q2: You're debugging a UART link between a microcontroller and a wireless module where data is occasionally corrupted, but only when the module transmits at the same time the microcontroller is receiving on another peripheral. How would you approach this?

**Answer:** This sounds like a classic interrupt-latency or shared-resource problem rather than a baud-rate mismatch. My approach would be systematic:

1. **Reproduce and characterize:** First, I'd try to reproduce it reliably and determine if the corruption is bit-level (framing errors, noise) or byte-level (missing bytes, duplicated bytes). A logic analyzer on the TX/RX lines would tell me if the waveform is clean — if it is, the issue is in firmware.

2. **Check interrupt priorities and latency:** If the microcontroller is handling another peripheral's interrupt at the same time, the UART receive interrupt could be delayed. If the UART RX buffer overflows or the interrupt is serviced too late, bytes are lost or the framing is misread. I'd check the interrupt priority assignments and measure worst-case interrupt latency.

3. **Examine the receive path:** Is the UART using DMA or interrupt-driven reception? If interrupt-driven, is the RX buffer large enough? If DMA, is there a race between the DMA completing and the application reading the data?

4. **Look for shared-resource conflicts:** If the UART and the other peripheral share a common clock, a DMA channel, or a memory region, there could be a subtle conflict. For example, if both use the same DMA controller and one has higher priority, the UART could stall.

5. **Check for electrical coupling:** If the waveform is clean on the scope but data is still corrupted, it could be a ground bounce or crosstalk issue when the other peripheral switches. I'd check the power supply rails and ground planes, especially if the wireless module draws significant current during transmission.

6. **Add defensive measures:** Regardless of root cause, I'd add a CRC or checksum to the protocol, implement retries, and ensure the UART driver handles framing errors gracefully (e.g., by resetting the receiver state machine).

In a medical device, this kind of intermittent corruption is exactly why the protocol layer needs error detection and retry logic — you can't rely on the physical layer being perfect.

**Possible follow-ups:**
- How would you determine whether the issue is in hardware or firmware first?
- What if the corruption only happens once every few hours? How would you instrument the system to capture the failure?

---

## Q3: How would you approach selecting between a polled and an interrupt-driven firmware architecture for handling multiple communication protocols (I2C, SPI, UART) in a battery-powered medical sensor device?

**Answer:** The choice between polled and interrupt-driven (or DMA-driven) communication depends on three factors: timing requirements, power consumption, and firmware complexity.

**Polled approach:**
- **Pros:** Simple, deterministic, easy to debug. No interrupt priority issues.
- **Cons:** Wastes CPU cycles, increases power consumption (the CPU can't sleep while polling), and can miss data if the polling interval is too long relative to the incoming data rate.
- **Best for:** Low-data-rate, periodic communication where the CPU has nothing else to do, or where the device is line-powered.

**Interrupt-driven approach:**
- **Pros:** CPU sleeps between events, saving power. Can handle asynchronous data arrival without missing bytes.
- **Cons:** More complex, requires careful priority assignment, and can introduce jitter if multiple interrupts compete.

**DMA-driven approach:**
- **Pros:** Minimal CPU involvement, ideal for large or continuous data transfers (e.g., streaming sensor data over SPI).
- **Cons:** Requires careful buffer management, and DMA channels are a limited resource.

For a battery-powered medical sensor device, my default would be interrupt-driven with the CPU entering a low-power state between events. The specific choice depends on the data rates:

- **I2C sensors** that send data periodically (e.g., every 100 ms) — interrupt on the I2C address match or use a timer to trigger reads.
- **SPI** for high-throughput data (e.g., an ADC streaming at high rate) — DMA with double buffering.
- **UART** for asynchronous events (e.g., user input or wireless module) — interrupt-driven with a ring buffer.

I would also consider a hybrid: use interrupts for event detection (e.g., a data-ready line from a sensor) and then use DMA or polled transfers for the actual data read, depending on the transfer size.

The key trade-off is power vs. latency. If the device can tolerate a few milliseconds of latency, you can use a low-frequency timer to wake the CPU and poll all peripherals in a round-robin fashion. This is often simpler and more power-efficient than keeping interrupts enabled, because the CPU wakes up once, does all pending work, and goes back to sleep.

**Possible follow-ups:**
- How would you estimate the worst-case CPU load for a given polling interval?
- When would you choose DMA over interrupt-driven even for small transfers?

---

## Q4: In a system using SPI with multiple slaves on independent chip selects, you notice that when one particular slave is deselected, it briefly drives MISO low, causing a glitch that corrupts the next transaction. How would you approach this?

**Answer:** This is a classic MISO contention or bus-hold issue. The symptom — a slave driving MISO after it's deselected — usually has one of several root causes:

1. **The slave's chip-select-to-output-disable timing is too slow.** Some slaves have a specified delay between CS deassertion and the output going high-impedance. If the master starts the next transaction before that delay elapses, the old slave is still driving MISO while the new slave is also driving it, causing contention.

2. **The slave's MISO pin is not truly tri-state.** Some devices have a push-pull output that doesn't go high-impedance on CS deassert. This is a hardware design issue — you'd need a series resistor or a bus switch to isolate the slave.

3. **The master's CS deassertion is too fast relative to the slave's internal state machine.** The slave may need a minimum CS-high time to properly reset its output stage.

My debugging approach:

- **Scope the MISO line and CS lines together.** Look for the glitch timing relative to CS deassertion. If the glitch occurs immediately after CS goes high, it's likely the slave's output-disable delay. If it occurs later, it could be a power-supply or ground issue.
- **Check the slave's datasheet** for the CS-to-output-high-impedance specification. Compare it to the master's timing.
- **Add a delay between transactions** (CS high time) in firmware to allow the slave to release the bus. This is the simplest fix if the timing margin is small.
- **Add a pull-up or pull-down resistor on MISO** to define the bus state when no slave is driving it. This prevents a floating line from being interpreted as a valid bit.
- **If the slave truly can't tri-state**, you need a hardware fix: a series resistor (e.g., 1 kΩ) on MISO to limit contention current, or a bus switch (e.g., an analog switch) that isolates the slave when its CS is deasserted.

For a medical device, I'd also consider whether the glitch could cause a safety issue. If the corrupted data could be misinterpreted as a valid sensor reading, the protocol layer needs a checksum to detect and reject it.

**Possible follow-ups:**
- How would you determine whether the fix should be in firmware (adding delay) or hardware (adding a resistor)?
- What if the glitch only occurs at certain temperatures or after the device has been running for a while?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single RS-485 bus for both real-time control commands and periodic telemetry data from 20 sensor nodes, with the control commands needing deterministic delivery within 5 ms. How would you guide the team to evaluate this approach?

**Answer:** This is a system architecture question that goes beyond the electrical layer. My guidance would focus on whether a single shared bus can meet the determinism requirement, and if so, how to structure the protocol.

**Step 1: Quantify the bus load.**
- Calculate the worst-case time to transmit a control command: at 115.2 kbps, a 10-byte frame (including overhead) takes roughly 1 ms. At 1 Mbps, it's ~0.1 ms.
- Calculate the total telemetry load: 20 nodes × (frame size + turnaround time) × polling frequency. If each node sends 50 bytes every 100 ms, that's 20 × 50 × 10 = 10,000 bytes/sec, which is about 0.87 ms of bus time per 100 ms at 115.2 kbps — well under 10% utilization. But if the telemetry is bursty or the polling is frequent, the load could spike.

**Step 2: Evaluate the protocol's determinism.**
- RS-485 is half-duplex, so only one node can transmit at a time. The master must control access. A simple polled scheme (master asks each node in turn) is deterministic but has a fixed latency that depends on the number of nodes and the response time.
- If the control command must be delivered within 5 ms, the master needs a priority mechanism. Options include:
  - **Time-division multiplexing (TDM):** Reserve a dedicated time slot for control commands. This guarantees latency but wastes bandwidth if no command is pending.
  - **Priority-based polling:** The master checks for pending control commands before polling telemetry. This adds jitter to telemetry but guarantees control latency.
  - **Event-driven with a dedicated "request to send" line:** A separate wire (or a second RS-485 channel) for control commands, keeping telemetry on the main bus. This is the most robust but adds hardware complexity.

**Step 3: Consider failure modes.**
- If a sensor node fails and holds the bus (e.g., stuck high), it blocks all communication. You need a bus timeout and a way to isolate a faulty node (e.g., a hardware watchdog that disconnects the node's driver).
- If the control command is safety-critical, you need a CRC, a sequence number, and an acknowledgment with retry. The retry must fit within the 5 ms budget, which means the round-trip time must be well under that.

**Step 4: Recommend a decision framework.**
- If the telemetry load is low and the control command is infrequent, a single bus with a priority-based polling scheme can work. The master should be the only device that initiates communication, and the protocol should have a defined maximum latency for control commands.
- If the telemetry load is high or the control command is frequent, I'd recommend splitting the traffic: either a second RS-485 bus or a different protocol (e.g., CAN-FD) that has built-in priority arbitration.

In the design review, I'd ask the junior engineer to produce a worst-case timing diagram showing the bus schedule under maximum load, including the control command latency. That diagram would quickly reveal whether the single-bus approach meets the 5 ms requirement.

**Possible follow-ups:**
- How would you handle a situation where a sensor node fails to respond to a poll? Does that affect the control command latency?
- Would you consider using CAN-FD instead of RS-485 for this application? What are the trade-offs?