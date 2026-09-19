# embedded-linux-bsp — Day 60

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is called before the clock and regulator it depends on are available, causing intermittent initialization failures?

**Answer:** This is a classic probe-ordering / deferred-probe problem, and the intermittent nature is the tell — if the dependency were simply missing, probe would fail deterministically. Intermittent failure usually means a race: the driver's probe is running concurrently with, or slightly ahead of, the clock or regulator provider being registered.

The first thing I'd do is confirm the diagnosis rather than assume it. I'd check whether the driver is using the correct resource-acquisition APIs — `devm_clk_get()` and `devm_regulator_get()` — and whether it's checking their return values. If the driver is calling `clk_get()` and ignoring an `-EPROBE_DEFER`, it will proceed with a NULL or error pointer and fail later in a confusing way. The kernel's deferred-probe mechanism exists precisely for this: when a provider isn't ready, the consumer should return `-EPROBE_DEFER` from probe, and the driver core will retry it later once providers register. So step one is verifying the driver propagates `-EPROBE_DEFER` correctly and doesn't swallow it.

If the driver is doing the right thing but still failing intermittently, I'd look at the device tree. Probe ordering in Linux is not guaranteed by DT node order — it's driven by driver registration order and the dependency graph the kernel can infer. If the clock or regulator provider is itself probed late (for example, an I2C-controlled PMIC whose I2C bus comes up after the consumer's bus), the consumer may probe before its provider. The fix is usually to make the dependency explicit: ensure the provider is described correctly in DT, that `clocks` and `*-supply` phandles point at the right nodes, and that the provider driver is built-in or loaded early enough. Sometimes the right answer is to move the provider earlier in the init sequence, or to make the consumer a module that loads after the provider.

I'd also enable `initcall_debug` and look at the probe ordering in dmesg, and check `/sys/kernel/debug/devices_deferred` (or the deferred-probe list) to see whether the device is being deferred and how many times. If it's deferred repeatedly and never succeeds, the provider may never be registering at all — which points back at the provider's own dependencies.

The deeper lesson is that on a custom board, probe ordering is a design property you have to reason about, not something to leave to chance. For a medical device where a sensor must be up before monitoring starts, I'd want the dependency chain documented and, where possible, enforced structurally rather than relying on timing luck.

**Possible follow-ups:**
- How would you distinguish between a genuine `-EPROBE_DEFER` loop and a driver that's silently failing to acquire its clock?
- If the provider is an I2C PMIC and the consumer is on a different bus, how would you guarantee ordering without hard-coding initcall levels?

## Q2: You're structuring a Yocto BSP for a product family where several boards share a common SoC and vendor BSP but differ in peripherals, device tree, and userspace packages. How would you organize the layers and recipes?

**Answer:** The goal is to keep the shared foundation in one place and push board-specific variation into the smallest possible surface, so that adding a new board is a matter of adding a machine configuration and a device tree rather than forking recipes.

I'd structure it as a small stack of layers. At the bottom, a BSP layer that carries the vendor kernel, bootloader, and the common machine include — the SoC-level settings, tune flags, and the base kernel configuration fragment. Above that, a product-family layer that defines the shared userspace: common libraries, the application stack, the base image recipe, and shared distro policy. Then, per-board, a thin machine layer (or machine `.conf` files within the family layer) that selects the device tree, adds board-specific kernel config fragments, and pulls in any board-only packages.

The key techniques: use `require`/`include` to share a common machine `.conf` and override only what differs; use `KERNEL_DEVICETREE` per machine to point at the right DTB; use `.bbappend` files to add board-specific config fragments to the kernel rather than editing the kernel recipe; and use `MACHINEOVERRIDES` so that recipes can conditionally include packages based on the machine. For userspace variation — say one board has a display and another doesn't — I'd gate the extra packages behind a machine feature or an override rather than branching the image recipe itself.

I'd also keep the vendor's layer untouched and layer my changes on top via `.bbappend`, so that when the vendor updates their BSP I can rebase my thin layer rather than merge a fork. And I'd keep the device trees in a separate recipe or a `files/` directory referenced by the kernel recipe, so DT changes are reviewable independently of kernel config changes.

The trade-off to be explicit about: too many layers becomes its own maintenance burden, and too few means board-specific hacks leak into shared recipes. The right granularity is usually "one layer for the shared SoC/vendor foundation, one for the product family, and machine configs within it" — adding a whole new layer per board is usually overkill unless the boards diverge substantially.

**Possible follow-ups:**
- How would you handle a board that needs a different kernel version entirely, not just a different config?
- Where would you put a board-specific systemd service, and how would you ensure it only installs on that machine?

## Q3: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** The first thing I'd establish is whether the fallback is happening because the eMMC boot path genuinely failed, or because the boot order logic is wrong and the network path is being tried first or unconditionally. Those are very different bugs.

I'd start by capturing the full U-Boot console output on a failing boot, not just the tail. U-Boot prints which boot device it's attempting and why it moved on. If the eMMC read is failing, there'll usually be an error from the MMC subsystem — a timeout, a CRC error, or a "no partition" message. If instead U-Boot is simply running a `bootcmd` that tries network after eMMC regardless of success, that's a configuration bug, not a hardware one.

On the configuration side, I'd inspect the environment: `printenv bootcmd`, `boot_targets`, and any `bootargs`. A common cause is that `bootcmd` was set up to try a list of targets and the network target was left in the list, or the environment was never saved and the board is falling back to a default environment that includes network boot. I'd check whether the environment is stored in eMMC, in a separate EEPROM, or is the built-in default — because if the saved environment is corrupt or the save failed, U-Boot silently uses the default, which may have a different boot order.

On the hardware side, intermittent eMMC failures point at signal integrity, power sequencing, or a marginal clock. If the eMMC sometimes fails to initialize, I'd look at the MMC clock speed, the bus width, and whether the reset/power sequencing meets the part's timing. A board that boots reliably on the bench but intermittently on the line often has a marginal supply or a marginal pull-up on the MMC lines.

I'd also rule out the obvious: is the network actually reachable, or is the "network boot" just U-Boot timing out and then falling through to something else? And is there a watchdog or a reset cause register that tells me the previous boot failed?

The fix depends on the root cause: if it's a config issue, I'd correct `bootcmd` and ensure the environment is saved and protected; if it's a hardware marginality, I'd address the MMC timing or power. Either way, I'd want the intended boot order to be explicit and the fallback to be deliberate — an unintended network boot on a medical device is both a security and a reliability concern.

**Possible follow-ups:**
- How would you make the environment robust against corruption so the board never silently reverts to a default that boots the wrong device?
- If the eMMC failure is marginal, how would you decide between slowing the MMC clock and fixing the board?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path holds. That rules out a naive design where both paths take the same mutex, because a best-effort task holding the lock can stall the real-time task indefinitely under priority inversion.

The first design decision is to separate the two paths structurally. The real-time task should have a lock-free or minimally-contended path to the hardware — ideally it owns the hardware access entirely, and the logging task never touches the hardware directly. Instead, the real-time path publishes data into a buffer that the logging task reads asynchronously. That way the logging task's latency is irrelevant to the real-time task.

For the buffer itself, I'd use a single-producer/single-consumer ring buffer with a lock-free design: the real-time side writes and advances a head pointer with appropriate memory barriers, the logging side reads and advances a tail pointer. No locks, no blocking. If the logging side falls behind and the buffer fills, the real-time side must decide whether to overwrite the oldest data or drop the newest — for logging, dropping is usually acceptable, but that policy has to be explicit and, for a medical device, documented.

If the hardware genuinely must be shared — say the device has a single command register — then the real-time task should have priority access and the logging task should only issue reads when the hardware is idle, with a bounded wait. In that case I'd use a priority-inheriting mutex (`rt_mutex`) rather than a plain mutex, so that if the logging task does hold the lock, the real-time task's priority is inherited and the logging task is boosted to finish quickly. But even with priority inheritance, the real-time task can still be delayed by the logging task's critical section, so the critical section must be kept extremely short.

I'd also consider whether the logging task needs to be in the kernel at all. Often the cleanest design is to expose the data to userspace via a character device or a `read()`-able interface, and let a userspace logging daemon consume it. That keeps the kernel path minimal and moves the best-effort work out of the kernel entirely.

The thing I'd verify with measurement, not assumption: worst-case latency of the real-time path under load. I'd instrument it and confirm the logging task genuinely cannot delay it, because "lock-free" designs can still have subtle contention on cache lines or memory barriers.

**Possible follow-ups:**
- How would you handle the case where the logging task must not lose data, so dropping isn't acceptable?
- What memory-ordering guarantees do you need on the ring buffer, and how would you verify them?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** I'd treat this as a coordination problem first and a technical problem second, because the technical change is probably small but the operational risk is real.

My first move would be to get the two teams to agree on what's actually at stake. The hardware team wants pins freed for a new peripheral — that's a legitimate need. The software team is worried about breaking the manufacturing line's early boot console, which is also legitimate: if the line relies on that console to detect a bad board, losing it silently is a real problem. So I'd want to understand both constraints precisely before proposing anything.

Then I'd separate the concerns. There are really two questions: (1) can the UART be moved at all without breaking early boot, and (2) if it moves, how do we preserve the manufacturing line's ability to see early boot output? The answer to (2) is usually yes — you can keep a console on the new pinmux, or provide an alternative early-boot diagnostic path. The risk isn't that the console disappears; it's that it disappears *without the line noticing*, or that the change lands late enough that the line's fixtures and procedures haven't been updated.

So I'd propose a staged approach. First, confirm the new pinmux is electrically viable and that the bootloader and device tree changes are well understood — this is a small, reviewable change. Second, make the change on a branch and validate it against the manufacturing line's actual test procedure, not just on the bench. Third, coordinate with manufacturing so the line's fixtures and documentation are updated in lockstep, and so there's a defined point at which the old pinmux is no longer supported. If the schedule is tight, I'd want the change gated behind a clear milestone rather than landing mid-production.

I'd also push back gently on the framing that this is a software-vs-hardware conflict. It's a change-management problem: a pinmux change touches bootloader, device tree, manufacturing fixtures, and documentation, and the cost is in the coordination, not the code. If the new peripheral is genuinely needed, the right answer is to do the change properly and absorb the coordination cost — not to block it, and not to sneak it in.

The one thing I'd insist on is that we don't ship a change that silently removes a diagnostic the line depends on. If we can't update the line in time, we either keep the old console available in parallel or we delay the pinmux change until we can.

**Possible follow-ups:**
- How would you decide whether to keep both UARTs available temporarily versus doing a clean cutover?
- If manufacturing can't update their fixtures before the change lands, what would you propose as an interim measure?