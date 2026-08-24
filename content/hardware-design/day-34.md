# hardware-design — Day 34

## Q1: How would you approach designing a battery management system for a medical device that uses a 2-cell Li-ion battery pack and must support both charging and discharging while the device is in continuous use?

**Answer:** I'd start by defining the system-level requirements: charge current and time, discharge profile (continuous vs. pulsed loads), operating temperature range, and the safety certifications the device must meet. For a medical device, the battery management system has two distinct functions that need to be treated separately: protection and management.

For protection, I'd use a dedicated battery protection IC that monitors overvoltage, undervoltage, overcurrent, and short-circuit conditions on each cell independently. This must be hardware-based and independent of the main processor — the protection IC should be able to disconnect the pack via FETs even if firmware hangs. For a 2-cell pack, I'd also consider cell balancing, though for series cells in a medical device, passive balancing during charging is usually sufficient unless the cells are significantly mismatched.

For charging, I'd evaluate whether a linear or switching charger is appropriate. With 2 cells in series, a linear charger would dissipate excessive heat — the input voltage would need to be around 8.4V plus headroom, and the power loss would be significant at any reasonable charge current. So a switching charger (buck topology) is the practical choice. The charger needs to support charging while the device is operating, which means the power path must be designed so the system load doesn't confuse the charger's current sensing. A common approach is a "path management" scheme where the charger can supply both the system load and the battery simultaneously, prioritizing the system load.

For fuel gauging, I'd use a coulomb-counting IC with voltage-based correction, rather than relying on voltage alone — the open-circuit voltage of Li-ion cells is too flat in the middle of the discharge curve to give accurate state-of-charge estimates, especially under varying loads.

The key safety considerations are: redundant protection (protection IC plus charger IC's own safety timers), thermal management (temperature sensing on the battery and charging cutoff outside the specified temperature window), and compliance with the relevant battery safety standards. I'd also ensure that the charging path is isolated from the patient in a medical device — typically through the overall system isolation strategy.

**Possible follow-ups:**
- How would you handle the transition between charge and discharge modes when the device is plugged in and unplugged while running?
- What happens if the protection IC and the charger IC disagree about the battery state?

---

## Q2: Walk me through how you would debug a circuit where a low-dropout regulator (LDO) output is stable at light load but oscillates when the load current increases beyond a certain threshold.

**Answer:** This is a classic LDO stability problem. LDOs use a pass element with a feedback loop, and their stability depends heavily on the output capacitor's ESR and the load current. The first thing I'd check is the output capacitor — its value, ESR, and whether it's actually the component I specified. Many LDOs require a minimum ESR for stability, and ceramic capacitors with very low ESR can push the loop into instability. Conversely, some modern LDOs are designed for ceramic caps and become unstable with higher-ESR electrolytic capacitors.

I'd start by measuring the oscillation frequency and amplitude with an oscilloscope, then correlate it with load current. I'd also check the input supply — if the input rail has significant impedance, the LDO's loop can interact with it, especially at higher load currents. I'd verify the input decoupling is adequate.

Next, I'd review the datasheet's stability requirements carefully: the required output capacitor range, ESR window, and any minimum load current specification. Some LDOs require a minimum load to maintain stability because the pass transistor's gain changes with current. If the design is marginal, I'd look at the phase margin — this can be measured using a network analyzer, or estimated by looking at the loop gain and phase response.

If the design is within the datasheet's recommended operating conditions, I'd suspect the actual components differ from the BOM — for example, a capacitor with different dielectric (X5R vs. X7R) that has much higher voltage coefficient, reducing its effective capacitance at the output voltage. I'd also check the PCB layout: long traces from the LDO output to the load, or the output capacitor placed far from the LDO's sense pin, can add parasitic inductance and resistance that degrades stability.

The fix depends on the root cause: adjust the output capacitor value or ESR, add a small series resistor in some cases, improve the layout, or select a different LDO with a wider stability range.

**Possible follow-ups:**
- How would you determine the phase margin of the LDO loop in practice?
- What if the oscillation only appears at cold temperatures — how would that change your investigation?

---

## Q3: How would you approach selecting the clock source for a high-resolution ADC in a medical device that must maintain accurate sampling over a 0–50°C temperature range, and what parameters would you evaluate?

**Answer:** The clock source for a high-resolution ADC is often overlooked, but it directly affects the ADC's SNR and SFDR. The key parameters are jitter (both random and deterministic), frequency accuracy, and temperature stability.

For a medical device measuring physiological signals, the sampling clock's absolute frequency accuracy matters for time-based measurements (e.g., heart rate), while jitter matters for SNR. The relationship is: SNR degradation due to clock jitter is approximately 20·log10(1/(2π·f_in·t_jitter)), where f_in is the input frequency and t_jitter is the RMS jitter. For a 16-bit ADC sampling a 100 Hz biopotential signal, the jitter requirement is actually quite relaxed — even 100 ps of jitter would be negligible at these low frequencies. However, if the same ADC is used for higher-frequency signals, jitter becomes critical.

I'd evaluate three options: a crystal oscillator, a MEMS oscillator, or using the microcontroller's internal oscillator. For a medical device, I'd typically avoid the internal RC oscillator unless the ADC has a built-in PLL that can clean up the jitter, because internal RC oscillators have poor temperature stability (±1-2% or worse) and relatively high jitter. A crystal oscillator with a specified frequency tolerance of ±20 ppm or better over temperature is usually sufficient for physiological measurements.

The key parameters to evaluate are: initial frequency tolerance, temperature stability (frequency deviation over 0–50°C), aging, RMS phase jitter (integrated over the relevant bandwidth), and startup time. For the ADC's sampling clock, I'd also consider whether the clock is used directly or through a PLL — a PLL can multiply jitter, so a clean reference is important.

I'd also consider the clock's interaction with the ADC's sampling aperture. If the ADC has an internal sample-and-hold, the aperture jitter is what matters, not just the clock jitter. Some ADCs specify aperture jitter separately. For a medical device, I'd also think about EMI — a clock running at a harmonic of the ADC's sampling frequency can create beat frequencies that appear as in-band noise.

Finally, I'd consider whether the clock needs to be synchronized to anything else in the system (e.g., a wireless radio's timing). If so, I'd need a clock that can be synchronized or a PLL that can lock to an external reference.

**Possible follow-ups:**
- How would you measure the actual jitter of the clock in your circuit?
- What if the ADC's sampling clock and the wireless radio's clock are asynchronous — how would you handle potential beat frequencies?

---

## Q4: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** This is a fundamental safety architecture question. The latch must be implemented in hardware, independent of firmware, and must fail safe. I'd start by defining the fault conditions, the latching behavior, and the reset conditions — these need to be documented in the requirements before any circuit design begins.

For the latch itself, I'd use a comparator to detect the fault condition (e.g., a voltage across a sense resistor exceeding a threshold, or a thermistor voltage crossing a temperature limit), followed by a latching element. The classic approach is a thyristor-like circuit using two transistors (a silicon-controlled rectifier equivalent) or a comparator with positive feedback. A comparator with positive feedback is cleaner because it provides a well-defined threshold and hysteresis.

The key design decisions are:

1. **Threshold accuracy:** The comparator's reference voltage needs to be accurate over temperature. I'd use a precision reference rather than a resistor divider from the supply, unless the application tolerates the drift.

2. **Latching behavior:** Once triggered, the latch must hold its state regardless of whether the fault condition clears. This means the latch's holding path must not depend on the fault signal remaining active.

3. **Reset mechanism:** The reset must be deliberate and safe. Options include: a manual reset button (with debouncing), a reset signal from the main processor (but this requires the processor to be alive and trusted), or a power-cycle reset (but this may not be acceptable if the fault could recur immediately). For a medical device, I'd typically require a manual reset or a reset that requires the operator to acknowledge the fault. The reset should also be verified — for example, the latch should only clear if the fault condition is no longer present.

4. **Fail-safe behavior:** If the latch circuit itself fails (e.g., a component opens or shorts), the system should default to the safe state. This means the latch should be designed so that a failure in the detection or latching circuitry results in the fault being asserted, not cleared. For example, if the comparator's output is used to enable a power path, the power path should be disabled when the comparator's output is in an indeterminate state.

5. **Independence:** The latch must not depend on the main processor or firmware. It should have its own reference, its own power supply (or at least be powered from a rail that's always available), and its own output that directly controls the safety-critical function (e.g., shutting down a motor driver).

I'd also add a test mechanism — a way to verify the latch circuit works during manufacturing test or periodic maintenance. This could be a test input that simulates the fault condition and verifies the latch triggers and holds.

The reset circuit needs careful design: if the reset is a button, I'd debounce it and ensure that a stuck button doesn't prevent the latch from re-triggering. If the reset is from firmware, I'd require a specific sequence (e.g., a command followed by a confirmation) to prevent accidental resets.

**Possible follow-ups:**
- How would you test the latch circuit to verify it meets the response time requirement?
- What if the fault condition is intermittent — how would you ensure the latch doesn't cause nuisance shutdowns?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing the hardware-based latch circuit (a comparator and latch that shuts down the motor driver on overcurrent) with a firmware-based solution that monitors current via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the hardware approach is necessary because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** I'd approach this as a technical disagreement that needs to be resolved through data and a shared understanding of the requirements, not through authority or stubbornness. The first thing I'd do is acknowledge the firmware lead's valid points — a firmware-based approach does offer flexibility in threshold adjustment, and it could save board space and cost. These are legitimate engineering trade-offs, not unreasonable suggestions.

Then I'd reframe the discussion around the safety requirements. The key question is: what happens if the firmware hangs or the ADC fails while the motor is in an overcurrent condition? In a medical device, the answer needs to be: the motor shuts down through an independent path. I'd ask the firmware lead to walk through the failure modes: if the firmware is stuck in an infinite loop, the ADC is returning garbage, or the GPIO is stuck high, what happens? The firmware-based approach cannot guarantee a safe response in these scenarios because it depends on the very components that might be failing.

I'd also raise the regulatory angle. For a medical device, the safety mechanism needs to be verifiable and its independence from the main processor needs to be documented. A hardware latch is straightforward to verify — you can test it in isolation. A firmware-based approach requires demonstrating that the firmware can't hang, that the ADC can't fail in a way that defeats the protection, and that the GPIO will always respond. This is much harder to verify and may not satisfy the regulatory requirements.

Rather than simply rejecting the proposal, I'd suggest a middle ground: we could evaluate whether the firmware-based approach could work as a secondary protection layer, in addition to the hardware latch. The hardware latch provides the guaranteed response; the firmware could provide additional features like logging the fault condition, adjusting thresholds for different operating modes, or providing a more graceful shutdown sequence. This way, the firmware lead's ideas add value without compromising safety.

If the firmware lead still disagrees, I'd suggest we do a formal risk assessment (e.g., a DFMEA) together, documenting the failure modes and the effectiveness of each approach. This moves the discussion from opinion to analysis. I'd also involve the quality or regulatory team if available, since they can provide guidance on what the standards require.

The key is to keep the discussion focused on patient safety and regulatory compliance, not on who wins the argument. I'd also make sure the decision is documented with the rationale, so it can be reviewed if questions come up later.

**Possible follow-ups:**
- What if the firmware lead argues that the hardware latch itself could fail — how would you respond?
- How would you handle this if the project schedule is tight and the firmware lead's approach would save significant development time?