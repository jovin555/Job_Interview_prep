# debugging-failure-analysis — Day 10

## Q1: How would you approach a failure investigation where a medical device's safety shutdown circuit activates intermittently during normal use, but the device logs show no fault condition from any monitored parameter at the time of shutdown?

**Answer:** This is a classic case where the absence of logged faults is itself a critical clue. I'd start by treating the safety shutdown as a symptom, not the root cause, and systematically work through the chain of events that could trigger it.

First, I'd verify the logging system's fidelity — is the log capturing at sufficient resolution and coverage to actually see the triggering condition? Many safety shutdowns are triggered by analog comparators or hardware-level monitors that operate independently of the firmware logging path. If the trigger is purely analog (e.g., an overcurrent comparator, a voltage supervisor, or a windowed watchdog), the firmware may never see the event that caused the shutdown. I'd review the schematic to identify every possible shutdown trigger path — both firmware-initiated and hardware-only — and cross-reference that against what the log actually records.

Next, I'd look for events that occur too quickly for the firmware to log. A transient on a supply rail, a glitch on a reset line, or a brief overcurrent condition lasting microseconds could trip a hardware protection circuit without the firmware ever registering a fault. I'd use a high-speed oscilloscope or logic analyzer to monitor the shutdown trigger lines and the relevant power rails during extended operation, ideally with the device instrumented in a way that captures pre-trigger data. A deep-memory scope with trigger on the shutdown signal would let me see what happened in the milliseconds before the event.

I'd also consider environmental factors — mechanical vibration, temperature changes, or electrostatic discharge events that might not be present in a bench test but occur in real-world use. If the device is portable, I'd want to understand how it's handled, stored, and charged, as these can introduce transients.

Finally, I'd examine the shutdown circuit itself for marginal design — component tolerances, aging effects, or noise susceptibility. A comparator with insufficient hysteresis, a reference voltage too close to the trip point, or a decoupling gap near the protection circuit could all cause intermittent triggering. I'd review the design margins and consider whether the trip thresholds have adequate guard banding against worst-case component drift and temperature variation.

**Possible follow-ups:**
- How would you instrument the device to capture a transient event that occurs only once every several days of operation?
- What specific design reviews would you conduct on the shutdown circuit itself to identify marginal behavior?

---

## Q2: You're investigating a field failure where a medical device's battery pack swelled after approximately 14 months of use. The battery management system (BMS) logs show no overvoltage, overcurrent, or overtemperature events. How would you approach this failure analysis?

**Answer:** Battery swelling after extended use without logged protection events points me toward a few categories of root cause: cell degradation from normal cycling, subtle charging issues that don't trip the BMS thresholds, or mechanical/environmental factors.

I'd start by requesting the full BMS log data — not just the fault events, but the regular telemetry: charge/discharge cycles, depth of discharge, temperature history, and charge termination behavior. Swelling is often a symptom of gas generation inside the cell, which can result from overcharging at a level below the protection threshold, from operating at elevated temperatures, or from physical damage. I'd look for patterns in the charging profile — for example, whether the charge termination current was reached consistently, or whether the cell voltage crept slightly higher over time.

Next, I'd examine the charging algorithm and hardware. If the charger uses a constant-current/constant-voltage profile, I'd verify that the voltage regulation accuracy is adequate across temperature and component tolerance. A charger that regulates to 4.2V ±1% is fine, but if the actual cell voltage drifts to 4.25V due to a resistor tolerance stack-up, that's a chronic mild overstress that won't trip protection but will accelerate degradation and gas generation. I'd also check the charge current taper — if the termination current is set too high, the cell may not be fully charged, but if it's set too low, the cell sits at high voltage longer, which also accelerates aging.

I'd also consider the mechanical design — is the battery pack constrained in a way that prevents normal swelling from being absorbed? Even a small amount of gas generation can cause visible swelling if the pack has no room to expand. And I'd review the thermal design: if the battery sits near a heat source or in a poorly ventilated area, elevated temperatures during charging can accelerate degradation.

Finally, I'd want to do a physical teardown of the returned pack — measure cell voltages, inspect for signs of electrolyte leakage, and potentially send cells for external analysis (e.g., CT scanning or gas analysis) to confirm the failure mechanism. This would help determine whether the root cause is cell manufacturing variation, charging system behavior, or environmental factors.

**Possible follow-ups:**
- What specific parameters would you look for in the BMS telemetry to distinguish between normal aging and a charging system fault?
- How would you determine whether the swelling is a safety risk that requires a recall versus an isolated incident?

---

## Q3: How would you approach debugging a failure where a medical device passes all individual component tests and sub-assembly tests, but fails when the full system is assembled and powered on — specifically, the main processor fails to communicate with a peripheral over SPI, and the failure is consistent across multiple units?

**Answer:** A consistent failure at full-system integration that doesn't appear at the sub-assembly level strongly suggests an interaction between subsystems — something that only manifests when the complete system is powered and operating. I'd approach this by systematically identifying what changes between the sub-assembly test and the full-system test.

First, I'd compare the two test configurations in detail. What's different? Additional power rails are energized, other peripherals are active, the physical layout is different (cabling, board spacing), and the grounding topology changes. I'd ask: is the SPI bus length different? Are there new sources of noise or interference? Is the ground reference shared differently?

The most common culprits in this scenario are power integrity and grounding. When the full system is powered, the additional current draw can cause ground bounce or supply voltage droop that wasn't present in the sub-assembly test. I'd probe the SPI lines and the processor's supply rails at the moment of failure, looking for noise, ringing, or voltage sag. I'd also check whether the SPI signals have adequate drive strength and whether the rise/fall times are marginal — a signal that's fine in isolation can fail when crosstalk from other active buses is added.

Another angle is the initialization sequence. In the full system, the processor may be attempting to communicate with the peripheral before the peripheral's power rail has stabilized, or before its own firmware has completed initialization. I'd review the boot sequence and check whether there's a timing dependency — for example, the peripheral's reset pin being released before its supply is within specification.

I'd also look at the physical layer — connector pinout, cable routing, and whether the SPI signals are properly terminated. If the full system adds a cable or a board-to-board connector, impedance discontinuity and increased capacitance can degrade signal integrity.

Finally, I'd use a divide-and-conquer approach: start with the full system and progressively disable subsystems until the failure disappears, then re-enable them one at a time to identify the specific interaction. This is more efficient than guessing at the cause.

**Possible follow-ups:**
- How would you determine whether the issue is a timing problem versus a signal integrity problem?
- What specific measurements would you take to compare the SPI signals between the sub-assembly test and the full-system test?

---

## Q4: A medical device has been in production for two years with a low field failure rate. In the last three months, the failure rate has increased fivefold, and the returned units all show the same symptom: a specific voltage regulator output is out of specification (reading low). The regulator and surrounding components are unchanged in the BOM. How would you approach this emerging failure trend?

**Answer:** A sudden increase in a previously stable failure rate is a red flag that something changed — and the change may not be in the design itself. I'd approach this as a trend investigation rather than a single-unit failure analysis, because the root cause likely lies in a change to the supply chain, manufacturing process, or usage environment.

I'd start by gathering data on the returned units: manufacturing date codes, component lot codes (especially for the regulator, its input/output capacitors, and the PCB), assembly line location, and any test data from production. I'd look for correlations — are the failures concentrated in a specific date range, a specific component lot, a specific assembly line, or a specific customer segment? This data analysis often narrows the search space dramatically.

Next, I'd examine the regulator's operating conditions in the failed units. A low output voltage could result from a marginal input supply, excessive load, or a degraded component. I'd measure the input voltage, output current, and the regulator's thermal behavior in the returned units. If the regulator is a linear type, I'd check for excessive power dissipation — perhaps the input voltage increased due to a change in the upstream supply. If it's a switching regulator, I'd look at the inductor, output capacitor, and feedback network for signs of degradation.

I'd also review the component supply chain. A change in the regulator's die revision, a different wafer fab, or a counterfeit component entering the supply could all cause subtle performance shifts. I'd verify that the components in the failed units match the approved BOM and that the date codes are consistent with the production period. I'd also check whether the PCB supplier changed — a variation in copper thickness, solder mask, or via quality could affect the regulator's performance.

Finally, I'd consider the usage environment. If the device is used in a new market or a different clinical setting, the operating conditions may have changed — higher ambient temperature, different input power quality, or a different load profile. I'd review the field data to see if the failure rate correlates with any customer or geography.

The key principle here is to treat this as a statistical and systemic investigation, not just a component-level analysis. The root cause may be upstream of the regulator itself.

**Possible follow-ups:**
- How would you prioritize the investigation between component-level analysis and supply chain/manufacturing investigation?
- What data would you request from the manufacturing team to help narrow down the root cause?

---

## Q5: You're leading a failure investigation where a medical device was returned from the field with a cracked solder joint on a critical component. The crack is visible under X-ray inspection. The device was in service for about two years. The manufacturing team says the soldering process is within specification, and the design team says the component placement and thermal design are adequate. How would you handle this situation and structure the investigation?

**Answer:** This is a situation where multiple teams have valid perspectives, and the challenge is to move from blame to systematic investigation. I'd structure this as a formal failure analysis with clear phases, and I'd start by establishing a shared understanding of the failure mechanism before anyone draws conclusions.

First, I'd convene the cross-functional team — manufacturing, design, quality, and reliability — and lay out the investigation plan. The goal is to determine the root cause, not to assign blame. I'd emphasize that the crack is a symptom, and the question is why it occurred: was it caused by mechanical stress, thermal cycling, manufacturing variation, or a combination?

I'd begin with a detailed physical analysis of the failed joint. X-ray is a good start, but I'd also want cross-sectioning to examine the intermetallic layer, the solder grain structure, and the crack propagation path. A crack that propagates through the bulk solder suggests thermal fatigue; a crack at the intermetallic interface suggests a contamination or wetting issue; a crack at the component lead suggests mechanical stress. This distinction is critical because it points to different root causes.

Next, I'd examine the mechanical and thermal environment. Two years in service means the device has experienced thousands of thermal cycles — even small temperature excursions can cause fatigue in solder joints if the coefficient of thermal expansion mismatch is significant. I'd review the thermal design: is the component near a heat source? Is the PCB constrained in a way that transfers stress to the solder joint? I'd also consider mechanical vibration or shock — is the device handheld, mounted, or subject to transport?

I'd then review the manufacturing data. The soldering process being "within specification" is necessary but not sufficient — I'd want to see the actual process data for the specific boards or date range in question. I'd look at reflow profiles, solder paste inspection results, and any rework history. I'd also check whether the component's footprint and pad design are appropriate for the expected thermal and mechanical loads.

Finally, I'd consider whether this is a single isolated failure or a trend. If it's one unit out of thousands, the investigation might conclude with a component-level anomaly. If it's a pattern, I'd want to understand the population risk and whether a design change, process change, or field action is warranted.

Throughout, I'd keep the team focused on evidence and data, and I'd document every finding so the investigation can be audited and the corrective action can be traced back to the root cause.

**Possible follow-ups:**
- How would you determine whether the crack is due to thermal fatigue versus mechanical stress, and what specific analysis would you use?
- How would you handle a situation where the manufacturing team and design team each believe the other is at fault, and the investigation is becoming contentious?