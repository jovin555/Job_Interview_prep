# medical-devices — Day 32

## Q1: How would you approach designing a test strategy for verifying that a medical device's firmware correctly handles a sensor that intermittently provides valid but erroneous readings — for example, a pressure sensor that occasionally reports a spike that is within the valid range but physiologically impossible?

**Answer:** I'd approach this as a multi-layered verification problem. First, I'd want to understand the failure modes we're guarding against — is the concern a transient electrical artifact, a sensor degradation issue, or a communication glitch? That understanding drives what we inject and how we verify the response.

The test strategy would combine several layers. At the unit level, I'd use fault injection to feed the firmware's input buffer with crafted sensor data — spikes, step changes, stuck values, and noise bursts — all within the valid ADC range but physiologically implausible. The key is to verify that the firmware's plausibility checks (rate-of-change limits, cross-channel correlation, expected value windows) correctly flag or reject these readings without crashing or hanging.

At the integration level, I'd use a sensor simulator or a signal generator feeding the actual analog front-end, so we exercise the full path from ADC through filtering to the application layer. This catches issues where the firmware's validation logic might be bypassed by how the driver layer processes data.

For the system-level test, I'd run extended soak tests with injected anomalies at random intervals while the device is in continuous monitoring mode. The acceptance criteria would be: no false alarms triggered by the injected spikes, no missed real alarms during the test window, and the device continues logging valid data without interruption.

I'd also want to verify the device's behavior when a reading is rejected — does it retry, hold the last valid value, or mark the data as suspect? That behavior needs to be defined in the requirements and tested explicitly. Finally, I'd document the traceability from each test case back to the specific requirement or risk control measure it verifies.

**Possible follow-ups:** How would you determine the thresholds for what constitutes a "physiologically impossible" reading? What would you do if the plausibility checks themselves introduce latency that delays real alarm detection?

---

## Q2: How would you approach developing a design verification test plan for a medical device that must measure both temperature and pressure, where the two sensors share a common ADC and multiplexer, and the device must maintain specified accuracy for both parameters simultaneously?

**Answer:** The shared ADC and multiplexer introduces a coupling risk — the settling time, sampling order, and crosstalk between channels can affect accuracy, so the test plan needs to specifically probe those interactions.

I'd start by reviewing the design to understand the sampling architecture: what's the ADC resolution, what's the multiplexer switching speed, and what settling time is allocated between channel switches? This informs what failure modes we need to test for.

The test plan would include several categories. First, individual channel accuracy — each sensor tested independently against a reference standard across the full operating range, to establish baseline accuracy. Second, simultaneous accuracy — both sensors active and being sampled alternately, with both inputs varying, to verify that neither channel's reading is degraded by the other. Third, crosstalk testing — holding one sensor at a fixed value while sweeping the other across its full range, then checking that the fixed channel doesn't drift. This is particularly important if one sensor has a higher impedance or longer settling time.

I'd also include tests for multiplexer switching artifacts — for example, rapidly changing one input while sampling the other, to catch charge injection or insufficient settling. And I'd test with worst-case source impedances, since the sensor's output impedance interacts with the multiplexer's input capacitance.

For the test setup, I'd use calibrated reference sources — a precision temperature bath or dry-block calibrator for the temperature sensor, and a pressure calibrator for the pressure sensor. Both need to be more accurate than the device's specified accuracy by a sufficient margin, typically 4:1 or better.

Finally, I'd include a test where both sensors are at their extremes simultaneously — for example, high temperature with low pressure — to verify accuracy across the full operating envelope, not just at nominal conditions.

**Possible follow-ups:** How would you determine the settling time requirements for the multiplexer? What would you do if crosstalk between channels exceeded the accuracy budget?

---

## Q3: During a design review for a medical device that uses a wireless link to transmit physiological data to a display unit, the firmware engineer proposes using an unacknowledged broadcast protocol to simplify the design, while the clinical team requires that data loss be detectable and that the display unit indicate when data is stale. How would you approach this trade-off?

**Answer:** This is a classic trade-off between design simplicity and clinical safety requirements, and I'd approach it by first clarifying what the clinical team actually needs versus what the firmware engineer is trying to avoid.

The clinical requirement is that data loss be detectable and staleness be indicated — that doesn't necessarily require an acknowledged protocol with retransmission. The key question is: what's the consequence of a lost packet? If the physiological parameter changes slowly and the display updates frequently, a lost packet might be acceptable as long as the display can indicate that data hasn't refreshed within a certain time window.

I'd explore whether the unacknowledged broadcast approach can meet the clinical requirement by adding a sequence number to each packet and a timestamp. The display unit can then detect gaps in the sequence and indicate staleness if no valid packet arrives within a defined timeout. This gives the clinical team their detectability and staleness indication without the complexity of acknowledgments and retransmissions.

However, I'd also want to understand the failure modes. If the wireless link is congested or interfered with, an unacknowledged protocol will drop packets silently — the display will show staleness, but the data is still lost. For a monitoring device, that might be acceptable if the clinical team can respond to the staleness indication. But if the data is used for alarm generation, we need to consider whether the alarm can be generated on the sensor side as well, so that critical events aren't lost in transmission.

I'd also consider the regulatory angle — under IEC 60601-1-2, we need to demonstrate that wireless communication is robust in the intended electromagnetic environment. An unacknowledged protocol might be more susceptible to interference, but with appropriate channel selection, error detection, and staleness indication, it can still meet the requirements.

My recommendation would be to document the decision in the risk management file, identifying the hazard (undetected data loss) and the risk controls (sequence numbers, staleness indication, possibly redundant transmission for critical data). If the clinical team accepts the residual risk with these controls, the simpler protocol may be justified.

**Possible follow-ups:** How would you verify that the staleness indication works correctly under real-world wireless interference conditions? What if the clinical team insists on guaranteed delivery for alarm-critical data?

---

## Q4: How would you approach verifying that a medical device's firmware meets IEC 62304 requirements for a Class C software safety classification?

**Answer:** For Class C software — where a software failure could result in death or serious injury — the verification approach needs to be comprehensive and rigorously documented. I'd structure the verification across multiple levels, with traceability throughout.

First, I'd confirm the classification is correct by reviewing the hazard analysis. Class C applies when software contributes to a hazardous situation that could cause death or serious injury. If the device monitors physiology and generates alarms, but doesn't directly control therapy, it might be Class B — but if a software failure could prevent an alarm that's needed to avoid serious injury, Class C could be justified. Getting this right matters because it drives the entire verification effort.

At the requirements level, I'd verify that every software requirement is traceable to a system requirement or risk control measure, and that each requirement is testable — unambiguous, verifiable, and with clear acceptance criteria. For Class C, the standard requires that software requirements be traced to system requirements and that the software architecture be documented with a clear decomposition.

For the architecture, I'd verify that safety-critical functions are isolated from non-critical functions — for example, that a failure in the UI or data logging can't prevent the monitoring and alarm functions from executing. This might be verified through code review, static analysis, and targeted fault injection testing.

At the unit level, I'd expect 100% statement and branch coverage for safety-critical modules, with unit tests that verify both normal behavior and error handling. For Class C, the standard requires that each software unit be verified — typically through code reviews and unit testing — and that the verification results be documented.

At the integration level, I'd verify that modules interact correctly, particularly at interfaces between safety-critical and non-critical code. This includes testing error propagation — for example, what happens when a non-critical task fails or returns an error to a safety-critical module.

At the system level, I'd run verification tests that exercise the full device, including fault injection to demonstrate that safety functions continue to operate under abnormal conditions. This includes testing with sensor failures, communication failures, and power anomalies.

Throughout, I'd maintain a traceability matrix linking each requirement to its verification activity and results. The software verification report would summarize the activities performed, the results, and any residual risks or known issues. For Class C, the documentation burden is significant, but it's proportionate to the risk — the goal is to demonstrate with evidence that the software behaves correctly in all foreseeable conditions.

**Possible follow-ups:** How would you determine whether a specific software module should be classified as Class A, B, or C under IEC 62304? What level of test coverage would you consider sufficient for a Class C module?

---

## Q5: You're leading a project where a field complaint reports that a medical device's patient-contacting silicone sensor pad is causing skin irritation in several patients. How would you approach the investigation and corrective action process?

**Answer:** This is a serious complaint that could indicate a biocompatibility issue, a manufacturing problem, or a use-related issue — and it requires a structured investigation following the regulatory requirements for complaint handling and field safety corrective actions.

I'd start by assembling a cross-functional team including quality, clinical affairs, manufacturing, and design engineering. The first step is to gather all available information: the complaint details, the number of affected patients, the severity of the irritation, the device lot numbers, and the clinical circumstances. I'd want to know if the irritation is limited to a specific lot, a specific manufacturing date range, or a specific patient population.

In parallel, I'd initiate a risk assessment to determine the severity and likelihood of the hazard. Skin irritation from a patient-contacting material could range from minor redness to more serious reactions, and the risk assessment would determine whether this requires immediate field action or can be addressed through a corrective action plan.

The technical investigation would examine several possibilities. First, I'd review the material specifications and the supplier's certificates of conformance — is the silicone the same material that was validated during design? Second, I'd check the manufacturing process — was there any change in processing parameters, curing time, or cleaning agents that could affect the material's biocompatibility? Third, I'd review the biocompatibility testing that was done during development — was ISO 10993 testing performed on the final material and process, or on a representative sample?

I'd also consider whether the irritation could be use-related — for example, if the pad is left in contact with skin for longer than intended, or if a cleaning agent used by the facility reacts with the material. The clinical team would be essential in understanding the actual use conditions.

If the investigation suggests a material or process issue, I'd quarantine the affected inventory and notify the supplier. If the risk assessment indicates a potential serious hazard, I'd initiate a field safety corrective action, which might include a recall, a field notification, or a design change — depending on the severity and scope.

Throughout, I'd document everything in the complaint handling system and the corrective action file, following the CAPA process. The key is to balance speed — because patient safety is at stake — with thoroughness, because we need to identify the root cause correctly to prevent recurrence. I'd also consider whether similar complaints have been reported previously, which would indicate a trend that needs broader investigation.

**Possible follow-ups:** How would you determine whether this complaint requires a field safety corrective action (FSCA) versus a routine corrective action? What if the investigation finds that the silicone material meets all specifications and passed ISO 10993 testing, but the irritation still occurs?