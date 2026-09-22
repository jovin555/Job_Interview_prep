# medical-devices — Day 63

## Q1: How would you approach designing the analog front-end for a patient-connected biosensor whose signal of interest is a fraction of a millivolt riding on a baseline that can drift by hundreds of millivolts, while keeping the design verifiable against a specified accuracy limit?

**Answer:** The core problem is dynamic range versus resolution: the signal of interest is tiny relative to the baseline, so if you amplify everything equally you either saturate on the baseline or lose the signal in the noise floor. I'd approach it in layers.

First, decide where the baseline is removed. Options are AC coupling (a high-pass stage) or a baseline-restoration/servo loop. AC coupling is simple and cheap but sets a lower corner frequency that must be well below the signal band, and it introduces a settling time after any transient — which matters if the device must recover quickly from a motion artifact or a lead-off event. A servo loop actively drives the baseline to mid-scale and can have better settling behavior, but it adds a control loop that itself must be analyzed for stability and for interaction with the signal band.

Second, the instrumentation amplifier stage. For a patient-connected front-end I want high common-mode rejection, high input impedance, and a defined input bias current path. The gain is set so the largest expected signal-plus-residual-baseline maps just inside the ADC's input range, leaving headroom for tolerance and drift. I'd budget the error contributions explicitly: amplifier offset and offset drift, gain error, CMRR over frequency, input-referred noise density integrated over the signal bandwidth, and the reference's own noise and drift. Each of these becomes a line in the error budget that must sum (worst-case or RSS, depending on the accuracy argument) to less than the specified limit.

Third, the ADC and reference. Resolution alone isn't accuracy — I care about effective number of bits at the actual signal bandwidth, and about whether the reference is quiet and stable enough that it doesn't dominate the budget. If the reference drifts, the whole measurement drifts with it.

Fourth, verifiability. This is the part that's easy to under-plan. I'd want the accuracy specification decomposed into a testable chain: a known signal injected at the input (or at a defined calibration point), a defined reference instrument traceable to a standard, and a test that exercises the full signal path including the ADC and any digital filtering. If the signal is small enough that the test equipment itself is a limiting factor, that has to be identified early, because it changes the verification strategy — you may need a precision source or an external lab.

The key discipline is that every stage's error contribution is written down and traced to a requirement, so that when the design is reviewed you can point to *why* each component was chosen and *how* the accuracy will be demonstrated.

**Possible follow-ups:**
- How would you decide between AC coupling and an active baseline-restoration loop for a given signal bandwidth?
- If the error budget shows the ADC reference dominates, what are your options?

---

## Q2: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** I'd start from the device's intended use and clinical function, not from the electronics. The particular standards are organized around clinical function and device type, so the first step is a clear statement of what the device does, in what environment, and on what patient population. From that, I'd build a list of candidate particular standards by reading the scope clause of each — the scope tells you whether the standard applies, and it's usually explicit about exclusions and about what happens when a device combines functions.

For a combined-function device, the usual situation is that more than one particular standard applies, each to its respective function. The general standard (60601-1) applies throughout, and each particular standard modifies or supplements it for its function. The practical approach is to build a requirements matrix: rows are the clauses of the general standard plus each applicable particular standard, columns are the device's subsystems, and each cell records whether the requirement applies, how it's met, and how it's verified. That matrix is what makes the compliance argument auditable rather than a narrative.

Conflicts are where this gets interesting. A particular standard can be more stringent than the general standard, and where it is, the more stringent requirement governs for that function. Genuine conflicts — where two requirements can't both be satisfied — are rare but do occur, and the resolution is almost always to go back to the risk analysis: which requirement is protecting against which hazard, and is there a design that satisfies both intents? If not, that's a conversation with the test lab and possibly the regulator, documented as a deviation with rationale, not something to resolve silently in the design.

I'd also flag that the applicable standards list is a living document. It's reviewed at design input, at each design review, and before submission, because a standard revision or a change in intended use can change the list.

**Possible follow-ups:**
- How would you document the rationale for a standard you decided *not* to apply?
- What would you do if a particular standard's requirement appeared to conflict with a usability requirement from the clinical team?

---

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The failure mode I want to avoid is the risk file that gets written backwards from the finished design — where hazards are listed to match what was already built, and the risk controls are described after the fact. That file passes an audit but doesn't actually influence the design, which defeats the purpose.

The way to avoid it is to make the risk file a working artifact from the start. At design input, I'd begin with hazard identification driven by intended use, clinical function, and the foreseeable misuse cases — not by the schematic. That produces an initial hazard list that's genuinely independent of the design, which is important because it means the design has to respond to it rather than the other way around.

From there, each hazard gets a risk estimate (severity and probability), and the risk controls are identified as design requirements. This is the key structural move: a risk control isn't a paragraph in a risk file, it's a requirement that flows into the design inputs, gets a design output, and gets verified. That's what makes the traceability real — you can follow a hazard to a control to a verification result without leaving the file.

The file itself I'd structure so that it's navigable: a hazard analysis (however you choose to format it — FMEA, fault tree, or a structured hazard table), a risk control measure list, a verification evidence index, and a residual risk evaluation with the overall benefit-risk conclusion. Each entry should have an owner and a status, so that at any design review you can see what's open.

Two things keep it maintainable. First, it's reviewed at every design review, not just at the end — so changes to the design trigger a re-look at the affected hazards. Second, the residual risk acceptance is a documented decision with a named approver, not an implicit "we didn't find anything else." That's what an auditor is actually looking for.

**Possible follow-ups:**
- How would you handle a hazard that's identified late, after the design is largely frozen?
- What's the difference between a risk control implemented in hardware versus one implemented in the instructions for use, and how does that affect the file?

---

## Q4: A clinical stakeholder requests a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** My first move is to understand what's actually being asked, because "usability change" can mean anything from a label change to a new enclosure. I'd sit down with the clinical stakeholder and the usability lead to get the specific use error or workflow problem they're trying to solve, and to understand how they arrived at that particular solution. Often the underlying problem is real but the proposed solution isn't the only one — and sometimes a firmware or labeling change addresses the same use error without touching hardware.

Once I understand the problem, I'd evaluate it against the risk file. If the use error is associated with a hazard, then it's not optional — it has to be addressed, and the question becomes *how*, not *whether*. If it's a preference rather than a risk, that's a different conversation, and it belongs in a prioritization discussion with the product owner, not a unilateral engineering decision.

For the options themselves, I'd lay out the trade space honestly: what each option costs in schedule, in verification and validation effort, in regulatory impact, and in residual risk. A hardware revision late in development isn't just the board respin — it's re-verification of affected requirements, potentially re-testing for EMC and safety, updated DHF, and a submission delay. That full cost needs to be visible to whoever is making the call, because the clinical stakeholder may not have that picture.

Then I'd bring it to the appropriate decision-maker — typically a program lead or a change control board — with a clear recommendation and the rationale. My job is to make the trade-off legible, not to make the business call unilaterally. If the decision is to proceed, I'd want it documented as a formal change with the schedule and regulatory impact acknowledged, so that it's a conscious decision rather than a surprise later.

The one thing I wouldn't do is quietly absorb the change into the schedule and hope. That's how projects end up with unverified changes in a submitted design.

**Possible follow-ups:**
- How would you handle it if the clinical stakeholder and the program lead disagreed on whether the change was necessary?
- What would you do if the change was clearly risk-relevant but the schedule impact was unacceptable to the business?

---

## Q5: How would you approach deciding whether a given software failure in a medical device should be classified as a safety-related failure requiring formal risk controls, versus a non-safety usability or reliability issue?

**Answer:** The classification should follow from the risk analysis, not from intuition about how bad the failure "feels." The question I ask is: if this failure occurs, what's the resulting hazardous situation, and what's the severity of the harm that could result? That's the same logic the risk file uses for any hazard, and applying it consistently is what keeps the classification defensible.

Concretely, I'd trace the failure to its effect on the device's clinical function. A failure that could cause the device to display a physiologically implausible value that a clinician might act on is different from a failure that causes a log entry to be dropped. A failure that could cause a therapy to be delivered incorrectly is different again. The severity of the potential harm, combined with the probability of the hazardous situation occurring and being undetected, drives whether formal risk controls are needed.

There's a subtlety around detectability. A failure that's immediately obvious to the user — a blank screen, an alarm — is often less risky than a silent failure that produces plausible-looking but wrong data. Silent failures tend to warrant more formal controls because the hazardous situation can persist undetected.

I'd also be careful not to let the classification be driven by convenience. It's tempting to call something a "usability issue" because that avoids a formal risk control and a verification burden. The discipline is to apply the same severity and probability criteria regardless of the engineering effort involved, and to document the rationale for the classification so it can be reviewed.

Where the classification is genuinely ambiguous, that's a signal to bring it to the risk management review rather than resolve it alone. And once classified as safety-related, the failure mode belongs in the risk file with a control and a verification, and the software's safety classification under IEC 62304 should be consistent with that.

**Possible follow-ups:**
- How would you handle a failure that's safety-related in one use environment but not another?
- What evidence would you want to see before accepting that a failure is "non-safety"?