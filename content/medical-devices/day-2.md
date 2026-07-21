# medical-devices — Day 2

## Q1: How would you approach designing the power management subsystem for a battery-powered medical device that must operate continuously for 7 days while monitoring multiple physiological sensors?

**Answer:** The first step is to build a detailed power budget from the system requirements. I'd identify every active component—microcontroller, sensors, wireless module, display if present—and estimate their current draw in each operating mode (active, idle, sleep, deep sleep). For a 7-day runtime, the average current consumption must be extremely low, which typically forces a duty-cycled architecture: the system spends most of its time in a low-power sleep state, waking periodically to take sensor readings, process data, and transmit or log results.

I'd select a microcontroller with multiple low-power sleep modes and fast wake-up times, and choose sensors that support standby or shutdown modes with microamp-level quiescent current. The battery chemistry (typically Li-ion or Li-Po for medical portables) determines the nominal voltage and capacity; I'd include a fuel gauge IC for accurate state-of-charge monitoring, which is important for clinical confidence. The power path must handle charging from USB or a dedicated charger while the device is in use, with seamless switchover so the device never resets when external power is connected or removed.

For the regulator topology, a switching converter (buck or buck-boost) for the main rail gives good efficiency, but sensitive analog sensor rails might need a low-noise LDO post-regulation to avoid switching ripple corrupting measurements. I'd also include protection features: overcurrent, overvoltage, reverse-battery protection, and thermal shutdown, all of which are expected under IEC 60601-1 for patient safety. Finally, I'd simulate the battery discharge curve under the expected duty cycle and validate with a prototype run—this catches surprises like inrush currents or regulator dropout at low battery voltage.

**Possible follow-ups:** How would you decide between a single-cell versus multi-cell battery configuration? What specific IEC 60601-1 clauses apply to the battery charging circuit?

## Q2: You're debugging a Class II medical device that intermittently fails EMC radiated emissions testing at a specific frequency band. How would you approach the investigation?

**Answer:** I'd start by confirming the failing frequency and its harmonics, then correlate that with known clock frequencies or switching frequencies in the design. For example, a 16 MHz microcontroller clock might show up at 16, 32, 48 MHz, and so on. I'd use a near-field probe and spectrum analyzer on the bench to locate the strongest emission source—often it's a long PCB trace acting as an antenna, a cable harness, or a poorly decoupled power rail.

Once I identify the culprit, I'd look at the layout: is the return path for that signal broken or excessively long? Are there un-terminated stubs on the trace? I'd check the decoupling capacitor placement—capacitors too far from the IC pin lose effectiveness above a few hundred MHz due to parasitic inductance. For a clock signal, adding a small series resistor (22–33 Ω) near the source can slow the edge rate just enough to reduce harmonics without affecting timing margins.

If the emissions are from a switching regulator, I'd examine the switching node layout (minimize loop area), check the inductor shielding, and consider adding a ferrite bead or snubber. For cable-related emissions, common-mode chokes or ferrite cores on the cable can help. I'd also verify the enclosure shielding and gasket continuity—sometimes a gap in the metal enclosure or a poorly bonded seam creates a slot antenna.

The key is to make one change at a time and re-test, because multiple changes can mask interactions. I'd document each attempt and the measured effect, which also helps if the fix needs to be justified to a certification body later.

**Possible follow-ups:** How would you distinguish between conducted and radiated emissions as the root cause? What design-stage practices could prevent this issue from appearing at the testing phase?

## Q3: How would you structure a risk management file for a new medical device under ISO 14971, and how does it integrate with the design history file?

**Answer:** I'd start with the intended use and reasonably foreseeable misuse of the device, because risk management is fundamentally about understanding how the device could cause harm in its intended context. From there, I'd identify hazards using techniques like preliminary hazard analysis (PHA) and FMEA—considering electrical shock, thermal hazards, mechanical failure, software errors, electromagnetic interference, and biological compatibility.

Each identified hazardous situation gets a risk assessment: severity of potential harm and probability of occurrence. The key is to be systematic and not skip "obvious" risks—regulators expect a complete picture. For each unacceptable risk, I'd define risk control measures, which follow the hierarchy: inherent safety by design (e.g., redundant overcurrent protection), protective measures (e.g., insulation, alarms), and finally information for safety (e.g., warnings in the IFU). After implementing controls, I'd re-evaluate residual risk and decide if it's acceptable per the company's risk acceptability criteria.

The risk management file integrates with the DHF at multiple points: design inputs should trace to risk controls, verification testing should confirm that controls work, and validation should confirm the device is safe in the clinical environment. Any design change triggers a risk review—does this change introduce new hazards or affect existing controls? This traceability is typically captured in a risk management report and a traceability matrix linking hazards, controls, verification activities, and design inputs.

**Possible follow-ups:** How do you handle a situation where a risk cannot be fully mitigated by design—what documentation is required? How does software risk management (IEC 62304) intersect with ISO 14971?

## Q4: During IEC 60601-1 testing, a prototype fails the dielectric strength (hi-pot) test between the patient connection and mains earth. How would you diagnose and resolve this?

**Answer:** A hi-pot failure means the insulation between the patient-accessible parts and protective earth is breaking down under the test voltage (typically 1500 VAC for Class II medical devices). The first step is to isolate the failure path: disconnect subassemblies one at a time—the power supply, the patient cable, the internal wiring harness, the PCB itself—and re-test each segment to find where the breakdown occurs.

Common causes include: a component with insufficient creepage/clearance (e.g., a transformer with inadequate isolation), a PCB with contamination or moisture on the surface, a damaged insulation barrier (cracked optocoupler, pinched wire), or a design error where a patient-connected trace runs too close to a mains-connected plane. I'd inspect the suspect area under magnification, looking for carbon tracks, solder splashes, or flux residue that could create a conductive path under high voltage.

If the failure is in a transformer or isolated DC-DC converter, I'd check the datasheet for the rated isolation voltage and verify the part was sourced correctly—counterfeit or substituted parts sometimes have lower ratings. For PCB-related failures, increasing the creepage distance by routing traces farther apart or adding a slot in the board can help. In some cases, the fix requires adding an insulating barrier (e.g., Mylar sheet, conformal coating) between the patient circuit and the mains circuit.

After implementing the fix, I'd repeat the hi-pot test and also perform the insulation resistance test (typically 500 VDC, measuring > 5 MΩ) to confirm the insulation is intact. I'd also review the design rules for creepage and clearance distances per IEC 60601-1 Table 6 or 7, and update the PCB layout guidelines to prevent recurrence.

**Possible follow-ups:** What is the difference between basic insulation, double insulation, and reinforced insulation in the context of patient protection? How would you test for leakage current separately from dielectric strength?

## Q5: A cross-functional team disagrees on whether to prioritize a new feature requested by clinicians versus completing regulatory documentation for an upcoming submission. How would you handle this as the lead engineer?

**Answer:** I'd first acknowledge that both are legitimate priorities—the feature could improve patient outcomes or workflow, and the regulatory submission is a hard deadline that affects market access. The key is to frame the decision in terms of risk to the project and the patient.

I'd call a brief meeting with the stakeholders: product management, clinical affairs, regulatory, and quality. I'd ask the clinical team to clarify the feature's impact—is it a safety improvement, a usability enhancement, or a nice-to-have? I'd ask regulatory to clarify the submission deadline and whether there's any flexibility (e.g., a later filing window). Then I'd assess the engineering effort: can the feature be implemented without destabilizing the current design? Does it require new verification testing that would delay the submission?

If the feature is safety-critical or addresses a usability issue that could cause patient harm, I'd argue for a phased approach: include the feature now if it can be done quickly, or document it as a planned design change for the next submission cycle. If the feature is non-critical, I'd recommend completing the current submission and adding the feature in a post-market release, with a clear plan for when that would happen.

I'd document the decision rationale in the project records, including the risk assessment that informed it. This protects the team if regulators or auditors later ask why a particular feature was or wasn't included. Throughout, I'd keep communication transparent—engineers need to know why their work is being reprioritized, and clinicians need to know their input was heard and will be addressed.

**Possible follow-ups:** How would you handle a situation where the feature request comes from a key customer who is threatening to delay a purchase order? What role does the quality management system play in this decision?