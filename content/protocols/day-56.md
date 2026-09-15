# protocols — Day 56

## Q1: How would you approach detecting and recovering from a UART break condition, and why does break detection matter in a medical device protocol?

**Answer:** A break condition is defined as the receive line being held in the space (logic-low) state for longer than one full character frame — typically longer than start bit + data bits + parity + stop bit. Most UART peripherals expose this as a status flag (often alongside framing and overrun errors), and some can generate an interrupt on break detection specifically.

The reason it matters is that a break is a distinct, unambiguous out-of-band signal. In many fieldbus and medical device protocols, a break is deliberately used as a frame delimiter or a "reset the receiver state machine" marker — for example, some protocols use a break to resynchronize after a fault, or to signal the start of a new session. If the firmware treats a break as just another framing error and discards it, you lose the ability to use it as a synchronization primitive, and worse, you may misinterpret the following bytes as valid data because the receiver's internal state is now misaligned.

My approach would be: first, confirm the peripheral actually reports break separately from framing error — some parts fold them together, which changes the strategy. Second, decide the protocol semantics: is a break a delimiter, an error, or a reset? Third, implement recovery so that after a break the receiver is explicitly re-armed — clear the error flags, flush any partial byte in the shift register, and reset the protocol state machine to an idle/waiting-for-start state rather than assuming the next byte is a continuation. Fourth, add a timeout so that a stuck-low line (a true fault, not a deliberate break) is detected and reported rather than silently blocking the receiver forever.

The subtlety is that a break and a stuck-low fault look identical at the electrical level for the first few milliseconds. The only way to distinguish them is duration and context: a deliberate break is bounded, a stuck line is not. So the recovery logic needs a timeout that treats "line low for longer than any legal break" as a hardware fault, not a protocol event.

**Possible follow-ups:**
- How would you distinguish a deliberate break from a disconnected or shorted line in firmware?
- If the UART peripheral does not have a dedicated break-detect interrupt, how would you implement one in software without missing short breaks?

## Q2: You're debugging a CAN-FD network where a node occasionally transmits an error frame that corrupts an in-progress message from another node, but only under heavy bus load. How would you approach this?

**Answer:** The first thing to establish is whether the error frame is a symptom or a cause. In CAN, a node only transmits an error frame when it has detected an error in a frame it is receiving — so the node emitting the error frame is usually the *victim*, not the culprit. The real question is what that node saw that made it flag an error.

Under heavy bus load, the most common causes are: a bit error caused by signal integrity (reflections, insufficient termination, excessive stub length, or a node whose transceiver is marginal), a stuff error or form error caused by a node transmitting outside its bit-time tolerance, or a CRC error from a corrupted frame. The fact that it only happens under load is a strong hint — under light load, the bus has more idle time and the transceivers have more margin; under heavy load, arbitration is more frequent, the bus is busier, and any marginal timing or signal integrity issue gets exposed.

My approach would be:
1. Capture the bus with a CAN analyzer that timestamps error frames and records the error counters of each node. Look at *which* node emits the error frame and *what* error type it reports (bit, stuff, CRC, form, ACK).
2. Check whether the error counters on any node are climbing over time — a node drifting toward error-passive is a strong signal of a marginal transceiver or a bit-timing mismatch.
3. Verify bit-timing configuration across all nodes: sample point, SJW, and prescaler must be consistent, and the sample point should be chosen so that all nodes agree within the oscillator tolerance budget. A node with a cheap crystal or an internal RC oscillator can drift enough under temperature to cause bit errors at the sample point.
4. Inspect the physical layer: termination at both ends only, stub lengths within budget, common-mode range, and whether the bus length is appropriate for the chosen arbitration and data-phase bit rates. CAN-FD is especially sensitive here because the data phase runs much faster than the arbitration phase, so a bus that worked fine at classic CAN rates can fail in the FD data phase.
5. If signal integrity looks marginal, look at whether the error frames correlate with specific message IDs or specific transmitters — that points at a particular node's driver or a particular segment of the bus.

The key discipline is not to "fix" the node emitting the error frame. That node is doing its job. The fix is almost always at the physical layer or in the bit-timing configuration of whichever node is actually transmitting the corrupted bits.

**Possible follow-ups:**
- How would you use the CAN error counters and error states to narrow down which node is the root cause?
- What is the relationship between bus length, arbitration bit rate, and data-phase bit rate in CAN-FD, and how would you choose them?

## Q3: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol does not have a built-in backpressure mechanism?

**Answer:** The first question is whether the hardware supports flow control at all. If RTS/CTS lines are available and wired, the cleanest solution is to enable hardware flow control: the receiver deasserts RTS (or CTS, depending on direction) when its receive FIFO crosses a high-water mark, and the transmitter pauses. This is handled by the UART peripheral, so it is robust against firmware latency — the only requirement is that the FIFO threshold is set low enough that the transmitter can react before the FIFO overflows.

If hardware flow control is not available, the options are:
1. **Software flow control (XON/XOFF):** the receiver sends a special byte to pause and resume the transmitter. This works only if the payload is not binary-transparent — if any data byte can equal the XON or XOFF code, you need an escaping scheme, which adds complexity and can itself be a source of bugs. It also adds latency because the pause request has to traverse the same link.
2. **Protocol-level backpressure:** if the protocol has any acknowledgment or request/response structure, the receiver can simply delay its response, which naturally throttles a well-behaved transmitter. This is the least invasive if the protocol already has request/response semantics.
3. **Increase buffering:** enlarge the receive FIFO or add a DMA-driven ring buffer so the receiver can absorb bursts. This does not solve sustained overrun, but it converts a hard failure into a latency problem, which is often acceptable.
4. **Reduce the effective data rate:** lower the baud rate, or insert idle time between frames at the protocol level. This is a last resort because it costs throughput, but it is simple and deterministic.

The decision hinges on whether the overrun is bursty or sustained. If it is bursty — the receiver occasionally gets a spike of data — buffering plus a modest high-water mark is usually enough. If it is sustained — the transmitter simply produces data faster than the receiver can process it on average — no amount of buffering will help, and you need either flow control or a lower data rate.

One more consideration: in a medical device, an overrun is not just a performance issue, it is a data integrity issue. If a byte is dropped, the receiver may silently misinterpret the rest of the frame. So the recovery path matters as much as the prevention: on overrun, the receiver should discard the entire frame and resynchronize, not try to salvage partial data.

**Possible follow-ups:**
- How would you choose the high-water mark for a hardware flow control FIFO threshold?
- If the protocol is binary-transparent and hardware flow control is unavailable, how would you implement software flow control without corrupting payload data?

## Q4: How would you approach choosing between a star topology and a daisy-chain topology for a multi-drop sensor network in a medical device, given that the sensors are physically distributed?

**Answer:** The choice is driven by a combination of electrical constraints, physical layout, and fault-tolerance requirements, and it is usually made before the protocol is finalized because it constrains which protocols are even viable.

**Star topology** means each sensor has its own point-to-point link back to a central hub. The advantages are: each link is independent, so a fault on one link does not affect the others; signal integrity is easier because each link is short and point-to-point; and the hub can use a separate transceiver per link, so there is no shared-bus arbitration problem. The disadvantages are cost and cabling — N sensors means N links, N transceivers at the hub, and N cable runs. It also does not scale well if the sensors are physically far apart, because the total cable length grows quickly.

**Daisy-chain (multi-drop) topology** means all sensors share a single bus. The advantages are: minimal cabling, one transceiver per node, and a single protocol domain. The disadvantages are: the bus is a shared resource, so you need arbitration or a master-slave discipline; a fault on the bus (a short, a stuck driver) can take down the whole network; and signal integrity degrades with stub length and total bus length, which limits the achievable bit rate.

For a medical device, the deciding factors are usually:
- **Determinism:** if any sensor requires bounded latency, a shared bus makes that harder because every node contends for the medium. A star topology gives each sensor a dedicated link, which makes latency analysis much simpler.
- **Fault isolation:** in a patient-connected device, a single fault should not take down unrelated functions. Star topology isolates faults naturally; daisy-chain does not, unless you add isolation or a fault-tolerant physical layer.
- **Cable length and routing:** if the sensors are distributed across a patient bed or a room, the total cable length may push you toward a topology that minimizes runs — which is usually daisy-chain — but then you have to respect the bus length and stub length limits of the chosen physical layer.
- **Power delivery:** if the sensors are powered over the same cable, daisy-chain means power and data share the bus, which complicates the design. Star topology lets you deliver power per link, which is simpler.

My approach would be to start from the requirements: how many sensors, how far apart, what latency and determinism each needs, what the fault-tolerance requirement is, and whether power is delivered over the cable. Then I would evaluate the candidate topologies against those requirements, and only then pick a protocol. In practice, a hybrid is common: a star of short daisy-chains, where each chain is a small multi-drop segment with its own master, and the masters are connected point-to-point to a central controller. That gives you the cabling efficiency of daisy-chain at the edge and the fault isolation and determinism of star at the core.

**Possible follow-ups:**
- How would the choice change if the sensors are battery-powered and must minimize cabling?
- What physical-layer constraints would you check first before committing to a daisy-chain topology?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I would start by acknowledging the legitimate motivation — pin count is a real constraint, and on a small microcontroller it is worth asking whether every interrupt needs its own line. But I would steer the discussion toward the specific risks of sharing an interrupt line, and let the team evaluate whether those risks are acceptable for this design.

The first issue is **latency and determinism**. When the shared interrupt fires, the ISR has to poll each peripheral to find out which one caused it. That polling takes time, and the time is variable depending on which peripheral fired and in what order the firmware checks them. For a UART receiving a byte, that variable latency can cause an overrun if the next byte arrives before the ISR has finished polling. For an SPI sensor, it can delay the read. For a GPIO alarm input, it can delay the response to a safety-relevant event. In a medical device, the alarm input is usually the one you least want to delay, so if it shares a line with a chatty UART, the alarm response time becomes dependent on UART traffic — which is exactly the kind of coupling you want to avoid.

The second issue is **interrupt priority and preemption**. If the three peripherals share one interrupt vector, they also share one priority. You cannot give the alarm input a higher priority than the UART, because they are the same interrupt. That means a long UART ISR can block the alarm ISR, or vice versa. On a microcontroller with a proper NVIC, separate interrupt lines let you assign priorities that reflect the safety criticality of each source. Sharing a line throws that away.

The third issue is **spurious and missed interrupts**. If two peripherals fire at nearly the same time, the shared line may only latch one edge, and the polling ISR may or may not see both. Depending on the peripheral's interrupt flag behavior, you can get a missed event or a spurious one. This is the kind of bug that is very hard to reproduce and very hard to debug in the field.

The fourth issue is **testability and debuggability**. With separate lines, you can set a breakpoint on the UART ISR and know exactly what fired. With a shared line, every interrupt goes through the same entry point, and you have to instrument the polling logic to know what happened. That makes the system harder to reason about during development and during regulatory testing.

So my guidance to the team would be: quantify the pin savings, then quantify the cost. If the pin savings are real and the cost is acceptable — for example, if the three peripherals are all low-rate and none is safety-critical — then sharing may be fine, provided the firmware polls in a fixed order and the worst-case latency is analyzed and documented. But if any of the three is safety-critical or has a hard latency requirement, the shared line is the wrong trade. The right answer is usually to find the pins elsewhere — a smaller package with more pins, a pin-mux change, or moving a non-critical function to a GPIO expander — rather than to compromise the interrupt architecture.

I would also point out that this is a good example of a decision that should be made with the risk file open. If the alarm input is a risk-control measure, then anything that degrades its response time is a risk-management concern, not just a firmware convenience.

**Possible follow-ups:**
- If the team decides to share the line anyway, what would you require in the firmware design to make the worst-case latency analyzable?
- How would you document this decision in the design history file so it is defensible during regulatory review?