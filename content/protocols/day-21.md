# protocols — Day 21

## Q1: How would you approach designing a communication architecture for a medical device where a central controller needs to communicate with multiple sensor modules, some requiring deterministic real-time response and others generating high-volume data, while keeping the system modular and testable?

**Answer:** I'd start by separating the requirements into two dimensions: timing criticality and data volume. For the deterministic real-time sensors, I'd look at protocols with bounded latency and priority arbitration — CAN-FD is a strong candidate because its message ID priority scheme gives you worst-case latency guarantees you can actually calculate. For high-volume data, I'd consider whether it truly needs to share the same physical bus or whether a separate higher-bandwidth path (like SPI or USB) makes more sense.

The key architectural decision is whether to use one bus or multiple. A single CAN-FD bus can handle both if you carefully budget the bandwidth and assign priorities — safety-critical messages get low ID numbers, telemetry gets higher IDs. But if the high-volume data is continuous and large, mixing it with deterministic traffic on the same bus creates analysis complexity. I'd model the worst-case bus load including the high-priority message's blocking time before committing.

For modularity, I'd define a clean protocol abstraction at the application layer — each sensor module presents a standardized interface regardless of the underlying transport. This lets you test each module in isolation with a loopback or simulator, then integrate incrementally. I'd also build in a test mode where the central controller can exercise each sensor module with known test patterns, which pays off enormously during both development and regulatory testing.

**Possible follow-ups:**
- How would you handle the case where a low-priority telemetry message is starved by higher-priority traffic?
- What metrics would you track during integration testing to validate your bus utilization model?

---

## Q2: You're debugging a system where a USB 2.0 device enumerates correctly on most hosts but fails on a specific embedded host controller. The device uses a composite descriptor with both HID and vendor-specific interfaces. How would you approach this?

**Answer:** I'd approach this systematically, starting with the most common causes of host-specific enumeration failures. First, I'd capture the full enumeration traffic with a USB protocol analyzer on both a working host and the failing one, comparing the descriptor requests and responses. The issue is often in how the host parses the configuration descriptor — some embedded hosts are stricter about descriptor ordering, alignment, or the exact values in the interface class codes.

Next, I'd check the device's response timing. Some hosts are sensitive to how quickly the device responds to control transfers, especially during the initial setup stage. If the device firmware is slow to respond because it's initializing other peripherals, a stricter host might time out. I'd also verify that the device handles standard requests it doesn't specifically support — like GET_DESCRIPTOR for string descriptors in a different language — by returning the correct stall or response rather than ignoring the request.

Another common issue is with the HID descriptor itself. Some hosts expect the report descriptor to be retrieved with a specific request type, and if the device only supports the short form or has an incorrect descriptor length, it can cause enumeration to fail on more particular hosts. I'd also check whether the device is properly handling bus reset and re-enumeration, since some hosts issue multiple resets during the enumeration sequence.

Finally, I'd look at the electrical layer — the embedded host might have different pull-up or pull-down characteristics, or the device's D+ pull-up might be marginal. A scope capture of the D+ and D− lines during the reset and enumeration sequence would reveal signal integrity issues that only manifest with certain host controllers.

**Possible follow-ups:**
- How would you structure the firmware to make the device more tolerant of hosts that issue unusual descriptor requests?
- What role does the device descriptor's `bMaxPacketSize0` field play in enumeration compatibility?

---

## Q3: How would you approach calculating pull-up resistor values for an I2C bus that must support both standard-mode (100 kHz) and fast-mode (400 kHz) operation, with multiple devices on the bus?

**Answer:** The pull-up calculation is a trade-off between rise time and current consumption. The I2C spec defines maximum rise times: 1000 ns for standard mode and 300 ns for fast mode. The pull-up resistor, together with the total bus capacitance, forms an RC time constant that determines the rise time.

I'd start by estimating the total bus capacitance — each device's pin capacitance, the PCB trace capacitance (typically 1–2 pF per centimeter for a 50-ohm trace, but for I2C it's more about the physical geometry), and any connector or cable capacitance. A typical estimate might be 10–20 pF per device plus trace capacitance.

The minimum pull-up resistance is determined by the maximum sink current of the devices' open-drain outputs — typically 3 mA for standard-mode devices and 20 mA for fast-mode. The formula is R_min = V_cc / I_ol_max. For a 3.3V bus, that's roughly 165 ohms for fast-mode devices. The maximum resistance is determined by the required rise time: R_max = t_rise / (0.8473 × C_bus) — the 0.8473 factor comes from the RC charging curve to reach the logic-high threshold.

For a bus that must support both modes, I'd calculate R_max for fast mode (300 ns rise time) since that's the tighter constraint, and verify that the resulting value also works for standard mode. I'd also check that the minimum resistance doesn't exceed the combined sink current capability of all devices that might drive the bus simultaneously — though in normal operation only one device drives at a time.

In practice, I'd also consider using a series resistor or a split pull-up configuration if the bus capacitance is high, and I'd verify the calculation with a scope measurement of the actual rise time on the prototype.

**Possible follow-ups:**
- How would the calculation change if the bus has devices operating at different voltage levels?
- What are the symptoms you'd expect to see if the pull-ups are too weak versus too strong?

---

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single RS-485 bus for a medical device system with 24 sensor nodes distributed along a 200-meter cable run. The system needs to poll each sensor every 50 ms, and each sensor responds with 32 bytes of data. The engineer argues that at 115200 baud, the bus can handle the throughput. How would you guide the team to evaluate this approach?

**Answer:** I'd guide the team to evaluate this on three axes: throughput, timing determinism, and electrical robustness.

First, throughput. At 115200 baud with 8 data bits, 1 stop bit, and no parity, each byte takes about 87 microseconds. A 32-byte response is roughly 2.8 ms, plus overhead for the poll command, inter-frame gaps, and turn-around time. With 24 nodes polled every 50 ms, the total time is 24 × (poll time + response time + turn-around time). If each poll-response cycle takes about 3.5 ms, the total is 84 ms — which exceeds the 50 ms polling interval. So the engineer's throughput argument likely fails on the math alone, even before considering protocol overhead.

Second, timing determinism. Even if the throughput barely fits, the system has no margin for error. Any retransmission, noise-induced corruption, or a sensor that's slow to respond would push the polling cycle over the 50 ms budget. I'd ask the engineer to calculate the worst-case latency including retries, and to consider whether the 50 ms requirement is a hard real-time constraint or a soft target.

Third, electrical robustness. A 200-meter run at 115200 baud is feasible with proper termination, but 24 nodes on a single bus creates stub length concerns. Each node's connection to the bus should be as short as possible — ideally less than 0.3 meters at these speeds. I'd also discuss fail-safe biasing, since 24 transceivers on the bus increase the chance of all nodes being in a disabled state, which leaves the bus floating and susceptible to noise.

I'd also raise the question of whether a single bus is the right topology at all. With 24 nodes, a star or multi-drop configuration with multiple buses might be more manageable — for example, four buses with six nodes each, which reduces stub issues and isolates faults to a smaller segment.

**Possible follow-ups:**
- How would you calculate the exact worst-case polling time including protocol overhead?
- What would you recommend as an alternative architecture if the single-bus approach doesn't meet the requirements?

---

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** I'd approach this in three phases: immediate response, root-cause analysis, and process improvement.

In the immediate response, my priority is to understand the scope of the issue and communicate transparently with stakeholders. I'd work with the engineer to characterize exactly what's failing — is it a protocol conformance issue, an interoperability problem, or a safety-related failure? I'd want to know whether this affects all devices or only certain configurations, and whether there's a workaround that allows testing to continue on other aspects of the device while the fix is developed.

For the root-cause analysis, I'd use a structured method like 5 Whys or a fishbone diagram. The question isn't just "what did the engineer do wrong" but "what gaps in our process allowed this to reach compliance testing undetected." Common contributors might include: inadequate test coverage in the protocol conformance test plan, lack of peer review on the protocol implementation, unclear requirements that led to misinterpretation, or insufficient integration testing with real hardware. I'd be careful to focus on the process gaps rather than assigning blame to the individual.

For process improvement, I'd look at what verification steps could have caught this earlier. This might include adding protocol conformance testing earlier in the development cycle, implementing automated protocol-level tests that run on every build, or adding a design review checkpoint specifically for communication protocol implementations. I'd also consider whether the requirements documentation was clear enough — if the engineer misinterpreted the spec, the spec itself might need clarification.

Throughout this, I'd maintain a supportive stance with the junior engineer. The goal is to fix the issue and prevent recurrence, not to create a culture of fear around mistakes. I'd involve them in the root-cause analysis and the fix, which turns the experience into a learning opportunity.

**Possible follow-ups:**
- How would you balance the need for thorough root-cause analysis with the pressure to fix the issue quickly and resume testing?
- What specific test cases would you add to the protocol conformance test plan to prevent similar issues in the future?