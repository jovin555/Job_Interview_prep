# debugging-failure-analysis — Day 74

## Q1: How would you approach debugging a device that passes all functional tests on the bench but fails only when powered from its internal battery, at the same nominal voltage as the bench supply?

**Answer:** The key insight is that "same nominal voltage" is not the same as "same source." A bench supply is a low-impedance, well-regulated source with effectively unlimited current headroom and a clean return path to earth ground. A battery is a finite source with its own internal resistance, a protection circuit (often a MOSFET plus a current-sense resistor), and no earth reference. So the first move is to stop treating the two as interchangeable and start characterizing the differences.

I'd begin by measuring the actual voltage at the load — not at the battery terminals — under the same operating conditions that trigger the failure. A battery's internal resistance plus the protection FET's Rds(on) plus trace resistance can produce a meaningful droop under transient load that a bench supply simply absorbs. If the failure correlates with a load transient (radio transmit, motor start, flash write), that droop is the prime suspect. I'd capture the rail with a scope on a short ground lead right at the IC's power pin, triggering on the failure event, and compare the transient response between battery and bench supply.

Second, I'd look at the return path and grounding. With a bench supply, the earth ground often provides an unintended low-impedance return that masks a marginal ground plane or a star-ground mistake. On battery, that path disappears. I'd check for ground bounce between the digital and analog domains, and between the battery connector and the main ground plane.

Third, I'd examine the battery's protection and fuel-gauge circuitry. Some protection ICs have non-trivial series resistance or introduce a small delay before they respond to inrush. If the device has a fuel gauge that communicates over I2C or SMBus, its activity can also inject noise onto the rail.

Finally, I'd consider whether the failure is actually a brownout-reset or a firmware-visible fault. If the MCU's brownout detector is tripping, that points squarely at transient droop. If the failure is a communication error or a sensor misread, it may be noise coupling rather than voltage level. The systematic approach is: reproduce on battery, capture the rail and the return, compare against the bench case, and let the delta tell you which of these mechanisms is at play.

**Possible follow-ups:**
- How would you distinguish between a brownout reset and a watchdog reset if the MCU's reset flags are ambiguous?
- If the battery's protection FET is the culprit, what design changes would you consider, and how would you validate them?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and loop-response problem, and the first thing I'd do is separate the two possible mechanisms: is the ripple the regulator failing to respond fast enough to the transient, or is it noise coupling from the switching subsystem into the rail through a path other than the regulator?

To separate them, I'd measure the rail at multiple points: right at the regulator output, at the input of the load, and at the decoupling capacitors near sensitive ICs. If the ripple is largest at the regulator output and decreases as you move toward the load, the regulator's transient response is the issue. If the ripple is small at the regulator but large at a distant IC, the coupling is happening through the board — ground bounce, shared impedance, or radiated coupling from the switching node.

For the regulator-response case, I'd look at the loop compensation, the output capacitor ESR and value, and the load-step magnitude and slew rate. A regulator with insufficient phase margin will ring or overshoot on a fast load step. I'd capture the load current with a current probe simultaneously with the rail voltage, so I can see the phase relationship between the transient and the response. If the rail dips and then rings, that's a loop-response problem. If the rail dips and recovers cleanly but the dip is too deep, that's a bulk-capacitance or ESR problem.

For the coupling case, I'd use a near-field probe to locate the switching node and the high-di/dt loop, then check whether the sensitive IC's ground reference is moving with respect to the regulator's ground. A common culprit is a shared ground return between the switching subsystem and the analog domain. The fix is usually layout — separate returns, a tighter switching loop, or a local filter — rather than a component change.

I'd also verify the measurement itself before chasing a fix. A scope probe with a long ground lead will pick up switching noise that isn't actually on the rail. I'd re-measure with a proper tip-and-barrel or a short spring ground to confirm the ripple is real.

**Possible follow-ups:**
- How would you determine whether the output capacitor's ESR or its capacitance value is the limiting factor?
- If the ripple is coupling through the ground plane, how would you confirm that without cutting traces?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** This is one of the harder classes of failure because there's no fault flag to anchor on, and the error is only visible in aggregate. The first thing I'd do is resist the temptation to assume it's a firmware bug or a hardware bug — the whole point is that the system's own checks passed, so the error is happening in a regime the checks don't cover.

I'd start by characterizing the error statistically. Is it a fixed offset, a gain error, a single-bit flip, a stale value, or a value from a different channel? Each of those points to a different mechanism. A single-bit flip suggests a memory or bus integrity issue. A stale value suggests a timing or handshake problem. A plausible-but-wrong value that's within range but offset suggests a calibration, reference, or multiplexer issue.

Next, I'd look at the data path end to end: sensor → analog front-end → ADC → firmware read → processing → storage/transmission. At each stage, I'd ask what could produce a plausible-but-wrong value without tripping a check. For example, if the ADC has a multiplexer and the firmware switches channels, a settling-time violation could produce a value that's a blend of two channels — plausible, in range, but wrong. If the sensor is ratiometric and the reference drifts, the reading shifts proportionally. If the firmware reads the ADC before the conversion-complete flag is set, it could latch the previous conversion — again plausible but wrong.

I'd also look at the timing of the errors. Do they correlate with other system activity — radio transmit, motor switching, flash writes, temperature changes? If they cluster around a specific event, that's a strong hint about the coupling mechanism. If they're uniformly distributed, it's more likely a marginal timing or a rare race.

To reproduce, I'd build a test that logs the raw ADC value alongside the processed value and a timestamp, and run it long enough to catch the event. Once caught, I'd compare the raw and processed values to localize where the corruption enters. If the raw value is already wrong, the problem is upstream of the firmware. If the raw value is correct but the processed value is wrong, the problem is in the firmware's handling.

Finally, I'd consider whether the system's self-test is actually capable of catching this class of error. If the self-test only checks range and plausibility, a plausible-but-wrong value will always pass. That's a gap worth closing regardless of the root cause.

**Possible follow-ups:**
- How would you design a self-test that could catch a plausible-but-wrong value without generating false positives?
- If the error correlates with a specific operating mode, how would you isolate whether it's a timing issue or a coupling issue?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** The first thing I'd do is reframe the situation. A split team with two plausible hypotheses is not a problem to be resolved by argument — it's a problem to be resolved by evidence. My job as the lead is to design the experiment that discriminates between the two, not to pick a side.

I'd start by writing down both hypotheses explicitly, along with the predictions each one makes. If hypothesis A is true, what should we see that we don't see if hypothesis B is true? If the two hypotheses make the same predictions, they're not actually different hypotheses — they're the same mechanism described two ways, and the team is arguing about vocabulary. If they make different predictions, those predictions are the test.

Next, I'd look at what evidence each hypothesis currently has and where the gaps are. Often, a split happens because one hypothesis has strong circumstantial evidence and the other has strong mechanistic reasoning, but neither has been tested directly. I'd identify the cheapest, fastest experiment that would produce a clear yes/no for at least one of them. Sometimes that's a bench test; sometimes it's a teardown of a returned unit; sometimes it's a targeted log or instrumentation change.

I'd also be explicit about the cost of being wrong. If one hypothesis, if true, would require a design change and the other would require a firmware change, the cost asymmetry matters. But I'd resist letting cost drive the conclusion — the point is to find the real cause, and a wrong fix is more expensive than a delayed one.

If the team is genuinely split and the evidence is genuinely ambiguous, I'd consider whether both mechanisms could be contributing. In complex systems, it's common for two marginal conditions to combine — each one alone wouldn't cause the failure, but together they do. In that case, the investigation needs to test the combination, not just each one in isolation.

Throughout, I'd keep the team focused on the shared goal: a defensible root cause with a corrective action that's traceable to evidence. I'd set a checkpoint — a specific date or a specific experiment — at which we review the evidence and decide whether to continue or to broaden the investigation. That prevents the split from becoming a stalemate.

**Possible follow-ups:**
- How would you handle a situation where the discriminating experiment is expensive or time-consuming, and the schedule is tight?
- If the evidence ultimately supports one hypothesis but not conclusively, how would you decide whether to implement a fix or continue investigating?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The first thing I'd do is acknowledge the frustration without dismissing it. Intermittent system-level failures are genuinely hard, and the fact that components pass in isolation is not a sign of incompetence — it's a sign that the failure is in the interaction, not the parts. That reframe alone often helps.

Then I'd sit down with them and walk through what they've done, not to audit it but to understand their mental model. The goal is to find the assumption that's driving their approach. Often, a junior engineer gets stuck because they're testing the wrong thing — they've assumed the failure is in a particular component or a particular signal, and every test they run is designed to confirm or deny that assumption. If the assumption is wrong, the tests will keep passing and the failure will keep happening.

I'd help them step back and ask: what does the failure actually look like at the system level? When it happens, what's the observable symptom? What's the smallest, most reliable reproduction they've achieved? If they haven't achieved a reliable reproduction, that's the first problem to solve — an intermittent failure that can't be reproduced can't be debugged systematically. I'd help them design a test that increases the failure rate, even if it's not the real-world condition. Thermal stress, voltage margining, timing stress, or running the system in a loop for hours are all legitimate ways to make an intermittent failure more frequent.

Next, I'd introduce the idea of instrumentation over isolation. Instead of pulling components out and testing them on the bench, I'd suggest instrumenting the system in place — adding logging, scoping the suspect signals during the failure, or using a debugger to catch the state at the moment of failure. The goal is to observe the failure in its natural habitat, not to recreate it in a simplified one.

I'd also help them structure the investigation. A common trap is to change multiple things at once and lose track of what mattered. I'd encourage one change at a time, with a clear prediction for each. And I'd encourage them to write down what they've ruled out, not just what they've tried — a ruled-out list is progress even when the failure persists.

Finally, I'd set a checkpoint. If they haven't made progress by a certain point, we'd escalate — bring in another engineer, broaden the instrumentation, or reconsider the problem statement. The goal is to keep them moving and to make sure the schedule pressure doesn't push them into a premature fix.

**Possible follow-ups:**
- How would you handle it if the junior engineer is reluctant to ask for help because they feel it reflects poorly on them?
- If the failure turns out to be a design issue rather than a bug, how would you help them communicate that to the team?