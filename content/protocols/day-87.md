# protocols — Day 87

## Q1: How would you approach debugging a CAN-FD network where a node occasionally transmits an error frame that corrupts an in-progress message from another node, but only under heavy bus load?

**Answer:** The "only under heavy load" qualifier is the most important clue — it points away from a static configuration error and toward something timing- or arbitration-dependent. I'd start by capturing the bus with a CAN analyzer that timestamps frames and decodes error frames, then correlate the error frames against bus utilization. A few hypotheses worth separating:

First, bit-timing and sample-point mismatch. Under light load, a node with a slightly off sample point may still sample correctly because the accumulated phase error stays within the resynchronization jump width. Under heavy load, back-to-back frames reduce the idle time available for resynchronization, so the same node starts mis-sampling and flags bit errors — which it then reports as an error frame, corrupting whatever was in flight. I'd verify each node's nominal bit rate, data-phase bit rate, and sample point against the network's intended values, and check that the SJW is large enough to absorb oscillator tolerance across all nodes.

Second, transceiver and physical-layer margin. Heavy load means more transitions and more current draw; a marginal transceiver, an unterminated stub, or a long drop can push a node's dominant/recessive levels outside the differential window at the moment of highest activity. I'd scope the differential signal at the offending node's pins during a load burst and look at rise/fall times, ringing, and common-mode shift.

Third, error counters and state. If the node is drifting toward error-passive, its behavior changes — it stops sending active error flags and its recovery timing shifts. Reading each node's transmit/receive error counters over time would show whether the offending node is accumulating errors before it emits the frame that corrupts others.

The fix depends on which hypothesis holds: retune bit timing and SJW, fix termination/stub layout, or replace a marginal transceiver. I'd also add a regression test that runs the network at worst-case load for an extended period, since this class of fault rarely shows up in short bench runs.

**Possible follow-ups:**
- How would you determine the correct sample point for a CAN-FD network with mixed node vendors?
- If the error frames only appear when a specific pair of nodes transmits back-to-back, what would that tell you?

## Q2: How would you approach designing a protocol abstraction layer so that application code can talk to sensors over I2C, SPI, UART, or CAN-FD without knowing which transport is underneath?

**Answer:** The goal is to keep the application's vocabulary about *what* it wants — read a temperature, set a gain, stream samples — separate from *how* those bytes move. I'd define a small transport interface that every physical layer implements: open/close, a read and a write that take a buffer and length, and a way to report status (busy, error, timeout). Above that, a device-level layer maps a logical sensor operation onto one or more transport transactions, so a register read over I2C and the equivalent over SPI look identical to the caller.

The tricky parts are the things that don't abstract cleanly. Latency and determinism differ enormously between transports — an I2C read at 400 kHz and a CAN-FD frame have very different timing envelopes — so the interface needs to expose enough for the application to reason about deadlines without hard-coding a transport. Error semantics also differ: a NACK, a framing error, and a bus-off condition are not the same failure, and collapsing them into one "error" code loses information the application may need for retry or fail-safe behavior. I'd keep a transport-specific error code alongside a normalized one.

I'd also resist over-abstraction. If the application only ever uses one transport for a given sensor, forcing it through a generic layer adds indirection and hides timing. The abstraction earns its keep when the same logical device genuinely needs to run over more than one physical interface — for example, a bench variant over UART and a production variant over CAN-FD — or when you want to unit-test device logic against a mock transport.

Finally, I'd make the layer testable in isolation: a fake transport that can inject timeouts, partial reads, and errors lets you exercise the device logic without hardware, which is where most of the value of the abstraction actually shows up.

**Possible follow-ups:**
- How would you handle a transport that supports block reads and one that only supports single-register reads behind the same interface?
- Where would you put retry logic — in the transport layer or the device layer?

## Q3: You're designing a half-duplex RS-485 link where the driver-enable and receiver-enable must switch at exactly the right moment, and the turnaround budget is tight. How would you approach this?

**Answer:** Half-duplex RS-485 turnaround is a timing problem with three distinct windows to get right: when to assert the driver, when to release it after the last bit, and when to re-enable the receiver. Getting any of them wrong produces either a truncated final byte, a collision with the responder, or a lost first byte.

The critical detail is that the UART's "transmit complete" flag usually fires when the last bit leaves the shift register, but the transceiver still needs the line to settle and the last bit to propagate. If you de-assert the driver on the transmit-complete interrupt alone, you can chop the stop bit. The safe approach is to wait for transmit-complete *and* account for the transceiver's propagation delay and the line's settling time — often a small hardware or timer delay after the flag. Some transceivers have a built-in auto-direction feature that handles this in silicon; where the budget is tight, that's worth considering because it removes firmware jitter from the equation.

On the receive side, you generally want the receiver enabled whenever you're not driving, so you don't miss the responder's first byte. The risk is that enabling the receiver while your own driver is still active causes you to hear your own transmission as an echo. The fix is to sequence driver-off before receiver-on, with the receiver enabled by default and only disabled during the transmit window if self-echo is a problem.

For a tight turnaround budget, I'd measure the actual round-trip: driver assert to first bit on the wire, last bit to driver release, and the responder's reaction time. If the budget is genuinely tight, the levers are a faster transceiver, a higher baud rate, or moving the turnaround decision into hardware (a timer or the transceiver's auto-direction) so firmware scheduling jitter doesn't eat into the margin. I'd also add a guard time between the end of one transmission and the start of the next, sized to the worst-case node reaction, rather than assuming the responder replies instantly.

**Possible follow-ups:**
- How would you size the guard time if nodes have different firmware reaction latencies?
- What happens if two nodes both think the bus is idle and drive at the same time?

## Q4: How would you approach choosing between a star topology and a daisy-chain topology for a multi-drop sensor network in a medical device where the sensors are physically distributed?

**Answer:** The choice is driven by the electrical characteristics of the physical layer, the cable routing in the actual device, and the failure behavior you can tolerate — not by a generic preference.

A daisy-chain (or bus) topology is the natural fit for differential buses like RS-485 and CAN, because it keeps stub lengths short and termination simple: one terminator at each end of the main run, with each node tapping the bus through a short drop. It's also the cheapest in cable and connectors. The catch is that a break in the chain can split the network, and the physical routing has to actually be a chain — if the sensors are spread around a patient frame in a way that forces long stubs, the daisy-chain advantage disappears and reflections become a problem.

A star topology centralizes the connection point, which makes fault isolation easier — a failed node or cable affects only its own leg — and can simplify routing when sensors are physically clustered around a hub. But for a differential bus, a true star with long legs creates impedance discontinuities and reflections unless you use a hub or repeater, and the total cable length budget is consumed faster. For point-to-point links like UART or USB, star is the natural topology because those aren't multi-drop buses at all.

In a medical device, I'd weigh three things beyond electricals: the routing constraints of the enclosure or patient frame, the fault-tolerance requirement (does losing one sensor's cable take down the whole bus?), and the regulatory/testability angle — a topology that's easy to instrument and test during compliance work is worth a lot. Often the answer is a hybrid: a daisy-chained differential bus for the distributed sensors, with short stubs kept within the stub-length limit, and a separate point-to-point link for any sensor that needs deterministic low latency.

**Possible follow-ups:**
- How would you calculate the maximum stub length for a given bit rate on an RS-485 bus?
- If a sensor must be hot-swappable, how does that affect the topology choice?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging the legitimate motivation — pin count is a real constraint, and sharing an interrupt is a recognized technique. Then I'd walk the team through what the proposal actually costs, because "the firmware can just poll" hides the real trade-offs.

The first question is latency. A shared interrupt means the ISR has to determine which peripheral fired before it can service any of them. If the alarm input is safety-relevant and needs a bounded response, the time spent polling the UART and SPI status registers before discovering the alarm is added latency on the most time-critical path. That may be acceptable or not, but it has to be quantified against the requirement, not assumed.

The second is the polling itself. Reading a peripheral's status register to clear or identify an interrupt can have side effects — some status bits clear on read, some require a specific sequence, and reading a UART's data register to check for a receive interrupt actually consumes the byte. So "just poll" isn't free; it can corrupt state if done carelessly. The team needs to check each peripheral's datasheet for whether a non-destructive status read is even possible.

The third is the failure mode. If two peripherals assert simultaneously, the ISR must handle both without losing either. With a shared line and edge-triggered interrupts, a second event arriving while the first is being serviced can be missed entirely. Level-triggered interrupts avoid that but require the ISR to keep servicing until all sources are clear, which changes the ISR's structure.

My guidance would be: if the alarm input is genuinely safety-critical, give it its own interrupt and share the line between the UART and SPI, which are more tolerant of a few microseconds of identification latency. If pin count truly forces a single shared line, then the design must specify level-triggered interrupts, a documented priority order for servicing, and a test that exercises simultaneous assertion of all three sources. I'd frame it as "here's what we'd need to prove for this to be safe," which keeps the review constructive rather than just rejecting the idea.

**Possible follow-ups:**
- How would you test that no interrupt is lost when two peripherals assert at the same time?
- What changes if the alarm input is level-triggered and stays asserted until acknowledged?