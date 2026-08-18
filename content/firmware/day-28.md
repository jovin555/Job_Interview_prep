# firmware — Day 28

## Q1: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The first principle is that a blocking flash erase in a lower-priority task should never be allowed to starve a higher-priority task. I'd start by questioning whether the flash erase truly needs to block for the full 100 ms. Many MCU flash controllers support sector erase with interrupt-on-complete, so I'd look at whether the erase can be initiated and then polled or handled via interrupt without blocking the CPU. If the hardware supports it, I'd structure the flash operation as a state machine: start the erase, yield to the scheduler, and resume when the erase-complete interrupt fires. This turns a blocking operation into a non-blocking one.

If the flash controller genuinely blocks the CPU (some do, especially on smaller parts), then I'd need to reconsider the architecture. Options include: moving the flash write to a dedicated lower-priority task and accepting that the sensor task will preempt it (which works if the sensor task's 1 ms deadline is hard and the flash operation can tolerate being interrupted mid-erase — though this depends on the flash controller's behavior); using a secondary storage device (e.g., external SPI flash) that doesn't block the CPU; or buffering sensor data in RAM and performing the flash write in a way that doesn't conflict with the sensor timing.

The key trade-off is between data integrity and real-time guarantees. For a medical device, I'd also consider whether losing sensor data during a flash erase is clinically acceptable. If not, I'd ensure the sensor task has priority and the flash operation is designed to be interruptible or deferred. I'd also verify the actual worst-case erase time on the specific hardware — datasheet values are often optimistic, and temperature/voltage variations can extend erase times.

**Possible follow-ups:** How would you handle the case where the flash erase cannot be interrupted and the sensor data is critical? What if the sensor task's deadline is 1 ms but the flash erase blocks for 100 ms — would you consider using a second MCU?

---

## Q2: How would you approach implementing a circular buffer for a data acquisition system that captures sensor samples at 10 kHz and processes them in bursts, where the buffer is shared between an ISR (writing) and a task (reading)?

**Answer:** For a single-producer/single-consumer circular buffer, I'd use a lock-free design with head and tail indices, where the ISR only updates the write index and the task only updates the read index. The key is that each side only reads the other side's index — never writes it — so there's no race condition as long as the indices are read/written atomically. On most embedded platforms, a 16-bit or 32-bit aligned index read/write is atomic, but I'd verify this on the specific architecture and use volatile or appropriate memory barriers if needed.

The buffer size needs to accommodate the burst processing pattern: if the task processes in bursts every N milliseconds, the buffer must hold at least the number of samples generated during that interval plus margin. I'd calculate: samples per burst period × sample size, plus headroom for interrupt latency and scheduling jitter. I'd also consider using a power-of-two size so the wrap-around can use a mask instead of a modulo operation.

Pitfalls I'd watch for: the classic full-vs-empty ambiguity (where head == tail could mean either empty or full) — I'd resolve this by either keeping one slot always empty or tracking a count. I'd also be careful about memory barriers on multi-core systems or when the compiler could reorder reads/writes. On single-core systems, I'd ensure the ISR and task code are compiled with appropriate volatile qualifiers. For overflow handling, I'd decide upfront whether to drop the newest sample (overwrite) or drop the oldest (block the writer) — for medical data, silently dropping samples is usually unacceptable, so I'd flag overflow as an error condition that the system can detect and respond to.

**Possible follow-ups:** How would you handle the case where the reader task is delayed and the buffer overflows? Would you use a different approach if there were multiple producers?

---

## Q3: You're reviewing a colleague's firmware code that uses a watchdog timer that kicks in the main loop. The device occasionally resets during a lengthy calibration routine that takes 3 seconds. The colleague proposes increasing the watchdog timeout to 5 seconds. How would you guide them?

**Answer:** Increasing the watchdog timeout is treating the symptom, not the cause. The real issue is that the main loop is blocked for 3 seconds, which means the watchdog can't be kicked — but it also means the system is unresponsive to other tasks, communication, and safety checks for that entire period. In a medical device, that's a much bigger concern than the watchdog reset itself.

I'd first ask what the calibration routine is doing for those 3 seconds. Is it genuinely busy-waiting on hardware, or is it polling a sensor that could be checked asynchronously? If the routine can be restructured into smaller steps — for example, a state machine that advances one step per main-loop iteration — then the watchdog can be kicked normally and the system remains responsive throughout. This is the preferred approach.

If the calibration genuinely requires a continuous 3-second operation (e.g., waiting for a sensor to stabilize), then I'd consider kicking the watchdog from a timer ISR during that period, but only if the system is actually healthy — meaning the ISR is still running and the CPU isn't hung. This is a legitimate pattern: the watchdog verifies that interrupts are still functioning, not just that the main loop is running. However, I'd want to ensure that the ISR-based kick doesn't mask a real fault, such as the main loop being stuck in an infinite loop while interrupts still fire.

I'd also look at whether the calibration routine has proper error handling — if the sensor never stabilizes, does the routine hang forever? A watchdog that resets the device after 3 seconds might be the only thing preventing a permanent hang. Increasing the timeout to 5 seconds would extend that window and potentially delay recovery from a genuine fault.

The right answer depends on the system's safety analysis. I'd guide the colleague to first understand why the routine takes 3 seconds, then restructure it to be non-blocking if possible, and only consider adjusting the watchdog timeout if the analysis shows the longer timeout doesn't compromise fault detection.

**Possible follow-ups:** What if the calibration routine genuinely cannot be broken into smaller steps? How would you verify that kicking the watchdog from an ISR doesn't mask a real system fault?

---

## Q4: You're debugging a firmware issue where a device's ADC readings are correct when the device is first powered on, but drift and become noisy after about 30 minutes of operation. The device is battery-powered and uses a switching regulator. How would you approach this?

**Answer:** I'd approach this systematically, starting with the hypothesis that the issue is thermal — the device heats up over 30 minutes, and a component's characteristics change with temperature. The switching regulator is a prime suspect: as it heats up, its output ripple or noise characteristics can change, and if the ADC reference or analog supply is derived from it, that noise couples into the readings. I'd first check the ADC reference voltage stability — if the reference drifts, the readings will drift proportionally. I'd measure the reference voltage and the analog supply rail over time using an oscilloscope, ideally with the device in a thermal chamber or at least monitoring ambient temperature.

Another angle is the battery itself. As the battery discharges, its internal resistance increases and the voltage sags under load. If the switching regulator's input voltage drops, it may enter a different operating mode (e.g., PFM vs PWM) that has different noise characteristics. I'd check the battery voltage profile over the 30-minute window and correlate it with the ADC drift.

I'd also consider the ADC's own thermal drift — many ADCs have a temperature coefficient on their internal reference or gain. If the device uses the internal ADC reference, that could be the culprit. I'd test this by comparing readings against a known stable voltage source (e.g., a precision reference) while monitoring the board temperature.

In firmware, I'd add diagnostics: log the ADC raw values, the reference voltage (if measurable), and the device temperature over time. This data would help correlate the drift with a specific cause. I'd also check whether the firmware has any averaging or filtering that might be affected by the noise — for example, if the noise is intermittent, a median filter might behave differently than a moving average.

Finally, I'd look at the PCB layout — is the ADC's analog ground properly separated from the switching regulator's ground? Is there adequate decoupling on the analog supply? These issues might not show up immediately but could manifest as the regulator's switching characteristics change with temperature.

**Possible follow-ups:** How would you distinguish between a thermal drift issue and a battery-discharge issue? What firmware-side mitigations might you consider if the hardware fix requires a board revision?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** I'd frame this as a design decision that should be driven by the specific requirements of the protocol, not by personal preference. The first step is to understand the protocol's characteristics: How many states and transitions are there? Are the transitions mostly deterministic, or do they depend on complex conditions? How likely is the protocol to change in the future? What are the safety implications of a bug in the transition logic?

For a protocol with a small number of states (say, fewer than 10) and straightforward transitions, a hand-coded state machine is often the right choice — it's readable, easy to trace in a debugger, and the control flow is explicit. For a protocol with many states, many transitions, or a high likelihood of future changes (e.g., adding new message types), a table-driven approach can be more maintainable because adding a new state or transition is just adding a row to a table, not modifying control flow.

I'd also consider the team's familiarity with each approach. A table-driven design can be harder to debug because the control flow is data-driven — you can't just step through the code to see what happens next; you have to look up the table entry. However, if the table is well-structured and the transition conditions are clear, this can be mitigated.

For a medical device, I'd weigh the safety analysis implications. A state machine is often easier to verify against a formal specification because the states and transitions map directly to the spec. A table-driven approach can be harder to formally verify unless the table itself is treated as data and validated separately.

I'd suggest the team prototype both approaches for a small subset of the protocol and evaluate them against criteria we agree on upfront: readability, testability, ease of adding a new state, and debug-ability. I'd also ask them to consider the long-term maintenance burden — who will be maintaining this code in two years, and which approach would they be more comfortable with?

Ultimately, I'd guide the team to a decision based on the protocol's complexity and the team's ability to maintain the chosen approach, not on which engineer argues more persuasively. If the protocol is genuinely complex, I might suggest a hybrid: a state machine for the high-level flow, with table-driven handling for specific sub-protocols or message types.

**Possible follow-ups:** How would you handle the situation if one engineer strongly prefers their approach and is resistant to the other? What criteria would you use to evaluate the two prototypes?