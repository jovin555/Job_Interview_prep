# hardware-design — Day 42

## Q1: How would you approach designing a low-battery detection circuit for a single-cell Li-ion powered medical device, where the threshold must be accurate to within ±2% over 0–50°C and the circuit must consume less than 1 µA in standby?

**Answer:** I'd start by recognizing that the accuracy requirement drives the architecture. A simple resistor divider feeding a comparator GPIO pin won't achieve ±2% over temperature because the microcontroller's internal reference and the divider's temperature coefficient both contribute error. 

My approach would be to use a dedicated voltage supervisor or comparator IC with an integrated precision reference, rather than relying on the MCU's internal reference. Key parameters I'd evaluate: the comparator's input offset voltage, the reference's initial tolerance and temperature drift, and the hysteresis characteristics. For a 3.0V threshold, ±2% means ±60mV budget. If the reference has ±1% initial tolerance and ±50ppm/°C drift, that's roughly ±30mV over 0–50°C, leaving ±30mV for comparator offset, resistor tolerance, and hysteresis — which is tight but achievable with a good precision comparator.

For the standby current, I'd look for a comparator with a shutdown pin or one that's inherently micropower. The resistor divider itself is a continuous drain — if I use a 1MΩ/1MΩ divider from a 3.7V battery, that's about 1.85µA, which already exceeds the budget. So I'd either use much higher value resistors (10MΩ range, being careful about PCB leakage and input bias current) or gate the divider with a MOSFET that only enables it periodically for a measurement.

I'd also consider where the threshold needs to be — is this a "battery empty, shut down now" signal or a "battery low, warn the user" signal? The shutdown threshold needs to account for the battery's minimum safe voltage under load, so I'd factor in the voltage drop across the battery's internal resistance at the device's maximum current draw. The warning threshold needs margin above that so the user gets meaningful advance notice.

Finally, I'd add hysteresis — typically 1–2% of the threshold — to prevent chatter when the battery voltage hovers near the threshold during load transients. The hysteresis should be verified across temperature since it's often implemented with an internal feedback resistor network.

**Possible follow-ups:**
- How would you verify the ±2% accuracy across temperature in production test, given that testing at multiple temperatures is expensive?
- What failure modes would you consider for this circuit in a medical device context, and how would you make it fail-safe?

---

## Q2: How would you approach debugging a circuit where a low-dropout regulator (LDO) output is stable at light load but oscillates when the load current increases beyond a certain threshold?

**Answer:** This is a classic LDO stability problem. The first thing I'd do is confirm the oscillation frequency and waveform shape with an oscilloscope — is it a clean sine wave, or is it more of a relaxation oscillation? The frequency and waveshape give clues about the mechanism.

The most common cause is the interaction between the LDO's output impedance and the equivalent series resistance (ESR) of the output capacitor. Many LDOs are designed to work with a specific ESR range — too low and the phase margin degrades, too high and you get a pole-zero pair that causes instability. If the design uses a ceramic capacitor with very low ESR, and the LDO wasn't designed for that, you'll often see instability that appears only at higher currents because the output transistor's transconductance changes with load.

I'd check the output capacitor's effective capacitance at the actual DC bias voltage — ceramic capacitors can lose 50–80% of their rated capacitance at higher DC voltages, which shifts the pole frequency. I'd also check if there's an ESR stabilization requirement in the datasheet that the current capacitor doesn't meet.

Another angle: the load itself. If the load is a microcontroller or other digital IC with fast current transients, the LDO's bandwidth might not be sufficient, and the output can ring. But the question says "oscillates," which suggests a sustained oscillation rather than a transient response issue.

My debugging sequence would be: (1) scope the output at the LDO pin and at the load to see if there's a difference, (2) check the input voltage — is it stable or is there interaction with the upstream supply? (3) try adding a small resistor in series with the output capacitor to increase ESR, or add a larger bulk capacitor in parallel, (4) review the datasheet's stability curves for the operating point, and (5) check the LDO's ground pin current — sometimes the ground pin current spikes during oscillation, which is a diagnostic signature.

If the LDO has an enable pin, I'd also check that the enable circuitry isn't interacting with the output. And I'd verify the PCB layout — long traces between the LDO output and the capacitor, or excessive parasitic inductance, can also cause instability.

**Possible follow-ups:**
- What if the LDO is stable with a 10µF ceramic but unstable with a 22µF ceramic — what would that tell you?
- How would you determine whether the issue is the LDO itself or the load's dynamic behavior?

---

## Q3: How would you approach designing a gate drive circuit for a high-side N-channel MOSFET used in a battery-powered load switch, where the battery voltage ranges from 3.0V to 4.2V and the load can draw up to 3A?

**Answer:** The core challenge here is that an N-channel MOSFET requires a gate voltage above the source voltage to turn on, and with a high-side configuration, the source sits at the battery voltage. At 3.0V battery, I need the gate to be at least 3V above that — so 6V or more — which exceeds the battery voltage. This means I need a charge pump or bootstrap circuit to generate the gate drive voltage.

First, I'd select the MOSFET based on the worst-case conditions: at 3.0V battery, the gate drive might only be 5–6V (after the charge pump), so I need a logic-level MOSFET with a low threshold voltage (Vgs(th) around 1–2V) and a fully specified Rds(on) at Vgs = 4.5V or even 2.5V. I'd check the Rds(on) at the lowest gate drive voltage, not just at 10V. At 3A, even 50mΩ means 0.45W of dissipation — significant in a small package, so I'd look for Rds(on) in the 10–30mΩ range at the actual drive voltage.

For the gate drive itself, I'd consider a charge pump IC designed for this purpose — there are dedicated high-side switch controllers that integrate the charge pump and gate driver. Alternatively, a bootstrap approach with a capacitor and diode can work if the load is switching periodically, but for a static load switch, a charge pump is more appropriate since there's no switching action to refresh the bootstrap capacitor.

I'd also think about the gate drive current and switching speed. For a load switch, I don't need fast switching — in fact, slower switching reduces EMI and inrush current. But I do need to ensure the gate is fully charged to keep the MOSFET in the linear region with minimum Rds(on). I'd add a gate resistor to control slew rate, sized to limit inrush current into any downstream capacitance.

Protection considerations: I'd add a gate-source zener or TVS to protect against overvoltage, and I'd ensure the gate drive circuit can't leave the MOSFET partially on if the charge pump fails — a pull-down resistor on the gate ensures the MOSFET defaults to off. I'd also consider the reverse body diode — if the load can source current back into the battery, I might need a second MOSFET in series or a different topology.

Finally, I'd verify the thermal performance: at 3A with 20mΩ Rds(on), that's 0.18W, which is manageable, but I'd check the thermal resistance of the package and the ambient temperature range to ensure the junction temperature stays within limits.

**Possible follow-ups:**
- How would you handle the inrush current when the load has significant bulk capacitance?
- What happens if the battery voltage drops below the charge pump's minimum operating voltage — how would you ensure the load switch behaves safely?

---

## Q4: How would you approach selecting between a SAR ADC and a sigma-delta ADC for a medical device that measures a slowly varying physiological signal (e.g., temperature or pressure) with high resolution, and what are the key trade-offs you'd consider?

**Answer:** For a slowly varying physiological signal, both architectures can work, but the decision hinges on the specific requirements: resolution, accuracy, power consumption, latency, and the nature of the signal and noise.

Sigma-delta ADCs excel at high resolution (16–24 bits) for low-bandwidth signals. They use oversampling and noise shaping to push quantization noise out of the band of interest, then a digital decimation filter removes it. This gives excellent resolution and inherent anti-aliasing — the digital filter provides most of the filtering, so the analog anti-aliasing filter can be simple or even omitted. The trade-offs are: higher latency (the decimation filter introduces group delay), higher power consumption (the modulator runs at a high oversampling ratio), and potential issues with multiplexing — sigma-delta ADCs are typically single-channel or have limited multiplexing capability because the digital filter needs to settle after switching channels.

SAR ADCs are simpler, lower power, and offer true sample-and-hold operation with no latency. They're easier to multiplex across multiple channels. However, achieving 16+ bits of effective resolution requires a very clean analog front-end — the SAR ADC itself doesn't provide filtering, so I need a proper anti-aliasing filter, and the reference and power supply noise directly affect the result. SAR ADCs also have a fundamental trade-off between resolution and speed — at 16 bits, the conversion time is typically microseconds, which is fine for this application.

For a medical device measuring temperature or pressure, I'd lean toward a sigma-delta ADC if I need very high resolution (18+ bits) and the signal is truly slow (a few Hz of bandwidth). The built-in filtering is a significant advantage in a noisy medical environment. But if I need to sample multiple sensors, or if power consumption is critical (battery-powered device), a SAR ADC with careful analog design might be the better choice.

I'd also consider the reference: both architectures need a stable, low-noise reference, but sigma-delta ADCs are often more sensitive to reference noise because of the high oversampling ratio. And I'd think about the system-level calibration — sigma-delta ADCs often have programmable gain and offset registers that simplify calibration, while SAR ADCs might need external calibration circuitry.

One more consideration: the input drive requirements. Sigma-delta ADCs typically have a switched-capacitor input that draws current in bursts, which can be challenging to drive with high-impedance sensors. SAR ADCs also have switched-capacitor inputs but the sampling capacitor is usually smaller. I'd need a buffer amplifier in either case, and the buffer's noise and offset become part of the system error budget.

**Possible follow-ups:**
- How would the choice change if the device needed to measure multiple channels with a single ADC?
- What impact does the ADC choice have on the overall power budget for a battery-powered device?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes using the microcontroller's internal ADC instead of the external dedicated ADC you've specified, arguing that the internal ADC is "good enough" and will save cost and board space. You believe the internal ADC's noise performance and accuracy are insufficient for the measurement requirements, and the datasheet specifications are marginal at best. How would you handle this disagreement?

**Answer:** I'd approach this as a data-driven engineering discussion rather than a matter of opinion or authority. The first step is to acknowledge the firmware lead's valid points — cost and board space are legitimate concerns, and if the internal ADC truly meets the requirements, it would be the better choice. The goal is to determine whether it does.

I'd propose we define the measurement requirements quantitatively: what's the required accuracy, resolution, noise floor, and drift over temperature? Then I'd suggest we do a side-by-side comparison of the datasheet specifications — not just the headline numbers, but the conditions under which they're guaranteed. Internal ADCs often have specifications that are "typical" rather than "guaranteed," or that apply only under specific conditions (e.g., with a specific reference voltage, at a specific temperature, or with the CPU in a specific power mode). I'd want to understand: what's the ENOB under the actual operating conditions? What's the reference voltage accuracy and drift? What's the input leakage current? How does the ADC performance change when the CPU is active and drawing current?

I'd also raise the system-level considerations: the internal ADC shares the power supply with the digital logic, so digital switching noise can couple into the conversion. The external ADC can have a cleaner, isolated supply and a dedicated reference. And in a medical device, we need to document the design decisions and demonstrate that the chosen components meet the requirements — if the internal ADC is marginal, that documentation becomes harder to defend during regulatory review.

If the datasheet comparison is inconclusive, I'd propose a practical test: build a prototype or evaluation board with the internal ADC and run it through the actual measurement scenario — with the sensor connected, under the expected noise conditions, across the temperature range. Measure the actual performance and compare it against the requirements. This gives us real data to make the decision, rather than arguing about datasheet interpretations.

If the testing shows the internal ADC is insufficient, I'd present that data clearly and explain why the external ADC is necessary. If the testing shows it's adequate, I'd accept the change and update the design accordingly. Either way, the decision is based on evidence, not position.

I'd also consider a middle ground: perhaps the internal ADC is adequate for some measurements but not others, or perhaps we can use the internal ADC for non-critical monitoring and keep the external ADC for the critical measurements. This might capture some of the cost savings while maintaining the required performance.

**Possible follow-ups:**
- What if the firmware lead pushes back and says the testing methodology is unfair or unrealistic — how would you respond?
- How would you document this decision for the regulatory file, regardless of the outcome?