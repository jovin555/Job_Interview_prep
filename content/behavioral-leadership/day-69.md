# behavioral-leadership — Day 69

## Q1: How would you approach a design review where the presenter has done solid technical work but the review package arrives late, is missing key calculations, and the meeting is the only slot before a milestone gate?

**Answer:** The instinct is to either cancel the review or push through on the strength of the presenter's reputation, and both are wrong for different reasons. Cancelling signals that the milestone matters less than the calendar; pushing through on trust defeats the purpose of a review, which is to have independent eyes on the reasoning, not to ratify the author.

I would start by separating two questions: is the *design* ready to be reviewed, and is the *package* ready to be reviewed? They're not the same. If the design is genuinely at a reviewable state but the documentation is thin, the right move is usually to run a scoped review — explicitly limited to the portions where the package is complete enough to evaluate — and schedule a follow-up for the rest, with the milestone gate conditioned on that follow-up rather than on today's meeting. That keeps the schedule honest without pretending the missing material doesn't matter.

In the meeting itself, I'd be explicit about what is and isn't being reviewed, so nobody leaves with a false sense that the whole design has been scrutinized. For the missing calculations, I'd ask the presenter to walk through the reasoning verbally and capture it as an action item to be written up and circulated — verbal reasoning in a review is a starting point, not a substitute for a documented calculation, especially for anything safety-related.

The harder conversation is with the presenter, and it should happen privately and without moralizing. A late, incomplete package is usually a symptom — overcommitment, a milestone that was never realistic, or a belief that reviews are a formality. I'd ask what happened rather than assume, and then make the expectation concrete: what "review-ready" means for this team, and how much lead time the package needs. If the same person is repeatedly late, that's a process problem to solve, not a character flaw to name.

**Possible follow-ups:**
- If the milestone owner insists the gate must pass today regardless, how would you handle that pressure without either caving or becoming the blocker?
- How would you decide which portions of a design are safe to review on verbal reasoning alone versus which absolutely require written calculations first?

## Q2: How would you approach structuring a root-cause investigation when the failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures under schedule pressure are where teams most often ship a fix that makes the symptom go away without understanding the cause — and in a regulated device that's a serious liability, because the same root cause can resurface in a different failure mode later.

The first discipline is to resist the framing that "we can't reproduce it" means "we can't investigate it." It usually means the reproduction conditions aren't understood yet. So the early work is characterization, not fixing: under what conditions does it appear — temperature, supply voltage, specific operating sequence, particular unit, particular firmware build, time since power-on? Even a handful of correlated observations narrows the search space enormously. I'd want the team capturing data continuously on the affected units rather than waiting to catch the failure live, because intermittent problems are often only visible in logs or traces after the fact.

Second, I'd separate containment from correction. Containment is legitimate and often necessary under pressure — a workaround, a screening test, a tightened incoming inspection — but it must be labeled as containment, with a clear statement that the root cause is still unknown and the corrective action is still open. The failure mode I want to avoid is containment quietly becoming the fix because the schedule moved on.

Third, I'd structure the investigation so it can proceed in parallel rather than serially: one thread on the most likely hardware contributors, one on firmware timing or state-machine paths, one on the manufacturing or environmental variables. Fishbone or a fault tree helps here not as ceremony but because it forces the team to name the hypotheses they're implicitly ruling out. Each hypothesis gets a test, even a cheap one, and the results get written down — because with intermittent failures, the team's memory of "we already checked that" is unreliable.

Finally, I'd be honest with stakeholders about the difference between "we have a containment" and "we understand the cause." Those are different risk postures, and the schedule decision should be made with that distinction visible rather than blurred.

**Possible follow-ups:**
- How would you decide when you've gathered enough characterization data to commit to a corrective action, versus continuing to investigate?
- If the intermittent failure only appears in the field and never on the bench, what instrumentation or field-data strategy would you put in place?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode in both directions is real. Oversimplify and the firmware team makes design choices that assume more headroom than exists; bury them in analog detail and they disengage and treat the constraint as someone else's problem.

I'd start from what the firmware team actually needs to decide, and work backward. They don't need the full noise analysis; they need to know the effective resolution they can rely on, the frequency content of the noise, and where the signal sits relative to the noise floor. Those three things determine almost every firmware decision that follows — filter design, averaging window, threshold margins, whether a particular measurement is even feasible at the required rate.

So the translation is: state the constraint as a budget the firmware can spend, not as a circuit description. "You have roughly this many effective bits at this sample rate, with noise concentrated in this band" is actionable. "The front end has a noisy reference and the layout isn't ideal" is not.

I'd also want to be explicit about what's fixed and what's negotiable. If the analog front end can be improved — better filtering, a cleaner reference, a layout change — that's a different conversation than if the hardware is frozen and firmware has to live within it. Making that boundary clear prevents the firmware team from either assuming they can ask for hardware changes that won't happen, or accepting a constraint that could actually be relaxed.

Where it gets genuinely collaborative is when the constraint interacts with a firmware choice. If the firmware wants a faster sample rate for a control loop, that trades against effective resolution — that's a joint decision, not a handoff. I'd want that conversation to happen with both sides looking at the same numbers, ideally with a shared measurement or a quick characterization run, rather than each side arguing from its own assumptions.

**Possible follow-ups:**
- How would you handle it if the firmware team pushes back that the constraint is a hardware problem they shouldn't have to design around?
- What would you put in writing so the constraint survives beyond the people in the room — a spec, a test, something else?

## Q4: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This is a common and often under-diagnosed pattern. The engineer isn't lacking capability — they're lacking the experience of being the person who has to commit to a decision and live with the consequences. Deferring to seniority is a rational strategy when you've never been accountable for the outcome, and it's reinforced every time someone more senior answers the question for them.

The first move is to stop answering for them. In design discussions, when a decision lands in their area, I'd redirect the question back — not as a test, but genuinely: "What's your read?" And then let the answer stand, even if it's not the one I'd have given, as long as it's defensible. The learning happens in owning the call, not in watching someone else make it.

The second move is to give them a decision with real stakes and real support. Not a trivial one, and not one where I've already decided the answer. Something where the trade-offs are genuine and the outcome matters. I'd make clear upfront that I'm available to think through it with them, but that the decision is theirs and I'll back it. That combination — real ownership plus a safety net — is what builds the muscle.

The third move is to make the reasoning visible after the fact. Once a decision has played out, whether it worked or not, I'd walk through it with them: what signals did you weigh, what would you do differently, what did you learn that you couldn't have known beforehand? That reflection is where execution strength turns into judgment.

I'd also watch for the case where the deference is a symptom of something else — a team culture where only senior voices are heard, or a manager who punishes wrong calls. If the environment doesn't tolerate a junior engineer being wrong occasionally, no amount of mentoring will fix the behavior, because the behavior is correct for the environment.

**Possible follow-ups:**
- How would you handle it if the engineer makes a decision you disagree with, and it turns out to be wrong — how do you support them without undermining the lesson?
- What would you do if the deference is coming from the team culture rather than the individual?

## Q5: How would you approach deciding how much technical detail to include when presenting a design trade-off to a mixed audience of engineers, a quality manager, and a product manager in the same room?

**Answer:** The temptation is to aim for the middle — enough detail to satisfy the engineers, not so much that the others tune out — and that usually produces a presentation that satisfies nobody. The better approach is to structure the presentation in layers, so each audience can engage at the depth they need without the others being held hostage.

I'd lead with the decision itself and its consequences: what we're choosing between, what each option costs in schedule, risk, and performance, and what I'm recommending and why. That's the layer everyone needs, and it should be comprehensible without any of the technical detail. A product manager needs to understand the schedule and risk implications; a quality manager needs to understand the safety and compliance implications; both need to know what's being asked of them.

Then the technical detail goes in a second layer, clearly marked as such — the reasoning behind the performance numbers, the assumptions, the things that could change the conclusion. Engineers will engage with this; the others can note that it exists and come back to it if a specific point matters to their decision. Putting it in an appendix or a backup slide rather than the main flow keeps the main narrative clean.

The key discipline is being honest about uncertainty in a way that's useful to all three audiences. "This estimate assumes X, and if X doesn't hold the schedule moves by roughly Y" is meaningful to a product manager. "The noise margin is tighter than I'd like at the temperature extremes" is meaningful to a quality manager. Neither requires the full analysis to be useful, but both require me to have done the analysis and to be willing to state its limits plainly.

I'd also resist the urge to soften a recommendation to avoid conflict. A trade-off presentation that doesn't actually recommend anything forces the room to make a decision without the benefit of the analysis, which is worse than a recommendation that gets overruled.

**Possible follow-ups:**
- How would you handle it if the quality manager asks a deeply technical question that the engineers in the room could answer but you want to keep the meeting on track?
- If the product manager pushes for a schedule commitment that the technical analysis doesn't support, how do you respond in the room?