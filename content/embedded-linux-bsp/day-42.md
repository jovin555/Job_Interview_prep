# embedded-linux-bsp — Day 42

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel is not detecting one of two identical I2C sensors on the same bus, while the other works fine?

**Answer:** I'd approach this systematically, starting with the assumption that the issue is likely one of addressing, hardware connectivity, or device tree configuration rather than a fundamental driver problem — since one sensor works, the bus and driver are functional.

First, I'd verify the device tree entries. With two identical sensors, the most common mistake is assigning the same I2C address to both nodes or using an incorrect address for one of them. I'd check the sensor's address pins (if it has them) against the device tree `reg` property. If the sensor uses a 7-bit address and the device tree specifies an 8-bit address, or vice versa, the kernel will fail to match the device.

Next, I'd check the kernel log for any messages about the missing sensor. If the kernel is probing the bus but not finding the device, I'd look for NAK errors or timeouts. If there's no probe attempt at all, the device tree node might be missing or have incorrect status.

I'd then verify the hardware side: check that the sensor's power supply is present, that the address pins are strapped correctly, and that the I2C lines actually reach the sensor. A common issue is a missing or incorrect pull-up resistor on the SDA/SCL lines for one section of the bus, or a solder bridge on the address pins. I'd use an oscilloscope or logic analyzer to verify that the sensor is actually responding to address probes.

If the hardware checks out, I'd try manually probing the bus from userspace using `i2cdetect` to see if the device responds at the expected address. If it does respond but the kernel isn't binding a driver, the issue is likely in the device tree — perhaps a missing `compatible` string or an incorrect interrupt configuration. If it doesn't respond, the problem is at the hardware or electrical level.

Finally, I'd check for subtle issues like bus capacitance differences between the two sensor locations, or a marginal solder joint that works intermittently. In a medical device context, I'd also want to understand whether this is a consistent failure on all units or a one-off — that distinction changes the investigation significantly.

**Possible follow-ups:**
- How would you distinguish between a device tree issue and a hardware issue if the sensor doesn't appear in `i2cdetect` output?
- What if the sensor is detected intermittently — how would you approach that?

---

## Q2: How would you approach implementing a kernel driver for a device that needs to perform a hardware-triggered DMA transfer, where the trigger comes from an external sensor's interrupt line, and the data must be processed and made available to userspace within a hard real-time deadline (e.g., 2 ms)?

**Answer:** This is a classic real-time data acquisition problem, and the key is to minimize latency at each stage of the pipeline: interrupt delivery, DMA setup, completion notification, and userspace access.

First, I'd design the hardware interface so that the sensor's interrupt line triggers the DMA controller directly, rather than routing through the CPU. Many DMA controllers support hardware-triggered transfers where an external signal initiates the DMA operation without CPU intervention. This eliminates the interrupt latency from the data path — the DMA starts essentially immediately when the sensor asserts its data-ready line.

The driver would configure the DMA channel to perform the transfer into a pre-allocated, physically contiguous buffer. I'd use `dma_alloc_coherent()` or a pre-allocated DMA buffer pool to avoid the overhead of page mapping during the transfer. The buffer should be double-buffered so that while one buffer is being filled by DMA, the previous buffer's data is being processed and delivered to userspace.

For the completion path, I'd use a threaded interrupt handler or a tasklet, depending on the processing requirements. The DMA completion interrupt should be handled with minimal work in the hard IRQ context — just enough to acknowledge the interrupt and wake the processing context. If the data processing is simple (e.g., a checksum or format conversion), it could be done in the tasklet. If it's more complex, a dedicated kernel thread with real-time priority (SCHED_FIFO) would be appropriate.

For userspace delivery with minimal latency, I'd avoid the overhead of `read()` syscalls and instead use `mmap()` to give userspace direct access to the DMA buffers, combined with a poll or eventfd mechanism for synchronization. This avoids copying data through the kernel and eliminates syscall overhead from the data path. The application would poll on the file descriptor, and when the driver signals buffer-ready, the application reads directly from the mapped memory.

To meet the 2 ms deadline, I'd also need to consider the worst-case latency chain: sensor interrupt → DMA trigger → DMA completion interrupt → kernel thread wakeup → userspace notification. Each stage adds latency, so I'd measure and profile each one. If the deadline is truly hard, I might need to consider whether the kernel's scheduling guarantees are sufficient, or whether some of the processing needs to move to a dedicated real-time core or an FPGA.

**Possible follow-ups:**
- How would you handle the case where the DMA transfer size varies between triggers?
- What if the 2 ms deadline includes the userspace application's processing time, not just the kernel's delivery time?

---

## Q3: How would you approach designing the boot sequence for a system with two processors — an application processor running Linux and a safety-critical microcontroller — where the microcontroller must be fully initialized and running its safety monitoring routines before the Linux userspace starts any critical applications?

**Answer:** This is fundamentally about establishing a deterministic handshake between the two processors and enforcing an ordering guarantee in the boot sequence.

The first design decision is the hardware reset architecture. I'd want the microcontroller to be released from reset before or simultaneously with the application processor, so it can begin its initialization immediately. The microcontroller should have its own independent clock source and power domain so its boot doesn't depend on the application processor's state.

For the handshake, I'd use a dedicated GPIO line or a simple mailbox mechanism in shared memory. The microcontroller would assert a "ready" signal once it has completed its self-tests and is running its safety monitoring routines. The application processor's bootloader (U-Boot) or kernel driver would wait for this signal before proceeding.

The key question is where in the boot sequence to enforce the wait. Waiting in U-Boot is simpler and provides a hard guarantee — the kernel won't even start until the microcontroller is ready. However, this adds to the total boot time and means the kernel can't do any parallel initialization. Waiting in the kernel (e.g., in a platform driver that probes early) allows the kernel to initialize other subsystems while waiting, but requires careful coordination to ensure no critical application starts before the microcontroller is ready.

For a medical device, I'd lean toward enforcing the wait in U-Boot or very early in the kernel boot, before the root filesystem is mounted. This provides the strongest guarantee that no userspace application can run before the safety monitor is active. The bootloader would poll the handshake GPIO with a timeout, and if the microcontroller doesn't signal ready within a specified window, the boot would halt with an error — this is the fail-safe behavior for a medical device.

Once the microcontroller signals ready, the boot proceeds. The kernel would then have a driver that maintains the handshake — monitoring the microcontroller's health via a watchdog or periodic heartbeat, and ensuring that if the microcontroller fails during operation, the system takes appropriate action (e.g., shutting down critical applications or triggering an alarm).

I'd also consider the reverse direction: what happens if the application processor needs to reboot? The microcontroller should be able to detect the application processor's reboot and either continue running independently or reset itself to a known state, depending on the safety requirements.

**Possible follow-ups:**
- What would you do if the microcontroller fails to signal ready within the timeout period?
- How would you handle the case where the application processor needs to reboot while the system is in operation?

---

## Q4: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel log shows "Failed to request IRQ" for a device that worked on the previous board revision?

**Answer:** This is a regression between board revisions, so I'd start by comparing the two revisions to identify what changed that could affect interrupt allocation.

First, I'd check the device tree to see if the interrupt configuration for the affected device changed between revisions. The interrupt number, trigger type (level vs. edge), or the interrupt controller phandle might be incorrect. I'd verify that the interrupt number in the device tree matches the actual hardware connection on the new revision — a common issue is that a peripheral moved to a different GPIO or interrupt line, but the device tree wasn't updated.

Next, I'd check whether the interrupt is actually available — is it already claimed by another driver? The "Failed to request IRQ" error often means the interrupt is already in use. On the new board revision, a different device might be claiming the same interrupt due to a device tree overlap or a driver probe order change. I'd look at `/proc/interrupts` to see which interrupts are claimed and by whom.

I'd also check the interrupt controller configuration. If the new board revision uses a different interrupt controller or a different GPIO controller for the interrupt line, the device tree might be referencing the wrong controller. The `interrupt-parent` property is a common source of this kind of error.

Another possibility is that the interrupt line is being held in an invalid state on the new revision. For example, if the device's interrupt output is active-low but the device tree specifies active-high, the interrupt controller might see a constant interrupt condition and refuse to allocate it. I'd check the trigger type configuration and verify the actual signal behavior with a logic analyzer.

If the hardware and device tree look correct, I'd check the driver's probe sequence. Perhaps the driver is trying to request the interrupt before the interrupt controller is ready, or before a GPIO controller that provides the interrupt is probed. This could be a probe ordering issue that manifests differently on the new revision due to timing changes.

Finally, I'd check the kernel log more broadly — is there an earlier error about the interrupt controller or GPIO controller failing to probe? Sometimes the root cause is upstream: if the interrupt controller itself fails, all downstream interrupt requests will fail.

**Possible follow-ups:**
- How would you determine whether the issue is a device tree problem or a driver probe ordering problem?
- What if the interrupt works fine when the driver is built as a module and loaded manually, but fails when built into the kernel?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a pre-production review, the hardware team reveals that they need to change the main processor's boot mode strap resistors to accommodate a new flash part. The change means the processor will boot from a different interface (e.g., from SPI NOR to eMMC), and the bootloader and kernel configurations are already tuned for the current boot source. The project is six weeks from the start of a clinical trial. How would you handle this situation?

**Answer:** This is a significant change with a tight timeline, so my first priority is to understand the full scope of the impact and establish a clear plan with the team.

I'd start by asking the hardware team for the specifics: why is the flash part changing, is the new part already qualified, and is the boot mode change a hard requirement or could the new flash part work on the existing interface? Sometimes the boot mode change is a side effect of the part selection, and there might be an alternative part that works with the existing configuration. I'd want to explore whether we can avoid the change entirely.

If the change is unavoidable, I'd assess the technical impact. The bootloader will need to be rebuilt with support for the new boot interface — this includes the driver for the new flash type, the boot command configuration, and potentially the boot script. The kernel will need the appropriate driver enabled and the device tree updated to reflect the new storage device. I'd also need to verify that the boot time is still within specification, since eMMC and SPI NOR have different initialization times.

I'd then create a detailed plan with clear milestones: update the bootloader, update the kernel configuration and device tree, test on a development board with the new flash part, and then validate on the production hardware. I'd want to get a sample of the new flash part as early as possible so we can start testing immediately rather than waiting for the production boards.

For the clinical trial timeline, I'd work with the project manager to identify what can be parallelized. For example, the kernel configuration changes can be developed and tested in parallel with the bootloader work. I'd also identify the critical path — likely the bootloader bring-up on the new interface — and allocate resources accordingly.

I'd also consider risk mitigation. Since we're six weeks from the clinical trial, I'd want a fallback plan. This might include keeping the old flash part available as a backup, or having a pre-built image that can be loaded via JTAG or another debug interface if the boot-from-new-interface has issues. I'd also want to ensure that the manufacturing team can program the new flash part during production — this might require different programming equipment or procedures.

Finally, I'd communicate clearly with the team about the risks and the plan. I'd set up regular checkpoints to track progress and escalate any issues early. In a medical device context, I'd also want to document the change and its impact on the design history file, since this affects the device's configuration management.

**Possible follow-ups:**
- How would you prioritize the work if the bootloader bring-up takes longer than expected?
- What would you do if the new flash part arrives and has a subtle incompatibility with the existing bootloader that takes weeks to resolve?