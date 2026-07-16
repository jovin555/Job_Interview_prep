# Protocols — Day 1

## Q1: What is I2C clock stretching and when would it be a concern in a medical device design?
**Answer:** Clock stretching is an I2C protocol feature where a slave device holds the SCL line low after the master releases it, to signal that it needs more time to process data before continuing the transaction. This is a valid part of the I2C specification, but it can cause problems if the master doesn't support it or if time-critical reads are required. In my work on the Smart OPEP device at Trudell Medical International, we used I2C to communicate with pressure sensors for flow capture. If a sensor had performed clock stretching during a patient breath cycle, it could have delayed sensor reads and affected the real-time RGB LED feedback timing. We verified that our master microcontroller handled clock stretching properly and that sensor read times stayed within our 10 ms sampling window to avoid data gaps.

**Possible follow-ups:** How would you debug a clock stretching issue on an oscilloscope? What happens if a master doesn't support clock stretching and the slave tries to use it?

---

## Q2: Explain the difference between RS485 and CAN-FD in terms of physical layer and application suitability for medical equipment.
**Answer:** RS485 uses differential signaling over a twisted pair, supports multi-drop networks up to 32 nodes typically, and is half-duplex unless four wires are used. It's simple and works well for point-to-point or broadcast communication at speeds up to 10 Mbps over short distances. CAN-FD (Flexible Data-Rate) also uses differential signaling but includes a robust arbitration mechanism where multiple nodes can transmit simultaneously without data corruption—the lowest-ID message wins. CAN-FD allows up to 64 data bytes per frame versus CAN's 8, and data rates can go above 5 Mbps in the data phase. For medical devices, RS485 is common for sensor arrays where deterministic timing isn't critical, while CAN-FD is better for safety-critical systems requiring guaranteed message delivery. On the SOBA Heart Lung Support Machine project, we used CAN-FD for motor speed control and biological parameter monitoring because we needed deterministic communication between the control box and multiple sensor modules without collisions. RS485 would have required a master-slave polling scheme that could have introduced latency in life-support feedback loops.

**Possible follow-ups:** How does CAN-FD handle error detection differently from RS485? What termination resistor values would you use for each?

---

## Q3: Walk me through how you would design a USB 2.0 interface for a medical device that needs to transfer patient monitoring data to a host computer.
**Answer:** For a Class II medical device like the Lotus printer unit that records toco values, maternal heart rate, and fetal heart rate, I would design the USB 2.0 interface with these considerations: First, select a microcontroller with an integrated USB peripheral—many STM32 parts have USB 2.0 full-speed (12 Mbps) which is sufficient for periodic vital sign data. Route the D+ and D- differential pair as 90-ohm controlled impedance traces on the PCB, keeping them as short as possible and equal in length to within 5 mils to minimize skew. Place a 1.5 kΩ pull-up resistor on D+ to signal full-speed device enumeration. Add ESD protection diodes (e.g., USBLC6-2) near the connector for patient safety isolation per IEC 60601. Use a ferrite bead on VBUS for EMI filtering. On the firmware side, implement a CDC (Communications Device Class) virtual COM port so the host sees a simple serial interface—no driver installation needed. For medical data integrity, add a CRC-16 checksum to each data packet and implement retry logic if the host doesn't acknowledge within a timeout. During IEC 60601 testing on the Lotus project, we had to ensure USB isolation met patient leakage current requirements, so we used a galvanic isolator (like ADuM3160) between the device side and the USB connector for the printer unit.

**Possible follow-ups:** How would you handle USB suspend/resume for a battery-powered medical device? What happens if the host computer goes to sleep during data transfer?

---

## Q4: Describe a situation where you had to troubleshoot a protocol-level issue on a medical device. What was the problem and how did you resolve it?
**Answer:** During IEC 60601 compliance testing for the Lotus (Printer and Toco) maternal/infant care system at Trudell Medical International, we encountered intermittent communication failures between the Toco device and the printer unit over a custom serial protocol running on RS485. The printer would occasionally miss toco value packets, causing gaps in the printed strip chart during labor monitoring—a critical safety issue.

**Situation:** The Toco device continuously transmitted uterine contraction data, maternal heart rate, and fetal heart rate to the printer over a multi-drop RS485 bus at 115200 baud. During regulatory testing, the printer would drop approximately 1 in every 500 packets without any error flags.

**Task:** Identify the root cause of the packet loss and implement a fix before the testing deadline, since this was a patient monitoring device where data integrity was essential.

**Action:** I used a digital oscilloscope to capture the RS485 differential signals during packet loss events. I noticed that the Toco device's enable pin on the RS485 transceiver was being toggled slightly too early after the last data byte—the transceiver was switching back to receive mode while the printer's UART was still processing the stop bit. This created a 2-3 microsecond window where the bus went high-impedance, and noise could corrupt the final bit. I adjusted the firmware timing on the Toco device's STM32 to add a 100-microsecond delay between the last byte transmission and disabling the driver. I also added a 120-ohm termination resistor at both ends of the RS485 bus (previously only one end was terminated) to reduce reflections.

**Result:** After the firmware fix and termination resistor addition, we ran 24-hour continuous data logging with zero packet drops. The device passed IEC 60601 testing, and the 8D root-cause investigation documented the fix for future designs. This experience taught me to always verify transceiver enable timing with an oscilloscope during protocol development.

**Possible follow-ups:** Why did you choose 100 microseconds specifically? How did you verify the fix under worst-case conditions?

---

## Q5: How would you select between SPI and I2C for sensor communication in a battery-powered medical IoT device like the Smart OPEP?
**Answer:** For the Smart OPEP device—which uses pressure sensors for flow capture, RGB LED feedback, and needs 7 days of continuous battery life—the choice between SPI and I2C depends on several factors:

**SPI advantages:** Higher data rate (typically 10-40 Mbps vs I2C's 400 kbps or 1 Mbps), full-duplex communication, simpler protocol with no addressing overhead. However, SPI requires more pins—at least 4 wires per bus (MOSI, MISO, SCLK, CS) plus a chip select per device.

**I2C advantages:** Only 2 wires (SDA, SCL) regardless of how many sensors are on the bus, built-in addressing, and lower power consumption because the bus lines are pulled high through resistors rather than actively driven. I2C also supports multiple masters and clock stretching.

**For the Smart OPEP:** I would choose I2C because: (1) The pressure sensors we used have I2C interfaces and sample at 100 Hz max—well within I2C's 400 kbps capability. (2) Battery life is critical—I2C's pull-up resistor scheme uses less power than SPI's active drivers when the bus is idle. (3) We only needed 2-3 sensors, so the addressing overhead is minimal. (4) The 2-wire interface saved PCB space and routing complexity in a compact handheld device. The trade-off is that I2C is more susceptible to noise on long traces, but in a small handheld device with short interconnects (<5 cm), this wasn't an issue. We did add 4.7 kΩ pull-up resistors and 100 pF filtering capacitors on each line to meet EMI requirements for medical certification.

**Possible follow-ups:** What if you needed to add a high-bandwidth sensor later—how would you handle that? How do you calculate the maximum I2C bus capacitance for a given speed?