# space-rad-hard — Day 79

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd treat this as three separable problems — source selection, fault isolation, and inrush management — and make sure the architecture keeps them from interacting badly.

For source selection, the two 28V feeds should be ORed rather than simply tied together. Ideal-diode or ORing-FET controllers give you low forward drop and, critically, reverse-current blocking so a fault on one feed can't drag the other down or back-feed it. If I use ORing FETs, I want them controlled by a scheme that fails safe: if the controller loses its own bias, the FET should default to off, not on. I'd also add independent current sensing per feed so the system knows which input is actually carrying load and can flag a feed that has silently dropped out.

For fault isolation, each downstream load branch gets its own protection — a fuse is too slow and non-resettable for a latch-up event, so I'd lean toward a current-limited load switch or an eFuse with a defined trip threshold and a latch-off or auto-retry behavior chosen per load criticality. The key architectural point is that a latch-up on one load must trip only that branch's protection, not collapse the common rail. That means the branch protection has to be faster than the bulk rail's own current limit, and the bulk capacitance has to be sized so a single branch fault doesn't sag the rail below the other loads' minimum operating voltage. I'd also think about whether the faulted branch should auto-retry (transient SET) or latch off (hard SEL) — auto-retry with a limited retry count is usually the right compromise, because a persistent short shouldn't be hammered indefinitely.

For hot-swap, the concern is inrush into the branch's bulk capacitance when a load is plugged in or when a branch is re-enabled after a fault. A load switch with a controlled slew rate — either a dedicated hot-swap controller with a programmed dV/dt or a gate-drive network that limits the FET's turn-on — keeps the inrush within the source's capability and avoids glitching the shared rail. I'd also add a soft-start on the bulk rail itself so the whole payload comes up gently.

The thing I'd be most careful about is the interaction between these: a hot-swap event on one branch can look like a fault to another branch's current monitor if the thresholds aren't coordinated. So I'd do a power budget and a fault-tree analysis up front, define the trip thresholds and timing for every protection element, and then verify the whole thing with a bench setup that can inject a short on one branch while monitoring the other.

**Possible follow-ups:**
- How would you decide between a latching and an auto-retry response for a branch that trips, and how would that decision change if the load is a critical actuator versus a housekeeping sensor?
- What would you look for on the bench to confirm that a hot-swap event on one branch isn't causing a nuisance trip on another?

## Q2: How would you approach derating and part selection for a space-deployed board, and how does derating interact with the radiation tolerance you're trying to achieve?

**Answer:** Derating and radiation tolerance are related but distinct, and I'd treat them as two separate filters that a part has to pass — not as substitutes for each other.

Derating is about reducing the electrical, thermal, and mechanical stress a part sees relative to its rated maximum, so that it has margin against the combined effects of manufacturing spread, aging, and the environment. For a space board I'd start from a derating standard — typically something in the MIL-STD-1547 / EEE-INST-002 family, or the program's own derating guideline — and apply it across voltage, current, power, junction temperature, and for some parts frequency and radiation. The exact numbers depend on the part class: a ceramic capacitor might be derated to 50% of rated voltage, a resistor to 60–70% of rated power, a semiconductor junction to a defined margin below its maximum. The point is that the part is never asked to operate near its limit, because the limit itself may have shifted by the time the part is in orbit.

Radiation tolerance is a separate axis. A part can be perfectly derated electrically and still be unusable if it has no TID data, or if its SEE cross-section is unknown. So part selection is really a two-dimensional problem: I need a part that meets the derating guideline *and* has radiation data adequate for the mission's environment — or, if it doesn't, I need to either qualify it myself or design around its uncertainty.

The interaction matters in a few places. First, TID degradation often shows up as parametric drift — leakage current increases, gain drops, reference voltage shifts — which eats into the margin that derating was supposed to preserve. So a part that's derated to 50% of its voltage rating at beginning of life may effectively be at 70% after 50 krad because its breakdown voltage has degraded. That means for radiation-exposed parts I want *more* derating margin than the baseline guideline, not less. Second, ELDRS (enhanced low-dose-rate sensitivity) can make a bipolar part degrade more at low dose rate than at the high dose rate used in many qualification tests, so the TID number on a datasheet may not be conservative for the actual mission. Third, displacement damage in optoelectronics and some semiconductors is cumulative and not captured by a simple voltage derating.

Practically, I'd build a part selection matrix: for each candidate, columns for electrical derating margin, TID rating vs. mission dose with margin, SEE data (SEL threshold, SEU cross-section), package and thermal suitability, and whether it's on a QML or has flight heritage. Parts that fail any column get flagged, and the program decides whether to qualify, mitigate, or replace. The derating and the radiation analysis feed each other — I don't do them in isolation.

**Possible follow-ups:**
- How would you handle a part that meets every derating guideline but has no radiation data at all, and the schedule doesn't allow a full qualification campaign?
- Where does derating interact with thermal design in a vacuum, given that there's no convection to carry heat away?

## Q3: How would you approach designing a radiation-tolerant analog signal chain for a spacecraft instrument where the sensor output is a low-level differential signal, and both the amplifier front-end and the ADC reference can experience single-event transients (SETs)?

**Answer:** The core problem is that a low-level differential signal has very little margin against a transient, and both the amplifier and the reference are single points where an SET can inject an error that looks like real signal. So I'd approach it as: make the signal as robust as possible before the first active device, then make the active devices' transients detectable and rejectable.

On the front end, I'd start with the sensor interface itself. A differential pair with good common-mode rejection, twisted or shielded routing, and a well-defined input filter helps reject both environmental noise and some of the transient energy. I'd put the anti-alias filter as close to the amplifier input as I can, because a filter before the first gain stage limits the bandwidth over which an SET can couple in. If the sensor allows it, I'd consider a passive or low-gain first stage so the first active device isn't running at high gain — high gain amplifies the transient along with the signal.

For the amplifier, I'd look for a part with radiation data, and if none is available, I'd design so that a transient on the amplifier output is detectable. That usually means either a redundant signal path (two amplifiers, compare outputs, flag a discrepancy) or a plausibility check downstream — if the ADC reading jumps outside the physically possible range for that sensor, reject the sample. For a critical measurement I'd lean toward the redundant path, because a plausibility check can't catch a transient that happens to land inside the valid range.

For the ADC reference, the concern is that an SET on the reference shifts the conversion result for every channel using that reference. The mitigations are: use a reference with radiation data if one exists; if not, filter the reference heavily (a large, low-ESR capacitor right at the reference pin, plus a series element if the reference can tolerate it) so a transient is attenuated before it reaches the ADC; and add a reference-monitor comparator that flags when the reference deviates beyond a window, so the system can discard conversions taken during that window. A ratiometric architecture — where the ADC's reference and the sensor excitation share the same source — can also help, because a common-mode shift on the reference partially cancels in the ratio.

The system-level piece is timing. If I know a transient has occurred (from the reference monitor or the redundant path), I need to know which samples are suspect and either discard them or flag them for the ground segment. That means the acquisition firmware needs a way to tag samples with a validity flag, and the telemetry needs to carry that flag. For a time-sensitive measurement where I can't just retry, the redundant path plus a voting or plausibility scheme is the only way to keep producing a usable value through a transient.

**Possible follow-ups:**
- How would you decide between a fully redundant analog path and a single path with plausibility checking, given the mass and power budget?
- If the reference monitor flags a transient, how would you handle the samples taken during the window — discard, interpolate, or flag and forward?

## Q4: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves to be acknowledged before I challenge the margin — otherwise the conversation becomes about who's right rather than about the design. So I'd start by restating what I understand the proposal to be and what problem it solves, and confirm I've understood it correctly. That does two things: it makes sure I'm not arguing against a straw man, and it signals that I'm engaging with the substance.

Then I'd move to the specific concern, and I'd try to make it concrete rather than general. "This is under-margined" is not a useful review comment; "the worst-case output of this converter is X, the load's absolute maximum is Y, and the gap is Z, which is smaller than the tolerance stack-up I'd expect over the mission" is. If I can point to a specific number, a specific datasheet line, or a specific failure mode, the engineer can engage with it directly. If I can't — if it's a gut feeling — then I should say so, and frame it as a question rather than a verdict: "I'm not sure this margin holds up under TID drift; can you walk me through how you accounted for that?"

I'd also be open to being wrong. The engineer may have considered something I haven't, or may have a justification I'm not aware of. If the proposal actually holds up under scrutiny, the right outcome is to accept it, and I should say that clearly. A design review where the lead never changes their mind isn't a review, it's a rubber stamp.

If we still disagree after the technical discussion, I'd try to find a way to resolve it that doesn't depend on authority. Options: ask the engineer to write up the analysis and the assumptions, and review it offline with a third party; propose a bench test or a worst-case analysis that would settle the question; or, if the risk is real but the schedule doesn't allow a full rework, propose a mitigation that reduces the risk without discarding the engineer's work — a monitor, a derating change, a screening step. The goal is to get to a decision the team understands and can defend, not to win the argument.

Throughout, I'd keep the tone on the design, not the designer. "I'm worried about this margin" is different from "you didn't think about this." And I'd make sure the engineer leaves the review knowing their work was taken seriously, even if the outcome was a change.

**Possible follow-ups:**
- What would you do if the engineer's proposal is technically defensible but you still believe the risk is unacceptable, and the schedule doesn't allow a full rework?
- How would you handle it if the same disagreement came up again in a later review, with the same engineer?

## Q5: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt (SEFI) that puts the main processor into a state where it's still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** The hard part of this test is that the failure mode is specifically designed to defeat the simplest recovery mechanism — a heartbeat monitor. So the test plan has to verify recovery from a state that looks alive to the watchdog but isn't actually running the control loop.

The first thing I'd do is define what "recovered" means, precisely. It's not enough that the processor resets; it has to come back up, re-initialize the control loop, and resume producing correct outputs within a bounded time. So the test needs a way to observe the control loop's actual output — not just the heartbeat — and confirm it's correct after recovery. That usually means instrumenting the firmware to emit a "control loop running" signal that's distinct from the heartbeat, or monitoring the actuator output directly.

For fault injection, since I can't inject actual radiation on the bench, I'd use a fault-injection harness that can put the processor into the target state deterministically. Options: a debugger that halts the core while leaving peripherals running (so the heartbeat keeps toggling but the loop stops); a firmware test mode that deliberately enters an infinite loop in the control task while a separate timer task keeps the heartbeat alive; or an external signal that corrupts a specific memory location the control loop depends on. The point is to reproduce the *symptom* — heartbeat alive, loop dead — not the cause.

Then I'd verify the recovery mechanism. If the design uses a heartbeat monitor, this test should show that the heartbeat monitor alone does *not* recover the system, which is the whole reason the test exists. If the design uses a more sophisticated monitor — a challenge-response watchdog, a control-loop output monitor, a cross-check between redundant tasks — the test should show that it does recover. I'd run the injection many times, at different points in the control loop's execution, to make sure the recovery isn't dependent on where the fault lands.

I'd also test the recovery's *completeness*. After recovery, does the system re-initialize state correctly? Does it resume from a safe state, or does it pick up stale data? Does it log the event so the ground segment knows it happened? A recovery that brings the loop back but leaves the system in an inconsistent state is not a recovery.

Finally, I'd test the boundary conditions: what if the fault happens during recovery? What if it happens repeatedly? What if the recovery mechanism itself is affected? The goal is to demonstrate that the system recovers from the target failure mode, and to find the cases where it doesn't, so they can be addressed before flight.

**Possible follow-ups:**
- How would you design the fault-injection harness so that it reproduces the target state without also triggering the recovery mechanism through some side effect?
- If the system uses a challenge-response watchdog, how would you verify that the challenge itself isn't being answered by a corrupted task?