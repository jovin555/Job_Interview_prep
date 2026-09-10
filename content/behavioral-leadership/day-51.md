# behavioral-leadership — Day 51

## Q1: How would you approach a design review where a senior engineer's proposed architecture is technically sound but the documentation package is too thin for reviewers to evaluate the safety-critical portions, and the engineer is likely to take a request for more detail as a personal criticism?

**Answer:** The first move is to separate the person from the package before the meeting, not during it. A thin package on safety-critical portions is a process gap, not a competence signal, and framing it that way in a private pre-review conversation keeps the senior engineer from reading the request as a verdict on their ability. In that conversation I'd be specific about what's missing and why it matters: not "add more detail," but "the reviewer can't trace how the fault-detection path behaves under a single-point failure, so they can't sign off on that section." Concrete gaps are easier to hear than general criticism.

In the review itself, I'd structure the agenda so the safety-critical sections get dedicated time with the author walking through their reasoning, rather than reviewers trying to reverse-engineer intent from a schematic. If the author can articulate the rationale verbally, that's often the fastest path to capturing it in writing afterward. I'd assign action items with owners and dates for the missing documentation, and treat those items as blocking for the design freeze — not as optional polish.

The longer-term fix is to make the review package expectations explicit and shared, so no one experiences a documentation request as a surprise or a slight. When the standard is visible and applied to everyone, it stops feeling personal.

**Possible follow-ups:**
- What would you do if the senior engineer agrees to add documentation but the added material still doesn't address the safety-critical gaps?
- How would you handle it if other reviewers start using the thin package as a reason to reject the architecture outright, when the architecture itself is fine?

## Q2: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** I'd start by asking what the disagreement is actually about. If it's a genuine technical trade-off where both positions are defensible and the data to decide doesn't exist yet, that's a team problem to solve — usually by defining the decision criteria together and, if needed, running a small prototype or bench test to generate the missing evidence. Escalating that kind of disagreement prematurely just moves the decision up without improving it, and it teaches the team that disagreement is a management problem rather than an engineering one.

Escalation becomes the right call when the disagreement is really about something else: conflicting priorities that the team doesn't have authority to resolve, a resource or schedule trade-off that affects other groups, or a pattern where the same two people keep re-litigating decisions and the team is losing time. It's also appropriate when the decision has cross-functional implications — regulatory, quality, or product — that the two engineers can't weigh on their own.

When I do escalate, I'd escalate the decision, not the people. I'd bring my manager a clear statement of the options, the trade-offs, the criteria that matter, and my recommendation, so the conversation is about choosing a path rather than adjudicating a conflict. And I'd close the loop with both engineers afterward so they understand how the decision was made and why, which matters more for the next disagreement than for this one.

**Possible follow-ups:**
- How would you handle it if your manager's decision goes against your recommendation and one of the engineers feels vindicated while the other feels overruled?
- What would you do if you noticed the same pair of engineers escalating disagreements repeatedly, even when the technical stakes were low?

## Q3: How would you approach building a cross-functional project timeline for a medical device when the hardware, firmware, and regulatory teams each have different estimates for how long their work will take, and there's no historical data from similar projects?

**Answer:** With no historical data, the honest starting point is that every estimate is a guess with a confidence range, and the useful work is making those ranges explicit rather than pretending to a single number. I'd ask each team not just for a duration but for what their estimate assumes — what has to be true for it to hold, and what would make it wrong. That surfaces the dependencies and unknowns that a flat number hides.

Then I'd map the dependencies across teams, because the schedule risk usually lives at the handoffs, not inside any one team's work. Hardware bring-up blocking firmware integration, firmware stability blocking regulatory test execution, test failures feeding back into hardware revisions — those are the places where a slip in one estimate compounds. I'd build the timeline around those interfaces and mark the points where a decision or a deliverable from one team gates another.

For the unknowns, I'd identify the highest-uncertainty items and propose early de-risking — a bench test, a prototype, a targeted feasibility study — so the estimate gets sharper before the schedule depends on it. And I'd communicate the timeline as a range with named risks rather than a single date, so stakeholders understand what they're committing to. Overpromising on a schedule built from guesses is how projects end up in post-mortems.

**Possible follow-ups:**
- How would you handle it if leadership insists on a single committed date rather than a range?
- What would you do if one team's estimate is consistently optimistic across multiple planning cycles, and you suspect the pattern will repeat here?

## Q4: How would you approach handling a situation where a team member consistently delivers high-quality technical work but has a pattern of missing internal deadlines, causing downstream delays for the rest of the team?

**Answer:** The first thing I'd want to understand is whether the missed deadlines are a capacity problem, a prioritization problem, or an estimation problem — because the fix is different for each. Someone who does excellent work but consistently runs late may be underestimating their own tasks, may be quietly absorbing work that isn't visible to me, or may be prioritizing depth over the schedule in a way that's a values mismatch rather than a skill gap. I'd have a direct conversation to find out which, without leading with the downstream impact as an accusation.

If it's estimation, the fix is usually structural: breaking work into smaller checkpoints, tracking actual versus estimated time, and making the estimate visible so it can be corrected early rather than discovered at the deadline. If it's capacity, the fix is workload or prioritization. If it's a values mismatch — the person genuinely believes quality justifies any delay — that's a harder conversation about the team's obligations to each other, because downstream teams are making commitments based on those dates.

Whatever the cause, I'd want the team member to see the downstream cost concretely, not abstractly. "This slipped three days and the integration test window closed" lands differently than "you missed a deadline." And I'd set up earlier check-ins so a slip is visible while there's still time to react, rather than surfacing at the point where it's already caused damage.

**Possible follow-ups:**
- What would you do if the team member acknowledges the pattern but says they'd rather deliver late than deliver something they're not proud of?
- How would you handle it if other team members start building buffer into their own plans to compensate, effectively hiding the real schedule?

## Q5: How would you approach leading a post-mortem after a medical device project missed its delivery deadline by several months, when team morale is low and there's a tendency to blame individual contributors rather than systemic issues?

**Answer:** The tone of the post-mortem is set before the meeting, in how I frame its purpose. If people walk in expecting a hunt for who caused the delay, they'll defend themselves and the real causes will stay buried. I'd frame it explicitly as a search for systemic causes — the conditions that made the delay likely — and make clear that the goal is to change those conditions, not to assign fault. That's not just kindness; it's the only framing that produces useful information.

In the session itself, I'd use a structured method rather than open discussion, because structure keeps the conversation from collapsing into blame. A timeline of events with decisions and their context, then a cause analysis that pushes past the first plausible explanation to the contributing factors underneath it. When someone names a person as a cause, I'd redirect to the conditions: what information did that person have, what pressure were they under, what process allowed the decision to go unchallenged. Most "individual" failures turn out to have systemic roots.

I'd also make sure the post-mortem produces a small number of concrete, owned actions rather than a long list of vague lessons. And I'd close by acknowledging the team's effort honestly — a missed deadline doesn't erase the work done, and morale recovers faster when people feel the retrospective was fair and useful rather than punitive.

**Possible follow-ups:**
- How would you handle it if a senior leader outside the team insists on identifying who was responsible, and wants that reflected in the post-mortem output?
- What would you do if the systemic causes you identify are outside your team's control — for example, a decision made at the portfolio level?