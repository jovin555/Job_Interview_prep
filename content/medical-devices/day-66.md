# medical-devices — Day 66

## Q1: How would you approach designing the patient leakage current measurement path for a device that has both BF-type and CF-type applied parts, and how would you decide which measurements are actually required?

**Answer:** The starting point is the classification of each applied part, because that drives which limits apply and under which fault conditions. A BF-type applied part has a higher patient leakage limit than a CF-type part, and the CF-type part is the one that constrains the design most tightly. So I'd build a measurement matrix: for each applied part, list the applicable leakage current type (patient leakage, patient auxiliary current), the operating condition (normal condition and each relevant single-fault condition), and the limit from the standard. Then I'd map the physical measurement points — which applied part to which reference — because leakage is always defined between two specific points, and getting the reference wrong is one of the most common mistakes.

For the measurement path itself, I'd use a measuring device that presents the impedance the standard specifies, so the reading is comparable to the limit. I'd pay attention to the isolation of the measurement setup: if the measuring instrument or its supply introduces its own path to earth, it can either mask or exaggerate the leakage you're trying to measure. I'd also verify the setup with a known reference before trusting any reading.

Deciding what's actually required comes down to reading the standard's clause for the specific applied part classification and the intended use, not assuming every combination must be tested. But I'd be conservative: if there's ambiguity about whether a fault condition applies, I'd measure it and document the rationale, because a reviewer will ask. The output of this exercise is a test plan that ties each measurement to a clause and a limit, which is what makes the verification defensible.

**Possible follow-ups:**
- How would you handle a device where one applied part is BF and another is CF, and they share a common reference node?
- What would you do if a measurement is marginally under the limit but the margin is smaller than your measurement uncertainty?

## Q2: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band failure is a strong hint that something in the device is resonant or that a specific coupling path becomes efficient at that frequency. I'd start by characterizing the failure precisely: sweep finely around the band to find the exact center and the width, and note whether the malfunction depends on field orientation, cable position, or the device's operating state. That tells me whether I'm looking at an antenna-like structure (a cable, a slot, a long trace) or a component-level susceptibility.

Next I'd try to localize the coupling path. Common culprits are cables acting as unintentional antennas, enclosure seams or apertures near a resonant dimension, and traces or loops whose length is a meaningful fraction of the wavelength at that frequency. I'd use near-field probing and, if available, a current probe on cables to see where the energy is actually entering. Shielding one section at a time — temporarily, with copper tape or ferrites — helps confirm the path before committing to a fix.

Once the path is known, the fix is usually one of: break the antenna (shorten or reroute the cable, add a common-mode choke), close the aperture (improve seam bonding, add gaskets), or harden the victim (add filtering or decoupling at the affected circuit, improve the reference plane). I'd also check whether the malfunction is a firmware-visible glitch that could be made more robust — for example, a transient on a communication line that a more tolerant protocol or a retry would absorb. The right fix depends on whether the root cause is coupling or susceptibility, and I'd want to address the coupling first because it's usually cheaper and more robust.

**Possible follow-ups:**
- How would you decide between adding a ferrite on a cable versus redesigning the cable routing?
- If the fix works on the bench but the failure returns at the test lab, what would you check first?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The file should be a living record that grows with the design, not a retrospective compilation. I'd set it up at the start with the hazard analysis as the spine: a structured list of hazards, the foreseeable sequences of events that could lead to harm, and the associated hazardous situations. Each entry gets a unique identifier so it can be referenced from design inputs, test cases, and change records.

From there, the file needs to show the full chain: hazard → risk estimate → risk control measure → verification that the control was implemented → verification that the control is effective → residual risk evaluation → overall benefit-risk conclusion. The key discipline is that every risk control has a corresponding verification activity, and that activity is traceable back to the hazard it addresses. If a design change later touches a component or function linked to a hazard, the file should make it obvious which entries need re-review.

I'd also keep the file organized so a reviewer can navigate it without a guide: a clear index, consistent naming, and a summary table that maps hazards to controls to evidence. The most common failure mode is a file that's technically complete but impossible to audit because the links are implicit. Making the links explicit — even if it means some redundancy — is what keeps it usable when someone unfamiliar with the project has to review it months later.

**Possible follow-ups:**
- How would you handle a risk control that turns out to be less effective than estimated during verification?
- Where does the risk management file interface with the design history file, and how do you avoid duplicating content?

## Q4: How would you approach selecting materials for a patient-contacting sensor housing that must meet both biocompatibility (ISO 10993) and mechanical durability requirements?

**Answer:** I'd treat this as a two-sided constraint problem: the material has to be safe in contact with the patient for the intended duration and type of contact, and it has to survive the mechanical and environmental stresses of its use. The first step is to define the contact category precisely — surface contact versus mucosal versus blood-contacting, and the duration (limited, prolonged, or long-term) — because that determines which ISO 10993 tests are relevant. Not every material needs the full battery of tests; the standard is risk-based, and the testing plan should follow from the contact scenario.

On the durability side, I'd define the mechanical requirements: impact resistance, flex fatigue, resistance to cleaning agents, and the temperature range it will see. Then I'd look for materials that have a documented biocompatibility history for the same contact category, because using a material with existing data reduces testing burden and risk. If a candidate material is new to the application, I'd plan for the relevant ISO 10993 tests and budget the time for them early, since they can be a schedule driver.

The practical tension is that the most durable materials aren't always the most biocompatible, and the most biocompatible aren't always the most durable. I'd resolve that by considering the whole assembly: sometimes the answer is a durable structural material with a biocompatible overmold or coating on the patient-contacting surface, rather than one material doing everything. I'd also verify that any coating or overmold stays intact over the device's life, because a compromised coating changes the biocompatibility profile.

**Possible follow-ups:**
- How would you handle a situation where the supplier's biocompatibility data is for a slightly different grade of the same material?
- What would you do if the mechanical testing shows a crack forming in a patient-contacting area after accelerated life testing?

## Q5: You're the lead engineer on a medical device project. During a design review, the quality manager insists that a new risk control measure must be added to address a hazard with an estimated risk level that the engineering team considers negligible. The schedule impact would be significant. How would you handle this situation?

**Answer:** I'd start by making sure we're actually disagreeing about the same thing. "Negligible" is a judgment, and the quality manager may be seeing a severity or probability that the team is underestimating, or may be applying a more conservative acceptance criterion. I'd ask them to walk through their reasoning: what's the hazardous situation, what's the harm, and how did they arrive at the risk estimate? Often the disagreement dissolves once the assumptions are on the table.

If the risk estimate genuinely is low but the quality manager still wants the control, I'd separate two questions: is the control required by the standard or by our own risk policy, and is it the most efficient way to address the concern? If it's required, the schedule impact is a planning problem, not a reason to skip it — I'd look at whether the control can be implemented in a way that minimizes rework, or whether it can be phased. If it's not strictly required, I'd want to understand what would make the quality manager comfortable: sometimes a documented rationale for accepting the risk, with the reasoning recorded, is sufficient and much cheaper than a design change.

Throughout, I'd keep the conversation focused on the risk rather than on whose judgment is right. The goal is a decision that's defensible to a reviewer and that the team can stand behind. If we can't reach agreement, I'd escalate through the defined decision path rather than let it stall the review, and I'd document the decision and its rationale either way.

**Possible follow-ups:**
- How would you document a decision to accept a risk without adding a control, so it holds up to a reviewer?
- If the quality manager's concern turns out to be valid but the schedule can't absorb the change, what options would you bring to the project team?