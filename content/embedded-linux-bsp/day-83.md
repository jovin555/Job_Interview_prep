# embedded-linux-bsp — Day 83

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is called, returns success, yet the device is completely non-functional — no errors in the log, no timeouts, just silence?

**Answer:** A silent success is one of the trickier failure modes because it means the driver *thinks* it initialized correctly, so the fault is usually in the assumptions the driver makes about the hardware rather than in the driver's control flow. I'd work through it in layers.

First, confirm the driver actually bound to the intended device. `ls /sys/bus/platform/drivers/<driver>/` (or the relevant bus) shows which devices are bound. If the device is bound but the wrong instance, or bound to a stale node, that alone explains the silence. Cross-check the device tree node's `compatible`, `reg`, and `status` against what the driver's `of_match_table` expects.

Second, verify the resources the driver requested are the ones the hardware actually uses. A classic silent failure is a `reg` base address or size that is off — the driver maps a region, writes to it, and nothing complains because the writes land in unmapped-but-tolerated space or in a different peripheral's registers. I'd read back a known register (an ID register or a status register with a fixed reset value) immediately after `ioremap` and compare against the datasheet. If the readback is all-zeros or all-ones, the mapping is wrong.

Third, check clocks and resets. Many drivers call `clk_prepare_enable` and `reset_control_deassert` and treat a return of 0 as "the clock is running." But if the clock is enabled yet the parent PLL is not locked, or the reset was deasserted before the clock stabilized, the peripheral can be powered but not clocked. I'd read the clock's actual rate via `clk_get_rate` and compare against the expected rate, and check the reset controller's status register if it exposes one.

Fourth, check pinmux. A peripheral can be fully initialized in software but have its pins muxed to a different function, so no signals reach the outside world. On many SoCs the pinmux is configured by the bootloader or by a separate pinctrl driver; if the pinctrl node is missing or the group is wrong, the driver runs happily and the hardware does nothing. I'd dump the pinmux registers for the relevant pins and compare against the expected function.

Fifth, if the device is on a bus (I2C, SPI), confirm the bus is actually alive. A driver can complete `probe()` after a successful `i2c_smbus_read_byte` that returned a cached or default value, especially if the bus adapter is not yet up. I'd use a bus analyzer or a scope to confirm transactions are physically happening.

The general principle: when `probe()` succeeds but the device is dead, the bug is almost always in the *assumptions* — wrong address, wrong clock, wrong pinmux, wrong bus — not in the driver's logic. So I'd verify each assumption against the hardware rather than re-reading the driver code.

**Possible follow-ups:**
- How would you distinguish between a pinmux problem and a clock problem if both would produce identical silent behavior?
- If the driver is built-in rather than a module, how does that change your debugging approach?

---

## Q2: You're bringing up a board where the kernel boots and the root filesystem mounts, but a userspace daemon that talks to a kernel driver via `ioctl` intermittently fails with `EINTR` and aborts. Nothing is intentionally sending it signals. How would you approach this?

**Answer:** `EINTR` on an `ioctl` means the call was interrupted by a signal before it completed. If nothing in the application is deliberately sending signals, the signal is coming from somewhere else — and the first job is to find out what it is and why it's being delivered.

First, I'd instrument the daemon to log the signal number when `EINTR` is returned. The usual suspects are `SIGCHLD` (a child process exited), `SIGALRM` (a timer expired), or a signal from the kernel itself such as `SIGIO` if asynchronous I/O is enabled on the file descriptor. `SIGCHLD` is especially common in daemons that fork helper processes and don't reap them promptly — the kernel delivers `SIGCHLD` on child exit, and if the daemon's `ioctl` is in progress, it gets interrupted.

Second, I'd check whether the file descriptor has `O_ASYNC` set or whether `F_SETOWN` was called on it. If so, the kernel will deliver `SIGIO` on I/O readiness, which can interrupt a blocking `ioctl`. That's a design issue, not a bug per se, but it needs to be handled.

Third, I'd look at the driver side. A well-written driver should not return `-EINTR` from an `ioctl` unless it genuinely was interrupted while waiting on something interruptible (e.g., a `wait_event_interruptible`). If the driver is using interruptible waits where it should use uninterruptible ones, or vice versa, that changes the behavior. I'd review the driver's wait logic and its signal handling.

Fourth, the correct fix in userspace is almost always to handle `EINTR` by retrying the `ioctl` rather than aborting. POSIX explicitly allows `ioctl` to return `EINTR`, and robust daemons loop on it. If the daemon aborts on `EINTR`, that's a userspace bug regardless of where the signal came from. But I'd still want to know the source, because an unexpected signal can indicate a deeper problem — e.g., a child process crashing repeatedly, or a timer firing more often than intended.

Fifth, if the signal is `SIGCHLD` from a helper, I'd check whether the daemon installs a `SIGCHLD` handler with `SA_RESTART`. Without `SA_RESTART`, system calls interrupted by the signal return `EINTR`; with it, the kernel automatically restarts many (but not all) calls. `ioctl` is not always restartable, so even with `SA_RESTART` the daemon should still handle `EINTR`.

The layered answer: find the signal, understand why it's being delivered, fix the userspace handling to retry on `EINTR`, and if the signal itself is unexpected, fix its source.

**Possible follow-ups:**
- How would you determine whether the signal is being delivered to the specific thread making the `ioctl` or to the process as a whole?
- What's the difference between `wait_event_interruptible` and `wait_event_killable` in a driver, and when would you use each?

---

## Q3: How would you approach structuring a Yocto BSP so that a board-specific kernel configuration fragment can be applied cleanly without forking the vendor's kernel recipe?

**Answer:** The goal is to keep the vendor's kernel recipe as the single source of truth for the kernel source and base configuration, and to layer board-specific changes on top through mechanisms Yocto already provides, so that a vendor kernel update doesn't require re-merging a fork.

The standard approach is to use a kernel configuration fragment (a `.cfg` file) plus a `SRC_URI` entry in a `.bbappend` that applies to the vendor's kernel recipe. The fragment contains only the `CONFIG_*` lines that differ from the vendor's base `defconfig`. Yocto's `kernel-yocto` class merges fragments in order, and the resulting `.config` is the union. This means the vendor's `defconfig` stays untouched, and the board-specific options live in a small, reviewable file.

Concretely, I'd create a layer (e.g., `meta-<board>`) with a `recipes-kernel/linux/` directory containing:
- `linux-<vendor>_%.bbappend` — appends to the vendor's kernel recipe, adding the fragment to `SRC_URI` and setting `KERNEL_FEATURES` or `SRC_URI += "file://board.cfg"`.
- `linux-<vendor>/board.cfg` — the fragment itself.

The `.bbappend` should use `FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"` so the fragment is found. It should not override `SRC_URI` wholesale — only append — so the vendor's patches and config remain in effect.

For options that must be *enabled* (not just present), I'd use `CONFIG_FOO=y` in the fragment. For options that must be *disabled*, `# CONFIG_FOO is not set`. Yocto's config merging respects both forms, but it's important to be explicit about disables, because a fragment that only sets `=y` options won't turn off anything the vendor enabled.

If the board needs a device tree change, that goes in a separate `.bbappend` or in the machine configuration, not in the kernel recipe. The machine conf (`conf/machine/<board>.conf`) sets `KERNEL_DEVICETREE` to point at the board's DTS, and the DTS itself lives in the layer under `recipes-kernel/linux/linux-<vendor>/`.

The key discipline: never edit the vendor's recipe or `defconfig` in place. Everything board-specific goes in the layer, expressed as fragments and appends. That way, when the vendor releases a new kernel, the layer's `.bbappend` either applies cleanly or fails loudly at parse time, and the board-specific delta is small enough to review in minutes.

**Possible follow-ups:**
- How would you verify that a fragment actually took effect, rather than being silently dropped during the merge?
- What's the difference between `KERNEL_FEATURES` and a plain `.cfg` fragment in `SRC_URI`, and when would you use one over the other?

---

## Q4: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** An intermittent fallback to network boot means U-Boot's boot sequence is reaching a point where the eMMC boot path fails, and the fallback path (usually `pxe` or `dhcp` in `bootcmd`) is being taken. The intermittency points to a timing or state issue rather than a hard configuration error, because a hard error would fail every time.

First, I'd capture the full U-Boot console output on a failing boot. The `bootcmd` typically tries a sequence of boot targets; the first one that fails prints an error and the next is tried. The error message tells me whether the eMMC device wasn't detected, the partition wasn't found, the filesystem wasn't readable, or the kernel image wasn't loadable. Each points to a different root cause.

Second, I'd check whether the eMMC is being detected reliably. `mmc list` and `mmc dev 0` in the U-Boot prompt show whether the controller sees the device. If the eMMC is sometimes not detected, the issue could be power sequencing — the eMMC's supply or reset line not being stable when U-Boot probes it — or a clock issue on the MMC controller. I'd scope the eMMC power rail and the reset line during boot to see if there's a race.

Third, I'd check the `bootcmd` itself. If it's structured as `run emmc_boot; run net_boot`, then any failure in `emmc_boot` falls through to `net_boot`. A more robust structure would be to make the eMMC path fail loudly (e.g., `if mmc dev 0; then ...; else echo "eMMC boot failed"; fi`) and to not have a network fallback in production at all. The fallback may have been intentional during development and left in by accident.

Fourth, I'd check the environment storage. If the U-Boot environment is stored in eMMC or in a SPI flash that's sometimes not readable, U-Boot may fall back to its default environment, which could have a different `bootcmd` that includes network boot. I'd verify where the environment is stored (`env print` shows the location) and whether the default environment differs from the saved one.

Fifth, I'd check for a hardware issue specific to the eMMC: a marginal solder joint, a marginal pull-up on the command/data lines, or a power rail that droops under load. Intermittent eMMC detection is a classic symptom of a marginal connection. I'd run the board through temperature cycling or vibration if the failure correlates with those.

The fix depends on the cause: if it's a race, fix the power sequencing or add a delay; if it's the `bootcmd` structure, make the eMMC path fail explicitly and remove the network fallback; if it's the environment storage, make the environment storage reliable or use a compiled-in default that doesn't include network boot.

**Possible follow-ups:**
- How would you make the eMMC boot path fail loudly in U-Boot so that a failure is visible rather than silently falling through?
- If the environment is stored in eMMC and the eMMC is intermittently undetectable, how would you ensure U-Boot still has a valid environment?

---

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** This is a cross-team trade-off between a hardware need (freeing pins) and a software constraint (early boot console stability), and the right approach is to make the trade-off explicit and find a path that satisfies both, rather than letting either team's position win by default.

First, I'd clarify the actual requirement on each side. On the hardware side: which pins does the new peripheral need, and is the debug UART the only candidate for relocation, or are there other options? On the software side: what exactly does the manufacturing line rely on — the UART's physical pins, the console output at a specific baud rate, or the fact that the console is available at a specific point in the boot sequence? The answer matters because moving the UART to a different pinmux group doesn't necessarily change the console's behavior; it changes which physical pins carry it. If the manufacturing line uses a test fixture that probes specific pins, the fixture may need to change, but the software may not.

Second, I'd assess the cost of the change on the software side. If the UART is configured in the device tree and in the bootloader's pinmux setup, the change is localized: update the pinmux node in the device tree, update the bootloader's pinmux configuration, and verify that the console still comes up at the same point in the boot sequence. The risk is not that the change is hard, but that it's easy to get wrong in a way that only shows up on the manufacturing line — e.g., the console works on the bench but not on the fixture because the fixture's probe is on the old pins.

Third, I'd propose a concrete plan: make the pinmux change on a prototype board, verify the console on both the bench and a manufacturing fixture, and only then commit to the change. If the manufacturing fixture needs to change, that's a separate workstream with its own lead time, and the schedule needs to account for it. If the fixture can't change in time, the hardware team needs to find another pin to free, or the new peripheral needs to wait.

Fourth, I'd make sure the decision is documented and owned. The design review should record: what changed, why, what the verification plan is, and who owns the manufacturing fixture update. A verbal agreement in a design review is not enough; the change needs to be traceable, especially on a medical device where the boot console may be part of the manufacturing test evidence.

The general principle: when hardware and software constraints conflict, don't argue about who's right — decompose the constraint into its actual components (pins vs. console behavior vs. fixture), find which components are truly coupled, and negotiate on the ones that aren't. Often the conflict is smaller than it first appears.

**Possible follow-ups:**
- If the manufacturing fixture cannot be updated before the next production run, what options would you present to the project?
- How would you verify that the console still comes up at the same point in the boot sequence after the pinmux change?