# space-rad-hard — Day 70

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd treat this as three separable problems — source selection, fault isolation, and inrush management — and make sure the design doesn't let any one of them compromise the others.

For source selection, the two 28V feeds should be combined through an ORing scheme rather than simply tied together. Diode ORing is the simplest and most robust, but the forward drop and the resulting dissipation are often unacceptable at payload currents, so an active ORing controller with a low-Rds(on) pass FET is usually the better trade. The key requirement is that the ORing element must fail open, not short — if one feed shorts, the ORing device on that leg has to isolate it without dragging the common rail down. That means the controller needs to detect reverse current and turn off fast, and the FET needs to be rated for the full bus transient plus margin.

For fault isolation, each downstream load should have its own current-limiting or eFuse stage rather than relying on a single upstream protection device. A latch-up on one load then trips only that load's protection, and the rest of the payload keeps running. I'd set the current limit above the load's worst-case inrush but below the point where the shared rail sags enough to reset other loads, and I'd make sure the protection device's trip response is fast enough to clear before the bus droops.

For hot-swap, the concern is the inrush into the load's input capacitance when it's plugged in or when its eFuse re-enables after a fault. A pure current limit will hold the FET in its linear region and dissipate a lot of power during a long inrush, so I'd use a controlled slew-rate start — either an eFuse with a programmed dV/dt or a dedicated hot-swap controller with a gate ramp — so the inrush current is bounded by the capacitance and the ramp rate rather than by the current limit. I'd also add a timer so that if the load doesn't come up within a defined window, the channel latches off rather than cooking the FET.

The interactions matter as much as the blocks. The ORing controller's reverse-current threshold has to be coordinated with the eFuse trip points so that a fault on one feed doesn't cause the other feed's ORing device to chatter. And the hot-swap ramp has to be slow enough not to disturb the bus but fast enough that the load's own supervisory logic doesn't time out. I'd verify all of this with a fault-injection test matrix — short each load, latch each load, hot-swap each feed — rather than just checking nominal operation.

**Possible follow-ups:**
- How would you decide between a discrete ORing controller and an integrated hot-swap/ORing IC for this application?
- What would you do if the two 28V feeds come from the same source upstream, so they're not truly independent?

## Q2: How would you approach selecting and qualifying a voltage supervisor or reset IC for a space-deployed system, given that most commercial parts are not radiation-characterized?

**Answer:** I'd start by being honest about what the part actually has to do, because that determines how much radiation risk is tolerable. A supervisor that only holds the processor in reset during power-up is a very different risk than one that's the sole guard against a brownout during a critical control loop. If the function is safety-critical, I'd push hard for a rad-hard or at least radiation-tested part, even at significant cost and lead time. If it's a secondary function, a COTS part with a documented test campaign may be acceptable.

For a COTS part, the qualification path is roughly: first, look for existing radiation data — manufacturer test reports, NASA/JPL or ESA databases, published papers. A part that's been tested by someone else, even at a different lot, is a much better starting point than an untested one. Second, if no data exists, decide whether to test. A focused heavy-ion and TID test on a small sample is often cheaper than people assume, and it converts an unknown into a bounded risk. Third, if testing isn't feasible, do a failure-modes analysis: what happens if the supervisor's threshold drifts with TID, if an SET causes a spurious reset, or if an SEL latches it? A spurious reset is usually recoverable; a supervisor that fails to assert reset when it should is the dangerous case.

The design should also not depend on the supervisor being perfect. I'd add diversity: an independent watchdog or a second supervisor with a different threshold, so a single failed supervisor doesn't leave the system unguarded. And I'd make sure the supervisor's output can't be the only thing holding the processor in a safe state — if it fails, the processor should still be able to detect the condition itself.

For the specific part selection, I'd look at the process technology. Bipolar and older CMOS nodes tend to have more published radiation behavior than modern fine-geometry parts, and a simple supervisor with few internal nodes is generally easier to bound than a complex one. I'd also check the package and the reference — a bandgap reference inside the supervisor is often the TID-sensitive element, and ELDRS can matter at low dose rates.

**Possible follow-ups:**
- How would you structure a limited-budget radiation test for a supervisor you can't find data on?
- What would you do if the only supervisor that meets your threshold accuracy has no radiation data and no viable alternative?

## Q3: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** The argument has a category error in it. TMR on the digital side protects against upsets in the digital logic — it doesn't protect against a wrong value arriving at the digital side in the first place. If the analog chain produces a corrupted measurement, TMR will faithfully vote on the corrupted value and pass it through. Redundancy downstream of a single point of failure doesn't remove the single point of failure.

So the first thing I'd do is trace the actual failure modes of the analog chain and ask what each one does to the control loop. An SET on the amplifier could produce a transient spike that the ADC samples; an SET on the ADC's sample-and-hold could corrupt a single conversion; a TID-induced drift in the amplifier's offset or gain could bias every measurement slowly over mission life. These are different problems and they need different mitigations.

For the transient cases, the cheapest mitigation is often temporal rather than spatial: sample the channel more than once and reject outliers, or compare against a plausibility window derived from the physics of the sensor. That doesn't require a second amplifier, and it catches single-sample corruption. For the drift case, temporal redundancy doesn't help — you need either a ratiometric measurement against a stable reference, periodic calibration against a known stimulus, or a second measurement path with a different topology so the two drift differently.

If the measurement genuinely feeds a safety-critical control loop and the consequences of a wrong value are severe, then I'd argue for actual redundancy in the analog chain — two independent signal paths, ideally with different amplifier topologies and separate ADC channels, with a comparison in the digital domain. That's expensive in board area and power, so it has to be justified by the criticality, but "the digital side has TMR" is not a justification for skipping it.

The conversation with the engineer is about making the failure modes explicit. I'd ask them to write down, for each element in the analog chain, what happens if it fails or upsets, and what the control loop does with the resulting value. Once that's on paper, the gap is usually obvious without me having to argue it.

**Possible follow-ups:**
- How would you decide between temporal redundancy and a fully redundant analog path for a given measurement?
- How would you handle a sensor that itself has no redundancy option — for example, a single physical transducer?

## Q4: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt that puts the main processor into a state where it's still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** This is the hard case for watchdog design, because the usual "is the heartbeat toggling?" check passes even though the processor is functionally dead. The test plan has to verify recovery from that specific failure mode, not just from a clean hang.

On the design side, the first thing is that the heartbeat can't be a simple GPIO toggle driven by a timer interrupt. It has to be a signal that can only be produced by the control loop actually completing a cycle — for example, the loop writes a sequence number or a checksum to a register that the watchdog reads, and the watchdog verifies the value is advancing and plausible. If the loop stops but the timer keeps running, the watchdog sees a stale or non-advancing value and resets. That's the mechanism the test has to exercise.

For the test itself, since I can't inject actual radiation on the ground, I'd use fault injection that reproduces the failure mode. The cleanest approach is to add a test hook in firmware that, on command, disables the control loop task but leaves the timer and heartbeat running. Then I verify that the watchdog fires within its expected window and the system recovers to a known-good state. I'd do this at several points in the mission sequence — during initialization, during nominal operation, during a critical control phase — because the recovery path may differ.

I'd also test the recovery itself, not just the detection. After the reset, does the system re-initialize correctly? Does it restore its state, or does it come up in a safe default? Does it log the event so the ground can see it happened? A watchdog that resets the processor into a bad state is worse than no watchdog.

Beyond the single-fault case, I'd test the interaction with the watchdog's own failure modes. What if the watchdog itself is upset? What if the reset line is stuck? What if the processor resets but the watchdog doesn't re-arm? These are the cases where a single watchdog isn't enough, and the test plan should reveal whether the design has a second layer — an external supervisor, a power-cycle path, or a ground command — to recover from a watchdog failure.

Finally, I'd run the test repeatedly and with variations in timing, because recovery behavior often depends on where in the loop the fault lands. A test that passes once isn't evidence; a test that passes across many injection points and timings is.

**Possible follow-ups:**
- How would you distinguish between a watchdog that's working and one that's resetting the processor so often the system never makes progress?
- What would you add to the design if the processor can hang in a state where even the watchdog's register read returns plausible-looking data?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing is to separate the person from the proposal. The engineer has done real work, and that work deserves to be engaged with on its merits, not dismissed because I disagree with the conclusion. If I open by saying "this is under-margined," I've made it about my judgment versus theirs, and the review becomes a contest. Instead I'd ask them to walk through the margin calculation — what environment they assumed, what part data they used, what the worst case is, and where the uncertainty sits. Often the disagreement is not about the conclusion but about an input: they assumed a lower dose, or a part with better data than I thought, or a derating factor I'd apply differently.

Once the inputs are on the table, the conversation becomes technical rather than personal. If we still disagree, I'd try to find the specific number or assumption that drives the difference and focus on that. "You've assumed 30 krad and I'd plan for 50 — can we agree on which is right for this orbit?" is a much more productive framing than "your design is under-margined." If we can't resolve it in the room, the right move is to assign an action: get the actual environment spec, get the part's radiation report, run the calculation with agreed inputs, and bring it back. That turns a disagreement into a task, and it usually resolves itself because the data settles it.

I'd also be open to being wrong. The engineer may have information I don't — a part with better data than I assumed, a mitigation I hadn't considered, a system-level constraint that changes the trade. If their analysis holds up, I should say so clearly and move on. That's not losing the argument; it's getting the right answer, which is the point.

If after all that I still believe the design is under-margined and the engineer doesn't, I'd make the decision as the lead and document the reasoning — not as "because I said so," but as "here's the environment assumption, here's the margin, here's why I'm not comfortable with it." The engineer may disagree, but they should be able to see the basis for the call. And I'd keep the door open: if they find data that changes the picture, we revisit.

The thing I'd avoid is letting it become adversarial. A design review where people are afraid to propose something wrong is a review that stops catching problems. The goal is to make the engineer's work better, not to win.

**Possible follow-ups:**
- What would you do if the engineer's proposal is technically defensible but you still believe the risk is too high for the mission?
- How would you handle it if the same engineer repeatedly proposes under-margined designs across multiple reviews?