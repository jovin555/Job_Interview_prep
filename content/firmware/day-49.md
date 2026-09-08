# firmware — Day 49

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** This is a classic priority-inversion-plus-blocking problem. The first thing I'd recognize is that you can't simply let a lower-priority task block the CPU for 100 ms in a system with a 1 ms hard deadline — that would cause the sensor task to miss its window entirely. The solution needs to address both the blocking nature of flash operations and the priority structure.

My approach would be multi-layered:

1. **Move the flash operation out of the critical path.** Flash erase/write operations on most MCUs are performed by a hardware controller, not by the CPU itself. The CPU typically just initiates the operation and then polls a status register or waits for an interrupt. If the driver is implemented as a blocking poll, that's a driver design problem, not an inherent hardware limitation. I'd look at whether the flash controller supports interrupts or DMA, and restructure the driver to be asynchronous — start the erase, yield the CPU, and get notified via interrupt or callback when it completes.

2. **If the flash controller truly blocks the CPU** (some older or simpler parts do stall the core during erase), then the architecture needs to change. Options include:
   - Using a separate flash chip on SPI/QSPI that doesn't stall the main CPU.
   - Moving the flash operation to a different core if the MCU is multi-core.
   - Accepting that the erase can't happen during active sensing and deferring it to a maintenance window.

3. **If some blocking is unavoidable**, I'd use Zephyr's priority inheritance mechanisms or restructure the task priorities. Zephyr supports priority inheritance on mutexes, which helps when the blocking is due to resource contention rather than raw CPU stall. But if it's a raw CPU stall, no RTOS primitive helps — the CPU simply can't run the sensor task.

4. **I'd also question the 100 ms figure.** Flash erase times are often specified as worst-case, and many devices have smaller page-erase operations that take far less time. If the lower-priority task only needs to erase a small region, a page erase might take 5–10 ms instead of 100 ms for a full sector. That changes the analysis significantly.

5. **Finally, I'd add a timing budget analysis.** I'd document the worst-case interrupt latency and task scheduling delay for the sensor task under all conditions, including during flash operations. If the numbers don't meet the 1 ms requirement, the design needs to change — not just the scheduling parameters.

**Possible follow-ups:**
- How would you handle the case where the flash erase is on the same chip as the code being executed, and the CPU does stall during erase?
- How would you verify that the sensor task never misses its deadline, given that flash erase timing can vary with temperature and supply voltage?

---

## Q2: You're debugging a firmware issue where a device's flash write operations occasionally corrupt data in an unrelated memory region. The corruption is intermittent and only occurs when the device is under heavy load. How would you approach this?

**Answer:** This is a serious symptom that suggests a few distinct root-cause categories, and I'd approach it systematically rather than guessing.

**First, I'd rule out the obvious: a pointer bug.** If some code is writing through a wild or uninitialized pointer, it could land anywhere in memory, including the flash buffer region. Under heavy load, timing changes could expose a race condition where a buffer is being used before it's initialized, or after it's been freed. I'd start by reviewing all code that touches the flash write path — the buffer being written, the DMA descriptors if used, and any cache-invalidation logic.

**Second, I'd look at DMA configuration.** If the flash write uses DMA, a common failure mode is a DMA descriptor or buffer that overlaps with other data structures. If the DMA is configured with the wrong buffer size or the buffer is on the stack and the stack grows into it, you'd get corruption under specific timing conditions. I'd check whether the DMA source buffer is properly aligned, whether the DMA channel could be conflicting with another peripheral, and whether cache coherency is handled correctly if the MCU has a cache.

**Third, I'd examine the flash controller's own constraints.** Some flash controllers require that writes be aligned to certain boundaries, or that the CPU not access the flash bank being programmed. If the code is executing from the same flash bank that's being written, and the linker has placed variables or code in a region that conflicts, you can get subtle corruption. I'd check the linker script and memory map.

**Fourth, I'd consider electrical issues.** Under heavy load, the supply voltage might droop, and if the flash programming voltage isn't stable, you can get marginal writes that corrupt adjacent cells. This is more of a hardware issue, but firmware can contribute by not properly sequencing power-hungry operations.

**My debugging methodology would be:**
1. Reproduce with instrumentation — add a memory guard pattern around the corrupted region to detect when and how it's being overwritten.
2. Use the MPU (Memory Protection Unit) if available to make the flash buffer region read-only except during the actual write operation, so any errant write triggers a fault immediately rather than silently corrupting data.
3. Check the watchdog and interrupt priorities — if a higher-priority ISR is preempting the flash write sequence at the wrong moment, it could corrupt the write.
4. Review the DMA and interrupt vectors for any overlap or misconfiguration.

**Possible follow-ups:**
- How would you use the MPU to help diagnose this without changing the behavior you're trying to reproduce?
- What specific checks would you do on the DMA configuration to rule out descriptor corruption?

---

## Q3: You're implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician. How would you approach this?

**Answer:** In a medical monitoring context, the fundamental principle is that it's always better to show "no data" or an error state than to show a plausible-but-wrong value. A clinician can respond to a missing reading; they cannot respond to a false one. So the design philosophy starts there.

**My approach would have several layers:**

1. **Validation at the protocol level.** If the sensor communicates over a bus like I2C or SPI, the first check is whether the data packet itself is valid — CRC, checksum, or parity. If the packet fails validation, it's discarded entirely, not partially used. I'd also check for bus-level errors like NACKs or timeout conditions.

2. **Range and plausibility checks.** Each physiological parameter should have defined valid ranges — both hard limits (e.g., a temperature can't be below 0°C or above 50°C in a living patient) and rate-of-change limits (a value can't jump by 20 units between two consecutive 1-second samples). These checks catch sensors that are drifting, stuck, or returning garbage while still passing a CRC.

3. **Redundancy and cross-checking where possible.** If there are two independent measurements of related parameters (e.g., heart rate derived from both an ECG and a pulse oximeter), they can be cross-validated. If they disagree beyond a threshold, that's a system-level error, not just a sensor error.

4. **State management, not just sample rejection.** A single bad sample is handled differently from a sensor that's been returning invalid data for 30 seconds. I'd implement a health state machine for each sensor: healthy → suspect (one or two bad readings) → degraded (persistent failures) → failed. The device's behavior changes based on the state — a suspect sensor might just have its data flagged, while a failed sensor triggers an alarm and possibly a mode change.

5. **Never display a false reading.** If the data can't be validated, the display shows "—" or "sensor error," not the last good value and not an extrapolated value. In some cases, showing the last known good value with a timestamp and a "stale data" indicator might be clinically useful, but it must be clearly marked as not current.

6. **Alarm and logging.** Any invalid data event should be logged with a timestamp for later analysis. If the invalid data rate exceeds a threshold, it should trigger an alarm so clinical staff know the sensor may be failing.

**The key architectural point** is that validation isn't a single check — it's a pipeline of checks at different levels, and the system needs to distinguish between "this sample is bad" and "this sensor is failing." The response to each is different.

**Possible follow-ups:**
- How would you handle the case where the sensor returns values that are within range but clearly wrong (e.g., a heart rate of 30 when the patient was just at 80)?
- How would you decide between showing "no data" versus showing the last valid reading with a staleness indicator?

---

## Q4: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** This is a classic design trade-off where both engineers have valid points, and the right answer depends on the specific characteristics of the protocol and the team's long-term maintenance situation. My role as the lead is to facilitate a decision based on evidence and requirements, not to simply pick a side.

**First, I'd reframe the discussion around the protocol's characteristics:**
- How many states are there, and how many transitions?
- Are the transitions mostly regular (every state can transition to most other states) or sparse (each state only transitions to a few others)?
- How often does the protocol change — is this a stable, well-defined spec or something that evolves frequently?
- Are there many conditional behaviors within a single state, or is each state's behavior fairly uniform?

**Second, I'd ask both engineers to articulate their concerns in terms of specific scenarios:**
- "Walk me through how you'd add a new state to each approach."
- "Walk me through how you'd debug a protocol violation in each approach."
- "How would you unit test each approach?"

**Third, I'd look at what the codebase already has.** If there's an existing pattern in the codebase, consistency matters. Introducing a second pattern for one protocol creates cognitive overhead for everyone who works on the code later.

**Fourth, I'd consider the team's experience.** If the team is very familiar with state machines and less so with table-driven design, that's a real cost — not because table-driven is harder, but because unfamiliar patterns lead to mistakes during the learning curve.

**My general guidance would be:**
- For protocols with fewer than ~10 states and mostly sparse transitions, a well-structured state machine (implemented as a table of function pointers or a switch with strict entry/exit discipline) is often clearer.
- For protocols with many states and dense transition matrices, or where the protocol is data-driven and likely to change frequently, a table-driven approach where the transition table is data rather than code can be more maintainable.
- A hybrid is often the best answer: a table that defines the legal transitions (for validation and documentation), with the actual state handling in functions.

**I'd also push for a concrete decision criterion:** rather than arguing abstractly, define what "better" means for this project — is it fewer bugs during initial development, easier debugging in the field, or faster feature additions over the next two years? Different priorities lead to different answers.

**Finally, I'd make sure the decision is documented** — not just the choice, but the reasoning, so that future team members understand why the pattern was chosen and what alternatives were considered.

**Possible follow-ups:**
- What if the protocol has a small number of states but very complex transition conditions — how does that affect your recommendation?
- How would you handle the situation where one engineer is clearly more senior and the other is more junior — does that change how you facilitate the decision?

---

## Q5: You're reviewing a colleague's firmware code that uses a watchdog timer that kicks in the main loop. The device occasionally resets during a lengthy calibration routine that takes 3 seconds. The colleague proposes increasing the watchdog timeout to 5 seconds. How would you guide them?

**Answer:** Increasing the watchdog timeout to accommodate a long operation is treating the symptom, not the cause — and in a medical device, it's the wrong instinct. The watchdog exists to detect that the system has stopped making progress. If a legitimate 3-second operation causes a reset, the problem is that the watchdog isn't being fed appropriately during that operation, not that the timeout is too short.

**My guidance would be:**

1. **First, understand what the watchdog is protecting against.** In a medical device, the watchdog is a last line of defense against firmware hangs, runaway loops, and stuck interrupts. If we simply extend the timeout to cover the worst-case legitimate operation, we also extend the time it takes to detect a genuine fault. A device that's hung for 5 seconds might be acceptable in some contexts, but in a monitoring device, that could mean missing critical events.

2. **The right pattern is to feed the watchdog at appropriate points during the long operation.** If the calibration routine has distinct phases — e.g., "apply stimulus," "wait for settling," "measure," "compute" — the watchdog should be kicked at the start of each phase or at regular intervals within the routine. This proves the system is still making progress without requiring the full 3 seconds to elapse before the watchdog is satisfied.

3. **I'd also look at why the routine takes 3 seconds.** Is it waiting on a sensor to stabilize? Is it performing a computation that could be optimized? Is it doing something that could be restructured? Sometimes the long operation itself is the problem — for example, if it's a blocking delay, it could be converted to a state machine that yields to other tasks between steps.

4. **I'd check whether the watchdog is being kicked in the main loop only.** If the calibration routine is blocking the main loop for 3 seconds, then the main loop can't kick the watchdog — that's the root cause. The fix is to either kick the watchdog within the calibration routine itself, or restructure the routine so it doesn't block the main loop.

5. **I'd also consider whether a windowed watchdog is appropriate.** A windowed watchdog requires that the kick happen within a specific time window — not too early and not too late. This prevents a stuck loop that happens to kick the watchdog at the right interval from masking a fault. If the device uses a windowed watchdog, the calibration routine needs to kick it within the window, which requires careful timing analysis.

6. **Finally, I'd document the decision.** The calibration routine's watchdog strategy should be documented in the design — why the routine takes as long as it does, where the watchdog is kicked, and what happens if the routine exceeds its expected duration. This is the kind of thing that comes up during regulatory review.

**The key principle:** the watchdog timeout should be set based on the maximum time the system should ever go without making progress — not the maximum time any legitimate operation takes. If those two numbers are in conflict, the operation needs to be restructured, not the watchdog weakened.

**Possible follow-ups:**
- How would you determine the appropriate watchdog timeout for a system that has both a fast control loop and a slow calibration routine?
- What if the calibration routine is genuinely uninterruptible and cannot be restructured — what are your options then?