# space-rad-hard — Day 73

## Q1: How would you approach designing a radiation-tolerant analog signal chain for a spacecraft instrument where the sensor output is a low-level differential signal, and both the amplifier front-end and the ADC reference can experience single-event transients (SETs)?

**Answer:** The core problem is that a low-level differential signal has very little amplitude headroom, so any transient injected anywhere in the chain — at the amplifier input, in the amplifier's internal bias network, or on the ADC reference — can look like real signal rather than obvious noise. I'd approach it in layers.

First, at the topology level: use a differential signal path end-to-end, including a differential or fully-differential amplifier and a differential-input ADC, so that common-mode transients couple equally into both legs and largely cancel. Keep the sensor-to-amplifier routing tightly coupled and symmetric so that a transient couples as common-mode rather than differentially. Where the sensor is single-ended, convert to differential as close to the sensor as possible.

Second, at the reference: the ADC reference is often the most vulnerable node because a transient there scales every conversion result. I'd filter the reference heavily with an RC or active filter whose corner is well below the sampling rate, and place a large, low-ESR local reservoir right at the reference pin so a short transient is absorbed before it moves the reference. If the reference is external and uncharacterized, I'd consider a redundant reference with a comparator that flags disagreement, or a ratiometric scheme where the reference and the signal share the same disturbance so it cancels in the ratio.

Third, at the conversion and validation level: since SETs are transient, I'd use temporal redundancy — take multiple samples and apply a median or a plausibility filter rather than trusting any single conversion. For a control loop, a slew-rate or rate-of-change limit on the accepted value rejects a one-sample spike without adding latency to legitimate changes. Where the measurement is safety-critical, I'd add a second, independent conversion path (different ADC or different reference) and compare.

Finally, at the physical level: guard the analog front-end from digital switching noise with separate analog/digital ground returns joined at one point, keep the analog supply filtered and separate, and shield or route away from high-speed digital. The goal is to make the chain tolerant both to radiation-induced transients and to ordinary switching noise, because the mitigation is largely the same.

**Possible follow-ups:**
- How would you distinguish a genuine fast sensor event from an SET-induced spike if both look like a one-sample excursion?
- If the reference and the signal share the same supply, how does that change your filtering strategy?

## Q2: How would you approach selecting and qualifying a voltage supervisor or reset IC for a space-deployed system, given that most commercial parts are not radiation-characterized?

**Answer:** I'd start by being clear about what the part actually has to do and what failure of it means. A voltage supervisor that falsely asserts reset causes an unnecessary reboot; one that fails to assert reset lets the processor run out of spec. Both are bad, but the second is usually worse, so I'd weight the selection toward parts whose failure mode is "asserts reset too eagerly" rather than "never asserts."

For a commercial part with no radiation data, I'd treat it as unqualified and decide whether I can tolerate that. Options, roughly in order of preference:

1. Find a part with published TID and SEE data, even if it's not on a QML — some manufacturers publish single-event test results for industrial parts, and that's usable evidence.
2. If no data exists, characterize it myself: TID at a cobalt-60 or proton facility to the mission dose with margin, and heavy-ion or proton testing for SEL and SET on the reset output. This is expensive, so I'd only do it for a part that's genuinely critical and has no alternative.
3. If testing isn't feasible, design around the uncertainty: use a supervisor with a simple, well-understood topology (a bandgap reference and a comparator, no internal state machine or trim memory that can upset), add external filtering and hysteresis so a transient on the sense input doesn't cause a spurious reset, and consider a discrete supervisor built from rad-tolerant components where I control every node.
4. Add diversity: don't rely on a single supervisor. Use an independent watchdog or a second supervisor with a different threshold, and require agreement before acting, or use the supervisor only as a secondary check behind a primary reset source.

I'd also look at derating and margin: a supervisor whose threshold sits right at the processor's minimum operating voltage has no room for TID-induced threshold drift, so I'd want the threshold comfortably below the processor's minimum and above the point where the processor is truly non-functional.

**Possible follow-ups:**
- How would you test a supervisor's SET behavior on the reset output specifically, as opposed to its threshold accuracy?
- If you use two supervisors with different thresholds, how do you arbitrate between them without adding a new single point of failure?

## Q3: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** The argument has a category error in it: TMR on the digital side protects against upsets in the digital logic, but it does nothing for a fault that originates in the analog front-end. If the amplifier or ADC produces a wrong value, all three TMR lanes receive the same wrong input and agree on it — TMR faithfully replicates the error. Redundancy only helps if the redundant copies fail independently, and a single analog chain is a single point of failure regardless of what's downstream.

So I'd separate two questions. First, is the analog chain actually a single point of failure for a safety- or mission-critical control loop? If yes, the digital TMR is not a substitute for analog redundancy. Second, what's the realistic failure mode of that chain in the radiation environment — an SET that produces a transient wrong reading, a TID-induced gain or offset drift, or a hard failure? Each calls for a different mitigation.

For a transient SET, temporal redundancy plus plausibility checking may be enough: sample multiple times, reject outliers, rate-limit the control input. For a persistent drift or a hard failure, you need spatial redundancy — a second independent chain, ideally with a different amplifier and ADC part so a common-mode radiation sensitivity doesn't take out both. If full duplication is too costly, a partial approach works: duplicate only the most critical element (for example, a second reference or a second ADC on the same conditioned signal) and cross-check.

I'd also point out that the control loop itself is a place to add tolerance: a loop that saturates or commands a dangerous actuator position on a single bad sample is fragile regardless of the source of the bad sample. Clamping the output, limiting slew rate, and requiring the measurement to persist before acting all reduce the consequence of a single wrong reading.

I'd frame this to the engineer not as "you're wrong" but as "TMR protects a different failure domain than the one you're worried about — let's map the analog chain's failure modes and decide which ones we can tolerate and which need redundancy."

**Possible follow-ups:**
- How would you decide between duplicating the whole analog chain versus adding a cheaper cross-check on just the ADC?
- If you duplicate the chain, how do you detect which copy is wrong when they disagree?

## Q4: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a poor fit for a fault-tolerant space bus in its standard form, so the first question is whether it's the right choice at all. It's single-ended, open-drain, has no error detection beyond the ACK bit, and a stuck node can hold SDA or SCL low and lock the entire bus. If the sensors are non-critical and the bus is short, it can work with mitigations; if it's carrying control-loop data, I'd push for a differential bus like RS485 or CAN-FD with proper error detection.

Assuming I²C is retained, I'd address three failure modes:

**Data corruption:** Add a CRC or checksum at the application layer, since I²C's ACK only confirms a byte was received, not that it was correct. Use a command/response protocol with sequence numbers so a corrupted or replayed message is detected. Read back critical writes and verify.

**Bus lock-up:** A node that has been upset mid-transaction can hold the bus. The standard recovery is clock stretching — the master toggles SCL up to nine times to flush the stuck slave, then issues a STOP. I'd implement that in the master firmware as an automatic recovery routine, and add a hardware watchdog that power-cycles the bus or the offending node if the recovery fails. Better still, put each node behind a bus switch or mux so a locked node can be isolated rather than taking down the whole bus.

**Node failure:** If one node can corrupt the bus for everyone, isolate it. A bus switch per node, or a mux that lets the master talk to one node at a time, limits the blast radius. For critical sensors, consider a redundant node on a separate bus segment.

At the physical layer, keep the bus short and well-terminated, use proper pull-up sizing for the bus capacitance, and add filtering to reject transients. And I'd make the master tolerant: timeouts on every transaction, retries with backoff, and a defined degraded mode where the system continues with the sensors it can still reach.

**Possible follow-ups:**
- How would you detect that a node is holding the bus versus the master having lost arbitration?
- If you isolate nodes behind a mux, how do you handle a node that's stuck in a state where it responds but with wrong data?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves acknowledgment before any critique — otherwise the review becomes about defending the work rather than improving the design. I'd open by restating what the proposal gets right and what problem it's solving, so it's clear I've understood it.

Then I'd move the discussion from opinion to evidence. "I think this is under-margined" is a position; "here's the margin calculation and here's the environment spec it's being compared against" is a shared basis for a decision. I'd ask the engineer to walk through their margin analysis — what environment they assumed, what derating they applied, what the worst-case corner is — and I'd do the same for my concern. Often the disagreement resolves itself once both parties are looking at the same numbers, because either the engineer missed a corner or I'm applying a criterion that doesn't fit this case.

If the numbers still disagree, I'd look for the underlying assumption that differs. Is it the total dose the mission actually sees? The derating standard being applied? Whether a particular failure mode is credible for this part? Naming the assumption makes it testable — we can go find the data, run the test, or ask someone who's flown the part.

If it can't be resolved with data in the room, I'd make the decision explicit and time-boxed: agree on what evidence would settle it, who will get it, and by when. If the schedule doesn't allow that, I'd make the call as the lead, but I'd explain the reasoning and the risk being accepted, and I'd document it. What I wouldn't do is let it become a status contest or quietly override the engineer — that kills the willingness to bring proposals forward, which is worse for the program than any single design decision.

Throughout, I'd keep the framing on the design and the mission, not on who's right. "How do we make sure this board survives the environment" is a question we're both answering; "your design is wrong" is a fight.

**Possible follow-ups:**
- What if the engineer is right and you're the one applying an overly conservative criterion?
- How would you handle it if the engineer agrees with your concern but the schedule doesn't allow a redesign?