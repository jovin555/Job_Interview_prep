# embedded-linux-bsp — Day 31

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel log shows "Unhandled fault: external abort on non-linefetch" when a driver accesses a memory-mapped FPGA peripheral?

**Answer:** An external abort on non-linefetch typically indicates the CPU attempted a memory access that the bus fabric or peripheral did not acknowledge — essentially a bus error. My first step would be to identify the exact address and access size from the kernel log, then map that address back to the memory map to confirm which peripheral region it belongs to. Common causes include: the peripheral clock being gated off, the memory region not being properly enabled in the memory controller or firewall registers, the FPGA not being programmed/configured at the time of access, or a mismatch between the physical address in the device tree and the actual address decoded by the FPGA.

I would start by checking whether the FPGA is actually programmed and its configuration done pin is asserted. Next, I'd verify the device tree memory region — is it marked as `reg = <...>` with the correct size, and does it fall within a range that the SoC's chip-select or memory controller is configured to decode? I'd also check whether the driver is using `ioremap()` correctly and whether the access size matches what the FPGA expects (e.g., a 32-bit read to a register that only supports 16-bit accesses can cause issues on some buses). Using a logic analyzer or the SoC's bus debug registers can help confirm whether the access is reaching the FPGA at all. If the abort happens during probe, I'd also check probe ordering — is the FPGA's firmware loaded before the driver attempts access? In a system with multiple peripherals, I'd also verify that no other driver has claimed the same memory region or that a firewall/TrustZone setting isn't blocking access.

**Possible follow-ups:** How would you distinguish between an external abort caused by a hardware fault versus a software bug in the driver? What tools would you use to trace the exact instruction causing the abort?

---

## Q2: How would you approach designing a kernel driver for a device that needs to log sensor data to a file on the root filesystem at a fixed rate (e.g., 100 Hz) without causing filesystem corruption on unexpected power loss?

**Answer:** Writing to a filesystem at 100 Hz from kernel space is generally the wrong architecture. Filesystem writes involve significant overhead, journaling, and caching behavior that can introduce latency and unpredictability — and a crash during a write can corrupt the filesystem. The standard approach is to have the kernel driver collect data into a ring buffer and expose it to userspace via a character device, `debugfs`, or a netlink socket. A userspace daemon then handles the actual file I/O at a rate it can manage, with appropriate buffering.

For power-loss safety, the key considerations are: use a filesystem designed for embedded use (e.g., ext4 with journaling, or a log-structured filesystem like UBIFS for raw NAND), mount with appropriate options (`sync` or `data=ordered` for ext4), and structure the logging so that a crash mid-write doesn't corrupt previously written data. Writing to a temporary file and atomically renaming it into place is a common pattern. Alternatively, if the data must survive power loss with minimal loss, consider writing to a dedicated partition or using a small battery-backed RAM buffer. For medical devices, the logging design should also consider the regulatory requirement for data integrity — the design should be documented and validated for the failure modes.

In the kernel driver itself, I'd use a high-resolution timer or hrtimer to sample at 100 Hz, store samples in a lock-free ring buffer (with appropriate memory barriers), and wake a userspace reader via `poll()` or `read()` blocking semantics. The userspace daemon would then batch writes — for example, accumulating 1 second of data and writing it in one operation — to reduce filesystem overhead and improve crash consistency.

**Possible follow-ups:** How would you handle the case where the userspace daemon crashes or is killed — how would the driver detect this and respond? What filesystem and mount options would you choose for a medical device that must survive unexpected power loss?

---

## Q3: How would you approach implementing a kernel driver for a device that uses DMA to transfer data from an FPGA to system memory, where the FPGA can generate data at rates exceeding what the CPU can process in real-time?

**Answer:** When the data rate exceeds CPU processing capability, the key is to avoid involving the CPU in the data path entirely. The architecture should be: FPGA writes data to system memory via DMA (either using the SoC's DMA controller with the FPGA as a slave, or the FPGA acting as a bus master), and the CPU only handles metadata — interrupts, buffer management, and occasional error handling.

The design would use a double-buffering or multi-buffer ring approach. The FPGA writes into one buffer while the CPU processes the other, then they swap. The DMA completion interrupt signals the driver to hand the filled buffer to userspace (via `mmap()` for zero-copy access) and return the empty buffer to the FPGA. The number of buffers depends on the data rate and processing time — you need enough buffers to cover the worst-case processing latency.

For the driver itself, I'd use the DMA engine API (`dma_request_chan()`, `dmaengine_prep_dma_cyclic()` or `dmaengine_prep_dma_async()` for scatter-gather). The FPGA would be configured to write to a fixed set of physical addresses, which the driver would allocate as DMA-capable memory (coherent or streaming, depending on cache coherency requirements). If the FPGA is a bus master, the driver needs to set up the buffer addresses in FPGA registers and handle the case where the FPGA writes out of bounds — using an IOMMU if available, or at minimum validating buffer indices on each interrupt.

If the CPU genuinely cannot keep up even with zero-copy, the design needs to change: either reduce the data rate (e.g., decimation in the FPGA), increase buffering (accepting higher latency), or offload processing to a dedicated DSP or hardware accelerator. The driver should also implement flow control — if all buffers are full, the FPGA should be told to drop data or pause, and the driver should track and report dropped samples to userspace.

**Possible follow-ups:** How would you handle cache coherency between the DMA writes and CPU reads? What if the FPGA can write to arbitrary addresses due to a bug — how would you protect the system?

---

## Q4: How would you approach debugging a kernel panic that occurs only on every third or fourth boot, with no consistent trigger?

**Answer:** Intermittent boot failures are among the most challenging to debug because they're often timing-dependent or related to hardware initialization races. My approach would be systematic:

First, I'd gather as much data as possible from each failure. Enable `CONFIG_PANIC_ON_OOPS`, `CONFIG_DEBUG_INFO`, and `CONFIG_KALLSYMS` to get a usable stack trace. Use a serial console with a high baud rate and capture the full log — ideally with a hardware serial logger that timestamps each line. If the panic message is consistent (same instruction, same call trace), that narrows it down significantly. If it varies, that suggests a more fundamental timing or memory issue.

Next, I'd look for common intermittent causes: DRAM initialization timing (especially if the memory controller settings are marginal), power supply ramp-up issues (a regulator that's slightly slow to stabilize), clock initialization races, or a device that occasionally fails to respond during probe (e.g., an I2C device that needs more time after reset). I'd check the boot log for any warnings or errors that appear in the failing boots but not successful ones — often the panic is a symptom of an earlier, subtler issue.

I'd also try to reproduce with variations: add `initcall_debug` to see which initcall is running when it fails, try different memory speeds or timing parameters, add delays in the bootloader before starting the kernel, or use `memtest` to check for marginal DRAM. If the failure correlates with temperature or time since power-on, that points to a hardware issue. Using a logic analyzer on the memory bus or checking the SoC's error registers can reveal ECC errors or bus timeouts.

If the panic is in a driver probe, I'd check whether the driver handles deferred probe correctly — a device that isn't ready when first probed should return `-EPROBE_DEFER` rather than crashing. I'd also verify that the driver's reset sequence is robust: does it wait long enough for the device to be ready? Is there a race between interrupt registration and device initialization?

Finally, I'd consider using `kexec` to capture a crash dump, or adding a watchdog that reboots the system and logs the previous boot's panic message to a persistent store (e.g., pstore/ramoops) so you can see the panic from the failed boot after the reboot.

**Possible follow-ups:** How would you use `pstore/ramoops` to capture panic logs across reboots? What hardware-level checks would you perform to rule out marginal DRAM or power supply issues?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during integration testing, you discover that the kernel's real-time scheduling class (SCHED_FIFO) is causing priority inversion on a shared hardware resource between your sensor driver and the display driver. The display team insists their driver needs the highest priority, and the sensor team says their data will be corrupted if they miss their deadline. How would you handle this situation?

**Answer:** Priority inversion on a shared resource is a classic real-time systems problem, and the first thing I'd do is step back from the "who gets the higher priority" argument and focus on understanding the actual resource contention. I'd call a meeting with both teams and ask them to walk me through the specific scenario: what resource is shared, what are the access patterns, what are the actual deadlines, and what happens when each driver misses its deadline. Often the real issue isn't the priority assignment itself but the design of the resource access — for example, if both drivers are using a spinlock or mutex that serializes access, the problem is the locking strategy, not the priorities.

I'd then look at the technical options: (1) Can the shared resource be partitioned or duplicated so each driver has its own instance? (2) Can the access be made non-blocking — e.g., using a lock-free algorithm or a hardware FIFO? (3) Can the sensor driver use a higher-priority thread that only briefly accesses the resource, while the bulk of its work happens without the lock? (4) Can we use priority inheritance (via `rt_mutex` or `mutex` with `CONFIG_RT_MUTEXES`) so that the lower-priority task holding the lock temporarily inherits the higher priority? (5) Can the display driver's work be deferred or split so it doesn't hold the resource for long periods?

I'd also challenge both teams on their actual requirements. The sensor team's "data will be corrupted" claim needs quantification — is it a hard real-time deadline (missing it causes patient harm) or a soft deadline (missing it causes degraded quality)? The display team's "needs highest priority" claim needs justification — what happens if a frame is delayed by a few milliseconds? In a medical device, the safety-critical sensor data should generally take precedence, but that's a decision that should be based on the risk analysis, not on which team argues louder.

My approach would be to facilitate a technical discussion where we agree on the actual constraints, then evaluate options against those constraints. If we can't resolve it technically, I'd escalate to the systems engineer or project manager with a clear recommendation based on the risk assessment — but I'd first exhaust the technical options, because there's almost always a design change that eliminates the contention entirely. I'd also document the decision and the rationale in the design history file, since this is exactly the kind of trade-off that regulatory auditors will want to see justified.

**Possible follow-ups:** How would you quantify and compare the risks of missing each driver's deadline in a medical device context? What if the two teams refuse to compromise — how would you escalate while keeping the project on track?