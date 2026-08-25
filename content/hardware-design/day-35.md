# hardware-design — Day 35

## Q1: How would you approach designing a precision voltage reference circuit for a 16-bit SAR ADC that must maintain accuracy within ±1 LSB over a 0–50°C temperature range, given a 3.3V supply and a 2.5V reference voltage?

**Answer:** The first step is to establish the accuracy budget. For a 16-bit ADC with a 2.5V reference, 1 LSB is approximately 38 µV. That's the total error budget across the entire signal chain, so the reference alone must consume only a fraction of it — typically I'd allocate no more than 25–30% of the budget to the reference itself.

Starting with the reference IC selection, I'd look at initial accuracy, temperature drift, and long-term stability. A ±0.05% initial tolerance translates to 1.25 mV, which is far too large for a 38 µV budget — so initial accuracy alone tells you that you need either a trimmable reference or one with much tighter specs. In practice, this means either choosing a reference with very low initial tolerance (which gets expensive) or planning for a calibration step at manufacturing to remove the initial offset.

The temperature drift is the harder constraint. Over 0–50°C, that's a 50°C span. To stay within, say, 10 µV of drift, you need a temperature coefficient of about 0.08 ppm/°C — which is essentially unobtainable in a standard reference. This tells me the real design approach is to combine a moderate-drift reference with system-level calibration. A reference with 2–5 ppm/°C drift would contribute 250–625 µV over the range, so the calibration must be done at multiple temperatures, or the system must accept a larger error budget than ±1 LSB at the extremes.

For the circuit itself, I'd pay close attention to the reference's output drive capability. A SAR ADC's reference input draws dynamic current during conversion — the internal capacitor array charges and discharges each sample. If the reference can't source that current transient without drooping, you get conversion errors that look like reference noise. I'd add a low-leakage, low-ESR capacitor (typically 1–10 µF) right at the reference output, and possibly a small series resistor to isolate the reference from the ADC's switching transients, forming a low-pass filter. The capacitor value needs to be large enough that the voltage droop during a conversion is negligible.

Layout is critical. The reference output trace should be short and direct to the ADC's REF pin, with a solid ground return. I'd keep the reference away from digital traces and switching regulators, and I'd use a dedicated ground island if the layout allows. The reference's power supply pin needs its own decoupling — a ferrite bead plus bulk and high-frequency capacitors — to isolate it from supply noise.

Finally, I'd verify the design with a measurement plan: characterize the reference's actual drift over temperature on a sample of boards, measure the ADC's code transitions against a known input, and confirm the total error stays within budget. This isn't a "set and forget" component — it needs empirical validation.

**Possible follow-ups:**
- How would you handle the trade-off between using a precision reference IC versus calibrating out the errors in firmware?
- What specific ADC reference input characteristics would you check in the datasheet to size the bypass capacitor correctly?

---

## Q2: How would you approach debugging a circuit where a MOSFET used as a low-side switch for a 2A resistive load is getting hot (case temperature 85°C) even though the gate drive voltage appears correct (10V) and the load current measures 2A?

**Answer:** The first thing I'd question is the assumption that the MOSFET is fully turned on. A case temperature of 85°C with 2A through the device suggests significant power dissipation — let's estimate: if the thermal resistance from junction to ambient is around 50–60°C/W, then 85°C case temperature with, say, 25°C ambient implies roughly 1–1.2W of dissipation. At 2A, that means the drain-source resistance is around 0.25–0.3Ω. If the MOSFET's datasheet specifies RDS(on) at 10V gate drive as, say, 50 mΩ, then the device is not operating in the fully enhanced region — it's likely in the linear region, partially turned on.

So the debugging approach starts with measuring the actual drain-source voltage while the load is active. If VDS reads, say, 0.5V at 2A, that confirms the device isn't fully enhanced. The question then becomes: why?

The most common cause is insufficient gate drive voltage relative to the MOSFET's threshold and the actual gate-source voltage at the device. Even if the gate driver outputs 10V, the voltage at the gate pin might be lower due to a series resistor, a pull-down network, or a damaged gate. I'd measure the gate-source voltage directly at the MOSFET pins, not at the driver output. I'd also check the gate waveform on an oscilloscope — if the gate is being driven with PWM, the average voltage might look correct on a multimeter, but the actual on-time might be short, or the gate might be ringing.

Another possibility is that the MOSFET is the wrong part for the application — perhaps it's a logic-level device that needs 4.5V for full enhancement, or perhaps it's a standard-level device that needs 10V but the gate drive is actually lower than measured. I'd verify the part number and check the RDS(on) specification at the actual gate voltage and current.

I'd also check for parasitic issues: a high-value resistor between the gate driver and the gate (sometimes added for slew-rate limiting) that's dropping voltage, or a gate-source capacitor that's slowing the turn-on. If the gate drive is a slow ramp rather than a fast transition, the MOSFET spends significant time in the linear region during each switching cycle, dissipating power.

Finally, I'd check the thermal path. Even with correct operation, if the PCB copper area under the MOSFET is insufficient, the thermal resistance will be higher than expected, and the case will run hot. The datasheet's thermal specs assume a certain PCB copper area — if the layout doesn't match, the temperature will be higher even with normal dissipation.

**Possible follow-ups:**
- If you find the gate voltage is correct at the pin but the MOSFET is still not fully enhanced, what other device parameters would you investigate?
- How would you determine whether the issue is switching loss versus conduction loss if the gate is being driven with PWM?

---

## Q3: How would you approach designing a comparator-based overcurrent detection circuit for a medical device's motor driver output, where the threshold must be accurate to within ±5% over temperature and the response time must be under 10 µs?

**Answer:** This is a classic "speed versus accuracy" design problem, and the key is to recognize that the current sense element and the comparator are both contributors to the error budget.

Starting with the sense element: a low-value shunt resistor is the most straightforward approach. For a motor drawing, say, 2A, a 10 mΩ shunt gives 20 mV of sense voltage — small but workable. The shunt's tolerance and temperature coefficient directly affect threshold accuracy. A 1% tolerance resistor with a 50 ppm/°C temperature coefficient would contribute roughly 1.5% error over a 50°C range — that's within budget but leaves little room for other errors. I'd consider a 0.5% or 0.1% resistor with a low TCR, or possibly a current-sense amplifier with an integrated shunt.

The comparator's input offset voltage is the next major error source. A typical comparator has 1–5 mV of offset, which on a 20 mV sense signal is 5–25% error — far too much. This is where the design gets interesting. Options include: using a precision comparator with sub-millivolt offset (more expensive), using a current-sense amplifier ahead of the comparator (adds propagation delay), or using a comparator with a built-in reference and hysteresis that's designed for this application.

The response time requirement of under 10 µs drives the comparator selection. Standard comparators have propagation delays of 10–40 ns, which is fine. The bigger delay contributor is the filtering you might add to reject noise. A simple RC filter on the sense signal will add delay — an RC time constant of 1 µs means the comparator won't trip until several microseconds after the actual overcurrent event. I'd need to balance noise immunity against response time, possibly using a comparator with built-in hysteresis rather than an external RC filter.

For the threshold reference, I'd use a precision voltage divider from a stable reference, not from the motor supply rail, since the supply can sag during motor actuation. The divider resistors need tight tolerance and low TCR to maintain the ±5% threshold accuracy.

The comparator output needs to drive the shutdown mechanism — typically a latch or directly the motor driver's enable pin. I'd add a small amount of positive feedback (hysteresis) to prevent chatter at the threshold, but the hysteresis value must be small enough not to significantly shift the effective threshold.

Finally, I'd verify the design with bench testing: sweep the load current through the threshold and measure the actual trip point and response time across temperature. The layout matters too — the shunt should be in the motor return path with Kelvin connections to the sense amplifier, and the comparator should be close to the shunt to minimize parasitic inductance.

**Possible follow-ups:**
- How would you handle the trade-off between adding a filter for noise immunity and meeting the 10 µs response time?
- What failure modes would you consider for the shunt resistor itself, and how would you detect them?

---

## Q4: How would you approach selecting a ferrite bead for a power rail that supplies both a sensitive analog sensor (drawing 10mA) and a digital microcontroller (drawing 50mA with 10mA transient spikes at 1 MHz)?

**Answer:** The first thing I'd clarify is the design intent: is the ferrite bead meant to isolate the analog sensor from the microcontroller's switching noise, or is it meant to filter the incoming supply rail? The answer changes the selection criteria significantly.

Assuming the goal is to isolate the analog sensor from the digital noise, I'd place the ferrite bead in series with the analog sensor's supply, not on the shared rail. The bead's impedance at 1 MHz — the frequency of the microcontroller's transient spikes — is the key parameter. I'd look for a bead with high impedance at 1 MHz, typically 100–600Ω at that frequency, while keeping DC resistance low to minimize voltage drop to the sensor.

The DC resistance matters because the sensor draws 10 mA continuously. A bead with 0.5Ω DCR would drop 5 mV — that might be acceptable or not, depending on the sensor's supply tolerance. I'd check the sensor's PSRR and supply voltage range to determine the allowable drop.

The current rating is also important. The bead must handle the 10 mA DC plus any transient current without saturating. Ferrite beads have a current-dependent impedance — as current increases, the bead's impedance decreases because the ferrite material saturates. I'd check the impedance versus current curve in the datasheet and ensure the bead maintains sufficient impedance at the actual operating current.

The impedance at the noise frequency is the primary selection criterion, but I'd also consider the bead's resonant frequency. Ferrite beads have a parallel resonance where they become inductive rather than resistive. If the bead's resonance falls near 1 MHz, it won't provide the expected filtering. I'd select a bead with resonance well above the noise frequency.

I'd also pair the ferrite bead with capacitors on both sides. The capacitor on the microcontroller side provides a low-impedance path for the transient current, while the capacitor on the sensor side forms a second-order low-pass filter with the bead. The capacitor values depend on the frequencies involved — for 1 MHz noise, I'd start with 0.1 µF on the sensor side and 10 µF on the supply side, then adjust based on measurement.

Finally, I'd verify the design empirically. I'd measure the noise on the sensor's supply pin with and without the bead, using a spectrum analyzer or oscilloscope with sufficient bandwidth. The bead's effectiveness depends on the actual noise spectrum, which may differ from the theoretical 1 MHz spike frequency.

**Possible follow-ups:**
- How would you determine whether a ferrite bead or an LC filter is more appropriate for this application?
- What would you check in the ferrite bead's datasheet to ensure it doesn't introduce a resonance that amplifies noise at a specific frequency?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead argues that the ADC sampling rate should be increased from 100 Hz to 1 kHz to improve measurement resolution through oversampling. You believe the higher rate will alias 50/60 Hz noise into the passband and require a much steeper anti-aliasing filter, increasing component count and board area. How would you handle this disagreement?

**Answer:** I'd start by acknowledging the firmware lead's underlying goal — improving measurement resolution is a legitimate objective, and oversampling is a valid technique when applied correctly. The disagreement isn't about the goal; it's about the method and the system-level implications.

I'd then frame the discussion around the actual signal chain and the math. The key question is: what's the signal bandwidth, and what's the noise spectrum? If the physiological signal of interest is, say, 0.5–100 Hz, then sampling at 100 Hz is already marginal — the Nyquist frequency is 100 Hz, and any noise above that aliases into the passband. That's why the anti-aliasing filter is there in the first place. Increasing to 1 kHz sampling doesn't inherently solve the aliasing problem — it just moves the Nyquist frequency to 500 Hz. The 50/60 Hz mains noise is still in the passband, and now you also have to worry about noise between 100 Hz and 500 Hz that wasn't a concern before.

The oversampling argument has merit if the noise is broadband and random — oversampling and averaging can improve resolution by reducing the noise bandwidth. But if the dominant noise is at specific frequencies (50/60 Hz and harmonics), oversampling alone won't help; you'd need to filter those frequencies specifically, which is what the anti-aliasing filter does.

I'd propose a structured approach to resolve this: first, characterize the actual noise spectrum on the bench. Measure the noise at the ADC input with the current filter and sampling rate, and identify the dominant noise sources. If the noise is broadband, oversampling might genuinely help, and we could explore it. If the noise is dominated by mains pickup, then the anti-aliasing filter is the right solution, and we should focus on improving that instead.

I'd also raise the practical concerns: a steeper anti-aliasing filter means more components, more board area, and potentially more phase delay in the signal path. For a medical device, we also need to consider the regulatory implications — any change to the signal chain requires re-verification, and the documentation burden is significant.

Rather than digging in on my position, I'd propose a small experiment: implement both approaches on a prototype or in simulation, measure the actual signal quality, and let the data drive the decision. This turns the disagreement into a collaborative engineering problem.

**Possible follow-ups:**
- What if the firmware lead insists that oversampling is a standard technique and your concerns are unfounded? How would you respond?
- How would you involve other stakeholders (e.g., regulatory, systems engineering) in this decision?