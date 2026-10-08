# behavioral-leadership — Day 79

## Q1: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?
**Answer:** The first move is to resist the pressure to jump straight to a fix, because an intermittent failure that isn't understood will usually come back. I'd separate the work into two parallel tracks: a short-term containment track and a longer-term root-cause track. Containment means reducing the blast radius — adding logging, tightening a guard condition, or limiting the operating envelope — while being explicit that containment is not a fix and must be tracked as temporary.

For the root-cause track, the core problem with intermittent failures is observability, so I'd invest first in instrumentation rather than guessing. That means capturing the state leading up to the event: timestamps, sensor readings, power rail behavior, task scheduling, and any error counters, ideally with enough resolution to see the sequence of events rather than just the final symptom. If the failure can't be triggered on demand, I'd try to widen the conditions under which it appears — temperature cycling, voltage margining, load variation, longer soak runs — to convert an intermittent into a reproducible one.

Structurally I'd use a disciplined method like 8D or a fishbone to keep the team from anchoring on the first plausible cause. The fishbone forces the group to consider multiple categories — hardware, firmware, environment, power, timing, user interaction — instead of converging prematurely. The 5 Whys is useful once a candidate cause is identified, but it's dangerous as a starting point because it can lead you down a single chain too early. I'd also make sure the team distinguishes between correlation and causation; an intermittent bug that appears after a firmware change may have nothing to do with that change.

Finally, I'd define what "verified fix" means before declaring victory. For an intermittent issue, that usually means a soak test or accelerated stress test that would have caught the original failure at some reasonable confidence level, not just "it hasn't happened in a week." I'd document the reasoning, the evidence, and the residual uncertainty so the decision to ship is an informed one rather than a hopeful one.

**Possible follow-ups:**
- How would you decide when containment is good enough to ship while root-cause work continues?
- What would you do if the instrumentation itself changes the timing enough to mask the failure?

## Q2: How would you approach a design review where the presenter is technically strong but consistently becomes defensive when their work is questioned, and the review needs to be genuinely critical to be useful?
**Answer:** The defensiveness is usually a signal that the person reads critique of the design as critique of themselves, so the first thing I'd change is the framing of the review itself, not the person. I'd set expectations at the start that the purpose is to find problems while they're cheap to fix, and that a review where nothing is challenged is a failed review. Making that a norm for everyone — including me presenting my own work and getting challenged — removes the sense that the presenter is being singled out.

In the session, I'd steer questions toward the design rather than the designer: "What happens if this input goes out of range?" rather than "Why didn't you consider this?" I'd also front-load genuine strengths before moving into risks, not as flattery but because it establishes that the review is balanced. When a concern comes up, I'd ask the presenter to walk through their reasoning rather than defend a conclusion — often the act of explaining surfaces the gap themselves, which is far less threatening than being told.

If the pattern persists across sessions, I'd address it privately rather than in the room. The conversation would be specific and behavioral: name what happened, describe the effect on the review (other reviewers stop raising concerns, which is worse for the design), and ask what would make it easier for them to receive critique. Sometimes the root cause is that they've been burned by a review that turned into an ambush, or they feel the review is being used to second-guess decisions that were already made. Understanding that changes the intervention.

I'd also protect the review process itself. If reviewers start softening their questions to avoid the reaction, the review becomes theater. I'd rather have a slightly uncomfortable review that catches a real issue than a smooth one that misses it.

**Possible follow-ups:**
- What would you do if the engineer's manager doesn't see the defensiveness as a problem?
- How would you handle it if a junior reviewer is the one being shut down by this person's reactions?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?
**Answer:** The goal is to give the firmware team a model they can reason about, not a lecture on analog design. I'd start by characterizing the constraint in terms of what it means at the firmware boundary: what's the effective number of bits after noise, what's the noise floor in the units the firmware cares about, what's the sample-to-sample variation, and what's the frequency content of the noise. That's the information a firmware engineer needs to decide on filtering, averaging, or sample timing.

I'd avoid two failure modes. The first is oversimplifying to "the ADC is noisy, just filter it" — that gives the firmware team no basis for choosing a filter or knowing when they've done enough. The second is handing over a full noise analysis with spectral plots and expecting them to extract the actionable part. The middle ground is a short document or conversation that states the constraint, shows one or two representative measurements, and explicitly states the assumptions the firmware can rely on — for example, "the noise is dominated by low-frequency drift below X Hz, so a simple moving average over N samples is appropriate" or "there's a switching artifact at a known frequency that averaging won't remove."

I'd also make the constraint testable. If the firmware team implements a filter, how do we know it's working? That means agreeing on a measurement — a known input, a captured dataset, a test fixture — so both teams can verify the result against the same reference. Without that, the conversation becomes opinion versus opinion.

Finally, I'd keep the interface explicit: what the hardware guarantees, what it doesn't, and what the firmware is responsible for compensating. Ambiguity at that boundary is where integration bugs live.

**Possible follow-ups:**
- How would you handle it if the firmware team's proposed filter introduces latency that violates a system timing requirement?
- What would you do if the noise characterization changes after a hardware revision?

## Q4: How would you approach deciding how much technical detail to include when presenting a design trade-off to a mixed audience of engineers, a quality manager, and a product manager in the same room?
**Answer:** I'd structure the presentation in layers so each audience can engage at the depth they need, rather than trying to find a single level that satisfies everyone. The top layer is the decision itself: what we're choosing between, what the trade-off is in plain terms, and what I'm recommending. That layer has to stand on its own for the product manager and anyone else who won't go deeper.

The second layer is the reasoning: the key criteria, the evidence behind each option, and the risks. This is where the quality manager usually engages, because their concerns are typically about risk, traceability, and whether the decision is defensible. I'd make sure that layer explicitly addresses regulatory or safety implications, because if it doesn't, the quality manager will ask — and it's better to have anticipated it.

The third layer is the technical detail: measurements, calculations, test data, and the assumptions behind them. I'd keep this available but not front-loaded. Engineers in the room will want it, and I'd rather have it in an appendix or a backup slide than force the whole room through it. If a technical question comes up, I can go there; if it doesn't, the meeting stays efficient.

The other thing I'd do is be explicit about what's still uncertain. Mixed audiences often read confidence as certainty, and a design trade-off presented as settled when it isn't can create problems later. Saying "this is my recommendation, and here's what would change my mind" gives the room a way to engage with the decision rather than just receive it.

**Possible follow-ups:**
- How would you handle it if the product manager pushes for a decision before the technical evidence is complete?
- What would you do if the quality manager raises a concern that the engineers in the room dismiss as overly conservative?

## Q5: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?
**Answer:** The pattern usually isn't a capability gap — it's that the engineer has never been in a position where the decision was theirs to make, so deferring has been a safe and rational strategy. The mentoring work is to create those positions deliberately, in a way that's low-risk enough that a wrong call doesn't become a career event.

I'd start by giving them ownership of a decision with real but bounded consequences: a component selection, a subsystem architecture, a test approach. The key is that it's genuinely theirs — I'd resist the urge to step in when they're working through it, even if I'd have decided differently. If I intervene every time, I've taught them that deferring is still the right move.

I'd also make the reasoning visible. When they bring a decision to me, I'd ask them what they'd choose and why, before offering my view. That flips the default from "what do you think?" to "here's my thinking, does it hold up?" Over time, that builds the habit of forming a position first. I'd also model the same behavior — walking through my own decisions, including the ones I got wrong, so they see that owning a decision isn't the same as being infallible.

For the deference-to-seniority habit specifically, I'd name it directly but without judgment: point out when it happens, and ask what they actually think. Sometimes the person doesn't realize they're doing it. And I'd create situations where they're the most senior person in the room on a topic, so the deference reflex has nowhere to go.

The measure of progress isn't that they stop asking for input — it's that they start bringing a position to the conversation rather than an open question.

**Possible follow-ups:**
- How would you handle it if a decision they own goes badly and they retreat back to deferring?
- What would you do if other senior engineers on the team keep bypassing them and going straight to you?