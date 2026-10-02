# embedded-linux-bsp — Day 73

## Q1: How would you approach diagnosing a kernel module that loads successfully but whose `init()` function returns before the hardware it drives is actually ready, leading to intermittent failures on the first access?

**Answer:** The symptom — module loads cleanly, first I/O fails intermittently — usually points to a race between driver initialization and hardware readiness, or between driver init and a dependency (clock, regulator, reset line, or parent bus) that hasn't been brought up yet. The right approach is to stop treating "module loaded" as "device ready."

First, I'd confirm the failure mode: is it always the *first* access, or does it depend on timing? If it's the first access, the driver is likely touching registers before the peripheral has come out of reset or before its clock is stable. I'd check whether the driver's `probe()` is doing the right thing — in a proper platform driver, `probe()` should acquire all resources (clocks via `clk_get`/`devm_clk_get`, regulators via `regulator_get`, GPIOs for reset, and the parent bus) and only then touch hardware. If any of those return `-EPROBE_DEFER`, the driver must propagate that error so the kernel retries later, rather than proceeding with a half-initialized device.

Second, I'd verify the device tree describes the dependencies correctly. A missing `clocks`, `power-domains`, or `reset-gpios` property means the driver has no way to know it must wait. If the driver is a bus driver (I2C/SPI), I'd check that the parent controller is actually up before the child probes — the kernel's device model handles this via probe ordering, but only if the DT hierarchy is correct.

Third, I'd add instrumentation: `dev_dbg` at the start and end of `probe()`, plus a read of a known ID register immediately after resource acquisition. If the ID read fails, the hardware isn't ready; if it succeeds but a later access fails, the issue is elsewhere (power sequencing, a shared bus, or a reset that's being re-asserted).

Finally, I'd consider whether the driver needs an explicit "wait for ready" loop — polling a status bit with a timeout — rather than assuming the device is ready the moment the clock is enabled. Many sensors and PHYs have a power-on settling time that the driver must respect.

**Possible follow-ups:**
- How would you distinguish a genuine hardware readiness issue from a probe-ordering issue in the kernel's device model?
- What's the difference between returning `-EPROBE_DEFER` and simply sleeping in `probe()`, and when is each appropriate?

## Q2: You're structuring a Yocto BSP for a product that must support both a production image and a factory-test image, where the factory image needs additional diagnostic tools, a different kernel command line, and a writable rootfs. How would you organize this without duplicating the BSP?

**Answer:** The goal is to keep one BSP layer and express the two images as *variants* of the same recipes, not as two parallel BSPs. Duplication is the enemy here — the moment you fork the BSP, the two images drift and the factory image stops being a valid proxy for production.

I'd structure it in layers. The BSP layer (`meta-<board>`) contains the machine configuration, kernel recipe/bbappend, device tree, and bootloader — all shared. Then I'd add a separate `meta-<product>-images` layer (or a `recipes-images` directory in a product layer) that defines two image recipes: `production-image.bb` and `factory-test-image.bb`. Both `require` a common `core-image.bb` include that pulls in the shared base packages, so the common set is defined once.

For the differences:
- **Extra tools:** the factory image adds `IMAGE_INSTALL:append` with the diagnostic packages (e.g., `i2c-tools`, `memtester`, `mtd-utils`, a custom test harness). These live in the product layer, not the BSP.
- **Kernel command line:** this is a machine-level concern, so I'd expose it as a variable the image can override — e.g., `APPEND` in the machine conf, with the factory image using a bbappend or a separate machine conf that sets a different `APPEND`. Alternatively, use `KERNEL_CMDLINE` overrides in the image recipe. The key is that the kernel recipe itself is unchanged.
- **Writable rootfs:** the production image should be read-only (or use an overlayfs/read-only rootfs with a separate data partition), while the factory image can be read-write. This is an image-level property — `IMAGE_FEATURES` and the rootfs type — not a BSP change. I'd use `read-only-rootfs` in `IMAGE_FEATURES` for production and omit it for factory.

The important discipline is: **the BSP layer never knows which image is being built.** It provides the machine, kernel, and bootloader. The image layer composes them. That way, when the kernel or device tree changes, both images pick it up automatically, and the factory image remains a faithful test of the production stack plus diagnostics.

**Possible follow-ups:**
- How would you ensure the factory image doesn't accidentally ship with the writable rootfs or diagnostic tools enabled?
- Where would you put a kernel configuration fragment that only the factory image needs, and how would you apply it without forking the kernel recipe?

## Q3: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is never called, even though the device tree node for the peripheral is present and the driver is built into the kernel?

**Answer:** This is a classic "device tree says it's there, but the kernel doesn't bind" problem. The driver being built-in rules out module loading issues, so the fault is almost always in the match between the device tree node and the driver's `of_match_table`, or in the node's status/compatibility.

I'd work through it systematically:

1. **Check the node is actually enabled.** A node with `status = "disabled"` (or missing `status`, which defaults to enabled in most bindings but not all) won't be probed. I'd dump the live device tree with `dtc -I fs /proc/device-tree` or check `/sys/firmware/devicetree/base/` to confirm the node is present and enabled at runtime — not just in the source `.dts`.

2. **Verify the `compatible` string matches.** The driver's `of_match_table` must contain the exact `compatible` string from the DT node. A typo, a vendor prefix mismatch, or a fallback string the driver doesn't list will silently prevent binding. I'd grep the driver source for the compatible string and compare it character-for-character with the DT.

3. **Confirm the driver is actually built in.** `CONFIG_<DRIVER>=y` in the kernel config, and the driver's `builtin_platform_driver()` or `module_platform_driver()` macro is present. If the driver is built as a module but not loaded, `probe()` won't run — but the question says built-in, so I'd verify the config symbol is set and the object is in the link.

4. **Check for a missing dependency that causes silent deferral.** If `probe()` returns `-EPROBE_DEFER` and the dependency never appears, the driver will sit in the deferred probe list forever. `cat /sys/kernel/debug/devices_deferred` (with `CONFIG_DEBUG_FS`) shows exactly which devices are deferred and why. This is often the fastest way to find the culprit — a missing clock, regulator, or parent bus.

5. **Look at the parent bus.** If the peripheral is on an I2C or SPI bus, the parent controller must be probed first. If the parent's `probe()` failed or deferred, the child never gets a chance. I'd check `dmesg` for the parent controller's probe status.

6. **Check for address/resource conflicts.** If two nodes claim the same `reg` range or the same interrupt, the second one may fail to probe with a resource conflict. `dmesg` usually reports this, but it can be buried.

The single most useful tool here is `devices_deferred` plus `dmesg | grep -i probe`. If the driver's `probe()` is never called at all, the issue is upstream of `probe()` — matching, enabling, or parent bus. If it's called and returns an error, the issue is inside `probe()`.

**Possible follow-ups:**
- What's the difference between a driver that never probes and one that probes but fails, and how does the debugging path differ?
- How would you confirm at runtime that the kernel actually parsed the device tree node you think it did?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on the logging path. That rules out any design where both paths share a lock that the logging task can hold while doing slow work (writing to disk, formatting, or waiting on I/O). The design principle is **decoupling**: the real-time path writes to a lock-free or very-short-critical-section buffer, and the logging path drains that buffer asynchronously.

Concretely, I'd structure it as a producer/consumer with a bounded ring buffer:

- **Real-time path (producer):** acquires the data, writes it into a pre-allocated ring buffer, and returns. The critical section is a few instructions — a head index update with proper memory barriers. No allocation, no sleeping, no mutex that the logging path can hold. If the buffer is full, the real-time path must decide: drop the oldest sample (overwrite) or drop the new one. For a medical or safety context, dropping the oldest is usually correct — you want the most recent data — but this must be a documented, deliberate policy, not an accident.

- **Logging path (consumer):** a kernel thread or workqueue that wakes periodically, drains the ring buffer, and writes to the log destination. It can sleep, block on I/O, and take as long as it needs — it never touches the real-time path's critical section except to read the tail index.

The key implementation details:
- Use `kfifo` or a custom ring buffer with `smp_store_release`/`smp_load_acquire` for the indices, so the producer and consumer don't need a lock.
- Pre-allocate the buffer at `probe()` time — no `kmalloc` in the real-time path.
- If the real-time task is in userspace, expose the buffer via `mmap` or a `read()` that never blocks, and let the userspace real-time thread write directly. If it's in-kernel, expose a kernel API.
- For the logging side, use a workqueue or a dedicated kthread with a configurable drain interval. If the log destination is a filesystem, consider whether the filesystem can block — if so, the logging thread must be the only one touching it.

The failure mode to avoid is the "shared mutex" design: real-time task takes mutex, logging task takes mutex and then does a slow write while holding it, real-time task blocks. That's a priority inversion waiting to happen. If a lock is unavoidable, it must be a `raw_spinlock` held for a bounded, tiny duration, and the logging path must never hold it across a sleep.

**Possible follow-ups:**
- How would you handle the case where the ring buffer overflows, and what policy would you choose for a medical device?
- If the real-time task is in userspace, how would you guarantee it never blocks on the kernel side?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** This is a cross-team trade-off between a hardware need (freeing pins) and a software/manufacturing dependency (early boot console). The right approach is to make the trade-off explicit, quantify the risk, and find a path that doesn't silently break the manufacturing line.

First, I'd separate the two concerns: **the pinmux change itself** and **the early boot console dependency**. They're related but not identical. The pinmux change is a device tree and bootloader change — mechanical, but it touches the earliest boot stages. The console dependency is a process and validation concern — the manufacturing line uses the UART for test and debug, and if it moves, their fixtures and scripts break.

I'd start by asking the hardware team: is the new peripheral *required* for the current milestone, or is it a future feature? If it's future, the pinmux change can be scheduled after the current manufacturing validation, and the risk is deferred. If it's required now, we need a mitigation.

For the software side, I'd assess what actually breaks:
- **Bootloader:** the UART pinmux is set in the bootloader's early init. Changing it means re-validating the bootloader on all board variants.
- **Device tree:** the UART node's pinctrl reference changes. This is a small, reviewable change.
- **Manufacturing fixtures:** if the console moves to a different physical connector or pin header, the fixtures need to change. This is the real cost — it's not a software change, it's a line change.

I'd propose a phased approach: keep the current UART pinmux for the current production revision, and add the new pinmux as an *alternate* configuration selectable at build time or via a board variant. That way, the manufacturing line keeps working, and the new peripheral can be brought up on a separate variant or a later revision. If the hardware team insists the change must happen now, I'd ask for a manufacturing impact assessment and a validation plan — the console must be verified on the new pinmux before the line switches over, and there must be a rollback path if it fails.

The key is not to say "no" or "yes" unilaterally, but to surface the dependency, quantify the risk, and propose a staged path. If the decision is made to proceed, it should be a documented, agreed trade-off with a validation gate — not a silent change that breaks the line on the next build.

**Possible follow-ups:**
- How would you structure the device tree and bootloader to support two pinmux configurations without duplicating the whole board file?
- What would you include in a validation plan to confirm the new pinmux doesn't break early boot on all board variants?