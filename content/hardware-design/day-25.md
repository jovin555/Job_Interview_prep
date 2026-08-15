# hardware-design — Day 25

## Q1: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The core requirement here is that the latch must be *fail-safe* — once a fault is detected, the system stays in a safe state until a human or a deliberate supervisory action clears it. I'd start by defining the fault detection and latch topology. A classic approach is a comparator (or a window comparator for over/under conditions) feeding a latch — either a discrete SR latch built from NAND/NOR gates, or a dedicated latch IC. The key design decisions are:

1. **Latch topology:** A discrete SR latch is simple and deterministic. I'd use a cross-coupled NAND pair, where the fault condition sets the latch and a reset signal clears it. The reset path must be edge-triggered or require a sustained signal — not just a level — to avoid clearing the latch if the reset line glitches.

2. **Reset authority:** The reset should come from a deliberate action — e.g., a momentary pushbutton, a key switch, or a command from a supervisory processor that has been verified healthy. If a processor is involved, I'd require a "reset enable" handshake: the processor must assert a reset-enable line, then pulse the reset line, and the latch only clears when both conditions are met. This prevents a single firmware glitch from clearing a real fault.

3. **Power-on behavior:** The latch must power up in a known state. I'd add a power-on reset circuit that forces the latch into the safe (fault) state until the system is deliberately initialized. This is critical for medical devices — you don't want a device powering up into an active state after a brown-out.

4. **Fault memory:** The latch should be powered from a rail that remains alive even if the main power fails — e.g., a backup battery or a capacitor that holds the latch state long enough for the system to shut down gracefully. Alternatively, use a non-volatile latch (like a latching relay or an EEPROM-based flag) if the fault must survive a full power cycle.

5. **Verification:** I'd add a test point or a status line so firmware can read the latch state, and I'd design the latch so it can be *tested* — e.g., a test mode that injects a simulated fault to verify the latch trips and holds.

The trade-off is between simplicity (discrete logic) and flexibility (programmable logic or a supervisor IC). For a medical device, I'd lean toward discrete logic or a dedicated supervisor IC because they're easier to analyze for safety certification — the behavior is deterministic and doesn't depend on firmware.

**Possible follow-ups:**
- How would you handle a fault that occurs *during* the reset sequence — e.g., the operator presses reset while the fault condition is still present?
- What if the fault condition is intermittent — how would you ensure the latch doesn't chatter?

---

## Q2: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The accuracy requirement drives everything here. For an RTD (e.g., PT100), a 0.1°C error corresponds to roughly 0.04 Ω — so the current source must be extremely stable, and the measurement chain must be designed to reject lead resistance and self-heating.

I'd start with the topology. A Howland current source (an op-amp-based voltage-controlled current source) is a common choice, but its accuracy depends on matched resistors. For higher precision, I'd consider a dedicated current source IC (e.g., a precision current reference) or a bootstrapped topology using a precision op-amp and a sense resistor.

Key design considerations:

1. **Current value and self-heating:** For an RTD, I'd use a low current — typically 100 µA to 1 mA. At 1 mA, a 100 Ω RTD dissipates 0.1 mW, which causes negligible self-heating (a fraction of a millidegree). The trade-off is that lower current means lower signal amplitude, so I need to budget noise carefully.

2. **Reference accuracy and drift:** The current source's accuracy is set by the voltage reference and the sense resistor. I'd use a precision reference (e.g., a bandgap or buried-zener reference with low drift) and a precision sense resistor (e.g., a metal-foil resistor with ±0.1% tolerance and low TCR). The op-amp's offset voltage and drift also contribute — I'd select an op-amp with low V_os (e.g., <10 µV) and low drift.

3. **Lead resistance compensation:** For a 2-wire RTD, lead resistance adds directly to the measurement. I'd use a 4-wire (Kelvin) connection for the RTD, which eliminates lead resistance from the measurement path. The current source drives the RTD through one pair of leads, and the voltage is sensed through a separate pair with high input impedance.

4. **Noise and filtering:** The current source should be low-noise — any noise on the current translates directly to measurement error. I'd add a low-pass filter on the current source output (e.g., an RC filter) to limit wideband noise, and I'd ensure the op-amp is stable with the capacitive load of the cabling.

5. **Calibration:** Even with precision components, I'd include a calibration step — e.g., a precision resistor in the signal path that can be switched in to verify the current source's accuracy. This is especially important for medical devices where the measurement must be traceable.

For a thermistor (NTC), the approach is similar but the nonlinearity is much larger, so the current source accuracy is less critical — the dominant error is the thermistor's own tolerance and the ADC's resolution. In that case, I'd focus more on the linearization and calibration strategy.

**Possible follow-ups:**
- How would you handle the trade-off between self-heating and signal-to-noise ratio when choosing the excitation current?
- What if the sensor is located several meters from the electronics — how would that affect your design?

---

## Q3: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** This is a classic symptom of a low-frequency oscillation or a power-supply-coupled disturbance. The fact that the input is shorted to ground rules out a signal-path issue, and the amplitude varying with supply voltage strongly suggests the disturbance is entering through the power rail or is a supply-dependent instability.

My debugging approach would be systematic:

1. **Characterize the disturbance precisely:** I'd capture the waveform on a scope with sufficient resolution (e.g., 16-bit ADC or a high-resolution scope) and measure the exact frequency, amplitude, and waveshape. Is it sinusoidal, sawtooth, or irregular? Does it drift over time? This helps narrow the cause — e.g., a relaxation oscillation vs. a thermal oscillation vs. a supply-ripple artifact.

2. **Check the power supply with a scope:** I'd probe the supply rail at the IC's power pin (not at the supply output) with AC coupling and high sensitivity. A 1–10 Hz disturbance on the rail could be caused by a thermal loop in a regulator (e.g., a linear regulator oscillating due to thermal feedback), a current-limit foldback, or a load that's cycling. I'd also check the reference voltage — if the reference is drifting at 1–10 Hz, that would directly couple into the output.

3. **Isolate the stage:** I'd bypass or disconnect stages one at a time — e.g., disconnect the output stage from the input stage, or power the front-end from a clean bench supply instead of the board's supply. If the disturbance disappears with a clean supply, it's supply-coupled. If it persists, it's internal to the front-end.

4. **Look for thermal effects:** A 1–10 Hz disturbance is suspiciously slow — it could be a thermal oscillation. For example, a power transistor or regulator heating up, changing its characteristics, and causing a feedback loop to oscillate. I'd use a thermal camera or a thermocouple to check if the temperature of any component is cycling at the same frequency.

5. **Check grounding:** A ground loop or a poor ground connection can cause low-frequency disturbances that track the supply. I'd check the ground path between the front-end and the supply — e.g., a long trace with significant resistance that creates a voltage drop when current flows.

6. **Consider the reference:** If the front-end uses a voltage reference, I'd check its output on a scope. Some references have a "popcorn noise" or micro-oscillation that appears at low frequencies. I'd also check if the reference's bypass capacitor is correctly sized — an undersized bypass can cause instability.

The most likely culprits, in my experience, are: (a) a regulator with a thermal loop oscillating, (b) a reference with inadequate bypassing, or (c) a ground-loop issue. The systematic isolation approach — clean supply, then clean reference, then clean ground — usually finds it quickly.

**Possible follow-ups:**
- What if the disturbance only appears when the device is powered from its battery, not from a bench supply — what would that tell you?
- How would you distinguish between a power-supply-induced disturbance and a ground-loop-induced disturbance?

---

## Q4: How would you approach designing a hardware-based over-temperature protection circuit for a medical device that uses a high-power motor driver, where the protection must be independent of the main microcontroller and must respond within milliseconds?

**Answer:** The key constraints are: (1) independence from the main processor, (2) fast response (milliseconds), and (3) fail-safe behavior. I'd design this as a dedicated analog protection circuit that sits between the temperature sensor and the motor driver's enable input.

My approach:

1. **Sensor selection:** A thermistor (NTC) is the most common choice for this — it's cheap, small, and has a fast thermal response. I'd place it as close as possible to the motor driver's heat source (e.g., on the driver IC's thermal pad or on the heatsink). For faster response, I could use a thermocouple, but that requires a cold-junction reference and amplification, which adds complexity. A PTC thermistor or a solid-state temperature switch (e.g., a thermostat IC) is another option — some have built-in hysteresis and a digital output, which simplifies the circuit.

2. **Comparator with hysteresis:** I'd use a comparator (not an op-amp — a comparator is designed for clean, fast switching) with a reference voltage that sets the trip point. The thermistor forms a voltage divider with a fixed resistor, and the divider output is compared against the reference. I'd add hysteresis (e.g., 5–10°C) to prevent chatter — the circuit should trip at, say, 85°C and reset at 75°C. The hysteresis also prevents the motor from cycling on/off rapidly.

3. **Latching vs. auto-reset:** For a medical device, I'd likely use a latching design — once the temperature exceeds the threshold, the motor is shut down and stays off until a deliberate reset. This prevents the motor from re-energizing if the temperature hovers near the threshold. The reset can be a manual pushbutton or a signal from the main processor (but the processor must not be able to *override* the protection — only clear it after the fault is resolved).

4. **Response time:** The comparator's propagation delay is typically microseconds, so the response is dominated by the thermal time constant of the sensor and the thermal path. To ensure the motor driver doesn't overheat before the sensor responds, I'd co-locate the sensor with the driver and ensure good thermal coupling (e.g., thermal vias, a thermal pad). I'd also verify the thermal response with a test — e.g., applying a step load and measuring how quickly the sensor temperature rises.

5. **Fail-safe design:** The circuit must fail in the safe direction. That means: if the sensor fails open or shorted, the circuit should trip (or at least not allow the motor to run). I'd design the divider so that a sensor failure (open or short) drives the comparator output to the "fault" state. I'd also add a pull-up/pull-down on the comparator output so that if the comparator loses power, the motor driver's enable is pulled to the safe state.

6. **Independence:** The protection circuit should have its own reference (not share the main processor's reference) and ideally its own supply rail or at least a well-filtered rail. The output should go directly to the motor driver's enable pin, not through the processor.

7. **Verification:** I'd test the circuit by injecting a simulated temperature (e.g., a resistor substituted for the thermistor) and verifying the trip point, hysteresis, and response time. I'd also test the failure modes — sensor open, sensor short, comparator output stuck — to confirm the circuit fails safe.

**Possible follow-ups:**
- How would you choose the trip point and hysteresis — what factors would you consider?
- What if the motor driver has a "soft" thermal shutdown built in — how would you coordinate your external protection with the driver's internal protection?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing your hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical disagreement, and my approach would be to focus on the *requirements* rather than the *implementation* — and to bring the discussion back to what the device must guarantee, not what's convenient.

First, I'd acknowledge the firmware lead's valid points: firmware-based protection is cheaper, more flexible, and can be adjusted without a board respin. Those are real benefits. But the question is whether the firmware approach can meet the *safety requirements* — and that's a requirements question, not a preference question.

I'd frame the discussion around three questions:

1. **What is the required safety integrity level?** For a medical device, the protection circuit is a safety function. If the device is Class II and the motor driver could cause patient harm if it overheats, the protection must be reliable under *all* conditions — including firmware hangs, ADC failures, and clock failures. A firmware-based solution is only as reliable as the firmware and the ADC — and if either fails, the protection is gone. The hardware circuit is independent of those failure modes.

2. **What does the standard require?** IEC 60601 and ISO 14971 require that safety functions be designed to be robust against single-fault conditions. If the firmware is the only protection, then a firmware hang is a single fault that defeats the safety function. A hardware circuit provides redundancy — even if the firmware hangs, the hardware still protects. I'd ask: "Can we demonstrate that the firmware-based approach meets the single-fault requirement? What's our analysis showing?"

3. **What's the failure mode analysis?** I'd propose we do a quick FMEA (Failure Mode and Effects Analysis) on both approaches. For the firmware approach, the failure modes include: firmware hang, ADC failure (stuck at a value), clock failure, GPIO failure, and software bugs. For the hardware approach, the failure modes are: comparator failure, sensor failure, and reference drift — but these are simpler and more predictable. The hardware approach has fewer failure modes and each is easier to analyze.

I'd also propose a *hybrid* solution: keep the hardware protection as the primary safety mechanism, but *also* implement the firmware monitoring as a secondary layer. The firmware can provide the flexible threshold adjustment and early warning (e.g., "temperature is rising, reducing motor speed"), while the hardware provides the guaranteed shutdown. This gives the firmware lead the flexibility they want without compromising safety.

If the firmware lead still disagrees, I'd escalate to the project's safety officer or the risk management team. This isn't a "my design vs. your design" issue — it's a safety requirement, and the decision should be made based on the risk analysis, not on board space or cost. I'd document the disagreement and the rationale in the design history file, and I'd ask for a formal risk assessment to settle it.

The key is to keep the discussion collaborative and requirements-driven, not adversarial. The firmware lead isn't wrong that firmware is cheaper — but the question is whether it's *safe enough*, and that's a question the risk analysis should answer.

**Possible follow-ups:**
- What if the firmware lead argues that the hardware circuit is *also* vulnerable to failure (e.g., the comparator could fail)? How would you respond?
- How would you handle this if the project manager is pushing for the firmware solution to meet a tight schedule?