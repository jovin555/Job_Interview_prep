# debugging-failure-analysis — Day 78

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key insight is that the failure correlates with a physical configuration change, not with a component or a firmware state — so the investigation should treat the enclosure and mounting position as the independent variable, not the electronics. I'd start by reproducing the offset with the board in the enclosure but not yet mounted, then with the enclosure closed but the unit held in free air, then in the final mounting position. That three-step sequence separates three distinct mechanisms: mechanical stress on the board or connectors, a change in the local electromagnetic or thermal environment, and a change in the grounding or return path through the mounting hardware.

If the offset appears only at the final mounting step, I'd suspect a ground loop or a change in the reference potential — for example, the chassis or mounting bracket providing an unintended return path, or a mounting screw shorting a via or a ground pour to a signal net. A quick check is to measure the analog front-end's reference and ground pins relative to the system ground with a high-impedance probe while the unit is in each configuration, and to compare the offset against the sensor's own zero point. If the offset appears when the enclosure is closed but before mounting, I'd look at cable routing, connector seating, or a shield can making contact with a component it shouldn't. If it appears only when the board is flexed by the mounting hardware, I'd look for a cracked solder joint, a stressed via, or a connector whose contact resistance changes with mechanical load — a classic case where a bench test with a test harness simply doesn't exercise the same mechanical boundary conditions.

Throughout, I'd keep the measurement setup identical across configurations — same probe, same reference point, same ambient temperature — because a small consistent offset is exactly the kind of result that can be created or hidden by changing the measurement setup between tests.

**Possible follow-ups:**
- How would you distinguish a genuine electrical offset from a measurement artifact caused by the probe's ground lead picking up a different common-mode voltage in each configuration?
- If the offset turns out to be caused by the mounting hardware, how would you decide between a design change and a manufacturing/assembly change?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a load-transient and power-distribution problem, so I'd approach it as a question of where the transient current is actually flowing and where the impedance is highest. The first step is to characterize the ripple properly rather than just observe it: measure at the regulator output, at the load's supply pins, and at the decoupling capacitors, using a probe with a very short ground lead or a proper ground spring — a long ground lead will pick up switching noise and make the problem look worse or different than it is. Comparing the ripple amplitude and shape at those three points tells me whether the regulator is failing to respond, whether the distribution network between the regulator and the load is too inductive, or whether the decoupling is inadequate at the point of load.

Next I'd look at the transient itself: what is the di/dt, what is the repetition rate, and does the ripple correlate with the switching edges of the high-current subsystem or with its control loop? If the ripple is at the subsystem's switching frequency, it's likely conducted or radiated coupling into the rail. If it's a damped oscillation following each load step, it's likely a control-loop or output-capacitor ESR/ESL issue. If it's a slow droop and recovery, it's likely bulk capacitance or regulator bandwidth.

I'd also check the return path. A high-current subsystem switching can cause ground bounce if its return current shares an impedance with the analog or digital ground reference — the ripple may not be on the rail at all, but between the rail and the point where the measurement is referenced. Probing differentially, or moving the ground reference to the load's own ground pin, often reveals whether this is a real rail disturbance or a ground-shift artifact.

Once I understand the mechanism, the fix space is usually: add or relocate decoupling at the point of load, reduce loop area in the high-current path, improve the regulator's transient response, or add a bulk capacitor with appropriate ESR. I'd verify any fix with the same measurement setup that revealed the problem, and check that it holds across load and temperature.

**Possible follow-ups:**
- How would you decide whether the fix belongs in the power distribution network or in the high-current subsystem's own switching behavior?
- What would you look for on a scope to distinguish a regulator control-loop instability from a decoupling insufficiency?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hardest part of this class of failure is that the system's own validation logic can't see it, so the investigation has to start by building observability that doesn't currently exist. I'd first try to characterize the error statistically: is the wrong value always off by a similar amount, does it occur at a particular sample rate or operating mode, does it correlate with temperature, supply voltage, or the activity of another peripheral? Even without a reproduction, a pattern in the offline data can point at a mechanism.

Then I'd instrument the signal chain at each stage — sensor output, analog front-end, ADC input, ADC output register, firmware variable, transmitted value — and compare them on the same acquisition. The goal is to find the first stage where the value diverges from the reference. If the divergence is at the ADC output, it's an analog or timing issue; if it's between the ADC register and the firmware variable, it's a read sequence, DMA, or buffer issue; if it's between the firmware variable and the transmitted value, it's a data-handling or concurrency issue.

Because the error is plausible rather than out of range, I'd pay particular attention to mechanisms that produce a small, structured error: a stale sample being read because a conversion-complete flag was checked before the conversion actually finished, a race between an ISR updating a shared buffer and the main loop reading it, a scaling or calibration constant being applied twice or not at all under a specific code path, or a bit error in a serial transfer that happens to land within the valid range. I'd also check whether the sensor itself has a mode where it returns a previous conversion or a default value under certain timing conditions — many sensors do, and the datasheet's timing diagram is where that shows up.

The corrective action depends on the mechanism, but the general principle is to add a plausibility or consistency check that would have caught this specific error — for example, a rate-of-change limit, a cross-check against a redundant measurement, or a sequence counter on the sensor read — so that the same class of failure is detectable in the future even if the root cause is intermittent.

**Possible follow-ups:**
- How would you design a test that reproduces a race condition that only manifests when the ISR and the main loop happen to interleave in a particular order?
- If the error turns out to be in the sensor's own output under a specific timing condition, how would you decide between a firmware workaround and a sensor change?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** The first thing I'd do is make sure the two hypotheses are actually competing rather than complementary — often, a split in the team is a sign that the two explanations describe different parts of the same failure chain, and the real question is which one is upstream. I'd restate each hypothesis as a specific, falsifiable prediction: if this is the root cause, what should we observe that we haven't observed yet, and what should we *not* observe? That reframing usually turns a philosophical disagreement into a set of experiments.

Then I'd design the cheapest, fastest test that discriminates between the two predictions — ideally one that can be run on existing units or existing data, without waiting for new hardware or a long test cycle. If no single test discriminates, I'd run both in parallel if the resources allow, with a clear owner and a deadline for each, rather than letting the team argue about which one to run first. I'd also explicitly look for evidence that would rule *out* each hypothesis, because teams tend to accumulate confirming evidence and neglect disconfirming evidence.

If the two hypotheses genuinely can't be separated with the available evidence, I'd be honest about that and choose the path that reduces risk fastest: implement the mitigation that addresses both, or the one that is cheapest to reverse, while continuing to gather data. What I would not do is let the investigation stall because the team can't agree — a documented decision with the reasoning, even if provisional, is better than an open disagreement that blocks progress. And I'd make sure the decision is recorded so that if new evidence later points the other way, it's clear what was decided and why.

**Possible follow-ups:**
- How would you handle a situation where the discriminating test is expensive or slow, and the schedule pressure is to just pick one hypothesis and move on?
- If the two hypotheses turn out to be complementary rather than competing, how does that change your corrective-action strategy?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, the system fails — is itself the most useful clue, and the first thing I'd do is help the engineer see that rather than treat it as a dead end. Testing in isolation removes the very conditions that produce the failure: the shared power rail, the shared ground, the timing interactions, the thermal environment, the cable and connector parasitics. So the debugging strategy needs to shift from "prove each component is good" to "find what changes when the components are together."

I'd sit down with them and ask two questions: what is the smallest configuration in which the failure still occurs, and what is the largest configuration in which it doesn't? That boundary is where the investigation should focus. Then I'd help them build a reproduction that is as close to the failing system as possible but still instrumentable — for example, keeping the real power supply and real cables but bringing out test points, rather than substituting a bench supply and jumper wires. Often the failure disappears precisely because the substitution changed the thing that mattered.

On the human side, I'd be careful not to take over the debugging — the goal is to unblock their thinking, not to solve it for them. I'd frame it as "let's look at this together for twenty minutes" rather than "here's what you should do," and I'd explicitly validate that the work they've done isn't wasted: ruling out the components is real progress, it just means the cause is in the interactions. If the schedule pressure is real, I'd help them time-box the next phase and agree on when to escalate or bring in additional help, so they're not carrying the uncertainty alone.

**Possible follow-ups:**
- How would you tell the difference between an engineer who needs a new debugging strategy and one who needs more time or resources?
- If the failure turns out to be a genuine system-level interaction that can't be reproduced on the bench, how would you structure the investigation around field data instead?