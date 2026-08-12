# debugging-failure-analysis — Day 22

## Q1: How would you approach a failure investigation where a medical device's analog measurement is accurate when tested with a known-good reference signal, but shows a consistent offset error when connected to the actual patient sensor — and the offset varies between different sensor units?

**Answer:** This is a classic interface-mismatch problem rather than a sensor or ADC problem, since the system performs correctly with a reference signal. The fact that the offset varies between sensor units tells me the issue is in the sensor-to-front-end interaction, not in the measurement chain itself.

My first step would be to characterize the sensor's electrical interface parameters — specifically its output impedance, drive capability, and any internal offset or bias requirements. A bridge-type sensor, for example, might have a different source impedance than the reference source used during calibration, which would interact with the front-end's input bias current or input impedance to create a voltage divider effect. I'd measure the actual DC resistance and output impedance of several sensor units and compare them to the reference source.

Next, I'd examine the front-end's input stage. If there's a non-inverting amplifier configuration, the input bias current flowing through a high source impedance creates an offset voltage. I'd check whether the design includes a bias current return path — a common issue with instrumentation amplifiers is that floating or high-impedance sources don't provide a DC path for bias currents, causing the output to rail or shift. I'd also verify the common-mode voltage range: if the sensor's common-mode output voltage sits near the edge of the amplifier's input range, the offset would appear as a gain-dependent error.

I'd also look at the cable and connector. Different sensor units might have slightly different cable lengths or connector resistances, which would matter if the measurement is ratiometric and the excitation voltage is being dropped across the cable. I'd measure the excitation voltage at the sensor itself, not just at the PCB, to confirm the sensor is actually seeing the expected reference voltage.

Finally, I'd compare the sensor's datasheet specifications against the front-end design. If the sensor has a specified output impedance range and the front-end was designed assuming a lower impedance, that's a design mismatch that needs correction — either by buffering the sensor output, increasing the front-end input impedance, or adjusting the excitation and measurement topology.

**Possible follow-ups:**
- How would you determine whether the offset is a gain error or a DC offset error, and how would that distinction change your investigation?
- What design changes would you consider to make the system more tolerant of sensor-to-sensor variation?

---

## Q2: How would you approach debugging a medical device where the firmware occasionally enters a hard fault handler, and the stack trace consistently points to a memory copy operation — but the source and destination addresses are always valid, and the memory being copied is within bounds?

**Answer:** When the stack trace consistently points to a memory copy operation but the addresses and lengths appear valid, I'd look beyond the copy itself and examine the conditions surrounding it. The hard fault might be a symptom of a corrupted stack or corrupted function parameters, not a problem with the copy logic itself.

First, I'd examine the stack at the point of the fault. If the stack pointer is corrupted or pointing to invalid memory, the fault handler's stack trace would be unreliable — the "memory copy" frame might be a red herring. I'd check whether the stack pointer value is plausible and whether the stack contents show signs of corruption, such as overwritten local variables or return addresses.

Second, I'd look at what's happening just before the copy. If the copy is part of a larger data-processing operation, the source data might be valid in terms of address and length, but the data itself might be malformed — for example, a structure containing a pointer that gets dereferenced during the copy, or a buffer that's valid but contains values that cause the copy implementation to behave unexpectedly.

Third, I'd consider memory alignment. If the copy operation uses word-sized accesses and the source or destination address is misaligned, some architectures generate a hard fault. The addresses might be "valid" in the sense that they point to allocated memory, but if they're not properly aligned for the copy routine's access width, that's a fault condition. I'd check the alignment of both addresses at the time of the fault.

Fourth, I'd examine whether the copy is happening in an interrupt context or a task context. If a lower-priority task is performing the copy and an interrupt fires that modifies the same memory region, the copy could encounter a race condition. I'd look at whether interrupts are properly disabled or whether the memory being copied is protected by a mutex or critical section.

Finally, I'd enable the fault handler to capture additional context — the fault status registers (CFSR, HFSR, MMFAR, BFAR on ARM Cortex-M) would tell me exactly what type of fault occurred: whether it's a bus fault, usage fault, or memory management fault, and the fault address register would point to the exact memory location that triggered the fault. That information would immediately narrow down whether the issue is alignment, a bad pointer dereference, or something else.

**Possible follow-ups:**
- How would you use the fault status registers to distinguish between a bus fault, a usage fault, and a memory management fault?
- What approach would you take to capture the fault context when the fault is intermittent and doesn't reproduce easily?

---

## Q3: How would you approach a failure investigation where a medical device's power supply exhibits a periodic voltage dip on a 3.3V rail — the dip is about 200mV and lasts for roughly 50 microseconds, occurring every 100ms — and the device occasionally resets during these dips, but not consistently?

**Answer:** A periodic dip at a fixed interval is a strong clue — it suggests a periodic load, not a random event. The 100ms period points to something like a sensor sampling cycle, a wireless beacon, an LED blink, or a motor PWM update. I'd start by correlating the dip timing with known system activities.

My first step would be to identify what's happening every 100ms. I'd review the firmware's periodic tasks and check whether any peripheral is enabled or disabled on that schedule. I'd also probe the current draw on the 3.3V rail and on the input side of the regulator to see whether the dip is caused by a load step or by an input voltage sag.

If the dip is load-induced, I'd look at the regulator's transient response. A 200mV dip for 50 microseconds suggests the regulator's bandwidth isn't high enough to respond to a fast load step, and the output capacitance is providing the transient current. I'd check the output capacitor's ESR and ESL — if the capacitor is a high-ESR type or if the PCB trace inductance between the capacitor and the load is high, the voltage dip would be larger than expected. I'd also verify that the capacitor is actually the value specified in the BOM and that it's properly placed close to the load.

If the dip is input-induced, I'd look at the upstream supply. If the 3.3V regulator is powered from a battery or a switching pre-regulator, a periodic load on the upstream supply could cause the input voltage to sag, which would propagate through the regulator. I'd measure the input voltage at the regulator during the dip to see if it's also sagging.

The intermittent resets are interesting — if the dip is consistent, why doesn't the device reset every time? I'd check the reset threshold of the microcontroller and the brown-out detector. If the reset threshold is close to the dip voltage, small variations in temperature, load, or supply voltage could push the rail below the threshold intermittently. I'd also check whether the dip coincides with a specific firmware activity that only happens sometimes — for example, if the 100ms event is a sensor read that occasionally takes longer or draws more current.

I'd also examine the ground path. If the dip is measured between the 3.3V rail and ground at the load, but the regulator's ground reference is at a different potential due to ground bounce, the effective voltage at the microcontroller could be lower than what the oscilloscope shows. I'd probe the ground at the microcontroller and at the regulator to check for a ground differential.

**Possible follow-ups:**
- How would you determine whether the dip is caused by a load step on the 3.3V rail or by an input voltage sag on the regulator's supply?
- What measurements would you take to determine whether the reset is caused by the voltage dip itself or by a firmware watchdog timeout triggered by the disturbance?

---

## Q4: How would you approach a failure investigation where a medical device's wireless communication works reliably in the lab, but in the clinical environment, the device intermittently fails to transmit data — and the failures correlate with times when the hospital's paging system is active?

**Answer:** This is an electromagnetic interference problem, and the correlation with the paging system is a valuable clue. The paging system is likely transmitting at a specific frequency with a specific modulation, and the interference path could be radiated, conducted, or a combination of both.

I'd start by identifying the paging system's frequency and power characteristics. Hospital paging systems often operate in the VHF or UHF bands, and the transmitter power can be significant. I'd determine whether the paging frequency is close to the device's wireless operating frequency or its harmonics, and whether the paging signal could be desensitizing the device's receiver or corrupting the transmitter's output.

Next, I'd characterize the interference path. I'd use a spectrum analyzer with a near-field probe to scan the device's PCB while the paging system is active, looking for induced currents or voltages on the wireless module's antenna trace, the RF front-end, or the digital interface lines. I'd also check whether the interference is coupling into the device through the power supply — if the paging signal is picked up by the AC mains or the device's power cable, it could be conducted into the device and then radiated by internal traces.

I'd also examine the device's antenna design and placement. If the antenna is a chip antenna or a PCB trace antenna, its radiation pattern and impedance matching could make it more susceptible to interference from specific directions. The clinical environment might have the paging transmitter in a location that aligns with the antenna's null or its main lobe, depending on how the device is oriented.

The fact that the device works in the lab but fails in the clinical environment suggests the interference is either stronger in the clinical setting or the device's susceptibility is marginal. I'd measure the actual field strength at the device's location in the clinical environment to understand the interference level, and I'd compare it to the device's specified immunity levels. If the device meets its EMC immunity specifications but still fails, the specifications might not cover the paging system's specific frequency or modulation.

I'd also look at the firmware's handling of communication failures. If the wireless protocol has retry mechanisms, the device might be able to recover from transient interference. But if the retry logic has a flaw — for example, if it doesn't properly reset the radio after a failed transmission — the device could get stuck in a failure state. I'd review the firmware's error handling to see whether it's robust enough to recover from interference events.

Finally, I'd consider mitigation options: adding shielding to the wireless module, improving the antenna's matching and filtering, adding ferrite beads on the power and data lines, or changing the wireless protocol's frequency or channel selection to avoid the paging band.

**Possible follow-ups:**
- How would you determine whether the interference is coupling into the device through the antenna or through the power supply?
- What design changes would you consider to improve the device's immunity to this specific interference source?

---

## Q5: How would you handle a situation where you're leading a failure investigation, and a junior engineer on your team has been debugging an issue for several days without progress — they've been testing components in isolation and everything passes, but the system-level failure persists. The engineer is becoming frustrated, and the project schedule is tight. How would you approach this?

**Answer:** The first thing I'd do is acknowledge the engineer's effort and the difficulty of the problem. They've been working hard, and frustration is a natural response when isolated component testing doesn't reveal the issue. I'd make it clear that the problem is challenging, not that their work is inadequate.

Then I'd shift the approach from component-level testing to system-level analysis. The fact that components pass in isolation but the system fails points to an interaction problem — something that only manifests when components are connected together. I'd guide the engineer to think about the interfaces between components rather than the components themselves.

I'd suggest a structured approach: first, define the exact conditions under which the failure occurs — what's powered, what's communicating, what's the sequence of events leading up to the failure. Then, work backward from the failure to identify the last known-good state. I'd ask questions like: "What's different between the system when it works and when it fails?" and "What are the shared resources — power rails, ground, communication buses, interrupt lines — that could be causing the interaction?"

I'd also suggest using a divide-and-conquer approach at the system level. Instead of testing components in isolation, I'd have the engineer progressively disable or disconnect subsystems to narrow down which combination of active subsystems triggers the failure. For example, if the failure only occurs when the wireless module and the sensor are both active, that points to a shared resource conflict — maybe a power supply that can't handle the combined load, or a communication bus that's being accessed by both.

I'd also encourage the engineer to look at the problem from a different angle. If they've been focused on hardware, I'd suggest reviewing the firmware's initialization sequence and resource management. If they've been focused on firmware, I'd suggest examining the hardware's power sequencing and signal integrity. Sometimes a fresh perspective — even from someone who isn't deeply familiar with the system — can spot something that's been overlooked.

Finally, I'd set up a collaborative debugging session where the engineer presents their findings to the team. This serves two purposes: it gives the engineer a chance to articulate their thinking, which often reveals assumptions or gaps, and it brings fresh eyes to the problem. I'd frame it as a team effort, not a review of the engineer's performance, and I'd make sure the engineer feels supported rather than judged.

**Possible follow-ups:**
- How would you balance giving the engineer ownership of the investigation with the need to make progress on a tight schedule?
- What specific questions would you ask the engineer to help them reframe their approach?