# space-rad-hard — Day 41

## Q1: How would you approach designing a fault-tolerant analog multiplexing scheme for a space-deployed system where a single-event transient (SET) on the mux select lines could route the wrong sensor channel to a precision ADC, potentially causing an incorrect control action?

**Answer:** This is a classic case where a single point of failure in the digital control path can corrupt an analog measurement that drives a safety-critical decision. My approach would be layered:

First, at the architectural level, I'd question whether a single shared mux is the right topology. If the channels feed independent control loops with different criticality, splitting them across two muxes or giving the most critical channel a dedicated ADC input removes the failure mode entirely. That's the strongest mitigation — eliminating the shared element.

If a mux is unavoidable, I'd add redundancy in the select-line encoding. Rather than a binary-encoded select, I'd consider one-hot or Gray-coded selection with a validity check. For example, if you use one-hot encoding, a single-bit upset either selects no channel (detectable as an invalid state) or selects the same channel (benign), rather than silently switching to a different valid channel. The firmware or a small PLD can monitor the select lines and assert an error flag if an invalid pattern appears.

I'd also add a "sample validity" handshake. The ADC conversion should be tagged with the channel address that was actually selected, not just the one the firmware intended. If the read-back channel doesn't match the commanded channel, the sample is discarded or flagged. This requires the mux to have read-back capability or a separate monitoring path.

Finally, I'd consider temporal redundancy — taking multiple samples and requiring agreement before acting on the value. This doesn't help if the SET persists, but it catches transient glitches. The key trade-off is latency: if the control loop needs a fresh sample every millisecond, you can't average over a long window.

**Possible follow-ups:** How would you handle the case where the SET occurs on the mux's analog switch itself, causing a momentary short between two channels? What if the mux is internal to the ADC and you can't observe the select lines directly?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." How would you handle this disagreement?

**Answer:** I'd start by acknowledging the engineer's point — the load is small and the topology is simple — but then reframe the question from "what could go wrong electrically" to "what could go wrong in this specific environment." The absence of radiation data doesn't mean the part is safe; it means we have no evidence either way. For a critical analog rail, that uncertainty is itself a risk.

I'd walk through the specific radiation failure modes. Total ionizing dose can shift the reference voltage or the pass transistor's characteristics, causing the output to drift outside the tolerance the ADC needs. Single-event transients on the error amplifier can cause output voltage spikes that corrupt a measurement in progress. Single-event latch-up is a real concern even at low current — a 50mA load doesn't prevent the regulator's internal parasitic SCR from latching and drawing current from the input bus. So "low power" doesn't mean "low risk" for latch-up.

I'd then ask what the rail actually feeds. If it's the reference or analog supply for a sensor that drives a control decision, the consequence of a transient is not "a noisy reading" — it's potentially an incorrect control action. That elevates the criticality regardless of the current level.

Practically, I'd propose a path forward rather than just rejecting the idea. Options include: checking if a radiation-tested equivalent exists from the same family; reviewing the part's internal topology to assess latch-up susceptibility; or running a limited radiation test on a few samples if the budget allows. If none of those are feasible, I'd recommend a known rad-tolerant regulator or a simple discrete solution with radiation-characterized components.

**Possible follow-ups:** What if the engineer responds that the system has a calibration routine that can correct for drift? How would you weigh the cost of a rad-hard part against the risk of using a COTS part?

---

## Q3: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The core principle is that the update path must never be the single point of failure. I'd design for three things: a guaranteed-safe boot path, integrity verification at every step, and the ability to roll back.

First, the boot architecture. I'd use a two-stage approach: a small, immutable bootloader in protected memory (ideally radiation-hardened or write-protected) that validates the application image before jumping to it. The bootloader itself should be simple enough to verify by inspection and should never be updated in the field. If the application image fails validation, the bootloader stays resident and waits for a new image — it doesn't try to execute corrupted code.

Second, the update process itself. The new image should be written to a separate bank or region, not over the currently running image. Only after the full image is received, stored, and validated (checksum, CRC, or cryptographic signature) would the system switch the boot pointer. This "download-then-activate" pattern means a corrupted transfer never leaves the system in a partially-updated state.

Third, redundancy. If the flash is susceptible to upsets, I'd store two copies of the application image and have the bootloader verify both, booting the healthier one. For critical systems, I'd also consider storing the image in a radiation-tolerant memory type (like MRAM) or using ECC-protected external flash with scrubbing.

Finally, I'd think about the update channel itself. The communication link that delivers the update can also be corrupted, so the protocol needs sequence numbers, retransmission, and a way to resume an interrupted transfer. And the system should be able to reject an update that is valid but incompatible with the current hardware revision.

**Possible follow-ups:** How would you handle the case where the bootloader itself is in flash that can be corrupted? What if the system has already booted into a corrupted application — how would you detect that and trigger recovery?

---

## Q4: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** Clock distribution in a radiation environment has two distinct concerns: the clock source itself (oscillator or PLL) and the distribution network. Both can be affected by single-event effects, but the failure modes are different.

For the source, I'd start with the oscillator. A crystal oscillator can experience frequency shifts from total ionizing dose, and a single-event transient on the oscillator circuit can cause a phase glitch or a temporary frequency jump. I'd select an oscillator with radiation characterization if available, or at least one with a simple, well-understood internal topology. For the PLL, if one is used, I'd be concerned about single-event transients on the phase detector or charge pump causing the loop to lose lock. A lock-detect circuit with automatic re-lock is essential.

For the distribution network, the main concern is that a single-event transient on a clock buffer or trace could cause a glitch that propagates to multiple devices simultaneously. If all FPGAs and ADCs sample on the same edge, a single glitch could corrupt a whole batch of samples. I'd consider distributing the clock as a differential signal (LVDS or similar) for noise immunity, and I'd add per-device clock monitoring. Each FPGA or ADC should have a clock-loss detector that flags an error rather than silently sampling on a bad clock.

For synchronized sampling specifically, I'd think about whether the system truly needs sample-level synchronization or just sample-consistent timing. If the ADCs are sampling at, say, 1 MSPS, a phase offset of a few nanoseconds between devices is usually acceptable. That opens the option of using independent oscillators with a periodic synchronization pulse (like a PPS signal) rather than a shared high-speed clock. This is more fault-tolerant because a failure in one clock domain doesn't affect the others.

If a shared clock is required, I'd add redundancy at the board level — a secondary oscillator that can be switched in, or a clock fan-out buffer with redundant inputs. The switchover logic needs to be glitch-free, which is itself a design challenge.

**Possible follow-ups:** How would you verify that all ADCs are actually sampling synchronously after a clock glitch event? What if the clock distribution is on a backplane connecting multiple boards — how does that change your approach?

---

## Q5: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement?

**Answer:** At this point, the technical facts have been laid out and the engineer is still pushing back. The issue is no longer purely technical — it's about decision-making under uncertainty and the engineer's understanding of what "acceptable risk" means in a space program. I'd shift the conversation from the specific part to the engineering process.

First, I'd ask the engineer to articulate the acceptance criteria. What would constitute evidence that this regulator is safe to use? If the answer is "it will probably work," that's not an acceptance criterion — that's a hope. I'd push for a concrete, documented rationale: either radiation test data on this part or a close variant, a derating analysis that shows the part's internal topology is inherently latch-up-immune, or a system-level analysis showing that the failure modes are truly benign. If none of these exist, the part doesn't meet the program's requirements, regardless of how small the load is.

Second, I'd reframe the risk in terms of mission impact. A calibration routine can correct for slow drift, but it cannot correct for a transient that corrupts a single measurement at the wrong moment. If that measurement feeds a control decision, the consequence is not "a slightly inaccurate reading" — it's a potentially incorrect action. The engineer needs to trace the failure mode to the system-level consequence, not stop at the component level.

Third, I'd invoke the program's risk management process. In a formal design review, this would be logged as a risk item with a severity and likelihood assigned. The engineer's argument is essentially "the likelihood is low because the load is small," but that conflates electrical stress with radiation susceptibility. I'd ask for the risk assessment to be documented formally, with the mitigation plan. If the mitigation is "calibration," I'd ask how calibration addresses a transient that lasts microseconds.

If the engineer still disagrees after this, I'd make the decision as the lead: the part is not approved for this application without additional data. I'd offer a concrete alternative — a radiation-tested regulator, or a simple discrete solution — and assign the engineer to evaluate the alternatives. The goal is not to win an argument but to ensure the design decision is based on evidence, not optimism.

**Possible follow-ups:** How would you handle this if the engineer is senior and has more experience than you? What if the schedule pressure is real and the alternative part has a long lead time — how would you balance that against the risk?