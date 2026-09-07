# embedded-linux-bsp — Day 48

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel log shows "Failed to request IRQ" for a device that worked on the previous board revision?

**Answer:** I'd approach this systematically, starting with the assumption that the interrupt controller configuration or the device's interrupt wiring has changed between revisions. First, I'd verify the device tree interrupt properties match the new hardware — checking the interrupt parent, the interrupt number, and the trigger type (level vs. edge, high vs. low). A common issue is that a GPIO line used for the interrupt was moved to a different bank or controller on the new revision, but the device tree still references the old one.

Next, I'd check whether the interrupt is actually being requested by another driver first. If two devices claim the same interrupt line, the second request will fail. This can happen if a new device was added to the board and its driver claims the shared line, or if the interrupt controller's domain mapping changed. I'd look at `/proc/interrupts` to see which interrupts are already claimed and compare against the device tree.

I'd also examine the interrupt controller driver itself — on some SoCs, the interrupt controller needs to be properly initialized before peripheral drivers request interrupts. If the controller probe order changed, or if a new controller node was added to the device tree, the timing of when the controller becomes available could affect whether the request succeeds.

Finally, I'd check the hardware itself. If the interrupt line is floating or improperly pulled, the interrupt controller might see spurious interrupts and mask the line, causing subsequent request attempts to fail. A scope or logic analyzer on the interrupt line during boot would confirm whether the line is behaving as expected.

**Possible follow-ups:**
- How would you distinguish between a device tree configuration error and a driver-level bug in this scenario?
- What if the interrupt is requested successfully but never fires — how would your debugging approach differ?

---

## Q2: How would you approach designing a kernel driver for a device that needs to wake the system from suspend, but the device is on an I2C bus that loses power during suspend?

**Answer:** This is a classic power-domain problem. The key constraint is that the wake-up source must remain powered and functional during suspend, even though the I2C bus it sits on does not. I'd start by examining the hardware architecture to understand the power domains — specifically, whether the wake-capable device has its own always-on power rail, or whether it shares the rail with the I2C controller.

If the device has independent power, the driver needs to be structured so that the interrupt line from the device is routed to a wake-capable interrupt controller pin (e.g., a GPIO that can wake the SoC from suspend). The driver would register the interrupt as a wake-up source using `enable_irq_wake()` during suspend, and disable it on resume. The I2C communication itself would only happen after resume, when the bus is powered back on.

If the device does not have independent power, then the hardware design itself is problematic — the device can't wake the system if it's powered down. In that case, I'd work with the hardware team to understand whether there's a separate always-on rail available, or whether a different device on a different bus should handle wake-up. If the hardware can't be changed, an alternative is to use a separate always-on GPIO or a PMIC's interrupt as the wake source, and then power up the I2C bus and re-initialize the device after resume.

The driver also needs to handle the resume path carefully. After the bus is powered back on, the device will need re-initialization — its register state will be lost. The driver's resume callback should restore the device to its pre-suspend state, including any configuration registers, and then re-establish communication. I'd also make sure the driver handles the case where the device was the wake source — it should read the device's status register to clear the wake event and determine why the system woke.

**Possible follow-ups:**
- How would you handle the case where the device needs to be accessed during the suspend path itself, after the I2C bus has already been suspended?
- What power management callbacks would you implement, and in what order would they be called relative to the bus driver's callbacks?

---

## Q3: How would you approach implementing a kernel driver for a device that uses DMA to transfer data from an FPGA to system memory, where the FPGA can generate data at rates exceeding what the CPU can process in real-time?

**Answer:** When the data rate exceeds what the CPU can handle in real-time, the fundamental strategy is to decouple data acquisition from data processing. The DMA engine should be moving data into system memory continuously, while the CPU processes data at its own pace — but the system must handle the case where the CPU falls behind.

I'd start by understanding the data rate and the buffer requirements. The DMA should be configured to use a ring buffer or a set of linked descriptors in system memory, so that the FPGA can keep writing data without CPU intervention between transfers. The key design question is how large the buffer needs to be to absorb bursts of data while the CPU is busy with other tasks.

For the DMA engine, I'd use the kernel's DMA engine API or the SoC's DMA driver, configuring it for cyclic or scatter-gather operation. With a cyclic DMA, the hardware continuously writes to a fixed buffer and wraps around — the driver just needs to track the current position. With scatter-gather, the DMA controller chains multiple descriptors, and the driver adds new buffers to the chain as it consumes data.

The critical part is flow control. If the CPU can't keep up, the buffer will eventually overflow. The driver needs to detect this condition — either by checking the DMA controller's position register against the last processed position, or by using interrupts when the DMA reaches certain watermark levels. When overflow is detected, the driver should drop data gracefully and report the condition to userspace, rather than corrupting the buffer or crashing.

For the userspace interface, I'd consider using a character device with `read()` semantics, or possibly `mmap()` for zero-copy access if the application can handle raw buffer access. If the data needs to be timestamped or correlated with other events, I'd include metadata in the buffer structure. The driver should also implement proper `poll()` support so userspace can block efficiently rather than busy-polling.

If the CPU genuinely cannot keep up even with an optimal driver, then the architecture needs to change — for example, preprocessing in the FPGA, or using a dedicated DMA channel to move data to storage without CPU involvement.

**Possible follow-ups:**
- How would you decide between a ring buffer approach and a linked-list descriptor approach for this scenario?
- How would you handle the case where the FPGA produces data in variable-sized bursts rather than a steady stream?

---

## Q4: How would you approach debugging a kernel panic that occurs only on every third or fourth boot, with no consistent trigger?

**Answer:** Intermittent kernel panics with no consistent trigger are among the most challenging debugging scenarios because the usual approach of reproducing the issue reliably doesn't work. I'd start by maximizing the information available from each occurrence. First, I'd ensure that `CONFIG_PANIC_ON_OOPS` is set and that the kernel is configured to capture a full crash dump — either through `kexec` with a crash kernel, or at minimum by enabling `CONFIG_DEBUG_INFO` and `CONFIG_KALLSYMS` so the stack trace is meaningful. I'd also enable `CONFIG_DEBUG_PAGEALLOC`, `CONFIG_SLUB_DEBUG`, and `CONFIG_DEBUG_OBJECTS` to catch memory corruption earlier.

Next, I'd look for patterns across the crashes. Even if the trigger seems random, the stack traces might share a common function or subsystem. I'd collect the panic logs from multiple occurrences and compare them — if the same code path appears repeatedly, that narrows the search significantly. I'd also check whether the panics correlate with specific hardware events, such as DMA activity, interrupt load, or power state transitions.

A common cause of intermittent panics is a race condition — for example, a driver accessing hardware before it's fully initialized, or two drivers accessing the same resource without proper locking. I'd review recent changes to the BSP, particularly any driver that was modified or added. I'd also look for timing-dependent issues, such as a driver that assumes a certain initialization order but can be probed in different orders depending on device tree enumeration.

If the panic appears to be memory-related, I'd suspect a buffer overflow or use-after-free that only manifests when memory layout happens to place data in a particular way. Running the system under stress — heavy memory allocation, frequent driver load/unload cycles, or extended soak testing — might make the panic more reproducible. I'd also try booting with different memory configurations (e.g., `mem=512M` to reduce available memory) to see if that changes the frequency.

Finally, if the panic is truly random and defies analysis, I'd consider using a hardware watchdog to automatically reboot the system and capture the panic log to persistent storage, so that each occurrence adds data to the investigation rather than requiring manual intervention.

**Possible follow-ups:**
- How would you use `ftrace` or `kprobes` to narrow down an intermittent issue like this?
- What role would hardware — such as marginal power supply or signal integrity issues — play in your investigation, and how would you rule it in or out?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during integration testing, you discover that the kernel's real-time scheduling class (SCHED_FIFO) is causing priority inversion on a shared hardware resource between your sensor driver and the display driver. The display team insists their driver needs the highest priority, and the sensor team says their data will be corrupted if they miss their deadline. How would you handle this situation?

**Answer:** Priority inversion on a shared resource is a classic real-time systems problem, and the first step is to move from positional negotiation to technical analysis. Rather than debating which team "wins," I'd call a meeting with both teams and frame the discussion around the actual scheduling requirements and the nature of the shared resource.

I'd start by asking both teams to quantify their constraints. For the sensor driver: what is the worst-case deadline, what happens if it's missed — is data corrupted, or just delayed? For the display driver: what is the actual worst-case execution time for its critical section, and how often does it need to run? Often, teams have worst-case estimates that are far more conservative than reality, and the actual numbers reveal that the conflict is smaller than perceived.

Next, I'd examine the shared resource itself. If it's a hardware register or a bus that both drivers access, the real question is whether the critical sections can be made shorter, or whether the resource can be accessed without holding a lock for the entire operation. For example, if the display driver holds a lock while waiting for a slow hardware operation, the sensor driver will be blocked regardless of priority. The fix might be to restructure the display driver to release the lock during the wait, or to use a different synchronization mechanism.

If the conflict is genuine and both deadlines are real, I'd look at the scheduling configuration. Priority inheritance (via `rt_mutex`) can solve the classic priority inversion problem — the lower-priority display driver temporarily inherits the sensor driver's priority while holding the shared lock, so it can't be preempted by medium-priority tasks. I'd also check whether the two drivers actually need to be SCHED_FIFO at all, or whether one could use SCHED_DEADLINE or a lower priority with proper rate limiting.

I'd also consider whether the shared resource can be partitioned — for example, if the conflict is on a bus, can the sensor use a different bus or a dedicated DMA channel? If the hardware allows it, eliminating the sharing entirely is the cleanest solution.

Finally, I'd document the analysis and the decision. In a medical device context, this kind of scheduling decision needs to be traceable — the rationale, the worst-case analysis, and the testing that validates the configuration should all be recorded. I'd also propose adding a stress test that exercises both drivers simultaneously at their maximum rates, to validate that the chosen solution holds up under worst-case conditions.

**Possible follow-ups:**
- How would you go about measuring the actual worst-case execution time for each driver's critical section?
- What if the analysis shows that both drivers genuinely cannot meet their deadlines with the current hardware — how would you escalate that?