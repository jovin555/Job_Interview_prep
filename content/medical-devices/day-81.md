# medical-devices — Day 81

## Q1: How would you approach designing the patient leakage current measurement path for a device that has both BF-type and CF-type applied parts, and how would you decide which measurements are actually required?

**Answer:** The starting point is to read the applied-part definitions and the measurement network requirements in IEC 60601-1 rather than assuming a single "leakage current" number applies everywhere. Patient leakage current is measured from each applied part, or from all applied parts connected together, to earth, and the limits differ by classification: BF-type applied parts have a higher normal-condition limit than CF-type, and CF-type parts carry the tighter limit because they are intended for direct cardiac contact. The measurement network itself is specified — a passive RC network representing the human body impedance — so the test fixture has to implement that network, not a generic current shunt, or the reading won't be comparable to the standard's limits.

Practically, I'd build the measurement path so each applied part can be individually isolated and connected to the measuring network, with a means to tie all applied parts together for the "all applied parts" measurement. The device under test needs to be configured for the worst-case operating state — all functions on, at maximum rated mains voltage plus tolerance, and with the polarity of the mains connection reversed — because leakage is not symmetric and the worst case is what has to pass. For a device with mixed BF and CF parts, the CF part drives the design: the isolation and creepage/clearance for that part must satisfy the CF requirement, and the BF part can usually share the same barrier if it's cheaper to standardize.

Deciding which measurements are required comes down to a matrix: for each applied part, normal condition and single-fault condition, and for each, the applicable limit. Single-fault conditions include things like one means of protection failing, an earth conductor opening, or a component shorting — the standard enumerates them, and you don't get to pick only the convenient ones. I'd document the matrix in the test plan so the lab and the reviewer can see the coverage, and I'd verify the fixture itself against a known reference before trusting any reading.

**Possible follow-ups:**
- If the CF-type applied part is failing its limit but the BF part passes, where would you look first in the circuit?
- How would you handle a device where the applied parts are not galvanically isolated from each other?

## Q2: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band failure is a strong hint that something in the device is resonant or that a specific coupling path is efficient at that frequency. I'd start by characterizing the failure precisely: sweep the band in small steps, note the exact frequency and field strength at which the malfunction begins, and check whether it's amplitude-dependent (a threshold effect) or truly frequency-selective. I'd also check whether the failure follows the field or the cable — rotating the device, changing cable routing, and using a near-field probe to see where the energy is actually entering.

The usual suspects are: a cable acting as an antenna and injecting common-mode current into a connector; a slot or seam in the enclosure resonating at that frequency; a high-impedance node in the analog front-end picking up the field; or a digital signal being corrupted at a clock harmonic. I'd try to correlate the failure frequency with the device's own clock harmonics and with the physical dimensions of cables and enclosure openings — a quarter-wave resonance at the failure frequency is a common explanation.

For resolution, the fix depends on the mechanism. If it's cable-borne common-mode current, a common-mode choke or a ferrite at the connector, plus better cable shielding termination, often helps. If it's an enclosure resonance, adding a gasket, changing a seam, or adding a small amount of lossy material can detune it. If it's an analog node, improving the front-end's common-mode rejection and adding a small filter at the input can raise the threshold. I'd verify the fix by re-sweeping the band and confirming margin, not just passing at the single frequency — the goal is to move the failure well outside the test band, not to squeak past one point.

**Possible follow-ups:**
- How would you distinguish between a fix that genuinely improves immunity and one that just shifts the failure frequency?
- What would you do if the fix required a board respin and the test lab slot was already booked?

## Q3: How would you approach determining which IEC 60601-2 particular standards apply to a device that combines two clinical functions — for example, a device that both monitors a physiological parameter and delivers a therapy — and how would you resolve conflicts between the general standard and the particular standards?

**Answer:** The general standard, IEC 60601-1, always applies. The 60601-2 series contains particular standards, each scoped to a specific device type or function, and the first step is to read the scope clause of each candidate standard carefully — the scope tells you whether your device falls within it, and it's not always obvious from the title. For a combined device, more than one particular standard can apply simultaneously, and the standard itself usually says so: many particular standards state that they take precedence over the general standard for the clauses they cover, and where two particular standards both apply, you have to satisfy both unless one explicitly excludes the other.

The practical approach is to build a clause-by-clause matrix. List the clauses of the general standard, then for each applicable particular standard, note whether it modifies, replaces, or adds to that clause. Where a particular standard tightens a limit — say, a stricter leakage current limit for a device that contacts the heart — the tighter limit governs. Where two particular standards appear to conflict, the resolution is usually to apply the more stringent requirement, and to document the rationale in the risk management file and the test plan so a reviewer can follow the reasoning. If the conflict is genuinely ambiguous, that's a question for the test lab or a regulatory consultant before you commit to a design, not something to resolve by guessing.

I'd also check the collateral standards — 60601-1-2 for EMC, 60601-1-6 for usability, 60601-1-8 for alarms, 60601-1-11 for home healthcare — because those apply based on the environment and features, not the device type, and they're easy to overlook when you're focused on the 60601-2 series.

**Possible follow-ups:**
- How would you document the applicability decision so it survives a regulatory review?
- What would you do if a particular standard's scope was ambiguous for your device?

## Q4: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The file should be a living record that grows with the design, not a retrospective compilation. I'd set it up at the start with the risk management plan, which defines the scope, the process, the criteria for risk acceptability, and the roles — that plan is what makes the rest of the file coherent. Then the hazard analysis and risk estimation are done iteratively: as the architecture takes shape, as FMEA or fault tree analysis is performed, and as verification results come in, the file is updated. The key is that each risk control measure is traceable to a design input or output, and each verification of that control is traceable back to the hazard it addresses.

Structurally, I'd keep the file organized around the risk management process rather than around document types: the plan, the hazard identification and risk estimation records, the risk control measures with their verification evidence, the residual risk evaluation, and the overall risk-benefit conclusion. A traceability matrix that links hazards to risk controls to verification evidence to design outputs is what makes the file auditable — a reviewer should be able to pick any hazard and follow the thread to the evidence that the control works.

The failure mode I'd actively avoid is the "big binder at the end" — where the file is assembled after the design is frozen, the traceability is reconstructed from memory, and gaps get papered over. To prevent that, I'd schedule risk management reviews at the same cadence as design reviews, so the file is updated at each milestone and the traceability is maintained incrementally. That also means the file reflects the design as it actually is, including changes, rather than a snapshot that's already stale.

**Possible follow-ups:**
- How would you handle a risk control that was verified but later found to be ineffective in the field?
- What's the difference between the risk management file and the design history file, and how do they relate?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** I'd start by understanding the request precisely — what clinical problem it solves, how often it occurs, and what the consequence is if it isn't addressed. A usability change that prevents a use error with patient harm potential is a different proposition from one that's a convenience improvement, and the risk management file is where that distinction gets made concrete. I'd ask the clinical team to articulate the hazard or use scenario, and I'd check whether it's already covered by an existing risk control or whether it's a new hazard.

Then I'd evaluate the options rather than treating it as binary. A hardware revision is one path, but there may be others: a firmware or UI change that achieves the same clinical outcome without touching the board; a labeling or training change; a change that can be deferred to a post-market software update if the device supports it; or a partial change that addresses the most critical part of the request now and the rest later. I'd also quantify the actual schedule and cost impact — not just "three months" but what specifically slips, whether the regulatory submission can be staged, and whether there's a predicate or a modular approval path that reduces the impact.

My response to the clinical team would be transparent: here's what we can do now, here's what it costs, here's the risk of doing it versus not doing it, and here's my recommendation. If the change is safety-relevant, the recommendation is to do it, and the schedule impact is the cost of doing the right thing. If it's not safety-relevant, I'd propose deferring it and documenting the decision with the rationale, so it's a conscious trade-off rather than a silent omission. Either way, the decision and its rationale go into the design history file.

**Possible follow-ups:**
- How would you handle it if the clinical team disagreed with your assessment that the change wasn't safety-relevant?
- What would you do if the change could be made in firmware but the device's software safety classification made that path expensive?