# firmware — Day 14

## Q1: How would you approach designing a firmware architecture for a device that must support both deterministic real-time control (e.g., a 1 kHz motor control loop) and non-real-time tasks like configuration management and data logging, where the non-real-time tasks must never cause jitter in the control loop?

**Answer:** The core principle is strict temporal isolation between the real-time control path and everything else. I would structure this as a priority-based preemptive RTOS (like Zephyr) with the control loop running in the highest-priority thread, or potentially in a timer ISR if the control period is tight enough that thread scheduling overhead is a concern.

The control loop thread should be designed to be completely self-contained: it owns its sensor data, its control state, and its actuator outputs. It should not call any blocking APIs, should not perform any I/O that can stall (no flash writes, no mutex waits on shared resources with lower-priority threads), and should have its stack and data structures statically allocated and cache-aligned to avoid contention.

For communication between the control loop and lower-priority tasks, I would use lock-free patterns where possible — for example, a single-producer/single-consumer ring buffer with volatile index variables, or a double-buffer where the control loop writes to one buffer while the logging task reads from the other, with an atomic flag to indicate which buffer is current. If a mutex is unavoidable, the control loop should use a non-blocking `try_lock` and skip the update if the lock is held, rather than blocking.

The non-real-time tasks (configuration, logging, UI) run at lower priorities. They must be designed so their worst-case execution time doesn't matter — they can be preempted at any point by the control loop. The key is that they never hold a resource the control loop needs, and they never disable interrupts for extended periods.

For the logging path specifically, I would use DMA for any peripheral transfers so the CPU isn't tied up, and I would buffer data in RAM, writing to flash only when a full page/sector is ready, so flash write latency never intersects with the control period.

**Possible follow-ups:**
- How would you handle a situation where the control loop occasionally needs to read a calibration value that is stored in flash and updated by the configuration task?
- What Zephyr kernel configuration options would you set to ensure the scheduler itself doesn't introduce jitter?

---

## Q2: You're debugging a firmware issue where a device communicates with a sensor over SPI, and the sensor occasionally returns corrupted data — but only when the device is running on battery power, not when connected to a bench supply. How would you approach this?

**Answer:** This is a classic power-integrity or grounding issue manifesting as a digital communication problem. The first thing I'd do is confirm the symptom is reproducible and characterize it: does it happen at a specific battery voltage, under specific load conditions, or after a specific event (like a motor starting or a radio transmitting)?

The fact that it works on a bench supply but not battery strongly suggests the issue is either:
1. **Power supply noise/ripple** — the battery has higher internal impedance, and when the device draws current (especially pulsed loads), the supply voltage dips or rings, potentially violating the sensor's or MCU's supply tolerance.
2. **Ground bounce or return-path issues** — the SPI signals reference ground, and if the ground path between the MCU and sensor has high impedance, current transients create voltage differences that corrupt logic levels.
3. **Electromagnetic interference** — the battery leads or the device enclosure may change the antenna characteristics, making the SPI bus more susceptible to radiated noise.

My debugging approach would be systematic:
- **Scope the power rails** at the MCU and sensor with a differential probe, looking at both DC level and ripple during SPI transactions. Compare battery vs. bench supply.
- **Scope the SPI lines** (SCLK, MOSI, MISO, CS) with the same trigger conditions, looking for signal integrity issues — ringing, slow edges, or level shifts.
- **Check the sensor's supply pin** specifically — if it has its own regulator or decoupling, verify it's adequate.
- **Test with a fresh battery vs. a partially discharged one** — if the issue worsens as voltage drops, it points to a margin problem.
- **Add a large bulk capacitor** near the battery input as a quick test — if the issue disappears, it confirms a supply impedance problem.

Once the root cause is identified, the fix might be: adding/improving decoupling, increasing the bulk capacitance, adding a ferrite bead or LC filter on the SPI lines, improving the ground plane, or adjusting SPI timing (slower clock, longer setup times) to give more margin.

**Possible follow-ups:**
- What if the corruption only happens when a specific peripheral (like a motor or heater) is active — how would that change your approach?
- How would you determine whether the issue is on the MCU side (bad data being sent) or the sensor side (bad data being received)?

---

## Q3: How would you approach implementing a firmware module that must handle graceful degradation when a critical sensor fails during operation, specifically for a device that monitors multiple physiological parameters where losing one parameter affects clinical decisions?

**Answer:** Graceful degradation in a medical context is about balancing three things: patient safety, clinical usability, and honest communication of device state. The design must be driven by a clinical risk assessment — for each sensor failure, what is the clinical impact, and what is the acceptable fallback behavior?

My approach would start with a failure-mode analysis for each sensor: what failure modes exist (no response, out-of-range values, erratic readings, stuck values), how to detect each one (timeouts, range checks, rate-of-change checks, redundant measurements), and what the clinical response should be (continue with reduced functionality, switch to a secondary sensor, or halt monitoring and alarm).

The firmware architecture would use a **health-status aggregator** — a central module that tracks the state of each sensor (healthy, degraded, failed) and the overall device state. Each sensor driver reports its status through a standardized interface, and the aggregator applies the clinical rules to determine the device's operational mode.

For the degraded mode itself:
- **Clear user notification** — the UI must show exactly what is lost and what is still available, using distinct visual/audible alarms that are different from critical alarms.
- **Data integrity** — any data recorded while a sensor is degraded must be tagged with the device state, so clinicians reviewing the data later know it was collected under degraded conditions.
- **Automatic recovery** — the firmware should periodically attempt to reinitialize the failed sensor (with appropriate backoff), and if it recovers, verify it's producing valid data before restoring full functionality.
- **No silent failures** — the device must never present degraded data as if it were normal. If a parameter is unavailable, it should be displayed as "unavailable" or "—", not as a stale or estimated value.

A key design principle is that the degradation logic should be **data-driven and configurable**, not hard-coded. Clinical teams may want to change thresholds or fallback behaviors based on new evidence, and that should be possible through a configuration update rather than a full firmware change.

**Possible follow-ups:**
- How would you handle the case where two sensors measure related parameters and one fails — should the device estimate the failed parameter from the other?
- How would you test the degradation paths to ensure they work correctly under all failure combinations?

---

## Q4: You're implementing a bootloader for a medical device that must support dual-bank OTA updates with guaranteed rollback if the new firmware fails to validate. How would you design the bootloader's decision logic for selecting which bank to boot, and what validation checks would you perform before booting?

**Answer:** The bootloader's decision logic is essentially a state machine with three inputs: the current boot bank, the validity of each bank's firmware image, and the reason for the current reset (power-on, watchdog, software-triggered). The goal is to always boot into a known-good image, even if that means reverting to the previous version.

**Validation checks before booting:**
1. **CRC or hash verification** — compute a CRC32 or SHA-256 over the entire firmware image and compare against a stored value. This catches corruption during transfer or storage.
2. **Image header validation** — verify the image header contains a valid magic number, version, and size that matches the actual image.
3. **Signature verification** — for a medical device, the image should be signed (e.g., ECDSA or RSA), and the bootloader verifies the signature using a public key stored in protected flash. This ensures the image came from the manufacturer and wasn't tampered with.
4. **Application self-test** — after jumping to the new image, the application runs a power-on self-test (POST) and reports success back to the bootloader (via a flag in shared RAM or a reserved flash region). If the POST fails or times out, the bootloader reverts on the next reset.

**Decision logic:**
- On power-up, the bootloader checks the "update pending" flag. If an update was in progress, it checks whether the new image is fully received and valid.
- If the new image is valid, it sets the boot bank to the new bank, clears the pending flag, and boots.
- If the new image is invalid (CRC fail, signature fail, or incomplete), it reverts to the previous bank, sets a "rollback occurred" flag for the application to report, and boots the old image.
- If the application was running and a watchdog reset occurs, the bootloader should check whether the application had set a "I'm alive and healthy" flag. If not, it may indicate the new firmware is unstable, and the bootloader should revert.

**Key design considerations:**
- **Atomicity** — the bank selection flag must be written atomically (e.g., a single flash word) so a power loss during the update can't leave the system in an undefined state.
- **Power-loss safety** — the update process must be resumable or restartable. If power is lost mid-update, the bootloader should detect the incomplete image and either wait for a new update or revert.
- **Rollback counter** — limit the number of rollbacks to prevent a boot loop between two bad images. After N failed attempts, the bootloader should enter a recovery mode that requires a wired connection or explicit user action.
- **Secure boot chain** — ideally, the bootloader itself is protected (read-only, write-protected flash), and the chain of trust extends from the bootloader to the application, and potentially to configuration data.

**Possible follow-ups:**
- How would you handle the case where the new firmware passes all validation checks but is functionally broken (e.g., it boots but crashes after 10 minutes)?
- What if the device loses power during the flash erase of the bank that contains the current running image — how do you ensure you don't brick the device?

---

## Q5: A junior engineer on your team has implemented a firmware module that uses a global flag to signal between an ISR and a main-loop task. The code works in testing, but you're concerned about correctness and maintainability. How would you guide them toward a better design?

**Answer:** This is a common pattern that works in simple cases but has subtle correctness issues. I'd start by acknowledging that the global flag approach is understandable — it's simple and works for a single flag with a single consumer. But I'd walk through the specific problems:

**Correctness issues:**
- If the flag is read and cleared in the main loop, there's a race condition: the ISR could set the flag between the read and the clear, and the event would be lost.
- If the flag is a multi-byte type (e.g., a 32-bit integer on an 8-bit MCU), reading it in the main loop while the ISR writes it could result in a torn read.
- The `volatile` keyword is necessary but not sufficient — it prevents compiler reordering but doesn't provide atomicity or memory barriers.
- If the system later moves to an RTOS, the same pattern with a shared variable between tasks needs additional synchronization.

**Better alternatives, in order of preference:**
1. **For a single event flag:** Use the RTOS primitive designed for this — a binary semaphore or an event flag group. The ISR gives the semaphore, and the task takes it. This handles the race condition, provides atomicity, and integrates with the scheduler (the task can block until the event occurs instead of polling).
2. **For data transfer:** Use a proper ring buffer (single-producer/single-consumer) with atomic index updates. The ISR writes data and advances the write index; the task reads and advances the read index. The indices should be declared `volatile` and updated in the correct order (write data, then update index).
3. **For multiple events:** Use an event flag group or a message queue, depending on whether you need to signal "something happened" or pass data along with the event.

I'd also emphasize the maintainability angle: a global flag is a form of shared state that makes the code harder to test, harder to reason about, and harder to extend. If a second ISR needs to signal the same task, or if the task needs to wait on multiple events, the global flag approach doesn't scale.

I'd suggest they refactor incrementally: first, replace the flag with a binary semaphore (minimal change, immediate correctness improvement), then, if there's data to pass, introduce a ring buffer. I'd also recommend they write a small unit test that exercises the ISR-to-task path with a stress loop to verify no events are lost.

**Possible follow-ups:**
- What if the system is bare-metal (no RTOS) — how would you handle ISR-to-main-loop communication without a semaphore?
- How would you test for the race condition you described, given that it may only manifest under specific timing conditions?