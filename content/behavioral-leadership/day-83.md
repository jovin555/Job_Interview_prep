# behavioral-leadership — Day 83

## Q1: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** The default should be to resolve it within the team, because escalation that could have been handled locally erodes the team's ownership and signals that technical disagreements are settled by authority rather than evidence. The first step is to diagnose *why* the disagreement persists. Often it isn't a genuine technical impasse at all — the two engineers may be optimizing for different criteria (one for reliability, one for schedule, one for cost) without having made those criteria explicit. Surfacing the actual decision criteria and weighting them against the project's priorities frequently dissolves the conflict, because the disagreement was never about the same question.

If the disagreement is genuinely technical and both positions are defensible, the right move is usually to convert opinion into evidence: define the specific conditions under which each approach wins or fails, and run a bounded experiment, prototype, or analysis to test them. A decision made on data is far easier for the losing side to accept than one made on seniority.

Escalation becomes appropriate when: the decision has cross-project or cross-team consequences beyond the two engineers' scope; it carries regulatory, safety, or cost implications that require a stakeholder with authority to accept the risk; the disagreement has become personal and is blocking progress despite good-faith attempts to resolve it; or the two engineers are at a genuine deadlock where additional data won't resolve it and a decision must be made to keep the project moving. When escalating, I'd frame it not as "these two can't agree" but as a clear decision request: here are the options, here are the trade-offs, here is the recommendation, here is what I need from you. That keeps the escalation productive and preserves the engineers' credibility rather than making it look like a failure to manage.

**Possible follow-ups:**
- How would you handle it if your manager's decision went against the recommendation you and the team had built a case for?
- What would you do if you noticed the same two engineers escalating disagreements repeatedly, suggesting a deeper team dynamic issue?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures are the hardest class of problem because the pressure to ship creates a strong temptation to apply a plausible fix and declare victory without ever confirming the mechanism. That temptation is exactly what produces repeat field failures. The discipline is to resist it and structure the investigation so that even under time pressure, you're building evidence rather than guessing.

The first move is containment, separate from correction: if the failure has field or safety impact, you need a stopgap that limits exposure — a tighter screening test, a firmware guard, a usage restriction — while making clear it is a mitigation, not a root cause. Then the investigation itself. Since you can't reproduce on demand, you shift from "reproduce the failure" to "capture the conditions when it occurs." That means instrumenting aggressively: logging, environmental monitoring, boundary-condition stress, and capturing as much state as possible at the moment of failure. The goal is to convert a rare event into a dataset.

In parallel, you build a structured hypothesis set rather than chasing the first plausible cause. A fishbone or fault-tree approach forces you to enumerate candidate mechanisms across categories — design margin, component variation, timing, thermal, EMI, manufacturing, software state — and then design targeted tests to eliminate or confirm each. The 5 Whys is useful once you have a confirmed mechanism, but premature 5 Whys on an unconfirmed cause just rationalizes a guess. You also want to look for the boundary: does it correlate with temperature, supply voltage, specific units, specific usage sequences, or time-in-service? Correlation with a boundary condition is often the fastest path to mechanism.

Critically, you verify effectiveness before closing. A fix is only validated when you can demonstrate, through accelerated stress, extended soak testing, or field monitoring, that the failure rate has actually dropped — not just that the symptom hasn't reappeared in a short window. And you document the reasoning, including the hypotheses you eliminated and why, because that record is what prevents the same investigation from being repeated later.

**Possible follow-ups:**
- How would you decide when you have enough evidence to ship a fix versus continuing to investigate, given the schedule pressure?
- What would you do if the intermittent failure only appeared in the field and never in any lab or accelerated test you could construct?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode in both directions is real: oversimplify and the firmware team makes assumptions that don't hold; over-detail and they disengage or treat it as the hardware team's problem. The bridge is to express the constraint in terms of *what the firmware can and cannot rely on*, backed by enough characterization that they trust the number.

Concretely, I'd start from the signal chain and quantify the actual limits: effective number of bits after noise, the noise floor in the band of interest, the settling behavior of the analog front end, and how those vary over temperature, supply, and time. Then translate that into firmware-relevant statements: "the usable resolution at the sensor is X LSBs, not the full ADC range"; "the front end needs N milliseconds to settle after a channel switch, so sampling faster than that returns garbage"; "noise is dominated by a periodic component at frequency F, so a simple average won't help but a synchronous filter will." Those are actionable.

I'd also give them the *why* at a level they can reason from, not just a rule to follow. If firmware understands that the noise is dominated by a switching supply at a known frequency, they can make better decisions about filter design and sample timing than if they're just told "use a 16-sample average." Understanding the mechanism lets them adapt when conditions change.

The delivery format matters too. A short written interface spec — signal ranges, noise characteristics, timing requirements, and the assumptions behind them — gives firmware something to design against and to point back to when something behaves unexpectedly. Pair that with a working session where they can ask questions and, ideally, a test fixture or captured data they can use to validate their filtering against real signals rather than idealized ones. The goal is that firmware treats the analog front end as a characterized system with known behavior, not a black box that "sometimes gives weird numbers."

**Possible follow-ups:**
- How would you handle it if the firmware team's proposed filtering approach would actually make the noise problem worse, but they've already built it?
- What would you do if the hardware characterization data you provided turned out to be incomplete once the system was integrated?

## Q4: How would you approach a design review where the presenter is technically strong but consistently becomes defensive when their work is questioned, and the review needs to be genuinely critical to be useful?

**Answer:** The instinct is to soften the review to avoid the reaction, but that defeats the purpose — a review that can't be critical isn't protecting the design or the patient. The better approach is to change the *frame* of the review so that critique is expected and normalized, rather than experienced as personal attack.

First, I'd set expectations before the review, not during it. If the presenter knows in advance that the purpose is to find problems while they're cheap to fix, and that every design in the room will get the same treatment, the critique lands differently. I'd also model the behavior myself: raise issues about my own work openly, and when I question theirs, frame it as "help me understand the reasoning here" rather than "this is wrong." Questions invite explanation; declarations invite defense.

Second, I'd structure the review so critique is systematic rather than ad hoc. Going through a checklist — interfaces, margins, failure modes, testability, regulatory implications — makes the questions feel like part of the process rather than a verdict on the person. It also distributes the scrutiny evenly, so the presenter isn't singled out.

Third, I'd separate the review from the person's identity by focusing on the artifact. "This trace width doesn't meet the derating requirement for this voltage" is about the design; "you didn't derate this properly" is about them. Same information, very different reception.

If defensiveness still shows up, I'd address it privately and directly, but without making it a character judgment. Something like: "I've noticed you get frustrated in reviews, and I want to understand what's driving it — is it the format, the timing, the way feedback is delivered?" Sometimes the defensiveness is a symptom of something fixable: reviews scheduled at bad times, feedback delivered in front of people the presenter wants to impress, or a history of reviews being used punitively. Fixing the underlying condition is more effective than asking someone to "be less defensive."

The long game is building a culture where being questioned is a sign of respect — it means the work is worth engaging with seriously — rather than a sign of doubt.

**Possible follow-ups:**
- What would you do if the defensiveness persisted despite your efforts, and it was starting to suppress honest input from junior engineers in the room?
- How would you handle a situation where the presenter's defensiveness is actually justified because past reviews *have* been used against them?

## Q5: How would you approach leading a post-mortem after a medical device project missed its delivery deadline by several months, when team morale is low and there's a tendency to blame individual contributors rather than systemic issues?

**Answer:** The first priority is to set the ground rules before the post-mortem starts, because once blame takes over, the useful information stops flowing. I'd state explicitly that the purpose is to understand the system that produced the outcome, not to identify who to punish — and that means we look at decisions in context, including decisions that looked reasonable at the time. If people believe the post-mortem is a search for a scapegoat, they'll either defend themselves or go quiet, and either way you lose the data you need.

Then I'd structure the analysis around the timeline and the decision points, not the people. What were the key milestones, what was known at each point, what decisions were made, and what information was available when they were made? This reframes "who screwed up" as "what conditions led to this outcome," which is both more accurate and more actionable. Missed deadlines are almost never caused by one person's failure; they're caused by a combination of optimistic estimates, unresolved technical unknowns, dependencies that weren't visible until late, and pressure to report good news.

I'd specifically look for systemic patterns: Were estimates consistently optimistic? Were risks identified early and then quietly dropped? Was there a point where someone raised a concern that got overridden or ignored? Was the schedule built on assumptions that were never validated? These are the things that, if fixed, prevent the next miss — and they're usually invisible if the conversation stays at the level of individual performance.

I'd also make sure the post-mortem produces concrete, owned actions, not just a document. Each systemic issue should have a specific change attached — a new estimation practice, a risk-review checkpoint, a clearer escalation path — with someone responsible for it. A post-mortem that ends in "we learned a lot" without changing anything is just a ritual.

Finally, morale. Low morale after a miss is real and it affects the next project. Part of the post-mortem's job is to acknowledge the effort that went in, separate the outcome from people's worth, and give the team a sense that the next project will be different because of what they learned. That's not spin — it's the difference between a team that carries the failure forward and one that metabolizes it.

**Possible follow-ups:**
- How would you handle it if the post-mortem surfaced that a specific individual's decision was a major contributor, and the team expects accountability?
- What would you do if leadership above you wanted the post-mortem to focus on individual accountability rather than systemic causes?