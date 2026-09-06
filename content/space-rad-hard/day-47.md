# space-rad-hard — Day 47

## Q1: How would you approach designing a fault-tolerant reset distribution network for a space-deployed system where multiple FPGAs and microcontrollers must be reset coherently after a single-event upset, but a single shared reset line could propagate a fault across all devices?

**Answer:** The core tension here is between coherent reset behavior and fault isolation. I'd start by defining what "coherent" actually means for the system — do all devices need to reset simultaneously, or do they need to reset in a specific sequence with validated handshakes between stages? In many space systems, a staggered reset is actually preferable because it lets a supervisory controller verify each device comes up correctly before releasing the next one.

For the distribution network itself, I would avoid a single shared reset line driven by one source. Instead, I'd architect it hierarchically: a radiation-hardened supervisor or CPLD generates reset commands, but each device receives its reset through an independent buffer or gate that the supervisor can control individually. This lets the supervisor reset one device without disturbing others, while still supporting a global reset command when needed.

I'd also consider the failure modes of the reset path itself. A reset line that gets stuck asserted is just as dangerous as one that never asserts. Using pull-up/pull-down resistors with defined default states, adding series resistors to limit fault current, and monitoring the actual reset state (rather than just commanding it) are all important. The supervisor should be able to detect a stuck reset line and isolate it.

For the supervisor itself, I'd want diversity — perhaps two independent watchdog paths with different mechanisms (one hardware timer, one software health check) so that a single SEU can't prevent reset generation. And critically, the reset network needs its own protection: if the supervisor is an FPGA, its configuration memory needs scrubbing or it needs to be a simpler, more robust device like a rad-hard CPLD or discrete logic.

Finally, I'd verify the reset timing across temperature and voltage extremes. Reset thresholds drift with TID, so the design needs margin between the supervisor's trip points and the devices' minimum valid reset voltage.

**Possible follow-ups:** How would you handle the case where one device fails to come out of reset correctly? What redundancy would you put in the supervisor itself to ensure it can't be permanently disabled by an SEU?

---

## Q2: How would you approach designing a radiation-tolerant current-sense circuit for a spacecraft power bus, where the sense resistor itself is exposed to radiation and its value may drift over the mission lifetime?

**Answer:** This is a good example of where you can't just design for the nominal case — you have to design for the drift envelope. First, I'd select the sense resistor material carefully. Metal foil or precision metal film resistors generally have better radiation stability than thick-film resistors, which can exhibit significant resistance drift under TID. I'd also derate the resistor's power dissipation well below its rating, since self-heating can compound radiation-induced drift.

For the measurement path, I'd use a four-wire Kelvin connection to eliminate lead and contact resistance from the measurement. The amplifier should be a radiation-tolerant instrumentation amplifier or a discrete design using rad-hard op-amps. I'd also consider using two independent sense paths with different gain settings — one for coarse current monitoring and one for fine measurement — so that if one path drifts, the other provides a cross-check.

Calibration is essential. I'd design the circuit with a known calibration current source that can be switched in periodically to measure the actual sense resistance in-situ. This lets the system recalibrate the current measurement over the mission, compensating for any drift. The calibration current itself needs to be derived from a radiation-tolerant reference, so you're not just trading one drift source for another.

I'd also think about single-event effects on the sense amplifier. A SET on the amplifier output could cause a spurious overcurrent reading that triggers a false trip. I'd add filtering to reject short transients, and I'd implement the overcurrent protection with a time-current curve — a short spike shouldn't trip the breaker, but a sustained overcurrent should. This is analogous to how you'd design inrush handling: the protection needs to distinguish between a real fault and a transient event.

**Possible follow-ups:** How would you verify the calibration circuit itself hasn't drifted? What failure rate would you consider acceptable for the protection function, and how would you test for it?

---

## Q3: You are reviewing a design for a space-deployed system where a junior engineer has placed a single ferrite bead in series with the ADC's analog supply rail to filter switching noise from the DC-DC converter. The ferrite bead has no radiation characterization, and the ADC's power supply rejection ratio (PSRR) is already specified as 60 dB at 1 MHz. How would you evaluate this design choice?

**Answer:** I'd approach this by separating the two concerns: does the ferrite bead provide meaningful filtering, and is its lack of radiation characterization a real risk?

On the filtering question, a ferrite bead's impedance is frequency-dependent, and its effectiveness depends on the source impedance of the DC-DC converter and the load impedance of the ADC. A single bead without a capacitor to ground on the ADC side forms a poor filter — you really need a pi-filter (bead-capacitor-bead or capacitor-bead-capacitor) to get significant attenuation. Also, ferrite beads have DC resistance that causes voltage drop under load, which could push the ADC supply out of tolerance if the current draw is significant.

On the radiation question, ferrite beads are passive magnetic components. Their primary radiation concern is TID-induced changes to the ferrite material's permeability, which could shift the bead's impedance characteristics over the mission. This is generally a slow degradation rather than a single-event effect, but it means the filtering performance at end-of-life could be worse than at beginning-of-life. The lack of radiation data means we can't quantify this shift.

The PSRR argument is worth examining carefully. PSRR is frequency-dependent and typically specified with ideal supply conditions — it assumes the supply is a clean source with a specific impedance. In practice, the interaction between the DC-DC converter's output impedance, the ferrite bead, and the ADC's input impedance can create resonances that actually amplify noise at certain frequencies. So the PSRR spec doesn't guarantee the ADC will be immune to the converter's switching noise.

My recommendation would be to characterize the actual noise environment — measure the converter's output ripple and switching transients at the ADC supply pin with the proposed filter — and verify the ADC's performance with that noise present. If the bead is needed, I'd want to understand its radiation behavior or select a part with known radiation performance. If the PSRR is genuinely sufficient, the bead may be unnecessary complexity that adds an uncharacterized component.

**Possible follow-ups:** What measurements would you run to verify the filter is actually needed? How would you handle the case where the bead is needed but no radiation data exists?

---

## Q4: How would you approach designing a fault-tolerant analog-to-digital conversion subsystem for a space-deployed system where a single-event transient (SET) on the sample-and-hold circuit could corrupt a critical measurement, and the system cannot simply retry because the measurement is time-sensitive?

**Answer:** This requires a layered approach because no single mitigation will be sufficient. The first layer is at the circuit level: I'd look at the ADC's architecture and how it implements the sample-and-hold. Some ADCs use a switched-capacitor front end where the sampling capacitor is charged through a switch — a SET that disturbs the switch control or the reference during the sampling window can corrupt the charge. Using an external sample-and-hold with a larger sampling capacitor can make the circuit more immune to charge injection from SETs, at the cost of slower acquisition.

The second layer is at the system level: even if a single sample is corrupted, can we detect it? If the measurement has known bounds or rate limits, a plausibility check can flag samples that are physically impossible. For example, in a temperature measurement, a reading that jumps 50 degrees in one sample period is almost certainly corrupted. This requires understanding the physical dynamics of what you're measuring.

The third layer is temporal redundancy with voting. Even if you can't retry the exact same sample, you can take multiple samples in quick succession and vote or average them. If the SET is a transient that affects only one sample, three samples with majority voting will reject the corrupted one. The key is that the samples need to be close enough in time that the underlying signal hasn't changed significantly, but far enough apart that a single SET is unlikely to affect more than one. This trades off measurement latency against reliability.

For truly time-sensitive measurements where even one sample period of delay is unacceptable, I'd consider redundant ADC channels measuring the same signal simultaneously, with voting in the digital domain. This doubles or triples the analog front-end, but provides true single-event immunity for the conversion function.

Finally, I'd think about what happens downstream. Even with all these mitigations, a corrupted measurement could still slip through. The control system should have its own rate limiting and fault detection so that a single bad reading doesn't cause a dangerous actuator command. The ADC subsystem should also flag when it detects a potential SET (e.g., when voting disagrees), so the system can log the event and potentially adjust its operating mode.

**Possible follow-ups:** How would you choose between temporal redundancy and spatial redundancy (multiple ADC channels)? What are the failure modes of the voting logic itself?

---

## Q5: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." You've explained the risks of TID drift, SETs, and SEL, but the engineer pushes back, saying that the system has a calibration routine and the ADC can tolerate brief supply transients. How would you handle this continued disagreement, and how would you ensure the design review process remains constructive rather than adversarial?

**Answer:** When an engineer continues to push back after the technical risks have been explained, it usually means one of two things: either they don't fully appreciate the severity of the failure modes, or they feel their design is being dismissed without adequate consideration. My approach would be to address both possibilities.

First, I'd reframe the discussion from abstract risk to concrete failure scenarios. Rather than saying "radiation can cause problems," I'd walk through specific, credible scenarios: What happens when the regulator's output drifts 10% due to TID? What happens when a SET causes a 100mV transient on the rail during an ADC conversion? What happens if the regulator latches up and draws excessive current — does the upstream protection clear it, or does it take down the entire bus? By making the failure modes concrete, the engineer can better evaluate whether the calibration routine and ADC tolerance actually cover the real failure envelope.

Second, I'd acknowledge what the engineer got right. The load is indeed small, and the risk may be lower than for a high-current digital rail. That's a valid point. But low probability isn't zero probability, and for a critical analog rail, the consequence of failure could be loss of the entire mission function. I'd ask the engineer to help me understand what testing or analysis would give us confidence — perhaps we can find a similar part with radiation data, or run a limited test, or add a simple protection circuit that bounds the risk.

Third, I'd use the design review process itself as a tool. I'd suggest we formally document the risk, the mitigation options, and the decision rationale. This isn't about bureaucratic process — it's about ensuring that if we accept the risk, we do so deliberately and with full understanding. I'd also invite the engineer to present their case to the broader team, which often helps surface considerations that either of us might have missed.

Finally, I'd keep the relationship constructive by separating the technical disagreement from the person. I'd make clear that I value the engineer's creativity and willingness to challenge assumptions — those are good traits. The goal is to reach the best technical decision, not to win an argument. If we still disagree after a thorough analysis, I'd escalate to the project's chief engineer or systems lead with both perspectives clearly documented, and I'd support the engineer in presenting their view fairly.

**Possible follow-ups:** What if the schedule pressure is significant and the engineer's approach would save two weeks? How would you balance risk acceptance against program constraints?