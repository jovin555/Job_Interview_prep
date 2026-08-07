# hardware-design — Day 17

## Q1: How would you approach designing a hardware-based overcurrent protection circuit for a motor driver in a medical device, where the protection must be independent of the main microcontroller and must respond within microseconds?

**Answer:** The core requirement here is that protection must work even if firmware hangs, the ADC fails, or the main processor is in a reset state — so the protection path must be purely analog. I'd start by defining the trip threshold and the response time budget. For a motor driver, the concern is usually both peak current (which can damage the MOSFETs or demagnetize the motor) and sustained overcurrent (which causes thermal damage). 

The classic approach is a low-side sense resistor in series with the motor return path, feeding a comparator with a precision reference. The sense resistor value is a trade-off: larger values give better signal-to-noise ratio at the comparator input but waste power and add voltage drop that reduces motor headroom. I'd typically target 50–100 mV of full-scale sense voltage to keep power dissipation manageable.

The comparator itself needs to be fast — propagation delay under 100 ns is achievable with standard comparators — and it must have hysteresis to prevent chatter when the current hovers near the threshold. The hysteresis band needs to be wider than the expected ripple from the motor's PWM switching, otherwise you get false trips. I'd also add a small RC filter on the sense input to reject switching transients, but the filter time constant must be short enough that the total delay (filter + comparator + latch + gate drive) still meets the response time requirement.

Once the comparator trips, it should drive a latch (a simple SR latch built from NAND gates or a dedicated latch IC) that holds the fault state. The latch output then disables the gate driver directly — not through the microcontroller. The reset path should be deliberate: either a manual reset button, a power-cycle, or a separate "fault acknowledge" signal from the MCU that's only enabled after the fault condition is verified clear.

A key design consideration is the reference voltage accuracy. If the threshold must be ±5% over temperature, a simple resistor divider from the supply rail won't suffice — I'd use a dedicated reference IC or a precision shunt reference. The sense resistor tolerance and temperature coefficient also contribute directly to threshold error, so a 1% or 0.5% resistor with a low TCR is usually warranted.

Finally, I'd verify the protection in fault injection testing: short the motor output, stall the motor, and ramp the supply voltage to confirm the protection trips consistently and within the time budget across temperature.

**Possible follow-ups:** How would you test that the protection circuit itself doesn't false-trip during normal motor startup inrush? What happens if the sense resistor itself fails open — how does the circuit fail safe?

---

## Q2: How would you approach selecting the decoupling capacitor network for a high-resolution ADC that shares a PCB with a wireless radio transmitting periodic bursts?

**Answer:** The challenge here is that the radio's current draw creates transient dips on the supply rail, and those dips can couple into the ADC's reference or analog supply and corrupt conversions. The decoupling strategy needs to address both the high-frequency content of the radio's switching edges and the lower-frequency envelope of the burst itself.

I'd start by characterizing the problem: what's the radio's current profile (peak, rise time, burst duration, duty cycle), and what's the ADC's PSRR as a function of frequency? The ADC datasheet gives PSRR at DC and maybe at 100 kHz, but the radio's current transient can have energy at much higher frequencies. If the PSRR data isn't available at the frequencies of interest, I'd plan to measure it or add margin.

The decoupling network should be staged. Right at the ADC's power pin, I'd place a small-value, low-ESL capacitor (e.g., 100 nF in 0402 or 0201 package) to handle the highest-frequency transients. Just beyond that, a larger value (1–10 µF) in a small package with low ESL. Then, at the point where the radio's supply branches off, I'd add bulk capacitance (47–100 µF) to absorb the radio's burst energy. The key is that the radio's decoupling should be local to the radio — the bulk cap for the radio should be at the radio, not shared with the ADC.

A ferrite bead between the main supply rail and the ADC's analog supply is often effective, but I'd check the bead's impedance at the radio's fundamental and harmonic frequencies. The bead creates a low-pass filter with the ADC's local capacitance, and the cutoff should be well below the radio's switching frequency. However, the bead also adds series resistance, which causes DC drop — I'd verify the ADC's supply voltage remains within spec under worst-case current.

One subtle point: the ground return path matters as much as the supply path. If the radio and ADC share a ground return with significant impedance, the radio's current transient creates a ground bounce that appears as a common-mode voltage at the ADC's input. I'd ensure the ADC's analog ground and the radio's ground are connected to the main ground plane with short, low-impedance paths, and I'd avoid routing any analog signals near the radio's ground return.

Finally, I'd verify the design by measuring the ADC's output noise with the radio transmitting versus idle. If the noise increases during transmission, I'd use a spectrum analyzer on the supply rail to identify the coupling frequency and adjust the filter accordingly.

**Possible follow-ups:** How would you decide whether to use a ferrite bead versus a pi-filter for the ADC supply? What if the ADC's PSRR datasheet doesn't cover the radio's frequency range?

---

## Q3: How would you approach designing an active anti-aliasing filter for a medical biopotential measurement system (e.g., ECG) that must pass 0.5–100 Hz and reject out-of-band noise, while keeping the noise contribution below 2 µV RMS?

**Answer:** The first step is to define the filter requirements precisely. The passband is 0.5–100 Hz, so I need a high-pass corner below 0.5 Hz and a low-pass corner at or above 100 Hz. The stopband rejection depends on the ADC's sampling rate and the noise sources present. For ECG, the dominant out-of-band noise is typically 50/60 Hz mains and its harmonics, plus muscle artifact and motion artifact that extend to a few hundred Hz.

The filter topology choice is a trade-off between component count, noise, and phase response. A 2nd-order Sallen-Key low-pass is simple and uses few components, but its roll-off is only 40 dB/decade — if the ADC samples at 500 Hz, the filter needs to attenuate noise at 250 Hz (the Nyquist frequency) by enough to prevent aliasing. A 4th-order filter (two cascaded 2nd-order stages) gives 80 dB/decade, which is usually sufficient. Alternatively, a multiple-feedback (MFB) topology is less sensitive to component tolerance but inverts the signal and has higher noise at high gains.

For the op-amp selection, the key parameters are input voltage noise density, current noise density, and bandwidth. A low-noise op-amp with 5–10 nV/√Hz voltage noise is typical. The resistor values in the filter also contribute Johnson noise — a 10 kΩ resistor generates about 12.8 nV/√Hz at room temperature. I'd keep resistor values in the 10–100 kΩ range to balance noise against capacitor size and bias current effects.

The noise budget: if the total noise must be under 2 µV RMS, I'd allocate maybe 1 µV RMS for the filter and 1 µV RMS for the rest of the signal chain. The filter's noise is the combination of the op-amp's voltage noise (shaped by the filter's bandwidth) and the resistor noise. For a 100 Hz bandwidth, the op-amp's white noise contributes roughly 5 nV/√Hz × √100 ≈ 50 nV RMS — well within budget. The resistor noise is similar. The real challenge is usually the 50/60 Hz notch, not the filter's intrinsic noise.

For the high-pass section, I'd use a 1st-order RC high-pass at 0.5 Hz or a 2nd-order Sallen-Key high-pass. The high-pass corner must be low enough to pass the ECG's ST segment without distortion — a 0.5 Hz corner with a 2nd-order response has about 12 dB of attenuation at 0.25 Hz, which may be acceptable depending on the clinical requirement. I'd verify the step response settling time, because a high-pass filter with too high a corner will cause baseline wander after a large transient (e.g., electrode movement).

Finally, I'd simulate the filter's frequency response and noise, then build and measure it. The measurement would include the filter's actual transfer function (using a network analyzer) and its output noise (using a low-noise preamp and spectrum analyzer). I'd also verify the filter's behavior with a realistic ECG signal containing 50/60 Hz interference to confirm the rejection is adequate.

**Possible follow-ups:** How would you handle the 50/60 Hz interference — would you use a notch filter, and what are the trade-offs? How would you verify the filter's phase response doesn't distort the ECG waveform?

---

## Q4: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** A low-frequency periodic disturbance that's present with the input shorted points to something in the power supply, reference, or ground path — not the signal path itself. The fact that it varies with supply voltage suggests the disturbance is coupled through the supply or is related to a supply-dependent bias point.

My first step would be to capture the disturbance on an oscilloscope with sufficient resolution and record duration. I'd look at the disturbance's exact frequency, amplitude, and waveform shape. Is it sinusoidal, sawtooth, or a pulse? Is it stable in frequency or does it drift? This tells me a lot about the source.

Next, I'd probe the power supply rail at the front-end's supply pin with an AC-coupled scope, using a low-inductance probe tip. If the disturbance appears on the supply, I'd trace it back: is it coming from the main supply, or is it generated locally? A 1–10 Hz disturbance on a supply rail often points to a thermal oscillation in a linear regulator — the regulator's output drifts with temperature, and the thermal time constant of the package creates a low-frequency feedback loop. This is especially common with LDOs operating near their dropout voltage or with insufficient output capacitance.

If the supply is clean, I'd check the voltage reference. A reference IC can oscillate at low frequency if its load capacitance is wrong or if it's unstable with the bypass capacitor value. I'd also check the reference's output with a high-resolution DMM or a nanovoltmeter to see if the disturbance is present there.

Another possibility is ground bounce or a ground loop. If the front-end's ground return shares a path with a switching regulator or a digital circuit that draws periodic current, the ground potential at the front-end can modulate at the switching frequency's envelope. But 1–10 Hz is unusually low for that — it's more likely a thermal or electrochemical effect.

I'd also consider the input protection network. If the input is shorted to ground through a protection diode or a capacitor, a leakage current that varies with temperature could create a small voltage that drifts. I'd check the short's quality — is it truly a low-impedance short, or is there a resistor in the path?

My systematic approach: (1) characterize the disturbance precisely, (2) probe supply, reference, and ground simultaneously to identify which node carries the disturbance, (3) isolate by powering the front-end from a clean bench supply and a separate reference, (4) if the disturbance persists, suspect the op-amp or front-end IC itself — possibly a bias current issue or a damaged part. I'd also check the PCB for contamination or moisture, which can create low-frequency electrochemical noise.

**Possible follow-ups:** How would you distinguish between a thermal oscillation in an LDO and a ground loop as the cause? What if the disturbance only appears when the device is battery-powered but not on a bench supply?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes moving the device's fault detection from a hardware comparator circuit to a firmware-based approach using the existing ADC and a GPIO. The firmware lead argues this will reduce cost and allow more flexible threshold adjustment. You believe the hardware approach is necessary because the fault detection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** I'd approach this as a technical disagreement that needs to be resolved through data and risk analysis, not through authority or stubbornness. The first thing I'd do is acknowledge the firmware lead's valid points — a firmware-based approach does offer flexibility, and reducing cost is a legitimate goal. Then I'd frame the discussion around the device's safety requirements and the failure modes we're protecting against.

I'd ask the firmware lead to walk through the failure scenarios: what happens if the firmware hangs while the motor is running? What happens if the ADC's reference drifts and the threshold becomes inaccurate? What happens if the ADC itself fails — does the fault detection fail open or fail safe? The key question is whether the firmware-based approach can guarantee the same safety integrity level as the hardware approach.

I'd also bring the regulatory perspective into the discussion. For a medical device, the fault detection is likely a safety mechanism that falls under IEC 60601 or ISO 14971. The risk analysis will need to demonstrate that the protection is reliable and fails safe. A hardware comparator with a latch is a simple, well-understood circuit that can be analyzed and tested deterministically. A firmware-based approach introduces more variables: the ADC's accuracy over temperature, the firmware's execution timing, the possibility of a hang or a stack overflow, and the interaction with other firmware tasks.

Rather than simply rejecting the proposal, I'd suggest a middle path: we could evaluate both approaches against the safety requirements and the risk analysis. If the firmware approach can meet the same safety integrity level with appropriate mitigation (e.g., a separate watchdog that monitors the firmware, or a redundant hardware path for the most critical faults), then it might be viable. But I'd want to see the analysis before agreeing.

I'd also propose a practical experiment: we could prototype the firmware-based approach and test it under fault injection — hang the firmware, corrupt the ADC reading, and see how the protection behaves. If the testing shows it's reliable, I'd be willing to reconsider. If not, we have data to support the hardware approach.

The key is to keep the discussion focused on patient safety and regulatory compliance, not on whose idea wins. I'd document the discussion, the analysis, and the decision in the design history file, so the rationale is captured for the regulatory submission.

**Possible follow-ups:** How would you handle the situation if the firmware lead refuses to accept your analysis and escalates to the project manager? What if the project manager pressures you to accept the firmware approach to meet a cost target?