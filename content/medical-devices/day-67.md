# medical-devices — Day 67

## Q1: How would you approach designing the patient leakage current measurement path for a device that has both BF-type and CF-type applied parts, and how would you decide which measurements are actually required?

**Answer:** The starting point is to read the applied-part definitions and the measurement network requirements out of the general standard rather than working from memory, because the limits and the test circuits differ by classification and by condition. BF and CF applied parts have different allowable patient leakage current limits, and CF is the stricter of the two, so a device carrying both classifications effectively has to satisfy the tighter limit on the CF part while still demonstrating the BF part meets its own limit. The measurement path itself is defined by the standard's measuring device — a specific passive network that simulates the impedance the patient would present — so the "measurement path" is really about building a fixture that inserts that network between the applied part and earth in the correct configuration for each test case.

Practically, I would map out the applied parts and their classifications first, then enumerate the test conditions: normal condition and each relevant single-fault condition, AC and DC components of leakage, and the different reference points (earth, other applied parts, mains on the applied part for the patient auxiliary current case). Each combination is a distinct measurement with its own limit, and the fixture has to be able to switch between them cleanly without introducing its own leakage or ground loops that corrupt the reading. That means paying attention to the fixture's own insulation, guarding, and the routing of the measurement leads, because at these current levels the fixture can easily dominate the result.

Deciding which measurements are actually required comes down to which applied parts exist, what their classifications are, and which fault conditions are credible for the design. You don't test every theoretical combination blindly; you test the combinations the standard requires for the classifications present, plus any configuration the risk analysis identifies as relevant. I would keep a matrix of applied part × condition × limit and treat it as the verification evidence, so it's traceable back to the requirement rather than being a lab notebook of ad hoc readings.

**Possible follow-ups:**
- How would you confirm the test fixture itself isn't contributing to the measured leakage?
- If a CF applied part shares a connector shell with a BF applied part, how does that affect your measurement plan?

## Q2: How would you approach designing the filtering strategy for a device that has to pass both conducted and radiated emissions limits while also meeting its own signal integrity requirements?

**Answer:** The key insight is that emissions filtering and signal integrity are often in tension, so the strategy has to be layered rather than a single filter dropped in at the end. I would start by separating the problem into source, coupling path, and victim. On the source side, the biggest wins usually come from slowing down edges where the design can tolerate it, controlling clock rise times, and keeping high-di/dt loops physically small. That reduces the broadband energy you have to filter in the first place, which is far more effective than trying to attenuate it after the fact.

For conducted emissions, the strategy is typically a combination of common-mode and differential-mode filtering at the power input and at any interface that leaves the enclosure. Common-mode chokes handle the common-mode component, X-capacitors handle differential mode, and Y-capacitors handle common mode to earth — but Y-capacitance is constrained by leakage current limits, which is a medical-specific wrinkle that doesn't apply in general consumer electronics. So the filter design has to be co-optimized with the leakage current budget, not designed independently and then checked.

For radiated emissions, the enclosure, cable routing, and connector pinout matter as much as any component. Keeping high-speed signals away from board edges and cable exits, providing a clean return path, and filtering or shielding cables that act as antennas are usually more effective than adding ferrites reactively. On the signal integrity side, the constraint is that any filter you add to a signal line also affects its impedance, its rise time, and potentially its timing margin, so filter placement and component selection have to be validated against the signal's own requirements — eye diagram, setup/hold, or analog settling, depending on the interface.

The overall approach is to model or at least reason about where the energy is going, design the filter to target that specific mechanism, and then verify both emissions and signal integrity together rather than sequentially, because a fix for one can break the other.

**Possible follow-ups:**
- How would you decide whether a problem is common-mode or differential-mode before choosing a filter?
- What would you do if the filter that fixes emissions also degrades an analog signal's settling time?

## Q3: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** The first step is to characterize the device by its clinical function and its intended use, not by its marketing description, because the particular standards are organized around what the device does to or for the patient. A device that combines monitoring and therapy may fall under more than one particular standard, and it's entirely possible for both to apply simultaneously rather than one superseding the other. I would build a list of candidate particular standards by function, then read each one's scope clause carefully to confirm applicability, because scope clauses often explicitly include or exclude certain device types.

Once the applicable set is identified, the general standard still applies in full unless a particular standard explicitly modifies or replaces a clause. Particular standards typically state which clauses of the general standard they amend, and the amendment can be a tightening, a relaxation, or a substitution of a test method. Where two particular standards both apply and both modify the same clause of the general standard, that's the conflict case, and it has to be resolved by reading the intent of each and, if necessary, seeking a regulatory interpretation rather than guessing. In practice the resolution is usually to meet the more stringent requirement, but that's a decision to document with rationale, not to assume.

The output of this exercise is a compliance matrix that maps each requirement to its source standard and clause, so that verification evidence can be traced back. That matrix is also what you'd show a reviewer to demonstrate you didn't miss an applicable standard. If there's genuine ambiguity, the right move is to raise it with the regulatory body or a notified body early, because discovering a missed particular standard late in the submission is expensive.

**Possible follow-ups:**
- How would you document the rationale for a decision to apply the more stringent of two conflicting requirements?
- What would you do if a particular standard's scope clause is ambiguous about whether your device is covered?

## Q4: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode to avoid is treating the risk management file as a deliverable that gets written once, near the end, to satisfy an auditor. That produces a document that's internally consistent on paper but disconnected from the actual design decisions, and it tends to fall apart the moment the design changes. The alternative is to treat it as a living artifact that's updated as part of the normal design process, with each hazard, risk control, and verification activity entered when it's identified rather than reconstructed later.

Structurally, I would organize it around the risk management process steps: hazard identification, risk estimation, risk evaluation, risk control, verification of risk control effectiveness, and evaluation of residual risk. Each hazard should trace forward to the risk control that addresses it and to the evidence that the control works, and backward to the design input or requirement that motivated it. That bidirectional traceability is what makes the file auditable — an auditor can pick any hazard and follow it to a verified control, or pick any design decision and see what risk it addresses.

Keeping it maintainable means integrating it with the change control process. When a design change is proposed, one of the review questions should be whether it affects any identified hazard or risk control, and if so, the file is updated as part of that change rather than in a separate pass. I would also keep the risk file's structure aligned with the design history file's structure so that cross-references stay stable, and avoid duplicating content between them — the risk file references the DHF evidence rather than restating it.

Finally, I would build in periodic reviews, not just at milestones, so that the file reflects the design as it actually is at any point in time. A file that's current is far more useful during a design review than one that's six months stale.

**Possible follow-ups:**
- How would you handle a risk control that turns out to be less effective than estimated during verification?
- How would you decide whether a newly identified hazard requires reopening a previously closed risk item?

## Q5: You're the lead engineer, and during a design review the quality manager insists on adding a risk control measure for a hazard the engineering team considers negligible. The schedule impact would be significant. How would you handle this situation?

**Answer:** The first thing I'd do is separate the disagreement into two parts: whether the hazard's risk is actually negligible, and whether the proposed control is the right response to it. Those are different questions and they often get conflated in the heat of a review. If the engineering team and the quality manager disagree on the risk estimate, that's a factual disagreement that should be resolvable with data — severity and probability estimates, clinical input, or reference to similar devices and their field history. I'd ask for the basis of each position rather than treating it as a matter of opinion.

If the risk genuinely is low, the question becomes whether the proposed control is proportionate. Risk management doesn't require eliminating every hazard; it requires reducing risk as far as reasonably practicable and then evaluating whether the residual risk is acceptable. A control that adds significant schedule cost for a hazard with negligible risk may not be the best use of that effort, but that's a judgment the quality function has a legitimate stake in, and I wouldn't want to override it unilaterally. The quality manager may also be seeing something the engineering team isn't — a regulatory precedent, a complaint trend, or a standard requirement that isn't obvious from the design side.

My approach would be to get the disagreement into a form where it can be evaluated on its merits: document the hazard, the risk estimate with its rationale, the proposed control, and the cost and schedule impact. Then bring it to the appropriate forum — a risk management review or a design review with the quality function present — and make the decision there with the rationale recorded. If the decision is to add the control, the schedule impact is real and has to be communicated to the project stakeholders rather than absorbed silently. If the decision is not to add it, the rationale for that decision needs to be documented in the risk file, because an auditor will ask why a proposed control wasn't implemented.

What I'd avoid is either capitulating to avoid conflict or dismissing the concern because the team thinks it's negligible. Both leave the project worse off — one adds unnecessary cost, the other leaves an undocumented decision that could become a finding later.

**Possible follow-ups:**
- What would you do if the quality manager's position is based on information they can't fully share, such as a confidential regulatory interaction?
- How would you communicate a schedule slip driven by a risk control decision to a project sponsor who is focused on the submission date?