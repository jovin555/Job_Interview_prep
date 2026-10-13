# embedded-linux-bsp — Day 84

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is called and returns success, yet the device is completely non-functional — no errors in the log, no timeouts, just silence?

**Answer:** A silent success is one of the harder classes of bring-up bug because the usual error paths are all quiet. I'd treat it as a "did the driver actually talk to the hardware, or did it just complete its bookkeeping?" problem and work outward from the register interface.

First, confirm the driver is bound to the right device instance. Check `/sys/bus/<bus>/devices/` and the driver's sysfs directory to see that the device is bound and that the driver's `probe()` really ran against the node I think it did — a common trap is two similar nodes, or a fallback compatible string matching a generic driver that probes cleanly but does nothing useful.

Second, verify the register accesses are landing where I think. If the peripheral is memory-mapped, dump the registers after probe and compare against the values the driver wrote (or against the reset values in the datasheet). If reads return all-zeros or all-ones, that usually points to a clock or power domain that was never enabled, a wrong base address, or a pinmux that never routed the signals out. If it's an I2C/SPI device, I'd put a scope or logic analyzer on the bus and check whether any transactions actually appear during probe — silence on the bus with a "successful" probe almost always means the driver's I/O helpers are being short-circuited (for example, a `regmap` configured with a no-op bus, or an optional regulator/clock that the driver treats as best-effort).

Third, check the dependencies the driver assumes are already satisfied. A driver can probe "successfully" while its clock is still gated, its reset line is still asserted, or its power rail is off — it just never notices because it doesn't read back a status register. I'd walk the device tree for `clocks`, `resets`, `power-domains`, and `regulators`, and confirm each is actually being enabled (check `clk_summary`, `regulator_summary`, and the reset controller state).

Fourth, if the driver exposes an interrupt, confirm the IRQ is actually firing. A device that probes fine but never interrupts is often a pinmux or interrupt-parent misconfiguration rather than a driver bug.

Finally, I'd add targeted `dev_dbg`/`pr_debug` at the register read/write points and re-run with dynamic debug enabled, so I can see the actual values going in and out rather than inferring from the absence of errors. The key discipline is: don't trust "probe returned 0" as evidence the hardware works — verify at the register and bus level.

**Possible follow-ups:**
- How would you tell the difference between a clock that's gated and a pinmux that's wrong, if both produce all-zero register reads?
- If the driver uses `regmap`, what configuration mistakes could make it silently skip real bus transactions?

## Q2: How would you approach structuring a Yocto BSP so that a board-specific kernel configuration option can be enabled without forking the vendor's kernel recipe?

**Answer:** The goal is to keep the vendor's kernel recipe as the single source of truth and express my board's deltas as additive, reviewable artifacts rather than a copy of the recipe. In Yocto the natural mechanism for that is a kernel configuration fragment applied through the kernel's `config`/`scc` metadata, referenced from a `.bbappend` in my own layer.

Concretely, I'd create a layer for the board (or the product family) that `BBLAYERS` includes alongside the vendor BSP layer. In that layer I'd add a `linux-<vendor>_%.bbappend` that appends to `SRC_URI` a `.cfg` fragment containing just the `CONFIG_*` lines I need, and points `KERNEL_CONFIG_FRAGMENTS` (or the older `KERNEL_FEATURES`) at it. The fragment is merged on top of the vendor defconfig at build time, so I never touch the vendor's recipe or its defconfig. If the option has dependencies, I'd express them in the fragment too, and rely on `bitbake -c menuconfig virtual/kernel` to sanity-check the resulting `.config` before committing.

A few practices that keep this maintainable across kernel version bumps: keep fragments small and single-purpose (one fragment per feature, not one giant board fragment), name them so their intent is obvious, and add a `KERNEL_FEATURES` entry only for options that genuinely must be on. I'd also add a build-time check — either a `do_configure:append` assertion or a separate recipe — that greps the final `.config` for the options I care about, so a vendor kernel bump that silently drops a symbol fails the build instead of shipping a board that boots without its peripheral.

The same pattern extends to device trees: rather than editing the vendor's `.dts`, I'd add my board's `.dts`/`.dtsi` in my layer and reference it via `KERNEL_DEVICETREE`, so the vendor tree stays pristine and my deltas are isolated.

**Possible follow-ups:**
- What happens if a fragment enables an option whose dependency isn't met, and how would you catch that at build time rather than at boot?
- How would you handle a vendor kernel bump that renames or removes a symbol your fragment depends on?

## Q3: You're bringing up a board where the kernel boots and the root filesystem mounts, but a userspace daemon that talks to a kernel driver via `ioctl` intermittently fails with `EINTR` and aborts. Nothing is intentionally sending it signals. How would you approach this?

**Answer:** `EINTR` means a blocking syscall was interrupted by a signal before it completed — so the first question is "what signal, and why is it being delivered?" The daemon aborting on `EINTR` is itself a bug (a well-written daemon should retry on `EINTR` for idempotent ioctls, or handle it explicitly), but the underlying cause is a signal arriving at an inconvenient time, and I'd want to find it rather than just paper over it.

I'd start by instrumenting the daemon to log which signal interrupted it. A `sigaction` handler that records `siginfo_t` (signal number, sender PID, `si_code`) turns "intermittent EINTR" into a concrete signal. Common culprits on embedded systems: `SIGCHLD` from a child process the daemon spawns (or from a helper it didn't realize it had), `SIGALRM` from a timer it set, `SIGIO`/`SIGPOLL` if it registered for async I/O, or a signal sent by another component (a watchdog kicker, a supervisor, a debug tool). If the daemon uses `SIGCHLD` with a handler that doesn't reap children, that alone can produce repeated signals.

If the signal turns out to be coming from the kernel driver side — for example, the driver is delivering a signal to userspace on an event — I'd check whether the driver's signal delivery is racing with the ioctl path, and whether the driver is using `kill_fasync` or similar in a way that fires more often than intended.

Independently of the root cause, I'd fix the daemon's error handling: for a blocking ioctl that's safe to retry, loop on `EINTR`; for one that isn't, restructure so the operation is either non-blocking or the daemon can resume cleanly. And I'd make sure the daemon isn't installing handlers that mask or mis-handle signals it doesn't own.

The broader lesson I'd apply: on an embedded system with multiple processes, signals are a shared resource, and a daemon that assumes it's the only signal recipient will eventually be surprised. I'd want the daemon's signal contract documented and its handlers explicit.

**Possible follow-ups:**
- How would you distinguish a `SIGCHLD` storm from a genuine `SIGALRM`-driven timeout if both produce `EINTR`?
- If the ioctl is not idempotent, what's a safe way to handle `EINTR` without corrupting device state?

## Q4: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** An unintended network fallback means the boot flow reached a point where the eMMC boot path failed or was skipped, and U-Boot's boot order moved on to the next candidate. I'd treat it as two questions: why did the eMMC path fail, and why is the network path even in the boot order?

On the first question, I'd look at what U-Boot actually reports before the fallback. If `mmc dev` or the equivalent fails, the usual causes are: the eMMC not finishing its internal initialization within U-Boot's timeout (some parts need a longer delay after power-on), a clock or voltage rail that isn't stable when U-Boot probes the controller, a card-detect or reset GPIO that's floating or mis-strapped, or a device tree / board config mismatch where U-Boot is looking at the wrong controller instance. Intermittency points strongly at a timing or power-sequencing issue rather than a hard wiring fault — I'd check the eMMC's power-up sequence against the datasheet and against the PMIC's soft-start timing, and I'd add a retry with a bounded delay around the eMMC init to see if that stabilizes it.

On the second question, I'd look at `bootcmd` and `boot_targets`. If the environment includes a network target (DHCP/TFTP) in the boot order, that's a deliberate configuration that someone left in — often inherited from a development or manufacturing image. I'd remove it from the production environment, or gate it behind a condition that can't be satisfied in the field (for example, only attempt network boot if a specific GPIO or environment variable is set). I'd also check whether the environment is being loaded from a persistent store that could have been overwritten, and whether there's a fallback chain that's broader than intended.

The fix is usually both: make the eMMC path robust (correct power sequencing, adequate init timeout, retry) and make the boot order explicit and minimal so that a transient eMMC failure doesn't silently divert to a network path that shouldn't exist in production. I'd also add logging so that when the fallback does happen, it's visible rather than silent.

**Possible follow-ups:**
- How would you make the eMMC init robust against a slow power ramp without hard-coding a delay that's too long for the fast case?
- What's a safe way to keep a network boot path available for manufacturing test without risking it in the field?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** I'd treat this as a coordination problem first and a technical one second, because both teams are raising legitimate concerns and the resolution depends on facts neither side has fully laid out.

First, I'd get the actual constraints on the table. From hardware: which pins are needed, why this particular pinmux group, and whether there's an alternative that avoids the debug UART. From software: exactly where the pinmux is configured (bootloader, device tree, or both), what the manufacturing line actually depends on (early console output for test logging, or something more), and what the change would cost in terms of re-validation. I'd want to know whether the manufacturing dependency is a hard requirement or a convenience that could be replaced.

Second, I'd separate the two concerns. Moving the debug UART is a pinmux change; the manufacturing dependency is a process dependency. They're related but not identical. If the manufacturing line needs early console output, that's a requirement to preserve regardless of which pins carry it — so the question becomes "can we move the UART and still give manufacturing what it needs?" rather than "can we move the UART at all?"

Third, I'd look for options that satisfy both sides. Possibilities: keep the debug UART on its current pins and find the new peripheral a different home; move the UART but provide an equivalent early-boot console on the new pins (which may just mean updating the bootloader and device tree consistently); or move the UART and give manufacturing a different mechanism for the test logging it relies on. I'd also check whether the new peripheral could share pins with something less critical, or whether the pinmux change could be made conditional on a board revision so both configurations are supported during the transition.

Fourth, I'd be explicit about the cost of each option — re-validation effort, risk to the manufacturing line, schedule impact — and bring that back to the review as a decision with trade-offs rather than a yes/no. If the change is worth doing, I'd want a plan that includes updating bootloader and device tree together, re-testing early boot console on the new pins, and confirming with manufacturing that their test flow still works before the change lands.

Throughout, I'd keep the tone collaborative: hardware isn't wrong to want the pins, software isn't wrong to protect the manufacturing dependency, and my job is to find the option that respects both rather than to pick a winner.

**Possible follow-ups:**
- If manufacturing's dependency turns out to be a convenience rather than a hard requirement, how would you decide whether to preserve it?
- How would you structure the change so that both the old and new pinmux configurations can be supported during a board revision transition?