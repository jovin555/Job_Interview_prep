# medical-devices — Day 53

## Q1: How would you approach determining the applicable IEC 60601-2 particular standards for a device that combines two functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** I'd start by defining the device's intended use and clinical function precisely, because the particular standards are scoped by function, not by product name. The general standard, IEC 60601-1, always applies, and then each particular standard (the 60601-2-xx series) applies to the specific function it covers. For a combined-function device, more than one particular standard can apply simultaneously, and the manufacturer has to satisfy all of them for the relevant functions.

The practical approach is: build a standards matrix that maps each device function to its candidate particular standard, then read the scope and the "exclusions" clauses carefully — some particular standards explicitly say they don't cover certain functions, which tells you another standard governs that part. I'd also check the collateral standards (the 60601-1-x series, like 1-2 for EMC, 1-6 for usability, 1-8 for alarms, 1-11 for home healthcare environment) because those apply across device types and often carry requirements the particular standards assume.

Where the general standard and a particular standard appear to conflict, the particular standard takes precedence for that specific requirement — that's the stated hierarchy. But in practice, most "conflicts" are actually the particular standard adding specificity or tightening a limit, not contradicting the general one. When there's genuine ambiguity, I'd document the interpretation, cite the clause, and where the risk is high, get a regulatory or test-lab opinion in writing before committing to a design. The key discipline is to make the applicability decision early, because it drives the test plan, the labeling, and the risk file, and changing it late is expensive.

**Possible follow-ups:**
- How would you document the standards applicability decision so it survives an audit or a design change?
- If a particular standard's test method doesn't map cleanly onto your device's architecture, how would you justify an alternative approach?

## Q2: How would you approach designing the creepage and clearance distances on a medical PCB that has a mains-referenced primary side, a secondary side, and a patient-connected applied part, where the applied part must be isolated from mains by two means of patient protection (2×MOPP)?

**Answer:** The starting point is to define the insulation diagram before touching the layout. I'd map every boundary — mains to secondary, secondary to applied part, and any boundary that has to withstand a single fault — and assign each one its required means of protection. For a patient-connected applied part isolated from mains by 2×MOPP, that means two independent insulation barriers in series, each individually rated for MOPP, not one barrier counted twice.

From there, creepage and clearance come from the tables in IEC 60601-1, and the inputs are: the working voltage across the barrier, the pollution degree of the environment, the material group of the PCB (which depends on the CTI of the laminate), and the altitude the device is rated for. Clearance is driven by the working voltage and any transient overvoltage the barrier must withstand; creepage is driven by working voltage, pollution degree, and material group. For mains-referenced barriers, the working voltage is the mains voltage, and for reinforced or 2×MOPP barriers the required distances are effectively doubled relative to basic insulation.

On the layout itself, the practical rules I'd enforce: keep the isolation barrier as a clearly marked, unbroken region with no traces crossing it except through the intended isolation component; route the barrier so that a single component failure can't bridge it; slot or route-out the PCB under the barrier where the standard allows it to increase creepage without eating board area; and be careful that conformal coating, if used to reduce creepage requirements, is applied and qualified per the standard's conditions — you can't just assume coating buys you a smaller distance. I'd also verify that the isolation components themselves (digital isolators, isolation amplifiers, transformers) are rated for the correct working voltage and MOPP level, since the PCB distances are only half the barrier.

Finally, I'd treat the creepage/clearance calculation as a design output that gets verified — both by measurement on the bare board and by the dielectric strength (hi-pot) test — and I'd keep the insulation diagram in the DHF so the rationale is traceable.

**Possible follow-ups:**
- How does the pollution degree assumption change if the device is used in a home environment versus a controlled hospital environment?
- What would you check on an isolation component's datasheet to confirm it actually provides the MOPP level you're claiming?

## Q3: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band, reproducible failure is a strong hint that something in the device is resonant or that a specific signal path is being demodulated by a nonlinear junction — it's not a broad shielding deficiency, or you'd see failures across a wide range. I'd approach it as a signal-chain problem rather than a "add more shielding" problem.

First, characterize the failure precisely: at what field strength does it start, how wide is the band, is it amplitude- or frequency-dependent, and what exactly is the malfunction — a reset, a corrupted reading, a communication dropout? That tells me whether the energy is coupling into a digital control line, an analog front-end, or the power rail.

Then I'd localize the coupling path. The usual suspects for a narrow-band failure are: a cable or trace acting as an antenna at that frequency (often a length that's a fraction of a wavelength), a connector or cable shield that's terminated poorly, a ground plane split that forces return currents through a sensitive area, or a semiconductor junction (an ESD diode, an unprotected input) rectifying the RF and shifting a bias point. I'd use a near-field probe to sniff where the energy is strongest on the board at that frequency, and I'd try targeted mitigations one at a time — a ferrite on the offending cable, a small RC or feedthrough filter at the affected input, a series resistor or common-mode choke on a communication line, or a local decoupling change — and re-test to confirm which one actually moves the failure threshold.

The fix usually ends up being a combination of filtering at the point of entry and improving the return path, not a global change. Once resolved, I'd verify at the required field strength with margin, and I'd document the root cause and the fix in the risk file, because an immunity failure is a risk-control-relevant finding.

**Possible follow-ups:**
- How would you decide whether the fix belongs in hardware or whether firmware mitigation (like a watchdog or error detection) is acceptable?
- How would you confirm the fix doesn't degrade emissions performance elsewhere?

## Q4: How would you approach building and maintaining traceability between design inputs, design outputs, verification, and validation in a design history file, especially as the design changes?

**Answer:** Traceability is really a data model, and the mistake is treating it as a document you write at the end. I'd set it up so that every design input has a unique identifier, every design output links back to the input(s) it satisfies, every verification activity links to the output it tests, and every validation activity links to the user need or intended use it confirms. The links are bidirectional: from any input you can see how it's realized and tested, and from any test you can see what requirement it covers.

The practical tooling matters less than the discipline. A requirements management tool with traceability matrices built in is ideal, but a well-structured spreadsheet with stable IDs works if it's maintained. The key is that IDs are stable — you never reuse or renumber an ID, because that breaks the audit trail — and that changes flow through the model rather than around it.

For change control, I'd tie traceability to the change process: when a design input changes, the change record identifies every affected output, verification, and validation item, and those get updated or re-run as appropriate. When a design output changes without an input change, the traceability shows which inputs it still satisfies and whether any verification needs to be repeated. This is where a lot of teams get caught — they change a component and forget that a verification test's validity depended on the old part.

I'd also keep the traceability live during development, not reconstructed before a submission, because reconstructing it always reveals gaps. And I'd make it reviewable: at each design review, the traceability status is part of what's reviewed, so missing links surface early. The end goal is that an auditor or a new engineer can pick any requirement and follow it end-to-end without asking anyone.

**Possible follow-ups:**
- How would you handle a design input that's satisfied by multiple outputs, or an output that satisfies multiple inputs?
- What would you do if you discovered, late in the project, that a verification test had no traceable link to a design input?

## Q5: You're the lead engineer, and during a design review the quality manager insists on adding a risk control measure for a hazard the engineering team considers negligible. The schedule impact is significant. How would you handle this situation?

**Answer:** I'd treat it as a risk-acceptance disagreement rather than a schedule argument, because framing it as "quality versus schedule" makes it adversarial and doesn't resolve anything. The real question is whether the residual risk, as estimated, is acceptable — and that's a decision the risk management process is supposed to make, not a negotiation between two people.

First, I'd ask the quality manager to walk through the hazard, the estimated severity and probability, and the basis for those estimates. Sometimes the disagreement is about the estimate itself — the engineering team may be assuming a probability that isn't well supported, or the quality manager may be applying a severity that's higher than the harm actually warrants. Getting the reasoning on the table usually clarifies whether this is a data disagreement or a judgment disagreement.

If it's a judgment disagreement about acceptability, I'd bring it back to the risk acceptability criteria that were defined at the start of the project — those criteria exist precisely so that individual cases don't get decided by whoever argues hardest. If the residual risk meets the criteria, the decision to accept is defensible and documented. If it doesn't, then the control measure is required regardless of schedule, and the conversation shifts to how to implement it with the least disruption.

If the criteria are genuinely ambiguous or the hazard sits near the boundary, I'd escalate to the risk management review or the appropriate decision-maker rather than let it stall, and I'd document the rationale either way. On schedule, I'd look for whether the control can be implemented in a way that doesn't require a full redesign — sometimes a labeling change, a firmware guard, or a test addition satisfies the intent at much lower cost. But I wouldn't let schedule pressure override a legitimate safety concern; that's exactly the kind of decision that looks bad in hindsight and worse in an audit.

**Possible follow-ups:**
- How would you handle it if the quality manager's concern is valid but the proposed control measure introduces its own new risk?
- What would you document to show the decision was made through the proper process rather than informally?