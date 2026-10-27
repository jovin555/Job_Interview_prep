# embedded-linux-bsp — Day 98

## Q1: How would you approach deciding whether a peripheral driver should be built into the kernel image versus built as a loadable module, for a device that must be functional before the root filesystem is mounted?

**Answer:** The deciding factor is dependency timing, not preference. Anything that must be operational before the root filesystem exists — the storage controller for that rootfs, the console UART, the clock/regulator/pinctrl providers those depend on, and any driver whose firmware or calibration data lives on that rootfs — has to be built in (`=y`). A loadable module (`=m`) can only be loaded after userspace and the module loader are running, so it is structurally incapable of serving a pre-rootfs dependency.

The reasoning chain I'd walk through: first, map the boot-critical path from reset to `init` and mark every driver on it as built-in. Second, look at probe ordering — a driver that is a supplier to another built-in driver (a PMIC regulator feeding the eMMC, a clock controller feeding the display) must also be built in, otherwise the consumer defers forever. Third, consider firmware loading: if a driver needs a firmware blob from `/lib/firmware`, it either has to move to an initramfs or be built in with the firmware embedded, because at early boot there is no filesystem to read from. Fourth, weigh the practical trade-offs for everything off the critical path — modules keep the kernel image small, speed up rebuilds during development, and let you reload a driver without rebooting, which is valuable for debugging. For production, though, a medical device benefits from a deterministic, minimal set of built-ins and a short, auditable module list, because every loadable module is another thing that can fail to load silently.

A useful sanity check is to ask: "If this driver fails to load, does the system still reach a state where it can report the failure?" If the answer is no, it belongs in the kernel image.

**Possible follow-ups:** How would you verify at build time that no boot-critical driver accidentally ended up as a module? What changes if the rootfs is on an initramfs rather than a fixed partition?

## Q2: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is called and returns success, yet the device is completely non-functional — no errors in the log, no timeouts, just silence?

**Answer:** "Probe succeeded but nothing works" usually means the driver believed it configured the hardware, but the hardware disagrees — so I'd split the investigation into what the driver *thinks* it did versus what the silicon *actually* shows.

First, instrument the driver itself: add temporary logging of every register write and read-back in probe, and confirm the values you read back match what you wrote. A very common failure is that the register writes go somewhere unexpected — wrong base address from the device tree, an address translation issue, or a clock that isn't actually running so writes are dropped. Reading back a known register (an ID register is ideal) is the fastest way to prove the bus path is real.

Second, verify the resources the driver assumed: is the clock actually enabled and at the expected rate (`clk_summary`), is the regulator on and at the right voltage, is the reset line deasserted, is the pinmux set to the peripheral function rather than GPIO? A driver can return success while all of these are silently wrong, because nothing in the driver checks them unless you wrote it to.

Third, check the interrupt path separately from the data path. If the device is interrupt-driven and the IRQ never fires, the driver looks healthy but never does anything. Confirm the interrupt is actually asserted at the pin, that the interrupt controller mapping in the device tree matches the schematic, and that the handler is registered on the right line.

Fourth, go below the driver: use a scope or logic analyzer on the actual bus lines (I2C/SPI) to see whether transactions are physically happening. If the driver logs "wrote 0x42 to reg 0x10" but the analyzer shows nothing on the wire, the problem is upstream of the driver — pinmux, clock, or power. If the analyzer shows the transaction but the device doesn't respond, the problem is the device or its power/enable.

Finally, compare against a known-good reference: does the same driver work on an eval board or previous revision? Diffing the device tree and the schematic between working and non-working hardware usually surfaces the discrepancy quickly.

**Possible follow-ups:** How would you distinguish a pinmux problem from a clock problem without a scope? What would you check first if the device works after a warm reboot but not a cold boot?

## Q3: How would you approach structuring a Yocto BSP so that a board-specific kernel configuration fragment can be applied cleanly without forking the vendor's kernel recipe?

**Answer:** The goal is to keep the vendor's kernel recipe untouched and layer your changes on top through the mechanisms Yocto already provides, so that a vendor BSP update can be pulled in without a merge conflict.

The cleanest approach is a `.bbappend` in your own layer that adds a configuration fragment via `SRC_URI` using the `file://` + `kernel-config` mechanism, plus `KERNEL_CONFIG_FRAGMENTS` (or the older `SRC_URI` fragment convention depending on the kernel class version). The fragment file contains only the options you need to change — `CONFIG_FOO=y`, `CONFIG_BAR=m`, and `# CONFIG_BAZ is not set` for disables — and Yocto's `merge_config.sh` applies it on top of the vendor's `defconfig`. This means the vendor's base config stays authoritative, and your delta is a small, reviewable, version-controllable file.

Key practices: keep the fragment minimal and scoped to the board (don't restate options the vendor already sets correctly, because that creates drift); name it after the board or feature so it's obvious what it's for; and put it in a board-specific layer rather than a shared one if only one variant needs it. If you have multiple variants sharing a SoC, use a common fragment plus per-variant fragments composed in the right order, so the shared baseline isn't duplicated.

For anything the fragment mechanism can't express — a patch to Kconfig itself, or a driver that isn't upstream — use a `.bbappend` with a `SRC_URI` patch and `FILESEXTRAPATHS` pointing at your layer, again without touching the vendor recipe. The discipline is: your layer owns the delta, the vendor layer owns the base, and `bitbake -e virtual/kernel` plus the generated `.config` in the workdir let you verify the merge actually produced what you intended.

**Possible follow-ups:** How would you detect that a vendor BSP update silently changed an option your fragment depends on? When would you choose a full custom `defconfig` over fragments, and what are the maintenance costs?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core principle is that the real-time path must never contend for a lock, buffer, or bus that the logging path can hold. So the design separates the two paths structurally rather than trying to make one lock "fair."

On the real-time side, the driver exposes an interface that the RT task can use without blocking: a pre-allocated, lock-free ring buffer in kernel memory that the RT task writes into (or that DMA fills), with the RT task only ever doing a bounded, non-blocking operation — ideally a single `memcpy` into a slot it owns, or an atomic index update. No mutex, no sleeping allocation, no waiting on the logging consumer. If the RT task is in userspace, this might be a `mmap`'d shared buffer plus an `ioctl` that never blocks, or a dedicated char device read that returns immediately.

On the logging side, a separate consumer — a kernel thread, a workqueue, or a userspace daemon — drains the ring buffer at its own pace and writes to storage or the network. If the consumer falls behind, the ring buffer either overwrites oldest data (acceptable for logging) or drops with a counter, but it never back-pressures the producer. The two sides communicate only through the ring buffer's atomic indices, so the logging task's latency is invisible to the RT path.

The subtle parts: memory barriers around the index updates so the consumer never reads a partially written slot; cache coherency if DMA is involved (the RT path and the DMA engine must agree on ownership of each buffer); and making sure the logging path's storage I/O (which can block for milliseconds) happens entirely on the consumer side, never inside a context the RT task waits on. I'd also give the RT path its own interrupt or polling mechanism so it isn't sharing an IRQ handler that the logging path can lengthen.

The verification is to measure worst-case latency of the RT access while the logging path is deliberately saturated — if the RT path's timing degrades when logging is busy, the separation isn't real.

**Possible follow-ups:** How would you size the ring buffer, and what would you do when the consumer can't keep up? How does this change if the RT task runs on a separate core in an AMP configuration?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** I'd treat this as a coordination and risk-management problem rather than a purely technical one, because both teams are right about their own constraints and the real question is how to change something safety-relevant without breaking a dependency the factory depends on.

First, I'd get the facts on the table: exactly which pins the new peripheral needs, whether the UART can move to a pinmux group that's electrically equivalent (same peripheral function, just different pads), and what specifically the manufacturing line uses the early console for — is it a hard requirement during every boot, or a diagnostic aid used during bring-up and test? That distinction changes the risk enormously.

Second, I'd separate the change into stages so it isn't a big-bang switch. The device tree and bootloader changes can be prepared and validated on a bench unit while the current pinmux remains the default. If the SoC supports it, I'd look at whether the bootloader can select the console pinmux at runtime based on a strap or a build variant, so the factory image keeps the known-good console and the new peripheral variant gets its own configuration. That way the manufacturing dependency isn't broken while the change is proven.

Third, I'd bring the manufacturing and test stakeholders into the review early rather than letting software and hardware negotiate it between themselves — the people who actually depend on the console output should confirm what "breaking" means and whether a documented alternative (a test point, a different debug header, a factory-test image) satisfies them.

Fourth, I'd insist on a validation plan: boot the new pinmux on multiple units, confirm the console works from the very first bootloader stage through userspace, and confirm the new peripheral functions. Only after that would the change become the default, with the old configuration retained as a fallback until the factory has signed off.

Throughout, I'd keep the tone collaborative — the hardware team has a real pin-budget problem, the software team has a real regression risk, and my job is to find the sequencing that lets both be true rather than picking a winner in the meeting.

**Possible follow-ups:** What would you do if the SoC doesn't support runtime pinmux selection for the console? How would you document this decision so it's traceable for regulatory review?