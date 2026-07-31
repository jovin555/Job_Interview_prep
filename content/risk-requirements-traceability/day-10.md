# risk-requirements-traceability — Day 10

## Q1: How would you approach handling a situation where a risk control measure has been implemented in hardware, but the verification test for that control is only specified at the system level, with no intermediate test at the hardware module level?

**Answer:** This is a common gap in multi-level traceability. The first step is to recognize that a system-level test may be the ultimate proof, but it's often insufficient for isolating failures or for efficient debugging. I would approach this by asking what the system-level test actually demonstrates. If the system test passes, does it prove the hardware control works, or could it pass for other reasons (e.g., the fault never actually occurred because of some other protection)? If the system test fails, can you tell whether the hardware control failed, or could it be a test setup issue, a firmware interaction, or a wiring problem?

The right approach is to establish a verification hierarchy. The system-level test verifies the integrated behavior — that the hazard is mitigated in the context of the full device. But you also want a hardware-level test that directly stresses the specific control mechanism — for example, injecting a fault at the input of the protection circuit and confirming the output responds correctly. This gives you diagnostic power and isolates the hardware contribution from the system contribution.

I would also look at the risk management file to see what failure mode the control is mitigating. If the hazard scenario involves a specific fault condition (e.g., a short circuit on a particular rail), the hardware-level test should reproduce that fault condition as directly as possible. The system-level test then confirms that, in the context of the full device, the hardware response actually prevents the hazardous outcome.

Finally, I would document the relationship between these two levels of verification in the traceability matrix — showing that the hardware-level test verifies the control mechanism itself, while the system-level test verifies the hazard mitigation. Both are needed, but they answer different questions.

**Possible follow-ups:**
- What if the hardware module is a sealed assembly that can't be bench-tested in isolation? How would you verify the control then?
- How would you decide whether a system-level test alone is sufficient for a particular risk control measure?

---

## Q2: How would you approach tracing a risk control measure that is implemented as a combination of hardware and firmware — for example, a hardware sensor that detects an over-temperature condition and firmware that decides to shut down a motor — when the hardware and firmware teams maintain separate requirements documents?

**Answer:** This is where a clear traceability architecture becomes essential. The key insight is that the risk control measure itself is a system-level concept — it doesn't belong exclusively to either the hardware or firmware requirements document. I would define the risk control measure at the system level in the risk management file, then trace it down to two separate design requirements: one in the hardware document (e.g., "the temperature sensor shall output a signal proportional to temperature with accuracy ±2°C over the range 0–100°C") and one in the firmware document (e.g., "the firmware shall initiate motor shutdown within 100ms of detecting a temperature reading above 85°C").

The critical piece is the interface between the two. I would ensure there's an explicit interface requirement — captured in an ICD or interface section of one of the documents — that defines how the hardware signal is presented to the firmware (e.g., voltage range, digital format, sampling rate). Without this, the hardware team might design a sensor that outputs a 0–3.3V analog signal, while the firmware team assumes a digital I2C interface. The traceability link between the hardware requirement and the firmware requirement goes through this interface definition.

For verification, I would expect three levels of testing: a hardware test that verifies the sensor output is accurate across temperature range, a firmware test that verifies the shutdown logic responds correctly to simulated sensor inputs (including boundary conditions like exactly 85°C and transient spikes), and a system-level test that verifies the integrated behavior — actual temperature rise, sensor response, firmware decision, and motor shutdown. Each test maps to a different level of the traceability chain.

**Possible follow-ups:**
- How would you handle the situation where the hardware team changes the sensor interface (e.g., from analog to digital) late in the project?
- Who should own the system-level traceability link between the hardware and firmware requirements — the systems engineer, the risk manager, or someone else?

---

## Q3: How would you approach determining whether a risk control measure that is implemented purely in firmware — such as a software-based interlock that prevents simultaneous operation of two motors — needs to be verified on the actual production hardware, or whether testing on a development board with the same microcontroller is sufficient?

**Answer:** This is fundamentally a question about test fidelity and what the verification is actually proving. The firmware logic itself — the state machine that prevents simultaneous motor operation — can be thoroughly tested on a development board or even in a host-based test environment, because the logic is independent of the specific hardware peripherals. You can verify all the state transitions, timing edge cases, and fault conditions in a controlled environment where you can inject inputs deterministically.

However, there are aspects of the implementation that are hardware-dependent. The firmware reads motor status from specific GPIO pins or a motor driver IC over SPI. The timing of those reads, the behavior of the interrupt controller, the watchdog configuration, and the power-on reset behavior are all hardware-specific. A development board with the same microcontroller but different peripherals might not exercise the same timing characteristics or failure modes.

My approach would be to split the verification into two parts. First, verify the logic thoroughly in a host-based or development-board environment — this gives you comprehensive coverage of the decision logic, boundary conditions, and error handling. Second, verify the integration on production-representative hardware — confirming that the firmware correctly reads the actual motor status signals, that the timing meets the requirements, and that the interlock actually prevents the hazardous condition in the real system.

The key question is what the risk analysis says about the failure mode. If the hazard is "both motors operate simultaneously," the verification must demonstrate that this cannot happen in the actual device. A development board test can prove the logic is correct, but only a production-hardware test can prove the implementation is correct — that the firmware actually receives the right signals, makes the right decision, and commands the right output in the real system.

**Possible follow-ups:**
- What if the production hardware isn't available until late in the project? How would you manage the verification schedule?
- How would you document the difference between "logic verification" and "integration verification" in the traceability matrix?

---

## Q4: How would you approach creating a traceability scheme that connects risk control measures to requirements when the same risk control measure is implemented differently across multiple product variants — for example, one variant uses a hardware watchdog timer while another uses a firmware-based watchdog, but both mitigate the same hazard?

**Answer:** This is a classic product-line traceability challenge. The key principle is to maintain traceability at the level of the risk control measure's intent, not its implementation. The risk management file should define the risk control measure in terms of what it must achieve — for example, "the system shall detect a firmware hang and reset the processor within 500ms." This is the common thread across variants.

Below that, each variant has its own design requirements. Variant A has a hardware requirement: "a hardware watchdog timer shall be configured with a timeout of 400ms and shall assert reset when not serviced." Variant B has a firmware requirement: "the firmware shall implement a software watchdog that monitors the main loop and resets the processor if the loop stalls for more than 400ms." Both trace up to the same risk control measure, but they have separate design requirements and separate verification activities.

The traceability matrix needs to handle this with a variant dimension. I would structure it so that the risk control measure row lists all variants, and each variant has its own column for design requirement and verification. This makes it easy to see at a glance which variants have complete traceability and which are missing a link.

The tricky part is managing changes. If the risk analysis changes — say, the hazard severity is reassessed and the required response time changes from 500ms to 200ms — you need to update the risk control measure definition, then check each variant's design requirement and verification to see if they still comply. This is where a good traceability tool or a well-structured spreadsheet with variant columns becomes essential.

I would also consider whether the variants are similar enough to share verification activities. If the hardware watchdog in Variant A and the firmware watchdog in Variant B are both verified by the same system-level test (e.g., "induce a firmware hang and confirm the system resets within 500ms"), then you can share that verification record across variants. But if the test methods differ — for example, the hardware watchdog requires fault injection at the watchdog IC, while the firmware watchdog requires corrupting the firmware's loop counter — then you need separate verification records.

**Possible follow-ups:**
- How would you handle a situation where a new variant is introduced mid-project? What steps would you take to ensure traceability is complete?
- How would you present the variant traceability to a regulatory auditor in a way that's clear and demonstrates completeness?

---

## Q5: (Behavioral) Imagine you're leading a project where the test engineer has created a verification test for a risk control measure, but during a dry run, the test passes even when the risk control is deliberately disabled. The test engineer argues that the test is still valid because it exercises the system under normal conditions and the risk control is "just a safety net." The quality manager insists the test must fail when the control is disabled, to prove the test is actually capable of detecting the failure. How would you resolve this disagreement?

**Answer:** The quality manager is fundamentally correct, and I would support that position, but I would also acknowledge the test engineer's underlying concern. A verification test that passes regardless of whether the risk control is active is not actually verifying anything — it's a false positive. The purpose of verification is to demonstrate that the control works, and you can't demonstrate that if the test can't distinguish between "control present and working" and "control absent."

However, the test engineer's point about the test exercising normal conditions is worth addressing. There are two distinct things being tested: the system's normal operation (which should be unaffected by the risk control) and the risk control's function under fault conditions. These need different test approaches. The normal-operation test confirms the control doesn't interfere with functionality; the fault-injection test confirms the control actually mitigates the hazard.

I would propose a two-part approach. First, modify the test to include a fault-injection step — deliberately disable the control and confirm the test detects the failure. This proves the test has discriminating power. Second, add a separate test that confirms normal operation is unaffected when the control is active. This addresses the test engineer's concern that the control shouldn't interfere with normal function.

I would also use this as an opportunity to review the test methodology more broadly. If a test can't detect the absence of the control, it's likely that the test isn't actually stressing the right conditions. This might indicate that the test needs to be redesigned to inject the specific fault condition identified in the risk analysis, rather than just running the system under nominal conditions and checking that nothing bad happens.

The resolution isn't about who's right — it's about recognizing that both perspectives are valid but address different questions. The test needs to prove both that the control works when needed and that it doesn't interfere when not needed. I would document both test cases in the verification plan and ensure the traceability matrix reflects both aspects.

**Possible follow-ups:**
- What if adding fault injection to the test significantly increases test time and cost? How would you justify the added expense?
- How would you handle a situation where the test engineer has already run the test and recorded a "pass" result, and now you need to decide whether to re-run it with the corrected methodology?