# behavioral-leadership — Day 58

## Q1: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** I'd treat escalation as a deliberate choice with a cost, not a default. The first question is whether the disagreement is actually about facts or about values and priorities. If it's a factual question — which approach meets a spec, which has lower risk under a given condition — it can usually be resolved inside the team with data: a bench measurement, a prototype, a review of the standard. Escalation adds little there and can erode the team's sense of ownership. If the disagreement is really about priorities that the team doesn't have the authority to set — schedule versus scope, cost versus margin, a regulatory interpretation that affects the whole program — then it belongs with whoever owns that trade-off, and trying to resolve it internally just delays the inevitable and burns goodwill.

I'd also weigh whether the disagreement is blocking progress. A disagreement that can be parked while both options are explored in parallel doesn't need a decision yet; one that's holding up a design freeze does. Before escalating, I'd make sure both engineers have had a fair hearing, that the options and their trade-offs are written down, and that I can state the decision that needs to be made in one sentence. Escalating a well-framed question is very different from escalating a personality clash. If it's the latter, the manager isn't the right tool — that's a conversation I need to have directly with the individuals.

**Possible follow-ups:**
- What would you do if the manager's decision went against the engineer you thought was right?
- How would you make sure the engineer who "lost" the escalation still felt heard and stayed engaged?

## Q2: How would you approach a design review where a senior engineer's proposed architecture is technically sound, but the documentation package is too thin for reviewers to evaluate the safety-critical portions — and the engineer is likely to take a request for more detail as a personal criticism?

**Answer:** The goal is to get the missing information without turning the review into a referendum on the engineer's competence. I'd separate the two explicitly at the start: state that the architecture looks sound and that the review's purpose is to verify the safety-critical portions, which requires a level of detail the package doesn't yet contain. Framing it as a process requirement rather than a judgment on the work makes it much less personal — the reviewer's job is to evaluate evidence, and if the evidence isn't there, the review can't conclude, regardless of how good the design is.

Concretely, I'd avoid vague requests like "add more detail." I'd name the specific items the reviewers need: the failure-mode analysis for the safety-critical path, the rationale for the chosen redundancy scheme, the calculations behind a particular margin. That turns an open-ended critique into a bounded, actionable list, which is easier to accept and easier to complete. I'd also offer to help — pairing on the safety-critical section, or having a second engineer draft the supporting analysis — so it reads as the team closing a gap together rather than one person being singled out. If the engineer still takes it personally, I'd address that privately afterward, but I wouldn't soften the requirement itself: for a safety-critical design, the documentation is part of the deliverable, not an optional extra.

**Possible follow-ups:**
- How would you handle it if the engineer argued that the safety analysis was "obvious" and didn't need to be written down?
- What would you do if the review had to conclude on a schedule and the documentation couldn't be completed in time?

## Q3: How would you approach building a cross-functional project timeline for a medical device when the hardware, firmware, and regulatory teams each give different estimates and there's no historical data from similar projects?

**Answer:** With no historical data, I'd stop treating the estimates as numbers to be reconciled and start treating them as ranges with stated assumptions. Each team's estimate is only meaningful alongside what it assumes — how many board spins, whether the firmware depends on hardware that doesn't exist yet, how long a regulatory review queue actually is. I'd run a session where each team walks through their assumptions and dependencies, and the disagreements usually turn out to be about different assumptions rather than different competence. That's a much more productive conversation than arguing over whose number is right.

From there I'd build the timeline around the critical path and the unknowns rather than a single date. I'd identify which tasks are genuinely sequential — you can't run compliance testing before the design is frozen — and which can overlap, and I'd attach explicit uncertainty to the items with the least information. For a medical device, regulatory and verification phases are often the ones with the widest ranges and the least controllability, so I'd represent them as ranges, not points. I'd also build in the decision points where the plan can be re-baselined once real data arrives, rather than pretending the first estimate is a commitment. When I present it, I'd be honest that the early version is a planning tool, not a promise, and that the range will narrow as the unknowns resolve.

**Possible follow-ups:**
- How would you communicate a wide range to a stakeholder who wants a single date?
- What would you do if one team's estimate was consistently optimistic across multiple projects?

## Q4: How would you approach handling a situation where a team member consistently delivers high-quality technical work but has a pattern of missing internal deadlines, causing downstream delays for the rest of the team?

**Answer:** The first thing I'd do is resist the assumption that this is a motivation or discipline problem. High-quality work plus missed deadlines often means the person is estimating optimistically, taking on more than they realize, or doing work that's invisible to the schedule — rework, debugging, helping others. I'd look at the pattern before the person: which deadlines slip, by how much, and what's happening in the days before each one. If the slips cluster around a particular type of task, that's a signal about the task or the estimate, not the individual.

Then I'd have a direct conversation, framed around the impact rather than the behavior. The downstream team is blocked, and that's a real cost the person may not be seeing if they're heads-down. I'd ask them to walk me through how they build an estimate and where it tends to go wrong, and we'd adjust together — smaller checkpoints, more explicit buffers, flagging risk earlier rather than at the deadline. The key is to make "I'm going to miss this" a safe and early thing to say, because a late warning is far more damaging than a missed date. If the pattern persists after that, it becomes a performance conversation, but I'd want to have genuinely tried the collaborative route first, especially with someone whose technical work is strong.

**Possible follow-ups:**
- How would you handle it if the person insisted their estimates were fine and the problem was elsewhere?
- What would you do if the downstream team started routing around this person?

## Q5: How would you approach leading a post-mortem after a medical device project missed its delivery deadline by several months, when morale is low and there's a tendency to blame individual contributors rather than systemic issues?

**Answer:** The tone of a post-mortem is set in the first few minutes, so I'd be explicit about the ground rules up front: we're here to understand what happened to the system, not to assign fault to people. That's not just kindness — blame produces defensiveness, and defensive people withhold the information the post-mortem needs to be useful. I'd frame it as: the schedule slipped, and the only way that's valuable is if we learn something that changes how we work next time. If someone made a decision that turned out badly, the useful question is what information or process would have led to a different decision, not who to punish.

Structurally, I'd build a timeline of the project's key decisions and events, and mark where the plan and reality diverged. Then I'd look for patterns across those divergences — were the estimates optimistic across the board, was there a dependency nobody owned, did a late requirement change cascade? I'd use a simple causal tool like a fishbone or a set of "why" chains to push past the first plausible explanation, because the first one is usually a symptom. I'd keep the discussion on the system and the process, and I'd make sure the output is a small number of concrete, owned changes rather than a long list of vague lessons. Finally, I'd acknowledge the team's effort honestly — a missed deadline doesn't erase the work — because morale is part of what determines whether the next project goes better.

**Possible follow-ups:**
- How would you handle it if a senior leader wanted to name individuals in the post-mortem?
- How would you make sure the action items from the post-mortem actually get implemented rather than filed away?