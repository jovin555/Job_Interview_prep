# protocols — Day 4

## Q1: You're designing a medical device that uses USB 2.0 for both charging and data transfer. How would you approach implementing the device descriptor hierarchy to ensure reliable enumeration across different host operating systems?

**Answer:** The descriptor hierarchy is the foundation of USB enumeration, and getting it right is critical for cross-platform compatibility. I'd start by carefully structuring the standard descriptors in the correct order: device descriptor, configuration descriptor, interface descriptor(s), endpoint descriptor(s), and any class-specific or vendor-specific descriptors. For a medical device that also charges, I'd pay particular attention to the configuration descriptor's `bMaxPower` field, ensuring it accurately reflects the device's maximum current draw during enumeration so the host can properly budget power.

I'd implement the device descriptor with a unique `idVendor` and `idProduct` combination, and set `bcdUSB` to 0x0200 for USB 2.0 compliance. For the configuration descriptor, I'd declare one configuration with the appropriate `bNumInterfaces`. If the device needs both a bulk endpoint for data streaming and an interrupt endpoint for status updates, I'd define separate interfaces or a composite device structure depending on the host driver model.

To maximize compatibility, I'd ensure the string descriptors are present but optional — some embedded hosts skip string retrieval. I'd also verify that the endpoint descriptors have correct `wMaxPacketSize` values (e.g., 64 bytes for full-speed bulk endpoints) and that `bInterval` is set appropriately for interrupt endpoints. Testing against Windows, macOS, and Linux hosts during development is essential, as each OS handles descriptor parsing quirks differently — for instance, Windows is stricter about descriptor ordering than Linux.

**Possible follow-ups:**
- How would you handle the case where a host requests the device descriptor multiple times during enumeration, and what should the device do if it's not ready to respond?
- What are the implications of using a composite device versus a single-interface device for a medical device that needs both HID and bulk transfer endpoints?

---

## Q2: In an RS-485 network for a patient monitoring system with 32 nodes spread across a 500-meter cable run, how would you approach termination resistor selection and placement?

**Answer:** For a 500-meter RS-485 network with 32 nodes, termination is critical to prevent signal reflections that cause data corruption. The characteristic impedance of typical twisted-pair cable used for RS-485 is around 120 ohms, so I'd start with termination resistors equal to that value — usually 120 ohms — placed at each physical end of the bus.

The key decision is whether to use a single termination resistor at each end or a more complex network. For this length and node count, I'd use a single 120-ohm resistor between the A and B lines at each end of the bus. The resistors should be placed as close to the last node's transceiver as possible, with stub lengths kept under 0.3 meters (roughly 1/10 of the shortest wavelength at the signaling rate). With 32 nodes, stubs can accumulate and cause signal degradation, so I'd recommend daisy-chaining nodes along the main trunk rather than using long drop cables.

I'd also consider fail-safe biasing to ensure the bus defaults to a known state when no driver is active. This typically involves pull-up and pull-down resistors on the A and B lines at one end of the bus — for example, a 680-ohm pull-up to 5V on line A and a 680-ohm pull-down to ground on line B. The biasing network must be designed so it doesn't overload the transceivers' common-mode range or draw excessive current.

For a medical device, I'd also verify that the termination and biasing network doesn't interfere with the required isolation barriers. Many medical RS-485 implementations use isolated transceivers to meet IEC 60601 patient leakage current requirements, and the termination resistors should be placed on the isolated side of the barrier.

**Possible follow-ups:**
- How would you calculate the maximum data rate achievable on this 500-meter network given the 32-node loading?
- What failure mode would you expect if termination resistors were placed at every node instead of just the ends?

---

## Q3: You're debugging a UART communication issue where a medical sensor occasionally sends framing errors after several hours of continuous operation. How would you approach this?

**Answer:** Intermittent framing errors that appear after extended operation suggest a drift-related problem rather than a fixed configuration error. I'd approach this systematically:

First, I'd confirm the framing errors are genuine by capturing the actual waveform on an oscilloscope or logic analyzer. A framing error occurs when the stop bit is sampled as a logic low instead of high, so I'd look at the received signal around the stop bit position to see if the line is being pulled low prematurely or if there's noise during that sampling window.

The most common cause is baud rate mismatch or drift. I'd check whether both sides are using the same nominal baud rate and whether their clock sources are stable over temperature. If the sensor uses an internal RC oscillator while the receiver uses a crystal, the RC oscillator may drift with temperature as the device warms up over hours of operation. I'd measure the actual baud rate of the sensor's transmission after several hours and compare it to the receiver's sampling rate. A mismatch of more than about 2-3% at typical UART baud rates can cause framing errors.

Another possibility is ground potential drift. In a medical device with multiple isolated sections, ground references can shift over time due to leakage currents or capacitive coupling. I'd check the common-mode voltage between the transmitter and receiver grounds using a differential probe, especially if the UART lines cross isolation boundaries.

I'd also examine the signal integrity: ringing, undershoot, or slow rise/fall times on the UART line can cause the receiver to sample at the wrong point. This is particularly relevant if the cable length is significant or if there's capacitive loading from ESD protection diodes. Adding a Schmitt trigger buffer or adjusting the drive strength on the transmitter might help.

Finally, I'd review the firmware's UART configuration — is the receiver using proper oversampling (typically 16x), and are the interrupt handlers fast enough to prevent overrun errors that might manifest as framing errors?

**Possible follow-ups:**
- If you found the baud rate was drifting by 1% over temperature, how would you decide whether to use a crystal oscillator or implement software-based baud rate correction?
- How would you distinguish between a framing error caused by baud rate mismatch versus one caused by noise on the stop bit?

---

## Q4: How would you approach selecting between I2C and SPI for a new sensor interface in a battery-powered medical device where the sensor is located on a separate PCB connected by a 15-centimeter flex cable?

**Answer:** For a sensor on a separate PCB connected by a 15-centimeter flex cable in a battery-powered medical device, I'd evaluate several factors:

**Power consumption:** I2C typically uses less power for low-data-rate sensors because it has lower dynamic current (open-drain outputs with pull-ups) and can operate at lower clock speeds. SPI's push-pull drivers consume more current per transition, though it can be more efficient for burst transfers since it completes transactions faster. For a battery-powered device, I'd lean toward I2C if the sensor data rate is low (e.g., temperature or pressure readings every few seconds).

**Cable length and signal integrity:** 15 centimeters is manageable for both protocols, but the flex cable's impedance and capacitance matter. I2C's open-drain architecture means rise times are determined by the pull-up resistors and bus capacitance. A flex cable adds capacitance — typically 1-2 pF per centimeter — so the total bus capacitance might be 30-50 pF including the sensor and PCB traces. I'd calculate the required pull-up resistors to meet the rise time specification for the desired clock speed. For 400 kHz fast-mode, the maximum allowable rise time is 300 ns, which limits the pull-up resistor value based on total capacitance.

**Noise immunity:** SPI's differential signaling (if using LVDS) or single-ended with dedicated return paths is generally more robust against noise than I2C's open-drain lines. In a medical device with motors, pumps, or wireless transmitters nearby, I'd consider whether the flex cable might pick up interference. I2C's lack of error detection at the protocol level means a single noise pulse could corrupt a transaction.

**Complexity and pin count:** I2C uses only two wires (SDA, SCL) regardless of the number of devices, while SPI requires at least three (MOSI, MISO, SCLK) plus a chip select per device. For a single sensor, SPI uses one more pin, which may be acceptable.

**My recommendation:** For a low-data-rate medical sensor (e.g., pressure or temperature), I'd start with I2C at 100 kHz or 400 kHz, carefully calculating pull-up resistors for the flex cable's capacitance. I'd add series resistors (22-33 ohms) at the master's outputs to dampen reflections, and consider using an I2C buffer/repeater if the capacitance exceeds the driver's capability. For higher data rates or noisy environments, I'd use SPI with careful attention to ground return paths in the flex cable — ideally with a dedicated ground trace alongside each signal.

**Possible follow-ups:**
- How would you calculate the maximum I2C bus capacitance for a given pull-up resistor value and clock speed?
- If you chose I2C and later found the flex cable was picking up motor noise, what circuit-level mitigations would you consider before switching protocols?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single SPI bus with daisy-chain configuration to connect four different sensors, each requiring different clock polarity and phase settings. How would you guide the team to evaluate this approach?

**Answer:** This is a design decision that touches on both technical feasibility and team collaboration. I'd guide the evaluation by first acknowledging the junior engineer's thinking — daisy-chaining reduces pin count and can simplify routing — then systematically examining the constraints.

The fundamental problem is that SPI daisy-chain mode requires all devices to use the same clock polarity (CPOL) and clock phase (CPHA) because they share the same SCLK and MOSI lines, with data propagating through the chain. If the four sensors require different CPOL/CPHA settings, daisy-chaining is not viable without additional hardware. I'd explain that SPI's CPOL and CPHA settings determine when data is sampled and shifted relative to the clock edge, and mismatched settings would cause data corruption.

I'd then walk through the alternatives:

1. **Independent chip selects with shared bus:** Use separate chip select lines for each sensor, all sharing the same MOSI, MISO, and SCLK. This requires the master to reconfigure its SPI peripheral's CPOL/CPHA before each transaction. This is feasible if the microcontroller supports per-transfer configuration and the sensors don't need simultaneous access. The trade-off is more GPIO pins for chip selects and potential latency from reconfiguration.

2. **Multiple SPI peripherals:** If the microcontroller has multiple SPI modules, assign each sensor to its own peripheral with dedicated pins. This allows simultaneous configuration but consumes more pins and may not be available on smaller microcontrollers.

3. **SPI mux/demux:** Use an analog multiplexer to route a single SPI bus to different sensors, with the mux's select lines controlled by GPIOs. This keeps the pin count low but adds propagation delay and may limit speed.

4. **Protocol change:** If the sensors support alternative interfaces, consider I2C or a custom protocol that better accommodates the diversity.

I'd frame this as a trade-off analysis: pin count vs. complexity vs. performance vs. future flexibility. I'd encourage the junior engineer to create a comparison table with columns for GPIO usage, maximum data rate, software complexity, and BOM cost. I'd also ask them to consider the system's data rate requirements — if the sensors are sampled infrequently, the overhead of reconfiguring the SPI peripheral may be negligible.

Finally, I'd emphasize that design reviews are about exploring options, not just finding the "right" answer. The goal is to understand the constraints and make an informed decision that balances all factors.

**Possible follow-ups:**
- How would you handle the situation where the junior engineer is strongly attached to the daisy-chain idea and argues that they can make it work with careful timing? How do you balance mentorship with maintaining design quality?
- If you decided to use independent chip selects with shared bus, how would you ensure that reconfiguring CPOL/CPHA between transactions doesn't introduce glitches on the bus?