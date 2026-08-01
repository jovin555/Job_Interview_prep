# hardware-design — Day 11

## Q1: How would you approach designing a multi-rail power supply sequencing scheme for a medical device that contains a microcontroller, an analog front-end, and a wireless radio, where the datasheets specify different power-up timing requirements for each rail?

**Answer:** Power supply sequencing is one of those areas where the consequences of getting it wrong are subtle but potentially serious — latch-up, undefined logic states, or damage to interface pins. My approach starts with a careful review of each IC's absolute maximum ratings and recommended power-up sequence, paying particular attention to any rail-to-rail pin voltage constraints. For example, if an ADC's digital interface pins connect to a microcontroller that powers up first, the ADC's ESD diodes could forward-bias and back-power the analog rail if the digital rail comes up significantly earlier.

Once I understand the constraints, I look at the simplest solution that meets them. If the rails naturally ramp within acceptable timing windows due to their respective load capacitances and regulator start-up times, no explicit sequencing is needed — I just verify this with simulation and bench measurements. If sequencing is required, I typically prefer passive approaches first: using the enable pins on downstream regulators, driven by a resistor-divider from an upstream rail, or using a simple RC delay on the enable pin. These are cheap, reliable, and easy to debug. For more complex requirements — like a specific order with minimum delays between rails — I'd consider a dedicated sequencer IC or a PMIC with integrated sequencing, which adds cost but provides deterministic behavior and often includes fault monitoring.

A critical detail is the discharge path. Sequencing isn't just about turn-on order; it's also about what happens during power-down and brown-out conditions. If the rails discharge at different rates, you can recreate the same violation conditions during shutdown. I'd include discharge resistors or active discharge circuits to ensure controlled ramp-down, and I'd verify the full power cycle — not just the initial power-up — during validation.

**Possible follow-ups:**
- How would you verify the sequencing is correct during testing, especially for fast transients that might be missed on a scope?
- What if a required rail-to-rail voltage difference is only specified as a maximum, not a timing requirement — how would you interpret that?

---

## Q2: Walk me through how you would debug a circuit where a precision voltage reference (2.5V output) reads correctly on a multimeter but the ADC's conversion results show a consistent 15 LSB offset at 16-bit resolution, and the offset scales with the reference voltage.

**Answer:** This is a classic case where the symptom points away from the reference's DC accuracy and toward something in the dynamic interaction between the reference and the ADC. A multimeter measures the average DC value, but a SAR ADC draws current from the reference in bursts during each conversion — the reference must settle back to its accurate value within the ADC's acquisition window. If the reference has high output impedance at the ADC's sampling frequency, or if the decoupling is inadequate, the reference voltage will droop during conversion and recover between conversions. The ADC will then convert against a slightly shifted reference, producing a consistent offset.

My debugging approach would start by looking at the reference output with a scope, triggered on the ADC's conversion start signal, with the input shorted to mid-scale. I'd look for droop or ringing at the reference pin during the sampling window. If I see droop, the fix is usually a larger bypass capacitor right at the reference input pin, or a low-impedance buffer between the reference and the ADC's reference input. Some SAR ADCs have a specified reference input current profile that requires a minimum capacitance value — I'd check that the bypass cap meets or exceeds it.

The fact that the offset scales with the reference voltage is a strong clue. If the offset were a fixed voltage, I'd suspect the ADC's internal offset or a ground offset. Scaling with reference suggests the reference voltage itself is being modulated — either by the ADC's sampling current or by some coupling from the conversion clock. I'd also check the reference's load regulation spec and whether the ADC's reference input draws current spikes that exceed what the reference can supply without significant voltage deviation. If the reference is a low-power, low-bandwidth part, it may simply not be able to source the ADC's dynamic current requirements, and a buffer amplifier would be the right solution.

**Possible follow-ups:**
- How would you distinguish between a reference droop issue and a ground bounce issue at the ADC's reference pin?
- What if the offset only appears at higher sampling rates — how would that change your analysis?

---

## Q3: How would you approach designing an ESD protection scheme for a medical device's external connector that carries a differential analog signal pair, where the signal bandwidth is 1 kHz and the source impedance is 10 kΩ, and the device must meet IEC 61000-4-2 immunity requirements?

**Answer:** The key tension here is protecting against ESD events while not degrading the analog signal's accuracy. With a 1 kHz bandwidth and 10 kΩ source impedance, I have significant freedom in choosing protection components because the signal is slow and high-impedance — but that high source impedance also means the circuit is vulnerable to even small leakage currents from protection devices.

My first step is to characterize the signal levels and the ADC's input range to understand how much protection-induced error I can tolerate. For a medical measurement, I'd typically budget for less than 0.1% error contribution from the protection network. I'd then select TVS diodes or steering diodes with low capacitance (in the low picofarad range, which is easy to find for this bandwidth) and, critically, low leakage current at the operating voltage. A TVS diode with 1 µA leakage at the signal's DC bias point would create a 10 mV error across a 10 kΩ source impedance — that's often unacceptable, so I'd look for parts with leakage in the nanoamp range.

The topology matters as much as the parts. I'd place the protection as close to the connector as possible, with a low-impedance path to the chassis ground or signal ground. For a differential pair, I'd use a common-mode choke or series resistors (if the error budget allows) between the connector and the protection devices to limit the current during an ESD event. Series resistors of 1–10 kΩ are often effective here since the signal bandwidth is low — they limit the ESD current without affecting the signal, and they work with the TVS diodes to clamp the voltage at the sensitive circuitry.

I'd also consider whether the connector's shield needs to be tied to chassis ground through a high-voltage capacitor or a dedicated ESD ground path, and whether a spark gap or discharge lug on the PCB is appropriate for very high-energy events. Finally, I'd validate the design with actual ESD testing at multiple voltage levels and both polarities, checking that the ADC readings remain within specification during and after the event.

**Possible follow-ups:**
- How would the protection scheme change if the signal were a 100 MHz high-speed digital pair instead of a 1 kHz analog signal?
- How would you verify that the protection devices don't introduce unacceptable leakage current over the device's operating temperature range?

---

## Q4: How would you approach designing a firmware-based calibration routine for a medical device's analog front-end that compensates for both offset and gain errors in the signal chain, given that the device has a known reference voltage available and the calibration must be performed at manufacturing time?

**Answer:** The goal of a manufacturing calibration is to characterize the signal chain's errors and store correction coefficients that the firmware applies during normal operation. My approach starts with understanding the error sources: the sensor's offset and gain error, the instrumentation amplifier's offset and gain error, the ADC's offset and gain error, and any temperature-dependent drift. For a manufacturing calibration, I'd focus on the static errors first, and design the routine so it can be extended to temperature compensation if needed.

The calibration procedure would use the known reference voltage as the stimulus. I'd design the front-end with a calibration mode that can switch the input to the reference — either through an analog multiplexer or a relay — so the firmware can measure the reference through the full signal chain. The routine would take multiple measurements at two or more known input levels: typically zero (or a known offset level) and a near-full-scale reference. From these measurements, the firmware computes the offset and gain correction factors using a linear model: corrected_value = (raw_value − offset) × gain_factor.

A critical detail is the measurement strategy. I'd take multiple samples at each calibration point and average them to reduce noise, and I'd ensure the front-end has settled before sampling — especially if the input multiplexer switches between different source impedances. I'd also sequence the calibration to measure the zero point first, then the reference point, and I'd verify the measurements are stable across a few seconds to catch any settling issues.

The correction coefficients would be stored in non-volatile memory, ideally with a checksum or CRC to detect corruption. I'd also store the calibration date, the equipment used, and the ambient temperature so the data can be traced and audited — this is important for medical device documentation. The firmware would apply the correction in real time, and I'd include a validation step in the manufacturing test that measures a known stimulus after calibration to confirm the residual error is within specification.

One consideration I'd raise early is whether the calibration should be a one-point or two-point routine. A one-point calibration (offset only) is faster but doesn't correct gain error. A two-point calibration is more thorough but requires a second reference level, which may need a precision voltage divider or a second reference source. The choice depends on the accuracy requirement and the expected magnitude of the gain error in the signal chain.

**Possible follow-ups:**
- How would you handle the case where the sensor itself has a significant offset that varies from unit to unit — would you calibrate it out or use a different approach?
- How would you design the calibration mode's input switching so it doesn't introduce parasitic paths that affect the normal measurement path?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes moving the sensor calibration from the manufacturing test to a self-calibration routine that runs at device startup, arguing that it will reduce manufacturing cost and improve long-term accuracy by compensating for drift. You believe the self-calibration approach is risky because the device's operating environment at startup may not provide a stable, known reference, and the calibration could introduce errors if the device is moved or subjected to vibration during the routine. How would you handle this disagreement?

**Answer:** I'd approach this as a technical trade-off that deserves a structured analysis rather than a debate about whose position is correct. The firmware lead raises a legitimate point — self-calibration can reduce manufacturing cost and address drift over the device's life, which is a real concern for medical devices that may be in service for years. My concern is equally valid: a calibration routine that runs in an uncontrolled environment could produce incorrect coefficients that are worse than no calibration at all.

My first step would be to schedule a focused discussion with the firmware lead, away from the full design review, to understand the specifics of their proposal. I'd want to know: what reference signal would the self-calibration use? How would the device know the reference is stable? What happens if the calibration is interrupted or the device is moved mid-routine? What's the expected drift rate of the signal chain, and does it actually justify frequent recalibration?

From there, I'd propose a middle path: implement the self-calibration as an option, but with safeguards. For example, the routine could require the device to be stationary and at a stable temperature — detected via the accelerometer and temperature sensor — before it proceeds. The routine could also validate its results by checking that the computed coefficients fall within expected ranges, and it could flag anomalies for the user or service technician. I'd also suggest running the self-calibration in parallel with the manufacturing calibration during the first production batch, comparing the results to validate the approach before committing to it.

If the firmware lead's proposal is fundamentally sound, I'd be willing to support it with the right safeguards. If my concerns remain, I'd escalate to the project manager with a clear risk assessment, including the potential impact on measurement accuracy and patient safety, and let the team make an informed decision. The key is to keep the discussion focused on data and risk, not on defending my original position.

**Possible follow-ups:**
- What specific validation criteria would you propose to determine whether the self-calibration approach is acceptable?
- How would you handle the situation if the firmware lead is unwilling to add the safeguards you're proposing?