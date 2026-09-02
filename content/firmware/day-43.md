# firmware — Day 43

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental issue is that a blocking flash erase in a lower-priority task can stall the scheduler, preventing the 1 ms sensor task from running. I'd approach this in layers.

First, I'd check whether the flash erase can be moved off the critical path entirely. Many modern MCUs have a dedicated flash controller that can perform erase operations with minimal CPU involvement, or the erase can be done via DMA. If the flash peripheral supports it, I'd configure the erase to run in the background and have the task wait on a completion interrupt rather than blocking.

If the hardware doesn't support background erase, I'd look at whether the flash erase can be broken into smaller operations — some flash controllers allow erasing by sector or page rather than the full block, which reduces the maximum blocking time. Even reducing a 100 ms block to 10 ms per sector makes the scheduling problem much more tractable.

Next, I'd examine the actual priority relationship. If the sensor task truly must run every 1 ms without exception, then any blocking operation that exceeds the task's period is unacceptable regardless of priority. The solution needs to be structural, not just a matter of adjusting priorities. Options include:

- Moving the flash erase to a separate thread that runs at a lower priority and accepts that it may be preempted mid-operation — but this only works if the flash controller supports suspend/resume, which many don't.
- Using a dedicated flash driver that performs the erase in small chunks, yielding to higher-priority tasks between chunks.
- If the erase genuinely cannot be interrupted, buffering sensor data during the erase window and processing it afterward — but this only works if the buffer can absorb 100 ms of data without overflow.

I'd also question whether the sensor task truly needs to run at 1 ms, or whether that's a derived requirement. Sometimes the actual requirement is "sample at 1 kHz with no more than X µs of jitter," which might be achievable with a hardware timer triggering DMA-based sampling directly into memory, bypassing the CPU and the RTOS scheduler entirely. That's often the cleanest solution for hard real-time sampling.

Finally, I'd verify the actual worst-case blocking time empirically rather than trusting the datasheet. Flash erase times can vary with temperature, supply voltage, and the number of program/erase cycles the device has undergone. I'd measure the real worst case and design against that, not the nominal value.

**Possible follow-ups:**
- How would you handle the case where the flash erase must complete atomically — for example, if a power loss mid-erase would corrupt the filesystem?
- How would you verify that your solution actually meets the 1 ms deadline under worst-case conditions?

---

## Q2: How would you approach implementing a firmware module that must handle graceful degradation when a critical sensor fails during operation, specifically for a device that monitors multiple physiological parameters where losing one parameter affects clinical decisions?

**Answer:** Graceful degradation in a medical monitoring context is fundamentally about risk management — the system must continue to be useful without ever becoming misleading. I'd start by defining what "degraded" means for each sensor and each combination of sensor failures, working with clinical input to understand which parameters are essential for safe operation versus which are supplementary.

The architecture would have three layers. First, a sensor abstraction layer that normalizes access to each physiological sensor and provides a consistent status model — healthy, suspect, failed, and recovering. Each sensor driver reports not just data but also confidence indicators: signal quality metrics, self-test results, communication integrity, and out-of-range detection.

Second, a fusion and validation layer that cross-checks readings where clinically appropriate. For example, if two parameters are physiologically correlated, a divergence between them might indicate one sensor is drifting rather than a genuine clinical event. This layer applies plausibility checks, rate-of-change limits, and redundancy logic where available.

Third, a user presentation layer that determines what to display and how. The key principle is that the system must never present a partial data set as if it were complete. If a parameter is unavailable, the display must clearly indicate "signal lost" or "sensor fault" rather than showing a stale or extrapolated value. The clinical user needs to know not just what the system is showing, but what it is *not* showing.

For the degradation logic itself, I'd implement a state machine per sensor with defined transitions. A sensor might go from "healthy" to "suspect" when it produces intermittent invalid readings, then to "failed" after a sustained loss of valid data. The transition thresholds need to balance sensitivity against false alarms — too aggressive and the system becomes a nuisance; too lenient and it might display unreliable data.

Critically, I'd design the system so that degradation is explicit and auditable. The device should log the onset of degradation, the criteria that triggered it, and any actions taken. For a medical device, this log becomes part of the device history record and may be needed for post-incident analysis.

I'd also consider what happens when the sensor recovers. The system shouldn't immediately trust a sensor that just came back online — it should require a stabilization period and possibly a self-check before restoring full confidence status.

**Possible follow-ups:**
- How would you decide which parameters are critical versus supplementary, and who should be involved in that decision?
- How would you handle the case where a sensor is producing plausible-looking but incorrect data — for example, a pressure sensor that has drifted but is still within its specified accuracy range?

---

## Q3: You're debugging a firmware issue where a device's flash write operations occasionally corrupt data in an unrelated memory region. The corruption is intermittent and only occurs when the device is under heavy load. How would you approach this?

**Answer:** This is a classic symptom of a memory corruption issue, and the "unrelated memory region" clue tells me the corruption is likely not a logical error in the flash write code itself — it's probably a memory access violation that happens to coincide with flash operations. I'd approach this systematically.

First, I'd try to characterize the corruption precisely. What address range is being corrupted? Is it always the same region, or does it vary? What pattern does the corruption take — is it a single byte, a word, or a block? Is the corrupted data always the same value, or does it vary? This information narrows down the possible causes significantly.

The most likely culprits, in order of probability, are:

**Stack overflow.** If a task or ISR stack grows into an adjacent memory region, writes to that region will corrupt whatever lives there. Flash operations often involve large local buffers or deep call chains, which increases stack usage precisely when flash writes occur. I'd check the linker map to see what lives adjacent to the suspected stack regions, and I'd enable stack overflow detection if the toolchain supports it.

**DMA descriptor or buffer misconfiguration.** If a DMA channel is configured with a buffer that overlaps other memory, or if the DMA descriptor table is corrupted, the DMA controller can write to arbitrary locations. Flash writes often use DMA, so a misconfigured DMA transfer could be the direct cause.

**Use-after-free or dangling pointer.** If some code path frees a buffer and then writes to it later, the memory may have been reallocated for another purpose. Under heavy load, the heap is more active, so the window for this type of bug widens.

**Interrupt-related reentrancy.** If a flash write routine is interrupted and the ISR also accesses the same memory, you can get corruption that only appears under specific timing conditions.

To isolate the cause, I'd use several techniques. First, I'd enable the MPU (Memory Protection Unit) if the MCU has one, configured to trap access to the corrupted region. This would turn an intermittent corruption into a deterministic fault that I can catch in the debugger. Second, I'd use the toolchain's memory poisoning features — filling freed heap blocks with a known pattern and checking for unexpected writes. Third, I'd add watermark patterns around suspected stack regions and check them periodically.

I'd also look at the flash driver implementation itself. Some flash controllers require specific register sequences or have timing constraints that, if violated, can cause bus errors that manifest as memory corruption. I'd verify that the driver is correctly handling wait states, and that any caching is properly invalidated after flash operations.

Finally, I'd consider whether the corruption is actually in the flash memory itself or in RAM. If the corrupted data is in flash, the cause is different — possibly a programming voltage issue or a violation of the flash controller's timing specifications. If it's in RAM, the cause is more likely a software bug.

**Possible follow-ups:**
- How would you use the MPU to help isolate this type of issue, and what are the limitations of that approach?
- What information would you want to capture in a crash log to help diagnose this if it occurred in the field?

---

## Q4: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** This is a classic engineering trade-off, and the right answer depends on the specific requirements of the system rather than on which approach is "better" in the abstract. My role as the lead is to structure the discussion so the team evaluates the options against concrete requirements rather than getting stuck in ideological positions.

I'd start by reframing the question: what are the actual requirements for this communication protocol? Specifically, I'd want to understand:

- What is the maximum latency allowed between data arrival and processing?
- What is the data rate and burst characteristics?
- What is the worst-case time the CPU can be unavailable to service this protocol?
- What other real-time tasks are running, and what are their deadlines?
- Is the protocol master-slave or peer-to-peer? Is it polled by our device, or does the remote device initiate communication?

Once we have these requirements quantified, the choice becomes much clearer. Polling is genuinely simpler and more predictable in terms of worst-case timing — you know exactly when the protocol is serviced because you control the poll interval. It's also easier to debug and test. However, polling wastes CPU cycles when there's no data, and it can miss data if the poll interval is too long relative to the data arrival pattern.

Interrupt-driven approaches are more responsive and efficient when data arrives sporadically, but they introduce timing variability — an interrupt can arrive at any point in the main loop, potentially preempting a timing-critical section. They also require careful handling of shared data between ISR context and task context.

I'd ask the team to work through a concrete analysis: given the protocol's data rate and the system's other timing requirements, what is the worst-case CPU utilization for each approach? What is the worst-case latency for each? What is the interrupt latency budget, and can the system tolerate the jitter that interrupts introduce?

I'd also raise a third option that often breaks the deadlock: DMA with interrupt completion notification. The DMA controller handles the byte-level transfer without CPU involvement, and the interrupt only fires when a complete message has been received. This gives the responsiveness of interrupts with much lower CPU overhead, and it reduces the interrupt rate from per-byte to per-message.

If the team is still deadlocked after this analysis, I'd suggest prototyping both approaches with the actual hardware and measuring the real timing characteristics. Data beats opinion. I'd ask each engineer to implement their approach for a specific message pattern and then we'd compare measured latency, CPU utilization, and code complexity.

Finally, I'd remind the team that this decision should be documented with the rationale, because it will likely be revisited as the system evolves. The decision should be based on requirements and data, not on personal preference.

**Possible follow-ups:**
- What if the requirements genuinely support both approaches — how would you make the final call?
- How would you handle the situation where one engineer refuses to accept the data from the other's prototype because they believe the test conditions were unfair?

---

## Q5: You're reviewing a colleague's firmware code that implements a state machine for a medical device's operational modes (idle, calibration, active monitoring, error). The state machine is implemented as a single switch-case inside a 200-line function, with state transitions scattered across multiple modules via global state variables. How would you approach refactoring this for maintainability and safety?

**Answer:** This is a safety-critical refactoring, so my approach would prioritize correctness and verifiability over elegance. The current design has several problems: the state machine logic is centralized but the state transitions are scattered, which means you can't reason about the system's behavior by reading one place; global state variables create hidden dependencies between modules; and a 200-line switch-case is difficult to test exhaustively.

Before touching any code, I'd want to understand the current behavior completely. I'd ask the colleague to walk me through the state machine, and I'd document every state, every event that can trigger a transition, every guard condition, and every action taken on entry to and exit from each state. This documentation becomes the specification against which I'll verify the refactored code.

The refactoring itself would follow a structured approach. First, I'd define a clear state transition table — a data structure that maps (current state, event) pairs to (next state, action) pairs. This table-driven approach has several advantages: it makes all transitions visible in one place, it's easy to verify against the documented specification, and it's straightforward to add validation that rejects undefined transitions.

Second, I'd encapsulate the state variable so it can only be modified through the state machine's transition function. No module should be able to set the state directly — they can only post events. This eliminates the scattered global state assignments.

Third, I'd define a clean event interface. Each module that needs to trigger a transition calls something like `post_event(device_state_machine, EVENT_SENSOR_FAILURE)` rather than directly manipulating state. The state machine module owns the transition logic and decides whether the event is valid in the current state.

Fourth, I'd separate the state machine logic from the actions. The transition table determines *what* happens (which state to enter), but the actual work — starting calibration, activating alarms, logging errors — should live in separate handler functions. This keeps the state machine itself simple and testable, while the action handlers can be as complex as needed.

For safety-critical validation, I'd add assertions that catch invalid transitions in development. If an event arrives that isn't valid in the current state, that's a bug, and the system should trap it rather than silently ignoring it or, worse, making an undefined transition.

I'd also think about how to make the state machine testable. With a table-driven design, I can write a test that iterates through every (state, event) pair and verifies that the transition is either valid and correctly handled, or explicitly rejected. This exhaustive testing is much harder with a switch-case implementation.

Finally, I'd work with the colleague rather than simply rewriting their code. The refactoring is an opportunity to transfer knowledge and build consensus on the design approach. I'd explain the reasoning behind each change and invite their input on the transition table, since they have the deepest knowledge of the current behavior.

**Possible follow-ups:**
- How would you handle the case where the current behavior has undocumented transitions that only occur under specific fault conditions?
- How would you verify that the refactored state machine behaves identically to the original in all valid scenarios?