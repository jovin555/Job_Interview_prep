# embedded-linux-bsp — Day 45

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel log shows "Failed to request IRQ" for a device that worked on the previous board revision?
**Answer:** I'd start by checking whether the interrupt line is actually being asserted and whether the controller is configured correctly. The most common cause when a device worked on a previous revision is a hardware change — the IRQ line may have been moved to a different GPIO bank, or the interrupt controller's interrupt-map in the device tree no longer matches the physical connection. I'd first verify the device tree: confirm the `interrupts` property references the correct controller, GPIO bank, and interrupt type (level vs. edge, active-high vs. active-low). A mismatch between the device tree's expectation and the actual hardware behavior is a classic source of this failure.

Next, I'd check whether the IRQ is already claimed by another driver. If the previous board revision had a different peripheral set, another device may now be probing first and grabbing the same interrupt line. I'd look at `/proc/interrupts` to see what's registered, and check the kernel log for any other driver that mentions the same IRQ number. I'd also verify the GPIO controller itself is properly initialized — if the GPIO bank's clock is gated or the pinctrl settings aren't applied, the interrupt won't be routable even if the device tree looks correct.

I'd also check the interrupt type flags. If the previous board used a level-triggered interrupt and the new revision has a different pull configuration or the sensor's interrupt output is now open-drain, the driver may request the wrong trigger type. Using `devm_request_irq` with the wrong flags can cause the interrupt to fire continuously or never at all. I'd use a logic analyzer or oscilloscope to confirm the actual signal behavior on the IRQ line during operation.

Finally, I'd compare the working and non-working configurations systematically — diff the device tree files, check for any changes in the interrupt controller driver or GPIO driver between kernel versions, and verify the SoC's interrupt multiplexing settings. If the hardware team made a change, I'd ask for the schematic diff to confirm the IRQ routing.

**Possible follow-ups:**
- How would you determine whether the problem is in the device tree, the driver, or the hardware itself?
- What if the IRQ is shared between two devices — how would you debug a spurious interrupt issue in that case?

---

## Q2: How would you approach designing a kernel driver for a device that needs to wake the system from suspend, but the device is on an I2C bus that loses power during suspend?
**Answer:** This is a common challenge in low-power embedded systems — the wake-up source sits on a bus that's powered down to save energy. The key is to separate the wake-up mechanism from the communication path. The device itself needs a dedicated wake-up line — typically a GPIO that can be configured as a wake-up interrupt source — that remains powered and connected to a wake-capable interrupt controller pin. The I2C bus itself can be powered down, but the wake GPIO must be on a always-on power domain.

In the driver, I'd implement the suspend callback to disable the I2C communication path but leave the interrupt enabled as a wake source. This means using `enable_irq_wake()` on the GPIO interrupt so the system can wake from suspend when the device asserts the line. The driver's resume callback would then reinitialize the I2C bus (since it lost power), reconfigure the device's registers, and re-establish communication.

There's a subtlety here: if the I2C controller itself is powered down, the driver must not attempt any I2C transactions during the suspend path after the bus is already off. The suspend sequence needs to be ordered carefully — the driver should complete any necessary I2C writes to put the device into its low-power state *before* the bus is powered down, then only configure the wake GPIO afterward.

I'd also consider whether the device needs to be accessed during the resume path before the I2C bus is fully reinitialized. If the bus controller has its own resume ordering constraints, the driver may need to defer the first I2C transaction until the bus is ready — possibly using a deferred probe mechanism or a workqueue that runs after the bus driver's resume completes.

For the device tree, I'd model the wake GPIO as a separate interrupt resource, distinct from any I2C interrupt the device might use during normal operation. This makes it clear that the wake path is independent of the bus. I'd also verify that the GPIO controller used for the wake line is in an always-on power domain — if it's not, the wake will never fire.

**Possible follow-ups:**
- How would you handle the case where the device needs to wake the system but also needs to communicate immediately after wake — how do you ensure the I2C bus is ready?
- What if the wake GPIO is also used for normal data-ready interrupts during active operation — how would you manage the dual role?

---

## Q3: How would you approach implementing a kernel driver for a device that uses DMA to transfer data from an FPGA to system memory, where the FPGA can generate data at rates exceeding what the CPU can process in real-time?
**Answer:** When the data rate exceeds what the CPU can handle, the design has to shift from interrupt-driven per-transfer processing to a buffered, DMA-centric architecture. The key is to decouple the DMA transfer rate from the CPU consumption rate using a ring buffer in system memory, with careful attention to flow control and backpressure.

I'd start by designing the DMA descriptor ring. The FPGA writes data into a set of pre-allocated DMA buffers, and the driver maintains a ring of descriptors that the DMA engine cycles through. The FPGA can be configured to write continuously into these buffers, wrapping around when it reaches the end. The driver's job is to keep ahead of the FPGA — processing completed buffers before the FPGA wraps around and overwrites them.

The critical design decision is how the driver learns that a buffer is full. Rather than interrupting the CPU for every buffer (which would overwhelm it at high data rates), I'd consider interrupt coalescing or a polling approach. The DMA controller may support interrupt moderation — interrupting after N transfers or after a time threshold. Alternatively, the FPGA can update a head pointer in shared memory that the driver polls at a controlled rate. This trades latency for CPU efficiency.

For flow control, the driver needs a mechanism to tell the FPGA to pause when the CPU is falling behind. This could be a register write to the FPGA, a dedicated backpressure signal, or simply letting the FPGA overwrite old data if the application can tolerate data loss (with a flag indicating dropped data). In a medical device context, data loss is usually unacceptable, so I'd implement a proper flow-control mechanism — the FPGA checks whether the next buffer is free before writing, and if not, it asserts an overflow condition that the driver can detect and report.

In terms of the DMA engine API, I'd use the kernel's DMA engine framework with `dma_map_single` or `dma_alloc_coherent` for the buffers, ensuring cache coherency is handled correctly. For high-throughput scenarios, I'd also consider using the `dmaengine_prep_dma_cyclic` API if the DMA controller supports cyclic transfers — this is ideal for continuous data streams where the same buffers are reused in a loop.

Finally, I'd think about how data gets to userspace. If the application needs the data, I'd use a character device with `read()` semantics backed by the ring buffer, or use `mmap()` to give the application direct access to the DMA buffers with a synchronization mechanism (like a poll or a sequence counter). The `mmap` approach avoids a copy and can handle very high data rates, but requires careful synchronization between kernel and userspace.

**Possible follow-ups:**
- How would you handle cache coherency between the DMA writes and CPU reads?
- What if the FPGA can generate data bursts that exceed the total available DMA buffer memory — how would you design the flow control?

---

## Q4: How would you approach debugging a kernel panic that occurs only on every third or fourth boot, with no consistent trigger?
**Answer:** Intermittent kernel panics with no consistent trigger are among the most challenging debugging scenarios because the usual approach — reproduce reliably, then bisect — doesn't work well. I'd approach this systematically, starting with the assumption that there's an underlying race condition or hardware timing issue that manifests probabilistically.

First, I'd maximize the information captured from each panic. I'd enable `CONFIG_PANIC_ON_OOPS`, ensure `CONFIG_DEBUG_INFO` is set, and configure `pstore` or a crash dump mechanism so the panic log survives the reboot. If the board has a hardware watchdog, I'd disable it during debugging so the system stays in the panic state for inspection. I'd also add a serial console with a high baud rate and capture the full log — the key is to get the *complete* stack trace and register dump, not just the last few lines.

Next, I'd look for patterns across multiple occurrences. Even if the panic seems random, there may be a correlation — the same function appears in the stack trace, or the panic happens at the same point in the boot sequence, or it correlates with a specific hardware event (like a particular peripheral being initialized). I'd collect logs from 10-20 panics and compare them. If the same code path appears repeatedly, that's my starting point.

I'd also consider timing-related causes. Intermittent panics on boot often stem from races between driver probes — two drivers initializing concurrently and accessing shared hardware without proper locking, or a driver accessing a peripheral before its clock is enabled. I'd look for any driver that doesn't properly handle deferred probe, or any shared resource (GPIO, clock, regulator) that's requested by multiple drivers without proper synchronization.

Memory corruption is another strong candidate. I'd enable `CONFIG_DEBUG_PAGEALLOC`, `CONFIG_DEBUG_OBJECTS`, and `CONFIG_KASAN` if the architecture supports it. These tools can catch out-of-bounds writes, use-after-free, and other memory bugs that might only manifest when the memory layout happens to be unfavorable. I'd also check for stack overflow — enabling `CONFIG_DEBUG_STACKOVERFLOW` and checking the stack size in the panic log.

Hardware timing issues are also possible — a power rail that ramps slightly differently on some boots, or a reset that doesn't fully complete. I'd check whether the panic correlates with cold boots vs. warm reboots, and whether adding a delay in the bootloader (to let power stabilize) changes the frequency. I'd also verify the memory controller configuration — if the DDR training is marginal, memory errors could cause random panics.

Finally, I'd use a bisection strategy, but with a twist. Instead of bisecting on the code, I'd bisect on *configuration* — disabling drivers one at a time, or changing the probe order, to see if the panic frequency changes. If disabling a particular driver eliminates the panic, I've found my culprit.

**Possible follow-ups:**
- How would you distinguish between a software race condition and a hardware timing issue?
- What kernel configuration options would you enable to maximize the diagnostic information from each panic?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during integration testing, you discover that the kernel's real-time scheduling class (SCHED_FIFO) is causing priority inversion on a shared hardware resource between your sensor driver and the display driver. The display team insists their driver needs the highest priority, and the sensor team says their data will be corrupted if they miss their deadline. How would you handle this situation?
**Answer:** Priority inversion on a shared resource is a classic real-time systems problem, and the first thing I'd do is step back from the "who gets the highest priority" argument and reframe the discussion around the actual requirement: what are the real-time constraints for each driver, and what's the worst-case impact of missing them?

I'd start by calling a meeting with both teams and asking them to quantify their requirements. For the sensor driver: what's the actual deadline — the time between data being ready and it being read? What happens if that deadline is missed — is data corrupted, or just delayed? For the display driver: what's the consequence of a delayed frame — a visual glitch, or something more serious? In a medical device, the sensor data likely has patient-safety implications, while the display might have usability implications. That doesn't automatically mean the sensor wins — a display that freezes could also cause problems if clinicians can't see critical information — but it gives us a basis for a rational decision rather than a priority war.

Once we have the actual constraints, I'd look at whether the shared resource contention can be eliminated entirely. The classic solution to priority inversion is to remove the sharing. Can the sensor driver use a different hardware path — a dedicated DMA channel, a separate I2C controller, or a different memory region? If the resource is a hardware register or a lock protecting a shared data structure, can we use a lock-free design — for example, a ring buffer with careful memory barriers, where the sensor driver writes and the display driver reads without holding a common lock?

If the sharing can't be eliminated, I'd look at the priority inheritance mechanisms. The kernel's RT mutexes (`CONFIG_RT_MUTEXES`) implement priority inheritance — if the display driver (high priority) blocks on a lock held by the sensor driver (lower priority), the sensor driver temporarily inherits the display driver's priority, so it can't be preempted by medium-priority tasks. This prevents the unbounded blocking that characterizes classic priority inversion. I'd check whether the drivers are using plain spinlocks or mutexes — if they're using spinlocks in a context where RT mutexes would work, that's a change worth making.

I'd also question whether both drivers genuinely need SCHED_FIFO. Often, only the time-critical portion of the driver needs real-time priority — the interrupt handler or a small kernel thread — while the bulk of the work can run at normal priority. I'd work with each team to identify the minimal critical section that needs real-time guarantees and see if those sections actually contend with each other.

If we genuinely have two hard real-time tasks sharing a resource and neither can yield, I'd escalate to the systems engineering team to review the architecture. This might mean changing the hardware design (separating the resources), changing the scheduling model (using a different core for one driver), or revisiting the actual deadlines to see if they can be relaxed. In a medical device context, this would also trigger a risk assessment — we'd need to document the failure mode and ensure the system handles it safely.

The key leadership point is that I wouldn't let this become a team-vs-team priority battle. I'd facilitate a data-driven discussion, look for architectural solutions first, and only escalate to a scheduling compromise if no better option exists.

**Possible follow-ups:**
- How would you determine whether the sensor driver's deadline is actually a hard real-time requirement or just a performance preference?
- What if the two drivers genuinely cannot share the resource without contention, and both have hard real-time requirements — what architectural changes would you propose?