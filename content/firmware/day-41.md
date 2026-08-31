# firmware — Day 41

## Q1: How would you approach designing a firmware architecture for a device that must support both a hard real-time control loop (e.g., 1 kHz motor control) and a non-real-time subsystem like a wireless stack, where the wireless stack has its own timing requirements and can consume significant CPU time?

**Answer:** The core principle is strict temporal isolation between the hard real-time path and everything else. I would start by defining the control loop's worst-case execution time (WCET) budget and verifying it against the 1 kHz period — typically aiming for the control task to use no more than 30–50% of the CPU so there's headroom for interrupts and other work.

For the architecture itself, I'd put the control loop at the highest priority in the RTOS, or better yet, drive it directly from a hardware timer interrupt if the control algorithm is short enough. The wireless stack would run as a lower-priority task, and I'd use a message queue or shared memory with careful synchronization (mutex or lock-free ring buffer) for any data passing between the two domains.

The critical design decision is how the wireless stack interacts with the control loop. If the wireless stack can block on network operations or perform long flash writes, those must never delay the control task. I'd use a priority-inversion-aware mutex (e.g., priority ceiling or priority inheritance) for shared resources, and I'd ensure the wireless stack's ISRs are short and defer heavy processing to its task context.

I would also consider using Zephyr's preemptive scheduling with the control task at a higher priority than the wireless task, and I'd carefully size the wireless task's stack and the message queue depth to handle bursts without dropping data. For the control loop itself, I'd avoid dynamic memory allocation entirely — all buffers would be statically allocated at build time.

Finally, I'd instrument the system with timing measurements (e.g., toggle a GPIO at the start/end of the control task, use a logic analyzer) to verify jitter stays within spec during worst-case wireless activity, and I'd stress-test with the wireless stack actively transmitting while the control loop runs.

**Possible follow-ups:**
- How would you handle the case where the wireless stack's ISR needs to preempt the control loop?
- What if the control algorithm is too long to fit in a single 1 kHz period — how would you restructure it?

---

## Q2: You're debugging a firmware issue where a device's flash write operations occasionally corrupt data in an unrelated memory region. The corruption is intermittent and only occurs when the device is under heavy load. How would you approach this?

**Answer:** This is a classic symptom of either a memory access violation, a DMA conflict, or a timing issue during flash operations. I'd approach it systematically.

First, I'd try to characterize the corruption precisely: which memory region is affected, what pattern of corruption (single bit, byte, word), and whether it correlates with specific flash addresses or specific code paths. I'd add a memory guard — fill the region around the corrupted area with a known pattern (e.g., 0xAA) and check it periodically to detect exactly when and where the corruption occurs.

Next, I'd look at the flash write path itself. Many MCUs require interrupts to be disabled or the CPU to be stalled during flash programming. If the flash controller shares a bus with DMA, a DMA transfer to another peripheral could conflict. I'd check whether the flash write routine disables interrupts properly, and whether any DMA channels are active during the write.

I'd also examine the linker script and memory map — is the corrupted region adjacent to the flash buffer or stack? A stack overflow or a buffer overrun in a nearby module could spill into the corrupted region. I'd enable the MPU (memory protection unit) if available to catch out-of-bounds accesses, and I'd check for any wild pointers or array indexing errors in code that runs concurrently with the flash write.

Under heavy load, timing becomes tighter — a task might be preempted mid-flash-write, or an ISR might fire during the write and access memory that's temporarily unavailable. I'd review the flash driver for proper critical-section handling and consider whether the write should be moved to a dedicated low-priority task with interrupts managed carefully.

Finally, I'd use the debugger to set a hardware watchpoint on the corrupted address to catch the exact instruction that writes to it. If the corruption is truly intermittent, I'd add logging around the flash write and the suspected concurrent operations to correlate the failure with specific system states.

**Possible follow-ups:**
- How would you distinguish between a stack overflow and a DMA conflict as the root cause?
- What role would the linker script play in your investigation?

---

## Q3: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The fundamental requirement is that invalid data must never reach the display or alarm logic as if it were valid. I'd design a multi-layer validation pipeline.

At the lowest layer, I'd validate the raw data integrity — check CRC or checksum, verify the frame structure, and confirm the data length matches expectations. Any frame that fails these checks is discarded immediately, and I'd increment a protocol error counter.

At the next layer, I'd apply plausibility checks based on the physiological parameter's known range and rate of change. For example, a heart rate of 400 bpm or a temperature that jumps 5°C in one sample is physiologically implausible. I'd define both absolute limits (hard bounds) and rate-of-change limits (derivative bounds) based on the clinical context and the sensor's specifications.

For handling individual bad samples, I'd use a combination of strategies: hold the last valid value for a short period (with a timestamp so the clinician knows it's stale), interpolate between valid samples if the gap is small, or mark the data as "invalid" and display a "signal lost" or "check sensor" message rather than showing a potentially wrong number.

The critical design decision is the escalation policy. A single bad sample might be tolerated with a hold, but repeated failures or a sustained pattern should trigger a degraded-mode alarm — the device continues operating but clearly indicates reduced confidence in the reading. I'd also log all invalid data events with timestamps for post-event analysis.

For the display logic, I'd separate the data acquisition path from the presentation path. The acquisition module outputs a data structure that includes a validity flag, a confidence level, and the raw value. The display module only renders values that pass all validation layers, and it always shows the validity status to the clinician.

Finally, I'd implement a state machine for sensor health: normal → degraded (intermittent errors) → failed (sustained errors). Each state has defined behavior for the display and alarms, and transitions are logged. This gives the clinical user clear, actionable information without ever presenting a false reading.

**Possible follow-ups:**
- How would you handle the trade-off between discarding bad data and delaying the display of valid data?
- What if the sensor returns values that are within range but systematically wrong (e.g., a calibration drift)?

---

## Q4: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** I'd frame this as a design decision that should be driven by the protocol's characteristics and the team's long-term maintenance needs, not by personal preference. I'd start by having both engineers articulate the specific requirements: how many states, how many transitions, how frequently the protocol changes, and who will maintain it.

For a protocol with a small number of states (say, fewer than 10) and relatively stable behavior, a well-structured state machine with explicit switch-case or function-pointer-based transitions is often clearer and easier to debug — you can trace the exact code path for each transition, and breakpoints are straightforward.

For a protocol with many states, complex transition conditions, or frequent additions of new states (e.g., a protocol that evolves across product generations), a table-driven approach — where transitions are defined in a data table with entries like {current_state, event, condition, next_state, action} — can be more maintainable. Adding a new transition becomes a data entry rather than a code change, and the table can be validated programmatically for completeness (e.g., no undefined transitions).

I'd suggest a hybrid approach as a middle ground: use a table for the transition logic (the "what happens next" decisions) and keep the action functions as separate, well-named functions (the "what happens" implementation). This gives the maintainability of the table with the debuggability of explicit functions.

I'd also ask the team to consider testability. A table-driven approach can be unit-tested more exhaustively — you can iterate over all table entries and verify each transition. A state machine can be tested with state coverage tools, but it's often harder to hit every path.

Finally, I'd recommend the team prototype both approaches for a small subset of the protocol and evaluate them against criteria: readability for new team members, ease of adding a new state, debugging experience, and test coverage. The decision should be based on that evaluation, not on which engineer argues more persuasively. I'd also note that consistency matters more than which pattern is chosen — a mixed approach across the codebase is the worst outcome.

**Possible follow-ups:**
- How would you handle the situation where one engineer refuses to accept the team's decision?
- What criteria would you use to evaluate the two prototypes?

---

## Q5: How would you approach designing a power management subsystem in Zephyr RTOS for a battery-powered medical device that must wake periodically to sample a sensor, process the data, and transmit results wirelessly, while ensuring no sensor readings are missed during the transition between sleep and active states?

**Answer:** The key challenge is that the sensor and radio have their own power-up and stabilization times, and the transition between sleep and active states is where data can be lost. I'd design the power management around a well-defined state machine with explicit timing budgets.

First, I'd map out the timing requirements: the sensor's power-up stabilization time, the ADC settling time, the radio's wake-up and connection time, and the processing time. The sleep period must be long enough to justify the wake overhead — if the sensor takes 50 ms to stabilize and the sleep period is only 100 ms, the device spends half its time just stabilizing.

For the wake sequence, I'd use a staged approach. The RTC or a low-power timer wakes the MCU from deep sleep. The MCU then powers up the sensor and immediately enters a low-power wait state (e.g., WFI) while the sensor stabilizes, rather than busy-waiting. Once the sensor is ready, the MCU samples the data, processes it, and then handles the wireless transmission.

The critical design decision is how to handle the sensor's stabilization time without missing readings. I'd use a timer-based wake sequence: the RTC wakes the MCU slightly before the next sample is due, giving enough time for the sensor to stabilize before the actual sampling instant. This "early wake" approach ensures the sample is taken at the correct time, not delayed by the stabilization period.

In Zephyr, I'd use the power management subsystem with PM_STATE_SUSPEND_TO_RAM or a custom low-power state, and I'd configure the RTC as a wake source. I'd also use Zephyr's sensor driver APIs with their built-in power management hooks where available.

For the wireless transmission, I'd decide whether to transmit immediately after each sample or buffer samples and transmit in bursts. Transmitting every sample keeps the radio on longer (higher average power), while buffering allows the radio to be off for longer periods but requires a larger buffer and introduces latency. For a medical monitor, I'd lean toward immediate transmission for critical parameters, with a small buffer to handle transient radio failures.

I'd also implement a "missed sample" counter and a degraded-mode alarm — if the device ever misses a sample due to timing issues, it must log the event and alert the user, because in a medical context, missing data is itself a safety concern.

Finally, I'd measure the actual power consumption in each state and verify the wake timing with a logic analyzer to ensure the device meets its battery life target while never missing a sample.

**Possible follow-ups:**
- How would you handle the case where the wireless transmission takes longer than the sleep period?
- What happens if the sensor's stabilization time varies with temperature or age?