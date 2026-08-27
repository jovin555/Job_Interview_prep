# space-rad-hard — Day 37

## Q1: How would you approach designing a fault-tolerant analog multiplexing scheme for a space-deployed system where a single-event transient (SET) on the mux select lines could route the wrong sensor channel to a precision ADC, potentially causing an incorrect control action?

**Answer:** This is a classic case where a single-event effect in digital control logic propagates into the analog domain and can cause a system-level safety issue. The first step is to recognize that the mux select lines are safety-critical, so I would treat them with the same rigor as any critical digital signal.

My approach would be multi-layered. First, at the digital level, I would encode the channel select using a scheme with Hamming distance — for example, using a Gray code or a custom encoding where adjacent channels differ by more than one bit, so a single-bit upset cannot silently switch to an adjacent channel. Better yet, I would use a redundant encoding with parity or a small CRC, and have the firmware validate the select code before accepting the conversion result. If the select code fails validation, the firmware should discard the sample and flag an error rather than acting on potentially misrouted data.

Second, at the analog level, I would consider adding a sample-and-hold or a settling-time delay after switching channels, and critically, I would verify the mux output against an expected voltage range. If the system knows what the selected sensor should roughly read (e.g., a pressure sensor in a known physiological range), a simple window comparator or firmware range check can catch grossly wrong channel selections.

Third, I would think about the control action side. The control loop should have rate limiting and plausibility checks on the actuator command, so even if a spurious reading gets through, the control system cannot respond with a dangerous step change. This is defense in depth — the mux error is caught at multiple layers rather than relying on any single mitigation.

Finally, I would consider the physical implementation: adding series resistors on the select lines to limit single-event transient current injection, and ensuring the mux's power supply is well-decoupled so a transient on the select input doesn't couple into the analog supply.

**Possible follow-ups:** How would you handle the trade-off between adding validation logic and increasing conversion latency in a time-critical control loop? What if the mux itself is a rad-hard part but the select line driver is a COTS FPGA?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA and a COTS operational amplifier for a critical analog signal conditioning path. The op-amp has no radiation data, but the designer argues that "it's a simple, mature part with a well-understood topology, and the system has a calibration routine." How would you evaluate this approach?

**Answer:** I would push back on this argument, but not dismiss it outright. The designer is right that the op-amp topology is well understood and that calibration can handle some drift, but the key question is whether the failure modes are bounded and detectable. A "mature part" with no radiation data is still an unknown quantity in the space environment.

The first thing I would do is assess what the op-amp is doing in the signal chain. If it's a unity-gain buffer for a low-impedance sensor, the risk profile is different than if it's a high-gain amplifier for a microvolt-level signal. I would ask: what happens if the op-amp's input offset voltage drifts by 10 mV due to TID? What if a single-event transient causes a momentary output glitch? Can the calibration routine detect and correct for these, or does it only handle static offset and gain errors?

I would also look at the specific radiation concerns. Bipolar op-amps are susceptible to ELDRS (enhanced low-dose-rate sensitivity), which means ground testing at high dose rate can significantly underestimate TID degradation. JFET-input op-amps can exhibit input bias current shifts. Even if the part is "simple," these are real, known failure mechanisms.

My recommendation would be to either select a radiation-characterized op-amp, or if the COTS part is truly necessary, to characterize it with a focused radiation test — even a limited TID test at a relevant dose rate would give useful data. I would also add design-level mitigations: a calibration routine that runs periodically and can detect out-of-range parameters, a window comparator on the output, and a fail-safe path in the system that doesn't rely on the op-amp's output being correct at all times.

The broader principle is that "mature" and "well-understood" are not substitutes for radiation data. The space environment introduces failure modes that terrestrial experience simply doesn't cover.

**Possible follow-ups:** How would you prioritize which COTS parts to radiation-test when budget is limited? What specific op-amp parameters would you want to characterize in a TID test?

---

## Q3: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental requirement here is that a failed update must never brick the system. This drives the architecture from the start.

My approach would be a multi-slot boot scheme with a robust bootloader. The bootloader itself lives in protected memory — ideally a separate, radiation-hardened flash or a region that is write-protected after initial programming. The bootloader's job is to validate and load application images, not to be updated itself (or if it must be updated, only via a very controlled, authenticated process).

For the application, I would use at least two image slots: a known-good "golden" image and a candidate update slot. The bootloader validates the candidate image using a CRC or hash before ever executing it. If validation fails, it falls back to the golden image. If the candidate passes validation but fails at runtime — for example, the system resets within a certain time window — a watchdog or a boot counter in non-volatile memory triggers a rollback to the golden image.

For the update process itself, I would design it as a state machine with explicit checkpoints. The update is downloaded to a staging area, validated, then written to the inactive slot. Only after the new image is fully written and verified is the boot flag flipped. If any step fails, the system stays on the current image.

For radiation-induced corruption of the flash itself, I would add periodic scrubbing of the inactive image slots — reading them back and correcting any single-bit errors if the flash supports ECC, or rewriting the image if errors accumulate. The active image should also be periodically validated against its stored checksum, though this has to be balanced against the risk of interrupting execution.

Finally, I would consider a remote recovery path: a minimal, radiation-hardened recovery routine that can accept a new image over a slow but reliable link, even if the main application is completely corrupted. This is the last line of defense.

**Possible follow-ups:** How would you handle the trade-off between validating the active image frequently versus the overhead of reading back large flash regions? What if the golden image itself becomes corrupted over a long mission?

---

## Q4: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." How would you handle this disagreement?

**Answer:** I would handle this by acknowledging the engineer's point about the low power level, but then reframing the discussion around what "minimal risk" actually means in this context. The load current and voltage don't change the fundamental issue: we have no data on how this part behaves under TID, under single-event effects, or under the thermal and vacuum conditions of the mission.

I would walk through the specific failure modes. A linear regulator in a radiation environment can experience output voltage drift due to TID, which directly affects the accuracy of the analog rail. It can also experience single-event transients on the output — a momentary voltage spike or dip that could corrupt a critical measurement. Even at 50 mA, a single-event latch-up in the regulator could cause a localized overcurrent condition that might not trip the main bus protection but could still damage the part or degrade its performance.

I would also point out that "critical analog rail" means the consequences of failure are high, regardless of the power level. The question isn't "how much power is at risk?" but "what happens if this rail misbehaves?" If the rail feeds a sensor signal chain that drives a control decision, a transient could cause an incorrect action.

My recommendation would be to either select a radiation-characterized regulator — there are many available even for low-current rails — or, if the COTS part is truly necessary, to add mitigation: a post-regulator filter to attenuate transients, a voltage supervisor to detect out-of-range output, and a fail-safe in the system that doesn't rely on this rail being perfect. I would also suggest a focused radiation test if the part is otherwise ideal.

The key teaching point for the junior engineer is that radiation tolerance is not about the nominal operating point — it's about the failure modes that radiation introduces, and those don't scale with power level.

**Possible follow-ups:** How would you help the junior engineer understand the difference between "the part will probably work" and "we have evidence the part will work"? What specific radiation test would you propose for this regulator?

---

## Q5: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** Clock distribution is one of those areas where a single failure can corrupt the entire system's timing, so I would design for redundancy and monitoring from the start.

My approach would start with the clock source. I would use at least two independent oscillators — ideally with different technologies (e.g., a crystal oscillator and a MEMS oscillator) so they don't share common failure modes. Each FPGA or ADC would have the ability to select between clock sources, either automatically via a clock monitor or under command from a central controller.

For the distribution network itself, I would use a fan-out buffer with redundant inputs. The buffer should have a clock monitor that detects loss-of-clock or frequency drift and automatically switches to the backup source. The switchover needs to be glitch-free or at least controlled, so downstream devices don't see a runt pulse or a phase jump that could corrupt their state.

For synchronized sampling across multiple ADCs, I would think carefully about the synchronization mechanism. A shared clock alone doesn't guarantee sample alignment if the ADCs have different PLL lock times or if the clock path delays differ. I would use a synchronization pulse (e.g., a SYNC signal) that is distributed with matched propagation delays, and I would design the ADCs to align their sampling edges to that pulse. The SYNC distribution should also be redundant, with a voting scheme at each ADC if possible.

I would also add monitoring and health reporting. Each FPGA should be able to detect clock anomalies — missing edges, frequency drift, excessive jitter — and report them to a central health monitor. This gives early warning of a degrading clock source before it causes a full failure.

Finally, I would consider the radiation effects on the clock components themselves. Oscillators can experience frequency shifts due to TID, and PLLs can experience single-event transients that cause phase hits. I would select radiation-characterized components where possible, and for COTS parts, I would derate and add monitoring to detect the expected failure modes.

The key principle is that the clock network is a single point of failure for the entire system, so it deserves the same redundancy and monitoring as any critical power rail.

**Possible follow-ups:** How would you handle the phase alignment between the redundant clock sources during switchover? What if the system requires sample synchronization across multiple boards connected by a backplane?