# hardware-design — Day 32

## Q1: How would you approach designing the analog front-end for a biopotential measurement system (e.g., ECG) that must reject common-mode interference from the patient's body while maintaining a usable signal, and what are the key design decisions you'd need to make?

**Answer:** The fundamental challenge in biopotential measurement is that the signal of interest is very small (on the order of millivolts or less) while common-mode interference — particularly 50/60 Hz mains pickup — can be orders of magnitude larger. My approach would start with the electrode interface and work through the signal chain systematically.

First, I'd use an instrumentation amplifier as the first active stage because its high common-mode rejection ratio (CMRR) is essential for rejecting the common-mode voltage that appears on both electrodes. The key decision here is the gain distribution: I'd typically set the instrumentation amplifier's gain to a moderate value (e.g., 10–20) rather than trying to do all the amplification in one stage. This keeps the common-mode voltage within the amplifier's input range while reducing the impact of noise from subsequent stages.

The reference electrode and right-leg drive circuit are critical for practical CMRR. A driven-right-leg circuit actively cancels common-mode voltage by sensing it and feeding back an inverted version through the body. This can improve effective CMRR by 40–60 dB compared to passive grounding alone. The trade-off is stability — the feedback loop must be compensated to avoid oscillation, and the current through the patient must be limited to safe levels per applicable medical standards.

For the input protection and conditioning, I'd include series resistors and clamping diodes to protect against defibrillation pulses and electrostatic discharge. These components must be chosen carefully because they add noise and can degrade CMRR if the impedance on the two inputs isn't well matched. I'd also consider AC coupling or a high-pass filter to remove the DC offset that arises from the electrode-skin interface — this offset can be tens of millivolts and would otherwise saturate the amplifier.

The anti-aliasing filter before the ADC is another key decision. For ECG, the passband is roughly 0.5–100 Hz, so I'd design a filter that passes this band while rejecting out-of-band noise. The filter order and topology (e.g., Sallen-Key vs. multiple feedback) involve trade-offs between component count, noise contribution, and phase response. I'd also need to consider whether the ADC's sampling rate and resolution are adequate — a 16-bit sigma-delta ADC with oversampling is often a good choice for this application because it simplifies the anti-aliasing requirements.

Finally, the grounding and layout strategy is crucial. The analog ground must be carefully separated from digital and power grounds to avoid coupling noise into the high-impedance input path. I'd use a solid ground plane with careful routing of the input traces, keeping them short, shielded, and well-separated from any switching signals.

**Possible follow-ups:**
- How would you characterize the CMRR of your front-end in practice, and what non-ideal factors would degrade it that wouldn't show up in a simple bench test?
- How would you handle the trade-off between the right-leg drive's effectiveness and patient safety current limits?

---

## Q2: How would you approach selecting between a SAR ADC and a sigma-delta ADC for a medical device that measures a slowly varying physiological signal (e.g., temperature or pressure) with high resolution, and what are the key trade-offs you'd consider?

**Answer:** The choice between SAR and sigma-delta architectures depends on the signal characteristics, resolution requirements, power budget, and the complexity of the surrounding circuitry.

For a slowly varying signal like temperature or pressure, sigma-delta converters are often attractive because they achieve high resolution (16–24 bits) through oversampling and noise shaping. The key advantage is that the oversampling ratio relaxes the anti-aliasing filter requirements considerably — a simple first-order RC filter is often sufficient, whereas a SAR ADC would require a sharper anti-aliasing filter to prevent out-of-band noise from folding into the passband. This is a significant practical advantage because high-order analog filters are bulky, expensive, and can introduce their own errors.

However, sigma-delta converters have a latency issue — the digital filter introduces a group delay that can be tens or hundreds of milliseconds. For a temperature sensor that changes slowly, this is usually acceptable, but if the signal has meaningful higher-frequency content or if the device needs to respond quickly to changes, this latency could be a problem. Sigma-delta converters also consume more power than SAR converters at the same sampling rate because of the oversampling and digital filtering.

SAR converters, on the other hand, offer sample-by-sample conversion with no latency, lower power consumption, and a simpler digital interface. The trade-off is that achieving 16-bit resolution requires a very clean analog front-end — the anti-aliasing filter must be carefully designed, and the reference and input circuitry must be extremely stable. SAR converters are also more sensitive to noise on the power supply and reference, so the PCB layout and decoupling become more critical.

For a medical device, I'd also consider the system-level implications. If the device needs to detect trends over time (e.g., a temperature trend), the sigma-delta's latency is irrelevant, and its high resolution and relaxed filtering requirements make it attractive. If the device needs to respond quickly to a threshold crossing (e.g., a pressure alarm), the SAR's low latency might be more important, even if it means more careful analog design.

I'd also look at the practical details: the sigma-delta's digital filter characteristics (e.g., whether it has 50/60 Hz rejection built in), the SAR's missing-code performance at the required resolution, and the reference voltage requirements for both. Ultimately, I'd prototype the signal chain and measure the actual noise performance in the target environment rather than relying solely on datasheet specifications.

**Possible follow-ups:**
- How would the sampling rate and resolution requirements change your decision between the two architectures?
- What specific datasheet parameters would you compare between two candidate ADCs to make your final selection?

---

## Q3: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** This is a classic symptom pattern that points to a low-frequency noise source coupled into the signal path, and the fact that it varies with supply voltage is a strong diagnostic clue. I'd approach this systematically, starting with the most likely causes.

First, I'd check whether the disturbance is truly periodic or if it's more of a drift or oscillation. A true periodic signal at 1–10 Hz suggests something is modulating the supply or the reference. The variation with supply voltage could indicate that the disturbance is being injected through the power supply rejection path — the circuit's PSRR is finite, and if there's low-frequency ripple on the supply, it will appear at the output attenuated by the PSRR.

The most common culprit in my experience would be a thermal effect — a component that's dissipating power and causing localized heating that modulates the circuit's behavior. For example, a voltage reference or an op-amp that's self-heating can cause a low-frequency drift that looks like a periodic disturbance, especially if there's a thermal time constant involved. I'd check the temperature of key components with a thermal camera or by touching them (carefully, with appropriate safety precautions) to see if any are unusually warm.

Another likely cause is a ground loop or a reference issue. If the ground reference for the analog section is shared with a digital circuit that's cycling at 1–10 Hz (e.g., a status LED blinking, a sensor reading at a low rate, or a communication retry), the ground bounce could be coupling into the signal path. I'd use an oscilloscope to measure the ground voltage at the analog front-end's reference point relative to the system ground, and I'd look for correlation between the disturbance and any digital activity.

I'd also suspect the voltage reference itself. Some reference ICs have a "popcorn noise" or random telegraph noise characteristic that appears as low-frequency steps or disturbances. This is a known failure mode for some reference designs, particularly older or poorly specified parts. I'd check the reference output on a spectrum analyzer or with a high-resolution ADC to see if the disturbance is present there.

The systematic approach would be: first, isolate the stage — short the input at each stage of the signal chain to determine where the disturbance enters. Then, check the power supply with a low-noise oscilloscope or spectrum analyzer to see if the disturbance is present on the rail. Then, check the reference. Then, check for thermal effects. I'd also try substituting components — a different op-amp, a different reference — to see if the disturbance follows a specific part.

Finally, I'd consider the measurement setup itself. A 1–10 Hz disturbance can be caused by the test equipment — for example, a ground loop between the device under test and the bench power supply or oscilloscope. I'd try powering the circuit from a battery to eliminate mains-related ground loops, and I'd check whether the disturbance persists when the circuit is isolated from all bench equipment.

**Possible follow-ups:**
- How would you distinguish between a thermal effect and an electrical coupling issue in this scenario?
- What specific measurements would you take to confirm or rule out a ground loop as the cause?

---

## Q4: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The key design challenge here is balancing two competing requirements: the latch must be reliable and fail-safe (it must maintain the fault state even if the triggering condition clears), and it must be resettable only through a deliberate action that ensures the system is safe to restart.

I'd start with the basic latch topology — a comparator or a discrete transistor pair that creates a positive feedback loop. When the fault condition is detected (e.g., the temperature exceeds a threshold), the comparator's output changes state, and the feedback network holds it in that state even after the temperature drops below the threshold. The design decisions are in the details: the threshold accuracy, the hysteresis (which is different from latching — hysteresis prevents chatter at the threshold, while latching holds the state indefinitely), and the reset mechanism.

For the reset, I'd require a deliberate action that can't happen accidentally. This could be a manual reset button, a power-cycle detection circuit, or a command from a supervisory processor — but the key is that the reset must be gated by additional conditions. For example, the latch might only reset when the fault condition has been cleared AND a reset signal is applied AND the system is in a known-safe state. I'd use a combination of logic gates or a small CPLD to implement these conditions, or I'd use a comparator with an enable pin that's controlled by the reset logic.

A critical consideration is the fail-safe behavior. The latch circuit should default to the fault state if any of its components fail — for example, if the comparator's output is stuck, or if the power supply to the latch fails. This means I'd design the logic so that the "safe" state is the fault state, and the reset action must actively drive the circuit out of it. I'd also consider what happens during power-up: the latch should initialize to the fault state until the system has verified that all conditions are safe.

The reset action itself needs careful thought. A manual reset button is simple but could be pressed accidentally. I'd require a deliberate action like holding the button for a specific duration, or pressing two buttons simultaneously, or using a key switch. If the reset is controlled by firmware, I'd require the firmware to verify the fault condition has cleared and that all safety interlocks are satisfied before asserting the reset signal. I'd also add a "reset request" handshake — the firmware requests a reset, and the hardware only grants it when the conditions are met.

Another important aspect is testability. In a medical device, the latch circuit must be verifiable — you need to be able to test that it triggers correctly and that it holds the fault state. I'd design in test points and possibly a test mode that allows the fault threshold to be lowered temporarily so the latch can be exercised without actually creating a dangerous condition.

Finally, I'd consider the distinction between a latch and a lockout. A latch holds the fault state until reset; a lockout might require the fault to be cleared AND a specific sequence of events to occur before the system can restart. For a medical device, the lockout approach is often more appropriate because it ensures that the operator has acknowledged the fault and taken deliberate action to address it.

**Possible follow-ups:**
- How would you design the reset logic to ensure it can't be accidentally triggered by a transient or a firmware glitch?
- How would you verify that the latch circuit fails safe — that is, that it defaults to the fault state on component failure?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing a hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical design decision, and my approach would be to focus on the engineering evidence and the regulatory requirements rather than letting it become a personality conflict. The first thing I'd do is acknowledge the firmware lead's valid points — a firmware-based approach does offer flexibility and cost savings, and those are legitimate considerations. But I'd frame the discussion around the fundamental question: what is the safety architecture of this device, and what level of independence is required for the protection mechanism?

I'd start by reviewing the applicable safety standards and the device's risk analysis. For a medical device, the safety requirements typically specify that protection functions must be independent of the main control function — this is a core principle in IEC 60601 and ISO 14971. If the firmware is responsible for both normal operation and fault detection, a single firmware failure could disable both. This is the classic "single point of failure" argument, and it's well-supported by regulatory guidance.

Rather than just asserting my position, I'd propose a structured evaluation. I'd suggest we conduct a failure modes and effects analysis (FMEA) on both approaches, considering scenarios like: what happens if the firmware hangs? What happens if the ADC fails in a way that produces a valid-looking but incorrect reading? What happens if the GPIO is stuck? What happens during firmware updates or boot? This would give us a systematic way to compare the two approaches and would likely reveal that the firmware-only solution has unacceptable failure modes.

I'd also raise the question of verification and validation. A hardware comparator circuit can be tested deterministically — you can apply a known temperature and verify the output. A firmware-based solution requires much more extensive testing to cover all the possible failure modes, and even then, you can't guarantee that the firmware will never hang. The regulatory burden for a firmware-only safety function is significantly higher, and the testing effort might offset the cost savings.

If the firmware lead still disagrees, I'd propose a compromise: keep the hardware comparator as the primary protection, but allow the firmware to monitor temperature as a secondary check and to provide more granular control. This gives the firmware lead the flexibility they want while maintaining the safety-critical independence. I'd also suggest we bring in a third party — perhaps a safety engineer or a regulatory consultant — to provide an independent assessment.

Throughout this, I'd keep the focus on patient safety and regulatory compliance rather than personal preferences. The goal isn't to win an argument; it's to ensure the device is safe and can be approved by regulators. I'd document the discussion and the rationale for the final decision, because that documentation will be needed for the design history file and the regulatory submission.

**Possible follow-ups:**
- How would you handle the situation if the firmware lead continues to push back after you've presented the safety analysis?
- What specific failure modes would you include in the FMEA to compare the hardware and firmware approaches?