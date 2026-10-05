# protocols — Day 76

## Q1: How would you approach debugging a UART link where the receiver reports framing errors only when a high-current load (e.g., a motor or heater) switches on the same board?

**Answer:** Framing errors that correlate with a high-current switching event point strongly at a physical-layer disturbance rather than a protocol or firmware bug, so I'd start by separating "the UART logic is wrong" from "the UART logic is being lied to by the electrical environment."

First, I'd characterize the failure precisely: is the error a true framing error (stop bit not seen at the expected time), a noise-induced false start bit, or a receiver overrun that the driver reports as framing? Scoping the RX line at the receiver pin while the load switches is the single most informative step — I'd look for ground bounce, a glitch that crosses the logic threshold, or a brief loss of the reference that shifts the sampling point. If the disturbance is on the ground or supply rail rather than the signal itself, that reframes the whole investigation toward return-path and decoupling issues.

From there I'd work through the usual suspects in order of likelihood: shared ground return impedance between the switching load and the UART transceiver (a classic cause of apparent signal corruption when nothing is wrong with the signal trace itself); inadequate local decoupling on the transceiver or the MCU's UART supply pin; the switching node capacitively coupling into a long or poorly referenced RX trace; and, less commonly, the load's switching transient pulling the transceiver's supply below its minimum and causing it to mis-sample. I'd also confirm the UART's oversampling and any digital glitch filter are actually enabled — sometimes the fix is partly configuration.

Mitigations follow the diagnosis: separate or star-ground the return paths so load current doesn't flow under the UART, add or improve local bulk and high-frequency decoupling, shorten and reference the RX trace (or route it away from the switching node), and consider a small RC or ferrite on the offending coupling path if it's genuinely radiated. I'd verify with the same scope setup that triggered the original failure, and I'd want the fix validated across the load's full switching range, not just one operating point.

**Possible follow-ups:**
- How would you tell the difference between a ground-bounce problem and a genuine signal-integrity problem on the RX line?
- If the disturbance only appears at certain load currents, how would you structure the test matrix to find the threshold?

## Q2: How would you approach designing a protocol abstraction layer so that application code can talk to sensors over I2C, SPI, UART, or CAN-FD without knowing which transport is underneath?

**Answer:** The goal is to keep the application's vocabulary about *what* it wants (read a temperature, set a gain, stream samples) completely separate from *how* those bytes travel. I'd structure it in layers with a narrow, transport-agnostic interface at the top.

At the top, I'd define a sensor-facing API in terms of operations and data, not registers or bus transactions — something like `read_measurement()`, `configure(channel, gain)`, `subscribe(callback)`. This layer knows nothing about I2C addresses or CAN identifiers.

Below that, a transport interface with a small, uniform set of primitives: open/close, a read/write or transfer call, and an error/status model. Each physical transport (I2C, SPI, UART, CAN-FD) implements this interface. The key design decision is making the error model uniform — a NACK, a CRC failure, a timeout, and a bus-off condition should all surface to the layer above in a consistent way, otherwise the abstraction leaks and the application starts branching on transport type, which defeats the purpose.

Above the transport sits a per-sensor driver that knows the device's actual protocol (register map, command framing, timing requirements) and uses the transport interface to execute it. This is where device-specific quirks live — a sensor that needs a delay after a config write, or one that only supports a particular transfer size.

Two things I'd be deliberate about. First, timing and determinism: some transports have very different latency and jitter characteristics, so if the application has real-time requirements, the abstraction needs a way to express them (or the application needs to be written so it doesn't assume uniform timing). Second, testability: because the transport interface is narrow, I can substitute a mock or a loopback transport and test the sensor driver and application logic without hardware, which is a large practical win.

I'd resist over-abstracting. If only one transport will ever be used, a full abstraction layer is premature. The value appears when you genuinely have multiple transports or expect to swap one, and the cost is an extra indirection and a discipline requirement to not let transport details leak upward.

**Possible follow-ups:**
- How would you handle a transport-specific feature (like CAN-FD's larger payload) without breaking the abstraction?
- Where would you put retry logic — in the transport layer or the sensor driver — and why?

## Q3: You're debugging a CAN-FD network where a node intermittently enters error-passive state and then recovers on its own, with no obvious pattern. How would you approach this?

**Answer:** Error-passive is the controller telling you it has accumulated enough transmit or receive errors to distrust itself, and the fact that it recovers on its own means the error condition is transient rather than a hard fault. So the investigation is about finding what's intermittently corrupting frames on that node's view of the bus.

I'd start by getting the error counters and error state transitions logged with timestamps — transmit error counter (TEC) and receive error counter (REC), plus which error type is incrementing (bit, stuff, CRC, form, ACK). The *type* of error is the biggest clue. A rising REC with CRC or form errors suggests the node is misreading frames that other nodes send fine, which points at the node's own receiver path, sampling point, or bit-timing configuration. A rising TEC with ACK errors suggests the node's transmissions aren't being acknowledged, which points at arbitration, bit-rate mismatch, or a physical issue on that node's transmit path.

Common root causes I'd work through: a bit-timing/sample-point mismatch between nodes (especially at CAN-FD data-phase rates, where the sample point is far more sensitive); a marginal physical layer on that specific node — bad termination, a long stub, a poor connector, or a transceiver that's marginal at the data-phase rate; ground potential differences between nodes causing common-mode issues; and, less often, a firmware issue where the node transmits at the wrong moment or with a malformed frame.

Because it's intermittent, I'd want to correlate the error events with bus activity — is it worse under high load, at a particular temperature, after a specific node transmits, or when a particular cable is moved? I'd also check whether the problem follows the node (swap it to a different bus position) or follows the bus position (swap a known-good node into that spot). That single experiment often separates "this node is bad" from "this location/cable is bad."

Mitigations depend on the finding: correct the bit-timing configuration and sample point, fix termination or stub length, improve grounding, or replace a marginal transceiver. I'd validate by running the network under the load and conditions that previously triggered the errors and confirming the error counters stay clean.

**Possible follow-ups:**
- How would you determine the correct sample point for the data phase, and why does it differ from the arbitration phase?
- If the error counters rise on multiple nodes simultaneously, what would that tell you?

## Q4: How would you approach choosing between a star topology and a daisy-chain topology for a multi-drop sensor network in a medical device, given that the sensors are physically distributed?

**Answer:** The choice is really driven by the electrical characteristics of the physical layer, the cable routing constraints, and the failure behavior you can tolerate — not by topology preference in the abstract.

For a differential bus like RS-485 or CAN, the standard guidance is a linear daisy-chain (bus) topology with short stubs, because the bus relies on controlled impedance and proper termination at the two ends. A star topology creates multiple branches, each of which is effectively a stub; long stubs cause reflections and impedance discontinuities that degrade signal integrity, especially at higher bit rates. So if the physical layer is RS-485 or CAN and the sensors are distributed along a cable run, daisy-chain is usually the right answer, with the sensors tapped off as close to the main line as possible.

A star can make sense when the physical layer tolerates it — for example, point-to-point links from a central hub to each sensor (each sensor on its own dedicated link), or when the distances are short and the bit rate is low enough that reflections don't matter. Star also has an operational advantage: a fault on one branch doesn't take down the others, and it's easier to isolate a single misbehaving node. The trade-off is more cable, more transceivers at the hub, and higher cost and complexity.

So my approach would be: identify the physical layer and its constraints first. If it's a shared differential bus, default to daisy-chain with proper termination and minimal stubs, and design the mechanical routing so the cable naturally passes each sensor. If the sensors are physically arranged such that a daisy-chain would require long back-and-forth runs, or if per-node fault isolation is a hard requirement, then evaluate a star or a hybrid (a hub with short point-to-point links) and check whether the bit rate and distances keep reflections manageable. I'd also factor in serviceability — in a medical device, being able to replace or isolate one sensor without disturbing the rest of the network can matter as much as the electrical trade-off.

**Possible follow-ups:**
- How would you handle a situation where the physical layout forces a star but the protocol is RS-485?
- What termination strategy would you use if the topology ends up being a hybrid?

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** The first priority is to stabilize the situation and protect the project, then understand how it happened, then fix the process so it doesn't recur — in that order. Blame is not useful and actively harmful here; the engineer is almost certainly already aware and stressed, and the team needs them engaged in the fix, not defensive.

Concretely, I'd start by getting a clear, shared understanding of the defect: what exactly is wrong, what the correct behavior should be, and what the regulatory impact is. Compliance testing failures have a specific character — they may require a formal deviation, a re-test, and documentation — so I'd loop in the regulatory/quality lead early to understand the process obligations, not just the technical fix. I'd also assess whether the failure is isolated to this one protocol or whether it hints at a broader gap (e.g., the same misunderstanding applied elsewhere).

On the schedule side, I'd be transparent with stakeholders quickly rather than hoping to absorb the delay. I'd present the technical root cause, the corrective action, the re-test plan, and a realistic revised timeline. Trying to hide or minimize a compliance delay usually makes it worse.

For the root cause of *how it happened*, I'd look at the system rather than the individual: was the protocol specification ambiguous or incomplete? Was there a review that should have caught it? Was there a test that should have exercised this path earlier? In my experience, a defect that survives to compliance testing usually means the verification was too shallow or the requirements weren't precise enough — those are process issues I own as much as the engineer does. I'd strengthen the review checklist and add targeted pre-compliance testing so this class of error is caught earlier next time.

With the engineer specifically, I'd have a private conversation focused on learning and support, not punishment, unless there's evidence of negligence or repeated disregard — in which case it becomes a performance conversation handled separately and appropriately. The public message to the team is about the fix and the process improvement, not about who made the mistake.

**Possible follow-ups:**
- How would you decide whether to add a formal review gate versus relying on better testing?
- If the same engineer made a similar mistake again, how would your approach change?