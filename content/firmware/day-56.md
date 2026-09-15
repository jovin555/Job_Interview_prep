# firmware — Day 56

## Q1: How would you approach designing a firmware module that must coordinate a sensor acquisition pipeline where the same sampled data needs to feed both a hard real-time control path and a slower logging/telemetry path, without the logging path ever stalling the control path?

**Answer:** The core principle is to decouple the two consumers so that the slower one can never block the faster one. I'd structure this as a producer/consumer split with a single acquisition stage that timestamps and publishes each sample, and two independent consumers downstream.

Concretely: the acquisition stage (ISR or high-priority thread) writes each sample into a lock-free single-producer/single-consumer ring buffer sized to absorb worst-case scheduling jitter on the consumer side. The control path reads from that buffer at its fixed rate and must never wait on anything shared with logging — no mutex held across both paths, no dynamic allocation, no flash access. The logging path reads from a *separate* buffer or a snapshot mechanism, so if it falls behind, it drops or coalesces samples rather than applying backpressure to acquisition.

The key design decisions are: (1) what happens on overflow — for control data, overwriting oldest is usually wrong because you'd lose a sample the control loop needed; for logging data, overwriting oldest is usually fine because telemetry is best-effort. So the two buffers need different overflow policies. (2) Whether logging runs in a lower-priority thread that can be preempted freely, or in a deferred context like a work queue, so it never runs at a priority that could delay the control path. (3) Whether the logging path needs the *raw* sample or a derived value — if it only needs averages or min/max over a window, the acquisition stage can compute those cheaply and hand off a much smaller payload, reducing buffer pressure.

I'd also want to make the timing contract explicit: the control path's deadline, the maximum tolerable jitter, and the logging path's acceptable latency. Those numbers drive the buffer sizing and the priority assignment, and they're what I'd document so a future change to either path can be checked against them.

**Possible follow-ups:**
- How would you verify that the logging path genuinely never affects control-path jitter — what would you measure, and how?
- If the logging path needs to write to flash and flash writes block for tens of milliseconds, how does that change the design?

## Q2: You're debugging a firmware issue where a device's behavior changes depending on whether a debugger is attached — with the debugger connected everything works, but standalone the device occasionally misbehaves. How would you approach this?

**Answer:** This is a classic heisenbug pattern, and the first thing I'd do is resist the temptation to "fix" it by leaving the debugger attached or adding a delay. The debugger changes several things simultaneously: it halts the core at breakpoints, it may slow down execution, it can mask timing-sensitive races, it often disables or changes watchdog behavior, and it may alter power state or clock configuration. Any of those could be the actual cause.

My approach would be to narrow down *which* debugger-induced change is masking the bug. First, I'd check whether the issue is timing-related by running standalone with an artificial delay inserted at a suspect point — if the bug disappears, it's likely a race or a peripheral that needs settling time. Second, I'd check watchdog behavior: many debuggers freeze the watchdog while halted, so a watchdog that's marginally too tight would only fire standalone. Third, I'd check whether the debugger is affecting low-power modes — attaching a debugger often prevents deep sleep, so a bug in the sleep/wake path would only appear standalone.

To actually catch it, I'd move toward non-intrusive observability: a GPIO toggled at key points and captured on a scope or logic analyzer, a RAM-based trace buffer that survives until the next boot and gets dumped afterward, or a UART log at a baud rate high enough not to perturb timing. If the device has an on-chip trace unit, that's ideal because it doesn't halt the core. I'd also try to make the bug deterministic — if it's a race, adding controlled stress (higher interrupt load, tighter loop timing) can turn "occasionally" into "reliably," which makes it debuggable.

The meta-point I'd want to convey: the debugger is a tool that changes the system under test, so "works with debugger" is not evidence the code is correct — it's evidence the bug is sensitive to something the debugger controls.

**Possible follow-ups:**
- How would you design the firmware so that this class of bug is easier to catch in the future?
- What's your approach if the bug only reproduces after hours of runtime and you can't attach a debugger for that long?

## Q3: How would you approach implementing a firmware module that must handle a peripheral which can be accessed by more than one thread, where the access patterns differ — one thread does short register reads, another does long burst transfers — and you want to avoid one starving the other?

**Answer:** The first question is whether the peripheral genuinely supports concurrent access or whether it's a shared resource that must be serialized. Most peripherals fall into the second category, so the design starts with a mutual-exclusion mechanism — but the choice of mechanism matters a lot given the asymmetric access patterns.

A plain mutex would work for correctness but creates a fairness problem: if the burst-transfer thread holds the lock for a long time, the short-read thread blocks for that entire duration, which may violate its latency requirement. So I'd think about the access patterns explicitly. Options:

1. **Chunk the long transfer.** Break the burst into smaller units, releasing the lock between chunks so the short-read thread can interleave. This trades some throughput for latency fairness, and it's often the right call when the short-read thread has a hard deadline.
2. **Priority inheritance or priority ceiling.** If the short-read thread is higher priority, a priority-inheriting mutex ensures the burst thread doesn't get preempted in a way that extends the hold time — but it doesn't help if the burst thread is simply *slow* by nature.
3. **Separate the concerns.** If the short reads are for status/health monitoring and the bursts are for data, sometimes the right answer is to have a single owner thread for the peripheral that services requests from both, using a queue. That serializes access by construction and lets the owner apply a scheduling policy (e.g., always service pending short reads before starting a new burst).
4. **Hardware-level arbitration.** Some peripherals have separate channels or FIFOs that can be dedicated to different purposes, which sidesteps the software contention entirely. Worth checking the datasheet before assuming software serialization is required.

I'd also want to define what "starving" means in measurable terms — is it a maximum latency on the short read, a minimum throughput on the burst, or both? That determines whether chunking is sufficient or whether a more elaborate scheduling scheme is needed. And I'd want to make sure the locking is correct under all paths, including error paths and timeouts, because a lock held across a blocking wait is a common source of exactly this kind of starvation.

**Possible follow-ups:**
- How would you test that the fairness policy actually holds under worst-case load?
- If the peripheral access is from an ISR and a thread, how does that change your approach?

## Q4: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it relies on a global variable to communicate between two threads without any synchronization. They argue that the variable is just a flag and "it's only one byte, so it's atomic." How would you guide them?

**Answer:** I'd start by acknowledging the kernel of truth in what they said — on many architectures, a single-byte aligned access *is* atomic at the hardware level, so the read or write itself won't tear. But that's not the whole story, and the gap between "the access is atomic" and "the code is correct" is exactly where these bugs live.

The issues I'd walk through with them:

1. **Compiler reordering and optimization.** Without a `volatile` qualifier or an atomic type, the compiler is free to cache the value in a register, reorder accesses, or eliminate what it sees as redundant reads. The flag might be read once and never re-checked, or a write might be moved after a subsequent operation that was supposed to happen first. This is the most common way "it's just a flag" code breaks — not at the hardware level, but at the compiler level.
2. **Memory ordering.** Even with `volatile`, the compiler and CPU can reorder *other* memory accesses around the flag. If the flag is meant to signal "the data is ready," the data write must be visible before the flag write, and the flag read must happen before the data read. That requires an acquire/release relationship, which a bare `volatile` flag doesn't provide. On a single-core Cortex-M this often works by accident, but it's not guaranteed and it definitely breaks on multi-core or when DMA is involved.
3. **Lost wakeups and races.** If the flag is a handshake ("I've set it, you clear it"), there's a window where both threads can act on stale state. A single byte doesn't protect against that — it's a protocol problem, not an atomicity problem.
4. **Maintainability.** Even if it happens to work today, the next person to touch the code has no way to know the synchronization contract. That's how these bugs get introduced later.

For the fix, I'd steer them toward the RTOS's proper primitives: a `k_sem`, `k_event`, or `k_poll` signal for thread-to-thread signaling, or `atomic_t` operations if it's genuinely just a counter or flag with no associated data. The point isn't to be pedantic — it's that the primitive encodes the intent and the memory-ordering guarantees, so the code is correct by construction rather than correct by luck.

I'd frame it as: "The question isn't whether this works on your board today. It's whether you can explain *why* it works, and whether it would still work if the compiler version changed, the optimization level changed, or the code moved to a different core." If they can't answer that, the code isn't done.

**Possible follow-ups:**
- How would you detect this kind of bug if it were already in production and causing intermittent failures?
- When *is* a bare `volatile` flag actually the right tool?

## Q5: How would you approach a situation where you're asked to add a new feature to a firmware module you didn't write, the module has no tests, and the original author has left the company?

**Answer:** I'd treat this as a code-archaeology problem first and a feature problem second, because the biggest risk isn't writing the feature — it's breaking something I don't understand.

My approach would be roughly:

1. **Understand the module's contract before touching it.** What are its inputs and outputs? What does it assume about its callers and about the hardware? I'd read the code with the datasheet and any available design docs open, and I'd write down the assumptions I find — especially implicit ones (timing, ordering, initialization sequence). The goal is to build a mental model I can state out loud, because if I can't explain what the module does, I can't safely change it.

2. **Build a safety net before changing anything.** Since there are no tests, I'd add characterization tests — tests that capture the *current* behavior, even if some of it looks wrong, so I have a baseline. For embedded code this often means a host-side test harness with the hardware abstracted, or a hardware-in-the-loop setup that exercises the module's real interfaces. The point isn't full coverage; it's enough coverage that a regression shows up as a test failure rather than a field failure.

3. **Make the smallest possible change.** I'd resist the urge to refactor while adding the feature. If the module needs restructuring to accommodate the feature cleanly, I'd do that as a separate, behavior-preserving change first, verified against the characterization tests, and then add the feature on top. Mixing the two makes it impossible to tell which change caused a problem.

4. **Instrument and observe.** Before and after the change, I'd add logging or tracing at the module's boundaries so I can see what it's actually doing in operation, not just what I think it's doing. This is especially valuable for modules that interact with hardware, where the failure mode is often a timing or ordering issue that doesn't show up in unit tests.

5. **Document what I learned.** The next person to touch this module shouldn't have to repeat the archaeology. I'd write down the contract, the assumptions, and the known sharp edges — even if it's just a comment block at the top of the file.

The behavioral dimension here is that I'd also communicate the risk to whoever asked for the feature. "I can add this, but the module has no tests and I don't have the original author to ask, so I'm going to spend some time building a safety net first" is a conversation worth having early, not a surprise to spring when the estimate slips.

**Possible follow-ups:**
- How would you decide how much characterization testing is "enough" before you feel safe making the change?
- What would you do if the module's behavior is clearly buggy but fixing it is out of scope for your feature?