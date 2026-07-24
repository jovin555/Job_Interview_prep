# medical-devices — Day 4

## Q1: How would you approach selecting and qualifying a replacement component for a medical device when the original part is discontinued by the manufacturer?

**Answer:** This is a common challenge in medical device lifecycle management, and the approach needs to be systematic because any component change can affect safety, performance, or regulatory status. I would start by understanding the original component's role in the device — is it a critical-to-safety component, a passive filtering element, or a general-purpose part? That determines the level of scrutiny required.

For a critical component, I would first identify potential replacements by reviewing the original manufacturer's recommended substitutes or cross-referencing parametric searches. Then I'd create a comparison matrix covering electrical parameters, package, thermal characteristics, and any environmental ratings (e.g., if the device undergoes sterilization). Next, I'd assess whether the replacement requires any PCB layout changes — even pin-compatible parts can have different parasitic characteristics that affect signal integrity or EMI performance.

The regulatory pathway depends on whether the change is considered a "significant change" under applicable regulations. I would evaluate whether the replacement affects the device's safety or performance characteristics as defined in the original design inputs. If it does, this may trigger a new 510(k) submission or equivalent. Even if not, the change must be documented in the design history file, with verification testing (e.g., functional testing, EMC pre-compliance, safety testing per IEC 60601) to confirm the replacement doesn't degrade performance. A risk assessment per ISO 14971 should also be updated to evaluate any new hazards introduced by the change.

**Possible follow-ups:** How would you determine whether a component change is "significant" enough to require a new regulatory submission? What testing would you prioritize if the replacement is in the power supply section of a patient-connected device?

---

## Q2: During IEC 60601-1 leakage current testing, you measure elevated patient leakage current on a BF-type applied part. How would you diagnose and resolve this?

**Answer:** Elevated patient leakage current in a BF-type applied part is a serious safety concern because it indicates that current could flow through the patient under normal or single-fault conditions. I would approach this systematically.

First, I'd verify the measurement setup — is the test equipment properly calibrated, and is the measurement being taken under the correct conditions (normal polarity, reversed polarity, neutral open, etc. per IEC 60601-1 Table 4)? Measurement technique matters; probe placement and lead routing can introduce artifacts.

Assuming the measurement is valid, I'd isolate the source by systematically disconnecting sub-circuits. The leakage path could be through the power supply's Y-capacitors to ground, through the isolation barrier in the signal chain, or through parasitic capacitance in the transformer or optocouplers. I'd measure leakage current at each stage: at the mains input, after the power supply, and at the patient connection point.

Common causes include: excessive Y-capacitance between primary and secondary sides of the power supply; inadequate creepage/clearance in the isolation barrier (possibly due to contamination or moisture); a damaged or incorrectly specified isolation component; or a layout issue where a high-voltage trace runs too close to the patient circuit. I'd inspect the PCB for any contamination, solder bridges, or conformal coating defects. If the design uses a medical-grade isolated DC-DC converter, I'd verify its rated isolation capacitance and leakage current specifications.

The resolution might involve reducing Y-capacitance (while maintaining EMI compliance), improving the physical isolation barrier, adding a guard trace, or selecting a different isolation component with lower coupling capacitance. Any change would need to be verified against both leakage current limits and EMC requirements, since reducing Y-capacitance can worsen conducted emissions.

**Possible follow-ups:** How would you balance reducing Y-capacitance to lower leakage current against the need to meet conducted emissions limits? What role does the patient protection resistor (if present) play in this scenario?

---

## Q3: How would you approach creating a clinical evaluation report (CER) for a novel medical device that has no substantially equivalent predicate device on the market?

**Answer:** For a novel device without a predicate, the clinical evaluation process is more demanding because you cannot rely on equivalence claims. The approach follows the MEDDEV 2.7/1 Rev.4 framework (or equivalent guidance depending on jurisdiction).

I would start by defining the device's intended purpose, clinical indications, and target patient population clearly — this forms the basis for the clinical evaluation plan (CEP). The CEP should specify the clinical questions to be answered, the endpoints of interest, and the acceptance criteria for safety and performance.

For a novel device, the literature search becomes critical but also challenging. I would conduct a systematic literature review covering: similar technologies used for different indications; analogous physiological measurement principles; relevant clinical studies on the underlying therapeutic or diagnostic approach; and safety data from related device categories. The search strategy needs to be documented, reproducible, and justified — including databases searched, search terms, inclusion/exclusion criteria, and date ranges.

If the literature review reveals insufficient clinical data to demonstrate safety and performance, the CER will identify this gap and recommend that a clinical investigation (clinical trial) is necessary. The CER is an iterative document — it should be updated as new clinical data becomes available. For a novel device, the initial CER might conclude that the available evidence is insufficient, which then drives the requirement for a formal clinical study.

Throughout the process, I would work closely with clinical affairs and regulatory affairs colleagues to ensure the CER aligns with the regulatory strategy and that any clinical investigation is designed to address the specific gaps identified in the evaluation.

**Possible follow-ups:** How would you determine whether a clinical investigation is truly necessary versus being able to justify safety and performance through bench testing and literature alone? What role does the risk management file play in defining the clinical evaluation endpoints?

---

## Q4: A field complaint comes in reporting that a medical device's patient-contacting sensor caused skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that could involve biocompatibility, manufacturing, or clinical use issues. I would approach it as a structured investigation following a CAPA (Corrective and Preventive Action) process, with urgency due to the patient safety implications.

First, I would ensure the complaint is properly documented and escalated according to the company's complaint handling procedures. If the skin irritation is severe or widespread, this could trigger a Field Safety Corrective Action (FSCA) or recall, so I would involve regulatory affairs immediately.

The investigation would begin by gathering all available information: the specific device lots involved, the patient population, the nature and severity of the irritation, and any photos or clinical notes. I would request the affected devices or sensors be returned for analysis. If multiple lots are involved, I'd look for commonalities in manufacturing date, raw material batches, or sterilization cycles.

The root cause investigation would branch into several areas:
- **Material analysis:** Was the sensor material changed? Did a supplier change their formulation or processing? I would request material certifications and batch records for the sensor material, and consider sending samples for chemical analysis (e.g., FTIR, GC-MS) to check for contaminants or degradation products.
- **Manufacturing process:** Were there any deviations in cleaning, sterilization, or packaging? Residual processing chemicals (mold release agents, cleaning solvents) could cause irritation. I'd review manufacturing records and consider process capability studies.
- **Biocompatibility:** Was the material originally tested per ISO 10993? If so, were the tests representative of the actual clinical use conditions (duration of contact, frequency of use, patient population)? Some materials that pass cytotoxicity testing can still cause irritation in a subset of patients.
- **Clinical use:** Could the irritation be related to how clinicians or patients use the device — e.g., adhesive application technique, cleaning agents used by the hospital, or patient-specific factors?

Once the root cause is identified, the corrective action might involve: changing the sensor material; modifying the manufacturing process (e.g., additional rinsing step); updating labeling to warn about potential irritation; or issuing a field correction to replace affected devices. The effectiveness of the corrective action must be verified, and the risk management file updated to reflect the new hazard and any residual risk.

**Possible follow-ups:** How would you prioritize between a material change versus a labeling change as the corrective action? What information would you need to decide whether a recall is necessary versus a field safety notice?

---

## Q5: How would you approach verifying that a medical device's firmware meets IEC 62304 requirements for a Class C software safety classification?

**Answer:** Class C is the highest software safety classification under IEC 62304, meaning the software can contribute to a hazardous situation that could result in death or serious injury. The verification approach must be correspondingly rigorous.

I would start by ensuring the software development process follows IEC 62304's requirements for Class C, which include: a documented software development plan; detailed software requirements specification (SRS); software architecture description; and detailed design documentation. Verification activities are required at each level.

For unit-level verification, every software unit must be tested against its detailed design. For Class C, this typically requires both static analysis and dynamic testing with structural coverage analysis (statement coverage, branch coverage, and MC/DC — modified condition/decision coverage). I would use a combination of automated static analysis tools to check for coding standard violations (e.g., MISRA C) and potential runtime errors, plus unit testing frameworks to exercise each function with defined inputs and expected outputs.

Integration testing verifies that software units work together correctly according to the architecture. For Class C, this includes testing all inter-unit interfaces, data flows, and task scheduling behavior in the RTOS environment. I would create test cases that exercise normal operation, boundary conditions, and error handling paths.

System-level testing verifies the software against the software requirements specification. This includes functional testing, performance testing, and robustness testing (e.g., what happens when a sensor fails or communication is lost). For a medical device, this testing should be performed on the actual hardware or a representative hardware-in-the-loop setup.

Beyond testing, IEC 62304 requires a software anomaly process — all defects found during verification must be documented, assessed for severity, and resolved before release. For Class C, there must be documented evidence that all identified anomalies are resolved or that residual anomalies are justified as not affecting safety.

Finally, the software verification must be traceable back to the software requirements. A traceability matrix linking requirements to test cases to test results is essential for the regulatory submission. The software release criteria must be defined in the software development plan, and no release should occur until all verification activities are complete and accepted.

**Possible follow-ups:** How would you handle a situation where achieving full MC/DC coverage is impractical for a particular module (e.g., due to compiler optimizations or hardware dependencies)? What role does the risk management file play in determining which software functions require the highest level of verification rigor?