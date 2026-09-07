# hardware-design — Day 48

## Q1: How would you approach designing a power supply architecture for a medical device that contains both a high-resolution analog front-end (requiring a noise floor below 50 µV RMS) and a motor driver that can draw 1A peaks?

**Answer:** I'd start by separating the noisy and sensitive domains at the architectural level rather than trying to fix noise problems later with filtering alone. The key principle is that the motor driver and the analog front-end should not share the same power path or return path if it can be avoided.

My approach would be:

1. **Define the power tree first.** I'd identify all rails needed: the motor supply (likely 5V or 12V), the analog rail (typically 3.3V or 5V with very low noise), and digital logic rails. The motor driver gets its own supply path directly from the battery or main input, while the analog section gets a dedicated low-noise regulator downstream of a separate switching stage or directly from the input through an LDO.

2. **Isolate the motor supply.** The motor driver should have its own bulk capacitance and, if necessary, a dedicated switching regulator. The return path for motor current should be routed separately back to the source, not through the analog ground plane. This prevents di/dt noise from the motor from coupling into the analog reference.

3. **Use a two-stage approach for the analog rail.** Rather than powering the analog front-end directly from a switching regulator, I'd use a switching preregulator followed by a low-noise LDO. The LDO provides PSRR at frequencies where the switcher's ripple and noise are significant. The LDO's output noise and PSRR specs need to be checked against the 50 µV RMS budget — not just the datasheet noise density at one frequency, but integrated noise across the bandwidth of interest.

4. **Budget the noise.** I'd work backward from the 50 µV RMS requirement. The analog front-end's own noise, the LDO's noise, and any coupled noise from the digital or motor sections each get a portion of the budget. If the LDO contributes 20 µV RMS and the front-end contributes 30 µV RMS, that's already at the limit — so I'd need to reduce one or the other.

5. **Consider the motor's current profile.** A 1A peak motor draw with fast edges means high di/dt. I'd look at the motor driver's switching frequency and edge rates, then ensure the power architecture has enough decoupling at the motor driver to keep transients local. A ferrite bead or small inductor between the motor supply and the rest of the system can help, but only if the voltage drop under peak current is acceptable.

6. **Grounding strategy.** I'd use a solid ground plane with careful partitioning rather than split planes, which can create return path discontinuities. The motor return current should be routed so it doesn't share copper with the analog return. If the motor and analog sections are on the same board, I'd place them at opposite ends and route the motor return directly to the input connector or battery return.

7. **Verify with measurements.** I'd characterize the actual noise on the analog rail with the motor running — both at steady state and during motor start/stop transients — using a scope with sufficient bandwidth and a low-noise probe. This catches issues that simulation might miss, like coupling through parasitic inductance in the ground plane.

The trade-off is always between cost/complexity and noise performance. A separate LDO for the analog section adds cost and power loss, but for a medical device where measurement accuracy is critical, that's usually justified.

**Possible follow-ups:**
- How would you decide whether to use a dedicated ground plane for the analog section versus a single unified ground plane?
- What specific LDO parameters would you evaluate to ensure the analog rail meets the 50 µV RMS requirement?

---

## Q2: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** This is a classic symptom pattern that points to a low-frequency modulation of the supply or reference, not a signal-path problem. Since the input is shorted, the disturbance is being injected somewhere in the power or reference path. The fact that it varies with supply voltage strongly suggests the disturbance is coupled through the supply or reference rather than being generated internally by the front-end.

My debugging approach would be:

1. **Characterize the disturbance precisely.** I'd capture the waveform on a scope with sufficient resolution and a long timebase. I need to know: Is it sinusoidal or more like a sawtooth or pulse? Is it exactly periodic or does it drift? What's the amplitude relative to the supply voltage? This tells me whether it's thermal cycling, a control loop oscillation, or something coupled from another system.

2. **Check the power supply with the same timebase.** I'd probe the supply rail at the front-end's power pin, not at the supply output. A 1–10 Hz disturbance on the rail could be caused by a regulator control loop that's marginally stable, a load that's cycling at that rate, or thermal effects in a reference or regulator. If the disturbance appears on the rail, I'd trace it back to the source.

3. **Look for low-frequency sources.** Common culprits at 1–10 Hz include:
   - A regulator's thermal shutdown/restart cycle (if the regulator is marginal on power dissipation)
   - A reference or regulator that's oscillating due to a marginal compensation network
   - A digital circuit that's waking up periodically (e.g., a watchdog or low-power timer) and drawing current pulses that modulate the supply
   - A ground loop or thermocouple effect at a connector or junction
   - An LDO that's oscillating at a very low frequency due to an unstable feedback loop with certain load conditions

4. **Isolate the injection point.** I'd power the front-end from a clean bench supply (battery or linear supply) and see if the disturbance disappears. If it does, the problem is in the on-board power path. If it persists, the problem is in the front-end itself or its reference. Then I'd substitute the reference with an external precision source to rule that out.

5. **Check the reference.** A voltage reference can exhibit low-frequency noise (flicker noise) that's more pronounced at low frequencies. If the reference is the source, I'd look at its noise spec and consider whether a different reference with lower 1/f noise is needed. But the amplitude varying with supply voltage suggests it's not just reference noise — it's supply-coupled.

6. **Examine thermal effects.** A 1–10 Hz disturbance can be thermal if there's a component that's self-heating and then cooling in a cycle. This could happen with a regulator that's dissipating significant power, or a reference that's oscillating between two temperatures. I'd check the case temperature of suspect components with a thermal camera or thermocouple while observing the disturbance.

7. **Consider the measurement setup itself.** If I'm using a scope probe with a long ground lead, I could be picking up low-frequency magnetic fields. I'd use a short ground spring and verify the measurement is real by moving the probe around.

The key insight is that a low-frequency disturbance that varies with supply voltage is almost always a power integrity issue, not a signal chain issue. The debugging should focus on the power path and reference, not on the amplifier or filter stages.

**Possible follow-ups:**
- What if the disturbance only appears when the device is running on battery power but not on a bench supply — what would that tell you?
- How would you distinguish between a power supply issue and a ground loop as the root cause?

---

## Q3: How would you approach selecting between a SAR ADC and a sigma-delta ADC for a medical device that measures a slowly varying physiological signal (e.g., temperature or pressure) with high resolution, and what are the key trade-offs you'd consider?

**Answer:** For a slowly varying physiological signal like temperature or pressure, the signal bandwidth is typically very low — often below 10 Hz, sometimes below 1 Hz. The key requirement is high resolution and accuracy at DC and very low frequencies, not high sampling rate. Both SAR and sigma-delta ADCs can work, but they have different strengths and weaknesses in this application.

**SAR ADC considerations:**
- SAR ADCs are inherently sample-by-sample converters with no latency. Each conversion is independent, which makes them predictable and easy to debug.
- They have excellent DC linearity and no idle tones or pattern noise issues that can plague sigma-delta converters.
- SAR ADCs are less sensitive to the clock quality and don't require a digital filter that can introduce group delay.
- However, achieving high resolution (18–20 bits) in a SAR ADC is difficult. Most SARs top out at 16–18 bits, and the noise performance at 16+ bits requires careful layout and a very clean reference.
- SAR ADCs require an anti-aliasing filter before the input because they sample at the Nyquist rate. For a low-bandwidth signal, this filter is simple — a single-pole RC might suffice — but it still needs to be there.

**Sigma-delta ADC considerations:**
- Sigma-delta converters achieve high resolution (20–24 bits) through oversampling and noise shaping. For a 10 Hz signal, a sigma-delta with a 20 Hz output data rate can achieve very high effective resolution.
- The built-in digital filter provides excellent anti-aliasing performance. The modulator samples at a high rate, and the digital decimation filter removes out-of-band noise. This simplifies the analog front-end.
- Sigma-delta converters have a latency due to the digital filter. For a slowly varying signal, this is usually acceptable, but it needs to be considered if the signal is used in a real-time control loop.
- They can exhibit idle tones and pattern noise at certain input levels, though modern devices handle this well.
- The reference and power supply rejection of sigma-delta converters is generally good, but the digital filter's response to out-of-band signals needs to be understood.

**My selection process would be:**

1. **Define the actual requirements.** What resolution do I truly need? For a temperature measurement with ±0.1°C accuracy over a 0–50°C range, I need roughly 12–14 bits of effective resolution depending on the sensor's sensitivity. For a pressure sensor with a specific accuracy requirement, I'd calculate the required ENOB from the noise budget. Often, the required resolution is lower than people assume.

2. **Consider the sensor's output impedance and drive capability.** If the sensor has high output impedance (e.g., a bridge or thermistor with high resistance), the ADC's input sampling behavior matters. SAR ADCs draw charge from the source during sampling, which can cause settling errors if the source impedance is too high. Sigma-delta ADCs with a buffered input are more forgiving.

3. **Evaluate the noise floor.** For a low-bandwidth signal, I'd compare the ADCs' noise-free resolution at the output data rate I need. A sigma-delta ADC might specify 24-bit resolution but only achieve 18 noise-free bits at 20 SPS. A 16-bit SAR might achieve 15.5 noise-free bits. The difference might be smaller than the datasheet's headline resolution suggests.

4. **Think about the system architecture.** If I need to multiplex multiple channels, a SAR ADC with an external mux is straightforward. Sigma-delta ADCs with integrated muxes exist but have settling time considerations when switching channels due to the digital filter. For a single-channel, slowly varying signal, a sigma-delta is often simpler.

5. **Consider calibration and drift.** Both types need calibration for offset and gain errors. The reference drift and ADC's own drift over temperature are often the limiting factors, not the converter architecture.

6. **Check power consumption.** For a battery-powered device, the ADC's power at the required sample rate matters. Sigma-delta ADCs can be very low power at low output data rates because they can duty-cycle the modulator.

In practice, for a single-channel, low-bandwidth, high-resolution measurement, I'd lean toward a sigma-delta ADC with a built-in PGA and reference buffer. It simplifies the analog front-end, provides excellent noise performance at low bandwidths, and the digital filter handles anti-aliasing. But if I needed multiple channels, fast channel switching, or deterministic latency, I'd choose a SAR ADC.

**Possible follow-ups:**
- How would the presence of 50/60 Hz interference affect your choice between SAR and sigma-delta?
- What if the signal bandwidth were 1 kHz instead of 10 Hz — would your recommendation change?

---

## Q4: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** A fault latch in a medical device serves two purposes: it ensures the device stays in a safe state after a fault, and it prevents nuisance cycling where the device repeatedly tries to restart into a fault condition. The design must be deterministic, fail-safe, and verifiable.

**Core design approach:**

1. **Choose the latch topology.** The classic approach is a comparator driving a thyristor-like latch or a comparator with positive feedback (a Schmitt trigger with a latching element). A common implementation uses a comparator whose output feeds back to its non-inverting input through a resistor network, creating a latch. Once the comparator trips, the feedback holds it in the tripped state even after the input returns to normal.

   Alternatively, a discrete SCR or a dedicated latch IC can be used. For medical devices, I'd prefer a comparator-based latch because it's easier to analyze, test, and verify than a discrete SCR circuit.

2. **Define the reset mechanism.** The latch must only reset through a deliberate action. Options include:
   - A momentary pushbutton that removes power from the latch or forces it into the reset state
   - A reset signal from a supervisory circuit that requires a specific sequence (e.g., power cycle with a minimum off-time)
   - A reset line from the main processor, but only if the processor itself is verified healthy (e.g., through a watchdog or a separate health monitor)

   For a medical device, I'd avoid a reset that can happen automatically without a deliberate operator action. A power-cycle reset is common, but I'd ensure the power must be removed for a minimum time (e.g., 5 seconds) to prevent rapid power cycling.

3. **Ensure the latch is fail-safe.** The latch should default to the safe state if power is lost or if a component fails. This means:
   - The latch should be active-low (the fault output is asserted when the latch is tripped), so a loss of power or a floating output defaults to the fault state.
   - The comparator's inputs should be biased so that if the sensor or sensing element fails open or short, the latch trips rather than clears.
   - Pull-up or pull-down resistors should be chosen so that a disconnected component results in a fault, not a false clear.

4. **Add hysteresis to prevent chatter.** The latch itself provides hysteresis by nature, but I'd verify that the trip point and reset point are well-separated. The latch should not be resettable by noise or minor fluctuations in the fault condition.

5. **Design for testability.** In a medical device, the latch circuit must be testable during manufacturing and during periodic maintenance. I'd include a test point that allows injecting a fault signal to verify the latch trips, and a way to verify the reset mechanism works. This might be a test pad that can be pulled to the fault condition or a command from the processor that triggers a self-test.

6. **Consider the reset action's safety.** The reset should only be possible when it's safe to restart the device. For example, if the latch was triggered by over-temperature, the reset should require that the temperature has dropped below a safe threshold — not just that the operator pressed a button. This might mean the reset circuit checks the fault condition is clear before allowing a reset, or it might mean the reset simply re-arms the protection and the device goes through a startup sequence that re-checks all conditions.

7. **Document the behavior.** The latch's behavior — what triggers it, how it's reset, what happens on power-up — needs to be documented in the design history file and verified through testing. The test plan should cover: fault injection, reset under fault-present conditions, reset under fault-cleared conditions, and power cycling.

**A specific implementation approach:**

I'd use a comparator with a reference voltage on one input and the sensed fault signal on the other. The comparator's output drives a MOSFET or logic gate that controls the device's enable line. Positive feedback from the output to the non-inverting input through a resistor divider creates the latch. The reset switch pulls the non-inverting input low (or high, depending on polarity) to break the latch.

The key design parameters are:
- The trip threshold voltage and its tolerance over temperature
- The latch's hold current and whether it can maintain the fault state indefinitely
- The reset mechanism's immunity to noise (debouncing, minimum pulse width)
- The behavior on power-up — does the latch default to the fault state or the safe state?

For a medical device, I'd also consider whether the latch should be implemented in hardware only or whether a CPLD or programmable logic device is acceptable. Hardware-only is simpler to verify and doesn't depend on firmware or configuration being correct.

**Possible follow-ups:**
- How would you verify that the latch circuit is fail-safe — what specific fault injection tests would you run?
- What if the fault condition is intermittent — how would you prevent the latch from being reset by a brief clearing of the fault?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing the hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the hardware approach is necessary because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical design decision, and the disagreement is fundamentally about where to place the safety boundary. My approach would be to move the discussion from opinion to evidence and risk analysis.

**First, I'd acknowledge the firmware lead's valid points.** A firmware-based approach does save board space and cost, and it does allow more flexible threshold adjustment. Those are real benefits. I'd start by acknowledging that so the discussion doesn't become adversarial.

**Then, I'd reframe the question around the safety requirements.** The key question isn't whether firmware *can* do the job — it's whether firmware *can be relied upon* to do the job under all fault conditions. I'd ask: What happens if the firmware hangs? What happens if the ADC's reference drifts? What happens if a memory corruption causes the firmware to execute the wrong code path? These aren't hypothetical concerns — they're failure modes that need to be analyzed under IEC 