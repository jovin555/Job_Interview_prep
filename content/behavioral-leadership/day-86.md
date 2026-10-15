# behavioral-leadership — Day 86

## Q1: How would you approach a design review where the presenter's package is technically solid but arrives late and is missing the calculations that justify a safety-critical decision, and the meeting is the only slot before a milestone gate?

**Answer:** The instinct is to either wave it through because the work is probably fine, or cancel the review because the package is incomplete — both are wrong. The right move is to separate the review into what can be decided now and what cannot, and be explicit about which is which.

First, I'd open the meeting by naming the situation plainly rather than letting it sit unspoken: the package arrived late, one safety-critical calculation is missing, and we have a milestone gate. That framing lets the room make a conscious choice instead of drifting into a rubber-stamp. Then I'd triage the agenda. Everything that doesn't depend on the missing calculation — interfaces, component selection, layout constraints, testability, the parts of the design that are fully documented — can be reviewed and closed today. That's real progress and it respects the milestone.

For the safety-critical item specifically, I would not approve it on the strength of the presenter's verbal assurance, however credible. A safety-critical calculation needs to be in the package, traceable, and reviewable by someone other than its author. So I'd mark that item as "reviewed pending documentation" — a conditional status, not a pass — and set a hard, short deadline for the calculation to be circulated in writing, with a named reviewer. If the milestone gate genuinely cannot move, I'd escalate that as a schedule risk to whoever owns the gate, with the specific blocker named, rather than quietly absorbing the risk by approving something I couldn't verify. The distinction that matters: I'm not blocking the project, I'm refusing to convert an undocumented assumption into an approved safety decision.

I'd also address the pattern, not just the instance. If packages routinely arrive late, that's a process problem — a review-readiness checklist, a package-due date ahead of the meeting, a rule that safety-critical items without supporting calculations are automatically deferred. Fixing the one meeting is tactical; fixing the intake process is what stops this recurring.

**Possible follow-ups:**
- If the presenter pushes back and says the calculation is "obvious" and the delay would cost the team a week, how do you hold the line without damaging the relationship?
- How would you decide which items are truly independent of the missing calculation, so you don't accidentally approve something that depends on it?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures under schedule pressure are where teams most often ship a fix that makes the symptom disappear without ever understanding the cause — and in a regulated device that's a serious liability, because an unverified fix can mask the problem or move it somewhere worse.

The first discipline is to resist the pressure to "just fix it" before you can reproduce it. If you can't reproduce it, you can't verify a fix, and an unverified fix is a guess with a signature on it. So the early work is instrumentation, not repair. I'd focus on making the failure observable: adding logging, capturing the state at the moment of failure, widening the conditions under which it occurs. Often the fastest path to a root cause is turning an intermittent failure into a reproducible one by finding the variable that triggers it — temperature, supply voltage, timing, a specific sequence of operations, a particular unit.

In parallel, I'd apply structured methods rather than brainstorming. A fishbone or Ishikawa diagram forces the team to consider categories systematically — hardware, firmware, environment, power, interfaces, user interaction — instead of anchoring on the first plausible theory. 5 Whys is useful once you have a candidate cause, to push past the first explanation to the underlying one. And I'd separate containment from correction: if the field risk is real, contain it (limit use, add a workaround, increase monitoring) while the investigation continues, but be clear that containment is not a fix and doesn't close the investigation.

On the pressure itself, I'd be honest with stakeholders about the difference between "we have a fix" and "we understand the cause and have verified the fix addresses it." Those are different claims with different confidence levels, and conflating them to hit a date is how you get a recurrence. I'd communicate the investigation as a bounded effort with defined checkpoints, so the pressure has somewhere to go other than into a premature fix.

**Possible follow-ups:**
- What specific evidence would you require before declaring an intermittent failure resolved, given that "it hasn't happened again" is weak evidence?
- How would you keep the team from anchoring on the first plausible theory when the failure is hard to observe?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode here is usually one of two extremes. Either the hardware engineer says "the analog front end is noisy, deal with it in firmware" — which gives the firmware team nothing actionable — or they hand over a full noise analysis and a stack of plots, which the firmware team can't map to a decision. The goal is to translate the constraint into the firmware team's own vocabulary: what it means for their filtering, their sampling strategy, their thresholds, and their error budget.

I'd start from the system requirement and work backward. If the end requirement is, say, a measurement accurate to some tolerance, then the question the firmware team actually cares about is: how much of that error budget does the analog front end consume, and how much is left for them? That reframes a hardware property as a shared budget, which is something both teams can reason about together. I'd give them the noise floor and its character — is it white noise, is it periodic and correlated with a switching supply, does it drift with temperature — because the character determines the right mitigation. Averaging helps with white noise; synchronous sampling or notch filtering helps with periodic noise; neither helps with drift.

I'd also be concrete about what's fixed and what's negotiable. If the ADC resolution is fixed by the chosen part, say so and explain the consequence. If the analog front end could be improved with a layout change or a different filter, say what that would cost and let the firmware team weigh it against doing more in software. The point is to make the trade-off visible rather than to hand down a constraint as if it were immutable.

Finally, I'd keep the conversation two-way. The firmware team often knows things the hardware team doesn't — how often they actually sample, what latency they can tolerate, whether they can afford a longer settling time. A constraint that looks hard in isolation may be easy once you know the firmware can sample more slowly or average over a longer window. Translating isn't just explaining hardware to firmware; it's finding the joint solution space.

**Possible follow-ups:**
- How would you handle it if the firmware team's proposed mitigation would push the measurement latency beyond what the system can tolerate?
- What would you put in writing so the constraint and its rationale survive past the current team?

## Q4: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This is a common and often under-diagnosed situation. The engineer isn't lacking skill — they execute well — but they've never been put in a position where the decision was theirs to own, so they've learned that deferring to seniority is safe. The mentoring goal isn't to make them more assertive for its own sake; it's to build the judgment and the accountability that come from actually owning a decision and living with its consequences.

I'd start by giving them real ownership of something bounded but genuine — a subsystem, a design decision with a clear scope — where they are the decision-maker, not the recommender. The key is that "owning" has to mean the decision is theirs even when a senior person disagrees, provided they can defend it with reasoning. That's the muscle that's missing. I'd make clear up front that I'll back their decision within its scope, and that the measure of success is not whether I would have chosen the same thing but whether they can justify their choice.

In reviews, I'd deliberately redirect. When they look to the most senior person for the answer, I'd turn it back: "What do you think, and why?" Not as a gotcha, but to make the deferral visible and to give them a safe place to practice committing to a position. Over time, the pattern of "I think X because Y, and here's what would change my mind" is exactly the habit that separates an executor from an owner.

I'd also normalize the discomfort of being wrong. A lot of deference comes from fear of being the one who chose badly. If the culture treats a well-reasoned decision that turned out wrong as a learning event rather than a failure, the engineer is far more willing to commit. I'd model that myself — being explicit about decisions I made that didn't pan out and what I took from them — so ownership doesn't feel like exposure.

**Possible follow-ups:**
- How would you handle it if, given real ownership, the engineer makes a decision that a senior colleague strongly disagrees with — do you let it stand?
- How would you tell the difference between healthy deference and a genuine lack of confidence that needs a different kind of support?

## Q5: How would you approach leading a technical decision when the team is split between two viable architectures and the disagreement has become personal rather than technical, with each side attributing bad motives to the other?

**Answer:** Once a technical disagreement turns personal, the technical merits stop being the deciding factor — people are defending their identity or their standing, not their reasoning. The first job is to de-escalate the framing before trying to resolve the substance, because you can't evaluate two architectures fairly while each side believes the other is arguing in bad faith.

I'd start by naming the dynamic without assigning blame: "We have two viable options and the discussion has gotten heated. Let's reset on what we're actually deciding." Then I'd reframe the disagreement as a shared problem — the team is trying to pick the best architecture for the device, and both options have real trade-offs. That moves the conflict from person-versus-person to team-versus-problem, which is the only frame where a technical resolution is possible.

Next, I'd force the discussion onto criteria rather than preferences. What are the actual decision factors — reliability, power, cost, schedule, regulatory risk, team familiarity, manufacturability? I'd get both sides to agree on the criteria first, before scoring either option, because agreeing on what matters is usually easier than agreeing on the answer and it exposes whether the disagreement is really about values or about facts. Often the two sides are optimizing for different criteria and haven't noticed.

Where the disagreement rests on a factual claim — "this approach is more reliable," "that one is simpler to certify" — I'd look for a way to test it rather than argue it. A prototype, a bench measurement, a review of a comparable design, a consultation with someone who's built both. Data resolves disputes that rhetoric can't, and it lets the losing side save face because the decision came from evidence, not from someone winning.

If, after all that, the disagreement is genuinely a judgment call between two defensible options, then it's my decision to make, and I'd make it, document the rationale, and be clear that the decision is made so the team can move forward. What I would not do is let it drag on indefinitely hoping consensus emerges — a prolonged unresolved split is corrosive in its own right. And I'd follow up individually with the person whose option wasn't chosen, because being overruled after a heated debate needs a human acknowledgment, not just a decision memo.

**Possible follow-ups:**
- How would you handle it if the person whose option lost continues to relitigate the decision after it's been made?
- What would you do if the disagreement is actually a proxy for a deeper interpersonal conflict that predates this decision?
- How would you document the decision and its rationale so it's defensible later, without it reading as a verdict against one side?