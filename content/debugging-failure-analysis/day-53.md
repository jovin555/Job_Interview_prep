# debugging-failure-analysis — Day 53

## Q1: How would you approach debugging a device that fails only when it is mounted in its final enclosure and installed in its operating position, but passes every test on an open bench?

**Answer:** This is a classic case where the bench setup is not a faithful model of the real system, so the first job is to figure out what the enclosure and mounting position actually change. The candidates are usually mechanical, thermal, or electromagnetic: the enclosure can alter airflow and therefore local temperature; mounting can introduce a new ground path or a new parasitic capacitance to a chassis; cable routing inside the enclosure can change loop areas and coupling; and the final position can bring the device near conductive or reflective surfaces that shift antenna behavior or stray coupling.

I would start by reproducing the failure in the assembled state and then bisecting the difference. A useful sequence: run the device open on the bench but with the enclosure placed loosely over it (no fasteners) to separate "enclosure present" from "enclosure closed and mounted." Then close it without mounting, then mount it without closing, and so on. Each step isolates one variable. If the failure appears only when the unit is fastened into its final position, that points at a mechanical or grounding change rather than the enclosure itself.

In parallel I would instrument the suspect nodes. If it is a measurement offset, I would measure at the analog front-end input with a high-impedance probe in both states and compare. If it is a communication or reset issue, I would look at the supply rails and the ground reference at the point of use, not at the regulator output — a ground shift between two boards or between a board and a chassis can be invisible at the supply but fatal at the signal. A current probe on the supply and a differential probe across the ground path often reveal whether the enclosure is adding an unintended return path.

The key discipline is to change one thing at a time and to keep a written log of which configuration fails. It is tempting to "fix" it by adding a ferrite or a capacitor, but that only helps if you understand what the enclosure changed. Once I have a hypothesis — say, a chassis ground loop or a thermal rise — I would confirm it with a targeted test: lift the ground path and see if the symptom moves, or add a thermocouple at the suspect component and correlate temperature with the failure.

**Possible follow-ups:**
- If the failure only appears when the unit is mounted on a metal surface, how would you distinguish a capacitive coupling effect from a ground-loop effect?
- How would you decide whether the fix belongs in the design or in the assembly/integration instructions?

## Q2: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it is only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hardest part of this class of bug is that nothing in the system considers it an error, so there is no fault flag to chase. The investigation has to start by making the invisible visible: I would add temporary instrumentation that logs the raw sensor value, the timestamp, the conversion result, and the state of any relevant control lines at the moment of each reading, so I can compare the "wrong but plausible" value against the raw data path.

The next step is to characterize the error statistically. Is the wrong value always off by a similar amount, or is it a single-bit corruption, or is it a stale value from a previous reading? Those three patterns point to very different causes. A consistent offset suggests a calibration or scaling bug, or a reference voltage that shifts under some condition. A single-bit flip suggests a memory or bus integrity issue. A stale value suggests a timing or handshake problem where the firmware reads the data register before the conversion is complete, or reads a buffer that was not updated.

I would then try to reproduce it under controlled conditions. Because it is intermittent, I would run the device in a loop with a known-good reference input and log every reading, then look for correlation with temperature, supply voltage, activity of other peripherals, or time since power-up. If the error correlates with, say, a motor or radio being active, that points at noise coupling into the analog path or a shared resource contention. If it correlates with temperature, that points at a component drifting or a timing margin shrinking.

A useful technique is to inject a known signal and compare the reported value against the expected value in real time, rather than reviewing offline. That turns a slow offline review into an immediate trigger, so I can capture the surrounding state at the moment of failure. I would also check the firmware's read sequence against the sensor's datasheet timing diagram carefully — a missing wait for the "data ready" flag, or reading a register that is double-buffered, is a common source of plausible-but-wrong values.

Finally, I would consider whether the error is in the measurement or in the reporting. If the raw conversion is correct but the stored or transmitted value is wrong, the problem is in the data handling, not the sensor. Splitting the path into "acquire," "convert," "store," and "transmit" and checking each stage with a known input is the fastest way to localize it.

**Possible follow-ups:**
- How would you design the logging so that it does not itself perturb the timing you are trying to observe?
- If the error only appears after long runtimes, how would you set up an accelerated test to reproduce it?

## Q3: You are debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a load-transient and power-integrity problem, so I would treat it as two questions: how big is the transient, and how well does the power delivery network respond to it? The fact that the ripple appears only when the subsystem switches tells me the disturbance is being injected by that subsystem's current draw, and the rail's response is inadequate somewhere between the regulator and the load.

I would start by measuring the transient properly. That means probing at the point of load with a short ground lead — a long ground clip on an oscilloscope probe will pick up loop inductance and show ringing that is not really on the rail. I would use a differential probe or a probe with a very short ground spring, and I would measure at the load's supply pins, not at the regulator output, because the impedance of the trace and vias between them is often where the problem lives. I would also measure the load current with a current probe or a shunt to see the shape and slew rate of the transient, since the rail's response depends on both the magnitude and how fast the current changes.

Once I have the waveform, I would break the response into frequency bands. The bulk capacitor handles the low-frequency portion, the ceramic decoupling handles the mid-frequency, and the regulator's control loop handles the slower correction. If the dip is a fast spike, the issue is likely insufficient high-frequency decoupling or too much inductance between the capacitor and the load. If the dip is a slower sag that recovers over tens of microseconds, the regulator's loop bandwidth or the bulk capacitance may be inadequate. If there is ringing, that points at a resonance between the output capacitance and the trace inductance, which can be damped with a small series resistance or a different capacitor combination.

I would also check the ground path. A transient current flowing through a shared ground return creates a voltage drop that appears as ripple at the load even if the regulator is doing its job. Measuring the ground at the load relative to the regulator ground, with a differential probe, will show whether the return path is contributing.

The fix depends on the diagnosis: more or better-placed decoupling, a lower-ESL capacitor, a layout change to shorten the loop, a regulator with higher loop bandwidth, or a soft-start or slew-rate limit on the switching subsystem to reduce the transient itself. I would verify the fix by re-measuring at the point of load under the worst-case load pattern, not just at the regulator.

**Possible follow-ups:**
- How would you determine whether the ripple is coming from the regulator's control loop or from the decoupling network?
- If the transient is caused by a motor or radio, would you address it at the source or at the rail, and why?

## Q4: You are leading a failure investigation and you have reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the temptation is to argue about which is more likely. I would instead reframe the problem as: what test would distinguish between them, and can we run it? The goal is to convert a debate into an experiment.

First I would write down both hypotheses explicitly, along with the evidence for and against each, and — critically — the prediction each one makes. If hypothesis A is true, what should we see that hypothesis B would not predict? If there is no observable difference between them, then either they are not really distinct, or we have not thought carefully enough about the mechanism. Making the predictions explicit usually reveals which test is most discriminating.

Then I would design the cheapest, fastest test that separates them. That might be a targeted measurement, a controlled experiment on a bench unit, a fault-injection test, or a review of field data with a specific filter. I would assign it to whoever is most able to run it, regardless of which hypothesis they favor, and I would set a clear criterion for what result would support which conclusion. This keeps the investigation evidence-driven rather than personality-driven.

If the two hypotheses are not mutually exclusive — which is common — I would consider whether both could be contributing, and whether one is a necessary condition and the other a trigger. In that case the investigation may need to establish the sequence rather than pick a single cause.

Throughout, I would keep the team focused on the shared goal: a defensible root cause with a corrective action that prevents recurrence. I would also be explicit about the cost of being wrong in each direction — a fix based on the wrong cause wastes time and may leave the real problem in the field — so the team understands why the extra test is worth it. If the schedule is tight, I would time-box the discriminating test and agree in advance what we do if it is inconclusive, so the investigation does not stall.

**Possible follow-ups:**
- What would you do if the discriminating test is inconclusive and the schedule does not allow further investigation?
- How would you document the two-hypothesis state so that a future engineer can pick up the thread?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they have been testing components in isolation and everything passes, but the system-level failure persists. They are frustrated and the schedule is tight. How would you approach this?

**Answer:** The first thing I would do is acknowledge that the approach they have taken is reasonable — testing components in isolation is a sensible first step — and that the fact that everything passes is itself useful information. The problem is not that they have been careless; it is that the failure lives at the system level, and isolated testing by definition cannot see it. Reframing it that way takes some of the frustration out of the situation.

Then I would help them change the question. Instead of "which component is broken," the question becomes "what is different about the system when it fails versus when it passes?" That means capturing the state of the whole system at the moment of failure: supply rails, ground references, timing between signals, temperature, and the sequence of events leading up to it. If the failure is intermittent, the priority is to make it reproducible or to instrument the system so that the failure is captured when it happens, rather than trying to reason about it after the fact.

I would sit down with them and go through what they have already ruled out, and look for the assumption that has not been tested. A common trap is assuming that because a component passes its own test, the way it is used in the system is correct — for example, a sensor that works on a bench but is read before its conversion is complete, or a signal that is fine in isolation but marginal when a neighboring trace switches. Another common trap is testing with a bench supply or a test harness that does not match the real power source or cabling.

I would also make sure they are not working in isolation themselves. Pairing them with someone who can look at the problem fresh, or asking them to walk me through their reasoning step by step, often surfaces the gap. And I would set a short, concrete next step — one experiment, with a clear expected outcome — so they have a way to make progress rather than continuing to search broadly.

On the schedule pressure: I would be honest that the timeline is tight, but explain that the fastest path is usually to stop guessing and get a measurement that discriminates. I would also consider whether to reassign part of the work or bring in another pair of hands, so the junior engineer is not carrying the whole investigation alone.

**Possible follow-ups:**
- How would you decide when to step in and take over versus letting them work through it?
- What would you do if the failure cannot be reproduced at all, and the only evidence is the field report?