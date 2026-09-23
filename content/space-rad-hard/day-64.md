# space-rad-hard — Day 64

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd start by treating the two feeds as genuinely independent sources that are only combined at the point of load, rather than tying them together at a single node. The architecture I'd reach for is an ORing scheme — either ideal-diode controllers or ORing FETs — so that a fault on one feed is isolated and the other continues to carry the load. The key design decisions are: (1) making the ORing elements fast enough to limit reverse current during a latch event, (2) sizing the downstream holdup capacitance so the load rides through the brief interval while the faulted feed is disconnected, and (3) ensuring the ORing control logic itself is single-fault tolerant, since a failure there defeats the whole point.

For hot-swap, the concern is inrush into the downstream bulk capacitance when a feed is inserted or reconnected. I'd use a hot-swap controller with a controlled dV/dt ramp on the pass FET gate, plus a current-limit loop that folds back rather than hard-latches, so a transient inrush doesn't trip the feed offline. I'd also add a soft-start that's independent of the ORing logic, so a hot-swap event on one feed can't glitch the other.

For latch-up survival specifically, the protection has to act faster than the latch can damage the part. That means per-load current limiting or e-fuses downstream of the ORing stage, so a latched load is disconnected locally rather than dragging the shared rail down. I'd also think about whether the fault should be latched off or auto-retried — for a payload, auto-retry with a bounded number of attempts is usually preferable to a permanent latch-off, but that's a mission-level decision.

Throughout, I'd be thinking about derating: the ORing FETs, the hot-swap controller, and the current-sense elements all need margin for TID-induced parameter drift over the mission, not just the initial datasheet values.

**Possible follow-ups:**
- How would you decide between ideal-diode controllers and simple ORing diodes, and what does that choice do to your efficiency and thermal budget?
- If the two feeds come from the same spacecraft bus, how does that change your fault-isolation assumptions?

## Q2: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** I'd separate the argument into two claims and address them independently. The first claim is that TMR on the digital side protects the analog measurement. It doesn't — TMR protects against upsets in the redundant logic itself, but it can't detect or correct a corrupted input. If the ADC presents a wrong value to all three TMR lanes, all three lanes agree on the wrong answer, and the voter faithfully passes it through. TMR only helps if the fault is inside the replicated logic, not upstream of it.

The second claim is that the analog chain doesn't need redundancy because it's "just" a sensor and an amplifier. That's where I'd push back with specifics: single-event transients on the amplifier output, on the ADC reference, or on the sample-and-hold can produce a spurious reading that looks valid to the digital side. A single-ended chain has no way to distinguish a real signal from an SET-induced spike. And a single-ended topology is more susceptible to ground-bounce and common-mode noise coupling than a differential one, which matters in a mixed-signal space board.

What I'd recommend depends on the criticality of the measurement. For a control-loop input, I'd want at least one of: a differential front-end with a matched reference, a plausibility check in firmware (rate-of-change limits, cross-checks against a redundant sensor), or a second independent measurement path. The cheapest effective mitigation is usually the firmware plausibility check, because it catches both SET-induced spikes and genuine sensor faults. If the measurement is safety-critical, I'd argue for a genuinely independent second path — different sensor, different amplifier, different ADC channel — so a common-mode fault in one path can't fool both.

The framing I'd use with the engineer is: TMR is a technique for a specific class of fault (logic upsets), not a general-purpose reliability strategy. You have to match the mitigation to the fault mode, and the analog front-end has different fault modes than the digital logic.

**Possible follow-ups:**
- How would you design the plausibility check so it doesn't reject legitimate fast transients in the measured signal?
- If you add a second analog path, how do you decide which one to trust when they disagree?

## Q3: How would you approach designing a radiation-tolerant current-sense circuit for a spacecraft power bus, where the sense resistor itself is exposed to radiation and its value may drift over the mission lifetime?

**Answer:** The core problem is that any current-sense scheme depends on a reference element — a shunt resistor, a Hall sensor, a current transformer — and if that element's characteristics drift with TID or displacement damage, the measurement drifts with it, silently. So the first thing I'd do is pick a sensing technology whose drift mechanism I understand and can bound.

For a shunt-based approach, the resistor itself is usually the most radiation-stable element in the chain — metal-foil and some thin-film resistors hold value well under TID — but the amplifier that measures the voltage across it is the weak point. A precision difference amplifier or current-sense amplifier can exhibit input offset drift, gain drift, and increased input bias current under TID, and some bipolar-input parts show enhanced low-dose-rate sensitivity (ELDRS) that makes them worse at low dose rates than at high ones. So I'd select the amplifier for radiation characterization, not just initial precision, and I'd derate its offset and gain specs for end-of-life.

For the topology, I'd use a Kelvin-connected shunt to keep the sense points out of the high-current path, and I'd keep the shunt value high enough that the sense voltage is well above the amplifier's offset drift, but low enough that the shunt's own power dissipation and self-heating don't cause a thermal drift that masquerades as a radiation effect. That's a real trade-off — a bigger shunt gives better signal-to-noise but more self-heating.

For the drift itself, I'd build in a calibration path. If the system has a known reference load or a calibration current source, the firmware can periodically re-zero the offset and re-scale the gain, which cancels slow TID-induced drift. That doesn't help with SETs, which are fast and transient, so I'd also add a plausibility filter — a rate-of-change limit or a median filter — to reject single-sample spikes. And I'd consider a redundant sense element with a different technology (e.g., a shunt plus a Hall sensor) so that a common-mode drift in one technology doesn't go undetected.

Finally, I'd be honest about what can't be calibrated out: if the shunt resistor itself drifts, no amount of amplifier calibration recovers the true current. So I'd either choose a shunt technology with characterized radiation stability, or I'd accept the drift and budget for it in the system's current-measurement accuracy requirement.

**Possible follow-ups:**
- How would you distinguish a genuine overcurrent event from an SET-induced spike in the sense amplifier, given that both look like a fast transient?
- If you can't find a radiation-characterized current-sense amplifier, what's your fallback?

## Q4: How would you approach selecting and qualifying a voltage supervisor or reset IC for a space-deployed system, given that most commercial parts are not radiation-characterized?

**Answer:** I'd start by being clear about what the supervisor actually has to do, because that determines how much radiation risk I can tolerate. A supervisor that holds the processor in reset until the rail is valid is a fairly benign function — if it trips early or late by a few tens of millivolts, the system still boots. A supervisor that's part of a fault-recovery path, where a missed reset means the processor stays hung, is much more critical. So the first step is classifying the function.

For a commercial part with no radiation data, I'd work through the failure modes systematically. TID: what's the total dose at the part's location, and does the vendor have any TID data at all, even from a different package or grade? Many commercial parts have some TID data available from the manufacturer or from published tests, even if it's not in the datasheet. If the part is bipolar-based, I'd specifically ask about ELDRS, because a part that survives 100 krad at high dose rate can fail at 10 krad at low dose rate.

SEE: for a supervisor, the relevant events are SETs on the comparator or reference (causing a spurious reset or a missed reset), SEUs in any internal registers or trim, and SEL. A spurious reset is usually recoverable; a missed reset is the dangerous one. I'd look at the part's internal architecture — a simple comparator-and-reference supervisor with no digital state is much less susceptible to SEU than one with internal registers or a digital interface.

For qualification, if the part is critical and I can't get vendor data, I'd budget for a focused radiation test — heavy-ion or proton for SEE, cobalt-60 or a proton beam for TID. That's expensive, so I'd prioritize: test the parts that are on the critical path, and for the rest, use a conservative derating approach and add system-level mitigation (e.g., an external watchdog that's independent of the supervisor).

The other option is to design around the problem: use a supervisor topology that's inherently radiation-tolerant — a discrete comparator with a rad-hard reference, or a rad-hard supervisor if one exists in the right package and voltage range. That's often more expensive in board area but avoids the qualification burden.

**Possible follow-ups:**
- How would you structure a limited radiation test campaign to get the most confidence per dollar?
- If the supervisor is the only thing holding the processor in reset, how do you protect against a supervisor failure that leaves the processor running with an invalid rail?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves respect — if I come in with "this is wrong," I've made it about them, and the review stops being about the design. So I'd start by asking them to walk me through their reasoning: what margin did they assume, where did that number come from, and what failure mode were they protecting against. Often the gap is in the assumptions, not the analysis, and hearing their assumptions out loud is the fastest way to find it.

Once I understand their reasoning, I'd frame my concern as a question rather than a verdict. "What happens to this design if the part drifts by X over the mission?" or "How does this behave under a single-event transient on that node?" That lets them engage with the technical issue directly, and if they have an answer I hadn't considered, I learn something. If they don't, the gap becomes visible without me having to declare it.

If we still disagree after that, I'd move to evidence. Can we find radiation data for the part? Can we run a quick test? Can we look at how a similar design fared in a comparable environment? The goal is to make the decision rest on data rather than on seniority. If the data isn't available and the risk is real, I'd make the call as the lead — that's my job — but I'd explain the reasoning clearly and document it, so the decision is traceable and the engineer understands why.

Throughout, I'd keep the tone collaborative. The engineer isn't wrong to have proposed the design; they're wrong about the margin, and that's a fixable thing. I'd also make sure to acknowledge what's good about their work — if the topology is sound and only the margin is off, say so. That keeps the review focused on the design and preserves the working relationship, which matters more than winning the argument.

**Possible follow-ups:**
- What would you do if the engineer's approach was actually correct and your concern was based on an outdated assumption?
- How would you handle it if the same engineer repeatedly under-margined designs, and the one-on-one conversations weren't changing the pattern?