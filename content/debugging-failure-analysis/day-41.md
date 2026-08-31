# debugging-failure-analysis — Day 41

## Q1: How would you approach a failure investigation where a medical device's analog measurement channel works correctly during bench testing, but shows a consistent gain error when connected to the actual patient sensor — and the error magnitude varies between different sensor units?

**Answer:** This is a classic interface-mismatch problem, and the fact that the error varies between sensor units is a strong clue that the issue is in the interaction between the device's front-end and the sensor's electrical characteristics, rather than in the device's signal chain alone.

My first step would be to characterize the sensor itself. I'd measure each sensor unit's key parameters — bridge resistance (if it's a bridge-type sensor), output impedance, sensitivity, and any internal calibration resistors. The variation between units suggests the sensor's source impedance or drive capability is interacting with the device's input stage in a way that creates a gain error.

Next, I'd examine the device's analog front-end loading effects. A gain error that varies with the sensor suggests the input impedance of the amplifier stage is not sufficiently high relative to the sensor's source impedance, creating a voltage divider effect. I'd calculate the expected loading error using the measured source impedance and the known input impedance, then verify with a simulation.

I'd also check whether the device provides any excitation voltage or current to the sensor. If the sensor is ratiometric, a mismatch in the excitation reference could cause a gain error that tracks with sensor impedance. I'd verify the excitation source's accuracy and its ability to maintain regulation under the varying load presented by different sensors.

Finally, I'd look at the calibration scheme. If the device calibrates using a fixed reference or a single known-good sensor, that calibration may not generalize across the full range of sensor tolerances. I'd recommend characterizing the sensor population's impedance spread and either adjusting the front-end design (higher input impedance, buffer stage) or implementing a per-sensor calibration procedure that accounts for the variation.

**Possible follow-ups:**
- How would you distinguish between a gain error caused by loading versus one caused by the sensor's own sensitivity tolerance?
- What changes would you consider to the front-end design to make it more tolerant of sensor variation?

---

## Q2: How would you approach debugging a medical device where the firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory regions being copied are within their allocated bounds?

**Answer:** This is a frustrating scenario because the obvious causes — invalid pointers, buffer overruns, out-of-bounds access — appear to be ruled out. When the stack trace is consistent but the addresses are valid, I'd broaden the investigation beyond the memory copy itself.

First, I'd question the assumption that the fault is actually caused by the memory copy. The stack trace shows where the fault was *detected*, not necessarily where it was *caused*. A corrupted stack, a corrupted function pointer, or a corrupted return address could cause execution to jump into the middle of a legitimate function, making the memcpy appear to be the culprit when it's actually a victim. I'd examine the full call stack, not just the top frame, and look for anomalies in the stack contents.

Second, I'd consider memory corruption from another source. Even though the copy's source and destination are within bounds, the copy could be reading from or writing to memory that was corrupted earlier by a different operation — a buffer overflow elsewhere, a DMA transaction writing to the wrong address, or a stack overflow from deep recursion. I'd check whether the data being copied is itself corrupted, and whether the fault correlates with specific data patterns.

Third, I'd look at alignment and bus-level issues. If the memory copy is implemented as a word-wise or optimized operation, a misaligned source or destination could cause a bus fault on some architectures. I'd verify alignment requirements and check whether the fault occurs more frequently with certain data sizes or alignments.

Fourth, I'd examine the memory copy implementation itself. If it's a library function, I'd verify the library version and any known errata. If it's custom code, I'd review the loop logic, pointer arithmetic, and any optimization flags that might affect behavior.

Finally, I'd instrument the system to capture more context. I'd add a fault handler that records the full register state, the fault status register contents, and a larger portion of the stack. I'd also consider using a hardware watchpoint on the source and destination memory regions to detect any unexpected writes, and I'd enable any available memory protection unit (MPU) to catch accesses outside known-good regions.

**Possible follow-ups:**
- How would you determine whether the fault is caused by the copy operation itself versus corrupted execution flow?
- What specific instrumentation would you add to capture more diagnostic information?

---

## Q3: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This points to an interoperability issue between the device's charging circuit and the specific charger's electrical characteristics. The fact that it works with the shipped charger but not with another model suggests the device is sensitive to something the other charger does differently.

I'd start by characterizing both chargers on the bench. I'd measure their output voltage under various load conditions, their current-limiting behavior, their startup and shutdown transients, and their output impedance. I'd also check whether the "specific model" charger uses a different charging protocol — for example, USB Battery Charging (BC 1.2), USB Power Delivery (PD), or a proprietary fast-charging scheme — and whether the device's charging controller is attempting to negotiate or detect something that the charger handles differently.

Next, I'd look at the device's input protection and negotiation circuitry. If the device has an inrush current limiter, a load switch, or a USB detection circuit, I'd verify that these operate correctly with the problem charger. A common issue is that a charger with a slower ramp-up or higher output capacitance causes the device's input circuit to oscillate or enter an unexpected state, drawing excessive current.

I'd also examine the charging algorithm itself. If the device's firmware selects a charge current based on what it detects from the charger, a misdetection could cause it to request more current than the charger can supply, pushing the charger into current limit and causing the adapter to overheat or the input voltage to collapse.

I'd measure the actual current draw and input voltage waveform when connected to the problem charger, looking for oscillation, excessive inrush, or a sustained overcurrent condition. I'd also check whether the problem is temperature-related — some chargers have different thermal behavior that could affect the device's charging circuit.

Finally, I'd review the charger's compliance with relevant USB specifications and the device's input requirements. If the problem charger violates a specification parameter — such as voltage tolerance, ripple, or current capability — that would explain the behavior. I'd document the findings and determine whether the fix is in the device (more robust input protection, better detection logic) or in the charger (if it's out of specification).

**Possible follow-ups:**
- What specific measurements would you take on the problem charger to characterize its behavior?
- How would you determine whether the fix should be in the device's hardware, firmware, or in the charger itself?

---

## Q4: How would you approach a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent communication failure is caused by a marginal pull-up resistor value on an I2C bus or by a firmware timing issue in the bus recovery routine?

**Answer:** This is a classic cross-functional disagreement where both hypotheses are plausible and neither team has conclusive evidence. My approach would be to structure the investigation so that the evidence, not opinion, drives the conclusion.

First, I'd establish a shared understanding of the failure. I'd ask both teams to agree on the exact symptom — what "communication failure" means in terms of observable behavior, how often it occurs, and under what conditions. I'd also agree on what data would be considered conclusive evidence for each hypothesis.

Second, I'd gather data that discriminates between the two hypotheses. For the pull-up hypothesis, I'd measure the I2C bus rise times, fall times, and voltage levels under actual operating conditions — not just on the bench, but with the full system running. I'd compare the measured rise time against the I2C specification for the bus speed being used, and I'd check whether the rise time is marginal. I'd also look at the bus capacitance — cable length, number of devices, PCB trace length — and calculate whether the pull-up value is appropriate.

For the firmware timing hypothesis, I'd examine the bus recovery routine in detail. I'd look at the timing of the recovery sequence — how long the bus is held, when the stop condition is generated, whether the routine properly handles the case where a slave is holding the clock line low. I'd also check whether the recovery routine can be triggered while a transaction is in progress, which could cause a race condition.

Third, I'd design experiments that isolate each variable. For the pull-up hypothesis, I could temporarily replace the pull-ups with a stronger value (lower resistance) on a test unit and see if the failure rate changes. For the firmware hypothesis, I could modify the recovery routine to be more robust — for example, adding a longer timeout or a different recovery sequence — and see if that changes the failure rate. I'd change one variable at a time and collect statistically meaningful data.

Fourth, I'd look for correlation between the failure and observable conditions. If the failure correlates with bus activity level, cable length, or temperature, that would favor the pull-up hypothesis. If it correlates with specific timing patterns or specific sequences of operations, that would favor the firmware hypothesis.

Finally, I'd bring both teams together to review the evidence. If the data clearly supports one hypothesis, I'd recommend a fix and verify it resolves the issue. If the data is inconclusive, I'd recommend addressing both — for example, strengthening the pull-ups and making the recovery routine more robust — while documenting which change actually resolved the issue.

**Possible follow-ups:**
- What specific measurements would you take to evaluate the pull-up resistor hypothesis?
- How would you design an experiment to isolate the firmware timing variable from the hardware variable?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a senior engineer on your team is convinced they know the root cause based on their experience with a similar device, but the evidence doesn't fully support their hypothesis — and they're pushing to implement a fix before the investigation is complete?

**Answer:** This is a common and challenging situation in failure investigations. The senior engineer's experience is valuable, but implementing a fix based on an unconfirmed hypothesis risks addressing the wrong cause and potentially introducing new problems — especially in a medical device where patient safety is at stake.

My approach would be to acknowledge the engineer's expertise and take their hypothesis seriously, while making it clear that the investigation process requires evidence before we implement changes. I'd ask them to walk me through their reasoning — what specific evidence from this failure points to their hypothesis, and what they believe the fix would accomplish. This serves two purposes: it shows respect for their experience, and it helps me understand the basis for their conclusion.

Next, I'd work with them to identify what evidence would confirm or refute their hypothesis. I'd ask: "If your hypothesis is correct, what would we expect to see in the data? What test would you propose to validate it?" This reframes the discussion from "implement the fix" to "validate the hypothesis," which is a more productive direction.

I'd also look for ways to test the hypothesis without committing to a full fix. For example, if the engineer believes a specific component is marginal, I'd propose measuring that component's behavior under the failure conditions, or running a targeted test that would expose the suspected weakness. If the hypothesis is correct, the test should show it; if not, we've gained valuable information.

I'd also ensure the investigation stays on track by maintaining a structured process — documenting all hypotheses, tracking what evidence supports or refutes each, and keeping the team focused on data collection. I'd make it clear that we're not ruling out any hypothesis prematurely, but we're also not implementing fixes until we have confidence in the root cause.

If the engineer continues to push, I'd have a private conversation to understand their concerns. They may have information I'm not aware of, or they may be under pressure from another stakeholder. I'd listen, address their concerns, and reiterate the importance of evidence-based decision-making — particularly for a medical device where a wrong fix could have serious consequences.

Finally, I'd keep the broader team informed of the investigation's progress and the rationale for the approach. Transparency helps prevent frustration and ensures everyone understands why we're taking the time to validate before implementing.

**Possible follow-ups:**
- How would you handle the situation if the senior engineer's hypothesis turns out to be correct, but the investigation delay caused a schedule slip?
- What would you do if the senior engineer went around you to implement the fix without your approval?