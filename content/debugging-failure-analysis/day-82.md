# debugging-failure-analysis — Day 82

## Q1: How would you approach debugging a device that passes all functional tests at room temperature but fails consistently when placed in an environmental chamber at 40°C?

**Answer:** Temperature-dependent failures almost always point to a parameter that is drifting toward a limit rather than a hard break, so the goal is to find which parameter has the least margin and confirm it crosses a threshold as temperature rises. I'd start by characterizing the failure boundary rather than jumping to a component: run the chamber in steps (e.g., 25, 30, 35, 40°C) with soak time at each step, and note the exact temperature at which the symptom first appears. That boundary is the most valuable data point — it tells you whether you're looking at a soft margin issue or a sharp transition like a thermal shutdown or a semiconductor junction effect.

From there I'd divide the problem into domains. On the hardware side, I'd measure the suspect rails and reference voltages at temperature, since bandgap references, oscillator frequency, and regulator output all shift with temperature. I'd check whether the failure correlates with a specific supply rail sagging, a clock drifting out of a timing window, or an analog offset growing. On the firmware side, I'd check whether any timing margin (setup/hold on an interface, ADC sampling window, watchdog period) is being consumed by the temperature-induced drift. A useful technique is to instrument the firmware to log internal timing and status so you can see whether the failure is the firmware misreading a marginal signal or the signal genuinely leaving spec.

I'd also verify the thermal path itself — a component that runs hot locally may be well within its own rating but heating a neighbor. A thermal camera or a thermocouple on suspect parts during the chamber run often reveals a localized hot spot that a room-temperature test never shows. The key discipline is to change one variable at a time: don't reflow parts and adjust firmware in the same iteration, or you won't know which fixed it.

**Possible follow-ups:**
- How would you distinguish a genuine component temperature coefficient from a mechanical issue like a connector losing contact as materials expand?
- If the failure only appears after the chamber has been at 40°C for an hour rather than immediately, how would that change your hypothesis?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a load-transient and power-distribution problem, so I'd treat it as two separate questions: is the regulator responding poorly to the transient, or is the transient coupling into the rail through the distribution network? I'd start by measuring the ripple at the load itself and at the regulator output separately, using a proper high-bandwidth probe technique — short ground lead or a ground spring, AC-coupled, bandwidth-limited to avoid picking up ambient noise. Where the ripple is worst tells you whether it's a regulator loop response issue or an impedance issue between the regulator and the load.

If the regulator output is clean but the load sees ripple, the problem is the impedance of the path — trace inductance, insufficient bulk capacitance, or a decoupling network that's ineffective at the transient's frequency content. I'd look at the transient's edge rate: a fast load step has energy at high frequency, where the bulk caps are inductive and only the small local decoupling caps help. That often means the fix is placing high-frequency decoupling closer to the load and adding bulk capacitance to supply the low-frequency portion. If the regulator output itself is ringing or drooping, I'd look at the control loop — compensation, output cap ESR, and whether the transient exceeds the regulator's slew capability.

I'd also check the return path. A switching subsystem can inject noise into the ground plane, and what looks like rail ripple may actually be ground bounce appearing differentially across the measurement. Probing ground at two points simultaneously often reveals this. The systematic approach is to isolate whether the disturbance is conducted (through the rail) or coupled (through ground or radiated), then address the specific mechanism rather than just adding capacitors everywhere.

**Possible follow-ups:**
- How would you decide between adding bulk capacitance versus improving the regulator's transient response?
- What role does the decoupling capacitor's ESL play, and how would you verify it's the limiting factor?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hardest part of this class of bug is that nothing in the system flags it, so the first job is to make the failure observable. I'd add instrumentation that captures the raw sensor data path — the ADC reading, any intermediate scaling or filtering, and the final value — with enough context (timestamp, operating mode, temperature, recent events) to reconstruct what happened. Without that, you're guessing. The goal is to turn a silent wrong value into a logged event with a traceable path.

Once it's observable, I'd look at where a plausible-but-wrong value can originate. Common causes are a stale read (the sensor wasn't ready and the firmware used the previous value), a race condition where a buffer is read while it's being updated, an indexing or scaling error that only triggers under specific conditions, or a communication glitch that returns a valid-looking but incorrect word. I'd check whether the wrong values cluster around specific events — a mode change, a communication retry, a buffer boundary — because that pattern points to the mechanism.

I'd also verify the sensor's own behavior: some sensors return a "last valid" value or a default on certain error conditions, and if the firmware doesn't distinguish that from a fresh reading, you get exactly this symptom. Checking the sensor's status register or a data-ready flag, rather than just reading the data register, is often the fix. The systematic approach is to reproduce the condition in a controlled way — fault injection, forced timing skew, or running at the edge of the operating envelope — so you can confirm the mechanism rather than infer it from field data alone.

**Possible follow-ups:**
- How would you design the logging so it doesn't itself perturb the timing you're trying to observe?
- If the wrong values only appear in the field and never on the bench, how would you narrow down the environmental or usage factor?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the trap is to let the team argue about which is more likely instead of designing a test that distinguishes them. My first move is to reframe the question: what observation would be true under one hypothesis and false under the other? That's the discriminating test, and it's usually cheaper and faster than continuing to accumulate supporting evidence for either side. I'd get the team to agree on that test before running it, so the result is accepted regardless of which way it falls.

I'd also make sure both hypotheses are stated precisely enough to be falsifiable. "It's a timing issue" is not a hypothesis; "the sensor's data-ready flag is being sampled before it settles when the bus is loaded" is. Vague hypotheses can't be tested and tend to persist because they're never disproven. Writing them down as specific, testable claims often reveals that one of them doesn't actually explain all the evidence, which resolves the split without a test.

On the human side, I'd keep the disagreement about the evidence, not about who's right. I'd acknowledge that both hypotheses are reasonable given what's known, and frame the discriminating test as the way to settle it fairly. If the test is expensive or slow, I'd look for a cheaper proxy that still discriminates. And I'd set a decision point: if the test is inconclusive, we pick the hypothesis with the lower-cost, lower-risk mitigation first while continuing to investigate, rather than stalling. The investigation has to converge, and a good leader makes the convergence explicit rather than letting it drift.

**Possible follow-ups:**
- What if the discriminating test is destructive or can only be run once — how would you decide?
- How would you handle it if the test result supports the hypothesis held by the less experienced engineer, and the senior engineer resists the conclusion?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, the system fails — usually means the failure depends on an interaction that isolation testing removes by definition. So the first thing I'd do is help the engineer see that their approach, while thorough, is testing the wrong thing. I'd ask them to walk me through what they've ruled out and how, and specifically what conditions their isolation tests don't reproduce: power sequencing, shared ground or supply impedance, timing between subsystems, thermal coupling, or the presence of other active circuitry. The gap between the bench setup and the real system is often where the bug lives.

I'd then help them shift from component-level testing to system-level observation. That means instrumenting the actual failing configuration — logging, scoping multiple signals simultaneously, capturing the state at the moment of failure — rather than removing parts. Intermittent failures need to be made to happen more often or captured when they do, so I'd look at whether we can increase the failure rate (run longer, stress the conditions, add load) or add triggers that freeze the state at the moment of failure. A logic analyzer with a trigger on the fault condition is often more productive than another round of isolation tests.

On the morale side, I'd normalize the frustration — intermittent system-level bugs are genuinely hard and a week without progress doesn't mean the engineer is failing. I'd pair with them rather than take over, because the goal is to build their debugging instincts, not just fix this bug. I'd also help them set smaller intermediate goals — "today we make it fail on demand" rather than "today we find the root cause" — so there's visible progress even before the answer. And I'd check whether the schedule pressure is real or perceived; sometimes the best thing a lead can do is shield the engineer from deadline noise so they can think clearly.

**Possible follow-ups:**
- How would you decide when to step in and debug it yourself versus continuing to coach?
- What would you do if the engineer's isolation testing had actually been the right approach and the bug was simply very rare?