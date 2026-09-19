# space-rad-hard — Day 60

## Q1: How would you approach designing a radiation-tolerant, high-reliability power feed for a payload that has two independent 28V bus inputs, where the system must survive a shorted or latched load on one feed without losing the other, and must also handle hot-swap events without disturbing the bus?

**Answer:** I'd treat this as three separate problems that share one architecture: fault isolation between feeds, inrush/hot-swap control, and latch-up containment on the load side.

For the two-feed architecture, the goal is that a fault on one feed never propagates to the other or to the downstream load. That means each feed gets its own blocking element — an ideal-diode/ORing controller or a suitably rated diode — so a short on one input cannot back-feed from the other. I'd avoid a simple passive OR of the two rails without current limiting, because a latched load can drag the shared node down and take the good feed with it. Instead, each feed path gets its own current-limited switch or eFuse, so an overcurrent event on one path trips only that path. The two paths then combine at a point that is itself protected.

For hot-swap, the concern is inrush into the downstream bulk capacitance when a feed is inserted or when the system switches over. I'd use a hot-swap controller with a controlled slew rate on the pass FET gate, plus a defined current limit and a fault timer, so the FET operates in its safe operating area during the inrush window rather than being stressed into failure. The current limit has to be set above the legitimate inrush peak but below the level that would damage the FET or disturb the bus. Sequencing matters too — I'd want the second feed to come up cleanly without a glitch on the first.

For latch-up containment, the load-side protection is what actually saves the system. A single-event latch-up looks electrically like a sudden low-impedance overcurrent. If the per-load current limit is set correctly and the latch-up is detected as a sustained overcurrent beyond a timeout, the switch can cycle power to that load only, leaving the rest of the payload running. The key design decision is the timeout: too short and you nuisance-trip on legitimate transients; too long and the latched device cooks. I'd also make sure the protection is latching-off rather than auto-retry in a tight loop, so a hard fault doesn't cause repeated inrush events.

The cross-cutting concern is that all of this has to be evaluated for radiation — the controller ICs themselves need either rad-tolerant parts or a design that tolerates their failure modes, and the current-sense elements need to hold their value over TID.

**Possible follow-ups:**
- How would you decide between a latching-off protection scheme and an auto-retry scheme for a load that's critical to the mission?
- What happens to your architecture if the ORing controller itself experiences a single-event transient that momentarily turns both paths on at once?

## Q2: How would you approach derating and part selection for a space-deployed board, and how does derating interact with the radiation tolerance you're trying to achieve?

**Answer:** Derating and radiation tolerance are two independent reliability levers, and the trap is treating them as substitutes. Derating buys margin against the ordinary stresses of launch, thermal cycling, and long-term drift; radiation tolerance addresses a completely different failure mechanism. A part that's derated to 50% of its voltage rating is not thereby more radiation-tolerant, and a rad-hard part still needs derating.

My approach to derating starts with the applicable standard — typically the derating tables in a space agency or MIL-style guideline — and applies them per component class: voltage, current, power, junction temperature, and for some parts frequency or gain. The point of derating is to keep the part away from the region where wear-out and parametric drift accelerate, and to leave headroom for the fact that the datasheet limits are themselves statistical. For a space board I'd pay particular attention to junction temperature derating, because in vacuum the thermal path is conduction-only and the margin you assumed on a bench with air cooling may not exist.

The interaction with radiation is where it gets interesting. TID causes parametric shifts — leakage currents rise, thresholds move, gain drops, reference voltages drift. If a part is derated tightly against its end-of-life limits, a TID-induced shift can push it out of spec even though the part is nominally "rad-tolerant." So the derating analysis has to be done against post-irradiation limits, not fresh-part limits, wherever radiation data exists. For parts with no radiation data, derating doesn't rescue you — it just means you don't know the post-irradiation behavior, and that's a qualification problem, not a margin problem.

There's also a subtle interaction with single-event effects. Derating a transistor's operating voltage reduces some single-event upset cross-sections and can reduce latch-up susceptibility, because latch-up depends on the parasitic thyristor turning on, which is voltage- and current-dependent. So sensible derating does help SEE margin somewhat — but it's a secondary effect, not a substitute for SEL-hardened parts or current-limited rails.

Practically, I'd maintain a derating table alongside the radiation tolerance table for every part, and flag any part where either column is unknown. Unknown in either column is a risk item that has to be closed before the design is considered qualified.

**Possible follow-ups:**
- How would you handle a part where the radiation data exists but only at a dose rate much higher than the mission's actual dose rate?
- Where does enhanced low-dose-rate sensitivity (ELDRS) fit into your derating analysis for bipolar parts?

## Q3: You're reviewing a design where a junior engineer has used a single-ended, non-redundant analog signal chain — sensor, amplifier, ADC — for a measurement that feeds a control loop. The engineer argues that the digital side already has TMR, so the analog side is "covered." How would you evaluate this argument?

**Answer:** The argument has a category error in it. TMR on the digital side protects against upsets in the digital logic — it does nothing for a single-event transient that corrupts the analog measurement before it ever reaches the ADC. If the analog front-end produces a wrong value, the digital logic will faithfully process, vote on, and act on that wrong value. Redundancy downstream of a single point of failure doesn't remove the single point of failure.

So the first thing I'd do is trace the actual failure path. Where can a single event corrupt the measurement? Candidates: the sensor itself, the amplifier (an SET can cause a transient output excursion), the ADC's sample-and-hold or reference, and the interconnect. If any of those can produce a plausible-but-wrong reading that the control loop would act on, then the analog chain is a real vulnerability regardless of what the digital side does.

Then I'd ask what the consequence of a wrong reading actually is. If the control loop is slow relative to the SET duration, and the loop has any filtering or plausibility checking, a brief transient may be rejected naturally. If the loop is fast and the actuator responds immediately, a single bad sample can cause a real physical excursion. The mitigation has to match the consequence.

Options I'd consider, roughly in order of cost: plausibility/range checking on the ADC result before it's used, so an out-of-range value is discarded rather than acted on; rate-of-change limiting, so a physically implausible jump is rejected; temporal redundancy — taking multiple samples and requiring agreement before acting; and spatial redundancy — two independent signal chains with a comparison, which is the analog equivalent of TMR but much more expensive in board area, power, and calibration effort.

I'd also point out that the digital TMR and the analog chain aren't independent if they share a reference, a supply, or a clock. A single event on a shared reference can corrupt both "redundant" paths simultaneously. So the review question isn't just "is the analog side redundant?" — it's "what is actually independent, and what is shared?"

The constructive framing for the junior engineer: the digital TMR is good work and it's necessary, but it's protecting a different failure mode. The question is whether the analog chain's failure modes are covered, and if not, what the cheapest adequate mitigation is.

**Possible follow-ups:**
- How would you decide between plausibility checking and full dual-chain redundancy for a given measurement?
- If the sensor and amplifier share a reference with the digital side, does that change your assessment of the TMR's value?

## Q4: How would you approach selecting and qualifying a voltage supervisor or reset IC for a space-deployed system, given that most commercial parts are not radiation-characterized?

**Answer:** A voltage supervisor is a deceptively simple part that sits in a critical path — if it fails, the whole system either resets when it shouldn't or fails to reset when it should. So I'd treat the selection as a risk-management exercise rather than a simple BOM pick.

First, I'd define what the supervisor actually has to do and what failure modes matter. The core function is: assert reset when the rail is out of tolerance, deassert when it's stable, and hold reset long enough for the processor to initialize. The failure modes that matter in space are: false assertion (nuisance reset), failure to assert (processor runs on a bad rail), threshold drift over TID, and single-event-induced glitches on the reset output.

Then I'd look at what radiation data exists. For most commercial supervisors, there's none. That leaves a few paths. One is to find a part with at least some published SEE data, even if it's not a full QML qualification — sometimes a manufacturer has done heavy-ion testing for a related part in the same family. Another is to design around the uncertainty: use a supervisor whose failure mode is benign, or add external filtering and hysteresis so a transient on the reset line doesn't propagate. A third is to test the candidate part myself, which for a low-cost part is often feasible at a heavy-ion facility even on a limited budget, because the test setup is simple.

I'd also consider whether the supervisor needs to be a dedicated IC at all. A discrete supervisor built from a rad-tolerant comparator and a reference can be more predictable than an uncharacterized integrated part, because you can reason about each element's behavior and you have more control over the threshold and hysteresis. The trade-off is board area and complexity.

For the reset output itself, I'd want it to be robust against SETs — a short glitch on reset can cause a spurious reboot, which in a control system is a real event. That argues for an RC filter on the reset line, or a supervisor with a built-in glitch filter, or a latching reset that requires a deliberate clear.

Finally, I'd document the qualification approach explicitly: what data exists, what testing was done, what the residual risk is, and what the mitigation is. "No radiation data" is acceptable only if it's a conscious, documented decision with a mitigation, not an oversight.

**Possible follow-ups:**
- How would you test a candidate supervisor at a heavy-ion facility on a limited budget — what would your test setup and pass/fail criteria be?
- If the supervisor's threshold drifts over TID, how would that interact with your power supply's regulation tolerance?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so that the review stays constructive and the right technical decision gets made?

**Answer:** The first thing I'd do is separate the person from the proposal. The engineer has done real work, and that deserves acknowledgment before I challenge anything — otherwise the conversation becomes about defending their effort rather than about the design. I'd start by restating what I understand their approach to be, so they know I've actually engaged with it, and then frame my concern as a question rather than a verdict: "Help me understand how this behaves under [specific radiation condition]."

The key is to make the disagreement about a shared criterion, not about my authority versus their judgment. In a radiation context, that criterion is usually traceable to a requirement — a dose level, a SEE cross-section limit, a derating rule, a mission profile. If I can point to the specific requirement the design is under-margined against, the conversation shifts from "I think this is risky" to "here's the number this has to meet, and here's why I don't think it does." That's a much easier conversation, and it's also fairer — if I'm wrong about the requirement, the engineer can show me.

If the engineer pushes back with a technical argument, I want to actually hear it. Sometimes the junior engineer has information I don't — a part revision, a test result, a mitigation I didn't know about. Being genuinely open to that is not just good manners; it's how you avoid making a bad call because you were too senior to listen. If their argument holds up, I should say so and update my position.

If it doesn't hold up, I'd try to find the smallest experiment or analysis that would settle it, rather than continuing to argue. Can we get the radiation data? Can we run a worst-case analysis? Can we test the specific failure mode? A concrete next step is better than a stalemate, and it gives the engineer a path to being right if they are.

Throughout, I'd keep the tone on the design, not the designer. "This margin is thinner than I'm comfortable with" is different from "you didn't think this through." And I'd be explicit that the goal is a design that survives the mission, not a design that wins the review.

If after all that we still disagree, I'd make the decision, document the reasoning, and own it — but I'd make sure the engineer understood that the decision was about the risk, not about them, and that their work on the proposal was valuable.

**Possible follow-ups:**
- What would you do if the engineer's approach was actually correct and you were the one who was under-informed?
- How would you handle it if the same disagreement came up again in a later review with a different engineer?