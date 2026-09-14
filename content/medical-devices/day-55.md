# medical-devices — Day 55

## Q1: How would you approach designing the thermal management for a patient-worn medical sensor that must remain within its safe touch-temperature limit during continuous operation, given that the electronics are sealed in a compact, non-vented enclosure?

**Answer:** The starting point is to treat the touch-temperature limit as a hard design input derived from the applicable standard, not as an after-the-fact check. I'd first build a rough thermal budget: estimate total dissipated power from the major contributors (regulator losses, sensor excitation, radio transmit bursts, MCU active current), then decide how much of that can be tolerated given the enclosure's surface area and the worst-case ambient the device will see. In a sealed, non-vented enclosure the only real escape paths are conduction through the housing and a small amount of radiation, so the design has to minimize generated heat rather than rely on removing it.

Practically, that means attacking the power budget first: choose a high-efficiency regulator topology, use duty-cycled or low-power modes for the radio and analog front-end, and avoid linear regulators dropping meaningful voltage where a switching converter is acceptable from an EMI standpoint. If the radio is the dominant transient source, spreading transmit bursts over time or reducing duty cycle often helps more than any thermal fix. For the mechanical side, I'd look at spreading heat across a larger surface rather than concentrating it — thermal vias under hot components, copper pours to distribute heat, and where the patient contact is, a deliberate thermal break or standoff so the hottest components aren't directly against skin. The patient-contacting surface is the one that matters for the touch limit, so the internal junction temperatures can be higher as long as the surface stays within limits.

Verification is where this gets interesting: I'd want thermocouples or thermal imaging on the actual enclosure surface at the worst-case ambient and worst-case operating mode, not just simulation, because sealed-enclosure convection is hard to model accurately. I'd also test at the extremes — maximum transmit duty cycle, maximum sensor load, and the highest specified ambient — since thermal problems usually only show up at the corner cases.

**Possible follow-ups:**
- How would you decide between reducing power consumption and adding a heat-spreading feature if the schedule is tight?
- What would you do if the surface temperature passed at room ambient but failed at the high end of the specified operating range?

## Q2: How would you approach deciding whether a given software failure in a medical device should be classified as a safety-related failure requiring formal risk controls, versus a non-safety usability or reliability issue?

**Answer:** The classification shouldn't be made by intuition or by whoever is loudest in the review — it should fall out of the risk management process. The first question is whether the failure could contribute to a hazardous situation, meaning could it lead to patient harm either directly or by removing a protective measure. If the answer is genuinely no, it's a reliability or usability issue. If there's any plausible path to harm, it belongs in the risk file and gets treated as safety-related until the analysis shows otherwise.

In practice I'd work through it systematically. Start with the failure mode and ask what the device does as a result — does it stop monitoring, does it display stale or wrong data, does it fail to alarm, does it alarm falsely in a way that could cause alarm fatigue or mask a real event? Then trace whether that behavior could reach the patient. A display glitch that's obviously cosmetic is different from a display glitch that could show a normal value when the patient is deteriorating. The distinction often isn't the software defect itself but the clinical consequence of the resulting device behavior.

I'd also be careful about the trap of "it's only a UI issue." Usability failures can absolutely be safety-related if they lead a clinician to a wrong action. That's why usability engineering and risk management are linked. If the failure could cause a use error with a hazardous outcome, it's safety-related regardless of whether the code path is in the "safety" module.

Once classified, the rigor follows: safety-related failures get traced to risk controls, verified, and covered by the software safety classification under IEC 62304. Non-safety issues still get tracked and fixed, but through normal defect management rather than the formal risk control path. The key discipline is documenting the rationale either way, so the decision is defensible during an audit.

**Possible follow-ups:**
- How would you handle a disagreement where one engineer argues a failure is safety-related and another argues it's purely cosmetic?
- Where does the boundary sit between a software failure that's caught by an independent hardware safety mechanism and one that isn't?

## Q3: How would you approach selecting materials for a patient-contacting sensor housing that must meet both biocompatibility (ISO 10993) and mechanical durability requirements?

**Answer:** I'd treat biocompatibility and durability as two constraints that have to be satisfied simultaneously, and the material selection is where they either coexist or fight each other. The first step is to define the contact category precisely — is it surface contact, mucosal, or indirect blood path, and what's the duration (limited, prolonged, permanent)? That determines which ISO 10993 test battery applies, and it's a common mistake to over- or under-test because the contact category wasn't pinned down early.

From there I'd shortlist materials that are already well-characterized for the intended contact type, because using a material with an established biocompatibility history dramatically reduces testing burden and risk. For a housing that also has to survive repeated handling, cleaning, and possibly disinfection, I'd look at the mechanical and chemical resistance requirements in parallel: does the material resist the cleaning agents it will actually see, does it hold up to drop and impact, does it maintain dimensional stability over the temperature range? A material that passes biocompatibility but crazes after a few cleaning cycles is not a solution.

The interaction between the two is where experience matters. Surface treatments, colorants, mold release agents, and adhesives can all introduce leachables that weren't in the base resin's biocompatibility data, so the finished assembly — not just the raw material — is what needs to be evaluated. I'd also consider whether the material can be processed in a way that avoids introducing contaminants, and whether secondary operations like ultrasonic welding or solvent bonding change the extractables profile.

Verification would combine the ISO 10993 testing appropriate to the contact category with mechanical and cleaning-cycle testing, and I'd want the biocompatibility testing done on the final, processed article rather than a coupon, because processing can change what leaches out.

**Possible follow-ups:**
- How would you handle a situation where the mechanically ideal material doesn't have an established biocompatibility history?
- What would you do if a cleaning agent specified by the clinical team turned out to degrade the chosen housing material?

## Q4: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band failure is actually a gift, because it points at a resonance rather than a broad susceptibility. The first thing I'd do is characterize it precisely: sweep finely around the failing frequency to find the exact center and the bandwidth, and note whether the malfunction depends on field orientation, cable position, or the device's operating mode. That tells me whether I'm looking at a resonant structure — a cable acting as an antenna, a trace or loop resonating at that frequency, or a coupling path into a specific circuit.

Next I'd try to localize the coupling path. Is it radiated into the enclosure, conducted in through a cable, or coupled into a specific connector? Simple experiments help: reroute or shorten cables, add temporary shielding or ferrites, and see whether the failure frequency or threshold moves. If adding a ferrite on a particular cable shifts the failure, that cable is the antenna. If shielding a particular region helps, the coupling is field-to-trace or field-to-component.

Once I know the path, the fix is usually one of a few things: break the resonance (change trace or cable length, add damping), reduce the loop area that's picking up the field, improve filtering or decoupling at the point where the energy enters the sensitive circuit, or improve the ground/reference integrity so the coupled energy has somewhere benign to go. For a narrow-band issue, a targeted filter or a small layout change is often more effective than broad shielding, and it's usually cheaper and less invasive.

I'd verify by re-sweeping the full band, not just the failing frequency, because a fix that shifts the resonance rather than eliminating it can just move the problem. And I'd confirm the fix holds across the full operating envelope — different modes, cable configurations, and the worst-case orientation.

**Possible follow-ups:**
- How would you distinguish a resonance in a cable from a resonance on the PCB itself?
- If the fix requires a layout change late in the project, how would you weigh that against a filtering-only solution?

## Q5: You're the lead engineer on a medical device project. During a design review, the quality manager insists that a new risk control measure must be added to address a hazard with an estimated risk level that the team considers negligible. The schedule impact would be significant. How would you handle this situation?

**Answer:** I'd start by separating the two things that are getting tangled: whether the risk estimate is correct, and whether the control is warranted given that estimate. Those are different conversations and conflating them is what makes these disagreements feel personal.

First I'd ask the quality manager to walk through the hazard and the risk estimate with the team, because "negligible" is a judgment and it's worth checking the assumptions behind it. Sometimes the disagreement is really about severity or probability inputs — maybe the team assumed a benign failure mode that the quality manager sees differently, or maybe there's a use case nobody considered. If the estimate holds up under scrutiny, then the question becomes whether the control is justified by the risk, and that's a decision the risk management process should make, not the schedule.

If the team genuinely believes the risk is acceptable and the control isn't warranted, I'd want that documented with the rationale, because "we decided not to" is a legitimate outcome as long as it's reasoned and recorded. But I'd also take the quality manager's concern seriously rather than dismissing it — quality often sees field or regulatory patterns that engineering doesn't, and a control that seems like overkill from a pure risk standpoint might be addressing a concern that's real for reasons outside the immediate analysis.

On the schedule side, I'd look for whether the control can be implemented in a way that's less disruptive than the initial estimate — sometimes a design change looks expensive until someone scopes it properly. If it truly can't fit, that's a trade-off to escalate with the facts: here's the risk, here's the control, here's the cost, here's the recommendation. The decision belongs to the project leadership with the risk documented, not to whoever argues hardest in the review.

**Possible follow-ups:**
- What would you do if the quality manager's position was based on a regulatory expectation you weren't aware of?
- How would you document a decision not to implement a proposed risk control so it holds up in an audit?