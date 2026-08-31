# hardware-design — Day 41

## Q1: How would you approach designing a power supply architecture for a medical device that contains both a high-resolution analog front-end and a motor driver, where the motor can draw 1A peaks and the analog section requires a noise floor below 50 µV RMS?

**Answer:** The fundamental principle here is separation — both electrical and physical. I would start by defining the power tree with distinct domains: a "dirty" domain for the motor driver and a "clean" domain for the analog front-end, each fed from the main battery or input supply through independent regulators.

For the motor driver, I'd use a switching regulator (buck or boost depending on the input voltage) optimized for efficiency and transient response, since the 1A peaks demand good load-step performance. For the analog section, I would not feed it directly from the switching regulator output. Instead, I'd use a two-stage approach: the switching regulator provides a pre-regulated rail, and then a low-noise LDO (or possibly two LDOs in series for very demanding applications) generates the final analog supply. The LDO's PSRR at the switching frequency and its harmonics is the key parameter — I'd check the PSRR curve across frequency, not just the DC value, because switching noise is broadband.

The layout is equally critical. I'd keep the motor driver's high-current loop physically separated from the analog section, with a star-point or split ground plane that connects at a single point (usually at the battery return or the ADC's ground reference). The motor driver's switching node should be kept short and away from the analog front-end. I'd also consider adding a ferrite bead or small series inductor between the LDO output and the analog circuitry to provide additional high-frequency isolation.

For the noise budget, I'd work backwards from the 50 µV RMS requirement. The LDO's output noise density (typically specified in nV/√Hz) integrated over the analog bandwidth, plus the noise contribution from the reference, the ADC's own noise, and any coupling from the digital section, must all sum to less than 50 µV RMS. I'd allocate the budget across these sources — for example, the LDO might get 20 µV, the reference 10 µV, the ADC 15 µV, and coupling 5 µV — and then verify each component meets its allocation.

Finally, I'd consider the motor driver's impact beyond just the power rail. The motor current returns through the ground system, and if the analog ground reference is in the path of that return current, you'll see voltage drops that appear as noise. This is why the physical layout and grounding strategy are as important as the component selection.

**Possible follow-ups:**
- How would you decide whether a single LDO is sufficient, or whether you need two stages of post-regulation?
- What specific LDO datasheet parameters would you evaluate to ensure it meets the noise requirement?

---

## Q2: Walk me through how you would debug a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage.

**Answer:** This is a classic symptom that points to something in the power or reference path rather than the signal path itself, since the input is shorted. The frequency range — 1–10 Hz — is a strong clue. It's too slow for typical switching regulator ripple (which would be in the kHz range) and too fast for thermal drift. The fact that the amplitude varies with the supply voltage tells me the disturbance is coupled through the supply or reference, not through the input.

My first step would be to confirm the disturbance is actually on the output and characterize it precisely — measure its frequency, amplitude, and whether it's sinusoidal or has a different shape. I'd use a scope with sufficient resolution and a long timebase, and I'd also check if the frequency is stable or drifting, which would help distinguish between a fixed source (like a clock or PWM) and something thermal or mechanical.

Next, I'd probe the power supply rails and the voltage reference with an AC-coupled scope, looking for the same 1–10 Hz component. If I see it on the supply, I'd trace back to what could generate a low-frequency disturbance on a power rail. Common culprits include: a control loop instability in a regulator (especially an LDO with a marginal stability margin), a thermal feedback loop where a component heats and cools cyclically, or a load that's periodically drawing current — for example, a microcontroller waking up periodically, or a sensor that's being pulsed.

If the disturbance is on the reference, I'd suspect the reference's own noise or a thermal effect. Some references have a "popcorn noise" or random telegraph noise component that appears at low frequencies. I'd also check if the reference is being loaded periodically.

Another important check is the ground system. A 1–10 Hz disturbance can come from a ground loop or from a ground connection that's picking up a low-frequency current — for example, from a heater or a thermoelectric cooler that cycles on and off. I'd measure the voltage between the analog ground and the system ground at the same frequency.

I'd also consider the test setup itself. Is the device on a bench with a lab power supply? Some lab supplies have a low-frequency ripple or a control loop that interacts with the device's load. I'd try a battery supply or a different power source to rule that out.

Once I've identified the source, the fix depends on the cause: improving the LDO's stability margin (output capacitor ESR), adding a low-frequency filter on the reference, isolating the ground, or moving the periodic load to a different supply rail.

**Possible follow-ups:**
- How would you distinguish between a power supply issue and a reference issue as the root cause?
- What test equipment would you use to capture and analyze a low-frequency disturbance that might be below the noise floor of a standard scope probe?

---

## Q3: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The core requirement is that the latch must be fail-safe and unambiguous — once a fault is detected, the system stays in a safe state until a human or a deliberate control action resets it. I'd start by defining the fault detection and the reset conditions clearly, because the latch design depends on what "deliberate, safe action" means in the product's context.

For the latch itself, the classic approach is a silicon-controlled rectifier (SCR) or a thyristor, which latches when triggered and stays latched until the current through it drops below the holding current. This is simple and inherently latching, but it has limitations: it can be sensitive to noise, and resetting it requires interrupting the current path, which may not be practical in all designs.

A more flexible approach is a comparator plus a latching element — either a discrete flip-flop or a comparator with positive feedback (a Schmitt trigger with a latching resistor network). The comparator monitors the fault condition (e.g., temperature above a threshold, or current above a limit), and when it trips, it sets the latch. The latch's output drives a shutdown signal — for example, disabling a motor driver or cutting power to a load.

The key design decisions are:

1. **Reset mechanism:** The reset must be deliberate. I'd design it so that the reset signal comes from a dedicated action — a physical reset button, a power-cycle that requires the user to release and re-apply power, or a command from a supervisory processor that has been explicitly verified. I would not allow the latch to reset automatically when the fault clears, because that could lead to rapid on-off cycling (chattering) that's dangerous in a medical device.

2. **Noise immunity:** The latch must not be set by transient noise. I'd add hysteresis to the comparator (or use a Schmitt trigger) so that the fault threshold has a defined trip point and reset point. I'd also add a small amount of filtering (an RC delay) to reject short transients, but I'd be careful that the delay doesn't prevent the latch from responding to a genuine fault within the required time.

3. **Fail-safe behavior:** The latch should default to the safe state. If power is lost, the system should fail safe — meaning the motor is disabled or the output is de-energized. This usually means the latch's output is active-low (or the load is driven through a normally-open contact that requires the latch to be un-tripped to energize).

4. **Reset verification:** After a reset, I'd want the system to verify that the fault condition has actually cleared before re-enabling the output. This might mean the reset action clears the latch, but the system waits for the fault monitor to confirm a safe condition before allowing the motor to re-energize.

5. **Testability:** For a medical device, the latch circuit should be testable — both at manufacturing and potentially in the field. I'd include a test point or a way to inject a simulated fault to verify the latch trips correctly.

For the reset action specifically, I'd consider whether the reset should be a momentary action (press a button) or a sustained action (hold for 2 seconds). A sustained action is more deliberate and reduces the chance of accidental reset. I'd also consider whether the reset should require a second independent confirmation — for example, the user must press reset and then confirm on a display.

**Possible follow-ups:**
- How would you design the reset circuit so that a single component failure cannot cause an unintended reset?
- How would you verify that the latch meets the response time requirement for the specific fault being monitored?

---

## Q4: How would you approach selecting between a SAR ADC and a sigma-delta ADC for a medical device that measures a slowly varying physiological signal (e.g., temperature or pressure) with high resolution, and what are the key trade-offs you'd consider?

**Answer:** For a slowly varying physiological signal, both architectures can work, but the decision comes down to the specific requirements: resolution, accuracy, power, latency, and the nature of the signal and noise.

**SAR ADC:** A SAR ADC gives you a sample-per-conversion result with no latency — you request a conversion and get a value. It's typically lower power for a given sample rate, has no latency or pipeline delay, and is easier to multiplex across multiple channels. The resolution is typically 12–18 bits, and the accuracy depends heavily on the reference and the front-end settling. For a slowly varying signal, the main concern is that SAR ADCs can be sensitive to noise on the input and the reference — you need good anti-aliasing filtering and careful layout. The noise performance is typically specified as ENOB, and for a 16-bit SAR, you might get 14–15 ENOB in practice.

**Sigma-delta ADC:** A sigma-delta ADC uses oversampling and noise shaping to achieve very high resolution — 20–24 bits is common. It's inherently better at rejecting broadband noise because of the digital filtering, and it provides excellent linearity and low noise for DC and slowly varying signals. The trade-offs are: it has latency (the digital filter introduces a delay, which matters if you need real-time response), it consumes more power (though modern devices are quite efficient), and it's harder to multiplex because the digital filter needs to settle after switching channels. The output is a continuous stream of samples rather than a single conversion, which can be an advantage for averaging but requires the host to handle the data rate.

For a temperature or pressure sensor in a medical device, I'd lean toward a sigma-delta ADC if the primary requirement is resolution and noise performance, and if the signal is truly slow (e.g., a few samples per second). The oversampling and digital filtering give you excellent noise rejection, and the high resolution means you don't need as much analog gain in the front-end, which reduces the noise contribution from the amplifier.

However, if the device needs to monitor multiple channels (e.g., several temperature sensors), a SAR ADC with a multiplexer might be more practical, because the sigma-delta's settling time after channel switching can be a problem. In that case, I'd use a SAR with sufficient resolution and ensure the front-end settling time is adequate.

I'd also consider the power budget. For a battery-powered device that's mostly in sleep mode, a SAR ADC that can do a single conversion and shut down might be more power-efficient than a sigma-delta that needs to run continuously to maintain its digital filter. Some sigma-delta ADCs have a one-shot mode, but the settling time still applies.

Finally, I'd consider the system-level calibration. Sigma-delta ADCs often have better inherent linearity, which simplifies calibration. SAR ADCs may require more careful offset and gain calibration, especially if the front-end has gain stages.

**Possible follow-ups:**
- How would the presence of 50/60 Hz mains interference affect your choice between SAR and sigma-delta?
- How would you handle the latency of a sigma-delta ADC if the device needs to respond quickly to a change in the measured parameter?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing the hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the hardware approach is necessary because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical disagreement, and my approach would be to focus on the engineering evidence and the regulatory requirements rather than trying to "win" the argument. I'd start by acknowledging the firmware lead's valid points — a firmware solution does offer flexibility and cost savings, and those are legitimate considerations. But I'd frame the discussion around the fundamental question: what is the required safety integrity level of this protection function, and can a firmware-based solution meet it?

I'd begin by laying out the failure modes that a firmware solution cannot address. If the firmware hangs — which is precisely the scenario the protection is meant to handle — the firmware-based protection is unavailable. Similarly, if the ADC fails (e.g., a stuck bit or a reference drift), the temperature reading could be wrong, and the protection might not trip. A hardware comparator with a dedicated temperature sensor and a latching circuit is independent of the main processor and the ADC, so it provides protection even when the rest of the system is compromised.

I'd also reference the regulatory context. For a medical device, the protection function would likely be classified according to its safety significance. If the over-temperature protection is required to prevent patient harm, it would need to meet the relevant safety standards (e.g., IEC 60601), which often require that safety functions be implemented with a level of independence and reliability that a single firmware path may not provide. I'd suggest we review the risk analysis (ISO 14971) to determine the required risk control measures and their integrity levels.

Rather than simply rejecting the firmware proposal, I'd propose a structured evaluation. I'd suggest we do a failure mode and effects analysis (FMEA) on both approaches, considering: the probability of firmware hang, the probability of ADC failure, the response time of each approach, and the consequences of a missed trip. I'd also consider a hybrid approach: keep the hardware comparator as the primary protection (for fail-safe independence), but allow the firmware to adjust the threshold within a safe range, or use the firmware to provide a secondary, more nuanced response (e.g., gradual power reduction before the hard shutdown). This way, we get the flexibility the firmware lead wants without compromising the safety function.

I'd also propose a practical test: we could prototype both approaches and run fault injection tests — deliberately hang the firmware, inject ADC errors, and see which approach reliably shuts down the motor. The data would help the team make an evidence-based decision.

Finally, I'd escalate if necessary. If we can't reach agreement and I believe the safety risk is significant, I'd involve the project's safety officer or the regulatory affairs team to get an authoritative interpretation of the requirements. In a medical device, safety decisions shouldn't be made by consensus alone — they should be driven by the risk analysis and the applicable standards.

**Possible follow-ups:**
- How would you determine whether the over-temperature protection is safety-critical enough to require hardware independence?
- If the team decides to go with the firmware approach despite your concerns, what would you do?