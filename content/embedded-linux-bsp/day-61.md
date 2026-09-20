# embedded-linux-bsp — Day 61

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is called before the clock and regulator it depends on are available, causing intermittent initialization failures?

**Answer:** This is a classic probe-ordering / deferred-probe problem, and the intermittent nature is the tell — it usually means the driver is racing against the clock and regulator frameworks rather than being properly wired into them.

The first thing I'd check is whether the driver is actually using the kernel's resource-management APIs at all. If the driver is calling `clk_get()` and `regulator_get()` and getting valid handles, then the frameworks themselves will return `-EPROBE_DEFER` when the provider isn't ready yet, and the driver just needs to propagate that return code up from `probe()`. If the driver is instead assuming the clock is already running (e.g., because the bootloader left it enabled) or reading a fixed voltage from a hardcoded value, then there's no deferral mechanism and the race is baked in.

So the diagnostic path is: confirm the driver returns `-EPROBE_DEFER` on any resource that isn't ready, confirm the device tree has the `clocks` and `*-supply` properties pointing at the right provider nodes, and confirm the providers themselves are probing early enough. A common cause is that the regulator provider is on an I2C bus that hasn't been populated yet, so the regulator driver probes late and the consumer driver gives up before it appears. The fix there is usually to make sure the consumer driver returns `-EPROBE_DEFER` rather than a hard error, and to check that the I2C controller itself is probing early enough.

I'd also look at `dmesg` for the "deferred probe pending" list — the kernel prints a summary of devices still waiting on dependencies, which often points straight at the missing provider. And I'd check whether the driver is registered as a `late_initcall` or has some ordering hint that's fighting the normal probe order.

The general principle: never assume a resource is ready just because the device tree says it exists. Use the frameworks, propagate `-EPROBE_DEFER`, and let the kernel's dependency graph sort it out.

**Possible follow-ups:**
- What's the difference between `-EPROBE_DEFER` and a hard probe failure, and how does the kernel decide when to retry a deferred probe?
- How would you debug this if the provider driver is built as a module rather than built-in?

## Q2: You're structuring a Yocto BSP for a product family where several boards share a common SoC and vendor BSP but differ in peripherals, device tree, and userspace packages. How would you organize the layers and recipes?

**Answer:** The goal is to keep the shared SoC and vendor support in one place, and push board-specific variation into thin layers on top, so that a change to the common BSP doesn't require touching every board.

I'd start with a base layer that holds the vendor's SoC support — kernel recipe, bootloader recipe, common machine configuration, and the shared device tree includes. That layer is essentially "what the silicon vendor gives us, cleaned up." On top of that, I'd create a machine layer per board (or per board family, if several boards are near-identical), each providing its own machine `.conf`, its own device tree, and any board-specific kernel config fragments. The machine `.conf` sets the things that genuinely differ: `MACHINE_FEATURES`, serial console, boot device, and the `KERNEL_DEVICETREE` variable pointing at the right DTB.

For userspace, I'd keep a separate distro or application layer that holds the product's packages, and use `IMAGE_INSTALL` overrides or `MACHINE_FEATURES` conditionals to pull in board-specific packages — for example, a touchscreen library only on the board that has a touchscreen. The key is to avoid duplicating recipes; if two boards need the same package but with different configuration, that's a `PACKAGECONFIG` or a `.bbappend` scoped to the machine, not a forked recipe.

The layering discipline matters: board layers should only `require` or `include` from the base layer, never the other way around. That keeps the dependency graph acyclic and lets you build any board by selecting its machine. I'd also keep the device tree sources in the base layer as shared `.dtsi` files, with each board's `.dts` including the common ones and overriding only what's different — that way a change to the SoC-level pinmux or clock tree propagates to every board automatically.

**Possible follow-ups:**
- How would you handle a board that needs a different kernel version from the rest of the family?
- Where would you put a board-specific patch to a shared vendor driver, and how would you keep it from affecting other boards?

## Q3: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path can hold, so the design has to separate the two paths at the data-structure level, not just at the scheduling level.

The real-time path should be as short as possible: it acquires the hardware, reads or writes the register or DMA buffer, and returns. It should never take a mutex that the logging path can hold, never allocate memory, and never wait on I/O. If the hardware access itself needs serialization, I'd use a spinlock with interrupts disabled for the shortest possible critical section — but ideally the real-time path is the only writer to the hardware, so no lock is needed at all.

The logging path should be decoupled through a lock-free ring buffer or a similar structure. The real-time path writes a record into the buffer (or, better, the DMA engine writes directly into a buffer that the real-time path just publishes), and the logging path reads from the buffer at its own pace. If the buffer fills, the logging path drops records rather than blocking the producer — that's the explicit trade-off: logging is best-effort, so it's allowed to lose data, but it's never allowed to slow down the real-time side.

For the userspace interface, I'd expose the real-time data through a mechanism that doesn't require the logging task to be involved — for example, a `read()` on a character device that returns the latest sample, or a memory-mapped buffer that userspace can poll. The logging task would use a separate interface, like a `read()` on a different file or a netlink socket, that drains the ring buffer.

The other consideration is priority: the real-time task should run at a priority that preempts the logging task, and the logging task should be structured so that even if it's preempted mid-operation, it doesn't hold any resource the real-time path needs. That usually means the logging path copies data out of the shared buffer under a short lock and then does all its formatting and I/O outside the lock.

**Possible follow-ups:**
- How would you size the ring buffer, and what would you do if the logging task consistently can't keep up?
- What kernel mechanisms would you use to make sure the real-time task actually gets scheduled when it needs to?

## Q4: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** The first thing I'd do is capture the actual boot log on a failing boot, because "falls back to network boot" usually means the boot sequence reached a point where the eMMC boot device wasn't available or the boot script failed, and U-Boot's `bootcmd` fell through to the next option in its list. The log will show which command failed and why.

The most common causes are: the eMMC device isn't enumerated in time (a power or reset timing issue), the boot partition or filesystem isn't readable (a corruption or partition-table issue), or the boot script itself has a conditional that's evaluating differently than expected. I'd check `mmc list` and `mmc dev` output on a failing boot to see whether the eMMC is even present. If it's intermittently missing, that points at hardware — power sequencing, reset timing, or a marginal clock — rather than software.

If the eMMC is present but the boot fails, I'd look at the `bootcmd` and any `boot_targets` or `bootorder` variables. U-Boot's distro boot framework will try each target in order, and if eMMC fails, it moves on to the next one — which might be network. The fix is usually to make the eMMC boot path fail loudly rather than silently falling through, or to remove network from the boot order entirely on a production image. On a development board you might want the fallback; on a production device you almost never do.

I'd also check whether the environment is being saved correctly. If the environment is stored in eMMC and the eMMC is the thing that's flaky, then a failed environment read could leave U-Boot with default variables that include network boot. That's a nasty failure mode because it looks like a boot-order problem but is actually a storage problem.

The systematic approach: reproduce with a serial console attached, capture the full log, identify the exact command that fails, and work backward from there. Don't assume it's the boot order until you've seen the log.

**Possible follow-ups:**
- How would you make the eMMC boot path fail explicitly rather than falling through to the next target?
- What would you check if the eMMC is present but the boot script intermittently can't read the kernel image?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** The first thing I'd do is separate the two concerns that are getting conflated: the technical change itself, and the manufacturing-line dependency on the current console output. They're both real, but they have different owners and different timelines, and treating them as one problem makes it look like a deadlock when it isn't.

On the technical side, moving a UART to a different pinmux group is a well-understood change — it touches the device tree pinmux node, the bootloader's early console configuration, and possibly the kernel command line. The risk is that early boot output is the primary diagnostic tool during bring-up and manufacturing test, so if the change is done wrong, you lose visibility exactly when you need it most. So I'd want the change done in a way that's verifiable: keep the old console configuration available as a fallback, test the new pinmux on a bench board before it goes anywhere near production, and make sure the bootloader and kernel agree on which UART is the console.

On the manufacturing side, the question is whether the line actually needs the console on that specific UART, or whether it just needs *a* console. If the line's test fixtures are wired to a specific physical connector, moving the UART means either rewiring the fixture or providing a second console path. That's a real cost, and it should be part of the decision — but it's a cost the hardware team may not have accounted for when they proposed the change.

So my approach would be: acknowledge both constraints, ask the hardware team what the new peripheral actually needs and whether there's an alternative pinmux that doesn't touch the console, and ask the manufacturing team what their fixture actually depends on. Then bring the options back to the group with the trade-offs laid out — keep the console and find another pin, move the console and update the fixture, or provide a secondary console path. The decision is a project-level one, not a BSP-level one, but the BSP team's job is to make the trade-offs visible and to make sure whatever is chosen is implemented safely.

**Possible follow-ups:**
- How would you validate the new pinmux without disrupting the manufacturing line?
- What would you do if the hardware team insists the change is necessary and the manufacturing team insists the console can't move?