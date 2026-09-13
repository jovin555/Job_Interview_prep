# protocols — Day 54

## Q1: How would you approach debugging a CAN-FD network where a single node occasionally transmits an error frame that corrupts an in-progress message from another node, but only under heavy bus load?

**Answer:** This pattern — errors that appear only under load and are attributable to one node — points toward a node whose bit timing or transceiver behavior degrades when the bus is busy, rather than a fundamental topology problem. I'd structure the investigation in layers.

First, confirm the symptom precisely. Use a CAN analyzer that timestamps every frame and error frame, and capture a long trace under representative load. I want to know: is the offending node transmitting an *active* error flag (which deliberately corrupts the bus) or a passive one? An active error frame means the node detected a bit error, stuff error, CRC error, or form error and is asserting dominance to signal it — so the real question is *why* it thinks it saw an error. That reframes the problem from "this node is broken" to "this node's view of the bus diverges from everyone else's."

Second, look at bit timing. CAN-FD has separate arbitration-phase and data-phase bit rates, and the sample point and SJW (synchronization jump width) must be consistent across all nodes. A node with a marginal sample point — say, sampling too early in the data phase — will work fine at low load but start mis-sampling when accumulated phase error from a long dominant-to-recessive sequence pushes the edge past its sample point. I'd verify each node's nominal bit timing registers and confirm the sample point is in the recommended 75–80% region for the data phase.

Third, consider the physical layer. Under heavy load the average bus voltage and the number of transitions change, which can expose marginal termination, excessive stub length, or a transceiver with slow loop delay. A node at the end of a long stub, or one whose transceiver has a longer loop delay than the others, can fall out of synchronization exactly when the bus is busiest. I'd check termination at both ends, measure stub lengths against the bit-rate limit, and scope the differential signal at the offending node's pins versus a known-good node.

Fourth, check for a firmware-level cause: is the node's transmit path being starved by a higher-priority interrupt, causing it to miss the start of a frame or to lose arbitration and then mis-handle the retry? A node that loses arbitration and immediately retries without respecting the intermission period can generate form errors.

The fix depends on the root cause — retune bit timing, fix termination, shorten a stub, or correct the firmware retry logic — but the diagnostic discipline is the same: separate "the node is faulty" from "the node's timing or electrical margin is the weakest link, and load exposes it."

**Possible follow-ups:**
- How would you determine the correct sample point and SJW for a given bus length and bit rate?
- If the trace shows the node going error-passive and recovering repeatedly, what would that tell you about the failure mode?

## Q2: How would you approach choosing between a star topology and a daisy-chain topology for a multi-drop sensor network in a medical device, given that the sensors are physically distributed?

**Answer:** The topology choice is really a question about the electrical characteristics of the physical layer, the mechanical constraints of the device, and the failure behavior you can tolerate — so I'd evaluate it against those three axes rather than picking a default.

Start with the physical layer. RS-485 and CAN are designed for a linear bus with termination at both ends and short stubs. A true star — where every node connects to a central point — creates a situation where you can't terminate properly: any termination you add is at the hub, not at the electrical ends of each branch, so reflections and standing waves appear. If the "star" is really a set of short branches off a central backbone, that's a different case and may be acceptable if each stub is short relative to the bit rate. So the first question is whether the distribution is genuinely star-like or just a bus with taps.

Second, mechanical and serviceability constraints. In a medical device, sensors may be in different physical modules — a patient-side pod, a display unit, a pump — connected by cables. A daisy-chain forces the signal to pass through every node, so a single node's connector or transceiver failure can break the bus for everything downstream. A star or a hub-and-spoke arrangement isolates failures better but costs more cable and a hub. For a device where a mid-chain failure would take down monitoring, that reliability difference matters.

Third, determinism and latency. On a linear bus, propagation delay is roughly proportional to total length, and arbitration (on CAN) or polling (on RS-485) is straightforward. In a star with a hub, you either need a repeater/hub that adds latency and jitter, or you accept that the "star" is really multiple point-to-point links, which changes the protocol entirely.

My practical approach: if the sensors are distributed along a cable run and the protocol is RS-485 or CAN, I'd default to a linear bus with proper termination and keep stubs short — that's what the standards assume. If the physical layout genuinely forces a star, I'd either use a hub/repeater designed for that purpose, or switch to a point-to-point topology (e.g., each sensor on its own link to a controller) and accept the extra wiring. I'd also prototype the worst-case node placement and measure signal integrity at the extremes before committing.

**Possible follow-ups:**
- How would you calculate the maximum allowable stub length for a given bit rate?
- If you had to use a star because of mechanical constraints, what would you do to preserve signal integrity?

## Q3: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol does not have a built-in backpressure mechanism?

**Answer:** When the protocol has no native backpressure, you have to add flow control at a layer the protocol doesn't know about — either in hardware, in the framing, or in the application's buffering strategy. I'd work through the options in order of how invasive they are.

First, check whether hardware flow control (RTS/CTS) is available. If the UART peripheral and the connector have spare pins, enabling RTS/CTS is the cleanest solution: the receiver deasserts CTS when its buffer is nearly full, and the transmitter pauses. The catch is that it only works if both ends support it and the cable carries the extra signals. On a two-wire link it's not an option.

Second, if hardware flow control isn't available, add a software flow-control mechanism at the framing layer. The classic approach is XON/XOFF: the receiver sends a special byte to pause and resume transmission. The problem is that XON/XOFF bytes can appear in the payload, so you need either an escaping scheme or a framing protocol that reserves those bytes. In a medical device, I'd be cautious about XON/XOFF because a corrupted flow-control byte can either stall the link or cause data loss, and that's hard to reason about for safety.

Third, if neither of those is acceptable, solve it at the application layer with a request/response or windowed protocol. Instead of the transmitter streaming freely, the receiver acknowledges each block and the transmitter only sends the next block when it has room. This adds latency and protocol complexity but gives you deterministic behavior and a natural place to add sequence numbers and CRCs. For a medical device, this is often the right trade because it makes the failure modes explicit and testable.

Fourth, as a mitigation rather than a fix, increase the receiver's buffer and use DMA so the CPU isn't the bottleneck. If the receiver is dropping bytes because an interrupt handler is too slow, DMA plus a larger ring buffer may eliminate the problem without changing the protocol. But I'd treat this as buying margin, not as a substitute for flow control — if the average data rate can exceed the receiver's sustained rate, no buffer size is enough.

My decision would hinge on: do both ends support RTS/CTS, is the link safety-critical, and can I change the protocol? For a safety-critical medical link, I'd lean toward a windowed application-layer protocol with explicit acknowledgements, because it makes the backpressure visible and testable rather than relying on a byte that might get corrupted.

**Possible follow-ups:**
- How would you test that the flow-control mechanism actually prevents loss under worst-case load?
- What are the risks of XON/XOFF in a binary protocol, and how would you mitigate them?

## Q4: You're debugging a system where a USB 2.0 device enumerates correctly on most hosts but fails on a specific embedded host controller. The device uses a composite descriptor with both HID and vendor-specific interfaces. How would you approach isolating whether the problem is in the descriptor configuration, the host controller driver, or the device firmware?

**Answer:** The fact that it works on most hosts but fails on one tells me the device is probably *mostly* compliant, and the failure is either a corner of the spec the embedded host enforces strictly, or a timing/behavior difference in that host's stack. I'd isolate the layer by layer, using the fact that enumeration is a well-defined sequence.

First, capture the actual enumeration traffic. A USB analyzer on the failing host will show exactly where it stops: does the host fail to read the device descriptor, the configuration descriptor, the string descriptors, or does it fail at Set Configuration or at the first class-specific request? That single observation usually narrows the problem by half. If the host never even issues a GET_DESCRIPTOR, the issue is likely electrical or at the port level. If it reads descriptors but rejects the configuration, it's a descriptor or power-budget issue. If it configures but the interface doesn't work, it's a class or endpoint issue.

Second, if the failure is at descriptor parsing, look for things embedded hosts are strict about: the total configuration descriptor length must match the sum of the interface, endpoint, and class-specific descriptors; the bMaxPower must be within the host's capability; the interface association descriptor (if used) must be correct; and the HID report descriptor must be well-formed. A common failure is a composite device that declares more endpoints or more power than the embedded host's root port can supply, or a HID descriptor that a full-featured host tolerates but a minimal host rejects.

Third, if the descriptors look correct, compare the host controller driver behavior. Embedded hosts often use a different USB stack (e.g., a minimal EHCI or OHCI implementation) that may not handle certain transfer types or may have a shorter timeout. I'd check whether the failure correlates with a specific request — for example, a control transfer that the device NAKs for too long, or a descriptor request the device answers slowly. If the device firmware has a long delay before responding to a control request, a host with a short timeout will fail where a desktop host succeeds.

Fourth, if it's firmware, look at the device's response timing and error handling. Does the device handle a SET_ADDRESS followed immediately by a GET_DESCRIPTOR without a delay? Does it handle a request for a descriptor larger than it expects? Does it correctly stall unsupported requests rather than returning garbage? A device that returns a malformed response to an unusual-but-legal request will pass on tolerant hosts and fail on strict ones.

The isolation strategy is: use the analyzer to find the exact failing step, then test that step against the spec, then compare the device's behavior on a known-good host to see if the difference is timing, descriptor content, or request handling. That tells you whether to fix the descriptor, the firmware, or to document a host-specific workaround.

**Possible follow-ups:**
- How would you determine whether the embedded host's timeout is shorter than the USB spec allows?
- If the issue is a descriptor the host rejects, how would you decide between fixing the descriptor and adding a workaround?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd treat this as a design trade-off discussion rather than a yes/no, and I'd guide the team to evaluate it against the system's real-time requirements and failure modes. The junior engineer's instinct — save pins — is legitimate; the question is whether the cost in latency and complexity is acceptable.

First, I'd ask the team to characterize the timing requirements of each source. The GPIO alarm input is the critical one: in a medical device, an alarm is often the highest-priority event, and its latency budget may be tight. If the alarm shares an interrupt line with a chatty UART, the alarm handler can't run until the firmware has polled the UART, the SPI sensor, and the GPIO to figure out which one fired. That polling takes time, and worse, it's nondeterministic — it depends on how much data the UART has queued. So the first question is: what's the worst-case latency for the alarm, and does shared-interrupt polling meet it?

Second, I'd ask about the failure modes. With a shared interrupt, a stuck or noisy peripheral can hold the line asserted and starve the others. If the SPI sensor's interrupt is level-triggered and its condition isn't cleared correctly, the CPU can spend all its time in the shared handler and never service the alarm. That's a safety concern in a medical device. With separate lines, a fault in one peripheral is contained.

Third, I'd ask about the firmware complexity. Polling three peripherals in one handler is simple in principle, but it has to be done carefully: read each peripheral's status, clear only the source that fired, and handle the case where two fired simultaneously. If the handler isn't reentrant or if clearing one source accidentally clears another, you get missed interrupts. That's a subtle bug class that's hard to test for.

Fourth, I'd weigh the pin savings against the cost. If the microcontroller genuinely doesn't have three free interrupt-capable pins, the shared line may be the only option — but then I'd want the design to mitigate the risks: make the alarm input edge-triggered and latch it in hardware so it can't be missed, give the alarm its own dedicated line if at all possible, and document the worst-case latency. If pins are available, separate lines are almost always the better choice for a safety-critical system.

My guidance to the team would be: don't reject the idea outright, but make the junior engineer quantify the latency and enumerate the failure modes. If the analysis shows the alarm latency is acceptable and the failure modes are contained, the shared line is defensible. If not, spend the pins. The review's job is to make the trade-off explicit, not to win the argument.

**Possible follow-ups:**
- How would you measure the worst-case latency of a shared interrupt handler in practice?
- If you had to use a shared interrupt line, what hardware or firmware techniques would you use to keep the alarm path deterministic?