# embedded-linux-bsp — Day 16

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the display output is garbled or shows incorrect colors, and the display controller is connected via MIPI DSI?

**Answer:** I'd start by isolating whether the problem is in the display pipeline configuration, the timing parameters, or the physical interface. First, I'd verify the basic link: check that the DSI controller is properly initialized, the PHY is locked, and the link is in the correct number of lanes and data rate. I'd use a logic analyzer or scope on the DSI lanes if available, but more practically, I'd check the kernel logs for any DSI or display controller errors during probe.

Next, I'd examine the device tree configuration for the display panel — the most common cause of garbled output is incorrect timing parameters (porches, sync widths, pixel clock) or a mismatch between the panel's expected data format and what the controller is configured to send. I'd compare the panel's datasheet timings against the device tree node, and also verify the color format (e.g., RGB888 vs RGB666) matches between the panel and the controller configuration.

If timings look correct, I'd check the clock tree — a miscalculated pixel clock or DSI clock can cause marginal timing that manifests as garbled output. I'd also verify the regulator and GPIO setup for the panel's reset and power sequencing, since an incorrect reset timing can cause the panel to come up in an undefined state.

Finally, I'd check the framebuffer or DRM/KMS configuration — if the system is using a simple framebuffer, the pixel format in the kernel command line or the bootloader's display setup might not match what the panel expects. I'd also verify the display controller's output format settings match the panel's input format.

**Possible follow-ups:**
- How would you distinguish between a timing issue and a data format issue?
- What tools would you use to inspect the DSI link state at runtime?

---

## Q2: How would you approach implementing a kernel driver for a device that needs to be accessed by both a real-time safety-critical task and a non-real-time monitoring task, where the safety-critical task must never be blocked by the monitoring task?

**Answer:** The core principle is that the safety-critical path must never depend on a lock that the non-real-time path can hold. I'd design the driver with separate access paths: the safety-critical task would use a lock-free or wait-free mechanism, such as a ring buffer with atomic read/write pointers, while the monitoring task would use a separate, slower path — perhaps a sysfs attribute or a secondary character device — that reads from the same buffer but can tolerate taking a mutex.

For the shared data, I'd use a single-producer/single-consumer ring buffer where the safety-critical task is the consumer and the driver's interrupt handler (or a high-priority kernel thread) is the producer. The monitoring task would read from a snapshot or a separate copy of the data, not from the same buffer, to avoid contention. If the monitoring task needs to read the same data, I'd have it take a seqlock — readers don't block writers, and the writer (the safety-critical path) never blocks on the reader.

I'd also ensure that the safety-critical task's access path doesn't allocate memory, take any sleeping locks, or call any function that could block. This means the driver's read path for the safety-critical interface would be a simple, non-blocking function that copies data from the hardware registers or DMA buffer into the ring buffer, using only atomic operations and memory barriers.

For the monitoring interface, I'd use a mutex-protected read that copies the latest data out, and it would be acceptable for that path to block. The key is that the two paths are completely independent — no shared locks, no shared buffers that require mutual exclusion.

**Possible follow-ups:**
- How would you handle the case where the monitoring task needs to see a consistent snapshot of multiple sensor values?
- What memory barriers would you need to ensure correctness on an ARM processor?

---

## Q3: How would you approach structuring the root filesystem for an embedded Linux medical device that needs to support over-the-air (OTA) updates with a rollback mechanism, while ensuring that patient data and configuration settings survive the update process?

**Answer:** I'd use a dual-partition (A/B) scheme for the root filesystem, with a separate, persistent data partition that is never touched during an update. The layout would be something like: partition A (rootfs A), partition B (rootfs B), and a data partition. The bootloader selects which rootfs to boot based on a flag stored in a small, dedicated metadata area (e.g., U-Boot environment or a separate partition).

The data partition would be mounted at a fixed location, such as `/data`, and all patient data, configuration files, and logs would be stored there. The root filesystem itself would be read-only or mounted read-only after boot, with only the data partition writable. This ensures that an update to the rootfs never affects patient data.

For the update mechanism, the update package would contain a complete rootfs image for the inactive partition. The update process would: write the new image to the inactive partition, verify its integrity (checksum and signature), update the bootloader flag to point to the new partition, and reboot. If the new system fails to boot or fails a health check (e.g., a watchdog or a userspace health monitor), the bootloader would automatically fall back to the previous partition.

I'd also consider using a read-only squashfs or erofs for the rootfs to prevent accidental corruption, with an overlay filesystem for any runtime-writable parts of the rootfs that aren't patient data — though ideally, all writable data goes to the data partition.

For the data partition, I'd use a journaling filesystem like ext4 with appropriate mount options (e.g., `data=ordered`) to minimize corruption risk on power loss. I'd also ensure that the data partition has its own integrity checking mechanism, such as a filesystem check at boot or a dedicated health monitoring service.

**Possible follow-ups:**
- How would you handle the case where the update itself corrupts the bootloader flag?
- How would you ensure that the data partition is not accidentally overwritten during a rootfs update?

---

## Q4: Behavioral — You're the BSP lead for a medical device project, and during a pre-production review, the manufacturing team reveals that the PCB for the main processor board has a routing error: the I2C pull-up resistors for a critical sensor bus are connected to the wrong voltage rail (3.3V instead of 1.8V). The sensor is rated for 1.8V I2C, and the board is already in production. The project is three weeks from the start of a clinical trial. How would you handle this situation?

**Answer:** First, I'd assess the immediate risk: is the sensor actually being damaged, or is it just operating out of spec? I'd work with the hardware team to determine if the sensor's I2C pins are 5V-tolerant or if the 3.3V pull-ups could cause latch-up or overstress. If there's a risk of damage, I'd recommend halting any further board population and testing until we understand the severity.

Next, I'd evaluate mitigation options. The most direct fix would be a board re-spin, but that's not feasible in three weeks. A practical alternative might be to depopulate the pull-up resistors on the affected boards and add external pull-ups to the 1.8V rail — either on a small adapter board or by reworking the PCB. If the sensor's I2C pins are actually tolerant to 3.3V, we might be able to proceed with a documented deviation and a risk assessment, but that would need to go through the regulatory and quality process.

I'd also check whether the sensor's I2C bus is shared with other devices — if so, the wrong pull-up voltage could affect the entire bus, not just the sensor. I'd verify the logic levels of all devices on that bus to ensure they're compatible with 3.3V signaling.

In parallel, I'd initiate a formal deviation process: document the issue, assess the risk to patient safety and device functionality, and get sign-off from the relevant stakeholders (hardware, quality, regulatory, clinical). If the clinical trial can proceed with the rework or the deviation, I'd ensure the manufacturing team implements the fix on all remaining boards and that the rework is verified with appropriate testing.

Finally, I'd lead a root-cause analysis to understand how the error escaped the design review and layout checks, and implement process improvements — such as automated design rule checks for voltage domain mismatches — to prevent recurrence.

**Possible follow-ups:**
- How would you prioritize between the clinical trial schedule and the need for a proper engineering fix?
- What would you do if the sensor is already showing signs of damage on some boards?

---

## Q5: How would you approach implementing a kernel driver for a device that needs to perform a hardware-triggered DMA transfer, where the trigger comes from an external sensor's interrupt line, and the data must be processed and made available to userspace within a hard real-time deadline (e.g., 2 ms)?

**Answer:** The key challenge is ensuring that the entire path from the sensor interrupt to userspace data delivery is deterministic and bounded within the deadline. I'd start by analyzing the timing budget: the interrupt latency, the DMA setup time, the transfer time, and the time to notify and copy data to userspace.

For the interrupt path, I'd use a threaded interrupt handler with a high real-time priority, or better, a dedicated high-priority kernel thread that waits on a wait queue. The interrupt handler would be minimal — just enough to acknowledge the interrupt and wake the thread. The thread would then configure the DMA channel, arm the transfer, and block until the DMA completion interrupt fires.

For the DMA setup, I'd pre-allocate and pre-configure the DMA descriptors and buffers to avoid any allocation or setup latency in the critical path. The DMA channel would be configured for a single transfer, and the completion callback would be a lightweight function that signals a completion variable or wakes the kernel thread.

To get data to userspace within the deadline, I'd use a pre-allocated, mmap'd buffer that the driver writes into via DMA, and the userspace application would poll on a file descriptor (using `poll()` or `epoll()`) for data availability. The driver would signal readiness by writing to a wait queue or using a `poll` callback. This avoids a `read()` syscall copy, which could add latency.

I'd also need to consider the DMA buffer's cache coherency — on ARM, I'd use `dma_alloc_coherent()` or handle cache invalidation properly with `dma_sync_single_for_cpu()` after the transfer completes.

Finally, I'd verify the timing with a logic analyzer or by timestamping in the driver and userspace, and I'd ensure that the kernel's real-time scheduling (e.g., `CONFIG_PREEMPT_RT` or appropriate priority settings) is configured so that the driver's thread isn't preempted by lower-priority work.

**Possible follow-ups:**
- How would you handle the case where the sensor generates interrupts faster than the DMA transfer can complete?
- What would you do if the 2 ms deadline is not met on the first implementation — how would you profile and optimize?