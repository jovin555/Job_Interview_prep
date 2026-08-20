# debugging-failure-analysis — Day 30

## Q1: How would you approach a failure investigation where a medical device's firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory being copied is within bounds?

**Answer:** This is a classic case where the stack trace is telling you *where* the fault manifests, but not necessarily *why*. When the memory copy operation itself checks out — valid addresses, correct bounds — I'd broaden the investigation beyond the copy routine itself.

First, I'd verify the stack trace is trustworthy. In deeply embedded systems, a corrupted stack pointer or a fault that occurs during an interrupt can produce a misleading backtrace. I'd check whether the hard fault handler itself is saving context correctly, and whether the stack pointer at the time of the fault is within the expected stack region. If the stack has overflowed or been corrupted, the trace could point to a victim rather than the culprit.

Next, I'd look at what's happening *around* the copy operation. Is the copy being performed from within an interrupt service routine? Is a DMA controller involved that might be writing to the same memory region concurrently? Is there any chance the source buffer is being modified by another task or ISR while the copy is in progress? A classic failure mode is a race condition where one context is writing to a buffer while another context is copying from it — the copy itself is fine, but the data changes mid-operation, and the fault is actually a symptom of a corrupted heap or stack elsewhere.

I'd also examine the memory map. Even if the source and destination addresses are "valid" in the sense that they point to allocated regions, are they pointing to the right *kind* of memory? For example, if the copy is from flash to RAM, but the source address calculation has an off-by-one that lands in a reserved region, the fault might be reported at the copy instruction but the real issue is the address calculation upstream.

Finally, I'd instrument the system. I'd add a watchdog or a periodic stack watermark check, log the program counter and link register at the point of the copy, and capture the full register file when the fault occurs. If the fault is intermittent, I'd want to capture several occurrences and compare them — looking for a pattern in the register values, the state of other peripherals, or the timing relative to other system events.

**Possible follow-ups:**
- How would you distinguish between a stack overflow and a heap corruption when the stack trace points to a valid-looking function?
- What specific instrumentation would you add to capture the state at the moment of the fault, given that the fault occurs only every 6–12 hours?

---

## Q2: How would you approach a failure investigation where a medical device's power supply exhibits a periodic voltage dip on a 3.3V rail — about 200mV for 50 microseconds, occurring every 100ms — and the device occasionally resets during these dips, but not consistently?

**Answer:** The periodicity is the key clue here. A 100ms period is too slow for a switching regulator's normal ripple — that would be in the kHz to MHz range. So something is drawing current in a periodic pattern, and I'd want to find what's synchronized to that 100ms interval.

My first step would be to correlate the dip with system activity. I'd check whether the 100ms period matches any firmware task scheduling, a sensor sampling interval, a wireless beacon, or a display refresh. I'd use a current probe on the 3.3V rail and a logic analyzer or oscilloscope to capture the dip alongside key digital signals — like the ADC conversion start, the radio TX enable, or a GPIO toggling. If the dip aligns with a specific event, that narrows the investigation considerably.

Once I identify the load event, I'd look at the power supply's transient response. A 200mV dip for 50 microseconds suggests the supply isn't responding fast enough to a sudden current draw. I'd check the output capacitor selection — is there enough bulk capacitance to handle the transient? Is the capacitor's ESR low enough? I'd also look at the regulator's bandwidth and whether it's stable under load transients. Sometimes the issue is that the regulator's compensation is marginal, and a periodic load step pushes it into instability.

I'd also consider the possibility that the dip is not on the rail itself but is a measurement artifact. If I'm probing at the regulator output, I might be seeing the effect of a load that's physically distant — the PCB trace inductance between the regulator and the load creates a voltage drop that's not visible at the regulator's sense point. I'd probe at the load's decoupling capacitors and compare the waveform to the regulator output.

Regarding the intermittent resets: the fact that the device doesn't always reset during the dip tells me the reset threshold is marginal. I'd check the microcontroller's brown-out reset (BOR) threshold and compare it to the actual minimum voltage during the dip. If the dip is right at the edge of the threshold, small variations in temperature, load current, or capacitor aging could push it over. I'd also check whether the reset is actually caused by the voltage dip at all — it could be a coincidence, and the reset might be triggered by a separate event that happens to correlate with the dip.

**Possible follow-ups:**
- How would you determine whether the fix should be in the power supply design (more capacitance, better regulator) or in the firmware (spreading the load over time)?
- What measurements would you take to confirm whether the reset is actually caused by the voltage dip versus a coincidental event?

---

## Q3: How would you approach a failure investigation where a medical device's wireless communication works reliably in the lab, but in the clinical environment, the device intermittently fails to transmit data — and the failures correlate with times when the hospital's paging system is active?

**Answer:** This is a classic electromagnetic interference (EMI) problem, and the correlation with the paging system is a strong lead. The paging system is likely operating at a frequency that's either close to the device's communication frequency or generating harmonics that fall within the device's receive band.

My first step would be to characterize the interference. I'd use a spectrum analyzer with a near-field probe to measure the RF environment in the clinical area during paging activity. I'd want to identify the paging system's frequency, modulation, and power level, and determine whether the interference is in-band (directly competing with the device's signal) or out-of-band (causing desensitization or intermodulation in the receiver front-end).

Next, I'd examine the device's receiver performance. If the paging signal is in-band, the issue might be receiver selectivity — the device's front-end filter isn't attenuating the paging signal enough, and the receiver is being desensitized. If the paging signal is out-of-band, I'd look at the receiver's linearity — a strong out-of-band signal can drive the LNA into compression or generate intermodulation products that fall in-band.

I'd also look at the device's own emissions. The paging system might be interfering with the device, but the device might also be interfering with itself — for example, if the device's own transmitter creates a spurious emission that coincides with the paging frequency, and the two signals mix in the receiver.

From a hardware perspective, I'd review the antenna design and placement. Is the antenna properly matched? Is there adequate shielding between the radio section and other circuitry? Are the ground planes solid? I'd also check the device's firmware — is the communication protocol robust against interference? Does it have retransmission, error correction, or channel hopping? If the protocol assumes a clean channel, a small amount of interference could cause failures.

Finally, I'd consider the regulatory angle. The hospital's paging system is licensed and operating within its allocated band. The medical device needs to coexist with it. If the interference is unavoidable, the solution might be to change the device's communication frequency, add filtering, or improve the protocol's resilience. I'd document the findings and work with the regulatory team to determine whether the device's immunity needs to be improved to meet the clinical environment's requirements.

**Possible follow-ups:**
- How would you distinguish between the paging system causing receiver desensitization versus the device's own emissions mixing with the paging signal?
- What protocol-level changes would you consider to improve resilience against intermittent interference?

---

## Q4: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This points to a compatibility issue between the device's charging circuit and the third-party charger's electrical characteristics. The first thing I'd do is characterize both chargers — measure their output voltage, current capability, and transient response under load. I'd also look at their communication protocols, if any, since USB chargers can negotiate voltage and current through the D+ and D- lines.

A common cause is inrush current. When the device is connected to a charger, the charging circuit's input capacitors charge up rapidly. If the charger has a soft-start feature or a current limit that's set differently than the shipped charger, the inrush current might exceed the charger's capability, causing the charger to fold back or oscillate. This could manifest as excessive current draw from the wall — the charger is trying to supply the inrush but is being held in a current-limit state.

Another possibility is that the third-party charger has a different output voltage. If it's slightly higher than the shipped charger, the charging circuit's input voltage protection might be operating at the edge of its threshold, causing the circuit to oscillate between charging and protection modes. This oscillation could draw excessive current from the wall.

I'd also check the USB data lines. Some chargers use the D+ and D- voltages to signal their current capability. If the third-party charger uses a different signaling scheme, the device might be requesting more current than the charger can actually supply, causing the charger to sag or shut down, which then causes the device to retry — creating a cycle of high current draw.

My investigation would start with a bench setup: I'd connect the device to the third-party charger and measure the input current, the voltage at the device's charging input, and the charger's output voltage and current simultaneously. I'd use an oscilloscope to capture the startup transient and look for oscillation or current limiting. I'd also test the device with a programmable DC supply to simulate the third-party charger's characteristics and identify the specific parameter that triggers the issue.

The fix might be in the device's charging circuit — adding input capacitance, adjusting the inrush limiter, or improving the input voltage protection — or it might be a firmware change to the charging algorithm to be more conservative when negotiating current with unknown chargers.

**Possible follow-ups:**
- How would you determine whether the issue is inrush current, voltage mismatch, or a communication protocol issue on the USB data lines?
- What design changes would you consider to make the device more robust across different chargers without compromising charging speed?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a senior engineer on your team is convinced they know the root cause based on their experience with a similar device, but the evidence doesn't fully support their hypothesis — and they're pushing to implement a fix before the investigation is complete?

**Answer:** This is a common and delicate situation. The senior engineer's experience is valuable, and their hypothesis deserves serious consideration — but implementing a fix based on an unconfirmed root cause in a medical device is risky, both for patient safety and for regulatory compliance.

My approach would be to acknowledge their expertise and take their hypothesis seriously, then work to either confirm or refute it with evidence. I'd frame it as: "Your experience with similar devices is exactly why we need to test this hypothesis thoroughly — if it's correct, we want to be confident in the fix, and if it's not, we want to find out before we commit to a change."

I'd propose a structured test plan that specifically targets their hypothesis. If their hypothesis predicts a certain behavior, we can design an experiment to verify it. For example, if they believe a specific component is marginal, we can test that component under the conditions that would expose the failure. If the test confirms their hypothesis, we proceed with confidence. If it doesn't, we have data to discuss.

I'd also make sure the investigation is following a proper root-cause analysis process — like 8D — where each hypothesis is evaluated against the evidence, and the root cause is confirmed before corrective action is implemented. This gives us a framework for the discussion that's objective rather than personal.

If the engineer continues to push for a fix before the evidence is conclusive, I'd escalate the discussion to the project's risk management process. In a medical device context, we have a responsibility to document the rationale for any design change, and the regulatory file needs to show that the root cause was properly identified. I'd explain that implementing a fix prematurely could lead to a recurrence of the failure, which would be worse for the project and for patient safety.

Finally, I'd keep the team focused on the goal — finding the actual root cause — rather than on who's right. I'd acknowledge that the engineer's experience is an asset, but the evidence is the ultimate authority. If needed, I'd bring in an independent reviewer to evaluate the evidence and the proposed fix, which can help defuse the situation by making it a technical discussion rather than a personal one.

**Possible follow-ups:**
- How would you handle the situation if the senior engineer's hypothesis is eventually proven wrong, and they've invested significant time and credibility in it?
- What would you do if the senior engineer goes over your head to a manager to push for the fix?