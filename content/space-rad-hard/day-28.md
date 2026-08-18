# space-rad-hard — Day 28

## Q1: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** Clock distribution in a radiation environment presents unique challenges because single-event transients (SETs) on clock lines can cause metastability, double-clocking, or missed clock edges across multiple devices simultaneously. My approach would start with the clock source itself — selecting a radiation-characterized oscillator or, if using a COTS part, derating it significantly and adding redundancy at the source level. For the distribution topology, I would avoid a single long trace fanning out to all loads; instead, I'd use a dedicated clock buffer or fan-out tree with point-to-point routing to each load, which limits the blast radius of any single transient.

For synchronization integrity, I would consider several layers of protection. First, at the board level, differential clock signaling (LVDS or similar) with proper termination and controlled impedance is more immune to both EMI and single-event transients than single-ended routing. Second, at the device level, I'd use PLLs with built-in lock detection and automatic re-lock capability — if a transient causes the PLL to lose lock, the system needs to detect and recover without manual intervention. Third, at the system level, I'd implement a monitoring scheme where each device periodically verifies clock integrity (for example, checking for unexpected gaps or extra edges) and reports anomalies to a central supervisor.

For synchronized sampling specifically, I would consider whether the ADCs need truly simultaneous sampling or whether a known, fixed phase offset is acceptable. If simultaneous sampling is critical, I'd use a clock distribution IC with matched skew across outputs, and I'd verify skew over temperature and radiation dose during qualification testing. I would also add a mechanism to resynchronize the system after a transient — for example, a global sync pulse that can be re-issued by the supervisor to re-align all converters.

**Possible follow-ups:** How would you verify that clock skew remains within specification after total ionizing dose accumulation? What would you do if a single-event transient caused a PLL to lock to a harmonic of the intended frequency?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has proposed using a single COTS FPGA with internal flash-based configuration memory to avoid the complexity of external configuration management. The engineer argues that flash-based FPGAs are "immune to configuration upsets" because they don't use SRAM for configuration. How would you handle this disagreement?

**Answer:** I would acknowledge that flash-based FPGAs do have an advantage over SRAM-based FPGAs in that the configuration is non-volatile and doesn't need to be reloaded after every power cycle or upset event. However, the claim that they are "immune to configuration upsets" is an overstatement that needs to be examined carefully.

Flash memory cells themselves are susceptible to total ionizing dose effects — charge trapped in the oxide layers can shift threshold voltages over time, eventually causing bits to flip or become stuck. Single-event effects can also occur in flash cells, though the cross-section is typically lower than SRAM. More importantly, the configuration logic that reads the flash and loads it into the fabric is still implemented in CMOS circuitry that is susceptible to single-event upsets and functional interrupts. A SEFI in the configuration controller could corrupt the loading process or cause the device to enter an undefined state.

I would also raise the question of what happens during operation. Even with flash-based configuration, the user logic and block RAM are still susceptible to SEUs. The flash-based approach eliminates one failure mode (configuration bitstream corruption in SRAM) but doesn't address the broader set of radiation effects. Additionally, flash-based FPGAs often have lower logic density and performance compared to SRAM-based parts, which may force design compromises.

My recommendation would be to evaluate the specific radiation data for the proposed part — not just "flash-based" as a category, but actual TID tolerance, SEL immunity, and SEU cross-sections for the configuration logic and user flip-flops. If the data is unavailable, I would treat it as an uncharacterized part and require a qualification plan. I would also ask the engineer to consider what happens if the configuration controller hangs mid-reload — is there a recovery path, or does the system need a full power cycle?

**Possible follow-ups:** What specific radiation tests would you require before accepting a flash-based FPGA for this application? How would you design a recovery mechanism for a configuration controller SEFI?

---

## Q3: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental principle here is that you must never have a single point of failure in the firmware update path — the system must always be able to recover to a known-good state, even if an update is corrupted mid-transfer or the new firmware is defective.

My approach would start with a multi-slot boot architecture. I'd partition the flash into at least two application slots — a current known-good image and a staging area for the new image. The bootloader would be stored in a separate, protected region (ideally in a radiation-hardened boot ROM or write-protected flash sector) and would implement a selection algorithm: boot the newest valid image, and if that fails validation or fails to start within a timeout, fall back to the previous known-good image.

For the update process itself, I would implement several layers of protection. First, the new image should be checksummed or signed (or both) before it's written to flash — validate the entire image in a staging buffer in RAM or a temporary flash region before committing it to the final location. Second, the write process should be interruptible and resumable, so a transient during the write doesn't leave a half-written image. Third, I'd use a "commit" flag that is set only after the new image has been fully written and verified — the bootloader checks this flag before selecting the new image, and clears it on first successful boot.

For radiation-specific concerns, I would add error detection and correction on the flash contents. This could be as simple as storing a CRC or checksum with each image, or as robust as using ECC on the flash controller if available. I would also consider periodic scrubbing of the active image in flash — reading it back and correcting any single-bit errors before they accumulate into multi-bit errors.

Finally, I would design the update protocol itself to be robust against corruption. The ground station or controlling node should be able to re-send the image, and the system should be able to abort an update and revert to the previous image at any point. The update should also be atomic from the user's perspective — either the new image is fully installed and verified, or the system continues running the old image.

**Possible follow-ups:** How would you handle the case where the new image passes checksum validation but is functionally defective and crashes the system? What if the bootloader itself is corrupted?

---

## Q4: How would you approach designing a test plan to verify that a space-deployed system can recover from a single-event functional interrupt (SEFI) that causes the main microcontroller to stop executing code, when you cannot inject actual radiation events during ground testing?

**Answer:** Since we can't create real radiation events in most ground test environments, the goal is to simulate the observable effects of a SEFI as faithfully as possible and verify that the recovery mechanisms work correctly. The key is to think about what a SEFI actually does — it halts instruction execution, possibly corrupts internal state, and may leave peripherals in undefined states — and then reproduce those conditions through software and hardware test hooks.

My approach would be multi-layered. First, I'd design the firmware with explicit test hooks that allow a test harness to force the conditions we're trying to recover from. This could include a debug command that deliberately jumps to an invalid instruction, triggers a software trap, or writes garbage to critical registers. The test harness can then verify that the watchdog or supervisor circuit detects the hang and initiates recovery.

Second, I'd use hardware-level fault injection. This could be as simple as a test header that allows shorting the reset line, or as sophisticated as a fault injection board that can glitch the clock or power supply to induce a controlled malfunction. For a microcontroller, I might use the debug interface (JTAG or SWD) to halt the core, corrupt register values, and then release it — simulating the aftermath of a SEFI without the actual radiation event.

Third, I'd test the recovery path itself under various conditions: recovery from a clean halt (PC pointing to a valid address), recovery from a corrupted stack pointer, recovery from a watchdog timeout where the processor is still toggling a heartbeat GPIO, and recovery from a state where the processor is drawing excessive current (simulating a latch-up condition). Each of these requires a different recovery mechanism, and the test plan should cover all of them.

I would also include long-duration soak testing where the system runs continuously and the test harness periodically injects faults at random intervals. This verifies not just that recovery works, but that the system can survive repeated SEFIs without degradation or accumulated state corruption. The test plan should document expected recovery times for each fault type and verify that they meet the system requirements.

Finally, I'd include a review of the recovery code itself — checking that the initialization sequence after a reset is complete enough to restore all peripherals to a known state, not just the CPU core. A common failure mode is that the system recovers from the SEFI but leaves a peripheral in an undefined state that causes intermittent failures later.

**Possible follow-ups:** How would you verify that the recovery mechanism itself isn't susceptible to the same SEFI? How would you test the interaction between multiple recovery mechanisms (e.g., watchdog timeout followed by power cycle)?

---

## Q5: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS microcontroller for housekeeping. The microcontroller has a built-in watchdog timer that the firmware enables during initialization. The designer argues that the internal watchdog is sufficient and no external watchdog is needed. How would you handle this disagreement?

**Answer:** I would approach this as a risk assessment discussion rather than a flat rejection of the designer's proposal. The internal watchdog is a legitimate first line of defense, but the question is whether it provides adequate coverage for the specific failure modes we're concerned about in a radiation environment.

The key issue is that the internal watchdog shares the same silicon, the same power supply, and the same clock domain as the processor it's supposed to monitor. If a single-event effect causes a SEFI that halts the CPU core, the watchdog timer may also be affected — its counter might freeze, its reset output might not assert, or the clock feeding it might be disrupted. Additionally, if the SEFI corrupts the watchdog configuration registers, the watchdog could be disabled entirely without the firmware noticing.

I would also consider the failure mode where the processor is executing but in a corrupted state — for example, stuck in an infinite loop that happens to include the watchdog refresh instruction. An internal watchdog that is refreshed by firmware can't distinguish between "healthy execution" and "corrupted execution that still hits the refresh." This is where an external watchdog with a longer timeout and independent clock becomes valuable — it forces the system to demonstrate healthy behavior over a longer window, not just execute a single instruction.

My recommendation would be to use both: the internal watchdog for fast detection of simple hangs, and an external watchdog with a longer timeout as a backstop for more subtle failures. The external watchdog should have its own clock source (not derived from the microcontroller's clock), its own power supply (or at least a well-filtered supply), and should be configured so that it cannot be disabled by software. I would also add a "heartbeat" pattern requirement — the firmware must toggle a GPIO in a specific sequence, not just write to a register — so that the external watchdog verifies actual execution progress.

I would frame this not as "your approach is wrong" but as "here are the specific failure modes that concern me, and here's how an external watchdog addresses them." The discussion should focus on risk tolerance and coverage, not on who is right. If the designer can demonstrate through analysis or testing that the internal watchdog provides adequate coverage for the specific radiation environment, I'd be willing to accept it with appropriate documentation — but I'd want that analysis to be explicit and thorough.

**Possible follow-ups:** How would you determine the appropriate timeout values for the internal versus external watchdog? What if the external watchdog itself is a COTS part with no radiation characterization — how would you qualify it?