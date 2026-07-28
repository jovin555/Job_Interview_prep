# behavioral-leadership — Day 7

## Q1: How would you approach leading a design review for a medical device PCB when you discover, mid-review, that the layout engineer placed a high-speed digital trace directly under an analog sensor's reference voltage path, and the original designer is not present to explain their reasoning?

**Answer:** I would first pause the review at that specific finding rather than letting the meeting continue and hoping to circle back. The absence of the original designer makes it critical to document the exact concern clearly so they can respond later, but the review shouldn't proceed past a potentially blocking issue without at least a containment decision.

I'd state the observation neutrally — "I'm seeing the digital trace routed directly beneath the analog reference path on layer 3, which creates a coupling risk" — and ask if anyone else on the call has context on why that routing was chosen. If no one does, I'd mark it as a formal action item requiring the designer's rationale before the layout is finalized, and I'd suggest a temporary containment: either flagging that section for re-routing or adding a ground plane stitch between the layers if stack-up allows.

The key leadership aspect is balancing the need to keep the review moving against the risk of approving a layout that could cause noise coupling issues during EMC or functional testing later. I'd also make a note to follow up with the layout engineer one-on-one afterward, not to assign blame but to understand their decision process and reinforce design guidelines for sensitive analog-digital separation. The review minutes should clearly state the finding, the containment action, and the required response before sign-off.

**Possible follow-ups:** How would you handle it if the layout engineer later explains they routed that way because the original placement forced it, and re-routing would require a major component relocation? What if the schedule pressure means the board needs to be released this week?

---

## Q2: How would you approach building a cross-functional project timeline for a medical device when the hardware, firmware, and regulatory teams each have different estimates for how long their work will take, and there's no historical data from similar projects?

**Answer:** I'd start by acknowledging that without historical data, every estimate is a guess with varying confidence levels, and the goal is to surface those uncertainties rather than force false precision. I'd bring the leads from each team into a structured estimation session, not a negotiation.

First, I'd ask each team to break their work into the smallest reasonable chunks — not just "firmware: 4 months" but specific phases like "sensor driver development," "communication protocol implementation," "power management state machine," and so on. For each chunk, I'd ask them to give three numbers: an optimistic estimate (if everything goes perfectly), a realistic estimate (assuming normal hiccups), and a pessimistic estimate (if they hit the worst plausible problems). This is essentially a lightweight PERT approach.

Then I'd look for dependencies between teams. For example, firmware can't test the sensor driver until hardware delivers a prototype with the sensor populated and working. Those dependencies often reveal that the critical path isn't where anyone assumed. I'd map those visually — even a simple whiteboard timeline with sticky notes — so everyone can see where their work connects.

The hardest part is managing the natural tendency for each team to pad their estimates defensively when they see others padding. I'd frame it as: "We're not trying to minimize the timeline; we're trying to find the most realistic one so we can communicate honestly to management and avoid surprises." If there's still wide disagreement, I'd suggest we identify the top three technical risks that could blow the schedule and agree to prototype or investigate those first, before committing to a full timeline.

**Possible follow-ups:** How would you handle it if one team's lead refuses to give a pessimistic estimate because they think it will be used against them later? What if the product manager insists on a single date and won't accept a range?

---

## Q3: How would you approach handling a situation where a senior engineer on your team consistently produces excellent technical work but has a pattern of dismissing questions from junior engineers during design reviews, saying things like "that's obvious" or "we don't need to discuss that"?

**Answer:** I would address this privately with the senior engineer first, not in front of the team or during a review. The behavior is damaging team culture and discouraging junior engineers from speaking up, which is a safety risk in medical device development — the next question a junior doesn't ask could be the one that catches a real issue.

In the private conversation, I'd frame it around the impact rather than the intent. Something like: "I've noticed in recent reviews that when junior engineers ask questions, you sometimes respond in a way that shuts down the discussion. I know you're not trying to be dismissive, but the effect is that people are hesitating to raise concerns, and we need those questions to catch problems early." I'd ask if there's a reason — maybe he feels the reviews are running too long, or he assumes certain knowledge that isn't there — and work together on a better approach.

I'd also suggest a concrete alternative: instead of saying "that's obvious," he could say "that's a good question — here's the reasoning behind that choice" or even "let me explain why that's not a concern in this case." That turns the moment into a teaching opportunity rather than a shut-down.

If the behavior continues after the conversation, I'd escalate to more structured coaching, including possibly having him observe a review where someone else handles questions well, or assigning him a mentoring role where he's explicitly responsible for developing junior engineers. The goal is to preserve his technical contribution while changing the interaction pattern.

**Possible follow-ups:** What if the senior engineer responds that he's just being efficient and the juniors should read the design documents before the review? How would you handle it if a junior engineer comes to you privately saying they no longer want to attend design reviews because of this engineer's behavior?

---

## Q4: How would you approach deciding whether to escalate a technical disagreement between two senior engineers to your manager, versus resolving it within the team?

**Answer:** I would first assess whether the disagreement is blocking progress and whether it falls within my authority to resolve. The threshold for escalation isn't the intensity of the disagreement — it's whether the team can make a timely, technically sound decision without involving higher management.

I'd start by facilitating a structured discussion between the two engineers. I'd ask each to clearly state their position, the data supporting it, and the specific trade-offs they see. Often, disagreements that seem fundamental are actually about different assumptions or priorities — one engineer might be prioritizing long-term reliability while the other is prioritizing time-to-market, and neither is wrong, they just need a decision framework that weights those factors.

If after that discussion there's still no resolution, I'd consider whether I can make the call myself based on the information presented. As the lead, I have the responsibility to make decisions when consensus isn't possible. I'd explain my reasoning, document it, and ask both engineers to commit to the chosen approach even if they disagree — that's part of professional engineering culture.

I would escalate only if: (1) the decision has significant cost or schedule implications beyond what I'm authorized to approve, (2) the disagreement reflects a deeper organizational issue (like unclear design authority or conflicting requirements from different stakeholders), or (3) the engineers are unable to work together professionally after the decision is made. In that case, I'd go to my manager with a clear summary of both positions, the data, and why I believe escalation is necessary — not to "tattle" but to get the organizational support needed to move forward.

**Possible follow-ups:** What if one of the engineers threatens to go over your head directly to your manager if you don't choose their approach? How would you handle a situation where you make the call, and the engineer whose approach wasn't chosen starts undermining the decision in team meetings?

---

## Q5: How would you approach leading a post-mortem after a medical device project missed its delivery deadline by several months, when team morale is low and there's a tendency to blame individual contributors rather than systemic issues?

**Answer:** I would structure the post-mortem to focus on process and system factors, not individual performance, and I'd set that expectation explicitly at the start. The goal is to learn what went wrong so the next project doesn't repeat it, not to assign blame. If people feel they're being set up for criticism, they'll either deflect or disengage, and we'll learn nothing useful.

I'd start by establishing ground rules: no names in the "what went wrong" column, focus on events and decisions rather than people, and everyone gets to speak without interruption. I'd use a structured framework like a timeline reconstruction — lay out the project's major milestones and decisions, then ask the team to identify where things started to deviate from plan. Often, the root cause of a late delivery happened months before the deadline was missed, but no one flagged it because everyone was optimistic.

I'd also separate the post-mortem into three phases: (1) what happened (factual timeline), (2) why it happened (root causes), and (3) what we'll do differently (actionable improvements). The third phase is the most important for morale — it turns the conversation from "we failed" to "here's how we'll be better next time."

If there's a specific decision or action that clearly contributed to the delay, I'd discuss it in terms of the decision-making process, not the person who made it. For example, instead of "John underestimated the sensor integration time," I'd say "the sensor integration estimate was based on a similar project that turned out to be less complex — how can we improve our estimation process for novel components?"

Finally, I'd make sure the post-mortem produces a short list of concrete, owned action items with owners and deadlines, and I'd follow up on them in subsequent team meetings. Nothing kills morale faster than a post-mortem that produces a long list of recommendations that are never implemented.

**Possible follow-ups:** How would you handle it if a team member insists on blaming a specific person during the post-mortem despite the ground rules? What if the root cause analysis reveals that the project was doomed from the start because the requirements were unrealistic, and the team knew it but no one spoke up?