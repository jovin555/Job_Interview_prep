# behavioral-leadership — Day 97

## Q1: How would you approach a design review where the presenter is technically strong but the review package arrives late and is missing the calculations that justify a safety-critical decision, and the meeting is the only slot before a milestone gate?

**Answer:** The first thing I'd do is separate the two problems: the process failure (late, incomplete package) and the technical risk (an unjustified safety-critical decision). They need different handling, and conflating them usually makes both worse.

On the process side, I'd treat the late package as a real issue to raise — but not in the room, in front of everyone, and not as a personal criticism of the presenter. A review where the package arrives late is a review where reviewers can't do their job properly, and that's worth a short, factual note afterward: what was missing, why it mattered, and what the expectation is for the next gate. The goal is to make the standard visible, not to embarrass anyone.

On the technical side, I would not let the meeting become a rubber stamp just because the milestone is close. For a safety-critical decision, the calculation is the evidence — without it, the review can't actually verify the decision, only hear it asserted. So I'd run the meeting on what *can* be reviewed: the architecture, the interfaces, the assumptions the calculation rests on. I'd ask the presenter to walk through the reasoning and the inputs, and I'd capture the missing calculation as a formal action item with an owner and a date. If the milestone gate genuinely requires that calculation to be closed, then the honest outcome of the review is "conditionally approved pending the calculation" — not "approved." I'd rather surface that at the gate than discover it later.

The key judgment is whether the missing calculation is a documentation gap or a genuine unknown. If the presenter can explain the reasoning and the numbers exist but weren't written up, that's a fast close. If the reasoning itself is shaky, that's a different conversation and the gate should reflect it.

**Possible follow-ups:**
- How would you handle it if the presenter pushes back and says the calculation is "obvious" and doesn't need to be written down?
- What would you do if the milestone gate owner pressures you to approve anyway to keep the schedule?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures are where teams most often skip straight to a plausible fix and call it done, so the first discipline is to resist that — but without turning the investigation into an open-ended science project while the schedule burns.

I'd start by being explicit about what we actually know versus what we're assuming, and get the team to agree on that list. Then I'd work the problem from two directions at once. From the data side: what do the failure reports have in common — environmental conditions, operating mode, time since power-on, specific units or batches, firmware version? Even a handful of reports can reveal a pattern if you tabulate the variables instead of reading them as anecdotes. From the mechanism side: build a fishbone across the plausible categories — hardware, firmware, power, environment, test setup, user interaction — and for each branch ask what evidence would confirm or rule it out. The branches that can be cheaply tested get tested first.

Because it's intermittent, I'd invest early in *capture* rather than guessing: instrumentation, logging, stress conditions that widen the operating envelope, and a way to catch the failure in the act. A failure you can trap is worth more than ten theories. In parallel, I'd apply containment — something that limits the impact or the blast radius while the investigation runs — and be clear with stakeholders that containment is not the fix.

On the pressure to ship: I'd separate "ship a fix" from "close the investigation." If a targeted mitigation is low-risk and reversible, it can go out as containment with the investigation continuing. What I would not do is declare root cause found on the basis of "we changed something and it hasn't recurred yet" — that's the classic trap, because an intermittent failure that hasn't recurred hasn't been shown to be fixed. Verification of effectiveness needs a defined test and a defined observation window before anyone calls it closed.

**Possible follow-ups:**
- How would you decide when you've done enough investigation to ship a corrective action versus continuing to dig?
- What does "verification of effectiveness" look like for a failure you can't reproduce on demand?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode I try to avoid is handing the firmware team a number without a meaning, or a lecture without an action. What they need is: what the constraint is, where it comes from, what it means for their code, and what they can and can't do about it.

I'd frame it as a budget. For something like ADC resolution and a noisy front end, the useful translation is a signal-chain budget: here's the sensor's output range, here's the noise floor of the analog front end, here's the effective resolution you can actually rely on after that noise, and here's the margin left for your filtering and your decision thresholds. That turns "the ADC is noisy" into "you have this much usable dynamic range, and here's the part of it that's already spent before your code runs." Firmware engineers can reason about a budget; they can't reason about a vague complaint.

I'd also be concrete about the *implications* rather than the physics: which measurements are affected, at what rates, and what the analog side has already done about it (filtering, averaging, reference stability, layout). And I'd be honest about what's fixed and what's negotiable — if the hardware can't change, say so plainly so the firmware team doesn't spend a week trying to solve it in software; if there's a hardware change that would help, name it and its cost.

The other half is listening. The firmware team often knows things about the real signal behavior that the analog designer doesn't — what the sensor looks like in the field, what the user does, what the timing actually is. A good translation is a two-way conversation, not a spec handoff. I'd want them to come back with "given that budget, here's the filter and here's the threshold we'd propose, and here's where we think the budget is too tight."

**Possible follow-ups:**
- How would you handle it if the firmware team proposes a software filter that you believe is masking a hardware problem rather than solving it?
- How would you document that signal-chain budget so it survives beyond the current team?

## Q4: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** My default is to resolve it within the team, because escalation has a cost — it takes the decision out of the hands of the people closest to the problem, and it can set a pattern where every hard disagreement gets kicked upward. But "resolve it within the team" doesn't mean "hope they work it out." It means I actively run a process to get to a decision.

The first question I'd ask is whether the disagreement is actually technical or whether it's become personal. If it's technical, the path is usually to make it empirical: what data would distinguish the two positions, can we prototype or test to get that data, and if we can't, what are the decision criteria — risk, schedule, cost, maintainability, regulatory impact? If both options are genuinely viable, someone has to own the call, and I'd rather that be a documented decision with rationale than a stalemate. If it's become personal, escalation won't fix it either; the real work is separating the people from the positions.

I'd escalate when one of a few things is true: the decision genuinely exceeds my authority or the team's scope (budget, headcount, a cross-team dependency); the disagreement is blocking work and the team can't converge despite a real attempt; there's a risk or compliance dimension that needs a level of sign-off above me; or the two engineers have a pattern of deadlock that's costing the team more than the decision is worth. In those cases I'd escalate *with* a recommendation and a summary of both positions, not just dump the conflict upstairs — that's what makes escalation useful rather than just a punt.

The thing I'd avoid is escalating to avoid making a call myself. If it's my call to make, I should make it, document why, and own it.

**Possible follow-ups:**
- How would you handle it if you escalate with a recommendation and your manager decides the other way?
- What would you do if the two engineers keep re-litigating a decision after it's been made?

## Q5: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This is a common and often under-diagnosed pattern — the engineer isn't lacking skill, they're lacking *practice* at owning a decision, and the deference is usually a rational response to never having been given real ownership. So the mentoring has to create safe, bounded opportunities to own something, not just encourage them to "speak up more."

I'd start by giving them a decision that's genuinely theirs — small enough that a wrong call is recoverable, but real enough that it matters. Something with a clear scope, a defined decision to make, and a review where they present the recommendation and the rationale rather than deferring to me. The point is to move them from "executing a decision someone else made" to "making the call and defending it." I'd be explicit that I want their recommendation first, before I offer mine, so the default isn't "wait for the senior person to speak."

In reviews and meetings, I'd actively redirect the deference. When a question comes to me that's really theirs, I'd hand it back — "that's your call, what do you think?" — and then support the answer rather than immediately improving on it. That last part matters: if every time they venture an opinion I refine it, they learn that venturing opinions is pointless. I'd save my refinements for a private debrief.

I'd also work on the *reasoning* side, not just the confidence side. A lot of deference comes from not having a structured way to reason about a decision under uncertainty, so we'd practice that: how do you frame the options, what are the criteria, what would change your mind, how do you decide when the data is incomplete. That gives them something to stand on when they're the least senior person in the room.

And I'd be patient about the timeline. Ownership is a habit built over months of small successes, and the measure of progress is that they start making calls without checking first — not that they become the loudest person in the room.

**Possible follow-ups:**
- How would you handle it if they make a call you disagree with — do you let them own the outcome?
- How would you tell the difference between deference that's a confidence issue and deference that's a genuine judgment gap?