# medical-devices — Day 49

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a situation where the device's non-volatile memory becomes corrupted during normal operation, given that the device must continue monitoring and displaying physiological data in real time?

**Answer:** I'd start by defining what "corrupted" means for each type of data stored — configuration parameters, calibration constants, logged physiological data, and the firmware image itself all have different criticality and recovery requirements. The test strategy needs to verify both detection and response for each category.

For detection, I'd use fault injection at the driver level — corrupting individual bytes, flipping bits in checksums, writing invalid CRC values, and simulating partial writes or power loss during write operations. The firmware should detect corruption through CRC or checksum verification at startup and during periodic integrity checks.

For response, the key distinction is between safety-critical and non-critical data. If calibration constants are corrupted, the device may need to enter a safe state or use default values with a prominent warning, because continuing to monitor with incorrect calibration could produce misleading physiological readings. If only logged data is corrupted, the device should quarantine or discard the bad records while continuing real-time monitoring — the display and alarm functions must not be blocked by a storage failure.

I'd structure the test matrix around three dimensions: corruption type (bit flips, stuck bits, zeroed regions, partial writes), data region affected (config, calibration, logs, code), and device state when corruption occurs (idle, actively monitoring, mid-alarm). Each combination should be tested to verify the device either recovers gracefully or enters a defined safe state, and that any user notification is accurate and actionable.

**Possible follow-ups:** How would you verify that the corruption detection mechanism itself doesn't introduce a single point of failure? What recovery behavior would you consider acceptable for corrupted calibration data versus corrupted log data?

---

## Q2: During a design review for a medical device that monitors fetal and maternal heart rates during labor, the firmware engineer proposes implementing heart rate variability (HRV) analysis as a software feature to detect fetal distress earlier than current methods. The algorithm is novel and has not been clinically validated. How would you approach evaluating this proposal?

**Answer:** This is fundamentally a question about scope, evidence, and risk, not just technical feasibility. I'd approach it in three stages.

First, I'd clarify the intended use. If the feature is meant to *alert* clinicians to fetal distress, that's a diagnostic claim with significant regulatory implications — it would likely require clinical validation, potentially a clinical study, and would change the risk profile of the device substantially. If it's meant to be an *informational display* of HRV metrics that clinicians can interpret alongside existing data, the regulatory burden is different but still requires careful consideration of usability and training.

Second, I'd assess the evidence gap. A novel, unvalidated algorithm for detecting fetal distress raises questions about sensitivity and specificity — false alarms could lead to unnecessary interventions (potentially C-sections), while missed detections could have catastrophic consequences. I'd ask what data exists to support the algorithm's performance, whether it has been tested against annotated clinical datasets, and what the proposed alarm thresholds are based on.

Third, I'd evaluate the regulatory and risk management path. Adding a new clinical decision-support feature would likely require updating the risk management file, potentially reclassifying the software under IEC 62304, and could require new clinical evidence for regulatory submission. I'd recommend scoping the feature as a research/evaluation module initially — perhaps collecting HRV data alongside standard monitoring in a non-alerting mode to build an evidence base — while keeping the cleared device functionality unchanged. This allows the clinical question to be answered without delaying the current submission or introducing unvalidated alerts into patient care.

**Possible follow-ups:** How would you handle pressure from the clinical team to include the feature in the initial release? What criteria would you use to determine when the algorithm has sufficient evidence to be considered for an alerting function?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure uterine contraction pressure during labor, where the sensor is a pressure transducer in contact with the patient's abdomen and the device must maintain specified accuracy across a range of patient body habitus (e.g., BMI from 18 to 45)?

**Answer:** The core challenge here is that the measurement chain includes a biological interface — the patient's abdomen — that varies significantly across the intended population. A test plan that only verifies the transducer and electronics in isolation would miss the dominant source of variability.

I'd structure the verification in layers. First, bench-level testing of the transducer and signal chain using calibrated pressure sources to verify the electrical and mechanical accuracy independent of the patient interface. This establishes the baseline performance of the hardware.

Second, I'd use physical phantoms or test fixtures that simulate different tissue thicknesses and mechanical properties — mimicking the range of body habitus from thin to obese patients. The fixture would need to replicate not just static pressure but also the dynamic characteristics of uterine contractions, since tissue damping and coupling affect the waveform shape, not just the peak amplitude. This is where I'd expect to find the most significant accuracy variation.

Third, I'd consider whether clinical validation data is needed to supplement bench testing. If the phantom models can't adequately represent the range of tissue properties, a clinical study comparing the device against an intrauterine pressure catheter (the reference standard) across different BMI groups may be necessary. This is a common situation for external tocodynamometry — the sensor measures abdominal wall displacement or pressure, which correlates with intrauterine pressure but is affected by tissue properties.

I'd also include environmental factors in the test matrix — temperature and humidity effects on the transducer, sensor placement variability, and motion artifacts from patient movement or breathing. The test plan should document the rationale for each test method and any limitations in the verification approach, which feeds into the risk management file and clinical evaluation.

**Possible follow-ups:** How would you determine whether bench testing with phantoms is sufficient or whether clinical data is required? What acceptance criteria would you set for accuracy across the BMI range?

---

## Q4: You're the lead engineer on a medical device project. During a design review, the clinical team requests a change that would improve usability but would require a significant hardware revision and delay the regulatory submission by three months. How would you evaluate and respond to this request?

**Answer:** I'd start by understanding the clinical rationale in depth — not just what the change is, but what problem it solves and how severe that problem is. I'd ask the clinical team to describe specific scenarios where the current design creates difficulty or risk, and whether there are workarounds that clinicians currently use. A usability issue that causes frequent errors or requires complex workarounds is different from one that's merely inconvenient.

Next, I'd assess the technical and regulatory impact systematically. A significant hardware revision means new layout, potentially new components, re-verification of affected requirements, and re-running EMC and safety testing — the three-month estimate may or may not be realistic. I'd work with the team to scope the actual impact: does the change affect patient safety or just ergonomics? Does it change the applied part configuration or isolation requirements? Would it require re-testing under IEC 60601-1, or just usability validation under IEC 60601-1-6?

I'd also consider whether there's a middle path. Can the usability improvement be partially addressed through a firmware change, a different accessory, or a labeling/training update for the initial release, with the hardware revision planned for the next iteration? This isn't always possible, but it's worth exploring before accepting the full delay.

If the change is genuinely important for patient safety or has a strong clinical justification, I'd present the trade-off to the project stakeholders with a clear analysis: what the delay costs (market timing, revenue, competitive position), what the risk of not making the change is (usability errors, clinician adoption barriers, potential safety events), and what the technical alternatives are. The decision ultimately belongs to the project sponsor, but my role is to give them an honest, complete picture — not to advocate for schedule over safety or vice versa.

**Possible follow-ups:** How would you handle a situation where the clinical team's request is based on anecdotal feedback from a few clinicians rather than systematic usability data? What criteria would you use to decide whether to escalate the decision to senior management?

---

## Q5: How would you approach verifying that a medical device's wireless communication (e.g., Bluetooth Low Energy) meets both the IEC 60601-1-2 immunity requirements and the wireless coexistence requirements for a hospital environment?

**Answer:** These are two distinct but related verification efforts. IEC 60601-1-2 immunity testing verifies that the device continues to function safely when exposed to specified electromagnetic disturbances — including radiated RF from other wireless devices — while wireless coexistence is about ensuring the device's own wireless link remains functional in a realistic RF environment with other transmitters present.

For the IEC 60601-1-2 immunity portion, I'd follow the standard's test matrix: radiated RF immunity at the specified field strengths (typically 3 V/m for non-life-supporting and 10 V/m for life-supporting devices in the 80 MHz to 2.7 GHz range), conducted RF immunity on cables, ESD, and magnetic field immunity. During these tests, I'd define pass criteria specific to the wireless function — the device must not reset, must not generate false alarms, and any degradation in wireless communication must not compromise the safety-critical monitoring function. The wireless link may drop temporarily during RF immunity testing, but the device should maintain its local monitoring and alarm functions and should indicate a communication failure to the user.

For coexistence testing, I'd take a more practical approach. The goal is to verify that the BLE link maintains adequate performance when other wireless devices — Wi-Fi, other BLE devices, Zigbee, cordless phones — are operating nearby. I'd set up a test environment with representative interfering sources at various distances and channel overlaps, then measure key link metrics: packet error rate, latency, reconnection time, and the time to detect and report a lost link. The acceptance criteria should be tied to the clinical use case — for continuous monitoring, brief data dropouts may be acceptable if the device detects and reports them, but the monitoring function itself must not be compromised.

I'd also consider the hospital environment specifically: BLE operates in the 2.4 GHz ISM band alongside Wi-Fi, which can be dense in hospitals. Channel selection, adaptive frequency hopping, and transmit power all affect coexistence performance. I'd verify that the device's BLE implementation uses the available mechanisms effectively and that the firmware handles link loss gracefully — buffering data where appropriate, reconnecting automatically, and alerting the user when the link is unavailable.

**Possible follow-ups:** How would you define "acceptable" wireless performance for a monitoring device — what packet error rate or data dropout duration would you consider tolerable? How would you test coexistence in a way that reflects real hospital conditions rather than an idealized lab setup?