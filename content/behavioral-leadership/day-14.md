# behavioral-leadership — Day 14

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a hardware design flaw or a firmware logic error, and the two teams have already started blaming each other?

**Answer:** The first priority is to defuse the blame dynamic and refocus the team on the evidence. I would call a joint meeting with both teams and explicitly frame the goal as understanding the system behavior, not assigning fault. I'd propose a structured investigation using a fishbone diagram to map all plausible causal categories — hardware, firmware, mechanical, environmental, and usage-related — so that no hypothesis is dismissed prematurely.

From there, I'd establish a clear evidence-collection plan. For a hardware-vs-firmware question, I'd look for discriminating data points: does the failure correlate with temperature, supply voltage, or specific firmware build versions? Can we reproduce it on a test bench with instrumentation on both the power rails and the communication lines? I'd ask each team to prepare a short summary of why their area could or couldn't be the cause, based on data rather than intuition.

I would also make sure we have a containment action in place while the investigation runs — for a medical device, that might mean restricting use, adding a workaround, or increasing monitoring — so that patient safety isn't dependent on how long the root-cause analysis takes. Once the investigation converges on a likely cause, I'd verify the hypothesis with a controlled experiment before committing to a corrective action, and then document the entire reasoning chain in the design history file.

**Possible follow-ups:** How would you handle a situation where one team refuses to participate in the joint investigation? What specific instrumentation would you want on the bench setup to discriminate between hardware and firmware causes?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** I'd start by assessing the current skill distribution across the team and mapping it against the anticipated needs of the upcoming projects. The goal isn't to make everyone a generalist — it's to build enough cross-project flexibility that the team can absorb workload spikes without creating bottlenecks around single individuals.

I'd structure the roadmap in three phases. First, a short-term phase focused on identifying critical single points of failure: which engineers hold unique knowledge that no one else has, and which project tasks would stall if that person were unavailable. For those areas, I'd pair engineers for knowledge transfer on the most time-critical items.

Second, a medium-term phase where I'd introduce cross-training through structured mechanisms — design review participation across projects, shared component libraries, and rotating "secondary owner" assignments where an engineer shadows a colleague's work on a different project. The key is to make cross-training a scheduled activity, not something that happens opportunistically when someone has spare time.

Third, a longer-term phase where I'd standardize common practices across projects — design guidelines, review checklists, documentation templates — so that moving between projects doesn't require relearning processes. I'd also work with each engineer to understand their career interests and identify which cross-training opportunities align with their growth goals, because voluntary engagement is far more effective than mandated rotation.

Throughout, I'd track progress not by hours spent in training but by measurable outcomes: can an engineer now review a design outside their specialty? Can they take over a task from a colleague with minimal handoff time? The metric is capability, not activity.

**Possible follow-ups:** How would you handle an engineer who resists cross-training because they feel it dilutes their expertise? How would you balance cross-training time against the immediate demands of active project deadlines?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** I'd approach this as a system-level problem that requires both teams to define the acceptance criteria together before any testing begins. The first step is to agree on what "stable" means for the analog sensor output during wake-up — what settling time is acceptable, what voltage or measurement error is tolerable, and what the clinical implications are if the sensor reads incorrectly during that transition.

With those criteria defined, I'd design a test matrix that covers the full wake-up sequence: the transition from sleep to active, the power rail ramp behavior, the sensor reference settling, and the first valid data point. I'd want to test across the operating temperature range and battery voltage range, because both affect analog behavior and wake-up timing.

I'd also recommend instrumenting the device to capture both domains simultaneously — a logic analyzer on the firmware side to timestamp the wake-up sequence, and an oscilloscope on the analog side to capture the sensor output and power rails. That way, if a failure occurs, we can correlate exactly which firmware event corresponds to which analog anomaly.

The key design question is whether the sleep mode should wake the full system at once or use a staged wake-up — for example, powering the analog front end first, allowing it to settle, and then enabling the sensor read. That's a firmware-hardware co-design decision that should be made based on the test results, not on either team's preference. I'd structure the test plan to explicitly compare both approaches if feasible.

Finally, I'd make sure the test results feed back into the risk management file — if the wake-up transition introduces a period of potentially inaccurate readings, that needs to be documented as a hazard, with mitigations such as discarding the first N samples or delaying data transmission until stability is confirmed.

**Possible follow-ups:** What specific analog parameters would you measure during the wake-up transition? How would you decide whether the sleep mode is worth the added complexity and testing burden?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd start by making sure the review evaluates both architectures against the same criteria rather than debating which one is "better" in the abstract. The relevant criteria for a medical device include: reliability and failure modes, development risk, testability, power consumption, thermal management, regulatory documentation burden, and long-term maintainability.

I'd ask the architect to present the modular design with explicit rationale for the partitioning — what drove the decision to use multiple microcontrollers? Is it isolation of safety-critical functions, independent reset domains, or performance limitations of available single processors? Similarly, I'd ask the opposing engineers to articulate the specific risks they see in the modular approach — is it concern about CAN-FD timing determinism, increased board complexity, or higher failure probability due to more components?

Rather than trying to resolve the disagreement through discussion alone, I'd push toward a data-driven comparison. That might mean a rapid prototyping effort to validate the CAN-FD timing budget under worst-case load, or a failure modes analysis comparing the two architectures. For a medical device, the safety case is paramount — if one architecture makes the safety argument significantly simpler, that's a strong point in its favor.

I'd also consider the team's experience. If the team has deep expertise with single-processor designs and no CAN-FD experience, that's a real risk factor for the modular approach, regardless of its theoretical merits. The review should weigh not just technical elegance but the team's ability to execute and maintain the design over the product's lifetime.

If the disagreement persists after the data is gathered, I'd escalate to a formal decision with documented rationale — the goal is to make a defensible choice, not to achieve unanimous agreement.

**Possible follow-ups:** What specific data would you want from a prototyping effort to help resolve this disagreement? How would you handle a situation where the architect's design is chosen but the opposing engineers remain unconvinced and could undermine implementation?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** The foundation of this culture is psychological safety — engineers need to know that raising a concern will not result in embarrassment, dismissal, or retaliation. But psychological safety alone isn't enough; I'd also need to give engineers a structured way to voice concerns that lowers the barrier to speaking up.

I'd introduce a lightweight mechanism for capturing concerns — something like a "technical concern log" where anyone can raise an issue with a design decision, regardless of whether they have a fully formed argument. The log entry might be as simple as "I'm uncomfortable with the choice of X because of Y, but I can't fully articulate why." The key is that the concern is acknowledged and tracked, not dismissed. It doesn't automatically block the decision, but it triggers a review — either a quick discussion or a more formal analysis depending on the severity.

I'd also model the behavior myself. When I have a gut-level concern about a design, I'd voice it openly and show that it's acceptable to say "I don't have the data yet, but this bothers me." That sets the norm that concerns don't need to be fully formed to be valid.

In design reviews, I'd explicitly allocate time for "concerns without solutions" — a segment where the goal is to surface unease, not to solve problems. This prevents the dynamic where a concern is only raised if the person has a fully worked-out alternative, which disproportionately silences junior engineers.

Finally, I'd track whether concerns raised early actually lead to design changes or further investigation. If engineers see that raising a concern sometimes changes the outcome — or at least leads to a thoughtful response — they'll be more likely to speak up next time. If concerns are consistently dismissed without engagement, no amount of encouragement will build the culture.

**Possible follow-ups:** How would you handle a situation where an engineer repeatedly raises concerns that turn out to be unfounded, and the team starts to ignore their input? How would you distinguish between a legitimate gut feeling and an unproductive objection that's blocking progress?