# medical-devices — Day 60

## Q1: How would you approach designing the analog front-end for a patient-connected sensor that must resolve a very small signal sitting on top of a much larger common-mode voltage, while keeping the design verifiable against a specified accuracy limit?
**Answer:** The core problem is that the signal of interest is tiny relative to the common-mode and noise environment, so the architecture has to be chosen before any component values are picked. I'd start by defining the signal chain budget: what is the full-scale input range, what resolution and noise floor are actually needed to meet the accuracy spec with margin, and what is the allowable input-referred noise density. From there I'd decide between a true differential instrumentation amplifier front-end, a differential ADC with integrated PGA, or a discrete amplifier chain, weighing CMRR, input bias current, and drift against the verification burden each creates.

For a patient-connected sensor, the front-end also has to respect the isolation and leakage-current constraints, so the amplifier's input bias current and the impedance of the patient interface both matter — a high-impedance electrode or transducer combined with a high-bias-current amplifier produces an offset that drifts with temperature and is hard to distinguish from a real signal. I'd want the reference and bias network to be low-impedance and well-decoupled, and I'd keep the analog return separate from digital return up to a single defined star point.

On the layout side, the priorities are: keep the sensitive analog traces short and symmetric, guard or shield where the source impedance is high, place the ADC reference decoupling right at the reference pin, and keep switching digital currents out of the analog return. For verification, I'd want a test point at each stage so the chain can be characterized stage by stage, not just end to end, and I'd plan to verify noise, offset, gain error, and CMRR separately so a failure points to a specific stage rather than "the analog front-end."

**Possible follow-ups:**
- How would you decide whether to do the gain and filtering in the analog domain versus in the digital domain after the ADC?
- How would you verify the front-end's CMRR and noise performance in a way that's repeatable enough to put in a design verification protocol?

## Q2: How would you approach deciding whether a device needs to comply with a particular standard in the IEC 60601-2 series, and how would you handle a situation where the general standard and a particular standard appear to conflict?
**Answer:** The starting point is the intended clinical function and the device's classification, not the product name. I'd map the device's functions against the scope statements of the candidate particular standards — each one defines what it covers and often what it excludes — and document that mapping as part of the regulatory planning. If the device combines functions, more than one particular standard may apply, and each has to be assessed on its own scope.

Where the general standard and a particular standard appear to conflict, the usual convention is that the particular standard takes precedence for the aspects it specifically addresses, and the general standard applies everywhere else. But "appears to conflict" is often actually "addresses a different aspect," so the first step is to read both clauses carefully and confirm whether they're genuinely in conflict or just addressing different requirements that both apply. If it's a genuine conflict, I'd document the interpretation, cite the precedence rule, and — where the interpretation materially affects safety or the submission — get a regulatory or notified-body opinion in writing rather than resolving it internally and hoping.

The output of this exercise should be a standards applicability matrix that lists each applicable standard, the clauses that apply, and how each will be verified. That matrix becomes an input to the test plan and to the DHF, so the reasoning is traceable later.

**Possible follow-ups:**
- How would you handle a device where a particular standard's test method is impractical to apply to your specific form factor?
- Who in the organization should own the standards applicability decision, and how do you keep it current as the design evolves?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable as a project runs, rather than becoming a document that's assembled at the end?
**Answer:** The risk management file should be a living set of linked artifacts, not a single binder produced at submission time. I'd structure it around the ISO 14971 process: risk management plan, hazard identification and risk analysis, risk evaluation, risk control, verification of risk control effectiveness, and evaluation of overall residual risk, with a production and post-production feedback loop closing back into the analysis.

Practically, the key is traceability in both directions. Every hazard should trace to the harm it could cause, to the risk control that addresses it, to the verification evidence that the control is effective, and to the design element that implements it. That means the risk file has to be linked to the design inputs, the design outputs, and the verification records — if those live in separate systems with no cross-references, the file decays the moment the design changes.

I'd also want the risk analysis to be updated as a routine part of change control, not as a separate activity. Any design change should trigger a review of whether it introduces a new hazard, affects an existing risk control, or changes the residual risk evaluation. And I'd keep the risk file's structure stable even as content changes, so reviewers can find things and so the file can be audited without a scavenger hunt.

**Possible follow-ups:**
- How would you handle a hazard that's identified late, after the design is largely frozen?
- What's the difference between verifying that a risk control is implemented and verifying that it's effective, and how would you capture both?

## Q4: A clinical stakeholder requests a usability change late in development that would require a hardware revision and push the regulatory submission out. How would you evaluate and respond to the request?
**Answer:** I'd treat it as a structured trade-off rather than a yes/no, and I'd want the decision made with the right people in the room — clinical, regulatory, quality, program management, and engineering. The first step is to understand what problem the change is actually solving: is it addressing a use error that could cause harm, a workflow inefficiency, or a preference? Those have very different weights, and a use error with a plausible harm path is a different conversation from a cosmetic preference.

If it's a genuine safety or usability concern, the question shifts from "should we do it" to "how do we do it correctly" — which may mean a design change now, a design change in a follow-on revision, or a risk control that doesn't require hardware. If it's a preference, I'd want to quantify the cost honestly: hardware revision, re-verification scope, any re-testing that's affected, and the submission impact. Then I'd present the options with their trade-offs and let the accountable decision-maker choose, documenting the rationale either way.

The thing I'd avoid is either silently absorbing the change and blowing the schedule, or reflexively saying no and leaving a real usability issue unaddressed. Both are failures of the same kind — not making the trade-off explicit.

**Possible follow-ups:**
- How would you decide whether the change can be deferred to a post-market revision without creating a regulatory obligation now?
- If the decision is to defer, how would you document that so it's defensible later?

## Q5: How would you approach verifying that a device's firmware correctly handles a sensor that intermittently produces readings within the valid range but physiologically implausible — for example, a pressure spike that is numerically possible but inconsistent with the patient's condition?
**Answer:** The first thing is to recognize that this is a plausibility problem, not a range problem, so a simple min/max check won't catch it. The firmware needs some model of what's physiologically reasonable given the recent history — rate-of-change limits, consistency with correlated parameters, or a short-window statistical check — and the design question is where that logic lives and how it fails safe.

I'd approach the verification by defining the failure modes explicitly: a single isolated spike, a sustained implausible level, a spike that coincides with a real event, and a spike that arrives during a period of otherwise valid data. Each needs a defined expected behavior — reject and substitute, flag and continue, or alarm — and the test cases should be derived from those definitions rather than from a generic "inject noise" test.

For testability, I'd want the plausibility logic to be separable from the acquisition path so it can be exercised with synthetic input sequences, and I'd want the test harness to be able to replay recorded or generated sequences deterministically. The verification plan should cover both the detection logic and the response: does the device continue monitoring the other parameters, does it avoid a false alarm, and does it log the event in a way that's useful for later analysis? The failure mode I'd be most concerned about is a plausibility filter that's too aggressive and suppresses a real event, so the test set has to include cases where the "implausible" reading is actually the clinically significant one.

**Possible follow-ups:**
- How would you decide the threshold between "reject" and "flag and continue" for a given parameter?
- How would you verify that the plausibility logic doesn't introduce a delay that affects alarm response time?