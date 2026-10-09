# behavioral-leadership — Day 80

## Q1: How would you approach a design review where the presenter has done solid technical work, but the review package arrives late and is missing key calculations, and the meeting is the only slot before a milestone gate?

**Answer:** The instinct to cancel and reschedule is understandable, but it usually trades a small quality problem for a schedule problem, and the milestone gate doesn't move. A better approach is to run the review in a modified form and be explicit about what it can and cannot accomplish.

First, before the meeting, I'd do a quick triage of the package: what's actually missing, and does any of it touch safety-critical or irreversible decisions? If the missing calculations are on a non-critical path, the review can proceed on the parts that are complete, with the gaps logged as action items. If a missing calculation is load-bearing for a safety or architecture decision, that specific decision gets deferred — not the whole review — and the gate is informed that one item is pending.

In the meeting itself, I'd state the constraint up front: "We have a partial package. Here's what we can meaningfully review today, here's what we're deferring, and here's what we need before the gate." That framing protects the presenter from being ambushed and protects the reviewers from pretending they've reviewed something they haven't. Reviewers should be asked to focus their attention on the sections that are complete rather than skimming everything and giving shallow feedback on all of it.

I'd also separate two kinds of feedback: issues that block the gate, and issues that can be addressed in a follow-up pass. Mixing them causes the review to stall on minor points while the real gaps go unaddressed.

Afterward, the action items need owners and dates, and the deferred items need a specific re-review — not a vague "we'll circle back." The milestone gate owner should get a short written note: what was reviewed, what was deferred, what the risk is. That's more honest than either rubber-stamping a thin package or blowing the gate over a fixable documentation gap.

The root cause of the late package is worth a separate conversation — was it a one-off, or is the review-prep process not giving presenters enough lead time? That's a process question, not a review-meeting question, and conflating them makes the presenter defensive.

**Possible follow-ups:**
- If the missing calculation turns out to be wrong when it arrives, how do you handle the fact that the gate was already passed?
- How would you decide whether to hold the gate versus pass it with a documented open item?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures are the case where the pressure to ship a fix is most dangerous, because the fastest-looking fix is usually a guess that masks the symptom without addressing the cause — and in a medical device that guess can hide a real hazard.

The first move is to resist the framing that "fix" and "investigate" are in tension. They're sequenced: containment first, then investigation, then corrective action. Containment means reducing the exposure — limiting the affected units, adding a temporary guard, tightening a test — while the investigation proceeds. Containment is not a fix and should be labeled as such so nobody mistakes it for closure.

For the investigation itself, the key insight with intermittent failures is that you can't reproduce on demand, so you have to instrument for capture. That means: increase logging and telemetry around the suspect subsystem, widen the conditions under which data is recorded, and set up triggers so that when the failure does occur, you get a snapshot instead of a report that says "it happened again." Without that, every occurrence is wasted.

In parallel, I'd build a structured hypothesis set — fishbone or 5-whys on the failure mode — and rank hypotheses by how well they explain the observed pattern: does it correlate with temperature, with a particular firmware state, with a specific unit, with time since power-on? Even a handful of occurrences can discriminate between hypotheses if you're capturing the right variables.

I'd also be explicit with the team and with stakeholders that "cannot reproduce" is a data problem, not a dead end, and that the honest schedule estimate includes time to capture occurrences. Overpromising a fix date on an intermittent failure is how teams end up shipping a change that doesn't hold.

Verification of effectiveness matters more here than anywhere: after a fix, you need a defined observation window and a way to confirm the failure rate actually dropped, not just that it hasn't been seen in a week.

**Possible follow-ups:**
- How do you decide when you've captured enough occurrences to be confident in a root cause?
- What do you tell a stakeholder who wants a fix date before the investigation has a root cause?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode on both sides is real: oversimplify and the firmware team makes design choices that assume more signal fidelity than exists; over-detail and they disengage and treat the hardware as a black box.

I'd start from what the firmware team actually needs to decide. They don't need the full noise analysis; they need to know the effective resolution and noise floor at the point where their algorithm consumes the signal, and how those behave across the operating envelope — temperature, supply variation, sample rate. So the translation is: "Here is the usable signal-to-noise at the ADC input, here is how it degrades at the extremes, and here is what that means for your filtering and threshold choices."

Concretely, that means giving them a small number of actionable numbers rather than a plot dump: effective number of bits at the relevant sample rate, the noise bandwidth, and any known periodic interference (switching supply harmonics, for example) they should expect to see and might filter. If there's a dominant noise source, name it, because it changes the right mitigation — a firmware averaging filter helps with white noise but does nothing for a coherent interferer.

I'd also flag the constraints that are non-negotiable versus the ones that are tradeable. If the analog front end can be improved with a layout or component change, say so and say what it would cost. If it can't, say that too, so the firmware team knows the limit is real and not a preference.

The best version of this is a short joint session where the hardware and firmware engineers look at the same data together, so questions get answered in the moment rather than over a document. A one-page interface spec — signal range, noise, sample rate, timing — that both sides agree to is worth more than a long report nobody reads.

**Possible follow-ups:**
- How would you handle it if the firmware team's proposed filtering approach would introduce latency that's unacceptable for the application?
- What would you put in a written interface spec between the analog front end and the firmware, and who owns it?

## Q4: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This is a common and often under-diagnosed pattern. The engineer isn't lacking skill — they're lacking the experience of carrying a decision through the consequences, and they've learned that deferring is safe. The mentoring goal is to build the muscle for ownership without setting them up to fail publicly.

I'd start by giving them a decision that's genuinely theirs, with a clear boundary: a subsystem or a component choice where the scope is small enough that a wrong call is recoverable, but real enough that it matters. The key is to make the ownership explicit — "this is your call, I'll review it, but you're deciding" — because otherwise the default deference kicks back in.

In the review, I'd resist the urge to give the answer. Instead I'd ask the questions a good reviewer would ask: what alternatives did you consider, why did you reject them, what would change your mind, what's the failure mode if you're wrong? That forces the reasoning to be theirs. If they say "I wasn't sure so I went with what the senior engineer suggested," that's the moment to redirect: "What did you think was right, and why?"

I'd also normalize the discomfort of deciding under uncertainty. A lot of deference comes from the belief that senior people have certainty that the junior person lacks — which isn't true. Making my own reasoning visible, including the parts I'm unsure about, models that decisions are made on the best available evidence, not on perfect knowledge.

Over time, I'd widen the scope and reduce the review intensity, and I'd make sure their decisions get visible credit — in design reviews, in the record — so ownership is reinforced rather than quietly absorbed by whoever is senior in the room.

**Possible follow-ups:**
- How would you handle it if the engineer makes a decision you disagree with, but it's within the scope you gave them?
- How do you tell the difference between healthy deference to experience and a confidence problem that needs a different intervention?

## Q5: How would you approach leading a technical decision when the team is split between two viable architectures and the disagreement has become personal rather than technical, with each side attributing bad motives to the other?

**Answer:** Once a technical disagreement turns personal, the technical merits stop being the deciding factor — people defend positions because backing down feels like losing, not because the position is right. So the first job is to de-escalate the framing before trying to resolve the substance.

I'd start by naming the pattern without assigning blame: "We've been going back and forth on this for a while, and I think we've stopped arguing about the architecture and started arguing about who's right. Let's reset." That's usually enough to get people to step back, because most engineers don't actually want the conflict — they've just gotten pulled into it.

Then I'd reframe the decision around criteria rather than positions. Instead of "which architecture is better," the question becomes "what does this application actually require, and which option meets those requirements with acceptable risk?" That moves the discussion from advocacy to evaluation. I'd get the team to agree on the criteria first — cost, schedule, reliability, regulatory burden, manufacturability, team familiarity — before scoring either option, because agreeing on criteria is much easier than agreeing on a conclusion.

Where the disagreement is genuinely about facts rather than values, a prototype or a focused test can settle it. A small experiment that answers the specific question — does this approach meet the timing budget, does this one hold up under the noise conditions — is worth more than another meeting. Where the disagreement is about values or risk tolerance, that's a decision that belongs to a defined owner, and I'd make that explicit rather than letting it drag.

Throughout, I'd keep the decision and its rationale documented, including the dissenting view. Recording why the losing option was rejected — and what would change the decision — protects the team from relitigating it later and gives the minority position a fair hearing.

If the personal dimension persists after the technical question is settled, that's a separate conversation with the individuals involved, not something to solve in the architecture meeting.

**Possible follow-ups:**
- What would you do if the two engineers continue to undermine the decision after it's made?
- How do you decide when a disagreement has crossed from technical to personal, and what signals tell you it's time to intervene directly?
