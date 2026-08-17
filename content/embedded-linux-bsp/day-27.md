# embedded-linux-bsp — Day 27

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel log shows "Failed to request IRQ" for a device that worked on the previous board revision?

**Answer:** I'd start by recognizing that "worked on the previous revision" is a valuable clue but not a diagnosis — something changed between revisions, and my job is to find what. The first step is to get the full error context: the exact IRQ number, the device name, and whether the failure happens at probe time or later. I'd check `dmesg` for the complete message and look for any preceding warnings about the interrupt controller or GPIO controller.

Next, I'd verify the device tree. A common cause is that the new board revision moved a peripheral to a different interrupt line, but the device tree still references the old one — or the interrupt parent (e.g., a GPIO controller or interrupt controller) is now disabled or has a different `#interrupt-cells` property. I'd compare the device tree source for the old and new revisions, paying attention to `interrupt-parent`, `interrupts`, and any `interrupt-names` properties.

I'd also check whether the IRQ is actually available. The error can occur if another driver has already claimed that interrupt line — perhaps a new device was added on this revision that grabs the same IRQ, or a shared IRQ handler is now registered with `IRQF_SHARED` when it shouldn't be. I'd look at `/proc/interrupts` to see what's registered and whether the line is already in use.

Hardware-level causes are also possible. If the interrupt line is now floating or not properly pulled up on the new revision, the interrupt controller might not see a valid edge or level, causing the request to fail or the IRQ to never fire. I'd check the schematic for the interrupt line — pull-up resistors, series resistors, and whether the device's interrupt output is actually connected to the right pin on the SoC.

Finally, I'd check the driver itself. If the driver requests the IRQ with specific flags (e.g., `IRQF_TRIGGER_RISING`) and the new hardware inverts the signal, the request might succeed but the interrupt never fires — which would look like a different symptom. But if the driver uses a legacy IRQ number that's now out of range, or if the platform device's resource assignment changed, the request itself could fail.

**Possible follow-ups:**
- How would you distinguish between a device tree issue and a driver issue when the error message is the same?
- What if the IRQ request succeeds but the interrupt never fires — how would your debugging approach change?

---

## Q2: How would you approach implementing a kernel driver for a device that needs to be accessed by both a real-time safety-critical task and a non-real-time monitoring task, where the safety-critical task must never be blocked by the monitoring task?

**Answer:** The core design principle here is that the safety-critical path must have deterministic, bounded access to the hardware, and the monitoring path must be completely isolated from it. I'd start by defining the access patterns: what operations each task performs, how frequently, and what the latency requirements are.

The cleanest approach is to avoid sharing the device directly. If the hardware allows it, I'd give the safety-critical task exclusive access to the device through a dedicated kernel driver or a real-time thread in userspace that uses `sched_setscheduler` with `SCHED_FIFO`. The monitoring task would get data through a separate channel — for example, the safety-critical driver could publish data to a lock-free ring buffer or a shared memory region that the monitoring task reads. This way, the monitoring task never touches the device hardware, so it can't block the safety-critical path.

If both tasks must access the same hardware (e.g., a single ADC that both need to read), I'd use a mutex or spinlock in the driver, but with careful priority handling. The key is to prevent priority inversion: if the monitoring task holds the lock and the safety-critical task is waiting, the monitoring task must be temporarily boosted to the safety-critical task's priority (priority inheritance) so it can finish and release the lock quickly. In the kernel, I'd use a `rt_mutex` which has priority inheritance built in, rather than a plain mutex.

I'd also consider whether the monitoring task can be preempted while holding the lock. If the critical section is short (just a register read or write), a spinlock with interrupts disabled might be acceptable — but I'd need to be careful about how long interrupts are disabled, since that affects the entire system's real-time behavior.

Another approach is to use a hardware FIFO or DMA. If the device supports DMA, the safety-critical task could set up a DMA transfer and the monitoring task could read the DMA buffer — but I'd need to ensure that the DMA buffer is not accessed concurrently in a way that causes data corruption.

Finally, I'd document the design clearly: which paths are real-time, what the worst-case latency is, and what happens if the monitoring task misbehaves (e.g., holds a lock too long). In a medical device context, this would feed into the risk analysis and the safety case.

**Possible follow-ups:**
- How would you handle the case where the monitoring task needs to configure the device (e.g., change sampling rate) while the safety-critical task is actively reading?
- What if the hardware doesn't support concurrent access at all — how would you arbitrate?

---

## Q3: How would you approach designing the boot sequence for a system with two processors — an application processor running Linux and a safety-critical microcontroller — where the microcontroller must be fully initialized and running its safety monitoring routines before the Linux userspace starts any critical applications?

**Answer:** The fundamental requirement is a deterministic handshake between the two processors, with the application processor holding off its critical userspace until the microcontroller confirms it's ready. I'd design this as a staged boot with explicit readiness signals.

First, I'd define the boot order. The microcontroller should come up first, or at least in parallel, and it should be able to initialize independently — it has its own clock, power, and firmware. The application processor's bootloader (U-Boot) should not assume the microcontroller is ready; instead, it should check a status signal or register.

The handshake mechanism depends on the hardware. Options include: a GPIO line that the microcontroller asserts when ready, a shared memory register with a magic value and sequence number, a mailbox mechanism, or a combination — for example, the microcontroller writes a status word to shared memory and then asserts a GPIO. I'd prefer a mechanism that includes both a level (GPIO) and data (shared memory) so the application processor can verify not just that the microcontroller is running, but that it's running the expected firmware version and has completed its self-tests.

In the bootloader, I'd add a wait-for-ready step with a timeout. The bootloader would poll the GPIO or shared memory register, and if the microcontroller doesn't become ready within a defined window, the bootloader would either halt with an error or boot into a degraded mode (depending on the safety requirements). This is important — the bootloader must not hang indefinitely, because that would make the system unbootable in the field.

Once Linux starts, the kernel should not start critical applications until the handshake is confirmed. I'd implement this in the init system: a service that runs early in the boot sequence, checks the handshake status (via a kernel driver that exposes the shared memory or GPIO), and only then starts the critical application services. If the handshake fails, the system should enter a safe state — for example, a maintenance mode or a shutdown with an error message.

I'd also consider the reverse direction: what if the application processor needs to reset or restart the microcontroller? The boot sequence should handle that gracefully, ensuring that a microcontroller reset doesn't leave the system in an inconsistent state.

Finally, I'd think about the failure modes: what happens if the microcontroller's firmware is corrupted, if it hangs during initialization, or if the handshake signal is stuck? Each of these needs a defined behavior, and in a medical device, these would be documented in the risk analysis.

**Possible follow-ups:**
- How would you handle the case where the microcontroller needs to be reset after Linux is already running — how would the handshake be re-established?
- What if the application processor boots faster than the microcontroller — how would you handle the timeout and retry logic?

---

## Q4: How would you approach implementing a kernel driver for a device that needs to perform a hardware-triggered DMA transfer, where the trigger comes from an external sensor's interrupt line, and the data must be processed and made available to userspace within a hard real-time deadline (e.g., 2 ms)?

**Answer:** This is a classic hard-real-time data path, and the key is to minimize latency and jitter at every stage. I'd start by mapping the data flow: sensor interrupt → DMA transfer → kernel processing → userspace notification → application processing. Each stage has a cost, and I need to budget the 2 ms across all of them.

The first decision is where the DMA transfer is set up. The sensor interrupt should trigger the DMA transfer directly, not go through the CPU first. Many SoCs support DMA requests from external pins or from a peripheral's interrupt line. If the sensor's interrupt can be routed to the DMA controller as a hardware request, the DMA controller can move the data to memory without CPU involvement. This is the lowest-latency path.

If that's not possible, the interrupt handler would need to set up the DMA transfer. In that case, I'd use a threaded interrupt handler or a tasklet, but I'd be careful about latency — a regular interrupt handler runs in atomic context and can't sleep, so setting up a DMA transfer there requires the DMA channels to be pre-configured and ready. I'd pre-allocate the DMA buffers and pre-configure the transfer descriptors so the interrupt handler just writes a few registers to start the transfer.

For the DMA completion, I'd use a completion callback that wakes up a kernel thread or a high-priority userspace thread. The callback should be minimal — just enough to signal the waiting task. I'd avoid doing any heavy processing in the callback itself.

For the userspace interface, I'd use a mechanism that minimizes latency: either a blocking read on a character device that wakes up when data is ready, or an eventfd that the application can poll. I'd avoid copying data unnecessarily — if possible, I'd use `mmap` so the application reads the DMA buffer directly, or use `dma_buf` to share the buffer. If a copy is needed, I'd use `copy_to_user` in the read path, but I'd make sure the buffer is cache-aligned and the copy is efficient.

I'd also consider using the PREEMPT_RT patch set if the system allows it, to make the kernel fully preemptible and reduce scheduling latency. And I'd pin the relevant kernel thread and the userspace application to a dedicated CPU core if the system has multiple cores, to avoid cache thrashing and scheduling delays.

Finally, I'd measure the actual latency under worst-case conditions — with other interrupts firing, with the memory bus under load, and with the CPU under load. The 2 ms budget needs headroom, so I'd aim for a measured worst-case latency well below that, and I'd document the margin.

**Possible follow-ups:**
- How would you handle the case where the sensor interrupt fires faster than the DMA transfer can complete — what's your backpressure mechanism?
- How would you debug a situation where the DMA transfer occasionally misses the deadline by a few hundred microseconds?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a pre-production review, the hardware team reveals that they need to change the main processor's boot mode strap resistors to accommodate a new flash part. The change means the processor will boot from a different interface (e.g., from SPI NOR to eMMC), and the bootloader and kernel configurations are already tuned for the current boot source. The project is six weeks from the start of a clinical trial. How would you handle this situation?

**Answer:** My first reaction would be to understand the scope of the change and the reason for it. The hardware team has presumably identified a supply chain issue or a technical problem with the current flash part, so I'd want to understand: Is this a forced substitution, or is there flexibility? What are the specific requirements of the new flash part? Is the change limited to the boot source, or does it affect other aspects of the design?

Once I understand the scope, I'd assess the impact on the software. The bootloader (U-Boot) would need to be configured to boot from the new interface — this includes the driver for the new flash type, the boot command, and potentially the environment variables. The kernel would need the corresponding driver enabled and the device tree updated to reflect the new storage device. I'd also need to check the root filesystem — if it's moving from SPI NOR to eMMC, the filesystem type and partition layout might change.

I'd then estimate the effort and timeline. The actual code changes might be relatively small — a few configuration changes and a device tree update — but the testing effort could be significant. I'd need to verify that the bootloader boots reliably from the new interface, that the kernel mounts the root filesystem correctly, that the OTA update mechanism works with the new storage, and that power-loss behavior is safe. In a medical device, this would also need to be documented and potentially go through a change review process.

Given the six-week timeline, I'd propose a parallel workstream: the software team starts the port immediately, while the hardware team provides early samples or a development board with the new flash part. I'd also identify the risks: if the new flash part has subtle differences (e.g., different erase block size, different timing), the software might work in testing but fail in the field. I'd want to understand the hardware team's qualification plan for the new part.

I'd also be honest about the schedule. If the change is truly necessary, I'd commit to a plan but flag the risks and the need for additional testing time. If the change can be deferred — for example, if the current flash part is still available for the clinical trial units — I'd recommend that approach, with the new flash part introduced in a later revision. The clinical trial is a critical milestone, and introducing a new boot source six weeks before it starts is a significant risk.

Finally, I'd document everything: the change request, the impact assessment, the testing plan, and the decision. In a medical device context, this would feed into the design history file and the risk management process.

**Possible follow-ups:**
- How would you handle the situation if the hardware team says the change is mandatory and cannot be deferred?
- What specific tests would you run to validate the new boot source before the clinical trial?