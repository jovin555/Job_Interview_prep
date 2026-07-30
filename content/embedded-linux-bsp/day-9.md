# embedded-linux-bsp — Day 9

## Q1: How would you approach implementing a kernel driver for a device that needs to handle multiple simultaneous I2C sensor reads while maintaining deterministic timing in a medical monitoring application?

**Answer:** This requires careful consideration of both the I2C bus limitations and the real-time requirements. I2C is inherently a multi-master, half-duplex protocol, so simultaneous reads from multiple sensors on the same bus are actually sequential from the bus perspective. The key is to structure the driver to minimize latency variation.

First, I'd assess whether all sensors can share a single I2C bus or if they need dedicated buses. For deterministic timing, I'd prefer dedicating a bus per critical sensor if the SoC has sufficient I2C controllers. If sharing is necessary, I'd use a kernel workqueue with a high-priority RT worker thread rather than tasklets, because workqueues can sleep during I2C transfers (which are blocking operations).

The driver should use the kernel's `i2c_transfer()` function with batched messages — combining multiple read/write operations into a single transfer where possible, which reduces bus arbitration overhead. For true determinism, I'd implement a periodic timer (using `hrtimer`) that triggers a batch read cycle at the required sampling rate. The timer callback would schedule a work item that performs all I2C transfers sequentially, then pushes data to a ring buffer accessible from userspace.

Critical considerations: ensure the I2C controller's clock speed is set appropriately for the bus length and sensor capacitance; use repeated START conditions instead of STOP/START between reads to maintain bus ownership; and handle arbitration loss or NACK conditions gracefully with retry logic that doesn't exceed the timing budget.

**Possible follow-ups:** How would you handle the case where one sensor on the shared bus starts generating clock stretching that delays reads from other sensors? What kernel configuration options are relevant for real-time I2C performance?

---

## Q2: You're debugging a system where the kernel boots and the root filesystem mounts correctly, but userspace applications that access a GPIO-controlled relay consistently fail with "Device or resource busy" errors. How would you approach this?

**Answer:** This error typically means something else has already claimed the GPIO. I'd start by checking the kernel's GPIO debug interface — looking at `/sys/kernel/debug/gpio` to see which driver or subsystem has requested that particular GPIO line. The output shows the pin number, label, and whether it's configured as input or output.

Common causes include: a pinmux conflict where the same GPIO is also configured for an alternate function (e.g., UART or I2C) in the device tree; a kernel driver that claimed the GPIO during probe but never released it; or the GPIO being used by the `gpio-leds` or `gpio-keys` driver if the device tree has overlapping definitions.

I'd also check the device tree to see if the GPIO is referenced in multiple nodes — for example, both as a regulator enable pin and as a GPIO-controlled relay. The pin control subsystem might have allocated it to a different peripheral. Running `cat /sys/kernel/debug/pinctrl/*/pinmux-pins` shows the current pinmux assignments.

If the GPIO is free in debugfs but userspace still gets the error, the issue might be in the userspace library — perhaps the application is using the wrong GPIO number (GPIO numbers can differ between the kernel's internal numbering and the sysfs/gpiochip interface). I'd verify by trying to export the GPIO manually via sysfs or using the `gpioinfo` tool from libgpiod.

**Possible follow-ups:** How would you distinguish between a pinmux conflict and a driver that's holding the GPIO without releasing it? What would you check in the device tree to identify overlapping GPIO usage?

---

## Q3: How would you design a kernel module that needs to log sensor data to a file on the root filesystem at a fixed rate (e.g., 100 Hz) without causing filesystem corruption on unexpected power loss?

**Answer:** This is a classic problem in embedded systems — balancing write performance with data integrity. At 100 Hz, we're generating 100 write operations per second, which is too fast for synchronous writes without causing severe performance degradation and flash wear.

The approach I'd take involves several layers:

First, the kernel module should not write directly to files — that's a userspace responsibility. Instead, the module should maintain a large ring buffer in kernel memory (allocated with `kzalloc` or `dma_alloc_coherent` for large buffers). The sensor data is written into this buffer from the interrupt or timer context. A kernel thread (using `kthread_run`) periodically wakes up, checks the buffer fill level, and copies data to a pre-allocated userspace buffer via a character device interface or relayfs.

On the userspace side, a daemon reads from the character device and writes to a file. For power-loss safety, I'd use a filesystem designed for embedded use — UBIFS on raw NAND or F2FS on eMMC — both handle unexpected power loss better than ext4. The daemon should use `O_SYNC` or `fdatasync()` periodically (e.g., every 100 writes, not every write) to balance integrity with performance.

For critical medical data where no loss is acceptable, consider a dual-buffer approach: the kernel module writes to two separate ring buffers, and the userspace daemon alternates reading from them. If power is lost, at most one buffer's worth of data is lost. Alternatively, use a dedicated SPI NOR flash or FRAM for the log — these have better write endurance and power-loss characteristics than NAND.

**Possible follow-ups:** How would you handle the case where the userspace daemon crashes or falls behind the kernel's write rate? What filesystem features (like journaling or writeback throttling) would you consider or avoid?

---

## Q4: How would you approach implementing a kernel driver for a device that uses DMA to transfer data from an FPGA to system memory, where the FPGA can generate data at rates exceeding what the CPU can process in real-time?

**Answer:** This is a flow-control problem. The FPGA can outrun the CPU, so we need backpressure or data dropping strategies. The approach depends on whether data loss is acceptable.

First, I'd characterize the maximum FPGA data rate and the CPU's processing capacity. If the FPGA can sustain 500 Mbps but the CPU can only process 200 Mbps, we have a fundamental mismatch.

The driver should use the kernel's DMA engine API (`dmaengine`) with scatter-gather lists. I'd allocate a pool of DMA buffers in a ring configuration — perhaps 16 or 32 buffers, each sized to hold a reasonable chunk of data (e.g., 64 KB). The FPGA writes into the currently active buffer, then triggers an interrupt when the buffer is full. The DMA controller (or the FPGA itself) should support chaining — automatically switching to the next buffer without CPU intervention.

The interrupt handler doesn't process data; it just moves the full buffer to a "ready" queue and wakes a kernel thread. The kernel thread processes buffers from the ready queue. If the ready queue fills up (meaning the CPU is falling behind), the driver has options: drop the oldest buffer (if data loss is acceptable), signal the FPGA to pause via a dedicated GPIO or register write (if the FPGA supports flow control), or increase buffer count to absorb bursts.

For medical monitoring where data loss is unacceptable, I'd implement a credit-based flow control protocol between the FPGA and the driver. The driver periodically sends a "buffer available" count to the FPGA; the FPGA only sends data when it has credits. This prevents the FPGA from overwhelming the system.

**Possible follow-ups:** How would you handle DMA buffer alignment and cache coherency on ARM platforms? What happens if the DMA transfer completes but the kernel thread isn't scheduled immediately due to higher-priority interrupts?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during integration testing, you discover that the kernel's real-time scheduling class (SCHED_FIFO) is causing priority inversion on a shared hardware resource between your sensor driver and the display driver. The display team insists their driver needs the highest priority, and the sensor team says their data will be corrupted if they miss their deadline. How would you handle this situation?

**Answer:** Priority inversion is a well-known problem in RTOS and RT-Linux systems, and it needs a structured resolution rather than a subjective "who's more important" debate.

First, I'd call a meeting with both teams and a systems architect to understand the actual timing requirements. I'd ask each team to provide hard numbers: the sensor team needs to specify the exact deadline (e.g., "data must be read within 2 ms of the hardware trigger") and what happens if it's missed (data corruption vs. stale data). The display team needs to specify their worst-case execution time and how often they hold the shared resource.

Then I'd analyze the shared resource itself. Is it a hardware peripheral (e.g., a DMA controller, a memory region, an SPI bus) or a software lock (mutex, spinlock)? If it's a hardware resource, can we duplicate it — give each driver its own instance? If it's a software lock, can we use a priority inheritance mutex (`PTHREAD_PRIO_INHERIT` in userspace, or `rt_mutex` in kernel) to temporarily boost the lower-priority task holding the lock?

If the resource truly must be shared, I'd propose a design change: restructure the drivers so the shared resource access is serialized through a dedicated mediator thread with a fixed priority between the two drivers. Neither driver directly accesses the resource; they queue requests to the mediator. This breaks the priority inversion chain.

If neither team can compromise on priority, I'd escalate to the systems engineer with a documented trade-off analysis showing the risk of each option — including the possibility of adding a dedicated hardware resource (e.g., a second SPI controller) to eliminate the sharing entirely. The final decision should be based on patient safety risk, not team preference.

**Possible follow-ups:** How would you document this decision for regulatory purposes (ISO 14971 risk management)? What if the hardware team says adding a second SPI controller would require a PCB respin that delays the project by three months?