# space-rad-hard — Day 6

## Q1: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** Clock distribution in a radiation environment presents several failure modes that need to be addressed simultaneously. I'd start by evaluating whether a single master clock source with fan-out buffers is sufficient, or if a redundant clock architecture is warranted based on mission criticality.

For the clock source itself, I would select a radiation-tolerant oscillator (such as a quartz crystal oscillator with known TID tolerance) rather than a MEMS-based device, which can be more susceptible to total dose effects. The oscillator should be derated for frequency stability over temperature and lifetime.

For distribution, I would use a dedicated clock fan-out buffer with low additive jitter, and critically, I would implement redundancy at the distribution level. A typical approach is a 1:2 or 1:3 fan-out with cross-strapping: two independent clock sources feed into a redundant distribution network, and each receiving device (FPGA, ADC) has a clock selection mechanism. This could be as simple as a radiation-tolerant clock mux with manual override, or an automatic switchover with glitch-free transition.

On the PCB layout, clock traces should be impedance-controlled, length-matched for skew, and isolated from noisy digital signals. I'd use differential clocking where possible (LVDS or CML) for better common-mode noise rejection, and ensure proper termination to avoid reflections.

For the ADCs requiring synchronized sampling, I would distribute a sample clock and a synchronization pulse (SYNC) separately. The SYNC signal should be debounced or have a voting mechanism if it passes through radiation-prone routing. Each FPGA should have its own PLL to clean up any jitter introduced during distribution, with the PLLs configured to lock to the same reference and generate aligned internal clocks.

Finally, I would include monitoring capability: each clock domain should have a frequency counter or phase detector that can detect drift or loss of lock, and report back to a system health monitor. This allows graceful degradation or reconfiguration if a clock source degrades over the mission.

**Possible follow-ups:** How would you handle the scenario where one clock source fails but the system must continue operating without interruption? What clock jitter budget would you allocate for a 16-bit ADC sampling at 10 MSPS, and how would you verify it during testing?

## Q2: How would you approach selecting and qualifying a voltage supervisor or reset IC for a space-deployed system, given that most commercial parts are not radiation-characterized?

**Answer:** Voltage supervision is a critical function because an incorrect reset state during a radiation event can cause system lock-up or data corruption. Since most commercial voltage supervisors are not radiation-characterized, I would take a layered approach.

First, I would select a part with inherently radiation-tolerant characteristics: a simple bipolar or CMOS design with wide operating margins, rather than a complex programmable supervisor. Simpler circuits tend to have fewer failure modes under radiation. I would look for parts with known heritage in similar applications, even if not formally QML-listed.

Second, I would implement design-level mitigation. Instead of relying on a single supervisor IC, I would use a combination of techniques:
- A primary supervisor with a fixed threshold for the main supply rail
- A secondary, independent supervisor (different manufacturer, different internal topology) monitoring the same rail with a slightly different threshold
- A discrete RC-based watchdog that provides a coarse reset if the supervisors disagree or if the microcontroller stops toggling

Third, I would add filtering on the reset output to prevent false triggers from single-event transients (SETs). A simple RC low-pass filter with a time constant of 1-10 microseconds can filter out most transients without delaying the reset too long for a genuine undervoltage condition. The filter should be placed after the supervisor output but before the reset distribution.

For qualification, I would perform:
- TID testing at a facility like a cobalt-60 source to at least 1.5x the mission dose, monitoring threshold voltage drift and output logic levels
- Heavy-ion testing for SEL (single-event latch-up) at a linear energy transfer (LET) above the worst-case expected for the orbit
- Temperature cycling over the full mission range to verify the threshold doesn't shift unacceptably

If the budget doesn't allow full characterization, I would use the supervisor only as a secondary monitor, with the primary reset generation coming from a more robust source like a radiation-hardened FPGA or a discrete circuit using qualified transistors.

**Possible follow-ups:** How would you design a discrete voltage supervisor using only resistors, capacitors, and a comparator if no suitable IC is available? What failure modes of a voltage supervisor are most concerning in a space environment, and how would you test for them?

## Q3: You are reviewing a design for a space-deployed system that uses a COTS FPGA for data processing. The design uses external configuration memory (flash) that is not radiation-hardened. How would you evaluate the risk of configuration upsets and what mitigation strategies would you recommend?

**Answer:** This is a significant concern because the FPGA configuration memory defines the entire logic function of the device. If the external flash is corrupted by a radiation event, the FPGA could load incorrect configuration data on the next power-up or reconfiguration, potentially causing functional failure.

First, I would evaluate the specific risk based on the flash technology. NOR flash is generally more radiation-tolerant than NAND flash, but both can experience single-event upsets (SEUs) in the memory cells and single-event functional interrupts (SEFIs) in the controller logic. The total ionizing dose tolerance of commercial flash is typically low (10-30 krad), so for longer missions this may be a lifetime issue as well.

For mitigation, I would recommend a multi-layered approach:

1. **Error detection and correction (EDAC) on the configuration data**: Store the configuration bitstream with error-correcting codes (ECC). When the FPGA loads configuration, the external memory controller should check and correct any single-bit errors. For multi-bit errors, the system should flag a fault and potentially reload from a backup.

2. **Redundant configuration storage**: Use two or three independent flash devices storing identical configuration data. A voting circuit or the FPGA itself can compare the outputs during readback and select the majority. This protects against a single device being completely corrupted.

3. **Scrubbing of the configuration memory**: Periodically read back the configuration data from the flash, check for errors, and rewrite corrected data. This prevents accumulation of errors over the mission. The scrub rate should be based on the expected upset rate for the orbit.

4. **Configuration integrity check on every power-up**: Before loading the FPGA, verify a checksum or CRC of the stored configuration. If it fails, attempt to load from a backup copy or enter a safe mode.

5. **Consider using the FPGA's internal configuration scrubbing**: Some FPGAs have built-in CRC checking of the configuration SRAM. While this doesn't protect the external flash directly, it can detect when the loaded configuration has been corrupted and trigger a reload from the external memory.

If the flash is particularly susceptible, I would also consider using a radiation-hardened configuration PROM or MRAM (magnetoresistive RAM) as the primary storage, with the COTS flash as a backup that is only used if the primary fails.

**Possible follow-ups:** How would you design the configuration reload mechanism to avoid a situation where a corrupted flash causes the FPGA to load a bad configuration repeatedly (bricking the system)? What is the trade-off between using a single, larger flash device versus multiple smaller devices for redundancy?

## Q4: How would you approach designing a power-on reset (POR) circuit for a space-deployed system that must guarantee proper initialization across all operating conditions, including after a single-event latch-up (SEL) event that causes a temporary overcurrent condition?

**Answer:** A power-on reset circuit for space must handle not only normal power-up but also recovery from radiation-induced events that may leave the system in an indeterminate state. The key requirements are: guaranteed reset assertion until all supply rails are stable, immunity to transients, and reliable release after a fault condition clears.

I would design the POR circuit as follows:

**Core architecture**: Use a precision voltage reference and comparator to monitor the main supply rail (e.g., 3.3V). The comparator's output drives a reset signal through a debounce timer. The threshold should be set to assert reset when the rail drops below the minimum operating voltage of the digital logic (typically 90% of nominal), with hysteresis to prevent oscillation near the threshold.

**SEL recovery consideration**: After an SEL event, the system may draw excessive current, causing the supply rail to collapse. When the rail drops below the POR threshold, the reset should assert immediately. However, the system must not re-assert power until the latch-up condition has cleared. I would add a retry timer that holds the system in reset for a minimum period (e.g., 100 ms) after the rail returns to nominal, allowing the latch-up to clear and the power supply to stabilize.

**Redundancy**: For critical systems, I would use two independent POR circuits monitoring different supply rails (e.g., 3.3V and 1.8V) with their outputs ANDed together. This ensures that if one rail is slow to rise or experiences a transient, the reset remains asserted.

**Transient immunity**: The comparator should have built-in filtering or an external RC network to ignore short-duration transients (less than 1 microsecond) that could be caused by single-event transients on the supply rail. However, the filter must be short enough that a genuine undervoltage condition (like a latch-up event) asserts reset quickly.

**Manual override**: Include a watchdog timer that can force a system reset if the main processor stops responding. This should be independent of the POR circuit and have its own supply and timing reference.

**Testing**: The POR circuit should be tested across temperature extremes, with slow and fast ramp rates on the supply, and with injected transients to verify immunity. For SEL recovery, I would test by temporarily shorting the supply rail (simulating a latch-up) and verifying that the system resets cleanly and recovers.

**Possible follow-ups:** How would you design the POR circuit to distinguish between a normal power-down and a latch-up event, so that the system doesn't enter an infinite reset loop? What components in a POR circuit are most susceptible to radiation, and how would you select alternatives?

## Q5: Imagine you are leading a team designing a radiation-hardened control board for a satellite. During a design review, a junior engineer presents a plan to use a single, large FPGA for all digital processing, with TMR applied only to the critical state machines. The engineer argues that applying TMR to the entire design would exceed the FPGA's logic capacity and that the non-critical logic (e.g., configuration registers, housekeeping interfaces) is "safe enough" without redundancy. How would you handle this disagreement?

**Answer:** I would first acknowledge the engineer's practical concern about logic capacity—that's a real constraint that can't be ignored. However, I would explain why the proposed approach carries hidden risks that could compromise mission reliability.

The core issue is that "non-critical" logic can still cause critical failures. A single-event upset in a configuration register that controls an ADC's power-down mode might seem benign, but if that register flips and the ADC powers down, the system loses a sensor reading that could be essential for a control loop. Similarly, an upset in a housekeeping interface's state machine could cause a bus lock-up, preventing the main controller from communicating with the rest of the satellite.

I would propose a structured approach to evaluate the risk:

1. **Failure mode analysis**: For each block of non-critical logic, we would perform a quick FMEA (failure mode and effects analysis) to determine the consequence of a single upset. If the consequence is "no effect" or "graceful degradation," then TMR may not be needed. If the consequence is "loss of function" or "system failure," then it should be protected.

2. **Tiered protection**: Instead of all-or-nothing TMR, we could use different levels of protection:
   - Critical state machines: Full TMR with voting
   - Configuration registers: Hamming code EDAC or triple-redundant storage with periodic scrubbing
   - Housekeeping interfaces: CRC or parity on data, with timeout-based error recovery
   - Non-essential status indicators: No protection, with the understanding that occasional errors are acceptable

3. **Resource optimization**: We could reduce logic usage by implementing TMR at a higher level. For example, instead of triplicating every flip-flop, we could triplicate entire functional blocks and vote at their outputs. This uses less logic than fine-grained TMR but still provides protection.

4. **Consider a different architecture**: If the FPGA is too small for adequate protection, we might split the design across two smaller FPGAs, each handling a subset of functions with cross-checking between them. This could actually improve fault tolerance while using less total logic per device.

I would also ask the engineer to quantify the risk: what is the expected upset rate for the unprotected logic, and what is the probability of a critical failure over the mission lifetime? If the numbers show that the risk is acceptable (e.g., less than 1% probability of mission failure), then the approach might be justified. But if the risk is higher, we need to find a way to protect the vulnerable logic, even if it means reducing functionality or using a larger FPGA.

Finally, I would frame this as a team decision: we would document the analysis, present the trade-offs to the project lead, and make a risk-informed choice together. The engineer's concern about logic capacity is valid, and we should respect that constraint while ensuring we don't accept unacceptable risk.

**Possible follow-ups:** How would you quantify the acceptable risk level for non-critical logic in a satellite mission? What would you do if the analysis shows that protecting all vulnerable logic would require a larger FPGA that exceeds the budget or schedule?