# protocols — Day 66

## Q1: How would you approach debugging an I2C bus where communication works reliably at 100 kHz but produces intermittent NACKs at 400 kHz, with the same devices and the same PCB?

**Answer:** The fact that the same hardware works at 100 kHz but not 400 kHz points strongly at a timing or signal-integrity margin issue rather than a logic or addressing bug, so I'd work from the physical layer upward.

First, I'd look at the bus rise time. I2C is open-drain, so the rising edge is set by the pull-up resistor charging the total bus capacitance. At 100 kHz there's plenty of time for the bus to settle before the clock samples it; at 400 kHz the window shrinks by 4×, and a slow rise time can mean the line hasn't reached the logic-high threshold when the receiver samples it — which can manifest as a spurious NACK or a corrupted bit. I'd measure the actual rise time on SDA and SCL with a scope at the worst-case point on the bus (usually the far end from the pull-up), and compare it against the fast-mode rise-time budget. If it's marginal, the fix is to reduce the pull-up resistance (subject to the sink-current limit of the weakest device) or reduce bus capacitance by shortening traces or removing stubs.

Second, I'd check whether the pull-up value was chosen for standard-mode assumptions. A resistor that gives a comfortable rise time at 100 kHz can be too weak at 400 kHz. I'd also verify the sink current at VOL for every device on the bus — lowering the resistor helps rise time but can violate the low-level output current spec of some slaves.

Third, I'd consider whether the NACKs correlate with specific transactions or devices. If only one device NACKs, it may be that device's own timing margin — some parts have a maximum clock frequency below 400 kHz, or need clock stretching that the master isn't honoring. I'd check whether the master respects clock stretching and whether the slave is actually stretching.

Finally, I'd look at noise and crosstalk: a faster clock has more high-frequency content, so a marginal layout that was fine at 100 kHz can couple noise into SDA/SCL at 400 kHz. I'd check for adjacent switching signals, ground return quality, and whether the bus is referenced cleanly.

The general principle: when a bus works at one speed and fails at a higher one with identical hardware, treat it as a margin problem — rise time, setup/hold, sink current, or noise — and measure rather than guess.

**Possible follow-ups:**
- How would you decide between lowering the pull-up resistor versus reducing bus capacitance?
- What scope setup would you use to capture a marginal rise time on an I2C bus?

## Q2: You're designing a half-duplex RS-485 link where the driver-enable and receiver-enable must switch at exactly the right moment, and the turnaround budget is tight. How would you approach this?

**Answer:** Half-duplex RS-485 turnaround is fundamentally a timing and state-machine problem, and the risk is that if the driver is enabled too early or disabled too late, two nodes drive the bus simultaneously and corrupt data, or the bus floats and picks up noise.

I'd start by defining the turnaround budget explicitly: the time from "last byte shifted out of the UART" to "driver disabled," plus the time for the line to settle, plus the time for the receiver to be enabled and the first start bit to be detected. Each of those has a worst-case number, and the sum has to fit inside the protocol's allowed gap.

On the transmit side, the key subtlety is that the UART's "transmit complete" flag (shift register empty) is not the same as "last bit has physically left the pin." I'd use the transmit-complete interrupt, not the transmit-buffer-empty interrupt, to trigger driver disable — otherwise the last byte gets truncated. Even then, I'd add a small guard delay to account for driver disable time and line settling, and I'd verify that delay against the transceiver datasheet rather than assuming.

On the receive side, I'd enable the receiver as soon as the driver is disabled, and I'd make sure the firmware doesn't start looking for a start bit until the line has settled — otherwise a reflection or the tail of the previous transmission can be misinterpreted as a start bit. Some designs add a brief idle-time check before accepting a new frame.

I'd also consider the failure modes: what happens if the software crashes mid-transmission with the driver enabled? That's a bus-lockup hazard, so I'd add a hardware or watchdog-based mechanism to force the driver to the disabled (high-impedance) state. And I'd make the turnaround timing a single tunable constant with margin, documented, rather than scattering magic delays through the code.

Finally, I'd verify it on a scope: measure the actual driver-enable-to-first-bit and last-bit-to-driver-disable timing across temperature and across several boards, because transceiver propagation delays vary.

**Possible follow-ups:**
- How would you handle a node that needs to respond within a very short window after receiving a frame?
- What would you do if the transceiver's enable/disable times are not well specified in the datasheet?

## Q3: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol does not have a built-in backpressure mechanism?

**Answer:** If the protocol has no backpressure mechanism, the first question is whether I can add one at a layer I control, because retrofitting flow control into a fixed protocol is much harder than designing it in.

If hardware flow control (RTS/CTS) is available on both ends and the connector has spare pins, that's the cleanest solution: the receiver deasserts RTS when its buffer is near full, and the transmitter pauses. The catch is that RTS/CTS only helps if the transmitter actually honors it, and it adds latency — the transmitter may have already sent a byte or two after the receiver deasserted, so the receiver's buffer needs headroom for that in-flight data.

If hardware flow control isn't possible, I'd consider software flow control (XON/XOFF) only if the payload is text-like and I can guarantee the escape characters never appear in data — which is rarely true for binary medical payloads, so I'd usually reject it.

If neither is possible, the practical approach is to make the receiver fast enough that it never overflows: use DMA to move bytes out of the UART FIFO into a ring buffer without CPU intervention, size the ring buffer for the worst-case burst, and make sure the interrupt or DMA-completion handling is bounded. I'd also look at whether the receiver's processing can be decoupled — parse frames in a lower-priority task rather than in the ISR.

If overflow still happens, I'd define a deterministic recovery: detect the overrun flag, discard the partial frame, resynchronize on the next frame boundary, and count the event. In a medical context, silently dropping bytes is unacceptable, so the protocol needs a way to detect that a frame was lost — a sequence number or a CRC that will fail — and the application needs a defined response.

The honest answer is that a protocol without backpressure is a design gap, and the right long-term fix is to add one; the short-term fix is to make overflow impossible by design and detect it if it happens.

**Possible follow-ups:**
- How would you size the receive ring buffer for a worst-case burst?
- What are the risks of using XON/XOFF with binary data?

## Q4: In a system where an SPI master talks to several slaves at different clock speeds and with different CPOL/CPHA modes, how would you approach structuring the firmware so that mode and speed changes are handled safely?

**Answer:** The core problem is that SPI mode and clock speed are properties of the transaction, not of the bus, so the firmware has to reconfigure the master between transactions and guarantee that no slave is left selected or mid-transaction when the configuration changes.

I'd structure this as a bus abstraction with per-device configuration. Each slave gets a descriptor that includes its chip-select line, its CPOL/CPHA mode, its maximum clock speed, and its word size. A transaction function takes a device handle, applies that device's configuration to the SPI peripheral, asserts its chip select, transfers, deasserts, and returns. The application never touches the SPI registers directly.

The safety concerns are: first, never change mode or speed while a chip select is asserted or a transfer is in progress — the peripheral must be idle. Second, ensure the chip select is deasserted before reconfiguring, and that there's a defined idle state. Third, if the bus is shared, serialize access with a mutex or a single-owner task so two devices can't interleave transactions.

I'd also think about the cost of reconfiguration. Changing CPOL/CPHA and prescaler on every transaction adds overhead and can glitch the clock line if not done carefully. Some peripherals require disabling the SPI block before changing mode. If the overhead matters, I'd group transactions by device and batch them, or use separate SPI peripherals for devices with incompatible modes if the MCU has them.

For CPOL/CPHA specifically, I'd verify the idle clock level matches the mode before asserting chip select, because some slaves interpret a clock edge during the idle-to-active transition as a bit. And I'd make sure the chip-select timing meets each slave's setup and hold requirements relative to the first and last clock edge.

Finally, I'd make the configuration table the single source of truth and test each device individually at its rated speed before testing them together, because the failure mode of a mode mismatch is usually a silent data corruption rather than an obvious error.

**Possible follow-ups:**
- How would you handle a slave that requires a different word size or bit order?
- What would you do if two slaves on the same bus have overlapping chip-select timing requirements?

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** The first priority is to separate the technical problem from the people problem, and to handle both without making the situation worse.

Technically, I'd want to understand exactly what's wrong and how deep it goes. Is it a localized bug in one message handler, or is the protocol implementation structurally wrong — wrong framing, wrong error handling, wrong state machine? That determines whether the fix is a patch or a redesign. I'd get the failing test case reproduced outside the compliance lab as quickly as possible, because debugging in a regulatory test environment is slow and expensive. Then I'd assess the blast radius: does the error affect only the failing test, or does it invalidate other tests that already passed? In a medical context, I'd also need to consider whether the issue affects the risk analysis or the design history file, because a protocol error that could affect safety-critical data has regulatory implications beyond the test itself.

On the people side, I'd avoid framing it as blame. Compliance testing is exactly where subtle protocol errors surface, and a junior engineer discovering this under test pressure is a normal part of the learning curve — the failure is usually in the review process, not the individual. I'd look at why the error wasn't caught earlier: was there no protocol conformance test before compliance testing? Was the design reviewed against the spec? Was the junior engineer given enough context about the protocol requirements? Those are process gaps I own as much as anyone.

Practically, I'd do three things: contain the schedule impact by communicating early and honestly with stakeholders about the delay and the recovery plan; fix the immediate issue with the junior engineer involved so they learn from it rather than being sidelined; and add a pre-compliance protocol test step so the next issue is caught before it reaches the lab.

The follow-up I'd expect from a good interviewer is whether I'd change how the team works, and the answer is yes — the lesson is that protocol correctness needs to be verified against the spec before regulatory testing, not during it.

**Possible follow-ups:**
- How would you decide whether to patch the existing implementation or rewrite it?
- What would you add to the design review process to catch protocol errors earlier?