# hardware-design — Day 24

## Q1: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The core requirement here is that a fault condition must persist until a deliberate reset action occurs — the system must not auto-recover from a potentially dangerous condition. I'd start by defining the fault input and the reset mechanism clearly.

For the latch itself, a classic approach is a SCR-style latch using two transistors (a PNPN structure) or a dedicated latch IC, but for medical devices I'd typically prefer a comparator with positive feedback (hysteresis) driving a latching element. The comparator monitors the fault condition (e.g., temperature via a thermistor or current via a sense resistor) against a reference. Positive feedback ensures that once the comparator trips, it stays tripped even if the input returns to normal.

For the reset path, I'd require two independent conditions: the fault must actually be cleared (e.g., temperature below a safe threshold), and a deliberate user action must occur (e.g., a reset button press). This prevents automatic recovery. The reset signal should be debounced and edge-triggered, not level-triggered, so a stuck button doesn't cause repeated reset attempts.

A key design consideration is the power-on state. The latch must default to a safe state on power-up — if the device is powered on while a fault condition exists, it should latch immediately rather than starting up normally. This requires careful sequencing of the reference voltage and the monitored signal.

For a medical device, I'd also add a test mechanism — a way to verify the latch circuit itself is functional during manufacturing test or periodic self-test, since a failed latch could be a silent failure. This might be a test input that simulates a fault condition and checks that the latch trips correctly.

**Possible follow-ups:**
- How would you ensure the latch doesn't false-trigger during power-up transients or normal inrush currents?
- What failure modes of the latch circuit itself would you consider, and how would you detect them?

---

## Q2: How would you approach selecting the inductor for a boost converter that must deliver 5V at 500mA from a single Li-ion cell (3.0–4.2V), where the load has fast current transients?

**Answer:** The inductor selection for a boost converter involves several interacting parameters, and the fast transient requirement adds an important constraint beyond steady-state operation.

First, I'd calculate the required inductance based on the switching frequency and the allowable ripple current. A common rule of thumb is to target ripple current at 20–40% of the maximum input current. For a boost converter, the input current is higher than the output current — at minimum input voltage (3.0V) and 5V/500mA output, the input current is roughly 1A at 85% efficiency, so ripple might be 200–400mA peak-to-peak. This gives an inductance in the range of 4.7–10µH for typical switching frequencies around 1–2MHz.

The critical parameter for the transient requirement is the inductor's saturation current rating. During a fast load transient, the inductor current can spike well above the steady-state average. I'd select an inductor with a saturation current rating at least 20–30% above the peak expected current, including the ripple component and transient overshoot. The saturation current must be specified at the worst-case temperature, since saturation current decreases as temperature rises.

I'd also check the DC resistance (DCR) — lower DCR improves efficiency but typically means a physically larger inductor. For a battery-powered device, efficiency directly impacts battery life, so this trade-off matters. The inductor's self-resonant frequency (SRF) should be well above the switching frequency to avoid parasitic effects.

Finally, I'd consider the inductor's core material. For a medical device, I'd prefer a shielded inductor to minimize EMI — the magnetic field from an unshielded inductor can couple into nearby sensitive analog circuitry. Ferrite cores are common, but for high-current applications, composite or iron-powder cores may be more appropriate as they handle DC bias better without saturating.

**Possible follow-ups:**
- How would you verify the inductor choice in the lab, particularly under transient load conditions?
- What happens if the inductor saturates during a transient — what's the failure mode and how would you protect against it?

---

## Q3: Walk me through how you would debug a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage.

**Answer:** This is a classic symptom pattern that points to a low-frequency, power-supply-coupled disturbance rather than an input-referred problem. Since the input is shorted, the disturbance is being injected somewhere in the signal chain — likely through the power supply, ground, or reference paths.

My first step would be to characterize the disturbance precisely. I'd capture the waveform on an oscilloscope with sufficient resolution to see the amplitude and frequency, and use an FFT to identify the exact frequency and any harmonics. The 1–10 Hz range is interesting — it's too slow for most switching regulators (which typically operate at hundreds of kHz) but could be a control-loop oscillation in a linear regulator, a thermal oscillation, or a beat frequency between two switching regulators.

Next, I'd check the power supply rails with a scope set to AC coupling and high sensitivity. If the disturbance appears on the supply rail, I'd trace it back to its source. A common cause is a linear regulator's control loop oscillating at low frequency due to an unstable load — this can happen with certain output capacitor ESR values. Another possibility is a switching regulator operating in pulse-skipping or burst mode at light load, which can produce low-frequency output ripple.

The fact that amplitude varies with supply voltage is a strong clue. This suggests the disturbance is coupled through the supply's PSRR — as the supply voltage changes, the disturbance amplitude changes because the PSRR is frequency-dependent and the operating point of the regulator changes.

I'd also check the reference voltage — if the ADC reference has low-frequency noise, it will appear as a disturbance on the output even with a shorted input. A reference with inadequate decoupling or a marginal stability margin can oscillate at low frequency.

My systematic approach would be: (1) characterize the disturbance precisely, (2) isolate the coupling path by powering sections from separate supplies, (3) check each supply rail and reference for the disturbance, (4) once the source is found, address it — this might mean adding bulk capacitance, adjusting the regulator's compensation, or improving decoupling.

**Possible follow-ups:**
- How would you distinguish between a power supply issue and a ground plane issue in this scenario?
- What test equipment would you use to isolate the disturbance source, and how would you set it up?

---

## Q4: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The key insight is that ±0.1°C accuracy requires understanding the entire signal chain — the current source, the sensor, and the measurement circuitry — and how each contributes to error over temperature.

For an RTD, which is more linear than a thermistor, the excitation current directly affects measurement accuracy. The current source must be stable over temperature and supply variations. I'd start by determining the required current level. For a PT100 RTD, a common choice is 1mA — high enough to produce a usable voltage (100–138.5mV over 0–100°C) but low enough to avoid self-heating errors. Self-heating is a critical consideration: even 1mA through an RTD can cause a fraction of a degree of error depending on the sensor's thermal resistance to the environment.

For the current source topology, I'd consider a few options. A simple approach is a voltage reference driving a precision op-amp with a sense resistor in the feedback loop — this creates a current that's set by the reference voltage divided by the sense resistor. The accuracy depends on the reference's initial tolerance and temperature drift, and the sense resistor's tolerance and TCR. For ±0.1°C, I'd need the current to be stable to roughly ±0.04% (since a PT100 has approximately 0.385 Ω/°C, and at 1mA that's 0.385 mV/°C — so ±0.1°C is ±38.5µV, which at 100–138.5mV signal range is about ±0.03–0.04%).

This drives component selection: a precision reference with low drift (e.g., 5 ppm/°C or better), a sense resistor with low TCR (e.g., 10 ppm/°C or better, possibly a metal foil resistor), and a low-offset, low-drift op-amp. I'd also consider a Kelvin (4-wire) connection to the sense resistor to eliminate trace resistance errors.

For the measurement side, I'd use a ratiometric approach where the ADC reference is derived from the same current source or voltage reference. This cancels first-order errors from reference drift. Alternatively, I'd use a differential measurement across the RTD with a high-impedance input to avoid loading errors.

I'd also budget the error sources: reference initial tolerance and drift, sense resistor tolerance and drift, op-amp offset and drift, and ADC errors. Each contributes to the total error budget, and I'd allocate the budget across components based on cost and availability.

**Possible follow-ups:**
- How would you handle the self-heating error, and what design choices would you make to minimize it?
- Would you use a ratiometric measurement approach, and if so, how would you implement it?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing your hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical design decision, and my responsibility as the hardware lead is to ensure the device meets its safety requirements — not to win an argument. I'd approach this as a collaborative engineering discussion grounded in the regulatory framework.

First, I'd acknowledge the firmware lead's valid points. The firmware approach does save board space and cost, and it does offer more flexibility in threshold adjustment. These are legitimate engineering trade-offs that deserve consideration.

Then, I'd reframe the discussion around the safety requirements. For a medical device, the over-temperature protection is a safety mechanism — it must prevent harm to the patient even under fault conditions. The key question is: what happens if the firmware hangs or the ADC fails? If the protection is entirely in firmware, a firmware crash could leave the motor running at an unsafe temperature. This is a single-point failure that violates the principle of independent protection.

I'd propose a middle-ground solution: keep a hardware-based protection circuit as the primary safety mechanism, but allow firmware to adjust the threshold within a safe range using a DAC or a digitally-controlled potentiometer. This gives the flexibility the firmware lead wants while maintaining the independence and reliability of a hardware failsafe. Alternatively, I'd suggest a hardware comparator with a fixed, conservative threshold as a backstop, with firmware able to implement a more precise threshold as an additional layer — but not as the only protection.

I'd also reference the regulatory context. IEC 60601 and ISO 14971 require that safety mechanisms be reliable and that single-point failures be analyzed. A firmware-only protection would require a very thorough analysis showing that the firmware cannot fail in a way that disables the protection — and even then, the risk assessment might not support it.

Throughout the discussion, I'd keep the focus on patient safety and regulatory compliance rather than personal preference. I'd invite the firmware lead to help me understand their constraints and work together to find a solution that meets both safety and cost/size goals. If we couldn't reach agreement, I'd escalate to the project manager or a safety review board with a clear analysis of the risks and trade-offs.

**Possible follow-ups:**
- How would you document this decision for the design history file (DHF) and regulatory submission?
- What if the firmware lead insists that the hardware circuit is over-engineering and the firmware approach is "good enough" — how would you respond?