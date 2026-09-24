# firmware — Day 65

## Q1: How would you approach designing a firmware module that must handle a sensor whose data-ready signal can arrive at any time, but whose data must only be read after a minimum settling delay that varies with temperature?

**Answer:** The core problem is that the trigger event (data-ready) and the validity window (settling delay) are decoupled, and the delay is not a fixed constant. I'd start by modeling the sensor's timing as a function of temperature — either from the datasheet curve or from characterization data — and encode that as a lookup table or a simple polynomial in firmware. The data-ready signal itself should be treated as a hint, not a guarantee: it tells you the conversion has started or completed, but not that the output is stable.

Architecturally, I'd separate the three concerns: detection (ISR or polling on the data-ready line), scheduling (a deferred context that waits out the settling delay), and acquisition (the actual read). The ISR should do the minimum — timestamp the event, set a flag, maybe kick a work item — and the settling delay should be handled in a thread or work queue using a timer, not a busy-wait. If the delay is temperature-dependent, I'd read the temperature sensor first (or use the last known value if it changes slowly), compute the required delay, and arm a one-shot timer for that duration.

The subtle part is what happens if a new data-ready arrives before the previous settling delay has elapsed. That's a design decision: either you drop the new event (if the sensor's rate is slower than the settling time, this shouldn't happen), or you queue it, or you treat it as an error condition. I'd want that behavior explicitly defined and tested, because it's exactly the kind of edge case that shows up in the field but not on the bench.

For verification, I'd instrument the firmware to log the actual measured delay between data-ready and read, and compare it against the expected settling time across the temperature range. If the margin is thin, that's a sign the model is wrong or the sensor is being pushed too hard.

**Possible follow-ups:**
- How would you handle the case where the temperature sensor itself has a slow response time relative to how fast the sensor's settling time changes?
- If the settling delay is long enough that it spans multiple data-ready events, how would you restructure the acquisition pipeline?

## Q2: You're debugging a firmware issue where a device's behavior is correct when powered from a bench supply but intermittently wrong when powered from a battery, and the wrong behavior correlates with the device transmitting wirelessly. How would you approach this?

**Answer:** The correlation with wireless transmission is the strongest clue — it points at a supply-rail disturbance rather than a logic bug. Wireless transmitters draw current in bursts, and a battery has higher source impedance than a bench supply, especially as it discharges. That burst current can cause a transient droop on the rail that affects analog references, ADC readings, or even the MCU's own core voltage if decoupling is marginal.

I'd approach it in layers. First, confirm the hypothesis: scope the supply rail at the MCU and at any analog front-end during a transmit burst, with the device on battery. Look for droop, ringing, or a slow recovery. Compare against the same measurement on the bench supply. If the rail is clean on the bench and dirty on battery, that's the mechanism.

Second, narrow the affected subsystem. Is it the ADC readings that go wrong, or is it the MCU misbehaving (resets, corrupted state)? If it's the ADC, the issue may be that the reference is derived from the same rail that's drooping, so the readings shift. If it's the MCU, it may be a brownout or a marginal decoupling issue. The fix is different in each case: a separate reference for the ADC, more bulk capacitance near the transmitter, a softer transmit ramp, or sequencing so the ADC isn't sampling during a transmit burst.

Third, consider whether the firmware can mitigate it. If the transmit burst is under firmware control, you can schedule ADC sampling to avoid the burst window, or add a settling delay after the burst before resuming sensitive measurements. That's a band-aid if the hardware is marginal, but it's a legitimate mitigation if the hardware is otherwise fine and the timing just happens to overlap.

The key is not to jump to a firmware fix before understanding the mechanism. A firmware workaround on top of a hardware problem tends to fail in a different way later.

**Possible follow-ups:**
- How would you distinguish between a brownout reset and a corrupted-but-still-running condition?
- If the fix requires a hardware change but you need a firmware mitigation to ship first, how would you scope and document that?

## Q3: How would you approach implementing a firmware module that must maintain a monotonic event log across a device that frequently enters and exits low-power sleep, where the log must remain correctly ordered even if the device resets unexpectedly?

**Answer:** The hard requirement is monotonicity across sleep and reset, which means the timestamp source can't be a simple free-running counter that resets on power loss. I'd separate the problem into two parts: a persistent time base and an in-RAM ordering mechanism.

For the persistent time base, the options are an RTC with a battery backup, a counter stored in non-volatile memory that's incremented on each wake, or a hybrid where the RTC provides coarse time and a RAM counter provides fine resolution within a wake period. The choice depends on what hardware is available and how much drift is acceptable. If there's no RTC, a monotonic counter in flash or EEPROM works, but you have to handle the write endurance — you can't increment it on every event. A common approach is to write a "boot epoch" value on each wake and combine it with a RAM counter for events within that epoch.

For ordering across reset, the log entries themselves need a sequence number that's assigned before the write and persisted with the entry. If the device resets mid-write, the entry is either complete (with a valid sequence number) or incomplete (and should be discarded on recovery). A CRC or a commit marker at the end of each entry handles that. On boot, the firmware scans the log, finds the last valid entry, and resumes from there.

The subtlety is what "monotonic" means when the device resets. If the RTC is battery-backed, time continues across reset and there's no ambiguity. If it's not, you have a gap, and the log needs to represent that gap explicitly rather than pretending it didn't happen. I'd design the log format to include a boot ID or epoch field so a reader can tell that entries on either side of a reset came from different sessions.

For testing, I'd deliberately power-cycle the device at random points during log writes and verify that the log is always readable and correctly ordered afterward. That's the only way to be confident the recovery logic actually works.

**Possible follow-ups:**
- How would you handle the case where the RTC itself drifts or is reset, and the log needs to remain internally consistent even if absolute time is wrong?
- What would you do if the flash write endurance is too low to write a boot epoch on every wake?

## Q4: A junior engineer on your team has implemented a firmware module that uses a single global state variable to track the device's operational mode, and multiple modules read and write it directly. The code works, but you're concerned about safety and maintainability. How would you guide them?

**Answer:** I'd start by understanding why they chose that approach — often it's because the module boundaries weren't clear when the code was written, and the global was the path of least resistance. I wouldn't lead with "this is wrong"; I'd lead with the specific failure modes it enables, because that's what makes the concern concrete rather than stylistic.

The concrete risks are: any module can transition the device to any state without going through validation, so illegal transitions become possible; there's no single place to add logging or assertions; and testing a module in isolation requires setting up global state that the module doesn't own. In a medical device context, the first one is the serious one — an illegal transition (say, from "active monitoring" directly to "idle" without going through a safe state) is a safety issue, not just a code-quality issue.

The refactor I'd guide them toward is to make the state variable private to a state-machine module, with a narrow API: a function to request a transition (which validates it against the current state and the event), a function to query the current state, and a callback or notification mechanism for modules that need to react to transitions. That way the state machine owns the transitions, and other modules observe rather than mutate.

I'd also suggest they add a transition table or a set of assertions that encode which transitions are legal, so that an illegal transition is caught at development time rather than in the field. That's the kind of thing that pays off during regulatory review as well, because it makes the intended behavior explicit.

The key is to frame it as "here's what this design makes possible that we don't want" rather than "here's the pattern you should have used." The former is a safety argument; the latter is a style argument, and style arguments don't land as well.

**Possible follow-ups:**
- How would you sequence the refactor so that it doesn't break the existing modules that read the global directly?
- If the state machine needs to be observable by a module that runs in a different thread, how would you handle the notification without introducing a race?

## Q5: How would you approach deciding whether a piece of firmware logic should run in an interrupt context, a deferred context (work queue or thread), or a low-priority background task?

**Answer:** The decision comes down to three questions: how much time does the work take, how deterministic does its timing need to be, and what does it need to touch?

Interrupt context is for work that must happen within a bounded, short time after the event — acknowledging a peripheral, capturing a timestamp, moving a byte into a buffer, setting a flag. The rule of thumb is that an ISR should be measured in microseconds, not milliseconds, and it should not block, allocate, or call anything that might sleep. If the work involves waiting for a peripheral, acquiring a mutex, or doing anything that could take an unbounded amount of time, it doesn't belong in the ISR.

Deferred context — a work queue or a high-priority thread — is for work that's triggered by an interrupt but can tolerate a small, bounded delay. This is where you do the actual processing: parsing a message, running a control calculation, updating a state machine. The delay is bounded by the scheduler, so it's still deterministic enough for most real-time requirements, but it's not as tight as an ISR.

Low-priority background tasks are for work that has no hard deadline: logging, telemetry, housekeeping, non-critical configuration updates. These can be preempted by anything and shouldn't hold resources that higher-priority work needs.

The tricky cases are the ones that sit on the boundary. A flash write, for example, takes milliseconds and can't be done in an ISR, but it also can't be preempted mid-write without risking corruption. That's a case where you need a dedicated context with a clear ownership model, and you need to think about what happens to higher-priority work while it's running. Similarly, a sensor read that takes 500 µs might be fine in a work queue but not in an ISR if the ISR latency budget is tight.

I'd also consider the failure mode: if the work is delayed, what breaks? If the answer is "nothing, it just happens later," it can go in a low-priority task. If the answer is "we miss a deadline and the system misbehaves," it needs a higher-priority context with a bounded latency.

**Possible follow-ups:**
- How would you measure the actual latency of a deferred context to confirm it meets the requirement?
- If a piece of work needs to run in a deferred context but also needs to be serialized with another piece of work in a different context, how would you handle the synchronization?