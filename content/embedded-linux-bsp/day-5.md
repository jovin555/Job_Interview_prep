# embedded-linux-bsp — Day 5

## Q1: How would you approach debugging a situation where a custom SPI NOR flash device is detected correctly in U-Boot but fails to mount as the root filesystem in Linux?

**Answer:** This is a classic boot-stage mismatch problem. First, I'd verify that the kernel's SPI controller driver and the SPI NOR flash driver are both enabled and correctly configured in the kernel (check `CONFIG_SPI`, `CONFIG_MTD_SPI_NOR`, and the specific flash chip driver). The fact that U-Boot sees it suggests the hardware connection is sound, so the issue is likely in the kernel configuration or device tree.

I'd start by checking the kernel boot log for SPI-related messages using `dmesg | grep spi` and `dmesg | grep mtd`. If the SPI controller isn't probed, I'd verify the device tree node for the SPI controller has `status = "okay"` and that the clock and pinmux references are correct. For the flash chip itself, I'd check that the `compatible` string in the device tree matches exactly what the kernel driver expects — U-Boot may use a different or more lenient matching mechanism.

Next, I'd check if the MTD subsystem creates the correct block device (`/dev/mtdblock0` or similar). If the MTD device appears but the root filesystem mount fails, the issue could be in the kernel command line: the `root=` parameter might point to the wrong partition or use an incorrect filesystem type. I'd verify the partition layout in the device tree matches what U-Boot programmed, and that `CONFIG_CMDLINE_PARTITION` or the fixed-partitions binding is set up correctly.

If everything looks correct, I'd try manually mounting from the U-Boot shell using `sf probe` and `sf read` to load the kernel and a small initramfs, then inspect the flash contents from Linux userspace to confirm the filesystem is intact.

**Possible follow-ups:** How would you add debug print statements to the SPI NOR driver to trace where the probe fails? What if the flash works with a different kernel version — how would you bisect the kernel change that broke it?

---

## Q2: You're designing a BSP for a system that uses a dual-core Cortex-A processor in asymmetric multiprocessing (AMP) mode, where one core runs Linux and the other runs a bare-metal real-time application. How would you handle memory partitioning and inter-core communication?

**Answer:** The first consideration is memory isolation. I'd partition the system memory at the hardware level using the memory protection unit (MPU) or MMU configuration, and define this in the bootloader. Typically, I'd reserve a contiguous region of DRAM for the bare-metal core using a `reserved-memory` node in the device tree, which prevents Linux from using that region. The bootloader would load the bare-metal firmware into that region and release the secondary core from reset.

For inter-core communication, I'd implement a simple shared memory protocol with a ring buffer or mailbox structure in the reserved memory region. A common approach is to use a small shared memory area with a status register (e.g., using the ARM doorbell mechanism or a dedicated GPIO interrupt) to signal new data. The Linux side would have a kernel module that maps the shared memory region via `ioremap` and registers an interrupt handler for the doorbell. The bare-metal side would poll or use its own interrupt controller.

I'd also need to handle cache coherency carefully. If the two cores share a cache hierarchy, I'd need to ensure proper cache maintenance operations (cache flush/invalidate) are performed before and after accessing shared memory. If they have separate caches, I'd use non-cacheable memory for the shared region or implement explicit cache synchronization.

The boot sequence would be: U-Boot loads both the Linux kernel and the bare-metal firmware, sets up the resource partition, releases the secondary core, and then boots Linux on the primary core. The bare-metal firmware would start executing immediately from its reset vector.

**Possible follow-ups:** How would you handle shared peripherals like a UART that both cores might want to use? What if the bare-metal core needs to access a DMA controller that Linux also manages?

---

## Q3: How would you approach writing a kernel module that controls a GPIO line to reset an external sensor, ensuring the reset sequence meets the sensor's timing requirements (e.g., 10ms low, then 50ms high before communication)?

**Answer:** I'd implement this as a platform driver that uses the GPIO descriptor API (`gpiod_*` functions) for modern, device-tree-aware GPIO control. The first step is to add a device tree binding for the sensor that includes a `reset-gpios` property, so the GPIO number and flags are specified in the device tree rather than hardcoded.

In the driver's probe function, I'd request the GPIO using `devm_gpiod_get_optional()` with the `GPIOD_OUT_LOW` flag to ensure the sensor starts in reset. For the timing, I'd use kernel delay functions: `msleep()` for the 10ms reset pulse (since it's > 1ms, a busy-wait isn't appropriate). After releasing the reset by setting the GPIO high with `gpiod_set_value()`, I'd use another `msleep(50)` before attempting to communicate.

I'd structure the reset as a helper function that can be called from probe and also exposed via a sysfs attribute or ioctl for runtime resets. The function would use `gpiod_set_value()` to toggle the line, with appropriate error handling if the GPIO request fails.

For power management, I'd implement suspend/resume callbacks that re-apply the reset sequence on resume, since the sensor's state may be lost during system sleep. I'd also consider using the `devm_*` managed API so that the GPIO is automatically released if the driver is removed.

**Possible follow-ups:** How would you handle the case where the sensor's reset timing requires microsecond precision? What if the sensor needs a specific power sequencing relative to other components on the board?

---

## Q4: You're debugging a system where the kernel boots successfully, but the root filesystem on an eMMC device becomes read-only after a few hours of operation. The logs show "I/O error" messages. How would you approach this?

**Answer:** This sounds like the eMMC device is encountering write failures and the kernel is remounting the filesystem as read-only to prevent data corruption. I'd start by examining the full kernel log around the time of the first I/O error using `dmesg` to identify the specific error type — is it a command timeout, CRC error, or a hardware-level write failure?

I'd check the eMMC health using the device's extended CSD register, which contains fields like "life time estimation" and "pre EOL information" that indicate wear level. If the device is near end-of-life, the solution is hardware replacement. If it's relatively new, I'd look at the electrical interface: check the eMMC clock frequency in the device tree — it might be running too fast for the board layout, causing signal integrity issues that manifest as intermittent errors.

I'd also verify the eMMC voltage supply. Some eMMC devices support multiple voltage modes (1.8V and 3.3V), and if the board is supplying 3.3V but the device is configured for 1.8V signaling, this can cause failures. The kernel boot log should show the negotiated voltage.

On the software side, I'd check if the eMMC driver is using the correct timing mode (HS200, HS400, etc.) and whether tuning was successful. I'd try forcing a lower speed mode in the device tree (e.g., `mmc-hs200-1_8v` instead of `mmc-hs400-1_8v`) to see if the errors stop. I'd also ensure that the eMMC power management features like `power-off-in-suspend` are configured correctly.

If the errors are specific to certain blocks, I'd use `badblocks` to scan the device and check for physical defects. Finally, I'd review the filesystem mount options — using `noatime` and appropriate journaling settings can reduce write wear.

**Possible follow-ups:** How would you implement a monitoring mechanism to detect early signs of eMMC degradation in a medical device? What filesystem features (like F2FS or UBIFS) might be more suitable for eMMC in write-intensive applications?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a pre-certification review, the regulatory engineer points out that your bootloader doesn't have a mechanism to verify the integrity of the kernel image before booting. The project is already in late-stage testing, and changing the boot flow could delay the schedule by weeks. How would you handle this?

**Answer:** First, I'd acknowledge the concern as valid — medical devices absolutely need verified boot to ensure only authorized, untampered software runs. I wouldn't dismiss it as a schedule issue. I'd ask the regulatory engineer to clarify the specific requirement: is it a full cryptographic signature verification, or would a simpler integrity check like a SHA-256 hash comparison against a stored value suffice? Understanding the minimum acceptable solution is critical.

Next, I'd assess what we can implement with minimal bootloader changes. If we're using U-Boot, it already has verified boot support via FIT images with hash verification. I'd check if our current boot flow uses FIT images — if not, migrating to them might be less invasive than implementing a custom solution. I'd also look at whether we can add a hash check in the existing boot script without modifying the bootloader binary itself, by storing the expected hash in a protected region of flash.

I'd then propose a phased approach to the project manager and regulatory team:
- **Phase 1 (immediate):** Implement a basic hash verification in the boot script, with a fallback to a known-good recovery image if verification fails. This can be done in a few days.
- **Phase 2 (next release):** Implement full cryptographic signature verification using U-Boot's verified boot mechanism, which provides stronger security guarantees.

I'd also discuss whether the current boot flow can be grandfathered under existing risk analysis, with the understanding that the full solution will be in place before the next regulatory submission. I'd document the gap in the risk management file and create a clear action plan with timelines.

Throughout this, I'd maintain open communication with the regulatory team — they're not the enemy, they're ensuring patient safety. I'd involve them in reviewing the proposed solution to confirm it meets the intent of the requirement, even if it's not the full implementation.

**Possible follow-ups:** How would you test that the boot integrity check doesn't introduce a single point of failure that could brick the device? What if the regulatory engineer insists on full cryptographic verification before certification — how would you negotiate the timeline?