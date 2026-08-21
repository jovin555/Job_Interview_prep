# debugging-failure-analysis — Day 31

## Q1: How would you approach a failure investigation where a medical device's firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory being copied is within bounds?

**Answer:** This is a classic case where the stack trace tells you *where* the fault manifested, but not necessarily *why*. The first principle is to distrust the stack trace as the root cause location — it's just the point where the corruption or fault became visible. I'd structure the investigation in phases:

First, I'd verify the fault is real and reproducible. I'd capture the full fault context: the fault status register (e.g., which bus error, usage fault, or hard fault), the link register value, and the stacked registers (R0–R3, R12, LR, PC, xPSR). The stacked PC and LR are critical — they tell me where the processor was when the fault occurred, and the LR tells me what called that function.

Second, I'd look at the memory copy operation itself. Even though the addresses are "valid" and "within bounds," I'd check:
- Is the copy length correct? A length that's off by one or two bytes could still be "within bounds" of the destination buffer but overwrite adjacent data.
- Is the copy source actually initialized? Copying from uninitialized memory could produce valid-looking addresses but garbage data.
- Is there a race condition where another interrupt or DMA operation is modifying the source or destination during the copy?

Third, I'd suspect memory corruption from elsewhere. A common pattern is that the stack trace points to a memcpy or similar operation, but the real culprit is a buffer overflow or use-after-free elsewhere that corrupted the stack or heap metadata. I'd check:
- Is the stack pointer valid? Stack overflow is a prime suspect — the fault could be occurring because the stack grew into an invalid region.
- Are there any watchdog or DMA operations that could be writing to unexpected locations?
- Is the memory copy operation itself being called from an interrupt context where it shouldn't be?

Fourth, I'd instrument the system. I'd add stack watermark monitoring (checking the maximum stack usage), memory protection unit (MPU) regions around critical buffers to catch out-of-bounds writes, and I'd log the fault context to non-volatile memory so I can correlate the fault with other system events.

Finally, I'd consider the hardware angle. If the fault is intermittent and the code is provably correct, I'd look at:
- Power supply integrity during the copy operation — a glitch on the core voltage during a burst of memory activity could cause a fault.
- Clock integrity — if the system uses a PLL or clock switching, a glitch could cause a bus error.
- EMC susceptibility — if the fault correlates with motor activity, wireless transmission, or other noise sources.

The key is to avoid the trap of assuming the stack trace is the root cause. It's the symptom location. The investigation needs to trace backward from the fault to the actual trigger.

**Possible follow-ups:**
- How would you use the MPU to help diagnose this type of issue without changing the system's behavior?
- What specific information would you want to capture in the fault handler to aid the investigation?

---

## Q2: How would you approach debugging a medical device where a specific analog input channel reads correctly when measured directly at the ADC input with an oscilloscope, but the firmware consistently reports a value that is offset by a fixed amount — and the offset is different on different units of the same device?

**Answer:** This is a fascinating discrepancy because it tells me the analog signal at the ADC pin is correct, but the digital value the firmware reads is wrong. The offset being different across units is a critical clue — it suggests a unit-to-unit variation in some component or a calibration issue rather than a systematic design error.

I'd start by verifying the measurement methodology. When the oscilloscope probe is on the ADC input, the probe itself adds capacitance and loading that could affect the signal. I'd want to confirm the scope reading is truly representative of what the ADC sees during its sampling window. I'd check:
- Is the scope probe loading the node? A 10x probe adds ~10pF, which could interact with the source impedance and cause settling issues.
- Is the ADC sampling time sufficient for the source impedance? If the source impedance is high and the sampling capacitor is large, the ADC might not fully charge to the input voltage within the sampling window. This would cause a gain error, not just an offset, but it's worth checking.
- Is the ADC reference voltage correct? If the reference is slightly off, the conversion result would be scaled, which could look like an offset at a specific input level.

The unit-to-unit variation points me toward component tolerances. I'd look at:
- The ADC reference circuit — if there's a reference buffer or divider with resistor tolerances, each unit would have a slightly different reference voltage.
- The input conditioning circuit — if there's an op-amp or filter with offset voltage specs, the offset would vary with the specific component installed.
- The ADC's internal offset calibration — many ADCs have a calibration register that might not be initialized correctly, or the calibration values might be stored in non-volatile memory and corrupted.

I'd also question the firmware's interpretation of the ADC result. Is there any post-processing that could introduce an offset? For example:
- Is the firmware applying a calibration offset that's stored in EEPROM? If the calibration data is corrupted or was never written correctly, each unit could have a different offset.
- Is the firmware reading the correct ADC channel? A mux configuration error could read a different channel that has a DC bias.
- Is the firmware using the correct data format? If the ADC outputs a signed value but the firmware interprets it as unsigned (or vice versa), you'd see a fixed offset.

My approach would be to:
1. Capture the raw ADC register value and compare it to the expected value from the scope measurement.
2. Check the ADC configuration registers — sampling time, reference selection, gain settings, and calibration status.
3. Measure the actual reference voltage on each unit and compare it to the expected value.
4. Check the input conditioning circuit components — measure the actual resistor and capacitor values, and verify the op-amp offset voltage if applicable.
5. Review the firmware's ADC reading and post-processing code for any offset or scaling operations.

The key insight is that the scope shows the analog signal is correct, so the problem is in the conversion process or the digital interpretation. The unit-to-unit variation narrows it to component tolerances or per-unit calibration data.

**Possible follow-ups:**
- How would you distinguish between an ADC reference issue and an input conditioning issue?
- What if the offset is proportional to the input voltage rather than fixed — how would that change your approach?

---

## Q3: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This is a compatibility issue that points to a difference between the two chargers rather than a defect in the device itself. The device works with its intended charger but misbehaves with a specific third-party charger. I'd approach this systematically:

First, I'd characterize the two chargers. I'd measure:
- Output voltage under no load and under load — some chargers have poor regulation and their output voltage can sag or rise significantly.
- Output voltage ripple and noise — a charger with excessive ripple could confuse the device's charging controller.
- The charger's current limit behavior — some chargers have a "fold-back" current limit that reduces voltage when current exceeds a threshold, while others shut down entirely.
- The charger's startup behavior — some chargers ramp up slowly, others have a brief overvoltage spike at power-on.

Second, I'd look at the device's charging circuit. The excessive current draw suggests the charger is being asked to deliver more current than it can handle, or the device is not properly negotiating the charging current. I'd check:
- Is the device's charging current set correctly? If the device requests more current than the charger can provide, the charger's voltage would sag, and the device might compensate by drawing even more current.
- Is there an inrush current issue at power-on? Some chargers have a soft-start feature, and if the device's input capacitance is large, the inrush current could exceed the charger's limit.
- Is the device's input protection circuit (if any) functioning correctly? A faulty input FET or diode could cause excessive current draw.

Third, I'd consider the USB negotiation protocol. If the device uses USB BC1.2 or USB-PD to negotiate charging current, the specific charger might not implement the protocol correctly, or the device might misinterpret the charger's capabilities. I'd check:
- Does the device detect the charger type correctly? If the device misidentifies the charger as a "dedicated charging port" when it's actually a "standard downstream port," it might request more current than the charger can provide.
- Does the charger advertise its current capability correctly? Some chargers have incorrect or non-compliant advertisement resistors.

Fourth, I'd reproduce the issue in a controlled manner. I'd connect the device to the problematic charger and measure:
- The input current over time — is it a constant excessive draw, or does it spike at specific moments?
- The input voltage during the excessive current draw — is the charger's output collapsing?
- The device's charging IC behavior — is it entering a fault mode, or is it trying to draw more current than the charger can supply?

Finally, I'd determine whether this is a device design issue or a charger compatibility issue. If the device is compliant with the relevant USB charging specifications, and the charger is non-compliant, the fix might be to document the incompatibility or add a more robust input current limiting circuit. If the device is over-requesting current, the fix would be in the device's charging algorithm or hardware.

The key is to understand the interaction between the device and the charger — it's a system-level issue, not just a device-level or charger-level problem.

**Possible follow-ups:**
- How would you determine whether the excessive current is a steady-state condition or an inrush transient?
- What specific measurements would you take to characterize the charger's behavior under load?

---

## Q4: How would you approach a failure investigation where a medical device's wireless communication works reliably in the lab, but in the clinical environment, the device intermittently fails to transmit data — and the failures correlate with times when the hospital's paging system is active?

**Answer:** This is a classic electromagnetic interference (EMI) problem where the clinical environment presents a radio frequency (RF) environment that the lab doesn't replicate. The correlation with the paging system is a strong clue that the interference is coming from that specific source. I'd approach this in stages:

First, I'd characterize the interference source. I need to understand:
- What frequency band does the paging system use? Many hospital paging systems operate in the VHF/UHF bands (e.g., 150 MHz, 450 MHz), but some use 900 MHz or even 2.4 GHz.
- What is the transmit power and duty cycle? A paging system that transmits frequently with high power could cause more interference than one that transmits rarely.
- Is the interference continuous or pulsed? Paging systems often transmit in bursts, which could explain the intermittent nature of the failures.

Second, I'd characterize the device's vulnerability. I'd look at:
- What frequency band does the device's wireless communication use? If the device uses 2.4 GHz (e.g., Bluetooth or Wi-Fi), the paging system at 450 MHz shouldn't directly interfere — but it could cause out-of-band interference or intermodulation products.
- What is the device's receiver sensitivity and selectivity? A receiver with poor selectivity could be desensitized by a strong out-of-band signal.
- Is the device's antenna properly matched and shielded? A poorly matched antenna could pick up interference on its cable or traces.

Third, I'd reproduce the issue in a controlled environment. I'd use a signal generator to simulate the paging system's signal and test the device's response. I'd vary:
- The frequency of the interfering signal — to find the frequencies where the device is most vulnerable.
- The power level — to find the threshold where the device starts to fail.
- The modulation type — to see if the interference is CW (continuous wave) or modulated.

Fourth, I'd investigate the coupling path. The interference could be:
- Radiated — the paging signal is picked up directly by the device's antenna or PCB traces.
- Conducted — the interference is picked up by the device's power cable or other external connections.
- Common-mode — the interference is converted to a common-mode signal on the device's cables, which then couples into the wireless module.

I'd use near-field probes to scan the device's PCB and identify where the interference is entering. I'd also check the device's grounding and shielding — a poorly grounded shield can actually make things worse by creating a resonant structure.

Fifth, I'd look at the device's firmware and protocol. The failure might not be a hardware issue at all:
- Is the device's wireless protocol robust against interference? Does it have retransmission, error correction, or channel hopping?
- Is the device's firmware handling the interference correctly? For example, if the wireless module reports a "busy" condition, does the firmware retry or give up?
- Is there a coexistence issue with other wireless devices in the clinical environment? The paging system might not be the direct cause — it might be correlated with other equipment that's active at the same time.

Finally, I'd implement and verify a fix. Depending on the root cause, the fix could be:
- Adding shielding or filtering to the device's enclosure or PCB.
- Improving the antenna design or placement.
- Adding a band-pass filter to the receiver front-end.
- Modifying the firmware to be more robust against interference (e.g., more retries, channel hopping).
- Changing the device's wireless protocol or frequency band.

The key is to understand the interference mechanism — frequency, power, coupling path — before implementing a fix. A fix that addresses the wrong mechanism could make things worse.

**Possible follow-ups:**
- How would you determine whether the interference is being picked up by the antenna or conducted through the power cable?
- What specific tests would you run to verify that your fix actually resolves the issue in the clinical environment?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a senior engineer on your team is convinced they know the root cause based on their experience with a similar device, but the evidence doesn't fully support their hypothesis — and they're pushing to implement a fix before the investigation is complete?

**Answer:** This is a common and challenging situation in failure investigations. The senior engineer's experience is valuable, but acting on an unconfirmed hypothesis risks implementing an ineffective fix, wasting time and resources, and potentially masking the real root cause. I'd handle this carefully, respecting the engineer's expertise while ensuring the investigation follows sound methodology.

First, I'd acknowledge the engineer's hypothesis and the value of their experience. I'd say something like, "I appreciate you sharing your experience with similar devices — that's exactly the kind of insight we need. Let's work together to validate this hypothesis against the evidence we have."

Second, I'd ask the engineer to articulate the full chain of reasoning from the observed symptom to their proposed root cause. I'd ask questions like:
- "What specific evidence in this case supports this hypothesis?"
- "What would we expect to see if this hypothesis is correct — what other symptoms or test results would confirm it?"
- "What evidence might we see that would contradict this hypothesis?"
- "Are there any aspects of this case that differ from the similar device you worked on?"

This approach does two things: it shows respect for the engineer's expertise, and it helps identify gaps in the reasoning. Often, when someone articulates their reasoning, they discover the gaps themselves.

Third, I'd propose a structured validation plan. Instead of saying "no, we can't implement the fix," I'd say, "Let's design a test that would confirm or refute this hypothesis. If the test confirms it, we can implement the fix with confidence. If it doesn't, we'll have learned something valuable and can move on to the next hypothesis." This reframes the situation from "you're wrong" to "let's prove it together."

The test should be:
- Specific — it should directly test the proposed mechanism.
- Measurable — it should produce a clear pass/fail result.
- Time-boxed — it shouldn't take weeks to run.
- Safe — it shouldn't risk patient safety or damage equipment.

Fourth, I'd manage the project schedule. If the engineer is pushing for a quick fix because of schedule pressure, I'd acknowledge that pressure and explain that a fix based on an unconfirmed hypothesis could actually delay the project further if it doesn't work. I'd also explore whether there are interim mitigation measures we can implement while the investigation continues — for example, a temporary workaround that reduces the risk without claiming to be the final fix.

Fifth, I'd document everything. I'd record the hypothesis, the reasoning, the validation test, and the results. This creates a clear audit trail and ensures that if the hypothesis is later confirmed or refuted, the decision-making process is transparent.

Finally, if the engineer continues to push despite the evidence, I'd escalate appropriately. I'd have a private conversation to understand their concerns — maybe they have information I don't have, or maybe they're under pressure from someone else. I'd also involve the project manager or quality manager if needed, explaining the risk of implementing an unvalidated fix in a medical device context.

The key principles are: respect the engineer's experience, validate hypotheses with evidence, maintain the integrity of the investigation process, and manage the tension between thoroughness and schedule pressure.

**Possible follow-ups:**
- What would you do if the validation test is inconclusive — it neither confirms nor refutes the hypothesis?
- How would you handle a situation where the senior engineer goes over your head to a manager to push for the fix?