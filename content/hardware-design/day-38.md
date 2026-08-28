# hardware-design — Day 38

## Q1: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** I'd start by defining the fault condition clearly — what threshold triggers it, what hysteresis is needed, and what the reset criteria should be. For the latch itself, I'd use a comparator with positive feedback (or a dedicated latch IC) that captures the fault event and holds the output state regardless of whether the input condition returns to normal. The key design decisions are around the reset mechanism and fail-safe behavior.

For reset, I'd require a deliberate action that can't happen accidentally — typically a manual reset button, a power-cycle with a minimum off-time, or a command from a supervisory processor that's itself monitored. The reset path should be independent of the fault-detection path so that a fault in the sensing circuitry doesn't prevent reset, and vice versa.

I'd also think carefully about power-up behavior. The latch must initialize to a known safe state — either "no fault" if the system is safe to start, or "fault" if the system requires explicit clearing before operation. This often means using a pull-up or pull-down on the latch's reset input that's only overridden by the deliberate reset action.

For medical devices, I'd add a test point or self-test capability to verify the latch circuit works — you need to be able to prove the protection is functional, not just assume it. This might mean injecting a test signal that simulates the fault condition and confirming the latch trips and holds.

**Possible follow-ups:**
- How would you handle the case where the fault condition is still present when the user attempts to reset the latch?
- What considerations would you apply to the latch's power supply to ensure it remains powered during a fault event?

---

## Q2: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** This symptom pattern — low-frequency periodic disturbance, present with input shorted, amplitude tracking the supply — points me toward a few specific categories. I'd start by ruling out the most likely culprits systematically.

First, I'd check the power supply itself. A 1–10 Hz disturbance on the output that scales with supply voltage suggests the supply has low-frequency ripple or oscillation that's coupling into the signal path. I'd put a scope on the supply rail with AC coupling and a long timebase to look for low-frequency content. This could be a control loop instability in a regulator, a thermal cycling effect in a reference, or even a load that's modulating at that rate.

Second, I'd look at the reference voltage. If the ADC or amplifier uses a reference that's drifting or oscillating at low frequency, the output would track it. I'd measure the reference with a high-resolution DMM or scope and look for the same periodicity.

Third, I'd consider thermal effects. A 1–10 Hz disturbance is in the range where self-heating in a component could cause periodic drift — for example, a resistor or transistor that heats up, changes value, then cools. This is more likely if the disturbance amplitude is small and the circuit has high gain.

Fourth, I'd check for ground loops or common-mode pickup. Even with the input shorted, a ground potential difference at low frequency (e.g., from a nearby transformer or motor) can inject current into the signal path. I'd try powering the circuit from a battery to see if the disturbance disappears.

Finally, I'd look at the input protection and filtering. A shorted input should be a clean reference, but if there's a capacitor in the input path that's leaky or has dielectric absorption, it could create a slow settling artifact that looks periodic.

The systematic approach is: isolate the signal chain stage by stage, measure at each node, and correlate the disturbance with supply, reference, temperature, and grounding changes.

**Possible follow-ups:**
- How would you distinguish between a power supply issue and a reference issue if both show the same periodicity?
- What test equipment would you want to have available for this kind of debug?

---

## Q3: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The first decision is the sensor type and excitation method. For an RTD, a constant current source is standard; for a thermistor, you might use a voltage divider or a constant current source depending on the linearization approach. I'll focus on the current source design since that's the core of the question.

For a precision current source, I'd consider two main topologies: a dedicated precision current source IC, or a discrete design using an op-amp, reference, and sense resistor. For medical-grade accuracy, I'd lean toward a discrete design because it gives me control over each error source.

The key error sources are: the voltage reference accuracy and drift, the sense resistor tolerance and temperature coefficient, the op-amp's offset voltage and drift, and the op-amp's bias current. For ±0.1°C with a PT100 RTD (approximately 0.385 Ω/°C), I need the current to be accurate to roughly ±0.05% or better, which means each error source needs to be budgeted carefully.

I'd use a precision reference (e.g., a bandgap or buried zener with low drift), a low-TCR sense resistor (e.g., 0.1% tolerance, ±5 ppm/°C or better), and a precision op-amp with low offset voltage and low drift. I'd also consider a Kelvin (4-wire) connection to the sense resistor to eliminate trace resistance errors.

For the RTD itself, I'd use a 4-wire connection to eliminate lead resistance errors. The current source drives the RTD, and a separate pair of wires senses the voltage across it. This is critical for medical accuracy over any cable length.

I'd also think about self-heating. The excitation current heats the RTD, which introduces an error. For a PT100, a common choice is 1 mA excitation, which keeps self-heating low while providing a usable signal (about 0.385 mV/°C). I'd verify the RTD's self-heating coefficient and ensure the error budget accounts for it.

Finally, I'd add calibration. Even with precision components, a one-point or two-point calibration at manufacturing time can correct residual offset and gain errors. This is especially important for medical devices where accuracy is verified and documented.

**Possible follow-ups:**
- How would you handle the trade-off between excitation current (signal level) and self-heating error?
- What would you do if the sensor cable is long and adds significant resistance?

---

## Q4: How would you approach selecting between a SAR ADC and a sigma-delta ADC for a medical device that measures a slowly varying physiological signal (e.g., temperature or pressure) with high resolution, and what are the key trade-offs you'd consider?

**Answer:** For a slowly varying physiological signal with high resolution requirements, I'd start by defining the actual specifications: signal bandwidth, required resolution (in bits or in absolute units), noise floor, sampling rate, power budget, and latency requirements.

For a signal like temperature or pressure, the bandwidth is typically very low — a few Hz at most. This is where sigma-delta ADCs shine. They use oversampling and noise shaping to achieve very high resolution (16–24 bits) with relatively simple anti-aliasing requirements. The digital filter in a sigma-delta ADC can be configured to reject mains frequency and its harmonics, which is valuable in medical environments.

SAR ADCs, on the other hand, sample at the Nyquist rate and require a proper anti-aliasing filter before the converter. They offer lower latency (important for control loops), no group delay from digital filtering, and they're less sensitive to the input signal's frequency content. However, achieving 16+ effective bits with a SAR ADC requires a very clean analog front-end and careful layout.

For a temperature or pressure sensor, I'd typically choose sigma-delta because:
- The signal is slow, so the digital filter's latency is acceptable
- The high resolution (often 20+ bits) reduces the need for external gain stages
- The built-in filtering simplifies the analog chain
- Power consumption can be very low with duty-cycled operation

I'd choose SAR if:
- The signal needs to be sampled synchronously with other events
- Low latency is critical (e.g., for a real-time control loop)
- The input is already well-conditioned and the bandwidth is higher
- I need to multiplex multiple channels with fast channel-to-channel settling

I'd also consider the ADC's input drive requirements. Sigma-delta ADCs often have a switched-capacitor input that requires a low-impedance driver (e.g., an op-amp buffer). SAR ADCs also need a driver that can settle within the acquisition time. For a medical device, I'd also look at the ADC's specified performance over the full temperature range, not just at 25°C.

**Possible follow-ups:**
- How would you handle the anti-aliasing requirement differently for each architecture?
- What power consumption trade-offs would you consider for a battery-powered device?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing your hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the hardware approach is necessary because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** I'd approach this as a safety engineering discussion, not a personal disagreement. The core question is: what level of independence and reliability does the protection require?

First, I'd acknowledge the firmware lead's valid points — firmware-based protection does save cost and board space, and it does allow more flexible threshold adjustment. Those are real benefits. But I'd frame the discussion around the safety requirements and the failure modes we need to protect against.

I'd ask the firmware lead to walk through the failure scenarios: What happens if the firmware hangs? What happens if the ADC returns a stuck value? What happens if the firmware is in the middle of a flash update? In each case, does the protection still work? If the answer is no, then the firmware approach doesn't meet the safety requirement.

I'd also reference the relevant standard — for medical devices, IEC 60601 requires that protection against a hazardous condition be provided even in the presence of a single fault condition. A firmware hang is a plausible single fault. The hardware comparator and latch are independent of the firmware and ADC, so they provide protection even if both fail.

Rather than insisting on my approach, I'd propose a path forward: let's document the safety requirements, do a formal risk analysis (e.g., FMEA) on both approaches, and let the analysis drive the decision. If the firmware approach can meet the safety requirements with additional measures (e.g., a separate watchdog, redundant ADC channels, a hardware interlock on the motor driver), I'd be open to considering it. But the burden of proof is on demonstrating that the firmware approach is safe, not on defending the hardware approach by default.

I'd also suggest a middle ground: keep the hardware comparator as a last-resort protection, but allow the firmware to adjust the threshold within a safe range by using a DAC or digital potentiometer. This gives flexibility while maintaining independence.

The key is to keep the discussion focused on patient safety and regulatory requirements, not on whose design wins. I'd offer to work together on the risk analysis and to document the decision rationale for the design history file.

**Possible follow-ups:**
- How would you handle the situation if the firmware lead continues to push back after the risk analysis?
- What specific failure modes would you want to see addressed in the firmware lead's proposal before you'd consider it acceptable?