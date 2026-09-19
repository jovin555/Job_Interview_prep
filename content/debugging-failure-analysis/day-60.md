# debugging-failure-analysis — Day 60

## Q1: How would you approach a failure investigation where a device's power rail collapses only during a specific operating mode, but the regulator and its passives all measure within specification when the board is powered in isolation?

**Answer:** The key insight is that "regulator measures fine in isolation" and "rail collapses in-system" are not contradictory — they describe two different load and source conditions, so the investigation should focus on what changes between them. I'd start by characterizing the collapse itself: is it a droop (regulator running out of loop bandwidth or current limit), a shutdown (fault protection tripping), or a brownout from an upstream source? That distinction drives everything downstream.

Next I'd reproduce the failure with the rail instrumented — a current probe on the regulator output and a scope on the rail at the load, not at the regulator output pin. Measuring at the regulator hides the IR drop and inductance between the regulator and the actual load, which is often where the real story is. I'd also capture the enable/fault pins and any power-good signal to see whether the regulator is actively shutting down or simply being dragged down.

Then I'd isolate the variable: disable subsystems one at a time within that operating mode to find which load is responsible. If the collapse correlates with a high-current event — a motor, a radio transmit burst, a heater, a flash write — I'd look at load transient response, inrush, and whether the bulk capacitance is adequate for that transient. I'd also check whether the mode change alters the regulator's own configuration (mode pin, feedback network, compensation) or whether an upstream rail sags first and takes this one with it.

Finally, I'd compare measured behavior against the regulator's datasheet transient response and current-limit curves, and verify the passives under the actual DC bias and temperature — a capacitor that measures fine on an LCR meter can lose most of its capacitance under bias, which is a classic reason a rail that "tests fine" collapses under a real transient.

**Possible follow-ups:**
- How would you tell the difference between a regulator hitting current limit and a load transient exceeding the loop's ability to respond?
- If the collapse only happens after the device has warmed up, how would that change your approach?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** Ripple that appears only under a switching load points to a source-impedance or loop-response problem rather than a steady-state regulation problem, so I'd approach it as a power integrity investigation rather than a component-fault hunt.

First, I'd measure properly: ripple must be probed at the point of load with a short ground lead (or a coaxial pigtail) to avoid picking up radiated switching noise in the probe loop. Measuring at the regulator output with a long ground clip is a common way to get a misleadingly clean or misleadingly noisy result. I'd capture the ripple synchronized to the subsystem's switching event so I can see whether it's load-transient-induced droop, ringing from parasitic inductance, or coupled noise.

Then I'd separate the mechanisms. If the ripple is a transient droop-and-recovery, that's a loop bandwidth or output capacitance issue — the regulator can't respond fast enough to the load step. If it's high-frequency ringing, that's likely parasitic inductance in the power path or a resonance between the output cap and the load's input cap. If it's periodic and correlates with the subsystem's PWM frequency, it may be conducted or radiated coupling rather than a regulation problem at all.

I'd then test the hypotheses: add bulk or high-frequency decoupling at the load to see if the ripple changes, which distinguishes a source-impedance problem from a coupling problem. Probe the ground return path to check for ground bounce. If the ripple persists with the load physically separated and connected by short leads, it's likely coupling; if it disappears, it's likely the power delivery network.

The corrective direction depends on the mechanism — better decoupling and layout for impedance, compensation or bulk capacitance for loop response, and filtering or shielding for coupling — but the important part is not to jump to "add more caps" before knowing which mechanism is actually at play.

**Possible follow-ups:**
- How would you distinguish conducted ripple from radiated coupling in this scenario?
- What role does the ground return path play, and how would you probe it?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** This is one of the harder classes of failure because every automated check passes — the value is in range, the self-test passes, and the system has no reason to flag it. The investigation has to start by making the failure observable, because right now the only detector is offline human review.

First, I'd characterize the error from the data: is it a fixed offset, a scaling error, a stuck value, a value from a different channel, or a transient that self-corrects? The pattern often points directly at the mechanism. A value that looks like a neighboring channel's reading suggests an addressing or multiplexing issue. A value that's plausible but slightly off suggests a calibration or reference problem. A value that's correct most of the time and wrong occasionally suggests a timing or race condition in the acquisition path.

Then I'd instrument the acquisition chain to capture the raw data alongside the processed value — ADC output, any intermediate scaling, and the final reported value — so I can see where the corruption is introduced. If the raw ADC value is correct but the reported value is wrong, the problem is in firmware processing. If the raw value is already wrong, it's in the analog front-end, the reference, or the sampling timing.

I'd also look at what's happening in the system at the moment of the bad reading: is another subsystem active, is a conversion running concurrently, is there a shared resource (SPI bus, DMA channel, ADC) being used by more than one consumer? Plausible-but-wrong values are often a symptom of a shared resource being read at the wrong time or a buffer being overwritten.

Finally, I'd add a lightweight integrity check — a cross-check against a redundant measurement, a plausibility window tighter than the self-test, or a checksum on the data path — not as the fix, but as a way to catch the next occurrence with context attached, so the investigation can converge instead of relying on luck.

**Possible follow-ups:**
- How would you design a plausibility check that catches this class of error without generating false positives?
- If the raw ADC value is correct but the reported value is wrong, where would you look first in the firmware?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the temptation is to argue about which is more likely — but that's not a productive use of the team's time. The productive move is to design a test that discriminates between them, so the evidence decides rather than seniority or conviction.

I'd start by writing down both hypotheses explicitly, along with what each one predicts. If hypothesis A is true, we should see X; if hypothesis B is true, we should see Y. If the two hypotheses make the same prediction, they're not actually distinguishable yet and we need a sharper test. If they make different predictions, that difference is the experiment.

Then I'd look for the cheapest, fastest test that separates them — ideally one that can be run on existing hardware or data without a long build cycle. Sometimes the discriminating evidence is already in the failure data and just hasn't been extracted. Sometimes it requires a targeted experiment: a controlled fault injection, a modified test condition, or a measurement that hasn't been taken yet.

I'd also be explicit with the team about the process: we're not voting on the root cause, we're running a test. That depersonalizes the disagreement and keeps the senior engineer's experience valuable — their hypothesis gets tested like any other, and if it's right, the test will show it. If the test is inconclusive, we design the next one.

Throughout, I'd keep the investigation documented so that whichever hypothesis is eliminated, the reasoning is traceable. And I'd set a checkpoint: if after a defined effort the discriminating test still isn't conclusive, we escalate to a broader set of conditions or bring in additional expertise, rather than letting the investigation stall on an unresolved split.

**Possible follow-ups:**
- What if the discriminating test is expensive or slow — how do you decide whether to run it or pursue a mitigation in parallel?
- How do you keep a senior engineer engaged when their hypothesis is the one being tested and possibly eliminated?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The first thing I'd do is recognize that the engineer isn't failing — they're stuck in a pattern that's very common and very understandable: testing components in isolation, finding everything passes, and concluding the problem must be elsewhere. The issue is that intermittent system-level failures often don't reproduce in isolation, so isolation testing can't find them. The engineer needs a different approach, not more effort in the same direction.

I'd sit down with them and reframe the problem: instead of asking "which component is broken," ask "what conditions are present when the failure occurs that aren't present when it doesn't." That shifts the work from component testing to condition characterization — capturing the state of the system at the moment of failure, not just the state of individual parts.

Practically, I'd help them build observability into the system: logging, instrumentation, or a test harness that captures the relevant signals continuously so that when the failure occurs, there's data. Intermittent failures are almost impossible to debug without a way to catch them in the act. I'd also help them define a reproduction strategy — can the failure be made more frequent by stressing a particular condition (temperature, load, timing, sequence)? A failure that happens once a day is much harder to debug than one that happens once a minute, and often the same underlying mechanism can be accelerated.

I'd also make sure they're not working in isolation themselves — pairing them with someone who has seen similar failures, or reviewing their test setup for blind spots, can break a stall quickly. And I'd be explicit that the schedule pressure is real but that flailing faster doesn't help; a focused change of approach is the fastest path.

Finally, I'd check in regularly but not hover — give them ownership of the new approach while making it clear I'm available to help think through the next step. The goal is to get them unstuck and rebuild their confidence, not to take the problem away from them.

**Possible follow-ups:**
- How would you help them decide when to escalate versus keep digging?
- What would you do if the failure still doesn't reproduce even with the new approach?