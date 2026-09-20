# behavioral-leadership — Day 61

## Q1: How would you approach a design review where the presenter is a strong engineer but has a history of becoming defensive when their work is questioned, and you need the review to be genuinely critical to be useful?
**Answer:** The goal is to separate the person from the artifact, and to make critique the expected output of the meeting rather than a judgment of the author. I would set the frame at the start: state explicitly that the purpose of the review is to find problems now, while they are cheap to fix, and that a review where nothing is challenged is a failed review. I would also model the behavior by inviting the presenter to walk through the areas they are least confident about first — this gives them control over the agenda and often surfaces the weak points themselves, which is far less threatening than having someone else find them.

Structurally, I would steer comments toward the design and away from the designer: "this trace routing creates a return-path discontinuity" rather than "you routed this badly." I would ask questions rather than issue verdicts where possible — "what was the reasoning behind this decoupling placement?" — because it either reveals a rationale the reviewer missed or lets the presenter reach the concern on their own. I would also make sure the review package is circulated in advance so the discussion is about substance, not about being ambushed live.

If defensiveness still surfaces, I would not escalate in the room. I would park the contentious item, note it as an action to resolve offline with data, and keep the rest of the review moving. Afterwards, a private conversation about how the review went — framed around the value of early challenge to the project, not around their behavior — is usually more effective than a public correction. Over time, the pattern I want to build is that being questioned is normal and low-stakes, and that the strongest engineers are the ones who invite it.

**Possible follow-ups:**
- How would you handle it if the defensiveness persists across multiple reviews despite your private feedback?
- What would you do if other reviewers start self-censoring because they don't want to trigger the reaction?

## Q2: How would you approach structuring a root-cause investigation when a failure is intermittent and cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?
**Answer:** Intermittent failures are the case where the pressure to ship a fix is most dangerous, because the temptation is to grab the first plausible cause and declare victory. I would resist that by separating containment from corrective action explicitly. Containment — a workaround, a guard band, a tighter screening test — can go out quickly to protect users or the line, but it must be labeled as containment and not mistaken for a root cause. The investigation continues in parallel.

For the investigation itself, the first move is to maximize observability rather than guess. If the failure can't be reproduced on demand, I want to instrument the system so that when it does occur, I capture the state: logging around the suspect subsystem, triggering on anomalous conditions, capturing supply rails, bus traffic, or timing at the moment of failure. I would also gather the population of occurrences — how many units, what conditions, what common factors — because patterns in the field data often narrow the search space faster than bench work.

I would use a structured method like 8D or a fishbone to force breadth before depth: list candidate causes across hardware, firmware, environment, and use conditions, then design a discriminating test for each rather than testing them one at a time by intuition. Where a hypothesis can be confirmed or eliminated cheaply, do that first. I would document each hypothesis and its result, because with intermittent issues the same dead ends get re-explored if the reasoning isn't written down. Only when a cause is confirmed by evidence — ideally by reproducing the failure on demand after the fix — would I call it closed, and I would verify effectiveness by monitoring after the fix ships.

**Possible follow-ups:**
- How would you decide when containment is good enough to ship while the root cause is still unknown?
- What would you do if the field data points to two equally plausible causes and you can only pursue one at a time?

## Q3: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?
**Answer:** The firmware team doesn't need the analog theory; they need to know what the constraint means for what they can and cannot do in software. So I would translate the constraint into a small number of actionable statements with numbers attached. For example: "the effective resolution at the sensor is X bits after noise, so a single sample is not trustworthy to better than Y; you need to average N samples to get a stable reading, and that averaging costs you Z milliseconds of latency." That gives them a budget they can design against instead of a vague warning.

I would pair that with the boundary conditions that matter to them: where the noise comes from (switching supplies, digital return currents, the sensor's own behavior), whether it is correlated with anything they control (PWM activity, communication bursts), and what happens at the extremes — saturation, clipping, or a rail that drifts with temperature. If there is a known failure mode, like the front end going non-linear near full scale, I would state it plainly so they can guard against it in code rather than discovering it in the field.

The key is to give them the "so what" first and the supporting detail second, so they can act immediately and dig deeper only if they need to. I would also offer to sit with them while they design the acquisition and filtering, because the interface between the analog front end and the sampling strategy is exactly where misunderstandings between the two disciplines cause problems. A short shared document — constraint, implication, recommended action — tends to prevent the same question from being re-litigated later.

**Possible follow-ups:**
- How would you handle it if the firmware team proposes a filtering approach that you believe will not actually solve the noise problem?
- How would you decide how much of the analog detail to include versus leaving out to keep the message clear?

## Q4: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?
**Answer:** My default is to resolve it within the team, because escalation that could have been avoided erodes the team's ownership and trains people to route around each other. But "resolve within the team" doesn't mean forcing a consensus — it means running a process that produces a decision the team can live with. The first step is to make sure the disagreement is actually about the same thing: often two senior engineers are arguing past each other because they're optimizing for different criteria (cost, schedule, reliability, manufacturability) without saying so. Naming the criteria explicitly frequently collapses the disagreement into a straightforward trade-off.

From there, I would push toward evidence. If the dispute is empirical — will this approach meet the timing budget, will this grounding scheme actually reduce noise — the answer is a test or a prototype, not a debate. A small experiment that both engineers trust is worth more than any amount of argument. If the dispute is genuinely a judgment call with no decisive data, then it becomes a decision to be made and documented with rationale, and I would make it (or designate who makes it) rather than letting it drift.

I would escalate when the decision exceeds my authority or the team's — for example, when it has cross-project or budget implications, when it touches a regulatory or safety position that needs a formal owner, or when the two engineers have reached an impasse that is blocking progress and no amount of evidence will settle it. Even then, I would escalate with a clear framing: here is the decision, here are the options, here is the trade-off, here is what I recommend — not "these two can't agree, please decide." Escalation should hand the manager a decision to ratify, not a problem to solve from scratch.

**Possible follow-ups:**
- How would you handle it if the two engineers keep re-opening a decision that was already made and documented?
- What would you do if your manager's decision goes against your own technical recommendation?

## Q5: How would you approach building a cross-functional project timeline for a medical device when the hardware, firmware, and regulatory teams each give different estimates and there's no historical data from similar projects?
**Answer:** With no historical data, the estimates are really guesses, and the danger is treating them as if they were reliable. I would start by decomposing each team's work into tasks small enough that the unknowns become visible, and then explicitly separating the parts that are well understood from the parts that are genuinely uncertain. The well-understood parts can be estimated with reasonable confidence; the uncertain parts should be flagged as such rather than averaged into a single number that hides the risk.

The dependencies are where cross-functional timelines usually break, so I would map them explicitly: what does firmware need from hardware before it can start, what does regulatory need from both before it can test, and which of those handoffs are hard gates versus things that can overlap. Medical device development has real serialization — you can't run compliance testing on a design that's still changing — and making those gates visible early prevents the schedule from being built on impossible parallelism.

For the uncertainty itself, I would use ranges rather than point estimates and communicate them as ranges: "hardware bring-up is three to five weeks, and the risk is in the sensor interface." I would identify the few unknowns that most affect the critical path and propose early de-risking work — a prototype, a bench test, a preliminary regulatory consultation — so that the estimate improves as the project proceeds rather than staying a guess. And I would build in explicit checkpoints where the estimates get revisited against what's actually been learned, because a timeline that's set once and never updated is worse than no timeline at all. Throughout, I would communicate the schedule as a set of assumptions and risks, not a promise, so that when something slips it's a known risk materializing rather than a surprise.

**Possible follow-ups:**
- How would you handle it if one team consistently underestimates and their slippage keeps pushing the critical path?
- How would you present a range-based timeline to a stakeholder who wants a single committed date?
