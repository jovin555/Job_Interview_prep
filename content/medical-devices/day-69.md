# medical-devices — Day 69

## Q1: How would you approach designing a patient leakage current measurement path for a device that has both BF-type and CF-type applied parts, and how would you decide which measurements are actually required?

**Answer:** The first step is to map the applied parts and their classifications against the standard, because the measurement matrix is driven by classification, not by the number of connectors. BF and CF parts have different limits — CF is roughly an order of magnitude tighter for patient leakage — and the limits also differ between normal condition and single-fault condition, and between AC and DC components. So I'd build a table: each applied part, its classification, the applicable limit under NC and SFC, and the relevant measurement mode (patient leakage to earth, patient leakage with mains on the applied part, etc.).

For the measurement path itself, the key is that the measuring device must present the impedance the standard specifies — the test setup is not a simple multimeter reading. I'd use a leakage current meter or a properly constructed measuring network (the RC network defined in the standard) so the reading reflects the frequency-weighted physiological hazard rather than a raw RMS number. The measurement point is between the applied part(s) and earth, with the device powered at nominal mains voltage plus tolerance, and I'd repeat at the mains frequency extremes the standard requires.

Deciding what's actually required comes down to: which applied parts are simultaneously accessible, whether they're isolated from each other, and whether the device has any patient-connection that could carry mains-derived current under a single fault. If two applied parts are galvanically isolated from each other, you measure them individually; if they share a reference, you have to consider the combination. I'd also confirm whether the device is Class I or Class II, since that changes the earth-referenced paths.

Practically, I'd design the isolation scheme so the measurement passes by construction — adequate creepage/clearance across the barrier, Y-capacitor selection that keeps leakage within limits, and a return path that doesn't couple mains noise onto the patient side. Then I'd verify with the actual test setup rather than trusting a simulation, because stray capacitance and cable routing dominate at these current levels.

**Possible follow-ups:**
- If a BF part passes but a CF part on the same device fails, where would you look first?
- How does the choice of isolation barrier (optocoupler vs. digital isolator vs. capacitive) affect the leakage measurement?

## Q2: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band failure is a strong hint that something in the design is resonant at that frequency — either an intentional or parasitic structure. I'd start by characterizing the failure precisely: sweep the band in small steps, note the exact frequency, the field strength at which it appears, the modulation, and the nature of the malfunction (does it recover, does it latch, does it reset?). That tells me whether it's a coupling problem into an analog front-end, a digital timing problem, or a power-rail disturbance.

Next I'd localize the coupling path. Common culprits: a cable or trace acting as an antenna at a quarter-wave or half-wave resonance, a connector or enclosure seam resonating, a decoupling network with a self-resonance in that band, or a ground plane split that creates a slot antenna. I'd use a near-field probe to sniff the board while injecting the field, and I'd try the classic experiments — ferrite clamps on cables, temporary shielding, changing cable routing — to see which one moves the failure frequency or threshold. If adding a ferrite on a specific cable shifts the resonance, that cable is the antenna.

Once I know the path, the fix is usually one of: damping the resonance (series termination, ferrite, RC snubber), improving the return path (stitching vias, eliminating splits under the sensitive circuit), tightening the decoupling so the rail doesn't sag at that frequency, or adding a filter at the point of entry. I'd be careful not to just add a bulk capacitor — at RF, a large cap can be inductive and make things worse; I'd pick the value based on the frequency and verify with an impedance measurement.

Finally, I'd re-test at the exact failing frequency and at the band edges, and confirm the fix doesn't degrade emissions or signal integrity elsewhere. A fix that passes immunity but pushes emissions over the limit is not a fix.

**Possible follow-ups:**
- How would you distinguish a resonance in the cable from a resonance on the PCB?
- If the failure only appears with a specific modulation (e.g., 80% AM at 1 kHz), what does that tell you?

## Q3: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** The starting point is the intended use and the device's clinical function, not its marketing category. I'd write down each function the device performs and map it to the scope statement of the relevant IEC 60601-2-XX standard. A device that monitors and also delivers therapy will typically fall under two particular standards, and both apply — you don't pick one. The general standard (60601-1) plus the collateral standards (60601-1-X, e.g., EMC, usability, alarms) always apply on top.

Conflicts are rare but real, and the resolution rule is usually stated in the particular standard itself: the particular standard takes precedence over the general standard for the specific requirement it addresses, and the general standard applies where the particular standard is silent. Where two particular standards both apply and appear to conflict, I'd read the scope and the "replacement/amendment" clauses carefully — most particular standards explicitly say which clauses of 60601-1 they replace. If a genuine ambiguity remains, that's a question for the test lab and possibly the standards committee, and I'd document the interpretation in the risk file and the test plan so it's auditable.

Practically, I'd build a requirements matrix: rows are the applicable clauses from 60601-1, the collaterals, and each particular standard; columns are the design inputs and the verification method. That matrix becomes the backbone of the DHF and makes it obvious if a requirement is unaddressed. I'd also flag any requirement that's new relative to a single-function device — for example, a therapy function often brings additional requirements around energy delivery, alarms, and fault conditions that a pure monitor doesn't have.

**Possible follow-ups:**
- How would you handle a situation where a particular standard's test method doesn't match how the device is actually used clinically?
- What would you do if the test lab interpreted a particular standard differently than you did?

## Q4: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The file should be a living artifact that tracks the design as it evolves, not a retrospective summary. I'd structure it around the ISO 14971 process: risk management plan, hazard identification, risk estimation, risk control, residual risk evaluation, and the overall risk/benefit conclusion — with each element traceable to the others and to the design inputs.

The practical key is to make the file the single source of truth for hazards, so that when a design change happens, the risk analysis is updated as part of the change, not after. I'd link each hazard to the design input it drives, the risk control measure that addresses it, the verification evidence that the control is effective, and the residual risk. That traceability is what makes the file auditable — an auditor can follow a hazard from identification through to the evidence that it's controlled.

I'd also keep the file structured so it's reviewable in slices: a hazard log that's readable on its own, a risk control verification section that maps to test reports, and a summary that shows the overall residual risk position. Version control and a clear change history matter, because the file will be reviewed against the design at a specific point in time.

One thing I'd avoid is treating the FMEA as the whole risk file. FMEA is a tool for identifying failure modes, but ISO 14971 is broader — it includes hazards from normal use, misuse, and the clinical environment, not just component failures. So the file needs both the bottom-up FMEA view and the top-down hazard analysis.

**Possible follow-ups:**
- How would you handle a hazard that's identified late in the project, after the design is largely frozen?
- How do you decide when residual risk is acceptable, and who signs off?

## Q5: You're the lead engineer on a medical device project. During a design review, the quality manager insists that a new risk control measure must be added to address a hazard with an estimated risk level that the engineering team considers negligible. The schedule impact would be significant. How would you handle this situation?

**Answer:** First, I'd separate the disagreement about the risk estimate from the disagreement about the control. The quality manager may be seeing something the engineering team isn't — a use case, a patient population, or a failure mode that wasn't in the original analysis. So I'd ask them to walk through their reasoning: what hazard, what sequence of events, what severity and probability, and what evidence supports that estimate. If they can articulate a credible scenario, the estimate probably needs revisiting regardless of schedule.

If, after that discussion, the team still believes the risk is negligible, I'd look at whether the disagreement is really about the estimate or about the acceptance criteria. ISO 14971 allows a manufacturer to define its own acceptability criteria, but those criteria have to be justified and applied consistently. If the quality manager is applying a stricter criterion than the team, that's a policy question, not a technical one, and it should be resolved at the level that owns the policy — not by the lead engineer unilaterally deciding.

On the schedule impact: I'd be honest that it's real, but I wouldn't let schedule drive the risk decision. The right sequence is to resolve the risk question first, then figure out how to absorb the schedule impact — which might mean a design change, a labeling or training control, or a different control that's less costly than the one originally proposed. Sometimes the disagreement is really about the specific control measure, and there's a cheaper effective alternative.

If we can't reach agreement, I'd escalate with a clear written summary of both positions and the evidence, and let the decision be made at the appropriate level with the trade-offs documented. What I wouldn't do is quietly drop the concern or let it become a schedule-driven decision without a record.

**Possible follow-ups:**
- What if the quality manager's concern is valid but the proposed control measure introduces a new usability risk?
- How would you document the resolution so it's defensible in an audit?