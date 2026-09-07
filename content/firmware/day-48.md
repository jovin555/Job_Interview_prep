# firmware — Day 48

## Q1: You're debugging a firmware issue where a device's flash write operations occasionally corrupt data in an unrelated memory region. The corruption is intermittent and only occurs when the device is under heavy load. How would you approach this?

**Answer:** This pattern — flash writes corrupting unrelated memory under load — points to a few classic root causes, and I'd approach it systematically rather than guessing.

First, I'd try to determine whether the corruption is in flash itself or in RAM. If the corrupted region is in RAM, the flash write is likely a red herring; the real issue is probably a buffer overrun or stack overflow that happens to coincide with flash activity because that's when memory pressure is highest. I'd check whether the corruption address correlates with a known buffer or stack region, and I'd enable the MPU (if available) to trap accesses to the corrupted region.

If the corruption is genuinely in flash, the most likely culprits are: (1) a flash driver that doesn't properly handle the write-while-erase or write-while-write constraints of the specific flash part, (2) a race condition where two contexts (e.g., an ISR and a task) both initiate flash operations without proper mutual exclusion, or (3) an electrical issue like insufficient power during the high-current flash operation — though that's less likely if it reproduces on a bench supply.

I'd also scrutinize the flash driver's use of DMA. If the DMA descriptor or buffer lives in a region that gets reclaimed or overwritten, the flash controller could write from the wrong source address. I'd verify that DMA buffers are statically allocated and never freed while a transfer is in flight.

To reproduce more reliably, I'd add instrumentation: log the flash operation start/end times, the addresses involved, and the current task/ISR context. I'd also deliberately stress the system — increase interrupt rate, add artificial memory pressure — to see if the corruption rate increases, which would support the memory-pressure hypothesis.

**Possible follow-ups:** How would you distinguish between a software race and a hardware/electrical issue in this scenario? What specific instrumentation would you add to narrow down the corruption source?

---

## Q2: How would you approach designing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core principle here is that the system must fail safe: it's better to show no reading or an explicit error than to display a plausible-but-wrong value. I'd design the data path with multiple layers of validation.

At the lowest layer, I'd validate the raw data integrity — CRC or checksum verification, and protocol-level checks like address and length fields. If the sensor provides a data-ready flag or status register, I'd check that too. Any frame that fails these checks is discarded immediately, not passed up the stack.

Next, I'd apply plausibility checks at the semantic level. Each physiological parameter should have a valid operating range defined from clinical requirements, plus rate-of-change limits — a heart rate that jumps 80 BPM in one sample interval is physiologically implausible even if each individual value is within range. These limits need to be configurable and documented, since they're clinically meaningful decisions.

For handling invalid samples, I'd use a policy that depends on the parameter's criticality and the failure duration. A single dropped sample might be handled by holding the last valid value briefly, but I'd never hold it indefinitely — after a short timeout, the display should show "no data" or an alarm rather than a stale value. For repeated failures, the device should escalate to an audible/visual alarm and log the event.

Critically, I'd separate the raw data path from the displayed value path. The display layer should only ever receive validated, post-processed values, and it should have its own logic for indicating data freshness. I'd also ensure that any error state is sticky enough that a single good sample doesn't clear an alarm condition — there should be hysteresis requiring several consecutive valid samples before returning to normal operation.

Finally, I'd build fault injection into the test plan: simulate CRC errors, out-of-range values, and intermittent sensor dropouts to verify the device never displays a false reading under any of these conditions.

**Possible follow-ups:** How would you decide between holding the last valid value versus showing "no data" when a sample is invalid? How would you handle a sensor that returns valid-looking but systematically biased data (e.g., a calibration drift)?

---

## Q3: You're leading a firmware team where two senior engineers disagree on whether to implement a critical communication protocol using a polling approach or an interrupt-driven approach. One argues that polling is simpler and more predictable for real-time constraints, while the other insists that interrupts are necessary for responsiveness. How would you guide the team to a decision?

**Answer:** I'd frame this as an engineering decision driven by requirements, not a matter of personal preference. The first step is to establish the protocol's actual timing requirements: What's the maximum latency between a byte arriving and it being read? What's the minimum inter-byte gap? What's the worst-case CPU load from other tasks during that window? Without these numbers, the debate is purely theoretical.

Once we have the requirements, I'd ask the team to evaluate both approaches against them. Polling is genuinely simpler and more deterministic — there's no interrupt latency, no nested interrupt concerns, and the code path is linear. It works well when the polling interval is short enough relative to the protocol's timing margins, and when the CPU has spare cycles. The risk is that polling consumes CPU even when there's no traffic, and if the polling interval is too long, bytes get dropped.

Interrupt-driven approaches are more responsive and CPU-efficient when traffic is bursty, but they introduce complexity: shared data between ISR and task context, potential priority inversion, and the need to keep ISR execution time bounded. The real question isn't which is "better" — it's which set of trade-offs fits this protocol and this system.

I'd also suggest a hybrid as a third option: interrupt-driven reception into a DMA ring buffer with a task that processes complete messages. This gives responsiveness without requiring the ISR to do protocol parsing. The DMA handles the byte-level timing, and the task handles the protocol logic at its own pace.

To make the decision concrete, I'd ask both engineers to write a short analysis document: their proposed architecture, worst-case latency calculations, CPU utilization estimates, and failure modes. Then we'd review them as a team against the requirements. If the numbers are close, I'd lean toward the simpler solution that meets requirements with margin, because simplicity is a feature in medical device firmware — it's easier to verify, test, and maintain over the product's lifetime.

**Possible follow-ups:** What specific timing requirements would you ask the team to quantify before making this decision? How would you handle the situation if one engineer's preferred approach clearly meets the requirements but the other's doesn't, yet the latter is the more senior engineer?

---

## Q4: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental problem is that a 100 ms blocking operation in any task will stall the entire system if it runs at a priority that prevents the 1 ms task from preempting it — and even if the flash task is lower priority, the blocking call itself ties up the CPU. The solution is to ensure the flash operation never blocks the scheduler.

The cleanest approach in Zephyr is to move the flash erase to a context that doesn't block other threads. Options include: (1) using Zephyr's flash driver with asynchronous support if the hardware and driver provide it, (2) running the erase in a dedicated lower-priority thread and accepting that the 1 ms task might miss deadlines during the erase — which is usually unacceptable, or (3) using a flash part that supports background erase while the CPU continues executing.

If the flash hardware doesn't support asynchronous erase, I'd look at whether the erase can be broken into smaller chunks. Many NOR flash parts allow sector-by-sector erase, and if each sector erase is, say, 5 ms, I could interleave the erase with the sensor task by having the flash task yield between sectors. But this only works if the sensor task's 1 ms deadline can tolerate brief preemption — which it should, since Zephyr's scheduler will preempt the flash task when the higher-priority sensor task becomes ready.

The real issue is that a single 100 ms blocking call in any task is a design smell. I'd question why the erase needs to be 100 ms in one shot. If it's a full-chip erase, I'd redesign to erase only the sectors that actually need it. If it's a wear-leveling or garbage-collection operation, I'd schedule it during a known idle period or when the device is in a state where missing sensor samples is acceptable.

I'd also consider whether the sensor data can be buffered during the erase window. If the sensor task can write to a DMA buffer or a sufficiently large FIFO, and the processing task can catch up afterward, then a brief blocking window might be tolerable. But for a true 1 ms hard real-time requirement, the answer is usually: the flash operation must not block the CPU for more than a fraction of a millisecond, which means either hardware support for background erase or a different storage strategy (e.g., RAM-backed logging with periodic flush during idle periods).

**Possible follow-ups:** How would you handle the case where the flash erase is a full-chip erase that genuinely cannot be interrupted? What Zephyr-specific mechanisms (e.g., thread priorities, preemption, interrupts) would you rely on to guarantee the 1 ms task meets its deadline?

---

## Q5: A junior engineer on your team has implemented a low-power mode for a medical monitoring device that enters deep sleep between sensor readings. The device wakes on a timer interrupt, takes a reading, then goes back to sleep. However, the device occasionally misses readings because the sensor itself requires a 50 ms stabilization time after power-up before it produces valid data. The engineer proposes keeping the sensor powered on continuously to avoid the stabilization delay. How would you guide them?

**Answer:** I'd start by acknowledging that the engineer has identified a real problem — the sensor stabilization time is incompatible with the current wake-sleep cycle — but I'd push back on the proposed solution because keeping the sensor powered continuously defeats much of the purpose of the low-power mode. In a battery-powered medical device, the sensor may be one of the largest power consumers, so powering it continuously could cut battery life dramatically.

Instead, I'd guide them to think about the problem in terms of the wake cycle's timing budget. The key insight is that the sensor's 50 ms stabilization time doesn't have to happen after the MCU wakes — it can happen before. The sequence could be: the timer fires, the MCU wakes and immediately powers on the sensor, then the MCU goes back to a lighter sleep state (not deep sleep) while the sensor stabilizes, and only then takes the reading. This way, the sensor is only powered for the duration of the stabilization plus the reading, not continuously.

Alternatively, if the sensor has a separate power rail controlled by a GPIO, the engineer could power the sensor on slightly before the MCU goes to deep sleep, so that by the time the MCU wakes on the timer, the sensor has already stabilized. This requires careful timing coordination but keeps the sensor powered only for the necessary window.

I'd also ask them to check the sensor's datasheet more carefully. Some sensors have multiple power modes — a "standby" mode that's lower power than full operation but still allows faster wake-up than from full power-off. If the sensor supports this, the engineer could put it in standby between readings rather than powering it off entirely, which might reduce the stabilization time from 50 ms to microseconds.

Finally, I'd emphasize that missing readings is itself a problem that needs a design-level solution, not just a power-management patch. If the device occasionally misses a reading because the sensor isn't ready, that's a reliability issue that needs to be addressed — either by ensuring the wake sequence always allows enough time for stabilization, or by detecting and handling missed readings gracefully (e.g., logging them, alerting the user, or adjusting the sampling schedule).

**Possible follow-ups:** How would you calculate the power trade-off between keeping the sensor powered continuously versus cycling it with a 50 ms stabilization delay? What other design changes might reduce the sensor's wake-up time or eliminate the need for a stabilization period?