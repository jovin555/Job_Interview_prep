# space-rad-hard — Day 76

## Q1: How would you approach designing a radiation-tolerant analog signal chain for a spacecraft instrument where the sensor output is a low-level differential signal, and both the amplifier front-end and the ADC reference can experience single-event transients (SETs)?

**Answer:** The core problem is that a low-level differential signal has very little amplitude margin, so even a brief transient on the front-end or the reference can corrupt a measurement that the control loop may act on before anyone notices. I'd start by separating the two failure paths — front-end SETs and reference SETs — because they need different mitigations.

For the front-end, the first line of defense is topology rather than parts: a true differential signal path with matched gain and a common-mode rejection stage rejects much of what a single-ended transient would inject. I'd add passive RC or LC filtering as close to the amplifier inputs as the signal bandwidth allows, sized so the filter corner is well above the signal of interest but low enough to attenuate the fast transient edge. Where the measurement is safety-critical, I'd consider a redundant or dual-path amplifier with a plausibility check between the two channels — if they disagree beyond a threshold, the reading is flagged rather than used. That's cheaper than trying to find an amplifier with guaranteed SET immunity, which is rarely available.

For the ADC reference, the key insight is that the reference is a DC node, so it can be heavily filtered without hurting signal bandwidth. I'd add a low-pass network at the reference pin, keep the reference trace short and well-decoupled, and consider a reference topology that recovers quickly from a transient. If the reference is shared across multiple channels, a single SET there corrupts all of them simultaneously, so I'd either give critical channels their own reference or add a comparison against an independent, slower reference to detect divergence.

The system-level mitigation that ties it together is temporal: sample, then validate before acting. A median-of-three or a rate-of-change plausibility check on the digitized value catches a single corrupted sample without needing the analog chain to be perfect. The trade-off is latency and complexity, so I'd reserve it for channels that actually feed a control action.

**Possible follow-ups:**
- How would you decide the filter corner frequency when the sensor signal itself has content close to the transient bandwidth you're trying to reject?
- If you add a redundant amplifier path for plausibility checking, how do you handle the case where both paths are corrupted by the same event?

## Q2: How would you approach selecting and qualifying a voltage supervisor or reset IC for a space-deployed system, given that most commercial parts are not radiation-characterized?

**Answer:** A voltage supervisor is deceptively critical — it's the part that decides whether the processor is allowed to run, so a supervisor that falsely asserts reset, or fails to assert when it should, can take down an otherwise healthy system. The challenge is that this is exactly the class of part where commercial vendors rarely publish radiation data, because the volumes don't justify it.

I'd start by defining what the supervisor actually has to do in this system: monitor which rails, with what threshold accuracy, with what reset pulse width, and does it need to hold reset through a brownout or a latch-up-induced overcurrent event. That definition tells me how much radiation performance I actually need versus how much is nice to have.

For qualification, I'd work through a tiered approach. First, look for any part with existing heavy-ion and TID data, even from a different grade or package — sometimes the die is the same and the data is transferable with caveats. Second, if no data exists, I'd assess the risk based on the part's function: a simple comparator-based supervisor with a bandgap reference has a different SET sensitivity profile than a microcontroller-based supervisor with internal state. Third, I'd plan a focused test campaign — TID to the mission dose with margin, and heavy-ion at the relevant LET threshold — rather than a full qualification, because budget rarely allows the full suite. If testing isn't feasible, I'd design around the uncertainty: add an independent watchdog or a second supervisor with a different topology so a single failure mode doesn't leave the system unsupervised.

The design-level mitigation matters as much as the part selection. I'd avoid relying on a single supervisor's threshold being accurate over TID, and I'd make sure the reset path itself is robust — a supervisor whose output driver degrades under dose is useless even if its threshold stays accurate.

**Possible follow-ups:**
- How would you structure a limited-budget radiation test for a supervisor to get the most decision-relevant data?
- If you use two supervisors with different topologies for diversity, how do you combine their outputs without creating a new single point of failure?

## Q3: You're reviewing a design for a space-deployed system that uses a COTS linear regulator to generate a 1.2V core voltage for an FPGA. The regulator's datasheet shows no radiation data, and the output voltage is specified as 1.2V ±2%. The FPGA requires 1.2V ±5% and draws up to 3A. How would you evaluate this choice and what alternatives would you recommend?

**Answer:** The first thing I'd flag is that the ±2% datasheet tolerance is a room-temperature, pre-rad number. It tells me nothing about how the regulator behaves after TID, and nothing about transient response to an SET on its internal reference or error amplifier. The FPGA's ±5% window sounds like it gives 3% of margin, but that margin is being consumed by things the datasheet doesn't cover: TID-induced reference drift, load transient response at 3A, and the FPGA's own tolerance to supply variation over its operating range.

I'd evaluate this in layers. First, what's the actual current profile — is 3A a steady-state number or a transient peak? A linear regulator at 3A with a 1.2V output is dissipating significant power, which raises thermal questions in vacuum independent of radiation. Second, what happens to the FPGA if the rail drifts to the edge of its window — does it fail gracefully or does it corrupt state? Third, is there any path to getting radiation data on this specific regulator, even a TID-only test, that would let me make a decision rather than guess?

For alternatives, I'd look at three directions. One is a rad-tolerant or rad-hard regulator with published data, accepting the cost and availability trade-offs. A second is a COTS regulator with a different topology that's inherently less sensitive — for example, one whose reference is external and can be a rad-hard reference, so the sensitive node is separated from the regulator itself. A third is a design-level mitigation: post-regulate with a rad-hard LDO, or add a voltage monitor that can detect an out-of-window condition and hold the FPGA in reset rather than letting it run on a marginal rail.

The recommendation I'd make depends on criticality. If this FPGA is doing housekeeping, the risk may be acceptable with monitoring. If it's in the control path, I'd push for a part with data or a topology that isolates the sensitive node.

**Possible follow-ups:**
- How would you evaluate the thermal feasibility of a 3A linear regulator in vacuum before worrying about its radiation performance?
- If you post-regulate with a rad-hard LDO, how do you handle the case where the upstream COTS regulator fails in a way that the LDO can't correct?

## Q4: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a poor fit for a radiation environment in some ways — it's single-ended, open-drain, and has no built-in error detection — but it's also ubiquitous and cheap, so the question is usually how to make it robust rather than whether to use it.

The failure modes I'd design against are: a corrupted data or address byte that a node misinterprets, a node that holds SDA or SCL low and locks the bus, and a node whose internal state machine gets stuck mid-transaction. These need different mitigations.

For data corruption, the protocol itself gives me almost nothing, so I'd add a layer above it: a checksum or CRC on every message, a sequence number so a node can detect a repeated or out-of-order message, and a defined behavior for what happens when a message fails validation — typically discard and request retransmission rather than act on suspect data. For critical commands, I'd consider a challenge-response or echo-back so the sender knows the receiver actually parsed the message correctly.

For bus lock-up, the standard recovery is clock stretching — the master toggles SCL up to nine times to flush any node stuck mid-byte, then issues a STOP. I'd build that into the master's firmware as an automatic recovery routine, not something an operator has to trigger. I'd also add a hardware watchdog on the bus itself: if no valid transaction completes within a timeout, the master resets the bus and re-enumerates.

For node-level faults, the key architectural decision is whether nodes can be individually isolated. If a node is stuck driving the bus, the only fix is to remove it, so I'd consider putting each node behind a bus switch or a series FET that the master can control. That adds complexity and cost, so I'd reserve it for nodes that are either high-risk or high-criticality.

The trade-off across all of this is latency and complexity. A CRC and retransmission scheme adds overhead to every transaction, which may not be acceptable for a high-rate sensor. I'd size the scheme to the criticality of the data — housekeeping telemetry can tolerate a simple checksum, while a control-loop input needs the full treatment.

**Possible follow-ups:**
- How would you handle the case where two nodes both try to recover the bus at the same time after a lock-up?
- If you add bus switches for isolation, how do you prevent the switch itself from becoming a single point of failure?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the technical question from the interpersonal one. The engineer has done real work, which means they've thought about the problem and probably have reasoning I should understand before I push back. If I lead with "this is under-margined," I've made it about my judgment versus theirs, and the review becomes a contest rather than a technical discussion.

So I'd start by asking them to walk me through their margin analysis — what they assumed, what data they used, and where they think the risk is. Often the disagreement turns out to be about a specific assumption rather than the whole approach. Maybe they used a room-temperature datasheet number where I'd want a worst-case-over-life number, or they assumed a derating factor that doesn't apply in vacuum. Naming the specific assumption makes the conversation concrete and gives them something to respond to that isn't just "I disagree."

If after that we still disagree, I'd try to reframe it as a shared question: what would have to be true for this design to be acceptable, and can we get evidence for that? That turns it into a testable proposition rather than a matter of opinion. Sometimes the answer is a focused test or analysis that resolves it. Sometimes the answer is that the evidence isn't available and we have to make a judgment call — in which case I'd be explicit that it's a judgment call, and that I'm making it based on the criticality of the function and the cost of being wrong.

Throughout, I'd keep the focus on the system rather than the person. "This function feeds a control loop, so the consequence of a marginal design is X" is different from "your design is risky." And I'd be open to being wrong — if they show me data I didn't have, I should update. The goal isn't to win the review, it's to make the right call and to keep the engineer engaged enough that they bring me the next problem early rather than late.

If we can't reach agreement and the decision is mine to make, I'd make it clearly and explain the reasoning, and I'd make sure the engineer knows their work was heard. A design review that ends with a decision the engineer disagrees with but understands is far better than one that ends with them disengaged.

**Possible follow-ups:**
- How would you handle it if the engineer's proposal had already been implemented and the schedule pressure made rework expensive?
- What would you do if you later found out the engineer was right and your concern was based on an outdated assumption?