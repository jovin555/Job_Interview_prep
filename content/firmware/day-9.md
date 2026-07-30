# firmware — Day 9

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 2 ms, but a lower-priority task occasionally needs to perform a flash erase operation that can block for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** This is a classic real-time scheduling problem where a long-blocking operation threatens the deadline of a higher-priority task. I would approach this by first analyzing whether the flash erase truly needs to block the entire CPU, or if the hardware supports non-blocking erase operations. Many modern MCUs have flash controllers that can perform erase in the background while the CPU continues executing from RAM. If that's available, I'd move the flash task's critical code and interrupt vectors to RAM, then trigger the erase and let the sensor task continue uninterrupted.

If the hardware doesn't support concurrent flash operations, I'd restructure the architecture. One approach is to use a dedicated lower-priority task that performs the flash erase, but break the erase into smaller chunks if the flash controller allows suspend/resume. Alternatively, I'd move the flash operations to a separate, lower-cost microcontroller that handles non-critical logging or configuration storage, communicating over a simple serial link. This isolates the blocking operation entirely.

Another practical approach is to buffer sensor data during the erase window. If the sensor produces data at 2 ms intervals, a 100 ms erase means buffering up to 50 samples. I'd allocate a pre-allocated circular buffer large enough to cover the worst-case erase duration plus margin, and ensure the sensor task writes to this buffer without blocking. After the erase completes, the lower-priority task processes the buffered data. This requires careful sizing of the buffer and validation that the system can catch up after the erase.

**Possible follow-ups:** How would you determine the minimum buffer size needed? What happens if the flash erase takes longer than expected due to retries or wear-leveling?

---

## Q2: You're debugging a firmware crash where a MicroPython script running on a constrained MCU causes a hard fault when performing a large memory allocation. The system has 64 KB of RAM total. How would you approach diagnosing whether this is a genuine memory exhaustion issue or a fragmentation problem?

**Answer:** I'd start by instrumenting the MicroPython heap to understand its state at the time of failure. MicroPython provides `gc.mem_free()` and `micropython.mem_info()` which can be called from the script or injected via a debug REPL connection. I'd add logging before and after the failing allocation to see the free memory trend. If free memory is near zero before the allocation, it's likely exhaustion. If there's plenty of free memory but the allocation still fails, fragmentation is the culprit.

For fragmentation diagnosis, I'd look at the heap's largest contiguous free block. MicroPython's `gc.dump()` or custom C-level instrumentation can show the free block list. If the largest free block is smaller than the requested allocation despite total free memory being sufficient, that confirms fragmentation. I'd also check whether the allocation is happening from a C interrupt handler or callback — MicroPython's memory allocator is not reentrant, and allocating from an ISR can corrupt the heap, causing seemingly random failures.

If fragmentation is the issue, I'd examine the allocation pattern. Repeated allocations and deallocations of varying sizes, especially in tight loops, are classic causes. I'd look for places where the script creates temporary objects (strings, lists, bytearrays) inside loops without forcing garbage collection. Solutions include pre-allocating buffers at startup, using `bytearray` or `array` modules for fixed-size allocations, or calling `gc.collect()` at strategic points to compact the heap. If the allocation pattern can't be changed, I'd consider moving the large allocation to C code using MicroPython's native module interface, where I can use a statically allocated buffer outside the MicroPython heap entirely.

**Possible follow-ups:** How would you distinguish between a heap corruption caused by an ISR versus normal fragmentation? What tools would you use to profile memory usage over time?

---

## Q3: You're implementing a bootloader for a medical device that must support dual-bank OTA updates with guaranteed rollback if the new firmware fails to validate. How would you design the bootloader's decision logic for selecting which bank to boot, and what validation checks would you perform before booting?

**Answer:** The bootloader's decision logic should be simple, deterministic, and resilient to power loss at any point. I'd structure it as a state machine with three states stored in a dedicated, protected flash region (separate from the application banks): a boot counter, a bank-select flag, and a pending-update flag. On each power-on or reset, the bootloader reads these flags and follows this logic:

1. Check if a pending update exists. If yes, check the validity of the new bank.
2. If the new bank is valid, increment a boot-attempt counter, clear the pending-update flag, and jump to the new bank.
3. If the new bank is invalid, fall back to the old bank and set a rollback flag for logging.
4. If no pending update, boot the bank indicated by the bank-select flag.

For validation, I'd perform multiple checks before considering a bank bootable. First, verify the CRC32 or SHA-256 hash of the entire application image, computed during the OTA download and stored alongside the image. Second, check a magic number at a fixed offset in the vector table area to confirm the flash contains a valid application entry point. Third, verify that the application's version number is greater than or equal to the current version (to prevent downgrades if that's a requirement). Finally, I'd include a watchdog-based health check: after booting the new application, the application must clear a "healthy boot" flag within a timeout period. If the watchdog resets before the flag is cleared, the bootloader increments a failure counter and, after a configurable number of consecutive failures, rolls back to the previous bank.

The boot counter is critical for handling power loss during the first boot of new firmware. If the device loses power immediately after jumping to the new bank, the boot-attempt counter won't be cleared. On the next boot, the bootloader sees the counter hasn't been reset, and after a threshold (e.g., 3 attempts), it automatically rolls back. This prevents the device from being stuck in a boot loop on corrupted firmware.

**Possible follow-ups:** How would you handle the case where the bootloader itself needs to be updated? What security considerations would you add for a medical device that must resist unauthorized firmware modification?

---

## Q4: You're reviewing a colleague's firmware code that uses a watchdog timer that kicks in the main loop. The device occasionally resets during a lengthy calibration routine that takes 3 seconds. The colleague proposes increasing the watchdog timeout to 5 seconds. How would you guide them?

**Answer:** I'd acknowledge that increasing the timeout would technically fix the symptom, but I'd guide them to consider whether this is the right solution for a medical device. A 5-second watchdog timeout means that if the firmware hangs during normal operation, the device could be unresponsive for nearly 5 seconds before recovering. For a medical monitoring device, that could mean missing critical patient data or failing to trigger an alarm in time. The timeout should be set based on the maximum acceptable latency for fault detection, not on the longest operation in the system.

Instead of increasing the timeout, I'd suggest restructuring the calibration routine to allow periodic watchdog kicks. The calibration likely consists of multiple steps — sensor warm-up, settling, data collection, computation — and many of these steps can be broken into smaller chunks. For example, if calibration involves averaging 100 sensor readings, the code could kick the watchdog after every 10 readings. If the calibration is a single blocking loop that can't be easily interrupted, I'd consider moving it to a lower-priority task that yields periodically, or using a hardware timer to generate periodic interrupts that kick the watchdog independently of the calibration code.

If the calibration truly cannot be broken into smaller pieces (e.g., it requires a continuous 3-second sensor settling time with no interruptions), then a better approach is to use a windowed watchdog or a separate supervisory watchdog with a longer timeout specifically for long-running operations. Some MCUs have multiple watchdog timers that can be configured differently. Alternatively, I'd implement a software-based health monitor that runs alongside the hardware watchdog — a task that checks for system responsiveness at a finer granularity while the hardware watchdog provides a safety net for catastrophic failures.

The key principle is that the watchdog timeout should reflect the system's safety requirements, not the convenience of the implementation. If the calibration truly needs 3 seconds, the design should accommodate that without compromising the watchdog's ability to detect faults during normal operation.

**Possible follow-ups:** How would you determine the appropriate watchdog timeout for a medical device? What other mechanisms could you use to detect that the calibration routine itself has hung?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** I'd start by framing this as a design decision that depends on specific system requirements rather than a matter of personal preference. I'd call a meeting with both engineers and walk through a structured decision framework based on the protocol's timing requirements, the system's overall task scheduling, and the consequences of missed data.

First, I'd ask the team to quantify the protocol's requirements: What is the maximum acceptable latency between data arrival and processing? What is the minimum and maximum data rate? Can data be buffered, or must every byte be processed immediately? For a medical device, we also need to consider whether the protocol has any safety-critical timing guarantees.

If the data rate is low and predictable (e.g., a sensor that sends a 10-byte packet every 100 ms), polling in a dedicated task with a 50 ms period is simple, deterministic, and easy to debug. The worst-case latency is bounded by the polling period plus processing time, and there's no risk of interrupt nesting or priority inversion. This is often the right choice for medical devices where predictability and testability are paramount.

If the protocol has bursty traffic or requires sub-millisecond response times (e.g., acknowledging a command within 100 µs), interrupts are likely necessary. In that case, I'd guide the team to design the interrupt handler to be as minimal as possible — typically just copying data to a DMA buffer or a lock-free ring buffer — and defer all protocol parsing and processing to a task. This gives responsiveness without sacrificing predictability.

I'd also suggest a hybrid approach: use interrupts for time-critical events (like detecting the start of a packet or a timeout), but use polling for the bulk of data transfer. For example, an interrupt could wake a task when data is available, and the task then polls the peripheral to read the data at its own pace. This combines the responsiveness of interrupts with the determinism of task-based processing.

To resolve the disagreement, I'd propose that each engineer prototype their approach on the target hardware with realistic traffic patterns. We'd measure worst-case latency, CPU utilization, and interrupt latency impact on other time-critical tasks. The data from these experiments would drive the decision, not opinions. This approach also gives both engineers ownership of the solution and turns the disagreement into a productive engineering exercise.

**Possible follow-ups:** How would you handle the case where the polling approach meets timing requirements but uses 30% CPU, while the interrupt approach uses 5% CPU but adds complexity? What criteria would you use to decide?