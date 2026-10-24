# behavioral-leadership — Day 95

## Q1: How would you approach a design review where the presenter's package is technically solid but arrives late and is missing the calculations that justify a safety-critical decision, and the meeting is the only slot before a milestone gate?

**Answer:** The instinct is to either wave it through because the work is good, or cancel the review because the package is incomplete — both are wrong. The milestone gate exists precisely to force a documented decision, so the goal is to make the review useful in the time available rather than to protect the schedule at the expense of the record.

I would start by separating the review into two parts. The first is the part that can be evaluated now: architecture, interfaces, component selection, and the qualitative reasoning behind the safety-critical choice. Reviewers can absolutely assess whether the approach is sound even without the numbers. The second is the missing justification — the trace width, derating, thermal margin, or whatever calculation underpins the safety claim. That part cannot be reviewed, and pretending otherwise is how undocumented safety decisions end up in a design history file.

So I would run the review, capture the substantive findings, and then explicitly record the gap as an open action with an owner and a date, and make the milestone sign-off conditional on that calculation being completed and reviewed by a named second engineer. That keeps the gate meaningful — the decision is documented, the gap is visible, and the risk is owned rather than absorbed silently. If the safety-critical item genuinely can't be dispositioned without the numbers, then the honest answer is that the gate slips, and I'd rather say that in the room than discover it during an audit.

The delivery problem itself is a separate conversation. A package arriving late and incomplete before a gate is a process signal, not a one-off, and I'd want to understand whether it's a workload issue, a misunderstanding of what the package needs to contain, or a habit — because the fix is different in each case.

**Possible follow-ups:**
- If the presenter pushes back and says the calculation exists but just wasn't written up, how do you handle that in the moment?
- How would you make the "conditional sign-off" mechanism credible rather than a rubber stamp that never gets closed out?

## Q2: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode in both directions is the same: the firmware team ends up designing against a mental model of the hardware that doesn't match reality. Oversimplify and they'll assume a clean signal and write filtering that fights the actual noise. Over-detail and they'll disengage and default to whatever the last project did.

I'd frame the constraint in terms of what the firmware can and cannot do about it. For an ADC, that means stating the effective number of bits actually achievable in the real system — not the datasheet figure — the noise floor in LSBs, the sampling rate versus settling trade-off, and which error sources are already handled in hardware versus which are the firmware's problem. For a noisy analog front end, it's the noise spectrum and where it sits relative to the signal of interest, because that determines whether a simple average helps or whether they need something smarter.

The key discipline is to give them a model they can test against, not just a number. If I can hand over a characterization — a noise histogram, a step response, a plot of drift over temperature — they can validate their filter against real data instead of guessing. And I'd make clear which margins are hard limits and which are negotiable, because otherwise everything looks equally rigid and they'll either over-engineer or assume there's slack where there isn't.

Finally, I'd close the loop: ask them to walk back their filtering approach and the assumptions it rests on, so I can catch a mismatch before it's baked into firmware. That conversation is usually where the real misunderstanding surfaces.

**Possible follow-ups:**
- How would you handle it if the firmware team's proposed filter would mask a failure mode the hardware team needs to detect?
- What would you do if the characterization data doesn't exist yet and firmware needs to start now?

## Q3: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** My default is to resolve it within the team, because escalation has a real cost — it takes the decision out of the hands of the people with the most context, it can feel like a verdict on who was right, and it teaches the team that disagreement gets outsourced upward. But "resolve it internally" can't mean "keep talking until someone gives up," so I'd apply a few tests.

First, is the disagreement actually technical, or is it about something else — ownership, credit, or a history between the two people? If it's technical, there's usually a path: define the decision criteria together, agree on what evidence would settle it, and if the evidence doesn't exist, prototype or test to generate it. A disagreement that can be converted into an experiment isn't really an escalation candidate.

Second, does the decision have consequences beyond the team — regulatory exposure, cross-team dependencies, cost, or a commitment already made to a customer? If so, the people who own those consequences need to be in the loop regardless of whether the engineers agree, and that's not escalation, it's just involving the right stakeholders.

Third, is it blocking? A disagreement that's been running for weeks and is holding up a milestone has stopped being productive, and at that point a decision needs to be made by whoever owns the trade-off — which may well be me, not my manager.

If it does need to go up, I'd frame it as a decision request with the options, the trade-offs, and a recommendation, not as "these two can't agree." Handing my manager a clean decision to make is useful; handing them a conflict to referee is not.

**Possible follow-ups:**
- What if one of the engineers goes around you and escalates directly — how do you handle that?
- How do you make sure the engineer whose position wasn't chosen stays engaged afterward?

## Q4: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** The pressure to ship a fix is exactly what makes intermittent failures dangerous, because the fastest-looking fix is often a change that makes the symptom less frequent without touching the cause — and in a medical device that's worse than no fix, because it erodes the ability to detect the problem later.

I'd start by resisting the framing that containment and root cause are in competition. They're sequenced, not opposed. Containment — limiting exposure, adding detection, tightening a screening test — can go out quickly and buys the time to investigate properly, as long as it's labeled as containment and not mistaken for the fix. The mistake is letting containment close the investigation.

For the investigation itself, the first job with an intermittent failure is instrumentation, not hypothesis. If you can't reproduce it, you need the device to tell you what happened when it does occur: logging, counters, error capture, environmental and timing context. I'd define what data would distinguish between the candidate causes before collecting it, so the logs answer a question rather than just accumulating noise. In parallel, I'd go back to the field data and look for the pattern — which units, which conditions, which firmware version, which usage sequence — because intermittency usually has a hidden variable, and the population data often reveals it faster than bench work.

I'd also be explicit about the difference between "we found a plausible mechanism" and "we verified the mechanism explains the observed failures." Those get conflated under schedule pressure. Verification of effectiveness matters here: after the fix, you need evidence the failure rate actually changed, not just that the mechanism is theoretically addressed.

**Possible follow-ups:**
- How do you decide when you've instrumented enough versus when you're just adding telemetry and delaying?
- What would you do if the fix ships and the field failure rate doesn't change?

## Q5: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This pattern is usually not a confidence problem — it's that the engineer has never been given a decision with real consequences attached, so deferring has always been the low-risk move and has never been visibly penalized. Mentoring here means changing what gets rewarded, not just encouraging them to speak up.

I'd start by giving them genuine ownership of a bounded decision — something with real trade-offs and a real outcome, but scoped so a wrong call is recoverable. The important part is that I don't take the decision back. If I ask for their recommendation and then substitute my own, I've confirmed that deferring was correct. I'd ask them to bring the options, the criteria, and a recommendation with reasoning, and then let the recommendation stand unless there's a specific reason it shouldn't — and if there is, say what it is rather than just overriding.

I'd also work on the skill underneath, which is often missing: knowing how to make a decision when the data is incomplete. Strong executors are used to problems with correct answers; design ownership means choosing between defensible options and owning the consequences. That's a separate skill and it needs practice, so I'd walk through decisions together — what would change your mind, what are you optimizing for, what's the cost of being wrong — until they can run that loop themselves.

Over time I'd widen the scope and reduce my involvement, and I'd make a point of publicly crediting their decisions in front of senior people, because part of what's keeping them deferring is an unspoken belief that the senior person's judgment is better. The evidence that it isn't has to come from somewhere.

**Possible follow-ups:**
- What would you do if they make a decision you'd have made differently, but it turns out fine?
- How do you tell the difference between deferring out of habit and deferring because they genuinely lack the context to decide?