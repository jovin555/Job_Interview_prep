# behavioral-leadership — Day 93

## Q1: How would you approach a design review where the presenter is technically strong but the review package arrives late and is missing the calculations that justify a safety-critical decision, and the meeting is the only slot before a milestone gate?

**Answer:** The instinct is to either cancel the review or wave it through on the strength of the presenter's reputation — both are wrong. I'd start by separating what the review can legitimately accomplish today from what it cannot. A design review has two jobs: catching technical problems and producing a documented, defensible record that the decision was scrutinized. Missing calculations undermine the second job even if the first is satisfied by the presenter's verbal explanation.

Practically, I'd open the meeting by naming the gap explicitly and neutrally: "The package is missing the trace-width and thermal margin calculations for the safety-critical path. We can still review the architecture and the risk controls today, but we cannot close out the safety-critical items without the numbers." Then I'd run the review in two passes — cover everything that doesn't depend on the missing calculations, capture those as reviewed, and formally park the safety-critical items as open actions with an owner and a date. The milestone gate gets a conditional status: the design review is complete except for a defined, small set of items that must close before the gate is actually passed. That's honest to the process and doesn't hold the whole review hostage to one person's late package.

I'd also address the pattern privately afterward. A late, incomplete package before a milestone gate is usually a symptom — the presenter may be overloaded, may not understand what "sufficient evidence" means for a safety-critical decision, or may be avoiding scrutiny. The fix differs by cause, so I'd ask rather than assume. If it's a standards problem, the answer is a review-package checklist that makes the expected contents explicit and a rule that packages are circulated a set number of days ahead. If it's workload, that's a resourcing conversation.

The key leadership move is refusing to let the milestone gate become a fiction. A gate that gets passed with undocumented safety-critical decisions is worse than a gate that slips by a week, because it teaches the team that the process is theater.

**Possible follow-ups:**
- If the presenter pushes back and says the calculations exist and they can walk you through them verbally, do you accept that as sufficient to close the item?
- How do you keep the conditional gate status from becoming a permanent loophole that other projects start relying on?

## Q2: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode in both directions is the same: the firmware team ends up either not believing the constraint is real, or not knowing what to do about it. Oversimplifying ("the ADC is noisy, just filter it") invites a firmware fix that masks the problem instead of respecting it. Over-detailing (a full noise analysis with spectral plots and no conclusion) gets skimmed and ignored.

What works is translating the constraint into a small number of actionable statements with numbers attached, framed in terms of what the firmware can and cannot rely on. For an ADC, that means something like: effective resolution at the sample rate you'll actually use, the noise floor in LSBs, the input range and where the signal of interest sits within it, and the sampling timing assumptions the hardware was designed around. Then the crucial part — the implication: "you cannot resolve changes smaller than X without averaging over N samples, and averaging over N samples costs you Y milliseconds of latency." Now the firmware team has a trade-off they can reason about rather than a vague warning.

I'd deliver it as a short written interface note, not a meeting, because firmware needs to refer back to it during implementation. The note should state the assumptions the hardware makes about firmware behavior — sample timing, reference settling, when the analog front end is allowed to be reconfigured — because those are the places where firmware can silently invalidate the hardware design. And I'd invite the firmware lead to challenge the numbers, because if they find a case where the constraint doesn't hold, that's valuable information, not insubordination.

The test of a good translation is whether the firmware team can make a design decision without coming back to ask what you meant. If they keep returning with clarifying questions, the note wasn't specific enough.

**Possible follow-ups:**
- How would you handle it if the firmware team proposes an averaging scheme that meets the latency budget on paper but you suspect will interact badly with the analog front end's settling behavior?
- What do you do when the hardware constraint genuinely can't be met by any reasonable firmware approach — who owns the decision to change the hardware?

## Q3: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This pattern is usually not a confidence problem — it's a habit formed in an environment where someone else always carried the decision risk. The engineer has learned that deferring is safe and that owning a decision exposes them to being wrong in public. Mentoring has to change the incentive structure, not just tell them to speak up.

I'd start by giving them genuine ownership of something with real consequences but bounded blast radius — a subsystem decision, a component selection, a test approach — and then deliberately not rescuing them. The hard part for a mentor is staying quiet when the engineer is working through a decision you could resolve in thirty seconds. If I answer every question, I've taught them that deferring works. Instead I'd redirect: "What are the two options you're weighing, and what would make you pick one?" That forces the reasoning out where it can be examined.

The second piece is making the reasoning visible and reviewable rather than the outcome. I'd ask them to write a short decision record for each significant choice — options considered, criteria, what would change their mind. This does two things: it gives them practice articulating a decision, and it gives me a concrete artifact to critique that isn't a personal judgment of them. Over time the record becomes evidence they can point to when someone more senior questions the choice, which reduces the social risk of owning it.

Third, I'd address the room dynamic directly. In reviews, I'd explicitly route questions to them first rather than letting a senior person answer, and I'd name the behavior when it happens — "let's hear the owner's view before we open it up." That's a small structural change that shifts who is expected to speak.

I'd measure progress by whether they start disagreeing with senior engineers on technical grounds and can defend it. That's the real milestone, not whether they seem more confident.

**Possible follow-ups:**
- What if the engineer's first independent decision turns out badly — how do you handle that so it doesn't reinforce the deferring habit?
- How do you get the senior engineers in the room to stop answering for them, without making it feel like you're policing them?

## Q4: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** The pressure to ship a fix is exactly what makes intermittent failures dangerous — the fastest-looking fix is usually a guess that suppresses the symptom and leaves the cause in place, and in a medical device that guess ships to patients. So the first leadership act is to reframe the pressure: a fix that doesn't address the cause isn't a fix, it's a delay with extra steps. That said, "we need more time" is not an acceptable answer on its own, so the investigation has to be structured to produce something useful fast.

I'd separate containment from correction immediately. Containment is legitimate and can move quickly: tighten the acceptance test, add a diagnostic log, restrict the operating envelope, increase sampling in the field — whatever reduces the chance of harm or of the failure escaping while the real investigation proceeds. Containment buys time honestly, as long as everyone understands it's containment and not closure.

For the investigation itself, the core problem with intermittent failures is that you can't study what you can't capture. So the first investment is instrumentation: what state was the system in when it failed, what was the sequence of events, what was the environmental context. If the failure leaves no trace, the highest-value work is making it leave a trace — logging, counters, watchdog capture, a flight-recorder buffer that dumps on reset. That's often a day of work that turns an unreproducible failure into a reproducible one.

Then I'd structure the hypothesis space rather than chase symptoms. A fishbone or fault-tree pass forces the team to enumerate candidate causes across hardware, firmware, environment, and use conditions, and to say for each one what evidence would confirm or eliminate it. That converts a vague "it's flaky" into a set of specific things to look for. I'd assign each hypothesis an owner and a discriminating test, and I'd prioritize the ones that are cheap to eliminate — ruling things out is progress even when nothing is confirmed.

I'd also insist on recording the investigation as it happens, not reconstructing it later. Intermittent failures have a way of disappearing after a change, and if you don't know which change fixed it, you don't know whether it's fixed. Verification of effectiveness matters more here than anywhere: the fix isn't done until you can state what conditions would have triggered the failure and show they no longer do.

**Possible follow-ups:**
- How do you decide when containment has gone on long enough that it's effectively become the permanent fix by default?
- If the failure rate is very low and instrumentation is expensive, how do you justify the cost of capturing it versus accepting the risk?

## Q5: How would you approach leading a technical decision when the team is split between two viable architectures and the disagreement has become personal rather than technical, with each side attributing bad motives to the other?

**Answer:** Once a disagreement turns personal, the technical merits stop being the binding constraint — no amount of additional analysis will resolve it, because each side reads new evidence as ammunition rather than information. So the first job is to de-escalate the framing before doing any more engineering.

I'd start by getting the two positions written down in a shared form: not "Architecture A vs. Architecture B" as camps, but a criteria matrix — what does this design actually need to do, weighted by importance. Cost, power, schedule risk, regulatory complexity, testability, long-term maintainability, supply risk. The point is to move the argument from "whose idea is better" to "which option scores better against criteria we all agreed to." That reframing is often enough to break the personal dynamic, because people will argue about weights and scores in a way they won't argue about each other's competence.

I'd also name the dynamic directly but without accusation — something like "I'm hearing us attribute motives to each other rather than examine the trade-offs, and that's going to cost us a good decision." Naming it in the room, calmly, usually resets the tone. If it doesn't, I'd take the two principals aside separately and ask each to state the other side's position fairly enough that the other would accept the summary. If they can't, they don't understand the position they're opposing, and that's the real problem to work on.

Where the disagreement is genuinely close, prototyping to resolve it is often the fastest path — a bounded, time-boxed spike that produces evidence neither side can dismiss as opinion. I'd frame it as "we're not deciding who's right, we're buying information," which lets both sides contribute without losing face.

Finally, whatever gets decided, I'd document the decision with the rationale and the dissenting view recorded. People accept decisions they lost more readily when the record shows their concern was heard and the reasoning was explicit. And if the losing side turns out to be right later, that record is what lets the team revisit the decision without it being about who won.

**Possible follow-ups:**
- What if one of the two engineers is significantly more senior, and the other side reads any process you impose as legitimizing the senior person's position?
- How do you handle it if, after the criteria matrix, the two options score essentially identically — do you just pick one, and how do you bring the other side along?