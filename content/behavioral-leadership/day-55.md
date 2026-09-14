# behavioral-leadership — Day 55

## Q1: How would you approach a design review where a senior engineer's proposed architecture is technically sound, but the documentation package is too thin for reviewers to evaluate the safety-critical portions — and the engineer is likely to take a request for more detail as a personal criticism?

**Answer:** The first move is to separate the technical merit from the process gap, and to make that separation explicit in how I frame the request. If the architecture is genuinely sound, I would open by acknowledging that — reviewers should not walk away thinking the design is being questioned when the real issue is that the evidence package doesn't let anyone verify the safety-critical claims. I'd reframe the ask away from "your documentation is inadequate" and toward "the review can't do its job without X, Y, and Z," which shifts the conversation from a judgment of the person to a requirement of the review process itself.

Concretely, I'd identify the specific safety-critical items that are unevaluable — for example, a fault-handling path, a watchdog strategy, or a power-loss behavior — and ask for targeted artifacts rather than a wholesale rewrite. A short addendum covering the failure modes and the rationale behind the chosen mitigations is far less threatening than "redo the package." I'd also offer to help scope what "enough detail" looks like, so the engineer isn't guessing at an invisible bar.

If the defensiveness persists, I'd have a private conversation and name the pattern gently: the goal is that a reviewer who wasn't in the room can independently reach the same conclusion the engineer reached. Framing documentation as a service to the *next* engineer — the one who inherits this design, or the auditor who reviews it — tends to land better than framing it as compliance overhead. The review itself should still proceed on the parts that are evaluable, with the thin sections flagged as action items to close before sign-off, so the engineer isn't blocked or publicly embarrassed.

**Possible follow-ups:**
- How would you handle it if the engineer agrees to add detail but the added detail still doesn't let a reviewer verify the safety-critical behavior?
- What would you do if other reviewers start piling on once they sense the package is thin, turning your targeted request into a broader critique?

## Q2: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** I'd treat escalation as a tool with a cost, not a default. The first question is whether the disagreement is actually about *facts* or about *values and priorities*. If it's factual — two engineers disagree about whether a particular approach will meet a timing budget, a thermal limit, or a noise floor — that's resolvable with data, and escalation is usually the wrong move because it outsources a technical question to someone who may be less close to the details. If it's about priorities — one engineer optimizing for schedule, the other for margin or manufacturability — then it may genuinely need a decision-maker above the team, because there's no technical fact that settles it.

Before escalating, I'd try to make the disagreement concrete: what would each engineer need to see to change their mind? Often that surfaces a cheap experiment, a prototype, or a bench measurement that resolves it in a day. If both engineers can agree on the test and the pass/fail criteria in advance, the disagreement usually dissolves on its own.

I'd escalate when the decision has cross-team or cross-functional impact that the two engineers can't legitimately make alone — for example, when it affects a committed schedule, a regulatory submission, or a budget — or when the disagreement has stalled past the point where it's blocking other work. When I do escalate, I'd escalate the *decision*, not the conflict: present the options, the trade-offs, the data, and a recommendation, rather than "these two can't agree." That keeps it a technical decision rather than a personnel problem, and it protects both engineers' standing. I'd also document the outcome and rationale so the decision doesn't get relitigated later.

**Possible follow-ups:**
- How would you handle it if your manager makes a decision that you and both engineers believe is technically wrong?
- What would you do if one of the engineers goes around you and escalates directly, before you've had a chance to resolve it?

## Q3: How would you approach building a cross-functional project timeline for a medical device when the hardware, firmware, and regulatory teams each give different estimates and there's no historical data from similar projects?

**Answer:** With no historical baseline, the honest starting point is that every estimate is a guess with wide error bars, and the timeline should be built to make that uncertainty visible rather than to hide it behind a single number. I'd start by decomposing each team's work into the smallest units that can be estimated independently, because "firmware: 6 months" is unactionable but "sensor driver bring-up, comms stack, power-state machine, integration test" gives something to reason about. Then I'd ask each team not for a single date but for a range — an optimistic, a likely, and a pessimistic — and capture the assumptions behind each.

The next step is to find the dependencies and the integration points, because those are where cross-functional timelines usually break. Hardware and firmware can often proceed in parallel until first-article bring-up; regulatory testing can't start until there's a stable build and a design freeze. Mapping those handoffs usually reveals that the critical path runs through one or two integration events, not through any single team's total effort. I'd build the timeline around those events and treat the individual team estimates as inputs, not as the schedule itself.

Because there's no historical data, I'd explicitly flag the largest unknowns and propose early de-risking — a prototype, a bench feasibility test, a pre-submission conversation with the regulatory body — so that the biggest uncertainties get resolved before they can wreck the schedule. I'd also build in explicit buffers at the integration points rather than padding each team's estimate, since padding everywhere hides where the real risk is. Finally, I'd present the timeline as a living document with named assumptions and a review cadence, so that as real data comes in, the estimates tighten rather than the whole plan being rebuilt from scratch.

**Possible follow-ups:**
- How would you handle it if one team's estimate is dramatically more optimistic than the others, and they resist widening their range?
- How would you communicate the uncertainty in the timeline to an executive who wants a single committed date?

## Q4: How would you approach handling a situation where a team member consistently delivers high-quality technical work but has a pattern of missing internal deadlines, causing downstream delays for the rest of the team?

**Answer:** The instinct is to treat this as a discipline problem, but the first thing to establish is *why* the deadlines are being missed, because the fix depends entirely on the cause. A high-quality engineer who misses internal dates is often optimizing for the wrong thing — they may be treating internal milestones as soft while treating technical correctness as the only real bar, or they may be systematically underestimating their own work, or they may be absorbing unplanned work (helping others, firefighting) that isn't reflected in their commitments. Each of those needs a different response.

I'd start with a private conversation, framed around impact rather than blame: name the specific downstream effects — a tester blocked, an integration window missed — and ask what's happening from their side. Often the engineer doesn't realize the internal date mattered to anyone, because no one ever told them *why* it mattered. Making the downstream dependency visible is frequently enough to change behavior, because the engineer isn't lazy — they just didn't see the cost.

If the cause is estimation, I'd work with them on breaking tasks down and building in explicit checkpoints, so slippage shows up early rather than at the deadline. If the cause is unplanned work, I'd help them protect their committed time and route interruptions elsewhere. If the pattern continues despite a clear conversation, I'd move to a more structured approach — shorter check-in cadence, explicit commitments, and a documented expectation — because at that point it's no longer a misunderstanding. Throughout, I'd keep the framing on the *behavior and its impact*, not on the person's value, since the technical work is genuinely good and I don't want to lose that.

**Possible follow-ups:**
- How would you handle it if the engineer argues that the internal deadlines are arbitrary and that quality matters more than dates?
- What would you do if the rest of the team starts resenting this person and adjusting their own estimates to compensate?

## Q5: How would you approach leading a post-mortem after a medical device project missed its delivery deadline by several months, when morale is low and there's a tendency to blame individual contributors rather than systemic issues?

**Answer:** The single most important thing in a post-mortem like this is to set the ground rules before anyone speaks, because once the conversation turns into blame, it's very hard to pull back. I'd open by stating explicitly that the purpose is to understand the *system* that produced the outcome, not to identify who to punish — and that means we're looking at how decisions were made, what information was available, what incentives existed, and where the process failed to surface problems early. If someone starts naming individuals, I'd redirect to the conditions that made that person's action reasonable at the time.

I'd structure the discussion around a timeline of key decisions and events, built *before* the meeting from documents, emails, and status reports, so the conversation is anchored in facts rather than memory and recrimination. Then I'd walk through it looking for the systemic patterns: were risks identified and then deprioritized? Were estimates challenged? Did bad news travel upward, or was it filtered? Was there a point where someone raised a concern that got overruled, and if so, why? Those questions usually reveal that the miss was the product of several small, individually reasonable decisions, not one person's failure.

I'd also make sure the post-mortem produces concrete, owned actions — not a vague "we'll communicate better" — and that those actions are tracked. And I'd be deliberate about morale: acknowledge the genuine difficulty of the project, recognize the work that *was* done well, and frame the outcome as something the team is now equipped to avoid rather than a verdict on their competence. A post-mortem that ends with people feeling attacked produces defensiveness and hidden problems next time; one that ends with shared understanding and specific changes produces a team that's actually more capable.

**Possible follow-ups:**
- How would you handle it if senior leadership wants a post-mortem that identifies who was responsible, rather than one focused on systemic causes?
- What would you do if the post-mortem reveals that you, as the lead, made one of the key decisions that contributed to the miss?