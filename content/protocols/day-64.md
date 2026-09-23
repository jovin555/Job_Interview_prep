# protocols — Day 64

## Q1: How would you approach debugging an I2C bus where communication works reliably at 100 kHz but produces intermittent NACKs at 400 kHz, with the same devices and the same PCB?

**Answer:** The fact that the same hardware works at 100 kHz but not 400 kHz points strongly at a timing/margin problem rather than a logic or addressing problem, so I'd work through the physical layer first. At 400 kHz the bus has roughly a quarter of the bit period, so anything that was marginal at 100 kHz — rise time, setup/hold margin, noise coupling — becomes a real failure.

I'd start by scoping the bus: look at SDA and SCL rise times against the I2C spec limits (roughly 300 ns for fast mode), and check whether the pull-up resistors are sized for the actual bus capacitance. A pull-up that's fine at 100 kHz can be too weak at 400 kHz, giving slow edges that eat into setup time and cause marginal NACKs. I'd measure the actual bus capacitance or estimate it from device count and trace length, then recalculate the pull-up value using the RC rise-time relationship, keeping in mind the trade-off: smaller pull-ups improve edges but increase low-level sink current and power.

Next I'd look for signal integrity issues — ringing, crosstalk from adjacent high-speed traces, or ground bounce — by probing at multiple points along the bus, not just at the master. A NACK that only appears at the far end of the bus often means the edge has degraded by the time it reaches that device. I'd also check whether any slave is doing clock stretching and whether the master's timing assumptions hold at the faster rate.

Finally I'd consider whether the issue is actually electrical or protocol-level: a scope capture showing a clean waveform but a NACK would push me toward the device's internal timing (e.g., a slave that needs more time between transactions than the master allows at 400 kHz). The systematic approach is to separate "is the waveform correct?" from "is the protocol timing correct?" and narrow from there.

**Possible follow-ups:**
- How would you decide between lowering the pull-up resistance and reducing bus capacitance by splitting the bus?
- If the waveform looks clean but NACKs persist, what device-level timing parameters would you check?

## Q2: In a system where an SPI master talks to several slaves at different clock speeds and with different CPOL/CPHA modes, how would you approach structuring the firmware so that mode and speed changes are handled safely?

**Answer:** The core risk here is that SPI mode and clock speed are properties of the *transaction*, not the bus, so any code path that changes them must guarantee the bus is idle and no other transaction is in flight. I'd structure this around a single serialized access layer rather than letting callers poke the peripheral registers directly.

Concretely, I'd define a per-device descriptor that captures its required mode (CPOL/CPHA), max clock, word size, and any timing constraints like inter-byte delays. The low-level driver would take that descriptor, reconfigure the peripheral, perform the transfer, and leave the bus in a known idle state. All SPI access goes through this layer, so there's exactly one place where mode/speed changes happen.

The safety concerns are: (1) never change mode mid-transaction, (2) ensure chip-select lines are deasserted before reconfiguring, and (3) handle the case where a higher-priority transfer preempts a lower one. In an RTOS context I'd protect the bus with a mutex and possibly a priority-inheritance scheme so a low-priority task holding the bus doesn't block a time-critical one. If the hardware supports it, I'd also verify that the peripheral actually latched the new configuration before starting the transfer — some controllers need a settle cycle after a mode change.

I'd also add a small guard: after reconfiguring, read back the control register to confirm the mode bits took effect, and assert on mismatch during development. That catches the class of bug where a mode change silently fails and you get corrupted data only on one device.

**Possible follow-ups:**
- How would you handle a slave that requires a minimum delay between the mode change and the first clock edge?
- What would you do if two devices on the same bus required incompatible modes and you couldn't reconfigure between them fast enough?

## Q3: You're debugging a CAN-FD network where a node intermittently enters error-passive state and then recovers on its own, with no obvious pattern. How would you approach this?

**Answer:** Error-passive is a symptom, not a root cause — the node has accumulated enough transmit or receive errors to cross the threshold, and then recovers because the error counters decrement on successful frames. So the real question is what's causing the error accumulation in the first place. I'd approach it as a data-gathering exercise before jumping to conclusions.

First, I'd capture the error counters over time — TEC and REC — along with the specific error types (bit errors, stuff errors, CRC errors, form errors, ACK errors). The *type* of error is the biggest clue. ACK errors suggest the node's transmissions aren't being acknowledged, which points at arbitration loss, bus loading, or a physical layer issue. Bit errors suggest signal integrity. Stuff errors can indicate a clock tolerance problem or a node transmitting at a slightly wrong bit rate.

Second, I'd look at the timing relationship. Does the error-passive event correlate with a specific other node transmitting, with bus load crossing some threshold, or with temperature/voltage changes? CAN-FD is sensitive to the data-phase bit rate and the transceiver's propagation delay; a marginal transceiver or a long stub can cause errors only under certain patterns.

Third, I'd check the physical layer: termination, stub lengths, common-mode voltage, and whether the bus length is compatible with the chosen bit rate. CAN-FD's higher data-phase rate shortens the bit time, so a bus that was fine at classic CAN rates can become marginal.

Finally, I'd consider whether the node's own configuration is the issue — sample point, SJW, and prescaler settings that are marginal for the network's actual bit timing. A node with a slightly off sample point can accumulate errors only when it's receiving from a particular transmitter.

**Possible follow-ups:**
- If the error counters show mostly ACK errors, what would that tell you about the network versus the node?
- How would you distinguish a physical-layer problem from a bit-timing configuration problem?

## Q4: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol has no built-in backpressure mechanism?

**Answer:** The first thing I'd establish is whether the link has hardware flow control pins available (RTS/CTS) or whether I'm limited to the data lines. If RTS/CTS is available, that's the cleanest solution — the receiver deasserts RTS when its buffer is near full, and the transmitter's UART hardware automatically pauses. But that only works if both ends honor it and the cabling carries the extra signals, which isn't always the case.

If I only have TX/RX, I'd implement software flow control at the application layer. The standard approach is XON/XOFF: the receiver sends a special control byte to pause and resume transmission. The catch is that XON/XOFF bytes can collide with payload data, so the protocol needs an escaping mechanism or a reserved control channel. In a medical device I'd be cautious about XON/XOFF because a lost or corrupted flow-control byte can leave the link stuck in the wrong state.

A more robust approach is to design the protocol so the receiver never has to buffer more than it can handle: use fixed-size frames with an explicit ACK, and have the transmitter only send the next frame after the previous one is acknowledged. That trades throughput for determinism, which is often the right call in a medical context. I'd also size the receiver's ring buffer generously and add a watermark interrupt so the firmware can react before the buffer overflows rather than after.

Regardless of mechanism, I'd add a timeout on the transmitter side so that if the receiver stops responding, the link doesn't hang forever — it fails safe and reports the condition.

**Possible follow-ups:**
- How would you handle the case where the flow-control byte itself is corrupted in transit?
- What are the trade-offs between ACK-based flow control and XON/XOFF in terms of latency and complexity?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd want to steer the discussion away from "does it save pins?" (it does) toward "what does it cost us in latency, determinism, and debuggability?" — because in a medical device those usually matter more than a couple of GPIO pins.

The first question I'd raise is latency. With a shared interrupt, the ISR has to poll each peripheral to find the source. For the alarm input, that polling delay could be the difference between meeting and missing a safety-relevant response time. I'd ask the team to quantify the worst-case time from the physical event to the handler running, including the polling of the other two peripherals. If the alarm path has a hard deadline, sharing an interrupt line with a chatty UART is a poor fit.

The second question is determinism and priority. A UART receiving a burst of data can generate frequent interrupts; if it shares a line with the alarm input, the alarm handler's latency becomes dependent on UART traffic. Separate interrupt lines let you assign priorities and guarantee the alarm is serviced promptly.

The third is debuggability and failure modes. With a shared line, a stuck peripheral can mask the others, and diagnosing which device actually asserted the line requires extra instrumentation. That's a real cost during bring-up and field investigation.

I'd also point out that "just poll to find out which one fired" is fine as a *fallback* but shouldn't be the primary mechanism for a safety-relevant input. A reasonable compromise might be to share the line between the UART and SPI sensor (both non-safety-critical, both tolerant of a few microseconds of polling) while giving the alarm input its own dedicated interrupt. That preserves the pin savings where it's harmless and protects the path where it matters. I'd frame the decision as a trade study with explicit criteria rather than a yes/no on the junior engineer's proposal.

**Possible follow-ups:**
- How would you quantify the worst-case latency introduced by polling three peripherals in one ISR?
- If pin count were truly constrained, what alternatives would you consider to a fully shared interrupt line?