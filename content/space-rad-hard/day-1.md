# space-rad-hard — Day 1

## Q1: What does "radiation-hardened" mean in the context of space electronics, and what are the key failure mechanisms you need to design against?

**Answer:** Radiation hardening means designing electronic systems to withstand the ionizing radiation environment found in space, which includes trapped particles in Van Allen belts, solar particle events, and cosmic rays. The key failure mechanisms are:

- **Single Event Effects (SEE):** Including Single Event Upsets (SEU) where a high-energy particle flips a memory bit, Single Event Latch-up (SEL) where it creates a parasitic SCR path that can cause destructive overcurrent, and Single Event Gate Rupture (SEGR) in power MOSFETs.
- **Total Ionizing Dose (TID):** Cumulative damage from radiation over the mission lifetime, which shifts threshold voltages in MOSFETs, increases leakage current, and degrades timing performance.
- **Displacement Damage:** Non-ionizing energy loss that degrades minority carrier lifetime in bipolar devices and optoelectronics.

In my experience designing the **5W High-Reliability EDFA** for space-qualified booster modules, we had to specify 50 kRad (Si) total dose tolerance. This meant selecting radiation-hardened STM32 variants, using external DACs and ADCs with known TID performance, and implementing watchdog timers and EDAC (Error Detection and Correction) on critical data paths to mitigate SEUs. We also added current-limiting circuitry on power rails to protect against latch-up events.

**Possible follow-ups:**
- How would you test a design to verify it meets a 50 kRad specification?
- What is the difference between radiation-hardened and radiation-tolerant design approaches?

---

## Q2: Explain how you would design a power supply for a space-rated system that must survive a single event latch-up condition without being destroyed.

**Answer:** A power supply for a space system must be designed to detect and safely clear latch-up events without damaging the load or the supply itself. The approach I used on the **5W High-Reliability EDFA** project involved several layers of protection:

1. **Current-limiting on each power rail:** We used precision current-sense resistors feeding comparators with programmable thresholds. If current exceeded the normal operating range by a margin (typically 1.5–2x), the comparator would trigger a shutdown sequence.
2. **Active latch-up detection and recovery:** Rather than a simple fuse (which is one-shot and unacceptable in space), we implemented a fold-back current limiter followed by a timed power-cycle. The controller would cut power for ~100ms, then re-apply it. If the latch-up condition cleared, normal operation resumed. If it persisted, the controller would attempt a limited number of retries before entering a safe state.
3. **Hot-swap protection:** The EDFA module included hot-swap controllers that provided inrush current limiting and overcurrent protection, which also served as a first line of defense against latch-up events.
4. **Redundancy:** Critical power rails had redundant regulators with OR-ing diodes, so if one regulator latched up and shut down, the redundant path maintained power to the load.

The key design consideration is that the detection and recovery circuitry itself must be radiation-hardened, otherwise it becomes a single point of failure.

**Possible follow-ups:**
- What happens if the latch-up occurs on a rail powering the microcontroller that manages the recovery?
- How do you choose the retry count and timing for latch-up recovery?

---

## Q3: What are the key differences between designing for commercial/medical reliability versus space radiation-hardened reliability?

**Answer:** While both medical (IEC 60601) and space applications demand high reliability, the failure modes and design approaches differ significantly:

| Aspect | Medical (IEC 60601) | Space Radiation-Hardened |
|--------|-------------------|-------------------------|
| **Primary threat** | Electrical safety, EMC, single-fault conditions | Radiation effects (SEE, TID, displacement damage) |
| **Failure mode focus** | Predictable, safe failure under fault conditions | Surviving unpredictable particle strikes |
| **Component selection** | Medical-grade, long-life industrial parts | Rad-hard or rad-tolerant qualified parts (often expensive, older process nodes) |
| **Redundancy** | Often dual-channel for critical functions (e.g., patient monitoring) | Triple Modular Redundancy (TMR) for critical logic |
| **Testing** | IEC 60601-1 safety testing, EMC per CISPR 11 | TID testing (Co-60 source), heavy ion testing for SEE |
| **Derating** | Standard derating per medical guidelines | Aggressive derating (often 50% of rated voltage/current) |
| **Cost sensitivity** | Moderate | Low (mission success is paramount) |

In my work on the **Lotus Toco device** (medical), we focused on isolation, leakage current, and single-fault condition testing per IEC 60601. For the **5W EDFA** (space), we focused on TID tolerance, SEU mitigation through hardware redundancy, and selecting parts with known radiation performance. The design review processes were similar in rigor, but the technical focus areas were completely different.

**Possible follow-ups:**
- Could you use a medical-grade component in a space design? What would be the risks?
- How does the design lifetime differ between a medical device (typically 5-10 years) and a space mission (could be 15+ years)?

---

## Q4: Describe the architecture you would use for a microcontroller-based system that must tolerate single event upsets in its program memory.

**Answer:** For a radiation-hardened microcontroller system like the one in the **5W High-Reliability EDFA**, where we used STM32 microcontrollers with external DAC/ADC, the architecture must address SEUs in both program memory (Flash) and data memory (SRAM). Here's the approach:

**For program memory (Flash):**
1. **ECC-protected Flash:** Use a microcontroller with built-in Error Correction Code on the Flash memory. Most rad-tolerant MCUs support single-bit error correction and double-bit error detection (SECDED).
2. **Periodic scrubbing:** Implement a background task that reads through the entire Flash memory periodically, checks ECC, and rewrites any corrected single-bit errors before they accumulate into multi-bit errors.
3. **Triple Modular Redundancy (TMR) for critical code:** For the bootloader and safety-critical routines, store three copies in Flash and use a voter circuit (or software voter) to select the majority output.
4. **Watchdog timer with independent clock source:** If the program counter jumps to an invalid location due to an SEU, the watchdog will reset the system.

**For data memory (SRAM):**
1. **ECC or parity on SRAM:** Use MCUs with ECC-protected SRAM, or implement software-based parity checking on critical data structures.
2. **Memory scrubbing:** Periodically read and rewrite SRAM locations to correct soft errors.
3. **Redundant storage for critical variables:** Store key state variables in two or three locations and compare them before use.

**For the external DAC/ADC interface:**
- Use CRC or checksums on all communication packets over SPI/I2C
- Implement read-back verification: after writing a DAC value, read it back to confirm
- Use redundant ADC readings with median filtering to reject single-event transients

The STM32 in the EDFA project had hardware ECC on Flash, and we implemented software-based triple redundancy for the control loop state machine that managed the laser pump diode current.

**Possible follow-ups:**
- How do you handle SEUs in the external ADC itself, which may not have radiation-hardened specifications?
- What is the performance penalty of periodic scrubbing, and how do you determine the scrub interval?

---

## Q5: Behavioral: Tell me about a time you had to make a design trade-off between radiation hardening requirements and another constraint like cost, size, or performance.

**Answer:** **Situation:** During the **5W High-Reliability EDFA** project, we were designing a space-qualified booster module that needed to fit within a very tight volume envelope while meeting 50 kRad total dose tolerance. The initial architecture used a single STM32 microcontroller with integrated DACs and ADCs, which was compact but the integrated peripherals had limited radiation data.

**Task:** I needed to decide whether to use the integrated STM32 peripherals (smaller, lower cost, but unproven for radiation) or add external radiation-hardened DACs and ADCs (larger, more expensive, but guaranteed performance).

**Action:** I led a trade study that considered:
- Volume constraints: The external components would add ~30% more PCB area
- Cost: External rad-hard parts were 5x more expensive
- Risk: The integrated peripherals had no TID characterization data beyond 20 kRad
- Schedule: Adding external parts required redesign of the analog front-end

I recommended the external DAC/ADC approach, but with a mitigation: we used commercial-off-the-shelf (COTS) parts that had been independently tested to 50 kRad, rather than fully qualified mil-spec parts. This saved 40% cost while still meeting the radiation requirement. We also redesigned the PCB layout to stack the external components on both sides of the board to manage the volume constraint.

**Result:** The design passed TID testing to 55 kRad (exceeding the 50 kRad requirement), and the board fit within the volume envelope by using a double-sided component placement strategy. The project stayed on schedule because we selected COTS parts with available test data rather than waiting for long-lead mil-spec components.

**Possible follow-ups:**
- What would you have done if the COTS parts had failed radiation testing?
- How did you verify that the double-sided layout didn't introduce thermal or EMC issues?