# risk-requirements-traceability — Day 49

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a hardware watchdog timer monitoring a firmware heartbeat, when the hardware and firmware teams each document their portions in separate specifications with no cross-references?

**Answer:** The core problem here is that the risk control is a *system-level* function — neither the hardware watchdog alone nor the firmware heartbeat alone mitigates the hazard; it's the interaction between them that provides the safety function. My approach would be to first define a single, system-level risk control identifier in the risk management file that represents the complete watchdog function, with a clear description of the hazard it mitigates and the failure condition it addresses (e.g., firmware hang leading to uncontrolled output).

From there, I'd establish the traceability chain at three levels. At the system level, the risk control links to a system requirement stating that the system shall reset within a specified time if the main control loop stops executing. This requirement is deliberately implementation-agnostic — it doesn't say "watchdog" or "heartbeat" — so it sits above the hardware/firmware split.

At the subsystem level, I'd work with each team to identify which of their existing requirements contribute to that system requirement. The hardware team likely has a requirement for the watchdog timer's timeout period and reset assertion. The firmware team likely has a requirement for the heartbeat toggle rate and the task that generates it. Each of these subsystem requirements gets a trace link *upward* to the system requirement, and the system requirement traces *downward* to both. This creates the cross-reference that's missing — even though the two documents don't reference each other directly, they both reference the same system-level parent.

For verification, I'd insist on three activities: hardware verification that the watchdog asserts reset when the heartbeat stops (this can be tested by simply not toggling the heartbeat), firmware verification that the heartbeat is generated correctly under normal operation, and — critically — a system-level test that demonstrates the complete chain: induce a firmware hang (e.g., by disabling interrupts), confirm the heartbeat stops, confirm the watchdog times out, and confirm the system resets into a safe state. The system-level test is the only one that truly verifies the risk control as an integrated function.

Finally, I'd document the traceability in the risk management file with a note explaining the architecture — that the control is intentionally split across two subsystems and that the system-level verification is the authoritative evidence. This prevents future auditors or engineers from assuming either subsystem's verification alone is sufficient.

**Possible follow-ups:**
- What if the hardware team's watchdog requirement and the firmware team's heartbeat requirement have different timing parameters (e.g., the watchdog timeout is 200ms but the heartbeat period is 100ms)? How would you verify the timing margin is adequate?
- How would you handle a situation where the firmware team's heartbeat requirement is written as "the system shall toggle the watchdog output at least once per second," but the hardware watchdog timeout is only 500ms?

---

## Q2: How would you approach determining whether a requirement in the SRS is truly a "safety requirement" derived from risk management, versus a "performance requirement" that exists for functional reasons, and how would you decide which traceability links are necessary for each type?

**Answer:** The distinction matters because safety requirements demand a different level of rigor in traceability and verification. My approach starts with a simple test: if the requirement were not met, would a patient, user, or operator be exposed to an unacceptable risk of harm? If yes, it's a safety requirement. If the consequence is degraded performance, reduced functionality, or user inconvenience — but no harm — it's a performance requirement.

In practice, I'd look at the origin of the requirement. Safety requirements typically trace back to a specific hazard identified in the risk analysis and a specific risk control measure. They often have language like "shall not," "shall prevent," "shall detect," or "shall limit" — they're about constraining behavior to avoid harm. Performance requirements usually trace back to user needs, marketing requirements, or system architecture decisions. They describe what the system should do, not what it must avoid doing.

That said, there's a gray zone. Some requirements serve dual purposes — for example, a requirement that a motor shall not exceed a certain speed might be both a performance limit (to achieve the clinical effect) and a safety limit (to prevent tissue damage). In that case, I'd treat it as a safety requirement for traceability purposes, because the safety consequence is the more severe outcome if it's not met.

For traceability, safety requirements need the full chain: hazard → risk control measure → safety requirement → design element → verification activity. They also need bidirectional traceability — you should be able to start from any hazard and find its controls, and from any safety requirement and find its originating hazard. Performance requirements need a lighter chain: source (user need, regulatory requirement, etc.) → requirement → verification. They don't need to link to the risk management file.

I'd also flag that the distinction should be made deliberately and documented. In practice, I'd review the SRS with the risk management team and mark each requirement as safety-related or not, with a rationale. This prevents scope creep where everything becomes a safety requirement (which creates excessive overhead) or the opposite problem where genuine safety requirements are treated as ordinary performance requirements (which creates regulatory risk).

**Possible follow-ups:**
- What if a requirement is safety-related in one operating mode but not in another? How would you handle the classification?
- How would you handle a requirement that was originally written as a performance requirement but is later discovered to have safety implications during the risk analysis?

---

## Q3: How would you approach creating a traceability scheme that captures the evolution of risk control measures and their associated requirements across multiple design iterations, given that both the risk analysis and the requirements specification are living documents?

**Answer:** The key insight is that traceability isn't a snapshot — it's a history. If you only capture the current state, you lose the ability to answer questions like "why did this requirement change?" or "was this risk control measure always implemented this way?" which are exactly the questions auditors and regulators will ask.

My approach would be to treat traceability links as versioned entities, not static connections. Each link gets metadata: when it was created, when it was modified, what changed, and why. This doesn't require a sophisticated tool — even a well-structured spreadsheet or a simple database can handle it — but it does require discipline in how changes are recorded.

Practically, I'd establish a change control process that works like this: when a risk control measure changes (say, the watchdog timeout is reduced from 200ms to 100ms), the change is logged in the risk management file with a rationale. The traceability link from that risk control to its system requirement is updated, and the link itself is versioned — the old link remains visible with an "effective until" date. The system requirement may or may not change (if it says "shall reset within 250ms," the requirement doesn't need to change even though the implementation did). If the requirement does change, that's another versioned link.

The same applies to requirements that change for non-risk reasons — a performance requirement might be relaxed because the user need changed. In that case, I'd check whether any risk control measures trace to that requirement. If they do, the change triggers a risk review: does the relaxed requirement still satisfy the risk control's intent? If not, the risk analysis needs updating.

For the traceability matrix itself, I'd maintain a "current state" view for day-to-day work, plus an audit trail of changes. The current state shows what's active now; the audit trail shows how we got here. Both are needed — the current state for engineering decisions, the audit trail for regulatory submissions and post-market reviews.

One practical technique I'd use is to include a "change history" tab or section in the traceability matrix itself, rather than relying on separate change logs. This keeps the history co-located with the links, making it easier to review the evolution of a particular requirement-to-risk-control path without jumping between documents.

**Possible follow-ups:**
- How would you handle a situation where a design iteration invalidates a previously verified risk control — for example, a component change that affects the timing of a hardware watchdog?
- What level of detail would you require in the change rationale to make the audit trail useful for a regulatory submission?

---

## Q4: How would you approach verifying that a risk control measure implemented as a firmware-based state machine — for example, preventing transition from "standby" to "active" unless all sensor self-tests pass — is correctly traced through to the system-level hazard it mitigates, and that the verification test adequately covers the failure scenario?

**Answer:** Let me break this into the two parts: traceability and verification adequacy.

For traceability, I'd start from the hazard — say, the device delivers therapy while a sensor is malfunctioning, leading to incorrect treatment. The risk control is the state machine guard that prevents activation unless self-tests pass. The chain should be: hazard → risk control measure → system requirement (e.g., "the system shall not transition from standby to active unless all critical sensor self-tests have passed within the current power-on session") → firmware requirement (the state machine behavior) → verification activity.

The critical thing here is that the system requirement must capture the *safety intent*, not just the implementation. If the firmware requirement says "the state machine shall not transition from STANDBY to ACTIVE if the self_test_complete flag is not set," that's an implementation detail. The system requirement should say something like "the system shall prevent therapy delivery if any critical sensor has not passed its self-test." This ensures that if the implementation changes (say, from a state machine to a different architecture), the safety intent is preserved and traceable.

For verification adequacy, I'd look at whether the test actually exercises the failure scenario the control is meant to mitigate. A test that puts the system in standby, runs the self-tests, confirms they pass, and then confirms the system transitions to active — that verifies the happy path but not the safety function. The meaningful test is: put the system in standby, *inject a sensor fault* so the self-test fails, and confirm the system *does not* transition to active. Even better, I'd test the boundary — what happens if one sensor passes and another fails? What if a sensor fails intermittently during the self-test sequence?

I'd also consider whether the test needs to run on target hardware or can run on a host. For a state machine guard, the logic itself might be testable on a host, but the sensor interface — the actual reading of the self-test result — depends on hardware. So I'd typically want at least one test on target hardware that injects a real fault (e.g., disconnecting a sensor or forcing an out-of-range reading) and confirms the guard engages. Host-based tests can cover the state machine logic broadly, but the hardware-in-the-loop test proves the integration.

Finally, I'd check that the verification record explicitly states which failure scenario was tested and how it maps to the hazard. The test report should say "this test verifies that the system prevents therapy delivery when the pressure sensor self-test fails, mitigating the hazard of incorrect therapy due to sensor malfunction" — not just "state machine transition test passed."

**Possible follow-ups:**
- How would you handle a situation where the self-test itself can fail in multiple ways (sensor not connected, sensor out of range, sensor communication error), and each failure mode needs different handling?
- What if the state machine guard is implemented across multiple firmware modules — how would you ensure the traceability captures the complete implementation?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a comprehensive traceability matrix linking every requirement to a risk control measure and a verification test. However, during a design review, the test lead points out that several verification tests are testing the wrong thing — for example, a test labeled "verifies overcurrent protection" is actually testing nominal current draw. The systems engineer insists the traceability matrix is correct because the requirement numbers match. How would you resolve this disagreement?

**Answer:** This is a situation where both people are partially right, and the resolution requires separating the two issues: the traceability matrix's internal consistency and the actual validity of the verification evidence.

First, I'd acknowledge the systems engineer's point — if the requirement numbers match, the matrix is internally consistent. The requirement for overcurrent protection is linked to a test, and the test is linked back to the requirement. That's structurally correct. But I'd also validate the test lead's concern — a traceability matrix is only as good as the evidence it connects. If the test doesn't actually stress the failure condition, then the verification is meaningless, regardless of whether the links are correct.

My approach would be to call a meeting with both engineers and walk through the specific test in question. I'd ask the test lead to explain what the test procedure actually does — what stimulus is applied, what's measured, what pass/fail criteria are used. Then I'd ask the systems engineer to read the requirement aloud. In most cases, the discrepancy becomes obvious: the requirement says "the system shall limit current to 2A under fault conditions," but the test procedure says "apply nominal load and measure current draw." The test verifies normal operation, not the fault response.

Once the gap is clear, I'd frame the issue not as "who's right" but as "what evidence do we need to close this gap?" The options are: modify the test to actually inject a fault (e.g., short the output and measure the current limit), or — if the test was intentionally designed as a nominal-condition check — add a separate fault-injection test. I'd also ask whether the requirement itself is clear about what "fault conditions" means — if it's ambiguous, that's a requirements issue that needs fixing, not just a test issue.

I'd also use this as a prompt to review other tests in the matrix with the same scrutiny. If one test is testing the wrong thing, others might be too. I'd propose a systematic review where the test lead and systems engineer go through each test together, confirming that the test procedure actually exercises the requirement's acceptance criteria. This turns a point of conflict into a collaborative quality improvement exercise.

Finally, I'd document the outcome — what was wrong, what was changed, and what process improvement prevents this from recurring. The process improvement might be a checklist for test development: before a test is approved, the test lead must confirm that the test procedure includes a step that stresses the failure condition, not just nominal operation. This ensures the traceability matrix links to *meaningful* verification, not just *existing* verification.

**Possible follow-ups:**
- What if the test lead discovers that *many* tests are testing the wrong thing, and fixing them would require significant schedule extension? How would you prioritize which tests to fix first?
- How would you handle a situation where the systems engineer argues that the test, while not directly stressing the fault condition, provides sufficient confidence because the design has been analyzed and the fault condition is "obviously" handled?