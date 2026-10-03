# firmware — Day 74

## Q1: How would you approach implementing a state machine where the same event can arrive from multiple sources (a user interface, a communication interface, and an internal timer), and the correct transition depends on which source sent it?

**Answer:** The key insight is that the event itself is not enough information — the state machine needs to know both *what* happened and *where it came from*, because the same nominal event can mean different things depending on origin. I'd model this by making the event type a composite: a source identifier plus an event code, rather than a flat enum of event codes. That way the transition table (or switch) can key on the pair, and the handler can distinguish "start requested by operator via UI" from "start requested by remote command" from "start triggered by internal timeout."

Structurally, I'd keep the state machine itself pure — a function that takes current state plus a composite event and returns the next state plus any actions — and have each source (UI task, comms task, timer callback) translate its raw input into that composite event before posting it to a single event queue. This centralizes the decision logic in one place, avoids scattering source-specific conditionals across modules, and makes the machine testable in isolation by feeding it synthetic events. It also naturally handles the case where a source is not permitted to trigger a transition in a given state: the transition table simply has no entry for that (state, source, event) tuple, and the machine can log or reject it explicitly rather than silently ignoring it.

I'd also think about priority and ordering. If two sources can post events nearly simultaneously, the queue ordering determines which transition wins, so I'd want a defined policy — either a priority field on the event or a documented rule that certain sources are only processed in certain states. And for safety-critical devices, I'd make sure that transitions triggered by an external source (comms) are gated by the same validation as internal ones, so a malformed or out-of-sequence remote command can't drive the device into an unsafe state.

**Possible follow-ups:**
- How would you represent the transition table so that adding a new source later doesn't require touching every state handler?
- What would you do if a source sends an event that is valid in the current state but arrives out of order relative to another source's event?

## Q2: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the first thing I'd do is resist the temptation to "fix" it by leaving the debugger attached. The debugger changes timing, halts the CPU, may mask or delay interrupts, and can alter power state — so the fact that it disappears under debug tells me the bug is timing- or state-dependent, not logic-dependent.

My approach would be to first characterize *what* the debugger changes. Attaching a debugger typically: slows execution, changes interrupt latency, may keep certain clocks or peripherals alive, and can prevent low-power modes from being entered. So I'd form hypotheses around those. For example, if the misbehavior only happens standalone, it could be a race condition that the debugger's slowdown happens to serialize, an uninitialized variable that the debugger's memory access happens to zero, a low-power transition that only occurs when not halted, or a watchdog that only fires when the CPU isn't being stopped.

To narrow it down without the debugger, I'd instrument the firmware itself: add a lightweight trace buffer in RAM (or a GPIO toggle) that records key events with timestamps, then read it out after the failure. This gives visibility into the sequence of events without perturbing timing the way a debugger does. I'd also try to reproduce with the debugger attached but *not* halted — i.e., using it only for observation — to see if the bug reappears, which would point at the halt itself rather than the connection.

If the trace points at a specific subsystem, I'd then use targeted techniques: for a suspected race, add assertions or a canary; for a suspected uninitialized read, initialize all RAM to a known pattern at startup and see if behavior changes; for a suspected power-state issue, log the power transitions. The goal is to make the bug observable in the standalone configuration, then fix the root cause rather than the symptom.

**Possible follow-ups:**
- How would you design a trace buffer so that it survives a reset and can be read out on the next boot?
- What are the risks of using a GPIO toggle as a debug signal in a system with tight timing or EMI constraints?

## Q3: How would you approach designing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** When the interrupt rate exceeds what the CPU can service, the ISR stops being a solution and becomes the problem — you get interrupt storms, missed deadlines elsewhere, and potentially a system that spends all its time in interrupt context. The first thing I'd do is quantify: what is the actual event rate, what is the ISR's execution time, and what is the CPU's available headroom? If the ISR is doing more than the minimum (e.g., parsing, logging, or buffer management), the fix may simply be to move work out of the ISR into a deferred context.

If the rate is genuinely too high for per-event interrupts, I'd look at reducing the number of interrupts rather than servicing them faster. Options include: switching to DMA so the peripheral transfers a block of data and interrupts only on completion or half-completion; using a FIFO in the peripheral so multiple events are batched into one interrupt; or, if the peripheral supports it, moving to a polling or timer-driven sampling scheme where the CPU reads a status register at a controlled rate rather than being interrupted per event. Each has trade-offs — DMA adds complexity and buffer management, FIFOs add latency, polling can miss events if the rate is bursty — so the choice depends on whether the data is lossy-tolerant or must be captured exactly.

If the events must be captured exactly and the rate is truly beyond the CPU, then the architecture itself is wrong and the answer is to add hardware (a small FPGA or a dedicated co-processor) or to reduce the event rate at the source. I'd also consider whether the ISR can be made cheaper: avoiding floating point, avoiding function calls into heavy code, using a minimal hand-off to a ring buffer, and ensuring the ISR is marked appropriately so the compiler doesn't generate unnecessary prologue/epilogue. The key is to treat the ISR as a hand-off mechanism, not a processing stage.

**Possible follow-ups:**
- How would you decide between DMA and a peripheral FIFO for a given data rate and buffer size?
- What symptoms would tell you that the ISR bottleneck is causing problems elsewhere in the system, rather than just in the peripheral itself?

## Q4: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** Stack sizing is one of those things that's easy to get wrong in both directions — too small causes corruption that's hard to trace, too large wastes RAM that a constrained device can't spare. My approach starts with a structured estimate, then verifies empirically, then adds margin.

For the estimate, I'd break down what each thread actually does: local variables, function call depth (including library calls like printf or floating-point routines, which can be surprisingly deep), interrupt stack usage if the thread can be interrupted (on some architectures the ISR uses the current thread's stack), and any context saved by the scheduler. I'd look at the worst-case call chain, not the typical one, because stack overflow happens at the worst moment, not the average. For threads that call into third-party or RTOS code, I'd check the vendor's documented stack requirements rather than guessing.

For verification, Zephyr provides tooling: `CONFIG_THREAD_STACK_INFO` and the `k_thread_stack_space_get()` API let you query high-water marks at runtime, and the `CONFIG_INIT_STACKS` option fills stacks with a known pattern so you can see how much was actually used. I'd run the system through its worst-case scenarios — not just nominal operation — and check the high-water marks. If a thread's usage is close to its allocation, I'd increase it; if it's using a small fraction, I'd consider trimming, but conservatively.

The margin question is important: I'd want enough headroom to absorb the difference between measured and worst-case, plus some for future changes. A common rule is to leave 25–50% headroom, but that's a heuristic — the real answer depends on how well you've characterized the worst case. I'd also enable stack sentinel or canary checking during development so that an overflow is caught immediately rather than manifesting as mysterious corruption later. And I'd document the sizing rationale, because the next person to touch the thread needs to know why it's sized the way it is.

**Possible follow-ups:**
- How would you handle a thread whose stack usage is highly variable depending on input, where the worst case is hard to bound?
- What are the trade-offs of using a separate interrupt stack versus sharing the thread stack, and how does that affect your sizing?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** This is a really common misconception, and I'd approach it as a teaching moment rather than a correction, because the engineer's reasoning isn't stupid — it's just incomplete. `volatile` does guarantee that the compiler won't optimize away or reorder accesses to that variable *relative to other volatile accesses*, which is why it's necessary for memory-mapped I/O and for variables shared with an ISR. But it does *not* provide atomicity, and it does *not* provide memory ordering guarantees on all architectures, and it does *not* prevent the compiler from reordering non-volatile accesses around it.

So the first thing I'd do is ask them to walk me through what happens if the variable is wider than the CPU's native word size, or if the ISR writes it while the thread is mid-read. On a 32-bit MCU, a 32-bit aligned write is typically atomic, but a 64-bit value or a struct is not — and `volatile` doesn't change that. I'd also ask about the case where the thread reads the flag, then reads a data buffer that the ISR wrote *before* setting the flag: without a memory barrier or an atomic operation with acquire/release semantics, the compiler or CPU could reorder those reads, and the thread could see the flag set but stale data.

The fix depends on what's actually needed. If it's a simple flag, an atomic type (like C11 `_Atomic` or Zephyr's `atomic_t`) with the appropriate memory ordering is the right tool. If it's a producer-consumer hand-off, a proper synchronization primitive — a `k_sem`, a `k_fifo`, or a lock-free ring buffer with correct memory barriers — is more appropriate. I'd frame it as: `volatile` tells the compiler "this can change unexpectedly," but it doesn't tell the compiler "this is shared state that needs synchronization." Those are different problems.

I'd also make sure the conversation is constructive: acknowledge that the code works in testing, explain *why* it works (probably because the compiler happened not to reorder, or the timing happened to be favorable), and explain why that's not a guarantee. Then I'd suggest a concrete refactor and offer to review it. The goal is for them to internalize the distinction, not just to change the code.

**Possible follow-ups:**
- How would you demonstrate the failure mode in a test, so the engineer can see the problem rather than just being told about it?
- What synchronization primitive would you recommend for a single-producer, single-consumer hand-off, and why?