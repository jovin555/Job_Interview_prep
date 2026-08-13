# hardware-design — Day 23

## Q1: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The core requirement here is fail-safe behavior: once a fault is detected, the system must remain in a safe state until a human or a controlled process explicitly clears it. I'd start by defining the fault detection mechanism—typically a comparator with a reference threshold for overcurrent or a thermistor/thermostat for over-temperature. The comparator output feeds a latch, which can be implemented with a simple SCR, a discrete flip-flop, or a dedicated latch IC. The key design considerations are:

1. **Latch topology:** A discrete solution using two transistors (a classic SCR-like latch) or a D-type flip-flop with the fault signal on the clock or set input. The latch must be powered from a rail that remains available even if the main system power is interrupted, so the fault state persists.

2. **Reset path:** The reset must be deliberate. Options include a momentary push-button that gates the latch's reset pin, or a reset signal from a supervisory circuit that only asserts after a specific sequence (e.g., power removed and reapplied, or a separate "clear fault" command from a processor that has been verified healthy). I'd avoid tying the reset directly to the main processor's GPIO without a hardware interlock, because if the processor is the thing that faulted, it can't be trusted to clear the latch.

3. **Fail-safe behavior:** The latch should default to the fault state on power-up. This means the reset input must be pulled to a state that keeps the latch asserted until explicitly cleared. A pull-down on the reset line that must be driven high to clear is a common approach.

4. **Hysteresis and debouncing:** The comparator should have some hysteresis to prevent chatter at the threshold, and the latch itself provides the "memory" so the fault doesn't need to be continuously present.

5. **Verification:** I'd include a test point or a status LED to verify the latch state during manufacturing test, and I'd document the reset procedure clearly for field service.

**Possible follow-ups:**
- How would you ensure the latch itself doesn't become a single point of failure?
- What happens if the reset button is held down while a fault condition is still present?

---

## Q2: How would you approach selecting the inductor for a boost converter that must deliver 5V at 500mA from a single Li-ion cell (3.0–4.2V), where the load has fast current transients?

**Answer:** The inductor is the energy storage element in a boost converter, so its selection directly affects efficiency, output ripple, and transient response. I'd work through this systematically:

1. **Determine the switching frequency:** This is usually set by the converter IC or chosen by me. Higher frequency allows a smaller inductor but increases switching losses and may complicate EMI. For a medical device, I'd likely choose something in the 1–2 MHz range to balance size and efficiency.

2. **Calculate the required inductance:** The minimum inductance is set by the allowable ripple current, typically 20–40% of the peak inductor current. For a boost converter, the inductor current is the input current, which at 3.0V input and 5V/500mA output is roughly 1A (accounting for efficiency). With 30% ripple, that's about 300mA peak-to-peak. Using the standard boost equation, I'd calculate the inductance needed to keep ripple within that bound.

3. **Check saturation current:** This is critical. The inductor must not saturate at the peak current, which includes the DC current plus half the ripple plus margin for transients. I'd select an inductor with a saturation rating at least 20–30% above the worst-case peak current. Saturation causes a sharp drop in inductance, which leads to excessive ripple, reduced efficiency, and potentially damaging current spikes.

4. **Consider DCR and core losses:** For a battery-powered device, efficiency matters. A lower DCR reduces I²R losses, but larger wire means a bigger part. Core losses at the switching frequency also matter, especially for ferrite cores. I'd look at the inductor's efficiency curve at the operating point.

5. **Transient response:** For fast load transients, the inductor's value affects how quickly the converter can deliver energy. A smaller inductor allows faster current slew but increases ripple. I'd check the converter's loop response and ensure the output capacitor can handle the transient until the loop catches up.

6. **Physical size and shielding:** In a medical device, the inductor's magnetic field can couple into nearby analog circuitry. A shielded inductor is often worth the extra cost. I'd also check the component's height and footprint against the mechanical constraints.

**Possible follow-ups:**
- How would you verify the inductor's saturation current rating is accurate, given that datasheet values can be optimistic?
- What happens to the converter's behavior if the inductor saturates during a transient?

---

## Q3: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** This symptom—a low-frequency periodic disturbance that persists with the input shorted and scales with the supply voltage—points to something in the power path or a thermal/mechanical effect rather than the signal path itself. I'd approach this methodically:

1. **Characterize the disturbance precisely:** I'd capture the waveform on an oscilloscope with a long timebase to measure the exact frequency, amplitude, and waveshape. Is it sinusoidal, sawtooth, or irregular? Does the frequency drift? This helps narrow the source.

2. **Check the power supply:** Since the amplitude scales with supply voltage, I'd suspect the supply rail itself. I'd probe the supply pin of the analog front-end with a differential probe (or AC-coupled) to see if the disturbance appears there. A common cause is a switching regulator operating in pulse-skipping or burst mode at light load—the burst frequency can be in the 1–10 Hz range. The regulator's output ripple at that frequency would couple into the analog circuitry through the reference or the amplifier's PSRR.

3. **Look for thermal cycling:** Another possibility is a component that's self-heating and cooling, causing its characteristics to drift. For example, a voltage reference with poor thermal regulation, or a resistor that heats up under load. The thermal time constant of a small component can be in the 0.1–1 second range, matching 1–10 Hz. I'd check the temperature of key components with a thermal camera or by touching them (carefully) to see if any are warm.

4. **Check the reference:** If the disturbance appears on the output with the input shorted, the reference voltage is a prime suspect. I'd probe the reference output directly to see if it's oscillating or drifting. Some references have a "popcorn noise" or microphonic behavior that can appear as low-frequency disturbances.

5. **Eliminate external coupling:** I'd check for mechanical vibration (fans, transformers) or optical coupling (fluorescent lights at 100/120 Hz, but that's higher). A 1–10 Hz disturbance could also be from a ground loop with a slowly varying magnetic field, though that's less common.

6. **Isolate the stage:** I'd disconnect the front-end from the rest of the circuit and power it from a clean bench supply to see if the disturbance persists. This separates a power-source problem from a circuit-internal problem.

**Possible follow-ups:**
- How would you distinguish between a power supply issue and a component-level issue like a faulty reference?
- What if the disturbance only appears when the device is in its enclosure, not on the bench?

---

## Q4: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The key to this design is understanding that the current source's stability directly translates to temperature measurement error. For an RTD, a typical sensitivity is about 0.385 Ω/°C, so a 1 µA error in a 1 mA excitation current causes a voltage error that corresponds to a fraction of a degree. I'd approach it as follows:

1. **Choose the excitation current:** For an RTD, I'd use a current in the 100 µA to 1 mA range. Higher current improves signal-to-noise ratio but causes self-heating, which introduces error. I'd calculate the self-heating based on the RTD's thermal resistance and keep the temperature rise well below 0.01°C.

2. **Select the current source topology:** The classic approach is a Howland current pump or a simple two-transistor current mirror with a precision reference. For medical-grade accuracy, I'd lean toward a dedicated precision current source IC or a discrete design using a precision op-amp and a low-drift resistor. The op-amp forces the voltage across a sense resistor to equal a reference voltage, so the current is Vref/Rsense.

3. **Component selection:** The sense resistor is the critical component—its tolerance and temperature coefficient directly set the current accuracy. I'd use a precision resistor with ±0.1% tolerance and ±5 ppm/°C drift or better. The reference voltage should also be stable; a precision bandgap reference with low drift is essential.

4. **Compensate for lead resistance:** For an RTD, lead resistance adds error. A 4-wire (Kelvin) connection eliminates this by sensing the voltage directly across the RTD. If 4-wire isn't possible, I'd use a 3-wire configuration with a bridge or a current-switching scheme to cancel lead resistance.

5. **Calibration and trimming:** Even with precision components, there will be initial error. I'd include a calibration step in manufacturing—either a software calibration that measures the actual current and compensates in the firmware, or a hardware trim (a potentiometer or a DAC-controlled adjustment) to set the current precisely.

6. **Noise and filtering:** The current source should be low-noise, since noise on the excitation current translates to noise on the measurement. I'd add a low-pass filter on the current source output and ensure the op-amp is a low-noise type.

7. **Self-heating and thermal management:** I'd place the sense resistor and reference away from heat sources and consider the PCB layout to minimize thermal gradients.

**Possible follow-ups:**
- How would you handle the trade-off between self-heating and signal-to-noise ratio?
- What if the sensor is a thermistor with a highly nonlinear response—how would that change your approach?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing your hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a classic safety-critical design disagreement, and the right approach is to focus on the requirements, not personalities. I'd handle it in several steps:

1. **Acknowledge the valid points:** The firmware lead is right that a firmware solution saves board space and cost, and it does allow more flexible threshold adjustment. I'd start by acknowledging those benefits so the discussion is collaborative, not adversarial.

2. **Reframe around the safety requirement:** I'd bring the discussion back to the system's safety requirements. The key question is: what happens if the firmware hangs or the ADC fails? If the over-temperature protection is in firmware, a firmware hang means no protection. That's a single point of failure in a system that's supposed to protect a patient. I'd ask the firmware lead to walk through the failure modes and show how the firmware approach remains safe under all of them.

3. **Propose a layered approach:** Rather than an either/or, I'd suggest a hybrid: keep a simple hardware comparator and latch as the last line of defense, but allow the firmware to adjust the threshold via a DAC or to read the temperature for monitoring and trend analysis. This gives the flexibility the firmware lead wants while maintaining the safety guarantee. The hardware circuit can be very simple—a comparator, a reference, and a latch—so the cost and space impact is minimal.

4. **Use the risk management framework:** In a medical device, this decision should be documented in the risk management file. I'd propose we formally assess both approaches using the ISO 14971 framework—identify hazards, estimate risk, and evaluate whether the risk is acceptable. This removes the decision from personal opinion and puts it on a documented, defensible basis.

5. **Escalate if needed:** If we still can't agree, I'd suggest bringing in a third party—a safety engineer or a regulatory consultant—to provide an independent assessment. In a medical device, the safety case has to be defensible to regulators, so an independent review is valuable.

The key is to keep the discussion focused on patient safety and regulatory requirements, not on who wins the argument. The goal is the safest design that meets the requirements, and if the firmware approach can be made safe with additional measures (e.g., a separate watchdog that's independent of the main processor), I'd be open to exploring that.

**Possible follow-ups:**
- How would you document this decision in the design history file?
- What if the firmware lead insists that the hardware approach is over-engineering and the firmware solution is "good enough" per the risk assessment?