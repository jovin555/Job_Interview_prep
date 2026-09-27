# protocols — Day 68

## Q1: How would you approach debugging an I2C bus where a slave device holds SDA low after a transaction, preventing any further communication until power is cycled?

**Answer:** This is the classic "stuck bus" condition, and the first thing to establish is whether the slave is genuinely holding SDA low or whether the master's own pin is latched. I'd start by scoping SDA and SCL at the moment of failure: if SDA is held low while SCL is idle high, the slave is stuck mid-transaction — typically because it was interrupted (a glitch, a reset, a clock edge it missed) while driving an ACK or a data bit, and it never saw the ninth clock that would have released it. If instead SDA is low and SCL is also being pulled low by the master, the problem is on the controller side, often a peripheral left in a bad state after an error interrupt.

Assuming it's the slave, the standard recovery is clocking: the master reconfigures SCL as a GPIO, toggles it up to nine times at a safe rate, and watches for SDA to release. Once SDA goes high, the master issues a STOP condition to return the bus to idle. This works because the slave's internal shift register only needs the missing clock edges to complete its byte and release the line. The important design point is that this recovery must be built into the driver as a bounded, deterministic routine — not an infinite loop — and it should be attempted before declaring the bus failed.

Beyond the immediate fix, I'd want to understand *why* it happened, because a stuck bus that recovers is still a latent defect in a medical device. Common root causes are: a slave that doesn't tolerate clock stretching from another device, a marginal pull-up that lets SDA rise too slowly at the bus's fastest edge, a glitch on SCL during a hot-plug event, or a slave whose own reset is asynchronous to the bus. I'd also check whether the master's timeout is shorter than the slowest slave's worst-case response — if the master abandons a transaction mid-byte, it can leave the slave mid-byte too. Adding a bus-recovery state machine plus a periodic bus-health check (idle-line verification before each transaction) is usually the right firmware-level mitigation.

**Possible follow-ups:**
- How would you distinguish a stuck slave from a master-side peripheral lockup without a scope?
- What pull-up and rise-time considerations would reduce the likelihood of this happening in the first place?

## Q2: In a system where an SPI master talks to several slaves at different clock speeds and with different CPOL/CPHA modes, how would you approach structuring the firmware so that mode and speed changes are handled safely?

**Answer:** The core risk is that SPI mode and clock changes are not atomic with respect to an in-flight transaction — if you reconfigure the peripheral while a transfer is still shifting out, you can corrupt the current frame or leave a slave mid-byte. So the firmware architecture should make "reconfigure" a deliberate, serialized operation rather than something any caller can do at any time.

I'd structure it around a small SPI bus abstraction that owns the peripheral. Each slave gets a descriptor containing its CPOL, CPHA, max clock, word size, and chip-select line. A transaction API takes the slave descriptor, and the bus layer does the following in order: assert the correct chip select, apply the mode and clock settings, run the transfer, then deassert chip select and return the peripheral to a safe idle state. The key is that mode/clock changes happen *only* between transactions, never during one, and the bus layer is the single writer of those registers. If the RTOS is involved, I'd guard the bus with a mutex so two tasks can't interleave a reconfiguration with someone else's transfer.

There are a couple of subtleties worth calling out. First, some MCU SPI peripherals require the enable bit to be cleared before CPOL/CPHA can be changed, which means you must ensure the peripheral is idle and the FIFO is drained — otherwise you can drop bytes. Second, changing CPOL mid-idle can generate a spurious clock edge on SCL, which some slaves interpret as a bit; the safe pattern is to set the mode while chip select is deasserted and the clock is in its idle state for that mode. Third, if a slave shares the bus with a device that needs a much slower clock, you can't just run everything at the fastest rate — you either reconfigure per transaction or accept the slower rate. I'd document the per-slave constraints in the descriptor so the bus layer enforces them rather than relying on callers to remember.

**Possible follow-ups:**
- How would you handle a slave that requires a delay between chip-select assertion and the first clock edge?
- What would you do if two slaves on the same bus had incompatible requirements that couldn't be reconciled by reconfiguration alone?

## Q3: How would you approach detecting and recovering from a UART break condition, and why does break detection matter in a medical device protocol?

**Answer:** A break condition is when the receive line is held in the space (low) state for longer than a full character frame — longer than start bit plus data plus parity plus stop. Most UART peripherals have a dedicated break-detect flag that fires when this happens, distinct from a framing error, because a framing error is a single malformed character while a break is a sustained line condition. The distinction matters: a framing error usually means a baud mismatch or noise on one byte, whereas a break is a deliberate or fault-induced line state that often signals something structural — a disconnected cable, a powered-down peer, or a protocol-level reset signal.

For detection, I'd enable the break interrupt (or poll the flag) and treat it as a first-class event rather than lumping it in with generic receive errors. On the recovery side, the correct behavior depends on what the break means in the protocol. In many designs a break is used as a synchronization or reset marker — the receiver flushes its partial frame buffer, resets its state machine to "waiting for start," and optionally signals the application that the link was reset. If the break persists, that's a hard fault: the line is stuck low, which in a medical device could mean a cable has been pulled or a peer has lost power. The firmware should then transition the link to a defined safe state rather than continuing to read garbage.

Why it matters in a medical context: a UART link that silently absorbs a break and keeps parsing can end up interpreting noise as valid data, or worse, treating a disconnected sensor as still reporting. Break detection gives you an explicit, early signal that the physical link has changed state, which feeds directly into the device's fault-handling and alarm logic. I'd also make sure the break handling is bounded and testable — inject a break in a test harness and verify the receiver flushes, resyncs, and reports the event within a defined time.

**Possible follow-ups:**
- How would you distinguish a break from a baud-rate mismatch that produces a run of framing errors?
- What would you do if the break condition clears but the peer never resumes transmitting?

## Q4: You're debugging a CAN-FD network where a node intermittently enters error-passive state and recovers on its own, with no obvious pattern. How would you approach this?

**Answer:** Error-passive means the node's transmit error counter has crossed 128, so it can still participate but must wait longer before transmitting and can no longer send active error frames. The fact that it recovers on its own tells me the error counter is oscillating around the threshold — successful transmissions decrement it, failures increment it — which points to an intermittent physical or timing issue rather than a hard fault. I'd approach it in layers.

First, capture the error counters and the error state transitions over time, ideally with a bus analyzer that timestamps frames and error frames. I want to know *which* error type is incrementing the counter: bit errors, form errors, stuff errors, or ACK errors. That single piece of information narrows the search enormously. ACK errors point to a node that isn't acknowledging — possibly a node that's powered but not yet initialized, or one whose receiver is marginal. Bit errors point to signal integrity: reflections, marginal termination, or a stub that's too long for the data-phase bit rate. Stuff errors and form errors often point to a node transmitting at the wrong bit rate or with a mismatched sample point.

Second, I'd look hard at the bit-rate and sample-point configuration across all nodes. CAN-FD has separate arbitration-phase and data-phase bit rates, and if two nodes disagree on the sample point — even if they agree on the nominal bit rate — they'll produce intermittent errors that depend on bus length and propagation delay. This is a very common cause of exactly the symptom described: works most of the time, fails when a particular node transmits at a particular point in the bus timing.

Third, I'd check the physical layer against the data-phase bit rate. CAN-FD's higher data rate shortens the bit time, which makes bus length, termination, and stub length far more critical than in classic CAN. A network that's fine at 500 kbit/s arbitration can fail intermittently in the 2–5 Mbit/s data phase if the topology wasn't designed for it. I'd verify termination at both ends, measure the actual differential signal at the worst-case node, and check for stubs longer than the data-phase budget allows.

Finally, I'd consider whether the error-passive node is the victim or the cause. If it's the only node going error-passive, it may have a marginal transceiver or a bad connection. If multiple nodes do it, the problem is likely shared — bus topology, termination, or a misconfigured node polluting the bus.

**Possible follow-ups:**
- How would you determine the correct sample point for a given bus length and bit rate?
- What would you change in the network design if the data-phase bit rate simply can't be supported by the existing topology?

## Q5: Imagine you're leading a design review where a junior engineer proposes using a single shared interrupt line for three different peripherals — a UART, an SPI sensor, and a GPIO alarm input — arguing that it saves pins and the firmware can just poll the peripherals to find out which one fired. How would you guide the team to evaluate this approach?

**Answer:** I'd start by acknowledging the legitimate motivation — pin count is a real constraint, and sharing an interrupt line is a recognized technique. The question isn't whether it's allowed, it's whether the *polling-to-disambiguate* strategy is compatible with the timing requirements of each peripheral. So I'd steer the review toward that: what is the worst-case latency each of these three sources can tolerate, and what does the shared-line approach do to that latency?

The UART is usually the most demanding, because it has a hardware FIFO that will overflow if you don't service it in time, and the overflow threshold is a hard deadline. The SPI sensor may be less time-critical if it's polled or if its data is buffered, but if it's an alarm or a data-ready signal, it may have its own deadline. The GPIO alarm input is the one I'd scrutinize hardest in a medical device — an alarm input that's delayed by a polling loop is a safety concern, and the whole point of an interrupt is to guarantee a bounded response. If the shared-line scheme means the alarm handler has to wait for the UART handler to finish polling, you've introduced a coupling between unrelated subsystems that's hard to reason about and hard to test.

I'd also raise the failure modes. With a shared line, a stuck-low peripheral can mask all the others — the ISR fires continuously, and if the disambiguation logic isn't robust, you can starve the real source. And the polling itself consumes CPU time in the ISR, which is exactly the kind of thing that's fine at bench load and problematic at worst-case load. In a medical device, I'd want the interrupt architecture to be analyzable: each source with a defined worst-case latency, and no source able to block another.

The guidance I'd give the team is: if pin count truly forces a shared line, then the disambiguation must be fast and deterministic (read a status register, not poll each peripheral in turn), the highest-priority source must be identifiable first, and the design must be validated under worst-case simultaneous load. But if the alarm input is safety-related, I'd push hard to give it its own line, because the cost of a pin is trivial compared to the cost of an unbounded alarm latency. The decision should come out of the timing analysis, not out of the pin budget alone.

**Possible follow-ups:**
- How would you structure the shared ISR so that the highest-priority source is always serviced first?
- What test would you run to prove the shared-line design meets its worst-case latency under simultaneous events?