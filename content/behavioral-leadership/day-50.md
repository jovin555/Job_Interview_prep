# behavioral-leadership — Day 50

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a battery management system fault or a charging circuit problem, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by establishing a structured investigation framework before any conclusions are drawn. The first step would be containment — ensuring patient safety by determining whether the device needs to be recalled, quarantined, or used with restrictions while the investigation proceeds. This is non-negotiable in medical devices.

Next, I'd assemble a small cross-functional team including hardware, firmware, and quality representatives, and clearly define the problem with objective evidence from the field reports. I'd then guide the team through a systematic root-cause analysis using tools like a fishbone diagram to map all potential contributors across categories — electrical, mechanical, firmware, environmental, and usage patterns.

For the specific battery-versus-charger question, I'd design a data-collection plan that discriminates between the two hypotheses. This might include: analyzing charge/discharge curves from returned units, examining fault logs if the firmware records battery events, measuring charging current and voltage at various states of charge, and checking for patterns in when failures occur — for example, do they happen during charging, after full charge, or during discharge? I'd also look at whether the issue correlates with specific charger firmware versions or hardware revisions.

The key is to avoid the trap of choosing between two hypotheses prematurely. I'd want the team to generate additional hypotheses beyond the initial two — for instance, could it be a connector contact issue, a thermistor reading problem affecting charge termination, or a firmware state-machine bug in the charging sequence? Often the real root cause is something neither team initially considered.

Once data points to a likely cause, I'd verify the hypothesis through controlled testing — reproducing the failure in the lab if possible — before committing to corrective action. The corrective action would then follow a formal change control process, with verification of effectiveness through extended testing and field monitoring.

**Possible follow-ups:**
- How would you handle it if the returned devices don't reproduce the issue in the lab?
- What criteria would you use to decide whether to issue a field safety notice while the investigation is still ongoing?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** I'd approach this as a structured transition that respects both the team's existing strengths and the new demands of a multi-project environment. The first step would be assessment — understanding each engineer's current skill set, their capacity for cross-training, and the technical requirements across the upcoming projects. I'd map the portfolio's needs against the team's capabilities to identify gaps and overlaps.

The roadmap would have several phases. In the near term, I'd focus on establishing shared infrastructure that reduces duplication — common design libraries, standardized schematic blocks, reusable firmware modules, and consistent documentation templates. This creates a foundation that makes it easier for engineers to move between projects because they're working with familiar building blocks.

For the medium term, I'd implement a deliberate cross-training program. Rather than simply assigning engineers to unfamiliar projects and hoping they learn, I'd pair them with specialists on a rotating basis — for example, having an engineer who typically owns power supply design work alongside a firmware engineer on a new project to understand the full system context. I'd also establish communities of practice within the team so that deep expertise isn't lost when someone shifts focus. The power supply expert might not own every power supply design anymore, but they'd review designs across all projects and mentor others.

I'd also need to address the cultural shift. Engineers who are used to being the sole authority on their specialty may feel threatened by having to share that space. I'd frame cross-project flexibility as career growth rather than dilution of expertise — the goal is T-shaped engineers who have deep specialization plus broad enough knowledge to contribute across projects.

Finally, I'd build in regular portfolio-level technical reviews where engineers present their project work to the whole team. This creates natural knowledge transfer and helps identify opportunities for reuse or shared problem-solving across projects.

**Possible follow-ups:**
- How would you handle an engineer who resists cross-training because they believe it dilutes their specialization?
- What metrics would you use to track whether the transition is successful?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** I'd approach this as a system-level engineering problem that requires both teams to understand each other's constraints rather than treating it as a firmware-versus-hardware dispute. The first step would be to define the actual requirements clearly — what does "significantly extends battery life" mean in measurable terms, and what are the sensor accuracy requirements during and after wake-up?

With those requirements established, I'd facilitate a technical session where the firmware team explains the proposed sleep mode architecture — what state the device enters, what remains powered, what the wake-up sequence looks like, and the expected timing. The hardware team would then explain their specific concerns: which analog components are affected, what settling times they expect, and what failure modes they're worried about.

The test strategy would need to address several layers. First, bench-level characterization testing to understand the actual behavior of the analog front-end during wake-up transitions — measuring settling times, noise levels, and reference voltage stability under controlled conditions. This data would tell us whether the hardware team's concerns are real and what margins exist.

Second, I'd design a test matrix that covers the full range of operating conditions — different battery voltages (including near end-of-life), temperature extremes, and various sensor configurations. The wake-up transition is likely to behave differently at low battery voltage or cold temperatures, so those edge cases need explicit coverage.

Third, I'd include long-duration cycling tests that exercise the sleep-wake transition thousands of times to catch intermittent issues that might not appear in single transitions. This is particularly important for medical devices where a sensor reading error during patient monitoring could have clinical consequences.

I'd also want to define clear pass/fail criteria upfront — what sensor accuracy is acceptable during the wake-up window, and how long after wake-up before the device must be producing valid data. If the hardware team's concerns are valid, the firmware may need to delay sensor readings until the analog front-end has stabilized, or the hardware may need additional decoupling or a cleaner power-switching scheme.

The key is that the test strategy should be designed to generate data that resolves the disagreement objectively, rather than letting either team's assumptions drive the decision.

**Possible follow-ups:**
- How would you handle it if the bench testing shows that the sensor doesn't stabilize quickly enough for the firmware's target wake-up time?
- What role would risk management (ISO 14971) play in this test strategy?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd start by framing the review as a decision-making exercise based on requirements and evidence, not as a debate to be won. The first step would be to ensure we have a clear statement of the system requirements — what the device needs to do, in what environments, with what performance constraints, and under what regulatory framework. Both architecture options should be evaluated against those requirements, not against personal preferences.

I'd then structure the review to systematically compare the two approaches across the dimensions that matter for this type of device. Key considerations would include: fault containment — in a medical device, can a failure in one subsystem be isolated so it doesn't take down the entire system? A modular architecture with multiple processors can provide better fault isolation if designed correctly, since a watchdog on one processor can potentially reset just that subsystem. But it also introduces new failure modes — inter-processor communication failures, synchronization issues, and more complex power sequencing.

Reliability is another critical dimension. A single high-performance processor simplifies the system in some ways — fewer components, simpler power architecture, no inter-processor communication to fail. But it also creates a single point of failure and concentrates all processing in one place, which may require more complex safety mechanisms to detect and handle failures.

I'd also consider development risk. Multiple microcontrollers communicating over CAN-FD is a well-understood architecture, but it introduces complexity in firmware development, debugging, and testing. A single processor might be simpler to develop for but could push the limits of what that processor can handle, creating performance risks.

Rather than letting the review become an abstract debate, I'd push for concrete evidence — processing load estimates, memory utilization projections, interrupt latency requirements, and safety analysis outcomes. If the team can't agree based on discussion alone, I'd propose a structured decision-making approach: perhaps a design spike or prototype to validate the riskiest assumptions of each architecture, or a formal trade study with weighted criteria.

If the disagreement persists after the analysis, I'd escalate to a documented decision with rationale — capturing both the chosen approach and the dissenting views, so that the decision can be revisited if new information emerges. In a medical device context, this documentation also serves the design history file and demonstrates that the decision was made through a rigorous process.

**Possible follow-ups:**
- What specific criteria would you weight most heavily in comparing the two architectures for a medical device?
- How would you handle it if the architect refuses to consider the alternative seriously?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** I'd approach this as a cultural change that requires both structural and behavioral interventions. The structural piece is about creating formal mechanisms for raising concerns that don't depend on individual courage. This might include a standing agenda item in design reviews where anyone can raise concerns without needing to frame them as fully-formed technical arguments, or an anonymous channel for raising issues that people might be uncomfortable voicing publicly.

The behavioral piece is about how leaders and senior engineers respond when concerns are raised. The most important thing is that raising a concern — even a vague one — is met with genuine engagement rather than dismissal or defensiveness. When someone says "I have a gut feeling something is wrong with this approach," the response should be to take it seriously and help them articulate what's driving that feeling. Often, a gut feeling is based on subtle patterns or past experiences that the person hasn't yet connected to specific technical evidence. The job of the leader is to help surface that underlying reasoning.

I'd also model this behavior myself. As a leader, I'd explicitly invite challenge to my own decisions and demonstrate that changing course based on new information is a sign of good engineering, not weakness. When I've made a decision and someone raises a concern, I'd thank them publicly, take time to genuinely consider their point, and if they're right, acknowledge it and adjust. If they're not right, I'd explain my reasoning clearly so they understand why the decision stands — but I'd never make them feel foolish for raising it.

Another important element is separating the idea from the person. In design reviews, I'd encourage language like "I have a concern about this approach" rather than "I disagree with your design." This shifts the focus to the technical issue rather than creating a personal conflict.

Finally, I'd recognize and reinforce the behavior when it happens. If a junior engineer raises a concern that leads to catching a real issue, that should be celebrated and highlighted as an example of the culture working. Over time, this creates a norm where raising concerns early is seen as responsible engineering practice rather than challenging authority.

**Possible follow-ups:**
- How would you handle a situation where an engineer repeatedly raises concerns that turn out to be unfounded, and the team starts to dismiss their input?
- What would you do if you raised a concern about a decision made by your own manager, and they dismissed it?