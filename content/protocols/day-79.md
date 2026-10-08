# protocols — Day 79

## Q1: How would you approach debugging a CAN-FD network where a node occasionally goes bus-off and stays off until the controller is reset, even though the bus itself appears healthy afterward?

**Answer:** Bus-off is the terminal state of the controller's transmit error counter (TEC) exceeding 255, so the first question is *why the TEC climbed*, not why the node stayed off. A healthy-looking bus afterward is expected — once the node is bus-off it stops transmitting, so the disturbance it was causing (or reacting to) disappears from the scope.

I'd work through the error counter mechanics systematically:

1. **Capture the transition, not the aftermath.** Trigger a logic analyzer or CAN analyzer on the error frame burst just before bus-off. The error frames themselves tell you whether the node was the *aggressor* (its own transmissions were being corrupted → ACK errors, form errors, bit errors it detected) or the *victim* (it was correctly receiving but losing arbitration repeatedly, or seeing errors from others).

2. **Distinguish the error types.** A rising TEC with mostly *acknowledge errors* points to a wiring/termination problem — the node transmits but nobody acknowledges, which happens with a broken stub, a missing termination, or a transceiver in the wrong mode. A rising TEC with *bit errors* points to signal integrity: reflections, ground offset, or a data-phase bit rate the physical layer can't actually support over that bus length. A rising TEC with *stuff errors* or *form errors* often points to a bit-timing mismatch — sample point or SJW configured differently on one node than the rest, which only bites at certain bit patterns.

3. **Check the data-phase bit rate against bus length.** CAN-FD's arbitration phase and data phase run at different rates, and the data phase is where the physical layer gets stressed. A bus that's fine at 500 kbit/s arbitration can fail at 2 or 5 Mbit/s data phase if the stub lengths, termination, or transceiver loop delay aren't up to it. This is a very common cause of exactly the symptom described — intermittent, load-dependent, and self-clearing once the offending node drops off.

4. **Look at the recovery configuration.** Whether the node auto-recovers from bus-off or requires a reset is a software choice (the controller's automatic bus-off recovery bit, or the application's own recovery state machine). If the design *intends* automatic recovery but the node stays off, that's a separate firmware bug layered on top of the electrical root cause — worth fixing regardless, because a medical device node that silently stays off the bus is a safety concern.

5. **Reproduce under controlled load.** Bus-off that only appears "occasionally" usually correlates with bus load, temperature, or a specific message pattern. I'd drive the bus to high load deliberately and watch the error counters, then vary one physical parameter at a time.

The key discipline is separating the *electrical/configuration root cause* (why errors accumulated) from the *recovery policy* (why it didn't come back). Both need fixing, but conflating them wastes time.

**Possible follow-ups:**
- How would you decide whether the node should auto-recover from bus-off or require an explicit application-level recovery, in a safety-critical context?
- If the error counters show mostly acknowledge errors, what physical-layer checks would you run first?

## Q2: You're designing a half-duplex RS-485 link where the driver-enable and receiver-enable must switch at exactly the right moment, and the turnaround budget is tight. How would you approach this?

**Answer:** Half-duplex RS-485 turnaround is fundamentally a timing-budget problem, and the failure modes are asymmetric: switch too early and you truncate your own last byte; switch too late and you either miss the start of the reply or, worse, briefly drive the bus while the other node is also driving, causing contention.

I'd approach it in layers:

**Hardware layer.** The transceiver's driver-enable and receiver-enable propagation delays, plus the driver's output enable/disable times, set a hard floor on how fast you can turn around. Some transceivers have asymmetric enable/disable times — the driver may take longer to *release* the bus than to *assert* it. I'd pick a transceiver whose datasheet numbers fit the budget with margin, and I'd check whether the receiver can be left permanently enabled (many designs tie RE low) so you only have to toggle DE. That removes one timing variable entirely.

**Firmware layer — the transmit side.** The critical rule is: don't de-assert DE until the last bit has *actually left the shift register*, not when the transmit buffer is empty. On most MCUs the "transmit complete" flag (TC) is the correct one to wait on, not "transmit data register empty" (TXE). Waiting on TXE is a classic bug that truncates the final byte. I'd also account for the transceiver's driver-disable delay after TC.

**Firmware layer — the receive side.** After releasing the bus, there's a window where the line is floating or settling before the remote node starts driving. If the receiver was disabled, re-enable it *before* you expect the first start bit, and ideally leave it enabled throughout. If the protocol has a defined inter-frame gap, use it as the turnaround window.

**Budgeting.** I'd write the turnaround budget down explicitly: last-bit-out time + driver-disable delay + line settling + remote node's own turnaround + first-bit-in margin. If the sum exceeds the protocol's allowed gap, the fix is usually to relax the protocol (larger gap), lower the baud rate, or use a transceiver with faster enable/disable — not to shave margins in firmware.

**Verification.** This is exactly the kind of thing that works on the bench and fails in the field, so I'd verify with a scope on the DE line and the A/B differential pair simultaneously, across temperature, and with the actual cable length and node count. A logic-analyzer view of the UART alone won't show you bus contention.

**Possible follow-ups:**
- How would you handle the case where the remote node's response time is variable, so the turnaround window isn't fixed?
- What would you check if you saw occasional corruption only on the *first* byte of a reply?

## Q3: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol has no built-in backpressure mechanism?

**Answer:** When the protocol has no backpressure, you have three broad options, and the right one depends on whether you can change the protocol, the hardware, or neither.

**Option 1 — Add hardware flow control (RTS/CTS).** If the UART peripherals and the connector have spare pins, this is the cleanest fix: the receiver de-asserts RTS (or CTS, depending on direction) when its buffer crosses a high-water mark, and the transmitter's UART hardware automatically pauses mid-stream. The advantage is that it's handled in hardware, so it works even if the transmitter's firmware is busy. The caveats: it requires the physical pins, both ends must agree on polarity and which signal gates which direction, and it only helps if the receiver's *hardware* FIFO is the bottleneck — if the receiver's *software* isn't draining the FIFO fast enough, CTS will assert but the data already in flight still overruns.

**Option 2 — Add software flow control (XON/XOFF).** If you can't add wires but can define in-band control characters, the receiver sends XOFF when its buffer is nearly full and XON when it drains. This works over a plain 3-wire link, but it has real hazards: the control characters must be escaped if they can appear in payload data, the transmitter must be able to stop *quickly* (within the receiver's remaining buffer), and there's an inherent round-trip latency — by the time XOFF arrives, the receiver has already accepted more bytes. So the high-water mark must be set with that latency in mind.

**Option 3 — Fix it at the protocol/application layer.** If neither of the above is possible, the answer is usually to restructure the exchange: make the transmitter send in bounded chunks and wait for an application-level acknowledgment before sending the next chunk. This is really "add backpressure at the application layer" — it's slower but it's the only option when you control neither the hardware nor the byte stream.

**Regardless of option, I'd also look at *why* the receiver can't keep up.** Sometimes the real fix is to increase the receiver's buffer, raise its task priority, use DMA to drain the UART FIFO without CPU involvement, or reduce the baud rate. Flow control is a band-aid over a throughput mismatch; if the mismatch is fundamental, flow control just moves the problem to "the link is slower than we need."

**Possible follow-ups:**
- How would you size the high-water mark for XON/XOFF given a known round-trip latency and buffer size?
- If the receiver's bottleneck is a slow application task rather than the UART itself, how would DMA help or not help?

## Q4: How would you approach selecting between RS-422 and RS-485 for a medical device that needs to connect a central controller to several distributed sensor modules?

**Answer:** The decision usually comes down to one question: does the central controller need to *receive* from multiple nodes on the same pair, or does it only need to *transmit* to them (or communicate point-to-point with each)?

**RS-422** is a four-wire, full-duplex, single-driver/multi-receiver standard. One driver, up to ten receivers on the same bus. It's the right choice when the topology is genuinely one-to-many *broadcast* — the controller talks, all sensors listen — or when you have a dedicated pair per direction and only one node ever drives each pair. It's simpler to reason about because there's no bus contention: only one driver exists on each pair, so you never have to arbitrate or turn a driver around.

**RS-485** is a two-wire (or four-wire), half- or full-duplex, multi-driver/multi-receiver standard. Multiple nodes can drive the same pair, which means you need a protocol for *who talks when* — either a master-slave polling scheme or a token/turnaround scheme. The payoff is that every node can both transmit and receive on the same pair, so a sensor can send data back to the controller without a second pair of wires.

For a medical device with a central controller and several distributed sensor modules, the practical considerations are:

- **If the sensors only ever respond to polls** and the controller is the only node that initiates, RS-485 half-duplex with a master-slave protocol is usually the most economical — two wires, one termination network, and the polling discipline gives you deterministic access.
- **If the sensors need to send unsolicited data** (alarms, events) or the traffic is genuinely bidirectional and continuous, RS-485 still works but the protocol has to handle contention; RS-422 with separate pairs avoids that but costs more cable and connector pins.
- **Cable and connector budget** matters in a medical device — more pairs means thicker cable, larger connectors, and more opportunities for a wiring error in the field.
- **Common-mode range and grounding** are similar between the two standards, but the multi-driver case in RS-485 makes ground-offset and fail-safe biasing more critical, because a node that's supposed to be silent must actually release the bus cleanly.
- **Fail-safe behavior** is a design consideration in both, but in RS-485 you also have to guarantee that no two nodes drive simultaneously — which is a protocol and firmware concern, not just an electrical one.

My default for a polled sensor network is RS-485 half-duplex, because it minimizes wiring and the master-slave discipline gives determinism. I'd only move to RS-422 if the topology were truly one-directional or if the bidirectional traffic were heavy enough that turnaround overhead dominated.

**Possible follow-ups:**
- How would the termination strategy differ between an RS-422 point-to-point link and an RS-485 multi-drop bus?
- If a sensor needed to raise an alarm without waiting to be polled, how would that change your choice?

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** The first priority is containment and honesty, not blame. A protocol defect found during compliance testing is a *finding*, and the worst thing a team can do is try to argue it away or patch it quietly — in a regulated environment, the integrity of the process is itself part of the product.

I'd structure my response in phases:

**1. Stabilize and understand the finding.** Before anything else, get a precise, written description of what failed, under what conditions, and what the test was actually checking. "The protocol is wrong" is not actionable; "the device NACKs under condition X, which the test interprets as a failure to meet requirement Y" is. I'd sit with the test engineer and the junior engineer together to reproduce it deterministically.

**2. Separate the defect from the process failure.** There are usually two things to fix: the technical defect, and the reason it wasn't caught earlier. The junior engineer may have made a genuine mistake, but if the defect reached compliance testing, the review and verification process also had a gap. I'd want to understand both without turning it into a personal issue — the goal is that the *team* learns, not that one person is punished.

**3. Assess the impact on the submission.** A protocol defect found during compliance testing may or may not invalidate other test results, depending on whether the affected interface was exercised in those tests. I'd work with the regulatory lead to determine what needs to be re-tested and whether the finding needs to be documented as a nonconformance with a corrective action. This is a regulatory decision, not an engineering one, and it should be made explicitly.

**4. Fix forward with a proper change process.** The fix goes through the same change-control and verification path as any other design change — updated requirements, updated test cases, regression testing. If the fix is rushed and undocumented, you've traded one compliance problem for another.

**5. Address the human side directly.** The junior engineer is likely to feel responsible and may be defensive or withdrawn. I'd have a private conversation that separates the technical mistake from their value to the team, and I'd be explicit that the review process exists precisely so that individual mistakes don't reach this stage — which means the process, not just the person, needs attention. I'd also make sure they're involved in the fix, so the learning is real rather than punitive.

**6. Fix the process.** Depending on the root cause, the corrective action might be: adding protocol-level test cases to the verification plan, requiring a second reviewer for interface code, adding a protocol conformance test earlier in the development cycle, or improving the requirements so the protocol behavior is unambiguous. The point is to make the *next* defect of this class get caught before compliance testing.

**7. Communicate upward honestly.** Schedule impact is real, and the sooner leadership knows the scope, the more options they have. I'd rather deliver bad news early with a plan than deliver it late with an excuse.

The through-line is: contain, understand, fix properly, learn, and protect the team's ability to surface problems early. A culture where a junior engineer is afraid to report a defect is a much bigger compliance risk than the defect itself.

**Possible follow-ups:**
- How would you decide whether the corrective action should be a process change, a design change, or both?
- If the junior engineer pushed back and argued the test was wrong, how would you handle that?