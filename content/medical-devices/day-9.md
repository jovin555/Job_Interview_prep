# medical-devices — Day 9

## Q1: During IEC 60601-1 testing, your medical device fails the patient leakage current test under normal condition (NC) with a measurement of 120 µA on a BF-type applied part, where the limit is 100 µA. How would you approach diagnosing and resolving this?

**Answer:** I'd start by understanding the measurement setup — the test typically applies mains voltage to the applied part through a measuring device (MD) while the device is powered and operating normally. A 20 µA exceedance suggests a specific leakage path rather than a systemic design flaw.

First, I'd isolate the leakage path by systematically disconnecting sub-circuits from the patient connection. The most common contributors are:
- **Y-capacitors** on the secondary side of the isolation barrier — these intentionally couple small AC currents to ground for EMI filtering. If present, I'd check whether their values are appropriate for medical-grade isolation (typically limited to a few nF total).
- **Creepage/clearance violations** — moisture or contamination on the PCB across the isolation barrier can create resistive leakage paths. I'd inspect the PCB under magnification, particularly around optocouplers, isolated DC-DC converters, and signal isolation components.
- **Transformer inter-winding capacitance** — if the device uses an isolated power supply, the primary-to-secondary capacitance of the transformer can couple leakage current. A Faraday shield between windings can reduce this.

I'd measure leakage current at each sub-assembly to identify the dominant contributor. If it's capacitive coupling from EMI filtering, I'd redistribute the Y-capacitance or use a lower-value capacitor while verifying the device still passes emissions testing. If it's a creepage issue, I'd look for PCB contamination, insufficient slotting, or inadequate conformal coating coverage. In a battery-powered medical sensor device, I've seen cases where a small capacitor placed across the isolation barrier for signal integrity was the culprit — removing or reducing it resolved the issue while maintaining signal quality.

**Possible follow-ups:** How would you distinguish between capacitive-coupled leakage and resistive leakage during your diagnosis? What documentation would you update after implementing the fix?

---

## Q2: How would you approach developing a software test plan for a medical device that uses machine learning for diagnostic decision support, given that IEC 62304 doesn't explicitly address AI/ML?

**Answer:** This is an emerging area where the regulatory framework is still evolving, so I'd take a risk-based approach grounded in existing standards while anticipating future guidance.

First, I'd classify the software per IEC 62304 — the ML component's safety classification depends on the severity of harm if it produces an incorrect output. For diagnostic decision support, this could be Class B or C depending on whether the clinician can independently verify the recommendation. I'd document this classification rationale in the software safety classification document.

For the ML model specifically, I'd extend traditional verification and validation approaches:

**Verification (did we build it right?):**
- Unit tests for data preprocessing and feature extraction pipelines
- Integration tests for the interface between the ML model and the rest of the firmware
- Model performance metrics on held-out test datasets (sensitivity, specificity, positive predictive value)
- Robustness testing against input variations (sensor noise, missing data, edge cases)

**Validation (did we build the right thing?):**
- Clinical validation using retrospective patient data, comparing model output against ground truth (e.g., expert clinician consensus)
- Usability testing to ensure the clinician understands when to trust vs. override the recommendation
- Stress testing with adversarial inputs or out-of-distribution data

I'd also address the "black box" concern by implementing explainability features — for example, outputting confidence scores or highlighting which input features drove the decision. The risk management file would include specific hazards related to ML errors (e.g., false negatives leading to delayed treatment) with corresponding risk controls like mandatory clinician review before any action is taken.

For regulatory submission, I'd reference FDA's guidance on AI/ML-based SaMD and ISO/IEC TR 24027 on bias in AI systems, even though they aren't directly harmonized with IEC 62304. The key is demonstrating a rigorous, documented process that addresses the unique risks of adaptive algorithms.

**Possible follow-ups:** How would you handle model updates after market release — would you need a new 510(k)? How would you test for dataset shift or concept drift in the field?

---

## Q3: A medical device you're developing uses a touchscreen interface that must be usable by clinicians wearing gloves in an operating room environment. How would you approach verifying that the user interface meets IEC 60601-1-6 usability engineering requirements?

**Answer:** IEC 60601-1-6 requires a usability engineering process per IEC 62366-1, which is a risk-based approach to identifying and mitigating use errors. I'd structure this around the usability engineering lifecycle.

First, I'd conduct a **formative usability evaluation** early in development. This would involve:
- Observing clinicians (surgeons, nurses, perfusionists) interacting with a prototype or mockup while wearing surgical gloves
- Identifying specific use errors: accidental touches, difficulty reading the screen under bright OR lights, inability to activate controls with gloved fingers
- Documenting the context of use: ambient lighting levels, typical viewing distance, whether the device is used during sterile procedures

Based on these findings, I'd refine the design — for example, increasing button sizes to at least 15-20 mm for gloved operation, using capacitive touch sensors with sufficient sensitivity through latex/nitrile gloves, and ensuring display contrast is adequate under 1000 lux ambient lighting.

The **summative usability evaluation** (formal validation) would test the final design with representative users performing critical tasks. I'd define the following:
- **Critical tasks** identified through the risk management process (e.g., setting alarm limits, starting/stopping therapy, acknowledging alarms)
- **Acceptance criteria** based on the severity of potential harm from use errors — for example, zero critical use errors, and a maximum acceptable rate of minor errors
- **Test environment** that simulates OR conditions: bright lights, ambient noise, time pressure, and clinicians wearing full PPE including gloves

I'd also address the **alarm management** aspects per IEC 60601-1-8 — ensuring that visual alarms on the touchscreen are distinguishable from other on-screen elements, and that the touchscreen doesn't interfere with the ability to acknowledge or silence alarms quickly.

The usability engineering file would include the use specification, identified use errors and their risk control measures, and the summative evaluation report demonstrating that residual risks from use errors are acceptable.

**Possible follow-ups:** How would you handle the trade-off between making buttons large enough for gloved use versus fitting all necessary controls on a single screen? What if the summative evaluation reveals a use error you didn't anticipate?

---

## Q4: You're the lead engineer on a medical device project that uses a wireless body-worn sensor to transmit patient data to a bedside monitor. During IEC 60601-1-2 immunity testing, the device exhibits intermittent data dropouts when exposed to a 10 V/m radiated RF field at 400 MHz. How would you approach diagnosing and resolving this?

**Answer:** This is a common challenge with wireless medical devices — the radiated RF field can couple into the device's circuitry and disrupt either the wireless communication link or the sensor data acquisition itself. I'd approach this systematically.

First, I'd characterize the failure more precisely:
- Does the dropout correlate with the RF field being on/off, or is there a latency effect?
- Does the dropout occur at the wireless receiver, the sensor front-end, or the data processing path?
- Is the dropout frequency-specific (suggesting a resonance) or broadband?

I'd set up the test with diagnostic tools: a spectrum analyzer connected to a near-field probe to identify which PCB traces or components are picking up the 400 MHz energy, and an oscilloscope monitoring critical signals (sensor ADC output, SPI/I2C lines, wireless module control signals) during exposure.

Common root causes and mitigations:

**1. RF coupling into sensor analog front-end:**
The 400 MHz field can be rectified by amplifier input stages, creating DC offsets that corrupt sensor readings. I'd check if the sensor signal chain has adequate filtering — a low-pass filter with cutoff below 10 MHz would attenuate 400 MHz by 60+ dB. If the sensor bandwidth allows, I'd add ferrite beads or LC filters at the input.

**2. RF interference with the wireless module:**
The wireless module (e.g., Bluetooth, Zigbee) may desensitize when the external field is near its operating frequency. I'd check the module's datasheet for out-of-band rejection specifications. If the 400 MHz field is far from the module's operating band, the issue is likely conducted coupling through the antenna feed or power supply lines. I'd add common-mode chokes on the antenna cable and ensure the module's ground plane is continuous.

**3. Conducted susceptibility through cables:**
If the sensor connects to the body via a cable, that cable acts as an antenna. I'd verify that cable shielding is properly terminated (360-degree接地 at both ends) and that any exposed conductors are minimized. Ferrite cores on the cable near the device connector can help.

**4. Power supply noise coupling:**
The RF field can couple into the battery or power management circuitry, causing voltage drops that reset the wireless module. I'd measure the supply voltage at the module during RF exposure and add additional decoupling if needed.

After implementing the fix, I'd repeat the immunity test at multiple frequencies across the 80 MHz to 2.7 GHz range to ensure no new resonances are introduced. The fix would be documented in the risk management file as a risk control measure for electromagnetic interference.

**Possible follow-ups:** How would you determine whether the fix is sufficient without running the full immunity test suite each time? What if the fix (e.g., adding a ferrite bead) degrades the wireless module's transmit performance?

---

## Q5: A field complaint reports that a medical device's rechargeable battery is swelling after 6-12 months of use in a hospital setting. The device is used for continuous patient monitoring and the battery is not user-replaceable. How would you approach the investigation and corrective action process?

**Answer:** Battery swelling in a medical device is a serious safety issue — it can lead to device failure, fire risk, or physical damage to the enclosure. I'd follow a structured 8D (eight disciplines) or CAPA (corrective and preventive action) process.

**Immediate actions (containment):**
- Issue a field safety notice to customers describing the symptoms (swelling) and instructing them to inspect devices and quarantine any with visible swelling
- Determine the affected lot numbers or date codes based on the complaint data — was this a single batch of batteries or a systemic issue?
- If the swelling poses an immediate fire risk, escalate to a field safety corrective action (FSCA) with the relevant regulatory authority

**Root cause investigation:**
I'd gather the swollen batteries and perform:
- **Visual and dimensional analysis** — measure the swelling extent, check for venting, electrolyte leakage
- **Electrical testing** — measure open-circuit voltage, internal resistance, capacity (if safely possible)
- **Disassembly** (by a battery lab) — inspect cell construction, separator integrity, electrode alignment
- **Charge/discharge cycling** — replicate the hospital usage profile (e.g., continuous charging with occasional discharge cycles) to see if swelling reproduces

Common root causes for Li-ion swelling:
- **Overcharging** — the charging algorithm may be pushing voltage too high, especially at elevated temperatures. I'd review the charge termination criteria (constant voltage setpoint, termination current threshold)
- **High temperature exposure** — hospital environments can be warm, and the device may generate internal heat. I'd check if the battery temperature during charging exceeds the manufacturer's specification
- **Cell quality issue** — the cell manufacturer may have changed electrode materials or electrolyte formulation without notification
- **Mechanical stress** — the battery compartment may be too tight, causing pressure on the cells during thermal expansion

**Corrective action:**
Depending on the root cause, I might:
- Adjust the charging algorithm (lower float voltage, add temperature-compensated charging)
- Add a temperature sensor to the battery pack and implement charge termination if temperature exceeds a threshold
- Switch to a different cell model with higher temperature tolerance
- Redesign the battery compartment to allow for slight expansion without stress on the cells

**Verification:**
I'd run accelerated life testing (e.g., continuous charging at 40°C for 500 cycles) to verify the fix doesn't cause swelling. The verification results would be documented in the CAPA record.

**Preventive action:**
I'd update the battery qualification process to include long-term float charging tests at elevated temperature as a routine part of supplier qualification. I'd also review the incoming inspection criteria for battery cells.

**Possible follow-ups:** How would you communicate this issue to the regulatory authority — would you file a medical device report (MDR) or a field safety corrective action (FSCA)? What if the battery supplier claims the issue is caused by your charging circuit, not their cells?