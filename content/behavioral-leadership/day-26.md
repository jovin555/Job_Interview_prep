# behavioral-leadership — Day 26

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor hardware failure or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a structured root-cause investigation rather than a hardware-versus-firmware debate. The first step is containment — ensuring patient safety and preventing further exposure while the investigation runs. That might mean a field safety notice, a usage restriction, or a software workaround, depending on the risk assessment.

Then I'd establish a cross-functional team with both hardware and firmware representation, plus quality and regulatory input. The key is to gather data before forming hypotheses. I'd want to see the actual failure data — field returns, logs, waveforms, environmental conditions at time of failure. I'd look for patterns: does the failure correlate with temperature, battery level, firmware version, or manufacturing lot? That data often narrows the field significantly.

I'd use a fishbone diagram to map all potential causes systematically, then apply 5-whys to the most plausible branches. For the sensor hardware path, I'd examine the analog front-end design, component stress, and manufacturing variability. For the firmware path, I'd review the filtering algorithm's edge cases — what happens with signal saturation, transient spikes, or unusual input patterns.

A critical step is designing experiments that discriminate between the hypotheses. For example, if the sensor is suspect, bench-testing the exact sensor batch under simulated conditions might reproduce the failure. If the algorithm is suspect, replaying captured raw data through the firmware in a controlled environment would show whether the filtering logic misbehaves. The goal is to find a test that would fail differently depending on which hypothesis is true.

I'd document everything in the design history file — the investigation plan, data collected, analysis, and conclusions. The corrective action depends on the root cause, but the verification of effectiveness step is essential regardless: after implementing a fix, we need to confirm the failure mode is actually eliminated under the conditions that triggered it originally.

**Possible follow-ups:**
- How would you handle it if the investigation data points to both causes contributing simultaneously?
- What would you do if the field data is incomplete or inconsistent, making pattern analysis unreliable?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** The core challenge here is shifting from a "one team, one product" mindset to a model where engineers need to contribute across multiple projects with different technical demands. I'd approach this in phases.

First, I'd assess the current skill matrix honestly — what each engineer is strong in, where the gaps are, and which combinations of skills are needed for the upcoming project portfolio. This isn't just about technical skills; it's also about understanding who thrives on variety versus who needs deep focus to be productive.

Second, I'd design a gradual transition rather than an abrupt restructuring. For engineers who are deep specialists, I'd start by giving them a small, well-scoped task on a second project — something that leverages their expertise but introduces them to a new domain. For example, a power supply specialist could review the power architecture on a different project before being asked to design it. This builds confidence and cross-project familiarity without overwhelming anyone.

Third, I'd invest in shared infrastructure that makes cross-project work easier. That means standardized design guidelines, reusable schematic blocks, common firmware libraries, and clear documentation practices. When engineers move between projects, they shouldn't have to relearn everything from scratch. The goal is to make the organizational knowledge accessible rather than locked in individual heads.

Fourth, I'd address the cultural aspect. Some engineers will resist being pulled away from their home project. I'd be transparent about why the transition is happening, what it means for their career growth, and how we'll manage workload to avoid burnout. I'd also create opportunities for cross-project knowledge sharing — technical lunch-and-learns, paired design reviews, or rotating "integration days" where engineers from different projects review each other's work.

Finally, I'd build in feedback loops. After each quarter, I'd review how the model is working — are projects getting the support they need? Are engineers developing new skills? Is quality being maintained? The roadmap should be adjusted based on what's actually happening, not just what we planned.

**Possible follow-ups:**
- How would you handle an engineer who is highly productive in their specialty but resists cross-project assignments?
- What metrics would you use to measure whether the transition is successful?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is a classic trade-off between power optimization and measurement integrity, and the test strategy needs to address both concerns systematically. I'd start by defining what "stable" means in this context — what settling time, what voltage tolerance, what measurement accuracy is required after wake-up. Without that shared definition, the two teams will talk past each other.

The test strategy would have several layers. First, characterization testing at the bench level: instrument the device to capture the power rail behavior during the sleep-to-active transition. I'd look at the supply voltage droop, the reference voltage settling, and the sensor output during the transition window. This tells us what the hardware actually does, not just what we expect.

Second, I'd design a test matrix that covers the realistic operating conditions — different battery states (full, nominal, near-empty), different temperatures, different sensor configurations. The wake-up transient might look fine at nominal conditions but fail at low battery or cold temperature.

Third, I'd include a stress test that exercises the worst-case scenario: frequent sleep/wake cycles with the sensor sampling immediately after wake-up. This simulates the most demanding real-world usage pattern and would expose timing margins that might be hidden in a single wake-up event.

Fourth, I'd add a long-duration soak test to catch subtle issues like gradual drift or cumulative effects from repeated cycling. A device that wakes up fine once might develop problems after thousands of cycles.

The key is that both teams' concerns are addressed in the same test plan. The firmware team gets data on whether the sleep mode actually delivers the expected power savings. The hardware team gets data on whether the analog performance meets the requirement. If the tests reveal a conflict — say, the power savings are great but the sensor takes too long to stabilize — then we have a data-driven basis for negotiating the design trade-off.

I'd also make sure the test results are documented in a way that supports the design history file, since this is a medical device and the testing rationale needs to be traceable.

**Possible follow-ups:**
- How would you handle it if the test results show the sensor instability is real but only occurs in a narrow operating window that's unlikely in practice?
- What would you do if the firmware team insists the sleep mode is essential to meet the battery life requirement, but the hardware team says the sensor design can't be improved further?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd start by making sure the review is structured around objective criteria rather than personal preference. The question isn't which architecture is "better" in the abstract — it's which one better meets the product requirements, risk profile, and development constraints.

I'd frame the review around specific evaluation criteria: reliability and failure modes, development complexity, power consumption, thermal management, regulatory risk, manufacturability, and long-term maintainability. Each criterion should be weighted according to the product's requirements. For a medical device, reliability and regulatory risk would carry significant weight.

For the modular multi-MCU approach, I'd want to understand the rationale. Perhaps the architect chose it because of physical separation requirements — sensors in different locations, or isolation requirements between patient-connected and non-patient-connected sections. CAN-FD is a robust protocol with good error detection, and it's well-suited for distributed systems. But I'd also probe the failure modes: what happens if one node fails? Does the system degrade gracefully? What's the additional complexity in firmware synchronization, boot sequencing, and diagnostics?

For the single-processor approach, I'd examine whether one processor can actually handle all the processing demands — sensor sampling rates, control loops, communication, and user interface — without timing conflicts. A single processor might be simpler, but if it's overworked, it could introduce its own reliability risks.

I'd also consider the team's experience. If the team has deep experience with multi-MCU systems, that reduces the risk of the modular approach. If they're more comfortable with single-processor designs, that's a point in favor of the simpler architecture. The review should be honest about the team's capabilities.

The decision framework I'd use is a trade-off analysis with clear criteria and scoring. Each architecture gets evaluated against the criteria, and the results are documented with rationale. If the disagreement persists after the analysis, I might suggest a prototyping exercise — build a minimal proof-of-concept for the riskiest aspects of each approach and let the data inform the decision.

The key is to keep the discussion focused on evidence and requirements, not on who has the stronger personality or the more senior title.

**Possible follow-ups:**
- How would you handle it if the architect has strong ownership of the design and takes the disagreement personally?
- What specific criteria would you weight most heavily for a Class II medical device?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** This is fundamentally about psychological safety and the norms we set for technical discussion. I'd start by modeling the behavior myself — explicitly inviting challenge to my own decisions, thanking people who raise concerns even when they're not fully formed, and making it clear that raising a question early is always better than discovering a problem late.

I'd establish a norm that "I have a concern but I can't fully articulate it yet" is a valid contribution to a discussion. In practice, that means when someone raises a gut feeling, the response should be to help them explore it — ask what specifically feels off, what assumptions might be wrong, what data would help clarify. The goal is to turn the gut feeling into a testable hypothesis, not to dismiss it or demand a fully-formed argument on the spot.

I'd also separate the idea from the person. In design reviews, I'd encourage language like "I have a concern about this approach" rather than "you're wrong." And I'd make it clear that a concern about a decision is not a personal attack on the person who made it.

Another practical step is to create structured opportunities for raising concerns outside the formal review setting. Some people are more comfortable raising concerns in smaller groups or in writing. I'd make sure there are multiple channels — design review meetings, one-on-one conversations, written comments on design documents, or a shared "concerns log" where anyone can add a question or worry without having to defend it in real-time.

I'd also follow up on concerns that were raised, even if they turned out to be unfounded. If someone raises a concern and it's addressed, I'd close the loop by explaining what was considered and why the decision stood or changed. That reinforces that raising concerns is worthwhile. If a concern turns out to be valid and catches a real problem, I'd make sure the person who raised it gets credit — that's the strongest reinforcement of the behavior.

Finally, I'd be careful about how consensus is built. If decisions are made by a vocal majority, quieter team members might feel their concerns aren't welcome. I'd use techniques like round-robin check-ins where everyone is explicitly asked for their view, or anonymous input for particularly contentious decisions.

**Possible follow-ups:**
- How would you handle a situation where someone repeatedly raises concerns that turn out to be unfounded, and the team starts to tune them out?
- What would you do if a senior engineer's behavior — like dismissing junior concerns — undermines the culture you're trying to build?