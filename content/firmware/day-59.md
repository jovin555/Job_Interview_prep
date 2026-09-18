# firmware — Day 59

## Q1: How would you approach designing a firmware module that must coordinate a sensor acquisition pipeline where the same sampled data feeds both a hard real-time control path and a slower logging/telemetry path, without the logging path ever stalling the control path?

**Answer:** The core principle is to decouple the two consumers so that the slower one can never exert backpressure on the faster one. I'd structure it as a producer/consumer pipeline with a single acquisition stage and two independent downstream paths.

The acquisition stage (typically an ISR or a high-priority thread triggered by a timer or DMA-complete event) does the minimum necessary work: read the sample, timestamp it, and publish it. "Publish" here means writing into two separate structures — one for the control path and one for the logging path — rather than having both consumers read from a single shared buffer. The control path gets a small, fixed-size, lock-free single-producer/single-consumer ring or a double-buffer that the control loop reads at its own rate; because it's the highest-priority consumer, it should never block waiting for data. The logging path gets its own ring buffer, ideally larger, that the acquisition stage writes into and a low-priority logging thread drains.

The key design decision is what happens when the logging buffer fills. The answer must be: the acquisition stage never waits. It either overwrites the oldest entry (acceptable for telemetry where losing old samples is tolerable) or drops the newest sample and increments a "dropped samples" counter that gets reported alongside the log. Either way, the control path is untouched. If the logging path is allowed to block the producer, you've coupled a soft-real-time task to a hard-real-time one, which is exactly the failure mode to avoid.

I'd also make the two paths share as little state as possible. If they must share a timestamp or sequence number, that should be a value copied at publish time, not a pointer into a buffer the other path might mutate. And I'd instrument both paths — a watermark on the logging buffer and a jitter measurement on the control loop — so that if the logging thread ever does start to interfere, it shows up as data rather than as a mysterious control-loop glitch.

**Possible follow-ups:**
- How would you decide between overwriting old log entries versus dropping new ones, and how would that decision differ for a diagnostic log versus a regulatory audit trail?
- If the control path and logging path run at very different rates, how would you handle timestamp alignment between the two so that a logged event can be correlated with the control-loop state at that moment?

## Q2: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** Stack sizing is one of those areas where the honest answer is "measure, don't guess," and the measurement has to happen under worst-case conditions, not average ones.

I'd start with a rough analytical estimate: sum the deepest call chain the thread can execute, add space for local variables and any large stack-allocated buffers, add the context-save frame for the architecture, and add margin for ISR nesting if the thread can be preempted by interrupts that use the same stack (on many architectures, ISRs run on the interrupted thread's stack). That gives a floor, not an answer.

Then I'd verify empirically. Zephyr has tooling for this — `CONFIG_THREAD_ANALYZER` and the thread analyzer shell command can report stack usage, and `CONFIG_INIT_STACKS` plus `CONFIG_STACK_SENTINEL` let you detect overflow. The critical part is exercising the paths that actually stress the stack: the deepest error-handling branches, the logging paths that format strings, the recursive or deeply-nested parsing routines. A stack that's fine in normal operation can overflow the first time an error path runs with a formatted log message on the stack.

I'd also be suspicious of any thread whose measured high-water mark is close to its allocation. A comfortable margin — often cited as 25–50% headroom — is cheap insurance, because stack usage can grow silently when someone adds a local buffer or a new function call three layers deep. And I'd treat stack sizing as something to re-verify after significant changes, not a one-time decision. If the project uses static analysis, tools that compute worst-case stack depth (like `puncover` or compiler-generated stack usage reports) are worth running in CI so a regression gets caught at review time rather than in the field.

**Possible follow-ups:**
- How would you handle a thread whose stack usage is dominated by a single large local buffer — would you move that buffer off the stack, and what are the trade-offs?
- On an architecture where ISRs share the interrupted thread's stack, how does that change your sizing calculation?

## Q3: A junior engineer has written a driver that works reliably on the bench but uses a fixed `k_sleep` delay to wait for a peripheral to become ready after each command, rather than checking a status register or using an interrupt. How would you guide them?

**Answer:** I'd start by acknowledging that the code works and that the instinct behind it — "wait long enough and it'll be ready" — isn't unreasonable on the surface. The goal isn't to make them feel wrong; it's to help them see why the approach is fragile in ways that don't show up on the bench.

The first issue is that a fixed delay is a guess about timing that the datasheet may not actually guarantee. If the delay is chosen to cover the typical case, it will eventually fail on a slow part, at temperature extremes, or when the peripheral is busy with something else. If it's chosen to cover the worst case, it wastes time on every single transaction. Either way, the delay encodes an assumption that isn't verified at runtime.

The second issue is that `k_sleep` yields the CPU, which is better than a busy-wait, but it still means the calling thread is blocked for the full delay even when the peripheral became ready almost immediately. In a system with any timing sensitivity, that's latency you're paying for no reason.

I'd walk them toward the better pattern incrementally. The simplest improvement is to poll the status register with a bounded timeout — check, and if not ready, yield briefly and check again, up to a maximum. That's still polling, but it's adaptive and it fails loudly instead of silently proceeding with bad data. The next step up is to use the peripheral's ready interrupt or a DMA-complete callback, so the thread sleeps until the hardware actually signals completion. That's the pattern that scales and that composes well with an RTOS.

I'd frame it as: the fixed delay is a placeholder for "I don't yet know how to wait for the real signal." Once you know what the real signal is — a status bit, an interrupt, a DMA flag — you can wait for that instead, and the code becomes both faster and more correct. I'd also point out that a bounded poll with a timeout is a good intermediate step because it surfaces the failure instead of hiding it, which makes debugging the next issue much easier.

**Possible follow-ups:**
- How would you decide between a bounded poll and an interrupt-driven wait for a given peripheral?
- What would you do if the peripheral's ready signal isn't exposed as an interrupt and the status register isn't reliable?

## Q4: How would you approach designing a firmware module that must detect a "stuck" peripheral — one that stops producing data without raising an error flag or interrupt — and recover from it without resetting the whole device?

**Answer:** This is a class of failure that's easy to miss because the peripheral is behaving "correctly" from its own point of view — it just isn't producing data, and it isn't telling you that. The detection has to come from outside the peripheral's own status reporting.

The first layer is a liveness check based on expected data flow. If the peripheral is supposed to produce a sample every N milliseconds, the firmware should have a watchdog-style monitor that expects to see data within some multiple of that interval. If the interval passes with no data, that's a fault condition, regardless of what the peripheral's status register says. The threshold needs to be chosen carefully — too tight and you get false positives during legitimate pauses; too loose and you're slow to detect a real hang.

The second layer is a recovery sequence that's graduated rather than binary. The first step is usually a soft reset of the peripheral — disable it, re-run its initialization sequence, re-enable it — without touching the rest of the system. If that doesn't restore data flow, the next step might be a bus-level recovery: for I2C, that could mean clocking out a stuck slave; for SPI, it might mean toggling chip select and re-initializing. Only if those fail would you escalate to a broader reset, and even then, the goal is to reset the smallest scope that fixes the problem.

The third layer is state management. When the peripheral is being recovered, the rest of the system needs to know that data from that peripheral is temporarily unavailable, so downstream consumers don't act on stale or missing data as if it were fresh. That means the recovery path has to interact with whatever graceful-degradation logic the system already has — marking the data source as invalid, suppressing derived outputs, and logging the event for later analysis.

I'd also make sure the recovery is observable. A silent recovery that works is fine, but you want a counter or a log entry so that if the same peripheral is getting stuck repeatedly, that pattern is visible rather than buried. A peripheral that needs recovery once a month is a different problem from one that needs it once an hour.

**Possible follow-ups:**
- How would you choose the liveness timeout so that it catches real hangs without false-triggering on legitimate pauses in data flow?
- If the peripheral is on a shared bus with other devices, how does that change your recovery strategy?

## Q5: How would you approach a situation where you've inherited a firmware module with no tests, no documentation, and a reputation for being fragile, and you need to make a change to it?

**Answer:** The instinct to rewrite is strong in this situation, and it's usually wrong — at least as a first move. The module has a reputation for being fragile, which means it probably contains accumulated fixes for problems that aren't obvious from reading the code. A rewrite throws away that embedded knowledge and reintroduces the same bugs in a new form.

I'd start by treating the existing behavior as the specification, even though it's undocumented. The first task is to characterize what the module actually does, not what it's supposed to do. That means reading the code carefully, tracing the call paths, and — critically — building a test harness that exercises the module's current behavior so I have a baseline. The tests don't have to be comprehensive; they have to be good enough to catch a regression in the behavior I'm about to touch. Characterization tests written against the current behavior, even if that behavior is ugly, are the safety net.

Then I'd make the smallest possible change that accomplishes the goal, with the tests running before and after. If the change requires understanding a part of the module I don't yet understand, I'd add instrumentation or logging to observe it in operation rather than guessing. The goal is to avoid the situation where I change something, it breaks in a way I don't understand, and I'm now debugging two problems at once.

Along the way, I'd document what I learn — not a full rewrite of the documentation, but notes on the parts I've had to understand, the invariants the module relies on, and the failure modes I've observed. That documentation is what makes the next change easier, and it's often more valuable than the change itself.

If, after characterizing the module, it becomes clear that the fragility is structural — the module's design makes correct changes nearly impossible — then a rewrite becomes a reasonable option, but it should be a deliberate decision made with the characterization tests in hand, not a reflex. And even then, the rewrite should be incremental where possible, replacing the module piece by piece rather than all at once.

**Possible follow-ups:**
- How would you decide when the accumulated fragility justifies a rewrite rather than continued incremental change?
- If the module has no tests and you can't easily run it in isolation, how would you build a characterization harness?