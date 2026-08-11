# hardware-design — Day 21

## Q1: How would you approach designing a hardware-based fault detection and response scheme for a medical device that monitors a patient's physiological parameter, where the detection must be independent of the main application processor?

**Answer:** The core principle here is that safety-critical fault detection must not depend on the health of the very processor it's protecting. I'd start by defining the specific fault conditions — for example, over-temperature, overcurrent, or a sensor signal out of range — and then determine the required response time and the fail-safe state for each.

For the detection itself, I'd use dedicated analog comparators with precision references rather than relying on the ADC. The comparator thresholds would be set with hysteresis to prevent chatter at the trip point. The key design decision is the reference source: it should be independent of the main processor's supply and ideally a dedicated voltage reference, because if the main rail sags during a fault, you don't want the threshold to shift.

For the response, I'd use a hardware latch — typically a set-reset flip-flop or a comparator with positive feedback — that captures the fault event and holds it. The latch output would directly gate the hazardous output (e.g., a motor driver enable pin) through a dedicated hardware path, not through firmware. The reset mechanism needs careful thought: it should require a deliberate action, such as a manual reset button or a power-cycle, and the reset path itself must be verified to clear the latch only when the fault condition has genuinely cleared.

One aspect that's often overlooked is the independence requirement. The fault detection circuit should have its own supply filtering, its own ground return, and be physically separated from the processor's circuitry to avoid common-mode failures. I'd also add a self-test mechanism — for example, a firmware-initiated test that injects a known signal to verify the comparator still trips — because a fault detector that silently fails is worse than none.

Finally, I'd document the safety rationale: a hazard analysis showing each fault mode, the detection method, the response, and the failure mode of the detection circuit itself. This becomes part of the regulatory submission for a medical device.

**Possible follow-ups:** How would you verify that the fault detection circuit is truly independent of the main processor? What if the fault condition is transient — how would you distinguish a real fault from a glitch?

---

## Q2: How would you approach selecting the inductor for a boost converter that must deliver 5V at 500mA from a single Li-ion cell (3.0–4.2V), where the load has fast current transients?

**Answer:** The inductor selection starts with the converter's switching frequency and the allowable ripple current. For a boost converter, the inductor current is continuous, and I'd typically target a ripple current of 20–40% of the average input current. At 5V/500mA output with, say, 90% efficiency, the input current at minimum battery voltage (3.0V) is roughly 1.85A, so the ripple target would be around 370–740mA peak-to-peak.

The inductance value comes from the basic inductor equation: L = V_in × D / (f_sw × ΔI), where D is the duty cycle. At 3.0V input and 5V output, the duty cycle is about 40% (ignoring diode drop). With a 1MHz switching frequency and 500mA ripple, that gives roughly 2.4µH. I'd then check the worst-case ripple at the maximum input voltage (4.2V), where the duty cycle is lower and the ripple will be smaller.

The critical parameter is saturation current. The inductor must not saturate at the peak current — which is the average input current plus half the ripple. In this case, that's about 2.1A at minimum battery voltage. I'd select an inductor with a saturation current rating at least 20–30% above that to account for temperature derating and part-to-part variation. The saturation current should be specified at the worst-case operating temperature, because inductor saturation current typically decreases as temperature rises.

I'd also check the DC resistance (DCR) for efficiency — a lower DCR reduces I²R losses but usually means a larger physical size. The self-resonant frequency (SRF) should be well above the switching frequency to avoid parasitic capacitance effects. Finally, I'd consider the core material: for a medical device, I'd prefer a shielded inductor to minimize radiated EMI, and I'd verify the core loss at the switching frequency, since ferrite cores can heat up significantly at high frequencies.

For the fast load transients, the inductor's role is less about transient response (that's the output capacitor's job) and more about ensuring the converter can deliver the peak current without saturating. I'd verify the inductor's saturation current against the worst-case peak current during a transient, not just the steady-state value.

**Possible follow-ups:** How would the inductor selection change if the switching frequency were 400kHz instead of 1MHz? What failure mode would you worry about if the inductor saturates during a load transient?

---

## Q3: Walk me through how you would debug a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage.

**Answer:** This is a classic symptom pattern that points to a low-frequency, power-supply-coupled disturbance rather than a signal-path issue. The fact that the input is shorted to ground rules out the sensor or input conditioning. The amplitude varying with the supply voltage strongly suggests the disturbance is entering through the power supply or a reference.

My first step would be to look at the power supply with a scope in AC-coupled mode, using a low-inductance probe tip, to see if there's a 1–10 Hz ripple on the rail. A common cause is a thermal oscillation in a linear regulator — where the regulator's output drifts, heats up, and then corrects, creating a low-frequency cycle. Another possibility is a switching regulator operating in a low-frequency burst mode or pulse-skipping mode at light load, which can produce periodic disturbances in the 1–10 Hz range.

If the supply looks clean, I'd check the voltage reference. A reference with inadequate decoupling or marginal stability can oscillate at low frequencies. I'd also check for ground bounce: if the analog ground and power ground are connected at a single point, and there's a low-frequency current draw elsewhere on the board (e.g., a display refresh or a sensor heater cycling), that can create a periodic ground potential shift.

Another angle is thermal: a 1–10 Hz disturbance is suspiciously close to thermal time constants. I'd check whether the disturbance frequency changes with ambient temperature or airflow. A component with a temperature-dependent offset — like an op-amp with a large offset voltage temperature coefficient — could create a low-frequency drift if there's a heat source nearby cycling on and off.

I'd also suspect the decoupling network. If the analog supply has a ferrite bead with a resonance that interacts with the decoupling capacitors, it could create a low-frequency oscillation. I'd check the impedance of the supply network across frequency.

My debugging sequence would be: (1) scope the supply rails with AC coupling, (2) scope the reference voltage, (3) check ground potential differences between analog and digital sections, (4) use a thermal camera or thermocouple to look for temperature cycling, and (5) if needed, bypass sections of the circuit to isolate the source. I'd also try powering the analog section from a clean bench supply to see if the disturbance disappears — that would confirm it's supply-coupled.

**Possible follow-ups:** How would you distinguish between a power supply issue and a ground loop as the cause? What if the disturbance only appears when the device is battery-powered but not when on a bench supply?

---

## Q4: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The first decision is the sensor type. For a thermistor, the excitation current must be low enough to avoid self-heating — typically 100µA or less for a small bead thermistor. For an RTD (typically 100Ω platinum), the excitation current is often 1mA, which at 100Ω produces only 0.1mW of self-heating, acceptable for most applications. The self-heating error must be included in the accuracy budget.

For the current source itself, I'd use a precision op-amp with a feedback loop around a sense resistor. The classic topology is a Howland current source or a simpler op-amp + MOSFET + sense resistor configuration. The key parameters are the reference voltage accuracy and the sense resistor tolerance and temperature coefficient. For ±0.1°C, I'd budget roughly ±0.05°C for the current source error, which translates to about ±0.05% current accuracy for a PT100 RTD (since the RTD changes about 0.385Ω/°C, and at 1mA that's 0.385mV/°C — so 0.1°C is about 38.5µV at the sense resistor).

The reference voltage should be a precision reference with low temperature drift — something like 5 ppm/°C or better. The sense resistor should be a precision resistor with a low temperature coefficient (e.g., 10 ppm/°C or better) and good long-term stability. The op-amp should have low offset voltage and low offset drift — for a 1mA current through a 1kΩ sense resistor, a 10µV offset error translates to 10nA of current error, which is negligible, but the offset drift over temperature matters.

I'd also consider the compliance voltage: the current source must be able to drive the sensor's maximum voltage drop (at the highest resistance and highest temperature) plus the sense resistor drop, while staying within the op-amp's output range. For a PT100 at 50°C (about 119.4Ω) with 1mA, that's about 119mV across the sensor plus 1V across a 1kΩ sense resistor — easily within a 3.3V supply.

For the measurement side, I'd use a ratiometric approach: use the same reference voltage for both the current source and the ADC reference. This cancels reference drift errors, because if the reference drifts, both the excitation current and the ADC's full-scale range shift in the same direction. This is a powerful technique for medical-grade measurements.

Finally, I'd include a calibration step at manufacturing: measure the actual current at a known temperature and store the correction factor. This compensates for the initial tolerance of the sense resistor and reference, leaving only drift over time and temperature.

**Possible follow-ups:** How would you handle the self-heating error in your accuracy budget? What if the sensor is located several meters away from the current source — how would that affect the design?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing your hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** I'd start by acknowledging the firmware lead's valid points — the firmware approach does save board space and offers flexibility, and those are legitimate engineering trade-offs. Then I'd reframe the discussion around the safety requirements rather than making it a personal disagreement.

The key question is: what does the safety standard require? For a medical device, the over-temperature protection is typically a safety mechanism, and the question is whether it needs to be independent of the main processor. If the hazard analysis shows that a firmware failure could lead to an unsafe condition (e.g., the motor continues running and causes patient harm), then the protection must be independent — that's a fundamental principle of safety engineering. The firmware can hang, the ADC can fail, or the GPIO can be misconfigured, and the protection must still work.

I'd propose a structured approach to resolve this: (1) review the hazard analysis and determine the required safety integrity level for the over-temperature protection, (2) assess the failure modes of the firmware-based approach — what happens if the firmware hangs, if the ADC returns erroneous readings, if the GPIO is stuck, or if there's a software bug in the threshold comparison, and (3) determine whether the firmware approach can meet the safety requirements with additional measures (e.g., a separate watchdog, redundant ADC channels, software self-tests).

If the analysis shows that firmware-based protection cannot meet the safety requirements, I'd present that evidence clearly. I'd also offer a middle ground: perhaps the firmware can provide the flexible threshold adjustment, but the hardware comparator remains as the final safety net. For example, the hardware comparator could have a fixed, conservative threshold (e.g., 85°C) that's high enough to avoid nuisance trips but low enough to prevent damage, while the firmware handles a more precise, application-specific threshold (e.g., 75°C) for normal operation. This gives the firmware lead the flexibility they want while maintaining the safety guarantee.

If we still disagree after the analysis, I'd escalate to the project manager or quality manager with a clear summary of the safety analysis, rather than letting it become a personality conflict. In a medical device context, the regulatory requirement for independent protection is well-established, and the decision should be based on the safety case, not on who argues more persuasively.

**Possible follow-ups:** How would you handle the situation if the firmware lead insists that the firmware-based approach can be made safe with a watchdog timer? What if the project schedule is tight and the hardware approach adds two weeks to the timeline?