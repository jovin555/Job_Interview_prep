# firmware — Day 30

## Q1: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core principle here is that in a medical monitoring context, the cost of a false reading is fundamentally different from the cost of no reading — and the firmware must be designed around that asymmetry. I'd structure the approach in layers.

First, at the data acquisition layer, I'd validate every sample before it enters the processing pipeline. This means checking CRC or checksum where the protocol supports it, verifying that values fall within physically plausible ranges (not just the sensor's electrical range, but what's physiologically possible for the parameter being measured), and checking for consistency with recent history — for example, a heart rate that jumps from 70 to 200 in a single sample might be real, but a jump to 400 is almost certainly an artifact.

Second, I'd implement a redundancy or voting scheme where appropriate. If the sensor provides multiple measurements per reporting interval, I'd use median filtering or outlier rejection rather than simple averaging, since a single outlier can skew an average. For critical parameters, I'd consider whether a second independent measurement path exists — even a less precise one — that could serve as a cross-check.

Third, I'd design the state machine to distinguish between "sensor reading valid," "sensor reading questionable," and "sensor failed." The device must never display a questionable reading as if it were valid. Instead, it should display the last known valid reading with a clear indicator that data is stale, or display "reading unavailable" with an alarm. The key is that the clinician must always know the confidence level of what they're seeing.

Finally, I'd think about persistence and trend analysis. A single invalid sample shouldn't trigger an alarm, but a pattern of invalid samples — say, 3 out of the last 5 — should escalate to a device fault indication. The firmware should track error rates and distinguish between a sensor that occasionally glitches and one that is degrading or failing.

**Possible follow-ups:**
- How would you decide between displaying the last valid reading versus displaying "no data" when a sensor reading fails validation?
- How would you handle the case where the sensor returns values that are individually plausible but collectively inconsistent (e.g., heart rate and oxygen saturation that don't correlate physiologically)?

---

## Q2: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** This is a classic priority inversion problem with a blocking resource, and the first thing I'd do is question the assumption that the flash erase must block for 100 ms in the first place. Most modern MCU flash controllers support some form of background or interruptible erase, or at minimum allow the erase to be paused and resumed. If the hardware supports it, I'd use a state machine that erases in small chunks — say, 1 ms at a time — yielding to the higher-priority task between chunks. This turns a 100 ms blocking operation into 100 smaller operations that each fit within the scheduling budget.

If the flash controller doesn't support interruptible erase, I'd look at whether the erase can be moved to a different memory type — for example, external SPI flash with its own controller that doesn't block the CPU, or a separate flash bank that can be erased while the main bank is executing. Many MCUs with dual-bank flash allow erasing one bank while executing from the other.

If neither option is available, I'd consider whether the sensor task can tolerate the 100 ms gap. A 1 ms sensor task that misses one sample might be acceptable if the data is oversampled or if the missing sample can be interpolated. But for a medical device, I'd need to verify this against the clinical requirements — some parameters genuinely need every sample.

Finally, I'd look at the Zephyr scheduling configuration itself. The sensor task should be a high-priority preemptive thread, and the flash operation should run in a lower-priority thread. If the flash erase is truly blocking and unavoidable, I'd ensure the sensor task's priority is high enough that it preempts the flash task the moment the erase completes, and I'd measure the actual worst-case latency rather than assuming it's acceptable. I'd also consider whether the sensor data could be buffered in a DMA ring buffer during the erase window, so no samples are lost even if the CPU is blocked.

**Possible follow-ups:**
- How would you measure and verify the actual worst-case latency introduced by the flash erase?
- What if the sensor data cannot tolerate any gaps — how would you guarantee zero sample loss?

---

## Q3: How would you approach designing a firmware architecture for a device that must support field-updatable firmware where the update image is delivered over an unreliable wireless link, and the device cannot be returned to the factory if an update fails?

**Answer:** The fundamental requirement here is that the device must remain functional regardless of what happens during the update process. I'd design around three pillars: a robust bootloader, a resilient download mechanism, and a clear recovery path.

For the bootloader, I'd use a dual-bank approach with a dedicated bootloader in protected flash. The bootloader's only job is to validate and launch one of two application images. Each image has a header containing a CRC or hash, a version number, and a validity flag. The bootloader checks the active image's validity flag and CRC before launching it; if either fails, it falls back to the other bank. The application itself can mark itself as "valid" only after it has successfully initialized all critical subsystems and run for a defined period without a reset — this prevents a boot loop where a faulty image passes CRC but crashes immediately.

For the download mechanism, I'd design the update as a series of small, independently verifiable chunks rather than one monolithic image. Each chunk has a sequence number, a CRC, and is acknowledged individually. The device stores received chunks in a staging area — either in the inactive flash bank or in external storage — and can resume from the last acknowledged chunk if the link drops. This makes the update resilient to intermittent connectivity. The device should also validate the complete image before committing it to the inactive bank, and only then flip the boot flag.

For the recovery path, I'd ensure the device can always revert to the last known-good image. If the new image fails validation at boot, the bootloader automatically boots the previous image. If the device boots the new image but then crashes repeatedly, a watchdog or a boot counter in the bootloader detects the instability and reverts. The device should also have a failsafe mode — perhaps a minimal recovery firmware in protected flash — that can accept a new update even if both application banks are corrupted.

I'd also think about the user experience: the device should clearly indicate update progress and status, and should never appear "dead" during an update. The update should be atomic from the user's perspective — either the device is running the old version, or it's running the new version, never a partial state.

**Possible follow-ups:**
- How would you handle the case where the device loses power mid-update, after some chunks are written but before the image is complete?
- How would you prevent a malicious or corrupted update image from being accepted?

---

## Q4: You're reviewing a colleague's firmware code that uses a large number of global variables to share state between modules. The code works correctly in testing but is difficult to maintain and test. How would you approach refactoring this without introducing regressions?

**Answer:** Refactoring a working system that has grown organically is a delicate operation — the goal is to improve structure without changing behavior. I'd approach this in phases, with verification at every step.

First, I'd establish a behavioral baseline. Before changing anything, I'd make sure there are comprehensive tests — ideally automated, but at minimum a documented manual test procedure — that exercise all the major functionality. For a medical device, this would include the normal operating paths, error paths, and edge cases. The tests don't need to be perfect; they need to be good enough to catch regressions.

Second, I'd map the data flow. I'd go through each global variable and document: which modules write to it, which modules read it, when in the execution sequence it's modified, and what invariants must hold. This is often the most revealing step — it frequently turns out that some globals are written by multiple modules at unpredictable times, which is a latent bug even if it hasn't manifested yet.

Third, I'd group related globals into cohesive structures. Rather than having `sensor_temp_raw`, `sensor_temp_filtered`, `sensor_temp_valid`, and `sensor_temp_timestamp` as separate globals, I'd create a `sensor_data_t` struct that holds them together. This is a low-risk change that immediately improves clarity and makes it easier to reason about the data as a unit.

Fourth, I'd introduce accessor functions or module boundaries. Instead of modules reading and writing globals directly, I'd define a small API — for example, `sensor_get_temperature()` and `sensor_set_temperature_valid(bool)`. This gives a single point of control where invariants can be enforced and where future changes (like adding mutex protection) can be made without touching every call site.

Fifth, and only after the above steps, I'd consider which globals truly need to be global versus which can be encapsulated within a module. Some state is genuinely system-wide and belongs in a shared context; other state is only used by one module and should be made static to that module.

Throughout the process, I'd run the test suite after each small change, not after a large batch of changes. If a regression appears, it's much easier to isolate when the change set is small. I'd also involve the original author in the review — they likely have context about why certain design decisions were made, and they'll be more receptive to changes they understand.

**Possible follow-ups:**
- How would you prioritize which globals to tackle first?
- What if the codebase has no existing tests — how would you establish a baseline before refactoring?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** When two senior engineers have a genuine technical disagreement, the worst thing I can do is pick a side based on seniority or force a compromise that satisfies neither. The right approach is to reframe the discussion around the actual requirements and let evidence drive the decision.

First, I'd ask both engineers to articulate the specific constraints that matter for this protocol: What is the worst-case latency requirement for receiving a message? What is the maximum acceptable CPU utilization? What is the message size and arrival pattern — is it a steady stream, or bursty? What happens if a byte is missed — is there a retry mechanism, or is data lost? These questions move the discussion from "polling vs. interrupts" in the abstract to "what does this specific protocol need?"

Second, I'd ask for concrete numbers. The polling advocate should estimate the worst-case polling interval needed to meet the protocol's timing requirements, and the CPU cost of polling at that rate. The interrupt advocate should estimate the interrupt rate, the time spent in the ISR per interrupt, and the impact on other time-critical tasks. If the protocol has a 1 ms response requirement and the polling loop runs at 10 kHz, polling might be perfectly adequate and simpler. If the protocol has a 100 µs response requirement, polling at that rate might consume too much CPU.

Third, I'd consider the system context. What else is running on this MCU? If there's a 1 kHz control loop that must not be disturbed, an interrupt-driven approach that fires at high rates could introduce jitter. On the other hand, if the CPU is mostly idle, polling might waste cycles that could be used for other tasks. I'd also consider the development and maintenance cost — polling is often easier to debug because the execution is deterministic, but interrupt-driven code is more scalable for complex protocols.

Fourth, I'd look for a hybrid approach that might satisfy both concerns. For example, a DMA-based solution with a completion interrupt gives the responsiveness of interrupts without per-byte interrupt overhead. Or a polling approach with a hardware timer that triggers a poll at a fixed interval can give predictable timing without a tight loop.

Finally, I'd ask the team to prototype the critical path — just the receive path, not the full implementation — and measure the actual worst-case latency and CPU usage for each approach. Data beats opinion. If both approaches meet the requirements, I'd lean toward the simpler one for maintainability, but I'd document the decision and the reasoning so it can be revisited if requirements change.

**Possible follow-ups:**
- How would you handle the situation where both approaches meet the requirements, but the engineers still can't agree?
- What if the disagreement is really about something else — for example, one engineer is concerned about long-term maintainability and the other about immediate schedule pressure?