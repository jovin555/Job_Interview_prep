# protocols — Day 3

## Q1: How would you approach calculating pull-up resistor values for an I2C bus that must support both standard-mode (100 kHz) and fast-mode (400 kHz) operation, with multiple devices on the bus?

**Answer:** The pull-up resistor selection for I2C is a trade-off between rise time requirements and current consumption. For a bus that must work at both 100 kHz and 400 kHz, I'd calculate based on the more stringent fast-mode requirements.

First, I'd determine the total bus capacitance by summing the pin capacitance of each device (typically 10 pF per device from datasheets) plus PCB trace capacitance (roughly 1-2 pF per inch of trace). For fast-mode, the maximum allowable rise time is 300 ns, and the RC time constant formula gives us: R_max = t_rise_max / (0.847 × C_bus). This sets the upper resistor limit.

The lower limit is determined by the maximum sink current of the I2C devices, typically 3 mA for standard-mode and fast-mode. Using Ohm's law with V_CC (usually 3.3V or 5V) and V_OL(max) of 0.4V: R_min = (V_CC - V_OL) / I_OL_max.

I'd select a standard resistor value between these two limits, then verify the rise time at 100 kHz (which has a 1000 ns rise time limit, so it's usually fine if fast-mode is satisfied). I'd also check power dissipation: P = V_CC² / R_pullup, which matters for battery-powered devices. If the calculated range is very narrow or nonexistent, that indicates the bus has too much capacitance, and I'd need to use a bus buffer or reduce the number of devices.

**Possible follow-ups:** How would you handle a situation where the calculated resistor range is empty (R_min > R_max)? What impact would adding a bus buffer have on your pull-up calculations?

---

## Q2: In an RS-485 network spanning approximately 200 meters with 16 nodes, how would you approach termination resistor selection and placement?

**Answer:** For a 200-meter RS-485 network, proper termination is critical to prevent signal reflections that cause data errors. The characteristic impedance of typical twisted-pair cable used for RS-485 is around 120 ohms, so I'd start with 120-ohm termination resistors.

The key decision is whether to use one or two termination resistors. For a point-to-point or short bus, a single resistor at the receiver end can suffice. However, at 200 meters with 16 nodes, I'd use two termination resistors — one at each physical end of the bus — to match the characteristic impedance at both extremes. Each resistor would be 120 ohms, placed across the A and B lines.

I'd also consider stub lengths. Each node connection to the main bus creates a stub, and at 200 meters with RS-485, stubs should be kept under about 0.3 meters (roughly 1/10 of the shortest wavelength at the data rate). If longer stubs are unavoidable, I might use lower data rates or consider active repeaters.

For fail-safe biasing, I'd add pull-up and pull-down resistors at one end of the bus to ensure the differential voltage stays above 200 mV when no driver is active. Typical values are 680 ohms pull-up to 5V and 680 ohms pull-down to ground, though this depends on the supply voltage and the number of termination resistors already present.

**Possible follow-ups:** How would your termination strategy change if you needed to support hot-swapping of nodes? What if the cable characteristic impedance is unknown?

---

## Q3: You're designing a USB 2.0 device that must reliably enumerate on hosts with different operating systems. How would you approach implementing the descriptor hierarchy to maximize compatibility?

**Answer:** USB enumeration is a structured negotiation where the host reads descriptors to understand the device's capabilities. For maximum compatibility, I'd follow the USB specification strictly and pay careful attention to several key areas.

First, the device descriptor must report correct values for bcdUSB (version), idVendor/idProduct, and bMaxPacketSize0. For full-speed devices, bMaxPacketSize0 must be 8, 16, 32, or 64 bytes — I'd use 64 bytes for efficiency. The configuration descriptor must accurately report the total length including all subordinate descriptors.

I'd structure the descriptor hierarchy as: device descriptor → configuration descriptor → interface descriptor(s) → endpoint descriptor(s). For a device with multiple functions, I'd use interface association descriptors (IADs) to group related interfaces, which improves compatibility with Windows and Linux.

String descriptors are optional but important for user experience. I'd implement at least a manufacturer string and product string, ensuring they're indexed correctly. The string descriptor zero (language ID array) must be present if any string descriptors are used.

A common compatibility issue is the configuration descriptor total length field. If this value is incorrect, the host may truncate or skip descriptors. I'd verify this programmatically during development by comparing the sum of all descriptor sizes against the declared total length.

For robust enumeration, I'd also ensure the device responds to standard requests within the required time limits — particularly the SET_ADDRESS request, which must be handled within 50 ms. I'd implement a state machine that tracks the enumeration sequence and handles unexpected host requests gracefully.

**Possible follow-ups:** How would you debug a device that enumerates on one host but fails on another? What are the most common descriptor errors that cause enumeration failures?

---

## Q4: How would you approach selecting between RS-422 and RS-485 for a medical device that needs to communicate with multiple sensors distributed across a patient monitoring system?

**Answer:** This selection depends on the specific communication requirements, particularly the network topology and whether bidirectional communication is needed.

RS-422 uses a single driver with multiple receivers — it's inherently simplex or full-duplex (separate transmit and receive pairs). RS-485 uses a single pair of wires in half-duplex mode, with multiple drivers that must take turns controlling the bus.

For a medical monitoring system, I'd consider these factors:

If each sensor only needs to transmit data to a central receiver (one-way communication), RS-422 would be simpler — no need for turn-around timing or driver enable control. The full-duplex capability means the central unit could simultaneously send configuration commands on a separate pair if needed.

If sensors need bidirectional communication (e.g., the central unit sends configuration commands and sensors respond with data), RS-485 is more appropriate because it allows multiple drivers on a single bus. However, I'd need to implement a protocol that manages bus access — typically a master-slave arrangement where the central unit polls each sensor.

For medical applications, I'd also consider:
- **Galvanic isolation**: Both standards support isolation, but RS-485 transceivers with integrated isolation are more common
- **Common-mode voltage range**: RS-485 has a wider range (-7V to +12V vs -7V to +7V for RS-422), which helps in environments with ground potential differences
- **Cable length**: Both support hundreds of meters at reasonable data rates
- **Fault tolerance**: RS-485 transceivers often include short-circuit protection and thermal shutdown

If the system requires bidirectional communication with multiple sensors, I'd lean toward RS-485 with a robust master-slave protocol, ensuring proper fail-safe biasing and termination. If sensors are unidirectional transmitters, RS-422 would be simpler and equally reliable.

**Possible follow-ups:** How would you handle the half-duplex turn-around timing in RS-485 for a system with 10 sensors? What safety considerations would you add for a medical device using these interfaces?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single UART with software bit-banging to communicate with three different sensors, each at different baud rates. How would you guide the team to evaluate this approach?

**Answer:** This is a situation where I'd want to understand the constraints driving the proposal before offering alternatives. I'd start by asking questions to clarify the requirements: What are the data rate and latency needs for each sensor? What are the microcontroller's available resources? Is this for a prototype or production?

Software bit-banging a UART is possible but comes with significant risks. The primary concern is timing accuracy — bit-banging relies on precise software timing loops, which can be disrupted by interrupts, especially in a system with multiple peripherals or an RTOS. At higher baud rates, even a few microseconds of interrupt latency can cause framing errors.

If the three sensors use different baud rates, the bit-banging approach would require reconfiguring the timing parameters each time the UART switches between sensors. This adds complexity and potential for errors if the switching logic isn't carefully implemented.

I'd guide the team through this evaluation:

1. **Check hardware resources**: Does the microcontroller have multiple hardware UARTs? Many mid-range MCUs have 3-5 UART peripherals. If so, using hardware UARTs is almost always preferable — they handle timing precisely, include buffering, and free CPU cycles for other tasks.

2. **Consider protocol alternatives**: If hardware UARTs are limited, could the sensors share a bus? For example, if the sensors support RS-485 or I2C, a single bus with addressing could replace multiple UART connections.

3. **Evaluate the bit-banging approach honestly**: If hardware UARTs truly aren't available and the sensors can't share a bus, I'd ask the engineer to characterize the worst-case interrupt latency and calculate whether the timing margin is adequate at each baud rate. I'd also want to see a plan for handling concurrent data reception — bit-banging can't receive on multiple "ports" simultaneously.

4. **Consider a middle ground**: If one sensor has a low baud rate (e.g., 1200 bps) and the others are higher, perhaps the low-rate sensor could be bit-banged while the others use hardware UARTs.

Ultimately, I'd encourage the team to prioritize reliability over component cost savings, especially in a medical context where communication errors could have clinical consequences. If the bit-banging approach is pursued, I'd recommend extensive testing across temperature and voltage ranges to verify timing stability.

**Possible follow-ups:** What specific test cases would you design to validate the bit-banged UART's reliability? How would you handle the scenario where a high-priority interrupt occurs during a bit-banged transmission?