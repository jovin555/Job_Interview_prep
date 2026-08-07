# debugging-failure-analysis — Day 17

## Q1: You're investigating a field failure where a medical device's vibration motor (used for a user alert) has stopped working. The motor driver IC tests fine on the bench, the firmware logs show the motor was commanded on, and the motor itself measures within specification when removed from the device. However, when the motor is connected to the device's PCB, it doesn't spin. How would you approach this?

**Answer:** This is a classic "works in isolation, fails in integration" problem, so I'd start by carefully defining what's different between the bench test and the integrated condition. The motor driver IC passes standalone tests, and the motor passes standalone tests — so the fault likely lives at the interface between them or in the interaction with something else on the board.

My first step would be to reproduce the failure consistently. I'd set up the device in a test configuration where I can command the motor on while probing the relevant nodes. I'd measure, in sequence: the motor driver's output voltage at the connector pins, the current being drawn, and the voltage at the motor terminals themselves. The key question is whether the driver is actually delivering power to the connector, or whether something between the driver output and the motor is dropping that voltage.

A common culprit in this scenario is a marginal solder joint or a cracked trace at the connector — especially in a device that experiences vibration during normal use. The motor connector is a mechanically stressed area, and a hairline crack in a solder joint can present as an intermittent open that only manifests when the motor is connected and drawing current. The bench test might pass because the test fixture applies different mechanical stress or because the driver is tested without the motor load.

I'd also check the return path — a high-resistance ground connection between the motor and the driver can prevent current flow even when the driver output looks correct. I'd measure the voltage difference between the motor's ground terminal and the driver's ground pin while the motor is commanded on. If there's a significant voltage drop, that points to a poor ground connection.

If the electrical path checks out, I'd look at whether the motor is mechanically seized or whether the load is somehow preventing rotation — but since the motor spins when removed, that's less likely. I'd also verify the firmware is actually commanding the correct output — not just logging that it did. Sometimes the log says "motor on" but the actual GPIO or PWM configuration is wrong, or the command is being overridden by a safety interlock.

Finally, I'd examine the physical connection under magnification — X-ray inspection of the connector solder joints can reveal cracks that aren't visible externally. If this is a field failure trend rather than a single unit, I'd want to understand whether the failure correlates with device age, usage patterns, or manufacturing batches.

**Possible follow-ups:** How would you determine whether this is a single-unit anomaly or a systemic issue requiring a design change? What data would you want from the field to help narrow down the root cause?

---

## Q2: How would you approach debugging a medical device where the firmware occasionally fails to enter its low-power sleep mode, causing the battery to drain faster than expected — but only when a specific peripheral (an external ADC) has been used recently? The ADC's datasheet specifies a "power-down" command, and the firmware does send it, but the current consumption remains high.

**Answer:** This is a firmware-hardware interaction issue where the symptom (elevated current) is clear, but the root cause is likely a mismatch between what the firmware intends and what the hardware actually does. I'd approach this in layers.

First, I'd confirm the failure mode precisely. I'd instrument the device to measure current consumption over time, and correlate the current trace with firmware execution — specifically, when the sleep command is issued and when the ADC's power-down command is sent. The question is whether the ADC is actually entering its low-power state, or whether something is keeping it awake.

A common issue with external ADCs is that the power-down command only takes effect if the serial interface (typically SPI or I2C) is in a known state when the command is sent. If the firmware sends the power-down command but leaves the chip-select line low, or if the clock line is left in an indeterminate state, the ADC might not recognize the command. I'd check the timing of the power-down command relative to the last data transfer — some ADCs require a specific number of clock cycles after the command before they actually enter power-down.

Another possibility is that the ADC's power-down state is being overridden by a hardware condition — for example, if a GPIO connected to the ADC's power-down pin (if it has one) is left in the wrong state, or if the ADC's reference input is still being driven by an external circuit. I'd check whether any other peripheral is holding the SPI bus active, preventing the ADC from seeing a clean command.

I'd also look at the firmware's sleep sequence more broadly. Sometimes the issue isn't the ADC itself but the order of operations — if the firmware puts the microcontroller to sleep before the ADC's power-down command has fully propagated, or if an interrupt from the ADC wakes the system immediately after sleep is entered, the device might never actually reach low-power mode.

To isolate the variable, I'd create a minimal test: put the device in sleep mode without using the ADC, measure current. Then use the ADC and immediately sleep, measure again. Then use the ADC, wait various durations, and sleep. This would tell me whether the issue is the ADC's power-down timing, the bus state, or something else. I'd also use a current probe with high temporal resolution to see whether the elevated current is constant or intermittent — a constant offset suggests something is left powered, while intermittent spikes suggest periodic wake-ups.

**Possible follow-ups:** What specific measurements would you take to distinguish between the ADC not entering power-down versus the microcontroller being woken by an interrupt? How would you verify that the ADC's power-down command is actually being received correctly?

---

## Q3: You're leading a failure investigation where a medical device's touchscreen becomes unresponsive after the device has been in continuous use for several hours. The touch controller is an I2C device, and the firmware includes a bus-recovery routine that resets the controller and re-initializes the I2C peripheral. The recovery routine works sometimes but not always. How would you structure this investigation?

**Answer:** The fact that the recovery routine works sometimes but not always is a critical clue — it suggests the failure isn't a simple lockup but rather a condition that sometimes persists even after reset. I'd structure this investigation in phases.

First, I'd want to characterize the failure precisely. I'd instrument the device to log: the I2C bus state (SCL/SDA levels), the touch controller's interrupt line, the time since last successful touch event, and the device's temperature. The "after several hours" pattern suggests a thermal component — the touch controller or the I2C pull-ups might be operating at elevated temperature, changing timing margins. I'd also check whether the failure correlates with the device's charging state or battery voltage, since I2C logic levels can shift as the supply rail droops.

Second, I'd examine the I2C bus behavior at the moment of failure. Using a logic analyzer or oscilloscope with deep memory, I'd capture the bus activity leading up to the failure. I'm looking for: clock stretching that never releases, SDA held low by the touch controller (a classic I2C lockup), or a corrupted transaction that leaves the controller in an undefined state. The distinction matters — if the controller is holding SDA low, the bus recovery routine needs to toggle SCL to release the bus before re-initializing. If the controller is simply not responding, the issue might be its internal state or power supply.

Third, I'd review the firmware's recovery routine carefully. A common flaw is that the recovery routine resets the I2C peripheral and the touch controller, but doesn't properly handle the case where the controller is mid-transaction — the controller might need a specific reset sequence (e.g., a reset pin toggle, or a specific I2C command) rather than just a bus re-initialization. I'd also check whether the recovery routine properly waits for the bus to be released before attempting re-initialization.

Fourth, I'd consider the hardware design. I'd check the I2C pull-up resistor values against the total bus capacitance — if the pull-ups are too weak for the bus capacitance, the rise times can be marginal, and this becomes worse at temperature or as the controller's input thresholds shift. I'd also check whether the touch controller's interrupt line is properly configured — if the interrupt is level-triggered and the controller is asserting it continuously, the firmware might be spending all its time servicing interrupts rather than communicating.

Finally, I'd want to reproduce the failure in a controlled environment. An environmental chamber at elevated temperature with continuous touch activity would help me capture the failure in real time. If I can reproduce it, I can try the recovery routine manually and observe whether it succeeds or fails, and under what conditions.

**Possible follow-ups:** What would you look for in the I2C bus capture to distinguish between a controller lockup versus a bus contention issue? How would you verify that the recovery routine is actually executing when the failure occurs?

---

## Q4: A medical device's firmware occasionally writes corrupted data to its configuration EEPROM, and the corruption is only detected when the device is powered on after being off for an extended period. The EEPROM has a write-protect pin that the firmware controls via GPIO. How would you approach this failure investigation?

**Answer:** This is a particularly interesting failure because the "detected after extended power-off" symptom suggests the corruption might not be happening during normal writes — it might be happening during power-down or power-up, when the system is in an undefined state.

My first hypothesis would be that the EEPROM is being written unintentionally during power transitions. The write-protect pin is controlled by GPIO, and during power-down, the GPIO might float or transition through an intermediate state before the microcontroller loses power. If the write-protect pin is active-low (protected when low), and the GPIO goes high during power-down, the EEPROM becomes unprotected at the exact moment when the power rails are collapsing — and the EEPROM's own power supply might still be high enough for it to respond to spurious signals on the I2C or SPI bus.

I'd start by examining the power-down sequence. I'd use an oscilloscope to capture, simultaneously: the main power rail, the EEPROM's supply, the write-protect GPIO, and the serial clock/data lines during power-down. I'm looking for any activity on the clock or data lines after the write-protect pin goes inactive. If the microcontroller's GPIO pins float during power-down, they can pick up noise and generate spurious clock pulses that the EEPROM interprets as a write command.

I'd also check the firmware's power-down sequence. Does the firmware explicitly set the write-protect pin to its protected state before entering sleep or initiating shutdown? Is there a window between when the firmware finishes its last legitimate write and when the power actually drops? If the firmware writes configuration data and then immediately shuts down without re-asserting write-protect, there's a window where the EEPROM is unprotected.

Another angle is the power-up sequence. When the device powers on, the microcontroller's GPIO pins might be in an undefined state until the firmware configures them. If the write-protect pin defaults to the unprotected state during this period, and the EEPROM's supply ramps up faster than the microcontroller's, the EEPROM might see spurious bus activity before the firmware takes control of the pins.

To investigate, I'd want to capture the power-up and power-down sequences with a logic analyzer or oscilloscope, paying attention to the relative timing of the EEPROM supply, the write-protect pin, and the bus lines. I'd also check whether the EEPROM has a "power-on reset" feature that prevents writes until the supply is stable — if not, the hardware design might need an external supervisor circuit to hold the write-protect pin in the protected state during power transitions.

Finally, I'd review the firmware's write routine. Is there a possibility that the firmware itself is writing corrupted data — for example, a buffer overflow or a race condition where the configuration data is being modified while it's being written? The fact that corruption is only detected after extended power-off might simply mean that the corrupted data is only read back at that point, and the corruption actually happened during a legitimate write earlier.

**Possible follow-ups:** How would you determine whether the corruption happens during power-down, power-up, or during normal operation? What hardware changes would you consider if the root cause is spurious bus activity during power transitions?

---

## Q5: You're leading a cross-functional investigation where a medical device's firmware and hardware teams disagree on the root cause of an intermittent failure. The device occasionally fails to complete a sensor read within the required time window, and the sensor occasionally returns stale data. The firmware team believes the hardware has a timing issue — the sensor's clock is slow or the data line has excessive capacitance. The hardware team believes the firmware is not handling the sensor's timing requirements correctly. How would you handle this situation and structure the investigation?

**Answer:** This is a classic cross-functional disagreement, and my first priority is to reframe the conversation from "whose fault is it" to "what is the evidence telling us." The goal isn't to assign blame — it's to understand the failure mechanism, and in many cases, the root cause is a combination of hardware and firmware factors that interact.

I'd start by establishing a shared understanding of the failure. I'd ask both teams to articulate, in precise terms, what they believe is happening and what evidence supports their position. The firmware team says the sensor's clock is slow — what measurement supports that? The hardware team says the firmware isn't handling timing — what specific timing requirement is being violated? I'd want to see the sensor's datasheet timing specifications, the firmware's timing analysis, and any oscilloscope captures of the actual bus activity.

Then I'd structure a joint investigation with clear milestones. The first step is to capture the failure in real time — I'd set up a test where the sensor read is performed repeatedly while monitoring the bus with a logic analyzer or oscilloscope, synchronized with firmware logs. The goal is to capture the exact moment of failure: what does the bus look like, what is the firmware doing, and what is the sensor's response?

The key question is whether the failure is a timing margin issue or a protocol violation. If the sensor's clock is running slow, the firmware might be issuing reads faster than the sensor can respond — but the firmware should be checking the sensor's ready/busy status. If the sensor is returning stale data, the firmware might not be properly waiting for new data to be available. I'd want to see whether the failure correlates with specific bus conditions — for example, does it happen more often at temperature extremes, or when other peripherals are active on the same bus?

I'd also look at the interface between the two teams' domains. For example, if the sensor uses I2C with clock stretching, the firmware needs to support clock stretching, and the hardware needs to ensure the bus capacitance is within specification for the pull-up resistors. A marginal pull-up value combined with a firmware timeout that's too short could produce exactly this symptom — neither team is "wrong," but the combination is fragile.

To move the investigation forward, I'd propose a series of controlled experiments. For example: (1) run the sensor read at a slower clock speed to see if the failure disappears — this would support the hardware timing hypothesis; (2) increase the firmware timeout and see if the failure disappears — this would support the firmware hypothesis; (3) measure the bus rise time and compare it to the sensor's specification — this would give objective data on the hardware margin. Each experiment isolates one variable and produces data that both teams can agree on.

Finally, I'd emphasize that the goal is to find the root cause and implement a robust fix — not to win an argument. If the evidence points to a marginal hardware design, the fix might be a firmware workaround (e.g., longer timeout) plus a hardware improvement (e.g., stronger pull-ups) for the next revision. If the evidence points to a firmware bug, the fix is clear. But the investigation needs to be driven by data, not by preconceptions.

**Possible follow-ups:** How would you handle a situation where one team refuses to accept the evidence because it contradicts their initial hypothesis? What specific measurements would you want to take to objectively characterize the timing margin?