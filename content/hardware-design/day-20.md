# hardware-design — Day 20

## Q1: How would you approach designing the input protection and conditioning circuit for a medical device that measures biopotential signals (e.g., ECG) from electrodes connected via a patient cable, considering both safety and signal quality?

**Answer:** The design needs to balance three competing requirements: patient safety (isolation, leakage current limits), signal fidelity (very small signals, high source impedance), and robustness (defibrillation pulses, ESD, RF interference from the environment).

Starting with safety: the patient-connected portion must be isolated from the mains-referenced circuitry, typically with a reinforced insulation barrier. I'd use an isolated front-end approach — either an isolated amplifier or a digital isolator after the ADC — and ensure the isolation barrier meets the applicable creepage/clearance distances and leakage current limits (typically ≤10 µA for BF-type applied parts under normal conditions). I'd also include a current-limiting resistor network in series with each electrode lead, sized to limit fault current to safe levels even if the patient comes into contact with another voltage source.

For signal conditioning, the front-end would be a two-stage approach. The first stage is a high-input-impedance instrumentation amplifier with a gain of maybe 10–20, a high CMRR (≥100 dB at 50/60 Hz), and a right-leg-drive circuit to actively cancel common-mode voltage. The second stage provides additional gain (total gain of maybe 100–1000) and filtering. I'd include a high-pass filter (0.05–0.5 Hz cutoff) to remove electrode offset potentials and DC drift, and a low-pass anti-aliasing filter before the ADC.

For protection: each electrode input needs a series resistor (e.g., 100 kΩ–1 MΩ) and clamping diodes to the supply rails to handle ESD and transient events. If defibrillation protection is required, I'd add spark-gap devices or gas discharge tubes, plus higher-value series resistors, to handle the high-voltage pulse without damaging the front-end.

The key trade-off is between input impedance and noise. Higher series resistance improves protection but increases thermal noise and interacts with the amplifier's input bias current. I'd select an instrumentation amplifier with very low bias current (e.g., FET-input) and keep the series resistance as low as safety allows.

**Possible follow-ups:**
- How would you verify that the isolation barrier meets leakage current requirements during design validation?
- What happens to the CMRR if the two electrode impedances are significantly mismatched, and how would you mitigate that?

---

## Q2: Walk me through how you would debug a circuit where a 3.3V rail measures correctly at the power supply output but drops to 2.9V at the load IC's power pin, and the drop only appears when the IC is actively processing data.

**Answer:** This is a classic dynamic voltage drop problem — the rail looks fine under static conditions but collapses under transient load. The fact that it only appears during active processing tells me the issue is related to current draw, not a static wiring problem.

My first step would be to confirm the measurement. I'd use an oscilloscope with a differential or 1:1 probe directly at the IC's power pin and ground pin (not at the supply output), measuring during the processing activity. I'd want to see the waveform — is it a steady drop, a periodic dip, or a spike-related droop? This tells me whether it's resistive (IR drop), inductive (di/dt), or a regulation loop issue.

The most likely causes, in order of probability:

1. **Trace/connector resistance**: A long, narrow trace or a connector contact with high resistance creates an IR drop proportional to current. During processing, the IC draws more current, and the drop appears. I'd calculate the expected resistance from the trace geometry and compare it to the measured drop divided by the current draw.

2. **Inadequate decoupling**: If the bulk capacitance is too far from the IC, or the high-frequency decoupling is insufficient, the local voltage collapses during fast current transients. The inductance of the trace between the bulk cap and the IC creates a voltage dip proportional to di/dt.

3. **Ground bounce**: The drop might actually be on the ground side — the IC's ground pin is elevated relative to the supply's ground due to current flowing through a shared ground path. This is easy to miss if you're only measuring the power pin relative to a different ground reference.

4. **Regulator transient response**: If the regulator's loop bandwidth is too low, it can't respond quickly enough to the load step, and the output droops until the loop catches up.

My debugging approach: first, measure both the power pin and ground pin at the IC with a differential probe. Then, add a temporary bulk capacitor (e.g., 100 µF) right at the IC's power pins — if the drop improves significantly, it's an inductance/trace issue. If not, it's more likely resistive or a regulator loop issue. I'd also check the ground path — measure the voltage between the IC's ground pin and the supply's ground terminal during the transient.

**Possible follow-ups:**
- How would you distinguish between an IR drop and an inductive drop from the waveform shape?
- What if the drop only appears at certain clock frequencies or data patterns — what does that tell you?

---

## Q3: How would you approach designing a hardware-based over-temperature protection circuit for a medical device that uses a high-power motor driver, where the protection must be independent of the main microcontroller and must respond within milliseconds?

**Answer:** The key requirements are independence from the main processor, speed, and reliability. The protection must work even if the firmware hangs, the ADC fails, or the microcontroller is in reset.

The architecture would be a dedicated analog comparator-based circuit with a temperature sensor placed at the critical thermal point — typically on the motor driver's heatsink or directly on the driver IC's thermal pad. I'd use a thermistor or a temperature-sensing IC with a comparator, not the microcontroller's ADC.

The circuit topology: a thermistor (NTC) in a voltage divider, with the divider output fed to a comparator's input. The other comparator input gets a reference voltage from a precision reference (not from the microcontroller's supply, which could be noisy or fail). The comparator output drives a latch circuit that disables the motor driver — either by pulling the enable pin low, cutting the gate drive, or opening a series switch in the motor supply path.

Key design considerations:

1. **Hysteresis**: The comparator needs hysteresis (e.g., 5–10°C) to prevent oscillation around the trip point. Without it, the circuit could rapidly toggle on/off at the threshold, causing relay chatter or repeated motor restarts.

2. **Latching behavior**: For a medical device, I'd typically latch the fault condition — once tripped, the circuit stays off until a deliberate reset (e.g., power cycle or a manual reset button). This prevents the motor from cycling on/off repeatedly, which could be dangerous if the fault condition persists.

3. **Response time**: A comparator with a propagation delay of tens of nanoseconds to a few microseconds is more than fast enough for a thermal event, which has a time constant of seconds. The real speed constraint is the sensor's thermal time constant — the thermistor must be physically close to the heat source to detect the temperature rise quickly.

4. **Fail-safe behavior**: I'd design the circuit so that a sensor failure (open or short) also triggers the protection. For example, if using an NTC thermistor, an open circuit would pull the comparator input to a voltage that trips the protection. This is a "fail-safe" design — any component failure results in the safe state (motor off).

5. **Verification**: I'd test the circuit by injecting a simulated temperature signal (e.g., a variable resistor in place of the thermistor) to verify the trip point, and also test with the actual motor running under load to measure the thermal response.

**Possible follow-ups:**
- How would you choose between a thermistor and a temperature sensor IC for this application?
- What if the motor driver's enable pin has a maximum voltage rating lower than your comparator's output — how would you interface them?

---

## Q4: How would you approach selecting the output capacitor for a boost converter that supplies a load with fast current transients (e.g., a wireless radio that bursts 200 mA for 5 ms), where the output voltage must stay within ±3% of 5V?

**Answer:** The output capacitor in a boost converter serves two roles: energy storage and output voltage regulation during load transients. The boost converter's control loop can't respond instantly to a load step — there's a delay while the inductor current ramps up — so the output capacitor must supply the transient current during that window.

My approach starts with the energy balance calculation. During the transient, the capacitor must supply the difference between the load current and the converter's output current capability. For a 200 mA step with a 5V output and ±3% tolerance (150 mV), I'd calculate the minimum capacitance using:

C ≥ I_transient × Δt / ΔV

But this is only the first-order approximation. The real-world behavior is more complex because:

1. **ESR (Equivalent Series Resistance)**: The capacitor's ESR creates an immediate voltage drop when current steps — this is a resistive drop, not a charge-depletion drop. For a 200 mA step and 150 mV budget, the ESR must be below about 750 mΩ, but I'd want much lower (e.g., <100 mΩ) to leave most of the budget for the charge-depletion effect.

2. **ESL (Equivalent Series Inductance)**: At the fast edges of the current transient, ESL causes a voltage spike proportional to di/dt. For a 5 ms burst, the edges might be fast (microseconds), so ESL matters. Ceramic capacitors in small packages have low ESL, which is why they're preferred for this role.

3. **Capacitor type and voltage derating**: I'd use ceramic capacitors (X5R or X7R dielectric) for the bulk of the capacitance, but I need to account for DC bias derating — a 10 µF, 10V ceramic cap might only provide 4–5 µF at 5V DC bias. I'd check the manufacturer's DC bias curves and size accordingly.

4. **Control loop interaction**: The output capacitor's value and ESR affect the converter's control loop stability. A boost converter in continuous conduction mode has a right-half-plane zero that makes compensation tricky. Adding too much capacitance can push the loop's crossover frequency down, slowing the transient response. I'd need to check the converter's datasheet for recommended output capacitance ranges and possibly adjust the compensation network.

5. **Multiple capacitors in parallel**: I'd typically use a combination — a larger bulk capacitor (e.g., 22–47 µF) for energy storage and a smaller, low-ESL ceramic (e.g., 1–4.7 µF) close to the load for high-frequency transient response.

The verification step would be a bench test: apply the actual load transient (or a simulated one with an electronic load) and measure the output voltage deviation with an oscilloscope. I'd check both the initial droop (ESR/ESL effect) and the recovery time (control loop response).

**Possible follow-ups:**
- How does the boost converter's right-half-plane zero affect your capacitor selection?
- What would you do if the measured transient response exceeds the ±3% specification?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing the hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical design decision, and I'd handle it by focusing on the engineering evidence and regulatory requirements rather than just asserting my position. The disagreement isn't about cost or board space — it's about whether the firmware approach can meet the safety requirements.

My approach would be structured:

1. **Acknowledge the valid points**: The firmware lead is right that a firmware solution saves cost and board space, and it does offer more flexibility in threshold adjustment. I'd acknowledge these benefits upfront to show I'm not dismissing their proposal out of hand.

2. **Reframe the discussion around requirements**: I'd bring the discussion back to the safety requirements. For a medical device, the over-temperature protection is a safety function — it prevents a hazardous condition (overheating, potential fire, or patient injury). The question isn't whether firmware *can* do it, but whether it can do it *reliably enough* to meet the safety requirements.

3. **Present the specific failure modes**: I'd walk through the failure scenarios that the hardware circuit handles but the firmware approach doesn't:
   - Firmware hangs or enters an infinite loop → no temperature monitoring
   - ADC fails (stuck at a value, out of range, or noisy) → no valid temperature reading
   - Firmware update goes wrong → protection disabled during the update
   - Watchdog timer resets the MCU → protection is unavailable during the reset period
   - The GPIO output fails → the motor can't be shut down even if the fault is detected

4. **Reference the regulatory framework**: I'd point out that IEC 60601 and ISO 14971 require that safety functions be designed with appropriate risk mitigation. A single-point failure in the firmware (a software bug, a hardware fault in the ADC, or a clock failure) could defeat the protection. The hardware circuit provides an independent, diverse channel — it doesn't share the same failure modes as the firmware path.

5. **Propose a middle ground if appropriate**: If the firmware lead's cost/size concerns are valid, I'd explore options that maintain the safety integrity:
   - Keep the hardware comparator but use a simpler, cheaper implementation
   - Use a dedicated temperature sensor IC with a built-in comparator and latch (some have this integrated)
   - Use the firmware as a secondary, redundant protection layer, with the hardware as the primary
   - If the firmware approach is truly necessary, add a hardware watchdog that's independent of the main processor and can shut down the motor if the firmware doesn't respond

6. **Escalate if needed**: If we can't reach agreement, I'd suggest a formal risk assessment (e.g., an FMEA) to evaluate both approaches against the safety requirements, and involve the quality/regulatory team. The decision should be based on documented risk analysis, not on who argues more persuasively.

The key principle is that safety-critical functions need independent, diverse protection paths. The firmware approach creates a single point of failure — if the MCU fails, both the monitoring and the response fail. The hardware circuit provides independence, which is a fundamental principle of safety design.

**Possible follow-ups:**
- How would you quantify the risk difference between the two approaches in a formal FMEA?
- What if the firmware lead argues that the MCU has a hardware watchdog that will reset it if it hangs — how would you respond?