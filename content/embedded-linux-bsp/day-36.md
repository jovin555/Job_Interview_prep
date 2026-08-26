# embedded-linux-bsp — Day 36

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel is not detecting one of two identical I2C sensors on the same bus, while the other works fine?

**Answer:** I'd start by verifying the obvious: check `i2cdetect` to see if the device appears on the bus at all, and compare the device tree entries for both sensors to ensure the addresses and compatible strings are correct. Since the sensors are identical, a likely culprit is an address conflict or a hardware issue specific to that sensor's connection.

Next, I'd check the kernel log for any probe errors related to the missing sensor — sometimes the driver probes but fails during initialization, which would show up as an error message. If the sensor isn't detected at the bus level, I'd use an oscilloscope or logic analyzer to verify the I2C lines during the scan, checking for proper pull-up behavior and signal integrity. A weak pull-up, a cold solder joint, or a marginal trace on one sensor's SDA/SCL lines could cause intermittent or failed communication.

If the sensor is detected by `i2cdetect` but the driver doesn't bind, I'd check whether the device tree node has the correct address and whether the driver's compatible string matches. I'd also verify that the interrupt line (if used) isn't shared or misconfigured, since a stuck interrupt line can prevent probe from completing. Finally, I'd check if the sensor's power supply or reset line is properly sequenced — sometimes one sensor's reset GPIO isn't being asserted correctly, leaving it in an undefined state.

**Possible follow-ups:**
- How would you distinguish between a hardware issue and a device tree configuration issue in this scenario?
- What if both sensors are detected by `i2cdetect` but only one works — how would you approach that?

---

## Q2: How would you approach implementing a kernel driver for a device that needs to perform a hardware-triggered DMA transfer, where the trigger comes from an external sensor's interrupt line, and the data must be processed and made available to userspace within a hard real-time deadline (e.g., 2 ms)?

**Answer:** This requires careful design across the interrupt path, DMA setup, and userspace delivery mechanism. First, I'd ensure the sensor's interrupt is configured as a hardware trigger for the DMA controller, rather than routing it through the CPU — this avoids interrupt latency and lets the DMA engine move data directly to memory. The DMA channel would be configured in cyclic or double-buffer mode so that while one buffer is being filled, the other can be processed.

For the kernel-to-userspace path, I'd avoid traditional read/write syscalls with blocking I/O, as those introduce scheduling latency. Instead, I'd use a mechanism like `O_NONBLOCK` with poll/epoll, or better yet, a shared memory region with a ring buffer that userspace can mmap. The driver would update a sequence counter or use a futex to signal new data availability. For hard real-time requirements, I'd also consider using the PREEMPT_RT patch set and marking the relevant threads as SCHED_FIFO with appropriate priorities.

The critical design question is whether the 2 ms deadline includes the entire path from sensor interrupt to userspace application processing. If so, I'd need to measure each stage: interrupt latency, DMA setup time, buffer management, and the wake-up path. I'd also ensure that the DMA completion interrupt is handled with minimal work — ideally just updating the buffer index and waking the waiting thread, with any heavy processing deferred to a dedicated kernel thread or done in userspace.

**Possible follow-ups:**
- How would you handle the case where the sensor generates data faster than userspace can consume it?
- What are the trade-offs between using a kernel thread versus a workqueue for processing the DMA data?

---

## Q3: How would you approach designing the boot sequence for a system with two processors — an application processor running Linux and a safety-critical microcontroller — where the microcontroller must be fully initialized and running its safety monitoring routines before the Linux userspace starts any critical applications?

**Answer:** The key constraint is establishing a deterministic handshake between the two processors before Linux userspace proceeds. I'd structure this in three phases: bootloader, kernel, and userspace.

In the bootloader phase, I'd have U-Boot release the microcontroller from reset and wait for a "ready" signal — either via a GPIO line, a shared memory mailbox, or a simple UART handshake. This ensures the MCU is at least running its initialization code before Linux starts booting. However, waiting in U-Boot adds boot time, so I might instead have U-Boot release the MCU and continue booting Linux, with the actual readiness check deferred to the kernel.

In the kernel phase, I'd write a small platform driver that probes early (using `initcall` or a device tree node with `status = "okay"`) and waits for the MCU to signal readiness. This driver would poll a shared memory location or wait on an interrupt from the MCU. The driver would expose a sysfs attribute or use a completion mechanism that blocks until the MCU is confirmed ready.

In the userspace phase, the critical applications would be started by a supervisor process (e.g., systemd with explicit ordering) that first checks the readiness flag from the kernel driver. If the MCU isn't ready within a timeout, the supervisor would either retry, log an error, or enter a safe state — depending on the safety requirements. I'd also consider using a hardware watchdog that the MCU must service, so that if the MCU fails to initialize, the system resets rather than proceeding with an unsafe configuration.

**Possible follow-ups:**
- What happens if the MCU never signals ready — how would you handle the failure mode?
- How would you handle the case where the MCU needs to be reset and re-initialized while Linux is already running?

---

## Q4: How would you approach implementing a kernel driver for a device that needs to be accessed by both a real-time safety-critical task and a non-real-time monitoring task, where the safety-critical task must never be blocked by the monitoring task?

**Answer:** The fundamental requirement is that the safety-critical path must have guaranteed access to the hardware regardless of what the monitoring task is doing. I'd start by identifying the shared resource — is it the device itself, a DMA channel, or an interrupt line? The design approach depends on the nature of the contention.

For the driver architecture, I'd use separate access paths: the safety-critical task would use a dedicated, lock-free interface (e.g., a ring buffer with atomic indices or a memory-mapped register region), while the monitoring task would use a more conventional interface with mutexes. The key is to avoid any shared locks between the two paths. If the hardware requires exclusive access, I'd use a priority-inheritance-aware mutex or a seqlock, where the safety-critical reader never blocks the writer and vice versa.

For interrupt handling, the safety-critical path would use a dedicated IRQ with `IRQF_NO_THREAD` to ensure it runs in hardirq context, while the monitoring path could use a threaded IRQ. The driver would maintain separate buffers for each consumer, with the safety-critical buffer being small and fixed-size to guarantee bounded latency.

I'd also consider whether the monitoring task truly needs direct hardware access or if it can consume data that the safety-critical path produces. If possible, I'd have the safety-critical driver expose a read-only interface (e.g., via sysfs or a shared memory region) that the monitoring task can poll without ever touching the hardware directly. This eliminates contention entirely.

**Possible follow-ups:**
- How would you handle the case where the monitoring task needs to configure the device, which requires exclusive access?
- What are the trade-offs between using a seqlock versus a priority-inheritance mutex in this scenario?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during integration testing, you discover that the kernel's real-time scheduling class (SCHED_FIFO) is causing priority inversion on a shared hardware resource between your sensor driver and the display driver. The display team insists their driver needs the highest priority, and the sensor team says their data will be corrupted if they miss their deadline. How would you handle this situation?

**Answer:** I'd start by convening a meeting with both teams to understand the actual constraints — not just their stated priorities, but the real timing requirements. I'd ask the display team to quantify what happens if their driver is delayed by, say, 5 ms or 10 ms: does the display tear, or does it just have a slightly delayed frame? Similarly, I'd ask the sensor team to quantify the exact deadline and what "corrupted data" means — is it a missed sample, or is it a cascading failure that affects other subsystems?

With that data, I'd look for ways to eliminate the contention rather than just arbitrate it. For example, if the shared resource is a DMA channel or a memory region, can we partition it so each driver has its own dedicated resource? If it's a bus (like I2C), can we move one device to a different bus or use a different access pattern? Often, the real fix is architectural — removing the shared resource entirely.

If the contention can't be eliminated, I'd propose a priority-inheritance protocol or a priority ceiling approach, where the lower-priority task temporarily inherits the higher priority when it holds the shared lock. This is the standard solution to priority inversion. I'd also suggest using `sched_setattr` with careful priority assignments based on measured worst-case execution times, rather than intuition.

Finally, I'd push for a system-level real-time analysis — using tools like `cyclictest` or ftrace to measure actual latencies — so we can make data-driven decisions about priorities rather than relying on team opinions. The goal is to find a configuration where both subsystems meet their requirements, and if that's not possible, I'd escalate with clear evidence about the trade-offs.

**Possible follow-ups:**
- How would you handle the situation if the display team refuses to lower their priority, citing a customer requirement?
- What metrics would you collect to make a data-driven decision about priority assignments?