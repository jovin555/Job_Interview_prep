# hardware-design — Day 27

## Q1: How would you approach designing a battery fuel gauge for a medical device that must operate across a wide temperature range (0–50°C) and report remaining capacity with reasonable accuracy, given that the device has both continuous low-current loads and periodic high-current pulses?

**Answer:** I'd start by recognizing that voltage-based fuel gauging alone won't be adequate here — the periodic high-current pulses cause significant voltage droop due to battery internal resistance, which would make voltage-based estimates misleading. The temperature range also complicates things because both battery capacity and internal resistance change substantially with temperature.

My approach would be coulomb counting (charge integration) as the primary method, combined with voltage-based correction. I'd use a dedicated fuel gauge IC with an integrated sense resistor and coulomb counter, rather than trying to implement this discretely — the integration accuracy, temperature compensation, and self-calibration features in modern gauge ICs are difficult to replicate with discrete components.

For the implementation, I'd pay careful attention to the sense resistor selection: it needs to be low enough to minimize voltage drop and power loss during the high-current pulses, but high enough to maintain measurement resolution during the low-current periods. A 5–10 mΩ resistor is often a reasonable starting point, depending on the current range.

For temperature compensation, I'd use the gauge's built-in temperature measurement and look-up tables for capacity vs. temperature. I'd also implement periodic open-circuit voltage (OCV) corrections when the device enters a known low-current state — this lets the gauge recalibrate against the voltage-based estimate and correct for coulomb counting drift.

One important consideration for a medical device is that the fuel gauge must be reliable and predictable. I'd ensure the gauge has a defined behavior at end-of-discharge — the device should give the user adequate warning before shutdown, and the gauge should not "jump" in its readings. I'd also consider whether the device needs to log battery health data for maintenance purposes.

**Possible follow-ups:**
- How would you handle the fuel gauge's accuracy during the first few charge/discharge cycles before it has "learned" the battery's characteristics?
- What safety considerations would you factor in if the fuel gauge IC itself fails — how would the device detect and respond to that?

---

## Q2: Walk me through how you would debug a circuit where a precision analog front-end's output shows a periodic disturbance at approximately 1–10 Hz, even when the input is shorted to ground, and the disturbance amplitude varies with the power supply voltage.

**Answer:** This is a classic symptom pattern that points toward a low-frequency noise source coupled into the signal path, and the fact that it varies with supply voltage is a strong clue. Let me walk through my systematic approach.

First, I'd confirm the disturbance is real and not a measurement artifact — I'd check with a spectrum analyzer or FFT on the output to verify the frequency content and see if there are harmonics or sidebands that might reveal the source.

The 1–10 Hz range is interesting because it's too slow for most switching regulators (which typically operate at 100 kHz–2 MHz) and too fast for thermal drift. Common culprits include: reference voltage noise, particularly from a reference with poor low-frequency noise performance; power supply ripple from a control loop that's oscillating at low frequency; or external interference from mains (50/60 Hz) that's being aliased or mixed down.

Since the amplitude varies with supply voltage, I'd suspect the power supply is involved. I'd start by measuring the actual supply rail at the analog front-end's supply pin with a scope in AC coupling mode, looking for low-frequency ripple or oscillation. A supply that's marginally stable can oscillate at low frequency, especially if there's a load-dependent feedback interaction.

I'd also check the voltage reference — a reference with inadequate decoupling or one that's oscillating can produce exactly this symptom. I'd measure the reference output directly and look for the same 1–10 Hz disturbance.

Another possibility is thermoelectric effects — if there's a temperature-sensitive component near a heat source (like a regulator or processor), the resulting thermal cycling can produce low-frequency signals. I'd check for any periodic heating in the system, such as a processor that wakes periodically.

My debugging sequence would be: (1) FFT the output to characterize the disturbance precisely; (2) measure supply rails and reference with AC coupling; (3) use a battery or clean bench supply to power the analog section in isolation; (4) if the disturbance disappears, work backward to identify which supply is the culprit; (5) if it persists, suspect the reference or the front-end itself — I'd bypass the front-end and measure the reference directly.

**Possible follow-ups:**
- What if the disturbance disappears when you power the board from a bench supply but reappears when using the device's battery? What would that tell you?
- How would you distinguish between a power supply issue and a ground loop issue in this scenario?

---

## Q3: How would you approach designing a hardware-based overcurrent protection circuit for a motor driver in a medical device, where the protection must be independent of the main microcontroller and must respond within microseconds?

**Answer:** For a medical device, the protection must be deterministic, fail-safe, and verifiable — this is a safety function, so it needs to work even if the main processor is hung or malfunctioning. I'd design this as a dedicated analog protection circuit with a clear, testable response.

The core architecture would be: a current-sense element (either a low-value sense resistor or the MOSFET's RDS(on) if that's accurate enough), a comparator with a precision reference for the threshold, and a latch or direct shutdown path to the motor driver's enable input.

For the sense element, I'd use a low-value, low-inductance sense resistor (e.g., 5–10 mΩ) in the source or emitter path of the motor drive stage. The voltage across it is amplified or compared directly against a reference. The key challenge is that the sense voltage is small, so I need a comparator with low offset voltage and good common-mode rejection.

For the comparator, I'd select one with a fast propagation delay (under 1 µs) and a built-in reference or use an external precision reference. The threshold should be set with some margin above the normal operating current but well below the absolute maximum rating of the motor driver and motor. I'd also add a small amount of filtering to prevent false trips from legitimate current transients — but this filtering must be carefully balanced against the response time requirement.

The output of the comparator would drive a latch circuit that shuts down the motor driver immediately. The latch is important because it maintains the fault state even after the overcurrent condition clears — this prevents the motor from rapidly cycling on and off. The latch would be reset only through a deliberate action, such as a power cycle or a manual reset signal.

For fail-safe behavior, I'd consider the failure modes: if the comparator loses power, the motor should default to off. I'd use a pull-down on the enable line so that any fault in the protection circuit results in the motor being disabled. I'd also add a test point or self-test capability so the protection can be verified during manufacturing and periodic maintenance.

Finally, I'd document the protection circuit's response time, threshold accuracy, and test procedure as part of the device's safety case — this is critical for regulatory review in a medical device.

**Possible follow-ups:**
- How would you verify that the protection circuit actually responds within the required time under all operating conditions?
- What if the motor's normal starting current briefly exceeds your protection threshold — how would you handle that without compromising safety?

---

## Q4: How would you approach selecting the decoupling capacitor network for a high-resolution ADC that shares a PCB with a wireless radio transmitting periodic bursts?

**Answer:** This is a classic mixed-signal challenge — the radio's current bursts create supply transients that can corrupt the ADC's reference and analog supply, degrading its performance. The goal is to isolate the ADC from these transients while maintaining a clean, stable supply.

I'd approach this in layers. First, I'd separate the ADC's analog supply and reference from the digital/radio supply at the PCB level — ideally with dedicated power planes or at least separate traces that only meet at a single point (a star point) near the main supply input.

For the ADC's supply pin, I'd use a multi-stage decoupling approach. The first stage, closest to the pin, would be a small-value, low-ESL capacitor (e.g., 100 nF in a 0402 or 0201 package) to handle high-frequency transients. The second stage would be a larger value (e.g., 1–10 µF) in a larger package to handle lower-frequency content. I'd also consider a ferrite bead between the main supply rail and the ADC's analog supply pin — this creates a low-pass filter that attenuates the radio's switching noise.

The critical parameter here is the impedance of the decoupling network across frequency. I'd model or simulate the impedance of the capacitor network to ensure it stays low (ideally under 1 Ω) across the frequency range of interest — from the ADC's sampling frequency down to the radio's burst repetition rate.

For the reference pin, I'd use a dedicated reference IC with its own decoupling, and I'd ensure the reference's output impedance is low at the ADC's sampling frequency. The reference decoupling is often more critical than the supply decoupling for ADC performance.

I'd also consider the physical layout: the decoupling capacitors must be placed as close as possible to the ADC's pins, with short, direct connections to the ground plane. The return current path for the radio's bursts should not flow through the ADC's ground connection — I'd use a solid ground plane and ensure the ADC's analog ground and the radio's ground are connected at a single point.

Finally, I'd verify the design by measuring the ADC's performance (e.g., SNR, ENOB) with the radio transmitting at full power, and compare it to the performance with the radio off. If there's degradation, I'd use a spectrum analyzer to identify the coupling path — it might be through the supply, the ground, or radiated coupling.

**Possible follow-ups:**
- How would you decide whether a ferrite bead is necessary, and how would you select its impedance and frequency characteristics?
- What if the ADC's performance is still degraded after your decoupling improvements — how would you isolate whether the coupling is through the supply, ground, or radiation?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing the hardware-based overcurrent protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors current via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** This is a safety-critical disagreement, and I'd handle it by focusing on the engineering evidence and regulatory requirements rather than just asserting my position. The key is to have a structured, respectful discussion that leads to the right decision for the device.

First, I'd acknowledge the firmware lead's valid points — the firmware approach does offer flexibility and cost savings, and those are legitimate engineering considerations. I'd then frame my concern around the safety requirements: for a medical device, the overcurrent protection is a safety function, and safety functions need to be reliable under all conditions, including fault conditions.

I'd ask the firmware lead to walk through the failure scenarios: what happens if the ADC's reference drifts, causing the current reading to be inaccurate? What happens if the firmware is stuck in a loop and can't execute the shutdown? What happens if the GPIO fails? The firmware approach depends on the entire chain — ADC, firmware execution, and GPIO — all working correctly. The hardware approach has a much simpler failure model: the comparator and latch either work or they don't, and we can test that.

I'd also reference the regulatory context — IEC 60601 and ISO 14971 require that safety functions be designed with appropriate reliability and that the design be justified through risk analysis. A firmware-based safety function is not inherently unacceptable, but it requires a much more rigorous analysis of failure modes, and it may require additional mechanisms (like a watchdog that's independent of the main firmware) to be acceptable.

Rather than just saying "no," I'd propose a path forward: we could do a formal risk analysis of both approaches, documenting the failure modes and their severity. If the firmware approach can meet the same safety integrity level as the hardware approach — with appropriate mitigations — I'd be open to considering it. But I'd want to see that analysis before agreeing.

If the firmware lead still disagrees, I'd escalate to the project manager or a safety engineer, presenting both perspectives and the risk analysis. The decision should be based on the safety case, not on who argues more persuasively.

**Possible follow-ups:**
- What if the firmware lead argues that the hardware approach also has failure modes (e.g., the comparator could fail)? How would you respond?
- How would you document this disagreement and its resolution for the project's design history file?