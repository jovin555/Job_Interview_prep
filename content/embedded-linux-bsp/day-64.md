# embedded-linux-bsp — Day 64

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is deferred indefinitely because a supplier it depends on never becomes available — with no obvious error in the kernel log?

**Answer:** Deferred probe is one of the more frustrating failure modes because the kernel is behaving correctly — it's just waiting on a dependency that never resolves, and the log is often silent about *why*. My approach is to treat it as a dependency-graph problem rather than a driver problem.

First, confirm the diagnosis. On a modern kernel, `/sys/kernel/debug/devices_deferred` (or the equivalent debugfs node) lists every device currently sitting in the deferred state, and the kernel usually records the reason string. If debugfs isn't mounted, enabling `CONFIG_DEBUG_DRIVER` and raising the log level with `dyndbg` on the driver core often surfaces the "supplier not ready" messages that are otherwise suppressed. That tells me *which* supplier is missing, which is half the battle.

Second, walk the supplier chain. A deferred probe almost always traces back to one of a small set of root causes: a clock that hasn't been registered yet (the clock provider's own probe is itself deferred or failed), a regulator whose parent supply is missing, a pinctrl or reset controller that hasn't come up, or a phandle in the device tree that points at a node which never gets bound to a driver. I check each of those in the device tree and confirm the referenced node actually has a matching driver and a valid `compatible` string.

Third, look at probe ordering. If the supplier is a driver that's built as a module and the consumer is built-in, the consumer will defer until the module loads — which may be never if the module isn't in the initramfs or rootfs. That's a classic silent failure. The fix is usually to make the dependency built-in, or to ensure the module is loaded early enough.

Fourth, if the supplier is genuinely present but its own probe is failing, I look at *its* log output — a failed regulator registration, a missing GPIO, an I2C bus that isn't up yet — because the deferred consumer is just the visible symptom.

The general principle: deferred probe is the kernel telling you the dependency graph is broken, not the driver. Trace the graph, find the node that never resolves, and fix the root cause rather than adding timeouts or retries to paper over it.

**Possible follow-ups:**
- How would you distinguish a deferred probe caused by a missing clock provider from one caused by a missing regulator, using only the device tree and kernel logs?
- If the supplier is a driver that must be loaded from userspace, how would you restructure the boot sequence so the consumer doesn't defer indefinitely?

## Q2: How would you approach structuring a Yocto BSP so that a board-specific kernel configuration fragment can be applied cleanly without forking the vendor's kernel recipe?

**Answer:** The goal is to keep the vendor's kernel recipe as the single source of truth and layer your board-specific changes on top, so that when the vendor bumps their kernel you rebase a small, well-defined set of changes rather than a forked tree.

The mechanism I'd use is the kernel's own configuration fragment support, wired through Yocto's `linux-yocto`-style `SRC_URI` with `.scc` and `.cfg` files, or — for a vendor kernel that doesn't use the yocto-kernel-cache — a `.cfg` fragment added via `SRC_URI` with the `KERNEL_CONFIG_COMMAND` or a `do_configure:append` that runs `merge_config.sh`. The fragment contains only the deltas: the options your board needs that the vendor's `defconfig` doesn't enable, and any options you need to *disable* (expressed as `# CONFIG_X is not set`). Keeping it as a fragment rather than a full defconfig means a vendor kernel bump doesn't silently drop your settings.

For the layer structure, I'd create a board-specific layer (e.g., `meta-<board>`) that `BBLAYERS` includes after the vendor layer. That layer holds:
- a `.bbappend` on the vendor kernel recipe that adds the config fragment to `SRC_URI` and, if needed, a device tree or patch,
- the device tree source or a patch adding it,
- any board-specific userspace recipes.

The `.bbappend` should be as thin as possible — ideally just `SRC_URI +=` and `FILESEXTRAPATHS:prepend`. Anything more complex (a `do_configure` override, a custom `KERNEL_CONFIG_COMMAND`) is a smell that the vendor recipe isn't structured for extension, and I'd raise that with the vendor rather than working around it.

The other half of "cleanly" is verification: I'd add a build-time check that the fragment's options actually landed in the final `.config` (a small `do_configure:append` that greps the merged config and fails the build if a required option is missing). That catches the case where a vendor kernel bump renames or removes an option and your fragment silently becomes a no-op.

**Possible follow-ups:**
- How would you handle a vendor kernel that doesn't support `merge_config.sh` and expects a full `defconfig`?
- What's your strategy for keeping the fragment in sync when the vendor bumps the kernel and some options are renamed or removed?

## Q3: You're debugging a system where the kernel boots and the root filesystem mounts correctly, but userspace applications that access a GPIO-controlled relay consistently fail with "Device or resource busy" errors. How would you approach this?

**Answer:** "Device or resource busy" on a GPIO almost always means the line is already claimed by something else — either another driver in the kernel, or a userspace process that grabbed it first. The debugging approach is to find out *who* holds the line before trying to fix the application.

First, I'd check the kernel side. `cat /sys/kernel/debug/gpio` shows every GPIO line, its direction, its current value, and — critically — the label of the consumer that requested it. If the relay's line shows a consumer label that isn't the application, that's the culprit: some driver (a pinctrl default state, a regulator, a reset line, a heartbeat LED) has claimed it. The fix is usually in the device tree: either the line is being claimed by a `gpio-hog` or a `pinctrl` state that shouldn't include it, or two nodes are both referencing the same GPIO.

Second, if the kernel side looks clean, I'd check userspace. The sysfs GPIO interface (`/sys/class/gpio/export`) and the newer character device interface (`/dev/gpiochipN`) have different ownership semantics. If the application is using the legacy sysfs interface and another process exported the same line, the second export fails with `EBUSY`. `lsof` on the gpiochip device node, or checking which process has the line exported, usually reveals it. A common cause is a systemd unit or an init script that exports the line for a different purpose and never releases it.

Third, I'd look at the device tree binding itself. If the relay is described as a `gpio-leds` or `gpio-keys` node *and* the application is trying to drive it directly, the kernel driver owns the line and userspace can't. The fix is to decide who owns the line — kernel driver or userspace — and remove the conflicting claim. For a relay that userspace controls, the device tree should describe it as a plain GPIO (or a `gpio-line-names` entry) without a kernel consumer.

The general principle: "busy" means ownership conflict, and the resolution is always to establish a single owner. I'd also add a note to the board bring-up documentation about which lines are kernel-owned and which are userspace-owned, because this class of bug recurs across boards.

**Possible follow-ups:**
- How would you decide whether a relay should be owned by a kernel driver or by userspace, from a safety and reliability standpoint?
- What's the difference in failure modes between the legacy sysfs GPIO interface and the character device interface when two processes contend for the same line?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path does, and the logging path must never hold a lock the real-time path needs. That rules out a naive shared mutex or a single shared buffer protected by a spinlock held across the logging operation.

The design I'd reach for is a lock-free or minimally-contended handoff between the two paths. Concretely:

The real-time path (typically an interrupt handler or a high-priority threaded IRQ) does the minimum work: read the hardware, timestamp, and push the sample into a pre-allocated ring buffer using a single-producer/single-consumer pattern. The producer only advances a write index; it never waits on the consumer. If the buffer is full, the real-time path overwrites the oldest entry (or drops, depending on the requirement) rather than blocking — the real-time deadline is non-negotiable, and losing a log sample is acceptable where missing a deadline is not.

The logging path runs in a workqueue or a low-priority thread. It reads from the ring buffer using the read index, copies data out to the filesystem or a socket, and advances the read index. Because the producer and consumer touch different indices, there's no lock contention on the data path — at most a memory barrier to ensure ordering.

For the shared hardware access itself, if both paths need to touch the same registers, I'd serialize only the register access with a short spinlock held for a few instructions, never across a copy or a sleep. The real-time path must never sleep, so any operation that could sleep (allocating memory, writing to a file, taking a mutex) belongs exclusively to the logging path.

I'd also consider whether the two paths need to share the device at all. If the logging path only needs the *data*, not the hardware, then the cleanest design is for the real-time path to own the hardware entirely and the logging path to consume only the ring buffer. That removes the shared-resource problem altogether.

Verification matters here: I'd want to measure worst-case latency on the real-time path under heavy logging load, using a tracepoint or a GPIO toggle plus an oscilloscope, to confirm the logging path genuinely can't perturb it.

**Possible follow-ups:**
- How would you size the ring buffer, and what policy would you choose when it overflows — overwrite oldest, drop newest, or block the producer?
- If the logging path needs to write to a filesystem that can block for hundreds of milliseconds, how do you ensure that never propagates back to the real-time path?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** This is a classic case where two teams are each optimizing for a real constraint — the hardware team for board real estate, the software team for manufacturing reliability — and the conflict is genuine, not a misunderstanding. My job as BSP lead is to make the trade-off explicit and find a path that doesn't silently break either side.

First, I'd separate the two concerns. The debug UART serves two distinct purposes: early boot console output (which the manufacturing line uses for diagnostics and pass/fail decisions) and post-boot debug logging. Those have different requirements. The manufacturing line's dependency is on the *early* console — U-Boot and early kernel messages — not necessarily on the UART staying on the same pins forever. So the question becomes: can we preserve early console output on the new pinmux, and what does it cost?

Second, I'd quantify the change. Moving a UART pinmux touches the device tree (the pinctrl state for the UART node), the bootloader's pinmux setup, and possibly the board's `stdout-path` in the device tree chosen node. It's not a one-line change, but it's also not a rewrite. The real risk is that the manufacturing line's test fixtures and scripts assume a specific physical connector or a specific console device name — that's an integration concern, not a software one, and it needs to be surfaced to manufacturing explicitly.

Third, I'd propose a concrete path rather than just objecting. Options I'd put on the table:
- Move the UART but keep the same console device name and baud rate, so manufacturing scripts don't change — only the physical pinout does, which the hardware team owns.
- If the new pinmux can't support early console (e.g., the pins are muxed to a peripheral that isn't up until later), propose keeping a minimal early-console path on the old pins and switching to the new pins after boot — but that adds complexity and I'd only recommend it if the hardware team's constraint is truly hard.
- If the change is genuinely risky for manufacturing, propose deferring it to the next board revision rather than the current one, so the current manufacturing flow isn't disrupted mid-qualification.

Fourth, I'd insist on a verification plan before committing: a bring-up test on a prototype board confirming early console output works on the new pinmux, and a walkthrough with the manufacturing team to confirm their fixtures and scripts still work. No change to the boot console path ships without that.

The general principle: when hardware and software constraints collide, don't argue about whose constraint is more important — decompose the requirement, quantify the cost of each option, and let the people who own the downstream risk (manufacturing, in this case) make an informed call. My role is to make sure the decision is explicit and the verification is real, not to win the argument.

**Possible follow-ups:**
- If manufacturing insists the console must stay on the original pins, how would you work with the hardware team to find an alternative way to free up the pins they need?
- How would you document the pinmux change so that a future engineer debugging a boot failure knows the console moved and why?