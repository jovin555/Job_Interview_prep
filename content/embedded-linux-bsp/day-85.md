# embedded-linux-bsp — Day 85

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is called and returns success, yet the device is completely non-functional — no errors in the log, no timeouts, just silence?

**Answer:** A silent success is one of the trickiest failure modes because it means the driver's control flow completed without the kernel flagging anything, so the fault is almost certainly in the assumptions the driver makes about the hardware rather than in the driver's error handling. I'd work outward from the driver in layers.

First, confirm the driver is actually talking to the device it thinks it is. A `probe()` that returns 0 but does nothing useful often means the device tree node matched a compatible string but the register base, interrupt number, or clock reference resolved to something wrong — or to a different peripheral entirely. I'd dump the resolved resources from within the driver (or via debugfs/sysfs if the subsystem exposes them) and compare against the schematic and the SoC reference manual.

Second, verify the hardware is actually powered and clocked. A device that never gets its enable GPIO asserted, or whose clock is gated, will accept register writes into a void and read back zeros or stale values without generating a bus error. I'd check the regulator and clock framework state, and probe the physical lines with a scope or logic analyzer if I have board access — that immediately tells me whether the driver is even reaching the part.

Third, check the register access path itself. If the driver uses a regmap or a bus abstraction, a misconfigured access size, endianness, or address stride can make every read return a plausible-looking but meaningless value, so the driver's "is the device present?" check passes on garbage. I'd read a known-constant register — a device ID or revision register — and confirm it matches the datasheet.

Finally, I'd instrument the driver to log what it actually reads and writes during probe, then compare that trace against the initialization sequence in the datasheet. Very often the driver is missing a required step — a soft reset, a power-up delay, an unlock sequence — that the datasheet mandates before the device responds. The absence of an error just means nothing checked.

**Possible follow-ups:**
- How would you distinguish between a device that's unpowered and one that's powered but held in reset?
- If the device ID register reads back correctly but the device still doesn't function, where would you look next?

## Q2: You're bringing up a board where the kernel boots and the root filesystem mounts, but a userspace daemon that talks to a kernel driver via `ioctl` intermittently fails with `EINTR` and aborts. Nothing is intentionally sending it signals. How would you approach this?

**Answer:** `EINTR` on an `ioctl` means the call was interrupted by a signal before it completed. If nothing in the application is deliberately sending signals, the signal is coming from somewhere else in the system — and the first thing to establish is whether the daemon is actually receiving a signal at all, or whether it's misinterpreting a different errno.

I'd start by confirming the errno. A surprising number of "intermittent EINTR" reports turn out to be a driver returning `-ERESTARTSYS` from a blocking wait that was woken by a signal the kernel itself delivered — for example, a `SIGCHLD` from a child process, a `SIGALRM` from a timer, or a signal from a watchdog or debugger. I'd add logging that captures the exact errno and, if possible, the signal number via a `sigaction` handler that records what arrived.

Next, I'd look at the driver's blocking behavior. If the `ioctl` handler waits on a completion, mutex, or wait queue with an interruptible wait, any signal delivered to the process will abort the wait and return `-ERESTARTSYS`, which the kernel translates to `EINTR` in userspace. That's correct kernel behavior — the bug is usually in the application, which should retry on `EINTR` rather than treating it as fatal. A robust daemon wraps its `ioctl` calls in a retry loop for `EINTR`.

But I'd also ask why a signal is arriving at all. Common culprits are a parent process reaping children, a `SIGPIPE` from a closed socket, or a timer the daemon itself set up. If the daemon installs handlers with `SA_RESTART`, most blocking syscalls will be automatically restarted instead of returning `EINTR` — that's often the cleanest fix for a daemon that genuinely doesn't want to be interrupted.

The deeper question is whether the driver should be using an interruptible wait in the first place. For a control path where the caller expects to block until completion, an uninterruptible or killable wait may be more appropriate, but that trades responsiveness for robustness. I'd weigh that against the daemon's requirements and document the contract clearly.

**Possible follow-ups:**
- What's the difference between `-ERESTARTSYS` and `-ERESTARTNOINTR` from a driver's perspective?
- How would you decide whether the fix belongs in the driver or the userspace daemon?

## Q3: How would you approach structuring a Yocto BSP so that a board-specific kernel configuration option can be enabled without forking the vendor's kernel recipe?

**Answer:** The goal is to keep the vendor's kernel recipe as the single source of truth and layer our changes on top, so that when the vendor bumps their kernel we rebase cleanly instead of merging a fork. Yocto gives us a few mechanisms for this, and the right one depends on whether the change is a config fragment, a patch, or a recipe-level override.

For a kernel configuration option, the cleanest approach is a configuration fragment. Yocto's kernel class supports `.cfg` fragments that get merged into the final `.config` via `merge_config.sh`. I'd create a small `.cfg` file in our own layer — something like `board-feature.cfg` containing just the `CONFIG_...=y` line — and reference it from a `.bbappend` on the vendor's kernel recipe using `SRC_URI` with the `file://` scheme and the appropriate `KERNEL_CONFIG_FRAGMENTS` or `SRC_URI:append` mechanism. The fragment is applied at build time, so the vendor's recipe and defconfig stay untouched.

The `.bbappend` lives in our layer and does only the minimum: it adds the fragment to `SRC_URI` and, if needed, sets a `KERNEL_FEATURES` or similar variable. It does not redefine the recipe's tasks or override its source. That keeps the diff between our layer and the vendor's layer tiny and reviewable.

If the change is more than a config option — say a small driver patch — I'd add it as a `.patch` file in our layer and include it in `SRC_URI` the same way, with `FILESEXTRAPATHS` pointing at our layer's files directory. Again, the vendor recipe is untouched; our `.bbappend` just appends to its source list.

The discipline that makes this work is keeping our layer's `.bbappend` files thin and well-commented, and treating any change that requires overriding a task or replacing a source as a signal that we should talk to the vendor rather than fork. I'd also add a build-time check or CI step that fails if our layer starts diverging from the vendor's recipe in ways we didn't intend.

**Possible follow-ups:**
- How would you verify that your config fragment actually took effect in the final kernel build?
- What would you do if the vendor's recipe doesn't use the kernel class's fragment mechanism at all?

## Q4: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** An intermittent fallback to network boot means U-Boot's boot sequence is reaching a point where the eMMC boot path fails or times out, and the boot order then proceeds to the next entry — which happens to be network. The intermittency tells me the failure is marginal: a timing issue, a power-rail ramp, or a signal-integrity problem on the eMMC interface, rather than a hard misconfiguration.

First, I'd confirm the boot order and the fallback behavior. U-Boot's `bootcmd` and the `boot_targets` environment variable define the sequence. If network boot is in the list at all, and eMMC boot can fail, the fallback is by design — so the real question is why eMMC boot fails intermittently. I'd check whether the fallback is even supposed to be reachable: in a production image, network boot should usually be removed from `boot_targets` entirely, so that a failure stops rather than silently booting something unintended.

Second, I'd look at the eMMC initialization timing. eMMC devices have a power-up sequence and a required delay before they respond to commands. If the board's power ramp is slow or the reset timing is marginal, the eMMC may not be ready when U-Boot first probes it, and a retry later in the boot sequence succeeds — which would explain the intermittency. I'd check the eMMC's datasheet for the minimum power-up delay and compare against what U-Boot actually waits.

Third, I'd look at signal integrity on the eMMC bus. At high clock speeds, marginal termination, trace length mismatch, or a weak pull-up can cause occasional CRC errors or timeouts during initialization. A logic analyzer or scope capture during a failing boot versus a passing boot would show whether the command/response lines are clean. If the failures correlate with temperature or supply voltage, that's a strong signal-integrity or power-integrity clue.

Finally, I'd make the failure visible. U-Boot's console output during a failing boot should show the eMMC init error or timeout. If it's being suppressed or the console isn't up yet, I'd enable verbose logging and capture the full boot log across many power cycles to characterize the failure rate and the exact point of failure.

**Possible follow-ups:**
- How would you make the boot deterministic so that a failure is loud rather than silently falling back?
- What U-Boot environment variables would you inspect to confirm the boot order?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** This is a classic case where a hardware change that looks trivial — moving a UART to different pins — has a software and manufacturing blast radius that isn't obvious from the schematic. My job as BSP lead is to make that blast radius visible and then help the team find a path that doesn't trade one problem for another.

First, I'd get the facts on the table. What exactly does the manufacturing line rely on? Is it the debug UART specifically, or any early console output? Is the console used for automated test fixtures, for operator-visible diagnostics, or both? If it's automated, the fixture may be pinned to specific test points, and moving the UART means the fixture changes too — that's a manufacturing engineering cost, not just a software cost. I'd want the manufacturing representative in the conversation before we decide anything.

Second, I'd assess the software change honestly. Moving a UART pinmux means changes in the bootloader's early pin configuration, the device tree's pinctrl node, and possibly the kernel command line if the console device name changes. None of that is hard, but it has to be done in the right order and tested at every stage — bootloader console, kernel early console, and userspace console. The risk isn't the change itself; it's doing it late in the project when there's no schedule margin to catch a regression.

Third, I'd look for alternatives before accepting the change. Can the new peripheral share pins with something less critical? Can the debug UART move to a pinmux group that's still accessible from the existing test fixture? Is there a spare UART that could serve as the debug console instead? Often the hardware team's first proposal isn't the only option, and a short exploration can find one that avoids the manufacturing impact entirely.

If the change is genuinely necessary, I'd propose a phased approach: implement the pinmux change in a branch, validate it end-to-end on a prototype board, coordinate with manufacturing to update the fixture and re-qualify the test procedure, and only then merge it into the mainline. I'd also make sure the change is captured in the requirements traceability and risk documentation, since the debug console is part of the manufacturing and service story for a medical device.

Throughout, I'd keep the tone collaborative. The hardware team has a real constraint — they need those pins. The software and manufacturing teams have real constraints too. The job is to find the solution that respects all of them, not to win the argument.

**Possible follow-ups:**
- How would you decide whether the debug UART change requires re-validation of the manufacturing test procedure?
- If the hardware team insists the change is non-negotiable and the schedule is tight, how would you sequence the work to minimize risk?