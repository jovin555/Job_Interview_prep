# debugging-failure-analysis — Day 59

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only when two things change at once: the enclosure is closed, and the unit is in its final mounting position. That points away from the analog signal chain itself and toward something mechanical, thermal, or grounding-related that the enclosure and mounting introduce. I'd start by separating those two variables rather than treating "assembled and installed" as one condition.

First, reproduce the offset with the board in the enclosure but sitting on the bench, then with the board out of the enclosure but physically mounted in the final position. If the offset follows the enclosure, I'm looking at mechanical stress on the board, a changed thermal environment, or a shield/cable routing change. If it follows the mounting position, I'm looking at grounding, chassis coupling, or a parasitic path through the mounting hardware.

For a consistent offset specifically, I'd suspect a DC-level mechanism rather than noise: mechanical stress on a strain-sensitive component (some ceramic capacitors and certain sensor packages shift value under flex), a reference or ground potential that changes when the board is tied to chassis ground through the mounting points, or a thermocouple-like effect at a connector. I'd measure the reference voltage and the analog ground at the ADC with a high-impedance meter in both states, and compare. A consistent offset with a stable reference usually means the signal return path or the sensor excitation has changed, not that the amplifier drifted.

I'd also check whether the mounting hardware creates a ground loop or a second return path that wasn't present on the bench. If the offset is small and repeatable, a differential measurement between the signal and its local return, taken at the ADC pins in both configurations, will usually localize it quickly.

**Possible follow-ups:**
- If the offset disappears when you loosen the mounting screws, what does that tell you, and how would you confirm it?
- How would you distinguish a mechanical-stress effect from a thermal effect if both change when the enclosure is closed?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a load-transient and impedance problem, not necessarily a regulator problem. The regulator may be perfectly capable of holding the rail under a slow load change, but the ripple appears when a fast, high-di/dt load hits the rail. The first thing I'd do is characterize the disturbance properly rather than just noting "excessive ripple": what's the amplitude, the frequency content, and the duration? Is it a transient dip-and-recovery, or a sustained oscillation? Those point to different mechanisms.

I'd measure at the load, not at the regulator output. Probing at the regulator's output capacitor can hide the voltage drop across the trace and via inductance between the regulator and the load. The right measurement is a short-ground-lead probe (or a proper tip-and-barrel connection) right at the load's power pins, with the ground referenced to the load's local ground. Long scope ground leads will pick up loop inductance and show ringing that isn't really there.

Then I'd look at the decoupling network between the regulator and the load. A high-di/dt load needs bulk capacitance close enough to supply charge before the regulator's control loop can respond, plus high-frequency ceramic decoupling right at the pins. If the bulk cap is far away, the trace inductance between it and the load turns into a voltage spike during the transient. I'd also check the regulator's loop stability — sometimes a load step excites a marginally stable control loop, and the "ripple" is actually ringing from insufficient phase margin.

Finally, I'd verify the load's own behavior. If the subsystem has a soft-start or slew-rate control, enabling it can reduce di/dt at the source. If not, adding local bulk capacitance and tightening the layout is the usual fix. I'd confirm the fix by re-measuring at the load under the worst-case switching condition, not just at idle.

**Possible follow-ups:**
- How would you tell whether the ripple is caused by the regulator's loop response or by the decoupling network's impedance?
- What would change in your approach if the disturbance were a sustained oscillation rather than a transient?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hardest part of this class of bug is that nothing in the system flags it, so the first job is to make the failure observable. I'd start by building a way to detect the error in real time rather than relying on offline review — for example, a cross-check against a redundant measurement, a plausibility model, or a comparison against a second sensor channel if one exists. Without a detector, I can't reproduce or count the events, and I'm debugging blind.

Once I can detect it, I'd characterize the error: is the wrong value a stale value (the previous reading), a bit-flipped version of the correct value, a value from the wrong channel, or a value that's simply outside the expected correlation with other signals? Each pattern points somewhere different. A stale value suggests a read that didn't complete or a buffer that wasn't refreshed. A bit flip suggests a data-integrity or memory issue. A wrong-channel value suggests an indexing or multiplexer bug.

I'd then instrument the path from the sensor to the stored value: the bus transaction, the raw ADC or sensor register contents, the conversion, and the value written to memory. If the raw reading is correct but the stored value is wrong, the bug is in the firmware's handling. If the raw reading itself is wrong, it's in the acquisition or the sensor interface. I'd log both the raw and the processed value with a timestamp and a sequence number so I can correlate an event with what else the system was doing at that moment.

A common root cause in this category is a race between an interrupt-driven update and a foreground read, where the foreground reads a partially updated multi-byte value. That produces plausible-but-wrong values that pass range checks. I'd look for any shared variable written in an ISR and read outside it without a proper critical section or atomic access.

**Possible follow-ups:**
- How would you design a plausibility check that catches this kind of error without generating false positives?
- If the error only appears after long runtimes, how would you accelerate reproduction without changing the system's behavior?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the productive move is to stop arguing about which is more likely and instead design a test that discriminates between them. The question isn't "which do we believe" — it's "what observation would be different under hypothesis A versus hypothesis B?" If I can find that observation, the investigation resolves itself. If I can't, that tells me the hypotheses aren't actually distinct, or I don't understand them well enough yet.

Practically, I'd write both hypotheses down explicitly, including the mechanism each one predicts and the evidence each one currently has. Then I'd look for the cheapest, fastest test that separates them — ideally one that can be run on existing hardware or data. I'd assign owners and a deadline for each test so the investigation doesn't drift. If the tests are expensive, I'd prioritize the one that, if it comes back negative, eliminates the most likely hypothesis.

I'd also be explicit with the team that holding two hypotheses open is not indecision — it's the correct state until the evidence separates them. What's not acceptable is implementing a fix for one hypothesis while pretending the other is ruled out. If schedule pressure forces a mitigation before root cause is confirmed, I'd frame it as a containment action, document that root cause is still open, and keep the discriminating test running in parallel.

If after the tests the evidence still doesn't separate them, I'd consider whether the two "causes" are actually one cause with two symptoms, or whether there's a third mechanism that explains both sets of evidence. That reframe often breaks the deadlock.

**Possible follow-ups:**
- How would you handle it if the discriminating test is too expensive or slow to run within the project timeline?
- What would you do if a senior stakeholder insists on picking one hypothesis and moving on?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, the system fails — usually means the bug lives in the interaction between components, not in any one component. Testing in isolation is the right instinct, but it can't find interaction bugs, so the engineer isn't failing; they're using a method that has a blind spot for this class of problem. I'd start by reframing that, because frustration often comes from feeling stuck when the method itself is the limitation.

I'd sit down with them and ask them to walk me through what they've established so far, not to re-verify it but to understand the boundary of what's been ruled out. Then I'd help them shift from component-level testing to system-level observation: what's different about the failing condition versus the passing condition? What's the smallest system configuration that still fails? Can we make it fail on demand, even if that means stressing it — temperature, load, timing, a specific sequence of operations?

The goal is to convert an intermittent failure into a reproducible one, because a reproducible failure is a solvable one. I'd suggest techniques like adding instrumentation to log the system state around the failure, running the system in a loop until it fails, or deliberately perturbing the conditions the failure seems to correlate with. I'd also encourage them to write down the current hypothesis and what would falsify it, so the debugging has direction rather than being a series of experiments.

On the human side, I'd make sure they know that asking for help after several days is the right call, not a failure. I'd pair with them for a session rather than taking the problem away, so they build the skill for next time. And I'd check whether the schedule pressure is coming from me or from elsewhere — if the timeline is genuinely tight, that's a reason to add resources or reprioritize, not a reason to pressure one person harder.

**Possible follow-ups:**
- How would you decide when to step in and take over versus continuing to coach?
- If the failure can't be made reproducible within the available time, what would you do next?