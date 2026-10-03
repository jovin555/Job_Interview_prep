# protocols — Day 74

## Q1: How would you approach debugging a UART link where the receiver reports framing errors only when a high-current load (e.g., a motor or heater) switches on the same board?

**Answer:** Framing errors that correlate with a switching load point strongly toward a noise/ground-integrity problem rather than a baud-rate mismatch, because the UART itself is fine until something injects a transient. I'd approach it in layers:

First, confirm the correlation is real and not coincidental — capture the error with a logic analyzer or scope triggered on the load's enable signal, and look at the UART RX line at the moment of switching. A framing error means the stop bit wasn't where the receiver expected it, so I'd be looking for a glitch that shifts an edge or causes the receiver to sample a false start bit.

Second, look at the physical layer. High-current switching produces fast di/dt, which couples into nearby traces through inductive and capacitive paths, and can also cause local ground bounce if the return path is shared. I'd check whether the UART traces run near the load's power path, whether the ground return for the load is separated from the signal ground, and whether there's adequate decoupling and bulk capacitance near the load. A common fix is to keep the switching return current out of the sensitive signal's reference plane and to add series termination or a small RC filter on the RX line if the noise is fast enough.

Third, check the receiver's input thresholds and whether the idle level is marginal. If the line sits close to a threshold, a small transient can flip it. Hysteresis or a proper line driver/receiver (rather than a bare GPIO) often helps.

Fourth, consider whether the issue is actually a shared-resource problem — e.g., the load switching causes a brief supply droop that resets or disturbs the UART peripheral's clock. That would show up as a different signature (loss of sync, not a single bad frame).

The key is to separate "noise coupled onto the line" from "reference/ground disturbance" from "supply disturbance," because each has a different fix. I'd instrument first, then change one thing at a time.

**Possible follow-ups:**
- How would you decide between adding a filter on the RX line versus fixing the grounding/return path?
- If the noise is common-mode rather than differential, how would that change your approach?

## Q2: How would you approach designing a protocol abstraction layer so that application code can talk to sensors over I2C, SPI, UART, or CAN-FD without knowing which transport is underneath?

**Answer:** The goal is to keep the application's view of a sensor stable while the transport underneath can change — for portability, for board variants, or for testability. I'd structure it in three layers:

A transport layer that exposes a small, uniform interface — something like `open`, `read`, `write`, `ioctl`/`configure`, `close` — with each concrete transport (I2C, SPI, UART, CAN-FD) implementing that interface. The transport layer owns the bus-specific details: addressing, chip-select handling, framing, timing, retries at the link level.

A device/sensor layer that knows the sensor's register map and command set, but talks only through the transport interface. This is where "read the pressure register" lives, expressed in terms of the transport's read/write primitives.

An application layer that consumes sensor-level operations (e.g., "get latest reading") and has no visibility into whether that came over I2C or CAN-FD.

Key design decisions: define the transport interface around what all four can actually support — a lowest-common-denominator plus optional capabilities — rather than forcing every transport to fake features it doesn't have. For example, CAN-FD is message-oriented while I2C is register-oriented, so the interface should probably be byte-buffer based with an explicit length, and let the device layer handle register semantics. Error handling needs a common taxonomy (timeout, NACK/no-response, CRC/framing error, bus busy) so the application can react consistently.

For testability, I'd make the transport interface mockable so the device and application layers can be tested without hardware. And I'd keep configuration (addresses, speeds, timeouts) out of the application code — it belongs with the transport/device binding.

The trade-off is abstraction cost: a generic interface can add overhead and can hide transport-specific optimizations. For a medical device where determinism matters, I'd allow the device layer to request transport-specific behavior through a narrow, explicit escape hatch rather than leaking it everywhere.

**Possible follow-ups:**
- How would you handle a transport that needs a different error-recovery model (e.g., CAN-FD error states) without leaking that into the application?
- Where would you put retry logic — transport layer or device layer — and why?

## Q3: In a CAN-FD network, how would you approach guaranteeing that a high-priority safety-critical message is never delayed by more than a bounded time, given that lower-priority telemetry also shares the bus?

**Answer:** This is a real-time schedulability question, and the answer is to reason about worst-case response time, not average behavior. CAN-FD's arbitration is priority-based and non-preemptive once a frame starts, so the worst case for a high-priority frame is: it becomes ready just after a lower-priority frame has started transmitting, and it must wait for that frame to finish (plus any higher-or-equal-priority frames already queued).

So the approach is:

First, assign identifiers so that the safety-critical message has the highest priority (lowest ID) on the bus. In CAN, lower numeric ID wins arbitration, so this is a deliberate design choice.

Second, bound the blocking time. The worst-case delay is the longest lower-priority frame that can be in flight when the critical message becomes ready, plus the transmission time of the critical frame itself, plus any queued higher-priority traffic. To bound this, you either limit the maximum frame size on the bus (CAN-FD allows up to 64 bytes, which is a long blocking time at low bit rate) or you ensure the critical message can't be blocked by a long telemetry frame — for example, by capping telemetry payloads or by scheduling telemetry so it doesn't start just before a critical window.

Third, account for the data-phase bit rate. CAN-FD lets you run the arbitration phase at one rate and the data phase faster, which shortens transmission time for a given payload. But the arbitration phase still runs at the slower rate, so the header/arbitration portion of every frame — including lower-priority ones — contributes to blocking.

Fourth, verify with analysis and then with measurement. I'd do a worst-case response-time calculation (classic CAN schedulability analysis adapted for FD), then confirm on a loaded bus with a scope or bus analyzer, injecting worst-case traffic patterns.

Fifth, consider whether CAN-FD alone can meet the bound. If the required latency is tighter than the bus can guarantee under all conditions, the honest answer may be to give the critical signal a dedicated path (separate bus or a direct line) rather than trying to force it onto a shared bus. That's a design decision, not a firmware trick.

**Possible follow-ups:**
- How does the choice of data-phase bit rate affect the worst-case blocking time for the critical message?
- What would you do if analysis shows the bound can't be met with the current telemetry load?

## Q4: You're debugging an I2C bus where communication works reliably at 100 kHz but produces intermittent NACKs at 400 kHz, with the same devices and the same PCB. How would you approach this?

**Answer:** Same devices, same board, only the speed changed — so the difference is timing margin, and I'd treat it as a signal-integrity and timing-budget problem rather than a protocol bug.

First, check the rise time. I2C is open-drain, so the bus rise time is set by the pull-up resistor and the total bus capacitance. At 100 kHz there's plenty of time for the line to reach a valid high; at 400 kHz the same RC may not settle before the receiver samples, especially on the last device or the far end of a long trace. I'd measure the actual rise time on SDA and SCL at the worst-case point and compare against the I2C spec's limits for fast mode. If it's marginal, the fix is smaller pull-ups (lower resistance) — but that increases current draw and the low-level sink requirement, so it's a trade-off, not a free win.

Second, check bus capacitance. More devices, longer traces, and connector stubs all add capacitance, which slows edges. If the bus is near the 400 pF fast-mode limit, that's a red flag. I'd estimate or measure it.

Third, check for clock stretching. If a slave stretches the clock and the master's timeout is tight, a NACK or timeout can appear at higher speeds where the master is less tolerant. I'd look at whether the NACK correlates with a specific device or a specific transaction.

Fourth, check the addressing and whether a device is actually present and responding — a NACK at 400 kHz but not 100 kHz could also be a device that simply isn't fast-mode capable, or whose internal timing can't keep up. Datasheet review matters here.

Fifth, look at noise coupling. Higher speed means the edges are faster and more likely to couple into adjacent traces; if the board has SDA/SCL running near a switching node, the higher-speed edges may be more susceptible.

The systematic approach: measure rise times and signal integrity first, because that's the most common cause of "works slow, fails fast" on I2C. Then check device capability and clock stretching. Then consider layout.

**Possible follow-ups:**
- How would you calculate the maximum pull-up resistance for a given rise-time target and bus capacitance?
- If reducing the pull-up value fixes it but increases power draw, how would you decide whether that's acceptable in a battery-powered device?

## Q5: How would you approach handling a situation where a junior engineer on your team has implemented a communication protocol incorrectly, and the error is only discovered during regulatory compliance testing, causing a significant schedule delay?

**Answer:** The first priority is to stabilize the situation and protect the patient-facing outcome, then deal with the process failure, then the person — in that order, and without turning it into a blame exercise.

Immediately: confirm the defect, understand its scope (is it one message type, one device, one mode?), and assess whether it's a safety issue or a compliance/documentation issue. If it's safety-relevant, that drives the urgency and the containment plan. I'd pull together the people who can actually fix it — the junior engineer, whoever owns the test, and a reviewer — and get a clear technical picture before committing to a recovery plan.

On the schedule: I'd be honest with stakeholders early rather than optimistic. A compliance-test failure usually means re-testing, which has its own lead time, so the recovery plan needs to account for that. I'd look for whether the fix can be scoped narrowly (a protocol-layer correction) versus requiring broader rework, and whether any partial re-test is possible.

On the process: the real question is why the error survived to compliance testing. That usually points to a gap — missing protocol conformance tests, a review that didn't catch it, or a spec that was ambiguous. I'd treat that as a systemic issue to fix, not just a one-off. Adding protocol-level unit/integration tests and a review checklist for interface behavior is the kind of change that prevents recurrence.

On the person: a junior engineer making a mistake is expected; the failure is in the system that let it reach compliance testing undetected. I'd give direct, private feedback focused on the technical gap and how to catch it earlier, and I'd make sure they're part of the fix rather than sidelined — that's how they learn. If there's a pattern of not asking for review or not testing, that's the conversation. But I wouldn't frame it as "you caused a delay"; I'd frame it as "here's what we all missed and how we change it."

The leadership judgment is to separate the technical recovery, the process fix, and the people management, and not let the schedule pressure push you into skipping the process fix — because that's how the same class of failure recurs.

**Possible follow-ups:**
- How would you decide whether to add a dedicated protocol conformance test phase, and how would you justify the schedule cost?
- If the junior engineer is defensive or blames the spec, how would you handle that conversation?