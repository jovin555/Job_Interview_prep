# protocols — Day 53

## Q1: How would you approach choosing between a star topology and a daisy-chain topology for a multi-drop sensor network in a medical device, given that the sensors are physically distributed?

**Answer:** The decision hinges on the electrical characteristics of the physical layer, the cable routing constraints, and the failure-containment requirements, not just on convenience of wiring.

A daisy-chain (bus) topology is the natural fit for differential buses like RS-485 and CAN-FD: the transceivers are designed to drive a terminated transmission line, and as long as stub lengths from the main trunk to each node are kept short relative to the bit period, signal integrity stays manageable. It minimizes cable and connector count, which matters in a device where every connector is a potential reliability and cleaning/reprocessing concern. The cost is that a single break in the trunk can take down downstream nodes, and termination must be placed correctly at the two physical ends of the bus.

A star topology is more forgiving from a fault-containment standpoint — a failed node or a cut branch affects only that branch — but it is electrically hostile to high-speed differential signaling because each branch looks like a stub. You can make a star work with point-to-point links (each sensor gets its own transceiver pair, effectively many independent links) or with a hub/repeater, but that multiplies transceivers, power, and cost. For lower-speed single-ended buses like I2C, a star is generally a bad idea because the lumped capacitance and reflections degrade edges, and the bus capacitance limit is shared across all branches.

So my approach would be: first characterize the required data rate, cable length, and node count; then check whether the chosen physical layer tolerates stubs at that rate. If it does, daisy-chain with proper termination and short stubs is usually the right answer for a distributed medical sensor network. If fault containment or physical routing forces a star, I'd either accept the rate/length penalty, add a hub/repeater, or move to a point-to-point topology per sensor. I'd also factor in whether nodes need power over the bus, since that constrains topology and conductor count as much as signaling does.

**Possible follow-ups:**
- How would you decide where to place termination resistors in a daisy-chain that has a connector in the middle of the run?
- If a star topology is unavoidable at a given data rate, what techniques would you use to preserve signal integrity?

## Q2: You're debugging a CAN-FD network where a node intermittently transitions into error-passive state and then recovers on its own, with no obvious pattern in when it happens. How would you approach this?

**Answer:** The fact that the node recovers on its own tells me the error counters are crossing the error-passive threshold and then decaying back below it — so this is a recurring, bounded error condition rather than a hard fault. I'd work from the CAN error model outward.

First, I'd capture the actual error frames and the error counter values over time using a bus analyzer, because the *type* of error tells you a lot. A rising receive error counter with form/stuff/CRC errors points at the receiver side — bit timing, sample point, or signal integrity. A rising transmit error counter with ACK errors points at the transmitter not being heard, which is often a wiring, termination, or transceiver issue. Bit errors that correlate with specific message IDs suggest arbitration or a node transmitting out of turn.

Second, I'd look at bit timing and sample point. CAN-FD has separate arbitration-phase and data-phase bit rates, and the sample point has to be consistent across nodes for the data phase to work reliably. If one node's oscillator tolerance or prescaler settings are marginal, it can pass at low rates and fail intermittently at higher data-phase rates. I'd verify the configured sample point and SJW against the oscillator tolerance budget, especially if any node uses an internal RC oscillator.

Third, I'd check the physical layer: termination value and placement, stub lengths, common-mode range, and whether the intermittent behavior correlates with a specific physical event — a motor starting, a relay switching, a cable being moved. Intermittent errors that "just happen" often correlate with an external disturbance or a temperature/load condition.

Fourth, I'd check whether the error-passive node is being starved of bus access or is transmitting at a rate that pushes its error counters up during arbitration losses. In a heavily loaded bus, a low-priority node can accumulate errors from repeated arbitration loss and bus-off recovery behavior.

The key is to separate "the node is misconfigured" from "the bus is disturbed" from "another node is misbehaving," because the fix is completely different in each case.

**Possible follow-ups:**
- How would you distinguish a bit-timing mismatch from a signal-integrity problem using only the error frame types?
- What would you check if the error-passive transitions only happen when a particular other node is transmitting?

## Q3: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol does not have a built-in backpressure mechanism?

**Answer:** If the protocol has no backpressure, I have three broad options, and the right one depends on whether I can change the protocol, change the hardware, or only change the firmware on one side.

The cleanest fix, if the hardware supports it, is to enable hardware flow control (RTS/CTS) and have the receiver deassert RTS when its buffer is near full. That gives byte-level backpressure with no protocol change. The catch is that both ends must honor it, and the receiver's RTS must be driven by a real buffer watermark, not just a GPIO toggled in software — otherwise the latency of the software response defeats the purpose.

If hardware flow control isn't available, the next option is software flow control (XON/XOFF), but that only works if the payload is text-like and you can guarantee the XOFF/XON bytes never appear in data. In a binary medical protocol that's usually not safe, so I'd avoid it unless the framing guarantees it.

If neither is possible, I'd attack the problem from the receiver side: increase the receive buffer, use DMA with a large circular buffer so the CPU isn't the bottleneck, and make sure the receive ISR does the minimum possible work. Often "the receiver can't keep up" is really "the receiver's ISR is too slow" or "the receiver is blocking on something else." I'd profile the receive path before assuming the link is the problem.

As a last resort, if the transmitter can be modified, I'd add application-level pacing: the transmitter sends a bounded burst and waits for an application-level ACK before continuing. That's effectively adding backpressure at the protocol layer, which is more work but gives deterministic behavior.

In a medical device I'd also want the failure mode to be safe: if the receiver's buffer does overflow, the firmware must detect it (overrun flag, framing error) and either request a retransmit or flag the data as invalid, rather than silently using corrupted data.

**Possible follow-ups:**
- How would you size the receive buffer and the RTS watermark to guarantee no overrun at the worst-case interrupt latency?
- What would you do if the transmitter is a third-party module you cannot modify?

## Q4: You're designing a system where an SPI master needs to communicate with three slaves, each requiring different clock polarity and phase settings. How would you approach the hardware and firmware architecture?

**Answer:** SPI mode (CPOL/CPHA) is a per-transaction property of the master's peripheral, not a property of the bus, so the first question is whether the master's SPI peripheral supports changing mode between transactions. Most modern MCU SPI peripherals do, but some have a single mode register that must be reconfigured, and reconfiguring mid-stream has timing implications.

If the master supports per-transaction mode changes, the architecture is straightforward: the firmware's SPI abstraction layer takes the target device's mode as part of the transfer descriptor, and the driver reconfigures CPOL/CPHA before asserting that device's chip select. The critical detail is ordering — you must set the mode *before* asserting CS, and you must not change it while any CS is asserted. I'd enforce that in the driver so a caller can't accidentally corrupt an in-flight transaction.

If the master does *not* support per-transaction mode changes, or if the reconfiguration cost is too high for the required throughput, the options are: (a) use a GPIO-based bit-banged SPI for the odd-mode device, accepting the throughput penalty; (b) use a separate SPI peripheral for the device with the incompatible mode; or (c) insert a small external logic/mux that translates the mode, which is usually more trouble than it's worth.

There's also a hardware consideration: if the three slaves share MISO, only one may drive MISO at a time, so chip-select discipline is essential. And if the slaves have different maximum clock rates, the master must run each transaction at the rate that device supports — you can't run the whole bus at the fastest device's rate.

So my approach: confirm the master's mode-switching capability first, then design the driver so mode is a per-transfer parameter, then verify with a scope that CS, clock, and data are correctly ordered for each device. If the master can't switch modes, I'd split the bus or bit-bang rather than try to force a single mode on incompatible devices.

**Possible follow-ups:**
- How would you verify on a scope that the mode is being applied correctly for each device?
- What would you do if two slaves share a chip select but require different modes?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging the legitimate motivation — pin count is a real constraint, and sharing an interrupt line is a recognized technique. Then I'd walk the team through the specific risks, because the answer depends entirely on the latency and determinism requirements of each peripheral.

The core issue is that a shared interrupt line turns a hardware event into a software search. When the ISR fires, the firmware has to poll each peripheral's status register to find the source. That adds latency proportional to the number of peripherals and the time to read each status register, and it introduces a failure mode: if two peripherals assert simultaneously, the ISR must handle both, and if it only handles the first one it finds, the second event can be lost or delayed.

For the UART, the risk is a receive overrun — if the ISR is busy polling the SPI and GPIO before it gets to the UART, and the UART's FIFO fills, you lose data. For the SPI sensor, the risk depends on whether the SPI is master or slave; if it's a slave, a missed or delayed interrupt can mean a missed transaction. For the GPIO alarm input, the risk is the opposite: an alarm is often the highest-priority event in a medical device, and burying it behind two other polls is exactly backwards.

So I'd frame the evaluation around three questions: What is the worst-case latency each peripheral can tolerate? What is the worst-case latency this shared-interrupt scheme can produce, including the case where all three fire at once? And what happens if the ISR misses a source?

If the answer is that all three peripherals are low-rate and latency-tolerant, the shared line is fine and saves a pin. If any of them — especially the alarm — has a hard latency bound, I'd push back and either give that peripheral its own interrupt or use a priority-aware interrupt controller (many MCUs have NVIC priority levels, but that only helps if the lines are separate). A middle ground is to share the line but have the ISR read a combined status register or use a small CPLD/OR-gate with a status latch so the ISR can identify the source in one read.

I'd also make sure the team documents the latency budget and the simultaneous-event case in the design, because "it worked on the bench" is not evidence that it meets the requirement.

**Possible follow-ups:**
- How would you measure the worst-case ISR latency of the shared-interrupt scheme?
- If the alarm input must have its own interrupt but pins are scarce, what alternatives would you consider?