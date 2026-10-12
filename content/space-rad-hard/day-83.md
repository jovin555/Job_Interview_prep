# space-rad-hard — Day 83

## Q1: How would you approach designing a radiation-tolerant analog-to-digital conversion subsystem where the ADC's voltage reference is a COTS part with no radiation data, and the measurement must hold accuracy over a multi-year mission?

**Answer:** The core problem is that a precision measurement is only as good as its reference, and an uncharacterized reference is an unknown in the error budget. I'd start by decomposing the error sources: initial accuracy, temperature drift, long-term drift, and the radiation-induced terms — total ionizing dose (TID) shift, enhanced low-dose-rate sensitivity (ELDRS) if it's a bipolar reference, and single-event transients (SETs) on the reference output. The datasheet covers the first three; the radiation terms are the gap.

My approach would be layered. First, I'd try to avoid the problem: look for a reference with at least some radiation characterization, even if it's not full QML, or a topology that is inherently less sensitive — for example, a buried-Zener or a bandgap with a proven low ELDRS history. If no characterized part exists, I'd treat the reference as a risk item and design around it. That means:

- **Margin the design** so that a bounded reference drift still leaves the system within its accuracy spec. If the spec is tight, this may force a different architecture.
- **Add a calibration path.** A ratiometric measurement — where the ADC measures the sensor against the reference and the reference drift cancels — is far more robust than an absolute measurement. If the sensor itself can be excited from the same reference, the ratio is stable even if the absolute reference moves.
- **Add an in-flight reference check.** A stable, radiation-hard secondary reference (even a lower-accuracy one) can be switched in periodically to detect gross drift, and the firmware can flag or compensate.
- **Filter SETs.** A reference SET is a fast transient; an RC filter on the reference output plus a median or majority filter in firmware on the ADC samples can reject single-sample spikes without corrupting the real signal.

The key judgment is that you can't calibrate out a drift you can't observe, so the design must either make the reference's absolute value irrelevant (ratiometric) or provide an independent way to observe it. I'd document the residual risk explicitly and, if budget allows, run a limited TID test on a few samples to bound the drift rather than assume it.

**Possible follow-ups:**
- How would you decide between a ratiometric architecture and an absolute measurement with periodic calibration?
- If the reference is bipolar and you're worried about ELDRS, how would you test for it without a full low-dose-rate facility?

## Q2: How would you approach designing a fault-tolerant power distribution scheme for a payload with multiple loads of different criticality, where a single-event latch-up (SEL) in any one load must not take down the rest of the system?

**Answer:** The design principle is that a SEL is a local fault and must stay local. The architecture should be a star, not a daisy chain: each load gets its own protection and its own current-limited feed from a common bus, so a latched load can only drag down its own branch.

Concretely, I'd work through it in layers:

- **Per-load current limiting.** Each branch gets a current-limit switch or an eFuse with a defined trip threshold. The threshold must be above the load's worst-case inrush but below what would collapse the bus. This is the primary containment.
- **Latch-up detection and power cycling.** A SEL typically shows as a sustained overcurrent. The protection device should latch off on overcurrent, and the controller should attempt a power cycle after a timeout — many SELs clear when power is removed. If the overcurrent persists after a retry, the load is declared failed and isolated permanently.
- **Bus stiffness.** The upstream bus and its bulk capacitance must be sized so that the transient of one branch tripping doesn't sag the bus below the other loads' minimum operating voltage. This is a decoupling and source-impedance question as much as a protection question.
- **Criticality tiering.** The most critical loads — the ones whose loss ends the mission — should not share a protection branch with non-critical loads, and may warrant their own redundant feed. Lower-criticality loads can share a branch if the analysis shows a single SEL can't take out two critical functions at once.
- **Fault reporting.** Each branch's protection should report status so the system knows which load latched and can log it, rather than silently retrying forever.

The trade-off is between protection granularity and complexity/volume. More branches means more parts and more failure points, so I'd tier by criticality rather than protect every load identically. I'd also verify the scheme with a fault-injection test — short a branch and confirm the rest of the system rides through.

**Possible follow-ups:**
- How would you set the current-limit threshold when a load has a large capacitive inrush?
- What's the risk of a protection device itself being sensitive to radiation, and how would you mitigate it?

## Q3: You're reviewing a design where a junior engineer has proposed using a single commercial LDO with no radiation data to post-regulate a critical analog rail, arguing that the upstream DC-DC is already rad-tolerant so "the LDO doesn't matter." How would you evaluate this argument?

**Answer:** The argument has a real kernel — the upstream converter does the heavy lifting for efficiency and isolation — but it's incomplete, and I'd want to walk through why carefully rather than just overrule it.

The LDO is in the signal path for the analog rail, so its behavior directly affects measurement accuracy. Three concerns:

1. **TID drift.** An uncharacterized LDO can shift its output voltage, reference, and dropout over dose. On a critical analog rail, even a small output shift changes the ADC's full-scale and the sensor's bias point. The upstream converter being rad-tolerant doesn't help — the LDO's own error is added on top.
2. **SETs.** An LDO can produce output transients under heavy ions. On an analog rail feeding a precision ADC or a sensor front-end, a transient during a conversion corrupts the measurement. The upstream converter's stability doesn't prevent this.
3. **SEL.** An LDO is a candidate for latch-up, and if it latches, the analog rail collapses regardless of how good the upstream is.

So the correct framing is: the upstream converter's tolerance is necessary but not sufficient. The LDO's own radiation behavior is a separate line item in the error and reliability budget.

How I'd handle it: I'd ask the engineer to show me the LDO's radiation data, or a plan to bound it. If none exists, I'd look for alternatives — a rad-tolerant LDO, a discrete pass element with a characterized reference, or a topology that removes the LDO entirely (e.g., a well-filtered rail straight from a rad-tolerant converter). If the LDO must stay, I'd add mitigation: output filtering for SETs, a supervisor to detect rail collapse, and margin in the accuracy budget for TID drift. The point isn't to reject the part — it's to make the risk explicit and either bound it or design around it.

**Possible follow-ups:**
- If you can't find a rad-tolerant LDO, what discrete alternative would you consider?
- How would you test an LDO's SET behavior on a limited budget?

## Q4: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt (SEFI) that leaves the processor still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** This is the hard case for watchdogs, because the usual "is the heartbeat toggling?" check passes while the system is actually dead. The test plan has to prove recovery from a *silent* hang, not just a stopped clock.

First, I'd define what "recovered" means: the control loop resumes producing correct outputs within a bounded time, the system state is consistent (no corrupted setpoints), and the event is logged. Then I'd build fault injection that reproduces the specific failure mode — a processor that's alive enough to toggle a pin but not running the loop.

Injection methods, roughly in order of fidelity:

- **Firmware-injected hang.** Add a test hook that deliberately enters a state where the heartbeat toggles but the control loop is skipped. This is the cheapest and most controllable way to exercise the recovery logic.
- **Debugger-forced state.** Halt the core in a way that leaves a timer or DMA still toggling the heartbeat, then release and observe recovery.
- **Fault injection on the bus or memory.** Corrupt a critical variable or a return address to induce a hang, and verify the recovery path catches it.

The recovery mechanism itself needs to be designed for this case, and the test verifies it. A plain heartbeat watchdog won't catch it, so the design needs a *functional* watchdog: the control loop must "check in" with a value that proves it actually ran — for example, a counter that only increments when the loop completes, or a challenge-response where the watchdog asks a question the loop must answer. If the loop is skipped, the check-in value goes stale and the watchdog fires.

The test plan would then verify: (a) the functional watchdog fires within the specified window, (b) the reset or recovery brings the loop back, (c) the system state is re-initialized safely, and (d) the event is logged. I'd also test the boundary — a loop that runs slowly but correctly should *not* trigger a false reset.

**Possible follow-ups:**
- How would you distinguish a slow-but-correct loop from a hung loop without false positives?
- What's the risk that the functional watchdog itself is affected by the same SEFI, and how would you mitigate it?

## Q5: You're leading a design review where a junior engineer has proposed a solution you believe is under-margined for the radiation environment. The engineer is confident and has done real work on it. How would you handle the disagreement so the review stays constructive and the right technical decision gets made?

**Answer:** The goal is to get to the right answer, not to win the argument, and the engineer's confidence usually means they've thought about it — so I'd start by genuinely understanding their reasoning before pushing back.

My approach:

1. **Separate the person from the proposal.** I'd frame it as "help me understand the margin here" rather than "this is wrong." That keeps the engineer engaged and often surfaces information I didn't have.
2. **Get to the shared model.** I'd ask them to walk me through the worst-case conditions they assumed — the radiation environment, the part's behavior, the derating. Often the disagreement is about an assumption, not the conclusion. If we can agree on the assumptions, the conclusion usually follows.
3. **Make the risk explicit and quantified.** "Under-margined" is vague; I'd try to turn it into a number or a bounded statement. What's the worst-case drift? What's the probability of the failure mode? What's the consequence if it happens? If the engineer can show the margin is actually adequate under a defensible worst case, I should update my view.
4. **Use evidence, not authority.** If I still believe it's under-margined, I'd bring data — a datasheet limit, a test result, a similar past failure, a standard's requirement — rather than "I've been doing this longer." That keeps it technical.
5. **Offer a path, not just a veto.** If the part or approach can't be justified as-is, I'd propose options: add mitigation, add margin elsewhere, test to bound the risk, or choose an alternative. Giving the engineer a way to solve the problem preserves ownership.
6. **Decide and document.** At some point the review has to converge. If we can't agree, I'd make the call, explain the reasoning, and record the decision and its rationale so it's traceable. If the engineer still disagrees, I'd want their dissent noted — that's healthy, and it protects the project if my call turns out wrong.

The constructive part is that the engineer should leave the review feeling heard and clear on *why* the decision went the way it did, even if it didn't go their way. That's what keeps them bringing proposals forward.

**Possible follow-ups:**
- What if the engineer's proposal is actually correct and your concern was based on a stale assumption?
- How would you handle it if the engineer becomes defensive and the review stalls?