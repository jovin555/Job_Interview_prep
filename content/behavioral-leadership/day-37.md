# behavioral-leadership — Day 37

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a battery management system fault or a charging circuit problem, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a structured root-cause investigation rather than a debate between two hypotheses. The first step is containment — ensuring patient safety by determining whether the device should be pulled from use or restricted in some way while the investigation proceeds. That's non-negotiable in a medical context.

Next, I'd gather data systematically before forming conclusions. I'd want to see field return data, device logs if available, charging behavior patterns, battery voltage curves, and any environmental factors like temperature or charge cycle counts. The key is to separate symptoms from evidence — what the user reports versus what the device actually recorded.

I'd then build a fishbone diagram to map all potential contributing factors across categories: electrical design, firmware, mechanical, environmental, and usage patterns. This prevents the team from anchoring on the two most obvious hypotheses. For each branch, I'd ask "why" repeatedly to get to root causes rather than symptoms.

For the two specific hypotheses — battery management system versus charging circuit — I'd look for discriminating evidence. For example, does the issue occur only during charging, or also during discharge? Does it correlate with specific charger models or charge states? Does the battery voltage behavior match a protection circuit fault or a charging regulation fault? These questions help narrow the investigation without prematurely committing to one theory.

I'd also make sure the investigation is documented in a way that supports regulatory requirements — an 8D report structure works well here, with clear containment actions, root cause analysis, corrective actions, and verification of effectiveness. The documentation matters as much as the technical finding, because in a medical device context, the investigation itself becomes part of the design history file.

Finally, I'd verify the corrective action actually addresses the root cause before closing the investigation. This means testing the fix under conditions that reproduce the original failure, not just confirming the device works under normal conditions.

**Possible follow-ups:**
- How would you decide whether to issue a field safety notice while the investigation is still ongoing?
- What specific data would you want to collect from field devices to discriminate between the two hypotheses?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** The core challenge here is shifting from a "one team, one product" mindset to a "shared resources, multiple priorities" model. I'd approach this in three phases: assessment, capability building, and structural changes.

In the assessment phase, I'd map the current skill set of each engineer against the anticipated needs of the upcoming projects. This isn't just about technical skills — it's also about understanding who thrives on deep focus versus who can context-switch effectively, and who has the potential to become a cross-project resource. I'd also look at what the projects actually need: do they share common building blocks like power management, sensor interfaces, or communication protocols that could be reused across projects?

In the capability building phase, I'd focus on creating shared infrastructure that reduces the burden of context-switching. This means developing reusable design blocks, standardized firmware drivers, and common design guidelines that engineers can pick up quickly when moving between projects. I'd also pair engineers deliberately — for example, having a specialist from one project review designs on another project, not to do the work but to build familiarity. This cross-pollination builds confidence and reduces the "I only know my project" problem.

The structural changes are the hardest part. I'd move away from rigid project assignments toward a matrix model where engineers have a home project but are expected to contribute to others. This requires clear prioritization — engineers need to know which project takes precedence when conflicts arise. I'd also establish regular cross-project design reviews so that knowledge flows naturally between teams rather than through formal documentation alone.

Finally, I'd be honest about the trade-offs. Multi-project flexibility comes at the cost of deep specialization. Some engineers will resist this, and I'd need to work with them individually to find a balance — perhaps allowing them to maintain a deep specialty in one area while contributing more shallowly to others. The goal isn't to make everyone a generalist; it's to make the team resilient enough that no single person becomes a bottleneck.

**Possible follow-ups:**
- How would you handle an engineer who is highly productive in their current single-project role but resists cross-project assignments?
- What metrics would you use to measure whether the transition to multi-project flexibility is working?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is a classic example of a system-level trade-off that can't be resolved by either team working in isolation. I'd approach it by defining the problem in terms of measurable requirements rather than opinions.

First, I'd establish what the device actually needs to do during wake-up. What's the acceptable settling time for the sensor readings? What accuracy is required during the first few samples after wake-up? What's the maximum allowable glitch or offset during the transition? These requirements should come from the clinical use case, not from what the hardware or firmware team thinks is achievable.

Once the requirements are clear, I'd design a test strategy that specifically targets the wake-up transition. This would include: measuring the analog sensor output during wake-up under controlled conditions, varying the sleep duration to see if longer sleep periods affect settling behavior, testing across temperature extremes since that affects both battery behavior and analog stability, and characterizing the power supply rails during the transition — looking for droop or ringing that could affect the sensor reference.

I'd also want to test the interaction between the firmware sleep mode and the hardware power sequencing. For example, if the firmware shuts down the sensor power supply during sleep, the wake-up sequence needs to ensure the supply is stable before the first sensor reading is taken. This is a classic coordination problem — the firmware needs to know the hardware settling time, and the hardware needs to know the firmware timing.

The test strategy should include both bench testing and automated testing. Bench testing gives you the detailed analog behavior — you can probe the actual waveforms and see what's happening during the transition. Automated testing gives you repeatability and coverage across many cycles, which is important because intermittent issues often only appear after hundreds or thousands of wake-up cycles.

Finally, I'd make sure the test results are documented in a way that supports the design verification process. The test strategy should map back to the requirements, and the results should be traceable to specific design decisions. If the wake-up transition proves problematic, the team needs to decide whether to adjust the firmware timing, add hardware settling circuitry, or accept a slightly longer wake-up time in exchange for stability.

**Possible follow-ups:**
- How would you decide whether the sleep mode is worth the risk if the wake-up transition proves difficult to stabilize?
- What specific test equipment would you use to characterize the wake-up transition?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** The first thing I'd do is separate the technical debate from the interpersonal dynamics. The goal of the review is to make the best engineering decision, not to determine whose opinion wins. I'd structure the review around specific evaluation criteria rather than allowing it to become a general "my architecture is better than yours" discussion.

The evaluation criteria should include: reliability and failure modes, development complexity, testability, regulatory risk, power consumption, cost, and long-term maintainability. Each criterion needs to be weighted based on the device's requirements. For a medical device, reliability and regulatory risk might outweigh cost and complexity. For a battery-powered device, power consumption might be critical.

I'd ask each side to present their architecture against these criteria with specific evidence. The modular team should explain how they handle inter-processor communication failures, how they ensure synchronization, and how they test the system as a whole. The single-processor team should explain how they handle the processing load, whether they have enough I/O and peripherals, and what happens if a single point of failure occurs.

I'd also push both sides to address the failure modes of their approach. For the modular design: what happens if one microcontroller fails? Can the others detect it and enter a safe state? For the single-processor design: what happens if the processor has a latent defect or a firmware bug that takes down the entire system? Both approaches have failure modes — the question is which failure modes are more acceptable for the specific clinical use case.

A key consideration is the team's experience. If the team has deep experience with single-processor designs but limited CAN-FD experience, that's a real risk factor regardless of which architecture is theoretically better. I'd want to understand the team's confidence level and what training or support would be needed for the modular approach.

If the debate remains deadlocked, I'd propose a prototyping exercise. Build a minimal proof-of-concept for both architectures and measure the critical parameters — communication latency, reliability under stress, power consumption, and development effort. This turns a theoretical debate into an empirical one. The prototype doesn't need to be complete; it just needs to be enough to validate the key assumptions on both sides.

Finally, I'd document the decision with rationale, including the alternatives considered and why they were rejected. This is critical for regulatory purposes — the design history file needs to show that the architecture decision was made deliberately, not arbitrarily.

**Possible follow-ups:**
- How would you handle a situation where the prototyping exercise is inconclusive?
- What specific failure modes would you want to analyze for each architecture before making a decision?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** The key here is to create psychological safety while also maintaining technical rigor. Engineers need to know that raising a concern — even a vague one — will be met with curiosity rather than defensiveness. But they also need to understand that a "gut feeling" is the starting point of an investigation, not the conclusion.

I'd start by modeling the behavior myself. When I have a concern about a design decision, I'd voice it openly, even if I can't fully articulate why. I'd say something like, "I have an uneasy feeling about this approach, and I'd like to explore it before we commit." This signals that it's acceptable to raise concerns without having a fully formed argument.

I'd also establish a norm that concerns are addressed with a structured response. When someone raises a concern, the team's job is to take it seriously and investigate — not to dismiss it or demand immediate proof. The person raising the concern doesn't need to have the answer; they just need to have identified a potential issue. The team's job is to determine whether the concern has merit.

One practical technique is to separate the "concern-raising" phase from the "problem-solving" phase. When someone raises a concern, the first response should be acknowledgment and exploration, not rebuttal. Only after the concern is fully understood should the team move into problem-solving mode. This prevents the natural tendency to immediately defend the existing decision.

I'd also make it clear that raising a concern that turns out to be unfounded is not a negative event. If someone raises a concern and investigation shows it's not an issue, that's still a valuable contribution — it means the team has verified the decision rather than assuming it was correct. I'd explicitly acknowledge this when it happens, so people don't learn to stay silent.

For the "senior person made the decision" dynamic, I'd establish a norm that seniority doesn't determine correctness. The best decision wins, regardless of who proposed it. This means senior engineers need to be willing to change their minds when presented with valid concerns, and they need to model that behavior publicly.

Finally, I'd create a formal mechanism for capturing concerns that might otherwise be lost. This could be a "concerns log" in the design history file, where anyone can raise a concern at any time, and the team is responsible for addressing it or explicitly deciding not to address it with rationale. This ensures that concerns raised informally don't get forgotten, and it creates a record that supports regulatory requirements.

**Possible follow-ups:**
- How would you handle a situation where a junior engineer repeatedly raises concerns that turn out to be unfounded, and the team is starting to tune them out?
- How would you distinguish between a legitimate "gut feeling" that warrants investigation and a concern that is based on misunderstanding or lack of information?