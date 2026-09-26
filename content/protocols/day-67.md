# protocols — Day 67

## Q1: How would you approach debugging an I2C bus where communication works reliably at 100 kHz but produces intermittent NACKs at 400 kHz, with the same devices and the same PCB?

**Answer:** The fact that the same hardware works at 100 kHz but not at 400 kHz points strongly at a timing or signal-integrity margin issue rather than a logic or addressing problem. The first thing I'd do is separate the two failure modes: is the NACK happening on the address byte, on a data byte, or on the final ACK of a read? That tells me whether the slave is failing to recognize its address (a timing/setup issue) or failing to deliver data in time (a clock-stretching or processing-latency issue).

At 400 kHz the bit period shrinks to 2.5 µs, so everything that was comfortably within margin at 100 kHz now has roughly a quarter of the timing budget. I'd work through the physical layer first: measure the actual rise time of SDA and SCL with a scope at the slave's pins, not at the master. If the rise time is a significant fraction of the bit period, the effective high-level voltage at the sampling point may not reach VIH before the master samples it. That usually means the pull-up resistors are too weak for the added bus capacitance — the RC time constant is fine at 100 kHz but marginal at 400 kHz. I'd compute the actual bus capacitance (traces, connectors, device pins) and check it against the fast-mode limit, then recalculate the pull-up value to hit the rise-time target while staying within the sink-current budget of the weakest device.

If the edges look clean, I'd look at clock stretching. A slave that needs more processing time may stretch SCL, and if the master doesn't honor stretching properly — or has a timeout that's too aggressive — you get exactly this kind of intermittent NACK that scales with speed. I'd also check for setup/hold violations introduced by the faster clock, and whether any device on the bus is only rated for standard-mode. Finally, I'd consider whether the NACKs correlate with temperature, supply voltage, or specific transactions, since a marginal timing issue often only manifests under one corner condition.

**Possible follow-ups:**
- How would you distinguish a pull-up problem from a clock-stretching problem using only a scope?
- If the bus capacitance is genuinely too high for 400 kHz, what are your options short of redesigning the board?

## Q2: You're designing a system where an SPI master needs to communicate with three slaves, each requiring different clock polarity and phase settings. How would you approach the hardware and firmware architecture?

**Answer:** The core constraint is that CPOL and CPHA are properties of the master's SPI peripheral configuration, not of the individual slave — the master generates the clock, so it can only be in one mode at a time. That means the firmware has to reconfigure the SPI peripheral between transactions whenever it switches to a slave that uses a different mode. The hardware side is straightforward: independent chip selects for each slave, and the shared MOSI/MISO/SCLK lines.

The real engineering work is in the firmware architecture. I'd build a small abstraction layer where each slave is described by a configuration struct — mode, clock speed, word size, chip-select pin — and the driver applies that configuration before every transaction. The critical discipline is that mode and speed changes must only happen when the bus is idle and all chip selects are deasserted. If you reconfigure the peripheral mid-transaction, or while another slave is still selected, you can glitch the clock or drive MISO at the wrong moment and corrupt the other device's data. So the sequence is always: assert CS, apply config if needed, transfer, deassert CS, and only then allow a reconfiguration for the next device.

I'd also think about whether reconfiguring on every transaction is acceptable. If one slave is polled at high frequency and another rarely, it may be worth grouping transactions by mode to minimize reconfigurations, or even considering whether a second SPI peripheral on the MCU could dedicate one bus to the odd-mode device. On the layout side, if the slaves are at different speeds, the shared clock trace has to be routed for the fastest device's signal integrity, and I'd keep the slower devices' chip-select and data traces short to avoid stubs that degrade the high-speed edges.

**Possible follow-ups:**
- What could go wrong if you change CPOL/CPHA while a chip select is still asserted?
- How would you handle a slave that requires a mode the MCU's SPI peripheral doesn't support in hardware?

## Q3: In a CAN-FD network for a medical device, you need to ensure that a high-priority safety-critical message is never delayed by more than 500 microseconds. How would you approach guaranteeing this timing requirement?

**Answer:** I'd start by being precise about what "never delayed by more than 500 µs" actually means — is that worst-case latency from the event occurring to the message being fully received, or from the message being queued to the start of transmission? That distinction drives the whole analysis. For a safety-critical bound, I'd assume the worst case: the message becomes ready to transmit at the exact moment a lower-priority frame has just started, and I need the full end-to-end time.

The first lever is CAN identifier priority. CAN arbitration is non-destructive and priority-based on the identifier, so the safety-critical message must have the lowest numerical ID on the bus. That guarantees it wins arbitration against any lower-priority traffic the moment the bus goes idle. But arbitration only helps once the bus is idle — if a lower-priority frame is already transmitting, the high-priority frame has to wait for that frame to finish. So the worst-case latency is bounded by the longest possible lower-priority frame that could be in flight when the critical message becomes ready.

That's where CAN-FD's dual bit rate matters. The arbitration phase runs at the slower nominal bit rate, but the data phase runs at the faster data bit rate. A long telemetry frame spends most of its time in the data phase, so its total on-wire time is much shorter than a classic CAN frame of the same payload. I'd compute the maximum frame time for the largest lower-priority frame, add the inter-frame spacing, and confirm the total fits within the 500 µs budget with margin. If it doesn't, the options are to cap the maximum payload of lower-priority frames, reduce the number of nodes that can transmit long frames, or raise the data-phase bit rate.

I'd also account for error frames and retransmission. A single error frame can add a full retransmission to the worst case, so the budget has to include at least one retransmission if the requirement is truly "never." And I'd verify the whole thing empirically with a bus analyzer that timestamps the critical message under worst-case load, because the analytical bound and the measured behavior can diverge once you factor in transceiver delays and node-level queuing.

**Possible follow-ups:**
- How does the error-passive state of a node affect your worst-case latency analysis?
- If the analytical worst case exceeds the budget, how would you decide between changing the bit rate and changing the message set?

## Q4: You're debugging a system where a USB 2.0 device enumerates correctly on most hosts but fails on a specific embedded host controller. The device uses a composite descriptor with both HID and vendor-specific interfaces. How would you approach isolating whether the problem is in the descriptor configuration, the host controller driver, or the device firmware?

**Answer:** I'd treat this as a bisection problem and try to move the boundary between "device-side" and "host-side" as cleanly as possible. The first step is to capture the actual USB traffic on the failing host with a bus analyzer, because enumeration is a well-defined sequence of control transfers and the point of failure tells you a lot. If the device fails before it even responds to the first GET_DESCRIPTOR, that's a physical or VBUS issue. If it responds to the device descriptor but fails on the configuration descriptor, that points at the descriptor content or the host's parsing of it.

A composite device is a common source of host-specific failures because the configuration descriptor contains class-specific descriptors and interface association descriptors, and different host stacks are more or less tolerant of variations in how those are ordered and sized. I'd compare the exact descriptor bytes the device returns against the USB specification and against what a known-good composite device returns. Common culprits are a wrong wTotalLength, an interface association descriptor that isn't placed correctly, or a HID report descriptor that's technically valid but that a particular host stack rejects.

To separate device firmware from host driver, I'd plug the same device into a different host with a known-good stack and confirm it enumerates — if it does, the device firmware is probably fine and the issue is host-side tolerance. Then I'd try a minimal composite device with the same descriptor structure but stripped-down functionality; if that also fails on the same host, it's the descriptor structure, not the endpoints. If it passes, the problem is in how the firmware handles the interface-specific requests after enumeration. I'd also check whether the failing host is a USB 1.1 or early USB 2.0 controller with known quirks around split transactions or high-speed chirp, since embedded hosts often have less mature stacks.

**Possible follow-ups:**
- What specific descriptor fields would you check first on a composite device that fails enumeration on one host?
- How would you determine whether the failure is a high-speed vs full-speed negotiation issue?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd want to make sure the team evaluates the proposal on its actual merits rather than dismissing it out of hand — sharing an interrupt line is a legitimate technique in some designs, and pin count is a real constraint. But I'd steer the discussion toward the specific risks it introduces in this context, and let the team reason through whether those risks are acceptable.

The first question is latency. If the firmware has to poll three peripherals to find out which one asserted the shared line, the worst case is that it polls the wrong two first and only finds the real source on the third read. For a UART receiving a byte, that delay could mean an overrun. For an SPI sensor, it could mean missing a data-ready window. For a GPIO alarm input, the whole point is usually that it's time-critical, so adding polling latency to an alarm path is a serious concern. I'd ask the team to quantify the worst-case service time for each source and compare it against each peripheral's timing requirement.

The second question is whether the sources can be distinguished at all. If all three lines are open-drain and wire-OR'd, then when the interrupt fires the firmware genuinely cannot tell which one asserted without reading each peripheral's status register — and reading a status register may itself clear the flag, so the order of reads matters. If the lines are push-pull and tied together, you can get contention. I'd ask the junior engineer to walk through the exact sequence of register reads and confirm that no source can be missed or double-counted.

The third question is what happens under simultaneous events. If the UART and the alarm both assert at the same time, the firmware has to handle both, and the polling approach has to be robust to that. I'd also raise the diagnostic angle: a shared line makes it harder to attribute an interrupt storm to a specific peripheral during field debugging.

My guidance to the team would be to weigh the pin savings against these costs, and consider alternatives — a small I/O expander, a CPLD, or simply accepting the extra pins if the package has them. If the team decides to go with the shared line, I'd want to see a documented worst-case latency analysis and a clear interrupt-service routine that reads all sources in a defined order.

**Possible follow-ups:**
- How would you structure the interrupt service routine to minimize the risk of missing a source?
- Under what circumstances would you actually endorse the shared-line approach?