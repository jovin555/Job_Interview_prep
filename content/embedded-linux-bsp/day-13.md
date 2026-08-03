# embedded-linux-bsp — Day 13

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the Ethernet interface works only when the cable is plugged in before power-on — not when the cable is plugged in after boot?
**Answer:** This is a classic PHY link-detection issue. The key clue is that the interface works when the cable is present at boot but not when plugged in afterward — this suggests the PHY isn't generating or the MAC isn't handling link-change interrupts properly. I'd approach this systematically:

1. **Check the PHY's interrupt configuration.** Many PHYs have an interrupt pin that signals link status changes. If the PHY's interrupt isn't wired to the SoC, or the device tree doesn't describe it, the MAC driver will only detect link at initial PHY polling during probe. After boot, the PHY may enter a low-power or isolated state, and without an interrupt to wake the driver, the link never gets renegotiated.

2. **Verify the device tree binding.** I'd confirm that the PHY node has the correct `interrupt-parent` and `interrupts` properties, and that the PHY's interrupt line is actually connected on the schematic. A common mistake is assuming the PHY's INT pin is active-low when it's actually open-drain, requiring a pull-up that might be missing.

3. **Test with PHY polling.** As a workaround, I'd check whether the driver supports polling mode (e.g., setting `phy-mode` correctly or using the `phy_polling` option). If polling works, it confirms the issue is interrupt-related rather than a fundamental PHY configuration problem.

4. **Check the MDIO bus.** If the PHY is on a separate MDIO bus or has an unusual address, the driver might not be probing it correctly after a reset. I'd verify the PHY is accessible via `mdio-tools` or by reading its registers through debugfs.

5. **Look at the MAC's link-management logic.** Some MAC drivers have a "fixed link" or "no-autoneg" mode that assumes the link is always up. If the driver is configured for fixed-link, it won't react to cable plug/unplug events at all.

The most likely root cause in my experience is a missing or misconfigured PHY interrupt — either the hardware line isn't connected, or the device tree doesn't declare it. The fix would be either wiring the interrupt properly or falling back to PHY polling with a short poll interval.

**Possible follow-ups:**
- How would you determine whether the issue is in the PHY driver or the MAC driver?
- What PHY registers would you read to confirm the link state, and how would you interpret them?

---

## Q2: How would you approach implementing a kernel driver for a device that needs to be accessed by both a real-time safety-critical task and a non-real-time monitoring task, where the safety-critical task must never be blocked by the monitoring task?
**Answer:** This is fundamentally a concurrency and priority design problem. The core principle is that the safety-critical path must have deterministic access to the hardware, while the monitoring path must be designed so it can never interfere — even if it misbehaves.

My approach would be:

1. **Separate the access paths at the hardware level if possible.** If the device has multiple channels, registers, or memory regions, I'd partition them so each task accesses its own hardware resources. This eliminates contention at the source.

2. **If hardware partitioning isn't possible, use a lock hierarchy with priority inheritance.** The safety-critical task should use a real-time mutex (e.g., `rt_mutex` in the kernel) that supports priority inheritance. This prevents the monitoring task from holding the lock while a higher-priority task waits, which would cause priority inversion. The monitoring task should use the same lock but with a lower priority class, so it can be preempted while holding the lock.

3. **Consider lock-free or wait-free approaches for read-mostly data.** If the monitoring task only needs to read status or telemetry, I'd use a sequence lock (`seqlock`) or a read-copy-update (RCU) approach. The safety-critical task writes to the data structure, and the monitoring task reads it without ever blocking the writer. The monitoring task might get stale data or have to retry, but that's acceptable for non-critical monitoring.

4. **Use dedicated interrupt or DMA paths.** If the device generates interrupts, the safety-critical task should handle them in hardirq or threaded-irq context with `IRQF_NO_THREAD` if needed. The monitoring task should never be in the interrupt path.

5. **Add instrumentation and validation.** I'd add lockdep validation to catch any potential deadlock or inversion at development time, and I'd stress-test with the monitoring task doing heavy I/O while the safety-critical task runs at its maximum rate.

The key design principle is that the safety-critical path should have its own dedicated hardware resources or a lock with priority inheritance — never a plain spinlock or mutex shared with a lower-priority task without inheritance semantics.

**Possible follow-ups:**
- How would you handle the case where the device has a single shared register that both tasks must write?
- What kernel configuration options or debugging tools would you use to verify that the safety-critical task never misses its deadline?

---

## Q3: How would you approach structuring the device tree for a system where a single FPGA peripheral exposes multiple functions — a DMA controller, a set of GPIOs, and a custom sensor interface — and each function needs to be managed by a separate kernel driver?
**Answer:** This is a common scenario with FPGA-based designs, and the key is to model the FPGA as a parent node with child nodes representing each functional block. This mirrors how the hardware is actually structured and lets each driver bind to its own node.

My approach:

1. **Create a top-level FPGA node** with the base address, clock, and reset information. This node represents the FPGA as a whole and might have a simple "fpga-region" compatible string if it's managed by the FPGA manager framework, or a custom compatible string if it needs a specific configuration driver.

2. **Define child nodes for each function**, each with its own compatible string, register offsets (relative to the parent's base), interrupts, and DMA channels. For example:
   - A DMA controller node with `compatible = "vendor,fpga-dma"`, its register offset, and interrupt.
   - A GPIO controller node with `compatible = "vendor,fpga-gpio"`, `gpio-controller` property, and `#gpio-cells`.
   - A sensor interface node with its own compatible string and interrupt.

3. **Use `ranges` to map addresses.** The parent node should have a `ranges` property that translates the FPGA's internal address space to the CPU's address space. Child nodes then use offsets relative to the FPGA base, which keeps the device tree clean and makes it easy to move the FPGA in the memory map without changing every child node.

4. **Handle shared resources carefully.** If the FPGA has a single interrupt line that's shared among functions, I'd use the `interrupt-controller` node inside the FPGA to represent the FPGA's interrupt controller, with each child node referencing it. This is more accurate than having all children point to the same GIC interrupt.

5. **Consider using a platform driver for the parent.** The parent driver would handle FPGA initialization (e.g., loading the bitstream, enabling clocks) and then let the child drivers probe independently. The parent driver can use `of_platform_populate()` to instantiate child devices.

The main advantage of this structure is that each driver is independent — you can enable or disable functions by changing the device tree, and each driver can be developed and tested in isolation. It also makes the hardware design explicit in the device tree, which helps with review and maintenance.

**Possible follow-ups:**
- How would you handle the case where the FPGA bitstream can be loaded at runtime, and the device tree needs to be updated after loading?
- What are the trade-offs between having a single monolithic driver versus multiple child drivers?

---

## Q4: Behavioral — You're the BSP lead for a medical device project, and during a pre-production review, the manufacturing team reveals that the PCB for the main processor board has a routing error: the I2C pull-up resistors for a critical sensor bus are connected to the wrong voltage rail (3.3V instead of 1.8V). The sensor is rated for 1.8V I2C, and the board is already in production. The project is three weeks from the start of a clinical trial. How would you handle this situation?
**Answer:** This is a serious issue because it's a hardware defect that could damage the sensor or cause communication failures — both unacceptable in a medical device headed to a clinical trial. My approach would be:

1. **Immediately assess the risk and impact.** First, I'd determine whether the 3.3V pull-ups will actually damage the sensor or just cause marginal operation. If the sensor's I2C pins are not 5V-tolerant and are only rated for 1.8V, applying 3.3V through pull-ups could exceed the absolute maximum ratings and cause permanent damage. Even if it doesn't immediately fail, it could cause reliability issues over time — which is especially concerning for a medical device.

2. **Stop production and quarantine affected boards.** I'd work with manufacturing to halt any further assembly and quarantine all boards that have this issue. We need to know exactly how many boards are affected and whether any have already shipped.

3. **Evaluate mitigation options in parallel:**
   - **Board rework:** If the pull-up resistors are discrete components, they could be removed or replaced with ones connected to the correct rail. This is feasible if the board has accessible pads and the rework can be done reliably.
   - **Disable the pull-ups in firmware:** If the SoC's I2C controller has internal pull-ups that can be enabled, we might be able to rely on those instead of the external ones. However, this depends on the SoC's capabilities and whether the internal pull-ups have appropriate values for the bus speed.
   - **Use a level shifter:** If there's space, adding a level shifter between the 3.3V rail and the sensor's I2C pins could protect the sensor. But this is a significant hardware modification.
   - **Software workaround:** If the sensor can tolerate 3.3V on its I2C pins for short periods (some sensors have absolute maximum ratings that allow this), we might be able to operate with reduced bus speed or shorter communication windows. This is risky and would need thorough validation.

4. **Engage the regulatory and quality teams.** Since this is a medical device, any hardware change — even a rework — needs to go through the change control process. I'd work with quality to document the issue, the mitigation, and the validation plan. The clinical trial schedule might need to be adjusted if the rework can't be completed in time.

5. **Lead the root-cause analysis.** Once the immediate issue is contained, I'd lead an 8D or similar root-cause investigation to understand how the routing error happened — was it a schematic error, a layout error, or a design review miss? This would inform process improvements to prevent recurrence.

The key is to be transparent with the project team and stakeholders about the severity, while working quickly to find a safe and reliable path forward. In a medical device context, we can't compromise on safety or reliability — even if it means delaying the clinical trial.

**Possible follow-ups:**
- How would you decide between reworking the boards versus scrapping them and re-spinning the PCB?
- What validation testing would you require before approving the boards for the clinical trial?

---

## Q5: How would you approach implementing a kernel driver for a device that needs to perform a hardware-triggered DMA transfer, where the trigger comes from an external sensor's interrupt line, and the data must be processed and made available to userspace within a hard real-time deadline (e.g., 2 ms)?
**Answer:** This requires careful design across the interrupt path, DMA setup, and userspace notification. The 2 ms deadline is tight but achievable on a modern embedded processor if the design is clean. Here's how I'd approach it:

1. **Use a threaded interrupt handler with high priority.** The sensor's interrupt line should be registered with `request_threaded_irq()` with a high-priority real-time thread (e.g., `SCHED_FIFO` with a high priority). The hardirq handler should be minimal — just acknowledging the interrupt and waking the threaded handler. The threaded handler does the actual work of setting up the DMA transfer.

2. **Pre-allocate and pre-configure DMA buffers.** To avoid allocation latency in the critical path, I'd allocate DMA-capable buffers at probe time using `dma_alloc_coherent()` or `dma_map_single()` with pre-mapped buffers. The buffers should be double-buffered so that while one buffer is being filled by DMA, the previous buffer's data can be processed and delivered to userspace.

3. **Use DMA engine API with a completion callback.** I'd use the DMA engine API (`dma_request_chan()`, `dmaengine_prep_dma_cyclic()` or `dmaengine_prep_slave_single()`) with a completion callback that fires when the transfer completes. The callback should be lightweight — it can wake a kernel thread or use a completion variable to signal a waiting process.

4. **Minimize copy operations.** If possible, I'd use `mmap()` to let userspace access the DMA buffers directly, avoiding a copy from kernel space to user space. This can be done by implementing an `mmap` file operation that maps the DMA buffers into the process's address space. Alternatively, use `copy_to_user()` if the data volume is small enough that the copy time is negligible.

5. **Use a real-time wait queue or `poll()` for userspace notification.** The driver should implement `poll()` or use a wait queue with a real-time priority so that the waiting userspace process is woken with minimal latency. For hard real-time, I'd consider using `futex` or a real-time signal (`SIGEV_THREAD` with `SCHED_FIFO`) to notify userspace.

6. **Profile and validate the timing.** I'd use `ftrace` or `perf` to measure the interrupt latency, DMA setup time, transfer completion, and userspace wake-up latency. The 2 ms budget needs to be broken down: interrupt latency (typically microseconds), DMA setup (tens of microseconds), transfer time (depends on data size and bus speed), and userspace notification (microseconds to tens of microseconds). If the total exceeds 2 ms, I'd look at optimizing the slowest component.

7. **Consider using a dedicated DMA channel with priority.** If the DMA controller supports channel priorities, I'd configure the sensor's channel with the highest priority to ensure it isn't delayed by other DMA traffic.

The key is to avoid any blocking operations in the critical path — no dynamic allocation, no sleeping locks, no I/O. Everything should be pre-allocated and pre-configured, and the interrupt-to-userspace path should be as short as possible.

**Possible follow-ups:**
- How would you handle the case where the DMA transfer size varies between triggers?
- What would you do if profiling shows that the userspace wake-up latency is the bottleneck?