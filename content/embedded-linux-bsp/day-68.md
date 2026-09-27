# embedded-linux-bsp — Day 68

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is deferred indefinitely because a supplier it depends on never becomes available — with no obvious error in the kernel log?

**Answer:** Deferred probe is one of the more frustrating classes of bring-up bugs because the kernel is behaving correctly — it's just waiting on something that will never arrive, and the default logging is deliberately quiet to avoid flooding the log with retries. The first thing I'd do is confirm that deferred probe is actually the mechanism at play rather than a silent probe failure. The kernel exposes this through `/sys/kernel/debug/devices_deferred`, which lists every device currently sitting in the deferred state along with the reason string the driver returned. If the device appears there, the supplier name in that reason string tells me exactly what the driver is waiting on — a clock, a regulator, a PHY, a parent bus, a GPIO, or another device.

From there I'd trace the supplier chain. The most common causes are: the supplier node exists in the device tree but its own driver never probed (so it never registers the resource); the supplier is registered but under a different name than the consumer's `*-supply` or `clocks` phandle expects; the supplier is on a bus that itself hasn't come up yet (an I2C or SPI controller whose pins aren't muxed); or the supplier is gated behind a driver that's built as a module and simply isn't loaded in the initramfs. I'd check `dmesg` for the supplier's own probe messages, verify the phandle references in the decompiled device tree (`dtc -I fs /sys/firmware/devicetree/base`), and confirm the supplier's driver is actually compiled in or available as a module.

If the supplier is genuinely never going to appear — say, a regulator that was removed in a board revision but the device tree wasn't updated — the fix is to correct the device tree, not to hack the driver. If the supplier is a legitimate dependency that's just slow to initialize, the right answer is usually to make sure the supplier's driver is built-in and ordered correctly, or to move the consumer's probe to a later initcall level. What I would not do is remove the dependency from the driver just to make probe succeed, because that dependency is there for a reason — the hardware genuinely needs that clock or rail before it can be touched.

**Possible follow-ups:**
- How would you distinguish a deferred probe caused by a missing supplier from one caused by a supplier that is present but returns `-EPROBE_DEFER` on its own probe?
- What are the risks of using `initcall_deferred` or `fw_devlink` settings to force probe ordering, and when would you avoid them?

## Q2: You're structuring a Yocto BSP for a product family where several boards share a common SoC and vendor BSP but differ in peripherals, device tree, and userspace packages. How would you organize the layers and recipes?

**Answer:** The goal is to keep the shared parts shared and the differences isolated, so that adding a new board variant is a small, reviewable change rather than a fork of the whole BSP. I'd structure it as a small stack of layers with clear ownership boundaries.

At the bottom, the vendor's SoC BSP layer stays untouched — I never modify it directly, because that makes future vendor updates painful. Above that, a "common" layer holds everything shared across the product family: the kernel recipe with the vendor's patches, the bootloader recipe, the base image recipe, and any common userspace packages. This layer is where the SoC-level configuration lives.

Above that, one layer per board variant, or one layer with a machine configuration per variant if the variants are close enough. Each board layer contains only what's genuinely different: the machine `.conf` (which selects the device tree, the kernel config fragment, the bootloader config, and the image features), the device tree source, any board-specific kernel config fragments, and any userspace packages unique to that variant. The device tree is the natural place for peripheral differences — a board with a touchscreen has the touchscreen node and its dependencies, a board without simply doesn't include that node.

For kernel configuration, I'd use config fragments rather than a full defconfig per board, so the common base is defined once and each board adds or removes only what it needs. For images, I'd define a base image in the common layer and have each board layer either inherit it or extend it with `IMAGE_INSTALL:append` for board-specific packages. The `bblayers.conf` for each product then just lists the vendor layer, the common layer, and the one board layer it needs.

The payoff is that a new board variant is a new machine conf, a new device tree, and a small config fragment — maybe a few hundred lines total — and it inherits all the shared maintenance for free. It also makes it obvious during review which changes affect all boards versus one board.

**Possible follow-ups:**
- How would you handle a situation where two board variants need different versions of the same userspace package?
- What's your approach to keeping the common layer's kernel recipe in sync when the vendor releases a BSP update?

## Q3: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** Intermittent fallback to network boot almost always means the primary boot path is failing sometimes, and U-Boot's boot sequence is moving on to the next candidate in `bootcmd` or the boot order. So the first job is to figure out whether the eMMC boot is actually failing, or whether U-Boot is being told to try network boot for some other reason.

I'd start by capturing the full U-Boot console output on a failing boot, not just the tail. The messages right before the fallback usually name the failure — a timeout waiting for the eMMC controller, a CRC error reading the boot partition, a "no valid image" message, or a device tree / environment mismatch. If the console is too noisy to read, I'd temporarily raise the log level or add a `pause` before the fallback so I can inspect the state.

Common root causes I'd check: the eMMC's boot partition or the bootloader area has a marginal read that fails at temperature or voltage extremes; the eMMC's boot bus width or speed mode is set too aggressively for the specific part; the environment is stored in eMMC and a corrupted environment causes U-Boot to fall back to its compiled-in default `bootcmd`, which may include a network attempt; or the boot order in the environment lists network before eMMC and only the eMMC entry is failing intermittently.

I'd also check whether the fallback is actually coming from U-Boot or from something earlier — some SoCs have a ROM boot fallback that tries multiple boot sources, and that's configured by strap pins, not by U-Boot. If the strap pins are marginal or the boot source detection is flaky, the SoC itself may be choosing network boot before U-Boot even runs.

Once I know the failure mode, the fix depends on the cause: if it's a marginal eMMC read, I'd reduce the bus speed or retry the read; if it's a corrupted environment, I'd make the environment redundant and add a recovery path; if it's the boot order, I'd make the eMMC entry the only one in the normal path and gate network boot behind an explicit recovery command. What I would not do is simply remove network boot from the environment, because that removes a useful recovery mechanism — the right fix is to make the primary path reliable and keep network boot as an intentional fallback, not an accidental one.

**Possible follow-ups:**
- How would you make the U-Boot environment redundant so that a corrupted environment doesn't cause an unintended fallback?
- What's the difference between a SoC ROM boot fallback and a U-Boot `bootcmd` fallback, and how would you tell which one is happening?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path can hold. That rules out a naive design where both paths take the same mutex, because a best-effort task holding that mutex — even briefly — can delay the real-time task past its deadline. The design has to give the real-time path a lock-free or wait-free way to get its data, and let the logging path consume from a separate buffer at its own pace.

The standard pattern is a producer/consumer split with a lock-free ring buffer. The real-time task is the producer: it writes samples into a pre-allocated ring buffer using atomic operations, never taking a sleeping lock, never allocating, and never waiting on the consumer. The logging task is the consumer: it reads from the ring buffer at its own rate, and if it falls behind, the oldest samples are simply overwritten — the real-time path never blocks, and the logging path accepts that it may lose data under load. That's usually the right trade-off for logging, because logging is best-effort by definition.

In the kernel, this means the driver exposes two interfaces: a real-time-friendly interface (often a character device with `O_NONBLOCK` reads, or a memory-mapped region the real-time task can read directly) and a separate interface for the logging task (a `read()` on a different file descriptor, or a `poll()`-based interface). The two share the ring buffer but not a lock. The real-time task's `read()` must be guaranteed to return immediately with whatever is available, never sleeping.

If the hardware itself needs serialized access — say, a single SPI bus that both paths want to use — then the real-time path has to own the bus, and the logging path has to be fed from a buffer the real-time path fills, not from direct bus access. The logging path never touches the hardware directly. That's the key architectural decision: the real-time path owns the hardware, and everything else consumes from buffers.

I'd also make sure the real-time path's interrupt handler is as short as possible — just enough to move data into the ring buffer and signal the consumer — and that any work that can be deferred is deferred to a threaded handler or a workqueue that the real-time path doesn't depend on.

**Possible follow-ups:**
- How would you size the ring buffer, and what happens when the logging task consistently can't keep up?
- What kernel primitives would you use to implement the lock-free ring buffer, and what are the memory-ordering considerations?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** The first thing I'd do is separate the two concerns that are getting conflated: the hardware team's need for pins, and the manufacturing line's need for a reliable early boot console. Both are legitimate, and the disagreement is really about whether the change can be made without breaking the second one — not about whether the change is worth doing.

I'd start by getting the facts on the table. What exactly does the manufacturing line use the debug UART for? Is it a hard requirement during every boot, or only during initial programming and failure diagnosis? If it's only needed during certain phases, there may be a way to satisfy both sides — for example, keeping the UART on the current pins during early boot and switching the pinmux later, or providing an alternate debug path (a different UART, a USB-serial bridge, or a test point) that the line can use. If the line genuinely needs the UART on those exact pins at every boot, then the change has a real cost that the hardware team needs to understand.

I'd also assess the software cost honestly. Moving a UART pinmux means changes to the bootloader's pinmux setup, the device tree, and possibly the early console configuration. That's not trivial, but it's also not unbounded — it's a known, bounded change. The risk is in the early boot window, where the console has to come up before the full device tree is parsed. I'd want to prototype the change on a bench board before committing to it, so we know whether the early console still works.

Then I'd bring the three teams together — hardware, software, and manufacturing — and frame the decision as a trade-off with a clear owner. If the new peripheral is genuinely required and there's no alternative pin, the change has to happen, and the manufacturing line needs a migration plan: a firmware update to their test fixtures, a documented change to their procedure, and a validation run before the change goes live. If there's an alternative pin for the new peripheral, that's usually the cheaper path. If the manufacturing line's requirement turns out to be softer than stated — say, they only need the console during initial bring-up — then the change may be acceptable with a documented workaround.

What I'd avoid is letting the decision be made by whoever is loudest in the room. The right outcome is a documented decision with the trade-offs written down, a prototype to de-risk the software change, and a migration plan for the manufacturing line if the change goes ahead. That way, whichever way the decision goes, everyone understands what they're signing up for.

**Possible follow-ups:**
- How would you validate that the early boot console still works after a pinmux change, given that the console has to come up before most of the kernel is initialized?
- If the manufacturing line's requirement turns out to be a hard constraint, how would you work with the hardware team to find an alternative solution for the new peripheral?