# behavioral-leadership — Day 85

## Q1: How would you approach a design review where the presenter's package is technically solid but arrives late and is missing the calculations that justify a safety-critical decision, and the meeting is the only slot before a milestone gate?

**Answer:** The instinct to either rubber-stamp the review to protect the schedule or cancel it outright are both wrong, because both trade a short-term convenience for a long-term risk. The right move is to separate the review into two parts: what can be genuinely evaluated today, and what cannot.

First, I'd open the meeting by naming the situation plainly rather than letting it sit unspoken — the package arrived late, and a specific safety-critical calculation is missing. Naming it removes the awkwardness and lets the team focus. Then I'd walk through what *is* reviewable: architecture, interfaces, component selection, test coverage, and any portions where the reasoning is complete. For the missing calculation, I would not approve it by default. Instead I'd ask the presenter to walk the reviewers through the reasoning verbally, and capture that reasoning as a review action item with an owner and a due date — the calculation must be written up and independently checked before the gate is considered closed.

The key discipline is that a milestone gate is not a meeting; it's a state of the design. If the calculation is genuinely safety-critical, the gate cannot be passed until it exists and has been reviewed. I'd communicate that clearly to whoever owns the schedule, framing it as "the review is 90% complete, with one blocking item that has a defined path to closure" rather than "the review failed." That gives the project manager something actionable instead of a binary.

I'd also treat the late package as a process signal worth examining separately from the technical content — was this a one-off, or is the review-preparation step being chronically squeezed? That's a conversation for after the gate, not during it.

**Possible follow-ups:**
- If the presenter pushes back and says the calculation was done informally and they're confident in it, how do you respond without turning the review into a confrontation?
- How would you decide whether the missing calculation is truly blocking or whether it can be deferred to a later verification stage?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures are the hardest class of problem because the pressure to ship creates a strong pull toward a plausible-sounding fix that may not address the actual root cause. The framework I'd use is containment first, root cause second, and I'd be explicit with stakeholders about the difference.

Containment means: what can we do right now to reduce the impact or probability of the failure while we investigate? That might be a firmware guard, an added self-test, a derating of an operating parameter, or a more conservative default. Containment is not a fix — it's a stopgap — and it must be labeled as such so it doesn't quietly become the permanent answer.

For the investigation itself, when you can't reproduce on demand, the goal shifts from "reproduce the failure" to "increase the observability of the system so that when it does fail, you capture the conditions." That means instrumenting the device — logging, counters, timestamps, environmental capture — and deploying that instrumentation into the field or into a stress environment where the failure is more likely to occur. You're essentially turning a rare event into a data-generating event.

In parallel, I'd use a structured method like 8D or a fishbone to enumerate candidate causes across hardware, firmware, environment, and user interaction, then design targeted experiments that can *falsify* each candidate rather than confirm a favorite. The team's natural bias is to jump to the cause they already suspect; the discipline is to make each hypothesis earn its place.

Finally, I'd resist declaring victory on the basis of "it hasn't happened since we changed X." Verification of effectiveness requires either a mechanism-level explanation of why the fix addresses the root cause, or a statistically meaningful period of observation — and for an intermittent failure, "it stopped happening" is weak evidence unless you understand *why*.

**Possible follow-ups:**
- How do you keep the team from treating containment as the fix once the pressure eases?
- What would you do if the instrumentation itself changes the behavior of the system enough that the failure no longer occurs?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode here is usually one of two extremes: either the hardware engineer says "the ADC is noisy, deal with it" and leaves the firmware team guessing, or they dump a full noise characterization on the firmware team and expect them to derive the implications themselves. Neither works. The right approach is to translate the constraint into the *decisions* the firmware team actually has to make.

Concretely, that means starting from the firmware's perspective: what are they trying to do with this signal? If they're sampling a slow-moving physiological parameter, the relevant facts might be the noise floor in LSBs, the effective number of bits at the sampling rate they'll use, and the frequency content of the noise. If they're trying to detect a fast transient, the relevant facts are different — settling time, sample-and-hold behavior, and the aliasing implications of their chosen sample rate.

I'd present the constraint as a small set of numbers with clear meaning: "at your target sample rate, you have roughly N effective bits of resolution, and the noise is concentrated below X Hz." Then I'd name the implications explicitly: "this means a simple moving average over K samples will get you to the resolution you need, but it will also add latency of L milliseconds, which may or may not be acceptable for your control loop." That gives the firmware team a decision to make rather than a problem to solve from scratch.

I'd also offer to sit with the firmware engineer while they design their filtering, because the boundary between "hardware noise" and "firmware filtering" is exactly where misunderstandings accumulate. A short joint session early is far cheaper than a late-stage argument about whose problem it is.

**Possible follow-ups:**
- What if the firmware team's proposed filtering approach would mask a real signal feature that the hardware team cares about?
- How would you document this kind of hardware-firmware interface so it survives beyond the current team?

## Q4: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This is a common and often under-recognized gap. An engineer who executes well but defers on decisions isn't lacking capability — they're lacking the experience of *owning* a decision and living with its consequences. The mentoring goal is to build that muscle gradually, in a way that doesn't set them up to fail publicly.

I'd start by giving them a decision that is genuinely theirs, with a clear scope and a clear boundary. Something like: "You own the choice of the sensor interface for this subsystem. Here's the constraint set. I want you to make the call, document your reasoning, and bring it to me not for approval but for review." The distinction between approval and review matters — approval keeps them in the deferring posture; review asks them to defend their reasoning.

When they bring the decision, I'd resist the urge to immediately offer my own answer. Instead I'd ask questions that surface whether they've considered the trade-offs: "What did you rule out, and why? What would have to be true for the other option to be better? What's the failure mode if you're wrong?" If they've genuinely thought it through, I'd back their call even if I'd have chosen differently — because the point is to build their judgment, not to have my judgment replicated.

Over time, I'd increase the stakes: first a component choice, then a subsystem architecture, then a cross-team interface. And I'd be explicit with them about what I'm doing and why, so they understand it's a deliberate development path rather than an arbitrary assignment. The most senior person in the room should be the one creating space for others to lead, not the one whose answer always wins.

**Possible follow-ups:**
- What if the engineer makes a decision you believe is wrong, and the cost of being wrong is significant?
- How would you handle it if the rest of the team keeps routing around them to you for decisions, undermining the mentoring?

## Q5: How would you approach leading a technical decision when the team is split between two viable architectures and the disagreement has become personal rather than technical, with each side attributing bad motives to the other?

**Answer:** When a technical disagreement turns personal, the technical content is no longer the bottleneck — the process is. My first move is to name that explicitly and without blame: "We've stopped arguing about the architectures and started arguing about each other. Let's reset." That's not a soft move; it's the only way to get back to a decision.

Then I'd reframe the problem so that the two sides are working on the same question rather than defending positions. The most effective way to do this is to write down the decision criteria together — cost, schedule, risk, manufacturability, regulatory burden, team familiarity — and get explicit agreement on how each criterion should be weighted. Often the disagreement softens once both sides see that they're optimizing for different criteria, not disagreeing about facts.

If the criteria still don't resolve it, the next step is to reduce the argument to something empirical. Can we prototype both? Can we run a bench test that distinguishes them? Can we build a small model that exposes the failure mode each side is worried about? A decision that can be tested is far better than a decision that has to be won by argument. If prototyping isn't feasible, I'd ask each side to write a one-page decision memo — the option, the reasoning, the risks, and what would change their mind. Writing forces clarity and often reveals that one side's case is stronger than it sounded in the room.

If after all that the team is still split, I'd make the call myself, document the rationale, and be clear that the decision is mine to own. What I would not do is let the disagreement drift, because a stalled decision is itself a decision — and usually the worst one.

**Possible follow-ups:**
- How do you make sure the losing side stays engaged after the decision goes against them?
- What would you do if the disagreement resurfaces later, once the chosen architecture starts showing its trade-offs in practice?