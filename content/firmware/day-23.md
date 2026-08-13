# firmware — Day 23

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The first principle is that a blocking flash erase in a lower-priority task should never be allowed to stall a 1 ms hard-real-time task. I'd start by questioning the assumption that the flash erase must block the CPU for 100 ms. Most modern MCU flash controllers support a "program/erase while executing from RAM" mode, or at least allow interrupts to be serviced during the erase operation. So the first step is to check the hardware capabilities — if the flash controller can signal completion via interrupt while code executes from RAM, the erase can be made asynchronous, and the sensor task simply continues running.

If the flash controller genuinely blocks the bus for the entire operation, then I'd look at whether the erase can be deferred or broken into smaller chunks. Some flash parts allow partial-page or sector erases that take less time. If the erase must happen atomically, I'd consider moving the erase to a dedicated lower-priority thread and using a mutex or semaphore to coordinate access to the flash — but critically, the sensor task must never block on that mutex. The sensor task would use a lock-free or ISR-safe mechanism (like a ring buffer) to hand data off, and the flash-writing task would drain that buffer whenever it gets CPU time.

Another approach is to use Zephyr's `flash` API with the `CONFIG_FLASH_ASYNC` option if the driver supports asynchronous operations. This lets the flash operation run in the background, and the sensor task continues uninterrupted. If none of these are possible, I'd have to reconsider the architecture — for example, using a separate MCU or a DMA-capable external flash that doesn't block the main bus.

The key trade-off is between data integrity and real-time guarantees. In a medical device, the 1 ms sensor read is likely safety-critical, so the flash erase must be designed around that constraint, not the other way around.

**Possible follow-ups:**
- How would you verify that the sensor task never misses its 1 ms deadline during a flash erase?
- What if the flash controller doesn't support interrupt-driven completion — how would you structure the code to minimize blocking?

---

## Q2: You're debugging a firmware crash that only occurs when a MicroPython script running on a constrained MCU performs a large memory allocation (e.g., creating a 10 KB bytearray). The system has 64 KB of RAM total. How would you approach diagnosing whether this is a genuine memory exhaustion issue or a fragmentation problem?

**Answer:** I'd start by instrumenting the system to get visibility into the MicroPython heap state. MicroPython provides `gc.mem_free()` and `gc.mem_alloc()` which give a snapshot of the heap, but for a more detailed view I'd use `micropython.mem_info()` which shows the heap layout, including free blocks and their sizes. The key diagnostic is whether the largest contiguous free block is large enough for the 10 KB allocation — if the total free memory is, say, 20 KB but the largest contiguous block is only 6 KB, that's fragmentation.

I'd also check whether the allocation is failing at the MicroPython level (raising `MemoryError`) or causing a hard fault. A `MemoryError` suggests the heap manager detected insufficient contiguous space. A hard fault could indicate something else — like a stack overflow in the C code that MicroPython calls, or a bug in a native module that's corrupting memory.

To distinguish between exhaustion and fragmentation, I'd add a periodic log that records `gc.mem_free()`, the largest free block, and the number of free blocks. If the largest free block is consistently small even when total free memory is high, it's fragmentation. If total free memory is genuinely low, it's exhaustion. I'd also look at whether the script is creating many small objects (like strings in a loop) that fragment the heap over time.

If it's fragmentation, the fix is often to pre-allocate the large buffer once at startup and reuse it, or to restructure the script to allocate large objects early before the heap gets fragmented. If it's exhaustion, I'd need to reduce the script's memory footprint — for example, by streaming data instead of buffering it all at once, or by moving the performance-critical allocation into a C module that uses static memory.

**Possible follow-ups:**
- How would you use `gc.threshold()` to tune when garbage collection runs?
- What are the trade-offs between moving the allocation to a C module versus keeping it in MicroPython?

---

## Q3: You're implementing an I2C driver for a medical sensor that must read 12 bytes of data every 10 ms. The sensor sometimes holds the clock line low (clock stretching) for up to 5 ms. How would you configure the I2C peripheral and handle this timing constraint in firmware?

**Answer:** The first thing I'd check is whether the MCU's I2C peripheral supports hardware clock stretching. Many modern I2C controllers handle this automatically — they wait for the clock line to be released without involving the CPU. If that's the case, the firmware just needs to set a generous timeout on the transaction and let the hardware handle the wait.

If the peripheral doesn't support hardware clock stretching, I'd need to handle it in firmware. The critical question is whether the 5 ms stretch fits within the 10 ms read period. Since the sensor can stretch for up to 5 ms, and the read itself takes some time, the worst-case transaction could be close to the 10 ms budget. I'd need to measure the actual worst-case timing and decide whether there's enough margin.

For the firmware design, I'd use interrupt-driven or DMA-based I2C rather than polling, so the CPU isn't blocked during the stretch. The I2C driver would start the transaction, and when the sensor stretches the clock, the peripheral (or the ISR) waits without consuming CPU cycles. I'd set a watchdog-style timeout on the transaction — if the stretch exceeds, say, 6 ms, the driver aborts and reports an error.

I'd also consider whether the 10 ms read period is a hard real-time requirement. If the sensor read is used for a control loop, a 5 ms stretch could cause jitter. In that case, I might use a double-buffer approach: the I2C DMA writes into one buffer while the previous buffer is being processed. This decouples the sensor read from the processing.

Finally, I'd verify the timing on the actual hardware with a logic analyzer, because clock stretching behavior can vary between sensor revisions and with bus capacitance. The datasheet's 5 ms spec is a worst-case — the actual stretch might be much shorter in practice.

**Possible follow-ups:**
- How would you handle a second sensor on the same bus that can't tolerate the 5 ms delay?
- What happens if the sensor stretches the clock indefinitely — how does your driver recover?

---

## Q4: You're reviewing a colleague's firmware code that uses a watchdog timer that kicks in the main loop. The device occasionally resets during a lengthy calibration routine that takes 3 seconds. The colleague proposes increasing the watchdog timeout to 5 seconds. How would you guide them?

**Answer:** Increasing the watchdog timeout to 5 seconds is treating the symptom, not the cause. The real issue is that the main loop is blocked for 3 seconds during calibration, which means the watchdog can't be kicked — but it also means the system is unresponsive to any other events for 3 seconds. In a medical device, that's a safety concern regardless of the watchdog.

I'd first ask what the calibration routine is actually doing. If it's a long computation, it should be broken into smaller steps that can be interleaved with watchdog kicks and other tasks. If it's waiting on a sensor or external event, the code should use a state machine that returns to the main loop between steps, so the watchdog can be serviced.

If the calibration genuinely must run uninterrupted for 3 seconds — for example, if it's waiting for a hardware signal that takes that long — then I'd look at whether the watchdog can be kicked from an interrupt or a separate low-priority task. Some watchdog implementations allow kicking from an ISR, which would keep the watchdog satisfied while the main loop is blocked. But I'd be cautious here: if the main loop is blocked, kicking the watchdog from an ISR masks the fact that the main loop is stuck. A better approach might be to use a separate "task watchdog" that monitors the main loop's progress, rather than just the hardware watchdog.

Another option is to use a windowed watchdog, which requires the kick to happen within a specific time window — neither too early nor too late. This prevents the "kick in a tight loop" pattern that can mask a stuck main loop.

The key principle is that the watchdog should verify the system is actually making progress, not just that some code path is executing. If the calibration routine is a legitimate long operation, the design should explicitly account for it — for example, by having the calibration routine report progress to a monitoring task that kicks the watchdog.

**Possible follow-ups:**
- How would you implement a "task watchdog" that monitors the main loop's progress separately from the hardware watchdog?
- What are the risks of kicking the watchdog from an ISR?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** I'd start by reframing the question: the choice between polling and interrupts shouldn't be made on principle — it should be driven by the specific requirements of the protocol and the system. I'd ask the team to define the hard constraints first: what's the maximum latency for receiving a message? What's the minimum time between messages? What's the CPU utilization budget? What's the worst-case interrupt latency in the system?

Once we have those numbers, we can evaluate both approaches against them. Polling is indeed simpler and more deterministic — there's no interrupt context to worry about, no reentrancy issues, and the timing is predictable. But it consumes CPU cycles even when there's no data, and if the polling interval is too long, we might miss short-duration events. Interrupts are more responsive and efficient when data arrives sporadically, but they introduce complexity: shared data between ISR and main context, potential priority inversion, and the need to carefully bound interrupt latency.

I'd also ask about the protocol's characteristics. If it's a request-response protocol where the device initiates all communication, polling might be perfectly adequate — the device knows when to expect a response. If the protocol is asynchronous, where messages can arrive at any time, interrupts (or DMA) are likely necessary to avoid missing data.

I'd suggest a structured evaluation: write a small prototype of each approach, measure the actual worst-case latency and CPU usage, and compare against the requirements. This turns a philosophical debate into an engineering decision. I'd also consider a hybrid approach — for example, using interrupts to wake the system from idle, but polling once the system is actively processing a transaction.

Finally, I'd remind the team that the decision isn't permanent. We can start with the simpler approach (polling) and add interrupts later if measurements show they're needed. The key is to document the decision, the constraints, and the measurements so future engineers understand why the choice was made.

**Possible follow-ups:**
- How would you handle the shared data between an ISR and the main loop if you chose the interrupt-driven approach?
- What measurements would you want to see before making the final decision?