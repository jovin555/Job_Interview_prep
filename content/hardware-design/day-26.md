# hardware-design — Day 26

## Q1: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The core requirement here is that the latch must be fail-safe and unambiguous — once a fault is declared, the system must remain in a safe state until a human or supervisory controller explicitly clears it. I'd start by defining the fault threshold and the response action (e.g., shutting down a motor driver or disconnecting a load), then choose a latching topology.

A common approach is a comparator feeding a latching circuit — either a discrete SCR-like structure or a comparator with positive feedback (hysteresis) that holds the output state. The key design decision is the reset mechanism. I'd use a separate reset line that requires a deliberate action: either a physical push-button, a signal from a supervisory processor that has been verified healthy, or a power-cycle that requires the user to power down and back up. The reset path should be independent of the fault detection path so a fault condition can't accidentally clear itself.

For medical devices, I'd also consider adding a visual or electrical indicator that the latch is set, and I'd ensure the latch's output is used in a fail-safe manner — for example, the latched signal should actively disable the hazardous output rather than merely flagging it. I'd also verify the latch's behavior under power-up and power-down transients, since a latch that sets spuriously during a brown-out could cause nuisance shutdowns, while one that fails to set during a fault could be dangerous.

**Possible follow-ups:**
- How would you test the latch to verify it holds the fault state indefinitely and resets only under the intended conditions?
- What failure modes of the latch itself would you analyze in an FMEA, and how would you mitigate them?

---

## Q2: How would you approach selecting the inductor for a boost converter that must deliver 5V at 500mA from a single Li-ion cell (3.0–4.2V), where the load has fast current transients?

**Answer:** The inductor selection starts with the converter's switching frequency and the allowable ripple current. For a boost converter, the inductor is the energy storage element, so its value directly affects both the ripple and the converter's ability to respond to transients. I'd typically target a ripple current of 20–40% of the maximum input current — for a 5V/500mA output from a 3.0V input, the input current is roughly 1A at the worst-case low battery voltage, so I'd aim for a ripple of 200–400mA peak-to-peak.

The inductance value comes from the standard boost equation: L = (V_in × D) / (f_sw × ΔI_L), where D is the duty cycle. With a 1MHz switching frequency and 3.0V input, that gives an inductance in the range of 2.2–4.7µH. I'd then check the saturation current rating — the inductor must handle the peak current (average input current plus half the ripple) without saturating, and I'd add margin for the transient case where the load steps from low to high current. A fast load transient will cause the inductor current to ramp up over several switching cycles, so the inductor's saturation current should be rated for the worst-case peak, not just the steady-state value.

I'd also consider the inductor's DC resistance (DCR) for efficiency — a lower DCR improves efficiency but usually means a larger package. For a medical device, I'd also check the inductor's self-resonant frequency to ensure it's well above the switching frequency, and I'd review the radiated EMI characteristics, since a poorly shielded inductor can couple noise into nearby analog circuitry.

**Possible follow-ups:**
- How would the inductor selection change if the load transient required the output voltage to stay within ±3% during a 200mA step?
- What would you check on the bench to verify the inductor choice is adequate before committing to the design?

---

## Q3: Walk me through how you would debug a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage.

**Answer:** A low-frequency periodic disturbance that persists with the input shorted points to something internal to the circuit rather than the signal source. The fact that it varies with the supply voltage is a strong clue — it suggests the disturbance is coupled through the power supply path or is caused by a supply-dependent mechanism.

My first step would be to characterize the disturbance precisely: measure its exact frequency, amplitude, and waveform shape, and determine whether it's truly periodic or drifting. I'd then check whether the frequency correlates with any known system clock, switching regulator frequency, or thermal time constant. A 1–10 Hz disturbance is too slow for most switching regulators (which run at hundreds of kHz), so I'd suspect either a thermal oscillation, a bias circuit instability, or a low-frequency reference issue.

Next, I'd isolate the stages. I'd probe the power supply rails at the analog front-end's supply pins with a scope set to AC coupling and high sensitivity — a supply that looks clean at the regulator output may have significant ripple or noise at the load due to layout inductance. I'd also check the voltage reference: a reference with marginal stability can oscillate at low frequency, especially if its output capacitor is incorrectly valued or placed. I'd also look at the bias network — a high-value resistor feeding a capacitor can form a low-frequency pole that interacts with the op-amp's feedback loop.

If the disturbance varies with supply voltage, I'd also suspect a thermal feedback loop: a component dissipating power heats up, changes its characteristics (e.g., offset voltage drift), and the resulting change in current draw alters the local supply voltage, which feeds back. This can create a low-frequency oscillation. I'd check component temperatures with a thermal camera and look for any component that's dissipating more than expected.

**Possible follow-ups:**
- How would you distinguish between a thermal oscillation and an electrical low-frequency oscillation in this circuit?
- What specific measurements would you take to confirm the disturbance is supply-coupled rather than generated within the amplifier itself?

---

## Q4: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The first decision is the sensor type and excitation scheme. For an RTD, a common approach is a precision current source that excites the sensor and measures the resulting voltage. The accuracy requirement of ±0.1°C translates directly into a current accuracy requirement — for a 100Ω PT100 RTD with a temperature coefficient of about 0.385 Ω/°C, a 1mA excitation current produces a signal of about 0.385 mV/°C, so the current source must be stable to within roughly 0.1% to achieve 0.1°C accuracy, plus the voltage measurement must be correspondingly precise.

I'd start with a precision reference voltage and a precision op-amp configured as a Howland current source or a simpler two-op-amp topology. The key parameters are the reference voltage accuracy and temperature drift, the op-amp's offset voltage and drift, and the matching of the resistors that set the current. For a 1mA current source, I'd use a 2.5V reference and a 2.5kΩ sense resistor — the resistor's tolerance and temperature coefficient directly set the current accuracy, so I'd choose a precision resistor with ±0.1% tolerance and a low TCR (e.g., 10 ppm/°C or better).

I'd also consider the compliance voltage — the op-amp must be able to drive the RTD's voltage drop plus the sense resistor's drop while staying within its output range. For a 3.3V supply and a 100Ω RTD, the total drop is about 2.6V, which is feasible but leaves little headroom, so I might use a higher supply rail or a lower excitation current. A lower current (e.g., 100µA) reduces self-heating in the RTD, which is important for accuracy — self-heating error is proportional to I²R, so reducing current by 10× reduces self-heating by 100×.

Finally, I'd design the measurement chain: a differential amplifier to sense the RTD voltage, with high CMRR and low offset drift, and I'd use a ratiometric measurement if possible — using the same reference for both the current source and the ADC reference eliminates reference drift as an error source.

**Possible follow-ups:**
- How would you compensate for the RTD's self-heating error, and how would you verify the compensation is effective?
- What would you do if the op-amp's offset voltage drift was the dominant error source, and you couldn't find a better op-amp?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing the hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** I'd start by acknowledging the legitimate engineering merits of the firmware proposal — it does save board space, reduces cost, and offers flexibility in threshold adjustment. Then I'd frame the discussion around the safety requirements rather than personal preference. The key question isn't which approach is cheaper or more flexible; it's whether the firmware approach can meet the safety requirements for a medical device.

I'd walk through the specific failure scenarios: if the firmware hangs due to a stack overflow, a deadlock, or a memory corruption, the over-temperature protection would be unavailable. If the ADC fails — which is a real possibility given that ADCs can latch up or produce erroneous readings — the firmware would be monitoring a faulty signal. In a medical device, the protection must be independent of the main processing path; this is a fundamental principle of safety-critical design. I'd reference the relevant standards — IEC 60601 requires that protective functions be reliable and fail-safe, and a single-point failure in the firmware or ADC must not defeat the protection.

I'd also propose a middle ground: if the firmware lead's concerns are about cost and flexibility, we could keep the hardware comparator but make the threshold adjustable via a digital potentiometer or a resistor divider controlled by a GPIO. This gives the firmware team the flexibility they want while maintaining the independence of the protection path. If the firmware lead still disagrees, I'd suggest we do a formal risk analysis — an FMEA or a hazard analysis — to document the failure modes and their severity, and let the data drive the decision. In a medical device, the safety argument should win, but it should win on evidence, not on authority.

**Possible follow-ups:**
- How would you respond if the firmware lead argues that the firmware can be written to be "safe" through watchdog timers and defensive programming?
- What specific IEC 60601 clauses or risk management principles would you cite to support your position?