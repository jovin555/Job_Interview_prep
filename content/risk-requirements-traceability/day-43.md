# risk-requirements-traceability — Day 43

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a hardware analog circuit with a trim potentiometer that must be calibrated during manufacturing — where the calibration setting itself is part of the risk control, and the verification test must confirm both the circuit function and the calibration tolerance?

**Answer:** This is a good example of a risk control that spans design, manufacturing, and verification — and it exposes why traceability can't stop at the engineering lab. I'd approach it in layers.

First, the risk management file should state the hazard, the control mechanism (the analog circuit), and the fact that the control's effectiveness depends on the calibration setting being within a specified range. That dependency needs to be explicit, not implicit — otherwise someone downstream could treat calibration as a purely manufacturing concern with no safety significance.

Second, the requirements need to capture both the functional behavior (e.g., the circuit trips at a specified threshold) and the calibration tolerance (e.g., the trim setting must be within X% of nominal). These are two distinct requirements, even though they're verified together. The calibration tolerance requirement should trace to the manufacturing procedure, not just to the design verification test — because the calibration happens at manufacturing time, and the design verification test on an engineering prototype doesn't prove the manufacturing process can consistently hit the tolerance.

Third, the verification strategy needs to distinguish between design verification and production verification. Design verification confirms the circuit design is sound — that with a correctly calibrated trim setting, the circuit trips at the right threshold across the operating temperature range. Production verification (or process validation) confirms the manufacturing process can actually set the trim within tolerance. These are different questions requiring different evidence.

For the traceability matrix, I'd create links from the hazard → risk control measure → the two requirements (functional and calibration tolerance) → design verification test for the functional behavior → manufacturing process validation for the calibration tolerance. The calibration requirement should also trace to the work instruction or test procedure used on the production line.

One subtlety: the trim potentiometer itself introduces a failure mode — it could drift after calibration, or be set incorrectly. So the risk analysis should consider whether the calibration needs to be verified at final test, or whether the circuit design should include a way to detect out-of-tolerance settings. That decision affects what goes into the traceability scheme.

**Possible follow-ups:**
- How would you handle the situation where the calibration tolerance is verified at manufacturing, but the functional trip point is only verified during design verification — is that acceptable, and under what conditions?
- What if the trim potentiometer is replaced with a digitally trimmable potentiometer controlled by firmware — how would that change your traceability approach?

---

## Q2: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a safety mechanism that can be bypassed or overridden by a clinician — for example, a "disable alarm" button on a patient monitoring device — and the override itself introduces a new hazard?

**Answer:** This is a classic case where the risk control measure creates a secondary risk, and the traceability scheme has to capture both the primary control and the new hazard introduced by the override capability.

I'd start by making sure the risk analysis itself is complete. The "disable alarm" button is a risk control for one hazard — perhaps nuisance alarms causing clinician distraction or alarm fatigue — but it introduces a new hazard: the alarm being disabled when a critical condition occurs. The risk analysis needs to document both the intended benefit (reducing alarm fatigue) and the new risk (missed critical alarms), along with any additional controls (e.g., automatic re-enable after a timeout, visual indicator that alarms are disabled, maximum disable duration).

For traceability, I'd create two parallel chains. The first chain traces the original hazard → the override capability as a risk control → the requirement that implements the override (e.g., "the user shall be able to temporarily silence audible alarms for a maximum of 2 minutes"). The second chain traces the new hazard (missed alarms while disabled) → the additional risk controls (e.g., visual alarm indicator, automatic re-enable) → their corresponding requirements.

The key point is that the override feature generates requirements that wouldn't exist otherwise, and those requirements need their own verification activities. The verification for the override must confirm not just that the button works, but that the mitigating controls work — that the visual indicator is visible, that the alarm re-enables after the timeout, that the disable function cannot be activated indefinitely.

In the traceability matrix, I'd make the relationship explicit: the override requirement traces both to the original hazard (as a control) and to the new hazard (as a hazard source). This dual relationship is important because it prevents someone from later removing the override feature without re-evaluating the original hazard, or from removing the mitigating controls without re-evaluating the new hazard.

I'd also consider whether the override needs to be treated differently in verification — for example, testing that the alarm disable function works correctly under nominal conditions, but also testing the failure scenario where the clinician forgets to re-enable alarms, to confirm the automatic re-enable mechanism functions as intended.

**Possible follow-ups:**
- How would you handle the traceability if the override is implemented in firmware but the decision to include the override was made during the risk analysis — where does that decision get documented?
- What if the override is a mechanical switch that bypasses the alarm circuit entirely — how would that change your verification approach?

---

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a software unit test that runs on a host PC (not the target hardware), and the risk control involves timing behavior that depends on the microcontroller's clock speed and interrupt latency?

**Answer:** This is a mismatch between the verification method and the nature of the risk control. The traceability matrix says the risk control is verified, but the verification evidence may not actually demonstrate the control works under real conditions.

I'd start by analyzing what the risk control actually depends on. If the timing behavior — say, a watchdog timeout or a response deadline — depends on the microcontroller's clock speed, interrupt latency, and peripheral timing, then a host PC test cannot fully verify it. The host PC has a different processor, different clock, different interrupt controller, and different compiler optimizations. The unit test might verify the logic is correct — that the firmware implements the right algorithm — but it can't verify the actual timing on the target hardware.

The right approach is to treat the host PC test as one layer of verification, not the complete verification. The host PC test verifies the software logic: the state machine transitions correctly, the timeout value is computed correctly, the response path is exercised. But you also need a target-hardware test that measures actual timing — for example, asserting a fault signal and measuring the time until the response occurs, using an oscilloscope or logic analyzer.

In the traceability matrix, I'd document both verification activities against the risk control requirement. The host PC test verifies the logical behavior; the target-hardware test verifies the timing performance. Each test covers a different aspect of the requirement, and both are needed for complete coverage.

If the risk control requirement is written purely in terms of logic — "the firmware shall transition to fault state when the timeout expires" — then the host PC test might be sufficient. But if the requirement includes timing — "the firmware shall disable the motor output within 100ms of the fault condition" — then the host PC test alone is inadequate, because it can't demonstrate the 100ms timing on different hardware.

I'd also consider whether the host PC test environment introduces any false confidence. A unit test that passes on a host PC might miss issues like interrupt priority inversion, timing jitter from other tasks, or cache effects — all of which only appear on the target hardware. So the traceability should reflect that the host PC test is necessary but not sufficient.

**Possible follow-ups:**
- How would you decide whether a host PC test is sufficient for a given risk control, or whether target-hardware testing is required — what criteria would you use?
- If the schedule only allows one verification activity, and you have to choose between the host PC test and the target-hardware test, which would you prioritize and why?

---

## Q4: How would you approach determining whether a risk control measure that is implemented as a hardware fuse (one-time, non-resettable) needs to be verified on every production unit, or whether verification on a sample basis is sufficient?

**Answer:** This is fundamentally a question about the nature of the risk control and the failure modes that verification is meant to detect. A hardware fuse is a one-time device — once it blows, it's destroyed — so you can't test it on every unit without destroying every unit. The question becomes: what are you actually trying to verify, and what failure modes are you trying to detect?

There are really two different things being verified. First, the design is correct: the fuse rating is appropriate for the circuit, the fuse will blow under the specified fault conditions, and it will not nuisance-blow under normal operation. This is design verification — it's done on engineering samples, and it's a one-time activity. You deliberately blow fuses under fault conditions to confirm they protect the circuit as designed.

Second, the manufacturing process is correct: the right fuse is installed in the right location, with correct solder joints, and no damage occurred during assembly. This is production verification. For a fuse, this typically involves inspection — visual inspection, automated optical inspection, or X-ray inspection for solder joint quality — rather than functional testing, because you can't functionally test a fuse without destroying it.

The question of sample-based versus 100% verification depends on the risk associated with a fuse failure. If a missing or incorrectly installed fuse could lead to a hazardous condition — say, a fire or an electric shock — then you might want 100% inspection, perhaps using automated optical inspection or electrical test that verifies the fuse is present and has the correct resistance (without blowing it). If the consequence of fuse failure is less severe, sample-based inspection might be acceptable, with the sample size justified by statistical process control data.

I'd also consider whether there are additional controls that reduce the need for 100% fuse verification. For example, if the circuit design includes redundancy — a second fuse or a different protection mechanism — then the risk of a single fuse failure is lower, and sample-based verification might be justified.

In the traceability matrix, I'd document the design verification separately from the production verification. The design verification confirms the fuse rating and circuit behavior; the production verification confirms the fuse is correctly installed. Both trace to the same risk control measure, but they're different verification activities with different methods and different sample sizes.

**Possible follow-ups:**
- How would you justify your sample size decision to a quality auditor who expects statistical rationale?
- What if the fuse is a critical safety component and the regulatory standard requires 100% verification — how would you handle that constraint?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that the verification activities are all scheduled for the very end of the project, after all design work is complete. The program manager argues that this is efficient because it avoids rework — the design is finalized before testing begins. The quality manager argues that late verification means design errors are discovered too late, causing expensive rework and schedule delays. How would you resolve this disagreement?

**Answer:** I'd start by acknowledging that both perspectives have merit, which is important for keeping the conversation constructive. The program manager is right that testing a moving target wastes effort — if the design is still changing, test results become obsolete quickly. The quality manager is right that discovering a fundamental design flaw at the end of the project is the most expensive possible outcome.

The resolution isn't to pick one side but to recognize that different types of verification have different optimal timing. Some verification activities are inherently late — final system-level validation against user needs, for example, can't happen until the system is complete. But other verification activities should happen much earlier. Design reviews, simulation, analysis, and unit-level testing can and should occur throughout development.

I'd propose restructuring the verification schedule into layers. Early in the project, focus on verification activities that catch fundamental design errors cheaply — design reviews, worst-case analysis, simulation, prototype testing of critical subsystems. Mid-project, as the design stabilizes, run more detailed verification — module-level testing, interface testing, environmental testing on engineering prototypes. Late in the project, run the final verification campaign — full system testing, regulatory testing, production-representative testing.

The key insight to share with both managers is that verification isn't a single event — it's a continuum. The goal is to catch each class of error at the earliest point where it's economically detectable. A PCB layout error is cheapest to catch at design review, more expensive at prototype testing, and most expensive if it's only caught during final system testing. A software logic error is cheapest to catch at unit test, more expensive at integration test, and most expensive in the field.

I'd also point out that the traceability matrix itself can help with scheduling. If we sort the verification activities by what they're verifying, we can identify which ones depend on early design decisions and which ones can wait. For example, a verification test for a risk control that depends on the mechanical enclosure design can't run until the enclosure is finalized — but a verification test for a firmware plausibility check could run much earlier on a development board.

Finally, I'd suggest a compromise: keep the final verification campaign as the official compliance evidence, but add interim verification milestones where the team reviews preliminary results and identifies risks early. This gives the program manager the stable design they want, and gives the quality manager early warning of potential issues.

**Possible follow-ups:**
- How would you handle the situation where the program manager agrees in principle but says there's no budget for early verification activities?
- What specific early verification activities would you prioritize for a medical device with firmware, hardware, and mechanical subsystems, and how would you justify each one?