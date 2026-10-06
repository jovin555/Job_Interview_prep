# behavioral-leadership — Day 77

## Q1: How would you approach a design review where the presenter is technically strong but consistently becomes defensive when their work is questioned, and the review needs to be genuinely critical to be useful?

**Answer:** The core problem is that the review's purpose and the presenter's sense of identity have become entangled — a critique of the design reads as a critique of the person. The first move is to reset that framing before the meeting, not during it. A short pre-brief with the presenter a day or two ahead of time does two things: it signals that you respect their work enough to give them a heads-up, and it lets you agree on how the review will run — for example, that the presenter walks through the design first without interruption, and questions are collected and addressed in a second pass. That structure removes the feeling of being ambushed mid-sentence.

During the review itself, model the behavior you want. Ask questions rather than making pronouncements: "What was the reasoning behind this choice?" lands very differently than "This is wrong." Frame concerns as risks to be evaluated rather than verdicts — "I'm wondering whether this trace routing creates a coupling path we should check" invites analysis; "this routing is bad" invites defense. When a concern is raised, explicitly separate the design from the designer: "This is a hard problem and the trade-off here is genuinely difficult" acknowledges the difficulty without conceding the point.

If defensiveness still surfaces, don't escalate in the room. Note the concern, park it as an action item, and follow up one-on-one afterward with data — a simulation, a measurement, a reference design — rather than argument. Defensiveness usually softens when the discussion moves from opinion to evidence. Over time, the goal is to build a norm where being questioned is the expected, normal cost of doing safety-critical work, and where the presenter's willingness to engage with hard questions is itself recognized as a strength.

**Possible follow-ups:**
- What would you do if the defensiveness persists across multiple reviews despite your efforts, and it's starting to suppress questions from other reviewers?
- How would you handle it if the presenter's manager is in the room and the defensiveness is partly performative — aimed at looking strong in front of leadership?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures are the hardest class of problem because the usual loop — observe, hypothesize, reproduce, fix, verify — breaks at the reproduction step. The instinct under schedule pressure is to skip straight to a plausible fix, but that's exactly the trap: without reproduction you can't verify the fix actually addresses the root cause, and you risk shipping a change that masks the symptom while the real failure mode remains.

The first priority is containment, kept strictly separate from correction. Containment means limiting the blast radius — tightening monitoring, adding a workaround, restricting the affected configuration — while being explicit that containment is not a fix and does not close the investigation. This buys time without pretending the problem is solved.

For the investigation itself, the goal is to convert "cannot reproduce" into "reproduces under conditions we haven't yet characterized." That means instrumenting aggressively: adding logging around the suspected subsystem, capturing environmental and timing context at the moment of failure, and building a stress or soak test that runs the system at the edges of its operating envelope — temperature, supply voltage, timing margins, load — where marginal failures tend to surface. A fishbone or Ishikawa pass helps enumerate candidate causes across categories (design margin, component variation, environmental, timing, software state) so the search isn't anchored on the first hypothesis. The 5 Whys is useful once a failure is captured, but it's premature before you have a reproducible event.

Throughout, the discipline is to document hypotheses and the evidence for and against each, so the investigation doesn't loop. When a fix is finally proposed, verification of effectiveness matters more than usual: the fix must be shown to eliminate the failure under the same conditions that produced it, not just to correlate with the failure going away. If schedule pressure forces a decision before full root cause is known, that decision should be made explicitly and documented as a risk, not quietly.

**Possible follow-ups:**
- How would you decide when to stop investigating and ship a mitigation, and how would you communicate that trade-off to stakeholders?
- What would you do if the intermittent failure only appears in the field and never on any bench or soak setup you can build?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode in both directions is real: oversimplify and the firmware team makes design choices that assume precision the hardware can't deliver; over-detail and they disengage, or worse, try to compensate in software for problems that should be fixed in hardware. The bridge is to translate the constraint into the firmware team's own vocabulary — what it means for their sampling strategy, filtering, calibration, and error budget — rather than describing it in analog terms they have no reason to internalize.

Concretely, that means expressing the constraint as a set of numbers and behaviors they can design against: the effective number of bits actually usable after noise, the noise floor and its spectral character (is it white, or is there a periodic component that filtering can target?), the settling time after a multiplexer switch or a gain change, the drift behavior over temperature, and the timing relationship between when a sample is requested and when it's valid. A short characterization document — measured, not theoretical — is worth more than a long explanation. If the analog front end has a known noise source at a particular frequency, saying "there's a switching artifact at this frequency, here's the measured amplitude" lets the firmware team decide whether to filter, average, or change their sampling phase.

Equally important is being explicit about what the firmware should *not* try to fix. If the noise is dominated by a hardware issue that should be resolved at the board level, say so, so the firmware team doesn't burn effort on elaborate digital filtering to paper over it. And keep a feedback loop: if the firmware team's filtering approach reveals something about the analog behavior you didn't characterize, that's a signal to go back and measure again. The relationship works best when the hardware side owns the analog truth and the firmware side owns the digital strategy, with a shared, measured interface between them.

**Possible follow-ups:**
- How would you handle it if the firmware team proposes a filtering approach that would work but adds latency the application can't tolerate?
- What would you do if the constraint turns out to be worse in production units than in the prototypes you characterized?

## Q4: How would you approach deciding how much technical detail to include when presenting a design trade-off to a mixed audience of engineers, a quality manager, and a product manager in the same room?

**Answer:** The instinct is to find a single level of detail that works for everyone, but that usually produces something too shallow for the engineers and too deep for everyone else. A better approach is to structure the presentation in layers, so each audience can engage at the depth they need without anyone being lost or bored.

Lead with the decision and its consequences in plain terms: what the trade-off is, what the options are, what each option costs in terms of performance, risk, schedule, and compliance, and what you're recommending. This top layer should be comprehensible to anyone in the room and should stand on its own — if the product manager only takes away this part, they should still be able to make an informed call. Then provide the supporting technical depth as a second layer, clearly marked as "for those who want the detail," covering the measurements, simulations, or analysis behind the recommendation. Engineers will dig into it; the quality manager will focus on the risk and compliance implications; the product manager can stay at the top layer and ask questions.

The key discipline is to be explicit about which parts of the trade-off are technical judgment and which are business or risk judgment. Engineers often present a recommendation as if it were purely technical when it actually embeds assumptions about acceptable risk or schedule — surfacing those assumptions lets the non-technical stakeholders contribute where their judgment is genuinely relevant. And always state what you'd need to change your recommendation: "if the schedule constraint were relaxed, I'd lean the other way" gives the room a lever to pull rather than forcing a yes/no on a fixed proposal.

**Possible follow-ups:**
- How would you handle it if the product manager pushes for a decision before the engineers feel the technical analysis is complete?
- What would you do if the quality manager raises a compliance concern that the engineers hadn't considered, and it changes the trade-off?

## Q5: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This pattern usually isn't a capability gap — the engineer can execute well — it's a confidence and ownership gap. They've learned that deferring to seniority is safe, and that owning a decision exposes them to being wrong in public. The mentoring goal is to build the muscle of making and defending a decision, in gradually increasing stakes, with a safety net that makes the early reps low-risk.

Start by giving them ownership of a decision that's genuinely theirs but bounded — a component selection, a subsystem architecture, a test approach — with a clear scope and a clear expectation that they will bring a recommendation, not a question. The critical part is what happens next: when they bring the recommendation, resist the urge to override it or to answer for them. Ask them to walk through their reasoning, probe the trade-offs, and if their choice is defensible, let them own it even if you'd have chosen differently. The lesson that their judgment is trusted only lands if they actually get to exercise it.

In meetings, actively redirect deference. When they look to a senior person for the answer, redirect the question back: "What's your read on this?" Do it consistently enough that it becomes the expected pattern. Pair this with a debrief habit — after a decision plays out, good or bad, walk through what the reasoning was and what the outcome taught, so the feedback loop is about the quality of the decision process, not just the result. Over time, the goal is for them to internalize that a well-reasoned decision that turns out wrong is still a good decision, and that deferring to seniority is not the same as good engineering.

**Possible follow-ups:**
- How would you handle it if a decision they own goes badly and they retreat back to deferring, treating the outcome as proof they shouldn't have decided?
- How would you adapt this approach if the senior person they defer to is someone who actively encourages the deference and prefers to make the calls themselves?