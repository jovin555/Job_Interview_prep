# space-rad-hard — Day 45

## Q1: How would you approach designing a fault-tolerant analog multiplexing scheme for a space-deployed system where a single-event transient (SET) on the mux select lines could route the wrong sensor channel to a precision ADC, potentially causing an incorrect control action?

**Answer:** This is a classic case where a single point of failure in the digital control path can corrupt an analog measurement, and the consequence isn't just bad data—it's potentially an incorrect control action. I'd approach this at several levels.

First, at the architecture level, I'd ask whether the mux is even necessary. If the system has enough ADC channels or can tolerate a dedicated ADC per critical sensor, eliminating the mux removes the failure mode entirely. That's the cleanest mitigation, though it costs board space, power, and money.

If a mux is required, I'd look at the select line encoding. A SET that flips one bit in a binary-encoded select could route any channel. Using one-hot or Gray-coded selection reduces the chance that a single-bit upset lands on a completely different channel—adjacent channels are more likely, which may be more tolerable. Even better, I'd consider adding parity or a simple checksum to the select word, with the mux controller validating before committing the channel change.

Second, at the circuit level, I'd add filtering and voting on the select lines themselves. Since the select signals are digital and relatively slow (compared to the ADC conversion rate), RC filtering or Schmitt triggers can reject narrow transients. If the select lines come from an FPGA, I'd implement triple voting on the select state machine and register the outputs.

Third, at the system level, I'd add plausibility checking on the measurement side. The firmware or FPGA should know which channel it requested and can validate the reading against expected ranges. If a reading is wildly out of family—say a temperature sensor suddenly reports a pressure value—the system should flag it, reject it, and potentially revert to a safe state rather than acting on it. This is especially important in a life-support context where an incorrect control action could be dangerous.

Finally, I'd consider adding a sample-and-hold or buffer stage after the mux so that even if the select line glitches mid-conversion, the ADC is sampling a stable value. The key is defense in depth: no single mitigation catches every case, but layering them reduces the residual risk to an acceptable level.

**Possible follow-ups:** How would you determine whether a SET on the mux select is actually a credible threat compared to other radiation effects in the system? How would you test that your plausibility checking doesn't reject legitimate readings during transients or sensor degradation?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement, and how would you ensure the design review process remains constructive rather than adversarial?

**Answer:** This is a situation where I need to separate the technical disagreement from the interpersonal dynamic. The engineer isn't being difficult—they're making an argument based on their assessment of risk, and my job is to help them see the gaps in that assessment without dismissing their reasoning.

First, I'd acknowledge the parts of their argument that have merit. Yes, a 5V rail at 50mA is low power, and yes, the ADC's PSRR and the calibration routine do provide some tolerance. That's a fair starting point. But I'd then walk through the specific failure modes that their mitigation doesn't cover.

TID drift is the clearest issue. A calibration routine corrects for offset and gain errors at the time of calibration, but TID effects accumulate over the mission. The regulator's output voltage could drift slowly, and if the calibration is only performed occasionally—or if the drift happens between calibrations—the system is operating with an uncorrected error. Worse, TID can also affect the regulator's transient response, noise characteristics, and even its ability to start up correctly. Calibration doesn't fix a regulator that's slowly becoming unstable.

SETs are another matter. A single-event transient on the regulator output could cause a brief voltage dip or spike. The ADC's PSRR helps reject supply noise at certain frequencies, but a fast transient can bypass PSRR entirely, especially if it couples directly into the reference or the input path. And if that transient occurs during a critical conversion, the resulting error could trigger an incorrect control action. The calibration routine doesn't help because the error is transient, not systematic.

SEL is the most serious concern. If the regulator latches up, it could draw excessive current from the bus, potentially dragging down the rail or triggering a bus-level protection event that affects other loads. At 50mA, the latch-up current might be small, but the failure mode isn't about the steady-state current—it's about the fault current during latch-up and the potential for permanent damage.

I'd also raise the qualification question. Even if the engineer is right that the risk is low, we need to quantify it. Without radiation data, we're guessing. I'd suggest a few options: look for a similar part with radiation characterization, run a low-cost TID test on a few samples, or accept the risk but document it in the risk register with a clear rationale. The key is that the decision should be explicit and traceable, not implicit.

To keep the review constructive, I'd frame this as a shared problem: "Help me understand the worst-case scenario if this part fails in each of these modes. What's the impact on the mission? What's the probability? If we can show that the risk is acceptable, I'm happy to proceed. If not, let's look at alternatives." This turns the disagreement into a joint risk assessment rather than a battle of opinions.

**Possible follow-ups:** How would you document this decision in the risk management file? What alternative parts or architectures would you propose, and how would you trade off cost, schedule, and risk?

---

## Q3: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental challenge here is that a firmware update is a rare, high-stakes operation where a single corrupted bit can brick the system. The strategy needs to protect against two distinct threats: corruption of the update image during transfer, and corruption of the existing firmware during the update process itself.

I'd start with the boot architecture. The system should have a small, immutable bootloader in protected memory—ideally in ROM or a radiation-hardened flash that's write-protected after initial programming. This bootloader's only job is to validate and launch the application, and to support the update process. It should never be overwritten by an update.

The application flash should be divided into at least two banks: a current bank and a staging bank. The update process writes the new image to the staging bank, validates it completely, and only then switches the boot pointer to the new bank. If the update is corrupted, the system simply boots the old, known-good image. This is the classic A/B or ping-pong approach, and it's the most robust because it never modifies the running image until the new one is fully verified.

For the update transfer itself, I'd use strong error detection and correction. Each packet should have a CRC or checksum, and the complete image should have a hash—SHA-256 or similar—that's verified before the boot pointer is switched. If the system has the bandwidth, I'd also consider sending the image twice and comparing, or using a forward error correction scheme to recover from bit errors without retransmission.

The radiation concern adds another layer. Flash memory can experience SEUs that flip bits in stored data, and the update image sitting in the staging bank is vulnerable while it waits for validation. So the validation step shouldn't be a single pass—it should include scrubbing or repeated reads to catch upsets that occur between the write and the validation. If the image is large and the validation takes time, I'd consider validating in sections and refreshing the staging bank periodically.

I'd also think about the update trigger and authorization. A corrupted command stream could initiate an update at the wrong time or with a bad image. The bootloader should require a specific, authenticated command sequence to enter update mode, and the update process should have a timeout so that a partial or stalled update doesn't leave the system in an indeterminate state.

Finally, I'd design for recovery from a failed update. If the new image passes validation but fails during execution—say it crashes on startup—the bootloader should detect this via a watchdog or a "boot successful" flag that the application sets after initialization. If the flag isn't set within a timeout, the bootloader reverts to the previous bank. This adds a layer of protection beyond just image validation.

The key principle is that the update process must never be the single point of failure. Every step should have a fallback, and the system should always be able to return to a known-good state.

**Possible follow-ups:** How would you handle the case where the bootloader itself is corrupted? How would you test the update and recovery process in a way that simulates radiation-induced corruption?

---

## Q4: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** Clock distribution in a space system is a classic case where a single point of failure can take down the entire digital subsystem. If the clock stops, everything stops—and if the clock glitches, you can get metastability, data corruption, or subtle timing violations that are very hard to debug. I'd approach this with redundancy, monitoring, and careful layout.

First, I'd establish the clock sources. A single oscillator feeding everything is the simplest architecture, but it's also a single point of failure. I'd use at least two oscillators—ideally with different part numbers or at least different lot codes to avoid common-mode failure—and a clock supervisor that can switch between them. The supervisor should monitor both the presence and the frequency of each clock, and it should have hysteresis to avoid oscillating between sources if one is marginal.

The switching itself needs care. Simply gating between two clocks can produce a glitch or a runt pulse. I'd use a glitch-free clock mux or a PLL-based approach where the secondary clock is phase-locked to the primary, so the switch is seamless. If the clocks are free-running and not phase-aligned, the switch will cause a phase discontinuity, which could disrupt synchronized sampling. In that case, I'd design the system to tolerate a brief resynchronization period after a switch.

For the distribution network, I'd use a tree structure with dedicated clock buffers at each branch. Each FPGA and ADC should have its own buffer, so a fault on one branch doesn't affect the others. The buffers should be radiation-tolerant and have their own bypassing and filtering. I'd also consider using differential clock signaling—LVDS or similar—for longer traces, because it's more immune to noise and single-event transients than single-ended CMOS.

Synchronized sampling adds another requirement. If the ADCs need to sample at the same instant, the clock edges must arrive at each ADC with controlled skew. This means careful PCB layout—matched trace lengths, controlled impedance, and minimal vias—and possibly per-channel delay adjustment to compensate for residual skew. Some systems use a separate "sample sync" pulse that's distributed alongside the clock, which can be easier to align than trying to match the clock edges themselves.

I'd also add monitoring and fault detection. Each FPGA should have a clock loss detector that can flag a missing or degraded clock. The system should be able to identify which clock domain failed and take appropriate action—switch to the redundant clock, shut down non-critical functions, or enter a safe state. In a life-support context, the response to a clock fault needs to be predefined and tested, because there may be no time for operator intervention.

Finally, I'd consider the radiation effects on the clock generation itself. Oscillators can experience frequency shifts from TID, and PLLs can experience single-event transients that cause phase hits. I'd select components with known radiation behavior, and I'd design the PLL loop filter to be robust against transient disturbances. The goal is a clock network that can tolerate a single fault—or a single radiation event—without losing synchronization or corrupting data.

**Possible follow-ups:** How would you verify that the clock distribution network meets the skew requirements across temperature and radiation dose? How would you handle the case where the two clock sources drift apart in frequency over the mission?

---

## Q5: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement, and how would you ensure the design review process remains constructive rather than adversarial?

**Answer:** This scenario is really about risk ownership and decision-making under uncertainty, not just about the regulator. The engineer has made a reasonable engineering argument—low power, calibration, PSRR—but they're treating the absence of radiation data as evidence of low risk, which is a logical error. The absence of data means the risk is unknown, not that it's low.

I'd start by reframing the question. Instead of asking "Is this part safe?" I'd ask "What would it take to make us confident this part is safe enough for this application?" That shifts the conversation from opinion to evidence. If we can't get radiation data, can we get a similar part with data? Can we run a limited test? Can we bound the risk through analysis? The answer might be that the risk is acceptable, but it should be an explicit, documented decision, not an implicit one.

I'd also introduce the concept of criticality. The engineer is focused on the electrical specifications—5V, 50mA—but the real question is what happens if this rail fails. If it powers the analog front-end for a life-support monitor, a transient or drift could cause an incorrect reading that leads to an incorrect clinical decision. That's a patient safety issue, not just a technical issue. The risk assessment needs to include the consequence of failure, not just the probability.

To keep the review constructive, I'd use a structured approach. I'd ask the engineer to walk through the failure modes and their mitigations in a formal way—maybe a simple FMEA or a risk matrix. This forces the discussion to be systematic rather than adversarial. I'd also bring in the regulatory context: for a medical device, the design needs to be traceable to a risk management file, and the decision to use an uncharacterized part needs to be justified and documented. That's not bureaucracy—it's how we ensure patient safety.

If the engineer still disagrees after a thorough analysis, I'd escalate the decision. In a design review, the lead engineer has the authority to make the final call, but I'd frame it as "I'm making this decision based on the risk assessment, and here's my reasoning. If you have additional data or analysis that changes the picture, I'm happy to revisit it." This respects the engineer's input while making it clear that the responsibility for the decision rests with the lead.

The key is to keep the process collaborative. The goal isn't to win an argument—it's to make the best decision for the mission and the patient. If the engineer feels heard and understands the reasoning behind the final decision, they'll be more likely to support it, even if they initially disagreed.

**Possible follow-ups:** How would you document this decision in the risk management file to satisfy regulatory requirements? What alternatives would you propose, and how would you trade off the cost and schedule impact of using a qualified part versus the risk of using the COTS part?