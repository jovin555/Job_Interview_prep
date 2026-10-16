# medical-devices — Day 87

## Q1: How would you approach designing the analog signal chain for a patient-connected sensor whose signal of interest is a fraction of a millivolt riding on a baseline that can drift by hundreds of millivolts, while keeping the design verifiable against a specified accuracy limit?

**Answer:** The core problem is dynamic range versus resolution: the baseline drift is orders of magnitude larger than the signal, so if you amplify everything equally you either saturate the front-end or lose the signal in the noise floor of the ADC. I'd structure the chain in stages. First, an instrumentation amplifier or a difference stage with high common-mode rejection to strip the shared baseline as early as possible, before it eats headroom. Second, a high-pass or baseline-restoration stage with a corner frequency chosen to sit below the physiological band of interest but above the drift — the key is that the drift is slow and the signal is faster, so frequency separation is the cleanest tool. Third, gain and anti-alias filtering ahead of the ADC, with the ADC's reference and input range matched so the signal occupies a meaningful fraction of full scale rather than a few LSBs.

Verifiability is where a lot of designs quietly fail. I'd define the accuracy budget up front — input-referred noise, offset, gain error, drift over temperature, and the ADC's own contributions — and allocate it across stages so each block has a testable target. That means specifying input-referred noise density and offset drift as requirements, not just "works." I'd also make sure the design can be characterized with a known signal injected at the input, so you can measure the chain end-to-end rather than trusting simulation. And I'd think about calibration: if the baseline offset varies part-to-part, a factory or self-calibration step may be needed, and that has to be designed in, not bolted on.

**Possible follow-ups:**
- How would you decide between AC coupling and a servo/DC-restoration loop for baseline removal, and what are the failure modes of each?
- If the drift is slow but not purely low-frequency — say it has a thermal component that moves faster than your high-pass corner — how would that change your approach?

## Q2: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** I'd start by mapping the device's intended use and each distinct clinical function to the standard hierarchy. IEC 60601-1 is the general standard and always applies. The 60601-1-xx collateral standards (EMC, usability, alarms, home healthcare environment, etc.) apply based on the device's characteristics and use environment, not its function. The 60601-2-xx particular standards apply per function — so a combined device may legitimately fall under two or more particular standards simultaneously.

The practical approach is to build a standards matrix: rows are the device's functions and characteristics, columns are candidate standards, and each cell records applicability and the specific clauses that impose requirements. For a combined device, I'd expect to apply both particular standards in full unless one explicitly scopes out the other function. Conflicts are usually not true contradictions but differences in stringency or test conditions — for example, one standard may specify a tighter alarm condition or a different leakage limit for a particular applied part. The resolution principle is that the more specific and more stringent requirement governs, and where a particular standard modifies a general-standard clause, the particular standard takes precedence for that clause. I'd document the rationale for each applicability decision and each conflict resolution in the compliance plan, because regulators and test labs will ask, and a defensible written rationale is worth more than an implicit judgment call.

**Possible follow-ups:**
- How would you handle a case where two particular standards specify different test setups for what is physically the same applied part?
- Where would you record the standards applicability decisions so they stay traceable through design changes?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode I'd design against is the risk file as a retrospective artifact — a binder assembled the week before submission that nobody consulted during design. To avoid that, I'd treat the risk management file as a living set of linked records that gets touched at every design review, not a deliverable with a due date.

Structurally, I'd anchor it on ISO 14971's process: risk management plan, hazard identification, risk estimation, risk control, verification of control effectiveness, evaluation of residual risk, and overall residual risk acceptance. The plan comes first and defines scope, criteria for acceptability, and who owns what. Hazard identification should draw from multiple sources — intended use and foreseeable misuse, similar-device history, standards, FMEA — and each hazard should trace to specific risk controls, which in turn trace to verification evidence. The traceability is what makes it auditable: for any hazard, you can walk forward to the control and the test that proves the control works, and backward from any design element to the hazards it addresses.

To keep it maintainable, I'd keep the risk file as structured data or a linked tool rather than prose, so changes propagate. When a design change occurs, the risk assessment is updated as part of the change, not after. And I'd make risk review a standing agenda item in design reviews so it stays current. The test of a good risk file is whether a new engineer can pick it up mid-project and understand why each control exists.

**Possible follow-ups:**
- How would you handle a hazard that's identified late, after the design is largely frozen?
- What's the difference between verifying a risk control's implementation and verifying its effectiveness, and why does it matter?

## Q4: How would you approach designing the filtering strategy for a device that has to pass both conducted and radiated emissions limits while also meeting its own signal integrity requirements?

**Answer:** The tension is that emissions filtering and signal integrity pull in opposite directions: filters that suppress emissions can also attenuate or distort the signals you care about, and the components that help emissions (ferrites, capacitors to ground) can introduce impedance mismatches or resonances that hurt signal quality. So I'd treat it as a co-design problem, not two separate tasks.

I'd start by understanding the noise sources and their frequency content — switching regulators, digital clocks, motor drives, communication interfaces — and the frequency bands where the device's own signals live. The goal is to place filter corner frequencies in the gaps: attenuate the noise bands without touching the signal bands. For conducted emissions, that usually means input filtering on the power entry — common-mode chokes, X and Y capacitors — sized to the switching frequencies and their harmonics. For radiated emissions, it's about loop area, return paths, and cable shielding as much as discrete filters; a tight layout with controlled return paths often does more than adding components.

For signal integrity, I'd keep high-speed or sensitive lines short, impedance-controlled, and referenced to a solid ground plane, and I'd be careful about where I place filtering so it doesn't degrade edge rates or introduce jitter. Where a signal line genuinely needs filtering, I'd use a differential or common-mode approach that preserves the differential signal. The verification loop is iterative: pre-compliance scan, identify the offending frequencies, correlate them to specific sources, and adjust. I'd also budget for the possibility that a fix for emissions creates a signal integrity problem, so both need to be re-verified together, not sequentially.

**Possible follow-ups:**
- How would you decide whether a ferrite bead or an LC filter is the right choice on a given line?
- If a filter you added for emissions causes a signal integrity failure, how would you diagnose which is the root cause?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** My first move is to understand the request precisely rather than react to the headline. "Usability change" can mean anything from a label tweak to a fundamental interaction redesign, and the actual scope determines whether the schedule impact is real. I'd sit down with the clinical lead and the usability engineer to characterize what problem the change solves, how it was identified (clinical feedback, usability testing, a near-miss), and whether it's a safety-relevant issue or a preference. That distinction matters enormously: if it's tied to a use error that could cause harm, it's not really optional, and the conversation shifts to how to do it, not whether.

If it's a genuine improvement but not safety-critical, I'd evaluate options rather than presenting a binary. Can the change be achieved in firmware or labeling without a hardware revision? Can it be partially addressed now and fully in a follow-on revision? Is there a software-only approximation that captures most of the benefit? I'd bring the regulatory lead in early, because the submission impact depends on whether the change affects the design inputs, the verification evidence, or the clinical evaluation — sometimes a change looks large but fits within existing verification.

Then I'd frame the decision for the stakeholders with clear trade-offs: cost, schedule, regulatory risk, and clinical benefit, with a recommendation. If the change is worth doing, I'd look for ways to parallelize — start the hardware revision while continuing submission work on the unaffected portions — rather than assuming the whole project stops. The worst outcome is either unilaterally refusing a clinically motivated request or silently absorbing a schedule slip without surfacing the trade-off.

**Possible follow-ups:**
- How would you decide whether the change requires re-verification of the whole device or just the affected subsystem?
- If the clinical team and the regulatory team disagree on whether the change is necessary, how would you drive a resolution?