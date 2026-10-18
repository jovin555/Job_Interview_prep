# behavioral-leadership — Day 89

## Q1: How would you approach a design review where the presenter has done solid technical work, but the review package arrives late and is missing the calculations that justify a safety-critical decision, and the meeting is the only slot before a milestone gate?

**Answer:** The instinct in that situation is to either wave it through because the work is probably fine, or to cancel the review and slip the milestone. Both are wrong. The right move is to run the review but explicitly re-scope it: separate what can be genuinely reviewed today from what cannot, and make that split visible in the minutes.

Concretely, I'd open by acknowledging the constraint out loud — "we have one slot before the gate, and the package is missing the trace-width and thermal-margin calculations for the safety-critical section." Then I'd walk the package in two passes. First pass: everything that doesn't depend on the missing calculations — architecture, component selection, interface definitions, layout topology, test coverage — gets a full review, because that work is real and the team's time is valuable. Second pass: I'd mark the safety-critical items as "reviewed for approach, not verified for margin," and record them as open action items with an owner and a date, not as approved.

The key discipline is that a milestone gate is a decision point, not a rubber stamp. If the gate criteria require documented justification for safety-critical decisions, then the honest outcome is a conditional pass with a hard follow-up: the calculations get reviewed asynchronously by a named second reviewer within a defined window, and if they don't hold up, the gate reopens. That protects the schedule without pretending the review was complete.

I'd also treat the late package as a process signal, not just a one-off. If review packages are routinely arriving late, the fix is upstream — a package-readiness checklist circulated a few days before the review, with the presenter confirming the safety-critical calculations are included. That's cheaper than repeatedly running half-reviews at gates.

**Possible follow-ups:**
- If the presenter pushes back and says the calculations exist but just weren't written up, how do you handle that in the room?
- How do you keep a conditional pass from becoming the default outcome at every gate?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures are where teams most often skip straight to a plausible fix and declare victory, and that's exactly the trap to avoid. The pressure to ship makes it tempting, but an unverified fix on an intermittent problem usually means the issue returns — often after release, which is far more expensive.

My approach starts with containment, kept explicitly separate from correction. Containment means reducing exposure while the investigation runs: tightening screening at test, adding a temporary workaround, increasing monitoring in the field, or holding a batch. Containment is allowed to be imperfect and temporary; it just has to be documented as such so nobody mistakes it for the real fix.

For the investigation itself, the core problem is that you can't reproduce on demand, so you have to change the economics of reproduction. That means instrumenting rather than guessing: adding logging around the suspect subsystem, capturing timestamps and state at the moment of failure, and running stressed or corner-case conditions (temperature extremes, supply margins, timing skew, EMC exposure) to raise the failure rate from "rare" to "observable." A failure you can trigger even once every few hundred cycles is investigable; one you can't trigger at all is not.

Then I'd apply structured analysis rather than intuition — a fishbone to enumerate candidate causes across hardware, firmware, environment, and test setup, and 5 Whys on whatever data the instrumentation yields. Crucially, I'd form explicit hypotheses and design a test that could *disprove* each one, rather than collecting evidence that confirms a favorite theory. The team should agree in advance what result would rule a cause out.

Finally, verification of effectiveness: the fix isn't done when the symptom stops appearing in a short run — it's done when you can show the mechanism is understood and the failure rate has dropped under conditions that previously provoked it. If you can't explain *why* the fix works, you don't yet have a root cause.

**Possible follow-ups:**
- How do you decide when you've done enough investigation to ship, given the pressure to move?
- What do you do if the instrumentation itself changes the timing enough that the failure disappears?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode in both directions is real. Oversimplify and the firmware team designs a filter around a problem they don't understand; over-detail and they disengage and just implement whatever was in the last email. The bridge is to translate the constraint into the *decisions it affects* on their side, backed by just enough numbers to make it credible.

I'd start from what the firmware team actually has to decide: how much averaging to do, what sample rate is realistic, whether a calibration step is needed, what tolerance to assume in their thresholds, and where in the signal chain their processing can and can't recover information. Then I'd express the hardware reality in those terms. For an ADC, that means stating effective resolution — not just the datasheet bit count, but the noise floor in LSBs at the relevant sample rate, so they know how many bits are actually usable. For a noisy front end, it means characterizing the noise: is it broadband, is it a specific frequency (say, switching supply ripple), is it correlated with a load event? That determines whether averaging helps or whether they need a notch or synchronous sampling.

The framing I find most useful is a short written interface note — a page, not a treatise — that states the constraint, the measured numbers behind it, the implications for firmware, and what is *not* recoverable in software. That last part matters most: telling them clearly "you cannot average your way out of this because it's a DC offset drift, not random noise" saves weeks.

I'd also offer a joint characterization session — put the hardware on a bench with the firmware engineer and capture real data together, so the numbers aren't abstract. Shared data resolves more ambiguity than any document.

**Possible follow-ups:**
- How do you handle it when the firmware team proposes a software fix that you believe is masking a hardware problem?
- What goes in the interface note if the hardware characterization isn't finished yet?

## Q4: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This pattern usually isn't a capability gap — it's a confidence and habit gap. The engineer has proven they can execute, but ownership is a different skill: forming a judgment, defending it, and living with the consequences. Deferring to the most senior person is a rational short-term strategy that has probably been rewarded, so the mentoring has to change what gets rewarded.

I'd start by giving them genuine ownership of something bounded but real — a subsystem decision, a component selection, a test strategy — with a clear statement up front that the decision is theirs and I will not overrule it unless there's a safety or compliance reason. That last clause matters: it tells them the delegation is real while keeping the guardrails honest.

The second piece is changing the conversation in reviews. Instead of asking "what do you think we should do?" — which invites deference — I'd ask them to state their recommendation *first*, before anyone senior speaks, and to give the reasoning and the trade-off they rejected. Making the junior voice go first in the room is a small structural change that does a lot of work.

Third, I'd make the reasoning visible rather than the answer. When they defer, I'd ask "what would you need to know to decide this yourself?" — which turns deference into a learning moment about what information they're missing, rather than a judgment about their ability. Over time they build a mental model of how decisions get made, not just what the senior person concluded.

And I'd be explicit that being wrong is part of the deal. If the only decisions that get praised are the ones that turn out right, deference is the safe play. I'd make a point of discussing decisions that didn't pan out, including my own, so the engineer sees that ownership and fallibility coexist.

**Possible follow-ups:**
- How do you handle it if the senior person in the room keeps answering for them despite your efforts?
- How would you tell whether the mentoring is working, without waiting for a big decision to go well?

## Q5: How would you approach leading a technical decision when the team is split between two viable architectures and the disagreement has become personal rather than technical, with each side attributing bad motives to the other?

**Answer:** Once a technical disagreement turns personal, more debate makes it worse — each side starts collecting evidence for their position and interpreting the other's motives rather than their arguments. The first job is to de-escalate the *frame*, then re-ground the decision in criteria both sides accept.

I'd start by naming the dynamic plainly but without blame: "we've moved from arguing about the design to arguing about each other, and that's not serving the decision." Then I'd reset the conversation around a shared decision framework. That means, before any further advocacy, getting both sides to agree on the criteria that matter — cost, schedule, risk, manufacturability, testability, regulatory burden, long-term maintainability — and, critically, on how those criteria are weighted for *this* product. A lot of architecture disputes dissolve once both sides realize they're optimizing for different criteria and neither has said so.

Next, I'd convert opinion into evidence wherever possible. If the disagreement is about, say, reliability or timing margin, a focused prototype or a bench measurement can settle it faster than another meeting. Where a prototype isn't feasible, I'd ask each side to write down their top three risks with the other architecture and their proposed mitigation — this forces steelmanning and often reveals that the "losing" side's concerns are addressable within the "winning" design.

On the personal dimension: I'd separate the people from the positions by having the discussion in a smaller setting first, and by making sure both engineers' concerns are visibly recorded in the decision record, including the ones not adopted. People accept a decision they lost if they believe it was heard fairly and can point to their concern in the record.

Finally, if the split persists after criteria and evidence, that's a decision I own as the lead — I'd make it, document the rationale and the dissenting view, and set a review point to revisit if the chosen path shows the predicted problems. Escalation upward is a last resort, because it teaches the team that disagreement gets outsourced rather than resolved.

**Possible follow-ups:**
- How do you rebuild working trust between the two engineers after the decision is made?
- What would make you decide the disagreement genuinely needs to go to your manager rather than being resolved in the team?
- How do you document a decision with a dissenting view without it reading as a hedge?