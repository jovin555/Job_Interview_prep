# risk-requirements-traceability — Day 11

## Q1: How would you approach determining the appropriate level of detail for documenting risk control measures in the risk management file versus the system requirements specification, particularly for controls that are implemented as a combination of hardware and firmware?

**Answer:** The key principle is that the risk management file and the SRS serve different purposes, and the level of detail should reflect those purposes. The risk management file documents *what* risk control is needed and *why* — the hazard, the sequence of events, the risk estimation, and the rationale for selecting the control. The SRS documents *what the system must do* to implement that control, at a level that allows design and verification activities to proceed independently.

For a combined hardware/firmware control, I would structure it as follows: the risk management file describes the control at the system level — for example, "the system shall prevent motor operation when an over-temperature condition is detected." The SRS then decomposes this into verifiable requirements: a hardware requirement for the temperature sensing circuit (e.g., "the sensing circuit shall assert a fault signal when temperature exceeds X°C ± tolerance"), and a firmware requirement for the response (e.g., "the firmware shall disable motor drive within Y ms of receiving the fault signal").

The critical distinction is that the risk management file should not contain implementation-specific details like specific voltage thresholds or timing values — those belong in the SRS where they can be traced to design elements and test cases. However, the risk management file should reference the SRS requirement numbers so the traceability chain is maintained. This avoids the problem of the risk file becoming a second, parallel requirements document that can drift out of sync with the actual design.

**Possible follow-ups:**
- How would you handle a situation where the hardware and firmware requirements for a combined control are developed by different teams with different documentation conventions?
- What level of detail in the risk management file would you consider "too much" — at what point does it become implementation detail rather than risk information?

---

## Q2: How would you approach verifying a risk control measure that is implemented as a hardware-based analog comparator with a hysteresis band, where the verification test must demonstrate both the trip point and the reset point, and the acceptable tolerance band is specified in the requirements?

**Answer:** This type of control requires careful thought about what "verification" means versus what "validation" means. The requirement likely specifies a nominal trip threshold with a tolerance band — for example, "the comparator shall assert a fault when the monitored voltage falls below 3.0V ± 5%, and shall de-assert when the voltage rises above 3.3V ± 5% (hysteresis)."

My approach would be to design a verification test that sweeps the input voltage across the full operating range, both increasing and decreasing, while monitoring the comparator output. The test should capture the actual trip and reset voltages and verify they fall within the specified tolerance bands. This is a parametric test, not just a go/no-go test.

However, there are several subtleties to address. First, the test must account for the actual load conditions — the comparator's behavior can shift with temperature, supply voltage, and the impedance of the source driving the monitored rail. Ideally, the verification test would exercise the comparator across the specified environmental range (temperature, supply variation) to confirm the tolerance band holds under worst-case conditions.

Second, I would consider whether the test should verify the comparator in isolation (bench-level test with a controllable voltage source) or in-situ (with the actual circuit that generates the monitored voltage). In-situ testing is more representative but harder to control — you may need to inject a fault condition to force the monitored rail to drop. A common approach is to do both: a bench-level characterization to verify the comparator's electrical behavior, and a system-level fault injection test to verify the end-to-end response.

Third, the test method must be documented with sufficient detail that it's reproducible — including the test setup, measurement points, equipment accuracy, and pass/fail criteria. This is particularly important for regulatory audits where the test method itself will be scrutinized.

**Possible follow-ups:**
- How would you handle a situation where the bench-level test passes but the in-situ test fails due to interaction with the rest of the circuit?
- How would you determine whether the tolerance band in the requirement is realistic given component tolerances and temperature drift?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has multiple operating modes (e.g., normal mode, standby mode, fault mode, maintenance mode), and a single risk control measure behaves differently in each mode?

**Answer:** This is a common challenge in medical devices where the system's behavior — and therefore the effectiveness of risk controls — depends on the operating state. The traceability scheme needs to capture not just *that* a control exists, but *under what conditions* it is active and what behavior is expected.

My approach would be to model the system's operating modes explicitly in the requirements structure. Rather than having a single requirement that says "the system shall shut down the motor on over-temperature," I would decompose this by mode: "in normal operating mode, the system shall shut down the motor within X ms of an over-temperature condition" and "in standby mode, the system shall maintain the motor in a disabled state and shall not respond to start commands when an over-temperature condition exists."

The traceability matrix would then capture the mode-specific requirements as separate entries, each linked to the same risk control measure in the risk management file. This allows verification activities to be designed per-mode, which is important because the test approach may differ — for example, testing the over-temperature response in normal mode requires the motor to be running, while testing it in standby mode requires verifying that the motor cannot be started.

I would also consider using a state machine diagram as part of the architecture documentation to make the mode transitions explicit. This helps identify edge cases — for example, what happens if an over-temperature condition occurs during a mode transition? The traceability scheme should capture whether the risk control is active during transitions, and if so, how it behaves.

One practical technique is to add a "mode" column to the traceability matrix, so each row captures the requirement, the risk control, the operating mode, and the verification activity. This makes it easy to spot gaps — for example, a risk control that is specified for normal mode but has no verification activity for fault mode.

**Possible follow-ups:**
- How would you handle a situation where a risk control behaves differently in a mode that is only entered under fault conditions, and that mode is difficult to test?
- How would you ensure that the mode-specific requirements remain consistent with the state machine diagram as the design evolves?

---

## Q4: During a design verification campaign, you discover that a risk control requirement was verified using a test that exercises the control in isolation (e.g., applying a test signal directly to the comparator input), but the risk analysis specifies that the control must be verified in the context of the full system, including the sensor that generates the signal. How would you address this discrepancy?

**Answer:** This is a classic verification adequacy question — the test may prove that the comparator works, but it doesn't prove that the end-to-end chain (sensor → signal conditioning → comparator → firmware response → actuator) works under realistic conditions. The risk analysis likely identified the hazard as arising from the *system* failing to respond to a real-world condition, not just the comparator failing.

My first step would be to assess the gap. I would review the risk analysis to understand exactly what failure scenario the risk control is meant to mitigate. If the hazard scenario involves a sensor that can fail in ways that produce incorrect signals (e.g., a sensor that drifts, shorts, or opens), then testing the comparator in isolation with a clean test signal does not demonstrate that the system will respond correctly when the sensor misbehaves.

I would then determine whether the isolated test is a legitimate *component-level* verification that can be supplemented by a *system-level* test, or whether it's an inadequate substitute. In many cases, both are needed: the component-level test verifies the comparator meets its electrical specifications, while the system-level test verifies the end-to-end response. The question is whether the system-level test exists in the verification plan.

If the system-level test is missing, I would raise this as a gap and work with the test team to add it. The test would need to inject a realistic fault condition at the sensor level — for example, using a sensor simulator or by physically disturbing the sensor input — and verify that the full chain responds correctly. This might require additional test fixtures or test software, so I would also assess the schedule and resource impact.

Finally, I would document the discrepancy and the resolution in the verification traceability matrix, noting that the component-level test verifies the comparator's electrical behavior and the system-level test verifies the end-to-end response. This maintains the audit trail and demonstrates that the gap was identified and closed.

**Possible follow-ups:**
- How would you determine whether a component-level test plus a system-level test is sufficient, or whether an intermediate (subsystem-level) test is also needed?
- How would you handle a situation where the system-level test is technically difficult or expensive to implement, and the team proposes to rely on analysis instead of testing?

---

## Q5: (Behavioral) Imagine you're leading a project where the firmware team has implemented a risk control measure as a software-based plausibility check on a sensor reading (e.g., rejecting readings that change by more than X% between consecutive samples). The firmware lead argues that the check is "self-evidently correct" from code review and doesn't need a formal verification test, because the logic is simple and the code review provides sufficient confidence. The quality manager insists that every risk control measure must have a documented verification activity with objective evidence. How would you resolve this disagreement?

**Answer:** I would start by acknowledging the firmware lead's point — code review is valuable and does catch many defects. However, I would reframe the discussion around what verification is meant to demonstrate. The question isn't just "is the code correct?" but "does the implemented behavior actually mitigate the hazard under the conditions identified in the risk analysis?"

For a plausibility check, the risk analysis likely identified specific failure scenarios — for example, a sensor that fails shorted, producing a constant reading, or a sensor that fails with a slowly drifting output. The plausibility check is designed to detect these specific failure modes. A code review can confirm that the logic implements the intended algorithm, but it cannot demonstrate that the algorithm actually detects the failure modes under realistic conditions — for example, with real sensor noise, timing variations, or edge cases in the data.

I would propose a middle ground: the verification test doesn't need to be elaborate or expensive. A simple test that injects synthetic sensor data — including the specific failure patterns identified in the risk analysis — and verifies that the plausibility check rejects them would provide objective evidence. This could be done as part of the firmware's automated test suite, so it doesn't add significant overhead.

I would also ask the firmware lead to help design the test, since they understand the implementation best. This turns the disagreement into a collaborative problem-solving exercise rather than a compliance battle. The key is to find a verification approach that provides meaningful evidence without being burdensome — and to document the rationale for the chosen approach in the verification plan.

If the firmware lead still resists, I would escalate to the principle that risk control measures are subject to regulatory scrutiny, and the verification evidence must be defensible in an audit. A code review is not typically considered sufficient objective evidence for a risk control measure, because it doesn't demonstrate behavior under the fault conditions specified in the risk analysis.

**Possible follow-ups:**
- How would you handle a situation where the firmware team argues that the plausibility check is "too simple to fail" and that any test would be testing the test, not the code?
- How would you balance the need for verification evidence against the project schedule, when adding tests for every risk control measure could delay the firmware release?