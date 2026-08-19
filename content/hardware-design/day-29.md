# hardware-design — Day 29

## Q1: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The core requirement here is that the latch must be fail-safe and deterministic — once a fault is detected, the system stays in a safe state regardless of whether the fault condition persists. I'd start by defining the fault detection mechanism: typically a comparator with a reference threshold, or a dedicated protection IC with built-in hysteresis. The latch itself can be implemented with a simple SCR-like structure using a transistor pair, or more commonly with a discrete latch built from a comparator with positive feedback (a Schmitt trigger configuration) driving a MOSFET that holds the fault state.

The key design decisions are: (1) how the latch is reset, and (2) how the reset action is made deliberately safe. For a medical device, the reset should require an explicit operator action — not an automatic recovery that could cycle the device into an unsafe state. I'd implement reset through a momentary push-button or a system-level command that requires a specific sequence, and the reset path should be independent of the fault detection path so a stuck fault sensor can't be cleared accidentally.

I'd also consider the power domain for the latch. If the latch is powered from the same rail it's protecting, a fault that collapses that rail could clear the latch unintentionally. In that case, I'd power the latch from a separate always-on rail or use a latching mechanism that doesn't depend on the protected supply. Finally, I'd add a test point or a way to verify the latch functionality during manufacturing test — you want to be able to inject a simulated fault and confirm the latch trips and holds.

**Possible follow-ups:**
- How would you handle the case where the reset button itself could be pressed accidentally during normal operation?
- What happens if the fault condition is still present when the operator attempts to reset the latch?

---

## Q2: Walk me through how you would debug a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage.

**Answer:** This is a classic symptom pattern that points to a few specific root causes. The 1–10 Hz frequency range is too slow for typical switching regulator noise (which would be in the kHz range) and too fast for thermal drift. The fact that the amplitude varies with supply voltage is a strong clue — it suggests the disturbance is coupled through the power supply path rather than being generated internally in the signal chain.

My first step would be to characterize the disturbance precisely: measure its exact frequency, amplitude, and waveform shape, and check whether it's synchronized to anything else on the board (e.g., a display refresh, a wireless beacon, or a motor PWM cycle). I'd use a spectrum analyzer on the output and also probe the supply rails with a differential probe to see if the same frequency component appears there.

A common cause in this frequency range is a control loop oscillation — for example, an LDO or switching regulator that's marginally stable and oscillating at a low frequency, or a reference buffer that's oscillating due to capacitive loading. The disturbance could be coupling into the analog front-end through the reference pin, the supply pin, or the ground path. I'd check the regulator's phase margin by looking at its transient response, and I'd verify that the reference decoupling is adequate.

Another possibility is a thermal oscillation — a component that's self-heating and causing a slow feedback loop through temperature-dependent parameters. This is more common with high-power components near the analog section. I'd check for hot spots with a thermal camera and see if the disturbance frequency changes with ambient temperature.

I'd also look at the ground path. If the analog ground and digital ground are connected at a single point but the return current path for some other circuit flows through that connection, you can get a low-frequency voltage gradient that modulates the "ground" reference of the analog front-end. A careful ground layout review, or temporarily isolating sections of the board, can help isolate this.

**Possible follow-ups:**
- How would you distinguish between a power supply oscillation and a ground loop as the root cause?
- What test equipment would you use to capture a low-frequency disturbance that's intermittent?

---

## Q3: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The first step is to work backward from the accuracy requirement to the current source specification. For a Pt100 RTD, ±0.1°C corresponds to roughly ±0.385 Ω, which at a typical excitation current of 1 mA means the voltage measurement needs to be accurate to about ±0.385 mV. The current source's stability directly contributes to this error budget — if the current drifts by even 0.1%, that's a significant fraction of the allowable error.

I'd start with a topology choice. A simple approach is a voltage reference driving a precision op-amp with a sense resistor in the feedback loop — the classic Howland current source or a simpler two-op-amp configuration. The key parameters are: the voltage reference's initial accuracy and temperature drift, the sense resistor's tolerance and TCR, and the op-amp's offset voltage and drift.

For a ±0.1°C budget, I'd typically allocate: sense resistor tolerance and drift (the dominant error source), voltage reference drift, and op-amp offset drift. A precision sense resistor with 0.1% tolerance and ±10 ppm/°C TCR would contribute roughly ±0.05% error over a 50°C range — that alone is borderline, so I'd likely need a better resistor (0.05% or 0.02%, with ±5 ppm/°C) or a ratiometric measurement approach.

The ratiometric approach is worth considering: instead of generating an absolute current, use the same reference voltage to drive both the current source and the ADC's reference. This cancels first-order reference drift because the measurement becomes a ratio rather than an absolute voltage. This is a common technique in precision temperature measurement.

I'd also consider the self-heating effect of the sensor. At 1 mA, a Pt100 dissipates about 0.1 mW, which in still air could cause a small temperature rise in the sensor itself. For high accuracy, I might reduce the excitation current to 500 µA or use pulsed excitation to minimize self-heating, trading off against increased noise sensitivity.

Finally, I'd think about the PCB layout: the sense resistor should be a Kelvin-connected four-terminal device to avoid trace resistance errors, and the current source should be physically separated from heat sources. I'd also add a calibration step at manufacturing — a single-point trim using a precision resistor in place of the sensor can correct for initial tolerance errors.

**Possible follow-ups:**
- How would you decide between a ratiometric and an absolute measurement approach?
- What error sources would you include in your noise budget, and how would you allocate the ±0.1°C budget across them?

---

## Q4: How would you approach designing a hardware-based overcurrent protection circuit for a motor driver in a medical device, where the protection must be independent of the main microcontroller and must respond within microseconds?

**Answer:** The key constraints here are speed and independence. A microcontroller-based solution typically can't respond in microseconds — by the time the ADC samples, the firmware processes, and the GPIO toggles, you've already allowed potentially damaging current to flow. So the protection needs to be a dedicated analog circuit.

The classic approach is a low-side sense resistor in series with the motor, a comparator that compares the voltage across the sense resistor to a reference threshold, and a latch or direct shutdown path that disables the motor driver. The comparator should have a fast propagation delay (tens of nanoseconds) and the shutdown path should be direct — either through the driver's enable pin or by pulling the gate of the high-side MOSFET low.

The critical design details are: (1) the sense resistor's value and power rating — it must be large enough to generate a usable voltage at the trip current but small enough to minimize power loss; (2) the comparator's input offset and hysteresis — you need enough hysteresis to avoid chatter at the threshold, but not so much that the trip point becomes inaccurate; (3) the reference voltage's accuracy and temperature stability — a simple resistor divider from a regulated rail may be adequate, but a precision reference is better if the threshold must be tight.

I'd also consider the response time budget. The comparator itself might respond in 50–100 ns, but the motor driver's shutdown path adds delay — some drivers have a propagation delay from the enable pin to the output of several hundred nanoseconds. The total response time must be fast enough that the current doesn't exceed the MOSFET's or motor's safe operating area during the fault. This means I need to know the fault current's rise time (which depends on the motor's inductance and the supply voltage) and calculate the energy delivered during the response window.

For a medical device, I'd also add a latch — once the protection trips, the system should stay off until a deliberate reset, rather than automatically retrying. And I'd consider redundant protection: a second, independent comparator with a slightly higher threshold as a backup, or a fuse as a last-resort protection.

**Possible follow-ups:**
- How would you verify that the protection circuit actually responds within the required time, and how would you test it under fault conditions?
- How would you handle the trade-off between a low sense resistor value (minimizing power loss) and the comparator's input offset voltage (which becomes more significant at lower sense voltages)?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, a colleague from the software team argues that the device's fault detection can be handled entirely in firmware — monitoring sensor values through the existing ADC and shutting down the system via a GPIO — eliminating the need for a dedicated hardware comparator circuit. The colleague argues this will reduce cost, save board space, and allow more flexible threshold adjustment. You believe the hardware approach is necessary because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** I'd approach this as a risk analysis discussion rather than a design authority argument. The fundamental question isn't about cost or board space — it's about whether the firmware-based approach can meet the safety requirements, and that's a question we should answer with data and standards, not opinions.

First, I'd acknowledge the valid points: firmware-based protection does offer flexibility, and the cost savings are real. Then I'd reframe the discussion around the device's safety requirements. In a medical device, the fault detection path is typically a safety function, and the question is whether it needs to be independent of the main processor. If the device is delivering a therapeutic output (like a motor-driven actuator), the protection must work even if the firmware hangs, the ADC fails, or the processor enters an undefined state. That's not a hypothetical concern — it's a fundamental reliability requirement.

I'd propose a structured evaluation: let's look at the failure modes and their consequences. If the firmware hangs while the motor is running, what happens? If the ADC's reference drifts, could the firmware's threshold become inaccurate? If the processor is stuck in a loop, can the GPIO actually be toggled? These are concrete scenarios we can analyze together.

I'd also reference the relevant standards — for medical devices, the safety architecture typically requires that protective functions be independent of the control function, or at least that the failure of the control function doesn't compromise the protective function. This isn't just my preference; it's a regulatory expectation.

If the colleague still disagrees, I'd suggest a compromise: we could implement the firmware-based protection as a secondary layer, but keep the hardware comparator as the primary, independent safety mechanism. The firmware could provide additional diagnostic information and more flexible threshold adjustment for non-safety-critical limits, while the hardware handles the safety-critical shutdown. This gives us the flexibility they want without compromising safety.

Finally, I'd document the decision and the rationale — whether we go with hardware, firmware, or both — so that the reasoning is captured for the design history file and any future regulatory review.

**Possible follow-ups:**
- How would you determine whether a particular fault detection function is "safety-critical" and therefore requires hardware independence?
- If the project schedule is tight and adding the hardware circuit would delay the design, how would you prioritize the competing concerns?