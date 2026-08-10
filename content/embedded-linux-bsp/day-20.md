# embedded-linux-bsp — Day 20

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel is not detecting one of two identical I2C sensors on the same bus, while the other works fine?

**Answer:** This is a classic "identical devices, different behavior" problem that usually points to something specific to the device instance rather than the bus or driver in general. I'd start by confirming the scope of the problem: is it always the same physical sensor that fails, or does it vary between boots? If it's always the same one, that suggests a hardware issue specific to that device's connection — a bad solder joint, a missing pull-up on its interrupt line, or an address conflict. If it varies, it's more likely a timing or initialization race.

Next, I'd check the kernel logs at probe time. Does the driver attempt to probe the device and fail with NACK, or does it never attempt at all? If there's no probe attempt, the device may not be present in the device tree, or the address may be wrong. If there is a probe attempt with a NACK, I'd use a logic analyzer or oscilloscope on the I2C lines to see if the device is actually responding — this distinguishes between a driver issue and a hardware issue. I'd also verify the device's address pins are strapped correctly, since two identical sensors on the same bus must have different addresses.

I'd also check whether the failing sensor's power supply is stable. If it shares a rail with something that draws current during boot, the sensor might be in an undefined state. A simple test is to swap the two sensors physically — if the problem follows the sensor, it's a bad part; if it stays with the position, it's the board. Finally, I'd verify the device tree entry matches the actual hardware: correct address, correct compatible string, and any required properties like interrupt lines or supply regulators.

**Possible follow-ups:**
- How would you use a logic analyzer to distinguish between a device not responding and a device responding with corrupted data?
- What device tree properties would you check first for an I2C sensor that fails to probe intermittently?

---

## Q2: How would you approach implementing a kernel driver for a device that needs to perform a hardware-triggered DMA transfer, where the trigger comes from an external sensor's interrupt line, and the data must be processed and made available to userspace within a hard real-time deadline (e.g., 2 ms)?

**Answer:** The key challenge here is meeting a hard deadline while keeping the data path efficient and avoiding priority inversion. I'd structure this in three layers: the interrupt handler, the DMA completion path, and the userspace interface.

For the interrupt handler, I'd keep it minimal — just acknowledge the interrupt and trigger the DMA transfer. The handler should be registered with `IRQF_NO_THREAD` or handled as a fast interrupt to minimize latency. The DMA transfer itself should be set up in advance (pre-allocated buffers, pre-configured DMA channels) so the interrupt handler only needs to write a few registers to start the transfer.

For DMA completion, I'd use a completion callback that runs in softirq or tasklet context. This callback should validate the data (e.g., check a CRC or header), then either copy it to a pre-allocated ring buffer or use a DMA buffer that's directly mapped to userspace via `mmap`. Copying data is safer but adds latency; direct mapping avoids the copy but requires careful cache management. For a 2 ms deadline, I'd likely use a ring buffer with a small number of buffers (e.g., 4–8) to allow the DMA engine to keep running while userspace processes the previous buffer.

For the userspace interface, I'd use a character device with `read()` or `poll()` semantics, or a netlink socket if the data is packet-oriented. The key is to avoid any blocking operations in the kernel path — userspace should be able to `poll()` for data and read it without the kernel doing anything that could miss the deadline. I'd also consider using `sched_setscheduler` with `SCHED_FIFO` for the userspace consumer thread, and document the real-time requirements clearly.

One important consideration is what happens if the deadline is missed. I'd implement a watchdog or timeout mechanism that detects missed deadlines and either drops the data (with a counter exposed to userspace) or triggers an error path. In a medical device context, this would feed into the risk management process — the system needs to know when it's not meeting its timing requirements.

**Possible follow-ups:**
- How would you handle cache coherency when using DMA buffers that are also accessed by userspace?
- What happens if the sensor generates interrupts faster than the DMA engine can complete transfers — how would you detect and handle this?

---

## Q3: How would you approach designing the boot sequence for a system with two processors — an application processor running Linux and a safety-critical microcontroller — where the microcontroller must be fully initialized and running its safety monitoring routines before the Linux userspace starts any critical applications?

**Answer:** This is fundamentally about establishing a deterministic handshake between the two processors and enforcing ordering in the boot sequence. I'd approach it in three phases: hardware-level reset control, bootloader coordination, and kernel/userspace gating.

At the hardware level, I'd ensure the application processor can hold the microcontroller in reset until it's ready to release it. This could be a GPIO connected to the microcontroller's reset pin, or the microcontroller could be the one holding the application processor in reset until it's ready. The key is that one side has deterministic control over the other's start.

In the bootloader (U-Boot), I'd add a handshake step: the bootloader releases the microcontroller from reset, then waits for a "ready" signal — typically a GPIO line or a message over a shared mailbox or UART — before proceeding to load the kernel. This ensures the microcontroller is at least running its initialization code before Linux starts. The handshake should have a timeout with a defined fallback behavior (e.g., log an error and continue, or halt the boot).

In the kernel, I'd use a driver that exposes the microcontroller's status to userspace. This driver would probe the shared communication channel (e.g., mailbox, shared memory with a magic number and status flags) and only report "ready" when the microcontroller has completed its safety initialization. The driver could also enforce a policy: if the microcontroller isn't ready within a certain time, the driver returns an error that userspace can act on.

In userspace, the critical applications should be started by an init system that checks the microcontroller's status before launching. With systemd, this could be a service with `After=` dependencies on a service that reads the status. With a simpler init, the startup script would check the status and either proceed or enter a safe state. The key principle is that the gating happens at multiple levels — bootloader, kernel driver, and userspace — so that even if one layer fails, the others provide backup.

I'd also consider what "fully initialized" means for the safety-critical microcontroller. It's not just that it's running — it needs to have completed its self-tests, initialized its safety monitors, and be actively monitoring before Linux applications start. The handshake should include a status word that indicates which stage of initialization the microcontroller has reached, not just a binary "alive" signal.

**Possible follow-ups:**
- How would you handle the case where the microcontroller fails its self-test during boot — what should the application processor do?
- How would you design the shared memory region for the handshake to avoid race conditions between the two processors?

---

## Q4: Behavioral — You're the BSP lead for a medical device project, and during a pre-production review, the hardware team reveals that they need to change the main processor's power supply from a fixed-voltage regulator to a programmable one (e.g., I2C-controlled) to meet new efficiency requirements. The software team has already completed the kernel and driver development for the fixed regulator, and the change will require a new driver, device tree changes, and potentially a different boot sequence. The project is five weeks from the start of a clinical trial. How would you handle this situation?

**Answer:** This is a significant change at a critical time, so my first step would be to understand the full scope before reacting. I'd call a meeting with the hardware team, the software team, and the project manager to clarify: Is the change mandatory, or is it a preference? What are the efficiency requirements driving it, and could they be met with the existing regulator plus firmware changes (e.g., adjusting the SoC's operating points)? Is the new regulator a drop-in replacement with the same pinout, or does it require PCB changes?

Once I understand the scope, I'd assess the software impact. The key questions are: Does the new regulator use the same voltage levels, or does it need to be programmed to different values at different boot stages? If it's the same voltage, the change might be minimal — just a new driver and device tree node. If the voltage needs to ramp in a specific sequence, the bootloader might need changes too, since the kernel might not be running early enough to program the regulator.

I'd then work with the team to create a risk assessment and a mitigation plan. Options might include: (1) using a hardware workaround — e.g., strap pins on the regulator to set a default voltage that matches the current design, so the software change is minimal; (2) developing the new driver in parallel with the existing hardware still working, so we have a fallback; (3) ordering early prototype boards with the new regulator to validate the software before the clinical trial units are built.

I'd also be transparent with the project manager about the risks. A change like this five weeks before a clinical trial is high-risk, and I'd recommend a formal change control process. If the change is truly mandatory, I'd propose a phased approach: get the hardware working with the default strap settings first, then add the programmable features after the clinical trial. If it's not mandatory, I'd recommend deferring it to a post-trial revision.

Throughout this, I'd document everything — the risk assessment, the decisions, the testing plan — because in a medical device context, this kind of change needs to be traceable for regulatory purposes. The clinical trial is the hard deadline, but patient safety is the ultimate constraint, and I'd make sure the team understands that we won't compromise safety to meet the schedule.

**Possible follow-ups:**
- How would you structure the testing plan for the new regulator to ensure it's ready for the clinical trial?
- What would you do if the hardware team says the change is mandatory and cannot be deferred, but the software team estimates it will take six weeks?

---

## Q5: How would you approach implementing a kernel driver for a device that needs to be accessed by both a real-time safety-critical task and a non-real-time monitoring task, where the safety-critical task must never be blocked by the monitoring task?

**Answer:** The core requirement is isolation — the monitoring task must never be able to delay or block the safety-critical path. I'd approach this by separating the data paths and using different access mechanisms for each task.

For the safety-critical task, I'd provide a dedicated interface that guarantees bounded latency. This could be a character device with `O_RDONLY` access that uses a pre-allocated, lock-free ring buffer. The driver would write data to this buffer in the interrupt or softirq context, and the safety-critical task would read from it using a non-blocking `read()` or a direct `mmap` of the buffer. The key is that the read path never takes a lock that the monitoring task could hold — I'd use a single-producer/single-consumer ring buffer with atomic index updates, which requires no locking at all.

For the monitoring task, I'd provide a separate interface — perhaps a sysfs entry, a debugfs file, or a second character device — that can afford to take locks and do more processing. The monitoring task might want statistics, configuration, or periodic snapshots, and it's acceptable for that path to block or take longer. The important thing is that the monitoring path never shares a lock with the safety-critical path.

I'd also think about what happens when the monitoring task needs to read the same data as the safety-critical task. In that case, I'd have the driver maintain two buffers: the lock-free ring buffer for the safety-critical task, and a separate copy or a snapshot mechanism for the monitoring task. The monitoring task might get slightly stale data, but that's acceptable for monitoring purposes.

Another consideration is the scheduling policy of the tasks themselves. The safety-critical task should run with `SCHED_FIFO` at a high priority, and the monitoring task should run at a normal or low priority. The driver can also enforce this — for example, by checking the task's scheduling policy on `open()` and rejecting access to the safety-critical interface from non-real-time tasks. This adds a layer of protection against misconfiguration.

Finally, I'd consider the failure modes. What happens if the safety-critical task doesn't read the buffer fast enough and it overflows? The driver should have a policy — drop the oldest data, drop the newest, or block the producer (which would be the DMA or interrupt handler, and blocking isn't an option). I'd typically drop the oldest data and increment an overflow counter that the monitoring task can read. This way, the safety-critical task always gets the most recent data, and the system can detect that data was lost.

**Possible follow-ups:**
- How would you handle the case where the monitoring task needs to configure the device (e.g., change the sample rate) while the safety-critical task is actively reading data?
- What kernel mechanisms would you use to ensure the safety-critical task's reads have bounded latency, even under heavy system load?