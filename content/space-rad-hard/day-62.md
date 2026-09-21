# space-rad-hard — Day 62

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd treat this as three separate problems that share one architecture: source selection, fault isolation, and inrush management.

For source selection, the two 28V feeds should be ORed in a way that prevents a fault on one from dragging down the other. A simple diode-OR works but wastes headroom and dissipates heat; an ideal-diode (active ORing) controller gives lower loss and, importantly, lets you monitor and report which feed is active. The ORing stage needs to be upstream of any shared bulk capacitance, otherwise a short on one feed can discharge the shared reservoir into the fault.

For fault isolation, each downstream load branch should have its own current-limiting or e-fuse stage with a defined trip threshold and a latch-off or retry behavior. The key design decision is whether a latched load should auto-retry or stay off until commanded — for a payload where an unpowered branch is safer than a repeatedly retried one, latch-off with telemetry is usually the right call. The e-fuse also needs to be sized so that its trip threshold is above the legitimate inrush of its own load but below the current the upstream bus can deliver into a hard short.

For hot-swap, the concern is the inrush into the branch's input capacitance when a load is inserted or a feed is switched in. That's controlled with a slew-rate-limited gate drive on the pass FET plus a defined dV/dt, so the bus sees a controlled current ramp rather than a step. You also want to make sure the ORing controller and the e-fuse don't fight each other during a feed transition — sequencing and hysteresis matter.

Throughout, I'd be thinking about single-event effects on the control logic itself: the ORing controller and e-fuse controller are active devices, and a SET on their enable or gate-drive logic could momentarily misbehave. Where the consequence is severe, I'd want either a rad-tolerant controller or a discrete, passive-dominant implementation that degrades gracefully.

**Possible follow-ups:**
- How would you decide between latch-off and auto-retry for a latched load, and what telemetry would you want to distinguish a real fault from a transient?
- If the two 28V feeds come from the same upstream source, does the redundancy actually buy you anything, and how would you verify that?

## Q2: How would you approach selecting and qualifying a voltage supervisor or reset IC for a space-deployed system, given that most commercial parts are not radiation-characterized?

**Answer:** I'd start by being honest about what the part actually has to do, because that determines how much radiation risk I can tolerate. A voltage supervisor's job is to hold reset until the rail is valid and to assert reset if the rail drops — so its failure modes are false reset (annoying but recoverable) and failure to reset (potentially catastrophic if the processor is in a bad state). The second failure mode is the one that drives the qualification effort.

For selection, I'd look first at whether a rad-tolerant or rad-hard supervisor exists that meets the threshold accuracy and timing I need. If not, I'd consider whether the function can be built from discretes — a comparator with a reference and an RC delay — because discrete implementations let me choose each element for radiation behavior and add redundancy where it matters. A single COTS supervisor with no data is a single point of failure for a safety-critical reset.

For qualification, if I have to use a COTS part, I'd want at minimum: TID data to the mission dose with margin, SEL immunity or a current-limited supply that survives a latch-up, and some sense of SET behavior on the reset output. If the vendor has no data, I'd budget for a focused test campaign — TID at a cobalt-60 source and heavy-ion or proton for SEE — rather than assume. The test plan should exercise the part at the rail voltages and temperatures it will actually see, because supervisor thresholds drift with both.

I'd also design the board so the supervisor isn't the only reset path: an external watchdog with a different failure mode, and a commandable reset from the processor itself, give diversity. The supervisor is one layer, not the whole strategy.

**Possible follow-ups:**
- How would you test a supervisor's SET behavior on the reset output without a full heavy-ion campaign?
- What derating would you apply to a supervisor's threshold accuracy over the mission lifetime, and why?

## Q3: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** I'd separate the argument into two claims and address them independently, because they're not the same point.

The first claim is that TMR on the digital side protects the analog measurement. It doesn't. TMR protects against upsets in the digital logic that processes the measurement; it does nothing about an SET in the amplifier, a drift in the ADC reference, or a corrupted sample-and-hold. If the analog front-end produces a wrong value, TMR will faithfully replicate and vote on the wrong value. The digital redundancy is downstream of the failure, so it can't catch it.

The second claim is that a single-ended chain is adequate. That depends on the criticality of the measurement and the failure modes. A single-ended chain is more susceptible to common-mode noise and ground shifts, and it has no way to detect a stuck or drifted front-end. For a measurement that feeds a control loop, I'd want at least one of: a differential front-end to reject common-mode, a second independent measurement path for cross-checking, or a plausibility check in firmware that flags out-of-range or inconsistent values. The cheapest of these is usually the plausibility check, but it only catches gross failures.

The constructive way to handle this in review is to ask the engineer to walk through the failure modes of the analog chain and show where each is detected. If the answer is "the digital TMR catches it," that's the gap to close. I'd frame it as "the digital side is well-covered; let's make sure the analog side has its own detection," which keeps the review about the design rather than about the person.

**Possible follow-ups:**
- What plausibility checks would you add in firmware to catch a drifted analog front-end, and what would you do when a check fails?
- How would you decide whether a second analog path is worth the cost versus accepting the risk with a documented rationale?

## Q4: How would you approach designing a fault-tolerant communication bus for a space-deployed system where multiple sensor nodes must reliably report data to a central controller, and single-event upsets (SEUs) can corrupt individual messages?

**Answer:** I'd think about this at three layers: the physical bus, the message format, and the protocol behavior.

At the physical layer, the bus needs to be robust to a node that's been upset into a bad state — for example, a node that holds the bus low and blocks everyone else. That argues for a bus with collision detection and a way to isolate a misbehaving node, or for a star topology where the controller can disable a branch. A shared multi-drop bus with no isolation means one upset node can take down the whole network.

At the message layer, every message needs a checksum or CRC strong enough to catch the corruption patterns you expect, plus a sequence number or timestamp so the controller can detect dropped or reordered messages. A CRC alone tells you a message is bad; it doesn't tell you whether you missed one. For critical data, I'd also consider a redundant transmission or a request/response with acknowledgment, so a single corrupted message doesn't silently become a missing measurement.

At the protocol layer, the controller needs a defined behavior when a node stops responding or starts sending garbage: retry a bounded number of times, then mark the node as failed and either use a redundant node or degrade gracefully. The protocol should also have a way to reset a node that's been upset — a commandable reset or a watchdog on the node itself — so recovery doesn't require a full system reset.

Throughout, I'd be thinking about the difference between a transient error (retry is fine) and a persistent one (the node is stuck and needs a reset). The protocol should distinguish them, and the controller should have telemetry on both so ground can see what's happening.

**Possible follow-ups:**
- How would you design the bus so that a node stuck driving the bus low can be isolated without a full system reset?
- What CRC polynomial and message structure would you choose, and how would you justify the choice against the expected error patterns?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is make sure I actually understand the engineer's reasoning before I push back. Confidence usually comes from somewhere — maybe they've found data I haven't seen, or they've made an assumption I disagree with but haven't articulated. So I'd ask them to walk through the margin calculation and the assumptions behind it, and I'd listen for the specific point where our models diverge.

Once I've found that point, I'd try to make the disagreement concrete rather than abstract. "I think this is under-margined" is hard to resolve; "you've assumed the converter's worst-case output is 3.3V, and I think we need to use the datasheet max of 3.47V" is a specific, checkable claim. If we can agree on the inputs, the conclusion usually follows. If we can't agree on the inputs, that's the real conversation — and it's often a question of what the mission's radiation environment actually is, which is a documentable fact rather than an opinion.

I'd also separate the technical question from the decision. Sometimes the right answer is "your analysis is correct, and the risk is acceptable given the mission profile." Sometimes it's "your analysis is correct, and the risk isn't acceptable, so we need a different part." The engineer's job is to make the analysis sound; my job as lead is to own the risk decision. Being clear about that division keeps the review from becoming a contest of confidence.

Finally, I'd make sure the outcome is documented — what we decided, why, and what would change the decision. That protects the engineer (their analysis is on record) and the project (the rationale is traceable if the assumption turns out to be wrong).

**Possible follow-ups:**
- What would you do if the engineer's analysis is sound but you still believe the risk is too high, and they disagree with your risk call?
- How would you handle it if the same engineer repeatedly under-margins designs — is that a coaching issue or a selection issue?