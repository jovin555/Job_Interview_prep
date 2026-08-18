# embedded-linux-bsp — Day 28

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the system clock is running roughly twice as fast as expected, and the RTC itself keeps correct time when read directly?

**Answer:** This is a classic symptom of a clock tree misconfiguration rather than an RTC hardware fault. The first step is to determine whether the issue is in the kernel's timekeeping or in how the hardware clock is being read. I'd start by checking `dmesg` for clock-related messages and verifying the clock source in use (`/sys/devices/system/clocksource/clocksource0/current_clocksource`). If the system is using a timer derived from a PLL that's configured with the wrong multiplier or divider, the kernel's tick rate will be off even though the RTC itself is accurate.

Next, I'd check the device tree clock bindings for the timer peripheral. A common cause is specifying the wrong clock frequency in the `clocks` property, or the clock driver not being aware of a PLL configuration that the bootloader set up differently than expected. I'd compare the actual hardware register values for the PLL and timer prescalers against what the kernel believes they should be — this can be done by reading the registers via devmem or a debugfs interface if available.

I'd also verify whether the bootloader and kernel agree on the board's clocking scheme. If U-Boot configures a PLL to one frequency but the kernel's clock driver assumes a different reference frequency, the derived timer clock will be wrong. The fix typically involves correcting the device tree clock node or ensuring the bootloader and kernel use consistent clock initialization.

Finally, I'd confirm the issue isn't in userspace — for example, an NTP daemon or a misconfigured `hwclock` script that's applying an incorrect drift correction. But given the symptom of "twice as fast," a clock tree issue is far more likely.

**Possible follow-ups:**
- How would you distinguish between a clock tree issue and a problem with the kernel's `CONFIG_HZ` setting?
- What tools would you use to measure the actual timer tick rate to confirm the diagnosis?

---

## Q2: How would you approach designing a kernel driver for a device that needs to be accessed by both a real-time safety-critical task and a non-real-time monitoring task, where the safety-critical task must never be blocked by the monitoring task?

**Answer:** The fundamental requirement here is that the safety-critical path must have guaranteed, bounded access to the hardware, while the monitoring task can tolerate delays. The cleanest approach is to separate the access paths entirely rather than trying to share a single interface with complex locking.

For the safety-critical task, I'd design the driver to provide a dedicated, lock-free or minimal-locking access path. This typically means using a ring buffer or shared memory region that the safety-critical task reads from directly, with the driver writing data into it from interrupt context or a high-priority kernel thread. The synchronization would use memory barriers and atomic operations — or a seqlock if the data is multi-word — rather than mutexes that could block.

The monitoring task would get a separate interface, such as a character device or sysfs entries, that reads from a copy of the data or from a secondary buffer. If the monitoring task needs to configure the device, that configuration path would use normal locking, but it would only touch registers that aren't in the safety-critical data path.

A key design decision is whether the safety-critical task runs in kernel space or userspace. If it's in userspace with real-time scheduling (SCHED_FIFO), the driver needs to provide an interface that doesn't require any syscalls that could block — for example, using `mmap` to expose the ring buffer directly, with the driver updating a shared head pointer. If it's in kernel space, the driver can expose a direct function call interface.

I'd also consider whether the hardware itself supports this split — for example, if the device has separate data and configuration register banks, or if DMA can write directly to a dedicated memory region. The driver should also handle the case where the monitoring task holds a lock and the safety-critical task needs access — the design should ensure the safety-critical path never takes that lock.

Finally, I'd document the timing guarantees explicitly: worst-case interrupt latency, maximum time to copy data to the ring buffer, and the conditions under which data could be dropped (e.g., if the safety-critical task doesn't consume fast enough).

**Possible follow-ups:**
- How would you handle the case where the monitoring task needs to reconfigure the device in a way that affects the safety-critical data path?
- What happens if the safety-critical task misses its deadline — how would the driver detect and report this?

---

## Q3: How would you approach implementing a kernel driver for a device that needs to perform a hardware-triggered DMA transfer, where the trigger comes from an external sensor's interrupt line, and the data must be processed and made available to userspace within a hard real-time deadline (e.g., 2 ms)?

**Answer:** This requires careful design across the interrupt path, DMA setup, and userspace delivery mechanism. The first consideration is whether the sensor's interrupt line can directly trigger the DMA controller, or whether the CPU must configure the DMA transfer in the interrupt handler. If the DMA controller supports hardware triggering, the ideal design is to have the sensor interrupt start the DMA transfer without CPU involvement — this minimizes latency.

If the CPU must be involved, the interrupt handler needs to be as short as possible: acknowledge the interrupt, configure the DMA channel, and start the transfer. The DMA completion interrupt then handles data processing. Both interrupt handlers should be registered with appropriate flags — `IRQF_NO_THREAD` if the handler must run in hardirq context to meet the deadline, or a threaded handler if the timing allows.

For the 2 ms deadline, I'd analyze the worst-case latency budget: interrupt latency, DMA setup time, transfer time, completion interrupt latency, processing time, and the time to make data available to userspace. If the processing is simple (e.g., a checksum or format conversion), doing it in the completion handler might be acceptable. If it's more complex, a dedicated high-priority kernel thread would be better.

For userspace delivery, the key question is whether the deadline applies to the data being available in kernel space or actually readable by the application. If it's the latter, I'd use a mechanism that avoids unnecessary copying — for example, `mmap` a DMA buffer directly to userspace, with the driver updating a timestamp and sequence number. Alternatively, a `read()` on a character device with the `O_DIRECT` flag or using `splice()` could work, but the syscall overhead and scheduling latency need to be budgeted.

I'd also consider using the PREEMPT_RT patch set if the deadline is tight and the system has other load. The driver should be designed to measure and log actual latencies during testing to verify the worst case is within budget.

**Possible follow-ups:**
- How would you handle the case where the DMA transfer size varies between triggers?
- What if the sensor interrupt rate can exceed the DMA controller's ability to keep up — how would you detect and handle overruns?

---

## Q4: Behavioral — You're the BSP lead for a medical device project, and during a pre-production review, the hardware team reveals that they need to change the main processor's boot mode strap resistors to accommodate a new flash part. The change means the processor will boot from a different interface (e.g., from SPI NOR to eMMC), and the bootloader and kernel configurations are already tuned for the current boot source. The project is six weeks from the start of a clinical trial. How would you handle this situation?

**Answer:** The first thing I'd do is understand the full scope of the change before reacting. I'd ask the hardware team for specifics: why the flash part is changing, whether the new part is a like-for-like replacement on the same interface or a genuinely different interface, and whether the change is mandatory or an option. I'd also want to know if the strap resistor change is already on the production boards or if it's a planned change for the next revision.

Assuming the change is mandatory, I'd assess the actual software impact. If the boot source changes from SPI NOR to eMMC, the bootloader needs to be rebuilt with the appropriate driver and the boot sequence adjusted. The kernel also needs the eMMC driver enabled and the root filesystem location updated. This is a well-understood change, but it carries risk — particularly around boot timing, driver initialization order, and whether the bootloader can reliably access the new flash part.

I'd then work with the team to create a mitigation plan. The key question is whether we can validate the change before the clinical trial. If we have prototype boards with the new strap configuration, we can bring up the new boot path immediately. If not, we need to simulate the change — for example, by configuring the bootloader to boot from eMMC on existing hardware if the interface is available, even if the straps aren't changed.

I'd also push back on the timeline if needed. Six weeks before a clinical trial is tight, and a boot source change touches the most critical part of the system — the ability to boot at all. I'd propose a risk assessment: what's the worst case if the new boot path has issues during the trial? If the device fails to boot, it's a patient safety issue. I'd recommend either extending the timeline to allow for proper validation, or finding a way to keep the current boot source for the trial and defer the change to the next revision.

If the change must proceed, I'd structure the work: update the bootloader, verify the kernel boots from eMMC, test power-loss scenarios, and create a rollback plan. I'd also ensure the manufacturing team understands the strap change is critical — a mis-populated resistor could brick the device.

**Possible follow-ups:**
- How would you handle the situation if the hardware team says the change is already on the production boards and can't be undone?
- What specific tests would you run to validate the new boot path before the clinical trial?

---

## Q5: How would you approach implementing a kernel driver for a device that needs to handle multiple simultaneous I2C sensor reads while maintaining deterministic timing in a medical monitoring application?

**Answer:** The core challenge is that I2C is a shared bus with inherent non-determinism — arbitration, clock stretching, and the fact that transactions are serialized. The first design decision is whether the sensors can be read independently or if they share the bus with other devices. If they're the only devices on the bus, we have more control; if not, we need to account for other traffic.

For deterministic timing, I'd first look at whether the sensors support any form of simultaneous sampling — for example, a "trigger all" command that captures all sensor values at the same instant, followed by sequential reads. This decouples the sampling instant from the bus read time. If the sensors don't support this, the next best approach is to minimize the time between individual reads and document the skew.

In the driver, I'd use a workqueue or a dedicated kernel thread to perform the reads, rather than doing them in the calling context. This allows the driver to batch reads and schedule them with precise timing. For each read cycle, the driver would: trigger all sensors simultaneously (if supported), then read each sensor's data in sequence, using the I2C transfer functions with appropriate timeouts.

The key to determinism is avoiding blocking operations in the read path. I'd use `i2c_transfer()` with a reasonable timeout, and ensure the driver doesn't hold any locks that could be contended. If the bus is shared, I'd consider using the I2C mux framework to isolate the sensors on their own bus segment, which reduces contention.

For the timing guarantee, I'd measure the actual worst-case read time for all sensors and compare it against the required sampling period. If the reads take too long, options include: using a faster bus speed (if the sensors support it), reading sensors in parallel if they're on different buses, or using DMA-capable I2C controllers if available.

I'd also design the driver to detect and report timing violations — for example, if a read cycle takes longer than the sampling period, the driver should log an error and potentially flag the data as suspect. In a medical device, this kind of diagnostic information is critical for post-market surveillance.

**Possible follow-ups:**
- How would you handle the case where one sensor on the bus is slow or unresponsive — does it affect the timing of the other reads?
- How would you verify the deterministic timing claim during testing, and what tools would you use?