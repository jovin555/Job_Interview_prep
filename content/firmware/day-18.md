# firmware — Day 18

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must run every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental issue here is that a blocking flash operation in a lower-priority thread can stall the scheduler, preventing the 1 ms sensor task from running on time. I'd approach this in layers:

First, I'd question whether the flash erase truly needs to block the calling thread. Most modern MCU flash controllers support a "program/erase while executing" mode where the flash peripheral operates independently, and the CPU can continue executing from RAM. The key is to run the flash driver's polling loop from a thread that doesn't interfere with the sensor task, or better, use the flash controller's interrupt or DMA completion signal to wake a thread only when the operation finishes.

If the flash controller on this particular MCU genuinely stalls the bus during erase (which is common on simpler parts), then I'd restructure the architecture. Options include: (a) moving the flash erase to a dedicated low-priority thread and accepting that the sensor task will be delayed during the erase — but then I need to quantify whether the sensor can tolerate a 100 ms gap, which for a 1 ms control loop it almost certainly cannot; (b) breaking the erase into smaller chunks (e.g., page-by-page instead of sector-by-sector) so the blocking period is reduced to a few milliseconds per chunk, and interleaving sensor reads between chunks; or (c) if the sensor data can be buffered, using a DMA-capable sensor interface to capture samples into a large buffer during the erase window, then processing them after.

I'd also look at Zephyr's thread priority configuration. The sensor task should be a cooperative or very high-priority preemptive thread. But no priority setting helps if the lower-priority thread blocks the kernel itself during the erase. The real solution is architectural — either the flash operation must not block the bus, or the sensor data path must tolerate the gap through buffering.

Finally, I'd add a runtime assertion or watchdog-style check that measures the actual worst-case sensor task latency during flash operations, so any regression in timing is caught in testing rather than in the field.

**Possible follow-ups:**
- How would you decide between buffering sensor data versus breaking the erase into smaller chunks?
- What Zephyr kernel configuration options (e.g., `CONFIG_MULTITHREADING`, preemption settings) would you verify are set correctly for this scenario?

---

## Q2: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core requirement is that invalid data must never be presented as valid — the system must fail safe. I'd design the sensor data path with multiple layers of validation and a clear policy for what happens when data is rejected.

At the lowest layer, I'd validate the raw data integrity: check CRC or checksum on every frame, verify the frame length and addressing, and confirm the data was received within the expected time window. Any failure here means the sample is discarded entirely — no partial data is used.

Next, I'd apply plausibility checks at the signal level: is the value within the physiological range for this parameter? Is the rate of change physically possible? For example, a heart rate that jumps from 70 to 200 bpm in one sample interval might be real, but a jump to 400 bpm is certainly an artifact. These checks should be configurable per parameter, with limits defined by clinical input and documented in the requirements.

Then I'd implement a data quality state machine. A single bad sample doesn't necessarily mean the sensor is faulty — it could be a transient artifact. I'd track consecutive failures and the overall error rate over a sliding window. The state machine would transition through states like: normal → suspect (occasional bad samples, still displaying data with a "low confidence" indicator) → invalid (sustained failures, stop displaying the parameter entirely and show a clear "sensor fault" message).

Critically, the display logic must be separate from the data validation logic. The display module should only ever receive validated, quality-assured values. If the validation layer determines data is unreliable, it sends an explicit "invalid" status to the display, which then shows the appropriate alert — never the last known good value presented as current, and never a blank screen that could be misinterpreted.

I'd also ensure that the device's alarm logic uses the same validated data stream. A false alarm is a serious problem in a medical setting, but a missed true alarm is worse. The validation layer should flag "uncertain" data to the alarm logic so it can decide whether to suppress, delay, or escalate based on clinical risk.

Finally, all rejected samples and state transitions should be logged with timestamps for post-event analysis. This is essential for both debugging and for regulatory traceability — if a clinician questions a reading, we need to be able to reconstruct exactly what the device saw and why it displayed what it did.

**Possible follow-ups:**
- How would you decide between displaying "no data" versus "last known good value" when the sensor becomes unreliable?
- How would you handle a sensor that returns plausible but systematically biased values (e.g., a temperature sensor that reads 1°C high)?

---

## Q3: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** This pattern — correct at power-on, then drift and noise after 30 minutes — points strongly to a thermal issue, a reference voltage problem, or a power supply degradation issue. I'd approach it systematically.

First, I'd characterize the failure precisely. I'd log the ADC raw counts, the calculated engineering values, and the device's internal temperature (if there's a temperature sensor) over time. I'd also log the battery voltage and the regulated supply rail. The goal is to correlate the onset of drift with some other measurable parameter — does the drift start when the board reaches a certain temperature? When the battery drops below a certain voltage? When the regulator's switching frequency changes?

Next, I'd examine the ADC reference. If the ADC uses an internal reference, it may have a temperature coefficient that causes drift as the board warms up. If it uses an external reference, I'd check whether that reference is stable over temperature and whether its decoupling is adequate. A marginal reference decoupling capacitor can cause noise to appear as the capacitor's ESR changes with temperature.

I'd also look at the power supply. A switching regulator's output ripple and transient response can degrade as components heat up — especially if an inductor or capacitor is operating near its temperature limits. I'd probe the ADC's VREF pin and the analog supply rail with an oscilloscope while the device is in the drifted state, looking for increased ripple or droop. I'd also check the ground plane — a marginal ground connection can cause noise that appears only when current draw increases due to thermal effects.

On the firmware side, I'd check whether the ADC is configured with adequate sampling time and whether the firmware is doing any averaging or filtering. If the drift is a slow offset shift, a periodic calibration routine (e.g., measuring an internal reference channel or a precision voltage divider) could correct it. If the noise is random, digital filtering might help, but I'd be cautious — filtering can mask a real hardware problem.

I'd also consider the battery itself. As the battery discharges, its internal resistance increases, and the regulator's input voltage may sag under load. If the regulator's dropout margin becomes marginal, the output could become noisy. This would explain why the issue appears after 30 minutes — the battery has discharged enough to affect the regulator.

Finally, I'd review the PCB layout — specifically the analog ground routing and the placement of the ADC's decoupling capacitors relative to the switching regulator. A layout that works at room temperature may become marginal as thermal gradients develop.

**Possible follow-ups:**
- How would you distinguish between a reference voltage drift and a signal chain gain drift?
- What would you look for in the ADC's configuration registers that could contribute to this behavior?

---

## Q4: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** I'd frame this as an engineering trade-off that should be decided based on the specific characteristics of the protocol and the team's long-term maintenance situation, not on personal preference.

First, I'd ask both engineers to map out the protocol's actual complexity. How many states are there? How many events or inputs? How many transitions? Is the protocol mostly linear (e.g., a simple command-response sequence) or does it have many conditional branches, nested states, or parallel sub-protocols? For a protocol with fewer than, say, 10-15 states and mostly straightforward transitions, a hand-coded state machine is often clearer and easier to trace in a debugger. For a protocol with dozens of states and complex transition rules, a table-driven approach can be more maintainable because the logic is data rather than code — you can add a new state or transition by editing a table entry rather than modifying control flow.

Second, I'd consider the team's experience and the codebase context. If the team is already comfortable with table-driven patterns and the codebase uses them elsewhere, consistency matters. If this is the first table-driven implementation in the codebase, the learning curve and review burden are real costs.

Third, I'd think about testability and verification. Both approaches can be tested, but the test strategy differs. A state machine is often easier to unit test by driving it through sequences of events. A table-driven approach can be tested by validating the table itself — checking for unreachable states, conflicting transitions, or missing entries — which can be done with a script or a separate test module. For a medical device, the verification effort is a significant factor.

I'd also raise the question of runtime behavior. A table-driven approach typically uses function pointers or lookup tables, which can be less efficient and harder to trace in a debugger (you see an index, not a named state). A state machine with explicit switch-case or if-else logic is more traceable. For a protocol with hard real-time constraints, this could matter.

Rather than picking one approach outright, I'd suggest a hybrid: use a state machine as the primary structure, but consider a table for specific aspects that are genuinely data-driven — for example, a table of valid event/state combinations for validation, or a table of timeout values per state. This gives the readability of a state machine with some of the maintainability benefits of a table.

Finally, I'd ask the team to do a small proof-of-concept — implement a representative subset of the protocol both ways and compare them on code size, readability, and test coverage. That's a concrete way to move from opinion to evidence.

**Possible follow-ups:**
- How would you handle the situation where one engineer refuses to accept the group's decision?
- What specific criteria would you use to evaluate the two proof-of-concept implementations?

---

## Q5: You're implementing a bootloader for a medical device that must support dual-bank OTA updates with guaranteed rollback if the new firmware fails to validate. How would you design the bootloader's decision logic for selecting which bank to boot, and what validation checks would you perform before booting?

**Answer:** The bootloader's core responsibility is to make a safe, deterministic decision about which bank to run, and to never leave the device in a state where it cannot boot at all. I'd design the decision logic as a simple, auditable sequence.

First, I'd define the bank metadata. Each bank has a header containing: a magic number (to confirm the bank is actually programmed), a firmware version, a CRC or hash of the entire firmware image, and a boot attempt counter. The bootloader maintains a small status record in a dedicated flash region (or in the bank header itself) that tracks the state of the last boot attempt.

The decision logic would be:

1. Read the metadata for both banks.
2. Determine which bank is marked as "current" (the one the bootloader last successfully booted).
3. Check if the "current" bank's metadata is valid — magic number matches, CRC of the header is correct.
4. If the current bank is valid, attempt to boot it. Before jumping, increment the boot attempt counter for that bank.
5. If the current bank fails to boot (detected by the application's early startup code reporting a "boot successful" flag back to the bootloader, or by a watchdog timeout), the bootloader decrements the attempt counter. If the counter exceeds a threshold (e.g., 3 attempts), the bootloader marks that bank as failed and switches to the other bank.
6. If the other bank is valid, boot it. If both banks are invalid, enter a recovery mode that accepts a wired or wireless connection for firmware recovery.

For validation before booting, I'd perform: (a) magic number check — confirms the bank contains a valid firmware image, not erased or garbage data; (b) CRC-32 or SHA-256 over the entire firmware image — this is the definitive integrity check; (c) version check — the bootloader should never boot an older version unless explicitly configured to do so, to prevent accidental downgrades; and (d) a "compatibility" check — the firmware image should declare the minimum bootloader version it requires, since a new application might depend on bootloader features.

The critical design principle is that the bootloader itself must be simple and robust. It should not rely on complex peripherals or a full RTOS. It should be written to minimize the chance of its own corruption, and ideally it should run from a protected flash region that the application cannot overwrite.

For the rollback mechanism, I'd use a "boot successful" handshake. After the bootloader jumps to the application, the application has a short window (e.g., 5 seconds) to perform its own self-checks and then write a "boot successful" flag to the status record. If the application crashes or hangs before writing this flag, the watchdog resets the device, and the bootloader sees that the boot attempt counter was not cleared — it then knows the boot failed and can roll back.

One subtlety: the boot attempt counter must be stored in a way that survives resets. This means writing to flash on every boot attempt, which has wear implications. I'd design the counter to be small (a few bits) and use a wear-leveling scheme if the device will undergo many update cycles.

**Possible follow-ups:**
- How would you handle the case where the application firmware is valid but fails at runtime after several minutes — should the bootloader roll back based on a longer timeout?
- How would you protect the bootloader itself from being corrupted during an OTA update?