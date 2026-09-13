# firmware — Day 54

## Q1: How would you approach implementing a state machine where the same event can arrive from multiple sources (a user interface, a communication interface, and an internal timer), and the correct transition depends on which source sent it?

**Answer:** The core problem is that a state machine driven purely by an event enum loses information about provenance, so two logically different situations collapse into the same transition. The cleanest approach is to make the event a small struct rather than a bare enum: an event type plus a source field plus any payload. The transition logic then has the full context to decide whether, say, a "start" from the UI should be honored while a "start" from the remote interface should be rejected because the device is in a state where remote initiation is not permitted.

I would keep the state machine itself as a pure function — given current state and an event, return the next state and any actions to perform — with no I/O, no globals, and no direct hardware access. That makes it trivially unit-testable by feeding event sequences and asserting on state and emitted actions. Actions get returned as a small list or a callback table rather than executed inline, so the caller controls when side effects happen and the state machine stays deterministic.

For the multi-source aspect specifically, I would normalize events at the boundary: each source has a thin adapter that translates its raw input into the canonical event struct, tagging the source. This keeps source-specific quirks (debouncing a button, parsing a packet, handling a timer expiry) out of the state machine. If the same event from different sources should be treated identically, the source field is simply ignored in that transition; if it matters, it is available. I would also guard against reentrancy — if an event handler can trigger another event synchronously, queue it rather than recursing, so the state machine processes one event at a time.

**Possible follow-ups:**
- How would you handle an event that arrives while the state machine is mid-transition, and the new event is only valid in the state you are about to leave?
- Would you log every event and transition, and if so, how would you keep the log from becoming a performance or storage problem on a constrained device?

## Q2: How would you approach deciding what belongs in a bootloader versus what belongs in the application, for a device that must support field updates?

**Answer:** The guiding principle is that the bootloader should be as small and as close to immutable as possible, because it is the one piece of code that must never fail — if it is broken, the device is bricked with no software recovery path. So I would put in the bootloader only what is strictly required to: verify an image, select which image to run, and jump to it. Everything else — the update protocol, the transport, the decision of when to update, the UI for triggering an update — belongs in the application, which can be updated and which has a fallback if it misbehaves.

Concretely, the bootloader needs image validation (a CRC or, better, a cryptographic signature check), a way to determine which bank is valid and which is the intended boot target, and a minimal recovery path if no valid image exists. It should not contain a network stack, a filesystem, or complex parsing logic, because every line of code there is a line that cannot be fixed in the field. The application handles receiving the image, writing it to the inactive bank, marking it as "pending verification," and then triggering a reset. The bootloader's job on the next boot is simply to see the pending flag, validate the new image, and either boot it or fall back.

A subtle but important point is the "trial boot" pattern: the bootloader boots the new image once, but the application must confirm it is healthy (by clearing a flag) within some window. If the device resets before confirmation — say the new image crashes on startup — the bootloader sees the flag still set and reverts to the known-good bank. This gives rollback without the bootloader needing to understand *why* the new image failed. I would also keep the bootloader's own update path separate and rarely used, ideally requiring a deliberate, harder-to-trigger mechanism, since a failed bootloader update is the one scenario with no software recovery.

**Possible follow-ups:**
- How would you protect the bootloader from being partially overwritten if power is lost during a bootloader update?
- What would you put in the bootloader to help diagnose a field failure, given that it has no easy way to report anything?

## Q3: How would you approach debugging a firmware issue that only reproduces after the device has been running for many hours, where the symptom is a gradual degradation rather than a hard failure?

**Answer:** Gradual degradation over hours points away from logic bugs and toward something accumulating or drifting: a slow memory leak, a counter that wraps or saturates, a resource that is acquired and not released, a thermal effect, or a timing drift. The first move is to instrument rather than guess. I would add lightweight, low-overhead telemetry — free heap or stack high-water marks, a count of allocated-but-not-freed objects, the value of any long-running counters, and a periodic timestamp — logged at a slow rate so the logging itself does not perturb the system. The goal is to see *what* changes monotonically over the hours before failure.

If the symptom is memory-related, I would track allocation and free counts per pool or per module, not just total free memory, because a leak of small fixed-size blocks can hide behind a healthy-looking total. If it is timing-related, I would log the actual period of a known periodic task and watch for drift. If it is thermal, I would correlate the degradation with a temperature reading if one is available, or with time-under-load if not.

The hard part is reproduction time. I would try to compress it: run the device at elevated temperature, at higher load, or with a stress harness that exercises the suspect path far more frequently than production would. If the failure is a hard fault, I would ensure a fault handler captures the faulting context — program counter, link register, stack contents — to a non-volatile location so it survives the reset and can be read afterward. A crash that only happens after eight hours is far more tractable if the device tells you exactly where it died rather than requiring you to be watching when it happens.

**Possible follow-ups:**
- How would you distinguish a genuine memory leak from fragmentation, given that both can cause an eventual allocation failure?
- If the degradation correlates with uptime but you cannot find any accumulating resource, what else would you suspect?

## Q4: A junior engineer has written a driver that works correctly but uses a fixed `k_sleep` delay to wait for a peripheral to become ready after each command, rather than checking the peripheral's status. How would you guide them?

**Answer:** I would start by acknowledging that the code works and that fixed delays are a legitimate technique in some situations — the concern is not that delays are always wrong, but that a fixed delay encodes an assumption about the hardware that is invisible and unverified. The delay is a guess: it is long enough on this board, at this temperature, with this part. If any of those change, the code silently breaks, and the failure mode is intermittent and hard to trace because nothing in the code says "I am assuming the peripheral is ready after 2 ms."

The better pattern is to poll the status register with a timeout: wait for the ready bit, but give up after a bounded time and return an error. This is still simple — it is a loop with a deadline — but it is self-documenting about what it is waiting for, it adapts to the actual hardware response time instead of a guessed worst case, and it fails loudly instead of proceeding on a false assumption. The timeout value is the only remaining guess, and it can be generous because it is only hit on a genuine fault, not on every transaction.

I would frame it as a question rather than a correction: "What happens if the peripheral is slower than expected here?" and let them reason to the answer. If they are concerned about the polling loop burning CPU, that is a fair point and worth addressing — the loop can yield, or the wait can be moved to a deferred context, or an interrupt can be used if the peripheral supports it. But the fix for "polling wastes CPU" is not "sleep a fixed amount"; it is "wait for the actual condition, in a way that does not block unnecessarily." I would also point out that a fixed delay makes the driver's timing behavior opaque to anyone tuning system performance later, whereas an explicit wait-for-ready is easy to reason about.

**Possible follow-ups:**
- How would you choose the timeout value, and what would you do if the peripheral legitimately takes longer than the timeout under some conditions?
- If the peripheral has no status register to poll, what options remain?

## Q5: How would you approach a situation where you discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules?

**Answer:** The first thing is to be honest and early about it rather than hoping it can be papered over. A design decision that is causing problems across several modules tends to get worse, not better, as more code is built on top of it, so the cost of changing it generally grows with time. I would quantify the problem concretely — what specifically is breaking, how often, and what is the workaround cost — so the decision to rework is based on evidence rather than a vague sense that something is wrong.

Then I would lay out the options honestly: fix it now with the associated rework, work around it and accept the ongoing cost, or defer it with a clear trigger for revisiting. Each has a real cost, and the right answer depends on where the project is, what the release commitments are, and how much the problem actually affects correctness or safety versus just being unpleasant. For a medical device, anything affecting correctness or the ability to demonstrate compliance moves toward "fix it now" regardless of schedule pressure.

If the decision is to rework, I would do it incrementally rather than as a big-bang rewrite: introduce the new approach alongside the old, migrate one module at a time with tests at each step, and keep the system working throughout. This limits the blast radius and makes it possible to stop and reassess if the rework turns out to be larger than expected. I would also communicate clearly with the people affected — other engineers whose modules depend on the change, and whoever owns the schedule — because a late design change that surprises people is far more damaging than one that is flagged and planned.

**Possible follow-ups:**
- How would you decide whether the rework is worth it if the project is close to a release and the problem is annoying but not incorrect?
- If you decide to work around it, how would you make sure the workaround does not quietly become permanent technical debt that no one remembers to revisit?