# risk-requirements-traceability — Day 59

## Q1: How would you approach tracing a risk control measure that is implemented as a firmware-based watchdog kick — where the firmware must periodically write to a hardware register to prove liveness — when the firmware team owns the kick logic and the hardware team owns the watchdog peripheral, and neither team's requirements document references the other?

**Answer:** The core problem is that the control is a *contract* between two subsystems, and a contract that lives in neither document is effectively undocumented. I'd start by treating the watchdog as a single integrated risk control with two halves, and make the interface between them explicit before touching either requirements document.

Concretely, I'd define an interface requirement that both teams own jointly — something like "the firmware shall write the watchdog service register at an interval no greater than T_service, and the hardware watchdog shall assert reset if no service write occurs within T_timeout, where T_timeout > T_service with defined margin." That single statement is the traceable artifact. It gets an ID, it lives in the system-level requirements (or an ICD), and both the firmware requirements and the hardware requirements derive from it and reference it.

From there, traceability becomes bidirectional and complete: the hazard → the integrated risk control → the interface requirement → the firmware requirement (kick cadence, what conditions suppress the kick) and the hardware requirement (timeout value, reset behavior, clock source independence) → each team's verification activity → and finally a system-level verification that the two halves actually work together under fault injection (e.g., halt the firmware and confirm the reset fires within the specified window).

The subtle risk I'd flag is the *independence* assumption. A watchdog only mitigates the hazard if the thing that fails is not also the thing that services the watchdog. If the same firmware task that could hang is also responsible for the kick, the control may be defeated by the very failure it's meant to catch. So the interface requirement should also capture any architectural constraint (separate task, separate clock, hardware-only timeout) that the risk analysis depends on — otherwise the traceability looks complete while the control is silently weakened.

**Possible follow-ups:**
- If the two teams disagree on the timeout value, how would you resolve it and where would the decision be recorded?
- How would you verify the independence assumption — that the watchdog can still fire when the firmware is fully hung?

## Q2: How would you approach deciding whether a risk control measure should be traced to a design requirement, a design element, or both — and what practical difference does that distinction make in a traceability matrix?

**Answer:** The distinction matters because requirements and design elements answer different questions, and a risk control usually needs both links to be auditable.

A *design requirement* states what the system must do or achieve — "the enclosure surface temperature shall not exceed X under single-fault conditions." A *design element* is the concrete thing that realizes it — a specific heatsink, a thermal cutoff, a derating choice, a particular trace width. Tracing a control only to a requirement tells you the intent exists but not what implements it; tracing only to a design element tells you something exists but not what it's supposed to achieve or how you'd know it's adequate.

In practice I'd trace risk controls to both where possible, because the two links serve different lifecycle needs. The requirement link is what you verify against and what survives a redesign — if the heatsink changes, the requirement stays and the verification still applies. The design element link is what you inspect, review, and change-control — it's how you catch that someone swapped a part and quietly invalidated a control.

There are cases where one link is genuinely sufficient. A purely procedural control (a label, an instruction in the manual) may have no design element — it traces to a requirement and to a verification-by-inspection of the label artwork. A component derating control may be awkward to express as a functional requirement, so it traces primarily to a design element plus a design-rule or analysis verification. The key is to be explicit about *which* link carries the verification burden, so that a gap analysis doesn't produce a false "covered" when only the weaker link exists.

**Possible follow-ups:**
- How would you handle a control where the design element is shared across several requirements, so a change to it affects multiple traces?
- What would you put in the matrix to make it obvious which link is the one being verified?

## Q3: How would you approach establishing traceability for a risk control measure that is implemented as a redundant channel — for example, a primary sensor path and an independent secondary path whose agreement is checked — where the control's effectiveness depends on the *independence* of the two channels rather than on either channel alone?

**Answer:** This is a case where the traceability matrix can look perfectly complete and still miss the actual control. The control isn't "sensor A works" or "sensor B works" — it's "the two channels fail independently, and disagreement is detected and acted upon." So the traceable artifact has to be the *independence claim* and the *comparison logic*, not just the two signal paths.

I'd structure it in three layers. First, a system-level risk control requirement that states the independence property explicitly — shared power, shared clock, shared ground, shared firmware task, shared communication bus are all things that can silently couple the channels and defeat the control. Second, a design element trace to the physical and logical separation that actually delivers that independence, plus a verification activity that *demonstrates* it — for example, fault injection on one channel while confirming the other continues to function and the disagreement is flagged. Third, the comparison/agreement logic itself as its own requirement, with its own verification, because the detection threshold and the response are separate from the redundancy.

The failure mode I'd watch for is common-cause coupling that nobody documented. If both channels share a regulator, a reference voltage, or a firmware module, the "redundancy" is nominal. So the traceability scheme should include a common-cause analysis link — the risk file should record which independence assumptions were made, and the matrix should show that each assumption has a verification activity. Without that, you've traced two channels and zero independence.

**Possible follow-ups:**
- How would you verify independence without physically destroying one channel on every unit?
- If the two channels share a power rail for cost reasons, how would that change the risk analysis and the traceability?

## Q4: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity's test procedure was written against an earlier revision of the requirement, so the test still passes but no longer exercises the current acceptance criteria?

**Answer:** This is a revision-control failure disguised as a passing test, and it's one of the more dangerous traceability gaps because the matrix shows green. The link exists, the test passes, and yet the control is effectively unverified against what it's now supposed to do.

My first move is to establish the facts: pull the requirement's revision history, the test procedure's revision history, and the change records that connect them. The question is whether the requirement changed and the test wasn't updated, or whether the test was updated but the traceability link still points at the old procedure. Those are different problems with different fixes.

If the requirement genuinely changed, the test is invalid for the current requirement and must be re-baselined — the acceptance criteria in the procedure need to be rewritten to match, and the test re-run. If the change was editorial (wording, formatting) and the acceptance criteria are materially identical, I'd document that assessment rather than re-run, but I'd still update the procedure's revision reference so the link is honest.

The systemic fix is to make requirement changes trigger a review of linked verification activities as part of the change-control process — a "downstream impact" check. A traceability matrix is only as good as its revision discipline; if links are static while the artifacts move, the matrix becomes a historical document rather than a live one. I'd also add a periodic audit that samples links and confirms the referenced revisions are current, because this kind of drift accumulates quietly.

**Possible follow-ups:**
- How would you decide whether a requirement change is material enough to require re-testing versus a documented assessment?
- What would you put in the change-control process to prevent this drift from recurring?

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has built a traceability matrix that links every risk control measure to a verification activity, and the matrix is complete and passes audit. However, a test engineer privately tells you that several of the linked tests were written by copying a similar test from a previous project and adjusting the labels, and that nobody has confirmed the tests actually exercise the failure conditions in this project's risk analysis. The systems engineer argues the matrix is compliant and the tests pass, so there's no problem. How would you handle this?

**Answer:** I'd treat this as a serious finding rather than a process nitpick, because the matrix is doing exactly what it's designed to do — it's just that the underlying evidence doesn't support the claim. A complete matrix with unvalidated tests is worse than an incomplete one, because it creates false confidence and would likely survive an audit while leaving a real safety gap.

I'd start by not escalating immediately on the basis of a private conversation. I'd verify the concern myself by picking a few of the flagged links and walking through them: does the test procedure's stimulus actually drive the failure condition named in the risk analysis, and does the acceptance criterion distinguish pass from fail in a way that would catch the control being absent? If the concern holds, I now have concrete examples rather than an allegation.

Then I'd bring it to the systems engineer and the test lead together, framed around the evidence rather than around blame. The point isn't that the matrix is wrong — it's that the matrix's claim ("this control is verified") depends on the test actually exercising the failure condition, and we need to confirm that. I'd propose a targeted review of the suspect links: for each, confirm the test's stimulus, its acceptance criterion, and its ability to fail when the control is disabled. Tests that don't meet that bar get rewritten or replaced.

I'd also address the systemic cause. Copying a test from a prior project isn't inherently wrong — it's efficient — but it needs a validation step that confirms the failure condition and acceptance criteria match *this* project's risk analysis. I'd fold that into the test-development workflow so the shortcut stays available but the verification of fitness is explicit. And I'd make sure the audit trail reflects the re-validation, so the matrix's claims are backed by evidence that actually supports them.

**Possible follow-ups:**
- How would you handle the fact that the test engineer raised this privately rather than through normal channels?
- If re-validating the tests would delay a scheduled verification milestone, how would you weigh that against the safety gap?