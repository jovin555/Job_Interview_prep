# debugging-failure-analysis — Day 35

## Q1: How would you approach a failure investigation where a medical device's analog measurement is accurate at room temperature, but shows a growing offset error as the device warms up during continuous operation — and the offset returns to zero after the device cools down?

**Answer:** This is a classic temperature-dependent failure, and the first step is to characterize the thermal behavior precisely rather than guessing at the cause. I'd start by instrumenting the device with thermocouples at key locations — the sensor itself, the instrumentation amplifier, the ADC reference, and the PCB near the power supply — while logging the measurement error continuously. The goal is to correlate the offset magnitude with specific component temperatures, not just ambient temperature.

The key insight is that an offset that grows with temperature points to a component whose characteristics drift with temperature. The usual suspects in an analog front-end are:

- **The voltage reference** — if it's a bandgap reference with poor temperature coefficient, the ADC's reference voltage drifts, which appears as a gain error rather than an offset. But if the reference is shared between the sensor excitation and the ADC, you can get ratiometric cancellation or, conversely, a systematic error if the sensor excitation and ADC reference drift differently.
- **The instrumentation amplifier's input offset voltage** — this drifts with temperature, and the drift specification (µV/°C) is often the limiting factor. If the amplifier is operating near its common-mode input range limit, the offset drift can be much worse than the datasheet spec.
- **The sensor bridge itself** — if it's a resistive bridge sensor, the bridge's zero offset drifts with temperature unless it has good temperature compensation. A mismatch in the temperature coefficients of the bridge resistors produces a temperature-dependent offset.
- **Thermocouple effects at junctions** — dissimilar metal junctions in the signal path (connectors, solder joints, relay contacts) generate small voltages that scale with temperature gradients across the board.

I'd also check whether the offset correlates with the device's internal temperature rise or with the sensor's temperature specifically. If the offset tracks the sensor temperature, it's likely a sensor or sensor-interface issue. If it tracks the PCB temperature near the amplifier, it's more likely an amplifier or reference issue.

The investigation would proceed by isolating sections of the signal chain. I'd measure the sensor excitation voltage at temperature, measure the amplifier output with the sensor disconnected and replaced by a precision resistor (to separate sensor effects from amplifier effects), and measure the ADC reference voltage at temperature. This divide-and-conquer approach identifies which stage introduces the error.

If the root cause turns out to be a marginal component selection — for example, an amplifier with insufficient offset drift specification for the device's operating temperature range — the fix might be a component change, a software calibration table that compensates for temperature, or a design change to reduce the temperature rise near the sensitive components.

**Possible follow-ups:**
- How would you distinguish between a gain error and an offset error in this scenario, and why does that distinction matter for the investigation?
- What role would the device's calibration procedure play in this investigation — could a calibration issue be mistaken for a temperature-dependent failure?

---

## Q2: How would you approach debugging a medical device where the firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory being copied is within bounds?

**Answer:** This is a frustrating class of bug because the obvious checks all pass. The stack trace pointing to a memory copy operation with valid addresses and in-bounds lengths suggests the fault isn't in the copy logic itself but in something that corrupts the state the copy operation depends on.

My first step would be to capture more information about the fault context. I'd want to know:

- **What is the exact fault type?** A bus fault, usage fault, or hard fault tells you different things. A bus fault on a data access could indicate the memory region isn't actually accessible at that moment — for example, a peripheral register that's been clock-gated or a memory region that's been remapped.
- **What are the actual register values at the time of the fault?** The fault status registers (CFSR, HFSR, BFAR, MMAR on ARM Cortex-M) often point to the specific address that caused the fault. If the faulting address is different from the source and destination of the copy, that's a critical clue.
- **Is the stack pointer valid?** If the stack has been corrupted, the "stack trace" might be misleading — you could be looking at garbage that happens to point to a memory copy function.

The fact that the stack trace consistently points to the same function but the fault is intermittent suggests a timing-dependent or state-dependent issue. I'd look at:

- **Interrupt interactions** — is the memory copy operation being interrupted by an ISR that also accesses the same memory region? A race condition between the main loop and an ISR could corrupt the data mid-copy, or the ISR could modify the memory map (e.g., enabling/disabling a peripheral clock).
- **DMA conflicts** — if a DMA channel is writing to the same memory region being copied, you can get corruption that's timing-dependent.
- **Stack overflow** — if the stack is close to overflowing, the copy operation's local variables or the function call itself could push the stack into an invalid region. The fault would appear at the copy operation because that's where the stack usage peaks.
- **Memory protection unit (MPU) configuration** — if the MPU is enabled and a region boundary is misconfigured, a valid-looking address could be inaccessible.

I'd also question whether the "memory copy" is actually a library function like `memcpy` that's being called from many places. The stack trace might consistently show `memcpy` because that's the common denominator, but the actual caller might vary. I'd want to see the full call stack, not just the faulting function.

For the investigation, I'd add fault logging that captures the fault status registers, the program counter, the link register, and the stack contents at the time of the fault. I'd also add a stack watermark to check for stack overflow, and I'd review the code for any shared memory access between the copy operation and interrupt handlers.

If the fault is truly intermittent and hard to reproduce, I might use a fault injection approach — deliberately corrupting memory or triggering the fault condition in a controlled way to see if the behavior matches — or I'd instrument the code to log the state of relevant variables before each copy operation.

**Possible follow-ups:**
- How would you determine whether the stack trace is reliable, or whether stack corruption is giving you misleading information?
- What specific fault status register values would you look for, and how would they guide your investigation?

---

## Q3: How would you approach a failure investigation where a medical device's wireless communication works reliably in the lab, but in the clinical environment, the device intermittently fails to transmit data — and the failures correlate with times when the hospital's paging system is active?

**Answer:** This is a classic electromagnetic interference (EMI) problem in a real-world environment. The correlation with the hospital's paging system is a strong clue that the device is susceptible to out-of-band interference or that the paging system is emitting signals that desensitize the wireless receiver.

My approach would start with understanding the frequency and characteristics of the interfering signal. Hospital paging systems can operate in various bands — some are in the VHF/UHF range, some use Wi-Fi or proprietary protocols in the 900 MHz or 2.4 GHz bands. I'd want to know:

- **What frequency does the paging system use?** If it's near the device's operating frequency, the issue could be receiver desensitization (the front-end saturates or the automatic gain control gets overwhelmed). If it's far away, the issue could be intermodulation products or broadband noise from the paging transmitter.
- **What is the paging system's modulation and duty cycle?** A high-power paging transmitter that's active periodically could be causing a temporary overload condition.

The investigation would involve several steps:

1. **Characterize the failure in the lab** — I'd try to reproduce the interference using a signal generator to simulate the paging signal. I'd sweep frequency and power level to find the device's susceptibility threshold. This tells me whether the issue is fundamental (the receiver can't reject the interference) or specific to the clinical environment.

2. **Measure the actual interference environment** — I'd use a spectrum analyzer with a near-field probe or a broadband antenna to measure the RF environment in the clinical area where the failures occur. This confirms the paging signal's frequency, power, and timing characteristics.

3. **Check the device's receiver specifications** — I'd review the wireless module's datasheet for selectivity, blocking, and intermodulation specifications. If the paging signal is within the receiver's specified blocking limits, the device should be immune — if it's not, the issue is a design deficiency.

4. **Examine the antenna and front-end design** — If the device uses an external antenna, the cable and connector could be picking up interference. If the antenna is on the PCB, the layout could be coupling interference into the receiver front-end. I'd check for filtering on the RF path and for any non-linear junctions (corroded connectors, marginal solder joints) that could generate intermodulation products.

5. **Consider the device's own emissions** — Sometimes the issue isn't the paging system directly but an interaction between the paging signal and the device's own circuitry. For example, the paging signal could be rectified by a non-linear junction in the device's enclosure or cabling, creating a baseband signal that disrupts the wireless module's operation.

The fix would depend on the root cause. If it's receiver desensitization, options include adding a band-pass filter at the antenna input, improving the receiver's automatic gain control behavior, or selecting a wireless module with better blocking specifications. If it's interference coupling through cabling or the enclosure, the fix might involve shielding, ferrite beads, or improved grounding.

I'd also consider whether the device's firmware can detect and recover from the interference — for example, by retrying transmissions after a delay or by switching to a different channel if the protocol supports it.

**Possible follow-ups:**
- How would you distinguish between receiver desensitization and interference coupling through the device's enclosure or cabling?
- What regulatory testing would apply to this scenario, and how would you use the results to guide the investigation?

---

## Q4: How would you approach a situation where a medical device passes all its design verification tests, but during a limited field trial, a small number of units report a "sensor fault" error that clears when the device is power-cycled — and the error code points to a sensor self-test failure that should be impossible given the sensor's specifications?

**Answer:** This is a situation where the device's behavior contradicts the expected failure modes, which means either the failure mechanism is outside the sensor's specified operating conditions, or the self-test logic is producing a false positive.

My first step would be to gather as much data as possible from the field units. I'd want to know:

- **What were the device's operating conditions at the time of the fault?** Temperature, battery voltage, time since power-on, and any other logged parameters. If the fault correlates with a specific condition — for example, low battery or high temperature — that narrows the investigation.
- **What exactly does the self-test check?** I'd review the firmware to understand what the self-test measures and what threshold triggers the fault. Sometimes the self-test is checking a parameter that's not actually specified in the sensor's datasheet, or the threshold is set too tightly for the sensor's normal variation.
- **What is the sensor's actual behavior at the time of the fault?** If the device logs raw sensor readings, I'd look at the data leading up to the fault. Is the sensor reading out of range, or is the self-test failing for a different reason — for example, a communication error with the sensor?

The fact that the error clears on power-cycle suggests a transient condition rather than a permanent sensor failure. Possible causes include:

- **A marginal power supply condition** — if the sensor's supply voltage dips below its minimum during a transient (e.g., when another peripheral draws current), the sensor might fail its self-test but recover when power is restored.
- **A timing issue in the self-test routine** — if the self-test is performed too soon after power-up or after a mode change, the sensor might not be ready, and the self-test fails even though the sensor is functional.
- **An intermittent communication issue** — if the sensor communicates over I2C or SPI, a glitch on the bus could cause the self-test read to fail. The firmware might interpret a communication failure as a sensor fault.
- **A firmware bug in the self-test logic** — the self-test might be checking the wrong register, using an incorrect expected value, or not handling a valid sensor state correctly.

I'd also question whether the "impossible" failure is truly impossible. The sensor's datasheet specifies performance under certain conditions — if the device operates the sensor outside those conditions (e.g., at a temperature or supply voltage outside the specified range), the sensor's behavior might not match the datasheet.

My investigation would involve:

1. **Reproducing the failure in the lab** — I'd try to trigger the self-test failure by varying operating conditions (temperature, supply voltage, timing) and by injecting bus errors. If I can reproduce it, I can debug it directly.

2. **Reviewing the self-test implementation** — I'd look at the firmware code to understand exactly what the self-test does and what conditions could cause a false failure.

3. **Adding diagnostic logging** — I'd enhance the firmware to log more detail when the self-test fails: the raw sensor readings, the sensor's status registers, the bus state, and the supply voltage. This data from the field would be invaluable.

4. **Examining the returned units** — If units are returned, I'd test the sensor in isolation to confirm it's functional, then test the full device to see if the fault reproduces.

The key principle here is to not assume the sensor is at fault just because the error code says "sensor fault." The error code is a firmware interpretation of a condition — the actual root cause could be anywhere in the system.

**Possible follow-ups:**
- How would you determine whether the self-test threshold is set appropriately, and what data would you use to validate it?
- If you couldn't reproduce the failure in the lab, how would you design a field-data collection strategy to gather more information?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a senior engineer on your team is convinced they know the root cause based on their experience with a similar device, but the evidence doesn't fully support their hypothesis — and they're pushing to implement a fix before the investigation is complete?

**Answer:** This is a common and challenging situation in failure investigation. The senior engineer's experience is valuable, but acting on an unconfirmed hypothesis in a medical device context can be dangerous — a fix that addresses the wrong root cause can create a false sense of security while the actual failure mode continues to put patients at risk.

My approach would be to acknowledge the engineer's expertise while creating a structured process that requires evidence before action. I'd start by having a private conversation to understand their reasoning. Often, the senior engineer has seen a similar pattern before, and their hypothesis is based on legitimate pattern recognition. I'd ask them to walk me through the evidence that supports their theory and the evidence that might contradict it. This isn't about dismissing their input — it's about understanding the full picture.

Then I'd propose a structured approach:

1. **Document the hypothesis and its predictions** — I'd ask the engineer to specify what evidence would confirm their hypothesis and what evidence would refute it. This turns the hypothesis into a testable theory.

2. **Identify the gaps in the current evidence** — I'd review the investigation data with the team and highlight what's missing. If the engineer's hypothesis explains some of the evidence but not all of it, I'd focus on the unexplained data.

3. **Design experiments to test the hypothesis** — I'd propose specific tests that would confirm or refute the theory. This might include fault injection, component testing, or data analysis. The key is that the tests are designed to be conclusive, not just confirmatory.

4. **Agree on a decision point** — I'd propose a timeline: if the tests confirm the hypothesis, we implement the fix; if they don't, we continue the investigation. This gives the engineer a clear path to validate their theory without prematurely committing to a fix.

If the engineer continues to push for an immediate fix, I'd escalate the discussion to the risk level. In a medical device context, implementing an unverified fix has regulatory and patient-safety implications. I'd frame the discussion around the consequences of being wrong: if we implement a fix based on an incorrect hypothesis, we might miss the real root cause, and the device could continue to fail in the field. The cost of a few more days of investigation is small compared to the cost of a failed corrective action.

I'd also make sure the investigation is well-documented. If the engineer's hypothesis is eventually confirmed, the documentation shows that we validated it properly. If it's refuted, the documentation shows why we didn't act on it. This protects both the team and the decision-making process.

The underlying principle is to respect experience while maintaining scientific rigor. Experience generates hypotheses; evidence confirms them. In a medical device context, the evidence bar has to be high because the consequences of being wrong are high.

**Possible follow-ups:**
- How would you handle the situation if the senior engineer's hypothesis is eventually confirmed, but the fix they proposed doesn't fully resolve the issue?
- What if the senior engineer is also the project manager and has authority to implement the fix without your approval — how would you handle that dynamic?