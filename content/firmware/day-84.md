# firmware — Day 84

## Q1: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core problem is that an edge on a GPIO line is not the same thing as "valid data is available" — the edge is just a hint, and the actual authority on whether data is valid is the peripheral's own status register or the data payload itself. So the design should treat the edge as a trigger to go *check*, not as a guarantee.

Concretely, I'd structure it in layers. First, the ISR for the edge should do almost nothing — timestamp the event, increment a counter, and signal a deferred context (a work queue item, a semaphore, or a thread flag). It should not read the peripheral directly, because the ISR may fire on a glitch and we don't want to spend time in interrupt context on a false alarm. Second, the deferred handler reads the peripheral's status register to confirm data is actually ready. If the status bit is not set, that's a glitch — log it, increment a diagnostic counter, and return without processing. If the status bit is set, read the data and validate it (CRC, range check, sequence number if the protocol has one). Third, if the data fails validation, discard it and treat it the same as a glitch for diagnostic purposes.

The reason to count glitches separately from real data is that the glitch rate is itself diagnostic information. If a board starts showing a rising glitch count, that's a signal about signal integrity, grounding, or a noisy supply — worth surfacing in a health metric rather than silently swallowing. I'd also consider whether hardware debouncing is appropriate: a small RC filter or a Schmitt-trigger input can eliminate many glitches at the source, and firmware should not be the first line of defense against a hardware problem that has a cheap hardware fix.

One subtlety: if the peripheral's data-ready signal is level-based rather than edge-based, the whole problem changes — you can poll the level and avoid the edge-detection issue entirely. So the first question I'd ask is whether the edge-triggered behavior is actually required by the peripheral, or whether it's a design choice that could be revisited.

**Possible follow-ups:**
- If the glitch rate is high enough that the deferred handler is being woken constantly, how would you avoid the system spending most of its time servicing false triggers?
- How would you distinguish a glitch from a real edge that arrived just before the peripheral's status bit was updated, given that the two events are not perfectly synchronized?

## Q2: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** The debugger-attached case is almost always a timing or state difference, not a logic difference — the code path is the same, but the timing, power state, or peripheral state is different. So the first move is to enumerate what the debugger actually changes: it halts the CPU at breakpoints, it may keep certain clocks running, it may hold the reset line in a different state, it may power the debug interface (which can back-power parts of the board), and it slows execution enough that race conditions and marginal timing are masked.

I'd start by trying to reproduce the failure without the debugger but with instrumentation that doesn't change timing much — a GPIO toggled at key points and captured on a scope or logic analyzer, or a small ring buffer in RAM that records timestamps and event codes and can be dumped after the fact. The goal is to get visibility into the standalone case without the debugger's side effects.

Then I'd look at the usual suspects in order of likelihood. Race conditions between ISRs and threads are the classic case — the debugger's halts serialize execution in a way that hides them. Marginal timing on a peripheral (setup/hold, clock stretching, bus recovery) is next. Power-related issues are also common: the debugger can supply or stabilize power in a way the standalone device doesn't have, so brownout, inrush, or regulator transient behavior can differ. And finally, initialization order or reset behavior can differ — some peripherals behave differently on a warm reset versus a cold reset, and the debugger's reset can mask that.

A useful technique is to deliberately make the standalone case *more* like the debugger case in one dimension at a time — for example, add a small delay at a suspect point and see if the failure disappears. If it does, that's strong evidence the issue is timing-related and points at where to look. Conversely, if adding a delay makes it worse, that's also informative.

**Possible follow-ups:**
- If you suspect a race condition but can't reproduce it reliably, what techniques would you use to increase the reproduction rate without changing the underlying bug?
- How would you decide whether the fix belongs in firmware or whether the hardware needs a change — for example, if the issue turns out to be a marginal setup time on a bus?

## Q3: How would you approach designing a firmware module that must survive a brownout — where the supply voltage sags briefly but doesn't fully drop — without corrupting persistent state or producing a spurious reset?

**Answer:** A brownout is a nasty case because the MCU may keep running but outside its guaranteed operating range, which means the behavior is undefined — flash writes may partially complete, RAM may flip bits, and the CPU may execute garbage. The design goal is to detect the sag early enough to either finish cleanly or stop safely, and to make the persistent state recoverable regardless.

The first line of defense is the MCU's own brownout detector (BOD) or supply voltage monitor, if it has one. Configure it to assert a reset or an interrupt at a threshold comfortably above the MCU's minimum operating voltage, with enough margin that the firmware has time to react before the supply drops below the point where the MCU is unreliable. If the BOD can only reset, that's still useful — the key is that the reset happens *before* the MCU does something undefined, not after.

If the BOD can generate an interrupt, the ISR should do the absolute minimum: set a flag in a RAM location that survives reset (a "no-init" section), and if a flash write is in progress, either let it complete if it's close to done or abort it cleanly. The ISR must not do anything that requires the supply to be stable — no flash writes, no long computations.

The second line of defense is the persistent state design itself. Any flash write that matters should be structured so that a partial write is detectable and recoverable. The standard pattern is a journal or a two-slot scheme: write the new record to a fresh location, then update a commit marker, then invalidate the old record. On boot, scan for the most recent valid commit. A CRC on each record catches partial writes. This way, even if the brownout hits mid-write and the MCU does something undefined, the worst case is that the new record is discarded and the old one is still valid.

The third piece is the boot path: on every boot, check the brownout flag and the persistent state, and if the state is inconsistent, recover to a known-good configuration rather than assuming the last write succeeded. And I'd want the brownout event itself logged, because a device that browns out repeatedly is telling you something about its power supply or its load profile.

**Possible follow-ups:**
- If the MCU has no brownout detector, what external circuitry or firmware techniques would you use to detect a sag before it becomes dangerous?
- How would you test a brownout recovery scheme without a programmable power supply that can produce controlled sags?

## Q4: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** Stack sizing is one of those things where the default answer — "give it plenty of margin" — is fine until it isn't, because on a constrained device you can't give every thread plenty of margin, and on a safety-critical device "probably enough" is not a defensible position. So I'd approach it as a measurement problem, not a guess.

The starting point is to understand what actually consumes stack in Zephyr: local variables, function call frames (including the call chain depth), saved registers on context switch, and any stack-allocated buffers. The biggest contributors are usually deep call chains, large local arrays, and floating-point or printf-family functions, which can pull in significant stack. So the first pass is to identify the worst-case call chain for each thread and estimate from there — but estimation is only the starting point.

The real answer comes from measurement. Zephyr provides stack analysis hooks: `k_thread_stack_space_get()` returns the unused stack for a thread, and there's a stack sentinel option (`CONFIG_THREAD_STACK_INFO` and related) that can detect overflow at runtime. I'd enable stack sentinel checking during development and testing, run the system through its full range of operating conditions — including the worst-case paths, error paths, and any rare but legitimate deep call chains — and then look at the high-water mark for each thread. The high-water mark tells you the actual worst-case usage observed, and you size from there with a margin that reflects how confident you are that you've exercised all paths.

The margin itself is a judgment call. For a thread with well-understood, bounded behavior, a modest margin is fine. For a thread that calls into third-party code, uses printf, or has data-dependent call depth, the margin needs to be larger, and I'd want to either bound the behavior or add runtime checking. On a medical device, I'd lean toward keeping the sentinel checking enabled in production if the overhead is acceptable, because a stack overflow that corrupts adjacent memory is exactly the kind of failure that's hard to diagnose in the field.

One more thing: stack sizing is not a one-time decision. As the code evolves, the worst-case usage changes, so the measurement needs to be part of the test suite, not a one-off exercise. A CI job that runs the worst-case scenarios and reports high-water marks catches regressions before they ship.

**Possible follow-ups:**
- How would you handle a thread whose worst-case stack usage is data-dependent and hard to bound — for example, a thread that parses variable-length messages?
- What's the trade-off between enabling stack sentinel checking in production versus only in development, and how would you decide?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** This is a really common misconception, and the engineer's reasoning is half right — `volatile` does prevent the compiler from optimizing away the access, which is necessary but nowhere near sufficient. The gap is that `volatile` says nothing about atomicity, memory ordering, or the interaction between the compiler and the CPU's own reordering. So the code can work in testing and still be wrong.

I'd start by walking through what `volatile` actually guarantees and what it doesn't. It guarantees that each access to the variable is emitted as a real load or store, in program order relative to other volatile accesses. It does not guarantee that a multi-byte access is atomic — a 32-bit variable on an 8-bit or 16-bit MCU is not atomic, and even on a 32-bit MCU, a read-modify-write is not atomic. It does not guarantee that non-volatile accesses around it are ordered correctly. And it does not provide any mutual exclusion, so if both the ISR and the thread do read-modify-write on the same variable, updates can be lost.

The right tool depends on what the variable is doing. If it's a simple flag or a single-word counter that only one side writes and the other reads, then an atomic type or a properly aligned single-word access with the right memory barriers may be sufficient — but I'd still want to be explicit about the ordering. If it's a shared data structure, a lock or a lock-free pattern with proper atomics is needed. In Zephyr specifically, the idiomatic tools are `atomic_t` for simple counters and flags, `k_sem` or `k_mutex` for mutual exclusion, and message queues or FIFOs for passing data between contexts. For ISR-to-thread signaling, a `k_sem` given from the ISR and taken from the thread is usually the cleanest pattern.

I'd frame the guidance around the principle rather than the specific fix: the question to ask is "what is the contract between these two contexts, and what mechanism enforces it?" `volatile` is not a synchronization primitive; it's a compiler directive. Once the engineer sees the distinction, the fix usually becomes obvious to them, and they're more likely to apply the reasoning to the next case.

I'd also want to make sure the conversation doesn't come across as "you're wrong" — the code working in testing is real evidence, and the engineer's instinct to avoid over-engineering is reasonable. The point is that "works in testing" and "correct" are different claims, and on a medical device the difference matters.

**Possible follow-ups:**
- If the variable is a single 32-bit counter incremented by the ISR and read by the thread, and the MCU is 32-bit, is `volatile` sufficient? What would you use instead, and why?
- How would you structure a code review or a lint rule to catch this class of issue across the codebase, rather than fixing it one instance at a time?