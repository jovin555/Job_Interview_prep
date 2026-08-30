# debugging-failure-analysis — Day 40

## Q1: How would you approach debugging a medical device where a specific sensor reading is correct when measured at the ADC input with an oscilloscope, but the firmware consistently reports a value that is offset by a fixed amount — and the offset is different on different units of the same device?

**Answer:** This is a classic case where the analog signal at the ADC input looks correct, but the digital value coming out is wrong — so the problem is almost certainly between the ADC input pin and the final stored/transmitted value. The fact that the offset varies between units is a strong clue that this isn't a firmware constant or a fixed calibration issue; it points to something unit-specific in the hardware path or in how the ADC is configured.

My first step would be to verify the ADC reference voltage on each unit. If the reference is derived from a regulator or a resistor divider that has tolerance, the actual reference voltage will vary between units, and the firmware's assumed reference value will produce a consistent offset that scales with the reference error. I'd measure the actual reference voltage on several units and compare it to what the firmware assumes.

Next, I'd check the ADC configuration — specifically the input scaling, gain settings, and whether the ADC is configured for single-ended or differential input. A mismatch between the hardware front-end gain and the firmware's assumed gain would produce a gain error, but a fixed offset (not scaling with input level) suggests something like a wrong offset calibration value, an incorrect ADC offset register setting, or a reference mismatch.

I'd also look at the input impedance and source impedance. If the sensor or front-end has high output impedance and the ADC's sample-and-hold capacitance isn't fully charged within the sampling window, you get a voltage droop that depends on the specific component tolerances on each board. This would show up as a unit-to-unit offset variation. The oscilloscope probe (typically 10MΩ) wouldn't load the circuit the same way the ADC's sample-and-hold does, so the scope would show the correct voltage while the ADC samples a slightly lower one.

Finally, I'd check the PCB layout — specifically the ground path between the sensor, the ADC, and the reference. A ground offset between the sensor ground and the ADC ground would add a fixed voltage to the measurement, and this offset would vary between units based on trace resistance and current flow.

The systematic approach is: verify the reference, verify the ADC configuration matches the hardware, check the sampling time versus source impedance, and then examine the ground topology. Each of these can be tested independently and will narrow down the root cause.

**Possible follow-ups:**
- How would you distinguish between a gain error and an offset error in this scenario, and what test would you run to confirm which one you're dealing with?
- If the offset scales with the input voltage (i.e., it's actually a gain error), how would that change your investigation?

---

## Q2: You're leading a cross-functional investigation where a medical device's firmware and hardware teams disagree on whether an intermittent communication failure is caused by a marginal pull-up resistor value on an I2C bus or by a firmware timing issue in the bus recovery routine. How would you handle this situation and structure the investigation?

**Answer:** The first thing I'd do is acknowledge that both hypotheses are plausible and that the goal is to find the root cause with evidence, not to win an argument. The structure of the investigation should be designed to discriminate between the two hypotheses rather than to prove either one.

I'd start by gathering objective data from the field failures. If the device logs include I2C bus state information, error codes, or timestamps, I'd analyze those for patterns — do the failures correlate with specific bus activity, with temperature, with time since power-up, or with specific firmware operations? This data alone can often narrow down the possibilities significantly.

Next, I'd set up a controlled reproduction effort. On the bench, I'd instrument the I2C bus with a logic analyzer or oscilloscope to capture the actual bus waveforms during failures. The key measurements would be: the rise time of the SDA and SCL lines (which directly reflects the pull-up resistor value and bus capacitance), the voltage levels reached during communication, and the timing of the failure relative to bus activity.

If the rise time is marginal — close to the I2C spec limit — that supports the pull-up hypothesis. I'd then test the effect of different pull-up values by temporarily modifying a test board. If the failure disappears with a stronger pull-up, that's strong evidence for the hardware hypothesis. If the rise time is well within spec but the failure persists, that shifts the focus to firmware.

For the firmware hypothesis, I'd review the bus recovery routine with the firmware team. The key question is: what happens when the bus is in an error state? Does the recovery routine properly release the bus, wait the required time, and re-initialize? I'd look for scenarios where the recovery routine could leave the bus in a state that conflicts with a slave device's internal state machine.

I'd also consider that both could be contributing. A marginal pull-up might make the bus more susceptible to noise or timing violations, and a firmware recovery routine that doesn't handle all error states properly might fail to recover when the bus is in a specific condition. The investigation should test both independently and then test them together.

Finally, I'd document everything in a shared log so both teams can see the evidence as it accumulates. The goal is to reach a conclusion that both teams agree on because the data supports it, not because one team out-argued the other.

**Possible follow-ups:**
- What specific measurements would you take to characterize the I2C bus timing, and what thresholds would you compare against?
- If the evidence shows the pull-up is marginal but the firmware recovery routine also has a bug, how would you prioritize the fixes?

---

## Q3: How would you approach a failure investigation where a medical device's analog measurement is accurate at room temperature, but shows a growing offset error as the device warms up during continuous operation — and the offset returns to zero after the device cools down?

**Answer:** A temperature-dependent offset that grows with warm-up and reverses on cool-down points to a thermal effect on a component or a connection in the analog signal path. The key is to identify which component's temperature coefficient is causing the offset, and whether it's a normal characteristic of a component operating outside its intended range or a sign of a marginal design.

I'd start by characterizing the failure precisely. I'd run the device in a controlled environment, monitoring the sensor reading and the internal temperature simultaneously. I'd also measure the temperature at key points on the PCB — the sensor, the instrumentation amplifier, the ADC, the reference, and any connectors in the signal path. This tells me which area heats up most and whether the offset correlates with a specific component's temperature.

The most common causes of temperature-dependent offset in an analog front-end are: the instrumentation amplifier's input offset voltage drift, the voltage reference's temperature coefficient, thermocouple effects at dissimilar metal junctions (especially at connectors or solder joints), and PCB stress on precision components (mechanical stress from thermal expansion can change resistor values and offset voltages).

I'd test each hypothesis by isolating the signal path. For example, I'd short the sensor input and measure the output offset as the device warms — if the offset appears with a shorted input, the problem is in the amplifier or reference, not the sensor. I'd also measure the reference voltage directly as the device warms to see if it drifts.

For thermocouple effects, I'd look at the connector between the sensor cable and the PCB. If the connector uses dissimilar metals (which most do), a temperature gradient across the connector creates a small voltage that adds to the signal. This is a classic issue in precision measurement systems and is often overlooked.

I'd also consider the PCB layout — if a precision resistor or the amplifier is near a heat source (a regulator, a processor, a motor driver), the temperature gradient across the component can create offset. Thermal imaging would help identify hot spots and temperature gradients.

Once I identify the dominant contributor, the fix could be: choosing a lower-drift amplifier or reference, moving the component away from the heat source, adding a guard trace or thermal relief, or compensating in firmware with a temperature-correction table (though this should be a last resort for a medical device, since it adds complexity and requires careful validation).

**Possible follow-ups:**
- How would you distinguish between a component's inherent temperature drift and a thermocouple effect at a connector?
- If the offset is caused by the voltage reference drifting, how would you decide between replacing the reference with a better one versus compensating in firmware?

---

## Q4: How would you approach debugging a medical device where the firmware enters a hard fault handler intermittently — roughly once every 6–12 hours — and the stack trace points to a different function each time?

**Answer:** An intermittent hard fault with a different stack trace each time is a strong indicator of memory corruption or a resource exhaustion issue rather than a single buggy function. When the stack trace points to different functions, the fault is likely a symptom of something that corrupted memory or the stack earlier, and the crash happens later when the corrupted data is used.

My first step would be to determine whether the fault is caused by: (1) a stack overflow, (2) a wild pointer or buffer overflow corrupting memory, (3) a race condition where two tasks or an ISR and a task access shared data without proper synchronization, or (4) a hardware issue like a marginal power rail or clock that causes random execution errors.

I'd start by checking the obvious: is the stack size adequate for the worst-case call depth? I'd enable stack overflow detection if the RTOS supports it, and I'd also check the stack usage statistics if available. A stack overflow would explain the intermittent nature and the varying crash locations.

If stacks look fine, I'd look at memory corruption. I'd use the memory protection unit (MPU) if the microcontroller has one, to protect critical regions and catch accesses to invalid addresses. I'd also add guard patterns around buffers and check them periodically — or use a runtime memory checker if available. The goal is to catch the corruption at the moment it happens, not when it causes a crash hours later.

I'd also review the code for common corruption sources: unchecked array indices, buffer overflows in memcpy or string operations, use-after-free, and DMA operations that write to memory without proper synchronization. The fact that the crash is intermittent suggests a timing-dependent bug — possibly a race condition between a task and an ISR, or between two tasks sharing a buffer.

For the hardware angle, I'd verify the power rails are clean and within specification, especially during transient loads. I'd also check the clock — if the device uses a PLL, a marginal configuration could cause occasional clock glitches that corrupt execution. I'd run the device in a temperature chamber to see if the failure rate changes with temperature, which would point to a marginal timing or voltage margin.

The key is to add instrumentation to catch the root cause at the moment it happens, rather than trying to analyze the crash after the fact. This means enabling the MPU, adding memory guards, logging system state (task IDs, ISR activity, stack high-water marks) at regular intervals, and possibly using a trace tool to capture the execution history leading up to the fault.

**Possible follow-ups:**
- How would you use the MPU to help diagnose this type of intermittent fault, and what regions would you protect?
- If the fault only occurs when a specific DMA channel is active, how would you investigate the interaction between DMA and the CPU's memory access?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a junior engineer on your team has been debugging an intermittent issue for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists, and they're becoming frustrated and the project schedule is tight?

**Answer:** The first thing I'd do is acknowledge the engineer's effort and the difficulty of the problem — intermittent system-level failures are genuinely hard, and testing components in isolation is a reasonable approach that just hasn't worked in this case. I'd also make it clear that the lack of progress isn't a reflection of their capability; it's a sign that the approach needs to change.

I'd then shift the investigation strategy. The key insight is that testing components in isolation won't find a system-level interaction problem — the failure only appears when components interact. So I'd guide the engineer toward system-level debugging techniques: reproducing the failure with the full system, instrumenting the system to capture data at the moment of failure, and using divide-and-conquer to isolate which subsystem interaction is involved.

I'd suggest specific techniques: adding logging at key points in the firmware to capture system state leading up to the failure, using a logic analyzer or oscilloscope to capture relevant signals during the failure, and systematically enabling/disabling subsystems to narrow down which combination triggers the problem. I'd also encourage them to look at the interfaces between components — the communication buses, the power distribution, the interrupt lines — rather than the components themselves.

I'd also offer to pair with them on the debugging session. Sometimes a fresh perspective helps, and working together can model good debugging practices. I'd ask them to walk me through what they've tried and what they've observed, because the process of explaining it often reveals assumptions or overlooked details.

Finally, I'd manage the schedule pressure by being transparent with stakeholders about the status and the plan. I'd communicate that we have a systematic approach, that we're making progress even if it's not visible yet, and that we're prioritizing finding the root cause over applying a quick fix that might not address the real problem. In a medical device context, the cost of a wrong fix is too high to rush.

The goal is to keep the engineer engaged and learning, maintain team morale, and drive the investigation to a conclusion — not to take over the investigation entirely, but to provide the support and direction needed to make progress.

**Possible follow-ups:**
- How would you decide when to take over the investigation yourself versus continuing to guide the junior engineer?
- If the engineer is resistant to changing their approach because they believe the component-level testing is the right method, how would you handle that?