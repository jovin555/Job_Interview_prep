# medical-devices — Day 79

## Q1: How would you approach designing the patient leakage current measurement path for a device that has both BF-type and CF-type applied parts, and how would you decide which measurements are actually required?

**Answer:** The first step is to map the applied parts and their classifications against the standard, because the measurement set follows directly from that classification rather than from the device as a whole. A BF-type applied part has a patient leakage limit under normal condition and a looser limit under single-fault condition; a CF-type applied part is held to a much tighter limit because it is intended for direct cardiac contact. If a single enclosure carries both, the enclosure and its isolation scheme generally have to satisfy the stricter CF requirement for anything that could come into contact with the CF part, so I would treat the CF limit as the governing constraint for shared circuitry.

For the measurement path itself, the key idea is that the standard defines a specific measurement network — a defined impedance that represents the human body — inserted between the applied part and earth, with the device powered at nominal mains voltage and then at 110% of the highest rated voltage. I would build the test setup so that each applied part can be measured individually and in combination, because leakage can add when multiple applied parts are connected to the same patient. The measurement instrument has to be capable of true-RMS measurement at the relevant frequencies and have the input impedance and bandwidth the standard calls for; a general-purpose multimeter is usually not adequate.

Deciding which measurements are actually required comes down to three questions: which applied parts exist, what classification each carries, and which fault conditions the standard requires me to simulate. For a device with both BF and CF parts, that typically means patient leakage for each part under normal condition, patient leakage under single-fault condition (open earth, open supply conductor, and so on), and — where the CF part is involved — the tighter CF limits apply. I would also check whether the device has any patient connections that are not classified as applied parts, since those still need to be evaluated for touch current.

The practical discipline is to write the measurement matrix down before touching the bench: rows for each applied part, columns for each condition, cells for the applicable limit. That prevents the common failure mode of measuring the easy cases and assuming the harder ones will pass.

**Possible follow-ups:**
- If the BF and CF applied parts share a common reference node, how does that affect which limit you apply?
- How would you verify that your measurement setup itself isn't contributing to the reading?

## Q2: During IEC 60601-1-2 immunity testing, a device passes radiated RF immunity at most frequencies but shows a reproducible malfunction in a narrow band around one specific frequency. How would you approach diagnosing and resolving it?

**Answer:** A narrow-band failure is a strong hint that something in the device is resonant at that frequency — either a cable acting as an antenna, a trace or loop with a resonant length, or an enclosure slot. The first thing I would do is characterize the failure precisely: sweep in fine steps around the problem frequency to find the exact center and the bandwidth over which the malfunction occurs, and note whether it depends on cable orientation, cable routing, or the position of the device relative to the field. That tells me whether I'm looking at a cable-coupled problem or a directly-coupled one.

Next I would try to localize it. If the device has external cables, I would repeat the test with cables dressed differently, with ferrites clamped at various points, and with cables shortened or looped. A ferrite that fixes it points to common-mode current on that cable. If the failure persists with all cables removed or dressed in a controlled way, I would look inside the enclosure — a slot or seam whose dimension is near a half-wavelength at that frequency can act as a slot antenna, and the fix is usually to break up the slot with additional fasteners, gaskets, or a conductive seam treatment.

For the circuit itself, I would use a near-field probe to sniff around the board while the field is applied, looking for the node where the disturbance is largest. Once I find the susceptible node, the fix is usually one of: adding a small series impedance or shunt capacitance to filter the disturbance, improving the return path so the disturbance doesn't flow through a sensitive reference, or adding local decoupling. If the disturbance is getting in through a connector, a feed-through capacitor or a common-mode choke at the connector is often more effective than anything on the board.

The important thing is to fix the coupling path rather than just the symptom. If I only add a filter at the point where the malfunction shows up, I may be leaving the actual coupling mechanism in place and it will reappear at a different frequency or in a different test configuration. I would verify the fix by re-sweeping the full band, not just the problem frequency, and by testing with the worst-case cable configuration.

**Possible follow-ups:**
- How would you decide between fixing the coupling path and adding a filter at the susceptible node?
- If the failure only occurs with one specific cable type, what does that tell you about the mechanism?

## Q3: How would you approach structuring a risk management file so that it stays useful and auditable throughout a project, rather than becoming a document assembled at the end?

**Answer:** The file has to be a living record of decisions, not a retrospective summary. The way I would structure it is around the hazard analysis as the spine: each identified hazardous situation links forward to the risk estimate, the risk control measure, the verification that the control was implemented, and the residual risk evaluation. Everything else — the design inputs, the verification results, the complaints — hangs off that spine as evidence.

Practically, that means the risk management file is organized so that any single hazard can be traced end-to-end without hunting through other documents. I would keep a hazard log that is updated at each design review, with a clear owner and status for each entry, rather than a static table that gets filled in once. When a design change happens, the first question is which hazards it touches, and the log should make that answerable in minutes.

The other structural choice that matters is separating the risk management plan from the risk management report. The plan states the scope, the method, the acceptance criteria, and the responsibilities up front — before the analysis starts. The report is the summary at the end that says the process was followed and the residual risks are acceptable. If the plan is written after the fact, the acceptance criteria tend to get reverse-engineered to match whatever the design ended up doing, which is exactly the failure mode auditors look for.

I would also make sure the file captures the rationale for decisions, not just the decisions. A risk control that was considered and rejected, with a note on why, is often more valuable during an audit than the control that was chosen, because it shows the analysis was real. And I would keep the file in a format that supports version control and review — a document that only one person can edit is a document that will drift out of date.

**Possible follow-ups:**
- How do you keep the risk file current when the design changes late in the project?
- What's the difference between a risk control measure and a risk control verification, and why does the distinction matter in the file?

## Q4: How would you approach deciding whether a given software failure in a medical device should be classified as a safety-related failure requiring formal risk controls, versus a non-safety usability or reliability issue?

**Answer:** The decision starts from the harm, not from the software. The question isn't "how bad is this bug" but "if this bug occurs in the field, what hazardous situation can it lead to, and what's the severity of the harm that could result?" That means I trace the failure forward through the device's function to the patient or operator. A display glitch that a clinician would immediately notice and work around is a different category from a display glitch that could cause a clinician to miss a critical alarm.

The framework I would use is the same one the risk management process uses: identify the hazardous situation the failure could contribute to, estimate the severity and probability, and compare against the acceptance criteria in the risk management plan. If the failure can contribute to a hazardous situation that exceeds the acceptance criteria, it's safety-related and needs a formal risk control — which might be a software control, a hardware control, or a labeling/instruction control. If it can't, it's a reliability or usability issue and gets handled through normal defect tracking.

The subtle cases are the ones where the failure is only dangerous in combination with something else — a sensor failure plus a specific patient condition, or a software failure plus a user action. Those are exactly the cases where the risk analysis has to be done carefully, because it's easy to dismiss each contributing factor as "unlikely" and miss that the combination is not. I would want the analysis to be explicit about the combination, not just the individual failure.

One thing I would avoid is using the software safety classification as a shortcut for this decision. The classification under IEC 62304 is about the software's contribution to hazardous situations, and it's a useful input, but it doesn't replace the hazard-by-hazard analysis. A Class B piece of software can still have a specific failure that needs a specific control.

**Possible follow-ups:**
- How would you handle a failure that only becomes hazardous in combination with a user error?
- If a failure is classified as non-safety, what documentation still needs to exist for it?

## Q5: You're the lead engineer on a project where the clinical team has requested a usability change late in development that would require a hardware revision and push the regulatory submission out by several months. How would you evaluate and respond to the request?

**Answer:** The first thing I would do is separate the clinical need from the proposed solution. The clinical team is asking for a change because of a problem they're seeing or anticipating; the specific change they've proposed is one way to address it, but it may not be the only way. So I would sit down with them and get to the underlying need — what's the clinical scenario, what goes wrong without the change, how often does it happen, and what's the consequence. That conversation often reveals that a smaller change, or a change that can be made in firmware or labeling, addresses most of the need.

If the need is real and the only way to address it is a hardware revision, then the decision becomes a trade-off between the clinical benefit and the cost of the delay. I would want to quantify both sides as much as possible: what's the clinical risk of shipping without the change, and what's the cost of the delay — not just schedule, but the risk of losing a market window, the cost of re-verification, and the impact on other projects. I would bring that trade-off to the project's decision-makers rather than making the call unilaterally, because the clinical and business considerations are outside my authority as the lead engineer.

There's also a middle path worth considering: ship the current design with a documented limitation or a workaround, and address the usability issue in a follow-on revision. That's not always acceptable — if the issue is a safety concern, it isn't — but if it's a usability improvement that clinicians can work around, it may be the right answer. The key is to make the decision explicitly, with the clinical team's input, rather than letting the schedule pressure make it by default.

Whatever the outcome, I would document the decision and the rationale. If the change is deferred, the risk file and the design history file should reflect that the issue was identified and consciously deferred, with the reasoning. That protects the project during an audit and makes sure the issue doesn't get lost.

**Possible follow-ups:**
- How would you handle it if the clinical team's need is real but the proposed change isn't the right solution?
- What would you do if the decision-makers want to defer the change but you believe it's a safety issue?