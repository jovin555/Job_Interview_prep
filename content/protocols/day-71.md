# protocols — Day 71

## Q1: How would you approach debugging an I2C bus where a slave device holds SDA low after a transaction, preventing any further communication until power is cycled?

**Answer:** This is the classic "stuck bus" condition, and the first step is to distinguish between two root causes: a slave that is mid-transaction and waiting for clocks it never receives (for example, the master reset mid-byte), versus a slave that has genuinely latched into a bad state. On a scope or logic analyzer, I'd confirm that SDA is held low while SCL is idle high — that pattern points to a slave holding the line, not a master.

The standard recovery is clocking the bus manually: temporarily reconfigure SCL as a GPIO, toggle it up to nine times while SDA is released, and watch for the slave to finish its byte and release SDA. If it does, issue a proper STOP condition (SDA low→high while SCL is high) to resynchronize the bus state machine, then re-init the peripheral. If nine clocks don't free it, the slave is likely in a latched fault state and only a targeted reset (a dedicated reset GPIO, or a power-cycle of that rail) will recover it.

For a medical device, the more important question is what happens in the field. I'd want the firmware to detect the stuck condition (SDA low with no active transaction), attempt the clocking recovery automatically, and if that fails, reset the offending device and log the event. I'd also look at *why* it happens — a master reset mid-transaction, a missing STOP, or a slave with a marginal timing spec — because recovery without root cause just hides a recurring fault.

**Possible follow-ups:**
- How would you implement the GPIO-based clock recovery in firmware without disturbing other devices on the same bus?
- Would you add a hardware watchdog or bus isolator, and what are the trade-offs?

## Q2: In a system where an SPI master talks to several slaves at different clock speeds and with different CPOL/CPHA modes, how would you approach structuring the firmware so that mode and speed changes are handled safely?

**Answer:** The core risk is that SPI mode and clock rate are properties of the *transaction*, not the bus, so any code path that changes them must guarantee no other transfer is in flight and that the change is applied before the chip select asserts. I'd structure this as a per-device descriptor — each slave has a struct holding its CPOL, CPHA, max clock, and CS line — and a single transfer function that takes that descriptor, reconfigures the peripheral, asserts CS, runs the transfer, deasserts CS, and returns. Application code never touches the SPI registers directly.

The subtle parts: first, mode changes on many MCUs require the peripheral to be disabled and re-enabled, which can glitch the clock line — so the sequence has to be done with CS deasserted and the bus idle. Second, if the bus is shared, you need a mutex or a single-owner scheduler so two tasks can't interleave a mode change with another device's transfer. Third, I'd keep the fastest device's settings as the default and only reconfigure when switching to a slower or differently-clocked device, to minimize churn.

On Zephyr, this maps naturally onto the SPI device model where each `spi_config` carries its own frequency and mode, and the driver handles the reconfiguration — but I'd still verify the driver's behavior on mode changes with a scope, because not all vendor drivers handle CPOL/CPHA switching cleanly.

**Possible follow-ups:**
- What would you check on a scope to confirm the mode change isn't producing a spurious clock edge?
- How would you handle a device that needs a mode change *within* a single logical transaction?

## Q3: You're debugging a CAN-FD network where a node intermittently enters error-passive state and then recovers on its own, with no obvious pattern. How would you approach this?

**Answer:** Error-passive means the node's transmit error counter has crossed 128, so the node is still able to communicate but must respect a longer intermission and can no longer send active error flags. The fact that it recovers on its own tells me the counter is decrementing successfully on good frames — so the errors are bursty, not a hard fault. That points toward a marginal physical layer or a timing/bit-rate mismatch rather than a dead transceiver.

I'd start by capturing the error counters and the error types (bit error, stuff error, CRC error, form error, ACK error) over time. The *type* of error narrows the cause fast: ACK errors suggest the node is transmitting but nobody is acknowledging — possibly a bit-rate mismatch or a node that's offline. Bit errors and stuff errors point to signal integrity: reflections from improper termination, stub length, or a sample-point mismatch between nodes. CRC errors on receive suggest the same physical issues or a node with a slightly different oscillator.

For CAN-FD specifically, I'd check the data-phase bit rate and sample point separately from the arbitration phase, because the two phases can have different timing requirements and a mismatch in the data phase only shows up on longer frames. I'd also verify termination at both ends, measure the differential signal at the problem node with a scope, and check whether the errors correlate with bus load or with a specific other node transmitting. If it correlates with one node, that node's transceiver or clock is suspect.

**Possible follow-ups:**
- How would you use the error counters and the node's error state machine to distinguish a physical-layer problem from a protocol problem?
- What would you change in the network if you found the sample points were mismatched across nodes?

## Q4: How would you approach implementing flow control on a UART link where the receiver occasionally cannot keep up with the transmitter, but the protocol has no built-in backpressure mechanism?

**Answer:** If the protocol has no backpressure, I have three levers: add hardware flow control, add software flow control, or change the buffering and scheduling so the receiver never falls behind. The right choice depends on whether I control both ends and whether the link is a bottleneck by design.

Hardware flow control (RTS/CTS) is the cleanest if the lines are available — the receiver deasserts RTS when its buffer crosses a high-water mark, and the transmitter pauses. The catch is that it only works if the transmitter honors it, and it adds two wires. Software flow control (XON/XOFF) works over a two-wire link but is fragile: the escape characters can collide with binary payload data, so it's only safe if the payload is constrained or escaped. If neither is possible, I'd increase the receiver's ring buffer and make sure the ISR drains the FIFO promptly, then move the heavy processing out of the ISR into a task so the UART isn't starved.

The deeper fix is to look at *why* the receiver stalls — a blocking operation in the receive path, a task priority inversion, or a burst that exceeds the buffer. In a medical device I'd also want a defined behavior when the buffer does overflow: drop the frame and flag it, rather than silently corrupting a partial message, because a half-received patient data frame is worse than a dropped one.

**Possible follow-ups:**
- How would you size the receive buffer given a known burst length and processing latency?
- What are the risks of XON/XOFF in a link that carries binary sensor data?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single UART with a software-based protocol multiplexer to communicate with four different sensors, each with different baud rates and protocols. The hardware engineer argues this is unreliable and wants four separate UART peripherals. How would you guide the team to a decision?

**Answer:** I'd frame it as a requirements question first, not a preference question. The key facts are: what are the four baud rates, what's the worst-case latency each sensor can tolerate, and is any of them safety-critical or time-sensitive? A software multiplexer that switches baud rate between transactions is workable *if* the sensors are polled slowly and none of them has a hard real-time deadline — but it's fragile, because every baud change has to be synchronized with the sensor's idle state, and a missed transition corrupts the next frame.

I'd ask the junior engineer to show the timing budget: how long each transaction takes, how often each sensor must be read, and what the worst-case latency is when all four are serviced in sequence. If the budget is comfortable and the sensors are tolerant, the single-UART approach can be acceptable, with the caveat that the multiplexer must be robust — explicit idle detection, a defined recovery if a sensor doesn't respond, and no baud change while a frame is in flight. If the budget is tight, or any sensor is safety-critical, the hardware engineer is right and the extra UARTs are cheap insurance.

The decision framework I'd push is: determinism and fault isolation versus pin count and cost. Four UARTs give independent, deterministic links and isolate a fault on one sensor from the others; one UART saves pins but couples all four sensors' reliability together. For a medical device, I'd lean toward the hardware engineer's position unless the requirements clearly show the single-UART approach meets every deadline with margin — and I'd want that margin documented, not assumed.

**Possible follow-ups:**
- How would you verify the software multiplexer's robustness if the team did choose the single-UART approach?
- What would you do if the MCU didn't have four UART peripherals available?