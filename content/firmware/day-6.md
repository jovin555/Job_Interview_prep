# firmware — Day 6

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase operation that can block for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** This is a classic real-time scheduling problem where a long-blocking operation threatens the deadline of a higher-priority task. I would approach this by first analyzing whether the flash erase truly needs to be synchronous, or if it can be deferred or restructured.

The most robust approach is to decouple the flash operation from the task that initiates it. Instead of having the lower-priority task perform the erase directly, I would implement a flash write queue serviced by a dedicated background thread at a lower priority, or use Zephyr's workqueue mechanism. The sensor task would continue running at its 1 ms interval, writing data into a circular buffer. The flash write task would drain that buffer when the sensor task isn't running, performing the erase as part of a larger write operation.

If the flash erase absolutely cannot be deferred (e.g., it's part of a critical data logging operation that must complete before the buffer overflows), I would consider hardware-level solutions: using a dual-bank flash architecture where one bank can be erased while the other is being read, or using external serial flash with a dedicated SPI bus and DMA so the CPU isn't blocked. In Zephyr, I could also explore using the flash driver's asynchronous API if available, which would allow the erase to proceed in the background while the sensor task continues.

Another option is to split the erase into smaller sectors if the hardware supports it, reducing the maximum blocking time. For example, if the flash has 4 KB sectors that erase in 20 ms each, I could erase one sector per sensor idle period rather than erasing a large block all at once.

**Possible follow-ups:** How would you size the circular buffer to ensure no data is lost during the flash operation? What if the flash controller doesn't support asynchronous operations — how would you handle that in firmware?

---

## Q2: You're debugging a firmware crash where a MicroPython script running on a constrained MCU causes a hard fault when performing a large memory allocation (e.g., creating a 10 KB bytearray). The system has 64 KB of RAM total. How would you approach diagnosing whether this is a genuine memory exhaustion issue or a fragmentation problem?

**Answer:** I'd start by instrumenting the MicroPython heap to understand the allocation landscape. MicroPython exposes `gc.mem_free()` and `gc.mem_alloc()` at the Python level, but for a hard fault I'd likely need to drop to C-level debugging. I'd connect a debugger and inspect the MicroPython heap structure — specifically the `mp_state_ctx.mem` fields to see total heap size, current free bytes, and the largest contiguous free block.

If the largest free block is smaller than 10 KB but total free memory is larger, that's a fragmentation problem. If total free memory is already below 10 KB, it's exhaustion. I'd also check whether the MicroPython heap is statically allocated or dynamically sized — on constrained MCUs it's often a fixed-size array, and the default might be too small.

For fragmentation specifically, I'd look at the allocation pattern. If the script repeatedly allocates and frees objects of varying sizes, the heap can become fragmented over time. I'd use `gc.dump_alloc_table()` or a custom C function to visualize the heap map. Common culprits include string operations that create temporary objects, or using lists/dicts that grow incrementally.

If fragmentation is the issue, I'd consider: (1) increasing the MicroPython heap size if there's unused RAM elsewhere, (2) pre-allocating large buffers at startup before fragmentation occurs, (3) using `micropython.alloc_emergency_exception_buf()` to ensure exception handling doesn't fail, and (4) restructuring the script to use `bytearray` or `array` modules which allocate contiguous blocks, rather than lists of small objects.

If it's genuine exhaustion, I'd profile the script's peak memory usage using `gc.mem_alloc()` at strategic points, and look for memory leaks — objects that are referenced but no longer needed, preventing garbage collection.

**Possible follow-ups:** How would you determine the optimal MicroPython heap size for a given application without wasting RAM? What tools or techniques would you use to profile memory usage over time?

---

## Q3: You're implementing a bootloader for a medical device that must support dual-bank OTA updates with guaranteed rollback. How would you design the bootloader's decision logic for selecting which bank to boot, and what validation checks would you perform before booting?

**Answer:** The bootloader's decision logic should be deterministic and fault-tolerant, following a priority-based decision tree. I'd structure it as follows:

First, the bootloader reads a persistent boot configuration stored in a dedicated flash page or EEPROM. This configuration contains: the active bank identifier, a boot attempt counter, a flag indicating whether the last boot was successful, and CRC/hash values for both firmware images.

The decision logic would be:
1. Check if a new firmware image has been fully received and validated in the inactive bank. If so, and if the current active bank is marked as healthy, prepare to switch banks on the next boot.
2. Read the boot attempt counter. If it exceeds a threshold (e.g., 3 attempts), mark the current bank as failed and fall back to the other bank.
3. Validate the candidate firmware image before booting: compute a CRC-32 or SHA-256 over the entire image, verify it matches the stored hash, check the image header for a valid magic number and version compatibility, and optionally verify a digital signature.
4. If validation passes, increment the boot attempt counter, set a "boot in progress" flag, and jump to the firmware entry point.
5. If validation fails, immediately fall back to the other bank and mark the failed bank as invalid.

The firmware itself, once running successfully, should clear the boot attempt counter and set a "boot successful" flag. This is typically done early in the firmware's initialization, before any complex operations begin. If the firmware crashes before clearing the counter, the bootloader will detect the failed boot on the next reset and roll back.

I'd also implement a watchdog timer that starts before jumping to firmware. If the firmware doesn't kick the watchdog within a reasonable time (indicating it started successfully), the bootloader can detect this and roll back on the next reset.

For safety-critical medical devices, I'd add a "safe mode" fallback: if both banks are corrupted, the bootloader enters a recovery mode that listens for a new firmware image over a dedicated interface (e.g., USB DFU or UART), rather than attempting to boot a corrupted image.

**Possible follow-ups:** How would you handle the case where the firmware successfully boots but has a latent bug that only manifests after hours of operation? How would you design the "boot successful" acknowledgment to be robust against power loss during the acknowledgment write?

---

## Q4: You're reviewing a colleague's firmware code that implements a state machine for a medical device's operational modes (idle, calibration, active monitoring, error). The state machine is implemented as a single switch-case inside a 200-line function, with state transitions scattered across multiple modules via global state variables. How would you approach refactoring this for maintainability and safety?

**Answer:** This is a common anti-pattern in embedded firmware that becomes increasingly problematic as the system grows. I'd approach the refactoring incrementally to avoid introducing regressions, especially given the medical device context where safety is paramount.

First, I'd document the existing state machine thoroughly — creating a state transition diagram that maps every possible transition, the conditions that trigger them, and the actions performed on entry/exit. This documentation becomes the specification for the refactored code and helps identify any implicit states or transitions that aren't obvious from the current implementation.

The refactoring strategy would be:

1. **Encapsulate state data**: Move the global state variable into a dedicated state machine structure, along with any state-specific data (timers, flags, sensor readings). This structure should be opaque to other modules, accessible only through defined interfaces.

2. **Implement a table-driven state machine**: Replace the monolithic switch-case with a state transition table. Each entry defines: current state, event/condition, next state, and action function pointer. This makes transitions explicit and auditable, and eliminates scattered global variable assignments.

3. **Separate entry/exit actions**: For each state, define explicit entry and exit functions. Entry actions run when entering the state (e.g., initializing hardware), and exit actions run when leaving (e.g., shutting down peripherals). This prevents the common bug where cleanup is forgotten on certain transition paths.

4. **Centralize event dispatch**: Create a single `process_event()` function that takes the current state and an event identifier, looks up the transition table, and executes the appropriate actions. This eliminates the scattered state transition logic.

5. **Add assertions and guards**: In the transition table lookup, add assertions that verify: the transition is valid (no undefined transitions), the action function pointer is non-null, and the state machine is in a known state. For medical devices, I'd also add runtime checks that log unexpected events rather than silently ignoring them.

The key safety consideration is that the refactored code must behave identically to the original for all valid inputs. I'd create a test harness that exercises every documented transition and compares the behavior (state sequence, outputs) between old and new implementations. For a medical device, I'd also involve the quality team in reviewing the transition table against the requirements.

**Possible follow-ups:** How would you handle the case where the existing code has implicit transitions that aren't documented? What testing strategy would you use to validate the refactored state machine against the original?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** This is a classic engineering trade-off where both positions have merit, and the right answer depends on the specific system constraints. I'd guide the team through a structured decision-making process rather than imposing a solution.

First, I'd call a meeting with both engineers and ask them to present their arguments with concrete data, not just opinions. I'd want to see:

- **Timing analysis**: What is the worst-case latency requirement for the protocol? What is the maximum acceptable jitter? How long does a single poll cycle take, and what is the worst-case polling interval given other CPU tasks?
- **CPU utilization**: What percentage of CPU time would polling consume at the required rate? Is that acceptable given other real-time tasks? What is the interrupt overhead (context switch time, ISR execution time) per event?
- **Complexity and maintainability**: How many interrupt sources would be needed? Are there priority inversion risks? How would interrupt-driven code be tested and debugged compared to polling?
- **Power consumption**: If the device is battery-powered, polling keeps the CPU active continuously, while interrupts allow sleep between events. What are the power budgets?

I'd then propose a decision framework based on the system's requirements:

- If the protocol has a very tight latency requirement (e.g., sub-microsecond response) and the CPU has dedicated cycles available, polling might be simpler and more deterministic.
- If the protocol is event-driven with long idle periods, interrupts are almost certainly better for power and CPU efficiency.
- If the protocol has moderate timing requirements and the CPU is heavily loaded, a hybrid approach might work: use interrupts to wake the CPU from sleep, but poll in the ISR or a high-priority task to handle the actual data transfer.

I'd also suggest prototyping both approaches on the actual hardware, measuring worst-case latency, CPU utilization, and power consumption. Data from real measurements is far more persuasive than theoretical arguments.

Finally, I'd ensure the decision is documented with the rationale, including the specific metrics that were considered and the trade-offs that were accepted. This prevents the same debate from recurring and provides context for future maintainers.

**Possible follow-ups:** What if the measurements show that polling meets the timing requirements but uses 40% CPU, while interrupts use 5% CPU but add 50 µs of jitter? How would you decide? How would you handle the situation where one engineer continues to advocate for their preferred approach after the decision is made?