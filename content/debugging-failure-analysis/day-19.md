# debugging-failure-analysis — Day 19

## Q1: How would you approach a failure investigation where a medical device's firmware and hardware teams disagree on whether an intermittent reset is caused by a firmware bug or a hardware issue — the device resets randomly, sometimes multiple times per day, sometimes not for a week, and the watchdog timer is expiring just before each reset?

**Answer:** The first step is to stop treating this as a hardware-versus-software debate and reframe it as a system-level problem. A watchdog timeout is a symptom, not a root cause — something is preventing the firmware from servicing the watchdog, and that could be a firmware hang, a hardware-induced fault that crashes the CPU, or a power/clock disturbance that corrupts execution.

I'd structure the investigation around three parallel workstreams. First, instrument the system to capture more data: add a crash logger that records the program counter, stack trace, and key register values at the moment of reset, and log the time between resets and any preceding events (sensor activity, wireless transmissions, motor actuation). Second, examine the hardware for conditions that could cause spurious resets or execution corruption — brown-out detector thresholds, supply voltage transients during high-current events, noise on the reset pin, or clock glitches. Third, review the firmware for watchdog-servicing patterns: is the watchdog being serviced in multiple places, could an ISR be blocking the main loop, or is there a code path that legitimately takes longer than the watchdog timeout?

The key discriminator is often the crash context. If the program counter consistently points to the same function or module, that suggests a firmware issue. If the reset happens during specific hardware events (motor starts, wireless transmits, power state changes), that points to a hardware interaction. If the stack trace is corrupted or points to random addresses, that suggests memory corruption or a hardware fault.

I'd also check whether the brown-out detector is actually enabled and properly configured — a common issue is a BOD threshold set too close to the minimum operating voltage, causing resets during transient dips that the oscilloscope might miss if you're only looking at steady-state levels.

**Possible follow-ups:**
- How would you determine whether the watchdog timeout is set appropriately for the worst-case firmware execution path?
- What specific measurements would you take to rule out a power supply transient as the cause?

---

## Q2: How would you approach debugging a medical device where a specific sensor reading is consistently correct at the ADC output, but the value stored in memory and transmitted over the communication interface is occasionally wrong — and the error appears to be a single-bit flip in the data?

**Answer:** This is a classic firmware-hardware interaction problem, and the fact that the ADC output is correct but the stored/transmitted value is wrong narrows the investigation significantly. The corruption is happening somewhere between the ADC reading and the data being written to memory or the transmit buffer.

I'd start by examining the data path in the firmware: how is the ADC value being read, converted, and stored? Is there a type mismatch (e.g., reading a 16-bit value into an 8-bit variable), a sign-extension issue, or an endianness problem? Is the data being copied through a buffer that might be shared with an interrupt service routine? A single-bit flip could be a race condition where an ISR modifies the data between the read and the store.

On the hardware side, I'd look at the bus integrity between the ADC and the microcontroller. If it's SPI or I2C, is there proper clock synchronization? Could there be a marginal timing violation that occasionally causes a bit to be sampled incorrectly? I'd check the signal integrity on the data and clock lines — rise times, ringing, crosstalk from adjacent traces — especially if the error correlates with other activity on the board.

I'd also consider whether the error is actually a bit flip or a data alignment issue. If the error is always in the same bit position, that suggests a specific hardware or software issue with that bit. If the error position varies, it's more likely a timing or synchronization problem.

The most productive approach is to add instrumentation: log the raw ADC value, the converted value, and the stored value at each step, and capture the system state (which peripherals are active, what the interrupt context is) when the error occurs. This will quickly reveal whether the corruption happens at the read, the conversion, or the store stage.

**Possible follow-ups:**
- How would you determine whether the bit flip is caused by a firmware race condition versus a hardware signal integrity issue?
- What would you look for in the schematic and layout to identify potential crosstalk sources on the ADC data lines?

---

## Q3: Walk me through your approach to a failure investigation where a medical device's power supply exhibits a periodic voltage dip on a 3.3V rail — the dip is about 200mV and lasts for roughly 50 microseconds, occurring every 100ms — and the device occasionally resets during these dips, but not consistently.

**Answer:** A 200mV dip on a 3.3V rail every 100ms is a strong clue — the periodicity suggests a specific load that's cycling at that rate, not a random event. I'd start by identifying what's happening on the board at 10Hz: is there a sensor sampling cycle, a wireless beacon, an LED blinking, or a motor PWM update?

The first measurement I'd take is a high-bandwidth scope capture of the 3.3V rail at the point of load (right at the decoupling capacitors of the microcontroller), not at the regulator output. The voltage at the regulator might look clean while the voltage at the load shows the dip, because the trace inductance between them creates a voltage drop during transient current draw. I'd also probe the ground plane — a ground bounce between the load and the regulator can cause the same symptom.

Next, I'd identify the current draw profile of the suspected load. If it's a sensor that's powered on for a short period each cycle, the inrush current could be causing the dip. I'd measure the current draw using a current probe or a sense resistor, and correlate the timing with the voltage dip.

The fact that the device resets only occasionally suggests the dip is marginal — sometimes it crosses the microcontroller's brown-out threshold, sometimes it doesn't. I'd check the BOD threshold and compare it to the minimum voltage during the dip. I'd also check whether the dip is worse under certain conditions — higher temperature, lower battery voltage, or when other loads are active simultaneously.

The fix would depend on the root cause. If it's a load transient, I'd add bulk capacitance at the load, improve the decoupling, or spread the load's current draw over time. If it's a regulator bandwidth issue, I'd adjust the compensation or add a feed-forward capacitor. If it's a ground bounce issue, I'd improve the grounding scheme.

**Possible follow-ups:**
- How would you determine whether the dip is caused by the load's current draw or by the regulator's inability to respond to the transient?
- What specific measurements would you take to distinguish between a trace inductance issue and a regulator bandwidth issue?

---

## Q4: How would you approach a failure investigation where a medical device's firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory being copied is within bounds?

**Answer:** A hard fault during a memory copy with valid addresses and in-bounds access is a puzzle that usually points to something subtler than a simple out-of-bounds error. I'd start by examining the exact fault type — is it a bus fault, a usage fault, or a hard fault? The fault status register will tell you whether it's an alignment issue, an undefined instruction, or a bus error on a specific address.

If the addresses are valid and in-bounds, I'd look at the alignment of the source and destination. ARM Cortex-M processors require aligned accesses for certain operations — if the copy routine is using 32-bit loads and stores, and either address is not 4-byte aligned, that will cause a hard fault. This is a classic issue when copying data that starts at an odd offset in a buffer.

Another possibility is that the memory copy is being interrupted by a higher-priority ISR that modifies the memory being copied, or that the copy routine itself is not re-entrant. If the fault happens only when the copy is interrupted at a specific point, that would explain the intermittent nature.

I'd also check the stack depth — if the hard fault occurs during a deep call chain, the stack might be overflowing into adjacent memory, corrupting the data being copied. The stack trace might point to the copy operation because that's where the corruption manifests, not where it originates.

The most effective debugging approach is to capture the full fault context: the fault status register, the program counter at the time of the fault, the link register, and the values of the source and destination pointers. I'd also add a stack watermark to check for stack overflow, and I'd review the copy routine's implementation — is it using a standard library function, or a custom loop? Custom copy loops are more prone to alignment and optimization issues.

**Possible follow-ups:**
- How would you determine whether the fault is caused by a stack overflow versus an alignment issue?
- What would you look for in the fault status register to narrow down the root cause?

---

## Q5: A cross-functional team is investigating a medical device failure where the device's alarm system occasionally fails to activate — the firmware logs show the alarm was triggered, but the hardware never produced sound or visual output. The firmware team believes the hardware is at fault because the code executed correctly, and the hardware team believes the firmware is at fault because the alarm driver circuit tests fine in isolation. How would you handle this situation and structure the investigation?

**Answer:** This is a classic interface problem — the failure is likely in the interaction between firmware and hardware, not in either side in isolation. The first thing I'd do is establish a shared understanding of the alarm activation path: from the firmware's alarm trigger, through the GPIO configuration, to the driver circuit, and finally to the transducer (buzzer, LED, or both). I'd map out every step and identify where the handoffs occur.

The key question is: what does "the alarm was triggered" mean in the firmware logs? Does it mean the firmware set the GPIO high, or does it mean the firmware called the alarm function? These are different things. I'd want to see the actual GPIO state at the time of the failure — was the pin driven high? If the pin was high, the issue is in the driver circuit. If the pin was low despite the firmware logging the trigger, the issue is in the firmware execution.

I'd also look at the timing. The alarm might be triggered and then immediately cleared by another code path — for example, if the alarm condition is transient and the firmware clears the alarm before the hardware has time to respond. This is a common issue with alarm systems: the firmware sets a flag, but the hardware requires a minimum pulse width to activate, and the flag is cleared too quickly.

Another angle is the GPIO configuration. Is the pin configured as push-pull or open-drain? Is the pull-up or pull-down correct? Is the pin shared with another function that might be reconfigured by a different code path? I'd review the pin mux configuration and check whether any other code modifies the GPIO settings.

To structure the investigation, I'd set up a test that captures the GPIO state, the driver circuit input, and the transducer output simultaneously, synchronized with the firmware logs. This would immediately show where the signal chain breaks. I'd also review the alarm activation code for any conditions that might prevent the GPIO from being set — for example, a mutex that's held by another task, or an interrupt that's disabled during a critical section.

The key is to avoid the blame game and focus on the signal chain as a system. Both teams need to agree on what data would prove or disprove their hypothesis, and then we collect that data together.

**Possible follow-ups:**
- How would you determine whether the issue is a timing problem (alarm cleared too quickly) versus a hardware driver problem?
- What specific instrumentation would you add to the system to capture the failure when it occurs?