# space-rad-hard — Day 71

## Q1: How would you approach designing a radiation-tolerant power distribution scheme for a payload that must survive a single-event latch-up (SEL) in any one load without losing the rest of the system, while also keeping the SEL from propagating back onto the primary bus?

**Answer:** The core idea is to treat each load as an independently protected branch rather than relying on a single upstream protection device. I'd start by partitioning the distribution into branches sized by current and criticality, then give each branch its own current-limiting element — a latching current limiter or an e-fuse with a defined trip threshold and a controlled response time. The trip threshold has to sit above the load's worst-case inrush and steady-state current but below the level at which a latched load would drag the rail down. That window is the whole design problem, so I'd characterize inrush carefully (capacitive loads, motor starts, hot-plug events) and add soft-start or slew-rate control where needed so the protection doesn't nuisance-trip.

For SEL specifically, the protection has to be able to *remove* power, not just limit it — a latched CMOS structure will hold the rail down until current is interrupted. So the branch switch needs a latch-off or retry-with-backoff behavior, and the retry logic needs to be bounded so a permanently damaged part doesn't oscillate. I'd also add per-branch telemetry (current, fault flag) so the controller can distinguish a transient overcurrent from a hard latch and decide whether to retry or isolate.

To keep a fault from propagating upstream, I'd make sure each branch's protection acts faster than the upstream converter's own limit, and I'd add bulk capacitance and/or a bus clamp so a sudden branch disconnect doesn't cause an inductive kick that disturbs the primary rail. Finally, I'd think about single points of failure in the protection itself — a single upstream fuse or a shared enable line can defeat the whole scheme — so I'd avoid shared control paths where the criticality justifies it.

**Possible follow-ups:**
- How would you decide between latch-off and automatic retry for a given branch, and what would drive that choice?
- How would you verify the protection scheme actually contains a latch during ground testing without being able to induce a real SEL?

## Q2: How would you approach selecting and qualifying a voltage reference for a precision ADC in a space application, given that most commercial references have no radiation data and the measurement must hold accuracy over a multi-year mission?

**Answer:** I'd separate the problem into three failure modes and treat each differently: total ionizing dose (TID) drift, enhanced low-dose-rate sensitivity (ELDRS) in bipolar references, and single-event transients (SETs) on the reference output.

For TID, the concern is parametric drift — initial accuracy is almost irrelevant over a multi-year mission compared to how the reference moves with accumulated dose. A part with excellent initial accuracy but no dose data is a liability. I'd look for references with published TID data, or at minimum a technology (buried Zener, certain bandgap topologies) with a well-understood dose response, and I'd budget the drift into the error analysis rather than assuming a calibration routine removes it — calibration corrects a *known* offset, not a parameter that continues to move after calibration.

ELDRS matters if the reference is bipolar: some parts degrade far more at low dose rate than at the high dose rate used in accelerated testing, so a part that "passes" a high-dose-rate screen can still fail in orbit. I'd want low-dose-rate data or a part known to be ELDRS-free.

For SETs, the reference output can glitch momentarily, which corrupts any conversion happening during the transient. Mitigations include filtering the reference (with attention to the filter's own radiation behavior), using a reference with a slow, well-damped response, and architecturally validating or averaging conversions so a single corrupted sample doesn't propagate into a control action.

If no qualified part fits, I'd consider a redundant reference with comparison, or a ratiometric approach where the reference and the signal share a common node so drift cancels — but I'd be explicit that this trades one error source for another.

**Possible follow-ups:**
- How would you structure the error budget to decide whether a given reference is acceptable?
- What would you do if the only reference that meets the accuracy target has no radiation data at all?

## Q3: You're leading a design review where a junior engineer has proposed a power architecture you believe is under-margined for the radiation environment. The engineer has done real analysis and is confident in it. How would you handle the disagreement so the review stays constructive and the right technical decision gets made?

**Answer:** First I'd make sure I actually understand their analysis before pushing back — a confident engineer with real work behind them often has a reason I haven't considered, and going in assuming they're wrong poisons the review. I'd ask them to walk me through their assumptions, especially the ones that are hardest to defend: what radiation environment did they assume, what part data did they rely on, and what happens at the corner where their margin is thinnest.

Then I'd reframe the disagreement away from "you vs. me" and toward the shared question: what does the mission actually require, and does this design meet it with margin we can defend? If the gap is a missing piece of data — no TID curve, no SET cross-section — that's not a matter of opinion, it's a gap we can close together, either by finding data or by testing. If the gap is a judgment call about acceptable risk, that's a decision the team should make explicitly and document, not something I should win by seniority.

I'd also separate "this is wrong" from "this is under-margined." Under-margined might be acceptable if the consequence is benign and recoverable; it's not acceptable if the failure mode is loss of a critical function. Naming the failure mode and its consequence usually moves the conversation from positions to trade-offs.

If we still disagree after that, I'd want the decision recorded with the reasoning and the residual risk, and I'd want a mitigation path — a test, a derating change, a fallback part — rather than just overruling. And I'd follow up privately afterward so the engineer doesn't feel the review was adversarial; the goal is a better design, not a quieter one.

**Possible follow-ups:**
- What if the engineer's analysis is correct but the schedule doesn't allow the mitigation you want?
- How do you keep a review constructive when you're the one being overruled?

## Q4: How would you approach designing a fault-tolerant I²C bus for a space-deployed system where multiple sensor nodes share the bus, given that single-event upsets can corrupt data or cause bus lock-ups?

**Answer:** I²C is a poor fit for a radiation environment in its vanilla form because it has several single points of failure: a stuck-low SDA or SCL from any node hangs the whole bus, there's no built-in error detection beyond the ACK bit, and clock stretching gives a misbehaving node a way to stall everyone. So the design has to add robustness at the protocol and physical layers.

At the physical layer, I'd add bus recovery logic — a controller-side routine that clocks SCL manually for a bounded number of cycles to flush a stuck slave, then issues a STOP. I'd also consider bus isolation so a failed node can be electrically removed rather than dragging the bus down, and I'd use a bus buffer or mux if the topology allows segmenting nodes.

At the protocol layer, I'd add a CRC or checksum to every message, since the ACK bit alone won't catch a corrupted payload. I'd add sequence numbers or a transaction ID so a retried message isn't double-applied, and I'd bound retries so a persistently failing node doesn't monopolize the bus. For critical data, I'd consider reading a value twice and comparing, or reading a value plus its complement, so a single corrupted read is caught.

I'd also think about the failure mode where a node's I²C state machine is corrupted by an SEU and it starts driving the bus incorrectly — that's where isolation and a watchdog on each node's bus interface help. And I'd make sure the controller itself has a timeout on every transaction, so a hung bus doesn't hang the controller.

**Possible follow-ups:**
- How would you decide which nodes need isolation versus which can share a segment?
- What's the trade-off between adding CRC and the extra bus traffic it creates?

## Q5: How would you approach designing a test plan to verify that a system recovers correctly from a single-event functional interrupt (SEFI) that puts the main processor into a state where it's still drawing current and still toggling a heartbeat line, but no longer executing the control loop?

**Answer:** The hard part here is that the failure mode is *silent* — the processor looks alive to a naive watchdog because the heartbeat is still toggling, so the test has to prove the recovery mechanism catches a fault that a simple timeout would miss. I'd start by defining what "recovery" means concretely: the control loop resumes, outputs return to a safe state, and any state that was in flight is either completed or cleanly abandoned.

Since I can't inject real radiation on the ground, I'd use fault injection at the firmware level — deliberately corrupting the state that the heartbeat depends on, or forcing the processor into a spin loop that still services the heartbeat, so the recovery logic is exercised against the exact failure mode. I'd also use hardware debug (JTAG halt, or a debugger that can freeze the core while leaving peripherals running) to simulate a hung core.

The test has to verify the *detection* mechanism, not just the recovery. If the design uses a heartbeat, I'd test that a heartbeat that's toggling but not advancing a sequence counter is still caught — that's the whole point. If the design uses a challenge-response or a "control loop alive" flag distinct from the heartbeat, I'd verify that flag is what actually triggers recovery.

I'd also test the recovery path itself: does the reset actually clear the hung state, does the system come back to a known-good configuration, and does it do so without corrupting persistent state or causing an unsafe output transient during the reset? And I'd test the boundary cases — recovery when the fault happens mid-transaction, recovery when it happens repeatedly, and recovery when the watchdog itself is the thing that's been corrupted.

Finally, I'd document the test coverage explicitly, because "we tested recovery" is not the same as "we tested recovery from the specific failure mode that a heartbeat-only watchdog would miss."

**Possible follow-ups:**
- How would you design the heartbeat or liveness signal so it can't be satisfied by a hung processor?
- What would you do if the recovery mechanism itself is susceptible to the same SEFI?