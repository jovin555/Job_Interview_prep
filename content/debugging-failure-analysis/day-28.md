# debugging-failure-analysis — Day 28

## Q1: How would you approach a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent communication error is caused by a marginal timing violation or a firmware race condition — the device occasionally fails to complete a sensor read within the required time window, and the error rate increases as the device warms up?

**Answer:** This is a classic firmware-hardware boundary problem, and the temperature dependence is a strong clue that narrows the investigation. I'd structure this in three phases.

First, establish ground truth with instrumentation. I'd put a logic analyzer or high-bandwidth scope on the communication bus (I2C, SPI, or whatever protocol is involved) and capture the actual waveforms during failures. I'd also instrument the firmware to log precise timestamps of every step in the sensor read sequence — when the transaction starts, when each byte is clocked, when the firmware considers the read complete, and any error flags. The goal is to determine whether the failure is a physical-layer issue (slow edges, marginal setup/hold times, excessive capacitance) or a logical-layer issue (firmware starting a transaction before the sensor is ready, or a race between an interrupt and the communication routine).

Second, characterize the temperature dependence. Since the error rate increases as the device warms up, I'd run controlled thermal cycling while monitoring the bus. If the timing margins degrade with temperature — for example, the sensor's clock low time stretches or the rise time on the data line increases — that points to a hardware marginality. If the firmware timing is the issue, the temperature dependence might come from the sensor's internal oscillator drifting, or from the main MCU's clock source changing behavior as it heats up. I'd also check whether the firmware's timeout values are based on worst-case datasheet timing or on typical values measured at room temperature.

Third, I'd design a discriminating experiment. One approach: deliberately slow down the bus clock and see if the failure rate changes. If slowing the clock eliminates the failures, that suggests a setup/hold margin problem. Another approach: add a small delay in the firmware between asserting chip-select and starting the clock, or between the last clock edge and releasing the bus — if that fixes it, the issue is likely a timing violation that the firmware can work around. I'd also check whether the sensor's datasheet specifies a maximum clock rise time or a minimum idle time between transactions, and verify those against the measured waveforms.

For the cross-team disagreement itself, I'd insist that both teams review the captured waveforms together. The data usually resolves the argument — if the scope shows the clock edges are within spec but the sensor still returns garbage, that's a firmware issue; if the edges are marginal or the sensor's response comes back late, that's a hardware issue. I'd also make sure both teams agree on the acceptance criteria for the fix before implementing anything.

**Possible follow-ups:**
- How would you determine whether the temperature dependence is in the sensor, the MCU, or the PCB traces?
- What specific measurements would you take to distinguish a setup-time violation from a hold-time violation on the bus?

---

## Q2: How would you approach debugging a medical device where the firmware enters a hard fault handler intermittently — roughly once every 6–12 hours — and the stack trace points to a different function each time?

**Answer:** A hard fault with a different stack trace each time is a strong indicator that the root cause is not a logic error in any single function — it's more likely memory corruption, a stack overflow, or a hardware issue that corrupts execution state. I'd approach this systematically.

First, I'd try to determine whether the fault is caused by memory corruption or by an actual invalid instruction/data access. I'd enable the hard fault handler to capture the fault status registers (CFSR, HFSR, BFAR, MMFSR) and the program counter at the time of the fault. If the fault is a bus fault or a memory management fault, the fault address register will tell me which address was accessed — that's a critical clue. If it's a usage fault (invalid instruction, divide by zero, unaligned access), that points to corrupted code or a corrupted function pointer.

Second, I'd look for memory corruption sources. The most common causes in embedded systems are: buffer overflows in arrays or structs, use-after-free or dangling pointers, stack overflow from deep recursion or large local variables, and DMA writes to the wrong address. I'd review the code for any memcpy, sprintf, or array indexing that could write past a buffer, and I'd check the linker map to see what's adjacent to the corrupted region. I'd also check whether the stack pointer is valid at the time of the fault — if the stack has grown into another region, that's a stack overflow.

Third, I'd use the hardware to help. If the MCU has a Memory Protection Unit (MPU), I'd configure it to protect the stack region and any critical data structures, so that an overflow or corruption triggers an immediate fault at the point of corruption rather than hours later. I'd also consider using the MCU's built-in stack canary or fill the stack with a known pattern at startup and periodically check whether it's been overwritten.

Fourth, I'd look for timing or interrupt-related causes. A hard fault that occurs every 6–12 hours could be triggered by a rare interrupt timing combination — for example, an interrupt firing in the middle of a multi-byte operation, or a race between two interrupts accessing the same data. I'd review the interrupt priorities and check whether any shared data is accessed from both the main loop and interrupt context without proper protection.

Finally, I'd consider hardware causes. A marginal power supply, a noisy reset line, or an intermittent clock issue could corrupt the program counter or cause the CPU to execute garbage. I'd check the power rails with a scope over an extended period, and I'd verify that the watchdog timer is configured correctly — if the watchdog fires, it could reset the MCU into a state that looks like a hard fault.

The key is to gather as much diagnostic data as possible from the fault itself, then use that data to narrow the search rather than guessing.

**Possible follow-ups:**
- How would you use the fault status registers to distinguish between a stack overflow and a corrupted function pointer?
- What role would you expect the watchdog timer to play in this investigation, and how would you verify it's not masking the root cause?

---

## Q3: How would you approach a failure investigation where a medical device's battery charging circuit draws excessive current from the wall adapter only when the device is connected to a specific model of USB charger, but charges normally with the charger that ships with the device?

**Answer:** This is a charger compatibility issue, and it's common because USB chargers vary significantly in their electrical characteristics despite being nominally "5V." I'd approach this by characterizing both chargers and the device's charging circuit under controlled conditions.

First, I'd characterize the two chargers on the bench. I'd measure their no-load output voltage, their voltage under various load currents, their output ripple, and their transient response to a step load. Many USB chargers have different cable compensation schemes, different current limits, and different output capacitance. A charger with high output capacitance and a slow transient response can cause the device's input voltage to sag or overshoot when the charging circuit switches between constant-current and constant-voltage modes, or when the device's load changes abruptly.

Second, I'd look at the device's charging circuit topology. If it's a linear charger, excessive current draw could be caused by the input voltage being too high, forcing the charger to dissipate more power, or by the charger's input current limit being triggered. If it's a switching charger, I'd check whether the input current limit is set correctly and whether the charger's input voltage regulation loop (sometimes called "input current limiting" or "VIN regulation") is interacting with the charger's output characteristics. Some chargers reduce their input current when the input voltage drops below a threshold — if the problematic charger has a higher output impedance, the input voltage might be dipping and causing the charger to behave differently.

Third, I'd measure the actual input current and voltage waveforms when the device is connected to each charger. I'd use a current probe and a scope to capture the startup transient, the steady-state charging current, and any switching events. I'd also check whether the device's input protection circuitry (like a load switch or a reverse-polarity protection FET) is behaving differently with the two chargers.

Fourth, I'd check the USB negotiation. If the device uses USB BC1.2 or USB-PD to negotiate charging current, the problematic charger might be advertising a different current capability, causing the device to draw more current than the charger can actually supply. I'd verify what the device requests and what the charger advertises.

Finally, I'd consider whether the issue is a ground loop or common-mode noise problem. Some chargers have significant leakage current or noise between their output ground and earth ground, which can cause issues with the device's measurement circuits or with the charging IC's sense lines.

The fix might be a firmware change (adjusting the input current limit or the negotiation protocol), a hardware change (adding input capacitance or a better input filter), or simply documenting that the device is only qualified with certain chargers. For a medical device, I'd also need to assess whether this is a safety issue — excessive current draw could cause the charger to overheat or the device to be damaged.

**Possible follow-ups:**
- How would you determine whether the excessive current is a steady-state condition or a transient at power-up?
- What safety considerations would you evaluate if the device is drawing more current than the charger is rated to supply?

---

## Q4: How would you approach debugging a medical device where the firmware occasionally fails to wake from a low-power sleep mode, and the failure is more frequent when the device has been in sleep for longer periods — the device is supposed to wake on an RTC alarm, but sometimes the RTC interrupt fires and the firmware doesn't resume execution?

**Answer:** This is a classic low-power wake-up failure, and the correlation with sleep duration is a strong clue. I'd approach this by examining the wake-up path, the power state, and the RTC behavior.

First, I'd verify the wake-up source is actually being asserted. I'd connect a scope or logic analyzer to the RTC interrupt pin and the MCU's wake-up pin, and I'd also monitor the MCU's current consumption. If the RTC interrupt fires but the MCU doesn't wake, the problem is in the MCU's wake-up configuration or the power management controller. If the RTC interrupt doesn't fire at all, the problem is in the RTC or its clock source.

Second, I'd examine the sleep configuration. Many MCUs have multiple low-power modes with different wake-up sources available. If the firmware configures the RTC alarm to wake the device from a deep sleep mode, but the RTC interrupt is only enabled in a lighter sleep mode, the device won't wake. I'd also check whether the firmware disables the RTC interrupt or the RTC clock before entering sleep, or whether a peripheral is left in a state that prevents the wake-up.

Third, the correlation with longer sleep duration suggests a few possibilities. One is that the RTC's clock source — typically a 32.768 kHz crystal — is drifting or stopping after extended operation. I'd check the crystal's startup characteristics and whether the RTC oscillator is running correctly after long periods. Another possibility is that the MCU's internal voltage regulator or power switch degrades over time in sleep mode, causing the wake-up logic to malfunction. I'd also check whether the sleep current is higher than expected, which could indicate that a peripheral is not fully powered down and is interfering with the wake-up path.

Fourth, I'd look at the firmware's wake-up handling. If the RTC interrupt fires but the ISR doesn't execute, it could be that the interrupt priority is set too low and another interrupt is blocking it, or that the firmware disables interrupts during the sleep entry sequence and never re-enables them. I'd review the sleep entry code carefully — a common bug is disabling interrupts, entering sleep, and then the wake-up interrupt fires but is masked because interrupts are still disabled.

Fifth, I'd consider the power supply. In sleep mode, the device's current draw drops dramatically, which can cause the power supply voltage to rise (if there's a load transient) or to become noisy (if the regulator is in a light-load mode). If the MCU's supply voltage is marginal during sleep, the wake-up logic might not function correctly. I'd measure the supply voltage during sleep and during the wake-up transition.

Finally, I'd try to reproduce the failure in a controlled way. Since the failure is more frequent with longer sleep durations, I'd run a test that cycles the device through sleep-wake cycles with varying sleep durations, and I'd log the RTC state, the interrupt flags, and the MCU's power state at each wake-up attempt. This would help me identify whether the failure is in the RTC, the wake-up path, or the firmware's handling.

**Possible follow-ups:**
- How would you verify that the RTC oscillator is still running correctly after extended sleep periods?
- What would you check in the firmware's sleep entry sequence to rule out a race condition between disabling interrupts and entering sleep?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a senior engineer on your team is convinced they know the root cause based on their experience with a similar device, but the evidence doesn't fully support their hypothesis — and they're pushing to implement a fix before the investigation is complete?

**Answer:** This is a common and delicate situation in failure analysis. The senior engineer's experience is valuable, but acting on an unconfirmed hypothesis in a medical device context could be dangerous — a fix that addresses the wrong root cause could leave the actual failure mode in place, or worse, introduce a new one.

My approach would be to acknowledge the engineer's expertise and take their hypothesis seriously, but to insist on evidence before implementing a fix. I'd frame it as: "Your experience with similar devices is exactly why we should test this hypothesis properly — if it's right, we want to be confident, and if it's wrong, we want to know now rather than after a field failure."

First, I'd ask the engineer to articulate the hypothesis clearly and identify what evidence would confirm or refute it. I'd ask: "What specific observation would make you certain this is the root cause? What would make you change your mind?" This helps move from intuition to testable prediction.

Second, I'd review the evidence we have and identify what's missing. If the engineer's hypothesis is plausible but the data doesn't fully support it, I'd design experiments to fill the gaps. For example, if they believe a specific component is marginal, I'd ask for the test data that would confirm it — perhaps a stress test, a thermal analysis, or a measurement of the component's behavior under the exact conditions of the failure.

Third, I'd use the engineering change process as a gate. In a medical device context, any fix needs to go through a formal change process with documented rationale, risk assessment, and verification testing. I'd insist that the proposed fix be documented with the evidence supporting it, and that the verification plan include tests that would specifically validate the root-cause hypothesis. If the fix doesn't pass those tests, we haven't solved the problem.

Fourth, I'd manage the team dynamics. The senior engineer might feel that their experience is being dismissed, so I'd make sure they feel heard and that their input is valued. I'd also make sure the rest of the team understands that we're not rejecting the hypothesis — we're validating it properly. If the engineer continues to push, I'd have a private conversation to understand their concerns — sometimes they have information or experience that hasn't been fully communicated.

Finally, if the pressure to implement a fix becomes intense — perhaps from management or from schedule constraints — I'd hold the line on the process. In a medical device, the cost of a wrong fix is far higher than the cost of a delayed investigation. I'd document the decision to continue the investigation, the rationale, and the risks of acting prematurely, and I'd escalate if necessary to ensure the decision is made at the appropriate level.

**Possible follow-ups:**
- How would you handle the situation if the senior engineer's hypothesis turns out to be correct, but the fix they proposed was incomplete?
- What would you do if management pressures you to implement the fix to meet a regulatory submission deadline?