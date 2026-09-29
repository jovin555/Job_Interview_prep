# debugging-failure-analysis — Day 70

## Q1: How would you approach debugging a device that passes every functional test on the bench but fails only when powered from its internal battery, at the same nominal voltage as the bench supply?

**Answer:** The first principle is that "same nominal voltage" is not the same operating condition, so I'd stop treating the bench supply as equivalent and start enumerating what actually differs between the two sources. A bench supply is typically a low-impedance, well-regulated source with a short, low-inductance cable and no protection circuitry in the path; a battery pack presents a different source impedance, a different transient response, and usually sits behind a protection IC, a fuel gauge, a fuse, and a connector. Any of those can turn a marginal design into a failing one without the DC voltage reading changing at all.

I'd structure it as a source-substitution experiment. Power the device from the bench supply but insert a series resistance and inductance that approximates the battery path, then re-run the failing scenario. If the failure appears, I've confirmed it's a source-impedance or transient-response problem rather than a voltage-level problem. If it doesn't, I'd look at what else the battery path adds — for example, a protection FET that drops out momentarily under inrush, a fuel gauge that communicates over I2C and shares a bus, or a connector with contact resistance that varies with mechanical stress.

Next I'd instrument the actual failure. I'd probe the rail at the point of load, not at the battery terminals, and capture with a scope set to trigger on the failure event rather than free-running. Load transients, inrush at power-up, and brief dips during radio transmit or motor activity are the usual suspects, and they're invisible to a DMM. I'd also check whether the device's own firmware is making a decision based on battery-specific telemetry — for instance, a low-battery threshold or a charge-state check that behaves differently when the gauge reports a real pack versus a bench supply.

The key discipline is to change one variable at a time and to reproduce the failure reliably before drawing conclusions. If I can't reproduce it on demand, I'd build a fixture that lets me switch between sources without disturbing anything else, so the only difference is the source itself.

**Possible follow-ups:**
- How would you decide whether the fix belongs in hardware or firmware?
- What would you measure to distinguish a source-impedance problem from a grounding problem?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and power-integrity problem, and the first thing I'd do is separate "the regulator is bad" from "the regulator is fine but the delivery network isn't." A regulator can meet its datasheet ripple spec into a resistive load and still produce large excursions when the load steps quickly, because the control loop has finite bandwidth and the output capacitance has to supply the transient current until the loop catches up.

I'd start by measuring properly. Ripple and transient measurements are easy to get wrong: a long ground lead on the probe picks up loop inductance and shows ringing that isn't really there, so I'd use a short ground spring or a proper tip-and-barrel connection, and probe directly across the output capacitor at the load, not at the regulator output pin. I'd capture the switching node, the output rail, and the load current simultaneously so I can correlate the ripple with the actual current step.

Then I'd characterize the transient itself: how fast is the current step, how large, and how often? That tells me whether I'm looking at a bulk-capacitance problem (slow, large droop), a high-frequency decoupling problem (fast edge, high-frequency ringing), or a loop-stability problem (ringing that persists after the step and decays slowly). Each points to a different fix — more bulk capacitance, better high-frequency decoupling and layout, or compensation and loop tuning.

I'd also check the obvious physical causes before redesigning anything: is the high-current subsystem's return current sharing a path with the sensitive rail's ground reference? Is there a ferrite or a narrow trace between the regulator and the load that adds impedance? Is the load actually drawing more current than the design assumed? Sometimes the "ripple" is really ground bounce on the measurement, and the fix is a layout or grounding change rather than more capacitance.

**Possible follow-ups:**
- How would you tell the difference between a loop-stability issue and a decoupling issue from the scope trace alone?
- What layout changes would you prioritize if you couldn't add more capacitance?

## Q3: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The fact that the offset appears only after assembly and installation tells me the electrical circuit is probably fine and something about the mechanical, thermal, or grounding environment is changing the measurement. I'd treat the enclosure and mounting as part of the circuit, because at the analog front-end level they usually are.

I'd start by reproducing the offset and then systematically removing variables. First, does the offset appear with the enclosure closed but the unit still on the bench? If yes, it's an enclosure effect — mechanical stress on the PCB, a cable routing change, a shield or metal part coupling into the front-end, or a thermal change from reduced airflow. If it only appears in the final mounting position, it's likely an installation effect — a ground reference that changes, a mounting screw that ties the board to a chassis at a different potential, or a nearby conductor that couples in.

For a consistent offset specifically, I'd look at things that shift a DC operating point rather than add noise: thermoelectric voltages at dissimilar metal junctions, a strain-induced change in a resistor or a solder joint, a reference voltage that shifts with temperature, or a ground offset between the sensor return and the ADC reference. A consistent offset is a strong hint that something is biasing the signal rather than corrupting it.

I'd measure the front-end with the enclosure open and closed, using the same instrument and the same reference, and I'd log temperature at the same time. If the offset tracks temperature, I'd use a thermal camera or a thermocouple to find which component is drifting. If it tracks mechanical state, I'd probe the board with a non-conductive tool to see if flexing changes the reading. The goal is to convert "it fails when assembled" into a specific physical mechanism before proposing any fix.

**Possible follow-ups:**
- How would you distinguish a thermal offset from a mechanical-stress offset?
- What would you check first if the offset only appeared after the unit was mounted on a metal surface?

## Q4: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** This is one of the harder classes of bug because the system's own validation isn't catching it, so I can't rely on the device to tell me when it's wrong. The first thing I'd do is define what "wrong" means precisely — is the value offset, scaled, stale, or from the wrong channel? The pattern of the error usually points at the mechanism, and I can't see the pattern until I've characterized it.

I'd pull the offline data and look for structure: does the error correlate with time since power-up, temperature, a particular operating mode, a specific sensor, or a particular sequence of events? Does it happen once per session or repeatedly? Is the wrong value always the same wrong value, or does it vary? A value that's consistently off by a fixed amount suggests a calibration or scaling issue; a value that's stale suggests a read that didn't complete but wasn't flagged; a value that's plausible but wrong in a random way suggests a data-integrity problem like a bit flip or a buffer overwrite.

Then I'd try to reproduce it under controlled conditions, because an intermittent bug that only shows up in field data is very hard to fix confidently. I'd add instrumentation — logging the raw ADC value, the timestamp, the sensor status register, and the firmware's internal state at the moment of the read — so that when it happens again I can see whether the sensor returned a bad value or the firmware mishandled a good one. That distinction is the fork in the road: sensor-side versus firmware-side.

I'd also review the code path for the read itself, looking for the usual suspects: a shared buffer that another task can modify, a read that isn't atomic with respect to an interrupt, a conversion that assumes a fixed timing, or a retry loop that returns the previous value on failure without flagging it. In my experience, "plausible but wrong" is often a stale-data or race-condition problem rather than a sensor problem, because a genuinely bad sensor reading usually trips a range check.

**Possible follow-ups:**
- How would you add instrumentation without changing the timing behavior you're trying to observe?
- If the error only appears in the field and never on the bench, how would you decide when you have enough evidence to act?

## Q5: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the temptation is to argue about which is more likely, and that argument rarely resolves anything because both sides are reasoning from the same incomplete evidence. I'd reframe the question from "which is more likely?" to "what observation would distinguish them?" That's the move that breaks the tie — not more debate, but a test that produces different results depending on which hypothesis is true.

Concretely, I'd write down both hypotheses and, for each, the predictions they make: if hypothesis A is correct, we should see X and not Y; if hypothesis B is correct, we should see Y and not X. Then I'd look for the cheapest, fastest test that lands on that fork. Sometimes it's a targeted measurement, sometimes it's a controlled experiment on a known-good unit, sometimes it's a review of manufacturing or field data that one hypothesis predicts and the other doesn't. If no such test exists yet, that itself is useful information — it tells me the investigation is missing a piece of evidence, and I'd go get it rather than pick a side.

I'd also be explicit with the team about the process, because the split is often as much about ownership and ego as about evidence. I'd make it clear that we're not voting on a root cause; we're designing an experiment to let the data decide. That takes the pressure off individuals to defend a position and puts the focus on the next measurement. If the schedule is tight, I'd time-box the discriminating test and agree in advance what result would close each branch.

If, after a genuine effort, the evidence still can't separate the two, I'd be honest about that rather than force a conclusion. I'd document both hypotheses, the evidence for each, and the test that would resolve it, and I'd recommend a corrective action that's robust to either cause if one exists — or a monitoring plan to catch the failure if it recurs. What I would not do is declare a root cause the evidence doesn't support just to close the investigation, because a wrong root cause leads to a wrong fix and the failure comes back.

**Possible follow-ups:**
- How would you handle it if the discriminating test is expensive or slow and the schedule won't allow it?
- How would you keep a senior engineer who's committed to one hypothesis engaged rather than defensive?