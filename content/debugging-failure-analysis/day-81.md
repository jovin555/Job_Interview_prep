# debugging-failure-analysis — Day 81

## Q1: How would you approach debugging a device that passes every functional test on the bench but fails only when powered from its internal battery, at the same nominal voltage as the bench supply?

**Answer:** The key insight is that "same nominal voltage" is not the same operating condition — a bench supply and a battery differ in output impedance, transient response, source impedance at high frequency, and grounding. I'd start by treating the power source itself as the variable under test rather than assuming the load is at fault.

First, I'd characterize both sources. On the bench supply I'd measure DC level, ripple, and load-transient response at the device's input. Then I'd repeat with the battery, ideally with a current probe and a scope at the device's power input pins, not at the far end of the cable. Batteries have low DC impedance but their effective impedance rises with frequency and depends on state of charge, temperature, and the protection circuitry in the pack — a battery pack with a BMS, a fuse, or a connector adds series resistance and inductance that a bench supply doesn't have.

Second, I'd look at the failure mode. If the device browns out or resets, I'd capture the rail during the event and look for a transient dip that the bench supply's bulk capacitance was masking. If it's a functional error rather than a reset, I'd suspect a threshold or reference issue — for example, an ADC reference derived from the battery rail, or a comparator whose trip point shifts with source impedance.

Third, I'd check the ground path. A bench supply often shares a low-impedance earth ground with the scope and the test equipment, which can mask ground-bounce or return-path problems. Running on battery removes that path, so any design that relied on it will behave differently.

Finally, I'd try to reproduce the failure deterministically by adding series resistance and inductance to the bench supply to emulate the battery's impedance, or by using a battery simulator. Once it reproduces on the bench, I can bisect the circuit — bypass the connector, add local bulk capacitance, isolate subsystems — one change at a time until the sensitivity is localized.

**Possible follow-ups:**
- How would you distinguish a source-impedance problem from a grounding problem if both produce similar symptoms?
- If the failure only appears at low state of charge, how would that change your investigation?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and power-distribution problem, and the first thing I'd do is separate the question of whether the regulator is failing to regulate from whether the measurement itself is misleading.

I'd start by measuring correctly. Ripple must be probed at the point of load, right across the decoupling capacitor, with a short ground lead — a long ground clip picks up loop inductance and radiated switching noise and will show ripple that isn't really there. I'd use a spring-tip ground or a coaxial pigtail, and I'd measure both at the regulator output and at the load's local decoupling to see where the disturbance originates and where it propagates.

Then I'd characterize the transient. With a current probe on the switching subsystem's supply, I'd capture the load step and the rail's response simultaneously. Key questions: how fast is the di/dt, how large is the step, and how does the rail recover? A slow recovery points to insufficient bulk capacitance or a regulator with inadequate loop bandwidth. A fast spike that the regulator never sees points to the impedance between the bulk capacitor and the load — trace inductance, connector inductance, or a missing local decoupling capacitor.

I'd also check the control loop. Some regulators become unstable or marginally stable under certain load conditions, and the "ripple" may actually be low-frequency oscillation rather than switching ripple. Looking at the frequency content tells you which it is: switching-frequency ripple points to filtering, sub-harmonic or low-frequency oscillation points to loop stability.

Finally, I'd consider whether the disturbance is conducted or radiated. If the switching subsystem has a fast edge rate, the noise may be coupling into the measurement or into adjacent traces rather than traveling through the power path. A near-field probe scan while the subsystem switches would reveal whether there's a radiated component.

The fix depends on the diagnosis: more local decoupling and lower-impedance routing for a distribution problem, a different compensation network or output capacitor for a stability problem, and layout or shielding changes for a coupling problem.

**Possible follow-ups:**
- How would you decide between adding bulk capacitance and adding high-frequency decoupling?
- What would you look for in the regulator datasheet to predict this behavior before layout?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** This is one of the harder classes of bug because there's no fault flag to anchor on — the system believes it's healthy. I'd approach it as a data-integrity investigation and work backward from the corrupted value to the point where it diverged from truth.

First, I'd establish ground truth. I'd instrument the system to log the raw sensor data at multiple points in the chain — at the sensor output, at the ADC input, at the ADC result register, and at the value the firmware stores and transmits. If I can capture a corrupted event with all four points logged, I can localize where the corruption enters. Without that, I'm guessing.

Second, I'd look at the failure signature. Is the wrong value a single-bit error, a stale value from a previous reading, a value from a different channel, or a plausible but shifted value? Each points somewhere different. A single-bit flip suggests a memory or bus integrity issue. A stale value suggests a timing or handshake problem — the firmware read the register before the conversion completed, or read a buffer that hadn't been updated. A channel mix-up suggests an addressing or multiplexer sequencing bug. A shifted value suggests a scaling or calibration error that only manifests under certain conditions.

Third, I'd consider the conditions under which it occurs. If it correlates with temperature, supply voltage, or activity in another subsystem, that narrows the search considerably. If it's purely random, I'd suspect a race condition or an uninitialized variable.

Fourth, I'd add defensive instrumentation: a checksum or sequence number on the sensor data path, and a self-consistency check that flags implausible transitions. This doesn't fix the bug, but it converts a silent failure into a detectable one, which is essential for a medical device and also gives me a reproducible trigger to debug against.

Finally, I'd consider whether the algorithm itself is the problem. If the sensor is within its datasheet accuracy but the system's fault threshold is tighter than the sensor's real-world behavior, the "wrong" value may be correct and the algorithm's expectation may be wrong. That's a requirements question, not a firmware bug, and it's worth checking early.

**Possible follow-ups:**
- How would you design the logging so it doesn't perturb the timing you're trying to observe?
- If the corruption only appears in the field and never on the bench, how would you make progress?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the temptation is to argue about which is more likely. I'd reframe the problem: instead of debating which is true, I'd ask what evidence would distinguish them, and then design the cheapest, fastest test that produces that evidence.

My approach has a few steps. First, I'd make both hypotheses explicit and falsifiable. "It's a timing problem" isn't a hypothesis — "the sensor's setup time is violated when the bus capacitance is at the high end of tolerance" is. Writing them down precisely often reveals that one is untestable as stated, or that they're not actually mutually exclusive.

Second, I'd look for the discriminating test. If hypothesis A predicts the failure rate scales with temperature and hypothesis B predicts it scales with bus length, then a test that varies one while holding the other constant will separate them. I'd prioritize tests that can be run quickly and that produce a clear yes/no rather than a subtle statistical difference.

Third, I'd consider whether both could be contributing. In complex systems, it's common for two marginal conditions to combine — neither alone causes failure, but together they do. If that's plausible, the investigation should test the combination, not just each in isolation.

Fourth, I'd manage the team dynamics deliberately. When people are split, it's usually because each side has invested in their hypothesis. I'd make it clear that the goal is not to be right but to find the answer, and that a test which eliminates a hypothesis is progress, not defeat. I'd assign the test to someone from the "other" camp where possible, so the result is credible to both sides.

Finally, if the discriminating test is expensive or slow, I'd consider a temporary mitigation that addresses both hypotheses simultaneously — for example, adding margin in both the timing and the layout — while the investigation continues. That protects the schedule without committing to a root cause prematurely, and it's honest about the fact that the root cause isn't yet confirmed.

**Possible follow-ups:**
- How would you handle it if the discriminating test is inconclusive?
- What would you do if the schedule pressure forces a decision before the investigation concludes?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, the system fails — is a strong signal that the debugging method is the problem, not the engineer's effort. Isolation testing is the right instinct, but it removes exactly the interactions that are likely causing an intermittent system-level failure. I'd treat this as a coaching moment rather than a rescue.

First, I'd sit down with them and ask them to walk me through what they've tried and what they've learned. Not to audit them, but to understand their mental model. Often the gap is that they've been testing the same hypothesis repeatedly with slightly different setups, rather than generating new hypotheses.

Second, I'd redirect the approach. Instead of testing components in isolation, I'd suggest they focus on reproducing the failure reliably first. An intermittent failure that can't be reproduced can't be debugged — every test is a coin flip. I'd ask what conditions correlate with the failure: temperature, time since power-on, activity in another subsystem, specific user actions. Even a weak correlation is a starting point.

Third, I'd introduce the idea of instrumenting the system rather than testing it. Instead of pulling components out, add logging, add a scope on the suspect signals, add a trigger that captures the state at the moment of failure. The goal is to catch the failure in the act, with enough context to see what's different.

Fourth, I'd suggest they bisect the system. If the failure requires the full system, start disabling subsystems one at a time until the failure stops. That's a systematic way to narrow the search without needing a hypothesis up front.

On the human side, I'd be explicit that being stuck for several days is normal on intermittent system-level bugs, and that the frustration is a signal to change method, not a sign of failure. I'd check in daily rather than taking over, and I'd make sure they know it's fine to ask for help earlier next time. If the schedule is genuinely at risk, I'd pair with them for a session rather than reassigning the work — that preserves their ownership and builds their skill.

**Possible follow-ups:**
- How would you tell the difference between an engineer who needs a method change and one who needs more time?
- What would you do if the failure still can't be reproduced after a week?