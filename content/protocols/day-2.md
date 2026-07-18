# protocols — Day 2

## Q1: What is clock stretching in I2C and why would it be a concern in a medical device design?
**Answer:** Clock stretching is an I2C protocol feature where a slave device holds the SCL line low after the master releases it, effectively pausing communication until the slave is ready to continue. This is typically used by slower slaves to give themselves time to process data before the next transaction.

In a medical device context, this becomes a reliability concern. On the **Smart OPEP Device**, we used pressure sensors communicating over I2C for flow capture. If a sensor performed clock stretching during a critical measurement window, it could delay the data acquisition loop and affect real-time patient feedback (RGB LED guidance). To handle this, we implemented a timeout mechanism in the I2C driver (Zephyr RTOS) that would abort the transaction if the stretch exceeded a safe threshold (e.g., 10 ms), log the event, and retry. This prevented a single stuck slave from hanging the entire sensor bus during therapy monitoring.

**Possible follow-ups:**
- How would you test that your clock stretching timeout doesn't miss valid data from a slow sensor?
- What happens if the master itself is the one that needs to stretch — does I2C support that?

---

## Q2: Explain the difference between UART and RS-485. When would you choose one over the other in an embedded medical system?
**Answer:** UART is a point-to-point, full-duplex protocol using two wires (TX/RX) with a common ground, typically limited to about 15 meters at 9600 baud. RS-485 is a differential, half-duplex protocol using a twisted pair, supporting up to 1200 meters and multiple nodes (up to 32 drivers) on the same bus.

In the **SOBA Heart Lung Support Machine**, we needed to communicate between the main control box and remote sensor modules (temperature, pressure) placed near the patient. The distances were under 2 meters, and we only had two nodes, so we used UART — it was simpler, required no transceiver ICs, and the noise immunity was adequate inside the shielded enclosure. However, for the **Lotus Toco device**, which monitors uterine contractions in a labor ward, the sensor head is physically separated from the base station by several meters, and there can be multiple monitoring stations in the same room. There, RS-485 was the right choice: differential signaling rejects the electrical noise from nearby medical equipment (infusion pumps, monitors), and the multi-drop capability lets us daisy-chain multiple Toco units if needed.

**Possible follow-ups:**
- How do you handle termination resistors on an RS-485 bus in a medical device that might be reconfigured in the field?
- What galvanic isolation considerations apply when using RS-485 in patient-connected equipment?

---

## Q3: Describe a situation where you had to debug a protocol-level issue on a real project. What was the problem and how did you resolve it?
**Answer:** (Behavioral/STAR)

**Situation:** On the **Lotus (Printer and Toco)** project at Trudell Medical International, we were integrating a thermal printer unit that recorded Toco values, maternal heart rate, and fetal heart rate. The printer communicated over UART at 115200 baud.

**Task:** During IEC 60601 pre-compliance testing, the printer would intermittently print garbled characters or skip lines, especially when other subsystems (sensor acquisition, display) were active. This was a regulatory risk — a failed printout during a clinical event could be a safety issue.

**Action:** I started by scoping the UART TX/RX lines. The waveforms looked clean at the source, but at the printer's RX pin, I saw glitches coinciding with the motor driver PWM switching. The issue was ground bounce: the printer's ground return shared a path with the motor driver's high-current return. I isolated the UART ground by routing a dedicated return trace from the printer connector directly to the main ground plane star point. I also added a 100-ohm series resistor on the TX line to dampen reflections, and a 10 nF capacitor to ground at the printer's RX pin to filter coupled noise.

**Result:** The garbled characters disappeared. The printer passed the emissions and immunity portions of IEC 60601 testing on the next attempt. The fix was documented in the 8D report as a layout guideline for future products.

**Possible follow-ups:**
- Why a series resistor and not just a stronger pull-up?
- Did you consider switching to a differential protocol like RS-422 for the printer link?

---

## Q4: In a CAN-FD network, how does the arbitration mechanism differ from classic CAN? Why would you use CAN-FD over SPI for intra-board communication in a medical device?
**Answer:** CAN-FD (Flexible Data-Rate) retains the same arbitration mechanism as classic CAN: dominant bits (0) overwrite recessive bits (1) on the bus, and the node that loses arbitration stops transmitting and retries later. The key difference is that after arbitration is resolved, CAN-FD can switch to a higher bit-rate (up to 8 Mbps) for the data phase, and it supports payloads up to 64 bytes versus classic CAN's 8 bytes.

For intra-board communication, SPI is usually simpler and faster for short distances (under 30 cm). However, on the **SOBA Heart Lung Support Machine**, we had multiple microcontrollers on the same PCB: one for motor speed control, one for biological parameter monitoring (temperature/pressure), and one for Wi-Fi comms. SPI would have required dedicated chip-select lines for each slave, consuming GPIOs and complicating the PCB routing. CAN-FD gave us a two-wire bus (CANH/CANL) connecting all three MCUs, with built-in error detection (CRC), message prioritization via arbitration, and the ability to add more nodes later without hardware changes. The 64-byte payload was useful for sending a full sensor data frame (temperature, pressure, motor RPM, status flags) in a single message. For a life-support device, the deterministic arbitration and error confinement of CAN-FD were also safety advantages over SPI's lack of error checking.

**Possible follow-ups:**
- How do you handle CAN-FD bit-timing configuration when the MCUs run at different clock speeds?
- What happens if a CAN node on your SOBA device fails — does the whole bus go down?

---

## Q5: You're designing a USB 2.0 interface for a Class II medical device that logs therapy data to a PC. Walk through the key hardware and firmware considerations to ensure reliable data transfer and regulatory compliance.
**Answer:** This maps directly to the **Smart OPEP Device**, which needed to offload patient usage logs via USB.

**Hardware considerations:**
- **Differential impedance:** Route the D+ and D- traces as a 90-ohm differential pair, matched in length (within 5 mm) to minimize skew. Keep them away from switching power supplies and clock lines.
- **ESD protection:** Add a USB-specific ESD protection diode (e.g., USBLC6-2SC6) on the D+/D- lines, rated for IEC 61000-4-2 level 4 (8 kV contact, 15 kV air). This is critical for a patient-connected device.
- **VBUS management:** Include a current-limited power switch (e.g., 500 mA limit per USB spec) and a TVS diode on VBUS. The device should not draw current from VBUS when not connected (no back-powering).
- **Common-mode choke:** Place a common-mode choke (e.g., 100 Ω at 100 MHz) on the differential pair to suppress EMI, helping pass IEC 60601 radiated emissions tests.

**Firmware considerations:**
- **Enumeration:** Implement a proper USB descriptor chain (device, configuration, interface, endpoint) identifying the device as a vendor-specific class or CDC ACM (virtual COM port). On the Smart OPEP, we used CDC ACM so the PC saw a simple COM port — no driver installation needed.
- **Bulk transfers:** Use bulk endpoints for data logging (error-corrected by USB hardware) rather than interrupt or isochronous, since log data is not time-critical but must be reliable.
- **Buffer management:** Allocate a double-buffer (ping-pong) in RAM so the application can fill one buffer while the USB peripheral transmits the other, preventing data loss if the PC is slow to read.
- **Disconnection handling:** Detect VBUS drop and gracefully close any open file handles on the SD card before the device loses power. We used a VBUS monitoring GPIO to trigger a shutdown sequence with a 10 ms hold-up capacitor.

**Regulatory:** The USB port must be isolated from patient connections (2 MOPP per IEC 60601-1). We used an isolated USB transceiver (e.g., ADuM3160) on the Smart OPEP to meet leakage current limits.

**Possible follow-ups:**
- How would you handle a situation where the PC sends a USB reset while the device is in the middle of writing to flash?
- What USB suspend/resume behavior is expected for a battery-powered medical device?