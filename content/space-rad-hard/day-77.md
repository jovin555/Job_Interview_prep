# space-rad-hard — Day 77

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd treat this as three separate problems that happen to share a connector: input ORing, per-feed fault isolation, and inrush management.

For input ORing, the goal is that either bus can independently power the load, and a fault on one input cannot back-feed or drag down the other. A common approach is ideal-diode ORing using either dedicated ORing controllers or back-to-back MOSFETs driven by a controller that monitors both forward voltage and reverse current. The key design point is that the ORing element must block reverse current quickly — if one feed shorts, the ORing device on that feed has to turn off before the good feed's voltage collapses. I'd size the reverse-current trip threshold and response time against the worst-case fault, and I'd verify the two feeds can't fight each other through the ORing path during a transient.

For per-feed fault isolation, I'd put a current-limiting or e-fuse stage on each input, ahead of the ORing. That stage does two jobs: it limits the current the payload can draw from a faulted feed, and it can latch off a feed that's drawing sustained overcurrent (which is what a latch-up event looks like from the bus's perspective). The latch-off should be resettable by command or by a supervised retry, not automatic — automatic retry into a persistent short just cooks the board. I'd also make sure the fault on one feed is reported as telemetry so the ground can see which feed tripped.

For hot-swap, the concern is inrush into the payload's bulk capacitance when a feed is connected or reconnected. Without control, that inrush can sag the bus and trip upstream protection. I'd use a hot-swap controller with a controlled slew rate on the pass FET's gate, plus a dV/dt limit or a current-limited startup ramp, so the bulk caps charge at a bounded rate. The hot-swap controller also gives you the current-limit and fault-timing functions you need for the isolation stage, so it's often the same part.

The interactions matter more than the individual blocks. The ORing controller's reverse-current threshold has to be compatible with the hot-swap controller's current limit, or a hot-swap event on one feed can look like a reverse-current event on the other. And the whole chain has to be evaluated for single-event effects — an SET on the ORing controller's gate drive could momentarily forward-bias the wrong path, so I'd want parts with SET characterization or add filtering and voting on the control signals.

**Possible follow-ups:**
- How would you decide between a latching fault response and an auto-retry response for the per-feed isolation stage?
- If the ORing controller has no radiation data, what would you do to bound the risk of an SET causing a cross-feed fault?

## Q2: How would you approach selecting and qualifying a voltage supervisor or reset IC for a space-deployed system, given that most commercial parts are not radiation-characterized?

**Answer:** I'd start by being clear about what the supervisor actually has to do, because that determines how much radiation risk I can tolerate. A supervisor that only holds reset low during power-up and releases it once the rail is valid is a fairly benign function — if it misbehaves, the worst case is usually a delayed or spurious reset, which the system can often absorb. A supervisor that gates a critical enable or that must assert reset on a brownout during a critical operation is a different risk class, because a failure there can leave the system in an undefined state.

Given that, my selection process would be: first, look for a part with published TID and SEE data, even if it's not on a QML. Some commercial supervisors have single-event test reports available, and a part with characterized LET threshold and no destructive events is far easier to justify than one with no data at all. Second, if no data exists, look at the process and topology. A supervisor built on a bandgap reference and a comparator has a different radiation response than one with internal digital state or an internal oscillator — the latter has more upset modes. Third, consider whether I can make the function radiation-tolerant by design rather than by part selection: for example, use a discrete comparator with a rad-tolerant reference and an RC time constant instead of an integrated supervisor, so the critical elements are ones I've characterized.

For qualification, if I can't get data and can't redesign around it, I'd plan a targeted test. A supervisor is a small, cheap part, so a limited test campaign — TID to the mission dose with margin, and heavy-ion or proton at a few angles — is often affordable. I'd test the specific failure modes I care about: does the threshold shift with dose, does it false-trip under heavy ions, does it latch up. I'd also test at the dose rate and temperature I expect, because ELDRS and temperature can change the answer.

The fallback, if testing isn't possible, is to design so the supervisor's failure is not catastrophic: add an independent reset path (a second supervisor from a different vendor, or a discrete watchdog-driven reset), and make the system's behavior on a spurious reset safe. That's not as good as a qualified part, but it's a defensible engineering position if the function is genuinely non-critical.

**Possible follow-ups:**
- How would you structure a limited radiation test campaign for a supervisor if you only had budget for one beam run?
- What would make you decide that a supervisor function is critical enough that a COTS part is simply not acceptable?

## Q3: How would you approach designing a radiation-tolerant analog signal chain for a spacecraft instrument where the sensor output is a low-level differential signal, and both the amplifier front-end and the ADC reference can experience single-event transients (SETs)?

**Answer:** The core problem is that a low-level differential signal has very little margin against a transient, so an SET anywhere in the chain can produce a reading that looks like a real measurement. I'd approach it in layers: reduce the probability of an SET reaching the output, detect it when it does, and make the system's response to a bad reading safe.

On the front-end, the first lever is the amplifier topology. A differential front-end with good common-mode rejection helps reject common-mode transients, but a differential SET that hits one input and not the other still gets through. I'd look for an instrumentation amplifier or a matched discrete front-end with radiation data, and I'd add input filtering — a differential RC and a common-mode choke — to limit the bandwidth that a transient can couple through. The filter corner has to be chosen against the signal bandwidth, so this is a trade, not a free win.

On the reference, an SET on the reference is particularly nasty because it shifts the entire conversion, not just one sample. I'd use a reference with SET characterization if one exists, and I'd add a large, low-ESR bypass right at the reference pin to slow the transient. If the reference is a critical single point, I'd consider a redundant reference with a comparator that flags a deviation, or a ratiometric approach where the reference and the signal share a common node so a transient on the reference partially cancels.

On detection, the practical approach is to look for physically implausible readings. A low-level sensor signal has bounded rate of change — if the ADC reports a step that exceeds what the sensor can physically produce, that's a flag. I'd implement a plausibility check in firmware: rate limiting, comparison against a redundant channel, or a median-of-three on consecutive samples. The check has to be tuned so it doesn't reject real fast events, which means I need to know the sensor's actual bandwidth.

On system response, the key question is what happens when a bad reading is detected. If the measurement feeds a control loop, the safe response is usually to hold the last good value or fall back to a safe default until the reading is confirmed, not to act on the transient. That requires the control loop to tolerate a brief hold, which is a system-level design decision, not just an analog one.

**Possible follow-ups:**
- How would you distinguish an SET from a real fast transient in the sensor signal, given that both can look like a step?
- If the reference and the signal path share a supply, how does that change your filtering strategy?

## Q4: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the technical question from the interpersonal one. The engineer has done real work, which means they've thought about the problem and probably have reasons for their choice. My job in the review is to find out whether those reasons hold up against the radiation environment, not to win an argument.

I'd start by asking them to walk me through their margin analysis — specifically, what environment they assumed, what part data they used, and where the margin comes from. Often the disagreement is not about the conclusion but about the assumptions. If they assumed a lower dose, or used a typical value instead of a worst-case value, or didn't account for ELDRS, that's a concrete, non-personal thing to discuss. I'd frame it as "help me understand how you got here" rather than "this is wrong."

If the assumptions are sound and the margin is genuinely thin, I'd focus on the consequence of being wrong. A thin margin on a non-critical function might be acceptable; a thin margin on something that can take the system down is not. That reframes the discussion from "is 20% enough?" to "what happens if it's not enough, and can we live with that?" That's usually a more productive conversation because it's about risk, not about who's right.

If we still disagree after that, I'd want to bring in evidence rather than authority. That could mean asking for a test, a second opinion from someone with radiation experience, or a review of the part's actual test data. If the engineer is confident, the best outcome is that they're right and we've verified it; if they're wrong, the evidence makes that clear without me having to assert it.

Throughout, I'd keep the tone collaborative. The engineer's work is valuable, and the goal is a design that survives the mission, not a design that matches my preference. If I end up overruling them, I'd explain the reasoning clearly and document it, so the decision is traceable and they understand it wasn't arbitrary.

**Possible follow-ups:**
- What would you do if the engineer's analysis was correct but the schedule didn't allow for the test you wanted?
- How would you handle it if the same engineer made a similar under-margined proposal on the next review?

## Q5: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a poor fit for a radiation environment in some ways — it's a shared, open-drain bus with no inherent error detection, and a single stuck node can hold SCL or SDA low and take the whole bus down. So the design has to compensate for the protocol's weaknesses.

The first layer is electrical. I'd use a bus with proper pull-ups sized for the bus capacitance and speed, and I'd consider a bus buffer or a mux that isolates segments so a fault on one segment doesn't kill the whole bus. If the nodes are physically distributed, segmenting the bus with a buffer that can be commanded to disconnect a bad segment is worth the complexity. I'd also add series resistors on the lines to limit the current a stuck node can sink, which reduces the chance of damage and makes recovery easier.

The second layer is protocol. I²C has no CRC, so I'd add one at the application layer — every message carries a checksum, and the receiver rejects anything that doesn't match. I'd also add sequence numbers or a transaction ID so a duplicated or reordered message is detectable. For critical data, I'd use a request-response pattern with an explicit acknowledgment rather than relying on the bus's ACK bit, because the ACK bit itself can be corrupted.

The third layer is recovery. The classic I²C lock-up is a slave holding SDA low mid-transaction. The standard recovery is to clock SCL manually for nine or more cycles until the slave releases SDA, then issue a STOP. I'd implement that in the master's firmware as an automatic recovery routine, triggered when a transaction times out. I'd also add a bus reset — a GPIO that can power-cycle or reset the bus segment — as a last resort.

The fourth layer is redundancy where it matters. If a sensor reading is critical, I'd either duplicate the sensor on a second bus or use a different protocol (SPI with a dedicated chip select, or a differential bus like RS485) for the critical path, so a single I²C fault doesn't take out the critical measurement. That's a system-level decision about which data is truly critical.

Finally, I'd make sure the master's own state is recoverable. If the master's I²C peripheral gets into a bad state, a watchdog-driven reinitialization of the peripheral should be part of the recovery flow, not just a bus-level recovery.

**Possible follow-ups:**
- How would you decide which sensors are critical enough to justify a redundant bus?
- What's the trade-off between segmenting the bus with buffers and keeping it simple with a single segment?