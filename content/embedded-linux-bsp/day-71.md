# embedded-linux-bsp — Day 71

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel driver's `probe()` function is deferred indefinitely because a supplier it depends on never becomes available — with no obvious error in the kernel log?

**Answer:** Deferred probe is a normal part of Linux's device model — when a driver's `probe()` returns `-EPROBE_DEFER`, the kernel adds the device to a pending list and retries later, once the missing supplier appears. The tricky part is that the kernel doesn't log a loud error for this; it's a silent retry loop, so the first step is to confirm that deferral is actually what's happening rather than a genuine probe failure.

I'd start by checking `/sys/kernel/debug/devices_deferred` (or the equivalent debugfs node on that kernel version), which lists devices currently waiting on a supplier. If the device shows up there, the question becomes *which* supplier is missing. Common culprits are a clock, a regulator, a reset controller, a pinctrl state, or an upstream bus (I2C/SPI) that hasn't probed yet. I'd trace the driver's `probe()` path and look at every `devm_*` or `*_get()` call that can return `-EPROBE_DEFER` — `devm_clk_get()`, `devm_regulator_get()`, `devm_gpiod_get()`, `of_phy_get()`, etc. Then I'd cross-check the device tree to confirm the referenced supplier node actually exists, has the right `compatible`, and is itself enabled (`status = "okay"`).

A frequent root cause is a device tree phandle pointing at a node that is disabled or has a mismatched label, so the supplier never registers and the consumer defers forever. Another is a supplier driver that itself is deferring on something further up the chain — so the real blocker is two or three links away. I'd walk the chain until I find the node that is genuinely failing to probe, then fix that. If the supplier is legitimately optional, the driver should use the non-deferring variant (`devm_clk_get_optional()`, etc.) so it doesn't block forever.

**Possible follow-ups:**
- How would you tell the difference between a device stuck in deferred probe and one whose `probe()` was simply never called because the device tree node wasn't matched?
- What would you do if the missing supplier is a driver that is built as a loadable module and the module never gets loaded?

## Q2: You're structuring a Yocto BSP for a product family where several boards share a common SoC and vendor BSP but differ in peripherals, device tree, and userspace packages. How would you organize the layers and recipes?

**Answer:** The goal is to keep the shared SoC and vendor support in one place and push board-specific variation into thin, well-separated layers so that a change for one board can't accidentally break another.

I'd typically use three tiers. First, the vendor's BSP layer stays untouched — treat it as an upstream dependency and never fork it, because forking makes vendor updates painful. Second, a common product layer that holds everything shared across the family: the SoC machine configuration, the base kernel recipe and configuration fragments, common bootloader settings, and shared userspace packages. Third, one thin machine layer per board, each defining its own `MACHINE` conf, its device tree, any board-specific kernel config fragments, and only the extra packages that board needs.

The mechanism that makes this clean is `bbappend` files and `MACHINEOVERRIDES`. A board layer can append to the kernel recipe to add a device tree or a config fragment without copying the whole recipe. Machine-specific variables like `KERNEL_DEVICETREE`, `SERIAL_CONSOLES`, and `IMAGE_INSTALL:append` let each board diverge only where it must. For userspace differences, I'd use image recipes or packagegroups that the board's machine conf pulls in, rather than sprinkling conditionals through shared recipes.

The key discipline is that shared recipes should never contain `if MACHINE == ...` logic — that's a smell that the variation belongs in the board layer. Keeping the dependency direction one-way (board layers depend on the common layer, never the reverse) is what keeps the family maintainable as boards are added or retired.

**Possible follow-ups:**
- How would you handle a peripheral that exists on two boards but is wired to different pins or a different I2C address?
- What's your approach to testing that a change in the common layer doesn't regress a board you didn't intend to touch?

## Q3: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core principle is that the real-time path must never block on anything the logging path controls. That means the two access paths have to be decoupled, and the shared resource — the device — needs a synchronization scheme where the logging task can only ever wait on the real-time task, never the other way around.

I'd start by separating the two concerns at the driver level. The real-time task gets a dedicated, minimal code path: it acquires the device, does its transfer, and releases it, with no allocation, no sleeping locks, and no waiting on userspace. The logging path doesn't touch the hardware directly at all — instead, the real-time path writes samples into a lock-free ring buffer (single-producer, single-consumer, using atomic indices and memory barriers), and the logging task drains that buffer from a separate context, such as a workqueue or a kthread, and writes to the log.

For the hardware access itself, if both paths genuinely need the device, I'd use a spinlock with `spin_lock_irqsave` on the real-time side and make sure the logging side's critical section is bounded and short. But better still is to avoid contention entirely: if the device supports it, give the real-time task its own channel or DMA path so the logging task never shares the same register window. If they must share, the logging task should use `mutex_trylock()` and simply skip a sample rather than block — losing a log line is acceptable, missing a real-time deadline is not.

The other thing I'd watch is priority: if the logging task runs at a higher priority than the real-time task, it can preempt it even without a lock. So the logging task should run at a lower priority, or on a separate CPU if available, and the real-time task should be on `SCHED_FIFO` with a priority that guarantees it preempts the logger.

**Possible follow-ups:**
- How would you size the ring buffer, and what happens when the logging task can't keep up?
- What memory-ordering guarantees do you need on the ring buffer indices, and how would you verify them?

## Q4: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** An unintended network-boot fallback usually means the boot sequence is reaching a point where the eMMC boot fails or times out, and U-Boot's `bootcmd` or `boot_targets` list still contains a network entry that then succeeds. So there are two things to separate: why the eMMC path is failing intermittently, and why the fallback is even possible.

First I'd confirm the fallback is real by watching the console during a failing boot — U-Boot prints which boot target it's trying and why it moved on. If the eMMC read is returning an error or a timeout, that points at the storage path: a marginal power rail, a clock or timing issue on the eMMC interface, a bad partition or corrupted boot image, or a device that isn't ready when U-Boot probes it. Intermittency often means a timing or power-sequencing margin problem rather than a hard failure, so I'd look at whether the eMMC is being given enough time to initialize and whether the supply is stable at the moment U-Boot accesses it.

Second, I'd look at the environment itself. `bootcmd` may be defined to try eMMC and then fall through to `boot_targets` that include `pxe` or `dhcp`. If the fallback was never intended, the fix is to remove the network targets from the boot order, or to make the eMMC failure a hard stop rather than a silent fall-through. I'd also check whether the environment is being loaded from a stale or default source — for example, if the saved environment is corrupt, U-Boot may fall back to a built-in default that still has network boot enabled. Verifying where the environment is stored and whether it's being read correctly is part of the investigation.

The durable fix is to make the intended boot path explicit and fail loudly if it can't be taken, rather than relying on a chain that happens to end in a network boot.

**Possible follow-ups:**
- How would you make the eMMC boot failure visible on the manufacturing line without requiring a console?
- What would you check in the device tree or U-Boot config to confirm the eMMC controller is being initialized with the right timing parameters?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** The first thing I'd do is separate the two concerns that are getting tangled: the technical change itself, and the manufacturing dependency on the current console. The hardware team's need is legitimate — freeing pins for a new peripheral is a real constraint. The software team's concern is also legitimate, but it's a risk to be managed, not a reason to refuse.

I'd start by getting the facts on the table. How is the debug UART actually used on the manufacturing line — is it a hard requirement for every unit, or a diagnostic aid used during bring-up and failure analysis? If it's the latter, there may be more flexibility than the software team assumes. I'd also confirm whether the new pinmux group can carry the same UART function at the same baud rate, or whether it changes the electrical characteristics in a way that affects the console.

Then I'd look at what the change actually touches. In most cases the pinmux is defined in the device tree and, for early boot, in the bootloader's own configuration. If both are updated together and tested on a prototype, the risk is manageable — the danger is changing one and not the other, which is exactly the kind of thing that produces a silent early-boot failure. I'd want a plan that updates both, verifies the console comes up from the very first bootloader stage, and includes a fallback if the new pinmux doesn't work.

On the process side, I'd bring the manufacturing and hardware teams into the same conversation rather than negotiating through the software team. If the manufacturing line genuinely depends on the console, we need to know that before we commit, and we may need to stage the change — for example, keep the old pinmux available on early prototypes and switch once the new peripheral is validated. The decision should be made with the schedule and the manufacturing impact visible to everyone, not by one team asserting a constraint the others can't see.

**Possible follow-ups:**
- If the manufacturing team insists the console must stay on the current pins, how would you propose resolving the pin conflict?
- How would you verify that the early boot console still works after the pinmux change, given that it's the very first thing that could fail?