# firmware — Day 1

## Q1: How would you approach designing firmware for a battery-powered medical sensor device that must run continuously for several days while maintaining accurate data acquisition?

**Answer:** The primary constraints are power efficiency and deterministic timing for sensor sampling. I would start by selecting a microcontroller with multiple low-power sleep modes and a flexible clock tree, then architect the firmware around an event-driven, tickless idle loop or a real-time operating system like Zephyr RTOS that supports power management natively.

The key strategy is to keep the CPU in deep sleep between operations. For periodic sensor reads, I'd use a low-power timer or RTC to wake the system, take a quick sample via DMA (so the CPU doesn't need to stay active during ADC conversion), buffer the data, and return to sleep. For communication (e.g., wireless or logging), I'd batch transmissions at longer intervals rather than streaming continuously, and use interrupt-driven I/O to avoid polling.

I would also pay careful attention to clock speed selection—running at the lowest frequency that meets timing requirements reduces dynamic power. For the sensor interface, I'd verify that the sensor's own power-down mode is used when not sampling, and that pull-up resistors on I2C/SPI lines are sized appropriately to minimize leakage.

**Possible follow-ups:**
- How would you handle the trade-off between sampling rate and battery life if the clinical requirement demands higher frequency data?
- What debugging tools would you use to measure actual current consumption in different firmware states?

---

## Q2: You are debugging a firmware issue where a UART communication link intermittently drops bytes under heavy CPU load. How would you approach this?

**Answer:** I would first confirm whether the problem is at the transmitter or receiver side by using a logic analyzer or oscilloscope to capture the UART waveforms. If the signal looks clean electrically, the issue is likely firmware timing.

The most common cause is that the UART receive interrupt is being delayed or missed because a higher-priority interrupt or a long critical section is blocking it. I would check the interrupt priority assignments—UART receive should typically be at a high priority, and I'd look for any ISRs that disable interrupts globally for too long. Using the debugger, I could set a breakpoint in the UART ISR and measure the latency from the start of a received byte to the ISR entry.

Another possibility is that the UART hardware FIFO (if present) is overflowing because the ISR doesn't empty it fast enough. I would check the FIFO trigger level and consider using DMA for UART reception to offload the CPU entirely. If DMA is available, the data moves to a ring buffer automatically, and the CPU only needs to process it when convenient.

Finally, I'd verify that the baud rate tolerance is adequate—if the system clock changes under load (e.g., due to PLL reconfiguration or clock scaling for power saving), the UART baud rate could drift out of spec.

**Possible follow-ups:**
- How would you distinguish between a hardware (electrical) issue and a firmware timing issue?
- What if the problem only occurs when a specific peripheral is active—how would you isolate the interaction?

---

## Q3: How would you structure firmware for a device that must support over-the-air (OTA) firmware updates in the field, with the requirement that a failed update must not brick the device?

**Answer:** The core approach is a dual-bank or A/B update scheme, where the flash memory is partitioned into two identical slots: one for the running application (active bank) and one for the new firmware (inactive bank). A small, immutable bootloader resides in protected flash and decides which bank to boot from.

The update process would work as follows: the application receives the new firmware image (typically via wireless or USB), validates its integrity using a checksum or cryptographic signature, and writes it to the inactive bank. Once the entire image is written and verified, the application sets a flag in a persistent metadata area (e.g., a dedicated flash page) indicating that the new bank should be attempted on next boot. The system then resets.

The bootloader checks the metadata flag, validates the new image (CRC, signature, version compatibility), and if valid, boots from the new bank. If the new firmware fails to boot (detected by a watchdog timer or a "boot successful" flag that the application must set early in its startup), the bootloader reverts to the previous known-good bank and optionally logs the failure.

I would also include a recovery mechanism: if both banks are corrupted, the bootloader should enter a minimal recovery mode that can accept a fresh firmware image via a simple serial or USB protocol, so the device can always be recovered even without network connectivity.

**Possible follow-ups:**
- How would you handle the case where the new firmware image is larger than the available inactive bank?
- What security considerations would you add if the device is in a regulated medical context?

---

## Q4: You are working with a Zephyr RTOS-based system where two tasks share a sensor data buffer. One task writes data from an interrupt handler, and the other reads it for processing. How would you ensure thread-safe access without excessive overhead?

**Answer:** The key challenge is that the writer is in interrupt context, so we cannot use mutexes (which require blocking). The standard Zephyr solution is to use an interrupt-safe data structure, such as a lock-free ring buffer or Zephyr's built-in k_msgq or k_fifo with ISR-safe APIs.

For a sensor data stream, I would typically use a k_msgq (message queue) because it handles fixed-size messages and provides both ISR-safe send (k_msgq_put from interrupt) and blocking receive (k_msgq_get from the task). The queue is inherently thread-safe for single-producer single-consumer scenarios, and Zephyr's implementation disables interrupts only for the brief period needed to update the queue pointers.

If the data volume is high and I need to avoid copying, I might use a lock-free ring buffer with volatile access and memory barriers. The interrupt handler writes to the head pointer, and the task reads from the tail pointer. I would ensure that the head pointer is only written by the interrupt and the tail pointer only by the task, and use atomic operations or compiler barriers to prevent reordering. Zephyr's sys_sflist or a custom implementation with __ATOMIC_SEQ_CST can work, but I'd benchmark to ensure the overhead is acceptable.

I would also consider using Zephyr's k_work subsystem to defer the processing out of the interrupt entirely: the ISR enqueues a work item, and the work handler runs in a thread context where mutexes are safe. This simplifies the design at the cost of slightly higher latency.

**Possible follow-ups:**
- What happens if the queue is full when the interrupt tries to send—how would you handle data loss gracefully?
- How would you test for race conditions in this scenario?

---

## Q5: A colleague on your team has implemented a firmware feature that works on their development board but fails intermittently on the production hardware. How would you approach this situation as a team member?

**Answer:** First, I would avoid assuming the problem is purely firmware or hardware—intermittent issues often live at the boundary. I'd start by gathering data: ask the colleague to share their test setup, the exact conditions under which it fails, and any debug logs or oscilloscope captures. I'd also check whether the production hardware has any known differences from the dev board (e.g., different revision of a component, different PCB layout, or different power supply decoupling).

Next, I would propose a structured debugging plan. We could instrument the firmware to log key state transitions and sensor readings at the point of failure, using a serial debug output or a circular buffer in RAM that can be dumped after a crash. If the failure is timing-sensitive, we might add GPIO toggles around critical sections and capture them on a logic analyzer alongside the failing signal.

I would also suggest a controlled comparison: run the same firmware on the dev board and the production board simultaneously, triggering the same input stimulus, and compare the behavior. If the production board fails consistently under a specific condition (e.g., temperature, supply voltage, or after a certain runtime), we can narrow the root cause.

As a team, we should approach this collaboratively rather than defensively. I'd offer to pair-debug or review the colleague's code with fresh eyes, and I'd share any similar issues I've encountered in the past (e.g., timing assumptions that broke with different component tolerances). If the issue persists, we might escalate to a formal root-cause analysis (like an 8D process) to ensure we document the learning for the team.

**Possible follow-ups:**
- How would you handle it if your colleague is defensive about their code and resists suggestions?
- What would you do if the issue only reproduces once every few hours, making debugging time-consuming?