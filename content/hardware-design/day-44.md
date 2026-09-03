# hardware-design — Day 44

## Q1: How would you approach designing a power supply architecture for a medical device that contains both a high-resolution analog front-end (requiring a noise floor below 50 µV RMS) and a motor driver that can draw 1A peaks?

**Answer:** I'd start by separating the noisy and sensitive domains as early as possible in the architecture. The motor driver should be powered from its own rail, ideally directly from the battery or main supply through a dedicated regulator, while the analog front-end gets its own low-noise LDO chain. The key principle is to prevent the motor's 1A current transients from modulating the analog supply rail through shared impedance or ground bounce.

I would first map out the full current profile: the motor's peak, average, and slew rate, plus the analog section's consumption. Then I'd design the power tree with physical separation in mind — the motor driver's return current should not share a ground path with the analog reference or the ADC's ground. A star-point grounding scheme, or a split ground plane with a single connection point, is usually necessary.

For the analog rail, I'd use a two-stage approach: a switching regulator to step down from the battery efficiently, followed by a low-noise LDO with high PSRR to clean the rail. The LDO's PSRR at the switching frequency and its harmonics is critical — I'd check the PSRR curve across frequency, not just the DC value. I'd also add a pi-filter (ferrite bead plus capacitors) between the switching regulator and the LDO if the switching noise is still too high.

For the motor driver, I'd ensure it has its own bulk capacitance close to the driver to supply the 1A peaks locally, minimizing the transient draw seen by the main supply. I'd also consider whether the motor needs a freewheeling or snubber circuit to reduce EMI coupling into the analog section.

Finally, I'd verify the design with measurements: probe the analog rail with a scope (using a low-inductance ground connection) while the motor is running, and check that the noise stays below the 50 µV RMS budget. If it doesn't, I'd look at where the coupling path is — through the supply, through ground, or through radiated EMI — and address that specific path rather than adding generic filtering.

**Possible follow-ups:** How would you decide between a single ground plane with careful partitioning versus split ground planes? What if the motor driver and analog front-end must be on the same PCB with limited board area?

---

## Q2: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** A 1–10 Hz disturbance with amplitude that tracks the supply voltage points toward a low-frequency noise source that's coupling through the power supply path, rather than something in the signal chain itself. The first thing I'd do is confirm the disturbance is real and not a measurement artifact — I'd check the probe setup, ensure I'm not picking up ground loop noise from the scope, and verify the disturbance appears consistently across multiple measurement points.

Next, I'd look at the power supply. The fact that the amplitude varies with supply voltage suggests the disturbance is either riding on the supply rail or is being modulated by supply variations. I'd use a scope in AC-coupled mode to look at the supply rail directly, and I'd also check the reference voltage — a disturbance on the reference would directly appear at the output. I'd also check the ground: a low-frequency ground loop between the analog front-end and the power supply's ground return can easily cause this.

If the supply rail is clean, I'd suspect a thermal or mechanical source. A 1–10 Hz disturbance is in the range of thermal time constants — a component heating and cooling, or a mechanical vibration (like a fan or a loose connection) causing microphonic effects in a ceramic capacitor or the PCB itself. I'd try freezing components with freeze spray or touching them gently with a non-conductive probe to see if the disturbance changes.

Another possibility is that the disturbance is coming from the reference or bias circuitry — for example, a reference that's oscillating at a very low frequency due to instability, or a bias resistor that's noisy. I'd check the reference output directly and also look at the bias currents.

Finally, I'd consider whether the disturbance is actually a beat frequency between two switching regulators or between a switching regulator and the mains frequency. If there are two switchers on the board operating at slightly different frequencies, their beat could land in the 1–10 Hz range. I'd check the spectrum of the disturbance and correlate it with the switcher frequencies.

**Possible follow-ups:** How would you distinguish between a power supply issue and a ground loop issue? What if the disturbance only appears when the device is running on battery power but not when connected to a bench supply?

---

## Q3: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The first decision is the sensor type and excitation method. For an RTD, a common approach is a precision current source (e.g., 1 mA) with a four-wire (Kelvin) connection to eliminate lead resistance errors. For a thermistor, the excitation current must be low enough to avoid self-heating — typically 100 µA or less, depending on the thermistor's dissipation constant.

For the current source itself, I'd use a precision op-amp with a low-drift, low-noise voltage reference and a precision resistor to set the current. The key parameters are: the reference's initial accuracy and temperature drift, the resistor's tolerance and TCR, and the op-amp's offset voltage and bias current. For ±0.1°C accuracy, I'd budget the error sources carefully — for a PT100 RTD, 0.1°C corresponds to roughly 0.385 Ω, which at 1 mA is 385 µV. So the total error from the current source, reference, and measurement chain must stay well below that.

I'd use a topology like a Howland current source or a simple op-amp + transistor current source. The Howland source is attractive because it can be made with a single op-amp and precision resistors, but it's sensitive to resistor matching — I'd use a matched resistor network or trim the resistors. Alternatively, a simple two-transistor current mirror with a precision reference and resistor in the emitter is often more stable in practice.

For the reference, I'd choose a precision voltage reference with low drift (e.g., 5 ppm/°C or better) and low noise. The current-setting resistor should be a precision resistor with a low TCR (e.g., 10 ppm/°C or better) — a metal foil or thin-film resistor would be appropriate. The op-amp should have low offset voltage (under 50 µV) and low offset drift.

I'd also consider self-heating of the sensor. Even at 1 mA, an RTD can self-heat by a fraction of a degree if the dissipation constant is low. I'd calculate the self-heating error and either reduce the current or account for it in the calibration.

Finally, I'd design the measurement chain — the voltage across the sensor needs to be measured with a high-resolution ADC, and the ADC's reference and input circuitry must not introduce errors. A ratiometric measurement (using the same reference for the current source and the ADC) can cancel reference drift errors, which is a powerful technique for precision temperature measurement.

**Possible follow-ups:** How would you decide between a ratiometric and an absolute measurement approach? What if the sensor is located several meters away from the measurement electronics — how would that change your design?

---

## Q4: How would you approach selecting between a SAR ADC and a sigma-delta ADC for a medical device that measures a slowly varying physiological signal (e.g., temperature or pressure) with high resolution, and what are the key trade-offs you'd consider?

**Answer:** For a slowly varying physiological signal, the first question is what "high resolution" means in context — is it 16 bits, 20 bits, or higher? And what's the actual signal bandwidth? Temperature and pressure signals are typically DC to a few hertz, which is well within the range of both architectures.

Sigma-delta ADCs are often the natural choice for this application because they offer very high resolution (up to 24 bits) with excellent noise performance, and they have built-in digital filtering that can reject mains frequency and other out-of-band noise. Their oversampling architecture effectively moves the quantization noise to higher frequencies, where the digital filter removes it. They're also relatively immune to aliasing because the digital filter provides most of the anti-aliasing function — though I'd still include a simple RC filter at the input to prevent out-of-band signals from saturating the modulator.

SAR ADCs, on the other hand, are typically faster, have lower latency, and consume less power for a given sample rate. They're also easier to interface with a multiplexer if I need to sample multiple channels. However, achieving very high resolution (above 16 bits) with a SAR ADC requires careful attention to the reference, the driver amplifier, and the layout — the noise floor of a SAR ADC is often limited by the reference and the input driver rather than the ADC itself.

For a medical device measuring temperature or pressure, I'd lean toward a sigma-delta ADC if the signal is truly slow and I need high resolution with good noise rejection. The built-in digital filtering is a significant advantage — it simplifies the analog anti-aliasing filter and provides excellent rejection of 50/60 Hz interference. I'd also consider the power consumption: sigma-delta ADCs can be very low power if I choose a device with a low-power mode, but the digital filter runs continuously, so the power scales with the modulator rate.

One key trade-off is latency. Sigma-delta ADCs have inherent latency due to the digital filter — the output is a filtered average over a time window. For a slowly varying signal, this is usually acceptable, but if the device needs to respond quickly to a change (e.g., a pressure alarm), the latency might be a concern. SAR ADCs have essentially zero latency — each conversion is independent.

Another consideration is the multiplexing requirement. If I need to sample multiple sensors, a SAR ADC with an external multiplexer is straightforward — I can switch channels and get a conversion immediately. With a sigma-delta ADC, the digital filter needs to settle after each channel switch, which adds dead time. Some sigma-delta ADCs have a "chopper" mode or a fast-settle option, but it's still a consideration.

Finally, I'd look at the practical implementation details: the reference requirements, the input drive requirements (sigma-delta ADCs often need a low-impedance driver with a good settling time), and the digital interface. For a medical device, I'd also consider the device's track record in similar applications and whether it has the necessary documentation for regulatory compliance.

**Possible follow-ups:** How would the choice change if you needed to sample multiple channels? What if the signal had a bandwidth of 1 kHz instead of a few hertz?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing your hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the hardware approach is necessary because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** I'd approach this as a technical disagreement that needs to be resolved through data and risk analysis, not through authority or stubbornness. The first thing I'd do is acknowledge the firmware lead's valid points — saving board space and cost are legitimate concerns, and flexible threshold adjustment is genuinely useful. I'd want to make it clear that I'm not dismissing the firmware approach out of hand.

Then I'd frame the discussion around the safety requirements. In a medical device, the over-temperature protection is a safety function — it's there to prevent harm to the patient if something goes wrong. The question isn't whether the firmware approach *could* work in the normal case; it's whether it provides the same level of safety in the failure cases. I'd ask the firmware lead to walk through the failure scenarios: what happens if the firmware hangs? What happens if the ADC fails or its reference drifts? What happens if the GPIO is misconfigured during a firmware update? The hardware comparator and latch are independent of the firmware — they work even if the processor is completely dead.

I'd also bring up the regulatory angle. For a medical device, the safety function needs to be analyzed under IEC 60601 and ISO 14971. A firmware-based protection would require a much more rigorous software safety analysis — you'd need to demonstrate that the firmware can't fail in a way that defeats the protection, which typically means the software would need to be developed to a higher safety integrity level. That adds development time and cost, which might offset the savings from removing the hardware components.

Rather than just saying "no," I'd propose a middle ground: we could do a formal trade-off analysis, looking at the failure modes, the regulatory requirements, and the development cost for each approach. I'd also suggest that if the firmware lead is concerned about the hardware approach's inflexibility, we could design the hardware comparator with a resistor-divider that allows some threshold adjustment, or use a digital potentiometer to set the threshold — that gives us the flexibility without sacrificing independence.

If the firmware lead still disagrees, I'd escalate to the project manager or the safety officer, framing it as a safety engineering question that needs a formal risk assessment. I'd document the disagreement and the rationale for each position, so the decision is made with full information. The key is to keep the discussion focused on patient safety and regulatory compliance, not on who wins the argument.

**Possible follow-ups:** What if the project manager pressures you to accept the firmware approach to meet a tight schedule? How would you document the disagreement and the decision-making process for the design history file?