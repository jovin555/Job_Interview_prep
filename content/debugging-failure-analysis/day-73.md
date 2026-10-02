# debugging-failure-analysis — Day 73

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key insight is that the offset appears only when three variables change at once: the enclosure is closed, the unit is mounted, and the test harness is replaced by the real signal path. I'd treat this as a classic "bench-to-installed" divergence and work to isolate which of those variables is actually responsible, rather than assuming it's mechanical stress or thermal.

First, I'd reproduce the offset and quantify it — magnitude, sign, and whether it's stable or drifts. A consistent offset points toward a DC-level shift (a ground reference change, a leakage path, or a bias current issue), whereas a noisy or drifting offset points toward coupling or thermal effects.

Then I'd divide the variables. I'd run the unit in the enclosure but on the bench (harness still connected) to see if the enclosure alone causes it. Then I'd run it open but in the final mounting position to see if the mounting causes it. Then I'd run it closed and mounted but with the harness still attached, to separate the signal-path change from the mechanical change. This isolates whether the cause is mechanical (flex, grounding through the mount, thermal), electrical (a different return path, a shield now connected), or a combination.

A common root cause in this scenario is that closing the enclosure changes the ground reference — for example, the analog front-end's return path now shares a chassis ground point that it didn't share on the bench, or a shield that was floating on the bench is now bonded to chassis. Another is that mounting hardware introduces a parallel ground path or a ground loop. I'd measure the analog front-end's reference and return nodes relative to the ADC's ground pin with a differential probe, both on the bench and installed, and compare.

I'd also check whether the offset correlates with the enclosure's thermal environment — a closed enclosure runs warmer, and a small thermal EMF at a connector or a bias-current shift in an instrumentation amplifier can produce a consistent offset. I'd log the offset versus temperature to rule that in or out.

Once I've isolated the variable, the fix follows from the mechanism: if it's a ground reference shift, I'd address the return path or add a proper star/kelvin reference; if it's thermal, I'd look at the front-end's temperature coefficient and compensation; if it's a shield bonding issue, I'd define the shield's reference explicitly. The important discipline is to change one variable at a time and confirm the offset tracks that variable before committing to a fix.

**Possible follow-ups:**
- How would you distinguish a ground-reference shift from a genuine sensor offset without a differential probe?
- If the offset only appears after the unit has been mounted for several hours, how would that change your investigation?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a load-transient and power-distribution problem, so I'd approach it as a power integrity investigation rather than a component-fault hunt. The rail is fine at steady state; the disturbance is injected by a switching load, which means the question is where that transient energy is going and why the rail can't absorb it.

First, I'd characterize the ripple properly. I'd measure at the load's power pins, not just at the regulator output, using a short-ground-spring probe or a coaxial pigtail to avoid picking up loop inductance from the probe itself. I'd capture the ripple's frequency, amplitude, and its timing relative to the switching event — does it occur at the switching edge, or is it a sustained oscillation? That distinguishes a transient response problem from a resonance problem.

Then I'd separate the possible mechanisms:
- **Regulator transient response** — if the ripple is a damped ring right at the load step, the regulator's control loop or output capacitance may be inadequate for the di/dt. I'd check the load step magnitude and slew rate against the regulator's transient spec.
- **PDN impedance / decoupling** — if the ripple is a sustained oscillation at a frequency unrelated to the regulator's bandwidth, it may be a resonance between the bulk and ceramic capacitors, or between the rail's parasitic inductance and the decoupling network. I'd sweep the PDN impedance or at least check the capacitor values and their self-resonant frequencies.
- **Ground bounce / return path** — if the ripple appears between the load's ground and the regulator's ground, the issue may be a shared return path with high di/dt. I'd probe ground at multiple points to see if there's a ground potential difference during switching.
- **Coupling** — if the ripple appears on the rail but the load current itself looks clean, the switching node may be coupling capacitively or inductively into the rail or its sense lines.

I'd also check whether the ripple is differential or common-mode relative to the rail's return, since that changes the fix — differential ripple points to decoupling or regulator response, common-mode points to layout and return path.

The fix depends on the mechanism: better decoupling and layout for PDN resonance, a faster or better-damped regulator for transient response, a dedicated return path or a ground plane change for ground bounce, and shielding or rerouting for coupling. I'd verify the fix by re-measuring at the same point under the same load condition, and also confirm I haven't just moved the problem to another frequency or another node.

**Possible follow-ups:**
- How would you tell the difference between a decoupling resonance and a regulator loop instability from the waveform alone?
- What layout changes would you prioritize if the ripple is caused by a shared return path?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** This is one of the harder classes of bug because there's no fault flag to anchor on — the system believes the data is valid. The investigation has to start by making the failure observable and reproducible, because "plausible but wrong" gives you almost nothing to work with until you can catch it in the act.

First, I'd try to characterize the error statistically. Is it a single sample, a burst, or a sustained offset? Does it correlate with time, temperature, operating mode, or a specific sequence of events? Even without a fault flag, the offline data may show a pattern — for example, the wrong values might cluster around a particular sensor read cadence or a particular system state. I'd mine the existing logs for that pattern before changing anything.

Then I'd add instrumentation to catch the next occurrence. That means logging the raw ADC value alongside the processed value, the timestamp, the sensor's status register, and the system state at the moment of the read. If the raw value is correct but the processed value is wrong, the bug is in the processing path — scaling, filtering, or a shared buffer. If the raw value is already wrong, the bug is upstream — the sensor, the interface, or the acquisition timing.

A common mechanism for "plausible but wrong" is a stale or torn read: the firmware reads a multi-byte value while the sensor is updating it, so it captures a mix of old and new bytes that happens to fall within the valid range. Another is a buffer or index error that occasionally reads the wrong channel or the wrong sample. Another is a filter or state machine that carries forward a value from a previous state. I'd look at the read sequence and the data path for any place where a value can be assembled from parts that aren't guaranteed to be consistent.

I'd also consider whether the error is in the sensor or the interface. If the sensor has an internal FIFO or a conversion-complete flag, the firmware may be reading before the conversion is done, or reading a register that isn't the one it thinks it is. I'd verify the interface timing against the sensor's datasheet and check for any missing handshake.

Once I can reproduce it, I'd use fault injection or a targeted stress test — for example, forcing the sensor to update at a different rate, or injecting a known pattern — to confirm the mechanism. The fix would be to make the read atomic (a proper latch or a read-verify-read), to add a plausibility check that's tighter than the current self-test, or to correct the timing or indexing. I'd also add a lightweight consistency check in the field so the next occurrence is caught immediately rather than weeks later.

**Possible follow-ups:**
- How would you design a plausibility check that catches this without generating false positives?
- If the error only appears in the field and never on the bench, how would you make it reproducible?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the temptation is to argue about which is more likely, but that's not a productive use of the team's time. The better move is to reframe the question from "which is right?" to "what evidence would distinguish them?" — and then design the cheapest, fastest test that produces that evidence.

First, I'd make both hypotheses explicit and falsifiable. For each, I'd write down what it predicts: if hypothesis A is true, what should we see that we don't see under hypothesis B? If the two hypotheses predict the same observable, then they're not actually distinguishable yet, and we need a different experiment or a finer measurement. If they predict different observables, we have a clear test.

Then I'd prioritize by cost and information gain. A test that's cheap and produces a clear yes/no is worth running even if it's not the most likely cause, because eliminating a hypothesis is progress. I'd avoid tests that are expensive and ambiguous — those tend to produce more debate, not less.

I'd also look for a test that can distinguish both hypotheses at once, rather than running two separate investigations. For example, if one hypothesis is a timing issue and the other is a marginal component, a test that varies timing while holding the component constant (and vice versa) can separate them in a single experiment.

Throughout, I'd keep the team aligned on the decision rule: we agree in advance what result would confirm or eliminate each hypothesis, so the outcome isn't contested after the fact. If the evidence still doesn't separate them, I'd consider whether the two causes could be interacting — sometimes the answer is "both, in a specific combination," and the investigation needs to test the combination rather than each in isolation.

If the schedule forces a decision before the evidence is conclusive, I'd be explicit about that: we're choosing the most likely cause based on current evidence, we're documenting the residual uncertainty, and we're defining a monitoring or verification step to confirm the fix actually resolves the field issue. That way the decision is defensible and reversible if new evidence appears.

**Possible follow-ups:**
- How would you handle it if the distinguishing test is expensive or would take weeks to run?
- What would you do if the team agrees on the test but disagrees on how to interpret the result?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The first thing I'd notice is the pattern: they're testing components in isolation, and everything passes. That's a strong signal that the bug isn't in any single component — it's in the interaction between them, or in a condition that only exists at the system level. The junior engineer isn't failing; they're using a debugging strategy that's well-suited to component faults and poorly suited to system-level intermittent faults. My job is to help them shift strategy, not to take over.

I'd start by asking them to walk me through what they've ruled out and how. That does two things: it respects the work they've done, and it lets me see whether there's a gap in their reasoning or a test that wasn't as conclusive as they thought. Often the breakthrough comes from realizing that a test that "passed" didn't actually exercise the failing condition.

Then I'd help them reframe the problem. Instead of "which component is bad?", the question becomes "what conditions are present when it fails that aren't present when it passes?" That means capturing the failure in context — logging the system state, the timing, the environmental conditions, and the sequence of events leading up to it — rather than testing components on the bench. I'd suggest they instrument the system to catch the failure in the act, and then work backward from the captured data.

I'd also introduce the idea of narrowing by bisection at the system level: if the failure is intermittent, can they make it more frequent by stressing the system — running it longer, at temperature extremes, with a particular workload, or with a specific sequence of operations? A failure that happens once a day is hard to debug; one that happens every few minutes is tractable. Accelerating the failure is often the single highest-leverage step.

On the morale side, I'd be explicit that intermittent system-level bugs are genuinely hard and that several days without progress is normal, not a sign of failure. I'd check in regularly, celebrate the eliminations as progress, and make sure they're not working in isolation — pairing them with someone for a session, or reviewing their logs with them, can break a stall. I'd also watch the schedule pressure: if the bug is blocking a milestone, I'd help them communicate that upward rather than letting them absorb the pressure silently.

If after a focused effort the bug still isn't resolved, I'd consider whether to bring in additional help or to escalate the risk, but I'd frame that as a resourcing decision, not a judgment on their work.

**Possible follow-ups:**
- How would you help them decide when to stop investigating a hypothesis and move on?
- What would you do if they resist the change in approach because they're convinced the component-level testing will eventually find it?