# medical-devices — Day 95

## Q1: How would you approach designing the filtering strategy for a device that must pass both conducted emissions and radiated emissions limits under IEC 60601-1-2, while also meeting its own signal integrity requirements?

**Answer:** I'd treat this as a single, layered problem rather than two separate compliance tasks, because the same filter components that fix emissions can degrade signal integrity if applied blindly.

I'd start by separating the noise domains. On the power input, the conducted emissions path is dominated by differential-mode noise from switching converters and common-mode noise coupled through parasitic capacitances to chassis. A two-stage approach usually works best: a differential-mode filter (X-capacitors plus a common-mode choke sized for the switching frequency) close to the source, and a common-mode filter (Y-capacitors to chassis plus a second choke) at the connector. The Y-capacitor value is bounded by earth leakage current limits under IEC 60601-1, so the leakage budget has to be allocated early — you can't just add capacitance until emissions pass.

For radiated emissions, the dominant mechanisms are usually cables acting as antennas and slots/apertures in the enclosure. I'd address this with source suppression first (slowing switching edges with gate resistors or snubbers, spread-spectrum clocking where the standard permits it), then cable termination and ferrites, then enclosure design. Filtering at the connector is far more effective than filtering at the die.

The signal-integrity tension comes in when the same common-mode chokes and capacitors sit on high-speed or sensitive lines. A choke that helps at 30 MHz can add insertion loss and skew at the signal's own bandwidth, and Y-capacitors on a differential pair can unbalance it. So I'd keep the emissions filter physically and electrically separate from signal nets, use differential filtering on differential signals, and verify with both a spectrum scan and an eye diagram or BER measurement — not just one or the other.

The key discipline is to define the emissions and signal-integrity budgets up front, pre-compliance test early with a near-field probe and a LISN, and iterate on the filter before the formal lab booking, because filter redesign at the lab is expensive and slow.

**Possible follow-ups:**
- How would you decide whether to solve a radiated emissions problem with filtering versus shielding versus source suppression?
- How do you keep the Y-capacitor leakage current contribution within the IEC 60601-1 earth leakage limit while still getting enough common-mode attenuation?

## Q2: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** I'd start from the device's intended use and clinical function, not from its marketing category, because the particular standards are organized around what the device does to or for the patient. I'd enumerate each distinct clinical function, then map each to its likely IEC 60601-2 part — for example, a monitoring function and a therapy-delivery function will each have a candidate particular standard, and a combined device may need to satisfy both.

The next step is to read each candidate standard's scope clause carefully. Scope clauses define what the standard covers and sometimes explicitly exclude combined devices or defer to another part. That's where most of the ambiguity lives, so I'd document the scope analysis rather than assume.

Where two particular standards both apply and appear to conflict, I'd resolve it in this order: first, check whether one standard explicitly states precedence or cross-references the other; second, apply the more stringent requirement where they genuinely conflict, since meeting the stricter one generally satisfies both; third, where the conflict is about test method rather than limit, run both methods and document the rationale. Any residual conflict or interpretation question goes to the regulatory affairs team and, if needed, to the test lab for a pre-submission opinion — I wouldn't resolve a standards conflict unilaterally in the DHF.

I'd also record the standards applicability analysis as a formal design input, because it drives the verification test plan and the regulatory submission, and it needs to be traceable and defensible.

**Possible follow-ups:**
- What would you do if a particular standard's test method is physically incompatible with the other function being active at the same time?
- How would you document the standards applicability decision so it survives a regulatory audit?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode I'd design against is the "risk file as a retrospective artifact" — a binder assembled the week before submission that nobody used during design. To avoid that, I'd make the risk management file a living set of linked records that the engineering team actually works from.

Structurally, I'd anchor it on the ISO 14971 process: risk management plan first (scope, responsibilities, risk acceptability criteria, review points), then hazard identification, risk estimation, risk control, verification of control effectiveness, and overall residual risk evaluation. The plan is important because it defines the acceptability criteria up front — without that, every risk decision becomes an argument later.

The practical key is traceability links. Each hazard should trace to the design input or architecture element it relates to, to the risk control measure, to the verification evidence that the control works, and to the residual risk decision. I'd keep these as structured records — a requirements/risk management tool or at minimum a controlled spreadsheet with stable IDs — so that when a design change happens, you can query which hazards and controls are affected. That's what makes the file useful during the project rather than just at the end.

I'd also build in scheduled risk reviews at design milestones and tie them to design reviews, so hazard identification is refreshed as the design matures and as new information (test failures, supplier changes, usability findings) arrives. DFMEA feeds into this naturally as a structured hazard-identification input.

Finally, I'd keep the file's structure aligned with the DHF so that risk controls appear as design inputs and their verification appears as design outputs — that way the two documents stay consistent instead of drifting apart.

**Possible follow-ups:**
- How would you handle a design change late in the project that invalidates a previously verified risk control?
- What's the difference between verifying a risk control's implementation and verifying its effectiveness, and why does it matter?

## Q4: How would you approach verifying that a medical device's firmware meets IEC 62304 requirements for a Class C software safety classification?

**Answer:** Class C means a software failure could contribute to a hazardous situation with unacceptable risk, so the verification burden is the highest tier: the standard expects rigorous unit-level verification, full traceability from requirements through code to tests, and evidence of structural coverage.

I'd start with the software safety classification rationale itself — documenting why the software is Class C, which hazards it can contribute to, and which software items are actually safety-critical versus which are lower-risk. IEC 62304 allows segregation: if you can architecturally separate a safety-critical item from non-critical items and show the separation holds, you can classify them differently. That architectural segregation is worth designing for deliberately, because it focuses the heavy verification effort where it matters.

For the Class C items, I'd build a verification strategy covering unit verification (with structural coverage analysis — statement, branch, and where justified MC/DC), integration testing, and system testing, all traced to software requirements. The requirements themselves need to be verifiable and complete, because traceability is only as good as what it traces to. I'd also plan for the standard's required activities around detailed design, unit implementation, and the anomaly/problem resolution process — defects found in testing need to be tracked, evaluated for safety impact, and closed with evidence.

A practical point: structural coverage analysis often reveals dead code or unreachable branches, and each one needs a documented disposition — either a test that reaches it or a justified rationale for why it's not reachable. That disposition work is a common audit finding if skipped.

I'd also make sure the software release criteria are defined in advance: which verification activities must be complete, what coverage thresholds apply, and what the sign-off chain is. That turns "is the software done?" into a checklist rather than a judgment call.

**Possible follow-ups:**
- How would you justify a segregation argument that lets part of the software be classified lower than Class C?
- What would you do if structural coverage analysis showed a safety-critical branch that no test could reach?

## Q5: You're the lead engineer, and during a design review the quality manager insists on adding a risk control measure for a hazard that the engineering team considers negligible. The schedule impact would be significant. How would you handle this situation?

**Answer:** I'd treat this as a risk-acceptability disagreement to be resolved with evidence, not as a schedule fight, because the quality manager is exercising a legitimate role and dismissing the concern outright would be the wrong move.

First I'd make sure we're actually arguing about the same thing. I'd ask the quality manager to walk through the hazard, the harm, the estimated severity and probability, and the basis for their estimate. Often these disagreements come down to different assumptions about probability of occurrence or about whether a sequence of events is credible — and once those assumptions are on the table, the disagreement either narrows or becomes a specific, testable question.

Then I'd bring it back to the risk management plan's predefined acceptability criteria. If the team's estimate places the risk below the acceptability threshold and the quality manager's estimate places it above, the real issue is the estimate, not the conclusion. I'd propose resolving that with data: review field data from similar devices, check whether the hazard appears in the DFMEA or in relevant standards' guidance, and if it's genuinely uncertain, consider a small verification activity to characterize it rather than a full design change.

On schedule, I'd be honest about the impact and present options rather than a flat no — for example, whether the control can be implemented in firmware or as a manufacturing/test step rather than a hardware revision, or whether it can be deferred to a later revision with a documented interim risk assessment. If the quality manager still believes the risk is unacceptable, that's a decision that should escalate to the risk management review with both positions documented, not be settled by the lead engineer's authority. The record of how the disagreement was resolved belongs in the risk management file either way.

**Possible follow-ups:**
- What would you do if the quality manager's position was based on a severity estimate you thought was implausible but couldn't disprove?
- How would you document a decision to defer a risk control to a future revision so it's defensible to a regulator?