# firmware — Day 85

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt rate is high enough that servicing every interrupt individually would consume an unreasonable share of CPU time?

**Answer:** The first step is to quantify the problem rather than assume it: measure the actual interrupt rate, the worst-case ISR execution time, and the resulting CPU utilization. If the ISR is short and the rate is manageable, the simplest correct design is often to keep it — premature optimization here creates complexity for no benefit. When the rate genuinely becomes a bottleneck, the standard approach is to decouple the interrupt from the work. The ISR does the minimum necessary to acknowledge the peripheral and move data into a buffer — ideally using DMA so the CPU isn't involved in the bulk transfer at all — then signals a deferred context (a work queue item, a thread, or a bottom-half) to do the processing. This keeps interrupt latency bounded and lets the scheduler decide when the heavier work runs.

If DMA isn't available or appropriate, another option is to reduce the interrupt rate itself: many peripherals support a FIFO or watermark level, so you can configure the interrupt to fire only when a batch of samples has accumulated rather than on every byte or sample. That converts a per-event interrupt into a per-batch interrupt and cuts overhead proportionally. A third consideration is interrupt coalescing or rate-limiting at the driver level, though this must be done carefully so you don't silently drop data.

The key trade-offs are latency versus throughput versus CPU headroom. Deferring work adds latency to the response, which matters if the peripheral has a hard deadline. Batching adds buffering requirements and can increase worst-case latency for the first sample in a batch. DMA adds setup complexity and buffer management but is usually the cleanest answer for continuous streams. I'd also make sure the design has a way to detect and report overruns — if the CPU genuinely can't keep up, that's a system-level problem that should surface as a measurable error rather than as silent data loss.

**Possible follow-ups:**
- How would you decide the buffer size and watermark level for a DMA-based design, and what happens if the consumer thread falls behind?
- What would you measure to prove the deferred-processing design actually solved the problem rather than just moving it?

## Q2: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core issue is that an edge-triggered signal is a claim about the world, and glitches mean that claim is sometimes false. The first line of defense is to not trust the edge alone — after receiving the interrupt, the handler should verify that the peripheral actually has valid data before acting on it. Most peripherals expose a status register or a data-ready bit that reflects the true state; reading that bit and only proceeding when it's set filters out spurious edges cheaply. If the peripheral doesn't offer such a status, you can validate the data itself — check a CRC, a range, or a sequence number — and discard anything that fails.

The second consideration is hardware and electrical: glitches often have a physical cause such as insufficient debouncing, a slow or noisy edge, or a missing pull-up. A small RC filter or a Schmitt-trigger input can eliminate many of these before firmware ever sees them, and it's worth raising with the hardware team rather than trying to solve everything in software. Firmware should also be robust to the case where the glitch is real and unavoidable.

The third piece is defensive design in the handler: treat the interrupt as a hint, not as ground truth. If the handler reads the status and finds nothing, it should return quickly without side effects. If the design uses a state machine, a spurious edge should land in a state where it's simply ignored rather than causing an invalid transition. I'd also add a counter for "interrupt fired but no data" events so the behavior is observable — if that counter climbs, it tells you the glitch rate is significant and worth addressing at the source.

**Possible follow-ups:**
- How would you distinguish a genuine glitch from a real data-ready event that arrived and was consumed by another part of the system before your handler ran?
- What would you do if the peripheral's status bit itself is unreliable and occasionally reports ready when no data is present?

## Q3: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the first thing to recognize is that attaching a debugger changes the system in several ways at once: it halts the CPU at breakpoints, it may slow execution, it can change timing, it can mask or expose race conditions, and it often changes the power state or clock behavior. So the goal is to figure out which of those differences is responsible, and the way to do that is to remove the debugger while keeping observability.

I'd start by replacing the debugger with non-intrusive instrumentation: a GPIO toggled at key points and watched on a scope or logic analyzer, a UART log, or an on-chip trace buffer if the MCU supports it. These let you see what's happening without halting the CPU. If the misbehavior disappears when you add logging, that itself is a clue — it suggests a timing-sensitive issue, and the logging is perturbing the timing in a way that hides it.

Common root causes for debugger-dependent behavior include: a race condition that the debugger's halts accidentally serialize; an uninitialized variable that happens to be zero under the debugger's memory setup but garbage otherwise; a timing-dependent peripheral interaction where the debugger's slowdown changes whether a deadline is met; and low-power or clock-gating behavior that the debugger's connection keeps the device out of. I'd also check whether the debugger is holding a reset line, a clock, or a power rail in a way that changes startup behavior.

The systematic approach is to bisect: reproduce the failure standalone, then add one observability mechanism at a time and see which one makes it disappear. The mechanism that hides it points at the underlying cause. Throughout, I'd keep the reproduction as close to the failing condition as possible — same power source, same temperature, same firmware build — because these bugs often depend on a combination of factors.

**Possible follow-ups:**
- If the issue only reproduces after hours of runtime, how would you structure the investigation so you're not waiting hours per iteration?
- How would you tell the difference between a race condition and an uninitialized-memory issue when both can look like "works with debugger, fails without"?

## Q4: How would you approach deciding what belongs in a bootloader versus what belongs in the application, for a device that must support field updates?

**Answer:** The guiding principle is that the bootloader should be as small and as simple as possible, because it's the one piece of code that must never fail — if the bootloader is broken, the device is unrecoverable in the field. Everything that isn't strictly necessary for the bootloader's job should live in the application, where it can be updated and where a bug is recoverable.

The bootloader's non-negotiable responsibilities are: verifying the integrity and authenticity of the application image before jumping to it (CRC or hash, and a signature check if secure boot is required), selecting which image to boot when there are multiple banks, and providing a recovery path if no valid image exists. It also needs to handle the mechanics of receiving and writing a new image, or at least coordinating with the application to do so — though the actual transfer is often better handled by the application, which has the full communication stack, while the bootloader only handles the final commit and validation.

Things that typically belong in the application: the full communication stack, the user interface, the decision of when to accept an update, and the logic for downloading and staging an image. The application can write the new image to a staging area and then request a reboot into the bootloader to validate and commit it. This keeps the bootloader free of protocol complexity.

The trade-offs are about size, attack surface, and update-ability. A larger bootloader can do more but is harder to verify and can't easily be updated itself. A minimal bootloader is easier to trust but pushes complexity into the application, which must then be careful not to brick the device by, say, corrupting the staging area. I'd also think about what happens if the bootloader itself needs a fix — if it's in read-only memory, that's a factory-only operation, which is a strong argument for keeping it minimal and getting it right the first time.

**Possible follow-ups:**
- How would you handle the case where the application is responsible for downloading the image but crashes mid-download?
- What validation checks would you perform in the bootloader before committing to a new image, and in what order?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** I'd start by acknowledging what they got right: `volatile` does prevent the compiler from caching the variable in a register or eliminating accesses to it, and that's a real and necessary property when a variable is modified by an ISR. So the instinct isn't wrong — it's just incomplete. The conversation is about what `volatile` does *not* guarantee.

The key points to walk through: `volatile` says nothing about atomicity. If the variable is wider than the machine's atomic access size, or if the thread does a read-modify-write, the ISR can interleave and corrupt the value. `volatile` also says nothing about memory ordering — on a multicore system or with certain compiler and CPU optimizations, other memory accesses can be reordered around the volatile access, so a flag being set doesn't necessarily mean the data it's guarding is visible. And `volatile` doesn't provide mutual exclusion, so if two contexts can both write, you can still lose updates.

The better design depends on what the variable is doing. If it's a simple flag signaling "data is ready," the right primitive is an atomic type with the appropriate memory ordering, or a proper synchronization object like a semaphore or a message queue. If it's a shared buffer, the ISR should hand off ownership through a queue or a lock-free ring buffer with correct memory barriers, not through a bare flag. In Zephyr specifically, `k_sem`, `k_msgq`, and the atomic APIs exist precisely for this, and they encode the ordering and atomicity guarantees that a bare `volatile` doesn't.

I'd frame it as: `volatile` is necessary but not sufficient. It's the right tool for "this variable can change outside the normal flow of control," but it's the wrong tool for "I need to coordinate between two execution contexts." I'd also point them at the specific failure modes — a torn read, a lost update, a reordered access — so they can recognize the pattern in the future rather than just applying a rule.

**Possible follow-ups:**
- Can you give a concrete example where `volatile` alone would still allow a bug, and how would the fix look?
- How would you decide between an atomic flag and a semaphore for a given ISR-to-thread handoff?