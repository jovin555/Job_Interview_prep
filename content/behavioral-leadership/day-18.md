# behavioral-leadership — Day 18

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor calibration drift or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a structured root-cause investigation rather than a debate between hardware and firmware hypotheses. The first step is containment — ensuring patient safety isn't compromised while we investigate. That might mean issuing a field safety notice, restricting device use, or implementing a temporary workaround, depending on the severity.

For the investigation itself, I'd use an 8D or similar structured approach. The key is to gather data that discriminates between the two hypotheses before committing to either. I'd want to see the actual sensor readings versus what the firmware reported — if we have raw calibration data logged, we can determine whether the drift is real (sensor issue) or whether the raw data looks correct but the filtered output is wrong (algorithm issue). I'd also look at the calibration history across multiple devices to see if drift correlates with age, environmental conditions, or specific sensor batches.

I'd pull together a small cross-functional team — someone who understands the sensor's physical characteristics, someone who can review the firmware filtering code, and someone from quality or regulatory to ensure we're documenting properly. Rather than letting each side defend their hypothesis, I'd ask both teams to propose what data would prove their hypothesis wrong. That shifts the conversation from advocacy to investigation.

Once we identify the root cause, we need to verify it with targeted testing — for example, running the firmware algorithm against known-good sensor data to see if the error reproduces, or testing the sensor with a calibrated reference. Then we implement corrective action, which might include a firmware patch, a sensor qualification change, or both, and we verify effectiveness over time before closing the investigation.

**Possible follow-ups:** How would you handle it if the data is inconclusive and both hypotheses remain plausible? What documentation would you expect to produce from this investigation for the design history file?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** I'd approach this as a change management challenge as much as a technical one. The first step is understanding the current state — what each engineer's strengths are, what the new portfolio requires, and where the gaps are. I'd have individual conversations to understand career aspirations and comfort levels with different types of work, because a roadmap that ignores people's interests and anxieties won't be sustainable.

The roadmap itself would have three tracks: technical skills, process adaptation, and team structure. On the technical side, I'd identify which skills are transferable across projects — for example, mixed-signal design fundamentals apply whether you're working on a respiratory device or a monitoring system — and which are project-specific. I'd create a cross-training plan where engineers pair on each other's projects, not just to learn the technical content but to understand different regulatory requirements, different sensor types, and different design constraints.

On the process side, a multi-project portfolio requires more standardization than a single-product focus. I'd work with the team to develop reusable design guidelines, checklists, and templates that can be adapted across projects rather than reinvented each time. This reduces the cognitive load of switching contexts.

On team structure, I'd consider whether we need dedicated specialists who remain the "go-to" for certain domains, but with a broader bench of engineers who can support multiple projects. I'd also think about how to manage context-switching — perhaps grouping similar projects together or assigning engineers to a primary and secondary project rather than spreading them too thin.

Finally, I'd build in regular retrospectives to see what's working and adjust the roadmap. The transition won't be linear, and the team needs to feel that the plan is evolving based on their input, not being imposed from above.

**Possible follow-ups:** How would you handle an engineer who is deeply resistant to broadening their focus and wants to remain a specialist? How would you measure whether the transition is succeeding?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** I'd approach this by designing a test strategy that directly addresses the interface between the two concerns — the wake-up transition itself. The firmware team's low-power mode is only viable if the analog front-end can deliver stable, accurate readings within the required settling time after wake-up, and the hardware team's concern is legitimate because power supply transients during wake-up can couple into sensitive analog paths.

The test strategy would have several layers. First, characterization testing to understand the actual behavior — measuring supply voltage transients, sensor output settling time, and ADC readings during wake-up under various conditions (different battery voltages, temperatures, and sleep durations). This data tells us whether the concern is real and how much margin exists.

Second, I'd design targeted stress testing around the wake-up event itself — repeated wake-sleep cycles to check for cumulative effects, worst-case timing where the sensor is read immediately after wake-up, and scenarios where the wake-up coincides with other system events like communication or motor activity.

Third, I'd include verification testing that ties back to the device's requirements — does the sensor still meet accuracy specifications during the first few seconds after wake-up? This is where we'd define pass/fail criteria based on the clinical requirements, not just on what the hardware or firmware team thinks is acceptable.

I'd also want the test strategy to include some flexibility — perhaps a test fixture that allows us to inject noise or vary supply impedance to find the margin boundaries. This helps us understand not just whether it works, but how robust it is.

Finally, I'd document the test results in a way that supports the design decision — if the wake-up transition is problematic, we need data to decide whether to adjust the firmware timing, add hardware filtering, or change the power supply architecture.

**Possible follow-ups:** How would you decide whether the test results indicate a design change is needed versus accepting the current design with documented limitations? How would you involve both teams in defining the pass/fail criteria?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd start by making sure the review is structured around objective criteria rather than personal preferences. The first question isn't which architecture is "better" in the abstract — it's which one better meets the system requirements, including performance, reliability, power, cost, development timeline, and long-term maintainability.

I'd ask the architect to walk through the requirements that drove the modular choice — perhaps there are isolation requirements, physical separation constraints, or independent safety functions that benefit from separate processors. I'd also ask the engineers advocating for the single-processor approach to articulate what they see as the risks of the modular design — complexity, inter-processor communication failures, synchronization issues, or development overhead.

The key is to get both sides to be specific. Rather than debating architecture philosophy, I'd push for concrete questions: What happens when a CAN-FD message is lost? How does the system behave during partial failures? What's the worst-case latency for critical functions? What's the development effort for debugging across multiple processors versus a single one?

If the disagreement persists, I'd suggest a structured evaluation using a decision matrix with weighted criteria — things like reliability, safety certification effort, power consumption, cost, and team expertise. This doesn't automatically resolve the disagreement, but it makes the trade-offs visible and forces the discussion to be about priorities rather than preferences.

I might also suggest a prototyping exercise — build a minimal version of the critical communication path in the modular architecture and measure latency, reliability, and development effort. Data from a prototype is often more persuasive than architectural arguments.

Finally, I'd document the decision with rationale, including the alternatives considered and why they were rejected. This is important for the design history file, but it also ensures that if the architecture is questioned later, the reasoning is preserved.

**Possible follow-ups:** What if the disagreement is not resolvable through data because both architectures are viable and the choice comes down to team experience and risk tolerance? How would you handle the decision then?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** I'd approach this by recognizing that psychological safety is built through consistent behavior over time, not through a single policy or announcement. The first step is modeling the behavior myself — openly raising concerns about my own decisions, acknowledging when I'm uncertain, and explicitly inviting challenge from the team.

I'd also make it clear that concerns don't need to be fully formed arguments. A "gut feeling" is often pattern recognition based on experience, and it deserves a respectful hearing. The expectation isn't that every concern is valid — it's that every concern is taken seriously and explored. I'd encourage engineers to frame their concerns as questions: "I'm not sure why, but something about this doesn't sit right — can we walk through the failure modes?" This lowers the barrier to speaking up.

When someone does raise a concern, the response matters enormously. I'd make sure the person feels heard — acknowledging the concern, asking clarifying questions, and taking it seriously even if we ultimately decide not to act on it. If we do act on it, I'd make sure the person gets credit. If we don't, I'd explain why, so the person understands their input was considered.

I'd also work to normalize the idea that design decisions are hypotheses, not conclusions. A decision made today is based on the best information available, but new information or new perspectives should always be welcome. This framing makes it easier for people to raise concerns because they're not challenging a final verdict — they're contributing to an ongoing evaluation.

Finally, I'd watch for patterns — if certain people never speak up, or if concerns are only raised in private, that tells me the culture isn't working. I'd have individual conversations to understand what's holding people back and address those specific barriers.

**Possible follow-ups:** How would you handle a situation where someone raises a concern that you believe is unfounded, but you're not entirely certain? How would you ensure that raising concerns doesn't slow down decision-making to the point of paralysis?