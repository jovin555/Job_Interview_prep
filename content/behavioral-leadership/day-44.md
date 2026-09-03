# behavioral-leadership — Day 44

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a battery management system fault or a charging circuit problem, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a structured root-cause investigation rather than a debate between two hypotheses. The first step is containment — ensuring patient safety and preventing further incidents while the investigation proceeds. That might mean issuing a field action, a software workaround, or usage guidance, depending on the risk assessment.

Once containment is in place, I'd assemble a small cross-functional team including hardware, firmware, and quality representatives. Rather than arguing which subsystem is at fault, I'd focus on gathering objective evidence. I'd want to see the actual field returns, not just reports — examining failed units can often narrow the problem significantly. I'd also pull telemetry or logged data if the device captures any, and review the charging and battery management schematics side by side.

A key technique is to design discriminating experiments — tests that would give different results depending on which hypothesis is correct. For example, if the issue is in the charging circuit, you might see abnormal behavior during charging specifically; if it's the battery management system, you might see issues during discharge or at specific state-of-charge levels. I'd also look at the failure distribution: are failures clustered by manufacturing date, firmware version, or usage patterns? That kind of data often points toward one root cause over another.

I'd document everything in a structured format like an 8D report, including the evidence for and against each hypothesis. If the evidence genuinely doesn't discriminate, I'd consider whether both issues could be contributing — sometimes what looks like an either/or is actually a system-level interaction. Only after identifying the actual root cause would I move to corrective action, and I'd verify the fix addresses the root cause rather than just the symptom.

**Possible follow-ups:** How would you decide whether to issue a field action before you've confirmed the root cause? What would you do if the two subsystems are owned by different engineers who each believe the other's design is at fault?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** The core challenge here is shifting from a model where each engineer owns a complete system to one where engineers need to contribute across multiple projects without losing the depth that made them effective. I'd approach this in three phases.

First, I'd assess the current skill distribution honestly. In a single-product environment, engineers often develop deep but narrow expertise — one person might be the "power supply person," another the "sensor person." For a multi-project portfolio, I'd map which skills are transferable and which are product-specific. I'd also look at the actual projects in the portfolio to understand what capabilities they genuinely need, rather than assuming everyone needs to know everything.

Second, I'd design a development plan that balances depth and breadth. Not everyone needs to become a generalist. A better model might be a T-shaped approach — deep in one or two core areas, with enough breadth to contribute effectively across projects. I'd identify natural pairings: for example, someone who deeply understands analog sensing could support multiple projects that all use similar sensor front-ends, even if the rest of the system differs. I'd also create shared resources — design guidelines, reusable circuit blocks, lessons-learned documents — so that knowledge gained on one project benefits others.

Third, I'd think about how to manage the transition itself. Moving from one project to multiple creates scheduling conflicts and context-switching overhead. I'd establish clear priorities and a transparent way to negotiate resource allocation when projects compete for the same engineer. I'd also be realistic about the learning curve — engineers need time to ramp up on new projects, and that time should be planned for rather than treated as a surprise.

The biggest risk is losing the depth that made the team successful in the first place. I'd make sure that as engineers broaden, they don't abandon their core expertise entirely — that depth is often what solves the hardest problems.

**Possible follow-ups:** How would you handle an engineer who resists broadening their skills because they feel their deep specialization is what makes them valuable? How would you measure whether the transition is succeeding?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is a classic system-level trade-off that needs a test strategy designed to address the specific risk, not just a generic test plan. The key concern is that during wake-up, the power supply rails may not have fully settled, reference voltages may still be stabilizing, and the sensor may not yet be producing accurate readings. The firmware team's sleep mode might save power, but if the device reports inaccurate data during the wake-up window, that's a patient-safety issue.

I'd start by defining the problem precisely. What is the maximum acceptable time after wake-up before the sensor readings meet accuracy specifications? What are the settling characteristics of the power supply, the reference, and the sensor itself? I'd want to characterize the hardware behavior empirically — measure the power rail settling time, the reference voltage stabilization, and the sensor output under controlled conditions.

Then I'd design a test matrix that covers the critical scenarios: wake-up from sleep under different battery voltage conditions, repeated wake-sleep cycles to catch thermal or charge effects, and wake-up at different points in the sensor's measurement cycle. I'd also test edge cases like wake-up during a critical measurement or wake-up when the battery is near its low-voltage cutoff.

A key part of the strategy is defining what "stable" means operationally. The firmware needs a clear criterion — for example, a settling time threshold or a signal-quality check — before it can trust the sensor data. I'd work with both teams to define a handshake: the hardware provides a "ready" indication or the firmware waits a specified time before using sensor data. The test strategy would verify that this handshake is reliable across the full operating envelope.

I'd also consider whether the sleep mode needs to be validated under real-world conditions, not just in the lab. Battery impedance changes with temperature and state of charge, and that can affect wake-up behavior. If feasible, I'd include some testing with actual batteries at different temperatures and charge levels.

The outcome should be a test plan that gives both teams confidence — the firmware team gets the battery life improvement, and the hardware team gets evidence that the wake-up transient doesn't compromise measurement accuracy.

**Possible follow-ups:** What would you do if testing revealed that the wake-up settling time is longer than the firmware's sleep interval allows? How would you decide whether the battery life improvement justifies adding complexity to the wake-up sequence?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd approach this as a data-driven architectural decision rather than a popularity contest. Both approaches have legitimate merits, and the right answer depends on the specific requirements of the device — not on which approach is more familiar or comfortable.

First, I'd make sure the review focuses on the actual requirements. What are the real-time constraints? How many independent functions need to run concurrently? What are the safety requirements — does the device need to isolate critical functions from non-critical ones? What are the power, size, and cost constraints? What's the expected service life and how will firmware updates be handled? These requirements should drive the discussion, not personal preference.

For a modular multi-MCU approach, the key advantages are fault isolation, independent development and testing, and potentially easier certification if functions are cleanly separated. The concerns are increased complexity, more inter-processor communication to validate, and more potential points of failure. For a single high-performance processor, the advantages are simpler communication, a single firmware image to manage, and potentially lower cost. The concerns are that a failure in one function could affect others, and the processor might be more complex than any single function needs.

I'd want to see a structured comparison — a trade-off matrix that scores each approach against the actual requirements. If the team is genuinely split, I'd suggest prototyping or simulation to resolve specific uncertainties. For example, if the concern is whether a single processor can handle the real-time load, a proof-of-concept with the actual processing tasks would give better data than debate.

I'd also consider the regulatory implications. In medical devices, the safety architecture matters — how failures are detected and handled, how critical functions are protected. A modular approach might make it easier to show that a failure in a non-critical function doesn't affect a critical one. But it also means more interfaces to validate and document.

The goal is to reach a decision that the whole team can support because it's grounded in evidence and requirements, not because one side won the argument. If we genuinely can't decide, I'd escalate with a clear summary of the trade-offs and a recommendation based on the risk assessment.

**Possible follow-ups:** How would you handle the situation if the architect is strongly attached to their design and sees the review as a personal challenge? What criteria would you use to decide when to escalate the decision rather than resolve it within the team?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** This is fundamentally about psychological safety and the norms of how technical discussions happen. Engineers won't raise early concerns if they fear being dismissed, embarrassed, or punished for being wrong. So the first step is modeling the behavior I want to see — as a leader, I need to explicitly invite challenge to my own decisions and respond to it constructively, even when the concern turns out to be unfounded.

I'd also work on separating the idea from the person. When someone raises a concern, the response should be "let's look at that" rather than "are you questioning my decision?" This means creating a norm where technical decisions are treated as hypotheses to be tested, not positions to be defended. One technique is to explicitly ask during design reviews: "What concerns do you have that you haven't raised yet?" or "If this decision is wrong, what would be the likely failure mode?" That gives people permission to raise half-formed concerns.

For gut feelings specifically, I'd validate that they're worth exploring. A gut feeling is often pattern recognition — the engineer has seen something similar before and their brain is flagging it, even if they can't yet articulate why. The right response is to take the concern seriously and help the engineer investigate it. I'd say something like, "Let's spend 30 minutes understanding what's bothering you about this." Often, that investigation either surfaces a real issue or gives the engineer the language to explain why the concern is unfounded — both are valuable outcomes.

I'd also make sure that raising concerns is visibly rewarded, not just tolerated. When someone raises an early concern that leads to a design change, that should be acknowledged as a positive contribution. When someone raises a concern that turns out to be unfounded, the response should still be appreciative — they did the right thing by speaking up.

Finally, I'd look at the structural factors. If engineers are afraid to raise concerns because of past experiences, changing that takes time and consistency. If the issue is that design reviews are too rushed or too focused on presentation rather than discussion, I'd change the format. The culture will follow the incentives and the modeled behavior.

**Possible follow-ups:** How would you handle a situation where a junior engineer raises a concern that is technically incorrect, and a senior engineer responds dismissively? What would you do if you notice that the same two or three people are always the ones raising concerns, while others stay silent?