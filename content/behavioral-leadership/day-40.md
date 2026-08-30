# behavioral-leadership — Day 40

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a battery management system fault or a charging circuit problem, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a structured root-cause investigation rather than a debate between two hypotheses. The first step is containment — ensuring patient safety and preventing further field exposure while the investigation runs. That might mean issuing a clinical hold or usage restriction, depending on severity. Then I'd assemble a small cross-functional team with representation from hardware design, firmware, and quality, and begin with a clear problem statement: what exactly is the reported symptom, under what conditions does it occur, and what data do we have from the field?

Rather than arguing about which subsystem is at fault, I'd focus on gathering evidence. I'd want to see the actual field data — battery voltage curves, charge/discharge cycles, temperature logs, and any fault flags the firmware recorded. I'd also want to examine returned units if available. The key is to look for discriminating evidence: for example, if the issue only occurs during charging, that points toward the charging circuit; if it occurs during discharge or standby, the battery management system becomes more likely. I'd also check whether the failure signature matches known failure modes for each subsystem — for instance, a charging circuit problem might show specific voltage/current ripple patterns, while a BMS fault might show incorrect state-of-charge estimation or cell imbalance.

I'd use a fishbone diagram to systematically capture all potential contributing factors across design, manufacturing, usage, and environment. Then I'd apply 5-whys to the most plausible branches. The critical discipline here is not to jump to a fix before the root cause is confirmed. Each hypothesis should have a corresponding test or analysis that would confirm or eliminate it. Once the root cause is identified, I'd implement both a corrective action for the design and a verification plan to prove the fix works under the exact conditions that triggered the failure. Finally, I'd document the entire investigation in the design history file, including the evidence trail and the rationale for the chosen corrective action.

**Possible follow-ups:**
- How would you handle the situation if the field data is incomplete or inconsistent, and you can't get enough returned units to perform a thorough analysis?
- What role would risk management (ISO 14971) play in deciding whether to issue a field correction while the investigation is still ongoing?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** The core challenge here is shifting from a "one product, one team" mindset to a portfolio mindset where engineers need to move between projects and share expertise. I'd start by understanding the current skill distribution across the team — who has deep expertise in which areas, and where the gaps are for the upcoming projects. I'd map the technical requirements of each project in the portfolio against the team's current capabilities, and identify both overlaps and unique demands.

The roadmap would have several tracks. First, a skills development track: I'd identify cross-training opportunities where engineers can build breadth without losing their depth. For example, an engineer who specializes in analog front-end design might shadow a colleague on a digital-heavy project, or take ownership of a small subsystem in a different domain. Second, a knowledge-sharing track: I'd establish regular technical forums where engineers present their work, not just as a status update but as a teaching opportunity — explaining design decisions, trade-offs, and lessons learned. This builds a shared vocabulary and makes it easier for people to move between projects later.

Third, a project assignment strategy: I'd deliberately staff projects with a mix of deep specialists and engineers who are building breadth, so that knowledge transfer happens naturally through pair work and design reviews. Fourth, a documentation and standardization track: multi-project portfolios benefit from reusable design guidelines, checklists, and reference designs. I'd invest time in codifying the team's hard-won knowledge into artifacts that reduce the learning curve for anyone moving to a new project.

Finally, I'd be honest about the tension between specialization and flexibility. Deep expertise is valuable, and I wouldn't want to lose it. The goal is not to make everyone a generalist, but to create enough cross-project fluency that the team can absorb workload spikes and cover for each other without compromising quality. I'd also work with each engineer individually to understand their career interests — some will want to deepen their specialty, others will want to broaden — and align the roadmap accordingly.

**Possible follow-ups:**
- How would you measure whether the transition is working, beyond just project delivery metrics?
- How would you handle an engineer who is highly resistant to cross-training because they feel it dilutes their expertise?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is a classic systems-level trade-off that needs a test strategy designed around the specific risk: the wake-up transition. The firmware team's goal is legitimate — longer battery life is a real user benefit, especially for a wearable or portable device. The hardware team's concern is also legitimate — analog sensors often need time to settle after power cycling, and if the firmware wakes the system too quickly, the first readings could be inaccurate or noisy.

I'd approach this by first defining what "stable" means in measurable terms. What is the acceptable settling time for the sensor output after wake-up? What is the maximum allowable error in the first few readings? These should be derived from the device's clinical requirements, not from what's convenient for either team. Once we have clear acceptance criteria, we can design a test strategy around them.

The test strategy would have several layers. First, characterization testing: I'd want to characterize the wake-up behavior across the full operating range — different temperatures, battery voltages, and sensor configurations. This tells us what the actual settling time is, rather than relying on worst-case assumptions. Second, stress testing: I'd test the wake-up transition repeatedly — thousands of cycles — to catch intermittent issues that might not appear in a single test. Third, boundary testing: I'd test the edge cases, such as wake-up from a very deep sleep state, or wake-up when the battery is nearly depleted, where the power supply might be less stable.

I'd also design tests that specifically probe the interaction between the firmware timing and the analog behavior. For example, I'd capture the sensor output waveform during wake-up and compare it against the firmware's assumption of when the data is valid. If the firmware starts reading too early, the test should catch it. I'd also want to test the system-level behavior — not just the sensor in isolation, but the full signal chain from sensor through amplification, filtering, and ADC conversion.

Finally, I'd make sure the test results feed back into the design. If the settling time is longer than the firmware expects, the firmware team needs to adjust their timing. If the settling time is acceptable but marginal, we might add a small hardware change, such as a faster-settling reference or a dedicated wake-up sequence. The key is that the test strategy doesn't just validate a decision — it generates data that informs the design.

**Possible follow-ups:**
- How would you handle a situation where the characterization testing shows that the settling time is acceptable at room temperature but marginal at low temperatures, and the device is expected to operate in cold environments?
- How would you decide whether to add a hardware fix (like a dedicated wake-up circuit) versus a firmware fix (like a longer delay before reading the sensor)?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** The first thing I'd do is separate the technical debate from the interpersonal dynamics. The goal of the review is to make the best engineering decision, not to declare a winner. I'd structure the review so that both positions are presented on their merits, with specific criteria for evaluation.

I'd start by asking the team to define what "better" means for this specific device. Is it reliability? Development speed? Long-term maintainability? Power consumption? Cost? Ease of certification? Each of these criteria might favor a different architecture. For a medical device, reliability and certifiability are usually paramount, but they need to be weighed against the practical realities of development timeline and team expertise.

Then I'd ask both sides to present their case against these criteria. The modular architecture advocates should explain why multiple microcontrollers are justified — perhaps the device has hard real-time constraints that are better isolated on separate processors, or perhaps the modularity enables independent development and testing of subsystems. The single-processor advocates should explain why their approach is simpler — fewer points of failure, no inter-processor communication to debug, simpler power management, and a smaller codebase to certify.

I'd also push both sides to address the weaknesses of their preferred approach. For the modular design: what happens if the CAN-FD bus has a fault? How do you handle firmware updates across multiple processors? What is the added complexity of debugging a distributed system? For the single-processor approach: what happens if one subsystem has a timing issue that affects another? How do you isolate faults? What is the risk of a single point of failure?

If the debate remains unresolved, I'd suggest a data-driven approach: build a small proof-of-concept or prototype that exercises the riskiest aspects of each architecture. For example, if the concern is CAN-FD reliability, build a test harness that stresses the bus under realistic conditions. If the concern is real-time performance on a single processor, benchmark the worst-case interrupt latency and task scheduling. The prototype doesn't need to be complete — just enough to retire the key technical risks.

Finally, I'd make sure the decision is documented with rationale, including the alternatives considered and the reasons for rejection. This is critical for regulatory purposes — the design history file should show that the architecture was chosen through a deliberate, traceable process, not just a consensus or a power struggle.

**Possible follow-ups:**
- How would you handle the situation if the proof-of-concept testing is inconclusive, and the team remains split?
- What role would the regulatory strategy play in your decision — for example, if one architecture is easier to certify but the other is technically superior?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** This is fundamentally about psychological safety and the norms of technical discourse. Engineers won't raise concerns if they fear being dismissed, embarrassed, or punished for being wrong. So the first step is to model the behavior I want to see: I'd openly raise my own concerns, even when they're half-formed, and I'd make a point of thanking people who raise concerns — not just when they're right, but when they're thoughtful.

I'd also establish a clear norm that a "gut feeling" is a valid starting point for a technical discussion, not a conclusion. The expectation would be that if someone has a concern, they bring it forward early, and the team's job is to help them articulate it — to ask questions like "What specifically feels off?" or "What would need to be true for your concern to be valid?" This turns a vague feeling into a testable hypothesis. The person raising the concern doesn't need to have the full technical argument worked out; they just need to be willing to engage in the process of refining it.

I'd also separate the idea-generation phase from the evaluation phase. In design reviews, I'd explicitly invite concerns and alternative viewpoints before the team settles on a decision. Once a decision is made, I'd still leave the door open for new information — but I'd make it clear that revisiting a decision requires new evidence, not just a rehash of the same arguments. This prevents the culture from becoming one where decisions are endlessly reopened.

Another practical step is to create multiple channels for raising concerns. Some engineers are comfortable speaking up in a group; others prefer to raise concerns one-on-one or in writing. I'd make sure all of these channels are available and that concerns raised through any channel are taken seriously and tracked to resolution. I'd also make it safe to raise concerns anonymously if needed, at least initially, until trust is built.

Finally, I'd address the behavior of senior engineers directly. If a senior person dismisses a junior engineer's concern, I'd intervene in the moment — not to embarrass the senior person, but to model how to engage with the concern constructively. Over time, the expectation becomes that seniority doesn't determine the validity of a technical argument; evidence and reasoning do.

**Possible follow-ups:**
- How would you handle a situation where an engineer repeatedly raises concerns that turn out to be unfounded, and the team starts to tune them out?
- How would you balance the need for psychological safety with the need to make decisions and move forward on a project timeline?