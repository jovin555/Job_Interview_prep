# behavioral-leadership — Day 71

## Q1: How would you approach a design review where the review keeps stalling because one reviewer raises a new objection in every session, and the team has started routing around the review process to make progress?
**Answer:** The first thing I'd do is separate the two problems: the reviewer's behavior and the team's workaround. The workaround is the more dangerous one, because once a team starts treating the review as an obstacle rather than a gate, you lose the safety net entirely — and in a regulated environment that's a compliance problem, not just a process annoyance. So I'd address that first by making clear that routing around review isn't acceptable, while also acknowledging that the team's frustration is legitimate and that I'm going to fix the root cause.

For the reviewer, I'd try to understand what's actually happening. There are a few common patterns: the reviewer may be genuinely finding real issues and the review package is too thin, so each session surfaces new gaps; the reviewer may be raising concerns that are real but out of scope for this gate, so they belong in a backlog rather than blocking the review; or the reviewer may be using the review as a venue for perfectionism or for re-litigating decisions that were already made. Each of these needs a different response. I'd have a one-on-one and ask directly what they feel is unresolved, and whether the review package is giving them what they need to evaluate the design in one pass.

Structurally, I'd change the review process so it can't stall indefinitely. That means: a clear entry criterion for what the package must contain, a defined scope for each gate (what's in and what's deferred), a rule that new objections raised after the review opens are logged as action items with owners and due dates rather than blocking closure, and a named decision owner who can call the question when the discussion has run its course. I'd also make sure objections are captured in writing with rationale, so they're not lost and so the reviewer can see their concerns are being tracked rather than dismissed. If the pattern continues after that, it becomes a performance conversation about how the person participates in reviews, not a technical one.

**Possible follow-ups:**
- How would you handle it if the reviewer's objections turn out to be technically valid, and the real problem is that the design isn't ready for review?
- What would you do if the reviewer is more senior than you and resists the process changes?

## Q2: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?
**Answer:** The goal is to hand the firmware team a model they can reason about, not a lecture on analog design and not a one-line "the ADC is noisy." I'd start by characterizing the constraint in the terms the firmware actually operates in: what is the effective number of bits after noise, what is the noise floor in LSBs, what is the sample rate, and what does that mean for the smallest signal change the firmware can reliably detect. That's the number that matters for their filtering, thresholding, and alarm logic — not the datasheet resolution.

Then I'd give them the shape of the noise, not just its magnitude. Is it white noise that averages down with oversampling, or is it correlated with a switching supply, a motor, or a communication burst, in which case averaging won't help and they need to synchronize sampling away from the noise source? That distinction changes the firmware strategy completely, so it's worth the extra half hour to characterize it on the bench and show them a capture. A picture of the noise in the time domain and a spectrum plot communicates more than a paragraph of description.

I'd also be explicit about what the hardware can and can't fix, and what the firmware should not try to compensate for. If the analog front end has a known offset drift over temperature, that's a calibration problem, and the firmware shouldn't be trying to filter it out. If the reference voltage has ripple, that's a hardware issue and no amount of digital filtering will recover the lost accuracy. Being clear about the boundary prevents the firmware team from spending weeks on a software fix for a hardware problem — and prevents the reverse, where hardware assumes firmware will clean it up.

Finally, I'd agree on a shared test: a known input signal, a defined measurement, and a pass/fail criterion that both teams accept. That turns the conversation from "is the ADC good enough?" into "does the system meet the requirement?", which is the question that actually matters and the one that's testable.

**Possible follow-ups:**
- How would you handle it if the firmware team proposes a filtering approach that you believe will mask a real hardware problem rather than solve it?
- What would you do if the constraint can't be met without a hardware change, and the schedule doesn't allow one?

## Q3: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?
**Answer:** The pattern here is usually not a capability gap — it's a confidence and ownership gap. The engineer has learned that deferring is safe, and that being wrong in front of a senior person is costly. So the mentoring has to create a space where they can be wrong cheaply and where the decision is genuinely theirs.

I'd start by giving them a real decision to own, scoped so the blast radius is contained but the decision is not trivial. Something where they have to weigh trade-offs, gather input, and commit — and where I deliberately do not give them the answer. The key is that I have to actually let them decide, including letting them decide something I wouldn't have chosen, as long as it's defensible. If I override them, I've taught them that deferring was correct.

I'd also change how I show up in meetings. If they present a design and I'm in the room, I'd hold back from answering questions directed at them, and if they look to me I'd redirect: "What's your read on that?" That's uncomfortable at first, but it's the only way they learn that the room will accept their answer. I'd also make a point of publicly crediting the decision to them when it goes well, and privately debriefing when it doesn't — focusing on the reasoning process, not the outcome.

For the deeper work, I'd have them write down the decision and the rationale before the review, including the alternatives they rejected and why. That forces them to articulate a position rather than react to the room, and it gives us something concrete to discuss afterward. Over time, the goal is that they walk into a review with a position they can defend, and that they experience the room treating that position as legitimate.

**Possible follow-ups:**
- How would you handle it if they make a decision you disagree with, and it turns out to be wrong?
- What would you do if the senior people in the room keep directing questions to you instead of to them, undermining the handoff?

## Q4: How would you approach structuring a root-cause investigation when the failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?
**Answer:** The pressure to ship a fix quickly is the biggest risk here, because the fastest path is usually to guess at the most likely cause and patch it, which often masks the symptom without addressing the root cause — and in a medical device that's a serious problem. So the first thing I'd do is separate containment from correction. Containment is legitimate and can be fast: if there's a way to detect the failure, limit its impact, or add a diagnostic that captures data when it occurs, that buys time without pretending we've solved anything. I'd be explicit with stakeholders that containment is not a fix and that the investigation continues.

For the investigation itself, when you can't reproduce on demand, you have to instrument for capture. That means adding logging, counters, or a trace buffer that records the state leading up to the failure, so that when it happens in the field or in test, you get data instead of a report. I'd also look hard at the conditions: does it correlate with temperature, supply voltage, specific sequences of operation, time since power-on, or a particular hardware revision? Even a weak correlation is a lead. And I'd widen the net on where it's observed — sometimes a failure that "can't be reproduced" is actually being reproduced but not recognized because the test doesn't exercise the right path.

I'd also apply structured methods rather than brainstorming. A fishbone or fault tree forces the team to enumerate possible causes across hardware, firmware, environment, and use, and then to design a test or a measurement that would confirm or eliminate each one. The discipline matters because it prevents the team from anchoring on the first plausible cause. And I'd keep a written record of what's been ruled out and how, so the investigation doesn't loop.

Finally, I'd manage the pressure explicitly. I'd tell stakeholders what we know, what we don't, what containment is in place, and what the plan is to find the root cause — and I'd resist committing to a fix date until we understand the mechanism. Committing to a date before you understand the cause is how you end up shipping a fix that doesn't work.

**Possible follow-ups:**
- How would you decide when you've done enough investigation to ship a fix, versus continuing to look for the true root cause?
- What would you do if the failure only occurs in the field and you can't get instrumentation onto the deployed units?

## Q5: How would you approach deciding how much technical detail to include when presenting a design trade-off to a mixed audience of engineers, a quality manager, and a product manager in the same room?
**Answer:** I'd structure the presentation in layers, so each audience can take what they need without anyone being lost or bored. The top layer is the decision itself: what we're choosing between, what the recommendation is, and what it costs — in schedule, risk, and money. That's the layer everyone needs, and it should be short enough that a product manager can follow it without the engineering detail. The middle layer is the reasoning: the key trade-offs, the criteria we used, and the evidence behind the recommendation. That's where the engineers and the quality manager will engage. The bottom layer is the supporting data — measurements, calculations, test results — which I'd have available but not present unless someone asks.

The critical discipline is to be honest about uncertainty at every layer. If a number is an estimate, say so. If a trade-off depends on an assumption that hasn't been validated, name the assumption. Quality and regulatory audiences especially need to know what's been verified versus what's assumed, because that affects risk. And product management needs to know what could change the answer, because that affects planning. Hiding uncertainty to make the recommendation look cleaner is the fastest way to lose credibility when the assumption turns out to be wrong.

I'd also be deliberate about what I'm asking for. Is this a decision meeting, where I need a yes/no, or an information meeting, where I'm briefing people? If it's a decision, I'd state the recommendation clearly and ask for a decision, rather than leaving it ambiguous. If it's information, I'd say so and not put people on the spot. Mixing the two is a common source of frustration.

Finally, I'd watch the room. If the engineers are nodding and the product manager is silent, I'd check in with the product manager directly — silence often means confusion, not agreement. If the quality manager raises a concern, I'd take it seriously in the room rather than deferring it, because that's exactly the kind of input that prevents a bad decision from going forward.

**Possible follow-ups:**
- How would you handle it if the product manager pushes for a decision before the engineers have finished evaluating the trade-off?
- What would you do if the quality manager raises a risk concern that you think is overstated, in front of the whole group?