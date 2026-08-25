# space-rad-hard — Day 35

## Q1: How would you approach designing a fault-tolerant analog multiplexing scheme for a space-deployed system where a single-event transient (SET) on the mux select lines could route the wrong sensor channel to a precision ADC, potentially causing an incorrect control action?

**Answer:** The core problem is that a single-event upset in the mux control logic can silently present the wrong sensor as valid data, and if that data feeds a control loop, the system could act on a false reading. I'd approach this in layers.

First, at the architecture level, I'd question whether a single shared mux is the right topology for the most critical channels. If there are two or three channels that drive safety-critical decisions, I'd consider dedicating separate ADC inputs to those and only multiplexing the non-critical or lower-rate channels. That eliminates the failure mode entirely for the channels that matter most.

Where multiplexing is unavoidable, I'd add validation at multiple levels. The firmware should know which channel it commanded and should verify the mux actually switched to that channel. One technique is to include a known reference voltage or a fixed identification resistor on each channel — after switching, the firmware reads the channel and checks that the value is plausible for that specific sensor before accepting it. This catches both mux select-line upsets and stuck switches.

I'd also consider encoding the select lines with a scheme that has built-in error detection, such as using a Gray code or adding a parity bit, so that a single-bit upset in the select logic produces an invalid code that the firmware can detect and reject rather than silently routing to the wrong channel. If the mux has an "enable" pin, I'd hold it disabled until the select lines are stable, then enable, wait for settling, and take the reading.

At the circuit level, I'd add filtering on the mux output — a simple RC low-pass filter with a time constant matched to the sensor bandwidth — to attenuate single-event transients that occur during the sampling window. I'd also consider taking multiple samples per channel and applying median or majority filtering in firmware, rejecting readings that deviate significantly from the previous valid value for that channel.

Finally, I'd implement a plausibility check in the control loop itself: rate-of-change limits, valid range checks, and cross-validation against redundant sensors where available. If a reading fails these checks, the system should default to a safe state rather than acting on the suspect value.

**Possible follow-ups:** How would you distinguish between a mux select-line upset and a transient on the analog signal path itself during debugging? What if adding a reference voltage to each channel is impractical due to pin count or board space?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA and a COTS operational amplifier for a critical analog signal conditioning path. The op-amp has no radiation data, but the designer argues that "it's a simple, mature part with a well-understood topology, and the system has a calibration routine." How would you evaluate this approach?

**Answer:** I'd acknowledge that the designer has a point about the topology being well-understood, but I'd push back on the assumption that "mature" and "well-understood" translate to radiation tolerance. The failure modes we care about in space — parametric drift from total ionizing dose, single-event transients on the output, and in some cases enhanced low-dose-rate sensitivity — are not captured by the part's commercial datasheet or its reputation in terrestrial applications.

The first question I'd ask is: what is this op-amp actually doing in the signal chain, and what is the consequence of its failure? If it's in a non-critical housekeeping path where a transient or drift causes a nuisance alarm, the risk might be acceptable with mitigation. If it's conditioning a signal that drives a control decision, the risk calculus changes significantly.

For the calibration argument specifically, I'd note that calibration can correct for static offset and gain errors, including slow drift from TID, but it cannot correct for single-event transients — a momentary spike or dip on the output that occurs between calibration cycles. The calibration routine also assumes the system can detect when drift has occurred and has a reference to calibrate against, which may not be true for all parameters.

If we must use this COTS part, I'd want to understand the specific failure modes and design mitigations around them. For TID drift, I'd look at the op-amp's internal topology — bipolar inputs are more susceptible to input bias current degradation, while CMOS inputs are more susceptible to offset voltage shifts. I'd derate the operating conditions, particularly supply voltage and input common-mode range, to give more margin. For single-event transients, I'd add output filtering with a bandwidth matched to the signal, and I'd implement plausibility checking in firmware — if the output jumps faster than the physical signal can change, reject it.

I'd also recommend a targeted radiation test if budget allows — even a limited TID test on a few samples can reveal whether the part degrades gracefully or fails catastrophically. If testing isn't possible, I'd look for a similar part that does have radiation data, or I'd consider whether a discrete or hybrid solution could meet the requirements with known parts.

The key principle is that the risk assessment should be based on the part's actual failure modes in the radiation environment, not on its terrestrial reliability. If we can't characterize the part, we need to design as if it will fail, and ensure the system can tolerate that failure.

**Possible follow-ups:** What specific op-amp parameters would you prioritize for radiation testing if you had a limited budget? How would you determine whether the calibration routine can actually compensate for TID-induced drift in this circuit?

---

## Q3: How would you approach designing a radiation-tolerant firmware update strategy for a space-deployed system where the application firmware resides in flash memory that is susceptible to single-event upsets, and a corrupted update could render the system unrecoverable?

**Answer:** The fundamental requirement is that a failed or corrupted update must never leave the system in a state where it cannot boot and run at least a minimal recovery capability. I'd design the update strategy around three principles: redundancy, validation, and atomicity.

For redundancy, I'd use a dual-bank or A/B partition scheme in flash. The system boots from the active bank, and updates are written to the inactive bank. Only after the new image passes validation does the system switch the boot pointer to the new bank. If the update fails at any point, the system continues to boot from the original bank. This requires enough flash capacity for two full images, which is a trade-off against cost and board space, but for a space system it's usually worth it.

For validation, I'd require multiple layers of checks before accepting an update. A cryptographic signature verifies the image came from an authorized source and wasn't corrupted in transit. A checksum or hash verifies the image was written correctly to flash. And a boot-time self-test verifies the image is actually executable — this could include a CRC check of the entire image, a test of critical peripherals, and a "bootstrap" sequence where the new firmware must report successful initialization within a timeout window before the bootloader commits to it.

For atomicity, the update process should be designed so that a power loss or reset at any point leaves the system in a known state. Writing to the inactive bank is inherently atomic in the sense that the active bank is untouched, but I'd also add a "commit" flag that is written only after the new image is fully validated. The bootloader checks this flag: if it's not set, the system boots the old image. If it is set, the system boots the new image and, after successful initialization, clears the flag.

I'd also consider the radiation susceptibility of the flash itself. If the flash can experience upsets that corrupt the stored image over time, I'd add periodic scrubbing — reading the image and correcting any single-bit errors using ECC if the flash supports it, or rewriting from a redundant copy. The bootloader itself should also be protected, either by residing in a radiation-hardened boot ROM or by having a redundant copy that the bootloader can fall back to.

Finally, I'd design the update protocol to be resumable. If the uplink is interrupted mid-transfer, the system should be able to resume from the last complete block rather than restarting from scratch, and it should be able to abort cleanly and revert to the current image.

**Possible follow-ups:** How would you handle the case where the new firmware passes validation but fails during operation — how do you roll back? What if the flash memory itself is corrupted by a single-event upset during the update process?

---

## Q4: How would you approach designing a fault-tolerant clock distribution network for a space-deployed system that uses multiple FPGAs and ADCs requiring synchronized sampling?

**Answer:** The design goal is to ensure that all devices sample on the same clock edge, and that a single-event upset or component failure cannot cause loss of synchronization across the system. I'd approach this at three levels: the clock source, the distribution topology, and the synchronization protocol.

At the source, I'd use a radiation-tolerant oscillator or crystal oscillator with known phase noise and frequency stability over temperature and TID. If the system can tolerate it, I'd consider a redundant clock source with automatic switchover — two oscillators feeding a clock mux or a PLL that can lock to either source. The switchover must be glitch-free, which is challenging, so I'd design the detection and switching logic carefully to avoid generating runt pulses or metastable states.

For distribution, I'd use a dedicated clock buffer or fan-out tree rather than routing the clock through the FPGA fabric, which introduces variable delay and single-point-of-failure risk. Each clock line should be properly terminated and impedance-matched to avoid reflections and ringing. I'd also consider using differential signaling (LVDS or LVPECL) for the clock distribution to improve noise immunity and reduce the chance of a single-event transient being captured as a false clock edge.

The synchronization protocol is where the real fault tolerance comes in. Even with a clean clock distribution, a single-event upset in one FPGA's PLL or clock divider could cause that device to drift out of phase. I'd implement a periodic synchronization mechanism — for example, a sync pulse generated by a master device and distributed to all slaves, with each slave using the sync pulse to realign its sampling clock. The sync pulse itself should be validated (e.g., expected period, pulse width) before being accepted, to avoid a transient being treated as a valid sync.

I'd also consider whether the system truly needs sample-accurate synchronization across all devices, or whether timestamping each sample with a common time base would be sufficient. Timestamping is more forgiving of clock skew and allows the system to detect and correct for drift in software, at the cost of more complex data processing.

For the ADCs specifically, I'd verify that their sampling clocks are derived from the same source and that the aperture delay is well-matched across devices. If the ADCs have an external sample clock input, I'd use that rather than relying on internal clock generation.

Finally, I'd add monitoring: each device should be able to report its clock status (locked, phase error, frequency error) to a central health monitor, so that drift or loss of lock is detected early and the system can take corrective action — either resynchronizing or switching to a redundant clock source.

**Possible follow-ups:** How would you handle the case where one FPGA's clock input is corrupted by a single-event transient — how do you detect and recover? What are the trade-offs between a centralized clock tree and a distributed clocking scheme with local PLLs?

---

## Q5: Imagine you are leading a design review for a space-deployed system where a junior engineer has proposed using a single commercial voltage regulator with no radiation data for a critical analog rail, arguing that "the rail is only 5V and the load is only 50mA, so the risk is minimal." How would you handle this disagreement?

**Answer:** I'd start by acknowledging that the engineer has correctly identified that the load is small and the voltage is modest — those are relevant factors. But I'd reframe the question: the risk isn't about the size of the rail, it's about what happens when the regulator fails, and how it fails. A 5V/50mA rail might be small, but if it powers the analog front-end that conditions a critical sensor signal, a failure there could be just as mission-threatening as a failure in a high-current digital rail.

I'd walk through the specific failure modes we care about in the space environment. Total ionizing dose can cause the regulator's output voltage to drift out of specification, its dropout voltage to increase, or its quiescent current to rise — any of which could degrade the analog performance. Single-event transients on the output could inject noise or spikes into the analog signal chain. Single-event latch-up in the regulator itself could cause a sustained overcurrent condition on the input bus, potentially affecting other loads on the same rail. None of these are captured by the commercial datasheet.

I'd also challenge the "minimal risk" framing. Without radiation data, we don't know the risk — we only know the risk is uncharacterized. The engineer is essentially asserting that the probability of failure is low without evidence. In a space system, we design for the possibility of failure, not just its probability. If the part fails, what's the consequence? If it's a graceful degradation that the system can detect and work around, maybe the risk is acceptable. If it's a hard failure that takes down the analog front-end, we need a mitigation.

I'd then ask the engineer to walk through the system-level impact of each failure mode and what mitigation could be applied. Could we add a post-regulator filter to attenuate transients? Could we add a voltage supervisor to detect drift and switch to a redundant path? Could we derate the operating conditions — lower input voltage, lower output current — to give more margin? Could we qualify the part with a limited radiation test?

If the part is truly critical and no mitigation is sufficient, I'd recommend selecting a radiation-characterized alternative, even if it costs more or has slightly worse electrical specifications. The cost of a part is small compared to the cost of a mission failure.

I'd also use this as a teaching moment about how we make design decisions in space systems: we don't rely on intuition about "minimal risk" — we rely on data, analysis, and a clear understanding of failure modes and consequences. The engineer's instinct to push back on unnecessary radiation-hardened parts is good — that's how we avoid over-engineering — but the burden of proof should be on demonstrating that the risk is acceptable, not on assuming it is.

**Possible follow-ups:** How would you help the junior engineer develop a framework for deciding when a COTS part is acceptable versus when a rad-hard part is required? What specific mitigation techniques would you consider to make this particular regulator acceptable if a rad-hard alternative is not available?