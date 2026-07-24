# debugging-failure-analysis — Day 4

## Q1: A medical device passes all functional tests at room temperature but consistently fails when placed in an environmental chamber at 40°C. How would you approach this thermal-related failure?

**Answer:** I'd start by confirming the failure is truly temperature-dependent and not a humidity or condensation issue, since environmental chambers often control both. I'd run the test at 40°C with controlled low humidity first, then repeat with elevated humidity to isolate the variable.

Once confirmed as temperature-related, I'd use a divide-and-conquer approach. I'd instrument the board with thermocouples at key locations — the processor, voltage regulators, sensors, and any oscillators or PLLs — while monitoring critical signals with an oscilloscope inside the chamber (or using extended cables to keep test equipment outside). I'd look for several common failure modes:

- **Voltage regulator dropout or thermal shutdown**: Some LDOs have thermal foldback that activates well below their absolute maximum junction temperature. I'd check if output rails sag as the chamber temperature rises.
- **Oscillator drift**: Crystal oscillators have temperature coefficients. If the system uses a PLL that loses lock when the reference drifts beyond the capture range, that could cause intermittent failures.
- **Component derating violations**: A capacitor's capacitance drops with temperature (especially Class 2 dielectrics like X5R/X7R), which could cause a decoupling network or timing circuit to go out of spec.
- **Thermal expansion causing intermittent connections**: BGA solder joints, connectors, or press-fit components might lose contact at elevated temperature.

I'd also check if the failure correlates with a specific temperature threshold or occurs gradually. If it's a hard threshold, I'd look for a component with a thermal shutdown or protection feature that's triggering. If it's gradual, I'd look for analog parameters drifting out of tolerance.

**Possible follow-ups:** How would you distinguish between a component-level thermal issue and a system-level thermal management problem (e.g., inadequate heat sinking or airflow)? What if the failure only occurs during the transition from cold to hot, not at steady-state temperature?

---

## Q2: How would you approach debugging a signal integrity issue where a high-speed SPI bus between a microcontroller and an ADC shows intermittent bit errors, but only when the device's motor driver is active?

**Answer:** This sounds like a classic EMI coupling problem where the motor driver's switching noise couples into the SPI bus. I'd approach it systematically:

First, I'd characterize the noise source. I'd probe the motor driver's switching nodes (FET gate drives, phase outputs) with a scope to understand the switching frequency, rise/fall times, and voltage transients. I'd also measure the motor current waveform to see if there's a correlation between current spikes and SPI errors.

Next, I'd examine the SPI signals themselves. I'd use a differential probe or ground-spring technique to measure the SPI clock, MOSI, MISO, and chip select lines with the motor both on and off. I'd look for:
- Noise coupled onto the clock line causing extra edges or jitter
- Ground bounce shifting the logic thresholds
- Common-mode noise that exceeds the receiver's input range

I'd then try to identify the coupling path. The three possibilities are:
- **Conducted coupling**: The motor driver and SPI share a power rail or ground return path. I'd check if adding a ferrite bead or LC filter on the motor driver's supply reduces the errors.
- **Radiated coupling**: The motor cables or PCB traces act as antennas. I'd try rerouting the SPI traces away from motor traces, adding ground guard traces, or using shielded cables for the motor.
- **Capacitive/inductive coupling**: Proximity between the SPI bus and high-current motor traces. I'd check the PCB layout for parallel runs.

A practical first step would be to slow down the SPI clock to see if the error rate drops — that would confirm noise coupling rather than a timing issue. I'd also try adding series resistors on the SPI lines to dampen ringing, or enabling Schmitt trigger inputs if the microcontroller supports them.

**Possible follow-ups:** What if the SPI bus is already running at the minimum acceptable speed for the ADC's data rate? How would you decide between hardware fixes (layout changes, shielding) and firmware workarounds (CRC, retransmission)?

---

## Q3: A field-returned medical device shows intermittent resets, and your analysis points to the watchdog timer expiring. The firmware team insists the code is correct and the watchdog timeout is set appropriately. How would you approach resolving this cross-team disagreement and finding the real root cause?

**Answer:** This is as much a collaboration challenge as a technical one. I'd start by reframing the conversation from "who's wrong" to "what's the system doing." The watchdog expiring means the firmware isn't servicing it in time — that could be a firmware bug, but it could also be a hardware issue preventing the firmware from running normally.

I'd propose a joint debugging session with the firmware engineer, focusing on evidence rather than opinions. Here's my technical approach:

First, I'd instrument the system to capture the state at the time of the watchdog reset. If the microcontroller has a reset cause register, I'd read it to confirm the watchdog was the source. I'd also look at the stack pointer and program counter from the reset vector if the chip preserves them.

Then I'd try to reproduce the issue on the bench with additional monitoring:
- I'd monitor the power rails with an oscilloscope, looking for glitches or brownouts that could cause the microcontroller to hang or execute corrupted instructions. A 1-2ms power dip could cause a crash without fully resetting the chip.
- I'd monitor the reset pin for noise or spurious assertions.
- I'd check the clock signal — a glitch on the oscillator could cause the firmware to execute invalid instructions or get stuck in a loop.
- I'd probe the watchdog's own input to verify it's actually being serviced at the expected interval.

If the hardware looks clean, I'd work with the firmware team to add diagnostic code — perhaps a circular buffer that logs the last N function calls or state transitions before a reset. This could reveal if the firmware is getting stuck in a particular code path, waiting on a peripheral that's not responding, or hitting an unexpected interrupt storm.

The key is to approach this as a joint investigation: "Let's look at the data together and see what it tells us." I'd also suggest swapping a known-good board into the field unit's enclosure to rule out mechanical issues like loose connectors or intermittent shorts.

**Possible follow-ups:** What if the firmware team is unwilling to add diagnostic code because of code size constraints or certification concerns? How would you handle a situation where the issue only occurs in the field and you can't reproduce it in the lab?

---

## Q4: How would you approach debugging a situation where a newly assembled batch of PCBs shows a 5% failure rate on the production test fixture, with all failures exhibiting the same symptom — a specific sensor reading is consistently out of specification?

**Answer:** A 5% failure rate with a consistent symptom suggests a process variation or component tolerance issue rather than a random defect. I'd approach this in stages:

**Stage 1 — Characterize the failure**: I'd take several failing units and several passing units, and compare them systematically. I'd measure:
- The sensor's output voltage or digital reading under controlled conditions
- The sensor's supply voltage and reference voltage
- The analog signal chain from sensor through any amplifiers/filters to the ADC
- The PCB assembly quality — solder joints, component alignment, cleanliness

**Stage 2 — Identify the variable**: Since it's a batch-level issue, I'd look for what changed. I'd check:
- Component date codes and manufacturers — did the sensor or a supporting component come from a different reel or supplier?
- Reflow oven profiles for this batch versus previous batches
- Stencil thickness and solder paste application
- Any manual assembly steps that could introduce variation

**Stage 3 — Component-level investigation**: If the sensor reading is consistently off in the same direction (always high or always low), I'd look at the sensor's bias circuit. For example, if the sensor requires an external reference resistor and that resistor's tolerance is critical, a batch of resistors at the edge of their tolerance band could shift all readings. I'd measure the actual resistor values in failing units versus passing units.

**Stage 4 — Statistical analysis**: I'd check if the failures correlate with specific positions on the panel (e.g., always the same location on the PCB panel, suggesting a reflow temperature gradient) or with specific assembly lots (e.g., all failures from the same shift or machine).

**Stage 5 — Root cause confirmation**: Once I have a hypothesis, I'd verify it by:
- Replacing the suspected component on a failing unit with one from a passing unit to see if the failure moves
- Measuring the parameter that's out of spec (e.g., reference voltage) across multiple units to see the distribution
- Checking the component manufacturer's datasheet for any application notes about sensitivity to PCB layout or soldering

**Possible follow-ups:** How would you decide whether to rework the failing units or scrap them? What if the root cause turns out to be a component that's within its datasheet specifications but marginal for this particular design?

---

## Q5: A medical device has been returned from the field with reports of intermittent "no reading" errors from a pressure sensor. The device logs show the error occurs randomly, sometimes days apart. How would you approach this intermittent failure investigation?

**Answer:** Intermittent failures that occur days apart are among the most challenging to debug. I'd approach this with a combination of data analysis, fault injection, and extended monitoring.

**Phase 1 — Mine the existing data**: Before touching the hardware, I'd analyze the device's logs in detail. I'd look for patterns:
- Does the error correlate with time of day, device orientation, or patient usage patterns?
- Are there any other logged events around the same time — temperature changes, battery voltage dips, communication errors?
- What's the time interval between the last valid reading and the error? Is it always the same?
- Does the error self-recover, or does it require a power cycle?

**Phase 2 — Physical inspection and baseline measurements**: I'd carefully inspect the returned device — looking for signs of moisture ingress, corrosion, mechanical stress on the sensor's pressure port, or damaged cables. I'd then characterize the sensor's performance under controlled conditions: accuracy, noise floor, response time, and supply current.

**Phase 3 — Hypothesis generation and fault injection**: Based on the data, I'd form hypotheses about the root cause and design tests to reproduce it:
- **Intermittent connection**: If the sensor uses a connector or flex cable, I'd try vibration testing, thermal cycling, or flexing the cable while monitoring the sensor output.
- **Moisture sensitivity**: I'd test the sensor in a controlled humidity chamber, especially if the device is used in a clinical setting where it might be exposed to fluids.
- **ESD or transient events**: I'd apply ESD pulses to the enclosure or connected cables while monitoring the sensor bus.
- **Power supply noise**: I'd inject ripple onto the sensor's supply rail at various frequencies and amplitudes.
- **Component aging**: If the device has been in the field for a while, I'd check if the failure correlates with operating hours or power cycles.

**Phase 4 — Extended monitoring**: If I can't reproduce the failure quickly, I'd set up a long-term automated test that cycles the device through its normal operating conditions while logging the sensor output continuously. I'd use a data acquisition system that can capture the sensor's raw signal at high resolution, not just the processed reading, so I can see if the error is preceded by noise, drift, or intermittent dropouts.

**Phase 5 — Root cause analysis**: Once I reproduce the failure, I'd use an 8D process to document the root cause, define corrective actions, and implement preventive measures — which might include component qualification changes, design modifications, or manufacturing process improvements.

**Possible follow-ups:** How would you prioritize which returned devices to analyze first if you have multiple field returns with different symptoms? What if the failure cannot be reproduced after weeks of testing — how would you make a risk-based decision about whether to redesign the sensor interface?