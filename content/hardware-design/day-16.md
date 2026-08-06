# hardware-design — Day 16

## Q1: How would you approach designing a hardware-based latch circuit for a medical device that must maintain a fault condition (e.g., over-temperature or overcurrent) even after the triggering event has cleared, while ensuring the latch can be reset only through a deliberate, safe action?

**Answer:** The core requirement here is a fail-safe memory element that doesn't depend on firmware. A classic approach is a silicon-controlled rectifier (SCR) or a discrete thyristor-like circuit built from a PNP/NPN transistor pair — essentially a positive-feedback latch. When the fault comparator trips, it triggers the latch; once latched, the pair holds itself on via regenerative feedback, so removing the fault doesn't clear it.

For a medical device, I'd add several layers around that basic topology:

- **Independent fault sensing:** The comparator or sensing element must have its own reference and supply path, so a failure in the main processor or its power rail doesn't disable the protection.
- **Reset mechanism:** The reset must be deliberate. Options include a momentary push-button that interrupts the latch's holding current, or requiring the main power to be removed for a defined period. If the device can be reset by cycling power, I'd ensure the latch has a defined power-on state (e.g., a pull-down on the base/gate) so it doesn't latch spuriously during brown-out or power-up transients.
- **Hysteresis:** The fault threshold should have hysteresis so that once latched, the circuit doesn't chatter if the fault condition hovers near the threshold.
- **Fail-safe behavior:** The latch's output should drive a normally-off device (e.g., a low-side MOSFET that must be turned on to enable the load), so if the latch loses power or its output transistor fails open, the load is de-energized.
- **Testability:** I'd include a test point or a way to verify the latch trips at the correct threshold during manufacturing test, without having to actually create the fault condition.

One subtlety: if the latch is holding a motor driver off, you need to consider what happens to inductive energy when the driver is disabled — a freewheeling path or brake resistor may be needed to safely dissipate that energy.

**Possible follow-ups:** How would you verify that the latch circuit itself doesn't create a safety hazard if a component fails short? What if the reset button is pressed while the fault condition is still present — should the latch re-trip immediately?

---

## Q2: How would you approach characterizing the common-mode rejection ratio (CMRR) of a differential amplifier front-end used for biopotential measurements, and what practical factors degrade CMRR that wouldn't show up in a simple bench test?

**Answer:** CMRR is fundamentally a ratio of differential gain to common-mode gain, but in practice, the *effective* CMRR of a complete front-end is almost always worse than the op-amp's datasheet value. I'd approach characterization in stages:

- **Bench measurement:** Apply a common-mode signal (e.g., 1V peak-to-peak at 50/60 Hz) to both inputs tied together, measure the output, and compute CMRR = 20·log(Vin_cm / Vout). I'd sweep frequency because CMRR degrades with frequency due to parasitic capacitance imbalances.
- **Source impedance imbalance:** The real-world killer. If the two electrodes have different source impedances (e.g., 10 kΩ vs 50 kΩ due to skin contact quality), the amplifier's input bias currents and the impedance mismatch convert common-mode voltage into differential voltage. I'd characterize CMRR with *realistic* source impedances connected, not just shorted inputs.
- **Component tolerance:** The resistor network around an instrumentation amplifier (or the discrete diff amp) must be matched. A 0.1% mismatch in one resistor can limit CMRR to around 60 dB. I'd analyze the worst-case CMRR from the resistor tolerance stack-up and consider trimming or using a precision-matched resistor array.
- **Layout parasitics:** Capacitance from each input trace to ground or to the power plane creates a frequency-dependent imbalance. I'd check the layout for symmetric routing of the input pair and guard traces.
- **System-level test:** The most meaningful test is with the actual patient cable and electrodes, because cable capacitance and electrode impedance are part of the system. I'd inject a common-mode voltage through the cable and measure the residual differential signal at the ADC.

The key insight is that datasheet CMRR is a *component* specification; the *system* CMRR is what matters for the measurement, and it's dominated by the surrounding circuit and mechanical design.

**Possible follow-ups:** How would you improve CMRR if the source impedance mismatch is unavoidable? What role does a right-leg drive (RLD) circuit play in improving effective CMRR?

---

## Q3: How would you approach selecting the switching frequency for a flyback converter used in a medical device's isolated power supply, where you need to balance transformer size, EMI, and efficiency?

**Answer:** The switching frequency is a central trade-off in flyback design, and I'd approach it by working through the constraints in order:

- **Isolation and creepage:** Medical devices often require reinforced insulation, which sets minimum physical distances across the isolation barrier. This constrains the transformer's minimum size regardless of frequency, so I'd first check whether the frequency choice even allows a transformer that meets the safety spacing.
- **Transformer core loss vs. copper loss:** Higher frequency allows a smaller core (lower volume), but core loss increases with frequency. At some point, the core loss dominates and efficiency drops. I'd estimate the loss split at candidate frequencies (e.g., 65 kHz, 100 kHz, 200 kHz) using the core material's loss curves.
- **EMI and the quasi-resonant valley:** Flyback converters are notorious for ringing at the drain node when the MOSFET turns off. Operating in quasi-resonant (valley-switching) mode reduces turn-on losses and some EMI, but the frequency varies with load. I'd consider whether the design can tolerate frequency modulation or whether a fixed-frequency design with good snubbing is more predictable for EMI compliance.
- **Practical frequency bands:** I'd avoid frequencies that fall in sensitive bands for the device's own circuitry. For example, if the device has a high-resolution ADC with a modulator at 2.5 MHz, I'd avoid switching frequencies that create beat frequencies in the ADC's passband. Similarly, I'd avoid the AM radio band (530–1700 kHz) and be careful with harmonics near any wireless communication frequencies.
- **Controller availability and cost:** The controller IC's minimum on-time, maximum duty cycle, and propagation delays set practical limits. A very high frequency (e.g., >1 MHz) may require a controller with fast comparators and careful layout, increasing cost and risk.

I'd also consider whether the design can use a fixed frequency with frequency jittering (spreading the spectrum) to help with EMI, versus a variable-frequency quasi-resonant design that's more efficient but harder to filter predictably.

**Possible follow-ups:** How would you handle the trade-off if the optimal frequency for efficiency creates an EMI problem at a specific harmonic? What snubber design would you use to damp the drain ringing?

---

## Q4: How would you approach designing a hardware-based interlock for a medical device that must prevent motor activation unless a sensor confirms a specific mechanical condition, and the interlock must be verifiable as fail-safe?

**Answer:** The design goal is that the motor can only run when the sensor confirms the safe condition, and any single failure in the interlock path must result in the motor being disabled — not enabled. I'd structure the design around a few principles:

- **Normally-open vs. normally-closed logic:** I'd design the interlock so that the *absence* of a valid signal disables the motor. For example, if the sensor is a Hall effect switch that outputs a logic high when the mechanical condition is met, I'd use that signal to enable a gate that drives the motor. If the sensor fails (output floats or goes low), the gate closes and the motor stops. This is the "fail-safe" direction: the safe state is the default state.
- **Redundancy and diversity:** For a critical interlock, I'd consider two independent sensors (e.g., a magnetic switch and an optical sensor) with their outputs combined in an AND configuration — the motor only runs if *both* confirm the condition. This protects against a single sensor failing in a way that falsely indicates the safe state.
- **Self-test capability:** A purely passive interlock can fail silently. I'd add a self-test path: the firmware (or a test circuit) can periodically assert a test signal that should *not* enable the motor — for example, by driving the sensor's output low and verifying the interlock blocks the motor. This catches stuck-high failures.
- **Output stage design:** The interlock should control the motor driver's enable pin, not just the PWM signal. If the interlock uses a series MOSFET in the motor's power path, a failure in the interlock logic (e.g., a shorted transistor) could bypass the interlock. I'd use a configuration where the motor's power path requires *both* the interlock signal and the firmware's PWM signal to be present — a two-key system.
- **Verification:** I'd document a failure modes and effects analysis (FMEA) for the interlock path, identifying each component's failure mode and whether it leads to a safe or unsafe state. This is where the "verifiable as fail-safe" requirement is actually proven — not by testing, but by analysis.

The key design principle is that the interlock must be *in* the power path, not just in the control path. If the interlock only gates a logic signal that the firmware reads, a firmware bug could bypass it entirely.

**Possible follow-ups:** How would you test the interlock to prove it fails safe? What if the sensor's output is analog (e.g., a potentiometer) rather than digital — how would you set the threshold?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the manufacturing engineer proposes replacing your specified precision voltage reference (a dedicated reference IC with ±0.05% initial accuracy and 5 ppm/°C drift) with the microcontroller's internal reference, arguing that the internal reference is "within the ADC's overall accuracy budget" and will save cost and board space. You believe the internal reference's temperature drift and initial tolerance are marginal for the measurement requirements, and the datasheet specifications are not guaranteed over the full operating range. How would you handle this disagreement?

**Answer:** I'd approach this as a data-driven engineering disagreement, not a matter of opinion or authority. My first step would be to frame the question precisely: what accuracy does the measurement actually require at the system level, and what error budget is allocated to the voltage reference?

I'd then gather the relevant data:

- **Datasheet comparison:** Pull the internal reference's specifications — initial tolerance, temperature coefficient, long-term drift, and noise — and compare them against the dedicated reference IC's specs. The key question is whether the internal reference's *worst-case* error over the full operating temperature range (0–50°C for a medical device) fits within the allocated error budget.
- **System-level analysis:** The ADC's accuracy is a combination of reference error, ADC nonlinearity, gain error, and noise. If the internal reference's drift alone consumes most of the error budget, there's no margin left for other error sources. I'd do a simple worst-case error calculation and present it.
- **Test data:** If the manufacturing engineer's claim is that the internal reference is "good enough in practice," I'd ask whether they have test data from the specific microcontroller lot we're using. Datasheet typical values are not guarantees — I'd want to see the distribution across temperature and units.

If the data shows the internal reference is genuinely marginal, I'd propose a compromise: use the internal reference for the prototype phase to gather real data, but keep the PCB footprint for the external reference as a populated option. This lets us make a data-driven decision rather than a speculative one. If the data confirms the internal reference is insufficient, we've already validated the concern; if it's adequate, we save the cost.

I'd also acknowledge the manufacturing engineer's valid point about cost and board space — those are real constraints. The discussion should be about *risk*, not about winning an argument. If we can't resolve it with data, I'd escalate to a formal risk assessment (e.g., a DFMEA entry) so the decision is documented with its rationale.

**Possible follow-ups:** What if the manufacturing engineer insists that the internal reference is adequate based on their experience with other products? How would you handle the situation if the project schedule doesn't allow time for a prototype comparison?