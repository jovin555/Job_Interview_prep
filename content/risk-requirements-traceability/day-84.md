# risk-requirements-traceability — Day 84

## Q1: How would you approach tracing a risk control measure that is implemented as a *latency budget* distributed across a chain of hardware and firmware elements — for example, "the system shall de-energize the output within a bounded time after a fault is detected" — when no single element owns the whole timing requirement?

**Answer:** The core problem is that a timing requirement is a *system-level* property that emerges from a chain of contributors, none of which individually satisfies or violates it. The traceability scheme has to reflect that structure rather than pretend a single element owns it.

My approach would be to decompose the budget explicitly. First, establish the total budget as a system-level safety requirement derived from the risk analysis — the risk file should state why that bound exists (e.g., the time beyond which the hazardous condition becomes unacceptable). Then allocate the budget across the chain: sensor detection latency, signal conditioning/filtering delay, ADC conversion, firmware detection and decision logic, output driver response, and any relay or contactor actuation time. Each allocation becomes a derived requirement owned by a specific element or team, with its own acceptance criterion and its own verification method — some by test, some by datasheet analysis, some by measurement.

The traceability matrix then has a parent-child structure: the system-level timing requirement traces down to each allocated sub-budget, and each sub-budget traces to its verification activity. Critically, the matrix must also capture the *composition rule* — the fact that the sub-budgets sum (or worst-case add) to the total. That composition is itself a verification activity: a system-level test that injects a fault and measures end-to-end response time, confirming the allocations hold in aggregate. Without that top-level test, you can pass every sub-budget and still miss the total, because of unmodeled contributors like interrupt latency or bus arbitration delays.

I'd also flag the interfaces between elements as the highest-risk part of the budget, since those are where ownership is ambiguous and where latency is easiest to overlook.

**Possible follow-ups:**
- How would you handle a sub-budget that is verified by analysis (e.g., a datasheet propagation delay) rather than by test — what evidence would you accept?
- If the system-level test passes but one sub-budget was never independently verified, is the traceability complete?

## Q2: How would you approach establishing traceability when a single risk control measure is implemented *redundantly* — the same hazard is mitigated by two independent controls, and the risk analysis credits both — but the two controls were added at different times by different teams?

**Answer:** Redundancy creates a specific traceability hazard: the risk analysis credits two controls, but if the traceability only shows one path cleanly, an auditor or a reviewer can't tell whether both are actually present, independent, and verified — or whether one was added later as a "belt and braces" measure that was never formally tied back to the hazard.

I'd start by making the risk file the single source of truth for the *claim*: one hazard, two credited controls, each with its own risk control ID. Then each control gets its own traceability thread — control → implementing requirement(s) → design element(s) → verification activity — so the two threads are visibly separate even though they converge on the same hazard. The matrix should show the convergence explicitly, not collapse the two into one row.

The harder part is the *independence* claim. If the risk analysis credits both controls on the basis that they're independent, that assumption needs its own verification — a common-cause failure analysis or a documented argument that the two controls don't share a power rail, a microcontroller, a sensor, or a software module. That analysis is a verification activity in its own right and should be traced to the hazard alongside the two controls.

For the "added at different times by different teams" aspect, I'd reconcile the two threads during a traceability review: confirm both controls still exist in the current design, both are still verified, and the independence argument still holds after any design changes. Late-added controls are the ones most likely to have drifted or been quietly removed.

**Possible follow-ups:**
- If the two controls turn out to share a common element, how does that change the risk analysis and the traceability?
- How would you decide whether the independence analysis needs to be redone after a design change to one of the controls?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a *manual* test with no automated logging — the operator toggles a signal and observes an LED — and the risk file treats it as objective evidence?

**Answer:** The traceability link exists, but the *quality* of the evidence is the issue. A manual observation with no logging is weak objective evidence: it's not repeatable in a documented way, it depends on operator judgment, and it can't be re-examined later if the result is questioned. For a risk control, that's usually not good enough.

I'd approach it in two steps. First, assess whether the manual test is *adequate for the risk* — for a low-severity control, a documented manual procedure with a pass/fail criterion and a recorded result might be acceptable. For a control mitigating a serious hazard, it almost certainly isn't. The severity and the nature of the control drive the required rigor.

Second, if the evidence is inadequate, strengthen it rather than just re-label it. That usually means instrumenting the test: capture the signal with a scope or logic analyzer, log the firmware state, or add a test hook that records the event with a timestamp. The goal is to convert "operator saw the LED" into "the output was de-energized within X ms of the fault, as recorded by [instrument]." That gives a measurable, repeatable, re-examinable result.

I'd also make sure the acceptance criterion is explicit and measurable, not "the LED turned off." And I'd document the test setup, the instrument calibration, and the pass/fail threshold so the evidence stands on its own.

**Possible follow-ups:**
- How would you decide which manual tests are acceptable as-is versus which need instrumentation?
- If instrumenting the test isn't feasible, what alternative evidence could support the risk control?

## Q4: How would you approach deciding whether a risk control measure should be traced to a *design requirement*, a *design element*, or *both* — and what practical difference does that distinction make in a traceability matrix?

**Answer:** The distinction matters because it determines what you can actually verify and what a gap in the matrix means.

A *design requirement* is a statement of what the system shall do — "the system shall disable the motor output within 100 ms of a fault signal." It's verifiable by test or analysis, and it's the natural anchor for a verification activity. A *design element* is the physical or logical thing that implements it — a specific comparator circuit, a firmware state machine, a relay. It's verifiable by inspection or by its own lower-level test.

Most risk controls need both links, but for different purposes. The requirement link answers "what must be true and how do we prove it?" The element link answers "where does this live in the design, and if that element changes, what risk controls are affected?" The element link is what makes change impact analysis possible — if someone redesigns the comparator, you can trace forward to every risk control that depends on it.

There are cases where only one link is meaningful. A control implemented purely through component derating (e.g., a capacitor voltage rating well above the maximum stress) may not map cleanly to a functional requirement — it's a design decision, not a behavior — so it traces primarily to a design element plus a design rule or analysis. Conversely, a purely procedural control (a label, an instruction) may trace to a requirement but have no single design element.

In the matrix, I'd capture both where they apply, and I'd treat a missing element link as a flag for change-impact risk, and a missing requirement link as a flag for verification risk. The two gaps mean different things and warrant different follow-up.

**Possible follow-ups:**
- How would you handle a risk control that traces to a design element but has no requirement — is that a gap?
- When a design element changes, how would you use the matrix to find affected risk controls?

## Q5: (Behavioral) Imagine you're leading a project where the risk management file lists a risk control measure, the SRS contains a requirement that implements it, and the verification plan contains a test that verifies the requirement — but when you trace the links, you find that the requirement was written by the systems engineer, the test was written by the test engineer, and neither of them has ever read the risk analysis entry that justifies the control. The links exist on paper, but the *intent* of the control has been lost between the documents. How would you handle this?

**Answer:** This is a documentation-integrity problem disguised as a traceability problem. The links are formally correct, but the *meaning* has been lost, which means the requirement and the test may not actually address the hazard the control was meant to mitigate — and nobody would notice until something went wrong.

I'd handle it in three moves. First, I'd treat it as a process gap, not a people problem — the systems engineer and test engineer did their jobs as the process defined them; the process just didn't require them to engage with the risk analysis. Blaming individuals would make it harder to fix.

Second, I'd close the loop on the specific control: bring the systems engineer, test engineer, and whoever owns the risk analysis entry into one conversation, walk through the hazard and the control's intent, and confirm that the requirement actually captures it and the test actually stresses the failure condition. If either doesn't, fix it. That's a targeted correction, not a rewrite.

Third, I'd fix the root cause so it doesn't recur. The most effective mechanism is to make the risk analysis entry a *required input* to both requirement authoring and test authoring — for example, a review checklist item that asks "which risk control does this requirement implement, and have you read its risk analysis entry?" I'd also consider adding a periodic traceability review where the risk owner, systems engineer, and test lead walk a sample of controls end-to-end and confirm the intent survived the handoffs.

The general principle: traceability links are necessary but not sufficient. The links have to carry *understanding*, and that requires the people on both ends to have read the same source.

**Possible follow-ups:**
- How would you scale that kind of intent-checking review across a large project without it becoming a bottleneck?
- If you found this pattern across many controls, would you stop and fix the process before continuing, or fix controls as you go?