# firmware — Day 80

## Q1: How would you approach designing a firmware module that must detect and recover from a peripheral that has silently stopped responding — no error flag, no interrupt, it just stops producing data — without relying on the peripheral's own status reporting?

**Answer:** The core problem is that the peripheral's own health reporting is untrustworthy in this failure mode, so liveness has to be inferred from the *absence* of expected activity rather than the presence of an error. The general approach is to build a watchdog around the data itself, not around the peripheral's registers.

Concretely, I'd structure it in layers:

1. **Define an expected cadence.** Every peripheral that should produce data has some nominal rate or at least a maximum inter-arrival time. That becomes the liveness contract: "if no valid sample arrives within N × nominal period, something is wrong." The multiplier accounts for normal jitter and scheduling delay.

2. **Timestamp on arrival, not on read.** The liveness check should be driven by a monotonic timestamp taken when data actually lands (in the ISR or DMA completion callback), not when a consumer thread happens to poll. Otherwise a busy consumer looks like a dead peripheral.

3. **Separate "no data" from "bad data."** A CRC failure, an out-of-range value, or a NACK is a different failure class than silence. Silence means the recovery path is likely a peripheral reset; bad data might mean a retry or a re-read. Conflating them leads to over-aggressive resets.

4. **Escalating recovery.** The first response is usually the cheapest: re-arm the transfer, toggle a chip-select, or issue a soft reset of the peripheral block. If that fails within a bounded number of attempts, escalate to a peripheral-level reset (disable clock, re-init registers, re-enable). Only if that fails do you consider a broader system action — and for a medical device, that broader action is usually "declare the sensor unavailable and degrade gracefully," not "reset the whole device."

5. **Make the recovery observable.** Log the event with enough context (which peripheral, how long silent, which recovery stage succeeded) so that field failures can be diagnosed. A silent recovery that works is still a bug report waiting to happen.

The key design principle is that the liveness monitor must live *outside* the peripheral's own driver state machine, so that a wedged driver can't also wedge its own health check. A separate supervisory task or a timer-driven check is the usual home for it.

**Possible follow-ups:**
- How would you avoid false positives during legitimate periods when the peripheral is intentionally idle, such as a low-power sleep window?
- Where would you put the liveness check in a Zephyr system — a dedicated thread, a `k_timer` callback, or a work queue item — and what are the trade-offs?

## Q2: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** Stack sizing is one of those areas where "it hasn't crashed yet" is not evidence of correctness, because stack overflow in an RTOS often manifests as corruption somewhere else entirely rather than a clean fault. I'd approach it as a measurement problem, not a guess.

**Starting point — estimate, then measure.** A rough static estimate comes from the deepest call chain: the thread's own frame, plus the deepest function it calls, plus ISR nesting if the thread can be preempted by interrupts that use the same stack (on many architectures, ISRs use the current thread's stack). Add margin for compiler variation, floating-point save areas, and library calls like `printf`/`snprintf`, which are notorious stack hogs. That estimate is a *floor*, not an answer.

**Measurement — the real answer.** Zephyr provides stack analysis tooling: `CONFIG_THREAD_ANALYZER` with runtime stack usage reporting, and `CONFIG_INIT_STACKS` combined with `k_thread_stack_space_get()` or the thread analyzer's unused-stack report. The pattern is: fill the stack with a known pattern at startup, run the system through its worst-case paths, then read how much of the pattern is still intact. The high-water mark is the real number.

**What "worst case" means.** The measurement is only as good as the workload. I'd deliberately exercise:
- The deepest error-handling paths, not just the happy path — error paths often have more nested calls.
- Any path that calls into logging or formatting, since those dominate stack use.
- ISR-heavy scenarios, if ISRs share the thread stack.
- The startup/initialization path, which is often deeper than steady-state.

**Margin.** Once measured, I'd add a safety margin — commonly 25–50% depending on how confident I am that the workload is representative — and document *why* that number was chosen. For safety-critical or medical firmware, the margin should be justified, not arbitrary, and the stack high-water mark should be re-checked whenever a significant code change lands.

**Verification in CI.** The strongest version of this is to make it a regression check: run the worst-case workload in a test harness, read the high-water mark, and fail the build if it exceeds a threshold. That turns stack sizing from a one-time guess into a continuously verified property.

**Possible follow-ups:**
- How would you handle a thread whose worst-case stack usage depends on data-driven recursion or a variable-depth call chain?
- What's the interaction between stack sizing and interrupt priority configuration on architectures where ISRs use the current thread's stack?

## Q3: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the debugger's presence is itself the clue. The debugger changes timing, changes power draw, changes memory contents, and sometimes changes the code path via debug-mode configuration. The first job is to figure out *which* of those is masking the bug.

**Step 1 — Characterize the difference.** I'd ask: does the bug disappear with the debugger merely *attached* (halted or not), or only when actively halted at breakpoints? Does it disappear with a serial debug print added, or only with JTAG/SWD? Each answer narrows the mechanism:
- If it disappears with any added delay (breakpoints, prints), it's likely a timing or race condition.
- If it disappears only with the debug probe physically connected, it could be a power/grounding effect, a floating pin being pulled by the probe, or a debug-peripheral clock that changes behavior.
- If it disappears only when halted, it's almost certainly a race or a state that gets "fixed" by the halt.

**Step 2 — Reproduce without the debugger.** The goal is to get the failure to happen with instrumentation that doesn't perturb timing. Options:
- Use a GPIO pin toggled at key points and watch it on a scope or logic analyzer — this adds nanoseconds, not milliseconds.
- Use a RAM-based trace buffer that the firmware writes to and that you dump *after* the failure, rather than streaming over a debug channel.
- Use the on-chip trace facilities (ETM/ITM on ARM, or a similar trace unit) which are designed to be low-perturbation.
- If the failure leaves a fault, capture the fault registers and a stack dump into a retained RAM region and read it out on the next boot.

**Step 3 — Look for the usual suspects.** Debugger-masked bugs are disproportionately:
- **Race conditions** between an ISR and a thread, or between two threads, where the debugger's halt or the added latency changes the interleaving.
- **Uninitialized memory** that happens to be zeroed or set to a benign value by the debugger's memory access.
- **Timing-dependent peripheral behavior**, e.g., a peripheral that needs a settling time the debugger's halt accidentally provides.
- **Optimization-sensitive code**, where the debug build (often `-O0`) behaves differently from the release build. This is worth ruling out early by testing an optimized build with the debugger attached.
- **Power-related issues**, where the debug probe's presence changes the supply or grounding.

**Step 4 — Fix the class, not the instance.** Once the mechanism is identified, the fix should address the underlying assumption — e.g., add proper synchronization, initialize the memory explicitly, add the required settling delay in code rather than relying on timing luck. A fix that only works because "the debugger is no longer attached" is not a fix.

**Possible follow-ups:**
- How would you distinguish a race condition from a timing-margin issue when both would be masked by a debugger?
- What would you put in a retained-RAM fault record to make a field failure diagnosable without a debugger?

## Q4: How would you approach implementing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** When the interrupt rate exceeds what the CPU can service, the ISR stops being a service routine and becomes a denial-of-service attack on the rest of the system. The fix is almost always to move work *out* of the ISR and, where possible, move data *without* the CPU at all.

**First, quantify the actual budget.** Before changing anything, I'd measure: what's the interrupt rate, what's the ISR's execution time, and what fraction of CPU time is the ISR consuming? If the ISR is consuming 80% of the CPU, the system has no headroom for anything else, and the problem is structural, not a matter of shaving a few cycles.

**Second, reduce the work per interrupt.** The ISR should do the minimum: acknowledge the interrupt, capture the data or a pointer to it, and signal a deferred context. Anything that can be deferred — parsing, validation, logging, state machine transitions — should be. This is the standard top-half/bottom-half split.

**Third, reduce the number of interrupts.** This is often the bigger win:
- **DMA.** If the peripheral supports it, configure DMA to move data into a buffer without per-byte or per-sample interrupts. The CPU then only gets an interrupt per *buffer*, not per *sample*. This can turn a 100 kHz interrupt rate into a 100 Hz one.
- **FIFO/burst modes.** Many peripherals have hardware FIFOs that let you service several samples per interrupt. Using them trades latency for interrupt rate.
- **Interrupt coalescing.** If the hardware supports it, or if you can batch in software, service multiple events per interrupt.

**Fourth, if the ISR is still too heavy, consider whether the interrupt is even necessary.** For some peripherals, a well-designed polling loop at a known rate is actually *cheaper* than an interrupt storm, because it eliminates the interrupt entry/exit overhead and gives you deterministic timing. This is one of the few cases where polling beats interrupts, and it's worth being honest about.

**Fifth, protect the rest of the system.** If the interrupt rate is genuinely irreducible, the ISR must be bounded: no unbounded loops, no blocking calls, no dynamic allocation, no logging that could block. And the system's scheduling must account for the ISR's CPU consumption — a high-priority thread that assumes it gets the CPU promptly will be starved if the ISR is eating 80% of it.

**The design principle:** the ISR's job is to get data out of the hardware and into a buffer as fast as possible, then get out of the way. Everything else is someone else's problem.

**Possible follow-ups:**
- How would you decide between DMA and a FIFO-based interrupt scheme for a given peripheral?
- If the ISR must run at a rate that leaves no CPU headroom, how would you restructure the system so that lower-priority work still makes progress?

## Q5: How would you approach a situation where you discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules?

**Answer:** The first thing I'd do is resist the two failure modes: pretending it's not a problem and pushing forward, or panicking and proposing a rewrite. Neither serves the project. The right response is a structured assessment followed by a transparent decision.

**Step 1 — Quantify the problem, not the feeling.** "This design is causing problems" is not actionable. I'd want to characterize: what specifically is failing or costly? Is it a correctness issue, a performance issue, a maintainability issue, or a schedule issue? How often does it bite? What's the cost of working around it versus fixing it? A design decision that's ugly but stable is a different situation from one that's causing intermittent field failures.

**Step 2 — Identify the actual decision point.** Often the "early decision" is really a cluster of related choices, and only one of them is the problem. Before proposing rework across several modules, I'd check whether a narrower change — an interface shim, a localized refactor, a new abstraction layer — can contain the damage without touching everything.

**Step 3 — Evaluate the options honestly.** There are usually three:
- **Fix it now.** Highest short-term cost, but if the problem is correctness or safety, this is often the only acceptable answer.
- **Contain it.** Add an abstraction or adapter that isolates the bad decision, so new code doesn't inherit it, and migrate incrementally. This is often the right answer when the problem is maintainability rather than correctness.
- **Live with it.** Accept the cost, document it, and move on. This is legitimate when the cost of change exceeds the cost of the problem — but it must be a conscious decision, not a default.

**Step 4 — Bring it to the team, not as a confession but as a decision.** The framing matters. "I made a bad call" invites blame; "here's a design constraint we've discovered, here are the options and their costs, here's what I recommend" invites engineering. I'd bring data: what's the impact, what's the cost of each option, what's the risk of each. If the decision affects schedule or scope, it belongs with whoever owns those trade-offs — not made unilaterally by me.

**Step 5 — If the decision is to change it, do it incrementally and safely.** A late-project refactor is dangerous. I'd want: a clear interface boundary, tests (or at least characterization tests) around the affected behavior, a migration path that keeps the system working at every step, and a rollback plan. If there are no tests, writing them is part of the cost of the change.

**Step 6 — Learn from it.** The post-mortem question isn't "who made the bad call" but "what would have surfaced this earlier?" Often the answer is a missing prototype, a missing interface review, or a requirement that wasn't understood at the time. That's the input to the next project's process.

The honest version of this answer acknowledges that late-project design problems are normal, that the engineer who made the decision is often the one best positioned to fix it, and that the worst outcome is not the rework — it's the rework done badly, under pressure, without a plan.

**Possible follow-ups:**
- How would you decide whether to contain the problem with an abstraction layer versus fixing it at the source?
- If the schedule doesn't allow a proper fix, how would you document the decision and its risks so that it's visible to the people who own the schedule?