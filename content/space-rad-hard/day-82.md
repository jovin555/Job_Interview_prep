# space-rad-hard — Day 82

## Q1: How would you approach designing a radiation-tolerant analog signal chain for a spacecraft instrument where the sensor output is a low-level differential signal, and both the amplifier front-end and the ADC reference can experience single-event transients (SETs)?

**Answer:** The core problem is that a low-level differential signal has very little amplitude margin, so any transient that couples into the front-end or shifts the reference is a large fraction of the measurement. I'd start by treating the two SET sources separately, because they need different mitigations.

For the amplifier front-end, the concern is a transient that either saturates the amplifier or produces a spurious output pulse. I'd look at the amplifier's transient recovery time and its behavior under a forced input step — parts that recover quickly and predictably are preferable to parts that latch or take a long time to settle. I'd also add passive filtering at the input to limit the bandwidth the transient can occupy, and consider whether the amplifier topology itself is inherently more or less sensitive (for example, a fully differential topology with good common-mode rejection helps reject common-mode transients). If the amplifier has no radiation data, I'd treat it as a risk item and plan either a targeted test or a design that tolerates its failure modes.

For the ADC reference, the concern is different: a transient on the reference shifts the conversion result for every channel, so it's a systematic error, not a per-channel one. I'd want a reference with good transient response and, ideally, radiation data. If that's not available, I'd add local decoupling sized to ride through short transients, and I'd consider a ratiometric or differential measurement scheme where the reference and the signal share the same disturbance, so it cancels. I'd also look at whether the system can detect a bad conversion — for example, by comparing against a redundant or slower reference path — and reject or flag it rather than acting on it.

The broader principle is that you can't always eliminate SETs in the analog chain, so you design for detection and graceful handling: filter what you can, make the measurement ratiometric where possible, and give the control loop a way to recognize and discard a corrupted sample rather than acting on it.

**Possible follow-ups:**
- How would you decide between adding a redundant reference path and simply adding more filtering and detection logic?
- If the sensor signal is time-sensitive and you can't retry a corrupted sample, how does that change your approach?

## Q2: You're reviewing a design for a space-deployed system that uses a COTS linear regulator to generate a 1.2V core voltage for an FPGA. The regulator's datasheet shows no radiation data, and the output voltage is specified as 1.2V ±2%. The FPGA requires 1.2V ±5% and draws up to 3A. How would you evaluate this choice and what alternatives would you recommend?

**Answer:** The first thing I'd note is that the ±2% initial tolerance is not the main problem — it's the absence of radiation data. A regulator with no radiation characterization has unknown behavior under TID and SEE, and for a core rail feeding an FPGA, that's a significant risk. TID can shift the reference and the error amplifier behavior, which directly moves the output voltage; a shift of even a few percent on top of the ±2% initial tolerance could push the rail outside the FPGA's ±5% window. And a single-event transient on the regulator's control loop could produce a glitch on the core rail, which is exactly the kind of event that can cause the FPGA to behave unpredictably.

So I'd evaluate it in two parts. First, the DC accuracy budget: initial tolerance plus temperature drift plus aging plus any radiation-induced shift has to stay inside ±5% with margin. With no radiation data, you can't close that budget — you'd be assuming zero radiation shift, which isn't a defensible assumption. Second, the transient behavior: a core rail with no radiation data gives you no basis for predicting how it responds to an SET, and the FPGA's core logic is sensitive to rail glitches.

For alternatives, I'd look at rad-tolerant or rad-hard LDOs or switching regulators with published TID and SEE data, even if they cost more or are larger. If a fully rad-hard part isn't available, I'd consider a topology that's inherently more tolerant — for example, a regulator whose output is post-filtered and monitored, with a voltage supervisor that can reset the FPGA if the rail goes out of spec. I'd also consider whether the FPGA can tolerate a slightly wider rail (some parts have wider core tolerances) and whether the system can afford a redundant regulator. The key point is that "no radiation data" is not the same as "no radiation problem" — it means the risk is unquantified, and for a core rail that's usually not acceptable.

**Possible follow-ups:**
- If a rad-hard regulator isn't available and the schedule is tight, what would you do to reduce the risk without changing the part?
- How would you test a COTS regulator to get enough confidence to use it, and what would you test for?

## Q3: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a good example of a bus that's simple and cheap but has failure modes that are awkward in a radiation environment. The two main concerns are data corruption and bus lock-up — a node that gets stuck holding SDA or SCL low can take down the whole bus.

For data corruption, the first line of defense is at the protocol level: use a checksum or CRC on every message, and have the receiver reject anything that fails. I²C's built-in ACK only tells you a byte was received, not that it was correct, so you need your own integrity check. I'd also add sequence numbers or timestamps so a receiver can detect a dropped or duplicated message, and I'd make the protocol idempotent where possible so a retry doesn't cause a double action.

For bus lock-up, the standard recovery is clock stretching or a bus recovery sequence: the master toggles SCL manually (as a GPIO) for a number of cycles to let the stuck slave release SDA, then issues a STOP condition to reset the bus state machines. I'd build that recovery into the master's firmware and trigger it on a timeout. I'd also consider whether the bus can be segmented — for example, using an I²C multiplexer so a fault on one segment doesn't take down the others — and whether critical nodes should have a separate bus or a redundant path.

Beyond that, I'd look at the physical layer: pull-up sizing, bus capacitance, and whether the bus is fast enough that a transient is more likely to be interpreted as a valid edge. Slower buses with good filtering are generally more robust. And I'd make sure the master has a way to detect a node that's misbehaving and isolate it — for example, by power-cycling that node's supply if it's on a switched rail.

The overall approach is: assume any single message can be corrupted, assume any node can lock the bus, and design the protocol and the recovery logic so the system can detect both and recover without human intervention.

**Possible follow-ups:**
- How would you decide between using an I²C multiplexer and giving critical sensors their own dedicated bus?
- What are the trade-offs of adding a CRC versus simply retrying a failed transaction?

## Q4: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt (SEFI) that puts the main processor into a state where it's still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** This is a nasty failure mode because the usual watchdog — "is the heartbeat toggling?" — is satisfied, so the system looks alive while it's actually not doing its job. The test plan has to specifically target that gap.

The first step is to define what "executing the control loop" actually means in observable terms. If the heartbeat is just a GPIO toggle, it's not a good proxy. I'd want a health metric that's tied to the control loop itself — for example, a counter that increments each time the loop completes, or a checksum over the loop's outputs, or a timestamp that's updated each iteration. The recovery mechanism should be based on that metric, not on the heartbeat.

For the test itself, since you can't inject real radiation on the ground, you need fault injection. I'd use a debugger or a test harness to force the processor into the stuck state — for example, by halting the control loop task while leaving the heartbeat task running, or by corrupting the loop's state so it spins without making progress. Then I'd verify that the recovery mechanism detects the condition and resets or restarts the loop within the required time. I'd repeat this across a range of injected states, because a SEFI could leave the processor in many different states, and the recovery needs to work for all of them.

I'd also test the recovery mechanism itself: what happens if the watchdog or supervisor is also affected? Does the system have a second layer — for example, an external supervisor that power-cycles the processor if the first-level recovery fails? And I'd test the boundary conditions: how long does recovery take, and does the system behave safely during that window?

Finally, I'd document the test as a repeatable procedure so it can be run on every firmware revision, because recovery logic is easy to break with unrelated changes.

**Possible follow-ups:**
- How would you design the health metric so it can't be satisfied by a stuck processor?
- If the processor is in a state where it's drawing excessive current, how does that change your recovery strategy?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves respect — the goal is to get to the right answer, not to win the argument. So I'd start by making sure I understand their reasoning: what assumptions did they make, what data did they use, and what margin did they calculate? Sometimes the disagreement is about a factual assumption (for example, the radiation environment or the part's behavior) rather than about the conclusion, and once that's on the table it's easier to resolve.

Then I'd make the margin explicit. If I think the design is under-margined, I'd walk through the budget — initial tolerance, temperature, aging, radiation, and any transient effects — and show where the margin disappears. If the engineer's analysis omitted a term, that's a concrete thing to discuss. If they included it but weighted it differently, that's a judgment call, and I'd want to understand why.

I'd also look for a way to test the disagreement rather than argue it. If the concern is a specific failure mode, can we characterize the part, run a test, or find data from a similar application? If the concern is a margin calculation, can we do a worst-case analysis together? Turning it into a shared technical question rather than a position makes it much easier to resolve.

If we still disagree after that, I'd fall back on the risk posture: for a space system, the cost of being wrong is high and the cost of extra margin is usually low, so the default should be to design to the conservative case unless there's a strong reason not to. I'd frame it that way — not "I'm overruling you" but "given the uncertainty, here's the margin we need to carry." And I'd make sure the engineer understands that the review process is about the design, not about them, and that raising concerns is expected.

Finally, I'd follow up: if we change the design, document why, so the decision is traceable and the engineer can see the reasoning. And if the engineer turns out to be right, say so — that builds the trust that makes the next disagreement easier.

**Possible follow-ups:**
- What would you do if the engineer's approach was actually correct but the review had already moved on?
- How would you handle it if the same engineer repeatedly proposed under-margined designs?