# hardware-design — Day 18

## Q1: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** A fault latch needs to be unambiguous about its two states and its reset path. I'd start with a comparator or dedicated fault-detection IC that trips when the monitored parameter crosses the threshold, then feed that into a latch — either a discrete SR latch built from NAND gates or a small logic IC like a D-type flip-flop. The key design decisions are the reset mechanism and the power-on behavior.

For the reset path, I would require both a physical user action (like pressing a reset button) and the fault condition being cleared before the latch can release. This prevents the system from automatically re-enabling into a still-faulty state. A common approach is to gate the reset signal with the fault signal itself — the latch only clears when reset is asserted *and* the fault is no longer present. This can be done with a simple AND gate or by using the fault signal to enable the reset input.

Power-on behavior is critical. The latch must default to a safe state when power is first applied. I'd use a pull-up or pull-down resistor on the latch's set input to ensure it powers up in the fault state, or use a reset IC that holds the latch in a known state until the supply is stable. This way, if the device powers up with a fault present, it stays locked out rather than attempting to operate.

I'd also add a visible indicator — an LED or a signal to the main processor — so the user and the system know the latch is engaged. The processor should not be able to clear the latch directly; it should only be able to *request* a reset, which the hardware then validates. This keeps the safety function independent of firmware behavior.

**Possible follow-ups:** How would you test the latch to verify it fails safe? What happens if the reset button itself fails shorted?

---

## Q2: How would you approach characterizing the settling time of a multi-channel ADC's input multiplexer when switching between two sensor channels with very different source impedances?

**Answer:** The settling time of an ADC input mux is dominated by the RC time constant formed by the source impedance and the ADC's input capacitance, plus the mux's own on-resistance. When the source impedances differ significantly, the settling time will be different for each channel, and the worst case determines the minimum sampling delay.

My approach would be to first calculate the theoretical settling time using the datasheet values: the mux on-resistance, the ADC's sampling capacitance, and the source impedance. The time constant is roughly (R_source + R_mux) × C_sample, and I'd want at least 8–10 time constants for 16-bit accuracy. But datasheet values are typical, not worst-case, so I'd verify empirically.

For characterization, I'd set up a test where I switch between a low-impedance source (near 0 Ω) and a high-impedance source (e.g., 100 kΩ), with the ADC configured to sample immediately after switching. I'd sweep the sampling delay and record the ADC output for a known input voltage on each channel. The settling time is the delay at which the reading stops changing by more than 1 LSB. I'd repeat this across temperature and with multiple units to capture unit-to-unit variation.

One practical issue is that the mux's on-resistance can vary with input voltage and temperature, so the settling time isn't constant. I'd also check whether the ADC has a dedicated input buffer or sample-and-hold amplifier — if it does, the source impedance matters less, but the buffer's own settling characteristics become the limiting factor.

**Possible follow-ups:** How would you handle a case where the calculated settling time is too long for your sampling rate? Would you consider adding an external buffer amplifier to one channel?

---

## Q3: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** For a resistive temperature sensor, the current source's stability directly translates to measurement error. A ±0.1°C error for a PT100 RTD corresponds to roughly ±0.385 Ω, and at a typical excitation current of 1 mA, that's ±385 µV of voltage error. The current source must therefore be stable to better than ±0.04% over temperature — that's the driving constraint.

I'd use a dedicated precision current source IC or a discrete design based on a precision voltage reference, an op-amp, and a precision resistor. The discrete approach gives more control: a voltage reference drives the non-inverting input of an op-amp, and a precision sense resistor in the feedback loop sets the current. The accuracy is determined by the reference's initial tolerance and temperature drift, the resistor's tolerance and TCR, and the op-amp's offset voltage and drift.

For the resistor, I'd select a low-TCR (±5 ppm/°C or better) precision resistor. For the reference, a ±0.05% initial accuracy with 5 ppm/°C drift would be adequate. The op-amp should have low offset voltage (under 50 µV) and low offset drift. I'd also consider using a Kelvin (4-wire) connection to the sense resistor to eliminate trace resistance errors.

A subtle point is self-heating of the sensor. The excitation current heats the RTD, causing a measurement error. I'd keep the current low enough that self-heating is negligible — typically 1 mA or less for a PT100. I'd also consider using a pulsed excitation where the current is only on during the measurement, reducing average power dissipation.

For calibration, I'd include a precision reference resistor in the circuit that can be switched in during manufacturing test to calibrate out the initial tolerance of the current source. This shifts the burden from absolute accuracy to stability, which is easier to achieve.

**Possible follow-ups:** How would you handle the trade-off between excitation current (for signal-to-noise ratio) and self-heating? What if the sensor is a thermistor with a highly nonlinear response?

---

## Q4: How would you approach debugging a circuit where a crystal oscillator (8 MHz, 20 pF load capacitance) fails to start reliably when the ambient temperature drops below 0°C, but works fine at room temperature?

**Answer:** This is a classic startup margin problem. The oscillator's gain must exceed the losses in the feedback network for oscillation to build up, and this margin shrinks as temperature drops because the crystal's equivalent series resistance (ESR) increases and the transistor's gain decreases. The fact that it works at room temperature but fails cold suggests the design is marginal.

My first step would be to measure the oscillator's negative resistance — the amount of energy the active circuit injects into the crystal. I'd do this by inserting a variable resistor in series with the crystal and increasing it until oscillation stops. The negative resistance should be at least 5–10 times the crystal's maximum ESR. If the margin is thin at room temperature, it will likely fail cold.

Next, I'd check the load capacitance. The crystal is specified for 20 pF, but the actual load capacitance is the series combination of the two external capacitors plus stray capacitance. If the external caps are too large, the crystal is pulled off its specified frequency and the oscillator's gain is reduced. I'd verify the actual load capacitance matches the crystal's specification.

I'd also examine the drive level. If the oscillator is overdriven, the crystal can be damaged or the oscillation amplitude can be unstable. If underdriven, the startup time increases and the circuit is more sensitive to temperature. I'd measure the drive level with a current probe and compare it to the crystal's maximum rating.

The fix depends on what I find. If the negative resistance margin is low, I'd increase the feedback resistor value or reduce the load capacitance. If the drive level is too high, I'd add a series resistor to limit current. If the crystal itself is marginal, I'd select a crystal with lower ESR or a tighter frequency tolerance. I'd also consider using a crystal oscillator module instead of a discrete design — these are guaranteed to start over their specified temperature range.

**Possible follow-ups:** How would you measure the negative resistance without disturbing the circuit? What if the problem only appears in production units, not on your bench prototype?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing a hardware-based overcurrent protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors the current via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** I'd start by acknowledging the legitimate merits of the firmware approach — it does save board space and offers flexibility — and then frame the discussion around the safety requirements rather than a personal preference. The core question is whether the protection function can be classified as safety-critical, and if so, what the standard requires.

I'd ask the firmware lead to walk through the failure scenarios: what happens if the firmware hangs while the motor is drawing excessive current? What if the ADC's reference drifts and the threshold becomes inaccurate? What if the ADC itself fails and reports a low current when the actual current is high? The firmware approach can't protect against failures in its own components. The hardware comparator and latch are independent of the firmware, so they provide a second layer of defense.

I'd also reference the relevant standard — IEC 60601 requires that safety functions be designed so that a single fault doesn't lead to a hazardous situation. If the firmware is the only protection, then a firmware hang is a single fault that defeats the protection. The hardware circuit provides redundancy.

Rather than insisting on my approach, I'd propose a middle ground: keep the hardware comparator and latch as the primary protection, but allow the firmware to read the comparator's status and adjust the threshold via a digital potentiometer or DAC. This gives the firmware lead the flexibility they want while maintaining the independent hardware safety net. If the firmware lead still disagrees, I'd escalate to the project's risk management process and let the formal hazard analysis drive the decision.

The key is to keep the discussion focused on patient safety and regulatory requirements, not on whose design is "better." I'd also document the disagreement and the rationale for the final decision in the design history file, since that's what a regulatory auditor would look for.

**Possible follow-ups:** How would you handle the situation if the firmware lead refuses to compromise and the project manager is pressuring you to accept the firmware-only approach to meet the schedule? What if the hardware comparator adds a week to the layout schedule?