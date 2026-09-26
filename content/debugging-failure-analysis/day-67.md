# debugging-failure-analysis — Day 67

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only when two variables change together — mechanical assembly and final mounting. That points away from the analog signal chain itself and toward something the assembly process introduces: mechanical stress on a component, a changed thermal environment, a grounding path that only exists once the enclosure is closed, or a cable routing that shifts coupling.

I'd start by holding everything constant except one variable. First, reproduce the offset with the board in the enclosure but sitting on the bench, not yet mounted. If the offset appears there, the enclosure is the trigger; if it only appears after mounting, the mounting position is the trigger. That single split saves a lot of time.

If the enclosure is the trigger, likely causes are: a screw or standoff applying stress to a strain-sensitive component (a ceramic capacitor, a crystal, or the sensor itself), a connector that seats differently once the housing is closed, or a ground plane that now couples to the enclosure's conductive surfaces. I'd use a thermal camera and a multimeter to check whether the offset correlates with a temperature shift, and I'd flex the board gently with the unit powered to see if the offset moves — that's a fast way to confirm mechanical stress.

If the mounting position is the trigger, I'd suspect a ground loop or a changed reference potential — for example, the unit now sits on a grounded metal fixture that provides an unintended return path. I'd measure the analog reference and the signal ground relative to the chassis, and I'd try isolating the unit from the mounting surface to see if the offset disappears.

Throughout, I'd keep the measurement setup identical between bench and installed conditions — same probe, same reference point, same load — because a "consistent offset" can also be an artifact of where you're clipping your ground lead.

**Possible follow-ups:**
- How would you distinguish a mechanical-stress-induced offset from a thermal one if both are present?
- If the offset is caused by the enclosure providing an unintended ground path, what design changes would you consider?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and power-integrity problem, so I'd approach it as a question of where the ripple originates and where it propagates, not just "the regulator is bad."

First, I'd characterize the ripple properly. I'd probe directly across the decoupling capacitors at the load, not at the regulator output, using a short ground lead or a proper probe tip to avoid picking up radiated noise. I'd capture the ripple synchronized to the switching event so I can see whether it's a transient response (a dip and recovery) or a sustained oscillation (a control-loop or resonance issue). Those two have very different fixes.

If it's a transient response, the likely causes are insufficient bulk capacitance, high ESR in the bulk caps, or a regulator whose loop bandwidth is too slow to respond to the load step. I'd measure the load step's di/dt and compare it against what the output capacitance can supply before the regulator reacts. Adding or relocating bulk capacitance close to the load, or reducing the parasitic inductance between the regulator and the load, are the usual remedies.

If it's a sustained oscillation, I'd suspect a resonance between the output capacitor and the trace inductance, or a control-loop stability issue. I'd sweep the load current and look for a frequency that shifts with load — that's a strong hint of a loop issue rather than a fixed resonance.

I'd also check the return path. A high-current subsystem switching can inject noise into the ground plane, and if the analog or digital return shares a path with that current, the "ripple" may actually be ground bounce. Probing ground at two points simultaneously with a differential probe would confirm that.

Finally, I'd verify the switching subsystem itself — sometimes the ripple is a symptom of excessive inrush or a poorly snubbed switch node, and fixing the source is cheaper than filtering the symptom.

**Possible follow-ups:**
- How would you decide between adding bulk capacitance and improving the regulator's transient response?
- How would you measure ground bounce without introducing probe-induced error?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hardest part of this class of bug is that nothing in the system thinks it's failing. The value passes range checks, passes self-tests, and looks like real data. So the investigation has to start by making the failure observable, because right now the only detector is a human reviewing data after the fact.

First, I'd try to characterize the error statistically. Is the wrong value always off by a similar amount, or is it random? Does it correlate with a particular operating mode, temperature, time since power-up, or a specific sequence of events? Even a rough pattern narrows the search enormously. If the wrong value is always a plausible neighbor of the correct value, that suggests a single-bit error or a stale sample; if it's a completely different but valid reading, that suggests a buffer or indexing problem.

Second, I'd add instrumentation that captures the raw data path, not just the final value. I'd log the raw ADC reading, the timestamp, the sensor's status register, and the firmware's internal state at the moment of conversion. If the raw ADC value is correct but the reported value is wrong, the bug is in the firmware's processing or buffering. If the raw value is already wrong, the bug is in the acquisition path — timing, channel selection, or the sensor interface.

Third, I'd look for the classic causes of "plausible but wrong": a race condition where a buffer is read while it's being updated, a stale value returned because a conversion-complete flag was checked before the conversion finished, a channel multiplexer that hasn't settled, or an indexing error that reads the previous sample. These all produce values that look real.

Fourth, I'd consider whether the error is in the data path or in the data's interpretation — for example, a units or scaling error that only manifests under certain conditions.

The corrective action has to include a way to detect this class of error in the future, because a silent wrong value is worse than a flagged fault. That usually means adding a plausibility check that's tighter than the range check, or a cross-check against a redundant measurement.

**Possible follow-ups:**
- How would you design a plausibility check that catches wrong-but-in-range values without generating false positives?
- If the error turns out to be a race condition, how would you make it reproducible enough to verify a fix?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the temptation is to argue about which is more likely. I'd try to reframe the problem so the team is deciding what evidence would distinguish them, rather than which one they believe.

First, I'd write down both hypotheses explicitly, along with the predictions each makes. If hypothesis A is true, what should we see that we don't see if hypothesis B is true? That's the discriminating test. Often the team has been collecting evidence that supports both, which is why they're stuck — the useful evidence is the evidence that separates them.

Second, I'd look for a test that's cheap and fast, even if it's not definitive. A quick experiment that eliminates one hypothesis is worth more than a long debate. If both hypotheses predict the same observable behavior, I'd look for a condition where they diverge — a different temperature, a different load, a different unit — and test there.

Third, I'd consider whether the two hypotheses might both be true, or whether one is a contributing factor and the other is the trigger. In complex systems, "either/or" is often a false framing. If both are real, the corrective action needs to address both, and the investigation should say so.

Fourth, I'd be explicit about the cost of being wrong. If pursuing hypothesis A first is cheap and reversible, and pursuing B is expensive, that's a legitimate reason to test A first even if B is slightly more likely. I'd make that reasoning visible to the team so the decision doesn't feel arbitrary.

Finally, I'd set a decision point: if the discriminating test doesn't resolve it within a defined time or budget, we escalate to a more invasive test — for example, instrumenting a unit and running it to failure under controlled conditions. The goal is to avoid an open-ended investigation that drifts.

**Possible follow-ups:**
- How would you handle it if the discriminating test is destructive and you only have one field-returned unit?
- How would you document the investigation so the reasoning is traceable if the conclusion is later challenged?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — components pass in isolation, the system fails — is a strong signal that the bug lives in an interaction, not in a component. The junior engineer isn't wrong to test components; they've just exhausted what that approach can tell them. My job is to help them shift the frame without making them feel like the work was wasted.

First, I'd sit with them and ask them to walk me through what they've tried and what they've observed, not just what they've concluded. Often the useful clue is in an observation they dismissed as noise. I'd ask specifically: what changes when the failure appears? What's different about the failing case versus the passing case — temperature, timing, load, a specific sequence of operations?

Second, I'd help them move from component-level testing to system-level instrumentation. If the failure is intermittent, the priority is to make it observable and, if possible, reproducible. That might mean adding logging, using a logic analyzer to capture the bus around the failure, or running the system in a loop until it fails. A failure you can't reproduce is a failure you can't fix, so making it reproducible is often the real first step.

Third, I'd introduce the "divide and conquer" approach at the system level: instead of testing components, bisect the system's behavior. Disable subsystems, simplify the configuration, and see which change makes the failure disappear. That narrows the interaction that's causing it.

Fourth, I'd watch for the trap of changing multiple things at once. When someone is frustrated, they tend to try several fixes simultaneously, which destroys the ability to learn from the result. I'd encourage one change at a time, with a clear prediction of what should happen.

On the human side, I'd acknowledge that intermittent bugs are genuinely hard and that several days without progress is normal, not a sign of failure. I'd also make sure they're not working in isolation — pairing them with someone for an afternoon, or reviewing their notes with them, often breaks a stuck investigation. And I'd check whether the schedule pressure is realistic; if the bug is genuinely hard, the right move may be to communicate that upward rather than push the engineer harder.

**Possible follow-ups:**
- How would you decide when to pull the engineer off the investigation versus letting them continue?
- What would you do if the failure can't be reproduced at all in the lab?