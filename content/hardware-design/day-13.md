# hardware-design — Day 13

## Q1: How would you approach designing a battery charging circuit for a medical device that must charge a single-cell Li-ion battery while the device is simultaneously in use, and what are the key safety considerations?

**Answer:** For a medical device that needs to operate while charging, I'd first establish whether the system can tolerate the charger interrupting the load path. The safest architecture for medical applications is a "path management" or "power-path" topology where the charger can supply the system load directly while charging the battery, rather than a simple charger that connects directly to the battery and load in parallel. This prevents the load from discharging the battery during charge termination and avoids the situation where the load's current draw confuses the charger's termination logic.

Key design decisions would include: selecting between a linear and switching charger based on thermal budget and charge current requirements — linear chargers are simpler and quieter but dissipate significant heat at higher currents; implementing proper charge profile (CC-CV) with temperature monitoring via an NTC thermistor on the battery pack; and ensuring the charger IC has a valid battery detection feature to avoid charging a shorted or damaged cell.

For safety, I'd focus on: redundant overvoltage and overcurrent protection (both the charger IC's internal limits and external protection), reverse current blocking to prevent the battery from back-feeding the charger when input power is removed, and compliance with the battery safety standards relevant to medical devices. I'd also consider the failure modes — what happens if the charger IC fails short, if the thermistor disconnects, or if the battery voltage doesn't rise during charging? The design should default to a safe state in each case.

For the "charge while in use" requirement specifically, I'd verify that the system's peak current draw plus the charge current doesn't exceed the input adapter's capability, and that the power-path switching doesn't cause voltage dips that could reset the microcontroller or corrupt ADC readings.

**Possible follow-ups:** How would you handle the situation where the device must charge and operate simultaneously but the input adapter can only supply enough current for one or the other? What additional considerations apply if this is a medical device that could be used by a patient without supervision?

---

## Q2: Walk me through how you would debug a circuit where a 16-bit SAR ADC produces correct readings at room temperature but shows increasing nonlinearity and missing codes as the temperature rises above 50°C.

**Answer:** I'd approach this systematically, starting with the hypothesis that temperature is affecting either the reference, the input signal chain, or the ADC itself.

First, I'd characterize the failure precisely: at what temperature does it start, does it progress gradually or suddenly, and is it consistent across multiple channels or only one? This helps narrow whether it's a shared reference issue or a per-channel problem.

Next, I'd check the voltage reference — many references have temperature coefficients that cause drift, but drift alone would typically show as gain error, not nonlinearity or missing codes. Missing codes more often indicate that the ADC's internal comparator or capacitor array is having trouble settling, which can happen if the reference voltage is noisy at temperature, or if the reference buffer's bandwidth is degrading.

I'd also examine the input driver op-amp. At elevated temperature, the op-amp's output impedance can increase, and if the ADC's sampling capacitor is drawing charge through that impedance, the settling time increases. If the op-amp can't fully settle within the acquisition window, you get exactly this kind of nonlinearity and missing codes. I'd check the op-amp's datasheet for how its open-loop gain and output impedance change with temperature.

I'd also look at the PCB layout — thermal expansion can cause micro-cracks in solder joints or stress on the ADC's package, which can manifest as intermittent connection issues. I'd use thermal imaging to see if there's a hot spot near the ADC or reference.

Finally, I'd check the ADC's power supply pins for increased ripple at temperature, since the ADC's PSRR degrades with temperature, and I'd verify that the digital interface isn't experiencing timing issues (though that would more likely cause communication errors than missing codes).

**Possible follow-ups:** How would you distinguish between a reference issue and an input settling issue using only measurements you can make with standard lab equipment? What if the problem only appears when the device is in its enclosure, not on the bench?

---

## Q3: How would you approach designing a low-power sleep mode for a battery-powered medical monitoring device that must wake periodically to take a sensor reading, while ensuring that the wake-up mechanism itself doesn't introduce noise into the analog front-end?

**Answer:** The core challenge here is that the wake-up event creates a transient disturbance — the processor and peripherals power up, current draw spikes, and the power rails can dip or ring — and that transient can couple into the analog front-end if the design isn't careful.

I'd start by separating the wake-up mechanism from the analog measurement in time. The firmware should wake the digital core first, let the power rails stabilize, then power up the analog front-end, and only then take the measurement. This "sequenced wake-up" avoids measuring during the transient.

For the hardware design, I'd consider: using a separate low-noise LDO for the analog front-end that is always powered but in a low-quiescent-current mode, so the analog reference and bias circuits stay stable; adding a dedicated wake-up timer or RTC that runs from a separate low-power domain, so the main processor can be fully powered down; and ensuring that the wake-up signal itself (typically a GPIO interrupt or timer output) is not routed near the analog signal traces.

I'd also think about the decoupling strategy — the wake-up transient will draw current from the bulk capacitor, and if the analog and digital sections share a common path to that capacitor, the voltage drop will couple into the analog supply. A pi-filter or ferrite bead between the digital and analog supply domains helps isolate the transient.

For the firmware side, I'd specify that the ADC should take multiple samples and discard the first few, since the first sample after wake-up may be corrupted by settling. I'd also consider using a duty-cycled approach where the analog front-end is powered continuously but the ADC only samples at the right time, rather than power-cycling the entire front-end, which creates thermal and electrical settling issues.

**Possible follow-ups:** How would you decide between keeping the analog front-end always powered versus power-cycling it for each measurement? What if the sensor itself requires a warm-up time after power is applied?

---

## Q4: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes using the microcontroller's internal ADC instead of the external dedicated ADC you've specified, arguing that the internal ADC is "good enough" and will save cost and board space. You believe the internal ADC's noise performance and accuracy are insufficient for the measurement requirements, and the datasheet specifications are marginal at best. How would you handle this disagreement?

**Answer:** I'd approach this by focusing on data and requirements rather than defending my original choice. First, I'd acknowledge that the firmware lead has a valid point about cost and board space — those are real considerations, and I should be open to the possibility that my original specification was over-engineered.

I'd propose a structured evaluation: we take the measurement requirements from the product specification — the required accuracy, resolution, noise floor, and sampling rate — and compare them against the internal ADC's datasheet specifications, particularly ENOB (effective number of bits), INL/DNL, and noise performance. I'd suggest we build a quick test fixture using an evaluation board with the same microcontroller and run the actual sensor signal through it, measuring the resulting data quality against the requirements.

If the internal ADC genuinely meets the requirements with adequate margin, I'd be willing to switch. But I'd also raise the risk factors: internal ADCs are often more susceptible to digital noise coupling from the microcontroller's own switching activity, and the performance can vary more with temperature and supply voltage. I'd ask whether we have the test data to prove it works across the full operating range, not just at room temperature.

I'd also consider the system-level implications — if the internal ADC requires extensive firmware filtering or calibration to meet the requirements, that adds firmware development time and complexity, which may offset the cost savings. I'd ask the firmware lead to estimate the effort for that.

Ultimately, I'd frame it as a joint decision based on evidence: we define the acceptance criteria together, run the evaluation, and let the data decide. If the internal ADC fails the evaluation, the firmware lead will understand why we need the external part. If it passes, I'll support the change.

**Possible follow-ups:** What if the evaluation shows the internal ADC is marginal — it passes at room temperature but the noise margin is thin? How would you decide whether to accept the risk or insist on the external ADC? How would you document this decision for the design history file?

---

## Q5: How would you approach designing the input protection and conditioning circuit for a medical device that measures biopotential signals (e.g., ECG) from electrodes connected via a patient cable, considering both safety and signal quality?

**Answer:** This is a classic medical front-end design problem where safety and signal quality pull in different directions, so I'd start by establishing the safety requirements first, then work on signal quality within those constraints.

For safety, the patient connection must be isolated from the mains and from any other hazardous voltages. I'd use a reinforced isolation barrier between the patient-side circuitry and the rest of the device, with appropriate creepage and clearance distances per the applicable standard. The patient-side circuitry should be designed to limit leakage current to safe levels, and I'd include series resistors in the electrode leads (typically 10-100 kΩ) to limit fault current if the patient comes into contact with another voltage source.

For the input protection, I'd use a combination of: series resistors for current limiting, clamping diodes to the supply rails to handle electrostatic discharge and defibrillator pulses (if the device needs to survive defibrillation), and possibly a spark gap or gas discharge tube for extreme events. The clamping diodes need to have very low leakage to avoid degrading the measurement, and the series resistors need to be chosen so that the voltage drop across them doesn't significantly attenuate the signal — for ECG, the source impedance is relatively high, so the input impedance of the amplifier needs to be very high (typically >10 MΩ).

For signal conditioning, I'd use an instrumentation amplifier with high CMRR as the first stage, since biopotential signals are differential and the common-mode interference (from mains coupling) can be much larger than the signal itself. I'd add a right-leg drive circuit to actively cancel common-mode voltage, and I'd include a driven shield on the patient cable to reduce motion artifacts and interference pickup.

For the filtering, I'd use a bandpass filter (typically 0.5-100 Hz for ECG) with a notch filter at 50/60 Hz if needed. The key is to place the filtering after the instrumentation amplifier, where the signal has already been amplified and the common-mode rejection has already occurred.

I'd also think about the grounding strategy — the patient-side ground should be isolated from the device ground, and I'd use a guard trace around the input traces to minimize leakage currents on the PCB.

**Possible follow-ups:** How would you handle the trade-off between input protection (which adds series resistance) and signal quality (which wants low source impedance)? What testing would you do to verify that the isolation barrier meets the safety requirements?