# debugging-failure-analysis — Day 75

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only when two variables change together: the enclosure is closed, and the unit is in its final mounting position. That points away from the analog signal chain itself and toward something mechanical, thermal, or grounding-related that changes when the assembly is complete.

I'd start by separating those two variables rather than treating them as one condition. First, test the board on the bench with the enclosure closed but not mounted — if the offset appears, it's an enclosure effect (thermal, shielding, or mechanical stress on the PCB). If it doesn't, mount the unit in its final position with the enclosure open — if the offset appears, it's a mounting effect (chassis grounding, strain on connectors, or a change in the reference plane).

For an enclosure effect, the usual suspects are thermal drift of a reference or amplifier as heat builds up in the sealed volume, or a change in parasitic capacitance/grounding when the board sits close to a conductive enclosure wall. I'd log the offset versus time and versus internal temperature to see whether it tracks warm-up. For a mounting effect, I'd look at whether the chassis introduces a ground loop, whether mounting hardware is shorting or loading a net, or whether the board flexes enough to shift a sensitive node.

The measurement discipline matters here: I'd measure the offset at the ADC input with a high-impedance probe in both states, so I can tell whether the error is introduced before the ADC (analog domain) or after it (reference/digital domain). If the analog input is clean but the reported value is offset, the problem is downstream — reference voltage, ADC configuration, or grounding of the reference. If the analog input itself shifts, it's the front-end or its environment.

**Possible follow-ups:**
- How would you determine whether the offset is thermal or mechanical if both change at the same time when the enclosure closes?
- What would you check first if the offset is repeatable but only appears after the unit has been mounted for several minutes?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and power-distribution problem, so I'd treat it as two questions: is the regulator responding poorly to the transient, or is the transient coupling into the rail through the distribution network rather than through the regulator?

First, I'd characterize the transient itself. I'd probe at the load with a short-ground-tip probe or a proper high-bandwidth differential setup, and capture the switching event to see the amplitude, slew rate, and duration of the current step. That tells me what the regulator is actually being asked to supply.

Then I'd probe the rail at several points — at the regulator output, at the bulk capacitor, at the local decoupling of the switching subsystem, and at the sensitive load — to see where the ripple is worst. If the ripple is worst at the regulator output, the regulator's loop response or output capacitance is the issue. If the ripple is worst at the far end of the rail, it's an impedance problem in the distribution network: trace inductance, insufficient local decoupling, or a shared return path.

I'd also check the return path. A common mistake is to assume the ripple is on the supply when it's actually ground bounce on the return, which shows up as apparent ripple when measured single-ended. A differential measurement between the rail and its local ground reference will separate those.

Once I know where the ripple originates, the fixes are usually one of: add or reposition local decoupling to shorten the high-frequency loop, add bulk capacitance to slow the transient seen by the regulator, improve the regulator's transient response (compensation, feed-forward), or separate the noisy subsystem's supply/return from the sensitive load's.

**Possible follow-ups:**
- How would you decide between adding bulk capacitance and improving the regulator's loop response?
- What measurement mistakes would make ripple look worse than it actually is?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hardest part of this class of bug is that nothing in the system flags it, so the first job is to make the failure observable. I'd start by building a way to detect it in real time rather than relying on offline review: a reference channel, a redundant read, or a plausibility check that compares the sensor against an independent estimate (for example, a second sensor, a model-based expectation, or a cross-check against a related measurement).

With detection in place, I'd narrow down where the corruption enters the chain. The value is plausible, which means it's not a gross data-path failure like a stuck bus or a zeroed buffer — it's more likely a subtle issue: a stale sample being used, a buffer being read before it's fully written, a scaling or calibration factor applied inconsistently, or a race between the sampling task and the consumer of the data.

I'd instrument the path: log the raw ADC value, the value after each processing stage, and the timestamp of each. If the raw value is correct but the processed value is wrong, the bug is in the processing. If the raw value is already wrong, the bug is in acquisition — timing, channel selection, or a conversion that completed before the input settled.

I'd also look at the timing relationship between the sensor read and whatever else the system is doing. A plausible-but-wrong value is often a sample taken during a transient — during a multiplexer switch, during a calibration cycle, or while another subsystem is loading the reference. Reproducing it under controlled conditions (forcing the concurrent activity) is usually the fastest way to confirm.

**Possible follow-ups:**
- How would you design a plausibility check that catches this without generating false positives?
- If the raw value is correct but the processed value is wrong, what are the most likely firmware causes?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the trap is to keep arguing about which is more likely. The productive move is to stop debating and design a test that discriminates between them — a test where the two hypotheses predict different outcomes.

I'd start by writing down, for each hypothesis, what it predicts: what should happen if it's true, and what should happen if it's false. Then I'd look for the cheapest, fastest experiment that separates those predictions. Often that's a targeted fault-injection or a controlled variation of one variable — for example, if one hypothesis says the failure depends on temperature and the other says it depends on timing, I can vary temperature at fixed timing and timing at fixed temperature and see which one moves the failure rate.

If no single test cleanly separates them, I'd consider whether they might both be contributing — sometimes the answer is "both, in sequence," and the investigation needs to establish the order rather than pick a winner. I'd also be explicit about what evidence would change my mind, so the team is working against a shared standard rather than defending positions.

On the team dynamics: I'd frame the split as a strength — two well-supported hypotheses mean the investigation has narrowed the space — and redirect the energy from advocacy to experiment design. I'd assign owners to each hypothesis and give them a deadline to produce discriminating evidence, so the decision is driven by data rather than by seniority or persistence.

**Possible follow-ups:**
- What would you do if the discriminating test is expensive or slow to run?
- How would you keep the team aligned if the evidence ends up supporting the hypothesis held by the less senior engineer?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — everything passes in isolation, the system fails — usually means the bug lives in an interaction, not in a component. Testing components in isolation is the right instinct, but it can't find a bug that only exists when the components are together, so the first thing I'd do is help the engineer reframe the problem rather than push harder on the same approach.

I'd sit down with them and ask two questions: what exactly have you observed, and what have you ruled out? Often the frustration comes from a mental model that's slightly off, and walking through the evidence together surfaces the assumption that's wrong. I'd resist the urge to take over — the goal is to get them unstuck, not to solve it for them.

Then I'd help them change the method. If they've been testing bottom-up (components in isolation), I'd suggest top-down: reproduce the failure at the system level first, then bisect — disable or bypass subsystems one at a time until the failure disappears, which localizes the interaction. If the failure is intermittent, I'd help them build a way to catch it in the act: logging, a trigger on the failure condition, or a stress condition that raises the failure rate so it's reproducible.

On the schedule pressure: I'd be honest that the fastest path is usually to change the approach, not to work longer hours on the same one. I'd also make sure they know it's normal to get stuck on interaction bugs and that asking for help early is a strength, not a failure. If the schedule is genuinely tight, I'd pair with them for a focused session rather than leave them to grind alone.

**Possible follow-ups:**
- How would you help them build a reproducible test case for an intermittent failure?
- What would you do if, after changing the approach, the failure still can't be reproduced on demand?