# behavioral-leadership — Day 70

## Q1: How would you approach a design review where the presenter has done solid technical work, but the review package arrives late and is missing key calculations, and the meeting is the only slot before a milestone gate?

**Answer:** The instinct to either cancel the review or wave it through are both wrong — one wastes the only slot, the other defeats the purpose of the gate. The better path is to run the review in a modified form and be explicit about what it can and cannot accomplish.

First, before the meeting, I'd triage the package myself: what's actually missing, and does any of it bear on safety-critical or irreversible decisions? If the missing calculations are on a non-critical subsystem, the review can proceed on the rest and the gap can be closed asynchronously. If they're on something safety-related, the review cannot approve that portion regardless of how good the rest is — and I'd say so up front rather than letting the meeting drift toward a false sense of completion.

In the meeting, I'd restructure the agenda: spend the time on the parts that are reviewable, capture the missing items as explicit action items with owners and dates, and record the review outcome as "conditional" rather than "approved." That distinction matters for traceability — a conditional review with documented open items is defensible; a review that quietly approved an incomplete package is not.

I'd also treat the late package as a process signal, not just a one-off. If it's a pattern, the fix is upstream — a package-readiness checklist with a deadline a few days before the review, so reviewers arrive having actually read the material. A review where nobody has read the package in advance isn't a review; it's a presentation.

The tone matters here too. The presenter did solid work; the problem is packaging and timing, not competence. I'd frame the missing calculations as "we can't responsibly sign off on this section yet" rather than "your work is incomplete," because the goal is to get the calculations done, not to make the engineer defensive about a milestone they're already stressed about.

**Possible follow-ups:**
- How would you decide whether a missing calculation is critical enough to block the milestone versus something that can be closed afterward?
- What would you do if the milestone owner pressures you to mark the review as fully approved to keep the schedule?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures under schedule pressure are where teams most often ship a fix that suppresses the symptom without addressing the cause — and in a medical device context, that's a regulatory and patient-safety problem, not just an engineering one. So the first move is to resist the framing that "quick fix" and "real investigation" are in tension. They're only in tension if you skip containment.

I'd separate the problem into two parallel tracks. The containment track addresses the immediate pressure: can we detect the failure condition, log it, fail safe, or limit exposure while the investigation continues? Containment buys time without pretending the problem is solved. The investigation track proceeds at the pace the evidence requires.

For an intermittent failure, the core challenge is observability. If you can't reproduce it on demand, you have to instrument for it — add logging, capture the state at the moment of failure, widen the conditions under which you're testing (temperature, voltage margins, timing, load). The goal is to convert "intermittent" into "reproducible under condition X." Until you can do that, any fix is a guess.

I'd apply structured methods rather than free-form debugging: a fishbone to enumerate candidate causes across hardware, firmware, environment, and use conditions; then 5 Whys on the most plausible branches; then design experiments that can falsify each hypothesis rather than confirm the favorite one. The discipline is to test the hypothesis you least want to be true, because that's the one most likely to be the actual cause.

Critically, I'd define up front what "verified fix" means — not "the failure stopped appearing in a short test run," but "we understand the mechanism, we can reproduce it, and the fix eliminates it under the reproduction conditions." A fix that makes an intermittent failure disappear without explanation is often just moving the failure somewhere harder to see.

**Possible follow-ups:**
- How would you communicate to leadership that a fix is contained but not yet root-caused, without it sounding like the team is stalling?
- What instrumentation would you add first when you have limited ability to modify the deployed hardware?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode in both directions is real. Oversimplify and the firmware team makes design choices that assume more signal fidelity than exists; over-explain and you lose them in analog detail that doesn't change what they should do. The target is a shared model of the constraint and its consequences, expressed in the firmware team's terms.

I'd start by characterizing the constraint quantitatively, not qualitatively. "The ADC is noisy" is useless. "At the current sampling configuration, the effective noise floor is X LSB, which corresponds to Y units of the measured quantity, and it's dominated by switching noise from the power supply at frequency Z" is actionable. The firmware engineer can then reason about filtering, averaging, sampling rate, and whether the noise is correlated with anything they control.

Then I'd translate it into the decisions the firmware team actually owns: what sample rate is achievable, what filtering is needed to hit the required resolution, whether the noise is white or structured (structured noise needs different handling than random noise), and what the latency cost of averaging is. If averaging 16 samples gets you the resolution you need but adds latency that breaks a control loop, that's a trade-off they need to see, not a number I hand them.

I'd also make the constraint testable. Rather than describing the noise in a document, I'd give them a way to observe it — a test point, a known input, a captured dataset — so they can validate their filtering against reality instead of against my description of it. Shared data beats shared prose.

Finally, I'd keep the interface explicit: what the hardware guarantees, what it doesn't, and what assumptions the firmware is allowed to make. If the firmware assumes the reference voltage is stable and it isn't, that's a system-level bug that neither team owns alone. Writing down the assumptions on both sides is how you catch that before it ships.

**Possible follow-ups:**
- How would you handle it if the firmware team's filtering solution works in the lab but the noise behaves differently in the field?
- Where would you draw the line between a hardware fix (better front end) and a firmware fix (better filtering)?

## Q4: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This is a common and often under-diagnosed situation. The engineer isn't lacking skill — they're lacking the experience of carrying a decision from problem definition through trade-offs to a defended conclusion, and the confidence that comes from having done it. Deferring to the most senior person is a rational strategy when you've never been the one accountable for the outcome.

The mistake would be to simply tell them to "be more decisive." Decisiveness without a decision-making framework just produces confident guesses. What they need is a repeatable way to structure a decision: define the requirements, enumerate the viable options, identify the criteria that matter, weigh the trade-offs, and document the rationale. If they have that scaffold, the decision becomes something they can reason through rather than something they need permission for.

I'd start by giving them ownership of a decision that's real but bounded — something with genuine trade-offs where the cost of a wrong call is recoverable. Then I'd resist the urge to answer when they bring the decision to me. Instead I'd ask the questions that surface their own reasoning: "What are the options? What does each one cost you? Which requirement does each one compromise? What would change your mind?" The goal is to make them the source of the answer, with me as a sounding board rather than an oracle.

I'd also address the room dynamic directly. In design reviews, I'd deliberately route questions to them before the senior person answers, and I'd name the behavior when it happens — not punitively, but as a signal that their judgment is wanted. Over time, the pattern of "wait for the senior person" breaks when they've successfully owned a few decisions and seen that the outcome was fine.

The measure of success isn't that they stop asking for input — good engineers ask for input. It's that they bring a position to the conversation rather than an empty cup.

**Possible follow-ups:**
- How would you handle it if the senior engineer in the room keeps answering for them, undermining the mentoring?
- How would you know when they're ready to own a decision with higher stakes?

## Q5: How would you approach leading a technical decision when the team is split between two viable architectures and the disagreement has become personal rather than technical, with each side attributing bad motives to the other?

**Answer:** Once a technical disagreement turns personal, the technical merits stop being the deciding factor — people are now defending their identity or their judgment, not their architecture. So the first job isn't to pick the better architecture; it's to de-escalate enough that the technical comparison can actually happen.

I'd start by naming the dynamic honestly but without blame. Something like: "We have two viable options and a decision to make. I've noticed the conversation has gotten heated, and I want to make sure we're deciding on evidence rather than on who argued hardest." Naming it explicitly usually lowers the temperature, because most people don't want to be the one who made it personal — they just got there incrementally.

Then I'd reframe the decision around criteria rather than positions. Instead of "which architecture is better," the question becomes "what do we need this system to do, and how does each option perform against those requirements?" I'd get the team to agree on the evaluation criteria first — cost, schedule, risk, manufacturability, regulatory burden, maintainability — before either side argues their case. Agreeing on the scorecard before scoring is how you prevent the criteria from being reverse-engineered to favor a preferred answer.

Where the disagreement is genuinely empirical — and often it is — I'd propose a bounded prototype or analysis to resolve it rather than continuing to argue in the abstract. A small experiment that tests the specific claim each side is making converts opinion into data. This also gives both sides a face-saving path: they're not conceding to each other, they're deferring to evidence.

If the disagreement persists after the criteria are agreed and the evidence is in, that's a signal the decision needs to be made rather than consensus reached. At that point I'd make the call, document the rationale and the dissenting view, and be clear that the decision is made so the team can move forward. A documented decision with a recorded dissent is healthier than an unresolved argument that stalls the project.

**Possible follow-ups:**
- How would you handle it if one of the engineers continues to relitigate the decision after it's been made?
- What would you do if the prototype results are ambiguous and don't clearly favor either architecture?