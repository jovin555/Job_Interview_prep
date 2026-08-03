# debugging-failure-analysis — Day 13

## Q1: How would you approach a failure investigation where a medical device's alarm system occasionally fails to activate, and the firmware logs show the alarm was triggered but the hardware never produced sound or visual output?

**Answer:** I'd start by treating this as a system-level failure rather than jumping to either the firmware or hardware side. The first step would be to map the complete alarm chain — from the firmware trigger condition, through the GPIO or driver control signal, to the transducer (buzzer, LED, or display element) and its power source. Since the logs confirm the firmware reached the trigger point, I'd focus on verifying that the control signal actually left the microcontroller and arrived at the driver circuit intact.

I'd want to capture the actual signals at multiple points in the chain — the microcontroller pin, the driver input, the driver output, and the transducer terminals. An oscilloscope with deep memory or a logic analyzer running for extended periods would be essential, since the failure is intermittent. I'd also check whether the alarm system shares any resources with other functions — for example, a timer channel, a PWM peripheral, or a GPIO port that gets reconfigured during normal operation. A common failure mode is a firmware path that reconfigures a shared peripheral or leaves a pin in the wrong state after some other operation completes.

I'd also examine the power supply to the alarm driver. If the alarm circuit is powered from a rail that's switched or regulated separately, a marginal connection or a component that drifts with temperature could cause intermittent operation. I'd review the schematic for any enable pins, pull-ups, or level-shifting circuits that could be in an indeterminate state. Finally, I'd consider environmental factors — temperature, humidity, or mechanical vibration — that might affect a marginal solder joint or connector.

**Possible follow-ups:** How would you determine whether this is a firmware logic issue versus a hardware signal integrity issue? What fault injection techniques would you use to verify the alarm circuit works when the root cause is identified?

---

## Q2: How would you approach debugging a medical device where the failure only occurs when two specific conditions happen simultaneously — for example, the device is charging AND a particular sensor is actively sampling — but neither condition alone causes the problem?

**Answer:** This type of interaction failure points to a resource contention or coupling issue. I'd begin by listing everything that's unique about the simultaneous state — what peripherals, power rails, clock domains, or interrupt sources are active in that combination that aren't active otherwise. The key is to identify the shared resource or coupling path.

I'd look at several categories of interaction. First, power: charging typically introduces ripple or transient load changes, and sensor sampling might be sensitive to that. I'd measure the sensor supply rail and reference voltage during both conditions separately and together, looking for noise, droop, or oscillation that only appears when both are active. Second, firmware: charging might trigger interrupt activity or a power management routine that delays or corrupts sensor reads. I'd review the interrupt priorities and any shared buffers or state variables. Third, electromagnetic coupling: the charging current path or switching regulator could radiate noise that couples into the sensor's analog front-end, especially if the PCB layout places the charging circuit near the sensor traces.

I'd also try to characterize the timing relationship — does the failure occur at a specific point in the charging cycle (for example, when the charger transitions between constant-current and constant-voltage modes) or at a specific sensor sampling rate? This might reveal a beat frequency or a specific transient event. I'd instrument the device to capture both conditions simultaneously — monitoring the sensor output, the charging current, and any relevant firmware state flags — to see exactly what happens at the moment of failure.

**Possible follow-ups:** How would you design an experiment to reproduce this interaction reliably in the lab? What would you look for in the PCB layout review to identify potential coupling paths?

---

## Q3: Walk me through your approach to a failure investigation where a medical device's non-volatile memory (flash or EEPROM) occasionally contains corrupted configuration data after a power loss event, even though the firmware includes a write-protection sequence and a checksum validation on readback.

**Answer:** I'd approach this by examining the entire power-loss sequence, not just the write operation itself. The critical question is: what happens to the power rails, the microcontroller's reset behavior, and the memory device's control signals during the power-down transient?

First, I'd look at the power supply behavior during brownout. If the main rail decays slowly, the microcontroller might continue executing instructions while operating outside its specified voltage range, potentially executing partial or corrupted write sequences. I'd check whether the brown-out detection (BOD) circuit is configured correctly and whether its threshold is set appropriately relative to the memory device's minimum operating voltage. If the BOD threshold is too low, the microcontroller might attempt writes while the memory is already below its reliable operating voltage.

Second, I'd examine the control signals to the memory device — chip select, write enable, and the clock or address lines. During power-down, these signals might float or glitch as the microcontroller's GPIO pins lose power at different rates. A floating chip-select line could cause the memory to interpret noise as a valid command. I'd check for pull-up or pull-down resistors on these lines and verify they're sized correctly for the power-down condition.

Third, I'd review the firmware's write sequence for edge cases. For example, if a write is interrupted mid-sequence, does the firmware have a recovery mechanism? Is there a possibility of a write being triggered by an interrupt handler that runs during the power-down sequence? I'd also check whether the checksum validation covers the entire configuration block and whether the firmware has a fallback to default values when corruption is detected.

Finally, I'd consider the memory device's own power-down behavior. Some devices have specific requirements for the order in which power and control signals are removed. I'd review the datasheet for any power-down timing specifications and verify the circuit meets them.

**Possible follow-ups:** How would you instrument the device to capture the exact state of the control signals during a power-loss event? What design changes would you consider to make the system more robust against this failure mode?

---

## Q4: How would you approach a situation where a medical device passes all its environmental testing (temperature, humidity, vibration) and EMC testing, but a small percentage of units fail in the field with the same symptom — a specific IC is found damaged (electrically shorted between two pins) when the units are returned and analyzed?

**Answer:** When a device passes all standard testing but still shows field failures with a specific IC damaged, I'd look for conditions that aren't covered by the standard test profiles. The key is to identify what's different about the field environment or usage patterns compared to the test conditions.

I'd start by analyzing the damaged ICs in detail — deprocessing if necessary to understand the failure mechanism. An electrical short between two specific pins can indicate overvoltage, overcurrent, electrostatic discharge (ESD), or a latch-up event. The specific pins involved often provide clues: if the short is between a power pin and ground, I'd suspect overvoltage or latch-up; if it's between two signal pins, I'd suspect ESD or a voltage difference between two circuits.

Next, I'd examine the application conditions. Are there any user actions or environmental conditions that could subject the IC to voltages beyond its absolute maximum ratings? For example, if the IC connects to an external interface (sensor connector, communication port, or patient connection), a fault in the external device or cable could back-feed voltage into the IC. I'd review the protection circuitry on all external interfaces — TVS diodes, series resistors, current limiting — and verify they're adequate for realistic fault conditions, not just the standard EMC test waveforms.

I'd also consider whether the failures correlate with specific usage patterns — for example, devices used with a particular accessory, in a particular setting, or after a specific event (like being dropped or exposed to moisture). I'd analyze the field return data for patterns in manufacturing date, component lot, or software version.

Finally, I'd consider whether the standard testing adequately covers the actual field conditions. For example, if the device is used in a home environment, patients might plug in third-party chargers or accessories that create conditions not covered by the EMC test setup. I'd review the test plans to identify gaps between the test conditions and real-world usage.

**Possible follow-ups:** How would you determine whether this is a design deficiency, a component quality issue, or a manufacturing process issue? What additional testing would you propose to reproduce the failure mode in the lab?

---

## Q5: A cross-functional team is investigating a medical device failure where the device's user interface (touchscreen) becomes unresponsive intermittently. The software team believes it's a hardware issue because the touch controller reports no data, and the hardware team believes it's a software issue because the touch controller passes all its standalone tests. How would you handle this situation and structure the investigation?

**Answer:** I'd start by reframing the discussion away from "hardware versus software" and toward understanding the complete system behavior. The fact that the touch controller passes standalone tests but fails in the system suggests an interaction issue, not a component failure. The goal is to find the conditions under which the system-level behavior breaks down.

I'd structure the investigation in three phases. First, characterization: I'd work with the team to define exactly what "unresponsive" means — does the touch controller stop reporting entirely, does it report but the data is ignored, or does the interface freeze at a different layer? I'd want to capture the state of the system at the moment of failure: the touch controller's register values, the interrupt status, the communication bus state, and any relevant firmware logs. This data would help narrow down where in the chain the failure occurs.

Second, reproduction: I'd design experiments to reproduce the failure under controlled conditions. I'd vary parameters that might affect the touch controller's operation — temperature, power supply voltage, electromagnetic interference from other subsystems, and user interaction patterns. I'd also examine whether the failure correlates with specific firmware states or operations, such as a particular screen being displayed or a specific background task running.

Third, analysis: Once we can reproduce the failure, I'd use the data to identify the root cause. If the touch controller stops responding on the I2C or SPI bus, I'd check for bus contention, clock stretching issues, or the controller entering a low-power state unexpectedly. If the controller reports data but the firmware doesn't process it, I'd look at interrupt handling, buffer management, or task scheduling issues.

Throughout this process, I'd emphasize that both teams need to work from the same evidence. I'd establish a shared log of findings and ensure that each hypothesis is tested with a controlled experiment. The goal isn't to assign blame but to understand the system behavior well enough to implement a robust fix.

**Possible follow-ups:** How would you handle the situation if the two teams continue to disagree about the root cause even after the investigation? What documentation or evidence would you require before implementing a corrective action?