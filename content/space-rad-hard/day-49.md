# space-rad-hard — Day 49

## Q1: How would you approach designing a fault-tolerant analog output stage for a space-deployed system where a single-event transient (SET) on a DAC's reference voltage could cause a momentary but dangerous output spike to an actuator?

**Answer:** I'd approach this by first recognizing that the reference voltage is the most sensitive node in the analog chain—a transient there directly modulates the DAC's full-scale output. My strategy would be layered:

**At the reference itself:** I'd use a precision reference with known radiation performance, and add a low-pass filter (e.g., RC or active filter) with a time constant that attenuates transients faster than the control loop's response time but slower than the reference's settling requirement. The filter bandwidth should be chosen so that legitimate reference changes (e.g., during calibration) pass through, but nanosecond-to-microsecond SETs are suppressed.

**At the output stage:** I'd add a slew-rate limiter or a clamping circuit on the DAC output before it reaches the actuator driver. This ensures that even if a transient slips through, the rate of change or absolute voltage at the actuator is bounded. For a motor or valve actuator, a hardware rate limiter is often more reliable than relying on firmware to catch the event.

**At the system level:** I'd implement redundant measurement—if the actuator command is critical, I'd use two DAC channels with independent references and vote on the output, or use a sample-and-hold that latches the commanded value and only updates on a validated write. This prevents a single transient from propagating to the actuator.

**In firmware:** I'd add a plausibility check—if the commanded output changes by more than a defined maximum rate or exceeds a safe range, the firmware would flag it and revert to a safe state. But this is a backstop, not the primary defense.

The key trade-off is between response time and transient immunity. A heavily filtered reference makes the system slower to respond to legitimate commands, so I'd characterize the actuator's actual bandwidth requirements and design the filter to pass the control signal while rejecting transients.

**Possible follow-ups:** How would you test that your filter actually rejects SETs of various durations and amplitudes? What if the actuator requires a fast response that conflicts with your filter time constant?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement, and how would you ensure the design review process remains constructive rather than adversarial?

**Answer:** I'd handle this by reframing the discussion from "is this part risky?" to "what is the quantified risk, and does our mitigation actually cover the failure modes?" The engineer's argument conflates two different things: calibration can correct for DC offset or gain drift, but it cannot correct for a transient that occurs during an actual measurement, nor does it help if the regulator latches up and shorts the rail.

I'd walk through the specific failure modes systematically:
- **TID drift:** Calibration could handle this if the drift is slow and monotonic, but only if the calibration interval is shorter than the drift rate. I'd ask: what's the expected drift per year, and how often do we calibrate?
- **SET on the output:** A brief transient on the rail could corrupt a measurement in progress. Calibration doesn't help because the error is transient and non-repeating. The ADC's PSRR might attenuate it, but only at certain frequencies—I'd ask the engineer to check the PSRR curve against the expected transient spectrum.
- **SEL:** If the regulator latches up, it could draw excessive current and potentially damage itself or the board. Calibration is irrelevant here. The real question is: what happens to the rest of the system when this rail collapses?

I'd also suggest a middle path: rather than arguing about whether the part is acceptable, we could do a quick risk assessment—what's the consequence of each failure mode, and what's the probability? If the consequence is a corrupted measurement that could be caught by a plausibility check, maybe the risk is acceptable. If it could cause an incorrect control action, it's not.

To keep the review constructive, I'd acknowledge the engineer's point where valid—yes, a 50mA rail is lower risk than a 3A rail, and yes, calibration handles some drift—but I'd insist on documenting the decision with a formal risk assessment rather than relying on intuition. I'd also offer to help the engineer find a radiation-characterized alternative or a way to test the specific part if budget allows. The goal is to make the decision based on data, not on who argues more persuasively.

**Possible follow-ups:** How would you structure that risk assessment in practice? What if the schedule pressure makes a formal assessment impractical—how would you prioritize?

---

## Q3: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The core principle is that you must never have a single point of failure in the update path—both the update mechanism and the storage must be resilient. I'd design this in layers:

**Bootloader design:** I'd use a two-stage bootloader. The first stage (in ROM or write-protected flash) is minimal and immutable—it only knows how to validate and jump to the second stage. The second stage handles application updates. This way, even if the application and the second-stage bootloader are both corrupted, the first stage can still recover the system.

**Image storage:** I'd keep at least two copies of the application firmware—a "golden" known-good image and a "current" image. The golden image is write-protected after initial programming and is only updated through a separate, highly controlled process. The current image is what normally runs. If the current image fails validation, the bootloader falls back to the golden image.

**Update validation:** Before writing new firmware, I'd validate the entire image—checksum, signature, and version check. During the write, I'd write to a scratch partition first, then validate the scratch copy, then atomically swap the pointers or use a flag to indicate which partition is active. This prevents a partial write from corrupting the running image.

**Radiation-specific considerations:** Flash itself can experience bit flips, so I'd add ECC or at least periodic scrubbing of the firmware storage. If the flash is read while the system is running, I'd verify each read against a stored checksum. For the update process itself, I'd use a protocol with error detection and retransmission—if a single packet is corrupted, the entire update isn't rejected, just that packet is retransmitted.

**Recovery path:** If both images are corrupted (e.g., a radiation event during the update window), the bootloader needs a way to recover—either from a ground command via a separate interface, or from a watchdog that detects repeated boot failures and enters a safe mode. The key is that the recovery path must not depend on the same flash that was corrupted.

The trade-off is between flash space (multiple images cost space) and reliability. For a critical system, the cost of an extra flash partition is worth the ability to recover.

**Possible follow-ups:** How would you handle the case where the update itself is interrupted by a radiation event—say, a SEFI in the microcontroller mid-write? How would you verify the golden image hasn't been corrupted over a multi-year mission?

---

## Q4: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** Clock distribution in a radiation environment has two distinct concerns: the clock source itself (oscillator upsets) and the distribution network (buffers, PLLs, and traces that can introduce skew or lose synchronization). I'd address both:

**Clock source redundancy:** I'd use at least two independent clock sources—for example, a master oscillator and a backup. The system needs a way to detect when the master has failed or drifted (e.g., frequency monitoring against a reference) and switch to the backup seamlessly. For synchronized sampling, the switchover must not cause a phase discontinuity that corrupts the sampling instant.

**Distribution topology:** I'd use a dedicated clock buffer with multiple outputs rather than daisy-chaining, so a failure in one branch doesn't affect others. Each FPGA and ADC gets its own buffer output. The trace lengths should be matched to minimize skew, and I'd use differential signaling (LVDS or similar) for the clock to reduce noise coupling and single-ended transient susceptibility.

**Synchronization scheme:** For ADCs that must sample simultaneously, I'd use a shared sample clock plus a synchronization pulse. The FPGAs would align their sampling to the sync pulse, not just the clock edge. This way, even if a clock transient causes a momentary glitch, the next sync pulse re-establishes alignment.

**Radiation-specific mitigation:** Clock buffers and PLLs can experience single-event transients that cause a brief frequency or phase shift. I'd add a phase-locked loop with a narrow bandwidth on each FPGA to filter out short transients, and I'd monitor the lock status. If a PLL loses lock, the system should flag it and potentially resynchronize rather than continuing with an unstable clock.

**Testing:** I'd verify the clock distribution under radiation testing—specifically looking for SET-induced jitter or phase hits on the clock lines. The test would need to measure phase alignment between multiple channels during irradiation, not just check that the clock is still running.

The key trade-off is between a simple, single-clock design (easier to synchronize, but a single point of failure) and a redundant, distributed design (more complex, but resilient). For a system requiring synchronized sampling over a multi-year mission, the complexity is justified.

**Possible follow-ups:** How would you detect that a clock source has drifted or failed in a way that's subtle—not a complete loss, but a frequency error? How would you handle the resynchronization of ADCs after a clock glitch without losing data?

---

## Q5: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement, and how would you ensure the design review process remains constructive rather than adversarial?

**Answer:** I'd recognize that this is now a disagreement about risk tolerance and evidence, not about technical facts—and I'd treat it as such. The engineer has made a claim ("the risk is minimal") and proposed a mitigation ("calibration and ADC tolerance"). My job is to test that claim with data, not to win an argument.

First, I'd ask the engineer to quantify the risk. What specific radiation environment are we designing for? What's the expected TID over the mission? What's the expected flux of heavy ions that could cause an SEL? Without those numbers, "minimal" is just an opinion. I'd ask the engineer to produce a simple risk matrix: for each failure mode (TID drift, SET, SEL), what's the probability and what's the consequence?

Second, I'd test the mitigation claims. The calibration routine—how often does it run, and what's the expected drift rate of this regulator under TID? If the drift is faster than the calibration interval, the calibration doesn't help. The ADC's tolerance to supply transients—what's the actual PSRR at the frequencies of interest, and what's the magnitude of the transient the regulator could produce? I'd ask the engineer to look up the ADC's PSRR curve and the regulator's transient response, not just assume they're compatible.

Third, I'd look for a compromise that addresses the underlying concern without forcing a full redesign. Options might include: adding a small RC filter on the regulator output to attenuate transients (cheap, low-risk), using a radiation-characterized reference instead of the regulator for the ADC's reference input (the reference is more critical than the rail), or adding a current limit on the regulator output to protect against SEL-induced latch-up.

To keep the review constructive, I'd frame it as a shared problem: "Help me understand why this part is the right choice, and let's figure out what additional evidence or mitigation would make me comfortable." I'd also make sure the decision is documented—if we proceed with the COTS part, we write down the risk assessment and the rationale, so that if it fails in testing or in orbit, we have a record of why we accepted the risk. That's not about blame; it's about learning.

If the engineer continues to resist, I'd escalate to a formal risk review with the broader team, not as a disciplinary action but as a way to get more perspectives. Sometimes a third party can see a mitigation or a concern that neither of us has considered.

**Possible follow-ups:** What if the schedule is too tight for a formal risk review—how would you make the call? How would you handle a situation where the engineer is technically correct that the risk is low, but the consequence of failure is catastrophic—how do you weigh those?