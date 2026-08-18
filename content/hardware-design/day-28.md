# hardware-design — Day 28

## Q1: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** The first step is to understand the sensor's transfer function and the required excitation accuracy. For an RTD, a common approach is a ratiometric design where the same reference voltage drives both the current source and the ADC reference — this cancels first-order errors from reference drift. For a thermistor, the nonlinearity must be characterized and either linearized in analog hardware or handled in firmware with a lookup table or polynomial.

For the current source itself, I'd use a Howland current pump or a precision op-amp with a sense resistor in the feedback loop. The key parameters are the sense resistor's tolerance and temperature coefficient — a ±0.1% tolerance with 10–25 ppm/°C drift is typically needed. The op-amp's offset voltage and drift matter too, since they directly contribute to current error. I'd also consider the self-heating of the sensor: the excitation current must be low enough (typically 100 µA–1 mA for RTDs) that I²R heating doesn't introduce more than a fraction of the allowed error.

The excitation current's absolute accuracy matters less than its stability over temperature and time, because a one-point calibration at manufacturing can correct for initial tolerance. What you can't easily correct is drift and temperature coefficient, so those are the specifications to focus on. I'd also include a means to verify the current source during production test — either a test point across the sense resistor or a calibration mode in firmware.

**Possible follow-ups:** How would you choose between a constant current and constant voltage excitation for this application? What error budget would you allocate to each stage in the signal chain?

---

## Q2: Walk me through how you would debug a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage.

**Answer:** A low-frequency periodic disturbance that persists with the input shorted points to something in the power path, reference path, or ground system rather than the signal path itself. The fact that amplitude scales with supply voltage is a strong clue — it suggests the disturbance is coupled through the supply or reference rather than being a true input-referred signal.

My first step would be to look at the power supply with a scope in AC-coupled mode, using a long timebase to capture the 1–10 Hz period. I'd check whether the disturbance exists on the supply rail itself — this could be a control loop oscillation in a regulator, possibly interacting with a downstream load that cycles at that rate. A common cause is a regulator with marginal phase margin that oscillates at low frequency when the load current changes, or a thermal loop in the regulator's protection circuitry.

Next, I'd check the voltage reference. Some references have a "popcorn noise" or micro-power instability that appears at low frequencies, and this can be exacerbated by supply ripple. I'd also examine the ground system — a ground loop between the analog front-end and the power supply return can pick up low-frequency currents from other parts of the system.

If the supply and reference look clean, I'd suspect thermal effects: a component (possibly an op-amp or reference) that's self-heating and causing a slow drift cycle, or a mechanical issue like a loose connection that modulates contact resistance. I'd use a thermal camera or freeze spray to identify any component that's cycling in temperature.

The systematic approach is to isolate stages: power the analog front-end from a clean bench supply, bypass the on-board regulator, and see if the disturbance disappears. Then substitute the reference with an external precision source. This binary search narrows the problem quickly.

**Possible follow-ups:** What if the disturbance only appears when the device is battery-powered but not when connected to a bench supply? How would you distinguish between a power supply issue and a reference issue?

---

## Q3: How would you approach selecting the inductor for a boost converter that must deliver 5V at 500mA from a single Li-ion cell (3.0–4.2V), where the load has fast current transients?

**Answer:** The inductor selection starts with the converter's switching frequency and the allowable ripple current. A common rule of thumb is to target 20–40% of the maximum load current as the peak-to-peak ripple. For 500 mA, that's 100–200 mA of ripple. The inductance value is then calculated from the standard boost converter equation: L = V_in × (V_out − V_in) / (f_sw × ΔI_L × V_out), evaluated at the worst-case condition — typically the lowest input voltage (3.0V), since that's when the duty cycle and ripple are highest.

Beyond the inductance value, the critical parameters are saturation current and DC resistance. The saturation current must be rated for the peak current — which includes the ripple — plus margin for temperature and component tolerance. I'd typically derate by at least 20–30%. The DCR affects efficiency and, more importantly for a load with fast transients, the converter's ability to respond to current steps. A higher DCR adds a zero in the control loop that can complicate compensation.

For fast load transients, I'd also consider the inductor's core material. A shielded ferrite core is preferred for EMI, but the core's permeability behavior under DC bias matters — some cores lose inductance significantly as current increases, which degrades transient response. I'd check the inductance vs. current curve in the datasheet, not just the saturation rating.

Finally, I'd verify the inductor's self-resonant frequency is well above the switching frequency and its harmonics, and check the thermal rating — the copper and core losses at the operating point must keep the temperature rise within limits, especially in a sealed medical device enclosure.

**Possible follow-ups:** How would the inductor choice change if the load transients were very fast (microseconds) versus slow (milliseconds)? What if the converter needed to operate in discontinuous conduction mode at light load?

---

## Q4: How would you approach designing a hardware-based overcurrent protection circuit for a motor driver in a medical device, where the protection must be independent of the main microcontroller and must respond within microseconds?

**Answer:** The core requirement is that protection must work even if the firmware hangs or the main processor fails, so the circuit needs a dedicated analog path: a sense element, a comparator, and a latch or direct shutdown mechanism.

For current sensing, I'd use a low-value sense resistor in the motor return path or the low-side of the H-bridge, with a Kelvin connection to the comparator's input to avoid errors from PCB trace resistance. The sense voltage is compared against a precision reference — a resistor divider from a reference voltage, or a dedicated comparator with an internal reference. The threshold accuracy depends on the sense resistor tolerance and the comparator's offset voltage; for a ±5% threshold accuracy, I'd need a 1% or better sense resistor and a comparator with low offset.

The response time budget includes the sense resistor's time constant (negligible), the comparator's propagation delay (typically 20–100 ns for a fast comparator), and the shutdown path to the motor driver's enable pin. The total should be well under the microsecond requirement. I'd use a comparator with push-pull output and ensure the motor driver's enable input has a fast response — some drivers have internal filtering that adds delay.

A key design decision is whether to use a latch or direct shutdown. A latch maintains the fault state even after the overcurrent condition clears, which is safer for a medical device — the motor stays off until a deliberate reset. The latch should be resettable only through a safe action, such as power cycling or a dedicated reset signal that requires a specific sequence. I'd also add a small amount of hysteresis to the comparator to prevent chatter at the threshold.

For fail-safe behavior, I'd consider the failure modes of the protection circuit itself: if the sense resistor opens, the comparator should default to the fault state; if the comparator loses power, the motor driver should be disabled. This might mean using a pull-down on the driver's enable line so that any loss of the protection circuit's output results in shutdown.

**Possible follow-ups:** How would you test this protection circuit to verify it meets the response time requirement? What failure modes of the protection circuit itself would you analyze in a DFMEA?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing your hardware-based overcurrent protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors current via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** I'd start by acknowledging the legitimate merits of the firmware proposal — it does save board space, reduces cost, and offers flexibility in threshold adjustment. Those are real benefits, and dismissing them outright would be counterproductive. But the fundamental issue is that the protection requirement is safety-critical, and the design must be robust to single-point failures.

I'd frame the discussion around the safety requirements rather than personal preference. The key question is: what happens if the firmware hangs or the ADC fails? In a firmware-based approach, both are single points of failure that defeat the protection. The hardware approach provides independence — it works regardless of the state of the main processor. This isn't just a design preference; it's a fundamental principle in medical device safety, where independent protection paths are required to prevent single faults from leading to hazardous situations.

I'd also raise the timing question: the ADC sampling rate and firmware execution time introduce latency that may not meet the response time requirement. A comparator responds in microseconds; a firmware loop that samples, processes, and asserts a GPIO might take milliseconds, depending on the ADC conversion time and the firmware's scheduling. During that window, the motor could deliver enough energy to cause harm.

Rather than simply rejecting the proposal, I'd offer a compromise: perhaps the firmware-based approach could be used as a secondary, supplementary protection — for example, to provide adjustable thresholds or to log fault events — while the hardware circuit remains as the primary, independent safety path. This gives the firmware team some of what they want while preserving the safety-critical function.

If the disagreement persists, I'd suggest we bring in the safety or regulatory engineering team to review the requirements and help make a data-driven decision. The goal is to reach consensus based on the safety case, not on who has the stronger opinion. I'd also document the discussion and the rationale for the final decision in the design history file, since that's part of good engineering practice for medical devices.

**Possible follow-ups:** What if the firmware lead argues that the hardware circuit itself can fail, and the firmware approach is actually more reliable because it can self-test? How would you respond? How would you structure a compromise that satisfies both safety requirements and the firmware team's concerns?