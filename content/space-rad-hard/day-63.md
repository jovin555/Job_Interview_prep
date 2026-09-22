# space-rad-hard — Day 63

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd treat this as three separable problems — feed isolation, fault containment, and inrush management — and make sure the design doesn't let any one of them compromise the others.

For feed isolation, the two 28V inputs should be combined through an ORing scheme that prevents a fault on one feed from dragging down the other. Ideal-diode controllers or ORing FETs are preferable to simple Schottky ORing because they give low forward drop and, more importantly, allow the faulty feed to be actively disconnected rather than just back-biased. Each feed needs its own reverse-polarity and overvoltage protection, and the ORing stage should be upstream of any shared bulk capacitance so a shorted feed can't discharge the common rail.

For fault containment, each downstream load branch gets its own current-limiting or e-fuse stage with a defined trip threshold and a latch-off or retry behavior chosen per load criticality. A latched load — which is exactly the failure signature a single-event latch-up produces — must be isolated at the branch level so the rest of the payload keeps running. I'd also think about whether the faulted branch should auto-retry or stay latched off: auto-retry risks oscillating into a persistent fault, while latch-off risks losing a recoverable load, so the choice should be driven by whether the load is mission-critical and whether the system can command a re-arm.

For hot-swap, the concern is inrush into the branch capacitance when a load is inserted or re-armed. That means a controlled slew rate on the pass FET, a dV/dt limit or active current foldback during startup, and enough local bulk capacitance downstream to ride through the transient without pulling the main bus below its undervoltage threshold. The bus itself should have enough holdup that a single branch's inrush doesn't disturb the other branches.

Throughout, I'd want the fault reporting to be observable — a latch-up event that silently self-clears is a reliability problem you can't characterize. And I'd verify the whole thing under worst-case conditions: minimum bus voltage, maximum load capacitance, and a simulated short on one feed while the other is at its lowest specified input.

**Possible follow-ups:**
- How would you decide between latch-off and auto-retry for a load that isn't strictly mission-critical but whose loss degrades science return?
- What would you look for in the ORing controller's datasheet to convince yourself it behaves correctly during a hot-swap event on the *other* feed?

## Q2: How would you approach designing a latch-up protection scheme for a mixed-signal board where the sensitive analog front-end and the digital processing section share a common 3.3V rail, and a single-event latch-up in either section could drag the whole rail down?

**Answer:** The core problem is that a shared rail couples the failure of one section into the other, so the first design decision is whether that sharing is actually necessary. If the analog front-end's noise and accuracy requirements allow it, splitting the 3.3V into separately protected branches — even if they originate from the same converter — gives you fault containment without a second converter. That's usually the highest-leverage change.

If they must share a rail, then the protection has to be fast enough to catch a latch-up before the rail collapses. A latch-up is a low-impedance, high-current state, so the signature is a rapid current rise with the rail voltage sagging. A current-sense element in series with the rail, feeding a comparator with a threshold set above the maximum legitimate transient current but below the latch-up current, can trigger a disconnect. The tricky part is speed versus false trips: the threshold has to clear normal inrush and load steps, but the response has to be fast enough that the rail doesn't sag below the brownout threshold of the *other* section before the disconnect happens. That usually means local bulk capacitance on each section to ride through the detection-and-disconnect window.

I'd also add per-section current limiting rather than relying solely on a single upstream protection device, because a single device protecting both sections means a fault in one takes down both. And I'd think about the recovery path: after a latch-up is cleared, the affected section needs a defined power-cycle sequence, and the unaffected section should not be disturbed by that sequence. That argues for independent enable control per section.

Finally, I'd want to understand the latch-up sensitivity of the specific parts. A part with a high LET threshold and a wide safe operating area is a much easier design problem than one that latches at low LET, and that difference should drive part selection before the protection circuit is finalized.

**Possible follow-ups:**
- How would you set the current threshold and response time without knowing the exact latch-up current signature of every part on the rail?
- If the analog front-end can't tolerate a power cycle mid-measurement, how does that change your recovery strategy?

## Q3: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** The argument has a category error in it: TMR on the digital side protects against upsets in the digital logic, but it does nothing for a single-event transient that corrupts the analog measurement *before* it ever reaches the digital domain. If the ADC samples a spurious value because the amplifier or the reference glitched, TMR will faithfully replicate and vote on the wrong number. Redundancy downstream of a corrupted input doesn't recover the input.

So the real question is what the analog chain's failure modes are and whether the control loop can tolerate them. A single-ended chain with no redundancy has at least three exposure points: the sensor itself, the amplifier front-end, and the ADC reference. Each can produce a transient that looks like a valid measurement. The severity depends on the loop's dynamics — a slow thermal loop might average out a brief spike, while a fast control loop could act on it immediately.

I'd want to see the engineer's reasoning about the *consequence* of a corrupted measurement, not just the probability. If a spurious reading can command an actuator to a dangerous state, then the analog chain needs its own protection: a plausibility check on the digitized value (rate-of-change limiting, range checking, comparison against a redundant or dissimilar measurement), or a redundant signal path with voting at the ADC output. Differential signaling through the chain also helps, because a common-mode transient couples less effectively into a differential pair.

I'd also push back on the framing that "the digital side is covered, so we're fine." The right framing is end-to-end: what's the probability that a corrupted measurement reaches the actuator, and what's the consequence? That analysis usually shows the analog front-end deserves at least as much attention as the digital logic.

**Possible follow-ups:**
- What's the difference between a plausibility check and true redundancy, and when is each appropriate?
- How would you decide whether the sensor itself needs redundancy, given that a redundant sensor doubles the analog front-end cost and board area?

## Q4: How would you approach derating and part selection for a space-deployed board, and how does derating interact with the radiation tolerance you're trying to achieve?

**Answer:** Derating and radiation tolerance are related but distinct, and conflating them is a common mistake. Derating is about keeping a part within a reduced envelope of its rated stress — voltage, current, power, junction temperature, and so on — so that it has margin against the normal variability of manufacturing, aging, and operating conditions. Radiation tolerance is about how the part behaves when it's exposed to ionizing particles. A part can be well-derated and still fail under radiation, and a rad-hard part can still be under-derated and fail thermally.

For part selection, I'd start from the mission environment: total dose, the expected heavy-ion environment, and whether single-event latch-up is a concern. That tells me whether I need a QML-qualified rad-hard part, a part with published radiation test data that I can evaluate against the mission, or a COTS part that I'll need to characterize myself. The trade-off is usually schedule and cost versus risk: rad-hard parts are expensive and have long lead times, but they come with the characterization already done. COTS parts are cheap and available, but the burden of proof is on me.

Derating interacts with radiation in a few specific ways. First, total ionizing dose effects are often worse at higher bias and temperature, so a part that's derated for voltage and junction temperature may have more TID margin than its rated numbers suggest — but that's not something to assume without data. Second, single-event latch-up sensitivity can depend on supply voltage and temperature, so derating the supply can sometimes reduce latch-up cross-section, though again this needs to be verified. Third, displacement damage in optoelectronics and some analog parts is a cumulative effect that derating doesn't help with at all.

The practical approach is to build a derating table per part class, apply it consistently, and then layer the radiation assessment on top — treating the two as separate gates that a part must pass. I'd also document the rationale for any part that doesn't have published radiation data, because that's the part most likely to become a problem later.

**Possible follow-ups:**
- How would you handle a part that meets the derating requirements but has no radiation data and no budget for testing?
- What's the difference between total dose margin and single-event margin, and how do you track them separately?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves acknowledgment before anything else — if the review starts with "this is wrong," the engineer will defend the work rather than examine it, and the review stops being useful.

Then I'd try to make the disagreement concrete rather than abstract. "Under-margined" is a judgment; the useful version is a specific question: what's the worst-case stress this part sees, what's its rated limit, and what's the margin between them? If I can get the engineer to walk through their own numbers, either the gap becomes visible to both of us, or I discover I was wrong about something. Both outcomes are good.

If the gap is real, I'd frame it as a shared problem rather than a verdict. The question isn't "is your design bad" but "what would it take to make this design defensible against the environment we're actually flying into?" That might mean a different part, additional protection, a test to characterize the part, or a documented risk acceptance if the consequence is low. The engineer is often the best person to find the cheapest path to margin, because they know the design better than I do.

I'd also be explicit about what would change my mind. If the engineer can show me radiation data, a derating analysis, or a test result that closes the gap, I should say so up front — that makes the review a search for evidence rather than a contest of opinions. And if the decision ultimately goes against the proposal, I'd make sure the reasoning is documented, so it's clear it was a technical judgment and not a personal one.

The thing I'd avoid is letting the review become about who's right. The goal is a design that survives the mission, and the fastest way to get there is to make the engineer a partner in finding the margin rather than a defendant in a trial about it.

**Possible follow-ups:**
- What if the engineer's proposal is actually correct and your concern is based on an outdated assumption — how do you make sure you'd notice that?
- How do you handle a situation where the schedule doesn't allow the test that would resolve the disagreement?