# space-rad-hard — Day 42

## Q1: How would you approach designing a radiation-tolerant current-sense circuit for a spacecraft power bus, where the sense resistor itself is exposed to radiation and its value may drift over the mission lifetime?

**Answer:** The first consideration is that the sense resistor is a passive component, so it won't experience single-event effects, but it can be affected by total ionizing dose and displacement damage, which can cause resistance drift. I'd start by selecting a resistor technology that's known to be relatively stable under radiation — metal foil or bulk metal film resistors tend to have better stability than thick film or carbon composition types. I'd also derate the resistor's power dissipation significantly, since self-heating can accelerate any radiation-induced drift.

For the measurement architecture, I'd use a four-wire Kelvin connection to eliminate lead and trace resistance from the measurement. The amplifier circuit itself needs radiation-tolerant components — an instrumentation amplifier or precision op-amp with known radiation behavior. I'd also consider the fact that the sense resistor's drift will appear as a gain error in the current measurement, so I'd design the system to accommodate periodic calibration. This could mean including a precision current source that can be switched in during calibration to measure the actual sense resistance, or designing the system to tolerate a known drift envelope.

I'd also think about the voltage drop across the sense resistor. A larger resistance gives better signal-to-noise ratio but wastes power and creates more heat. A smaller resistance reduces power loss but makes the measurement more susceptible to offset and noise errors. The trade-off depends on the current range and the accuracy required. Finally, I'd consider whether to use two sense resistors in parallel — if one drifts or fails open, the other still provides a measurement path, though with a known change in calibration.

**Possible follow-ups:**
- How would you determine the acceptable drift envelope for the sense resistor over the mission lifetime, and how would that feed into your calibration strategy?
- What failure modes other than resistance drift would you consider for a sense resistor in a space environment?

---

## Q2: You are reviewing a design for a space-deployed system where a junior engineer has placed a single ferrite bead in series with the ADC's analog supply rail to filter switching noise from the DC-DC converter. The ferrite bead has no radiation characterization, and the ADC's power supply rejection ratio (PSRR) is already specified as 60 dB at 1 MHz. How would you evaluate this design choice?

**Answer:** I'd start by separating the two concerns: the ferrite bead's filtering function and its radiation tolerance. On the filtering side, a ferrite bead in series with the analog supply is a common technique to attenuate switching noise, but it's only effective if the impedance at the switching frequency is appropriate and if there's adequate decoupling capacitance on the ADC side of the bead to form a low-pass filter. The ADC's PSRR of 60 dB at 1 MHz tells us how well the ADC rejects supply noise that reaches its pin, but it doesn't eliminate the need for filtering — it just sets the budget for how much noise can be present.

The bigger issue is the radiation tolerance. A ferrite bead is a magnetic component, and its impedance characteristics can change under total ionizing dose due to changes in the ferrite material's permeability. It could also potentially experience single-event effects, though these are less well-documented for passive magnetic components. Without radiation data, we're assuming the bead's impedance characteristics remain stable over the mission, which is an unverified assumption.

I'd recommend one of two paths. First, we could look for a ferrite bead with existing radiation test data — some vendors do provide this for space-qualified parts. Second, if no radiation data exists, we could either accept the risk with a documented rationale and a test plan to characterize the part, or we could redesign the filtering to use components with known radiation behavior — for example, a simple RC filter using a series resistor and a capacitor, where both components have well-understood radiation responses. The resistor approach has the downside of DC voltage drop, but for a low-current analog rail, that's often acceptable.

I'd also question whether the ferrite bead is even necessary. If the ADC's PSRR is adequate and the layout properly separates analog and digital ground planes, the bead might be adding complexity without meaningful benefit. I'd want to see the noise analysis that justifies the filtering requirement.

**Possible follow-ups:**
- How would you characterize the ferrite bead's radiation response if you had to use it? What test would you design?
- What's the difference in approach between filtering a supply rail for a precision ADC versus filtering a digital supply rail?

---

## Q3: How would you approach designing a fault-tolerant analog-to-digital conversion subsystem for a space-deployed system where a single-event transient (SET) on the sample-and-hold circuit could corrupt a critical measurement, and the system cannot simply retry because the measurement is time-sensitive?

**Answer:** This is a case where we need both hardware and firmware mitigation because we can't rely on retry. The first line of defense is at the circuit level. I'd consider using two independent ADC channels sampling the same signal simultaneously, with separate sample-and-hold circuits and separate reference paths. If the two readings agree within a tolerance band, we accept the measurement. If they disagree, we have a fault indicator — but we still need to decide what value to use.

For the voting logic, I'd think about whether we need a third channel for true majority voting, or whether two channels with a plausibility check are sufficient. In a time-sensitive system, a third channel adds complexity and cost, but it gives us a definitive answer when two channels disagree. With only two channels, a disagreement leaves us uncertain which one is correct.

At the firmware level, I'd implement a plausibility check based on the expected signal characteristics. For example, if we're measuring a motor speed or a physiological parameter, we know the rate at which the signal can legitimately change. A sample that jumps beyond that rate is suspect. We could also use a median filter over the last three samples — if the current sample is an outlier compared to the previous two, we can flag it and use a predicted value based on the signal's dynamics.

I'd also look at the sample-and-hold circuit itself. Using a larger hold capacitor makes the circuit less susceptible to single-event charge injection, at the cost of slower acquisition time. If the signal bandwidth allows, this is a simple and effective mitigation. Similarly, I'd consider adding a small RC filter at the ADC input to limit the bandwidth and reduce the impact of transients on the input signal path.

Finally, I'd think about the system-level response. Even with all these mitigations, a corrupted measurement might still get through. The control system should be designed to tolerate a single bad sample — for example, by limiting the slew rate of actuator commands or by having a watchdog that detects out-of-range control actions.

**Possible follow-ups:**
- How would you determine the tolerance band for accepting two ADC readings as "in agreement"?
- What are the trade-offs between using two channels with plausibility checking versus three channels with majority voting?

---

## Q4: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement?

**Answer:** When an engineer continues to push back after the technical risks have been explained, I'd first make sure we're actually disagreeing about the same thing. The engineer's argument has two parts: that the load is small, and that the system can tolerate the effects. I'd acknowledge that the load is indeed small — that's not in dispute. The question is whether the failure modes of the regulator are acceptable, and that's where I'd focus the discussion.

I'd ask the engineer to walk me through the specific failure modes and their system-level consequences. For TID drift, what happens if the output voltage drifts outside the ADC's input range? The calibration routine can correct for a fixed offset or gain error, but it can't correct for a supply that's out of specification. For a SET on the regulator's reference, what happens if the output momentarily spikes or dips? The ADC's PSRR might reject some of that, but a large enough transient could still corrupt a measurement. And for SEL, what happens if the regulator latches up and draws excessive current? That could take down the entire rail, not just the analog section.

I'd also ask the engineer to quantify the risk. What's the probability of each failure mode, and what's the consequence? If the engineer can't provide that analysis, then the argument that "the risk is minimal" is an assertion, not an engineering assessment. I'd suggest we do a formal risk assessment using the ISO 14971 framework — even though this is a space system, the same principles of risk analysis, risk evaluation, and risk control apply.

If the engineer still disagrees after that analysis, I'd escalate the decision. In a design review, the lead engineer has the responsibility to make the final call, but I'd want to document the disagreement and the rationale for the decision. I'd also suggest a compromise: use the commercial regulator for now, but add a test plan to characterize its radiation response, and design the board with a footprint that allows swapping in a radiation-tolerant part if the test results warrant it.

**Possible follow-ups:**
- How would you structure a formal risk assessment for this decision, and what inputs would you need from the engineer?
- At what point would you escalate this disagreement to a higher authority, and how would you document it?

---

## Q5: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The core principle is that we must never be in a position where a corrupted update leaves the system without a known-good firmware image. That means we need redundancy in the firmware storage and a boot sequence that can recover from a bad update.

I'd start with a dual-bank or A/B partition scheme in flash. The system boots from one bank while the other is available for updates. The bootloader validates the active bank before jumping to it — checking a CRC or cryptographic signature. If the active bank fails validation, the bootloader falls back to the other bank. This gives us a known-good image to recover from.

For the update process itself, I'd use a multi-stage approach. First, the new image is downloaded to a staging area in RAM or a separate flash region. The image is validated — CRC, signature, and possibly a test that checks for structural integrity. Only after validation is the image written to the inactive bank. The write process itself needs to be robust: if a single-event upset corrupts a word during the write, we need to detect it. Writing the image twice and comparing, or reading back after writing and verifying, are both options.

The boot sequence also needs to handle the case where the update is written successfully but the new image is faulty. The bootloader should attempt to boot the new image, but if it fails to initialize within a timeout, it should automatically revert to the previous bank. This requires a watchdog or a boot counter that the bootloader increments on each attempt and the application resets after successful initialization.

I'd also consider the radiation effects on the flash itself. Flash memory can experience bit flips in the stored data, so the inactive bank should be periodically scrubbed — read, check, and rewrite if errors are found. The bootloader itself should be stored in a radiation-tolerant memory, or at least have a copy in a protected region.

Finally, I'd think about the update command path. The update should be triggered by a command from the ground or from a trusted source, and the update process should be resumable — if the link drops mid-download, we don't want to start over from scratch. A resumable protocol with checkpoints is important for long updates over a constrained link.

**Possible follow-ups:**
- How would you handle the case where both firmware banks are corrupted — for example, after a large solar particle event?
- What are the trade-offs between using CRC versus a cryptographic signature for firmware validation, given the processing power available on the flight microcontroller?