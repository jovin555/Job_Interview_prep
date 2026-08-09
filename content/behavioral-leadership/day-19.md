# behavioral-leadership — Day 19

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a hardware design flaw or a firmware logic error, and the two teams have already started blaming each other?

**Answer:** The first priority is to neutralize the blame dynamic and redirect the teams toward a structured, evidence-based investigation. I would call a joint meeting with both teams and explicitly reset the framing: we're not looking for who to blame, we're looking for what the data says. I'd establish a shared timeline of the failure events and a common set of facts before any hypothesis gets defended.

From there, I would structure the investigation using a formal root-cause methodology — starting with containment to protect patients and limit field exposure, then moving into systematic data collection. I'd assign specific, non-overlapping data-gathering tasks to each team: the firmware team would instrument the code to log state transitions, timing, and error flags around the failure window; the hardware team would capture power supply behavior, signal integrity measurements, and environmental conditions. The key is that each team gathers data on their own domain without being asked to judge the other's.

I would also look for a discriminating experiment — something that would produce different outcomes depending on which hypothesis is true. For example, if the failure is timing-related, running the device with a modified clock configuration or adding deliberate delays might change the failure pattern. If it's a power integrity issue, the failure might correlate with specific load conditions or supply voltage variations. The experiment should be designed so that one hypothesis is either strongly supported or eliminated.

Throughout this, I'd keep the focus on the evidence trail. If the data eventually points to one side, the conversation shifts from blame to corrective action — and I'd make sure both teams participate in the fix, because in mixed-signal systems, the root cause is often an interaction between domains rather than a clean single-domain fault.

**Possible follow-ups:**
- How would you handle it if one team refuses to accept the evidence because they believe the test methodology is flawed?
- What would you do if the investigation reveals that both the hardware and firmware have contributing issues?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** The core challenge here is shifting from a "one team, one product" mindset to a "shared resources, multiple priorities" model. I would start by mapping the current skill sets against the anticipated needs of the new portfolio — not just at a high level, but at the level of specific competencies: who can do mixed-signal design, who owns firmware architecture, who understands the regulatory requirements for each product class.

The roadmap would have three parallel tracks. First, a **capability-building track**: identify the gaps between current skills and future needs, then create a structured cross-training plan. This might mean pairing engineers on different projects so they learn by exposure rather than by formal training alone. Second, a **process track**: establish lightweight, repeatable design and review processes that work across projects — shared design checklists, common documentation templates, and reusable verification approaches. This reduces the overhead of context-switching because engineers don't have to relearn processes for each project. Third, a **resource allocation track**: define how engineering capacity gets assigned across projects, including how to handle priority conflicts and how to protect deep-work time.

I would also be deliberate about managing the cultural shift. Engineers who are used to being the sole expert on a system may feel threatened by cross-project flexibility — they might worry that their depth is being diluted. I'd address this by framing cross-training as depth-plus-breadth: they're not losing their specialization, they're gaining the ability to contribute earlier in a project's lifecycle and to catch integration issues that only become visible when you understand multiple domains.

Finally, I'd build in regular portfolio-level reviews where engineers present their work to the broader team. This serves two purposes: it spreads knowledge organically, and it creates natural opportunities for engineers to see how their piece fits into the larger portfolio.

**Possible follow-ups:**
- How would you handle an engineer who resists cross-training because they believe it will dilute their expertise?
- What metrics would you use to track whether the transition is succeeding?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is a classic mixed-signal integration problem where the test strategy needs to bridge the gap between firmware behavior and analog performance. I would approach it by designing a test matrix that specifically targets the wake-up transition window — that's where the risk lives.

First, I'd define what "stable" means operationally. The hardware team needs to specify acceptable settling time, voltage ripple limits, and sensor output accuracy during and after the wake-up transition. Without those concrete thresholds, the test is subjective and the two teams will argue about whether a result is a pass or fail.

The test strategy would include several layers. **Characterization testing** would map the wake-up behavior across the full operating envelope: different battery voltages (from full charge to near cutoff), different temperatures, and different sleep durations. The concern is that a long sleep period might allow capacitors to discharge further, making the wake-up transient worse. **Stress testing** would push the worst-case scenarios — rapid wake-sleep cycling, wake-up during an active sensor reading, and wake-up when the battery is already low. **Long-duration soak testing** would catch issues that only appear after many cycles, such as gradual drift in the power supply or cumulative timing skew.

I would also recommend adding test instrumentation specifically for this transition — for example, a high-speed ADC capture of the sensor output synchronized with a firmware log of the wake-up sequence. This lets the teams correlate firmware timing with analog behavior, which is essential for diagnosing whether a failure is caused by the firmware sequence, the power supply response, or the sensor's own settling characteristics.

Finally, I'd make sure the test results are reviewed jointly by both teams, not just the team that owns the test. The goal is to build a shared understanding of the wake-up behavior, not to produce a pass/fail that one team can use against the other.

**Possible follow-ups:**
- How would you decide whether a wake-up transient that causes a brief sensor inaccuracy is acceptable for the device's intended use?
- What would you do if the characterization testing reveals that the sleep mode causes a subtle but consistent offset in the sensor readings that only appears after several wake cycles?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** The first step is to make sure the review is structured around objective criteria rather than personal preference. I would start by defining the evaluation framework: what does the system actually need in terms of processing performance, isolation between functions, power consumption, reliability, and regulatory risk? The architecture decision should be evaluated against those requirements, not against a general preference for simplicity or modularity.

I would ask the architect to present the modular design with explicit rationale for each decision — why multiple microcontrollers, why CAN-FD specifically, how the communication protocol handles failure modes, and what happens if one node fails. Then I'd ask the opposing engineers to articulate their concerns in the same structured way: what specific risks do they see, and what would they propose instead?

The key is to identify whether the disagreement is about facts or about values. If it's about facts — for example, whether CAN-FD can meet the latency requirements — then the review should include a data-gathering exercise, possibly a prototype or a simulation, to resolve the factual question. If it's about values — for example, whether modularity is worth the added complexity for easier future upgrades — then the discussion needs to be framed around the product requirements and the business context, not around engineering aesthetics.

I would also push the discussion toward the failure modes that matter for a medical device. A modular architecture has a real advantage in fault isolation: if one function fails, the others can continue operating. But that advantage only matters if the system is designed to handle partial failures gracefully. A single-processor design has fewer interconnects to fail, but a processor failure takes down everything. The question isn't which is simpler — it's which failure modes are acceptable for the intended use.

If the disagreement persists after the data is gathered, I would document both positions with their rationale and make a decision based on the evidence, with a clear record of why the decision was made. That documentation is critical for regulatory purposes — the design history file needs to show that the architecture decision was deliberate and justified.

**Possible follow-ups:**
- How would you handle it if the architect's modular design is more expensive to manufacture, but the architect argues it's safer because of fault isolation?
- What specific criteria would you use to decide whether the communication latency over CAN-FD is acceptable for a life-support device?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** The foundation of this culture is psychological safety — engineers need to know that raising a concern will not result in embarrassment, dismissal, or retaliation. But psychological safety alone isn't enough; you also need a process that gives those concerns a legitimate path into the decision-making flow.

I would start by modeling the behavior myself. When I have a concern about a design decision, I would voice it openly, even if I can't fully articulate why it bothers me. I'd say something like, "I have a nagging feeling about this approach, but I can't pin down the technical reason yet. Can we spend a few minutes exploring it?" This signals that it's acceptable to raise incomplete concerns.

I would also establish a norm that every concern gets a response — not necessarily agreement, but a genuine engagement. When someone raises a concern, the team's job is to either validate it, find evidence against it, or identify what additional information would resolve it. The concern should never just be dropped. This creates a culture where raising a concern is seen as contributing to the team's thinking, not as being difficult.

For the "gut feeling" cases specifically, I would encourage engineers to frame their concern as a question or a hypothesis rather than a definitive objection. "I'm worried that this approach might have an issue with X — can we check?" This lowers the bar for speaking up while still giving the team something concrete to investigate.

I would also make sure that design reviews and decision meetings explicitly include a "concerns" segment — a dedicated time where anyone can raise doubts, even if they can't fully articulate them. This institutionalizes the practice rather than relying on individual courage.

Finally, I would track how concerns are handled. If someone raises a concern that turns out to be valid, I would make sure that gets acknowledged publicly — not to embarrass the decision-makers, but to reinforce that raising concerns is valuable. If a concern turns out to be unfounded, I would make sure the person who raised it isn't made to feel foolish. The goal is to make raising concerns a neutral-to-positive behavior, not a risky one.

**Possible follow-ups:**
- How would you handle a situation where a junior engineer raises a concern that is technically incorrect, and a senior engineer responds dismissively?
- How would you distinguish between a genuine "gut feeling" that deserves investigation and a concern that is really just anxiety about change?