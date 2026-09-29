# embedded-linux-bsp — Day 70

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is deferred indefinitely because a supplier it depends on never becomes available — with no obvious error in the kernel log?

**Answer:** Deferred probe is one of the more frustrating classes of bring-up bugs precisely because it's designed to be quiet — the kernel intentionally suppresses repeated deferral messages to avoid log spam, so "no obvious error" is expected behavior, not a sign that nothing is wrong. The first step is to make the invisible visible: enable `initcall_debug` and dynamic debug for the driver core (`dyndbg="file drivers/base/dd.c +p"` or the equivalent via debugfs), which will surface the `-EPROBE_DEFER` returns and the supplier names being waited on. From there, I'd check `/sys/kernel/debug/devices_deferred` (or the sysfs equivalent on the kernel version in use) to see exactly which device is stuck and what it's waiting for.

Once I know the supplier, the question becomes *why* it never becomes available. Common causes: the supplier's own `probe()` is itself deferred in a chain (so I need to walk the chain to its root), the supplier is disabled in the device tree (`status = "disabled"`), the supplier's driver isn't built into the kernel or loaded as a module, or the phandle in the consumer's DT node points at the wrong node. I'd verify the DT with `dtc` decompilation and cross-check phandles against the supplier nodes. If the supplier is a regulator or clock, I'd also check whether its own dependencies (parent clock, parent regulator, I2C bus) are satisfied — a regulator on an I2C bus that itself hasn't probed will silently block everything downstream.

If the chain is genuinely circular or the ordering is wrong, the fix is usually in the device tree (correct `status`, correct phandles, correct `depends-on` style properties) or in the driver (returning `-EPROBE_DEFER` only when the supplier is truly not ready, not on transient errors). I'd also add a timeout-based diagnostic in development builds so that a stuck deferral eventually logs a warning rather than hanging forever.

**Possible follow-ups:**
- How would you distinguish a genuine deferred-probe cycle from a supplier that simply hasn't been built into the kernel?
- What's the risk of returning `-EPROBE_DEFER` too liberally in a driver, and how would you bound it?

## Q2: You're structuring a Yocto BSP for a product family where several boards share a common SoC and vendor BSP but differ in peripherals, device tree, and userspace packages. How would you organize the layers and recipes?

**Answer:** The guiding principle is to separate what's common from what varies, and to make the varying parts additive rather than forks. I'd typically use three layers: a **vendor BSP layer** (untouched, pulled in as-is), a **common product layer** that captures the shared SoC configuration, kernel recipe, bootloader recipe, and base image — everything that's true for every board in the family — and a **per-board layer** (or per-board `MACHINE` configuration within a single board layer) that adds only the deltas: the board's device tree, its `MACHINE.conf` with the right `KERNEL_DEVICETREE`, `SERIAL_CONSOLES`, and any board-specific kernel config fragments.

For the device tree, I'd keep a common `.dtsi` in the common layer and have each board's `.dts` include it and override only the nodes that differ. For kernel configuration, I'd use config fragments (`*.cfg` files applied via `SRC_URI`) rather than editing the defconfig, so each board's additions are visible and reviewable. For userspace, I'd use `IMAGE_FEATURES`, `IMAGE_INSTALL`, and `PACKAGE_EXCLUDE` in the board's `MACHINE.conf` or in a board-specific image recipe that `require`s a common base image.

The key discipline is: never fork the vendor's kernel or bootloader recipe. If a patch is needed, add it via a `.bbappend` in the common layer with a clear name, and keep the patch set minimal and rebaseable. This makes kernel version bumps a matter of rebasing a small patch set rather than reconciling a fork.

**Possible follow-ups:**
- How would you handle a board that needs a different kernel version from the rest of the family?
- What's your approach to keeping the common layer from accumulating board-specific hacks over time?

## Q3: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path holds. That rules out a shared mutex or a single-threaded workqueue that both paths funnel through. The design I'd reach for is a **lock-free or minimally-contended handoff**: the real-time path (typically an interrupt handler or a high-priority threaded IRQ) writes into a pre-allocated ring buffer using a single-producer/single-consumer pattern with atomic head/tail indices, and the logging path reads from the other end of that ring buffer at its own pace. The real-time path never waits for the logging path; if the ring is full, the real-time path either overwrites the oldest entry (if the data is telemetry) or drops and increments a counter (if the data is safety-relevant and must not be silently lost).

For the userspace interface, I'd expose the real-time data via a `read()` on a character device with `O_NONBLOCK` semantics, and the logging data via a separate interface (a second char device, a `debugfs` file, or a `relayfs`/`tracefs` channel). Keeping the two interfaces separate means the logging consumer can be slow without ever touching the real-time path's locks.

I'd also be careful about the interrupt handler itself: it should do the minimum possible work — timestamp, copy into the ring, wake the logging thread if needed — and defer anything heavier to a threaded IRQ or a workqueue that runs at a priority below the real-time task. If the SoC supports it, I'd pin the real-time task to a dedicated core and use `SCHED_FIFO` with a priority above the logging thread, so even scheduler contention can't delay it. Finally, I'd instrument the real-time path with a latency histogram (e.g., via `trace_printk` or a custom `debugfs` counter) so that any regression in worst-case latency is caught early.

**Possible follow-ups:**
- How would you size the ring buffer, and what would you do if the logging consumer is persistently slower than the producer?
- What are the failure modes of a single-producer/single-consumer ring buffer if the producer is an interrupt handler and the consumer is a userspace thread?

## Q4: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** Intermittent fallback to network boot almost always means the primary boot path is failing *sometimes*, and U-Boot's boot order is silently moving on to the next candidate. The first thing I'd do is stop the autoboot and inspect the environment: `printenv bootcmd`, `printenv boot_targets`, and the `bootcmd` chain. If `boot_targets` includes `pxe` or `dhcp` and the board is falling through to them, that's the mechanism — the question is why the eMMC path is failing intermittently.

I'd then reproduce with `setenv boot_targets mmc0` (or the equivalent) to force the eMMC path and see whether the failure still occurs. If it does, the problem is in the eMMC path itself: possible causes include marginal eMMC initialization timing (the eMMC needs a longer power-on delay than the board provides), a race between the eMMC controller and the boot ROM, or a corrupted boot partition that only fails on some power cycles. I'd check the eMMC's `EXT_CSD` and boot partition configuration, verify the `mmc` device is enumerated consistently (`mmc list` across many power cycles), and look at whether the failure correlates with temperature, supply ramp, or specific boards.

If forcing the eMMC path makes the failure disappear, the problem is in the fallback logic — perhaps a timeout is too short, or a `bootcmd` is returning non-zero on a transient error and U-Boot is treating that as "try the next target." In that case I'd tighten the boot logic: make the eMMC path retry once before falling through, and explicitly disable network boot targets in the production environment (`boot_targets=mmc0` only) so that a transient eMMC failure can't silently turn into a network boot. For production, I'd also consider locking the environment (`CONFIG_ENV_IS_NOWHERE` or a read-only environment) so that a corrupted environment can't change the boot order.

**Possible follow-ups:**
- How would you distinguish an eMMC initialization timing issue from a corrupted boot partition?
- What's the risk of disabling network boot entirely in the bootloader, and how would you preserve a recovery path?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** The first thing I'd do is separate the two concerns that are being conflated: the *debug UART* and the *manufacturing console*. They may be the same physical UART today, but they don't have to be, and the manufacturing line's dependency is on the console output, not on which pinmux group carries it. So I'd start by asking the hardware team what the new pinmux group looks like, whether the UART controller itself is unchanged (only the pins move), and whether the new pins are still accessible on the production test fixture. If the controller is the same and only the pinmux changes, the software change is a device tree and bootloader pinmux update — not a functional change — and the risk is manageable.

The real risk is the *timing* of the change relative to the manufacturing line's qualification. If the line has already qualified a test procedure that depends on the console appearing on specific pins, changing the pinmux invalidates that qualification. So I'd bring the manufacturing team into the conversation early, not after the decision is made. I'd propose a path: (1) confirm the new pinmux is electrically sound and the UART controller is unchanged; (2) make the change on a development branch and validate early boot console output on a prototype; (3) coordinate with manufacturing on a re-qualification window, or — if the schedule doesn't allow it — propose keeping the current debug UART on its existing pins and moving a *different*, less critical peripheral to the freed pins instead.

If the hardware team insists the move is necessary and the schedule is tight, I'd escalate to the project lead with a clear statement of the trade-off: the change is technically feasible, but it carries a manufacturing re-qualification cost that needs to be scheduled, and the alternative (moving a different peripheral) may avoid that cost entirely. The goal isn't to win the argument — it's to make sure the decision is made with the full cost visible.

**Possible follow-ups:**
- How would you validate early boot console output on the new pinmux before committing to the change?
- If manufacturing can't re-qualify in time, what alternatives would you propose to the hardware team?