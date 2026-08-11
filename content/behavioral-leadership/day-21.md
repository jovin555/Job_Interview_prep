# behavioral-leadership — Day 21

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor hardware failure or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by establishing a structured investigation framework before any conclusions are drawn, because the risk with this type of ambiguity is that teams anchor on the first plausible explanation and then look for confirming evidence. The first step would be to gather all available data from the field — device logs, error codes, timestamps, environmental conditions, and any user-reported symptoms — and lay it out chronologically. I'd then form a small cross-functional team with representation from both hardware and firmware, and explicitly frame the investigation as hypothesis-driven rather than blame-driven.

For the sensor hardware hypothesis, I'd look at whether the failure pattern correlates with environmental factors like temperature, mechanical stress, or power supply events, and whether the sensor's raw output (before filtering) shows characteristics consistent with a hardware fault — for example, saturated readings, open-circuit signatures, or intermittent dropouts. For the firmware hypothesis, I'd examine whether the filtering algorithm could produce the observed symptoms under specific input conditions — for instance, if the filter has a known edge case with rapid signal changes or if the issue correlates with specific firmware versions or configuration settings.

A key technique is to look for discriminating evidence — data points that would behave differently under each hypothesis. For example, if the device logs raw unfiltered sensor values alongside filtered values, comparing them can immediately narrow the search. If the raw signal looks clean but the filtered output is wrong, that points to firmware; if the raw signal itself is corrupted, that points to hardware. I'd also consider whether the issue can be reproduced in a controlled environment — either by simulating the sensor input in a test harness or by subjecting the hardware to the suspected stress conditions.

Once the evidence narrows the field, I'd design targeted experiments to confirm the root cause rather than just the most likely cause. This might include instrumenting a device with the suspect firmware but a known-good sensor, or vice versa. I'd document every step, including what was ruled out and why, so the investigation is auditable. Only after root cause is confirmed would I move to corrective action, and I'd ensure both containment (protecting patients in the field) and long-term corrective action (design change, process change, or both) are addressed separately.

**Possible follow-ups:**
- How would you handle the situation if the field data is insufficient to discriminate between the two hypotheses, and the team is under pressure to issue a field action quickly?
- What role would the risk management file (ISO 14971) play in deciding whether to issue a recall, a software update, or a hardware retrofit?

---

## Q2: How would you approach building a technical mentoring relationship with a junior engineer who is technically capable but tends to over-engineer solutions — adding unnecessary complexity, extra components, or overly elaborate firmware — when the project requires simple, robust, and manufacturable designs?

**Answer:** I'd start by understanding why they over-engineer, because the root cause matters. Often it comes from a place of wanting to demonstrate capability, or from a lack of experience with the constraints of real-world design — cost, manufacturability, testability, and long-term maintainability. Sometimes it's also a lack of confidence in the simple solution, so they add complexity as a safety net.

The first step would be to establish a shared framework for evaluating design choices. I'd introduce a simple question set: What problem does this feature solve? What happens if we remove it? What failure modes does it introduce? What does it cost in terms of board area, power, BOM cost, and test time? This shifts the conversation from "what can we add" to "what is the minimum required to meet the specification."

I'd also use design reviews as a teaching opportunity. Rather than just rejecting a complex solution, I'd walk through the trade-off analysis with them — comparing their approach against a simpler alternative on criteria like reliability, cost, and development time. The goal is to teach judgment, not just enforce a preference. I'd also give them small, real design tasks with tight constraints — for example, "design this interface with no more than three passive components" — so they build experience with constraint-driven design.

Another important element is helping them understand that simplicity is a feature in medical devices. Every additional component is a potential failure point, a potential compliance issue, and a potential supply chain risk. I'd share examples of how simple designs are often the most robust — for instance, a well-designed analog front end with careful layout can outperform a complex digital correction scheme. Over time, I'd expect them to internalize this mindset, but I'd also be patient — over-engineering often decreases as engineers gain experience with field failures and manufacturing realities.

**Possible follow-ups:**
- How would you handle it if the junior engineer's over-engineered solution actually passed all technical reviews, but you knew it would create long-term manufacturing or supply chain risk?
- What specific design review questions would you use to help the engineer evaluate whether a feature is truly necessary?

---

## Q3: How would you approach leading a design review for a medical device PCB when you discover, mid-review, that a critical safety-related trace width calculation was never documented, and the original designer is no longer with the company?

**Answer:** The immediate priority is to determine whether the design is safe, not to assign blame. I'd pause the review on that specific item and treat it as a formal non-conformance — the trace width calculation is a safety-critical parameter, and the absence of documentation means the design cannot be verified as meeting its requirements. I would not allow the review to proceed as if the design were complete.

The first step would be to check whether the calculation can be reconstructed from available evidence. The trace width for a safety-related current path is typically determined by the maximum fault current, the allowable temperature rise, the copper weight, and the ambient temperature range. If the schematic and layout are available, I can calculate the required trace width from first principles using the IPC-2221 or IPC-2152 standards, and then compare it against what was actually implemented. I'd also check whether the design files contain any notes, constraints, or simulation results that might have captured the rationale indirectly.

If the reconstructed calculation shows the trace is adequate, I'd document the calculation, have it independently verified by a second engineer, and add it to the design history file as a formal record. If the calculation shows the trace is inadequate, that's a critical finding — the design cannot proceed without a change, and the change would need to go through the full change control process, including risk assessment and potentially re-verification.

I'd also use this as a trigger to review the design documentation process. The fact that a safety-critical calculation was undocumented suggests a systemic gap — perhaps the design review checklist didn't require documentation of calculations, or the original designer didn't have a clear standard for what needed to be recorded. I'd work with the team to update the design review checklist and documentation standards so this type of gap is caught earlier in the process, ideally before the design reaches a formal review.

**Possible follow-ups:**
- How would you handle the situation if the reconstructed calculation shows the trace is marginal — within tolerance but with no margin for manufacturing variation?
- What would you do if the design review checklist itself didn't require trace width calculations to be documented, and the team saw this as a one-off oversight rather than a systemic issue?

---

## Q4: How would you approach managing a situation where two senior engineers on your team have a fundamental disagreement about whether to use a hardware-based watchdog timer or a software watchdog with a separate supervisory IC for a life-support medical device, and the decision is blocking the project timeline?

**Answer:** I'd first make sure both engineers feel heard, because in a high-stakes safety-critical decision, a rushed or dismissive process will undermine trust and could lead to a poor technical outcome. I'd set up a structured technical debate where each engineer presents their position with specific evidence — not just preference — covering reliability, failure modes, compliance implications, and implementation complexity.

For the hardware watchdog argument, the key points would typically be: it operates independently of the main processor, so it can detect a hung processor even if the software is completely non-functional; it has a simpler failure mode analysis; and it's easier to verify during compliance testing. For the software watchdog with a supervisory IC, the arguments would typically be: it can monitor more than just a heartbeat — it can check that specific tasks are completing within their deadlines; it can be updated in firmware if the timing requirements change; and it may reduce BOM cost and board space.

I'd then push both engineers to address the specific requirements of a life-support device. The critical question is: what happens when the main processor hangs? A hardware watchdog will reset the system, but if the reset doesn't restore safe operation, it's not sufficient. A software watchdog can detect a hung task and potentially put the system into a safe state, but it depends on the processor still being able to execute code. The real question is whether the device needs a fail-safe state that can be reached without the main processor functioning at all — in which case, hardware-based monitoring of critical outputs might be necessary regardless of the watchdog choice.

I'd also bring in the compliance perspective. IEC 60601 requires that single-fault conditions not lead to unacceptable risk. The watchdog choice affects how the system behaves under a processor failure, so the decision needs to be tied to the risk analysis. I'd ask the team to map out the failure scenarios and show how each watchdog approach addresses them. If the hardware watchdog is sufficient for all identified failure modes, it may be the simpler choice. If there are failure modes that require software intervention, a hybrid approach — hardware watchdog for processor hang, software monitoring for task-level failures — might be the right answer.

If the disagreement persists after a structured technical debate, I'd consider prototyping or simulation to resolve the key uncertainty. For example, if the concern is whether the software watchdog can reliably detect a hung task within the required time, a simple test on the actual hardware could settle it. I'd also document the decision with rationale, including the dissenting view, so that the reasoning is preserved for future audits. Ultimately, the decision needs to be made based on the risk analysis and the specific requirements of the device, not on which engineer is more persuasive.

**Possible follow-ups:**
- How would you handle it if one engineer's preferred approach is more expensive and complex, but they argue it's safer, while the other engineer argues the simpler approach is actually more reliable because it has fewer failure modes?
- What role would the device's risk management file play in resolving this disagreement, and how would you ensure the final decision is traceable to specific risk analysis outputs?

---

## Q5: How would you approach building a culture of structured root-cause analysis on a team that currently treats investigations as a quick fix-and-move-on exercise, without documenting the analysis or verifying that the fix actually addresses the root cause?

**Answer:** I'd start by understanding why the team behaves this way. Often it's a combination of time pressure, a belief that the fix is obvious, and a lack of consequences for recurring issues. The key is to make structured root-cause analysis feel like a tool that saves time in the long run, not an administrative burden.

The first step would be to introduce a lightweight, standardized process that doesn't feel like bureaucracy. A simple template with five sections — problem description, immediate containment, root cause analysis (using 5 Whys or a fishbone diagram), corrective action, and verification of effectiveness — can be completed in a short meeting if the team is disciplined. I'd emphasize that the goal is not to produce a perfect document but to ensure the team actually thinks through the problem before jumping to a fix.

I'd also model the behavior myself. When I lead an investigation, I'd walk through the structured process openly — showing how I separate containment from corrective action, how I use the 5 Whys to dig past the obvious cause, and how I verify that the fix actually works before closing the issue. This demonstrates that the process is practical, not theoretical.

A critical element is verification of effectiveness. The team likely skips this step because it requires waiting and observing, which feels like wasted time. I'd make it a non-negotiable part of the process — a fix is not complete until we've confirmed it works under the conditions that caused the original failure. This might mean running a test, monitoring the system for a period, or simulating the failure condition. I'd also track recurring issues — if the same problem comes back, that's a signal that the root cause analysis was incomplete or the fix was ineffective.

Finally, I'd connect the process to outcomes the team cares about. If a structured investigation prevents a recurring issue from eating up engineering time, or prevents a field failure that would require a recall, that's a tangible win. I'd celebrate those wins publicly and use them as examples of why the process is worth the effort. Over time, the goal is for structured root-cause analysis to become the default behavior, not something that requires enforcement.

**Possible follow-ups:**
- How would you handle a situation where a senior engineer resists the structured process, arguing that they already know the root cause and the documentation is a waste of time?
- What metrics or indicators would you use to track whether the team is actually adopting the structured approach, rather than just going through the motions?