# space-rad-hard — Day 27

## Q1: How would you approach designing a fault-tolerant analog output stage for a space-deployed system where a single-event transient (SET) on a DAC's reference voltage could cause a momentary but dangerous output spike to an actuator?

**Answer:** I'd approach this by first defining the hazard: what magnitude and duration of output spike constitutes "dangerous" for the specific actuator, and what the worst-case SET amplitude and recovery time might be for the chosen DAC and reference. That gives me the design targets.

At the circuit level, I'd consider several layers of mitigation. First, on the reference itself — use a reference with known SET response, add a low-pass filter with a time constant matched to the actuator's response (so a transient that's shorter than the filter time constant gets attenuated), and consider a small shunt capacitor directly at the DAC's reference input. Second, on the output path — add a series resistor and/or a clamp circuit (e.g., a precision clamp or back-to-back Zener) that limits the maximum voltage the actuator can see regardless of what the DAC does. Third, in firmware — implement a rate limiter or slew-rate control on the DAC output, and add a plausibility check: if the commanded value changes faster than the physical system could possibly respond, treat it as a fault and hold the last valid value or ramp to a safe state.

I'd also add a hardware-based safety interlock independent of the DAC path — for example, a window comparator on the output voltage that can disable the actuator driver or assert a shutdown signal if the output exceeds a safe range for more than a few microseconds. This gives a deterministic, hardware-only backstop that doesn't depend on firmware executing correctly.

Finally, I'd verify the design with fault injection: simulate SETs of varying amplitude and duration at the reference node, and confirm the output stays within the safe envelope. If the actuator has a mechanical time constant, I'd also check that the energy delivered during a transient is below what could cause damage.

**Possible follow-ups:** How would you choose between a hardware clamp versus a firmware rate limiter as the primary protection? What if the actuator requires a fast response that conflicts with the filtering you'd like to add?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA and a COTS precision voltage reference for an ADC. The reference's datasheet specifies initial accuracy of ±0.1% and temperature drift of ±20 ppm/°C, but has no radiation data. The designer argues that because the reference is "precision" and the system has a calibration routine, radiation-induced drift can be calibrated out. How would you evaluate this approach?

**Answer:** I'd push back on the assumption that calibration can fully compensate for radiation-induced drift, because calibration is a point-in-time correction. If the reference drifts monotonically with TID, a single calibration at the start of the mission won't help — you'd need periodic recalibration, and you'd still have error between calibration points. If the drift is non-monotonic or has sudden steps (which can happen with certain reference architectures under irradiation), calibration becomes even less effective.

The bigger issue is that "no radiation data" means we don't know the failure mode. The reference could experience:
- Gradual TID-induced drift (potentially correctable with periodic calibration)
- Enhanced low-dose-rate sensitivity (ELDRS), where the drift is worse at the actual space dose rate than at typical test rates
- Single-event transients (SETs) on the output, which are momentary and cannot be calibrated out at all
- Single-event latch-up (SEL), which could be destructive

I'd also question whether the system's calibration routine can even detect a drifted reference. If the calibration uses the same reference as the measurement path, it's a ratiometric calibration that won't correct reference error. If it uses an external standard, how is that standard verified over the mission?

My recommendation would be: (1) characterize the reference with at least a TID test and a heavy-ion SEE test — even a limited test with a few devices gives you data on the failure modes; (2) if testing isn't feasible, select a reference with existing radiation data or use a rad-hard part; (3) design the system to tolerate SETs on the reference (e.g., filtering, redundant measurements, plausibility checks); and (4) if the reference is used for critical measurements, consider a dual-reference architecture with cross-checking.

**Possible follow-ups:** What if the budget only allows testing three devices at a single dose rate? How would you design the calibration routine to detect reference drift during the mission?

---

## Q3: How would you approach designing a fault-tolerant boot sequence for a space-deployed system that uses an SRAM-based FPGA with external configuration memory (flash), where both the FPGA configuration bitstream and the flash memory are susceptible to single-event upsets?

**Answer:** I'd design the boot sequence with multiple layers of protection, because a single corrupted bit in the configuration bitstream can cause anything from a minor functional error to a complete failure to configure.

First, the flash memory itself: I'd store the bitstream with error detection and correction coding — at minimum CRC-32 for detection, ideally with a SEC-DED ECC scheme or a redundant copy of the bitstream. I'd also consider using a radiation-tolerant flash if available, or at least one with known SEE characteristics.

Second, the boot controller: rather than having the FPGA self-configure from flash (which is common in commercial designs), I'd use a separate controller — either a rad-hard microcontroller or a CPLD — that reads the bitstream from flash, verifies the CRC, and then configures the FPGA. This controller can also implement a retry strategy: if configuration fails, it re-reads the bitstream, re-verifies, and retries. After a configurable number of failures, it can fall back to a golden (known-good) copy of the bitstream stored in a different memory region or a different device.

Third, the FPGA configuration itself: I'd use the FPGA's built-in configuration error detection if available (e.g., CRC checking during configuration), and I'd implement readback verification after configuration completes — read back the configuration frames and compare against the expected bitstream. This catches bit flips that occurred during the configuration process itself.

Fourth, during operation: configuration memory in an SRAM-based FPGA can still upset after boot. I'd implement periodic scrubbing — reading back the configuration and correcting any errors — either using the FPGA's internal scrub logic or an external controller. The scrub rate should be fast enough to prevent accumulation of multiple errors in the same logic block.

Finally, I'd design the boot sequence to be observable: telemetry that reports which copy of the bitstream was used, how many retries occurred, and the results of readback verification. This gives ground operators visibility into the health of the configuration chain.

**Possible follow-ups:** How would you handle the case where the golden copy in flash is also corrupted? What if the boot controller itself is susceptible to SEFIs during the boot process?

---

## Q4: Imagine you are leading a design review for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS microcontroller for housekeeping. The microcontroller has a built-in watchdog timer that the firmware enables during initialization. The designer argues that the internal watchdog is sufficient and no external watchdog is needed. How would you handle this disagreement?

**Answer:** I'd start by acknowledging what the internal watchdog does well: it's simple, requires no additional components, and can detect a firmware hang where the main loop stops executing. But I'd then walk through the failure modes that an internal watchdog may not cover.

The key concern is that the watchdog and the processor share the same silicon. A single-event functional interrupt (SEFI) that affects the processor core may also affect the watchdog peripheral — for example, the SEFI could corrupt the watchdog's configuration registers, disable it, or cause it to be periodically refreshed by a stuck interrupt handler even though the main application is hung. In a radiation environment, you can't assume that the watchdog is more reliable than the processor it's watching, because they're the same die.

There's also the question of what "watching" means. An internal watchdog typically only detects a failure to refresh — it doesn't detect a processor that's executing but producing wrong results. An external watchdog can be designed to monitor not just a heartbeat but also the plausibility of the system's behavior (e.g., a separate supervisor that checks that the housekeeping microcontroller is communicating with the FPGA at the expected rate).

My recommendation would be to use both: an internal watchdog as a first line of defense (it's free and catches most hangs), plus an external watchdog with a longer timeout as a backstop. The external watchdog should be a simple, radiation-tolerant part — a timer IC or a discrete RC-based circuit — that is independent of the processor. It should also have a manual reset capability so that ground commands can force a system reset even if both watchdogs are compromised.

I'd also raise the question of what happens after a watchdog reset: does the system return to a known-good state, or does it re-boot into the same corrupted condition? The reset should trigger a full re-initialization, not just a restart of the application.

**Possible follow-ups:** How would you choose the timeout values for the internal versus external watchdog? What if the external watchdog adds unacceptable board space or power consumption?

---

## Q5: How would you approach designing a test plan to verify that a space-deployed system can recover from a single-event functional interrupt (SEFI) that causes the main microcontroller to stop executing code, when you cannot inject actual radiation events during ground testing?

**Answer:** Since we can't create real radiation events in most ground test environments, the goal is to simulate the observable effects of a SEFI and verify that the recovery mechanisms work as designed. I'd structure the test plan around fault injection at multiple levels.

At the hardware level, I'd inject faults directly into the reset and watchdog circuitry:
- Force the watchdog timeout by stopping the firmware from refreshing it (e.g., via a debugger breakpoint or a test mode that disables the refresh)
- Assert an external reset manually to simulate a watchdog-triggered reset
- Use a fault injection switch or relay to momentarily interrupt the power supply, simulating a power-cycle recovery
- If the system has a hardware test port, use it to force the processor into a stuck state (e.g., hold the clock, assert a bus error)

At the firmware level, I'd add test hooks that can simulate SEFI-like conditions:
- A test command that causes the firmware to enter an infinite loop without refreshing the watchdog
- A test command that corrupts a critical data structure (e.g., the stack pointer, a configuration register) to verify that error detection and recovery mechanisms catch it
- A test mode that disables interrupts and verifies the watchdog still fires

At the system level, I'd verify the full recovery sequence:
- After a simulated SEFI, does the watchdog reset the processor?
- Does the processor re-initialize correctly, including all peripherals and communication interfaces?
- Does the system return to its pre-fault state (e.g., resume telemetry, re-establish communication with the ground station)?
- Is the fault logged for post-event analysis?

I'd also test the "hang with heartbeat" scenario — where the processor continues toggling a GPIO but is no longer executing the main application. This requires a more sophisticated watchdog that monitors not just the heartbeat but also the content or timing of the heartbeat (e.g., a windowed watchdog that requires the refresh to occur within a specific time window, or a watchdog that monitors a secondary signal that only the main loop toggles).

Finally, I'd document the expected recovery time for each fault scenario and verify that it meets the system requirements. The test plan should also include repeated testing (e.g., 100+ iterations) to build confidence that recovery is reliable, not just a one-time success.

**Possible follow-ups:** How would you verify that the system recovers to a known-good state rather than a degraded state? What if the SEFI corrupts the processor's configuration registers in a way that prevents the watchdog from being re-enabled after reset?