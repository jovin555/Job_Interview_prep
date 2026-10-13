# space-rad-hard — Day 84

## Q1: How would you approach designing a radiation-tolerant analog-to-digital conversion subsystem where the ADC's voltage reference is a COTS part with no radiation data, and the measurement must hold accuracy over a multi-year mission?

**Answer:** The reference is usually the accuracy bottleneck in any precision acquisition chain, so I'd start by treating "no radiation data" as an unknown risk rather than a zero risk. First I'd characterize what the mission actually needs: what absolute accuracy and drift budget the measurement requires, and how much of that budget the reference is allowed to consume. Then I'd look for whatever partial data exists — total ionizing dose curves, ELDRS sensitivity, single-event transient behavior — even if it's from a similar process node or a sibling part, because process-level behavior often transfers better than part-level datasheets suggest.

Architecturally, I'd avoid making a single uncharacterized reference the sole source of truth. Options include: using a rad-tolerant reference if one exists within the accuracy budget; ratio-metric conversion where the reference and the signal share the same excitation so drift partially cancels; periodic in-flight calibration against an on-board transfer standard or a known internal reference; and redundancy, where two references are compared and a disagreement flags the measurement as suspect. I'd also add monitoring — a dedicated ADC channel that watches the reference voltage itself, so drift becomes observable telemetry rather than a silent error.

On the layout side, I'd keep the reference thermally and electrically quiet: its own filtered supply, guard traces, and physical separation from switching regulators. For the single-event transient concern, I'd add a small RC or active filter on the reference output and, if the measurement is time-critical, a sample-and-hold or median-of-N acquisition so a transient spike doesn't propagate into a control action. Finally, I'd write the risk into the test plan: if the budget allows, a low-dose-rate or proton test on the reference alone is far cheaper than testing the whole board, and it converts an unknown into a number.

**Possible follow-ups:**
- How would you decide between a ratio-metric architecture and an absolute-reference architecture for a given sensor type?
- If the reference drifts slowly over the mission, how would your calibration routine distinguish drift from a real change in the measured quantity?

## Q2: You're reviewing a design where a junior engineer has proposed using a single commercial LDO with no radiation data to post-regulate a critical analog rail, arguing that the upstream DC-DC is already rad-tolerant so "the LDO doesn't matter." How would you evaluate this argument?

**Answer:** The argument has a kernel of truth — the upstream converter does most of the heavy lifting for bulk regulation and isolation from the bus — but it conflates "the upstream is rad-tolerant" with "the downstream is therefore protected." The LDO sits directly in the analog signal path, and its behavior under radiation is what the ADC and front-end actually see. So I'd separate the concerns.

First, what failure modes matter for an LDO in this position? Total ionizing dose can shift the bandgap reference and the error amplifier, changing the output voltage over mission life — that's a slow drift that a calibration routine might catch but that also eats accuracy budget. Single-event transients on the pass transistor or control loop can produce output glitches that couple straight into the analog rail. Single-event latch-up in the LDO itself can drag the rail down or draw excessive current. And enhanced low-dose-rate sensitivity is a real concern for linear bipolar parts, where the damage at low dose rate can be worse than at the high dose rates used in qualification testing.

So my evaluation would be: does the LDO's output tolerance, over the mission's TID and temperature range, still leave margin for the analog chain? If the answer is "we don't know because there's no data," that's the problem — not the topology. Mitigations I'd consider: choose a rad-tolerant or rad-hard LDO if one fits the current and noise budget; add a downstream filter and a voltage monitor so drift and transients are observable; add current limiting and latch-up protection on the rail; and if the part must stay, budget a focused radiation test on the LDO alone, which is cheap relative to testing the whole assembly.

The framing I'd use with the engineer is: "You're right that the upstream converter protects the LDO from the bus. The question is what protects the analog chain from the LDO." That reframes it as a shared problem rather than a disagreement about whether the LDO "matters."

**Possible follow-ups:**
- How would you distinguish an LDO's TID-induced drift from a temperature effect during ground testing?
- If the LDO is the only part in the chain without radiation data, how would you prioritize testing it against other unknowns?

## Q3: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is attractive for sensor fan-out because it's simple and cheap, but it's also fragile in ways that radiation makes worse. The two failure modes I'd design against are data corruption (a bit flip in a transaction) and bus lock-up (a node holding SDA low, or a clock stretch that never releases, blocking the whole bus).

For data corruption, the first layer is protocol-level integrity: every transaction carries a CRC or checksum, and the master validates before acting on the data. I²C's built-in ACK is not sufficient — it only confirms a device responded, not that the payload is correct. I'd also add sequence numbers or timestamps so a stale or duplicated read is detectable, and I'd make writes idempotent where possible so a retry doesn't cause a double action.

For lock-up, the classic mitigation is a bus recovery routine: the master toggles SCL manually (typically nine clocks) to flush a stuck slave, then issues a STOP condition. That routine should be automatic and triggered by a timeout, not left to a human. Beyond that, I'd consider bus isolation — segmenting the bus with a mux or buffer so one stuck node can be electrically isolated rather than taking down the whole bus. If a node is non-critical, that's straightforward; if it's critical, the isolation has to be paired with a redundant path or a degraded-mode strategy.

I'd also think about the physical layer: pull-up sizing, bus capacitance, and whether the bus is single-ended (which I²C is) and therefore more susceptible to noise coupling. In a mixed-signal space board, I'd keep the I²C routing away from switching regulators and high-speed digital, and consider differential I²C extenders or a different bus (like CAN-FD or RS485) if the environment is noisy enough that single-ended signaling is a liability.

Finally, I'd make the bus observable: log transaction errors, lock-up events, and recovery attempts as telemetry, so the ground can see whether the bus is degrading over mission life.

**Possible follow-ups:**
- How would you decide between adding bus isolation and simply moving to a differential bus like RS485 or CAN-FD?
- If a critical sensor is on the shared bus and the bus locks up, what does your degraded-mode strategy look like?

## Q4: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** This is really three problems layered together: input redundancy, fault isolation, and inrush/hot-swap control. I'd design them as separate stages so each can be reasoned about and tested independently.

For input redundancy, the goal is that either 28V feed can power the payload alone, and a fault on one feed doesn't propagate to the other. The classic approach is ORing diodes or, more efficiently, ideal-diode controllers (active ORing) that use a MOSFET plus a controller to emulate a diode with much lower loss. The key requirement is reverse-blocking: if one feed shorts or sags, the ORing element must prevent current from flowing backward into the faulted feed. I'd also add per-feed current sensing and a fault flag so the system knows which feed failed.

For fault isolation on the load side, each load or load group gets its own protection — a fuse, an e-fuse, or a current-limiting switch — so a shorted or latched load trips only its own branch. The trip threshold and response time need to be chosen so normal inrush doesn't false-trip but a real fault is cleared before it drags the bus down. For latch-up specifically, the protection has to be able to interrupt the fault current and, ideally, power-cycle the affected load to clear the latch, rather than latching off permanently.

For hot-swap and inrush, the concern is that plugging in a load with bulk capacitance looks like a momentary short to the bus. I'd use a hot-swap controller with a controlled slew rate on the pass FET, plus a dV/dt limit or current limit during startup, so the inrush is bounded. The controller also needs to handle the case where the load is already faulted at plug-in — it should trip rather than try to power a short.

Across all three, I'd add telemetry: per-feed voltage and current, per-branch fault status, and hot-swap event counters. That turns the power system from a black box into something the ground can diagnose. And I'd derate everything for the vacuum thermal environment, since conduction-cooled components run hotter than their datasheet conditions assume.

**Possible follow-ups:**
- How would you set the current-limit threshold and response time so normal inrush doesn't trip the protection but a real fault does?
- If one feed fails and the payload runs on the remaining feed, how would you decide whether to shed non-critical loads?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves respect — the goal of the review is to get the right answer, not to win an argument. So I'd start by making sure I understand their reasoning fully before I push back. Often the disagreement is about assumptions rather than conclusions: they may have assumed a dose level, a mission duration, or a derating factor that I'd challenge, and once we surface that, the conversation becomes about the assumption rather than about their competence.

I'd frame the concern as a question rather than a verdict: "Walk me through how this behaves at end-of-life dose" or "What's the margin here if the part drifts by its worst-case TID spec?" That invites them to stress-test their own design rather than defend it. If they've already considered it and have an answer, I learn something. If they haven't, they discover the gap themselves, which is far more durable than me pointing it out.

If we still disagree after that, I'd move to evidence: what data do we have, what data could we get, and what would it cost to resolve the question? Sometimes the answer is a focused test or a worst-case analysis that settles it. Sometimes the answer is that the risk is real but acceptable given mission constraints, and we document it as a known risk with a mitigation plan. Either way, the decision gets made on the basis of shared evidence rather than seniority.

Throughout, I'd keep the tone collaborative and make it clear that raising a concern is not a criticism of the engineer. I'd also make sure the review record captures the concern and the resolution, so if the risk materializes later, we know it was a conscious decision rather than an oversight. And I'd follow up privately if I sensed the engineer felt singled out — the goal is to build their judgment, not to make them defensive in front of the team.

**Possible follow-ups:**
- What would you do if the engineer's proposal was technically defensible but you still felt the risk was too high to accept?
- How would you handle it if the same engineer repeatedly under-margined designs, and the issue became a pattern rather than a one-off?