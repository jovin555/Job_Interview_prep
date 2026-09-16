# firmware — Day 57

## Q1: How would you approach designing a firmware module that must detect and recover from a peripheral that silently stops responding — no error flag, no interrupt, it just stops producing data — without relying on the peripheral's own status reporting?
**Answer:** The core problem is that a silent failure gives you no signal from the device itself, so the detection has to come from outside it. The general approach is to build a liveness contract around the peripheral rather than trusting its status registers: define what "healthy" looks like in terms of observable behavior (a new sample within N ms, a counter incrementing, a heartbeat register changing), and have a supervisor — a watchdog-style task or a timer-driven check — verify that contract independently.

Concretely, I'd structure it in layers. First, a per-peripheral liveness monitor that timestamps the last successful transaction or data arrival and compares it against a deadline derived from the expected rate, with margin for jitter. Second, a recovery ladder that escalates rather than jumping straight to a full reset: re-initialize the peripheral and its bus, then power-cycle the peripheral if it has a controllable supply or enable pin, then reset the MCU as a last resort. Each rung should be attempted a bounded number of times before escalating, and the escalation state should be logged so the failure is diagnosable later.

The subtle parts are choosing the deadline and avoiding false positives. A deadline that's too tight will trip during legitimate long operations or bus contention; too loose and you've lost the safety benefit. I'd derive it from the worst-case legitimate gap plus margin, and make it configurable so it can be tuned during validation. I'd also distinguish "no data" from "stale data" — a peripheral that keeps returning the same value may be just as dead as one returning nothing, so a change-detection or sequence-number check can catch that class of failure.

For a medical device context, recovery also has to be safe: while the peripheral is being recovered, the system must not present stale or default values as if they were live measurements. That means the recovery path and the data-validation path have to be designed together — the consumer of the data needs to know the source is in a degraded state, not just receive whatever was last buffered.

**Possible follow-ups:**
- How would you decide whether a silent peripheral failure should trigger a full device reset versus a degraded-mode operation, and who should make that call?
- How would you test this recovery logic when the failure is, by definition, something the peripheral never reports?

## Q2: You're implementing a circular buffer shared between an ISR that writes samples and a task that reads them. How would you handle the case where the reader falls behind and the writer would overwrite unread data?
**Answer:** The first decision is what the correct behavior is when the buffer is full, and that's a system-level question, not a buffer-level one. There are three broad policies: overwrite the oldest data (drop-oldest), reject the newest sample (drop-newest), or block the writer until space is available. Blocking is almost never acceptable in an ISR, so in practice it's drop-oldest or drop-newest, and the choice depends on what the data is for. For a control loop, the freshest data usually matters most, so drop-oldest is often right. For an audit or logging path, losing the oldest data may be unacceptable, so drop-newest with an overflow counter is better.

Mechanically, the classic single-producer/single-consumer ring buffer works without locks if you're careful about the read and write indices. The writer owns the write index and only reads the read index; the reader owns the read index and only reads the write index. On a 32-bit MCU, if the indices are `size_t` and the buffer size is a power of two, the index updates are naturally atomic and you can use a mask instead of a modulo. The volatile qualifier goes on the indices, not the buffer contents, and you need a memory barrier or an acquire/release discipline to prevent the compiler and CPU from reordering the index update relative to the data write — otherwise the reader can observe a new index before the data it points to is visible.

The failure mode to watch for is the "full vs empty" ambiguity: if head equals tail, is the buffer empty or full? The standard fixes are to keep a count, to waste one slot, or to use a separate full flag. I'd also add an overflow counter that the reader can inspect, so the system can report that data was lost rather than silently pretending the stream was continuous — that matters a lot in a medical context where a gap in the data has clinical meaning.

**Possible follow-ups:**
- How would you extend this to multiple producers or multiple consumers, and what synchronization would that require?
- How would you size the buffer, and what would you measure to know whether the size is actually adequate?

## Q3: How would you approach deciding whether a piece of firmware logic belongs in an interrupt service routine versus a deferred context such as a work queue or a thread?
**Answer:** The default should be "as little as possible in the ISR." The ISR's job is to acknowledge the hardware, capture the minimum state needed to avoid losing information, and hand off the rest. Everything else — parsing, validation, logging, state machine transitions, anything that can block or take unbounded time — belongs in a deferred context.

The criteria I'd apply: First, does it have a hard deadline that only the ISR can meet? If the hardware will lose data or misbehave unless you respond within microseconds, it has to be in the ISR. Second, does it block or take unbounded time? Anything that calls into an RTOS primitive that can sleep, or that loops over a variable-length structure, is out. Third, does it touch shared state that other contexts also touch? If so, keeping it out of the ISR reduces the number of places you need to reason about concurrency. Fourth, does it need to run at a priority above everything else, or would a high-priority thread do just as well?

In Zephyr specifically, the tools for deferral are work queues (for short, non-blocking deferred work), `k_timer` callbacks (which run in the system timer's ISR context, so the same rules apply), message queues, and dedicated threads. A common pattern is: ISR captures the data into a small buffer or posts to a `k_msgq`, and a thread at an appropriate priority does the processing. The ISR stays short and bounded, and the processing runs at a priority you can reason about relative to the rest of the system.

The trade-off is latency and complexity. Deferring adds a scheduling delay and requires you to think about queue depths and back-pressure. But the alternative — a long ISR that disables interrupts for hundreds of microseconds — is usually worse, because it degrades the timing of everything else in the system, including things you didn't think were related.

**Possible follow-ups:**
- How would you measure whether an ISR is actually too long, and what would you do if you found it was?
- What's the difference between a work queue and a thread in Zephyr, and when would you choose one over the other?

## Q4: A junior engineer has written a driver that works reliably on the bench but uses a fixed delay to wait for a peripheral to become ready after each command, rather than checking a status register or using an interrupt. How would you guide them?
**Answer:** I'd start by acknowledging that the code works and that the instinct behind it — "I know this peripheral takes about X milliseconds, so I'll wait X milliseconds" — isn't unreasonable on its face. The problem is that it's a bet on the worst case, and that bet is usually wrong in at least one of three ways: the delay is too short under some conditions (temperature, voltage, part-to-part variation, a slower clock), the delay is too long and wastes time that could be doing useful work, or the delay is fine on the bench but not on the production hardware where the timing margin is different.

I'd walk them through the failure modes concretely. If the delay is too short, the driver reads garbage or the peripheral ignores the command, and the bug is intermittent and hard to reproduce — exactly the kind of thing that shows up in the field, not on the bench. If the delay is too long, the system is slower than it needs to be, and in a system with a real-time control loop, that delay is jitter that eats into the loop's margin. And a fixed delay is a hidden assumption about the hardware that isn't documented anywhere, so the next person to touch the code won't know why the number is what it is.

Then I'd show them the better pattern. The right approach depends on the peripheral: if it has a status register or a "ready" bit, poll that with a timeout — the timeout is the safety net, not the primary mechanism. If it has an interrupt, use it and let the driver sleep until the interrupt fires. If it's a bus transaction, use the bus controller's own completion signaling rather than a delay. The key idea is to wait on the actual condition, with a bounded timeout, rather than on a guess about how long the condition takes.

I'd also make the point that this isn't just about correctness — it's about testability and maintainability. A driver that waits on a condition can be tested by simulating the condition; a driver that waits on a fixed delay can only be tested by waiting. And I'd offer to pair with them on converting one instance so they can see the pattern in their own code, rather than just handing them a rule.

**Possible follow-ups:**
- What would you do if the peripheral genuinely has no status register and no interrupt, and the only way to know it's ready is to wait?
- How would you review the rest of the codebase for the same pattern, and how would you prioritize which instances to fix first?

## Q5: How would you approach a situation where you've inherited a firmware module with no tests, no documentation, and a reputation for being fragile, and you need to make a change to it?
**Answer:** The first move is to resist the urge to rewrite it. A module with a reputation for being fragile is often fragile in ways that aren't obvious from reading the code — the fragility may be load-bearing, in the sense that some other part of the system depends on the current behavior, including its quirks. A rewrite throws away that implicit knowledge and replaces it with your assumptions, which is how you turn a fragile module into a broken one.

So I'd start by characterizing the module's actual behavior rather than its intended behavior. That means building a test harness around it — even a crude one — that exercises the inputs and outputs you can observe, and capturing the current behavior as a baseline. The tests don't have to be pretty; they have to be repeatable. If the module talks to hardware, I'd look for a way to stub or simulate that hardware so the tests can run without the target. If it can't be tested at all in its current form, that itself is the first finding, and the first change might be to introduce a seam — a function pointer, a thin abstraction layer — that makes it testable without changing its behavior.

Once there's a baseline, I'd make the smallest possible change to address the actual requirement, and verify against the baseline. If the change requires understanding a part of the module that isn't clear, I'd add a comment or a short design note as I go, so the next person has a starting point. I'd also look for the specific fragility the reputation refers to — is it a race condition, an unhandled error path, a dependency on initialization order? — and if I find it, I'd document it and, if it's in scope, fix it with a test that demonstrates the fix.

The social part matters too. If the module has a reputation, there's probably someone who knows why. I'd ask around before assuming the code is the whole story — the fragility might be a workaround for a hardware erratum, or a response to a requirement that isn't written down anywhere. That conversation is often faster than reverse-engineering the code.

**Possible follow-ups:**
- How would you decide when the module has accumulated enough tests and documentation that a rewrite is now the lower-risk option?
- What would you do if the module's behavior is non-deterministic, so you can't capture a stable baseline?