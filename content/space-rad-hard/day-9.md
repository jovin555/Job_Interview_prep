# space-rad-hard — Day 9

## Q1: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** Clock distribution in a space environment presents several unique challenges. Single-event transients (SETs) can cause glitches on clock lines, and total ionizing dose can degrade clock buffer performance over time. I would start by selecting radiation-hardened clock buffers and PLLs where possible, or at minimum characterize COTS alternatives for TID and SET susceptibility.

For the architecture itself, I'd consider a star topology with a central, radiation-hardened clock source feeding dedicated buffers for each load, rather than a daisy-chain or multi-drop configuration. This limits the impact of a single failure to one branch. Each clock line should be differentially routed (LVDS or similar) to provide common-mode rejection against noise and transients. AC-coupling at the receiver can help block DC shifts caused by radiation-induced leakage currents.

For redundancy, I'd evaluate a dual-redundant clock source with automatic switchover. The secondary oscillator runs continuously but is gated at the output; if the primary fails or drifts out of specification (detected by a frequency monitor or phase detector), the system switches to the backup. The switchover itself must be glitch-free — typically achieved using a PLL that can re-lock before the switch, or a cross-point switch with holdover capability.

For the ADCs requiring synchronized sampling, I'd distribute a sample clock and a sync pulse separately. The sync pulse resets the internal sample counters across all ADCs simultaneously, compensating for any skew in the clock distribution. I'd also add programmable delay elements on each ADC's clock input to allow fine-tuning of skew during board-level calibration.

**Possible follow-ups:** How would you verify that the clock distribution meets jitter requirements after radiation exposure? What happens if the backup oscillator also fails — do you have a third level of redundancy?

## Q2: You are reviewing a design for a space-deployed system that uses a COTS FPGA with no radiation characterization. The design uses external configuration memory stored in a parallel NOR flash. How would you evaluate the risk of configuration bit upsets, and what mitigation strategies would you recommend beyond just using TMR on the FPGA fabric?

**Answer:** This is a significant risk because a single-bit upset in the configuration memory can change the FPGA's routing or logic function, potentially causing failures that TMR on the fabric cannot correct — the fabric might be voting correctly on corrupted logic. The external NOR flash is also vulnerable to SEUs and TID effects.

First, I'd evaluate the flash memory's susceptibility. Parallel NOR flash is generally more radiation-tolerant than NAND, but it's still susceptible to bit flips in the storage array and to single-event functional interrupts (SEFIs) in the control logic. I'd look for any existing radiation test data on the specific part or similar process technology. If none exists, I'd flag this as a high-risk item requiring testing.

For mitigation, I'd recommend a multi-layered approach:

1. **Configuration memory scrubbing:** Continuously read back the configuration memory and compare against a golden copy stored in radiation-hardened memory (e.g., MRAM or a rad-hard PROM). When a discrepancy is found, issue a partial reconfiguration to correct the affected frame. The scrub rate should be fast enough to catch upsets before they accumulate to an uncorrectable level.

2. **Triple-redundant configuration storage:** Store three copies of the bitstream in the NOR flash, each with its own CRC. During configuration, read all three and vote on each word. If two copies agree, use that value. If all three disagree, flag an error and retry.

3. **Configuration integrity check after loading:** After the FPGA configures, perform a readback and compare against the golden reference. If mismatches are found, reconfigure immediately.

4. **Watchdog for configuration lockup:** The FPGA's configuration logic can enter a SEFI state where it refuses to accept new bitstreams. A dedicated watchdog timer should monitor the configuration done signal. If configuration doesn't complete within a timeout, power-cycle the FPGA and retry.

5. **Consider using configuration through a radiation-hardened CPLD or microcontroller:** Instead of loading directly from flash, have a rad-hard device read the flash, perform error checking, and feed the bitstream to the FPGA. This adds a layer of protection against flash SEFIs.

**Possible follow-ups:** How would you determine the required scrub rate? What if the golden copy in rad-hard memory is too small to store the full bitstream?

## Q3: How would you approach designing a power-on reset (POR) circuit for a space-deployed system that must guarantee proper initialization across all operating conditions, including after a single-event latch-up (SEL) event that causes a temporary overcurrent condition?

**Answer:** A POR circuit for space must handle several failure modes that terrestrial designs don't typically address. After an SEL event, the system may experience a voltage droop as the current limiter engages, followed by a power cycle. The POR must ensure that all devices reset cleanly when the supply recovers, regardless of how long the droop lasted or how quickly the voltage ramps.

I would design the POR around a radiation-hardened voltage supervisor IC with adjustable threshold and hysteresis, or build a discrete circuit using a precision reference and comparator. Key considerations:

1. **Threshold with hysteresis:** The POR should assert reset when the supply voltage falls below a threshold (e.g., 90% of nominal) and de-assert only after the supply has risen above a higher threshold (e.g., 95%). This prevents oscillation during slow ramp-up or noisy recovery from an SEL.

2. **Minimum reset pulse width:** The reset pulse must be long enough to guarantee all devices complete their internal reset sequences — typically 100-200 ms for most microcontrollers and FPGAs. This can be implemented with an RC delay or a digital timer.

3. **Glitch immunity:** The POR must ignore very short voltage dips (microsecond-scale) that don't represent a true power failure. A digital debounce filter or a retriggerable monostable multivibrator can provide this.

4. **Separate POR for each voltage rail:** In a multi-rail system (3.3V, 1.8V, 1.2V), each rail should have its own POR, and the system reset should be asserted if any rail is out of tolerance. A logical AND of all POR outputs ensures all rails are valid before releasing reset.

5. **SEL recovery integration:** The POR should interface with the latch-up protection circuit. When an SEL is detected (via overcurrent monitoring), the system should assert reset immediately, then power-cycle the affected rail. The POR ensures that after the power cycle, the reset remains asserted until all rails are stable.

6. **Watchdog interaction:** The POR should also be triggered by the watchdog timer if the system fails to initialize within a timeout period. This provides a recovery path for SEFI events that corrupt the boot sequence.

**Possible follow-ups:** How would you test that the POR works correctly across all temperature and radiation conditions? What if the voltage supervisor itself suffers a single-event transient that falsely triggers reset?

## Q4: How would you approach implementing a fault-tolerant bootloader for a microcontroller in a space-deployed system, given that a corrupted bootloader could render the system unrecoverable?

**Answer:** The bootloader is the most critical piece of firmware in a space system — if it's corrupted, the system may become completely unrecoverable, especially if there's no physical access for reprogramming. I would design the bootloader with multiple layers of protection:

1. **Dual-bootloader architecture:** Store two copies of the bootloader in separate memory regions (e.g., the first and last sectors of flash). The primary bootloader runs first. If it fails its integrity check (CRC or signature verification), the secondary bootloader takes over. The secondary bootloader should be minimal — just enough to validate and load the primary, or to accept a new firmware image over a communication link.

2. **Write protection:** Once the bootloader is programmed during manufacturing, hardware write-protect the bootloader sectors. Many microcontrollers have lock bits or protection registers that prevent accidental or intentional writes to specified flash regions. This should be enabled before deployment and verified during testing.

3. **Golden copy in radiation-hardened memory:** Store a compressed or encoded copy of the bootloader in a separate radiation-hardened memory (e.g., MRAM or EEPROM). If both flash copies are corrupted, the bootloader can be restored from this golden copy. The restoration routine itself must be stored in ROM or in a protected region that cannot be corrupted.

4. **Bootloader integrity check on every reset:** Before jumping to the application, the bootloader should verify its own integrity using a CRC or hash. If the check fails, it attempts to load the secondary copy or the golden copy. If all copies fail, it enters a recovery mode where it listens for a new firmware image over a dedicated recovery interface (e.g., UART or CAN bus).

5. **Application-level watchdog for bootloader:** The application firmware should periodically verify that the bootloader is still intact. If corruption is detected, the application can initiate a bootloader recovery process before the next reset.

6. **Atomic update mechanism:** When updating the bootloader in the field (if allowed), the update process must be atomic — either the entire bootloader is written successfully, or the old version remains intact. This requires sufficient spare flash sectors to hold the new image while the old one is still running.

**Possible follow-ups:** How would you handle the case where the microcontroller's boot ROM itself is corrupted? What recovery interface would you choose, and how would you ensure it's available even if the main communication interfaces are non-functional?

## Q5: Imagine you are leading a team designing a radiation-hardened control board for a satellite payload. During a design review, a junior engineer presents a plan to use a single, large FPGA for all digital processing, with TMR applied only to the critical state machines. The engineer argues that applying TMR to the entire design would exceed the FPGA's logic capacity and that the non-critical logic (e.g., configuration registers, housekeeping interfaces) is "safe enough" without redundancy. How would you handle this disagreement?

**Answer:** I would approach this as a coaching opportunity rather than simply overriding the engineer's decision. First, I'd acknowledge the practical constraint — the FPGA has limited resources, and full TMR may not be feasible. Then I'd guide the team through a structured risk assessment to determine what "safe enough" really means.

I'd start by asking: "What is the consequence of a single-event upset in each of these non-critical blocks?" For configuration registers, a single bit flip could change a system parameter — perhaps a threshold voltage or a calibration coefficient. If that parameter controls something safety-critical (like a motor speed or a heater current), then it's not truly non-critical. For housekeeping interfaces, a corrupted telemetry value might cause a false alarm on the ground, or it might mask a real problem. Neither is acceptable for a mission-critical system.

I'd then propose a middle-ground approach:

1. **Categorize all logic blocks by failure consequence:** Use a formal FMEA or FMECA to classify each block as critical (failure causes loss of mission or safety hazard), important (failure degrades performance but doesn't cause loss of mission), or non-essential (failure causes minor inconvenience). Only the truly non-essential blocks should be left without TMR.

2. **Apply selective TMR with resource-aware optimization:** For blocks that are too large for full TMR, consider alternative mitigation techniques. For example, configuration registers can be protected with Hamming codes or CRC rather than full TMR, which uses fewer resources. State machines can use Hamming-encoded state encoding instead of TMR. Housekeeping interfaces can use CRC or checksums on each packet.

3. **Consider partitioning across multiple smaller FPGAs:** If the single large FPGA can't accommodate the required mitigation, splitting the design across two or three smaller FPGAs might provide better fault isolation and allow each to be fully mitigated within its capacity.

4. **Document the risk acceptance:** For any block left without TMR or other mitigation, formally document the risk, the rationale, and the acceptance authority. This ensures that the decision is visible to the entire team and to the customer.

Finally, I'd emphasize that in space systems, "non-critical" is a dangerous label. A single upset in a seemingly unimportant register could cascade into a system failure. The goal is not to eliminate all risk — that's impossible — but to ensure that every risk is understood, documented, and accepted by the appropriate stakeholders.

**Possible follow-ups:** How would you handle it if the engineer still disagrees after your explanation? What if the schedule pressure makes it impossible to redesign the FPGA partitioning?