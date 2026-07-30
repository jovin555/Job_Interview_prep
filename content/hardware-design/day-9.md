# hardware-design — Day 9

## Q1: How would you approach designing a precision voltage reference circuit for a 16-bit SAR ADC that must maintain accuracy within ±1 LSB over a 0–50°C temperature range, given a 3.3V supply and a 2.5V reference voltage?

**Answer:** I'd start by calculating the actual voltage tolerance required. For a 16-bit ADC with a 2.5V reference, 1 LSB is approximately 38 µV. The reference must therefore maintain its output within ±38 µV over the full temperature range and including initial accuracy, line regulation, and long-term drift.

The first decision is whether to use a series reference or a shunt reference. For this application, a series reference is typically preferred because it offers lower quiescent current and better line regulation, which matters when the 3.3V supply may have ripple or droop.

I'd look for a reference with a temperature coefficient (tempco) of 5 ppm/°C or better. Over a 50°C range, a 5 ppm/°C reference would drift 250 ppm total, which is 625 µV — far exceeding the 38 µV budget. So I'd need a much tighter reference, likely 1 ppm/°C or lower, which would give 50 ppm over 50°C, or 125 µV — still marginal. Some precision references achieve 0.5 ppm/°C typical, yielding about 62.5 µV, which is closer but still tight.

This tells me the ±1 LSB requirement is extremely demanding and may not be achievable with a single reference alone. I'd consider a few approaches: using a higher-performance reference (e.g., a buried-zener type with a heater to stabilize temperature), implementing a ratiometric measurement scheme where the ADC reference and sensor excitation share the same reference voltage (cancelling drift), or adding a temperature sensor and software correction.

For the output buffer, I'd use a low-noise, low-drift op-amp with sub-µV/°C offset drift. The reference output should be Kelvin-connected to the ADC's reference input with a dedicated trace, and a low-ESR capacitor (typically 1–10 µF) placed right at the ADC reference pin per the datasheet recommendations. I'd also add a ferrite bead and a smaller bypass capacitor to filter high-frequency noise from the supply.

**Possible follow-ups:** How would you verify the reference's drift performance during board-level testing without an expensive temperature chamber? What would you do if the ADC's internal reference buffer has a lower bandwidth than expected, causing settling errors during fast channel switching?

---

## Q2: Walk me through how you would debug a circuit where a MOSFET used as a low-side switch for a 2A resistive load is getting hot (case temperature 85°C) even though the gate drive voltage appears correct (10V) and the load current measures 2A.

**Answer:** A MOSFET running hot at 2A with 10V gate drive suggests it's not fully in the ohmic (linear) region — it's operating in the saturation region with significant drain-source voltage drop. I'd start by measuring Vds directly at the MOSFET terminals with an oscilloscope, not just a multimeter, because the issue might be pulsed or intermittent.

If Vds is, say, 1V while conducting 2A, that's 2W of dissipation. In a typical SMD package like a DPAK or SO-8 with a thermal resistance of 40–60°C/W to ambient, 2W would produce an 80–120°C temperature rise, which matches the 85°C case temperature if ambient is around 25°C. So the question is: why is Vds so high?

Several possibilities come to mind. First, the MOSFET's Rds(on) might be higher than expected. I'd check the datasheet's Rds(on) specification at Vgs=10V and the actual junction temperature — Rds(on) increases with temperature (typically 0.5–1% per °C), so if the device is already hot, it could be in a thermal runaway loop. Second, the gate drive voltage at the MOSFET gate might not actually be 10V under load — I'd probe the gate-source voltage with an oscilloscope to check for ringing, droop, or insufficient drive current causing slow switching transitions.

Third, the MOSFET might be the wrong part for this application. Some MOSFETs are optimized for low-voltage logic-level gate drive (2.5–4.5V) and have higher Rds(on) at 10V, while others are optimized for higher gate voltages. I'd verify the specific Rds(on) curve in the datasheet.

Fourth, I'd check the PCB layout — if the MOSFET's drain or source connections have high resistance due to thin traces, insufficient copper area, or poor thermal vias, the effective resistance adds to the dissipation. I'd measure voltage drop across the PCB traces themselves.

Finally, I'd check for oscillation. A MOSFET with long gate traces can oscillate at high frequency due to parasitic inductance and capacitance, causing it to spend significant time in the linear region. I'd probe the gate with a short-ground-spring scope probe to look for high-frequency ringing.

**Possible follow-ups:** How would you determine whether the MOSFET is operating within its safe operating area (SOA) given the measured Vds and current? If you found the gate drive waveform had excessive ringing, how would you dampen it without slowing the switching speed too much?

---

## Q3: How would you approach designing a comparator-based overcurrent detection circuit for a medical device's motor driver output, where the threshold must be accurate to within ±5% over temperature and the response time must be under 10 µs?

**Answer:** I'd start by selecting a current-sense method. For a motor driver output, a low-side shunt resistor is simplest but creates a ground offset that can be problematic in medical devices with sensitive analog sections. A high-side shunt with a differential amplifier avoids ground disturbance but adds complexity and common-mode voltage challenges. For response time under 10 µs, a shunt resistor is the fastest approach since Hall-effect or fluxgate sensors typically have longer propagation delays.

I'd choose a shunt resistor value that produces a reasonable voltage drop at the threshold current — typically 50–100 mV full-scale to keep power dissipation low while providing enough signal for the comparator. For a 2A threshold, a 25 mΩ shunt gives 50 mV. The resistor must be a low-inductance type (e.g., metal-strip or thick-film) to avoid inductive voltage spikes during motor current transients that could falsely trigger the comparator.

The comparator selection is critical. I'd look for a device with internal hysteresis (typically 5–10 mV) to prevent oscillation near the threshold, a propagation delay under 5 µs (leaving margin for filtering and debounce), and a low input offset voltage — ideally under 1 mV to maintain accuracy. The comparator's input common-mode range must accommodate the shunt voltage.

For temperature stability, the shunt resistor's temperature coefficient matters. A ±50 ppm/°C resistor would drift ±1250 ppm over a 25°C range, or about ±0.125%, which is fine. The comparator's offset drift (typically 1–5 µV/°C) and the reference voltage drift are the dominant error sources. I'd use a precision voltage reference or a resistor divider from a regulated supply for the threshold voltage, with low-drift resistors (e.g., ±25 ppm/°C or better).

I'd add a small amount of filtering — perhaps an RC filter with a time constant of 1–2 µs — to reject motor commutation noise without exceeding the 10 µs response budget. The filter cutoff should be high enough that the comparator still triggers within spec.

Finally, I'd add a latch or retriggerable one-shot on the comparator output so that a single overcurrent event is captured and held for the system controller, rather than requiring the controller to poll fast enough.

**Possible follow-ups:** How would you test the response time and threshold accuracy during production? How would you handle the case where the motor's inrush current at startup briefly exceeds the overcurrent threshold?

---

## Q4: How would you approach selecting a ferrite bead for a power rail that supplies both a sensitive analog sensor (drawing 10mA) and a digital microcontroller (drawing 50mA with 10mA transient spikes at 1 MHz)?

**Answer:** This is a classic mixed-signal power filtering challenge where the ferrite bead must isolate the analog sensor from digital switching noise without causing voltage drop or resonance issues.

I'd start by characterizing the noise that needs to be attenuated. The microcontroller's 10mA spikes at 1 MHz will create voltage ripple on the power rail proportional to the impedance at that frequency. The analog sensor likely needs a clean supply — perhaps 100 µV or less of ripple — so I need significant attenuation at 1 MHz and its harmonics.

A ferrite bead's impedance curve typically rises with frequency, peaking in the 100 MHz–1 GHz range, and has relatively low impedance at 1 MHz — often just a few ohms. So a single ferrite bead may not provide enough attenuation at 1 MHz. I'd consider a two-stage filter: a bulk capacitor and a small inductor or a larger ferrite bead for the main rail, followed by an RC or LC filter dedicated to the analog sensor.

For the ferrite bead selection, I'd look at the DC resistance (DCR) first. With 60mA total current (10mA + 50mA), a DCR of 0.5Ω would drop 30mV, which is acceptable for a 3.3V rail. I'd check the current rating — the bead must handle 60mA continuous without saturating (ferrite beads don't saturate like inductors, but their impedance drops at high current). I'd also check the impedance at 1 MHz — if the bead offers only 10Ω at 1 MHz, the attenuation is limited. I might choose a bead with higher impedance (e.g., 100Ω at 100 MHz) and add a 10 µF capacitor on the output side to create a low-pass filter with a corner frequency around 10–100 kHz.

The critical risk with ferrite beads is resonance. The bead's inductance (typically 0.1–1 µH) combined with the downstream capacitance can create a parallel LC resonance that actually amplifies noise at certain frequencies. I'd simulate or calculate the resonant frequency and ensure it doesn't coincide with the microcontroller's switching frequency or its harmonics. Adding a small series resistor (e.g., 1–5Ω) or using a ferrite bead with higher effective resistance at resonance can dampen this.

For the analog sensor specifically, I'd add a dedicated LC filter (e.g., 10Ω + 10 µF) after the ferrite bead, providing additional attenuation at low frequencies where the ferrite bead is less effective.

**Possible follow-ups:** How would you measure whether the ferrite bead is actually reducing noise or making it worse due to resonance? What would you do if the analog sensor's supply current varied dynamically, causing the voltage drop across the ferrite bead to change and affect the sensor's accuracy?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead argues that the ADC sampling rate should be increased from 100 Hz to 1 kHz to improve measurement resolution through oversampling. You believe the higher rate will alias 50/60 Hz noise into the passband and require a much steeper anti-aliasing filter, increasing component count and board area. How would you handle this disagreement?

**Answer:** I'd approach this as a collaborative engineering trade-off rather than a confrontation. The firmware lead has a valid point — oversampling can improve effective resolution, and in many systems it's a perfectly reasonable approach. My concern about aliasing is also valid. The key is to quantify both positions so we can make a data-driven decision.

First, I'd acknowledge the firmware lead's goal and explain my concern clearly: "I understand you want to improve resolution through oversampling, which is a proven technique. My concern is that at 1 kHz sampling, the 50/60 Hz mains noise and its harmonics will alias into the 0–500 Hz baseband, and our current analog filter has a cutoff around 40 Hz with a gentle roll-off. We'd need a much steeper filter — likely a 4th or 5th order active filter — which adds 3–4 op-amps, additional passives, and board area. Let's work through the numbers together to see if the benefit justifies the cost."

I'd then propose a structured analysis. We'd calculate the effective resolution improvement from oversampling — oversampling by a factor of 10 (from 100 Hz to 1 kHz) gives about 1.5 extra bits of resolution if the noise is white and Gaussian. We'd compare that to the ADC's existing ENOB. If the ADC already has 14 ENOB and we only need 12 bits, oversampling may not be necessary.

Next, I'd look at the noise spectrum. If the dominant noise is 50/60 Hz (which is common in medical devices), oversampling doesn't help because the noise is deterministic, not random. In fact, oversampling can make it worse by aliasing harmonics. I'd suggest we measure the actual noise floor on a prototype to understand the spectrum.

If the firmware lead's goal is achievable through other means — such as a digital notch filter in firmware, or a synchronous sampling scheme that rejects mains noise — I'd explore those options. For example, sampling at exactly 100 Hz (synchronous with 50 Hz mains) would place mains noise at DC and its harmonics at multiples of 100 Hz, which are easily filtered digitally.

Ultimately, I'd propose a compromise: keep the analog filter as-is (or add a simple 2nd-order Sallen-Key with minimal extra cost), sample at 1 kHz, and implement a digital low-pass filter in firmware to remove aliased noise. This shifts the complexity from hardware to software, which may be acceptable if the microcontroller has spare MIPS. We'd prototype both approaches and compare the actual SNR and board area.

If we still disagreed after the analysis, I'd escalate to the project manager or systems engineer with our respective data, recommending a path based on the project's priorities — whether that's minimizing board area, maximizing resolution, or reducing firmware complexity.

**Possible follow-ups:** How would you structure a quick experiment to determine whether the aliasing concern is real or theoretical in your specific system? What if the firmware lead's manager pressures you to accept the change because "software is cheaper than hardware" — how would you respond?