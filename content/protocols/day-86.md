# protocols — Day 86

## Q1: How would you approach designing a protocol abstraction layer so that application code can talk to sensors over I2C, SPI, UART, or CAN-FD without knowing which transport is underneath?

**Answer:** The core idea is to define a transport-agnostic interface at the boundary the application actually cares about — typically a small set of operations like `read(handle, buffer, len)`, `write(handle, buffer, len)`, and maybe `ioctl`-style configuration — and then implement one backend per physical transport behind that interface. The application links against the abstract interface only; the concrete backend is selected at compile time (static binding, good for constrained MCUs) or at init time via a registration table (function-pointer vtable per transport).

Key design decisions:

- **Keep the abstraction at the right level.** If you abstract too low (raw byte streams), every caller re-implements framing and retry logic. If you abstract too high (e.g., "read temperature"), you lose the ability to exploit transport-specific features. A good middle ground is a *message-oriented* interface: the transport layer handles framing, addressing, and error signalling, while the application handles semantics.
- **Model errors uniformly.** I2C has NACKs, SPI has no acknowledgement at all, UART has framing/parity errors, CAN-FD has error frames and bus-off states. The abstraction should map these into a common error enum (timeout, bus error, device not responding, CRC failure) so the application doesn't need transport-specific error handling.
- **Don't hide timing characteristics that matter.** A blocking `read()` on I2C at 100 kHz and on CAN-FD have very different latency profiles. The interface should expose whether an operation is synchronous or asynchronous, or at least document worst-case timing, so real-time callers can reason about it.
- **Configuration stays per-transport.** Bus speed, CPOL/CPHA, device address, etc. belong in the backend's init, not in the generic interface.

The payoff is testability: you can implement a mock backend that injects faults (timeouts, corrupted bytes) and run the entire application stack against it without hardware.

**Possible follow-ups:**
- How would you handle a transport that supports multi-drop (I2C, RS-485) versus point-to-point (SPI) in the same abstraction?
- Where would you put retry logic — in the abstraction layer or in each backend?

---

## Q2: You're debugging a CAN-FD network where a node occasionally goes bus-off and stays off until the controller is reset, even though the bus itself appears healthy afterward. How would you approach this?

**Answer:** Bus-off means the controller's transmit error counter (TEC) exceeded 255, so the first question is *why the TEC climbed that high* — a single transient glitch usually won't do it. I'd work through it in layers:

1. **Confirm it's really transmit-side.** Read the error counters and the last error code register before the reset. If TEC is what's saturating (not REC), the node is failing to get its own frames acknowledged or is losing arbitration repeatedly in a way that generates errors.
2. **Check for a missing or late ACK.** A node that transmits into a bus where no other node is listening (e.g., the only other active node is in a reset or sleep state) will retransmit and increment TEC on every failed attempt. If the "healthy bus" is actually idle because peers dropped off, that alone explains bus-off.
3. **Look at bit timing and sample point.** If the node's nominal bit rate or sample point is slightly off from the rest of the network — different oscillator, wrong prescaler, wrong SJW — it will produce form/stuff errors under certain bit patterns. This often shows up intermittently because it depends on the data content.
4. **Check termination and stub length.** A reflection that only corrupts certain bit sequences can cause sporadic errors that accumulate.
5. **Examine the recovery policy.** Many controllers require software to explicitly clear the bus-off state (or wait for the 128×11 recessive-bit recovery sequence). If the firmware never re-initialises after bus-off, the node stays silent forever — which matches "stays off until reset."

The fix is usually two-part: find the physical or timing root cause of the error accumulation, *and* implement a proper bus-off recovery handler (with a back-off and a health check) so a single fault doesn't permanently remove a node from a medical network.

**Possible follow-ups:**
- How would you distinguish a node-local timing problem from a network-wide disturbance?
- What recovery policy would you consider safe in a medical device — automatic re-init, or require a supervised restart?

---

## Q3: How would you approach detecting and recovering from a UART break condition, and why does break detection matter in a medical device protocol?

**Answer:** A break condition is when the receive line is held in the space (dominant) state longer than a full character frame — typically longer than start bit + data + parity + stop. Most UART peripherals flag this in a status register (often alongside framing and overrun errors), and some can generate an interrupt on break detect.

Detection approach:
- Enable break-detect interrupt (or poll the status flag) and treat it as a distinct event from a normal framing error, because the recovery is different.
- On break, flush the RX FIFO and reset the receive state machine in firmware. A break often means the peer reset, lost power, or the line was disconnected — any partial frame in the buffer is garbage.
- Optionally use break as a deliberate in-band signal: some protocols use a break as a frame delimiter or a "resync" marker, so the handler may need to distinguish "intentional break" from "fault break."

Why it matters in a medical device: a break is one of the few unambiguous signals that the link peer has gone away or the cable has been disturbed. If the firmware ignores it, the receiver can sit waiting for the rest of a frame that will never arrive, or worse, misinterpret the next bytes as continuation of a corrupted message. In a device where a sensor reading drives a clinical decision, silently accepting a truncated or misaligned frame is a safety issue. The correct behaviour is to detect the break, discard the partial frame, mark the link as degraded, and either re-synchronise on the next valid frame or raise a fault — never to keep parsing as if nothing happened.

**Possible follow-ups:**
- How would you distinguish a break caused by a peer reset from one caused by a cable fault?
- Would you use break as a deliberate protocol delimiter, and what are the risks of doing so?

---

## Q4: How would you approach debugging a UART link where the receiver reports framing errors only when a high-current load (e.g., a motor or heater) switches on the same board?

**Answer:** This is a classic noise-coupling symptom, and the fact that it correlates with a specific load event is the most useful clue. I'd approach it as a signal-integrity and grounding problem first, not a firmware problem.

1. **Scope the RX line at the receiver pin.** Trigger on the load switching (e.g., the gate drive or relay coil signal) and look at the UART line. Framing errors mean the start or stop bit was misread, so I'd look for a glitch, a ground bounce, or a slow edge right at a bit boundary.
2. **Check the ground reference.** A high-current load switching causes a transient in the ground plane. If the UART transmitter and receiver reference different ground points, the receiver sees the difference as a common-mode shift on the signal. This is the most common cause of "only when the motor turns on" framing errors.
3. **Look at the load's return path.** If the motor or heater current returns through a path that shares impedance with the UART ground or the MCU's ground, the switching transient appears directly on the logic reference. Fixes include separating the power and signal grounds, adding a star ground point, or using a differential link (RS-422/RS-485) if the distance and environment warrant it.
4. **Check decoupling and bulk capacitance** on the MCU supply — a supply dip during load switch-on can cause the UART peripheral's clock to glitch, which shows up as framing errors.
5. **Consider the load's switching speed.** A slow-switching relay or a PWM'd heater produces different noise spectra than a hard-switched motor. Snubbers, gate resistors, or a slower edge on the load driver can reduce the transient.

Only after the physical cause is understood would I consider firmware mitigation (e.g., oversampling, glitch filters), because masking a real electrical problem in a medical device is the wrong direction.

**Possible follow-ups:**
- How would you decide between fixing the grounding and switching to a differential physical layer?
- What would you check if the framing errors persisted even with the load disconnected but the driver still switching?

---

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd steer the discussion away from "is it possible" (it usually is) toward "what does it cost in latency, determinism, and failure modes," because those are the things that matter in a medical device.

Points I'd raise for the team to work through:

- **Latency budget.** A shared interrupt means the ISR must poll all three peripherals to find the source. That adds latency to every event, and the worst case is when the *last* peripheral polled is the one that fired. For a UART receiving a byte stream, that latency can cause an overrun; for an alarm input, it delays the response. The team should quantify the worst-case service time and compare it to each peripheral's deadline.
- **Priority inversion.** A UART RX interrupt and a safety alarm are not equal priority. Sharing a line forces them to the same priority, so a burst of UART traffic can delay alarm handling. In a medical device, that's usually unacceptable.
- **Spurious and missed interrupts.** If two peripherals fire close together, the shared ISR may see only one edge (depending on the interrupt controller's edge/level behaviour) and miss the other. The team should check whether the MCU's interrupt controller latches edges or requires level-sensitive handling, and whether the shared line can lose events.
- **Debuggability.** With separate lines, a scope or logic analyser shows exactly which peripheral fired. With a shared line, every debug session starts with "which one was it?" That cost compounds over the product's life.
- **Pin budget reality check.** If the MCU genuinely lacks pins, the right answer may be a pin-expander, an interrupt aggregator with a status register, or a different MCU — not a shared line that trades determinism for pin count.

If the team still wants to proceed, I'd ask for a written worst-case timing analysis and a fault-injection test plan showing that no event is lost under simultaneous arrivals. If that analysis can't be produced, the design isn't ready.

**Possible follow-ups:**
- If the MCU has an interrupt aggregator with a status register, how would that change your recommendation?
- How would you structure the test plan to prove no events are lost under simultaneous arrivals?