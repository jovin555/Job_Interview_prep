# behavioral-leadership — Day 16

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a hardware design flaw or a firmware logic error, and the two teams have already started blaming each other?

**Answer:** The first priority is to reframe the conversation from blame to evidence. I would call a joint meeting with both teams and explicitly state that the goal is to understand the failure mechanism, not to assign fault. I'd propose a structured investigation using the 8D methodology, starting with establishing a cross-functional team that includes representatives from both hardware and firmware, plus quality and regulatory if needed.

The key is to define the problem precisely before diving into causes. I'd ask both teams to contribute to a detailed problem statement: what exactly fails, under what conditions, how often, and what the observable symptoms are. Then I'd guide the team through a fishbone diagram to map all potential causes across categories—design, manufacturing, environment, usage, and so on—rather than letting each team focus only on their own domain.

For the actual investigation, I'd look for ways to isolate variables. For example, if the issue is intermittent, I'd want to capture data from the field—logs, error codes, environmental conditions—to see if there's a pattern. I'd also consider whether there are existing test setups that could reproduce the issue in a controlled way. If the hardware team suspects noise on a bus, we could add probing points or use a logic analyzer; if the firmware team suspects a timing bug, we could add instrumentation or trace logging. The goal is to design experiments that would produce different outcomes depending on which hypothesis is correct.

Throughout this, I'd keep communication open and transparent. Each team should present their findings to the whole group, not just to me. This prevents siloed analysis and ensures that a finding from one team can be challenged or validated by the other. I'd also document everything—hypotheses, experiments, results, and decisions—because in a medical device context, this documentation will likely be needed for the design history file and potentially for regulatory reporting.

Finally, once the root cause is identified, I'd ensure the corrective action addresses the systemic issue, not just the immediate symptom. If it's a hardware issue, the fix might involve a design change, but we'd also need to verify whether the firmware could be more robust against that failure mode. If it's a firmware issue, we'd still want to consider whether the hardware design could be improved to reduce susceptibility. The investigation doesn't end with finding the cause; it ends with a verified corrective action and a plan to prevent recurrence.

**Possible follow-ups:**
- How would you handle the situation if one team refuses to accept the evidence pointing to their domain as the root cause?
- What would you do if the investigation reveals that the issue is actually caused by an interaction between hardware and firmware that neither team could have predicted independently?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** The transition from single-product to multi-project work is as much a cultural shift as a technical one. I'd start by understanding the current state: what projects are coming, what skills exist on the team, and where the gaps are. I'd map each engineer's strengths and interests against the anticipated project needs, but I'd be careful not to assume that deep specialization means someone can't grow into a broader role—it often just means they haven't had the opportunity.

The roadmap would have three parallel tracks. First, technical skill development: I'd identify cross-training opportunities where engineers can pair on tasks outside their specialty. For example, a firmware engineer might shadow a hardware engineer during a PCB layout review, or a hardware engineer might work with firmware on a bring-up task. The goal isn't to make everyone a generalist, but to build enough shared vocabulary that people can collaborate effectively across projects.

Second, process and tooling: multi-project work requires better documentation, reusable design blocks, and clearer handoff points. I'd work with the team to create standardized templates for design reviews, requirements traceability, and project status reporting. I'd also look for opportunities to create shared libraries or reference designs that can be reused across projects, which reduces the burden on individual engineers and makes cross-project work more efficient.

Third, leadership and ownership: in a single-product environment, there's often one clear technical lead. In a multi-project environment, you need multiple people who can own technical decisions for their project. I'd identify engineers who show potential for this and give them increasing responsibility—starting with leading a design review, then owning a subsystem, then owning a full project. I'd pair them with mentors and provide regular feedback.

I'd also be honest about the trade-offs. Multi-project work means less time for deep dives into any single problem, and some engineers will find that frustrating. I'd address this by ensuring that each project still has space for technical excellence—for example, by protecting time for proper design reviews and root-cause analysis rather than rushing to meet deadlines. The goal is to build a team that can flex across projects without losing the rigor that medical device development requires.

**Possible follow-ups:**
- How would you handle an engineer who is resistant to cross-training and wants to remain a deep specialist in their current area?
- How would you measure the success of this transition, both in terms of project outcomes and team development?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is a classic trade-off between power optimization and signal integrity, and the right answer depends on the specific application requirements. I'd start by clarifying the constraints: what is the required measurement accuracy during and immediately after wake-up, how quickly does the device need to take a valid reading, and what is the acceptable power budget?

With those constraints defined, I'd design a test strategy that specifically targets the wake-up transition. The key concern is that when the device enters and exits low-power mode, the power supply voltage may dip or ripple, and the analog front-end may need time to settle. I'd want to characterize this behavior empirically rather than relying on assumptions.

The test plan would include several layers. First, bench-level characterization: using a programmable power supply and an oscilloscope, I'd measure the supply voltage and the sensor output during wake-up transitions under various conditions—different battery voltages, different load conditions, different sleep durations. I'd also test with the actual sensor connected, not just a dummy load, because the sensor's own behavior during power-up can be unpredictable.

Second, I'd design a test matrix that covers the expected use cases. For example, if the device wakes up periodically to take a measurement, I'd test whether the measurement taken immediately after wake-up meets accuracy requirements, and if not, how long the device needs to settle before a valid reading can be taken. This might lead to a design change—for example, adding a settle delay before sampling, or keeping the analog front-end powered while only the digital section sleeps.

Third, I'd involve both teams in the testing. The firmware team would need to instrument the code to log wake-up events and timing, and the hardware team would need to verify that the power supply design can handle the transient load. I'd also want to test at temperature extremes, because both battery performance and analog settling time are temperature-dependent.

Finally, I'd document the results and the rationale for whatever design decision is made. If the sleep mode is approved, the test data becomes part of the design verification evidence. If it's not, the data shows why, and we can explore alternatives—for example, a less aggressive sleep mode or a hardware change to improve settling time. The key is that the decision is based on data, not on which team argues more persuasively.

**Possible follow-ups:**
- What specific measurements would you take to characterize the wake-up transient, and what would you consider acceptable performance?
- How would you handle a situation where the test results show that the sleep mode causes a brief but measurable degradation in sensor accuracy, and the product requirements don't specify whether that degradation is acceptable?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** The first step is to make sure the review is structured around objective criteria rather than personal preference. I'd define the evaluation criteria upfront: reliability, safety, power consumption, development risk, manufacturability, serviceability, and compliance with relevant standards. Each architecture should be assessed against these criteria, not just argued for or against.

I'd also want to understand the requirements that drove the architect's choice. A modular design with multiple microcontrollers might make sense if the device has physically distributed subsystems, if there are different safety integrity levels for different functions, or if the team has existing expertise in a particular microcontroller family. A single high-performance processor might make sense if the device is compact, if the processing demands are well within a single chip's capability, or if the team wants to minimize the number of components that could fail.

Rather than letting the debate be abstract, I'd push for a concrete comparison. I'd ask both sides to produce a simple trade-off matrix: for each criterion, how does each architecture score, and what evidence supports that score? For example, on reliability, the modular design might have more components that could fail, but it also provides fault isolation—if one microcontroller fails, the others might continue operating. On power consumption, multiple microcontrollers might use more power overall, but they might also allow more granular power management. On development risk, a single processor might be simpler to program, but a modular design might allow parallel development by different teams.

I'd also consider whether the two architectures could be partially combined. For example, could the device use a single high-performance processor for the main control loop but have a separate low-power microcontroller for safety-critical monitoring? This might capture the benefits of both approaches.

Finally, I'd ensure that the decision is documented with its rationale. If the modular design is chosen, the review record should capture why it was preferred over the simpler alternative, and what risks were identified and how they'll be mitigated. If the single-processor design is chosen, the record should capture why the modular approach was rejected. This documentation is important not just for the design history file, but also for future engineers who will wonder why the architecture looks the way it does.

**Possible follow-ups:**
- How would you handle a situation where the architect is unwilling to consider alternatives and insists that their design is the only viable option?
- What specific technical risks would you want to investigate further before making a final decision between the two architectures?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** Building this culture starts with how I respond when someone raises a concern, especially an early or vague one. The worst thing I could do is dismiss it or demand a fully formed argument before taking it seriously. Instead, I'd thank the person for raising it and treat it as a starting point for investigation, not a challenge to be defeated.

I'd also model this behavior myself. When I have a concern about a design, I'd voice it openly, even if I can't articulate exactly why it bothers me. This signals that it's acceptable to have incomplete thoughts and that the team's job is to explore them together, not to have all the answers upfront.

Structurally, I'd create explicit opportunities for this kind of input. Design reviews would include a dedicated time for "concerns and open questions" where anyone can raise an issue without needing to propose a solution. I'd also encourage engineers to bring concerns to me or to the team lead outside of formal reviews, and I'd make sure those concerns are tracked and addressed, not just acknowledged and forgotten.

When a concern is raised, I'd respond with curiosity rather than defensiveness. I'd ask questions to understand the concern better: "What specifically worries you about this approach?" or "What would need to be true for your concern to be valid?" This helps the person articulate their thinking and helps the team evaluate the concern on its merits.

I'd also be careful about how consensus is built. If a decision is made by consensus, I'd explicitly invite dissenting views before finalizing it, and I'd make it clear that changing your mind based on new information is a sign of good judgment, not weakness. After the decision is made, I'd still leave the door open for new concerns to be raised, because new information might change the picture.

Finally, I'd recognize and reinforce the behavior. When someone raises a concern that leads to a design improvement, I'd acknowledge their contribution publicly and explain how it helped. This creates a positive feedback loop where people see that speaking up is valued, not punished.

**Possible follow-ups:**
- How would you handle a situation where an engineer repeatedly raises concerns that turn out to be unfounded, and the team starts to tune them out?
- How would you balance the need for psychological safety with the need to make timely decisions and move forward?