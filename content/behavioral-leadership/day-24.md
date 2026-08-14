# behavioral-leadership — Day 24

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor calibration drift or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a data-collection problem rather than a debate between hardware and firmware. The first step is to gather as much field data as possible — device logs, calibration records, environmental conditions at time of failure, and any error codes. I'd want to understand whether the issue correlates with device age, temperature, or specific firmware versions, since calibration drift typically worsens over time while algorithm errors often appear after a specific firmware update or under particular input conditions.

Next, I'd design experiments to discriminate between the two hypotheses. For calibration drift, I'd look at raw sensor readings before filtering — if the raw values are shifting over time, that points to the sensor or reference circuit. For a filtering algorithm error, I'd examine whether the raw data looks correct but the processed output is wrong. I'd also check if the issue reproduces in a controlled lab environment with known-good sensors, which would strongly suggest firmware.

I'd document the investigation using a structured approach like 8D or a fishbone diagram, capturing evidence for each hypothesis. The key is to avoid jumping to corrective action until the root cause is confirmed. I'd also consider whether both causes could be contributing — sometimes a marginal sensor combined with an algorithm that's sensitive to certain input characteristics creates a failure that neither team sees in isolation. Once the root cause is confirmed, I'd implement containment (like a field alert or software patch) while developing the permanent corrective action, and I'd verify the fix addresses the actual failure mode before closing the investigation.

**Possible follow-ups:** How would you handle it if the field data is sparse and you can't get enough samples to statistically distinguish between the two causes? What containment actions would you consider while the investigation is ongoing?

---

## Q2: How would you approach managing a situation where a senior engineer on your team consistently delivers excellent technical work but has a pattern of dismissing questions from junior engineers during design reviews, saying things like "that's obvious" or "we don't need to discuss that"?

**Answer:** I'd approach this as a coaching and culture issue rather than a performance problem. The senior engineer's technical work is strong, so the issue is about how their behavior affects team dynamics and the quality of design reviews. Dismissive responses discourage junior engineers from raising concerns, which is dangerous in medical device development where a question that seems "obvious" might reveal a real gap in the design.

First, I'd have a private conversation with the senior engineer to understand their perspective. They may not realize how their tone comes across, or they may be frustrated by questions they perceive as basic. I'd frame the conversation around the value of diverse perspectives in design review — a question from a junior engineer might catch an assumption that the senior engineer has held for years without questioning. I'd also point out that the goal of a design review isn't just to validate the design but to build the team's understanding, and that answering questions thoroughly is part of their leadership responsibility.

In parallel, I'd work on the review process itself. I could introduce a structured format where questions are collected and addressed systematically, rather than in a free-form discussion where a dominant voice can shut down others. I might also assign the senior engineer a mentoring role for specific junior engineers, which gives them a constructive outlet for their expertise and creates a context where they're expected to explain their reasoning.

If the behavior continues, I'd be more direct about the impact — explaining that the team is losing valuable input and that junior engineers are becoming reluctant to speak up, which is a real risk to design quality. I'd also check in with the junior engineers to make sure they feel supported and encourage them to keep raising questions, even if the initial response is dismissive.

**Possible follow-ups:** How would you handle it if the senior engineer responds defensively and says the junior engineers should "do their homework" before asking questions? What would you do if you notice the junior engineers have started avoiding design reviews altogether?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** I'd approach this as a system-level problem that requires both teams to understand each other's constraints. The firmware team sees an opportunity to extend battery life, which is a real product benefit. The hardware team is concerned about analog settling time and potential measurement errors during the transition from sleep to active mode. Both concerns are valid, so the test strategy needs to address the interface between them.

First, I'd define the specific failure modes we're worried about. For the hardware side, that includes: power supply settling time after wake-up, reference voltage stability, sensor bias settling, and any transient noise from the switching regulator or power management IC. For the firmware side, that includes: the exact sequence of wake-up events, timing between waking the sensor and taking a measurement, and whether the firmware waits for the hardware to stabilize before reading data.

The test strategy would have three layers. First, bench-level characterization: measure the actual settling times of the power rails and sensor outputs during wake-up transitions, using an oscilloscope and precision measurements. This gives us real data on whether the hardware concern is justified and what margin exists. Second, firmware-level testing: verify that the firmware respects the measured settling times and doesn't take measurements too early. This might involve adding a configurable delay or a "data ready" signal from the sensor. Third, system-level testing: run the device through realistic use cycles — including frequent wake-ups and long sleep periods — and compare measurement accuracy against a known reference.

I'd also include a stress test that simulates worst-case conditions: rapid wake-sleep cycling, low battery voltage, and temperature extremes. The goal is to find the boundary conditions where the sleep mode causes measurement errors, so we can either adjust the firmware timing or add hardware margin. Finally, I'd document the test results and the rationale for the final design — whether that's implementing the sleep mode with adjusted timing, or deciding that the hardware needs a faster-settling reference or additional decoupling.

**Possible follow-ups:** How would you handle it if the bench testing shows that the settling time is longer than the firmware team's target wake-up time, and neither team wants to compromise? What if the extended battery life from the sleep mode is critical for the product's market positioning?

---

## Q4: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** I'd start by understanding the current state of the team's skills and the demands of the new portfolio. The transition from single-product to multi-project requires a shift from deep specialization to a broader skill set, but that doesn't mean everyone needs to be a generalist. The goal is to create a team where each member has a primary area of depth plus enough breadth to contribute across projects, and where knowledge sharing is structured rather than ad hoc.

The roadmap would have several phases. First, assessment: map the team's current skills against the requirements of the new projects. Identify gaps — both technical gaps (e.g., someone who only knows I2C now needs to work with CAN-FD) and process gaps (e.g., engineers who are used to a single design history file now need to manage multiple concurrent DHFs). Second, training and cross-training: pair engineers on projects outside their specialty, create internal technical talks, and encourage shadowing during design reviews. The goal is to build a baseline level of familiarity across the portfolio while maintaining depth in each person's core area.

Third, process adaptation: the single-product workflow likely has serial handoffs — hardware finishes, then firmware starts. Multi-project requires more parallel work and more frequent integration points. I'd introduce lightweight design reviews at the architecture level so that engineers working on different projects can share lessons learned. Fourth, resource planning: with multiple projects, there will be competing demands for the same specialists. I'd work with project managers to identify which tasks truly require deep expertise and which can be handled by engineers with broader skills, and I'd build a training plan to develop that breadth over time.

Finally, I'd establish a knowledge-sharing mechanism — a design guidelines document, a lessons-learned log, or regular technical forums — so that the team doesn't lose the benefits of specialization even as they become more flexible. The transition is as much about culture as it is about skills, so I'd also recognize and reward cross-project contributions, not just deep technical work in a single area.

**Possible follow-ups:** How would you handle it if some engineers resist the transition and want to stay in their specialized role? How would you balance the need for cross-training against the risk of losing deep expertise in a critical area?

---

## Q5: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd approach this as a decision that needs to be based on system requirements, not architectural preference. Both approaches have legitimate trade-offs, and the right choice depends on factors like the device's complexity, safety requirements, power budget, and the team's ability to maintain the system over its lifecycle.

First, I'd make sure the review is structured around objective criteria rather than opinions. I'd ask the team to define what "reliable" means for this specific device — is it about fault tolerance, deterministic timing, or minimizing points of failure? A modular design with multiple microcontrollers can actually improve fault isolation — if one processor fails, the others can maintain critical functions. A single processor simplifies the system but creates a single point of failure. For a medical device, the safety case matters more than simplicity.

Second, I'd push for data. If the concern is CAN-FD reliability, I'd ask for evidence — what's the expected bus load, what's the error handling strategy, and what happens if a message is corrupted or lost? If the concern is about the complexity of multi-processor firmware, I'd ask about the team's experience with distributed systems and whether they have the tooling to debug cross-processor issues. I'd also consider the regulatory implications — a modular design might make it easier to isolate changes during design verification, but it also means more interfaces to document and test.

Third, I'd look at the specific requirements that might favor one approach. For example, if the device has hard real-time constraints for motor control and also needs to handle complex user interface logic, separating those onto different processors can make the timing analysis much simpler. If the device is small and battery-powered, a single processor might be more power-efficient. If the device needs to be upgraded in the field, a modular design might allow updating one function without affecting others.

Finally, I'd make sure the decision is documented with the rationale, including the alternatives considered and why they were rejected. If the team still disagrees after the review, I'd suggest a prototyping exercise — build a minimal version of the critical communication path on CAN-FD and measure the actual timing and error rates. That data will resolve the disagreement more effectively than another meeting.

**Possible follow-ups:** How would you handle it if the disagreement is not about technical merits but about the team's confidence in their ability to debug a multi-processor system? What if the architect's modular design is driven by a desire to reuse existing code from a previous project, and the senior engineers see that as a hidden agenda?