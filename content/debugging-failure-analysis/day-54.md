# debugging-failure-analysis — Day 54

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only when two variables change together: the enclosure is closed and the unit is mounted. That points away from the analog signal chain itself (which is proven good on the bench) and toward something the mechanical configuration introduces — grounding, shielding, mechanical stress, or thermal environment.

I'd start by separating those two variables. Test the board in the open enclosure but unmounted, then closed but unmounted, then closed and mounted. If the offset only appears when mounted, the mounting hardware is implicated — a screw compressing a PCB near a strain-sensitive component, a mounting boss altering the ground return path, or a chassis connection changing the reference potential. If it appears as soon as the enclosure closes, I'd look at shielding and grounding: does the enclosure connect the analog ground to chassis at a point that creates a ground loop, or does closing it change the coupling between the analog front-end and a switching source?

For a consistent offset specifically, I'd suspect a reference or bias issue rather than noise. I'd measure the analog reference and the front-end bias point in both configurations with a high-impedance probe, and check whether the offset tracks a change in the reference, the sensor excitation, or the amplifier's input bias. I'd also check for mechanical stress on the sensor or its connector — a cable routed differently when the enclosure closes can load a bridge sensor or shift a connector contact resistance.

Throughout, I'd keep it to one change at a time: open/closed, mounted/unmounted, harness vs. real cable, and log the offset for each. That isolates which single variable correlates with the fault before I start theorizing about mechanism.

**Possible follow-ups:**
- If the offset appears only when mounted, how would you determine whether it's mechanical stress versus a grounding change?
- How would you confirm the offset is in the analog domain and not introduced by the ADC or firmware scaling?

## Q2: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the trap is letting the team argue about which is more likely instead of designing a test that separates them. My job as lead is to convert the debate into an experiment.

First, I'd restate both hypotheses precisely and, for each, write down the specific observation that would be true if it were the cause and false if it weren't. That usually reveals that the two hypotheses make different predictions somewhere — even if the current evidence doesn't distinguish them. If they genuinely predict the same thing under all conditions, they may be two descriptions of the same failure, and I'd say so.

Then I'd design the cheapest, fastest test that discriminates between them. Often that means reproducing the failure with one variable forced to each extreme — for example, if one hypothesis is thermal and the other is timing, run the unit hot-but-idle and cold-but-loaded. I'd assign owners, set a time box, and commit in advance to what result would confirm or eliminate each hypothesis, so nobody can reinterpret the data after the fact.

If the discriminating test is expensive or slow, I'd run both hypotheses' fixes as controlled experiments in parallel on separate units, but I'd be explicit that a fix that makes the symptom disappear is evidence, not proof — I'd still want the mechanism confirmed before closing. I'd also keep a written decision log so the reasoning is traceable, which matters for a regulated device where the corrective action has to be justified.

The leadership part is making it safe to be wrong: I'd frame it as "the evidence decides," not "my hypothesis wins," and I'd be willing to kill my own preferred theory first to set the tone.

**Possible follow-ups:**
- What would you do if the discriminating test is inconclusive and the schedule won't allow more investigation?
- How do you prevent a "split team" from becoming a personal conflict rather than a technical disagreement?

## Q3: How would you approach debugging a device that fails only when two subsystems are active at the same time — for example, a wireless radio transmitting while a high-current actuator is switching — but neither subsystem alone produces any failure?

**Answer:** A failure that requires two conditions simultaneously is almost always a shared-resource or coupling problem: the two subsystems are competing for something — current, ground reference, timing, or a shared bus — and the failure only appears when both are stressing it at once.

My first move is to characterize the coupling. I'd instrument the shared resources: the supply rail feeding both subsystems, the ground return, and any shared clock or bus. I'd trigger a scope on the actuator switching edge and look at what happens to the radio's supply and ground during that event, and vice versa. If the radio's supply dips or its ground bounces when the actuator switches, that's a power-integrity coupling. If the actuator's control signal glitches when the radio transmits, that's likely conducted or radiated EMI coupling into a high-impedance node.

I'd then try to break the coupling one path at a time. Add local bulk capacitance at the radio to see if a supply dip is the mechanism. Improve the ground return or add a star point to see if it's a shared-impedance issue. Temporarily move or shield the antenna to test radiated coupling. Each change tests a specific mechanism rather than just "trying things."

I'd also check timing: if the two subsystems share an interrupt controller, a DMA channel, or a bus, the failure could be a firmware-level contention that only manifests when both are active. In that case the scope shows clean analog signals but the failure persists, which redirects me to the firmware.

The discipline is to keep the two conditions independently controllable so I can turn each on and off and watch the coupling directly, rather than trying to reason about it from the symptom alone.

**Possible follow-ups:**
- If the coupling turns out to be radiated rather than conducted, how would you confirm that and what would you change?
- How would you decide whether the right fix is at the hardware level or the firmware level?

## Q4: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** This is one of the harder classes of bug because every automated check passes — the value is in range, the self-test is satisfied, and the system has no reason to flag it. The failure is silent, so the investigation has to start by making it visible.

First I'd try to reproduce it under instrumentation. If I can log raw sensor data alongside the processed value, I can catch the moment the value diverges and see whether the error is in the acquisition, the conversion, or the processing. If I can't reproduce on demand, I'd add targeted logging in the field or in a long-duration test to capture the raw and processed values together, so the next occurrence is diagnosable.

Then I'd reason about what "plausible but wrong" implies. It rules out gross faults like a disconnected sensor or a saturated ADC. It's consistent with a stale sample (the firmware read an old value), a race condition (the value was updated mid-read), a scaling or calibration error that only triggers under certain conditions, or a single-bit corruption in the data path. I'd check each: does the wrong value match a previous reading (stale)? Does it correlate with a concurrent operation (race)? Does it appear only at certain temperatures or after certain sequences (calibration drift)?

I'd also look at the data path end to end — sensor, front-end, ADC, DMA, buffer, processing, storage — for places where a value could be read while it's being written, or where a buffer could be partially updated. A double-buffered or atomic read is the usual fix for that class.

The key is that because the failure is silent, the investigation depends on improving observability first. Without a way to see the raw value at the moment of the error, I'm guessing.

**Possible follow-ups:**
- How would you design the logging so it doesn't itself perturb the timing and hide a race condition?
- If the wrong value matches a previous reading, how would you distinguish a stale-read bug from a legitimate repeated measurement?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, the system fails — usually means the bug lives in the interaction between components, not in any one of them. Testing parts in isolation can't find an interaction bug, so the engineer isn't failing; the method has hit its limit. I'd say that explicitly, because it reframes the frustration as a method problem rather than a competence problem.

I'd sit down with them and ask them to walk me through what they've ruled out and how. That does two things: it respects the work they've done, and it often surfaces an assumption they haven't tested. Then I'd help them shift from component-level testing to system-level observation: what changes at the moment of failure? Can they reproduce it at all, even rarely? What's the shortest path to a reproduction?

If it's truly intermittent, I'd help them build observability — logging, a trigger on the failure condition, a way to capture state at the moment it happens — so the next occurrence yields data instead of just a symptom. I'd also suggest they stop changing things and start measuring, because a week of "try this, try that" without a reproduction tends to add variables rather than remove them.

On the schedule pressure, I'd be honest: a bug that isn't understood can't be reliably fixed, and a rushed fix that masks the symptom often returns. I'd help them time-box the investigation and set a checkpoint, and I'd offer to pair with them or take a fresh look myself, since a second perspective often breaks a stall. The goal is to get them unstuck and keep them engaged, not to take the problem away from them.

**Possible follow-ups:**
- How would you help them build a reproduction when the failure only happens every few days?
- If the schedule genuinely can't absorb more investigation, how would you decide between a targeted workaround and continuing the root-cause work?