# risk-requirements-traceability — Day 54

## Q1: How would you approach tracing a risk control measure that is implemented as a hardware watchdog timer monitoring a firmware heartbeat, when the hardware and firmware teams each document their portions in separate specifications with no cross-references?

**Answer:** The core problem is that the control is a *loop*, not a component — the hardware timer is useless without the firmware servicing it, and the firmware heartbeat is meaningless without the hardware that resets the system when it stops. So the first step is to define the control at the system level as a single, named risk control measure with its own identifier in the risk management file, and to state its safety intent explicitly: "if the firmware stops executing its main loop, the system shall be reset within a bounded time." That system-level entry becomes the anchor that both subsystem documents point back to.

From there, I'd decompose the control into two verifiable sub-requirements — one hardware (the watchdog asserts reset within its timeout window when the heartbeat input is absent) and one firmware (the main loop toggles the heartbeat within a period comfortably shorter than the hardware timeout, under all operating modes). Each sub-requirement carries a reference to the parent risk control ID, so the traceability matrix shows the loop closing: hazard → risk control → hardware sub-requirement + firmware sub-requirement → verification activities for each. The critical part is that neither sub-requirement is considered verified in isolation for the *safety* claim; there must also be an integration-level verification that demonstrates the end-to-end behavior — heartbeat stops, reset occurs, system recovers to a safe state.

Practically, I'd push for a shared identifier convention so the two documents can be cross-referenced without renumbering either team's scheme, and I'd make the integration test the acceptance gate for the risk control, with the two subsystem tests treated as supporting evidence.

**Possible follow-ups:**
- How would you handle the case where the firmware heartbeat period is configurable at runtime — does that change how you trace and verify the control?
- If the hardware watchdog has a fixed timeout that can't be changed, how does that constrain the firmware requirement, and where would you document that constraint?

## Q2: How would you approach deciding whether a risk control measure should be traced to a design requirement, a design element, or both — and what practical difference does that distinction make in a traceability matrix?

**Answer:** The distinction matters because requirements and design elements answer different questions and are verified differently. A *requirement* is a statement of what the system must do or how well it must do it, with a measurable acceptance criterion — it's the thing you verify against. A *design element* is the specific implementation that satisfies the requirement — a circuit block, a firmware module, a mechanical feature. Tracing a risk control only to a design element tells you *where* the control lives but not *what it must achieve*, which makes verification ambiguous. Tracing it only to a requirement tells you *what must be achieved* but not *how*, which makes impact analysis weak when the design changes.

In practice, I'd trace risk controls to both, but with different roles. The risk control measure links to one or more design requirements that express its safety intent in measurable terms — those are what verification activities attach to. The same requirements then link down to the design elements that implement them, so a change to a design element can be walked back up to the risk control it supports. This gives bidirectional traceability: hazard → risk control → requirement → design element → verification, and the reverse path for change impact.

The practical payoff shows up during change control. If someone modifies a design element, the matrix immediately shows which requirements and which risk controls are affected. If the trace stopped at the design element, you'd have no measurable criterion to re-verify against; if it stopped at the requirement, you'd have no way to know which physical or software artifact to inspect when the requirement needs to change.

**Possible follow-ups:**
- For a risk control implemented purely through component derating, is there a meaningful "design requirement," or does the trace legitimately stop at the design element?
- How would you handle a single design element that implements multiple requirements, some safety-related and some not?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity's acceptance criterion is stated as "the control functions as designed" rather than as a measurable pass/fail threshold?

**Answer:** "Functions as designed" is not an acceptance criterion — it's a placeholder that defers the real decision to whoever runs the test, which means the test can't produce objective evidence and can't fail in a defensible way. The first move is to go back to the risk analysis and ask what the control is actually supposed to achieve: what failure condition does it mitigate, and what observable, measurable behavior demonstrates that mitigation? That question usually yields a concrete threshold — a trip point, a response time, a state transition, a bounded output — that can be written as a pass/fail criterion.

Once the criterion is defined, I'd check whether the existing test procedure actually exercises the failure condition or just the nominal path. A test that only confirms the control "works" under normal conditions doesn't demonstrate that it mitigates the hazard, because the hazard occurs under fault conditions. So the acceptance criterion needs to be paired with a test setup that injects or simulates the fault the control is meant to catch, and the pass/fail threshold needs to be tied to the risk analysis's tolerance for that fault.

If the criterion genuinely can't be reduced to a single measurable number — say, the control is a state machine guard with several transition conditions — then it should be decomposed into a set of measurable sub-criteria, each with its own pass/fail, rather than left as a vague statement. The traceability matrix entry should point to the specific criterion, not to the test procedure as a whole, so that a gap in one sub-criterion is visible.

**Possible follow-ups:**
- What would you do if the test engineer argues that a measurable threshold is impossible because the control's behavior is qualitative?
- How would you handle an acceptance criterion that is measurable but whose tolerance was never justified against the risk analysis?

## Q4: How would you approach creating a traceability scheme that captures the evolution of risk control measures and their associated requirements across multiple design iterations, given that both the risk analysis and the requirements specification are living documents?

**Answer:** The key insight is that traceability has to be versioned, not just linked. If the risk analysis and the SRS both change over time, a static matrix becomes a snapshot that's wrong the moment either document is revised. So the scheme needs to record not just "requirement X traces to risk control Y" but "requirement X revision 3 traces to risk control Y revision 2, and here's what changed and why."

Practically, I'd use unique, stable identifiers for risk controls and requirements that persist across revisions, with revision history captured separately. When a risk control is modified — say, its detection threshold is tightened — the change should trigger a review of every requirement and verification activity linked to it, and the matrix should show which links were re-validated and which are now stale. A link that hasn't been re-confirmed against the current revision should be flagged, not silently carried forward.

I'd also capture the *rationale* for changes, not just the change itself, because during an audit or a design review the question is usually "why did this control change, and did the change invalidate any verification?" A change log attached to the risk control, cross-referenced from the matrix, answers that. And I'd build in a periodic reconciliation step — a review checkpoint where the current revisions of the risk analysis and the SRS are compared against the matrix to catch drift before it becomes a compliance problem.

**Possible follow-ups:**
- How would you handle a situation where a requirement was deleted but its linked risk control still exists — does the risk control now have no requirement, and is that a gap?
- What tooling or process would you put in place to make stale links visible without requiring manual review of the entire matrix?

## Q5: (Behavioral) Imagine you're leading a project where the risk management team insists that every risk control measure must be traced to a *single* verification activity, arguing that multiple links per control make the matrix unreadable and hard to audit. The test lead argues that several controls genuinely require multiple verification activities — for example, a control verified partly by analysis and partly by test. How would you resolve this disagreement?

**Answer:** Both positions have a legitimate concern underneath them — the risk team is worried about auditability, and the test lead is worried about coverage — so I'd try to separate the two issues rather than pick a winner. The readability concern is real: a matrix where every control fans out to five links is hard to review. But forcing a one-to-one mapping would either drop verification activities or misrepresent what was actually done, and a matrix that misrepresents the evidence is worse than one that's dense.

My approach would be to keep the matrix readable by structuring it in layers rather than flattening it. The top-level view shows one row per risk control with a single "verification status" column — complete, partial, or gap — so an auditor can scan coverage at a glance. Drilling into any row reveals the individual verification activities, each with its method (test, analysis, inspection, review) and its specific acceptance criterion. That way the risk team gets the clean summary they want, and the test lead gets the multiple links they need, without either being hidden.

I'd also push for a shared definition of what counts as a distinct verification activity. If a control is verified partly by analysis and partly by test, those are two activities with two different kinds of evidence, and collapsing them into one link would obscure that. The resolution isn't "one link or many" — it's "one summary status, many underlying activities, with a clear rule for when an activity is distinct enough to warrant its own row."

**Possible follow-ups:**
- How would you handle a control where the analysis and the test give conflicting results — which one governs the verification status?
- If the risk team's real concern is audit time, what would you change about the matrix format to address that without reducing the number of links?