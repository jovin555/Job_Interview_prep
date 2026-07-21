# risk-requirements-traceability — Day 2

## Q1: How would you structure a requirements traceability matrix (RTM) for a medical device development project, and what key relationships would you capture beyond simple "requirement-to-test" links?

**Answer:** I would structure the RTM as a living document that captures bidirectional traceability across the entire development lifecycle. Beyond the basic requirement-to-test-case links, I'd include:

- **Source-to-requirement traceability**: Each requirement should link back to its origin — whether that's a user need, a regulatory standard (e.g., IEC 60601 clause), a risk control measure from the ISO 14971 risk management file, or a system-level specification.

- **Requirement-to-design-element traceability**: Each requirement should map to specific architectural components, software modules, hardware blocks, or interface definitions. This ensures you can assess the impact of a requirement change on the design.

- **Requirement-to-verification traceability**: Not just to test cases, but also to analysis, inspection, and demonstration methods. Some requirements (e.g., "the device shall not exceed 45°C surface temperature") may be verified by thermal analysis rather than a single test.

- **Risk-control-to-requirement traceability**: Every risk control measure documented in the DFMEA or hazard analysis should be traceable to one or more requirements that implement it, and from those requirements to the verification activities that confirm effectiveness.

- **Bidirectional links**: The matrix must work both ways — from a requirement forward to its verification, and from a test result backward to the requirement it validates. This is critical during root-cause investigations when a test failure occurs.

I would maintain this in a requirements management tool (like DOORS or Jama) rather than a spreadsheet, as the relationships become complex and need version control, impact analysis, and audit trail capabilities.

**Possible follow-ups:** How would you handle a situation where a single test case verifies multiple requirements? How do you maintain traceability when requirements change late in development?

---

## Q2: How would you approach integrating ISO 14971 risk management activities with requirements engineering in a medical device project?

**Answer:** I would treat risk management and requirements engineering as parallel, interdependent workflows rather than sequential handoffs. The key integration points are:

1. **Initial hazard identification informs requirements**: During the preliminary hazard analysis, identified hazards and hazardous situations should directly generate risk control requirements. For example, if a hazard analysis identifies "overheating due to battery charger failure" as a risk, that should produce a requirement like "the charging circuit shall include independent over-temperature protection with automatic shutdown."

2. **Risk control measures become verifiable requirements**: Each risk control measure selected during risk evaluation must be translated into a specific, testable requirement. This ensures the risk management file doesn't exist in isolation — it's directly linked to what the engineering team builds and tests.

3. **Verification results feed back into risk assessment**: When a requirement derived from a risk control measure fails verification, that triggers a re-evaluation of the associated risk. The residual risk may no longer be acceptable, requiring additional controls or design changes.

4. **Traceability between risk items and requirements**: I'd maintain a clear mapping where each row in the risk management file (hazard → hazardous situation → harm → risk control → verification) has corresponding entries in the requirements database. This is essential for regulatory audits — an auditor will want to see that every identified risk has been addressed and verified.

5. **Change management is unified**: Any proposed requirement change should trigger an impact assessment on the risk management file, and vice versa. A design change that affects a risk control measure must be evaluated before implementation.

**Possible follow-ups:** How do you handle residual risk acceptance documentation in the requirements traceability? What if a risk control measure is implemented through a process (like a manufacturing test) rather than a design feature?

---

## Q3: During a design review, you discover that a critical safety requirement has no corresponding verification activity in the test plan. How would you handle this situation?

**Answer:** I would treat this as a quality system finding that needs immediate attention. My approach would be:

1. **Assess the gap**: First, determine whether the requirement is truly untested or whether verification is happening through another mechanism (analysis, inspection, or a different test case that implicitly covers it). Review the requirement's origin — is it from a risk control measure, a regulatory standard, or a user need? This helps prioritize the response.

2. **Determine verification method**: For the missing verification, I'd work with the test engineering team to define an appropriate method. Some requirements may be verifiable by analysis (e.g., worst-case timing calculations), inspection (e.g., labeling requirements), or a new test case. The method must be objective and repeatable.

3. **Update the traceability matrix**: Add the link between the requirement and the new verification activity. If the requirement is safety-critical, I'd also check whether the risk management file needs updating — the absence of verification means the risk control measure hasn't been confirmed effective.

4. **Evaluate schedule and resource impact**: If a new test case requires additional hardware, test fixtures, or lab time, this needs to be communicated to project management. For safety-critical gaps, I'd advocate for delaying release rather than accepting untested requirements.

5. **Root cause the gap**: After addressing the immediate issue, I'd investigate how the requirement ended up without verification. Was it a process failure in the requirements management workflow? A handoff issue between systems engineering and test? This prevents recurrence.

**Possible follow-ups:** What if the requirement is impossible to test directly (e.g., "the device shall not cause patient injury under any single fault condition")? How would you handle a situation where the test would require destructive testing of every production unit?

---

## Q4: How would you approach creating a requirements traceability strategy for a system that combines hardware, firmware, and wireless communication subsystems, where requirements span multiple engineering disciplines?

**Answer:** I would establish a multi-level traceability architecture that accounts for the system decomposition and interface complexity:

1. **Define a hierarchical requirements structure**: Start with system-level requirements that capture overall functionality, safety, and performance. These decompose into subsystem-level requirements for hardware, firmware, and communications. Each subsystem's requirements should be owned by the respective engineering team but managed in a shared repository.

2. **Explicitly capture interface requirements**: Cross-subsystem interfaces (e.g., the I2C bus between the sensor hardware and the firmware, or the wireless protocol between the device and the tablet application) need their own requirements and traceability. These are often where gaps occur — hardware assumes firmware handles error checking, firmware assumes hardware guarantees timing, and neither verifies the interface.

3. **Use a common identifier scheme**: All requirements across disciplines should follow a consistent numbering convention that indicates level (system, subsystem, component) and domain (HW, FW, COMMS). This makes traceability links unambiguous.

4. **Establish integration verification traceability**: Beyond unit-level tests for each subsystem, integration tests that exercise cross-subsystem interactions need their own traceability. For example, a test that verifies "the firmware shall correctly parse sensor data received over I2C" traces to both a firmware requirement and a hardware interface requirement.

5. **Implement change impact analysis across domains**: When a hardware requirement changes (e.g., a different pressure sensor with a different I2C address), the traceability matrix should immediately show which firmware and communication requirements are affected. This requires the tooling to support cross-referencing.

6. **Hold cross-functional traceability reviews**: At key milestones, bring hardware, firmware, and systems engineers together to review the traceability matrix. This catches missing links that individual teams might overlook — for instance, a firmware team might not realize a hardware timing requirement affects their interrupt service routine design.

**Possible follow-ups:** How would you handle conflicting requirements between subsystems (e.g., hardware power budget vs. firmware processing requirements)? What metrics would you use to assess the completeness of your traceability coverage?

---

## Q5: (Behavioral) Imagine you're leading a cross-functional team that has never used formal requirements traceability before. Some team members see it as unnecessary overhead that slows development. How would you gain their buy-in and implement a traceability process?

**Answer:** I would approach this as a change management challenge, not just a technical one. My strategy would be:

1. **Start with the "why"**: I'd explain traceability not as a bureaucratic exercise but as a tool that makes everyone's job easier. For the test engineer, it answers "what exactly am I testing and why?" For the firmware developer, it answers "if I change this code, what requirements might break?" For the project manager, it answers "are we done yet?" I'd use concrete examples from past projects where missing traceability caused rework or late-stage surprises.

2. **Find a pain point to solve first**: Rather than implementing a full traceability framework from day one, I'd identify one recurring problem the team faces — perhaps late-discovered requirement gaps, or difficulty proving completeness to a regulator. I'd propose a lightweight traceability approach that directly addresses that pain point. Success there builds credibility.

3. **Start small and iterate**: I'd suggest piloting traceability on one subsystem or one feature, not the entire project. Use a simple spreadsheet or a lightweight tool, not an enterprise system. Let the team experience the benefits at small scale before scaling up.

4. **Make it part of existing workflows**: Instead of adding separate traceability review meetings, I'd integrate traceability checks into existing design reviews and test plan reviews. The question becomes "do we know which requirements this design element satisfies?" rather than "fill out this separate form."

5. **Acknowledge the overhead honestly**: I'd validate their concern — yes, traceability takes effort. But I'd frame it as an investment that pays back by reducing rework, catching gaps early, and making regulatory submissions smoother. I'd also advocate for reasonable granularity: not every trivial requirement needs deep traceability, but safety-critical and regulatory requirements do.

6. **Lead by example**: I'd personally maintain traceability for my own work and show how it helped me catch an issue or communicate more clearly with another team. Peer demonstration is more persuasive than management mandate.

**Possible follow-ups:** How would you handle a team member who consistently fails to update traceability links? What would you do if upper management questions the time spent on traceability during a schedule crunch?