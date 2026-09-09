# firmware — Day 50

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The core issue is that a blocking operation in a lower-priority context is starving a higher-priority task. The first principle is that no task should ever block for 100 ms in a way that prevents a 1 kHz deadline from being met. I'd look at several layers of solution:

First, I'd question whether the flash erase truly needs to block the calling task. Most flash controllers support either interrupt-driven completion or a polling loop that can be broken into chunks. If the hardware allows it, I'd move the erase operation into a dedicated low-priority task that uses an asynchronous or interrupt-driven flash driver, so the calling task can yield while the erase proceeds in the background. The high-priority sensor task would then never be blocked by the erase.

Second, if the flash controller genuinely blocks the CPU during erase (which is common with internal flash on many MCUs), I'd need to look at the timing more carefully. A 100 ms blocking erase on internal flash is unusually long — many internal flash erases complete in tens of milliseconds or less. If this is external SPI flash, the erase command itself doesn't block the MCU; only the polling for completion does, and that can be deferred to a lower-priority context.

Third, I'd consider whether the sensor task truly needs to run every 1 ms, or whether it could use a double-buffering scheme where it reads a batch of samples less frequently. If the sensor has an internal FIFO, I could configure it to accumulate samples and interrupt less often, reducing the scheduling pressure.

Finally, I'd look at priority inversion more broadly. If the lower-priority task holds a mutex or other resource that the high-priority task needs, I'd need to ensure priority inheritance is enabled. But the fundamental answer is architectural: don't let a long-blocking operation live in a task that shares CPU time with a hard real-time task. Move it to a context where blocking is acceptable, or make the operation non-blocking.

**Possible follow-ups:**
- What if the flash erase cannot be made asynchronous because the flash controller has no interrupt support? How would you handle that constraint?
- How would you verify, through testing or analysis, that your solution actually meets the 1 ms deadline under worst-case conditions?

---

## Q2: You're debugging a firmware issue where a device's flash write operations occasionally corrupt data in an unrelated memory region. The corruption is intermittent and only occurs when the device is under heavy load. How would you approach this?

**Answer:** This symptom — corruption in an unrelated memory region during flash writes under heavy load — points to a few classic root causes, and I'd approach it systematically rather than guessing.

First, I'd want to determine whether the corruption is in RAM or in flash. If it's RAM corruption, the most likely culprits are: a buffer overflow somewhere that happens to be triggered by timing under load, a stack overflow in a task or ISR, or a DMA descriptor pointing at the wrong location. If it's flash corruption, I'd suspect the flash driver is writing to the wrong address due to an indexing error, or there's a power supply issue where the voltage dips during the high-current flash operation and causes marginal writes.

I'd start by reproducing the issue with a debugger attached and setting a hardware watchpoint on the corrupted memory region. When the watchpoint triggers, I'd examine the call stack and the instruction that caused the write. This immediately tells me whether it's a wild pointer, a DMA issue, or something else.

If the corruption is in flash, I'd examine the flash driver's address calculation logic, particularly around boundary conditions — for example, what happens when a write spans a sector boundary, or when the write address is computed from a pointer that could be misaligned. I'd also check whether the flash controller's status register is being polled correctly, because writing to flash while a previous operation is still in progress can cause undefined behavior.

Under heavy load, I'd also suspect a race condition where two tasks or an ISR and a task are both issuing flash operations without proper mutual exclusion. If the flash driver isn't protected by a mutex or if interrupts aren't disabled during the critical section of the operation, a second write could start while the first is mid-operation, causing the controller to behave unpredictably.

Finally, I'd check the power supply. Flash writes draw more current than normal operation, and if the supply voltage sags under load, it can cause marginal behavior in both the flash and other peripherals. A scope capture of the supply rail during the failure would confirm or rule this out.

**Possible follow-ups:**
- How would you go about adding a hardware watchpoint if the corruption only happens once every several hours of operation?
- What specific checks would you do on the flash driver's mutual exclusion logic?

---

## Q3: You're reviewing a colleague's firmware code that implements a communication protocol using a single large interrupt service routine that handles both byte-level reception and complete message parsing. The ISR disables interrupts for the entire duration, which can be up to 300 µs for a long message. The system also has a 1 kHz control loop that must meet strict timing. How would you approach this situation?

**Answer:** This is a classic architectural problem: the ISR is doing too much work, and the interrupt-disable period is violating the timing budget of the control loop. A 300 µs interrupt-disable window on a system with a 1 kHz control loop means the control loop can miss its deadline by up to 30% of its period — that's almost certainly unacceptable.

The fundamental principle is that ISRs should do the minimum work necessary to service the hardware and defer everything else to thread context. In this case, I'd restructure the design into two layers:

1. **The ISR layer** should only handle byte-level reception — moving each received byte from the UART data register into a DMA buffer or a ring buffer, and clearing the interrupt flag. This should take on the order of microseconds, not hundreds. If the UART supports DMA, even better — the DMA controller can move bytes into memory without CPU intervention, and the ISR only fires when a complete message or a timeout occurs.

2. **The message parsing layer** should run in a normal task or thread context. A task can be triggered by a semaphore or a message queue notification from the ISR when a complete frame is available. Parsing can then take as long as needed without affecting interrupt latency or the control loop timing.

I'd also check whether the colleague is disabling interrupts globally or just managing the UART peripheral's interrupt enable bits. If they're calling something like `__disable_irq()` around the entire ISR, that's a more serious problem — it blocks all other interrupts, including the timer interrupt driving the control loop. The fix is to use the peripheral's own interrupt priority and enable/disable bits rather than globally masking interrupts.

Finally, I'd want to understand why the parsing takes so long. If it's doing something like string operations or waiting for a slow peripheral during parsing, that's another sign the work belongs in thread context. If it's genuinely compute-intensive, it might need to be broken into smaller steps or moved to a lower-priority task that can be preempted.

**Possible follow-ups:**
- How would you handle the case where the protocol requires a response to be sent within a strict time window after receiving a message?
- What would you do if the MCU has limited RAM and you can't afford a large ring buffer for received data?

---

## Q4: You're implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician. How would you approach this?

**Answer:** In a medical monitoring context, the requirement is clear: never display a false reading. This means the firmware must distinguish between "no data available" and "invalid data," and handle both without ever presenting fabricated or stale values as current readings.

I'd start by defining what "invalid" means for each sensor reading. This typically falls into three categories: (1) communication-level failures like CRC mismatches or missing acknowledgments, (2) value-level failures where the data is within protocol bounds but physiologically impossible or implausible (e.g., a heart rate of 500 bpm), and (3) consistency failures where the reading conflicts with other sensors or recent history (e.g., a temperature that jumps 10°C in one sample).

For communication failures, the approach is straightforward: retry with a bounded number of attempts, and if the sensor still doesn't respond, transition to a defined error state. The device should clearly indicate "sensor fault" or "no data" rather than showing the last known value as if it were current. In a multi-parameter monitor, losing one parameter shouldn't take down the whole device — the other parameters should continue displaying with a clear indication that one channel is unavailable.

For value-level validation, I'd implement range checks based on physiological limits, rate-of-change limits, and cross-sensor consistency checks. For example, if the device monitors both maternal heart rate and fetal heart rate, a reading that's identical on both channels for an extended period might indicate a sensor cross-talk issue rather than a true physiological event. These checks should be configurable and well-documented, with the thresholds based on clinical input rather than arbitrary engineering guesses.

The key design principle is that the display layer should only ever show readings that have passed all validation checks. If a reading fails validation, the system should either show the last valid reading with a "stale data" indicator (if the staleness is within acceptable clinical bounds) or show "no data" with an alarm. The decision of which to do should be driven by the clinical risk assessment — for some parameters, showing a slightly stale value with a warning is safer than showing nothing; for others, any stale value is dangerous.

I'd also implement a logging mechanism that records all raw sensor data, validation results, and display decisions. This is critical for post-incident analysis and for regulatory compliance — if there's ever a question about whether the device displayed a false reading, the log provides an audit trail.

**Possible follow-ups:**
- How would you decide between showing a stale value with a warning versus showing "no data" when a sensor reading fails validation?
- How would you handle a sensor that intermittently returns plausible but incorrect values — for example, a value that passes range checks but is actually wrong due to a hardware issue?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** When two senior engineers disagree on an architectural approach, my role isn't to pick a winner but to facilitate a decision based on the specific requirements of the project. Both state machines and table-driven approaches are valid; the right choice depends on the nature of the protocol, the team's experience, and the long-term maintenance context.

First, I'd ask both engineers to articulate their concerns in terms of concrete project requirements rather than general preferences. What specific aspects of this protocol make one approach better than the other? For example: How many states and transitions are there? How likely is the protocol to change in the future? Who will be maintaining this code — the original authors or a broader team? What are the safety and certification requirements?

For a protocol with a small, fixed number of states (say, fewer than 10) and transitions that are unlikely to change, a well-structured state machine is often the better choice. It's straightforward to trace the logic, easy to debug with a state variable watch, and simple to verify against the protocol specification. The key is that it must be implemented cleanly — not as a monolithic switch-case with scattered global state, but as a structured module with clear state transition functions and a single point of entry for each event.

For a protocol with many states, complex transition conditions, or a high likelihood of extension (new message types, new states added over time), a table-driven approach can be more maintainable. The transition table becomes data rather than code, which means adding a new state or transition doesn't require modifying control flow — just adding a row to the table. This can also be easier to verify against the specification, because the table can be reviewed as a matrix of states versus events.

I'd also consider a hybrid approach: use a state machine for the high-level protocol flow but use tables for specific sub-decisions, like message type dispatch or error handling. This is often the pragmatic middle ground.

To make the decision, I'd suggest we prototype the critical portion of the protocol in both approaches — perhaps a 2-3 day spike — and evaluate them against criteria we agree on upfront: readability for a new engineer joining the team, ease of unit testing, memory footprint, and how well each handles the specific error cases in our protocol. The team then evaluates the prototypes against these criteria rather than arguing abstract preferences.

Finally, I'd remind the team that this decision isn't irreversible. If we choose one approach and it proves problematic, we can refactor — especially if we've kept the protocol logic isolated from the rest of the system. The cost of changing approaches later is much lower if we've built clean interfaces around the protocol module.

**Possible follow-ups:**
- What specific criteria would you propose for evaluating the two prototypes?
- How would you handle the situation if, after the spike, the team remains deadlocked because both approaches work equally well?