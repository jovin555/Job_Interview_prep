# firmware — Day 64

## Q1: How would you approach designing a firmware module that must detect and recover from a peripheral that has silently stopped responding — no error flag, no interrupt, it just stops producing data — without relying on the peripheral's own status reporting?

**Answer:** The core problem is that the peripheral's own health reporting is untrustworthy in this failure mode, so the detection has to come from *outside* the peripheral. I'd treat it as a liveness problem rather than an error-handling problem.

The primary mechanism is a data-freshness watchdog: the module records a timestamp each time valid data arrives, and a supervisory context (a low-priority thread, a timer callback, or a hardware watchdog fed conditionally) checks whether that timestamp has gone stale relative to the expected data rate. The threshold should be generous enough to absorb normal jitter and retries — typically several multiples of the nominal period — but tight enough to catch a real stall before it affects the user-visible function. Crucially, the freshness check must be driven by an independent time source, not by the same peripheral or bus that may have hung.

On detection, recovery should be staged rather than a blunt reset. First attempt a soft recovery: re-initialize the peripheral, re-run its configuration sequence, and verify with a known-good transaction (e.g., reading a device ID register or a status register with a known value). If that fails, escalate to a bus-level recovery — for I2C that often means manually clocking out a stuck slave or issuing a bus-clear sequence; for SPI it may mean toggling chip select and re-arming the peripheral. Only if those fail would I consider resetting a larger subsystem, and I'd avoid a full device reset unless the peripheral is safety-critical and there's no other path.

Two design points matter for correctness. First, the recovery must be idempotent and safe to run while other threads may be mid-transaction — so the peripheral needs a lock or ownership model, and recovery should quiesce other users first. Second, the module should expose the stall and recovery events as diagnosable state (counters, last-good timestamp, recovery attempts) so that field failures can be analyzed rather than just silently papered over. For a medical device, I'd also want the degraded state to be visible to the application layer so it can decide whether to continue with reduced functionality or alert the user.

**Possible follow-ups:**
- How would you choose the staleness threshold without either missing real stalls or triggering false recoveries during normal bus contention?
- If the peripheral is shared between a safety-critical path and a non-critical path, how does that change your recovery strategy?

## Q2: You're implementing a circular buffer shared between an ISR that writes samples and a task that reads them. How would you handle the case where the reader falls behind and the writer would overwrite unread data?

**Answer:** The first decision is a policy decision, not a code decision: when the writer catches the reader, do you drop the *oldest* data (overwrite) or the *newest* data (reject the write)? That choice should be driven by what the data is for. For a control loop, the freshest sample matters most, so overwriting old data is usually right. For an audit or diagnostic log, losing the oldest entries may be unacceptable, so you'd reject new writes and set an overflow flag instead. For a medical monitor, you generally want to preserve the most recent clinically relevant window and clearly flag that a gap occurred, rather than silently presenting a continuous-looking stream.

Mechanically, the classic lock-free single-producer/single-consumer ring works well here: a head index written only by the ISR, a tail index written only by the reader, both sized to a power of two so index wrapping is a mask rather than a modulo. The subtlety is that the reader must read head exactly once into a local, and the writer must read tail exactly once, to avoid a torn view if the other side updates mid-check. Memory barriers or `volatile`-qualified indices (with the right ordering semantics for the target) are needed so the compiler and CPU don't reorder the data write relative to the index update.

For the overflow case specifically, I'd make the behavior explicit and observable. The writer, on detecting that advancing head would collide with tail, either advances tail (overwrite mode) or drops the sample and increments an overflow counter (reject mode). Either way, the reader should be able to detect that a discontinuity occurred — for example, by comparing a sequence number or by checking the overflow counter — so downstream processing doesn't treat a gap as continuous data. If the application can tolerate it, a "watermark" or hysteresis approach also helps: once you've overflowed, keep a small margin so you don't thrash between full and not-full.

I'd also size the buffer from the worst-case burst, not the average rate: if the reader can be delayed by a flash write or a scheduling hiccup, the buffer must absorb that delay plus margin. And I'd instrument it — high-water mark, overflow count, and worst-case reader latency — because those numbers tell you whether the sizing assumption is actually holding in the field.

**Possible follow-ups:**
- How would you verify the ring buffer is correct under concurrency without relying on luck during testing?
- If the reader occasionally needs to process a burst larger than the buffer, how would you restructure the design?

## Q3: How would you approach deciding what belongs in a bootloader versus what belongs in the application, for a device that must support field updates?

**Answer:** The guiding principle is that the bootloader should be as small, simple, and hard to change as possible, because it's the one piece of code that must never fail — if it's broken, the device is unrecoverable in the field. Everything that can change over the product's life, or that carries risk if it changes, belongs in the application.

Concretely, the bootloader owns: the entry decision (which image to boot), image validation (signature/CRC/hash checks), the update application mechanism (writing a new image to the inactive bank, verifying it, and marking it bootable), and rollback logic if the new image fails to validate or fails to confirm itself. It should also own any minimal recovery path — for example, a way to enter update mode if the application is corrupt. It should *not* own product features, communication stacks beyond the minimum needed to receive an image, or anything that would grow its attack surface or its code size.

The application owns everything else, including the decision to *initiate* an update, the protocol for transferring the image (which can be a full network stack), and the "confirm I booted successfully" handshake back to the bootloader. A common pattern is a two-stage confirmation: the bootloader boots the new image in a "tentative" state, the application runs a self-test and then writes a confirmation flag, and if the bootloader ever sees a tentative image without confirmation (e.g., after a reset), it rolls back to the known-good bank.

The boundary is also a security boundary. If there's a secure boot chain, the bootloader holds the root of trust and verifies the application's signature; the application may in turn verify its own resources. Keeping that chain minimal in the bootloader reduces the code that must be audited and frozen.

A practical test I'd apply: "If this code needs to change in a year, can it change without touching the bootloader?" If the answer is no, it probably belongs in the application. The exception is anything required to *recover* from a failed application — that has to live in the bootloader by definition.

**Possible follow-ups:**
- How would you handle the case where the bootloader itself needs a field update?
- What's the minimum set of validation checks you'd insist on before booting a new image, and why?

## Q4: A junior engineer has written a driver that works reliably on the bench but uses a fixed `k_sleep` delay to wait for a peripheral to become ready after each command, rather than checking a status register or using an interrupt. How would you guide them?

**Answer:** I'd start by acknowledging what's right about their instinct: a fixed delay *is* simple, and on the bench it works. The problem isn't that it's wrong in the happy path — it's that it's wrong in three ways that don't show up on the bench.

First, it's not actually deterministic in the way it looks. The delay has to be sized for the *worst-case* readiness time across all units, temperatures, and supply voltages. If you size it for the typical case, you get intermittent failures in the field; if you size it for the worst case, you've added latency to every transaction, which may violate the system's timing budget. Either way, you've traded a real, measurable quantity (the peripheral's status) for a guess.

Second, it blocks the calling thread. In an RTOS, a `k_sleep` in a driver means the thread is unavailable for that whole window, which can starve other work or push a higher-priority task past its deadline. Even if the delay is "short," it's unbounded from the system's perspective.

Third, it hides errors. If the peripheral never becomes ready — because it's hung, misconfigured, or the bus is stuck — a fixed delay just proceeds and the failure surfaces later, far from its cause, as corrupted data or a confusing downstream error. A status check or interrupt lets you detect and report the failure at the point it happens.

The better pattern depends on the peripheral. If it exposes a ready/busy status bit, poll it with a bounded timeout — not an infinite loop — and return an error if the timeout expires. If it can raise an interrupt when ready, use that and let the thread sleep on a semaphore or completion, which is both more efficient and more responsive. In Zephyr, that's typically a `k_sem` or `k_poll` on the peripheral's IRQ. The key is that the wait is *event-driven* with a timeout, not *time-driven*.

I'd frame the guidance as: "The delay is a symptom of not knowing when the peripheral is ready. Let's find out what the peripheral actually tells us, and use that." Then I'd pair with them to add the status check or interrupt, add a timeout, and add a test that forces the slow/failed case so the fix is actually verified rather than assumed.

**Possible follow-ups:**
- How would you choose the timeout value, and what should happen when it expires?
- What if the peripheral genuinely has no status bit and no interrupt — how would you handle it then?

## Q5: How would you approach a situation where you discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules?

**Answer:** The first thing I'd do is separate the *technical* question from the *project* question, because they have different answers and conflating them leads to bad decisions.

Technically, I'd quantify the problem before proposing anything. What exactly is failing or becoming unmaintainable? Is it a correctness issue, a performance issue, or a maintainability issue? How much rework is actually required — is it truly "several modules," or is it one interface that several modules happen to call? Often the blast radius is smaller than it first appears once you map the actual dependencies. I'd also look for a containment strategy: can the problematic decision be isolated behind an interface so that the rest of the system doesn't have to change, even if the implementation does? That's frequently the difference between a two-week fix and a two-month rewrite.

On the project side, I'd bring it to the team early rather than sitting on it, and I'd bring options, not just a problem. Typically there are three: fix it now (costs schedule, removes the risk), work around it (ships on time, carries the risk forward), or schedule it for a defined later point (e.g., after the current milestone). Each has a cost, and the decision is a risk-management call that the team lead or product owner should make with full information — not something I'd decide unilaterally, and not something I'd hide.

I'd also be honest about my own role in it. Owning the decision means owning the communication of it, without over-apologizing or being defensive. The useful framing is: "Here's what we know now that we didn't know then, here's the impact, here's what I recommend, and here's what I need from you to decide."

Finally, I'd capture the lesson in a way that's useful rather than punitive — for example, an architecture note or a design review checkpoint that would have surfaced the issue earlier. The goal isn't to relitigate the original decision; it's to make the next one better.

**Possible follow-ups:**
- How would you decide between a containment strategy and a full rework if the schedule is tight?
- If the team decides to work around it, how would you make sure the risk is tracked and doesn't get forgotten?