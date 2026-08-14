# embedded-linux-bsp — Day 24

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a GPIO-controlled peripheral (e.g., a sensor power switch) doesn't respond when toggled from userspace, even though the GPIO chip is detected and the pin is exported correctly?

**Answer:** I'd approach this systematically, starting with the simplest explanations before moving to more complex ones. First, I'd verify the GPIO is actually being toggled at the hardware level — using a logic analyzer or oscilloscope on the physical pin — because the software stack might be reporting success while the pin isn't changing state. If the pin isn't toggling, I'd check the pin mux configuration in the device tree; on many SoCs, a GPIO pin might be muxed to a different peripheral function by default, and the pinctrl node needs to explicitly configure it as a GPIO. I'd also verify the GPIO controller's clock is enabled and that the bank's power domain is active.

If the pin is toggling but the peripheral isn't responding, I'd check the electrical path — pull-up/pull-down resistors, level shifters, or series resistors that might be attenuating the signal. I'd also verify the polarity: the device tree might specify `GPIO_ACTIVE_LOW` when the hardware is actually active-high, or vice versa. This is a common source of confusion, especially when the device tree binding documentation is ambiguous.

Another angle: if the GPIO is on an I2C or SPI expander rather than the SoC's built-in controller, I'd check whether the bus communication is reliable — a marginal I2C bus (wrong pull-up values, excessive capacitance) could cause intermittent or failed writes to the expander. I'd also check whether another driver or kernel subsystem has claimed the GPIO line, which would cause the request to fail silently or the toggle to be ignored. Finally, I'd verify the userspace API being used — the legacy sysfs interface and the newer gpiochip character device interface have different semantics, and mixing them can lead to unexpected behavior.

**Possible follow-ups:**
- How would you determine whether the issue is in the device tree pinctrl configuration versus the GPIO driver itself?
- What kernel interfaces would you use to inspect the current state of a GPIO line and its configuration from userspace?

---

## Q2: How would you approach designing a kernel driver for a device that needs to perform a hardware-triggered DMA transfer, where the trigger comes from an external sensor's interrupt line, and the data must be processed and made available to userspace within a hard real-time deadline (e.g., 2 ms)?

**Answer:** This is fundamentally about minimizing latency and jitter across the entire data path. I'd start by analyzing the timing budget: 2 ms is generous for a single DMA transfer on most modern SoCs, but the challenge is the end-to-end path — interrupt latency, DMA setup, transfer completion notification, and userspace wake-up. I'd break the design into stages.

For the interrupt path, I'd request the sensor's interrupt as a threaded IRQ with `IRQF_TRIGGER_RISING` (or appropriate edge), and in the top half, I'd do the minimal work needed to trigger the DMA — writing the DMA descriptor and issuing the start command. The actual data processing would happen in the bottom half or in a dedicated kernel thread. Using `request_irq` with `IRQF_NO_SUSPEND` might be necessary if the system can enter low-power states.

For the DMA engine, I'd use the standard DMA engine API (`dma_request_chan`, `dmaengine_prep_slave_single`, `dmaengine_submit`, `dma_async_issue_pending`) rather than touching the DMA controller registers directly — this keeps the driver portable across SoCs. I'd use a cyclic or double-buffered DMA setup so that while one buffer is being filled, the previous buffer can be processed, avoiding gaps between transfers. The DMA completion callback would run in interrupt context, so I'd keep it minimal — perhaps just waking a wait queue or completing a completion object.

For the userspace interface, I'd use a character device with `read()` blocking on a wait queue, or better, use `poll()`/`epoll()` so the application can wait on multiple events. I'd also consider using `O_NONBLOCK` with a ring buffer in the kernel so that data isn't lost if userspace is temporarily delayed. The key is to avoid copying data unnecessarily — if the DMA buffer is cache-coherent or properly aligned, I could use `dma_alloc_coherent` and mmap it to userspace, eliminating a copy.

For the real-time aspect, I'd ensure the kernel is configured with `CONFIG_PREEMPT_RT` if possible, or at least `CONFIG_PREEMPT` enabled. I'd also check that the interrupt isn't shared with other devices, and I'd consider setting the IRQ affinity to a dedicated core if the SoC has multiple cores. Finally, I'd profile the actual latency with `ftrace` or `perf` to verify the 2 ms budget is met under worst-case conditions — interrupt storms, memory pressure, or concurrent DMA activity.

**Possible follow-ups:**
- How would you handle the case where the sensor generates interrupts faster than the DMA can be re-armed?
- What are the trade-offs between using a threaded IRQ versus a hard IRQ for this scenario?

---

## Q3: How would you approach structuring a Yocto-based BSP for a product that has two hardware variants — one with a touchscreen display and one without — where the touchscreen variant requires additional userspace libraries (e.g., for gesture recognition) and a different kernel configuration (e.g., touchscreen driver enabled)?

**Answer:** I'd structure this using Yocto's layer and machine concepts to keep the variants cleanly separated. The key principle is that machine-specific configuration belongs in the machine configuration file, while package and image differences belong in the image recipes or distro configuration.

First, I'd create two machine configuration files — `myproduct-touch.conf` and `myproduct-base.conf` — both inheriting from a common `myproduct-common.inc` that defines the shared SoC, bootloader, and kernel configuration. The touchscreen variant would set `MACHINE_FEATURES += "touchscreen"` and possibly define a different kernel configuration fragment. For the kernel, I'd use kernel config fragments: a base fragment with common drivers, and a touchscreen-specific fragment that enables the touch controller driver and any related input subsystem options. These would be conditionally included based on the machine — for example, using `SRC_URI_append_machine-touch` to add the fragment.

For the userspace libraries, I'd use `MACHINE_FEATURES` to conditionally include packages in the image. In the image recipe, I'd write something like `IMAGE_INSTALL:append = ' ${@bb.utils.contains("MACHINE_FEATURES", "touchscreen", "libgesture libtouch-calibration", "", d)}'`. Alternatively, I could create a custom packagegroup — `packagegroup-myproduct-touch` — that pulls in all the touchscreen-related libraries and tools, and include that packagegroup conditionally in the image.

For the root filesystem, I'd use a common base image recipe and then create two derived image recipes — `myproduct-image-touch.bb` and `myproduct-image-base.bb` — each inheriting from a common `myproduct-image-common.bb`. This keeps the image customization explicit and makes it clear which image is built for which variant. I'd also consider using `EXTRA_IMAGE_FEATURES` for debug tools that should only appear in development builds.

The device tree would also differ between variants — the touchscreen variant would include the touch controller node and possibly different pin muxing. I'd handle this by having the kernel recipe build both device trees and select the appropriate one in the bootloader configuration, or by using a device tree overlay that's applied at boot. In U-Boot, I'd set the `fdtfile` environment variable based on the hardware revision detected at runtime, or use a hardware strap pin to select the correct device tree.

**Possible follow-ups:**
- How would you handle the case where the two variants share the same kernel binary but need different device trees?
- How would you ensure that the touchscreen-specific libraries don't bloat the base variant's image?

---

## Q4: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel log shows "Failed to request IRQ" for a device that worked on the previous board revision?

**Answer:** This is a classic regression between board revisions, and I'd approach it by comparing what changed electrically and logically between the two revisions. The "Failed to request IRQ" message typically means `request_irq()` returned an error — usually `-EBUSY` (the IRQ is already claimed) or `-EINVAL` (invalid IRQ number). I'd start by checking the full kernel log to see which IRQ number is failing and whether any other driver has already claimed it.

First, I'd verify the device tree: the interrupt property might reference a different GPIO bank or interrupt controller on the new revision. If the hardware team moved the device's interrupt line to a different pin, the device tree needs to be updated accordingly. I'd check `/proc/interrupts` to see which IRQs are already registered and whether there's a conflict. I'd also check the GPIO controller's interrupt settings — on many SoCs, GPIO interrupts need to be enabled in the GPIO controller's interrupt mask register, and the pinctrl configuration must set the pin as an interrupt input.

Another possibility is that the IRQ number is valid but the interrupt controller (GIC or GPIO controller) isn't properly initialized. This could happen if the interrupt controller's device tree node is missing or misconfigured, or if the interrupt controller driver failed to probe. I'd check `dmesg` for errors from the interrupt controller driver itself.

I'd also consider the electrical side: if the device's interrupt line is floating or has incorrect pull-up/pull-down configuration, the device might be generating spurious interrupts before the driver requests the IRQ, causing the IRQ to be disabled by the kernel's spurious interrupt detection. This would manifest as the IRQ being unavailable or the device appearing to be in a bad state.

Finally, I'd check whether the driver is being probed at the right time — if the device's interrupt controller (e.g., an I2C GPIO expander with interrupt support) hasn't probed yet, the IRQ domain might not be available, causing `irq_of_parse_and_map()` to fail. This is a common issue with probe ordering, and the fix might be to add a dependency in the device tree (`interrupts-extended` with a phandle to the expander) or use deferred probing.

**Possible follow-ups:**
- How would you use `/proc/interrupts` and `/sys/kernel/debug/gpio` to narrow down the issue?
- What device tree changes would you look for when comparing the two board revisions?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a pre-production review, the hardware team reveals that they need to change the main processor's boot mode strap resistors to accommodate a new flash part. The change means the processor will boot from a different interface (e.g., from SPI NOR to eMMC), and the bootloader and kernel configurations are already tuned for the current boot source. The project is six weeks from the start of a clinical trial. How would you handle this situation?

**Answer:** I'd start by acknowledging that this is a significant change with real schedule risk, but it's not necessarily a blocker. The first step would be to understand the full scope: is this a change in the boot source only, or does it also affect the root filesystem location, the bootloader's storage driver, and the kernel's root device? I'd ask the hardware team for the new flash part's datasheet and the exact strap configuration, and I'd verify whether the new eMMC is already supported by the current bootloader and kernel versions.

Next, I'd assess the technical impact. For U-Boot, I'd need to ensure the eMMC driver is enabled and that the boot sequence (`bootcmd`) is updated to load the kernel from eMMC instead of SPI NOR. For the kernel, I'd need to update the root device in the device tree or kernel command line (`root=/dev/mmcblk0p2` instead of `root=/dev/mtdblock3`). I'd also check whether the bootloader needs to be stored on the eMMC's boot partition, which requires configuring the eMMC's boot bus width and boot partition enable bits — this is a one-time setup that might need to be done via a separate flashing tool.

I'd then create a risk mitigation plan. The key question is whether we can validate the new boot path before the clinical trial. If we have prototype boards with the new strap configuration, I'd prioritize getting a bootable image onto one of them within a few days. If not, I'd ask the hardware team whether the straps can be temporarily overridden (e.g., by soldering jumpers) to test the new configuration on existing boards. I'd also prepare a fallback: if the eMMC boot path proves unreliable, can we keep the SPI NOR as a secondary boot source with a fallback mechanism in U-Boot?

For the schedule, I'd be transparent with the project manager about the risks and the validation steps needed. I'd propose a two-track approach: track A is getting the eMMC boot working and validated; track B is preparing a contingency plan (e.g., keeping SPI NOR for the clinical trial and switching to eMMC for production). I'd also involve the manufacturing team early to understand their flashing process — if they're already set up to program eMMC on the production line, that's a plus; if not, we need to develop that capability.

Finally, I'd document everything — the strap configuration, the boot sequence changes, the validation results, and the fallback plan — and make sure the regulatory team is aware of the change, since it affects the device's firmware update and recovery procedures, which are relevant to the design history file. I'd also ensure that the change is properly tracked in the risk management documentation, since a boot failure in the field could have patient safety implications.

**Possible follow-ups:**
- How would you prioritize the validation steps if you only had one week before the clinical trial?
- What specific U-Boot and kernel configuration changes would you need to make, and how would you verify them?