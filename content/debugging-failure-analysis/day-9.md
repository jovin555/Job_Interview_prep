# debugging-failure-analysis — Day 9

## Q1: How would you approach debugging a medical device where the firmware enters a hard fault handler intermittently — roughly once every 6–12 hours — and the stack trace points to a different function each time?

**Answer:** This pattern — a hard fault that hits different locations — strongly suggests a memory corruption issue rather than a deterministic code bug. The corruption could be a stack overflow, heap corruption, or a buffer overrun that silently damages memory, and the fault manifests later when the corrupted memory region is accessed.

My approach would be:

1. **Enable the MPU (Memory Protection Unit)** if the microcontroller supports it and the RTOS allows. Configure it to trap access to unused memory regions and to set stack guard pages. This can catch the corruption at the moment it happens rather than when it's discovered.

2. **Check stack allocation.** In a Zephyr RTOS system, I'd verify that each thread's stack size is adequate — not just by static analysis, but by measuring actual stack usage. Zephyr has `CONFIG_THREAD_STACK_INFO` and runtime stack usage tracking. I'd enable those and look for threads using more than 80% of their allocated stack.

3. **Instrument the heap allocator.** If the system uses dynamic memory allocation (malloc/k_free), I'd enable heap debugging features — guard bands around allocations, fill patterns on free, and double-free detection. Many RTOS implementations offer this. I'd run the system with these checks enabled and look for corruption patterns.

4. **Examine the fault log more carefully.** Even though the PC (program counter) varies, the fault syndrome register (e.g., the CFSR in ARM Cortex-M) might show a consistent pattern — is it always an imprecise bus fault? Always a usage fault from an undefined instruction? That tells us something about the corruption mechanism.

5. **Reduce variables.** If possible, I'd run the system with different subsystems disabled to see if the fault rate changes. For example, if disabling the wireless stack eliminates the fault, that narrows the search considerably.

The key insight is that a hard fault hitting random locations is almost never a bug in the code at those locations — it's a bug elsewhere that corrupted them.

**Possible follow-ups:**
- What if the MPU isn't available on this microcontroller? How else would you catch the corruption?
- How would you distinguish between a stack overflow and a heap corruption based on the fault symptoms?

---

## Q2: You're debugging a medical device where the analog front-end for a pressure sensor shows a periodic 50mV spike on the output every 100ms, exactly synchronized with the system's wireless beacon interval. The spike is within the sensor's bandwidth and corrupts the measurement. How would you approach this?

**Answer:** This is a classic conducted or radiated coupling problem where a periodic RF event is injecting noise into a sensitive analog path. The 100ms period matching the beacon interval is the critical clue — the wireless transmitter's current draw or RF field is coupling into the analog front-end.

My systematic approach:

1. **Characterize the coupling path.** I'd start by determining whether the noise is conducted (through the power supply) or radiated (through the air or PCB parasitics). I'd probe the analog supply rail with a differential probe during a beacon transmission — if I see the same 50mV spike on the supply, it's conducted. If the supply is clean but the sensor output still shows the spike, it's radiated coupling.

2. **Check the power supply.** If conducted, I'd look at the power distribution. The wireless transmitter likely draws a pulsed current of several hundred mA during the beacon. If the analog front-end shares a regulator or has inadequate filtering between the digital and analog supply domains, that current pulse creates a voltage drop. I'd verify the PSRR (power supply rejection ratio) of the analog front-end at the beacon frequency and check for adequate decoupling — particularly a low-ESR capacitor close to the analog supply pin.

3. **If radiated:** I'd use a near-field probe to scan the PCB during a beacon transmission. The coupling could be through:
   - The sensor trace acting as an antenna
   - The sensor cable (if external) picking up the field
   - Ground plane segmentation creating a large loop area in the analog path
   - The sensor itself being susceptible to RF rectification

4. **Temporal mitigation.** If the coupling can't be eliminated, I'd work with the firmware team to implement a blanking window — the ADC reading is gated off during the beacon transmission, and the measurement is taken either just before or just after. This is a common technique in mixed-signal systems with periodic RF activity.

5. **Physical mitigation options:** Depending on the root cause, solutions might include adding a ferrite bead on the sensor supply, increasing the analog ground plane area, moving the antenna further from the sensor trace, or adding a small RC filter on the sensor output if the bandwidth allows.

**Possible follow-ups:**
- How would you determine whether the coupling is through the sensor's power pin versus the signal output pin?
- What if the blanking window approach introduces a timing error in the pressure measurement — how would you compensate?

---

## Q3: A medical device passes all functional and safety tests at the design verification stage, but during a 30-unit pilot production run, three units fail a 72-hour burn-in test with the same symptom: the device stops communicating after approximately 48 hours and requires a power cycle to recover. How would you approach this?

**Answer:** This is a latent defect or marginal design issue that only manifests under extended operation. The fact that three out of thirty units fail with the same symptom, and all fail around the same time point (48 hours), suggests a systematic issue rather than random component failure.

My approach:

1. **Examine the failure mode in detail.** I'd connect a logic analyzer or protocol analyzer to the communication bus on a unit during burn-in and capture the exact sequence leading up to the failure. Does the device stop transmitting, or does it stop responding? Is there a specific error code or status register value just before failure?

2. **Check for progressive degradation.** I'd instrument one of the failing units with additional monitoring — power rail voltage logging, temperature logging at critical components, and watchdog timer activity. A slow drift in a voltage reference, a capacitor degrading under bias, or a marginal solder joint that opens when heated could all cause a failure after many hours.

3. **Compare failing vs. passing units.** I'd swap key components between a failing unit and a passing unit to isolate the root cause. For example:
   - Swap the main microcontroller between units — does the failure follow the chip or stay with the board?
   - Swap the communication transceiver
   - Swap the power supply components

4. **Thermal analysis.** I'd use a thermal camera to compare temperature profiles between units during burn-in. A component running hotter than expected could be operating outside its safe operating area, leading to drift or intermittent failure after extended operation.

5. **Review the burn-in test conditions.** Are the failing units from the same production batch? Same component date codes? Same assembly shift? This could point to a process variation — perhaps a reflow profile issue or a specific component lot with marginal performance.

6. **Accelerated testing.** If the failure is time-dependent, I'd try to accelerate it — increase the ambient temperature, increase the communication rate, or reduce supply voltage to see if the failure occurs sooner. This helps confirm the root cause mechanism.

**Possible follow-ups:**
- What if swapping components doesn't isolate the issue because the failure is intermittent and takes 48 hours to reproduce each time?
- How would you decide whether to halt the pilot production run while the investigation is ongoing?

---

## Q4: You're investigating a field return where a medical device's enclosure shows signs of corrosion around the USB connector, and the device no longer charges. The device was used in a home healthcare setting. How would you approach this failure analysis?

**Answer:** This is a environmental ingress failure that could have multiple contributing factors — the user's environment, the connector design, the sealing method, or the electrical protection circuitry. The investigation needs to determine both the physical failure mechanism and whether the design is adequate for the intended use environment.

My approach:

1. **Document the physical evidence.** I'd photograph the corrosion pattern in detail, noting whether it's localized to specific pins, whether there's evidence of liquid residue, and whether the corrosion extends inside the enclosure. I'd use a microscope to examine the connector for cracks in the housing or gaps in the seal.

2. **Determine the corrosive agent.** I'd use energy-dispersive X-ray spectroscopy (EDX) or X-ray fluorescence (XRF) on the corrosion residue to identify the chemical composition. Common culprits in home healthcare include:
   - Sweat or body fluids (high chloride content)
   - Cleaning agents (bleach, hydrogen peroxide, alcohol)
   - Humidity with ionic contaminants
   - Galvanic corrosion between dissimilar metals in the connector

3. **Check the electrical protection.** I'd examine the charging circuit — specifically the ESD protection diodes, the overvoltage protection, and any conformal coating inside the device. If the corrosion bridged the VBUS and ground pins, it could have damaged the charger IC. I'd check for secondary damage downstream.

4. **Review the design specifications.** What is the IP rating of the USB connector? Was it specified as sealed or unsealed? What is the intended cleaning protocol for the device? If the device is meant to be wiped down with disinfectant, the connector should be rated for that exposure.

5. **Simulate the failure.** I'd set up a controlled test where I expose identical devices to the suspected corrosive agent — for example, applying saline solution to the connector and letting it dry, then repeating the charge cycle. This helps confirm the failure mechanism and test potential fixes.

6. **Evaluate design mitigations.** Depending on the root cause, solutions might include:
   - Switching to a sealed USB connector with an IP67 rating
   - Adding a conformal coating over the connector pins inside the device
   - Using a magnetic charging connector instead of a physical USB port
   - Adding a sacrificial anode or using corrosion-resistant materials
   - Improving the user instructions for cleaning and drying the connector

**Possible follow-ups:**
- How would you distinguish between a design flaw and user misuse in your root cause determination?
- What regulatory reporting obligations might apply if this corrosion could be linked to a patient safety issue?

---

## Q5: You're leading a cross-functional investigation into a medical device failure where the device's motor (used for a therapeutic function) stopped mid-procedure. The device logs show a motor current spike followed by a stall condition, and the fuse is blown. The mechanical team believes the electrical design is at fault, and the electrical team believes the mechanical design caused an overcurrent condition. How would you handle this situation and structure the investigation?

**Answer:** This is a classic cross-functional disagreement where each team sees the symptom from their own perspective. The key is to structure the investigation so that objective data, not opinion, drives the conclusion. As the lead investigator, my role is to facilitate that process and keep the focus on evidence.

My approach:

1. **Establish the investigation framework.** I'd convene both teams and agree on a structured root cause analysis methodology — typically an 8D process or a formal fault tree analysis. The first step is to define the problem precisely: what exactly happened, when, and under what conditions? We need to agree on the facts before we can analyze causes.

2. **Collect and preserve all evidence.** Before any analysis begins, I'd ensure:
   - The failed device is quarantined and not tampered with
   - The motor, fuse, and drive electronics are photographed and documented
   - The device logs are extracted and time-stamped
   - Any similar units from the same production batch are identified

3. **Divide the investigation into parallel workstreams.** Rather than debating who is at fault, I'd assign each team to investigate their own domain:
   - **Electrical team:** Characterize the motor driver circuit. Measure the motor's electrical characteristics (winding resistance, inductance, back-EMF constant). Check the fuse rating vs. the motor's stall current. Look for any electrical failure modes — shorted MOSFET, failed current sense resistor, gate drive issues.
   - **Mechanical team:** Examine the motor and load path. Check for binding, excessive friction, foreign object obstruction, or bearing failure. Measure the mechanical torque required to turn the mechanism. Look for signs of wear or misalignment.
   - **Cross-cutting:** Examine the fuse under a microscope — does it show evidence of a slow overcurrent (gradual heating) or a fast short circuit (explosive opening)? This tells us about the nature of the fault.

4. **Recreate the failure.** I'd set up a test with a known-good unit and try to reproduce the stall condition under controlled conditions. Can we cause a stall by increasing the mechanical load? By reducing the motor voltage? By introducing a partial short in the motor windings? This helps identify the necessary and sufficient conditions for the failure.

5. **Review the design specifications.** What is the maximum mechanical load the motor is designed to handle? What is the stall current at that load? Is there a current limit in the motor driver, or does it rely solely on the fuse for protection? If there's no active current limiting, the design may be marginal.

6. **Facilitate a data review.** Once both teams have their findings, I'd lead a structured review where each team presents their evidence. The goal is not to assign blame but to identify the root cause chain. Often, the root cause is a system-level issue — for example, a tolerance stack-up in the mechanical assembly that occasionally causes binding, combined with a motor driver that doesn't have active current limiting, combined with a fuse that's rated too high to protect against a partial stall.

7. **Drive to corrective actions.** Once the root cause is identified, I'd lead the team in developing corrective actions that address the system, not just one team's contribution. This might include adding active current limiting in the firmware, increasing the mechanical tolerance, adding a stall detection algorithm, or changing the fuse specification.

**Possible follow-ups:**
- How would you handle a situation where one team is resistant to accepting evidence that points to their domain as a contributing factor?
- What if the investigation reveals that the failure was caused by a combination of factors that individually are within specification — how would you decide whether a design change is warranted?