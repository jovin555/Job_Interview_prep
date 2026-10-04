# firmware — Day 75

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** The first step is to quantify the problem rather than assume it. I'd measure the actual interrupt rate, the worst-case ISR execution time, and the CPU headroom left for everything else. If the ISR is genuinely saturating the CPU, no amount of clever ISR code will fix it — the architecture has to change.

The core principle is to make the ISR do the absolute minimum: acknowledge the interrupt, move the data (or a pointer to it) into a buffer, and return. Everything else — parsing, filtering, state updates, logging — belongs in a deferred context. In Zephyr that typically means a work queue or a dedicated thread woken by a semaphore or message queue. The ISR should never call anything that can block, allocate, or take a mutex.

If the rate is still too high even with a minimal ISR, I'd look at three levers. First, DMA: if the peripheral supports it, let the DMA controller move data into a ring buffer and have the interrupt fire only on a half-buffer or full-buffer boundary rather than per sample. That converts a per-byte interrupt storm into a handful of interrupts per buffer. Second, hardware FIFOs: many peripherals have a configurable watermark so the interrupt only asserts when N samples are queued. Third, if the peripheral supports it, coalescing or batching at the hardware level.

I'd also check whether the interrupt priority is set correctly relative to other interrupts in the system. A very high-rate interrupt at the highest priority can starve lower-priority interrupts and cause subtle timing failures elsewhere. Sometimes the right answer is to lower its priority and accept slightly more latency, so the rest of the system stays healthy.

Finally, I'd verify the fix under worst-case conditions — maximum data rate, all other subsystems active — not just nominal. The failure mode here is usually a slow degradation that only shows up when the system is fully loaded.

**Possible follow-ups:**
- How would you decide between a work queue and a dedicated thread for the deferred processing?
- What would you do if the peripheral doesn't support DMA or a hardware FIFO?

## Q2: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The key insight is that an edge on a data-ready line is a hint, not a guarantee. The firmware should treat the edge as "something may be ready" and then confirm that with the peripheral's own status register or a validity check on the data itself before acting on it.

Concretely, I'd structure the ISR to do the minimum: set a flag or post to a semaphore, and let a deferred context do the actual read. In that deferred context, before reading, I'd check the peripheral's status register (if it has one) to confirm data is actually available. If the peripheral has no status register, I'd validate the data after reading — check a CRC, a range, a sequence number, or whatever the protocol provides — and discard anything that fails validation.

For the glitch itself, there are two layers of defense. At the hardware level, a small RC filter or a Schmitt-trigger input can suppress very short glitches, and if the MCU supports it, a digital input filter (some peripherals have a configurable glitch filter) is even better because it's deterministic. At the firmware level, I'd consider debouncing in the ISR: ignore edges that arrive within a minimum time window after the last accepted edge, since the peripheral physically cannot produce valid data that fast. That's a cheap, deterministic guard.

I'd also think about what happens if a real edge is missed because of the debounce window. If the peripheral can genuinely produce back-to-back data-ready events, the debounce window has to be shorter than the minimum inter-event time, and I'd verify that against the datasheet. If it can't, the window is safe.

The failure mode to avoid is treating every edge as gospel and reading the peripheral when it has nothing to give — that can return stale data, garbage, or lock up the bus. Confirming before acting is the discipline that makes this robust.

**Possible follow-ups:**
- How would you test this in the lab without being able to reproduce the glitch on demand?
- What would you do if the peripheral's status register itself is unreliable?

## Q3: How would you approach designing a firmware module that must survive a brownout — where the supply voltage sags briefly but doesn't fully drop — without corrupting persistent state or producing a spurious reset?

**Answer:** Brownout is one of the nastier failure modes because the MCU may keep running while its behavior becomes undefined — flash writes can corrupt, RAM contents can flip, and the brownout detector may or may not trip depending on how the supply sags. The design has to assume the worst.

The first line of defense is the hardware brownout detector (BOD) or supply voltage supervisor. If the MCU has one, I'd enable it and set the threshold high enough that it trips before the core voltage drops below the level where flash writes or RAM retention become unreliable. The BOD ISR should be treated as an emergency: stop any in-progress flash write, mark the persistent state as "in transition," and either complete the operation atomically or abandon it cleanly. The goal is to never leave persistent state in a half-written condition.

For persistent state, the standard technique is a journal or a double-buffered scheme. Instead of overwriting a configuration block in place, write the new version to a second slot, verify it, then update a small "active slot" pointer. If power fails mid-write, the old slot is still intact and the pointer still points to it. The pointer update itself has to be atomic — either a single word write with a CRC, or a small commit record that's only considered valid if its CRC checks out.

For RAM, I'd be careful about what's assumed to survive. If the design relies on RAM retention across a brownout, that's a risky assumption unless the datasheet explicitly guarantees it down to the BOD threshold. Anything critical should be re-derived from persistent state on wake, not assumed to still be in RAM.

I'd also make sure the reset path is clean. A brownout that trips the BOD should produce a reset that the firmware can distinguish from a power-on reset, so the boot code knows to check for an interrupted operation and recover. If the BOD doesn't trip and the MCU keeps running through the sag, the firmware should have a periodic "am I still healthy?" check — a watchdog, a supply voltage readback via ADC, or both — so it can detect the condition and reset deliberately rather than continue in an undefined state.

**Possible follow-ups:**
- How would you decide the BOD threshold, given that too high causes spurious resets and too low risks corruption?
- How would you test brownout behavior without a programmable supply?

## Q4: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** I'd start by acknowledging what they got right: `volatile` does prevent the compiler from caching the variable in a register or optimizing away the access, and that's a real concern in ISR-shared code. So their instinct isn't wrong — it's just incomplete.

The gap is that `volatile` says nothing about atomicity or ordering. On a 32-bit MCU, a 32-bit aligned read or write is usually atomic, but a multi-byte structure, a read-modify-write, or a non-aligned access is not. And even for a single word, `volatile` doesn't prevent the compiler or CPU from reordering other memory accesses around it, which matters if the flag is meant to signal that other data is ready. The classic bug is: ISR writes data, then sets a `volatile` flag; the thread sees the flag but reads stale data because the data write hadn't been ordered before the flag write.

The right tool depends on what's being communicated. For a simple "data is ready" signal where the data itself is a single word, an atomic type or a memory barrier plus `volatile` can be sufficient. For anything more complex, the correct primitives are a semaphore, a message queue, or a `k_fifo` — Zephyr provides all of these, and they handle the memory ordering and wake-up semantics correctly. For a shared buffer, a mutex or a lock-free ring buffer with proper acquire/release semantics is the right answer.

I'd frame it as: `volatile` is a compiler directive, not a synchronization primitive. It tells the compiler "don't assume this doesn't change," but it doesn't tell the CPU or the memory system anything. Synchronization is about ordering and atomicity, and that's what the kernel primitives are for.

I'd also point them at the specific failure mode — the reordering bug — and suggest they try to reproduce it by adding a small delay or a compiler barrier in the right place. Seeing the bug appear and disappear is usually more convincing than an argument.

**Possible follow-ups:**
- Are there cases where `volatile` alone is genuinely sufficient for ISR/thread communication?
- How would you review the rest of the codebase for similar patterns without being heavy-handed about it?

## Q5: How would you approach a situation where you discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules?

**Answer:** The first thing I'd do is resist the urge to either hide it or immediately propose a rewrite. Both are emotional responses. The right move is to quantify the problem: what specifically is failing, how often, what's the impact, and what's the cost of each option. That turns a vague "this is bad" into a decision the team can actually make.

I'd lay out the options honestly. Option one: live with it, and mitigate the symptoms. Sometimes the design decision is ugly but the actual failure rate is low enough that a targeted workaround is the right call, especially late in a project. Option two: refactor the affected modules incrementally, behind a stable interface, so the change is contained and can be tested piece by piece. Option three: a full rewrite of the affected area, which is almost never the right answer late in a project but sometimes is if the design is fundamentally unsound.

The key is to separate "this is architecturally wrong" from "this is causing a problem we can't ship with." Those are different conversations. If it's the latter, an incremental refactor behind an interface is usually the answer — it lets the team keep shipping while the underlying design improves. If it's the former, the honest thing is to escalate early, with data, and let the people who own the schedule make the call.

I'd also own the decision. If I made the original call, I'd say so plainly rather than framing it as "the design" or "the code." That builds more trust than trying to distance myself from it, and it makes it easier for others to be honest about their own decisions later.

Finally, I'd make sure the lesson gets captured — not as blame, but as a design review note or a decision record — so the same class of decision gets more scrutiny next time. The value of a late discovery is partly in fixing it and partly in not repeating it.

**Possible follow-ups:**
- How would you decide whether to escalate to a program manager versus handle it within the team?
- What would you do if the team disagreed about whether the design decision was actually the root cause?