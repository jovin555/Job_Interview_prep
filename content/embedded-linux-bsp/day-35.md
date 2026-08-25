# embedded-linux-bsp — Day 35

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel is not detecting one of two identical I2C sensors on the same bus, while the other works fine?

**Answer:** I'd start by confirming the problem is at the kernel level rather than the hardware level. First, I'd check whether the sensor is actually present on the bus using `i2cdetect` from userspace — if the device shows up there but the kernel driver isn't binding to it, that points to a device tree or driver matching issue. If it doesn't show up at all, I'd suspect a hardware problem.

For the device tree angle, I'd verify the second sensor's node has the correct `reg` address matching its address pins, and that the interrupt line (if used) is correctly specified and not conflicting with another device. A common issue is two devices sharing an interrupt line where the device tree doesn't properly describe the sharing, or where the GPIO controller can't route both interrupts.

I'd also check the kernel log for probe deferral messages — the driver might be returning `-EPROBE_DEFER` because a dependency (like a regulator or reset GPIO) isn't ready, and if the probe is never retried, the device stays unbound. I'd look at `/sys/bus/i2c/devices/` to see if the device is present but in an "unbound" state.

On the hardware side, I'd verify the address pins are strapped correctly on the second sensor, check the pull-ups on SDA/SCL are adequate for both devices (especially if the second sensor is farther from the controller), and confirm there's no address conflict — two identical sensors often need different address strap configurations.

**Possible follow-ups:**
- How would you distinguish between a device tree issue and a driver issue when the sensor is detected by `i2cdetect` but the driver doesn't bind?
- What kernel configuration options or debugfs interfaces would you use to trace probe deferral chains?

---

## Q2: How would you approach implementing a kernel driver for a device that needs to perform a hardware-triggered DMA transfer, where the trigger comes from an external sensor's interrupt line, and the data must be processed and made available to userspace within a hard real-time deadline (e.g., 2 ms)?

**Answer:** This is fundamentally about minimizing latency between the hardware event and the data reaching userspace, while ensuring the DMA transfer is set up before the trigger arrives. I'd structure this as a character device driver with a ring buffer, using a combination of interrupt-driven and DMA-based data movement.

The key design decision is how the DMA is triggered. If the sensor's interrupt line can directly trigger the DMA controller (hardware-linked), that's ideal — the DMA transfer starts without CPU involvement. In that case, the interrupt handler's job is just to wake up a kernel thread or use a wait queue to signal that data is ready. If the DMA can't be hardware-triggered, the interrupt handler must initiate the DMA transfer, which adds latency but is still feasible within 2 ms if the transfer is small.

For the DMA setup, I'd allocate the DMA buffer using `dma_alloc_coherent` or `dma_map_single` to ensure it's physically contiguous and properly aligned. The buffer would be a double-buffered or ring-buffer arrangement so that while one buffer is being filled by DMA, the previous one can be copied to userspace.

For the userspace path, I'd use a combination of `poll`/`select` with a wait queue, and possibly `O_NONBLOCK` reads. The driver would signal readiness via `poll_wait`, and the read operation would copy from the completed DMA buffer. To meet the 2 ms deadline, I'd avoid any sleeping locks in the interrupt path, use `spin_lock` or lock-free ring buffer techniques, and ensure the copy-to-userspace operation is the only potentially blocking step.

If the deadline is truly hard, I'd also consider using a real-time kernel patch (PREEMPT_RT) or moving the processing to a dedicated high-priority kernel thread with `SCHED_FIFO`. I'd also measure the actual latency distribution under load — the worst-case latency matters more than the average.

**Possible follow-ups:**
- How would you handle the case where the DMA transfer size varies between triggers?
- What happens if the userspace application doesn't read the data fast enough — how would you handle buffer overflow?

---

## Q3: How would you approach designing the boot sequence for a system with two processors — an application processor running Linux and a safety-critical microcontroller — where the microcontroller must be fully initialized and running its safety monitoring routines before the Linux userspace starts any critical applications?

**Answer:** This requires careful coordination between the bootloader, kernel, and userspace initialization. The fundamental constraint is that the safety-critical microcontroller must be ready before any Linux application that depends on its monitoring starts operating.

I'd approach this in layers. First, at the bootloader level, I'd ensure the microcontroller is released from reset and given its firmware (if it doesn't have its own non-volatile storage) before the kernel starts. This could mean loading the MCU firmware from the bootloader or having the bootloader assert a GPIO that releases the MCU from reset. The bootloader should also verify the MCU is running — perhaps by checking a handshake GPIO or reading a status register over a shared interface — before proceeding to boot Linux.

At the kernel level, I'd write a small driver that manages the MCU's lifecycle. This driver would be responsible for: confirming the MCU is alive (via a heartbeat or status register), exposing a "ready" flag to userspace, and potentially managing a watchdog relationship where the MCU monitors the Linux side. The driver would probe early in the kernel boot sequence, and its probe function would block until the MCU signals readiness — this ensures that by the time userspace starts, the MCU is confirmed operational.

In userspace, I'd use a synchronization mechanism — either a sysfs attribute exposed by the driver, or a dedicated initialization service that runs before any critical applications. Systemd, for example, could have a service that waits for the MCU-ready signal before starting dependent services. The critical applications would have an explicit dependency on this service.

I'd also consider the failure modes: what happens if the MCU doesn't come up? The system should fail safe — either refusing to start critical applications, or entering a degraded mode where only non-critical functions are available. This decision should be documented in the risk analysis.

**Possible follow-ups:**
- How would you handle the case where the MCU needs to be reflashed in the field — would the boot sequence change?
- What if the MCU takes significantly longer to initialize than the Linux kernel — how would you handle the timing mismatch?

---

## Q4: How would you approach implementing a kernel driver for a device that needs to be accessed by both a real-time safety-critical task and a non-real-time monitoring task, where the safety-critical task must never be blocked by the monitoring task?

**Answer:** The core challenge is ensuring that the safety-critical path has guaranteed access to the hardware while the monitoring task can observe data without interfering. I'd design this with a clear separation of concerns: the safety-critical task gets a dedicated, low-latency path, while the monitoring task gets a secondary, potentially slower path.

For the hardware access itself, I'd use a lock-free or priority-aware mechanism. If the device has separate registers or channels for different functions, I'd partition them so each task accesses its own registers — no shared state, no locking needed. If they must share the same register space, I'd use a `spin_lock` with a very short critical section (just the register read/write), and ensure the monitoring task never holds the lock while doing anything slow like copying to userspace.

For the data path, I'd give the safety-critical task a dedicated ring buffer that's written by the interrupt handler and read by the safety-critical task. This ring buffer would be lock-free — using read/write indices with memory barriers — so the monitoring task can't block it. The monitoring task would get its own copy of the data, perhaps via a separate, larger buffer that's updated less frequently, or by reading the same ring buffer in a non-destructive way.

In terms of scheduling, the safety-critical task would run as a high-priority kernel thread with `SCHED_FIFO`, or the driver would expose a file descriptor that the safety-critical userspace task opens with real-time priority. The monitoring task would run at normal priority. I'd also ensure that the driver's interrupt handler does minimal work — just copying data to the ring buffer and waking the safety-critical task — so interrupt latency stays low.

I'd also consider using `mutex` vs `spinlock` carefully: the safety-critical path should never take a sleeping lock, because that could block on the monitoring task. If a sleeping lock is unavoidable, I'd use priority inheritance or a priority ceiling protocol to prevent priority inversion.

**Possible follow-ups:**
- How would you handle the case where the monitoring task needs to configure the device (e.g., change sampling rate) while the safety-critical task is actively using it?
- What debugging tools would you use to verify that the safety-critical task never misses its deadline under load?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during integration testing, you discover that the kernel's real-time scheduling class (SCHED_FIFO) is causing priority inversion on a shared hardware resource between your sensor driver and the display driver. The display team insists their driver needs the highest priority, and the sensor team says their data will be corrupted if they miss their deadline. How would you handle this situation?

**Answer:** I'd start by framing this as a technical problem to be solved with data, not a negotiation between teams. Priority inversion is a well-understood issue, and the solution isn't necessarily about who gets the higher priority — it's about eliminating the conditions that cause the inversion.

First, I'd call a meeting with both teams to understand the exact resource contention. I'd ask: what shared resource is involved? Is it a hardware register, a lock, a DMA channel, or something else? How long does each driver hold the resource? What are the actual deadlines and worst-case execution times? This information is critical — without it, any priority assignment is guesswork.

Once I understand the contention, I'd look at the standard solutions. If the inversion is caused by a lock, I'd consider: (1) using a priority inheritance mutex (`rt_mutex`), which is the standard kernel solution for priority inversion; (2) reducing the critical section so the lock is held for a very short time; (3) eliminating the shared lock entirely by partitioning the resource — for example, if both drivers access different registers of the same device, they might not need to share a lock at all.

If the resource is truly indivisible, I'd work with both teams to quantify the actual timing requirements. The sensor team's deadline might be 2 ms, but their actual worst-case execution time might be 500 µs — leaving plenty of margin. The display team might need high priority for perceived responsiveness, but their actual latency requirement might be much looser. With this data, we can make an informed decision about priority assignment.

I'd also consider whether the contention can be avoided architecturally. For example, could the sensor driver use DMA to move data without CPU involvement, reducing the time it needs the shared resource? Could the display driver batch its updates to reduce lock frequency?

Finally, I'd document the decision and the reasoning, and I'd add a stress test that exercises both drivers simultaneously to verify the fix works under worst-case conditions. This isn't about picking a winner — it's about ensuring the system meets its safety and performance requirements.

**Possible follow-ups:**
- What if the data shows that both drivers genuinely need the resource at the same time and neither can tolerate delay — what's your fallback plan?
- How would you communicate the resolution to the broader engineering team and to management, especially if it requires one team to change their design?