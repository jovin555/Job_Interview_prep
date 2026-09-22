# firmware — Day 63

## Q1: How would you approach designing a firmware module that must operate correctly across a brownout event — where the supply sags briefly but doesn't fully drop — without corrupting persistent state or producing a spurious reset?

**Answer:** The core problem is that a brownout is a window where the MCU may still be executing but its behavior is no longer guaranteed: flash writes can partially complete, RAM contents may become unreliable at the margins, and the brownout detector (BOD) may or may not trip depending on how the supply recovers. The design has to assume the worst case — that the CPU keeps running through a region where its guarantees don't hold.

The first line of defense is the hardware/configuration layer. I'd configure the BOD threshold above the minimum operating voltage of the MCU and all peripherals that must stay coherent, and make sure the BOD is set to *reset* rather than *interrupt* if the goal is fail-safe behavior — an interrupt-based BOD can be useful for a controlled shutdown, but only if there's enough energy budgeted (bulk capacitance) to complete that shutdown. That energy budget is a hardware conversation, not a firmware one, but firmware has to respect it: if the hold-up time is, say, a few milliseconds, the shutdown routine must be written to finish well inside that.

For persistent state, the key principle is that no single write should ever leave storage in an ambiguous state. That means either a journaling/atomic-update scheme (write new record to a spare slot, then commit a pointer or CRC; the old record remains valid until the commit succeeds) or a dual-copy scheme with a validity marker. On a brownout mid-write, the worst case is a torn record — the recovery logic on next boot must be able to detect that and fall back to the last known-good copy. I'd also avoid doing flash writes at all when the supply is marginal: if the firmware has any visibility into supply health (an ADC on the rail, a comparator, a fuel gauge), it should defer non-critical writes until the supply is comfortably in range.

For spurious resets, the concern is the opposite failure mode: the device resets but the application treats it as a normal boot and re-initializes state that should have been preserved, or worse, re-runs a calibration that was mid-flight. The reset cause register should be read early and logged, and the boot path should distinguish power-on reset from brownout reset from watchdog reset. A brownout reset during a critical operation should trigger a specific recovery path, not the generic one.

Finally, I'd want a way to test this. A programmable supply that ramps down and back up at controlled rates, combined with firmware instrumentation that logs reset cause and the state of persistent storage on each boot, lets you characterize the actual behavior rather than assuming it. The failure modes here are exactly the kind that only show up in the field, so building a repeatable bench test is worth the effort.

**Possible follow-ups:**
- How would you decide between a BOD-triggered controlled shutdown and a BOD-triggered immediate reset for a given product?
- If the device has no way to sense the supply rail directly, what other signals could you use to infer that a brownout is imminent?

## Q2: How would you approach implementing a firmware module that must timestamp events with millisecond resolution across a device that sleeps for long periods, where the timestamp must remain monotonic and must not be corrupted by the sleep/wake transition?

**Answer:** The hard part isn't generating a millisecond tick — it's maintaining a coherent time base when the CPU is off and only a low-power counter (RTC, LP timer, or a wake-up counter) is running. The design has to separate "wall time" from "monotonic uptime," because they have different requirements and different failure modes.

For monotonicity, the cleanest approach is a single 64-bit software counter that is only ever incremented, never reset except at cold boot. The low-power hardware counter provides the sub-second resolution; the software layer extends it to 64 bits by tracking overflows. On each wake, the firmware reads the hardware counter, computes the delta since the last read (handling wraparound), and adds it to the software counter. The critical detail is that the read-and-extend operation must be atomic with respect to any other code that reads the timestamp — otherwise a reader can observe a torn 64-bit value. On a 32-bit MCU, that means either a seqlock-style read (read high, read low, re-read high, retry if high changed) or a short critical section.

For the sleep/wake transition specifically, the danger is that the hardware counter's behavior across sleep isn't what you assume. Some low-power counters stop in certain sleep modes; some continue but with reduced accuracy; some have a wake-up latency that means the first read after wake is stale. The firmware should read the counter *after* the wake-up sequence has completed and the clock is stable, not before. If the counter is known to have a wake-up settling time, that has to be accounted for — either by waiting for a status bit or by budgeting the known error into the timestamp.

Corruption across sleep is usually a symptom of the counter being re-initialized on wake, or of the software extension logic running before the hardware counter is valid. I'd structure the wake path so that the very first thing it does is capture the hardware counter into a shadow register, then do everything else. That way, even if a later part of the wake path resets or reconfigures the counter, the captured value is safe.

For wall-clock time (if the device needs it), the RTC provides seconds and the monotonic counter provides the sub-second offset. The two are reconciled at boot and whenever the RTC is set. The monotonic counter should never be adjusted backward — if the RTC is corrected, that's a separate offset applied at read time, not a mutation of the monotonic base.

I'd also want a way to detect and log anomalies: if the delta between two consecutive reads is implausibly large or negative, that's a signal that something went wrong in the sleep transition, and it should be recorded rather than silently absorbed.

**Possible follow-ups:**
- How would you handle the case where the low-power counter's frequency drifts with temperature, and the timestamp needs to stay accurate over days?
- What's the trade-off between using a hardware RTC with a battery backup versus relying on the MCU's low-power counter across sleep?

## Q3: A junior engineer has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** This is a really common misconception, and it's worth correcting carefully because the engineer's reasoning isn't wrong about what `volatile` does — it's wrong about what it's sufficient for. `volatile` tells the compiler "don't cache this in a register, re-read it every time." That's necessary for an ISR-shared variable, but it's not sufficient for correctness on most modern MCUs.

The gaps are: first, `volatile` says nothing about atomicity. If the shared variable is wider than the machine's natural word size, or if the thread does a read-modify-write (increment, compare-and-swap, bit set), the operation can be interrupted mid-way and the ISR can observe or produce a torn value. Second, `volatile` says nothing about ordering with respect to *other* memory accesses. The compiler and the CPU can reorder non-volatile accesses around a volatile one, which means a flag can appear set before the data it's supposed to guard is actually visible. Third, on multi-core or DMA-coherent systems, `volatile` doesn't insert memory barriers, so cache coherency and store buffers can hide the write from the other context.

The right guidance is to introduce a proper synchronization primitive. For a simple flag or counter, an atomic type with explicit memory ordering (e.g., C11 `_Atomic` with `memory_order_acquire`/`release`, or the RTOS's atomic API) is the minimal correct fix. For anything more complex — a buffer, a queue, a state structure — the answer is a lock-free ring buffer with acquire/release semantics, or a proper mutex if the ISR can't take a mutex (in which case a critical section or a lock-free design is needed). The key teaching point is that the choice of primitive should be driven by *what invariant is being protected*, not by "make the compiler not optimize it."

I'd also point out that the code "works in testing" is exactly the expected outcome — these bugs are timing-dependent and often only manifest under specific compiler optimization levels, specific interrupt timing, or on a different core. So the fact that it passes tests is not evidence of correctness; it's evidence that the test conditions didn't hit the window. That's worth internalizing as a general principle.

The way I'd frame it to the engineer: "You're right that `volatile` is necessary here. The question is whether it's sufficient. Let's look at what invariant this variable is protecting and whether the current code actually guarantees it under all interleavings." That keeps it collaborative rather than a correction, and it builds the habit of reasoning about interleavings rather than about compiler behavior.

**Possible follow-ups:**
- How would you decide between a lock-free approach and a critical section for a given ISR/thread shared variable?
- What's the difference between `volatile` and an atomic with `memory_order_relaxed`, and when would each be appropriate?

## Q4: How would you approach deciding what belongs in a bootloader versus what belongs in the application, for a device that must support field updates?

**Answer:** The guiding principle is that the bootloader should be as small and as simple as possible, because it's the one piece of code that can never be updated in the field (or if it can, updating it is the highest-risk operation in the system). Everything that can live in the application should, because the application is what gets updated and what gets the benefit of bug fixes.

That said, there's a set of responsibilities that *must* be in the bootloader because the application can't be trusted to perform them on itself. The bootloader owns: the decision of which image to boot (including rollback logic if the new image fails validation), the image validation itself (CRC, signature, version checks), the actual flash programming of the new image, and the minimal communication path needed to receive an image when the application is not running or is not trusted. It also owns the recovery path — if the application is corrupt or fails to validate, the bootloader must be able to enter a known-good state and accept a new image.

The application owns everything else: the normal communication stack, the user interface, the decision to *initiate* an update, the download of the image into a staging area (if the bootloader's receive path is too limited), and the post-update verification that the new image is functioning. The application can also own the "commit" decision — marking the new image as good after it has run successfully for some period — which is a common pattern for rollback safety.

The boundary is usually drawn at the point where the application can no longer be trusted. If the application is running and healthy, it can do the work. If it's not, the bootloader has to. So the bootloader's job is to handle the cases where the application is absent, corrupt, or has explicitly handed control over.

There are practical constraints that push the boundary in one direction or the other. Flash size is the obvious one — a bootloader that includes a full TCP/IP stack and a TLS implementation is no longer small. Security is another: if the bootloader must verify signatures, it needs the crypto primitives, which adds size and complexity. And the update transport matters: if the device can only be updated over a link that requires a complex stack, either the bootloader carries that stack (large, risky) or the application downloads the image and hands it to the bootloader (smaller bootloader, but the application must be running to receive the update).

My default would be: bootloader does validation, selection, programming, and a minimal recovery transport (often just a serial or USB DFU path). Application does the normal update flow, including downloading over the production transport, and hands the validated image to the bootloader. That keeps the bootloader small enough to audit and simple enough to trust, while still allowing the application to be updated over whatever link the product actually uses.

**Possible follow-ups:**
- How would you handle the case where the application is running but the update transport is only available in the bootloader?
- What's the trade-off between a bootloader that can update itself and one that is permanently fixed?

## Q5: How would you approach a situation where you've inherited a firmware module with no tests, no documentation, and a reputation for being fragile, and you need to make a change to it?

**Answer:** The first instinct is to make the change as surgically as possible and get out — but that's usually the wrong move, because the module's fragility means a surgical change is likely to break something in a way you won't detect until it's in the field. The right approach is to spend a bounded amount of time building enough understanding and enough safety net to make the change confidently, and to be explicit with stakeholders about that cost.

I'd start by characterizing the module's actual behavior rather than its intended behavior. That means reading the code carefully, but also instrumenting it: adding logging at entry and exit points, at state transitions, at error paths, and running it through its normal operating scenarios to see what it actually does. The goal is to build a mental model that matches reality, not the documentation that doesn't exist.

Then I'd build a test harness around it — not a comprehensive test suite, but enough tests to pin down the behavior I'm about to change and the behavior I'm afraid of breaking. The harness might be host-based (compile the module for the development machine with stubs for hardware dependencies) or target-based (run on real hardware with a scripted stimulus). Host-based is usually faster to iterate on and catches logic errors; target-based catches timing and hardware interaction issues. Ideally both, but if I have to pick one, I'd pick the one that exercises the failure modes I'm most worried about.

The tests I'd write first are the ones that capture the *current* behavior, even if that behavior is wrong. The point is to have a regression baseline: if my change alters behavior in a way I didn't intend, the test fails and I know. Once I have that, I can make the change, and I can also start fixing the fragility — but incrementally, with each fix backed by a test.

I'd also look for the specific sources of fragility. Common ones: shared global state, implicit ordering dependencies between functions, error paths that aren't exercised, assumptions about timing or hardware state that aren't documented, and code that's been patched many times without refactoring. Identifying these tells me where to be most careful and where to add defensive checks.

Finally, I'd communicate the situation. If the change is small and the risk is low, I might just do it with a test around the specific path. If the module is central and the change is significant, I'd flag that the work includes building a safety net, and that the schedule should reflect that. Trying to hide the cost of dealing with legacy code is how you end up shipping a regression.

**Possible follow-ups:**
- How would you decide when to stop adding tests and just make the change?
- What would you do if the module's behavior is so timing-dependent that a host-based test harness can't reproduce the relevant conditions?