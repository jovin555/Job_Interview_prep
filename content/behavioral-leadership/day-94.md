# behavioral-leadership — Day 94

## Q1: How would you approach a design review where the presenter is a strong engineer whose work is technically sound, but who has a history of becoming defensive when questioned — and the review genuinely needs to be critical to be useful?

**Answer:** The core problem here is separating the critique of the work from the identity of the person, and doing it structurally rather than relying on interpersonal skill in the moment. I'd start before the meeting: set the review's ground rules explicitly at the top — the purpose is to find issues while they're cheap to fix, every comment is about the artifact and not the author, and the presenter is expected to defend decisions with data rather than defer or dig in. Framing critique as a shared obligation ("we're all here to stress-test this") rather than a judgment of the presenter lowers the temperature.

Second, I'd change the mechanics of how feedback is delivered. Instead of open-floor questioning, which tends to produce a rapid-fire interrogation that feels personal, I'd use a structured round: each reviewer states their concern, the evidence behind it, and what would resolve it. That format forces comments to be specific and evidence-based, which both makes them less personal and makes them harder to dismiss. I'd also model the behavior myself — raise a concern about my own past decisions or explicitly say "I might be wrong here, here's my reasoning" — so being questioned visibly isn't a status threat.

Third, I'd redirect defensiveness into the technical question. If the presenter pushes back, I'd ask "what evidence would change your mind?" or "what test would settle this?" That converts a defensive reaction into a falsifiable question, which is exactly where you want the energy to go. If a specific exchange gets heated, I'd park it as an action item to resolve offline with data rather than let the review become a debate.

Finally, I'd follow up privately afterward — not to soften the critique, but to reinforce that the review did its job and that being challenged is normal and expected for senior people too. Over time, the goal is a culture where the strongest engineers are the ones most comfortable being questioned, because that's the signal of a healthy review process.

**Possible follow-ups:**
- What would you do if the defensiveness persists across multiple reviews despite the structural changes?
- How would you handle it if other reviewers start self-censoring because they don't want to trigger the reaction?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent, non-reproducible failures are the case where the pressure to "just fix it" is most dangerous, because a fix you can't verify against a reproduction is a guess. So the first move is to resist treating the absence of a reproduction as a reason to skip structure — instead, treat *characterizing the failure* as the deliverable. I'd start by mining every existing data point: field logs, timestamps, environmental conditions, firmware versions, batch/lot numbers, operator reports. The goal is to find the pattern in *when* it fails, because intermittency almost always has a hidden variable — temperature, supply voltage, timing margin, a specific sequence of events, a particular component lot.

From there I'd apply a structured method rather than brainstorming. A fishbone (Ishikawa) diagram across the categories — hardware, firmware, environment, user interaction, manufacturing — forces the team to consider causes they'd otherwise skip. Then 5 Whys on the most plausible branches, and critically, I'd separate *containment* from *corrective action*. Containment is what you do now to limit field impact while you investigate — a tighter screening test, a firmware guard, a usage restriction — and it's legitimate to ship containment under pressure. What you must not do is call containment a root-cause fix and close the investigation.

To make progress without a reproduction, I'd invest in *instrumentation*: add logging, capture more state at the point of failure, run accelerated stress (thermal cycling, voltage margining, extended soak) to try to force the failure into the open. I'd also define in advance what evidence would confirm or eliminate each candidate cause, so the investigation converges instead of sprawling. And I'd verify effectiveness explicitly — after the fix, define the test or monitoring that proves the failure rate actually dropped, rather than assuming it did.

**Possible follow-ups:**
- How would you decide when containment is good enough to ship versus when you need to hold the release?
- What would you do if the investigation points to a cause you can't fully confirm before the deadline?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode in both directions is real: oversimplify and the firmware team makes design choices that assume precision the hardware can't deliver; over-detail and they tune out and treat the constraint as "the hardware team's problem." The bridge is to translate the constraint into *what it means for their decisions*, not into a physics lecture and not into a single number.

Concretely, I'd express the constraint as a budget the firmware team can reason about: effective number of bits after noise, the noise floor in the band they care about, the sample rate versus settling time trade-off, and where the analog front end's error sources sit relative to their signal of interest. Then I'd connect that to their world — "given this noise floor, a single sample isn't enough for your threshold detection; here's the averaging or filtering that gets you there, and here's the latency cost." That gives them a lever (filtering, oversampling, timing) rather than a wall.

I'd also make the constraint *observable*. Rather than describing noise abstractly, provide measured data — a noise histogram, a spectrum, a plot of the front end's response — so the firmware team can see the problem rather than take it on faith. And I'd agree on the interface contract explicitly: what the hardware guarantees, what it doesn't, and what the firmware must do to stay within spec. Writing that down as a shared interface control document prevents the "I assumed the hardware was clean" conversation later.

Finally, I'd keep a feedback loop. If the firmware team finds the constraint is blocking a requirement, that's a signal the hardware design or the requirement needs revisiting — the translation isn't one-way.

**Possible follow-ups:**
- How would you handle it if the firmware team pushes back that the hardware constraint is unreasonable and should just be designed away?
- What would you put in the interface control document to make the constraint enforceable rather than advisory?

## Q4: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** The default should be to resolve it within the team, because escalating too readily trains the team to route every disagreement upward and erodes both the seniors' ownership and my credibility as the person who's supposed to make these calls. But "resolve it yourself" isn't the same as "suppress it" — the decision hinges on a few questions.

First, is the disagreement *technical and resolvable with data*? If both positions are defensible and the gap is evidence, the right move is to design the test or prototype that settles it, and let the data decide. Escalating a question that a bench measurement could answer is a failure of the engineering process, not a management decision.

Second, does it have *consequences beyond the team's authority* — regulatory impact, cost, schedule, cross-team dependencies, or a safety-critical call? If resolving it commits the organization to something outside my scope, the manager needs to be in the loop regardless of whether the team can technically decide it.

Third, is it *actually about the technical question*, or has it become personal? If the two engineers are attributing bad motives to each other, escalation won't fix that — it just moves the conflict up a level. That needs to be addressed directly first.

Fourth, is there a *time constraint* where the team genuinely can't converge? Then escalation with a clear recommendation ("here's the trade-off, here's what I'd choose and why") is appropriate — escalating a decision with a recommendation is very different from escalating a fight.

Whatever the outcome, I'd document the decision and its rationale, so the team has a record and the losing side understands they were heard.

**Possible follow-ups:**
- How would you handle it if the two engineers agree to a resolution but one of them keeps relitigating it afterward?
- What would you do if your manager, when escalated to, makes a call you believe is technically wrong?

## Q5: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This is a common and often invisible gap — someone who executes beautifully but has never had to carry a decision from ambiguity to commitment, so they've learned to wait for the senior voice rather than form and defend their own judgment. The mentoring goal isn't to make them louder; it's to build the experience of *owning* a decision, which only comes from actually doing it in a low-stakes setting first.

I'd start by giving them a scoped decision to own end-to-end — something with real consequences but bounded blast radius, where I commit in advance to not overriding them unless there's a safety or compliance issue. The key is that I have to genuinely let them decide, including when I'd have chosen differently, because the lesson is in carrying the outcome. I'd be explicit about the scope: "this is yours, here's the boundary, here's what I need to see in your rationale."

Second, I'd work on the *articulation* of decisions, not just the making of them. A decision that isn't defended with reasoning is one that gets overridden by the loudest voice. So I'd coach them on structuring a decision: options considered, criteria, trade-offs, what would change their mind, and the recommendation. Practicing that in a low-stakes review builds the muscle for the high-stakes one.

Third, I'd address the deference pattern directly but without judgment — name it, explain why it matters (a team that only hears from the most senior person loses the judgment of everyone else), and give them a concrete behavior to practice, like being the first to state a position in a review rather than the last. I'd also model disagreeing with senior people myself, so they see it's safe.

Finally, I'd track it over time — not with a formal review, but by progressively widening the scope of what they own and checking whether the deference is fading.

**Possible follow-ups:**
- How would you handle it if the engineer's first owned decision goes badly — do you step in, and how?
- What would you do if the deference is driven by a real power dynamic, such as a very dominant senior engineer in the room?