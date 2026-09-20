# firmware — Day 61

## Q1: How would you approach implementing a state machine for a device's operational modes where the same event can arrive from multiple sources — a user interface, a communication interface, and an internal timer — and the correct transition depends on which source sent it?

**Answer:** The key insight is that the *source* of an event is part of the event's identity, not just its type. If you collapse "start command from UI" and "start command from comms" into a single `EVT_START`, you lose the information needed to make the right transition, and you end up scattering source checks throughout the transition logic.

The cleanest approach is to define the event as a small struct or tagged union that carries both a type and an origin: something like `{ .type = EVT_START, .source = SRC_UI }`. The state machine's transition table is then keyed on the pair `(current_state, event_type, source)`, or the handler for a given event type dispatches on source internally. Either way, the decision is explicit and testable rather than implicit.

A few design considerations matter here. First, decide whether source-dependent behavior is genuinely a *transition* difference (different next state) or a *guard/action* difference (same next state, different side effect). If it's the latter, keep the transition table simple and put the source check in the action — this avoids combinatorial explosion in the table. Second, for events that are semantically identical regardless of source (e.g., a fault notification), don't force a source dimension; only add it where it actually changes behavior. Third, if events arrive from different contexts — an ISR for a timer, a thread for comms, a UI callback — you need a single serialization point (a queue or a dedicated state-machine thread) so transitions are processed one at a time and you never have two contexts mutating state concurrently. The state machine should be a single-threaded consumer of an event queue; producers just enqueue.

Finally, this is exactly the kind of logic that benefits from a table-driven representation, because the `(state, event, source)` matrix is easy to review for completeness — you can enumerate every cell and confirm each has a defined behavior, including "ignore" or "log and stay."

**Possible follow-ups:**
- How would you handle an event that arrives while the state machine is mid-transition — do you queue it, drop it, or block the producer?
- If two sources can issue conflicting commands nearly simultaneously, where would you resolve the conflict — at the source, in the queue, or in the state machine?

## Q2: You're debugging a firmware issue where a device's behavior changes depending on whether a debugger is attached — with the debugger connected everything works, but standalone the device occasionally misbehaves. How would you approach this?

**Answer:** This is a classic heisenbug, and the first thing to recognize is *why* attaching a debugger changes behavior. There are several distinct mechanisms, and identifying which one applies usually points straight at the root cause.

The most common cause is **timing**. A debugger halts the core, single-steps, and adds latency to every memory access and interrupt. If the bug is a race condition, a too-tight timing margin, or a missing synchronization, the debugger's slowdown can mask it entirely. The second common cause is **uninitialized or stale state**: a debugger often zeroes RAM on connect, or the act of halting lets a peripheral settle, so a variable that would otherwise contain garbage happens to be benign. Third is **power and clock behavior**: attaching a debugger can change the power state (some debuggers hold certain domains alive), alter clock configuration, or prevent a low-power mode from being entered — so a bug that only manifests in a specific sleep state disappears. Fourth is **watchdog and timeout behavior**: the debugger may freeze the watchdog, so a timeout that would fire standalone never fires.

My approach is to first *characterize* the difference rather than guess. I'd ask: does it fail only when the debugger is attached, or only when it's detached? Does it correlate with a specific power mode, a specific peripheral, or a specific timing window? Then I'd try to reproduce the failure *without* a debugger using non-intrusive instrumentation — GPIO toggles, a spare UART logging to a buffer, or a trace facility — so I can observe behavior without perturbing timing. If the bug is timing-sensitive, I'd deliberately stress the timing: add delays in the standalone build to see if the failure window shifts, or remove them to see if it worsens.

For the specific mechanisms: if I suspect uninitialized memory, I'd fill RAM with a known pattern at startup and see if the failure changes character. If I suspect a low-power mode, I'd disable sleep and see if the bug vanishes. If I suspect the watchdog, I'd log reset cause. The goal is to convert "works with debugger" into a concrete hypothesis about *what the debugger is changing*, then test that hypothesis directly.

**Possible follow-ups:**
- How would you instrument the standalone build to capture evidence without a debugger, given that adding logging itself changes timing?
- If the bug turns out to be a race condition that only appears at full speed, how would you make it reproducible enough to fix confidently?

## Q3: How would you approach designing a firmware module that must log diagnostic events to flash, where the log must survive a power loss mid-write and the flash has limited erase cycles?

**Answer:** There are two independent problems here — *atomicity* (a power loss mid-write must not corrupt the log) and *endurance* (limited erase cycles must be spread out) — and the design has to address both.

For atomicity, the core principle is that you never overwrite the only copy of valid data in place. A common pattern is a log-structured or append-only scheme: records are written sequentially into a region, and each record carries a header with a sequence number and a CRC. On power-up, the firmware scans the region, validates each record's CRC, and treats the first invalid or incomplete record as the end of the log — everything before it is intact, and the partial record is simply discarded. This works because a torn write only ever damages the *last* record, never earlier ones. If you need a record to be committed atomically, you can write it in two phases: write the payload with a "pending" marker, then write a small "committed" marker (or update a sequence field) only after the payload is fully written and verified. A power loss between the two leaves a pending record that's ignored on recovery.

For endurance, the key is to avoid erasing the same sector repeatedly. Options include: (1) a **circular log** across multiple sectors, so erases rotate through the region rather than hammering one sector; (2) **wear leveling**, either built into the filesystem layer or implemented manually by tracking erase counts per sector and preferring less-worn ones; (3) **reducing write frequency** by buffering events in RAM and flushing in batches, which trades some risk of losing the most recent events against a large reduction in erase cycles; and (4) **separating hot and cold data** so that frequently-updated counters don't share a sector with rarely-written configuration.

A practical design also needs a policy for what happens when the log fills: either wrap (overwriting oldest records, which requires erasing the oldest sector) or stop logging and signal the condition. For a diagnostic log, wrapping is usually acceptable, but the wrap point should be recorded so the reader knows the log is not complete from boot.

**Possible follow-ups:**
- How would you verify the atomicity guarantee — what test would convince you that a power loss at any point during a write cannot corrupt committed records?
- If the device logs frequently and the flash endurance is marginal, how would you decide between batching writes in RAM versus logging every event immediately?

## Q4: How would you approach deciding whether a piece of firmware logic belongs in an interrupt service routine versus a deferred context such as a work queue or a thread?

**Answer:** The default answer should be "defer," and the burden of proof is on keeping something in the ISR. The reason is that ISR context is the most constrained environment in the system: it runs at high priority, it typically cannot block or sleep, it often cannot allocate, and anything it does directly adds to interrupt latency for every other interrupt in the system. So the question isn't "can this run in an ISR?" but "does this *need* to run in an ISR?"

The things that genuinely need to be in the ISR are the ones that are **time-critical and cannot tolerate the latency of deferral**: acknowledging the interrupt source so it doesn't re-fire, capturing data that would otherwise be lost (reading a FIFO before it overflows, latching a timestamp), and clearing the condition that caused the interrupt. That's usually a small, bounded amount of work — read a register, copy a few bytes into a buffer, set a flag or post to a queue, return.

Everything else — parsing a received message, running a state machine transition, updating a display, writing to flash, doing floating-point math, calling into a protocol stack — belongs in a deferred context. The ISR's job is to capture the event and hand it off as cheaply as possible. In Zephyr, that handoff is typically a `k_msgq` or `k_fifo` post, a `k_work` submission, or a semaphore give; the deferred context then does the real work at a priority that doesn't starve the rest of the system.

A few practical criteria help decide borderline cases. How long does the work take? If it's more than a few microseconds, defer it. Does it block or sleep? Then it *must* be deferred — you can't block in an ISR. Does it touch shared state that other contexts also touch? Then deferring it to a single context simplifies synchronization enormously. Is it reentrant-safe if the same interrupt fires again while you're handling it? If not, defer. And critically: does deferring it risk missing a deadline? If the deferred context can't be scheduled in time, that's the one case where the work has to stay in the ISR — but then you should also be asking whether the system's priority structure is right.

**Possible follow-ups:**
- How would you measure whether an ISR is doing too much work — what would you look at to decide it needs to be split?
- If a deferred work item can be posted faster than it can be processed, how would you handle the backlog without unbounded memory growth?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it relies on a global variable to communicate between two threads without any synchronization. They argue that the variable is just a flag and "it's only one byte, so it's atomic." How would you guide them?

**Answer:** I'd start by taking their reasoning seriously rather than dismissing it, because there's a kernel of truth in it — a single-byte aligned load or store often *is* atomic at the instruction level on many architectures. The problem is that instruction-level atomicity is not the same as *thread-safe communication*, and the gap between those two ideas is exactly what I want them to see.

The first issue is that atomicity of the access doesn't guarantee **visibility or ordering**. Without a memory barrier or a properly synchronized primitive, the compiler is free to cache the flag in a register, reorder the read relative to other accesses, or optimize the check away entirely — especially in a loop like `while (!flag) {}`, which a compiler may legitimately turn into an infinite loop because it can't see that another thread modifies `flag`. The second issue is that the flag is almost never *just* a flag: it usually signals that some other data is ready, and without a barrier the reader can observe the flag set before the data it's supposed to protect is actually visible. That's the classic "flag says data is ready, but the data isn't there yet" bug, and it's intermittent and miserable to debug.

The third issue is maintainability and portability. Even if the code happens to work on the current compiler and architecture, it's relying on undefined behavior that a compiler upgrade, an optimization-level change, or a move to a different core can silently break. Code that works "by accident" is a liability.

For the fix, I'd steer them toward the right primitive for the job rather than a blanket "use a mutex." If it's genuinely a single flag used for signaling, the right tool is usually an atomic type with explicit memory ordering (`atomic_t` with acquire/release semantics in Zephyr), or better, a proper synchronization primitive like a semaphore or a `k_event` — because those express the *intent* ("I'm signaling that something happened") and handle the memory ordering for you. If the flag protects a larger data structure, a mutex or a lock-free pattern with correct barriers is appropriate. I'd also point them at the code review checklist angle: any shared mutable state between contexts should be identifiable by its synchronization, and if you can't point to the primitive that protects it, that's the smell.

I'd frame the whole conversation around "what is this variable *for*?" — if it's signaling, use a signaling primitive; if it's protecting data, use a lock. The goal is to get them to reach for the right abstraction by default, not to memorize a rule about byte sizes.

**Possible follow-ups:**
- How would you demonstrate the failure to them — what test or tool would make the race condition visible rather than theoretical?
- If the flag is on a hot path where a mutex would add unacceptable overhead, what alternatives would you consider, and what would you have to prove about them?