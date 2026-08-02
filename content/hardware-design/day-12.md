# hardware-design — Day 12

## Q1: How would you approach designing a soft-start circuit for a medical device that draws significant inrush current when power is first applied, and what trade-offs would you consider between inrush limiting and startup time?

**Answer:** The primary goal of soft-start is to limit inrush current during power-up, which protects upstream supplies, connectors, and the device's own components from stress. My approach would start by characterizing the worst-case inrush scenario: the bulk capacitance on the rail, the load's initial state, and the upstream supply's current capability.

For a simple, robust solution, I'd consider an N-channel MOSFET with a controlled gate ramp. The gate voltage is ramped slowly using an RC network or a dedicated soft-start pin on a hot-swap controller, which limits the slew rate of the output voltage and therefore the charging current into the bulk capacitors. The key design equation is I = C × dV/dt — if I know the maximum acceptable inrush current and the total capacitance, I can calculate the required voltage slew rate and size the RC time constant accordingly.

The main trade-off is startup time versus inrush current. A slower ramp reduces inrush but delays the device reaching its operating state. In a medical device, this matters because there may be a requirement for the device to be ready within a certain time after power-on — for example, a monitoring device that must begin acquiring data quickly. I'd also consider whether the load itself draws current during startup — if the microcontroller or sensors initialize before the rail is fully settled, that could cause unpredictable behavior.

Another consideration is whether the soft-start should be active on every power-up or only during hot-plug events. For battery-powered devices, the battery's own internal resistance provides some natural inrush limiting, but for devices powered from external supplies or backplanes, a dedicated soft-start circuit is more critical. I'd also verify the soft-start behavior across temperature, since the MOSFET's threshold voltage and the RC time constant both drift with temperature.

**Possible follow-ups:**
- How would you verify that your soft-start circuit actually limits inrush current to the calculated value, and what test setup would you use?
- What happens if the device is power-cycled rapidly — would your soft-start circuit behave correctly, and how would you handle that scenario?

---

## Q2: Walk me through how you would debug a circuit where a 3.3V rail measures correctly at the power supply output but drops to 2.9V at the load IC's power pin, and the drop only appears when the IC is actively processing data.

**Answer:** This is a classic IR-drop or impedance problem that only manifests under dynamic load. I'd approach it systematically.

First, I'd confirm the measurement itself — measuring at the IC pin with a scope probe, not a multimeter, because the drop may be transient. I'd want to see the waveform: is it a steady DC offset, or is it a droop that coincides with processing bursts?

If the drop correlates with processing activity, the likely causes are: (1) excessive resistance in the power path (narrow trace, via resistance, ferrite bead, or connector contact resistance), (2) insufficient decoupling capacitance near the IC, or (3) the upstream regulator's transient response being too slow.

I'd measure the voltage at intermediate points along the path — at the regulator output, after the ferrite bead, at the via transition, and finally at the IC pin. This isolates where the drop occurs. If the drop is across the ferrite bead, its DC resistance may be higher than expected, or it may be saturating under the transient current. If the drop is across the PCB trace, I'd calculate the trace resistance using the copper weight and dimensions — a 10 mil trace, 1 oz copper, and 2 inches long has roughly 100 mΩ, which at 1A transient gives 100 mV of drop.

I'd also check the decoupling network. If the bulk capacitor is too far from the IC, the parasitic inductance of the trace between them limits how quickly charge can be delivered. The solution might be adding a smaller, closer capacitor (e.g., 100 nF or 1 µF in a small package) to handle the high-frequency portion of the transient, while the bulk capacitor handles the longer-duration droop.

Finally, I'd verify the regulator's transient response. A regulator with a slow loop bandwidth may not respond quickly enough to a load step, causing a droop that the output capacitors must cover. If the capacitors are insufficient, the droop will be larger than acceptable.

**Possible follow-ups:**
- How would you determine whether the issue is trace resistance versus insufficient decoupling, and what measurements would distinguish between them?
- If the drop is caused by the ferrite bead, how would you select a replacement that solves the problem without compromising EMI filtering?

---

## Q3: How would you approach designing an analog multiplexer front-end for a medical device that must sample multiple sensor channels with a single ADC, where the sensors have significantly different source impedances (ranging from 1 kΩ to 100 kΩ)?

**Answer:** The core challenge here is that the multiplexer's settling time depends on the source impedance and the ADC's input capacitance. When switching between channels, the ADC's sampling capacitor must charge through the source impedance, and the RC time constant determines how long you must wait before the conversion is valid.

My approach would start by calculating the worst-case settling time: τ = (R_source + R_mux) × C_sample. For a 100 kΩ source and a typical 10 pF sampling capacitor, τ is 1 µs. For 16-bit accuracy, you need roughly 11 time constants to settle within 1 LSB, which gives 11 µs — that's substantial if you're sampling many channels.

To mitigate this, I'd consider several options. First, adding a unity-gain buffer amplifier between the multiplexer and the ADC. The buffer presents a low, consistent output impedance (typically < 1 Ω) to the ADC, making the settling time independent of the sensor's source impedance. The trade-off is added cost, board area, and the buffer's own offset and noise contributions.

Second, I'd look at the multiplexer's charge injection. When the mux switches channels, it injects a small charge into the signal path, which creates a voltage glitch that must settle before conversion. The glitch amplitude depends on the mux's charge injection specification and the source impedance — higher source impedance means the glitch takes longer to dissipate.

Third, I'd consider the sampling strategy. If the ADC has a programmable sampling time, I'd ensure it's set long enough for the worst-case channel. Alternatively, I could sample the highest-impedance channel first and use the settling time of the other channels to hide the delay.

Finally, I'd think about the system-level trade-off between settling time and throughput. If the device needs to sample many channels rapidly, the buffer approach is almost mandatory. If throughput is less critical, a longer sampling time with careful PCB layout (minimizing parasitic capacitance at the mux output) may suffice.

**Possible follow-ups:**
- How would you characterize the actual settling time of your front-end in the lab, and what test signal would you use?
- What happens if one of the sensors has a much higher source impedance than the others — would you treat that channel differently?

---

## Q4: How would you approach designing a low-noise linear regulator stage for a medical device's analog front-end, where the input is a switching regulator output and the analog circuitry requires both low noise and good PSRR across a wide frequency range?

**Answer:** The key challenge is that switching regulators produce noise at the switching frequency and its harmonics, plus broadband noise from the control loop. The linear regulator must attenuate this noise sufficiently that it doesn't degrade the analog front-end's performance.

My approach would start with a noise budget. I'd determine the analog front-end's allowable supply-induced noise — for example, if the ADC has 10 µV of input-referred noise and the PSRR of the analog chain is 60 dB, then the supply noise must be below a certain level. This gives me a target for the linear regulator's output noise and PSRR.

For the regulator selection, I'd look at three key parameters: output noise density (typically specified in nV/√Hz), PSRR across frequency, and transient response. A low-dropout regulator with a quiet bandgap reference is essential. Some regulators have excellent PSRR at low frequencies but degrade at higher frequencies — I'd check the PSRR curve, not just the DC value.

The input filtering matters as much as the regulator itself. I'd place a ferrite bead or small inductor between the switching regulator output and the linear regulator input, forming an LC filter with the input capacitor. This attenuates the high-frequency switching noise before it reaches the linear regulator. The ferrite bead's impedance should peak at the switching frequency and its harmonics.

The output capacitor selection is also critical. The output capacitor and the regulator's internal error amplifier form a control loop — the capacitor's ESR and ESL affect both stability and noise. I'd use a low-ESR ceramic capacitor, but I'd also consider whether a small RC filter at the regulator output provides additional high-frequency attenuation without affecting stability.

Finally, I'd think about the PCB layout. The linear regulator's ground pin must connect to the analog ground plane at a single point, and the output trace should be routed away from the switching regulator's inductor and switch node to avoid magnetic coupling. I'd also verify the design with a spectrum analyzer measurement of the output noise, comparing it against the noise budget.

**Possible follow-ups:**
- How would you choose between a single high-PSRR LDO versus a two-stage approach (e.g., an LC filter followed by an LDO)?
- What measurements would you take to verify that the linear regulator's output noise meets the analog front-end's requirements?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes moving the device's calibration from a one-time factory calibration to a periodic self-calibration that runs during device startup. The firmware lead argues this will improve long-term accuracy by compensating for component drift. You're concerned that the self-calibration routine requires a stable, known reference condition that may not exist at device startup — for example, the sensor may not be at a known temperature, or the device may be in motion. How would you handle this disagreement?

**Answer:** I'd approach this as a collaborative engineering problem rather than a disagreement to be won. The firmware lead's underlying goal — improving long-term accuracy by compensating for drift — is valid, and I'd acknowledge that. My concern is specifically about the validity of the calibration reference at startup.

First, I'd ask the firmware lead to walk me through the proposed calibration procedure in detail: what reference is used, what conditions are assumed, and what happens if those conditions aren't met. This helps me understand whether my concern is valid or whether they've already considered the reference stability issue.

If the concern is valid, I'd propose a middle ground. For example, instead of calibrating at every startup, the device could perform a calibration only when it detects that conditions are stable — perhaps after a warm-up period, or when the sensor is known to be at a reference temperature. Alternatively, the device could store the last successful calibration and use it until a new one can be reliably performed.

I'd also suggest a data-driven approach: implement the self-calibration in a way that logs the calibration results and the conditions at the time of calibration. After field data is collected, we can analyze whether the calibration is actually improving accuracy or introducing errors. This turns the disagreement into an experiment that can be evaluated with real data.

If we still can't agree, I'd escalate to the project's risk management process. In a medical device, calibration errors could affect patient safety, so this is a legitimate concern for the risk file. I'd propose a formal risk assessment that evaluates both approaches — the risk of drift without recalibration versus the risk of incorrect calibration at startup — and let the data and risk analysis drive the decision.

**Possible follow-ups:**
- What specific conditions would you require before accepting a self-calibration approach, and how would you verify those conditions are met?
- How would you design a test protocol to compare the factory-calibration-only approach against the self-calibration approach in terms of long-term accuracy?