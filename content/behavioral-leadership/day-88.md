# behavioral-leadership — Day 88

## Q1: How would you approach a design review where the presenter's package is technically solid but arrives late and is missing the calculations that justify a safety-critical decision, and the meeting is the only slot before a milestone gate?

**Answer:** The first thing I'd do is separate the two problems: the review process failure (late, incomplete package) and the technical decision that still needs a defensible basis. They need different handling, and conflating them usually makes both worse.

On the process side, I'd state the expectation plainly but without turning the meeting into a scolding: a safety-critical calculation that isn't in the package can't be reviewed, because reviewers can't verify reasoning they can't see. That's not a formality — in a regulated context, an undocumented justification is effectively an unjustified decision, and it's exactly the kind of gap an auditor will find later. So the honest position is that the review cannot close the safety-critical item today, regardless of schedule pressure.

On the technical side, I'd salvage what the slot can actually accomplish. I'd ask the presenter to walk through the calculation verbally and on a whiteboard, with the reviewers acting as a check on the method and assumptions even if the written artifact is missing. That gives us a preliminary read — is the approach sound, are the load cases and margins reasonable — while being explicit that a verbal walkthrough is not a substitute for the documented calculation. I'd capture the discussion in the minutes so the reasoning isn't lost, and assign a hard action: the calculation written up and circulated for asynchronous sign-off by a named date, with the milestone gate conditioned on that sign-off rather than on today's meeting.

I'd also want to understand *why* the package was late, because the fix differs. If it's a one-off — someone was pulled onto a field issue — that's a scheduling problem. If it's chronic, it's a process problem: review packages need a submission deadline that's enforced, and the milestone plan needs to account for review lead time rather than treating the review as a zero-duration event at the end. I'd raise that separately from the individual, because blaming the presenter in the room fixes nothing and guarantees the next package is also late and now also defensive.

The key discipline is not letting "the meeting is the only slot" become an argument for approving something unreviewed. A milestone gate that can be passed without its safety-critical justification isn't a gate.

**Possible follow-ups:**
- If the presenter pushes back that the calculation is straightforward and "obvious," how do you respond without being dismissive?
- What would you do if the milestone owner decides to waive the gate and proceed anyway?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent, cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures are where teams most often skip straight to a plausible fix, and where that shortcut is most dangerous — you can't verify effectiveness against a failure you can't reproduce, so "it seems better now" becomes the acceptance criterion. I'd resist that explicitly and structure the work in phases.

First, containment versus correction. Under pressure, the immediate need is often to limit exposure — tighten screening, add a workaround, increase monitoring, restrict the affected configuration — without claiming the root cause is understood. I'd be very clear in communication that containment is not a fix and does not close the investigation. That distinction protects the schedule conversation: you can tell stakeholders "exposure is limited starting now" while being honest that the corrective action is still open.

Second, make the failure observable before trying to explain it. An intermittent failure that can't be reproduced is usually a failure whose triggering conditions aren't instrumented. So the early work is detection: logging, counters, capturing state at the moment of failure, stress conditions that widen the operating envelope (temperature, supply margin, timing corner, load), and running enough cycles that a low-probability event becomes measurable. The goal is to convert "it happened once in the field" into a rate you can compare against after a candidate fix. Without a baseline rate, verification of effectiveness is impossible.

Third, generate hypotheses systematically rather than by whoever speaks loudest. A fishbone across the categories — hardware, firmware, environment, manufacturing variation, use conditions — then rank by which hypotheses are testable with the instrumentation we now have. I'd favor experiments that discriminate between hypotheses over experiments that confirm a favorite one.

Fourth, once a candidate cause is identified, verify by prediction: the fix should make a specific, falsifiable prediction about the failure rate or the triggering condition, and the data should match. If it doesn't, the cause wasn't root.

Throughout, I'd keep a written record — hypotheses, tests, results, ruled-out branches — because intermittent investigations routinely get re-litigated when someone new joins or when the failure recurs months later, and the ruled-out list is often as valuable as the conclusion.

**Possible follow-ups:**
- How do you decide when you've run enough cycles to trust a fix, given you can't prove a negative?
- What do you do if the failure rate is so low that statistically meaningful verification would take months?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The failure mode in both directions is the same: the firmware team ends up making design choices against a mental model of the hardware that doesn't match reality. Oversimplify and they'll assume precision the front end doesn't have; over-detail and they'll tune out and default to whatever the last person told them.

I'd start from what the firmware actually has to decide, and work backward. The useful framing is usually not "the ADC is 12-bit" but "here is the effective resolution and noise floor you'll actually see at the sample rate you're planning, here's how it changes with gain and settling time, and here's the band where the signal of interest lives versus where the noise lives." That's the information that determines filter design, averaging depth, sample timing, and whether a given feature is even achievable.

Concretely, I'd want to hand over three things. First, a short characterization: measured noise versus configuration, not datasheet typicals — real numbers from the actual board, because the layout and reference design dominate the outcome. Second, the constraints stated as budgets: how much settling time a channel switch costs, what sample rate is realistic at the resolution they need, where the analog and digital domains interact (shared reference, ground return paths, switching noise from the digital side coupling back). Third, the failure signatures: what a marginal reading looks like versus a real signal, so they can recognize when they're fighting the hardware rather than the algorithm.

I'd present it as a short written note plus a working session, not a document dump. The written note matters because it becomes the reference when I'm not in the room and when someone new joins; the session matters because it lets them push back with "but I need X" and lets me answer with a concrete alternative or a "that requires a hardware change, here's the cost."

The most important part is making the constraint actionable rather than just true. "The front end is noisy" is not actionable. "At your target rate, expect roughly this much effective noise, so a single-sample threshold will false-trigger; here's the averaging window that gets you under it, and here's the latency that costs you" — that's a constraint the firmware team can design against and can argue with if their requirements demand it.

**Possible follow-ups:**
- How would you handle it if the firmware team's requirement genuinely can't be met within the hardware's limits — who owns that conversation?
- What would you do if the firmware team implements a filter that masks a hardware problem rather than addressing it?

## Q4: How would you approach a mentoring relationship with an engineer who is strong at execution but has never owned a design decision end-to-end, and tends to defer to whoever is most senior in the room?

**Answer:** This pattern usually isn't a confidence problem so much as a practice gap — they've never had to carry a decision from ambiguous requirements through trade-offs to a defended conclusion, so deferring to seniority feels like the safe, correct move. Telling them to "be more confident" doesn't build the missing skill; giving them structured reps does.

I'd start by making the ownership explicit and bounded. Rather than "own this subsystem," which is too vague to practice against, I'd hand them a specific decision with a clear scope: here's the question, here are the constraints, you own the recommendation, and you'll present it and defend it in the design review. Bounded scope matters because it lets them practice the full arc — gather data, weigh trade-offs, commit, defend — without the stakes of an open-ended mandate.

Second, I'd change what happens in the room. If they defer to the most senior person, the fix is partly structural: in reviews, I'd ask for their recommendation first, before the senior voices weigh in, and I'd explicitly protect that ordering. If a senior engineer jumps in early, I'd redirect — "hold that thought, let's hear the recommendation first." That's a small move but it changes the social default, and defaults are most of what drives deferring behavior.

Third, I'd work the reasoning out loud with them before the review, not the answer. The useful coaching is "what would change your mind? what's the strongest argument against your choice? what data would settle it?" — so they arrive with a defended position rather than a hopeful one. Over time they internalize the questions and stop needing me to ask them.

Fourth, I'd let them own a decision that turns out wrong, and treat that as the most valuable rep rather than a failure. How someone handles being wrong in public — revising cleanly, without either collapsing or digging in — is a big part of what "owning a decision" actually means, and it's much easier to learn on a bounded decision with a mentor nearby than on a high-stakes one later.

I'd also watch for the case where the deference is well-founded — sometimes the senior person genuinely does have context the junior lacks, and the right move is to transfer that context rather than push them to override it. The goal is judgment, not contrarianism.

**Possible follow-ups:**
- How would you tell the difference between healthy deference and a confidence gap that needs intervention?
- What would you do if a senior engineer on the team undermines the arrangement by continuing to answer for them?

## Q5: How would you approach leading a technical decision when the team is split between two viable architectures and the disagreement has become personal rather than technical, with each side attributing bad motives to the other?

**Answer:** Once a disagreement turns personal, the technical merits stop being the binding constraint — the first job is to de-escalate the framing, and only then can the technical question be resolved on its merits. Trying to win the technical argument while the room is in blame mode usually hardens both sides.

I'd start by naming the situation honestly but without assigning fault: we have two defensible options, the discussion has stopped being productive, and that's costing us more than either option's downsides. Naming it explicitly and treating it as a shared problem — "we need a decision process, not another debate" — tends to lower the temperature because it stops being about who's right.

Then I'd restructure the decision so it's about criteria rather than positions. Concretely: get both sides to agree, in writing, on what the decision actually has to satisfy — cost, schedule, risk, manufacturability, regulatory burden, maintainability, team familiarity — and how those criteria are weighted. This is the step that most often dissolves the personal framing, because people discover they disagree less about the criteria than about which option they'd already committed to. If they genuinely disagree about weighting, that's a legitimate disagreement to surface and resolve at the right level, not a personality conflict.

Next, convert opinion into evidence where it's cheap to do so. A short prototype, a benchmark, a rough cost model, a review of a similar past design — anything that lets a claim be tested rather than asserted. Data-driven resolution works partly because it's more reliable and partly because it gives both sides a face-saving way to move: "the data settled it" is much easier to accept than "you were wrong."

I'd also separate the people from the positions in a practical way — ask each side to articulate the strongest version of the *other* option, and to state what evidence would change their mind. That does two things: it tests whether the disagreement is real, and it makes the eventual decision easier to accept because each side has already engaged with the alternative.

Finally, whatever is decided, I'd document the decision with its rationale and the alternatives considered — including the losing option's merits. That matters for the audit trail, but it also matters for the team: a documented rationale signals the decision was made on criteria, not on who was more forceful, which is what repairs trust after a personal disagreement.

**Possible follow-ups:**
- What would you do if, after all that, the disagreement is genuinely 50/50 and the team still won't converge?
- How would you handle it if one of the two engineers continues to relitigate the decision after it's made?