# behavioral-leadership — Day 48

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a battery management system fault or a charging circuit problem, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a structured root-cause investigation rather than a debate between two hypotheses. The first step is containment — ensuring patient safety and preventing further exposure while the investigation runs. That might mean issuing a field action to restrict charging under certain conditions, or adding interim guidance, depending on the risk assessment.

Then I'd assemble a small cross-functional team — hardware, firmware, quality, and possibly the field service group — and begin with a disciplined data collection phase before any analysis. The key is to gather evidence from the actual field returns: charge curves, battery voltage and temperature logs, charging current profiles, and physical inspection data. I'd want to know things like: Did the failures cluster around specific chargers, firmware versions, or environmental conditions? Were there common failure modes in the returned units — swollen cells, damaged charge FETs, blown fuses, or nothing visible at all?

I'd use a fishbone diagram to map all plausible causes across categories — electrical, thermal, firmware, mechanical, and usage patterns — and then apply 5 Whys to narrow down. The critical discipline here is not to let the team jump to a fix before the evidence points clearly to one branch. If the data genuinely supports both hypotheses, I'd design experiments that discriminate between them — for example, bench-testing the charging circuit under worst-case conditions versus cycling batteries with a controlled charger to reproduce the failure.

Once the root cause is confirmed, I'd implement corrective action through formal change control, and — this is often missed — define how we'll verify effectiveness. That means tracking field performance after the fix for a defined period, not just assuming the problem is solved. Throughout, I'd keep the investigation documented in a format that supports both the design history file and any regulatory reporting obligations.

**Possible follow-ups:** How would you handle the pressure to issue a corrective action before the root cause is confirmed, when the two hypotheses point to very different fixes? What specific data would you want from the field before you even start bench testing?

---

## Q2: How would you approach building a risk management culture on a medical device team that currently treats ISO 14971 documentation as a checkbox exercise done after the design is complete?

**Answer:** The core problem is that risk management has become an administrative afterthought rather than an engineering discipline. I'd start by reframing the purpose: ISO 14971 isn't about producing documents for auditors — it's a structured way to identify what could harm a patient or user, and to make sure the design actually mitigates those harms. The documentation is just the evidence that this thinking happened.

I'd begin by integrating risk activities into existing engineering milestones rather than adding them as separate tasks. For example, the risk management file shouldn't be created after the design is done — it should start with the concept phase, when the team is defining user needs and intended use. At each design review, I'd make the risk file a standing agenda item: what new hazards have we identified since the last review, and how have they changed the design? This makes risk analysis a living document that evolves with the design.

I'd also work to make the connection concrete for engineers. When someone proposes a design change, the natural question becomes: "What hazard does this change introduce, and what's the resulting risk?" When someone identifies a potential failure mode during a design review, I'd capture it immediately as a potential hazard rather than letting it disappear. This shifts the mindset from "risk management is paperwork" to "risk management is how we catch problems before they reach patients."

To build momentum, I'd start with one project as a pilot — working closely with the team to make the risk file genuinely useful, not just compliant. I'd also bring in concrete examples of how early risk identification has prevented real harm or costly late-stage redesigns, ideally from within the company's own history. Over time, as engineers see that risk thinking actually improves their designs and reduces rework, it becomes part of the culture rather than an imposed requirement.

**Possible follow-ups:** How would you handle a senior engineer who argues that formal risk analysis slows down the design process and that their experience is sufficient? What specific artifacts or meeting changes would you implement in the first month?

---

## Q3: How would you approach leading a design review for a medical device PCB when you discover, mid-review, that the layout engineer placed a high-speed digital trace directly under an analog sensor's reference voltage path, and the original designer is not present to explain their reasoning?

**Answer:** First, I'd stop the review at that specific finding and make sure everyone understands the technical concern clearly: a high-speed digital trace can couple switching noise into the analog reference path through parasitic capacitance and ground bounce, potentially corrupting the sensor measurements. This is a classic mixed-signal layout issue, and in a medical device context, the stakes are higher because the sensor data may drive clinical decisions.

I wouldn't immediately declare it a defect, though. There are scenarios where such a placement might be acceptable — for example, if the reference path is heavily filtered, if the digital trace is on an internal layer with adjacent ground planes providing shielding, or if the analog sampling occurs at a time when the digital signal is quiet. Without the original designer present, I can't know their reasoning. So the right move is to flag it as a review action item requiring either justification or redesign.

I'd assign someone to document the finding precisely — layer stack, trace spacing, reference net, and the potential coupling mechanism — and then set up a follow-up with the original designer. In the meantime, I'd ask the team to assess whether this is a risk that can be analyzed or whether it needs empirical verification. If the layout is already fabricated, we might need to bench-test the actual noise coupling. If it's still in layout, we can evaluate whether a reroute is feasible without cascading delays.

The key leadership point is maintaining a constructive tone. The goal isn't to embarrass the layout engineer but to ensure the design is sound. I'd frame it as: "We've found a potential issue that needs resolution — let's understand the reasoning and determine whether it's acceptable or needs correction." This models how design reviews should work: findings are about the design, not the person.

**Possible follow-ups:** How would you decide whether to halt the design review entirely versus continuing with other items while this is investigated? What if the original designer insists the placement is fine but cannot provide a clear technical rationale?

---

## Q4: How would you approach managing a situation where a senior engineer on your team consistently delivers excellent technical work but has a pattern of dismissing questions from junior engineers during design reviews, saying things like "that's obvious" or "we don't need to discuss that"?

**Answer:** This is a situation where the technical quality of the work isn't the issue — the problem is the impact on team dynamics and, ultimately, on design quality. When junior engineers are dismissed, they stop asking questions, and that's when real issues get missed. A design review where people are afraid to speak up is not a design review — it's a presentation.

I'd start with a private conversation with the senior engineer. I'd be specific about the behavior I've observed, using concrete examples rather than generalities. I'd frame it around the impact: when junior engineers are shut down, the team loses the benefit of fresh perspectives, and we risk missing issues that a more experienced eye might overlook. I'd also acknowledge their technical strength — the goal isn't to diminish their expertise but to make the review process more effective for everyone.

I'd also introduce structural changes to the design review process itself. For example, I might implement a "round-robin" format where each attendee is explicitly invited to raise questions or concerns before moving to the next section. This creates a norm where participation is expected, not optional, and makes it harder for one person to dominate. I'd also establish ground rules for reviews: questions are always legitimate, and if something seems "obvious," the burden is on the presenter to explain it clearly rather than on the questioner to already know it.

If the behavior continues after the private conversation, I'd escalate the discussion — not punitively, but by making the connection to team effectiveness and the engineering culture we're trying to build. I'd also check in with the junior engineers privately to understand their experience and make sure they feel supported. The underlying principle is that psychological safety in design reviews is not a soft skill — it's a technical risk mitigation strategy.

**Possible follow-ups:** How would you handle it if the senior engineer responds defensively, arguing that junior engineers should do their homework before asking basic questions? What would you do if you observed the same behavior continuing after your initial conversation?

---

## Q5: How would you approach leading a technical decision when two senior engineers disagree on whether to use a hardware timer interrupt or a dedicated PWM peripheral for motor speed control in a medical device, and both approaches have valid trade-offs?

**Answer:** I'd start by making sure the disagreement is framed around engineering evidence rather than personal preference. Both approaches have legitimate trade-offs — a hardware timer interrupt offers flexibility and precise timing control, while a dedicated PWM peripheral offloads the timing from the CPU and provides more predictable waveform generation. In a medical device context, the decision should hinge on reliability, determinism, and failure modes, not on which engineer is more persuasive.

I'd structure the decision process around the specific requirements of the application. Key questions would include: What is the required speed control accuracy and response time? What happens if the CPU is busy with other tasks — does the motor speed need to remain stable? What are the failure modes of each approach — for example, if the timer interrupt is delayed or missed, does the motor behave unsafely? Is there a watchdog or supervisory mechanism that can detect a fault in either approach?

I'd ask each engineer to prepare a brief analysis addressing these questions, including worst-case timing scenarios and failure mode analysis. If the disagreement persists after the analysis, I'd consider a prototyping approach — implementing both options on a bench setup and measuring the actual behavior under realistic load conditions. Data from a prototype often resolves disagreements more effectively than extended debate.

If the decision still remains genuinely close, I'd make the call based on the risk assessment and document the rationale clearly. In a medical device, I'd lean toward the approach that offers more deterministic behavior and simpler failure analysis, even if it's slightly less flexible. The key is that once the decision is made, both engineers commit to it — and the documentation captures not just what was chosen, but why, so future engineers understand the context.

**Possible follow-ups:** How would you handle it if one engineer refuses to accept the decision and continues to advocate for their approach after the decision is made? What specific failure mode analysis would you want to see before making the final call?