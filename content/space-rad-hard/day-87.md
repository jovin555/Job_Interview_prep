# space-rad-hard — Day 87

## Q1: How would you approach designing a radiation-tolerant analog-to-digital conversion subsystem where the ADC's voltage reference is a COTS part with no radiation data, and the measurement must hold accuracy over a multi-year mission?

**Answer:** The core problem is that a voltage reference sets the absolute accuracy of every conversion, so any drift in the reference — from total ionizing dose, enhanced low-dose-rate sensitivity (ELDRS), or temperature — shows up directly as measurement error that no amount of downstream digital processing can recover. With no radiation data on the part, I would treat the reference as an unquantified risk and work the problem from three directions.

First, quantify the risk rather than assume it away. I would look for any published single-event or TID data on the die or a comparable process, check whether the manufacturer has a rad-tolerant variant of the same reference, and if budget allows, run a screening test — at minimum a TID step-stress at low dose rate to expose ELDRS, since bipolar references are especially prone to it. If testing isn't possible, I would bound the error with a conservative assumption and design the rest of the chain to tolerate it.

Second, reduce the reference's influence on the measurement. A ratiometric architecture, where the ADC and the sensor excitation share the same reference, cancels first-order reference drift because the reference appears in both the numerator and denominator. Where that isn't possible, I would use a reference with low initial tolerance and low temperature coefficient and add a periodic in-system calibration against a stable, radiation-characterized secondary standard — for example, a bandgap or buried-Zener reference with known TID behavior — so slow drift is corrected over the mission.

Third, add redundancy and monitoring. Two independent references of different technologies, cross-checked against each other, let the system flag disagreement and fall back to the more trustworthy one. A reference that drifts slowly is detectable; a reference that fails suddenly is not, so I would also add a sanity check on the reference voltage itself through a known divider into a spare ADC channel.

The trade-off is cost, board area, and calibration complexity versus guaranteed accuracy. For a multi-year mission I would rather spend the mass and power on a characterized reference or a ratiometric topology than gamble on an unquantified COTS part.

**Possible follow-ups:**
- How would you distinguish reference drift from ADC drift if both are uncharacterized?
- What calibration cadence would you choose, and how would you verify the calibration standard itself hasn't drifted?

## Q2: You're reviewing a design where a junior engineer has proposed using a single commercial LDO with no radiation data to post-regulate a critical analog rail, arguing that the upstream DC-DC is already rad-tolerant so "the LDO doesn't matter." How would you evaluate this argument?

**Answer:** The argument has a real kernel of truth — a clean upstream rail does reduce the LDO's burden — but it conflates two different failure modes. The upstream DC-DC being rad-tolerant says nothing about whether the LDO itself will survive TID, latch up, or pass a single-event transient through to the analog load. The LDO is a series pass element in the signal path; if it latches or its pass transistor degrades, the analog rail is gone regardless of how good the DC-DC is.

I would evaluate it on three axes. First, TID and ELDRS: an uncharacterized LDO may drift its output voltage or reference over dose, and for a critical analog rail even tens of millivolts of drift can corrupt a precision measurement. Second, single-event effects: a SET on the LDO's error amplifier can couple directly onto the analog rail, and an SEL can drag the rail down or destroy the part. Third, the LDO's own PSRR and noise — the reason it's there — may itself degrade with dose, so the filtering you're relying on may not hold late in the mission.

My recommendation would be to either select a rad-tolerant or radiation-characterized LDO, or, if the rail is truly non-critical, document the acceptance of the risk explicitly with a rationale and a monitoring plan. What I would not accept is "the upstream is fine, so this doesn't matter" as the justification, because it doesn't address the LDO's own failure modes. I'd frame it to the engineer as: the upstream converter protects the LDO from input disturbances, but it can't protect the LDO from itself.

**Possible follow-ups:**
- If the rail is genuinely non-critical, what would a defensible risk-acceptance argument look like?
- How would you test an uncharacterized LDO to decide whether it's acceptable?

## Q3: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the same bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is attractive for sensor fan-out because it's simple and low-pin-count, but it's fragile in a radiation environment for two reasons: a single SEU on the clock or data line can be interpreted as a valid start/stop condition, and a slave that gets stuck holding SDA low can lock the entire bus. So the design has to assume both data corruption and bus-level lock-up.

For data corruption, I would add integrity at the protocol layer: a CRC or checksum on every transaction, sequence numbers so a repeated or dropped message is detectable, and a defined retry policy with bounded attempts. A corrupted read that fails CRC is simply retried; a corrupted write is more dangerous, so writes to actuators or configuration registers should be read-back-verified.

For bus lock-up, the standard recovery is clock stretching or a manual bus-clear: if SDA is held low with SCL idle, the master toggles SCL up to nine times to flush the stuck slave, then issues a stop condition. I would implement that in firmware as an automatic recovery routine triggered by a bus-idle timeout, not rely on a human to notice. A hardware watchdog on the bus master, or a bus switch that can isolate a misbehaving segment, adds another layer.

Architecturally, I would consider segmenting the bus — a separate I²C segment per criticality group, or a mux that lets the master isolate a faulty node — so one stuck slave can't take down sensors that feed a control loop. And I would make sure the pull-up resistors and bus capacitance are derated for the environment, since a marginal bus is more likely to be pushed over the edge by a transient.

The trade-off is complexity and pin count versus robustness. For a life-support or control-loop measurement, the extra mux and recovery logic is worth it; for housekeeping telemetry, CRC plus retry may be enough.

**Possible follow-ups:**
- How would you decide which nodes get their own bus segment versus sharing one?
- What's the risk of the bus-clear routine itself being interrupted by another SEU mid-recovery?

## Q4: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt (SEFI) that leaves the processor still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** This is the hardest class of SEFI to test because the obvious health signals — current draw and a heartbeat — both look normal. The processor is alive enough to toggle a GPIO but has lost the thread of its actual work. A naive watchdog that only checks the heartbeat will never fire, so the test plan has to verify that the recovery mechanism detects loss of *function*, not just loss of *liveness*.

I would structure the test around fault injection rather than waiting for real radiation. On the bench, I can inject the failure in several ways: halt the control task while leaving a low-priority heartbeat task running, corrupt the control loop's state variable so it computes garbage but keeps running, or use a debugger to freeze the core at a specific point. Each injection targets a different flavor of "alive but not working."

The recovery mechanism itself needs to be functional, not just temporal. A heartbeat alone is insufficient; I would add a functional check — for example, the control loop must update a sequence counter or a computed output that a supervisor task verifies is changing within expected bounds. If the counter stops advancing or the output goes out of range, the supervisor triggers a reset. The test then verifies that this functional watchdog fires within the specified time and that the system returns to a known-good state.

I would also test the recovery path's own robustness: after the reset, does the system re-initialize cleanly, re-establish its state, and resume control without a transient that could harm the actuator? And I would test repeated injections to make sure the recovery doesn't degrade — for example, a counter that overflows after N recoveries.

Since real radiation can't be injected on the ground, I would document the injection methods and the coverage they provide, and be explicit about what remains unverified — for example, whether the functional watchdog itself is susceptible to the same SEFI.

**Possible follow-ups:**
- How would you set the functional watchdog's timeout without false-triggering on normal jitter?
- What would you do if the functional check itself is corrupted by the same event?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves respect — the goal is to get to the right answer, not to win the argument. I'd start by asking them to walk me through their reasoning and the assumptions behind it, because either they've accounted for something I haven't, or there's a gap I can point to concretely.

Then I'd try to make the disagreement about evidence rather than opinion. If the concern is margin, I'd ask: what's the worst-case number, where does it come from, and what's the consequence if it's exceeded? Often the fastest path is to put the numbers on the board together — the part's absolute maximum, the supply's worst-case output, the derating guideline — and let the gap speak for itself. If the engineer's analysis holds up, I should be willing to change my mind; that's the point of the review.

If the gap is real and the engineer still pushes back, I'd shift from "you're wrong" to "here's the risk we'd be accepting, and here's who owns it." I'd document the concern, the proposed mitigation, and the residual risk, and escalate the decision if it's above my authority. That keeps it constructive — the engineer isn't being overruled arbitrarily, they're being asked to accept a documented risk or find a way to close it.

Throughout, I'd keep the tone collaborative: "help me understand," "what would change your mind," "what's the cheapest way to close this gap." A design review that turns adversarial loses the engineer's future honesty, which is far more costly than any single margin call.

**Possible follow-ups:**
- What would you do if the engineer's proposal is technically defensible but you still believe the risk is unacceptable?
- How would you follow up after the review to make sure the relationship and the decision both hold up?