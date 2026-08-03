# medical-devices — Day 13

## Q1: How would you approach designing a fault injection test strategy for a medical device's firmware to verify that safety-critical monitoring functions continue to operate correctly when non-critical tasks (like data logging or UI updates) fail or consume excessive CPU time?

**Answer:** I'd start by identifying which functions are safety-critical versus non-critical, based on the hazard analysis and the device's intended use. The key concern is that a non-critical task shouldn't be able to starve or corrupt a safety-critical path. My approach would be multi-layered:

First, I'd establish the architectural separation — typically using a real-time operating system with priority-based preemptive scheduling, where safety-critical tasks run at higher priorities with bounded execution times. I'd verify this through static analysis of task priorities, stack usage, and worst-case execution time estimates.

For fault injection specifically, I'd design tests that target the failure modes most likely to affect the critical path: CPU starvation (by creating a busy-loop at a higher priority), memory exhaustion (by allocating until the heap is depleted), and resource deadlocks (by holding mutexes that critical tasks need). I'd also inject faults at the RTOS API level — for example, deliberately making a semaphore give or message queue send fail to verify the critical task handles the error gracefully.

The test harness would need to monitor that safety-critical functions — like sensor sampling, alarm generation, or therapy delivery — continue meeting their timing and accuracy requirements while faults are injected. I'd use hardware timers or logic analyzers to verify timing, and check that alarm conditions are still detected and annunciated correctly.

Finally, I'd document the traceability from each identified hazard (e.g., "failure to detect patient disconnect") to the specific fault injection test that verifies the mitigation. This ensures the test strategy is defensible in a regulatory submission.

**Possible follow-ups:** How would you decide which faults are worth injecting versus which are too unlikely to justify the effort? How would you handle the situation where a fault injection test reveals that a non-critical task can indeed block a critical one?

---

## Q2: How would you approach verifying that a medical device's enclosure and mechanical design provide adequate protection against liquid ingress, given that the device will be used in a home environment where it may be exposed to spills or cleaning fluids?

**Answer:** I'd approach this from two angles: understanding the actual use environment and then designing verification tests that reflect realistic conditions rather than just relying on generic IP ratings.

First, I'd work with the usability engineering team to understand how the device will actually be used and cleaned in a home setting. This might involve contextual inquiry or user research to see what cleaning agents are used, how the device is handled, and what spill scenarios are realistic. This informs the design input requirements — for example, whether the device needs to survive a direct spill onto a top surface, or just incidental splashing during cleaning.

From a design perspective, I'd ensure the enclosure design includes appropriate gaskets, sealed connectors, and drainage paths where needed. The mechanical design should be reviewed for potential ingress points — seams, button openings, display windows, and ventilation ports all need consideration.

For verification, I'd design a test matrix that includes: a drip test simulating spills from a certain height and volume, a spray test simulating cleaning with a damp cloth or spray bottle, and potentially an immersion test if the device could be submerged. I'd also test with representative cleaning agents — not just water — because some chemicals can degrade gaskets or seals over time. The device should be powered and operating during these tests where realistic, to verify that ingress doesn't cause electrical safety hazards or functional failures.

I'd also consider accelerated aging of the seals — for example, thermal cycling or UV exposure if the device might be used near a window — to verify the ingress protection doesn't degrade over the device's expected lifetime.

**Possible follow-ups:** What IP rating would you target, and how would you justify that choice? How would you handle a situation where the ingress protection design conflicts with the thermal management requirements?

---

## Q3: During a design review for a medical device that uses a rechargeable battery, the firmware team proposes implementing a fuel gauge using voltage-based estimation, while the hardware engineer recommends adding a coulomb-counting fuel gauge IC. How would you approach this trade-off?

**Answer:** This is a classic trade-off between simplicity and accuracy, and the right answer depends heavily on the device's requirements and use case.

Voltage-based estimation is simpler and cheaper — it requires no additional hardware and can be implemented entirely in firmware. However, it's inherently inaccurate during load transients because battery voltage sags under load and recovers when the load is removed. This makes it particularly problematic for medical devices with variable current draw — like a device that has periodic high-current events (e.g., a motor or wireless transmission) interspersed with low-power monitoring. The error can be significant, especially as the battery ages and its internal resistance increases.

Coulomb counting provides much better accuracy because it integrates current over time. The trade-off is additional hardware cost, PCB area, and complexity. Modern fuel gauge ICs also handle battery aging, temperature compensation, and self-discharge estimation, which are important for a device that might be in storage for extended periods.

My approach would be to first define the actual requirements: What accuracy is needed for the battery gauge? Is the primary purpose to give the user a percentage display, or is it safety-critical — for example, ensuring the device doesn't shut down mid-procedure? What is the expected discharge profile — continuous, intermittent, or variable? What is the operating temperature range?

For a medical device, I'd also consider the failure modes. A voltage-based system can give false "battery full" readings after a load is removed (recovery effect), which could mislead a clinician into thinking they have more runtime than they actually do. A coulomb-counting system needs periodic recalibration to a known state (usually full or empty), and if that calibration doesn't happen, accuracy degrades over time.

I'd likely recommend a hybrid approach: use a coulomb-counting fuel gauge IC for the primary estimation, but also monitor voltage as a cross-check and for safety limits (e.g., cutoff voltage). The firmware should also track the battery's state of health and adjust the capacity estimate as the battery ages. The key is to document the accuracy requirements, justify the chosen approach, and verify through testing that the system meets those requirements across the device's operating envelope.

**Possible follow-ups:** How would you verify the fuel gauge accuracy across the battery's lifetime? What happens if the fuel gauge IC itself fails — how would the device detect and respond to that?

---

## Q4: How would you approach developing a design verification test plan for a medical device that measures multiple physiological parameters, when some of the parameters require specialized test equipment that is not yet available in the lab?

**Answer:** I'd start by prioritizing the verification activities based on risk and regulatory requirements, then develop a plan that sequences testing to make the best use of available resources while identifying what's needed to close the gaps.

First, I'd map each design input requirement to its verification method — test, analysis, or inspection — and identify which ones require specialized equipment. For those, I'd determine whether there's an alternative verification method that provides equivalent confidence. For example, if a parameter requires a specific patient simulator that's not available, could we use a calibrated signal source with known characteristics, or a benchtop setup that generates the physiological signal through a validated model?

I'd also look at what can be verified now with available equipment. Many electrical safety tests, EMC pre-compliance checks, and firmware functional tests don't require specialized physiological simulators. I'd sequence the plan to complete those first, which also helps identify design issues early before the specialized equipment arrives.

For the specialized equipment gap, I'd work with the test lab or equipment vendors to understand lead times and whether rental or loaner equipment is available. I'd also consider whether the device manufacturer or a third-party test house has the equipment and could perform the testing under our supervision.

Critically, I'd document the rationale for any alternative verification methods in the verification plan, including the limitations and how we've addressed them. If a test method is deferred, I'd ensure there's a clear risk assessment — what's the impact of not verifying this requirement yet, and what mitigations are in place? This might include additional design analysis, earlier prototype testing, or conservative design margins.

Finally, I'd communicate the plan and constraints to stakeholders early, so there are no surprises about the verification schedule. The goal is to maximize progress while being transparent about what remains to be done and why.

**Possible follow-ups:** How would you handle a situation where an alternative verification method provides results that differ from what you'd expect from the gold-standard test? How would you decide which requirements are critical to verify first versus which can be deferred?

---

## Q5: You're leading a project where a junior engineer on your team has designed a PCB for a medical device's sensor interface. During your review of the layout, you notice that the analog ground and digital ground are not separated, and the ADC reference decoupling capacitor is placed too far from the ADC's reference pin. The junior engineer argues that the design will work fine based on simulation results. How would you handle this situation?

**Answer:** I'd approach this as both a technical issue and a mentoring opportunity. The technical concern is valid — ground noise coupling into the analog reference can directly affect measurement accuracy, and the decoupling capacitor placement is critical for maintaining a low-impedance path at the ADC's reference frequency. However, the junior engineer's confidence based on simulation is understandable, and dismissing it outright would be counterproductive.

First, I'd acknowledge the value of the simulation work and ask the engineer to walk me through the simulation setup — what models were used, what noise sources were included, and what the results showed. This helps me understand their reasoning and also gives me a chance to identify any gaps in the simulation (for example, did it include the parasitic inductance of the trace between the capacitor and the ADC pin? Did it model the ground plane impedance?).

Then I'd explain the practical concerns that simulations often miss: the inductance of vias and traces, the coupling between adjacent traces, and the fact that the ground plane is shared between analog and digital circuits. I'd suggest we look at the layout together and discuss why the separation matters — for example, digital switching currents flowing through the shared ground impedance create voltage differences that appear as noise on the analog reference.

Rather than forcing the change, I'd propose we do a quick experiment or analysis to validate the concern. This could be a simple measurement on the prototype — measuring the ADC noise with the current layout versus a modified version — or a more detailed simulation that includes the parasitic elements. If the concern is confirmed, we have data to support the change. If not, we've learned something and can proceed with confidence.

I'd also frame this as a learning opportunity about the difference between simulation and real-world performance, and about the importance of following established layout guidelines even when simulations suggest they might not be necessary. The goal is to build the engineer's judgment, not just enforce compliance.

**Possible follow-ups:** What if the schedule pressure makes it impractical to do a prototype experiment — how would you decide whether to require the layout change? How would you document this decision for the design history file?