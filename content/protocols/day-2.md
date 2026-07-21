# protocols — Day 2

## Q1: How would you approach selecting a communication protocol for a new battery-powered medical sensor device that needs to stream data to a central monitor?

**Answer:** The selection starts with system-level requirements: data rate, distance, power budget, number of nodes, and regulatory constraints. For a battery-powered medical sensor, power efficiency is often the primary constraint, so I'd first look at low-power serial protocols like I2C or SPI for on-board sensor communication, and then consider the link to the central monitor.

If the monitor is within the same enclosure or a short distance (e.g., <1 meter), I2C or SPI with a shielded cable could work, but for longer runs (e.g., bedside to a central station), RS485 or CAN-FD would be more appropriate due to differential signaling and noise immunity. Wireless options like Bluetooth Low Energy (BLE) are attractive for patient mobility, but you must consider coexistence, latency, and medical-device wireless coexistence testing under IEC 60601-1-2.

I would also evaluate protocol overhead: a protocol like CAN-FD has built-in error detection and prioritization, which is valuable for safety-critical data, but adds complexity. For a simple sensor streaming periodic data, a lightweight UART-based protocol with a custom framing and CRC might be sufficient. The key is to prototype the top two candidates and measure actual power consumption, latency, and error rates under realistic conditions before committing.

**Possible follow-ups:** How would you handle protocol selection if the device also needs firmware updates over the same link? What trade-offs would you consider between using a standard protocol versus a custom lightweight one?

## Q2: You're debugging an I2C bus where a sensor occasionally stops responding after several hours of operation. How would you approach this?

**Answer:** I'd start by reproducing the issue in a controlled setup with a logic analyzer or oscilloscope capturing the SCL and SDA lines continuously. I'd look for common I2C failure modes: clock stretching that never releases, a slave holding SDA low (bus lock-up), or glitches on the lines due to noise or insufficient pull-up strength.

If the bus locks up with SDA held low, that usually indicates a slave device entered an invalid state. I'd check the supply voltage to the sensor at the moment of failure — a brown-out or transient dip could cause the sensor's I2C peripheral to glitch. I'd also verify that the master's I2C timeout handling is implemented: many I2C peripherals can be reset by toggling the SCL line nine times to complete a hung transaction.

Another common cause is bus capacitance exceeding the I2C specification for the chosen speed mode (e.g., 400 kHz fast mode). Over time, temperature changes or component aging can push marginal timing over the edge. I'd measure rise times on SCL/SDA and compare against the spec, then either reduce the bus speed, increase pull-up current, or add a bus buffer/repeater.

Finally, I'd review the sensor's datasheet for any errata about I2C behavior during low-power modes or after specific command sequences — sometimes a workaround like adding a dummy read before each transaction is documented.

**Possible follow-ups:** How would you implement I2C bus recovery in firmware without a hardware reset line? What would you look for on the oscilloscope to distinguish a slave lock-up from a master-side issue?

## Q3: In a multi-processor system using SPI, how would you handle the situation where two slaves need to share a single SPI bus but have incompatible clock polarity or phase requirements?

**Answer:** SPI's flexibility with CPOL and CPHA settings means you can reconfigure the master's SPI peripheral between transactions, as long as the master supports per-slave configuration. The typical approach is to use separate chip-select lines for each slave, and before asserting a given slave's chip-select, reconfigure the master's clock polarity and phase to match that slave's requirements. Between transactions, you de-assert the chip-select, change the SPI mode, then assert the next slave's chip-select.

However, this adds latency and complexity in the driver. If the slaves are truly incompatible (e.g., one requires CPOL=0/CPHA=0 and another CPOL=1/CPHA=1), you must ensure the bus lines are in a known idle state between transactions — particularly the clock line, which could glitch if the mode change causes a clock transition while a chip-select is still asserted.

An alternative is to use a dedicated SPI bus per slave if pin count allows, or use an SPI multiplexer/switch that isolates the slaves electrically. In a Zephyr RTOS environment, I'd implement the per-slave configuration in the device tree bindings and use the SPI controller's `config` function to switch modes on each transaction. I'd also add a brief delay after reconfiguring to let the clock settle before starting the transaction.

**Possible follow-ups:** What happens if you change CPOL while the clock line is high — could that create an unintended clock edge? How would you test that your mode-switching logic is glitch-free?

## Q4: You're designing a system that uses CAN-FD for communication between multiple medical device modules. How would you approach ensuring deterministic message delivery for a high-priority safety-critical message?

**Answer:** CAN-FD's built-in arbitration mechanism already prioritizes messages by identifier — lower identifier values win arbitration. So the first step is to assign the lowest identifier to the safety-critical message. But arbitration alone doesn't guarantee maximum latency, because a high-priority message can still be delayed if the bus is busy with a lower-priority frame that has already started transmission.

To bound the worst-case latency, I'd perform a response-time analysis for the CAN bus. This involves calculating the longest time a high-priority message might wait, considering the longest possible lower-priority frame (which, in CAN-FD, can be up to 64 bytes of data at a higher bit-rate in the data phase). I'd also account for error frames and retransmissions — a single bit error can cause a frame to be retransmitted, doubling its transmission time.

Practical mitigations include: using a dedicated CAN bus for safety-critical traffic if the overall bus load is high; implementing a time-triggered schedule (e.g., using CAN with Time-Triggered Communication, TTCAN, or a custom slot-based scheme); and ensuring the bus load stays below ~30-40% for hard real-time systems. I'd also add a hardware watchdog that monitors for missing periodic safety messages and triggers a safe state if a deadline is missed.

Finally, I'd verify the analysis with empirical testing: inject worst-case bus traffic and measure the actual latency of the safety message under all operating conditions, including during bus-off recovery scenarios.

**Possible follow-ups:** How would you handle the case where a node goes bus-off and then reconnects — could that cause a burst of errors that delays your safety message? What's the difference between CAN 2.0 and CAN-FD in terms of worst-case frame length?

## Q5: Imagine you're leading a cross-functional team where a firmware engineer and a hardware engineer disagree on whether to use UART or I2C for a new sensor interface. The firmware engineer wants I2C for multi-drop capability; the hardware engineer prefers UART for simplicity and lower pin count. How would you guide the team to a decision?

**Answer:** I'd start by facilitating a structured trade-off discussion rather than letting it become a personal preference debate. The first step is to list the non-negotiable requirements: how many sensors need to share the bus, what data rate is needed, what cable length is required, and what are the power constraints.

If only one sensor is involved, the hardware engineer's point about UART simplicity is strong — it uses two wires, no pull-up resistors, and is easier to debug with a simple terminal. But if future expansion to multiple sensors is likely, the firmware engineer's preference for I2C's multi-drop capability has merit, though I2C has distance limitations and requires careful bus capacitance management.

I'd propose we prototype both options on a breadboard with the actual sensor and measure: signal integrity at the required cable length, power consumption in active and sleep modes, and the time to implement the driver on our chosen RTOS. I'd also ask both engineers to estimate the development and testing effort for each option — sometimes the "simpler" protocol requires more firmware workarounds (e.g., I2C bus recovery, clock stretching handling) that offset the hardware simplicity.

Ultimately, I'd frame the decision around risk: which option has fewer unknowns for this specific application? If neither is clearly superior, I'd suggest a decision matrix with weighted criteria (e.g., power, cost, development time, reliability) and have the team score each option together. The goal is to reach consensus based on data, not hierarchy.

**Possible follow-ups:** How would you handle the situation if after prototyping, both options meet requirements but the disagreement persists? What role would regulatory compliance (e.g., IEC 60601 isolation requirements) play in this decision?