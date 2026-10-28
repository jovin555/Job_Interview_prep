# debugging-failure-analysis — Day 99

## Q1: How would you approach debugging a device where the failure only reproduces when the unit is powered from its internal battery, but passes every test on a bench supply at the same nominal voltage?

**Answer:** The first thing I'd do is stop treating "same nominal voltage" as "same electrical environment," because it almost never is. A bench supply is a low-impedance, well-regulated source with a short, low-inductance cable; a battery pack is a higher-impedance source with protection circuitry, a fuel gauge, and a connector in the path. So I'd start by characterizing the difference rather than assuming it's a firmware or component fault.

Concretely: I'd instrument the actual rail at the load — not at the supply terminals — with a scope probe at the decoupling capacitors, using a short ground lead or a proper probe tip, and compare the transient response under the same workload in both configurations. I'd look at load-step response, ripple, and any droop during high-current events like radio transmit bursts or motor/actuator switching. I'd also check inrush and the battery protection circuit's behavior — some protection ICs or fuel gauges will briefly limit current or fold back under certain load profiles, which a bench supply never does.

Then I'd look at what else changes when the battery is connected: does the firmware take a different power path, enable a different regulator, or change a clock or low-power mode based on a "battery present" GPIO? A surprising number of "battery-only" bugs are actually "different code path" bugs. I'd confirm by logging the power-path state and the active configuration in both setups.

The discipline here is one variable at a time: swap the bench supply for a battery emulator with programmable output impedance, or add series resistance/inductance to mimic the pack, and see if the failure follows the source impedance. If it does, it's a power-integrity problem; if it doesn't, it's a configuration or state problem. That single experiment usually splits the search space cleanly.

**Possible follow-ups:** How would you set up a battery emulator to reproduce this, and what output impedance would you start with? If the failure follows source impedance, where would you look first — bulk capacitance, the protection circuit, or the regulator's loop response?

## Q2: You're debugging a power rail that shows excessive ripple only when a high-current subsystem is switching, but the ripple is within specification when that subsystem is idle. How would you approach this?

**Answer:** This is a classic load-transient and power-distribution problem, so I'd approach it as "the rail is fine statically but the delivery network can't supply the transient." The idle-state measurement tells me the DC operating point and the regulator's quiescent behavior are fine; the switching-state ripple tells me the problem is in the AC path — output capacitance, ESR, loop response, or the physical layout between the regulator and the load.

I'd start by measuring properly: scope the rail right at the load's power pins with a short ground return, and simultaneously capture the switching node and the load current (current probe or a sense resistor) so I can correlate ripple events with specific current edges. I'd want to see whether the ripple is synchronous with the switching frequency of the high-current subsystem (suggesting coupling or ground bounce) or with the regulator's own switching (suggesting insufficient output cap or loop instability under transient).

Then I'd separate the mechanisms. If the ripple appears at the load but not at the regulator output, it's an IR/inductive drop or ground-bounce issue in the distribution — I'd check the return path, via placement, and whether the high-current subsystem shares a ground return with sensitive circuitry. If it appears at the regulator output too, I'd look at output capacitance and ESR, and whether the transient exceeds the regulator's loop bandwidth. A quick test: add bulk capacitance locally at the load and see if the ripple drops — that confirms a distribution/decoupling issue rather than a regulator design issue.

I'd also verify the measurement itself isn't lying — probe ground lead inductance can manufacture "ripple" that isn't there. A quick sanity check with a differential probe or a properly tipped probe against a known-good reference is worth the five minutes.

**Possible follow-ups:** How would you distinguish ground bounce from a genuine rail droop in that measurement? If adding local bulk capacitance fixes it, is that an acceptable design fix or a band-aid — and how would you decide?

## Q3: A device's firmware occasionally reports a sensor value that is plausible but wrong — not out of range, not flagged by any self-test, just incorrect — and it's only caught later when the data is reviewed offline. How would you approach this investigation?

**Answer:** The hard part here is that "plausible but wrong" defeats every range check and self-test, so the investigation has to be built around capturing the actual data path rather than relying on the device's own judgment about its health. My first move is to make the failure observable: add instrumentation that logs the raw sensor value, the timestamp, the relevant state (which mode, which channel, what the previous value was), and ideally a checksum or sequence number, so that when a bad value appears offline I can reconstruct exactly where in the chain it went wrong.

Then I'd divide the data path into stages — sensor output, analog front-end, ADC conversion, firmware processing/scaling, storage, and transmission — and figure out which stage the corruption enters. The key question is whether the wrong value is wrong at the ADC (an analog or conversion problem) or wrong only after firmware processing (a scaling, indexing, buffer, or concurrency problem). If I can log the raw ADC counts alongside the processed value, that single comparison usually localizes it immediately.

I'd also look hard at concurrency and memory: is the value being read while a DMA transfer or interrupt is updating the same buffer? Is there a shared variable without proper atomic access? Is a calibration coefficient being applied from a table that's occasionally stale or misindexed? "Plausible but wrong" is very often a data-integrity bug — a torn read, a race, or an off-by-one in a lookup — rather than a sensor fault, because a real sensor fault usually produces out-of-range or noisy values.

Finally, I'd try to make it reproducible: run accelerated cycles, vary temperature and supply, and inject faults deliberately (e.g., force a known input and check the full chain end-to-end). If I can't reproduce it on demand, I'd at least build a targeted stress test around the suspected stage and let statistics do the work.

**Possible follow-ups:** How would you design the logging so it doesn't itself perturb the timing you're trying to observe? If the raw ADC value is correct but the processed value is wrong, what are the first three things you'd check?

## Q4: You're leading a failure investigation and you've reached a point where two plausible root causes remain, both supported by partial evidence, and the team is split on which to pursue. How would you handle this and drive the investigation to a conclusion?

**Answer:** When two hypotheses both have partial support, the trap is letting the team argue about which is "more likely" — that's a debate you can't win with the evidence you have. What I try to do is convert the disagreement into a discriminating experiment: what single test or measurement would give a different result depending on which hypothesis is true? If I can find that, the split resolves itself on data rather than opinion.

Practically, I'd write both hypotheses down explicitly with their predicted observable consequences — "if it's A, we should see X under condition Y; if it's B, we should see Z." Then I'd rank the experiments by cost and discriminating power and run the cheapest one that separates them first. I'd also assign owners to each hypothesis so both get pursued in parallel rather than the team coalescing around one and starving the other of attention — that keeps the minority view honest and often surfaces the answer faster.

I'd be explicit about decision criteria and timelines up front: "we run these two experiments by this date; if neither is conclusive, we escalate to a controlled fault-injection or a design-of-experiments approach." And I'd keep the corrective-action decision gated on confirmed root cause — I don't want to ship a fix for the more popular hypothesis just to relieve pressure, because a wrong fix in a medical device is worse than a delayed one.

Throughout, I'd keep the tone collaborative: the goal isn't to prove someone wrong, it's to let the evidence pick the winner. Framing it that way usually defuses the split, because both camps can agree on the experiment even when they disagree on the conclusion.

**Possible follow-ups:** What would you do if the discriminating experiment is expensive or takes weeks, and the schedule won't allow it? How do you keep the team from treating the "losing" hypothesis as wasted effort?

## Q5: How would you approach a failure investigation where a device's analog front-end is accurate on the bench with a test harness, but shows a small, consistent offset only when the enclosure is fully assembled and the unit is installed in its final mounting position?

**Answer:** The bench-to-enclosure delta is the whole story here, so I'd treat "what changes when it's assembled and mounted" as the primary variable. The offset being small and consistent — rather than noisy or intermittent — points toward a systematic effect: a mechanical stress on a component, a changed thermal environment, a grounding or shielding change, or a different reference/return path once the enclosure and mounting hardware are in place. Consistent offset is a strong hint that it's not random noise coupling but a bias being introduced.

I'd start by reproducing it in stages: bench with harness, then board in enclosure but not mounted, then fully mounted in the final position. That ladder tells me whether it's the enclosure itself (shielding, thermal, cable routing) or the mounting (mechanical stress, grounding through the chassis, a changed return path). If the offset appears only at the final mounting step, I'd suspect mechanical stress on the sensor or its solder joints, or a ground reference shifting because the chassis now provides a parallel return.

For a bridge-type sensor front-end, I'd specifically check the excitation/reference and the amplifier's input bias — a small mechanical stress on the sensor or a change in the reference ground can shift the bridge output or the amp's common-mode operating point. I'd also check thermal: does the offset track with warm-up time once enclosed, and does it return to zero when cooled? That distinguishes a thermal/mechanical bias from an electrical coupling issue.

I'd verify with a controlled experiment — apply the mounting torque in steps and watch the offset, or run the unit with the enclosure grounded vs. isolated — and confirm the mechanism before proposing a fix. The fix then follows the mechanism: strain relief or mounting isolation for mechanical, a grounding/reference change for electrical, or thermal design changes if it's temperature-driven.

**Possible follow-ups:** How would you tell a mechanical-stress-induced offset apart from a thermal one if both appear only after assembly? If the offset is within the sensor's datasheet accuracy but still trips the system's fault threshold, how would you decide whether to fix the hardware or adjust the algorithm's tolerance?