# behavioral-leadership — Day 39

## Q1: How would you approach leading a technical decision when two senior engineers disagree on whether to use a hardware timer interrupt or a dedicated PWM peripheral for motor speed control in a medical device, and both approaches have valid trade-offs?

**Answer:** I'd start by framing the decision around the system requirements rather than personal preference. The key is to identify what actually matters for this specific application: timing precision, jitter tolerance, CPU load, power consumption, and failure modes. I'd ask both engineers to articulate their concerns in terms of these criteria rather than general architectural preferences.

For a motor speed control application in a medical device, I'd want to understand the control loop requirements first. A hardware timer interrupt gives more flexibility in terms of when and how often the control algorithm runs, but it consumes CPU cycles and can introduce jitter if other interrupts preempt it. A dedicated PWM peripheral offloads the waveform generation entirely, which is more deterministic, but it may have limitations on resolution, frequency range, or duty cycle granularity depending on the specific microcontroller.

I'd suggest a structured comparison: have each engineer document their approach against the same set of criteria — worst-case timing accuracy, interrupt latency impact on other critical functions, power consumption in active and low-power modes, and what happens on peripheral failure. If the decision still isn't clear, I'd propose a prototyping exercise where both approaches are implemented on the same hardware and measured against the actual requirements. Data from a real board beats theoretical arguments every time.

Once a decision is made, I'd document the rationale, the alternatives considered, and the criteria used — this is critical for medical device design history files and for preventing the same debate from resurfacing later.

**Possible follow-ups:** What specific measurements would you take during the prototyping exercise to make the decision data-driven? How would you handle the situation if the prototyping results are inconclusive or show both approaches are equally viable?

---

## Q2: How would you approach building a risk management culture on a medical device team that currently treats ISO 14971 documentation as a checkbox exercise done after the design is complete?

**Answer:** The core issue is that risk management is being treated as a documentation task rather than an engineering activity. I'd start by reframing it: risk management isn't paperwork, it's a design tool that helps you build better products. The documentation is just the evidence that the thinking happened.

I'd begin by integrating risk activities into existing engineering workflows rather than adding them as separate tasks. For example, design reviews should include a standing agenda item on risk — not "did we update the risk table?" but "what new risks have we identified since the last review, and how do they affect our design?" This makes risk identification a natural part of engineering discussion rather than a separate exercise.

I'd also work on making the connection between risk analysis and design decisions explicit. When a design change is made, the question should be "how does this affect the risk profile?" not "do we need to update the risk file?" The risk management file should be a living document that evolves with the design, not a retrospective summary.

For the team that sees this as overhead, I'd emphasize the practical value: a good risk analysis catches problems early when they're cheap to fix, rather than during verification testing or worse, in the field. I'd also make sure the team sees examples of how risk analysis actually drives design changes — showing a specific case where identifying a hazard early led to a simpler, safer design is more convincing than any policy statement.

Finally, I'd make risk management part of how we measure engineering quality, not just regulatory compliance. If a design review doesn't identify any new risks, that's a red flag — it means the team isn't thinking deeply enough, not that the design is perfect.

**Possible follow-ups:** How would you handle a team member who argues that risk analysis is slowing down the project? What specific changes would you make to the design review process to incorporate risk management?

---

## Q3: How would you approach leading a design review for a medical device PCB when you discover, mid-review, that a critical safety-related trace width calculation was never documented, and the original designer is no longer with the company?

**Answer:** First, I'd stop the review at that specific item and acknowledge the gap openly — this isn't about assigning blame, it's about ensuring the design is safe and compliant. The trace width calculation for a safety-related circuit is fundamental: it determines whether the trace can handle the expected current without overheating, which directly affects patient safety.

I'd immediately assess what we do know. Can we determine the trace width from the PCB layout files? Can we calculate the expected current from the circuit schematic and component specifications? If we can reconstruct the calculation from available information, we can verify it against the actual layout. If we can't, the trace needs to be treated as unverified until we can either redo the calculation or justify it through testing.

I'd also check whether there are any related documents that might contain the information — email threads, meeting notes, older revisions of the design, or similar designs from the same engineer that might have used the same calculation approach. In a medical device context, this gap also raises a design history file completeness issue that needs to be addressed.

The immediate action is to document the gap, flag it as a review finding, and assign someone to reconstruct the calculation. The design shouldn't proceed past this point until the trace is verified — either through recalculation or through testing that demonstrates the trace can handle the required current under worst-case conditions. I'd also use this as a lesson for the team: critical calculations need to be documented at the time they're done, not reconstructed later.

**Possible follow-ups:** How would you verify the trace's adequacy if the original calculation can't be reconstructed? What changes would you make to the design review process to prevent this situation from recurring?

---

## Q4: How would you approach handling a situation where a regulatory audit is scheduled in two weeks, and you discover that several key design verification test reports are missing signatures or have incomplete data that cannot be re-run in time?

**Answer:** I'd start by doing a thorough assessment of exactly what's missing — which reports, which signatures, which data points. The first step is to understand the scope of the problem before deciding how to address it. Some gaps might be administrative (a signature that can be obtained from someone who was present during the test), while others might be substantive (test data that was never recorded).

For administrative gaps, I'd work quickly to resolve them — getting signatures from the appropriate people, completing missing metadata, and ensuring the reports are properly filed. These are legitimate fixes, not falsification, because the underlying test was actually performed.

For substantive gaps — missing data that can't be reconstructed — I'd be honest about the situation. The options are: (1) determine if the data exists elsewhere (raw data files, lab notebooks, electronic records), (2) assess whether the missing data can be derived from other recorded information, or (3) acknowledge that the test needs to be repeated. If the test genuinely needs to be repeated, I'd communicate this clearly to the auditor rather than trying to hide it.

I'd also prepare a clear explanation of what happened and what we're doing about it. Auditors are generally more concerned with how you handle a non-conformance than with the non-conformance itself. A transparent approach — "we identified this gap, here's our corrective action plan, here's the timeline" — is far better than trying to present incomplete data as complete.

Before the audit, I'd also do a broader sweep of all the documentation to identify any other gaps, so we're not discovering issues during the audit itself. This gives us the opportunity to address what we can and prepare explanations for what we can't.

**Possible follow-ups:** What would you do if the auditor discovers the incomplete data during the audit before you've had a chance to address it? How would you prioritize which gaps to address first?

---

## Q5: How would you approach managing a situation where a senior engineer on your team consistently delivers excellent technical work but has a pattern of dismissing questions from junior engineers during design reviews, saying things like "that's obvious" or "we don't need to discuss that"?

**Answer:** This is a situation where I'd address both the immediate behavior and the underlying cause. The senior engineer's technical expertise is valuable, but dismissing questions creates two problems: it discourages junior engineers from speaking up, and it can mask genuine design issues that deserve discussion.

I'd start with a private conversation with the senior engineer. The goal isn't to criticize their technical work — it's to help them see the impact of their communication style. I'd frame it around the team's effectiveness: when junior engineers ask questions, it's often because they're identifying gaps in the documentation or the reasoning that others have missed. A question that seems "obvious" to someone with years of experience might reveal a genuine ambiguity in the design.

I'd also suggest a practical technique: instead of dismissing a question, the senior engineer could ask themselves "what might this person be seeing that I'm not?" Even if the answer is "nothing," taking the question seriously and explaining the reasoning builds trust and helps junior engineers learn. The goal is to shift from "that's obvious" to "here's why we made this choice" — which is more work in the moment but pays off in team capability.

In parallel, I'd work on the team culture around design reviews. I'd establish a norm that all questions are legitimate in a review — the whole point is to scrutinize the design from every angle. I'd also make sure junior engineers have a way to raise concerns outside the review if they feel intimidated, perhaps through a written comment process or a pre-review discussion.

If the behavior continues after the conversation, I'd escalate — not as punishment, but because the pattern is undermining the team's ability to do thorough design reviews, which is a safety issue in a medical device context. A design review where people are afraid to ask questions is not a review at all.

**Possible follow-ups:** How would you handle the situation if the senior engineer responds defensively to your feedback? What would you do if a junior engineer tells you they're avoiding asking questions in reviews because they're afraid of being dismissed?