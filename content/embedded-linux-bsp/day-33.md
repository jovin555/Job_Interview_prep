# embedded-linux-bsp — Day 33

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel log shows "Failed to request IRQ" for a device that worked on the previous board revision?

**Answer:** I'd start by treating this as a resource-conflict or configuration-drift problem rather than assuming the device itself is broken. The first step is to check whether the IRQ number in the device tree actually matches the interrupt line routed on the new board revision — a common cause is a hardware change (e.g., the interrupt pin moved to a different GPIO bank or the interrupt controller's output changed) that wasn't reflected in the device tree. I'd verify the device tree's `interrupts` property against the schematic and the SoC's interrupt controller binding.

Next, I'd check whether the IRQ is already claimed by another driver. This can happen if two devices are accidentally assigned the same interrupt line, or if a driver probes earlier and grabs the line without releasing it. I'd look at `/proc/interrupts` and the kernel log for other "request_irq" messages around the same time. If there's a conflict, the fix is usually in the device tree or in the probe ordering — for example, adding `interrupts-extended` with an explicit controller reference, or using a `depends-on` style property if the platform supports it.

I'd also check the interrupt controller itself. If the previous board used a GPIO controller as the interrupt parent and the new revision routes the line through a different controller (e.g., the SoC's built-in interrupt controller), the device tree's `interrupt-parent` may be wrong. Finally, I'd verify that the interrupt line isn't being held asserted at boot — some devices need their interrupt line deasserted before the driver requests it, and a hardware change (like a missing pull-up or an inverted polarity) can cause the line to be stuck active, which can lead to a failed request or an immediate storm.

**Possible follow-ups:**
- How would you distinguish between a device tree issue and a driver issue when the IRQ request fails?
- What tools or kernel config options would you enable to get more diagnostic information about interrupt registration?

---

## Q2: How would you approach designing a kernel driver for a device that needs to log sensor data to a file on the root filesystem at a fixed rate (e.g., 100 Hz) without causing filesystem corruption on unexpected power loss?

**Answer:** The key principle here is that the kernel driver should not be writing to a filesystem directly — that's a userspace responsibility. Filesystem writes involve page cache, journaling, and block layer operations that are not appropriate to perform from kernel context, especially at a fixed rate. So I'd structure the solution as a kernel driver that captures the sensor data and exposes it to userspace (e.g., via a character device, a ring buffer with `read()`, or a netlink socket), and a userspace daemon that handles the file I/O.

For the filesystem side, the critical design decision is choosing a filesystem and write strategy that survives power loss. I'd use a journaling filesystem like ext4 with `data=ordered` or `data=writeback` mode, but more importantly, I'd avoid writing directly to the root filesystem. Instead, I'd mount a dedicated data partition (e.g., on a separate eMMC partition or a separate flash device) with appropriate mount options. For high-frequency logging, I'd consider a log-structured filesystem or a raw block device with a simple ring-buffer format, since those are more tolerant of power loss.

The daemon should batch writes — accumulate data in memory and flush periodically (e.g., every second or when a buffer fills) rather than writing every sample individually. This reduces write amplification and wear on flash storage. I'd also use `fsync()` or `fdatasync()` at controlled intervals to ensure data is durable, but not on every write, since that would kill throughput. For unexpected power loss, the journal will handle metadata consistency, and the batching means at most a small window of data is lost — which should be documented as a design trade-off.

If the requirement is truly hard real-time logging with zero data loss on power failure, then a filesystem is the wrong tool entirely — I'd use a dedicated logging hardware (e.g., a battery-backed SRAM or a separate microcontroller with its own non-volatile storage) and treat the Linux side as a relay.

**Possible follow-ups:**
- How would you handle the case where the userspace daemon crashes — how would the system recover and resume logging?
- What mount options or filesystem features would you use to minimize wear on the flash storage?

---

## Q3: How would you approach implementing a kernel driver for a device that uses DMA to transfer data from an FPGA to system memory, where the FPGA can generate data at rates exceeding what the CPU can process in real-time?

**Answer:** The fundamental issue here is that if the FPGA generates data faster than the CPU can process, no amount of driver optimization will keep up — you need to design for backpressure or data reduction. I'd start by quantifying the actual rates: what's the FPGA's peak data rate, what's the CPU's processing capacity per unit of data, and what's the acceptable latency for the application? If the CPU genuinely can't keep up, the driver design must include a mechanism for the FPGA to pause or drop data.

Assuming the rates are manageable with proper buffering, I'd design the driver around a DMA ring buffer. The FPGA writes into a pre-allocated, physically contiguous DMA buffer (or a set of buffers), and the driver uses DMA engine APIs (e.g., `dma_alloc_coherent` or `dma_map_single` with a scatter-gather list) to set up the transfers. The FPGA signals completion via an interrupt, and the driver's interrupt handler acknowledges the transfer, updates the ring buffer head/tail pointers, and wakes up a kernel thread or uses a workqueue to process the data. The key is to avoid copying data in the interrupt handler — the handler should be minimal and defer processing to a lower-priority context.

For the ring buffer, I'd use a multi-buffer approach: the FPGA fills buffer N while the CPU processes buffer N-1. This double-buffering (or triple-buffering) prevents the CPU from stalling on DMA setup. The driver should also implement flow control — if the CPU falls behind, the driver can either drop the oldest data (with a counter to track drops) or signal the FPGA to pause via a GPIO or a register write. In a medical device context, dropping data is usually unacceptable, so I'd design the system to ensure the CPU has sufficient headroom, and I'd add a monitoring mechanism (e.g., a high-water mark on the ring buffer) to detect when the system is approaching overload.

For the userspace interface, I'd expose the data via a character device with `read()` semantics that block when no data is available, or use a mmap'd region for zero-copy access if the application can handle the data directly. I'd also consider using `poll()` or `epoll` to let the application wait efficiently.

**Possible follow-ups:**
- How would you handle the case where the FPGA generates data in bursts that exceed the DMA buffer size?
- How would you measure and verify that the driver is keeping up with the data rate under load?

---

## Q4: How would you approach debugging a situation where a custom board running Linux boots successfully, but the system clock is running roughly twice as fast as expected, and the RTC itself keeps correct time when read directly?

**Answer:** This symptom — the system clock running at roughly double speed while the RTC is correct — points to a clock source configuration problem, not an RTC issue. The RTC is a separate device that tracks time independently; the system clock is derived from a hardware timer or clock source. If the system clock runs fast, the kernel's notion of time is advancing faster than real time, which means the clock source's frequency is being misconfigured.

The most likely cause is a mismatch between the actual oscillator frequency and what the kernel or bootloader configured. For example, if the board uses a 24 MHz crystal but the kernel's clock driver is configured for 12 MHz, the timer will count twice as fast. I'd start by checking the device tree's clock configuration — the `clocks` property for the timer or the system timer node should reference the correct clock source and frequency. I'd also check the bootloader's clock initialization, since U-Boot often sets up the PLLs and dividers before the kernel starts.

Another common cause is a clock driver bug or a missing clock-frequency property in the device tree. Some SoCs require the `clock-frequency` property to be explicitly set in the timer node, and if it's missing or wrong, the kernel may default to a wrong value. I'd verify the actual oscillator frequency with an oscilloscope or by reading the hardware registers, then compare that to what the kernel thinks it is.

I'd also check whether the kernel is using the correct clock source. On ARM systems, the kernel may use the architected timer (if available) or a peripheral timer. If the device tree doesn't correctly describe which timer is the system clock source, the kernel might pick the wrong one. I'd look at `/sys/devices/system/clocksource/clocksource0/current_clocksource` to see which clock source is active, and check the kernel log for clock initialization messages.

Finally, I'd verify the RTC-to-system-clock synchronization. If the system clock is being set from the RTC at boot, and the RTC is correct, the drift will accumulate after boot. The fix is in the clock configuration, not the RTC driver.

**Possible follow-ups:**
- How would you verify the actual oscillator frequency on the board without a scope?
- What kernel config options or device tree properties would you check to confirm the clock source setup?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during integration testing, you discover that the kernel's real-time scheduling class (SCHED_FIFO) is causing priority inversion on a shared hardware resource between your sensor driver and the display driver. The display team insists their driver needs the highest priority, and the sensor team says their data will be corrupted if they miss their deadline. How would you handle this situation?

**Answer:** I'd start by framing this as a technical problem to be solved with data, not a disagreement to be arbitrated by opinion. The first step is to understand the actual timing requirements of both drivers. I'd ask the sensor team to quantify their deadline — what's the maximum acceptable latency between a sensor interrupt and the data being read? And I'd ask the display team to quantify theirs — what's the refresh period, and what happens if a frame is delayed? Often, the "hard" requirement is softer than it sounds, and having concrete numbers lets us reason about the system.

Next, I'd analyze the shared resource. Priority inversion happens when a high-priority task (the sensor driver) blocks on a lock held by a lower-priority task (the display driver), and a medium-priority task preempts the lower-priority task, extending the block. The classic fix is priority inheritance — the lower-priority task temporarily inherits the higher priority while holding the lock. In the kernel, this is handled by mutexes (which implement priority inheritance) versus spinlocks (which don't). If the drivers are using spinlocks, switching to mutexes where possible would be my first recommendation.

If the resource is a hardware register or a bus that can't be protected by a mutex (e.g., a shared I2C bus), then I'd look at serializing access differently — for example, using a dedicated kernel thread for each driver with a fixed priority, and using a lock-free ring buffer or a mailbox mechanism to pass data between the interrupt handler and the thread. This decouples the interrupt latency from the processing latency.

I'd also consider whether the two drivers actually need to share the resource at the same time. If the sensor reads happen at a fixed rate and the display refresh happens at a fixed rate, we might be able to schedule them so they don't overlap — though that's fragile and I'd avoid it as a primary solution.

Finally, I'd bring both teams together to review the analysis. I'd present the timing numbers, the lock analysis, and the proposed fix, and get agreement on the approach. If the display team still insists on the highest priority, I'd ask them to demonstrate why — what happens if their refresh is delayed by, say, 5 ms? If they can't show a concrete failure, the sensor deadline takes precedence. If both are truly hard, then the hardware design needs to change (e.g., separate buses or a dedicated DMA path), and I'd escalate that as a design change request.

**Possible follow-ups:**
- How would you measure and verify that priority inversion is actually occurring, rather than just theorizing about it?
- What if the shared resource is a hardware register that can only be accessed atomically — how would you handle that case?