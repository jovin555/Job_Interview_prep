# protocols — Day 82

## Q1: How would you approach debugging a CAN-FD network where a node occasionally goes bus-off and stays off until the controller is reset, even though the bus itself appears healthy afterward?

**Answer:** Bus-off is the terminal state of the CAN error-confinement mechanism, so the first thing to establish is *why* the transmit error counter (TEC) climbed past 255 in the first place — the bus-off itself is a symptom, not the root cause. I'd approach it in layers:

1. **Read the controller's error counters and error code capture registers** before the reset clears them. Most CAN-FD controllers expose TEC/REC, the last error type (bit error, stuff error, CRC error, ACK error, form error), and sometimes the bit position where the error occurred. That single piece of data usually splits the problem in half: an ACK error points at "nobody acknowledged me" (wiring, termination, wrong bit rate, node not present), while a bit or stuff error points at signal integrity or a bit-rate mismatch in the data phase.
2. **Check for a data-phase vs arbitration-phase bit-rate mismatch.** CAN-FD has two bit rates (nominal/arbitration and data). A node configured with the wrong data-phase prescaler or sample point will often pass arbitration and then fail in the data phase, which can look intermittent because it only manifests on longer payloads. This is a very common cause of "works most of the time" behavior.
3. **Look at the physical layer under load.** Bus-off that only appears under heavy traffic often traces to reflections from excessive stub length, missing or doubled termination, or a common-mode shift when many nodes transmit. A scope capture at the worst-case node, triggered on the error frame, is worth more than hours of log reading.
4. **Check whether the node is being reset by something else.** If the controller is going bus-off and the firmware's recovery path is a full reset, confirm the recovery is actually automatic-recovery-on-bus-off vs manual. Many controllers default to requiring a software re-init; if the firmware never re-inits, the node stays silent forever. That's a firmware bug masquerading as a hardware fault.
5. **Reproduce deterministically.** If it's load-dependent, drive the bus with a traffic generator to a known utilization and see whether the failure correlates with a specific message or node.

The fix is usually one of: correct the bit timing, fix termination/stubs, or implement a proper bus-off recovery state machine with a backoff so a flapping node doesn't immediately re-offend.

**Possible follow-ups:**
- How would you distinguish a bus-off caused by a single dominant-stuck node from one caused by a marginal physical layer?
- What recovery policy would you implement so a node that keeps going bus-off doesn't degrade the whole network?

## Q2: You're designing a half-duplex RS-485 link where the driver-enable and receiver-enable must switch at exactly the right moment, and the turnaround budget is tight. How would you approach this?

**Answer:** Half-duplex RS-485 turnaround is fundamentally a timing and state-machine problem, and the failure modes are almost always "talked too early" or "listened too late." I'd structure it as follows:

- **Define the turnaround budget explicitly.** The budget is: last bit out of the driver → driver disabled → line settles → receiver enabled → first start bit detected. Each of those has a real number attached (driver disable time from the transceiver datasheet, line settling dominated by the RC of the bus and termination, receiver enable time). If the sum exceeds the gap the protocol allows, the protocol or the transceiver choice is wrong, not the firmware.
- **Never disable the driver in the middle of a byte.** The classic bug is disabling DE from a timer that fires slightly before the UART's transmit-complete flag. I'd gate DE de-assertion on the UART's "transmission complete" (TC/TXE) interrupt, not on "transmit buffer empty," because the shift register may still be clocking out the last byte.
- **Keep the receiver enabled during transmit where the hardware allows.** Many transceivers let you keep RE asserted while DE is asserted; the driver simply overpowers the receiver. This removes the "listen too late" half of the problem entirely and lets you detect collisions or a stuck peer. If the transceiver can't do that, you need a deliberate enable delay after DE drops.
- **Add a guard time and make it configurable.** A small inter-frame gap (a few bit times, tunable) absorbs transceiver and cable variation and gives the far end time to turn around. It costs throughput but buys determinism.
- **Handle the failure case.** If the master transmits and gets no reply within a timeout, it must return to receive mode and retry or flag the node — never stay stuck driving the bus.

For a tight budget, I'd also consider a transceiver with fast enable/disable times and, if the MCU supports it, hardware-assisted DE control (some UARTs drive DE automatically on the last stop bit), which removes firmware jitter from the critical path.

**Possible follow-ups:**
- How would you measure the actual turnaround time on the bench to validate your budget?
- What happens to your scheme if a node's firmware crashes while it holds DE asserted?

## Q3: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol has no built-in backpressure mechanism?

**Answer:** When the protocol itself has no backpressure, you have to add flow control at a layer the protocol doesn't know about, and you have to decide whether you're allowed to change the wire protocol at all. I'd work through the options in order of intrusiveness:

1. **Hardware flow control (RTS/CTS) if the lines exist.** This is the cleanest: the receiver de-asserts RTS/CTS when its buffer crosses a high-water mark and re-asserts at a low-water mark. The key design points are hysteresis (don't toggle at a single threshold or you'll chatter), and making sure the transmitter actually respects CTS mid-stream rather than only at frame boundaries. If the hardware lines aren't wired, this is off the table without a board change.
2. **Software flow control (XON/XOFF) if the payload is text-safe.** This works only if the data stream can never contain the XON/XOFF byte values, or if you escape them. In a binary medical protocol that's usually not acceptable, so I'd be cautious.
3. **Application-level pacing without changing the protocol semantics.** If you can't add control bytes, you can still shape traffic: the transmitter sends at a rate the receiver is known to sustain, or sends in bursts with a fixed inter-burst gap derived from the receiver's worst-case processing time. This is really open-loop flow control — it trades throughput for determinism and requires you to characterize the receiver's worst case, not its average.
4. **Increase buffering and use DMA.** Often the "receiver can't keep up" is really "the receiver's interrupt latency is too high." Moving to DMA with a ring buffer and processing in a lower-priority task can absorb bursts without any protocol change. This is frequently the right first fix because it's a firmware change only.
5. **Drop-and-retry at a higher layer.** If the protocol has any sequence numbers or CRCs, you can let the receiver drop frames it can't handle and rely on the upper layer to detect the gap and request retransmission. This is only acceptable if the upper layer genuinely tolerates it and the timing requirements allow the retry.

The decision hinges on: can I change the wire format, and what's the worst-case latency the application tolerates? For a medical device I'd lean toward hardware flow control or DMA buffering, because both are deterministic and don't rely on the peer cooperating at the application layer.

**Possible follow-ups:**
- How would you size the high- and low-water marks for RTS/CTS given a known worst-case processing time?
- If you can't change the hardware, how would you prove the open-loop pacing is safe under worst-case load?

## Q4: How would you approach selecting between RS-422 and RS-485 for a medical device that needs to connect a central controller to several distributed sensor modules?

**Answer:** The core difference is that RS-422 is a point-to-point (or one-driver-to-many-receivers) balanced interface, while RS-485 is a true multipoint bus that supports multiple drivers sharing one pair. So the selection question is really: does more than one node ever need to transmit?

- **If only the central controller ever transmits** and the sensors only listen or reply on a separate dedicated pair, RS-422 can be sufficient and is simpler — no driver-enable arbitration, no bus contention, and the electrical margins are a bit more forgiving because you're not sharing the medium.
- **If any sensor needs to transmit back on the same pair** — which is almost always the case for a sensor network — you need RS-485's multipoint capability, with driver-enable control and a protocol that arbitrates who talks when. RS-422 cannot do this safely; two drivers on the same pair will fight.
- **Topology and node count.** RS-485 is specified for up to 32 unit loads (more with fractional-load transceivers) on a shared bus, which fits a distributed sensor network. RS-422 is typically one driver to up to ten receivers, so it doesn't scale to a multi-drop sensor topology.
- **Cable length and data rate.** Both share the same underlying balanced-signaling physics, so the length-vs-bit-rate trade-off is similar. The choice isn't usually driven by distance; it's driven by whether the medium is shared.
- **Medical-specific considerations.** For a patient monitoring system, the multipoint RS-485 bus means a single fault (a node stuck driving) can take down the whole network, so you need fail-safe biasing and a stuck-driver recovery strategy. RS-422's point-to-point nature isolates faults better but doesn't support the topology you likely need. Galvanic isolation requirements and leakage current limits apply to both and may push you toward isolated transceivers regardless.

In practice, for a central controller talking to several distributed sensor modules where the sensors must respond, RS-485 is the default answer, and the real design work goes into termination, biasing, and the arbitration protocol rather than the RS-422-vs-485 choice itself.

**Possible follow-ups:**
- How would the answer change if the sensors only ever needed to be polled and never initiated communication?
- What isolation and leakage-current constraints would you check before finalizing the transceiver choice?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd treat this as a legitimate trade-off to be evaluated rather than a mistake to be corrected, because pin-count pressure is real and the proposal isn't automatically wrong — it's wrong *for some use cases*. I'd guide the review through a few concrete questions:

1. **What's the worst-case latency each peripheral can tolerate?** The GPIO alarm input is the tell. If it's a patient alarm or a safety-relevant signal, the time to service it is bounded by how long it takes to poll all three peripherals in the shared ISR, plus the latency of the slowest one. If the SPI sensor's transaction takes milliseconds, the alarm could be delayed by that much every time the SPI fires. That may be unacceptable, and it's the kind of thing that's easy to miss until it's a field problem.
2. **Can the firmware reliably tell who fired?** Polling works only if each peripheral's status flag is unambiguous and the act of reading it doesn't clear another peripheral's flag or have side effects. SPI status registers, in particular, often require a read that itself takes time and can interact with an in-progress transfer. If two peripherals fire nearly simultaneously, the shared ISR must handle both without losing either.
3. **What's the cost of the alternative?** If the MCU genuinely has no spare interrupt-capable pins, the options are: a shared line with a fast, well-defined polling order; an I/O expander or interrupt aggregator that gives you per-source status; or moving a peripheral to DMA/polling so it doesn't need an interrupt at all. Each has a cost, and the review should compare them honestly.
4. **What does the failure mode look like?** With a shared line, a stuck-asserted peripheral can mask the others. That's a reliability concern for a medical device, and it should be weighed against the pin savings.

My guidance to the team would be: if all three sources are non-safety, low-rate, and have unambiguous status flags, a shared line with a documented polling order can be acceptable and should be captured in the design record. If any source is safety-relevant or has a tight latency bound, it needs its own interrupt or a hardware aggregator that preserves per-source identity. The decision should be written down with the reasoning, not left implicit.

**Possible follow-ups:**
- How would you structure the shared ISR so that a slow peripheral can't starve a fast one?
- What would you document in the design record to justify the shared-line decision if it's accepted?