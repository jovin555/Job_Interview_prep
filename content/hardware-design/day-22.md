# hardware-design — Day 22

## Q1: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The core requirement here is that the latch must be *fail-safe* — once a fault is detected, the system must stay in a safe state until a human or a deliberate supervisory action clears it. I'd start by defining the fault detection and the latching mechanism separately.

For the detection side, I'd use a comparator with a small amount of hysteresis to avoid chatter at the threshold. The comparator's output would drive a latching element — typically a thyristor-style SCR crowbar, a latching relay, or a discrete latch built from a transistor pair or a D-type flip-flop. For medical devices, I'd lean toward a discrete or logic-based latch rather than relying on firmware, because the latch must work even if the processor hangs.

The key design decision is the reset path. The reset must be *deliberate* — for example, requiring the user to remove power and then reapply it, or to press a physical reset button that's mechanically interlocked with the fault condition. I would not allow a software reset to clear the latch, because software could be in an unknown state. If a reset button is used, I'd debounce it and require it to be held for a minimum duration to prevent accidental clears.

I'd also consider the power source for the latch. If the latch is powered from the same rail that's being protected, a crowbar-style latch will collapse the rail and hold it off — which is inherently fail-safe. If the latch is powered from a separate rail, I need to ensure that rail is always available when the device is powered.

Finally, I'd verify the latch's behavior under fault conditions: what happens if the fault and the reset occur simultaneously? The design should prioritize the fault — the latch should win. I'd also check the latch's state on power-up. It should default to a safe state (fault asserted) until the system is explicitly initialized.

**Possible follow-ups:**
- How would you test the latch to prove it holds the fault state through a power glitch or brown-out?
- What are the trade-offs between a thyristor crowbar and a discrete transistor latch for this application?

---

## Q2: How would you approach selecting the switching frequency for a buck converter in a medical device that must balance efficiency, output ripple, and EMI compliance?

**Answer:** The switching frequency is a central trade-off that affects nearly every other component in the converter. I'd approach it by first establishing the constraints from the system level, then narrowing down the frequency range, and finally validating with measurements.

The lower bound on frequency is typically set by the size of the passive components. At lower frequencies, the inductor and output capacitors must be larger to store the same energy and maintain the same ripple. For a compact medical device, that's often a practical limit. The upper bound is set by switching losses in the MOSFETs and the controller's capability, as well as by EMI — higher frequencies radiate more easily and are harder to filter.

For a medical device, EMI compliance is usually the dominant constraint. I'd look at the frequency bands where the device must meet radiated and conducted emissions limits. If the switching frequency or its harmonics fall into a particularly sensitive band (e.g., a band used by the device's own wireless radio), I'd either shift the frequency or design the filtering to attenuate those specific harmonics.

Efficiency is the next consideration. I'd estimate the switching losses (gate drive, Coss, body diode) and conduction losses at the candidate frequencies. For a device that spends most of its time in standby, I might choose a lower frequency to reduce switching losses, even if it means larger passives. For a device with high continuous load, a mid-range frequency (400 kHz–1 MHz) often balances efficiency and size.

I'd also consider the control loop. The crossover frequency of the feedback loop is typically 1/10th to 1/5th of the switching frequency. If I need a fast transient response (e.g., for a motor actuation burst), I need a high enough switching frequency to support a fast loop.

Finally, I'd prototype with the chosen frequency and measure: output ripple, efficiency across the load range, and a pre-compliance EMI scan. If the EMI scan shows margin issues, I'd adjust the gate drive strength, snubber, or the switching frequency slightly to move the harmonics out of the problem band.

**Possible follow-ups:**
- How would you handle a situation where the optimal frequency for efficiency conflicts with the frequency that gives clean EMI?
- What role does the gate drive resistance play in the EMI vs. efficiency trade-off?

---

## Q3: How would you approach debugging a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage?

**Answer:** This symptom — a low-frequency periodic disturbance that's present with the input shorted and that tracks the supply voltage — points me toward a few specific classes of problems. I'd start by confirming the disturbance is real and not a measurement artifact, then work through the likely causes systematically.

First, I'd verify the measurement setup. A 1–10 Hz disturbance can be picked up from the bench power supply's own ripple, from a ground loop in the test setup, or from thermal drift in the probe. I'd power the circuit from a battery or a clean linear supply and re-measure. I'd also check whether the disturbance is present on the supply rail itself — if the supply has a low-frequency ripple component, that's a clue.

If the disturbance tracks the supply voltage, I'd suspect inadequate power supply rejection in the analog front-end. The op-amp's PSRR is typically specified at DC and at higher frequencies, but it can degrade at low frequencies due to the internal bias circuitry. I'd check the PSRR curve in the datasheet at 1–10 Hz. If the PSRR is poor there, I'd add a low-frequency filter on the supply rail — a larger bulk capacitor or an RC filter — to attenuate the ripple before it reaches the op-amp.

Another common cause is thermal cycling. If the circuit has a component that self-heats (e.g., a voltage regulator or a resistor dissipating significant power), the temperature change can cause a low-frequency drift in the op-amp's offset voltage. I'd check the temperature of the components with a thermal camera or by touching them (carefully) to see if the disturbance frequency correlates with a thermal time constant.

I'd also look at the reference voltage. If the ADC reference is derived from the supply rail, any low-frequency ripple on the supply will appear as a disturbance in the conversion results. I'd verify the reference is stable and well-filtered.

Finally, I'd check for a ground loop between the analog ground and the power supply ground. A low-frequency current flowing through the ground path can create a voltage difference that appears at the op-amp's input. I'd use a differential measurement to check the voltage between the analog ground and the supply ground.

**Possible follow-ups:**
- How would you distinguish between a power supply ripple problem and a thermal drift problem?
- What specific measurements would you take to isolate the disturbance to the op-amp vs. the reference vs. the ground path?

---

## Q4: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The accuracy requirement of ±0.1°C drives everything in this design. I'd start by working backward from the temperature accuracy to the electrical requirements, then design the current source and the measurement chain to meet those requirements with margin.

For an RTD (e.g., a PT100), the sensitivity is approximately 0.385 Ω/°C. A ±0.1°C error corresponds to ±0.0385 Ω. If I drive the RTD with a 1 mA current source, that's ±38.5 µV of voltage error. The current source's stability directly translates to measurement error — a 1% current error would cause roughly 2.5°C of error, so I need the current to be stable to better than 0.04% over temperature and time.

I'd use a precision reference and a matched resistor to set the current. The key is to use a resistor with a low temperature coefficient (e.g., ±5 ppm/°C or better) and a reference with similar or better stability. I'd also consider a Kelvin (4-wire) connection to the RTD to eliminate lead resistance errors — at 1 mA, even 1 Ω of lead resistance would cause a 0.26°C error.

For the current source topology, I'd use a Howland current pump or a simple op-amp + transistor current source. The Howland pump is attractive because it can source current from a single supply and the output impedance is high, but it requires matched resistors to maintain that high impedance. I'd use a precision op-amp with low offset voltage and low drift (e.g., <10 µV/°C) to avoid introducing errors.

I'd also consider the self-heating of the RTD. At 1 mA, a PT100 dissipates 0.1 mW, which causes a small temperature rise — typically negligible, but I'd check the RTD's self-heating coefficient. If self-heating is a concern, I could reduce the current to 100 µA, but then the voltage signal is smaller and noise becomes more significant.

For the measurement chain, I'd use a differential amplifier or an instrumentation amplifier to measure the RTD voltage, and a precision ADC (e.g., 16-bit or higher) to digitize it. I'd also measure the reference voltage or use a ratiometric measurement — where the ADC reference is derived from the same current source — to cancel out current source drift.

Finally, I'd calibrate the system at manufacturing time. Even with precision components, there will be residual offset and gain errors. A two-point calibration (at 0°C and 50°C) would allow me to correct for these errors in firmware, bringing the system well within the ±0.1°C requirement.

**Possible follow-ups:**
- How would you decide between a ratiometric measurement and an absolute measurement with a separate reference?
- What would you do if the self-heating of the RTD at 1 mA caused a measurable error?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing your hardware-based over-temperature protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors temperature via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** I'd approach this as a technical disagreement that needs to be resolved through data and risk analysis, not through authority or stubbornness. The first thing I'd do is acknowledge the firmware lead's valid points — a firmware-based solution does save board space and offers flexibility. Then I'd reframe the discussion around the safety requirements.

I'd start by asking the firmware lead to walk through the failure scenarios with me. Specifically, I'd ask: "What happens if the firmware hangs while the motor is running and the temperature is rising? What happens if the ADC's reference drifts and the temperature reading is falsely low? What happens if the GPIO is stuck high?" These are not hypothetical edge cases — they're the exact scenarios the protection circuit is designed to handle.

I'd then reference the relevant safety standard. For a medical device, the protection must be *independent* and *fail-safe*. Independence means the protection shouldn't rely on the same processor that's controlling the motor — if the processor hangs, the protection must still work. A hardware comparator and latch are independent by design. A firmware solution is not.

I'd also bring up the concept of "common cause failure." If the firmware has a bug that causes it to hang, that same bug could potentially affect the temperature monitoring code. Even if the monitoring code is in a separate task, a watchdog could reset the system — but the reset time might be too long to prevent damage.

Rather than just saying "no," I'd propose a compromise: keep the hardware comparator as the primary protection, but add a firmware-based monitoring as a secondary layer. The firmware could provide the flexible threshold adjustment the firmware lead wants, while the hardware provides the fail-safe backstop. This addresses the firmware lead's concerns about flexibility while maintaining safety.

If the firmware lead still disagrees, I'd escalate to a formal risk assessment — a DFMEA or a hazard analysis — where the failure modes are documented and reviewed by the team. This removes the decision from personal opinion and puts it into a structured process that the team can agree on.

**Possible follow-ups:**
- How would you handle the situation if the firmware lead's proposal was supported by the project manager, who is concerned about the schedule?
- What specific failure modes would you document in the DFMEA to justify keeping the hardware protection?