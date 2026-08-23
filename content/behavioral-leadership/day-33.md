# behavioral-leadership — Day 33

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor hardware failure or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by establishing a structured investigation framework before any conclusions are drawn, because the risk with dual-cause scenarios is that teams anchor on their preferred hypothesis early. The first step would be to clearly define the observed symptom in measurable terms — what exactly is the device doing, under what conditions, and what data supports that characterization? I'd then form a small cross-functional team with representation from both hardware and firmware, and explicitly frame the goal as understanding the failure mechanism, not assigning blame.

From there, I'd use a fishbone diagram to map all plausible contributing factors across categories — sensor hardware, firmware filtering, power supply stability, environmental conditions, and patient/user interaction patterns. This prevents the investigation from narrowing too quickly. Next, I'd gather evidence systematically: pull field-returned units if available, review the firmware filter implementation against the sensor datasheet specifications, examine the raw unfiltered sensor data if it was logged, and check whether the failure correlates with specific hardware revisions or firmware versions.

The key discriminator is usually to design experiments that would produce different outcomes depending on which hypothesis is correct. For example, if the sensor hardware is at fault, you'd expect the raw signal to show anomalies before filtering; if the filter algorithm is at fault, the raw signal might look clean but the processed output would be wrong. I'd also look at the failure rate distribution — does it cluster in certain production lots or environmental conditions, which would point to hardware, or does it correlate with specific firmware update timing, which would point to software?

Throughout this process, I'd document everything in a format that supports the design history file, because in a medical device context, the investigation itself becomes part of the quality record. Once the root cause is identified with reasonable confidence, I'd implement containment actions first — such as a field advisory or a firmware patch that mitigates the immediate risk — then develop the permanent corrective action, and finally verify effectiveness through targeted testing before closing the investigation.

**Possible follow-ups:**
- How would you handle the situation if the evidence is genuinely ambiguous and you cannot definitively isolate one root cause?
- What level of confidence would you require before implementing a corrective action, and how would you communicate residual uncertainty to the team?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** The core challenge here is shifting from a "one team, one product" mindset to a "shared resources, multiple priorities" model, which requires both structural and cultural changes. I'd start by assessing the current skill matrix across the team — who has deep expertise in which areas, who has adjacent skills that could be developed, and where the critical single points of failure are. This assessment would inform both project staffing and a deliberate cross-training plan.

I'd then work with the team to define a capability development roadmap that balances project needs with individual growth. The goal isn't to make everyone a generalist, but to create enough redundancy that no project is blocked by one person's availability. For example, if one engineer is the only expert in analog sensor design, I'd pair them with a digital-focused engineer on a project that requires both skill sets, with the explicit expectation that knowledge transfer is part of the deliverable. Similarly, I'd look for opportunities to rotate engineers across projects in a structured way — not just "help out when needed," but with defined learning objectives and a mentor on the receiving team.

I'd also establish shared infrastructure that reduces the cost of context-switching: common design guidelines, reusable schematic blocks, standardized firmware drivers, and a centralized knowledge base. When engineers move between projects, they shouldn't have to reinvent the wheel each time. This is especially important in medical devices where design history documentation and compliance requirements are consistent across products — the processes transfer even if the technical details don't.

Finally, I'd be transparent about the transition timeline and the rationale. Engineers who are used to deep specialization may feel threatened by the expectation to broaden their skills, so it's important to frame this as career growth rather than dilution of expertise. I'd also watch for signs of overload during the transition — multi-project work can easily lead to context-switching fatigue — and adjust staffing or priorities before burnout becomes a problem.

**Possible follow-ups:**
- How would you handle an engineer who resists cross-training because they believe their deep specialization is more valuable to the team?
- What metrics or indicators would you use to track whether the transition is succeeding?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is a classic systems-level trade-off that requires the test strategy to address both the firmware's promise (extended battery life) and the hardware's concern (sensor stability). I'd start by defining what "stable" means in measurable terms — what is the acceptable settling time and accuracy tolerance for the sensor readings after wake-up, and how does that compare to the normal operating mode? Without a clear specification, the hardware team's concern remains vague and the firmware team can't design against it.

The test strategy would then have three layers. First, characterization testing: measure the actual current draw in the new sleep mode across the full battery voltage range and temperature range, and simultaneously capture the sensor output during wake-up transitions. This gives us the data to evaluate both claims — does the sleep mode actually deliver the expected battery life, and does the sensor output show unacceptable transients or settling behavior? Second, stress testing: deliberately vary the wake-up conditions — different sleep durations, different battery states of charge, different temperatures — to find edge cases where the sensor behavior might degrade. Third, long-duration soak testing: run the device through many sleep/wake cycles to catch issues that only appear with repeated transitions, such as drift or cumulative errors.

I'd also design the test to be diagnostic rather than just pass/fail. If the sensor is unstable during wake-up, we need to know whether the issue is power supply settling, reference voltage drift, or firmware reading too early. So the test setup should include the ability to capture raw sensor data alongside the processed output, and ideally monitor the power rail during the transition.

If the testing reveals a real conflict — the sleep mode saves power but the sensor needs longer to stabilize — then the solution is likely a firmware change: delay the first reading until the sensor has settled, or use a two-stage wake-up where the analog front-end powers up before the full system. The test strategy should be designed to inform that kind of design decision, not just to validate a fixed approach.

**Possible follow-ups:**
- How would you decide how much testing is enough before signing off on the new sleep mode?
- What would you do if the battery life improvement is significant but the sensor stability issue cannot be fully resolved?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd approach this as a decision that needs to be made on evidence and requirements, not on architectural preference. The first step would be to ensure the review is structured around the actual system requirements — what are the real-time constraints, the safety requirements, the expected data throughput, the power budget, and the long-term maintainability needs? Both architectures should be evaluated against these criteria, not against general principles like "simpler is better" or "modular is more flexible."

I'd ask the architect to walk through the specific reasons for the modular choice: Is there a genuine need for physical separation (for example, sensors in different locations)? Are there processing tasks that need to run concurrently with hard real-time deadlines? Is there a safety argument for isolating functions so that a failure in one subsystem doesn't affect others? Similarly, I'd ask the engineers advocating for the single-processor approach to articulate their concerns concretely — is it about CAN-FD protocol complexity, debugging difficulty, power consumption, or something else?

The key is to convert opinions into testable claims. If someone says "CAN-FD adds complexity," the follow-up question is: what specific complexity, and what is the actual risk to the project? If someone says "a single processor is more reliable," the question is: what failure mode does it prevent, and does the modular design introduce a failure mode that the single-processor design doesn't have?

In a medical device context, I'd also bring in the regulatory perspective early. Both architectures need to be defensible in a design history file — the rationale for the choice needs to be documented, and the safety analysis needs to address failure modes at the system level. A modular design with multiple processors might require a more complex failure modes and effects analysis, but it might also provide better fault isolation. A single processor might be simpler to analyze, but it creates a single point of failure.

If the disagreement persists after the technical discussion, I'd suggest a rapid prototyping or simulation exercise to generate data on the specific points of contention — for example, measuring actual CAN-FD latency under worst-case bus loading, or benchmarking the single-processor's ability to handle the combined processing load. Data from a prototype is much more persuasive than architectural arguments in the abstract.

**Possible follow-ups:**
- How would you handle the situation if the prototyping exercise is inconclusive or shows that both architectures are technically viable?
- What role would the regulatory or quality team play in this architectural decision?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** The foundation of this culture is psychological safety, but that's built through specific behaviors and structures, not just a stated value. I'd start by modeling the behavior myself — explicitly inviting challenge on my own decisions, and responding to concerns with genuine curiosity rather than defensiveness. When someone raises a concern, even a vague one, the response should be "help me understand what's bothering you about this" rather than "what's your evidence?"

I'd also create structured opportunities for early concern-raising that lower the barrier to speaking up. For example, design reviews should have a dedicated time for "concerns and intuitions" where team members can raise issues without needing to have a fully formed technical argument. The expectation is that the team will help develop the concern into a testable hypothesis, rather than dismissing it for lack of detail. This is particularly important in medical device development, where a vague unease about a design might be the first signal of a safety issue that hasn't yet been articulated.

Another key element is how the team responds when a concern turns out to be valid. If someone raises a concern that catches a real problem, that should be celebrated and documented as a positive example, not treated as an embarrassment for the person who made the original decision. Conversely, if a concern turns out to be unfounded, the person who raised it should not be made to feel foolish — the process of investigating and dismissing it should still be seen as valuable due diligence.

I'd also work to separate the idea of "the decision is wrong" from "the decision might need more scrutiny." A concern doesn't have to overturn a decision to be worth raising — it might just reveal an assumption that needs to be documented, or a risk that needs to be mitigated even if the decision stands. This framing makes it safer for people to speak up because they're not positioning themselves as opposing the decision, just as contributing to its robustness.

Finally, I'd be attentive to power dynamics. If a senior person makes a decision, junior team members need to see that challenging it doesn't carry career risk. That means the senior person's response to challenge is the most important behavior in the culture — if they respond well, others will follow; if they respond poorly, no amount of stated values will overcome that.

**Possible follow-ups:**
- How would you handle a situation where a team member repeatedly raises concerns that turn out to be unfounded, and the team is starting to tune them out?
- How would you distinguish between a healthy culture of questioning and a culture where decisions are never finalized because they're endlessly revisited?