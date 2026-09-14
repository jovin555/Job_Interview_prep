# protocols — Day 55

## Q1: How would you approach designing a multi-drop sensor network where some nodes need deterministic, low-latency response and others generate bursty high-volume data, and both must share the same physical medium?

**Answer:** The first step is to separate the two traffic classes conceptually before choosing a physical layer, because the requirements pull in opposite directions. Deterministic low-latency traffic wants a protocol with bounded arbitration time and priority encoding — CAN-FD is a natural fit because its arbitration field gives you priority-based access with a calculable worst-case latency, and its data-phase bit rate lets you pack a useful payload into a short frame. Bursty high-volume traffic wants raw throughput and is tolerant of jitter, which is where a shared bus starts to hurt: a long telemetry frame occupies the medium and delays the control frame behind it.

The practical approaches are: (1) keep one physical bus but enforce strict priority and frame-length discipline — cap telemetry payloads, fragment them, and never let a low-priority node hold the bus for more than one frame time; (2) physically or logically partition — give the deterministic traffic its own bus or its own time slots, and let telemetry use the remaining bandwidth; or (3) use a time-triggered schedule where the control traffic has reserved slots and telemetry fills the gaps. The decision hinges on the actual worst-case latency budget for the control message, the total telemetry bandwidth, and whether the two classes can tolerate being on the same medium at all. I'd model the bus utilization and compute the worst-case response time for the highest-priority frame before committing, rather than assuming the higher data rate solves it.

**Possible follow-ups:**
- How would you compute the worst-case latency of the highest-priority frame on a CAN-FD bus carrying mixed traffic?
- If the latency budget can't be met on a shared bus, how would you decide between adding a second bus versus moving to a time-triggered schedule?

## Q2: You're debugging a CAN-FD network where one node intermittently goes error-passive and then recovers on its own, with no obvious pattern. How would you approach this?

**Answer:** Error-passive means the node's transmit error counter or receive error counter crossed the threshold, so the first question is which counter and why. I'd start by capturing the error counters and the error frames themselves over a long run — many CAN controllers expose the TEC/REC values and the last error code, which tells you whether it's a bit error, stuff error, CRC error, form error, or ACK error. That single piece of information usually narrows the search dramatically.

If it's a transmit error counter climbing, the node is losing arbitration repeatedly or its transmissions are being corrupted — check for a node with a dominant bit stuck, a marginal transceiver, or a termination problem that only manifests at certain temperatures or cable positions. If it's the receive error counter, the node is seeing corrupted frames from elsewhere, which points at the bus itself: reflections from excessive stub length, missing or doubled termination, or a common-mode shift outside the transceiver's range. The fact that it recovers on its own suggests the error condition is transient and load- or environment-dependent, so I'd correlate the events with bus load, temperature, and physical activity near the harness. I'd also verify the bit timing and sample point settings across all nodes — a node with a mismatched sample point can pass at low load and fail intermittently at high load.

**Possible follow-ups:**
- How would you determine whether the problem is the node's own transceiver versus the bus wiring?
- What would you change in the network design to make a single marginal node less able to disrupt the whole bus?

## Q3: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol has no built-in backpressure mechanism?

**Answer:** The cleanest fix is to add backpressure at a layer the receiver controls. If the hardware supports RTS/CTS, use it — it's the lowest-latency option because the receiver deasserts the line before its buffer overflows, and the transmitter pauses mid-stream without any protocol change. If hardware flow control isn't available, the options are software flow control (XON/XOFF) or a credit/window scheme at the application layer. XON/XOFF is simple but fragile: it can't be used if the payload can contain the XON/XOFF byte values, and it adds latency because the transmitter only reacts after the receiver has already sent the character.

A more robust approach is a framed protocol with sequence numbers and an explicit ACK/window, so the receiver advertises how much buffer space it has and the transmitter never sends more than that. This costs you framing overhead and a round-trip of latency, but it's deterministic and doesn't depend on in-band control characters. The choice depends on the latency budget and whether the link is point-to-point or shared. Regardless of mechanism, I'd also look at why the receiver can't keep up — if it's a firmware architecture problem (blocking in an ISR, no DMA, oversized critical sections), fixing that may be cheaper than adding a flow-control layer.

**Possible follow-ups:**
- What are the failure modes of XON/XOFF that make it unsuitable for binary payloads?
- How would you size the receiver buffer given a known worst-case service latency?

## Q4: How would you approach choosing between a star topology and a daisy-chain topology for a multi-drop sensor network in a medical device where the sensors are physically distributed?

**Answer:** The topology choice is really a trade between wiring complexity, signal integrity, and fault containment. A daisy-chain (bus) topology is the classic choice for RS-485 and CAN because it minimizes stub length — each node taps the bus with a very short stub, which keeps reflections manageable at higher bit rates. Its weakness is that a single break in the bus segments the network, and a faulty node can load down the whole bus. A star topology puts each node on its own branch, which contains faults better and can simplify cable routing when sensors are physically spread out, but the long branches act as stubs and cause reflections unless you use a repeater or a hub at the center, which adds cost and a single point of failure.

In practice, for a distributed medical sensor network I'd lean toward a bus/daisy-chain with short stubs and proper termination at both ends, because it's the best-understood configuration for multi-drop differential signaling and it scales to the cable lengths these systems typically use. I'd only go to a star if the physical layout made daisy-chaining impractical, and then I'd budget for a hub or repeater and verify the signal integrity at the branch points. The decision also depends on the protocol: CAN-FD and RS-485 both assume a linear bus, so a star forces you to either accept degraded margins or add active components.

**Possible follow-ups:**
- How would you terminate a star topology if you were forced to use one?
- What's the relationship between stub length and maximum bit rate on a multi-drop bus?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging the legitimate motivation — pin count matters, and on a constrained MCU sharing an interrupt line is a real technique. Then I'd walk through the failure modes. The core problem is that the shared line turns a hardware event into a software search: when the ISR fires, the firmware has to read each peripheral's status register to find the source, and that takes time. For the alarm input, that latency may be unacceptable — an alarm is exactly the kind of event where you don't want to be polling two other peripherals first. For the UART, if the shared ISR is slow to identify the source, you can overrun the receive FIFO. For the SPI sensor, the interrupt is often just a data-ready signal, which is more tolerant of a few microseconds of delay.

I'd ask the team to quantify the worst-case service latency for each source and compare it to each peripheral's timing requirement. If the alarm and UART both need sub-microsecond response, sharing is probably wrong. If the SPI sensor is the only latency-tolerant source, a better design might be to share the line between the SPI sensor and something else, or to use a small amount of external logic to OR the sources into separate MCU pins if pins are truly scarce. I'd also point out that "poll to find the source" is fine as a fallback but shouldn't be the primary mechanism for a safety-relevant alarm. The goal is to make the trade-off explicit rather than accept the pin-saving argument at face value.

**Possible follow-ups:**
- How would you measure or estimate the worst-case ISR service latency for a shared interrupt line?
- If pins are genuinely exhausted, what external logic could you add to separate the sources without changing the MCU?