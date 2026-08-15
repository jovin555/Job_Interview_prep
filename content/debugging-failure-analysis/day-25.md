# debugging-failure-analysis — Day 25

## Q1: How would you approach debugging a medical device where a specific analog input channel reads correctly when measured directly at the ADC input with an oscilloscope, but the firmware consistently reports a value that is offset by a fixed amount — and the offset is different on different units of the same device?

**Answer:** This is a classic case where the measurement point and the firmware's reference point are telling different stories, so the first step is to establish exactly where in the signal chain the offset is being introduced. I'd start by tracing the complete path from the sensor connector through any conditioning circuitry (amplifiers, filters, protection networks) to the ADC input pin, and then verify what the ADC is actually converting.

The fact that the oscilloscope shows a correct signal at the ADC input but the firmware reports an offset suggests several possibilities. First, I'd check whether the ADC's reference voltage is what the firmware assumes it to be — if the reference has tolerance or drift, the digital code will be offset even though the analog signal looks correct. I'd measure the actual reference voltage and compare it to the firmware's calibration constant. Second, I'd verify the ADC's configuration: is the input channel configured for single-ended vs. differential mode correctly? Is the gain setting what the firmware expects? A mismatch between the hardware configuration and the firmware's assumption would produce exactly this symptom.

The unit-to-unit variation in the offset is a strong clue. If the offset were a fixed design error, it would be consistent across units. Variation suggests a component tolerance issue — perhaps the reference voltage tolerance, an input bias current interacting with a high source impedance, or a gain-setting resistor tolerance in the conditioning stage. I'd measure the actual reference voltage and the gain-stage resistor values on several units and correlate them with the observed offset. I'd also check whether the offset scales with the input voltage (a gain error) or is constant (an offset error) — that distinction narrows the search considerably.

I'd also want to rule out a firmware issue: is the firmware reading the correct ADC channel, and is it applying the correct scaling and calibration? I'd review the ADC initialization code and the channel mux configuration. Finally, I'd check whether the ADC's input sampling time is adequate for the source impedance — if the ADC is sampling before the internal sampling capacitor is fully charged, you get a systematic error that varies with source impedance and thus with component tolerances.

**Possible follow-ups:**
- How would you distinguish between a gain error and an offset error in this scenario, and how would that change your investigation?
- What specific measurements would you take to verify the ADC reference voltage is the root cause?

---

## Q2: You're leading a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent communication failure is caused by a marginal pull-up resistor value on an I2C bus or by a firmware timing issue in the bus recovery routine. How would you handle this situation and structure the investigation?

**Answer:** The first thing I'd do is acknowledge that both hypotheses are plausible and that the goal is to let evidence, not conviction, drive the conclusion. I'd frame the investigation around gathering data that can discriminate between the two failure modes rather than trying to prove either side right.

I'd start by characterizing the failure more precisely. What exactly happens when communication fails? Does the bus hang with SCL or SDA held low? Does the sensor return NACKs? Does the firmware's recovery routine trigger, and does it succeed or fail? I'd want to capture bus traffic during a failure event using a logic analyzer with a deep buffer, ideally with timestamping, so we can see the exact sequence of events leading up to the failure.

The pull-up resistor hypothesis and the firmware timing hypothesis make different predictions. If the pull-up value is marginal, I'd expect to see slow rise times on the bus, especially at higher bus capacitance or when multiple devices are connected. I'd measure the rise time on both SCL and SDA against the I2C specification for the selected bus speed, and I'd check whether the rise time degrades as the bus warms up or as more devices are added. I'd also check the actual bus capacitance and compare it to the pull-up value — a rule of thumb is that the RC time constant should be well below the maximum rise time specified for the bus speed.

The firmware timing hypothesis predicts a different signature. If the recovery routine is the problem, I'd expect to see the failure occur specifically after a bus error or after the recovery routine has been invoked. I'd review the recovery routine's state machine: does it properly release the bus, wait the required time, and re-initialize the peripheral? Does it handle the case where the bus is held low by a slave device? I'd look for race conditions between the recovery routine and other tasks or interrupts.

I'd structure the investigation as a series of controlled experiments. First, measure rise times and compare to specification. Second, stress the bus by adding capacitance and see if the failure rate increases — that would support the pull-up hypothesis. Third, instrument the firmware to log when the recovery routine is invoked and whether it completes successfully. Fourth, try a firmware change that uses a more robust recovery sequence (e.g., toggling SCL to release a stuck slave) and see if the failure rate changes. Each experiment should change only one variable.

The key is to keep the investigation collaborative — I'd have both teams review the data together and agree on what each experiment would prove or disprove before running it. This prevents the investigation from becoming adversarial and ensures buy-in on the conclusion.

**Possible follow-ups:**
- What specific measurements would you take to characterize the I2C bus timing, and what would you compare them against?
- How would you design an experiment that could definitively rule out one of the two hypotheses?

---

## Q3: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This is a compatibility issue that points to the interaction between the device's charging circuit and the charger's electrical characteristics. I'd start by characterizing both chargers — the one that works and the one that doesn't — to understand what's different. Key parameters to measure include output voltage under load, current capability, ripple, and how the charger responds to a load step.

The most common cause of this type of issue is inrush current. When the device is connected, the charging circuit's input capacitors charge rapidly, drawing a large current spike. A charger with a different output capacitance or a different current-limiting behavior may respond differently to this inrush. Some chargers have a soft-start feature that limits current, while others may momentarily drop their output voltage or oscillate when hit with a capacitive load. I'd measure the inrush current profile on both chargers using a current probe and a scope with a trigger on the connection event.

Another possibility is that the problematic charger has a different output voltage tolerance. If the charger's output is slightly higher than expected, the charging circuit's input protection or the charger IC's input overvoltage threshold might be triggered, causing the circuit to behave abnormally. I'd measure the actual output voltage of both chargers under no-load and under load.

I'd also consider the charger's ground reference and whether there's any leakage current or ground loop issue. A charger with a different grounding scheme (e.g., a two-prong vs. three-prong plug) could create a ground potential difference that affects the charging circuit.

I'd structure the investigation by first reproducing the issue reliably, then measuring the key electrical parameters on both chargers, and then correlating the differences with the observed behavior. I'd also check whether the device's charging circuit has any input protection components (like a TVS diode or a fuse) that might be interacting with the charger's characteristics. Finally, I'd review the charging IC's datasheet for any application notes about input source compatibility and compare the device's input circuit against the recommended design.

**Possible follow-ups:**
- What specific measurements would you take on both chargers to characterize their behavior?
- How would you determine whether the issue is an inrush current problem versus a voltage tolerance problem?

---

## Q4: How would you approach debugging a medical device where the firmware occasionally fails to wake from a low-power sleep mode, and the failure is more frequent when the device has been in sleep for longer periods — the device is supposed to wake on an RTC alarm, but sometimes the RTC interrupt fires and the firmware doesn't resume execution?

**Answer:** This is a subtle power-management issue where the failure mode depends on the duration of the sleep state, which suggests something that changes over time — either a hardware state that degrades or drifts, or a firmware state that becomes corrupted or inconsistent.

I'd start by reproducing the issue with instrumentation. I'd want to monitor the RTC interrupt line, the MCU's wake-up pin, and the current consumption simultaneously. The current profile would tell me whether the device is actually staying in sleep mode (low current) or whether it's partially awake but stuck (elevated current). I'd also check whether the RTC interrupt is actually being generated — is the RTC alarm flag set when the device fails to wake?

The time-dependence is a key clue. If the failure is more frequent after longer sleep periods, I'd consider several mechanisms. First, the RTC might be running from a different clock source in sleep mode (e.g., an internal RC oscillator vs. an external crystal), and that clock might drift or become unstable over time. If the RTC alarm is set relative to a timebase that drifts, the alarm might fire at the wrong time or not at all. I'd verify which clock source the RTC uses in sleep mode and measure its accuracy over extended periods.

Second, the MCU's low-power mode configuration might have a subtle issue. Some MCUs require specific sequences for entering and exiting low-power modes, and if a peripheral is left in an active state, it can prevent proper wake-up. I'd review the sleep-entry code and the wake-up configuration — is the RTC interrupt enabled in the right interrupt controller? Is the interrupt priority set correctly? Is there a chance that another interrupt is pending and consuming the wake-up event?

Third, I'd consider a brown-out or voltage droop issue. If the device's power supply has a marginal decoupling capacitor that leaks over time, the voltage might droop slightly during extended sleep, and the MCU's brown-out detector might be triggering or the RTC might be operating at the edge of its specified voltage range. I'd measure the supply voltage during sleep and at the moment of the expected wake-up.

I'd also check the firmware's wake-up handling. If the ISR runs but the main code doesn't resume correctly — for example, if the firmware's sleep loop has a race condition where the wake-up flag is cleared before the main loop checks it — the device would appear to not wake even though the interrupt fired. I'd review the sleep/wake state machine carefully.

Finally, I'd consider whether the RTC alarm is being set correctly for long sleep durations. If the firmware uses a 16-bit counter or a timer with limited range, the alarm might wrap around or be set incorrectly for longer intervals. I'd verify the RTC configuration for the maximum expected sleep duration.

**Possible follow-ups:**
- How would you determine whether the RTC interrupt is actually firing when the device fails to wake?
- What specific measurements would you take to check for a voltage droop issue during extended sleep?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a junior engineer on your team has been debugging an issue for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. The engineer is becoming frustrated, and the project schedule is tight. How would you approach this?

**Answer:** The first thing I'd do is acknowledge the engineer's effort and the difficulty of the problem — they've been working hard, and frustration is a natural response to an elusive bug. I'd make it clear that the goal is to work together to find a more effective approach, not to assign blame.

I'd then ask the engineer to walk me through their investigation in detail — what they've tested, what they've ruled out, and what their current hypotheses are. This serves two purposes: it helps me understand the technical landscape, and it often reveals assumptions or blind spots that the engineer hasn't questioned. I'd listen for places where they've been testing components in isolation without considering the interactions between components, which is a common trap in system-level failures.

The key insight I'd offer is that when isolated components pass but the system fails, the problem is likely in the interaction — the interface between components, the timing, the loading, or the environment. I'd suggest shifting the investigation from component-level testing to system-level observation. Instead of testing each part separately, I'd recommend instrumenting the system as a whole — monitoring multiple signals simultaneously, logging system state, and trying to capture the failure as it happens.

I'd also suggest a more structured approach to the debugging. Instead of trying many things and hoping something works, I'd propose a systematic divide-and-conquer strategy: identify the smallest subsystem that exhibits the failure, then progressively add components until the failure appears. This narrows the search space and makes the investigation more manageable.

I'd also encourage the engineer to question their assumptions. What are they assuming about the system that might not be true? For example, are they assuming the power supply is stable under all conditions? Are they assuming the firmware initialization sequence is correct? Are they assuming the timing requirements are met? I'd ask them to write down their assumptions and then design experiments to test each one.

Finally, I'd offer to pair with the engineer on the next debugging session. Working together, we can bring fresh eyes to the problem and catch things that a single investigator might miss. I'd also make sure the engineer knows that asking for help is a sign of good engineering judgment, not weakness — the goal is to solve the problem, not to solve it alone.

**Possible follow-ups:**
- How would you balance giving the engineer autonomy to solve the problem with stepping in to provide direction?
- What specific questions would you ask the engineer to help them identify their assumptions?