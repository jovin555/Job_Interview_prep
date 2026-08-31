# behavioral-leadership — Day 41

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a battery management system fault or a charging circuit problem, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a structured root-cause investigation rather than a debate between two hypotheses. The first step is containment — ensuring patient safety by determining whether the device needs to be recalled, quarantined, or issued a field safety notice while the investigation proceeds. That decision gets made with input from regulatory affairs and clinical stakeholders, not just engineering.

Once containment is in place, I'd assemble a small cross-functional team including hardware, firmware, and quality representatives. I'd begin by gathering all available evidence: field return data, device logs, battery voltage and temperature telemetry if available, charging cycle history, and any environmental factors reported by users. The key is to collect data before forming conclusions, because confirmation bias is a real risk when two plausible mechanisms exist.

I'd then map out a decision tree for each hypothesis. For the battery management system fault, what would the expected symptoms be — premature shutdown, capacity fade, voltage sag under load? For the charging circuit problem, what would we expect — overvoltage, undercharging, thermal events during charging? I'd compare the actual field data against these predicted signatures. Often the evidence will discriminate between the two even before any teardown.

If the data is inconclusive, I'd design targeted experiments. This might include bench testing returned units under controlled charging conditions, monitoring cell voltages during charge cycles, or using thermal imaging to identify hot spots. I'd also review the design history file for both subsystems — component selection, derating calculations, and any known issues from similar designs.

The critical discipline here is not to jump to a fix until the root cause is confirmed. In medical devices, the corrective action must be verified as effective, and the investigation must be documented in a way that would withstand regulatory scrutiny. I'd use an 8D framework to keep the process structured: containment, root cause analysis, corrective action, verification of effectiveness, and prevention of recurrence.

**Possible follow-ups:**
- How would you decide whether to issue a field safety notice while the investigation is still ongoing?
- What specific data would you want to collect from the field before deciding which subsystem to investigate first?

---

## Q2: How would you approach building a risk management culture on a medical device team that currently treats ISO 14971 documentation as a checkbox exercise done after the design is complete?

**Answer:** The core problem is that risk management has become an administrative afterthought rather than an engineering discipline. I'd approach this by reframing risk as a design input rather than a design output, and by making the connection between risk activities and engineering decisions visible and practical.

First, I'd look at how risk management is currently integrated into the development process. If the team is writing risk documents after the design is frozen, they're essentially reverse-engineering justification for decisions already made. I'd work to shift risk activities earlier — starting with a preliminary hazard analysis during concept development, and updating the risk management file at each design review rather than at the end.

To make this practical, I'd integrate risk thinking into existing engineering rituals. For example, at each design review, I'd require a brief risk assessment as part of the presentation — not a separate document, but a slide that asks: what new hazards does this design decision introduce, what's the severity and probability, and what mitigation is in place? This makes risk assessment a natural part of engineering discussion rather than a separate administrative task.

I'd also work to connect risk documentation to real engineering artifacts. The risk management file should reference specific design elements — schematics, layout decisions, firmware logic — and those design elements should reference back to the risk analysis. This traceability makes the documentation useful rather than ceremonial.

For the team culture itself, I'd look for opportunities to make risk thinking visible and valued. This might include celebrating engineers who identify potential hazards early, or using near-miss incidents as teaching moments rather than blame events. I'd also encourage engineers to bring "what if" questions to design reviews — what happens if this sensor drifts, if this connector fails, if this firmware path is executed out of order?

Finally, I'd work with quality and regulatory affairs to streamline the documentation process itself. If the forms are cumbersome or the process is overly bureaucratic, engineers will naturally treat it as a checkbox exercise. Making the process efficient and the documentation genuinely useful is part of the solution.

**Possible follow-ups:**
- How would you handle pushback from engineers who feel that risk documentation takes time away from actual design work?
- What specific changes would you make to the design review process to incorporate risk assessment without making reviews longer?

---

## Q3: How would you approach leading a design review for a medical device PCB when you discover, mid-review, that the layout engineer placed a high-speed digital trace directly under an analog sensor's reference voltage path, and the original designer is not present to explain their reasoning?

**Answer:** The first thing I'd do is pause the review and acknowledge what we've found without assigning blame. The absence of the original designer means we can't get context in real time, but that doesn't stop us from evaluating the design on its merits.

I'd start by asking the team to assess the actual risk rather than assuming the worst. The severity of a digital trace under an analog reference path depends on several factors: the switching frequency and slew rate of the digital signal, the impedance of the reference path, the sensitivity of the analog sensor, and the physical separation between the traces. A low-speed I2C line under a well-filtered reference might be benign, while a high-frequency clock under a high-impedance reference could be a real problem.

I'd want to look at the specific details: what layer is the digital trace on, what's the stack-up, is there a ground plane between them, what's the trace width and spacing, and what's the reference voltage source impedance? If the design has a solid ground plane between the layers and adequate decoupling on the reference, the coupling might be negligible. If the reference is high-impedance and poorly decoupled, even modest coupling could be problematic.

If we can't determine the risk from the layout alone, I'd recommend a targeted analysis. This could include a quick simulation of the coupling, or a bench test on a prototype if one exists. I'd also check whether the design has any margin — for example, is the reference voltage tolerance tight enough that a small noise injection would cause a problem, or is there headroom?

Regardless of the outcome, I'd document the finding in the review notes and flag it for follow-up. If the risk is real, the fix might be as simple as rerouting the trace, adding a ground guard trace, or improving the reference decoupling. If the risk is negligible, we still document the analysis so the decision is captured for future reviewers.

The broader lesson is about design review process. This is exactly why reviews should include a checklist that covers cross-domain interactions — digital noise coupling into analog circuits is a classic failure mode. I'd also note that the absence of the original designer highlights the importance of design documentation that captures rationale, not just the final layout.

**Possible follow-ups:**
- What specific measurements or simulations would you run to quantify the coupling risk?
- How would you handle the situation if the fix requires a layout revision that delays the project schedule?

---

## Q4: How would you approach managing a situation where a senior engineer on your team consistently delivers excellent technical work but has a pattern of dismissing questions from junior engineers during design reviews, saying things like "that's obvious" or "we don't need to discuss that"?

**Answer:** This is a situation where the technical quality of the work isn't the issue — the problem is the impact on team dynamics and the long-term health of the design review process. I'd approach it on two levels: addressing the immediate behavior and addressing the underlying culture.

First, I'd have a private conversation with the senior engineer. The goal isn't to reprimand but to understand their perspective and help them see the impact of their behavior. I'd frame it around the purpose of design reviews — they're not just validation of a design, they're a mechanism for catching problems early and developing the team. When a junior engineer asks a question, it might be because they don't understand something, but it might also be because they've spotted a genuine issue that the senior engineer has overlooked. Dismissing questions discourages people from speaking up, and in medical device development, that's a safety risk.

I'd also point out that the senior engineer's expertise is most valuable when it's used to teach, not to shut down discussion. A question that seems "obvious" to them might be a gap in someone else's understanding that, if left unaddressed, could lead to a mistake later. Taking two minutes to explain the reasoning builds the team's capability and reduces future errors.

If the behavior continues, I'd escalate the approach. This might mean setting explicit expectations for design review conduct — for example, a ground rule that all questions get a substantive response, or that the review chair ensures quieter team members have space to speak. I'd also model the behavior I want to see by asking questions myself, even when I think I know the answer, to normalize the idea that questions are welcome.

On the culture level, I'd work to make design reviews psychologically safe. This includes establishing norms where questions are valued, where "I don't know" is an acceptable answer, and where the goal is collective understanding rather than individual performance. Over time, this creates an environment where junior engineers feel empowered to raise concerns early — which is exactly what you want in medical device development.

**Possible follow-ups:**
- How would you handle the situation if the senior engineer becomes defensive during your conversation?
- What specific ground rules would you establish for design reviews to prevent this pattern from recurring?

---

## Q5: How would you approach building a cross-functional project timeline for a medical device when the hardware, firmware, and regulatory teams each have different estimates for how long their work will take, and there's no historical data from similar projects?

**Answer:** When there's no historical data and the teams have divergent estimates, the worst thing I could do is force a single number through negotiation or averaging. Instead, I'd approach this as an exercise in uncertainty management and dependency mapping.

First, I'd get the teams together to map out the actual dependencies between their work streams. Hardware can't be verified until firmware has basic drivers working; firmware can't be fully tested until hardware prototypes exist; regulatory documentation depends on both. Understanding these dependencies is more important than the individual estimates, because the critical path is what drives the timeline.

Once the dependencies are mapped, I'd ask each team to break their work down into smaller pieces and provide estimates with explicit confidence levels. Instead of "firmware will take 6 months," I'd ask for "the bootloader and driver bring-up will take 6-8 weeks, the application layer will take 8-12 weeks, and integration testing will take 4-6 weeks, but the integration testing estimate assumes the hardware is stable." This granularity reveals where the uncertainty actually lives.

I'd then build the timeline as a range rather than a single date. The project has an optimistic case, a most likely case, and a pessimistic case, and I'd present all three to stakeholders. The key is to be explicit about what drives the pessimistic case — for example, if the hardware team's estimate assumes a clean first prototype, but the firmware team's estimate assumes hardware revisions, that's a risk to flag.

I'd also identify where we can compress the timeline through parallel work or early risk retirement. For example, firmware development can start on development boards before the final hardware is ready. Regulatory documentation can be drafted in parallel with design work rather than after. These strategies reduce the critical path without requiring anyone to commit to an unrealistic estimate.

Finally, I'd build in checkpoints where we reassess the timeline based on actual progress. The estimate is a living document, not a commitment. At each milestone, we compare actual progress against the plan and update the forecast. This approach acknowledges uncertainty while still giving stakeholders a basis for planning.

**Possible follow-ups:**
- How would you present the range of estimates to executives who want a single committed delivery date?
- What specific strategies would you use to identify and retire the highest-risk unknowns early in the project?