# firmware — Day 55

## Q1: How would you approach designing a firmware module that must log diagnostic events to flash, where the log must survive a power loss mid-write and the flash has limited erase cycles?

**Answer:** The core problem is that a flash write is not atomic — a power loss partway through a page program can leave a partially written page with an indeterminate state, and a log that corrupts on power loss is worse than no log at all. I'd structure the storage as a circular log of fixed-size records, each with a header containing a sequence number, a length, and a CRC over the payload. On write, I'd program the record, then verify by reading it back and checking the CRC. On boot, I'd scan the log from the last known-good record forward, and treat the first record that fails CRC or has an implausible sequence number as the tail — everything after it is discarded. This makes the log self-healing: a torn write is simply the new tail.

For erase-cycle endurance, I'd avoid erasing on every record. Instead I'd erase whole sectors and write records sequentially within a sector until it's full, then move to the next sector in the ring and erase the oldest one only when the ring wraps. That amortizes one erase across many records. I'd also keep a small RAM buffer and flush in batches where the application allows, so a burst of events costs one write rather than many. The trade-off is that a power loss can lose the buffered events — so I'd flush immediately for events that matter for post-mortem analysis (faults, resets) and batch only routine telemetry.

A subtlety is wear leveling across the ring: if the device always writes the same small number of records and then idles, one sector takes all the wear. I'd either rotate the starting sector on each boot or track a write counter per sector and prefer the least-worn one. For a medical device, I'd also make the log region a separate partition from configuration and firmware, so a log corruption can never affect the code that boots.

**Possible follow-ups:**
- How would you distinguish a torn write from a genuinely corrupt record if both fail CRC?
- What would change if the log had to be readable by an external tool without the device's firmware?

## Q2: You're debugging a firmware issue where a device works correctly for days, then a peripheral driver starts returning errors that clear on reboot. How would you approach this?

**Answer:** A failure that only appears after long runtime and clears on reboot points at state that accumulates — something is not being reset, freed, or re-initialized. I'd start by narrowing whether the problem is in the driver's own state or in the system around it. First question: does the error correlate with a counter, a time, or an event count? If I can log the driver's internal state (error counters, retry counts, buffer indices, last status register value) and see it degrade gradually, that tells me it's accumulation rather than a one-shot bug.

Common culprits I'd check in order. One is a resource leak: a buffer, semaphore, or file descriptor acquired on each transaction but not released on an error path, so the pool slowly drains until allocation fails. Two is a counter or index that wraps or saturates — a sequence number that overflows, or a retry counter that never resets and eventually trips a threshold. Three is a hardware state that drifts: a peripheral FIFO that fills because a condition was missed once, or an error flag that latches and is never cleared, so every subsequent read reports the stale error. Four is a timing or clock issue — a reference clock that drifts with temperature, or a watchdog-adjacent timer that slowly loses sync.

My method would be to add instrumentation that captures the driver's state at the moment of failure, not just the fact of failure, and to run a soak test with that instrumentation. If I can reproduce it faster by stressing the specific path (higher transaction rate, injected errors, temperature), I'd do that. I'd also check whether a soft reset of just the peripheral — re-initializing it without rebooting the whole device — clears the error. If it does, that strongly implicates peripheral state rather than the CPU or memory, and it also gives me a candidate mitigation while I find the root cause.

**Possible follow-ups:**
- How would you decide whether a periodic peripheral re-initialization is an acceptable mitigation or a mask over a real bug?
- What instrumentation would you add without changing the timing behavior enough to hide the bug?

## Q3: How would you approach deciding whether a piece of firmware logic should run in an interrupt context, a deferred context (work queue or thread), or a low-priority background task?

**Answer:** The decision comes down to three properties: how much time the work takes, how deterministic its timing must be, and what it's allowed to block on. An ISR should do the minimum needed to acknowledge the hardware and capture the data that would otherwise be lost — read the status register, clear the flag, copy a byte or a sample into a buffer, and signal. Anything that can take unbounded time, allocate memory, take a mutex, or call into a subsystem that might block does not belong in an ISR, because it inflates interrupt latency for everything else and can deadlock against code that disables interrupts.

The middle tier — a work queue or a high-priority thread — is where I'd put work that must happen soon after the event but can tolerate a small, bounded delay: parsing a received message, running a control calculation, updating a state machine. This tier can block on kernel primitives, which is the main reason to move work here. The lowest tier — a background or idle-priority task — is for work with no timing requirement: logging, housekeeping, statistics, non-critical communication.

The criteria I'd apply explicitly: if the work must complete before the next interrupt of the same source, it may need to stay in the ISR or run at a priority above that source. If it must complete within a deadline but not before the next event, a deferred context with a known worst-case execution time is right. If it has no deadline, push it down. I'd also consider the cost of the handoff itself — posting to a work queue has overhead, and for a very high-rate event the handoff can cost more than the work. In that case, a small amount of work in the ISR plus a batched handoff (process N samples at once) is often the right compromise.

**Possible follow-ups:**
- How would you measure the actual interrupt latency and deferred-context latency to validate the split?
- What happens to your design if the deferred context's priority is lower than a task that can block it for a long time?

## Q4: A junior engineer has written a driver that works on the bench but uses a fixed delay to wait for a peripheral to become ready after each command, rather than polling a status register or using an interrupt. How would you guide them?

**Answer:** I'd start by acknowledging why the fixed delay feels safe — it's simple, it's deterministic in the sense that it always waits the same amount, and it works on the bench. The concern isn't that it's wrong today; it's that it's fragile in ways that won't show up until later. A fixed delay is a bet that the peripheral is always ready within that time, and that bet is made against the datasheet's worst case, the temperature range, the specific silicon revision, and the load on the system. If any of those change, the delay is either too short (intermittent failures that are hard to reproduce) or too long (wasted time that hurts responsiveness or power).

I'd walk them through the alternatives and when each is appropriate. Polling a status register with a timeout is the smallest change: it's still simple, it's deterministic in the sense that it returns as soon as the device is ready, and the timeout bounds the worst case so a stuck peripheral doesn't hang the system forever. That's usually the right first step. If the wait is long relative to the system's other work, an interrupt or a completion callback lets the CPU do something useful instead of spinning — but that adds complexity, so it's a trade-off, not a default.

The key teaching point is the timeout. A poll loop without a timeout is a hang waiting to happen; a fixed delay without a check is a silent failure waiting to happen. I'd ask them to add a bounded poll with a timeout and an error return, and to think about what the caller should do when the timeout fires — retry, report, or degrade. I'd also point out that the fixed delay hides the peripheral's actual behavior, so it makes debugging harder later: with a status check, you can log how long the device actually took and see when it's drifting.

**Possible follow-ups:**
- How would you choose the timeout value, and what would you do if the datasheet only gives a typical, not a worst-case, ready time?
- When would a fixed delay actually be the right choice?

## Q5: How would you approach a situation where you've inherited a firmware codebase with no tests, no documentation, and a reputation for being fragile, and you need to make a change to it?

**Answer:** The instinct to rewrite is usually wrong, and the instinct to just make the change and hope is also wrong. The realistic path is to make the change safely by first building just enough understanding and just enough safety net to know whether I've broken something. I'd start by mapping the system at the level I need: what are the entry points, what are the shared state variables, what are the timing-critical paths, and where does the code I'm about to touch sit relative to those. I don't need to understand everything — I need to understand the blast radius of my change.

Then I'd build a minimal safety net around that blast radius, not the whole system. That might be a host-side test harness for a pure function, a bench test that exercises the specific path, or simply a set of logged inputs and outputs captured before the change so I can compare after. The point is to have a way to detect regression, not to achieve full coverage. If the code is genuinely untestable because it's tangled with hardware, I'd look for the smallest seam I can introduce — a function pointer, a thin HAL — to make the part I care about testable without restructuring everything.

For the change itself, I'd make it as small and as reversible as possible, and I'd document what I learned as I go — not a full design doc, but notes on the invariants I discovered, the assumptions I had to make, and the parts I deliberately left alone. That documentation is often more valuable than the change, because it's the start of the map the next person needs. I'd also flag to the team the specific risks I found but didn't fix, so they're visible rather than buried.

The behavioral part is managing expectations. A fragile codebase with no tests is a known liability, and the right response is to make the change safely and to leave it slightly better than I found it — not to declare a rewrite or to pretend the fragility isn't there. If the change is risky enough that I can't make it safely in the time available, that's a conversation to have early, not a surprise at the end.

**Possible follow-ups:**
- How would you decide when the accumulated fragility justifies a targeted refactor versus continuing to patch?
- How would you get buy-in from a team that has normalized the fragility and sees your caution as slowing things down?