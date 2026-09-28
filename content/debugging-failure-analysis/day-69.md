# debugging-failure-analysis — Day 69

## Q1: How would you approach debugging a device that passes every functional test on the bench but fails only when powered from its internal battery, at the same nominal voltage as the bench supply?

**Answer:** The first principle is that "same nominal voltage" is not the same electrical environment, so I'd treat the bench supply and the battery as two different sources and enumerate what actually differs between them. A bench supply is typically a low-impedance, well-regulated source with a short, thick cable and a large output capacitance; a battery pack presents a different source impedance, a different transient response, and often a protection circuit (PCM/BMS) in series that can current-limit or briefly disconnect under load steps. So the failure is likely tied to source dynamics rather than steady-state voltage.

I'd start by instrumenting the battery rail at the point of load with a scope on a fast timebase, triggering on the failure event, and comparing the transient behavior against the bench case. Key things to look at: load-step response (does the rail sag or ring when a subsystem switches on?), inrush current at power-up or at mode transitions, and whether the protection FET in the pack is momentarily opening. I'd also check the battery's internal resistance and the connector/contact resistance — a marginal contact can look fine at DC but drop under pulsed load.

Then I'd try to reproduce the failure on the bench by deliberately degrading the source: add series resistance to emulate battery ESR, reduce the bulk capacitance, or use a source-measure unit with programmable output impedance. If the failure reproduces with a "battery-like" source, I've isolated the variable to source impedance/transient response rather than the battery itself. From there it's a normal divide-and-conquer: which rail collapses first, which subsystem is switching at that moment, and whether the fix is more bulk capacitance, a softer startup ramp, or a layout/decoupling improvement.

**Possible follow-ups:**
- How would you distinguish a brownout caused by source impedance from one caused by a firmware-controlled load transient?
- If the protection FET in the pack is the culprit, how would you confirm that without opening the pack?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-induced power integrity problem, and the key is to separate "the regulator is bad" from "the delivery network can't supply the transient." I'd first characterize the ripple properly: probe at the load with a short ground lead (or a proper coax/pigtail probe) right across the decoupling capacitor, not at the regulator output, because the ripple you care about is what the load actually sees. I'd capture the switching event on a fast timebase and look at the shape — is it a high-frequency ring (inductance in the delivery path), a slow sag (insufficient bulk capacitance or regulator loop bandwidth), or a periodic dip synchronized with the subsystem's PWM?

Next I'd measure the load current transient itself, ideally with a current probe or a shunt, to quantify di/dt. That tells me whether the problem is the magnitude of the step or the speed of the step. If it's a fast step, the culprit is usually parasitic inductance between the bulk cap and the load — the fix is placement, not more capacitance. If it's a slow sag, the regulator's transient response or bulk capacitance is the issue.

I'd also check the regulator's stability: a load step can push a marginally compensated loop into oscillation, which shows up as ringing that only appears under dynamic load. And I'd verify the feedback sense point — if it's sensing at the wrong node, the regulator is regulating the wrong voltage. The systematic approach is: measure at the load, quantify the transient, then decide whether the fix is layout (reduce loop area, move caps), component selection (lower ESR, higher loop bandwidth), or control (soft-start the load, add slew-rate limiting).

**Possible follow-ups:**
- How would you tell the difference between a decoupling problem and a regulator loop stability problem from the scope trace alone?
- What would you change first if the ripple frequency matches the subsystem's switching frequency exactly?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hardest part of this class of bug is that there's no fault flag to trigger on, so the first job is to make the failure observable. I'd start by adding instrumentation that captures the raw data path — the ADC reading, the timestamp, the sensor's status register, and the value the firmware computed — so that when a bad value is reported, I have the full context rather than just the final number. If the device has enough RAM or non-volatile storage, a rolling log of the last N samples with their metadata is invaluable.

Then I'd think about where a "plausible but wrong" value can come from. Candidates include: a stale reading (the sensor was read before it finished converting, or a previous value was reused), a scaling/calibration error that only manifests in a particular range, a race condition where the value is read while it's being updated, a communication error that corrupted a bit but still landed in a valid range, or a sensor self-test that passed but the sensor was in a marginal state. Each of these has a different signature, so I'd design the instrumentation to distinguish them — for example, log the sensor's "data ready" flag and the raw bytes on the bus, not just the parsed value.

I'd also try to reproduce it under controlled conditions: run the device through the operating envelope (temperature, supply voltage, sample rate, concurrent activity) and see if the error rate changes. If it correlates with a specific condition, that narrows the field. Finally, I'd check the data path end-to-end against a known-good reference — feed a precision source and compare the reported value to the expected value across the full range, not just at a few points, because a plausible-but-wrong error often hides in a specific segment of the transfer function.

**Possible follow-ups:**
- How would you design the logging so it doesn't itself perturb the timing you're trying to observe?
- If the error only appears in the field and never on the bench, how would you decide what to instrument before shipping a diagnostic build?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** The first thing I'd do is reframe the situation: having two plausible hypotheses is not a failure of the investigation, it's the normal state before you have a discriminating test. The team being split is actually useful, because each camp has usually accumulated evidence for their view — the problem is that the evidence so far doesn't distinguish between the two. So my job is to design a test that gives a different result depending on which hypothesis is true.

I'd start by writing down, for each hypothesis, what it predicts that the other does not. If both hypotheses predict the same observable behavior, then they're not really competing explanations — they may be two contributing factors, or one may be a symptom of the other. If they do predict different things, I'd look for the cheapest, fastest experiment that separates them: a targeted measurement, a controlled perturbation, or a swap test. I'd assign owners and a deadline, and make clear that the goal is not to prove one side right but to eliminate one hypothesis.

If the discriminating test is expensive or slow, I'd consider running both in parallel, but I'd be explicit about what each is testing and what result would change our mind. I'd also guard against the trap of "the most likely cause" being treated as "the confirmed cause" — in a medical device context, an unconfirmed root cause that leads to a corrective action is a regulatory and safety risk. If we genuinely can't discriminate in the time available, I'd document both hypotheses, the evidence for each, and the residual risk, and propose a containment action that's robust to either cause while the investigation continues. That keeps the project moving without pretending we've found something we haven't.

**Possible follow-ups:**
- How would you handle it if the discriminating test is destructive and you only have one returned unit?
- What would you do if the team's split is partly driven by seniority or personality rather than evidence?

## Q5: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The fact that the offset appears only after assembly and installation tells me the variable is something mechanical or environmental that the bench setup doesn't reproduce — so I'd treat this as a "what changed when we closed the box" problem. The candidates are: mechanical stress on the PCB or on the sensor (board flex, mounting torque, connector mating force), a change in thermal environment (the enclosure traps heat, shifting the offset of the amplifier or the sensor bridge), a change in grounding or shielding (the enclosure becomes part of the ground path or couples noise differently), or a change in the sensor's physical orientation relative to gravity or the patient.

I'd start by reproducing the offset in a controlled way: assemble the unit but leave it open, measure; then close it and measure; then mount it in the final position and measure. That isolates which step introduces the offset. If it's the enclosure closing, I'd look at whether the board is being flexed — strain gauges on the PCB near the analog front-end can show this directly. If it's the mounting position, I'd check whether the sensor is sensitive to orientation (many pressure and force sensors are) or whether the mounting introduces a thermal path that changes the local temperature.

If it's thermal, I'd measure the actual temperature at the amplifier and sensor in the assembled unit versus the bench, and compare the offset drift against the datasheet's temperature coefficient. If the drift is larger than the datasheet predicts, the problem may be a mismatch between the sensor's and the amplifier's temperature coefficients, or a thermal gradient across the front-end. The fix could be as simple as a layout change to keep the front-end isothermal, a different op-amp with better offset drift, or a calibration step performed in the assembled state. The key is to identify which physical change causes the offset before choosing a fix, because a calibration that doesn't address the cause will drift again in the field.

**Possible follow-ups:**
- How would you distinguish a mechanical stress effect from a thermal effect if both are present at the same time?
- If the offset is consistent across units, does that change your hypothesis about the cause?