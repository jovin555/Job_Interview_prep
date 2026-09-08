# behavioral-leadership — Day 49

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a battery management system fault or a charging circuit problem, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a structured root-cause investigation rather than a debate between two hypotheses. The first step would be to establish a clear containment action to protect patients and users while the investigation proceeds — for example, issuing guidance on charging practices or usage limitations if warranted by the risk assessment. Then I'd assemble a small cross-functional team including whoever owns the battery management firmware, the analog hardware engineer responsible for the charging path, and someone from quality or regulatory to ensure the investigation stays aligned with ISO 14971 risk management expectations.

The key is to gather data systematically before committing to either hypothesis. I'd want to see field-returned units, charging logs if the device captures them, and any telemetry from the battery management system. I'd also review the design documentation for both subsystems — the charging circuit's current/voltage limits, protection features, and the battery management system's monitoring thresholds. A fishbone diagram can help map all potential contributing factors across both subsystems: component stress, firmware state-machine edge cases, environmental factors like temperature during charging, and user behavior patterns.

Rather than asking which team is right, I'd push for evidence that discriminates between the two hypotheses. For instance, if the failure correlates with specific charger models or charging conditions, that points toward the charging circuit. If it correlates with battery age or state-of-charge patterns, that points toward the battery management system. I'd also look for any common-mode causes — something like a marginal connector or ground bounce issue could manifest as symptoms in both subsystems.

Once the evidence points in a direction, I'd verify the root cause through targeted testing — reproducing the failure under controlled conditions if possible. Only after confirming the actual failure mechanism would we move to corrective action, which might include a hardware change, a firmware patch, or both. Throughout this process, I'd document everything in the design history file, including the rationale for ruling out the alternative hypothesis, because that traceability is essential for regulatory compliance and for preventing similar issues in future designs.

**Possible follow-ups:**
- How would you handle pressure from management to implement a fix quickly before the root cause is confirmed?
- What specific data would you want to collect from field-returned units to discriminate between these two failure modes?

---

## Q2: How would you approach building a risk management culture on a medical device team that currently treats ISO 14971 documentation as a checkbox exercise done after the design is complete?

**Answer:** The core problem is that risk management has become an administrative afterthought rather than an engineering discipline that informs design decisions. I'd approach this as a cultural change that requires both structural and behavioral shifts.

Structurally, I'd integrate risk management activities into the existing engineering workflow rather than bolting them on at milestones. That means risk analysis should start during concept development — even a preliminary hazard identification at the requirements stage — and continue iteratively as the design evolves. I'd work with the team to establish a rhythm where risk review is a standing agenda item at design reviews, not a separate activity. The goal is to make risk thinking part of how engineers naturally evaluate design options: "What happens if this component fails? What if the firmware hangs? What if the user does something unexpected?"

Behaviorally, I'd focus on making the connection between risk documentation and engineering value visible. Many engineers see ISO 14971 paperwork as bureaucracy because they don't see how it improves the product. I'd show them concrete examples — perhaps from past projects — where early risk identification caught a real hazard that would have been expensive to fix later. I'd also emphasize that the risk file is a living engineering document: when a design changes, the risk analysis should be updated to reflect new hazards or changed risk levels, and that update should inform whether additional mitigation is needed.

I'd also involve engineers directly in risk activities rather than having a dedicated risk manager do it for them. When engineers facilitate their own hazard identification sessions or lead the DFMEA for their subsystem, they develop ownership and a deeper understanding of the process. I'd pair this with training that focuses on the reasoning behind the methodology — how risk control measures relate to actual patient safety — rather than just the mechanics of filling out the forms.

Finally, I'd make sure that risk management outputs actually feed back into design decisions. When a risk assessment identifies a hazard that requires mitigation, that mitigation should appear as a design requirement with traceability. When engineers see their risk analysis leading to concrete design changes, they'll understand that this isn't checkbox compliance — it's good engineering practice that happens to satisfy regulatory requirements.

**Possible follow-ups:**
- How would you handle pushback from engineers who argue that risk documentation takes time away from actual design work?
- How would you measure whether the risk management culture has actually improved?

---

## Q3: How would you approach leading a design review for a medical device PCB when you discover, mid-review, that the layout engineer placed a high-speed digital trace directly under an analog sensor's reference voltage path, and the original designer is not present to explain their reasoning?

**Answer:** This is a situation where I need to balance several priorities: keeping the review productive, not making assumptions about the designer's intent, and ensuring the design is actually sound before it moves forward.

First, I'd acknowledge the finding and flag it as a discussion item rather than immediately declaring it a defect. There are scenarios where such a placement might be acceptable — for example, if there's a solid ground plane between the digital trace and the analog reference path, or if the digital signal is low-speed enough that coupling is negligible. Without the designer present to explain their reasoning, I'd note the concern and ensure it's tracked as an action item requiring either justification or modification.

I'd then guide the review to examine the specific coupling mechanisms. What's the rise time of the digital signal? What's the impedance of the reference voltage path? Is there adequate decoupling on the analog reference? Are there guard traces or ground pours providing isolation? These are the technical questions that determine whether the placement is actually problematic. I'd also look at the broader layout context — sometimes a trace placement that looks wrong in isolation is actually the best option given other constraints, like keeping the analog section away from a noisy switching regulator or maintaining a clean return path.

If the review team concludes the placement is likely problematic, I'd recommend a targeted simulation or bench test to quantify the coupling before committing to a layout change. A quick SPICE simulation of the coupling path, or a prototype measurement if a board exists, would give data rather than speculation. If a change is needed, I'd ensure the action item is assigned with a clear owner and a follow-up review to verify the fix.

The deeper lesson here is about review process. This situation highlights why design reviews should include the original designer and why layout decisions should be documented with rationale. I'd use this as an opportunity to discuss whether the team's review checklist adequately covers mixed-signal layout concerns like analog/digital separation, and whether we need better documentation of layout trade-offs.

**Possible follow-ups:**
- What specific measurements or simulations would you run to determine if the coupling is actually a problem?
- How would you handle the situation if the layout change would delay the project schedule significantly?

---

## Q4: How would you approach managing a situation where a senior engineer on your team consistently delivers excellent technical work but has a pattern of dismissing questions from junior engineers during design reviews, saying things like "that's obvious" or "we don't need to discuss that"?

**Answer:** This is a leadership challenge that requires addressing both the behavior and its impact on the team. The technical work is excellent, but the dismissive behavior undermines the design review process and discourages junior engineers from raising concerns — which is particularly dangerous in medical device development where a question not asked could lead to a missed hazard.

I'd start with a private conversation with the senior engineer. The goal isn't to criticize their technical judgment but to help them see the impact of their communication style. I'd frame it around the purpose of design reviews: they exist to surface concerns and catch problems early, and that only works if everyone feels safe asking questions. A junior engineer's question might seem obvious to someone with years of experience, but the question itself might reveal a gap in the documentation or a misunderstanding that others share. I'd also point out that dismissing questions discourages future questions — and the team loses the benefit of fresh perspectives.

I'd also model the behavior I want to see. During reviews, I'd explicitly welcome questions from all team members and demonstrate how to respond constructively — even to questions that seem basic. When a junior engineer asks something, I'd take it seriously, answer it thoroughly, and thank them for raising it. This sets a norm that questions are valued.

For the senior engineer specifically, I might suggest they try a different framing when they think a question is obvious: instead of "that's obvious," something like "let me explain the reasoning behind that choice" or "good question — here's why we did it this way." This turns a potentially dismissive moment into a teaching opportunity and reinforces the rationale for design decisions.

If the behavior continues despite the conversation, I'd escalate appropriately — perhaps involving their manager or HR if needed — but I'd also consider whether there are underlying causes. Sometimes engineers who dismiss questions are feeling pressure about the project timeline or are frustrated by repeated questions on topics they've explained before. Understanding the root cause helps me address the behavior more effectively.

**Possible follow-ups:**
- How would you handle the situation if the senior engineer becomes defensive during your conversation?
- What would you do if a junior engineer tells you they're now afraid to ask questions in design reviews because of this engineer's behavior?

---

## Q5: How would you approach leading a technical decision when two equally experienced engineers disagree on whether to use a hardware timer interrupt or a dedicated PWM peripheral for motor speed control in a medical device, and both approaches have valid trade-offs?

**Answer:** When two experienced engineers disagree on a technical approach and both have valid arguments, the worst outcome is letting the decision drag on or forcing a resolution based on seniority or personality. I'd approach this as a structured decision-making process that focuses on the specific requirements of the application.

First, I'd ensure both engineers have the opportunity to fully articulate their positions and the reasoning behind them. Often, disagreements like this stem from different priorities — one engineer might be prioritizing worst-case timing accuracy while the other is prioritizing code simplicity or power consumption. I'd ask each to explain their concerns and what they see as the critical risks of the alternative approach.

Then I'd evaluate both options against the specific requirements of the medical device. For motor speed control, key questions include: What is the required speed control accuracy? What is the motor's PWM frequency range? Are there safety requirements around motor behavior — for example, must the motor stop or maintain a specific speed in a fault condition? How does each approach handle edge cases like a missed interrupt or a PWM peripheral malfunction? In a medical device, the safety implications of each approach are paramount — a hardware timer interrupt might be more flexible but introduces risks around interrupt latency and priority inversion, while a dedicated PWM peripheral might be more deterministic but less flexible for complex control algorithms.

I'd also consider the broader system context. What microcontroller is being used, and what are its capabilities? Is the firmware team more experienced with one approach? What are the testing and verification implications? In a medical device, the approach that's easier to verify and validate might be preferable even if it's slightly less elegant from a pure engineering standpoint.

If the disagreement persists after this analysis, I might suggest a prototyping exercise — implementing both approaches on a development board and measuring the actual performance differences. Data from a real implementation often resolves theoretical disagreements. If time constraints don't allow prototyping, I'd make a decision based on the requirements analysis, document the rationale thoroughly, and ensure both engineers understand that the decision was made based on evidence and requirements, not politics.

The key is to make the decision transparent and traceable. In a medical device context, the design history file should capture not just the decision but the alternatives considered and the rationale for the chosen approach. This protects the team if questions arise during regulatory review or if the decision needs to be revisited later.

**Possible follow-ups:**
- What specific safety considerations would you weigh most heavily in this decision for a medical device?
- How would you handle the situation if the engineer whose approach was not selected continues to raise concerns about the decision in team meetings?