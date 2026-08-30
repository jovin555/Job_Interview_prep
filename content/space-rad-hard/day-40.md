# space-rad-hard — Day 40

## Q1: How would you approach designing a radiation-tolerant power distribution architecture for a satellite payload that has multiple voltage rails (e.g., 3.3V, 1.8V, 1.2V) and must survive a single-event latch-up (SEL) on any single rail without losing the entire system?

**Answer:** I'd start by treating each voltage rail as an independent fault domain. The key principle is that a latch-up on one rail should not be able to take down the others, either through the power path itself or through shared control logic.

First, I'd put a current-limiting or fold-back protection circuit on each rail's input, before the point-of-load regulation. This could be a dedicated hot-swap controller, a current-sense resistor with a comparator driving a series FET, or a latch-up protection IC if one is qualified for the mission. The important characteristics are: it must trip fast enough to prevent damage (latch-up currents can be several amps), it must latch off or fold back rather than oscillate, and it must be resettable — either automatically after a delay or via a command from the housekeeping controller.

Second, I'd ensure that the rails are not cascaded in a way that creates a single point of failure. For example, if the 1.2V rail is derived from the 3.3V rail through a linear regulator, a latch-up on the 3.3V rail will also kill the 1.2V rail. Where possible, each rail should be fed from the main bus through its own protection stage and its own DC-DC converter. If cascading is unavoidable, the protection must be sized for the worst-case downstream fault.

Third, I'd add per-rail voltage and current monitoring back to the housekeeping controller. This gives you two things: early warning of an impending latch-up (current slowly creeping up) and the ability to command a power cycle of a specific rail without affecting others. The monitoring also helps with post-event analysis — you can log which rail latched up and when.

Finally, I'd consider the SEL event itself. A latch-up is essentially a low-impedance path between the supply and ground through a parasitic thyristor. The protection circuit needs to interrupt that path quickly enough that the device doesn't overheat and fail permanently. This means the current-limit response time matters, not just the steady-state limit. I'd also verify that the protection circuit itself is radiation-tolerant — a COTS hot-swap controller with no radiation data is itself a risk.

**Possible follow-ups:**
- How would you size the current-limit threshold for a rail that has a large inrush current at power-up?
- What happens if the housekeeping controller that resets the protection circuits is itself affected by a single-event upset?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." How would you handle this disagreement?

**Answer:** I'd acknowledge that the engineer has a point about the low power level, but I'd reframe the discussion around what "risk" actually means in a space environment. The concern isn't just about whether the regulator can deliver 50mA — it's about what radiation can do to the regulator's output voltage, noise performance, and long-term reliability.

For an analog rail, the failure modes that matter are subtle. Total ionizing dose (TID) can cause the reference voltage to drift, which shifts the output voltage. It can also increase leakage currents in the pass transistor, which degrades line and load regulation. Single-event transients (SETs) on the regulator's internal reference or error amplifier can cause momentary output voltage spikes or dips — and for a precision analog rail, even a 50mV transient can corrupt a measurement. The regulator might also be susceptible to single-event latch-up (SEL) itself, and at 50mA the current might not be enough to damage the part, but it could still pull the rail down long enough to disrupt the system.

I'd also point out that "no radiation data" is not the same as "radiation-tolerant." Many commercial regulators are built on processes that are actually quite sensitive to TID — bipolar parts, in particular, can show significant degradation at relatively low doses due to enhanced low-dose-rate sensitivity (ELDRS). Without test data, you're assuming the part is fine, and that assumption needs to be justified.

What I'd propose instead: either select a part with existing radiation characterization (even if it's from a similar family or a known test report), or run a targeted radiation test on the specific part. If budget and schedule don't allow testing, I'd look for a drop-in alternative from a qualified manufacturer. If the engineer's part is truly the only option, then I'd want to understand what the system-level mitigation would be — for example, can the ADC tolerate a brief supply transient? Is there a calibration routine that can compensate for drift? Can the rail be monitored and the system alerted if it goes out of spec?

The key is to move the conversation from "the risk is minimal" to "what is the specific failure mode, what is its probability, and what is the consequence?" That's the risk-based approach we should be using for every part in a space design.

**Possible follow-ups:**
- What if the engineer responds that the system has a calibration routine that can compensate for any drift?
- How would you prioritize which parts need radiation testing when you have limited budget?

---

## Q3: How would you approach designing a fault-tolerant analog multiplexing scheme for a space-deployed system where a single-event transient (SET) on the mux select lines could route the wrong sensor channel to a precision ADC, potentially causing an incorrect control action?

**Answer:** This is a classic case where a single-event effect in digital logic can propagate into the analog domain and cause a system-level failure. The first thing I'd do is assess the consequence: if routing the wrong channel to the ADC could trigger an incorrect control action, then the mux selection logic needs to be treated as safety-critical.

The most robust approach is to add redundancy and validation to the channel selection. Instead of a single select word, I'd use a scheme where the select lines are encoded with error detection — for example, a Hamming code or a simple parity bit. The ADC or the controller would validate the select word before accepting the conversion result. If the select word fails validation, the conversion is discarded and the system either retries or enters a safe state.

Another layer is to use a "valid" strobe signal that is asserted only after the select lines have settled and been verified. The mux would only change channels when the strobe is active, and the ADC would only sample when the strobe is de-asserted. This prevents a transient on the select lines from being captured mid-switch.

I'd also consider the physical implementation. If the mux is a COTS part, I'd want to know its radiation characteristics — some muxes are susceptible to SETs on the internal decode logic. If the mux is implemented in an FPGA, then the select logic can be protected with triple modular redundancy (TMR) or at least with error-detecting codes on the state machine.

At the system level, I'd add a plausibility check on the ADC reading itself. If the sensor channels have known ranges, the controller can reject readings that are physically impossible for the expected channel. For example, if channel 1 is a temperature sensor that should read between -40°C and +125°C, and the ADC returns a value that would correspond to 500°C, the controller should flag it as a potential mux error and re-read the channel.

Finally, I'd think about the control action. If a wrong reading could cause an unsafe actuator command, the control loop should have a rate limiter or a "safe hold" that prevents large, sudden changes based on a single reading. This is a system-level mitigation that doesn't eliminate the fault but bounds its consequence.

**Possible follow-ups:**
- How would you implement the plausibility check without adding too much latency to the control loop?
- What if the mux is a commercial part with no radiation data — would you test it, replace it, or add system-level mitigation?

---

## Q4: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental requirement is that a failed or corrupted update must never leave the system in an unbootable state. This means the boot path and the update path need to be designed with redundancy and atomicity in mind.

The first decision is the boot architecture. The most common approach is a two-image scheme: a golden bootloader in protected memory (ideally radiation-hardened or at least write-protected) and two application image slots in flash. The bootloader validates the application image — using a CRC or a cryptographic hash — before jumping to it. If the image fails validation, the bootloader falls back to the other slot. This gives you a known-good image to recover from.

For the update process itself, I'd design it as a multi-step transaction. First, the new image is downloaded and stored in a staging area, not directly into the active slot. The staging area should be separate from both application slots. Once the full image is received, it's validated — checksum, version check, compatibility check. Only after validation does the update commit, which means copying the image into the inactive slot and updating a boot flag or pointer. The commit step should be atomic: either the new image is fully in place and marked valid, or the old image remains active.

I'd also add a "boot counter" mechanism. Each time the system boots, the bootloader increments a counter. If the system fails to boot successfully within a certain number of attempts, the bootloader automatically switches to the other image. This handles the case where the new image passes validation but is actually broken at runtime.

For radiation effects on the flash itself, I'd consider a few things. First, the flash should be protected with error detection and correction (ECC) if available. Second, the bootloader should scrub the application image periodically — reading it back and correcting any single-bit errors before they accumulate. Third, the boot flags and pointers should be stored in multiple locations with voting, since a single upset in the boot pointer could cause the system to boot the wrong image.

Finally, I'd think about the update command path. The update should require a specific command sequence, and the system should be able to abort the update and revert to the previous image if the new one fails to boot. The ground station should also have the ability to force a fallback to the golden image.

**Possible follow-ups:**
- How would you handle the case where the flash memory itself is corrupted during the update — for example, a single-event upset in the address decoder?
- What if the golden bootloader is in the same flash device as the application images?

---

## Q5: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement?

**Answer:** At this point, I'd shift from explaining the technical risks to establishing a decision-making framework. The disagreement isn't really about the regulator — it's about how we make component selection decisions in a space program, and what level of evidence is required to accept risk.

I'd start by acknowledging what the engineer got right: the calibration routine does help with slow drift, and the ADC's PSRR does help with some transient noise. But I'd then ask the engineer to quantify the residual risk. Specifically: what is the expected TID-induced drift for this part over the mission lifetime? What is the expected SET rate and amplitude? What is the SEL cross-section? If the engineer can't answer these questions — and with no radiation data, they can't — then we're not making an engineering decision, we're making a guess.

I'd then propose a structured path forward. There are three options, and I'd ask the engineer to evaluate each one against the mission requirements:

1. **Replace the part** with a radiation-characterized alternative. This is the lowest risk but may require a schedule impact or a redesign of the analog front-end.
2. **Test the part** with a targeted radiation campaign. This is a middle ground — it costs money and time, but it gives us actual data to make a decision. I'd ask the engineer to scope what tests would be needed: TID to the mission dose, heavy-ion testing for SEL and SET, and possibly ELDRS testing if the part is bipolar.
3. **Accept the part with system-level mitigations.** This is the highest risk, and it requires the engineer to define what those mitigations are and how they'll be verified. For example, if the calibration routine is the mitigation for drift, how often will it run? What happens if the drift exceeds the calibration range? If the ADC's PSRR is the mitigation for transients, what is the worst-case transient amplitude and duration that the ADC can tolerate, and how will we verify that the regulator's SET behavior stays within that envelope?

I'd also bring in the program-level context: what is the consequence of a failure on this rail? If it's a critical analog measurement that feeds a control loop, then the risk tolerance is very different than if it's a non-critical housekeeping channel. The risk assessment should be documented in the system's risk management file, with a clear rationale for whatever decision we make.

If the engineer still pushes back after this, I'd escalate the discussion to the project's chief engineer or the radiation effects lead. Not because the engineer is wrong — they might be right that the part is fine — but because this is a decision that needs to be made with full visibility into the mission's risk posture, and it shouldn't be made unilaterally by one person on the team.

**Possible follow-ups:**
- How would you handle the situation if the engineer's proposed mitigations are actually reasonable, but you still have concerns about the part's long-term reliability?
- What if the schedule pressure is real, and replacing or testing the part would delay the program? How would you weigh that against the risk?