# embedded-linux-bsp — Day 8

## Q1: How would you approach implementing a kernel driver for a device that needs to handle multiple simultaneous I2C sensor reads while maintaining deterministic timing in a medical monitoring application?

**Answer:** This requires careful design around the fact that I2C is a shared bus with inherent non-determinism due to arbitration and bus contention. I would start by analyzing whether the sensors can be placed on separate I2C buses or if they must share one — in a medical device, dedicating separate I2C controllers to critical sensors is often worth the PCB cost.

If they must share a bus, I'd structure the driver to use a kernel workqueue with a high-priority kworker thread, rather than relying on in-interrupt-context I2C transfers (which are generally not allowed anyway since I2C transfers can sleep). The driver would maintain a ring buffer of pending read requests, and the workqueue would process them in a round-robin fashion, using the `i2c_transfer()` API with repeated starts where possible to minimize bus overhead per transaction.

For deterministic timing, I'd use a high-resolution timer (hrtimer) to trigger read cycles at a fixed interval, rather than allowing reads to be triggered asynchronously from userspace. The timer callback would queue work to the workqueue, ensuring reads happen at predictable intervals regardless of userspace load. Each sensor's data would be timestamped at the start of the I2C transaction using `ktime_get()` and stored in a per-sensor buffer accessible via a character device or IIO framework.

The key trade-off is between throughput and determinism. If the sensors require different sampling rates, I'd use a timer at the LCM of all rates and skip reads for sensors that don't need data on that tick. I'd also implement a watchdog that detects if a single I2C transfer hangs the bus (e.g., slave holding SCL low) and resets the bus via the I2C controller's recovery mechanism.

**Possible follow-ups:** How would you handle the case where one sensor's read consistently takes longer than the sampling interval? What if the sensors have different I2C addresses but identical register maps — how would you structure the device tree binding?

---

## Q2: You're debugging a system where the kernel boots and the root filesystem mounts correctly, but userspace applications that access a GPIO-controlled relay consistently fail with "Device or resource busy" errors. How would you approach this?

**Answer:** The "Device or resource busy" error for a GPIO typically means something else has already claimed that GPIO line. I'd start by checking `/sys/kernel/debug/gpio` (if debugfs is mounted) to see which driver or process has the GPIO requested. The output shows the chip, line number, current consumer label, and direction.

If debugfs isn't available, I'd check `cat /sys/kernel/debug/pinctrl/*/pinmux-pins` to see pinmux assignments — the pin might be claimed by a different peripheral function (e.g., UART or I2C) rather than being configured as GPIO. This is common when the device tree has conflicting pinctrl settings.

Next, I'd examine the device tree for the GPIO controller node and the relay node. The relay's `gpios` property might reference the wrong GPIO bank or line number. I'd verify the GPIO controller's `#gpio-cells` property — if it's 2 (gpio, flags) but the relay node only provides one cell, the kernel might misinterpret the line number.

I'd also check if the GPIO is being used by the kernel's GPIO hog mechanism (a `gpio-hog` subnode in the device tree that reserves the line at boot). If the relay's driver and a hog both claim the same line, the second claimant gets -EBUSY.

If none of these reveal the issue, I'd add a `GPIOF_EXPORT` flag or use the `gpio-export` driver to temporarily export the line to sysfs and try toggling it from the shell — this helps distinguish between a kernel-level claim conflict and a userspace API issue.

**Possible follow-ups:** What if the error only occurs on one out of ten identical boards? How would you check if the pinmux is being configured correctly by the bootloader versus the kernel?

---

## Q3: How would you design a kernel module that needs to log sensor data to a file on the root filesystem at a fixed rate (e.g., 100 Hz) without causing filesystem corruption on unexpected power loss?

**Answer:** Writing to a filesystem from kernel space at 100 Hz is problematic for several reasons: kernel code should avoid filesystem operations directly (it's better to push data to userspace), and frequent writes increase wear on flash storage and risk corruption on power loss.

The recommended approach is to have the kernel module expose the sensor data through a character device or the IIO framework, and let a userspace daemon handle the logging. The daemon can use `O_SYNC` or `fdatasync()` at controlled intervals, and can implement buffering strategies that are easier to manage in userspace.

However, if the requirement genuinely demands kernel-side logging (e.g., the system has no userspace during early boot, or the sensor data is needed for safety-critical logging), I would:

1. **Use a high-resolution timer** to collect data at 100 Hz and store it in a large circular buffer in kernel memory (e.g., 10 seconds worth of data to absorb write latency).

2. **Use a kernel thread** (kthread) that periodically drains the buffer to a file using `kernel_write()` or `vfs_write()`. The thread would wake up every 500ms or when the buffer is 50% full, whichever comes first, to batch writes.

3. **Write to a dedicated partition** formatted with a journaling filesystem like ext4 or, better yet, a raw block device with a simple log-structured format that is resilient to power loss. A raw device avoids filesystem metadata corruption entirely.

4. **Implement a write-ahead log** — before overwriting old data, write the new data to a separate location and atomically update a pointer. This ensures that on power loss, the most recent complete record is always recoverable.

5. **Use `O_SYNC` or `sync_file_range()`** with `SYNC_FILE_RANGE_WRITE_AND_WAIT` to ensure data reaches the storage medium before acknowledging the write.

For a medical device, I'd also implement a startup check that scans the log partition for incomplete records and either discards or repairs them, and I'd monitor the filesystem's remaining space to prevent silent failures.

**Possible follow-ups:** How would you handle the case where the storage medium is nearly full? What if the logging rate needs to increase to 1 kHz — would you change your approach?

---

## Q4: How would you approach implementing a kernel driver for a device that uses DMA to transfer data from an FPGA to system memory, where the FPGA can generate data at rates exceeding what the CPU can process in real-time?

**Answer:** This is a classic flow-control problem. The key is to decouple the DMA transfer rate from the CPU processing rate using a ring buffer in system memory, and to implement backpressure so the FPGA doesn't overwrite unprocessed data.

I'd structure the driver as follows:

1. **Allocate a DMA-capable ring buffer** using `dma_alloc_coherent()` or `dma_alloc_noncoherent()` (depending on coherency requirements). The buffer would be divided into multiple segments (e.g., 16 segments of 64 KB each). The FPGA writes to one segment while the CPU reads from another.

2. **Use DMA engine API** — register a DMA channel via `dma_request_chan()` and set up a cyclic transfer if the FPGA continuously streams data, or use scatter-gather DMA for burst transfers. The DMA completion callback would fire when a segment is full.

3. **Implement flow control** — when the CPU is falling behind, the driver needs to tell the FPGA to pause. This could be a dedicated GPIO line (FPGA waits for a "ready" signal), or a register write over a side-channel like SPI. The driver would deassert the ready signal when all buffer segments are full and reassert it when the CPU frees a segment.

4. **Use a kthread for processing** — the DMA completion callback would wake a kernel thread that processes the completed segment (e.g., copies it to a userspace buffer via a character device read, or applies a filter). The thread runs at a real-time priority (SCHED_FIFO) to minimize latency.

5. **Implement a watermark mechanism** — the driver exposes two thresholds to userspace via sysfs: a "high watermark" (when the buffer is 75% full, userspace should start reading faster) and a "low watermark" (when it's 25% full, the risk of overflow has passed). Userspace can poll on a file descriptor that becomes readable when data is available.

If the FPGA genuinely outpaces the CPU even with these measures, the system design is fundamentally flawed — the driver should log an overflow event and drop the oldest data rather than crashing. For a medical device, this would trigger an alarm indicating the system cannot meet its processing requirements.

**Possible follow-ups:** How would you handle cache coherency between the CPU and DMA? What if the FPGA and CPU are on different interconnects with different memory ordering guarantees?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during integration testing, you discover that the kernel's real-time scheduling class (SCHED_FIFO) is causing priority inversion on a shared hardware resource between your sensor driver and the display driver. The display team insists their driver needs the highest priority, and the sensor team says their data will be corrupted if they miss their deadline. How would you handle this situation?

**Answer:** Priority inversion in a medical device is a safety concern, not just a performance issue, so I'd treat it with the same rigor as a hardware fault. My approach would be:

First, I'd call an immediate meeting with both teams, the systems architect, and a regulatory representative if available. I'd bring data — specifically, a trace of the actual scheduling behavior showing the inversion scenario: which thread held the lock, which thread was blocked, and for how long. Without data, the discussion becomes emotional rather than technical.

During the meeting, I'd frame the problem as a system-level constraint, not a team conflict. The question isn't "whose driver is more important" but "how do we meet both requirements within the real-time guarantees the device needs." I'd present three categories of solutions:

1. **Eliminate the shared resource** — can the sensor and display use separate hardware resources (e.g., separate SPI buses, separate DMA channels)? This is the cleanest fix and avoids priority inversion entirely. If the hardware allows it, this is my preferred path.

2. **Use priority inheritance** — if the shared resource must remain shared, I'd implement a mutex with priority inheritance (via `rt_mutex` in the kernel) so that the lower-priority task holding the lock temporarily inherits the higher priority of the blocked task. This prevents the inversion but adds complexity and must be carefully tested for deadlocks.

3. **Restructure the scheduling** — if the sensor's deadline is truly hard (data corruption on miss) and the display's is soft (visible glitch but no safety impact), then the sensor should have higher priority. I'd ask the display team to quantify what happens if they miss a deadline — if it's just a frame drop, that's acceptable. If it's a safety concern, we need to revisit the architecture.

I'd also propose a short-term mitigation: add a kernel configuration that enables `CONFIG_PREEMPT_RT` (if not already enabled) and use `schedule_timeout()` with appropriate priority ceilings. For the long term, I'd push for a hardware change in the next revision to decouple the resources.

Finally, I'd document the decision in the risk management file (ISO 14971 context) — even if we solve the inversion, the fact that it was possible represents a hazard that should be tracked. I'd also add a kernel selftest that stresses the shared resource under high load to catch regressions.

**Possible follow-ups:** What if the hardware team says they can't change the design for another 18 months? How would you implement priority inheritance in a driver that currently uses a spinlock?