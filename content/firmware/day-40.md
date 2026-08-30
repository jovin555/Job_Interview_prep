# firmware — Day 40

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** This is a classic priority inversion and blocking problem. The first thing I'd recognize is that the flash erase operation itself is the bottleneck — no amount of scheduling cleverness makes a 100 ms blocking operation disappear. So I'd address it at three levels:

**Architectural level:** Move the flash erase off the critical path entirely. Rather than having the lower-priority task perform the erase inline, I'd have it submit the erase request to a dedicated flash management module. That module would either use the flash controller's interrupt-driven completion mechanism (many MCUs support this) or, if the hardware requires blocking, I'd consider whether the erase can be deferred to a period when the sensor task isn't running — for example, during a known idle window.

**Scheduling level:** If the erase must happen while the sensor task is active, I'd look at whether the flash peripheral can be accessed via DMA or a hardware accelerator that frees the CPU. Some flash controllers allow you to initiate an erase and poll a status bit without stalling the CPU — though the bus may still be contended. If the MCU truly blocks, I'd consider whether the sensor data can be buffered during the erase window. A 1 ms period with a 100 ms erase means we'd need to buffer roughly 100 samples — that's often feasible with a DMA circular buffer feeding a larger RAM buffer, as long as the sensor peripheral itself can keep sampling without CPU intervention.

**Priority level:** I'd also examine whether the sensor task truly needs to run at 1 ms priority, or whether it could be driven by a hardware timer with DMA that only interrupts when a buffer fills. This decouples the sampling rate from the RTOS scheduler entirely.

The key principle is: don't try to schedule around a blocking operation — eliminate the blocking or move it out of the way.

**Possible follow-ups:**
- What if the MCU's flash controller doesn't support interrupt-driven erases and truly blocks the CPU?
- How would you size the DMA buffer to guarantee no data loss during the worst-case erase?

---

## Q2: You're reviewing a colleague's firmware code that uses a large number of global variables to share state between modules. The code works correctly in testing but is difficult to maintain and test. How would you approach refactoring this without introducing regressions?

**Answer:** I'd approach this as a gradual, test-supported refactoring rather than a big-bang rewrite. The first step is to understand the current data flow — I'd map out which globals are written by which modules and read by which modules, and identify the actual dependencies. This often reveals that many globals are only used within a single module and can be made static immediately with no risk.

For the remaining globals, I'd look for natural groupings — for example, a set of variables that all relate to sensor state, or to communication status. These become the basis for a struct or a module with explicit accessor functions. The key is to introduce the accessors first, before changing the underlying storage, so the call sites are updated incrementally.

I'd also introduce a test harness early. Even if the codebase doesn't have unit tests, I'd create a simple test that exercises the module's behavior at its boundaries — feeding known inputs and checking outputs. This gives a safety net for the refactoring. For a medical device, this is especially important because the behavior is safety-relevant.

One technique I'd use is to keep the global variable in place but route all access through functions. Once all access is through functions, I can change the storage to be module-local or instance-based without touching call sites. This two-phase approach — first encapsulate access, then change storage — minimizes the risk of regressions.

I'd also be careful about initialization order. Globals in C are zero-initialized, but if we move them into a struct that's dynamically initialized, we need to ensure the initialization happens before any module uses the data. This is a common source of subtle bugs during refactoring.

**Possible follow-ups:**
- How would you handle the case where two modules both write to the same global, and the order of writes matters?
- What role would code review play in this refactoring process?

---

## Q3: You're debugging a firmware crash that only occurs when a MicroPython script running on a constrained MCU performs a large memory allocation (e.g., creating a 10 KB bytearray). The system has 64 KB of RAM total. How would you approach diagnosing whether this is a genuine memory exhaustion issue or a fragmentation problem?

**Answer:** I'd start by instrumenting the memory subsystem to understand what's actually happening. MicroPython typically provides `gc.mem_free()` and `gc.mem_alloc()` — I'd add logging around the allocation to see how much free memory exists before the allocation, and whether the allocation succeeds or fails. If `mem_free()` reports more than 10 KB but the allocation still fails, that's a strong indicator of fragmentation.

The next step is to understand the heap layout. MicroPython uses a single heap for both Python objects and the interpreter's internal allocations. I'd check the heap's total size and how it's configured — often it's a fixed-size array defined at build time. If the heap is, say, 40 KB and the script has been running for a while, the heap may have many small free blocks scattered throughout, none of which is large enough for a contiguous 10 KB allocation.

To distinguish between exhaustion and fragmentation, I'd look at the pattern of allocations. If the script repeatedly allocates and frees objects of varying sizes, fragmentation is likely. If the script is allocating more total memory than the heap can hold, it's exhaustion. I'd also check whether the crash is a `MemoryError` exception (which MicroPython raises when allocation fails) or a hard fault — a hard fault during allocation could indicate heap corruption, which is a different problem entirely.

For the fix, if it's fragmentation, I'd look at whether the script can allocate the large buffer once at startup and reuse it, or whether the heap size can be increased. If it's exhaustion, I'd need to reduce the script's memory footprint — for example, by processing data in smaller chunks rather than buffering the entire dataset. In some cases, the right answer is to move the memory-intensive operation into a C module where memory can be managed more predictably.

**Possible follow-ups:**
- How would you determine the optimal heap size for a given MicroPython application?
- When would you decide that a particular operation should be implemented in C rather than MicroPython?

---

## Q4: You're implementing a bootloader for a medical device that must support dual-bank OTA updates with guaranteed rollback if the new firmware fails to validate. How would you design the bootloader's decision logic for selecting which bank to boot, and what validation checks would you perform before booting?

**Answer:** The core principle is that the bootloader must be simple, deterministic, and conservative — it should default to the known-good bank whenever there's any doubt. I'd structure the decision logic as a series of checks, each of which can result in "boot bank A," "boot bank B," or "enter recovery mode."

First, the bootloader needs a persistent record of which bank is current and which is pending. This is typically stored in a dedicated flash region or in the last sector of each bank. The record would include: a magic number to validate the record itself, the bank's version, a status field (e.g., "valid," "pending update," "update in progress," "update failed"), and a CRC of the record.

The decision logic would work like this:

1. **Read the boot record.** If the record is corrupt (bad magic or CRC), default to the bank with the highest version that passes validation, or enter recovery mode if neither validates.

2. **Check for a pending update.** If the status indicates an update is in progress, the bootloader checks whether the new bank is complete and valid. If the update was interrupted (e.g., power loss mid-write), the bootloader marks the update as failed and boots the previous bank.

3. **Validate the candidate bank.** Before booting any bank, the bootloader performs:
   - **CRC check** of the entire firmware image (or at least the vector table and critical sections).
   - **Vector table validation** — the initial stack pointer must be within RAM, and the reset handler must be within flash.
   - **Version check** — the new firmware must have a version equal to or newer than the current one (unless a downgrade is explicitly allowed).
   - **Signature verification** — for a medical device, I'd expect at least an HMAC or, ideally, an asymmetric signature to prevent unauthorized firmware.

4. **Boot the selected bank.** The bootloader sets a "booting" flag in the boot record, then jumps to the application. The application is responsible for clearing this flag once it has initialized successfully — this is the "confirmation" step. If the application fails to start (e.g., watchdog reset before clearing the flag), the bootloader sees the "booting" flag on the next reset and rolls back to the previous bank.

The rollback is guaranteed because the bootloader never erases the previous bank until the new bank has been confirmed by a successful boot. The confirmation mechanism — the application clearing the "booting" flag — is what makes the rollback automatic rather than requiring user intervention.

**Possible follow-ups:**
- How would you handle the case where the application boots but is functionally broken (e.g., it passes validation but crashes after a few minutes)?
- What additional considerations would you have for a device that must remain operational during the update (e.g., a medical monitor that can't be taken offline)?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** I'd start by reframing the question: this isn't about which pattern is "better" in the abstract, but about which is better for *this specific protocol* and *this team's context*. I'd ask both engineers to articulate what they mean by "complex" — is the protocol primarily sequential (many states, few transitions per state), or is it primarily combinatorial (many transitions, many conditions per transition)? That distinction often points to the right answer.

For a protocol that is mostly sequential — like a handshake with a clear progression of steps — a state machine is often more readable because it mirrors the protocol's natural flow. For a protocol with many cross-cutting transitions — where almost any state can transition to almost any other state based on various conditions — a table-driven approach can be more maintainable because the transition logic is data rather than code.

I'd also consider the team's familiarity with each pattern. If the team has deep experience with state machines and the protocol is well-suited to it, that's a strong argument. Conversely, if the team is more comfortable with table-driven approaches and the protocol is likely to evolve, that's also valid. The "best" pattern is the one the team can maintain correctly over the device's lifetime.

I'd suggest a concrete evaluation: have each engineer sketch out a small but representative portion of the protocol using their preferred approach — maybe 10 states and 20 transitions. Then the team can compare the two side by side on criteria like: how easy is it to trace a specific scenario? How easy is it to add a new state? How easy is it to verify that all transitions are handled? This makes the decision concrete rather than theoretical.

For a medical device, I'd also weigh testability and safety analysis. A state machine with explicit state variables is often easier to trace in a debugger and easier to reason about for safety certification. A table-driven approach can be more compact but may require tooling to visualize and verify the table's completeness. If the team can't agree, I'd lean toward the approach that makes the protocol's behavior most visible and auditable, because that's what matters for regulatory review.

Finally, I'd note that these aren't mutually exclusive — a hybrid approach is often effective, where the high-level protocol is a state machine and the transition conditions are table-driven. The goal is to make the code clear and maintainable, not to win an architectural argument.

**Possible follow-ups:**
- How would you handle the situation where one engineer's approach is clearly better for the protocol, but the other engineer is the one who will be maintaining it long-term?
- What role would the device's safety requirements play in your decision?