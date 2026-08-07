# medical-devices — Day 17

## Q1: How would you approach verifying that a medical device's firmware correctly handles a situation where the real-time clock (RTC) loses power or is reset, given that the device logs time-stamped physiological data that may be used for clinical decision-making?

**Answer:** The first step would be to define what "correct handling" means for this specific device, since the clinical implications of an incorrect timestamp depend on how the data is used. If the logged data supports treatment decisions, an incorrect timestamp could be a patient safety issue, so this would need to be addressed through the risk management process.

From a design perspective, I'd look at the hardware architecture first. Does the RTC have a backup power source, like a supercapacitor or coin cell? If so, I'd verify that the switchover between main power and backup power is seamless and that the RTC doesn't glitch or reset during the transition. I'd also check whether the RTC has a power-fail detection output that the firmware can monitor.

For the firmware, I'd want to see a clear mechanism for detecting that the RTC has lost time. This could be a validity flag in the RTC itself, or the firmware could maintain a "last known good time" in non-volatile storage and compare it against the RTC on each boot. If the RTC time is earlier than the last known good time, that's a strong indication of a reset.

The key design decision is what happens when an invalid time is detected. The device should not silently log data with an incorrect timestamp. Options include: entering a "time not set" state where the device continues monitoring but flags the data as having unknown time, or requiring the user to set the time before monitoring can resume. The choice depends on the clinical scenario — for a continuous monitoring device, stopping monitoring might be worse than logging with a flag.

I'd also verify the behavior across power cycles. For example, if the device is unplugged for 30 seconds and then reconnected, the RTC should maintain time if it has backup power. If the backup is depleted, the device should detect this and handle it appropriately.

For testing, I'd develop a matrix of scenarios: RTC battery present and charged, RTC battery depleted, RTC battery removed, main power interrupted for various durations, and combinations of these. I'd verify that the device either maintains correct time or enters the defined error state, and that no data is logged with silently incorrect timestamps.

**Possible follow-ups:** How would you test the RTC behavior when the backup power source is partially depleted but not fully dead? What if the device is in storage for six months before first use — how would you handle the initial time setting?

---

## Q2: How would you approach designing a test strategy for verifying that a medical device's enclosure provides adequate protection against electrostatic discharge (ESD) for both the operator and the patient, given that the device has a touchscreen interface and is used in a home environment?

**Answer:** This requires thinking about ESD from two perspectives: the IEC 60601-1-2 immunity requirements (does the device continue to function correctly when subjected to ESD?) and the safety perspective (does the ESD event create a hazard for the user or patient?).

For the test strategy, I'd start by identifying the applicable ESD test levels. IEC 60601-1-2 typically requires higher levels than general commercial equipment because medical devices may be used in environments with higher static levels, and the consequences of failure are more severe. For a home-use device, I'd also consider the user's environment — carpeted floors, dry climates, synthetic clothing — which can generate higher static charges.

The test plan would include both contact discharge and air discharge testing at all user-accessible points, including the touchscreen, enclosure seams, connectors, and any exposed metal parts. I'd pay particular attention to the touchscreen, since it's a direct interface point. For each test point, I'd verify both that the device continues to function correctly and that no hazardous condition is created.

For the touchscreen specifically, I'd want to verify that the display doesn't glitch or reset during a discharge, and that any protective coating or glass doesn't degrade over repeated discharges. I'd also test the device in various configurations — connected to mains, on battery, with peripherals attached — since the ESD path can change.

One aspect that's often overlooked is testing at different humidity levels. ESD severity increases in low humidity, so I'd want to test at the lower end of the device's specified operating range. I'd also consider repeated discharges at the same point, since a single discharge might not reveal a weakness that becomes apparent after multiple events.

For the safety aspect, I'd verify that the ESD event doesn't create a path to the patient-connected parts. This ties back to the isolation design — the ESD should be shunted to chassis ground or earth, not coupled into the patient circuit. I'd review the PCB layout and enclosure design to confirm that spark gaps or transient suppressors are positioned to divert the discharge away from sensitive circuits.

**Possible follow-ups:** How would you handle a situation where the device passes ESD testing in the lab but fails in a home environment with high static levels? What design changes would you consider if the touchscreen is particularly vulnerable to ESD?

---

## Q3: How would you approach developing a design verification test plan for a medical device that must measure and display a physiological parameter with a specified accuracy, when the reference measurement method requires specialized test equipment that is only available at an external laboratory?

**Answer:** This is a common challenge in medical device development, and the key is to structure the verification approach so that you can gain confidence in the device's accuracy without having continuous access to the reference equipment.

I'd start by understanding what the reference method actually measures and how it relates to the device's measurement principle. For example, if the device uses a pressure sensor to measure respiratory flow, the reference might be a calibrated flow bench or a pulmonary function testing system. The question is whether the reference measures the same physical quantity through the same pathway, or whether there's a transfer function involved.

The first step would be to establish a correlation between the device's output and the reference measurement. This would involve taking the device to the external lab and running a series of tests across the full measurement range, including edge cases and clinically relevant values. The goal is to characterize the device's accuracy relative to the reference across its operating envelope.

Once that correlation is established, I'd develop a secondary verification method that can be used in-house. This might involve calibrated test fixtures, precision signal generators, or mechanical simulators that produce known inputs. The key is that these secondary methods are traceable to the reference method through the correlation study.

For example, if the device measures pressure, I might use a precision pressure calibrator in-house that has its own NIST-traceable calibration. The correlation study at the external lab would confirm that the device's readings match the reference, and the in-house calibrator would be used for routine verification. The calibrator itself would be periodically recalibrated to maintain traceability.

I'd also think about the statistical aspects. The verification plan should include enough test points and repetitions to establish confidence in the accuracy specification, not just a single measurement at each point. I'd want to understand the device's measurement variability — both within a single unit and across units — to ensure that the accuracy specification is achievable across production.

The documentation would need to clearly show the chain of traceability: the external reference, the correlation study, the in-house verification method, and how each production unit is verified. This is important for the design history file and for regulatory review.

**Possible follow-ups:** How would you handle a situation where the correlation study reveals that the device's accuracy varies across the measurement range? What if the external lab's reference method is updated during the development program?

---

## Q4: You're leading a project where a supplier has delivered a batch of PCBs for a medical device, and incoming inspection reveals that the via fill material on a critical high-voltage isolation area is not fully cured. The supplier claims the boards will pass hi-pot testing and that the issue is cosmetic. How would you handle this situation?

**Answer:** This is a situation where I'd need to balance the immediate schedule pressure against the long-term reliability and safety implications. The first thing I'd do is clarify what "not fully cured" actually means — is it a surface tackiness, or does it affect the material's dielectric properties? These are very different situations.

I'd want to understand the specification for the via fill material and what the curing process is supposed to achieve. The purpose of the via fill in a high-voltage isolation area is to provide a controlled dielectric barrier between the primary and secondary sides of the isolation barrier. If the material isn't fully cured, its dielectric strength might be reduced, and it could also absorb moisture over time, which would further degrade its insulating properties.

The supplier's claim that the boards will pass hi-pot testing is relevant but not sufficient. Hi-pot testing is a go/no-go test at a specific voltage, and it doesn't tell you about the safety margin or the long-term behavior. A board that barely passes hi-pot today might fail after six months of exposure to humidity and thermal cycling. For a medical device, I need to understand the safety margin, not just whether it passes the test.

I'd also consider the failure mode. If the via fill is part of the isolation barrier, a failure could create a direct path between the patient-connected circuit and mains voltage. That's a critical safety hazard. Even if the risk is low, the consequence is severe enough that I'd want to understand the situation thoroughly before accepting the boards.

My approach would be to:
1. Quarantine the affected batch and prevent any of those boards from being used in production.
2. Request the supplier's data on the curing process, including time-temperature profiles and any quality records for the batch.
3. Run additional testing on sample boards — not just hi-pot, but also insulation resistance, partial discharge testing if applicable, and possibly accelerated aging to understand long-term behavior.
4. Work with the supplier to determine whether the issue is isolated to this batch or indicates a process control problem.

If the testing shows that the boards have adequate safety margin and the issue is truly cosmetic, I might accept them with a deviation, but only with documented justification and risk assessment. If there's any doubt about the isolation integrity, I'd reject the batch and work with the supplier on a corrective action plan.

**Possible follow-ups:** How would you document this decision in the risk management file? What if the supplier is the only source for these boards and rejecting the batch would delay the project by three months?

---

## Q5: How would you approach developing a post-market surveillance plan for a medical device that includes both active monitoring of field performance and a mechanism for identifying emerging safety signals that weren't anticipated during the design phase?

**Answer:** Post-market surveillance is often treated as a compliance activity, but it's really a continuous risk assessment process. The goal is to confirm that the device's real-world performance matches the assumptions made during design, and to detect new hazards that weren't identified during development.

I'd start by reviewing the risk management file to understand what hazards and failure modes were anticipated during design. This gives me a baseline for what to monitor. For each identified hazard, I'd define what data would indicate that the risk is higher than expected. For example, if the design assumed a certain battery life, I'd monitor field reports of battery failures and compare the rate against the design assumption.

But the plan also needs to capture unanticipated issues. This means looking beyond formal complaint reports. I'd want to include:
- Customer service interactions that might not rise to the level of a formal complaint
- Service and repair records, which can reveal patterns of wear or failure
- Literature reviews and competitor recalls, which might indicate a class-wide issue
- Usage data if the device can capture it, such as error logs or performance metrics

The key is to define thresholds and triggers. When does a pattern of reports become a signal that requires investigation? I'd establish a process for reviewing the data on a regular cadence — monthly or quarterly depending on the device's risk class — and for escalating when the data suggests a potential safety issue.

I'd also think about how to distinguish between normal variation and a real signal. For example, if the device has a reported failure rate of 0.1%, is a month with 0.3% a cause for concern or just statistical noise? This requires understanding the expected baseline and having a structured approach to analyzing the data.

The plan should also include a mechanism for feeding information back into the design process. If the surveillance reveals a pattern of issues, that information should inform design changes, updates to the risk management file, and potentially updates to the instructions for use.

Finally, I'd make sure the plan is documented and that the responsibilities are clear. Who reviews the data? Who makes the decision to escalate? Who communicates with regulatory authorities if a field safety corrective action is needed? Having these roles defined in advance makes the process much smoother when an issue does arise.

**Possible follow-ups:** How would you determine whether a pattern of reported issues requires a field safety corrective action versus just a design change for future production? How would you handle a situation where the surveillance data suggests a risk that was previously considered negligible is actually higher than expected?