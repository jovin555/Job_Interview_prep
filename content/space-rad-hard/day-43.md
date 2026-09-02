# space-rad-hard — Day 43

## Q1: How would you approach designing a fault-tolerant analog multiplexing scheme for a space-deployed system where a single-event transient (SET) on the mux select lines could route the wrong sensor channel to a precision ADC, potentially causing an incorrect control action?

**Answer:** The core problem is that a single-event transient on the mux address lines can silently corrupt which channel is being sampled, and if that corrupted reading feeds a control loop, the system could act on data from the wrong sensor. My approach would start at the architecture level rather than just adding filtering at the output.

First, I'd question whether a multiplexed ADC front-end is even the right topology for the critical channels. If there are only a few truly safety-critical sensors, dedicating a separate ADC input or a separate sample-and-hold per channel eliminates the mux failure mode entirely. That's the most robust option, though it costs board area and power.

If multiplexing is necessary, I'd consider the failure modes systematically. An SET on the select lines can cause three things: sampling the wrong channel, sampling a channel that isn't selected at all (e.g., an unconnected input or a shorted pair), or a transient glitch that settles back to the correct channel mid-conversion. Each has different consequences.

For mitigation, I'd use several complementary techniques. First, encode the channel selection with redundancy — for example, use a Gray-coded or parity-protected select word rather than a simple binary decode, so that a single-bit upset produces either an invalid code that can be rejected or an adjacent channel that's still within a plausible range. Second, I'd add a settling-time delay after changing channels before starting the conversion, and I'd verify the mux output has settled to within the ADC's LSB before sampling. Third, I'd implement plausibility checks in firmware: each channel should have expected ranges, rate-of-change limits, and cross-channel consistency checks. If a reading falls outside those bounds, the system should flag it, reject it, and either retry the conversion or switch to a safe default state rather than acting on the suspect value.

For the select line drive itself, I'd add series resistance and possibly filtering at the mux control inputs to attenuate fast transients, and I'd ensure the mux's power supply is well-decoupled so an SET on the supply doesn't corrupt the internal decode logic. Finally, I'd consider adding a second, independent mux or a redundant ADC path for the most critical channels, with a voting or cross-check scheme in firmware.

The key design principle is defense in depth: no single mitigation catches every failure mode, so you layer architectural choices, circuit-level filtering, and firmware validation to reduce the probability of an incorrect control action to an acceptable level.

**Possible follow-ups:**
- How would you handle the trade-off between adding a settling delay for mux switching and the need for high sample rates in a time-critical control loop?
- What specific plausibility checks would you implement in firmware, and how would you distinguish a genuine sensor fault from an SET-induced transient?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement?

**Answer:** This is a situation where the engineer is treating the problem as purely electrical when it's actually a system-level reliability and mission-assurance issue. The calibration routine argument is particularly problematic because it assumes the drift is static and predictable — but TID effects can be non-monotonic, and SETs are transient events that calibration cannot correct. The ADC's supply tolerance also doesn't help if the regulator itself latches up or its output collapses entirely.

I'd handle this by reframing the discussion around risk acceptance rather than technical correctness. The question isn't "will this regulator work?" — it's "what is the consequence if it fails, and who has authorized accepting that risk?" I'd walk through a structured analysis: identify the failure modes (TID-induced drift, SET on the output, SEL, single-event burnout), estimate the probability of each over the mission lifetime, and assess the consequence of each on the system's ability to meet its requirements. If the analog rail feeds a critical measurement that drives a control action, the consequence could be mission failure — not just a slightly degraded reading.

I'd also challenge the assumption that "no radiation data" means "no radiation risk." Absence of data is not evidence of safety. Commercial parts vary widely in their radiation tolerance, and some are surprisingly sensitive. Without test data, you're making an unquantified assumption.

If the engineer continues to push back, I'd escalate through the proper channels — not as a personal disagreement, but as a formal risk assessment that needs a decision from the project's systems engineering or program management. I'd document the analysis, the open questions, and the recommendation, and let the appropriate authority make an informed risk acceptance decision. In a safety-critical or mission-critical system, the engineer's opinion that "the risk is minimal" is not a substitute for a formal risk assessment.

That said, I'd also look for a middle ground. If the cost or schedule impact of a rad-hardened part is prohibitive, there might be alternatives: use a commercial part but add external protection (e.g., a current-limiting circuit for SEL, a crowbar or supervisor for overvoltage), or qualify the specific part with a targeted radiation test. The point is to make the risk visible and managed, not to silently accept it.

**Possible follow-ups:**
- How would you structure the risk assessment document, and what information would you require before accepting the risk?
- What external protection circuits could make a COTS regulator acceptable for a non-critical rail, and what residual risks would remain?

---

## Q3: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental requirement is that a failed or corrupted update must never leave the system in a state where it cannot boot and execute at least a minimal recovery function. That drives the architecture from the start.

The first decision is memory partitioning. I'd use at least two independent firmware images: a bootloader in protected memory (ideally radiation-hardened or write-protected flash) and at least one application image, preferably two for A/B redundancy. The bootloader must be simple, robust, and capable of validating and loading an application image. It should be small enough that it can be thoroughly tested and unlikely to contain bugs, since it's the last line of defense.

For the update process itself, I'd design it as a multi-stage transaction with validation at each step. The new image would be received in chunks, each with a CRC or hash, and stored in a staging area — either in a separate flash region or in the inactive bank. Only after the complete image has been received and its integrity verified would it be marked as the active candidate. The bootloader would then validate the candidate's header, checksum, and possibly a digital signature before committing to booting it.

The critical protection is the "two-image" scheme: the system always boots from the last-known-good image unless the new image passes all validation. If the new image fails to boot or fails a post-boot self-test within a timeout, the bootloader automatically reverts to the previous image. This requires a reliable "boot success" handshake — the application must explicitly signal the bootloader that it has initialized correctly, and the bootloader must have a watchdog or timer to detect a hang.

For radiation-induced corruption of the stored images themselves, I'd add periodic integrity checks. The bootloader or a background task can compute and verify checksums of the inactive image, and if corruption is detected, it can either mark that image as invalid or re-download it from a redundant source. The active image should also be monitored — if a critical section is corrupted, the system should be able to reboot into the bootloader and switch to the backup image.

I'd also consider the update transport. If the update comes from a ground station or external source, the link itself may introduce errors, so the protocol needs end-to-end integrity checking. And I'd design the update to be resumable — if the link drops mid-transfer, the system should be able to resume without restarting from scratch.

Finally, I'd test the recovery paths thoroughly on the ground: corrupt an image at various points, interrupt an update at various stages, and verify the system always recovers to a known-good state. The test plan is as important as the design itself.

**Possible follow-ups:**
- How would you handle the case where the bootloader itself is corrupted by a single-event upset?
- What metrics or criteria would you use to determine that a newly updated image is "healthy" before committing to it as the primary boot target?

---

## Q4: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** Clock distribution in a space environment has two distinct challenges: maintaining signal integrity across multiple loads, and ensuring that a single-event upset or component failure doesn't take down the entire timing network. I'd address both from the start.

For the topology, I'd use a dedicated clock buffer or fan-out tree rather than daisy-chaining clocks from one device to another. A tree structure isolates each load — if one branch fails or experiences an SET, the other branches are unaffected. The clock source itself should be a radiation-tolerant oscillator, and I'd consider redundancy at the source level: two oscillators with a selection mechanism, or a PLL that can lock to either source.

For the distribution, I'd pay careful attention to impedance matching, termination, and trace routing. The clock lines should be treated as transmission lines with controlled impedance, proper termination at the receivers, and minimal stub lengths. I'd use differential signaling (LVDS or similar) for longer runs or where noise immunity is critical, since differential pairs are less susceptible to single-event transients than single-ended lines.

The synchronization requirement for ADCs is the key constraint. If all ADCs must sample simultaneously, the clock edges must arrive at each ADC within a tight skew budget. I'd use length-matched traces or delay adjustment to equalize propagation delays, and I'd verify the skew with a high-bandwidth oscilloscope during bring-up. For very tight synchronization, I'd consider a dedicated sync pulse in addition to the clock — a separate line that triggers the sample-and-hold across all ADCs simultaneously, with the clock used only for conversion timing.

For radiation tolerance, I'd add filtering and protection on the clock lines to attenuate transients, and I'd consider a clock-monitoring circuit that detects loss of clock or excessive jitter and switches to a redundant source. The monitoring circuit itself needs to be radiation-tolerant — a simple PLL or frequency comparator can detect a clock that's stopped or drifted outside tolerance.

One subtle issue is that an SET on a clock buffer's output can cause a glitch that propagates to all downstream devices. I'd mitigate this by using clock buffers with built-in glitch suppression, or by adding a small RC filter at each receiver input to reject narrow transients — though this adds delay and must be balanced against the skew budget.

Finally, I'd verify the entire network under worst-case conditions: temperature extremes, supply voltage variation, and radiation testing if possible. The clock is the heartbeat of the system, and a failure there can cause anything from corrupted data to a complete system hang.

**Possible follow-ups:**
- How would you detect and recover from a clock failure during operation, and what would the system do in the interim?
- What trade-offs would you consider between using a single high-frequency clock with dividers versus multiple lower-frequency clocks distributed to different subsystems?

---

## Q5: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement, and how would you ensure the design review process remains constructive rather than adversarial?

**Answer:** This is as much a leadership and communication challenge as a technical one. The engineer has proposed a solution, heard counterarguments, and is defending their position — which is actually good engineering behavior if channeled correctly. My goal is to move from a debate about the specific part to a structured decision-making process that the whole team can support.

First, I'd acknowledge the engineer's valid points. The calibration routine does address slow, monotonic drift, and the ADC's supply tolerance does provide some margin against small transients. By validating what their approach handles correctly, I build credibility and reduce defensiveness.

Then I'd reframe the discussion around the failure modes their approach doesn't address. Calibration cannot correct for a sudden, non-monotonic shift in output voltage. The ADC's supply tolerance doesn't help if the regulator latches up and the rail collapses entirely, or if an SET on the regulator's internal reference causes a transient that exceeds the ADC's absolute maximum rating rather than just its specified tolerance. I'd ask the engineer to walk through each failure mode and explain how their design handles it — this turns the disagreement into a joint analysis rather than a confrontation.

I'd also introduce the concept of risk ownership. In a space-deployed system, the engineer proposing a COTS part is implicitly accepting risk on behalf of the mission. That risk acceptance needs to be documented, quantified, and approved by someone with the authority to make that call. I'd ask the engineer to draft a formal risk assessment — failure modes, estimated probabilities, consequences, and mitigation options — which serves two purposes: it forces rigorous thinking, and it creates a record that can be reviewed by the broader team or program management.

If the engineer still resists, I'd offer a compromise path. Perhaps the part can be used but with additional protection: a current limiter for SEL, a voltage supervisor to detect out-of-tolerance output, or a targeted radiation test to characterize the specific part. These add cost and complexity, but they might be acceptable if the schedule or budget for a rad-hardened part is prohibitive.

Throughout this, I'd keep the tone collaborative. The goal isn't to "win" the argument — it's to reach the best decision for the mission. I'd explicitly say that the engineer's willingness to defend their design is valuable, and that the review process is exactly where these questions should be raised. If we reach an impasse, I'd escalate to a formal design review with the project's systems engineer or chief engineer, presenting both perspectives and the analysis we've done. The decision then rests with the appropriate authority, and everyone can support it because the process was transparent and rigorous.

**Possible follow-ups:**
- How would you handle the situation if the engineer's manager or the program manager overrules your technical recommendation for schedule reasons?
- What would you do differently if this same disagreement arose again with a different engineer on a future project?