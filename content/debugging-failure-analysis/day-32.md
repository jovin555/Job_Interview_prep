# debugging-failure-analysis — Day 32

## Q1: How would you approach debugging a medical device where a specific analog input channel reads correctly when measured directly at the ADC input with an oscilloscope, but the firmware consistently reports a value that is offset by a fixed amount — and the offset is different on different units of the same device?

**Answer:** This is a classic case where the measurement point and the measurement method are telling you different things, and the unit-to-unit variation is a key clue. I'd start by questioning what the oscilloscope probe is actually seeing versus what the ADC sees. A high-impedance scope probe at the ADC pin can load the circuit differently than the ADC's own sampling capacitor, especially if the source impedance is high. The fact that the offset varies between units suggests a component tolerance issue rather than a fixed design error.

My systematic approach would be:

1. **Verify the ADC reference voltage on each unit.** If the reference is derived from a resistor divider or a regulator with loose tolerance, the ADC's full-scale range shifts, producing a gain error that looks like an offset at a specific input level. Measure the actual reference voltage on multiple units and compare against the firmware's assumed value.

2. **Check the source impedance and ADC sampling time.** If the sensor or front-end has high output impedance and the ADC sampling time is marginal, the sampling capacitor may not fully charge, causing a droop that appears as an offset. This would vary with component tolerances (e.g., the RC time constant of the source). I'd calculate the worst-case settling time and compare against the ADC's acquisition time setting.

3. **Look at the input bias current path.** If the front-end uses an instrumentation amplifier or op-amp, input bias currents flowing through a high-value resistor in the signal path can create a DC offset. The magnitude depends on the resistor tolerance and the specific op-amp's bias current, which explains unit-to-unit variation.

4. **Measure the actual voltage at the ADC input with a precision multimeter** (not a scope) while the firmware is running, and compare that to the firmware-reported value. This separates a front-end hardware issue from an ADC configuration issue.

5. **Review the firmware's ADC calibration routine.** Some ADCs have offset/gain calibration registers. If the calibration is performed at a specific temperature or with a specific reference, and the calibration constants are stored per-unit, a corrupted or improperly applied calibration constant would produce a unit-specific offset.

The key insight is that the scope reading being correct doesn't mean the ADC sees the same voltage — the probe, the ADC input structure, and the firmware's interpretation are three separate links in the chain, and each needs to be verified independently.

**Possible follow-ups:**
- How would you determine whether the offset is a gain error versus a true offset error, and why does that distinction matter for the fix?
- What measurements would you take to characterize the ADC's input settling time on the actual board?

---

## Q2: How would you approach a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent communication failure is caused by a marginal pull-up resistor value on an I2C bus or by a firmware timing issue in the bus recovery routine?

**Answer:** This is a classic cross-disciplinary disagreement, and the first step is to recognize that both teams may be partially right — the failure could be a combination of a marginal hardware condition and a firmware routine that doesn't robustly handle it. I'd structure the investigation to gather data that discriminates between the hypotheses rather than trying to settle the argument directly.

My approach:

1. **Define the failure precisely.** What does "intermittent communication failure" mean exactly — a NACK, a bus hang, corrupted data? When does it occur — after a specific sequence, at a specific temperature, after a specific number of transactions? I'd ask both teams to agree on the observable symptom before discussing causes.

2. **Capture the failure in action.** I'd instrument the system to log the I2C bus state (SCL/SDA levels) and the firmware's state machine at the moment of failure. A logic analyzer with deep capture, triggered on the failure condition, would show whether the bus is stuck low, stuck high, or exhibiting marginal levels. This data alone often resolves the disagreement.

3. **Measure the electrical parameters.** I'd measure the rise time of SCL and SDA on the actual board, at the actual pull-up resistor values, with the actual bus capacitance (including the sensor's input capacitance and any cable or connector). I'd also measure the worst-case rise time across the operating temperature range, since pull-up resistance and input thresholds both shift with temperature.

4. **Review the firmware's bus recovery routine.** If the firmware detects a bus hang and toggles SCL to recover, I'd check whether the routine accounts for the worst-case rise time. A common issue is that the recovery routine generates clock pulses faster than the bus can actually rise, so the slave never sees a valid clock edge. I'd also check whether the recovery routine properly handles the case where SDA is stuck low.

5. **Run a fault-injection test.** I'd deliberately vary the pull-up resistance (e.g., swap in higher-value resistors to simulate worst-case tolerance) and stress the bus with different transaction patterns to see if the failure reproduces. This directly tests the hardware hypothesis. Similarly, I'd vary the firmware timing parameters to test the software hypothesis.

6. **Look for interaction effects.** The most likely root cause is often an interaction: the pull-up value is marginal (within spec but at the slow edge), and the firmware's recovery routine doesn't wait long enough for the bus to reach a valid logic level before proceeding. Fixing either one alone might reduce the failure rate but not eliminate it.

The key is to frame this as a joint investigation where both teams contribute data, not as a competition. The goal is to find the root cause, not to assign blame.

**Possible follow-ups:**
- What specific measurements would you take to characterize the I2C bus rise time, and what would you compare them against?
- How would you design a fault-injection test that isolates the hardware contribution from the firmware contribution?

---

## Q3: How would you approach debugging a medical device where the firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory being copied is within bounds?

**Answer:** This is a frustrating scenario because the obvious checks — address validity and bounds — pass, yet the fault persists. The key insight is that a hard fault during a memory copy with valid addresses often points to something other than the copy itself: it could be a corrupted stack, a misaligned access, a fault during a memory access that the copy triggers (like a bus fault on a peripheral address), or a stack overflow that corrupts the return address.

My systematic approach:

1. **Capture the full fault context, not just the stack trace.** I'd record the fault status registers (CFSR, HFSR, BFAR, MMFAR on ARM Cortex-M) at the moment of the fault. These registers tell you the exact cause: whether it's a bus fault (address error), a usage fault (e.g., divide by zero, unaligned access), or a hard fault escalated from a configurable fault. The BFAR/MMFAR registers would tell you the faulting address, which may be different from the source/destination of the copy.

2. **Examine the stack pointer at the time of the fault.** If the stack pointer is corrupted or points to an invalid region, the stack trace itself is unreliable. I'd check whether the stack pointer is within the allocated stack region and whether the stack has overflowed into adjacent memory. A stack overflow can corrupt local variables, return addresses, and the data being copied.

3. **Check for unaligned access.** If the memory copy is operating on a buffer that's not aligned to the architecture's requirement (e.g., a 32-bit access at an odd address), some architectures generate a usage fault. The source and destination addresses might be "valid" in the sense of being within memory, but if one of them is misaligned, the copy itself can fault. I'd check the alignment of both addresses and the copy size.

4. **Look at what the copy is actually doing.** Is it a `memcpy` call, or is it a custom loop? If it's a custom loop, I'd check the loop counter and the pointer increments. A common bug is a loop counter that's off by one, causing the copy to write one word past the destination — but the stack trace would still point to the copy function, and the addresses might appear valid if the overflow is into adjacent allocated memory.

5. **Check for a corrupted source buffer.** If the source data is corrupted (e.g., a buffer overflow elsewhere wrote garbage into the source), the copy itself might trigger a fault if the corrupted data causes an invalid operation — though this is less likely with a simple memory copy. More likely, the corruption is in the stack frame itself, so the return address after the copy is invalid.

6. **Reproduce with instrumentation.** I'd add logging around the copy operation — record the source address, destination address, length, and the values of key registers before the copy. I'd also enable the fault handler to capture the full context and store it in a reserved memory region that survives the reset. This gives you the actual faulting address and the exact state at the moment of failure.

7. **Consider the compiler's optimization.** Sometimes the stack trace points to a memory copy because the compiler inlined a larger operation (like a struct assignment) into a `memcpy` call. The actual fault might be in a different logical operation that the compiler implemented as a copy. I'd look at the disassembly to see what the copy is actually doing.

The most common root causes I've seen in this pattern are stack corruption from a buffer overflow elsewhere, or a misaligned access that only occurs with certain data patterns. The fault status registers are the key to narrowing this down quickly.

**Possible follow-ups:**
- How would you go about capturing the fault status registers if the device resets before you can read them?
- What would you look for in the disassembly of the memory copy function to identify a potential misalignment issue?

---

## Q4: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This is a compatibility issue that points to a difference between the two chargers, not necessarily a defect in the device itself. The key is to characterize what's different about the "problem" charger and why the device's charging circuit responds differently.

My approach:

1. **Characterize both chargers electrically.** I'd measure the output voltage, current capability, and — critically — the transient behavior of both chargers under load. Key parameters include: the no-load voltage, the voltage droop under load, the output ripple, and the response to a load step. Many USB chargers have different implementations of the USB BC 1.2 or USB-PD negotiation, and some have poor load transient response.

2. **Check the device's charging input protection and negotiation.** The device likely has some form of input protection (e.g., overvoltage protection, inrush limiting) and possibly a USB detection circuit. I'd check whether the device negotiates the input current limit based on the charger's characteristics. Some chargers use a voltage divider on the D+/D- lines to signal their current capability; if the device misreads this, it might request more current than the charger can supply, causing the charger's output to collapse and the device to draw excessive current trying to compensate.

3. **Measure the inrush current at connection.** The excessive current might be an inrush event, not a steady-state condition. Different chargers have different output capacitance and different soft-start behavior. If the device's input capacitance is large, connecting to a charger with a fast rise time could cause a large inrush current that the charger interprets as a fault or that causes the charger's protection to engage. I'd measure the current waveform at the moment of connection for both chargers.

4. **Look at the charger's overcurrent protection behavior.** Some chargers fold back their output voltage or current when overloaded, while others shut down and retry. If the device's charging circuit briefly draws more current than the charger's rating (e.g., during a load transient), the charger might enter a protection mode that causes the device to see a voltage drop, which then causes the charging circuit to draw even more current — a positive feedback loop.

5. **Check the device's input voltage range and undervoltage lockout.** If the problem charger has a higher output impedance, the voltage at the device's input might sag below the charging IC's undervoltage lockout threshold when the charger starts delivering current. The IC might then oscillate between trying to charge and shutting down, which could manifest as excessive average current draw.

6. **Test with a programmable load.** I'd use a programmable DC supply to simulate the problem charger's characteristics — specifically its output impedance and transient response — to reproduce the failure in a controlled way. This lets me isolate whether the issue is the charger's steady-state characteristics or its transient behavior.

7. **Review the charging IC's configuration.** I'd check the input current limit setting, the input voltage regulation threshold (some charging ICs reduce charge current to maintain input voltage), and the thermal regulation. A misconfigured input current limit could cause the device to draw more current than the charger can supply.

The likely root cause is a mismatch between the device's input current requirement and the charger's capability, possibly exacerbated by the charger's transient response. The fix might be a firmware change to the input current limit, a hardware change to the inrush limiting, or simply documenting the charger compatibility requirement.

**Possible follow-ups:**
- What specific measurements would you take on the problem charger to characterize its behavior under load?
- How would you determine whether the issue is an inrush problem versus a steady-state overcurrent problem?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a senior engineer on your team is convinced they know the root cause based on their experience with a similar device, but the evidence doesn't fully support their hypothesis — and they're pushing to implement a fix before the investigation is complete?

**Answer:** This is a common and challenging situation in failure analysis. The senior engineer's experience is valuable, but acting on an unconfirmed hypothesis in a medical device context is risky — a fix that addresses the wrong root cause can introduce new failure modes, and in a regulated environment, the corrective action process requires evidence. I'd handle this by respecting their experience while insisting on evidence-based decision-making.

My approach:

1. **Acknowledge their hypothesis and its value.** I'd start by saying that their experience with a similar device is exactly the kind of insight that can shortcut a long investigation, and I'd ask them to walk me through the reasoning — what specifically about the current failure matches the previous one, and what's different? This shows respect and also forces a clear articulation of the hypothesis.

2. **Compare the hypothesis against the evidence.** I'd lay out the evidence we have — the failure data, the test results, the device logs — and ask the engineer to show how their hypothesis explains each piece of evidence. I'd also ask what evidence would disprove their hypothesis. This is a non-confrontational way to test the hypothesis's fit.

3. **Propose a parallel track.** Rather than either accepting or rejecting their fix, I'd propose running their proposed fix as a controlled experiment while the investigation continues. For example: "Let's implement your fix on a small sample of units and run them through the same test that reproduces the failure. If it resolves the issue, that's strong evidence. Meanwhile, we'll continue gathering data on the remaining units to confirm the root cause." This gives the engineer a path forward while maintaining the integrity of the investigation.

4. **Quantify the risk of acting prematurely.** I'd frame the discussion around risk: what's the cost of implementing the fix if it's wrong? In a medical device, that includes re-verification costs, potential regulatory impact, and the risk of a field failure if the fix introduces a new issue. I'd ask the engineer to consider whether the evidence is strong enough to justify that risk, or whether a bit more investigation time is worth the certainty.

5. **Use the 8D process as a framework.** In a formal failure investigation, the corrective action (step 7) comes after root cause confirmation (step 5). I'd remind the team that implementing a fix before root cause confirmation violates the process and could compromise the regulatory traceability of the corrective action. This isn't about bureaucracy — it's about ensuring the fix is defensible if the device is audited.

6. **Escalate if necessary.** If the engineer continues to push and the disagreement is blocking progress, I'd escalate to the project sponsor or quality manager, presenting both the engineer's hypothesis and the evidence gap. The decision then becomes a management decision about risk tolerance, not a technical argument.

The key is to keep the investigation moving forward and to use the disagreement as an opportunity to strengthen the evidence base, not to let it stall the team.

**Possible follow-ups:**
- How would you handle the situation if the senior engineer's proposed fix is actually implemented by the team before you can intervene, and it doesn't resolve the failure?
- What specific evidence would you require before you'd be comfortable implementing a fix based on an engineer's experience rather than on a confirmed root cause?