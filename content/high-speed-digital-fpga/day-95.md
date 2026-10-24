# high-speed-digital-fpga — Day 95

## Q1: How would you approach designing the configuration and boot path for an FPGA that must load its bitstream from external flash, where the flash device has a non-trivial wake-up latency and the board may be power-cycled rapidly?

**Answer:** The core problem is that the FPGA's configuration controller starts issuing commands a fixed time after power-good, but the flash may still be in its internal power-up or wake-from-deep-power state and will not respond yet. I would treat this as a sequencing and handshake problem rather than a "pick a bigger flash" problem.

First, I would characterize the flash's actual timing: power-up-to-ready time, any tRST or wake-up delay after a reset or deep-power exit, and the first-access latency versus steady-state read latency. Those numbers, not the datasheet's typical read timing, drive the design. Then I would make the FPGA wait for a genuine ready indication rather than a fixed delay — either the flash's own ready/busy pin if it has one, or a conservative delay derived from the worst-case power-up spec across temperature and supply ramp. A fixed delay tuned on the bench is exactly the thing that fails on the cold board or the fast-ramping supply.

For rapid power-cycling, the risk is that the supply rails have not decayed below the flash's reset threshold before power is reapplied, so the flash comes up in an indeterminate state. I would add a proper supply supervisor with a defined reset threshold and hysteresis, and if the application truly allows back-to-back power cycles, consider a brown-out detector that holds the FPGA in reset until the rails are valid and stable. On the FPGA side, I would use the configuration controller's own error/retry mechanism where available, and design a fallback: if the primary image fails to load within a timeout, fall back to a golden image or assert a system reset and retry.

I would also verify the whole path at the corners — slow ramp, fast ramp, hot, cold, and rapid re-power — because this class of bug is almost always a corner-case timing issue, not a nominal-condition one.

**Possible follow-ups:**
- How would you decide between a fixed worst-case delay and a hardware ready handshake, and what would make you choose one over the other?
- If the flash is shared with another device (e.g., a processor that also boots from it), how does that change your sequencing?

## Q2: How would you approach debugging an FPGA design where the device configures successfully and runs correctly for a period of time, but then the configuration appears to be lost — the device stops responding and requires a reconfiguration to recover?

**Answer:** "Configuration lost" is a symptom with several very different root causes, so the first job is to narrow down what actually happened rather than assume the bitstream was corrupted. I would instrument the board to capture the state at the moment of failure: is the DONE pin still asserted? Is INIT_B or the configuration error flag toggling? Is the device's internal oscillator or a heartbeat signal still running? That single observation splits the problem in half — if DONE is still high and a heartbeat is alive, the fabric is configured and the issue is functional (a hung state machine, a clock that stopped, a PLL that lost lock); if DONE dropped or the error flag fired, the configuration itself was disturbed.

If the configuration really is being lost, the usual suspects are power integrity and environmental disturbance. A transient on the core or auxiliary rail — a load step, a marginal regulator, a decoupling network that resonates — can dip the supply below the configuration-retention threshold and reset the fabric. Thermal effects can do the same if a regulator or a solder joint is marginal. I would scope the rails with a fast probe at the failure moment, and I would check whether the failure correlates with a specific activity (a burst of DSP traffic, a transceiver link coming up, a motor or relay nearby).

Other causes worth ruling out: a watchdog or supervisor that is resetting the device (so it looks like lost configuration but is actually a reset), a configuration flash that is being disturbed by another master on a shared bus, or a marginal configuration clock. I would also check whether the failure is reproducible with a specific stimulus or only with time, since time-correlated failures point at thermal or drift, and stimulus-correlated failures point at functional or power-integrity issues.

The fix follows the cause: tighten the PDN, add or resize bulk capacitance, fix the supervisor thresholds, or correct the functional hang. I would not "fix" it by adding an automatic reconfiguration watchdog unless I understood the cause, because that masks a real reliability problem.

**Possible follow-ups:**
- How would you distinguish a genuine configuration loss from a device reset caused by an external supervisor?
- What would you look for on the core rail to confirm a power-integrity cause, and what probe bandwidth would you need?

## Q3: How would you approach designing the clock domain crossing for a multi-bit Gray-coded counter value that increments continuously in a fast domain (e.g., 250 MHz) and must be sampled by a slower domain (e.g., 50 MHz) for logging, where the sampled value must always be a coherent snapshot and never a corrupted mix of bits?

**Answer:** The key insight is that a Gray code changes only one bit per increment, so a value sampled at an arbitrary instant is either the old value or the new value — never a corrupted mix — provided the receiving domain re-registers the bus through a proper synchronizer and the bits are sampled together. That is the whole reason to use Gray coding for a continuously changing counter crossing domains.

The design: in the fast domain, keep the counter in binary for arithmetic, and convert to Gray with the standard XOR reduction (gray = binary ^ (binary >> 1)) as a registered output. In the slow domain, pass the Gray bus through a two-flop synchronizer per bit (or a single synchronizer stage followed by a register, depending on the tool's CDC methodology), then convert back to binary for logging. Because only one bit transitions per increment, the worst case at the sampling boundary is that you capture either the previous or the next count — both are valid, coherent values. The metastability window affects at most the one changing bit, and the two-flop synchronizer resolves it to one of the two stable states.

The subtleties I would call out: the Gray code must be generated and registered in the source domain so that all bits launch from the same clock edge — if the bits are combinational and skew between them exceeds a clock period, the one-bit-at-a-time guarantee breaks. I would also make sure the counter increments by exactly one per step; if it can jump by more than one (e.g., a prescaler that adds a variable amount), Gray coding no longer guarantees single-bit change and the scheme is invalid. Finally, I would constrain the CDC in the timing constraints and run the tool's CDC checker to confirm the synchronizer is recognized, and I would document the assumption that the counter is monotonic with unit steps.

**Possible follow-ups:**
- What happens to the coherence guarantee if the counter can be reset or loaded with an arbitrary value in the fast domain?
- How would you verify this CDC in simulation, given that metastability is not modeled by default?

## Q4: How would you approach mitigating via stub effects on a high-speed serial channel that must transition between the top and bottom layers of a thick backplane?

**Answer:** A via through a thick backplane is a stub: the portion of the barrel below the layer where the signal enters (or above where it exits) is an open-circuited transmission-line segment that resonates and causes a notch in the channel's insertion loss, plus reflections that close the eye at high data rates. The longer the stub relative to the signal's wavelength, the lower the frequency of the first resonance and the worse the impact. So the whole mitigation strategy is about making the stub electrically short or compensating for it.

The first lever is layer assignment and via design: route the signal on layers close to the connector or the destination so the stub is short, and use blind or buried vias where the fabrication process allows, since those eliminate the unused barrel entirely. If back-drilling is available, use it to remove the unused portion of the barrel below the signal layer — this is the standard fix on thick backplanes and is very effective, at the cost of an extra fabrication step and some depth tolerance. I would specify the back-drill depth with margin and confirm the fabricator's capability.

The second lever is to compensate the residual stub: add a small amount of capacitance or a tuned structure at the via to shift or damp the resonance, or use the connector and package models together with the via model in a channel simulation to see whether the eye still closes. I would not rely on "it's only a few hundred mils" reasoning — at multi-gigabit rates a stub of a few hundred mils can put a notch right in the band of interest.

The third lever is at the system level: choose a connector and layer stack-up that minimize the transition, and if the channel is marginal, use the SerDes's equalization (pre-emphasis and receive equalization) to compensate — but equalization cannot recover a deep notch, so the physical fix comes first. I would verify with a 3D electromagnetic extraction of the via and connector, feed that into a channel simulation with the SerDes IBIS-AMI models, and confirm the eye and BER margin before committing to the stack-up.

**Possible follow-ups:**
- How would you decide whether back-drilling is worth the cost versus accepting the stub and relying on equalization?
- What would you look for in the channel's insertion-loss plot to confirm a via stub is the culprit rather than the connector?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer presents a timing closure report showing all constraints met, but you notice the report was generated with a set of timing exceptions (false paths and multicycle paths) that the engineer added to make the design close. The engineer argues that the exceptions are legitimate because "those paths don't need to meet single-cycle timing." How do you handle this situation?

**Answer:** I would treat this as a review of the exceptions themselves, not as an accusation, because the engineer may well be right — multicycle paths and false paths are legitimate tools when they reflect the actual design intent. The problem is that an exception is a promise to the tool, and a wrong promise produces a design that passes timing analysis and fails in hardware. So the review question is: for each exception, can we justify it from the design's behavior, and is it documented?

My approach in the review would be to walk through the exceptions one at a time and ask three things. First, what is the actual relationship between the launch and capture clocks on this path — is it genuinely asynchronous (false path), or is it a synchronous path that happens to be slow (multicycle)? Second, if it is a multicycle path, what guarantees the data is stable for the number of cycles claimed — is there a handshake, a valid signal, or a state machine that holds the data? Third, is the exception scoped as tightly as possible — a false path on a whole clock domain is a very different risk from a false path on one named net.

I would ask the engineer to demonstrate the justification, not just assert it. For a multicycle path, that means showing the enable or handshake that holds the data; for a false path, showing that the two domains are truly asynchronous and that the crossing is handled by a proper synchronizer. If the justification holds, I would ask that it be documented in the constraints file with a comment and, ideally, covered by a CDC or timing assertion so a future change cannot silently invalidate it. If it does not hold, we remove the exception and fix the design — retime, pipeline, or restructure — rather than paper over it.

The tone matters: I want the engineer to leave the review understanding *why* exceptions are dangerous, not feeling that they were caught cheating. I would frame it as "the exception is a claim we're making to the tool; let's make sure we can defend it," and I would make documenting exceptions a standing item in the review checklist so it becomes routine rather than personal.

**Possible follow-ups:**
- How would you verify after the fact that a multicycle path exception is actually safe, given that the tool will no longer check it?
- What would you do if the engineer's justification is plausible but you cannot fully verify it before tape-out?