# behavioral-leadership — Day 32

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor hardware failure or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing the investigation around evidence rather than hypotheses, because the moment we pick a side, we bias the data collection. The first step is containment — ensuring patient safety isn't at risk while we investigate. That might mean issuing a clinical hold or a field action depending on severity. Then I'd assemble a small cross-functional team with representation from both hardware and firmware, and we'd define what data we need to discriminate between the two causes without assuming either is correct.

The key is to look for discriminating evidence — data points that would behave differently depending on which hypothesis is true. For a sensor hardware failure, I'd expect to see the raw ADC readings behaving abnormally — saturation, stuck values, or noise patterns that don't correlate with the physical quantity being measured. For a firmware filtering error, the raw sensor data would look correct, but the processed output would be wrong. So I'd want to capture both raw and filtered data from affected devices, ideally with timestamps so we can correlate with the reported symptom onset.

I'd also pull the design history file and review the sensor calibration records and the filter implementation. If we have returned units, I'd do bench testing — measuring the sensor directly with known stimuli while logging both raw and processed values. The 8D methodology fits well here: define the problem precisely, contain, find root cause with data, implement corrective action, and verify effectiveness. The important discipline is not to jump to corrective action until the root cause is confirmed with evidence, because if we guess wrong, we've wasted time and potentially left the real problem in the field.

**Possible follow-ups:**
- How would you handle pressure from management to implement a fix quickly before the root cause is confirmed?
- What if the two hypotheses are not mutually exclusive — how would you structure the investigation to detect a combined cause?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** The core challenge here is shifting from a "one team, one product" mindset to a model where engineers need to contribute across multiple projects without losing the deep expertise that made them valuable in the first place. I'd start by mapping the technical skills we have against the technical demands of the upcoming projects — not just the obvious overlaps, but also the adjacent skills that could be developed.

I'd structure the roadmap in three phases. The first phase is awareness: helping each engineer understand where their skills fit across the portfolio and where the gaps are. This isn't about forcing everyone to become generalists — it's about identifying which skills transfer and which are project-specific. The second phase is capability building: pairing engineers on cross-project assignments, creating shared design guidelines and reusable IP blocks, and establishing communities of practice so that knowledge doesn't stay siloed in one project. The third phase is operationalizing: adjusting the project planning process so that resource allocation explicitly accounts for skill development, not just immediate delivery needs.

A practical mechanism I'd use is a skills matrix that we review quarterly, not as a performance tool but as a planning tool. It helps us answer questions like: who can support a design review on a project they're not assigned to? Who needs a second project to round out their experience? I'd also be careful about the failure mode where engineers feel their specialization is being devalued. The message should be that deep expertise is still essential — we're just asking them to apply it in more contexts and to help others build depth in adjacent areas.

**Possible follow-ups:**
- How would you handle an engineer who resists cross-project work because they feel it dilutes their expertise?
- What metrics would you use to track whether the transition is succeeding?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is a classic case where both teams are right about different things, and the test strategy needs to address both concerns rather than picking a winner. I'd start by defining what "stable" means operationally — what are the acceptable bounds on sensor readings during and after wake-up, and how long is the settling time allowed to be? Without that shared definition, the hardware and firmware teams will be arguing past each other.

The test strategy would have three layers. First, bench-level characterization: using a controlled test setup where we can precisely time the wake-up event and capture the analog sensor output with high resolution — looking for glitches, settling time, offset shifts, or noise during the transition. This is where we'd characterize the worst-case behavior across temperature and supply voltage, because wake-up transients often interact with power supply droop. Second, system-level integration testing: running the full firmware state machine through repeated sleep/wake cycles while logging both the raw sensor data and the processed output, to see if any artifacts propagate through the filtering chain. Third, long-duration soak testing: running the device through thousands of cycles to catch intermittent issues that don't show up in short tests — things like charge pump behavior or capacitor leakage that only manifest over time.

I'd also want to look at the wake-up sequence itself as a design element, not just a test target. The firmware could stagger the wake-up — powering the analog front end first, waiting for settling, then taking a reading — rather than waking everything simultaneously. That might be a design change that satisfies both teams. The test strategy should include a phase where we experiment with different wake-up sequences and measure the trade-off between settling time and power consumption.

**Possible follow-ups:**
- How would you decide what settling time is acceptable when the clinical requirements don't specify it explicitly?
- How would you handle a situation where the sleep mode works in bench testing but fails intermittently in field use?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd approach this as a decision that needs to be made on evidence and trade-offs, not on preference or seniority. The first step is to make sure both positions are fully articulated with their underlying assumptions. The modular approach is often chosen for fault isolation, development parallelism, and the ability to use lower-cost parts. The single-processor approach is often chosen for simplicity, reduced interconnect complexity, and easier certification. Both are legitimate — the question is which set of trade-offs fits this specific device's requirements.

I'd structure the review around a few key questions. What are the safety requirements? If the device needs to maintain critical functions even when a subsystem fails, modularity might be the right call. What are the development timeline and team composition? If the team has deep expertise in one architecture and not the other, that's a real factor. What are the certification implications? A single-processor system might have a simpler safety case, but a modular system might make it easier to isolate and test individual functions. What about power, size, and cost constraints? Those might rule out one approach entirely.

I'd also push for a concrete comparison rather than an abstract debate. Ask both sides to produce a rough block diagram, a preliminary risk assessment, and an estimate of development effort. If the disagreement persists, I'd propose a prototyping exercise — build a minimal version of the critical communication path in both architectures and measure things like latency, fault behavior, and development complexity. The goal isn't to declare a winner in the meeting; it's to identify what evidence would resolve the disagreement and then go get that evidence. If we genuinely can't decide, I'd escalate with a clear framing of the trade-offs and a recommendation, rather than letting the decision stall.

**Possible follow-ups:**
- What if the architect's modular design is driven by a preference for a particular vendor's ecosystem rather than technical requirements?
- How would you handle a situation where the team reaches a decision but a minority still strongly disagrees?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** The key is to separate the act of raising a concern from the act of proving it. If engineers feel they need a fully formed technical argument before they can speak up, they'll stay silent — and sometimes that gut feeling is the first signal of a real problem. I'd establish a norm that early concerns are welcomed as discussion starters, not challenges to authority. The expectation isn't that every concern is valid or acted upon — it's that every concern gets heard and evaluated fairly.

Practically, I'd do a few things. First, in design reviews, I'd explicitly invite dissenting views — not just "does anyone have concerns?" but a structured check where each engineer is asked if they see anything that worries them, even if they can't fully articulate why. Second, I'd model the behavior myself: when I have a vague concern about a design, I'd raise it openly and say "I can't pin down exactly what bothers me about this, but I want to talk through it." That signals that uncertainty is acceptable. Third, I'd make sure that when someone raises a concern that turns out to be unfounded, they're not penalized or subtly mocked — because that will shut down future concerns.

I'd also work on the response side. When a concern is raised, the response should be "let's look at that" rather than "why do you think that?" or "that doesn't make sense." The goal is to create a culture where the cost of raising a concern is low and the cost of missing a real problem is high. In medical devices, the stakes justify erring on the side of over-communication. I'd also track concerns informally — not as a formal metric, but to notice patterns like "the junior engineers never speak up in reviews" or "concerns about power integrity always come up late" — and use those patterns to improve how we structure reviews and how early we involve the right people.

**Possible follow-ups:**
- How would you handle a situation where a junior engineer raises a concern that is technically incorrect, and a senior engineer responds dismissively?
- How would you distinguish between a healthy culture of raising concerns and a culture where every decision gets second-guessed to the point of paralysis?