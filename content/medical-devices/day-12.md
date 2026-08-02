# medical-devices — Day 12

## Q1: How would you approach designing the firmware architecture for a medical device that must maintain a safety-critical monitoring function while also handling non-critical tasks like user interface updates and data logging?

**Answer:** I'd start by separating the firmware into distinct safety-critical and non-critical partitions, both logically and physically. The safety-critical monitoring path—sensor acquisition, signal conditioning, alarm generation—would run on a dedicated high-priority RTOS task with deterministic timing, isolated memory regions where the platform supports it (like MPU-protected regions on Cortex-M devices), and no dynamic memory allocation. Non-critical tasks like UI rendering and data logging would run at lower priorities and be designed so that even if they stall or crash, the monitoring path continues unaffected.

For the communication between partitions, I'd use a message-passing model with bounded queues rather than shared memory, so the non-critical side can't corrupt monitoring data. The monitoring task would be the only one with direct access to the safety-relevant sensor peripherals and alarm outputs. I'd also implement a watchdog strategy that distinguishes between "monitoring is alive" and "UI is responsive"—the safety watchdog should only be fed by the critical path.

On the RTOS side, I'd carefully analyze interrupt latencies and task scheduling to prove worst-case timing for the monitoring loop. If the device uses Zephyr, I'd leverage its kernel objects and static thread configuration to enforce this separation at build time. The key principle is that the safety function must never depend on the health or performance of non-critical features—degraded mode operation should be designed in from the start, not bolted on later.

**Possible follow-ups:** How would you verify that the isolation between critical and non-critical tasks actually holds under fault conditions? What happens when the non-critical side needs data from the monitoring side—how do you prevent it from interfering?

---

## Q2: During design verification, you discover that a medical device's firmware occasionally writes corrupted data to its non-volatile storage, which could affect the integrity of logged physiological data. How would you approach diagnosing and resolving this?

**Answer:** I'd approach this systematically, starting with understanding the failure mode before touching any code. First, I'd characterize the corruption pattern—is it always the same bytes, same addresses, same timing relative to power events or other operations? This data helps narrow the root cause space significantly.

The likely candidates fall into a few categories: power-loss during write operations, insufficient decoupling causing brownouts during flash writes, interrupt interference corrupting the write sequence, or a software bug in the storage abstraction layer. I'd instrument the system to capture the state at the moment of corruption—adding checksums to every write, logging the stack context, and monitoring supply voltage during write operations.

For power-loss corruption, I'd implement a write-ahead logging or double-buffer scheme with a validity flag, so a partially written record is detected and discarded on the next boot. For brownout issues, I'd check the power supply design—flash writes draw significant current, and if the supply dips below the minimum operating voltage, you get undefined behavior. A brown-out detector that triggers a controlled shutdown before the voltage drops too low is often the right mitigation.

I'd also review the interrupt configuration around write operations. If a high-priority interrupt can fire mid-write and the ISR itself writes to the same flash region, that's a classic corruption source. The fix might be as simple as disabling interrupts around the write sequence or moving the write to a dedicated task with proper synchronization.

Finally, I'd add a CRC or checksum to every stored record and implement a validation routine at startup, so any residual corruption is detected and handled gracefully rather than propagating into clinical use.

**Possible follow-ups:** How would you test the fix to prove the corruption is actually resolved? What if the corruption only appears after weeks of continuous operation?

---

## Q3: How would you approach developing a test plan for verifying that a medical device's alarm system meets the requirements of IEC 60601-1-8, given that the device has both visual and audible alarms with different priority levels?

**Answer:** I'd start by mapping the alarm system requirements from IEC 60601-1-8 into a traceable verification matrix. The standard specifies distinct requirements for alarm signals—priority levels (low, medium, high), visual and audible characteristics, and alarm state transitions. Each requirement needs a corresponding test method, and I'd design the plan to verify both the physical characteristics of the alarms and the logical behavior of the alarm system.

For audible alarms, I'd verify frequency content, pulse patterns, and sound pressure levels using calibrated measurement equipment. The standard specifies particular frequency ranges and temporal patterns for different priorities—for example, high-priority alarms have a specific pulse pattern that differs from medium priority. I'd measure these at the distances and angles specified in the standard, typically at 1 meter from the device.

For visual alarms, I'd verify illumination intensity, flash rate, and color coding. The standard requires specific colors for different alarm priorities—red for high, yellow for medium, cyan for low—and specific flash patterns. I'd use photometric measurements to verify these characteristics.

Beyond the physical measurements, I'd test the logical behavior: alarm activation conditions, alarm state transitions (e.g., from high to medium priority), alarm reset behavior, and alarm silencing. I'd create a state-machine-based test matrix that exercises every legal transition and verifies the correct alarm signal for each state. I'd also test the alarm system's behavior under fault conditions—what happens when the alarm itself fails, and how the system indicates that failure.

The test plan would include both automated tests (using a test harness that can simulate sensor inputs and measure alarm outputs) and manual tests where a human observer verifies alarm perception. For the automated portion, I'd use a microphone and photodiode to capture the alarm signals and compare them against the standard's requirements programmatically.

**Possible follow-ups:** How would you handle the requirement that alarm signals must be distinguishable from each other when multiple alarms are active simultaneously? What about alarm fatigue considerations for devices used in home environments?

---

## Q4: You're leading a project where the hardware team has delivered a PCB revision that fixes a known noise issue on the analog sensor front-end, but the new layout introduces a ground loop that could affect EMC performance. The schedule is tight and the EMC test lab is booked for next week. How would you handle this situation?

**Answer:** This is a classic engineering judgment call where you have to balance technical risk against schedule pressure. I wouldn't simply proceed with the EMC test or cancel it outright—I'd first assess the severity of the ground loop issue and whether it's likely to cause a test failure.

I'd start by reviewing the layout change with the hardware engineer to understand the ground loop path. If it's a small loop with minimal current flow, it might not significantly affect radiated emissions or immunity. I'd also look at whether the loop is in the signal path or just in the power return path—a ground loop in the analog front-end is more concerning than one in a non-critical digital section.

If the analysis suggests the risk is manageable, I'd proceed with the EMC test but add a contingency plan. I'd prepare mitigation strategies in advance—ferrite beads, shielding options, or layout tweaks that could be implemented quickly if the test fails. I'd also brief the test engineer on the known issue so they can watch for specific symptoms during the test.

If the analysis suggests the ground loop is likely to cause a failure, I'd consider postponing the test. A failed EMC test isn't just a schedule delay—it can burn significant time and money in debugging and retesting, and it can damage confidence in the design. Sometimes spending a week to fix the layout is faster than going through a test-fix-retest cycle.

In either case, I'd document the decision and the rationale in the design history file. The key is making a deliberate, risk-informed decision rather than letting the schedule make the decision for you.

**Possible follow-ups:** How would you decide whether the ground loop is severe enough to postpone the test? What if the EMC test lab has a long lead time and postponing means a two-month delay?

---

## Q5: How would you approach establishing a post-market surveillance process for a medical device that has been on the market for several years, when the existing process only captures complaints that come through the customer support line?

**Answer:** I'd start by recognizing that post-market surveillance is broader than complaint handling—it's about systematically collecting and analyzing data on the device's real-world performance to identify emerging risks and drive continuous improvement. The current process captures only a fraction of the available information.

I'd expand the data sources to include: service and repair records (which often reveal failure patterns before they become complaints), sales and distribution data (to understand the installed base and exposure), training records (to identify usability issues), and published literature on similar devices. I'd also look at social media and online forums where clinicians sometimes discuss device issues informally—not as a primary source, but as an early-warning signal.

For the analysis side, I'd establish a regular review cadence—monthly for signal detection, quarterly for trend analysis. I'd define clear triggers for deeper investigation: a single serious incident, a cluster of similar complaints, an increase in a specific failure mode, or a trend that suggests a design weakness. Each trigger would initiate a documented investigation following the ISO 14971 risk management framework.

I'd also make sure the process feeds back into the design process. Post-market data should inform design reviews for next-generation products and, when appropriate, trigger updates to the risk management file. If the data reveals a new hazard or a change in risk level, that needs to be documented and addressed through the formal risk management process.

Finally, I'd verify that the process meets regulatory expectations for the markets where the device is sold. Different jurisdictions have different requirements for post-market surveillance—some require periodic safety reports, others require specific timeframes for reporting serious incidents. The process needs to be designed to meet those obligations, not just to satisfy internal quality goals.

**Possible follow-ups:** How would you determine whether a pattern of complaints indicates a reportable event versus normal device variability? How would you handle a situation where post-market data reveals a risk that wasn't identified during pre-market risk analysis?