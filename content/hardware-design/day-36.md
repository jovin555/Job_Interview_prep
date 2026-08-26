# hardware-design — Day 36

## Q1: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The core requirement here is that a fault condition must be *remembered* independently of the main processor, and the reset path must be deliberate and safe. I'd start by defining the fault detection mechanism — typically a comparator with a reference threshold, or a dedicated protection IC. The comparator's output feeds a latch, which can be implemented with a simple SCR (silicon-controlled rectifier), a discrete transistor pair, or a dedicated latch IC. The key design decisions are:

1. **Latch topology:** An SCR is simple and robust, but has a holding current requirement that must be guaranteed over the full operating range. A discrete transistor pair (e.g., two BJTs or a BJT + MOSFET) gives more control over the holding condition and reset behavior. A dedicated latch IC (like a flip-flop with a reset input) is cleanest but requires a valid logic supply — which may not be available if the fault is a power supply failure.

2. **Reset mechanism:** The reset must be deliberate — typically requiring a user action like power-cycling the device, pressing a physical reset button, or removing the fault source and then pressing a reset. I would *not* allow an automatic reset after the fault clears, because in a medical device, an intermittent fault that clears and re-triggers could cause repeated on/off cycling of a therapeutic output, which is dangerous. The reset path should be electrically independent of the fault detection path — for example, a momentary switch that pulls the latch's reset pin low, or a power-cycle that requires the user to deliberately turn the device off and on.

3. **Fail-safe behavior:** The latch must default to the *safe* state on power-up. This means the latch's power-on state must be well-defined — if the latch is a flip-flop, it needs a defined reset on power-up; if it's a discrete pair, the biasing must ensure it powers up in the unlatched state. I'd also consider what happens if the latch's own supply fails — the output must default to the safe state (e.g., motor driver disabled).

4. **Independence from the main processor:** The latch and its reset path must not depend on firmware. The reset button should directly gate the latch's reset input, not go through a GPIO that firmware controls. If firmware *must* be involved (e.g., for a "fault acknowledged" feature), I'd add a hardware AND condition — the latch resets only when both the physical button is pressed *and* a hardware-enable signal is present.

5. **Verification:** I'd verify the latch's behavior across temperature, supply voltage, and fault duration. I'd also test the reset path under fault conditions — for example, if the fault is still present when the user presses reset, the latch should immediately re-trigger, not oscillate.

**Possible follow-ups:**
- How would you test that the latch reliably re-triggers if the fault is still present at reset?
- What happens if the latch's own supply rail collapses during a fault — how do you ensure the output defaults to the safe state?

---

## Q2: How would you approach selecting between a SAR ADC and a sigma-delta ADC for a medical device that measures a slowly varying physiological signal (e.g., temperature or pressure) with high resolution, and what are the key trade-offs you'd consider?

**Answer:** For a slowly varying physiological signal, the first question is what "high resolution" actually means in terms of *accuracy* — not just bit count. Both architectures can deliver 16–24 bits, but they achieve it very differently.

**SAR ADC considerations:**
- SAR ADCs are typically 12–18 bits, with a conversion time in the microsecond range. They're inherently sample-by-sample — no latency, no need for digital filtering. This makes them easy to multiplex across multiple channels.
- The accuracy depends heavily on the external reference, the input driver (settling time, charge kickback), and the layout. A 16-bit SAR needs a very clean reference and a low-impedance input source.
- For a slowly varying signal, the SAR's speed is overkill, but it gives you the flexibility to oversample and average in firmware if needed.

**Sigma-delta considerations:**
- Sigma-delta ADCs are typically 16–24 bits, but they're *not* sample-by-sample — they use heavy oversampling and decimation filtering, which introduces latency and a group delay. For a slowly varying signal, this latency is usually irrelevant.
- The key advantage is that the sigma-delta's noise shaping pushes quantization noise out of the band of interest, so you get very high effective resolution in a narrow bandwidth — ideal for a 0–100 Hz physiological signal.
- The key disadvantage is that the digital filter's response can be a concern if the signal has any fast transients — for example, a pressure spike during a cough in a respiratory device. The filter can ring or smear the transient. I'd need to check the filter's step response and settling time.
- Sigma-delta ADCs also have a *differential* input structure that's well-suited to bridge sensors (like a pressure bridge), and they integrate the input over a sampling window, which provides inherent averaging of high-frequency noise.

**My decision process:**
1. Define the signal bandwidth and required accuracy (e.g., ±0.1°C over 0–50°C, or ±1% of reading for pressure).
2. Determine the noise budget — what's the sensor's output impedance, what's the expected noise floor, and what's the ADC's input-referred noise contribution?
3. Check the signal's transient behavior — if the signal can have fast edges (e.g., a pressure pulse), I'd lean SAR with oversampling, or a sigma-delta with a filter mode that has a fast settling option.
4. Consider the system-level implications — does the ADC need to be multiplexed? Does the firmware need sample-by-sample access, or is a filtered stream acceptable?
5. For a single-channel, slowly varying, high-accuracy measurement, I'd typically lean sigma-delta *if* the latency is acceptable, because the noise performance in a narrow bandwidth is superior. But if I need multi-channel multiplexing or fast response to transients, SAR is often the better choice.

**Possible follow-ups:**
- How would the anti-aliasing filter requirement differ between the two architectures?
- If the signal has a 10 ms transient that must be captured accurately, how would that change your choice?

---

## Q3: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** This is a classic "noise in the signal chain" debug. The key clues are: (1) the disturbance is periodic and low-frequency, (2) it's present with the input shorted, and (3) it scales with the supply voltage. I'd approach this systematically:

1. **Confirm the measurement setup:** First, I'd verify that the disturbance isn't an artifact of my measurement — is the scope probe grounded correctly? Is there a ground loop between the DUT and the scope? I'd try a battery-powered scope or a differential probe to rule this out.

2. **Identify the frequency precisely:** A 1–10 Hz periodicity is suspicious. I'd measure the exact frequency and look for correlations — is it exactly 50/60 Hz divided down? Is it the mains frequency's second harmonic? Is it related to a switching regulator's frequency divided down? I'd use an FFT on the scope to get the exact frequency and look for harmonics.

3. **Trace the coupling path:** Since the amplitude scales with supply voltage, the disturbance is likely coupled through the supply. I'd check:
   - **Power supply ripple:** Is the supply itself oscillating at 1–10 Hz? This could be a control-loop instability in an LDO or switching regulator — a low-frequency oscillation that's often load-dependent. I'd measure the supply rail directly at the op-amp's supply pin with a wide-bandwidth scope.
   - **Thermal effects:** A 1–10 Hz disturbance can be thermal — a component heating and cooling, causing a resistance change or a voltage offset drift. I'd check if the disturbance's amplitude changes with airflow (e.g., blowing on the board) or with the device's orientation.
   - **Reference instability:** If the circuit uses a voltage reference, a low-frequency disturbance on the reference would scale with supply voltage. I'd measure the reference output directly.
   - **Ground bounce:** A low-frequency current loop through the ground plane could cause a periodic offset. I'd check the ground voltage at the op-amp's input and output pins relative to the board's star ground.

4. **Isolate the stage:** I'd short the input at different points — at the connector, at the op-amp's input pin, and at the ADC's input — to determine which stage introduces the disturbance. I'd also bypass the op-amp entirely and feed a known DC voltage directly to the ADC to see if the disturbance persists.

5. **Check for external coupling:** A 1–10 Hz signal is often environmental — vibration (piezoelectric effects on cables), a nearby motor or pump cycling, or even a mechanical relay opening/closing. I'd check if the disturbance correlates with any mechanical activity in the lab.

6. **Most likely culprits:** In my experience, the most common causes are: (a) a marginal LDO that's oscillating at low frequency due to an incorrect output capacitor ESR, (b) a ground loop between the analog and digital sections that's modulated by a low-frequency digital signal (e.g., a status LED blinking at 1 Hz), or (c) a thermal oscillation in a high-value resistor in the feedback network.

**Possible follow-ups:**
- How would you distinguish between a power-supply-coupled disturbance and one coupled through the ground plane?
- What if the disturbance only appears when the device is running on battery, not on a bench supply — how would that change your approach?

---

## Q4: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The first step is to translate the ±0.1°C requirement into an electrical specification. For an RTD (e.g., PT100), the sensitivity is approximately 0.385 Ω/°C, so ±0.1°C is ±0.0385 Ω. If I drive the RTD with 1 mA, that's ±38.5 µV of signal error. For a thermistor, the sensitivity is much higher but highly nonlinear, so the error budget depends on the specific thermistor curve and the measurement temperature.

**Key design decisions:**

1. **Excitation current level:** Higher current gives more signal but causes self-heating. For a PT100, 1 mA is a common compromise — it produces 0.385 mV/°C and dissipates only 0.1 mW at 100 Ω (negligible self-heating). For a thermistor, I'd use a much lower current (e.g., 100 µA) because thermistors have higher resistance and are more sensitive to self-heating.

2. **Current source topology:** The classic approach is a Howland current source (an op-amp with a bridge feedback network) or a simple op-amp + transistor current source. The Howland source is attractive because it's precision and can be made bipolar, but it's sensitive to resistor matching — the two feedback resistor ratios must match to within 0.01% or better to maintain a high output impedance. A simpler approach is an op-amp driving a MOSFET or BJT with a sense resistor in the feedback loop. The sense resistor's tolerance and temperature coefficient directly set the current accuracy — I'd use a precision resistor (0.1% tolerance, ±10 ppm/°C or better).

3. **Reference and op-amp selection:** The current source's accuracy is set by the reference voltage and the sense resistor. I'd use a precision reference (e.g., 2.5V with ±0.05% initial accuracy and low drift) and divide it down to set the current. The op-amp needs low offset voltage (to avoid adding error to the reference) and low drift. A chopper-stabilized op-amp (offset < 5 µV, drift < 0.05 µV/°C) is a good choice.

4. **Error budget:** I'd allocate the ±0.1°C budget across: (a) current source accuracy and drift, (b) ADC reference accuracy and drift, (c) ADC quantization and noise, (d) sensor tolerance and drift, and (e) self-heating error. For a PT100 with 1 mA excitation, self-heating in still air can be 0.05–0.1°C, so I'd need to account for that — possibly by using a pulsed excitation (e.g., 1 mA for 10 ms, then off) to reduce average power.

5. **Calibration:** Even with precision components, I'd include a calibration step at manufacturing — measure the actual current with a precision resistor and store the correction factor in firmware. This relaxes the component tolerances and improves the end-to-end accuracy.

6. **Layout:** The sense resistor and RTD connections should be Kelvin (4-wire) to eliminate lead resistance errors. The current source's output should be guarded or shielded to prevent leakage currents, especially in a humid environment.

**Possible follow-ups:**
- How would you handle the self-heating error if the sensor is in a well-insulated enclosure?
- What if the sensor is a thermistor with a highly nonlinear response — how would that change your design?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing a hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical disagreement, so I'd handle it with a structured, evidence-based approach rather than simply asserting my position. Here's how I'd approach it:

1. **Acknowledge the valid points:** The firmware lead is right that a firmware-based approach saves cost and board space, and it does allow more flexible threshold adjustment. I'd start by acknowledging those benefits so the discussion is collaborative, not adversarial.

2. **Reframe the question around the safety requirement:** The core issue isn't cost or board space — it's whether the protection meets the device's safety requirements. I'd ask: *"What does the risk analysis say about this fault condition? What's the required response time, and what's the required behavior if the main processor fails?"* If the risk analysis requires the protection to be independent of the main processor (which is common for over-temperature in a motor-driven medical device), then a firmware-based solution is architecturally non-compliant, regardless of how well it's implemented.

3. **Use the standards framework:** IEC 60601 and ISO 14971 typically require that a single fault (including a firmware hang or ADC failure) doesn't lead to an unacceptable risk. I'd ask the firmware lead to walk through the failure modes: *"What happens if the ADC's I2C bus hangs? What happens if the firmware is stuck in a loop and never reads the ADC? What happens if a memory corruption causes the threshold to be set to an invalid value?"* Each of these needs a credible answer. If the firmware lead can't provide one, that's the evidence that the hardware approach is necessary.

4. **Propose a middle ground if appropriate:** If the firmware lead's concern is threshold flexibility, I'd suggest a hybrid approach — keep the hardware comparator and latch for the *critical* shutdown path, but allow firmware to read the temperature and adjust the threshold via a digital potentiometer or a DAC-controlled reference. This gives the flexibility they want while preserving the independent hardware safety path.

5. **Escalate if needed:** If we still can't agree, I'd bring in the risk management engineer or the project's safety officer to facilitate a formal risk assessment. The decision should be based on the risk analysis, not on who argues more persuasively. I'd document the disagreement and the rationale for the final decision in the design history file.

6. **Keep the tone collaborative:** Throughout, I'd emphasize that we both want a safe, reliable device — we just have different views on how to achieve it. The goal is to find the solution that best meets the safety requirements, not to "win" the argument.

**Possible follow-ups:**
- What if the firmware lead insists that the firmware can be made "safe enough" with a watchdog timer and a self-test at startup — how would you respond?
- How would you document this disagreement in the design history file to satisfy regulatory requirements?