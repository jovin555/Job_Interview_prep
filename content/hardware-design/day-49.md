# hardware-design — Day 49

## Q1: How would you approach designing a power supply architecture for a medical device that contains both a high-resolution analog front-end (requiring a noise floor below 50 µV RMS) and a motor driver that can draw 1A peaks?

**Answer:** The fundamental principle here is separation — both physical and electrical — between the noisy, high-current domain and the sensitive analog domain. I would start by defining the power tree with independent rails for the motor driver and the analog front-end, rather than trying to share a single regulated rail.

For the motor driver, I'd use a switching regulator (buck or boost depending on the input source) that can handle the 1A peaks with adequate headroom. The key concern is that switching regulators generate ripple and radiated noise at the switching frequency and its harmonics, which can couple into the analog circuitry through conducted paths (shared ground impedance, power supply coupling) or radiated paths (electromagnetic coupling to sensitive traces).

For the analog front-end, I would not power it directly from the switching regulator output. Instead, I'd use a two-stage approach: the switching regulator provides a "pre-regulated" rail, followed by a low-dropout linear regulator (LDO) with high PSRR to supply the analog circuitry. The LDO acts as a noise barrier, attenuating the switching ripple and high-frequency noise from the switcher. I'd select an LDO with good PSRR across the frequency range of interest — not just at DC, but critically at the switching frequency of the upstream regulator and its harmonics.

The ground architecture is equally important. I'd use a star ground or split ground plane approach, ensuring that the high-current motor return path doesn't share copper with the analog ground reference. The motor driver's ground return should be routed directly back to the power supply input, not through the analog ground plane. If a single ground plane is necessary, I'd carefully partition it so that the motor current path doesn't flow through the analog section's ground reference.

I'd also add a pi-filter (ferrite bead plus capacitors) on the analog rail to provide additional high-frequency isolation. The ferrite bead should be selected to be lossy at the switching frequency and its harmonics, not just at very high frequencies.

Finally, I'd verify the design through measurement: check the analog rail noise with the motor running at full load, not just in standby. This is where many designs fail — the noise spec is met in isolation but violated when the motor is actually actuating.

**Possible follow-ups:**
- How would you decide between a split ground plane and a solid ground plane with careful partitioning?
- What specific LDO parameters would you evaluate to ensure adequate noise rejection at the switching regulator's frequency?

---

## Q2: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** This is a classic symptom pattern that points toward a low-frequency periodic source that's coupling into the signal path through the power supply. The fact that the disturbance amplitude varies with the supply voltage is a strong clue — it suggests the noise is entering through a path that's modulated by the rail voltage, such as PSRR limitations or a ground bounce that scales with supply current.

My debugging approach would be systematic:

First, I'd characterize the disturbance precisely. I'd capture the waveform on an oscilloscope with sufficient resolution to see the low-frequency component, and use an FFT to identify the exact frequency. A 1–10 Hz disturbance is suspiciously close to mains frequency (50/60 Hz) divided down, or possibly a thermal cycling effect. I'd check whether the frequency is stable or drifts — a stable frequency suggests an electrical source, while a drifting frequency might suggest a thermal or mechanical effect.

Next, I'd isolate the power supply as the coupling path. I'd replace the supply with a clean bench supply (linear, low-noise) and see if the disturbance disappears. If it does, the problem is in the on-board power generation or distribution. If it persists, I'd look at other paths — ground loops, external interference, or the reference circuitry.

If the disturbance tracks the supply, I'd probe the supply rail directly at the analog front-end's power pin with an AC-coupled scope, looking for the same 1–10 Hz component. If it's present, I'd trace it backward through the power tree — is it coming from the input supply, a switching regulator's control loop oscillating at low frequency, or a load that's periodically drawing current?

A common root cause for low-frequency disturbances that vary with supply voltage is a control loop instability in a switching regulator — sometimes called "sub-harmonic oscillation" or a low-frequency limit cycle. This can happen when the compensation network is marginal, or when the load current is very light and the regulator is in pulse-skipping or burst mode. I'd check whether the regulator is operating in the expected mode and whether the output ripple shows the same periodicity.

Another possibility is a ground loop between the analog front-end and the rest of the system, where a low-frequency current (perhaps from a heater, motor, or other periodic load) flows through the ground conductor and creates a voltage offset that appears at the amplifier output. I'd check the ground voltage difference between the analog ground and the system ground with a sensitive measurement.

I'd also consider thermal effects — if the disturbance period is in the 1–10 Hz range, it's probably too fast for thermal cycling of a component, but I wouldn't rule out a self-heating effect in a precision reference or amplifier that's creating a periodic offset.

**Possible follow-ups:**
- How would you distinguish between a power supply coupling issue and a ground loop issue in this scenario?
- What test equipment setup would you use to capture and analyze a disturbance at these low frequencies?

---

## Q3: How would you approach selecting between a SAR ADC and a sigma-delta ADC for a medical device that measures a slowly varying physiological signal (e.g., temperature or pressure) with high resolution, and what are the key trade-offs you'd consider?

**Answer:** For a slowly varying physiological signal like temperature or pressure, the signal bandwidth is typically very low — often below a few hertz, sometimes up to a few hundred hertz for pressure waveforms. The key requirement is high resolution with low noise, not high sampling rate.

Sigma-delta ADCs are often the natural choice for this application. Their oversampling and noise-shaping architecture pushes quantization noise out of the band of interest, achieving very high effective resolution (16–24 bits) with relatively modest analog front-end requirements. The built-in digital filter also provides excellent rejection of out-of-band noise, which can simplify the anti-aliasing requirements — often a simple RC filter suffices.

SAR ADCs, by contrast, sample the signal directly and require a proper anti-aliasing filter before the converter. They offer lower latency, no pipeline delay, and are less sensitive to multiplexing artifacts. However, achieving 16+ effective bits with a SAR ADC requires a very clean analog front-end, careful layout, and a low-noise reference — the burden is on the external circuitry rather than the converter's architecture.

Key trade-offs I'd consider:

**Resolution and noise:** Sigma-delta converters typically achieve higher effective resolution for low-bandwidth signals. A 24-bit sigma-delta might deliver 18–20 effective bits in a 10 Hz bandwidth, while a 16-bit SAR might deliver 14–15 effective bits in practice due to noise.

**Latency:** Sigma-delta converters have inherent latency due to the digital filter. For a temperature or pressure monitor, this is usually irrelevant. For real-time control loops, it could matter.

**Multiplexing:** If I need to measure multiple channels with one ADC, SAR is easier to multiplex because of its "sample-on-command" nature. Sigma-delta converters need settling time after switching channels, which can be problematic if the input multiplexer changes frequently.

**Power consumption:** For battery-powered devices, sigma-delta converters can be very power-efficient for low-bandwidth signals because they can operate at low oversampling rates. SAR converters have power that scales with sampling rate.

**Anti-aliasing requirements:** Sigma-delta's internal digital filter provides inherent anti-aliasing, while SAR requires an external analog filter. For a medical device where board space and component count matter, this is a real consideration.

**Reference sensitivity:** Both architectures are sensitive to reference noise, but sigma-delta's noise shaping makes it somewhat more forgiving of low-frequency reference noise in the passband.

In practice, for a medical temperature or pressure monitor, I'd lean toward a sigma-delta ADC with a built-in PGA (programmable gain amplifier) if the sensor signal is small. The integration reduces external component count and the noise performance is typically excellent. However, if I needed to sample multiple channels rapidly or if the signal had meaningful higher-frequency content, I'd reconsider.

**Possible follow-ups:**
- How would the presence of a multiplexer change your ADC selection?
- What specifications would you compare between two candidate ADCs to make the final decision?

---

## Q4: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** A hardware latch for a medical device fault condition needs to satisfy two seemingly contradictory requirements: it must be persistent (once triggered, it stays triggered even if the fault clears), and it must be resettable only through a deliberate action that ensures the system is safe to restart.

The classic approach is a silicon-controlled rectifier (SCR) or thyristor latch, or more commonly, a discrete latch built from a comparator and a feedback network. The comparator approach is more flexible and easier to design with precise thresholds.

The basic topology: a comparator monitors the fault condition (e.g., temperature via a thermistor divider, or current via a sense resistor). When the fault threshold is crossed, the comparator output goes high. A feedback resistor from the output to the non-inverting input creates positive feedback — once the output goes high, it holds itself high even if the input drops back below the threshold. This is the latching behavior.

For the reset mechanism, I'd design it so that the latch can only be cleared by removing power entirely (a power-on reset) or by a deliberate reset signal that's gated by additional safety conditions. In a medical device, I would not allow an automatic reset after a fault — the operator must acknowledge the fault and take deliberate action.

Key design considerations:

**Threshold accuracy:** The comparator threshold must be accurate over temperature and supply variation. I'd use a precision reference (not just a resistor divider from the supply) to set the threshold, since the supply may vary.

**Hysteresis vs. latching:** It's important to distinguish between hysteresis (where the threshold for turning off is lower than the threshold for turning on, but the circuit recovers automatically) and true latching (where the circuit stays in the fault state indefinitely). For a medical device, I'd typically want true latching for safety-critical faults — the device should not restart automatically after an over-temperature or overcurrent event.

**Reset integrity:** The reset mechanism must be debounced and must not be susceptible to noise or glitches. A simple RC debounce or a proper reset IC might be needed. The reset should also be gated — for example, the operator must release the reset button and press it again, or the reset must be held for a minimum duration.

**Fail-safe behavior:** The latch must fail in the safe state. If power is lost, the latch should reset to the "no fault" state, but the system should then require a deliberate restart sequence. If the comparator itself fails, the design should ensure the output defaults to the fault state.

**Independence from firmware:** The latch should be entirely hardware-based, not dependent on the microcontroller. The microcontroller can read the latch state and can initiate a reset, but the latch must function correctly even if the firmware hangs.

**Verification:** I'd verify the latch through fault injection testing — simulate the fault condition, confirm the latch triggers, remove the fault, confirm the latch holds, then test the reset sequence to confirm it only clears under the intended conditions. I'd also test for noise immunity — brief transients on the sense input should not trigger the latch falsely.

**Possible follow-ups:**
- How would you design the reset circuit to ensure it can't be triggered accidentally by noise or a glitch?
- What failure modes of the latch circuit itself would you analyze as part of a risk assessment?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing the hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the hardware approach is necessary because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical design decision where the disagreement isn't about preference — it's about the fundamental safety architecture of the device. My approach would be to address it through structured engineering analysis rather than positional debate.

First, I'd acknowledge the firmware lead's valid points. A firmware-based approach does offer flexibility in threshold adjustment, and it could save board space and cost. These are legitimate engineering considerations, and dismissing them outright would be counterproductive.

Then, I'd reframe the discussion around the safety requirements. In a medical device, the over-temperature protection isn't just a convenience feature — it's a safety function that prevents patient harm. The question isn't "which approach is cheaper" but "which approach can be verified to meet the safety requirements under all foreseeable conditions."

I'd propose we conduct a structured analysis together, using the framework of ISO 14971 (risk management) and IEC 60601 (medical device safety). Specifically, I'd suggest we analyze the failure modes of each approach:

For the firmware approach, the key question is: what happens if the firmware hangs or crashes? If the protection is implemented in firmware, a firmware failure could disable the protection entirely. We'd need to demonstrate that the firmware is fail-safe — that a crash would result in the motor being shut down, not left running. This is very difficult to guarantee without a separate watchdog mechanism, and even then, there's a window during which the motor could run unprotected.

For the hardware approach, the protection is independent of firmware state. Even if the firmware crashes, the comparator and latch will still detect over-temperature and shut down the motor. This provides a layer of defense that's independent of software correctness.

I'd also raise the question of the ADC as a common-mode failure point. If the ADC fails or its reference drifts, the firmware might not detect the over-temperature condition. The hardware comparator, using a separate reference and sensing path, provides diversity — it's unlikely to fail in the same way as the ADC.

Rather than insisting on my approach, I'd propose we evaluate both options against the safety requirements and let the analysis drive the decision. If the firmware lead can demonstrate that the firmware approach meets the safety requirements with adequate reliability — perhaps with a hardware watchdog and a separate temperature sensing path — I'd be open to considering it. But the burden of proof should be on demonstrating safety equivalence, not on cost savings.

I'd also suggest we involve the risk management team and possibly a safety reviewer to ensure the decision is made with appropriate expertise and documentation. In a medical device, these decisions need to be traceable and defensible in a regulatory submission.

**Possible follow-ups:**
- How would you structure the failure modes and effects analysis (FMEA) to compare these two approaches fairly?
- What if the firmware lead insists that the cost savings are significant enough to justify the additional risk — how would you escalate or resolve that?