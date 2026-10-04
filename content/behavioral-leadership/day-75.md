# behavioral-leadership — Day 75

## Q1: How would you approach a design review where the presenter is technically strong but consistently becomes defensive when their work is questioned, and the review needs to be genuinely critical to be useful?

**Answer:** The core problem is that the review's purpose — finding problems before they reach production — is in direct tension with the presenter's instinct to defend their work. If I don't address that tension, the review degrades into either false consensus (nobody raises hard questions) or open conflict (questions feel like attacks). Neither produces useful output.

My approach starts before the meeting. I'd talk to the presenter privately and reframe what the review is for: the goal is not to evaluate them, it's to stress-test the design while changes are still cheap. I'd be explicit that a review where nothing is challenged is a failed review, and that the most valuable reviewers are the ones who find the issues the designer couldn't see because they were too close to the work. Framing critique as a service to the design rather than a judgment of the person changes the emotional stakes.

In the meeting itself, I'd model the behavior I want. When I raise a concern, I'd phrase it as a question about the design's behavior under specific conditions rather than a verdict — "What happens to the sensor reading during the wake-up transition if the reference hasn't settled?" rather than "This is wrong." I'd also deliberately separate the phases: first, walk through the design and let the presenter explain their reasoning without interruption; then, open the floor for questions. That gives the presenter a chance to be heard before being challenged, which reduces the sense of ambush.

If defensiveness still surfaces, I'd acknowledge the concern rather than dismiss it — "That's a fair point, and it may well be fine; let's capture it as an action to verify" — and move on. The key is not to win the argument in the room but to make sure the question gets recorded and answered, even if the answer comes later. I'd track every open question as an action item with an owner and a due date, so nothing gets lost to social friction.

Over time, the fix is cultural: if reviews consistently produce useful findings that get acted on, and if senior people visibly accept critique of their own work, defensiveness loses its rationale. But that's a slow build, and in the meantime I'd rather have an awkward review that catches a real issue than a smooth one that doesn't.

**Possible follow-ups:**
- How would you handle it if the presenter's defensiveness is causing junior engineers to stop asking questions entirely?
- What would you do if the presenter's manager tells you the reviews are "too harsh" and asks you to soften them?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures under schedule pressure are the worst combination, because the pressure pushes toward a fix before the cause is understood — and a fix applied to an unknown cause is just a guess that may mask the problem or introduce a new one. My first move is to resist that pressure explicitly and get agreement on what "done" means: not "the symptom stopped" but "we understand the mechanism and can show the fix addresses it."

The investigation itself has to be structured around capturing the failure rather than waiting for it. If it can't be reproduced on demand, the priority is instrumentation: add logging, counters, or trace capture around the suspect subsystems so that when the failure does occur, you have data instead of a story. In embedded systems this often means ring buffers that survive a reset, watchdog-triggered dumps, or long-duration soak testing with continuous monitoring. The goal is to convert a rare event into a recorded one.

In parallel, I'd build a hypothesis list and rank by likelihood and by how cheaply each can be tested. A fishbone or fault-tree exercise with the team is useful here — not for ceremony, but because intermittent failures often have multiple contributing conditions (a timing margin that's only violated at temperature extremes, a race that only manifests under a specific interrupt load), and the diagram forces those combinations onto the table. Then I'd design experiments that can discriminate between hypotheses rather than just confirm the favorite one.

Containment is separate from correction. If the schedule genuinely can't wait, I'd ship a containment — a conservative workaround, a tightened operating envelope, additional monitoring — clearly labeled as temporary, with the investigation continuing. What I would not do is present a containment as a root-cause fix, because that's how the same failure comes back in the field with no investigation trail.

Finally, verification of effectiveness: once a fix is in, I'd define in advance what evidence would show the failure is actually gone — a soak test of sufficient duration, a specific counter staying at zero, a stress condition that previously triggered it. Without that, "we haven't seen it since" is not evidence.

**Possible follow-ups:**
- How would you decide how long a soak test needs to run before you can reasonably claim the fix worked?
- What would you do if the failure rate is so low that even a long soak test is unlikely to trigger it?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode on both sides is the same: the firmware team ends up either not understanding the constraint at all, or understanding it so abstractly that they can't make design decisions with it. The fix is to translate the constraint into the terms the firmware actually operates in — numbers, timing, and behavior — rather than leaving it as a hardware description.

Concretely, for something like ADC resolution or front-end noise, I'd characterize the constraint as a set of measurable properties the firmware can reason about: the effective number of bits after noise, the noise floor in LSBs, the settling time required after a channel switch or a gain change, the frequency content of the noise, and how those vary with temperature or supply. That's the information the firmware team needs to decide things like how many samples to average, whether to use a digital filter and of what order, how long to wait before sampling after a mux change, and what resolution is actually meaningful versus what's just quantization noise.

I'd also give them the "so what" explicitly. If the effective resolution is lower than the datasheet's nominal bits, the firmware team needs to know that a single reading is not trustworthy and that averaging or oversampling is required — and roughly how much. If the noise has a periodic component, they need to know its frequency so they can avoid aliasing it into the signal band. That's the difference between handing over a spec sheet and handing over a design constraint.

The other half is making it a conversation, not a broadcast. I'd sit with the firmware lead and walk through the measurements, ideally with a scope or a data capture so they can see the noise rather than just read a number. And I'd ask them what they need to know that I haven't told them — often the firmware team will surface a question (like behavior during a supply brownout, or the settling time after a reset) that the hardware characterization didn't cover, and that's exactly the kind of gap that causes integration surprises later.

The test of whether the translation worked is whether the firmware team can make a design decision without coming back to ask what the hardware "really means." If they can, the constraint was communicated at the right level.

**Possible follow-ups:**
- How would you handle it if the firmware team's proposed filtering approach would add latency that the application can't tolerate?
- What documentation would you produce so this constraint survives beyond the people in the room?

## Q4: How would you approach deciding how much technical detail to include when presenting a design trade-off to a mixed audience of engineers, a quality manager, and a product manager in the same room?

**Answer:** The instinct is to find a single level of detail that works for everyone, and that usually fails — it's either too shallow for the engineers or too deep for the product manager, and the quality manager is often listening for something neither of the other two cares about. The better approach is to structure the presentation in layers, so each audience can engage at the depth they need without forcing everyone through the same content.

I'd start with the decision itself and the recommendation, stated plainly: what we're choosing between, what I recommend, and why — in one or two sentences. That gives everyone the headline and the "so what" immediately, and it means the product manager isn't waiting through ten minutes of analysis to find out whether the schedule is affected.

Then I'd layer the justification. The first layer is the trade-off in business or project terms: cost, schedule, risk, regulatory impact. That's the layer the product manager and quality manager care about most. The second layer is the technical reasoning — the measurements, the analysis, the assumptions — which the engineers need but which the others can tune out without losing the thread. The third layer is the supporting detail: the raw data, the calculations, the references, kept in an appendix or a linked document rather than presented live.

The quality manager is a special case worth planning for. Their concern is usually not "which option is better" but "is the decision justified, documented, and traceable" — so I'd make sure the presentation explicitly covers the rationale, the assumptions, the residual risk, and how the decision will be recorded. If that's missing, the quality manager will (correctly) hold up the decision regardless of how good the technical case is.

Throughout, I'd watch for the signal that I've lost someone — a question that reveals a gap, or silence from a group that should be engaged — and adjust. And I'd end with a clear statement of what decision is being asked for, who needs to agree, and by when, so the meeting produces a decision rather than a discussion.

**Possible follow-ups:**
- How would you handle it if the product manager pushes back on a technical recommendation they don't fully understand?
- What would you do if the quality manager wants more documentation than the schedule allows before the decision can be made?

## Q5: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This is a common and often under-diagnosed pattern: the engineer is capable, but they've learned that deferring is safe and that owning a decision exposes them to being wrong in public. The mentoring goal isn't to make them more assertive as a personality trait — it's to build their capacity to own a decision and defend it with reasoning, which is a skill, not a temperament.

I'd start by giving them a decision to own that's genuinely theirs, with a clear boundary: this is your call, here's the scope, here's what I need from you when you bring it back. The key is that the decision has to be real — if I reserve the right to override it on a whim, they'll correctly conclude that owning it is theater. I'd make clear up front what would cause me to step in (safety, regulatory, or a factual error) and that everything else is theirs to decide and defend.

When they bring the decision back, I'd resist the urge to evaluate the answer first. Instead I'd ask them to walk me through their reasoning: what options they considered, what they ruled out and why, what assumptions they made, what would change their mind. That does two things — it forces them to practice articulating a decision, and it surfaces whether they actually reasoned it through or just picked the option they thought I'd want. If it's the latter, that's the coaching moment, and it's much more useful than me just telling them the "right" answer.

I'd also work on the deferring behavior directly. In meetings, when they look to the most senior person before answering, I'd redirect: "What's your read on this?" — not to put them on the spot, but to make the deferral visible and give them a chance to practice. Over time, the goal is that they answer first and the senior person responds, rather than the reverse.

The measure of progress isn't that they become the loudest voice in the room. It's that they can make a decision, explain it, and hold it under questioning — and that they know when to change their mind because of new evidence rather than because someone senior disagreed.

**Possible follow-ups:**
- How would you handle it if the engineer makes a decision you disagree with, but their reasoning is sound?
- What would you do if the deferring behavior is reinforced by a senior engineer who likes being the one everyone defers to?