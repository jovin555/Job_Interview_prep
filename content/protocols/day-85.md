# protocols — Day 85

## Q1: How would you approach designing a protocol abstraction layer so that application code can talk to sensors over I2C, SPI, UART, or CAN-FD without knowing which transport is underneath?

**Answer:** The goal is to invert the dependency: the application should depend on an abstract interface, and each transport should be an implementation of that interface. I'd start by defining a transport-agnostic contract that captures what the application actually needs — typically open/close, a read and a write with a buffer and length, a way to report errors, and some notion of blocking versus non-blocking or asynchronous completion. Crucially, that contract should express *semantics*, not wire details: "read N bytes from register R" rather than "send these raw bytes." If the interface leaks transport-specific concepts like chip-select or arbitration, the abstraction has already failed.

Each transport then implements the contract. A UART implementation wraps a byte stream; an I2C implementation wraps register-oriented transactions; a CAN-FD implementation wraps message frames. Where transports differ fundamentally — for example, CAN-FD is message-oriented while UART is stream-oriented — I'd handle the mismatch in the adapter, not in the application. A common approach is to define a small set of device-level operations (read register, write register, read block) and let each adapter map those onto whatever the underlying bus supports, including any framing or fragmentation needed.

The other half of the design is error handling. Each transport has different failure modes — NACKs and bus lockups on I2C, framing errors on UART, bus-off on CAN-FD — so I'd define a normalized error taxonomy at the interface boundary and translate transport-specific errors into it. That keeps the application's recovery logic transport-independent. I'd also keep timing and retry policy configurable per transport rather than baked into the application, since a retry that makes sense on a short I2C bus may be wrong on a long RS-485 run.

Finally, testability: because the application only sees the interface, I can substitute a mock transport in unit tests and exercise application logic without hardware. That's often the strongest argument for doing the abstraction at all.

**Possible follow-ups:**
- Where would you draw the line between the abstraction layer and the device driver, so the abstraction doesn't become a leaky catch-all?
- How would you handle a transport that supports features the others don't, like CAN-FD's priority arbitration, without polluting the common interface?

## Q2: You're debugging an I2C bus where communication works reliably at 100 kHz but produces intermittent NACKs at 400 kHz, with the same devices and the same PCB. How would you approach this?

**Answer:** The fact that it works at 100 kHz and fails at 400 kHz points strongly at a timing or signal-integrity margin issue rather than a logic bug, because the protocol and devices are unchanged. I'd work through the physical layer first.

The most common cause is bus capacitance combined with pull-up strength. At 400 kHz the rise time budget is much tighter, so a bus that just barely meets timing at 100 kHz can fail to reach the logic-high threshold in time at 400 kHz. I'd measure the actual rise time on SDA and SCL with a scope and compare it against the I2C specification's limit for fast mode. If the edges are too slow, the fix is either reducing effective capacitance (shorter traces, fewer devices, better routing) or lowering the pull-up resistance — but lowering it increases current draw and the low-level sink requirement, so I'd check that every device can still pull the line below VIL.

Second, I'd look at whether the NACKs correlate with specific devices or specific transactions. If one device NACKs, it may be that its internal timing can't keep up at 400 kHz, or it needs clock stretching that the master isn't honoring. I'd check whether the master supports clock stretching and whether the device is actually asserting it.

Third, I'd consider noise and crosstalk. Faster edges couple more aggressively into adjacent traces, so a marginal layout can pass at 100 kHz and fail at 400 kHz. I'd look at whether SDA and SCL run near switching nodes or long parallel runs.

I'd also verify the master's own timing — setup and hold, and whether it's actually generating a clean 400 kHz with the expected duty cycle. Sometimes the "400 kHz" is nominal and the real waveform has jitter or a distorted duty cycle that eats into the margin.

The systematic approach is: scope the waveforms, measure rise/fall times and thresholds, check pull-ups against capacitance, then isolate whether the failure is device-specific or bus-wide.

**Possible follow-ups:**
- How would you calculate the maximum allowable pull-up resistance for a given bus capacitance and target rise time?
- If the scope shows clean edges but you still get NACKs, where would you look next?

## Q3: How would you approach debugging a CAN-FD network where a node occasionally goes bus-off and stays off until the controller is reset, even though the bus itself appears healthy afterward?

**Answer:** Bus-off means the controller's transmit error counter exceeded the threshold, so the node accumulated enough errors to be removed from the bus. The fact that it stays off until reset tells me the firmware isn't implementing automatic recovery, or the recovery is gated on something that never happens. So there are two threads: why the errors accumulated, and why recovery doesn't occur.

On the error side, I'd first capture what's happening on the bus at the moment the node goes off. Bus-off is usually the end of a cascade, not a single event — a node that's slightly out of sync, has a bad sample point, or is transmitting into a bus that another node is also driving will rack up errors quickly. I'd check the bit timing configuration: sample point, propagation segment, and the relationship between arbitration-phase and data-phase bit rates. CAN-FD's dual bit rate is a common source of trouble, because the data phase is much faster and far less tolerant of propagation delay and transceiver skew. If the sample point in the data phase is marginal, a node can work fine at low load and fail under specific timing conditions.

I'd also check for physical issues that only manifest intermittently: termination, stub length, common-mode range, and whether the transceiver is being driven near its limits. A marginal bus can look healthy on a scope at idle but produce errors during arbitration when multiple nodes drive simultaneously.

On the recovery side, I'd look at the controller's error handling configuration. Many CAN controllers support automatic bus-off recovery, but it may be disabled, or the firmware may be waiting for a condition that never occurs. I'd also check whether the node is being held in a reset or error state by application logic. If recovery is implemented, I'd make sure it includes a defined backoff and a re-initialization sequence, and that the node doesn't immediately re-enter bus-off by transmitting into a still-degraded bus.

The disciplined approach is to log the error counters and the last few frames before bus-off, correlate with bus load and other nodes' behavior, and separate "why did errors accumulate" from "why didn't it recover."

**Possible follow-ups:**
- How would you decide whether automatic bus-off recovery is appropriate for a safety-critical medical device, versus requiring an explicit reset?
- What would you check in the bit-timing configuration if errors only appear at high bus load?

## Q4: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol has no built-in backpressure mechanism?

**Answer:** Without protocol-level backpressure, I have to add flow control at a layer the receiver and transmitter both understand. The cleanest option, if the hardware supports it, is RTS/CTS hardware flow control: the receiver deasserts RTS when its buffer is near full, and the transmitter's UART hardware pauses automatically. That's the most robust because it doesn't depend on firmware timing. But it requires spare pins and a transmitter that honors CTS, which isn't always available.

If hardware flow control isn't possible, I'd implement a software handshake at the application layer. The receiver sends an XOFF-style message when its buffer crosses a high-water mark and an XON when it drains below a low-water mark. The transmitter must check for these messages and pause. The catch is that this only works if the transmitter can be paused quickly enough — if it's mid-burst, the receiver's buffer has to absorb the in-flight data. So I'd size the buffer with margin and set the water marks conservatively.

A third option is to restructure the protocol so the transmitter never sends more than the receiver has explicitly requested — a credit-based or request/response scheme. That's often the right answer in a medical device because it makes the data flow deterministic and bounded, at the cost of some throughput.

Regardless of mechanism, I'd define the failure behavior: what happens if the receiver's buffer overflows anyway? Dropping data silently is usually unacceptable in a medical context, so I'd want a detectable error and a defined recovery, such as a resynchronization sequence or a request to retransmit. I'd also test the worst case deliberately — feed the receiver at maximum rate while it's busy with a higher-priority task — to confirm the flow control actually holds.

**Possible follow-ups:**
- How would you size the receiver buffer and set the high/low water marks?
- What are the trade-offs between hardware RTS/CTS and a software XON/XOFF scheme in terms of latency and reliability?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd want the team to separate the two claims: that sharing the line saves a pin, and that polling to identify the source is acceptable. The first is true but small; the second is where the real risk lives, and it depends entirely on the system's timing requirements.

The core question is latency and determinism. With a shared interrupt, the ISR has to poll each peripheral to find which one asserted. That adds latency to every event, and worse, it makes the worst-case latency depend on how many peripherals are checked and how long each check takes. For a GPIO alarm input in a medical device, that latency may be unacceptable — an alarm that's delayed by a few hundred microseconds while the firmware checks the UART and SPI first could matter. I'd ask the junior engineer to state the required response time for each source and show that the polling approach meets the tightest one.

There's also a correctness hazard: if two peripherals assert at nearly the same time, the ISR might service one and miss the other, or the second event could be lost if the flag is cleared incorrectly. With separate interrupt lines, the hardware queues them. With a shared line, the firmware has to guarantee it drains all sources before returning, which is easy to get wrong.

I'd also raise the diagnostic angle. A shared line makes it harder to tell which peripheral is misbehaving during bring-up or field debugging, because every event looks the same at the pin.

That said, I wouldn't reject it outright. If the timing analysis shows the polling latency is acceptable for all three sources, and the firmware is structured to drain all sources reliably, sharing a line can be a legitimate pin-saving choice. The decision should be driven by the timing requirements, not by pin count alone. I'd ask the team to document the worst-case latency for each source under the shared-line scheme and compare it against the requirements, then decide.

**Possible follow-ups:**
- How would you structure the ISR to guarantee no event is lost when multiple peripherals share a line?
- If the timing analysis shows the shared line is too slow for the alarm input, what alternatives would you consider before adding pins?