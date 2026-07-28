# firmware — Day 7

## Q1: You're designing a Zephyr RTOS-based system where a sensor task must wake every 100 ms to read data, but the device also needs to enter deep sleep between reads to conserve power. How would you structure the power management to ensure no data is missed?

**Answer:** The key challenge here is coordinating the wake-up timing with the sensor's own stabilization requirements. I'd approach this by first characterizing the sensor's power-up and stabilization latency — many sensors require tens of milliseconds after power-on before producing valid readings. This means the 100 ms interval isn't simply "sleep 100 ms, read, repeat."

I'd structure this using Zephyr's power management subsystem, specifically the `pm_state_force()` or system power management hooks. The approach would be:

1. Use a hardware timer (RTC or low-power timer) as the wake-up source, configured to fire slightly earlier than the 100 ms target to account for sensor stabilization time.
2. In the wake-up ISR or a dedicated power management callback, sequence the sensor power-up first, then allow the sensor to stabilize while the MCU remains in a lighter sleep mode (e.g., retention sleep with fast wake).
3. After stabilization, take the reading, process it, then power down the sensor and re-enter deep sleep.

The critical detail is that the MCU shouldn't enter deep sleep immediately after the sensor powers down — there's a window where the sensor is stabilizing that the MCU must remain awake. I'd implement this as a state machine within the power management handler: `WAKE -> POWER_SENSOR -> STABILIZE -> READ -> POWER_DOWN_SENSOR -> SLEEP`.

For the 100 ms period, I'd also consider using Zephyr's `k_timer` with a workqueue, but only if the workqueue handler can complete within the available time budget. If the sensor stabilization takes 30 ms and the read takes 5 ms, that leaves 65 ms of deep sleep — worthwhile for battery life.

**Possible follow-ups:** How would you handle the case where the sensor's stabilization time varies with temperature or age? What if the 100 ms interval is a hard real-time requirement and the sensor stabilization eats into that budget?

---

## Q2: You're debugging a firmware crash where a MicroPython script running on a constrained MCU causes a hard fault when performing a large memory allocation (e.g., creating a 10 KB bytearray). The system has 64 KB of RAM total. How would you approach diagnosing whether this is a genuine memory exhaustion issue or a fragmentation problem?

**Answer:** I'd start by instrumenting the MicroPython heap to understand its state. MicroPython exposes `gc.mem_free()` and `gc.mem_alloc()` at the Python level, but for a hard fault, the allocation likely failed at a lower level. I'd add a debug build that logs heap statistics before and after each allocation, or use MicroPython's `micropython.mem_info()` if available.

To distinguish exhaustion from fragmentation, I'd look at two things:
1. **Total free memory vs. largest contiguous block.** If `gc.mem_free()` shows 12 KB free but the largest free block is only 4 KB, that's fragmentation. MicroPython's garbage collector uses a mark-sweep collector that doesn't compact, so fragmentation is a real risk.
2. **Heap layout.** I'd dump the heap block list (MicroPython has `gc.dump_alloc()` or similar debug functions) to see the distribution of allocated and free blocks.

If it's fragmentation, the solution might be to pre-allocate the bytearray at startup (before other allocations fragment the heap), or to restructure the script to use smaller allocations. If it's genuine exhaustion, I'd look at what else is consuming memory — perhaps there's a memory leak in a C extension module or the script is holding references to large objects that prevent garbage collection.

I'd also check whether the hard fault is actually a MemoryError that wasn't caught, versus a genuine hardware fault from accessing invalid memory. MicroPython's `MemoryError` exception should be catchable, so if the script isn't handling it, that's a code issue. If it's a hard fault, it might be that the allocation itself is corrupting memory — perhaps a buffer overflow elsewhere is damaging the heap metadata.

**Possible follow-ups:** How would you add heap profiling to a production build without significantly impacting performance? What tools exist in MicroPython for tracking down memory leaks?

---

## Q3: You're implementing an I2C driver for a medical sensor that must read 12 bytes of data every 10 ms. The sensor sometimes holds the clock line low (clock stretching) for up to 5 ms. How would you configure the I2C peripheral and handle this timing constraint in firmware?

**Answer:** This is a classic real-time constraint problem — the 10 ms period means we have a tight budget, and 5 ms of clock stretching consumes half of it. I'd approach this by considering the trade-offs between polling, interrupt-driven, and DMA-based I2C.

First, I'd check the MCU's I2C peripheral capabilities. Many modern I2C controllers have built-in clock stretching support — they automatically wait for the clock to be released without requiring CPU intervention. If the peripheral handles this in hardware, the firmware just needs to set an appropriate timeout.

If the peripheral doesn't handle stretching automatically, I'd use interrupt-driven I2C with a timeout. The approach would be:
1. Configure the I2C in interrupt mode with a 6 ms timeout (slightly above the maximum 5 ms stretch).
2. Start the transaction, then yield to other tasks while waiting for the interrupt to complete.
3. If the timeout fires, abort the transaction and retry on the next cycle.

The critical consideration is whether the 10 ms period is a hard real-time requirement. If the sensor read must happen exactly every 10 ms, and clock stretching can consume 5 ms, that leaves only 5 ms for the rest of the system. In that case, I'd consider:
- Using DMA for the I2C transaction to minimize CPU involvement during the stretch period.
- Offloading the read to a dedicated I2C controller if the MCU has multiple.
- Pre-emptively starting the transaction slightly early to absorb the stretch within the 10 ms window.

I'd also implement a watchdog for the I2C bus — if the sensor holds the clock low beyond the maximum specified stretch time, the bus is likely stuck and needs recovery (toggle SCL to reset the slave).

**Possible follow-ups:** How would you handle the case where clock stretching causes the I2C transaction to overlap with the next scheduled read? What if the sensor's datasheet doesn't specify a maximum stretch time?

---

## Q4: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** This is a classic engineering trade-off where both positions have merit, so I'd guide the team through a structured decision process rather than picking a side.

First, I'd establish the system's requirements quantitatively: What is the maximum acceptable latency for responding to a message? What is the minimum time between messages? What is the CPU utilization budget for this protocol? Without numbers, the debate is theoretical.

Then I'd walk through the trade-offs with concrete data:
- **Polling** gives deterministic latency (bounded by the polling interval) but wastes CPU cycles when idle. It's simpler to debug and doesn't have interrupt nesting or priority inversion issues. It works well if the polling interval can be short enough to meet latency requirements without consuming too much CPU.
- **Interrupt-driven** gives lower average latency and better CPU utilization during idle periods, but introduces complexity: interrupt priorities, nesting, shared data protection, and potential for missed interrupts if the ISR takes too long.

I'd propose we prototype both approaches with the actual hardware and measure:
1. Worst-case response latency under maximum system load.
2. CPU utilization during typical operation.
3. Code complexity (lines of code, cyclomatic complexity).
4. Test coverage achievable for each approach.

If the latency requirement is, say, 1 ms and the CPU can poll every 500 µs with only 10% utilization, polling is the clear winner. If the requirement is 100 µs and the CPU can't poll that fast without consuming 80% of cycles, interrupts become necessary.

I'd also consider a hybrid approach: use interrupts for the initial message detection (waking the CPU from sleep or idle), then switch to polling for the message processing. This gives the responsiveness of interrupts with the determinism of polling for the critical path.

**Possible follow-ups:** How would you handle the case where the chosen approach fails during integration testing? What metrics would you use to validate the decision after implementation?

---

## Q5: You're reviewing a colleague's firmware code that implements a state machine for a medical device's operational modes (idle, calibration, active monitoring, error). The state machine is implemented as a single switch-case inside a 200-line function, with state transitions scattered across multiple modules via global state variables. How would you approach refactoring this for maintainability and safety?

**Answer:** This is a safety-critical concern for a medical device — scattered state transitions via global variables make it nearly impossible to verify that all state transitions are valid and that the device can't enter an invalid state. I'd approach the refactoring in stages, prioritizing safety and regression prevention.

**Stage 1: Document the current behavior.** Before changing anything, I'd work with the colleague to trace all possible state transitions and document them in a state transition table. This serves as the specification for the refactored code and helps identify any implicit or undocumented transitions.

**Stage 2: Encapsulate the state machine.** I'd create a dedicated state machine module with:
- A private state variable (no global access).
- A single entry point for state transitions (e.g., `sm_handle_event(event_t event)`).
- Validation logic that rejects invalid transitions (e.g., going from idle to error without passing through calibration).

**Stage 3: Replace the monolithic switch-case with a table-driven approach.** A transition table (array of structs mapping `{current_state, event, next_state, action_function}`) is more maintainable and easier to verify than a 200-line switch. It also makes it trivial to check for completeness — every state/event combination must be explicitly handled.

**Stage 4: Add safety mechanisms.** For a medical device, I'd include:
- A state timeout watchdog — if the device stays in a particular state too long, transition to a safe error state.
- An explicit "invalid transition" handler that logs the event and enters a safe state.
- Unit tests that verify every valid transition and confirm that invalid transitions are rejected.

Throughout this process, I'd emphasize that the refactoring should not change the external behavior — we're restructuring, not redesigning. I'd pair with the colleague on the refactoring to transfer knowledge and ensure they understand why the new approach is safer.

**Possible follow-ups:** How would you handle the case where the existing code has implicit state transitions (e.g., a timer callback that directly modifies the global state variable)? What testing strategy would you use to validate the refactored code against the original behavior?