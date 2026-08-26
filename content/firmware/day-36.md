# firmware — Day 36

## Q1: How would you approach designing a firmware architecture for a device that must support both a hard real-time control loop (e.g., 1 kHz motor control) and a non-real-time subsystem like a wireless stack, where the wireless stack has its own timing requirements and can consume significant CPU time?

**Answer:** The core principle is strict temporal isolation between the hard real-time path and everything else. I would structure this as a two-tier architecture: the control loop runs at the highest priority with a dedicated timer interrupt or a high-priority RTOS task, and the wireless stack runs as a lower-priority task. The critical design decision is that the control loop must never block on anything the wireless stack does — no shared locks, no waiting on buffers that the wireless task fills, no calling into wireless stack APIs from the control context.

For the control loop, I'd use a timer-driven approach where the 1 kHz tick fires an interrupt that performs the control calculation directly, or signals a high-priority task that preempts everything else. The control code should be self-contained: it reads sensors, computes outputs, and writes to actuators using only its own private data structures. Any data that needs to flow between the control loop and the wireless subsystem (e.g., telemetry) should go through a lock-free mechanism — typically a double-buffer or a single-writer/single-reader ring buffer with careful memory ordering, since the control context and the wireless task are the only two accessors.

For the wireless stack itself, I'd give it a defined CPU budget. If the stack can't complete its work within its allocated time slice, it should defer to the next cycle rather than overrunning into control-loop time. This might mean configuring the wireless stack's internal buffers and task priorities so that it yields frequently, or using a cooperative scheduling approach where the wireless stack processes a bounded amount of work per invocation.

I'd also carefully budget interrupt latency. The wireless stack may generate interrupts that need servicing, but those ISRs must be short and defer heavy processing to the lower-priority task. If the wireless radio requires DMA, I'd ensure the DMA completion interrupt has a bounded latency and doesn't interfere with the control timer.

Finally, I'd verify the architecture with worst-case analysis: measure the maximum time the control loop is ever delayed, and prove it's well within the 1 kHz budget. This means instrumenting the system to record interrupt latency and task preemption times under full wireless load.

**Possible follow-ups:** How would you handle a situation where the wireless stack vendor's library blocks for longer than your control loop budget? What if the control loop and wireless stack need to share a sensor reading — how would you design that data path?

---

## Q2: You're debugging a firmware issue where a device's flash write operations occasionally corrupt data in an unrelated memory region. The corruption is intermittent and only occurs when the device is under heavy load. How would you approach this?

**Answer:** Flash corruption that affects unrelated memory regions is almost always a symptom of something deeper — flash doesn't corrupt RAM directly, so I'd be looking for a mechanism that bridges the two. The most common culprits are: a DMA channel writing to the wrong address, a stack overflow that happens to land in the flash buffer, a race condition where two tasks write to the same buffer simultaneously, or a hardware issue like marginal power supply during the high-current flash write.

My first step would be to reproduce it deterministically. I'd instrument the system to log the state at the moment of corruption — which task was running, what the stack pointers were, which DMA channels were active, and what the flash controller was doing. If I can capture the corrupted data pattern, that often tells me the source: all zeros or all ones suggests a bus issue, a recognizable data pattern from another buffer suggests a DMA or buffer-overrun problem.

I'd also check the flash driver itself. Many flash operations require interrupts to be disabled or the CPU to be stalled; if the driver doesn't handle this correctly, an interrupt could fire mid-write and cause the flash controller to misbehave. I'd review the driver for proper wait-state handling, bus locking, and whether it correctly handles the case where another bus master (like DMA) tries to access memory during the write.

Another angle is power integrity. Flash writes draw significant current, especially on internal charge pumps. If the supply voltage dips during a write, it can cause marginal behavior in other peripherals. I'd check the power supply with a scope during a write operation, and also verify that the firmware isn't doing anything unusual with clock configuration during writes.

If the corruption is in RAM, I'd also suspect a stack overflow in a task that happens to be running during the flash write. I'd check stack high-water marks and consider adding stack canaries to catch overflows.

**Possible follow-ups:** How would you go about reproducing an intermittent corruption issue that only happens under heavy load? What tools or instrumentation would you add to the system to help diagnose it?

---

## Q3: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The fundamental requirement is that the system must fail safe — it's better to show no reading or an explicit error than to display a plausible but incorrect value. I'd design the sensor data path with multiple layers of validation and a clear policy for what happens when data fails validation.

The first layer is at the protocol level: verify CRC or checksum on every read, check that the sensor's status registers indicate valid data, and verify the data is internally consistent (e.g., a temperature reading that jumps 10 degrees in 100 ms is physiologically implausible). I'd implement range checks against both absolute limits and rate-of-change limits, since a sensor can produce in-range but still impossible values.

The second layer is temporal: maintain a short history of recent valid readings. If a single reading fails validation, I'd consider whether to hold the last valid value, interpolate, or flag the reading as invalid. For a medical monitor, I'd generally not hold a stale value indefinitely — the clinician needs to know the data is current. A common approach is to display the last valid reading with a "data stale" indicator after a short timeout, and to transition to an explicit "sensor error" state if invalid data persists.

The third layer is state management: the firmware should track the sensor's health over time. A single CRC failure might be a transient glitch; ten in a row indicates a real problem. I'd implement a state machine with states like "normal," "degraded" (intermittent errors, still displaying data with warnings), and "failed" (no data displayed, alarm raised). The transitions between these states should have hysteresis to avoid flapping.

Critically, the decision about what to display must be made by the firmware, not left to the display layer. The data validation and display logic should be separate modules, with the validation module producing a data structure that includes both the value and its confidence/validity status. The display module then renders based on that status — never showing an invalid value as if it were valid.

Finally, I'd make sure the failure behavior is documented and tested. The validation logic should be unit-tested with simulated invalid data, and the system-level behavior (what the clinician sees) should be verified against the requirements.

**Possible follow-ups:** How would you handle a sensor that produces valid-looking but slowly drifting values — how would you detect that? What if the clinician needs to see the raw data for troubleshooting — how would you provide that without compromising the safety display?

---

## Q4: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** This is a classic priority inversion problem with a blocking resource. The flash erase blocks the lower-priority task, but the real issue is that the flash peripheral itself may block the CPU or the bus, which can affect the high-priority task regardless of RTOS scheduling.

First, I'd check whether the flash erase actually blocks the CPU or just the calling task. On many MCUs, flash erase stalls the CPU core because the flash controller can't service instruction fetches while erasing. If that's the case, no RTOS scheduling will help — the high-priority task simply can't run during the erase. The solution is to use a flash controller that supports "erase while read" or to move the flash to a separate QSPI device that doesn't stall the main flash. If the MCU's flash does stall the CPU, I'd need to either accept the 100 ms gap (which is likely unacceptable for a 1 ms sensor task) or use external flash.

If the flash erase only blocks the calling task (e.g., external SPI flash where the task waits on a semaphore), then the RTOS can schedule the high-priority task during the wait. In that case, the design is straightforward: the flash task blocks on a semaphore, the scheduler runs the sensor task at its 1 ms period, and the flash task resumes when the erase completes.

But there's a subtler issue: the flash erase task might hold a mutex or other resource that the sensor task needs. I'd ensure the sensor task never shares a lock with the flash task. If the sensor task needs to log data to flash, I'd use a queue or buffer so the sensor task just enqueues data and never blocks on the flash operation itself.

I'd also consider whether the flash erase can be broken into smaller chunks. Many flash devices allow sector erases that are faster than full-chip erases, or the erase can be paused and resumed. If the hardware supports it, I could interleave the erase with sensor reads.

Finally, I'd verify the actual worst-case timing. The 100 ms figure is the flash erase time, but the sensor task's actual deadline is 1 ms. I'd measure the maximum time between sensor task invocations under worst-case conditions (flash erase + any other interrupts) and confirm it meets the requirement. If it doesn't, I'd need to change the hardware architecture — for example, using a dual-bank flash or external flash — rather than trying to fix it in software.

**Possible follow-ups:** What if the sensor task and the flash task both need to access the same SPI bus? How would you handle bus arbitration? What if the flash erase is on the same chip as the sensor data — how does that change your approach?

---

## Q5: A junior engineer on your team has implemented a low-power mode for a medical monitoring device that enters deep sleep between sensor readings. The device wakes on a timer interrupt, takes a reading, then goes back to sleep. However, the device occasionally misses readings because the sensor itself requires a 50 ms stabilization time after power-up before it produces valid data. The engineer proposes keeping the sensor powered on continuously to avoid the stabilization delay. How would you guide them?

**Answer:** I'd start by acknowledging that the engineer has identified a real problem — the sensor stabilization time is a genuine constraint that must be handled. But keeping the sensor powered continuously defeats the purpose of the low-power mode, and for a battery-powered medical device, that's likely a non-negotiable requirement. The question is whether we can find a middle ground.

First, I'd ask the engineer to characterize the problem more precisely. Is the 50 ms stabilization time a fixed hardware spec, or does it vary with temperature, supply voltage, or how long the sensor was off? Sometimes the stabilization time is shorter if the sensor is kept in a low-power state rather than fully powered off. Many sensors have multiple power states — off, standby, and active — and the transition from standby to active might be much faster than from off to active. If the sensor supports a standby mode with lower power consumption than active but faster wake-up than full off, that could be the solution.

If the sensor truly needs 50 ms from full power-off, then I'd look at the timing budget. The device wakes on a timer interrupt, takes a reading, and goes back to sleep. If the wake interval is, say, 1 second, then 50 ms of stabilization is 5% of the duty cycle — that might be acceptable if the sensor's active current is low. The engineer could power the sensor at wake time, wait 50 ms, take the reading, and power it down. The key is to overlap the stabilization time with other wake-up activities — for example, the MCU could do its own housekeeping (checking battery voltage, updating the RTC, etc.) during the sensor stabilization period.

I'd also ask whether the sensor really needs to be powered down at all. If the sensor's sleep current is negligible compared to the MCU's sleep current, keeping it in a low-power state might be simpler and more reliable. The trade-off is between power consumption and complexity — sometimes the power savings from fully powering down the sensor aren't worth the timing complexity.

Finally, I'd emphasize the importance of measuring, not assuming. The engineer should measure the actual current draw in each configuration — sensor fully off, sensor in standby, sensor powered continuously — and the actual wake-up and stabilization times. The decision should be data-driven, not based on intuition about what "should" be more efficient.

**Possible follow-ups:** How would you handle the case where the sensor's stabilization time varies with temperature, and the device must operate in both warm and cold environments? What if the sensor's power-up sequence can fail intermittently — how would you detect and recover from that?