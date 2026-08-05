# debugging-failure-analysis — Day 15

## Q1: How would you approach debugging a medical device where the failure occurs only when the device is operated at a specific altitude or in a low-pressure environment, such as during air transport of a patient?

**Answer:** This is a classic environmental stressor that's easy to overlook because it doesn't appear in standard bench testing. My approach would be systematic:

First, I'd try to reproduce the failure in a controlled environment — ideally a hypobaric chamber if available, or at minimum by understanding what physical parameters change with altitude. The key variables are reduced air pressure, reduced air density (affecting cooling), and potentially reduced partial pressure of oxygen.

I'd start by reviewing the device's design for altitude-sensitive components. Common culprits include:
- **Sealed enclosures or packages** — if the device has a sealed housing, the pressure differential can stress seals, flex the PCB, or affect components with mechanical structures (e.g., MEMS devices, pressure sensors, relays)
- **Electrolytic capacitors** — their sealed construction can be affected by pressure differentials
- **Cooling-dependent components** — if the design relies on convective cooling, reduced air density means less heat dissipation, potentially pushing components closer to thermal limits
- **Reference voltages** — some voltage references and analog circuits can shift with pressure due to package stress

I'd also examine the failure mode itself. If it's an intermittent reset, I'd look at whether the pressure change could cause mechanical flexing of the PCB, creating intermittent connections. If it's a sensor reading error, I'd check whether the sensor is pressure-sensitive by design (like a barometric sensor) or by accident (package stress affecting a bridge circuit).

The investigation would include reviewing the design's environmental specifications — was altitude/pressure ever specified as a requirement? If not, that's a gap in the requirements definition that needs to be addressed.

**Possible follow-ups:**
- How would you determine whether the root cause is mechanical (PCB flex, connector stress) versus electrical (component parameter shift)?
- What design changes would you consider to make the device more robust to pressure variations?

---

## Q2: Walk me through your approach to a failure investigation where a medical device's firmware and hardware teams disagree on whether a timing violation is a hardware or software problem — the device intermittently fails to complete a sensor read within the required time window, and the sensor occasionally returns stale data.

**Answer:** This is a classic firmware-hardware boundary issue, and the first step is to stop thinking in terms of "hardware's fault" versus "software's fault" and instead focus on understanding the actual timing behavior of the system.

I'd start by instrumenting the system to capture precise timing data. This means using a logic analyzer or oscilloscope to measure the actual timing of the communication transaction — when the master initiates the read, when the slave responds, and when the data is actually valid. Simultaneously, I'd add firmware instrumentation to log timestamps at key points in the software flow.

The key question is: is the sensor actually returning data late, or is the firmware initiating the read late, or is the firmware not giving the sensor enough time to respond?

I'd look at the sensor's datasheet timing specifications carefully. Many sensors have a maximum conversion time, and if the firmware's timeout is set too close to that maximum, you'll get intermittent failures when the sensor is at the edge of its specification — especially if temperature or supply voltage affects the conversion time.

I'd also examine the communication protocol's timing margins. For example, if this is I2C, I'd check whether the clock stretching behavior is properly handled. If it's SPI, I'd check whether the clock rate and setup/hold times have adequate margin.

The systematic approach is to:
1. Capture actual timing waveforms during the failure
2. Compare measured timing against the sensor's datasheet specifications
3. Check whether the firmware's timeout and retry logic accounts for worst-case sensor timing
4. Check whether any other system activity (interrupts, other bus traffic) could delay the firmware's response

If the sensor is genuinely returning data late, that's a hardware issue — but the fix might be in firmware (increasing timeout, adding retries) or in hardware (changing the sensor, adjusting pull-ups, reducing bus capacitance). If the firmware is initiating reads late, that's a software issue. The investigation should produce data that makes the answer clear rather than relying on opinion.

**Possible follow-ups:**
- What specific measurements would you take to distinguish between late sensor response versus late firmware initiation?
- How would you determine whether the timing margin is adequate, and what margin would you consider acceptable for a medical device?

---

## Q3: How would you approach a failure investigation where a medical device's power supply exhibits audible noise (whining or buzzing) that correlates with the device's processing load, and the noise is only noticeable in a quiet clinical environment?

**Answer:** Audible noise from a power supply is a symptom that often points to the interaction between the control loop and the load characteristics. The first step is to identify which component is producing the noise — it could be:
- An inductor or transformer (magnetostriction or mechanical vibration from the magnetic field)
- A ceramic capacitor (piezoelectric effect, especially with high-voltage AC ripple across it)
- A ferrite bead or other magnetic component

The correlation with processing load is a strong clue. When the processor's load changes, the power supply's control loop must respond. If the loop is marginally stable, it can oscillate at an audible frequency (typically 1–20 kHz) rather than the designed switching frequency (typically hundreds of kHz to MHz). This is often called "burst mode" or "pulse skipping" behavior at light loads, or it could be loop instability under transient load conditions.

My approach would be:
1. **Identify the noise source** — use a stethoscope or a simple probe (like a plastic tube) to localize which component is vibrating. A thermal camera can also help if the component is dissipating excess energy.
2. **Measure the power supply output** — use a wide-bandwidth oscilloscope to capture the output voltage during the noisy condition. Look for low-frequency modulation of the switching waveform or sub-harmonic oscillation.
3. **Characterize the load profile** — measure the actual current draw pattern from the processor during different processing loads. The noise might occur during specific load transitions rather than steady-state operation.
4. **Check the control loop** — review the compensation network and compare it against the expected load range. If the loop is under-compensated for the transient load steps, it can ring at an audible frequency.

For a medical device, this is more than a cosmetic issue — audible noise can be distracting to clinicians and alarming to patients. The fix might involve adjusting the compensation network, changing the switching frequency, adding a load transient response improvement (like feed-forward), or selecting components with better mechanical characteristics.

**Possible follow-ups:**
- How would you determine whether the noise indicates a reliability risk or is purely a nuisance issue?
- What design changes would you consider to eliminate the audible noise without compromising power supply performance?

---

## Q4: You're leading a failure investigation where a medical device's safety-critical firmware occasionally fails to respond to a hardware interrupt — the interrupt flag is set in the peripheral, but the ISR never executes. The firmware team has reviewed the code and believes the interrupt configuration is correct. How would you approach this?

**Answer:** This is a particularly challenging failure mode because it sits at the boundary between hardware and firmware, and the symptom — interrupt flag set but ISR not executing — has several possible explanations.

I'd structure the investigation around the interrupt path, examining each stage:

**1. Interrupt source configuration:**
- Is the peripheral's interrupt enable bit actually set? Sometimes a register write doesn't take effect due to a bus timing issue or a race condition with another peripheral access.
- Is the interrupt priority configured correctly? If the interrupt is at a priority level that's masked by the current processor state, it won't execute until the mask is cleared.

**2. Interrupt controller (NVIC or equivalent):**
- Is the interrupt actually enabled in the interrupt controller? This is separate from the peripheral's interrupt enable.
- Is the interrupt pending bit being set? If the peripheral generates the interrupt but the NVIC doesn't show it as pending, there's a hardware path issue.
- Is there a priority inversion or masking issue? If a higher-priority interrupt is stuck in a loop or a lower-priority interrupt is incorrectly configured, it can prevent the target ISR from executing.

**3. Processor execution state:**
- Is the processor actually executing code when the interrupt occurs? If the processor is in a tight loop with interrupts disabled, or in a low-power mode with the wrong wake-up configuration, the ISR won't run.
- Is there a race condition where the interrupt occurs during a critical section where interrupts are disabled, and the flag gets cleared before interrupts are re-enabled?

**4. Hardware path:**
- Is the interrupt signal actually reaching the processor? This could be a PCB routing issue, a level versus edge trigger mismatch, or a signal integrity problem on the interrupt line.

My investigation would start with instrumentation — I'd add debug output at key points: when the peripheral flag is set, when the NVIC pending bit is set, and when the ISR entry is executed. I'd also use a logic analyzer to capture the interrupt line activity alongside the processor's execution state.

One common root cause I've seen in this type of failure is a race condition where the firmware clears the interrupt flag in the peripheral before the interrupt controller has latched the pending bit — the interrupt is lost entirely. This can happen if the firmware polls the flag and clears it in a different code path than the ISR.

Another possibility is that the interrupt is being generated while the processor is in a state where interrupts are disabled (e.g., during a flash write operation or a critical section), and the flag gets cleared by another code path before interrupts are re-enabled.

**Possible follow-ups:**
- How would you determine whether this is a hardware path issue versus a firmware configuration issue?
- What design practices would you recommend to make the interrupt handling more robust against this type of failure?

---

## Q5: A cross-functional team is investigating a medical device failure where the device's battery life has degraded significantly in the field — devices that should last 7 days on a charge are now lasting only 3–4 days after about a year of use. The battery management system logs show normal charge/discharge cycles, and the battery cells are within their expected capacity degradation curve. How would you approach this investigation?

**Answer:** This is an interesting failure because the battery itself appears to be behaving normally — the issue is likely in the system's power consumption rather than the battery's health. The device is consuming more power than it should, or the power management is not as effective as designed.

I'd structure the investigation around the device's power consumption profile:

**1. Verify the power consumption baseline:**
- Measure the actual current draw of a field-returned device in various operating modes (active, idle, sleep) and compare against the design specifications.
- Check whether the device is spending more time in high-power states than expected. For example, if the device should be in sleep mode 90% of the time but is actually only sleeping 70% of the time, that alone could explain the battery life reduction.

**2. Look for power management degradation:**
- Are there firmware changes that could have affected power management? Even if the firmware version is unchanged, a memory leak or a gradually accumulating state could cause the device to stay in higher-power modes.
- Is there a hardware degradation that increases power consumption? For example, a partially shorted component, increased leakage current in a capacitor, or a connector with increased resistance that causes more power dissipation.

**3. Examine the charging behavior:**
- The BMS logs show normal charge/discharge cycles, but I'd look deeper — is the device actually reaching full charge? Is the charge termination happening correctly, or is the device stopping charging early?
- Is there a parasitic load during charging that's reducing the effective charge delivered to the battery?

**4. Consider environmental factors:**
- Has the device's usage pattern changed? If patients are using the device more frequently or for longer sessions, the battery life would naturally decrease.
- Is the device operating in a different temperature range than originally specified? Battery capacity decreases at low temperatures, and if the device is being used in colder environments, the effective capacity would be lower.

**5. Look for gradual degradation mechanisms:**
- Is there a component that's gradually increasing its leakage current over time? This could be related to moisture ingress, contamination, or component aging.
- Is the firmware's power management state machine degrading — for example, a timer that's gradually drifting, causing the device to wake up more frequently than intended?

The key insight is that the battery is a symptom, not the root cause. The investigation needs to focus on the system's power consumption and whether it has changed over time.

**Possible follow-ups:**
- How would you distinguish between increased active-mode current versus reduced time in sleep mode as the cause?
- What design changes would you consider to make the device's power consumption more robust against aging and environmental variation?