# behavioral-leadership — Day 45

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a battery management system fault or a charging circuit problem, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing the investigation around data collection rather than hypothesis testing between the two teams. The first step is to gather the actual field units or their data logs, because the fault signature often discriminates between the two paths before any deep analysis begins. I'd look at things like charge termination voltage, charge current profiles over time, cell voltage divergence, and whether the fault occurs during charging or during discharge — that alone narrows the space considerably.

Next, I'd structure the investigation using a formal root-cause framework like 8D or a fishbone diagram, but the key is to keep the two hypotheses alive until the evidence rules one out. I would not allow the team to commit to one cause prematurely, because in medical devices the corrective action paths diverge sharply: a battery management fault might require a firmware fix and a recall of field units for software update, while a charging circuit fault could require a hardware change, a board rework, and potentially a different regulatory submission strategy.

I'd also establish a clear evidence standard upfront. For example, if the battery management hypothesis is correct, we should be able to reproduce the failure on the bench with a known-good charger. If the charging circuit hypothesis is correct, we should see the fault signature change when we substitute a known-good charger or measure specific node voltages during the charge cycle. I'd assign one engineer to own each hypothesis and have them report back with data, not opinions. This prevents the investigation from becoming a blame game and keeps it focused on what the evidence shows.

Once the root cause is confirmed, I'd ensure the containment action protects patients immediately — even before the permanent corrective action is ready — and then verify the corrective action's effectiveness through targeted testing that specifically exercises the failure mode we identified.

**Possible follow-ups:**
- How would you handle a situation where the two engineers leading the parallel investigations are both finding evidence that supports their own hypothesis and dismissing evidence that supports the other?
- What specific test setups or measurements would you request to discriminate between a battery management fault and a charging circuit fault?

---

## Q2: How would you approach building a risk management culture on a medical device team that currently treats ISO 14971 documentation as a checkbox exercise done after the design is complete?

**Answer:** The core problem is that the team sees risk management as a documentation activity rather than an engineering activity. I'd start by reframing it: risk management is not something you write up after the design — it's a design input that shapes architecture, component selection, and test strategy. The documentation is just the record of that thinking.

To shift the culture, I'd integrate risk activities into existing engineering rituals rather than adding new ones. For example, at every design review, I'd require the team to explicitly discuss what hazards the current design introduces, what mitigations exist, and what residual risk remains. This doesn't need to be a formal DFMEA session every time — it can be a standing agenda item that forces the conversation. Over time, the team starts to think in risk terms naturally because it becomes part of how they evaluate design choices.

I'd also make the connection between risk analysis and test planning explicit. When the team writes a design verification test plan, I'd ask them to trace each test back to a specific hazard or failure mode identified in the risk analysis. If a test doesn't trace to a risk, either the test is unnecessary or the risk analysis is incomplete. This creates a practical reason to do risk analysis well — it directly drives what testing is needed, which is something engineers care about.

Another practical step is to introduce risk thinking early in the design process, not after the schematic is done. During architecture discussions, I'd ask questions like: "What happens if this sensor drifts out of spec?" or "What's the failure mode if this power rail collapses during a measurement?" These questions force the team to think about failure modes before the design is locked in, which is where risk management actually saves time and money.

Finally, I'd make sure the team sees the consequences of good risk management. When a risk analysis catches a real issue early — before a prototype is built or before a test fails — I'd highlight that as a win, not as extra work. That positive reinforcement is what changes the culture from checkbox compliance to genuine engineering practice.

**Possible follow-ups:**
- How would you handle a situation where a senior engineer argues that formal risk analysis is slowing down the design process and that their experience is sufficient to identify hazards?
- What specific changes would you make to the design review agenda to incorporate risk discussions without making reviews significantly longer?

---

## Q3: How would you approach leading a design review for a medical device PCB when you discover, mid-review, that the layout engineer placed a high-speed digital trace directly under an analog sensor's reference voltage path, and the original designer is not present to explain their reasoning?

**Answer:** The first thing I'd do is stop the review and assess whether this is a genuine concern or a potential non-issue. A high-speed digital trace under an analog reference path is a classic layout red flag, but the actual risk depends on several factors: the rise time of the digital signal, the coupling distance, the impedance of the reference path, and whether the reference path has adequate decoupling or filtering. I wouldn't immediately declare it a defect — I'd want to understand the design intent first.

Since the original designer isn't present, I'd look at the design documentation — the schematic notes, the layout guidelines, and any design decisions recorded in the DHF. If the documentation doesn't explain the choice, I'd flag it as a documentation gap and a potential signal integrity issue, and I'd schedule a follow-up with the designer before the review concludes. The key is not to let the review proceed as if the issue doesn't exist, but also not to make a unilateral decision to rework the board without understanding the context.

If the review can't be paused, I'd document the concern as an open action item with a clear owner and a deadline to resolve it before the layout is released for fabrication. I'd also ask the team to evaluate the specific coupling risk: what is the digital signal's edge rate, what layer is the trace on, what is the distance to the reference path, and is there a ground plane between them? If the stackup has a solid ground plane between the digital layer and the analog reference layer, the coupling may be negligible. If they're on adjacent layers with no shielding, that's a much more serious concern.

I'd also use this as a teaching moment for the team. The fact that a layout decision like this can be made without documentation or review is a process gap. I'd suggest adding a layout review checklist that specifically flags cross-domain coupling risks — digital traces near analog reference paths, high-current switching near sensitive analog circuitry, and similar issues — so these are caught systematically rather than by chance.

**Possible follow-ups:**
- What specific measurements or simulations would you request to determine whether the coupling is actually a problem before deciding to rework the board?
- How would you handle a situation where the original designer returns and explains that the trace placement was intentional because of routing constraints, but the analog engineer disagrees with the rationale?

---

## Q4: How would you approach managing a situation where a senior engineer on your team consistently delivers excellent technical work but has a pattern of making design decisions unilaterally and only informing the team after the fact, which has caused rework and frustration among other team members?

**Answer:** I'd start by understanding the root cause of the behavior before addressing it directly. There are several possible reasons a senior engineer works unilaterally: they may believe they have the full context and don't need input, they may have been burned by slow group decision-making in the past, they may not trust the team's technical judgment, or they may simply not realize the impact of their approach on others. The corrective action differs depending on which of these is true.

I'd have a private conversation with the engineer, framed around impact rather than blame. I'd acknowledge their technical strength and the value they bring, then describe the specific pattern I've observed — decisions made without consultation that later required rework or caused frustration. I'd ask for their perspective: do they see the pattern, and what drives it? This isn't a disciplinary conversation; it's a diagnostic one. The goal is to understand their reasoning and to establish that the issue is about process and collaboration, not about their technical competence.

Once I understand the driver, I'd work with them to establish a clear expectation: certain categories of decisions need to go through the team or at least be communicated before implementation. I'd define what those categories are — for example, architecture changes, component substitutions that affect the BOM, or any change that impacts another engineer's work. I'd also make it clear that the issue isn't their technical judgment — it's that the team needs visibility to coordinate, and that unilateral decisions create rework even when the decision itself is technically sound.

I'd also address the team dynamic. If the engineer is making unilateral decisions because they don't trust the team's input, I'd need to build trust by ensuring that design discussions are genuinely productive and that the engineer's concerns are heard. If the issue is that the engineer feels group decision-making is too slow, I'd establish a faster decision framework — for example, a clear escalation path or a "decide and inform" category for low-risk decisions — so they don't feel the only alternative to unilateral action is a slow consensus process.

Finally, I'd monitor the situation over time. If the behavior continues despite the conversation, I'd escalate the consequences — not punitively, but by making the impact of the behavior visible in project reviews and by tying it to the team's overall performance goals. The key is consistency: the engineer needs to see that this is a real expectation, not just a one-time request.

**Possible follow-ups:**
- How would you handle a situation where the engineer acknowledges the pattern but argues that their unilateral decisions have generally been correct and that the team's objections are based on ego rather than technical merit?
- What specific decision categories would you define as requiring team consultation versus those that can be made unilaterally, and how would you communicate that to the rest of the team?

---

## Q5: How would you approach leading a post-mortem after a medical device project missed its delivery deadline by several months, when team morale is low and there's a tendency to blame individual contributors rather than systemic issues?

**Answer:** The first priority is to establish psychological safety. If the post-mortem becomes a blame session, people will either defend themselves or go silent, and we'll learn nothing. I'd start the meeting by explicitly stating that the purpose is to understand the system, not to assign blame — and I'd hold myself to that standard as well. If the project missed its deadline, there are likely systemic factors: unclear requirements, unrealistic estimates, poor cross-team coordination, or inadequate risk identification. Individual mistakes are usually symptoms of those systemic issues, not the root cause.

I'd structure the post-mortem using a formal framework like 8D or a fishbone diagram, but adapted for a project-level review rather than a technical failure. The key is to ask "why" iteratively: Why did the project miss the deadline? Because the firmware integration took longer than expected. Why did it take longer? Because the hardware interface changed late in the cycle. Why did the interface change? Because a requirement was misunderstood. Why was it misunderstood? Because the requirements document was ambiguous and there was no formal traceability. Each "why" moves the discussion from individual blame to systemic causes.

I'd also make sure the discussion covers the full timeline, not just the final months. Often, the seeds of a missed deadline are planted early — in estimation, in scope definition, or in the initial architecture. I'd ask the team to walk through the project timeline and identify where the schedule first started to slip, and what decisions were made at that point. This helps the team see that the problem wasn't a single failure but a series of decisions and conditions that compounded over time.

After the analysis, I'd focus on actionable improvements. The post-mortem should produce a small number of concrete changes — not a long list of recommendations that never get implemented. I'd prioritize the top three to five systemic fixes and assign owners and timelines. I'd also schedule a follow-up in a few months to check whether those changes were actually implemented and whether they're having the intended effect. A post-mortem that doesn't lead to change is just a venting session.

Finally, I'd address morale directly. A missed deadline is demoralizing, especially if the team worked hard and the failure was due to factors outside their control. I'd acknowledge the team's effort, take responsibility for the parts of the failure that were leadership or process failures, and frame the post-mortem as an investment in making the next project more successful. The goal is to leave the team feeling that the process was worthwhile and that their input will lead to real change.

**Possible follow-ups:**
- How would you handle a situation where, during the post-mortem, a specific individual's mistake is clearly identified as a contributing factor — how do you address that without turning the session into a blame game?
- What specific changes to the project planning process would you propose to prevent the systemic issues you identified from recurring on the next project?