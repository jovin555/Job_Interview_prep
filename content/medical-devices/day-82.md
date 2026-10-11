# medical-devices — Day 82

## Q1: How would you approach designing the analog front-end for a patient-connected sensor whose signal of interest is a fraction of a millivolt riding on a baseline that can drift by hundreds of millivolts, while keeping the design verifiable against a specified accuracy limit?

**Answer:** The core problem is dynamic range versus resolution: the baseline drift is orders of magnitude larger than the signal, so a single fixed-gain stage would either saturate on the drift or leave the signal buried in the noise floor. I'd break it into stages. First, an instrumentation amplifier with high common-mode rejection to reject the large common-mode component and establish a clean differential measurement. Second, a high-pass or baseline-restoration stage to strip the slow drift — but I'd be careful here, because a high-pass corner set too high will attenuate genuine low-frequency content in the signal, and a corner set too low won't track drift fast enough. The corner frequency is a clinical decision as much as an engineering one, so I'd derive it from the signal's actual bandwidth requirement and confirm it with the clinical/algorithm team. Third, a gain stage to bring the signal into the ADC's useful range, followed by an anti-aliasing filter matched to the sample rate.

For verifiability, the key is that every stage's contribution to error must be traceable to the accuracy budget. I'd allocate the total error budget across offset, gain error, noise, drift, and nonlinearity, then pick components whose datasheet limits fit within their allocation over the operating temperature range — not just at 25°C. I'd also make sure the design can be characterized: inject a known signal at the input and measure the full chain's response, so verification isn't just "it looks reasonable on a scope" but a measured transfer function against the spec. If the drift is dominated by a sensor effect rather than the electronics, that changes the architecture — you may need a ratiometric or modulated approach rather than fighting it in the analog domain.

**Possible follow-ups:**
- How would you decide between AC-coupling the signal and doing baseline restoration in firmware?
- What would you do if the drift turned out to be thermal and correlated with the device's own self-heating?

## Q2: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** I'd start from the device's intended clinical function and its classification, not from the marketing description, because the applicable particular standard is driven by what the device actually does to or for the patient. I'd map each function to its likely particular standard — monitoring functions and therapy functions usually fall under different parts of the 60601-2 series — and then treat the device as subject to all of them simultaneously. The general standard (60601-1) plus its collateral standards (60601-1-2 for EMC, 60601-1-6 for usability, 60601-1-8 for alarms, 60601-1-11 for home healthcare, etc.) apply throughout; the particular standards layer additional, function-specific requirements on top.

Conflicts are rarer than people assume, but where they appear, the general principle is that the more specific requirement governs, and where a particular standard explicitly states a deviation from the general standard, that deviation takes precedence for that clause. The practical approach is to build a requirements matrix: rows are clauses, columns are the applicable standards, and each cell records whether the requirement applies, is superseded, or is additive. That matrix becomes part of the design inputs and makes the conflict resolution auditable rather than a judgment call buried in someone's head. If a genuine ambiguity remains, I'd document the interpretation and the rationale, and where it materially affects safety, raise it with the regulatory/notified body early rather than at submission.

**Possible follow-ups:**
- How would you handle a device where one function is Class II and the other would be Class III if standalone?
- What would you do if a particular standard referenced an older edition of the general standard?

## Q3: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow, reproducible band is a strong hint that something in the device is resonant at that frequency — a cable acting as an antenna, a trace or loop with a resonant length, or an enclosure seam. The first step is to characterize it properly: sweep finely around the failing frequency to find the exact center and the bandwidth, and note whether the malfunction depends on cable routing, device orientation, or which cables are connected. That tells you whether the coupling path is radiated into the enclosure, conducted along a cable, or both.

Then I'd localize. A near-field probe swept over the board and along cables while injecting at the failing frequency can show where the energy is concentrating. If the coupling is into a cable, the fix is often at the cable interface — a common-mode choke, a ferrite, better shield termination, or a change in connector pinout to reduce the loop area. If it's into the enclosure, it may be a seam or aperture acting as a slot antenna, addressed with gasketing, seam overlap, or a change in vent/aperture geometry. If it's coupling directly onto a sensitive node, it's a layout or filtering problem at that node.

The important discipline is to fix the coupling path rather than just hardening the victim, because hardening the victim often just moves the failure to a different frequency or a different test. I'd verify the fix by re-sweeping the full band, not just the failing point, and confirm no new susceptibility appeared elsewhere. I'd also document the root cause and the fix in the EMC test report, since that's part of the technical file.

**Possible follow-ups:**
- How would you distinguish a cable-borne coupling path from a direct-field coupling path experimentally?
- If the fix requires a PCB change, how would you decide whether to respin or add a temporary mitigation to get through the test?

## Q4: How would you approach deciding whether a given software failure in a medical device should be classified as a safety-related failure requiring formal risk controls, versus a non-safety usability or reliability issue?

**Answer:** The classification should follow from the risk analysis, not from intuition about how bad the failure "feels." I'd start by asking what the hazardous situation is that the failure could lead to, and whether that situation could result in harm to the patient or operator. If the failure can contribute to a hazardous situation, it's safety-related and belongs in the risk management process — regardless of how likely it seems, because likelihood is a separate axis from severity. If the failure only degrades usability or availability without a credible path to harm, it's a quality or reliability issue and can be handled through normal defect tracking.

The subtle cases are the ones where the failure doesn't directly cause harm but removes a risk control. For example, if a software function is itself a risk control measure (an alarm, a limit, an interlock), then a failure of that function is safety-related by definition, because it defeats a control the risk file depends on. That's the test I'd apply: does this failure either create a hazardous situation or defeat a risk control? If yes to either, it goes through the risk process.

I'd also be careful about the "no harm possible" conclusion — it needs to be justified in the risk file, not asserted. And I'd want the classification decision to be reviewable, so I'd document the reasoning and the hazardous situation analysis, not just the conclusion. If there's genuine disagreement on the team, that's a signal the risk analysis is incomplete, and the right move is to resolve it in the risk file rather than by seniority.

**Possible follow-ups:**
- How would you handle a failure that is safety-related only in combination with another independent failure?
- What's the difference in verification rigor between a safety-related software failure and a non-safety one?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** I'd treat it as a trade-off to be made explicitly, not a yes/no to be delivered on the spot. First I'd understand the request properly: what clinical problem is it solving, how often does that problem occur, and what's the consequence if it isn't addressed? A usability change that prevents a use error with patient harm potential is a different proposition from one that's a convenience improvement. I'd want the clinical team to articulate the hazard or the workflow pain in concrete terms, because that determines whether it's a safety issue, a satisfaction issue, or a nice-to-have.

Then I'd get a realistic cost picture from engineering: is it truly a hardware revision, or can part of it be done in firmware or enclosure tooling? What's the minimum change that addresses the clinical need? Sometimes the requested change has a smaller-footprint alternative that gets most of the benefit. I'd also check whether the change could be deferred to a post-market software update or a subsequent hardware revision without compromising safety — that's often the right answer for a non-safety usability improvement.

With the clinical need and the cost both on the table, I'd bring it to a decision forum with the right stakeholders — clinical, regulatory, quality, program management — and make the trade-off explicit: here's the benefit, here's the schedule and cost impact, here's the regulatory implication. My recommendation would be driven by whether the change addresses a safety-relevant use error. If it does, the schedule impact is the cost of doing it right, and I'd advocate for it. If it doesn't, I'd advocate for capturing it for the next revision and protecting the submission. Either way, the decision gets documented with its rationale, because "we decided to delay" or "we decided to defer" both need a defensible record.

**Possible follow-ups:**
- How would you handle it if the clinical team escalated the request above you?
- What would you do if the change were safety-relevant but the schedule impact threatened the company's funding milestone?