# space-rad-hard — Day 85

## Q1: How would you approach designing a radiation-tolerant power distribution scheme for a payload where several loads share a common upstream rail, and a single-event latch-up (SEL) in any one load must not collapse the rail for the others?

**Answer:** The core principle is to isolate the fault at the lowest possible level so that a latched load draws current only from its own branch, not from the shared source. I would start by segmenting the distribution: each load (or small group of loads with similar criticality and current profile) gets its own protection switch — a current-limited load switch or an eFuse — placed as close to the load as practical. That switch needs three behaviors: a current limit that trips before the upstream converter's own limit is reached, a latch-off or timed-retry response so a persistent SEL doesn't hold the rail in a brownout, and a fast enough response to keep the transient from sagging the common rail below the other loads' minimum operating voltage.

The sizing has to be done against the worst case, not the nominal. I'd budget the upstream converter's current headroom so that one branch at its current limit plus all other branches at their normal draw still stays within the converter's capability. Bulk capacitance on the common rail buys time for the protection to act, but it also stores energy that feeds the fault, so there's a trade-off between ride-through and fault energy — I'd size it for the hold-up the other loads actually need, not more.

I'd also think about the failure mode of the protection device itself. A single switch is a single point of failure; for high-criticality loads, a redundant feed path or a cross-strapped arrangement may be warranted. And I'd want telemetry on each branch — current sense and fault flags — so the system can report which load latched and take a recovery action rather than blindly power-cycling everything.

**Possible follow-ups:**
- How would you decide between latch-off and auto-retry for a given load, and what does that choice imply for the rest of the system?
- If the protection switch itself is a COTS part with no radiation data, how does that change your architecture?

## Q2: How would you approach selecting and qualifying a voltage reference for a precision ADC in a space application, given that most commercial references have no radiation data and the measurement must hold accuracy over a multi-year mission?

**Answer:** I'd treat this as a two-part problem: what the reference does under radiation, and what the system can tolerate if it drifts. On the part side, I'd first look for references with published TID and single-event data — either rad-hard by design or COTS parts that a lab has characterized. If none exists, the honest position is that the part is unqualified, and I'd either fund a characterization test or design around the uncertainty.

The design-around is where the real engineering is. A reference that drifts with TID is a slow, monotonic error, so if the system has an in-situ calibration path — a known-good secondary standard, a ratiometric measurement against a stable element, or a periodic recalibration against an on-board reference — the drift can be tracked rather than assumed away. But that only works if the drift is slow and the calibration is trustworthy. Single-event transients on the reference are a different problem: a momentary spike during a conversion corrupts that sample, and no amount of calibration fixes it. For that I'd look at filtering, conversion redundancy (take multiple samples and reject outliers), or a reference topology that's inherently less SET-sensitive.

I'd also be careful about the assumption that "precision" implies radiation tolerance. Initial accuracy and temperature drift say nothing about TID behavior, and ELDRS in particular can cause bipolar references to degrade at low dose rates in ways a high-dose-rate test won't reveal. So the qualification plan has to match the mission's actual dose rate, not just the total dose.

**Possible follow-ups:**
- How would you structure a calibration routine so that it can't itself be fooled by a radiation-induced error?
- What's the difference between testing a reference at high dose rate versus low dose rate, and why does it matter here?

## Q3: You're reviewing a design where a junior engineer has proposed using a single commercial LDO with no radiation data to post-regulate a critical analog rail, arguing that the upstream DC-DC is already rad-tolerant so "the LDO doesn't matter." How would you evaluate this argument?

**Answer:** The argument has a kernel of truth — the upstream converter sets the bulk of the regulation and the LDO only cleans up the residual — but it doesn't follow that the LDO is therefore safe. The LDO is in the signal path for the analog rail, so anything it does wrong shows up directly at the load. Three failure modes matter here.

First, TID: an uncharacterized LDO can shift its output voltage, its dropout, or its quiescent current as dose accumulates. A slow output shift on an analog rail is a measurement error that may or may not be calibratable. Second, single-event transients: an SET on the LDO's pass element or error amplifier can produce a momentary output excursion that the downstream ADC sees as a real signal. Third, SEL: a latch-up in the LDO can drag the rail down or, worse, present a low-impedance path that the upstream converter tries to feed.

So my response would be to separate the two claims. "The upstream is rad-tolerant" is about the upstream; it says nothing about the LDO's own behavior. I'd ask for the LDO's radiation data, and if there is none, I'd want either a characterized alternative, a characterization test, or a design that tolerates the LDO's failure modes — for example, a downstream filter that rejects SETs, or a redundant reference path that doesn't depend on the LDO's absolute accuracy. The point isn't to win the argument; it's to make the risk explicit and decide whether it's acceptable for this rail's criticality.

**Possible follow-ups:**
- If the LDO is the only part available and there's no budget to characterize it, what would you do?
- How would you decide whether a given analog rail is "critical enough" to justify the extra cost of a rad-tolerant regulator?

## Q4: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt (SEFI) that leaves the processor still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** The hard part here is that the failure mode is invisible to the obvious detectors. A watchdog that just looks for a heartbeat will be satisfied, and a current monitor will see normal draw. So the test plan has to exercise the recovery logic against a fault that mimics this specific signature, and it has to do so without a particle beam if one isn't available.

I'd start by defining what "still executing the control loop" actually means in observable terms — a counter that increments only when the loop completes, a checksum over the loop's output, a timestamp that advances. That gives a signal the recovery logic can actually key on, and it's also the signal the test needs to corrupt. Then I'd build a fault-injection harness: either a debugger that halts the core at a chosen point, a test hook in firmware that forces the loop into a stuck state while leaving the heartbeat running, or an external stimulus that corrupts the loop's state. The point is to reproduce the signature, not just "hang the processor."

The test then verifies three things: that the recovery mechanism detects the condition, that it takes the correct action (reset, reinitialize, switch to a redundant path), and that the system returns to a known-good state and resumes the control loop. I'd run it repeatedly, at different points in the loop, and with the heartbeat deliberately left running, to make sure the detector isn't accidentally relying on the heartbeat stopping. If a beam is available, I'd use it to confirm the injected fault is representative, but the ground test is what gives repeatable coverage.

**Possible follow-ups:**
- How would you design the recovery mechanism so it doesn't itself get stuck in the same state?
- What's the risk of a recovery action that's too aggressive, and how would you bound it?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing is to separate the person from the proposal. The engineer has done real work, and that work is valuable regardless of whether the conclusion holds — so I'd start by making sure they know I've read it and that the concern is about the margin, not about their effort. Then I'd try to convert the disagreement from a matter of opinion into a matter of shared criteria.

In practice that means asking questions rather than making assertions. What radiation environment is this designed against? What's the worst-case part behavior you assumed, and where did that number come from? What happens if the part is at the edge of its tolerance and the environment is at the edge of its spec? Often the gap isn't that the engineer is wrong about the nominal case — it's that the margin analysis stopped at nominal. Walking through the worst case together usually either reveals the gap or reveals that I was wrong about it, and both outcomes are fine.

If we still disagree after that, I'd want to make the decision explicit and documented: here's the risk, here's the mitigation, here's who owns the call. I'd also want to give the engineer a path to be right — if they can produce data or analysis that closes the gap, I'd rather change my mind than force a decision. The goal isn't to win the review; it's to make sure the board that ships is one we both understand the risks of.

**Possible follow-ups:**
- What would you do if the engineer's approach was already baked into a schedule commitment?
- How would you handle it if the disagreement were with a more senior engineer rather than a junior one?