# risk-requirements-traceability — Day 63

## Q1: How would you approach tracing a risk control measure that is implemented as a hardware watchdog timer monitoring a firmware heartbeat, when the hardware and firmware teams each document their portions in separate specifications with no cross-references?

**Answer:** The core problem is that the control is a *contract* between two subsystems, and a contract that lives in two documents with no cross-reference is effectively undocumented. I would start by treating the watchdog as a single risk control measure with a single owner in the risk management file, and then decompose it into the two halves that each team owns — the hardware peripheral configuration and the firmware kick behavior — while keeping both halves anchored to the same risk control ID.

Practically, I'd introduce a shared identifier scheme: the risk control gets an ID in the risk management file, and both the hardware design specification and the firmware requirements document carry that same ID as a cross-reference field, even if their internal numbering schemes differ. The hardware spec documents the watchdog's timeout window, reset behavior, and clock source; the firmware spec documents the kick period, the conditions under which kicking is suspended, and what happens on reset. The critical interface parameters — timeout value, kick margin, reset latency — belong in an interface control document so there's one authoritative place for the numbers both teams must agree on.

For verification, I'd resist the temptation to verify each half in isolation and call it done. The hardware team can verify the peripheral resets when the kick stops, and the firmware team can verify the kick logic runs on schedule, but neither proves the integrated control works. The end-to-end verification — deliberately halting the heartbeat and confirming the system reaches its safe state within the specified time — has to be a system-level test that exercises both halves together.

**Possible follow-ups:**
- If the two teams use different requirement numbering schemes, how would you keep the cross-references stable as requirements change?
- What would you do if the hardware team's timeout window and the firmware team's kick period were specified independently and turned out to be incompatible?

## Q2: How would you approach deciding whether a risk control measure should be traced to a design requirement, a design element, or both — and what practical difference does that distinction make in a traceability matrix?

**Answer:** The distinction matters because a requirement and a design element answer different questions. A requirement states *what must be true* — a measurable, verifiable obligation. A design element states *how it is realized* — a specific circuit, component, firmware module, or mechanical feature. A risk control measure often needs both links, but for different purposes.

If a risk control is only traced to a design element, you can show that something was built, but you have no objective criterion to verify against — there's nothing to test *to*. If it's only traced to a requirement, you can verify the behavior, but you may lose the connection to the specific implementation that provides the control, which matters when the design changes. So the practical rule I'd apply is: trace to a requirement whenever the control has a measurable behavior or property that can be verified, and trace to a design element whenever the control depends on a specific implementation choice that could be changed or substituted.

In the matrix, this shows up as two different link types. Requirement links support verification traceability — requirement to test. Design element links support change impact analysis — if this component changes, which risk controls are affected? A control like a firmware plausibility check naturally has both: a requirement stating the rejection threshold and a design element identifying the module that implements it. A control like component derating may have only a design element link plus a verification-by-analysis activity, because there's no functional behavior to state as a requirement.

**Possible follow-ups:**
- How would you handle a risk control that has a design element link but no requirement link, and the design element is later substituted with an equivalent part?
- Does tracing to both create redundancy in the matrix, and how would you keep the two link types from drifting out of sync?

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity's acceptance criterion is stated as "the control functions as designed" rather than as a measurable pass/fail threshold?

**Answer:** "Functions as designed" is not an acceptance criterion — it's a placeholder that defers the real decision to whoever runs the test, which means the test isn't repeatable and the result isn't objective evidence. The first thing I'd do is go back to the risk analysis and ask what the control is actually supposed to achieve: what failure condition does it mitigate, and what observable behavior demonstrates that mitigation? That gives the raw material for a measurable criterion.

Then I'd work with the test author to convert it into something with a threshold, a tolerance, and a defined test condition. For a control that disables an output on a fault, that might be "output disabled within X ms of the fault being applied, verified at the minimum and maximum specified operating conditions." For a control that rejects out-of-range sensor readings, it might be "readings outside the specified band are rejected in N consecutive samples, with no false rejection of in-band readings across the operating range." The point is that the criterion has to be something two different people running the test would agree on.

I'd also check whether the vagueness is masking a deeper problem — sometimes "functions as designed" appears because nobody has actually defined what correct behavior looks like under fault conditions, which is a risk analysis gap, not just a test-writing gap. If that's the case, the fix belongs upstream in the risk management file, not just in the test procedure.

**Possible follow-ups:**
- How would you handle pushback from a test author who argues that adding precise thresholds will make the test brittle or hard to pass?
- If the risk analysis itself doesn't specify a quantitative threshold, how would you go about deriving one?

## Q4: How would you approach establishing traceability for a risk control measure that is implemented as a redundant channel — for example, a primary sensor path and an independent secondary path whose agreement is checked — where the control's effectiveness depends on the *independence* of the two channels rather than on either channel alone?

**Answer:** This is a case where the control's value lives in a property — independence — that isn't located in either channel, so a naive traceability scheme that links the control to "the primary sensor" and "the secondary sensor" misses the point entirely. The traceability has to capture the independence claim itself as something that can be verified.

I'd start by making the independence argument explicit in the risk management file: what common-cause failures could defeat it, and what design features prevent them? Separate power rails, separate signal paths, different sensing technologies, physically separated routing, independent firmware tasks or processors — each of these is a claim that needs its own verification activity. So the traceability structure fans out: the risk control links to the agreement-check logic, to each channel, and to each independence-preserving design feature, and each of those links carries its own verification.

The verification activities then split into two kinds. Functional verification confirms the agreement check detects disagreement and responds correctly. Independence verification confirms the channels can't fail together in the ways the risk analysis identified — this is often verified by analysis, inspection, or fault injection rather than a simple pass/fail test. I'd make sure the matrix shows both, because a matrix that only shows the functional test would give false confidence that the control is fully verified.

**Possible follow-ups:**
- How would you verify independence by test rather than by analysis, and when would analysis be the more appropriate method?
- If the two channels share a common power supply, how would that affect the traceability and the verification activities?

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has built a traceability matrix that links every risk control measure to a verification activity, and the matrix is complete and passes audit. However, a test engineer privately tells you that several of the linked tests were written by copying a similar test from a previous project and adjusting the labels, and that nobody has confirmed the tests actually exercise the failure conditions in this project's risk analysis. The systems engineer argues the matrix is compliant and the tests pass, so there's no problem. How would you handle this?

**Answer:** The systems engineer is right that the matrix is compliant and the tests pass, and wrong that there's no problem — because the matrix is only as good as the claim behind each link, and a link that points to a test that doesn't exercise the failure condition is a false link. This is exactly the kind of gap that passes audit and fails in the field, so I'd treat it as a real issue rather than a documentation nitpick.

I'd start by not making it adversarial. The test engineer raised a legitimate concern, and the systems engineer is defending work that looks complete on paper. I'd ask for a focused review: take the flagged tests and, for each one, walk through the risk analysis failure condition and ask whether the test would fail if the control were removed or defeated. That's a concrete, answerable question, and it usually settles the matter quickly — either the test does exercise the condition and the concern is resolved, or it doesn't and the gap is obvious to everyone in the room.

Where gaps are confirmed, I'd treat them as verification gaps, not just test-rewrite tasks. The fix is to re-derive the test from the failure condition in the risk analysis, not to patch the existing test. I'd also want to understand how the copied tests got linked in the first place — if the linking was done by matching labels rather than by reading the failure conditions, that's a process weakness that will recur, and it's worth addressing at the matrix-review step rather than only fixing the individual tests. Throughout, I'd keep the framing on the shared goal: a matrix that reflects reality, not one that merely passes audit.

**Possible follow-ups:**
- How would you spot this kind of false link in a matrix review before a test engineer has to raise it privately?
- If the schedule doesn't allow re-deriving all the flagged tests, how would you prioritize which ones to fix first?