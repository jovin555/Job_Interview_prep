# medical-devices — Day 7

## Q1: During IEC 60601-1 leakage current testing, you measure elevated patient leakage current on a BF-type applied part. How would you approach diagnosing and resolving this?

**Answer:** I would start by confirming the measurement setup is correct — verifying the test equipment calibration, the measurement network (MD) used for BF-type applied parts, and that the device is configured in normal and single-fault conditions per IEC 60601-1 Table 4. Elevated patient leakage current typically points to one of several root causes: inadequate isolation between the patient circuit and mains or earth, a compromised protective earth connection, or excessive capacitance coupling across the isolation barrier.

My diagnostic approach would be systematic. First, I'd check the physical isolation — verify that creepage and clearance distances between the patient circuit and any mains-connected or earth-referenced circuits meet the requirements for the device's insulation class (typically 2×MOPP for patient connections). I'd inspect the PCB layout for any contamination, solder bridges, or flux residue that could create leakage paths, especially around optocouplers, isolation transformers, or capacitive coupling elements.

Next, I'd measure the isolation impedance directly — using a megohmmeter to check that the isolation resistance meets the minimum 4 MΩ at 500 V DC for a single MOOP, or higher for 2×MOPP. If the resistance is low, I'd look for component damage or design issues. If resistance is acceptable but leakage current is still high, the culprit is often capacitive coupling — the parasitic capacitance across the isolation barrier (e.g., transformer inter-winding capacitance, optocoupler capacitance) can create a displacement current path. In that case, I'd evaluate whether the design can reduce this capacitance (e.g., using a shielded isolation transformer with a Faraday shield connected to protective earth) or whether adding a Y-capacitor from the patient circuit to earth (within the 5 nF limit for BF-type) can shunt the leakage current safely.

Finally, I'd verify the fix by repeating the leakage current test under all required conditions, including reversed mains polarity and single-fault conditions like an interrupted protective earth.

**Possible follow-ups:** How would you distinguish between a resistive leakage path and a capacitive coupling issue during diagnosis? What documentation would you update after resolving the issue?

---

## Q2: How would you approach creating a clinical evaluation report (CER) for a novel medical device that has no substantially equivalent predicate device on the market?

**Answer:** For a novel device without a predicate, the CER must rely primarily on clinical investigation data rather than equivalence arguments. I would structure the approach around MEDDEV 2.7/1 Rev.4 or the relevant regulatory guidance (e.g., MDR Annex XIV for EU, or FDA guidance for 510(k) de novo classification).

First, I'd establish the scope and plan — defining the device's intended purpose, clinical indications, target population, and the specific clinical claims. This becomes the foundation for the clinical evaluation plan (CEP), which outlines the methodology for identifying, appraising, and analyzing clinical data. Since there's no predicate, the CEP must specify that the evaluation will rely on: (1) a systematic literature review to identify any relevant clinical data from similar devices or analogous technologies, (2) data from the device's own clinical investigations if available, and (3) any post-market surveillance data from early feasibility studies.

The literature search protocol is critical here — I'd work with a clinical affairs specialist to define search terms across multiple databases (PubMed, Embase, Cochrane), with clear inclusion/exclusion criteria. The search should capture not just direct clinical outcomes but also safety data, adverse events from analogous technologies, and any published bench or animal studies that support the device's safety and performance.

For the appraisal phase, each identified study would be assessed for scientific validity, relevance, and quality using established appraisal tools (e.g., CASP checklists). The analysis phase would synthesize the evidence, identifying gaps and limitations. If the literature alone cannot demonstrate sufficient clinical evidence, the CER would conclude that a clinical investigation is necessary — and that becomes a design input for the next phase of development.

The final CER document would include a clear statement of the residual clinical uncertainty, a justification for why the benefit-risk profile is acceptable despite the lack of predicate data, and a plan for post-market clinical follow-up (PMCF) to collect additional real-world evidence after market entry.

**Possible follow-ups:** How would you handle a situation where the literature review reveals conflicting evidence about the safety of a similar technology? What role does the notified body or regulatory reviewer play in accepting a CER for a novel device?

---

## Q3: A field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that requires immediate attention under the post-market surveillance and complaint handling system. My approach would follow a structured investigation aligned with ISO 13485 and the device's risk management file per ISO 14971.

First, I'd ensure patient safety by assessing the severity of the reported reactions — are these mild erythema cases or more serious chemical burns? I'd work with the quality and regulatory teams to determine if a field safety corrective action (FSCA) or recall is warranted based on the severity and frequency. If the irritation is widespread or severe, I'd recommend temporarily suspending distribution while the investigation proceeds.

The investigation itself would have several parallel tracks. One track is the clinical assessment — gathering detailed information from the complainants: how long was the pad in contact with skin, was it used per instructions, were there any pre-existing skin conditions, and what was the exact nature of the irritation? This helps determine if the issue is device-related or user-related.

A second track is the material and manufacturing investigation. I'd request retained samples from the same lot(s) as the complaint devices, plus any raw material batch records for the silicone. The investigation would include: (1) reviewing the material certification and biocompatibility test reports (ISO 10993-10 for skin sensitization, ISO 10993-5 for cytotoxicity), (2) checking if there were any changes in the silicone formulation, curing process, or mold release agents that could introduce irritants, (3) testing the suspect pads for leachables or residual chemicals (e.g., platinum catalyst residues, unreacted monomers, or mold release compounds), and (4) verifying the manufacturing process controls — cure time, temperature, and post-processing steps like cleaning or sterilization.

A third track is the risk management file review. I'd re-evaluate the original risk analysis for skin irritation — was this hazard identified? Were the risk control measures (material selection, biocompatibility testing, process validation) adequate? If the investigation finds a new hazard or that existing controls were insufficient, I'd initiate a design change or process change, update the risk management file, and implement corrective and preventive actions (CAPA).

Throughout the process, I'd document every step in the complaint handling system, maintain traceability to the device lot numbers, and communicate findings to the relevant regulatory authorities as required (e.g., Health Canada mandatory problem reporting, FDA MDR, or EU vigilance reporting).

**Possible follow-ups:** How would you determine whether the root cause is a material contamination issue versus a design issue with the silicone formulation itself? What criteria would you use to decide whether to issue a field safety notice versus a full recall?

---

## Q4: How would you approach verifying that a medical device's firmware meets IEC 62304 requirements for a Class C software safety classification?

**Answer:** Class C is the highest software safety classification under IEC 62304, meaning the software can contribute to a hazardous situation that results in death or serious injury. The verification approach must be correspondingly rigorous, covering all phases of the software development lifecycle.

I would start by confirming the software safety classification is correct — reviewing the hazard analysis to ensure that all software items that could contribute to Class C hazards are properly identified. If the classification is confirmed, the verification plan must address all the mandatory activities for Class C per IEC 62304 Table A.1, including: software unit verification, software integration and integration testing, system testing, and software release.

For unit verification, Class C requires that every software unit undergo both static analysis and dynamic testing. I'd ensure the team uses a combination of methods: code reviews or inspections for every unit (not just sampling), static analysis tools to detect coding standard violations (e.g., MISRA C) and potential runtime errors, and unit testing with structural coverage analysis. The coverage criteria for Class C are more stringent — typically requiring modified condition/decision coverage (MC/DC) for the highest-risk modules, or at minimum statement and branch coverage for all units.

For integration testing, I'd verify that the test plan covers all software item interfaces, data flows between units, and the interaction with hardware. The integration tests should trace back to the software architecture and detailed design. For Class C, anomaly response testing is also required — verifying that the software handles error conditions gracefully and transitions to safe states as specified in the risk controls.

System testing must verify that the software meets all software requirements, including safety-related requirements. I'd ensure the test cases cover normal operation, boundary conditions, and fault injection scenarios. The traceability matrix linking software requirements to test cases must be complete and auditable.

Finally, for software release, I'd verify that the release documentation includes: a known anomalies list with risk assessment for each unresolved issue, a software version identifier, a summary of all verification activities performed, and a statement that the software is ready for release based on predefined release criteria. For Class C, the manufacturer must also document that the software has been verified to not contain any residual defects that could lead to an unacceptable risk.

Throughout this process, I'd ensure that all verification results are documented in the software development file, with clear pass/fail criteria and sign-offs. Any deviations or non-conformances would be tracked through the problem resolution process per IEC 62304 Clause 9.

**Possible follow-ups:** How would you handle a situation where achieving MC/DC coverage is impractical for a particular module due to compiler optimizations or hardware dependencies? What is the relationship between software verification and the risk management process for a Class C device?

---

## Q5: You're the lead engineer on a medical device project. During a design review, the quality manager insists that a new risk control measure must be added to address a hazard with an estimated risk level that the team considers negligible. The schedule impact would be significant. How would you handle this situation?

**Answer:** This is a common tension in medical device development — balancing risk management rigor with project constraints. My approach would be to facilitate a structured, evidence-based discussion rather than letting it become a confrontation between engineering and quality.

First, I'd acknowledge the quality manager's concern and thank them for raising it — their role is to ensure patient safety, and that should never be dismissed. Then I'd propose that we step through the risk management process together to examine the hazard more carefully. I'd pull up the risk management file and review the specific hazard, the sequence of events leading to the hazardous situation, and the existing risk controls. The key question is whether the risk estimation is accurate.

I'd suggest we re-evaluate the risk estimation using the established risk acceptance criteria from the risk management plan. If the team rated the risk as negligible, I'd ask: what severity and probability were assigned? How were these determined? Is there any clinical data, standards guidance, or historical field data that supports this estimation? If the quality manager has specific concerns about the estimation methodology, we should address those directly — perhaps the severity was underestimated, or the probability of occurrence was based on assumptions that need validation.

If after this review the evidence still supports a negligible risk level, I'd ask the quality manager to articulate what specific residual risk they find unacceptable. Sometimes the concern is not about the numerical risk level but about the lack of objective evidence — in which case the solution might be to add a verification step (e.g., a test to confirm the risk control is effective) rather than a new design control. Other times, the concern might be about the risk acceptance criteria themselves — perhaps they need to be revisited for this particular hazard type.

If we genuinely disagree after a thorough review, I'd escalate to the project's risk management board or the designated risk management review team, which typically includes clinical, regulatory, and management representatives. The decision should be documented in the risk management file with the rationale for whichever path is chosen. If the quality manager's position is ultimately overruled, that decision must be formally documented with justification. Conversely, if the evidence supports adding the control, I'd work with the team to find the least schedule-impacting way to implement it — perhaps a phased approach where the control is added in the next design iteration rather than holding up the current release.

The key principle is that risk management decisions should be based on objective evidence and documented rationale, not on schedule pressure or authority. My role as lead engineer is to ensure that the process is followed correctly and that all voices are heard, while keeping the project moving forward.

**Possible follow-ups:** How would you handle a situation where the quality manager refuses to accept the documented rationale and continues to block the design review sign-off? What role does the risk management board play in resolving such disagreements?