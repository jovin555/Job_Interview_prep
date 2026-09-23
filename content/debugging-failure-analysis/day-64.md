# debugging-failure-analysis — Day 64

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key insight is that nothing about the electronics changed — only the mechanical, thermal, and electromagnetic environment did. So I'd treat the enclosure and mounting position as the variables under test, not the circuit.

First, I'd reproduce the offset reliably and quantify it: magnitude, sign, and whether it's stable or drifts. A *consistent* offset points toward a static effect — mechanical stress, a changed ground reference, or a thermal gradient — rather than a random noise coupling issue.

Then I'd bisect the mechanical assembly. Test the bare board on the bench (baseline), then with the enclosure open but the board mounted on its standoffs, then with the lid on, then in the final installed orientation. That sequence isolates whether the cause is mounting stress, the closed enclosure, or the installation position.

The most common culprits for a consistent offset:
- **Mechanical stress on the sensor or its solder joints** — mounting torque or board flex changes the strain on a bridge-type sensor or its compensation network, shifting the zero point. I'd check mounting torque specs and whether the offset correlates with screw tightening.
- **A changed ground/return reference** — once the enclosure is bonded and the unit is installed, the analog ground reference can shift relative to the ADC's reference, producing a fixed offset. I'd measure the analog front-end output and the ADC reference simultaneously, both referenced to the same point.
- **Thermal gradient** — a closed enclosure changes the thermal profile, and a thermocouple junction or a resistor divider with a temperature coefficient can introduce a stable offset once the unit reaches thermal equilibrium. I'd let the unit soak to steady state and see if the offset tracks temperature.
- **Capacitive/EMI coupling to the enclosure** — less likely to give a *consistent* offset, but possible if a shield or a metal surface is now part of the signal return path.

I'd confirm the mechanism by changing one variable at a time — e.g., loosen the mounting screws and see if the offset disappears, or add a temporary thermal break and re-measure. Once confirmed, the fix is usually mechanical (mounting/isolation), layout (reference/return path), or thermal (compensation/placement), and I'd verify it with the same assembled-and-installed test that exposed the problem.

**Possible follow-ups:**
- If the offset only appears after the unit has been installed for a while, how would you separate a thermal effect from a mechanical creep effect?
- How would you decide whether to fix this in hardware versus compensating it in firmware calibration?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and power-distribution problem, so I'd approach it as a power integrity investigation rather than a component fault.

First, I'd characterize the ripple properly. Where am I measuring? A ripple measurement is only meaningful if it's taken correctly — at the decoupling capacitors with a short ground lead (or a proper tip-and-barrel probe), not with a long ground clip that picks up loop inductance. I'd capture the waveform and note the frequency, amplitude, and whether it's synchronized with the switching subsystem's switching frequency or with the regulator's own switching frequency.

Then I'd separate the possible mechanisms:
- **Insufficient bulk/decoupling capacitance** — the switching subsystem draws a fast current step, and the local charge reservoir can't supply it before the regulator loop responds, so the rail sags and rings. I'd look at the transient response and see if adding bulk capacitance locally reduces the ripple.
- **Regulator loop bandwidth / stability** — if the load step is faster than the regulator's control loop can respond, the rail dips. I'd check the regulator's transient response spec and whether the output capacitor ESR/ESL is within the recommended range for stability.
- **PDN impedance** — at the switching frequency and its harmonics, the impedance from the load to the regulator may have a resonance (from capacitor ESL and trace inductance) that amplifies the ripple. A PDN impedance sweep, or simply probing at multiple points along the rail, can reveal a high-impedance node.
- **Ground bounce / return path** — if the high-current subsystem shares a return path with sensitive analog circuitry, the switching current develops a voltage across the shared ground impedance. I'd probe the ground at both the source and the load to see if the "ripple" is actually a ground shift.
- **Coupling** — the ripple could be radiated or capacitively coupled from the switching node rather than conducted. A near-field probe would help distinguish this.

I'd confirm the mechanism by changing one thing at a time: add local bulk capacitance, then improve the ground return, then check the regulator's compensation. The fix is usually a combination of better local decoupling, a cleaner return path, and possibly a regulator with faster transient response or a feed-forward capacitor.

**Possible follow-ups:**
- How would you distinguish conducted ripple from radiated coupling without a full EMC chamber?
- If adding capacitance makes the ripple worse, what would that tell you about the regulator's stability?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** This is one of the harder classes of bug because there's no fault flag to anchor on — the system believes the data is valid. So the investigation has to start with making the failure observable and reproducible, then working backward from the bad value to its origin.

First, I'd instrument the data path. If the value is plausible but wrong, the corruption could happen at any stage: the sensor itself, the analog front-end, the ADC, the firmware's read/conversion routine, the storage, or the transmission. I'd add logging or tracing at each stage — raw sensor output, ADC counts, post-conversion value, stored value, transmitted value — so that when a bad value occurs, I can see exactly where it first diverges from a known-good reference.

Second, I'd look for patterns in the bad data. Is the wrong value always off by a similar amount, or a similar ratio? Is it a single-bit error, a stuck value, a value from a different channel, or a value that looks like a previous sample? Each pattern points to a different mechanism:
- **Single-bit flips** suggest a memory or bus integrity issue — ECC, a marginal timing violation, or a soft error.
- **A value from a different channel** suggests an ADC multiplexer sequencing or channel-address bug.
- **A stale value** suggests a read that didn't complete or a buffer that wasn't refreshed.
- **A scaled/offset value** suggests a conversion or calibration bug.

Third, I'd try to reproduce it under controlled conditions — temperature, supply voltage, timing stress, or a specific sequence of operations — since intermittent plausible-but-wrong values often correlate with a marginal condition rather than a hard fault.

Finally, I'd consider whether the system's own validation is adequate. If a plausible-but-wrong value can pass every self-test, that's a gap in the validation logic, and part of the corrective action may be to add a plausibility or cross-check that would catch it in the field.

**Possible follow-ups:**
- If you can't reproduce it on the bench, how would you design a field data-logging scheme to capture enough context to diagnose it?
- How would you decide whether the root cause is in the sensor, the analog front-end, or the firmware?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the temptation is to argue about which is more likely. I'd redirect the team away from debate and toward a discriminating test — a test whose outcome is different depending on which hypothesis is true.

First, I'd make both hypotheses explicit and falsifiable. For each one, I'd ask: what evidence would we expect to see if this were the root cause, and what would we expect *not* to see? Writing that down often reveals that one hypothesis is actually a subset of the other, or that they're not mutually exclusive — sometimes both contribute.

Then I'd design the cheapest, fastest test that separates them. The goal isn't to prove one right; it's to eliminate one. A good discriminating test changes one variable that only one hypothesis predicts matters. For example, if one hypothesis is thermal and the other is timing, a test that holds temperature constant while varying timing (or vice versa) will separate them.

If the two hypotheses can't be separated by a single test, I'd run them in parallel with a clear decision point: each track gets a defined experiment, a defined timeframe, and a defined result that would confirm or refute it. That keeps the team productive instead of stalled.

I'd also watch for the human dynamic — when a team is split, people often dig in. I'd make it clear that the goal is the correct root cause, not winning the argument, and that a hypothesis being eliminated is a successful outcome, not a failure. If a senior person is attached to one hypothesis, I'd give them a fair hearing but insist the decision be driven by evidence.

Finally, I'd document the reasoning and the decision criteria so that when the answer emerges, it's clear *why* the team chose the path it did — which matters for the corrective action and for any future audit.

**Possible follow-ups:**
- What would you do if the discriminating test is expensive or takes weeks, and the schedule is tight?
- How would you handle it if, after the test, the evidence still doesn't clearly favor one hypothesis?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The first thing I'd notice is the pattern: they're testing components in isolation, and everything passes. That's a strong signal that the problem isn't in any single component — it's in the interaction between them, or in a condition that only exists at the system level. So the debugging *strategy* needs to change, not just the effort.

I'd start by sitting down with them and asking them to walk me through what they've tried and what they've observed — not to audit them, but to understand their mental model. Often, explaining it out loud surfaces an assumption they haven't questioned. I'd also ask what the failure actually looks like at the system level: when does it happen, what's the symptom, what's the surrounding context.

Then I'd help them reframe. Instead of testing components in isolation, I'd suggest reproducing the failure at the system level and then *bisecting* the system — removing or disabling subsystems one at a time to see which one's presence is necessary for the failure. That's a divide-and-conquer approach that works when the fault is in an interaction rather than a component.

I'd also encourage them to instrument the system so the failure is observable when it happens — logging, a trigger, a scope capture — because an intermittent failure that leaves no trace is very hard to chase. And I'd remind them that "everything passes in isolation" is itself a clue: it means the test conditions don't match the failure conditions, so the next step is to figure out what's different about the system-level environment.

On the human side, I'd normalize the frustration — intermittent system-level bugs are genuinely hard, and several days without progress doesn't mean they're doing it wrong. I'd offer to pair on it for a session, not to take over, but to give them a fresh perspective and to model a different approach. And I'd check whether the schedule pressure is making them rush, because rushing an intermittent-failure investigation usually makes it slower.

**Possible follow-ups:**
- How would you decide when to step in and take over versus continuing to coach them?
- If the failure can't be reproduced on demand, how would you help them make progress anyway?