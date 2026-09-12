# embedded-linux-bsp — Day 53

## Q1: How would you approach configuring a Linux kernel for an embedded product where you need to strip the image down to the minimum required drivers and features, while still keeping the configuration maintainable across kernel version bumps?

**Answer:** I'd treat the kernel config as a first-class artifact rather than something edited ad hoc in `menuconfig`. The workflow starts from a known-good base — typically the SoC vendor's `defconfig` or a reference board config — and then layers deliberate changes on top. The key discipline is to make every change intentional and documented, because a config that "just works" but nobody understands becomes unmaintainable the moment you bump the kernel version.

Concretely, I'd begin by identifying the actual hardware inventory: which buses are populated (I2C, SPI, UART, USB, CAN), which storage is used, which networking, and which peripherals are genuinely needed at boot versus later. Then I'd disable everything else. For trimming, `make localmodconfig` is a useful starting point because it derives a config from currently loaded modules, but it's a blunt instrument — it can miss drivers that are needed only on cold boot or only on a hardware variant, so I'd never ship its output unmodified. I'd cross-check against the schematic and the device tree.

For maintainability, I'd keep the config in version control as a `defconfig` fragment rather than a full `.config`, and use `savedefconfig` to produce a minimal diff against the architecture default. That makes kernel version bumps far less painful, because the diff is small and reviewable. Where the kernel supports it, I'd also consider config fragments (`merge_config.sh`) so that common options live in a shared fragment and product-specific options live in their own fragment — this scales well when you have multiple products on the same SoC.

I'd also be careful about the trade-off between `=y` and `=m`. Built-in is simpler for boot-critical drivers and avoids initramfs complexity, but modules give flexibility and smaller base images. For a medical device where the boot path must be deterministic and auditable, I'd lean toward building boot-critical drivers in and keeping the module set small and explicit.

Finally, I'd validate the config by actually booting it and checking `dmesg` for missing drivers, deferred probes, and unexpected fallbacks. A trimmed config that silently loses a peripheral is worse than a fat one.

**Possible follow-ups:**
- How would you detect that a driver you disabled is actually needed only on a rare boot path, like recovery or manufacturing mode?
- What's your approach to reviewing a kernel config change submitted by another engineer?

## Q2: How would you approach structuring a Yocto layer to support a product family where multiple boards share a common SoC and BSP but differ in peripherals, device tree, and userspace packages?

**Answer:** The goal is to avoid forking the vendor BSP layer and to avoid duplicating recipes across boards. I'd structure it as a small number of layers with clear responsibilities. A base layer holds the SoC-common pieces: the vendor kernel recipe append, the common device tree includes, and shared userspace components. Then a per-product layer (or per-product configuration within the same layer, depending on how different the products are) holds the board-specific device tree, machine configuration, and any packages unique to that variant.

The machine configuration is the natural place to express hardware differences. Each board gets its own `MACHINE` with its own `conf/machine/<board>.conf`, specifying the device tree, kernel recipe, serial console, and any `MACHINE_FEATURES`. The device tree itself can share a common `.dtsi` for the SoC and include board-specific `.dts` files, which mirrors how the kernel community structures things and keeps duplication low.

For userspace differences — say one variant has a touchscreen and needs gesture libraries, another doesn't — I'd use `IMAGE_FEATURES`, `MACHINE_FEATURES`, or a distro/override mechanism rather than branching recipes. `bbappend` files scoped to the machine override (e.g., `_<machine>`) let you add packages or change kernel config only for the relevant board. If the difference is large enough, separate image recipes that share a common `include` are cleaner than one image recipe full of conditionals.

The critical discipline is: never modify the vendor layer in place. Use `bbappend` and layer priority. If the vendor layer has a bug, carry a patch in your own layer with a clear commit message and a plan to upstream or drop it. This keeps the vendor layer upgradable, which matters enormously when the vendor releases a security fix.

I'd also keep the layer metadata honest: `layer.conf` with correct `BBFILE_PRIORITY`, `LAYERSERIES_COMPAT`, and a `README` documenting what each layer is for. And I'd set up CI to build every machine on every change, because the failure mode of a product-family layer structure is that one variant silently breaks while everyone tests the other.

**Possible follow-ups:**
- How would you handle a vendor kernel patch that conflicts with a patch you're carrying in your own layer?
- When would you split a product family into separate layers versus separate machines in one layer?

## Q3: How would you approach debugging a situation where a custom board running Linux boots successfully, but a peripheral that is present in the device tree never gets its driver's probe function called, and there are no obvious errors in the kernel log?

**Answer:** A silent non-probe is one of the more frustrating classes of BSP bug because the usual error paths — failed resource request, failed regulator, failed clock — usually leave a trace. If there's genuinely nothing in `dmesg`, I'd work through the probe pipeline systematically.

First, confirm the device tree node is actually being parsed. The compiled DTB on the running system is the ground truth, not the source `.dts`. I'd extract it from `/sys/firmware/devicetree/base` or decompile the DTB and check that the node exists, that its `compatible` string matches what the driver's `of_match_table` expects, and that `status` is `"okay"` rather than `"disabled"`. A surprising number of these turn out to be a `status` override in a board `.dts` that disabled a node inherited from the SoC `.dtsi`.

Second, check whether the driver is even built into the kernel or available as a module. If it's a module, is it loaded? If it's built-in, does the `compatible` string in the driver exactly match the one in the device tree? A single character difference means the match never happens, and the kernel has no reason to complain — it just doesn't bind.

Third, check the parent bus. If the peripheral is on an I2C or SPI bus, the parent controller must probe first. If the parent controller failed to probe or is disabled, the child never gets a chance. `ls /sys/bus/i2c/devices` or the equivalent for the bus is a quick way to see whether the child device was even instantiated.

Fourth, consider probe ordering and deferred probe. If the driver's probe returns `-EPROBE_DEFER` because a dependency (regulator, clock, GPIO, PHY) isn't ready, the kernel will retry later — but if the dependency never becomes available, the device silently never probes. `cat /sys/kernel/debug/devices_deferred` (when `CONFIG_DEBUG_FS` and the deferred-probe debug are enabled) is invaluable here. It tells you exactly which device is waiting on what.

Fifth, if all of that checks out, I'd add `initcall_debug` or enable dynamic debug for the driver to see whether probe is entered at all. If probe is entered and returns early without logging, that's a driver bug worth fixing regardless.

The meta-point is that "no error in the log" usually means the kernel never got far enough to have an error — the device was never matched, or the parent never came up. So I'd focus on the matching and dependency chain before suspecting the driver's internal logic.

**Possible follow-ups:**
- How would you tell the difference between a device that never probed and one that probed and then was unbound?
- What would you check if the device probes correctly but the driver's remove callback is never called on shutdown?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core principle is that the real-time path must never block on anything the logging path controls. That rules out a naive shared mutex or a single workqueue where both paths queue work. The design has to give the real-time path a bounded, predictable latency regardless of what the logging path is doing.

I'd start by separating the two concerns at the data level. The real-time task needs the device's current state or a fresh sample with a hard deadline. The logging task needs a history of samples, but it can tolerate latency and jitter. So the driver should expose two distinct interfaces: a low-latency read path for the real-time consumer, and a buffered path for logging.

For the real-time path, I'd use a lock-free or minimally-locked mechanism. If the device is memory-mapped and the real-time task can read a register directly, that's ideal — no kernel involvement at all beyond the mapping. If the read requires a bus transaction (I2C, SPI), the real-time task needs a way to issue it without contending with the logging task. One approach is a dedicated kernel thread or a high-priority work item that owns the bus access, with the real-time task reading from a shared buffer that the thread keeps fresh. Another is to give the real-time task its own pre-allocated transaction and use a per-CPU or per-context lock that the logging path never takes.

For the logging path, I'd use a ring buffer in kernel space that the real-time path writes into (or that the driver's own acquisition thread writes into) and the logging task drains. The ring buffer should be sized so that the logging task can fall behind without ever causing the producer to block — if it fills, the oldest data is dropped and a counter is incremented. Dropping log data is acceptable; blocking the real-time path is not. The logging task then reads from the ring buffer at its own pace and writes to wherever the logs go.

The subtle part is the shared hardware. If both paths need to touch the same registers, I'd serialize at the lowest level with a spinlock held for the shortest possible time, and ensure the real-time path's critical section is bounded. If the hardware supports it, I'd prefer to have the real-time path use a hardware feature — like a FIFO or a DMA channel — that the logging path doesn't touch at all, eliminating contention entirely.

I'd also be explicit about priority. The real-time task should run at a priority that preempts the logging task, and the logging task should be structured so that it yields frequently and doesn't hold any resource the real-time path needs. If the logging task does heavy work like formatting or writing to disk, that work should happen outside any lock the real-time path could contend on.

Finally, I'd validate with measurement, not assumption. Tracing the real-time path's latency under load from the logging path — using `ftrace`, `cyclictest`, or a hardware timer — is the only way to know whether the design actually meets its deadline. A design that looks correct on paper can still fail because of an unexpected shared resource, like a common clock domain or a bus arbitration delay.

**Possible follow-ups:**
- How would you size the ring buffer, and what would you do if the logging task consistently can't keep up?
- What kernel mechanisms would you use to give the real-time task priority without starving the rest of the system?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a pre-production review, the hardware team reveals that they need to change the main processor's boot mode strap resistors to accommodate a new flash part. The change means the processor will boot from a different interface (e.g., from SPI NOR to eMMC), and the bootloader and kernel configurations are already tuned for the current boot source. The project is six weeks from the start of a clinical trial. How would you handle this situation?

**Answer:** The first thing I'd do is resist the urge to either panic or immediately agree. The change is real and presumably driven by a supply or qualification reason, but the schedule impact is also real, and the two need to be weighed together with facts rather than assumptions.

I'd start by getting the full picture from the hardware team: why the change is necessary, whether it's a hard requirement or a preference, what the lead time is on the new flash part, and whether there's any alternative that avoids the boot-source change. Sometimes the "new flash part" can be accommodated on the existing interface with a different part number, or the strap change can be deferred to a later revision. Understanding the constraint space is the first step.

If the change is genuinely necessary, I'd scope the software impact honestly. Changing the boot source touches the bootloader configuration, the boot device selection logic, potentially the bootloader's own build (different defconfig or different build target), the kernel's root filesystem location and mount parameters, and any manufacturing or provisioning scripts that assume the old boot source. It also touches the test plan, because the boot path is the most safety-critical part of the system and needs to be re-validated. I'd write this down as a concrete list with rough effort estimates, not a vague "this will take time."

Then I'd bring that scope to the project manager and the hardware lead together, with options. Option one: make the change now and accept a schedule impact, with a clear statement of what slips. Option two: make the change but stage it — for example, support both boot sources in the bootloader for a transition period, so the clinical trial can proceed on the current hardware while the new hardware is brought up in parallel. Option three: defer the change to the next hardware revision if the current flash part can be sourced through the trial. Each option has different risk and cost, and the decision is a project-level one, not a BSP-level one.

If the decision is to proceed, I'd structure the work to de-risk it. The bootloader change is the highest-risk piece because a mistake there bricks the board, so I'd want the new boot path validated on a small number of prototype boards before it goes anywhere near the trial units. I'd also want a fallback — if the new boot source doesn't work, can we revert to the old one quickly? That means keeping the old boot configuration in the build system, not deleting it.

Throughout, I'd keep the regulatory and quality context visible. For a medical device, a change to the boot path is a change to the device's fundamental behavior, and it likely triggers a change-control process, re-testing, and documentation updates. The clinical trial timeline is a constraint, but it's not a reason to skip those steps — it's a reason to start them early and be honest about what's achievable.

The communication discipline matters as much as the technical work. I'd make sure the project manager has a clear, dated plan with dependencies and risks, and that the hardware team understands what the software side needs from them — schematics, strap configuration details, and prototype boards — and by when. A change like this fails more often from uncoordinated handoffs than from technical difficulty.

**Possible follow-ups:**
- How would you decide whether to support both boot sources simultaneously versus switching cleanly?
- What would you do if the hardware team insists the change is trivial and doesn't warrant a schedule adjustment?