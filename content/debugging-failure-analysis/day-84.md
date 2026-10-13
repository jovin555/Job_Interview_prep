# debugging-failure-analysis — Day 84

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key insight is that the offset appears only when two variables change together — mechanical assembly and physical mounting — so I'd treat this as a stimulus-coupling problem rather than a component tolerance problem. The bench harness typically provides a clean, short, well-referenced signal path; the assembled unit introduces a different ground reference, different cable routing, and mechanical stress on the PCB.

I'd start by separating the two variables. First, reproduce the offset with the board fully assembled but sitting on the bench in the same orientation as the bench test — if the offset appears, the enclosure itself is the culprit (mechanical stress on a solder joint or connector, changed thermal environment, or a shield/case now acting as an antenna or ground path). If it doesn't appear, the mounting position is the trigger, which points to grounding, chassis coupling, or a nearby field source.

Next, I'd measure the actual analog input at the ADC pin with a high-impedance probe while the unit is in the failing state, and compare it to the sensor output at the connector. That tells me whether the offset is introduced before the ADC (sensor, cabling, front-end gain/offset network) or after it (reference drift, ADC input leakage, firmware scaling). A consistent offset that tracks the assembly state usually means a reference or ground return path has changed — for example, a star ground point that's now shared with the chassis, or a shield that's tied to signal ground in one configuration and chassis ground in the other.

I'd also check for mechanical contributors: flexing of the board when screwed into the enclosure can shift a high-impedance node, crack a via, or change the seating of a connector. A quick test is to torque the mounting screws progressively and watch the offset — if it moves with torque, it's mechanical. If it's stable, I'd move to thermal: the enclosed unit runs warmer, and a front-end with a temperature-sensitive offset (input bias current, resistor TCR mismatch, reference tempco) will drift. I'd confirm by stabilizing the enclosure temperature and re-measuring.

Finally, I'd verify the reference and ground at the ADC with a differential probe to rule out a ground loop between the measurement setup and the device under test — a classic source of "offset only in the real installation" artifacts.

**Possible follow-ups:**
- If the offset tracks torque on the mounting screws, how would you narrow down which joint or node is responsible without destructive analysis?
- How would you distinguish a genuine front-end offset from a measurement artifact caused by your own probe grounding in the assembled unit?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a load-transient and power-distribution problem, so I'd approach it in layers: characterize the disturbance, localize where it originates, then determine why the decoupling or regulation isn't absorbing it.

First, I'd measure the ripple properly. Probing a switching rail with a standard ground lead picks up loop inductance and gives misleading results, so I'd use a short ground spring or a coaxial/pigtail probe right at the decoupling capacitor terminals, and measure differentially where possible. I'd capture the ripple both at the regulator output and at the load's input pins — the difference between those two points tells me whether the disturbance is generated at the source or coupled along the distribution path.

Then I'd characterize the transient itself: what's the amplitude, duration, and repetition rate, and does it correlate exactly with the subsystem's switching edges or with its enable/disable transitions? A dip synchronized with a motor or radio turn-on is an inrush/load-step event; ripple synchronized with a PWM or switching frequency is a control-loop or decoupling issue. That distinction drives everything downstream.

For a load-step event, I'd check the regulator's transient response against the load's actual current slew rate — if the load demands current faster than the regulator's loop can respond, the bulk and local decoupling have to supply the difference, and if their impedance is too high at the relevant frequency, the rail sags. I'd measure the impedance of the decoupling network (or reason about it from the cap values, ESR, and layout) and check whether the bulk cap is physically far from the load, whether the high-frequency caps have long via loops, and whether the ground return for the load shares impedance with the regulator's feedback reference.

I'd also rule out layout and grounding issues: a load whose return current flows through a shared ground trace will modulate the regulator's ground reference and appear as ripple. And I'd check whether the subsystem's own supply filtering is adequate — sometimes the fix is local to the aggressor, not the regulator.

The systematic principle is: don't change anything until you can point to the mechanism. Measure at the source, at the load, and at the reference, and the location of the largest disturbance tells you where to focus.

**Possible follow-ups:**
- How would you decide whether the fix belongs at the regulator (loop compensation, bulk capacitance) versus at the load (local decoupling, slew-rate limiting)?
- If the ripple is within the regulator's datasheet transient spec but still causes a downstream failure, how would you frame the problem?

## Q3: How would you approach a failure investigation where a device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline?

**Answer:** This is one of the harder classes of bug because there's no fault signal to trigger on — the system believes it's healthy. The approach has to shift from "catch the failure" to "make the failure observable and reproducible," then work backward from the corrupted value to its origin.

First, I'd establish what "wrong" means precisely. Is the value offset, scaled, stale, or a plausible value from a different channel or a previous sample? The pattern of the error is the strongest clue. A value that's plausible but wrong often means the data path delivered a valid-looking number that came from the wrong place — a buffer that wasn't refreshed, a channel that wasn't selected, a conversion that completed on stale input, or a value that was overwritten by a concurrent access.

Next, I'd add instrumentation that captures the raw data at each stage of the pipeline: the sensor output, the ADC conversion result, the value in the driver buffer, and the value as logged. Comparing these across a known-good and a known-bad event localizes where the corruption enters. If the ADC result is correct but the logged value is wrong, it's a firmware data-handling issue; if the ADC result itself is wrong, it's an acquisition or timing issue.

I'd then look for the classic mechanisms: a race between an interrupt-driven conversion and a foreground read (torn read of a multi-byte value), a DMA buffer that's read before the transfer completes, a channel multiplexer that switches before the previous conversion settles, or a shared buffer written by two contexts without protection. These produce exactly this symptom — a valid-looking value that's simply not the one that should be there.

Because the failure is intermittent and only caught offline, I'd also build a targeted stress test: run the acquisition at the fastest rate and under the same concurrent load as the field condition, log both the raw and processed values with timestamps, and let it run long enough to catch the event. Fault injection — deliberately delaying an interrupt, forcing a buffer collision — can confirm a suspected mechanism faster than waiting for it to occur naturally.

Finally, I'd make sure the fix is verified against the mechanism, not just the symptom: if it was a torn read, the fix is atomic access or a double-buffered handoff, and the test should demonstrate that the specific race can no longer produce a bad value.

**Possible follow-ups:**
- How would you design the logging so it doesn't itself perturb the timing and mask or create the bug?
- If the corrupted value is always plausible and never out of range, what does that tell you about where in the pipeline to look first?

## Q4: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The first thing I'd recognize is that the engineer isn't failing — they're using a method that works for deterministic bugs but doesn't fit an intermittent, system-level problem. Testing components in isolation proves the components are fine; it doesn't exercise the interactions where the failure actually lives. So my job is to help them change the question they're asking, not to take over.

I'd start by sitting down with them and asking them to walk me through what they've observed, not what they've concluded. Often the raw observations contain a pattern they've dismissed — a correlation with temperature, with a particular sequence of operations, with how long the unit has been running. I'd help them write down the failure conditions explicitly: what's the shortest path to reproduce it, even if it's rare, and what's different about the times it does versus doesn't occur.

Then I'd help them reframe from "which component is broken" to "what condition triggers the failure." That usually means building a way to observe the system while it's failing — logging, a debugger attached, a scope on the suspect signal — rather than testing pieces on the bench. If they can't reproduce it on demand, the next step is to make it more frequent: run it longer, stress it thermally, run it under the same concurrent load as the field, or add instrumentation to catch the state at the moment of failure.

I'd also be deliberate about morale. Being stuck for days is demoralizing, and the schedule pressure makes it worse. I'd normalize that intermittent system-level bugs are genuinely hard, acknowledge the work they've done (ruling out the components is real progress), and give them a concrete next step rather than a vague "keep at it." Pairing on the problem for an hour often unsticks it — not because I know the answer, but because a second perspective catches assumptions.

If the schedule truly can't absorb more open-ended debugging, I'd help them time-box: define what a good-enough interim mitigation looks like (a watchdog, a recovery path) while the root cause work continues, so the project isn't blocked on a single investigation.

**Possible follow-ups:**
- How would you tell the difference between an engineer who needs a method change and one who needs more resources or a different assignment?
- If the failure can't be reproduced at all, how would you guide them to make progress without a reproduction?

## Q5: How would you approach a failure investigation where a device's analog front-end is accurate at room temperature, but shows a growing offset error as the device warms up during continuous operation — and the offset returns to zero after the device cools down?

**Answer:** The reversibility is the most informative clue: a drift that fully recovers on cooling points to a temperature-dependent parameter, not a permanent damage mechanism. So I'd treat this as a thermal characterization problem and work from the outside in.

First, I'd quantify the relationship between temperature and offset. I'd instrument the unit with thermocouples or use a thermal camera to map where the heat actually is — the offset may correlate with the temperature of a specific component (the front-end amplifier, the reference, a resistor network) rather than the ambient or the enclosure. Plotting offset against the temperature of the suspect component, rather than against time, usually turns a messy curve into a clean line and tells me which part is responsible.

Then I'd reason about the mechanisms that produce a temperature-dependent offset in an analog front-end. The usual suspects are: input offset voltage drift in the instrumentation amplifier, input bias current drift interacting with source impedance, gain resistor TCR mismatch (which produces a gain error that can look like an offset at a fixed input), reference voltage tempco, and thermocouple effects at dissimilar-metal junctions in the signal path. Each has a distinct signature — for example, bias-current drift scales with source impedance, so it would change if I swapped the sensor for a low-impedance source; a reference tempco would shift the whole transfer function, not just the zero point.

I'd isolate the mechanism with targeted experiments: substitute a stable low-impedance source for the sensor to remove source-impedance effects, measure the reference directly over temperature, and if possible swap in a component with a tighter tempco to see whether the drift changes. Comparing the measured drift against the datasheet tempco of each candidate tells me whether the observed behavior is even within spec — sometimes the "failure" is a design that didn't budget for the real thermal environment, which is a design fix, not a component fix.

Finally, I'd consider whether the thermal environment itself is the problem: if a power component is heating the front-end more than expected, the fix might be thermal (layout, copper, airflow) rather than electrical. The corrective action should address the mechanism, and the verification should demonstrate the offset stays within budget across the full operating temperature range, not just at the two endpoints.

**Possible follow-ups:**
- How would you distinguish a genuine component tempco issue from a self-heating effect where the front-end's own power dissipation changes its temperature?
- If the drift is within every component's datasheet spec but still exceeds the system's error budget, how would you frame the root cause and the corrective action?