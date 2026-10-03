# behavioral-leadership — Day 74

## Q1: How would you approach leading a design review where the presenter is technically strong but the review package arrives late and is missing key calculations, and the meeting is the only slot before a milestone gate?

**Answer:** The instinct is to either cancel the review or push through it as a formality, and both are wrong. Cancelling burns the only slot before the gate; pushing through without the calculations means the review can't actually evaluate the safety-critical portions, so any "approval" is meaningless and creates a false record.

I'd start by separating the review into two parts. The first part — architecture, interfaces, requirements coverage, risk-relevant decisions — can often be reviewed from what *is* present, because those are reasoning questions rather than arithmetic questions. I'd run that portion properly and capture real findings. The second part — anything that depends on the missing calculations, like thermal margins, trace current capacity, derating, or timing budgets — I would explicitly mark as *not reviewed*, with a named owner and a date for a follow-up session. That keeps the milestone gate honest: the gate passes on the things that were genuinely reviewed, and the unreviewed items are tracked as open actions rather than silently absorbed.

I'd also address the root cause separately from the meeting. A late, incomplete package is usually a process problem, not a character flaw — the presenter may not have a template, may not know what "review-ready" means, or may have been given the deadline too late. So after the review I'd work with them on a standard package checklist and a submission deadline that sits a few days ahead of the review, so there's time to fix gaps before the room is full.

The key principle: never let a review produce an approval it didn't earn. It's better to have a review with clearly scoped gaps than a review that looks complete and isn't.

**Possible follow-ups:**
- If the milestone gate owner insists the review must be marked "complete" to keep the schedule, how would you handle that pressure?
- How would you decide which missing items are serious enough to block the gate versus which can be tracked as open actions?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures are where teams most often ship a fix that makes the symptom disappear without addressing the cause — and in a medical device that's a serious risk, because the failure mode may still be present and just harder to trigger.

My first move is containment, clearly separated from correction. Containment is whatever protects the user or the field right now — a tighter screening test, a firmware guard, a usage restriction — and it's explicitly labelled as temporary. The pressure to "ship a fix quickly" is usually pressure for containment, and naming it that way lets the team move fast without pretending the investigation is over.

For the investigation itself, when you can't reproduce on demand, you stop trying to reproduce the exact failure and start trying to reproduce the *conditions*. That means instrumenting the system to capture data continuously — logging supply rails, timing margins, temperature, bus traffic, sensor readings — so that when the failure does occur, you have a snapshot of the state around it rather than a report that says "it happened again." I'd also look hard at the boundary conditions: what's different about the units or environments where it fails? Is it a specific batch, a specific temperature range, a specific sequence of user actions, a specific power-up state? Intermittent failures usually live at a margin — a timing margin, a noise margin, a thermal margin — and the job is to find which margin is being exceeded and under what conditions.

I'd use a structured method — 8D or fishbone — not as paperwork but because it forces the team to enumerate candidate causes across hardware, firmware, environment, and use, and then design a test that discriminates between them. And critically, I'd define up front what evidence would confirm each hypothesis, so the investigation doesn't drift into whoever argues loudest.

Finally, verification of effectiveness: after a candidate fix, the question isn't "did the symptom stop?" but "did we demonstrate the mechanism is gone?" If you can't show the mechanism, you can't claim the fix.

**Possible follow-ups:**
- How would you decide when you've gathered enough evidence to conclude a root cause, versus continuing to investigate?
- If the failure rate is very low, how would you design a verification that gives you confidence the fix worked?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode here is a hardware engineer handing firmware a number with no context ("the ADC is 12-bit, deal with it") or a full analog analysis the firmware team can't use. Neither helps them make a decision.

What the firmware team actually needs is the *budget*: how much of the total error or noise is attributable to the analog front end, how much is available to them, and what the constraint means for the algorithms they're considering. So instead of "the ADC is 12-bit," I'd frame it as: "the analog front end contributes roughly this much noise and this much quantization error at the sample rate you'll use; that leaves you this much headroom for filtering and averaging before you eat into the measurement accuracy the requirement demands." That's a number they can design against.

I'd also give them the *shape* of the problem, not just the magnitude. Is the noise white and therefore reducible by averaging? Is it correlated with a switching supply and therefore better handled by synchronizing sampling away from the switching edge? Is it low-frequency drift that averaging won't help? Those distinctions change the firmware strategy completely, and they're hardware facts the firmware team can't easily discover on their own.

Where it genuinely matters, I'd sit with the firmware engineer and look at the data together — a scope capture or a logged sample stream — rather than describing it in a document. Shared data resolves more misunderstandings than shared prose.

And I'd be honest about what's still uncertain. If the analog front end's behaviour at temperature isn't fully characterized, I'd say so, and propose that we characterize it together rather than letting firmware assume a margin that isn't there.

**Possible follow-ups:**
- How would you handle it if the firmware team proposes a filtering approach that would mask a real hardware problem rather than solve it?
- How would you decide how much of the error budget to allocate to hardware versus firmware when both teams could reduce it?

## Q4: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This is usually not a confidence problem — it's a *practice* problem. The engineer has never had to carry a decision from problem statement through trade-off analysis to a defended conclusion, so deferring to seniority is a rational strategy in the absence of that experience. The fix is to give them the experience in a controlled way, not to tell them to be more assertive.

I'd start by handing them a decision that's genuinely theirs to make, with a real but bounded scope — something where the consequences of a wrong choice are recoverable. The critical part is the framing: I'd ask them to come back not with a recommendation, but with the *options and the criteria*. What are the candidate approaches? What are the trade-offs? What would have to be true for each to be the right choice? That forces the reasoning to happen before the room can influence it.

Then, in the review itself, I'd deliberately hold back my own opinion until they've presented theirs. If I speak first, the exercise collapses — they'll just agree with me. I'd ask questions rather than give answers: "What happens if that assumption is wrong?" "How would you test that?" "What would change your mind?" And when they land on a defensible position, I'd say so explicitly, so they get the signal that their reasoning held up on its own merits.

Over time I'd increase the stakes and the ambiguity — decisions with less complete information, decisions that affect other teams — and gradually step further out of the room. The goal is that they stop asking "what do you think?" and start asking "here's what I think, does this hold up?"

I'd also be careful not to confuse deference with a lack of judgement. Some engineers defer because they've learned that disagreeing with a senior person has a cost. If that's the case, the mentoring has to include making it visibly safe to disagree — which is a culture issue, not just a coaching one.

**Possible follow-ups:**
- How would you handle it if the engineer makes a decision you believe is wrong, but it's within the scope you gave them?
- How would you tell the difference between genuine deference and a lack of technical confidence, and would your approach change?

## Q5: How would you approach leading a technical decision when the team is split between two viable architectures and the disagreement has become personal rather than technical, with each side attributing bad motives to the other?

**Answer:** Once a disagreement turns personal, the technical merits stop being the deciding factor — people are now defending their standing, not their position. So the first job is to change the *shape* of the conversation, not to adjudicate the technical question.

I'd start by separating the two things that have gotten tangled: the decision criteria and the decision itself. I'd ask both sides to write down, independently, what the architecture needs to achieve — the requirements, the constraints, the things that would make an option unacceptable. Very often the two lists overlap far more than either side expects, and the disagreement shrinks to a much smaller set of genuine differences. That reframing is usually enough to take the heat out of it, because both sides can see they agree on most of the problem.

For the remaining genuine differences, I'd try to convert opinion into evidence. If the dispute is about which option is more reliable, or simpler to bring up, or easier to test, then there's usually a way to prototype or benchmark the specific point of contention rather than argue it abstractly. A small, time-boxed experiment that both sides agree to accept the result of is worth more than any amount of debate. And I'd get agreement on the decision criteria *before* seeing the results, so nobody can move the goalposts afterwards.

If the disagreement still can't be resolved on evidence — because it's genuinely a judgement call about risk or priorities — then it's my decision to make, and I'd make it explicitly, document the rationale, and be clear that the decision is mine to own. What I wouldn't do is let it drift, or split the difference in a way that produces a worse architecture than either option.

Throughout, I'd keep the focus on the problem rather than the people. If someone is attributing bad motives, that's a signal they feel their position isn't being heard on its merits, so making sure both sides are genuinely heard — and seen to be heard — is part of the technical work, not a soft add-on.

**Possible follow-ups:**
- What would you do if, after the decision is made, one side continues to undermine it in side conversations?
- How would you handle it if the disagreement is really about which team owns the risk, rather than about the architecture itself?