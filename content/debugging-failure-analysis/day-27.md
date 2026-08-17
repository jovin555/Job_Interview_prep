# debugging-failure-analysis — Day 27

## Q1: How would you approach a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent reset is caused by a firmware bug or a hardware issue — the device resets randomly, sometimes multiple times per day, sometimes not for a week, and the watchdog timer is expiring just before each reset?

**Answer:** The watchdog expiring is a symptom, not a root cause — the watchdog is doing its job by resetting a system that has stopped being serviced. The real question is why the firmware stops feeding the watchdog. I'd structure this investigation around three parallel tracks.

First, I'd work on improving observability. The current logs apparently don't capture enough context around the reset events. I'd add a crash logger that records the program counter, stack pointer, and a portion of the stack contents at the moment the watchdog fires, plus a "last known good" state variable that tracks where in the main loop or which task was executing. I'd also capture the state of key peripherals — particularly any that generate interrupts — and the values of critical GPIO pins. This data often immediately distinguishes between a firmware hang (the PC will be in a consistent region of code) and a hardware-induced issue (the PC may be random, or the system may be resetting before firmware even runs).

Second, I'd examine the hardware side for conditions that could cause the firmware to hang or crash. This includes checking the power supply for glitches or droops that could cause a brownout or a flash corruption, verifying that the clock source is stable, and looking for noise coupling into reset or interrupt lines. I'd also check whether any peripheral could be holding the bus in a state that causes the firmware to block indefinitely — for example, an I2C or SPI transaction that never completes because a device is holding the clock line low.

Third, I'd look at the firmware architecture itself. Common causes of watchdog expiries include interrupt storms — where a peripheral generates interrupts faster than the ISR can clear them, starving the main loop — and priority inversion where a low-priority task holds a resource that a high-priority task needs. I'd also review whether any code path disables interrupts for extended periods, which would prevent the watchdog from being serviced even though the CPU appears to be running.

The key to resolving the cross-team disagreement is to stop debating hypotheses and instead gather data that discriminates between them. I'd push both teams to agree on what evidence would convince them, then work together to instrument the system to capture that evidence.

**Possible follow-ups:**
- How would you decide whether to increase the watchdog timeout as an interim mitigation while the investigation continues?
- What specific crash-logging techniques would you use on a resource-constrained MCU with limited flash and RAM?

---

## Q2: How would you approach debugging a signal integrity issue where a high-speed SPI bus between a microcontroller and an ADC shows intermittent bit errors, but only when the device's motor driver is active?

**Answer:** This is a classic coupled-noise problem — the motor driver is the aggressor and the SPI bus is the victim. I'd approach this systematically, starting with characterization before attempting any fix.

First, I'd reproduce the failure reliably and characterize the timing relationship. I'd trigger an oscilloscope on the motor driver's switching activity and look at the SPI lines simultaneously. The key questions are: Do the bit errors occur at the moment of motor commutation, or continuously while the motor runs? Are the errors on the clock line, the data line, or both? What's the timing relationship between the motor switching edge and the corrupted bit?

Next, I'd determine the coupling mechanism. There are three main possibilities: conducted noise through the shared power supply, radiated coupling from the motor cables or the motor itself, and ground bounce from the motor current returning through a shared ground path. To discriminate, I'd use near-field probes to map where the noise is strongest, and I'd measure the voltage difference between the MCU ground and the ADC ground during motor operation. I'd also check whether the SPI signals are corrupted at the source (MCU pins) or only at the receiver (ADC pins) — this tells you whether the noise is being injected into the driver or into the transmission line.

Once I understand the coupling path, I'd evaluate mitigation options in order of preference. If it's ground bounce, I'd look at the return current path — is the motor current sharing a ground trace with the digital circuitry? A star-ground or separate ground plane for the motor driver is often the right fix. If it's power supply noise, I'd check the decoupling on the MCU and ADC supply pins and consider a ferrite bead or pi-filter on the motor supply. If it's radiated coupling, I'd look at the SPI trace routing — are the traces running near the motor cables? Are they properly impedance-controlled with a solid return plane? I might also consider reducing the SPI clock rate if the timing margin allows, or adding series termination to reduce ringing.

The important principle is to make one change at a time and verify the effect. I'd also consider whether the SPI communication can be made more robust in firmware — for example, adding CRC checking and retries — but that's a mitigation, not a fix. The root cause needs to be addressed in the hardware.

**Possible follow-ups:**
- How would you determine whether the coupling is common-mode or differential-mode?
- What specific measurements would you take to confirm that a proposed fix actually resolves the issue rather than just reducing the error rate below your detection threshold?

---

## Q3: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This is a compatibility issue that likely stems from how the device negotiates or draws power from the charger. I'd start by characterizing the two chargers — the one that works and the one that doesn't — to understand what's different about them.

The first thing I'd measure is the electrical behavior of both chargers under load. Key parameters include: output voltage at no load and under load, voltage ripple, current capability, and how the charger behaves during inrush. Many USB chargers have different implementations of the USB Battery Charging specification — some advertise their current capability via resistor dividers on the D+/D− lines, others use proprietary protocols. If the device's charging circuit is interpreting the advertisement incorrectly, it might draw more current than the charger can supply, causing the charger to fold back or the device to draw excessive current.

I'd also look at the inrush behavior. Some chargers have a slow-start output that ramps up gradually; others come up quickly. If the device's charging circuit has a large input capacitance, the inrush current when connected to a fast-rising charger could be excessive. The charger that ships with the device might have a current-limiting feature that the third-party charger lacks.

Another angle is the ground and shield connection. Some USB chargers have a different ground reference or leakage path that could cause current to flow through unintended paths. I'd measure the current in both the VBus and ground lines separately to see if the excess current is actually going into the device or if it's a measurement artifact.

I'd also check the device's own charging profile. Does the device implement USB enumeration or battery-charging detection? If the device assumes it's connected to a dedicated charging port and draws full current, but the third-party charger is a downstream port that can only supply 500mA, that would explain the problem. The fix might be in firmware — implementing proper charger detection — or in hardware — adding a current-limiting circuit that caps the input current regardless of what the charger advertises.

Finally, I'd want to understand the failure mode of the "excessive current" — is the charger shutting down, is the device's input protection triggering, or is something overheating? That tells you whether the issue is a compatibility problem or a safety problem.

**Possible follow-ups:**
- How would you test whether the issue is related to inrush current versus steady-state current draw?
- What changes would you consider making to the device's charging circuit to improve compatibility with third-party chargers without compromising safety?

---

## Q4: How would you approach debugging a medical device where the firmware occasionally fails to wake from a low-power sleep mode, and the failure is more frequent when the device has been in sleep for longer periods — the device is supposed to wake on an RTC alarm, but sometimes the RTC interrupt fires and the firmware doesn't resume execution?

**Answer:** This pattern — failure rate increasing with time in sleep — points me toward something that degrades or drifts over time rather than a simple logic error. I'd approach this in layers.

First, I'd verify the RTC is actually generating the interrupt. I'd connect a logic analyzer or oscilloscope to the RTC interrupt output pin and confirm that the interrupt line asserts at the expected time. If the interrupt fires but the firmware doesn't wake, the problem is in the wake path — either the interrupt isn't reaching the CPU, or the CPU wakes but fails to execute the ISR. If the interrupt doesn't fire, the problem is in the RTC itself or its clock source.

The "more frequent with longer sleep" symptom is a strong clue. Possible causes include: the RTC crystal oscillator failing to start or running intermittently after extended periods (crystal startup issues are common, especially with high-ESR crystals or insufficient drive level); the sleep current being higher than expected, causing the battery voltage to sag below the RTC's minimum operating voltage; or a firmware issue where a timer or counter used for the wake comparison is overflowing or being corrupted over time.

I'd also examine the sleep mode configuration. Some MCUs have multiple low-power modes with different wake sources enabled. If the RTC interrupt is configured to wake the device from a deeper sleep mode that it doesn't actually support, or if the interrupt priority is set such that it's masked during the wake sequence, that could cause intermittent failures. I'd review the exact sequence of register writes entering sleep and the wake-up vector.

Another angle is the power supply during sleep. If the device's voltage regulator has a very low quiescent current mode for sleep, it might not be able to source enough current for the RTC or for the wake-up transient. I'd measure the supply voltage during sleep and at the moment of wake to see if there's a droop.

For the longer-sleep correlation specifically, I'd check whether the RTC is running from a separate coin cell or from the main battery. If it's from the main battery, the battery voltage will be slightly lower after extended sleep, which could push the RTC or the wake circuitry into a marginal operating region. I'd also check the crystal — some crystals have a "sleep" phenomenon where they stop oscillating after extended periods at low drive levels, and the startup time increases with the duration of inactivity.

I'd instrument the device to log the RTC interrupt status, the wake source register, and the program counter at wake to see whether the device is actually waking and crashing, or not waking at all.

**Possible follow-ups:**
- How would you test whether the issue is related to the crystal oscillator's startup characteristics?
- What firmware changes would you consider to make the wake sequence more robust, such as using multiple wake sources or adding a wake-up validation routine?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a junior engineer on your team has been debugging an issue for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. The engineer is becoming frustrated, and the project schedule is tight. How would you approach this?

**Answer:** This is a common situation in complex system debugging, and the first thing I'd do is acknowledge that the engineer's frustration is valid — they've been working hard and following a reasonable approach. The issue isn't their effort; it's that they're stuck in a particular investigative loop that isn't yielding new information.

I'd sit down with them and review what they've tested and what they've learned — not to second-guess them, but to help them see the problem from a different angle. The key insight I'd want to surface is that testing components in isolation validates that the components work, but it doesn't validate the interactions between them. System-level failures are often caused by interactions — timing, loading, ground paths, power supply coupling — that don't appear when components are tested alone.

I'd suggest a few specific techniques to break the logjam. First, I'd ask them to characterize the failure more precisely — what exactly happens, when does it happen, and what's different between the passing and failing conditions? Sometimes the answer is in the details they haven't written down. Second, I'd suggest they try to make the failure more frequent or more reproducible by stressing the system — changing the supply voltage, temperature, or clock speed. A failure that's easier to reproduce is easier to debug. Third, I'd suggest they instrument the system at the boundaries between components — what's the actual signal at the interface between the MCU and the peripheral, not just what each component does in isolation?

If they're still stuck, I'd offer to pair with them for a debugging session. Two people looking at the same problem often see different things. I'd also ask them to explain the system architecture to me as if I were new to it — the act of explaining often reveals assumptions or gaps in understanding.

Finally, I'd make sure the engineer knows that being stuck is a normal part of complex debugging, not a personal failure. The goal is to help them develop better debugging strategies, not just to solve this one issue. I'd frame the experience as a learning opportunity and make sure they come away with a clearer process for approaching system-level failures in the future.

**Possible follow-ups:**
- How would you decide when to step in and take over the debugging versus continuing to guide the junior engineer?
- What would you do if the junior engineer's approach is fundamentally flawed — for example, they're not using a systematic method at all?