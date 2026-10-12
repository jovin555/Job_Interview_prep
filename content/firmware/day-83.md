# firmware — Day 83

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** The first step is to recognize that the problem is not really "the ISR is too slow" but "the ISR is doing too much." An ISR should do the minimum work required to acknowledge the hardware and hand off data — typically reading a register or moving a word into a buffer — and defer everything else. If the interrupt rate genuinely exceeds what the CPU can service even with a minimal ISR, then the design has to change at a higher level.

I'd approach it in layers. First, quantify the actual rate and the per-interrupt cost: how many interrupts per second, how many cycles does the ISR body take, and what fraction of CPU time does that consume? If it's already near 100%, no amount of ISR tuning will help — the peripheral needs to be reconfigured. Options include enabling a FIFO or DMA so that the hardware buffers multiple samples and raises an interrupt only when a threshold is reached, reducing the interrupt rate by the FIFO depth. If the peripheral supports it, switching from per-sample to per-block interrupts is usually the cleanest fix.

If DMA isn't available, I'd look at whether the ISR can be made cheaper: avoid function calls, avoid floating point, avoid any logging or locking, and make sure the compiler isn't generating unnecessary prologue/epilogue. Sometimes the fix is as simple as marking the ISR with the right attributes and keeping it in a single translation unit so it can be inlined.

If the rate is still too high, the honest answer is that the hardware or the sampling requirement is mismatched to the CPU, and that needs to be surfaced early rather than papered over with a bigger buffer. A larger buffer only delays the problem — it doesn't change the average service rate.

**Possible follow-ups:**
- How would you measure the actual ISR execution time and interrupt rate on a running system without perturbing the timing?
- If the peripheral only supports per-sample interrupts and DMA is not an option, what architectural changes would you consider?

## Q2: How would you approach implementing a state machine where the same event can arrive from multiple sources (a user interface, a communication interface, and an internal timer), and the correct transition depends on which source sent it?

**Answer:** The key insight is that the event itself is not enough — the state machine needs to know the event's origin, because the same nominal event (say, "start") may mean different things depending on whether it came from a physical button, a remote command, or an internal timeout. I'd model this by making the event a structured type that carries both a type and a source, rather than a bare enum.

Concretely, I'd define an event as a small struct or a tagged union with at least two fields: an event ID and a source ID. The transition table or switch logic then keys on the pair, not just the event ID. This keeps the source information explicit and prevents the common bug where a remote "stop" and a local "stop" get collapsed into one path and one of them ends up with the wrong semantics.

I'd also think carefully about priority and ordering. If a UI event and a timer event arrive in the same tick, which one wins? That's a policy decision that should be documented, not left to whatever order the dispatcher happens to process them. In an RTOS, I'd typically funnel all events into a single queue so they're serialized, and the state machine processes them one at a time — that avoids reentrancy and makes the ordering deterministic.

For maintainability, I'd keep the transition logic in one place rather than scattering it across modules. A table-driven approach works well here because the (state, event, source) → (next state, action) mapping is naturally tabular, and it makes it easy to see at a glance which combinations are handled and which are not. The unhandled combinations are often where the bugs live, so making them visible is valuable.

**Possible follow-ups:**
- How would you handle an event that arrives while the state machine is in the middle of executing a transition action?
- What would you do if two sources can legitimately send the same event with the same semantics — would you still distinguish them?

## Q3: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the debugger's presence changes several things at once: it halts the CPU at breakpoints, it may slow down or serialize memory accesses, it can change the timing of interrupts, and it often disables or alters low-power modes. So the first job is to figure out which of those differences is masking the bug.

I'd start by narrowing down what "attached" means in this case. If the debugger is merely connected but not actively halting, the difference is likely electrical or timing-related — for example, the debug probe may be holding a reset line, providing a ground reference, or keeping a clock alive. If the debugger is actively used with breakpoints, the difference is more likely a race condition or a timing-sensitive path that the halt masks.

A useful technique is to reproduce the failure without a debugger but with instrumentation that doesn't change timing much — for example, toggling a GPIO pin at key points and capturing it on a scope or logic analyzer, or using a small RAM-based trace buffer that the firmware writes to and that can be read out after the fact. This gives visibility without halting the CPU.

I'd also look at the usual suspects for debugger-dependent behavior: uninitialized variables that happen to be zeroed by the debugger's memory initialization, watchdog timeouts that are extended by the debugger's halt, low-power modes that the debugger prevents from entering, and interrupt priorities that behave differently when the debugger is in the loop. Checking the linker map and startup code for anything that depends on the debugger's presence is also worth doing.

Finally, I'd try to make the failure reproducible in a way that doesn't depend on the debugger at all — for example, by adding a deliberate delay or a stress condition that triggers the race more reliably. Once it's reproducible standalone, normal debugging techniques apply.

**Possible follow-ups:**
- How would you use a RAM trace buffer to capture the sequence of events leading up to a failure without halting the CPU?
- What specific low-power or clock-related behaviors might a debugger change that could mask a bug?

## Q4: How would you approach deciding whether a piece of firmware logic should run in an interrupt context, a deferred context (work queue or thread), or a low-priority background task?

**Answer:** The decision comes down to three questions: how much work is it, how time-critical is it, and what does it need to touch?

If the work is small and bounded — reading a register, clearing a flag, pushing a byte into a buffer — it belongs in the ISR. The ISR's job is to acknowledge the hardware and capture the data before it's lost. Anything beyond that risks blocking other interrupts and increasing latency for everyone.

If the work is larger but still needs to happen promptly — parsing a received message, updating a state machine, driving a short sequence — it belongs in a deferred context. In Zephyr, that's typically a work queue item or a dedicated thread. The ISR signals the deferred context (via a semaphore, a work item submission, or a message queue) and returns quickly. The deferred context runs at a priority that's high enough to meet the deadline but low enough not to starve other important work.

If the work is not time-critical — logging, telemetry, housekeeping, non-urgent configuration — it belongs in a low-priority background task. This keeps it out of the way of the real-time paths and lets the scheduler decide when there's spare CPU.

The other consideration is what the work touches. If it needs to take a mutex, allocate memory, or call into a subsystem that might block, it cannot run in an ISR — those operations are not ISR-safe. That alone often forces the decision toward a deferred context.

I'd also think about the cost of the handoff itself. A work queue submission is cheap, but it's not free, and if the ISR fires very frequently, the overhead of deferring every event can add up. In that case, batching — accumulating several events in the ISR and deferring once — can be worth it.

**Possible follow-ups:**
- How would you decide the priority of the deferred context relative to other threads in the system?
- What are the risks of doing too much in a deferred context versus too little?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** I'd start by acknowledging the part they got right: `volatile` does prevent the compiler from caching the variable in a register or eliminating the access, which is necessary for the ISR and the thread to see each other's writes. So the instinct isn't wrong — it's just incomplete.

The gap is that `volatile` says nothing about atomicity or ordering. If the variable is wider than the CPU's native word size, or if it's a multi-field structure, a read or write can be torn — the thread can observe a half-updated value. And even for a single word, `volatile` doesn't prevent the compiler or the CPU from reordering accesses to *other* variables around it, which matters if the flag is meant to signal that some other data is ready. On a multicore system, it also doesn't provide any memory barrier semantics.

So the fix depends on what the variable is actually doing. If it's a simple flag that signals "data is ready," the right primitive is an atomic type with the appropriate memory ordering — in Zephyr, `atomic_t` with `atomic_set` and `atomic_get`, or a `k_sem` if the thread needs to block. If it's a buffer plus a flag, the flag needs to be published with release semantics and consumed with acquire semantics, so that the data writes are visible before the flag is seen. A `k_sem` or a `k_fifo` handles this naturally and is usually the clearest option.

I'd frame the conversation around correctness rather than style: the code works today, but it's relying on assumptions that aren't guaranteed by the language or the platform, and those assumptions can break under a different compiler, optimization level, or CPU. The goal is to make the synchronization explicit and portable, not to add complexity for its own sake.

I'd also suggest they write a small test that exercises the ISR/thread interaction under stress — for example, running the ISR at a high rate while the thread reads — to see whether the current approach ever produces a torn or stale value. Sometimes seeing the failure mode is more convincing than an argument.

**Possible follow-ups:**
- What's the difference between `volatile` and an atomic type in terms of the guarantees each provides?
- How would you explain memory ordering (acquire/release) to someone who hasn't encountered it before?