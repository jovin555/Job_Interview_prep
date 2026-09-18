# protocols — Day 59

## Q1: How would you approach debugging a CAN-FD network where a node intermittently enters error-passive state and recovers on its own, with no obvious pattern in when it happens?

**Answer:** Error-passive is a state the controller enters after its transmit or receive error counters exceed a threshold, so the first step is to treat it as a symptom rather than a root cause. I'd start by capturing the error counters (TEC/REC) and the error state transitions over time, ideally with a bus analyzer that timestamps error frames and correlates them with what else is happening on the bus. The key question is whether the node is *causing* errors or *observing* them — a node that sees errors from another transmitter will increment its REC, while a node with a marginal transmitter or bad wiring will increment its TEC.

From there I'd narrow the cause along a few axes: physical layer (termination, stub length, common-mode range, ground offset between nodes), bit-timing (sample point mismatch between nodes, especially in the arbitration phase vs the data phase where CAN-FD switches bit rate), and protocol-level (a node transmitting at the wrong DLC, or a transceiver with a slow loop delay that fails at the higher data-phase rate). Intermittency usually points to something environmental or marginal — temperature drift affecting an oscillator, a connector that's not fully seated, or a node whose sample point is just barely inside tolerance and only fails when another node's clock drifts the other way. I'd also check whether the failures cluster around specific traffic patterns, which would suggest a bus-load or arbitration-related cause rather than a purely physical one.

**Possible follow-ups:**
- How would you determine the correct sample point for each node, and what tool would you use to verify it?
- If the error counters show the node is mostly *receiving* errors rather than generating them, how does that change your investigation?

## Q2: You're designing a half-duplex RS-485 link where the driver-enable and receiver-enable must switch at exactly the right moment, and the turnaround budget is tight. How would you approach this?

**Answer:** Half-duplex RS-485 turnaround is fundamentally a timing problem, and the failure modes are well known: if you enable the driver too early you can clip the tail of the previous byte; if you disable it too late you hold the bus and block other nodes; if you enable the receiver too late you miss the first bit of the response. I'd approach it in layers.

At the hardware level, I'd pick a transceiver with a known and short enable/disable propagation delay, and I'd make sure the DE/RE pins are driven from a GPIO with predictable timing — not from a shared signal that has to propagate through logic. I'd also consider whether the UART's transmit-complete flag is a reliable trigger for de-asserting DE, since on many MCUs the "transmit complete" interrupt fires only after the shift register has fully emptied, which is exactly what you want.

At the firmware level, I'd structure the driver as a small state machine: idle (receiver enabled), transmit (driver enabled, receiver disabled), and a guard interval after the last byte before re-enabling the receiver. The guard interval has to account for the transceiver's disable time plus the line settling time, and it should be derived from the datasheet, not guessed. If the turnaround budget is genuinely tight, I'd measure it on a scope — DE, the differential pair, and the first bit of the response — rather than trusting the datasheet alone, because PCB parasitics and cable capacitance shift the real numbers.

**Possible follow-ups:**
- How would you handle the case where the master and a slave both try to drive the bus at the same time due to a firmware bug?
- What role does fail-safe biasing play in ensuring the receiver doesn't see spurious start bits during the idle period?

## Q3: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol does not have a built-in backpressure mechanism?

**Answer:** If the protocol has no backpressure, you have three broad options, and the right one depends on whether you can change the protocol, the hardware, or neither.

The cleanest fix, if the hardware supports it, is to add hardware flow control (RTS/CTS) — the receiver asserts CTS when its buffer is nearly full, and the transmitter respects it. That requires both ends to cooperate and the connector to carry the extra lines, which isn't always possible.

If you can't add lines, the next option is software flow control (XON/XOFF), but that only works if the payload is text-like or you can guarantee the control characters never appear in the data — which is rarely true for binary sensor data. A safer variant is to reserve a small control channel in the existing protocol: a single-byte "pause" and "resume" opcode, with the payload escaped or length-prefixed so the opcodes can't be confused with data.

If you can't change the protocol at all, the remaining option is to make the receiver fast enough that it never overflows — larger DMA buffers, interrupt-driven reception instead of polling, or a higher-priority task for the UART. That's a band-aid, but it's sometimes the only choice for a legacy interface. In all cases I'd add a receive-overflow counter and log it, because silent data loss on a medical link is worse than a visible error.

**Possible follow-ups:**
- How would you decide between a hardware and a software flow-control solution if the connector has spare pins but the protocol is fixed?
- What would you do if the receiver's buffer overflows despite flow control being asserted — how would you recover the link?

## Q4: In a system where an SPI master talks to several slaves at different clock speeds, how would you approach structuring the firmware so that mode and speed changes are handled safely?

**Answer:** The core risk is that SPI mode (CPOL/CPHA) and clock speed are properties of the *transaction*, not the bus, so any code path that changes them has to do so atomically with respect to other transactions. If two tasks share the bus and one changes the mode while the other is mid-transfer, you get corrupted data on both.

I'd structure this around a single bus-owner abstraction: one mutex or one dedicated SPI task owns the peripheral, and every transaction goes through it. Each slave gets a small descriptor — mode, max clock, chip-select GPIO, and any timing constraints (setup/hold, inter-byte delay) — and the bus owner reconfigures the peripheral from that descriptor before asserting chip select. That way the mode and speed are always set in the same place, and there's no path where a caller can forget to set them.

Two details matter in practice. First, some MCUs require the SPI peripheral to be disabled before changing mode or prescaler, so the reconfiguration sequence has to be ordered correctly and the chip select must be de-asserted during the change. Second, if a slave has a slow maximum clock but the bus is shared, you can't just run everything at the slowest speed — you'd waste throughput on the fast slaves. The descriptor approach handles this naturally: each transaction runs at its own slave's speed. I'd also add a small inter-transaction delay if any slave needs time between chip-select edges, and I'd verify the actual SCK frequency on a scope rather than trusting the prescaler math, since clock dividers on some MCUs don't produce the exact frequency you'd expect.

**Possible follow-ups:**
- How would you handle a slave that requires a specific number of dummy clocks before it responds?
- What would you do if two slaves on the same bus have incompatible mode requirements and you can't change either one?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging the legitimate motivation — pin count matters, especially on a small MCU — and then walk through what the shared line actually costs in terms of latency, determinism, and debuggability, because those are the things that matter in a medical device.

The first question is latency. With a shared line, the ISR has to poll each peripheral's status register to find the source, and the order of polling determines which peripheral gets serviced first. For a UART that's fine — a few microseconds of extra latency is usually acceptable. For an SPI sensor with a tight timing requirement, or for an alarm input that needs to be latched immediately, the polling order becomes a design constraint that's easy to get wrong and hard to notice until something fails intermittently.

The second question is whether the peripherals can even share a line cleanly. If the sources are level-sensitive and one of them stays asserted until serviced, the ISR can get stuck re-entering on the same source. If they're edge-sensitive, you can miss an edge that occurs while the ISR is running. Either way, the firmware has to be written carefully, and the failure mode is a missed event — which in a medical device is exactly the kind of thing that shows up in a field complaint rather than a bench test.

The third question is debuggability. With separate lines, a scope trace tells you immediately which peripheral fired. With a shared line, you're inferring from firmware logs, which is slower and less reliable.

My guidance would be: if the pin budget genuinely forces a shared line, then the design needs to specify the polling order, the edge/level behavior of each source, and a test that exercises simultaneous events on two peripherals. If the pin budget allows separate lines, the extra pins are almost always worth it. I'd frame it as a trade-off to be made explicitly, not a default.

**Possible follow-ups:**
- How would you test a shared-interrupt design to make sure no event is ever missed?
- If the team decides to keep the shared line, what would you require in the firmware design to make the polling order safe?