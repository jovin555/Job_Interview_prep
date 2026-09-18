# behavioral-leadership — Day 59

## Q1: How would you approach structuring a root-cause investigation when a failure is intermittent and cannot be reproduced on demand, and the team is under pressure to ship a fix quickly?

**Answer:** Intermittent failures are the hardest class of problem because the absence of a reproduction makes it tempting to jump to a plausible-sounding fix and move on. I would resist that and structure the work deliberately.

First, I would treat the investigation as two parallel tracks: containment and root cause. Containment is about limiting exposure — tightening screening, adding a temporary guard in firmware, or restricting the operating envelope — while being explicit that containment is not a fix and must be tracked as temporary. This buys time without pretending the problem is solved.

Second, I would shift the goal from "reproduce the failure" to "increase the probability of observing it." That means instrumenting the system to capture more context when the anomaly occurs: logging timestamps, supply rail behavior, bus traffic, temperature, and firmware state at the moment of failure. If the failure is rare, I would run accelerated or stressed conditions — temperature cycling, voltage margin testing, extended soak runs — to raise the observation rate. The point is to convert a rare event into a measurable one.

Third, I would apply a structured method rather than free-form brainstorming. A fishbone diagram helps organize candidate causes across categories — hardware, firmware, environment, user interaction, manufacturing variation. From there, 5 Whys or fault-tree analysis can drill into the most probable branches. Critically, each hypothesis should generate a testable prediction: if this is the cause, then changing this variable should change the failure rate. That keeps the investigation falsifiable rather than a debate.

Fourth, I would document the reasoning as it happens, not after. For an intermittent issue, the trail of what was ruled out is as valuable as the eventual answer, because it prevents the team from re-litigating the same hypotheses and it supports the eventual corrective action rationale.

Finally, once a root cause is identified, I would verify effectiveness — not just confirm the fix works in the lab, but confirm the failure rate actually drops under the same stressed conditions that exposed it. A fix that "seems to work" because the failure was rare to begin with is not verified.

**Possible follow-ups:**
- How would you decide when to stop investigating and ship a containment fix, versus continuing to chase the root cause?
- If two plausible causes remain after testing, how would you prioritize which to pursue with limited time?

## Q2: How would you approach translating a hardware constraint — such as limited ADC resolution or a noisy analog front end — into terms the firmware team can act on, without either oversimplifying or burying them in detail?

**Answer:** The goal is to give the firmware team a model of the constraint that is accurate enough to design against, without requiring them to become analog engineers.

I would start by characterizing the constraint in the units the firmware team already works in. Instead of saying "the front end has poor noise performance," I would express it as something like: at this sample rate, the effective number of bits is reduced, so the last few counts of the reading are not meaningful and should not be treated as signal. That reframes a hardware property as a firmware design rule.

Second, I would provide a small set of concrete behaviors the firmware should and should not rely on. For example: the sensor reading is stable to within a certain band over a given time window, so filtering should target that band; or the supply rail droops during a particular event, so the firmware should not sample during that window. These are actionable statements, not physics lectures.

Third, I would pair the constraint with the reason it exists, briefly. Firmware engineers make better trade-off decisions when they understand why a limit is there — whether it is a component tolerance, a layout compromise, or a fundamental noise floor. That context also helps them push back intelligently if they think the constraint can be relaxed.

Fourth, I would set up a shared verification method. If the firmware team is going to filter or calibrate around a hardware limitation, both teams should agree on how they will confirm the combined system meets the requirement. That might be a bench test with a known input, or a captured dataset both teams can analyze. Agreeing on the test up front prevents a later dispute about whether the firmware "fixed" a hardware problem or masked it.

Finally, I would keep the communication channel open rather than treating it as a one-time handoff. Hardware and firmware constraints interact, and a short recurring sync — or a shared document that both teams update — catches drift before it becomes a design issue.

**Possible follow-ups:**
- How would you handle it if the firmware team proposes a software workaround that you believe masks a hardware problem rather than solving it?
- What would you put in a written interface document between the two teams to prevent misunderstandings?

## Q3: How would you approach a design review where the presenter is a strong engineer but has a history of becoming defensive when their work is questioned, and you need the review to be genuinely critical to be useful?

**Answer:** The tension here is that a review only has value if it surfaces problems, but a defensive presenter can shut down the very discussion you need. I would address the dynamic before the review, not during it.

First, I would set expectations with the presenter privately, ahead of time. I would frame the review as a shared exercise in finding issues early, when they are cheap to fix, rather than an evaluation of the person. I would also ask them directly what kind of feedback they find most useful and how they prefer it delivered. That conversation does two things: it lowers the sense of threat, and it gives me information about how to run the session.

Second, I would structure the review so that critique is normalized rather than personal. One effective technique is to have the presenter walk through the design's assumptions and open questions explicitly — "here is what I am confident about, here is what I am less sure of." When the presenter names the uncertain areas themselves, questions about those areas feel like collaboration rather than attack. I would also model the behavior by asking questions in a neutral, curious form — "what happens if this input is out of range?" rather than "this is wrong."

Third, I would separate the roles of the review. Someone other than the presenter should be capturing action items, and I would make clear that the output of the review is a list of items to resolve, not a verdict on the design or the designer. This shifts the emotional weight from "am I being judged" to "what do we need to close out."

Fourth, if the presenter does become defensive in the moment, I would not escalate or argue. I would acknowledge the point, note it as something to follow up on, and move on. A review is not the place to win an argument. If a substantive disagreement remains, I would take it offline with the specific people involved and resolve it with data.

Finally, I would follow up after the review to reinforce that the process worked — that issues were found and the design is better for it. Over time, repeated experiences of "critique led to a better outcome, not a punishment" are what change the behavior.

**Possible follow-ups:**
- What would you do if the presenter's defensiveness is affecting the willingness of junior engineers to speak up in reviews?
- How would you handle a review where the presenter is not defensive but simply does not engage with the feedback at all?

## Q4: How would you approach deciding whether a technical disagreement between two senior engineers should be escalated to your manager, versus resolved within the team?

**Answer:** Escalation is a tool, not a failure, but it should be used deliberately. My default is to resolve within the team, and I would escalate when specific conditions are met.

The first question I would ask is whether the disagreement is actually about facts or about values. If it is about facts — which approach has lower noise, which has better thermal margin, which is easier to manufacture — then it can usually be resolved with data. I would push for a small experiment, a calculation, or a review of prior art, and let the result settle it. Escalating a factual question to a manager who has less technical context than the two engineers is usually the wrong move.

If the disagreement is about values or priorities — for example, one engineer prioritizes schedule and the other prioritizes a safety margin — then it may not be resolvable by data alone, because the two people are optimizing for different things. That is a signal that the decision needs a decision-maker with authority over the trade-off, which may be me, or may be my manager.

The second question is whether the disagreement is blocking progress. If the two engineers can proceed on parallel paths — prototyping both options, or deferring the decision while other work continues — then there is no need to escalate yet. Escalation is warranted when the decision is on the critical path and the team cannot move without it.

The third question is whether the disagreement has become personal or is affecting the rest of the team. If the two engineers are still engaging constructively, I would keep it in the team. If it has become a recurring conflict that is draining the team or causing others to take sides, then involving a manager — or a neutral technical authority — can be the right way to break the deadlock and reset the dynamic.

If I do escalate, I would do it in a way that is fair to both engineers: I would present the decision, the options, the trade-offs, and the specific point of disagreement, rather than framing it as one person being right. And I would make clear to both engineers what the escalation is for, so it does not feel like going behind anyone's back.

**Possible follow-ups:**
- How would you handle it if your manager makes a decision you believe is technically wrong?
- What would you document after a disagreement is resolved, so the rationale is not lost?

## Q5: How would you approach building a cross-functional project timeline for a medical device when the hardware, firmware, and regulatory teams each give different estimates and there is no historical data from similar projects?

**Answer:** When there is no historical data, the estimates are essentially educated guesses, and the risk is that the timeline becomes a negotiation about optimism rather than a realistic plan. I would approach it as a structured way to surface and manage uncertainty, not as an attempt to produce a precise date.

First, I would ask each team to break their work into the smallest meaningful units they can, and to give a range rather than a single number — a best case, a likely case, and a worst case. Ranges are more honest than point estimates when there is no data, and they make the uncertainty visible instead of hiding it inside a single number.

Second, I would identify the dependencies between the teams explicitly. In a medical device project, the dependencies are often the real source of schedule risk: firmware cannot be fully verified until hardware is stable, regulatory testing cannot begin until the design is frozen, and so on. Mapping these dependencies shows where a slip in one team's work propagates, which is often more important than the individual estimates.

Third, I would separate the work into what is well understood and what is genuinely unknown. Well-understood work — a routine board bring-up, a standard test protocol — can be estimated with reasonable confidence. Unknown work — a new sensor integration, a first-time regulatory pathway — should be flagged as a risk with a contingency, not given a false precision. I would make the unknowns visible to stakeholders rather than averaging them into the plan.

Fourth, I would build the timeline around milestones and decision points rather than a single end date. Milestones like "design freeze," "verification testing complete," and "regulatory submission ready" give the team and stakeholders checkpoints to reassess. If a milestone slips, the team can replan from there rather than discovering the slip at the end.

Finally, I would communicate the plan as a range with named risks, not as a commitment. Stakeholders can make better decisions — about scope, resourcing, or launch expectations — when they understand which parts of the schedule are solid and which are uncertain. Overpromising on a timeline built from guesses is how projects end up in the post-mortem situation where everyone is looking for someone to blame.

**Possible follow-ups:**
- How would you handle it if leadership pressures you to commit to the optimistic end of the range?
- What would you do if, partway through the project, one team's estimate turns out to be significantly wrong?