# medical-devices — Day 75

## Q1: How would you approach designing the patient leakage current measurement path for a device that has both BF-type and CF-type applied parts, and how would you decide which measurements are actually required?

**Answer:** The starting point is to stop thinking of "leakage current" as one test and instead map the measurement matrix that the standard actually defines. IEC 60601-1 treats leakage current as several distinct quantities — earth leakage, enclosure/touch current, and patient leakage — and each is measured under both normal condition (NC) and single-fault condition (SFC), with different limits depending on the applied part classification. So the first design task is to enumerate the applied parts, assign each a classification (BF vs CF), and then build a matrix of measurement points: which applied part, which condition, which fault state, and which limit applies. CF parts carry tighter limits than BF, so a device with both will have at least two different limit sets to satisfy.

For the measurement path itself, the key is that the measuring device (MD) must be inserted in a way that reflects the standard's defined network — typically a human-body impedance model — and that the return path is well-defined and low-impedance. I'd design the test setup so that each applied part can be individually isolated and connected to the MD without disturbing the others, which usually means a breakout harness or test fixture rather than probing the finished enclosure. The reference earth point matters too: the MD's reference must be tied to the same earth the device sees, otherwise the reading is meaningless.

Deciding which measurements are required is a matter of reading the standard's applicability clauses rather than testing everything. If a device has no earth connection (Class II), earth leakage is not applicable. If an applied part is not patient-connected in the sense the standard defines, patient leakage may not apply. The trap is over-testing and under-testing simultaneously — running every test "just in case" wastes lab time, while skipping a test because it "seems" inapplicable can invalidate the submission. I'd document the applicability rationale for each measurement in the test plan so a reviewer can follow the logic.

**Possible follow-ups:**
- How would you handle a device where one applied part is BF and another is CF, and the CF part's limit is violated only when the BF part is also connected?
- What would you do if a measurement is marginally over the limit and you suspect the test setup itself is contributing to the reading?

## Q2: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band failure is almost always a resonance or a coupling path that's tuned to that frequency, not a broad susceptibility problem. The first thing I'd do is characterize the failure precisely: at what field strength does it start, how wide is the band, and is the malfunction repeatable at the same frequency with the same field orientation and cable arrangement. That tells me whether I'm looking at a structural resonance (enclosure, cable, PCB trace) or a component-level susceptibility.

Next I'd try to localize the coupling path. The usual suspects are cables acting as antennas — patient cables, power cords, sensor leads — and the fix is often at the cable interface rather than the PCB. I'd temporarily add ferrites or shielding at different points and see which one shifts or eliminates the failure. If the failure moves when I move a cable, the cable is the antenna. If it persists with cables dressed differently, I'd look at the enclosure seams and apertures, since a slot or seam can act as a slot antenna at a specific frequency.

On the PCB side, I'd look for high-impedance nodes that are sensitive at that frequency — an unbypassed reference, a long trace to a high-impedance input, a poorly decoupled supply rail. The fix is usually a combination of better decoupling at the affected node, a small series element to break the resonance, and possibly a layout change to shorten the return path. I'd also check whether the failure is a true functional upset or just a display/communication glitch, because that changes the risk assessment and the acceptable fix.

The important discipline is to fix the root cause rather than just adding shielding until it passes. A shield that masks a resonance may pass the test but leave the device vulnerable in the field, and it adds cost and mechanical complexity. I'd want to understand the mechanism well enough to explain why the fix works.

**Possible follow-ups:**
- How would you decide whether a ferrite or a layout change is the more appropriate fix?
- If the failure only occurs at one specific field orientation, what does that tell you about the coupling path?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode I'd want to avoid is the "risk file as a retrospective artifact" — a binder assembled in the last month before submission that nobody used during design. The way to avoid that is to make the risk management file a living part of the design process, with entries created and updated as design decisions are made, not after.

Structurally, I'd start with the risk management plan, which defines scope, responsibilities, the risk acceptability criteria, and how risk will be evaluated. That plan is the contract for the rest of the file. Then the hazard analysis: identify hazards, estimate severity and probability, and record the risk. The key discipline is that every risk control measure gets traced to a design input or a verification activity, so the file shows not just "we identified this hazard" but "here is the evidence the control works."

I'd keep the file organized so that each hazard has a clear thread: hazard → hazardous situation → harm → risk estimate → control measure → verification of control → residual risk → acceptance decision. That thread is what an auditor or reviewer follows, and if any link is missing, the file looks incomplete even if the design is sound. I'd also version-control it alongside the design, so changes to the design trigger a review of the affected risk entries rather than a separate, disconnected update.

The practical habit that keeps it maintainable is to review the risk file at every design review, not just at milestones. If a design review changes a circuit or a firmware behavior, the risk file should be updated in the same cycle. That way the file reflects the design as it actually is, and the final submission is a matter of confirming completeness rather than reconstructing history.

**Possible follow-ups:**
- How would you handle a situation where a risk control measure is added late in the project and the verification evidence isn't yet available?
- What would you do if a design change invalidates a previously accepted residual risk?

## Q4: How would you approach deciding whether a given software failure in a medical device should be classified as a safety-related failure requiring formal risk controls, versus a non-safety usability or reliability issue?

**Answer:** The decision hinges on whether the failure can contribute to a hazardous situation that could result in harm to the patient or operator. That's a risk-based question, not a code-based one, so I'd start by tracing the failure to its potential clinical consequence. If the failure can cause the device to withhold therapy, deliver incorrect therapy, fail to alarm on a critical condition, or present misleading information that a clinician would act on, it's safety-related. If the failure only affects convenience features, logging, or non-critical display elements, it may be a reliability or usability issue.

The IEC 62304 software safety classification is a useful frame here, but it's a classification of the software item or system, not of an individual failure. A Class B or C software system can still have failures that are non-safety-related, and a Class A system can have failures that matter. So I'd separate the two questions: what is the software safety classification of this item, and is this specific failure safety-related within that context.

For the safety-related failures, the response is formal: a risk control, a verification activity, and evidence that the control is effective. For non-safety failures, the response can be lighter — a defect fix, a usability improvement, a reliability action — but it still needs to be tracked and closed. The trap is treating a failure as "just a bug" because it's easy to reproduce or because it's in a non-critical module, when its downstream effect is actually safety-relevant. I'd want the decision documented with the reasoning, so it's defensible if a reviewer asks why a particular failure wasn't treated as safety-related.

**Possible follow-ups:**
- How would you handle a failure that is safety-related only in combination with another independent failure?
- What evidence would you want to see before accepting that a failure is genuinely non-safety-related?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** The first thing I'd do is separate the clinical need from the proposed solution. The clinical team is asking for a change because of a problem they're seeing or anticipating; the hardware revision is one way to address it, but it may not be the only way. So I'd want to understand the underlying need — what task is difficult, what error is possible, what workflow is being disrupted — before accepting that a hardware revision is required.

Once I understand the need, I'd evaluate the options along three axes: clinical benefit, regulatory impact, and schedule impact. A usability change that reduces a realistic use error is not something to dismiss lightly, because use errors are a recognized source of harm and regulators expect them to be addressed. But a change that adds convenience without reducing a meaningful risk may not justify a submission delay. I'd want the clinical team to articulate the risk or the workflow problem in concrete terms, and I'd want to know whether the change is a "must" or a "would be nice."

If the change is genuinely necessary, I'd look for the least disruptive way to deliver it. Sometimes a firmware change, a labeling change, or a training change can address the same need without touching hardware. If a hardware revision is truly required, I'd scope it as narrowly as possible and look at whether it can be introduced as a post-market change rather than holding the initial submission. That decision depends on the regulatory pathway and the risk of the change, so it's a conversation with regulatory, not a unilateral engineering call.

The response to the clinical team should be transparent about the trade-off, not a flat yes or no. I'd explain what the change costs in schedule and what it delivers in clinical value, and I'd ask them to help prioritize. That keeps the relationship constructive and makes the decision a shared one rather than an engineering veto.

**Possible follow-ups:**
- How would you handle a situation where the clinical team insists the change is essential but regulatory advises against delaying the submission?
- What would you do if the usability issue could be mitigated by training rather than a design change?