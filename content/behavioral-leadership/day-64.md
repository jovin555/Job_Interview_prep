# behavioral-leadership — Day 64

## Q1: How would you approach a design review where the presenter is a strong engineer but has a history of becoming defensive when their work is questioned, and you need the review to be genuinely critical to be useful?

**Answer:** The defensiveness is usually a symptom of the review feeling like a verdict on the person rather than on the design, so the first move is to change what the review is *about*. Before the session, I'd frame it explicitly: the goal is to find the failure modes the designer can't see from inside their own head, and a review that produces no objections is a wasted review, not a compliment. I'd also separate the roles — the presenter walks through the design, but I'd ask them to lead with the parts they're least sure about, which reframes uncertainty as professional rigor rather than weakness.

During the review, I'd model the behavior I want. Instead of "why did you do it this way?", which reads as an accusation, I'd use "walk me through the trade-off between X and Y here" or "what would have to be true for this to fail?" That keeps the focus on the design space rather than the designer's judgment. I'd also make sure the first several comments are genuinely substantive rather than nitpicks, because a presenter who gets buried in cosmetic feedback early will armor up for the rest of the session.

If the defensiveness still shows up — a curt answer, a "that's already handled" that isn't — I wouldn't escalate in the room. I'd note it, keep the review moving, and follow up one-on-one afterward to separate the technical content from the interpersonal friction. Often the defensiveness is about a specific past experience or a fear that the review is a performance evaluation in disguise. Naming that privately, and being clear that raising a concern is a contribution rather than an attack, does more than anything I could say in front of the group.

Structurally, I'd also make sure action items are captured with owners and a follow-up date, so the review ends with a shared artifact rather than a vague sense of having been criticized. That gives the presenter something concrete to respond to and a reason to see the review as useful.

**Possible follow-ups:**
- What would you do if the defensiveness persisted across multiple reviews despite your efforts?
- How would you handle it if another reviewer in the room was the one triggering the defensiveness, rather than the presenter?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures are the hardest case because the pressure to ship a fix is highest exactly when the evidence is thinnest, and a fix based on a guess tends to either mask the symptom or introduce a new one. The first thing I'd do is resist the urge to jump to a solution and instead invest in making the failure *observable*. That usually means instrumentation: adding logging, counters, or a way to capture state at the moment of failure, so that when it does occur, we get data instead of a shrug. If the failure is rare, I'd also try to increase the failure rate deliberately — stress the system, run it at temperature extremes, cycle power, vary timing — to turn a rare event into a reproducible one.

In parallel, I'd structure the investigation so it doesn't depend on a single hypothesis. A fishbone or Ishikawa-style breakdown forces the team to enumerate categories — timing, power, thermal, mechanical, firmware state, environmental — rather than anchoring on the first plausible cause. From there, 5 Whys can drill into the most likely branches, but I'd be careful not to treat it as a ritual; the value is in the discipline of asking "and why would that happen?" until you hit something you can actually test.

Containment is separate from correction. If the pressure is real, I'd ship a containment — a workaround, a guard, a conservative default — while being explicit that it's containment and not a root-cause fix. That buys time without pretending the problem is solved. The corrective action only goes in once we've verified the mechanism, and verification means we can predict when the failure should and shouldn't occur, then confirm that prediction.

The last piece is verification of effectiveness. A fix that makes the symptom disappear isn't proof; the proof is that the failure mode is gone under conditions that previously triggered it. If we can't reproduce the failure at all, we document the reasoning, the evidence, and the residual uncertainty, and we keep monitoring in the field.

**Possible follow-ups:**
- How would you decide when to stop investigating and accept a containment as the permanent solution?
- What would you do if the intermittent failure only appeared in the field and never in the lab, despite your best efforts to reproduce it?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode on both sides is the same: the firmware team ends up either treating the hardware as a black box and writing code that fights it, or getting a data dump that they can't turn into a decision. The bridge is to translate the constraint into the *behavior* it produces, not just the number. "12-bit ADC" is not actionable; "at the bottom of the range, one LSB is roughly X microvolts, and the front end has about Y microvolts of noise, so the last two bits are effectively noise and you should treat anything below that as dither" is actionable.

I'd start by characterizing the analog front end honestly — noise floor, effective number of bits, settling time, any nonlinearity near the rails — and then express those in terms the firmware can use: how many counts of noise to expect, how long to wait after a channel switch before the reading is valid, what the minimum meaningful change is. If there's a filter or an averaging scheme that the hardware already provides, I'd say so explicitly, because otherwise the firmware team will add their own and the two will interact badly.

I'd also give them a way to verify. A simple test — short the input, sample a few thousand points, look at the distribution — lets the firmware team confirm the noise behavior themselves rather than taking my word for it. That turns the constraint from a claim into a shared observation, which is much more durable when someone later questions why the code does what it does.

Finally, I'd keep the interface documented. The firmware team shouldn't have to reverse-engineer the analog behavior from the schematic. A short note — what the signal looks like, what the noise looks like, what timing is required — is worth more than a long one, as long as it's accurate and it's kept current when the hardware changes.

**Possible follow-ups:**
- How would you handle it if the firmware team's proposed filtering scheme would actually make the noise problem worse?
- What would you do if the hardware constraint turned out to be worse than the datasheet suggested, after the firmware was already written against the optimistic numbers?

## Q4: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** The default should be to resolve it within the team, because escalation has a cost — it takes the decision out of the hands of the people closest to the problem, it can feel like a verdict on who was right, and it sets a precedent that disagreements get punted upward. But "resolve it within the team" doesn't mean "let it drag on." The question is whether the team has a path to a decision, not whether the disagreement exists.

I'd first check whether the disagreement is actually technical or whether it's about something else — scope, ownership, a past decision one of them feels was overridden. If it's technical, the path is usually to make the disagreement concrete: what would each approach do under the conditions we care about, and can we test it? A prototype, a bench measurement, or even a back-of-envelope calculation often collapses the argument faster than another meeting. If the disagreement is about values or priorities — safety margin versus schedule, for example — that's not something the two engineers can resolve on their own, and it may need a decision-maker.

I'd escalate when the team has genuinely exhausted its own options: the disagreement is blocking progress, both positions are defensible, and the decision has consequences beyond the team's scope — cost, regulatory posture, a cross-team dependency. In that case I'd escalate with a clear framing: here are the two options, here's the trade-off, here's what we'd need to decide, and here's my recommendation if asked. Escalating with a recommendation is very different from escalating with a problem.

What I'd avoid is escalating to avoid the discomfort of the conversation, or letting a disagreement fester because neither engineer wants to be the one to back down. Both of those are failures of leadership, not of the engineers.

**Possible follow-ups:**
- How would you handle it if the two engineers agreed to a decision in the room and then one of them continued to argue against it afterward?
- What would you do if your manager's decision went against your own technical judgment?

## Q5: How would you approach building a cross-functional project timeline for a medical device when the hardware, firmware, and regulatory teams each give different estimates and there's no historical data from similar projects?

**Answer:** The absence of historical data is the real problem, not the disagreement between teams. Each team's estimate is probably reasonable from where they sit, but they're estimating different things — hardware is thinking about design and layout, firmware is thinking about bring-up and integration, regulatory is thinking about test cycles and documentation — and none of them is accounting for the dependencies between those phases. So the first step is to get the estimates into a common structure: what are the actual work packages, what does each one depend on, and what's the critical path?

I'd build the timeline from the dependencies rather than from the estimates. If regulatory testing can't start until hardware is frozen, then the regulatory estimate is bounded by the hardware estimate, and the two can't be treated as independent. That usually surfaces the real risk: not that one team is slow, but that a slip in one phase cascades into another. I'd also separate the estimate from the uncertainty — a range is more honest than a point estimate when there's no historical data, and it gives stakeholders something to plan against.

For the unknowns, I'd identify the assumptions each team is making and flag the ones that are load-bearing. If the firmware estimate assumes the hardware is stable by a certain date, and the hardware estimate assumes a component is available, those assumptions need to be visible, because they're where the schedule will actually break. I'd also build in explicit checkpoints where we re-estimate based on what we've learned, rather than treating the initial timeline as fixed.

Communicating this to stakeholders means being clear about what's known, what's assumed, and what's uncertain — without either overpromising or hiding behind the uncertainty. A timeline that says "we'll know more after the first prototype" is more useful than one that pretends to precision it doesn't have.

**Possible follow-ups:**
- How would you handle it if one team's estimate was consistently optimistic across multiple projects, and you had no authority over that team?
- What would you do if a stakeholder insisted on a single delivery date despite the uncertainty you'd flagged?