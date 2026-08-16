# space-rad-hard — Day 26

## Q1: How would you approach designing a radiation-tolerant voltage reference circuit for a precision ADC in a space-deployed system, given that the reference itself may experience single-event transients (SETs) that cause momentary voltage spikes or dips?

**Answer:** The key challenge is that a voltage reference serves as the absolute scale for all measurements, so any transient on it directly corrupts every conversion performed during that window. My approach would be layered:

First, at the component level, I'd look for references with known radiation characterization—ideally on a QML list or with published heavy-ion and TID data. If forced to use a COTS part, I'd review its internal architecture: bandgap-based references tend to be more SET-tolerant than those using Zener breakdown, and some parts have internal filtering or multiple sampling stages that reduce transient susceptibility.

Second, at the circuit level, I'd add a low-pass filter between the reference output and the ADC's reference input. The bandwidth of this filter must be carefully chosen—it needs to reject SETs with durations in the microsecond range while still settling quickly enough for the ADC's sampling requirements. A capacitor directly at the ADC reference pin is essential, sized to hold the voltage stable during a conversion cycle.

Third, at the system level, I'd implement measurement validation. If the ADC samples the reference itself periodically (through a multiplexer), the firmware can detect when the reference has drifted from its expected value and flag or discard measurements taken during that window. For truly critical channels, redundant references with majority voting—or at least cross-checking between two independent references—can catch transients that affect only one.

Finally, I'd consider the PCB layout: the reference should have a clean, dedicated ground return, be thermally isolated from heat sources, and be placed away from high-speed digital traces to minimize coupled noise that could exacerbate SET effects.

**Possible follow-ups:** How would you size the filter capacitor to balance SET rejection against ADC settling time? What if the reference's radiation data shows it's susceptible to permanent damage from TID, not just transients?

---

## Q2: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single COTS FPGA with internal configuration memory (flash-based) to avoid the complexity of external configuration management. The engineer argues that flash-based FPGAs are "immune to configuration upsets" because they don't use SRAM for configuration. How would you handle this disagreement?

**Answer:** I'd acknowledge that the engineer has identified a real advantage—flash-based FPGAs do eliminate the class of configuration bitstream upsets that plague SRAM-based FPGAs, since the configuration is stored in non-volatile cells that are far less susceptible to single-event upsets. That's a legitimate design consideration.

However, I'd push back on the assumption that this makes the configuration "immune." Flash cells can still experience upsets, particularly from heavy ions, though at much lower rates than SRAM. More importantly, the FPGA's internal registers, block RAM, and state machines are still implemented in volatile logic that remains susceptible to SEUs. The configuration being stable doesn't protect the operational data.

I'd also raise several practical concerns. First, what is the radiation characterization of this specific COTS part? Many flash-based FPGAs have no published heavy-ion data, and the manufacturer may not support space applications. Second, flash-based FPGAs typically have lower logic density and performance than SRAM-based parts, which may constrain the design. Third, if the configuration flash is internal, you lose the ability to scrub or reload the configuration independently—you're trusting the internal cells entirely.

My recommendation would be to evaluate the part's radiation data seriously, and if it's inadequate, consider either a qualified rad-hard FPGA or an SRAM-based COTS FPGA with external configuration management, including scrubbing and reload capability. If the flash-based approach is retained, I'd want to see a plan for how the design handles SEUs in the fabric and memory, and how the system recovers if the configuration is ever corrupted.

**Possible follow-ups:** What if the flash-based FPGA has some radiation data showing acceptable TID tolerance but no heavy-ion data for configuration upsets? How would you weigh the risk? What testing would you propose to close that gap?

---

## Q3: How would you approach designing a fault-tolerant analog output stage for a space-deployed system where a single-event transient (SET) on a DAC's reference voltage could cause a momentary but dangerous output spike to an actuator?

**Answer:** This is a classic case where the failure mode is time-limited but consequence-severe, so the mitigation strategy must focus on both preventing the spike and ensuring the system can detect and respond if one occurs.

At the circuit level, I'd start with the DAC reference path. A filtered reference—using a capacitor bank with appropriate ESR characteristics—can slow the reference's response to a transient, reducing the magnitude of the resulting output spike. I'd also consider whether the DAC's output stage can be designed with a slew-rate limit, so even if the reference jumps, the output can't change faster than the actuator can safely tolerate.

For the output stage itself, I'd add protection circuitry. A window comparator monitoring the output voltage can detect when it exceeds the commanded value by more than a defined margin, triggering a fast shutdown or latch that holds the output in a safe state. This needs to be an analog circuit—not firmware-dependent—because the response time required is typically microseconds, faster than a processor can react.

At the system level, I'd implement a "command and verify" scheme in firmware. Before applying a new output value, the firmware reads back the current output and confirms it matches the last commanded value. If a mismatch is detected, the system can enter a safe state. For truly critical actuators, I'd consider a hardware interlock: a separate, independent path that can disable the output stage if certain conditions are violated.

Finally, I'd think about the actuator itself. What is the safe state? If the actuator must hold position, a brake or mechanical latch might be needed. If it must return to a home position, a spring-return mechanism could be appropriate. The electronics can only do so much—the system design should ensure that even a worst-case output spike doesn't cause physical damage.

**Possible follow-ups:** How would you test this protection circuitry to verify it responds fast enough? What if the window comparator itself is susceptible to SETs—how do you protect the protector?

---

## Q4: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental principle is that you must never have a single point of failure in the boot path. The system must always be able to recover to a known-good state, even if the update process is interrupted or corrupted.

I'd start with a multi-slot firmware architecture. The system would have at least two firmware images: a golden or bootloader image that is write-protected and never updated in the field, and one or more application images that can be updated. The bootloader validates the application image—checking a CRC or digital signature—before jumping to it. If validation fails, it falls back to the previous known-good image or enters a recovery mode.

For the update process itself, I'd design it as a transaction with explicit states. The new image is written to an inactive slot, validated in place, and only then is the active slot pointer updated. If any step fails, the system reverts to the previous image. This is analogous to a database transaction with commit and rollback.

Given the radiation environment, I'd add scrubbing of the flash contents. Periodically, the firmware reads back the stored image and verifies its checksum. If a single-bit error is detected, it can be corrected if ECC is available, or the affected word can be rewritten from a redundant copy. For critical systems, I'd consider storing the application image in two independent flash devices and using majority voting during the boot read.

I'd also think about the update trigger. The system should be able to receive a new image via a reliable, error-checked communication protocol, with the image itself protected by strong error detection. The update should be resumable—if interrupted, it can continue from the last valid block rather than restarting.

Finally, I'd design for the worst case: if the system becomes completely unbootable, there must be a hardware recovery path. This could be a dedicated recovery mode triggered by a strap pin or a command interface that bypasses the normal boot sequence, allowing a minimal bootloader to be loaded into RAM and used to reprogram the flash.

**Possible follow-ups:** How would you handle the case where the flash device itself is damaged by TID and can no longer be written? What if the bootloader image is in the same flash device as the application?

---

## Q5: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS microcontroller for housekeeping. The microcontroller has a built-in watchdog timer that the firmware enables during initialization. The designer argues that the internal watchdog is sufficient and no external watchdog is needed. How would you handle this disagreement?

**Answer:** I'd start by acknowledging the legitimate point: an internal watchdog, properly configured, can detect and recover from many software hangs and even some SEU-induced failures. It's not a useless feature, and for less critical functions it may be entirely adequate.

However, I'd raise the fundamental concern: the watchdog is part of the same silicon that is susceptible to radiation effects. If a single-event functional interrupt (SEFI) affects the microcontroller's clock system, power management, or the watchdog peripheral itself, the internal watchdog may not fire when needed. The failure domain includes the watchdog—it's not an independent observer.

I'd also consider the failure modes that an internal watchdog can't catch. If the processor enters a state where it continues executing code but the program counter is corrupted, the watchdog may be periodically refreshed by coincidence, masking the fault. A hardware watchdog with a longer timeout and a requirement for a specific, complex refresh sequence is harder to accidentally satisfy.

My recommendation would be to add an external watchdog—ideally a simple, radiation-tolerant timer circuit—that is independent of the microcontroller. The refresh signal should be a carefully designed sequence that the firmware must execute deliberately, not just a GPIO toggle that could be caught in a loop. The external watchdog should also have a defined behavior on timeout: asserting a hardware reset, and possibly also triggering a fault log or telemetry event.

I'd also use this as an opportunity to discuss the broader fault tolerance strategy. The external watchdog is one layer; the system should also have a higher-level health monitor—perhaps the FPGA—that can detect when the microcontroller is not responding correctly and take appropriate action, such as resetting it or switching to a redundant controller.

**Possible follow-ups:** What if the external watchdog is a COTS part with no radiation data—how would you qualify it? How would you design the refresh sequence to be robust against accidental refreshes during corrupted execution?