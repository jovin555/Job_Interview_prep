# space-rad-hard — Day 78

## Q1: How would you approach designing a radiation-tolerant analog signal chain for a spacecraft instrument where the sensor output is a low-level differential signal, and both the amplifier front-end and the ADC reference can experience single-event transients (SETs)?

**Answer:** The core problem is that a low-level differential signal has very little amplitude headroom, so any transient that couples into the front-end or shifts the reference will corrupt the measurement in a way that's hard to distinguish from real signal. I'd approach it in layers.

First, at the topology level: keep the front-end fully differential from sensor to ADC, because a differential path rejects common-mode transients that couple equally into both legs. Choose an instrumentation amplifier or a differential amplifier with good CMRR and, critically, one whose input bias network doesn't create a high-impedance node that a transient can charge up. If the sensor is truly low-level, the first stage sets the noise floor, so I'd want the gain as early as possible — but not so early that a transient gets amplified into saturation and takes time to recover.

Second, for the reference: a single reference IC is a single point of failure for SETs. I'd consider either a filtered reference (RC plus a low-leakage, radiation-tolerant capacitor close to the ADC) to slow down and attenuate fast transients, or a ratiometric approach where the ADC measures against the same reference that drives the sensor excitation, so a reference transient affects both and partially cancels. Where accuracy demands it, I'd look at a reference with known SET behavior, or average multiple conversions and reject outliers.

Third, at the conversion level: oversample and use a median or trimmed-mean filter rather than a simple average, so a single corrupted sample doesn't drag the result. If the measurement is time-sensitive and can't be retried, I'd add a plausibility check — rate-of-change limits, comparison against a redundant or slower secondary channel — and flag or hold the last good value rather than acting on a spike.

Finally, layout and grounding: keep the analog return separate from digital, guard the sensitive nodes, and place the anti-alias filter as close to the ADC input as possible so transients have less opportunity to couple in. The overall principle is defense in depth — no single mitigation is sufficient, but rejection, filtering, redundancy, and plausibility checking together make the chain robust.

**Possible follow-ups:**
- How would you distinguish a genuine fast sensor event from an SET-induced spike if both look like a sudden step?
- If the reference and the sensor excitation share a node, what new failure modes does that introduce?

## Q2: You're reviewing a design for a space-deployed system that uses a COTS linear regulator to generate a 1.2V core voltage for an FPGA. The regulator's datasheet shows no radiation data, and the output voltage is specified as 1.2V ±2%. The FPGA requires 1.2V ±5% and draws up to 3A. How would you evaluate this choice and what alternatives would you recommend?

**Answer:** The first thing I'd note is that the ±2% initial tolerance is not the real problem — the real problem is that with no radiation data, I have no idea how the reference, error amplifier, and pass element behave under TID or whether the part is susceptible to SETs or SEL. So the ±2% spec tells me nothing about the parameter that actually matters.

I'd evaluate it in three steps. First, TID: over a multi-year mission the regulator's internal reference and feedback network can drift, and without data I can't bound that drift. If the FPGA's ±5% window is the only margin, and the regulator starts at ±2%, I've effectively got ±3% left for TID drift, aging, load regulation, and transient response — that's thin, and I can't prove it holds. Second, SEE: a linear regulator with a bipolar or CMOS pass element can latch up, and a 3A core rail latching up is a serious event — it can drag the rail down, trip the upstream converter, or damage the FPGA. Third, SETs: a transient on the output during a heavy-ion strike could momentarily exceed the FPGA's absolute maximum and stress the core.

For alternatives, I'd look at: (a) a radiation-tolerant or radiation-hardened regulator with published TID and SEE data, even at higher cost; (b) if a COTS part is unavoidable, add a radiation-tolerant LDO or a clamp downstream to bound the output, plus a current-limit and latch-up protection scheme on the rail; (c) consider a switching regulator with a rad-hard controller if efficiency matters, since linear at 3A from a higher rail dissipates a lot of heat in vacuum; and (d) if the FPGA has an internal core regulator or can accept a wider tolerance, use that to relax the external requirement.

The key point I'd make in review: "no radiation data" is not the same as "radiation-tolerant," and for a 3A core rail feeding an FPGA, I need either data or a mitigation that bounds the failure.

**Possible follow-ups:**
- How would you design a latch-up protection scheme for a 3A core rail without adding so much series resistance that you violate the FPGA's droop requirements?
- If you had to qualify this COTS regulator with limited budget, what would your test plan look like?

## Q3: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a deceptively fragile bus in a radiation environment because it's open-drain, has no built-in error detection beyond the ACK bit, and a single node that gets stuck holding SDA or SCL low can hang the entire bus. So I'd treat fault tolerance at three levels: protocol, electrical, and recovery.

At the protocol level, I'd add a checksum or CRC to every message, because the ACK bit alone won't catch a corrupted payload. I'd also include a sequence number or transaction ID so a node can detect a duplicated or out-of-order message, and I'd design commands to be idempotent where possible so a retry after a corrupted transfer doesn't cause a double action. For critical data, I'd consider a request/response with a readback verification rather than a fire-and-forget write.

At the electrical level, I'd make sure the bus has proper pull-ups sized for the capacitance and speed, and I'd consider a bus buffer or multiplexer that can isolate a faulty segment. If a single node can drag the bus down, a segmented bus with a switchable buffer lets the controller isolate that node and keep the rest of the system running. I'd also add series resistors or current limiting on each node's bus pins to reduce the chance that a latched node takes the whole bus with it.

At the recovery level, the controller needs a way to detect a stuck bus and recover it. A common technique is a bus recovery routine: the controller clocks SCL manually (as a GPIO) for up to nine pulses to flush any node that's mid-byte, then issues a STOP condition. If that fails, the controller can power-cycle the offending node via a load switch or a dedicated reset line. I'd also add a timeout on every transaction so the firmware never blocks indefinitely waiting for an ACK.

Finally, I'd consider whether I²C is the right choice at all. If the bus is critical and the environment is harsh, a differential bus like RS485 or CAN-FD with built-in CRC and fault confinement may be more appropriate, even at higher pin and power cost. The trade-off is complexity versus robustness, and for a multi-node critical system I'd lean toward the more robust option.

**Possible follow-ups:**
- How would you implement bus recovery in firmware without a dedicated I²C recovery peripheral?
- If you segment the bus with a multiplexer, how do you handle the case where the multiplexer itself is hit by an SET?

## Q4: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt (SEFI) that puts the main processor into a state where it's still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** This is the hardest class of SEFI to test because the processor looks alive — it's drawing current, the heartbeat is toggling — but the control loop is dead. A naive watchdog that just checks for a heartbeat will never fire, so the test plan has to verify that the recovery mechanism catches this specific failure mode, not just a full hang.

I'd start by defining what "recovery" means: the control loop resumes within a bounded time, the outputs go to a safe state during the interruption, and the system logs the event. Then I'd build a way to inject the fault on the ground, since I can't rely on actual radiation during bench testing.

For injection, I'd use one of a few techniques. The cleanest is a debugger or on-chip debug unit that halts the control loop task while leaving the heartbeat task running — this exactly reproduces the "alive but not controlling" state. If the processor supports it, I'd use a fault injection framework that corrupts the program counter or a critical variable to send the loop into an invalid state. On hardware without debug access, I could use a GPIO-driven test mode in firmware that deliberately stalls the control loop while keeping the heartbeat alive.

The recovery mechanism itself needs to be more than a heartbeat check. I'd design a "control loop liveness" check: the control loop must update a counter or a sequence number that the supervisor monitors, and if the counter stops advancing within a window, the supervisor triggers a reset. The heartbeat can be a separate, slower signal that confirms the supervisor itself is alive. This way, a SEFI that kills the loop but not the heartbeat is caught by the liveness check, and a SEFI that kills the supervisor is caught by the heartbeat check.

The test plan would then: (1) inject the fault, (2) verify the liveness check fires within the specified window, (3) verify the reset brings the system back to a known state, (4) verify the outputs were safe during the interruption, and (5) verify the event was logged. I'd repeat this across temperature, voltage, and clock corners, and I'd run it many times to catch marginal timing. I'd also test the case where the fault occurs during the reset sequence itself, to make sure the recovery doesn't get stuck.

**Possible follow-ups:**
- How would you set the liveness check window so it's tight enough to catch a real SEFI but loose enough not to false-trigger on normal jitter?
- What would you do if the processor's debug unit is itself affected by the fault injection?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves respect — if I come in with "this is wrong," I lose the room and I might miss something they've thought of that I haven't. So I'd start by asking them to walk me through their reasoning: what environment they assumed, what data they used, what margin they calculated, and what failure modes they considered. Often the gap is an unstated assumption rather than a calculation error, and surfacing it together is more productive than me asserting it.

Then I'd make the risk concrete rather than abstract. "Under-margined for the radiation environment" is easy to dismiss; a specific failure mode with a specific consequence is not. I'd say something like: "Walk me through what happens if this part sees a 50 krad dose and its reference drifts 3% — where does that show up in the system, and what's the consequence?" If the engineer can answer that and show the system tolerates it, maybe I'm wrong and I should update. If they can't, the gap becomes visible to everyone in the room, not just me.

I'd also bring the decision criteria into the open. In a design review, the question isn't "who's right" — it's "what does the program need, and what's the evidence?" If the program has a radiation requirement, a derating guideline, or a heritage part list, I'd anchor the discussion to those rather than to my opinion. That depersonalizes it: we're both trying to meet the same requirement, and the question is whether this proposal meets it.

If we still disagree after that, I'd propose a path forward rather than dig in. Options might be: get the missing data (a radiation test, a vendor query, a heritage reference), add a mitigation that bounds the risk, or escalate to a broader review with the program's radiation SME. I'd frame it as "let's resolve this with evidence" rather than "I'm overruling you." And I'd follow up privately afterward to make sure the engineer doesn't feel singled out — design reviews are stressful, and a junior engineer who feels attacked will stop bringing proposals forward, which is the opposite of what I want.

The meta-point: the goal of the review is the right decision, not my decision. If I keep that frame, the disagreement stays technical and the team stays intact.

**Possible follow-ups:**
- What would you do if the engineer's proposal had already been built into a prototype and changing it would cost schedule?
- How would you handle it if the program manager sided with the engineer for cost reasons?