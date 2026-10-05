# debugging-failure-analysis — Day 76

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key insight is that the offset appears only when two variables change together — enclosure assembly and final mounting — so the first job is to separate them rather than treat "installed" as one condition. I'd build a test matrix: open bench, board in enclosure but loose on the bench, enclosure closed and torqued, and finally mounted in the operating position. If the offset appears at the "enclosure closed" step, the cause is mechanical or thermal coupling inside the unit; if it only appears at final mounting, it's likely a ground-path or stray-coupling change introduced by how the unit contacts its mounting surface.

From there I'd reason about what an enclosure actually changes: it adds a ground reference path, it changes airflow and therefore local temperature, it can flex the PCB or press on connectors, and it can bring a metal surface close to sensitive traces. A small consistent offset smells like a DC-level shift — a ground reference moving, a bias network being loaded, or a thermocouple-like junction forming — rather than noise. I'd measure the analog front-end's reference and ground at the ADC input with a high-impedance probe in each configuration, and compare the difference between the board's local ground and the enclosure/mounting ground. If the offset tracks a ground potential difference, I'd look at how the analog ground is bonded and whether the enclosure is creating a parallel return path.

I'd also check whether the offset is temperature-correlated by measuring immediately after assembly versus after thermal soak, since a closed enclosure changes the thermal environment. If the offset is stable and repeatable, that points to a DC/grounding mechanism; if it drifts with time or temperature, it points to thermal or mechanical stress. Throughout, I'd keep one variable changing at a time so I can attribute the offset to a specific condition rather than guessing.

**Possible follow-ups:**
- If the offset disappears when you open the enclosure but the temperature is the same, what does that tell you?
- How would you distinguish a ground-reference shift from a genuine sensor or amplifier offset?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a load-transient and power-integrity problem, so I'd start by characterizing the ripple properly rather than just observing it. I'd measure at the point of load, not at the regulator output, using a short-ground-spring probe or a coaxial pigtail to avoid picking up loop inductance from the probe itself — a long ground lead will show ringing that isn't really there. I'd capture the ripple synchronized to the switching event so I can see whether it's a transient response, a sustained oscillation, or a periodic dip.

Then I'd separate the mechanisms. If the ripple is a transient dip at the moment the subsystem switches on, the likely causes are insufficient bulk capacitance, a slow regulator loop response, or excessive trace/plane impedance between the regulator and the load. If it's sustained ringing, I'd suspect the regulator's control loop is marginally stable under that load, or there's an LC resonance between the output capacitor and the parasitic inductance of the routing. If it's a periodic dip at the subsystem's switching frequency, I'd look at whether the subsystem's return current is sharing the same ground path as the sensitive rail.

I'd probe the ground bounce at the load's ground pin simultaneously with the rail, because a lot of "ripple" measured single-endedly is actually ground movement. I'd also check the regulator's datasheet for its transient response and compare the measured dip against the expected response for the actual load step. Fixes would follow the mechanism: more or better-placed bulk and high-frequency decoupling, tighter load-transient routing, separating the high-current return from the analog return, or adjusting the regulator's compensation if the loop is the issue. I'd verify each change with the same synchronized measurement so I can attribute the improvement.

**Possible follow-ups:**
- How would you tell whether the dip is caused by the regulator's loop response versus the PCB's impedance?
- What role does the placement of the bulk capacitor play relative to the load?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hardest part of this class of bug is that nothing in the system flags it, so the first task is to make the failure observable. I'd add instrumentation that captures the raw sensor data path — the ADC reading, the timestamp, the conversion result, and the value actually transmitted — so I can compare what the hardware produced against what the firmware reported. Without that, any investigation is guesswork. I'd also log enough context (operating mode, temperature, recent commands, bus activity) to correlate the bad value with a condition.

Then I'd reason about where a plausible-but-wrong value can come from. It could be a stale value being read because a conversion wasn't complete, a race between the sensor read and a buffer update, a scaling or calibration constant applied incorrectly under a specific code path, a bit error on the bus that happens to land in range, or a value from the wrong channel being read due to a multiplexer or register configuration issue. The fact that it's plausible and in-range suggests it's not a gross corruption but a logic or timing problem — the system is reading a real number, just not the right one at the right time.

I'd try to reproduce it deterministically by stressing the conditions most likely to trigger it: high bus load, concurrent operations, temperature extremes, or rapid mode changes. If I can reproduce it, I'd use a logic analyzer or trace to see the exact sequence. If I can't, I'd add a checksum or sequence tag to the sensor data path so that a stale or mismatched value can be detected in the field, which both helps the investigation and is a reasonable defensive measure. The corrective action depends on the mechanism, but the discipline is the same: make it observable, reproduce it, then fix the specific cause rather than the symptom.

**Possible follow-ups:**
- How would you distinguish a stale-value bug from a bus bit error that happens to be in range?
- What would you add to the data path to detect this in the field without changing the measurement?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the danger is that the team argues about which is more likely instead of designing a test that separates them. My first move is to reframe the disagreement as a question: what observation would be true if hypothesis A is correct and false if hypothesis B is correct? That turns a debate into an experiment. I'd list the discriminating evidence for each hypothesis and identify the cheapest, fastest test that distinguishes them — ideally one that doesn't require a full rebuild or a long field trial.

I'd also be explicit about what each hypothesis predicts. If A is a timing violation, it should get worse with temperature or clock margin; if B is a layout coupling issue, it should correlate with a specific physical configuration or a specific aggressor signal. Those predictions are testable. I'd assign the tests, set a time box, and agree in advance what result would cause the team to abandon each hypothesis — that prevents the investigation from drifting.

If the tests are inconclusive, I'd consider whether both mechanisms could be contributing, which is common in intermittent failures, and whether a fix that addresses both is practical. I'd also make sure the decision is documented with the evidence, so that if the chosen fix doesn't resolve the issue, the team can revisit the other hypothesis without relitigating the whole investigation. The goal is to converge on evidence, not on consensus or seniority.

**Possible follow-ups:**
- What if the discriminating test is expensive or slow — how do you decide whether to run it?
- How do you keep the team aligned if the evidence later points back to the hypothesis you set aside?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here is classic: component-level testing passes, system-level failure persists, which usually means the problem is in the interaction between components rather than in any one component. My first step is to help the engineer reframe the problem — not "which component is broken" but "what condition exists at the system level that doesn't exist in isolation." That reframe alone often unblocks people, because they've been proving components are good, which was never the question.

I'd sit with them and ask what they've actually observed versus assumed, and what the failure depends on — does it correlate with temperature, time, a specific sequence of operations, a particular unit, or a particular configuration? Intermittent failures usually have a hidden variable, and the job is to find it. I'd suggest instrumenting the system to capture the state at the moment of failure rather than testing components out of context, and I'd help them design a reproduction that keeps the system intact.

I'd also be mindful of the human side. Several days without progress is demoralizing, and pressure from the schedule makes it worse. I'd acknowledge the work they've done — ruling out components is real progress — and give them a concrete next step rather than just "keep looking." If I have relevant experience, I'd share how I'd approach it, but I'd let them drive so they build the skill. If the schedule is genuinely tight, I'd help them escalate or bring in another set of eyes rather than let them grind alone. The goal is to get them unstuck and to leave them with a better method for the next intermittent failure.

**Possible follow-ups:**
- How do you balance giving direction versus letting them solve it themselves?
- What would you do if the failure still can't be reproduced after another week?