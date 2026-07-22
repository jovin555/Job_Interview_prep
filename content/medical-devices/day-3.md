# medical-devices — Day 3

## Q1: How would you approach selecting appropriate creepage and clearance distances for a medical device PCB that has both mains-connected and patient-connected circuits?

**Answer:** The first step is to determine the applicable working voltage and the pollution degree of the intended environment. For medical devices, IEC 60601-1 specifies minimum creepage and clearance distances based on the insulation type — functional, basic, supplementary, or reinforced — and the voltage between the circuits. Patient-connected circuits require a higher level of protection, typically reinforced insulation between patient and mains, or double insulation (basic + supplementary). I would start by identifying the peak working voltage and the transient overvoltage category, then consult Table 9 and Table 10 in IEC 60601-1 (3rd edition) for the minimum distances. For example, a 250 Vrms mains circuit at pollution degree 2 requires roughly 4 mm clearance for basic insulation, but reinforced insulation doubles that. I would also consider conformal coating as a way to reduce creepage requirements if the design is space-constrained, but only if the coating is qualified per the standard. Finally, I would verify the distances in the PCB layout tool using a design rule check and document the rationale in the design history file.

**Possible follow-ups:**
- How does the presence of a protective earth connection affect the insulation requirements between patient and mains?
- What would you do if the required creepage distance cannot be physically achieved on the PCB?

---

## Q2: How would you approach verifying that a medical device's software meets IEC 62304 requirements for a Class B software safety classification?

**Answer:** I would begin by confirming the software safety classification through a hazard analysis per ISO 14971, identifying whether a software failure could lead to unacceptable risk. For Class B, the software could cause injury but not death or serious injury. The verification approach would follow a structured lifecycle: software development plan, software requirements specification, architectural design, detailed design, unit implementation and verification, integration and system testing, and software release. For verification specifically, I would ensure each software requirement has a corresponding test case in the software test plan, with traceability maintained in a requirements traceability matrix. Unit testing would cover all modules at the code level, integration testing would verify interfaces between modules, and system testing would validate the software against the requirements in the target hardware environment. I would also perform code reviews and static analysis to catch defects early. The software release criteria would include that all critical and major defects are resolved, and that the risk management file confirms residual risks are acceptable. All verification results would be documented in the software verification report as part of the design history file.

**Possible follow-ups:**
- How would you handle a situation where a software defect is discovered during system testing but the release deadline is approaching?
- What distinguishes Class B verification activities from Class C, and when would you need to escalate?

---

## Q3: During IEC 60601-1-2 immunity testing, your medical device exhibits erratic behavior when exposed to a 3 V/m radiated RF field at 80 MHz. How would you approach diagnosing and resolving this?

**Answer:** I would first document the exact test conditions: frequency, modulation, field strength, device configuration, and the specific behavior observed. Then I would approach the diagnosis systematically. The first step is to determine whether the susceptibility is in the analog front-end, the digital processing, or the power supply. I would use a near-field probe and a spectrum analyzer to locate where the RF energy is coupling into the circuit — common entry points are cables, PCB traces acting as antennas, unshielded enclosures, or apertures. For a medical device, patient cables are a frequent coupling path, so I would check if ferrite chokes or common-mode filtering on the patient interface reduces the issue. If the problem is on the PCB, I would look for long traces that could act as quarter-wave antennas at 80 MHz (roughly 0.9 meters for a quarter wave, but harmonics or PCB resonances can be shorter). Shielding the sensitive circuitry with a grounded metal can, adding ferrite beads on power supply lines, or improving the grounding scheme — such as using a solid ground plane and stitching vias around the PCB perimeter — are typical countermeasures. I would also verify that the enclosure's conductive coating or gasketing is continuous and properly bonded to the system ground. After implementing a fix, I would retest at the failing frequency and also sweep adjacent frequencies to ensure the problem hasn't shifted.

**Possible follow-ups:**
- How would you distinguish between conducted and radiated coupling for this type of failure?
- What role does the device's operating mode (e.g., monitoring vs. therapy delivery) play in determining the acceptable level of immunity?

---

## Q4: How would you approach identifying which IEC 60601-2 particular standards apply to a new medical device that combines respiratory monitoring with drug infusion?

**Answer:** I would start by determining the primary intended use and the physiological systems the device interacts with. For respiratory monitoring, IEC 60601-2-12 (lung ventilators) or IEC 60601-2-79/80 (respiratory support devices for home use) might apply depending on whether the device provides ventilation or just monitoring. For drug infusion, IEC 60601-2-24 (infusion pumps and controllers) would be relevant. However, since the device combines both functions, I would check IEC 60601-1's guidance on multi-function devices — the device must comply with all applicable particular standards for each function. I would also review the collateral standards: IEC 60601-1-2 (EMC), IEC 60601-1-6 (usability), IEC 60601-1-8 (alarm systems), and IEC 60601-1-9 (environmentally conscious design) if relevant. The key is to create a compliance matrix early in development, listing each standard and the specific clauses that apply. I would also consult with a regulatory affairs specialist or a notified body for interpretation, especially if there is ambiguity — for example, whether a monitoring-only device falls under the ventilator standard or a separate monitoring standard. Finally, I would document the rationale for including or excluding each standard in the design history file.

**Possible follow-ups:**
- If the device has a software-only alarm system, how does IEC 60601-1-8 apply differently than for a hardware-based alarm?
- How would you handle a conflict between requirements in two different particular standards for the same device?

---

## Q5: You are the lead engineer on a medical device project. During a design review, the quality manager insists that a new risk control measure must be added to address a hazard with an estimated risk level that the team considers negligible. The schedule impact would be significant. How would you handle this situation?

**Answer:** I would first acknowledge the quality manager's concern and ask for a few minutes to review the specific hazard analysis together. The goal is to ensure we're both looking at the same data — the hazard identification, the sequence of events, the severity of harm, and the probability of occurrence. If the risk is truly negligible, the ISO 14971 risk management process allows for risk acceptance when the residual risk is judged acceptable based on the risk evaluation criteria defined in the risk management plan. I would ask the quality manager to walk through why they believe the risk is not acceptable, and I would share my reasoning for why the team considers it negligible. If we still disagree, I would suggest a structured approach: convene a small cross-functional team (design, quality, clinical, regulatory) to perform a formal risk estimation review, using the same risk matrix and criteria from the risk management plan. If the review confirms the risk is negligible, we document the decision and the rationale in the risk management file. If the review identifies a legitimate concern, then we accept the schedule impact and plan the risk control measure. The key is to depersonalize the disagreement by anchoring the discussion in the documented risk management process, not in opinions. If the quality manager still insists beyond what the process supports, I would escalate to the project sponsor or the designated management representative for risk management, as defined in the organization's quality system.

**Possible follow-ups:**
- How would you ensure that the risk estimation review is objective and not biased by schedule pressure?
- What documentation would you create to capture the disagreement and the resolution process?