# behavioral-leadership — Day 30

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor hardware failure or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by establishing a structured investigation framework before any analysis begins, so the team doesn't anchor on one hypothesis. The first step is containment — ensuring patient safety isn't at risk while we investigate. That might mean a field safety notice, a usage restriction, or increased monitoring, depending on the severity.

Then I'd set up a formal root-cause analysis using something like 8D or a fishbone approach. The key is to gather data that discriminates between the two hypotheses rather than data that confirms either one. For a sensor hardware failure versus a firmware filtering issue, I'd look for discriminating evidence: raw sensor data logs versus filtered output, failure patterns across device lots and firmware versions, environmental conditions at time of failure, and whether the failure correlates with specific sensor serial numbers or production batches.

I'd also make sure both the hardware and firmware teams contribute to the data collection plan jointly, so neither side feels the investigation is biased against them. Once we have enough data, I'd want a formal decision point where the evidence is reviewed against both hypotheses, and the team commits to the most probable cause — or acknowledges it could be both, which is common. The corrective action then follows the evidence, and we verify effectiveness before closing the investigation.

**Possible follow-ups:**
- How would you handle it if the data is inconclusive after the initial investigation?
- What would you do if one team resists accepting the evidence because it points to their area?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** I'd start by assessing the current skill distribution and identifying which capabilities are transferable across projects versus which are product-specific. The goal isn't to force everyone to become generalists — it's to build enough cross-project fluency that the team can flex resources without losing depth where it matters.

I'd structure the roadmap in phases. First, establish a shared technical foundation: common design standards, reusable building blocks, and documentation practices that work across projects. This reduces the cost of context-switching. Second, create a deliberate cross-training plan — pairing engineers from different projects on specific tasks, or having engineers lead design reviews for projects outside their specialty. This builds familiarity without pulling them off their core work entirely.

I'd also introduce a lightweight resource allocation process that makes trade-offs visible. When projects compete for the same specialist, the team needs a transparent way to prioritize — not just whoever shouts loudest. Finally, I'd set expectations that career growth now includes cross-project contribution, not just deeper specialization. That means recognizing and rewarding engineers who successfully apply their skills in new contexts.

**Possible follow-ups:**
- How would you handle an engineer who is deeply specialized and resistant to working outside their area?
- What metrics would you use to track whether the transition is succeeding?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** I'd approach this as a risk trade-off that needs data on both sides. The firmware team's concern is battery life — a legitimate product requirement. The hardware team's concern is sensor stability — a legitimate safety and performance requirement. Neither should win by default; the test strategy should resolve the uncertainty.

I'd design a test matrix that specifically exercises the wake-up transition under realistic conditions: different sleep durations, different battery voltage levels, different temperatures, and repeated wake cycles. The key is to characterize the analog sensor settling time and accuracy during the transition window, not just steady-state performance. I'd also want to measure whether the wake-up transient affects the sensor reading itself or just the signal chain — those have different implications.

I'd also include a stress test that simulates worst-case conditions: frequent wake-ups, low battery, and noisy environments. If the sensor instability only appears under narrow conditions, the team can decide whether to accept the risk, add a settling delay in firmware, or adjust the hardware. The test strategy should produce data that lets the team make an informed trade-off rather than arguing from opinion.

**Possible follow-ups:**
- What specific sensor parameters would you measure during the wake-up transition?
- How would you decide whether the sleep mode is acceptable if the sensor instability only occurs under extreme conditions?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd structure the review so that the discussion is driven by requirements and evidence, not preference. The first step is to clarify what the architecture needs to achieve: safety requirements, performance constraints, power budget, development timeline, and long-term maintainability. Both architectures should be evaluated against the same criteria.

I'd ask the architect to present the modular design's rationale — what drove the decision, what trade-offs were considered, and what alternatives were rejected and why. Then I'd give the opposing engineers the same opportunity. The key is to separate facts from opinions: what data exists to support each approach, and what is speculative?

I'd also push the discussion toward specific technical concerns rather than general preferences. For example, if the concern is reliability, we should discuss failure modes of multi-processor communication versus single-processor complexity. If the concern is development risk, we should discuss team experience and toolchain maturity. I'd want the review to produce a decision matrix with clear criteria, and if the team still can't agree, I'd propose a prototyping or simulation exercise to generate data on the most contentious points.

**Possible follow-ups:**
- How would you handle it if the architect has already invested significant time in the modular design and is resistant to revisiting the decision?
- What specific criteria would you put in the decision matrix?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** I'd start by modeling the behavior myself — openly questioning my own decisions and inviting challenge. If the leader doesn't demonstrate that raising concerns is safe, no policy will make it happen. I'd also make a distinction between raising a concern and having a fully formed argument. A gut feeling is valid input; it means something doesn't sit right, and that's worth exploring. The expectation isn't that the person has the answer — it's that they flag the discomfort so the team can investigate.

I'd also create structured opportunities for early concerns: design reviews that explicitly include a "what worries you about this?" segment, or a standing agenda item in project meetings where anyone can raise a concern without needing to propose a solution. The key is to respond constructively when someone does raise a concern — even if it turns out to be unfounded. If people get dismissed or embarrassed for speaking up, they'll stop doing it.

Finally, I'd work on the team's decision documentation. When decisions are made, I'd want the rationale recorded, including what was considered and rejected. That makes it easier for someone to raise a concern later because they can point to a specific assumption or trade-off they disagree with, rather than challenging the decision as a whole.

**Possible follow-ups:**
- How would you handle a situation where someone repeatedly raises concerns that turn out to be unfounded?
- What would you do if a senior engineer reacts defensively when their decision is challenged?