# risk-requirements-traceability — Day 64

## Q1: How would you approach tracing a risk control measure that is implemented as a firmware-based watchdog kick — where the firmware must periodically write to a hardware register to prove liveness — when the firmware team owns the kick logic and the hardware team owns the watchdog peripheral, and neither team's requirements document references the other?

**Answer:** The core problem is that the control is a *contract between two subsystems*, and neither subsystem's document captures the contract — each captures only its half. The watchdog only works if the kick timing, the timeout window, and the reset behavior are jointly correct, so a traceability scheme that stops at the subsystem boundary can show full coverage while the integrated behavior is unverified.

My approach would be to introduce an explicit interface-level requirement that owns the contract, and trace both halves to it. Concretely:

- Define a system-level (or ICD-level) requirement stating the safety intent: "The system shall detect loss of firmware liveness within [bounded time] and transition to [safe state]." This is the requirement the hazard traces to.
- Under it, derive two child requirements: a hardware requirement for the watchdog peripheral (timeout window, reset source, clock independence, behavior on reset) and a firmware requirement for the kick logic (kick period, kick condition, what must be true before kicking, behavior if the kick cannot be performed). Both children trace *up* to the interface requirement and *across* to each other via the ICD.
- The verification activity then has to be an integrated test, not two unit tests. A hardware-only test of the peripheral and a firmware-only test of the kick routine can both pass while the integrated system fails — for example, if the firmware kicks from an interrupt that the watchdog reset also disables, or if the kick period is nominally inside the window but drifts outside it under worst-case clock tolerance or interrupt latency.

The key insight I'd emphasize: for a watchdog specifically, the failure mode you care about is *loss of liveness*, which is an emergent property. You cannot verify it by inspecting either half. So the traceability matrix needs a row that says "this control is verified by an integrated test that deliberately stops the kick and confirms the reset occurs within the specified window."

I'd also flag the clock-independence question early, because it's a classic gap: if the watchdog is clocked from the same source as the firmware, a clock failure defeats both. That's a design property that should be captured as a requirement and verified, not left implicit.

**Possible follow-ups:**
- If the firmware team argues that the kick logic is "trivially correct" and doesn't need a formal requirement, how would you justify documenting it?
- How would you verify the watchdog's behavior under worst-case interrupt latency without instrumenting the production firmware?

## Q2: How would you approach establishing traceability for a risk control measure that is implemented as a redundant channel — for example, a primary sensor path and an independent secondary path whose agreement is checked — where the control's effectiveness depends on the *independence* of the two channels rather than on either channel alone?

**Answer:** This is a case where the traceability matrix can look perfectly complete and still miss the thing that actually matters. If you trace "primary sensor requirement → primary sensor test" and "secondary sensor requirement → secondary sensor test," you've verified that each channel works. You have *not* verified that the control works, because the control's whole value is that the two channels fail independently. Two channels that share a power rail, a clock, a ground reference, or a common-mode failure mode are not redundant in any meaningful sense — they're one channel with extra parts.

So the traceability scheme needs a requirement that captures the *independence property itself*, and that requirement needs its own verification activity. Something like: "The primary and secondary sensor paths shall not share a common failure mode that can cause both to report the same erroneous value." That's a design requirement with a safety intent, and it traces to the hazard.

Verification of that requirement is typically a mix of methods, which is where it gets interesting:

- **Analysis** — a common-cause failure analysis or a dependency review of the two paths (shared supplies, shared references, shared communication buses, shared firmware modules). This is legitimate objective evidence for an independence claim, provided the analysis method and criteria are defined.
- **Inspection** — schematic and layout review to confirm physical separation, separate regulators, separate ADC channels, etc.
- **Test** — fault injection: force one channel to a known-bad value and confirm the disagreement is detected and the system responds correctly. This is the test that actually exercises the control.

The traceability matrix should show the independence requirement linked to *all three* verification activities, not just the functional test. A common audit finding is that the matrix shows the control traced to a single "redundancy test" that only checks nominal agreement — which proves nothing about independence.

I'd also want the agreement-check logic itself traced separately, because that's a third element: the comparator that decides "these two readings disagree" has its own thresholds and its own failure modes (too loose a threshold misses real faults; too tight a threshold causes false trips). That's a distinct requirement from the independence of the channels.

**Possible follow-ups:**
- If the two channels share a firmware module, does that break independence? How would you decide?
- How would you verify the agreement-check threshold without knowing the exact failure distribution of the sensors?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity's test procedure was written against an earlier revision of the requirement, so the test still passes but no longer exercises the current acceptance criteria?

**Answer:** This is a configuration-management failure that masquerades as a traceability success. The matrix shows a link, the test passes, and the audit is clean — but the link is stale. The requirement changed, the test didn't, and nobody noticed because the traceability tool only checks that a link *exists*, not that the linked artifacts are consistent.

The first thing I'd do is establish how widespread it is. A single stale test is a fix; a pattern of stale tests suggests the change-control process isn't propagating requirement revisions into the verification plan. I'd pull the revision history of the requirement and the test procedure and compare dates, then check whether other requirements in the same subsystem have the same problem.

For the specific case, the resolution is straightforward in principle: the test procedure needs to be revised to match the current acceptance criteria, and then re-run to confirm the control still passes under the *current* criteria. The important part is not to assume the old pass carries over — the requirement changed for a reason, and the new criteria may be stricter or may exercise a different condition. A test that passed against the old criteria tells you nothing about the new ones.

The deeper fix is process. A few things I'd want in place:

- Requirement revisions should trigger a review of linked verification activities, not just a notification. The traceability tool should be able to flag "this requirement changed since the linked test was last revised."
- Test procedures should reference the requirement by revision, not just by ID, so a mismatch is visible.
- The verification plan should be treated as a living document that's reviewed alongside the SRS at each design review, not frozen after the first release.

I'd also want to check whether the requirement change was itself properly assessed for risk impact. If the acceptance criterion changed, someone should have asked whether the change affects the risk control's effectiveness — and if it does, whether the residual risk evaluation still holds.

**Possible follow-ups:**
- How would you catch this kind of staleness in a traceability tool that only tracks links, not revisions?
- If the requirement change was a relaxation of the acceptance criterion, does that change your approach?

## Q4: How would you approach deciding whether a risk control measure should be traced to a design requirement, a design element, or both — and what practical difference does that distinction make in a traceability matrix?

**Answer:** The distinction matters because requirements and design elements answer different questions, and a traceability matrix that conflates them can pass audit while leaving real gaps.

A **design requirement** is a statement of what the system must do or be — it's the "shall" statement. A **design element** is the thing that implements it — a circuit block, a firmware module, a mechanical feature, a component. The relationship is that a requirement is satisfied *by* one or more design elements, and a design element may satisfy one or more requirements.

For risk control measures, I'd generally want both links, but for different purposes:

- **Requirement link** — proves the control has been captured as something the design is obligated to do, with measurable acceptance criteria. This is what verification traces against. Without it, the control exists only in the risk file and there's nothing to verify.
- **Design element link** — proves the control has actually been implemented somewhere in the design, and lets you do impact analysis when that element changes. If a firmware module is refactored, you want to know which risk controls depend on it.

The practical difference shows up in two scenarios:

1. **Impact analysis.** If a design element changes, the design-element link tells you which requirements (and therefore which risk controls) may be affected. If you only have requirement links, you have to reason about it manually.
2. **Gap detection.** If a risk control traces to a requirement but not to any design element, the requirement may be unimplemented — a real gap. If it traces to a design element but not to a requirement, the control may be implemented but not verifiable — also a gap, and a common one for controls that "just exist" in the design without ever being written down as a requirement.

For controls implemented through design margins or derating — component selection, creepage distances, thermal margins — the design-element link is often the *primary* one, because there may not be a clean functional requirement. In those cases I'd still want a requirement, but it may be phrased as a design constraint ("the isolation barrier shall maintain [X] mm creepage under [Y] pollution degree") rather than a functional behavior. That gives verification something to trace against, even if the verification method is inspection or analysis rather than test.

The rule of thumb I'd use: every risk control needs at least one requirement (so it's verifiable) and at least one design element (so it's implemented and impact-analyzable). If either is missing, that's a finding.

**Possible follow-ups:**
- For a control implemented purely through component derating, what would the requirement look like, and how would you verify it?
- How would you handle a design element that implements multiple risk controls — does that create any traceability problems?

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has built a traceability matrix that links every risk control measure to a verification activity, and the matrix is complete and passes audit. However, a test engineer privately tells you that several of the linked tests were written by copying a similar test from a previous project and adjusting the labels, and that nobody has confirmed the tests actually exercise the failure conditions in this project's risk analysis. The systems engineer argues the matrix is compliant and the tests pass, so there's no problem. How would you handle this?

**Answer:** The systems engineer is technically correct that the matrix is compliant, and that's exactly the problem — the matrix is measuring the wrong thing. A traceability matrix proves that links *exist*; it does not prove that the linked verification actually verifies the control. If the tests were copied from a previous project and relabeled, the links are real but the evidence is not. This is the kind of finding that passes an audit and fails in the field, so I'd treat it as serious rather than as a documentation nitpick.

My approach would be to separate the two issues and address them in order:

**First, establish the facts.** I'd ask the test engineer to identify specifically which tests are affected and what the mismatch is — is it that the test doesn't exercise the fault condition at all, or that it exercises a different fault condition, or that it exercises the right condition but under nominal rather than worst-case parameters? The severity of the response depends on which. I'd also want to know whether this is a one-off or a pattern, because if several tests were copied, the whole verification campaign may need re-examination.

**Second, decide the disposition.** For each affected test, the question is whether the existing test can be shown to actually verify the control (in which case it may just need a documented rationale and possibly a revision to make the coverage explicit), or whether it genuinely doesn't exercise the failure condition (in which case it needs to be rewritten and re-run). I would not accept "the test passes" as evidence — a test that doesn't exercise the failure condition passing tells you nothing about whether the control works.

**Third, address the process gap.** The root cause is that verification tests were treated as reusable artifacts without a check that they map to *this* project's risk analysis. The fix is a review step: before a test is accepted as verification evidence for a risk control, someone with knowledge of the risk analysis confirms that the test's stimulus and acceptance criteria actually correspond to the failure condition being mitigated. That review should be part of the verification plan approval, not an afterthought.

On the disagreement with the systems engineer: I'd frame it not as "the matrix is wrong" but as "the matrix is necessary but not sufficient." The matrix is doing its job — it's showing where evidence *should* be. The question is whether the evidence at those links is valid. That reframing usually gets a systems engineer on board, because it's not asking them to defend the matrix; it's asking them to help validate the evidence the matrix points to.

I'd also loop in quality early, because if the finding is confirmed, it likely needs to be documented as a corrective action, and the verification campaign may need to be re-opened. Better to surface that deliberately than to have it discovered later.

**Possible follow-ups:**
- If the affected tests are for low-severity risks, would you still require them to be rewritten, or would you accept a documented rationale?
- How would you prevent this from happening again without adding a heavy review burden to every test?