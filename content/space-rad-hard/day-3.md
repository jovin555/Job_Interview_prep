# space-rad-hard — Day 3

## Q1: How would you approach designing a memory scrubbing strategy for an SRAM-based FPGA in a space application, and what trade-offs would you consider?

**Answer:** Memory scrubbing for SRAM-based FPGAs addresses single-event upsets (SEUs) that accumulate in configuration memory over time. The core approach involves periodically reading back the configuration memory and correcting any bit flips before they cause functional failures.

I would start by characterizing the expected upset rate based on the orbit environment (e.g., LEO vs GEO vs deep space) and the device's SEU cross-section from the manufacturer's data. This gives a mean time between upsets (MTBU) that drives scrub rate selection.

For the scrub implementation, there are two main strategies: blind scrubbing and readback scrubbing. Blind scrubbing rewrites the entire configuration memory from a known-good golden image stored in radiation-hardened memory (e.g., MRAM or PROM) on a fixed schedule, without checking for errors first. Readback scrubbing reads the configuration frames, compares them to a golden copy, and only rewrites frames with errors. Readback scrubbing consumes less power and causes less configuration memory wear, but requires more complex logic and a reliable comparison mechanism.

The key trade-offs are:
- **Scrub interval vs. availability:** Scrubbing too frequently wastes power and may cause brief functional interruptions; too infrequently allows multiple bit errors to accumulate, potentially exceeding the error correction capability of any built-in ECC.
- **Single-bit vs. multi-bit error handling:** Most configuration memories have ECC that corrects single-bit errors and detects double-bit errors. For multi-bit upsets, the scrubber must detect the uncorrectable error and trigger a full reconfiguration or system reset.
- **Golden image storage:** The reference image must itself be radiation-hardened. Using triple-modular redundancy (TMR) for the storage or storing multiple copies with CRC verification is advisable.

A practical approach for a medium-complexity design would be to use readback scrubbing with a scrub interval of roughly 1/10th the expected MTBU, combined with frame-level CRC checking to catch multi-bit errors. The scrubber itself should be implemented in radiation-hardened logic (e.g., a rad-hard CPLD or ASIC) rather than in the FPGA being scrubbed, to avoid the scrubber itself being corrupted.

**Possible follow-ups:** How would you verify that your scrubber is working correctly during ground testing? What would you do if the golden image storage itself develops a fault?

---

## Q2: How would you approach thermal management for a high-power DC-DC converter in a vacuum environment where there is no convective cooling?

**Answer:** In vacuum, heat transfer relies entirely on conduction and radiation, with no convective path. For a DC-DC converter that may dissipate 10-20W or more, this requires a deliberate thermal path from the heat-generating components to the spacecraft structure or a dedicated radiator.

The first step is to identify all heat sources: the switching FETs, the transformer or inductor, the rectifier diodes, and any control ICs. Each component has a maximum junction temperature that must not be exceeded, typically derated to 80-85% of the absolute maximum for space applications.

For conduction, I would design a thermal stack that minimizes the number of interfaces and uses high-thermal-conductivity materials. The power components would be mounted on a metal-core PCB or directly to a metal baseplate using thermal vias and copper coin inserts. At each interface—component to PCB, PCB to baseplate, baseplate to chassis—I would use a space-qualified thermal interface material (TIM) such as a graphite sheet or a metal-filled silicone pad, avoiding materials that outgas or degrade in vacuum.

For radiation, the baseplate or heatsink should have a high-emissivity surface coating (e.g., black anodize or a space-grade thermal paint) to maximize radiative heat transfer to the surrounding structure. The view factor to the spacecraft radiator or cold plate must be considered—if the converter is boxed in by other boards, radiation alone may be insufficient, and conduction becomes the primary path.

I would also consider the thermal derating of the converter itself. Many COTS DC-DC converters are rated for full power only with forced air cooling; in vacuum, they may need to be derated to 50-70% of their nominal rating. Selecting a converter with a wide operating temperature range and a baseplate-cooling option is preferable.

Finally, I would model the thermal path using finite element analysis (FEA) early in the design, iterating on the board layout, component placement, and mechanical mounting until all junction temperatures are within limits under worst-case hot conditions. Testing would include thermal vacuum (TVAC) chamber testing to validate the model.

**Possible follow-ups:** How would you handle a situation where the spacecraft bus voltage is 28V but your DC-DC converter is only 85% efficient, dissipating 15W? What changes would you make to the mechanical design?

---

## Q3: You are reviewing a schematic for a space-rated system that uses a COTS microcontroller with external watchdog timer. The watchdog timer's reset output is connected directly to the microcontroller's reset pin. What potential issues do you see, and how would you improve the design?

**Answer:** There are several potential issues with a direct watchdog-to-reset connection in a space environment:

1. **Single-event latch-up (SEL) in the watchdog itself:** If the watchdog timer is also a COTS part, it could latch up due to a heavy ion strike. A latched watchdog might hold the reset line in an incorrect state, either preventing the microcontroller from running or continuously resetting it. The watchdog should be a radiation-hardened part, or at minimum have latch-up protection such as a current-limiting resistor on its output.

2. **No isolation between watchdog and microcontroller:** If the microcontroller experiences a single-event functional interrupt (SEFI) that causes it to drive its reset pin as an output (some microcontrollers have bidirectional reset pins), it could fight the watchdog's output. A series resistor (e.g., 100-470 ohms) between the watchdog output and the microcontroller reset pin prevents contention and limits current.

3. **Single point of failure:** A single watchdog provides no redundancy. For critical systems, I would consider a dual-watchdog architecture with diverse implementations—for example, one internal watchdog in the microcontroller and one external, or two external watchdogs from different manufacturers. The watchdogs should have different timeout periods so that if one fails, the other still provides coverage.

4. **No provision for disabling the watchdog during ground testing or debug:** In a space system, you may need to run the microcontroller without the watchdog during bring-up or failure analysis. A jumper or test point that allows the watchdog output to be isolated (e.g., a 0-ohm resistor that can be removed) is useful.

5. **Watchdog timeout selection:** The timeout must be long enough to accommodate the worst-case execution time of the main loop, including any error handling or recovery routines, but short enough to detect a hung processor before it causes system-level harm. For a medical or life-support system (like Project Z), the timeout might need to be on the order of milliseconds; for a satellite payload, seconds may be acceptable.

An improved design would use a rad-hard watchdog with an open-drain output, a pull-up resistor to the microcontroller's supply, and a series resistor to the reset pin. The watchdog's own supply should be filtered and protected against transients. Additionally, the watchdog should monitor a "heartbeat" signal that is toggled by the firmware only after the firmware has verified critical system health checks (e.g., memory integrity, sensor readings within range), not just a simple timer tick.

**Possible follow-ups:** How would you test that the watchdog actually resets the microcontroller under all fault conditions? What if the microcontroller's internal oscillator drifts due to radiation—how does that affect the watchdog strategy?

---

## Q4: How would you approach selecting between a single radiation-hardened FPGA and a multi-chip solution using several COTS FPGAs with TMR for a space application that requires high logic density?

**Answer:** This is a classic trade-off between risk, cost, schedule, and performance. A single rad-hard FPGA (e.g., from the RTG4 or PolarFire families) offers guaranteed radiation tolerance, a known SEU cross-section, and simpler board layout and power distribution. However, these parts are expensive, have long lead times, and may have lower logic density or fewer I/Os than the latest COTS FPGAs.

A multi-chip COTS solution with TMR can achieve similar or better fault tolerance at lower component cost, but introduces significant complexity:

**For the multi-chip COTS approach, I would consider:**

1. **TMR architecture:** Three identical COTS FPGAs would each run the same logic, with a majority voter on all outputs. The voter itself must be radiation-hardened (e.g., in a rad-hard CPLD or ASIC) to avoid being a single point of failure. The FPGAs would need to be synchronized, which requires careful clock distribution and periodic resynchronization.

2. **Scrubbing:** Each COTS FPGA would need its own configuration memory scrubber, since SRAM-based FPGAs are susceptible to configuration upsets. This adds three scrubbers (or one shared scrubber with multiplexed access, which is a single point of failure).

3. **Power and thermal:** Three FPGAs consume roughly three times the power of one rad-hard FPGA, which complicates thermal management and may exceed the spacecraft's power budget. The power supply must be sized accordingly, with sufficient margin.

4. **Board area and routing:** Three FPGAs plus voters, scrubbers, and supporting circuitry require significantly more PCB area. The routing for the voter interconnects must be carefully designed to avoid introducing timing skew or signal integrity issues.

5. **Synchronization challenges:** The three FPGAs must start from the same state and process the same inputs synchronously. Any timing difference between the three paths (due to process variation, temperature, or radiation-induced delay changes) can cause the voters to see different values at the voting instant, leading to incorrect majority outputs.

**Decision framework:**

- If the logic density requirement can be met by a single rad-hard FPGA, and the budget and schedule allow for it, I would choose the single rad-hard part for its simplicity and lower risk.
- If the required logic density exceeds what rad-hard FPGAs offer, or if the cost/lead time is prohibitive, I would consider a hybrid approach: use a rad-hard FPGA for critical control logic and COTS FPGAs for non-critical data processing, with TMR only on the COTS side.
- For a truly high-density application where neither option is clearly superior, I would prototype both approaches and compare them on power consumption, timing closure, and testability before making a final decision.

**Possible follow-ups:** How would you handle clock distribution to three synchronized COTS FPGAs? What happens if one FPGA's PLL loses lock due to a single-event transient?

---

## Q5: Imagine you are leading a team designing a radiation-hardened control board for a satellite. A junior engineer on your team has designed a power supply that meets the electrical specifications but uses a commercial electrolytic capacitor that is not rated for vacuum operation. The engineer argues that the capacitor is "good enough" because similar parts have been used in previous projects. How would you handle this situation?

**Answer:** This is a situation where technical judgment must be balanced with mentoring and team dynamics. The engineer's argument—that similar parts have been used before—is understandable but potentially dangerous in a space application where the consequences of a single component failure can be mission-ending.

I would approach this as a teaching opportunity rather than simply overriding the decision. First, I would acknowledge the engineer's reasoning: yes, commercial electrolytic capacitors can work in benign environments, and yes, previous projects may have gotten away with it. But space is not a benign environment, and "getting away with it" is not the same as a qualified design.

I would then walk through the specific failure mechanisms of electrolytic capacitors in vacuum:

1. **Electrolyte evaporation:** Electrolytic capacitors contain a liquid or gel electrolyte. In vacuum, the electrolyte can outgas and evaporate over time, changing the capacitor's capacitance and equivalent series resistance (ESR). This can cause the capacitor to fail open or, worse, to overheat and rupture.

2. **Pressure differential:** The sealed can of an electrolytic capacitor is designed for atmospheric pressure. In vacuum, the internal pressure can cause the can to bulge or the seal to leak, again leading to electrolyte loss.

3. **Thermal cycling:** In orbit, the capacitor may experience extreme temperature swings. Electrolytic capacitors have relatively poor temperature stability compared to ceramic or tantalum types, and repeated thermal cycling can degrade the dielectric.

4. **Radiation effects:** While electrolytic capacitors are generally less sensitive to radiation than semiconductors, the polymer or paper separators can degrade under total ionizing dose, and the electrolyte itself may undergo chemical changes.

I would then ask the engineer to research and present a comparison of qualified alternatives: tantalum capacitors (which are inherently more radiation-tolerant and have no liquid electrolyte), ceramic capacitors (which are vacuum-compatible but have voltage derating concerns), or space-qualified electrolytic capacitors from a QML vendor. I would guide them to look at the manufacturer's data sheets for vacuum compatibility and radiation test data.

If the schedule is tight and we need a decision quickly, I would explain that we cannot accept the risk of an unqualified part in a critical power supply. We would replace the electrolytic with a tantalum capacitor of equivalent capacitance and voltage rating, and adjust the board layout if needed. I would also add a note to the design review checklist to explicitly verify vacuum compatibility for all components.

Finally, I would use this as a learning point for the whole team: in space design, qualification and environmental testing are not optional. A part that works on the bench may fail catastrophically in orbit, and it's our job to anticipate those failure modes, not just hope they don't occur.

**Possible follow-ups:** What if the engineer's capacitor is the only one that fits the board space and meets the ripple current requirements? How would you resolve the conflict between schedule pressure and component qualification?