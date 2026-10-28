# behavioral-leadership — Day 99

## Q1: How would you approach a design review where the presenter is technically strong but the review package arrives late and is missing the calculations that justify a safety-critical decision, and the meeting is the only slot before a milestone gate?

**Answer:** The first move is to separate the two problems: the review process failed, and the milestone gate is real. I would not cancel the review, because a milestone gate without a review is worse than a review with incomplete inputs — but I also would not let the meeting proceed as if the package were complete, because that quietly converts a review into a rubber stamp.

Concretely, I would open the meeting by naming the gap explicitly and neutrally: "The package is missing the trace-width and creepage calculations for the safety-critical section. We can review everything else today, and we need a defined path for that section before the gate closes." Then I would run the review on what is reviewable — architecture, component selection, layout topology, test coverage — and capture the missing calculations as a formal action item with an owner and a date, not a verbal "send it later."

For the safety-critical portion specifically, I would ask the presenter to walk through the reasoning verbally in the room, even without the written numbers. That does two things: it lets experienced reviewers sanity-check the logic and catch a wrong assumption early, and it produces a record of what was said that can be transcribed into the review minutes. If the verbal walkthrough reveals the calculation was never actually done — not just undocumented — that changes the severity: it becomes a finding, not a documentation gap, and the gate should not close until it is resolved.

The systemic piece matters as much as the immediate one. A package arriving late and incomplete before a milestone gate is usually a symptom of a review-preparation standard that isn't enforced, or of a schedule that leaves no time to prepare. After the meeting I would raise with the presenter — privately, not in the room — what made the package late, and whether the fix is a checklist, an earlier internal deadline, or a schedule conversation. The goal is that the next gate doesn't reproduce the same situation.

**Possible follow-ups:**
- If the verbal walkthrough reveals the calculation was never done, how do you handle the milestone gate conversation with the program side?
- How do you keep the review productive when half the room wants to stop and wait for the missing calculations?

## Q2: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode in both directions is the same: the firmware team ends up making design choices against a mental model of the hardware that doesn't match reality. Oversimplify and they'll assume more headroom than exists; bury them in detail and they'll disengage and default to whatever the last person told them.

What works is translating the constraint into the terms the firmware actually operates in — bits, counts, noise floor, timing, update rate — and pairing each number with the consequence for their code. "The ADC is 12-bit over a 3.3 V reference" is a datasheet fact. "That's roughly 0.8 mV per count, and the front-end noise is on the order of a few counts peak-to-peak, so a single sample is not trustworthy — you need averaging or filtering, and here's the settling time that implies" is something a firmware engineer can design against. The constraint becomes actionable when it tells them what they cannot do and what it will cost to work around it.

I would also be explicit about what is fixed versus what is negotiable. Some constraints are hard — the ADC resolution is what it is on this board revision. Others are soft — the analog filter corner could move if there's a strong reason. Marking which is which prevents the firmware team from either designing around a constraint that could have been changed, or assuming they can negotiate something that's frozen. And I would put the numbers in a short written interface document rather than leaving them in a meeting, because firmware will revisit these assumptions repeatedly and verbal transmission degrades.

The last piece is closing the loop: ask the firmware team to restate the constraint back in their own terms, and check that their filtering and sampling strategy actually reflects it. If they've built a filter that assumes a cleaner signal than the hardware delivers, better to find that in a design review than in system integration.

**Possible follow-ups:**
- How do you handle it when the firmware team pushes back and says the hardware should just be changed to make their life easier?
- What goes in that interface document, and who owns keeping it current when the hardware changes?

## Q3: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** The default should be resolution within the team, because escalating every disagreement trains the team to route decisions upward and erodes the technical authority of the people closest to the work. But "resolve it yourselves" isn't a policy — it needs a test for when escalation is actually the right call.

I would use roughly three criteria. First, authority: does the disagreement hinge on something the team genuinely cannot decide — budget, headcount, a cross-organizational commitment, a schedule trade-off that belongs to program management? If so, it isn't a technical disagreement at all; it's a decision that was never the team's to make, and escalating is correct. Second, consequence and reversibility: if the two options carry materially different safety, regulatory, or cost consequences and the choice is expensive to reverse, the cost of a wrong call resolved internally may exceed the cost of escalating. Third, deadlock: if the disagreement has been worked through the normal means — data, prototyping, review — and both sides remain entrenched, escalation is a way to get a decision rather than let it drift.

Before escalating, though, I would make sure the team has actually done the work to resolve it. That means the disagreement is stated as a specific technical question rather than two positions, each side's argument is written down with its assumptions and evidence, and there's a clear statement of what data or test would settle it. Very often, forcing that structure either resolves the disagreement or reveals that it's really about something else — a requirements ambiguity, a risk-tolerance difference, a past bad experience. Those are better addressed directly than escalated.

When I do escalate, I would escalate a framed decision, not a complaint: here are the two options, here's the evidence for each, here's the team's recommendation if there is one, and here's what we need from you. And I would tell both engineers that's what's happening, so nobody experiences it as being overruled behind their back.

**Possible follow-ups:**
- What if one of the two engineers goes around you and escalates directly to your manager?
- How do you make sure an escalated decision gets documented so it doesn't get relitigated later?

## Q4: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** The pressure to ship a fix quickly is exactly what makes intermittent failures dangerous, because the fastest available fix is usually a guess, and a guess that appears to work — because the failure is intermittent and stops for a while — is indistinguishable from a real fix until it fails again in the field. So the first thing I would do is separate containment from correction, and be explicit with stakeholders that they are different things on different timelines.

Containment is what buys time: tighten the screening test, add a margin, restrict the operating envelope, add logging so the next occurrence captures data. Containment can ship fast and should, as long as everyone understands it does not close the investigation. Correction waits for a verified root cause.

For the investigation itself, the core problem is that you can't reproduce on demand, so you have to make the failure reproduce itself. That means instrumenting for capture rather than trying to trigger it: add persistent logging around the suspect subsystem, capture the state at the moment of failure, and let the device run until it happens. In parallel, I would widen the search rather than narrowing prematurely — build a fault tree or fishbone across hardware, firmware, environment, and use conditions, and look for the variable that correlates with occurrence. Intermittent failures usually have a hidden variable: temperature, supply margin, a timing race, a specific sequence of user actions, a particular batch of components. Finding that variable is the actual work.

I would also resist the temptation to accept the first plausible explanation. With intermittent failures, the first theory that "explains" the symptom often just explains one instance. The test is whether the theory predicts when the failure should and shouldn't occur — and whether you can make it occur deliberately by manipulating the suspected variable. If you can't make it happen on purpose, you probably haven't found it.

Throughout, I would keep a written investigation log — hypotheses, tests, results, ruled-out causes — because intermittent investigations run long and the team will otherwise re-test things it already eliminated.

**Possible follow-ups:**
- How do you decide when containment has bought enough time versus when the investigation needs to be escalated for more resources?
- What do you do if the failure rate is so low that capturing data would take months?

## Q5: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** Deferring to seniority is often a rational response to never having been given real ownership — if every decision you make gets overridden or second-guessed, you learn to wait for the senior person to speak. So the mentoring approach is less about building confidence in the abstract and more about creating genuine, bounded ownership where the engineer makes the call and lives with it.

I would start by scoping a decision that is real but contained: a subsystem choice, a component selection, a test approach — something with actual consequences but a limited blast radius. Then I would make the ownership explicit and public: this is yours to decide, here's the deadline, here's what I need from you — a recommendation with the trade-offs and the reasoning. The key is that I don't make the decision for them, and I don't hover. If they bring me a question, I'd reflect it back — "what do you think, and why?" — rather than answering it, at least the first time.

The harder part is what happens when their decision is wrong. If it's low-consequence, letting them discover the error and correct it themselves teaches more than preventing it. If it's higher-consequence, I'd intervene before it's irreversible but frame it as a review of their reasoning, not a replacement of their judgment. What I want to avoid is the pattern where the mentor quietly fixes the decision and the engineer learns that ownership is nominal.

I would also work on the "most senior in the room" reflex directly. In design reviews, I'd deliberately ask for their view before the senior people speak, and I'd name good reasoning when I see it — not generic praise, but "that trade-off analysis was the right way to frame it." Over time the goal is that they experience their own judgment being taken seriously, which is what actually displaces the habit of deferring.

**Possible follow-ups:**
- How do you handle it if a senior engineer on the team keeps overriding the mentee's decisions despite the ownership you've set up?
- How do you know when the mentoring has worked — what would you look for?