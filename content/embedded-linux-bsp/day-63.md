# embedded-linux-bsp — Day 63

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is deferred indefinitely because a supplier it depends on never becomes available — with no obvious error in the kernel log?

**Answer:** Deferred probe is one of the more frustrating failure modes because the kernel is behaving correctly — it's just not telling you loudly why. The mechanism itself is straightforward: when a driver's `probe()` returns `-EPROBE_DEFER`, the driver core moves it to a deferred list and retries later, on the assumption that a dependency (a clock, regulator, GPIO, PHY, or another device) isn't ready yet. The problem is that if the supplier never registers, the consumer retries forever and the only visible symptom is a device that simply never appears.

My first step is to confirm the diagnosis rather than assume it. On a modern kernel, `/sys/kernel/debug/devices_deferred` (or the equivalent debugfs node) lists exactly which devices are stuck in deferred probe and, in many kernels, the reason string. If debugfs isn't mounted or the kernel is too old, enabling `initcall_debug` and dynamic debug on the driver core (`dyndbg="file drivers/base/* +p"`) will show the deferral and retry activity. That tells me whether I'm actually looking at deferred probe or at a driver that never matched at all — those are different problems.

Once I know it's deferred probe, I work backwards along the dependency chain. The usual culprits are: a regulator whose parent supply is missing or misnamed in the device tree; a clock provider that itself failed to probe (so it's a chain of deferrals, not a single one); a GPIO or pinctrl controller that hasn't registered; or a `-supply` property that references a node label that doesn't exist or is misspelled. I check the device tree binding for the consumer against the actual supplier node — property names and `phandle` references are a common source of silent mismatch, because a missing supply often just means the property is ignored rather than causing a hard error.

A particularly nasty variant is a circular dependency: device A defers on B, and B defers on A. The kernel can't resolve that, and it looks identical to a missing supplier. I look for that by tracing the full dependency graph rather than stopping at the first deferral.

If the supplier genuinely exists in hardware but isn't described in the device tree, the fix is to add the node and wire the reference. If the supplier is described but its own driver isn't enabled in the kernel config, that's a config issue. And if the dependency is real but the ordering is wrong, the right answer is usually to make the consumer properly express its dependency (via `-supply`, `clocks`, `resets`, etc.) so the driver core can order things, rather than to hack around it with initcall ordering.

The key discipline is: don't paper over deferred probe by forcing probe order or ignoring the return code. Deferred probe exists precisely so that ordering is expressed declaratively. If it's not resolving, something in the description is wrong, and that's what needs fixing.

**Possible follow-ups:**
- How would you distinguish a genuine circular dependency from a simple missing supplier, and what would you do about the circular case?
- If the supplier is an external chip on an I2C bus that itself probes late, how would you make sure the consumer's dependency is expressed correctly?

## Q2: You're structuring a Yocto BSP for a product family where several boards share a common SoC and vendor BSP but differ in peripherals, device tree, and userspace packages. How would you organize the layers and recipes?

**Answer:** The guiding principle is to separate what's common from what varies, and to make the varying parts additive rather than forked. A product family is exactly the case where a naive "copy the BSP per board" approach becomes unmaintainable, so the layer structure has to reflect the shared/variant split from the start.

I'd typically use three layers. First, a vendor or SoC layer that comes from the silicon vendor and is treated as read-only — I never modify it, I only consume it. Second, a common product-family layer that holds everything shared across the boards: the SoC-level machine configuration, the common kernel recipe and its configuration fragments, the shared bootloader recipe, and any userspace packages that every board in the family needs. Third, one thin machine layer per board, or a single board layer with per-machine `.conf` files, holding only what's genuinely board-specific: the device tree, the machine definition (`MACHINE`), any board-only kernel config fragments, and board-specific userspace packages.

The mechanism that makes this clean is `require`/`include` and `SRC_URI`-based fragments rather than copying. The common layer defines a base machine or a base kernel recipe; each board's `.conf` sets `MACHINE` and pulls in the common include, then adds its own device tree and config fragments. Kernel configuration is handled with `KERNEL_CONFIG_FRAGMENTS` or `.scc`/`.cfg` fragments layered on top of the vendor defconfig, so a board only expresses its delta. Device trees live in the board layer and are selected via `KERNEL_DEVICETREE`.

For userspace, I'd use `IMAGE_INSTALL` and packagegroups. A common packagegroup covers the shared runtime; each board's image recipe appends its specific packages. That way a board that needs an extra sensor library or a display stack just adds it, without touching the common image.

The payoff is that a kernel version bump or a vendor BSP update happens in one place — the common layer — and every board inherits it. The cost is a bit more upfront structure, but for a family of boards that's the right trade. The anti-pattern to avoid is per-board kernel recipes that are 95% identical; that's where maintenance burden and drift come from.

**Possible follow-ups:**
- How would you handle a board that needs a kernel patch the other boards don't, without forking the common kernel recipe?
- How would you manage the vendor layer if you need to override one of its recipes — `bbappend` versus a higher-priority layer?

## Q3: How would you approach implementing a kernel driver for a device that needs to be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path can hold, so the design has to decouple the two rather than have them share a lock or a buffer naively.

The first decision is where the real-time access happens. If the real-time task is in userspace, I'd avoid having it go through a path that can be preempted by the logging task's syscalls. The cleanest approach is to give the real-time path its own dedicated interface — a separate character device or a separate `ioctl`/`read` path — that takes a lock the logging path never touches. The logging path gets a different interface entirely.

The second decision is how data flows from the real-time side to the logging side. The real-time path should write into a lock-free or minimally-contended buffer — a ring buffer with a single producer and single consumer, using atomic indices rather than a mutex. The real-time producer never waits: if the buffer is full, it either overwrites the oldest entry or drops the new one, depending on which is acceptable for the application, but it never blocks. The logging consumer drains the buffer at its own pace. This is the classic single-producer/single-consumer ring buffer pattern, and it's the right tool here because the producer's cost is bounded and independent of the consumer.

The third decision is interrupt handling. If the device generates interrupts, the hard IRQ handler should do the minimum — timestamp, copy a small amount of data into the ring, acknowledge — and defer everything else to a threaded handler or a workqueue. The real-time task's latency is then bounded by the hard IRQ handler, not by the logging path.

I'd also be careful about the locking discipline on the hardware access itself. If both paths need to touch the same registers, the real-time path must be able to preempt or bypass the logging path. One way is to have the logging path only ever read from the ring buffer and never touch hardware directly — all hardware access goes through the real-time path. That removes the shared-resource problem entirely.

Finally, I'd verify the design under load: run the logging path at its worst case while measuring the real-time path's latency, and confirm the real-time deadline is met. If it isn't, the ring buffer or the interrupt split is usually where the fix is.

**Possible follow-ups:**
- How would you size the ring buffer, and what would you do if the logging consumer is consistently slower than the producer?
- If the real-time task is in userspace and the logging task is also in userspace, how would you keep them from contending on the same file descriptor?

## Q4: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** Intermittent fallback to network boot almost always means the primary boot path is failing sometimes, and U-Boot's boot order is then walking down the list to the next available option. So the first thing I'd do is stop treating the network boot as the bug and start treating it as a symptom — the real question is why the eMMC boot fails intermittently.

I'd start by capturing the full U-Boot console output on a failing boot, not just the tail. The boot order is controlled by `bootcmd` and the `boot_targets` environment variable, and U-Boot prints which target it's trying and why it moved on. If the eMMC device isn't even enumerated, that points to a hardware or initialization issue — power sequencing, clock, or the eMMC itself not responding within the timeout. If it enumerates but the boot partition or the kernel image isn't found, that points to a filesystem or partition layout issue.

A common cause of intermittent eMMC failures is timing: the eMMC needs a stable clock and supply before it responds, and if the board's power sequencing is marginal, the eMMC may occasionally not be ready when U-Boot probes it. I'd check whether the failure correlates with temperature, supply ramp, or a cold versus warm boot. If it's cold-boot-only, that's a strong hint about initialization timing.

Another common cause is the environment itself. If `bootcmd` is stored in eMMC and the eMMC read is flaky, U-Boot may fall back to a default environment that includes network boot. I'd check whether the environment is being loaded from eMMC or from a fallback source, and whether the fallback environment has network boot enabled. The fix there is usually to make the environment storage more robust, or to explicitly disable network boot in the fallback path so a failure is loud rather than silent.

I'd also look at whether the network boot is genuinely unintended or just undesired. If `boot_targets` includes `pxe` or `dhcp` and the board has a link, U-Boot will try it. Removing those from `boot_targets` and setting a bounded `bootretry` makes the failure mode explicit: the board either boots from eMMC or it stops, rather than silently doing something else.

The discipline here is to make the failure visible. A board that silently falls back to network boot in the field is worse than a board that fails to boot, because the failure is hidden. So part of the fix is usually to tighten the boot order and remove the unintended fallback, and part is to root-cause the intermittent eMMC failure underneath it.

**Possible follow-ups:**
- How would you determine whether the intermittent eMMC failure is a hardware timing issue versus a software timeout that's too short?
- What would you change in the U-Boot environment to make a failed eMMC boot fail loudly instead of falling back?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** This is a classic case where two teams are each right about their own concern, and the job is to find a path that satisfies both rather than to pick a winner. The hardware team needs the pins; the software team needs the manufacturing line's early console to keep working. Those aren't actually in conflict if we're deliberate about it.

My first move is to get the facts on the table before anyone commits to a position. What exactly does the manufacturing line depend on — is it the U-Boot console, the kernel console, or both? Is it used for pass/fail decisions, or just for visibility? How much lead time does the line need to adapt? And on the hardware side, is the new peripheral's pin requirement hard, or is there an alternative pinmux option that avoids the conflict? Often the "we must move the UART" conclusion softens once the actual constraints are laid out.

Assuming the move is genuinely necessary, the technical path is usually to keep the early console working on the new pins rather than to remove it. The device tree and bootloader pinmux can be updated to route the debug UART to the new group, and as long as the manufacturing fixtures are updated to the new physical location, the console still works. The risk the software team is flagging is real — a pinmux change touches early boot, and if it's wrong, you lose visibility exactly when you need it most. So the mitigation is to make the change in a controlled way: update the pinmux in both U-Boot and the kernel device tree in the same change, verify the console comes up on the new pins on a bench board before it goes anywhere near the line, and give the manufacturing team a clear transition plan with a known-good fallback.

I'd also want to understand whether the manufacturing line can tolerate a transition period where both pin groups are supported. If the board revision is changing anyway, the line may be re-fixturing regardless, and the pinmux change rides along with that. If the line is not changing, then the cost of the change is real and needs to be weighed against the benefit of the new peripheral — that's a project-level trade, not a purely technical one, and it should be escalated with the facts rather than decided unilaterally by either team.

The behavioral part is to keep the conversation on the shared goal — a board that works and a line that can test it — rather than letting it become hardware versus software. I'd propose a concrete plan: bench-verify the new pinmux, document the change, coordinate the line update, and keep a rollback path. That gives both teams something they can agree to.

**Possible follow-ups:**
- If the manufacturing line can't be updated in time, what options would you present to the project to keep the schedule?
- How would you verify the new pinmux is correct before the change reaches the manufacturing line?