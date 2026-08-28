# behavioral-leadership — Day 38

## Q1: How would you approach managing a situation where a senior engineer on your team is technically excellent but consistently resists following the company's design documentation standards, arguing that the documentation is "busywork" that slows down real engineering?

**Answer:** I'd start by understanding the root of the resistance rather than treating it as a compliance problem. There's a meaningful difference between someone who doesn't see value in documentation and someone who finds the specific process burdensome. I'd have a one-on-one conversation to understand their perspective — maybe the templates are outdated, maybe the level of detail required doesn't match the project phase, or maybe they've had a bad experience where documentation was used punitively.

If the issue is that they don't see the value, I'd connect documentation to outcomes they do care about. For medical devices specifically, the design history file isn't administrative overhead — it's the evidence that the device is safe and effective, and it's what allows someone else to pick up the work without the original designer. I'd walk through a concrete example: what happens when a field issue requires tracing a design decision back to its rationale, and the documentation doesn't exist? That's not hypothetical in this industry.

If the issue is process friction, I'd work with them to improve the system. Maybe the documentation can be restructured, or some artifacts can be generated more efficiently from existing tools. The goal is to make compliance feel like engineering rather than paperwork.

I'd also be clear about the boundary: documentation is non-negotiable in regulated development, but how we get there can be flexible. I'd set expectations about what must be documented and when, and I'd follow up consistently. If the behavior continues after coaching, I'd escalate through performance management — but I'd want to exhaust the "make the process better" path first, because that often produces improvements that benefit the whole team.

**Possible follow-ups:**
- How would you handle it if the engineer's resistance is shared by several team members who see the documentation standards as excessive?
- What specific documentation artifacts would you consider non-negotiable for a Class II medical device, and which ones might be negotiable?

---

## Q2: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a battery management system fault or a charging circuit problem, and the two possible causes would require very different corrective actions?

**Answer:** I'd structure this as a systematic investigation rather than a debate between two hypotheses. The first step is containment — if there's any safety concern, the device should be flagged or recalled appropriately while we investigate. That's non-negotiable for medical devices.

Then I'd gather data before forming conclusions. I'd want to see the actual field returns, any logged data from the devices, charging behavior patterns, and environmental conditions at time of failure. I'd also want to understand the failure distribution — is it correlated with specific chargers, specific firmware versions, specific usage patterns? That data often narrows the problem space significantly.

I'd then design experiments that can discriminate between the two hypotheses. For example, if the battery management system is at fault, I'd expect to see certain voltage or temperature signatures during charging. If it's the charging circuit, I'd expect different signatures — perhaps related to input voltage regulation or charge current control. I'd also look at the interface between the two: the communication between the charger and the battery management system, since faults often live at boundaries rather than in one subsystem.

I'd use a structured framework like an Ishikawa diagram to map all potential causes within both subsystems, then prioritize based on evidence. The key is to avoid anchoring on one hypothesis too early. I'd document the investigation as it progresses so the reasoning is traceable — that's important both for regulatory purposes and for ensuring the corrective action actually addresses the root cause.

Once the root cause is identified, I'd implement containment, then corrective action, then verify effectiveness. I'd also review whether similar failure modes exist in other products or subsystems.

**Possible follow-ups:**
- How would you handle it if the data is inconclusive and you need to make a decision about whether to issue a field correction while the investigation continues?
- What specific test equipment or measurements would you use to discriminate between a battery management system fault and a charging circuit problem?

---

## Q3: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** I'd start by assessing the current state honestly: what skills exist, what the new portfolio demands, and where the gaps are. The transition from single-product to multi-project is as much a cultural shift as a technical one. Engineers who are used to deep specialization need to develop the ability to context-switch and to apply their expertise across different problem domains.

I'd structure the roadmap in phases. First, I'd identify the core competencies that are transferable across projects — things like mixed-signal design, firmware architecture, compliance knowledge, and design review practices. These are the foundation. Then I'd map which engineers have which strengths and where cross-training would be most valuable.

I'd also think about how to create cross-project learning opportunities without overwhelming anyone. Pairing engineers from different projects for design reviews, creating communities of practice around shared challenges (like power management or sensor integration), and rotating technical ownership of shared infrastructure are all ways to build flexibility gradually.

A key part of the roadmap is documentation and knowledge sharing. In a single-product environment, tribal knowledge can work. In a multi-project environment, it doesn't scale. I'd invest in making design rationale explicit — not just what was decided, but why — so that engineers can move between projects without needing to rediscover context.

I'd also be realistic about pacing. You can't transform a team overnight. I'd prioritize the cross-training that delivers the most value first, and I'd communicate the roadmap clearly so engineers understand why the change is happening and what's in it for them — broader skills, more career options, and more resilience for the team.

**Possible follow-ups:**
- How would you handle an engineer who is resistant to cross-training because they feel it dilutes their expertise in their core area?
- How would you measure whether the transition to multi-project flexibility is actually working?

---

## Q4: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** I'd approach this as a system-level problem rather than a firmware-versus-hardware disagreement. Both concerns are valid: the sleep mode extends battery life, which matters for usability and possibly for safety (a device that dies mid-use is a problem), but the wake-up transition is exactly where analog circuits are most vulnerable to noise and settling issues.

First, I'd define what "stable" means in measurable terms. What are the sensor accuracy requirements during and after wake-up? How long can the system tolerate settling time before readings are valid? What are the acceptable transient excursions? These specifications need to come from the clinical requirements, not from either team's preference.

Then I'd design a test strategy that specifically exercises the wake-up transition under realistic conditions. I'd want to characterize: the power supply ramp during wake-up, the analog sensor output during the transition, the time to reach specified accuracy, and any interaction with the battery's state of charge. I'd also test across temperature, since both battery behavior and analog settling are temperature-dependent.

I'd also think about the firmware-hardware interface. The firmware team needs to know what the hardware can guarantee during wake-up — for example, when it's safe to start taking valid readings. That might mean adding a hardware "settled" signal, or it might mean the firmware needs to wait a specified time before trusting sensor data. The test strategy should validate that this handshake is robust.

I'd also consider whether the sleep mode can be designed to reduce the wake-up stress — for example, keeping the analog front-end powered while sleeping the digital sections, or sequencing the wake-up so the power supply stabilizes before the sensor is enabled. These are design options that the test strategy can evaluate.

Finally, I'd make sure the test strategy includes both bench testing and system-level testing, because the interaction between the sleep mode and the rest of the system (wireless communication, user interface, other sensors) might reveal issues that component-level testing misses.

**Possible follow-ups:**
- How would you handle it if the test results show that the wake-up transition causes sensor readings to be out of specification for longer than the firmware team's timing budget allows?
- What specific measurements would you take to characterize the wake-up transient, and what equipment would you use?

---

## Q5: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd structure the review so that the discussion is about evidence and trade-offs rather than preferences. Both architectures have legitimate merits, and the right answer depends on the specific requirements of the device — not on which approach is more familiar or more fashionable.

First, I'd make sure the review package includes the system requirements that drive the architecture decision: processing load, real-time constraints, safety requirements, power budget, physical size, and the regulatory context. The architecture should be evaluated against these requirements, not against abstract notions of "simpler" or "more reliable."

I'd then facilitate a structured comparison. For the modular approach, the key questions are: what does the CAN-FD communication add in terms of latency and determinism? How does the team handle fault isolation between the microcontrollers? What's the additional complexity in firmware integration and testing? For the single-processor approach, the questions are: can the processor meet all the real-time requirements without resource contention? What happens if one subsystem has a fault — does it take down the whole system? How does the team handle the risk of a single point of failure?

I'd also push the discussion toward the specific failure modes that matter for a medical device. For example, if one function is safety-critical and another is non-critical, separating them onto different microcontrollers can provide fault containment. But that separation comes at the cost of communication complexity and potential for communication failures. The review should evaluate which failure modes are more likely and more severe for this specific device.

If the disagreement persists, I'd suggest prototyping or simulation to resolve the key uncertainties. For example, if the concern is whether the single processor can meet timing requirements, a proof-of-concept with the actual processing load would settle it. If the concern is CAN-FD reliability, a communication stress test would provide data.

Finally, I'd make sure the decision is documented with the rationale — not just the outcome, but the trade-offs considered and why the chosen approach won. That documentation is valuable both for regulatory purposes and for future engineers who will need to understand why the architecture looks the way it does.

**Possible follow-ups:**
- How would you handle it if the review reaches a stalemate and the team needs to make a decision to keep the project on schedule?
- What specific criteria would you use to determine whether the modular approach's fault containment benefits outweigh its communication complexity?