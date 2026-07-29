# hardware-design — Day 8

## Q1: How would you approach selecting the switching frequency for a buck converter in a medical device that must balance efficiency, output ripple, and EMI compliance?

**Answer:** The switching frequency selection involves several trade-offs that must be evaluated against the specific requirements of the medical device. Higher switching frequencies (e.g., 1–2 MHz) allow smaller inductor and capacitor values, reducing board area and component height — important for portable devices. However, higher frequencies increase switching losses in the MOSFET and gate-drive losses, reducing efficiency at light loads. They also make EMI filtering more challenging because the fundamental and its harmonics extend into frequency bands where conducted and radiated emission limits are stricter.

Lower frequencies (e.g., 100–400 kHz) improve efficiency and simplify EMI filtering, but require larger passive components and may produce audible noise if the frequency falls in the human hearing range. For a medical device, I would start by identifying the critical constraints: Is board space at a premium? Is the device battery-powered (favoring efficiency at typical load currents)? What are the applicable EMI standards (e.g., CISPR 11 for medical equipment)?

A practical approach is to select a frequency that keeps the inductor ripple current between 20–40% of the maximum load current, then verify that the resulting output ripple meets the device's requirement (e.g., ≤10 mV peak-to-peak for an analog supply). I would also check the converter's datasheet for frequency spread-spectrum options, which can help with EMI compliance by reducing peak emissions. Finally, I would prototype the chosen frequency and measure both efficiency across the load range and conducted emissions in a pre-compliance test, iterating if needed.

**Possible follow-ups:**
- How would you decide between a fixed-frequency and a variable-frequency (e.g., PFM) control scheme for a medical device that spends most of its time in standby?
- What specific layout considerations change when you double the switching frequency from 500 kHz to 1 MHz?

---

## Q2: Walk me through how you would design a low-battery detection circuit for a single-cell Li-ion powered medical device, where the threshold must be accurate to within ±2% over 0–50°C and the circuit must consume less than 1 µA in standby.

**Answer:** The key challenge here is achieving ±2% accuracy across temperature while keeping quiescent current under 1 µA. A simple resistor divider feeding a microcontroller's ADC is problematic because the divider itself draws current continuously — a 1 MΩ divider on a 3.7V battery draws about 3.7 µA, already exceeding the budget. Instead, I would use a precision voltage reference and a comparator with an enable pin, or a dedicated battery-monitoring IC with an integrated voltage reference and programmable thresholds.

My preferred approach for ultra-low-power designs is to use a nanopower comparator (e.g., with 300 nA typical supply current) combined with an external precision voltage reference that can be gated. The circuit works as follows: The battery voltage is divided by a high-value resistor network (e.g., 10 MΩ total) to bring it into the comparator's input range. The comparator's non-inverting input receives this divided voltage, while the inverting input receives a fixed reference voltage (e.g., 1.2V from a shunt reference). The comparator output goes to a microcontroller interrupt pin.

To meet the ±2% accuracy requirement, I need to account for: resistor divider tolerance (use 0.1% tolerance resistors with low TCR, e.g., ±25 ppm/°C), reference voltage accuracy over temperature (select a reference with ±0.5% initial accuracy and <50 ppm/°C drift), and comparator offset voltage (choose a comparator with <1 mV offset). The total worst-case error can be calculated by summing these contributions.

For the 1 µA standby budget, I would gate the voltage reference with a microcontroller GPIO pin — the reference is only powered on for a few milliseconds every few seconds when the battery voltage needs to be checked. During the off period, the reference draws zero current, and the comparator's quiescent current (e.g., 300 nA) plus the resistor divider current (e.g., 370 nA from a 10 MΩ divider) keeps the total well under 1 µA. The microcontroller itself would be in deep sleep, waking periodically to read the comparator output.

**Possible follow-ups:**
- How would you add hysteresis to this comparator circuit to prevent oscillation near the threshold, and how does hysteresis affect the accuracy?
- What failure modes would you consider for this circuit in a medical device, and how would you make it fail-safe?

---

## Q3: How would you approach designing a precision voltage reference circuit for a 16-bit SAR ADC that must maintain accuracy within ±1 LSB over a 0–50°C temperature range, given a 3.3V supply and a 2.5V reference voltage?

**Answer:** For a 16-bit SAR ADC with a 2.5V reference, 1 LSB is approximately 38 µV. Maintaining accuracy within ±1 LSB over temperature requires careful selection of the voltage reference IC and its support circuitry. I would start by calculating the allowable drift: over a 50°C range, the reference's temperature coefficient must be better than ±38 µV / 50°C = ±0.76 µV/°C, which translates to approximately ±0.3 ppm/°C relative to 2.5V. This is an extremely demanding requirement — most standard references are in the 1–5 ppm/°C range, so I would need a high-precision reference (e.g., a buried-Zener or XFET type) with a specified drift of ≤0.5 ppm/°C.

Beyond the reference IC itself, several other factors affect accuracy. The reference's output noise must be low enough not to degrade the ADC's SNR — I would check the reference's 0.1–10 Hz noise specification and add a low-pass filter (e.g., a 10 µF capacitor in parallel with a 0.1 µF ceramic) to reduce wideband noise. The reference's load regulation matters because the ADC draws dynamic current during conversion — I would ensure the reference can source the ADC's maximum reference input current with minimal voltage drop, or add a buffer amplifier with low offset drift.

PCB layout is critical: the reference's output must be routed with a dedicated trace (not shared with digital signals), and its bypass capacitors should be placed as close as possible to the reference's output pin. The reference's ground pin should connect directly to the ADC's analog ground plane, not through a shared digital ground path.

Finally, I would consider using a ratiometric measurement approach if the sensor and reference share the same supply — this cancels out some supply and reference drift errors. If absolute accuracy is required, I would include a calibration routine in firmware that measures a known voltage during production and stores correction coefficients.

**Possible follow-ups:**
- How would you characterize the actual temperature drift of your reference circuit during validation, and what equipment would you use?
- If the reference's output noise specification is given as 10 µV peak-to-peak (0.1–10 Hz), how would you determine whether this is acceptable for your 16-bit system?

---

## Q4: How would you approach debugging a circuit where a crystal oscillator (8 MHz, 20 pF load capacitance) fails to start reliably when the ambient temperature drops below 0°C, but works fine at room temperature?

**Answer:** This is a classic symptom of insufficient negative resistance in the oscillator circuit at low temperatures. The crystal's equivalent series resistance (ESR) increases as temperature decreases, and if the oscillator's negative resistance (which is determined by the amplifier gain and feedback network) is only marginally higher than the crystal's ESR at room temperature, the startup margin can disappear at low temperatures.

My debugging approach would be systematic. First, I would measure the actual negative resistance of the oscillator circuit at room temperature using a series resistor method: insert a variable resistor in series with the crystal, increase it until oscillation stops, and the negative resistance equals the sum of the crystal's ESR plus the inserted resistor value. A good rule of thumb is that the negative resistance should be at least 5 times the crystal's maximum ESR over the full temperature range. If the margin is insufficient, I would increase the amplifier's drive strength (if the microcontroller allows it) or reduce the feedback resistor value.

Second, I would verify the load capacitance. The crystal's datasheet specifies a load capacitance (e.g., 20 pF), and the PCB's stray capacitance plus the two external loading capacitors (typically in a Pierce oscillator configuration) must match this value. If the external capacitors are too large, the oscillator will be over-loaded, reducing the negative resistance and making startup unreliable. I would measure the actual oscillation frequency at room temperature — if it's significantly off from 8 MHz, the load capacitance is likely incorrect.

Third, I would check the drive level. If the oscillator is under-driven, it may not have enough gain to overcome the crystal's ESR at low temperatures. Conversely, over-driving can damage the crystal. I would measure the voltage across the crystal with an oscilloscope probe (using a low-capacitance probe to avoid loading the circuit) and compare it to the crystal's maximum drive level specification.

Finally, I would examine the PCB layout around the crystal: long traces, ground plane cuts underneath the crystal, or nearby switching signals can all affect startup reliability. The crystal and its loading capacitors should be placed as close as possible to the oscillator pins, with a solid ground plane underneath and no digital traces crossing the oscillator area.

**Possible follow-ups:**
- How would you calculate the required negative resistance for reliable startup given a crystal with 50 Ω maximum ESR?
- What changes would you make to the circuit if you cannot increase the drive strength and the negative resistance margin is still insufficient?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the manufacturing engineer argues that your chosen PCB stackup (8-layer, with two dedicated ground planes) is unnecessarily expensive and proposes a 4-layer stackup instead. You believe the 8-layer design is necessary for signal integrity and EMI compliance, particularly for the high-resolution ADC and wireless transmitter on the board. How would you handle this disagreement?

**Answer:** I would approach this as a collaborative problem-solving exercise rather than a confrontation. First, I would acknowledge the manufacturing engineer's concern — cost is a legitimate constraint, and their perspective on manufacturability is valuable. Then, I would propose a structured analysis to determine whether the 8-layer stackup is truly necessary or whether a 4-layer design could be made to work with additional mitigation measures.

I would suggest we jointly review the specific signal integrity and EMI risks that drove the 8-layer decision. For example, the high-resolution ADC requires a clean analog ground reference and isolation from the digital switching noise of the microcontroller and wireless transmitter. In an 8-layer stackup, I can dedicate two layers to ground (one for analog, one for digital) with a split plane, and use the additional layers for power routing and signal routing with controlled impedance. In a 4-layer stackup, I would have only one ground plane, making it much harder to isolate the analog and digital sections.

I would propose a trade-off analysis: identify which signals are most critical and determine whether they can be adequately protected in a 4-layer design with careful routing, increased use of guard traces, and possibly lower-impedance decoupling. I would also consider whether the wireless transmitter's emissions could be managed with additional shielding (adding cost) or whether the 8-layer stackup's inherent isolation is more cost-effective overall.

To resolve the disagreement objectively, I would suggest we prototype a critical subsection of the board (e.g., the ADC front-end and the transmitter) in both 4-layer and 8-layer configurations and measure signal-to-noise ratio, radiated emissions, and receiver sensitivity. This data would inform a data-driven decision. If the 4-layer version meets all requirements with acceptable margin, I would be happy to adopt it. If not, the test results would justify the additional cost of the 8-layer stackup to the project manager and stakeholders.

Throughout this process, I would maintain a collaborative tone — the goal is to find the best solution for the project, not to win an argument. I would also document the analysis and test results so that future projects can benefit from the learning.

**Possible follow-ups:**
- What specific measurements would you take on the prototypes to compare the two stackup options?
- If the 4-layer prototype fails EMI testing, but the manufacturing engineer argues that the test setup is overly conservative, how would you decide whether to accept the risk or insist on the 8-layer design?