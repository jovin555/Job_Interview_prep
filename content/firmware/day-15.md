# firmware — Day 15

## Q1: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core principle here is that in a medical monitoring context, an invalid reading must never be presented as a valid one. I'd structure the approach around three layers: detection, handling, and user communication.

For detection, I'd implement validation at the driver level — checking CRC or checksum where the protocol supports it, verifying that values fall within physiologically plausible ranges, and looking for rate-of-change anomalies (e.g., a heart rate that jumps 80 BPM in one sample interval is almost certainly an artifact). This validation should be separate from the raw data acquisition path so that the raw data is preserved for debugging.

For handling, the strategy depends on the failure mode. A single invalid sample might be discarded and the next sample used, but only if the measurement is continuous and a single missed sample doesn't compromise the clinical picture. For persistent failures, I'd implement a graduated response: first, retry with a short backoff; then, if failures continue, transition to a degraded mode where the parameter is marked as "unavailable" rather than showing stale or interpolated data. The key safety principle is that showing "no data" is always safer than showing potentially wrong data.

For user communication, the display should clearly indicate the parameter's status — e.g., "signal lost" or "sensor fault" — rather than simply blanking the value. This follows the principle that the clinician needs to know not just what the value is, but whether the measurement chain is trustworthy.

I'd also implement a diagnostic log that records the raw data, the validation failure reason, and the timestamp, so that post-event analysis can determine whether the failures indicate a sensor degradation trend or a transient interference issue.

**Possible follow-ups:**
- How would you decide between discarding a single bad sample versus holding the last valid reading?
- What validation checks would you apply to the data before it reaches the display layer, and where in the architecture would you place them?

---

## Q2: You're debugging a firmware issue where a device's ADC readings become noisy and inaccurate after the device has been running for several hours, but only when the battery is below 30% charge. The readings are fine on a bench supply. How would you approach this?

**Answer:** This pattern — noise appearing at low battery but not on a bench supply — suggests a power integrity issue that manifests under specific conditions. I'd approach this systematically.

First, I'd characterize the problem precisely. Is the noise correlated with specific events (e.g., radio transmissions, motor activity, display updates) or is it continuous? I'd capture the raw ADC values alongside system events to build a timeline. This helps distinguish between a continuous degradation (e.g., increasing ripple) and an event-triggered issue (e.g., a load transient that the battery can't handle at low charge).

Next, I'd examine the power path. At low battery voltage, a linear regulator's dropout margin shrinks, and its PSRR (power supply rejection ratio) degrades. If the ADC reference is derived from the same rail, the noise couples directly into the measurement. I'd check whether the ADC reference is independent of the battery rail, and whether the regulator's output capacitance is adequate for the load transients. A bench supply has much lower output impedance than a battery, so it can mask supply-rail droop that occurs in the field.

I'd also look at the ADC configuration. Is the sampling time adequate for the source impedance? At low battery, the internal reference or the sensor's output impedance might shift, and if the sampling capacitor isn't fully charged, you get inaccurate readings. I'd verify the ADC's settling time against the worst-case source impedance.

For the firmware side, I'd check whether the ADC is being read during high-current events. If the radio or motor is active during sampling, the supply rail may dip. I'd consider synchronizing ADC reads to avoid these windows, or adding a small delay after a load event to allow the rail to settle.

Finally, I'd instrument the system to log battery voltage, regulator output, and ADC readings together, so that the correlation between supply droop and measurement error can be confirmed rather than assumed.

**Possible follow-ups:**
- What specific ADC settings would you check first, and why?
- How would you determine whether the issue is analog (power integrity) or digital (firmware timing) in origin?

---

## Q3: How would you approach designing a firmware architecture for a device that must support field-updatable firmware where the update image is delivered over an unreliable wireless link, and the device cannot be returned to the factory if an update fails?

**Answer:** The fundamental requirement here is that the device must remain functional — or at least recoverable — regardless of what happens during the update. I'd design around three pillars: a robust bootloader, a staged update process, and a recovery path.

For the bootloader, I'd use a dual-bank approach with a small, immutable bootloader in protected flash. The bootloader's job is minimal: check a boot flag, validate the active image's integrity (CRC or cryptographic signature), and jump to it. If the active image fails validation, it boots the alternate bank. The bootloader itself must be simple enough to be thoroughly tested and never need updating — if it does need updating, that's a separate, carefully controlled process.

For the update delivery, I'd stage the image in an external flash or a dedicated partition, not directly into the target bank. This decouples the unreliable download from the critical flash programming step. The download can be chunked with per-chunk CRC validation, and the device can resume from the last good chunk if the link drops. Only after the complete image is verified in staging would I initiate the bank swap.

For the swap itself, I'd use a two-step commit: write the new image to the inactive bank, verify it (CRC, and ideally a boot-time self-test), then set the boot flag and reset. If the new image fails to boot or fails its self-test, the bootloader rolls back to the previous bank. The rollback must be automatic and require no user intervention.

I'd also consider a "recovery mode" accessible via a button or serial command, which forces the bootloader to accept a new image over a wired link as a last resort. This is a safety net for the case where both banks are somehow corrupted — rare, but the consequences of a bricked medical device justify the extra complexity.

**Possible follow-ups:**
- How would you handle the case where the device loses power mid-write to the inactive bank?
- What self-tests would you require the new firmware to pass before committing to it?

---

## Q4: You're leading a firmware team where two senior engineers disagree on whether to use a real-time operating system (RTOS) or a bare-metal super-loop architecture for a new medical device. One argues that the RTOS adds complexity and overhead, while the other argues that the super-loop will become unmaintainable as features are added. How would you guide the team to a decision?

**Answer:** I'd frame this as an engineering decision based on requirements, not a matter of preference or fashion. The goal is to find the architecture that best satisfies the device's real-time constraints, safety requirements, and long-term maintainability — while being honest about the team's ability to execute either approach well.

First, I'd have the team enumerate the device's actual requirements: how many concurrent tasks exist, what their timing constraints are, what the worst-case interrupt latency can be, how much memory is available, and what the safety certification implications are. For a medical device, I'd also consider whether the architecture needs to support features like task isolation, watchdog integration, or deterministic scheduling that an RTOS provides out of the box.

Then I'd evaluate both options against those requirements. A super-loop is genuinely simpler and has lower overhead — it can be easier to reason about for a small number of tasks with well-defined timing. But it becomes fragile when you have multiple tasks with different rates, or when a long-running operation in one task delays others. An RTOS provides preemptive scheduling, which gives you isolation between tasks — a bug in a low-priority task can't starve a high-priority one. That isolation is a safety feature in itself.

I'd also consider the team's experience. If the team has deep RTOS experience, the learning curve is irrelevant. If they don't, the RTOS introduces risk — but so does a super-loop that grows beyond what it can handle. I'd ask the team to estimate the complexity of the final system, not the current prototype.

My recommendation would typically be: if the system has more than three or four concurrent responsibilities with different timing requirements, or if any task has a hard real-time deadline that must not be missed, an RTOS is the safer choice. If the system is genuinely simple — one control loop, one communication interface — a well-structured super-loop with a clear state machine can be perfectly adequate.

The key is to make the decision based on evidence and requirements, and to document the rationale so that future engineers understand why the choice was made.

**Possible follow-ups:**
- What specific criteria would you use to decide whether the system's complexity justifies an RTOS?
- How would you handle the certification implications of adding an RTOS to a medical device?

---

## Q5: How would you approach implementing a firmware module that must handle a burst of data from a sensor at high speed (e.g., 1000 samples at 10 kHz) while the rest of the system is running normal operations, without dropping any samples?

**Answer:** The key challenge here is that 10 kHz sampling means a new sample every 100 µs, and the CPU can't spend all its time servicing the sensor. I'd approach this by moving the data capture out of the CPU's critical path as much as possible.

First, I'd use DMA to transfer samples from the sensor into memory without CPU intervention. The sensor interface (SPI or I2C) would be configured to trigger DMA transfers, and the DMA controller would write samples directly into a buffer. The CPU would only be involved at the start (setting up the transfer) and at the end (processing the completed buffer). This eliminates the per-sample interrupt overhead.

For the buffer, I'd use a double-buffering scheme: while DMA is filling one buffer, the CPU processes the other. This avoids the need for a shared buffer that's being written and read simultaneously, which would require synchronization and could cause data loss. The double-buffer also gives the CPU a full buffer's worth of time (100 ms for 1000 samples) to process the data, which is ample.

I'd also consider whether the sensor supports a burst mode or a FIFO. Many sensors can be configured to sample internally and hold data in an on-chip FIFO, which the MCU can then read in larger chunks. This reduces the bus traffic and gives the MCU more flexibility in when it reads the data.

For the processing side, I'd ensure that the task handling the data is high-priority but not so high that it starves other tasks. The processing should be split into two phases: a time-critical phase that copies or minimally processes the data (e.g., storing it to a larger buffer or flash), and a non-time-critical phase that does the heavy analysis. This way, the real-time requirement is only on the data capture, not on the analysis.

Finally, I'd instrument the system to detect dropped samples — e.g., a counter that increments when a DMA transfer completes but the buffer wasn't ready. This gives early warning of a design flaw rather than silent data loss.

**Possible follow-ups:**
- How would you handle the case where the sensor data rate exceeds what the DMA controller can sustain?
- What happens if the processing task is delayed and the double-buffer isn't ready when DMA completes?