# space-rad-hard — Day 21

## Q1: How would you approach designing a fault-tolerant boot sequence for a system with multiple microcontrollers where one controller is responsible for validating and releasing the others from reset, and that controller itself is susceptible to single-event upsets?

**Answer:** The fundamental problem here is that you've created a single point of failure — the validating controller — and if it upsets, the entire system can be held in reset or boot into an invalid state. I'd approach this with a layered strategy rather than relying on any single mechanism.

First, I'd question the architecture itself. Is there a reason one controller must gate the others? If the boot sequence is truly critical, I'd consider whether each controller can validate its own firmware and boot independently, with the "validating" role being advisory rather than mandatory. This removes the single point of failure at the architectural level.

If the hierarchical boot is unavoidable, I'd design the validation controller to be as robust as possible: use a radiation-hardened part if available, implement its boot code in protected memory (e.g., flash with ECC or a rad-hard boot ROM), and add a hardware watchdog that is independent of the controller's own execution — ideally a separate rad-hard watchdog IC with a long timeout that can distinguish between "still booting" and "hung."

For the downstream controllers, I'd design their reset release to be fail-safe: if the validating controller doesn't release them within a specified window, they should have a fallback path — for example, a hardware timer that releases reset after a timeout, or the ability to boot from a redundant copy of firmware. The key principle is that a single upset in one device should not be able to permanently prevent the system from reaching a known-good state.

I'd also add a recovery mechanism: if the validating controller detects that it has been upset (e.g., through a self-test or a sanity check from another node), it should be able to reset itself and re-attempt the boot sequence, with a limited number of retries before declaring a fault.

**Possible follow-ups:** How would you handle the case where the validating controller's firmware itself is corrupted? What if the watchdog timer is also affected by radiation — how would you detect and recover from that?

---

## Q2: You are reviewing a design for a space-deployed system that uses a radiation-hardened FPGA for data processing and a COTS microcontroller for housekeeping. The microcontroller has a built-in watchdog timer that the firmware enables during initialization. The designer argues that the internal watchdog is sufficient and no external watchdog is needed. How would you evaluate this approach?

**Answer:** I'd push back on this. The internal watchdog has a fundamental weakness: it shares the same silicon, the same power supply, and the same clock domain as the processor it's supposed to monitor. A single-event functional interrupt (SEFI) that disrupts the processor core may also disrupt the watchdog circuitry, the clock generation, or the interrupt controller that the watchdog relies on. If the watchdog is implemented in firmware — for example, if the firmware must periodically re-arm it through a register write — then a firmware upset that causes the processor to execute garbage code could potentially keep the watchdog satisfied while the system is in a non-functional state.

An external watchdog provides diversity: it's a separate device with its own power supply (or at least its own supply filtering), its own clock, and its own logic. It doesn't depend on the processor's firmware or internal state. Even a simple external watchdog with a fixed timeout and a "kick" input provides a level of independence that an internal watchdog cannot match.

That said, I'd also consider the failure modes the watchdog needs to protect against. A simple timeout watchdog catches a hung processor, but it doesn't catch a processor that's executing incorrect but non-hanging code. For that, you might need a more sophisticated approach — a "windowed" watchdog that requires kicks at specific times, or a health-check mechanism where the processor must perform a self-test and report status. But even a basic external watchdog is a significant improvement over relying solely on the internal one.

I'd also look at the reset path: when the watchdog fires, does it reset the entire system cleanly, including the FPGA configuration and all peripherals? If the reset only affects the microcontroller, the system might come back in an inconsistent state.

**Possible follow-ups:** How would you design the external watchdog circuit to be radiation-tolerant itself? What if the watchdog's timeout is too short for the system's boot time — how would you handle that?

---

## Q3: How would you approach designing a radiation-tolerant power-on reset (POR) circuit for a space-deployed system that must guarantee proper initialization across all operating conditions, including after a single-event latch-up (SEL) event that causes a temporary overcurrent condition?

**Answer:** The POR circuit has two distinct jobs: ensuring clean initialization at power-up, and ensuring recovery after a latch-up event. These have different requirements, and I'd design for both.

For power-up, the POR must hold the system in reset until all supply rails are within their specified operating ranges and stable. I'd use a voltage supervisor IC that monitors each rail with hysteresis and a delay — not just a simple RC circuit, which can be unreliable with slow-rising supplies or brown-out conditions. The supervisor should have a defined threshold with margin against the minimum operating voltage of the logic, and the reset release should be delayed until all rails are stable.

For latch-up recovery, the challenge is that the system may be drawing excessive current, and the supply voltage may be collapsed or oscillating. The POR must be able to generate a clean reset once the overcurrent condition is cleared. I'd design the latch-up protection as a current-limiting or current-sensing circuit that detects the overcurrent, removes power from the affected load (or crowbars it), and then re-applies power after a delay. The POR should be designed to work with this sequence: it should hold reset asserted during the power interruption and release it only after the supply has been re-established and stable.

One subtlety: the POR circuit itself must be radiation-tolerant. A commercial voltage supervisor may be susceptible to single-event transients that cause false resets or, worse, failure to assert reset when needed. I'd select a rad-hard supervisor if available, or use a discrete implementation with radiation-tolerant components. I'd also add redundancy — for example, two supervisors with their outputs ANDed together — so that a single-event upset in one doesn't cause a spurious reset or a missed reset.

Finally, I'd consider the reset release timing: after a latch-up event, the system should come up in a known state, which may require a longer reset pulse than normal power-up to allow all devices to fully re-initialize.

**Possible follow-ups:** How would you test the POR circuit to verify it works correctly under latch-up conditions? What if the supervisor IC itself is not radiation-characterized — how would you qualify it?

---

## Q4: How would you approach designing a memory scrubbing strategy for an SRAM-based FPGA in a space application, and what trade-offs would you consider?

**Answer:** Memory scrubbing for an SRAM-based FPGA is about correcting single-event upsets in the configuration memory before they accumulate to the point of causing a functional failure. The core trade-off is between scrub frequency, scrub coverage, and the overhead (in logic, power, and bus bandwidth) required to implement it.

The first decision is scrub granularity: do you scrub the entire configuration frame by frame, or only critical frames? Full scrubbing is simpler and catches all upsets, but it takes longer and may not be feasible if the configuration memory is large and the scrub must complete within a certain window. Partial scrubbing — targeting only frames that contain critical logic — is faster but leaves non-critical frames unprotected, which may be acceptable if those frames only affect non-essential functions.

The second decision is scrub method: readback-compare or blind scrubbing. Readback-compare involves reading the configuration memory, comparing it against a golden copy, and correcting any differences. This detects upsets but requires a golden copy stored in radiation-tolerant memory (e.g., rad-hard flash or PROM) and consumes bus bandwidth for the readback. Blind scrubbing simply rewrites the configuration memory from the golden copy on a periodic basis, without reading it first. This is simpler and faster, but it can't detect upsets that occur between scrubs, and it may overwrite a configuration that has been intentionally modified (e.g., by a dynamic reconfiguration).

The third consideration is scrub frequency. The scrub interval must be short enough that the probability of multiple upsets accumulating in the same frame — which could cause a functional failure — is acceptably low. This depends on the upset rate, which varies with orbit and solar activity. I'd calculate the expected upset rate and set the scrub interval to achieve a target mean time to failure, typically with a margin of 10x or more.

I'd also consider the interaction between scrubbing and the application logic. Scrubbing the configuration memory doesn't affect the state of the flip-flops or block RAM, so the application logic continues running during the scrub. However, if a configuration upset has already caused a functional error, scrubbing alone won't fix it — you may need to also reset the affected logic or reload the design.

Finally, I'd think about the implementation: the scrub controller can be implemented in the FPGA fabric itself, but that logic is also susceptible to upsets. A more robust approach is to use a separate rad-hard device (e.g., a rad-hard microcontroller or a dedicated scrub controller) to perform the scrubbing, so that a single upset in the FPGA can't disable the scrub function.

**Possible follow-ups:** How would you determine the optimal scrub interval for a given orbit? What if the golden copy of the configuration bitstream is corrupted — how would you detect and recover from that?

---

## Q5: Imagine you are leading a design review for a space-deployed system that uses a COTS DC-DC converter to generate a 3.3V rail for digital logic. The converter's datasheet specifies a maximum output voltage of 3.47V under worst-case conditions, and the FPGA's absolute maximum rating is 3.6V. A junior engineer argues that the 130 mV margin is acceptable because "the FPGA will never actually see 3.47V in practice." How would you handle this disagreement?

**Answer:** I'd acknowledge the engineer's point that the worst-case condition may be unlikely, but I'd explain that "unlikely" is not the same as "impossible," and in a space-deployed system, we design for worst-case conditions because we can't repair or replace components after launch.

The 130 mV margin might seem comfortable, but I'd ask the engineer to walk through the full worst-case analysis. The converter's 3.47V maximum is likely specified at a particular input voltage, load current, and temperature. Are we accounting for all of those simultaneously? What about transient conditions — during a load step, the output voltage can overshoot beyond the steady-state specification. What about the FPGA's absolute maximum rating — is it specified for continuous operation or only for short transients? If the FPGA's absolute maximum is 3.6V but the recommended operating range is lower, say 3.3V ±5% (3.135V to 3.465V), then the converter's worst-case output of 3.47V already exceeds the recommended range, even if it's within the absolute maximum.

I'd also consider the radiation environment. Total ionizing dose can cause shifts in the converter's reference voltage and feedback circuitry, potentially pushing the output voltage higher over the mission lifetime. If the converter is COTS and not radiation-characterized, we don't know how its output will drift. Similarly, single-event transients in the converter's control circuitry could cause output voltage spikes that exceed the FPGA's absolute maximum, even if the steady-state voltage is within spec.

My recommendation would be to add margin at the system level. Options include: selecting a converter with tighter output voltage tolerance, adding a post-regulator (e.g., an LDO) to guarantee the FPGA supply stays within its recommended range, or adding a voltage supervisor that shuts down the rail if it exceeds a safe threshold. I'd also recommend radiation testing of the converter to characterize its output voltage drift and transient behavior.

The key principle I'd convey is that in space systems, we design for the worst case, not the typical case. A 130 mV margin might be fine on paper, but we need to understand all the factors that could erode that margin over the mission lifetime.

**Possible follow-ups:** How would you determine the acceptable margin for a given component? What if adding a post-regulator introduces its own reliability concerns — how would you weigh those trade-offs?