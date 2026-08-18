# medical-devices — Day 28

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a sensor that intermittently provides valid but erroneous readings — for example, a pressure sensor that occasionally reports a spike that is within the valid range but physiologically impossible?

**Answer:** I'd start by distinguishing between two failure modes: sensor faults that are detectable at the hardware level (open/short, out-of-range) and faults that produce plausible but incorrect values. The latter is the harder case because the firmware can't simply check against a hard limit. My approach would be multi-layered:

First, I'd characterize the expected physiological signal envelope — for a pressure sensor in respiratory monitoring, that means defining maximum rates of change, plausible ranges, and expected waveform morphology. These become the basis for plausibility checks in firmware, but I'd be careful about over-filtering, since legitimate transient events (coughing, movement artifacts) can produce rapid changes that shouldn't be discarded.

Second, I'd design the test strategy around fault injection at multiple levels: hardware-level injection (switching in a faulty sensor or simulating a spike at the analog front-end), firmware-level injection (forcing the sensor driver to return specific values), and system-level testing with recorded physiological waveforms that have known artifacts superimposed.

Third, I'd verify not just that the firmware detects the erroneous reading, but that it responds correctly — for example, by flagging the data as suspect, continuing to monitor other parameters, and avoiding false alarms while still alerting the user that data quality is degraded. The test plan would include scenarios where the erroneous reading persists, where it's intermittent, and where it occurs simultaneously with a genuine critical event, to ensure the plausibility checks don't mask real alarms.

**Possible follow-ups:** How would you determine the threshold between a legitimate physiological transient and an erroneous reading without causing false positives? How would you verify that the plausibility checks themselves don't introduce a safety risk by delaying detection of a genuine event?

---

## Q2: During a design review for a medical device that uses a rechargeable battery, the firmware engineer proposes implementing a battery fuel gauge using voltage-based estimation, while the hardware engineer recommends adding a dedicated coulomb-counting fuel gauge IC. How would you approach this trade-off?

**Answer:** This is a classic trade-off between simplicity and accuracy, but in a medical device the decision needs to be driven by the clinical requirements. I'd start by asking what the fuel gauge is actually used for — is it just a "low battery" warning, or does the device need to provide a meaningful estimate of remaining operating time to clinicians? If the device monitors a patient continuously, the consequences of an inaccurate estimate are different than for a device that's used intermittently.

Voltage-based estimation is attractive because it's essentially free — it uses the ADC already present and requires no additional hardware. But the accuracy depends heavily on the battery chemistry and load profile. For a lithium-ion cell with a relatively flat discharge curve, voltage-based estimation becomes unreliable in the last 20-30% of capacity, which is exactly the region where the user needs accurate information. Temperature, load current, and battery age all further degrade the estimate.

A coulomb-counting IC provides much better accuracy because it integrates current over time, but it requires calibration, adds cost and board space, and still needs periodic voltage-based correction to account for self-discharge and coulombic efficiency variations.

My approach would be to quantify the requirement first: what accuracy does the clinical use case demand? If the device just needs to warn the user "charge soon," voltage-based estimation with a conservative threshold might be acceptable. If the device needs to display remaining operating time, or if the clinical workflow depends on knowing how much monitoring time remains, I'd lean toward the dedicated IC. I'd also consider a hybrid approach — using voltage-based estimation for the simple warning and adding a coulomb-counting IC only if the requirements demand it. The decision should be documented in the design inputs with the accuracy requirement traced to the clinical use case.

**Possible follow-ups:** How would you verify the accuracy of the fuel gauge across the battery's service life, given that battery capacity degrades with cycling? What single-fault conditions would you consider for the fuel gauge circuit itself?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The key challenge here is that the two sensors share a signal chain, so errors in one channel can affect the other — through multiplexer leakage, settling time issues, or common-mode noise. The test plan needs to verify not just that each channel meets its accuracy specification in isolation, but that they do so when operating together.

I'd structure the plan in three phases. First, characterization of the signal chain: measure the ADC's gain error, offset error, and noise for each channel independently, using precision sources. This establishes the baseline performance of the shared components. Second, cross-channel interaction testing: verify that switching between channels doesn't introduce crosstalk or settling errors — for example, by applying a full-scale signal to one channel and a small signal to the other, then checking that the small signal isn't corrupted. This is particularly important if the temperature sensor has a slow response and the pressure sensor has fast transients, since the multiplexer switching rate and settling time become critical.

Third, end-to-end accuracy testing with the actual sensors connected, using calibrated references for both temperature and pressure simultaneously. The test should include scenarios where both signals are changing at their maximum expected rates, to stress the multiplexer's ability to track both channels adequately.

I'd also include a fault injection element: what happens if one sensor fails or produces an out-of-range signal? Does it corrupt the other channel? The test plan should verify that the firmware can detect and isolate a faulty channel without degrading the other.

**Possible follow-ups:** How would you determine the required multiplexer switching rate and settling time to meet both accuracy specifications? What would you do if the cross-channel interaction testing revealed unacceptable crosstalk?

---

## Q4: You're leading a project where a field complaint reports that a medical device's rechargeable battery is swelling after 6-12 months of use in a hospital setting. The device is used for continuous patient monitoring and the battery is not user-replaceable. How would you approach the investigation and corrective action process?

**Answer:** Battery swelling is a serious safety concern — it can indicate internal short circuits, overcharging, or thermal runaway risk, and in a patient-monitoring device it could compromise the enclosure or cause burns. I'd treat this as a potential serious incident and escalate it appropriately within the organization's CAPA process.

My investigation would follow a structured root-cause approach. First, I'd gather data: how many complaints, what's the commonality (specific lot codes, manufacturing date, firmware version, charging patterns), and what's the severity — is it cosmetic swelling or is the device malfunctioning? I'd request the affected devices be returned for analysis, including battery disassembly and inspection by the battery manufacturer if needed.

Parallel to the physical investigation, I'd review the design: the charging algorithm (constant current/constant voltage parameters, termination current, temperature monitoring), the protection circuitry (overvoltage, overcurrent, over-temperature), and the mechanical design (battery compartment clearance, thermal management). I'd also review the battery specification and qualification testing — was the battery cycled under the actual use conditions (frequent partial discharges, continuous trickle charging, elevated temperature)?

A common root cause in hospital settings is that devices are left on continuous charge for extended periods, which can stress the battery if the charging algorithm isn't designed for float charging or if the termination current is set too high. Another possibility is that the battery's internal protection circuit is failing, or that the cell chemistry is not suited for the application.

Once the root cause is identified, the corrective action could range from a firmware update to adjust charging parameters, to a hardware change (different battery, improved protection circuit, better thermal management), to a field action if the risk warrants it. Throughout the process, I'd document everything in the CAPA file and coordinate with regulatory affairs on any reporting obligations, since battery swelling in a medical device may be a reportable event depending on the jurisdiction.

**Possible follow-ups:** How would you assess the risk to patients while the investigation is ongoing — would you recommend any interim measures? How would you determine whether the battery swelling is a design issue versus a manufacturing defect?

---

## Q5: How would you approach verifying that a medical device's firmware meets IEC 62304 requirements for a Class C software safety classification?

**Answer:** Class C is the highest software safety classification under IEC 62304 — it applies when a software failure could contribute to a hazardous situation that could result in death or serious injury. The verification effort needs to be commensurate with that risk.

I'd start by confirming the classification is correct, since it drives the entire development and verification effort. If the software directly controls therapy delivery or makes decisions that could harm the patient, Class C is appropriate. If it only monitors and alerts, Class B might be more appropriate — but that's a decision that should be documented with justification.

For Class C, the standard requires a comprehensive set of activities. At the unit level, every software unit needs to be verified — typically through code reviews and unit testing with coverage analysis. I'd use a combination of static analysis (to catch coding errors and safety-critical violations), dynamic testing (with branch and MC/DC coverage where feasible), and formal methods where appropriate for the most safety-critical algorithms.

At the integration level, I'd verify that the software components interact correctly, particularly at interfaces where data is passed between modules. This includes testing error handling, timing behavior, and resource management. At the system level, I'd verify that the software meets its requirements in the context of the complete device, including interaction with hardware and other software components.

A key aspect of Class C verification is traceability — every software requirement must be traced to its implementation and to the tests that verify it. The verification results, including any defects found and their resolution, must be documented in the software verification report. I'd also ensure that the verification activities are independent — the standard requires that verification be performed by someone other than the original developer, which may mean involving a separate test team or independent reviewer.

Finally, I'd integrate the software verification with the overall system verification — the software's contribution to system-level hazards needs to be verified through the risk control measures, and the verification evidence should be linked to the risk management file.

**Possible follow-ups:** How would you determine the appropriate level of coverage (e.g., statement, branch, MC/DC) for different parts of the software? How would you handle verification of third-party or legacy software components that weren't developed under IEC 62304?