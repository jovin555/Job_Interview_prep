# embedded-linux-bsp — Day 50

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel log shows "Unhandled fault: external abort on non-linefetch" when a driver accesses a memory-mapped FPGA peripheral?

**Answer:** An external abort on non-linefetch typically indicates the CPU attempted a memory access that the bus fabric or the peripheral itself could not satisfy — the access never completed successfully at the hardware level. This is distinct from a page fault, which is a software/MMU issue. My first step would be to identify the exact address being accessed when the abort occurs, from the kernel log's fault register dump and the PC value at the time of the fault. I'd then check that address against the memory map: is it within the region assigned to the FPGA in the device tree? Is the region actually enabled in the SoC's address decode logic, or does it need a specific clock or power domain enabled first?

Next, I'd verify the FPGA is actually configured and running. If the FPGA bitstream loads late in boot or from userspace, a driver probing before configuration completes would hit a non-responsive bus. I'd also check whether the access size and alignment match what the FPGA's AXI/APB bridge expects — some FPGA interfaces only support 32-bit accesses, and a byte or half-word access can cause an abort. A logic analyzer or the FPGA's own debug interface can confirm whether the access ever reached the peripheral. I'd also check for a bus timeout: if the FPGA takes too long to respond (or never responds), the SoC's bus fabric may abort the transaction. This could be a clocking issue — the FPGA's interface clock not running, or running at the wrong frequency relative to the bus.

Finally, I'd review the driver's use of functions like `ioremap()` — if the physical address is correct but the mapping is wrong (e.g., mapping a 4 KB region but accessing beyond it), the access could fall outside the mapped window. The systematic approach is: confirm the address is valid and enabled, confirm the FPGA is configured and clocked, confirm the access type is supported, and then use hardware debug tools to see whether the transaction physically reaches the peripheral.

**Possible follow-ups:**
- How would you distinguish between an external abort caused by an invalid address versus one caused by a peripheral that's present but not responding?
- What device tree properties or kernel configuration options would you check to ensure the FPGA memory region is properly described?

---

## Q2: How would you approach designing a kernel driver for a device that needs to wake the system from suspend, but the device is on an I2C bus that loses power during suspend?

**Answer:** This is a classic power-domain problem. The key issue is that the wake-up source itself sits on a bus that's powered down during suspend, so the interrupt line from the device — which should wake the system — may not be valid, and even if it is, the system can't communicate with the device until the bus is powered back on.

First, I'd check whether the device's interrupt line is connected to a GPIO or interrupt controller that remains powered during suspend. If the interrupt controller stays alive, the device can still trigger a wake even if the I2C bus is down — the interrupt line is just a voltage level, not a bus transaction. The driver's suspend callback should configure the device (before power is cut) to enable its wake interrupt, and then enable the corresponding interrupt as a wake source using `enable_irq_wake()`. The key is to do all I2C communication *before* the bus loses power.

If the interrupt line also loses power or isn't wired to a wake-capable controller, I'd need a different approach: either keep the I2C bus powered (which defeats the purpose of suspending it), add a separate always-on GPIO that the device can assert as a wake signal, or use a different wake source entirely (e.g., a separate always-on sensor or a real-time clock alarm).

On resume, the driver must handle the fact that the I2C bus was powered down: the device may have lost its configuration, so the resume callback needs to re-initialize it. I'd also check whether the I2C controller itself needs re-initialization after power restoration — some controllers lose their clock configuration or need a bus reset. The driver should also handle the case where the device's state is unknown after resume — it may have missed events while the system was suspended, so a full re-sync of device state may be necessary.

**Possible follow-ups:**
- How would you verify that the wake interrupt actually fires during suspend, given that you can't easily debug while the system is asleep?
- What are the trade-offs between keeping the I2C bus powered versus powering it down and re-initializing on resume?

---

## Q3: How would you approach implementing a kernel driver for a device that uses DMA to transfer data from an FPGA to system memory, where the FPGA can generate data at rates exceeding what the CPU can process in real-time?

**Answer:** When the producer (FPGA) can outpace the consumer (CPU), the fundamental challenge is buffering and flow control. The driver can't just "keep up" — it needs a strategy to handle the rate mismatch gracefully. I'd start by characterizing the actual data rates: what's the FPGA's peak sustained throughput, what's the burst size, and what's the realistic processing rate on the CPU side? This determines whether the problem is occasional bursts that can be buffered, or a sustained rate that fundamentally exceeds CPU capacity.

For the DMA design itself, I'd use a ring buffer of DMA descriptors in memory, each pointing to a fixed-size buffer. The FPGA writes into these buffers, and the driver processes them in order. The key is having enough descriptors queued to absorb bursts — the depth depends on the worst-case latency of the CPU's processing path (interrupt latency, scheduling delay, actual processing time). I'd also consider using double-buffering or a multi-descriptor ring so the FPGA always has a buffer available while the CPU processes the previous one.

If the sustained rate genuinely exceeds what the CPU can process, the driver needs a policy: drop data (with a counter so userspace knows data was lost), or implement a backpressure mechanism where the FPGA pauses when buffers are full. In a medical device context, dropping data is usually unacceptable, so backpressure or rate-limiting at the source is preferred. I'd also consider whether some processing can be offloaded — e.g., the FPGA can do simple filtering or decimation before DMA, reducing the data rate to something the CPU can handle.

For the interrupt strategy, I'd use either DMA completion interrupts (one per buffer) or a combination of interrupts and polling, depending on the expected interrupt rate. If interrupts would arrive too frequently, I'd consider using a high-resolution timer to drain the ring buffer in batches, trading latency for CPU efficiency. The driver should also expose statistics — bytes transferred, overruns, dropped buffers — so the system can detect if the CPU is falling behind and alert userspace.

**Possible follow-ups:**
- How would you decide between interrupt-driven DMA completion and polling the DMA status register?
- What happens when the ring buffer is full — how does the driver handle the FPGA continuing to write?

---

## Q4: How would you approach debugging a kernel panic that occurs only on every third or fourth boot, with no consistent trigger?

**Answer:** Intermittent panics with no consistent trigger are among the hardest debugging problems because the usual approach — reproduce reliably, then bisect — doesn't work directly. I'd start by treating it as a statistics problem: gather as much data as possible from each failure. I'd enable `CONFIG_PANIC_ON_OOPS`, `CONFIG_DEBUG_INFO`, and `CONFIG_KALLSYMS` to get the most informative panic output, and I'd capture the full console log from each failure — not just the panic message but everything leading up to it. Often the "inconsistent" panic has a pattern that only emerges over multiple observations: maybe it correlates with a specific driver probe order, a particular memory allocation pattern, or a timing window.

I'd look at whether the panic is in the same location each time or varies. If it's the same location, it's likely a race condition or a use-after-free that manifests under specific timing. If it varies, it could be memory corruption — a wild pointer, buffer overflow, or bad DMA that corrupts random kernel structures. For memory corruption, I'd enable `CONFIG_DEBUG_PAGEALLOC`, `CONFIG_SLUB_DEBUG`, and KASAN if the architecture supports it. These tools can catch out-of-bounds accesses and use-after-free at the point of corruption rather than at the point of the panic.

I'd also check for hardware causes: marginal timing on a memory bus, a loose connector, or a power supply issue that only manifests under certain temperature or load conditions. Running memtest86+ or the kernel's own memory self-test can rule out DRAM issues. I'd also check the kernel log for earlier warnings — MCE errors, DMA errors, or I2C/SPI timeouts — that might indicate a failing component.

If the panic is timing-dependent, I'd try to correlate it with system activity: does it happen during boot, during a specific workload, or at idle? I'd instrument the system with ftrace or tracepoints to capture what was happening in the moments before the panic. Finally, I'd consider whether the panic is actually in the kernel or if it's a hardware reset that *looks* like a panic — a watchdog reset or voltage drop can produce similar symptoms.

**Possible follow-ups:**
- How would you use the kernel's `pstore` or crash dump mechanisms to capture information from a panic that happens during boot, before the root filesystem is available?
- What kernel configuration options would you enable to maximize the diagnostic value of each panic?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during integration testing, you discover that the kernel's real-time scheduling class (SCHED_FIFO) is causing priority inversion on a shared hardware resource between your sensor driver and the display driver. The display team insists their driver needs the highest priority, and the sensor team says their data will be corrupted if they miss their deadline. How would you handle this situation?

**Answer:** Priority inversion on a shared resource is a classic real-time systems problem, and the first thing I'd do is step back from the "my priority is higher" argument and focus on the actual requirements. Both teams are defending their positions based on assumptions, but the real question is: what are the actual timing requirements for each driver, and what's the actual worst-case blocking time on the shared resource?

I'd start by calling a meeting with both teams to establish the facts. I'd ask the display team to quantify their worst-case acceptable latency and the sensor team to quantify their deadline and the consequence of missing it. In a medical device, the sensor data is likely safety-relevant, so missing a deadline might mean corrupted patient data — that's a patient safety issue. The display, by contrast, might have a latency requirement for user feedback, but a few milliseconds of delay is probably acceptable. This isn't about whose driver is "more important" — it's about which deadline is harder and what the consequences of missing each are.

Once we have the requirements on the table, I'd look at the technical options. The cleanest fix is usually to eliminate the shared resource contention rather than arbitrate it. Can the sensor driver use a different hardware path — a dedicated DMA channel, a different bus, or a private memory region? Can the display driver's access be restructured to hold the lock for less time, or use a non-blocking approach? If the resource genuinely must be shared, I'd look at priority inheritance or priority ceiling protocols — the kernel supports `PRIO_INHERIT` for mutexes, which would let the lower-priority display driver inherit the sensor driver's priority while holding the lock, preventing the sensor from being blocked indefinitely.

I'd also question whether SCHED_FIFO is even the right tool for both drivers. Maybe the display driver doesn't need real-time priority at all — perhaps it can run as a regular SCHED_OTHER task with a high nice value, leaving the real-time class for the sensor driver. This is a design question, not a political one. My role as BSP lead is to facilitate the technical discussion, ensure the requirements are documented, and drive the team toward a solution that meets the system's actual needs — not to referee a priority war.

**Possible follow-ups:**
- How would you document the resolution in the project's design history file (DHF) for regulatory purposes?
- What if the sensor team's deadline is genuinely tight and the display team's latency requirement is also hard — how would you approach the trade-off?