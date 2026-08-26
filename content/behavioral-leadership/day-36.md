# behavioral-leadership — Day 36

## Q1: How would you approach leading a technical investigation when a field-reported issue with a medical device could be caused by either a sensor hardware failure or a firmware filtering algorithm error, and the two possible causes would require very different corrective actions?

**Answer:** I'd start by framing this as a data-collection problem rather than a debate between the hardware and firmware teams. The first step is to establish a neutral fact base: pull the field-returned units, gather any logged data from the devices, and review the failure patterns across the installed base. I'd look for discriminating evidence — for example, whether the failure correlates with specific sensor lots, environmental conditions, or firmware versions. If the device logs raw sensor values before filtering, that data alone can often separate the two hypotheses. If the raw values look clean but the output is wrong, that points to firmware; if the raw values themselves are anomalous, that points to hardware.

Once we have data, I'd design targeted experiments to test each hypothesis independently. For the sensor hardware path, that might mean bench-testing returned units with known-good firmware to see if the anomaly reproduces. For the firmware path, it might mean replaying logged raw data through the filtering algorithm in simulation to see if it produces the observed error. I'd also use a structured framework like a fishbone diagram to ensure we're considering all contributing factors — power supply noise, EMI, timing, calibration drift — rather than prematurely narrowing to the two obvious candidates.

The key is to avoid letting the two teams commit to their preferred explanation before the evidence is in. I'd set a rule that we don't discuss corrective actions until we have a confirmed root cause, and I'd document the investigation as we go so the reasoning is traceable. If the evidence genuinely supports both hypotheses simultaneously — for example, marginal sensor hardware that exposes a firmware robustness gap — then the corrective action would need to address both, but with a clear priority based on which contributes more to the failure.

**Possible follow-ups:** How would you handle a situation where the field data is insufficient to discriminate between the two hypotheses? What would you do if one team refuses to accept the evidence because it contradicts their earlier analysis?

---

## Q2: How would you approach building a risk management culture on a medical device team that currently treats ISO 14971 documentation as a checkbox exercise done after the design is complete?

**Answer:** The core problem is that the team sees risk management as documentation rather than as a design activity. I'd start by reframing the purpose: the risk management file isn't something you write to satisfy an auditor — it's a record of the thinking you already did during design. To shift the culture, I'd integrate risk activities into existing engineering workflows rather than adding them as separate overhead.

Concretely, I'd introduce risk as a standing agenda item in design reviews. Instead of asking "have we updated the risk table?" I'd ask "what new hazards does this design decision introduce, and how are we mitigating them?" This makes risk analysis a natural part of technical discussion. I'd also link risk items to specific design requirements and verification tests, so the team can see that risk management drives actual engineering work rather than existing independently of it.

I'd also work to make the risk file a living document that engineers actually use. That means keeping it in a format that's easy to update — not a static document that requires a formal change process for every edit. Early in the project, I'd hold a facilitated risk workshop where the team identifies hazards together, using techniques like brainstorming and structured hazard analysis. This builds ownership because the team sees their own input reflected in the document.

Finally, I'd connect risk management to the engineering instinct engineers already have. Most engineers naturally think about "what could go wrong with this design?" — the skill is channeling that instinct into a structured format. I'd acknowledge that the documentation is necessary for regulatory reasons, but the value is in the analysis itself. Over time, as engineers see risk analysis catch real problems before they reach testing, the culture shifts from checkbox compliance to genuine risk awareness.

**Possible follow-ups:** How would you handle a team member who sees risk management as someone else's job? How would you measure whether the culture shift is actually working?

---

## Q3: How would you approach leading a design review for a medical device PCB when you discover, mid-review, that a critical safety-related trace width calculation was never documented, and the original designer is no longer with the company?

**Answer:** The immediate priority is to determine whether the design is actually safe, not just whether the documentation exists. I'd pause the review on that specific item and treat it as a design verification question. The trace width calculation for a safety-related path — for example, a fuse input or a current-limiting resistor connection — can be re-derived from first principles using the known current, allowable temperature rise, copper weight, and ambient temperature range. I'd ask a qualified engineer on the team to perform that calculation independently and compare it against the actual trace geometry in the layout.

If the re-derived calculation shows the trace is adequate, then the issue becomes a documentation gap rather than a design defect. I'd have the engineer document the calculation, note that it was performed retrospectively, and flag it for the design history file. If the calculation shows the trace is marginal or inadequate, then we have a real safety issue that needs a design change, and the review would be blocked on that item until a fix is implemented.

I'd also use this as a lesson about design review preparation. The fact that this gap wasn't caught earlier suggests the review package didn't include a requirement that all safety-related calculations be documented before the review. I'd propose adding a checklist item for future reviews: any safety-critical parameter must have its calculation traceable to a source document or standard. This turns an individual gap into a process improvement.

Throughout this, I'd be careful about tone. The original designer is gone, so there's no value in assigning blame. The focus should be on verifying the design and fixing the process gap.

**Possible follow-ups:** What if the re-derived calculation shows the trace is inadequate, but the board is already in manufacturing? How would you prioritize the documentation fix versus the design fix?

---

## Q4: How would you approach handling a situation where a regulatory audit is scheduled in two weeks, and you discover that several key design verification test reports are missing signatures or have incomplete data that cannot be re-run in time?

**Answer:** I'd start by triaging the findings into categories: reports that are complete but missing signatures, reports with minor data gaps that can be resolved with existing records, and reports with substantive gaps that genuinely cannot be completed in time. The first two categories are administrative — signatures can be obtained from the original test engineers if they're still available, and minor gaps might be fillable from raw data logs or test equipment records.

For the substantive gaps, I'd be honest about what can and cannot be done. I would not fabricate data or backdate signatures — that's both unethical and a regulatory violation that would be far worse than a non-conformance. Instead, I'd prepare a formal gap assessment that documents exactly what is missing, why it cannot be completed in the available time, and what the plan is to close the gap. This becomes part of the audit response.

I'd also think about whether any of the missing data can be legitimately reconstructed. For example, if a test was performed but the report was never finalized, the raw data from the test equipment might still exist and could be used to complete the report. If a test was performed but the data was lost, that's a different situation — the test may need to be repeated, which likely can't happen in two weeks.

In the audit itself, I'd be transparent. Auditors generally respond better to a clear, honest gap assessment with a remediation plan than to vague assurances or attempts to hide the issue. I'd present the gap as a process failure — the report completion workflow wasn't followed — rather than a technical failure of the device. I'd also use this as a trigger to review the report completion process to understand why reports were left unsigned or incomplete, so the same issue doesn't recur.

**Possible follow-ups:** How would you decide which gaps to disclose proactively versus only if the auditor asks? What if the missing data is for a test that is critical to demonstrating safety?

---

## Q5: How would you approach building a cross-functional project timeline for a medical device when the hardware, firmware, and regulatory teams each have different estimates for how long their work will take, and there's no historical data from similar projects?

**Answer:** I'd start by breaking the work down into smaller, well-defined tasks rather than relying on high-level phase estimates. A hardware team might say "layout takes six weeks," but that estimate is more meaningful when broken into schematic completion, component selection, layout, design review, and prototype fabrication. The same applies to firmware and regulatory work. Smaller tasks make it easier to identify dependencies and to have informed conversations about why estimates differ.

I'd also explicitly separate tasks into those with known scope and those with significant unknowns. For the unknowns, I'd ask the teams to provide a range rather than a single point estimate — for example, "two to four weeks" instead of "three weeks." This communicates uncertainty honestly without forcing a false precision. I'd then build the timeline around the more conservative end of the range for critical-path items, while identifying which tasks have flexibility.

For the dependency analysis, I'd map out what each team needs from the others. Hardware needs requirements from the system level; firmware needs hardware prototypes or at least a stable interface specification; regulatory needs design documentation that only exists after design work is done. Some of these dependencies can be parallelized — for example, firmware can start developing against a hardware abstraction layer before the actual PCB exists, and regulatory can begin drafting the submission structure early even if the content isn't final.

I'd also build in explicit buffer time for the integration and testing phases, since that's where cross-team issues typically surface. Rather than treating the timeline as a commitment, I'd present it as a working model that will be refined as estimates firm up. I'd schedule a checkpoint after the first few weeks to compare actual progress against the plan and adjust. The goal is a timeline that the teams believe in because it reflects their input, not one that's imposed from above.

**Possible follow-ups:** How would you handle a situation where one team's estimate is significantly longer than what the project deadline allows? How would you communicate the schedule uncertainty to executives who want a firm commitment date?