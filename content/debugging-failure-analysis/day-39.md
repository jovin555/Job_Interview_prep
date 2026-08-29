# debugging-failure-analysis — Day 39

## Q1: How would you approach debugging a medical device where a specific sensor reading is correct when measured at the ADC input with an oscilloscope, but the firmware consistently reports a value that is offset by a fixed amount — and the offset is different on different units of the same device?

**Answer:** This is a classic case where the analog signal is fine at the point of measurement, but something between the ADC input pin and the firmware's reported value is introducing a unit-to-unit variable offset. I'd start by clarifying exactly where the oscilloscope probe is connected — if it's at the ADC input pin itself, then the analog front-end is likely not the problem, and I'd focus on the digital path.

First, I'd verify the ADC reference voltage on each unit. A unit-to-unit offset that varies suggests something like a reference tolerance issue, a gain error in the ADC's internal PGA (if one is used), or a firmware calibration constant that isn't being applied correctly. I'd check whether the offset scales with the input voltage (gain error) or is constant regardless of input (offset error) — that distinction narrows the search considerably.

Next, I'd look at the ADC configuration. If the firmware is using a different ADC channel, sampling time, or reference selection than intended, that could produce a consistent offset. I'd also check whether the firmware is reading the correct data register or applying any post-processing (averaging, filtering, offset subtraction) that might be miscalibrated.

If the offset varies between units, I'd suspect a component tolerance issue in the reference circuit or the analog front-end — perhaps a resistor divider or reference buffer with wider-than-expected tolerance. I'd measure the actual reference voltage on several units and compare it to what the firmware assumes. If there's a mismatch, the fix might be a per-unit calibration step in production, or a tighter-tolerance component.

Finally, I'd check whether the offset correlates with anything measurable — board revision, component date codes, or assembly lot — which could point to a specific component supplier or process variation.

**Possible follow-ups:**
- How would you distinguish between a gain error and an offset error in your measurements?
- What calibration approaches would you consider for production, and what are the trade-offs of each?

---

## Q2: How would you approach a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent communication failure is caused by a marginal pull-up resistor value on an I2C bus or by a firmware timing issue in the bus recovery routine?

**Answer:** The first thing I'd do is acknowledge that both hypotheses are plausible and that the goal is to gather evidence, not to win an argument. I'd structure the investigation to test both hypotheses independently while collecting data that could discriminate between them.

For the hardware hypothesis — marginal pull-up resistance — I'd start by measuring the actual rise times on SDA and SCL under worst-case conditions: maximum bus capacitance, minimum supply voltage, and at the temperature extremes the device is rated for. I'd check the pull-up values against the I2C specification for the bus speed being used, and I'd look at the waveform with a scope to see if the rise time is marginal. If possible, I'd also measure the bus capacitance to calculate whether the pull-up value is appropriate.

For the firmware hypothesis — the bus recovery routine — I'd review the code to understand exactly what happens when a bus hang is detected. I'd look at whether the recovery routine properly handles the I2C peripheral state machine, whether it generates the required clock pulses to release a stuck slave, and whether there's a race condition between the recovery routine and other interrupt handlers that might also be accessing the bus.

The key discriminating experiment would be to instrument the system to capture the bus state at the moment of failure. A logic analyzer with deep memory, or a scope triggered on the failure condition, could show whether the bus is actually stuck (SCL or SDA held low) or whether the failure is in the firmware's handling of a normal bus condition. I'd also check the error logs — if the firmware records the I2C status registers at the time of failure, that could tell us whether the bus was truly hung or whether the peripheral reported an error that the firmware mishandled.

I'd also consider a controlled experiment: temporarily increasing the pull-up value (or adding a stronger pull-up) on a few units to see if the failure rate changes. Similarly, I'd modify the firmware recovery routine on a few units to see if that changes the failure rate. Changing one variable at a time is essential here.

Finally, I'd bring both teams together to review the evidence and agree on the next experiment. The goal is to converge on root cause through data, not through persuasion.

**Possible follow-ups:**
- What specific measurements would you take to characterize the I2C bus timing margin?
- How would you design an experiment to test the firmware recovery routine in isolation?

---

## Q3: How would you approach debugging a medical device where the firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory regions being copied are within their allocated bounds?

**Answer:** This is a frustrating scenario because the obvious causes — invalid pointers or out-of-bounds access — have been ruled out. I'd approach this by questioning the assumption that the fault is actually caused by the memcpy itself. The stack trace points to the memcpy, but the root cause could be memory corruption that occurred earlier, and the memcpy is just where the corruption manifests.

First, I'd check whether the fault is a bus fault, a usage fault, or a hard fault — the fault status registers (CFSR, HFSR, BFAR, MMFSR on ARM Cortex-M) would tell me whether it's an alignment issue, an imprecise bus error, or something else. An imprecise bus fault, for example, can be reported at an instruction that's unrelated to the actual cause.

Next, I'd look at the memory regions involved. Even though the source and destination addresses are within bounds, I'd check whether the memory regions overlap, whether the DMA controller is also accessing the same memory, or whether a peripheral is writing to that region via a memory-mapped register that's misconfigured. I'd also check whether the memcpy is being called from an interrupt context while another interrupt or the main loop is also accessing the same buffer — a race condition could corrupt the data mid-copy.

I'd also examine the stack. If the stack trace is corrupted or if the stack pointer is invalid, the "consistent" stack trace might be misleading. I'd check the stack usage — is the stack overflowing into adjacent memory? A stack overflow could corrupt the memcpy's arguments or return address, causing a fault that appears to be in the memcpy.

Another angle: I'd check whether the memcpy is using a DMA-based implementation (some libraries use DMA for large copies). If so, a DMA configuration issue — wrong transfer size, misaligned buffer, or a DMA interrupt conflict — could cause a fault that appears to be in the memcpy but is actually in the DMA setup.

Finally, I'd consider adding instrumentation: a memory protection unit (MPU) configuration that makes the buffer regions read-only or no-access except during the copy, or a canary pattern around the buffers to detect corruption. I'd also enable the fault handler to capture the full register state and the fault status registers, and I'd log the memcpy parameters (source, destination, length) at the time of the fault.

**Possible follow-ups:**
- How would you use the fault status registers to narrow down the cause?
- What role could a DMA controller play in this type of failure, and how would you investigate that?

---

## Q4: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This is a classic interoperability issue, and I'd approach it by first characterizing the difference between the two chargers. The fact that the device works with one charger and not another suggests the problem is in how the device negotiates or handles the charger's electrical characteristics, not a fundamental fault in the charging circuit.

I'd start by measuring the electrical characteristics of both chargers: output voltage under load, current capability, voltage ripple, and any negotiation protocol behavior (like USB Battery Charging or USB-PD). The "specific model" of charger might have a slightly higher output voltage, a different current limit behavior, or a different inrush characteristic that triggers the excessive current draw.

Next, I'd measure the device's input current waveform when connected to each charger. I'd look at the inrush current at connection, the steady-state charging current, and any transient behavior during charging. If the excessive current is an inrush issue, the charger's output capacitance or current limiting behavior might be interacting with the device's input capacitance in a way that causes a large current spike.

I'd also check the device's charging protocol. If the device uses USB Battery Charging negotiation (like BC1.2), the specific charger might be presenting a different "charger type" signature that causes the device to draw more current than intended. For example, if the charger advertises a higher current capability than it can actually deliver, the device might try to draw more current, causing the charger to sag or the device to overdraw.

Another angle: the charger might have a different ground reference or leakage current path that causes a ground loop or common-mode issue. I'd check whether the excessive current is on the VBus line or on the ground line, and whether it's AC or DC.

I'd also consider the device's input protection circuitry. If the device has a reverse-voltage protection FET or an input current limiter, the specific charger's voltage characteristics might cause that circuit to behave differently — for example, a slightly higher voltage might cause the protection FET to operate in a different region.

Finally, I'd check whether the issue is reproducible with multiple samples of the "problem" charger model, and whether it's consistent across multiple device units. If it's consistent, I'd document the charger's characteristics and work with the charging circuit design to ensure compatibility — possibly by adjusting the input current limit, adding inrush limiting, or improving the charger detection algorithm.

**Possible follow-ups:**
- What specific measurements would you take on both chargers to characterize the difference?
- How would you determine whether the issue is an inrush problem versus a steady-state current draw problem?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a junior engineer on your team has been debugging an intermittent issue for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists, and they're becoming frustrated and the project schedule is tight?

**Answer:** The first thing I'd do is acknowledge the engineer's effort and the difficulty of the problem — intermittent system-level failures are genuinely hard, and testing components in isolation is a reasonable approach that just hasn't yielded results yet. I'd want to preserve their confidence and keep them engaged, not make them feel like they've failed.

Then I'd shift the approach. The key insight is that testing components in isolation has ruled out individual component failures, which is valuable information — but the failure is clearly at the system level. I'd suggest we step back and look at the interactions between components rather than the components themselves. What changes when the full system is assembled? Power distribution, ground paths, timing relationships, shared resources — these are all things that don't exist in isolation.

I'd ask the engineer to walk me through their debugging process in detail. Often, the act of explaining the process reveals assumptions that were made along the way — maybe they've been testing with a bench supply instead of the battery, or they've been using a different firmware build, or they've been triggering the system in a way that doesn't match the real failure condition. I'd also ask what they've ruled out and how confident they are in those conclusions.

Next, I'd suggest a different debugging strategy. Instead of trying to reproduce the failure and catch it in the act, I'd propose instrumenting the system to capture more data — adding logging, using a logic analyzer or scope to monitor multiple signals simultaneously, or adding temporary debug code to the firmware. The goal is to observe the system at the moment of failure rather than trying to infer the cause from post-mortem analysis.

I'd also consider pairing the engineer with someone who has a different perspective — maybe a firmware engineer if they're hardware-focused, or vice versa. A fresh set of eyes can often spot something that the person who's been staring at the problem for days has missed.

Finally, I'd set up a structured review — maybe a short daily check-in where the engineer presents their latest findings and we collectively decide on the next experiment. This keeps the investigation moving, prevents the engineer from going down another multi-day rabbit hole, and ensures the team's collective expertise is being applied.

**Possible follow-ups:**
- How would you balance giving the engineer ownership of the investigation with the need to make progress on a tight schedule?
- What specific questions would you ask to help the engineer identify assumptions they might have made?