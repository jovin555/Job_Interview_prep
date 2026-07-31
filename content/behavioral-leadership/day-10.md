# behavioral-leadership — Day 10

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a hardware design flaw or user misuse, and the two possible causes point to very different corrective actions?

**Answer:** The first priority is to resist the temptation to commit to either hypothesis prematurely, because the corrective actions diverge so significantly — one path leads to a design change with full verification and regulatory impact, the other leads to labeling or training updates. I would structure the investigation to systematically gather evidence that discriminates between the two possibilities rather than evidence that confirms either one.

I'd start by defining the physical evidence needed. For a hardware flaw, I'd look for patterns that correlate with specific device revisions, serial number ranges, or environmental conditions. For user misuse, I'd look for patterns that correlate with specific user behaviors, workflow steps, or usage contexts. The key is to identify what data would be conclusive for each hypothesis before collecting it.

I would also examine the device itself if it's available — a physical inspection often reveals whether the failure mode is consistent with a design issue or with a particular use pattern. For example, in a battery-powered device, if the reported issue involves unexpected shutdown, I'd want to know whether the battery voltage at the time of failure was within the expected operating range, which would point toward a design issue, or below it, which might point toward a usage pattern.

Throughout this, I'd keep the investigation team cross-functional — hardware, firmware, clinical affairs, and field service — because each group sees different evidence. I'd document everything in a format that supports a formal root-cause analysis, because in a medical device context, the investigation itself becomes part of the design history file and may be reviewed by regulators.

**Possible follow-ups:**
- How would you handle the situation if the evidence is genuinely ambiguous and you need to make a decision about whether to issue a field correction while the investigation continues?
- What role would the risk management file play in guiding your investigation priorities?

---

## Q2: How would you approach building a technical mentoring relationship with a junior engineer who is highly capable but tends to avoid asking for help until they are significantly stuck, often wasting days on problems that a brief conversation would have solved?

**Answer:** The core issue here is not technical capability but psychological safety and communication norms. A junior engineer who avoids asking for help is often worried about appearing incompetent, or they may have come from an environment where struggling independently was valued. The fix is to normalize the act of asking early and often.

I would start by having a direct conversation about how I work — making it explicit that I expect to be consulted early, that "I'm stuck" is a perfectly acceptable status update, and that the cost of asking early is far lower than the cost of discovering a wrong approach after days of work. I would also model this behavior myself by verbalizing my own uncertainties and asking questions in front of the team, so it becomes a visible norm rather than a stated rule.

Structurally, I would introduce a lightweight check-in cadence — not a formal status meeting, but a brief daily or every-other-day touchpoint where the expectation is to discuss blockers, not just report progress. I would also try to understand what kind of help they respond to best. Some engineers want a hint and then to work it out themselves; others want a full walkthrough. Tailoring the response to their preference makes asking for help feel less costly.

Finally, I would watch for the pattern where they come to me after days of struggle and make a point of responding with curiosity about their process rather than criticism about the delay. The goal is to reinforce that the learning is in the conversation, not in the solo struggle.

**Possible follow-ups:**
- How would you handle it if the junior engineer continues to avoid asking for help despite your efforts, and you start seeing quality issues in their work?
- How would you balance giving them enough autonomy to grow versus stepping in early enough to prevent wasted effort?

---

## Q3: How would you approach evaluating whether a design change made during the prototyping phase of a medical device should be carried forward into the formal design verification phase, when the change was made informally and its rationale is only partially documented?

**Answer:** This is a common and tricky situation because the informal change may be perfectly sound technically, but it hasn't been through the rigor required for a medical device design history file. The first step is to assess what we actually know about the change — what was modified, why, and what evidence exists that it works as intended. If the rationale is only partially documented, I would reconstruct it through conversation with the engineer who made the change, review of any test data or notes, and comparison against the original design intent.

The key question is whether the change is substantively different from what was originally specified. If it's a minor adjustment — say, a resistor value change to improve a threshold margin — the path forward might be to document the rationale, assess the impact on the risk management file, and update the design specification accordingly. If it's a more significant change — say, a different sensor interface or a revised power architecture — then it may need to go back through design input review before it can be formally carried forward.

I would also consider whether the change was validated in the context where it will actually be used. A change that works in a lab prototype may not have been tested under the full range of environmental, EMC, or usability conditions required for design verification. If the change affects safety-critical parameters, I would want to see evidence that it doesn't introduce new failure modes or degrade existing mitigations.

The decision ultimately comes down to whether the change can be properly documented, risk-assessed, and verified within the existing project timeline, or whether it needs to be treated as a new design input that triggers additional development work. I would present this trade-off clearly to the project team rather than making the call unilaterally.

**Possible follow-ups:**
- How would you handle a situation where the engineer who made the change has left the company and the rationale is genuinely lost?
- What criteria would you use to decide whether the change is significant enough to require a full design review versus a documented deviation?

---

## Q4: How would you approach managing a situation where a senior engineer on your team is technically excellent but has a pattern of making design decisions unilaterally and only informing the team after the fact, which has caused rework and frustration among other team members?

**Answer:** The first thing I would do is understand the engineer's motivation. Some engineers work this way because they genuinely believe they're being efficient — they see consultation as overhead. Others do it because they lack confidence in the team's ability to contribute meaningfully, or because they've been rewarded in the past for being decisive. The intervention needs to be tailored to the underlying cause.

I would have a private conversation where I acknowledge their technical strength and then describe the specific impact of the unilateral decisions — not in terms of process violation, but in terms of concrete consequences: rework, missed deadlines, and erosion of team trust. The goal is to make the cost of their approach visible to them, because they may genuinely not see it.

I would then propose a specific behavioral change: for decisions that affect other team members' work, they need to consult before finalizing, not after. I would be concrete about which decisions require consultation — anything that affects interfaces, schematics, layout constraints, or firmware behavior — and which ones they can continue to make independently. This gives them a clear boundary rather than a vague expectation.

I would also look at the system around them. If the team has no established design review process, or if decisions are typically made in informal conversations that not everyone is part of, then the engineer's behavior may be a symptom of a broader communication gap. Strengthening the formal decision-making process — for example, requiring design change notifications or architecture reviews for significant decisions — can help without making it personal.

Finally, I would monitor whether the behavior changes over the next few projects. If it doesn't, I would escalate through the normal performance management process, because the impact on team effectiveness and morale is real and won't resolve on its own.

**Possible follow-ups:**
- How would you handle it if the engineer pushes back and argues that their unilateral approach has produced better results than the team's collaborative process?
- How would you rebuild trust with the rest of the team if they've already become frustrated with this engineer's behavior?

---

## Q5: How would you approach preparing a team for a regulatory audit when you know that several design decisions were made informally during development and the design history file does not fully capture the rationale behind them?

**Answer:** The first step is to assess the gap honestly. I would review the design history file against the actual development history — talking to the engineers who were involved, reviewing meeting notes, and looking at email threads — to identify which decisions are undocumented or under-documented. The goal is to build a complete picture of what the auditors might ask about, not to hide anything.

Once I know the gaps, I would prioritize them by risk. Some undocumented decisions are low-risk — for example, a minor component substitution that doesn't affect safety or performance. Others are high-risk — for example, a change to a safety-related parameter or a deviation from a standard design practice. The high-risk gaps need to be addressed before the audit, either by reconstructing the rationale through conversation and documentation, or by acknowledging the gap and having a credible explanation ready.

I would also prepare the team for how to handle questions about these gaps during the audit. The worst thing an engineer can do is to improvise an answer that contradicts the documentation or to become defensive. I would coach them to answer honestly — "this decision was made informally, and here's the technical rationale" — and to direct the auditor to the risk management file or design input documents where the intent is captured.

If there are gaps that genuinely cannot be reconstructed, I would prepare a statement that acknowledges the limitation and describes what was done to verify the design despite the documentation gap. In a medical device context, the verification evidence often matters more than the documentation of intent — if the design demonstrably meets its requirements, the missing rationale is a quality system finding rather than a safety finding.

Finally, I would use the audit preparation as an opportunity to improve the documentation process going forward, so that the same gaps don't recur. The audit is a forcing function — it's the right time to establish a culture where design decisions are documented as they're made, not reconstructed later.

**Possible follow-ups:**
- How would you handle a situation where the auditor specifically asks about a decision that you know was made informally and you don't have a credible technical rationale to offer?
- How would you balance being transparent about documentation gaps with the need to present the design in the best possible light during the audit?