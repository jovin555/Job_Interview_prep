# behavioral-leadership — Day 43

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a battery management system fault or a charging circuit problem, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a structured root-cause investigation rather than a debate between two hypotheses. The first step would be to gather all available evidence from the field — returned units, failure logs, charge/discharge cycle data, environmental conditions at time of failure — before any analysis begins. I'd want to avoid the trap of the team anchoring on whichever hypothesis seems more likely based on intuition.

Once evidence is collected, I'd map out what data would definitively differentiate between the two failure modes. For a battery management system fault versus a charging circuit problem, I'd look at things like: voltage and current profiles during charging, cell balancing behavior, temperature readings, and state-of-charge reporting accuracy. Each hypothesis makes different predictions about what those measurements should show. For example, a charging circuit problem might show abnormal voltage/current at the charging input, while a BMS fault might manifest as incorrect cell voltage readings or premature charge termination.

I'd also consider whether both could be contributing — sometimes what looks like an either/or is actually an interaction. The charging circuit might be stressing the BMS in a way that exposes a marginal design, or vice versa. The investigation should be designed to detect that possibility rather than assume mutual exclusivity.

From a process standpoint, I'd use a fishbone diagram to systematically capture all potential contributing factors across categories — components, firmware, environment, usage patterns, manufacturing — rather than just the two obvious candidates. This prevents premature narrowing. I'd also ensure containment actions are in place while the investigation proceeds, since this is a field issue affecting patient safety.

Finally, I'd document the investigation in a format that supports regulatory review — clear evidence chain, analysis methodology, conclusions, and verification of any corrective action. The corrective action itself would need to be verified as effective before closing the investigation, not just implemented and assumed to work.

**Possible follow-ups:** How would you structure the investigation timeline when patients are potentially affected and you need to balance speed with thoroughness? What would you do if the evidence equally supports both hypotheses even after targeted testing?

---

## Q2: How would you approach building a technical leadership roadmap for a team that is transitioning from a single-product medical device focus to a multi-project portfolio, where engineers are used to deep specialization rather than cross-project flexibility?

**Answer:** The core challenge here is shifting both mindset and structure — engineers who have spent years mastering one product's intricacies need to develop transferable skills and comfort with context-switching. I'd approach this in phases.

First, I'd assess what skills are genuinely transferable versus product-specific. Someone who has deep expertise in the analog front-end of one device likely has skills that apply to other sensor interfaces, even if the specific components differ. The goal isn't to make everyone a generalist, but to identify which specializations are portable and which need to be deliberately developed.

Second, I'd create a skills matrix mapping current team capabilities against the anticipated needs of the upcoming projects. This would highlight gaps early — for example, if one project requires significant wireless expertise and no one on the team has done RF design before, that's a hiring or training decision, not something to discover mid-project.

Third, I'd think about how to structure work assignments to build cross-project flexibility gradually. Rather than throwing someone into a completely unfamiliar domain, I'd look for adjacent assignments — perhaps pairing a specialist from one project with a specialist from another on a shared design task. This creates natural knowledge transfer without forcing anyone to work entirely outside their competence area.

I'd also need to address the documentation and knowledge-sharing infrastructure. Single-product teams often carry a lot of tribal knowledge. In a multi-project environment, that becomes unsustainable. I'd invest in design guidelines, reusable component libraries, and lessons-learned documentation that capture decisions and rationale in a way that's accessible across projects.

Finally, I'd be realistic about the transition timeline. People don't become cross-project flexible overnight, and forcing it too quickly creates risk — especially in medical devices where deep domain knowledge matters for safety. I'd phase the transition, perhaps starting with one pilot project that requires some cross-pollination, then expanding based on what works.

**Possible follow-ups:** How would you handle an engineer who is resistant to moving away from their area of deep expertise? How would you measure whether the transition is succeeding?

---

## Q3: How would you approach designing a test strategy for a battery-powered medical sensor device where the firmware team wants to add a new low-power sleep mode that significantly extends battery life, but the hardware team is concerned about the mode's effect on analog sensor stability during wake-up transitions?

**Answer:** This is fundamentally a question about characterizing a transient behavior that sits at the hardware-firmware boundary. I'd approach it by designing a test strategy that specifically targets the wake-up transition window, since that's where the risk lies.

First, I'd want to understand the failure mechanism the hardware team is worried about. When the device enters sleep mode, power rails may droop or become noisy as the regulator adjusts to lower load. On wake-up, there's typically a transient as the load suddenly increases — the supply voltage may dip, and analog reference circuits may take time to settle. If the firmware starts sampling the sensor immediately after wake-up, readings could be corrupted.

The test strategy would need to characterize three things: the settling time of the power rails after wake-up, the settling time of the analog front-end (including any reference voltages or bias circuits), and the firmware's actual sampling timing relative to wake-up. The key question is whether the firmware waits long enough for the analog chain to stabilize before taking measurements.

I'd design a test matrix that varies the sleep duration (since settling behavior may differ between short and long sleeps), the battery state of charge (since regulator behavior can change as the battery depletes), and temperature (since component settling times are temperature-dependent). I'd also test worst-case scenarios — for example, wake-up events that coincide with other activities like wireless transmissions or motor activation, which could add noise to the power rails.

The critical instrumentation would be a high-bandwidth oscilloscope capturing the power rail and analog output simultaneously with a digital signal indicating when the firmware starts sampling. This lets us directly measure the margin between analog settling and the first sample. I'd also want to capture data across multiple units, since component tolerances mean one unit's behavior may not represent the fleet.

If the testing reveals insufficient margin, the resolution could be firmware-side (adding a delay before sampling), hardware-side (adding decoupling or a reference buffer), or a combination. The test strategy should be designed to provide the data needed to make that decision objectively.

**Possible follow-ups:** How would you determine the acceptable settling time margin for a medical device? What would you do if the firmware team is resistant to adding a delay because it affects their timing budget?

---

## Q4: How would you approach leading a technical review of a proposed architecture for a new medical device where the system architect has chosen a modular design with multiple microcontrollers communicating over CAN-FD, but several senior engineers believe a single high-performance processor would be simpler and more reliable?

**Answer:** I'd approach this as a data-driven architecture decision, not a popularity contest. Both positions have merit, and the goal is to reach the best decision for this specific product, not to declare a winner.

First, I'd make sure the review focuses on the actual requirements and constraints rather than general preferences. What are the processing demands? Are there hard real-time requirements that could be compromised by sharing a single processor? What are the safety architecture requirements — does the device need independent channels for redundancy? What about power consumption, physical size, and thermal constraints? What's the expected production volume, and how does that affect the cost trade-off between one expensive processor versus several cheaper ones?

I'd ask the architect to walk through the key design drivers that led to the modular choice — perhaps there are isolation requirements, or different processing domains that need to be physically separated for safety reasons. Similarly, I'd ask the engineers advocating for the single-processor approach to articulate their concerns specifically: is it about reliability, complexity of inter-processor communication, development effort, or something else?

A useful technique is to turn the disagreement into a set of testable questions. For example, if the concern is that CAN-FD introduces latency or reliability risk, what are the actual timing requirements for the messages between the processors? Can those be quantified and evaluated against the CAN-FD capability? If the concern is development complexity, what's the team's actual experience with multi-processor systems versus high-performance single-processor designs?

I'd also consider whether a hybrid approach might address the core concerns of both sides — perhaps two processors rather than four, or a single processor with a separate safety monitor. The best answer might not be either of the two options on the table.

Finally, I'd ensure the decision gets documented with its rationale, including the alternatives considered and why they were rejected. This is especially important in medical devices, where the design history file needs to capture not just what was decided but why — and it prevents the same debate from recurring later when the original participants have moved on.

**Possible follow-ups:** How would you handle the situation if, after the review, the architect remains committed to their original design despite the concerns raised? What criteria would you use to decide whether to escalate the disagreement?

---

## Q5: How would you approach building a culture where engineers feel comfortable raising concerns about a design decision early, even when the decision was made by a senior person or a consensus of the team, and even when the concern is based on a "gut feeling" rather than a fully articulated technical argument?

**Answer:** This is about psychological safety combined with intellectual rigor — creating an environment where people can say "something about this doesn't feel right" without being dismissed, while also giving them a path to develop that intuition into something testable.

I'd start by modeling the behavior myself. When I have a concern that's not fully formed, I'd voice it openly and frame it as a hypothesis to explore rather than a conclusion. I'd also make a point of thanking people who raise concerns, especially when the concern turns out to be valid — and even when it doesn't, because the process of examining it often strengthens the design.

The key structural piece is creating a mechanism for capturing and tracking concerns. In design reviews, I'd explicitly allocate time for "concerns that aren't fully formed" — not just technical objections with data behind them. I'd want to normalize the idea that a gut feeling is often pattern recognition based on experience, and it deserves investigation even before the person can articulate exactly why something bothers them.

I'd also work on the response to concerns when they're raised. The worst thing a leader can do is dismiss a concern because the person can't immediately provide rigorous evidence. Instead, I'd help the person develop their concern into something testable — asking questions like "what specifically makes you uncomfortable?" or "what would need to be true for your concern to be valid?" This turns an amorphous feeling into a concrete question that can be investigated.

For concerns about decisions made by senior people, I'd establish a norm that decisions are always revisable when new information emerges — and that raising a concern isn't disrespectful, it's part of the engineering process. I'd also be careful about how senior people respond when their decisions are questioned. If a senior engineer reacts defensively, that sends a message to the whole team. I'd work with senior team members on receiving feedback gracefully.

Finally, I'd make sure that when concerns are raised and investigated, the outcome is communicated back to the team — whether the concern led to a change, was investigated and found not to be an issue, or is still being explored. This closes the loop and shows that raising concerns has an impact, which encourages future participation.

**Possible follow-ups:** How would you handle a situation where someone repeatedly raises concerns based on gut feelings that turn out to be unfounded, and the team starts to tune them out? How would you distinguish between a valuable intuitive concern and one that's based on bias or resistance to change?