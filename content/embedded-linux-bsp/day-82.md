# embedded-linux-bsp — Day 82

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is deferred indefinitely because a supplier it depends on never becomes available — with no obvious error in the kernel log?

**Answer:** `-EPROBE_DEFER` is a cooperative mechanism, not an error, so the kernel deliberately stays quiet about it — which is exactly why this class of bug is frustrating. The driver is saying "I need a resource that isn't registered yet, try me again later," and the deferred-probe list keeps retrying it. If the supplier never appears, the retries just keep happening silently.

My approach is to first confirm the deferral is actually happening rather than assuming it. The deferred-probe list is exposed in debugfs, so I'd check `/sys/kernel/debug/devices_deferred` (or the equivalent `deferred_probe` debugfs node) to see whether the device is sitting there and, if the kernel version exposes it, what it's waiting on. That immediately tells me whether this is a deferral loop or a probe that simply never ran.

Next I'd identify the supplier the driver is waiting for. Common culprits are a clock provider, a regulator, a pinctrl/GPIO controller, a reset controller, or a parent bus (I2C/SPI) that hasn't probed yet. The driver's `probe()` typically calls something like `devm_clk_get()`, `devm_regulator_get()`, or `devm_gpiod_get()` and gets `-EPROBE_DEFER` back. I'd trace which of those calls is returning the defer.

Then I'd check the supplier side. Is the supplier node present in the device tree? Is its driver built into the kernel or available as a module that's actually loaded? Is the supplier itself stuck in its own deferral, creating a chain? A very common root cause is a device tree phandle pointing at a node whose driver was never enabled in the kernel config, or a supplier whose own `probe()` is deferred because *its* parent bus isn't up.

I'd also verify probe ordering assumptions. If the supplier is on an I2C bus and the I2C controller driver is built as a module that loads late, the consumer may defer for a long time and then succeed — that's fine. But if the supplier driver is simply missing, it defers forever. Enabling `initcall_debug` and dynamic debug on the driver's probe path can make the retry pattern visible.

The fix is usually one of: enable the missing supplier driver, correct a device tree phandle or `status` property, fix a dependency cycle where two drivers each wait on the other, or — if the dependency is genuinely optional — change the consumer to treat the resource as optional so it doesn't defer on it.

**Possible follow-ups:**
- How would you distinguish a legitimate deferral that will resolve from a permanent one during bring-up?
- What would you do if two drivers were each deferring on the other, forming a cycle?

## Q2: You're structuring a Yocto BSP for a product family where several boards share a common SoC and vendor BSP but differ in peripherals, device tree, and userspace packages. How would you organize the layers and recipes?

**Answer:** The goal is to keep the shared SoC and vendor support in one place and push board-specific variation into thin layers on top, so a change to the common base doesn't require touching every board.

I'd start with a clear layer split. A `meta-<vendor>` or vendor BSP layer stays untouched as the upstream reference. Then a `meta-<product>-common` layer holds everything shared across the family: the SoC machine configuration fragments, common kernel config fragments, common recipes, and the base image. On top of that, one thin `meta-<board>` layer per board holds only what differs — the board's device tree, its machine `.conf`, its kernel config fragment, and any board-only userspace packages.

The machine configuration is the key lever. Each board gets its own `MACHINE` in its board layer, and that machine `.conf` selects the device tree, sets `SERIAL_CONSOLES`, and pulls in the right kernel config fragment via `KERNEL_FEATURES` or a `.scc`/`.cfg` fragment. The common layer provides the recipes; the board layer only overrides.

For the device tree, I'd keep the shared SoC `.dtsi` in the common layer and have each board's `.dts` include it and add its own peripherals. That way a SoC-level fix propagates to every board automatically.

For userspace packages, I'd use `IMAGE_FEATURES`, `IMAGE_INSTALL`, and `PACKAGECONFIG` rather than forking the image recipe. A board that needs an extra daemon adds it in its own image append or via a `MACHINE`-conditional in the common image. If the variation gets complex, a `DISTRO` or image variant per product tier is cleaner than a pile of conditionals.

The discipline that makes this work is: board layers contain only board-specific content, and anything that would be duplicated across two or more boards gets promoted to the common layer. I'd also keep the layer dependencies explicit in `layer.conf` so bitbake fails fast if someone builds a board without its required common layer.

**Possible follow-ups:**
- How would you handle a board that needs a patched version of a recipe shared with the rest of the family?
- How would you keep the common layer from accumulating board-specific conditionals over time?

## Q3: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the best-effort path must never block or delay the real-time path, so the design has to decouple them rather than have them contend for the same lock or the same hardware access window.

The first principle is to keep the real-time path as short and lock-free as possible. If the device is memory-mapped, the real-time task should be able to read or write its registers directly without taking a mutex that the logging path also holds. If the hardware requires serialized access, I'd use a spinlock with interrupts disabled only for the minimum critical section, and make sure the logging path never holds that lock while doing anything slow like formatting strings or writing to a buffer that could block.

The second principle is to give the logging path its own buffer and its own timing. The real-time path writes data into a pre-allocated ring buffer — ideally a lock-free single-producer/single-consumer ring, or a per-CPU buffer — and returns immediately. The logging task drains that buffer at its own pace. If the buffer fills, the logging path drops data rather than back-pressuring the real-time path. Dropping log data is acceptable; missing a real-time deadline is not.

The third principle is to avoid priority inversion. If a mutex is unavoidable, it should be a priority-inheriting mutex (`rt_mutex`), and the logging task should run at a lower priority than the real-time task. But the cleaner answer is to design so no shared mutex exists on the real-time path at all.

For the interface to userspace, I'd expose the real-time data through a mechanism that doesn't require the logging task to be involved — for example, a `read()` on a char device that the real-time consumer uses, separate from the logging path. If the real-time task is in userspace, I'd consider `ioctl` or `mmap` for the lowest-latency access, and make sure the driver's file operations don't take a global lock that the logging path also needs.

Finally, I'd verify the design under load: run the logging path at full tilt while measuring the real-time path's worst-case latency, and confirm the logging path's behavior degrades gracefully (drops data) rather than causing the real-time path to miss deadlines.

**Possible follow-ups:**
- How would you size the ring buffer, and what would you do if the logging task consistently can't keep up?
- How would you prove to a reviewer that the real-time path can't be blocked by the logging path?

## Q4: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** An intermittent fallback to network boot usually means the boot sequence is reaching a point where the intended boot source fails or times out, and U-Boot's boot order then tries the next entry — which happens to include network. So the real question is twofold: why is the eMMC path intermittently failing, and why is network in the boot order at all?

I'd start by making the boot process observable. U-Boot's `bootcmd` and `boot_targets` variables define the order, and the console output during boot shows which target is being attempted and why it's moving on. I'd capture full boot logs across many power cycles, including cold boots, to see whether the fallback correlates with something — temperature, power ramp timing, a specific board, or a specific number of cycles.

On the "why is network in the order" side, I'd inspect the environment. If `boot_targets` includes `pxe` or `dhcp`, that's the fallback path. It may be a leftover from a development environment, or it may be the default from the vendor's `defconfig`. The fix there is to set `boot_targets` explicitly to the intended order and, if network boot should never happen in production, remove it entirely. I'd also check whether the environment is being loaded from the right place — if the environment is stored in eMMC and eMMC is intermittently unreadable, U-Boot may fall back to a default environment that includes network.

On the "why does eMMC intermittently fail" side, I'd look at the eMMC initialization path. Common causes are marginal power ramp timing (the eMMC isn't ready when U-Boot probes it), a clock or bus-width setting that's marginal, signal integrity on the eMMC lines, or a reset/power sequencing issue where the eMMC isn't fully powered before access. I'd check whether the failure correlates with cold boot versus warm boot, since that often points at power sequencing or initialization timing. I'd also verify the eMMC's boot partition and the bootloader's expectations match — a mismatch in where U-Boot looks for the next stage can cause a timeout that triggers the fallback.

The fix is usually a combination: correct the boot order so network isn't an unintended fallback, and address the underlying eMMC initialization marginality — for example, adding a delay or retry in the eMMC init, correcting a power-sequencing assumption, or fixing a device tree property that affects the controller's timing.

**Possible follow-ups:**
- How would you make the fallback deterministic so it either always works or always fails loudly, rather than intermittently?
- What would you check in the eMMC device tree node if the failure only happens on cold boot?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** This is a case where a hardware optimization collides with a software dependency that has real operational consequences, so I'd want to separate the technical question from the process question and make the trade-off explicit rather than let either team win by assertion.

First, I'd get the facts on the table. What exactly does the manufacturing line depend on — is it the UART console for flashing and test, or is it a specific pin that's probed? Is the dependency on the *pin* or on the *console output*? Those are different problems. If it's console output, the UART can move as long as the console still works on the new pins. If it's a physical test fixture probing specific pins, that's a harder constraint.

Second, I'd assess the actual cost of the change. Moving a debug UART means updating the pinmux in the device tree, the bootloader's early console configuration, and any scripts or fixtures that reference it. That's a known, bounded amount of work — not a reason to reject the change outright, but a reason to schedule it deliberately rather than slip it in during a design review.

Third, I'd look for alternatives before accepting the disruption. Can the new peripheral use different pins? Can the debug UART stay where it is and the new peripheral share or time-multiplex? Is there a spare pinmux option that satisfies both? Often the hardware team's first proposal isn't the only option, and asking "what problem are we actually solving" surfaces a cheaper solution.

If the change is genuinely necessary, I'd treat it as a controlled change with a plan: update the device tree and bootloader, verify early boot console output on the new pins, coordinate with manufacturing to update any fixtures or scripts, and validate on a prototype before committing. I'd also make sure the change is captured in the requirements and traceability documentation, since in a medical device context a change to the boot console can affect manufacturing test procedures and therefore the device history record.

Throughout, I'd keep the tone collaborative. The hardware team has a legitimate need; the software team has a legitimate risk. My job as BSP lead is to make the trade-off visible, propose the least disruptive path that meets both needs, and own the coordination so neither team is surprised.

**Possible follow-ups:**
- How would you decide whether the manufacturing dependency is a hard constraint or something that can be updated?
- If the change had to happen mid-clinical-trial, how would you manage the risk?