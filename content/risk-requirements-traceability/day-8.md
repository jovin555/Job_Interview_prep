# risk-requirements-traceability — Day 8

## Q1: How would you approach establishing traceability between risk control measures and requirements when the same risk control measure is implemented differently across multiple product variants or hardware revisions?

**Answer:** This is a common challenge in medical device families or platforms that evolve over time. I would approach it by separating the *intent* of the risk control measure from its *implementation* at the traceability level.

First, I'd define the risk control measure at a functional level in the risk management file — for example, "the system shall detect and respond to an overcurrent condition on the motor drive output within 100ms." This functional statement remains stable across variants. Then, in the requirements specification, I'd create a parent requirement that captures this functional intent, with variant-specific child requirements that describe how it's implemented in each revision (e.g., "Rev A uses a hardware fuse; Rev B uses a firmware-controlled current sense with MOSFET cutoff").

The traceability matrix would link the risk control measure to the parent requirement, and then each variant-specific child requirement would trace to its own verification activity. This way, when a new variant is introduced, you only need to add the implementation-specific requirements and verification, without re-tracing the entire risk control chain.

For the verification side, I'd maintain a separate column in the traceability matrix indicating which product variants each verification test applies to. This prevents the common problem of a test passing on one hardware revision but not being run on another, while still maintaining clear traceability from hazard through to verified control.

**Possible follow-ups:**
- How would you handle the situation where a risk control measure is removed entirely in a later hardware revision because a different design approach eliminates the hazard?
- What if the verification method differs between variants — one uses automated test equipment, another uses manual inspection?

---

## Q2: During a design verification campaign, you discover that a risk control requirement was verified using a benchtop prototype, but the risk management file specifies that verification must be performed on production-representative units. How would you address this discrepancy?

**Answer:** This is a serious gap because it undermines the validity of the risk control verification. I would treat it as a non-conformance that needs formal resolution through the design change process.

First, I'd document the discrepancy clearly: what was verified, on what hardware, against what criteria, and what the risk management file actually requires. Then I'd assess the technical impact — is the benchtop prototype electrically and mechanically representative enough that the test results are still valid? For example, if the risk control involves a timing threshold that depends on parasitic capacitance, a benchtop prototype with different PCB layout or component tolerances might not demonstrate the same behavior as production hardware.

If the prototype is sufficiently representative, I'd document a rationale for accepting the existing test results, including a technical justification and a risk assessment. This would be reviewed and approved through the design review process. If it's not representative, I'd initiate a corrective action to perform the verification on production-representative hardware, which might mean building additional units or waiting for the next production batch.

In either case, I'd also review whether other risk control verifications were performed on the same prototype to identify if this is an isolated issue or a systemic problem with the verification planning. The root cause might be that the verification team didn't have clear guidance on what constitutes "production-representative" hardware, which would point to a need to improve the verification plan template.

**Possible follow-ups:**
- What if the production-representative hardware won't be available until after the regulatory submission deadline?
- How would you distinguish between a prototype that is "representative enough" versus one that isn't, for verification purposes?

---

## Q3: How would you approach creating a traceability scheme that connects risk control measures implemented in firmware (e.g., software-based timeouts, plausibility checks, state machine guards) back to system-level hazards, given that firmware requirements often change more frequently than hardware requirements during development?

**Answer:** Firmware's iterative nature requires a traceability approach that accommodates change without becoming a maintenance burden. I would use a layered traceability model with different levels of granularity.

At the top level, I'd trace system-level hazards to firmware *functional* requirements — for example, "the firmware shall implement a plausibility check on pressure sensor readings before enabling the motor." This functional requirement is relatively stable because it's derived from the risk analysis, not from the implementation details.

Below that, I'd trace the functional requirement to firmware *design* requirements that describe the specific implementation approach — e.g., "the plausibility check shall compare the current reading against the previous reading, and reject changes greater than 20% per 10ms window." These design requirements may change as the algorithm is refined, but they still trace upward to the same functional requirement.

At the lowest level, I'd use a version-controlled traceability matrix that captures the link between design requirements and specific code modules or test cases. This matrix would be updated as part of the firmware change control process — every time a firmware requirement changes, the traceability impact is assessed and the matrix is updated.

To manage the frequency of changes, I'd use a tool that supports automated traceability updates (like a requirements management tool with API integration to the issue tracker), so that when a firmware requirement is modified, the traceability links are flagged for review rather than requiring manual re-entry. I'd also schedule periodic traceability audits — perhaps at each firmware release milestone — to verify that the traceability remains complete and accurate.

**Possible follow-ups:**
- How would you handle the situation where a firmware risk control is implemented across multiple source files or modules, and a change in one module breaks the traceability chain?
- What level of detail would you require in firmware requirements to make traceability meaningful without being overly prescriptive?

---

## Q4: (Behavioral) Imagine you're leading a project where the systems engineer has created a comprehensive requirements traceability matrix linking every requirement to a risk control measure and a verification test. However, during a design review, the test lead points out that several verification tests are testing the wrong thing — for example, a test labeled "verifies overcurrent protection" is actually testing nominal current draw. The systems engineer insists the traceability matrix is correct because the requirement numbers match. How would you resolve this disagreement?

**Answer:** This is a situation where process compliance has been mistaken for technical correctness — the traceability matrix is internally consistent but doesn't reflect reality. I'd approach it by separating the process issue from the technical issue.

First, I'd acknowledge that the systems engineer is correct that the traceability matrix is formally complete — the requirement numbers link to test case numbers. But I'd reframe the discussion around the *purpose* of traceability: it's not just about having links, but about demonstrating that each risk control measure is adequately verified. A link that connects a requirement to a test that doesn't actually exercise the risk control is a false sense of security.

I'd propose a joint review session with the systems engineer and test lead, going through each discrepancy case by case. For each one, we'd ask: "Does this test actually stress the failure scenario identified in the risk analysis?" If not, we'd document the gap and determine what needs to change — either the test needs to be revised, or the traceability link needs to be corrected.

To prevent this in the future, I'd suggest adding a peer review step for the traceability matrix before verification begins, where a technical reviewer (not just a process reviewer) checks that each test method actually matches the risk control intent. I'd also recommend that the test procedures include a brief rationale statement explaining how the test conditions relate to the failure scenario — for example, "this test injects a 5A load to simulate a motor stall condition, verifying that the overcurrent protection trips within 100ms."

The key is to maintain respect for both perspectives: the systems engineer's focus on process completeness and the test lead's focus on technical validity. Both are necessary for a robust traceability system.

**Possible follow-ups:**
- What if the test lead's assessment is based on a misunderstanding of the requirement, and the test is actually correct?
- How would you handle the schedule impact of revising multiple tests that were found to be incorrect during this review?

---

## Q5: How would you approach verifying that a risk control measure implemented as a firmware-based state machine (e.g., preventing transition from "standby" to "active" unless all sensor self-tests pass) is correctly traced through to the system-level hazard it mitigates, and that the verification test adequately covers the failure scenario?

**Answer:** This type of risk control is particularly challenging because it involves temporal logic and state-dependent behavior that a single pass/fail test may not fully exercise. I would approach verification in layers.

First, at the traceability level, I'd ensure the risk management file clearly documents the hazard (e.g., "device activates therapy without valid sensor data, causing patient harm"), the risk control measure ("firmware state machine shall prevent transition to active state unless all sensor self-tests pass"), and the expected behavior under fault conditions. The SRS would contain a requirement like "the device shall not enter the active state if any sensor self-test has failed since the last power-on reset."

For verification, a single test that checks "device enters active state when all self-tests pass" is insufficient — it only tests the nominal case. The verification plan needs to include multiple test cases that cover the failure scenarios:

1. **Fault injection at startup:** Force a sensor self-test to fail and verify the state machine remains in standby.
2. **Fault during operation:** If the state machine allows transitions from active back to standby, verify that a self-test failure during active mode triggers a transition to a safe state.
3. **Transient fault recovery:** Verify that a self-test that fails then passes on retry does not cause unexpected state transitions.
4. **Boundary conditions:** Test the timing — what happens if a self-test completes just as the transition command is received?

I'd also include a structural coverage analysis of the state machine implementation — for example, verifying that every state transition that should be guarded by the self-test check actually has that guard in the code. This can be done through code review or static analysis tools.

For the traceability matrix, I'd link the risk control measure to the parent requirement, then to each individual test case. The matrix should show that the combination of test cases covers both the nominal and fault scenarios. If any failure scenario from the risk analysis doesn't have a corresponding test case, that's a traceability gap that needs to be addressed.

**Possible follow-ups:**
- How would you handle the situation where the state machine has dozens of states and transitions, and exhaustive testing is impractical?
- What role would design documentation (e.g., state machine diagrams) play in establishing traceability for this type of risk control?