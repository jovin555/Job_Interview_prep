# medical-devices — Day 83

## Q1: How would you approach designing the analog signal chain for a patient-connected sensor whose signal of interest is a fraction of a millivolt riding on a baseline that can drift by hundreds of millivolts, while keeping the design verifiable against a specified accuracy limit?

**Answer:** The core problem is dynamic range: the useful signal is tiny relative to both the baseline drift and the common-mode environment, so the architecture has to reject the large slow-moving component before the ADC rather than relying on digital post-processing to recover it. I'd start by separating the requirements into three numbers — the signal bandwidth, the baseline drift bandwidth, and the required resolution at the signal of interest — because those determine whether a DC-coupled or AC-coupled front-end is appropriate.

For a biosensor with a slowly drifting baseline, a high-pass stage (or AC coupling) placed early removes the drift but also removes any DC diagnostic information and introduces its own settling and low-frequency noise concerns, so the corner frequency has to sit well below the signal band but well above the drift band. Instrumentation amplifier front-ends give good common-mode rejection, but CMRR degrades with frequency and with source impedance imbalance, so I'd match the input network carefully and consider a driven-shield or active-guard arrangement if the source impedance is high or unbalanced.

From there, the gain staging matters: putting most of the gain in the first stage improves the noise contribution of later stages, but it also reduces headroom for the residual baseline and any transient. I'd typically split gain across two stages, with the first stage sized so the worst-case baseline plus signal still fits inside the supply rails with margin. For the ADC, a delta-sigma converter with a higher oversampling ratio can push quantization noise out of band and relax the analog anti-alias filter, which is often easier to make verifiable than a steep analog filter near the signal band.

Verifiability is the part that's easy to underestimate. I'd want the accuracy budget broken down explicitly — sensor tolerance, amplifier offset and drift, gain error, reference tolerance, ADC INL/DNL, and noise — with each term either measured or bounded by a datasheet limit over the operating temperature range. Then the verification plan tests the assembled chain against a reference signal source at the specified accuracy limit, not just individual stages, because errors that look negligible in isolation can stack. I'd also include a drift test over time and temperature, since baseline drift is exactly the failure mode the architecture is meant to handle.

**Possible follow-ups:**
- How would you decide between a fully analog high-pass stage and a digital baseline-tracking approach, and what would make you change your mind?
- If the accuracy budget showed the reference was the dominant error term, how would you address that?

## Q2: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** I'd start from the intended clinical function and the device's classification rather than from the standard list, because the particular standards are organized around device types and clinical use, not around the engineering subsystems. The first step is to write down every clinical function the device performs and map each to the relevant particular standard — for a combined monitor-and-therapy device, that likely means one particular standard for the monitoring function and another for the therapy function, plus any collateral standards that apply to both.

Once I have the candidate list, I'd confirm applicability against the scope clause of each standard, because scope language is where "this applies to devices that..." either includes or excludes the device. If a function is genuinely novel and no particular standard covers it, the general standard plus the relevant collateral standards govern, and the risk management file has to carry the burden of justifying that no particular standard applies.

Conflicts are the harder part. Where a particular standard tightens or overrides a general-standard requirement, the particular standard takes precedence for that function — that's the normal hierarchy. Where two particular standards impose different requirements on a shared subsystem (for example, different alarm or accuracy requirements for the monitoring and therapy functions), I wouldn't try to pick one; I'd design to the more stringent requirement where they can be reconciled, and where they genuinely can't, I'd document the conflict, the rationale for the chosen interpretation, and get it reviewed with regulatory early rather than late. The worst outcome is discovering the conflict during submission.

I'd also keep a traceability matrix that maps each requirement to its source standard and clause, so that when a standard is revised or a reviewer questions an interpretation, the reasoning is visible. That matrix is also what makes the design history file defensible.

**Possible follow-ups:**
- How would you handle a situation where a particular standard's test method isn't practical for your device's form factor?
- What would you do if a notified body disagreed with your interpretation of which particular standard applies?

## Q3: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band failure is a strong clue: it usually points to a resonance or a coupling path that's efficient only at that frequency, rather than a broad susceptibility problem. I'd resist the temptation to immediately add filtering, because that treats the symptom and can mask the actual coupling mechanism.

First I'd characterize the failure precisely — what exactly malfunctions, at what field strength and modulation, and whether it's repeatable with the device in a fixed orientation. Then I'd try to localize the coupling path. Common candidates are cable harnesses acting as antennas, enclosure seams or apertures that resonate near that frequency, and PCB structures (ground plane resonances, trace lengths that are a fraction of a wavelength) that couple energy into a sensitive node. A quick way to narrow it down is to repeat the test with cables dressed differently, with the enclosure partially shielded, or with the device in different orientations — if the failure moves or disappears, that tells you which path dominates.

Once I have a hypothesis, I'd confirm it with a near-field probe or a bench setup that injects at the suspect frequency, so I can iterate faster than in the chamber. The fix depends on the mechanism: if it's a cable, common-mode chokes, ferrites, or improved shield termination may help; if it's an aperture or seam, gasketing or changing the seam geometry; if it's a PCB resonance, layout changes such as stitching vias, better reference plane continuity, or relocating the sensitive node. On the firmware side, if the malfunction is a transient logic upset rather than a hard failure, defensive measures like watchdog supervision, input validation, and state recovery can improve robustness, but I'd treat those as complementary to fixing the coupling, not as a substitute.

Throughout, I'd keep the fix verifiable: re-test at the failing frequency and at the band edges, and confirm the fix didn't shift the problem elsewhere. EMC fixes frequently move the resonance rather than eliminate it.

**Possible follow-ups:**
- How would you decide whether a firmware mitigation is acceptable versus requiring a hardware change?
- If the failure only occurs at one orientation, how would you interpret that?

## Q4: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode I'd want to avoid is the risk file becoming a retrospective artifact — a binder assembled before submission that nobody consulted during design. The way to prevent that is to make the risk file a living part of the design process, with entries created and updated as decisions are made, not after.

Structurally, I'd organize it around the ISO 14971 process: hazard identification, risk estimation, risk evaluation, risk control, verification of risk control effectiveness, and evaluation of residual risk and overall benefit-risk. Each hazard entry should link to the design inputs it affects, the risk control measures chosen, and the verification evidence that those measures work. That linkage is what makes the file auditable — a reviewer can follow a hazard from identification through to the evidence that it's controlled.

Practically, I'd keep the risk file in a tool that supports traceability rather than a static document, so that when a design change occurs, the affected hazards and controls are visible. I'd also establish a cadence — risk reviews at design milestones, and a rule that any design change triggers a risk impact assessment — so the file stays current rather than drifting out of sync with the design.

Two things I'd pay particular attention to: first, that risk control verification is genuinely independent of the design (testing the control actually works, not just that it was implemented), and second, that residual risk evaluation is documented with rationale, because that's where reviewers focus. I'd also make sure the file captures hazards that were considered and dismissed, with reasoning, since that demonstrates the analysis was thorough rather than convenient.

**Possible follow-ups:**
- How would you handle a situation where a risk control measure is added late in the project and affects already-verified design outputs?
- What would you do if the risk file and the design history file started to diverge?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** My first instinct would be to understand the request fully before reacting to the schedule impact, because "usability change" can mean anything from a label tweak to a fundamental interaction redesign, and the right response depends on which it is. I'd want to know what clinical problem the change solves, how often it occurs, and what the consequence is if it isn't addressed — because a change that prevents a use error with patient safety implications is a different conversation than one that's a convenience improvement.

If the change is safety-relevant, the calculus shifts: a use-related hazard that isn't addressed is a risk management issue, and the schedule impact has to be weighed against the risk of shipping a device with a known usability problem. In that case I'd work with the clinical and quality teams to characterize the risk properly and document the decision, whatever it is.

If the change is not safety-relevant, I'd evaluate whether there's a path that captures most of the benefit without the full hardware revision — a firmware or labeling change, a change that can be deferred to a future revision, or a partial implementation. I'd also want to understand the true cost of the delay: sometimes "three months" is a rough estimate that shrinks once the actual scope is defined, and sometimes it's optimistic.

Whatever the outcome, I'd make the trade-off explicit and get it decided at the right level, not absorbed silently by engineering. That means presenting the options with their costs and risks — proceed as planned, implement the change now with the delay, or defer — and letting the people who own the clinical, regulatory, and business consequences make the call with full information. I'd also document the decision and its rationale, because if the change is deferred, that decision needs to be defensible later.

**Possible follow-ups:**
- How would you handle it if the clinical team and the regulatory team disagreed on whether the change was necessary?
- If the decision was to defer, how would you make sure the issue is tracked and revisited rather than forgotten?