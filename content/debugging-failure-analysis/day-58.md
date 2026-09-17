# debugging-failure-analysis — Day 58

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only when two variables change together — the enclosure is closed and the unit is mounted. That points away from the analog signal chain itself and toward something mechanical, thermal, or grounding-related that changes with assembly and orientation.

I'd start by reproducing the condition in a controlled way and then peeling back one variable at a time. First, I'd measure the offset with the board on the bench, then with the board inside the open enclosure, then with the enclosure closed, then with the unit in its final mounting position. If the offset only appears at the last step, the mounting is implicated; if it appears as soon as the enclosure closes, it's likely thermal or a grounding/shielding change.

For a consistent offset rather than noise, I'd suspect a few things: a ground reference shift caused by the board now being tied to the enclosure or chassis at a different point, a mechanical stress on a component (a flexing PCB changing a resistor or capacitor value slightly), or a thermal gradient that develops once airflow is restricted. I'd measure the analog ground reference and the sensor excitation at the point of measurement, not just the output, to see whether the offset originates upstream or is introduced at the ADC. I'd also check whether the mounting hardware is creating an unintended ground loop or a second ground path.

If it's mechanical stress, a strain gauge or a simple flex test on the bench can confirm it. If it's thermal, a thermocouple or thermal camera on the front-end components while the enclosure is closed will show the gradient. The fix depends on the cause — a layout change to decouple the sensitive node from mechanical stress, a grounding revision, or a thermal path change — but the diagnosis has to come before any fix.

**Possible follow-ups:**
- How would you distinguish a grounding-related offset from a thermal one if both are plausible?
- If the offset is within the sensor's datasheet accuracy but still triggers a fault, how would you decide whether to fix the hardware or adjust the firmware threshold?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and power-distribution problem, and the first thing I'd do is separate the question of whether the regulator is failing to respond or whether the ripple is being coupled into the measurement or into a downstream node.

I'd start by measuring the rail right at the regulator output with a proper high-bandwidth probe and a short ground lead — a long ground clip will pick up switching noise and give a misleading picture. Then I'd measure at the load's decoupling capacitors, because the ripple seen at the load can be very different from the ripple at the regulator. If the ripple is large at the load but small at the regulator, the problem is the impedance between them — trace inductance, insufficient bulk capacitance, or a ground return that's shared with the switching subsystem.

Next I'd look at the switching event itself. Is the ripple synchronized with the subsystem's switching edges? If so, I'd check the load transient response: does the regulator's control loop recover quickly, or does it ring? I'd also check whether the subsystem's return current is flowing through a path that shares impedance with the sensitive rail's ground reference — a common-impedance coupling problem.

Practical steps: add temporary bulk capacitance close to the load to see if the ripple drops (confirming a PDN impedance issue), probe the ground at both ends to check for ground bounce, and look at the switching node of the subsystem to see if there's ringing or overshoot that's coupling back. If the ripple is differential-mode on the rail, it's a decoupling/PDN issue; if it's common-mode, it's a grounding or layout issue. The fix follows from which one it is — more or better-placed decoupling, a layout revision to separate the return paths, or a snubber on the switching node.

**Possible follow-ups:**
- How would you decide between adding bulk capacitance versus improving the high-frequency decoupling?
- What would you look for in the layout to confirm a shared ground-return path?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hardest part of this kind of bug is that nothing in the system flags it, so the investigation has to start with making the failure observable. I'd first try to characterize the error statistically: how often does it happen, is it correlated with time, temperature, operating mode, or a particular sensor, and is the wrong value always wrong in the same way (a fixed offset, a scale error, a stale value, a bit flip)?

Then I'd add instrumentation. If the firmware can log the raw ADC value alongside the processed value, that immediately tells me whether the corruption is in the analog domain, the conversion, or the processing. If the raw value is correct but the processed value is wrong, it's a firmware or math issue. If the raw value is wrong, it's analog or timing. If the value is stale — the same as the previous reading — it's a communication or timing issue where the read didn't actually complete but the firmware used the old buffer.

I'd also look at the timing of the read relative to other system activity. A plausible-but-wrong value often comes from reading a register while it's being updated, from a conversion that wasn't complete, or from a buffer that was overwritten by a higher-priority task. Checking the sensor's datasheet for conversion timing and any "data ready" signaling is important — if the firmware polls instead of waiting for the ready flag, it can read a partially updated value.

Finally, I'd consider whether the error is in the data path or in the interpretation. A value that's plausible but wrong could be a correctly read value that's being scaled or offset incorrectly under a specific condition — for example, a calibration constant that's loaded incorrectly at startup, or a unit conversion that's applied twice. The investigation has to keep both the signal chain and the software path in view until the evidence narrows it down.

**Possible follow-ups:**
- How would you design a test to distinguish a stale-value bug from a partially-updated-register bug?
- If the error only appears in the field and not on the bench, how would you make it reproducible?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the temptation is to argue about which is more likely. I'd try to reframe the problem so the team is deciding what evidence would distinguish them, rather than which one feels right.

The first step is to write down, for each hypothesis, what it predicts that the other does not. If both hypotheses predict the same observable behavior, then the current evidence can't separate them and we need a new experiment. If they predict different things — different failure rates under a specific condition, different signatures on a scope, different behavior when a variable is changed — then we design a test that discriminates between them.

I'd also look for a way to make the two hypotheses not mutually exclusive. In a lot of real failures, there's a primary cause and a contributing factor, and the team is split because each side is looking at a different part of the chain. Mapping the failure as a sequence — trigger, contributing condition, failure mechanism, observed symptom — often shows that both hypotheses are partially right and fit at different points in the chain.

On the process side, I'd set a decision point: agree on what test will be run, what result would support each hypothesis, and a deadline for the answer. That keeps the investigation moving and prevents it from becoming a debate. If the test is inconclusive, I'd escalate to a broader set of measurements rather than picking a side. The goal is to let the evidence decide, and to be explicit about what would change each person's mind.

**Possible follow-ups:**
- How would you handle it if the discriminating test is expensive or takes weeks to run?
- What would you do if the evidence ultimately supports a cause that's unpopular with part of the team?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, system fails — usually means the bug lives in an interaction, not in any single component. The junior engineer isn't wrong to test components, but the approach has hit its limit, and the most useful thing I can do is help them change the question they're asking.

I'd start by sitting down with them and asking them to walk me through what they've observed, not what they've concluded. Often the observations contain a clue that's been dismissed because it didn't fit the current hypothesis. I'd ask: when does it fail, when does it not, what's different between those cases, and what have you changed that didn't matter? That last question is often the most informative, because it shows what's been ruled out.

Then I'd help them build a minimal reproduction. Intermittent system-level failures are usually reproducible if you can find the right conditions — a specific sequence, a specific timing, a specific temperature, a specific combination of subsystems active. If it can't be reproduced on demand, the next step is to add instrumentation so that when it does happen, the system captures enough state to understand it. Logging, a scope trigger, or a firmware trace can turn a rare event into a recorded one.

I'd also normalize the emotional side. Being stuck for several days is normal in this kind of work, and it's not a sign of failure — it's a sign the problem is genuinely hard. I'd make sure they know the schedule pressure is mine to manage, not theirs to absorb, and that the priority is finding the cause, not looking like they're making progress. Pairing them with someone for a fresh perspective, or just having them explain the problem out loud, often breaks the logjam.

**Possible follow-ups:**
- How would you decide when to pull the engineer off the problem versus keep them on it?
- What would you do if the failure turns out to be in a subsystem owned by another team?