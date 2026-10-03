# medical-devices — Day 74

## Q1: How would you approach designing the analog signal chain for a patient-connected sensor whose signal of interest is very small and rides on a large, slowly varying baseline — for example, a biosensor whose useful signal is a fraction of a millivolt on top of a baseline that can drift by hundreds of millivolts?

**Answer:** The core problem is dynamic range versus resolution: the baseline is orders of magnitude larger than the signal, so a single fixed-gain stage would either clip on the baseline or leave the signal buried in the noise floor. I'd structure the chain in stages and decide where to remove the baseline.

First, the front-end. A high-impedance instrumentation amplifier or a precision difference amplifier sets the common-mode rejection, which is what keeps the large baseline from dominating. For patient-connected sensors, the input bias current and input offset drift matter as much as the gain-bandwidth — a low offset-drift amp keeps the baseline from wandering for reasons that have nothing to do with the patient.

Second, baseline removal. There are two broad approaches: AC-couple with a high-pass corner low enough that it doesn't distort the signal of interest, or actively subtract an estimate of the baseline (a DC servo loop or a DAC-driven offset). AC coupling is simpler and more predictable, but the corner frequency has to be chosen against the slowest component of the real signal — if the signal itself has low-frequency content, a high-pass will eat it. An active baseline subtraction keeps the DC information but adds a control loop that itself has to be stable and verified.

Third, gain and filtering. Once the baseline is removed, the residual signal can be amplified into the ADC's input range. Anti-alias filtering belongs before the ADC, and the filter order is a trade-off between roll-off steepness and settling behavior — a higher-order filter that rings can corrupt the very signal you're trying to preserve.

Fourth, the ADC. Resolution, sample rate, and input architecture (differential vs single-ended, SAR vs delta-sigma) all follow from the signal bandwidth and the accuracy target. A delta-sigma converter with built-in gain can simplify the chain but shifts the design problem into the digital domain.

Throughout, I'd keep the design verifiable: every stage should have a defined gain, offset, and noise contribution so the total error budget can be traced back to the accuracy specification. If a stage can't be characterized on the bench, it can't be verified against the requirement.

**Possible follow-ups:**
- How would you decide between AC coupling and an active DC servo loop for baseline removal?
- How would you verify the noise performance of the chain against the accuracy specification without a fully characterized reference source?

## Q2: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** I'd start from the device's intended clinical function and its classification, not from the marketing description. The applicable particular standards are driven by what the device actually does to or for the patient, so a device that monitors and also delivers therapy may fall under two particular standards simultaneously.

The process: identify each distinct clinical function, map each to its candidate IEC 60601-2 standard, and confirm applicability against the scope clause of each standard — the scope tells you what the standard covers and, just as importantly, what it excludes. Where two particular standards both apply, both are in force; you don't get to pick one. The general standard (IEC 60601-1) and the collateral standards (notably 60601-1-2 for EMC, 60601-1-6 for usability, 60601-1-8 for alarms, 60601-1-11 for home healthcare) apply on top of the particulars.

Conflicts are resolved by precedence: the particular standard takes precedence over the general standard for the specific requirement it addresses, and the general standard fills in everything the particular doesn't cover. Where two particular standards impose different limits on the same parameter, that's a genuine conflict that has to be resolved by applying the more stringent requirement, or by documenting the rationale and confirming with the test lab and the regulatory reviewer.

Practically, I'd build a compliance matrix early: rows for each requirement, columns for the standard and clause, with a note on how each is met and where it's verified. That matrix is what makes the submission defensible and what surfaces conflicts before the test lab does.

**Possible follow-ups:**
- How would you handle a situation where a particular standard's requirement is ambiguous and the test lab interprets it differently than you do?
- How would you document the rationale for a standard you've determined does *not* apply?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode of a risk management file is that it becomes a retrospective artifact — assembled to satisfy an audit rather than to drive design decisions. To avoid that, the file has to be a living part of the design process from the start.

I'd structure it around the ISO 14971 process: hazard identification, risk estimation, risk evaluation, risk control, verification of risk control effectiveness, and evaluation of residual risk. Each of those is a section, but the sections are linked by traceability — every hazard traces to a risk control, every risk control traces to a verification activity, and every verification traces to evidence.

The key structural decisions:

First, keep the hazard analysis and the design inputs connected. A hazard that drives a risk control should appear as a design input, so the control is designed in rather than bolted on. That linkage is what makes the file auditable — an auditor can follow a hazard through to the design output and the verification evidence.

Second, maintain the file incrementally. Each design review should update the risk analysis with new hazards, new controls, and new residual risk evaluations. If the file is only touched at milestones, it drifts from the design.

Third, separate the risk management plan, the risk analysis, and the risk management report. The plan defines the process and the acceptance criteria; the analysis is the working document; the report summarizes the residual risk at the end. Keeping them separate makes each one easier to maintain and review.

Fourth, make the acceptance criteria explicit and stable. If the criteria for acceptable residual risk change mid-project, every prior evaluation has to be revisited — so the criteria belong in the plan and should be agreed early.

Finally, treat the file as a communication tool, not just a compliance artifact. When a design decision is contested, the risk file is where the trade-off is documented and where the rationale lives. That's what makes it useful rather than ceremonial.

**Possible follow-ups:**
- How would you handle a hazard that's identified late in the project, after the design is largely frozen?
- How would you decide when a residual risk is acceptable versus when it needs further control?

## Q4: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band failure is a strong clue: it points to a resonance or a coupling path that's tuned to that frequency, rather than a broadband susceptibility. The first step is to characterize the failure precisely — what's the exact frequency, how wide is the band, what's the field strength at which it appears, and what's the observable malfunction. That characterization tells you whether you're looking at a structural resonance, a cable resonance, or a semiconductor junction effect.

Next, I'd localize the coupling path. The usual suspects are cables acting as antennas, enclosure seams or apertures, and PCB traces or planes that resonate at the frequency of interest. A near-field probe sweep across the board and along the cables, with the device operating and monitored, can show where the energy is entering. If the failure disappears when a specific cable is dressed differently or a specific connector is shielded, that's the path.

Then I'd identify the victim. The coupling path leads to a circuit that's misbehaving — often an analog front-end, a reset line, or a communication interface. Once the victim is known, the fix is usually one of: reduce the coupling (shielding, filtering, cable routing, ground stitching), increase the victim's immunity (filtering at the pin, adding hysteresis, improving the reference), or shift the resonance away from the test frequency (changing trace length, adding a damping element).

I'd verify the fix at the same frequency and field strength, then re-run the full immunity sweep to confirm the fix didn't create a new susceptibility elsewhere. A fix that solves one frequency but introduces another is not a fix.

**Possible follow-ups:**
- How would you distinguish a cable resonance from a PCB resonance as the coupling path?
- If the fix requires a board respin, how would you decide between a layout change and an enclosure-level mitigation?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** The first thing I'd do is separate the clinical need from the proposed solution. A usability request often describes a problem — clinicians find a workflow awkward, or a control is hard to reach — and the proposed change is one way to solve it. Sometimes the underlying need can be met without a hardware revision, or with a smaller change than the one proposed. So I'd start by understanding what problem the clinical team is actually trying to solve.

Then I'd assess the change against three axes: safety and efficacy impact, regulatory impact, and schedule impact. A usability change that affects how a clinician interacts with a safety-critical function is not just a usability change — it may trigger a new risk analysis, new usability validation, and potentially a new submission. A change that's purely cosmetic has a much smaller footprint. The regulatory impact is often the deciding factor, because a hardware revision late in development can invalidate verification work that's already been done.

I'd bring the clinical team, the regulatory lead, and the project manager together to evaluate the options. The options are usually: implement the change now and accept the delay, implement a partial change that addresses the most critical part of the need, defer the change to a post-market update, or find a workflow or training mitigation that addresses the need without a design change. Each option has a different risk and schedule profile, and the decision should be made with the trade-offs visible, not by default.

If the change is deferred, I'd document the rationale and the clinical need so it's captured for the next revision — deferring isn't the same as ignoring. If the change is implemented, I'd re-baseline the schedule and the verification plan explicitly, so the impact is understood by everyone.

**Possible follow-ups:**
- How would you decide whether a usability change triggers a new usability validation under IEC 62366?
- If the clinical team disagrees with your recommendation to defer, how would you handle that?