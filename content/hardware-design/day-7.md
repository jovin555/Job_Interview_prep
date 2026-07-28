# hardware-design — Day 7

## Q1: How would you approach designing a buck converter for a medical device that must operate from a 12V input rail and deliver 3.3V at 2A, with strict requirements on output ripple (≤10mV peak-to-peak) and EMI?

**Answer:** I'd start by selecting a buck converter IC with an integrated high-side MOSFET rated for at least 1.5× the input voltage (18V minimum) and with adequate current capability—typically 3A or higher for margin. The switching frequency is a key trade-off: higher frequency (say 1–2 MHz) allows smaller inductor and capacitor values, which saves board space, but increases switching losses and makes EMI filtering harder. For a medical device, I'd lean toward 400–800 kHz to balance size with manageable EMI.

For the inductor, I'd calculate the required inductance based on the desired ripple current—typically 30–40% of the load current, so about 600–800 mA peak-to-peak. Using the standard buck formula: L = (Vin - Vout) × D / (ΔI × fsw), where D = Vout/Vin. I'd then verify the inductor's saturation current rating exceeds the peak current (Iload + ΔI/2) by at least 20%, and check its DC resistance (DCR) to ensure acceptable I²R losses.

For the output capacitor, the ripple voltage requirement of 10mV peak-to-peak drives the selection. The ripple has two components: the capacitive ripple (ΔI / (8 × fsw × Cout)) and the ESR ripple (ΔI × ESR). I'd choose a ceramic capacitor with low ESR—typically multiple 22–47 µF MLCCs in parallel to reduce both ESR and ESL. I'd also add a small feed-forward capacitor across the upper feedback resistor to improve transient response.

For EMI mitigation, I'd place the input capacitor as close as possible to the IC's input pin, use a dedicated ground plane under the converter, and add a ferrite bead plus a small capacitor (e.g., 100 pF) at the output to filter high-frequency noise. A snubber across the switching node (a series RC from switch node to ground) can damp ringing. Finally, I'd keep the feedback trace short and away from the inductor and switching node.

**Possible follow-ups:** How would you select the output capacitor's voltage rating considering DC bias derating? What would you do if the measured output ripple exceeds 10mV after the first prototype?

---

## Q2: How would you approach selecting a ferrite bead for a power rail that supplies both a sensitive analog sensor (drawing 10mA) and a digital microcontroller (drawing 50mA with 10mA transient spikes at 1 MHz)?

**Answer:** This is a classic mixed-signal power filtering challenge. The ferrite bead must attenuate the digital switching noise while not starving the analog sensor of clean power or causing excessive voltage drop during transients.

First, I'd characterize the noise I need to suppress. The microcontroller's 1 MHz switching transients are the primary concern—I want at least 20–30 dB attenuation at that frequency. I'd look at the ferrite bead's impedance vs. frequency curve: at 1 MHz, I'd target an impedance of 100–600 Ω, depending on how much isolation is needed.

Second, I'd check the DC resistance (DCR). At 60mA total current (10mA + 50mA), a DCR of 0.5 Ω would drop 30mV—acceptable for a 3.3V rail if the downstream devices can tolerate it. For the analog sensor, which is more sensitive, I might use a separate LDO or a second-stage RC filter after the ferrite bead.

Third, I'd verify the current rating. Ferrite beads can saturate at high DC bias, which reduces their impedance. I'd choose a bead rated for at least 100mA (2× the nominal current) to ensure the impedance doesn't collapse during the 10mA transients.

Fourth, I'd consider the resonant frequency. Some ferrite beads have a self-resonant peak that can actually amplify noise at certain frequencies. I'd check the datasheet and ensure the resonant frequency is well above my noise frequencies of interest.

Finally, I'd place the ferrite bead close to the microcontroller's power pin, with a bulk capacitor (10–47 µF) on the input side and a smaller decoupling capacitor (0.1 µF) on the output side. For the analog sensor, I'd add an additional RC filter (e.g., 10 Ω + 10 µF) after the ferrite bead to provide further attenuation.

**Possible follow-ups:** How would you test whether the ferrite bead is actually providing the expected attenuation in-circuit? What failure mode would you watch for if the bead is undersized for the DC current?

---

## Q3: How would you approach designing an active low-pass filter for a medical-grade ECG signal (0.5–100 Hz bandwidth) that must reject 50/60 Hz mains interference by at least 60 dB, while adding less than 2 µV RMS of noise?

**Answer:** For an ECG front-end, the filter must balance noise, phase response, and component tolerance. I'd use a multiple-feedback (MFB) or Sallen-Key topology—likely a 2nd-order Butterworth or Bessel filter. Bessel offers linear phase response, which preserves the ECG waveform shape (important for diagnostic accuracy), while Butterworth gives a sharper roll-off but with some phase distortion. For diagnostic ECG, I'd lean toward Bessel.

The cutoff frequency should be set around 100 Hz, with a notch at 50/60 Hz. I'd implement the notch using a twin-T or state-variable topology, but a simpler approach is to combine a 2nd-order low-pass (cutoff ~40 Hz) with a 2nd-order high-pass (cutoff ~0.5 Hz) to create a bandpass, then add a dedicated 50/60 Hz notch filter. The notch must be narrow (Q of 5–10) to avoid attenuating nearby cardiac frequencies.

For noise, the op-amp selection is critical. I'd choose a low-noise op-amp with input voltage noise density below 10 nV/√Hz—for example, the OPAx188 or ADA4528 series. With a bandwidth of 100 Hz, the integrated noise from the op-amp alone would be roughly 10 nV/√Hz × √(100 Hz × 1.57) ≈ 125 nV RMS, well within the 2 µV budget. Resistor thermal noise is another contributor: a 10 kΩ resistor generates about 12.9 nV/√Hz at room temperature, so I'd keep resistor values below 100 kΩ to stay under 40 nV/√Hz.

Component tolerance matters for notch filter depth. I'd use 1% resistors and 5% capacitors, and consider trimming the notch frequency with a digital potentiometer or by selecting capacitors in production. For the notch to achieve 60 dB rejection, the component matching must be within about 0.1%—which may require a switched-capacitor filter or an active notch with adjustable Q.

Finally, I'd simulate the filter in SPICE with Monte Carlo analysis to verify that worst-case component tolerances still meet the 60 dB rejection requirement. If not, I'd add a second-order notch stage or use a higher-order filter.

**Possible follow-ups:** How would you handle the 50/60 Hz notch if the device must work in both 50 Hz and 60 Hz regions? What would you do if the filter's phase shift causes visible distortion in the ECG waveform?

---

## Q4: How would you approach debugging a circuit where a MOSFET used as a low-side switch for a 2A resistive load is getting hot (case temperature 85°C) even though the gate drive voltage appears correct (10V) and the load current measures 2A?

**Answer:** A hot MOSFET at 2A with proper gate drive suggests excessive power dissipation, which comes from either conduction losses (I² × Rds(on)) or switching losses. Since the load is resistive and presumably DC or low-frequency, switching losses are likely minimal—so I'd focus on conduction losses first.

The first step is to measure the drain-to-source voltage (Vds) while the MOSFET is on. If Vds is, say, 0.5V at 2A, that's 1W of dissipation—which could explain 85°C depending on the package and thermal resistance. But if Vds is much higher (e.g., 2V), the MOSFET isn't fully enhanced despite the 10V gate drive.

I'd check the gate-to-source voltage (Vgs) directly at the MOSFET pins, not just at the gate driver output. There could be a voltage drop across a gate resistor or parasitic inductance. If Vgs is actually lower than 10V, the Rds(on) increases dramatically. For a typical logic-level MOSFET, Rds(on) might be specified at Vgs = 10V, but at Vgs = 5V it could be 2–3× higher.

Next, I'd verify the MOSFET's Rds(on) specification at the actual operating temperature. MOSFETs have a positive temperature coefficient—Rds(on) can double at 85°C compared to 25°C. If the datasheet specifies Rds(on) = 50 mΩ at 25°C, it might be 100 mΩ at 85°C, giving 0.4W dissipation (2A² × 0.1Ω). That's still modest, but if the thermal resistance (θJA) is 100°C/W, the junction temperature would rise 40°C above ambient—plausible for 85°C case temperature.

I'd also check for oscillation. A long gate trace or poor layout can cause the MOSFET to oscillate at high frequency, increasing switching losses. I'd probe the gate with a scope (using a short ground spring, not the long ground lead) to look for ringing or oscillation.

Finally, I'd verify the load is truly resistive. An inductive component (e.g., long cables) could cause the MOSFET to operate in the linear region during turn-off, dissipating significant power. I'd measure the current and voltage waveforms simultaneously to see if there's overlap during switching transitions.

**Possible follow-ups:** If you find the MOSFET is operating in the linear region during turn-off, how would you modify the gate drive to fix it? How would you calculate whether the MOSFET needs a heatsink given the measured power dissipation?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead argues that the ADC sampling rate should be increased from 100 Hz to 1 kHz to improve measurement resolution through oversampling. You believe the higher rate will alias 50/60 Hz noise into the passband and require a much steeper anti-aliasing filter, increasing component count and board area. How would you handle this disagreement?

**Answer:** I'd start by acknowledging the firmware lead's goal—improving measurement quality is a shared objective. Then I'd propose a structured, data-driven approach to resolve the disagreement rather than letting it become a debate of opinions.

First, I'd suggest we jointly analyze the noise spectrum of the sensor signal. We could capture the raw sensor output with a scope or data logger to see what frequencies are present, including 50/60 Hz pickup and any harmonics. This gives us a factual basis for the discussion.

Second, I'd explain the trade-off clearly: oversampling at 1 kHz could indeed improve resolution by about 2.5 bits (since oversampling by 10× gives roughly √10 ≈ 3.16× noise reduction, or about 1.6 bits), but it requires an anti-aliasing filter with a cutoff at 500 Hz (Nyquist) and steep roll-off to attenuate 50/60 Hz by at least 60 dB. That means a 4th or 5th order filter, which adds 2–3 op-amps, several precision resistors and capacitors, and significant board area. Alternatively, if we keep the 100 Hz sampling rate, a simple 2nd-order filter with cutoff at 30 Hz provides adequate anti-aliasing and 50/60 Hz rejection.

Third, I'd propose a compromise: we could test both approaches on a breadboard or in simulation. We'd build the simpler 2nd-order filter with 100 Hz sampling and measure the actual noise floor. If the noise is already acceptable for the clinical requirement, there's no need for oversampling. If it's marginal, we could consider a moderate increase to 200–300 Hz sampling with a 3rd-order filter, which might give enough oversampling benefit without the full complexity of a 1 kHz system.

Fourth, I'd involve the clinical or regulatory team to clarify the actual accuracy requirement. Often, engineers optimize for specifications that exceed what the clinical application needs. If the 100 Hz system meets the clinical requirement with margin, the higher sampling rate is unnecessary complexity and cost.

Finally, I'd document the decision with the supporting data—noise measurements, filter design options, and the clinical requirement—so the team has a clear record of why we chose one approach over the other. This prevents the same debate from recurring later.

**Possible follow-ups:** What if the firmware lead insists that oversampling is standard practice in their previous projects and refuses to compromise? How would you escalate this if you can't reach agreement?