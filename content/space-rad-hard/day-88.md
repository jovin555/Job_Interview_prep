# space-rad-hard — Day 88

## Q1: How would you approach designing a radiation-tolerant analog-to-digital conversion subsystem where the ADC's voltage reference is a COTS part with no radiation data, and the measurement must hold accuracy over a multi-year mission?

**Answer:** The reference is the accuracy anchor for the whole conversion chain, so a COTS reference with no radiation data is a real risk that has to be characterized or engineered around, not assumed away. I'd start by decomposing the problem: what accuracy does the measurement actually need at end of life, and how much of the error budget can the reference consume? That tells me whether a COTS reference is even viable or whether I need to move to a characterized part.

If I stay with a COTS reference, I'd treat it as an unknown and build in three layers of protection. First, margin: derate the reference's initial accuracy and tempco so that even a pessimistic TID-induced drift still leaves headroom in the error budget — and remember that drift is monotonic over dose, so it doesn't average out. Second, topology: use a ratiometric measurement where possible so the reference error cancels in the ratio, or use a reference with a stable, well-understood bandgap topology and add a second, independent reference for cross-checking. Third, observability: route the reference voltage itself into a monitored ADC channel so the system can detect drift in flight and either compensate in firmware or flag the channel as degraded.

I'd also plan a characterization path — even a limited TID test at a few dose points on a handful of parts gives far more confidence than a datasheet with no radiation section, and it's usually cheaper than people assume. The key discipline is to make the reference's behavior observable and bounded rather than trusting it silently.

**Possible follow-ups:** How would you distinguish reference drift from ADC drift if both are uncharacterized? What would you do if the reference's drift is non-monotonic and can't be calibrated out?

## Q2: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** The argument conflates two different fault domains. TMR on the digital side protects against upsets in the logic that processes the measurement — it does nothing for an SET that corrupts the analog value before it's ever digitized. A single-event transient on the amplifier output or in the sample-and-hold can produce a plausible-looking but wrong reading, and TMR downstream will faithfully vote on three copies of the same corrupted input. Redundancy only helps if the redundant paths are independent at the point where the fault occurs.

So I'd evaluate the chain by asking: where can a single event inject an error that no downstream mechanism can catch? For a control-loop measurement, the dangerous case is a transient that looks like a valid sample — no out-of-range flag, no CRC failure, just a wrong number that drives an actuator. That's exactly the failure mode single-ended analog is blind to.

Mitigations I'd discuss: spatial or temporal redundancy in the analog path (dual amplifiers feeding separate ADC channels, or repeated sampling with plausibility checks), rate-of-change limiting in firmware so a single wild sample can't move the actuator, and a sanity check against a secondary sensor or a model-based estimate. I'd frame it to the engineer not as "your design is wrong" but as "TMR protects the digital domain; let's map the analog domain's fault paths and decide which ones need coverage." That keeps the review collaborative and gets to a defensible answer.

**Possible follow-ups:** How would you implement a rate-of-change limiter without adding lag that destabilizes the control loop? When would dual analog paths be overkill versus necessary?

## Q3: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a deceptively fragile bus in a radiation environment because it has several failure modes beyond simple data corruption. A clock or data line glitch can leave a slave holding SDA low, which locks the whole bus; a corrupted address or command byte can put a device into an unexpected state; and a stuck node can drag the bus for everyone. So the design has to handle corruption, lock-up, and isolation as separate problems.

For corruption: add a CRC or checksum at the message layer, since I²C's own ACK doesn't detect bit flips in the payload. Use a defined transaction format with a length field and sequence numbers so a truncated or replayed message is rejected. For lock-up: implement bus recovery in the master — clock out up to nine pulses on SCL to let a stuck slave release SDA, then issue a STOP, and only escalate to a power-cycle of the offending node if recovery fails. For isolation: put each node behind a bus switch or expander so a failed node can be electrically removed, and give the master the ability to segment the bus.

I'd also consider whether I²C is the right choice at all for a multi-node space bus — it's fine for housekeeping, but for anything critical I'd look at a differential bus with better fault containment. If I²C stays, the firmware needs a bus-health state machine that tracks errors per node and degrades gracefully rather than hanging the whole system on one bad transaction.

**Possible follow-ups:** How would you detect which node is holding the bus low without being able to query it? What's the trade-off between bus segmentation and added failure points from the switches themselves?

## Q4: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** This is really three problems layered together: source redundancy, fault isolation, and inrush management. I'd start with the architecture — each 28V feed gets its own protection and ORing path so that a fault on one feed can't propagate to the other or to the common load rail. Ideal-diode or ORing controllers with reverse-current blocking are the usual choice; the key requirement is that a shorted feed must be disconnected before it drags the shared rail down, which means fast overcurrent detection and a disconnect element (eFuse or hot-swap controller) sized to the fault current, not just the operating current.

For latch-up on a load: the protection has to distinguish a transient inrush from a sustained overcurrent. That means a current-limit profile with a timed foldback or a retry strategy — allow a brief high-current window for capacitive loads, then latch off if the current doesn't fall. I'd also make the latch-off recoverable under command or by a supervised auto-retry, so a transient SEL doesn't permanently kill a load that would otherwise be fine.

For hot-swap: the inrush limiter has to keep the 28V bus disturbance within spec during insertion — controlled dV/dt on the pass element, and enough bulk capacitance on the load side to ride through the insertion transient without pulling the bus below its minimum. I'd verify all of this with a test plan that includes shorted-load, hot-swap, and simultaneous worst-case events, because the interactions between the three are where designs usually break.

**Possible follow-ups:** How would you set the retry policy so a persistent fault doesn't cause endless bus disturbance? What failure modes of the ORing controller itself would you need to protect against?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real analysis, so the review should engage with that analysis rather than dismiss the conclusion. I'd start by asking them to walk through their margin calculation and the assumptions behind it — often the disagreement isn't about the numbers but about what environment or worst case was assumed. Making the assumptions explicit turns a clash of opinions into a shared technical question.

Then I'd bring data to the table rather than authority. If I believe the design is under-margined, I should be able to point to a specific mechanism — a TID drift path, an SET that isn't covered, a worst-case corner that wasn't analyzed — and show the consequence. If I can't articulate that concretely, I need to reconsider whether my concern is real. Conversely, if the engineer can show their margin holds under the assumptions I care about, I should update.

Where we still disagree, I'd frame it as a risk decision rather than a correctness argument: what's the cost of the extra margin versus the cost of a failure in flight, and who owns that trade? I'd document the decision and the rationale either way, so it's traceable. And I'd keep the tone collaborative — the goal is the right design, not winning the review. A junior engineer who feels heard is far more likely to raise the next concern early, which is exactly what you want on a radiation-hardened program.

**Possible follow-ups:** What would you do if the engineer's analysis is correct but the schedule can't absorb the fix? How do you make sure a documented risk acceptance doesn't become a way to avoid hard decisions?