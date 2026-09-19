# protocols — Day 60

## Q1: How would you approach debugging a system where an I2C bus works reliably at 100 kHz but produces intermittent NACKs at 400 kHz, with the same devices and the same PCB?

**Answer:** The first thing I'd do is separate the electrical problem from the protocol problem, because a speed-dependent failure on the same hardware almost always points to the analog layer rather than the firmware.

At 100 kHz, the bus has roughly 10 µs per bit; at 400 kHz, that drops to 2.5 µs. The rise time of SDA and SCL is set by the RC time constant formed by the pull-up resistors and the total bus capacitance. If the rise time is a significant fraction of the bit period, the receiver may not see a valid logic high before it samples, which shows up as a NACK or a spurious start/stop. So I'd start by scoping SDA and SCL at the failing speed and measuring the actual rise time — not just checking that it looks "square enough." The I2C spec gives a maximum rise time of 300 ns for fast mode, and if I'm close to or over that, the pull-ups are too weak for the capacitance on the board.

From there I'd work through the usual suspects in order: total bus capacitance (traces, connectors, device pins, and any cable), pull-up value versus the target rise time, and whether the pull-ups are referenced to the right rail. A common trap is that a device's input threshold or its own internal capacitance changes behavior at higher edge rates. I'd also check for anything that could be marginal only at speed — a long stub, a connector with high pin capacitance, or a device that's technically fast-mode capable but has a slow internal setup time.

If the electrical layer checks out, I'd look at the protocol layer: is the master respecting the minimum bus-free time between transactions, is clock stretching being handled, and is there any chance of a repeated start being misinterpreted. But I'd only go there after I've confirmed the edges are clean, because chasing firmware when the problem is a 10 kΩ pull-up on a 300 pF bus wastes a lot of time.

**Possible follow-ups:**
- How would you calculate the maximum allowable pull-up value given a measured bus capacitance and a target rise time?
- If the rise time is fine but you still get NACKs only at 400 kHz, what would you check next?

## Q2: How would you approach designing the firmware architecture for an SPI master that must talk to several slaves running at different clock speeds and using different CPOL/CPHA modes?

**Answer:** The key insight is that SPI mode and clock speed are properties of the *transaction*, not of the bus, so the firmware needs a clean way to reconfigure the peripheral between transactions without leaving the bus in an ambiguous state.

I'd structure this as a small SPI abstraction layer that owns the peripheral and exposes a transaction API — something like `spi_transfer(device, tx_buf, rx_buf, len)` — where the device descriptor carries its mode, max clock, chip-select line, and any per-device timing constraints. The layer's job is to, for each call: assert the correct chip select, configure CPOL/CPHA and the clock divider for that device, run the transfer, then deassert the chip select and return the peripheral to a safe idle state.

The subtle parts are the transitions. When you change CPOL, the idle level of SCL changes, so you must ensure the clock line is in the correct idle state *before* the chip select goes active, otherwise a slave can see a spurious edge. Similarly, changing the clock divider mid-operation can glitch the clock, so the reconfiguration has to happen while the peripheral is disabled and the bus is idle. I'd also make sure the chip-select deassertion happens after the last clock edge with enough setup/hold margin, and that no two devices are ever selected simultaneously — that's a classic source of MISO contention.

For testability, I'd keep the layer free of any knowledge about *what* the devices are; it just moves bytes. That makes it easy to unit-test with a mock peripheral and easy to reason about when a new sensor is added. If the MCU has multiple SPI peripherals, I'd also consider whether grouping devices by mode onto separate peripherals reduces the reconfiguration churn, but that's a hardware decision that should be made with the layout in mind.

**Possible follow-ups:**
- How would you handle a device that needs a delay between chip-select assert and the first clock edge?
- What would you do if two devices on the same bus required incompatible modes and you couldn't add a second peripheral?

## Q3: You're debugging a CAN-FD network where a node occasionally goes error-passive and then recovers on its own, with no obvious pattern. How would you approach this?

**Answer:** Error-passive is a symptom, not a root cause — it means the node's transmit error counter or receive error counter crossed 128. So the real question is what's driving the error counter up in the first place, and why it recovers.

I'd start by capturing the error counters over time, either through the controller's diagnostic registers or by logging the error frames on a bus analyzer. The pattern of *which* counter is climbing tells you a lot. If the transmit error counter is climbing, the node is failing to win arbitration or is seeing its own transmissions corrupted — that points to a physical-layer or bit-timing issue on that node's side. If the receive error counter is climbing, the node is seeing errors in frames from other nodes, which points to a bus-wide problem or a node-specific receiver issue.

The fact that it recovers on its own is important. CAN's error counters decrement on successful transmissions and receptions, so a node that goes error-passive and then recovers is experiencing intermittent errors, not a hard fault. That pattern often comes from something marginal: a bit-timing mismatch between nodes (sample point or SJW not aligned across the network), a termination or stub issue that only bites at certain data-phase bit rates, or a node whose oscillator drifts with temperature. CAN-FD makes this worse because the data phase runs at a much higher bit rate than the arbitration phase, so a network that's fine in arbitration can fail only in the data phase.

I'd check the bit-timing configuration across all nodes first — sample point, SJW, and the data-phase prescaler — because a mismatch there is a common and easily fixed cause. Then I'd look at the physical layer: termination at both ends, stub lengths, and whether the data-phase bit rate is actually supportable over the cable length in use. If the errors correlate with temperature or with specific traffic patterns, that narrows it further.

**Possible follow-ups:**
- How would you determine whether the problem is a single node or the whole network?
- What's the relationship between the error counters and the node's transition between error-active, error-passive, and bus-off?

## Q4: How would you approach implementing flow control on a UART link where the receiver occasionally can't keep up with the transmitter, but the protocol has no built-in backpressure mechanism?

**Answer:** The first question is whether I can change the protocol or only the firmware on one side, because that determines whether I add real flow control or work around its absence.

If I control both ends, the cleanest answer is hardware flow control — RTS/CTS — where the receiver deasserts its ready line when its buffer is close to full, and the transmitter respects that before sending the next byte. That's the standard solution and it's well understood. The subtlety is that RTS/CTS only helps if the transmitter checks it *before* starting a byte, and if the receiver asserts it early enough that the transmitter's in-flight byte doesn't overflow the buffer. So the threshold has to account for the worst-case latency between the receiver deciding to deassert and the transmitter actually stopping.

If I can't change the protocol — say the other end is a third-party module — then I have to solve it on my side. Options include: increasing the receiver's buffer and draining it faster (often by moving the UART handling to a higher-priority interrupt or DMA), reducing the transmitter's effective rate by inserting gaps between bytes or frames, or using a software handshake embedded in the payload if the protocol has any spare field. The last one is fragile because it depends on the other end cooperating, so I'd treat it as a last resort.

I'd also want to understand *why* the receiver can't keep up. Is it a CPU load problem, a buffer size problem, or a burstiness problem? If the data arrives in bursts, a larger buffer with DMA may be enough. If it's sustained overload, no amount of buffering fixes it — the link is simply over-subscribed and the answer is to reduce the data rate or split the traffic.

**Possible follow-ups:**
- How would you size the receive buffer given a known worst-case interrupt latency?
- What are the failure modes of relying on a software handshake embedded in the payload?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd want to steer the discussion away from "does it save pins" and toward "what does it cost us in latency, determinism, and debuggability," because those are the things that actually matter in a medical device.

The first thing I'd ask is what the worst-case response time is for each of those three sources. The GPIO alarm input is the one that worries me most — if it's a patient alarm, the system may have a hard requirement on how quickly it's acknowledged, and a shared interrupt that requires the firmware to poll three peripherals to figure out who fired adds latency and, worse, adds a failure mode where a slow peripheral masks a fast one. The UART and SPI sensor are more forgiving, but they still have their own timing constraints.

I'd also raise the issue of interrupt priority and preemption. With a shared line, all three sources land in the same ISR, so you lose the ability to give the alarm input a higher priority than, say, a UART receive. In an RTOS that matters, because it affects whether a high-priority task can preempt a low-priority one promptly.

Then there's debuggability. A shared interrupt line makes it harder to tell, from a logic analyzer trace or a scope, which peripheral actually fired. In a regulated environment where you may need to demonstrate that the alarm path is deterministic, that's a real cost.

I wouldn't just say "no" — I'd ask the junior engineer to bring back a latency budget for each source and a proposed priority scheme, and then we'd decide together whether the pin savings justify the added complexity. Often the answer is that a small pin expansion or a different package solves the problem more cleanly, but the conversation is more productive if we evaluate it on the engineering merits rather than on seniority.

**Possible follow-ups:**
- How would you structure the ISR if the team decides to keep the shared line?
- What would you document in the design file to justify the decision either way?