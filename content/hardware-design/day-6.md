# hardware-design — Day 6

## Q1: How would you approach designing a precision current source for driving a medical-grade temperature sensor (e.g., an RTD or thermistor) that must maintain accuracy within ±0.1°C over a 0–50°C range?

**Answer:** I'd start by understanding the sensor's excitation requirements and the resulting signal levels. For an RTD, a common approach is a constant current source because the resistance change is small (roughly 0.385 Ω/°C for a Pt100), so the excitation current must be stable enough that drift doesn't mask the temperature signal.

The key design decisions would be:

1. **Excitation current selection:** I'd choose a current that produces a usable voltage swing without causing self-heating. For a Pt100, 1 mA is typical — it generates about 0.1–0.4 V across the sensor while keeping self-heating below 0.1°C in most packages.

2. **Current source topology:** A Howland current pump (improved Howland with matched resistors) is a good choice for moderate accuracy. For higher precision, I'd consider a voltage reference driving a precision resistor in series with the sensor, buffered by an op-amp — this trades compliance voltage for simplicity and stability.

3. **Reference selection:** The current source's accuracy depends on the voltage reference and the sense resistor. I'd select a low-drift voltage reference (e.g., <10 ppm/°C) and a precision resistor with tight tolerance (0.1%) and low TCR (<25 ppm/°C). The op-amp should have low offset voltage drift (<1 µV/°C) and low bias current.

4. **Noise and filtering:** The excitation current's noise directly couples into the measurement. I'd add a low-pass filter at the current source output (e.g., RC with a corner frequency well below the measurement bandwidth) and ensure the sense resistor is a low-inductance type.

5. **Kelvin sensing:** For the RTD connection, I'd use a 4-wire configuration to eliminate lead resistance errors. The current source drives the outer pair, and the voltage sense is taken from the inner pair using a high-impedance differential amplifier.

6. **Calibration and trimming:** Even with precision components, I'd include a calibration step — either a trim potentiometer in the current-setting resistor or a digital calibration factor stored in firmware. The calibration would be performed at a known temperature (e.g., ice bath at 0°C) to null out initial offsets.

**Possible follow-ups:** How would you handle the trade-off between excitation current (for better signal-to-noise ratio) and self-heating error? What happens if the sensor cable is long — how does cable capacitance affect stability?

---

## Q2: Walk me through how you would debug an op-amp circuit that oscillates at approximately 1 MHz when connected to a capacitive load, but works fine with a purely resistive load.

**Answer:** This is a classic stability problem caused by the capacitive load adding a pole to the op-amp's feedback loop, reducing phase margin. Here's my systematic approach:

1. **Confirm the oscillation characteristics:** First, I'd use an oscilloscope to verify the oscillation frequency (1 MHz) and amplitude. I'd check whether the oscillation is sinusoidal or shows signs of slew-rate limiting, which would indicate the op-amp is hitting its output current limit.

2. **Identify the capacitive load:** I'd measure or estimate the total capacitive load — this includes the load capacitance itself, any cable capacitance, and the op-amp's own output capacitance. For medical sensors, long cables can easily add 50–100 pF per meter.

3. **Check the op-amp's datasheet:** I'd look at the op-amp's phase margin specification for various capacitive loads. Many general-purpose op-amps (e.g., LM358, OPAx134) have reduced phase margin above 100–200 pF. The datasheet's "capacitive load drive" graph would tell me if 1 MHz oscillation is expected.

4. **Apply a compensation technique:** The most common fix is adding an isolation resistor (typically 10–100 Ω) in series with the op-amp output, before the capacitive load. This resistor creates a zero that cancels the pole from the load capacitance. I'd calculate the resistor value using: R = 1/(2π × f_GBW × C_load) as a starting point, then adjust empirically.

5. **Add a feedback capacitor:** If the circuit uses inverting or non-inverting gain, I'd add a small capacitor (a few pF) in parallel with the feedback resistor. This creates a phase lead that improves stability. The value should be chosen so the feedback network's pole is at roughly the same frequency as the load's pole.

6. **Verify with a step response test:** After applying compensation, I'd inject a small square wave at the input and observe the output for ringing or overshoot. A well-compensated circuit should show clean settling with minimal overshoot (<10%).

7. **Check for parasitic effects:** If oscillation persists, I'd examine the PCB layout — long traces between the op-amp output and the load can add inductance, and poor decoupling can cause high-frequency instability. I'd ensure the op-amp's supply pins have 0.1 µF ceramic capacitors placed within 2 mm of the pins.

**Possible follow-ups:** How would you choose between an isolation resistor and a feedback capacitor — when would one be preferred over the other? What if the load capacitance varies from unit to unit or with temperature?

---

## Q3: How would you approach selecting an ADC for a medical device that must digitize a biopotential signal (e.g., ECG) with a bandwidth of 0.5–100 Hz, a resolution of 16 bits, and a maximum input range of ±5 mV, while operating from a single 3.3V supply?

**Answer:** This is a challenging combination because the input signal is very small (±5 mV) relative to the supply voltage, and the required resolution is high. Here's my approach:

1. **Determine the required dynamic range:** With a ±5 mV input range and 16-bit resolution, the LSB size is 10 mV / 65536 ≈ 0.15 µV. This is extremely small — thermal noise alone at room temperature in a 100 Hz bandwidth is about 1.3 µV RMS for a 10 kΩ source. So the ADC's noise floor must be well below 0.15 µV to achieve true 16-bit resolution.

2. **Consider the ADC architecture:** A sigma-delta ADC is the natural choice here. Sigma-delta converters offer high resolution (up to 24 bits) at low bandwidths, and they inherently provide noise shaping that pushes quantization noise out of the signal band. A SAR ADC with 16 bits at this signal level would require an extremely low-noise front-end and careful layout.

3. **Evaluate the need for a PGA:** With a ±5 mV input and a 3.3V supply, the ADC's full-scale range is typically 3.3V (or 2.5V with an internal reference). The signal must be amplified by roughly 300–500× to use the ADC's full range. I'd look for a sigma-delta ADC with an integrated programmable gain amplifier (PGA) — many medical-grade ADCs (e.g., ADS129x series) include PGAs with gains up to 12 or 24, plus internal reference and common-mode rejection.

4. **Check input-referred noise:** The ADC datasheet should specify input-referred noise in µV RMS or peak-to-peak at the chosen gain and data rate. For a 16-bit effective resolution at ±5 mV, I'd want input-referred noise below 0.5 µV RMS. If the ADC's noise is higher, I'd need to either reduce bandwidth (more filtering) or use averaging.

5. **Consider the reference:** The ADC's reference voltage directly affects the gain accuracy. I'd use the ADC's internal reference if it has low drift (<10 ppm/°C), or an external precision reference. For a biopotential measurement, the reference's long-term stability matters more than absolute accuracy because the signal is AC-coupled.

6. **Evaluate common-mode rejection:** Biopotential signals have large common-mode components (e.g., 50/60 Hz mains interference). The ADC's CMRR at the PGA input should be >100 dB. I'd also plan for a driven-right-leg (DRL) circuit to actively cancel common-mode voltage.

7. **Check the data rate:** For ECG, a sampling rate of 250–500 SPS is sufficient (Nyquist at 100 Hz). Sigma-delta ADCs typically offer programmable data rates, and I'd choose the lowest rate that meets the bandwidth requirement to maximize noise performance.

**Possible follow-ups:** How would you handle the DC offset from electrode half-cell potentials (which can be ±300 mV) when the signal is only ±5 mV? What filtering would you place before the ADC to prevent aliasing?

---

## Q4: How would you approach designing a hot-swap protection circuit for a medical device that receives power from an external supply through a connector, where the input voltage is 12V and the device can draw up to 3A steady-state?

**Answer:** Hot-swap protection is critical for medical devices because connecting a live power source can cause inrush current that damages connectors, causes voltage drops that reset other circuitry, or generates sparks that could be hazardous in an oxygen-rich environment. Here's my approach:

1. **Define the requirements:** I'd start by specifying the maximum allowable inrush current (e.g., 1A peak for <1 ms), the operating voltage range (12V ±10% or wider), the maximum continuous current (3A), and the transient protection requirements (e.g., IEC 61000-4-5 surge immunity for medical devices).

2. **Choose the topology:** The most common approach is an N-channel MOSFET as a pass transistor with a hot-swap controller IC. The controller ramps up the gate voltage slowly, limiting the inrush current by controlling the MOSFET's turn-on time. For 12V at 3A, a dedicated hot-swap controller (e.g., TPS2592x, LT4356) is preferable to a discrete solution because it integrates current sensing, overvoltage protection, and fault handling.

3. **Select the MOSFET:** The MOSFET must handle the steady-state current with acceptable temperature rise. I'd choose a MOSFET with Rds(on) < 20 mΩ at Vgs = 10V to keep conduction losses below 0.2W. The SOA (safe operating area) curve must cover the inrush condition — during startup, the MOSFET operates in the linear region with high Vds and high current simultaneously. I'd verify that the SOA at the expected inrush duration (e.g., 1 ms) is adequate.

4. **Set the current limit:** The hot-swap controller typically uses a sense resistor to measure current. I'd choose a resistor value that sets the current limit at about 4–5A (1.3–1.7× the steady-state current) to allow for transients while protecting against short circuits. The sense resistor should be a low-inductance type with adequate power rating (I²R losses at 3A are small, but during fault conditions the power can be significant).

5. **Add input protection:** Before the hot-swap circuit, I'd place:
   - A TVS diode for overvoltage protection (e.g., 15V standoff, 24V clamping)
   - A reverse polarity protection diode (or a second MOSFET for ideal diode behavior)
   - An input capacitor (10–100 µF) to absorb transients from the cable inductance

6. **Consider the output capacitance:** The hot-swap controller's slew rate should be set so that charging the output capacitors doesn't exceed the inrush current limit. I'd calculate the required slew rate: dV/dt = I_limit / C_load. For a 100 µF output cap and 1A limit, the slew rate would be 10 V/ms, giving a startup time of about 1.2 ms.

7. **Add fault indication:** I'd include a power-good signal from the controller to the system microcontroller, indicating when the output voltage has reached 90% of the input. This allows the system to hold off initialization until power is stable.

8. **Thermal considerations:** During a sustained short circuit, the hot-swap controller will fold back or latch off. I'd verify that the MOSFET's junction temperature stays within limits during the fault detection time (typically 1–10 ms). The PCB layout should include adequate copper area for heat dissipation.

**Possible follow-ups:** How would you handle the case where the external supply has long cables with significant inductance — what additional protection would you add? What if the medical device must meet IEC 60601-1 leakage current requirements — how does that affect the hot-swap design?

---

## Q5: (Behavioral) Imagine you're leading the hardware design for a medical device that uses a new sensor IC that your team has never worked with before. Halfway through the development cycle, you discover that the sensor's output has a systematic offset that varies significantly with temperature, and the datasheet doesn't specify the temperature coefficient. The project schedule is tight, and the firmware team is waiting for your finalized sensor interface to begin their calibration work. How would you handle this situation?

**Answer:** This is a common scenario in medical device development — new components often have undocumented behaviors that surface late in the design cycle. Here's how I'd approach it:

1. **Quantify the problem immediately:** First, I'd characterize the offset variation across the device's operating temperature range (e.g., 0–50°C for a medical device). I'd set up a temperature chamber test with a few samples of the sensor, measure the offset at multiple temperature points, and determine whether the behavior is consistent across units or varies significantly. This tells me whether a fixed compensation is possible or if per-unit calibration is needed.

2. **Assess the impact on the system:** I'd calculate whether the uncompensated offset would cause the device to fail its accuracy requirements. If the offset is small enough that it can be calibrated out in firmware, the impact is manageable. If it pushes the signal outside the ADC's input range, the hardware may need modification.

3. **Explore mitigation options in parallel:**
   - **Firmware calibration:** If the offset is consistent across units, I'd work with the firmware team to implement a temperature lookup table or polynomial correction. This requires adding a temperature sensor near the sensor IC and storing calibration coefficients.
   - **Hardware trimming:** If the offset is large, I might add a trim potentiometer or a DAC to null the offset at the analog front-end. This adds BOM cost but keeps the firmware interface simple.
   - **Sensor replacement:** If the offset is unacceptable and cannot be calibrated, I'd evaluate alternative sensors that have specified temperature coefficients. This is the worst case because it requires a PCB respin.

4. **Communicate with the team:** I'd call a brief meeting with the firmware lead, project manager, and quality/regulatory lead. I'd present the data I've collected, the options I've identified, and my recommendation. I'd be clear about the trade-offs — firmware calibration adds development time but avoids hardware changes; hardware trimming adds BOM cost but simplifies firmware.

5. **Propose a path forward:** Assuming the offset is consistent and moderate, I'd recommend firmware calibration with a temperature sensor. I'd commit to providing the characterization data within 2–3 days, including the temperature sensor placement recommendation and the expected accuracy after correction. This allows the firmware team to begin their calibration algorithm development while I complete the characterization.

6. **Document the decision:** In a medical device, any design change must be documented. I'd create a design change notice (DCN) or engineering change order (ECO) describing the issue, the characterization results, and the mitigation approach. This documentation supports the design history file (DHF) and regulatory submissions.

7. **Prevent recurrence:** After the immediate issue is resolved, I'd review our component selection process. For future projects, I'd recommend that any new sensor IC be characterized for temperature behavior early in the design cycle, even if the datasheet claims it's specified. I'd also suggest adding a "design margin" requirement — if the datasheet doesn't specify a parameter that's critical to our application, we should either get a characterization report from the manufacturer or plan for early testing.

**Possible follow-ups:** How would you handle the situation if the firmware lead insists that the calibration must be done in hardware because their schedule is already committed? What if the sensor manufacturer tells you the temperature coefficient is "proprietary" and won't share the data?