# embedded-linux-bsp — Day 6

## Q1: How would you approach implementing a kernel driver for a device that needs to handle multiple simultaneous I2C sensor reads while maintaining deterministic timing in a medical monitoring application?

**Answer:** This requires careful consideration of the I2C bus architecture and kernel scheduling. I2C is inherently a shared bus with multi-master arbitration, so deterministic timing means controlling both bus contention and driver latency. My approach would be:

First, evaluate whether the sensors can share a single I2C bus or need dedicated buses. If timing requirements are tight (e.g., reading three sensors every 10ms), dedicating separate I2C controllers to critical sensors eliminates arbitration delays. The device tree would describe each bus as a separate I2C node.

For the driver itself, I'd use the kernel's I2C framework (`struct i2c_driver`) with the `i2c_transfer()` API, but avoid the standard client-probe model for timing-critical paths. Instead, I'd implement a kernel worker thread (using `kthread_worker` or a high-resolution timer) that runs at a fixed priority, rather than relying on the I2C subsystem's asynchronous messaging. This worker would:
- Pre-allocate all transfer buffers to avoid allocation latency
- Use `i2c_master_send()`/`i2c_master_recv()` directly in the worker context
- Implement a simple state machine to pipeline reads across sensors on the same bus

For true determinism, consider using the kernel's `PREEMPT_RT` patch set if the system can support it, and pin the worker thread to a dedicated CPU core. The driver should also handle bus recovery — if a sensor holds the clock line low, the kernel's I2C bus recovery mechanism (bit-banging SCL) needs to be triggered without blocking the entire system.

Finally, validate timing with a logic analyzer or oscilloscope on the actual I2C lines, not just software timestamps, because kernel scheduling jitter can mask bus-level issues.

**Possible follow-ups:** How would you handle a sensor that occasionally NAKs its address during a scan? What if the I2C controller itself has a FIFO that can queue multiple transactions — how would you leverage that?

---

## Q2: You're debugging a system where the kernel boots and the root filesystem mounts correctly, but userspace applications that access a GPIO-controlled relay consistently fail with "Device or resource busy" errors. How would you approach this?

**Answer:** This is a classic GPIO resource contention issue. The "Device or resource busy" error typically means the GPIO line is already claimed by another kernel driver or subsystem. My debugging approach would be:

First, check `/sys/kernel/debug/gpio` (if CONFIG_DEBUG_GPIO is enabled) to see which driver has claimed the GPIO in question. This shows the pin number, current direction, and the consumer label. If debugfs isn't available, I'd check the device tree to see if the GPIO is referenced by multiple nodes — perhaps the pin is defined both as a GPIO-controlled relay and as a reset line for another device, or it's being used by a pin control subsystem.

Next, examine the boot log with `dmesg | grep gpio` to see which drivers probed and claimed the pin. Look for messages like "gpio-xxx: claimed by driver-yyy". If a driver is claiming the GPIO during probe but not releasing it, that's the culprit.

Common causes include:
- The GPIO is also defined in a pinctrl node for some other peripheral
- A regulator driver has claimed it as a voltage enable pin
- The GPIO controller's `gpio-reserved-ranges` property in the device tree is misconfigured
- A previous kernel module that used the GPIO didn't properly free it on unload

If the GPIO is legitimately shared (e.g., an open-drain line with multiple drivers), the solution is to use the `gpiod` API with the `GPIOD_FLAGS_BIT_NONEXCLUSIVE` flag, or restructure the device tree to assign the GPIO to a single consumer that exports it via a character device or sysfs.

**Possible follow-ups:** How would you modify the device tree to debug this without recompiling the kernel? What if the GPIO controller itself is a GPIO expander on I2C — how does that change the debugging approach?

---

## Q3: How would you design a kernel module that needs to log sensor data to a file on the root filesystem at a fixed rate (e.g., 100 Hz) without causing filesystem corruption on unexpected power loss?

**Answer:** Writing to a filesystem from kernel space at 100 Hz is problematic for several reasons: kernel modules shouldn't directly perform filesystem I/O (that's userspace's job), and frequent writes increase wear on flash storage and risk corruption. The proper design is a split architecture:

**Kernel side:** Implement a character device driver that maintains a large ring buffer in kernel memory (allocated with `kmalloc` or `dma_alloc_coherent`). The driver's interrupt handler or worker thread writes sensor data into this buffer using lockless ring buffer techniques (e.g., `kfifo` or a custom atomic head/tail pointer). The driver exposes a `read()` file operation that copies data from the ring buffer to userspace, blocking if the buffer is empty.

**Userspace side:** A dedicated logging daemon (written in C or Python) opens the character device, reads data in large chunks (e.g., 64KB at a time), and writes to a file using standard POSIX I/O. This daemon can:
- Use `O_SYNC` or `fdatasync()` periodically (e.g., every 100ms) to ensure data reaches the storage medium
- Buffer writes in userspace to reduce system call overhead
- Handle the filesystem safely because it runs in userspace with proper error handling

For power-loss safety on the filesystem side, use a journaling filesystem like ext4 with `data=ordered` mode, or consider a transactional filesystem like UBIFS for raw NAND. The daemon should also implement a simple write-ahead log: write data to a temporary file, then atomically rename it to the final location.

If the requirement truly demands kernel-side file writes (e.g., no userspace is running yet), the only safe approach is to use the kernel's `vfs_write()` interface with a dedicated kernel thread, but this is strongly discouraged for production systems. A better alternative is to use pstore/ramoops to store critical data in a reserved RAM region that survives reboot, then extract it on next boot.

**Possible follow-ups:** How would you handle the case where the ring buffer fills up faster than userspace can drain it? What filesystem features would you look for in an eMMC-based medical device to minimize write amplification?

---

## Q4: Behavioral — You're the BSP lead for a medical device project, and during integration testing, you discover that the kernel's real-time scheduling class (SCHED_FIFO) is causing priority inversion on a shared hardware resource between your sensor driver and the display driver. The display team insists their driver needs the highest priority, and the sensor team says their data will be corrupted if they miss their deadline. How would you handle this?

**Answer:** Priority inversion in a medical device is a safety-critical issue that needs systematic resolution, not a compromise based on team preferences. Here's how I'd approach it:

First, I'd call a meeting with both teams, the systems architect, and the safety engineer. The goal isn't to declare a winner but to understand the actual constraints. I'd ask each team to provide:
- The exact timing requirements (deadline, period, worst-case execution time)
- The shared resource in question (is it a hardware mutex, a DMA channel, a memory region?)
- The consequence of missing a deadline (data corruption vs. visual glitch vs. patient harm)

With that data, I'd analyze the priority inversion scenario. Classic priority inversion occurs when a high-priority task (sensor) is blocked waiting for a resource held by a low-priority task, while a medium-priority task (display) preempts the low-priority task. The solution depends on the resource:

- If the resource is a spinlock or mutex in kernel space, switch to priority inheritance mutexes (`CONFIG_MUTEX_SPIN_ON_OWNER` with RT mutexes). The kernel's RT mutex implementation automatically boosts the priority of the lock holder to the highest waiting priority, breaking the inversion.
- If the resource is a hardware register or DMA channel, consider using a hardware semaphore if the SoC provides one, or restructure the drivers to use a dedicated mediator driver that serializes access with proper priority handling.
- If the resource is a memory buffer shared via DMA, implement a double-buffering scheme where each driver gets its own buffer and the hardware switches between them atomically.

I'd also challenge the priority assignments themselves. In a medical device, the sensor data path likely has a direct patient safety impact, while the display might tolerate occasional frame drops. The priority should reflect criticality, not convenience. If the display truly needs high priority (e.g., for alarm rendering), then the resource contention needs a hardware-level solution.

Finally, I'd document the analysis and resolution in the risk management file (per ISO 14971) as a design mitigation for priority inversion hazards. The decision would be reviewed by the safety team before implementation.

**Possible follow-ups:** What if the priority inversion is caused by a third-party driver that you can't modify? How would you validate that your fix actually resolves the inversion under all load conditions?

---

## Q5: How would you approach implementing a kernel driver for a device that uses DMA to transfer data from an FPGA to system memory, where the FPGA can generate data at rates exceeding what the CPU can process in real-time?

**Answer:** This is a classic flow-control problem — the producer (FPGA) can outrun the consumer (CPU/driver). The key is to design a backpressure mechanism that prevents data loss without dropping to polling or busy-waiting. Here's my approach:

**DMA engine setup:** Use the kernel's DMA engine API (`dmaengine`) with a scatter-gather list of pre-allocated DMA buffers. I'd allocate a pool of buffers (e.g., 16 buffers of 64KB each) using `dma_alloc_coherent()` or `dma_alloc_noncoherent()` depending on cache coherency requirements. Each buffer is registered as a scatter-gather entry.

**Flow control strategy:** Implement a circular buffer of DMA descriptors. The FPGA writes to the current buffer and signals completion via an interrupt when the buffer is full. The driver's interrupt handler:
1. Disables further DMA transfers to the current buffer (by clearing the FPGA's "buffer ready" flag)
2. Submits the completed buffer to a workqueue for processing
3. Advances to the next buffer in the pool
4. Re-enables DMA to the new buffer

If all buffers are in use (FPGA has filled them faster than the workqueue can process), the driver has two options:
- **Drop data:** Clear the FPGA's "ready" flag and let it overwrite the oldest buffer (acceptable only if data loss is tolerable)
- **Backpressure:** Assert a GPIO line to tell the FPGA to pause transmission, then de-assert when a buffer becomes free

**Processing path:** The workqueue function copies data from the DMA buffer to a larger ring buffer in system memory (or directly to userspace via a character device read). After processing, the buffer is returned to the free pool.

**Key considerations:**
- Use `dma_sync_single_for_cpu()` / `dma_sync_single_for_device()` for cache maintenance if using non-coherent DMA
- Ensure the interrupt handler is fast — it should only flip buffer ownership and schedule work, not do data processing
- Consider using threaded IRQs (`request_threaded_irq`) to move the bulk of interrupt work to a process context
- For very high data rates, use the DMA engine's cyclic mode with linked-list descriptors to avoid per-buffer interrupt overhead

**Possible follow-ups:** How would you handle the case where the FPGA signals a buffer full but the DMA transfer hasn't actually completed yet (race condition)? What if the system needs to support multiple DMA channels from different FPGA modules simultaneously?