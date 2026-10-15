# medical-devices — Day 86

## Q1: How would you approach designing the patient leakage current measurement path for a device that has both BF-type and CF-type applied parts, and how would you decide which measurements are actually required?

**Answer:** The starting point is not the test bench, it's the classification and the standard. IEC 60601-1 defines leakage current limits by the type of applied part and by the condition being tested, so before touching a meter I'd build a matrix: for each applied part, its classification (BF vs CF), whether it's intended for direct patient contact, and the applicable limits under normal condition (NC) and single fault condition (SFC). CF parts carry tighter limits than BF parts, and the limits also differ between patient leakage, patient auxiliary current, and earth leakage — these are distinct measurements with distinct test setups, not interchangeable.

For the measurement path itself, the key is that the test network and the reference point must match what the standard specifies. Patient leakage current is measured from the applied part, through the specified measuring device (the RC network defined in the standard), to earth — and for a floating applied part the measurement is referenced differently than for an earthed one. I'd make sure the applied parts can be individually isolated during test so I'm measuring one at a time and not inadvertently summing currents through a shared return. If the device has multiple applied parts that are galvanically connected internally, that changes what "per applied part" even means, and I'd document the rationale.

Deciding which measurements are required comes down to: every applied part classification gets tested in every condition the standard requires, plus the combinations the standard calls out (for example, mains voltage applied to an applied part under SFC). I'd also check whether the device has any non-applied-part accessible conductive surfaces that fall under enclosure leakage current. The output of this exercise is a test matrix that a reviewer can trace back to specific clauses — that traceability is as important as the numbers.

**Possible follow-ups:**
- How would you handle a device where two applied parts of different classifications share a common internal reference?
- What would you do if a measurement sits just under the limit but the margin is uncomfortably small?

## Q2: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band failure is a strong clue — it usually means something in the design is resonant or has a specific susceptibility at that frequency, rather than a broad shielding or grounding deficiency. I'd start by characterizing the failure precisely: sweep around the band to find the exact center, the bandwidth, and the field strength threshold at which it appears. That tells me whether it's a sharp resonance (narrow, threshold-like) or a broader coupling issue.

Then I'd try to localize the coupling path. Common candidates are cable harnesses acting as antennas, a connector or cable shield that's terminated poorly, a slot or seam in the enclosure near a quarter-wavelength of the offending frequency, or a semiconductor junction that's demodulating the RF into a low-frequency disturbance the firmware then misinterprets. I'd use near-field probes to sniff where the energy is actually getting in, and I'd try targeted mitigations one at a time — ferrite on a specific cable, additional shield grounding, a small RC snubber on a susceptible input — to see which one moves the threshold.

On the resolution side, the fix depends on the mechanism. If it's a cable resonance, I'd address the termination and routing. If it's a demodulation issue at an analog input, I'd add filtering at the point of entry. If it's firmware misinterpreting a transient, I'd look at whether the input needs debouncing or plausibility checks — but I'd be careful not to paper over a hardware susceptibility with software, because the standard is about the device not becoming unsafe or essential-performance-degrading, and a software mask can hide a real problem. I'd also verify the fix doesn't just shift the resonance elsewhere.

**Possible follow-ups:**
- How would you distinguish a cable-resonance problem from an enclosure-aperture problem?
- If the fix requires a board respin, how would you decide whether to proceed or to seek a test deviation?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode I want to avoid is the risk file as a retrospective artifact — a binder assembled the week before submission that nobody consulted during design. To prevent that, I'd treat the risk management file as a living set of linked artifacts that gets touched every time the design changes, not a document with a start and end date.

Structurally, I'd anchor it on the ISO 14971 process: hazard identification, risk estimation, risk evaluation, risk control, verification of control effectiveness, and evaluation of residual risk and overall benefit-risk. Each hazard traces to specific design inputs, and each risk control traces to a design output and a verification activity. That traceability is what makes the file auditable — a reviewer should be able to pick any hazard and follow it forward to the control and the evidence that the control works, and backward to the design input that drove it.

Practically, I'd keep the risk analysis in a tool or structured format that supports linking, not a static spreadsheet that gets copy-pasted. I'd establish a cadence where risk review is a standing agenda item at design reviews, so new hazards surface while there's still time to address them. And I'd make sure the file captures the reasoning behind decisions — why a particular risk was judged acceptable, what alternatives were considered — because that reasoning is often what an auditor or reviewer actually wants to see, and it's the first thing lost when the file is assembled after the fact.

**Possible follow-ups:**
- How would you handle a risk that's identified late, after the design is largely frozen?
- What's your approach to keeping the risk file consistent when the same hazard appears in multiple subsystems?

## Q4: How would you approach deciding whether a given software failure in a medical device should be classified as a safety-related failure requiring formal risk controls, versus a non-safety usability or reliability issue?

**Answer:** The deciding question is whether the failure could contribute to an unacceptable risk to the patient or operator, not whether the failure is annoying or whether it's "in the software." I'd work from the hazard analysis rather than from the failure in isolation: does this failure mode, on its own or in combination with other failures, lead to a hazardous situation that the risk analysis has identified? If yes, it's safety-related and needs a risk control with verification. If no, it may still be a defect worth fixing, but it's handled through normal defect tracking rather than as a safety control.

The subtlety is that the same failure can be safety-related in one context and not another. A display glitch that shows a stale value might be a usability issue if the clinician has other independent indications, but it could be safety-related if that display is the sole means of communicating a critical alarm. So I'd always ask: what's the clinical consequence, and is there an independent means of detecting or mitigating the failure? That's why the analysis has to be grounded in the intended use and the clinical workflow, not just the code.

I'd also be careful about the trap of classifying something as "just usability" to avoid the overhead of a formal control. If there's genuine uncertainty about whether a failure is safety-related, the conservative path is to treat it as safety-related until the analysis shows otherwise — and to document that reasoning, because the classification decision itself is part of the risk file. IEC 62304's software safety classification is a related but distinct concept; I'd keep the two aligned so the software architecture and the risk controls tell a consistent story.

**Possible follow-ups:**
- How would you handle a disagreement between the software lead and the quality lead on whether a failure is safety-related?
- What evidence would you want to see before downgrading a failure from safety-related to non-safety?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** My first move is to understand the request properly before reacting to the schedule impact — what clinical problem is it solving, how often does it occur, and what's the consequence if it isn't addressed? A usability change that prevents a use error with patient harm potential is a very different conversation from a change that makes a workflow marginally more convenient. I'd want the clinical team to articulate the risk or the evidence behind the request, not just the preference.

Then I'd lay out the options honestly. There's usually a spectrum: a full hardware revision is one end, but there may be a firmware-only mitigation, a labeling or training change, a change that can be deferred to a post-launch revision, or a partial change that addresses the core risk without the full scope. I'd work with the clinical, regulatory, and program leads to evaluate each option against the risk it addresses and the cost it imposes. If the change genuinely addresses a safety-relevant use error, the schedule impact may be the right trade — but that decision belongs to the program with the risk information in front of it, not to me unilaterally.

If the decision is to proceed, I'd want the change controlled through the design change process: updated design inputs, updated risk analysis, re-verification of affected requirements, and a clear plan for what regulatory impact it has. If the decision is to defer, I'd want that documented with the rationale, so it's a conscious risk decision rather than an oversight. Either way, the worst outcome is letting the request sit unresolved while the schedule quietly erodes.

**Possible follow-ups:**
- How would you handle it if the clinical team and the program manager disagreed on whether the change was necessary?
- What would you do if the change could be made in firmware but would require re-validating a safety-critical function?