# debugging-failure-analysis — Day 21

## Q1: How would you approach a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent communication error is caused by a marginal timing violation or a firmware race condition — the device occasionally fails to complete a sensor read within the required time window, and the error rate increases as the device warms up?

**Answer:** This is a classic firmware-hardware boundary problem where the disagreement itself is informative — it tells me the failure is intermittent and likely marginal, not a gross fault. I'd structure the investigation around three phases: characterization, isolation, and correlation.

First, I'd work to reproduce the failure consistently and characterize it. Since the error rate increases with temperature, I'd use an environmental chamber to sweep temperature and see if I can make the failure deterministic. I'd also instrument the system to capture as much data as possible around each failure — timestamps, sensor state, bus state, and any hardware status registers.

Second, I'd isolate the variable. The key question is whether the timing violation is real (the hardware genuinely doesn't meet the sensor's timing specification) or whether the firmware is violating the protocol (e.g., not respecting setup/hold times, polling too early, or not handling the sensor's busy signal). I'd use a logic analyzer or oscilloscope to capture the actual bus timing during failures and compare it against the sensor's datasheet requirements. I'd look specifically at: the time between the last clock edge and the sensor's data output, the time between the firmware's read command and the sensor's response, and whether the sensor's clock is within specification at the operating temperature.

Third, I'd correlate the captured waveforms with the firmware's execution state. If the firmware team can add debug hooks to log the exact sequence of operations around the failure, I can compare the software's view of events with the hardware's actual behavior. For example, if the firmware believes it waited the required time but the oscilloscope shows it didn't, that's a firmware timing issue. If the firmware waited correctly but the sensor still didn't respond in time, that's a hardware margin issue.

For the specific case of temperature-dependent failure, I'd also check whether the sensor's clock or data lines have excessive capacitance or marginal drive strength — these can cause timing degradation as temperature changes. I'd measure the signal rise/fall times and compare them against the sensor's input thresholds at both room temperature and elevated temperature.

The key principle is to avoid arguing about hypotheses and instead gather data that both teams can agree on. A shared waveform capture with annotated timing measurements is much more persuasive than either team's interpretation of the symptom.

**Possible follow-ups:**
- How would you decide whether to fix this as a firmware issue (e.g., adding delay or retry logic) versus a hardware issue (e.g., changing pull-up values or reducing bus capacitance)?
- What specific measurements would you take to determine whether the sensor's clock is marginal at elevated temperature?

---

## Q2: How would you approach a failure investigation where a medical device's power supply shows a periodic voltage dip on a 3.3V rail — the dip is about 200mV and lasts for roughly 50 microseconds, occurring every 100ms — and the device occasionally resets during these dips, but not consistently?

**Answer:** This pattern — a periodic, short-duration dip at a fixed interval — strongly suggests a load that's switching at a 10Hz rate. I'd start by identifying what's drawing current at that frequency. In a medical device, common candidates include: a sensor sampling cycle, a wireless beacon, an LED driver, or a motor controller. I'd correlate the dip timing with the firmware's activity schedule.

My approach would be systematic:

First, I'd verify the measurement itself. A 50-microsecond dip is short enough that probe technique matters. I'd measure at the decoupling capacitor closest to the load, using a short ground spring rather than a long ground lead, to avoid picking up ground bounce or probe inductance artifacts. I'd also measure at multiple points along the rail to understand whether the dip is localized or global.

Second, I'd identify the load. I'd use a current probe on the suspect load's supply pin and compare the current draw timing with the voltage dip timing. If they align, I've found the culprit. If not, I'd look for other periodic loads.

Third, I'd analyze the power supply's response. A 200mV dip on a 3.3V rail is about 6% — that's significant but not necessarily fatal. The question is whether the supply's control loop is responding appropriately or whether there's a stability issue. I'd check: the supply's load transient response specification, the output capacitance (is there enough bulk capacitance to handle the transient?), and the control loop's bandwidth (is it fast enough to correct a 50-microsecond dip?).

Fourth, I'd investigate why the reset is intermittent. If the dip is consistent, why doesn't the device always reset? I'd check the microcontroller's brown-out reset threshold — if the dip brings the rail close to but not always below the threshold, small variations in temperature, supply voltage, or component tolerance could push it over the edge intermittently. I'd also check whether the reset is actually caused by the voltage dip or by something else that happens to coincide with it (e.g., a glitch on the reset pin, or a firmware watchdog timeout caused by the disturbance).

Finally, I'd consider the fix options. Depending on the root cause, these could include: adding bulk capacitance to reduce the dip magnitude, increasing the supply's loop bandwidth, moving the load's switching frequency away from a resonant frequency, or adding a brown-out detector with a more appropriate threshold. The key is to understand the margin — how close is the rail to the reset threshold, and what's the worst-case combination of conditions?

**Possible follow-ups:**
- How would you determine whether the dip is caused by the load's current draw or by the power supply's control loop instability?
- What would you look for to determine whether the reset is caused by the voltage dip or by a coincidental event?

---

## Q3: How would you approach a failure investigation where a medical device's analog front-end produces accurate readings on the bench, but shows a consistent offset error when connected to the patient cable — and the offset varies between different cable samples?

**Answer:** This is a classic interface problem — the bench setup and the patient cable present different electrical conditions to the analog front-end. The fact that the offset varies between cable samples tells me the cable itself is part of the problem, not just the connection.

I'd start by characterizing the electrical differences between the bench setup and the patient cable. The most likely culprits are: contact resistance at the connector, cable resistance (especially if the cable is long or uses thin conductors), shield/guard configuration, and parasitic capacitance. I'd measure each cable sample's resistance, capacitance, and insulation resistance, and correlate those measurements with the observed offset.

The most common cause of a cable-dependent offset in a medical device is a ground or reference mismatch. If the analog front-end uses a single-ended measurement and the patient cable introduces resistance in the ground return path, the ground potential at the sensor will differ from the ground potential at the ADC. This creates a voltage offset that's proportional to the current flowing through the ground path. I'd check: is the sensor's ground connected to the same ground reference as the ADC? Is there a separate sense line for the reference? Is the cable's shield connected at both ends or one end?

Another common cause is contact resistance at the connector. If the connector pins have high or variable contact resistance, the signal path resistance changes, which can create an offset if the sensor's output impedance is significant. I'd measure the contact resistance of each pin in the connector and look for any that are out of specification.

I'd also consider the sensor's output impedance and the ADC's input impedance. If the ADC's input impedance is not significantly higher than the cable's resistance, the voltage divider effect will create a gain error that looks like an offset. This would explain why the offset varies between cables — different cables have different resistances.

My investigation would proceed as follows: measure the cable parameters, measure the front-end's input impedance, calculate the expected offset from the resistance and current values, and compare with the observed offset. If they match, I've confirmed the mechanism. If not, I'd look for other factors — perhaps the cable's capacitance is causing settling time issues, or the shield is picking up interference.

The fix would depend on the root cause: a four-wire (Kelvin) connection for the sensor, a buffer amplifier with higher input impedance, a dedicated sense line for the reference, or a connector with lower and more consistent contact resistance.

**Possible follow-ups:**
- How would you distinguish between a contact resistance problem and a ground reference mismatch?
- What design changes would you consider to make the measurement insensitive to cable variations?

---

## Q4: How would you approach a failure investigation where a medical device's firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory being copied is within bounds?

**Answer:** This is a frustrating scenario because the obvious causes — invalid pointers, out-of-bounds access, unaligned access — have been ruled out. When the stack trace is consistent but the addresses are valid, I'd look beyond the memory copy itself and consider what's happening around it.

My approach would be to question the assumption that the fault is caused by the memory copy operation. The stack trace shows where the fault was detected, but not necessarily where the corruption occurred. The actual root cause could be: memory corruption elsewhere that's only detected during the copy, a stack overflow that corrupts the copy's local variables, a race condition where another interrupt or task modifies the source or destination during the copy, or a hardware issue like a marginal memory bus or ECC error.

I'd start by examining the fault handler's captured state more carefully. What's the fault status register telling me? Is it a bus fault, a usage fault, or a hard fault? A bus fault would suggest a hardware access problem — perhaps the memory region isn't accessible at that moment (e.g., a peripheral is powered down, or a DMA controller is holding the bus). A usage fault would suggest an instruction-level problem — perhaps an unaligned access or an undefined instruction. The fault status register often points to the specific cause.

Next, I'd look at the memory copy operation itself. Is it using a DMA controller or a CPU loop? If it's DMA, I'd check the DMA configuration — is the transfer size correct? Is the DMA channel shared with another peripheral? Could a DMA interrupt be firing at the wrong time and corrupting the transfer? If it's a CPU loop, I'd check the compiler's optimization — could the compiler be reordering operations or using a word-copy instruction that requires alignment?

I'd also investigate the timing context. When does the fault occur? Is it always during the same point in the system's operation? Does it correlate with a specific interrupt or task switching event? If the copy is happening while another interrupt is active, there could be a reentrancy issue — the interrupt handler might be calling the same copy function or modifying the same memory.

Another angle is memory protection. If the system uses an MPU (Memory Protection Unit), I'd check whether the MPU configuration is correct — could the copy be accessing a region that's temporarily marked as privileged-only or execute-never? Could the MPU be configured with overlapping regions that cause unexpected access violations?

Finally, I'd consider hardware issues. If the memory is external (e.g., SDRAM or external flash), I'd check the timing margins — could the memory be marginal at certain temperatures or voltages? Could there be a signal integrity issue on the memory bus that causes occasional read or write errors? I'd run a memory test (e.g., walking 1s and 0s, or a pseudo-random pattern) over an extended period to look for intermittent failures.

The key principle is to not assume the stack trace tells the whole story. The fault is detected at the copy, but the cause could be anywhere in the system. I'd systematically rule out each possibility: memory corruption, stack overflow, race condition, MPU misconfiguration, and hardware marginality.

**Possible follow-ups:**
- How would you determine whether the fault is caused by memory corruption that occurred earlier versus a problem with the copy operation itself?
- What specific fault status registers would you examine, and what would each indicate?

---

## Q5: You're leading a cross-functional investigation into a medical device failure where the device's motor (used for a therapeutic function) stopped mid-procedure. The device logs show a motor current spike followed by a stall condition, and the fuse is blown. The mechanical team believes the electrical design is at fault, and the electrical team believes the mechanical design caused an overcurrent condition. How would you handle this situation and structure the investigation?

**Answer:** This is a situation where the two teams are each pointing at the other, and the pressure is high because it's a medical device that failed during a procedure. My first priority is to establish a structured, evidence-based investigation that both teams can participate in without feeling blamed. The goal is to find the root cause, not to assign fault.

I'd structure the investigation in four phases: evidence collection, failure analysis, correlation, and corrective action.

**Phase 1: Evidence collection.** Before any analysis, I'd secure the failed device and preserve all evidence. This includes: the device itself, the motor, the fuse, the PCB, and any logged data. I'd also collect the device's usage history — how long it had been in service, how many procedures it had completed, and any maintenance records. I'd photograph the device and document the physical condition before any disassembly.

**Phase 2: Failure analysis.** I'd break this into parallel workstreams:

- *Electrical analysis:* Examine the fuse to determine the nature of the overcurrent — a fast, high-current event (e.g., a short circuit) versus a slower, sustained overcurrent (e.g., a stalled motor). The fuse's fracture pattern and any arcing marks can tell us a lot. I'd also examine the motor driver circuit — are the MOSFETs or H-bridge components damaged? Is there evidence of a short circuit on the PCB? I'd measure the motor's winding resistance and check for insulation breakdown.

- *Mechanical analysis:* Examine the motor and its mechanical linkage. Is there evidence of binding, wear, or foreign material? Could the motor have been mechanically stalled by the patient's movement or by a mechanical failure in the device? I'd check the gearbox (if present), the shaft, and any bearings. I'd also look for signs of overheating — discoloration, melted plastic, or burnt insulation.

- *Log analysis:* The device logs show a current spike followed by a stall. I'd examine the timing — how long did the current spike last before the stall? Was the current within the motor driver's specification? Were there any prior events — previous current spikes, temperature increases, or unusual motor behavior?

**Phase 3: Correlation.** The key question is: did the electrical event cause the mechanical failure, or did the mechanical failure cause the electrical event? I'd look for evidence that answers this. For example:

- If the fuse shows a fast, high-current fracture pattern, that suggests a short circuit — possibly in the motor windings or the driver circuit. This could be caused by insulation breakdown (electrical) or by mechanical damage to the motor (e.g., a wire chafed by a moving part).

- If the motor shows signs of mechanical binding (e.g., a seized bearing or a jammed gear), that would cause the motor to draw high current, which could blow the fuse. This would point to a mechanical root cause.

- If the motor windings show signs of overheating (discolored insulation, burnt smell), that suggests the motor was running against a mechanical load for an extended period before the fuse blew.

I'd also look at the sequence of events in the log. Did the current spike occur suddenly (suggesting a short circuit) or gradually (suggesting increasing mechanical load)? Did the motor speed decrease before the current spike? These details can help distinguish between the two scenarios.

**Phase 4: Corrective action.** Once the root cause is established, I'd work with both teams to develop corrective actions. If it's an electrical issue, the fix might be: a more robust motor driver, better overcurrent protection, or a fuse with a different rating. If it's a mechanical issue, the fix might be: a more robust mechanical design, better tolerances, or a sensor that detects mechanical binding before it causes a failure. In either case, I'd also consider whether the device needs a more comprehensive monitoring system — for example, current sensing that can detect an abnormal motor condition before it becomes critical.

Throughout the investigation, I'd keep both teams informed and involved. I'd hold regular status meetings where each team presents their findings, and I'd make it clear that the goal is to understand the failure mechanism, not to assign blame. This approach helps maintain collaboration and ensures that the final root cause is supported by evidence, not by whichever team argues more persuasively.

**Possible follow-ups:**
- How would you handle a situation where the evidence is inconclusive — for example, the fuse is blown but there's no clear evidence of either an electrical short or a mechanical jam?
- What specific tests would you run on the motor and the motor driver circuit to determine which failed first?