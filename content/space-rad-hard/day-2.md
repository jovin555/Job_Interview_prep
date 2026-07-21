# space-rad-hard — Day 2

## Q1: What are the primary radiation effects that threaten electronics in space, and how do they differ in terms of failure mechanisms and mitigation strategies?

**Answer:** There are three main categories of radiation effects to consider. Total Ionizing Dose (TID) is cumulative damage from ionizing radiation over the mission lifetime — it degrades transistor thresholds, increases leakage current, and can eventually cause functional failure. Mitigation involves using radiation-hardened process technologies, shielding (typically aluminum or tantalum), and derating components well below their specified limits.

Single Event Effects (SEEs) are caused by a single energetic particle striking a sensitive node. These include Single Event Upsets (SEUs — bit flips in memory or logic), Single Event Latch-up (SEL — a parasitic SCR structure turning on, potentially destructive), and Single Event Gate Rupture (SEGR — damage to power MOSFET gates). Mitigation for SEUs includes error-correcting code (ECC) memory, triple modular redundancy (TMR) in critical logic paths, and watchdog timers. SEL mitigation often requires current-limiting power supplies and latch-up detection circuits that power-cycle the affected section.

Displacement Damage (DD) is non-ionizing energy loss that displaces atoms in the crystal lattice, degrading minority carrier lifetime in bipolar devices and increasing dark current in photodetectors. This is particularly relevant for optoelectronics and sensors. Mitigation involves selecting devices with known displacement damage tolerance and derating optical performance margins.

**Possible follow-ups:** How would you choose between a rad-hard ASIC and a commercial-off-the-shelf (COTS) part with mitigation for a low-earth-orbit mission? What is the significance of linear energy transfer (LET) in characterizing SEE susceptibility?

---

## Q2: How would you approach designing a power supply for a space-rated system that must survive a total ionizing dose of 50 krad(Si) while maintaining efficiency above 85%?

**Answer:** I would start by selecting components that are either radiation-hardened by design or have been characterized for TID tolerance at the required dose. For a 50 krad requirement, many COTS parts with proper derating can work, but I would verify radiation test data from the manufacturer or third-party sources.

For the power topology, I'd likely use a radiation-tolerant controller IC combined with external MOSFETs that have been characterized for both TID and SEE (particularly SEGR in the drain-gate overlap region). The switching frequency should be chosen to balance efficiency against the increased susceptibility of magnetics and capacitors to radiation — higher frequencies allow smaller magnetics but may stress components more.

Key design techniques include: using ceramic capacitors with sufficient voltage derating (typically 50% or more) since their capacitance degrades under bias and radiation; selecting MOSFETs with higher breakdown voltage than nominal to account for threshold shifts; and adding de-rating for all passives — resistors may drift in value, and magnetics may experience core damage over time.

For the control loop, I would avoid relying on internal compensation that might shift with radiation. Instead, I'd use external compensation components that can be characterized for drift. I would also include telemetry for output voltage and current monitoring so that degradation can be tracked over the mission.

**Possible follow-ups:** How would you test this power supply to verify it meets the 50 krad requirement? What failure modes would you specifically look for during radiation testing?

---

## Q3: You are debugging a system that experiences intermittent lock-ups in a 50 krad radiation-hardened design during ground testing with a proton beam. The lock-ups occur only at certain beam energies and disappear when the beam is removed. How would you approach this?

**Answer:** This sounds like a Single Event Latch-up (SEL) or a Single Event Functional Interrupt (SEFI) rather than a TID issue, given the energy dependence and the fact that it recovers when the beam is removed. I would start by instrumenting the system to capture the state at the moment of lock-up — specifically monitoring supply currents on each voltage rail, since SEL typically causes a sharp current increase.

If the current spikes and then the system locks, that strongly suggests latch-up. I would check if the system recovers on its own after a power cycle — if it does, the latch-up was non-destructive. If it doesn't, the part may have been damaged. I would also look at the beam energy and compare it to the LET threshold of the suspect devices. If the beam energy corresponds to an LET above the device's published threshold, that confirms the mechanism.

If the current doesn't spike, it could be a SEFI — a single event that corrupts a control state machine or configuration register. In that case, I would add a watchdog timer that can reset the system, and consider implementing a "scrub" routine that periodically refreshes critical configuration registers.

I would also review the PCB layout — are there any sensitive nodes near the beam entry path? Sometimes the package or shielding geometry can focus particles onto vulnerable areas. Adding localized shielding or moving sensitive components might help.

**Possible follow-ups:** How would you distinguish between SEL and SEFI without adding extra test instrumentation? What changes would you make to the design to prevent this from occurring in flight?

---

## Q4: How would you select and qualify a microcontroller for a space application that requires both radiation tolerance and low power consumption?

**Answer:** I would begin by defining the radiation requirements — TID tolerance, SEE susceptibility (SEU rate per bit-day), and any single-event latch-up immunity requirements. For low-earth orbit, 20-50 krad TID is common, while geostationary or deep-space missions may need 100-300 krad.

For the microcontroller selection, I would look at three tiers: fully radiation-hardened parts (like the RAD750 or LEON-based processors), radiation-tolerant COTS (like certain ARM Cortex-M or STM32 families that have been characterized), and standard COTS with mitigation. For a low-power application, a radiation-tolerant ARM Cortex-M4 or M7 with ECC on flash and SRAM could be appropriate, provided the manufacturer publishes radiation test data.

Key selection criteria include: availability of radiation test reports from the manufacturer or third-party labs; the presence of ECC or parity on internal memories; watchdog timer and brown-out reset robustness; and the ability to operate from a single supply with low quiescent current.

Qualification would involve: reviewing existing test data for the specific lot date code; performing TID testing on a sample of devices (typically 5-11 units) to 1.5x the mission dose; performing heavy-ion testing for SEE characterization at relevant LET values; and conducting burn-in and life testing. I would also derate the clock speed and supply voltage to provide margin against threshold shifts.

For low power, I would select a microcontroller with multiple sleep modes that maintain state retention, and ensure that the power management unit itself is radiation-tolerant — a rad-hard LDO or DC-DC converter feeding the MCU.

**Possible follow-ups:** How would you handle firmware updates in a radiation environment where flash memory may experience bit flips? What mitigation would you use for the external crystal oscillator, which can be sensitive to displacement damage?

---

## Q5: Imagine you are leading a team that has a tight schedule to deliver a radiation-hardened control board for a satellite payload. Halfway through development, a key rad-hard FPGA becomes unavailable due to supply chain issues. How would you handle this situation?

**Answer:** First, I would assess the impact — is the FPGA critical to the design, or could we substitute it with a different part? I would immediately convene a cross-functional team including procurement, systems engineering, and the FPGA designers to understand the constraints.

The first option would be to identify an alternative FPGA from a different manufacturer that meets the radiation requirements and has available stock. This would require a rapid qualification effort — reviewing existing test data, possibly running a quick radiation test on a small sample, and updating the design to accommodate the new part's pinout, configuration, and toolchain.

If no direct replacement exists, I would consider a redesign using a different architecture. For example, replacing the FPGA with a radiation-hardened microcontroller plus external logic, or splitting the FPGA functions across multiple smaller, available parts. This would be more work but might be feasible if the FPGA's functions are well-documented and modular.

Another option is to use a COTS FPGA with radiation mitigation techniques — TMR in the design, configuration memory scrubbing, and shielding. This carries more risk but might be acceptable if the mission's radiation environment is benign (e.g., low-earth orbit with short duration).

I would also communicate transparently with the customer or program management about the situation, presenting the options with their associated risks, schedule impacts, and costs. The decision would be made collaboratively, and I would ensure the team has clear direction and resources to execute the chosen path.

Throughout this, I would maintain a risk register and track mitigation actions. The key is to avoid panic — supply chain issues are common in space hardware, and having a contingency plan from the start of the project would have made this easier.

**Possible follow-ups:** How would you prioritize which FPGA functions to keep if you had to split the design across multiple smaller devices? What documentation would you update to capture the change for future missions?