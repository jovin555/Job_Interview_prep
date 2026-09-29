# firmware — Day 70

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** The first step is to recognize that this is fundamentally a throughput problem, not a coding problem — if the event rate genuinely exceeds what the CPU can service per event, no amount of ISR optimization will fully solve it, so the goal becomes reducing per-event work and/or shedding load gracefully.

Concretely, I'd work through a few layers:

1. **Quantify the budget.** Measure the actual ISR entry/exit overhead plus the minimum work required (reading a status register, moving a byte or word, clearing the flag). Compare that against the event rate to see how much headroom, if any, exists. This tells you whether you're 10% over budget or 10x over budget — the strategies differ.

2. **Minimize work inside the ISR.** The ISR should do the absolute minimum: acknowledge the source, capture the data into a pre-allocated buffer or ring, and defer everything else. No parsing, no logging, no floating point, no blocking calls. If the peripheral has a FIFO, use it — let the hardware absorb bursts and only interrupt on a threshold or on FIFO-non-empty rather than per-sample.

3. **Move to DMA.** If the peripheral supports it, DMA is usually the correct answer: the CPU is no longer in the per-sample path at all, and you interrupt once per block instead of once per byte. This changes the problem from "service every event" to "service every N events," which is often enough to bring it back within budget.

4. **Coalesce or batch.** If DMA isn't available, consider whether the peripheral can be configured to interrupt less often — e.g., a "buffer half-full" or "sample count reached" interrupt instead of per-sample. Many peripherals have this and it's often overlooked.

5. **Prioritize and shed.** If the event rate is genuinely higher than the CPU can handle even after the above, then something has to give. Options: drop samples deliberately with a counter so the loss is visible and bounded rather than random; reduce the sample rate at the source; or move the work to a higher-priority context and accept that lower-priority work will be starved. The key is to make the degradation explicit and observable rather than letting the system silently fall behind.

6. **Reconsider the architecture.** If this is a recurring pattern, it may indicate the MCU is undersized for the workload, or that the peripheral configuration is wrong (e.g., polling a slow bus at a rate the bus can't sustain). Sometimes the right answer is a hardware or partitioning change, not a firmware one.

Throughout, I'd instrument the system so I can see ISR duration, ISR frequency, and any dropped-event counters — without that, you're guessing.

**Possible follow-ups:**
- How would you measure ISR duration accurately without perturbing the timing you're trying to measure?
- If you had to drop samples, how would you decide which ones to drop and how would you surface that to the rest of the system?

## Q2: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** This is a classic case where the hardware signal can't be fully trusted, so the firmware has to validate rather than assume. The approach has two parts: making the edge handling robust, and making the data validation independent of the edge.

On the edge side:

- **Debounce in hardware if possible.** If the board allows it, an RC filter or a Schmitt-trigger input is the cleanest fix — it removes the glitch before firmware ever sees it. Firmware debouncing is a fallback, not a first choice, because it costs CPU time and adds latency.
- **If debouncing in firmware**, don't use a blocking delay. Instead, timestamp the edge (using a hardware timer capture if available) and require a minimum interval between accepted edges. Edges arriving faster than the peripheral's minimum possible data rate are, by definition, spurious.
- **Use the peripheral's own status.** Most data-ready signals correspond to a status bit or a FIFO level in the peripheral. After an edge, read that status; if it says "no data," the edge was spurious and can be ignored. This is often the most reliable check because it's the peripheral's own view of reality.

On the data side:

- **Never trust the edge as proof of valid data.** Even a genuine edge can precede data that fails a CRC, is out of range, or is otherwise invalid. So the read path should always validate: check CRC or checksum if the protocol provides one, check range plausibility, and check that the value isn't a known "no data" sentinel.
- **Distinguish "no data" from "bad data."** A spurious edge that yields no data is different from a real edge that yields corrupt data. The former can be silently ignored (with a counter for diagnostics); the latter may need to trigger a retry, a fault, or a degraded-mode transition depending on the application.
- **Bound the consequences.** If glitches are frequent, the system shouldn't spin retrying forever. A bounded retry count, a rate limiter, or a "too many spurious edges, declare the peripheral faulty" state prevents a glitch storm from consuming the CPU.

For a medical device specifically, the validation layer matters more than the edge handling, because the requirement is usually "never present a false reading" rather than "never miss a reading." So I'd err toward rejecting ambiguous data and flagging it, rather than accepting it and hoping.

**Possible follow-ups:**
- How would you distinguish a glitch on the data-ready line from a genuine but very short pulse that the CPU missed?
- If the peripheral has no CRC and no status bit, what other validation could you apply?

## Q3: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** Stack sizing is one of those areas where "it works in testing" is not evidence of correctness, because stack overflow often manifests as corruption somewhere else rather than an immediate crash. So I treat it as something to measure, not estimate.

**Initial sizing:**
- Start from a reasoned estimate: the deepest call chain, plus the largest local frame in that chain, plus space for the context switch frame, plus any ISR nesting that can occur on that thread's stack (on some architectures, ISRs use the current thread's stack). Add margin — typically 25–50% — because estimates are always wrong in the optimistic direction.
- Zephyr's `CONFIG_THREAD_STACK_INFO` and the `k_thread_stack_space_get()` API let you query the unused portion at runtime, which is the key measurement tool.

**Verification:**
- **Fill pattern / canary.** Zephyr can paint the stack with a known pattern at creation (`CONFIG_INIT_STACKS`), so you can see how deep the high-water mark actually went. This is the single most useful technique — it tells you the real worst case observed, not the theoretical one.
- **Exercise the worst case.** The high-water mark is only meaningful if you've actually run the path that uses the most stack. That means deliberately triggering the deepest error-handling paths, the largest logging calls, the most nested callbacks, and any code that runs only on rare events. A stack that's fine in normal operation can overflow the first time an error path runs.
- **Check across configurations.** Debug vs. release builds, different compiler optimization levels, and different feature sets all change stack usage. A stack sized for a debug build may be over-sized for release, or vice versa if inlining changes.
- **Watch for recursion and large locals.** Any recursive function or large on-stack array is a red flag. If a function needs a big buffer, it should generally be static, in a memory pool, or heap-allocated — not on the stack.
- **Add runtime protection.** Zephyr's stack sentinel (`CONFIG_STACK_SENTINEL`) and MPU-based stack protection (`CONFIG_MPU_STACK_GUARD`) turn a silent overflow into a detectable fault. For a medical device, I'd want this enabled in at least the test builds, and ideally in production if the overhead is acceptable.

**Ongoing:**
- Keep the high-water measurements in CI or in a periodic diagnostic dump, so a future change that increases stack usage gets caught before it becomes a field issue. Stack usage tends to creep up over a project's life, and without measurement it creeps silently.

**Possible follow-ups:**
- How would you handle a thread whose worst-case stack usage is genuinely hard to bound, e.g., because it calls into a library with deep internal call chains?
- What's the trade-off between enabling MPU stack guards and the runtime overhead they add?

## Q4: You're debugging a firmware issue where a device's behavior is correct when powered from a bench supply but intermittently wrong when powered from a battery, and the wrong behavior correlates with the device transmitting wirelessly. How would you approach this?

**Answer:** The correlation with both battery power and wireless transmission is a strong hint that this is a power integrity or supply-impedance issue, not a logic bug. The bench supply has low output impedance and can absorb transient current demands; a battery has higher impedance, and the wireless transmit burst draws a large, fast current spike. That spike, combined with the battery's impedance and the board's decoupling, can cause a local supply droop that affects sensitive analog or digital circuitry.

My approach would be:

1. **Confirm the hypothesis with measurement, not inference.** Put a scope probe on the supply rail at the point of load — not at the battery terminals — with a fast timebase, and trigger on the wireless transmit event. Look for a droop, a ringing, or a ground bounce that coincides with the misbehavior. Also probe the ground reference at the same point, because ground bounce is often the real culprit and is easy to miss if you only look at the positive rail.

2. **Characterize the failure mode.** Is the wrong behavior a reset, a corrupted reading, a communication error, or something else? The nature of the failure tells you which subsystem is being affected. If it's an ADC reading, the analog reference or the analog supply is suspect. If it's a digital communication error, the digital rail or ground is suspect. If it's a reset, the brownout detector or the core supply is suspect.

3. **Check the obvious hardware factors.** Decoupling capacitor placement and value — are they close enough to the load, and is there enough bulk capacitance to ride through the transmit burst? Is the wireless module's supply shared with sensitive analog circuitry, or is it on its own regulator? Is the ground plane continuous under the transmit path, or is there a slot that forces return currents through a high-impedance path?

4. **Check the firmware side.** Is the firmware doing anything that makes the problem worse — e.g., starting an ADC conversion at the same moment as a transmit burst, or failing to sequence power domains correctly? Sometimes the fix is to schedule sensitive operations away from the transmit window, or to add a small delay after transmit before sampling.

5. **Consider the battery itself.** A battery near end-of-life, or one with high internal resistance, will show this more than a fresh one. If the failure correlates with battery state of charge, that's a strong confirmation. The fix might be a larger bulk capacitor, a different regulator topology, or a firmware change to reduce peak current (e.g., lower transmit power, or stagger transmissions).

6. **Verify the fix under the worst case.** Once you've made a change, test with a battery at low state of charge, at temperature extremes if relevant, and with the transmit duty cycle at its maximum. A fix that works on a fresh battery at room temperature may not hold in the field.

The key discipline here is to resist the temptation to "fix it in firmware" before you understand the physical mechanism. A firmware workaround that masks a supply droop may fail under conditions you haven't tested.

**Possible follow-ups:**
- How would you distinguish a supply droop from a ground bounce if you only have one scope probe?
- If the root cause turns out to be a hardware layout issue that can't be changed, what firmware mitigations would you consider, and what are their limits?

## Q5: How would you approach a situation where you discover, late in a project, that a firmware design decision you made early on is now causing significant problems, and changing it would require rework across several modules?

**Answer:** The first thing I'd do is separate the technical question from the interpersonal one, because they need different handling and conflating them makes both worse.

**Technically:**
- **Quantify the problem.** "This is causing significant problems" needs to become concrete: what specifically is failing, how often, and what's the cost of leaving it? Is it a correctness issue, a maintainability issue, a performance issue, or a schedule issue? The answer determines whether rework is justified at all.
- **Evaluate the options honestly.** There are usually more than two: (a) full rework now, (b) targeted fix that addresses the worst symptoms without changing the architecture, (c) workaround at the boundary that contains the problem, (d) defer to the next major revision. Each has a cost and a risk. I'd write these down rather than argue them verbally, because writing forces clarity and gives others something concrete to react to.
- **Estimate the rework.** Not just "it touches several modules" but "here's the list of modules, here's the interface changes, here's the test impact, here's the estimated effort." A rough but honest estimate is far more useful than a vague sense of dread.
- **Identify the minimum viable change.** Often the full rework isn't necessary — a narrower change to the interface or the data flow can capture most of the benefit at a fraction of the cost. I'd look for that before proposing the big version.

**Interpersonally:**
- **Own it early.** If the decision was mine, I'd say so plainly and without defensiveness. Trying to obscure the origin of the problem erodes trust faster than the problem itself.
- **Bring options, not just a problem.** "Here's what's wrong, here are three ways to handle it, here's my recommendation and why" is a much easier conversation than "we have a problem."
- **Frame it around the project's goals, not my preference.** The question isn't "should we do the rework I want" but "what's the best use of the remaining time given what we now know." That framing makes it a shared decision rather than a personal one.
- **Respect the schedule reality.** If the schedule genuinely can't absorb the rework, then the honest answer may be "we contain it now, document it clearly, and fix it properly in the next revision." That's a legitimate outcome, not a failure — as long as the containment is real and the debt is recorded.

**Afterward:**
- Whatever we decide, I'd make sure the decision and its rationale are written down, so that six months later nobody has to reconstruct why the code looks the way it does.
- I'd also look at whether the original decision could have been caught earlier — not to beat myself up, but to see if there's a process change (an earlier interface review, a spike, a prototype) that would catch the next one sooner.

The worst outcome isn't the rework or the workaround — it's pretending the problem isn't there and letting it surface in the field.

**Possible follow-ups:**
- How would you decide between containing the problem now and fixing it properly, if the schedule pressure is coming from a customer commitment?
- If the decision was made by someone else who's no longer on the project, how would you handle the conversation differently?