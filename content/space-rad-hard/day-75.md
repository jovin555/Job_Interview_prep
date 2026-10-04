# space-rad-hard — Day 75

## Q1: How would you approach designing a radiation-tolerant analog signal chain for a spacecraft instrument where the sensor output is a low-level differential signal, and both the amplifier front-end and the ADC reference can experience single-event transients (SETs)?

**Answer:** The core problem is that a low-level differential signal has very little amplitude margin, so a transient anywhere in the chain — at the amplifier input, in the amplifier's internal bias network, or on the ADC reference — can produce a reading that looks like a real measurement rather than obvious garbage. I'd approach it in layers.

First, at the topology level: keep the front-end fully differential from sensor to ADC, because a differential path gives common-mode rejection that attenuates a transient coupled equally onto both legs, and it lets me use matched, symmetric components so a single-event transient in one device doesn't create a large differential error. I'd choose an instrumentation amplifier or a differential amplifier with good CMRR and, where possible, a radiation-characterized part; if only COTS parts are available, I'd treat the lack of data as a risk item and plan for characterization or mitigation rather than assuming it's fine.

Second, at the reference: the ADC reference is often the single most dangerous node, because a transient there scales every code. I'd consider a reference with a large output capacitor and a low-pass filter at the reference pin to slow and attenuate fast transients, and I'd look at whether the reference can be made redundant or at least monitored. If the reference drifts or spikes, the system needs a way to detect it — for example, by periodically converting a known internal reference or a ratiometric check.

Third, at the conversion and validation level: I'd use oversampling and averaging where the signal bandwidth allows, since a transient that affects only one sample gets diluted. I'd add plausibility checks in firmware — rate-of-change limits, comparison against a redundant or secondary channel, and a "measurement valid" flag that suppresses control actions when the reading is suspect. For a control loop, I'd rather hold the last known-good value or go to a safe state than act on a transient-corrupted reading.

Finally, at the physical level: guard the analog front-end from digital switching noise with separate analog/digital ground returns, careful partitioning, and filtering on supply pins, because SETs and switching noise both degrade the same low-level signal and you can't always tell them apart after the fact.

**Possible follow-ups:**
- How would you decide whether a transient reading should be rejected outright versus filtered and used?
- If the reference itself is the most SET-sensitive node, how would you detect a reference transient that lasts longer than one conversion?

## Q2: You're reviewing a design for a space-deployed system that uses a COTS linear regulator to generate a 1.2V core voltage for an FPGA. The regulator's datasheet shows no radiation data, and the output voltage is specified as 1.2V ±2%. The FPGA requires 1.2V ±5% and draws up to 3A. How would you evaluate this choice and what alternatives would you recommend?

**Answer:** I'd separate the two concerns: static accuracy and radiation behavior. On static accuracy, the numbers look superficially fine — ±2% on 1.2V is ±24 mV, and the FPGA tolerance is ±5%, or ±60 mV, so there's roughly 36 mV of DC margin. But that margin is not the whole story. I'd want to know the regulator's tolerance over temperature, line and load regulation, and transient response at 3A, because a fast load step on an FPGA core rail can produce a transient that exceeds the DC window even if the steady-state number passes. I'd also check the dropout and thermal margins, since a linear regulator dropping from a higher rail at 3A dissipates significant power and its accuracy spec may not hold at temperature extremes.

On radiation, the absence of data is the real problem. A linear regulator has a bandgap reference, an error amplifier, and a pass element — all of which can shift under total ionizing dose, and the pass element and control loop can be susceptible to single-event transients and, depending on topology, single-event latch-up. Without data, I can't claim the rail stays within ±5% over the mission, and I can't claim the part won't latch up. A regulator that drifts out of tolerance can take the FPGA outside its operating range and cause functional failures that look like logic errors.

My recommendation would be: first, see whether a radiation-characterized or radiation-tolerant regulator exists for this rail, even at higher cost or lower efficiency. If a COTS part must be used, I'd want radiation test data — at minimum TID and heavy-ion/SET screening — or a documented, defensible rationale for why the risk is acceptable, plus mitigation. Mitigation could include a redundant or monitored rail, a voltage supervisor that resets the FPGA if the rail leaves tolerance, and current limiting or latch-up protection on the regulator output. I would not sign off on "no data, but the DC numbers pass" for a core rail that the whole design depends on.

**Possible follow-ups:**
- If radiation testing isn't feasible within budget, what would you do instead?
- How would a voltage supervisor on the 1.2V rail interact with the FPGA's own power-on reset requirements?

## Q3: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is convenient but fragile in a radiation environment because it's a shared, open-drain bus with a simple protocol and no built-in error detection beyond the ACK bit. Two failure modes dominate: data corruption (an SEU flips a bit in a message or in a node's state machine) and bus lock-up (a node holds SDA or SCL low, or a glitch leaves the bus in an invalid state, and no further traffic can proceed).

For data integrity, I'd add a checksum or CRC to every message payload, since the single ACK bit is not enough to catch multi-bit corruption. I'd also add sequence numbers or a transaction ID so a node can detect a repeated or out-of-order message. Where the sensor supports it, I'd read back configuration registers after writing them, and I'd use a defined "read twice and compare" pattern for critical values.

For lock-up recovery, I'd design the bus master to detect a stuck bus — for example, by timing out on SCL and then issuing a recovery sequence of clock pulses to free a slave that's holding SDA low, followed by a STOP condition. If that fails, the master should be able to power-cycle or reset individual sensor nodes, which means each node needs an independently controllable reset or power switch rather than sharing one. I'd also consider bus isolation: segmenting the bus with a mux or buffer so a fault on one segment doesn't take down the whole bus, and so the master can isolate a misbehaving node.

At the system level, I'd make the master's I²C driver defensive: bounded retries, a watchdog on each transaction, and a fallback to a safe state if a critical sensor can't be read. And I'd think about whether I²C is the right choice at all for a critical, multi-node, radiation-exposed bus — a differential bus like RS485 or CAN-FD with built-in CRC and fault confinement may be more robust, at the cost of more pins and complexity.

**Possible follow-ups:**
- How would you implement per-node reset without adding a lot of GPIO or a separate reset controller?
- What's the trade-off between adding bus segmentation and adding protocol-level error detection?

## Q4: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt (SEFI) that puts the main processor into a state where it's still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** This is the hard case for watchdogs, because the usual "is the heartbeat toggling?" check passes even though the processor is functionally dead. The test plan has to prove that the recovery mechanism catches a processor that is alive enough to toggle a pin but not alive enough to run the control loop.

First, I'd define what "recovery" means concretely: the control loop resumes within a bounded time, outputs return to valid values, and any state that was in flight is either completed or safely discarded. Then I'd design fault injection that reproduces the SEFI condition without radiation. Options include: halting the control loop task while leaving a low-priority task or interrupt to toggle the heartbeat; corrupting the control loop's state or program counter via a debugger; or using a test hook in firmware that deliberately stops servicing the loop while keeping the heartbeat alive.

The key design point is that the watchdog must be fed by the control loop itself, not by a separate timer or low-priority task. If the heartbeat is generated by the same code path that runs the control loop, then a SEFI that halts the loop also stops the heartbeat, and a simple watchdog works. If the heartbeat is independent, then the watchdog alone is insufficient and I need a second mechanism — for example, a "loop completion" counter that the watchdog checks, or a windowed watchdog that requires the heartbeat within a specific time window and with a specific pattern, so a stuck-but-toggling processor fails the pattern check.

The test plan would then verify: (1) the watchdog fires when the loop stops but the heartbeat continues; (2) the reset or recovery action brings the system back to a known-good state; (3) the recovery time is within the system's tolerance; (4) repeated injections don't leave the system in a degraded state; and (5) the recovery mechanism itself is not defeated by a corrupted state that persists across reset (e.g., a bad value in non-volatile memory). I'd also test the boundary cases — heartbeat toggling too fast, too slow, or with the wrong pattern — to confirm the windowed logic behaves as intended.

**Possible follow-ups:**
- How would you test the case where the processor is stuck in an interrupt handler that still services the heartbeat?
- What would you do if the recovery mechanism itself is susceptible to the same SEFI?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves acknowledgment before any critique — otherwise the review becomes adversarial and I lose the chance to actually change the design. I'd start by asking them to walk me through their reasoning and the assumptions behind it, because either they've considered something I haven't, or the gap will become visible in the walkthrough without me having to assert it.

Then I'd focus the discussion on the specific margin or failure mode I'm worried about, and frame it as a question rather than a verdict: "What happens to this rail if the part drifts by X over the mission?" or "What's the failure mode if this node latches up?" If the engineer has an answer, we test it together. If they don't, the gap is now a shared problem rather than my objection.

I'd bring evidence where I can — radiation data, derating guidelines, a similar failure mode from a previous program, or a quick calculation — because "I've seen this before" is weaker than "here's the number." If the data doesn't exist, I'd propose getting it: a test, a vendor query, or a documented risk acceptance with the right stakeholders. That turns the disagreement into a decision about how much evidence we need, which is easier to resolve than a clash of opinions.

If we still disagree after that, I'd make the call as the lead, but I'd do it transparently: state the decision, the reasoning, and what would change my mind. I'd also make sure the engineer's concern is recorded, because if I'm wrong, I want the record to show they raised it. And I'd follow up afterward to make sure the relationship isn't damaged — a design review is a recurring event, and I need this engineer to keep bringing me their real analysis, not just the answers they think I want.

**Possible follow-ups:**
- What would you do if the engineer's proposal was actually correct and your concern was based on an outdated assumption?
- How would you handle it if the same engineer repeatedly proposed under-margined designs?