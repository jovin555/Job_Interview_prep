# debugging-failure-analysis — Day 49

## Q1: How would you approach a failure investigation where a medical device's analog measurement channel is accurate during bench testing, but shows intermittent spikes when the device is connected to a specific model of infusion pump — and the spikes correlate with the pump's motor operation?

**Answer:** This is a classic conducted or radiated interference problem where the coupling path only exists when two specific systems are physically connected and operating together. I'd structure the investigation around three questions: what's the coupling path, what's the noise source characteristic, and why does the victim circuit respond the way it does.

First, I'd characterize the interference precisely. I'd connect the device to the infusion pump exactly as it's used clinically, then use a differential probe across the analog front-end input and an oscilloscope triggered on the spike events. I'd want to know the spike's amplitude, duration, rise time, and repetition rate, and whether it appears at the sensor input, the amplifier output, or the ADC input — that tells me where the coupling enters the signal chain.

Next, I'd isolate the coupling path. The pump's motor is likely a brushed DC motor with commutator noise, or a brushless motor with PWM drive. The noise could couple through the patient cable (common-mode current on the cable shield or conductors), through the ground connection between the two devices, or radiatively into the PCB. I'd test each path systematically: disconnect the ground connection between devices while maintaining signal integrity (using an isolated measurement setup), add a ferrite clamp on the cable to see if the spikes attenuate, and use near-field probes to scan the PCB while the pump operates to identify where the interference enters the board.

I'd also look at the grounding architecture. Medical devices often have isolated patient connections, but the isolation barrier can be compromised by parasitic capacitance, especially at higher frequencies. If the pump's motor noise is coupling through the isolation capacitance, I'd expect to see common-mode current on the cable that converts to differential-mode noise at the analog front-end due to impedance imbalance.

The fix would depend on the coupling path: common-mode chokes on the cable, improved filtering at the analog input, better grounding or shielding strategy, or a combination. I'd also verify the fix doesn't degrade the device's IEC 60601-1-2 EMC performance or patient isolation characteristics.

**Possible follow-ups:** How would you determine whether the interference is common-mode or differential-mode? What measurements would you take to characterize the noise source on the infusion pump side?

---

## Q2: How would you approach a failure investigation where a medical device's firmware occasionally enters a hard fault handler, and the stack trace consistently points to a floating-point operation — but the fault occurs at different points in the code each time, and the device uses a microcontroller with a hardware FPU?

**Answer:** A hard fault consistently pointing to floating-point operations, but at different code locations, suggests something systematic about the FPU state or the floating-point environment rather than a logic error in any single calculation. I'd approach this by examining several layers of the system.

First, I'd check the FPU configuration and context handling. If the RTOS or interrupt handlers aren't properly saving and restoring FPU registers on context switches, a task or ISR could corrupt the FPU state, causing a fault when another task later performs a floating-point operation. This is a well-known issue with Cortex-M processors — the FPU registers are banked, and if the OS doesn't enable lazy stacking or properly save the extended register file on context switches, the FPU state can be corrupted. I'd verify the FPU is enabled correctly at startup, check the RTOS configuration for FPU context saving, and review the interrupt handler entry/exit sequences.

Second, I'd look at memory alignment and stack depth. Floating-point operations often use larger stack frames, and if a task's stack is marginally sized, a deep call path involving floating-point could overflow the stack. The fault would appear at different code locations because the stack overflow manifests when the corrupted stack pointer is used, not necessarily at the point of overflow. I'd measure actual stack usage with a stack watermark or fill pattern, and check whether the fault correlates with specific tasks or interrupt nesting levels.

Third, I'd examine whether the fault correlates with specific data values. A NaN or infinity propagating through calculations can cause faults in some FPU configurations, especially if the FPU is configured to trap on invalid operations. I'd check whether the fault occurs more frequently when certain sensor values are out of range, and whether the firmware validates floating-point inputs before use.

I'd also consider whether the fault is actually a memory access issue that happens to be reported at a floating-point instruction. The fault handler's stack trace shows where the fault was detected, but the root cause could be a corrupted stack pointer, a wild pointer write that corrupted memory, or a DMA operation that overwrote code or data. I'd examine the fault status registers to determine the exact fault type — whether it's a bus fault, usage fault, or memory management fault — and whether the address reported is valid.

Finally, I'd try to reproduce the fault under controlled conditions with fault injection: deliberately corrupt the FPU state, fill the stack with patterns, and feed boundary-value data to the floating-point routines to see which condition reproduces the fault signature.

**Possible follow-ups:** How would you verify that the RTOS is properly saving FPU context on context switches? What fault status registers would you examine first, and what would they tell you?

---

## Q3: How would you approach a production issue where a newly assembled batch of PCBs shows a higher-than-expected failure rate during burn-in testing, with failures characterized by a specific voltage rail slowly drooping over several hours until the device resets — and the rail's regulator tests within specification when removed from the board?

**Answer:** This pattern — a rail that droops slowly over hours, with the regulator testing fine in isolation — points me toward something that changes over time or with temperature, rather than a static defect. I'd approach this as a systematic investigation with several parallel tracks.

First, I'd characterize the failure precisely. I'd instrument a failing board with a data logger on the suspect rail, measuring voltage and current over the full burn-in period. I'd also monitor the regulator's input voltage, the load current, and the board temperature at several points. The key question is whether the droop is caused by the regulator's output degrading, the load current increasing, or the input supply sagging. I'd also check whether the droop rate correlates with board temperature — if the board heats up over time and the failure accelerates, that suggests a thermal component.

Second, I'd look at the load. A slowly increasing current draw could indicate a component that's degrading under stress — a marginal semiconductor junction, a capacitor with leakage that increases with temperature, or a solder joint that's developing resistance. I'd use a thermal camera to look for hot spots on the board during burn-in, and I'd probe the rail at multiple points to see if the droop is uniform or localized. If the droop is localized near a specific component, that narrows the search considerably.

Third, I'd examine the regulator's behavior more carefully. A regulator can test fine under static conditions but fail under dynamic load or at elevated temperature. I'd check the regulator's thermal performance — is the solder connection to the thermal pad adequate? Is the PCB copper pour for heat dissipation properly designed? I'd also look at the regulator's compensation network: if a compensation capacitor has a poor temperature coefficient or is the wrong value, the regulator's loop stability could degrade as the board warms up, causing the output to droop under load.

Fourth, I'd compare the failing boards against known-good boards from previous batches. I'd review the assembly records — were there any changes in component lots, solder paste, or reflow profiles? I'd also check whether the failing boards share a common characteristic: same assembly shift, same solder paste batch, same component date codes. This could point to a materials or process issue rather than a design issue.

Finally, I'd consider the burn-in test itself. Is the test condition representative of actual use? If the burn-in test loads the rail more heavily than real-world use, the failure might be a test artifact rather than a field failure. But regardless, a rail that droops over hours indicates a real reliability concern that needs to be understood before the boards ship.

**Possible follow-ups:** How would you determine whether the droop is caused by the regulator's output degrading or the load current increasing? What specific measurements would you take to distinguish between these two scenarios?

---

## Q4: How would you approach a failure investigation where a medical device's real-time clock (RTC) loses time — not by drifting, but by jumping forward or backward by several hours — and the jumps don't correlate with any user interaction, power events, or firmware activity logs?

**Answer:** An RTC that jumps by hours rather than drifting suggests the time value itself is being corrupted or overwritten, rather than the oscillator running fast or slow. I'd approach this by examining the possible mechanisms for time corruption, working from the most likely to the least likely.

First, I'd look at the RTC's power architecture. Many RTCs have a separate backup battery or supercapacitor supply to maintain time when the main power is off. If the backup supply is marginal — perhaps a weak battery or a leaky decoupling capacitor — the RTC could experience a brownout that causes it to reset or corrupt its internal registers. The jump could occur when the RTC's power crosses a threshold and the device re-initializes from an incorrect value. I'd measure the backup supply voltage over time, including during power transitions, and check whether the RTC's power-fail flag is being set.

Second, I'd examine the RTC's communication interface. If the RTC is accessed over I2C or SPI, a corrupted read or write could load an incorrect time value. A glitch on the bus — perhaps from an interrupt handler that runs during the RTC access, or from a marginal pull-up value — could cause the firmware to read garbage data and write it back. I'd review the firmware's RTC access routines for proper bus locking, error checking, and retry logic, and I'd check whether the RTC has a write-protection mechanism that's being properly used.

Third, I'd consider the RTC's alarm or wake-up features. Some RTCs have alarms that can trigger interrupts, and if the alarm registers are corrupted, the RTC could behave unexpectedly. I'd check whether the RTC's alarm flags are being set and whether the firmware properly clears them. I'd also look at whether the RTC has a tamper detection or timestamp feature that could be interfering.

Fourth, I'd look at environmental factors. RTC crystals are sensitive to shock and vibration, and a mechanical shock could cause the oscillator to momentarily stop or run erratically, potentially causing the RTC to lose counts. But a jump of several hours would require the oscillator to be off for that duration, which would be noticeable in the device's operation. More likely, the jump is a register-level corruption.

I'd also examine the firmware's time-setting logic. If the device synchronizes time from an external source — a wireless module, a host system, or a user interface — a corrupted sync message could set the time incorrectly. I'd review the time-sync protocol for validation checks, and I'd check whether the jumps correlate with any communication events, even if they're not logged.

Finally, I'd try to reproduce the issue under controlled conditions. I'd subject the device to power cycling, bus traffic, and vibration while monitoring the RTC's registers in real-time, looking for the moment when the time value changes. I'd also add temporary instrumentation — perhaps logging the RTC's raw register values at high frequency — to capture the exact sequence of events leading to a jump.

**Possible follow-ups:** How would you distinguish between the RTC's internal registers being corrupted versus the firmware writing an incorrect value? What instrumentation would you add to capture the moment of the jump?

---

## Q5: How would you handle a situation where you're leading a cross-functional failure investigation, and you discover that the root cause points to a design decision made by a senior engineer who is still on the team — and the finding could reflect poorly on them or create tension within the group?

**Answer:** This is a situation where the technical investigation is straightforward, but the human dynamics require careful handling. The goal is to resolve the technical issue while maintaining a constructive team environment and preserving the engineer's dignity — because the finding is about a design decision, not about their competence as an engineer.

First, I'd make sure the evidence is solid before sharing the finding. I'd review the data with fresh eyes, confirm the root cause through multiple lines of evidence, and make sure I can articulate the finding clearly and objectively. I'd also consider whether the design decision was reasonable given the information available at the time — many failures are the result of decisions that were sound under the original constraints but didn't account for factors that emerged later. This context matters for how the finding is framed.

Second, I'd speak with the senior engineer privately before presenting the finding to the broader team. I'd share the evidence, explain the analysis, and give them the opportunity to provide additional context or challenge the conclusion. This isn't about seeking permission — it's about ensuring they're not blindsided and that I have the full picture. I'd frame the conversation around the technical finding, not the person: "The evidence points to X as the root cause. I wanted to review this with you first because I know you were involved in that design area, and I want to make sure I haven't missed anything."

Third, I'd focus the team discussion on the process and the fix, not the blame. When presenting the finding, I'd emphasize that the goal is to understand what happened so we can prevent recurrence, and I'd frame the design decision in its historical context — what was known at the time, what constraints existed, and why the decision made sense then. This shifts the conversation from "who made the mistake" to "what can we learn."

Fourth, I'd involve the senior engineer in developing the corrective action. This serves two purposes: it leverages their expertise to design a robust fix, and it gives them ownership of the solution rather than leaving them associated only with the problem. It also signals to the team that the investigation is about improvement, not punishment.

Finally, I'd consider the broader implications. If the design decision was influenced by systemic factors — schedule pressure, incomplete requirements, inadequate review processes — the corrective action should address those factors, not just the technical fix. This is where the investigation can add real value beyond solving the immediate problem.

**Possible follow-ups:** How would you handle the situation if the senior engineer disagrees with the finding and becomes defensive? How would you present the finding to the broader team in a way that maintains trust and psychological safety?