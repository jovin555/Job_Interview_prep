# firmware — Day 81

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** The first step is to recognize that the ISR is doing too much work per event, not that the interrupt rate is inherently unmanageable. The goal is to make the ISR as short as possible — ideally just acknowledging the interrupt and moving data or a pointer into a queue — and defer everything else to a lower-priority context.

Concretely, I'd look at a few strategies. First, reduce per-event work in the ISR: if the peripheral supports it, switch from per-byte or per-sample interrupts to a DMA-driven transfer that fires one interrupt per block rather than per unit of data. That alone often collapses the interrupt rate by orders of magnitude. Second, if DMA isn't available, use a hardware FIFO on the peripheral and only interrupt when the FIFO crosses a threshold, so the ISR drains several items at once. Third, if the events are genuinely independent and frequent, use a counting or coalescing scheme — the ISR increments a counter or sets a flag, and a deferred context (a work queue item, a thread, or a bottom-half) processes the accumulated work. This trades latency for throughput, which is usually the right call when the CPU simply cannot keep up with per-event servicing.

The key design principle is to separate "capture" from "process." Capture must be fast and lossless; processing can be batched. I'd also instrument the system to measure actual ISR entry/exit time and interrupt rate, because "the ISR is the bottleneck" is a hypothesis that should be confirmed with data before restructuring. If the ISR is already minimal and the rate is still too high, the answer may be a hardware change — a faster MCU, a different peripheral mode, or offloading to a dedicated co-processor.

**Possible follow-ups:**
- How would you decide between a work queue and a dedicated thread for the deferred processing?
- What would you do if the deferred context also can't keep up, and data loss is unacceptable?

## Q2: How would you approach implementing a firmware module that must timestamp events with millisecond resolution across a device that sleeps for long periods, where the timestamp must remain monotonic and must not be corrupted by the sleep/wake transition?

**Answer:** The core problem is that the free-running counter used for millisecond timing typically stops or is not maintained in deep sleep, so a naive `k_uptime_get()`-style timestamp will either lose time or jump backward across a sleep/wake boundary. The design needs a persistent time base that survives sleep.

The usual approach is a two-part time base: a low-power, always-on counter (often the RTC, running off a 32.768 kHz crystal) that continues counting through sleep, plus a software offset that accounts for any time the RTC itself was not running (for example, if the RTC is also gated in the deepest sleep mode). On wake, the firmware reads the RTC, computes elapsed time since the last known-good timestamp, and advances a monotonic software counter. The critical detail is that the update must be atomic with respect to any code that reads the timestamp — otherwise a reader could observe a partially updated value. A seqlock or a critical section around the read-modify-write is appropriate.

I'd also guard against the RTC being reset or corrupted: store a "last known timestamp" in retained memory or a small backup register, and on boot, validate it against the RTC. If the RTC value is implausible (for example, it went backward), fall back to the retained value and flag the anomaly rather than silently producing a non-monotonic timestamp. For millisecond resolution specifically, I'd check whether the RTC tick rate actually supports it — a 1 Hz RTC cannot give millisecond resolution on its own, so you'd combine the RTC's coarse count with a high-resolution timer that runs while awake, and reconcile the two at each wake.

**Possible follow-ups:**
- How would you handle the case where the device resets unexpectedly, so the retained timestamp is stale?
- What accuracy trade-offs come with using the RTC versus a dedicated always-on timer?

## Q3: A junior engineer has written a driver that works reliably on the bench but uses a fixed `k_sleep` delay to wait for a peripheral to become ready after each command, rather than checking a status register or using an interrupt. How would you guide them?

**Answer:** I'd start by acknowledging that the code works and that the instinct to keep things simple is reasonable — fixed delays are easy to reason about and often "good enough" on a bench. Then I'd walk through why they're fragile in production, using concrete scenarios rather than abstract principles.

The main issues are: the delay is a guess that must cover the worst-case readiness time across all parts, temperatures, and supply voltages, so it's either too short (intermittent failures) or too long (wasted time and power, which matters in a battery device). It also blocks the calling thread, which in an RTOS means it can delay higher-priority work or, if called from an ISR, is simply illegal. And it hides the actual state of the peripheral, so when something does go wrong, there's no signal to diagnose.

The better pattern depends on the peripheral: if it has a status register or a data-ready pin, poll that with a bounded timeout rather than sleeping a fixed amount — this is both faster in the common case and safer in the worst case. If it has an interrupt, use it and let the thread block on a semaphore or event, which frees the CPU entirely. I'd suggest they implement the polling-with-timeout version first, since it's a small change and preserves their mental model, then move to interrupt-driven if the peripheral supports it.

I'd frame it as "make the wait event-driven instead of time-driven" and offer to pair on the first conversion so they see the pattern. The goal is to build the habit, not to rewrite their code for them.

**Possible follow-ups:**
- How would you choose a timeout value for the polling version, and what would you do if the timeout expires?
- What would you do if the peripheral has no status register and no interrupt — only a fixed delay is possible?

## Q4: How would you approach deciding what belongs in a bootloader versus what belongs in the application, for a device that must support field updates?

**Answer:** The guiding principle is that the bootloader should be as small and as simple as possible, because it's the one piece of code that must never fail — if it's broken, the device is unrecoverable in the field. Everything that can live in the application should live there, because the application can be updated and rolled back.

So the bootloader's job is narrow: verify the integrity and authenticity of the application image, select which image to boot (in a dual-bank scheme), perform the actual copy or bank switch if needed, and hand off control. It should not contain business logic, communication stacks beyond what's needed to receive an update, or anything that changes frequently. Integrity checking (CRC or hash) and signature verification belong in the bootloader because they gate whether the application is allowed to run at all. The rollback decision — "the new image failed to validate, so boot the old one" — also belongs there, since it must work even if the new application is completely broken.

What belongs in the application: the update client that downloads or receives the image, the logic that decides when to apply an update, any user-facing prompts, and the "commit" signal that tells the bootloader the new image has proven itself (for example, after a successful self-test or a period of stable operation). The application is also where you'd put version reporting, update scheduling, and communication with whatever backend delivers the image.

A useful test for the boundary: "If this code has a bug, can the device still be recovered?" If the answer is no, it belongs in the bootloader and must be reviewed and tested to a much higher standard. If the answer is yes, it belongs in the application where it can be fixed by an update.

**Possible follow-ups:**
- How would you handle the case where the bootloader itself needs a security fix?
- Where would you put the logic that decides whether a newly booted image is "good enough" to commit?

## Q5: How would you approach a situation where you discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules?

**Answer:** The first thing is to be honest and early about it — the worst outcome is to hide the problem and let it compound. I'd quantify the impact: what specifically is breaking, how many modules are affected, what's the cost of fixing it now versus shipping with it, and what's the risk of each path. That analysis is what turns "I made a mistake" into a decision the team can actually make.

Then I'd look for the smallest change that addresses the root cause rather than the symptom. Often the "design decision" is really a few concrete interfaces or assumptions, and you can introduce an abstraction layer or a compatibility shim that lets you fix the core issue without rewriting every caller at once. That buys time and reduces risk. If a full rework is genuinely necessary, I'd propose a phased approach: fix the highest-risk or highest-churn modules first, keep the system working at each step, and avoid a big-bang rewrite.

I'd also bring it to the team and the relevant stakeholders rather than deciding alone, because the schedule and risk trade-off is a shared call. I'd present options with estimates, not just the problem. And I'd be clear about what I'd do differently next time — for example, prototyping the risky interface earlier, or writing a short design note that surfaces assumptions for review before they harden.

The behavioral point is that owning a late-discovered design problem is normal in engineering; what matters is surfacing it early, framing it as a decision, and driving it to resolution without defensiveness.

**Possible follow-ups:**
- How would you decide whether to fix it now or ship with a known limitation and fix it in the next release?
- How would you keep the team's morale and trust intact while working through the rework?