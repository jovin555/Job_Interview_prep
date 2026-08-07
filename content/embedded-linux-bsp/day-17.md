# embedded-linux-bsp — Day 17

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel is not detecting one of two identical I2C sensors on the same bus, while the other works fine?

**Answer:** I'd start by narrowing down whether this is a hardware or software issue. First, I'd check the obvious: is the sensor actually powered, are the address pins set correctly, and is the device present on the bus? I'd use `i2cdetect` to scan the bus and see if the device responds at all. If it doesn't appear, I'd check the schematic and layout — a common issue is a missing pull-up on the reset line, or the sensor's address being strapped differently than the device tree expects.

If the device does appear in `i2cdetect` but the kernel driver doesn't bind, I'd look at the device tree entry. Two identical sensors on the same bus need distinct `reg` properties matching their hardware addresses. I'd verify the device tree node has the correct address, compatible string, and that the interrupt line (if used) isn't shared incorrectly with the other sensor.

Another angle: if both sensors share a reset GPIO, the driver for the working sensor might be asserting reset during probe, leaving the second sensor in reset. I'd check the driver's probe sequence and whether the reset GPIO is properly deasserted for each device.

I'd also check the kernel log for probe errors — sometimes the driver probes but fails on a register read, which could indicate a marginal I2C timing issue or a bad solder joint. In that case, I'd slow down the bus speed temporarily to see if the problem goes away, which would point to a signal integrity issue.

**Possible follow-ups:**
- What if the sensor is detected intermittently — how would you determine if it's a timing issue versus a power sequencing problem?
- How would you verify that the device tree node is actually being matched to the correct hardware instance?

---

## Q2: How would you approach designing a kernel driver for a device that needs to be accessed by both a real-time safety-critical task and a non-real-time monitoring task, where the safety-critical task must never be blocked by the monitoring task?

**Answer:** The core principle here is that the safety-critical path must never depend on a resource that the non-real-time path can hold indefinitely. I'd start by separating the access paths at the driver level.

The driver would maintain a single hardware interface, but the safety-critical task would get a dedicated, lock-free or minimal-locking access path. For example, the driver could use a kernel thread or a high-priority workqueue for the safety-critical reads, with the data placed in a lock-free ring buffer that the monitoring task reads from. The monitoring task would only ever see a snapshot of the latest data — it never blocks the hardware access itself.

If both tasks need to write to the device, I'd use a mutex with priority inheritance, or better, design the protocol so the safety-critical task uses a separate command path (e.g., a dedicated register or command byte) that doesn't require the same lock as the monitoring path. In some cases, using `mutex_lock` with `rt_mutex` semantics (which the kernel supports for real-time tasks) can prevent priority inversion.

I'd also consider whether the monitoring task even needs direct hardware access. If it only needs data, the driver can push samples to it via a read-only interface, and the monitoring task can miss samples without consequence. The safety-critical task, by contrast, would have a guaranteed worst-case access time, verified through analysis or testing.

Finally, I'd make sure the driver's interrupt handler and any DMA buffers are allocated and locked in memory to avoid page faults during the safety-critical path.

**Possible follow-ups:**
- How would you handle the case where the monitoring task needs to configure the device, and that configuration could interfere with the safety-critical operation?
- What kernel mechanisms would you use to verify that the safety-critical task meets its timing requirements?

---

## Q3: How would you approach structuring the root filesystem for an embedded Linux medical device that needs to support over-the-air (OTA) updates with a rollback mechanism, while ensuring that patient data and configuration settings survive the update process?

**Answer:** I'd use a dual-partition (A/B) scheme for the root filesystem, with a separate persistent data partition. The layout would be something like:

- **Bootloader** (read-only, or with a small writable environment)
- **Partition A** — root filesystem (read-only at runtime)
- **Partition B** — root filesystem (read-only at runtime)
- **Data partition** — writable, holds patient data, configuration, logs

The bootloader would track which partition is active and which is the "known good" one. On boot, it would attempt the active partition; if the kernel fails to mount the rootfs or a health check fails within a timeout, the bootloader falls back to the other partition.

The root filesystem itself should be mounted read-only to prevent corruption and to make the update process atomic — you write the new image to the inactive partition, verify its integrity (checksum/signature), then flip the boot flag. The data partition is mounted read-write and is never touched during an update.

For the data partition, I'd use a journaling filesystem like ext4 or UBIFS (for NAND flash) to survive power loss. I'd also consider storing configuration in a structured way (e.g., a SQLite database or versioned key-value store) so that if the application needs to migrate data after an update, it can do so cleanly.

The update process itself would be: download the image to a staging area, verify the signature, write to the inactive partition, update the bootloader flag, and reboot. If the new partition fails to boot or the application doesn't report healthy within a timeout, the bootloader reverts to the previous partition automatically.

**Possible follow-ups:**
- How would you handle the case where the update succeeds but the application crashes on startup — how would the system detect that and roll back?
- What if the data partition format needs to change between versions — how would you handle migration?

---

## Q4: How would you approach debugging a situation where a custom board running Linux boots successfully, but the Ethernet interface works only when the cable is plugged in before power-on — not when the cable is plugged in after boot?

**Answer:** This is a classic PHY link-detection issue. The most common cause is that the PHY's link status is only checked at driver probe time, and if no cable is present, the PHY reports "link down" and the driver never re-checks. When the cable is plugged in later, the PHY doesn't generate an interrupt (or the interrupt isn't wired/enabled), so the driver never notices.

I'd start by checking whether the PHY interrupt line is connected to the SoC and properly configured in the device tree. If the PHY has an interrupt pin, I'd verify it's wired to a GPIO that can wake the MAC driver. If it's not connected, the driver needs to poll the PHY status periodically — most MAC drivers have a `phy_polling` or link-timer mechanism.

Next, I'd check the PHY driver's `read_status` function. Some PHYs require a specific register read sequence to latch the link status, and if the driver doesn't handle that correctly, it might miss a link-up event.

I'd also check the MDIO bus — if the PHY is on a separate MDIO bus that's powered down or clock-gated after boot, the driver might not be able to read the PHY status when the cable is plugged in.

Finally, I'd test with `ethtool` to manually check the link status and force a renegotiation. If `ethtool -s eth0 autoneg on` brings the link up, that confirms the driver isn't detecting the change automatically. From there, I'd look at the driver's interrupt handling or polling configuration.

**Possible follow-ups:**
- How would you determine whether the issue is in the PHY driver, the MAC driver, or the device tree configuration?
- What if the PHY interrupt is connected but the driver still doesn't respond — how would you debug that?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a pre-production review, the hardware team reveals that they need to change the main processor's power supply from a fixed-voltage regulator to a programmable one (e.g., I2C-controlled) to meet new efficiency requirements. The software team has already completed the kernel and driver development for the fixed regulator, and the change will require a new driver, device tree changes, and potentially a different boot sequence. The project is five weeks from the start of a clinical trial. How would you handle this situation?

**Answer:** First, I'd acknowledge that this is a significant change, but I'd resist the urge to push back purely on schedule grounds. The hardware team presumably has a valid reason — efficiency requirements are often tied to thermal or battery-life constraints that matter for the clinical trial.

I'd start by calling an immediate cross-functional meeting with hardware, software, and project management to understand the full scope. Key questions: Is the programmable regulator a drop-in replacement pin-wise, or does it require PCB changes? Does the bootloader need to configure it before the kernel starts (e.g., to set the core voltage), or can the kernel handle it? What's the risk if the regulator isn't configured correctly — could it damage the processor?

From a BSP perspective, I'd assess the actual work: writing a regulator driver (or using the existing kernel regulator framework with a new device tree binding), updating the device tree to describe the regulator and its consumers, and potentially adding early initialization in U-Boot if the kernel needs the correct voltage before it can run. The regulator framework in Linux is well-established, so this is likely a matter of adding a new driver chip and updating the DT, not a ground-up effort.

I'd also evaluate the testing burden. The change affects power sequencing, which is critical for reliability. I'd want to run at least a subset of the existing power-cycling and stress tests, plus verify that all peripherals still work at the new voltage levels.

For the schedule, I'd propose a phased approach: first, get a minimal working configuration (regulator set to the same voltage as the fixed one) to unblock the clinical trial, then optimize the voltage scaling later if needed. I'd also ask the hardware team if they can provide an engineering sample with the new regulator early, so we can start bring-up before the production boards arrive.

Finally, I'd document the risk and the mitigation plan, and make sure the project manager understands the trade-offs — we can meet the deadline, but we may need to accept a reduced feature set (e.g., no dynamic voltage scaling initially) to do so safely.

**Possible follow-ups:**
- How would you handle the situation if the hardware team says the new regulator requires a different boot sequence that the bootloader must handle, and the bootloader team is already at capacity?
- What specific tests would you insist on before signing off on this change for the clinical trial?