# protocols — Day 61

## Q1: How would you approach debugging an I2C bus where a slave device holds SDA low after a transaction, preventing any further communication until power is cycled?

**Answer:** A stuck-low SDA line is almost always a state-machine desynchronization between master and slave, not a hardware failure. I'd approach it in layers.

First, confirm the diagnosis: with the bus idle, measure SDA and SCL. If SDA is held low while SCL is free, the slave believes it is still mid-transaction — typically it was clocked partway through a byte and is waiting for the remaining clocks to release the line. The classic recovery is to manually clock SCL as a GPIO for up to nine pulses while SDA is released, then issue a STOP condition (SDA low-to-high while SCL is high). This walks the slave's shift register to completion so it releases SDA.

Then I'd ask *why* it desynchronized, because the recovery is a band-aid. Common root causes: a master reset or brownout mid-transaction leaving the slave mid-byte; a glitch on SCL interpreted as an extra clock edge; a slave that stretches the clock beyond the master's timeout and gets abandoned; or noise coupling onto SCL in a mixed-signal design. I'd correlate the failure with events like power transients, watchdog resets, or nearby switching activity.

For a robust design, I'd build the recovery into firmware: a bus-recovery routine that detects SDA-stuck-low at startup or after a timeout, bit-bangs the clock pulses, issues a STOP, and re-initializes the peripheral. I'd also add a hardware watchdog on the bus and consider whether the master should re-initialize the I2C peripheral after any reset. In a medical device, the recovery must be deterministic and logged, because a silently hung sensor bus is a patient-safety concern.

**Possible follow-ups:**
- How would you distinguish a slave holding SDA low from a master that failed to generate a proper STOP?
- What would you change in the hardware design to make this failure less likely in the first place?

## Q2: In a system where an SPI master talks to several slaves at different clock speeds, how would you approach structuring the firmware so that mode and speed changes are handled safely?

**Answer:** The core risk is that SPI mode (CPOL/CPHA) and clock speed are properties of the *transaction*, not the bus, so any code path that changes them must guarantee no other transfer is in flight and that the change is applied before the chip select asserts.

I'd structure it as a transaction descriptor: each slave has an associated configuration — clock speed, CPOL/CPHA, word size, chip-select line, and any inter-byte delay. The SPI driver exposes a single "transfer" call that takes the descriptor, and internally it reconfigures the peripheral, asserts the correct CS, runs the transfer, deasserts CS, and returns. The application never touches the SPI registers directly.

The safety concerns are concurrency and ordering. If multiple tasks can initiate transfers, I'd serialize access with a mutex or a queue so that a mode change can't happen mid-transfer. On an RTOS like Zephyr, I'd lean on the SPI API's per-device configuration rather than a shared global, and make sure the driver applies config atomically. I'd also verify that the peripheral actually latches the new CPOL/CPHA before the first clock edge — some controllers need a dummy write or a settling delay, and getting this wrong produces a corrupted first byte that's easy to misattribute to the slave.

Finally, I'd make the descriptor table the single source of truth, so adding a slave means adding a row, not editing transfer code. That keeps the mode/speed handling testable in isolation.

**Possible follow-ups:**
- How would you handle a slave that needs a delay between CS assertion and the first clock edge?
- What would you do if two slaves on the same bus required different CPOL/CPHA and you couldn't change modes reliably between transactions?

## Q3: You're debugging a CAN-FD network where a node intermittently transitions into error-passive state and then recovers on its own, with no obvious pattern. How would you approach this?

**Answer:** Error-passive means the node's transmit error counter (TEC) or receive error counter (REC) crossed 128, so the node is still on the bus but can no longer send active error frames. Self-recovery tells me the counters are decrementing on successful frames, so the node isn't permanently broken — it's accumulating errors in bursts.

I'd start by capturing the error counters and the error types over time. CAN controllers expose TEC/REC and often a last-error-code register; logging those with timestamps turns "no obvious pattern" into a histogram of which error dominates — bit errors, stuff errors, CRC errors, form errors, or ACK errors. That single piece of data usually splits the problem in half.

If it's ACK errors, the node is transmitting but nobody is acknowledging — a wiring, termination, or bit-rate mismatch issue, or a node that's the only transmitter on a segment. If it's bit or stuff errors, I'd suspect physical-layer integrity: reflections from incorrect termination, stub length, or a data-phase bit rate that's too aggressive for the bus length. CAN-FD is especially sensitive here because the data phase runs much faster than the arbitration phase, so a bus that's fine at the arbitration rate can fail only in the data phase. I'd check the sample-point settings and the transceiver's loop delay against the chosen data rate.

If it's CRC errors correlated with specific traffic, I'd look at whether a particular node's timing is marginal — clock tolerance, transceiver delay, or a node whose bit timing wasn't matched to the rest of the network. I'd also check for a node that's transmitting outside its allocated time or a gateway that's injecting frames at the wrong rate.

The fix depends on the cause: correct termination and stub lengths, lower the data-phase rate or adjust sample points, replace a marginal transceiver, or fix a misconfigured node. I'd verify with a bus analyzer that captures error frames and correlates them with physical events.

**Possible follow-ups:**
- How would you tell the difference between a physical-layer problem and a node configuration problem using only the error counters?
- Why does CAN-FD's data phase make bus-length and termination more critical than in classic CAN?

## Q4: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol has no built-in backpressure mechanism?

**Answer:** If the protocol has no backpressure, I have to add it at a layer the protocol doesn't own — either the electrical layer (hardware flow control) or the framing layer (software flow control), or I have to change the timing assumptions.

The cleanest option is hardware flow control: RTS/CTS. The receiver deasserts RTS when its buffer crosses a high-water mark and reasserts it below a low-water mark, and the transmitter's UART hardware pauses automatically. This requires both ends to support it and the cable to carry the extra lines — fine on a board-to-board link, sometimes impractical on a two-wire field bus. The subtlety is hysteresis: if the thresholds are too close, you get oscillation; if the receiver's FIFO is small, the transmitter may already have bytes in flight when RTS drops, so the receiver must size its buffer to absorb the worst-case in-flight data.

If hardware flow control isn't available, software flow control (XON/XOFF) is an option, but it's fragile — the flow-control characters must be escaped if they can appear in payload, and it adds latency. For a medical device I'd be cautious about it.

If neither is possible, I'd attack the problem from the other side: reduce the transmitter's burst rate, add application-level acknowledgment with a sequence number and a retransmit window, or restructure the protocol so the receiver can request data rather than being pushed to. Fundamentally, if the receiver can be slower than the transmitter and there's no backpressure, you need either a buffer large enough to absorb the burst or a protocol change — there's no third option.

I'd also instrument the link to measure the actual overflow rate and buffer occupancy, so the fix is sized to reality rather than guessed.

**Possible follow-ups:**
- How would you size the receiver buffer given a known transmitter burst size and UART FIFO depth?
- What are the risks of using XON/XOFF in a binary protocol, and how would you mitigate them?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd want to separate the two claims being made: that sharing the line saves pins (true, and worth considering), and that polling to identify the source is acceptable (this is where the real risk lives). I'd steer the review toward the second claim.

The key question is latency and determinism. When the shared interrupt fires, the ISR has to read each peripheral's status register to find out who asserted. That takes time, and worse, it's non-deterministic — the order of polling affects how quickly the alarm input is serviced. For a GPIO alarm input in a medical device, that latency could matter a great deal. I'd ask the team to state the worst-case service time for the alarm and check whether polling can meet it.

There's also a correctness hazard: if two peripherals assert at nearly the same time, a naive "read one, clear it, return" ISR can miss the second event or clear a flag it didn't service. The ISR must loop until all sources are cleared, which lengthens the critical section and can starve lower-priority work. And if the peripherals share a level-triggered line, a source that isn't cleared will re-trigger immediately, potentially causing an interrupt storm.

I'd frame the decision as a trade: pins saved versus determinism, ISR complexity, and debuggability. A reasonable compromise is to share the line only among peripherals with similar latency requirements and to keep the alarm input on its own line, or to use a small interrupt controller or GPIO expander with per-source status. I'd ask the junior engineer to prototype the shared-line ISR and measure worst-case latency under simultaneous events — that turns an opinion into data, and it's a good learning exercise either way.

**Possible follow-ups:**
- How would you structure the ISR so that no event is lost when two sources assert simultaneously?
- What would change if the shared line were edge-triggered instead of level-triggered?