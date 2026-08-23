# space-rad-hard — Day 33

## Q1: How would you approach designing a fault-tolerant analog multiplexing scheme for a space-deployed system where a single-event transient (SET) on the mux select lines could route the wrong sensor channel to a precision ADC, potentially causing an incorrect control action?

**Answer:** This is a classic case where a single-event effect in digital control logic propagates into the analog domain and can cause a system-level failure. My approach would start with a risk assessment: what is the consequence of reading the wrong channel? If it's just a bad telemetry point, filtering may be sufficient. If it could trigger an incorrect control action — say, a motor command based on a false pressure reading — then we need active mitigation.

The first line of defense is at the architecture level. I would consider whether the mux selection can be made redundant or self-checking. Options include: (1) using two muxes in parallel with their outputs averaged or compared before conversion, (2) encoding the channel select with a simple error-detecting code (e.g., a Hamming code or even just a parity bit) and having the firmware validate the selection before accepting the reading, or (3) reading a known reference channel periodically to verify the mux is actually routing the intended input.

In firmware, I would implement a "select, settle, verify, convert" sequence: after setting the mux address, the firmware reads back the address lines (if accessible) or performs a conversion on a known calibration voltage to confirm the correct channel is selected before trusting the measurement. I would also add plausibility checks on the converted value — if a pressure reading suddenly jumps to a value that's physically impossible given the last several samples, treat it as suspect rather than acting on it immediately.

At the board level, I would consider adding filtering on the mux select lines (RC filters to slow edges and reduce SET susceptibility) and ensuring the mux's analog supply is well-decoupled so a transient on the select logic doesn't couple into the signal path. If the application allows, using a mux with built-in break-before-make and overvoltage protection also helps prevent a transient from damaging the ADC input.

The key principle is defense in depth: don't rely on any single mitigation. The analog path should be designed so that even if a wrong channel is selected, the system can detect and reject the bad reading before it drives an actuator.

**Possible follow-ups:** How would you verify that your plausibility checks are robust enough to catch a transient-induced error without rejecting legitimate fast-changing signals? What if the mux itself is radiation-hardened but the select logic is in an FPGA — where would you place the boundary of responsibility?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA and a COTS operational amplifier for a critical analog signal conditioning path. The op-amp has no radiation data, but the designer argues that "it's a simple, mature part with a well-understood topology, and the system has a calibration routine." How would you evaluate this approach?

**Answer:** I would push back on the assumption that "simple and mature" equates to "radiation-tolerant." Op-amps are particularly sensitive to total ionizing dose effects — specifically, input bias current and offset voltage drift, which can be significant even at moderate dose levels. A calibration routine performed at the start of life cannot correct for radiation-induced drift that accumulates over the mission, because the drift is often non-linear and may not be predictable from ground testing alone.

My evaluation would start with a quantitative analysis: what is the allowable drift in the signal chain before the measurement becomes unacceptable? If the op-amp's offset voltage spec is, say, ±1 mV, and the system can tolerate ±5 mV of total error, then a radiation-induced drift of even 2-3 mV could push the system out of spec. Without radiation data, we're essentially gambling on the part's behavior.

I would then look at alternatives: (1) is there a radiation-characterized op-amp available, even if it's older or has slightly worse specs? (2) Can the circuit topology be changed to reduce sensitivity to op-amp parameters — for example, using a chopper-stabilized architecture that's less sensitive to offset drift, or using a higher-gain first stage with the op-amp in a configuration where its offset is less critical? (3) Can the calibration routine be extended to run periodically during the mission, using a known reference voltage to re-zero the offset?

If we must use the COTS part, I would require a radiation test — even a limited one — to characterize the part's behavior. A simple TID test on a few samples would give us data on offset drift and bias current change, which we could then use to bound the error budget. I would also add margin in the design: if the system needs ±5 mV, design for ±2 mV at beginning of life so there's room for drift.

The broader lesson is that "calibration" is not a cure-all for radiation effects. It can correct for systematic, predictable drift, but it cannot correct for transient effects, and it cannot correct for drift that occurs between calibration intervals. The design must be robust to the worst-case radiation-induced error, not just the nominal case.

**Possible follow-ups:** How would you design a periodic in-flight calibration routine for an analog signal chain? What parameters would you monitor to detect that the op-amp is degrading beyond acceptable limits?

---

## Q3: How would you approach designing a fault-tolerant power distribution architecture for a satellite payload that must survive a single-event latch-up (SEL) on any single load without losing the entire system, when the payload has multiple loads with different current requirements and criticality levels?

**Answer:** The fundamental principle is to partition the power distribution so that a fault on any single load is contained and doesn't propagate to other loads or the main bus. I would start by classifying loads by criticality and current draw, then design the distribution hierarchy accordingly.

For each load or group of loads, I would include a dedicated latch-up protection circuit: a current-limiting switch or an electronic circuit breaker that can detect the characteristic signature of a latch-up — a sudden, sustained increase in current — and shut down that branch within microseconds. The key parameters are the trip threshold (set above the normal operating current but below the latch-up current) and the response time (fast enough to prevent damage to the load or the bus).

The protection circuit itself must be radiation-tolerant, since it's the very component that's supposed to protect against radiation-induced events. I would use a design that's inherently robust: a series FET with a current-sense resistor and a comparator, with the trip point set by a resistor divider. The circuit should latch off when tripped, requiring a command from the system controller to re-enable, rather than automatically retrying — this prevents a persistent latch-up from causing repeated power cycling.

For critical loads, I would consider redundant power paths: two independent switches feeding the same load, so that if one path latches off, the other can still supply power. This requires the load to be designed to handle power from either path, or a diode-OR arrangement at the load.

I would also add bus-level protection: a main bus limiter that protects the spacecraft power bus from a fault in the payload's internal distribution. This is the last line of defense — if a branch protection circuit fails, the bus limiter prevents the fault from affecting other payloads on the same bus.

Finally, I would design the system to detect and report latch-up events: a telemetry channel that records which branch tripped, when, and how many times. This information is critical for diagnosing the health of the payload and for deciding whether to re-enable a tripped branch.

The trade-off is between protection granularity and complexity. More branches mean better fault isolation but more components, more mass, and more potential failure points. The right answer depends on the criticality of each load and the overall mission risk tolerance.

**Possible follow-ups:** How would you set the current trip threshold for a load that has a high inrush current during startup? How would you handle a load that experiences legitimate current spikes during normal operation?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS DC-DC converter for the 3.3V rail. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, and the FPGA's absolute maximum rating is 3.6V. A junior engineer argues that the 130 mV margin is acceptable because "the FPGA will never actually see 3.47V in practice — the converter will typically output 3.3V, and the FPGA's absolute maximum rating already includes some safety margin." How would you handle this disagreement?

**Answer:** I would acknowledge that the engineer has a point about typical behavior, but I would reframe the discussion around worst-case analysis and design margin philosophy. In space systems, we design for worst-case conditions, not typical ones, because the cost of a failure is extremely high and the environment is unforgiving.

The key issue is that "absolute maximum rating" is not a specification for normal operation — it's the limit beyond which damage may occur. Operating near that limit, even briefly, is a violation of good design practice. The industry standard is to derate: to keep operating conditions well below absolute maximum ratings, typically by 20% or more. For a 3.6V absolute maximum, a 20% derating would suggest a maximum operating voltage of around 2.88V, which is clearly not practical for a 3.3V rail — so the real question is what derating factor is appropriate for this specific application.

I would also challenge the assumption that the converter will "typically" output 3.3V. The datasheet's worst-case spec of 3.47V exists for a reason: it accounts for line and load variations, temperature effects, component tolerances, and aging. In a space environment, temperature extremes can be severe, and the converter's output voltage can shift over mission life. The 3.47V spec is the designer's guarantee of the maximum voltage the converter will produce under any combination of specified conditions — we should assume it can happen.

My recommendation would be to add margin in one of two ways: (1) select a converter with a tighter output voltage specification, or (2) add a post-regulation stage — for example, a low-dropout regulator that takes the converter's output and produces a clean, well-regulated 3.3V with much tighter tolerance. The LDO adds some power loss, but for a digital rail, the efficiency hit may be acceptable.

If neither option is feasible, I would require a detailed analysis showing that the FPGA's absolute maximum rating has sufficient margin for the specific conditions of this mission, including radiation-induced voltage transients on the 3.3V rail. I would also ask for a test plan to verify the rail voltage under worst-case conditions — thermal extremes, load transients, and input voltage variations.

The broader point is that design reviews are not about winning arguments — they're about ensuring the design meets its requirements with adequate margin. I would encourage the engineer to think in terms of "what could go wrong" rather than "what will probably happen."

**Possible follow-ups:** What if the only available converter with the required radiation tolerance has this exact output voltage specification — how would you mitigate the risk? How would you verify the actual output voltage under worst-case conditions during ground testing?

---

## Q5: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental requirement is that a firmware update must never leave the system in a state where it cannot boot or cannot accept another update. This drives the architecture toward redundancy and atomicity.

The first decision is the boot architecture. I would use a two-stage approach: a small, immutable bootloader in protected memory (ideally in radiation-hardened ROM or a one-time-programmable region) that is never updated, and an application image in flash that can be updated. The bootloader's job is to validate the application image before executing it — checking a CRC or cryptographic signature — and to provide a fallback path if validation fails.

For the application image itself, I would use a dual-bank or A/B partition scheme: two copies of the firmware in separate flash regions. The bootloader always boots from the "known good" bank, and updates are written to the inactive bank. Only after the new image is fully written and validated is the active bank switched. If the new image fails to boot or fails validation, the bootloader reverts to the previous bank.

This approach requires enough flash for two images, which may not always be available. In that case, I would use a compressed image with a small recovery kernel: the bootloader can load a minimal recovery image that supports communication with the ground station and can receive a new application image. The recovery image itself must be protected — either in the same protected memory as the bootloader or in a separate flash region that is write-protected during normal operation.

For the update process itself, I would design it as a state machine with explicit validation at each step: (1) receive the new image in chunks, with each chunk CRC-checked; (2) write each chunk to the inactive bank; (3) after the full image is written, verify the complete image CRC; (4) set a "commit" flag that tells the bootloader to try the new image; (5) reboot and run the new image; (6) after successful initialization, the new image sends a "success" message to the ground station, which then confirms the commit. If no confirmation is received within a timeout, the bootloader reverts to the previous bank.

I would also consider the effect of radiation on the update process itself. A single-event upset during the update could corrupt the new image or the commit flag. The CRC checks catch corruption in the image, but the commit flag itself should be protected — for example, by storing it in multiple locations with a voting scheme, or by using a write-once mechanism.

Finally, I would design the update protocol to be resumable: if communication is lost mid-update, the system should be able to resume from the last received chunk rather than starting over. This reduces the exposure window and makes the update more robust in a noisy or intermittent communication environment.

**Possible follow-ups:** How would you handle the case where the bootloader itself is corrupted? What if the system has only enough flash for a single image — how would you ensure recoverability? How would you test the update process to verify it works under fault conditions?