# firmware — Day 16

## Q1: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core principle here is that in a medical monitoring context, the firmware must fail safe — it's better to show "no data" or "sensor error" than to display a plausible-looking but incorrect value. I'd structure the approach in layers.

First, at the data acquisition layer, I'd validate every raw read before it enters the processing pipeline. This means checking CRC or checksum where the protocol supports it, verifying that the data length matches expectations, and confirming the sensor is in the expected operational state (e.g., not in a configuration mode). Any frame that fails these checks should be discarded immediately, not passed up the stack.

Second, at the signal-processing layer, I'd apply plausibility checks. Each physiological parameter should have defined valid ranges — both absolute bounds (e.g., a temperature reading of 45°C is physiologically implausible) and rate-of-change limits (e.g., a heart rate that jumps 80 BPM in one sample interval is suspect). Values that fall outside these bounds should be flagged as suspect rather than silently accepted.

Third, I'd implement a redundancy and persistence strategy. For a single sensor, this might mean requiring N consecutive valid readings before updating the displayed value, or using a median filter over the last M samples to reject outliers. If the device has multiple sensors measuring related parameters (e.g., SpO₂ and heart rate), cross-checking between them can catch single-sensor failures.

Finally, the display and alarm logic must distinguish between "valid measurement," "suspect measurement," and "no measurement." A suspect reading might be displayed with a "low confidence" indicator or held at the last valid value with a timestamp showing it's stale. An alarm should never be triggered or suppressed based on a single suspect reading — it should require confirmation across multiple samples or a secondary source.

The key architectural point is that validation should be a distinct layer with clear interfaces, not scattered throughout the application code. This makes it testable in isolation and auditable for regulatory purposes.

**Possible follow-ups:**
- How would you handle the trade-off between responsiveness and false-reading rejection when a patient's condition is genuinely changing rapidly?
- How would you document this validation logic for a regulatory submission (e.g., IEC 60601)?

---

## Q2: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 2 ms, but a lower-priority task occasionally needs to perform a flash write that blocks for up to 50 ms. How would you approach this scheduling conflict?

**Answer:** This is a classic priority-inversion and deadline-miss problem. The flash write blocking for 50 ms while a 2 ms sensor task needs to run will cause the sensor task to miss its deadline, which is unacceptable for a real-time sensing application.

The first thing I'd examine is whether the flash write actually needs to block the CPU for the full 50 ms. Many modern MCUs have a flash controller that can perform writes in the background while the CPU continues executing from cache or RAM. If the hardware supports it, I'd use the flash controller's interrupt or status flag to signal completion, allowing the sensor task to run during the write. This is the ideal solution because it eliminates the blocking entirely.

If the flash peripheral genuinely blocks the CPU, I'd look at whether the flash operation can be deferred or broken up. For example, if the lower-priority task is writing a log entry, could it buffer the data and write it in smaller chunks between sensor reads? A 2 ms period gives a 2 ms window between reads — even writing 256 bytes in that window might be feasible if the flash write time per byte is small enough.

Another approach is to use Zephyr's thread priorities and scheduling more deliberately. The sensor task should be at a higher priority than the flash-writing task, but that alone doesn't help if the flash task blocks the CPU. I'd consider using a dedicated lower-priority thread for flash operations and ensuring that the sensor task's stack and data are in RAM, not in flash, so that code execution isn't stalled by the write.

If the flash write absolutely cannot be avoided or shortened, I'd look at the system-level design. Can the flash write be scheduled to occur during a period when the sensor task doesn't need to run? For example, if the sensor has a burst mode where it captures data internally for a short period, the flash write could happen during that burst. Or, if the system has multiple sensor tasks, could the flash write be deferred until a lower-activity period?

Finally, I'd consider whether the sensor task really needs to run every 2 ms, or whether it could use DMA to capture data continuously and only wake the CPU when a buffer is full. This would reduce the CPU load and give more scheduling headroom.

The key is to quantify the actual timing requirements, understand the hardware's capabilities, and then choose the approach that guarantees the sensor task's deadline without over-engineering the solution.

**Possible follow-ups:**
- How would you measure and verify that the sensor task is actually meeting its 2 ms deadline in practice?
- What if the flash write is for a firmware update that must not be interrupted?

---

## Q3: How would you approach designing a firmware architecture for a device that must support multiple communication interfaces (e.g., USB, UART, and wireless) for configuration and data retrieval, where the same data needs to be accessible through any interface?

**Answer:** The key architectural principle here is to separate the data model from the transport mechanisms. The configuration parameters and data streams should live in a single, well-defined data layer that all interfaces read from and write to. Each communication interface then becomes a thin adapter that translates between the transport protocol and the internal data model.

I'd start by defining a canonical data model — a set of structured data types (e.g., configuration structs, telemetry records, command definitions) that are transport-agnostic. This model should be versioned so that future changes are traceable. The data model should also define access semantics: which parameters are read-only, which are read-write, and what validation rules apply when a parameter is modified.

For the interface adapters, each one (USB, UART, wireless) would implement a common interface contract. This contract would include methods for: parsing incoming messages, validating them against the data model, applying changes (for configuration), and formatting outgoing data. The adapters should not contain business logic — they should only handle protocol-specific concerns like framing, checksums, and flow control.

A critical design decision is how to handle concurrent access. If a configuration parameter is being modified over USB while a wireless client is reading the same parameter, you need a synchronization mechanism. I'd use a mutex or a reader-writer lock around the data model, with the granularity chosen based on how frequently data changes and how large the data structures are. For frequently-updated telemetry data, a double-buffer or publish-subscribe pattern might be more appropriate than locking.

Another important consideration is consistency. If a configuration change requires multiple parameters to be updated atomically (e.g., changing a sensor's calibration coefficients), the interface layer should support a "transaction" concept — the client sends a complete configuration set, and the device applies it atomically or rejects it entirely. This prevents a partial update that leaves the device in an inconsistent state.

Finally, I'd design for testability. Each adapter should be testable in isolation with mock data, and the data model should have unit tests that verify validation rules and access semantics. This is especially important in a medical device context where the behavior of each interface needs to be documented and verified for regulatory compliance.

**Possible follow-ups:**
- How would you handle a situation where two clients on different interfaces try to modify the same configuration parameter simultaneously?
- How would you version the data model so that older clients can still communicate with newer firmware?

---

## Q4: You're debugging a firmware issue where a device's ADC readings become noisy and inaccurate after the device has been running for several hours, but only when the battery is below 30% charge. The readings are fine on a bench supply. How would you approach this?

**Answer:** This symptom pattern — time-dependent degradation that correlates with battery state — suggests a few distinct categories of root cause, and I'd approach it systematically.

First, I'd consider power supply quality. As a battery discharges, its internal impedance rises and its output voltage drops. If the ADC's reference voltage is derived from the battery rail (directly or through a regulator), the reference itself may be drifting or noisy at low charge. I'd check the schematic to see what the ADC reference is tied to. If it's a band-gap reference powered from the battery rail, I'd look at whether the reference has sufficient headroom at the minimum battery voltage. I'd also check whether there's a low-dropout regulator (LDO) in the path and whether it's dropping out of regulation as the battery voltage approaches its dropout threshold.

Second, I'd look at the ADC input path. If the sensor signal is conditioned by an op-amp or instrumentation amplifier, the amplifier's output swing may be limited at lower supply voltages, causing clipping or non-linear behavior. Similarly, if there's a filter capacitor on the ADC input, its effective capacitance may change with voltage if it's a ceramic capacitor (DC bias effect), which could alter the filter's cutoff frequency and let in more noise.

Third, I'd consider thermal effects. After several hours of operation, the device may have warmed up. If the battery is also warming up, its characteristics change. But more importantly, if there's a temperature-sensitive component in the signal path (e.g., a precision resistor or reference), its drift over temperature could explain the time-dependent degradation. The correlation with battery level might be coincidental — the device has been running long enough to heat up by the time the battery is at 30%.

Fourth, I'd look at firmware-level causes. Is the ADC being sampled at a consistent rate, or does the sampling interval change as the battery voltage drops? Some MCUs have an internal ADC that takes longer to settle at lower supply voltages, or the ADC's internal reference may be less accurate. If the firmware is doing any power management based on battery level (e.g., reducing the ADC sampling rate to save power), that could introduce aliasing or averaging artifacts.

My debugging approach would be: first, capture the raw ADC values and the battery voltage simultaneously to see if there's a correlation. Second, probe the ADC reference voltage and the sensor signal at the ADC input while the device is in the failing state. Third, compare the behavior with a bench supply set to the same voltage as the battery at 30% charge — this separates "battery behavior" from "low voltage behavior." Fourth, review the firmware's ADC configuration and any power-management code that might be triggered by battery level.

The most likely root causes, in my experience, are either a marginal power supply design that degrades at low battery voltage, or a firmware issue where the ADC configuration or sampling behavior changes based on battery level.

**Possible follow-ups:**
- How would you determine whether the issue is analog (hardware) or digital (firmware) before diving into either?
- What design changes would you consider to make the ADC measurement more robust across the full battery voltage range?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to use a real-time operating system (RTOS) or a bare-metal super-loop architecture for a new medical device. One argues that the RTOS adds complexity and overhead, while the other argues that the super-loop will become unmaintainable as features are added. How would you guide the team to a decision?

**Answer:** This is a common and important architectural decision, and my role as the lead is to ensure the decision is made based on evidence and requirements, not on personal preference or past experience. I'd structure the discussion around several key factors.

First, I'd ask the team to enumerate the device's actual requirements. How many concurrent tasks or functions need to run? What are their timing requirements — are there hard real-time deadlines, or is everything best-effort? How much complexity is expected in the interaction between tasks? For a medical device, I'd also consider the regulatory implications — both architectures can be made safe, but the documentation and verification burden differs.

Second, I'd look at the team's experience and the project timeline. If the team has deep RTOS experience, the "complexity" argument carries less weight. Conversely, if the team has only done bare-metal work, introducing an RTOS mid-project could be risky. I'd also consider the long-term maintainability — if this device will be in the field for 10+ years and will receive feature additions, the RTOS's structured task model might be more maintainable than a growing super-loop.

Third, I'd consider the specific technical requirements. If the device needs precise timing (e.g., a 1 kHz control loop with bounded jitter), both approaches can work, but the RTOS gives you priority-based preemption which makes it easier to guarantee that a high-priority task runs on time. If the device has multiple independent functions that need to run concurrently (e.g., sensor acquisition, user interface, communication, logging), the RTOS's task model maps naturally to those functions. If the device is very simple — one sensor, one output, no user interface — a super-loop might genuinely be simpler and more appropriate.

I'd also raise the question of what "complexity" means in this context. An RTOS does add code and configuration, but it also provides well-tested primitives for synchronization, scheduling, and inter-task communication. A super-loop with hand-rolled state machines and timing logic can become more complex and harder to verify as features are added. The question is whether the RTOS's complexity is "good complexity" that reduces overall system complexity, or "bad complexity" that adds overhead without benefit.

My approach would be to have each engineer present a concrete architecture sketch for the device — not a general argument, but a specific design showing how they'd structure the tasks or the super-loop, how they'd handle the key timing requirements, and how they'd handle the expected feature set. Then we'd evaluate both designs against the requirements, looking at timing guarantees, memory usage, testability, and maintainability.

If the decision is genuinely close, I'd consider a hybrid approach: start with a super-loop for the initial prototype to validate the hardware, then migrate to an RTOS if the complexity grows. But for a medical device, I'd be cautious about a "we'll migrate later" plan, because the verification and validation effort for a medical device is substantial, and re-architecting the firmware after the DHF (Design History File) is started is costly.

Ultimately, the decision should be documented with clear rationale, including the alternatives considered and why the chosen approach was selected. This documentation is valuable for the regulatory file and for future engineers who will maintain the device.

**Possible follow-ups:**
- What specific criteria would you use to evaluate the two architecture proposals objectively?
- How would you handle the situation if one engineer refuses to accept the decision and continues to advocate for their preferred approach?