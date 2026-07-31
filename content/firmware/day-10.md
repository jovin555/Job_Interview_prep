# firmware — Day 10

## Q1: How would you approach designing a watchdog strategy for a medical device that has a legitimate long-running operation (e.g., a flash erase or calibration routine) that can take several seconds, while still ensuring the watchdog provides meaningful fault detection?

**Answer:** The key principle is that the watchdog should detect a hung system, not punish legitimate long operations. I would first analyze the long operation to understand exactly where the time goes and whether it can be broken into smaller chunks. For flash operations, many controllers allow page-by-page or sector-by-sector erases with interruptible steps, so I'd restructure the code to perform the operation incrementally and kick the watchdog between chunks. For genuinely atomic long operations, I'd use a multi-tier approach: a shorter timeout watchdog for the main loop, and a separate mechanism—such as a task monitor or a secondary longer-timeout watchdog—that validates the long operation is actually progressing. I'd also implement a "progress heartbeat" from the long operation itself, so the watchdog is kicked only when there's evidence of forward progress, not just because the main loop happens to be running. This distinguishes between a device that's busy doing useful work and one that's stuck in an infinite loop. Finally, I'd ensure the watchdog is enabled early in boot, cannot be disabled in normal operation, and has a debug-mode bypass that's clearly gated so it can't accidentally ship enabled.

**Possible follow-ups:**
- How would you handle the case where the long operation is in a third-party library you can't modify?
- What are the trade-offs between using a windowed watchdog versus a standard timeout watchdog in this scenario?

---

## Q2: You're debugging a firmware issue where a device intermittently resets, and you suspect it might be either a stack overflow or a watchdog timeout. The device has a JTAG debugger attached, but the reset happens infrequently and unpredictably. How would you approach isolating the root cause?

**Answer:** I'd start by gathering data rather than guessing. First, I'd check whether the MCU has a reset cause register that indicates what triggered the last reset—this immediately distinguishes between a watchdog reset, a brown-out reset, a software reset, or a hardware reset pin. If it's a watchdog reset, I'd want to know if the watchdog fired because the system was truly hung or because a legitimate operation took too long. I'd instrument the code to record the program counter and stack pointer at the point of the last watchdog kick, along with a rolling log of recent events. For stack overflow detection, I'd use the MCU's stack pointer limit register if available, or fill the stack with a known pattern (e.g., 0xAA) at startup and periodically check how much of the pattern has been overwritten. I'd also enable the compiler's stack protection features if available. Since the issue is intermittent, I'd add a non-volatile "crash log" that captures the reset cause, the last known task/function, and a snapshot of key state variables before the reset. This way, even if I can't catch it live, the device records enough information on the next boot for me to analyze. I'd also consider temporarily adding a longer watchdog timeout or disabling it in a debug build to see if the resets stop—if they do, it's likely a watchdog issue rather than a hardware fault.

**Possible follow-ups:**
- How would you distinguish between a stack overflow in an ISR versus a regular task?
- What information would you include in the crash log to make debugging most effective?

---

## Q3: How would you approach implementing a firmware module that needs to communicate with a sensor over SPI, where the sensor occasionally requires up to 500 µs to prepare a response after receiving a command? The system uses Zephyr RTOS, and the sensor is read at 100 Hz.

**Answer:** The first decision is whether to use polling, interrupt-driven, or DMA-based SPI. At 100 Hz, the read rate itself isn't demanding, but the 500 µs sensor preparation time means the CPU can't just busy-wait without wasting significant processing time. I'd structure this as a two-phase transaction: send the command, then yield the CPU or perform other work while waiting for the sensor to be ready. In Zephyr, I'd use the asynchronous SPI API with a completion callback, or I'd split the transaction into separate write and read operations with a delay or a GPIO-based "data ready" interrupt between them if the sensor provides one. If the sensor has a busy/data-ready pin, I'd use that as an interrupt trigger to avoid fixed delays. If not, I'd use a timed delay that's slightly longer than the worst-case preparation time, but I'd make that delay configurable and based on the datasheet specification. During the wait, the RTOS can schedule other tasks. I'd also consider whether the SPI bus is shared with other devices—if so, I need to ensure the bus isn't held for the entire transaction duration, which could block other peripherals. Using the Zephyr SPI driver with proper chip-select management and transaction splitting would address this. Finally, I'd measure the actual timing on hardware to verify the worst-case preparation time and add margin, since datasheet values can be optimistic.

**Possible follow-ups:**
- How would you handle the case where the sensor's preparation time varies significantly between units?
- What are the trade-offs between using a fixed delay versus a hardware "data ready" signal?

---

## Q4: How would you approach designing a firmware architecture for a device that must support multiple communication interfaces (e.g., USB, UART, and wireless) for configuration and data retrieval, where the same data needs to be accessible through any interface?

**Answer:** I'd design a layered architecture that separates the data management from the transport mechanisms. At the core would be a single data model or service layer that owns the device state, configuration parameters, and data buffers. Each communication interface (USB, UART, wireless) would be implemented as a separate transport module that translates between its protocol and the core service API. This way, the data logic is written once and tested once, and adding a new interface only requires implementing a new transport adapter. For the protocol itself, I'd define a common command/response format that's transport-agnostic—for example, a simple framing layer with a command ID, payload length, and checksum, which can be carried over any physical link. I'd also need to handle concurrency: multiple interfaces could send commands simultaneously, so the core service must be thread-safe, likely using a mutex or message queue to serialize access. For data retrieval, I'd use a subscription or request/response pattern depending on whether the data is event-driven or polled. I'd also consider whether the interfaces should be able to operate simultaneously or if there's a priority scheme (e.g., USB takes precedence over wireless). Finally, I'd ensure that error handling and logging are consistent across all interfaces, so debugging doesn't depend on which transport was used.

**Possible follow-ups:**
- How would you handle the case where two interfaces send conflicting configuration commands at the same time?
- How would you test the core service layer independently of the transport implementations?

---

## Q5: A junior engineer on your team has implemented a firmware module that uses a global flag to signal between an ISR and a main-loop task. The code works in testing, but you're concerned about correctness and maintainability. How would you guide them toward a better design?

**Answer:** I'd start by acknowledging that the current approach works and then walk through the specific risks. A global flag shared between an ISR and main-loop code has several issues: it needs to be declared `volatile` to prevent the compiler from optimizing away reads, it doesn't provide any mechanism for the main loop to know when new data is ready (it must poll), and it doesn't handle the case where multiple events occur before the main loop processes them—a single flag can only represent one pending event. I'd guide the engineer toward using the RTOS primitives that already exist in the system. For example, in Zephyr, a semaphore or a message queue is the idiomatic way to signal from an ISR to a task. The ISR gives a semaphore or pushes data onto a queue, and the task blocks on that primitive, waking only when data is available. This eliminates polling, handles multiple events naturally, and is thread-safe by design. I'd also discuss the importance of keeping ISRs minimal—they should capture data and signal, not perform complex processing. If the system is bare-metal rather than RTOS-based, I'd suggest a ring buffer with proper head/tail index management, where the ISR writes and the main loop reads, with careful attention to atomicity and memory barriers. I'd frame this as a learning opportunity about the trade-offs between simple global variables and proper synchronization primitives, emphasizing that the latter are more robust and easier to reason about.

**Possible follow-ups:**
- What specific problems could arise from using a simple flag if the ISR fires twice before the main loop processes the first event?
- How would you decide between using a semaphore versus a message queue for this signaling?