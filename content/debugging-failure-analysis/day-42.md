# debugging-failure-analysis — Day 42

## Q1: How would you approach debugging a medical device where a firmware update appears to have introduced a new intermittent failure — the device occasionally resets during normal operation, and the resets began only after the update was deployed to the field?

**Answer:** I'd start by treating this as a regression investigation, which means first establishing a clear baseline. The critical question is whether the hardware changed, the firmware changed, or both — and in this case, we know the firmware changed. The first step would be to confirm the reported symptom is genuinely new and not simply more visible now (for example, if the update added logging that reveals resets that were always happening). I'd review the firmware change log and diff to identify which subsystems were touched — clock configuration, interrupt priorities, watchdog setup, power management, or peripheral initialization are common culprits for reset-related regressions.

Next, I'd try to reproduce the issue in a controlled environment. If I can't reproduce it on the bench, I'd look at what's different in the field: battery state, temperature, user interaction patterns, or timing of events. I'd also examine the reset cause register or equivalent hardware status bits on returned units — this tells you whether the reset was from a watchdog timeout, brown-out, software-triggered reset, or external pin. That single piece of data narrows the investigation dramatically.

If the reset cause points to a watchdog timeout, I'd look at whether the firmware update changed task timing, added a blocking operation, or altered interrupt latency in a way that starves the watchdog feed. If it points to a brown-out, I'd investigate whether the update increased current consumption — for example, by enabling a peripheral that was previously disabled, or changing the CPU clock frequency. I'd also check whether the update changed the order of initialization such that a peripheral is drawing current before the power supply is fully settled.

The key principle is to use the evidence from the device itself — reset cause registers, fault logs, and any debug output — before forming hypotheses. I'd also consider rolling back the firmware on a small sample of affected units to confirm the update is indeed the trigger, which is a clean A/B test.

**Possible follow-ups:**
- How would you determine whether the issue is a firmware timing problem versus a hardware marginality that the new firmware simply exposes?
- What specific information would you ask the field service team to collect from affected devices before they power-cycle them?

---

## Q2: Walk me through your approach to a failure investigation where a medical device's analog measurement is accurate at power-up, but drifts over several hours of continuous operation — and the drift direction reverses when the device is turned off and restarted.

**Answer:** This pattern — drift that accumulates during operation and resets on power cycle — strongly suggests a thermal or self-heating effect, or possibly a charge-accumulation effect like dielectric absorption or electrochemical phenomena. I'd approach this systematically.

First, I'd characterize the drift precisely: is it monotonic, does it plateau, does it correlate with any measurable parameter like case temperature, board temperature, or power consumption? I'd instrument the device with thermocouples at key locations — near the sensor, the reference voltage, the ADC, and the input conditioning circuitry — and log both temperature and the measured value over time. If the drift tracks temperature, that's a strong lead.

The most common root causes in this scenario are: a voltage reference that drifts with temperature, an instrumentation amplifier with an input bias current that changes with temperature, a sensor that self-heats due to excitation current, or a PCB-level effect like moisture absorption or mechanical stress relaxation in solder joints or the sensor package.

I'd also look at the power supply to the analog front-end. If a regulator's output drifts with temperature, that directly affects the measurement. I'd measure the reference voltage and supply rails over the same time window to see if they drift in correlation with the measurement error.

Another angle: if the device uses a bridge-type sensor, the excitation voltage matters. A small drift in the excitation source appears as a proportional measurement error. I'd verify the excitation is stable and that the ADC's reference is truly ratiometric with the sensor excitation.

Finally, I'd consider firmware effects — for example, if the ADC's sampling timing changes as the system warms up (due to clock drift), or if an averaging filter has a subtle bug that accumulates error. I'd rule these out by logging raw ADC codes alongside the processed values.

**Possible follow-ups:**
- How would you distinguish between a sensor drift problem and a signal-chain drift problem?
- What role would accelerated life testing or temperature cycling play in confirming your hypothesis?

---

## Q3: How would you approach a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent communication failure is caused by a marginal PCB layout issue or by a firmware timing violation — the device occasionally fails to complete a sensor read over SPI, and the failure rate increases as the device warms up?

**Answer:** This is a classic cross-disciplinary disagreement, and the first thing I'd do is establish a shared evidence base rather than let either team argue from theory. The temperature correlation is a valuable clue — it suggests a marginal timing margin that degrades as components heat up, which could be either electrical (trace capacitance, driver strength, pull-up values changing with temperature) or firmware-related (timing loops that assume a fixed clock rate, or interrupt latency that increases with temperature due to other activity).

I'd structure the investigation around three parallel tracks. First, characterization: instrument the SPI bus with a logic analyzer or oscilloscope and capture actual waveforms during failures — measure setup/hold times, clock edge placement, and signal integrity parameters like rise time and ringing. This gives us ground truth about what's happening electrically at the moment of failure.

Second, firmware analysis: review the SPI driver code for any timing assumptions — for example, hard-coded delays, polling loops with no timeout, or shared resources that could cause the SPI transaction to be delayed by an interrupt. I'd also check whether the firmware verifies the SPI peripheral's busy flag correctly, and whether there's a race between the SPI transaction and a higher-priority interrupt.

Third, hardware analysis: look at the PCB layout for the SPI traces — trace length, impedance, ground return path, and proximity to noisy components. I'd measure the actual signal integrity at the receiver pins, not just at the driver, because the failure is at the receiving end.

The key experiment would be to create a controlled stress test — for example, running the SPI at different clock speeds and temperatures to find the margin boundary. If the failure occurs at a clock speed well below the rated maximum, that points to a hardware margin issue. If the failure only occurs when specific firmware conditions are met (like a particular interrupt firing), that points to firmware.

I'd also look for a way to make the failure deterministic. If we can trigger it reliably, we can test one variable at a time — changing the SPI clock speed, adding a delay, or modifying the layout — to isolate the cause. The goal is to reach a point where both teams agree on the evidence, even if they initially disagree on the interpretation.

**Possible follow-ups:**
- How would you handle the situation if the evidence is genuinely ambiguous and both hypotheses remain plausible?
- What would you do to prevent this type of cross-team disagreement in future projects?

---

## Q4: How would you approach debugging a medical device where the failure occurs only when the device is used by a specific patient population — for example, elderly users who tend to hold the device in a particular way — and the failure is a touchscreen that becomes unresponsive after several minutes of use?

**Answer:** This is a fascinating case because the variable isn't just the device — it's the interaction between the device and its user. The fact that the failure correlates with a specific user population suggests a physical interaction mechanism rather than a purely electronic one.

I'd start by trying to understand exactly how these users hold and interact with the device. I'd observe the usage pattern, or work with the clinical team to document it — hand position, grip pressure, whether the device is resting on a surface or held, and whether any part of the hand or body is in contact with specific areas of the device. The key question is: what's different about this interaction compared to other users?

Several mechanisms could explain the symptom. First, capacitive touchscreens can become unresponsive if there's a conductive path from the user's body to the device's ground or to the touch controller's reference — for example, if the user's hand bridges the touch surface to a grounded metal part of the enclosure. Second, the device might be experiencing a ground potential shift or common-mode noise injection when held in a particular way. Third, the touch controller's sensitivity settings might be marginal, and the specific capacitance presented by these users' hands (which can vary with skin moisture, calluses, or contact area) pushes it over the threshold.

I'd also consider mechanical factors — if the user grips the device in a way that flexes the PCB, it could create intermittent contact issues in the touch controller's connections or change the capacitance of the touch sensor.

My approach would be to instrument the device during actual use — or a simulation of the use pattern — and capture the touch controller's raw data, including signal-to-noise ratio, baseline values, and any error flags. I'd also measure the device's ground potential relative to the user and to any nearby grounded objects. If possible, I'd try to reproduce the failure with a test setup that mimics the user's hand — a grounded conductive pad or a saline-filled glove can simulate the electrical characteristics of a hand.

Once I understand the mechanism, the fix could be in firmware (adjusting touch sensitivity, adding a noise filter, or recalibrating the baseline), in hardware (improving grounding, adding shielding, or changing the touch sensor layout), or in the mechanical design (changing the enclosure to prevent the user's hand from bridging certain areas).

**Possible follow-ups:**
- How would you involve the clinical team or human factors engineers in this investigation?
- What would you do if you couldn't reproduce the failure in a controlled setting?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and you discover that the root cause points to a design decision made by a senior engineer who is still on the team — and the finding could reflect poorly on them or create tension within the group?

**Answer:** This is a situation where the technical investigation is straightforward, but the human dynamics require careful handling. The first principle is that the investigation's purpose is to find the root cause and prevent recurrence — not to assign blame. I'd keep that framing front and center throughout.

My approach would be to present the findings as a system issue rather than an individual error. In most cases, a design decision that later proves problematic was reasonable given the information available at the time — the failure typically emerges from a combination of factors, not a single mistake. I'd look for the full context: what constraints existed when the decision was made, what information was available, and what assumptions have since changed.

Before going public with the findings, I'd have a private conversation with the senior engineer. I'd share the evidence, explain the investigation's conclusion, and give them the opportunity to provide additional context or alternative interpretations. This isn't about softening the truth — it's about ensuring the findings are complete and accurate before they're shared more broadly. The engineer might have information about the decision that the investigation didn't uncover.

When presenting to the wider team, I'd focus on the corrective actions and the system improvements that will prevent similar issues — for example, adding a design review checkpoint, improving the verification process, or documenting assumptions more thoroughly. I'd frame it as: "We found a gap in our process, and here's how we'll close it."

I'd also be mindful of the power dynamics. If the senior engineer is defensive, I'd acknowledge their perspective and invite them to contribute to the corrective action plan — this gives them a constructive role and helps maintain their engagement. If the engineer is receptive, I'd acknowledge the difficulty of the decision they made and the value of their experience in moving forward.

The goal is to maintain a culture where failures are seen as learning opportunities, not as personal failings. This is especially important in medical device development, where the ability to report and investigate issues openly is critical for patient safety.

**Possible follow-ups:**
- How would you handle the situation if the senior engineer becomes defensive and disputes the findings?
- How would you ensure that the corrective actions are implemented without creating resentment or resistance?