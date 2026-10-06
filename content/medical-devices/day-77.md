# medical-devices — Day 77

## Q1: How would you approach designing the analog front-end for a patient-connected sensor whose signal of interest is a fraction of a millivolt riding on a baseline that can drift by hundreds of millivolts, while keeping the design verifiable against a specified accuracy limit?

**Answer:** The core problem is dynamic range versus resolution: the baseline drift is orders of magnitude larger than the signal, so a single DC-coupled gain stage would either saturate on the drift or leave the signal buried in the noise floor. I'd start by separating the two concerns architecturally. First, an instrumentation amplifier or a low-noise differential front-end with high common-mode rejection handles the differential signal and rejects what it can of the common-mode baseline. Then I'd remove the residual baseline with either AC coupling (a high-pass corner set well below the signal band of interest) or an active baseline-restoration loop — a servo that senses the slow average and feeds a correction back into the amplifier's reference pin. The choice between them depends on whether the signal has meaningful content near DC; if it does, AC coupling is out and the servo approach is required.

For the signal chain itself, I'd pick an ADC whose resolution and noise density are adequate for the smallest signal I need to resolve, not just the full-scale range, and I'd budget the error terms explicitly: front-end input-referred noise, amplifier offset drift over temperature, ADC quantization and INL, and reference stability. The reference is often the quietest place to spend money — a noisy or drifting reference directly corrupts the measurement.

Verifiability is the part that's easy to under-plan. I'd define the accuracy limit as a testable specification with a defined test method, then make sure the design can actually be measured against it: a known signal source, a way to inject a calibrated baseline offset, and test points that let me characterize the front-end independently of the rest of the system. If the accuracy claim can't be demonstrated with available equipment, that's a design problem, not just a test problem — I'd either add the instrumentation or restructure the verification approach. I'd also characterize drift over temperature and time early, because those are the terms most likely to blow the budget late.

**Possible follow-ups:**
- How would you decide between an analog baseline-restoration servo and doing the correction digitally after the ADC?
- What would you put in the error budget, and how would you allocate the total accuracy limit across the stages?

## Q2: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** I'd start from the device's intended clinical function and its classification, not from the standards list. The general standard, IEC 60601-1, always applies. The 60601-2-xx particular standards are scoped by device type, so the first step is to map each function the device performs to the particular standard that governs that function — a monitoring function and a therapy function will typically each pull in a different particular standard. I'd document that mapping explicitly, because it's exactly the kind of thing a reviewer will ask about, and it needs to be defensible.

Where two particular standards both apply, they generally coexist rather than conflict — each adds requirements on top of the general standard for its own function. The real work is identifying where they impose different or overlapping requirements on shared subsystems: for example, alarm requirements, applied-part classification, or leakage current limits that differ because one function has a different patient contact configuration. When requirements genuinely appear to conflict, I'd go back to the normative text and the rationale, and where it's still ambiguous, I'd consult the standards themselves and, if needed, a test lab or regulatory consultant before locking the design. The conservative resolution is usually to meet the more stringent requirement where it doesn't compromise the other, and to document the reasoning either way.

The output of this exercise should feed directly into the design inputs and the risk management file, so the applicable standards aren't a separate compliance artifact bolted on at the end — they shape the requirements the design is verified against.

**Possible follow-ups:**
- How would you handle a case where the two particular standards specify different alarm priority schemes for the same alarm condition?
- Where would you record the standards applicability decision so it stays traceable through design changes?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode I'd design against is the risk file that gets written backwards from a finished design — it looks complete but doesn't actually drive anything, and it falls apart the moment the design changes. To avoid that, I'd treat the risk management file as a living set of linked artifacts rather than a single document, and I'd establish the structure before detailed design starts.

The backbone is the ISO 14971 process: hazard identification, risk estimation, risk control, verification of control effectiveness, and evaluation of residual risk. I'd keep each of those as its own traceable record, with explicit links — each hazard traces to the design inputs or architecture elements it affects, each risk control traces to the design output that implements it and the verification evidence that confirms it works, and each residual risk traces to the acceptance decision and who made it. That linkage is what makes the file auditable: a reviewer can follow any hazard through to the evidence that it's controlled.

Practically, I'd keep the risk analysis current by tying it to the design review cadence — every design review includes a check that new hazards introduced by design changes have been assessed and that existing controls still hold. I'd also make sure the file captures the reasoning, not just the conclusions: why a particular severity or probability was assigned, why a control was chosen over an alternative, why a residual risk was accepted. That reasoning is what a reviewer or an auditor actually needs, and it's the first thing lost when the file is reconstructed after the fact.

**Possible follow-ups:**
- How would you handle a design change late in the project that invalidates a previously verified risk control?
- What's the difference between verifying a risk control's implementation and verifying its effectiveness, and how would you capture both?

## Q4: How would you approach designing the filtering strategy for a device that has to pass both conducted and radiated emissions limits while also meeting its own signal integrity requirements?

**Answer:** The tension is that emissions filtering and signal integrity pull in opposite directions on the same nodes — anything that attenuates high-frequency energy leaving the board also attenuates the signal you're trying to preserve. So I'd start by separating the problem into two domains: the interfaces where filtering is required for compliance, and the internal signal paths where integrity is the priority.

For conducted emissions, the noise leaves through the power input and through I/O cables, so the filtering belongs at those boundaries — a combination of common-mode chokes, X and Y capacitors, and differential-mode inductors on the power input, sized against the applicable limits and the switching frequencies present in the design. The key is to place the filter at the connector so noise doesn't couple onto cables after the filter, and to keep the filter's return paths tight so the filter itself doesn't become a radiator. For radiated emissions, the dominant mechanisms are usually cables acting as antennas and fast edges on internal traces, so the strategy is often more about layout and edge control — minimizing loop areas, controlling return paths, and slowing edges where the timing budget allows — than about adding filter components.

For signal integrity, I'd keep the compliance filtering out of the sensitive analog and high-speed digital paths entirely, and instead address those paths with layout discipline: controlled impedance, proper referencing, and separation from noisy switching nodes. Where a signal genuinely has to cross a noisy boundary, I'd use a targeted approach — a differential pair, a common-mode choke that's transparent to the differential signal, or an isolation barrier — rather than a blanket low-pass filter that would degrade the signal.

The two goals are reconciled by budgeting: decide up front which nodes are allowed to be filtered and how much, and verify both emissions and signal integrity against that budget rather than discovering the conflict during compliance testing.

**Possible follow-ups:**
- How would you decide where to place a common-mode choke on a high-speed differential link without degrading the eye diagram?
- If a design passes conducted emissions but fails radiated, where would you look first?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** My first move is to understand what problem the clinical team is actually trying to solve, because the requested change is often one proposed solution to a need that might have other solutions. I'd get the clinical stakeholder to describe the use scenario and the failure or difficulty they're seeing, and I'd check whether it's a genuine safety or usability issue versus a preference. That distinction drives everything that follows — a safety-related usability issue has a different weight than a nice-to-have.

If it's a real issue, I'd evaluate the options rather than accepting the binary of "do the hardware revision" or "say no." There may be a firmware or labeling change that addresses the same need without touching hardware, or a change that can be staged — implemented in a future revision while the current submission proceeds. I'd also quantify the actual impact: what the hardware change costs in schedule, what it does to the regulatory submission, and whether the submission can proceed in parallel or has to be reworked. That gives the decision-makers real trade-offs instead of a vague "it'll be late."

Then I'd bring it to the right forum — a design review or change control board with clinical, quality, regulatory, and program representation — because a decision with regulatory and schedule consequences shouldn't be made by engineering alone. I'd present the options with their risks and let the group decide, documenting the rationale either way. If the decision is to defer, I'd make sure the need is captured in the risk file and the post-market or next-revision plan so it isn't lost. If the decision is to proceed, I'd re-baseline the schedule and the regulatory plan explicitly rather than pretending the original dates still hold.

**Possible follow-ups:**
- How would you handle it if the clinical team believes the issue is safety-related but the risk assessment concludes it isn't?
- What would you do to keep the team's morale and momentum intact if the decision is to delay the submission?