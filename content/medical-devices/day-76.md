# medical-devices — Day 76

## Q1: How would you approach designing the patient leakage current measurement path for a device that has both BF-type and CF-type applied parts, and how would you decide which measurements are actually required?

**Answer:** The starting point is to read the applied-part classifications off the intended-use and risk documents, because the classification drives everything downstream. BF and CF parts have different limits, and the tighter limit governs the whole measurement plan — a CF part is held to a much lower patient leakage current than a BF part, so if a device has both, you cannot design to the BF number and assume the CF part is covered.

For the measurement path itself, the key idea is that patient leakage current is defined as the current flowing through the patient connection to earth (or to another patient connection, depending on the measurement configuration), so the test setup has to model the patient as a defined impedance network and the device as it would actually be connected in use. That means:

- **Identify every applied part and its classification** from the labeling and risk file, and note which parts are simultaneously accessible to the patient.
- **Determine the applicable measurement configurations** — normal condition and single-fault condition, and for each, whether the measurement is from the applied part to earth, from one applied part to another, or through the patient-connected network. The standard defines these configurations; the job is to map the device's actual applied parts onto them rather than inventing a setup.
- **Build a measurement jig that matches the standard's patient impedance network** rather than a generic current probe, and verify the jig itself against a known reference before trusting any reading.
- **Decide which measurements are actually required** by asking: which applied parts are patient-connected, which are simultaneously accessible, and which fault conditions are credible for this device. A part that is never simultaneously accessible with another may not need the inter-part measurement; a part that is only ever used alone may not need the multi-part configuration. The risk file and intended-use description should drive this, not a blanket "test everything" approach.
- **Document the rationale** for including or excluding each configuration, because a reviewer will ask why a given measurement was omitted.

The practical trap is treating the measurement as a single number when it is really a matrix of configurations, and then discovering late that one configuration was never characterized. Building the matrix early, and tracing each cell back to a requirement, keeps the verification defensible.

**Possible follow-ups:**
- How would you decide whether a given applied part is BF or CF in the first place, and what would you do if the classification were ambiguous?
- If a measurement came back close to but under the limit, how would you decide whether that margin is acceptable?

## Q2: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band, reproducible failure is actually a gift compared to an intermittent one, because reproducibility means you can characterize it. The first step is to stop treating it as a pass/fail event and start treating it as a characterization problem: sweep the band finely, at the same field strength and modulation, and record exactly where the malfunction starts and stops, what the malfunction actually is (reset, corrupted reading, display glitch, communication dropout), and whether it depends on device orientation, cable routing, or the state of the device when the field is applied.

From there, the diagnosis usually falls into a few categories:

- **Resonance in a cable or harness.** A cable whose length is near a quarter-wavelength at the offending frequency becomes an efficient antenna and couples energy into the enclosure or onto a signal line. The fix is often a ferrite, a different cable route, or a shorter cable — but the diagnosis is confirming that the failure follows the cable, not the board.
- **A resonant structure on the PCB or in the enclosure.** A slot, a long unbroken ground return, or a poorly stitched ground plane can form a resonant cavity or a slot antenna. The diagnostic is to probe the field distribution or use a near-field probe to find where the energy is actually coupling in.
- **A susceptible node in the signal chain.** An analog front-end with high impedance, a long unshielded trace, or a reference node with inadequate decoupling can rectify RF and shift a bias point. The diagnostic is to monitor the suspect node while the field is applied and see whether the disturbance appears there first.
- **A firmware or watchdog interaction.** Sometimes the RF causes a transient that the firmware mishandles — a spurious interrupt, a bus error, a watchdog reset — and the "malfunction" is really the firmware's response to a transient rather than the transient itself.

The resolution follows the diagnosis: if it is coupling, address the coupling path (shielding, filtering, grounding, cable routing); if it is a susceptible node, address the node (impedance, decoupling, filtering); if it is a firmware response, address the response (better error handling, more robust watchdog strategy). The important discipline is to confirm the mechanism before changing anything, because "add a ferrite and hope" produces a fix that may not survive a design change.

**Possible follow-ups:**
- How would you decide whether the fix belongs in hardware or firmware?
- What would you do if the fix worked on the bench but the failure reappeared at the test house?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode of a risk management file is that it becomes a retrospective artifact — a binder assembled in the last weeks before submission, disconnected from the design decisions that actually shaped the product. The way to avoid that is to treat the file as a living traceability structure that is updated as decisions are made, not as a deliverable that is written once.

Practically, that means a few structural choices:

- **Anchor the file to the hazard, not to the document.** Each hazard should have a stable identifier, a description, an estimate of severity and probability, the risk control(s) applied, and the verification evidence that the control works. When a design changes, you update the affected hazard entries rather than rewriting the whole file.
- **Link each risk control to a design output and a verification activity.** If a risk control is "the enclosure prevents access to live parts," that control should trace to a specific design feature and a specific verification test. If it does not trace, it is an assertion, not a control.
- **Keep the risk file and the DHF cross-referenced but distinct.** The DHF holds the design inputs, outputs, verification, and validation; the risk file holds the hazard analysis and risk controls. They reference each other, but conflating them makes both harder to maintain.
- **Review the file at defined points** — design reviews, major design changes, post-market feedback — rather than only at submission. A risk file that has not been touched since the last review is a signal that it is not being used.
- **Record the rationale for residual risk acceptance** at the time the decision is made, with the people who made it. Reconstructing that rationale months later is both harder and less credible.

The test of a good risk file is whether a new engineer could pick it up, understand why a given control exists, and know what would need to change if the design changed. If the file only makes sense to the person who wrote it, it is not doing its job.

**Possible follow-ups:**
- How would you handle a risk control that turns out to be ineffective during verification?
- What would you do if a hazard were identified late in the project, after most of the design was frozen?

## Q4: How would you approach deciding whether a given software failure in a medical device should be classified as a safety-related failure requiring formal risk controls, versus a non-safety usability or reliability issue?

**Answer:** The classification should not be made by intuition about how bad the failure "feels" — it should be made by tracing the failure to a hazardous situation and asking whether it could lead to patient harm. The framework is:

1. **Describe the failure precisely.** Not "the display froze" but "the display stopped updating the heart rate value while the underlying monitoring continued." The precision matters because different descriptions lead to different hazard analyses.
2. **Ask whether the failure can contribute to a hazardous situation.** A hazardous situation is a circumstance in which a person is exposed to a hazard. If the failure cannot, under any credible sequence of events, contribute to a hazardous situation, it is not a safety-related failure — it may still be a reliability or usability issue worth fixing, but it does not need the same formal treatment.
3. **If it can contribute, estimate the severity of the potential harm** and the probability of the sequence occurring. This is where the risk file earns its keep: the severity and probability estimates should already exist for the hazards the device addresses, and the failure should be mapped onto them.
4. **Decide the control strategy based on the risk level.** A high-severity, non-negligible-probability failure needs a formal risk control — which might be a design change, a detection mechanism, a mitigation in the user interface, or a combination. A low-severity or negligible-probability failure may be acceptable with documentation of the rationale.
5. **Document the decision and the reasoning**, including the cases where the answer was "not safety-related." The negative decisions are as important to record as the positive ones, because they show the analysis was done.

The common failure mode is to classify by symptom rather than by consequence: a cosmetic glitch and a missed alarm can both present as "the screen did something unexpected," but only one of them is safety-related. The discipline is to always trace back to the hazardous situation.

**Possible follow-ups:**
- How would you handle a failure that is safety-related only in combination with another failure?
- What would you do if the team disagreed on whether a failure could contribute to a hazardous situation?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** The first move is to separate the request from the proposed solution. The clinical team is asking for an outcome — a usability improvement — and the hardware revision is one way to achieve it, not necessarily the only way. So the conversation starts with: what specifically is the usability problem, what is the clinical consequence of not fixing it, and what is the minimum change that would address it?

From there, the evaluation has a few dimensions:

- **Clinical significance.** Is this a nice-to-have or does it address a use error that could lead to harm? If it is the latter, it is not really optional — it becomes a risk management question, and the schedule impact is a consequence of a safety need rather than a preference.
- **Regulatory implications.** A change that affects the user interface may affect the usability engineering file, the risk analysis, and potentially the submission itself. The regulatory lead needs to be in the conversation early, because "delay the submission" and "submit and then change" have very different regulatory consequences.
- **Alternative implementations.** Can the outcome be achieved with a firmware change, a labeling change, a training change, or a change to a non-critical mechanical part? A hardware revision is the most expensive option and should be the last resort, not the first.
- **Cost of delay versus cost of not changing.** A three-month delay has real cost, but so does shipping a device with a known usability problem — particularly if it later generates complaints or a field correction. The comparison should be explicit, not assumed.
- **Decision ownership.** This is not a decision the lead engineer should make alone. It needs the clinical lead, the regulatory lead, the program manager, and probably the quality lead, with a clear owner for the final call.

The response to the clinical team should be honest about the trade-off and specific about what is being asked: "Here is what we can do within the current schedule, here is what would require a delay, and here is what we recommend and why." The worst outcome is a vague "we'll look into it" that leaves everyone uncertain and the schedule quietly slipping.

**Possible follow-ups:**
- How would you handle it if the clinical team insisted the change was safety-critical but the risk analysis did not support that?
- What would you do if the change could be made in firmware but would require re-verification of a large portion of the software?