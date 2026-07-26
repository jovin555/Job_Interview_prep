# firmware — Day 5

## Q1: You're designing a Zephyr RTOS-based system where multiple sensor threads need to share a pool of fixed-size data buffers. How would you choose between using a memory pool versus memory slabs, and what configuration considerations would you need to account for?

**Answer:** The choice between memory pools and slabs in Zephyr depends on the allocation pattern and predictability requirements. Memory slabs are ideal when all buffers are the same fixed size — they provide deterministic allocation and deallocation with no fragmentation, which is critical in medical devices where allocation latency must be bounded. Memory pools, by contrast, support variable-size allocations from a single pool but can suffer from external fragmentation over time.

For a sensor data system, I would lean toward memory slabs if all sensor readings produce the same size data packet. I'd configure the slab with enough blocks to cover worst-case buffering: typically the maximum number of in-flight sensor readings that could accumulate during peak processing latency, plus margin. I'd also set the slab's alignment to match the DMA or cache-line requirements of the sensor interface.

If different sensors produce different-sized packets, I might use multiple slabs (one per size class) rather than a single pool, to maintain deterministic behavior. I'd also consider using Zephyr's `k_mem_slab_alloc` with a timeout of `K_NO_WAIT` in interrupt context and a finite timeout in thread context, with a fallback strategy (e.g., drop oldest sample) if allocation fails.

**Possible follow-ups:**
- How would you handle the case where a high-priority thread needs a buffer but the slab is empty?
- What debugging tools in Zephyr can help you monitor slab utilization at runtime?

---

## Q2: You're debugging a firmware issue where a MicroPython script running on a constrained MCU causes the system to reset unpredictably when performing string concatenation operations. How would you approach diagnosing whether this is a memory fragmentation issue, a stack overflow, or something else?

**Answer:** I'd start by ruling out the most common causes systematically. First, I'd check whether the MicroPython heap is fragmented by enabling the `gc.mem_free()` and `gc.mem_alloc()` diagnostic functions and logging them before and after the string operations. If free memory is sufficient but allocation still fails, fragmentation is likely — MicroPython's garbage collector can compact the heap, but not if there are references scattered throughout.

Next, I'd examine stack usage. MicroPython's C stack is separate from its heap, and deep call chains (especially with recursive operations or nested function calls in user scripts) can overflow the stack. I'd increase the MicroPython task's stack size in the Zephyr thread configuration as a test, or use Zephyr's stack usage monitoring (`CONFIG_THREAD_STACK_INFO`) to see peak usage.

If neither shows the issue, I'd look at the MicroPython string implementation itself. String concatenation in MicroPython creates a new string object and frees the originals, which can cause heap churn. I'd recommend using `''.join()` with a list of string fragments instead of repeated `+` operations, as this allocates the final buffer once. I'd also check whether the script is running in an interrupt context accidentally — MicroPython isn't safe to run in ISRs, and doing so can cause subtle corruption.

Finally, I'd enable Zephyr's fault handlers and examine the crash dump. A hard fault with an address near the stack pointer suggests stack overflow; a bus fault accessing a freed memory region suggests heap corruption.

**Possible follow-ups:**
- What tools exist in MicroPython to profile memory usage without modifying the script?
- When would you decide to rewrite a performance-critical MicroPython function in C as a native module?

---

## Q3: You're implementing an I2C driver for a medical sensor that must read 12 bytes of data every 10 ms. The sensor sometimes holds the clock line low (clock stretching) for up to 5 ms. How would you configure the I2C peripheral and handle this timing constraint in firmware?

**Answer:** Clock stretching of this duration (5 ms out of a 10 ms period) means the I2C transaction could consume up to half the sampling interval, which creates a real-time constraint. I'd approach this with several considerations:

First, I'd configure the I2C controller's clock stretching timeout to be longer than 5 ms — many MCU I2C peripherals have a hardware timeout that can abort the transaction if SCL is held low too long. I'd set this to at least 10 ms to avoid false timeouts.

Second, I'd use interrupt-driven I2C rather than polling, because polling would block the CPU for the entire 5 ms stretch. With interrupts, the CPU can service other tasks while waiting for the sensor to release the clock. In Zephyr, I'd use the I2C API's asynchronous mode with a completion callback, or use a semaphore that the ISR signals when the transaction completes.

Third, I'd consider the impact on the overall system schedule. If the 10 ms sensor read is the highest priority, I'd ensure the I2C interrupt has sufficient priority to preempt lower-priority work. However, I'd also verify that the total I2C transaction time (including stretching) plus processing time fits within the 10 ms window, with margin. If it doesn't, I might need to increase the sampling interval or use DMA to offload the data transfer.

Finally, I'd add a watchdog-aware timeout: if the I2C transaction doesn't complete within 15 ms (accounting for worst-case stretch plus normal transfer time), I'd abort and retry, logging the event for reliability tracking.

**Possible follow-ups:**
- How would you handle the case where clock stretching causes the I2C transaction to overlap with the next scheduled read?
- What bus-level issues could cause excessive clock stretching, and how would you distinguish them from normal sensor behavior?

---

## Q4: A junior engineer on your team has implemented a low-power mode for a medical monitoring device that enters deep sleep between sensor readings. The device wakes on a timer interrupt, takes a reading, then goes back to sleep. However, the device occasionally misses readings because the sensor itself requires a 50 ms stabilization time after power-up before it produces valid data. The engineer proposes keeping the sensor powered on continuously to avoid the stabilization delay. How would you guide them?

**Answer:** I'd acknowledge that the engineer has identified a real timing conflict, but I'd guide them toward a more nuanced solution than keeping the sensor always on, which would defeat the purpose of deep sleep for power savings.

First, I'd analyze the power budget. If the sensor consumes significantly less power than the main MCU, keeping just the sensor powered while the MCU sleeps might be acceptable. Many sensors have a separate sleep mode that consumes microamps while maintaining internal state, allowing faster wake-up than a full power-on. I'd check the sensor datasheet for a "standby" or "idle" mode with a shorter stabilization time.

Second, I'd consider the wake-up sequence timing. Instead of waking the MCU, taking a reading, and sleeping, I'd restructure the sequence: wake the MCU early enough to power up the sensor and let it stabilize before the reading is needed. For example, if the sensor needs 50 ms to stabilize and the reading interval is 1 second, the MCU could wake 60 ms before the reading time, power the sensor, wait 50 ms, take the reading, then sleep. The extra 10 ms of MCU active time is negligible compared to keeping the sensor on continuously.

Third, I'd look at hardware-level solutions. If the sensor has a "data ready" pin, I could use that as a wake-up source instead of a timer — the sensor could be powered continuously in a low-power mode, and its data-ready interrupt wakes the MCU only when valid data is available.

Finally, I'd emphasize the importance of measuring actual power consumption rather than assuming. The engineer should prototype both approaches (sensor always on vs. sequenced wake-up) and measure current draw to make an informed decision.

**Possible follow-ups:**
- How would you handle the case where the sensor's stabilization time varies with temperature or age?
- What Zephyr power management features would you use to implement the sequenced wake-up approach?

---

## Q5: You're leading a firmware team that is transitioning from a bare-metal approach to using Zephyr RTOS for a new medical device. Two senior engineers disagree: one wants to port the existing bare-metal drivers directly into Zephyr as custom drivers, while the other wants to rewrite them using Zephyr's native driver model. How would you guide the team to a decision?

**Answer:** This is a common tension between time-to-market and long-term maintainability. I'd facilitate a structured decision by evaluating several factors with the team:

First, I'd assess the complexity and quality of the existing drivers. If they are well-tested, documented, and have passed regulatory scrutiny, porting them as custom drivers might be the lower-risk path for the initial release. Zephyr allows out-of-tree drivers that don't follow the native model, so this is technically feasible. The key risk is that custom drivers won't benefit from Zephyr's power management, clock control, or DMA abstractions, which could complicate future features.

Second, I'd evaluate the device's peripheral requirements. If the hardware uses standard interfaces (I2C, SPI, UART) with common peripherals, Zephyr's native drivers are likely mature and well-tested. If the hardware uses an obscure sensor or custom FPGA interface, a custom driver might be unavoidable anyway.

Third, I'd consider the regulatory implications. Medical device software requires traceability and verification. If we rewrite drivers, we need re-verification. If we port existing drivers, we need to verify the integration with Zephyr's scheduler and interrupt handling. Either way, there's verification work — the question is which path has more predictable effort.

My recommendation would typically be a hybrid approach: for standard peripherals (I2C, SPI, UART), use Zephyr's native drivers to gain power management and DMA support. For custom or complex peripherals, create a clean abstraction layer that wraps the existing driver code, then gradually refactor toward the native model in future releases. This gives us a working system sooner while establishing a migration path.

I'd also suggest a proof-of-concept sprint: have each engineer implement their approach for one peripheral, then compare code size, performance, power consumption, and development time. Data beats opinions.

**Possible follow-ups:**
- How would you ensure that the chosen approach doesn't create technical debt that blocks future certification?
- What Zephyr-specific testing infrastructure would you set up to validate driver behavior under the RTOS scheduler?