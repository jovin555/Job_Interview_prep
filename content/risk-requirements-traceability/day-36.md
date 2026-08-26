# risk-requirements-traceability — Day 36

## Q1: How would you approach establishing traceability for a risk control measure that is implemented as a hardware analog circuit with a trim potentiometer that must be calibrated during manufacturing — where the calibration setting itself is part of the risk control, and the verification test must confirm both the circuit function and the calibration tolerance?

**Answer:** This is a good example of a risk control that has both a design element and a manufacturing element, and the traceability needs to capture both. I'd approach it in layers. First, in the risk management file, the risk control would be documented as the complete measure: the analog comparator circuit *plus* the calibrated trim setting that places the trip point within the specified tolerance band. The hazard being mitigated, the fault condition, and the required performance (e.g., the trip point must be within X% of nominal) would all be captured there.

From a requirements perspective, I'd split this into two linked requirements. The first is a design requirement: the circuit shall implement a comparator with a trip point adjustable over a specified range. The second is a manufacturing requirement: the calibration procedure shall set the trip point to within the specified tolerance. These are different requirements because they're verified differently and owned by different groups — design engineering and manufacturing/test engineering.

For verification, I'd want three levels of evidence. First, design verification: on engineering units, demonstrate that the circuit can be calibrated to the specified tolerance and that the trip point is stable over temperature and supply variation. This proves the design is capable of meeting the requirement. Second, manufacturing process validation: demonstrate that the production calibration procedure, as written, consistently produces units within tolerance. This proves the process works. Third, production verification: on each unit, the calibration step itself records the final trip point value, and that record becomes the objective evidence that the control is correctly set on that specific unit.

The traceability matrix would then show: hazard → risk control (comparator + calibration) → two requirements (design and manufacturing) → three verification activities (design verification, process validation, production calibration record). The key insight is that the calibration setting is not just a manufacturing convenience — it's part of the safety function, so it needs its own traceability path, not just a note in the assembly instructions.

**Possible follow-ups:**
- How would you handle a situation where the trim potentiometer drifts out of tolerance over the product's lifetime, and how would that affect the traceability?
- What if the calibration is done by an automated test system that also performs other functional tests — how would you ensure the calibration data is captured as objective evidence for this specific risk control?

---

## Q2: How would you approach creating a traceability scheme that connects risk control measures to requirements when the system has a safety mechanism that can be bypassed or overridden by a clinician — for example, a "disable alarm" button on a patient monitoring device — and the override itself introduces a new hazard?

**Answer:** This is a classic case where the risk control creates a secondary risk, and the traceability scheme needs to capture that chain explicitly. I'd start by documenting in the risk management file that the override is itself a risk control measure — it mitigates the hazard of nuisance alarms causing alarm fatigue or causing the clinician to ignore alarms. But the override introduces a new hazard: a critical alarm being silenced when the clinician is not attending to the patient.

The traceability would then have two parallel paths. The first path traces the override function as a risk control: hazard (alarm fatigue) → control (clinician can silence alarm) → requirement (the device shall provide a means to temporarily silence audible alarms) → verification (test that the silence function works as specified). The second path traces the new hazard introduced by the override: hazard (critical alarm silenced during patient risk) → control (the override shall be temporary, shall be visually indicated, and shall not silence critical alarms) → requirements (e.g., "the alarm silence function shall automatically re-enable after X minutes," "a visual indicator shall be displayed whenever alarms are silenced," "alarms of severity level 1 shall not be silencable") → verification for each of those requirements.

The important design principle is that the override must have a time limit, a clear visual indication, and exclusions for the most critical alarms. Each of those design features is itself a risk control measure for the secondary hazard, and each needs its own traceability path. The traceability matrix would show the full chain: original hazard → override control → secondary hazard → secondary controls → requirements → verification. This is sometimes called a "risk control chain" or "cascading risk control" in the risk management file.

I'd also want the traceability to capture the human factors element. The verification for the override should include usability testing to confirm that the clinician understands the override state and its implications — that's part of verifying the risk control is effective, not just that the button works.

**Possible follow-ups:**
- How would you determine whether the override should be a hardware switch, a software button, or a combination, and how would that decision affect traceability?
- How would you handle the traceability if the override behavior differs between operating modes — for example, the override is allowed in normal mode but not in a critical care mode?

---

## Q3: How would you approach handling a situation where a risk control measure is traced to a verification activity, but the verification activity is a software unit test that runs on a host PC (not the target hardware), and the risk control involves timing behavior that depends on the microcontroller's clock speed and interrupt latency?

**Answer:** This is a fundamental question about verification fidelity — whether the test environment is representative of the production environment for the specific behavior being verified. My first step would be to understand exactly what aspect of the risk control is being verified by the host PC test. If the risk control is a software timeout that must trigger within a certain window, and the timing depends on the microcontroller's clock speed and interrupt latency, then a host PC test is likely not adequate for the timing aspect.

I'd break the verification into two parts. The first part is the logic of the risk control: does the firmware implement the correct state transitions, the correct comparison logic, the correct response when the timeout expires? That can be verified on the host PC with unit tests, because the logic is independent of the hardware timing. The second part is the timing behavior: does the timeout actually fire within the required window on the target hardware, given the actual clock speed, interrupt priorities, and other tasks competing for CPU time? That must be verified on the target hardware or on hardware that is representative in terms of clock speed and interrupt behavior.

So my approach would be to require both: a host PC unit test for the logic, and a target hardware test for the timing. The traceability matrix would show the risk control traced to two verification activities, each covering a different aspect. The host PC test verifies the logic; the target hardware test verifies the timing. If the risk analysis specifies a particular timing tolerance, the target hardware test must demonstrate the timeout fires within that tolerance under worst-case conditions — for example, with the highest-priority interrupt firing at the same time.

If the team argues that the host PC test is sufficient because the logic is correct, I'd push back by asking: what is the failure mode the risk control is mitigating? If the failure mode is "motor continues running after sensor signal is lost," then the timing of the shutdown is critical — a motor that shuts down 500ms late may still cause harm. The host PC test cannot demonstrate that the timing is met on the actual hardware, because the host PC has a different clock speed, different interrupt latency, and different scheduling behavior.

**Possible follow-ups:**
- How would you determine what "representative hardware" means for the timing verification — is a development board with the same microcontroller sufficient, or do you need the actual production PCB?
- What if the timing requirement has a wide tolerance — for example, the shutdown must occur within 1 second, and the firmware typically responds in 10ms — would you still require target hardware testing?

---

## Q4: How would you approach determining whether a risk control measure that is implemented as a hardware fuse (one-time, non-resettable) needs to be verified on every production unit, or whether verification on a sample basis is sufficient?

**Answer:** This is a question about the difference between design verification and production quality control, and the answer depends on the failure mode the fuse is mitigating and the consequences of a fuse not working. Let me think through the logic.

First, there's the design verification question: does the fuse, as selected and placed in the circuit, provide the intended protection? That's verified during design verification — you demonstrate on engineering units that the fuse blows within the specified current and time characteristics, and that it protects the downstream circuitry. That's a one-time design activity, not a per-unit activity.

Then there's the production question: is the fuse correctly installed on every unit? The risk here is a manufacturing defect — a fuse that is not soldered correctly, a wrong-value fuse placed by mistake, or a fuse that is damaged during assembly. The question is whether you need to test every unit or whether sampling is sufficient.

The key factors are: the severity of the hazard if the fuse fails to protect, the likelihood of a manufacturing defect, and the detectability of the defect. If the fuse is protecting against a hazard with high severity — for example, preventing a battery fire — then the consequences of a defective fuse are severe. If the manufacturing process has a known failure rate for fuse installation, that affects the sampling plan. And if the defect is detectable by a simple continuity test or a visual inspection, that's different from a defect that requires a full functional test to detect.

In practice, I'd approach it this way. The fuse's protective function — that it blows at the right current — is verified during design verification and doesn't need to be re-verified on every unit. But the correct installation of the fuse — that it's the right value, correctly soldered, and present — should be verified on every unit, because a missing or wrong fuse is a manufacturing defect that could defeat the risk control. This verification could be a simple continuity check or a visual inspection, not a full functional test. The traceability would show the risk control traced to two verification activities: design verification of the fuse's protective characteristics, and production verification of correct installation on every unit.

If the team proposes sample-based verification, I'd ask what the sampling plan is based on and what the acceptance criteria are. Sampling is appropriate for attributes that are statistically controlled, but for a safety-critical component like a fuse, the cost of a single defective unit may be unacceptable. I'd also consider whether the fuse is part of a single-fault-tolerant design — if there's redundancy, sampling might be more defensible.

**Possible follow-ups:**
- How would you document the rationale for the verification approach in the risk management file, so that a regulator or auditor can understand why sample-based verification was acceptable?
- What if the fuse is a one-time device that can't be tested without destroying it — how would you verify it on every unit without blowing the fuse?

---

## Q5: (Behavioral) Imagine you're leading a project where the systems engineer has created a traceability matrix that links every risk control measure to a verification activity, but during a review, you discover that the verification activities are all scheduled for the very end of the project, after all design work is complete. The program manager argues that this is efficient because it avoids rework — the design is finalized before testing begins. The quality manager argues that late verification means design errors are discovered too late, causing expensive rework and schedule delays. How would you resolve this disagreement?

**Answer:** I'd start by acknowledging that both perspectives have merit, and then I'd try to reframe the discussion from "when do we test" to "what are we trying to learn at each stage of the project." The program manager is right that testing a finalized design avoids the cost of re-testing after design changes. But the quality manager is also right that if a design error is only discovered at the end, the rework is much more expensive than if it had been caught earlier.

The resolution is to distinguish between different types of verification and schedule them appropriately. Some verification activities are inherently design verification — they confirm that the design meets the requirements, and they should happen as soon as the design is mature enough to test. For example, if a risk control depends on a hardware comparator's trip point, you want to verify that early, on a prototype, because if the design is wrong, you need to know before you commit to the PCB layout. Other verification activities are production verification — they confirm that the manufactured units meet the requirements, and they happen at the end by definition.

So I'd propose a verification strategy that layers testing throughout the project. Early in the project, you do design verification on prototypes — bench tests, simulations, and analysis that confirm the design approach is sound. As the design matures, you do more integrated verification — testing on engineering units that are representative of the final design. At the end, you do the formal verification campaign on production-representative units, which provides the objective evidence for the design history file.

The key is that the traceability matrix should show not just *what* is verified, but *when* in the project it's verified, and *what* the verification is intended to demonstrate at that stage. A risk control that depends on a novel circuit topology should have early verification to de-risk the design. A risk control that depends on manufacturing processes — like a calibration step — should have verification at the end, because the process doesn't exist until production is set up.

I'd also point out that the cost of rework isn't just the cost of re-testing — it's the cost of redesign, re-layout, re-fabrication, and the schedule impact of all of that. Catching a design error early, when it's still a schematic change, is far cheaper than catching it after the PCB is fabricated and assembled. So the question isn't "test early or test late" — it's "what do we need to learn at each stage to avoid expensive rework later?"

In practice, I'd propose a verification plan that includes early design verification on prototypes, intermediate verification on engineering units, and final verification on production-representative units, with the traceability matrix showing which risk controls are verified at each stage. I'd work with the program manager to identify which risk controls are highest-risk and need early verification, and which can reasonably wait until the end.

**Possible follow-ups:**
- How would you handle a situation where the program manager agrees with early verification in principle, but the budget only allows for one round of prototype fabrication — how would you prioritize which risk controls to verify early?
- How would you ensure that early verification results are properly documented and traceable, so they can be used as evidence in the final design history file?