# risk-requirements-traceability — Day 17

## Q1: How would you approach handling a situation where a risk control measure is traced to a verification test, but the test was written to verify a *different* requirement and only incidentally exercises the risk control under nominal conditions — so it passes, but it never actually stresses the failure condition the control is meant to mitigate?

**Answer:** This is a classic traceability integrity problem — the link exists on paper, but the evidence doesn't actually demonstrate the control works under the conditions that matter. My approach would be to first confirm the gap objectively: review the test procedure step-by-step against the risk control's failure condition, and document specifically where the test diverges from what the risk analysis requires. The key question is whether the test stimulates the fault condition the control is designed to mitigate, or whether it merely observes the system operating normally.

Once confirmed, I'd treat this as a traceability gap and raise it formally — through a design review or a discrepancy report, depending on the project's quality system. The fix isn't just to relabel the link; it's to either modify the existing test to include the fault injection, or create a new test specifically for the risk control. I'd also look at whether other risk controls have similar "incidental coverage" links, because if one slipped through, others might have too. A systematic audit of all risk-control-to-test links would be warranted, focusing on whether each test actually stimulates the failure condition, not just whether the requirement numbers match.

**Possible follow-ups:**
- How would you distinguish between a test that provides *partial* coverage of a risk control versus one that provides *no* meaningful coverage?
- If the test engineer argues that the nominal-condition test is "good enough" because the control is designed with margin, how would you respond?

---

## Q2: How would you approach establishing traceability for risk control measures that are implemented through a combination of hardware and firmware, where the hardware team documents the control in their design specification and the firmware team documents their portion in a software requirements document — but neither document references the other, and the risk management file treats the control as a single integrated measure?

**Answer:** The core issue is that a single risk control has been fragmented across two documentation domains, and the traceability needs to reflect both the decomposition and the integration. I'd start by mapping the control's complete chain: the hazard, the risk control measure as described in the risk management file, the hardware portion (e.g., a sensor or comparator), the firmware portion (e.g., the decision logic and actuation), and the verification activities for each portion.

The key principle is that the risk management file should describe the control at the *system level* — what it does and what hazard it mitigates — while the hardware and firmware documents describe their respective *implementations*. The traceability matrix needs to show three types of links: (1) hazard-to-system-level-control, (2) system-level-control-to-hardware-implementation and system-level-control-to-firmware-implementation, and (3) each implementation-to-its-verification activity. Additionally, there needs to be a link showing that the *combination* of hardware and firmware is verified together at the system level, because neither subsystem test alone proves the integrated control works.

To make this work in practice, I'd introduce a shared identifier for the risk control that both teams reference — for example, a risk control ID from the risk management file that appears in both the hardware and firmware documents. This creates the cross-reference that's currently missing. I'd also ensure the system-level verification test is explicitly traced to the risk control ID, so the integrated behavior is covered. The goal is to make the traceability reflect the architecture: the control is one logical entity, implemented by two physical/logical components, verified both at the component level and at the integration level.

**Possible follow-ups:**
- How would you handle the situation where the hardware and firmware teams use different numbering schemes for their requirements?
- What would you do if the system-level integration test for the combined control is scheduled late in the program, and a component-level test failure occurs early — how would you assess the impact?

---

## Q3: How would you approach determining whether a risk control measure that is implemented as a hardware-based analog comparator with a firmware response — for example, the comparator detects an over-voltage condition and asserts an interrupt, and the firmware responds by disabling a power output — should be verified as a complete system, or whether separate hardware and firmware verification is sufficient?

**Answer:** The answer depends on the nature of the failure modes and the interaction between the two portions. The hardware comparator has its own failure modes — it could fail to trip at the correct threshold, drift with temperature, or have a slow response time. The firmware has its own failure modes — it could miss the interrupt, take too long to respond, or fail to disable the output. Separate verification is appropriate for the *individual* failure modes: the hardware test should verify the comparator trips at the specified threshold across the operating temperature range, and the firmware test should verify the interrupt handler disables the output within the specified time.

However, separate verification is *not* sufficient for the *integrated* behavior. There are failure modes that only appear when the two portions interact — for example, the comparator's output might have a rise time that the firmware's interrupt controller doesn't reliably detect, or the firmware might be delayed by other interrupt handlers running at higher priority. These interaction failures can only be caught by a system-level test that exercises the full chain: apply an over-voltage stimulus, let the comparator trip, let the firmware respond, and measure the time from stimulus to output-disable.

My approach would be to require both levels of verification. The component-level tests provide diagnostic granularity — if the system test fails, you need to know whether the comparator or the firmware is at fault. The system-level test provides the objective evidence that the integrated control actually works. I'd also consider whether the risk analysis specifies a response time or other timing requirement for the complete chain; if it does, that requirement can only be verified at the system level.

**Possible follow-ups:**
- How would you handle the situation where the system-level test passes, but the component-level tests reveal a marginal margin in the comparator's trip point — would you accept the system-level result as sufficient?
- What if the firmware response includes a delay that is acceptable at the system level but makes the component-level firmware test difficult to write — how would you structure the verification?

---

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has multiple operating modes — for example, normal mode, standby mode, and fault mode — and a single risk control measure behaves differently in each mode?

**Answer:** The key insight is that a risk control measure that behaves differently across operating modes is effectively *multiple controls* from a verification perspective, even if it's a single physical implementation. The traceability scheme needs to capture the mode-dependent behavior explicitly, or you'll end up with a verification test that covers one mode and falsely claims coverage for all.

My approach would be to decompose the risk control measure by operating mode. For each mode, I'd document: (1) what the control does in that mode, (2) what the hazard scenario is in that mode, and (3) what the verification activity is for that mode-specific behavior. The traceability matrix would have one row per mode-control combination, rather than one row for the control as a whole. This makes gaps visible — if the control is only verified in normal mode, the matrix immediately shows missing rows for standby and fault modes.

I'd also consider whether the mode transitions themselves need to be traced. For example, if the control is supposed to activate when transitioning from normal to fault mode, the transition behavior is a distinct requirement that needs its own verification. The traceability scheme should capture not just the steady-state behavior in each mode, but the behavior during transitions between modes.

Finally, I'd ensure the risk management file explicitly identifies which modes are relevant to each hazard and control. If the risk analysis doesn't mention modes, that's a gap in the risk analysis itself — the traceability scheme can't compensate for a risk analysis that hasn't considered mode-dependent behavior.

**Possible follow-ups:**
- How would you handle a situation where the risk analysis identifies a hazard that only exists in fault mode, but the verification plan only tests the control in normal mode?
- How would you represent mode-dependent behavior in a traceability matrix without making the matrix so complex that it becomes unusable?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that several of the verification activities are actually "verification by analysis" — for example, a worst-case timing analysis or a thermal derating calculation — rather than physical tests. The quality manager argues that analysis is not objective evidence and demands physical testing for all risk controls. The systems engineer argues that some controls, like timing margins or thermal derating, can only be practically verified by analysis, and that physical testing would be impractical or impossible. How would you resolve this disagreement?

**Answer:** I'd start by separating the two issues that are being conflated: whether analysis *can* be objective evidence, and whether a *specific* analysis is adequate for a *specific* risk control. The quality manager is right that analysis can be misused — a calculation that isn't validated, or that uses assumptions that don't match the real system, is not objective evidence. But the systems engineer is also right that some controls are inherently analytical — you can't physically test a worst-case timing margin without creating the exact worst-case conditions, which may be impossible or impractical.

My approach would be to establish criteria for when analysis is acceptable. First, the analysis must be based on validated models or calculations — for example, a timing analysis that uses measured propagation delays from the actual components, not just datasheet typical values. Second, the analysis must include conservative assumptions — if there's uncertainty, the analysis should err on the side of predicting failure, not success. Third, the analysis should be independently reviewed — ideally by someone who didn't perform the original calculation. Fourth, where feasible, the analysis should be correlated with at least one physical test to validate the model — for example, measure the actual timing on a representative unit and compare it to the analysis.

I'd also look at the specific risk controls in question. For a thermal derating calculation, the analysis might be perfectly adequate if the component's power dissipation is well-understood and the thermal model has been validated. For a worst-case timing analysis, the analysis might be adequate for the *design margin* but not for the *functional behavior* — you might still need a physical test to verify the system actually works under nominal conditions, with the analysis covering the worst-case extrapolation.

In practice, I'd convene a meeting with the quality manager, the systems engineer, and the relevant technical experts to go through each disputed control one by one. For each, we'd ask: What is the failure mode? Can it be physically tested? If not, what analysis is proposed, and is it adequate? The outcome would be a documented decision for each control — either physical test, analysis with defined criteria, or a combination. The key is to move from a binary "analysis vs. test" argument to a risk-based discussion about what evidence is sufficient for each specific control.

**Possible follow-ups:**
- How would you handle a situation where the quality manager agrees to accept analysis, but only if it's performed by an external consultant — and the budget doesn't allow for that?
- What would you do if the analysis reveals a marginal result — for example, the timing margin is positive but only by a small amount — and the systems engineer argues it's still acceptable?