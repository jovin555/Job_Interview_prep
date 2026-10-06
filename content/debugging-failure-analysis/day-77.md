# debugging-failure-analysis — Day 77

## Q1: How would you approach debugging a device that fails only when it is powered from its internal battery, but passes every test when powered from a bench supply at the same nominal voltage?

**Answer:** The key insight is that "same nominal voltage" is not the same as "same source." A bench supply is an ideal-ish source with low output impedance, fast transient response, and no current limit unless you set one; a battery has finite source impedance that rises with age and state of charge, a different transient response, and a voltage that sags under load. So the first move is to stop treating the two as interchangeable and instead characterize the difference.

I'd start by instrumenting the battery rail itself — not the bench rail — with a scope probe at the point of load, using a short ground lead or a proper probe tip, and look at the rail during the exact operating condition that triggers the failure. What I'm hunting for is a transient: a dip during a load step (radio transmit, motor start, flash write, display backlight), a slow droop over time, or high-frequency noise that the bench supply's bulk capacitance was quietly absorbing. I'd also measure the battery's internal resistance indirectly by watching the voltage step under a known load, and check the connector and any series protection (fuse, ideal-diode, PTC) for added resistance.

In parallel I'd check the firmware side: does the firmware read battery voltage and change behavior — brownout detection thresholds, low-power mode entry, clock switching, peripheral enabling — based on that reading? A firmware path that only executes on battery power is a classic reason a device "only fails on battery." I'd also verify that the brownout reset threshold and the regulator's dropout voltage are not marginal at the battery's low end.

The discipline here is one variable at a time: reproduce on battery, capture the rail, then reproduce on bench supply with a series resistor added to emulate battery impedance. If the failure follows the added impedance, you've localized it to source impedance rather than the battery itself.

**Possible follow-ups:**
- How would you distinguish a brownout-induced reset from a firmware bug that only triggers on battery?
- What would you do if the failure only appears on a battery that has been in the field for a while, not a fresh one?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a load-transient and loop-stability problem, and the first thing I'd do is separate "the regulator is misbehaving" from "the measurement is lying to me." Probing technique matters enormously here: a long ground lead on a scope probe picks up switching noise and loop area, and it's easy to "measure" ripple that isn't really on the rail. I'd re-probe with a short ground spring or a coaxial tip right at the output capacitor, and confirm the ripple is real before chasing it.

Assuming it's real, I'd characterize it properly: what is the ripple frequency — is it at the regulator's switching frequency, at the load's switching frequency, or at some beat between them? Is it a transient dip that recovers, or a sustained oscillation? A sustained oscillation that appears only under load often points to a control-loop stability issue — insufficient output capacitance, wrong ESR, or a compensation network that was tuned for light load. A transient dip that recovers points more toward bulk capacitance and transient response.

I'd then look at the load itself: how fast is the current step, and how large? If the subsystem switches a large current in a few microseconds, the regulator's loop bandwidth may simply be too slow to respond, and the bulk capacitor has to supply the charge until the loop catches up. That's a capacitance and ESR question, not a regulator question. I'd also check the layout — is the load's return current sharing a path with the regulator's feedback node? A ground return that couples switching current into the feedback divider will produce exactly this symptom.

The systematic approach: measure the load current step with a current probe, measure the rail response at the load, and then vary one thing at a time — add bulk capacitance, change the feedback tap point, adjust compensation — to see which one moves the symptom. That tells you whether you're fighting the loop, the bulk network, or the layout.

**Possible follow-ups:**
- How would you tell the difference between a loop-stability problem and a bulk-capacitance problem without a network analyzer?
- What layout changes would you consider if the ripple correlates with the load's return current path?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** This is one of the harder classes of bug because there's no alarm, no fault code, and no obvious trigger — the system thinks it's healthy. The first thing I'd do is resist the urge to guess at the sensor and instead build a way to catch the event in the act. That usually means adding instrumentation: a timestamped raw-value log at the point where the sensor data enters the firmware, alongside the processed value, so I can see whether the corruption happens at the sensor interface, in the processing pipeline, or in the storage/transmission path.

The "plausible but wrong" characteristic is a strong clue. If the value were out of range, I'd suspect a communication error or a sensor fault. If it were stuck or zero, I'd suspect a read failure. Plausible-but-wrong suggests either a stale value being reused (the read failed silently and the firmware kept the last good value), a scaling or unit conversion applied twice or not at all, a race condition where a buffer is read while it's being updated, or a data-type issue — a signed/unsigned mix-up, an overflow, or a fixed-point scaling error that only manifests at certain values.

I'd also look at the timing: does the error correlate with a specific operating mode, a specific sensor, a specific firmware task priority, or a specific time since boot? If it correlates with a task that runs concurrently with the sensor read, that points to a race. If it correlates with temperature or supply voltage, that points to an analog or timing marginality. If it correlates with nothing obvious, I'd add a checksum or sequence counter to the sensor data path so I can detect the corruption at the moment it happens rather than weeks later.

The broader principle is that a silent data-integrity failure needs a detection mechanism before it needs a fix. Without a way to catch it in the act, you're guessing.

**Possible follow-ups:**
- How would you design the logging so it doesn't itself perturb the timing you're trying to observe?
- If the corruption turns out to be in the storage path rather than the sensor path, how would your approach change?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** The first thing I'd do is reframe the situation: the goal isn't to pick a winner, it's to find a test that distinguishes between the two hypotheses. If both are supported by partial evidence, then the evidence so far is consistent with both — which means I haven't yet found the observation that separates them. That's a gap in the investigation plan, not a failure of the team.

I'd start by writing down, for each hypothesis, what it predicts that the other does not. If hypothesis A is true, what should I see that I wouldn't see if B were true? That prediction is the discriminating test. Sometimes it's a measurement — a specific node's behavior under a specific condition. Sometimes it's a controlled experiment — disable one subsystem and see if the failure persists. Sometimes it's a statistical argument — if A were true, the failure rate should scale with X, and it doesn't.

If no discriminating test is immediately available, I'd look at whether the two hypotheses are actually independent or whether one is a subset of the other. Often what looks like two root causes is really one root cause with two contributing factors, and the fix needs to address both. In that case, the right move is to stop treating it as either/or and instead characterize the interaction.

On the team dynamics side, I'd be explicit that we're not voting on the answer — we're designing the experiment that settles it. That takes the ego out of it. I'd assign one person to try to falsify hypothesis A and another to try to falsify hypothesis B, and set a time box. If after the time box neither is falsified, we escalate to a more invasive test — instrumented units, fault injection, or a controlled field trial — rather than continuing to argue.

**Possible follow-ups:**
- What would you do if the discriminating test is expensive or would delay the project significantly?
- How would you handle it if one team member has significantly more experience and is convinced their hypothesis is correct?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, system fails — is a strong signal that the problem is in the interaction between components, not in any one component. That's a hard thing to see when you're deep in it, and it's a very common place for a junior engineer to get stuck, because the instinct is to keep testing the same components more carefully rather than to change the level of abstraction.

My first move would be to sit down with them and ask them to walk me through what they've tried and what they've ruled out. Not to audit them, but to understand the shape of the problem. Often the act of explaining it out loud surfaces the assumption they haven't questioned. I'd listen for phrases like "the power supply is fine" or "the firmware is fine" — those are the assumptions worth re-examining at the system level.

Then I'd help them reframe: instead of testing components, let's characterize the failure. When does it happen? How often? What's the shortest path to reproduce it? What's the longest? Does it correlate with temperature, time since boot, a specific sequence of operations, a specific unit? An intermittent failure that can't be reproduced on demand is very hard to debug, so the first goal is to make it reproducible — even if that means running a stress loop for hours.

I'd also introduce them to a technique they may not have tried: divide the system in half and determine which half the failure lives in. If you can swap a board, disable a subsystem, or substitute a known-good module, you can bisect the system rather than testing components one by one. That's usually much faster.

On the morale side, I'd be careful not to take the problem away from them — that's demoralizing. Instead I'd work alongside them, give them a concrete next step, and check in regularly. The message is "this is a hard problem, you're not failing, let's change the approach together." And I'd make sure they know that asking for help earlier is a strength, not a weakness.

**Possible follow-ups:**
- How would you decide when to step in and take over versus continuing to coach?
- What would you do if the junior engineer's approach is fundamentally sound but they just need more time?