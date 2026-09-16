# behavioral-leadership — Day 57

## Q1: How would you approach a design review where a senior engineer's proposed architecture is technically sound, but the documentation package is too thin for reviewers to evaluate the safety-critical portions — and the engineer is likely to take a request for more detail as a personal criticism?

**Answer:** The first move is to separate the two issues: the quality of the architecture and the completeness of the evidence package. Those are different conversations, and conflating them is what makes the request feel like a personal attack. I'd open the review by explicitly affirming the parts of the design that are strong — if the architecture is genuinely sound, say so, and say why, with specifics. That establishes that the review is not a verdict on the engineer's competence.

Then I'd reframe the documentation gap as a property of the review process rather than a deficiency of the author. A design review can only evaluate what's been made visible; if the safety-critical paths aren't documented, the review can't discharge its function, regardless of how good the underlying design is. I'd frame the ask as "help us see what you already know" rather than "you didn't do your job." Concretely, I'd name the specific artifacts needed — for example, the fault-tree or FMEA entries covering the safety-critical blocks, the rationale for component derating or redundancy choices, and the traceability from safety requirements to the design elements that satisfy them — rather than issuing a vague "needs more detail."

If the engineer still reads it as criticism, I'd take it offline rather than litigate it in the room. A short one-on-one where I acknowledge that documentation is often the least rewarding part of the work, and that the request is about making the design defensible to an auditor or a new team member, usually lands better than a public back-and-forth. I'd also offer a concrete path: a template, a worked example from a prior review, or pairing on the first section so the standard is clear.

The structural fix is to make the expectation explicit before the review, not during it. A published review-entry checklist — what must be present for a safety-critical design to be reviewable — turns "I'm asking you for more" into "the process requires this of everyone." That removes the personal dimension from future instances.

**Possible follow-ups:**
- What would you do if the engineer agrees to add documentation but the added material is still too thin to evaluate the safety-critical portions?
- How would you handle it if other reviewers in the room start piling on, turning your request into a broader critique?

## Q2: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** The default should be to resolve it within the team — escalation is a tool, not a reflex, and overusing it erodes the team's sense that it can make its own decisions. But "resolve it internally" doesn't mean "let it drag." I'd apply a few tests.

First, is the disagreement technical or is it about something else — ownership, credit, or a history between the two people? If it's genuinely technical, it's usually resolvable with data: a prototype, a bench measurement, a calculation, or a review of the relevant standard. If it's relational, no amount of data will settle it, and that's a different conversation.

Second, does the decision have a deadline, and does the disagreement block it? A disagreement that can be resolved by a two-week experiment is worth running. A disagreement blocking a milestone next week needs a decision now, and if the two engineers can't converge, someone has to make the call.

Third, what's the blast radius? A choice that's cheap to reverse and contained to one subsystem can be decided by whoever owns that subsystem, with the rationale documented. A choice that affects safety, regulatory submission, or the whole system architecture, or that's expensive to reverse, warrants a broader decision — and that may legitimately involve my manager, not as an arbiter of who's right, but as the owner of the risk.

If I do escalate, I'd escalate the decision, not the conflict. I'd bring my manager a clear framing: the two options, the trade-offs, the criteria that matter, my recommendation and reasoning, and what I need from them. I would not bring "A and B are fighting." And I'd tell both engineers in advance what I'm doing and why, so escalation doesn't feel like going behind anyone's back.

**Possible follow-ups:**
- What would you do if your manager's decision goes against your recommendation, and you believe the recommendation was better supported by the evidence?
- How would you handle it if one of the engineers escalates over your head because they don't accept your process?

## Q3: How would you approach building a cross-functional project timeline for a medical device when the hardware, firmware, and regulatory teams each give different estimates and there's no historical data from similar projects?

**Answer:** With no historical data, the honest starting point is that the estimates are guesses, and the timeline should be built to expose that rather than hide it. I'd resist the temptation to average the three numbers into a single figure that looks authoritative — that just launders uncertainty into false precision.

Instead, I'd decompose each team's work into the smallest units that can be estimated with some confidence, and separate the parts that are genuinely known from the parts that are unknown. "Firmware integration" is not estimable; "bring up the sensor driver on the eval board" is. The unknowns are where the schedule risk lives, and they deserve to be named explicitly rather than buried inside a larger task.

Then I'd structure the plan around dependencies and decision points rather than a single end date. What does regulatory need from hardware before it can start? What does firmware need from hardware before integration testing can begin? Where are the points at which a decision has to be made, and what information is needed to make it? A dependency-driven plan makes the critical path visible and shows where a slip in one team propagates.

For the estimates themselves, I'd ask each team to give a range rather than a point — a best case, a likely case, and a worst case — and to state the assumptions behind each. That surfaces disagreement productively: if hardware assumes a component is available in four weeks and firmware assumes six, that's a conversation worth having now, not at the milestone.

Finally, I'd build in explicit checkpoints where estimates get revised against actual progress. The first checkpoint is the most valuable, because it's the first real data the project has. I'd communicate the plan to stakeholders as a range with named risks, not a promise — and I'd say plainly that the first revision will come after the first checkpoint, so nobody is surprised when the number moves.

**Possible follow-ups:**
- How would you handle it if a stakeholder insists on a single committed date rather than a range?
- What would you do if, at the first checkpoint, one team's actual progress is far behind its estimate and the others are on track?

## Q4: How would you approach handling a situation where a team member consistently delivers high-quality technical work but has a pattern of missing internal deadlines, causing downstream delays for the rest of the team?

**Answer:** The first thing I'd want to understand is what "missing deadlines" actually means in this case, because the pattern could have several very different causes and the response depends on which one it is. Is the person underestimating their own work? Are they being pulled onto other tasks? Are they gold-plating — continuing to refine past the point of diminishing returns because the work is never "done enough" for them? Or are the deadlines themselves unrealistic, and this person is simply the one willing to say so by missing them?

I'd start with a direct, private conversation, framed around the impact rather than the person: "When this slips, the integration test can't start, and that pushes the whole team." Then I'd ask them to walk me through how they plan their work and where the time actually goes. Often the answer is visible in that conversation — they may not realize the downstream effect, or they may be silently absorbing scope that was never agreed.

If the cause is estimation, the fix is usually to break work into smaller increments with more frequent check-ins, so a slip is visible in days rather than weeks. If the cause is competing priorities, the fix is at my level — protecting their time or making the trade-off explicit to whoever is pulling on them. If the cause is perfectionism, that's a coaching conversation about what "good enough to hand off" means, and it may need concrete criteria rather than a general exhortation to stop polishing.

What I would not do is let it continue unaddressed because the output is high quality. High-quality work that arrives late still delays everyone downstream, and quietly tolerating it tells the rest of the team that deadlines are optional for some people. The conversation is fairer to the person than letting resentment build around them.

**Possible follow-ups:**
- What would you do if the person acknowledges the pattern but says the quality of their work is more important than the schedule, and they're not willing to change?
- How would you handle it if other team members start adjusting their own plans around this person's expected lateness, effectively normalizing it?

## Q5: How would you approach leading a post-mortem after a medical device project missed its delivery deadline by several months, when morale is low and there's a tendency to blame individual contributors rather than systemic issues?

**Answer:** The purpose of a post-mortem is to change what the organization does next time, and blame is the enemy of that goal — once people feel they're being judged, they stop volunteering the information the post-mortem needs. So the first job is to set the ground rules explicitly: we're here to understand the system that produced this outcome, not to identify who to punish. I'd say that out loud at the start, and I'd enforce it in the room.

I'd structure the analysis around the timeline rather than around people. Reconstruct what happened, in order, with the decision points marked: when did we first know the schedule was at risk? What information was available at that point? What decision was made, and by what process? That framing naturally surfaces systemic issues — an estimate that was never revisited, a risk that was raised but not acted on, a dependency that nobody owned — without requiring anyone to be the villain.

I'd also separate the technical causes from the process causes. A missed deadline is rarely one thing; it's usually a technical surprise compounded by a process that couldn't absorb it. Both deserve attention, but they have different fixes.

On morale: I'd acknowledge it directly rather than pretending the room is fine. A long overrun is demoralizing, and people need to hear that acknowledged before they can engage productively. I'd also make sure the output of the post-mortem is a small number of concrete, owned actions rather than a long list of vague lessons — a post-mortem that produces nothing actionable makes people feel the exercise was theater, which is worse than not doing it.

Finally, I'd be careful about my own contribution. If I was part of the decisions that led here, I'd say so. A leader who participates in the analysis rather than standing outside it changes the tone of the whole conversation.

**Possible follow-ups:**
- What would you do if, despite the ground rules, one person becomes the focus of the discussion and others start attributing the overrun to them?
- How would you handle it if the post-mortem identifies a systemic issue that traces back to a decision made above your level?