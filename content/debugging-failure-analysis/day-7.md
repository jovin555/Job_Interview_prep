# debugging-failure-analysis — Day 7

## Q1: How would you approach diagnosing a medical device that passes all functional tests at the module level but exhibits a slow sensor drift when integrated into the full system, where the drift is within the sensor's datasheet accuracy but triggers a fault condition in the system algorithm?

**Answer:** This is a classic integration-level issue where the problem isn't a component failure but a system-level interaction. I'd start by characterizing the drift precisely — logging the sensor reading alongside reference measurements over several hours to understand the drift's shape (linear, exponential, cyclic) and whether it correlates with any other system parameter like temperature, supply voltage, or processor load.

Next, I'd look at what changes between module-level and system-level testing. The sensor's reference voltage or excitation current might be shared with other circuitry in the full system, introducing subtle variations. I'd probe the sensor's supply rail and reference input with a precision multimeter and oscilloscope over the same timeframe, looking for correlations. Thermal effects are another common culprit — the sensor might be near a heat-producing component in the full system that wasn't present in module testing, causing a temperature coefficient effect that's within the datasheet but exceeds the algorithm's tolerance.

I'd also examine the algorithm's fault threshold. Sometimes the issue is that the threshold was set based on the sensor's typical accuracy rather than its worst-case over temperature and aging. I'd calculate the total error budget including temperature drift, aging, and supply sensitivity, then compare that to the algorithm's threshold. If the budget exceeds the threshold, the fix might be adjusting the algorithm, adding a calibration routine, or implementing a moving-average filter that rejects slow drift while preserving response time.

**Possible follow-ups:** How would you determine whether the drift is coming from the sensor itself or from the signal conditioning circuitry? What if the drift only appears when the system is running on battery power but not when connected to a lab supply?

---

## Q2: You're investigating a production yield issue where approximately 2% of boards fail a functional test immediately after power-up — the microcontroller doesn't start executing code. The failures appear random across batches and don't correlate with any specific component lot. How would you approach this?

**Answer:** A 2% failure rate with no lot correlation suggests a process or design marginality issue rather than a defective component. I'd start by collecting detailed data on the failures — are they truly random, or do they cluster by assembly shift, reflow oven zone, board location on the panel, or test fixture? Even small patterns can point to the root cause.

For the failing boards themselves, I'd begin with the basics: measure the power supply rails at the microcontroller pins during power-up, looking for the correct ramp rate and final voltage. Many microcontrollers have a specific power-on reset (POR) threshold and ramp rate requirement — if the supply ramps too slowly or has a glitch during ramp-up, the POR circuit might not trigger correctly, leaving the microcontroller in an undefined state. I'd use a deep-memory oscilloscope to capture the entire power-up sequence, triggering on the supply crossing the POR threshold.

I'd also check the reset pin — a weak pull-up, a noisy reset circuit, or a capacitor that's slightly out of tolerance could cause intermittent reset issues. The crystal oscillator startup time is another candidate: if the oscillator is slow to start or has marginal drive strength, the microcontroller might attempt to execute code before the clock is stable. I'd measure the oscillator startup waveform on both failing and passing boards to compare.

If the issue is truly random, I might set up a controlled experiment: take a batch of known-good boards and intentionally vary one parameter at a time (supply voltage at the low end of tolerance, temperature at the high end, oscillator load capacitance at the edge of spec) to see if I can reproduce the failure mode. This helps identify which parameter is marginal.

**Possible follow-ups:** What if the microcontroller starts executing code but crashes within the first few milliseconds — how would your approach change? How would you rule out a firmware initialization timing issue?

---

## Q3: How would you approach debugging a thermal failure in a sealed medical device that was returned from the field with a melted plastic housing near the battery charging circuit?

**Answer:** This is a safety-critical failure that requires a structured investigation. I'd start with visual inspection and documentation — photographs under magnification, noting the exact location and pattern of the melting. The pattern can tell you a lot: is the melting concentrated at a specific component, or is it more diffuse? Is there evidence of arcing, charring, or discoloration of the PCB?

Next, I'd carefully disassemble the device and examine the battery charging circuit. I'd look for signs of component stress — cracked solder joints, lifted pads, discolored components, or bulging capacitors. I'd measure the key components: the charging IC for shorts, the inductor for saturation damage, the sense resistors for value drift, and the battery connector for signs of high resistance or arcing.

The root cause often falls into one of several categories: a component failure that caused excessive current, a design marginality that allowed a fault condition to go undetected, or a manufacturing defect like a cold solder joint that created high resistance and localized heating. I'd check the charging IC's datasheet for known failure modes and verify that the protection features (overcurrent, overtemperature, reverse battery) are functioning as designed.

I'd also review the device's fault detection and shutdown logic. If the charging IC has a thermal shutdown feature, did it trigger? If not, why? Was the thermal protection threshold set appropriately for the sealed enclosure? I'd calculate the expected junction temperature of the charging IC under worst-case charging conditions, considering the thermal resistance of the sealed enclosure, and compare that to the IC's maximum rating.

Finally, I'd perform fault injection testing on a reference unit — intentionally creating the suspected failure conditions (e.g., shorting the battery input, overloading the charger output, blocking airflow) to see if the failure mode reproduces. This confirms the root cause and validates the corrective action.

**Possible follow-ups:** How would you determine whether the melting was caused by a single catastrophic event or by cumulative thermal stress over time? What additional testing would you recommend for the corrective action validation?

---

## Q4: How would you approach debugging a signal integrity issue where a high-speed SPI bus between a microcontroller and an ADC shows intermittent bit errors, but only when the device's motor driver is active?

**Answer:** This is a classic EMI coupling problem where the motor driver's switching noise is interfering with the SPI bus. I'd start by characterizing the interference — what frequency is the motor driver switching at, and what are the rise/fall times of the motor drive signals? Fast edges on long motor wires can create significant radiated emissions and conducted noise.

I'd use a near-field probe and spectrum analyzer to scan the PCB while the motor is running, looking for areas where the switching noise couples onto the SPI traces. Common coupling paths include: capacitive coupling from the motor driver's high-voltage switching nodes to nearby SPI traces, inductive coupling from the motor current loop to the SPI ground return path, or conducted noise on the shared power supply rail.

For the SPI bus itself, I'd probe the clock and data lines with an oscilloscope while the motor is active, looking for noise on the signal edges. I'd check for ground bounce — if the motor current returns through the same ground plane as the SPI bus, the voltage drop across the ground impedance can shift the logic thresholds. I'd measure the ground voltage difference between the microcontroller and the ADC using a differential probe.

Mitigation strategies depend on the coupling mechanism. If it's capacitive coupling, I might increase the spacing between the motor traces and the SPI traces, add a ground guard trace, or reduce the impedance of the SPI lines. If it's conducted noise on the power supply, I'd check the decoupling — the motor driver might need a larger bulk capacitor or a ferrite bead to isolate its switching noise from the analog supply. If it's ground bounce, I'd look at the ground return path — a solid ground plane with minimal impedance between the microcontroller and ADC is critical.

I'd also consider the SPI timing margins. If the noise is small but the setup/hold margins are already tight, even minor noise can cause errors. I might slow down the SPI clock or add a small RC filter on the data lines (if the data rate allows) to improve noise immunity.

**Possible follow-ups:** How would you determine whether the coupling is through the ground plane or through the power supply? What if the SPI bus is operating at 20 MHz and you can't slow it down — what other options do you have?

---

## Q5: A senior manager asks you to lead a cross-functional root-cause investigation for a critical medical device failure that occurred in the field. The device was returned with a note that it "stopped working" — no error logs, no visible damage. The project schedule is tight, and there's pressure to find a quick fix. How would you structure this investigation?

**Answer:** This is a situation where the pressure for speed can easily lead to jumping to conclusions, so the first step is to establish a disciplined process that actually saves time by avoiding wasted effort. I'd start by assembling a small cross-functional team — hardware, firmware, quality, and manufacturing — and define the scope of the investigation clearly. We need to agree on what we know, what we don't know, and what constitutes a confirmed root cause versus a hypothesis.

The first practical step is a thorough physical inspection of the returned device. I'd document the device's condition with photographs, check for any signs of physical damage, corrosion, or tampering, and then attempt to reproduce the failure. If the device powers up and works, I'd run it under various conditions — different loads, temperatures, orientations — to see if I can trigger the failure. If it doesn't power up, I'd systematically measure the power rail from the battery through to the microcontroller, looking for opens, shorts, or components that are drawing excessive current.

While the physical investigation is underway, I'd have the firmware team check if there's any non-volatile memory that might contain diagnostic data — sometimes devices store error codes or fault flags even if they don't have a formal logging system. I'd also review the device's history: when was it manufactured, what batch, what was the last service date, and are there any other similar field returns?

For the root-cause analysis, I'd use a structured approach like 8D or fishbone diagramming to generate hypotheses, then prioritize them based on evidence and testability. The key is to test one hypothesis at a time, with clear pass/fail criteria, rather than trying multiple fixes simultaneously. This might feel slower initially, but it prevents the common trap of implementing a "fix" that doesn't actually address the root cause.

To manage the schedule pressure, I'd communicate transparently with the manager about what we can deliver and when. I'd propose interim milestones: a preliminary assessment within 48 hours (what we know, what we suspect, what we need), a containment action within a week (if needed to prevent further field failures), and a confirmed root cause within a defined timeframe based on the complexity. I'd also ask the manager to help protect the team from distractions so we can focus on the investigation.

**Possible follow-ups:** How would you handle a situation where two team members have conflicting hypotheses and both have some supporting evidence? What if the containment action is expensive and the business wants to skip it — how would you advocate for patient safety?