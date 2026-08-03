# behavioral-leadership — Day 13

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a firmware timing bug or a hardware power supply problem, and the two teams have already started blaming each other?

**Answer:** The first priority is to defuse the blame dynamic and refocus the team on the evidence. I would call a joint meeting with both teams and explicitly frame the goal as understanding the system behavior, not assigning fault. I'd propose a structured investigation using a fishbone diagram to map all plausible causes across firmware, hardware, power delivery, and environmental factors — this helps people see that the problem likely has multiple contributing factors rather than a single culprit.

For the technical approach, I'd want to separate the variables. I'd ask the firmware team to add instrumentation around timing-critical sections — logging timestamps for when interrupts fire, when the power management state changes, and when the fault occurs. Simultaneously, I'd ask the hardware team to capture power rail behavior with an oscilloscope, ideally synchronized with the firmware logs using a common trigger. The key is to determine whether the firmware timing issue only manifests under specific power conditions, or whether the power issue only causes problems when certain firmware paths are active.

I'd also establish a containment action early — if the device is in the field, that might mean a software patch to add more conservative timing margins or a hardware workaround, depending on which fix is faster to validate. The corrective action would come later, once the root cause is confirmed through controlled experiments. Throughout, I'd document everything in a shared investigation log so the reasoning is transparent and the final root-cause analysis is defensible.

**Possible follow-ups:** How would you handle it if one team refuses to participate in the joint investigation? What if the evidence points to a combination of both issues — how would you prioritize which to fix first?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** I'd start by assessing the current skill distribution and identifying which competencies are transferable across the new projects. The goal isn't to make everyone a generalist — it's to build a team where each person has a primary specialization plus enough breadth to contribute meaningfully to at least one other project area.

I'd structure the roadmap in three phases. First, a skills inventory and gap analysis: what does each project need, and where do current team members have adjacent skills that could be developed? Second, a deliberate cross-training plan — this could include pair rotations where an engineer works on a secondary project for a defined period, or "shadowing" a lead on a different project to learn the system architecture. Third, establishing shared infrastructure: common design guidelines, reusable hardware modules, and standardized documentation templates that reduce the cost of moving between projects.

A critical piece is managing the cultural shift. Engineers who are used to deep ownership of a single product may feel threatened by the transition. I'd be transparent about the rationale — that multi-project flexibility makes the team more resilient and creates more growth opportunities — and I'd ensure that specialization is still valued, not penalized. I'd also create a "community of practice" model where engineers with the same specialization across different projects meet regularly to share lessons learned, so the depth of knowledge isn't lost even as people work across more projects.

**Possible follow-ups:** How would you handle an engineer who strongly resists cross-training and wants to remain focused on their current product? How would you measure whether the transition is successful?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is fundamentally a system-level problem that requires both teams to understand the full wake-up sequence. I'd start by bringing both teams together to map the exact timing of the wake-up event — from the moment the processor exits sleep to the moment the sensor data is considered valid. The key question is: what is the settling time of the analog front-end, and does the firmware currently wait long enough before sampling?

I'd propose a test strategy that characterizes the wake-up transient across the full operating envelope: temperature extremes, battery voltage range, and different sleep durations. The hardware team would capture the analog sensor output and power rail behavior during wake-up using an oscilloscope, while the firmware team would instrument the code to log the exact timing of each step in the wake-up sequence. By overlaying the two, we can see whether the sensor is being sampled before it has settled.

I'd also design a stress test that exercises the worst-case scenario — for example, a very short sleep duration followed by a wake-up, repeated thousands of times, to catch any cumulative effects like capacitor drift or charge pump instability. If the hardware team's concern is valid, the fix might be a longer settling delay in firmware, a hardware change to reduce the settling time, or a combination of both. The test strategy should be designed to give both teams the data they need to make that decision objectively.

**Possible follow-ups:** What if the settling time varies significantly across different units due to component tolerance — how would you handle that? How would you decide whether the battery life benefit justifies the added complexity?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd structure the review to focus on the specific requirements that drive the architecture choice, rather than letting it become a debate about general preferences. The first question is: what are the actual constraints? For a medical device, I'd want to understand the safety architecture — does the modular design provide isolation between functions that need to be independently certified or fault-contained? Is there a regulatory reason to separate the control loop from the user interface?

I'd ask the architect to walk through the key scenarios that motivated the modular choice: what happens when one module fails — does the system degrade gracefully? What are the certification implications of each approach? I'd also ask the engineers who favor the single-processor approach to articulate their concerns concretely — is it about CAN-FD timing determinism, memory partitioning, or something else?

A useful technique is to create a decision matrix with weighted criteria: safety, reliability, development effort, certification risk, manufacturing cost, and future extensibility. Each team scores both architectures against the criteria, and the discussion focuses on where the scores diverge. If the disagreement persists, I'd propose a prototyping exercise — build a minimal proof-of-concept of the riskiest aspect of each architecture. For example, if the concern is CAN-FD timing, a prototype that demonstrates worst-case latency under full bus load would provide data rather than opinion.

Finally, I'd ensure the decision and its rationale are documented in the design history file, including the dissenting views and why they were or weren't adopted. This is important for regulatory defensibility and for future design reviews.

**Possible follow-ups:** What if the prototyping exercise is too expensive or time-consuming — how would you make the decision without it? How would you handle it if the architect is unwilling to consider alternatives?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** The foundation is psychological safety — engineers need to know that raising a concern will be met with curiosity, not defensiveness. I'd model this behavior myself by explicitly inviting challenges to my own decisions and responding to them with genuine engagement rather than justification. When someone raises a concern, even a vague one, I'd thank them and take it seriously, asking clarifying questions to help them articulate what's bothering them.

I'd also establish a norm that "gut feelings" are valid starting points for investigation. A concern doesn't need to be fully formed to be worth exploring — the expectation is that we'll investigate it together. I might say something like, "Let's spend 30 minutes looking at this — if it turns out to be nothing, we've still learned something." This lowers the barrier to speaking up.

Structurally, I'd create multiple channels for raising concerns: design reviews, but also one-on-one meetings, a shared technical risk log, and perhaps an anonymous channel if the team is large enough. The risk log is particularly useful because it normalizes the idea that concerns are tracked and addressed systematically, not dismissed or forgotten.

Finally, I'd make sure that when someone does raise a concern that leads to a design change, they get visible credit — not in a performative way, but by acknowledging the contribution in team meetings and in the design documentation. This reinforces the behavior and shows that speaking up has real impact.

**Possible follow-ups:** How would you handle a situation where an engineer repeatedly raises concerns that turn out to be unfounded — how do you keep the culture open without letting it become disruptive? What if the concern is raised anonymously and you can't follow up with the person directly?