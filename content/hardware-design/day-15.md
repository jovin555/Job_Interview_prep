# hardware-design — Day 15

## Q1: How would you approach designing a hardware-based over-temperature protection circuit for a medical device that uses a high-power motor driver, where the protection must be independent of the main microcontroller and must respond within milliseconds?

**Answer:** The key requirement here is that protection must be independent of the main processor — if the firmware hangs or the MCU is resetting, the protection still needs to work. I'd start by defining the failure scenario: what temperature threshold triggers shutdown, how fast the temperature can rise under a fault condition (e.g., a stalled motor), and what the safe state should be (typically removing gate drive from the motor driver).

For the sensing element, I'd use a thermistor or a temperature-sensing IC with a comparator rather than relying on the MCU's ADC. The comparator's reference voltage sets the trip point, and I'd add hysteresis to prevent oscillation around the threshold — otherwise the system could rapidly cycle on and off, which is worse than staying off. The comparator output would drive a latching circuit or directly gate the motor driver's enable pin.

A critical design consideration is the response time. A thermistor has thermal mass and may not respond quickly enough to a fast temperature rise. In that case, I'd consider adding a secondary protection based on a parameter that responds faster — for example, motor current sensing. If the motor stalls, current spikes immediately, and an overcurrent comparator can shut down the driver in microseconds, well before the temperature rises to dangerous levels. The thermal protection then serves as a backup for slower overload conditions.

I'd also think about the fail-safe behavior. If the temperature sensor fails open or short, what happens? I'd design the circuit so that a sensor failure results in a safe state — for example, using a pull-up that forces the comparator output to the shutdown state if the thermistor opens. Finally, I'd verify the protection path is truly independent: separate power supply filtering, no shared traces with the MCU's circuitry, and the protection logic should be in hardware, not dependent on firmware configuration.

**Possible follow-ups:**
- How would you test that the protection circuit responds correctly under a real fault condition without damaging the device?
- What if the comparator itself fails — how would you design for that failure mode?

---

## Q2: How would you approach selecting the output capacitor for a boost converter that supplies a load with fast current transients (e.g., a wireless radio that bursts 200 mA for 5 ms), where the output voltage must stay within ±3% of 5V?

**Answer:** The output capacitor in a boost converter serves two roles: stabilizing the control loop and supplying energy during load transients before the converter's control loop can respond. For a fast transient, the control loop bandwidth is typically too low to respond within microseconds, so the capacitor must supply the initial energy deficit.

I'd start by calculating the energy requirement. For a 200 mA step for 5 ms with a 150 mV allowable droop (3% of 5V), the charge needed is roughly I × t = 200 mA × 5 ms = 1 mC. The capacitance required is approximately Q/ΔV = 1 mC / 150 mV ≈ 6.7 mF — but that's a worst-case estimate that ignores the converter's ability to deliver current during the transient. In practice, the converter will contribute some current, so I'd use a smaller value and verify with simulation.

The more important consideration is the capacitor's ESR and ESL. A ceramic capacitor with low ESR will handle the high-frequency component of the transient, but ceramics have limited capacitance per footprint and their capacitance drops with DC bias — a 22 µF ceramic might only provide 10 µF at 5V bias. I'd likely use a combination: a bulk electrolytic or polymer capacitor for the energy storage (higher capacitance, higher ESR) and a ceramic capacitor in parallel for the high-frequency response.

I'd also check the capacitor's ripple current rating. The boost converter's inductor current is pulsed, and the output capacitor must handle the RMS ripple current without overheating. For a 5V output at 200 mA average, the ripple current can be several hundred mA RMS, which is fine for most ceramics but needs checking for electrolytics.

Finally, I'd verify the control loop stability with the chosen capacitor. Boost converters in continuous conduction mode have a right-half-plane zero that complicates compensation, and a large output capacitor can shift the pole frequencies. I'd simulate the loop with the actual capacitor model (including ESR and ESL) and verify phase margin across load and input voltage ranges.

**Possible follow-ups:**
- How would the choice differ if the load transient were 1 µs instead of 5 ms?
- How would you verify the capacitor's DC bias derating for the specific voltage and temperature range?

---

## Q3: Walk me through how you would debug a circuit where a 12-bit DAC's output voltage is correct when measured with a high-impedance multimeter, but the downstream ADC reads values that are consistently 20–30 LSB low, and the error increases with the DAC's output code.

**Answer:** This symptom — correct voltage at the DAC output but low readings at the ADC — points to a loading problem between the two devices. The multimeter has very high input impedance, so it doesn't load the DAC output. The ADC's input, however, may present a significant load, especially if it's a SAR ADC with a switched-capacitor input that draws charge from the source during sampling.

The fact that the error increases with output code is a key clue. At higher DAC output voltages, the DAC's output amplifier may be sourcing more current, and if there's a series resistance between the DAC and ADC — perhaps from a filter resistor or a poorly chosen multiplexer — the voltage drop across that resistance becomes larger at higher currents. I'd first check the schematic for any series components between the DAC and ADC, and verify their values.

I'd also look at the ADC's input architecture. A SAR ADC's input capacitance charges during the acquisition phase, and if the source impedance is too high, the input capacitor doesn't fully charge to the input voltage within the acquisition time. The result is a systematic error that increases with the input voltage — exactly matching the symptom. The solution is either to reduce the source impedance, increase the acquisition time, or add a buffer amplifier between the DAC and ADC.

Another possibility is that the ADC's reference voltage is being loaded. If the DAC and ADC share a reference, and the DAC's output stage draws current from the reference through a shared trace, the reference voltage could droop when the DAC outputs a high code. I'd check the reference voltage at the ADC's reference pin while sweeping the DAC code — if it droops, that's the problem.

My debugging approach would be: first, measure the voltage at the ADC's input pin (not the DAC output) with the ADC actively sampling — this requires an oscilloscope probe with sufficient bandwidth. If the voltage at the ADC input is lower than at the DAC output, there's a series impedance or the ADC is loading the source. I'd then check the ADC's datasheet for the input impedance and required source impedance for the given acquisition time, and compare with the actual circuit.

**Possible follow-ups:**
- How would you determine whether the issue is the source impedance or the ADC's acquisition time?
- What if the error only appears at higher temperatures — how would that change your analysis?

---

## Q4: How would you approach designing a power supply decoupling strategy for a board that has both a high-resolution sigma-delta ADC and a Class D audio amplifier, where the amplifier's switching frequency is 400 kHz and the ADC's modulator runs at 2.5 MHz?

**Answer:** This is a challenging coexistence problem because the Class D amplifier is a high-current switching load that can inject noise into the power rails, and the sigma-delta ADC is sensitive to power supply noise that can alias into its passband. The key is to prevent the amplifier's switching noise from reaching the ADC's supply and reference pins.

I'd start by separating the power domains physically and electrically. The amplifier should have its own supply rail, decoupled with bulk capacitance (e.g., 10–100 µF) and low-ESR ceramics right at its supply pins. The ADC should have a separate, clean supply rail — ideally from a dedicated LDO that provides good PSRR at both 400 kHz and 2.5 MHz. A ferrite bead between the main supply and the ADC's LDO input can provide additional high-frequency isolation, but I'd verify the bead's impedance at the relevant frequencies and its DC resistance doesn't cause excessive voltage drop.

The PCB layout is critical. I'd keep the amplifier's high-current loop (supply, output stage, ground return) physically separated from the ADC's analog section. A solid ground plane is essential, but I'd be careful about where the amplifier's ground return connects to the main ground plane — ideally at a single point near the power input, not near the ADC. The ADC's ground reference should be clean; any ground bounce from the amplifier's current pulses will shift the ADC's reference and appear as noise.

I'd also consider the frequency relationship. The amplifier's 400 kHz switching frequency and its harmonics could beat with the ADC's 2.5 MHz modulator frequency, producing intermodulation products that fall in the ADC's passband. If the ADC's digital filter has notches at multiples of the modulator frequency, I'd check whether 400 kHz and its harmonics fall near those notches. If not, I might need to add a small RC filter on the ADC's supply or adjust the amplifier's switching frequency slightly (if the design allows) to move the interference away from sensitive frequencies.

Finally, I'd verify the strategy with measurements: measure the ADC's noise floor with the amplifier idle and with it operating at full output. If the noise floor rises, I'd use a spectrum analyzer to identify the interference frequencies and trace them back to the coupling path — is it through the power supply, ground, or radiated?

**Possible follow-ups:**
- How would you decide whether to use a ferrite bead or an LC filter between the main supply and the ADC's LDO?
- What if the amplifier's switching frequency can't be changed — how would you mitigate the intermodulation products?

---

## Q5: (Behavioral) Imagine you're the lead hardware engineer on a medical device project, and during a design review, the firmware lead proposes replacing a hardware-based overcurrent protection circuit (a comparator and latch that shuts down the motor driver) with a firmware-based solution that monitors the current via the ADC and shuts down the motor through a GPIO. The firmware lead argues this will save board space, reduce cost, and allow more flexible threshold adjustment. You believe the firmware approach is unsafe because the protection must work even if the firmware hangs or the ADC fails. How would you handle this disagreement?

**Answer:** I'd approach this as a safety engineering discussion, not a personal disagreement. The core question is whether the firmware-based protection can meet the safety requirements — specifically, the response time and the failure modes. I'd start by asking the firmware lead to walk through the worst-case scenario: if the MCU is executing a tight loop or stuck in an interrupt handler, can the firmware still respond to the overcurrent condition within the required time? If the ADC reading is corrupted or the firmware is hung, the protection is lost.

I'd frame the discussion around the device's risk analysis. For a medical device with a motor driver, an overcurrent condition could lead to overheating, fire, or unintended actuation — all of which are patient safety hazards. The question is whether the risk assessment allows a single point of failure (the firmware) for this protection function. In most cases, the answer is no — you'd want the protection to be independent of the main processor, or at least have a redundant path.

Rather than simply rejecting the proposal, I'd explore whether there's a middle ground. For example, could we keep a simplified hardware comparator that provides a fast, coarse overcurrent shutdown, while the firmware provides a more precise, adjustable threshold for normal operation? The hardware comparator would be a safety net — it doesn't need to be accurate, just fast and reliable. This gives the firmware lead the flexibility they want while maintaining the safety integrity.

If we can't reach agreement, I'd escalate to the project's risk management process. The decision should be based on the documented risk analysis and the applicable safety standards, not on personal preference. I'd propose a formal risk assessment that evaluates both approaches — including failure modes, response times, and testability — and let that document drive the decision. In a regulated medical device environment, the risk management file is the ultimate authority.

**Possible follow-ups:**
- How would you test that the hardware protection circuit actually works in a fault condition, given that you don't want to damage the device during testing?
- What if the firmware lead argues that the hardware comparator adds a component that could fail — how would you respond to that failure mode argument?