# firmware — Day 94

## Q1: How would you approach designing a watchdog strategy for a device that must distinguish between a genuine firmware hang and a legitimate but slow operation, without simply extending the timeout until the watchdog becomes meaningless?

**Answer:** The core problem is that a single timeout value forces a trade-off between fault-detection latency and tolerance for long operations, and widening the timeout to accommodate the slowest operation degrades detection for everything else. I'd separate the two concerns rather than compromise on one number.

The first technique is a windowed watchdog rather than a simple timeout. A windowed watchdog resets the device if the kick arrives *too early* as well as too late, which catches the case where a task has run away and is kicking in a tight loop without doing real work — a failure mode a plain timeout misses entirely. The window is set around the expected kick cadence for the normal path.

For the long operation itself, I'd avoid having the slow routine kick the watchdog directly from inside its loop, because that couples the watchdog to code that may itself be the thing that's hung. Instead, the long operation reports progress to a supervisor — for example, it updates a progress counter or sets a "busy" state with an expected duration — and the supervisor decides whether the operation is still making forward progress. If the operation stalls without advancing its progress marker, the supervisor stops kicking and lets the watchdog fire. This keeps the kick decision in one place and makes "is this still alive?" an explicit question rather than an implicit one.

A second option is to have the long operation run in a context where the watchdog is temporarily serviced by a dedicated timer-driven path that only kicks while a valid "operation in progress" flag is set, with a hard ceiling on how long that flag can remain set. That ceiling is the real safety net: no operation is allowed to suppress the watchdog indefinitely.

I'd also make sure the watchdog is independent — either a hardware watchdog with its own clock source or at minimum one that isn't disabled by the same fault that hangs the CPU — and that debug-mode bypass is deliberate and documented, not accidental. And I'd instrument it: log why each kick happened and which subsystem was being serviced, so that when a reset does occur there's evidence to work from rather than a bare reset with no context.

**Possible follow-ups:** How would you test that the watchdog actually fires when it should, given that a hung system can't log anything? What's the risk of a supervisor task that itself becomes the bottleneck for every subsystem's liveness?

## Q2: How would you approach implementing a state machine for a device's operational modes where the same event can arrive from multiple sources — a user interface, a communication interface, and an internal timer — and the correct transition depends on which source sent it?

**Answer:** The key insight is that the event's *identity* isn't just "what happened" but "what happened and where it came from," and the state machine should model that explicitly rather than collapsing sources into a single event code and then trying to disambiguate inside the transition logic.

I'd define events as a structured type carrying at minimum an event ID and a source identifier, and where relevant a payload. The transition table or switch then keys on the pair (current state, event ID, source) — or, more maintainably, the event ID namespace is partitioned by source so that "START from UI" and "START from comms" are genuinely distinct events that happen to share a verb. That keeps the transition logic flat and readable instead of nesting source checks inside each case.

The second concern is arbitration. If two sources can produce conflicting events in the same window — say the UI requests a mode change while a timer-driven safety event fires — the state machine needs a defined precedence. I'd make that precedence explicit and documented, typically by giving safety/internal events priority over user-initiated ones, and by defining what happens to a user request that arrives during a safety transition (usually rejected with a reason, not silently dropped). The state machine should be the single authority on mode; no other module should set the mode variable directly.

I'd also separate *event generation* from *event handling*. Each source's driver or handler posts an event into a queue; a single state-machine task drains the queue and processes events in order. That serializes transitions, eliminates the race where two sources try to transition simultaneously, and makes the whole thing testable — you can feed a scripted event sequence and assert the resulting state trajectory without any hardware.

For maintainability, I'd keep the transition logic in one place — a table or a single well-structured dispatch — and keep the *actions* (what to do on entering a state) in separate functions. That way adding a source or an event is a localized change, and the state machine's structure stays visible at a glance.

**Possible follow-ups:** How would you handle an event that arrives while a transition is already in progress and the machine isn't ready to accept it? Where would you put the logic that decides whether a user-initiated event is even legal in the current state?

## Q3: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the first move is to resist the temptation to "fix" it by changing timing blindly. The debugger changes several things at once: it halts the CPU at breakpoints, it may slow or alter memory access, it can mask timing-sensitive races, it changes the power profile, and it may disable or alter low-power modes. So the first job is to figure out *which* of those differences is masking the bug.

I'd start by narrowing the observation method. If the misbehavior disappears with the debugger attached but I can still run standalone with logging over a UART or a RAM buffer, I'd capture evidence that way — a ring buffer in RAM that survives until the fault, dumped on the next boot. That gives me a trace without halting the CPU. If the fault is a hard fault, I'd make sure the fault handler captures the stacked registers, fault status registers, and a stack snapshot before resetting, so the next boot can report what happened.

Then I'd test specific hypotheses about what the debugger is masking. If it's a race condition, the debugger's halts widen timing windows and hide it — so I'd look for unsynchronized shared state, missing memory barriers, or ISR/main-loop interactions. If it's a low-power issue, the debugger often keeps clocks or peripherals alive that would otherwise be gated, so I'd check whether the bug correlates with sleep entry/exit. If it's a timing margin issue — a peripheral that needs settling time, a bus that's marginal — the debugger's slower execution can accidentally provide the margin.

I'd also check the obvious: does attaching the debugger change the boot path, disable a watchdog, or alter a configuration fuse? Some parts behave differently under debug by design.

The disciplined approach is to change one variable at a time: run standalone with logging only, then with the debugger attached but not halted, then with breakpoints, and see where the behavior flips. That localizes which debugger side-effect is responsible, which usually points straight at the root cause.

**Possible follow-ups:** How would you capture a trace of what happened before a hard fault without a debugger attached? What kinds of bugs are *more* likely to appear with the debugger attached rather than less?

## Q4: How would you approach deciding whether a piece of firmware logic belongs in an interrupt service routine versus a deferred context such as a work queue or a thread?

**Answer:** The default should be "as little as possible in the ISR," and the burden of proof is on keeping something in interrupt context. The reasoning is that ISR time is a shared, non-preemptible resource: everything you do there delays every other interrupt and every thread, and it's the hardest context to debug.

The criteria I'd apply: does this work need to happen before the interrupt source can be re-enabled or before the next event arrives? If the peripheral will overrun or lose data unless serviced within microseconds, the *minimum* necessary to prevent that — reading a data register into a buffer, clearing the status flag, re-arming the peripheral — belongs in the ISR. Everything else — parsing, validation, state transitions, logging, communication — belongs in a deferred context.

A useful test is to ask what the ISR would do if the deferred context were slow. If the answer is "nothing bad, as long as the buffer doesn't overflow," then the work can be deferred. If the answer is "we lose data," then either the buffer is too small or the work genuinely must be in the ISR — and I'd first check whether a larger buffer or DMA would let me defer it anyway.

I'd also consider the latency budget explicitly. If the system has a hard real-time requirement — say a control loop that must complete every millisecond — then the ISR's worst-case execution time is part of that budget, and anything that pushes it up is a direct threat to the deadline. Deferring work is how you keep the ISR bounded.

The mechanism for deferral matters too: a work queue is fine for low-priority housekeeping, a dedicated thread with appropriate priority is better when the deferred work has its own timing requirement, and a bottom-half or threaded interrupt is appropriate when the work is logically part of the driver but too heavy for the ISR. The choice should follow the work's priority and latency needs, not convenience.

**Possible follow-ups:** How would you decide the priority of the deferred thread relative to other threads in the system? What's the risk of deferring work to a thread that then gets starved?

## Q5: You're leading a firmware team that is transitioning from a bare-metal approach to using an RTOS for a new medical device. Two senior engineers disagree: one wants to port the existing bare-metal drivers directly into the RTOS as custom drivers, while the other wants to rewrite them using the RTOS's native driver model. How would you guide the team to a decision?

**Answer:** I'd start by reframing the disagreement away from "port vs. rewrite" and toward "what does each option actually cost us over the device's life, and what does the regulatory context demand?" Both engineers are probably right about something, and the job is to surface what that is.

The case for porting is real: the bare-metal drivers are proven, they've been through validation, and rewriting them introduces new risk into code that currently works. In a medical device, "it works and it's been tested" has genuine value, and a rewrite means re-verifying behavior that was already verified. The case for the native model is also real: custom drivers that bypass the RTOS's driver framework tend to fight the RTOS — they don't participate in its power management, they don't compose with its device tree or configuration system, and they become a maintenance island that only the original author understands.

So I'd structure the decision around a few concrete questions. First, how much of the existing driver is actually reusable? Often the register-level logic — the sequences, the timing, the error handling — is the valuable part and is largely portable, while the *integration* with the system (how it's called, how it blocks, how it reports errors) is what needs to change. That suggests a middle path: keep the proven register-level logic, but wrap it in the RTOS's driver model so it participates in the framework. That's often the best of both.

Second, what does the regulatory and verification burden look like for each path? If the existing drivers are part of a validated design history file, I'd want to understand what re-verification a rewrite triggers versus what a wrapper preserves. That's a conversation to have with the quality/regulatory side early, not after the decision.

Third, what's the team's actual familiarity with the RTOS's driver model? If nobody has written a native driver before, the first one will be slow and error-prone, and that cost is real. I'd factor in a learning curve and possibly a spike — have one engineer write one native driver as a proof of concept and measure how it goes — rather than deciding in the abstract.

My role as lead is to make the criteria explicit, get both engineers to agree on what "good" looks like, and then let the evidence decide rather than letting seniority or volume decide. I'd also make sure the decision is documented with its rationale, because in a year someone will ask why the drivers look the way they do.

**Possible follow-ups:** How would you handle it if the proof-of-concept driver takes three times longer than estimated? What would you do if the regulatory team says a rewrite triggers a full re-validation you can't afford on this schedule?