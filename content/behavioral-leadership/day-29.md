# behavioral-leadership — Day 29

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor hardware failure or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a data-collection problem rather than a debate between teams. The first step is to establish a clear containment action — for a medical device, that might mean issuing a field notice or restricting use until we understand the scope — while we gather evidence. I'd then structure the investigation using a formal methodology like 8D or a fishbone diagram, but the critical piece is defining what data would definitively distinguish between the two hypotheses before anyone starts pointing fingers.

For a sensor hardware failure versus a filtering algorithm error, the discriminating evidence would come from looking at the raw, unfiltered sensor data versus the processed output. If we can retrieve both from the field or reproduce the issue in the lab, we can compare: does the raw signal show the anomaly (suggesting hardware or physical sensing issues), or does the raw signal look clean while the filtered output is corrupted (suggesting algorithm error)? I'd also look at whether the failure correlates with environmental factors like temperature, vibration, or power supply events, which would lean toward hardware, versus whether it correlates with specific data patterns or timing, which would lean toward firmware.

I'd assign a small cross-functional team to work the problem jointly rather than in parallel silos, with a shared log of findings. The key is to document every piece of evidence against both hypotheses — not just the one you suspect — so that when a root cause is identified, the rationale is defensible in a regulatory context. Once we have a probable cause, we'd implement a corrective action and, importantly, design a verification test that proves the fix actually addresses the root cause rather than just masking symptoms.

**Possible follow-ups:** How would you handle it if the two teams disagree on what constitutes sufficient evidence to rule out their respective hypotheses? What would you do if the field data is incomplete and you can't retrieve the raw sensor data?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** I'd approach this as a change-management challenge as much as a technical one. The first step is to understand the current skill distribution and the demands of the upcoming portfolio — what projects are coming, what technical domains they span, and where the overlaps and gaps are. I'd map each engineer's strengths against the portfolio needs and identify where cross-training would have the highest leverage.

The key is to create a gradual transition rather than an abrupt one. I'd start by identifying shared building blocks across projects — common communication protocols, power management approaches, or compliance processes — and create internal standards or reference designs that engineers can contribute to and reuse. This gives specialists a way to contribute their deep knowledge to multiple projects without becoming generalists overnight.

I'd also establish a "lead engineer" model where each project has a technical lead, but engineers rotate through supporting roles on projects outside their primary specialty. For example, a firmware specialist might support hardware bring-up on a new project, not by writing firmware but by helping define test interfaces and debug strategies. This builds cross-project awareness without forcing people out of their competence zone.

Finally, I'd be explicit about the career development angle — helping engineers see that cross-project flexibility makes them more valuable and opens growth paths. I'd pair each engineer with a development plan that includes stretch assignments, paired work with colleagues in other specialties, and regular check-ins on progress. The goal isn't to make everyone a generalist; it's to build a team where specialists understand enough about adjacent domains to collaborate effectively across a portfolio.

**Possible follow-ups:** How would you handle an engineer who resists cross-training and wants to remain a deep specialist? How would you measure whether the transition is succeeding?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** I'd approach this as a risk-balancing problem that needs a test strategy designed to answer a specific question: does the wake-up transition from sleep mode introduce artifacts or instability in the analog sensor readings, and if so, under what conditions? The test strategy needs to characterize the behavior across the full operating envelope, not just the nominal case.

First, I'd define the specific failure modes we're concerned about — settling time after wake-up, reference voltage drift, power supply transients during the transition, and any coupling between the digital wake-up events and the analog front end. I'd then design a test matrix that varies the key parameters: sleep duration, wake-up trigger source, battery state of charge, temperature, and the timing between wake-up and the first sensor sample.

The critical test is to capture the analog sensor output continuously across the wake-up transition, with high time resolution, so we can see exactly what happens during the settling period. I'd also test with the actual firmware implementation, not a simplified version, because the timing of register writes and peripheral initialization can affect the analog behavior. We'd want to measure both the raw sensor signal and the processed output to understand whether any transient artifacts are being filtered or amplified by the firmware.

I'd also design the test strategy to include a margin assessment — if the sensor needs, say, 10 milliseconds to settle after wake-up, we need to know whether that's consistent across units, temperatures, and battery voltages, or whether it varies enough that we need to add margin to the firmware timing. The output of this testing should be a clear specification for the minimum wake-up-to-sample delay, validated across the operating range, plus any hardware changes needed to reduce settling time if the margin is too tight.

**Possible follow-ups:** How would you handle it if the test results show that the sleep mode causes unacceptable sensor instability, but the firmware team says the battery life requirement can't be met without it? What test equipment and measurement techniques would you use to capture the wake-up transient accurately?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd start by making sure the review is structured around objective criteria rather than preference or experience bias. Both architectures are viable in principle, so the question is which one better meets the specific requirements of this device — reliability, safety, power consumption, development risk, manufacturability, and long-term maintainability.

I'd ask the architect to present the modular design against a clear set of evaluation criteria, and I'd ask the opposing engineers to do the same for the single-processor approach. The key is to force the discussion into concrete trade-offs: What are the failure modes of each architecture? How does each handle a single-point failure? What are the power implications of multiple MCUs versus one high-performance processor? What's the development effort for CAN-FD communication versus shared memory or a single RTOS instance? How does each architecture affect the safety certification effort under IEC 60601?

I'd also push for data where possible. If there's uncertainty about processing load, we could do a preliminary analysis or a small proof-of-concept to measure actual CPU utilization and timing margins. If the concern is about CAN-FD reliability, we could look at the specific bit rates, bus loading, and error-handling requirements. The goal is to convert opinion-based disagreement into evidence-based decision-making.

If the disagreement persists after the technical analysis, I'd look at secondary factors: team familiarity with the technologies, the timeline, and the risk tolerance of the organization. A modular design might offer better fault isolation and upgradeability, but a single processor might be simpler to certify and debug. I'd document the decision with the rationale, the alternatives considered, and the trade-offs accepted — that documentation becomes part of the design history file and is valuable for future audits and for onboarding new team members.

**Possible follow-ups:** How would you handle it if the two sides remain deadlocked after the technical analysis, and the decision is blocking the project timeline? What criteria would you use to make the final call yourself?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** I'd start by modeling the behavior myself — explicitly inviting challenge on my own decisions and thanking people when they raise concerns, even if the concern turns out to be unfounded. The key is to separate the act of raising a concern from the validity of the concern itself. If people only get positive feedback when their concerns are correct, they'll stop raising them early.

I'd also establish a norm that "gut feelings" are legitimate starting points for investigation, not conclusions. When someone raises a concern based on intuition, the response should be: "That's worth looking into — let's figure out what data would confirm or refute it." This turns the concern into a productive inquiry rather than a challenge to authority. Over time, people learn to articulate their intuitions more clearly because they see that the follow-up is always a structured investigation, not a dismissal.

I'd also look at the structural incentives. If raising a concern late in a project is costly, people will hesitate to raise it early — so I'd make sure that early concerns are rewarded, even if they don't change the outcome. That might mean publicly acknowledging someone who raised a concern that led to a small design tweak, or giving credit in project reviews to people who identified risks early. I'd also make it clear that raising a concern is never penalized, even if the concern is ultimately deemed not valid — the behavior we want is vigilance, not certainty.

Finally, I'd work on the team's communication norms. In design reviews, I'd explicitly ask for dissenting views and create space for people who are less assertive. I might use techniques like having each engineer write down their concerns anonymously before the discussion, or going around the room to ensure everyone speaks. The goal is to make raising concerns a normal, expected part of the engineering process rather than an act of courage.

**Possible follow-ups:** How would you handle a situation where someone raises a concern that you believe is unfounded, and you have strong evidence to dismiss it — but you don't want to discourage them from raising concerns in the future? How would you distinguish between a healthy culture of challenge and a culture where decisions are constantly second-guessed and nothing gets done?