# debugging-failure-analysis — Day 62

## Q1: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The key observation is that the offset appears only after two changes happen together — the enclosure is closed and the unit is mounted. That points away from the analog signal chain itself and toward something the mechanical/installation context introduces: mechanical stress on the PCB or sensor, a changed thermal environment, a changed ground reference, or a changed parasitic path.

I'd start by separating the two variables rather than treating "assembled and mounted" as one condition. Test the board powered and running in four states: open bench, in the enclosure but unmounted, mounted but with the enclosure open, and fully assembled and mounted. If the offset tracks the enclosure, it's likely thermal or a shielding/grounding change. If it tracks the mounting, it's likely mechanical stress — board flex altering a strain-sensitive component, a connector, or a solder joint, or a mounting point now tying the board ground to a chassis at a different potential.

For the electrical side, I'd measure the offset at the ADC input with a high-impedance probe while the unit is in the failing state, so I can tell whether the error is upstream of the ADC (sensor, amplifier, reference) or introduced digitally. I'd also check the reference voltage and the analog ground at the point of measurement, because a small ground shift between the sensor return and the ADC ground shows up as a fixed offset. If the offset is stable and repeatable, that's a strong hint it's a DC path issue — a ground offset, a bias current through a changed impedance, or a reference divider — rather than noise.

If it correlates with the enclosure, I'd look at thermals: does the offset appear after warm-up, and does it scale with internal temperature? A consistent offset that appears once the unit is closed often means a component is now running warmer and its bias point has shifted. I'd confirm with a thermal camera or a thermocouple on the suspect parts and compare against the open-bench case.

The discipline throughout is one change at a time: change only the enclosure state, or only the mounting state, and re-measure. That keeps the cause from hiding behind two simultaneous variables.

**Possible follow-ups:**
- If the offset only appears when the unit is mounted, how would you determine whether it's mechanical stress versus a ground/chassis connection?
- How would you decide whether this is a design issue to fix or a calibration issue to compensate for in firmware?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a load-transient and power-distribution problem, so I'd approach it as a question of where the transient current is flowing and how the rail responds to it, not just "the regulator is bad."

First, characterize the event properly. I'd measure the ripple at the load — right at the decoupling capacitors of the switching subsystem and at the input of the sensitive circuitry — not only at the regulator output. Ripple measured at the regulator can look fine while the rail at the load is bouncing, because the impedance of the trace and via between them turns the transient current into a voltage drop. I'd use a short-ground-spring probe tip and a wideband scope to avoid picking up probe-loop artifacts that masquerade as ripple.

Then I'd separate the mechanisms. A high-current subsystem switching produces a fast current step; the rail response depends on the decoupling network's impedance versus frequency. If the ripple is a high-frequency ring, it's likely insufficient local decoupling or a resonance between the bulk and ceramic capacitors. If it's a slower droop-and-recover, it's likely the regulator's transient response or the bulk capacitance being too far away or too small. If it's a periodic dip synchronized to the switching, I'd check whether the switching return current is sharing a ground path with the sensitive analog circuitry — a common-impedance coupling problem.

I'd also check the layout: is the high-current loop tight, or does it enclose a large area that couples into nearby traces? Is the ground return for the switching subsystem separate from the analog ground until a single star point? Ground bounce from a shared return is a very common cause of "ripple only when the big load switches."

For fixes, the order I'd consider is: improve local decoupling at the load, tighten the high-current loop, separate the return paths, add bulk capacitance closer to the transient source, and only then revisit the regulator's compensation or transient spec. Changing the regulator first is usually treating the symptom.

**Possible follow-ups:**
- How would you tell the difference between insufficient decoupling and a ground-return coupling problem?
- What measurements would you take to confirm the regulator itself is or isn't the limiting factor?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hard part here is that the error is silent — it passes every range check and self-test, so the usual fault detection won't catch it. That means the investigation has to start with making the failure observable, because right now the only evidence is offline data review.

First I'd try to characterize the error from the data that already exists. Is the wrong value a single sample, or a run of samples? Is it a fixed offset, a scaled value, a stale value from a previous reading, or a value that looks like it belongs to a different channel? The pattern often points directly at the mechanism: a stale value suggests a read that didn't complete and the buffer wasn't updated; a scaled or offset value suggests a conversion or calibration step; a value from another channel suggests a buffer/indexing or DMA issue.

Then I'd add instrumentation to catch it in the act. That could be a checksum or sequence counter on each sensor read, a redundant read compared against the primary, or a timestamp so I can correlate the bad sample with what else the system was doing at that moment. The goal is to turn a silent error into a logged event with context — which peripheral was active, what the timing was, whether an interrupt was pending.

I'd also look at the read path end to end: sensor → bus transaction → driver buffer → conversion → application. A plausible-but-wrong value often comes from a race where the buffer is read while it's being updated, or from a bus transaction that returned a valid-looking but incorrect frame because of a marginal timing or a missing error check. If the bus has no CRC or the driver doesn't validate it, a corrupted frame can pass straight through.

Finally, I'd try to reproduce it deliberately — inject the suspected condition (a concurrent high-priority interrupt, a bus error, a timing stress) and see whether the wrong value appears. If I can reproduce it on demand, the root cause usually follows quickly.

**Possible follow-ups:**
- How would you add validation to the read path without adding so much overhead that it changes the timing behavior you're trying to observe?
- If the bad value only appears in the field and never on the bench, how would you capture enough context to diagnose it?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the temptation is to argue about which is more likely. I'd redirect the team away from debating likelihood and toward finding the test that discriminates between them — a measurement or experiment whose outcome is different depending on which hypothesis is true.

The first step is to state both hypotheses precisely enough that they make different predictions. "It's a timing issue" and "it's a layout issue" are too vague to test. If I can write down what each one predicts — for example, hypothesis A predicts the failure rate changes when I change X but not Y, hypothesis B predicts the opposite — then I have a discriminating experiment. If I can't find any observation that separates them, that usually means the hypotheses aren't specific enough yet, and the real work is refining them.

I'd also consider whether the two causes could both be real and interacting — sometimes the split in the team is a false dichotomy, and the failure needs both conditions. In that case the discriminating test is to remove one condition and see whether the failure disappears.

Practically, I'd assign the discriminating test to whoever is most skeptical of the hypothesis it would confirm, so the result is credible to both sides. I'd set a clear decision criterion in advance: what result would make us abandon each hypothesis. And I'd time-box it — if the test is inconclusive, we refine rather than keep running the same experiment.

Throughout, I'd keep the tone collaborative: the goal is to converge on the truth, not to win. Framing it as "what would change your mind?" tends to defuse the split and get people contributing to the test rather than defending a position.

**Possible follow-ups:**
- What would you do if the discriminating test is inconclusive and the schedule won't allow more investigation?
- How would you keep the team aligned if the evidence eventually points to one hypothesis and the people who backed the other feel their work was wasted?

## Q5: A junior engineer has been debugging an intermittent failure for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. They're frustrated and the schedule is tight. How would you approach this?

**Answer:** The pattern here — everything passes in isolation but the system fails — is a classic sign that the debugging is happening at the wrong level. Component-level testing can't reproduce a failure that depends on the interaction between components, so the engineer isn't failing; the method is mismatched to the problem.

I'd start by acknowledging that and reframing it, because frustration usually comes from feeling stuck, and the fastest way to unstick someone is to give them a different, more promising angle rather than more pressure. I'd ask them to walk me through what they've tried and what they've observed, not to check up on them but to understand the failure's behavior. Often the useful information is in the details they've dismissed.

Then I'd help them shift from "test components" to "characterize the failure." Questions I'd work through with them: Can you reproduce it at all, and if so, what's the shortest path to reproduction? What's different between the failing system and the passing bench setup — power source, cabling, grounding, load, temperature, timing? Intermittent system-level failures usually depend on a condition that the bench setup doesn't have, so the goal is to find that condition and bring it into the test.

I'd also introduce structure: a hypothesis list, a log of what's been ruled out and why, and one change at a time. A junior engineer can spin on many small changes without a record, and the record itself often reveals the pattern.

On the schedule pressure, I'd be honest that the priority is finding the mechanism, not appearing busy. I'd offer to pair on it for a session — sometimes a second set of eyes on the same data breaks the logjam — and I'd make sure they know asking for help early is the right move, not a failure. The goal is to get them to a reproducible failure, because once it reproduces reliably, the rest is usually straightforward.

**Possible follow-ups:**
- How would you decide when to step in and take over versus continuing to coach them through it?
- If the failure can't be reproduced on demand, how would you guide them to make progress anyway?