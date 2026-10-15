# embedded-linux-bsp — Day 86

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is called, returns success, yet the device is completely non-functional — no errors in the log, no timeouts, just silence?

**Answer:** A silent success is one of the more deceptive failure modes because the kernel has already told you it thinks everything is fine. I'd treat it as a "the driver believes it configured the hardware, but the hardware disagrees" problem and work outward from the driver's own assumptions.

First, I'd confirm the driver actually bound to the intended device instance. On a system with multiple similar peripherals, it's easy for `probe()` to run against the wrong node or a stale compatible string, so I'd check the sysfs device tree (`/sys/bus/.../devices/`) and the driver's `of_match` table against the actual device tree node. A mismatch here produces exactly this symptom: probe runs, registers, and then nothing talks to the real hardware.

Second, I'd verify the resources the driver thinks it owns. A common cause is that the driver maps a register region, clock, or reset line that is correct on paper but wrong in practice — for example, a base address that overlaps another peripheral, or a clock that is enabled but gated at a parent. I'd read back the peripheral's ID or version register through `/dev/mem` or a small debug module to confirm the CPU can actually see the device at the address the driver mapped. If the read returns all-ones or all-zeros, the mapping or the power/clock domain is wrong even though `ioremap` succeeded.

Third, I'd check the pinmux and pad configuration. A device can be fully powered and clocked but have its pins still assigned to another function, so the driver's register writes go nowhere useful. This is especially common after a board revision where the pinmux table was updated for one peripheral but not another.

Fourth, I'd look at whether the driver is actually being exercised. Sometimes the "non-functional" report is really "the userspace path never triggers a transfer" — the driver is fine, but the character device node, the `ioctl` number, or the sysfs attribute the application uses doesn't match what the driver exposes. I'd strace the application and confirm the syscall reaches the driver.

Finally, if all of that checks out, I'd instrument the driver with a temporary debugfs node or dynamic debug prints at the point where it programs the hardware, and compare the register values it writes against the datasheet's expected sequence. The gap between "what the driver wrote" and "what the hardware needs" is usually where the answer is.

**Possible follow-ups:**
- How would you distinguish between a driver that never actually touches the hardware and one that touches it but with the wrong values?
- If the device works on a development board but not on production hardware, what would you check first?

## Q2: You're bringing up a board where the kernel boots and the root filesystem mounts, but a userspace daemon that talks to a kernel driver via `ioctl` intermittently fails with `EINTR` and aborts. Nothing is intentionally sending it signals. How would you approach this?

**Answer:** `EINTR` on an `ioctl` almost always means the calling thread was interrupted by a signal while blocked in a slow or interruptible path inside the driver, and the daemon's error handling treats that as fatal rather than retrying. The fix is usually two-sided: make the daemon robust, and understand why the driver is returning an interruptible wait in the first place.

On the daemon side, the correct pattern is to loop on `EINTR` and re-issue the `ioctl` rather than aborting. `EINTR` is not an error condition in the sense of "the operation failed" — it means "you were interrupted before the operation completed, and you may retry." A daemon that treats it as fatal will fall over any time an unrelated signal (a `SIGCHLD` from a helper process, a `SIGALRM` from a timer, a debugger attach) lands during a blocking call. I'd check whether the daemon installs any signal handlers without `SA_RESTART`, because that flag is exactly what determines whether a blocked syscall is restarted automatically or returns `EINTR`.

On the driver side, I'd look at what the `ioctl` is doing. If it's waiting on a completion, a mutex, or a hardware event, the wait should be interruptible only if the driver genuinely supports being interrupted and cleaned up correctly. If the operation is meant to be atomic from the caller's perspective, the driver may be using `wait_event_interruptible` where `wait_event` or a bounded `wait_event_interruptible_timeout` would be more appropriate. I'd also check whether the driver is spuriously waking waiters — for example, a completion that fires for an unrelated event and returns `-ERESTARTSYS` without the caller expecting it.

The diagnostic step is to reproduce with `strace -f -e trace=ioctl` and correlate the `EINTR` returns with signal delivery in the same trace. That tells you whether the signal is coming from inside the process (a handler firing) or from outside (a `SIGSTOP`/`SIGCONT` from a supervisor, or a `ptrace` attach). Once you know the source, the fix is usually either `SA_RESTART` on the handler or a retry loop in the daemon — and often both, because defensive retry logic is correct regardless.

**Possible follow-ups:**
- What's the difference between `ERESTARTSYS` and `EINTR` from the driver's perspective, and why does it matter?
- How would you decide whether a given `ioctl` should be restartable at all?

## Q3: How would you approach structuring a Yocto BSP so that a board-specific kernel configuration option can be enabled without forking the vendor's kernel recipe?

**Answer:** The goal is to keep the vendor's kernel recipe as the single source of truth for the kernel source and base configuration, and layer board-specific deltas on top through mechanisms Yocto already supports, rather than copying the recipe into your own layer and diverging.

The cleanest approach is a kernel configuration fragment applied through the `SRC_URI` of a `.bbappend` in your board layer. Yocto's kernel class supports `.cfg` fragments that are merged into the final `.config` at build time, and the merge is validated against the base configuration so that a fragment which tries to enable something incompatible with the vendor's `defconfig` fails loudly rather than silently. The `.bbappend` names the vendor recipe (with `%` wildcarding if you want to track version bumps) and adds the fragment to `SRC_URI` with the appropriate `KERNEL_CONFIG_FRAGMENTS` or `SRC_URI:append` syntax. The fragment itself is a small file containing just the `CONFIG_*` lines you need, which keeps the diff reviewable.

For options that are genuinely board-specific and shouldn't leak into other boards sharing the same vendor BSP, the fragment lives in the board's layer and is only pulled in by that board's machine configuration. If two boards share most of the delta, a common fragment plus a board-specific one keeps duplication down.

The alternative — a full `defconfig` override — is tempting but fragile: it freezes the configuration at a point in time and stops tracking the vendor's changes, so a vendor kernel update that adds a new required option will silently drop it. Fragments compose; full overrides don't.

I'd also make sure the fragment is validated in CI. A common failure mode is that a fragment enables an option that depends on another option the vendor disabled, and the kernel build either warns or silently drops it. Checking the final `.config` in the build artifacts, or using `bitbake -c menuconfig` to inspect the merged result, catches that early.

**Possible follow-ups:**
- How would you handle a fragment that needs to *disable* an option the vendor enabled, rather than enable a new one?
- What happens if the vendor bumps the kernel version and your fragment references an option that no longer exists?

## Q4: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** An intermittent fallback to network boot usually means the boot sequence is reaching a point where the primary boot device is not ready or not recognized, and the bootloader's fallback path is being taken because it was never explicitly disabled. The fix is part diagnosis, part hardening the boot configuration so the fallback can't happen silently.

First, I'd confirm what "intermittent" actually correlates with. Does it happen more on cold boots than warm resets? More on boards from a particular production batch? More when a specific peripheral is attached? The pattern usually points at either a timing issue (eMMC not ready when U-Boot probes it) or a hardware variance (a marginal solder joint, a slow power rail, a different eMMC part). I'd capture the full U-Boot console log on a failing boot and compare it against a passing boot, looking for the point where the eMMC probe returns an error or times out.

Second, I'd look at the boot order and fallback configuration. U-Boot's `bootcmd` and the `boot_targets` environment variable determine the sequence, and if the network target is in the list, a failure to boot from eMMC will fall through to it. The correct fix is usually to remove the network target from `boot_targets` entirely on production units, or to gate it behind an explicit condition (a GPIO strap, a magic environment variable) so it can only be entered deliberately. Leaving it in "just in case" is exactly what causes this class of bug.

Third, I'd check the eMMC initialization timing. Some eMMC devices need a longer delay after power-on before they respond to the first command, and if U-Boot's `mmc` driver probes too early, the probe fails and the fallback triggers. The fix is either a longer delay in the board's `board_init` or `mmc` init path, or a retry loop around the eMMC probe. I'd also verify the eMMC's power rail and reset line are sequenced correctly relative to the SoC's boot.

Fourth, I'd check whether the environment itself is being corrupted or reset. If the saved environment is lost (bad eMMC sector, a failed `env save`), U-Boot falls back to the compiled-in default environment, which may include the network boot target even if the saved environment doesn't. Verifying that the environment is stored redundantly and that `env save` is actually succeeding closes that gap.

Finally, I'd make the failure visible. A board that silently falls back to network boot in the field is much worse than one that halts with a clear error, so I'd add a check that the primary boot device was found and, if not, either halt or signal the failure through an LED or a log entry that the manufacturing line or field service can see.

**Possible follow-ups:**
- How would you distinguish between an eMMC that's slow to initialize and one that's genuinely failing?
- What's the risk of removing the network boot target entirely, and how would you preserve a recovery path?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** This is a case where both teams are right about their own concerns, and the job is to find a path that satisfies the hardware's pin budget without silently breaking a manufacturing dependency. I'd start by making the dependency explicit and quantified, because "the manufacturing line relies on it" is a claim that needs a concrete answer to "how, and what breaks if it changes?"

First, I'd get the software team to describe exactly what the manufacturing line uses the debug UART for: is it a human reading boot messages, an automated test fixture parsing output, or a recovery path for a bricked board? Each of those has a different tolerance for change. An automated fixture that greps for specific strings is much more sensitive than a human watching a console. I'd also confirm whether the UART is used in the field or only during manufacturing, because that changes the risk profile significantly.

Second, I'd ask the hardware team what the new peripheral actually needs and whether there's an alternative pin assignment that avoids the conflict. Pinmux changes are often proposed as the first solution when a different package option, a different peripheral instance, or a small board respin could avoid touching the debug UART entirely. If the new peripheral can be moved instead, that's usually the lowest-risk path.

Third, if the move is genuinely necessary, I'd propose a staged approach: keep the current UART as the primary console for the current hardware revision, and add the new pinmux as a secondary console that can be selected by a device tree overlay or a bootloader environment variable. That lets the manufacturing line keep working unchanged while the new peripheral is brought up, and gives the software team time to update the test fixtures and validate the new console before the old one is retired. The key is that the change is opt-in and reversible during the transition, not a hard cutover.

Fourth, I'd make sure the change is captured in the requirements traceability and risk documentation. In a medical device context, changing the debug interface is a change to the manufacturing and service process, not just a firmware change, and it needs to go through the same change control as any other design change. I'd want the hardware team, software team, manufacturing, and regulatory all aligned on the plan before anyone touches the device tree.

Finally, I'd set a clear decision point: if the new peripheral can't wait and the manufacturing line can't tolerate a transition period, that's a schedule conflict that needs to be escalated to the project lead, not resolved by one team unilaterally changing the pinmux. My role as BSP lead is to surface the trade-off clearly, not to absorb it silently.

**Possible follow-ups:**
- How would you validate that the new console works correctly before retiring the old one?
- If the manufacturing line's test fixture can't be updated in time, what would you do?