# embedded-linux-bsp — Day 52

## Q1: How would you approach debugging a situation where a custom board running Linux boots successfully, but a kernel module that registers a platform driver never has its probe function called, even though the device tree node for the peripheral is present?

**Answer:** The first thing to establish is whether the driver is even being matched against the node, because "node present" and "driver bound" are two separate conditions. I'd start by confirming the driver is actually built and loaded — checking that the config symbol is enabled (built-in or module), and that the module is present in the running kernel. If it's a module, `modinfo` and `lsmod` tell me whether it loaded at all; a silent load failure often points to a missing dependency or a symbol mismatch.

Next I'd look at the device tree side. The node must have a `compatible` string that exactly matches one of the driver's `of_device_id` table entries — a typo or a vendor prefix mismatch is a classic cause of a probe that never fires. I'd dump the live device tree (`/proc/device-tree` or `dtc` on the decompiled blob) to confirm the node survived into the kernel, because a node can be present in the source `.dts` but dropped by an overlay, a `status = "disabled"` property, or a bad phandle reference.

Then I'd check the driver's probe prerequisites. Even with a matching compatible, probe can be deferred indefinitely if a resource it depends on isn't ready — a clock, regulator, reset line, or GPIO referenced by phandle that hasn't been registered yet. `dmesg` usually shows "probe deferred" or "failed to get ..." messages, and `/sys/kernel/debug/devices_deferred` lists devices stuck in deferred probe. That debugfs file is often the fastest way to see the real blocker.

Finally, I'd verify the node isn't being consumed by a different driver first (two drivers claiming the same compatible), and that the parent bus is actually probing. If the parent never probes, children never get a chance. Working outward from "is the driver loaded" → "does the compatible match" → "are dependencies satisfied" → "is the parent alive" covers the vast majority of silent no-probe cases.

**Possible follow-ups:**
- How would you tell the difference between a probe that was deferred and one that failed outright?
- What would change in your approach if the node were added via a device tree overlay rather than the base tree?

## Q2: How would you approach structuring a Yocto layer to add a vendor kernel patch and a custom device tree to an existing BSP without forking the vendor's layer?

**Answer:** The guiding principle is to never modify a vendor or upstream layer in place — you add a layer on top that overrides or extends what's below it. Forking the vendor layer means you inherit the maintenance burden of every future vendor update, and you lose the ability to cleanly rebase. So the approach is a new layer with the appropriate priority and layer dependencies declared in its `layer.conf`.

For the kernel patch, the clean way is a `.bbappend` on the vendor's kernel recipe. In that append I'd add the patch to `SRC_URI` and, if needed, adjust `FILESEXTRAPATHS` so BitBake finds my patch files in my layer rather than the vendor's. The patch itself should be a proper `git format-patch`-style file with a clear commit message, so it's reviewable and can be upstreamed later if appropriate. I'd keep the patch minimal and scoped — one logical change per patch — so that when the vendor bumps their kernel, I can tell quickly whether my patch still applies.

For the custom device tree, there are two common patterns. If the vendor kernel recipe builds device trees from a `KERNEL_DEVICETREE` variable, I can append my `.dts` to that list and provide the source file in my layer. Alternatively, if the device tree is built separately, I'd add it via a dedicated recipe or a machine configuration that points at my `.dts`. Either way, the machine conf in my layer selects the device tree and any related kernel config fragments, keeping the vendor's machine definition untouched.

The key discipline is layering: my layer depends on the vendor layer, overrides only what it must, and stays thin. That way a vendor update is a rebase of a small append rather than a merge conflict across a forked tree.

**Possible follow-ups:**
- How would you handle a situation where the vendor's kernel recipe doesn't expose a clean variable for adding device trees?
- What are the trade-offs between a `.bbappend` and a full recipe override in this scenario?

## Q3: How would you approach debugging a U-Boot environment where the board boots from eMMC but intermittently falls back to a network boot, and the fallback is not intended?

**Answer:** Intermittent fallback to network boot almost always means the primary boot path is failing *sometimes*, and U-Boot is walking down its boot order to the next available option. So the real question isn't "why does it network boot" — it's "why does the eMMC boot path fail intermittently." I'd treat the network boot as a symptom, not the disease.

First I'd confirm the boot order and the fallback behavior. `bootcmd`, `boot_targets`, and any `BOOT_ORDER`-style variables define the sequence. If network is in the list after eMMC, then any eMMC failure — even a transient one — will trigger the fallback. I'd consider whether the fallback should exist at all in production; often the right fix is to remove network from the boot targets entirely so a failure is loud rather than silently masked.

Then I'd hunt the intermittent eMMC failure. Candidates: marginal power sequencing on the eMMC rail (the part not being ready when U-Boot probes it), a timing or clock issue on the eMMC interface, a bad block or partition table that's occasionally unreadable, or a reset/initialization race. Because it's intermittent, I'd want to correlate failures with conditions — cold boot vs warm boot, temperature, supply ramp. Adding U-Boot debug output around the eMMC init and read steps, and logging the exact error, is the starting point.

I'd also check whether the environment itself is being saved reliably. If `saveenv` writes to eMMC and occasionally corrupts or fails, the environment could be reverting to a default that includes network boot. That's a different root cause than a read failure, and it's worth ruling out early by checking whether the environment is stored in eMMC, SPI flash, or EEPROM, and whether its checksum is valid on the failing boots.

The disciplined approach: reproduce with logging, isolate whether the failure is in eMMC init, read, or environment storage, fix the underlying marginal condition, and then decide deliberately whether a fallback path should exist in production at all.

**Possible follow-ups:**
- How would you make a boot failure visible to the manufacturing line instead of silently falling back?
- What power-sequencing measurements would you want to correlate with the intermittent failures?

## Q4: How would you approach implementing a kernel driver for a device that must be accessed by both a hard real-time task and a best-effort logging task, where the logging task must never delay the real-time access?

**Answer:** The core requirement is that the real-time path must never block on anything the logging path holds, so the design has to decouple them rather than have them contend for the same lock or the same bus transaction. The first decision is where the real-time access happens. If the deadline is truly hard, the safest place is often not a userspace task at all but the driver's own interrupt or a high-priority kernel thread, with the real-time consumer reading from a buffer the driver fills — that removes scheduler latency from the critical path.

For the shared resource, I'd avoid a single mutex that both paths take. Instead I'd give the real-time path a lock-free or very short critical section — for example, a ring buffer where the producer (real-time) writes and the consumer (logging) reads, with only atomic index updates and no blocking. The logging task reads from the buffer at its own pace; if it falls behind, it drops or overwrites old data rather than back-pressuring the real-time producer. That's the key inversion: the best-effort task must be the one that yields, never the real-time one.

If both paths genuinely need to touch the same hardware register or bus, I'd serialize only the hardware access with a spinlock held for the minimum possible time, and make sure the logging path never holds it across a sleep or a slow operation. Any I/O the logging path does — writing to a file, sending over a socket — happens after it has copied data out of the shared buffer, outside the critical section.

I'd also set priorities deliberately: the real-time thread at a high SCHED_FIFO priority, the logging thread at normal or low priority, and I'd verify with a latency measurement that the real-time path's worst-case time is unaffected by logging activity. The design principle throughout is that the real-time path owns the timing, and the best-effort path is structured so it can always be preempted or made to wait.

**Possible follow-ups:**
- How would you verify that the logging task truly never affects the real-time path's worst-case latency?
- What would you do if the hardware itself can only be accessed by one path at a time and the access is slow?

## Q5: Behavioral — You're the BSP lead for a medical device project, and during a design review the hardware team proposes moving the main processor's debug UART to a different pinmux group to free up pins for a new peripheral. The software team says the current pinmux is baked into the device tree and bootloader, and changing it risks breaking early boot console output that the manufacturing line relies on. How would you handle this situation?

**Answer:** I'd treat this as a coordination and risk-management problem rather than a purely technical one, because both teams have legitimate concerns and the disagreement is really about sequencing and risk ownership. My first move is to get the facts on the table: exactly which pins are needed, why the new peripheral can't use an alternative, and precisely what depends on the current debug UART — is it just the manufacturing line, or also field diagnostics, regulatory test fixtures, or the bootloader's own early output?

Then I'd separate the two questions that are getting conflated. The first is "can the pinmux change be made technically?" — almost certainly yes, with device tree and bootloader updates. The second is "what breaks, and who absorbs that risk?" — that's where the manufacturing dependency matters. Early boot console output is often a lifeline for the production line; if it disappears or moves, the line needs a new procedure, new fixtures, or a new test step, and that has a cost and a lead time.

I'd propose options rather than a yes/no. One option is to keep the debug UART where it is and find the new peripheral a different pin or a different interface. Another is to move the UART but preserve an equivalent early-boot console on the new pins, so the manufacturing procedure changes minimally. A third is to move it and accept the manufacturing change, but only with a documented migration plan and a validation step. I'd bring the manufacturing stakeholder into the conversation rather than deciding for them, because they own the impact.

Throughout, I'd keep the discussion anchored on evidence and on the regulatory context — in a medical device, changing anything that affects traceability or test coverage needs to be deliberate. My role as BSP lead is to make the technical trade-offs visible, quantify the software and validation effort for each option, and drive the group to a decision that someone explicitly owns, rather than letting it be decided by whoever pushes hardest.

**Possible follow-ups:**
- How would you handle it if the hardware team had already committed the pinmux change in a board revision?
- What would you document to make sure the manufacturing impact is tracked through to validation?