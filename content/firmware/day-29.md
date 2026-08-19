# firmware — Day 29

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The core issue is that a blocking flash operation in any task will stall the scheduler if it runs at a priority equal to or higher than the sensor task, or if it disables interrupts. The first step is to check whether the flash driver being used supports asynchronous or non-blocking operations — many modern flash controllers and drivers (including Zephyr's flash API with `flash_erase` in a thread context) can offload the actual erase to hardware and notify completion via callback or interrupt. If the hardware supports it, I'd use that path so the lower-priority task initiates the erase and then blocks on a semaphore or waits for a callback, allowing the scheduler to run the 1 ms sensor task in the meantime.

If the flash hardware does not support asynchronous erase, the next option is to move the flash operation to a dedicated lower-priority thread and accept that the sensor task will be delayed during the erase — but that's likely unacceptable for a 1 ms deadline. In that case, I'd look at whether the erase can be broken into smaller chunks (some flash parts support sector or sub-sector erases with shorter block times), or whether the data to be erased can be staged in RAM and written incrementally during idle periods. Another approach is to use Zephyr's `flash_erase` with the `CONFIG_FLASH_ASYNC` option if available, or to use a DMA-assisted write path.

I'd also examine the actual timing: a 100 ms block is a long time, so I'd want to measure whether the flash driver is truly blocking for the full erase or whether it's polling a status register in a way that could be converted to interrupt-driven completion. Finally, I'd consider whether the sensor data can be buffered during the erase window — if the sensor task can push samples into a DMA-backed ring buffer and the processing can catch up afterward, that might be acceptable depending on the application's requirements. The key is to never let a non-real-time operation starve a hard real-time task without a deliberate, documented trade-off.

**Possible follow-ups:**
- How would you verify that the sensor task actually meets its 1 ms deadline under worst-case conditions?
- What if the flash erase cannot be made asynchronous and the sensor data cannot be buffered — how would you present the trade-off to the system architect?

---

## Q2: You're reviewing a colleague's firmware code that implements a communication protocol using a single large interrupt service routine that handles both byte-level reception and complete message parsing. The ISR disables interrupts for the entire duration, which can be up to 300 µs for a long message. The system also has a 1 kHz control loop that must meet strict timing. How would you approach this situation?

**Answer:** This is a classic interrupt latency problem. A 300 µs ISR with interrupts disabled is almost certainly going to cause jitter or missed deadlines in a 1 kHz control loop, which has a 1 ms period — the ISR is consuming nearly a third of the entire period. The fundamental issue is that the ISR is doing too much work: byte-level reception is inherently interrupt-driven (or better, DMA-driven), but message parsing is a processing task that belongs in a thread context.

I'd restructure this into a two-stage design. The ISR (or DMA) handles only byte reception and places raw bytes into a ring buffer, then signals a lower-priority thread via a semaphore or work queue. The thread performs message framing, validation, and parsing. This keeps the ISR extremely short — just a few microseconds to copy a byte and update the buffer index. If the protocol has strict timing requirements for responses, the thread can be prioritized appropriately, but it should never run inside the ISR.

If the byte rate is high enough that interrupt-per-byte is too costly, I'd move to DMA reception with an idle-line or byte-count interrupt to signal when a complete message has arrived. This eliminates per-byte interrupts entirely. The key principle is to minimize work in interrupt context and move all non-time-critical processing to thread context. I'd also measure the actual interrupt latency and control loop jitter before and after the change to quantify the improvement.

**Possible follow-ups:**
- How would you handle a protocol where the response must be sent within 100 µs of receiving a complete message — would that change your approach?
- What if the MCU doesn't have a DMA controller — how would you adapt the design?

---

## Q3: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** This is fundamentally a data integrity and fail-safe design problem. The first principle is that invalid data must never be silently discarded or blindly displayed — the system needs a defined behavior for every possible failure mode. I'd start by classifying the types of invalid data: CRC failures (corruption during transmission), out-of-range values (physiologically impossible readings), and values that are within range but inconsistent with previous readings (e.g., a sudden jump that violates a known rate-of-change limit).

For CRC failures, the module should retry the read a limited number of times (e.g., 2–3 attempts) with a short delay, since transient bus errors are often recoverable. If retries fail, the module should flag the sensor as unavailable and enter a degraded mode. For out-of-range values, the module should apply plausibility checks against the sensor's specified operating range and the physiological limits of the parameter being measured. For rate-of-change violations, I'd use a hysteresis or rate-limit filter that rejects readings that change faster than physically possible.

The critical part is the system-level response: the module must communicate the invalid data condition to the higher-level application through a defined status interface, not just return a value. The display layer must have explicit rules — for example, showing "---" or "sensor error" rather than a stale or fabricated value. In a medical context, the device should also log the event for later review and potentially trigger an alarm if the sensor remains unavailable. I'd also ensure that the module's behavior is documented in the requirements traceability matrix and that the failure modes are covered by the risk management file (ISO 14971-style analysis), since this is a safety-relevant behavior.

**Possible follow-ups:**
- How would you handle a sensor that returns values that are individually plausible but collectively inconsistent (e.g., heart rate and SpO2 that don't match)?
- What would you do if the sensor returns a valid-looking but incorrect value that passes all your checks?

---

## Q4: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** I'd guide the team by reframing the debate away from personal preference and toward the specific requirements of the system. The right answer depends on the protocol's timing requirements, the CPU load, and the consequences of missing a message. I'd start by asking both engineers to write down the concrete constraints: the message rate, the maximum acceptable latency between message arrival and processing, the worst-case CPU utilization of each approach, and the behavior under error conditions.

For a protocol with a low message rate (e.g., a few messages per second) and no strict latency requirement, polling is often simpler and perfectly adequate — it avoids interrupt nesting issues and makes the code easier to reason about. For a protocol with high message rates or strict latency bounds (e.g., a response must be sent within 100 µs), interrupts or DMA are likely necessary. The key is to quantify the requirements rather than argue abstractly.

I'd also ask them to consider the failure modes: with polling, what happens if the main loop is delayed by a long operation? With interrupts, what happens if the ISR is too long or the interrupt rate is too high? I'd encourage them to prototype both approaches and measure the actual worst-case latency and CPU usage. If the team is still split after the data is gathered, I'd make a decision based on the risk profile: for a medical device, I'd favor the approach that is easier to verify and test, even if it's slightly less efficient, unless the performance requirement forces the other choice. The decision should be documented with the rationale, and the chosen approach should be reviewed against the requirements traceability matrix.

**Possible follow-ups:**
- What if the two engineers have valid points and the requirements genuinely allow either approach — how do you decide?
- How would you ensure the chosen approach is actually verified against the timing requirements during testing?

---

## Q5: You're debugging a firmware crash that only occurs when a MicroPython script running on a constrained MCU performs a large memory allocation (e.g., creating a 10 KB bytearray). The system has 64 KB of RAM total. How would you approach diagnosing whether this is a genuine memory exhaustion issue or a fragmentation problem?

**Answer:** This is a common issue with MicroPython on constrained devices, and the first step is to understand how MicroPython manages memory. MicroPython uses its own heap (typically a portion of the total RAM, configured at build time) with a garbage collector that can compact or move objects depending on the build configuration. A crash during a large allocation could be either genuine exhaustion (the heap doesn't have 10 KB free) or fragmentation (the heap has 10 KB free but not in a contiguous block).

I'd start by instrumenting the system to get visibility into the heap state. MicroPython provides `gc.mem_free()` and `gc.mem_alloc()` which give the total free and allocated bytes, but these don't directly show fragmentation. I'd add logging around the allocation to capture the free memory before and after, and I'd also check the heap size configured in the build — if the MicroPython heap is only, say, 40 KB, then a 10 KB allocation is a quarter of the heap, which is significant. I'd also check whether the allocation is happening in a context where other objects are still referenced (e.g., inside a loop that accumulates data without releasing it).

To distinguish exhaustion from fragmentation, I'd try a few approaches. First, I'd run a test that allocates and frees various sizes to see if the heap becomes fragmented over time. Second, I'd check whether the crash happens on the first large allocation or only after the script has been running for a while — if it's the latter, fragmentation is more likely. Third, I'd look at whether the allocation can be avoided entirely: for a 10 KB bytearray, could the data be processed in smaller chunks, or could it be allocated once at startup and reused? If the allocation is genuinely needed, I'd consider increasing the MicroPython heap size (if the MCU has spare RAM) or moving the memory-intensive operation to a C module that uses static or dynamically allocated memory outside the MicroPython heap.

Finally, I'd check the MicroPython build configuration — some ports support heap compaction or a different allocation strategy that reduces fragmentation. If the issue is fragmentation, I'd also look at the script's allocation patterns: repeated creation and discarding of large objects in a loop is a common cause, and restructuring the script to reuse buffers can often resolve it.

**Possible follow-ups:**
- How would you determine the right size for the MicroPython heap versus the C heap in a mixed C/MicroPython system?
- What are the trade-offs of moving the memory-intensive operation to a C module versus trying to fix the fragmentation in the script?