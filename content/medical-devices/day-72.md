# medical-devices — Day 72

## Q1: How would you approach designing the patient leakage current measurement path for a device that has both BF-type and CF-type applied parts, and how would you decide which measurements are actually required?

**Answer:** I'd start by mapping the applied parts and their classifications against the standard, because the measurement matrix is driven entirely by that classification and by whether the part is intended for direct cardiac contact. CF-type parts carry the tightest limits (in the microamp range under normal condition, and a higher but still small limit under single-fault condition), while BF-type parts have a more relaxed limit. The measurement path itself has to be built so that it doesn't perturb the very quantity being measured: you want a low-impedance, well-defined measurement network referenced to earth, with the device powered from the correct supply configuration (mains polarity both ways, and for single-fault, the relevant fault applied one at a time). I'd measure each applied part individually and in combination, because leakage can sum across parts that share a reference or a return path.

The practical decisions are: which parts are simultaneously accessible to the patient, whether any parts are isolated from each other, and whether the device has a functional earth or is Class I vs Class II. Those determine whether you measure patient leakage to earth, patient leakage between parts, or both. I'd build a test fixture that lets me switch the measurement network between parts without rewiring the device, and I'd document the exact configuration for each measurement so the results are reproducible and traceable to the standard's clauses. If a part is CF-type, I'd also verify the isolation barrier independently, since the leakage measurement is really a proxy for barrier integrity.

**Possible follow-ups:**
- How would you handle a device where two applied parts are internally connected but the standard treats them as separate?
- What would you do if a measurement is marginally over the limit but only under one polarity of mains?

## Q2: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band failure is a strong hint that something in the device is resonant or that a specific cable or trace is acting as an efficient antenna at that wavelength. I'd first confirm the failure is repeatable and characterize it precisely — sweep finely around the band, vary the field polarization and the device orientation, and note whether the malfunction correlates with a particular cable position or enclosure seam. That tells me whether the coupling is radiated into the enclosure, conducted along a cable, or picked up by a specific trace.

From there I'd work the usual suspects: cable routing and shielding (a cable whose length is a fraction of the wavelength at that frequency is a classic culprit), enclosure apertures and seams, and any high-impedance node in the analog front-end that's sensitive to small induced currents. On the fix side, I'd prefer to attack the coupling path rather than just the victim — adding common-mode chokes or ferrites on the offending cable, improving the ground reference, tightening the enclosure, or adding a small RC or feedthrough filter at the point where the disturbance enters a sensitive node. I'd also check whether the firmware is misinterpreting a transient as valid data; sometimes a defensive check in software (range validation, plausibility filtering) is a legitimate part of the immunity strategy, though it shouldn't be the only line of defense. I'd re-test at the exact failing frequency and then re-sweep the full band to make sure the fix didn't shift the problem elsewhere.

**Possible follow-ups:**
- How would you decide between fixing the coupling path versus hardening the victim circuit?
- If the fix works at the test lab but the device is later used near a different RF source, how would you gain confidence it's robust?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The key is to treat the risk management file as a living artifact that's updated as design decisions are made, not as a retrospective summary. I'd set it up around the ISO 14971 process: hazard identification, risk estimation, risk control, verification of the control's effectiveness, and evaluation of residual risk — with each step traceable to the design inputs and outputs it touches. Practically, that means a hazard analysis that's started early (from the intended use, the use environment, and the foreseeable misuse), and a risk control table that's updated whenever a design change introduces or removes a hazard.

To keep it maintainable, I'd link each risk control to the specific design element that implements it and to the verification evidence that proves it works — so when the design changes, you can see immediately which risk controls are affected. I'd also keep the file organized so a reviewer can follow the logic without hunting: hazard → risk estimate → control → verification → residual risk → acceptability decision. Design reviews become natural checkpoints where the file is reviewed alongside the design. The failure mode to avoid is a file that's technically complete but disconnected from the actual design, because then it's neither useful during development nor defensible during an audit.

**Possible follow-ups:**
- How would you handle a risk control that's implemented in software versus one implemented in hardware, in terms of the evidence you'd keep?
- What would you do if a design change late in the project invalidated a previously verified risk control?

## Q4: How would you approach deciding whether a given software failure in a medical device should be classified as a safety-related failure requiring formal risk controls, versus a non-safety usability or reliability issue?

**Answer:** I'd start from the harm, not from the software. The question is whether the failure could contribute to an unacceptable risk to the patient or operator, directly or through a chain of events. So I'd trace the failure forward: what does the device do when this failure occurs, what does the user see, and could that lead to a hazardous situation? A failure that only degrades convenience or causes a nuisance alarm is different from one that could suppress a critical alarm, display stale data as if it were live, or drive an output incorrectly.

If the failure can plausibly contribute to harm, it belongs in the risk management process — it gets a hazard entry, a risk estimate, and a control, and the software that implements that control gets the corresponding safety classification under IEC 62304. If it can't, it's still worth tracking as a reliability or usability issue, but it doesn't need the same formal apparatus. The judgment call is often at the boundary, and that's where I'd want the risk management and software leads to agree explicitly rather than let it default. I'd also be careful not to let "it's just a display issue" become a reflex — a display that misleads a clinician about a patient's state is a safety issue, not a cosmetic one.

**Possible follow-ups:**
- How would you document the rationale for deciding a failure is *not* safety-related, so it's defensible later?
- How does the software safety classification change the verification and testing you'd require?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** I'd first make sure I understand the request precisely — what clinical problem it solves, how often it occurs, and what the consequence is if it's not addressed. A usability change that prevents a use error with patient harm potential is a different conversation from one that's a convenience improvement, and the answer depends on which it is. I'd bring the clinical team, the quality/regulatory lead, and the engineering leads together to characterize the change and its true cost, including not just the hardware revision but the re-verification, re-validation, and any impact on the submission.

Then I'd lay out the options honestly: do it now and accept the schedule slip; do it as a post-market change after the initial submission; find a software-only or minor-hardware way to achieve most of the benefit; or defer it if the risk doesn't justify the cost. I'd want the decision made on the basis of risk and clinical benefit, not on who asked loudest. If the change is genuinely safety-relevant, the schedule argument doesn't win — you do it. If it's not, I'd push for a documented decision to defer or phase it, with the rationale recorded so it's not relitigated. Throughout, I'd keep the regulatory lead in the loop early, because a late change can affect the submission strategy in ways that aren't obvious from the engineering side.

**Possible follow-ups:**
- How would you handle it if the clinical team and the regulatory lead disagreed on whether the change is safety-relevant?
- What would you put in place to make sure a deferred change actually gets revisited rather than forgotten?