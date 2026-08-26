# debugging-failure-analysis — Day 36

## Q1: How would you approach a failure investigation where a medical device's firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory being copied is within bounds?

**Answer:** This is a classic case where the stack trace tells you *where* the fault manifested, but not necessarily *why*. When the addresses are valid and bounds are correct, I'd look beyond the memory copy itself and consider what could corrupt the execution context or the data being copied.

First, I'd check whether the fault is actually occurring *during* the copy or *after* it — a fault reported at the copy instruction could be a red herring if the stack has been corrupted and the return address is garbage. I'd examine the full register state at the fault, not just the program counter. If the link register or stack pointer looks abnormal, that points to stack corruption elsewhere.

Next, I'd consider the source data itself. If the copy source is a peripheral buffer or DMA destination, the data might be changing mid-copy. A DMA transfer completing during the copy could cause a bus contention issue or the source data could be in an inconsistent state. I'd check whether the copy source is volatile or shared with an interrupt context.

I'd also look at alignment. If the copy operation assumes aligned access but the source or destination address is occasionally misaligned, that could trigger a hard fault on some architectures. This would explain why the fault is intermittent — the alignment issue only occurs with certain data patterns or buffer positions.

Finally, I'd instrument the code to log the addresses, sizes, and a checksum of the data before the copy, and capture the full fault status register. This data would help determine whether the fault is consistent with a specific data pattern or buffer state.

**Possible follow-ups:** How would you distinguish between a stack overflow and a stack corruption from a wild pointer? What tools or debugger features would you use to capture the register state at the time of the fault?

---

## Q2: How would you approach debugging a medical device where the failure occurs only when the device is connected to a specific accessory cable, but never when using the test harness on the bench?

**Answer:** This is a strong indicator that the accessory cable is introducing an electrical characteristic that the test harness doesn't — resistance, capacitance, shielding, or pinout differences. I'd start by characterizing the cable itself: measure pin-to-pin resistance, insulation resistance, capacitance between conductors, and check the shield connection. I'd also verify the pinout against the schematic — a mis-wired cable could connect signals to the wrong pins, or connect a signal to ground.

Next, I'd compare the electrical environment between the accessory cable and the test harness. The cable might have longer conductors, higher capacitance, or different termination. If the cable carries power, I'd check for voltage drop under load — a marginal power rail could cause brownouts or reset issues. If it carries signals, I'd look at signal integrity: rise times, ringing, and crosstalk at the receiving end.

I'd also consider whether the cable creates a ground loop or changes the grounding topology. A cable with a shield connected at both ends could create a ground loop with the host system, introducing noise or offset into the measurement path.

Finally, I'd examine the connector itself — worn pins, intermittent contact, or contamination could cause marginal connections that only manifest under certain mechanical conditions. I'd try multiple samples of the same cable model to determine whether the issue is specific to one cable or characteristic of the design.

**Possible follow-ups:** What specific measurements would you take on the cable to characterize it? How would you determine whether the issue is the cable itself or the interaction between the cable and the device's input circuitry?

---

## Q3: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This points to a compatibility issue between the device's charging circuit and the specific charger's electrical characteristics. I'd start by characterizing both chargers — measuring their output voltage under no load and under load, their current capability, and their transient response. A charger with poor regulation or high output ripple could cause the charging circuit to behave differently.

I'd also look at the negotiation protocol. Many USB chargers use the D+ and D− lines to signal their current capability. If the device's charging circuit misinterprets the charger's signaling, it might request more current than the charger can supply, causing the charger to sag or the device to draw excessive current trying to compensate.

Another angle is the charger's inrush characteristics. Some chargers have a slow start or a current limit that behaves differently under load. If the device's charging circuit has a large input capacitance, the inrush current at connection could exceed the charger's capability, causing it to fold back or oscillate.

I'd also check whether the specific charger has any unusual features — like a different ground reference, leakage current, or a floating output — that could affect the device's charging circuit. I'd measure the current draw over time, not just at steady state, to see if the excessive current is continuous or transient.

**Possible follow-ups:** How would you determine whether the issue is in the device's charging circuit or in the charger's output characteristics? What safety considerations would you keep in mind when testing with a non-certified charger?

---

## Q4: How would you approach a failure investigation where a medical device's analog measurement is accurate at room temperature, but shows a growing offset error as the device warms up during continuous operation — and the offset returns to zero after the device cools down?

**Answer:** A temperature-dependent offset that recovers after cooling suggests a component with a temperature coefficient that's larger than expected, or a thermal gradient affecting the measurement path. I'd start by identifying which components in the analog front-end are temperature-sensitive — the sensor itself, the instrumentation amplifier, the reference voltage, or the ADC.

I'd use a thermal camera or thermocouples to map the temperature distribution across the board during operation. This would tell me whether the offset correlates with a specific component's temperature or with a thermal gradient across the PCB. A gradient across the input terminals of an instrumentation amplifier, for example, can create a thermocouple effect at the solder joints or in the copper traces, producing a voltage offset.

I'd also check the voltage reference. Many references have a temperature coefficient specified in ppm/°C, and a small drift in the reference would directly affect the measurement. I'd measure the reference voltage at room temperature and at operating temperature to see if it's drifting more than expected.

Another possibility is self-heating in the sensor itself. If the sensor is excited with a current or voltage, the power dissipation could heat the sensor element, changing its characteristics. This would explain why the offset grows over time as the sensor heats up.

I'd also look at the PCB layout — components near the analog path that dissipate significant power, like regulators or drivers, could create a thermal gradient that affects the measurement. I'd check whether the offset correlates with the power dissipation of nearby components.

**Possible follow-ups:** How would you distinguish between a component with a poor temperature coefficient and a thermal gradient issue in the PCB layout? What design changes would you consider to mitigate this issue?

---

## Q5: You're leading a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent communication failure is caused by a marginal pull-up resistor value on an I2C bus or by a firmware timing issue in the bus recovery routine. How would you handle this situation and structure the investigation?

**Answer:** The first step is to acknowledge that both hypotheses are plausible and that the goal is to find the root cause, not to win an argument. I'd structure the investigation to gather data that can distinguish between the two hypotheses rather than relying on opinion or experience.

I'd start by defining what "intermittent" means in this context — how often, under what conditions, and what the failure signature looks like. I'd collect data from the field or from reproduction attempts: bus waveforms, error codes, timestamps, and the state of the bus when the failure occurs.

For the hardware hypothesis, I'd measure the I2C bus characteristics — rise times, fall times, and signal levels at the receiving end. I'd check whether the pull-up values are within the I2C specification for the bus capacitance and speed. I'd also measure the bus capacitance to see if it's higher than expected, which would slow the rise time and potentially cause timing violations.

For the firmware hypothesis, I'd review the bus recovery routine — how it handles a stuck bus, whether it generates the correct number of clock pulses, and whether it properly releases the bus after recovery. I'd also look at the timing of the recovery routine relative to other operations — could it be interrupted, or could it conflict with another task accessing the bus?

I'd then design experiments that can discriminate between the two. For example, if the issue is marginal pull-ups, increasing the pull-up strength (temporarily, with a test fixture) should reduce or eliminate the failures. If the issue is firmware timing, adding a delay or changing the recovery sequence should affect the failure rate. I'd make one change at a time and track the failure rate.

I'd also consider that both could be contributing — a marginal pull-up value might make the bus more sensitive to timing issues in the firmware. The investigation should look for the combination of factors, not just a single root cause.

**Possible follow-ups:** How would you handle the situation if the data is inconclusive and both teams remain convinced of their hypothesis? What criteria would you use to determine when the investigation has gathered enough evidence to implement a fix?