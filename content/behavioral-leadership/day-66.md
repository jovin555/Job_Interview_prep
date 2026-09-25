# behavioral-leadership — Day 66

## Q1: How would you approach a design review where the review keeps stalling because one reviewer raises a new objection in every session, and the team has started routing around the review process to make progress?

**Answer:** The first thing I'd do is separate the two problems, because they have different fixes. The team routing around the review is the more dangerous symptom — in a regulated environment, an undocumented design decision is a compliance problem regardless of whether the objection was valid. So I'd want to restore the process's legitimacy before trying to manage the individual.

I'd start by looking at whether the reviewer's objections are actually substantive. Sometimes a reviewer who raises something new every session is doing it because the review package doesn't give them enough to evaluate up front — they're discovering gaps live that should have been visible in the materials. In that case the fix is upstream: a review package with a clear scope, a defined decision list, and explicit "out of scope for this review" boundaries. If the reviewer still finds real issues, that's a signal the package is thin, not that the reviewer is difficult.

If the objections are genuinely new each time and not converging, I'd talk to the reviewer one-on-one, not in the room. I'd frame it around the review's purpose: "We need to reach a decision on these specific items so the team can proceed. What would you need to see to be comfortable closing them out?" That converts an open-ended objection into a defined exit criterion. If the concern is real but out of scope, it goes on a tracked action list with an owner and a date — it doesn't block the current decision, but it isn't dropped either.

For the team routing around the process, I'd be direct that skipping review isn't an option, but I'd also acknowledge why they're doing it — the process as currently run isn't producing decisions. Fixing the process is what earns the right to insist people follow it. I'd also make sure decisions and their rationale get recorded, so a later objection is a new decision point rather than a re-litigation of something already closed.

**Possible follow-ups:**
- What would you do if the reviewer's objections turned out to be correct, and the design genuinely needed rework each time?
- How would you handle it if the reviewer reported to a different manager and didn't accept your framing of the review's scope?

## Q2: How would you approach deciding how much technical detail to include when presenting a design trade-off to a mixed audience of engineers, a quality manager, and a product manager in the same room?

**Answer:** I'd structure the presentation in layers rather than trying to find one level of detail that works for everyone, because there isn't one. The opening should be at a level everyone can follow: what decision is being made, what the options are, what the trade-off is in plain terms, and what you're recommending. That's the part the product manager and quality manager need, and the engineers can tolerate it because it's short.

Then I'd go into depth in a way that's skippable — an appendix, a backup slide, or a clearly marked "detail" section. The engineers who want to interrogate the analysis can go there; the others aren't forced through it. The key is that the depth is available on demand rather than front-loaded.

The framing of the trade-off itself matters more than the volume of detail. For a quality manager, the relevant axis is usually risk and compliance — does this option affect a safety requirement, a verification activity, or the design history file? For a product manager, it's schedule, cost, and user impact. For engineers, it's performance, complexity, and maintainability. Same decision, three different lenses, and I'd make sure each lens gets an explicit sentence rather than assuming people will translate.

I'd also be careful not to hide uncertainty behind detail. If a number is an estimate, I'd say so. If there's a risk we haven't fully characterized, I'd name it rather than let it sit in a footnote. Mixed audiences tend to trust the presenter less when they sense the depth is being used to obscure rather than clarify.

**Possible follow-ups:**
- How would you handle it if the product manager pushed for a decision before the engineers had finished evaluating the options?
- What would you do if the quality manager's concern was valid but not something the engineers had considered?

## Q3: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** The deferral pattern is usually not a confidence problem — it's that the engineer has never been in a position where the decision was actually theirs, so deferring has been a rational strategy. The fix is to create that position deliberately, in a low-stakes setting first.

I'd start by giving them ownership of a decision with a real but bounded scope — something where the consequences of a wrong call are recoverable, and where I'm available as a sounding board rather than a decision-maker. The important part is that I don't answer the question when they bring it to me. If they ask "which option should we pick," I'd turn it back: "What's your recommendation, and what's the reasoning?" That's uncomfortable at first, but it's the only way the muscle develops.

I'd also make the reasoning explicit rather than just the outcome. A lot of engineers who defer have never seen how a senior person actually weighs trade-offs — they see the conclusion, not the process. So I'd narrate my own reasoning out loud in situations where I do decide, and I'd ask them to do the same when they decide. Writing a short decision record — options considered, criteria, choice, rationale — is a good forcing function, because you can't write that down without actually having a position.

Over time I'd widen the scope and reduce my involvement, but I'd keep a regular check-in where we review decisions they've made and what they'd do differently. The goal isn't to make them confident; it's to make them practiced. Confidence tends to follow competence, not the other way around.

**Possible follow-ups:**
- What would you do if they made a decision you disagreed with, and it was within the scope you'd given them?
- How would you handle it if the deferral behavior was reinforced by the team culture, where junior engineers are expected to defer?

## Q4: How would you approach leading a technical decision when the team is split between two viable architectures and the disagreement has become personal rather than technical, with each side attributing bad motives to the other?

**Answer:** Once a disagreement turns personal, continuing to argue the technical merits in the same forum usually makes it worse — each side reads the other's arguments as evidence of bad faith rather than as data. So the first move is to change the frame, not to adjudicate the technical question.

I'd separate the people from the decision. One way is to restate both positions in neutral terms and get each side to confirm that the restatement is fair. That's often enough to defuse the "you're not listening to me" dynamic, because each side hears their own position accurately represented by someone else. If they can't agree on the restatement, that itself is diagnostic — it usually means the disagreement is about something other than what they think it's about.

Then I'd try to convert the disagreement into something testable. If both architectures are viable, there's usually a specific claim underneath the disagreement — a performance threshold, a failure mode, a cost assumption — that can be checked rather than argued. A prototype, a benchmark, or a targeted analysis on that one claim often resolves the dispute faster than another meeting, because it moves the conversation from positions to evidence. If the claim can't be tested within the time available, then the decision has to be made on judgment, and I'd say so explicitly rather than pretending there's a data-driven answer.

If it still doesn't resolve, I'd make the call myself, document the rationale, and be clear that the decision is made — not that one side "won." The losing side needs to know their concerns were heard and recorded, and that if the chosen path hits the specific problem they predicted, we'll revisit. That's what keeps a decision from becoming a permanent faction.

**Possible follow-ups:**
- What would you do if the person whose position lost continued to undermine the decision after it was made?
- How would you decide when to escalate rather than make the call yourself?

## Q5: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** The pressure to ship a fix quickly is the main risk here, because intermittent failures are exactly the case where a plausible-looking fix gets shipped without evidence that it addresses the cause. So the first thing I'd do is separate containment from correction. Containment — a workaround, a guard, a conservative fallback — can go out quickly if it reduces harm, and it buys time. But I'd be explicit that containment is not the fix, and that the investigation continues.

For the investigation itself, the core problem is that you can't reproduce on demand, so you have to increase the rate at which the failure reveals itself. That means instrumenting rather than guessing: add logging around the suspected boundary, capture the state at the moment of failure, and try to widen the conditions under which it occurs — temperature, supply margin, timing stress, load. The goal is to turn a rare event into a frequent one so it becomes observable.

In parallel I'd build a fault tree from the system level down, and use it to decide what to instrument rather than instrumenting everything. With an intermittent fault, the temptation is to add logging everywhere, which produces noise and slows the analysis. A structured decomposition — what are the possible failure modes, which are consistent with the observed symptoms, which can be ruled out cheaply — narrows where to look.

I'd also be disciplined about what counts as a fix. A change that makes the symptom disappear is not the same as a change that addresses the cause, especially when the failure is intermittent, because "it hasn't happened since" is weak evidence. I'd want a mechanism-level explanation of why the change eliminates the failure, and a way to verify effectiveness — either by reproducing the original condition and showing it no longer fails, or by monitoring over a defined period with a clear criterion for success.

**Possible follow-ups:**
- How would you decide when you've gathered enough evidence to conclude the root cause, given that you can't reproduce it reliably?
- What would you do if the containment workaround introduced its own risk, and the team wanted to ship it as the permanent fix?