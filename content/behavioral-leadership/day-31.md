# behavioral-leadership — Day 31

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor hardware failure or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a data-collection problem rather than a debate between the hardware and firmware teams. The first step is to establish a clear, shared definition of the observed failure — what exactly the device is doing, under what conditions, and how often. I'd want to gather as much field data as possible: device logs, error codes, timestamps, environmental conditions, and any patterns across the installed base.

Once we have the symptom clearly characterized, I'd structure the investigation to systematically eliminate one branch at a time. For the sensor hardware branch, I'd look at whether the raw sensor readings are plausible — checking against known physical limits, looking for saturation, drift, or intermittent connection issues. For the firmware branch, I'd examine whether the filtering algorithm could be producing the observed behavior with valid sensor inputs — for example, edge cases in the filter's state initialization, numerical overflow, or timing-dependent behavior.

The key is to design experiments that discriminate between the two hypotheses rather than arguments. For instance, if we can capture raw unfiltered sensor data alongside the filtered output, that immediately tells us whether the problem is upstream or downstream of the filter. If the raw data looks clean and the filtered output is wrong, it's a firmware issue. If the raw data itself is corrupted, it's a hardware issue.

I'd also make sure both teams are involved in defining the test criteria before we run the experiments, so that the results are accepted as conclusive regardless of which branch they point to. Once we have a confirmed root cause, I'd document the evidence trail carefully — in a medical device context, this becomes part of the corrective action record, and the reasoning needs to be defensible in a regulatory audit.

**Possible follow-ups:**
- What if the field data is insufficient to discriminate between the two hypotheses — how would you decide whether to pursue both corrective actions simultaneously or wait for more data?
- How would you ensure that the investigation doesn't stall while the two teams wait for each other to provide evidence?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** I'd approach this as a capability-building exercise rather than just a resource allocation problem. The first step is to understand what each engineer's current strengths are and what the new portfolio actually requires — not just in terms of technical skills, but in terms of how work gets structured across projects.

I'd start by mapping the portfolio's technical requirements against the team's current skill set. Some engineers will naturally adapt to working across projects; others will resist because they've built deep expertise in one area and see breadth as a threat to their value. I'd want to have honest conversations about this — not forcing everyone to become generalists, but finding ways to leverage deep expertise across multiple projects where it's actually applicable.

For the transition itself, I'd introduce a structured approach to knowledge sharing. This might include cross-training sessions where engineers present their domain expertise to the rest of the team, creating reusable design guidelines and checklists that capture the lessons from the single-product days, and pairing engineers from different specialties on early multi-project tasks so they learn by working together rather than by reading documentation.

I'd also think carefully about how to manage the transition period. Going from one project to multiple means engineers will need to context-switch, which is cognitively expensive. I'd want to establish clear priorities and boundaries — for example, protecting focused deep-work time for complex design tasks, while building in structured handoff points where engineers can shift between projects without losing track of where they are.

Finally, I'd make the case to senior management that this transition needs investment in tooling and process, not just reassignment of people. Multi-project work requires better documentation, more robust design reuse, and clearer interfaces between subsystems — all of which take time to build.

**Possible follow-ups:**
- How would you handle an engineer who is deeply specialized and resistant to working on projects outside their expertise?
- What metrics or indicators would you use to track whether the transition is succeeding?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** I'd approach this by recognizing that both teams are raising legitimate concerns, and the test strategy needs to address both the battery life benefit and the sensor stability risk. The first step is to define what "sensor stability during wake-up" actually means in measurable terms — settling time, voltage drift, noise floor, or some combination — and what the acceptable limits are for the device's clinical use case.

I'd structure the test strategy around three phases. First, characterization testing on the bench: measure the sensor output during wake-up transitions under controlled conditions, varying parameters like supply voltage, temperature, and time spent in sleep mode. This tells us whether there's actually a problem and what its boundaries are. Second, stress testing: push the device through worst-case scenarios — rapid sleep/wake cycles, low battery, extreme temperatures — to see if the instability compounds or triggers other issues. Third, long-duration testing: run the device through realistic usage patterns to verify that the battery life improvement is real and that the sensor stability issues don't appear intermittently over time.

I'd also want to design the test strategy to be diagnostic, not just pass/fail. If the sensor is unstable during wake-up, we need to know why — is it the power supply ramping, the sensor's internal settling, or interference from the digital circuitry waking up? So I'd include instrumentation hooks in the test setup: monitoring the supply rail, the sensor output, and the digital activity simultaneously so we can correlate events.

One important consideration is that the test strategy shouldn't just verify the new sleep mode works — it should also verify that it doesn't break anything else. The wake-up transition is a stress point for the whole system, so I'd include tests for communication integrity, data logging accuracy, and any safety-related functions that might be affected.

Finally, I'd make sure the test results are documented in a way that supports the design decision — whether that's proceeding with the sleep mode, modifying it, or abandoning it. In a medical device context, this becomes part of the design history file, and the rationale for the decision needs to be traceable.

**Possible follow-ups:**
- How would you handle a situation where the characterization testing shows the sensor instability is real but only occurs under conditions that are unlikely in normal use?
- What if the firmware team's battery life projections depend on a sleep mode duty cycle that the hardware team believes is unrealistic?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd start by making sure the review focuses on the requirements and constraints that drove the architect's choice, rather than letting it become a debate about architectural philosophy. The first question I'd ask is: what are the actual requirements that this architecture needs to satisfy? Things like processing load, real-time constraints, power budget, physical distribution of sensors and actuators, safety isolation requirements, and manufacturability.

Once the requirements are on the table, I'd ask the architect to walk through how the modular design addresses each one, and then ask the proponents of the single-processor approach to do the same. The goal is to get both sides to articulate their reasoning in terms of the requirements, not just their preferences. For example, if the device has sensors physically distributed across a large area, a modular design might reduce analog signal routing complexity — but if the processing load is modest, a single processor might be simpler and cheaper.

I'd also want to explore the specific concerns the senior engineers are raising. "Simpler and more reliable" is a reasonable position, but I'd push for specifics: what failure modes does the modular design introduce that the single-processor approach avoids? Conversely, what failure modes does the single-processor approach introduce that the modular design mitigates? In a medical device, safety isolation is often a key consideration — if one subsystem fails, can the others continue to operate? A modular design might provide better fault containment, but it also introduces communication failures as a new failure mode.

If the disagreement persists after the requirements-based discussion, I'd suggest a structured comparison: a trade-off matrix that scores each architecture against the requirements, with the scoring criteria agreed upon by both sides. This doesn't guarantee consensus, but it forces the discussion to be explicit about what matters and why.

Finally, I'd make sure the outcome of the review is documented — not just the decision, but the rationale, the alternatives considered, and the reasons for rejection. In a medical device context, this becomes part of the design history file, and future reviewers need to understand why this decision was made.

**Possible follow-ups:**
- What if the trade-off matrix shows the two architectures are roughly equivalent on most criteria, but the teams still disagree on the one or two criteria where they differ?
- How would you handle a situation where the architect's modular design is driven by a desire to reuse existing code or hardware from a previous project, rather than by the current project's requirements?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** I'd approach this by recognizing that the problem isn't really about the engineers who have concerns — it's about the environment that makes them hesitant to speak up. The first step is to examine how concerns are currently received. If a junior engineer raises a concern and gets dismissed or talked over, they'll learn quickly not to do it again. So the culture change has to start with how senior people respond to concerns, especially vague ones.

I'd establish a norm that any concern, no matter how preliminary, gets acknowledged and taken seriously. That doesn't mean every concern gets acted on — but it does mean the person raising it gets a genuine response: "That's interesting, can you tell me more about what's bothering you?" or "Let's think through that together." The goal is to separate the act of raising a concern from the outcome of the concern. Raising it should always be safe; acting on it should depend on the merit.

For the "gut feeling" case specifically, I'd encourage engineers to articulate the underlying worry as best they can — not as a fully formed technical argument, but as a question or a hypothesis. "I'm not sure why, but something about the power sequencing feels off" can be a starting point for investigation. I'd also model this behavior myself: when I have a vague concern about a design, I'd voice it openly and show that it's okay to not have all the answers.

I'd also build structured opportunities for raising concerns. Design reviews should have a dedicated time for open concerns, not just a walkthrough of the design. I'd consider anonymous channels if the team is large or if there's a history of people being dismissed. But ultimately, the goal is to make raising concerns a normal, expected part of the engineering process — not a brave act that requires courage.

Finally, I'd track how concerns are handled and follow up on them. If someone raises a concern and it turns out to be valid, I'd make sure they get credit for it. If it turns out to be unfounded, I'd make sure they don't get penalized for raising it. Over time, this builds the trust that makes the culture work.

**Possible follow-ups:**
- How would you handle a situation where an engineer repeatedly raises concerns that turn out to be unfounded, and the team starts to tune them out?
- What if the senior person whose decision is being questioned is defensive and takes concerns as a personal attack — how would you address that directly?