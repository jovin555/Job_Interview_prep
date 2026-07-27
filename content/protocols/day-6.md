# protocols — Day 6

## Q1: You're designing a medical device that uses USB 2.0 for both charging and data transfer. During compliance testing, the device fails enumeration on certain host controllers. How would you approach debugging this?

**Answer:** I'd start by capturing USB traffic with a USB protocol analyzer or logic analyzer to see exactly where enumeration fails. The enumeration process follows a specific sequence: reset, speed detection, device descriptor request, then configuration descriptor requests. I'd check whether the device responds correctly to each stage.

Common failure points include: incorrect descriptor structure (wrong bMaxPacketSize0 for full-speed vs high-speed), timing violations in response to host requests, or voltage droop on VBUS during inrush current when charging begins. I'd verify the D+/D- termination resistors are correct for the intended speed — for full-speed devices, a 1.5kΩ pull-up on D+; for high-speed, the device must initially present as full-speed then transition.

I'd also check the device's power configuration. If the device draws more than 100mA before enumeration completes (or more than 500mA without a configuration descriptor declaring it as a high-power device), the host may reset or refuse to enumerate. For charging, I'd verify the device properly negotiates charging current through battery charging specification (BC 1.2) or USB PD rather than attempting to draw high current during the enumeration phase.

**Possible follow-ups:** How would you structure the configuration descriptor to support both charging-only mode and data-transfer mode? What happens if the device needs to suspend and resume while charging?

---

## Q2: In a CAN-FD network for a medical device with multiple nodes, you need to ensure that a high-priority safety-critical message is never delayed by more than 500 microseconds. How would you approach guaranteeing this timing requirement?

**Answer:** I'd approach this through a combination of protocol configuration and system-level analysis. First, I'd ensure the safety-critical message uses the lowest CAN-ID (highest priority) in the network, since CAN arbitration gives bus access to the message with the dominant start-of-frame first. This means no other message can delay it — the safety message will win arbitration as soon as the bus is idle.

However, the worst-case delay isn't just arbitration — it's waiting for the current message to finish transmitting. So I'd calculate the maximum blocking time: the longest possible message on the bus (typically a 64-byte data frame at the arbitration bit rate) plus inter-frame spacing. For a 500 kbps arbitration bit rate, a maximum-length standard CAN-FD frame takes roughly 1.2ms, which already exceeds the 500μs requirement.

To meet the timing, I'd consider: using CAN-FD's faster data phase bit rate (e.g., 2 Mbps or higher) to shorten non-safety messages; limiting the maximum DLC of non-critical messages; or using the CAN-FD protocol's transmitter delay compensation to run higher data rates. I'd also verify the bus length supports the chosen bit rates — longer buses require lower bit rates due to propagation delay.

Finally, I'd perform a worst-case response time analysis using tools like CANcalc or RTaW-Pegase, modeling all message periods, priorities, and transmission times to mathematically prove the safety message meets its deadline under all bus load conditions.

**Possible follow-ups:** How would you handle the scenario where a lower-priority message has already started transmitting when the safety message becomes ready? What role does the CAN-FD E2E CRC play in safety-critical applications?

---

## Q3: You're designing an RS-485 network for a patient monitoring system where 24 sensor nodes are distributed across a 300-meter cable run. How would you approach termination resistor selection and placement?

**Answer:** For a 300-meter RS-485 network with 24 nodes, proper termination is critical to prevent signal reflections that cause data corruption. I'd start by determining the characteristic impedance of the chosen cable — typically 120Ω for standard twisted-pair RS-485 cable. The termination resistors should match this impedance.

For a point-to-multipoint network, I'd place a single termination resistor at each end of the main bus cable — not at every node. This means one 120Ω resistor at the master/controller end and one at the farthest physical node. Stub lengths from the main bus to each node should be kept as short as possible (ideally under 0.3 meters at high data rates) to avoid creating impedance discontinuities.

However, with 24 nodes, the total load on the bus becomes significant. Each RS-485 receiver presents a unit load (UL), and standard transceivers are typically 1/8 UL, meaning 24 nodes present 3 unit loads. The termination resistors plus receiver loads create a DC load that the driver must overcome. I'd verify the driver can handle this — most RS-485 drivers can drive up to 32 unit loads.

For fail-safe biasing, I'd add pull-up and pull-down resistors at one end of the bus (typically 680Ω to 1kΩ) to ensure the differential voltage stays above 200mV when no driver is active, preventing the receivers from seeing random noise as valid data. This is especially important in medical devices where false data could be dangerous.

**Possible follow-ups:** How would the termination approach change if you needed to operate at 10 Mbps instead of 115.2 kbps? How would you handle hot-swapping a node without disrupting the bus?

---

## Q4: You're debugging a system where an SPI bus communicates with three sensors on separate chip selects. The bus works correctly at 1 MHz but produces corrupted data at 10 MHz. How would you approach this?

**Answer:** This is a classic signal integrity issue at higher frequencies. I'd approach it systematically:

First, I'd examine the physical layout. At 10 MHz, the signal wavelength is about 30 meters on a PCB, so trace length matching becomes important if the sensors are at different distances. I'd check if the clock and data lines have significantly different lengths — mismatches over a few centimeters can cause setup/hold violations at 10 MHz.

Second, I'd look at the bus capacitance. Each sensor's input capacitance (typically 5-15 pF) plus PCB trace capacitance (roughly 1-2 pF per centimeter) adds up. If the total exceeds the driver's capability, the clock edges will slew, causing timing violations. I'd calculate the RC time constant of the driver output impedance (often 20-50Ω) times total bus capacitance. If the time constant exceeds roughly 1/10 of the clock period, that's a problem.

Third, I'd check the SPI mode configuration. Some sensors have specific setup/hold requirements relative to the clock edge. At 1 MHz, timing margins are generous; at 10 MHz, a 50ns setup time requirement becomes significant. I'd verify the microcontroller's SPI peripheral can meet the sensor's timing requirements at the higher speed.

Fourth, I'd probe the signals with an oscilloscope — looking for overshoot, undershoot, ringing, and slow edges on the clock line. I'd check that the MISO line isn't being contended (all slaves should tri-state their MISO when not selected). I'd also verify the chip select signals have clean edges and proper timing relative to the clock.

Finally, I'd consider adding series termination resistors (22-33Ω) near the master to dampen reflections, and ensure each sensor's chip select trace is properly routed to avoid crosstalk.

**Possible follow-ups:** If one specific sensor works fine at 10 MHz when it's the only device on the bus but fails when other sensors are present, what would you suspect? How would you verify whether the issue is capacitive loading or crosstalk?

---

## Q5: Imagine you're leading a design review where a firmware engineer proposes using a single UART with a software-based protocol multiplexer to communicate with four different sensors, each with different baud rates and protocols. The hardware engineer argues this is unreliable and wants four separate UART peripherals. How would you guide the team to a decision?

**Answer:** I'd frame this as a trade-off analysis that considers reliability, development complexity, and system constraints.

First, I'd ask clarifying questions: What are the data rates and update frequencies for each sensor? Can the microcontroller handle the interrupt load of bit-banging multiple protocols? What are the consequences of a missed or corrupted sensor reading? Is this a safety-critical function?

The firmware engineer's approach has appeal — it saves pins and potentially BOM cost. However, software bit-banging of UART at different baud rates is notoriously tricky. The microcontroller must precisely time each bit, and any interrupt latency (from other peripherals, RTOS tasks, or DMA) can cause framing errors. With four different baud rates, the timing constraints become even tighter because the firmware must switch between different bit-period calculations.

The hardware engineer's approach is more robust — dedicated UART peripherals handle timing in hardware, with hardware FIFOs and automatic baud rate generation. This is almost certainly more reliable, especially in a medical device where data integrity is critical.

I'd suggest a middle-ground evaluation: Could two UARTs with hardware multiplexing (e.g., using analog switches or external UART-to-multi-channel ICs) serve the need? Could the sensors be consolidated to use compatible baud rates? Could the system use a single higher-speed UART with a protocol that addresses individual sensors?

Ultimately, for a medical device, reliability should take priority over pin savings. Unless there's a hard constraint (e.g., the microcontroller literally doesn't have enough UART peripherals and cannot be changed), I'd lean toward the hardware engineer's approach. If pin count is truly constrained, I'd recommend upgrading to a microcontroller with more UART peripherals rather than risking data corruption through software bit-banging.

**Possible follow-ups:** How would you structure a risk assessment to formally compare these two approaches? What testing would you require to validate the software multiplexer approach if the team decided to pursue it despite the concerns?