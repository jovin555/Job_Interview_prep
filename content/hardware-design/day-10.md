# hardware-design — Day 10

## Q1: How would you approach designing a buck-boost converter for a medical device powered by a 2-cell Li-ion battery pack (5.0–8.4V), where the output must be a regulated 5V rail and the load can draw up to 1.5A during motor actuation but only 50mA in standby?

**Answer:** The first decision is whether a true buck-boost topology is actually needed or whether the input range can be managed differently. With a 2-cell pack, the nominal voltage is 7.4V, so a buck converter alone would cover most of the discharge curve—but the output would drop below 5V once the pack falls below roughly 5.5V, which wastes usable battery capacity. A buck-boost is justified here to extract energy from the full discharge range.

For the topology itself, I'd evaluate three options: a four-switch synchronous buck-boost (single inductor), a SEPIC, or a two-stage approach (boost followed by buck). The four-switch synchronous topology is usually the best fit for this power level—it's efficient across the whole input range, uses a single inductor, and modern controllers handle the mode transitions (buck, boost, and buck-boost) seamlessly. SEPIC is simpler in some ways but typically less efficient and has higher component stress. A two-stage approach doubles the conversion losses.

Key design considerations would include: inductor selection based on the worst-case current ripple in both buck and boost modes (saturation current must exceed peak current plus margin), compensation design that remains stable across mode transitions, and output voltage ripple—especially since the load steps from 50mA to 1.5A during motor actuation. The transient response requirement is critical: the output must stay within regulation during the load step, which means the loop bandwidth and output capacitance need to be sized together. I'd also pay attention to the transition region where the converter switches between buck and boost modes—some controllers have a dead-zone or hysteresis here that can cause output glitches.

For a medical device, I'd also consider the EMI implications. The switching node voltage swings across the full input range, so the layout needs careful attention to minimize loop area. I'd add an input filter to prevent conducted emissions from coupling back into the battery lines, and I'd verify that the switching frequency doesn't create beat frequencies with other clocks on the board.

**Possible follow-ups:**
- How would you handle the mode transition region to avoid output voltage glitches?
- What inductor parameters would you prioritize, and how would you verify saturation margin over temperature?

---

## Q2: Walk me through how you would debug a circuit where a precision instrumentation amplifier's output is noisy (peak-to-peak noise is 3× the expected value) even though the input is shorted to the reference voltage, and the power supply ripple is within specification.

**Answer:** When an instrumentation amplifier shows excessive noise with a shorted input, the problem is almost never the amplifier itself—it's something in the surrounding circuit or measurement setup. I'd approach this systematically.

First, I'd verify the measurement setup. A shorted input should produce noise dominated by the amplifier's input voltage noise and the gain-setting resistor's thermal noise. If I'm measuring with an oscilloscope, I need to check that the probe is properly grounded and that I'm not picking up ambient interference. A spectrum analyzer or FFT of the output would help distinguish between broadband noise (possibly a real circuit issue) and discrete spectral peaks (likely interference or oscillation).

Next, I'd check the reference pin. Many instrumentation amplifiers have a reference input that sets the output common-mode level. If this pin is left floating or connected through a high-impedance path, noise on the reference will appear directly at the output. I'd verify that the reference is properly driven with a low-impedance source and adequately decoupled.

Then I'd examine the power supply pins. Even if the supply ripple is within specification at the supply output, the ripple at the amplifier's pins could be higher due to trace inductance and inadequate decoupling. I'd check the decoupling capacitor placement—they should be as close to the pins as possible, with a small-value capacitor (e.g., 0.1µF) for high-frequency decoupling and a larger bulk capacitor nearby. I'd also check the ground connection: if the amplifier's ground pin connects to a noisy digital ground, that noise will couple into the output.

Another common culprit is the gain-setting resistor. If it's a discrete resistor, its thermal noise contributes directly to output noise. But more importantly, if the resistor has parasitic inductance or capacitance, it can create a resonant circuit with the amplifier's input capacitance, potentially causing peaking in the noise response. I'd check the resistor's value and type—metal film resistors are generally better than thick-film for low noise.

Finally, I'd check for oscillation. An instrumentation amplifier with a capacitive load can oscillate, and the oscillation might not be obvious on a time-domain trace if it's at a high frequency. I'd check the output with a wide-bandwidth scope and look for any high-frequency ringing or spurs in the spectrum.

**Possible follow-ups:**
- How would you distinguish between conducted noise on the supply and radiated interference?
- What if the noise appears only when the gain is set to a specific value?

---

## Q3: How would you approach designing a battery fuel gauge for a medical device that must report remaining capacity with ±5% accuracy, using a Li-ion battery, when the device has variable loads (sensor bursts, wireless transmission, and sleep modes)?

**Answer:** Fuel gauging in a medical device is challenging because the accuracy requirement is meaningful—clinicians may rely on the reading to decide whether to replace or recharge the device, and an inaccurate reading could lead to unexpected shutdown during use.

The first decision is between voltage-based and coulomb-counting (charge integration) methods. Voltage-based estimation is simple but inaccurate under variable loads because the battery voltage sags differently depending on current draw and temperature. Coulomb counting is more accurate but requires a sense resistor and integration over time, and it drifts if not periodically recalibrated. For a medical device with ±5% accuracy under variable loads, I'd use a hybrid approach: coulomb counting as the primary method, with voltage-based correction at known states (e.g., when the device enters a stable low-current sleep mode, the open-circuit voltage can be used to recalibrate).

For the implementation, I'd select a fuel gauge IC that integrates coulomb counting, voltage measurement, and temperature sensing. The IC should support a low-value sense resistor (e.g., 10mΩ) to minimize power loss, and it should have a sleep mode that consumes minimal current itself. The gauge's accuracy depends on the battery's characteristics, so I'd need to characterize the battery's discharge curves at multiple temperatures and load profiles to build or validate the model.

The key challenge is handling the variable load profile. The gauge needs to track charge flow accurately during high-current bursts (wireless transmission) and low-current periods (sleep). The sense resistor's value and the gauge's ADC resolution determine the minimum current that can be accurately measured. I'd also need to account for the battery's internal resistance, which causes voltage sag under load—the gauge should compensate for this when estimating remaining capacity.

Temperature compensation is critical. Li-ion capacity decreases at low temperatures, and the discharge curve shifts. The gauge should have a temperature sensor (either internal or external) and apply temperature correction factors. I'd also implement a "learning" algorithm that updates the battery's full-charge capacity based on observed charge/discharge cycles, since the actual capacity degrades with age.

For the medical device context, I'd also consider safety: the gauge should be able to detect fault conditions (overcurrent, over-temperature, short circuit) and communicate with the system's protection circuitry. And I'd design the reporting to be conservative—if the gauge is uncertain, it should err on the side of reporting less capacity rather than more.

**Possible follow-ups:**
- How would you handle the initial calibration of the fuel gauge, and how often would you recalibrate?
- What if the battery is user-replaceable—how would the gauge handle a new battery with different characteristics?

---

## Q4: How would you approach designing a watchdog circuit for a medical device's microcontroller that must be independent of the main processor and must reliably reset the system if the firmware hangs, while avoiding false resets during normal operation?

**Answer:** A watchdog in a medical device is a safety mechanism—it must catch firmware hangs without disrupting normal operation. The design has two parts: the hardware watchdog circuit itself and the firmware "kick" mechanism.

For the hardware, I'd first decide between an internal watchdog (inside the MCU) and an external watchdog IC. An external watchdog is generally preferred for medical devices because it's independent of the MCU—if the MCU's clock fails or the internal watchdog circuitry is corrupted, the external watchdog still operates. I'd select a watchdog IC with a programmable timeout period, typically in the range of 1–10 seconds, depending on the device's worst-case normal operation cycle.

The timeout period is critical. It must be long enough that the firmware can always kick the watchdog during normal operation—even under worst-case conditions like a lengthy sensor read or wireless transmission—but short enough that a hang is detected quickly. I'd analyze the firmware's execution paths to determine the maximum time between kicks during normal operation, then set the timeout to at least 2× that value for margin.

The kick mechanism is where many designs fail. The firmware should kick the watchdog based on a "heartbeat" that indicates the system is functioning correctly, not just that the interrupt handler is running. A common approach is to have the main loop or a high-priority task kick the watchdog only after completing a sequence of operations (e.g., reading sensors, checking communication, verifying memory). This way, if the firmware is stuck in a loop but interrupts are still running, the watchdog still fires.

I'd also consider the watchdog's behavior during low-power modes. If the device enters a sleep mode for extended periods, the watchdog must either be disabled or have a very long timeout. Some watchdog ICs have a "sleep mode" input that pauses the timeout. I'd design the firmware to put the watchdog in sleep mode when the MCU enters low-power state, and wake it when the MCU wakes.

For the reset output, I'd use a push-pull output that drives the MCU's reset pin. I'd also add a reset pulse stretcher to ensure the MCU sees a valid reset pulse even if the watchdog's output is brief. And I'd consider adding a "reset cause" indicator—the watchdog IC can have a flag that the firmware reads after reset to determine whether the reset was caused by a watchdog timeout or a power-on reset, which helps with debugging.

Finally, I'd verify the watchdog's behavior during power-up. The watchdog should start timing only after the supply voltage is stable, and it should not fire during the MCU's initial boot sequence. Some watchdog ICs have a "startup delay" that gives the MCU time to initialize before the watchdog begins counting.

**Possible follow-ups:**
- How would you test the watchdog's reliability—how would you verify it catches a firmware hang?
- What if the firmware needs to perform a lengthy operation (e.g., a firmware update) that takes longer than the watchdog timeout?

---

## Q5: (Behavioral) Imagine you're leading the hardware design for a medical device that uses a new wireless communication module. During integration testing, you discover that the module's radiated emissions are causing intermittent errors in the device's high-resolution ADC readings. The module vendor says the emissions are within their datasheet specifications, and the firmware lead suggests adding a software filter to suppress the errors. How would you handle this situation?

**Answer:** This is a classic integration problem where the interaction between two subsystems creates a failure that neither subsystem exhibits in isolation. The first thing I'd do is characterize the problem precisely—I need to understand the mechanism before I can choose a solution.

I'd start by measuring the ADC errors and correlating them with the wireless module's activity. Are the errors occurring only during transmission bursts, or also during reception? What's the frequency and amplitude of the interference at the ADC's input? I'd use a spectrum analyzer to look at the emissions from the wireless module and compare them with the ADC's susceptibility—the ADC's input bandwidth and sampling frequency determine which frequencies can alias into the passband.

Once I understand the coupling path, I'd evaluate options. The vendor saying the emissions are within spec doesn't mean the module is suitable for this application—the spec is for the module in isolation, not in a system with a sensitive ADC. But I also wouldn't immediately reject the module; the issue might be solvable with good engineering.

The firmware lead's suggestion of a software filter is worth considering, but I'd be cautious. A software filter can suppress the errors if the interference is at a known frequency and the filter doesn't degrade the ADC's measurement accuracy. However, if the interference is broadband or if the filter reduces the effective resolution, it might not be acceptable for a medical device. I'd also consider that a software filter is a "mask" rather than a fix—if the interference mechanism isn't understood, the filter might not be robust across all operating conditions.

The hardware options include: improving the PCB layout to reduce coupling (e.g., better grounding, shielding the ADC section, adding a guard trace between the wireless module and the ADC), adding filtering at the ADC's input (e.g., a low-pass filter to reject the wireless frequencies), or adding shielding around the wireless module. I'd also consider the antenna placement—if the antenna is close to the ADC's analog input traces, moving it or reorienting it could significantly reduce coupling.

I'd approach this as a collaborative problem-solving exercise. I'd present the data to the firmware lead and the vendor, explain the trade-offs of the software filter approach, and propose a plan: first, implement a temporary software filter to confirm the mechanism (does it eliminate the errors?), then work on the hardware fix to reduce the coupling at the source. The goal is to have both a short-term mitigation and a long-term robust solution.

If the vendor is unwilling to help, I'd document the issue thoroughly and escalate within the project team. The decision ultimately depends on the project timeline and the severity of the issue—if the hardware fix is straightforward, I'd prioritize it; if it requires a board revision, I'd implement the software filter as a temporary measure while planning the revision.

**Possible follow-ups:**
- How would you decide whether the software filter alone is acceptable for a medical device, or whether a hardware fix is mandatory?
- How would you communicate the issue to the vendor and what would you ask them to do?