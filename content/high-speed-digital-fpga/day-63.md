# high-speed-digital-fpga — Day 63

## Q1: How would you approach designing the clock domain crossing for a multi-bit counter value that is continuously incrementing in a fast domain (e.g., 250 MHz) and must be sampled by a slower domain (e.g., 50 MHz) for display or logging, where the sampled value must always be a coherent snapshot and never a corrupted mix of bits?

**Answer:** A continuously changing multi-bit value cannot be passed through per-bit synchronizers, because each bit can resolve on a different destination clock edge and the destination can latch a value that never actually existed in the source domain — a classic coherency failure. The standard approach is to use a handshake or a snapshot register rather than trying to synchronize the live counter directly.

The cleanest pattern is a "capture and hold" scheme: the destination domain raises a request, which is synchronized into the source domain through a two-flop synchronizer. The source domain then loads the current counter value into a holding register and asserts an acknowledge. The acknowledge is synchronized back to the destination, which then reads the held value. Because the value is frozen in the source domain before the destination reads it, the snapshot is guaranteed coherent. The cost is latency — several destination clock cycles — but for display or logging that is almost always acceptable.

An alternative when the counter is monotonic and the destination only needs an approximate value is Gray coding: convert the binary count to Gray before crossing, synchronize the Gray bits, then convert back to binary in the destination. Because only one Gray bit changes per increment, a synchronizer can only ever capture the old value or the new value, never a spurious intermediate. This is lower latency but only works when the value changes by one step at a time and the destination tolerates a one-count lag.

The decision hinges on whether the destination needs an exact, coherent value (use the handshake) or a monotonic approximation (use Gray coding). I would also add an assertion or formal check that the held register is not updated while the acknowledge is pending, since that is the failure mode that silently corrupts the snapshot.

**Possible follow-ups:**
- How would you handle the case where the source counter can increment faster than the handshake can complete, so the destination never sees a stable value?
- What CDC verification techniques would you use to prove the handshake is correct before tape-out?

## Q2: How would you approach debugging an FPGA design where the DDR3 interface passes its built-in calibration and memory test at power-up, but fails intermittently only after the device has been running for several minutes and the board has warmed up?

**Answer:** A failure that appears only after thermal soak points strongly at a timing margin issue rather than a functional bug — the interface is marginal at the calibration temperature and drifts out of the eye as the die and board heat up. The first thing I would do is separate the two contributors: the FPGA's internal delay (which shifts with junction temperature) and the PCB/DRAM delay (which shifts with board temperature). If the failure correlates with FPGA junction temperature rather than ambient, the internal delay lines are the likely culprit; if it correlates with ambient, the board or DRAM is more suspect.

Practically, I would instrument the design to log the calibration results — the per-bit read/write leveling delays and the DQS-to-DQ skew — at power-up and again at the point of failure. If the calibration window is narrow to begin with, that tells me the interface was never robust and the thermal drift simply pushed it over the edge. I would also check whether the memory controller is re-calibrating periodically or only once at boot; many controllers support periodic re-calibration, and enabling it can mask a marginal design, but the real fix is to widen the margin.

On the hardware side, I would look at the reference voltage and termination: VREF and ODT settings that are correct at 25 °C can be wrong at 85 °C if the regulator drifts. I would also verify the power integrity of the DDR rails under thermal load, since a rail that sags slightly at temperature can shrink the input eye. The systematic approach is to characterize the eye at both temperature extremes using the controller's built-in eye-scan or a BER test, then adjust the leveling offsets and termination to center the eye across the full temperature range rather than optimizing for room temperature.

**Possible follow-ups:**
- How would you distinguish between a DRAM-side thermal issue and an FPGA-side one without swapping parts?
- What changes to the calibration algorithm would you make to make it robust across temperature?

## Q3: How would you approach designing the power distribution network for an FPGA transceiver bank, where the rails have both high-frequency switching noise from the SerDes and slower, larger current transients from the fabric, and you need to keep the supply within the transceiver's tight ripple specification?

**Answer:** The transceiver rails are the hardest PDN problem on most FPGA boards because the noise sources span a very wide frequency range and the tolerance is tight. I would start by separating the two noise mechanisms. The high-frequency switching noise from the SerDes is in the hundreds of MHz to GHz range and is handled by the on-die and package capacitance plus the highest-frequency discrete capacitors placed as close to the balls as possible. The slower, larger transients from the fabric are in the tens to hundreds of kHz range and are handled by bulk capacitance and the regulator's loop bandwidth.

The key insight is that the PDN must present a low impedance across the entire frequency range where the current transients occur, not just at one frequency. I would target a flat impedance profile from the regulator's crossover frequency up to the point where the on-die capacitance takes over. That means selecting capacitor values so their self-resonant frequencies overlap and cover the band without gaps, and placing the smallest-value capacitors closest to the load. I would also pay attention to the mounting inductance — a capacitor with the right value but a long via loop can be useless at high frequency.

For verification, I would use a combination of simulation and measurement. A PDN impedance simulation with the actual stack-up and placement gives the impedance profile before layout is committed. After the board is built, I would measure the rail with a wideband probe and a fast oscilloscope, and if possible inject a known current step to measure the transient response. For the transceiver specifically, I would also check the jitter of the recovered clock under worst-case traffic, since supply noise couples into the SerDes and shows up as jitter.

**Possible follow-ups:**
- How would you decide between a single regulator with a wideband loop and multiple regulators for the transceiver rails?
- What layout practices would you enforce to keep the mounting inductance of the high-frequency capacitors low?

## Q4: How would you approach verifying that a high-speed FPGA design's timing constraints are complete and correct before sign-off, given that a missing or incorrect constraint can produce a design that passes timing analysis but fails in hardware?

**Answer:** The core problem is that timing analysis only checks what you tell it to check, so a clean report is meaningless if the constraints are incomplete. I would treat constraint completeness as a separate verification task, not something that falls out of the timing report.

The first step is to enumerate every clock in the design and confirm each one has a create_clock or create_generated_clock constraint with the correct period, and that the clock relationships (synchronous, asynchronous, or exclusive) are explicitly declared. Any clock that is not declared will have its paths analyzed as if they were unconstrained, which usually means they are silently ignored. I would also check that every input and output port has a set_input_delay or set_output_delay relative to a real reference clock, because unconstrained I/O is a common source of hardware failures that simulation never catches.

The second step is to look for false paths and multicycle paths that were added to silence violations rather than because the path is genuinely false. These are the most dangerous constraints because they hide real problems. I would review each one and require a justification — a false path should only be used when the path is structurally impossible to exercise, not when it is merely inconvenient. I would also run a "constraint coverage" check: a script that reports any path in the design that is not covered by at least one constraint, so nothing falls through the cracks.

Finally, I would cross-check the constraints against the design intent using a combination of static analysis and targeted simulation. For critical interfaces like DDR or source-synchronous ADC buses, I would verify the timing budget by hand against the datasheet and confirm the constraints match. The goal is to make the constraints a reviewed artifact, not an afterthought.

**Possible follow-ups:**
- How would you detect a constraint that is technically present but has the wrong value, such as a clock period that is too long?
- What role would you give to formal or lint tools in catching constraint errors?

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** This is a teaching moment, not a blame moment, and the way I handle it matters more than the specific fix. The engineer's reasoning is a common and understandable mistake — they've observed the signal working in simulation and concluded it is safe, without realizing that simulation does not model metastability or the timing relationship between asynchronous clocks. My first move is to acknowledge that the observation is real but explain why it is not sufficient evidence.

I would walk through the failure mechanism concretely: the signal is asynchronous to the destination clock, so the destination flop's setup and hold window can be violated, and the flop can go metastable — its output can be an intermediate voltage or oscillate before resolving. Even if it resolves, it can resolve to different values on different boards or at different temperatures, which is exactly the kind of intermittent failure that is hardest to debug in the field. The fact that it "works" in the lab is not a guarantee; it just means the violation hasn't happened yet.

Then I would move to the fix. For a single-bit control signal, a two-flop synchronizer is the standard solution, and I would explain the reasoning: the first flop may go metastable, but the second flop gives the metastability time to resolve before the signal is used. For a multi-bit bus, a two-flop synchronizer per bit is not sufficient, and we would need a handshake or a FIFO depending on the data rate. I would also point out that the synchronizer needs to be placed correctly in the RTL and constrained properly so the tools do not optimize it away or retime it.

Finally, I would use this as an opportunity to improve the team's process. I would suggest adding a CDC lint check to the design flow so that unsynchronized crossings are caught automatically rather than relying on review. That way the lesson is institutionalized, not just applied to this one instance. Throughout, I would keep the tone collaborative — the goal is to make the engineer a better designer, not to make them defensive.

**Possible follow-ups:**
- How would you handle it if the engineer pushed back and insisted the signal was genuinely stable, perhaps because it comes from a slow source?
- What would you do if you discovered this same pattern in several other places in the design after the review?