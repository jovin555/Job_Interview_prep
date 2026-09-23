# medical-devices — Day 64

## Q1: How would you approach designing the analog front-end for a patient-connected sensor whose signal of interest is a fraction of a millivolt riding on a baseline that can drift by hundreds of millivolts, while keeping the design verifiable against a specified accuracy limit?

**Answer:** The core problem is dynamic range versus resolution: the baseline drift is orders of magnitude larger than the signal, so a single DC-coupled gain stage would either saturate on the drift or leave the signal buried in the noise floor. I'd start by separating the two concerns architecturally.

First, I'd decide where the baseline is removed. Options are AC coupling (a high-pass corner well below the signal band), a DC servo/active baseline restoration loop, or a differential front-end that rejects the common-mode component before gain. The choice depends on whether the signal has meaningful content near DC — if it does, AC coupling is out and a servo loop that tracks slow drift while preserving the signal band is preferable. The servo's time constant has to be set so it doesn't eat into the lowest frequency of interest.

Second, I'd pick the instrumentation amplifier or differential stage based on input offset, offset drift, input bias current, and CMRR at the frequencies where the common-mode interference lives — not just the DC CMRR on the datasheet. For a patient-connected part, input bias current also matters for patient safety and for electrode offset tolerance.

Third, I'd set the gain and the ADC resolution together. The total noise budget has to be allocated across the sensor, the front-end, the reference, and the ADC, and the target is that the front-end's input-referred noise is comfortably below the resolution the accuracy spec demands, with margin for the reference and quantization. I'd also make sure the anti-alias filter corner and order are chosen against the actual sampling rate and the noise the ADC would otherwise fold back.

Verifiability is a design constraint, not an afterthought. I'd define the accuracy spec in terms of a testable quantity — input-referred error over a stated baseline range, temperature range, and source impedance range — and make sure the bench setup can actually inject a known small signal on a known large baseline. That usually means a characterized signal source and a reference measurement path, and it means the calibration and test points are designed into the board rather than bodged on later.

**Possible follow-ups:**
- How would you decide between AC coupling and a DC servo loop if the signal band extends close to DC?
- How would you verify the front-end's noise performance when the dominant noise source is the sensor itself rather than the electronics?

## Q2: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** I'd start from the device's intended use and its clinical claims, because the particular standards are scoped by function and by the environment of use, not by the product's marketing category. The first step is to enumerate every function the device performs and map each to the relevant part of the 60601-2 series. A combined device typically inherits the obligations of each function's particular standard, so the applicable set is the union, not a single choice.

Once I have the candidate list, I'd read each particular standard's scope clause carefully — some explicitly exclude certain functions, some apply only when the function is the primary purpose, and some have their own definitions of applied parts or essential performance. I'd build a compliance matrix that lists each requirement from the general standard and each particular standard, and marks where they overlap, where one is silent, and where they genuinely conflict.

Conflicts are usually resolved by the principle that the particular standard takes precedence over the general standard for the specific function it governs, but that's a starting point, not a blanket rule — a particular standard can be more or less stringent, and the general standard still applies wherever the particular one doesn't address the topic. Where two particular standards impose different limits on the same parameter, I'd look for the more conservative interpretation unless there's a documented rationale for why one governs, and I'd raise it with the test lab and, if needed, the regulatory reviewer early rather than discovering it at submission.

The practical discipline is to do this mapping during requirements definition, not during test planning. It shapes the design inputs, the risk file, and the verification plan, and it's much cheaper to resolve a scope question on paper than to re-test a finished device.

**Possible follow-ups:**
- How would you document the rationale for which particular standards you decided were not applicable?
- What would you do if a test lab and your own reading of the scope disagreed on whether a particular standard applies?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode I'd design against is the risk file that gets written backwards from a finished design — it's technically complete but it doesn't reflect how decisions were actually made, and it can't survive an audit question about why a particular control exists.

I'd structure it around the ISO 14971 process rather than around a document template. That means the file has a clear chain: intended use and reasonably foreseeable misuse, hazard identification, risk estimation, risk evaluation against the acceptability criteria, risk control, verification of the control's effectiveness, and evaluation of residual risk. Each link should reference the design artifacts that actually carry the information — the requirements, the architecture, the test reports — rather than duplicating them.

The key habit is that risk items are living entries, not a one-time list. When a design decision changes, the risk entry that motivated it should be updated in the same change, and the traceability should run both ways: from hazard to control to verification evidence, and from a design change back to the hazards it might affect. I'd keep the acceptability criteria defined and approved up front, because retrofitting criteria after the fact is where a lot of audit findings come from.

I'd also separate the risk file's structure from its tooling. A spreadsheet or a requirements tool can both work, but the structure has to make it obvious, for any hazard, what controls exist, how each was verified, and what residual risk was accepted and by whom. And I'd make sure the file captures the risk-benefit and residual-risk acceptance decisions explicitly, since those are the parts reviewers and auditors probe hardest.

**Possible follow-ups:**
- How would you handle a hazard that's identified late, after the design is largely frozen?
- How do you keep the risk file consistent with the DHF when both are changing at the same time?

## Q4: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band failure is a strong clue: it points to a resonance or a coupling path that's tuned to that frequency, rather than a broad susceptibility of the whole design. I'd treat it as a signal-integrity and coupling problem first, and resist the temptation to just add shielding everywhere.

I'd start by characterizing the failure precisely — the exact frequency band, the field strength at which it appears, whether it's amplitude- or frequency-dependent, and what the malfunction actually is at the circuit level. Is it a logic upset, an analog measurement error, a reset, a communication dropout? That tells me whether the energy is coupling into a digital net, an analog front-end, a clock, or a cable.

Then I'd work the coupling path. Common candidates are cable harnesses acting as antennas, a resonant trace or loop on the board, a connector or cable shield that's terminated poorly, or a slot or seam in the enclosure that's near a half-wavelength at that frequency. I'd use a near-field probe and, if available, a current probe on the cables to find where the energy is actually entering, and I'd compare the failing frequency against the physical dimensions of the board, cables, and enclosure to see which structure is resonant there.

On the fix side, the options are usually: change the coupling path (cable routing, shield termination, ferrite, connector pinout), change the victim's susceptibility (filtering, decoupling, layout, clock routing, adding hysteresis or filtering in firmware where appropriate), or change the source of the resonance (board dimensions, ground plane integrity, enclosure seams). I'd prefer fixes that address the root coupling path over blanket shielding, because shielding tends to move the problem rather than solve it and can create new issues.

Importantly, I'd verify the fix at the failing frequency and at the band edges, and re-run the full sweep, because a fix that shifts the resonance can create a new failure elsewhere. And I'd document the root cause and the fix in the risk file, since an immunity failure is a risk-control-relevant event.

**Possible follow-ups:**
- How would you distinguish a cable-coupled failure from a board-level resonance?
- If the fix requires a firmware change rather than a hardware change, how would you verify it's robust across units and not just the one on the bench?

## Q5: You're the lead engineer, and during a design review the quality manager insists on adding a risk control measure for a hazard the engineering team considers negligible. The schedule impact would be significant. How would you handle this situation?

**Answer:** I'd treat the disagreement as a question about the risk evaluation, not about whose judgment is better, and try to move the conversation onto the criteria rather than the conclusion.

First, I'd make sure we're actually disagreeing about the same thing. Often the engineering team is estimating severity and probability from a technical standpoint, while the quality manager is weighing the same hazard against the clinical context, the user population, or the regulatory expectation. Those can produce different evaluations without either side being wrong. So I'd ask the quality manager to walk through how they arrived at their estimate, and I'd walk through ours, using the approved acceptability criteria as the shared reference.

If the estimates still diverge, I'd look at whether the difference is in the probability estimate or the severity estimate, because those have different remedies. A probability disagreement can often be resolved with data — field data, test data, literature, or a targeted analysis. A severity disagreement is usually about the clinical consequence, and that's a conversation to have with the clinical or medical affairs representative, not to settle between engineering and quality.

On the schedule question, I'd separate "is this control warranted" from "what does it cost." If the control is warranted, the schedule impact is a planning problem, and I'd look at whether there's a less costly control that achieves the same risk reduction, or whether the control can be phased. If the control isn't warranted under the criteria, I'd say so clearly and document the rationale, because "we didn't have time" is not a defensible reason to skip a control.

The one thing I wouldn't do is let it become a personal standoff. If we can't converge, I'd escalate to the designated risk management authority or the review board with both positions and the criteria laid out, and let the decision be made and recorded. That's not avoiding the decision — it's putting it where the accountability actually sits.

**Possible follow-ups:**
- What would you do if the quality manager's position was based on a regulatory expectation you couldn't find in the standard?
- How would you record a decision to not add a control, so it's defensible later?