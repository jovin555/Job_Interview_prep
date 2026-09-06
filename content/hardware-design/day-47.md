# hardware-design — Day 47

## Q1: How would you approach designing a power supply architecture for a medical device that contains both a high-resolution analog front-end (requiring a noise floor below 50 µV RMS) and a motor driver that can draw 1A peaks?

**Answer:** The fundamental challenge here is that the motor driver and the analog front-end have directly conflicting power requirements — the motor needs a low-impedance, high-current path with fast transient response, while the analog section needs a clean, low-noise rail. I would not try to make a single rail serve both purposes.

My approach would be to separate the power domains at the architectural level. The motor driver should be supplied from its own rail, ideally directly from the battery or main supply through a dedicated path with appropriate bulk capacitance near the motor driver to handle the 1A peaks locally. The analog front-end should be supplied through a dedicated low-noise path — typically a switching preregulator followed by an LDO or a pi-filter, depending on the noise budget.

The key design decisions would be:

1. **Physical separation**: Keep the motor driver's power path and return path physically separated from the analog supply on the PCB. Don't share ground vias or route the motor return current under the analog section.

2. **Star-point grounding**: Connect the analog ground, motor ground, and digital ground at a single point, usually at the main supply return. This prevents motor current from flowing through the analog ground plane.

3. **Bulk capacitance strategy**: Place sufficient bulk capacitance at the motor driver's supply pins to handle the 1A peaks locally, rather than drawing that transient current through the main supply traces. This keeps the transient voltage drop away from the analog rail.

4. **LDO selection for the analog rail**: The LDO feeding the analog section needs good PSRR across the frequency range of the motor's switching noise. I'd look at the PSRR curve, not just the DC specification, and verify it's adequate at the motor's PWM frequency and its harmonics.

5. **Noise budget verification**: I'd calculate the expected noise contribution from each stage — the switching regulator's output ripple, the LDO's noise and PSRR, and the analog front-end's own noise — and confirm the total stays below the 50 µV RMS requirement with margin.

For the motor driver itself, I'd consider whether it needs its own local regulation or can run directly from the battery. If the motor causes significant voltage droop on the main rail, that droop must not couple into the analog supply — which is another argument for the LDO approach on the analog side.

**Possible follow-ups:**
- How would you decide between using an LDO versus a second switching regulator followed by filtering for the analog rail?
- What specific measurements would you perform during bring-up to verify that motor transients aren't coupling into the analog front-end?

---

## Q2: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** A periodic disturbance in the 1–10 Hz range with the input shorted tells me the noise is being injected internally, not through the signal path. The fact that amplitude varies with supply voltage is a strong clue — it suggests the disturbance is coupled through the power supply or is related to some internal oscillation that's supply-dependent.

My debugging approach would be systematic:

1. **Characterize the disturbance precisely**: I'd capture the waveform on an oscilloscope with sufficient resolution to see the actual shape — is it sinusoidal, sawtooth, or something else? I'd measure its exact frequency and amplitude, and check whether it's stable or drifting. I'd also check if it's synchronized to anything else in the system, like a switching regulator's clock or a periodic firmware event.

2. **Check the power supply with a spectrum analyzer**: I'd look at the actual supply rail at the analog front-end's pins, not at the regulator output. A 1–10 Hz disturbance on the supply could be caused by a thermal oscillation in a regulator, a slow control loop instability, or even a load that's periodically drawing current. I'd use a low-noise, high-resolution measurement to see if the disturbance appears on the supply.

3. **Isolate the power source**: I'd temporarily power the analog front-end from a clean bench supply (battery or linear supply) to see if the disturbance disappears. If it does, the problem is upstream in the power path. If it persists, the problem is internal to the analog circuit itself.

4. **Look for thermal effects**: Low-frequency disturbances in this range are sometimes thermal — a component self-heating and cooling creates a slow cycle. I'd check if the disturbance frequency changes with ambient temperature or if any component is running warm. A thermal imaging camera or just touching components (carefully) can help identify a warm component.

5. **Check for internal oscillation**: Some op-amp circuits can oscillate at low frequencies due to thermal feedback inside the IC or due to interaction with the decoupling network. I'd verify the decoupling is adequate and properly placed, and check the op-amp's stability with the actual load it's driving.

6. **Examine the reference and bias circuits**: If the disturbance is common to multiple stages, it might originate in a shared reference or bias circuit. I'd measure the reference voltage and bias currents to see if they're stable.

The supply-voltage dependence is a useful clue. If the disturbance amplitude increases with supply voltage, it could indicate a circuit that's marginally stable and oscillating — the higher supply increases loop gain, pushing the circuit closer to instability. This would point me toward checking the feedback network and compensation of any amplifiers in the signal chain.

**Possible follow-ups:**
- What if the disturbance disappears when you power the circuit from a battery — how would you then isolate whether it's the regulator itself or something else on the supply rail?
- How would you determine whether the disturbance is common-mode (affecting both inputs equally) or differential?

---

## Q3: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The first step is to understand what ±0.1°C accuracy means in terms of the electrical requirements. For a PT100 RTD, 0.1°C corresponds to approximately 0.385 Ω — so at a typical excitation current of 1 mA, that's 0.385 µV of signal change. This immediately tells me that the current source's stability and the measurement system's resolution are both critical.

For the current source itself, I'd consider the key error sources:

1. **Initial accuracy**: The absolute value of the current matters less than its stability, because a ratiometric measurement can cancel out the absolute error. If I use the same reference for both the current source and the ADC, then variations in the reference cancel. This is a key design principle — make the measurement ratiometric.

2. **Temperature drift**: The current source's temperature coefficient directly affects measurement accuracy. If the current drifts by 100 ppm/°C and the temperature changes by 10°C, that's 0.1% error — which could be significant. I'd look for a current source topology with low temperature drift, or use a precision reference IC with a known, low drift specification.

3. **Noise**: The current source's noise translates directly into measurement noise. I'd need to filter the excitation current or the measurement to achieve the required resolution. A low-pass filter on the measurement path is usually more practical than trying to make the current source itself noiseless.

4. **Self-heating**: The excitation current heats the RTD, causing a measurement error. For a PT100, 1 mA might cause 0.05–0.1°C of self-heating depending on the package and thermal environment. I'd need to either reduce the current, account for the self-heating in calibration, or use pulsed excitation to minimize average power.

For the circuit topology, I'd consider a few options:

- **Howland current pump**: This is a classic precision current source using an op-amp and matched resistors. Its accuracy depends heavily on resistor matching — I'd use precision resistors (0.1% or better) or a matched resistor network. The Howland pump's advantage is that it can source or sink current and can be referenced to ground.

- **Series resistor with precision voltage reference**: If the sensor's resistance is small compared to the series resistor, the current is approximately constant. For an RTD with 100–140 Ω over range, a series resistor of 10 kΩ with a 2.5V reference gives approximately 250 µA with only 0.4% variation over the full RTD range — but that variation is predictable and can be calibrated out.

- **Dedicated current source IC**: Some precision reference ICs include current source outputs with very low drift. These are simple to use but may not offer the flexibility needed.

I'd also think about the measurement architecture. A ratiometric approach — where the ADC's reference voltage is derived from the same source that drives the current — eliminates errors from reference drift. The ADC would measure the ratio of the RTD voltage to the reference voltage, which is independent of the absolute current value.

For the ±0.1°C requirement, I'd budget the errors: sensor tolerance (can be calibrated out), self-heating, current source drift, ADC resolution and noise, and reference drift. Each error source should be allocated a portion of the total budget, and I'd verify the design meets the budget through analysis and testing.

**Possible follow-ups:**
- How would you decide between a 2-wire, 3-wire, or 4-wire RTD connection, and what are the accuracy implications of each?
- How would you calibrate the system at manufacturing time to remove the sensor's initial tolerance and the current source's absolute error?

---

## Q4: How would you approach selecting between a SAR ADC and a sigma-delta ADC for a medical device that measures a slowly varying physiological signal (e.g., temperature or pressure) with high resolution, and what are the key trade-offs you'd consider?

**Answer:** For a slowly varying physiological signal, both SAR and sigma-delta ADCs can work, but they have fundamentally different strengths and weaknesses that I'd evaluate against the specific requirements.

**Sigma-delta advantages for this application:**
- Inherently high resolution — 16 to 24 bits are common, with the high resolution achieved through oversampling and noise shaping
- Excellent for low-bandwidth signals because the oversampling ratio can be very high, pushing quantization noise far out of band
- Built-in digital filtering that can provide excellent 50/60 Hz rejection if the decimation filter is designed appropriately
- Very good INL and DNL performance at high resolutions

**Sigma-delta disadvantages:**
- Latency — the digital filter introduces a delay between the analog input and the digital output. For a slowly varying signal this is usually acceptable, but it must be characterized
- The input multiplexing is more complex — sigma-delta ADCs are not well-suited to rapidly switching between multiple channels because the digital filter needs time to settle after each channel change
- The output data rate is limited by the oversampling ratio — for a 24-bit ADC with a 10 Hz output rate, the modulator might run at several MHz, but the effective throughput is low

**SAR ADC advantages:**
- Low latency — the conversion is essentially instantaneous, making SAR ADCs ideal for multiplexed systems
- Easy to multiplex multiple channels with fast settling
- Power scales with sampling rate — at low sample rates, SAR ADCs can be very power-efficient
- No latency or pipeline delay

**SAR ADC disadvantages:**
- Resolution is typically limited to 16–18 bits for practical purposes
- Achieving high resolution requires a very clean reference and careful layout — the SAR ADC is more sensitive to noise on the reference and supply
- No inherent filtering — any noise on the input is aliased into the passband, so an anti-aliasing filter is essential

For a single-channel, slowly varying signal, I'd lean toward a sigma-delta ADC because the high resolution and built-in filtering are valuable, and the latency is not a concern for temperature or pressure. The sigma-delta's oversampling also simplifies the anti-aliasing requirement — the analog filter can be much simpler because the modulator samples at a high rate.

However, if the device needs to measure multiple sensors and multiplex them into one ADC, a SAR ADC becomes more attractive. The multiplexer can switch between channels and the SAR ADC settles quickly, whereas a sigma-delta ADC would need a settling time after each channel change, reducing the effective throughput.

I'd also consider the system-level architecture. If the signal is already conditioned by an analog front-end with good filtering, a SAR ADC might be sufficient. If the raw sensor signal is being digitized directly, the sigma-delta's built-in filtering is a significant advantage.

Power consumption is another factor. For a battery-powered device that samples infrequently, a SAR ADC can be turned on, take a reading, and turned off very quickly. A sigma-delta ADC needs to run continuously for a period to produce a valid conversion, which might consume more energy per measurement.

Finally, I'd look at the resolution requirement carefully. "High resolution" doesn't necessarily mean high accuracy. A 24-bit sigma-delta ADC might have 24-bit resolution but only 18 bits of actual accuracy due to noise and linearity limits. I'd evaluate the ENOB (effective number of bits) rather than the raw resolution specification.

**Possible follow-ups:**
- How would the choice change if you needed to sample four different sensors at 100 Hz each?
- What anti-aliasing requirements would you have for each ADC architecture?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing the hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the hardware approach is necessary because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical design decision, and I'd approach it with the understanding that the disagreement isn't personal — it's about finding the right engineering solution. My goal would be to ensure the design meets the safety requirements while also being open to legitimate cost and space savings if they don't compromise safety.

First, I'd acknowledge the firmware lead's valid points. A firmware-based approach does offer flexibility — thresholds can be adjusted in software, and the implementation might be simpler. I'd want to show that I'm taking the proposal seriously, not dismissing it out of hand.

Then I'd reframe the discussion around the safety requirements rather than personal preference. For a medical device, the protection circuit's purpose is to prevent a hazardous condition — in this case, over-temperature that could harm the patient or damage the device. The question isn't which approach is cheaper or more flexible; it's which approach can be verified to meet the safety requirements.

I'd raise specific technical concerns:

1. **Failure independence**: The over-temperature protection is a safety function. If it's implemented in firmware, then a firmware failure — a hang, a stack overflow, an infinite loop — could disable the protection at exactly the moment it's needed. The hardware approach provides an independent layer of protection that doesn't depend on the firmware executing correctly.

2. **ADC failure modes**: The firmware-based approach relies on the ADC to measure temperature. If the ADC fails — perhaps it returns a stuck value or an incorrect reading — the protection might not trigger. A hardware comparator with a dedicated temperature sensor is a simpler, more predictable circuit that's easier to analyze for failure modes.

3. **Response time**: Depending on the thermal time constant of the system, the firmware approach might be fast enough. But if the temperature can rise quickly under fault conditions, the firmware's response time — including ADC conversion time, processing, and GPIO update — might be too slow. The hardware comparator can respond in microseconds.

4. **Verification and documentation**: For a medical device, the safety function needs to be verified and documented. A hardware comparator circuit is straightforward to analyze — I can calculate its response time, threshold accuracy, and failure modes. A firmware-based approach requires a different kind of verification, including code review, testing for edge cases, and demonstrating that the protection works even under fault conditions.

I'd also propose a middle ground. Perhaps the firmware-based monitoring can be added as a secondary layer of protection — a redundant check that complements the hardware circuit. The hardware provides the guaranteed, fail-safe protection, while the firmware can provide additional monitoring and diagnostics. This gives the firmware lead some of the flexibility they want while maintaining the safety integrity.

If the firmware lead still disagrees, I'd suggest we bring the decision to the project's risk management process. For a medical device, safety decisions shouldn't be made by whoever argues most persuasively in a design review — they should be made through a structured risk assessment that considers the failure modes, their severity, and the effectiveness of the mitigation. I'd propose we document both approaches, analyze the failure modes of each, and let the risk assessment guide the decision.

Throughout this, I'd maintain a collaborative tone. The firmware lead is a colleague with valid expertise, and the goal is to design the best possible device. I'd avoid making it a win-lose argument and instead focus on finding the solution that best serves the patient's safety and the project's success.

**Possible follow-ups:**
- What if the project manager pressures you to accept the firmware-based approach to meet a cost target? How would you handle that pressure?
- How would you document this decision in the design history file to show that the safety analysis was thorough and objective?