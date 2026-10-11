# firmware — Day 82

## Q1: How would you approach implementing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** The first step is to recognize the symptom: the ISR is consuming so much CPU that lower-priority work starves, or the ISR itself starts missing events because it can't return before the next one arrives. The root cause is almost always that the ISR is doing too much work per event — parsing, buffering, or even just too many register accesses — rather than the event rate being fundamentally unserviceable.

The general strategy is to shrink the ISR to the absolute minimum and move everything else to a deferred context. In practice that means the ISR does only what *must* happen in interrupt context: acknowledge the peripheral, capture the essential datum (a byte, a sample, a timestamp), push it into a lock-free or carefully-synchronized buffer, and return. Parsing, validation, protocol handling, and logging all move to a thread or work queue. If the event rate is genuinely higher than the CPU can handle even with a minimal ISR, then the architecture is wrong — the answer is DMA or a hardware FIFO so the CPU isn't involved per-event at all, or reducing the effective event rate by batching in hardware.

A few concrete techniques matter here. First, check whether the peripheral has a FIFO or DMA mode that lets you service many events per interrupt — that alone often drops the interrupt rate by an order of magnitude. Second, if the ISR must run per-event, keep it to a handful of instructions and avoid anything that can block or take a lock. Third, use a ring buffer with a single producer (the ISR) and a single consumer (a thread), which can be made lock-free with proper memory ordering. Fourth, if the ISR is still too slow, consider whether the interrupt priority is causing it to preempt something it shouldn't, or whether the peripheral's interrupt is firing on conditions you don't actually care about (e.g., both edges when you only need one).

The trade-off to articulate is latency versus throughput versus CPU budget. A minimal ISR plus deferred processing gives you bounded ISR latency and lets the scheduler decide what runs next, at the cost of some added complexity and a small latency penalty for the deferred work. That's almost always the right call when the ISR is the bottleneck.

**Possible follow-ups:**
- How would you measure whether the ISR is actually the bottleneck versus something else in the system?
- What synchronization primitives would you use for the ISR-to-thread handoff, and why?

## Q2: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the debugger's presence is itself a clue. Attaching a debugger changes several things: it may halt the core at breakpoints, it slows execution, it can change the timing of interrupts relative to main code, it may disable certain low-power modes, and it can affect the state of peripherals or clocks. So the first question is: which of those differences is masking the bug?

I'd start by narrowing down what "misbehaves" means — is it a crash, a wrong value, a missed event, a hang? That determines which class of bug is likely. Then I'd try to reproduce the failure without a debugger but with instrumentation that doesn't change timing much: a GPIO toggled at key points and captured on a scope or logic analyzer, a UART log at low baud, or a RAM-based trace buffer that's dumped after the fact. These perturb the system far less than a debugger halt.

Common root causes for debugger-dependent behavior include: a race condition that the debugger's slowdown happens to serialize correctly; an uninitialized variable that happens to be zero when the debugger's startup code runs; a timing-sensitive peripheral interaction (e.g., a sensor that needs a delay the debugger accidentally provides); a low-power mode that the debugger prevents from being entered, hiding a wake-up bug; or a watchdog that the debugger disables. I'd also check whether the debugger is masking a fault — some debug configurations will halt on a fault instead of resetting, so a fault that would reset the device standalone just looks like "it stopped."

The systematic approach is to bisect the differences. Run standalone but with the debugger's low-power disable replicated in firmware; run standalone but with a small deliberate delay added where the debugger would have halted; run standalone with the watchdog enabled versus disabled. Each experiment isolates one variable. Once the failure reproduces standalone, normal debugging applies.

**Possible follow-ups:**
- How would you capture a trace of what happened leading up to a failure without a debugger attached?
- What kinds of bugs are most likely to be masked by a debugger, and why?

## Q3: How would you approach designing a firmware module that must survive a brownout — where the supply voltage sags briefly but doesn't fully drop — without corrupting persistent state or producing a spurious reset?

**Answer:** A brownout is one of the harder reliability problems because the MCU may continue executing while its supply is out of spec, which means it can do unpredictable things — including writing garbage to flash or EEPROM. The design has to assume that at any moment the supply could sag, and that the firmware's job is to either ride it out cleanly or fail safely.

The first line of defense is hardware and MCU-level: most modern MCUs have a brownout detector (BOD) that holds the core in reset below a threshold. The firmware design should configure the BOD threshold high enough that the core stops before its operation becomes unreliable, and low enough that normal supply ripple doesn't trigger it. That threshold is a hardware/firmware co-design decision and needs to be validated against the actual supply behavior.

The second line of defense is the persistent-state design. Any write to non-volatile memory should be structured so that a power loss mid-write leaves the data in a recoverable state. The standard techniques are: write to a new location and only commit a pointer/flag after the write completes (so a torn write leaves the old data intact); use a checksum or CRC per record so a partially-written record is detected and discarded; and keep a small "in-progress" marker that's cleared only after the write is verified. For critical state, a journal or double-buffered scheme is worth the flash cost.

The third piece is detecting and recovering from the event. On boot, the firmware should check whether the last shutdown was clean — a "clean shutdown" flag set during normal power-down and cleared on boot. If it wasn't clean, the firmware knows a brownout or unexpected reset occurred and can take recovery action: re-validate persistent state, re-initialize peripherals that might be in an unknown state, and log the event. This is also where you'd decide whether to hold the device in a safe state until the supply is confirmed stable.

The trade-offs are flash wear (journaling costs erase cycles), boot time (validation adds latency), and complexity. For a medical device, the safe-state behavior on an unclean boot is usually the most important requirement, and it's worth the cost.

**Possible follow-ups:**
- How would you test that your brownout handling actually works, given that you can't easily reproduce a real brownout on the bench?
- What's the difference between a brownout and a brief power interruption, and how would the firmware design differ?

## Q4: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** I'd start by acknowledging the part they got right: `volatile` does tell the compiler not to cache the variable in a register or reorder accesses to *that variable* relative to other volatile accesses. So their intuition isn't baseless. But the gap is that `volatile` says nothing about atomicity, nothing about ordering relative to non-volatile accesses, and nothing about the memory model of the target — which is exactly where the bugs live.

The concrete failure modes I'd walk them through: a multi-byte variable (say a 32-bit counter on an 8- or 16-bit MCU) can be read by the thread while the ISR is halfway through updating it, producing a torn value. A flag-plus-data pattern — ISR sets data, then sets a flag; thread reads flag, then reads data — can be reordered by the compiler or the CPU such that the thread sees the flag set but stale data. And on a multicore or DMA-coherent system, `volatile` doesn't insert the memory barriers needed to make the write visible in the right order.

The right tool depends on the situation. For a single flag or a single word that fits in the native word size, an atomic type or an atomic load/store is the correct primitive — it gives both the compiler and the CPU the right guarantees. For a producer-consumer handoff of more than one word, the standard pattern is a lock-free ring buffer with acquire/release semantics on the head and tail indices, or a proper synchronization primitive if the platform provides one. In Zephyr, that might be a `k_sem`, a `k_fifo`, or an atomic-based scheme depending on whether the ISR can block (it can't) and what the latency budget is.

I'd frame the guidance as: `volatile` is a compiler directive, not a synchronization primitive. It's necessary in some cases (e.g., a memory-mapped register that the compiler must not optimize away) but never sufficient on its own for inter-context communication. Then I'd pair them with a concrete refactor of their module — pick the simplest correct primitive, add a comment explaining why, and add a test that exercises the handoff under stress. The goal isn't to make them feel wrong; it's to give them the mental model that `volatile` and "atomic" and "synchronized" are three different things.

**Possible follow-ups:**
- How would you write a test that would actually catch a torn read or a reordering bug in this module?
- When *is* `volatile` the right tool, and what's a concrete example?

## Q5: How would you approach a situation where you discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules?

**Answer:** The first thing I'd do is resist the urge to either panic or quietly work around it. Late-discovered design problems are normal in embedded work, and the response should be deliberate rather than reactive.

I'd start by characterizing the problem precisely: what exactly is the decision, what are the symptoms it's causing, and what's the cost of *not* changing it? Sometimes the "significant problems" are actually a small number of localized symptoms that can be mitigated without touching the architecture. Other times the decision is genuinely load-bearing and the rework is unavoidable. Being honest about which case this is prevents both over-reacting and under-reacting.

If the change is genuinely needed, I'd assess the blast radius: which modules depend on the decision, what's the migration path, and can it be done incrementally or does it require a big-bang change? Incremental is almost always preferable — it lets you keep shipping, validate each step, and back out if something goes wrong. I'd also look for a compatibility shim: can the old interface be preserved as a thin adapter over the new one, so modules can migrate one at a time rather than all at once?

Then I'd bring it to the team and stakeholders early, with a clear picture: what the problem is, what the options are (fix now, fix later, mitigate, accept), and what each costs in schedule and risk. This is the part where engineers sometimes go quiet and try to fix it in the background, which is usually the wrong call — the people planning the project need to know, and they may have context (a customer commitment, a regulatory milestone) that changes the calculus.

Finally, I'd make sure the fix includes a lesson: what signal would have caught this earlier, and how do we build that into the process? Maybe it's a design review at a different point, maybe it's a prototype that exercises the decision under realistic load, maybe it's a written-down assumption that someone could have challenged. The goal isn't blame — it's making the next project less likely to hit the same class of problem.

**Possible follow-ups:**
- How would you decide between fixing the design and mitigating the symptoms, if the schedule is tight?
- How would you communicate the issue to a stakeholder who's focused on the original delivery date?