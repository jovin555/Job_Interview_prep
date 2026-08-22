# space-rad-hard — Day 32

## Q1: How would you approach designing a fault-tolerant analog output stage for a space-deployed system where a single-event transient (SET) on a DAC's reference voltage could cause a momentary but dangerous output spike to an actuator?

**Answer:** This is a classic case where a single-event effect in a seemingly passive component—the reference—can create a hazardous output condition. My approach would start by understanding the failure path: an SET on the reference causes a transient voltage excursion, which the DAC translates directly into an output error, and if the actuator is fast enough, it responds before the transient self-corrects.

The first line of defense is at the reference itself. I'd use a reference with known radiation characterization where possible, and add filtering at its output—a capacitor with appropriate ESR characteristics to slow the transient response without compromising stability. The capacitor value needs to be sized so that the time constant is longer than the expected SET duration (typically nanoseconds to microseconds) but short enough not to degrade the reference's ability to track legitimate load changes.

Beyond that, I'd add a rate-of-change limiter or slew-rate limiting stage between the DAC output and the actuator driver. This could be as simple as an RC filter with a time constant matched to the actuator's safe response time, or an active circuit that limits the maximum slew rate regardless of the input transient. The key is that the actuator should never see a step change faster than it can safely handle.

For the highest-integrity systems, I'd consider a windowed comparator that monitors the DAC output against expected bounds and disables the actuator driver if the output goes outside the valid range. This creates a "guard band" that catches transients before they reach the actuator. The challenge is setting the window tight enough to catch real faults but loose enough to avoid nuisance trips during normal operation, so I'd derive the window from the worst-case legitimate operating envelope plus margin.

Finally, I'd look at the system-level response: what does the actuator do when the drive signal is removed? If it fails safe (e.g., returns to a neutral position), then a fast crowbar or disconnect is appropriate. If it locks in its last state, I'd need to ensure the recovery sequence is well-defined. The trade-off is between availability—keeping the actuator operational—and safety—preventing a dangerous output. For a life-support or propulsion system, safety wins, and I'd design for a fail-safe disconnect with a clear recovery path.

**Possible follow-ups:** How would you size the output filter to avoid interfering with normal control loop bandwidth? What if the actuator requires a continuous signal and cannot tolerate being disconnected?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." How would you handle this disagreement?

**Answer:** I'd start by acknowledging the engineer's point—the power level is indeed low, and the risk of a destructive event is probably small. But the argument conflates two different things: the probability of a radiation effect and the consequence of that effect. Even if the probability of an SEL or TID-induced failure is low, the consequence is that a critical analog rail disappears, which could take down the entire measurement chain. In a space system, you don't get to swap a part or reboot easily, so the risk assessment has to be consequence-weighted, not just probability-weighted.

I'd walk through the specific failure modes. For a linear regulator, the main concerns are TID-induced drift in the reference or pass element, which could shift the output voltage outside the ADC's acceptable range over the mission, and SEL, which could cause a latch-up that draws excessive current and potentially damages the part or the board. Even at 50mA, a latch-up could pull the input rail down and affect other loads sharing that rail. There's also the question of whether the part's internal bandgap reference is stable under TID—some commercial parts show significant drift that isn't specified in the datasheet.

Then I'd ask what the engineer knows about the part's construction and process. If it's a modern CMOS part on a thin oxide process, it might actually be relatively TID-tolerant, but without data, that's speculation. I'd suggest a pragmatic path: either select a part with existing radiation data, or run a limited TID test on a few samples to characterize the part. If budget and schedule don't allow testing, I'd look for a pin-compatible alternative with known radiation behavior, or add a simple post-regulation stage using a radiation-tolerant reference and pass element.

The deeper point I'd make is that "minimal risk" is not the same as "acceptable risk." In space systems, we accept risk only when we understand it and have a mitigation for the consequences. Without characterization data, the risk is unknown, and unknown risk in a critical path is generally not acceptable. I'd frame this as a shared problem: how do we get the engineer's design to work within the constraints, rather than simply rejecting the proposal.

**Possible follow-ups:** How would you prioritize which parts need radiation testing when you have limited budget? What if the commercial regulator is the only part that meets the electrical requirements?

---

## Q3: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental requirement is that a failed or corrupted update must never brick the system. That means the update path has to be designed with the same rigor as the application itself, and the boot architecture has to support recovery from any failure point.

My starting point is a multi-slot boot architecture. I'd have at least two application image slots in flash—a "known good" golden image and a "current" image—plus a small, immutable bootloader that is either in radiation-hardened flash or protected by ECC and scrubbing. The bootloader's job is to validate the current image before jumping to it, and if validation fails, fall back to the golden image. The golden image might be a reduced-functionality version that can maintain safe operation and support a re-update, rather than the full application.

For the update process itself, I'd use a copy-and-swap approach: the new image is written to the inactive slot, validated in place (checksum, signature, and possibly a test run in a sandboxed mode), and only then is the active slot pointer switched. This avoids the window where the system is running from a partially-written image. The switch itself should be atomic—a single write to a status word that the bootloader checks—and the status word should have redundancy or ECC protection.

During the update, I'd also consider power-loss resilience. If the system loses power mid-write, the bootloader must be able to detect that the inactive slot is incomplete and either retry or fall back. This means each slot needs a valid/invalid marker that is written last, after the entire image is verified. I'd also add a "boot counter" that increments on each boot attempt and resets after successful operation for a defined period—if the system fails to boot successfully three times in a row, the bootloader automatically reverts to the golden image.

For the flash itself, I'd use parts with ECC if available, and I'd implement scrubbing of the flash contents during idle time to correct single-bit errors before they accumulate into multi-bit errors. The update protocol should also include error detection on every packet, with retransmission, so that a corrupted packet is caught at the link level rather than propagating into the stored image.

Finally, I'd test the recovery paths explicitly: corrupt an image mid-write, simulate a power loss during update, flip bits in the active image, and verify the system always recovers to a known-good state. The test plan is as important as the design, because the failure modes are rare and you need to prove the recovery works before you're relying on it in orbit.

**Possible follow-ups:** How would you handle the case where the golden image itself becomes corrupted? How would you verify the new image is safe to run before switching to it?

---

## Q4: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** Clock distribution in a space system has two distinct challenges: maintaining signal integrity across the distribution network, and ensuring that a single-event upset in the clock path doesn't corrupt the timing for multiple devices simultaneously. I'd address both from the start.

For the distribution topology, I'd use a tree structure with a single master oscillator feeding a clock buffer or fan-out chip, rather than daisy-chaining from one device to the next. The master oscillator should be radiation-tolerant—either a qualified crystal oscillator or a TCXO with known TID behavior—and the fan-out buffer should have its own radiation characterization. Each branch of the tree should be independently terminated and impedance-controlled to avoid reflections, and I'd add series termination at the source and parallel termination at each destination.

The key design decision is whether to use a single-ended or differential clock. For ADCs and FPGAs, LVDS or LVPECL differential clocks are more robust to noise and have better-defined thresholds, which matters when a transient could otherwise cause a false clock edge. Differential signaling also gives you common-mode rejection, so a single-event transient that couples equally to both lines is less likely to cause a spurious edge. The trade-off is higher power and more board area, but for a synchronized sampling system, the robustness is worth it.

For fault tolerance, I'd consider a redundant clock source with automatic switchover. The secondary oscillator runs continuously, and a phase detector monitors the primary. If the primary fails or drifts out of spec, the switchover logic selects the secondary. The switchover itself has to be glitch-free—you don't want a runt pulse on the clock line during the transition—so I'd use a cross-barred switch or a PLL that can re-lock without disturbing the downstream devices. The challenge is that a simple mux can produce a glitch, so the switchover circuit needs to be designed carefully, possibly using a "make-before-break" approach or a clock-gating scheme that stops the clock cleanly, switches sources, and restarts.

I'd also add per-device clock monitoring. Each FPGA or ADC should have a clock-loss detector that can flag a missing or corrupted clock. This gives you early warning of a distribution problem and lets the system take corrective action—for example, reconfiguring the sampling schedule or switching to a redundant clock path—before data corruption propagates.

Finally, I'd think about the synchronization requirement itself. If the ADCs must sample simultaneously, the clock edges must arrive at each ADC within a tight skew window. This means the trace lengths from the fan-out buffer to each ADC must be matched, and I'd verify this with a timing analysis that includes the buffer's propagation delay variation over temperature and TID. The layout is as important as the circuit design here—a well-designed clock tree on paper can fail in practice if the PCB routing introduces skew.

**Possible follow-ups:** How would you handle the case where the redundant clock source also fails? What if the ADCs require a specific phase relationship between the clock and a trigger signal?

---

## Q5: Imagine you are leading a design review for a space-deployed system where a junior engineer has implemented triple modular redundancy (TMR) on all flip-flops in the FPGA design, but has not applied TMR to the configuration memory or the block RAM. The engineer argues that the configuration memory is "protected by the FPGA's built-in error detection" and the block RAM is "not critical." How would you handle this disagreement?

**Answer:** I'd begin by acknowledging what the engineer got right—TMR on the flip-flops is a solid foundation and addresses a significant class of single-event upsets. But the argument that configuration memory is adequately protected by built-in error detection needs scrutiny, because the failure modes are quite different.

For configuration memory, the built-in error detection typically means CRC checking, which detects corruption but does not correct it. The critical question is: what happens when an error is detected? If the FPGA responds by halting or reconfiguring, that's a system-level disruption that could take the entire payload offline, even if the flip-flop TMR would have masked the underlying upset. The CRC check might catch the error, but the recovery action could be worse than the original fault. I'd ask the engineer to walk through the specific response to a detected configuration error and whether the system can tolerate that response. If the answer is that the FPGA halts and requires external reconfiguration, then the configuration memory is effectively a single point of failure, and TMR on the flip-flops doesn't help.

For block RAM, the "not critical" claim needs to be tested against the actual data flow. If the block RAM stores coefficients, calibration data, or intermediate results that feed into the critical path, then an upset in that RAM could propagate into the TMR-protected logic and cause a majority-voter error. The engineer may have classified the RAM as non-critical based on its function, but I'd want to see a traceability analysis showing that no data from the block RAM reaches a critical output without validation. In my experience, "non-critical" RAM often turns out to be more important than it appears, especially when it holds state that the TMR logic depends on.

I'd also raise the question of what "TMR on all flip-flops" actually means in practice. If the TMR is applied at the logic level but the voting is done in a way that shares resources—for example, a single voter circuit that can itself be upset—then the TMR has a single point of failure. The engineer should be able to show that the voters are also triplicated or that the voting is distributed.

My approach would be to reframe the discussion around system-level reliability rather than component-level protection. The goal is not to protect every flip-flop, but to ensure that no single upset can cause a system-level failure. That requires a fault tree analysis that traces from each potential upset location to the system-level consequence. I'd ask the engineer to produce that analysis for the configuration memory and block RAM, showing either that an upset cannot reach a critical output or that the recovery mechanism is fast enough and safe enough. If the analysis shows a gap, then we add protection—scrubbing for the configuration memory, ECC or TMR for the block RAM—based on the actual risk, not on an assumption about what's critical.

**Possible follow-ups:** How would you determine which block RAM contents are actually critical? What scrubbing rate would you recommend for the configuration memory, and how would you trade that against the FPGA's availability?