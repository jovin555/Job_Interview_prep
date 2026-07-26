# high-speed-digital-fpga — Day 5

## Q1: How would you approach designing a finite state machine (FSM) in an FPGA that must handle asynchronous inputs without metastability issues?

**Answer:** The core challenge with asynchronous inputs is that they can violate the setup/hold times of flip-flops in the FPGA, leading to metastable states where the output hovers at an indeterminate voltage before resolving. The standard approach is to synchronize the asynchronous input using a multi-stage synchronizer—typically two or three cascaded flip-flops clocked by the destination clock domain—before feeding it into the FSM logic. The first flip-flop may go metastable, but the second (and third) provide a full clock cycle for it to resolve, reducing the mean time between failures (MTBF) to an acceptable level.

For the FSM design itself, I would use a one-hot or Gray-encoded state encoding rather than binary, because only one state bit changes per transition, which reduces the chance of the FSM entering an invalid state if the synchronized input is sampled slightly early or late. I would also include a default or "safe" state in the case statement, and consider adding a watchdog timer that forces a reset if the FSM remains in an unexpected state for too long. For critical safety applications, I might implement a triple-redundant FSM with voting logic, though this is area-intensive.

**Possible follow-ups:** How would you choose between two-stage and three-stage synchronizers? What happens if the asynchronous input changes faster than the clock frequency?

---

## Q2: How would you approach debugging an FPGA design where the PLL fails to lock consistently across temperature and voltage variations?

**Answer:** I would start by isolating whether the issue is with the PLL itself or with the reference clock feeding it. First, I'd probe the reference clock input with an oscilloscope to verify it meets the PLL's specified amplitude, frequency accuracy, and jitter requirements across the operating range. If the reference clock is clean, I'd then examine the PLL configuration parameters: the feedback divider (M), pre-divider (N), and post-divider (O) values, as well as the charge pump current and loop filter bandwidth settings.

For temperature/voltage sensitivity, the loop filter bandwidth is often the culprit. A wider bandwidth gives faster lock acquisition but is more susceptible to noise; a narrower bandwidth is more stable but takes longer to lock and may not track temperature-induced drift. I would check the FPGA vendor's PLL simulation tools to model lock time and jitter across the worst-case corner (slow-slow process, high temperature, low voltage). If the PLL has programmable charge pump current settings, I would try increasing it to improve lock range.

I would also verify that the PLL's power supply is clean—ripple on the analog supply rail can prevent lock. A dedicated linear regulator with proper decoupling (ferrite bead + bulk capacitor + multiple 100 nF caps) for the PLL analog supply is essential. Finally, I'd check the PCB layout for noise coupling into the PLL's analog pins from nearby switching digital signals.

**Possible follow-ups:** How would you distinguish between a PLL lock issue caused by power supply noise versus one caused by reference clock jitter? What FPGA-specific tools or features could help diagnose this?

---

## Q3: How would you approach implementing a high-speed serial interface (e.g., 5 Gbps) in an FPGA using the built-in transceivers, and what are the key considerations for the PCB layout around the transceiver channels?

**Answer:** The FPGA's built-in serial transceivers (often called GTY, GTH, or similar depending on the family) handle the high-speed serialization/deserialization, clock recovery, and equalization. The key implementation steps would be: configuring the transceiver channel parameters (line rate, reference clock frequency, pre-emphasis/de-emphasis levels, receive equalization settings), generating the required reference clocks (typically a low-jitter differential clock at a fraction of the line rate), and connecting the transceiver to the serial I/O through the appropriate I/O bank.

For PCB layout, the critical considerations are:
- **Impedance control:** The differential trace pair must be designed for the target impedance (typically 100Ω differential, 50Ω single-ended) with tight tolerance (±10% or better).
- **AC coupling capacitors:** Place series capacitors (typically 100 nF) on the transmit and receive differential pairs, close to the FPGA pins, with careful pad geometry to minimize impedance discontinuity.
- **Reference clock routing:** The transceiver reference clock must be routed as a differential pair with its own dedicated ground return path, isolated from noisy digital signals.
- **Power supply filtering:** Each transceiver channel typically requires multiple voltage rails (transceiver core, transmitter, receiver) with individual ferrite bead filters and decoupling capacitors placed as close as possible to the FPGA power pins.
- **Via minimization:** Each via on a high-speed serial lane introduces impedance discontinuity and signal loss. If vias are unavoidable, back-drilling should be used to remove unused stub lengths.
- **Ground plane continuity:** A solid, uninterrupted ground plane beneath the transceiver channels is essential. Any slot or split in the ground plane beneath the differential pairs will cause impedance mismatch and increased crosstalk.

**Possible follow-ups:** How would you choose between AC coupling and DC coupling for the serial link? What pre-emphasis or equalization settings would you start with, and how would you optimize them?

---

## Q4: How would you approach designing a multi-rate digital filter in an FPGA that must operate at different sample rates (e.g., 48 kHz, 96 kHz, and 192 kHz) while maintaining the same filter characteristics?

**Answer:** The approach depends on whether the filter coefficients need to change with the sample rate or whether the architecture can be made rate-independent. For a filter with fixed frequency-domain characteristics (e.g., a low-pass filter with a 20 kHz cutoff), the normalized cutoff frequency changes with sample rate, so the coefficients must be recalculated for each rate. I would pre-compute coefficient sets for each supported rate and store them in block RAM, then select the appropriate set based on the operating mode.

For the implementation, I would use a systolic or transposed direct-form FIR architecture that can be clocked at a fixed high rate (e.g., 200 MHz) while the data rate varies. The filter would process samples using a clock enable signal derived from the sample rate—each valid sample triggers one filter computation cycle. This approach keeps the logic timing constant regardless of sample rate. The coefficient memory would be addressed by a counter that increments with each clock enable pulse, cycling through the taps.

If the filter must support real-time rate switching without glitches, I would implement a "coefficient update" handshake: when the rate changes, the filter completes its current sample, loads the new coefficient set from a double-buffered memory, and then resumes processing. The double buffer ensures that the filter never sees a partially updated coefficient set.

**Possible follow-ups:** How would you handle the case where the filter must switch rates mid-stream without dropping samples? What are the trade-offs between using a single high-speed clock versus multiple clock domains for this design?

---

## Q5: Behavioral question — You're the lead engineer on a high-speed FPGA design project. During a design review, a junior engineer presents a simulation showing the design meets timing at the slow-slow process corner but fails at the fast-fast corner. The engineer suggests ignoring the fast-fast corner because "the chip will never actually run that fast." How do you handle this situation?

**Answer:** I would first acknowledge the engineer's observation—it's true that the fast-fast corner represents a best-case process variation combined with high voltage and low temperature, which is not a typical operating condition. However, I would explain that we cannot ignore it for several reasons.

First, the fast-fast corner can expose hold-time violations that don't appear at the slow-slow corner. A hold violation means data might arrive at a flip-flop too early, before the previous data has been captured, causing incorrect operation regardless of clock speed. This is a functional failure, not just a performance limitation. Second, during system bring-up or testing in a cold environment, the device could actually operate near the fast-fast conditions. Third, the FPGA vendor's timing analysis tools are designed to verify across all corners because real silicon spans the entire process range—a chip from one wafer might be closer to fast-fast while another is closer to slow-slow.

I would guide the engineer to examine the failing paths in detail. Often, fast-fast failures are caused by insufficient output delay constraints, clock skew, or combinational logic paths that are too short. The fix might involve adding delay elements (using LUT-based delays or dedicated delay cells), adjusting clock skew constraints, or restructuring the logic to balance path delays. I would suggest we work together to identify the root cause and implement a fix, rather than dismissing the corner. This turns the situation into a learning opportunity about why comprehensive timing closure across all corners is a standard industry practice.

**Possible follow-ups:** How would you prioritize which timing violations to fix first when there are hundreds of failing paths? What tools or techniques can help identify the root cause of fast-corner hold violations quickly?