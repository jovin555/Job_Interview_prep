# medical-devices — Day 68

## Q1: How would you approach designing the analog front-end for a patient-connected sensor whose signal of interest is a fraction of a millivolt riding on a baseline that can drift by hundreds of millivolts, while keeping the design verifiable against a specified accuracy limit?

**Answer:** The core problem is dynamic range: the useful signal is tiny compared to the baseline offset, so the first priority is to remove the baseline before it consumes the ADC's range. I'd start by separating the problem into three stages — electrode/sensor interface, baseline rejection, and gain/filtering — and treat each as a block with its own error budget that rolls up into the overall accuracy specification.

At the interface, the goal is a high, stable input impedance and a well-defined return path, because a drifting baseline often originates in the electrode-skin interface or the sensor's own bias network rather than in the electronics. I'd choose an instrumentation amplifier or a purpose-built analog front-end with good common-mode rejection, and I'd pay close attention to input bias current and its drift, since that current flowing through source impedance converts directly into offset drift.

For baseline rejection, the classic approach is AC coupling with a high-pass corner low enough not to attenuate the signal band of interest, but that only works if the baseline drift is genuinely slow relative to the signal. If the drift and the signal overlap in frequency, a simple high-pass won't separate them, and I'd need either a servo/DC-restore loop that actively nulls the baseline, or a modulation/demodulation scheme. The trade-off is that a servo loop introduces its own settling behavior and can interact with the signal, so it has to be analyzed for stability and for how it behaves during saturation or a step change in baseline.

For gain and filtering, I'd distribute gain across stages rather than putting it all in one place, so that no single stage saturates on the baseline before it's removed, and so that noise contributions are dominated by the first stage. Anti-alias filtering belongs before the ADC, and I'd want the filter's passband and the ADC's sample rate chosen together so that out-of-band noise doesn't fold back into the signal band.

The verifiability part is what makes this a medical design rather than just a good analog design. I'd define the accuracy limit in terms of the actual clinical parameter, then work backward to an input-referred error budget covering offset, gain error, noise, drift over temperature and time, and the reference's own stability. Each term gets a testable allocation. Then I'd design the verification to inject known signals — a small signal on a large, slowly varying baseline — and confirm the output stays within the budget across the specified operating conditions. I'd also want a way to test the baseline-rejection stage in isolation, because if the whole chain is only tested end-to-end, a failure gives you no information about which block is responsible.

**Possible follow-ups:**
- How would you decide between a hardware servo loop and a digital baseline-estimation algorithm in firmware?
- How would you verify the front-end's behavior when the baseline drifts faster than the servo loop can track?

## Q2: How would you approach deciding whether a given software failure in a medical device should be classified as a safety-related failure requiring formal risk controls, versus a non-safety usability or reliability issue?

**Answer:** The deciding factor isn't how the failure feels or how often it occurs — it's whether the failure can contribute to a hazardous situation, and whether that hazard can lead to harm. So I'd work from the risk management process rather than from a judgment call in the moment.

The first step is to trace the failure to its effect on the device's clinical function. A software failure that causes the device to stop displaying data is a reliability problem if the device also alarms and the clinician has other means of monitoring; the same failure is safety-related if it silently suppresses an alarm or causes the device to display a plausible but wrong value that a clinician would act on. The distinction usually comes down to whether the failure is detectable by the user and whether it can lead to an incorrect clinical decision or a missed intervention.

I'd also look at it from the perspective of the software safety classification under IEC 62304. The classification is driven by the harm that a software failure could contribute to, considering the risk controls external to software. If the software is the only barrier preventing a hazardous situation, that pushes the classification up; if hardware or procedural controls independently mitigate the hazard, that can lower it. This is why the classification has to be made with the risk management file open, not in isolation.

For anything that lands on the safety-related side, the failure needs to be captured as a hazard, analyzed for its causes, and addressed with risk controls that are then verified. For non-safety issues, they still belong in the defect tracking and reliability processes, but they don't need the same formal risk-control treatment. The important discipline is to document the reasoning either way, because a later reviewer — or a regulator — will want to see why a given failure was or wasn't treated as safety-related.

One practical caution: it's easy to under-classify by reasoning "the user would notice." That assumption is itself a risk control, and it needs to be justified with usability evidence, not asserted. If the only thing standing between a software failure and patient harm is that a clinician happens to notice, that's a control worth examining carefully.

**Possible follow-ups:**
- How would you handle a disagreement between the software lead and the quality lead on a borderline classification?
- How does the classification affect the rigor of your unit and integration testing?

## Q3: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** I'd start by describing the device in terms of its clinical functions and its physical/electrical characteristics, because the particular standards are organized around device types and around the specific hazards those types present. A combined-function device can fall under more than one particular standard, and the general standard (60601-1) plus the collateral standards (like 60601-1-2 for EMC, 60601-1-6 for usability, 60601-1-8 for alarms, 60601-1-11 for home healthcare) apply on top of whichever particular standards are relevant.

The practical approach is to build a matrix: list each function, identify the particular standard that governs it, and note the clauses that apply. For a monitoring-plus-therapy device, that might mean one particular standard for the monitoring function and another for the therapy function, with the general and collateral standards applying throughout. I'd confirm the list against the device's intended use statement and against the regulatory pathway for each target market, because the applicable standards can differ by jurisdiction even when the underlying IEC text is the same.

Conflicts between the general standard and a particular standard are resolved by the principle that the particular standard takes precedence for the specific requirements it addresses — it exists precisely because the general standard's requirements aren't sufficient or appropriate for that device type. But "takes precedence" doesn't mean the general standard stops applying; it means that where the particular standard specifies a different limit, test method, or requirement, that one governs for that aspect, and the general standard continues to apply everywhere the particular standard is silent.

Where two particular standards both apply and appear to conflict, I'd look at whether they're actually addressing the same hazard or different ones. Often they're addressing different hazards and can both be satisfied. If there's a genuine conflict — for example, different leakage current limits for different applied parts — the resolution is usually to apply the more stringent requirement to the shared element, or to design the device so that the two functions are electrically separated enough that each can meet its own standard. That's a design decision as much as a compliance one, and it's better made early, because retrofitting separation late in development is expensive.

I'd document the standard applicability analysis as part of the design inputs, with a rationale for each inclusion and exclusion. That analysis is what a reviewer will check first, and it's also what protects the project from discovering a missed standard during submission.

**Possible follow-ups:**
- How would you handle a device where a particular standard's test method doesn't map cleanly onto your device's architecture?
- How would you keep the standard applicability analysis current as the device's intended use evolves?

## Q4: How would you approach designing the filtering strategy for a device that has to pass both conducted and radiated emissions limits while also meeting its own signal integrity requirements?

**Answer:** The two goals pull in opposite directions: emissions compliance wants to attenuate high-frequency energy leaving the device, while signal integrity wants to preserve the high-frequency content the device's own signals depend on. The way to reconcile them is to treat filtering as a system-level problem with a clear separation between the frequencies that carry information and the frequencies that carry noise, and to place the filtering where it does the most good with the least harm to signal integrity.

I'd start by understanding the noise sources and their paths. Conducted emissions are dominated by switching power supplies and by high-speed digital return currents, and they travel out through the power leads and through any cable that acts as an antenna. Radiated emissions are driven by the same currents but couple through board traces, cables, and enclosure apertures. So the first line of defense is usually layout and grounding: keeping return currents local, minimizing loop areas, and controlling the impedance of the return path. Filtering is what you add after the layout has done what it can.

For conducted emissions, the standard approach is a multi-stage filter on the power input — common-mode chokes plus differential-mode and common-mode capacitors — with the corner frequency chosen to attenuate the switching frequency and its harmonics while passing the line frequency and any low-frequency transients the device must tolerate. The filter has to be designed with the actual source and load impedances in mind, because a filter's attenuation depends on the impedance mismatch it sees; a filter that looks good on paper can be ineffective or even resonant in the real circuit.

For radiated emissions, filtering on cables and connectors is often more effective than filtering on the board, because cables are the most efficient antennas. Ferrites, common-mode chokes, and feed-through capacitors at cable entries can suppress the common-mode currents that radiate. On the board itself, series termination on high-speed lines and careful control of edge rates can reduce the high-frequency content without destroying signal integrity, as long as the edge rate is still fast enough for the timing budget.

The signal-integrity side is where the trade-off has to be managed explicitly. Every filter you add to a signal line adds impedance, capacitance, and possibly skew, all of which can degrade the signal. So I'd separate the design into "signals that must be filtered" and "signals that must not be," and for the latter I'd rely on layout, shielding, and grounding rather than on filtering. For the former, I'd choose filter topologies that attenuate the noise band without intruding on the signal band, and I'd verify the filter's effect on the signal with the same rigor as its effect on emissions.

The verification strategy is to test emissions and signal integrity together, not separately, because a change that fixes one can break the other. Pre-compliance testing early, with the actual cables and enclosure, is worth far more than a late-stage fix.

**Possible follow-ups:**
- How would you decide whether a filter belongs on the board or in the cable assembly?
- How would you diagnose an emissions failure that only appears when a specific cable is connected?

## Q5: You're the lead engineer, and during a design review the quality manager insists on adding a risk control measure for a hazard the engineering team considers negligible. The schedule impact would be significant. How would you handle this situation?

**Answer:** The first thing I'd do is separate the disagreement into two parts: whether the hazard's risk is actually negligible, and whether the proposed control is the right response to it. Those are different questions, and conflating them is what turns a technical discussion into a schedule fight.

On the risk question, I'd go back to the risk management file and look at how the risk was estimated — the severity, the probability of occurrence, and the basis for both. If the engineering team's "negligible" judgment rests on an assumption that hasn't been documented or verified, that's a gap worth closing regardless of the schedule. If it rests on solid evidence, I'd want the quality manager to see that evidence, because the disagreement may be about the estimate rather than about the conclusion. It's also possible the quality manager is seeing a hazard path the engineering team hasn't considered — a use error, a combination of failures, or a population the team hasn't thought about — and that's exactly the kind of input the review process exists to surface.

On the control question, even if the risk is real, the proposed control may not be the most effective or the least disruptive way to address it. I'd ask what the control is actually doing — does it reduce severity, reduce probability, or improve detectability — and whether there's an alternative that achieves the same risk reduction with less schedule impact. Sometimes the answer is a design change; sometimes it's a labeling or training control; sometimes it's a verification activity that confirms the risk is lower than estimated. The point is to keep the conversation on risk reduction rather than on the specific control the quality manager proposed.

If, after that, the risk genuinely warrants a control and the control genuinely costs schedule, then the schedule cost is real and has to be managed as a project decision, not hidden. I'd bring it to the project leadership with a clear statement of the risk, the options, and the trade-offs, and let the decision be made with full information. What I wouldn't do is quietly drop the control to protect the schedule, because that's the kind of decision that looks fine until it shows up in a field complaint or an audit.

Throughout, I'd keep the tone collaborative. The quality manager is doing their job, and the engineering team is doing theirs; the goal is a defensible risk decision, not a win.

**Possible follow-ups:**
- How would you handle it if the quality manager's concern turned out to be valid but the proposed control was impractical?
- How would you document the decision so it's defensible later?