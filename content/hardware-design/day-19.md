# hardware-design — Day 19

## Q1: How would you approach designing a hardware-based over-temperature protection circuit for a medical device that must be independent of the main microcontroller and respond within milliseconds?

**Answer:** The key requirement here is that protection must work even if the firmware hangs or the main processor fails, so the circuit needs to be entirely self-contained in hardware. I'd start by defining the thermal trip point and hysteresis window based on the maximum safe operating temperature of the protected component — for a motor driver, that's typically the junction temperature limit derated with a safety margin.

For the sensing element, an NTC thermistor is usually the practical choice because it's inexpensive and doesn't require a reference junction like a thermocouple. I'd place it as close as possible to the heat source, ideally under the component or on the thermal pad. The thermistor forms one leg of a resistor divider, and the divider output feeds a comparator with a precision reference on the other input. The comparator's output drives a latch or directly gates the motor driver's enable pin.

The critical design considerations are: first, the comparator needs built-in hysteresis (or external positive feedback) to prevent oscillation around the trip point — otherwise the system will chatter as temperature hovers near the threshold. Second, the response time requirement of milliseconds is easily met by a comparator, but the thermal time constant of the thermistor itself matters — a small SMD package responds faster than a larger one. Third, the trip point accuracy depends on the thermistor tolerance and the reference accuracy, so I'd budget for that: a 1% thermistor and 0.5% reference gives roughly ±2–3°C accuracy, which is usually acceptable for over-temperature protection.

For the latch and reset mechanism, I'd use a simple SCR-style latch or a flip-flop that holds the fault state until a deliberate reset — either a power cycle or a manual reset button. The reset path should be independent of the main processor so the system can recover even if firmware is hung. I'd also add a test point and possibly a test mode that lets manufacturing verify the trip threshold without actually heating the device to dangerous temperatures.

Finally, I'd verify the circuit's behavior across the full temperature range of the thermistor itself — the divider ratio changes with ambient temperature, so I need to confirm the trip point doesn't drift unacceptably from −10°C to +50°C ambient.

**Possible follow-ups:**
- How would you verify that the protection circuit actually responds within the required time, given that you can't safely heat the device to the trip point during testing?
- What failure modes of the thermistor or comparator would you consider, and how would the circuit behave if the thermistor fails open or short?

---

## Q2: How would you approach selecting the inductor for a boost converter that must deliver 5V at 500mA from a single Li-ion cell (3.0–4.2V), where the load has fast current transients?

**Answer:** The inductor selection for a boost converter involves several interrelated parameters, and the fast transient requirement adds an important constraint. I'd work through this systematically.

First, I'd determine the required inductance value from the ripple current specification. For a boost converter, the inductor ripple current is typically set to 20–40% of the average input current. With a 5V/500mA output and efficiency around 90%, the input power is roughly 2.8W, so at minimum input voltage (3.0V), the average input current is about 0.93A. If I target 30% ripple, that's about 280mA peak-to-peak. The inductance is then calculated from the standard boost equation: L = V_in × D / (f_sw × ΔI_L), where D = (V_out − V_in) / V_out. At 3.0V input with a 1MHz switching frequency, that gives roughly 4.7µH.

Second, the saturation current rating is critical. The inductor must handle the peak current — average input current plus half the ripple — without saturating. In this case, that's about 1.07A, so I'd look for an inductor rated at least 1.5–2A saturation current to provide margin. Importantly, I'd check the saturation current at the actual operating temperature, since saturation current decreases as temperature rises.

Third, for the fast transient requirement, the inductor's role is somewhat indirect — the output capacitor handles most of the transient energy, but the inductor's series resistance (DCR) affects how quickly the converter can replenish the output. A lower DCR means less power loss and better transient response. I'd also consider the inductor's core material — for 1MHz operation, a ferrite core is appropriate, but I'd check the AC losses at the switching frequency.

Fourth, I'd consider the inductor's self-resonant frequency (SRF). The SRF should be well above the switching frequency to avoid parasitic capacitance effects. For a 4.7µH inductor, the SRF is typically in the tens of MHz, which is fine for 1MHz switching.

Finally, I'd verify the design in simulation with the actual load transient profile — a 500mA step with a fast edge — to confirm the output voltage stays within the required tolerance. If the transient response is inadequate, I might increase the output capacitance rather than change the inductor, since the inductor value is largely set by the ripple requirement.

**Possible follow-ups:**
- How would the inductor selection change if the switching frequency were lowered to 400kHz to improve efficiency?
- What would you check on the inductor's datasheet to ensure it's suitable for high-frequency operation?

---

## Q3: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** This is a classic symptom pattern that points to a low-frequency, power-supply-coupled interference source rather than a signal-path problem. The fact that the disturbance appears with the input shorted rules out any issue with the sensor or input conditioning. The key clue is that the amplitude varies with the supply voltage — that suggests the disturbance is coupling through the power supply path.

I'd start by confirming the disturbance frequency precisely and checking whether it's stable or drifting. A stable frequency in the 1–10 Hz range often points to a thermal oscillation or a reference source. A drifting frequency might suggest an electromechanical source or a relaxation oscillator.

My first hypothesis would be a thermal feedback loop. If the analog front-end dissipates enough power to cause localized heating, and a temperature-sensitive component (like the reference or the input stage) is nearby, you can get a low-frequency thermal oscillation. The time constant of thermal coupling is typically in the 1–10 Hz range. I'd check for this by measuring the temperature of key components with a thermal camera or by touching components while watching the output — if the disturbance changes when you touch a specific component, that's a strong clue.

My second hypothesis would be a reference or bias circuit issue. If the voltage reference has insufficient decoupling or is oscillating at a low frequency, that would couple directly into the signal path. I'd probe the reference output with a scope in AC-coupled mode to look for low-frequency modulation.

My third hypothesis would be a ground loop or ground bounce issue. Even with the input shorted, if there's a ground path that carries current from another part of the circuit (like a switching regulator or a display), the resulting ground potential variation would appear at the output. I'd check the ground voltage between the analog front-end's ground and the system ground with a scope.

My debugging approach would be: first, use a spectrum analyzer or FFT on the output to characterize the disturbance precisely. Second, probe the power supply rails at the analog front-end's pins — if the disturbance appears there, it's a supply issue. Third, probe the reference output. Fourth, try isolating sections of the circuit — disconnect the load, bypass the reference, or power the analog front-end from a bench supply instead of the system supply. If the disturbance disappears with a clean bench supply, the problem is in the power path.

I'd also consider whether the disturbance correlates with any periodic activity elsewhere in the system — a wireless radio waking up, a display refreshing, or a motor cycling. Even at 1–10 Hz, these events could cause supply dips that couple into the analog path.

**Possible follow-ups:**
- How would you distinguish between a thermal oscillation and a power-supply-coupled interference using measurements alone?
- What would you look for in the layout to confirm or rule out a ground-loop issue?

---

## Q4: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The accuracy requirement of ±0.1°C drives every design decision here, so I'd start by working backward from that to establish the error budget. For a typical RTD like a PT100, the sensitivity is about 0.385 Ω/°C, so ±0.1°C corresponds to ±0.0385 Ω. For a thermistor, the sensitivity is much higher but highly nonlinear, so the error budget depends on the specific part.

For the current source itself, the key parameters are accuracy, stability, and noise. The current source's error contributes directly to the temperature measurement error — if the current drifts by 0.1%, that's roughly 0.1°C error for a PT100. So I'd target the current source accuracy and stability to be at least 10× better than the overall requirement, meaning ±0.01% or better.

I'd use a precision voltage reference and a precision op-amp in a Howland current pump configuration, or a simpler two-op-amp design with a precision resistor to set the current. The critical components are:

The voltage reference: I'd choose a reference with low initial error (±0.05% or better) and low temperature drift (5 ppm/°C or better). Over a 50°C range, a 5 ppm/°C reference drifts 250 ppm, which is about 0.025% — that's within budget but tight, so I might go with a 2 ppm/°C reference for more margin.

The sense resistor: This is often the dominant error source. I'd use a precision resistor with ±0.01% tolerance and a low temperature coefficient (10 ppm/°C or better). A metal foil resistor is ideal. The resistor's power dissipation should be kept low to minimize self-heating — for a 1mA current source with a 1kΩ sense resistor, dissipation is only 1mW, which is fine.

The op-amp: I'd look for low offset voltage (under 50µV), low offset drift (under 0.5µV/°C), and low bias current (under 1nA for a FET-input op-amp). The op-amp's offset voltage directly adds to the reference voltage, so a 50µV offset on a 2.5V reference is only 0.002% — acceptable.

For the sensor excitation, I'd use a current of 1mA for a PT100 — this keeps self-heating low while providing a reasonable signal level (0.385V at 0°C). The sensor's self-heating error depends on the thermal resistance of the package, so I'd verify that the power dissipation (1mW) produces negligible temperature rise.

I'd also consider the lead wire resistance for the RTD. If the sensor is remote, lead resistance adds directly to the measurement. A 3-wire or 4-wire connection eliminates this error, but if only 2-wire is possible, I'd need to calibrate out the lead resistance or use a lead-compensation technique.

Finally, I'd design the calibration procedure: a two-point calibration at known temperatures (e.g., ice bath at 0°C and a precision bath at 50°C) to correct for the current source's absolute error and the sensor's tolerance. The calibration coefficients would be stored in the device's non-volatile memory.

**Possible follow-ups:**
- How would the design change if you were using a thermistor instead of an RTD, given the thermistor's exponential nonlinearity?
- How would you verify the ±0.1°C accuracy in production without a precision temperature bath?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing your hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical disagreement, so I'd approach it with a focus on the regulatory requirements and the actual risk, not on defending my original design. The first thing I'd do is acknowledge the firmware lead's valid points — a firmware-based approach does save board space and cost, and it does allow more flexible threshold adjustment. Those are legitimate engineering trade-offs, and I'd want to be open to them if the safety case can be maintained.

However, the core issue here is that the protection must work under fault conditions, including firmware failure. The IEC 60601 framework requires that safety functions be designed so that a single fault doesn't lead to an unacceptable risk. If the firmware hangs, the ADC fails, or the firmware's temperature monitoring loop is delayed by other tasks, the over-temperature protection could fail exactly when it's needed most.

I'd frame the discussion around the safety requirements rather than personal preference. I'd ask: "What's the failure mode analysis for the firmware-based approach? What happens if the ADC's I2C interface locks up? What happens if the firmware is stuck in an interrupt handler? What's the worst-case response time if the firmware is busy with other tasks?" These questions move the discussion from opinion to engineering analysis.

I'd also point out that the regulatory review will ask exactly these questions. The design history file needs to document the safety analysis, and a firmware-based protection scheme will require a much more rigorous software safety analysis — potentially including a software safety classification that triggers additional documentation and testing requirements. The apparent cost savings in hardware might be offset by increased software development and verification costs.

That said, I'd be open to a hybrid approach. For example, we could keep a simple hardware comparator as a last-resort shutdown — just a comparator, reference, and a latch, which is minimal cost and board space — while using the firmware-based approach for more nuanced thermal management, like reducing motor speed before shutting down. The hardware provides the fail-safe backstop, and the firmware provides the flexible, intelligent control.

If the firmware lead still disagrees after this discussion, I'd escalate to the project manager and the quality/regulatory team, because this is a safety decision that shouldn't be made unilaterally by either engineer. I'd document the disagreement and the analysis in the design history file, and let the formal risk management process (ISO 14971) drive the decision.

**Possible follow-ups:**
- How would you quantify the risk difference between the hardware and firmware approaches to present to the project manager?
- What if the firmware lead argues that the hardware comparator could also fail — how would you respond?