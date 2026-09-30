# firmware — Day 71

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt can fire faster than the CPU can service it, so that the ISR itself becomes the bottleneck?

**Answer:** The first step is to quantify the problem rather than assume it: measure the actual interrupt rate, the worst-case ISR execution time, and the CPU headroom left for everything else. If the ISR is genuinely saturating the core, no amount of clever ISR code will fix it — the architecture has to change. The general strategies, roughly in order of preference:

1. **Reduce the work per interrupt.** Move everything that isn't strictly time-critical out of the ISR into a deferred context — a work queue, a thread, or a bottom-half mechanism. The ISR should do the minimum: acknowledge the source, capture the data or a pointer to it, and signal. Anything involving parsing, logging, or decision-making belongs elsewhere.
2. **Batch or coalesce.** If the peripheral supports it, configure it to interrupt on a threshold or after N samples rather than per-event, so the interrupt rate drops by an order of magnitude. Many peripherals have FIFOs or watermark interrupts precisely for this.
3. **Move to DMA.** If the data is a stream, DMA with a half-transfer and full-transfer interrupt is usually the right answer — the CPU only wakes when a buffer is half full or full, not per byte.
4. **Prioritize and mask.** If some interrupts are less urgent, lower their priority or temporarily mask them during the critical window. This doesn't reduce total load but it protects the timing of the truly critical path.
5. **Accept that the design is wrong.** If none of the above brings the load within budget, the hardware or the peripheral configuration is the problem, and that's a conversation to have early rather than papering over it in firmware.

The key discipline is to budget interrupt latency explicitly — decide up front what the worst-case ISR time is allowed to be, and treat any ISR that exceeds it as a defect, not a tuning problem.

**Possible follow-ups:**
- How would you measure worst-case ISR execution time reliably, given that the worst case may only occur under specific conditions?
- If the peripheral has no FIFO and no DMA support, what options remain?

## Q2: You're debugging a firmware issue where a device's behavior is correct when powered from a bench supply but intermittently wrong when powered from a battery, and the wrong behavior correlates with the device transmitting wirelessly. How would you approach this?

**Answer:** The correlation with wireless transmission is the strongest clue — it points at a supply integrity or grounding problem rather than a logic bug. A bench supply typically has very low output impedance and good transient response; a battery has higher effective series resistance, and the wireless transmit burst draws a large, fast current pulse. That pulse can cause a supply droop or a ground bounce that the bench supply simply absorbs.

My approach would be:

1. **Instrument the supply.** Put a scope probe on the supply rail at the point of load — not at the battery terminals — with a short ground lead, and trigger on the transmit event. Look for droop, ringing, or a slow recovery. Also probe the ground reference at the same point to catch ground bounce.
2. **Correlate the failure with the transient.** If the misbehavior happens in the window right after the transmit burst begins, that's strong evidence. If it happens at a different time, the wireless correlation may be coincidental (e.g., both are symptoms of a shared cause).
3. **Check the obvious hardware suspects.** Bulk decoupling near the load, the ESR of the bulk capacitor, the trace impedance between battery and load, and whether the wireless module shares a supply rail with sensitive analog or digital logic without adequate isolation.
4. **Check firmware-side assumptions.** Does the firmware assume a stable supply during the transmit window? For example, does it read an ADC or a sensor during transmit, when the reference or the analog supply may be disturbed? Does it assume a brownout won't occur, when in fact the supply is dipping below the brownout threshold briefly?
5. **Reproduce deterministically.** If possible, replace the battery with a supply that has a series resistor to emulate battery ESR, so the failure can be triggered on demand rather than chased intermittently.

The fix could be hardware (better decoupling, separate rails, a bulk cap with lower ESR) or firmware (avoid sensitive operations during transmit, add a brownout-tolerant sequence), but the diagnosis has to come first.

**Possible follow-ups:**
- How would you distinguish a supply droop from a ground bounce as the root cause?
- If the fix has to be in firmware because the hardware is already in production, what would you do?

## Q3: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core problem is that an edge-triggered signal is a claim, not a guarantee — the firmware has to validate the claim before acting on it. The approach has three layers:

1. **Validate at the source.** When the edge fires, don't immediately consume data. First check the peripheral's own status register or data-ready bit to confirm that data is actually available. If the status bit says no, the edge was spurious — log it if useful, but don't proceed. This is the cheapest and most reliable filter, and it works whenever the peripheral exposes a status bit.
2. **Validate the data.** Even if the status bit says data is ready, the data itself may be invalid — a CRC failure, an out-of-range value, or a stale reading. Apply the same validation the module would apply to any reading, and reject or flag anything that fails.
3. **Debounce or filter the edge in hardware or firmware.** If the glitch is a genuine electrical artifact (e.g., a slow edge crossing a threshold, or noise on the line), a small RC filter or a Schmitt-trigger input may eliminate it at the source. In firmware, a short debounce window — ignore edges within N microseconds of the last accepted edge — can suppress repeated glitches, but this is a blunt instrument and should be a last resort, because it can also suppress legitimate closely-spaced events.

The design principle is that the ISR should treat the edge as a hint to go look, not as proof that data is present. That keeps the module robust even if the electrical environment is noisy.

**Possible follow-ups:**
- What are the risks of a firmware debounce window, and how would you choose the window size?
- If the peripheral has no status register and no CRC, how would you validate the data?

## Q4: You're debugging a firmware issue where a device's behavior is correct on the first power-up after flashing, but after a warm reset (without power cycling) a peripheral initializes incorrectly. How would you approach this?

**Answer:** A warm reset that leaves a peripheral in a bad state almost always means the peripheral was not fully reset by the reset controller, or the firmware's initialization sequence assumes a cold-start state that doesn't hold after a warm reset. The approach is to compare the two cases systematically:

1. **Characterize the difference.** What exactly is different after a warm reset? Is the peripheral's configuration register in an unexpected state? Is a FIFO still holding stale data? Is a clock or PLL still running when the firmware assumes it's off? Reading back the peripheral's registers after init in both cases is the fastest way to see the divergence.
2. **Check the reset tree.** Many MCUs have multiple reset domains — a warm reset may reset the CPU and some peripherals but not others. If the peripheral is in a domain that isn't reset by a warm reset, the firmware must explicitly reset it (via a peripheral reset register or a software reset command) before configuring it.
3. **Check the initialization sequence for assumptions.** Does the init code assume the peripheral is disabled at the start? Does it assume a particular clock is off? Does it assume a FIFO is empty? Any of these can be false after a warm reset, and the fix is usually to make the init sequence explicitly bring the peripheral to a known state rather than assuming it.
4. **Check for stale state in the firmware itself.** If the firmware keeps state in RAM that survives a warm reset (because RAM isn't cleared), and the init code reads that state, it may be acting on stale data. A warm reset that doesn't clear RAM is a common source of this class of bug.
5. **Reproduce and bisect.** Once the divergence is identified, the fix is usually small — an explicit reset, a reordering of init steps, or clearing a state variable. Verify by testing both cold and warm reset paths.

The general lesson is that "reset" is not a single thing on most MCUs, and firmware init sequences should be written to bring the system to a known state explicitly rather than relying on the reset controller to have done it.

**Possible follow-ups:**
- How would you determine which reset domains are affected by a warm reset on a given MCU?
- If the peripheral has no software reset, what alternatives exist?

## Q5: A junior engineer on your team has implemented a firmware module that works correctly in testing, but you notice it uses a `volatile` global variable as the sole synchronization mechanism between an ISR and a thread. They argue that `volatile` guarantees the compiler won't optimize the access away, so it's safe. How would you guide them?

**Answer:** This is a common and understandable misconception, and the right response is to acknowledge what `volatile` does correctly before explaining what it doesn't do. `volatile` does guarantee that the compiler will not optimize away or reorder accesses to that variable relative to other volatile accesses — that part of the engineer's reasoning is correct. What it does not guarantee is atomicity or memory ordering with respect to non-volatile accesses, and those are exactly what's needed for ISR/thread synchronization.

The specific gaps:

- **Atomicity.** A `volatile` variable is not atomic just because it's one byte or one word. On many architectures, a read-modify-write (e.g., `counter++`) is not atomic, and even a plain read or write can be torn if the variable is larger than the bus width. The compiler is free to emit a load-modify-store sequence that can be interrupted mid-way.
- **Memory ordering.** `volatile` does not establish a happens-before relationship with other memory accesses. The compiler and the CPU can reorder non-volatile accesses around a volatile one, which means data written before a flag is set may not be visible when the flag is observed.
- **The right tools.** The correct primitives are atomic operations (e.g., C11 `_Atomic`, or the platform's atomic intrinsics), memory barriers where ordering matters, and — for anything more complex than a single flag — a proper synchronization primitive like a mutex, a semaphore, or a lock-free queue designed for the ISR/thread boundary.

How I'd guide them: rather than just saying "that's wrong," I'd walk through a concrete failure scenario — for example, a counter incremented in the ISR and read in the thread, where the read-modify-write is interrupted — and show how the bug manifests intermittently. Then I'd point them at the correct primitive for their specific case. The goal is for them to internalize the distinction between "the compiler won't remove this access" and "this access is safe to share across contexts," because that distinction comes up repeatedly in embedded work.

**Possible follow-ups:**
- What's the difference between `volatile` and `_Atomic` in C11, and when would you use each?
- If the shared data is larger than a single word, what synchronization options exist that don't require disabling interrupts?

**Possible follow-ups:**
- How would you review a codebase to find other instances of this same misconception?
- What's the cost of using a mutex in an ISR context, and why is it usually not allowed?