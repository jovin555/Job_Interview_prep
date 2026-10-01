# space-rad-hard — Day 72

## Q1: How would you approach designing a radiation-tolerant analog signal chain for a spacecraft instrument where the sensor output is a low-level differential signal, and both the amplifier front-end and the ADC reference can experience single-event transients (SETs)?

**Answer:** The core problem is that a low-level differential signal has very little amplitude margin, so a transient anywhere in the chain — at the amplifier input, in the amplifier's internal bias network, or on the ADC reference — can produce an output that looks like a real measurement. I'd start by separating the two failure modes: transient (recoverable, short-duration) and permanent (TID-induced drift or latch-up). For SETs, the design goal is to make the transient either not reach the output or be detectable and discardable.

At the front end, I'd use a differential amplifier topology with good common-mode rejection, because a differential pair tends to reject common-mode transients that couple into both inputs equally. I'd add RC filtering as close to the amplifier inputs as the signal bandwidth allows — the corner frequency is a trade-off between noise rejection and signal fidelity, and for a low-level signal I'd want the filter to attenuate transients that are much faster than the signal of interest. I'd also consider whether the amplifier itself has any history of SET sensitivity; if not, I'd treat it as an unknown and design assuming it can glitch.

For the ADC reference, the key insight is that a transient on the reference corrupts the conversion result even if the input signal is clean. I'd use a reference with a large output capacitor and a low-pass filter to slow down any transient, and I'd consider a reference topology that is inherently less sensitive — for example, a buried Zener or a bandgap with internal filtering. If the reference is external, I'd add a series resistor and a capacitor to ground to form a filter, and I'd verify that the reference's transient response is fast enough to recover before the next conversion.

The most important part is the detection layer. I'd add a comparator or a window detector that flags when the signal exceeds a plausible range, and I'd use that flag to discard the sample rather than pass it to the control loop. If the measurement is time-sensitive and can't be retried, I'd use a redundant measurement path — two independent ADCs or two independent signal chains — and compare them; if they disagree beyond a threshold, the system knows something is wrong. This is essentially a voting scheme at the analog level, and it's more robust than trying to make a single chain immune.

**Possible follow-ups:**
- How would you decide the threshold for the window detector without knowing the exact SET cross-section of the amplifier?
- If the two redundant chains disagree, how would you decide which one to trust, or would you discard both?

## Q2: You're reviewing a design for a space-deployed system that uses a COTS linear regulator to generate a 1.2V core voltage for an FPGA. The regulator's datasheet shows no radiation data, and the output voltage is specified as 1.2V ±2%. The FPGA requires 1.2V ±5% and draws up to 3A. How would you evaluate this choice and what alternatives would you recommend?

**Answer:** The first thing I'd note is that the electrical margin looks fine on paper — ±2% output versus ±5% requirement leaves 3% of headroom — but that margin is only valid at beginning of life and at room temperature. The real question is what happens under radiation. A COTS linear regulator with no radiation data has three unknowns: TID-induced drift in the reference and error amplifier, SETs on the pass transistor or control loop, and SEL susceptibility. Any of these can push the output outside the FPGA's tolerance or cause a transient that the FPGA sees as a brownout or overvoltage.

For TID, the concern is that the regulator's internal reference can drift with dose, and the output voltage can shift monotonically over the mission. If the regulator drifts by even 2–3%, the margin is gone. For SETs, a transient on the output can cause the FPGA to lose configuration or enter an undefined state, and a 3A load means the regulator's transient response is not trivial — the output can dip or spike before the loop recovers. For SEL, a latch-up in the regulator can drag the rail down or cause a short, and if the regulator doesn't have current limiting or thermal shutdown that works in the space environment, it can destroy itself.

My recommendation would be to either use a radiation-characterized regulator — one with TID data and SEL immunity — or to add a post-regulator that is rad-hard and can absorb the COTS regulator's drift. If neither is available, I'd consider a discrete linear regulator built from rad-hard components: a rad-hard op-amp, a rad-hard pass transistor, and a rad-hard reference. That gives you control over the topology and the ability to derate and qualify each part. I'd also add a voltage supervisor that monitors the 1.2V rail and holds the FPGA in reset if the rail goes out of tolerance, and I'd add a crowbar or clamp to protect against overvoltage transients.

The other option is to change the architecture: if the FPGA can tolerate a wider input range, or if you can use a rad-hard switching regulator followed by a rad-hard LDO, you can move the problem to a part that has radiation data. The key is not to accept "no radiation data" as a reason to skip the analysis — it's a reason to either test the part or design around it.

**Possible follow-ups:**
- How would you test a COTS regulator for SET sensitivity if you had limited beam time?
- If you use a discrete rad-hard regulator, how would you handle the loop stability and transient response at 3A?

## Q3: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a deceptively fragile bus in a radiation environment because it's open-drain, has no inherent error detection beyond the ACK bit, and a single node that holds SDA or SCL low can lock the entire bus. The first design decision is whether I²C is the right choice at all — if the bus is critical, I'd consider a differential bus like RS485 or CAN-FD, which have better noise immunity and built-in error detection. But if I²C is required, I'd approach it at three levels: protocol, electrical, and recovery.

At the protocol level, I'd add a checksum or CRC to every message, because the ACK bit only tells you that a device responded, not that the data is correct. I'd also add a sequence number or a transaction ID so that a corrupted message can be detected as out of order. For critical data, I'd use a request-response pattern with a read-back: write the value, read it back, and compare. If the read-back doesn't match, retry a bounded number of times and then flag the node as failed.

At the electrical level, I'd add series resistors on SDA and SCL to limit the current during a fault, and I'd consider a bus isolator or a multiplexer that can disconnect a faulty node from the bus. If a node latches up and holds the bus low, the isolator can isolate it and let the rest of the bus continue. I'd also add pull-up resistors that are sized for the bus capacitance and the radiation environment — a pull-up that drifts with TID can change the rise time and cause timing violations.

The most important part is recovery. I²C has a well-known recovery procedure: if the bus is stuck, the master can send a series of clock pulses (typically 9) to free a slave that is holding SDA low. I'd implement that in firmware as a recovery routine, and I'd add a bus monitor that detects when the bus is stuck for longer than a threshold and triggers the recovery. If the recovery fails, the master can power-cycle the offending node via a load switch. I'd also add a watchdog on each node so that a node that is stuck in a bad state resets itself.

Finally, I'd consider redundancy: if the bus is critical, I'd use two independent I²C buses with the sensors duplicated on both, and the master would cross-check the two. That way, a single bus fault doesn't lose the measurement.

**Possible follow-ups:**
- How would you detect which node is holding the bus low without being able to query the nodes?
- If you use a bus isolator, how do you handle the case where the isolator itself is hit by an SET?

## Q4: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt (SEFI) that puts the main processor into a state where it's still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** This is a classic "silent hang" scenario, and it's one of the hardest to test because the processor looks alive to a simple watchdog. The first step is to define what "recovery" means: the processor must return to executing the control loop, the control loop must resume with correct state, and the system must not have lost any critical data or produced a dangerous output during the hang. The test plan has to verify all three.

Since you can't inject actual radiation during ground testing, you need to simulate the SEFI. The most direct way is to use a debugger or a test harness that can halt the processor's control loop while leaving the heartbeat toggling. On an ARM Cortex-M, for example, you can set a breakpoint in the control loop and let the heartbeat interrupt continue — that reproduces the "alive but not controlling" state. Alternatively, you can add a test mode in firmware that deliberately stops the control loop but keeps the heartbeat running, and trigger it via a command.

The test then verifies that the recovery mechanism detects the hang and recovers. The key is that the recovery mechanism must not rely on the heartbeat alone. I'd use a multi-level watchdog: a hardware watchdog that the control loop must kick, not the heartbeat; a software watchdog that monitors the control loop's progress through a state machine; and a "liveness" check that verifies the control loop is producing outputs within expected bounds. If any of these fail, the system resets the processor or switches to a redundant processor.

The test plan would cover: (1) the hang is detected within the specified time; (2) the reset or switchover occurs; (3) the control loop resumes with correct state — this is where you need to verify that the state was saved in non-volatile or redundant memory before the hang; (4) the system does not produce a dangerous output during the hang or the recovery; and (5) the recovery works repeatedly, not just once. I'd also test the case where the hang occurs during a critical operation, such as a write to an actuator, to make sure the recovery doesn't leave the actuator in an unsafe state.

Finally, I'd test the recovery under different conditions: at different points in the control loop, with different sensor inputs, and with the bus in different states. The goal is to build confidence that the recovery is robust, not just that it works in one scenario.

**Possible follow-ups:**
- How would you verify that the control loop state was correctly saved before the hang, if the hang itself could corrupt the state?
- If the processor is in a state where it's still toggling the heartbeat but not executing the control loop, how do you distinguish that from a processor that is executing the control loop but with a stuck sensor input?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves respect — the goal is not to win the argument but to make sure the design is right. I'd start by asking questions rather than making statements: "Walk me through how you arrived at this margin," "What radiation data did you use for this part," "What happens if the part drifts by X over the mission?" That does two things: it shows I'm taking the work seriously, and it often surfaces the gap in the analysis without me having to point it out.

If the gap is real — for example, the engineer used a COTS part with no radiation data and assumed the margin is sufficient — I'd focus on the consequence, not the criticism. I'd say something like: "The concern I have is that this part has no TID data, so we don't know how much the output will drift over the mission. If it drifts by more than the margin, the FPGA could see an out-of-tolerance rail. How would we detect that, and what's the fallback?" That frames it as a shared problem to solve, not a judgment on the engineer's work.

If the engineer pushes back — which is fair, they've done the work — I'd suggest a concrete way to resolve it: "Let's get the radiation data, or if it's not available, let's add a test or a mitigation that covers the risk. If the mitigation is too expensive, let's look at alternatives together." I'd also be open to being wrong: if the engineer has data I don't have, or if there's a system-level reason the margin is acceptable, I'd want to hear it. The goal is the right decision, not my decision.

If the disagreement persists and the risk is significant, I'd escalate it — not as a conflict, but as a request for a second opinion or a risk assessment. I'd document the concern and the proposed mitigation, and I'd make sure the decision is made with full information. The worst outcome is not a disagreement; it's a design that ships with an unaddressed risk because no one wanted to push back.

**Possible follow-ups:**
- How would you handle it if the engineer's proposal is actually correct and your concern was based on a misunderstanding?
- If the engineer is junior and the disagreement is public in the review, how do you correct the record without undermining them?