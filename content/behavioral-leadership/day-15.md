# behavioral-leadership — Day 15

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a hardware design flaw or a firmware logic error, and the two teams have already started blaming each other?

**Answer:** The first priority is to reframe the conversation from blame to evidence. I would call a joint meeting with both teams and explicitly establish ground rules: we're investigating a system-level issue, not assigning fault, and the goal is to understand the failure mechanism before proposing any fix. I'd propose a structured investigation using a fishbone diagram to map all potential contributing factors across hardware, firmware, environment, and usage — this helps both teams see that the problem likely spans multiple domains rather than living entirely in one.

From there, I'd design a data collection plan that isolates variables. For example, if the issue is intermittent, I'd want to capture detailed logs with timestamps from the firmware alongside analog measurements from the hardware — ideally synchronized so we can correlate events. I'd ask each team to identify what evidence would definitively rule out their subsystem, and what evidence would implicate it. This forces both sides to think about testable hypotheses rather than defending positions.

I'd also ensure we document everything in a shared investigation log, including negative results, so we don't repeat experiments and so the reasoning is traceable later. If the investigation stalls, I'd consider bringing in an independent engineer from outside the project to review the evidence with fresh eyes. Throughout, I'd keep stakeholders informed of progress without overpromising a timeline, since root-cause investigations in complex systems are inherently unpredictable.

**Possible follow-ups:**
- How would you handle a situation where one team refuses to accept evidence that points to their subsystem?
- What criteria would you use to decide when to escalate the investigation to management?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** I'd start by assessing the current skill distribution across the team and mapping it against the anticipated needs of the upcoming projects. The goal isn't to make everyone a generalist — it's to build enough cross-training that the team can flex resources without losing deep expertise where it matters. I'd identify which skills are project-specific versus transferable, and where there are single points of failure (e.g., only one person who understands the power supply design or the wireless stack).

The roadmap would have three phases. First, a short-term stabilization phase where I ensure each active project has clear ownership and that critical knowledge is documented — this might mean pairing engineers on key tasks or creating design guidelines that capture tribal knowledge. Second, a medium-term cross-training phase where I deliberately assign engineers to adjacent areas — for example, having the firmware engineer participate in hardware design reviews, or having the analog engineer shadow the digital layout work. The goal is exposure, not mastery. Third, a longer-term phase where we establish reusable platforms and design patterns across projects, so that engineers aren't starting from scratch each time.

I'd also address the cultural aspect. Engineers who are used to deep specialization may feel threatened by the expectation to work outside their comfort zone. I'd frame cross-training as career growth rather than dilution of expertise, and I'd make it safe to ask questions in unfamiliar areas. I'd also be realistic about productivity — there's a learning curve, and I'd build that into project estimates rather than expecting the same throughput during the transition.

**Possible follow-ups:**
- How would you measure whether the cross-training is actually working?
- How would you handle an engineer who resists working outside their specialty?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** I'd approach this as a system-level trade-off that needs characterization data before making a decision. The first step would be to define what "stability" means operationally — for example, how long after wake-up does the analog sensor need to settle before readings are within specification, and what's the acceptable transient behavior during that window? Both teams need to agree on these criteria before we can evaluate the sleep mode.

Next, I'd design a characterization test that exercises the worst-case wake-up scenarios. This would include measuring the supply voltage rail during the transition, observing the sensor output during the settling period, and correlating any anomalies with firmware timing. I'd want to test across the full operating temperature range and battery voltage range, since both affect analog behavior. The key is to generate data that lets us make an informed decision rather than relying on intuition.

If the data shows the wake-up transient causes unacceptable sensor instability, I'd look at mitigation options: a staggered wake-up sequence where the analog front-end powers up before the sensor is sampled, a longer settling delay in firmware, or a hardware change like adding a small LDO or RC filter to smooth the supply transition. Each option has trade-offs in power consumption, complexity, and cost, and I'd document those trade-offs in a trade study.

Finally, I'd make sure the test strategy includes verification in the final system configuration, not just on the bench — because the interaction between firmware timing and analog behavior can be sensitive to layout, grounding, and other system-level factors. The decision should be data-driven, and the data should come from realistic conditions.

**Possible follow-ups:**
- What specific measurements would you take to characterize the wake-up transient?
- How would you handle a situation where the data is inconclusive and the schedule pressure is mounting?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd start by making sure the review is structured around objective criteria rather than personal preference. The key questions are: what are the system's actual requirements — processing load, real-time constraints, safety requirements, power budget, physical layout constraints, and regulatory considerations — and how does each architecture address them? I'd ask the architect to walk through the requirements traceability, showing how the modular design maps to each requirement, and I'd ask the skeptics to do the same for the single-processor approach.

I'd also push both sides to articulate their concerns in testable terms. For example, if the concern is that CAN-FD introduces latency or jitter, what's the actual timing budget for the critical control loop? If the concern is that a single processor creates a single point of failure, what's the safety analysis saying about failure modes? The goal is to move from opinion to analysis.

I'd consider whether a prototyping exercise would help resolve the key uncertainties. For example, if the main question is whether CAN-FD can meet the real-time requirements, a proof-of-concept with the actual communication stack on representative hardware would provide data. Similarly, if the concern is about the complexity of managing multiple firmware images and their interactions, a risk assessment of the development and maintenance burden would be valuable.

Finally, I'd ensure the decision is documented with rationale, including the alternatives considered and why they were rejected. This is especially important in a medical device context where the design history file needs to capture the reasoning. The decision should be made on evidence, not on who argues most persuasively.

**Possible follow-ups:**
- How would you handle a situation where the prototyping exercise is inconclusive?
- What criteria would you use to decide whether the modular architecture's added complexity is justified?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** I'd start by modeling the behavior myself — openly raising concerns about my own decisions and inviting challenge. If I make a design choice and then publicly ask the team to poke holes in it, that sets a tone that questioning is expected, not punished. I'd also make a point of thanking people who raise concerns, even when the concern turns out to be unfounded, because the act of raising it is valuable.

I'd also create structured opportunities for early input. For example, I'd introduce a lightweight "pre-review" step where the design is presented informally before the formal review, specifically to surface concerns while the design is still malleable. I'd also make it clear in team norms that a concern doesn't need to be fully formed — it's okay to say "something about this doesn't sit right" and then work together to articulate what's driving that feeling. Often the gut feeling is based on experience that hasn't been consciously processed yet.

I'd also address the power dynamics explicitly. If a senior person makes a decision, I'd encourage the team to treat it as a hypothesis to be tested, not a conclusion to be accepted. I'd ask the senior person to model receptiveness to challenge, and I'd intervene if I saw dismissive responses that shut down discussion. Over time, the goal is to make raising concerns feel like a normal part of engineering practice rather than an act of courage.

Finally, I'd make sure that concerns are tracked and addressed — if someone raises an issue and it's never acknowledged or resolved, they'll stop raising them. Even if the decision doesn't change, the person needs to understand why their concern was considered and set aside.

**Possible follow-ups:**
- How would you handle a situation where a junior engineer raises a concern that is technically incorrect, and a senior engineer responds dismissively?
- How would you balance encouraging early concerns with avoiding decision paralysis from endless debate?