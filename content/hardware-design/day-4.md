# hardware-design — Day 4

## Q1: How would you approach selecting decoupling capacitors for a mixed-signal PCB that contains both a high-resolution ADC and a wireless transmitter that bursts 100mA current pulses?

**Answer:** The key challenge here is that the ADC needs a clean, low-noise supply while the wireless transmitter creates large, fast current transients that can couple noise into the ADC's supply rail. I'd start by analyzing the frequency content of both the ADC's noise sensitivity and the transmitter's current profile.

For the ADC section, I'd follow the manufacturer's recommendations as a baseline, typically placing a 100nF ceramic capacitor as close as possible to each supply pin, with a smaller 10nF or 1nF for higher-frequency decoupling. The ADC's reference input would get its own dedicated decoupling, often a 10µF electrolytic or tantalum in parallel with 100nF ceramic, placed to minimize loop area.

For the transmitter, the burst current demands bulk capacitance to supply the instantaneous charge without drooping the rail. I'd calculate the required capacitance based on the burst duration, current magnitude, and allowable voltage droop. For example, if the transmitter draws 100mA for 100µs and I can tolerate 50mV droop, I'd need at least 200µF of bulk capacitance local to the transmitter. This bulk capacitance would be a combination of electrolytic or ceramic capacitors with low ESR.

Critically, I'd use a star-point or split-plane grounding strategy to keep the transmitter's return currents from flowing through the ADC's ground path. A ferrite bead on the ADC's supply rail, placed between the bulk supply and the ADC's local decoupling, can provide additional isolation at the transmitter's fundamental frequency and its harmonics. I'd verify the ferrite bead's impedance at the relevant frequencies and ensure it doesn't saturate under the DC bias current.

**Possible follow-ups:** How would you choose between using a ferrite bead versus a pi-filter for isolating the ADC supply? How would you simulate or measure whether your decoupling network is adequate before building the board?

---

## Q2: Walk me through how you would design an instrumentation amplifier front-end for a medical-grade biopotential measurement (e.g., ECG or EMG), from electrode to ADC.

**Answer:** Biopotential measurements present several challenges: the signals are very small (microvolt to millivolt range), they ride on a large DC offset (up to ±300mV from electrode half-cell potentials), and they're susceptible to 50/60Hz mains interference and motion artifacts.

I'd start with the electrode interface. The input stage needs very high input impedance (typically >10MΩ) to avoid loading the electrode-tissue interface, which has its own impedance that varies with frequency and skin preparation. I'd use an instrumentation amplifier (INA) as the first stage because it provides high common-mode rejection ratio (CMRR), high input impedance, and gain with a single external resistor.

The INA's gain would be set modestly, perhaps 10-100, to amplify the signal while keeping the DC offset within the amplifier's linear range. A right-leg drive circuit would be essential for ECG to actively cancel common-mode voltage at the body, improving effective CMRR by 40-60dB at mains frequencies.

After the INA, I'd add a high-pass filter to remove the DC offset and very low-frequency drift. For ECG, a cutoff around 0.05-0.5Hz is typical. This could be a passive RC filter or an active Sallen-Key stage, depending on whether I need buffering. Then a second gain stage would bring the signal to the ADC's full-scale range, followed by an anti-aliasing low-pass filter with cutoff at perhaps 40-100Hz for ECG, or higher for EMG.

The ADC selection would consider resolution and sampling rate. A 16-bit or 24-bit sigma-delta ADC with built-in PGA is common for these applications, as it can digitize the small signal directly with sufficient dynamic range. I'd pay careful attention to the reference voltage, using a low-noise precision reference.

Throughout the design, I'd use guard traces around the high-impedance inputs, maintain a clean analog ground plane, and keep digital signals and switching power supplies physically separated from the sensitive front-end.

**Possible follow-ups:** How would you protect the input stage against defibrillation pulses or ESD events that might occur in a clinical setting? What considerations would change if this were a wearable device running on a battery?

---

## Q3: How would you approach characterizing the input-referred noise of an op-amp circuit you've designed, and how would you use that information to determine whether the circuit meets a 10µV peak-to-peak noise requirement?

**Answer:** I'd approach this in two phases: analytical prediction during design, and empirical measurement on the prototype.

During design, I'd start with the op-amp's datasheet specifications for voltage noise density (e.g., nV/√Hz) and current noise density (pA/√Hz). I'd calculate the total noise over the circuit's bandwidth by integrating the noise spectral density, accounting for the gain of each stage and the noise contribution from resistors (Johnson-Nyquist noise). For a simple non-inverting amplifier, the dominant sources are typically the op-amp's voltage noise, the voltage noise from the feedback resistors, and the current noise flowing through the source impedance and feedback network.

I'd pay attention to the 1/f corner frequency — if the signal bandwidth extends below a few hundred Hz, the 1/f noise can dominate. I might choose a bipolar-input op-amp for lower voltage noise at low frequencies, or a JFET-input op-amp for lower current noise if source impedances are high.

For measurement, I'd short the inputs to ground (or to the expected source impedance), amplify the output noise through a known-gain stage, and observe it on an oscilloscope in AC-coupled mode. I'd capture a long time record and measure the peak-to-peak voltage, then divide by the total gain to refer it back to the input. Alternatively, I could use a spectrum analyzer or FFT to measure the noise spectral density and integrate it.

To determine if the circuit meets 10µV p-p, I'd compare the measured or calculated value against the requirement. A common rule of thumb is that the RMS noise multiplied by 6.6 gives the peak-to-peak value for Gaussian noise (99.9% confidence). So I'd need the input-referred RMS noise to be below about 1.5µV RMS. If the measured value exceeds this, I'd investigate whether the excess comes from the op-amp, the resistors, or external pickup, and adjust the design accordingly — perhaps by reducing resistor values, choosing a lower-noise op-amp, or narrowing the bandwidth.

**Possible follow-ups:** How would you distinguish between true circuit noise and 60Hz pickup from the measurement setup itself? What if the noise requirement is specified as a maximum RMS value rather than peak-to-peak?

---

## Q4: You're designing a battery-powered device that uses a boost converter to generate 5V from a single Li-ion cell (3.0-4.2V). The load has a 500mA peak current requirement. How would you select the inductor, and what parameters would you check to ensure the design is robust?

**Answer:** Selecting the inductor for a boost converter involves several trade-offs around size, efficiency, and output ripple. I'd start by determining the required inductance value based on the converter's switching frequency, input voltage range, output voltage, and desired inductor current ripple.

For a typical boost converter, I'd target the inductor current ripple to be about 20-40% of the average input current at nominal conditions. The worst-case ripple usually occurs at the minimum input voltage (3.0V) because the duty cycle is highest. Using the standard boost inductor equation, I'd calculate the minimum inductance needed to keep the ripple within that range.

Once I have a candidate inductance value, I'd check several key parameters:

1. **Saturation current (Isat):** The inductor must not saturate at the peak current, which is the average input current plus half the ripple current. I'd derate this by at least 20% to account for temperature effects and manufacturing tolerance. Saturation causes a sharp drop in inductance, leading to excessive current and potential damage.

2. **DC resistance (DCR):** Higher DCR increases I²R losses, reducing efficiency and generating heat. For a 500mA load, I'd look for DCR in the milliohm range, perhaps 20-100mΩ depending on the physical size.

3. **Self-resonant frequency (SRF):** The inductor's SRF should be well above the switching frequency (typically 10x or more) to ensure it behaves as an inductor rather than a capacitor at the switching frequency.

4. **Core material:** For a medical device, I'd consider shielded inductors to minimize EMI. Ferrite cores are common for switching frequencies in the hundreds of kHz to low MHz range. I'd also check for audible noise — some inductors can whine at frequencies in the audible range under certain load conditions.

5. **Thermal performance:** I'd check the inductor's rated current and temperature rise specifications, ensuring the device's ambient temperature plus self-heating stays within the inductor's rated temperature range.

Finally, I'd verify the inductor physically fits the board and meets any height constraints, especially in a portable device. I'd also simulate or breadboard the design to confirm the ripple and efficiency match calculations before committing to the layout.

**Possible follow-ups:** How would the inductor selection change if the boost converter needed to operate in discontinuous conduction mode (DCM) at light loads? What failure modes would you test for during validation?

---

## Q5: (Behavioral) Imagine you're leading a design review for a medical device's sensor interface, and the firmware lead argues that the ADC sampling rate can be reduced to save power, while you believe the lower rate will alias noise into the passband and degrade measurement accuracy. How would you handle this disagreement?

**Answer:** This is a classic cross-disciplinary trade-off where both perspectives have merit, and the right answer depends on the system requirements. I'd approach it by first acknowledging the firmware lead's valid concern — power consumption is critical in a battery-powered medical device, and reducing the sampling rate is a legitimate way to save it.

I'd then suggest we work through the problem together quantitatively. I'd ask: what is the bandwidth of the physiological signal we're measuring? What is the noise spectrum present at the analog front-end output? If the signal bandwidth is, say, 100Hz and the firmware lead proposes sampling at 200Hz (the Nyquist rate), I'd explain that any noise above 100Hz would alias into the signal band. I'd show the anti-aliasing filter's roll-off characteristics and demonstrate that with a 200Hz sample rate, we'd need a very sharp filter to prevent aliasing, which would require more poles and potentially introduce phase distortion.

Instead of simply opposing the idea, I'd propose alternatives that could satisfy both goals. For example:
- Could we use a sigma-delta ADC that oversamples and decimates internally, achieving high resolution with lower power than a SAR ADC running at high speed?
- Could we keep the ADC sampling at a higher rate but duty-cycle the analog front-end, powering it down between samples?
- Could we add a simple RC anti-aliasing filter before the ADC that's adequate for the lower sample rate, accepting some signal attenuation at the band edge?

I'd suggest we prototype both approaches and measure actual power consumption versus signal quality, using the device's accuracy requirements as the acceptance criteria. If we can't reach agreement, I'd escalate to the project manager or systems engineer, framing the decision as a documented trade-off with clear rationale, so the choice is recorded for future reference and regulatory traceability.

**Possible follow-ups:** What if the firmware lead has already implemented the lower sampling rate and the prototype is built — how would you determine whether aliasing is actually causing a problem? How would you document this decision for a regulatory submission like an IEC 60601 design history file?