# debugging-failure-analysis — Day 38

## Q1: How would you approach a failure investigation where a medical device's analog measurement is accurate at room temperature, but shows a growing offset error as the device warms up during continuous operation — and the offset returns to zero after the device cools down?

**Answer:** This is a classic temperature-dependent failure signature, and the first thing I'd do is characterize the thermal behavior precisely rather than jumping to component-level hypotheses. I'd start by instrumenting the device with thermocouples at key locations — the sensor itself, the analog front-end, the reference voltage source, and the ADC — while logging both temperature and the measured offset simultaneously. This tells me whether the offset tracks a specific component's temperature or the ambient/board temperature more broadly.

Once I have the thermal map, I'd look at the most likely culprits in order of probability. The reference voltage is a prime suspect — many voltage references have temperature coefficients that, while within datasheet specs individually, can produce noticeable offset drift if the reference is shared between the sensor excitation and the ADC reference. A ratiometric measurement should cancel reference drift, so if the design uses separate references for excitation and conversion, that's a red flag. Similarly, the instrumentation amplifier's offset voltage and bias currents drift with temperature, and if the gain-setting resistors have mismatched temperature coefficients, the gain error will drift too.

I'd also examine the PCB layout for thermocouple effects — if there are dissimilar metal junctions near a heat source (like a regulator or processor), small Seebeck voltages can develop that look exactly like offset drift. This is especially relevant in medical devices where the sensor signal is small (millivolt-level or less).

The systematic approach is: measure first, form hypotheses based on the thermal signature, then test each hypothesis with controlled experiments — for example, heating individual components with a heat gun while monitoring the offset, or cooling specific areas to see if the offset reverses. I'd also check whether the offset correlates with the device's internal temperature rise or with ambient temperature, since that distinguishes self-heating effects from environmental sensitivity.

**Possible follow-ups:** How would you determine whether the offset is coming from the sensor itself versus the signal conditioning chain? What design changes would you consider to make the measurement more temperature-stable?

---

## Q2: How would you approach a failure investigation where a medical device's firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory regions being copied are within their allocated bounds?

**Answer:** This is a frustrating class of bug because the obvious checks all pass. The key insight is that a hard fault during a memcpy with valid addresses and bounds usually means the fault isn't actually in the memcpy itself — it's a symptom of something that corrupted the system state earlier. The stack trace points to where the corruption manifests, not where it originated.

I'd start by expanding the investigation beyond the immediate fault location. First, I'd check whether the fault is a bus fault, usage fault, or hard fault — the fault status registers (CFSR, HFSR, BFAR, MMFSR) will tell you the precise reason. If it's a bus fault, the address that caused it might be different from the memcpy source/destination. If it's a usage fault, it could be an unaligned access or an invalid instruction.

Next, I'd look at what else was happening in the system around the time of the fault. Was an interrupt active? Was DMA running? Could a DMA transfer be writing into the memory region being copied? Could a stack overflow have corrupted the calling function's local variables? I'd examine the stack pointer at the time of the fault — if it's near the stack boundary, stack overflow is a strong candidate. I'd also check whether the memcpy source or destination could be in a memory region that's been remapped or disabled by a peripheral configuration change.

Another angle is to look at the data being copied. If the memcpy is copying a structure or buffer, is the size parameter correct? A common bug is passing a size that's larger than intended — for example, copying `sizeof(pointer)` instead of `sizeof(struct)`, or a struct that changed size when a field was added. The addresses might be valid, but the copy could be reading past the end of the source into unmapped memory.

I'd also consider whether this is a timing-dependent issue — for example, a race condition where one task is modifying the source buffer while another task is copying it. The fault might occur when the source buffer is in an inconsistent state. Adding a mutex or disabling interrupts around the copy would test this hypothesis.

Finally, I'd want to reproduce the fault in a controlled environment with fault injection — deliberately corrupting memory, forcing stack overflows, or triggering the suspected race condition to see if I can reproduce the same stack trace. If I can't reproduce it, I'd add more instrumentation to the field units to capture the fault status registers and stack contents at the moment of the fault.

**Possible follow-ups:** What specific fault status registers would you check first, and what would each one tell you? How would you distinguish between a stack overflow and a DMA corruption issue?

---

## Q3: How would you approach debugging a signal integrity issue where a high-speed SPI bus between a microcontroller and an ADC shows intermittent bit errors, but only when the device's motor driver is active?

**Answer:** This is a classic EMI/coupling problem, and the fact that it correlates with the motor driver is the key clue. The motor driver is almost certainly the noise source, and the SPI bus is the victim. The first step is to characterize the noise — I'd use a near-field probe to scan the PCB while the motor is running to identify where the noise is radiating from and what frequencies are involved. I'd also look at the SPI signals on an oscilloscope with the motor on and off, comparing the waveforms for ringing, overshoot, and noise injection on the clock and data lines.

The coupling path matters as much as the source. I'd ask: is the noise coupling through the ground plane (ground bounce from the motor current), through the power supply (shared rail between the motor driver and the ADC), or through radiated EMI (the motor cables or the PCB traces acting as antennas)? Each path has a different fix.

For ground bounce, I'd check whether the motor driver's return current shares a path with the SPI signals or the ADC's ground. A split ground plane or a star-point grounding scheme might be needed. For power supply coupling, I'd look at the decoupling on the ADC's supply pin — if the motor driver is drawing large current spikes, the supply rail could be dipping or ringing, and the ADC's internal reference could be affected. Adding a ferrite bead or a dedicated LDO for the analog section might help.

For radiated coupling, I'd look at the physical layout — are the SPI traces running parallel to the motor cables? Are they close to the motor driver's output traces? Increasing the spacing, adding ground guard traces, or routing the SPI on an internal layer between ground planes would reduce coupling.

I'd also check the SPI signal integrity itself — if the signals have excessive ringing or slow edges, the noise margin is reduced, making them more susceptible to coupling. Adding series termination resistors to match the trace impedance, or adjusting the drive strength of the microcontroller's GPIO pins, could improve the margin.

The systematic approach is: identify the noise source (motor driver), characterize the noise (frequency, amplitude, coupling path), then address the coupling path with layout changes, filtering, or shielding. I'd also verify the fix by running the motor at various speeds and loads while monitoring the SPI bus for errors over an extended period.

**Possible follow-ups:** How would you determine whether the coupling is through the ground plane versus radiated EMI? What specific layout changes would you prioritize if you found the SPI traces were running parallel to the motor cables?

---

## Q4: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This is a compatibility issue that points to a difference between the two chargers — and the key is to characterize those differences rather than assuming the device is at fault. I'd start by measuring the electrical characteristics of both chargers: output voltage under load, current capability, ripple, and — critically — the inrush current behavior when the device is connected. Many USB chargers have different soft-start characteristics, and some have a higher output capacitance that causes a larger inrush current when the device is plugged in.

The excessive current draw could be an inrush event — if the charger's output capacitance is large, the initial charging current can be much higher than the steady-state current. If the device's input circuit has a large bulk capacitor, the combination could cause a current spike that exceeds the charger's capability, potentially triggering its overcurrent protection or causing the charger to fold back. I'd measure the inrush current with a current probe and a high-speed oscilloscope to see the actual waveform.

Another possibility is that the specific charger has a different voltage profile — for example, a charger that negotiates a higher voltage (like 9V or 12V) via USB PD or a proprietary protocol, and the device's charging circuit isn't expecting that voltage. If the device's input protection or charging IC sees a higher-than-expected voltage, it might draw excessive current or enter an abnormal state. I'd check whether the charger is advertising a different voltage/current profile than the device expects.

I'd also consider the charger's ground reference — some chargers have a different ground topology (e.g., a floating ground or a different common-mode voltage), which could cause current to flow through unexpected paths. This is especially relevant in medical devices where isolation and leakage current are critical.

The systematic approach is: measure the charger's output characteristics, measure the device's input current waveform when connected to each charger, and compare. Then I'd test the device with a programmable power supply that can replicate the specific charger's characteristics to isolate which parameter (voltage, current capability, inrush, or ground reference) is causing the issue.

**Possible follow-ups:** How would you determine whether the excessive current is an inrush event versus a steady-state condition? What design changes would you consider to make the device more tolerant of different chargers?

---

## Q5: How would you handle a situation where you're leading a cross-functional failure investigation, and the firmware team believes the issue is a hardware timing problem while the hardware team believes it's a firmware race condition — but neither team has conclusive evidence, and the project schedule is tight?

**Answer:** The first thing I'd do is acknowledge that both teams have legitimate perspectives and that the goal is to find the root cause, not to assign blame. The tension between firmware and hardware teams is common in embedded systems because many failures sit at the interface — they're neither purely hardware nor purely firmware, but a combination of both.

I'd structure the investigation around evidence rather than opinions. The key is to design experiments that can discriminate between the two hypotheses. For example, if the firmware team believes the hardware has a timing issue, I'd ask them to specify the exact timing requirement they believe is being violated — what signal, what setup/hold time, what clock frequency. Then I'd ask the hardware team to measure that specific parameter on the actual hardware. If the hardware team believes it's a firmware race condition, I'd ask them to identify the specific race — what two operations are competing, and what the interleaving would look like.

I'd also look for data that both teams can agree on. The device logs, the oscilloscope captures, and the fault status registers are objective evidence. I'd bring both teams together to review the same data and ask each team to explain how their hypothesis fits the evidence. If neither hypothesis fully explains the data, that's a signal that the real cause might be something else entirely.

If the investigation is stalled, I'd consider bringing in an external perspective — someone who hasn't been involved in the project and can look at the problem fresh. This is often more effective than continuing to argue within the existing teams. I'd also consider fault injection or controlled experiments to test each hypothesis directly — for example, deliberately introducing a timing margin issue in firmware to see if it reproduces the failure, or deliberately slowing the clock to see if the failure disappears.

The key is to keep the investigation focused on evidence and to avoid letting the schedule pressure force a premature conclusion. I'd communicate to the stakeholders that a wrong fix is more expensive than a slightly delayed investigation, and that we need to reach a defensible root cause before implementing a corrective action.

**Possible follow-ups:** How would you handle a situation where one team refuses to accept evidence that contradicts their hypothesis? What would you do if the investigation is taking too long and management is pushing for a fix before root cause is confirmed?