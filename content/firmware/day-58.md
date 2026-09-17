# firmware — Day 58

## Q1: How would you approach designing a firmware module that must detect a "stuck" peripheral — one that stops producing data without raising an error flag or interrupt — and recover from it without resetting the whole device?

**Answer:** The core problem is that you can't rely on the peripheral to tell you it's broken, so you need an independent liveness check driven by the application. The general pattern is a watchdog-style "heartbeat" at the application layer: each consumer of the peripheral records a timestamp (or a monotonic counter) every time it successfully receives fresh data, and a supervisory task periodically checks whether that timestamp has advanced within an expected window. The window should be derived from the peripheral's nominal data rate plus generous margin — not a magic number — so it tolerates normal jitter but catches a genuine stall.

On detection, recovery should be staged rather than immediate. The first step is usually a soft re-initialization of the peripheral: disable it, reset its registers to a known state, re-run the init sequence, and re-arm any DMA or interrupt configuration. If that fails to restore data within a bounded number of attempts, escalate to a bus-level recovery — for example, toggling the bus lines to unstick a slave that's holding a line, or power-cycling the peripheral's supply rail if the hardware supports it. Only if all of that fails should you consider a device-level reset, and even then it should be a controlled reset that preserves any safety-critical state and logs the event.

Two things matter for correctness: the recovery logic must itself be bounded (no infinite retry loops that hang the supervisory task), and the detection must be independent of the peripheral's own status reporting, since a stuck peripheral may report "fine" indefinitely. In a medical context, you'd also want the degraded state surfaced to the user or clinician rather than silently recovered, because repeated stalls are a signal worth investigating.

**Possible follow-ups:**
- How would you distinguish a genuinely stuck peripheral from one that's simply idle because there's no data to send?
- Where would you place the supervisory check — a dedicated low-priority thread, a timer callback, or the existing main loop — and what would drive that choice?

## Q2: How would you approach deciding between a memory pool and memory slabs in Zephyr RTOS when multiple threads need to share fixed-size data buffers?

**Answer:** Both are fixed-size allocators, so the decision usually comes down to the shape of the allocation pattern and the concurrency requirements rather than raw performance. A memory slab is optimized for a single block size and is the right choice when every allocation is the same size and you want the lowest possible allocation/deallocation overhead — it's essentially a free-list of identically sized blocks. A memory pool supports multiple block sizes within one pool, which is useful when you have a small number of related sizes (say, a header block and a payload block) but don't want to manage separate slabs for each.

The concurrency angle matters more in practice. Both are thread-safe, but you need to think about what happens when the pool is exhausted: does the allocating thread block waiting for a free block, or does it get an error and have to handle it? For a real-time sensor pipeline, blocking indefinitely on a buffer is usually unacceptable — you'd rather drop or defer a sample than stall a high-priority thread. So you'd typically configure the allocation to be non-blocking (or with a bounded timeout) and have the caller handle the "no buffer available" case explicitly.

Configuration considerations: size the pool for the worst-case number of in-flight buffers across all threads, not the average, and account for the fact that a buffer handed to a lower-priority consumer may be held longer than expected. You also want to think about alignment — DMA-capable buffers often need specific alignment, and the pool's block alignment must satisfy that. Finally, instrument the pool's high-water mark during testing so you can confirm your sizing assumption rather than guessing.

**Possible follow-ups:**
- How would you detect and diagnose pool exhaustion in the field without adding significant overhead to the allocation path?
- If a high-priority thread and a low-priority thread both draw from the same pool, how would you prevent the low-priority thread from starving the high-priority one?

## Q3: A junior engineer has implemented a firmware module that works correctly in testing but uses a fixed `k_sleep` delay after each command to wait for a peripheral to become ready, rather than checking a status register or using an interrupt. How would you guide them?

**Answer:** I'd start by acknowledging why the approach feels attractive — a fixed delay is simple, it's easy to reason about, and it "works" on the bench. The concern isn't that it's wrong in the sense of producing incorrect results today; it's that it's fragile in ways that won't show up until conditions change. The delay is tuned to one specific part, at one temperature, at one clock speed. A different silicon revision, a slower clock, or a part that's marginally out of spec can turn a working delay into an intermittent failure that's very hard to debug later.

The better pattern is to wait on the condition the peripheral actually signals — poll the status register with a bounded timeout, or better, let the peripheral's interrupt tell you when it's ready. The key insight to convey is that "wait for ready" and "wait for a fixed time" are different things: the first is correct by construction, the second is correct only as long as your timing assumption holds. A bounded poll loop gives you the same simplicity the engineer likes, but it's self-correcting and it fails loudly (timeout) instead of silently.

I'd also point out the real-time cost: a fixed `k_sleep` in a high-priority thread blocks that thread for the full delay even when the peripheral is ready sooner, which wastes CPU and can push other work past its deadline. A status-based wait returns as soon as the condition is met, so it's both more robust and more efficient. If the engineer is worried about determinism, the answer is that a bounded poll with a known maximum iteration count is just as deterministic as a fixed delay — and it's deterministic in the right way.

**Possible follow-ups:**
- How would you help them choose between a bounded poll and an interrupt-driven wait for a given peripheral?
- What would you do if the peripheral's datasheet doesn't specify a maximum ready time, only a typical one?

## Q4: How would you approach designing a firmware module that must log diagnostic events to flash, where the log must survive a power loss mid-write and the flash has limited erase cycles?

**Answer:** The two constraints — power-loss survivability and limited endurance — pull in different directions, so the design has to address both explicitly. For power-loss survivability, the standard approach is a log-structured or append-only scheme where each record is written with a self-describing header that includes a sequence number and a CRC (or equivalent integrity check). On boot, the reader scans for the last record with a valid header and CRC; anything after that is treated as a torn write and discarded. This means a power loss mid-write can only ever lose the in-progress record, never corrupt earlier ones. You also want to avoid in-place updates to a record — always append a new record rather than modifying an existing one, because an in-place update that's interrupted leaves the record in an indeterminate state.

For endurance, the key is to avoid erasing the same sector repeatedly. A circular log across multiple sectors spreads writes evenly, and you only erase a sector when the log wraps around to it. If the log is small and writes are frequent, you can add a RAM buffer that batches records and flushes them periodically, trading a small window of potential loss for a large reduction in erase cycles. The trade-off to make explicit is how much data you're willing to lose on power loss versus how much endurance you need — those are the two knobs.

A few practical details: reserve a small amount of flash for a "log metadata" region that tracks the current write position and wrap count, and update it carefully (again, append-style or with a checksum) so it survives power loss too. And think about what happens when the log is full — do you overwrite the oldest records, stop logging, or signal an error? For diagnostic logs, overwriting oldest is usually right, but it should be a deliberate decision, not an accident of the implementation.

**Possible follow-ups:**
- How would you verify that the power-loss recovery actually works, given that you can't easily cut power at an arbitrary point during a write?
- If the log is used for regulatory traceability rather than just diagnostics, how would that change your design?

## Q5: How would you approach a situation where you've inherited a firmware module with no tests, no documentation, and a reputation for being fragile, and you need to make a change to it?

**Answer:** The first instinct is to make the change as surgically as possible and get out, but that usually backfires because you don't yet know what the module actually does or what depends on its current behavior. So I'd start by building a safety net before touching anything. That means characterizing the module's behavior as it exists today — not what it's supposed to do, but what it actually does — through a combination of reading the code carefully, instrumenting it to log its inputs and outputs, and writing characterization tests that capture the current behavior even if some of that behavior looks wrong. The point of characterization tests isn't to assert correctness; it's to detect unintended changes.

In parallel, I'd map the module's interfaces: who calls it, what it calls, what shared state it touches, and what its timing assumptions are. Fragile modules often have hidden coupling — a global variable that another module reads, an implicit ordering requirement between calls, a timing dependency that isn't documented anywhere. Finding those before making the change is what prevents the change from breaking something three modules away.

Only then would I make the change, and I'd make it in the smallest increment that's independently verifiable, with the characterization tests running at each step. If the change requires refactoring the module to be testable, I'd do that refactoring as a separate, behavior-preserving step first, so that any test failure is unambiguously attributable to either the refactor or the feature change, not both at once. And I'd document what I learned as I go — the module's actual contract, its hidden dependencies, its known fragilities — because that documentation is what turns a fragile module into a maintainable one over time.

**Possible follow-ups:**
- How would you decide how much characterization testing is enough before making the change, given schedule pressure?
- What would you do if the characterization tests reveal behavior that looks like a bug, but other modules appear to depend on it?