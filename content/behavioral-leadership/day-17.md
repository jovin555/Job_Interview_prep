# behavioral-leadership — Day 17

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor calibration drift or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a data-collection problem rather than a debate between hypotheses. The first step is to establish a clear timeline of when the issue was first reported, under what conditions, and whether there's any pattern in the affected units — serial number ranges, manufacturing dates, firmware versions, or environmental conditions at time of use. This helps narrow the search space before any deep technical work begins.

Next, I'd want to isolate the variables. If the device logs raw sensor data or intermediate values, that's the most valuable evidence — it lets us determine whether the raw readings were already out of range before any filtering occurred, or whether the raw data looked correct and the error was introduced downstream. If such logs don't exist, I'd look at whether we can reproduce the issue in a controlled lab setting using the same sensor batch and firmware version.

I'd also consider the physics of the failure. Sensor drift typically manifests gradually, correlates with age or environmental exposure, and often affects all channels using the same sensor type. A firmware filtering error tends to appear suddenly — perhaps after a specific software update — and may affect only certain operating modes or input ranges. These distinguishing characteristics can be tested directly.

The key is to avoid committing to one hypothesis too early. I'd structure the investigation so that both teams — hardware and firmware — contribute evidence independently, then compare findings against the distinguishing criteria. If the evidence genuinely points in both directions, I'd design a targeted experiment that forces a discriminating outcome, such as bypassing the filter in a test unit or swapping in a known-good sensor.

**Possible follow-ups:** How would you handle it if the evidence is genuinely ambiguous even after targeted testing? What if the investigation is time-critical because the device is in active clinical use?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** The core challenge here is shifting from a "one team, one product" mindset to a model where engineers need to contribute across multiple projects without losing the deep expertise that made the original product successful. I'd approach this in three phases.

First, I'd assess the current skill matrix honestly. What are the genuine overlaps between projects? For example, if all three projects use similar sensor interfaces, power management architectures, or communication protocols, those are natural areas for cross-project sharing. I'd map each engineer's strengths against the portfolio's needs and identify where the gaps are — not just in technical skills, but in context — because a great analog designer who only knows one product's requirements will struggle when asked to work on a different sensor suite without support.

Second, I'd introduce a structured knowledge-sharing mechanism. This could be a shared design library of validated circuit blocks, interface standards, or lessons-learned documents from each project. The goal is to make expertise portable — so that an engineer moving from Project X to Project Y doesn't have to reinvent the wheel or rely on tribal knowledge. I'd also pair engineers across projects for specific tasks, so they gain exposure without being thrown in cold.

Third, I'd think carefully about how to preserve deep specialization where it matters. Not everything should be cross-trained. Some areas — like radiation-hardened design or specific regulatory expertise — are rare and valuable, and forcing those engineers to spread too thin would be a mistake. The roadmap should identify which skills are truly portable and which need to remain concentrated, then design the project assignments accordingly.

Finally, I'd communicate the transition clearly: what changes, what doesn't, and why the team structure is evolving. Engineers often resist this kind of change because they fear losing mastery or being spread too thin. Acknowledging that concern directly and showing how the new structure actually protects deep expertise while adding flexibility is essential.

**Possible follow-ups:** How would you handle an engineer who is the sole expert on a critical subsystem and resists any attempt to cross-train others? How would you measure whether the transition is succeeding?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is a classic tension between power optimization and analog performance, and the right approach is to design a test strategy that directly characterizes the risk rather than arguing about it theoretically. I'd start by defining what "sensor stability during wake-up" actually means in measurable terms — settling time, voltage ripple on the analog supply, reference voltage drift, or ADC reading variance — and establish pass/fail criteria based on the device's accuracy requirements.

The test strategy would have three layers. First, bench-level characterization: using a controlled setup, I'd cycle the device through the proposed sleep and wake-up sequence thousands of times while monitoring the analog front-end with a high-bandwidth oscilloscope and logging ADC readings. This would reveal whether there's a consistent transient on wake-up, how long it lasts, and whether it affects measurement accuracy. I'd also test across temperature extremes and battery voltage levels, since both affect analog behavior and wake-up transients.

Second, I'd design a comparative test: run the same measurement sequence with the sleep mode enabled versus disabled, and compare accuracy statistics. This directly answers the question "does the sleep mode actually degrade performance in a way that matters?" rather than relying on theoretical concerns.

Third, I'd consider the system-level implications. Even if the analog front-end settles correctly, the firmware needs to know when it's safe to take a measurement. The test strategy should include a handshake mechanism — perhaps a hardware signal or a fixed settling delay — that ensures measurements are only taken after the analog chain is stable. This turns the hardware concern into a firmware requirement that can be verified.

The key principle is to make the risk measurable and then test against defined criteria, rather than letting the two teams argue about whether the risk is real. If the testing shows the sleep mode causes unacceptable transients, the design needs to change — either by adding a settling delay, improving the power supply decoupling, or adjusting the wake-up sequence.

**Possible follow-ups:** What if the bench testing shows marginal results that pass the criteria but leave little margin? How would you decide whether to accept the risk or require a design change?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd start by reframing the discussion around the actual requirements rather than the architectural preference. The question isn't "which architecture is better in general" but "which architecture better satisfies this device's specific constraints — safety, reliability, power, cost, development timeline, and regulatory complexity." I'd ask the team to list the key requirements and then evaluate both options against them systematically.

For a medical device, the critical questions are: What happens if one processor fails? Can the system detect the failure and respond safely? Does the modular architecture provide genuine fault isolation, or does it just add complexity without real safety benefit? Conversely, does a single processor create a single point of failure that's harder to mitigate? These are the kinds of questions that should drive the decision, not intuition about which approach "feels" more reliable.

I'd also push for data where possible. If the team has experience with both architectures — even from non-medical projects — that experience is relevant. Are there known failure modes with multi-processor communication that need to be addressed? What's the actual track record of CAN-FD in similar applications? If the concern is about communication reliability, that's a legitimate technical issue that can be analyzed — bus loading, error handling, message timeouts, and fail-safe behavior.

The decision also has practical dimensions. A modular architecture might allow parallel development, which could shorten the timeline. But it also means more firmware to write, more integration testing, and more documentation for regulatory submission. A single processor might be simpler to qualify but could create a bottleneck in development. These trade-offs need to be explicit.

I'd structure the review so that both sides present their case with evidence, then I'd facilitate a decision based on the requirements matrix. If the team remains split, I'd consider a prototyping exercise — even a partial one — to test the riskiest assumptions. The goal is to reach a decision that the whole team can support because it's grounded in requirements and evidence, not because one side won the argument.

**Possible follow-ups:** How would you handle it if the architect is the most senior person on the team and has strong ownership of the proposal? What if the decision needs to be made quickly because the project is already behind schedule?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** The foundation of this culture is psychological safety — engineers need to know that raising a concern will be met with curiosity, not defensiveness or dismissal. But that alone isn't enough; I'd also need to give them a structured way to express concerns that don't yet have a fully formed technical basis.

I'd start by modeling the behavior myself. When I have a concern that's not fully articulated, I'd voice it openly and explain that I'm flagging it for investigation rather than asserting it as fact. This signals that it's acceptable to raise half-formed concerns and that the team's job is to help develop them into either a real issue or a resolved question.

I'd also introduce a lightweight mechanism for capturing concerns — perhaps a "technical concerns log" that's reviewed regularly. The key is that concerns are tracked and addressed, not just discussed and forgotten. When someone raises a concern, the team should respond with "let's investigate that" rather than "let's discuss it now and move on." This gives the concern a life beyond the meeting.

For the "gut feeling" case specifically, I'd encourage engineers to articulate what's driving the feeling — is it a pattern they've seen before? A similarity to a past failure? A discomfort with the complexity? These clues often point to a real issue that can be investigated. I'd also make it clear that a concern doesn't need to be fully formed to be valid; it needs to be taken seriously and either validated or resolved through investigation.

Finally, I'd address the power dynamics directly. If a senior person makes a decision, I'd explicitly invite challenge: "This is my current thinking, but I want to hear where you think it might be wrong." And when someone does raise a concern that turns out to be valid, I'd make sure they get credit for it — publicly. That reinforces the behavior more than any policy statement.

**Possible follow-ups:** How would you handle a situation where an engineer repeatedly raises concerns that turn out to be unfounded, and the team starts to tune them out? How would you balance encouraging open concern-raising with keeping the team focused and moving forward?