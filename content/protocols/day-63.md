# protocols — Day 63

## Q1: How would you approach debugging an I2C bus where a slave device holds SDA low after a transaction, preventing any further communication until power is cycled?

**Answer:** This is the classic "stuck bus" condition, and the first step is to understand *why* it happens before reaching for a fix. A slave typically holds SDA low when it has lost synchronization with the master — for example, if the master was reset mid-transaction, or if a glitch on SCL caused the slave to miss a clock edge and it is now waiting for more clocks to finish a byte it thinks is still in progress. The slave is essentially mid-bit and will not release SDA until it sees the clock edges it expects.

Diagnostically, I would first confirm the condition with a scope or logic analyzer: is SDA genuinely held low while SCL is idle high? Then I would check whether the master's reset behavior or a power glitch on the slave is correlated with the lockup. On the firmware side, the standard recovery is clocking: the master temporarily reconfigures SCL as a GPIO, toggles it up to nine times (enough to flush any partial byte and generate a STOP-like condition), then issues a proper STOP and re-initializes the peripheral. This is a well-established recovery sequence and should be built into the driver rather than left as a manual step.

For prevention, I would look at whether the master ever aborts a transaction mid-byte (e.g., on a timeout), whether the slave's power rail is stable during the transaction, and whether there is adequate filtering on SCL/SDA. In a medical device, I would also want the recovery to be automatic and observable — logged as a fault event — because a bus lockup that requires a power cycle is not acceptable in the field.

**Possible follow-ups:**
- How would you decide how many clock pulses to issue during recovery, and what would you do if nine pulses don't release the line?
- Would you put the recovery logic in the I2C driver or in a higher-level supervisor task, and why?

## Q2: In a system where an SPI master talks to several slaves at different clock speeds, how would you approach structuring the firmware so that mode and speed changes are handled safely?

**Answer:** The core risk is that SPI mode (CPOL/CPHA) and clock speed are properties of the *transaction*, not the bus, so any code path that changes them must do so atomically with respect to other transactions. If two tasks share the bus and one changes the mode while the other is mid-transfer, you get corrupted data on both.

The cleanest structure is a single bus-owner abstraction: one mutex or bus-manager task owns the physical SPI peripheral, and every slave driver requests a transaction through it, specifying its required mode and speed. The manager applies the settings, performs the transfer, and releases the bus. This keeps mode/speed changes serialized and makes it impossible for two callers to interleave.

Within that, I would keep per-slave configuration in a small descriptor table (mode, max clock, chip-select pin, word size) rather than scattering constants through the code. That makes it easy to review and to change when a slave is swapped. I would also be careful about the ordering of operations: change mode and speed *before* asserting chip select, and deassert chip select before changing them again, so no slave ever sees a clock edge in the wrong mode. Finally, I would add a test that deliberately interleaves transactions to different slaves at different speeds to catch any accidental shared-state bug.

**Possible follow-ups:**
- How would you handle a slave that needs a slower clock only for certain commands but can run faster for others?
- What would you do if the SPI peripheral requires a settling delay after a mode change?

## Q3: You're debugging a CAN-FD network where a node intermittently transitions into error-passive state and then recovers on its own, with no obvious pattern. How would you approach this?

**Answer:** Error-passive means the node's transmit error counter has crossed the threshold, so it can still communicate but must be more conservative. The fact that it recovers on its own tells me the errors are transient and the counter is decrementing between bursts. The question is what is generating those errors.

I would start by capturing the error counters and the error types (bit error, stuff error, CRC error, form error, ACK error) over time, ideally with a bus analyzer that can log error frames and correlate them with traffic. The pattern often points to the cause: ACK errors suggest the node is transmitting when no other node is listening or the bus is being driven incorrectly; bit errors suggest a physical-layer issue (reflections, termination, common-mode); stuff errors can indicate a baud-rate mismatch or a node with a marginal clock.

I would then check the physical layer carefully — termination at both ends, stub lengths, common-mode voltage, and whether the node's transceiver is being powered or enabled at the right times. On a CAN-FD network, I would also verify that all nodes agree on the arbitration and data-phase bit rates and the sample point; a mismatch there can produce intermittent errors that only show up under certain traffic patterns. Finally, I would look at whether the node's firmware is doing anything unusual — for example, transmitting during bus-off recovery or with a stale configuration — and whether the error counters are being reset or masked in a way that hides the real trend.

**Possible follow-ups:**
- How would you distinguish a physical-layer problem from a protocol-configuration problem using only the error counters?
- What would you do if the error-passive events only occur when a specific other node is transmitting?

## Q4: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol does not have a built-in backpressure mechanism?

**Answer:** If the protocol has no backpressure, the first question is whether I can add one without breaking compatibility. If both ends are under my control, the cleanest fix is to add hardware flow control (RTS/CTS) if the pins are available, or a simple software handshake (XON/XOFF or an application-level "ready" message) if they are not. Hardware flow control is preferable because it is handled by the UART peripheral and does not depend on the receiver parsing the data stream.

If I cannot change the protocol, then the receiver has to absorb the burst. That means buffering: a ring buffer sized to the worst-case burst, with the ISR or DMA filling it and the application draining it. The key is to size the buffer from measured worst-case behavior, not from a guess, and to have a defined policy for what happens when it overflows — drop oldest, drop newest, or assert a fault. In a medical device, silently dropping data is usually unacceptable, so I would want the overflow to be a detectable, logged event, and I would want the system to degrade in a defined way rather than corrupt the data stream.

I would also look at the root cause: is the receiver slow because of a blocking operation elsewhere in the firmware, or because the application task is being starved? Sometimes the right fix is to move the draining to a higher-priority task or to use DMA so the CPU is not in the critical path at all.

**Possible follow-ups:**
- How would you size the ring buffer if you cannot measure the worst-case burst directly?
- What would you do if the transmitter cannot be slowed down and the receiver's buffer is already at its practical limit?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I would start by acknowledging the legitimate motivation — pin count matters, especially on a small MCU — and then walk through the failure modes rather than dismissing the idea outright. The core issue is latency and determinism: with a shared line, the ISR has to poll each peripheral to find the source, and that polling takes time. For a UART receiving a continuous stream, that delay can mean a lost byte. For an SPI sensor, it can mean missing a conversion-ready window. For a GPIO alarm input, it can mean a delay in responding to a safety-relevant event, which in a medical device is the most serious of the three.

I would ask the team to quantify the worst-case latency for each peripheral and compare it to that peripheral's timing requirement. If any of them has a hard deadline that the shared-line polling cannot meet, the approach is disqualified for that peripheral. I would also point out that the "poll to find the source" logic has to be robust against the case where two peripherals fire at nearly the same time — the ISR must not clear one flag and miss the other.

If the timing analysis shows the shared line is acceptable for some peripherals but not others, a reasonable compromise is to share the line only among the low-urgency peripherals and give the safety-critical one its own interrupt. That preserves the pin savings where it is safe and keeps the deterministic path clean. The point of the review is not to win the argument but to make the trade-off explicit and documented, so the decision is defensible later.

**Possible follow-ups:**
- How would you structure the shared ISR so that it cannot miss a second peripheral firing while it is servicing the first?
- If the team decides to keep the shared line, what would you want to see in the test plan to verify it behaves correctly under simultaneous events?