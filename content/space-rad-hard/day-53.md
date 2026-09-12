# space-rad-hard — Day 53

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd treat this as three separable problems — source selection, fault isolation, and inrush management — and make sure the design doesn't let one compromise the others.

For source selection, the two 28V feeds should be combined through an ORing scheme rather than a hard parallel tie. Ideal-diode controllers or ORing FETs give you reverse-current blocking and let either feed carry the load alone if the other drops out or faults. A key detail is that the ORing element must be able to interrupt fault current, not just block reverse flow — otherwise a short on one feed can drag the shared rail down before any protection acts.

For fault isolation, each feed gets its own protection stage: a fuse or eFuse with a defined I²t curve, plus a current-limit loop that holds the load in a bounded current rather than letting it collapse the bus. The current limit has to be set above the worst-case legitimate inrush but below the level that would disturb the other feed. For latch-up-prone loads, a latching current limit with a retry or latch-off policy is usually preferable to a simple foldback, because foldback can leave a latched load sitting in a low-current state that never trips the fuse.

For hot-swap, the concern is the inrush into the downstream bulk capacitance when a board is inserted or a feed is re-enabled. A hot-swap controller with a controlled dV/dt ramp, plus a SOA-aware pass FET, keeps the inrush within the FET's safe operating area and prevents a bus sag that the other feed's loads would see. I'd also add a bleed path so the bulk caps discharge predictably, and make sure the hot-swap controller's fault timer is long enough to ride through legitimate startup but short enough to protect the FET.

The cross-cutting point is that the two feeds must be genuinely independent — separate protection, separate ORing elements, no shared node that a single fault can short. I'd verify that with a fault-injection test matrix: short each feed, latch each load, hot-swap each board, and confirm the other feed and the downstream loads stay within spec.

**Possible follow-ups:**
- How would you decide between a latching current limit and an auto-retry scheme for a load that might latch up repeatedly?
- What would you look for in an ORing controller's datasheet to confirm it can actually clear a fault, not just block reverse current?

## Q2: How would you approach derating and part selection for a space-deployed board, and how does derating interact with the radiation tolerance you're trying to achieve?

**Answer:** Derating and radiation tolerance are two separate margins that have to be managed together, because they can work against each other if you treat them independently.

Derating is about staying well inside a part's specified limits so that wear-out mechanisms, parameter drift, and transient stresses don't push it out of spec over the mission. Typical practice is to derate voltage to something like 70–80% of rated, current to 70–80%, junction temperature to a margin below the absolute maximum, and power dissipation similarly. The exact numbers depend on the program's derating standard, but the principle is consistent: you're buying margin against the things the datasheet doesn't fully capture.

Radiation tolerance adds a second axis. A part might be comfortably derated electrically but still fail TID because its parametric drift under irradiation eats the margin you thought you had. So the two have to be evaluated together: if a part's TID data shows its threshold voltage shifting by some amount, that shift has to be subtracted from the electrical margin before you decide the derating is adequate. Similarly, a part that's derated hard on voltage might still be vulnerable to SEL if the derating doesn't address the latch-up trigger condition.

In practice I'd build a selection matrix with columns for electrical derating, TID margin, SEE sensitivity (SEU/SEL/SEFI), and package/thermal constraints, and I'd reject any part that fails on any axis rather than trying to trade one against another. For parts with no radiation data, the honest answer is that you either characterize them, use them only in non-critical functions with mitigation, or don't use them. Derating doesn't substitute for radiation data — it's a separate margin that has to be satisfied on its own.

**Possible follow-ups:**
- How would you handle a part that passes electrical derating and TID but has no SEL data?
- Where does derating stop being useful and start being a way to avoid characterizing a part?

## Q3: How would you approach designing a fault-tolerant communication bus for a space-deployed system where multiple sensor nodes must reliably report data to a central controller, and single-event upsets (SEUs) can corrupt individual messages?

**Answer:** I'd start by separating the problem into message integrity, node liveness, and bus arbitration, because SEUs can attack all three and each needs a different defense.

For message integrity, the baseline is a CRC strong enough to catch the error patterns you expect, plus a sequence number or timestamp so the controller can detect dropped, duplicated, or reordered messages. A CRC alone catches corruption but not a message that's been replaced wholesale, so a sequence number and a length field matter. For critical values, I'd consider sending the data redundantly — either the same value twice in separate frames, or a value plus its complement — so the controller can vote or cross-check. The cost is bandwidth, so this is reserved for the parameters that actually feed control actions.

For node liveness, each node needs a heartbeat or periodic status message, and the controller needs a timeout that declares a node dead if it stops reporting. The tricky part is distinguishing "node is dead" from "node is alive but its messages are being corrupted" — a node that's sending garbage still looks alive on a heartbeat. So the controller should track both heartbeat presence and message validity rate, and escalate if either degrades.

For bus arbitration, SEUs can corrupt the arbitration phase itself, causing collisions or a node to grab the bus incorrectly. A deterministic, time-slotted scheme (TDMA-style) is more robust here than a contention-based one, because each node has a fixed slot and a corrupted arbitration can't cause a collision — at worst it causes a missed slot, which the controller can detect. If the bus is shared and a node can lock it up (a stuck-dominant fault on a differential bus, for example), I'd add bus recovery logic: detect the lock-up, force the bus idle, and re-initialize.

Finally, I'd make the protocol fail-safe rather than fail-silent: if the controller loses confidence in a node's data, it should flag that value as invalid and either use a last-known-good value with a staleness flag or drop into a safe state, rather than acting on a corrupted reading.

**Possible follow-ups:**
- How would you decide between a time-slotted bus and a contention-based one for a given node count and update rate?
- What would you do if a node's messages pass CRC but the values are implausible — how do you distinguish an SEU from a real sensor fault?

## Q4: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** The argument conflates two different things: TMR protects against upsets in the digital logic that processes a value, but it does nothing for an upset that corrupts the value before it ever reaches the digital domain. If the analog front-end produces a wrong reading — because an SET hit the amplifier, the ADC reference, or the sample-and-hold — TMR on the downstream logic will faithfully replicate and vote on the wrong number. Redundancy downstream of a single point of failure doesn't remove that failure.

So the first thing I'd do is walk through the analog chain and ask, for each stage, what a single-event transient would do and whether anything downstream would catch it. The sensor itself is usually the least susceptible, but the amplifier, the ADC input, and especially the ADC reference are all candidates. An SET on the reference is particularly nasty because it shifts every conversion during the transient, and a control loop acting on that could command a wrong output.

Then I'd look at what mitigations are actually available and proportionate. Options include: a redundant ADC channel with comparison or voting; a reference with its own monitoring or a second reference used as a sanity check; analog filtering or a median filter in firmware to reject single-sample transients; and a plausibility check that rejects readings outside a physically expected range before they reach the control loop. The right combination depends on how fast the control loop is and how much a wrong value costs — a slow loop can afford to filter and retry, a fast one may need hardware redundancy.

The key point I'd make in the review is that "the digital side has TMR" is not a reason to leave the analog side single-ended; it's a reason to check whether the analog side's failure modes are actually covered by something else. If they aren't, the design has a gap that TMR elsewhere doesn't fill.

**Possible follow-ups:**
- How would you decide whether a plausibility check in firmware is sufficient, or whether you need a redundant analog channel?
- What's the difference in mitigation strategy between an SET on the ADC reference and an SET on the amplifier input?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the technical question from the interpersonal one. The engineer has done real work, and that deserves to be acknowledged before anything else — starting with "this is wrong" puts them on the defensive and makes it harder to reach a good decision. So I'd open by asking them to walk through their reasoning and the assumptions behind it, and I'd listen for where the margin actually comes from.

Then I'd try to make the disagreement concrete rather than abstract. "Under-margined" is a judgment; the useful version is a specific scenario — a particular radiation event, a particular parameter drift, a particular worst-case condition — where the design's margin is consumed. If I can point to that scenario and show the numbers, the conversation becomes about the scenario, not about who's right. If I can't point to it, that's a signal I might be wrong, and I should be open to that.

I'd also try to find out whether we're disagreeing about facts or about risk tolerance. Sometimes the engineer has data I don't have, and the right move is to update. Sometimes we agree on the facts but disagree on how much margin is enough, and that's a decision that should be made against the program's requirements and standards, not by whoever argues hardest. If the program has a derating standard or a radiation margin requirement, that's the tiebreaker.

If we still disagree after that, I'd escalate the decision rather than force it — bring in a second reviewer or the responsible engineer, and document the disagreement and the rationale. That protects both of us and makes sure the decision is made on the merits. And throughout, I'd keep the tone on the design, not the person: the goal is a board that works, and the engineer's confidence is an asset as long as it's pointed at the right problem.

**Possible follow-ups:**
- What would you do if the engineer's data turned out to be correct and your concern was unfounded?
- How would you handle it if the same engineer repeatedly proposed under-margined designs?