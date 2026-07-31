# embedded-linux-bsp — Day 10

## Q1: How would you approach debugging a situation where a custom board running Linux experiences intermittent resets, and the watchdog timer is not the cause?
**Answer:** Intermittent resets without watchdog involvement typically point to power integrity, thermal issues, or marginal timing rather than software faults. My approach would be systematic:

First, I'd rule out the obvious software causes by checking kernel logs for panic messages, OOM killer activity, or hardware error exceptions (SError, abort) that might indicate a software-triggered reset. If the logs show a clean reboot with no panic, that strongly suggests a hardware-level reset — either from a brown-out detector, external reset line, or PMIC fault.

Next, I'd instrument the hardware. A logic analyzer or oscilloscope on the reset line, power rails, and key supply voltages (especially core voltage) during the reset event can reveal droops or glitches. I'd also check the PMIC's fault registers — many PMICs latch the cause of a reset or power-down, which is often overlooked.

I'd also examine thermal behavior. If resets correlate with load or ambient temperature, I'd check junction temperatures and look for marginal solder joints or inadequate decoupling that only manifests at temperature extremes.

If the resets are truly random and hardware checks come back clean, I'd add a hardware watchdog that logs the reset cause to non-volatile storage (like a PMIC RTC register or a dedicated FRAM), so the next reset provides more forensic data. This turns a "random" problem into a measurable one.

**Possible follow-ups:** How would you distinguish between a software-triggered reset and a hardware reset from the logs alone? What specific kernel configurations or boot parameters would you enable to capture more diagnostic information?

---

## Q2: How would you approach implementing a kernel driver for a device that needs to perform a long operation (e.g., a firmware update to an external sensor that takes several seconds) without blocking the rest of the system?
**Answer:** The core principle is to never hold a lock or block the calling process for the entire duration of a multi-second operation. The standard approach is to structure the driver as a state machine with asynchronous completion.

I'd design the driver with a workqueue or a kernel thread that manages the long operation. The userspace application initiates the operation via an ioctl or write() call, and the driver immediately returns (or returns after queuing the work), allowing the application to poll for completion or block on a wait queue if it has nothing else to do.

For the actual transfer, I'd use interrupt-driven or DMA-based I2C/SPI transfers rather than polling. Each transfer step would be queued, and the completion handler would advance the state machine to the next step. This keeps the CPU available for other tasks and avoids busy-waiting.

I'd also consider using the kernel's `mutex` with `mutex_lock_interruptible()` to allow the waiting process to be interrupted by signals, and I'd implement proper cancellation — if the user cancels the operation, the driver should be able to abort gracefully without leaving the sensor in an unknown state.

For a medical device context, I'd also add a timeout mechanism. If the operation doesn't complete within a specified window, the driver should log an error, reset the sensor, and return a failure to userspace rather than hanging indefinitely.

**Possible follow-ups:** How would you handle the case where the userspace application crashes mid-operation? How would you ensure the driver doesn't leave the sensor in a partially-updated state?

---

## Q3: How would you approach designing the device tree for a system where a single I2C bus has multiple sensors with different interrupt lines, and you need to ensure that interrupt-driven reads work reliably under heavy bus traffic?
**Answer:** The device tree itself is declarative — it describes the hardware topology, and the reliability comes from how the drivers and interrupt handling are implemented. But there are important device tree design considerations.

First, I'd ensure each sensor node has its own `interrupts` property pointing to the correct GPIO or interrupt controller line, with the appropriate trigger type (edge vs. level). For sensors that generate level-triggered interrupts, I'd use `interrupts-extended` if the interrupt controller requires it, and I'd make sure the `interrupt-parent` is correctly specified.

For reliability under heavy traffic, I'd consider whether the I2C bus itself is the bottleneck. If sensors generate interrupts frequently, the interrupt handler should only wake up a kernel thread or tasklet — it should never perform I2C transactions directly in interrupt context, since I2C is slow and can't be called from atomic context anyway. The actual read would happen in a workqueue or threaded IRQ.

In the device tree, I'd also specify `wakeup-source` if any sensor should wake the system from suspend, and I'd set appropriate `pinctrl` states if the interrupt lines need pull-ups or specific drive strength.

One subtle point: if multiple sensors share an interrupt line (via a wired-OR configuration), the device tree should reflect that with `interrupts-extended` and the driver must handle shared interrupts by checking each device's status register to determine which one actually fired.

**Possible follow-ups:** How would you handle a sensor that misses an interrupt because the I2C bus was busy when the event occurred? What are the trade-offs between threaded IRQs and workqueues for this scenario?

---

## Q4: How would you approach implementing a kernel driver for a device that needs to periodically read a sensor at 10 kHz and make the data available to a userspace application with minimal latency, on a single-core ARM Cortex-A processor?
**Answer:** This is a demanding real-time requirement on a single-core application processor. The first question I'd ask is whether 10 kHz truly requires kernel-level processing, or whether the sensor can buffer data and be read in bursts.

Assuming the sensor generates an interrupt per sample, the key design decisions are:

**Interrupt handling:** I'd use a threaded IRQ rather than a hard IRQ handler, since the actual I2C/SPI read will block. The threaded handler runs in process context and can sleep, which is required for bus transactions. The hard IRQ handler should be minimal — just wake the thread.

**Data path:** I'd use a kernel ring buffer (e.g., `kfifo`) to decouple the interrupt-driven producer from the userspace consumer. The driver writes samples to the ring buffer in the threaded IRQ, and userspace reads via `read()` or `mmap()`. Using `mmap()` with a shared ring buffer avoids the copy_to_user overhead and syscall latency for each sample.

**Scheduling:** On a single-core system, the threaded IRQ competes with other tasks. I'd use `sched_setscheduler()` from userspace to set the reading application to SCHED_FIFO with a high priority, ensuring it gets scheduled promptly. The threaded IRQ itself runs at a kernel priority that preempts normal tasks.

**Batching:** If the sensor supports it, I'd configure it to accumulate samples in its own FIFO and interrupt less frequently (e.g., every 100 samples at 100 Hz interrupt rate). This reduces interrupt overhead and bus traffic dramatically.

**Alternative approach:** If the sensor doesn't have a FIFO and 10 kHz is truly continuous, I'd question whether a single-core Cortex-A is the right platform. A small MCU or FPGA handling the high-rate acquisition and the application processor reading bulk data would be a more robust architecture.

**Possible follow-ups:** What are the trade-offs between using a high-resolution timer to poll the sensor versus relying on interrupts? How would you measure and verify that you're meeting the latency requirement?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review, the hardware team reveals that they've changed the I2C bus speed from 100 kHz to 400 kHz to accommodate a new sensor. The firmware team says their driver relies on the 100 kHz timing for a critical sensor's initialization sequence, and they're concerned about reliability. The hardware team insists the change is necessary and the sensor should work at 400 kHz. How would you handle this situation?
**Answer:** This is a classic cross-team conflict where both sides have legitimate concerns, and my role is to facilitate a technical resolution rather than take sides.

First, I'd call a meeting with both teams and ask each to present their technical evidence. The firmware team should explain exactly which timing parameters in the initialization sequence are affected by the bus speed change — is it a minimum clock low time, a setup/hold time, or a timeout that assumes a slower clock? The hardware team should explain why 400 kHz is necessary — is it a bandwidth requirement from the new sensor, or a design choice that could be revisited?

The key question is whether the critical sensor's initialization can be done at 100 kHz while the rest of the bus operates at 400 kHz. Many I2C controllers support per-transfer clock speeds, or the bus can be re-configured between transactions. If the sensor's normal operation works at 400 kHz but its initialization requires slower timing, we could do the init at 100 kHz and then switch to 400 kHz.

If that's not possible, I'd ask the firmware team to characterize the failure mode — does the sensor fail to initialize entirely, or does it initialize with marginal timing that could cause intermittent issues? In a medical device, intermittent issues are unacceptable, so we'd need a definitive answer.

I'd also suggest a practical experiment: run the initialization at 400 kHz on the actual hardware with a scope probing the I2C lines, checking that the timing parameters meet the sensor's datasheet requirements. If the datasheet says the sensor supports 400 kHz, the firmware team's concern might be based on assumptions rather than measured data.

If we can't reach a consensus, I'd escalate to the systems engineer with a clear summary of the technical trade-offs and a recommendation. The decision should be based on data and risk assessment, not on which team is more persuasive.

**Possible follow-ups:** How would you handle the situation if the hardware team's change is already baked into the PCB layout and can't be easily reverted? What documentation or testing would you require before signing off on the change?