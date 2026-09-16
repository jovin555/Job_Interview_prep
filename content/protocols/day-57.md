# protocols — Day 57

## Q1: How would you approach detecting and recovering from a UART break condition, and why does break detection matter in a medical device protocol?

**Answer:** A break condition is defined as the receive line being held in the dominant (spacing) state longer than a full character frame — typically longer than the start bit plus data bits plus parity plus stop bit. Most UART peripherals expose this as a status flag (often alongside framing and overrun errors), and some can generate an interrupt on break detection specifically. The first thing I'd do is distinguish a genuine break from a framing error: a framing error means the stop bit wasn't where it was expected, whereas a break means the line stayed low across the whole frame boundary. On the receive side, I'd configure the UART to flag break, clear the flag by reading the data register (or a dedicated status register, depending on the peripheral), and then decide what the break means at the protocol layer. In many simple protocols a break is used as an out-of-band signal — a wake-up, a resynchronization marker, or an explicit "link down" indication — so the firmware needs a defined state machine transition rather than just discarding the byte.

Recovery matters because a break can leave the receiver mid-frame with a partially assembled message. I'd flush the receive FIFO, reset the protocol parser to its idle state, and re-arm the receiver. If the link uses a framing protocol with a header and length field, the parser should be able to resynchronize on the next valid header rather than assuming byte alignment is preserved. On the transmit side, if the device can also generate a break, I'd make sure the driver only does so deliberately and with a bounded duration, since an accidental long break on a shared or half-duplex link can be interpreted by the peer as a fault.

In a medical device context, break detection is useful as a positive indication that the physical link has gone idle or been disconnected, which is safer than silently waiting for a timeout. I'd want the higher-level state machine to treat a break as a link event — log it, transition to a safe state if the link is safety-relevant, and attempt recovery — rather than as ordinary data loss. The key design principle is that the receiver should never be left in an ambiguous state after a break; it should always return to a known idle state and be ready to resynchronize.

**Possible follow-ups:**
- How would you distinguish a break condition from a genuine line disconnect or a stuck-low driver on the peer?
- If your protocol uses break as a wake-up signal, how would you prevent a noise-induced glitch from being misinterpreted as a break?

## Q2: You're debugging a CAN-FD network where a node intermittently transitions into error-passive state and then recovers on its own, with no obvious pattern. How would you approach this?

**Answer:** Error-passive means the node's transmit error counter or receive error counter has crossed the threshold (typically 128), so it can still participate but must be more conservative — it can no longer send active error frames. The fact that it recovers on its own suggests the counter is oscillating around the threshold rather than the node being permanently broken, which points to an intermittent physical or timing issue rather than a hard fault.

I'd start by capturing the error counters over time along with the error types being reported — bit errors, stuff errors, CRC errors, form errors, ACK errors. The distribution of error types narrows the cause considerably. A cluster of ACK errors suggests the node isn't being heard or isn't hearing others, which points to termination, stub length, or a marginal transceiver. Bit errors and stuff errors during the data phase, especially at the higher CAN-FD data rate, often point to signal integrity: reflections from improper termination, excessive stub length, or a bit-rate/sample-point mismatch between nodes. Form errors can indicate a node with a different configuration (wrong DLC handling or a non-conforming controller).

I'd also check whether the errors correlate with bus load or with a particular message. If the node only goes error-passive when a specific high-priority message is being transmitted, that could indicate a node with a mismatched bit-timing configuration that only manifests when the bus is busy. I'd verify the sample point and bit timing on every node — CAN-FD is much less forgiving of sample-point mismatch than classical CAN, especially in the data phase where the bit rate is higher and the propagation delay budget is tighter.

On the physical side, I'd measure with a scope or a CAN analyzer at the node's pins: check for ringing, check the differential voltage levels, check that termination is correct at both ends and only at the ends, and check stub lengths. I'd also verify the transceiver's common-mode range and that the ground reference between nodes is adequate — a ground offset can push the differential signal out of the receiver's valid window intermittently.

The recovery behavior itself is informative: the CAN error counter decrements on successful transmissions and receptions, so a node that recovers is one that's still successfully communicating most of the time. That argues against a dead transceiver and toward a marginal condition. I'd instrument the firmware to log the error counters and the last error type before each transition, then correlate with bus traffic and environmental conditions. The goal is to find the trigger, not just to reset the node.

**Possible follow-ups:**
- How would you determine whether the problem is on this node or on a peer that's corrupting the bus?
- What would you check first if the error-passive transitions only happen at the higher CAN-FD data-phase bit rate?

## Q3: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol does not have a built-in backpressure mechanism?

**Answer:** The first question is whether the hardware supports flow control at all. If RTS/CTS lines are available and wired, that's the cleanest solution — the receiver deasserts RTS when its buffer is near full, and the transmitter's UART hardware pauses automatically without any protocol change. That's the option I'd reach for first because it's handled below the application layer and doesn't require modifying the message format.

If hardware flow control isn't available, I'd look at the protocol layer. Even without a formal backpressure mechanism, most protocols have some slack I can exploit. If the receiver can't keep up, the options are to slow the transmitter, buffer more on the receiver, or drop and retry. Slowing the transmitter can be done with an in-band signal if the protocol has any spare message type or a reserved control byte — for example, a "pause" or "credit" message that the receiver sends when its buffer crosses a high-water mark. If the protocol is strictly one-directional or has no control channel, I'd consider adding a small out-of-band signal on a GPIO if a spare pin exists, which is essentially a software-defined RTS.

If none of that is possible, the fallback is receiver-side buffering plus a defined overflow policy. I'd size the buffer to absorb the worst-case burst, and when it does overflow, the receiver must have a deterministic behavior — either drop the oldest data, drop the newest, or reset the parser and resynchronize. The choice depends on what the data is: for a stream of sensor samples, dropping the oldest and keeping the most recent is often preferable; for a command stream, dropping anything is dangerous, so the receiver should signal an error and the transmitter should retransmit.

The deeper point is that "the protocol has no backpressure" is usually a design gap, not an immutable constraint. If the link is safety-relevant, I'd argue for adding an explicit flow-control mechanism — even a simple sequence number and ACK — because relying on the receiver always keeping up is fragile. I'd also instrument the receiver to count overruns so the problem is visible rather than silent.

**Possible follow-ups:**
- How would you size the receiver buffer if you can't add flow control and the transmitter's burst pattern is unpredictable?
- What's the risk of using a GPIO as a software RTS line, and how would you make it robust against the transmitter missing the signal?

## Q4: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging the legitimate motivation — pin count matters, especially on a small package — and then walk through what the shared line actually costs in terms of latency, determinism, and failure modes. The core issue is that a shared interrupt line turns a hardware event into a software search problem: when the ISR fires, the firmware has to poll each peripheral's status register to find out which one asserted. That's fine if the peripherals are slow and the polling is bounded, but it's a problem if any of them is latency-sensitive.

The GPIO alarm input is the one I'd focus on first. An alarm is typically the highest-priority event in a medical device, and if it shares a line with a UART that's receiving a burst of data, the alarm's latency is now coupled to how long the UART polling takes. That's a determinism problem, not just a performance problem. I'd ask the team to quantify the worst-case time from the alarm asserting to the firmware recognizing it, and compare that to the system's safety requirements.

The second issue is that polling status registers to disambiguate can have side effects. Reading a UART status register often clears flags; reading an SPI status register may acknowledge an interrupt. If the firmware polls in the wrong order, or if two peripherals assert simultaneously, it can miss an event or clear a flag it didn't mean to. That's a correctness risk that's easy to overlook in a design review.

The third issue is diagnosability. With separate interrupt lines, the ISR tells you immediately which peripheral fired. With a shared line, a stuck-low peripheral can mask all the others, and the firmware has no way to tell which one is at fault. In a medical device, that's a real maintainability and safety concern.

I'd guide the team toward a decision by asking: what's the actual pin budget, and is there a middle ground? Options include giving the alarm its own interrupt (it's the one that matters most), sharing the line between the UART and SPI if their latency requirements are compatible, or using a small I/O expander or interrupt controller that provides per-source status. The point of the review isn't to reject the idea outright — it's to make the trade-off explicit and ensure the team has thought about the worst case, not just the typical case.

**Possible follow-ups:**
- How would you structure the ISR if the team does decide to share the line, to keep the worst-case latency bounded?
- What would you want to see in the firmware design to prove that simultaneous interrupts from two peripherals can't cause a missed event?

## Q5: How would you approach choosing between a star topology and a daisy-chain topology for a multi-drop sensor network in a medical device, given that the sensors are physically distributed?

**Answer:** The choice is really driven by four things: the electrical characteristics of the physical layer, the cable routing constraints in the device, the failure behavior you can tolerate, and the protocol's addressing model. I'd work through them in that order.

On the electrical side, the physical layer constrains the topology more than people expect. RS-485 and CAN are designed for a linear bus with termination at both ends and short stubs — a star topology with long branches creates impedance discontinuities and reflections that degrade signal integrity, especially at higher bit rates. So if the physical layer is RS-485 or CAN, a true star is usually a bad idea unless the branches are very short or you use a repeater/hub. I2C is the opposite: it's a bus, but its capacitance limit means a star with long branches adds capacitance and can push you over the limit. So the first question is: what does the chosen physical layer actually support?

On the routing side, the physical layout of the device often decides the question before the electrical analysis does. If the sensors are distributed around a patient monitoring system with a central controller, a daisy-chain may require running cable out to each sensor and back, which can be longer and more awkward than a star. But if the sensors are along a single cable run, a daisy-chain is natural. I'd want to see the actual cable routing before committing.

On failure behavior, the topologies differ in an important way. In a daisy-chain, a break in the cable or a failed node can take down everything downstream of it. In a star, a failure in one branch is isolated to that branch. For a medical device, that's a significant difference — if one sensor failing can disable the others, that's a safety consideration. I'd want to know whether the system needs to keep operating with a degraded set of sensors, and whether the protocol has a way to detect and isolate a failed node.

On the protocol side, the addressing model matters. A daisy-chain with a store-and-forward protocol (each node repeats to the next) can extend reach but adds latency per hop and makes the failure behavior worse. A star with a central controller polling each branch independently gives more deterministic latency and simpler fault isolation, at the cost of more cable and more controller ports.

My approach would be to make the trade-off explicit: state the physical layer's constraints, the routing constraints, the failure requirements, and the latency requirements, and then pick the topology that satisfies all of them — or, if none does, propose a hybrid (for example, a star of short RS-485 segments, each terminated, with a repeater at the center). The key is not to pick a topology by habit but to derive it from the requirements.

**Possible follow-ups:**
- If the physical layer is RS-485 and the routing forces a star, what techniques would you use to keep the signal integrity acceptable?
- How would you design the protocol's fault detection so that a failed node in a daisy-chain doesn't silently take down the nodes behind it?