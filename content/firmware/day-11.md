# firmware — Day 11

## Q1: How would you approach implementing a firmware module that must handle multiple sensors on a shared I2C bus, where one sensor is known to occasionally hold the bus with clock stretching for up to 5 ms, and another sensor must be read at a strict 100 Hz rate?

**Answer:** The core tension here is between the strict timing requirement of the 100 Hz sensor and the unpredictable bus occupancy caused by clock stretching from the other sensor. I'd start by quantifying the actual timing budget: at 100 Hz, we have 10 ms between reads, so a 5 ms clock-stretch event consumes half the budget — that's workable but leaves little margin for other bus traffic or scheduling jitter.

My approach would be to isolate the problematic sensor's transactions. Rather than mixing both sensors in a single polling loop, I'd structure the firmware so the 100 Hz sensor's read is a high-priority operation that gets dedicated bus time. In a Zephyr RTOS context, I'd consider giving the high-rate sensor its own I2C controller if the MCU has more than one — that completely eliminates contention. If only one controller is available, I'd use a mutex with priority inheritance to prevent the lower-priority sensor transaction from blocking the high-rate read, and I'd carefully sequence transactions so the clock-stretching sensor is accessed during periods when the 100 Hz read has already completed.

I'd also verify whether the clock stretching is actually necessary or if it's a configuration issue. Some sensors stretch the clock because they're configured with a too-fast bus speed or because they need a delay after a command before data is ready. Sometimes you can reduce or eliminate stretching by adjusting the I2C clock speed, inserting a deliberate delay between the command and data phases, or using the sensor's "no-stretch" mode if it has one.

Finally, I'd instrument the system to measure actual worst-case transaction times rather than relying on datasheet values. I'd add timing hooks around each I2C transaction and log the maximum observed duration. This gives you real data to decide whether you need to change the bus topology, move the problematic sensor to a different bus, or adjust the scheduling.

**Possible follow-ups:**
- How would you handle the situation where the 100 Hz sensor's read occasionally fails because the bus is still held by the other sensor?
- Would you consider using DMA for the I2C transactions, and how would that interact with the clock-stretching behavior?

---

## Q2: How would you approach designing a firmware architecture for a device that needs to support both a real-time control loop (e.g., motor speed control at 1 kHz) and a non-real-time feature set (e.g., configuration, logging, user interface), where the two must not interfere with each other?

**Answer:** The fundamental principle is separation of concerns with explicit priority guarantees. I'd architect this as two distinct domains: a real-time domain that owns the control loop and any safety-critical functions, and a management domain that handles everything else. In a Zephyr RTOS context, this maps naturally to thread priorities — the control loop gets a high priority with a tight period, and everything else runs at lower priorities.

The critical design decision is how the two domains communicate. I would not allow the management domain to directly call into the control loop's code or share variables without synchronization. Instead, I'd use a message-passing or shared-data pattern with explicit synchronization: the control loop publishes its state (motor speed, current, fault flags) to a structure protected by a mutex or read-copy-update pattern, and the management domain reads snapshots of that state. Commands flow the other way through a queue — the management domain posts a command (e.g., "set speed to 3000 RPM"), and the control loop picks it up at a safe point in its cycle.

The control loop itself should be designed to never block. All its inputs should be ready when it needs them — sensor reads should be DMA-driven with double buffering, and the loop should consume the latest available data rather than waiting for fresh data. If a sensor read is delayed, the loop should use the previous sample and flag a data-age warning rather than stalling.

I'd also carefully budget the CPU time. The control loop at 1 kHz with, say, 50 µs of work per cycle uses 5% of CPU on a typical MCU. That leaves ample headroom for the management domain, but I'd still measure worst-case interrupt latency and ensure that no lower-priority activity can delay the control loop's start beyond its deadline. This might mean disabling interrupts around critical sections in the management domain, or using a mutex with priority ceiling to prevent priority inversion.

**Possible follow-ups:**
- How would you handle a situation where the management domain needs to perform a long operation, like a flash write, that could interfere with the control loop?
- What metrics would you collect to verify that the two domains are not interfering in practice?

---

## Q3: You're debugging a firmware issue where a device intermittently fails to wake from a low-power sleep mode when a specific wake-up source is triggered. The device uses multiple wake sources (timer, GPIO, RTC), and the failure only occurs after the device has been in sleep for several hours. How would you approach this?

**Answer:** Intermittent wake failures after long sleep periods suggest a few likely categories: a race condition during the wake sequence, a configuration that degrades over time (e.g., a register getting corrupted), or a hardware issue like a marginal power supply or a floating pin. I'd approach this systematically.

First, I'd try to reproduce the issue with instrumentation. I'd add a non-volatile log that records the wake source, the time in sleep, and the state of relevant peripherals at the moment of wake. This log would be written to flash or retained RAM before entering sleep and updated immediately upon wake. If the device fails to wake entirely, I'd need a hardware debugger or a secondary watchdog that can capture the state.

Second, I'd examine the wake-up configuration carefully. A common issue is that a wake-up source is configured but its interrupt flag isn't cleared before entering sleep, or the interrupt priority is set such that it can't preempt the sleep entry sequence. Another classic issue is that the RTC or timer used for wake is configured with a prescaler or compare value that overflows or wraps after a certain duration — for example, a 16-bit timer that wraps after ~65 seconds if not reconfigured, or an RTC alarm that's set for a specific time rather than a relative offset.

Third, I'd look at the power domain behavior. Some MCUs have different power domains, and a peripheral in a domain that's powered down during deep sleep may lose its configuration. If the wake source is in a domain that's powered down, the wake event may never reach the wake-up controller. I'd verify the power domain configuration and ensure the wake source is in a domain that remains powered.

Finally, I'd consider the possibility of a hardware issue: a marginal solder joint on the wake pin, a pull-up resistor that's too weak, or noise on the wake line that intermittently triggers and then clears the wake condition before the MCU fully wakes. I'd use a scope or logic analyzer to capture the wake pin behavior over an extended period.

**Possible follow-ups:**
- How would you design the wake-up logging so that it doesn't interfere with the low-power operation?
- What would you do if the issue only reproduces in the field and not in the lab?

---

## Q4: How would you approach implementing a firmware module that must parse and validate configuration data received over a communication interface, where the data format is defined by an external specification and may contain both critical parameters (e.g., dosage limits) and non-critical settings (e.g., display brightness)?

**Answer:** The key principle is defense in depth — validation at multiple layers, with clear separation between parsing, semantic validation, and application of the configuration. I'd structure this as a pipeline: first, the raw data is checked for structural integrity (framing, length, checksum); second, it's parsed into a typed structure; third, semantic validation checks that values are within safe ranges and that combinations of values are coherent; and only then is the configuration applied.

For the parsing layer, I'd avoid manual byte-by-byte parsing where possible and use a schema-driven approach — either a code-generated parser from a formal description (like a .proto file or a JSON schema) or a table-driven parser that maps field IDs to offsets, types, and validation rules. This reduces the risk of parsing bugs and makes the code easier to audit.

The critical parameters need special handling. For something like a dosage limit, I'd apply range checking against hard-coded safe bounds that are compiled into the firmware, not just against the previous value. I'd also require explicit confirmation for critical parameter changes — the device would enter a "pending" state where the new configuration is staged but not active, and only becomes active after a second command confirms it. This prevents a single corrupted packet from putting the device into an unsafe state.

I'd also think about what happens when validation fails. The device should reject the entire configuration, not partially apply it. I'd use a transactional approach: parse and validate everything into a temporary structure first, and only if all checks pass, swap the active configuration. If any check fails, the device keeps its previous configuration and logs the rejection reason.

For the non-critical settings, I'd still validate them, but the failure mode is different — a bad brightness value should be rejected, but it shouldn't block the application of critical parameters. I might separate the configuration into two blocks: a critical block that must be fully valid before any changes are applied, and a non-critical block that can be applied independently.

**Possible follow-ups:**
- How would you handle versioning of the configuration format when the specification evolves?
- How would you ensure that a configuration change is atomic — that the device never runs with a partially applied configuration?

---

## Q5: A junior engineer on your team has implemented a firmware module that communicates with a sensor over SPI. The module works in testing, but you notice that the engineer has disabled the SPI peripheral's interrupt and is instead polling the SPI status register in a tight loop while other tasks in the system are starved. The engineer argues that polling is simpler and more predictable. How would you guide them?

**Answer:** I'd acknowledge that the engineer's instinct isn't wrong — polling can be simpler and more predictable in some contexts, particularly for very short transactions where the interrupt overhead would dominate. But in this case, the tight polling loop is starving other tasks, which is a system-level problem. The right answer depends on the specifics: how long does the SPI transaction take, how often does it happen, and what are the timing requirements of the other tasks?

I'd start by asking the engineer to measure the actual transaction time. If a single SPI transaction takes, say, 20 µs and happens once per second, then a tight polling loop is wasteful but not catastrophic — you're burning 20 µs of CPU per second, which is negligible. But if the transaction takes 500 µs and happens at 100 Hz, that's 50 ms of CPU time per second — 5% of the CPU — spent in a busy loop, and that's likely to cause problems.

If polling is genuinely the right approach for the transaction duration, I'd suggest using a blocking poll with a timeout and a yield — in Zephyr, that might be `k_sleep(K_USEC(...))` or `k_yield()` between polls, or using a semaphore that's released by a timer. This keeps the code simple but allows other tasks to run. Alternatively, if the transaction is short enough, the engineer could use a non-blocking poll that checks the status register once, and if the transaction isn't complete, defers the rest of the work to a later call — effectively a cooperative state machine.

If the transaction is long enough that polling would waste significant CPU, I'd guide the engineer toward interrupt-driven or DMA-driven SPI. The key insight is that the choice between polling, interrupts, and DMA isn't about simplicity — it's about matching the mechanism to the timing requirements. Polling is appropriate when the transaction is short and infrequent, interrupts are appropriate when you need to respond quickly to completion, and DMA is appropriate when you're moving large blocks of data and want to minimize CPU involvement.

I'd also point out that the engineer should consider the system-level impact, not just the module-level behavior. A firmware module that works in isolation but starves other tasks is a system failure. The design should account for the whole system's timing budget.

**Possible follow-ups:**
- How would you help the engineer determine whether the SPI transaction is short enough to justify polling?
- What metrics or tools would you use to demonstrate the starvation problem to the engineer?