# firmware — Day 4

## Q1: You're designing a Zephyr RTOS-based system where a sensor task must wake every 100 ms to read data, but the device also needs to enter deep sleep between reads to conserve power. How would you structure the power management to ensure no data is missed?

**Answer:** I'd use Zephyr's power management subsystem, specifically the `pm_state` API, to coordinate sleep entry and exit. The key is to decouple the timing from the application task logic. I'd configure a hardware timer (e.g., a low-power RTC or LPTIM) as a wake-up source, set to fire every 100 ms. The sensor task would use `k_sleep()` with a timeout of `K_MSEC(100)`, but the actual wake-up would be driven by the timer interrupt, not the scheduler tick. 

Between sensor reads, the system would enter a deep sleep state (e.g., `PM_STATE_SUSPEND_TO_IDLE` or `PM_STATE_STANDBY`, depending on the MCU). The critical design point is ensuring the sensor's power rail is controlled by a GPIO so it can be shut off during sleep, and that the sensor's initialization time after power-up fits within the 100 ms window. I'd also use a retention register or backup SRAM to preserve the sensor's configuration state across sleep cycles, avoiding re-initialization overhead. The wake-up ISR should be minimal — just clear the timer flag and return — letting the scheduler resume the sensor task naturally.

**Possible follow-ups:**
- How would you handle the case where the sensor requires a warm-up time longer than the 100 ms interval?
- What if the device also needs to respond to an external event (e.g., a button press) while in deep sleep — how would you prioritize that wake-up source?

---

## Q2: You're debugging a firmware crash that only occurs when a MicroPython script running on a constrained MCU performs a large memory allocation (e.g., creating a 10 KB bytearray). The crash is a MemoryError, but the system has 64 KB of RAM total. How would you approach diagnosing whether this is a genuine memory exhaustion issue or a fragmentation problem?

**Answer:** First, I'd check the MicroPython heap size at build time — it's typically configured via `micropython_heap_size` in the linker script or board configuration. If the heap is set to, say, 32 KB, a 10 KB allocation might fail if other objects are already allocated. But fragmentation is a common culprit on constrained systems. 

I'd start by adding a periodic call to `gc.mem_free()` and `gc.mem_alloc()` to a debug output, logging the values around the allocation point. If `mem_free()` shows more than 10 KB available but the allocation still fails, fragmentation is likely. I'd then use `gc.dump()` to inspect the heap layout — it prints all allocated blocks and their sizes. If I see many small allocations scattered across the heap, that confirms fragmentation.

For a fix, I'd consider: (1) pre-allocating the bytearray at startup and reusing it, (2) increasing the overall heap size if the linker script allows, or (3) moving the allocation to a C module using `mp_obj_new_bytes()` with a pre-allocated buffer from a static pool, bypassing the MicroPython heap entirely. If the allocation is truly dynamic and unavoidable, I'd implement a fallback that defragments by calling `gc.collect()` before the allocation, or restructure the script to allocate the buffer earlier when the heap is less fragmented.

**Possible follow-ups:**
- When would you decide to drop down to C for a memory-intensive operation rather than trying to fix it in MicroPython?
- How would you profile the peak heap usage of a MicroPython script without adding logging code that changes the memory layout?

---

## Q3: You're implementing a bootloader for a medical device that must support dual-bank OTA updates with a guaranteed rollback if the new firmware fails to validate. How would you design the bootloader's decision logic for selecting which bank to boot?

**Answer:** I'd use a three-state decision model based on a small metadata structure stored in a dedicated flash page (or EEPROM) that persists across resets. The metadata would contain: (1) the active bank number (0 or 1), (2) a "pending update" flag, (3) a boot counter, and (4) a CRC of the firmware image in each bank.

The boot flow would be:
1. On reset, the bootloader reads the metadata. If the "pending update" flag is set, it means an OTA was initiated but not yet confirmed.
2. The bootloader computes the CRC of the firmware in the bank pointed to by "active bank" and compares it to the stored CRC. If it matches, it boots that bank.
3. If the CRC fails, or if the boot counter has exceeded a threshold (e.g., 3 attempts), the bootloader switches to the other bank and clears the "pending update" flag — this is the rollback.
4. After booting, the application must explicitly call a "confirm update" function (e.g., via a shared API or a magic value in RAM) within a timeout. If confirmed, the bootloader clears the "pending update" flag and resets the boot counter. If not confirmed (e.g., the new firmware crashes), the watchdog resets the device, and the boot counter increments — eventually triggering the rollback.

The key design trade-off is the boot counter threshold: too low risks rolling back a valid but slow-to-start image; too high risks bricking the device if the bad image always passes CRC but crashes after confirmation. I'd set the threshold to 3, and ensure the watchdog timeout is short enough that a crash causes a reset within seconds.

**Possible follow-ups:**
- How would you handle the case where both banks have valid CRCs but the device keeps rolling back — what debugging hooks would you add?
- What secure boot considerations would you add if this device needed to prevent unauthorized firmware from running?

---

## Q4: You're reviewing a colleague's firmware code that implements a state machine for a medical device's operational modes (idle, calibration, active monitoring, error). The state machine is implemented as a single switch-case inside a 200-line function, with state transitions scattered across multiple modules via global state variables. How would you approach refactoring this for maintainability and safety?

**Answer:** I'd propose a table-driven state machine pattern, which is more maintainable and testable, especially for medical devices where traceability matters. The refactoring would follow these steps:

First, I'd define a state table as a const array of structures, where each entry contains: the current state, the event that triggers a transition, the next state, and a function pointer to an action handler. This makes all transitions visible in one place — critical for safety review.

Second, I'd encapsulate the state variable within a single module (e.g., `state_machine.c`) with a private static variable, exposing only a `process_event(event_t event)` function. This eliminates the global state variable and prevents external modules from arbitrarily changing state.

Third, I'd break the 200-line function into smaller action handlers — one per state-event pair. Each handler would be a separate function with a single responsibility, making them unit-testable. For example, the "calibration" state's "timer_expired" event would call `handle_calibration_timer()`.

To avoid regressions, I'd write a test harness that exercises all state transitions from the original code, capturing the sequence of states and outputs. Then I'd run the same test suite against the refactored code. I'd also add assertions: for example, that invalid events in a given state return an error code rather than silently ignoring them, which is important for medical device safety.

**Possible follow-ups:**
- How would you handle state machines that have hierarchical or nested states (e.g., a "monitoring" state that has sub-states for different sensor modes)?
- What documentation would you require alongside the state table to satisfy a medical device design history file (DHF) audit?

---

## Q5: A junior engineer on your team has implemented a watchdog timer that kicks in the main loop, but the device occasionally resets during a lengthy calibration routine that takes 3 seconds. The engineer proposes increasing the watchdog timeout to 5 seconds. How would you guide them?

**Answer:** I'd start by acknowledging that increasing the timeout would fix the symptom, but I'd explain why it's not the right solution — especially for a medical device. A 5-second watchdog timeout means a fault could go undetected for nearly 5 seconds, which is unacceptable if the device is monitoring a patient's vital signs. The real issue is that the calibration routine is blocking the watchdog kick for too long.

I'd guide the engineer through these alternatives, in order of preference:

1. **Restructure the calibration routine** to be interrupt-driven or task-based, so it can yield periodically. For example, break the 3-second calibration into 100 ms chunks, kicking the watchdog between each chunk. This keeps the watchdog responsive while still completing calibration.

2. **Use a cooperative watchdog kick** — place the kick call inside a high-priority timer ISR that runs independently of the main loop. This ensures the watchdog is serviced even if the main loop is blocked, but I'd caution that this masks the fact that the main loop is stuck, so it should only be used if the blocking is intentional and safe.

3. **Switch to a windowed watchdog** if the MCU supports it. A windowed watchdog requires the kick to occur within a specific time window — not too early, not too late. This prevents the "kick in ISR" approach from masking a stuck main loop, because if the main loop misses its window, the watchdog resets.

If none of these are feasible, I'd consider increasing the timeout, but only after a risk analysis showing that a 5-second detection delay is acceptable for the specific failure modes. I'd also document the rationale in the design history file.

**Possible follow-ups:**
- How would you test that the restructured calibration routine actually kicks the watchdog at the right intervals under all conditions?
- What if the calibration routine is a black-box library that you cannot modify — how would you handle the watchdog in that case?