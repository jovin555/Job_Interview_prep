# behavioral-leadership — Day 53

## Q1: How would you approach a design review where a senior engineer's proposed architecture is technically sound, but the documentation package is too thin for reviewers to evaluate the safety-critical portions — and the engineer is likely to take a request for more detail as a personal criticism?

**Answer:** The first move is to separate the technical merit of the architecture from the completeness of the review package, and to make that separation explicit out loud. I'd open by affirming what the design gets right — if the architecture is sound, saying so plainly removes the implication that the request for detail is a verdict on the engineer's competence. Then I'd reframe the gap as a property of the review process rather than of the person: a design review can only discharge its responsibility if reviewers can independently trace the safety-critical paths, and that's true regardless of who authored the package. Framing it as "the review can't sign off on what it can't see" moves the conversation from judgment to process.

Practically, I'd avoid a vague "add more detail" request, which reads as criticism and is also unactionable. Instead I'd name the specific artifacts the review needs — for a safety-critical subsystem, typically the failure-mode reasoning, the rationale for key component and margin choices, and the traceability from requirement to implementation to verification evidence. Giving a concrete, bounded list signals that this is a checklist item, not a referendum on the engineer's ability. I'd also offer to help scope it, or to have a second reviewer work through the safety-critical sections alongside them, so the extra work is shared rather than assigned.

If the defensiveness persists, I'd take it offline rather than let it play out in front of the room, and try to understand what's underneath it — often it's time pressure, or a belief that documentation is bureaucratic overhead rather than engineering. That's a longer conversation about why the documentation exists: not to satisfy a process, but because a reviewer, an auditor, or a future maintainer has to be able to reconstruct the safety argument without the original author present. I'd keep the standard firm while keeping the delivery low-friction.

**Possible follow-ups:**
- What would you do if the engineer agrees to add detail but the revised package still doesn't let reviewers evaluate the safety-critical portions?
- How would you handle it if other reviewers start treating the thin package as acceptable because the architecture "looks fine"?

## Q2: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** The default should be to resolve it within the team, because escalation that could have been avoided erodes the team's ownership and trains people to route around each other. But "resolve it internally" isn't the same as "force a decision" — the first job is to understand whether the disagreement is actually about facts, about priorities, or about something else entirely, because each calls for a different response.

If it's a factual disagreement — two engineers disagree about whether a particular approach will meet a timing margin, a noise budget, or a power target — that's resolvable with data, and it shouldn't be escalated at all. The right move is to design a test, a calculation, or a prototype that will settle it, and to agree in advance on what result would change each person's mind. A disagreement that can be converted into an experiment is a healthy one.

If it's a priorities or values disagreement — say, one engineer weights schedule and the other weights design margin — that's not resolvable by data alone, and it may genuinely need a decision from someone with the authority to set priorities. That's a legitimate escalation, but I'd frame it as "we need a decision on priorities," not "these two can't agree." I'd also try to resolve it one level up within the team first, by making the trade-off explicit and asking whether there's a framing both can accept.

I'd escalate when the disagreement is blocking progress, when it involves cross-team or resource commitments beyond my authority, when it's recurring and consuming disproportionate energy, or when there's a risk the team is avoiding a decision that has real consequences. I'd also escalate if the disagreement has become personal rather than technical, because that's a different problem than the engineering question. The key is to escalate the *decision*, with a clear statement of the options and trade-offs, rather than escalating the *conflict*.

**Possible follow-ups:**
- How would you frame the escalation so it doesn't come across as you failing to manage your team?
- What would you do if your manager's decision went against the option you personally thought was stronger?

## Q3: How would you approach building a cross-functional project timeline for a medical device when hardware, firmware, and regulatory each give different estimates and there's no historical data from similar projects?

**Answer:** When there's no historical data, the estimates people give are really expressions of uncertainty, and the mistake is to average them into a single number that hides that uncertainty. I'd start by decomposing each team's work into the smallest units that can be estimated with some confidence, and by separating the parts that are well-understood from the parts that are genuinely unknown. The unknowns are where the schedule risk lives, and they deserve to be visible rather than buried in a padded estimate.

I'd then make the dependencies explicit — firmware bring-up can't finish before hardware is available, regulatory testing can't start before design freeze, and so on — because a lot of apparent disagreement about duration is actually disagreement about sequencing and assumptions. Getting the teams in one room to agree on the dependency graph often resolves more of the discrepancy than arguing about individual numbers.

For the estimates themselves, I'd use ranges rather than points, and I'd ask each team what would have to be true for their optimistic and pessimistic cases. That surfaces the assumptions, which can then be tested or retired early. Where the ranges are wide, I'd identify what could be done early to narrow them — a feasibility prototype, an early regulatory pre-submission conversation, a bench test of the riskiest subsystem — because reducing uncertainty early is cheaper than absorbing it late.

Finally, I'd present the timeline to stakeholders as a range with the key risks called out, not as a false-precision date. For a medical device, the regulatory phase in particular has long, non-compressible lead times, so I'd build those in as fixed constraints and let the engineering phases flex around them. And I'd plan to re-baseline at each major milestone, because the first estimate for something nobody has built before is a starting hypothesis, not a commitment.

**Possible follow-ups:**
- How would you handle it if one team consistently gives estimates that turn out to be optimistic, and the others have started discounting them?
- How would you communicate a wide range to a stakeholder who wants a single date?

## Q4: How would you approach handling a situation where a team member consistently delivers high-quality technical work but has a pattern of missing internal deadlines, causing downstream delays for the rest of the team?

**Answer:** The quality of the work matters and shouldn't be discounted — a strong contributor who misses dates is a different problem than a weak one, and the solution isn't to treat them as a performance issue. But the downstream impact is real, and letting it continue signals to the rest of the team that internal deadlines are optional, which is corrosive.

I'd start by trying to understand the pattern rather than assuming it's a discipline problem. There are several common causes: the person may be underestimating their own work because they're a perfectionist and keep refining past the point of diminishing returns; they may be taking on more than they admit, or absorbing interruptions; they may be blocked by something they haven't surfaced; or they may simply not have internalized that internal milestones matter as much as external ones. Each of these calls for a different response, so diagnosing before acting is essential.

Once I understand the cause, I'd address it concretely. If it's perfectionism, the conversation is about defining "done" for internal milestones and agreeing that good-enough-for-this-stage is the right bar — internal deadlines exist precisely so that downstream work can start, and over-polishing early work delays the whole system. If it's overcommitment, the fix is visibility: making their workload and its conflicts explicit so we can rebalance. If it's a hidden blocker, the fix is a standing check-in or a norm that blockers get raised early. If it's a values gap, I'd be direct that internal milestones are commitments, not aspirations, and explain the downstream cost in concrete terms.

Throughout, I'd keep the framing on the system and the impact rather than the person's character, and I'd look for whether the team's planning process is contributing — for example, if internal deadlines are set without the person's input, missed dates may be a symptom of top-down estimation rather than individual unreliability. The goal is a durable fix, not a one-time correction.

**Possible follow-ups:**
- How would you handle it if the person acknowledges the pattern but doesn't change it after several conversations?
- What would you do if the rest of the team has started building in buffer for this person's work, effectively hiding the problem?

## Q5: How would you approach leading a post-mortem after a medical device project missed its delivery deadline by several months, when morale is low and there's a tendency to blame individual contributors rather than systemic issues?

**Answer:** The first priority is to set the ground rules before the discussion starts, because a post-mortem that turns into a blame session produces defensiveness and hides information rather than surfacing it. I'd state explicitly that the purpose is to understand the system that produced the outcome, not to assign fault to individuals — and that this isn't just a nicety, it's the only way to get accurate information. People who feel they're being judged will describe what they did, not what actually happened.

I'd structure the discussion around the timeline and the decisions, not the people. Walking through what was known at each point, what was decided, and what the alternatives were tends to reveal that most "individual failures" were actually reasonable decisions made with incomplete information, under constraints that weren't visible at the time. That reframing is often what lifts morale, because it replaces "we failed" with "the system had these gaps."

I'd look specifically for systemic contributors: estimation that didn't account for the unknowns, dependencies that weren't surfaced early, a change-control process that let scope creep in without schedule impact being assessed, or a culture where bad news traveled slowly. For a medical device project, I'd also check whether regulatory or verification phases were under-resourced relative to their actual duration, since those are common sources of late surprises.

The output should be a small number of concrete, owned actions with dates — not a long list of vague lessons. And I'd follow up on those actions in subsequent reviews, because a post-mortem whose recommendations are never revisited teaches the team that the exercise is theater. Finally, I'd be careful to acknowledge the genuine effort people put in, even as we're honest about the outcome; low morale after a missed deadline is best addressed by showing that the team's work is valued and that the path forward is concrete.

**Possible follow-ups:**
- How would you handle it if a senior leader insists on naming individuals as responsible during the post-mortem?
- How would you keep the post-mortem from becoming a venue for unrelated grievances that have been building up?