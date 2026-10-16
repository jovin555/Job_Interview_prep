# firmware — Day 87

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt rate is high enough that servicing every interrupt individually would consume an unreasonable share of CPU time?

**Answer:** The first step is to quantify the problem rather than assume it — measure the actual interrupt rate, the per-ISR cost (entry/exit overhead plus the work done), and the resulting CPU load, because "high enough to be a problem" is a number, not a feeling. If servicing every edge really does eat an unreasonable share of the budget, the goal becomes reducing the *number* of interrupts the CPU has to take, not just making each one faster.

The standard techniques, roughly in order of preference:

- **DMA with a large transfer and a completion (or half-transfer) interrupt.** Instead of one interrupt per byte or per sample, the peripheral fills a buffer autonomously and only interrupts the CPU when a block is done or when the buffer is half-full. This turns N interrupts into 1 or 2 per block. This is usually the highest-leverage fix for streaming peripherals.
- **FIFO/burst modes.** Many peripherals have an internal FIFO with a programmable watermark. Raising the watermark means the interrupt fires only when enough data has accumulated, cutting the rate proportionally.
- **Interrupt coalescing / batching.** If the peripheral can't DMA, accumulate events and service them in batches — e.g., let a timer-driven handler drain a hardware queue rather than taking an interrupt per event.
- **Deferring work out of the ISR.** Keep the ISR minimal (capture the data, clear the flag, signal a thread or work queue) so the *latency* per interrupt is small even if the rate is high. The heavy processing happens in a lower-priority context.

The trade-off to be explicit about is latency versus CPU load. Batching and DMA reduce CPU load but add latency between the event and when software sees it. For a control loop or a safety-relevant signal, that added latency may be unacceptable, so the design has to be driven by the deadline, not just by CPU percentage. I'd also watch for the failure mode where the ISR itself becomes the bottleneck — if interrupts arrive faster than the ISR can retire them, you get interrupt storms and missed events, and the fix is architectural (DMA/coalescing), not micro-optimization.

**Possible follow-ups:**
- How would you decide between DMA and a larger FIFO watermark if both are available?
- What would you monitor in the field to detect that an interrupt-rate assumption has been violated?

## Q2: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core principle is: never trust a single edge as proof that valid data exists. An edge is a *hint* that something may have happened; the data itself, or a status register, is the authority. So the design should separate "an edge occurred" from "valid data is present," and validate before acting.

Concretely, I'd approach it in layers:

- **Debounce/qualify in hardware where possible.** If the signal can be filtered with an RC network or a Schmitt-trigger input, that removes many glitches before firmware ever sees them. Firmware debouncing is a fallback, not the first choice, because it costs CPU and adds latency.
- **Validate against the peripheral's own status.** After an edge, read the data-ready/status bit or the data register itself and confirm it indicates fresh, valid data. If the status says "no new data," treat the edge as spurious and discard it. This is the most robust check because it uses the peripheral's ground truth.
- **Sanity-check the payload.** Even with a valid status, apply range/CRC/consistency checks to the data before using it. A glitch that happens to coincide with a stale-but-valid status bit should still be caught by payload validation.
- **Debounce in time if needed.** If glitches are frequent and the peripheral has no reliable status, a short qualification window (ignore edges within N µs of the last accepted one) can help — but this must be tuned against the real minimum inter-event spacing, or you'll drop legitimate events.

The important design decision is what to do with a rejected edge: log it (for diagnostics), count it (to detect a degrading signal), but do not let it propagate as a data event. And I'd make the validation logic a single, testable function so it can be unit-tested with synthetic glitch patterns rather than only discovered in the field.

**Possible follow-ups:**
- How would you distinguish a glitch from a genuine but very short data-ready pulse?
- If the peripheral has no status register at all, what other evidence could you use to validate an edge?

## Q3: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic "heisenbug" and the debugger's presence is itself the clue. Attaching a debugger changes several things simultaneously: it halts the core at breakpoints, it may slow or serialize execution, it can change timing (so races disappear), it may alter power state, and it can mask or expose certain faults. The first job is to figure out *which* of those differences is responsible, because they point to very different root causes.

My approach:

- **Characterize the difference.** Does the misbehavior disappear only when halted at a breakpoint, or also when merely connected but running free? If it's the former, it's likely a timing/race issue. If it's the latter, it could be power, clock, or debug-peripheral side effects.
- **Replace the debugger with non-intrusive instrumentation.** Use a GPIO toggled at key points, a spare UART, or a trace buffer (SWO/ETM if available) to observe behavior without halting the core. This preserves timing while giving visibility.
- **Look for the usual suspects for timing-sensitive bugs:** uninitialized variables that happen to be zero when the debugger resets memory, race conditions between ISR and thread, missing `volatile` on shared variables, and reliance on execution speed (e.g., a delay loop that's "long enough" only when the core isn't being slowed).
- **Check power and clock.** A debugger can hold the target in a state that changes supply or clock behavior. If the bug correlates with a power state (e.g., low-power mode, brownout), the debugger may be masking it.
- **Reproduce without the debugger using logging.** Add persistent logging (to flash or a ring buffer) that survives the event, then read it back after the fact. This is often the only way to catch a bug that only manifests at full speed.

The key discipline is to avoid "fixing" it by leaving the debugger attached or by adding a delay that happens to hide the race. The goal is to find the actual timing or state dependency and make the code correct regardless of execution speed.

**Possible follow-ups:**
- How would you use a trace buffer to catch a race that only happens at full speed?
- What code patterns most commonly cause "works with debugger, fails without" behavior?

## Q4: How would you approach designing a firmware module that must survive a brownout — where the supply voltage sags briefly but doesn't fully drop — without corrupting persistent state or producing a spurious reset?

**Answer:** A brownout is a window where the supply is below the reliable operating threshold but hasn't gone to zero. The danger is that the MCU may still be "running" but executing incorrectly — flash writes can corrupt, RAM can flip, and the core can behave unpredictably. So the design has two goals: *detect* the brownout early enough to act, and *protect* persistent state so that whatever happens, the device comes back to a known-good state.

Key elements:

- **Use the brownout detector / supply monitor, not just the reset pin.** Most MCUs have a brownout reset (BOR) or programmable voltage monitor (PVD) that can trigger an interrupt *before* the supply falls below the core's reliable operating voltage. Configure it to fire early, and treat that interrupt as "prepare for imminent loss of power."
- **Have a defined "safe state" to enter on brownout.** On the PVD interrupt, stop writing to flash, stop motor/peripheral activity that could be dangerous, and put persistent state into a consistent form. The window may be only microseconds, so this must be a short, pre-planned sequence — not a general shutdown routine.
- **Make persistent state crash-safe by design.** Use a journaling or double-buffered scheme with a commit marker: write the new record, then atomically flip a marker that says "this record is valid." If power is lost mid-write, the marker still points to the old valid record. Never overwrite the only copy of critical state in place.
- **Validate on boot.** After any reset, the firmware should check the integrity of persistent state (CRC, marker, version) and fall back to a known-good default or the last valid record if it's inconsistent. This turns "corrupted state" into "recoverable state."
- **Distinguish brownout from a real reset.** If the PVD fired, the boot code can read a status flag and know the reset was supply-related, which is useful for diagnostics and for deciding whether to re-run a calibration or re-initialize a peripheral.

The trade-off is between the cost of the protection (extra flash writes, a small amount of reserved space, a few microseconds of latency on the PVD interrupt) and the risk of corruption. For a medical device, the protection is essentially mandatory, because corrupted persistent state can mean wrong dosage limits or lost calibration.

**Possible follow-ups:**
- How would you test a brownout protection scheme without a programmable supply?
- What's the difference between a brownout detector and a watchdog, and why do you need both?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** I'd start by acknowledging the part they got right: `volatile` *does* tell the compiler not to cache the variable in a register or reorder accesses to it relative to other volatile accesses, so it's necessary for a shared flag between an ISR and a thread. The mistake is treating it as *sufficient*. `volatile` says nothing about atomicity, nothing about ordering relative to non-volatile accesses, and nothing about the fact that on a multi-core or pipelined system the write may not be visible to the other context when you expect. It's a compiler directive, not a synchronization primitive.

The concrete failure modes to walk through with them:

- **Non-atomic multi-byte access.** If the shared variable is larger than the native word size, or if the "flag" is actually a struct or a pointer, the reader can observe a torn value. `volatile` doesn't prevent that.
- **Ordering.** The compiler (and the CPU) can reorder a non-volatile write relative to the volatile flag. So the reader can see "flag set" before the data it's supposed to signal is actually written. This is the classic "publish data, then set flag" bug.
- **Lost updates.** If both sides read-modify-write the variable, `volatile` doesn't make that atomic; you can lose an update.

The right guidance is to use a proper synchronization primitive for the *handoff*, and reserve `volatile` for what it's actually for. Options, depending on the situation:

- **A single flag with a clear one-writer/one-reader discipline** can be made safe with an atomic type (`atomic_t` in Zephyr) or a memory barrier, plus a defined ordering (write data, then barrier, then set flag).
- **A message queue or ring buffer** is usually the better design: the ISR posts data, the thread consumes it, and the queue's own synchronization handles atomicity and ordering. This also decouples the two contexts and makes the data flow explicit.
- **A mutex or spinlock** if both sides genuinely need to share mutable state, though a mutex can't be taken in an ISR, so that constrains the design.

I'd frame it not as "your code is wrong" but as "here's the class of bug this invites, and here's a pattern that removes the whole class." Then I'd ask them to write a small test that exercises the handoff under load, so they can see the difference between "works in testing" and "correct by construction." The teaching goal is to move them from "it works" to "I can explain why it's correct."

**Possible follow-ups:**
- What's the difference between `volatile` and `atomic_t` in Zephyr, and when would you use each?
- How would you prove that a flag-based handoff is correct, rather than just observing that it works?
- If the ISR needs to pass a small amount of data (not just a flag) to the thread, what's the cleanest pattern?