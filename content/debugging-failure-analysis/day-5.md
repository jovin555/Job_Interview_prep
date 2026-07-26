# debugging-failure-analysis — Day 5

## Q1: A medical device has been returned from the field with intermittent "communication lost" errors logged between the main processor and a sensor module. The error logs don't show any pattern — sometimes hours between events, sometimes days. How would you approach this investigation?

**Answer:** I'd start by treating this as a field-return failure investigation, which means the first priority is preserving evidence and understanding the use conditions. I'd begin with a structured interview of the field service team or customer to understand the environment — was the device in continuous use, were there power events, was it moved or bumped when errors occurred? Simultaneously, I'd examine the device's non-volatile logs for any correlated events: voltage dips, temperature excursions, reset counters, or other sensor errors that might have occurred near the same timestamps.

Next, I'd perform a physical inspection of the returned unit — looking for cracked solder joints, loose connectors, corrosion, or mechanical stress marks on the sensor module interconnect. I'd measure the connector pin resistance and check for intermittent opens by flexing the board and cable while monitoring continuity.

For the electrical investigation, I'd set up a test that replicates the field configuration and run it for an extended period while monitoring the communication bus with a logic analyzer or oscilloscope, triggering on error conditions. I'd also inject controlled disturbances — power supply ripple, mechanical vibration, temperature cycling — to see if any of these reproduce the failure. If the error is related to a specific sensor reading or command sequence, I'd look for timing violations or noise on the sensor's power rail during those operations.

The key is to narrow the hypothesis space systematically: is it a hardware issue (intermittent connection, noise coupling, power integrity) or a firmware issue (race condition, buffer overflow, state machine edge case)? I'd try to reproduce the failure in a controlled setting before committing to a root cause.

**Possible follow-ups:** How would you decide whether to focus on hardware or firmware first? What specific measurements would you take on the communication bus to distinguish between a driver issue and a noise issue?

---

## Q2: How would you approach debugging a power rail that shows excessive ripple only when the device's wireless transmitter is active, but the ripple is within specification when the transmitter is idle?

**Answer:** This is a classic dynamic load interaction problem. The first step is to characterize the ripple precisely — measure it at the load's decoupling capacitors, not at the power supply output, because the impedance between them matters. I'd use a short ground-spring probe to minimize measurement artifact and capture the ripple waveform synchronized with the transmitter's on/off transitions.

I'd look at the ripple frequency content: is it at the transmitter's data rate, the switching regulator's frequency, or some beat frequency between them? If the ripple occurs at the transmitter's packet rate, the issue is likely the transient load current demand exceeding the regulator's bandwidth. If it's at the switching frequency but modulated by transmitter activity, it could be a layout or decoupling issue where the transmitter's return current path shares impedance with the power rail.

I'd then measure the load current profile of the transmitter — using a current probe or a low-side sense resistor — to understand the magnitude and slew rate of the current step when the transmitter turns on. Comparing this to the regulator's transient response specification tells me whether the regulator itself is adequate or if additional bulk decoupling is needed.

Next, I'd check the PCB layout: is the transmitter's power trace routed separately from sensitive analog circuits? Are the decoupling capacitors placed with short, low-inductance paths to the transmitter's power pins? I'd look for shared vias or long traces that create common impedance coupling.

If the ripple is still problematic, I'd try adding a ferrite bead and additional capacitance to create a pi-filter at the transmitter's power input, or consider a dedicated LDO for the transmitter if the main rail is a switching regulator. The fix depends on whether the issue is insufficient decoupling, regulator bandwidth, or layout parasitics.

**Possible follow-ups:** How would you distinguish between ripple caused by insufficient decoupling versus ripple caused by regulator instability? What measurement technique would you use to verify that your fix actually reduced the ripple at the load?

---

## Q3: A firmware engineer reports that a sensor reading occasionally returns all zeros, but only when the system has been running for more than 30 minutes. The sensor uses I2C, and the firmware includes error-checking that retries failed reads. How would you approach this as a hardware engineer?

**Answer:** This sounds like a thermal or aging-related issue that a hardware engineer should investigate in parallel with the firmware team. I'd start by instrumenting the system to capture the I2C bus traffic during the failure — a logic analyzer triggered on the all-zeros read would show whether the sensor is actually responding with zeros, or if the bus is stuck, or if there's a NACK condition.

I'd also monitor the sensor's power rail and the I2C bus voltages with an oscilloscope, looking for degradation over time. A common failure mode is that a weak pull-up resistor or marginal solder joint becomes intermittent as temperature rises and components expand. I'd measure the I2C pull-up resistor values and check if they're appropriate for the bus capacitance and speed — marginal pull-ups can cause rising-edge timing violations that get worse as temperature increases.

I'd check the sensor's datasheet for any timing parameters that have temperature dependence, like startup time or conversion time. If the firmware's retry logic is too aggressive, it might be reading before the sensor has completed a conversion, and that timing margin might shrink with temperature.

I'd also look at the sensor's supply voltage over time — if a regulator drifts or a capacitor degrades with temperature, the sensor might be operating near its brown-out threshold after 30 minutes. I'd use a thermal camera or thermocouples to identify hot spots near the sensor or its power circuitry.

Finally, I'd set up an accelerated test: run the device in a temperature chamber at the maximum specified ambient temperature and see if the failure occurs sooner. If it does, that confirms a thermal sensitivity. If not, I'd look for other time-dependent mechanisms like capacitor aging or charge pump degradation.

**Possible follow-ups:** What specific I2C bus characteristics would you check on the oscilloscope to distinguish between a sensor that's not responding versus a sensor that's returning bad data? How would you design a test to determine if the issue is in the sensor itself versus the communication path?

---

## Q4: You're investigating a production yield issue where 2% of boards fail a functional test immediately after power-up — the microcontroller doesn't start executing code. The failures are random across batches and don't correlate with any specific component lot. How would you approach this?

**Answer:** This is a classic "infant mortality" or marginal design issue. The fact that it's random and doesn't correlate with component lots suggests a design margin problem rather than a defective component. I'd start by characterizing the failing boards in detail — what exactly does "doesn't start executing" mean? I'd probe the microcontroller's power rails, reset pin, oscillator, and boot pins on a failing board and compare them to a passing board.

I'd look at the power-up sequence timing: does the reset pin de-assert after all power rails are stable? Is there a voltage monitor or supervisor IC that holds the microcontroller in reset until the supply is valid? I'd measure the rise time of the power rails and the reset delay to see if there's a race condition where the microcontroller tries to start before its oscillator is stable or before the supply has reached the minimum operating voltage.

I'd also check the oscillator startup — measure the crystal or resonator waveform at power-up. Some crystals have slow startup times, especially if the load capacitance is marginal or if there's contamination on the PCB. I'd look at the oscillator amplitude and frequency stability during the first few milliseconds.

If the power-up sequence looks correct, I'd examine the boot configuration pins — are they pulled to the correct levels with appropriate resistors? A marginal pull-up or pull-down could cause the microcontroller to boot from the wrong memory or enter a test mode.

I'd also consider the possibility of ESD damage during handling or test — even though the failures are random, a subtle ESD event could damage the microcontroller's internal power-on reset circuitry without causing catastrophic failure. I'd check the handling procedures and ESD protection on the test fixture.

The systematic approach is to create a checklist of all conditions required for the microcontroller to start (power good, reset released, oscillator running, boot configuration correct) and verify each one on multiple failing boards, looking for a consistent deviation from the passing boards.

**Possible follow-ups:** How would you design a test to determine whether the issue is in the power-up timing versus a marginal component? If you found that the reset de-asserts 2ms before the main supply reaches its final voltage, how would you determine if that's the root cause?

---

## Q5: A senior manager asks you to lead a cross-functional root-cause investigation for a critical medical device failure that occurred in the field. The device was returned with a note that it "stopped working" — no error logs, no visible damage. The project schedule is tight, and there's pressure to find a quick fix. How would you structure this investigation?

**Answer:** I'd start by establishing a structured investigation process and communicating it clearly to the team and the manager. The first step is to preserve the evidence — the device should be handled with care, photographs taken of its condition, and any non-volatile memory read out before any disassembly. I'd also gather information about the patient context: how long was the device in service, what was it doing when it failed, were there any recent service events or software updates?

Next, I'd assemble a small cross-functional team — hardware, firmware, quality, and manufacturing — and schedule a kickoff meeting to review what we know and what we don't know. I'd emphasize that we need to follow a systematic process like 8D (Eight Disciplines) to avoid jumping to conclusions. The pressure to find a quick fix is exactly when teams make mistakes by fixing symptoms rather than root causes.

I'd create a fault tree analysis covering possible failure modes: power supply failure, microcontroller failure, connector issue, firmware corruption, environmental stress, etc. Each branch of the tree would have a test or measurement that can confirm or rule out that path. I'd assign owners to each branch and set a timeline for completing the investigations.

I'd also establish a communication cadence — daily stand-ups for the investigation team and weekly updates to management — so that progress is visible and the team feels supported rather than pressured. If we find a likely cause, we'd validate it by trying to reproduce the failure in a controlled test before implementing any fix.

The key is to balance speed with rigor. I'd identify the most likely failure modes based on the device's history and field data, and prioritize those investigations. But I'd also ensure we don't close the investigation until we have a confirmed root cause and a corrective action that prevents recurrence, not just a band-aid fix.

**Possible follow-ups:** How would you handle a situation where the team identifies two plausible root causes and can't agree on which one to pursue first? What would you do if the investigation takes longer than the project schedule allows — how would you communicate that to management?