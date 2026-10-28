# firmware — Day 99

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt rate is high enough that servicing every interrupt individually would consume an unreasonable share of CPU time?

**Answer:** The first step is to quantify the problem rather than assume it: measure the actual ISR entry/exit overhead plus the minimum work per interrupt, multiply by the interrupt rate, and compare that against the CPU budget. If servicing every interrupt individually would eat, say, 40% of the core, that's the number that drives the design decision.

The standard remedy is to decouple the interrupt from the work. Keep the ISR as short as physically possible — acknowledge the source, move the data or status into a buffer, and return — and let the expensive part happen in a deferred context. For a high-rate data source, DMA is usually the right answer: configure the peripheral to write directly into a ring buffer and generate an interrupt only on half-transfer and full-transfer events (or on a watermark), so the interrupt rate drops by the DMA burst length. The ISR then just advances a pointer and signals a thread or work item.

If DMA isn't available or the peripheral doesn't support it, coalesce in the ISR: read multiple samples per interrupt if the hardware FIFO allows, or use a timer-driven poll at a rate the CPU can sustain. The key trade-off is latency versus throughput — batching increases the worst-case latency to the first sample in a batch, so you have to confirm the application can tolerate that. I'd also watch for the failure mode where the ISR is still too slow and interrupts start backing up: enable the peripheral's overrun flag and count overruns explicitly, so the system degrades visibly rather than silently dropping data.

**Possible follow-ups:** How would you size the DMA ring buffer, and what happens when the consumer falls behind? How would you verify on real hardware that the ISR budget assumption actually holds under worst-case conditions?

## Q2: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core principle is: never trust a single edge as proof of valid data. Treat the edge as a hint that something *may* have happened, and confirm with the peripheral's own status or data-valid indication before acting on it.

Concretely, I'd structure the ISR to do minimal work — record that an edge occurred and, if the hardware exposes a status register or FIFO level, check it. If the status says no new data, the edge was spurious and the ISR returns without touching the data path. If the status says data is available, read it and validate it (range check, CRC if the protocol provides one, sequence number continuity) before passing it downstream.

For glitch rejection at the hardware level, I'd look at what the MCU offers: input filtering/deglitch on the GPIO, or an RC filter on the board if the noise is genuinely analog. But firmware should not *rely* on the hardware filter — it should be defense in depth. I'd also add a counter for "edge seen but no data" events; if that counter climbs, it's telling you the signal integrity or the peripheral's timing is marginal, which is diagnostic gold.

One subtlety: if the peripheral can assert data-ready and then have the data consumed by another path (e.g., DMA), the ISR might see an edge for data that's already gone. So the validation logic has to account for the actual data flow, not just the pin state.

**Possible follow-ups:** How would you distinguish a glitch from a genuine but very short pulse? What would you do if the spurious edges only appear at certain temperatures or supply voltages?

## Q3: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** I'd start from a calculated estimate and then prove it empirically — never ship on the estimate alone.

The estimate comes from enumerating what the thread actually does: its call depth, the largest local buffers, the deepest library call chain (printf-style formatting and floating-point math are notorious stack hogs), plus the context-save frame the architecture pushes on interrupt entry. Zephyr's `CONFIG_THREAD_STACK_INFO` and the `k_thread_stack_space_get()` API let you query high-water marks at runtime, and the `CONFIG_INIT_STACKS` option fills stacks with a known pattern so you can see how deep the usage actually went. I'd run the system through its worst-case paths — error handling, logging enabled, the deepest protocol parse — and check the high-water mark after each.

The verification step is where discipline matters: add a safety margin (commonly 25–50% depending on how confident you are in the worst-case coverage), then enable stack sentinel checking (`CONFIG_STACK_SENTINEL`) and, if available, MPU-based stack overflow detection so an overflow faults deterministically instead of silently corrupting an adjacent thread's stack. I'd also test with the debug/logging configuration that ships in production, not just the lean dev build — logging can add surprising depth.

The failure mode to avoid is sizing once and never revisiting. Stack usage changes as features are added, so the high-water check should be part of the release checklist, not a one-time exercise.

**Possible follow-ups:** How would you handle a thread whose worst-case stack usage is genuinely hard to bound, such as one running a recursive parser? What's the trade-off between per-thread stacks and a shared stack for cooperative threads?

## Q4: You're debugging a firmware issue where a device's behavior is correct when the debugger is attached, but the device occasionally misbehaves when running standalone. How would you approach this?

**Answer:** This is a classic heisenbug, and the first instinct should be to suspect that attaching the debugger *changes* the system — timing, power state, or memory contents — rather than assuming the debugger is "fixing" a real bug.

The usual suspects, in rough order of likelihood: timing. The debugger halts the core, which stretches out delays and changes the relative timing of events, so a race condition or a marginal setup/hold timing issue disappears. Second, power: a debug probe often back-feeds or changes the supply/ground reference, masking a brownout or noise problem. Third, uninitialized memory: the debugger or the flash-loading process may leave RAM in a different state than a cold boot, hiding a missing-initialization bug. Fourth, low-power modes: the debugger can prevent the core from entering deep sleep, so a wake-up or retention bug never triggers.

My approach is to make the standalone case observable without a debugger. Use a spare UART or a RAM-backed log buffer that survives reset, and instrument the suspect code paths with timestamped markers. If the misbehavior is timing-related, toggle a GPIO at key points and capture it on a scope or logic analyzer — that gives you real-time visibility without halting the core. Reproduce with the debugger attached but *not* halted (run-mode only), then compare against standalone. If the bug vanishes only when halted, that's strong evidence for a race or timing margin. From there, I'd look at the specific shared state or peripheral timing involved and harden it — proper synchronization, adequate setup/hold margins, or explicit initialization.

**Possible follow-ups:** How would you capture a crash that only happens standalone, where you can't attach a debugger at the moment of failure? What role does the watchdog play in getting you a usable post-mortem?

## Q5: You discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules. How would you approach this situation?

**Answer:** The first thing I'd do is resist the two tempting extremes: silently hacking around it, and unilaterally launching a big refactor. Both are ways of avoiding the conversation that actually needs to happen.

I'd start by characterizing the problem precisely — what specifically is breaking, how often, and what the cost of *not* fixing it is (field failures, missed requirements, escalating maintenance burden). A vague "this design is bad" won't get buy-in; a concrete "this decision causes X failure mode in scenario Y, and here's the evidence" will. Then I'd lay out the realistic options with honest cost estimates: a full refactor, a targeted fix that contains the damage to the affected modules, or a documented workaround with a plan to address it in the next revision. Each has a different risk and schedule profile, and the right choice depends on where the project is relative to release and what the regulatory or safety implications are.

The ownership piece matters: since it was my decision, I'd be upfront about that rather than framing it as an external problem. That builds the credibility needed to propose the fix. I'd bring the options to whoever owns the schedule and risk — tech lead, project manager — and make the trade-off explicit so the decision is made with full information, not sprung on them. If the targeted fix is chosen, I'd make sure the underlying issue is captured in the design documentation and risk file so it's tracked rather than quietly forgotten. And I'd want a regression test that pins the failure mode, so whatever fix is chosen is verifiably effective.

**Possible follow-ups:** How would you decide whether the targeted fix is genuinely sufficient or just deferring the problem? How would you communicate the schedule impact without it reading as blame-shifting?