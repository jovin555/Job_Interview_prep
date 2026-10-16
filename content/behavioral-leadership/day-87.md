# behavioral-leadership — Day 87

## Q1: How would you approach a design review where the presenter has done solid technical work, but the review package arrives late and is missing the calculations that justify a safety-critical decision, and the meeting is the only slot before a milestone gate?

**Answer:** The first move is to separate the two problems: the quality of the work and the quality of the package are not the same thing, and conflating them either punishes good engineering or lets a documentation gap slide because the engineer is trusted. I would open the review by acknowledging the time constraint explicitly, so nobody pretends the missing calculations don't matter, and then propose a split: proceed with the review of everything that can be evaluated now — architecture, interfaces, component selection, test approach — and formally defer sign-off on the safety-critical item until the calculations are in the package. A milestone gate is a checkpoint, not a verdict; it's legitimate to record "reviewed with open action items" as long as the open items are specific, owned, and dated, and as long as the gate owner agrees that the safety-critical item cannot be closed without them. What I would not do is let the meeting quietly approve the item by omission, because that's how undocumented safety rationale ends up in a design history file that later fails an audit or, worse, hides a real design error.

I'd also treat the late package as a process signal rather than a personal failing. If this is a one-off, a short conversation about what happened is enough. If it's a pattern, the fix is structural — a review-readiness checklist with a defined cutoff, so the expectation isn't "bring whatever you have" but "the package is complete enough to review two days before the meeting." That protects the presenter too: it gives them a legitimate reason to push back on being scheduled before they're ready.

**Possible follow-ups:**
- If the milestone owner insists on full sign-off today and won't accept a conditional pass, how would you handle that?
- How would you decide which missing calculations are truly blocking versus nice-to-have for the review to proceed?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures are where pressure and good methodology collide hardest, because the temptation is to ship the most plausible fix and move on. The discipline I'd apply is to separate containment from correction from the start, and to be explicit with stakeholders that these are different things with different timelines. Containment — a watchdog, a retry, a derated operating mode, a firmware guard — can often go out quickly and buys time without claiming to have solved anything. Correction requires an actual root cause, and an intermittent failure by definition means you don't have one yet.

For the investigation itself, the first priority is turning an intermittent failure into a measurable one. That usually means instrumentation rather than guesswork: adding logging around the suspect subsystem, capturing the state at the moment of failure, and widening the capture window so you catch the lead-up rather than just the symptom. If the failure correlates with something — temperature, supply voltage, a particular sequence of user actions, time since power-on, a specific unit or lot — that correlation is the thread to pull. If it doesn't correlate with anything observable yet, the honest answer is that the instrumentation is insufficient, and improving it is the next task, not a distraction from it.

I'd also resist the pull toward a single hypothesis too early. A fishbone pass across hardware, firmware, environment, and manufacturing is cheap and keeps the team from anchoring. And I'd insist that whatever fix is eventually proposed gets a verification-of-effectiveness step — a defined way to demonstrate the failure rate actually dropped, not just that it hasn't recurred in the last few days. "We haven't seen it since" is not evidence; it's the absence of evidence, and on an intermittent issue that distinction matters.

**Possible follow-ups:**
- How would you communicate to a product manager that containment is going out but the root cause is still unknown?
- What would make you decide the investigation has hit diminishing returns and the right move is a design change rather than continued diagnosis?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode on both sides is the same: the firmware team gets told "the analog front end is noisy" and either over-corrects with heavy filtering that destroys response time, or under-corrects and blames the hardware when the readings are bad. The way out is to hand over a characterization, not an adjective. That means a small set of concrete numbers the firmware team can design against: the noise floor in LSBs or volts at the relevant bandwidth, the effective resolution after averaging, the settling time of the front end after a channel switch or a wake-up event, and the sample rate the hardware can actually sustain without the readings degrading. Those numbers turn a vague constraint into a design space.

I'd also frame it in terms of what the firmware is allowed to assume and what it must not. For example: "You can assume the reading is stable within X after Y milliseconds of settling; you cannot assume two consecutive samples are independent, because the front end has a low-pass characteristic." That kind of statement is more useful than a filter recommendation, because it lets the firmware team choose its own approach while staying inside the real limits. Where there's a genuine trade-off — say, more averaging buys resolution but costs latency — I'd present it as a curve or a small table rather than picking for them, unless the system-level requirement already fixes the answer.

The other half is making sure the hardware team owns its side. If the front end is noisier than it needs to be, the right response isn't to teach firmware to filter around a hardware problem — it's to fix the hardware and tell firmware the new numbers. Translating a constraint well includes being honest about which constraints are inherent and which are just current.

**Possible follow-ups:**
- How would you handle it if the firmware team's filtering choice then degrades a different requirement, like alarm response time?
- What documentation would you leave behind so this characterization doesn't have to be redone by the next person?

## Q4: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This pattern usually isn't a confidence problem — it's that the engineer has never been in a position where the decision was actually theirs, so deferring has been the correct behavior their whole career. The mentoring move is to change the structure, not to give pep talks. That starts with handing over genuine ownership of something bounded: a subsystem, a component selection, a test approach — with the explicit understanding that they make the call and defend it, and that I will not override them in the room even if I'd have chosen differently. If I do disagree, I raise it the same way any other reviewer would, and let them decide.

The second piece is rehearsing the decision, not just making it. Before a design review, I'd have them walk me through the trade-offs and the rationale as if I were the skeptical reviewer, and I'd push on the weak points specifically. The goal is that by the time they're in the room, they've already heard the hard questions once. Over time, the training wheels come off — fewer rehearsals, larger scope, more visibility to senior stakeholders.

I'd also watch for the moment they defer in a meeting and name it afterward, privately: "You had the data on that one — what stopped you from saying so?" Sometimes the answer is a real gap in their knowledge, which is useful to know. Sometimes it's just habit, and pointing it out once or twice is often enough to break it. What I'd avoid is publicly putting them on the spot to force them to speak up, because that tends to produce either silence or a defensive answer, neither of which builds the muscle.

**Possible follow-ups:**
- How would you handle it if a senior engineer in the room keeps answering for them despite your having set up the ownership?
- How would you know the mentoring is working — what would you look for over a few months?

## Q5: How would you approach leading a technical decision when the team is split between two viable architectures and the disagreement has become personal rather than technical, with each side attributing bad motives to the other?

**Answer:** Once a disagreement turns personal, the technical merits are no longer the thing driving the decision — the identity of who proposed what is. The first job is to de-escalate the framing before trying to resolve the substance, because a decision made while people are defending their competence rather than their design will be contested no matter which way it goes. Practically, that means resetting the conversation around criteria rather than proposals: what does the system actually need to do, what are the hard constraints, and what would make each option fail? If both sides can agree on the evaluation criteria before re-arguing the options, the discussion usually gets less personal on its own, because the argument shifts from "your design is wrong" to "this criterion is or isn't met."

The second move is to convert opinion into evidence wherever the disagreement is actually empirical. A lot of architecture disputes that feel like matters of judgment are really matters of fact that nobody has measured — power consumption, latency, cost at volume, bring-up risk, how much firmware complexity each option implies. A short prototype or a bench measurement on the contested point often resolves more than another meeting. Where the disagreement is genuinely about values rather than facts — say, simplicity versus flexibility — that's a legitimate thing to disagree about, and the right move is to make the trade-off explicit and let a named decision-maker choose, with the rationale documented so the losing side isn't left feeling overruled by fiat.

I'd also be direct with the individuals involved, separately. If someone is attributing bad motives to a colleague, that's a behavior issue distinct from the technical one, and it needs to be named rather than worked around. The architecture decision will eventually be made; the working relationship has to survive it.

**Possible follow-ups:**
- What would you do if the two engineers are both senior to you and neither accepts your framing of the criteria?
- How would you document the decision so that the losing side's concerns are preserved rather than erased?