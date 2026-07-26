# hardware-design — Day 5

## Q1: How would you approach designing a gate drive circuit for a high-side N-channel MOSFET used in a battery-powered load switch, where the battery voltage ranges from 3.0V to 4.2V and the load can draw up to 3A?

**Answer:** The fundamental challenge here is that an N-channel MOSFET requires a gate-to-source voltage (Vgs) above its threshold to fully enhance, but in a high-side configuration the source sits at the battery voltage when the switch is on. With a 3.0V battery, the gate would need to be driven to perhaps 5-6V to achieve low Rds(on) — higher than the battery itself can provide. I'd approach this with a charge pump or bootstrap circuit.

For a simple load switch, a charge pump IC designed for this purpose is the most straightforward solution. These devices integrate a flying capacitor topology to generate a gate drive voltage of roughly 2x the input, then regulate it to a safe level (typically 5-10V). Key parameters to check: the charge pump's startup time (important if the load switch must engage quickly), its quiescent current (critical for battery life), and whether it can supply enough gate charge to switch the MOSFET on and off at the required rate.

If the application requires very low standby current, I might consider a different topology — perhaps a P-channel MOSFET instead, which avoids the gate drive voltage issue entirely. The trade-off is that P-channel MOSFETs generally have higher Rds(on) for the same die size and cost more. For a 3A load, the voltage drop across a P-channel might be acceptable if the battery voltage is high enough, but at 3.0V near end-of-discharge, every millivolt matters.

**Possible follow-ups:** How would you calculate the required gate drive current for a given switching frequency? What happens if the charge pump output voltage exceeds the MOSFET's maximum Vgs rating?

---

## Q2: Walk me through how you would select a Schottky diode for a boost converter's output rectification stage, given a 5V output at 500mA with a switching frequency of 1MHz.

**Answer:** In a boost converter, the Schottky diode serves as the rectifying element that conducts during the off-time of the switching MOSFET. At 1MHz, the diode's switching speed becomes critical — a standard rectifier diode would have excessive reverse recovery losses. Schottky diodes are the natural choice because they're majority-carrier devices with negligible reverse recovery charge.

I'd start with the voltage rating: the diode must block the output voltage plus some margin. For a 5V output, I'd look for a 20V or 30V rated part — higher voltage ratings come with higher forward voltage drop (Vf) and higher junction capacitance, so I wouldn't overspec unnecessarily.

The forward current rating should handle the peak inductor current, not just the average output current. In a boost converter operating in continuous conduction mode, the peak current can be 1.5-2x the average input current. For 500mA output at 5V from a 3.7V nominal battery, the average input current is roughly (5V × 0.5A) / (3.7V × efficiency) ≈ 750mA, so peak current might be 1-1.5A. I'd select a diode rated for at least 2A.

The critical parameter at 1MHz is the diode's junction capacitance (Cj). High capacitance causes switching losses as the diode's junction charges and discharges each cycle. I'd look for a Schottky with Cj under 50pF at the reverse voltage. Forward voltage drop is also important for efficiency — lower Vf means less conduction loss, but often comes with higher leakage current at elevated temperatures. In a medical device, I'd check the leakage at the maximum operating temperature (perhaps 60°C ambient) to ensure it doesn't cause thermal runaway or reduce battery life.

**Possible follow-ups:** How would the diode selection change if the converter operated in discontinuous conduction mode? What failure mode would you worry about if the diode overheats?

---

## Q3: How would you approach designing a comparator-based overcurrent detection circuit for a medical device's motor driver output, where the threshold must be accurate to within ±5% over temperature and the response time must be under 10µs?

**Answer:** This requires careful attention to the comparator's propagation delay, input offset voltage, and the sensing element's accuracy. I'd start by selecting the current sensing method. A low-side sense resistor in the return path is simplest, but it creates a ground offset that can cause issues if other circuits share that ground. A high-side sense resistor with a differential amplifier avoids ground disturbance but adds complexity. For a motor driver, I'd lean toward low-side sensing because the motor current is already noisy and the ground offset can be managed with proper layout.

The sense resistor value is a trade-off: larger values give a higher voltage drop for better signal-to-noise ratio but waste power as heat. For a motor drawing perhaps 1-2A, a 10mΩ resistor gives 10-20mV at the threshold — too small for a typical comparator's input offset. I'd use a 50mΩ resistor, giving 50-100mV, which is reasonable. The resistor must be a low-inductance type (e.g., metal strip) to avoid voltage spikes from fast current edges.

For the comparator, I'd look for a device with low input offset voltage (under 1mV) and fast propagation delay (under 1µs to leave margin for filtering). The reference voltage for the threshold must be stable over temperature — a precision shunt reference or a resistor divider from a regulated supply, with the resistor values chosen for low temperature coefficient.

The real challenge is noise immunity. Motor current has significant ripple and commutation spikes. I'd add a low-pass filter before the comparator to reject noise, but the filter's time constant must be short enough to meet the 10µs response requirement. A single-pole RC filter with a cutoff around 500kHz gives roughly 0.3µs time constant, which is acceptable. I'd also add a small amount of positive feedback (hysteresis) to prevent oscillation near the threshold — typically 1-5mV of hysteresis is sufficient.

**Possible follow-ups:** How would you test and calibrate this circuit during production? What happens if the motor's inrush current exceeds the threshold during startup — how would you handle that?

---

## Q4: You're designing a crystal oscillator circuit for a 32.768kHz real-time clock in a medical device that must maintain ±5ppm accuracy over 0-50°C. How would you select the load capacitance and verify the circuit's startup margin?

**Answer:** A 32.768kHz tuning-fork crystal is highly sensitive to load capacitance — the wrong value shifts the oscillation frequency. The crystal's datasheet specifies a load capacitance (CL), typically 12.5pF or 6pF. The actual load capacitance seen by the crystal is the series combination of the two external capacitors (C1 and C2) plus the PCB trace capacitance and the oscillator pin capacitance. The formula is: CL = (C1 × C2) / (C1 + C2) + Cstray, where Cstray is typically 2-5pF.

If the crystal specifies CL = 12.5pF and I estimate Cstray = 3pF, then I need (C1 × C2) / (C1 + C2) = 9.5pF. Using equal capacitors, each would be 19pF — I'd use 18pF as a standard value. The frequency error from a 1pF mismatch in load capacitance is roughly 1-2ppm, so this selection is adequate for ±5ppm if the capacitors have reasonable tolerance (e.g., ±5% NP0/C0G ceramic).

Startup margin is critical — a crystal that doesn't reliably start oscillating is a field failure. The oscillator's negative resistance must exceed the crystal's equivalent series resistance (ESR) by a factor of 5-10. I'd measure this by inserting a variable resistor in series with the crystal and increasing it until oscillation stops. The negative resistance is the value at which oscillation ceases, minus the crystal's ESR. For a 32.768kHz crystal with ESR around 50kΩ, I'd want negative resistance of at least 300-500kΩ.

Drive level is another concern — excessive drive current can damage the crystal or cause frequency drift. I'd measure the current through the crystal using a current probe or by measuring the voltage across a small series resistor, then calculate power as I² × ESR. Most 32.768kHz crystals have a maximum drive level of 1µW. If the drive level is too high, I'd increase the external capacitors or add a series resistor to limit current.

**Possible follow-ups:** How would the design change if you needed a 25MHz fundamental-mode crystal for a microcontroller instead of a 32.768kHz watch crystal? What test equipment would you use to verify frequency accuracy?

---

## Q5: (Behavioral) Imagine you're in a design review for a medical device's battery charging circuit, and the manufacturing engineer argues that your chosen Li-ion charger IC is too expensive and proposes a discrete charger circuit using a current-limited LDO and a comparator. You believe the integrated solution is necessary for safety and compliance with IEC 60601. How would you handle this disagreement?

**Answer:** I'd start by acknowledging the manufacturing engineer's cost concern — it's valid, and in medical devices we have a responsibility to balance safety with commercial viability. I wouldn't dismiss the discrete approach outright, but I'd ask to walk through the safety implications together.

I'd frame the discussion around the specific requirements of IEC 60601 for battery charging in a patient-connected device. The standard requires protection against single-fault conditions — if a component fails, the patient must not be exposed to hazardous voltage or current. An integrated charger IC typically includes built-in safety features: overvoltage protection, overcurrent protection, thermal shutdown, and a safety timer that terminates charging if the battery doesn't reach full voltage within a specified time. A discrete implementation would need to replicate all of these with separate components, each of which adds failure points and requires its own verification.

I'd propose a compromise: let's evaluate the discrete design against the same failure mode analysis we'd apply to the integrated solution. We could create a simplified FMEA for both approaches, comparing the number of components, the failure modes of each, and the resulting hazard severity. If the discrete design can meet the same safety integrity level with acceptable cost savings, I'd be open to it. But I'd also point out that the integrated solution's certification history — the IC manufacturer has likely already done IEC 60601 compliance testing — reduces our regulatory risk and time-to-market.

If we still disagree after the technical analysis, I'd suggest a small prototyping effort: build both circuits and run accelerated life testing and fault injection tests. That gives us objective data to make the final decision, rather than arguing opinions. The goal is to find the best solution for the product, not to win an argument.

**Possible follow-ups:** What specific single-fault conditions would you test in the discrete charger design? How would you document this decision-making process for the design history file?