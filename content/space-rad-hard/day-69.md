# space-rad-hard — Day 69

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd treat this as three separate problems that share one architecture: fault isolation between feeds, per-load protection, and controlled inrush.

For feed isolation, the goal is that a fault on one 28V input cannot drag down the other or back-feed into it. That means each feed gets its own blocking element — an ideal-diode/ORing controller or a suitably derated Schottky — plus independent current limiting, so a short on feed A is contained to feed A. I'd avoid a simple diode-OR into a single bulk node without per-feed current limiting, because a hard short on one feed will try to pull the shared node down through the other feed's path.

For load protection, I'd put an eFuse or hot-swap controller in front of each load, sized so that a single-event latch-up on any one load trips that load's current limit and latches it off, rather than collapsing the rail. The trip threshold and response time need to be chosen against the load's legitimate inrush and transient demand — too tight and you nuisance-trip on normal startup; too loose and you don't catch a latch-up before it drags the bus.

For hot-swap, the concern is inrush into the load's input capacitance. I'd use a controlled slew-rate gate drive on the pass FET, or a dedicated hot-swap controller with a programmed dV/dt, so the bus sees a bounded current ramp instead of a step. I'd also add local bulk capacitance on each load's input so the transient is supplied locally rather than pulled from the bus.

The cross-cutting piece is that all of this has to be radiation-aware: the ORing controller, the eFuse, and any sense circuitry are themselves exposed, so I'd want parts with at least some SEE characterization, or design in margin and monitoring so a single upset in the protection logic doesn't disable the protection. And I'd want telemetry on each feed and each load's current so a latch-up event is observable, not just silently recovered.

**Possible follow-ups:**
- How would you decide between a latching-off protection scheme and an auto-retry scheme for a latched load, given that you can't service the payload?
- What would you monitor to distinguish a genuine latch-up from a transient inrush event that just looks like overcurrent?

## Q2: How would you approach designing a radiation-tolerant current-sense circuit for a spacecraft power bus, where the sense resistor itself is exposed to radiation and its value may drift over the mission lifetime?

**Answer:** The core issue is that any current-sense topology depends on a reference element — a shunt resistor, a Hall sensor, or a sense FET's Rds(on) — and each of those drifts under TID and displacement damage to different degrees. So the first decision is topology, and the second is how you compensate for the drift you can't eliminate.

A shunt resistor is usually the most radiation-stable option because the drift mechanism is mostly bulk material damage, which for a metal-foil or bulk-metal element is small compared to a semiconductor sense element. But "small" isn't "zero," and the resistor's temperature coefficient interacts with the thermal environment, so I'd want a low-TCR part and I'd want to know its behavior under the expected dose. A sense FET's Rds(on) is a much worse choice here — it drifts with both dose and temperature, and the drift is large enough that a fixed gain stage will read wrong.

For the amplifier side, I'd use a differential amplifier or current-sense amplifier with good CMRR, because the shunt sits at bus potential and the common-mode is high. I'd want the amp to be radiation-tolerant or at least characterized, and I'd add input filtering to keep single-event transients on the bus from coupling into the sense path.

The compensation strategy is where I'd spend the most thought. If the shunt value can drift, a one-time factory calibration is not enough — I'd want either an in-situ reference (a known current source or a second, more stable sense element to cross-check against) or a periodic calibration against a known load. If neither is available, I'd design the measurement to be ratiometric where possible, so that drift in the sense element cancels against drift in the reference, and I'd widen the uncertainty budget rather than pretend the reading is exact.

Finally, I'd treat the current-sense output as a monitored signal, not a control input, unless the control loop can tolerate the drift. If it feeds a protection threshold, I'd set the threshold with margin for the worst-case drift over life, and I'd add a plausibility check against other telemetry so a drifting sense element doesn't silently cause a false trip or a missed fault.

**Possible follow-ups:**
- How would you validate the drift behavior of a candidate shunt resistor without a dedicated radiation test campaign?
- If the sense element drifts and you can't calibrate in orbit, how would you keep the protection function trustworthy?

## Q3: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** The argument conflates two different failure domains. TMR on the digital side protects against upsets in the logic that processes the measurement — it does nothing for an upset in the measurement itself. If the analog front-end produces a wrong value, all three TMR lanes will faithfully agree on the wrong value, and the voter will pass it through. TMR only helps when the redundant copies can disagree; a single sensor feeding a single amplifier feeding a single ADC gives you one copy, so there's nothing to vote on.

So I'd separate the question into two: what failure modes does the analog chain have, and which of them matter for this control loop?

The analog chain has its own SEE susceptibility — single-event transients in the amplifier, in the ADC's sample-and-hold, or in the reference can produce a spurious reading. It also has TID drift, which is a slow bias rather than a transient. And it has the ordinary analog failure modes: open sensor, shorted input, saturated amplifier.

For a control loop, the dangerous case is usually a transient that looks like a valid measurement and drives the loop the wrong way. So the mitigation isn't necessarily full triple redundancy of the analog chain — that's expensive and often impractical for a sensor. It's more likely: a plausibility check on the reading (rate-of-change limit, range check, comparison against a second independent measurement if one exists), a hold-last-good or fail-safe behavior when the reading is implausible, and a time-domain filter that rejects single-sample transients without adding too much lag to the loop.

I'd also want to know whether the sensor itself can be duplicated. If the measurement is critical enough that a wrong value is dangerous, then two independent sensors with a cross-check is the right answer, and the digital TMR then protects the comparison logic. If duplication isn't possible, then the design has to accept that the analog chain is a single point of failure and mitigate at the system level — fail-safe on implausible input, and a control law that degrades gracefully rather than acting on a bad reading.

The framing I'd give the junior engineer is: TMR protects against disagreement between redundant copies. It doesn't create redundancy where none exists. The analog chain needs its own answer.

**Possible follow-ups:**
- How would you set the rate-of-change limit for a plausibility check without rejecting legitimate fast transients in the measured quantity?
- If you can't duplicate the sensor, how would you decide between fail-safe shutdown and hold-last-good for an implausible reading?

## Q4: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a poor fit for a fault-tolerant bus in a radiation environment, and I'd start by acknowledging that rather than trying to patch it into one. The protocol has no error detection beyond the ACK bit, no framing, and a well-known failure mode where a slave holding SDA low mid-transaction wedges the bus. In a radiation environment, an upset in a slave's state machine can produce exactly that condition, and the master has no protocol-level way to recover.

If I²C is fixed by the sensor selection, then the design has to add the robustness the protocol lacks. On the physical side: separate the bus into segments with a bus switch or mux per segment, so a wedged slave on one segment doesn't take down the others. Add series resistors and keep the bus capacitance within spec so rise times stay clean. Consider a bus buffer with rise-time acceleration if the bus is long or heavily loaded.

On the protocol side: every transaction gets a CRC or checksum in the payload, because the ACK bit alone won't catch a corrupted byte that happens to ACK. Every write is read back and verified. Every read is range-checked and rate-checked before it's used. And the master implements a timeout on every transaction, so a slave that doesn't respond doesn't hang the master.

For lock-up recovery, the standard trick is to clock the bus manually — toggle SCL as a GPIO for up to nine cycles to let the stuck slave finish its byte and release SDA, then issue a STOP. That recovery has to be built into the master's driver, and it has to be triggered by a watchdog or a bus-health monitor, not by the master's normal code path, because the master itself may be the thing that's wedged.

The deeper answer is that if the system genuinely needs a fault-tolerant multi-drop bus, I²C is the wrong choice and I'd push for something with real framing and error detection — CAN-FD, RS-485 with a proper protocol layer, or a point-to-point topology with a dedicated link per sensor. The cost of adding CRC, readback, segmentation, and lock-up recovery to I²C often exceeds the cost of just using a better bus.

**Possible follow-ups:**
- How would you detect that a slave is wedged versus just slow, without false-triggering the recovery sequence?
- If you segment the bus with switches, how do you handle the case where the switch itself is upset?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the technical question from the interpersonal one, because they need different handling. The technical question is: is the margin actually insufficient, and by how much? The interpersonal question is: how do I challenge the work without making the engineer defensive, so that the review produces a better design rather than a winner and a loser?

On the technical side, I'd ask the engineer to walk me through the margin calculation — not to catch them out, but because the fastest way to resolve a margin disagreement is to look at the same numbers together. Often the disagreement is about assumptions rather than arithmetic: they assumed a typical value where I'd assume worst-case, or they used a datasheet number that doesn't account for TID drift, or they didn't include the transient case. Once we're looking at the same assumptions, the gap either closes or it becomes concrete and specific.

If the gap is real, I'd frame it as a question rather than a verdict: "What happens to this design if the parameter drifts by X over the mission?" or "What's the failure mode if this assumption is wrong?" That lets the engineer reason to the conclusion themselves, which is both more respectful and more durable than me just overruling them. If they still disagree, I'd ask them to write down the assumption they're relying on and what would have to be true for it to hold — that often surfaces the disagreement in a form we can actually test or analyze.

On the interpersonal side, I'd be explicit that the review is about the design, not the engineer, and that finding a margin problem in review is a success, not a failure — it's much cheaper than finding it in test or on orbit. I'd also make sure I'm not the only voice; if there's a radiation specialist or a systems engineer in the room, their input carries more weight than mine alone, and it depersonalizes the call.

If after all that we still disagree, I'd make the decision, document the reasoning and the dissenting view, and move on. But I'd do it in a way that leaves the engineer able to disagree without it being career-limiting, because the next review is more important than this one, and I want them to bring me their real analysis, not the analysis they think I want to hear.

**Possible follow-ups:**
- How would you handle it if the engineer's manager is in the room and starts defending the engineer rather than the design?
- What would you do if the schedule pressure makes the "right" fix expensive and the engineer's under-margined solution is the only one that fits the timeline?