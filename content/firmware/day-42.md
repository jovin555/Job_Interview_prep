# firmware — Day 42

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental issue here is that a blocking operation in any task can stall the scheduler, and a 100 ms flash erase would completely destroy a 1 ms deadline. I would start by questioning the assumption that the flash erase must block the CPU at all. Most modern MCUs have a flash controller that can perform erase operations in the background while the CPU continues executing from RAM or cache. If the hardware supports it, I'd structure the flash driver to initiate the erase and use an interrupt or polling flag to signal completion, allowing the sensor task to continue uninterrupted.

If the hardware doesn't support background erase, the next approach is to break the erase into smaller chunks — many flash controllers allow erasing by sector or page rather than the entire block at once. I'd interleave these smaller operations with the sensor reads, ensuring each chunk completes well within the 1 ms budget. This requires careful timing analysis: if a sector erase takes 5 ms, that's still too long, so I'd need to look at the actual hardware capabilities.

Another option is to use Zephyr's threaded flash API with a dedicated low-priority thread, but that only helps if the flash operation itself doesn't block the CPU. If it does, the scheduler can't run during the erase regardless of thread priorities. I'd also consider whether the flash write could be deferred — for example, buffering data in RAM and writing it during a period when the sensor task can tolerate a gap, or using a double-buffer scheme where one buffer is written to flash while the other is being filled.

Finally, I'd verify the actual timing constraints. Is the 1 ms sensor read truly hard real-time, or is there some tolerance? If the sensor has an internal FIFO that can buffer samples for a few milliseconds, a brief blocking period might be acceptable. I'd document the worst-case latency budget and ensure the design meets it with margin.

**Possible follow-ups:**
- How would you determine whether the sensor read is truly hard real-time versus having some tolerance?
- What Zephyr kernel primitives would you use to coordinate between the flash task and the sensor task?

---

## Q2: You're debugging a firmware issue where a device's flash write operations occasionally corrupt data in an unrelated memory region. The corruption is intermittent and only occurs when the device is under heavy load. How would you approach this?

**Answer:** This is a classic symptom of either a memory access violation or a hardware-level issue with the flash controller. I'd start by ruling out the most common software cause: a buffer overflow or out-of-bounds pointer write that happens to coincide with the flash operation. Under heavy load, timing changes can expose latent bugs — for example, a race condition where a buffer is being written while another task reads it, or a stack overflow that corrupts adjacent memory.

My first step would be to enable the MPU (Memory Protection Unit) if the MCU has one, configured to trap any access to the corrupted region. This would immediately tell me whether the corruption is from an illegal write or something else. I'd also enable the compiler's stack canary and check for stack overflow indicators.

If the MPU doesn't catch anything, I'd look at the flash driver itself. Some flash controllers have a limited number of write buffers, and under heavy load, a poorly implemented driver might write to the wrong address due to a race condition in the address/data register setup. I'd review the driver code for any shared state that isn't protected — for example, a global variable holding the current write address that could be modified by an interrupt.

Another angle is DMA. If the flash write uses DMA, a DMA descriptor or buffer that's being modified while the transfer is in progress could cause writes to the wrong location. I'd check whether the DMA descriptors are in cached memory and whether cache coherency is handled correctly.

Hardware-wise, I'd verify the power supply to the flash during heavy load. If the device is battery-powered and the flash write draws significant current, a voltage droop could cause marginal behavior. I'd also check the PCB layout — a ground bounce issue during high-current switching could cause spurious writes.

Finally, I'd try to reproduce the issue with instrumentation: logging the flash controller's state registers, the corrupted address, and the call stack at the time of corruption. If I can capture the exact sequence of events leading up to the corruption, that usually points directly to the root cause.

**Possible follow-ups:**
- How would you use the MPU to help diagnose this without changing the behavior of the system?
- What specific checks would you perform on the DMA configuration to rule out descriptor corruption?

---

## Q3: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core requirement is that invalid data must never be presented as valid — the system must fail safe. I'd design a multi-layer validation approach.

First, at the protocol level, every sensor read should be checked for CRC or checksum validity. If the sensor provides a CRC, a mismatch means the data should be discarded immediately, not retried indefinitely — a single retry might be reasonable, but repeated failures should trigger a different path.

Second, at the data level, I'd apply plausibility checks based on the physiological range of the parameter. For example, if the sensor measures heart rate, values outside 0–300 bpm are physically impossible and should be rejected. These bounds should be configurable and documented, derived from clinical requirements rather than arbitrary choices.

Third, I'd implement a redundancy or consistency check where possible. If the device has multiple sensors measuring related parameters, cross-validation can catch errors — for example, a sudden change in one parameter without a corresponding change in another might indicate a sensor fault.

When invalid data is detected, the system must decide how to respond. For a single bad sample, the typical approach is to hold the last valid reading and flag it as "stale" — the display should indicate that the value hasn't updated recently. If invalid data persists beyond a threshold (e.g., 3 consecutive failures or 5 seconds), the system should transition to a degraded mode: display "sensor fault" or "check sensor" rather than showing a potentially incorrect value. This aligns with the principle that it's better to show no data than wrong data.

I'd also implement a state machine for sensor health: normal → suspect (intermittent errors) → fault (persistent errors). The transition thresholds should be based on the clinical risk — for a critical parameter, the threshold for declaring a fault should be lower.

Finally, all invalid data events should be logged with timestamps for post-event analysis. This is important for both debugging and for regulatory traceability — if there's ever a question about whether the device displayed a false reading, the log provides evidence of what happened.

**Possible follow-ups:**
- How would you decide between holding the last valid reading versus displaying "no data" when a sensor fails?
- What criteria would you use to determine the threshold for transitioning from "suspect" to "fault" state?

---

## Q4: You're reviewing a colleague's firmware code that uses a watchdog timer that kicks in the main loop. The device occasionally resets during a lengthy calibration routine that takes 3 seconds. The colleague proposes increasing the watchdog timeout to 5 seconds. How would you guide them?

**Answer:** Increasing the watchdog timeout to accommodate a long operation is treating the symptom, not the cause. The real problem is that the watchdog is being kicked in the main loop, which means it's not actually monitoring whether the system is healthy — it's just monitoring whether the main loop is running. During the calibration routine, the system might be completely stuck in a loop and the watchdog would still be kicked if the kick happens before the routine starts.

The correct approach is to restructure the watchdog strategy so that it provides meaningful fault detection. There are a few options:

First, I'd ask whether the calibration routine can be broken into smaller steps, with the watchdog kicked between steps. This way, if the routine hangs partway through, the watchdog will fire. This is the preferred approach because it maintains tight fault detection while allowing the long operation to proceed.

Second, if the routine can't be broken up, I'd consider using a separate task or state to kick the watchdog during the calibration — but only if there's a way to verify progress. For example, the calibration routine could update a progress counter, and a separate watchdog task could check that the counter is advancing. If the counter stops advancing, the watchdog isn't kicked.

Third, I'd look at whether the watchdog is windowed. A windowed watchdog requires the kick to happen within a specific time window — not too early and not too late. This prevents the "kick in the main loop" pattern where the watchdog is kicked regardless of whether the system is actually functioning correctly.

I'd also question whether the calibration routine itself is safe to interrupt. If the calibration involves writing to external hardware or adjusting trim values, a reset mid-calibration could leave the device in an inconsistent state. In that case, the design should ensure that calibration is either atomic (with a recovery mechanism if interrupted) or resumable.

Finally, I'd emphasize that the watchdog timeout should be based on the maximum time the system should ever spend without making progress, not on the longest legitimate operation. If the calibration takes 3 seconds, the watchdog should be structured to detect a hang within that 3-second window, not extended to 5 seconds to accommodate it.

**Possible follow-ups:**
- How would you implement a progress-based watchdog kick for a long-running operation?
- What are the trade-offs between a windowed watchdog and a standard timeout watchdog?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** This is a classic design trade-off, and the right answer depends on the specific characteristics of the protocol and the team's long-term maintenance situation. I'd guide the team through a structured decision process rather than trying to pick a winner in the moment.

First, I'd ask them to map out the protocol's complexity. How many states are there? How many transitions? Are there many conditional paths based on data content, or is the flow relatively linear? For a protocol with fewer than 10-15 states and mostly straightforward transitions, a hand-coded state machine is often clearer. For a protocol with dozens of states and many cross-cutting conditions, a table-driven approach can reduce the code to data, making it easier to verify completeness and add new states without modifying control flow.

Second, I'd consider the failure modes. In a medical device, we need to be able to prove that every possible input is handled safely. A table-driven approach makes it easier to enumerate all transitions and verify that undefined transitions are handled explicitly — the table can be inspected for completeness. A hand-coded state machine can hide missing transitions in the default case of a switch statement.

Third, I'd think about who will maintain this code. If the team is small and the protocol is stable, readability matters most. If the protocol is expected to evolve — new states, new messages, new behaviors — the table-driven approach often wins because adding a new state is just adding a row to a table, not restructuring code.

I'd also suggest a hybrid approach: a state machine framework with a table-driven transition definition. The state machine logic (the engine) is written once and tested thoroughly, and the protocol-specific transitions are defined in a table. This gives the readability of a state machine with the maintainability of a table.

Finally, I'd recommend that the team prototype both approaches for a small subset of the protocol and evaluate them against concrete criteria: lines of code, time to implement a new state, ease of unit testing, and clarity of the code review. The decision should be based on evidence, not preference. If the team is still split after that, I'd make the call based on which approach better supports the safety requirements of the medical device — and I'd document the rationale so the decision is traceable.

**Possible follow-ups:**
- What specific criteria would you use to evaluate the two prototypes?
- How would you ensure that undefined transitions are handled safely in whichever approach is chosen?