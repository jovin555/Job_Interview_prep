# high-speed-digital-fpga — Day 44

## Q1: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design's internal state machine appears to be stuck in an illegal state only when a specific external input sequence occurs, and the issue is not reproducible in RTL simulation?

**Answer:** This is a classic symptom of a design that behaves correctly in simulation but fails in hardware due to differences between the simulated model and the actual implementation. My approach would be systematic:

First, I'd verify that the state machine encoding is correct and that the reset behavior is well-defined. A common root cause is that the state machine enters an illegal state due to a metastability event on an asynchronous input, or due to a race condition between state transitions and input sampling. I'd check whether all inputs to the state machine are properly synchronized to the clock domain — if any input comes from an asynchronous source without a two-flop synchronizer, that's a prime suspect.

Second, I'd examine the specific input sequence that triggers the failure. In simulation, inputs change at deterministic times relative to the clock edge. In hardware, input timing relative to the clock edge varies continuously. If the state machine samples an input that is changing at the clock edge, metastability can occur, and the state machine can end up in an unintended state. I'd look for any paths where the input is used combinationally in the next-state logic without proper synchronization.

Third, I'd add debug instrumentation. I'd use an integrated logic analyzer (ILA) core to capture the state register value, the inputs, and the next-state logic outputs around the time of the failure. This would tell me whether the state machine is actually in an illegal state, or whether it's in a legal state but the outputs indicate otherwise. I'd also check whether the state encoding uses one-hot or binary encoding — one-hot is more robust for detecting illegal states because any state with more than one bit set is immediately identifiable.

Fourth, I'd review the synthesis and implementation reports. Sometimes the synthesis tool optimizes away "unreachable" states or merges equivalent states in ways that change behavior. I'd verify that the state encoding constraints (if any) were respected, and that no false paths or multicycle constraints were incorrectly applied to the state machine logic.

Finally, if the issue is reproducible, I'd create a testbench that models the actual hardware timing more accurately — including input timing variations, clock jitter, and asynchronous input behavior — to try to reproduce the issue in simulation. If the state machine has a "safe" state or a watchdog timeout mechanism, I'd verify that it's working correctly.

**Possible follow-ups:**
- How would you design the state machine differently from the start to make this class of problem less likely to occur?
- What specific checks would you perform on the synthesis constraints to rule out incorrect false-path or multicycle assignments?

---

## Q2: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** When data changes frequently and latency matters, the fundamental challenge is that you cannot use simple multi-flop synchronization for multi-bit data — each bit could be captured at a different time, producing a corrupted word. The standard approaches are:

**Asynchronous FIFO:** This is the most robust solution for continuous, high-frequency data transfer. The key design considerations are: (1) using Gray-code pointers on both sides to safely cross the clock boundary, (2) properly synchronizing the pointers with two-flop synchronizers, (3) ensuring the FIFO depth is sufficient for the worst-case burst size and latency variation, and (4) handling the full/empty flags correctly. The latency is bounded by the FIFO propagation delay plus synchronization latency (typically 2-3 destination clock cycles for the empty flag to propagate). For minimizing latency, I'd place the FIFO as close to the consuming logic as possible and consider using a "show-ahead" or "first-word fall-through" mode so that the first word is available at the output before the read request arrives.

**Handshake with data hold:** For infrequent transfers, a four-phase handshake (request/acknowledge) ensures data integrity, but it has higher latency and lower throughput. To minimize latency, I'd use a two-phase (edge-sensitive) handshake instead of four-phase, which reduces the number of clock cycles per transfer.

**MUX-based synchronization with feedback:** For very wide buses where FIFO implementation is expensive, a technique using a "data valid" signal synchronized through a pulse synchronizer, combined with holding the data stable until the destination acknowledges, can work. The data bus itself doesn't need synchronization — only the control signals do. The destination samples the bus only after seeing the synchronized valid signal, ensuring the data has settled.

For the specific case of frequently changing data with minimal latency, I'd lean toward the asynchronous FIFO with Gray-coded pointers. The latency through a well-designed asynchronous FIFO is typically 3-5 destination clock cycles, which is usually acceptable. If that's still too much, I'd need to question whether the clocks are truly asynchronous — if they have a known frequency relationship, I could use a synchronous FIFO with properly generated read/write enables, which has lower latency.

I'd also verify the design with formal CDC verification tools or careful simulation with randomized clock phase offsets, since CDC bugs are notoriously difficult to catch in normal simulation.

**Possible follow-ups:**
- How would you determine the required FIFO depth for this application?
- What happens if the destination clock is much faster than the source clock — does that change your approach?

---

## Q3: How would you approach verifying that a high-speed FPGA design will meet its timing requirements when you have a mix of logic operating at 200 MHz and 400 MHz, and the design includes paths that cross between these domains?

**Answer:** This requires a multi-layered verification approach:

**Constraint definition:** First, I'd ensure that all clocks are properly defined in the SDC (Synopsys Design Constraints) file. This includes creating the 200 MHz and 400 MHz clocks, defining their relationship (if they're derived from the same source, I'd use `create_generated_clock` with the appropriate divide-by-2 relationship), and setting clock uncertainty values that account for jitter and board-level effects. If the clocks are truly asynchronous, I'd need to define CDC constraints properly.

**CDC analysis:** For paths crossing between the 200 MHz and 400 MHz domains, I'd first determine whether these are true asynchronous crossings or whether they have a known phase relationship. If they're derived from the same PLL with a known relationship, I can use `set_clock_groups` or `set_false_path` only on properly synchronized paths. For genuinely asynchronous crossings, I'd verify that every crossing uses a proper synchronization mechanism (FIFO, handshake, or multi-flop synchronizer for single-bit signals). I'd use a CDC verification tool if available, or carefully review each crossing manually.

**Timing closure:** For the 400 MHz paths, I'd run timing analysis and examine the critical paths. If timing fails, I'd look at: (1) whether the logic is properly pipelined, (2) whether the synthesis tool is inferring the right structures (DSP slices, block RAMs), (3) whether placement is optimal, and (4) whether I/O constraints are realistic. For the 200 MHz domain, timing is usually easier, but I'd still check for hold-time violations, which can occur even at lower frequencies.

**Cross-domain timing:** For paths that cross between domains (if they're synchronous with a known relationship), I'd verify that the timing tools are correctly analyzing the inter-domain paths. If the 400 MHz clock is an exact multiple of the 200 MHz clock, the tools can analyze the paths, but I'd need to ensure the constraints reflect the actual relationship. If there's uncertainty in the phase relationship, I'd add appropriate uncertainty values.

**Simulation verification:** I'd run gate-level simulation with back-annotated delays (SDF) to verify that the design works with actual timing. I'd also run simulation with different clock phase offsets to stress-test the CDC paths.

**Hardware validation:** Finally, I'd plan a hardware bring-up strategy that includes: (1) checking clock frequencies and jitter with an oscilloscope, (2) running built-in self-tests (BIST) for any memory interfaces, (3) using chipscope/ILA to monitor internal signals at speed, and (4) running extended stress tests at temperature and voltage corners.

**Possible follow-ups:**
- How would you handle a situation where the 400 MHz domain has paths that barely meet timing with zero margin?
- What specific clock uncertainty values would you use, and how would you justify them?

---

## Q4: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** This is a demanding PDN requirement — 20A at 0.85V with 1A/ns slew rate means the PDN impedance must be extremely low across a wide frequency range. The target impedance can be calculated: with ±3% tolerance (25.5 mV) and 20A transient, the maximum allowable PDN impedance is approximately 1.275 mΩ across the frequency range of interest.

My approach would be:

**Frequency-domain analysis:** The PDN must maintain low impedance from DC up to the frequency where the on-die decoupling takes over (typically hundreds of MHz). I'd break the PDN into tiers: (1) voltage regulator module (VRM), (2) bulk decoupling on the board, (3) high-frequency ceramic capacitors near the FPGA, (4) the FPGA package and on-die capacitance. Each tier is effective over a specific frequency range, and the goal is to have no gap in coverage.

**VRM selection:** The VRM must handle the DC current and have a fast enough transient response. For 20A with 1A/ns slew rate, a multi-phase buck converter with a high switching frequency (or a VRM with excellent transient response) is needed. The VRM's output impedance and bandwidth determine its effectiveness up to a few hundred kHz. I'd also consider the VRM's control loop stability and whether additional bulk capacitance is needed to handle the initial transient before the VRM loop responds.

**Bulk decoupling:** I'd place bulk capacitors (e.g., 470 µF to 1000 µF polymer or tantalum capacitors) near the FPGA to handle transients in the 10 kHz to 1 MHz range. The ESR and ESL of these capacitors matter — I'd use multiple capacitors in parallel to reduce effective ESR and ESL.

**High-frequency decoupling:** For the 1 MHz to 100 MHz range, I'd use a matrix of ceramic capacitors (0402 or 0201 size) with values from 0.1 µF to 10 µF, placed as close to the FPGA power pins as possible. The key is minimizing the loop inductance — the capacitors must be connected to the power and ground planes with short, wide traces or directly through vias. I'd use a mix of capacitor values to create a low-impedance profile across a wide frequency range.

**PCB stack-up and plane design:** The power and ground planes must be closely coupled (thin dielectric) to provide low inductance. For 0.85V core, I'd dedicate a full plane layer, with the ground plane directly adjacent. The plane pair provides distributed capacitance that helps at higher frequencies. I'd also ensure that vias connecting the FPGA power pins to the planes are numerous and placed close together to minimize inductance.

**Simulation and verification:** I'd perform PDN simulation using tools like SIwave or PowerSI to verify the impedance profile meets the target. I'd simulate the frequency-domain impedance from the VRM output to the FPGA power pins, and also run time-domain transient simulations with a current profile that models the FPGA's worst-case switching behavior. On the hardware, I'd verify with: (1) an impedance analyzer to measure the PDN impedance, (2) a high-bandwidth oscilloscope with a differential probe to measure voltage ripple at the FPGA power pins during worst-case operation, and (3) thermal imaging to check for hot spots.

**Possible follow-ups:**
- How would you determine the worst-case transient current profile for the FPGA?
- What would you do if the measured voltage ripple exceeds the ±3% specification?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical concern and the junior engineer's understanding of the system behavior, while maintaining a constructive and educational tone.

First, I'd acknowledge the engineer's reasoning — they're correct that average rates matter, and it's good that they're thinking about the memory controller's write buffer. This validates their analytical approach. Then I'd guide them through a more complete analysis:

I'd ask them to walk me through the worst-case burst scenario. Specifically: what's the maximum burst duration from the ADC, what's the ADC's maximum instantaneous data rate, what's the DDR3 controller's sustainable write bandwidth (considering refresh cycles, read/write turnaround, and bank conflicts), and what's the latency from the FIFO filling to the memory controller actually accepting data? The key insight is that the memory controller's write buffer is not an infinite resource — it has its own depth, and if the FIFO fills faster than the memory controller can drain it (including the memory controller's own buffering), data will be lost.

I'd suggest we work through the calculation together. For example, if the ADC produces 16-bit samples at 500 MSPS, that's 1 GB/s of data. If the DDR3 interface is 64 bits wide at 600 MHz (DDR — 1200 MT/s), the theoretical bandwidth is 9.6 GB/s, but the sustainable bandwidth might be only 60-70% of that due to refresh overhead, read/write turnaround, and bank conflicts — so maybe 6 GB/s. That seems like plenty of margin, but the question is about burst behavior. If the ADC produces a burst of 1024 samples at full rate, that's 2 KB of data. At 1 GB/s, this burst takes 2 µs. The FIFO is 64 words deep — if each word is 16 bits, that's only 128 bytes, which would fill in 128 ns. The memory controller needs to start accepting data within that time, and if it's busy with a refresh cycle or a read operation, it might not be able to respond in time.

I'd also point out that the FIFO depth needs to account for the round-trip latency of the flow control mechanism. If the FIFO full flag needs to propagate back to the write side, and the memory controller needs time to arbitrate for the DDR3 bus, the total latency could be several hundred nanoseconds. The FIFO needs to be deep enough to absorb data during this latency window.

Rather than just telling the engineer the FIFO is too small, I'd work with them to calculate the required depth based on the worst-case burst scenario and the memory controller's worst-case response latency. I'd also suggest adding a simulation testbench that models the burst behavior and the memory controller's variable latency to verify the FIFO depth is sufficient.

Finally, I'd frame this as a learning opportunity about the difference between average and worst-case analysis in real-time systems. The design review process is exactly for catching these kinds of issues before they become field failures.

**Possible follow-ups:**
- How would you help the junior engineer develop a systematic approach to analyzing burst behavior in future designs?
- What documentation or design notes would you expect the engineer to produce after this review to capture the analysis?