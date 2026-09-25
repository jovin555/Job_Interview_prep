# firmware — Day 66

## Q1: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core problem is that an edge-triggered interrupt tells you *something happened*, not that *valid data is present*. The first line of defense is to treat the interrupt as a hint rather than a guarantee: in the ISR, do the minimum possible work — timestamp the event, set a flag or post to a work queue — and defer the actual decision about validity to a context where you can afford to check.

For the validity check itself, I'd look at what the peripheral actually exposes. Most data-ready sources have a companion status register, a FIFO level, or a data-valid bit that is authoritative. The ISR (or the deferred handler) should read that status and only proceed if it confirms real data. If the peripheral offers no such confirmation, then the protocol layer has to provide it — for example, a CRC or a sequence number on the payload, so a spurious wake-up simply fails validation and is discarded.

For the glitch itself, there are two angles. On the hardware side, a small RC filter or a Schmitt-trigger input can suppress short glitches before they ever reach the MCU, and this is often the cheapest fix. On the firmware side, a debounce window — ignoring further edges for a short period after the first — is reasonable if the real data rate is well below the glitch rate, but it's a blunt instrument and can mask genuine back-to-back events, so I'd only use it if the timing budget clearly allows.

The important design principle is that spurious events must be *harmless*, not just *rare*. If a glitch can cause the firmware to read a stale register and treat it as fresh data, that's a correctness bug waiting to happen. So I'd structure the handler so that a spurious edge results in a no-op or a discarded sample, never in a state transition or a logged value. I'd also add a counter for discarded events so that if the glitch rate rises — say, due to a marginal connection or EMI — it shows up in diagnostics rather than silently degrading data quality.

**Possible follow-ups:**
- How would you distinguish a genuine burst of high-rate events from a glitch storm, if both look like many edges close together?
- If the peripheral has no status register and no CRC, what other mechanisms could you use to gain confidence that a read is valid?

## Q2: How would you approach deciding whether a piece of firmware logic should run in an interrupt context, a deferred context (work queue or thread), or a low-priority background task?

**Answer:** I'd frame the decision around three properties: how much latency the logic can tolerate, how long it takes to execute, and what it needs to touch.

Interrupt context is for the minimum work needed to acknowledge the hardware and capture time-critical state — reading a data register before it's overwritten, clearing a flag, timestamping an event. The rule of thumb is that an ISR should be short and bounded, because it blocks everything at or below its priority. Anything that can block — taking a mutex, allocating memory, doing I2C or flash I/O — is disqualified from interrupt context outright.

Deferred context (a work queue or a dedicated thread) is where the real processing goes. This is the right home for anything that needs to call into a driver, take a lock, or run for more than a few microseconds. The choice between a work queue and a dedicated thread usually comes down to whether the work needs its own priority and stack, or whether it can share a cooperative worker. A work queue is lighter and simpler; a dedicated thread is warranted when the work has a specific priority relationship to other tasks or needs to block on its own synchronization primitives.

Low-priority background tasks are for things that genuinely don't care when they run — housekeeping, log flushing, statistics aggregation. The danger here is starvation: if the background task never gets scheduled because higher-priority work is always pending, it can silently stop making progress. So I'd want a way to detect that, either through a watchdog on the background task's progress or through a periodic health check.

The subtle cases are where the same event needs both fast acknowledgment and slow processing. The pattern there is to split: the ISR captures the event and hands off a minimal descriptor, and the deferred context does the heavy lifting. That keeps latency low without pushing work into a context where it doesn't belong.

**Possible follow-ups:**
- How would you decide the priority of a deferred work item relative to other threads in the system?
- What symptoms would tell you that you've put too much work in an ISR, and how would you confirm it?

## Q3: You're debugging a firmware issue where a device's behavior is correct on the first power-up after flashing, but after a warm reset (without power cycling) a peripheral initializes incorrectly. How would you approach this?

**Answer:** The asymmetry between cold boot and warm reset is the key clue. On a cold boot, every register in the system is at its power-on reset value. On a warm reset, the CPU restarts but many peripherals, clocks, and external chips retain whatever state they were left in. So the bug is almost certainly a case where the initialization code assumes a clean slate that only exists after a power cycle.

My first step would be to enumerate what *isn't* reset by a warm reset. That includes the peripheral's own registers if it's on a separate power domain, external chips on the board (sensors, PHYs, power management ICs), and any state held in RAM that survives a soft reset. I'd compare the register contents of the peripheral after a cold boot versus after a warm reset and look for the differences — that usually points straight at the missing step.

Common culprits are: a peripheral that needs an explicit software reset before configuration, because leftover configuration from the previous run causes the new configuration to be rejected or partially applied; an external chip that needs a power-cycle or a reset line toggled, which the firmware never asserts; and clock or PLL configuration that assumes the PLL is off, when in fact it's still locked from before.

The fix is to make initialization idempotent — that is, to bring the peripheral to a known state explicitly rather than assuming it starts there. That means issuing a software reset, waiting for it to complete, and then configuring from scratch, regardless of what state the peripheral was in. For external chips, it means asserting the reset line or the enable pin in a defined sequence at startup.

I'd also want to understand *why* this wasn't caught earlier. If the test procedure only ever power-cycles between runs, warm reset paths go untested. Adding a warm-reset test case to the bring-up checklist is the durable fix, not just patching the one peripheral.

**Possible follow-ups:**
- How would you determine which registers survive a warm reset on a given MCU, if the datasheet is ambiguous?
- If the peripheral is on a shared bus and another device is holding it in a bad state, how would you recover without a full power cycle?

## Q4: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** I'd start by acknowledging the part they got right: `volatile` does prevent the compiler from caching the variable in a register or eliminating the access, and that's a real and necessary property when a variable is shared with an ISR. The mistake is treating that as sufficient for synchronization, when it only addresses one of several hazards.

The first hazard is atomicity. `volatile` says nothing about whether a read-modify-write is atomic. If the thread does `counter++` on a `volatile` variable while the ISR also modifies it, the increment can be lost — the compiler will emit a load, an add, and a store, and an interrupt between the load and the store will clobber the result. For a single-byte flag this may not bite, but the moment the shared data is wider than the native word, or the access is a read-modify-write, it does.

The second hazard is ordering. `volatile` does not establish a memory barrier. The compiler and the CPU are both free to reorder non-volatile accesses around a volatile one, which means the thread can observe the flag as set before the data it's supposed to protect is actually visible. This is the classic "flag says ready but the buffer isn't" bug, and it's exactly the kind of thing that passes testing and fails in the field.

The right guidance is to steer them toward a proper synchronization primitive. For a simple flag or a single word, an atomic type with explicit acquire/release semantics is the correct tool — it gives both atomicity and ordering, and it documents the intent. For anything larger, a mutex or a message queue is the right answer, and in an RTOS the ISR-side primitive is usually a `k_sem_give` or a `k_msgq_put` from an ISR-safe variant. That moves the data across the boundary in a way the kernel understands, rather than relying on the programmer to reason about every possible reordering.

I'd frame it not as "your code is wrong" but as "here's the class of bug this pattern is vulnerable to, and here's the primitive that closes it." Showing a concrete interleaving where the current code fails is usually more convincing than an abstract argument.

**Possible follow-ups:**
- Are there cases where a `volatile` flag between an ISR and a thread *is* actually sufficient, and how would you decide?
- How would you audit an existing codebase for this pattern, and how would you prioritize which instances to fix first?

## Q5: How would you approach designing a firmware module that must detect and recover from a peripheral that has silently stopped responding — no error flag, no interrupt, it just stops producing data — without relying on the peripheral's own status reporting?

**Answer:** The defining feature of this failure mode is that the peripheral's own reporting is untrustworthy — if it's stopped, its status register may be stale, or it may report "fine" while producing nothing. So the detection has to come from outside the peripheral, based on the *absence* of expected behavior rather than the *presence* of an error.

The most reliable primitive is a liveness check driven by a timer. If the peripheral is expected to produce data at some rate, the firmware can maintain a timestamp of the last successful transaction and compare it against a deadline. If the deadline passes without a new event, the peripheral is presumed stuck. The deadline needs margin — it should be several times the expected interval, so that normal jitter or a brief bus stall doesn't trigger a false positive — but not so long that the system operates on stale data for an unacceptable period.

For peripherals that don't produce data spontaneously, the equivalent is a periodic health probe: a benign read of a known register, or a round-trip command, whose success confirms the peripheral is alive. The probe has to be chosen so that it doesn't disturb normal operation and so that its failure is unambiguous.

Recovery is where the design gets interesting, because the right response depends on what the peripheral is. For a simple sensor, a bus-level recovery — clocking out a stuck slave, re-initializing the peripheral, re-running the configuration sequence — is often enough. For something more complex, a full re-initialization including a hardware reset line may be required. The recovery should be attempted a bounded number of times; if it keeps failing, the module should escalate to a degraded mode rather than looping forever, and it should surface the condition to the rest of the system so that the higher-level logic can decide what to do.

Two design points I'd insist on. First, the liveness check must not itself depend on the peripheral's status reporting, or it inherits the same blind spot. Second, the recovery path must be tested — it's easy to write a recovery routine that's never exercised and turns out to be broken when it's finally needed. Injecting a fault that stops the peripheral is the only way to know the recovery actually works.

**Possible follow-ups:**
- How would you choose the liveness deadline if the peripheral's data rate varies with operating conditions?
- What would you log or report when a peripheral is recovered, so that a field failure can be diagnosed later?
- How would you avoid the recovery routine itself becoming a source of disruption if the peripheral is only briefly slow rather than truly stuck?