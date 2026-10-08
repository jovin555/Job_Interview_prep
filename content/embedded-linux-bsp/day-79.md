# embedded-linux-bsp — Day 79

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is deferred indefinitely because a supplier it depends on never becomes available — with no obvious error in the kernel log?

**Answer:** `-EPROBE_DEFER` is a cooperative mechanism: the driver says "I'm not ready, try me again later," and the driver core re-queues it. If it loops forever, the dependency graph is broken somewhere, and the kernel is usually quiet about it because deferral is treated as normal, not an error.

My approach is to make the dependency graph visible rather than guess at it. First, I'd confirm the deferral is actually happening and identify the missing supplier — enabling `initcall_debug` and dynamic debug on the driver core (`dyndbg="file drivers/base/dd.c +p"`) usually prints which supplier lookup returned `-EPROBE_DEFER`. From there I'd walk the chain: does the supplier node exist in the device tree, is its driver built into the image (not just a module that never gets loaded), is its `compatible` string matched by a driver, and is *it* itself deferred on something further upstream? Deferral chains can be several links deep, and the real culprit is often at the root, not where the symptom appears.

Common root causes I'd check deliberately: a phandle in the device tree pointing at a node whose driver isn't compiled in; a clock or regulator provider that's registered but whose own probe is deferred; a `compatible` string typo that silently means "no driver will ever claim this"; or a supplier that's a module and the rootfs isn't up yet when the consumer probes. I'd also check whether the supplier's driver is even present in the kernel config — a missing `CONFIG_` symbol produces exactly this silent, endless deferral.

The fix depends on the cause: correct the device tree, enable the missing config, fix the `compatible` string, or adjust initcall ordering / module load order. The important discipline is to fix the *root* of the chain, not to paper over it by forcing probe order or removing the deferral — those hide a real dependency bug that will resurface under a different boot condition.

**Possible follow-ups:**
- How would you tell the difference between a genuine deferral loop and a driver that simply never matches the node?
- If the supplier is a module that loads late, what are your options to make the consumer probe reliably without hard-coding load order?

## Q2: You're structuring a Yocto BSP for a product family where several boards share a common SoC and vendor BSP but differ in peripherals, device tree, and userspace packages. How would you organize the layers and recipes?

**Answer:** The goal is to factor out what's common once and express only the differences per board, so adding a new variant is a small, reviewable change rather than a fork.

I'd structure it in layers. A **common SoC/BSP layer** holds the vendor kernel, bootloader, and the shared machine configuration — the parts that are identical across the family. On top of that, a **machine layer** defines one `MACHINE` per board, each pointing at its own device tree, its own kernel config fragments, and its own bootloader defconfig. Then a **distro or product layer** carries the userspace policy: which image features, which packages, which init system, and any product-wide configuration.

The per-board differences live in small, targeted artifacts: a device tree file per variant, kernel config *fragments* (not full defconfigs) that get merged onto the common base, and a machine-specific `IMAGE_INSTALL` or packagegroup for the userspace bits that only some boards need. The key discipline is that the common layer never references a specific board, and each machine layer never duplicates what the common layer already provides — otherwise you get drift where a fix lands in one variant and not the others.

For the device tree specifically, I'd keep a common `.dtsi` with the shared SoC and peripheral definitions and have each board's `.dts` include it and override or add only what differs. That mirrors the layer structure at the device-tree level and keeps the two in sync conceptually.

The payoff is maintainability: a kernel version bump or a security fix touches the common layer once, and every board inherits it. A new board is a new machine conf, a new device tree, and a small fragment — not a copy of the whole BSP.

**Possible follow-ups:**
- How would you prevent a board-specific hack from leaking into the common layer over time?
- Where would you put a userspace package that two of five boards need but the others must not have?

## Q3: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** An intermittent fallback to network boot almost always means the primary boot path is *sometimes* failing and U-Boot is silently moving to the next entry in its boot order — the fallback isn't a bug in itself, it's a symptom that the eMMC path isn't reliable.

First I'd make the failure visible. U-Boot is usually quiet about why it moved on, so I'd enable verbose boot (`bootargs`/`bootcmd` tracing, `setenv bootdelay` and console logging) and watch the actual sequence: does it fail to read the eMMC at all, fail to find the boot partition, fail to load the kernel, or fail to verify it? Each points somewhere different. I'd also check `bootcmd`/`boot_targets` and the `bootorder` environment — if network is in the list at all, any primary failure will fall through to it, so part of the fix is deciding whether network should even be a fallback in production.

Then I'd hunt the intermittency. eMMC issues that appear only sometimes often trace to: marginal power sequencing (the eMMC not fully ready when U-Boot first touches it), a clock or timing configuration that's out of spec, signal integrity on the eMMC lines, or a device-tree/`mmc` configuration mismatch. I'd correlate failures with things like temperature, power-on vs warm reset, and which board unit — if it's one unit, suspect hardware; if it's all units under a specific condition, suspect configuration or timing.

I'd also check whether the environment itself is being corrupted or reset — a bad `saveenv` or a worn environment sector can cause U-Boot to come up with a default (network-inclusive) environment instead of the intended one. And I'd verify the boot partition contents are actually intact, since a partially written kernel image would fail to load intermittently.

The fix is to make the primary path deterministic and to remove or tightly control the unintended fallback, then validate across many power cycles and units — not just a single successful boot.

**Possible follow-ups:**
- How would you distinguish a power-sequencing issue from a signal-integrity issue on the eMMC lines?
- What would you change in the U-Boot environment to make an unintended network fallback impossible in production?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path can hold. That rules out a naive shared mutex or a single queue that both paths contend on, because a slow logger could stall the real-time reader.

The design principle is to decouple the two paths so they share data but not locks in the critical section. The real-time task gets a lock-free or very short critical-section path to the hardware — ideally it's the only writer to the device, and it publishes data into a ring buffer using a lock-free single-producer/single-consumer scheme. The logging task is the consumer: it reads from the ring buffer at its own pace, and if it falls behind, it drops or overwrites old entries rather than ever pushing back on the producer. The real-time task never waits for the logger; at most it does an atomic index update.

For the hardware access itself, if both tasks genuinely need to touch the device, I'd serialize with a priority-inheritance-aware primitive (a real-time mutex) rather than a plain spinlock, and keep the held time as short as possible — ideally the real-time task does the register access and hands off data, and the logger only ever touches the buffer, never the hardware. If the logger must read registers, I'd give it a separate, non-blocking path or have the real-time task snapshot the values into the buffer for it.

I'd also think about what "never delay" means quantitatively: the real-time task's worst-case latency budget drives every choice — buffer size, whether the logger runs in a thread or a workqueue, whether interrupts are threaded, and whether the real-time task can tolerate any atomic operations at all. And I'd make the drop behavior explicit and observable, because silently losing log data is itself a problem in a medical context — the system should know and report that it dropped samples rather than pretend it didn't.

**Possible follow-ups:**
- How would you size the ring buffer, and what happens when it fills?
- If the real-time task and the logger both must read the same hardware register, how would you avoid the logger ever blocking the real-time read?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** This is a change-management problem where two legitimate needs are in tension: hardware wants pins back, and software/manufacturing depends on a stable early-boot console. My job is to make the trade-offs explicit and find a path that doesn't silently break the line.

First I'd get the facts on the table rather than let each side argue from assumption. What exactly does the manufacturing line use the early console for — is it a hard dependency for test fixtures, or a convenience? How early does it need to be available — before or after the bootloader hands off to the kernel? And what does the new peripheral actually require — is it a hard pin conflict, or could it be resolved another way (a different pinmux option, a different package, a spare pin)? Often the "we must move the UART" conclusion softens once the real constraint is understood.

Then I'd assess the change's true blast radius. Moving the debug UART touches the bootloader pinmux, the device tree, possibly the kernel command line, and any test scripts or fixtures that assume the current port. That's a cross-cutting change, so it needs a coordinated plan, not a one-line edit. I'd want it staged: change it in a branch, verify early boot output still works from the very first bootloader stage through kernel handoff, and confirm the manufacturing fixtures still function — or update them in the same change.

If the change is genuinely necessary, I'd sequence it so manufacturing isn't surprised: give them advance notice, a firmware/software version they can qualify, and a rollback path. If it can be avoided or deferred, I'd push back with the concrete cost — requalification of the boot flow and manufacturing fixtures — so the decision is made with eyes open rather than as a "small pinmux tweak."

The principle I'd hold to: never let a pinmux change land without verifying the *entire* boot chain and the downstream consumers, because early-boot console breakage is exactly the kind of thing that looks trivial in review and stops a production line.

**Possible follow-ups:**
- How would you verify early boot console output end-to-end after a pinmux change?
- If manufacturing can't tolerate any change to the console, what alternatives would you propose to free up the pins?