# embedded-linux-bsp — Day 75

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is deferred indefinitely because a supplier it depends on never becomes available — with no obvious error in the kernel log?

**Answer:** `-EPROBE_DEFER` is a cooperative mechanism, not an error, so the kernel deliberately stays quiet about it — the driver is telling the framework "I'm not ready yet, try me again later." The first thing I'd do is confirm that deferral is actually what's happening rather than a silent failure. I'd check `/sys/kernel/debug/devices_deferred` (or the equivalent debugfs node on that kernel version), which lists devices currently parked in the deferred state along with the reason. That immediately tells me *which* supplier is missing, rather than guessing.

From there the investigation branches. If the supplier is a regulator, clock, GPIO controller, or PHY, I'd verify that its own driver is present and built in (or loadable), that its device tree node exists and is enabled (`status = "okay"`), and that its compatible string actually matches a driver in the tree. A very common cause is a device tree node that references a supply by phandle, but the referenced node is either disabled, misspelled, or points at a parent that itself is deferred — deferral chains can be several links deep. I'd walk the chain from the deferred consumer back to the root supplier.

I'd also check probe ordering assumptions: if the supplier is on a bus that comes up late (I2C, SPI), and the consumer is a platform driver that probes early, deferral is expected and should resolve once the bus is up. If it *never* resolves, the supplier's own probe is likely failing for a different reason — so I'd enable dynamic debug for that supplier's driver and look at its probe path. Sometimes the supplier probes, returns an error that isn't `-EPROBE_DEFER`, and the consumer waits forever because the supplier never registers.

Finally, I'd rule out the mundane: is the supplier driver compiled as a module that never gets loaded? Is there a `regulator-always-on` or `boot-on` property missing that causes the supplier to be torn down? Is the clock provider's `#clock-cells` correct? These are all things that produce a silent, permanent deferral.

**Possible follow-ups:**
- How would you distinguish a genuine deferral loop from a one-time deferral that simply hasn't resolved yet at the time you're looking?
- If the supplier is a PMIC on I2C and the I2C controller itself is deferred, how would you untangle that chain?

## Q2: You're structuring a Yocto BSP for a product family where several boards share a common SoC and vendor BSP but differ in peripherals, device tree, and userspace packages. How would you organize the layers and recipes?

**Answer:** The guiding principle is to keep the vendor's BSP layer untouched and put all product-specific customization in layers above it, so that vendor updates can be pulled in without merge conflicts. I'd typically end up with a small hierarchy: the vendor's SoC/BSP layer at the bottom, a "common" layer for the product family that captures shared recipes, shared kernel config fragments, and shared userspace packages, and then one thin machine layer per board that contains only what's genuinely board-specific — the device tree, the machine configuration (`conf/machine/<board>.conf`), and any board-only packages.

The machine configuration is where the board identity lives: `MACHINEOVERRIDES`, the kernel device tree selection, the U-Boot defconfig, and the image recipe selection. Because Yocto's override mechanism is hierarchical, a board machine can inherit from a common family include and only override what differs. That keeps duplication low — if all boards share the same kernel recipe and the same rootfs baseline, that lives in the common layer, and each board layer just adds its deltas.

For the device tree, I'd keep the shared SoC-level `.dtsi` in the common layer and have each board's `.dts` include it and add board-specific nodes. That mirrors how the kernel community structures things and makes it obvious what's board-specific versus SoC-specific.

For userspace packages, I'd use `IMAGE_INSTALL` and `IMAGE_FEATURES` in the machine conf or in a family-level include, with board-specific additions in the board layer. If a board needs a package that others don't, that goes in its machine conf; if a package is common to the family, it goes in the family include. I'd also use `BBMASK` or layer priorities carefully so that a board layer can override a recipe from the common layer without forking it — for example, a `.bbappend` in the board layer that adds a board-specific patch or config fragment.

The test of whether the structure is right is: can I add a new board by creating one new layer with a machine conf, a device tree, and a couple of bbappends, without touching any existing layer? If yes, the layering is doing its job.

**Possible follow-ups:**
- How would you handle a board that needs a different kernel version from the rest of the family?
- Where would you put a shared systemd service that all boards run, and how would a single board disable it?

## Q3: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** Intermittent fallback to network boot usually means the primary boot path is failing *sometimes*, and U-Boot's boot order is walking down to the next entry. So the first question is: what's actually failing on the eMMC path, and why only sometimes? I'd start by capturing the full U-Boot console output across many boots — not just the successful ones — because the failure message is often a single line that scrolls past. If the console is quiet, I'd raise the log level or add `debug` to the boot command.

Common causes fall into a few buckets. First, timing: eMMC initialization can be marginal if the controller's clock or the card's power ramp is at the edge of spec, and it may fail on cold boots but succeed on warm ones, or vice versa. I'd check whether the failures correlate with temperature, power-on vs. reset, or specific boards. Second, the boot order itself: `bootcmd` might be defined as a sequence that tries eMMC, then falls through to `pxe` or `dhcp` if the eMMC read returns an error. If the eMMC read is flaky, the fallback triggers. I'd inspect `bootcmd`, `boot_targets`, and any `bootargs` that might be getting overwritten.

Third, the environment itself: if the environment is stored in eMMC and the eMMC is flaky, U-Boot might be loading a stale or corrupted environment, or falling back to a default environment that has network boot enabled. I'd check whether the environment is being saved correctly and whether the default environment (compiled in) has network boot in its boot order — because if the saved environment is lost, the default takes over.

Fourth, the network fallback might be enabled by a `boot_targets` variable that includes `dhcp` or `pxe` unconditionally. If the intent is eMMC-only, the cleanest fix is to remove network targets from `boot_targets` entirely, so a failed eMMC boot produces a clear error rather than a silent fallback. That also makes the failure visible instead of masked.

Once I've identified the root cause, I'd decide whether the fix is in hardware (eMMC signal integrity, power sequencing), in U-Boot configuration (boot order, environment storage), or both. And I'd add a deliberate, loud failure path so that if eMMC boot ever fails in the field, it's obvious rather than silently falling back to something unintended.

**Possible follow-ups:**
- How would you make the eMMC boot path more robust against marginal initialization without changing the hardware?
- If the environment is stored in eMMC and the eMMC is the thing failing, how would you ensure U-Boot can still recover?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path holds, and the logging path must never run in a context that can preempt or delay the real-time path. That shapes the whole design.

The first decision is where the real-time access happens. If the real-time task is in userspace, the driver needs to expose an interface that supports deterministic, bounded-latency access — typically a `read()` or `ioctl()` on a character device, with the driver's critical section kept as short as possible and no sleeping locks on that path. If the real-time task is in-kernel (or on a separate core), the driver might expose a kernel-internal API instead. Either way, the real-time path should use a spinlock or a lock-free mechanism, not a mutex, because a mutex can sleep and can be held by the logging path.

The second decision is how the logging path gets its data without touching the real-time path's critical section. The cleanest pattern is a lock-free ring buffer: the real-time path writes samples into the ring (or the driver's ISR does), and the logging path reads from it at its own pace. If the logging path falls behind, it drops samples rather than applying backpressure — that's the key property, because backpressure would be exactly the delay we're trying to avoid. The ring buffer needs a single producer and single consumer, or proper memory barriers if there are multiple, and the real-time side must never wait for space.

The third decision is priority and CPU affinity. If the system has multiple cores, pinning the real-time task to one core and the logging task to another removes most of the contention. If it's single-core, the real-time task should run at a higher scheduling priority (e.g., `SCHED_FIFO`) and the logging task at normal priority, and the driver must ensure the logging path never holds a lock the real-time path needs. Any shared data structure should be designed so the real-time side only ever does a non-blocking operation.

I'd also think about what "hard real-time" means here in terms of the deadline and jitter budget, because that determines how much buffering and how much work the ISR can do. If the deadline is tight, the ISR should do the minimum — timestamp and enqueue — and defer processing. And I'd want to measure worst-case latency under load, not just average, because the logging task's behavior under stress is exactly what could break the real-time guarantee.

**Possible follow-ups:**
- How would you verify that the logging task truly never delays the real-time path, and what would you measure?
- If the ring buffer fills because the logging task is stalled, what should the real-time path do — drop oldest, drop newest, or something else?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** The first thing I'd do is separate the two concerns that are getting conflated: the *technical* question of whether the pinmux change is feasible, and the *process* question of what the manufacturing line actually depends on and how much notice it needs. Both matter, but they have different owners and different timelines.

On the technical side, I'd want to understand exactly what "baked in" means. The pinmux for the debug UART typically appears in three places: the bootloader's early console setup, the kernel's device tree (or a `pinmux` node the kernel applies), and possibly a hardware strap or fuse. Changing it means touching at least the first two, and the risk is that early boot output — the very first lines from the bootloader and early kernel — disappears or goes to the wrong pins. That's a real risk, because early boot output is often the only visibility you have when something goes wrong before the console driver is up.

So I'd ask the hardware team to clarify the actual constraint: is the new peripheral's pin requirement hard, or is there an alternative pinmux that frees the needed pins without moving the debug UART? Often there's a third option that neither team has considered. If the move is genuinely necessary, I'd want to know whether the new pinmux can be made to coexist with the old one during a transition — for example, keeping the old UART active in the bootloader and switching in the kernel, or vice versa — so that manufacturing doesn't lose visibility overnight.

On the process side, I'd bring in the manufacturing line owner early, because "the manufacturing line relies on it" usually means there's a test fixture, a script, or a human procedure that expects console output on specific pins. That's a change-management problem, not just a firmware problem. I'd want to know how much lead time they need, whether the fixture can be updated, and whether there's a window where both pinmuxes are supported.

My recommendation would be to treat this as a change with a migration plan rather than a binary yes/no. If the change is necessary, we do it in a controlled way: update the bootloader and device tree together, keep a fallback console path if possible, validate on a small batch of boards before rolling to the line, and give manufacturing a clear cutover date with a documented procedure. If it's not necessary, we push back with the alternative pinmux. Either way, the decision gets made with both teams in the room and the risk explicitly stated, rather than one team unilaterally changing something the other depends on.

**Possible follow-ups:**
- If manufacturing says they can't update their fixture in time, what options would you propose?
- How would you validate that early boot console output still works after the pinmux change, given that it's hard to test automatically?