# embedded-linux-bsp — Day 77

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but the kernel's `probe()` for a platform driver is deferred indefinitely because a `regmap`-based I2C sensor's parent bus is not yet available at the time the driver is registered?

**Answer:** A perpetual `-EPROBE_DEFER` on a `regmap`-based I2C sensor almost always means the driver's dependency chain is not resolving, not that the driver itself is broken. The first thing I'd do is confirm the deferral is actually happening and identify what's missing, rather than assuming. I'd enable dynamic debug for the driver and the deferred-probe core (`dyndbg` on the driver plus the `deferred_probe` tracepoints), then look at `/sys/kernel/debug/devices_deferred` — that file lists every device currently sitting in the deferred list, which immediately tells me whether the sensor is stuck and, by omission, which supplier it's waiting on.

From there I'd reason about the dependency graph. A `regmap`-I2C sensor depends on: the I2C adapter being registered, the sensor's own device tree node being present and correctly parented under that adapter, and any regulators/clocks/GPIOs the driver requests before it touches the bus. Common root causes are: the I2C controller node itself is deferred (so the bus never appears), the sensor node is placed under the wrong parent in the device tree so it's never bound to the adapter, a `vdd`/`vddio` regulator is referenced but its own driver is deferred or the regulator node is missing, or the driver requests a GPIO (e.g., a reset or interrupt line) that's owned by a pinctrl/gpio driver that hasn't probed yet. I'd walk the device tree from the sensor node upward and check each phandle.

A subtle one worth calling out: if the sensor driver calls `devm_regmap_init_i2c()` in `probe()` before its regulators are enabled, and the regulator is the deferred supplier, the driver returns `-EPROBE_DEFER` correctly — but if the driver instead *ignores* the regulator error and proceeds, you get a different failure mode (bus timeouts) rather than a clean defer. So I'd verify the driver is returning the defer rather than swallowing it.

If the dependency is genuinely circular or the supplier never probes, I'd check whether the supplier driver is even built in — a missing `CONFIG_` for the regulator or pinctrl driver produces exactly this "deferred forever, no error" symptom, because the kernel has nothing to bind the supplier to. `zcat /proc/config.gz | grep` the relevant symbols, or check the `.config` used for the build.

The fix is usually one of: correct the device tree parenting/phandles, enable the missing supplier driver in the kernel config, or add the missing regulator/clock to the sensor node. I'd avoid the temptation to "fix" it by forcing probe order with `initcall` tweaks or by removing the defer — that masks the real dependency and tends to resurface as an intermittent failure later.

**Possible follow-ups:**
- How would you tell the difference between a device that's deferred because its supplier is genuinely absent versus one that's deferred because of a device tree phandle typo?
- If the supplier driver is present and probes successfully but the sensor still defers, what would you check next?

## Q2: You're structuring a Yocto BSP for a product family where several boards share a common SoC and vendor BSP but differ in peripherals, device tree, and userspace packages. How would you organize the layers and recipes?

**Answer:** The goal is to keep the shared SoC/vendor foundation in one place and push board-specific variation into thin, composable layers, so that adding a new board is a matter of adding a layer and a machine config rather than forking anything.

I'd structure it as a small stack. At the bottom, the vendor's BSP layer stays unmodified — I treat it as a read-only upstream and never patch it in place. Above that, a `meta-<product>-common` layer holds everything shared across the family: the common kernel recipe append (or a `.bbappend` that adds the family's config fragments), common userspace packages, the shared image recipe, and any common recipes. Then one thin `meta-<product>-<board>` layer per board holds only what's genuinely board-specific: the machine `.conf` (SoC tuning, serial console, kernel device tree selection, bootloader config), the board's device tree(s), and any board-only packages.

The machine configuration is where most of the variation lives. Each board's `.conf` sets `MACHINE`, the `KERNEL_DEVICETREE`, the U-Boot config, and pulls in the right kernel config fragments via `KERNEL_FEATURES` or a `.scc`/`.cfg` fragment. Because the kernel recipe is shared, I'd express board differences as config fragments rather than separate kernel recipes — that keeps one kernel build path and avoids divergence.

For userspace, I'd use `IMAGE_FEATURES`, `IMAGE_INSTALL`, and `PACKAGE_FEED`/`BBMASK`-style mechanisms to vary packages per board, and where a board needs a different rootfs layout I'd use a rootfs overlay or a board-specific image recipe that `require`s the common one. The key discipline is: if two boards need the same change, it goes in the common layer; if only one board needs it, it goes in that board's layer. That keeps the common layer honest and prevents the "every board has its own copy of everything" drift that makes product families unmaintainable.

I'd also set up a `bblayers.conf` template and a `local.conf.sample` per board so a developer can switch boards with a single `MACHINE=` change, and I'd keep the layer priority and `BBFILE_PRIORITY` values deliberate so board layers can override common ones cleanly when they must.

**Possible follow-ups:**
- How would you handle a board that needs a different kernel version from the rest of the family without forking the common kernel recipe?
- Where would you put a patch that applies to the vendor kernel for all boards versus one that applies to a single board?

## Q3: How would you approach debugging a U-Boot environment where the board is supposed to boot from eMMC but intermittently falls back to a network boot that was never intended to be enabled?

**Answer:** An intermittent fallback to network boot means the boot sequence is reaching a point where the intended boot source fails and U-Boot's fallback path takes over — so the real question is *why the eMMC boot is failing intermittently*, and separately, *why the fallback is even reachable*. I'd treat those as two problems.

First, I'd make the failure visible. U-Boot's console output during the boot attempt is the primary evidence: I'd check whether the eMMC device is enumerated at all (`mmc list`, `mmc dev`), whether the partition/filesystem is found (`ls mmc 0:1` or the equivalent), and whether the boot script or `bootcmd` is failing at a specific step. If the console is quiet, I'd raise the log level (`setenv loglevel debug` or the build-time `CONFIG_LOGLEVEL`) and, if needed, add `CONFIG_MMC`/`CONFIG_MMC_SDHCI` debug. The intermittency suggests a timing or signal-integrity issue rather than a logic error — eMMC enumeration can fail if the controller is probed before the card's power rail is stable, or if the clock is set too aggressively for the board's layout.

Second, I'd look at the fallback path itself. U-Boot's `bootcmd` typically tries a list of boot targets; if network boot is in that list and reachable, a failed eMMC attempt will silently fall through to it. I'd inspect `bootcmd` and the `boot_targets`/`BOOT_TARGET_DEVICES` configuration and confirm whether network boot is intentionally in the list. If it isn't supposed to be there, the fix is to remove it from the boot target list or gate it behind an explicit condition, so a failed eMMC boot fails loudly instead of silently netbooting. That's a configuration hygiene issue independent of the eMMC flakiness.

For the root cause of the intermittent eMMC failure, I'd check: power sequencing (is the eMMC rail stable before the controller probes?), the `mmc` node's `vmmc`/`vqmmc` regulators and their `regulator-always-on`/`boot-on` flags, the bus width and speed mode in the device tree versus what the board actually supports, and whether the card's `non-removable`/`no-1-8-v` properties are correct. I'd also check for a marginal reset or a shared reset line that another peripheral is toggling. If it's signal integrity, the symptom often correlates with temperature or with a specific board revision, which is a useful clue.

The discipline I'd apply: fix the fallback so failures are observable, then chase the intermittent eMMC failure with the fallback removed, so I'm not chasing a moving target.

**Possible follow-ups:**
- How would you make a failed eMMC boot fail loudly rather than silently falling through to the next boot target?
- If the eMMC enumeration failure correlates with temperature, what would that suggest about the hardware?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path holds, and the logging path must never be able to extend the real-time path's latency. That rules out a naive shared mutex or a single queue that both paths contend on.

The design I'd reach for is a lock-free or minimally-contended handoff between the two paths. The real-time task's access to the device should be the only thing on the critical path: it acquires whatever hardware access it needs (a spinlock held for the shortest possible window, or better, a hardware mechanism that doesn't require a lock at all), performs the register access, and publishes the data. The logging task should never touch the hardware directly — it should consume data the real-time path has already published, so the two never contend on the device.

For the handoff, I'd use a single-producer/single-consumer ring buffer with a lock-free design: the real-time path writes into the ring and advances the write index with a release barrier; the logging path reads the read index with an acquire barrier and consumes. If the ring is full, the real-time path must not block — it either overwrites the oldest entry (if the logging data is best-effort and lossy is acceptable) or drops the new entry and increments a drop counter. The key property is that the real-time path's worst-case latency is bounded by the ring write, not by anything the logging task does.

If the hardware itself can only be accessed by one context at a time, I'd serialize access with a spinlock but ensure the logging path only ever takes it for a bounded, short operation, and never while holding another lock the real-time path needs. I'd also consider whether the logging path can be moved entirely out of the driver — e.g., the real-time path publishes to a buffer and a separate userspace or workqueue consumer does the logging — which removes the contention entirely.

I'd also think about priority: if the logging task runs at a lower priority and the real-time task at a higher one, a priority-inheritance-aware mutex would prevent inversion, but a spinlock is still preferable for the shortest critical sections. And I'd instrument the real-time path's latency (e.g., with a cycle counter or `trace_printk`) to prove the logging path never extends it, because "it should be fine" isn't evidence.

**Possible follow-ups:**
- How would you decide between a lock-free ring buffer and a spinlock-protected shared buffer for this handoff?
- If the logging task must not lose data, how would that change your design?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** This is a case where the technical change is small but the blast radius touches a process the manufacturing line depends on, so I'd treat it as a coordination problem first and a pinmux problem second.

My first move would be to separate the two concerns: *can* the pinmux change be made safely, and *what does the manufacturing line actually depend on*? I'd ask the hardware team what the new peripheral needs and whether there's an alternative pin assignment that avoids the debug UART entirely — sometimes the pin conflict is real, sometimes it's a default that can be reassigned. I'd ask the software team to be specific about what "baked in" means: is the UART pinmux in the bootloader's early pin config, in the kernel device tree, or both? Those have different change costs. And I'd ask manufacturing what they actually use the early console for — is it a hard requirement on every unit, or a debug aid used during bring-up and fault diagnosis?

With those answers, I'd frame the options for the group rather than picking one unilaterally. Option A: keep the debug UART where it is and find another pin for the new peripheral. Option B: move the UART, and accept that the manufacturing line's early-console procedure changes — which means updating the bootloader pinmux, the device tree, the manufacturing test procedure, and any fixtures or scripts that parse the console. Option C: move the UART but preserve an early-console path on a different interface (e.g., a USB-serial bridge or a secondary UART) so manufacturing isn't blocked.

I'd push for a decision that's explicit about the cost on each side, and I'd want the manufacturing impact quantified before agreeing to move the UART — "the line relies on it" is a strong signal that the change needs a migration plan, not just a code change. If the decision is to move it, I'd sequence it so the bootloader and device tree changes land together, the manufacturing procedure is updated and validated on a pilot unit before the line switches over, and there's a rollback path if the new console setup doesn't work on the line. I'd also make sure the change is captured in the DHF/design change process, since it touches a validated manufacturing step.

The thing I'd avoid is letting the decision be made on "it's just a pinmux change" — the code change is small, but the process change is what carries the risk, and that's what needs the planning.

**Possible follow-ups:**
- If manufacturing insists the early console must remain on the original UART, how would you resolve the pin conflict?
- How would you validate that the new console setup works on the manufacturing line before committing to the change?