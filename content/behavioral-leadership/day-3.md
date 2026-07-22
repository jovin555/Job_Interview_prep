# behavioral-leadership — Day 3

## Q1: How would you approach convincing a skeptical quality assurance manager to accept a deviation from a standard design practice when you believe the alternative approach is actually safer for the specific application?

**Answer:** I'd start by acknowledging their concern directly — their job is to protect patient safety and regulatory compliance, so skepticism is appropriate. Rather than arguing against the standard, I'd frame the discussion around the specific risk profile of our application versus what the standard assumes.

First, I'd prepare a side-by-side comparison showing how the standard practice addresses certain failure modes, and then demonstrate — ideally with data from simulations or bench testing — why those failure modes don't apply or are better mitigated by the alternative. For example, if the standard calls for a specific isolation barrier topology but our device has fundamentally different leakage current paths due to its battery-powered, patient-isolated design, I'd show the actual measured isolation performance of both approaches.

I'd also propose a concrete verification plan: additional testing beyond what the standard requires, or a documented risk assessment (per ISO 14971) that formally compares the two approaches. The goal is to give the QA manager something they can defend to an auditor — not just my opinion, but a documented rationale with supporting evidence.

Finally, I'd ask for a trial period or limited-scope approval rather than a permanent change, so we can gather real-world data before committing. This reduces the perceived risk on their side.

**Possible follow-ups:** What would you do if the QA manager still refuses after you've presented the data? How would you handle a situation where the standard practice and the alternative have different failure modes — neither is clearly safer?

---

## Q2: How would you approach managing a situation where two senior engineers on your team have a fundamental disagreement about whether to use a single high-performance microcontroller or a dual-processor architecture for a new medical device, and the decision is blocking the project timeline?

**Answer:** I'd first separate the technical debate from the schedule pressure. Calling a time-boxed decision meeting with both engineers, I'd ask each to prepare a one-page summary of their position covering: the key technical trade-offs (cost, power, reliability, development effort), the specific risk each approach mitigates or introduces, and what evidence they have — whether from datasheets, previous projects, or simulations.

During the meeting, I'd facilitate rather than decide. I'd ask each engineer to restate the other's position to ensure mutual understanding, then identify where they actually agree. Often in these debates, 80% of the requirements are met by either approach, and the disagreement is about the last 20%.

If we can't reach consensus, I'd propose a structured tiebreaker: identify the single most critical requirement that differentiates the two approaches — for example, worst-case interrupt latency for a safety-critical sensor readout — and run a focused benchmark or prototype to resolve that specific question. I'd set a hard deadline for that experiment, typically one to two weeks, and commit the team to accepting whichever approach wins on that metric.

If the timeline truly can't accommodate even a short experiment, I'd make the call myself based on the risk profile: which approach has the fewer unknowns, or which failure mode is easier to detect and mitigate in software. I'd document the decision rationale and the dissenting opinion, so if issues arise later we have a clear record of why we chose that path.

**Possible follow-ups:** How would you handle it if one of the engineers is more senior or more vocal, and the other is being overshadowed? What if the disagreement is actually about future-proofing versus time-to-market — how do you weigh those?

---

## Q3: How would you approach building a culture of design review participation on a team where engineers historically treat reviews as rubber-stamp exercises or avoid them altogether?

**Answer:** I'd start by understanding why the current culture exists. Often it's because reviews feel like gatekeeping or criticism rather than collaborative improvement. I'd address this by reframing the purpose: design reviews are not about catching mistakes — they're about making the design better through diverse perspectives.

Practically, I'd implement three changes. First, I'd establish a clear review structure with defined roles: the presenter prepares a focused package (schematics, layout highlights, key design decisions with trade-offs) and sends it 48 hours in advance. Reviewers come with written questions, not just comments during the meeting. This shifts the dynamic from "let me present my work" to "let's discuss the decisions I've documented."

Second, I'd model the behavior I want. In my own reviews, I'd explicitly call out design decisions I'm uncertain about and ask for input — showing that vulnerability is safe and that good engineers ask for help. I'd also make a point of thanking reviewers who find issues, publicly acknowledging that their catch saved us time or risk.

Third, I'd track and close the loop. After each review, I'd send a summary of action items and decisions, and follow up at the next review to show how previous feedback was incorporated. When people see their input actually changes the design, they become more invested.

For engineers who consistently avoid participating, I'd have a private conversation to understand their barriers — maybe they feel they don't know enough about the specific technology, or they've had bad experiences. I'd pair them with a more experienced reviewer for a few cycles, or assign them specific areas to focus on (e.g., "please review just the power supply section") to build confidence.

**Possible follow-ups:** How would you handle a senior engineer who dominates every review and discourages others from speaking up? What metrics would you use to measure whether the review culture is improving?

---

## Q4: How would you approach leading a project estimation and planning session for a new medical device feature when the requirements are still vague and the team has never built anything similar before?

**Answer:** I'd resist the temptation to give a single number. Instead, I'd break the estimation into phases and communicate the uncertainty explicitly.

First, I'd work with the team to decompose the feature into the smallest reasonable chunks — not full work breakdown, but functional blocks that we can reason about independently. For each block, we'd estimate three scenarios: optimistic (everything goes perfectly), most likely (normal challenges), and pessimistic (major unknowns surface). This gives a range rather than a false precision.

For the blocks with the widest range between optimistic and pessimistic — the true unknowns — I'd propose a short investigation sprint (one to two weeks) to reduce that uncertainty. The goal isn't to build the feature, but to answer specific questions: Can this sensor achieve the required accuracy at the target power budget? Does this communication protocol work reliably through the device enclosure? The results of that sprint then inform a more confident estimate for the remaining work.

I'd present this to stakeholders as a phased approach: "We can give you a rough order-of-magnitude estimate today, but I'm recommending a two-week investigation phase to narrow it down. After that, I can give you a much more reliable timeline." I'd also explicitly state what assumptions we're making and what would change the estimate — for example, "If the sensor accuracy doesn't meet spec, we'll need to add an external amplifier, which adds two weeks and increases BOM cost by roughly $X."

Finally, I'd build in buffer for the unknowns — typically 30-50% for the first iteration of a novel feature — and clearly label it as contingency, not schedule slack. This way, if we discover something unexpected, we have room to handle it without immediately blowing the timeline.

**Possible follow-ups:** How would you handle a product manager who insists on a single-point estimate despite your explanation of uncertainty? What if the investigation sprint reveals that the feature is significantly harder than expected — how do you communicate that without losing stakeholder confidence?

---

## Q5: How would you approach handling a situation where you discover, mid-way through a medical device project, that a junior engineer on your team has been making unauthorized design changes to the firmware without updating the design history file or going through change control?

**Answer:** First, I'd address the immediate compliance risk. I'd stop any further changes and quarantine the affected units or software versions. Then I'd work with the engineer to reconstruct exactly what was changed, when, and why — not to assign blame, but to understand the scope of the impact. I'd document everything we find, including timestamps and any testing that was done on the modified versions.

Next, I'd assess the safety impact. Were the changes in a safety-critical function? Could they affect patient monitoring, alarm thresholds, or treatment delivery? If there's any possibility of patient harm, I'd escalate immediately to quality and regulatory, and potentially initiate a field safety corrective action process. If the changes were in non-critical areas (e.g., UI cosmetics or logging), the risk is lower but the process violation is still serious.

Once the immediate situation is contained, I'd have a private conversation with the engineer. I'd start by acknowledging that their intent was likely positive — they saw an improvement and wanted to implement it quickly. But I'd clearly explain why the process exists: in medical devices, every change must be traceable because we need to prove to regulators that the device is safe and effective. A well-intentioned change that isn't documented is, from a regulatory perspective, the same as a malicious one — it breaks the chain of evidence.

I'd also ask what drove them to bypass the process. Was it frustration with slow change control? Did they not understand the requirements? Was there pressure from management to move faster? Understanding the root cause helps me fix the system, not just the individual.

Depending on the severity, I'd work with quality to determine whether a formal corrective action (like a CAPA) is needed. I'd also use this as a teaching moment for the whole team — without naming the individual — to reinforce why change control exists and what the consequences of bypassing it can be, both for patient safety and for the company's regulatory standing.

**Possible follow-ups:** How would you handle it if the engineer's unauthorized changes actually improved performance, and reverting them would delay the project? What if the engineer is a high-performer who is otherwise excellent — how does that affect your response?