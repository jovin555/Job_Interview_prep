# debugging-failure-analysis — Day 11

## Q1: How would you approach a failure investigation where a medical device's LCD display intermittently shows corrupted characters, but only when the device is powered from battery rather than from an external supply?

**Answer:** This is a classic power-domain versus signal-integrity interaction problem, and the battery-versus-external-supply distinction is the key clue. I'd start by characterizing the electrical difference between the two power sources — battery impedance is typically higher, and the voltage sags under load transients, whereas an external supply is stiff. I'd first probe the display's power rails and the LCD controller's supply with a differential probe, looking for ripple or droop that correlates with the corruption events. If the corruption is truly random, I'd use a long acquisition on a deep-memory scope with the display refresh rate as a trigger reference.

Next, I'd examine the interface between the controller and the display — whether it's parallel or serial — and check timing margins. With battery power, the system may be operating at a slightly lower voltage, which can shift logic thresholds and reduce noise margins. I'd look at the rise/fall times of the data and clock lines, and check for crosstalk from adjacent traces, especially during display refresh when many lines toggle simultaneously.

I'd also consider whether the battery's internal resistance is causing the supply to droop specifically during display refresh bursts, which draw significant current. Adding a bulk capacitor near the display connector or increasing the value of the existing decoupling might resolve it, but I'd want to verify the root cause first rather than just adding capacitance. I'd also check whether the firmware is doing anything different on battery power — for example, lowering the CPU clock or entering a low-power mode that changes the timing of the display interface.

**Possible follow-ups:**
- How would you determine whether the issue is a supply voltage problem versus a logic-level margin problem?
- What measurements would you take to confirm that the battery's internal impedance is the contributing factor?

---

## Q2: How would you approach a failure investigation where a medical device's firmware occasionally writes corrupted data to its flash memory, and the corruption is only detected weeks later when the device is powered on after being off for an extended period?

**Answer:** This is a particularly challenging failure mode because the symptom appears long after the actual fault event, which means the investigation has to work backwards from the corrupted data to the write operation that caused it. I'd start by examining the flash memory contents to understand the pattern of corruption — is it a single bit, a byte, or a block? Is the corruption always in the same location, or does it vary? This can hint at whether the issue is a marginal write operation, a power-loss during write, or a hardware issue like a marginal address line.

I'd then look at the firmware's flash write routine and the conditions under which writes occur. In a medical device, flash writes often happen during data logging or parameter updates. I'd check whether the write routine has proper error checking, whether it verifies the data after writing, and whether it handles power-loss during write correctly. Many flash corruption issues trace back to a power glitch during a write cycle, where the device loses power mid-operation and the flash ends up in an indeterminate state.

From a hardware perspective, I'd examine the power supply to the flash device — is there adequate decoupling? Is the supply stable during write operations, which draw higher current? I'd also check the control lines — chip enable, write enable, and address lines — for glitches or marginal timing. A slow rise time on a control line can cause spurious writes. I'd also consider whether the flash device is being operated within its specified voltage range, especially at end-of-life battery voltage.

Finally, I'd look at the device's power-down sequence. If the firmware doesn't properly disable the flash before power is removed, a decaying supply voltage can cause spurious write operations. The fact that the corruption is only detected after a long power-off period suggests the device may be writing garbage during the power-down transition, and the corrupted data is only noticed when the device is next powered on and reads back the stored values.

**Possible follow-ups:**
- What specific measurements would you take to characterize the power-down sequence?
- How would you design a test to reproduce this failure in the lab?

---

## Q3: How would you approach a situation where a medical device passes all its design verification tests, but during a limited field trial, a small number of units report a "sensor fault" error that clears when the device is power-cycled — and the error code points to a sensor self-test failure that should be impossible given the sensor's specifications?

**Answer:** When a failure mode contradicts the component's specifications, it's a strong signal that the device is operating the component outside its intended conditions, or that the self-test logic itself is flawed. I'd start by treating the sensor's self-test as a system-level function rather than a component-level guarantee. The self-test may be checking something that's affected by the system's state — for example, a voltage reference that's shared with other circuitry, or a timing parameter that depends on the firmware's scheduling.

I'd first gather as much data as possible from the field units — the error logs, the device's operating history, battery state, temperature, and any other parameters recorded around the time of the fault. I'd look for patterns: does the fault occur at a specific battery voltage? After a specific activity? At a specific temperature? Even if the logs don't show an obvious pattern, the absence of a pattern is itself useful information.

Next, I'd examine the self-test implementation in firmware. What exactly does the self-test check, and what thresholds does it use? Are the thresholds based on the sensor's datasheet specifications, or were they derived from actual system measurements? A common issue is that self-test thresholds are set too tight, based on ideal conditions, and the real system has additional noise or offset that pushes the reading outside the threshold. I'd also check whether the self-test is affected by the order of initialization — for example, if the sensor is tested before its power supply has fully settled, or before the ADC reference has stabilized.

From a hardware perspective, I'd look at the sensor's power supply and reference circuitry. If the sensor's supply has a droop during a specific operation — like a motor starting or a wireless transmission — the self-test reading could be corrupted. I'd also check the sensor's communication interface for noise or timing issues that could cause a spurious reading. Finally, I'd consider whether the sensor itself is marginal — perhaps a small percentage of sensors have slightly different characteristics that push them outside the self-test thresholds, even though they function correctly in normal operation.

**Possible follow-ups:**
- How would you determine whether the issue is a firmware threshold problem versus a hardware marginality issue?
- What changes would you propose to the self-test implementation to make it more robust?

---

## Q4: How would you approach debugging a failure where a medical device's real-time clock (RTC) loses time — not by drifting, but by jumping forward or backward by several hours — and the jumps don't correlate with any user interaction or power events?

**Answer:** An RTC that jumps by hours rather than drifting suggests a register corruption event or a communication error between the main processor and the RTC, rather than a crystal accuracy issue. I'd start by examining the RTC's communication interface — typically I2C or SPI — and looking for conditions that could cause a partial write or a corrupted read. A partial write could occur if the processor is interrupted mid-transaction, or if the I2C bus is held low by a device that's not releasing the line properly.

I'd also examine the RTC's power supply and backup battery circuitry. If the RTC's supply dips below its minimum operating voltage, even briefly, it could cause the time registers to become corrupted. I'd check the decoupling on the RTC's supply pin, and look at the switchover circuitry between the main supply and the backup battery. A marginal switchover could cause a glitch that resets or corrupts the RTC's internal registers.

Another angle is the RTC's interrupt or alarm functionality. If the RTC is configured to generate an interrupt, and that interrupt line is noisy or has a marginal pull-up, it could cause spurious events that the firmware interprets as a time-setting command. I'd also check whether the firmware has any code that writes to the RTC's time registers — for example, a time-sync routine that runs periodically. If that routine has a bug — like writing the time registers in the wrong order, or writing a partially updated time structure — it could cause a jump.

I'd also consider the RTC's calibration or temperature compensation features. Some RTCs have automatic temperature compensation that adjusts the oscillator frequency, and a bug in that logic could cause a jump. However, that would typically cause drift rather than a discrete jump. The discrete jump points more toward a register write or read corruption. I'd set up a test that logs the RTC time at high frequency, along with the I2C bus activity, power supply voltage, and any interrupt events, to try to capture the exact moment of the jump and correlate it with other system activity.

**Possible follow-ups:**
- How would you distinguish between a firmware-induced register write and a hardware-induced corruption event?
- What would you look for in the I2C bus traffic around the time of the jump?

---

## Q5: A junior engineer on your team has been investigating a field failure where a medical device's buzzer (used for alarms) occasionally fails to sound, even though the firmware logs show the alarm was triggered. The engineer has spent a week testing the buzzer driver circuit in isolation and it works perfectly every time. They're frustrated and the investigation is stalled. How would you handle this situation?

**Answer:** I'd first acknowledge the engineer's effort and validate that their isolation testing was methodical — testing the driver circuit in isolation is a reasonable step. Then I'd reframe the problem: the fact that the circuit works in isolation is actually a critical clue. It means the issue is likely an interaction between the buzzer circuit and something else in the system, not a fault in the buzzer circuit itself. I'd guide them to shift from testing the circuit in isolation to testing it in the full system context.

I'd suggest a structured approach to identify what's different when the buzzer is in the full system. Is the buzzer's power supply shared with other loads that could cause a voltage drop when they're active? Is the buzzer's drive signal — typically a PWM from the microcontroller — affected by other firmware activity? Is there a ground bounce issue when other high-current loads switch simultaneously? I'd ask the engineer to review the system schematic and identify everything that shares the buzzer's supply rail, ground return path, and GPIO port.

I'd also suggest they look at the firmware's alarm handling logic. The logs show the alarm was triggered, but does the firmware actually drive the buzzer pin? Is there a condition where the firmware thinks it's driving the buzzer but the pin is actually in a different state — for example, a GPIO configuration issue where the pin is reconfigured for another function, or a race condition where the alarm is triggered but then suppressed by a higher-priority task? I'd encourage them to add instrumentation — like a logic analyzer on the buzzer pin and the supply rail — and run the full system through its normal operating sequence to try to reproduce the failure.

Finally, I'd suggest they review the field return data more carefully. Are the failures clustered in a specific batch of units, a specific firmware version, or a specific usage pattern? That data might point to a root cause that's not visible in the circuit itself. I'd also encourage them to document their findings so far and share them with the team — sometimes a fresh perspective can spot something that's been overlooked.

**Possible follow-ups:**
- How would you help the engineer prioritize which system interactions to investigate first?
- What would you do if the failure can't be reproduced in the lab despite the field evidence?