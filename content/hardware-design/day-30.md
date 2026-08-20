# hardware-design — Day 30

## Q1: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The core requirement here is that the latch must be *retriggerable* — once a fault occurs, the system stays in a safe state until a human or a controlled process explicitly clears it. I'd start by defining the fault threshold and the reset conditions clearly, since these drive the entire circuit topology.

For the latch itself, a classic approach is a comparator feeding a SCR or a discrete transistor latch, or a comparator with positive feedback (hysteresis) that creates a bistable state. A comparator with a resistor divider providing positive feedback is often the cleanest because it's deterministic and easy to analyze. The key design decision is the reset path: I'd use a dedicated reset input that requires a deliberate action — for example, a momentary push-button, a signal from a supervisory microcontroller that has been verified healthy, or a power-cycle with a mandatory "safe state" entry sequence.

The critical safety consideration is that the reset path must not be defeatable by the same fault condition. For instance, if the fault is over-temperature, the reset button should be electrically isolated from the thermal path, and the circuit should verify the fault has actually cleared before allowing a reset — otherwise you get a "reset loop" where the device immediately re-latches. I'd add a small delay or a "fault cleared" verification window before the latch releases.

For a medical device, I'd also want the latch to be testable — a way to inject a simulated fault during manufacturing test to verify the latch trips and holds. And I'd document the failure modes: what happens if the latch transistor fails short or open, and whether the fail-safe direction is correct (i.e., a component failure should default to the latched/safe state, not to normal operation).

**Possible follow-ups:**
- How would you ensure the latch itself doesn't get triggered by transient noise or power-up glitches?
- What if the reset action needs to be performed by the main processor — how would you prevent a firmware hang from defeating the reset?

---

## Q2: How would you approach selecting the inductor for a boost converter that must deliver 5V at 500mA from a single Li-ion cell (3.0–4.2V), where the load has fast current transients?

**Answer:** The selection starts with the inductor's role in a boost converter: it stores energy during the switch-on time and delivers it to the output during switch-off. The two parameters that dominate are inductance value and saturation current rating.

First, I'd calculate the minimum inductance based on the allowable ripple current. A common rule of thumb is to target 20–40% of the maximum input current as peak-to-peak ripple. For a boost converter, the input current is higher than the output current — at 3.0V input and 5V/500mA output, the input current is roughly 1A (accounting for efficiency), so ripple might be 200–400mA. Using the standard boost inductor equation (L = V_in × D / (f_sw × ΔI)), I'd get a value in the range of a few microhenries, depending on switching frequency.

The more critical check is saturation current. The inductor must handle the *peak* current — the average input current plus half the ripple — without saturating. If the inductor saturates, its inductance collapses, current spikes, and you get excessive noise, efficiency loss, and potentially damage to the switch. I'd derate the saturation current rating by at least 20–30% over the worst-case peak, and I'd check the saturation curve at the operating temperature, since saturation current decreases as temperature rises.

For fast load transients, I'd also consider the inductor's DCR (DC resistance) — lower DCR improves efficiency and reduces thermal stress. And I'd check the self-resonant frequency (SRF) to ensure it's well above the switching frequency, so the inductor behaves as an inductor, not a capacitor, at the switching harmonics.

Finally, I'd verify the inductor's core material — ferrite vs. iron powder vs. composite — because that affects both saturation behavior and core losses at the switching frequency. For a medical device, I'd also consider audible noise: some inductors whine at certain frequencies, which could be unacceptable in a patient environment.

**Possible follow-ups:**
- How would the inductor selection change if the switching frequency were 400 kHz versus 2 MHz?
- What failure modes would you consider for the inductor in a medical device context?

---

## Q3: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** This is a classic symptom pattern that points to a power-supply-coupled disturbance rather than a signal-path issue. The fact that the input is shorted to ground rules out the sensor or input conditioning as the source, and the amplitude varying with supply voltage strongly suggests the disturbance is entering through the power rails.

My first step would be to characterize the disturbance precisely: measure its frequency, amplitude, and waveform shape with a scope on the output, and simultaneously probe the power supply rail. I'd look for a corresponding ripple or disturbance on the supply at the same frequency. If the disturbance is on the supply, I'd trace it back — is it a switching regulator's low-frequency ripple? A control loop oscillation in a regulator? A thermal cycling effect in a reference?

A 1–10 Hz frequency is suspiciously low for most switching regulators (which typically run at 100 kHz–2 MHz), so I'd look for:
- A control loop instability in a linear regulator or reference — some regulators oscillate at low frequency when the load or output capacitance is marginal.
- A thermal feedback loop — a component heating and cooling, causing its parameters to drift at a low rate.
- A ground loop or reference drift — the "ground" at the input isn't actually at the same potential as the output reference, and the difference is modulated by something at 1–10 Hz.

I'd also check the reference voltage itself — if the ADC reference is drifting at 1–10 Hz, the output would show it even with a shorted input. I'd probe the reference with a scope in AC-coupled mode at high sensitivity.

The systematic approach is to isolate the disturbance by powering sections independently: power the analog front-end from a clean bench supply and see if the disturbance disappears; then power the rest of the board normally. That tells you whether the disturbance is generated internally or coupled in from elsewhere. I'd also check for mechanical issues — a loose connection or a component with a poor solder joint that's thermally cycling.

**Possible follow-ups:**
- What if the disturbance only appears when the device is battery-powered but not when it's on a bench supply — what would that tell you?
- How would you use an FFT or spectrum analyzer to help identify the source?

---

## Q4: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The first decision is the sensor type — RTD or thermistor — because that drives the current source requirements. For an RTD (typically 100Ω at 0°C), a common approach is a constant current source of 100µA to 1mA. The current must be stable because any drift directly translates to a temperature error: for a 100Ω RTD with a temperature coefficient of about 0.385 Ω/°C, a 1µA drift at 1mA excitation produces roughly 0.1Ω error, which is about 0.26°C — so the current source needs to be very stable.

I'd start with a precision reference and an op-amp-based current source. A common topology is the "Howland current pump" or a simpler two-op-amp design where a precision reference voltage is applied across a precision resistor, and the op-amp forces that voltage across the resistor to generate a known current. The key components are:
- A precision voltage reference (e.g., a bandgap reference with low drift, or a buried zener for higher accuracy).
- A precision resistor with low temperature coefficient (e.g., 0.1% tolerance, ±5 ppm/°C or better).
- An op-amp with low offset voltage and low offset drift — the offset voltage directly adds to the reference voltage error.

For the ±0.1°C requirement, I'd do a budget analysis: reference accuracy and drift, resistor tolerance and drift, op-amp offset and drift, and the sensor's own calibration. Each contributor gets allocated a portion of the error budget.

For a thermistor, the situation is different — thermistors are more sensitive but highly nonlinear, and self-heating is a bigger concern. I'd use a much lower current (e.g., 10–100µA) to keep self-heating below 0.01°C, and I'd account for the nonlinearity in firmware calibration.

I'd also consider a ratiometric approach: instead of generating an absolute current, use the same reference for both the current source and the ADC reference. This cancels reference drift — if the reference drifts, both the excitation current and the ADC scale drift in the same direction, and the measurement stays accurate. This is a powerful technique for medical devices where absolute accuracy over temperature is hard to achieve.

Finally, I'd add a calibration step at manufacturing — a known resistance in place of the sensor — to trim out residual offset and gain errors, and I'd document the self-heating calculation to verify it's within the error budget.

**Possible follow-ups:**
- How would you handle the self-heating trade-off between using a higher current for better signal-to-noise ratio and a lower current for less self-heating?
- What if the sensor is located remotely from the electronics — how would the lead resistance affect the measurement?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing your hardware-based overcurrent protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors current via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical disagreement, and the way I'd handle it is to focus on the *requirements* rather than the *implementation* — and to bring the discussion back to what the device actually needs to do.

First, I'd acknowledge the firmware lead's legitimate points: firmware-based protection does save board space and cost, and it does allow flexible threshold adjustment. Those are real benefits, and I wouldn't dismiss them. But I'd frame the discussion around the safety requirements: what does the protection need to guarantee, and under what failure conditions?

I'd ask a few pointed questions:
- What happens if the firmware hangs while the motor is running? Does the protection still engage?
- What happens if the ADC fails — either reading zero or reading a stuck value?
- What's the required response time for the protection? If the motor driver can be damaged or cause a hazard in 1ms, can firmware reliably respond that fast?

The key insight is that firmware-based protection creates a *single point of failure*: the same processor that runs the application is also responsible for detecting and responding to the fault. If the processor hangs, both the application and the protection fail. A hardware comparator and latch is independent — it works regardless of firmware state.

I'd propose a middle ground: keep the hardware comparator as the *primary* safety mechanism, but allow the firmware to adjust the threshold via a DAC or a digital potentiometer, or to read the comparator's status. This gives the firmware lead the flexibility they want while preserving the independence and guaranteed response time of the hardware. I'd also reference the relevant safety standard — for a medical device, the protection that prevents a hazardous condition typically needs to be fail-safe and independent of the application processor, and I'd suggest we review the requirements traceability to confirm what's actually mandated.

If we still disagreed, I'd escalate to a formal risk assessment — a DFMEA or a hazard analysis — where we document the failure modes of both approaches and let the risk assessment drive the decision. That takes the disagreement from "my opinion vs. yours" to "what does the analysis say is safe?"

**Possible follow-ups:**
- What if the firmware lead argues that the hardware comparator adds a failure mode of its own — what if the comparator fails? How would you respond?
- How would you document this decision in the design history file (DHF) for regulatory purposes?