# firmware — Day 24

## Q1: You're debugging a firmware issue where a device's real-time clock (RTC) drifts significantly when the device is in low-power mode, but is accurate when running normally. The device uses an external 32.768 kHz crystal. How would you approach this?

**Answer:** This is a classic low-power RTC drift problem, and I'd approach it systematically. First, I'd confirm the drift magnitude and direction — is it gaining or losing time, and by how much? That tells me whether the oscillator is running fast or slow in sleep mode.

The most common root cause is that the crystal oscillator circuit is operating in a different regime during low-power mode. When the MCU enters deep sleep, the internal oscillator driver circuitry may change its bias conditions, or the load capacitance seen by the crystal may shift because other circuitry on the same pins or power domain is powered down. I'd check the crystal's load capacitance specification against the actual PCB parasitic capacitance and the MCU's internal load capacitance settings — a mismatch that's tolerable during normal operation can become significant when the oscillator is running at reduced drive levels.

Another angle is the power supply. In low-power mode, the regulator may be in a different mode or the supply voltage may droop slightly, which can shift the oscillator's operating point. I'd measure the supply voltage and the oscillator waveform during sleep mode using a high-impedance probe or by temporarily forcing the device to stay awake while replicating the sleep-mode power conditions.

I'd also check whether the RTC is actually running from the crystal during sleep, or if the firmware is switching to a different clock source (like an internal RC oscillator) to save power. If the firmware is gating the crystal oscillator or switching clock sources during sleep, that would directly explain the drift. I'd review the clock configuration code for the sleep path.

Finally, I'd consider temperature effects. If the device is in a different thermal environment during sleep (e.g., inside an enclosure, near other components that are powered down), the crystal's temperature coefficient could cause drift. I'd log the temperature alongside the RTC drift to see if there's a correlation.

**Possible follow-ups:** How would you determine whether the issue is hardware (crystal/capacitance) versus firmware (clock source switching)? What measurements would you take to isolate the cause?

---

## Q2: How would you approach implementing a firmware module that must handle a sensor which occasionally returns invalid data (e.g., out-of-range values or CRC failures), where the device is a medical monitor that must never display a false reading to the clinician?

**Answer:** The core principle here is that the firmware must distinguish between "no data available" and "invalid data" and handle both without ever presenting a false reading. I'd start by defining what "invalid" means for each sensor parameter — out-of-range values, CRC mismatches, values that violate rate-of-change limits, or values that fail consistency checks against other sensors.

The architecture would have three layers. First, the driver layer validates raw data at the point of acquisition: check CRC, verify the frame structure, and reject obviously corrupt data. Second, a validation layer applies domain-specific checks — physiological plausibility, rate-of-change limits, and cross-sensor consistency. Third, the application layer decides how to respond: retry, use the last valid reading with a timestamp, or mark the parameter as unavailable.

For a medical monitor, the critical design decision is what to display when data is invalid. The safest approach is to display the last valid reading with a clear "data stale" indicator, and after a defined timeout, display "no data" or "sensor error" rather than extrapolating. The clinician must never see a value that could be misinterpreted as a current measurement when it isn't.

I'd also implement a retry strategy with bounded retries — retrying indefinitely can mask a genuine sensor failure. The retry logic should be time-boxed, and the device should transition to a degraded state with an audible or visual alarm if the sensor doesn't recover.

For the "never display a false reading" requirement, I'd add a final safety check at the display layer: any value that reaches the UI must have passed all validation checks and must have a timestamp within a defined freshness window. This belt-and-suspenders approach ensures that even if a bug in an upstream layer lets invalid data through, the display layer catches it.

**Possible follow-ups:** How would you handle a sensor that returns plausible but incorrect values (e.g., a pressure sensor that reads consistently 10% high)? How would you design the degraded-state indication so it's clear to the clinician without being alarming?

---

## Q3: You're designing a Zephyr RTOS-based system where a high-priority sensor task must read data every 1 ms, but a lower-priority task occasionally needs to perform a flash erase that blocks for up to 100 ms. How would you approach this scheduling conflict?

**Answer:** The fundamental problem is that a blocking flash erase in a lower-priority task can stall the entire system, including the high-priority sensor task, because the flash controller is typically shared and the erase operation blocks the CPU or the bus. I'd approach this in layers.

First, I'd check whether the flash erase can be performed without blocking the CPU. Many MCUs have a flash controller that can perform erase operations in the background while the CPU continues executing from RAM. If the hardware supports this, I'd copy the erase routine to RAM and use the flash controller's interrupt or status flag to know when the erase completes. This is the cleanest solution because the sensor task never stalls.

If the hardware doesn't support background erase, I'd look at whether the flash erase can be broken into smaller operations. Some flash controllers allow erasing by sector or even by page, and the erase time scales with the size. If I can erase smaller chunks, I can interleave the erase with sensor reads — erase one sector, let the sensor task run, erase the next sector, and so on. This requires the flash driver to be reentrant or at least designed to yield between chunks.

Another approach is to use Zephyr's flash API with a dedicated flash thread at a priority below the sensor task, and accept that the sensor task will preempt the erase. But if the erase blocks the CPU, preemption doesn't help — the CPU is stuck in the erase loop. So the real question is whether the hardware allows the CPU to execute other code during the erase.

If none of the hardware options work, I'd reconsider the design. Can the data that needs to be stored in flash be buffered in RAM and written later? Can the flash write be deferred to a time when the sensor task isn't running (e.g., during a low-activity period)? Can the sensor data be stored in a larger RAM buffer and flushed less frequently? These are system-level trade-offs that might be more practical than fighting the flash controller.

I'd also verify the actual worst-case erase time on the specific hardware — datasheet values are often optimistic, and the real time depends on temperature, supply voltage, and the number of program/erase cycles the flash has already endured.

**Possible follow-ups:** How would you handle the case where the sensor task must not miss a single sample, even during the flash operation? What if the flash erase time is not deterministic?

---

## Q4: You're reviewing a colleague's firmware code that uses a large number of global variables to share state between modules. The code works correctly in testing but is difficult to maintain and test. How would you approach refactoring this without introducing regressions?

**Answer:** Refactoring a working system that's hard to maintain is a delicate operation — the worst outcome is breaking something that already works. I'd approach it as a series of small, verifiable steps rather than a big-bang rewrite.

First, I'd establish a safety net. Before changing anything, I'd make sure there's adequate test coverage — unit tests for the modules that use the globals, and integration tests that exercise the full system. If tests don't exist, I'd write characterization tests that capture the current behavior, even if that behavior isn't ideal. These tests document what the system actually does, which is the ground truth for the refactor.

Next, I'd categorize the globals. Some globals are truly shared state that multiple modules need to access — those need a proper interface. Others are effectively module-private state that happens to be global — those can be made static and moved into the module that owns them. Still others might be configuration values that should be passed as parameters or stored in a configuration structure.

For the truly shared state, I'd introduce accessor functions or a small state-management module that owns the data and exposes a controlled interface. The key is to start with the interface and keep the underlying storage as-is initially — so the refactor is behavior-preserving. Once the interface is in place, I can change the storage mechanism (e.g., from a global struct to a module with private state) without touching the rest of the system.

I'd also look for patterns in how the globals are used. If multiple globals are always read or written together, they likely belong in a single struct. If a global is written in one module and read in several others, that's a dependency that should be made explicit through the interface.

Throughout the refactor, I'd keep each change small and run the test suite after every step. If a change causes a regression, it's much easier to isolate when the change is small. I'd also use static analysis tools to find all references to each global before moving it, so nothing is missed.

Finally, I'd document the new architecture — the ownership model for each piece of state, the interfaces, and the rationale. This prevents the next person from reintroducing globals because they didn't understand the design.

**Possible follow-ups:** How would you prioritize which globals to refactor first? How would you handle a global that is written from an interrupt context and read from a task context?

---

## Q5: You're leading a firmware team where two senior engineers disagree on whether to use a state machine pattern or a table-driven approach for implementing a complex device protocol. One argues that a state machine is more readable and easier to debug, while the other argues that a table-driven approach is more maintainable and easier to extend. How would you guide the team to a decision?

**Answer:** This is a classic design trade-off, and my role as the lead is to make sure the decision is based on the specific requirements of the protocol and the team's ability to maintain it — not on personal preference or dogma.

First, I'd ask both engineers to articulate the concrete requirements that matter for this protocol: How many states and transitions are there? How often will the protocol change? Who will maintain it — the current team or future engineers who may not have been involved in the design? What are the failure modes — is it safety-critical, and how will the implementation be verified?

I'd also ask them to sketch a small but representative portion of the protocol in both styles — say, the connection establishment and error handling — so we can compare them side by side. This grounds the discussion in the actual problem rather than abstract arguments.

For a protocol with a small, stable number of states, a hand-coded state machine is often the right choice. It's explicit, easy to trace in a debugger, and the control flow is visible in the code. For a protocol with many states, complex transition conditions, or frequent changes, a table-driven approach can be more maintainable because adding a state or transition is a data change, not a code change. The table also serves as documentation of the protocol itself.

I'd also consider the team's experience. If the team is more comfortable with one style, that's a real factor — a well-implemented state machine by a team that understands it is better than a poorly implemented table-driven approach by a team that doesn't. But I'd also weigh the long-term maintainability: if the protocol is likely to grow, the table-driven approach might be worth the initial learning curve.

For a safety-critical device, I'd also think about verification. A table-driven approach can be easier to verify systematically — you can enumerate all transitions from the table and check them against the specification. A hand-coded state machine might be easier to review for correctness but harder to exhaustively test.

My decision framework would be: if the protocol is small and stable, go with the state machine. If it's large, complex, or likely to evolve, go with the table-driven approach. If it's in between, I'd consider a hybrid — a table for the transition logic with explicit handler functions for each state's actions, which gives some of the benefits of both.

I'd also make sure the decision is documented — the rationale, the trade-offs considered, and the chosen approach — so that future engineers understand why the design is the way it is. And I'd set up a review point after the implementation is underway to check that the chosen approach is working in practice, with a willingness to revisit if it isn't.

**Possible follow-ups:** How would you handle the situation where one engineer strongly disagrees with the final decision and is reluctant to implement it? What criteria would you use to evaluate whether the chosen approach is working after implementation?