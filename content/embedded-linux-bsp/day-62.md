# embedded-linux-bsp — Day 62

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is deferred indefinitely because a supplier it depends on never becomes available — with no obvious error in the kernel log?

**Answer:** A probe that defers forever is almost always a dependency graph problem, not a driver bug, so I'd treat it as a topology question first. The kernel's deferred-probe mechanism returns `-EPROBE_DEFER` when a driver asks for a resource — a clock, a regulator, a GPIO, a PHY, an IIO channel — that isn't registered yet, on the assumption it will appear later. If it never appears, something in the chain is either missing, mis-described, or itself stuck deferring.

My first step is to make the invisible visible. `debugfs` exposes `/sys/kernel/debug/devices_deferred`, which lists exactly which devices are parked and why. That immediately narrows it from "the driver doesn't work" to "this specific supplier isn't ready." From there I'd walk the supplier chain: does the supplier's own node exist in the device tree, is its driver built into the image (not just a module that never loads), and is *it* also deferred? Deferral chains are common — a regulator depends on an I2C bus, the I2C bus depends on a pinctrl state, the pinctrl depends on a clock — and the real culprit is often several links back.

Common root causes I'd check in order: a `phandle` typo or a node referenced before it's defined; a supplier driver compiled as a module that isn't in the initramfs or rootfs; a `status = "disabled"` on a parent node that silently orphans the child; a clock or regulator name mismatch between the device tree and what the driver requests (the driver asks for `"vdd"` but the DT labels it `"vdd-supply"` incorrectly); or a circular dependency where two devices each wait on the other. I'd also enable `initcall_debug` and bump the driver core's deferred-probe logging to see the ordering.

If the chain is genuinely correct but ordering is the issue, the fix is usually to make the supplier probe earlier — built-in rather than modular, or a `-EPROBE_DEFER`-friendly ordering — rather than to hack the consumer. The key discipline is: never "fix" a deferred probe by removing the dependency check, because that just converts a clean deferral into a race that fails intermittently in the field.

**Possible follow-ups:**
- How would you tell the difference between a genuine circular dependency and a simple ordering problem?
- If the supplier is a module that must load from the rootfs, how does that interact with the fact that the consumer might be needed to mount the rootfs?

## Q2: How would you structure a Yocto BSP so that a board-specific kernel configuration change can be applied cleanly without forking the vendor's kernel recipe?

**Answer:** The goal is to never touch the vendor's recipe or their `defconfig` directly, because the moment you fork it you own every future merge and you lose the ability to rebase onto their updates. Yocto gives you two clean mechanisms, and I'd use both deliberately.

For configuration, I'd use kernel configuration fragments via `SRC_URI` with the `.cfg` extension and the `kernel-yocto` class's merge machinery. A fragment is a small file containing only the options you're changing — `CONFIG_FOO=y`, `# CONFIG_BAR is not set` — and the build system merges it on top of the vendor's base config. This keeps your delta explicit, reviewable, and version-controllable, and it survives a vendor kernel bump because you're expressing intent ("I need this option on") rather than shipping a whole frozen config. The `# CONFIG_X is not set` form matters: a fragment that only sets options can't *disable* something the vendor enabled, so for anything you need off you must write the explicit "is not set" line.

For the recipe itself, I'd create a `.bbappend` in my own layer that matches the vendor's kernel recipe name and version, and add my fragments and any patches through `SRC_URI`. The `.bbappend` is the sanctioned extension point — it layers on top without copying. I'd pin the append to the vendor recipe's `PV` (or use `%` wildcards carefully) so that a vendor version bump forces me to consciously re-validate rather than silently applying a stale fragment.

The structural discipline: one layer for the SoC/vendor BSP, one layer for the board, one for the product. Board-specific config lives in the board layer's `.bbappend` and fragments; product-wide policy lives higher up. That way a second board on the same SoC reuses the vendor layer untouched and only adds its own small fragment set. I'd also keep a `defconfig`-diff check in CI so that if a fragment silently fails to apply — which Yocto will warn about but not always fail on — it gets caught before it reaches a build.

**Possible follow-ups:**
- How would you detect that a fragment silently failed to apply, given that the build may still succeed?
- What's the trade-off between using a fragment versus a full custom `defconfig` for a heavily customized board?

## Q3: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** An intermittent fallback to network boot means the boot sequence is reaching a failure point on the eMMC path and then continuing down a fallback chain that shouldn't exist in production. So there are really two bugs: the intermittent eMMC failure, and the presence of an unintended fallback. I'd fix both, but I'd characterize the first one before touching anything.

First, I'd understand the boot logic. U-Boot's `bootcmd` is often a chain — try eMMC, and if that fails, try network, then USB, then drop to a prompt. In a production image that chain should be collapsed to a single deterministic path with a defined failure behavior (halt, or a recovery mode), not a cascade. So step one is to read the actual `bootcmd` and `boot_targets` and confirm whether the fallback is baked into the environment or coming from a default. If it's in the environment, that's a configuration defect regardless of the eMMC issue.

Second, I'd chase the intermittency. Intermittent eMMC boot failures on a custom board usually trace to one of a few things: power sequencing — the eMMC rail not being stable when U-Boot first touches it, which is timing- and temperature-dependent; signal integrity on the eMMC data/clock lines, especially if the bus speed is marginal; a marginal reset or a missing power-on-reset delay; or the eMMC itself entering a state (e.g., after an unclean shutdown) where the first access times out but a retry succeeds. I'd instrument by enabling U-Boot's verbose MMC logging, checking the `mmc` probe return codes, and correlating failures with temperature and power-cycle count. If it correlates with cold boot but not warm reboot, that points at power sequencing or reset timing rather than the eMMC part itself.

Third, I'd make the failure observable. Right now the fallback masks the real error — the board "boots" over the network and nobody sees the eMMC failure. I'd want the eMMC failure to be logged and, in production, to halt rather than silently take a different path, so the defect surfaces in test instead of in the field.

The principle: a boot chain that can silently take an unintended path is a reliability hazard, especially in a regulated device. Deterministic boot with explicit, logged failure is the target.

**Possible follow-ups:**
- How would you distinguish a power-sequencing issue from a signal-integrity issue on the eMMC bus without a scope on every unit?
- Where would you store the "known good" boot configuration so that a corrupted environment can't itself cause a fallback?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path can hold, so the design has to physically separate the two so they don't contend for the same lock or the same bus transaction. I'd start by asking what "real-time access" actually means here — is it a register read the RT task does directly, or does it go through the driver? That determines where the isolation boundary sits.

The cleanest pattern is a producer/consumer split with a lock-free or minimally-contended handoff. The real-time side does the minimum: it reads the hardware (or is triggered by the hardware interrupt) and writes into a pre-allocated ring buffer using a lock-free single-producer/single-consumer scheme, then returns. The logging side is a separate context — a workqueue, a kthread, or a userspace reader — that drains the ring buffer at its own pace. Because the RT side only ever writes to a slot the consumer isn't reading, it never waits on the logger. If the ring buffer fills because logging is slow, the correct behavior is to drop or overwrite oldest data on the logging side, never to block the RT side.

Key implementation details: pre-allocate all buffers at probe time so the RT path never allocates; use `spin_lock_irqsave` only for the tiny critical section that updates the ring indices, or better, use atomic indices so there's no lock at all on the RT path; and make sure the RT path doesn't take a mutex, because a mutex can sleep and can be held by the logging task. If the hardware itself is a shared resource — say both tasks need to touch the same I2C device — then the RT task must own the bus and the logging task must consume only the already-captured data, never issue its own bus transactions.

I'd also think about priority: if the logging task runs at a priority that can preempt the RT task, that's a priority-inversion setup waiting to happen. The RT task should be higher priority, and any shared lock must be a priority-inheriting one or, preferably, eliminated. Finally, I'd validate with a latency measurement — instrument the RT path to timestamp entry and exit and confirm the worst-case latency is bounded regardless of logging load. The design isn't proven until you've shown the RT deadline holds under maximum logging pressure.

**Possible follow-ups:**
- If the hardware genuinely can only be accessed by one context at a time, how would you arbitrate without letting the logger block the RT task?
- How would you size the ring buffer, and what's the failure mode when it overflows?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** I'd treat this as a coordination problem first and a technical one second, because both teams are right about something real: hardware needs the pins, and software is protecting a manufacturing dependency that isn't obvious from the schematic. The failure mode I want to avoid is either side "winning" the argument and the other side discovering the consequence late.

My first move is to get the actual constraints on the table rather than the positions. For the hardware side: is the new peripheral blocking a milestone, and is this pinmux move the only option or just the preferred one? For the software side: what exactly does the manufacturing line depend on — is it the UART console specifically, or the ability to see early boot output at all? Those are different problems with different solutions. If manufacturing just needs *visibility* into early boot, the console could move to a different UART, or to a different physical access point, without losing the capability. If they need *that specific* UART on *that specific* connector, that's a harder constraint.

Then I'd quantify the change. Moving a debug UART in the device tree is usually small — a pinmux node change and a `stdout-path` update — but the risk is in the bootloader, because the console is often configured there too and the two must agree, and in any early-boot code that assumes the console is up before the device tree is parsed. So the real question is whether we can make the change and still guarantee early console output, and whether we can validate that on the manufacturing line's actual test procedure rather than just on a bench.

I'd propose a path that de-risks it: prototype the pinmux change on a spare board, confirm early boot output still appears on the new UART through the full boot sequence, and have manufacturing run their existing procedure against the prototype before we commit. If the change can't preserve the manufacturing dependency, I'd push back with data rather than opinion — show what breaks and propose alternatives (a different free pin, a test point, a different peripheral placement). If it can preserve it, I'd sequence the change so the device tree and bootloader move together and the manufacturing procedure is updated in the same release, not after.

The through-line: I don't want to be the person who says "no, it's baked in," nor the person who says "sure, change it" without checking. I want the decision made with the manufacturing dependency visible to everyone, and a validation step that proves the change is safe before it lands.

**Possible follow-ups:**
- If manufacturing insists on the exact same UART and connector, what alternatives would you propose to free up the pins?
- How would you make sure the device tree and bootloader console settings can't drift out of sync in future changes?