# embedded-linux-bsp — Day 54

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel module that registers a platform driver never has its probe function called, even though the device tree node for the peripheral is present?

**Answer:** A silent probe failure usually means the driver and the device tree node never actually matched, or the match happened but probe returned early without logging. I'd work through it systematically:

First, confirm the device tree node is actually present in the *running* kernel's view, not just the source `.dts`. On modern kernels, `/sys/firmware/devicetree/base/` exposes the live tree — I'd check that the node exists there and that its `compatible` string is exactly what the driver's `of_device_id` table expects. A single character difference, or a vendor prefix mismatch, silently prevents the match.

Second, check whether the driver is even bound to the bus. For a platform driver, look under `/sys/bus/platform/drivers/<driver-name>/` — if the device isn't listed there, the match failed. If it *is* listed but probe didn't run, the issue is elsewhere.

Third, verify the driver is actually compiled in or loaded. A `menuconfig` change that didn't take, or a module that failed to `insmod` due to a missing symbol dependency, will leave the driver absent with no obvious error at boot. `dmesg | grep <driver>` and `lsmod` confirm this.

Fourth, look for deferred probe. If the driver depends on a clock, regulator, GPIO, or PHY that isn't ready yet, `-EPROBE_DEFER` causes the kernel to retry later — but if the dependency never resolves, probe never succeeds. `dmesg` usually shows "probe deferred" messages, and `/sys/kernel/debug/devices_deferred` lists what's stuck.

Fifth, if all of the above looks correct, add a `pr_info` at the very top of probe to confirm entry, and check whether probe is returning an error before reaching the interesting code. A common trap is a `devm_*` allocation or a `platform_get_irq` that fails silently because the DT property name is wrong.

The key discipline is to separate "did the match happen" from "did probe run" from "did probe succeed" — each has a different debugging path.

**Possible follow-ups:**
- How would you tell the difference between a deferred probe and a probe that simply never matched?
- What would you check if the node is present, the compatible string matches, but the driver still isn't listed under `/sys/bus/platform/drivers/`?

## Q2: How would you approach structuring a Yocto layer to add a vendor kernel patch and a custom device tree to an existing BSP without forking the vendor's layer?

**Answer:** The goal is to extend, not fork — forking a vendor layer means you inherit the maintenance burden of every future vendor update, and you lose the ability to rebase cleanly. The right approach is a thin layer of your own that sits above the vendor's in `bblayers.conf` and uses Yocto's override and append mechanisms.

For the kernel patch, I'd create a `.bbappend` on the vendor's kernel recipe (e.g., `linux-vendor_%.bbappend`) that adds a `SRC_URI` entry pointing to my patch file in the layer's `files/` directory. The patch applies on top of the vendor's source without modifying their recipe. If the patch is version-specific, I'd pin the append to the exact kernel version with a `_%` wildcard only if I'm confident it applies across versions — otherwise a versioned append is safer.

For the device tree, there are two common approaches. If the vendor kernel builds DTBs from a `KERNEL_DEVICETREE` variable, I can append my custom `.dts` to that variable in the `.bbappend` and place the source file in the layer. If the vendor uses a separate `device-tree` recipe or a `dtb` package, I'd append to that instead. The important thing is to keep the `.dts` in *my* layer, not the vendor's, so it's version-controlled with my product.

For layer priority, I'd set `BBFILE_PRIORITY` appropriately — my layer should be higher than the vendor's so my appends win, but I need to be careful not to accidentally override recipes I didn't intend to touch. A narrow `.bbappend` with a specific recipe name avoids that.

Finally, I'd document the layer's purpose and the exact vendor layer version it's tested against, because the append is only valid as long as the vendor's recipe structure doesn't change underneath it. When the vendor updates, the append is the first thing to re-verify.

**Possible follow-ups:**
- What happens if the vendor updates their kernel recipe and your patch no longer applies cleanly — how would you handle that?
- How would you structure the layer if you needed to support two different custom device trees for two hardware variants?

## Q3: How would you approach debugging a U-Boot environment where the board boots from eMMC but intermittently falls back to a network boot, and the fallback is not intended?

**Answer:** An intermittent fallback to network boot means the boot sequence is reaching a failure point in the eMMC path often enough to trigger the fallback, but not consistently — so the root cause is likely marginal rather than a hard failure. I'd approach it in layers.

First, I'd confirm what the boot sequence actually is. U-Boot's `bootcmd` is often a chain of `if`/`then` or a `boot_targets` list, and the fallback is whatever comes after the eMMC attempt fails. I'd print the environment (`printenv`) and trace the exact commands. Sometimes the fallback is explicit in `bootcmd`; sometimes it's the default `boot_targets` order in distro boot.

Second, I'd capture the failure. The key is to see *why* the eMMC boot attempt fails on the boots where it falls back. U-Boot's console output during the failed attempt is the primary evidence — does it fail to read the partition, fail to load the kernel image, fail a checksum, or time out? Each points to a different cause. If the console is too noisy, I'd increase verbosity or add `echo` statements around the eMMC load.

Third, I'd consider marginal hardware or timing. Intermittent eMMC read failures can come from signal integrity issues on the eMMC bus, a marginal power rail, or a clock configuration that's slightly out of spec — all of which can pass on some boots and fail on others. I'd check whether the failure correlates with temperature, power-on vs. warm reset, or specific boards. If it's board-specific, it's likely hardware; if it's random across boards, it's more likely firmware or configuration.

Fourth, I'd look at the eMMC initialization sequence. If U-Boot is re-initializing the eMMC on every boot, a timing or retry issue in the init could cause intermittent failures. Some eMMC parts need specific delays or retry logic that a generic driver doesn't provide.

Fifth, I'd consider whether the fallback is actually a *recovery* mechanism that's working as designed but firing too often. If the eMMC path is genuinely marginal, the fix might be to harden the eMMC path (better signal integrity, more retries, a slower clock) rather than to remove the fallback.

The fix depends on the root cause: if it's a configuration issue, fix the config; if it's marginal hardware, fix the hardware or add retries; if it's a U-Boot bug, patch U-Boot. Removing the fallback without fixing the underlying failure would just turn an intermittent fallback into an intermittent boot failure.

**Possible follow-ups:**
- How would you determine whether the intermittent failure is in the eMMC hardware or in U-Boot's eMMC driver?
- If the fallback is a deliberate recovery mechanism, how would you decide whether to keep it or remove it?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path does. That rules out any design where both paths share a mutex, a spinlock held across a slow operation, or a single workqueue. The design principle is to decouple the two paths so the real-time path has a bounded, short critical section and the logging path consumes data asynchronously.

The typical structure is a producer-consumer split. The real-time task (or the driver's interrupt handler, if the device is interrupt-driven) writes data into a lock-free ring buffer or a double-buffered region. The write side uses only atomic operations or a short spinlock that's never held across a copy to userspace. The logging task reads from the buffer on its own schedule, draining it at whatever rate it can sustain.

For the buffer itself, a single-producer single-consumer ring buffer with atomic head/tail indices is the classic choice — no locks on the fast path, and the slow consumer can fall behind without affecting the producer. If the buffer fills, the producer either overwrites the oldest data (if the real-time data is more important than completeness) or drops new data (if the log must be complete but the real-time path can't wait). That's a policy decision that has to be made explicitly, not left to chance.

For the interface to userspace, I'd expose the real-time data through a `read()` on a character device or an `ioctl` that returns immediately with the latest sample, and the logging data through a separate `read()` that blocks until data is available. Keeping the two interfaces separate means the logging task's blocking behavior can't affect the real-time task's access.

For the real-time task specifically, I'd also consider whether it needs to run in kernel space at all. If the real-time task is a userspace process with `SCHED_FIFO`, the driver's job is just to make the data available with minimal latency — a `read()` that returns immediately, or a memory-mapped buffer the task can poll. If the real-time task is in kernel space (e.g., a high-priority kthread), the driver can hand data directly to it via a callback or a wait queue, but the callback must be short and non-blocking.

The key discipline is to never let the logging path's slowness propagate into the real-time path. That means no shared locks held across slow operations, no unbounded queues that the real-time path waits on, and no priority inversion where a low-priority logging task holds a resource the real-time task needs.

**Possible follow-ups:**
- How would you handle the case where the real-time task and the logging task both need to read the same hardware register?
- What would you do if the logging task consistently can't keep up with the data rate — drop data, or slow down the producer?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** This is a classic case where a hardware change that looks small has a software and manufacturing impact that isn't obvious from the hardware side. My job as BSP lead is to make that impact visible and to find a path that satisfies both teams' real needs, rather than letting either side win by default.

First, I'd make sure I understand the hardware team's actual constraint. Why does the new peripheral need *those* pins specifically? Is it a hard requirement from the peripheral's datasheet, or is it a layout convenience? Sometimes there's flexibility in which pins are used, and the pinmux conflict can be avoided entirely. I'd ask before assuming the change is necessary.

Second, I'd quantify the software impact honestly. Moving the debug UART means changes to the device tree (the pinmux node and the UART node), the bootloader's early console configuration, and potentially the kernel's earlycon setup. The risk isn't just "it might break" — it's that early boot console output is the primary diagnostic tool during bring-up and on the manufacturing line, and losing it makes every future boot failure harder to debug. That's a real cost that needs to be weighed against the hardware benefit.

Third, I'd look for a middle path. Options might include: keeping the debug UART on its current pins and finding different pins for the new peripheral; moving the debug UART but adding a second console (e.g., a USB-serial bridge) that the manufacturing line can use; or moving the UART but ensuring the new pinmux is validated early in the next prototype build so the manufacturing line has time to adapt. The right answer depends on how much flexibility the hardware team has and how much lead time the manufacturing line needs.

Fourth, if the change is genuinely necessary, I'd treat it as a coordinated change, not a software-only one. That means: a device tree change reviewed by both teams, a bootloader change tested on real hardware, a validation plan that confirms early console works on the new pins, and a communication plan for the manufacturing line so they know what's changing and when. I'd also want the change to land in a prototype build before it hits production, so any issues are caught early.

Throughout, I'd keep the conversation focused on the shared goal — shipping a working product — rather than on which team's preference wins. The hardware team isn't wrong to want the pins; the software team isn't wrong to worry about the console. The job is to find a solution that respects both.

**Possible follow-ups:**
- What would you do if the hardware team insists the pinmux change is non-negotiable and the manufacturing line says they can't adapt in time?
- How would you validate that the new pinmux doesn't introduce signal integrity issues on the debug UART?