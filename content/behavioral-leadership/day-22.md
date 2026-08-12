# behavioral-leadership — Day 22

## Q1: How would you approach managing a situation where two senior engineers on your team have a fundamental disagreement about whether to use a hardware-based watchdog timer or a software watchdog with a separate supervisory IC for a life-support medical device, and the decision is blocking the project timeline?

**Answer:** First, I'd separate the technical debate from the timeline pressure. The worst outcome is making a safety-critical decision based on schedule pressure rather than engineering merit. I'd bring both engineers together and frame the discussion around the specific requirements of the application — what failure modes are credible, what the watchdog actually needs to protect against, and what the system-level safety architecture requires.

I'd ask each engineer to articulate their position in terms of concrete failure scenarios rather than general preferences. For a life-support device, the key questions are: what happens if the main processor hangs, what happens if the watchdog itself fails, and what is the required response time? A hardware watchdog is typically more independent of the processor it's monitoring, but a software watchdog with a supervisory IC can offer more flexibility in detecting subtle firmware faults. The real question is what the system safety case requires.

If the disagreement persists after a structured technical discussion, I'd suggest a small, time-boxed prototyping exercise to test the specific failure scenarios that are in dispute. This converts an abstract argument into data. If that's not feasible within the timeline, I'd escalate to the system safety engineer or technical lead with a clear summary of both positions, the trade-offs, and a recommendation based on the risk assessment. The key is documenting the decision rationale regardless of which approach is chosen, because in a medical device, the reasoning behind a safety-related decision is as important as the decision itself.

**Possible follow-ups:** How would you decide when to escalate versus resolve within the team? What specific failure scenarios would you want to test in the prototyping exercise?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** I'd start by understanding the current skill distribution and the demands of the upcoming projects. The goal isn't to make everyone a generalist overnight — it's to create enough cross-project flexibility while preserving the deep expertise that the team already has. I'd map each engineer's strengths against the technical requirements of the new projects and identify where there are genuine gaps versus where we can cover with collaboration.

The roadmap would have three phases. First, a short-term phase focused on immediate project needs — pairing specialists from different areas on shared problems, creating shared design guidelines that capture institutional knowledge, and establishing cross-project design reviews so that expertise is shared rather than siloed. Second, a medium-term phase focused on deliberate skill development — identifying two or three technical areas where cross-training would have the highest impact, and creating structured opportunities for engineers to work outside their comfort zone with mentorship. Third, a longer-term phase focused on building reusable platforms and design blocks that reduce the need for deep specialization in every project.

The biggest challenge is cultural. Engineers who are used to being the sole expert in a domain may resist sharing or may feel threatened by cross-training. I'd address this by framing the transition as an opportunity to deepen their impact — their expertise becomes more valuable when it's applied across multiple projects rather than confined to one. I'd also be transparent about the fact that multi-project portfolios require some redundancy in skills, not because anyone is replaceable, but because the team needs to be resilient.

**Possible follow-ups:** How would you identify which skills to cross-train first? How would you handle an engineer who resists moving away from their specialization?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is a classic case where both teams are right about different things. The firmware team is right that low-power modes are essential for battery life in a portable device — but the hardware team is right that wake-up transitions are exactly when analog circuits are most vulnerable to noise, settling issues, and reference drift. The test strategy needs to address both concerns without treating them as mutually exclusive.

I'd structure the test strategy around three layers. First, characterization testing at the bench level, where we deliberately exercise the wake-up transition under controlled conditions — varying the sleep duration, the wake-up trigger, the supply voltage, and the temperature — to understand the actual behavior of the analog front end during the transition. This is where we'd measure settling time, reference stability, and any glitches on the sensor output. Second, integration testing at the system level, where we run the full device through realistic use patterns — including the specific sensor measurements that matter clinically — to verify that the sleep mode doesn't degrade measurement accuracy in practice. Third, long-duration testing to catch intermittent issues that only appear over many sleep/wake cycles.

The key is defining what "stable" means before we start testing. The hardware team needs to specify acceptable bounds for settling time, voltage droop, and measurement error during and after wake-up. The firmware team needs to understand those bounds and design the wake-up sequence to respect them — for example, adding a settling delay before taking a measurement, or powering up the analog section before the digital section. The test strategy should verify both that the hardware meets its specifications and that the firmware respects them.

**Possible follow-ups:** How would you handle a situation where the characterization testing reveals that the sleep mode causes unacceptable sensor instability? How would you decide whether to modify the hardware, the firmware, or the sleep mode design itself?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd start by making sure the review focuses on the system requirements rather than personal preferences. Both architectures are viable — the question is which one better meets the specific needs of this device, including safety, reliability, power, cost, and development risk. I'd ask the architect to walk through how the modular design addresses each requirement, and I'd ask the critics to do the same for the single-processor approach.

For a medical device, the key considerations are usually safety isolation, failure containment, and certification complexity. A modular design with multiple microcontrollers can provide better isolation between safety-critical and non-critical functions — if one processor fails, the others continue operating. It can also simplify certification by separating the safety-critical software from the less critical application code. On the other hand, a single high-performance processor can reduce complexity, power consumption, and cost, and it avoids the communication overhead and potential failure modes of an inter-processor bus.

I'd push the discussion toward concrete questions: What are the safety requirements, and does the architecture make them easier or harder to satisfy? What happens when a communication link fails — can the system detect it and respond safely? What is the development team's experience with each approach? What is the certification risk? If the disagreement persists, I'd suggest a structured trade study that scores each architecture against the requirements, with the scoring criteria agreed upon in advance. This doesn't guarantee consensus, but it ensures the decision is based on documented reasoning rather than advocacy.

**Possible follow-ups:** How would you handle a situation where the trade study still doesn't resolve the disagreement? What criteria would you include in the trade study?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** This is fundamentally about psychological safety, and it starts with how leadership responds to concerns when they're raised. If the first time someone raises a gut-feeling concern, they're met with "give me data" or "we already decided this," the culture will shut down quickly. I'd model the behavior I want by taking every concern seriously, even if it's vague, and helping the person articulate what's behind the feeling — often a gut feeling is based on subtle pattern recognition that hasn't been consciously processed yet.

I'd also create structured opportunities for early input. Design reviews shouldn't be the first time people see a decision — I'd encourage engineers to share work-in-progress early, before it's polished, and to invite questions at that stage. I'd explicitly thank people for raising concerns, even when the concern turns out to be unfounded, because the cost of a false alarm is low compared to the cost of a missed issue. I'd also make it clear that raising a concern is not the same as blocking a decision — the concern gets heard and evaluated, but the decision still moves forward unless the concern identifies a real problem.

For the "consensus" problem specifically, I'd work to break the pattern where consensus is treated as a decision that can't be revisited. Consensus should mean "we've considered the options and this is the best one we know of" — not "we've decided and don't want to hear otherwise." I'd encourage engineers to frame concerns as "have we considered X?" rather than "I disagree with the decision," which lowers the perceived stakes. And I'd make sure that when a concern does lead to a change, the person who raised it gets credit — that reinforces the behavior more than any policy statement.

**Possible follow-ups:** How would you handle a situation where an engineer repeatedly raises concerns that turn out to be unfounded, and the team starts to dismiss their input? How would you distinguish between a gut feeling worth investigating and one that's just anxiety about change?