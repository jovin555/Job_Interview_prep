# firmware — Day 92

## Q1: How would you approach designing a firmware module that must handle a peripheral whose interrupt rate is high enough that servicing every interrupt individually would consume an unreasonable share of CPU time?

**Answer:** The first step is to quantify the problem rather than assume it: measure the actual interrupt rate, the per-ISR entry/exit cost, and the work done per interrupt, then compute the fraction of CPU time consumed. If that fraction is unacceptable, the goal becomes reducing the number of interrupts the CPU services, not making the ISR faster in isolation.

The standard techniques, roughly in order of preference:

- **DMA with large transfers.** Let the peripheral move data into memory autonomously and interrupt only on completion of a block, half-buffer, or watermark. This converts N per-sample interrupts into a small number of per-block interrupts. The ISR then just signals a consumer task and re-arms the DMA.
- **FIFO/watermark thresholds.** Many peripherals have hardware FIFOs. Set the receive threshold so the interrupt fires only when enough data has accumulated to be worth servicing. This trades latency for throughput and is usually the cheapest fix.
- **Interrupt coalescing / batching.** If the hardware supports it, or via a timer, batch multiple events into one service call.
- **Deferred processing.** Keep the ISR minimal — capture the status, move data out of the peripheral, clear the flag, and hand off to a work queue or thread. The expensive parsing/processing happens outside interrupt context, which also keeps interrupt latency bounded for other peripherals.

The trade-off to articulate: batching and DMA increase latency and buffer memory requirements, and you must handle the case where the consumer falls behind (overrun detection, backpressure, or dropping with a counted error rather than silently). For a medical device, an overrun is a data-integrity event that must be detected and reported, not hidden. I'd also verify the design with measured CPU load and worst-case interrupt latency, not just average throughput.

**Possible follow-ups:** How would you detect and report a DMA overrun to the application without adding latency to the ISR? What changes if the peripheral has no FIFO and no DMA support?

## Q2: How would you approach implementing a firmware module that must handle a peripheral whose data-ready signal is edge-triggered, but where the signal can occasionally glitch and produce a spurious edge that does not correspond to valid data?

**Answer:** The core principle is: never trust the edge alone — always confirm with the peripheral's own status or data validity before acting on it. The edge is a hint that something may have happened; the status register or the data payload is the authority.

Concretely:

- **Validate in the ISR or deferred handler.** On the edge, read the peripheral's status/data-ready flag. If it isn't actually set, treat the interrupt as spurious: count it, clear the pending interrupt, and return. This is cheap and catches most glitches.
- **Debounce where appropriate.** If the signal is a GPIO, hardware or software debouncing (a short blanking window after the first edge) can filter mechanical or electrical noise. For a genuine data-ready line, a small time-based filter is usually enough.
- **Check data integrity at the protocol layer.** Even a "valid" edge can correspond to a corrupted transfer. CRC, framing checks, and range validation on the payload catch the cases the edge check misses. A spurious edge that produces a bad read should be discarded and counted, not propagated.
- **Distinguish "no data" from "error."** A glitch that yields no valid data is not the same as a sensor fault. The module should expose a spurious-interrupt counter and a data-validity counter separately so diagnostics can tell them apart.
- **Consider the root cause.** If glitches are frequent, the fix may be hardware: a pull resistor, a filter capacitor, better grounding, or a Schmitt-trigger input. Firmware should be robust to glitches, but a high glitch rate is a signal to involve hardware engineering.

The trade-off is latency versus robustness: validating in the ISR adds a register read but keeps the response fast; deferring validation to a thread is cheaper in interrupt context but adds scheduling delay. For a data-ready line where the data must be read promptly before it's overwritten, I'd validate the status in the ISR and do the heavier integrity checks in the deferred handler.

**Possible follow-ups:** How would you decide the blanking window duration, and what happens if a legitimate edge arrives inside it? How would you test this behavior without being able to inject glitches on real hardware?

## Q3: How would you approach sizing thread stacks in a Zephyr RTOS application, and what would you do to verify that your sizing is actually correct rather than just "probably enough"?

**Answer:** Stack sizing should be an evidence-based process, not a guess with a safety margin bolted on. My approach:

1. **Start from a measured baseline.** Enable Zephyr's stack usage reporting (`CONFIG_THREAD_ANALYZER`, `CONFIG_THREAD_STACK_INFO`, and the high-water-mark tracking). Run the system through its worst-case paths — not just the happy path — and read the actual peak usage per thread.
2. **Account for the worst case, not the average.** The high-water mark only tells you what happened, not what could happen. Identify the deepest call chain per thread, including ISR nesting that runs on that thread's stack (on many architectures, ISRs use the interrupted thread's stack). Add the context-switch frame, any floating-point or FPU context if enabled, and library calls with known-large frames (printf-family, crypto, JSON parsing).
3. **Add a justified margin.** A common rule is 25–50% headroom over measured worst case, but the margin should reflect confidence: a thread with a well-understood call graph needs less than one calling into a third-party library whose internals you don't control.
4. **Verify continuously.** Keep the analyzer enabled in debug builds and in CI, and treat a high-water mark approaching the limit as a build failure or at least a warning. Add a canary pattern at the stack base and check it periodically in test builds.
5. **Re-verify after changes.** Any new library, deeper call chain, or added ISR nesting invalidates the old number. Stack sizing is not a one-time task.

The trade-off is RAM versus safety: over-provisioning wastes RAM that constrained devices can't spare, under-provisioning causes stack overflow that may manifest as seemingly unrelated corruption. For safety-critical firmware, I'd rather have a measured number with a documented margin than a generous guess, because the measured number can be defended in review and re-checked in CI.

**Possible follow-ups:** How would you detect a stack overflow at runtime, and what would you do when you detect one? How does enabling an FPU change your sizing calculation?

## Q4: How would you approach designing a firmware module that must survive a brownout — where the supply voltage sags briefly but doesn't fully drop — without corrupting persistent state or producing a spurious reset?

**Answer:** Brownout handling has to be designed at three layers: detection, protection of persistent state, and recovery behavior.

**Detection.** Use the MCU's brownout detector (BOR) or a supply-voltage monitor with a threshold set above the MCU's minimum operating voltage but below nominal. The key parameter is the warning window: the time between the threshold being crossed and the supply falling below the point where the MCU can no longer execute reliably. That window determines what you can safely do in response. If the window is too short for the MCU to react, the design needs hardware help — a supervisor IC that holds the part in reset until the supply is stable, or enough bulk capacitance to extend the window.

**Protection of persistent state.** The rule is: never leave persistent state in a state that is only valid if the write completes. Techniques:

- **Atomic commit patterns.** Write new data to a staging area, then flip a single commit marker (or a sequence number with CRC) as the last step. On boot, an incomplete commit is detected and discarded or rolled back.
- **Journaling or double-buffering in flash.** Keep two copies with sequence numbers and CRCs; the valid one is the one with the highest sequence number and a matching CRC.
- **Avoid long flash operations in the brownout window.** If the warning window is short, don't start a multi-millisecond erase; instead, set a flag and let the next boot handle it.
- **Disable writes when the supply is marginal.** If the monitor indicates a sag, defer non-critical writes until the supply recovers.

**Recovery behavior.** On boot after a brownout, the firmware should distinguish a genuine power-on from a brownout recovery (via a reset-cause register), validate persistent state, and enter a safe state if anything is inconsistent. It should not produce a spurious reset in the sense of resetting during normal operation — the BOR should only assert when the supply is genuinely out of spec, and the threshold should be chosen to avoid nuisance trips during legitimate load transients.

The trade-off is between the complexity of atomic-commit schemes and the cost of corruption. For configuration and calibration data, the atomic-commit pattern is cheap and worth it. For high-rate logging, a journaled ring with CRC per record is more appropriate. I'd also test this deliberately: a programmable supply that ramps down and back up at various rates, plus a fixture that cuts power mid-write, is the only way to know the design actually works.

**Possible follow-ups:** How would you choose the brownout threshold, and what would you do if the MCU's BOR window is too short for your flash write? How would you test brownout behavior reproducibly in a lab?

## Q5: You're leading a firmware team that is transitioning from a bare-metal approach to using Zephyr RTOS for a new medical device. Two senior engineers disagree: one wants to port the existing bare-metal drivers directly into Zephyr as custom drivers, while the other wants to rewrite them using Zephyr's native driver model. How would you guide the team to a decision?

**Answer:** I'd frame this as a decision to be made on explicit criteria rather than on preference, and I'd make sure both engineers feel their concerns are legitimate — because both positions have real merit.

First, I'd get the facts on the table:

- **What does "port directly" actually mean?** Wrapping bare-metal register-poking code in a Zephyr thread is possible, but it bypasses the device model, the power management hooks, and the interrupt-handling conventions. That has real costs: it won't participate in `pm_device` state transitions, it may conflict with Zephyr's interrupt controller abstraction, and it becomes a maintenance island.
- **What does "native driver model" actually cost?** Rewriting means re-validating behavior that already works, against a schedule. For a medical device, re-validation is not free — it touches the verification evidence.

Then I'd apply criteria:

- **Reuse vs. rewrite per driver.** Not every driver needs the same answer. A simple GPIO or ADC driver is cheap to rewrite natively and gains full integration. A complex, heavily validated driver with subtle timing might be wrapped initially behind a native-model façade, with the internals ported incrementally. The façade gives the rest of the system a consistent interface while containing the risk.
- **Power management requirements.** If the device must enter low-power states and the drivers need to participate in suspend/resume, native integration is close to mandatory. That's a strong argument for the native model on any driver in the power path.
- **Validation and traceability.** Whatever we choose, the verification evidence has to be regenerated or re-justified. I'd ask both engineers to estimate that cost honestly, because it's often the deciding factor.
- **Long-term ownership.** Who maintains this in two years? A native driver is easier for a new engineer to understand because it follows a documented pattern; a bespoke wrapper is a knowledge silo.

My likely recommendation would be a hybrid with a clear rule: new drivers and drivers in the power path go native; existing validated drivers get a native-model interface with the internals ported as time and risk allow, and each port is tracked as a deliberate task rather than left indefinitely. I'd document the decision and the rationale so it doesn't get relitigated, and I'd set a review point to revisit the wrapped drivers once the first native ones are proven.

The leadership part is making sure the decision is made on criteria the team agrees on, not on seniority. I'd ask each engineer to write down the specific failure modes they're worried about, then check whether the chosen approach actually addresses them.

**Possible follow-ups:** How would you handle it if the engineer who wanted the direct port remains unconvinced after the decision? What would you do if the first native driver rewrite takes significantly longer than estimated?