# debugging-failure-analysis — Day 50

## Q1: How would you approach a failure investigation where a medical device's firmware occasionally enters a hard fault handler, and the stack trace consistently points to a floating-point operation — but the fault occurs at different points in the code each time, and the device uses a microcontroller with a hardware FPU?

**Answer:** This is a classic case where the stack trace is telling us *where* the fault manifests, not necessarily *why*. The fact that the fault always points to a floating-point operation but at different code locations suggests something systematic about the FPU state or the data being processed, rather than a bug in any single function.

My first step would be to determine whether the fault is actually an FPU exception (like an invalid operation, division by zero, or inexact result) or whether the FPU is just where the corruption happens to surface. I'd check the hard fault status registers — specifically the Configurable Fault Status Register (CFSR) — to see which exception type fired. If it's a bus fault or usage fault rather than a precise FPU exception, that changes the investigation entirely.

Assuming it is an FPU-related fault, I'd look at several areas:

1. **FPU context preservation**: If the RTOS or interrupt handlers aren't properly saving and restoring FPU registers (especially in Cortex-M4/M7 parts with lazy stacking), a context switch can leave the FPU in an inconsistent state. I'd verify that the FPU is enabled, that the automatic context saving is configured correctly, and that any manual context-switch code handles the extended register set.

2. **Stack alignment**: FPU instructions often require 8-byte stack alignment. If a function with FPU operations is called from a context where the stack isn't properly aligned, you can get a usage fault. This would explain why the fault appears at different locations — it depends on the call path at that moment.

3. **Data corruption**: If a buffer overflow or DMA issue is corrupting the floating-point data itself, you could get NaN or infinity values that trigger FPU exceptions when operated on. I'd examine whether the faulting values are plausible — logging the input operands when the fault occurs would help.

4. **Voltage or clock integrity**: FPU operations are sensitive to marginal supply voltage or clock timing. If the fault is more frequent at certain temperatures or after the device has been running for a while, I'd suspect a power integrity issue rather than a firmware bug.

I'd instrument the code to capture the FPU status registers and the offending operand values at the moment of the fault, then correlate those with the specific code location. If the same invalid data pattern appears across different fault locations, that points to a data corruption source. If the operands are always valid but the operation itself faults, that points to an FPU configuration or context-switching issue.

**Possible follow-ups:**
- How would you distinguish between a precise FPU exception and a fault that merely surfaces during an FPU instruction due to memory corruption elsewhere?
- What specific diagnostic information would you want to capture in the fault handler to aid this investigation?

---

## Q2: How would you approach a production issue where a newly assembled batch of PCBs shows a higher-than-expected failure rate during burn-in testing, with failures characterized by a specific voltage rail slowly drooping over several hours until the device resets — and the rail's regulator tests within specification when removed from the board?

**Answer:** This pattern — a rail that degrades over hours rather than failing immediately — suggests something is progressively loading the rail or the regulator is thermally degrading. The fact that the regulator passes when tested in isolation is a critical clue: the problem likely involves the interaction between the regulator and the load, or something about the board assembly itself.

I'd structure the investigation in stages:

**Stage 1: Characterize the failure precisely.** I'd instrument several failing boards with high-resolution data logging on the drooping rail — measuring the voltage at the regulator output, at the load, and at intermediate points. I'd also monitor the regulator's input voltage, current draw, and temperature. The key question is whether the droop is linear, exponential, or stepwise — that tells you about the mechanism. I'd also check whether the droop rate correlates with ambient temperature or load activity.

**Stage 2: Isolate the cause.** Several hypotheses come to mind:

- **Marginal solder joints**: A cold solder joint or insufficient wetting on a high-current path could have higher-than-expected resistance that increases as the joint heats up. This would cause the voltage at the load to droop even if the regulator output is stable. I'd check the voltage at the regulator output versus at the load — if they diverge over time, that's a resistive path issue.

- **Component derating**: A capacitor with marginal voltage rating or an inductor approaching saturation could degrade as temperature rises. I'd check whether any components on the rail are running hotter than expected using a thermal camera during the burn-in.

- **Regulator thermal shutdown or foldback**: Even if the regulator passes bench testing, the thermal environment on the actual board might be different — poor thermal vias, adjacent heat sources, or inadequate copper pour. I'd measure the regulator's case temperature during the failure and compare it to the derating curve.

- **Process variation**: Since this is a new batch, I'd check whether any assembly parameters changed — solder paste, reflow profile, or component sourcing. I'd compare the failing batch against known-good batches, looking at solder joint quality under X-ray and checking component date codes.

**Stage 3: Correlate and confirm.** Once I have a hypothesis, I'd deliberately reproduce it — for example, by adding a known marginal joint to a test board or by heating the suspect component — and confirm the same failure signature appears.

The key discipline here is to avoid jumping to "the regulator is bad" just because it fails in isolation. The regulator is one component in a system, and the failure mode is a system-level symptom.

**Possible follow-ups:**
- What specific measurements would you take to distinguish between a regulator problem and a load-side problem?
- How would you determine whether this is a systematic design issue versus a manufacturing process variation?

---

## Q3: How would you approach debugging a medical device where the analog front-end for a pressure sensor shows a periodic 50mV spike on the output every 100ms, exactly synchronized with the system's wireless beacon interval — and the spike corrupts the measurement?

**Answer:** The synchronization with the wireless beacon is the key clue here — this is almost certainly an EMI coupling issue where the RF transmission is injecting noise into the analog front-end. The 50mV spike is large enough to corrupt a pressure sensor reading, so this is a real signal integrity problem, not just measurement noise.

I'd approach this systematically:

**Step 1: Characterize the coupling path.** I need to understand how the RF energy is getting into the analog front-end. The main possibilities are:

- **Conducted coupling**: The wireless module and the analog front-end share a power rail or ground path. During transmission, the module draws a current pulse that causes a voltage drop or ground bounce that couples into the analog circuitry. I'd check the power supply to the analog front-end during a beacon transmission — looking for dips or spikes on the rail.

- **Radiated coupling**: The RF energy is coupling directly into the analog traces, the sensor cable, or the PCB traces. This is more likely if the analog front-end traces act as antennas at the wireless frequency. I'd use a near-field probe to map where the RF energy is strongest during transmission.

- **Ground coupling**: The analog ground and the RF ground might not be properly separated, allowing return currents from the RF section to flow through the analog ground plane.

**Step 2: Isolate the path.** I'd try several experiments:

- Power the analog front-end from a separate, clean supply (battery or bench supply) while the rest of the system runs normally. If the spikes disappear, it's a conducted coupling issue through the power rails. If they persist, it's radiated coupling.

- Temporarily disable the wireless transmission (but keep the module powered) to confirm the spike is truly RF-related and not a digital noise issue from the module's state changes.

- Move the sensor and cable away from the antenna to see if the spike amplitude changes — that would confirm radiated coupling through the sensor path.

**Step 3: Implement and verify countermeasures.** Depending on the coupling path:

- For conducted coupling: Add ferrite beads or PI filters on the analog power rail, ensure proper decoupling at the analog front-end, and check that the analog and digital/RF grounds are properly separated and joined at a single point.

- For radiated coupling: Improve shielding on the sensor cable, add a ground guard trace around the analog front-end, or reposition the antenna relative to the analog circuitry.

- For ground coupling: Review the ground plane layout — ensure the RF return current doesn't flow through the analog ground region.

**Step 4: Verify the fix doesn't introduce new problems.** After implementing a countermeasure, I'd verify the spike is gone across the full operating range — different beacon intervals, different power levels, and with the device in various orientations. I'd also check that the fix doesn't degrade wireless performance or EMC compliance.

The critical insight is that the synchronization tells you the noise source, but you still need to find the coupling path — and the fix depends entirely on which path it is.

**Possible follow-ups:**
- How would you determine whether the coupling is through the power rail or through the sensor cable itself?
- What trade-offs would you consider between hardware fixes (filtering, shielding) and firmware fixes (blanking the ADC during transmission)?

---

## Q4: How would you approach a failure investigation where a medical device's real-time clock (RTC) drifts significantly — losing about 5 minutes per day — but only when the device is in a low-power sleep mode? The RTC uses an external 32.768 kHz crystal.

**Answer:** A 5-minute-per-day drift is enormous — that's roughly 3,500 parts per million, which is far beyond any reasonable crystal tolerance. A typical 32.768 kHz crystal should be accurate to within 20–100 ppm. This magnitude of drift points to something fundamentally wrong with the oscillator circuit or its environment during sleep mode, not a calibration issue.

The fact that it only happens in sleep mode is the critical clue. During sleep, the main processor and most peripherals are powered down, which changes the electrical and thermal environment around the RTC. I'd consider several mechanisms:

**1. Insufficient drive level or marginal oscillation.** In sleep mode, the power supply voltage might be lower (if the device drops to a lower-voltage rail) or the power supply noise characteristics might change. If the crystal oscillator circuit is marginal — wrong load capacitance, excessive stray capacitance, or insufficient drive — it could be operating in an unstable mode where it occasionally skips cycles or oscillates at a slightly different frequency. I'd check the oscillator's startup margin and measure the actual waveform at the crystal pins during sleep mode.

**2. Load capacitance mismatch.** The crystal's frequency accuracy depends on the load capacitance being correct. If the circuit's effective load capacitance is significantly off from the crystal's specified load, the frequency will be offset. This could be a design issue that's always present but only noticeable during sleep because the RTC is the only active clock. I'd verify the crystal's specified load capacitance against the actual circuit capacitance (including stray capacitance from PCB traces and pin capacitance).

**3. Temperature effects.** If the device is in a low-power state, the internal temperature might be different than during active operation — possibly cooler if the processor isn't generating heat. Some crystals have significant temperature coefficients, but even a poor crystal shouldn't drift 3,500 ppm over normal temperature ranges. This alone wouldn't explain the magnitude.

**4. Power supply noise or droop during sleep.** If the RTC's power supply is noisy or droops during sleep mode — perhaps because the main regulator is disabled and a low-power LDO takes over — the oscillator could be affected. I'd measure the RTC's supply voltage and the crystal waveform during sleep mode to check for anomalies.

**5. Clock source switching.** Some microcontrollers allow the RTC to be clocked from different sources (external crystal, internal RC oscillator, or the main system clock divided down). If the firmware or a configuration register is causing the RTC to switch to an internal RC oscillator during sleep mode — perhaps as a power-saving measure — that would explain the massive drift. Internal RC oscillators are typically accurate to only 1–2%, which matches the observed drift. I'd verify the RTC clock source configuration in both active and sleep modes.

My investigation would start by confirming the actual clock source during sleep mode — reading the relevant configuration registers and checking whether the firmware changes any clock settings when entering sleep. I'd also measure the crystal waveform during sleep to confirm it's actually oscillating at the correct frequency. If the crystal is oscillating correctly but the RTC is still drifting, the issue is in the RTC's clock path or configuration. If the crystal itself is off-frequency during sleep, the issue is in the oscillator circuit.

**Possible follow-ups:**
- How would you distinguish between a firmware issue (clock source switching) and a hardware issue (oscillator circuit problem)?
- What measurements would you take to verify the crystal is actually oscillating at 32.768 kHz during sleep mode?

---

## Q5: You're leading a cross-functional failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent communication failure is caused by a marginal PCB layout issue or by a firmware timing violation — the device occasionally fails to complete a sensor read over SPI, and the failure rate increases as the device warms up. How would you handle this situation and structure the investigation?

**Answer:** This is a situation where the temperature dependence is actually the most valuable clue, because it gives us a physical variable to work with. Both teams have plausible hypotheses — a marginal layout could show timing degradation as resistance increases with temperature, and a firmware timing violation could become more likely as clock margins shift. My job as the lead is to structure an investigation that lets the evidence discriminate between these hypotheses rather than letting the teams argue from theory.

**Step 1: Establish a shared understanding of the failure.** I'd bring both teams together to agree on the failure signature — what exactly happens, when it happens, and what the observable symptoms are. I'd want to confirm that the failure is consistent across multiple units and that we can reproduce it reliably in a temperature-controlled environment. If we can reproduce it at will by heating the device, we have a powerful tool for testing hypotheses.

**Step 2: Define what each hypothesis predicts.** I'd ask each team to articulate their hypothesis in terms of testable predictions:

- The hardware team's layout hypothesis predicts that the SPI signals show measurable degradation — increased rise/fall times, ringing, or timing violations at the receiver — that worsens with temperature. This should be observable with a scope probing at the sensor's pins.

- The firmware team's timing hypothesis predicts that the failure correlates with specific code paths or timing conditions — perhaps the sensor read is attempted while another operation is ongoing, or the SPI clock configuration is marginal. This should be observable by instrumenting the firmware to log timing data around each read attempt.

**Step 3: Design experiments that discriminate.** Rather than arguing about which is more likely, I'd design experiments that would produce different outcomes depending on which hypothesis is correct:

- **Experiment 1**: Probe the SPI lines at the sensor with a high-bandwidth scope during the failure. If the signals show clear timing violations (setup/hold violations, excessive ringing), that supports the layout hypothesis. If the signals are clean but the sensor still returns wrong data, that supports a firmware issue.

- **Experiment 2**: Vary the SPI clock frequency. If the layout is marginal, lowering the clock speed should reduce or eliminate the failures. If the firmware has a race condition, clock speed might not matter.

- **Experiment 3**: Add instrumentation to the firmware to log the exact timing of each SPI transaction relative to other system activities. If failures correlate with specific concurrent operations, that supports a firmware timing issue.

**Step 4: Manage the team dynamics.** I'd make it clear that this isn't about which team is "right" — it's about finding the root cause so we can fix it. I'd encourage both teams to contribute to the experiment design and to be open to evidence that contradicts their initial hypothesis. I'd also set a timeline for the investigation and agree on decision criteria — what evidence would convince us to pursue one hypothesis over the other.

**Step 5: Drive to root cause and corrective action.** Once the evidence points in one direction, I'd lead the team through a structured root-cause analysis — using something like a fishbone diagram or 5-whys — to understand not just the immediate cause but the systemic issues that allowed it. If it's a layout issue, why didn't design review catch it? If it's a firmware timing issue, why didn't the code review or testing catch it? The corrective action should address both the immediate fix and the process gap.

The key leadership principle here is to keep the investigation evidence-driven rather than opinion-driven. Both teams have legitimate expertise, but the failure doesn't care about organizational boundaries — it will reveal itself through careful measurement and experimentation.

**Possible follow-ups:**
- How would you handle a situation where the evidence is genuinely ambiguous and could support either hypothesis?
- What would you do if one team refuses to accept the evidence and continues to push their original hypothesis?