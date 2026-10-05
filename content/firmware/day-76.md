# firmware — Day 76

## Q1: How would you approach implementing a state machine where the same event can arrive from multiple sources (a user interface, a communication interface, and an internal timer), and the correct transition depends on which source sent it?

**Answer:** The core problem is that a bare event enum loses information the moment two sources can produce the same logical event. The fix is to make the event a composite: a source identifier plus an event code, rather than a single scalar. I'd define an event struct or a packed value that carries both, so the transition logic can discriminate on the pair.

From there, the design question is where the source-awareness lives. Two viable patterns:

- **Source in the event, handled in the transition table.** Each (state, source, event) tuple maps to a next state and an action. This keeps all policy in one place and is easy to review, but the table grows multiplicatively with the number of sources.
- **Source handled at the dispatch boundary.** Each source has its own ingress path that normalizes or tags the event before it reaches a shared state machine. The state machine then only sees events it cares about, and source-specific policy (e.g., "a UI stop is advisory, a comms stop is authoritative") is applied before the transition.

I'd lean toward the second when the sources have genuinely different semantics, because it keeps the state machine's transition table small and readable, and it localizes the "who is allowed to do what" rules where they're easiest to test. I'd lean toward the first when the sources are symmetric and the difference is purely informational.

Two things I'd insist on regardless of pattern:

1. **Single-threaded event processing.** All sources funnel into one queue, and one context drains it. If an ISR or a comms callback mutates state directly, you've reintroduced the race the state machine was supposed to eliminate.
2. **Explicit handling of unexpected (state, source, event) combinations.** The default case should not silently ignore — it should log or assert, because a silently dropped event in a medical device is a latent bug that surfaces months later.

I'd also make the source part of the event's identity in any logging or trace, so that when something goes wrong in the field you can reconstruct which path fired.

**Possible follow-ups:**
- How would you handle a case where the same source can legitimately send the same event twice in quick succession — do you deduplicate, or is that the state machine's problem?
- If the timer source fires while a comms event is mid-processing, how do you guarantee ordering, and does ordering even matter for your transitions?

## Q2: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the first instinct — "the debugger is masking it" — is usually right, but the mechanism matters. Attaching a debugger changes several things simultaneously: it halts and single-steps the core, it may disable or slow certain low-power modes, it can alter timing, and it often changes how the flash/RAM is accessed. I'd work through those systematically rather than guessing.

First, I'd characterize the difference. Does the misbehavior disappear entirely with the debugger attached, or just become rarer? Does it correlate with a specific operation — a flash write, a sleep entry, a peripheral init? If I can narrow it to one operation, the debugger's effect on that operation is the lead.

The usual suspects, roughly in order of how often they bite:

- **Timing-dependent races.** The debugger's halt/single-step changes instruction timing enough to hide a race between an ISR and a thread, or between two peripherals. A logic analyzer or a GPIO toggled at the suspect points is more honest than a debugger here, because it doesn't perturb the timing.
- **Low-power modes.** Many debuggers keep the debug clock or a peripheral alive, which prevents the device from entering the deepest sleep state. If the bug only appears in a sleep state the debugger is suppressing, that's the answer. I'd test by running standalone with a power profiler or by toggling a GPIO on sleep entry/exit.
- **Watchdog behavior.** Some debug configurations freeze the watchdog while halted. If the bug is a watchdog reset that the debugger is masking, standalone operation will show it.
- **Flash access / cache.** Debuggers sometimes change flash wait states or cache behavior. If the bug correlates with code execution from a particular region, this is worth checking.
- **Uninitialized memory.** The debugger may zero or leave RAM in a different state than a cold boot. A standalone cold boot with a known RAM pattern is the honest test.

My approach would be to reproduce standalone with instrumentation that doesn't perturb timing — GPIO toggles, a UART log at low priority, or a ring buffer in RAM that I dump after the fact. The debugger is for inspection, not for reproduction, once I suspect it's masking the bug.

**Possible follow-ups:**
- How would you distinguish a timing race from a low-power-mode issue if both are plausible?
- If the bug only reproduces once every few hours standalone, how do you get enough signal to debug it without spending days per iteration?

## Q3: How would you approach designing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** The first thing to establish is whether the interrupt rate is genuinely higher than the service rate, or whether the ISR is just doing too much work. Those are different problems with different fixes.

If the ISR is doing too much — parsing, logging, state updates, anything beyond acknowledging the peripheral and moving data — the fix is to shrink the ISR to the minimum: read the data register, push to a buffer, clear the flag, return. Everything else moves to a deferred context (a work queue, a thread, or a bottom-half). This is the standard top-half/bottom-half split, and it's usually enough.

If the interrupt rate genuinely exceeds what the CPU can service even with a minimal ISR, then interrupts are the wrong mechanism. Options:

- **DMA.** If the peripheral supports it, let DMA move data into a buffer and interrupt only on buffer completion or half-completion. This collapses thousands of interrupts into a handful. The trade-off is latency and buffer sizing — you need enough buffer to cover the worst-case service interval.
- **Polling in a dedicated high-priority thread.** Counterintuitive, but if the data rate is high and steady, a tight polling loop can be more efficient than interrupt entry/exit overhead. This only works if the thread can be scheduled reliably and nothing else needs the CPU during that window.
- **Hardware flow control or throttling.** If the peripheral supports it, back-pressure the source so it can't outrun the consumer. This is often the cleanest answer when the source is external.
- **Reducing the data rate.** Sometimes the honest answer is that the system is over-specified and the peripheral is being clocked faster than the application needs.

The decision hinges on the data's timing requirements. If the data is bursty, DMA with a large buffer is usually right. If it's continuous and the CPU genuinely can't keep up, the architecture is wrong and needs to change — no amount of ISR optimization fixes a fundamental throughput mismatch.

I'd also instrument the ISR entry/exit with a GPIO or a cycle counter early, because "the ISR is the bottleneck" is a hypothesis, not a diagnosis. Measuring it takes an afternoon and saves a week of guessing.

**Possible follow-ups:**
- How would you size the DMA buffer if the consumer's worst-case service interval is unknown?
- If the peripheral doesn't support DMA and polling isn't viable, what's your fallback?

## Q4: How would you approach deciding what belongs in a bootloader versus what belongs in the application, for a device that must support field updates?

**Answer:** The guiding principle is that the bootloader should be as small and as close to immutable as possible, because it's the one piece of code that must work even when everything else has failed. Every feature added to the bootloader is a feature that can brick the device if it has a bug.

The bootloader's non-negotiable responsibilities:

- **Verify the application image before jumping to it.** CRC or hash check, and ideally a signature check if the threat model warrants it. If verification fails, the bootloader must not jump.
- **Select which image to boot** in a dual-bank scheme, based on a validity flag or a boot counter.
- **Provide a recovery path** — a way to receive a new image even if the current application is corrupt. This might be a serial/USB DFU mode, a wireless update path, or both.
- **Handle the update protocol itself**, or at least the part that writes the new image to the inactive bank.

Everything else belongs in the application:

- **Application-level configuration** — the bootloader shouldn't know about sensor calibration or user settings.
- **Logging and diagnostics** — the application owns these; the bootloader can have a minimal fault log if it's needed for field diagnosis, but it shouldn't grow into a general logging system.
- **Business logic of any kind** — if it's not about getting a valid image running, it doesn't belong in the bootloader.

The tricky cases are the ones in between. A wireless update stack, for example, is large and complex — putting the whole thing in the bootloader bloats it and increases the attack surface. The common pattern is to put a minimal update receiver in the bootloader (enough to accept an image over a simple, robust protocol) and let the application handle the richer update experience (resumable downloads, progress UI, etc.), handing off to the bootloader only for the final write-and-verify step.

I'd also insist on a clear boundary in the memory map and a documented interface between the two — a shared struct or a fixed set of flash addresses for the handoff state. That interface is the contract, and it needs to be versioned so that a bootloader update doesn't break an older application or vice versa.

**Possible follow-ups:**
- How would you handle a bootloader update itself, given that a failed bootloader update is unrecoverable?
- If the application needs to trigger a bootloader entry (e.g., for a user-initiated update), how do you pass that intent across the boundary safely?

## Q5: A junior engineer has written a driver that works reliably on the bench but uses a fixed `k_sleep` delay to wait for a peripheral to become ready after each command, rather than checking a status register or using an interrupt. How would you guide them?

**Answer:** I'd start by acknowledging that the code works — that's real, and it's not nothing. The concern isn't that it's broken today; it's that a fixed delay encodes an assumption that will eventually be wrong. The delay is long enough on this bench, with this part, at this temperature. It won't be long enough on a slower part, a colder board, or a busier system, and when it fails it'll fail intermittently and be miserable to debug.

I'd frame it as a robustness question rather than a style preference, because that's what it actually is. The conversation I'd want to have:

- **What is the delay actually waiting for?** Usually the answer is "the peripheral to finish its internal operation." The datasheet almost always specifies a status bit or a ready signal for exactly this. If it does, the fix is to poll that bit with a timeout, or better, use the interrupt if one exists.
- **What's the worst-case timing?** If the datasheet gives a max, the delay should be at least that — but even then, a fixed delay wastes time in the common case and is fragile in the worst case. Polling with a timeout is strictly better: it's fast when the peripheral is fast and safe when it's slow.
- **What happens if the peripheral never becomes ready?** A fixed delay hides this — the code proceeds and reads garbage. A polled wait with a timeout can detect the failure and report it, which matters enormously in a medical device.

I'd suggest they implement the polled version and compare, so they can see the improvement themselves rather than taking my word for it. If the peripheral genuinely has no ready signal and the datasheet only gives a timing spec, then a delay is defensible — but it should be a named constant tied to the datasheet value, with a comment explaining why, not a magic number.

The broader point I'd want to land is that "it works on the bench" is the beginning of the conversation, not the end. The bench is the easiest environment the code will ever run in.

**Possible follow-ups:**
- How would you handle a peripheral whose ready signal is unreliable — it sometimes asserts before the data is actually valid?
- If the delay is genuinely required by the hardware, how would you make it robust to temperature or voltage variation?