# high-speed-digital-fpga — Day 37

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For asynchronous clock domains with frequently changing multi-bit data and a latency constraint, I'd first characterize the actual frequency relationship and jitter characteristics of both clocks. If the clocks have a known, stable frequency ratio (even if non-integer), I'd consider a synchronous FIFO with carefully computed depth based on worst-case frequency drift and burst behavior. If truly asynchronous with no reliable relationship, an asynchronous FIFO with gray-coded pointers is the standard approach — it bounds latency to the FIFO's propagation delay plus synchronization time (typically 2-3 destination clock cycles for pointer synchronization).

The key design decisions are: (1) FIFO depth — sized for worst-case burst length plus synchronization latency, not average throughput; (2) pointer encoding — gray code for the read/write pointers to ensure only one bit changes per increment, eliminating multi-bit synchronization hazards; (3) full/empty flag generation — using synchronized pointers with appropriate guard bands to prevent false flags; and (4) data path width — wider FIFO entries reduce the pointer toggle rate relative to data throughput.

For minimizing latency, I'd avoid adding any handshaking on the data path itself. The FIFO approach gives bounded latency of roughly one destination clock cycle for the data plus 2-3 cycles for pointer synchronization. I'd also verify the design with formal CDC verification tools to catch any missed synchronization paths, and run simulation with randomized clock phase offsets to stress-test the boundary conditions.

**Possible follow-ups:** How would you determine the minimum safe FIFO depth for your specific clock relationship? What happens if the frequency ratio drifts over temperature or voltage?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully (DONE pin goes high) but the device does not enter the expected functional state — for example, all outputs remain tri-stated or in a default state?

**Answer:** When configuration completes but the design doesn't become functional, I'd work through this systematically. First, I'd verify the configuration source and bitstream integrity — confirm the bitstream was generated from the correct build (check build timestamp, revision control tag, and that the bitstream matches the target device/package). I'd also check the configuration mode pins and any status registers that report configuration errors.

Next, I'd examine the design's initialization sequence. Many designs have a startup state machine that waits for conditions like PLL lock, external reset deassertion, or a specific input pattern. I'd probe the PLL locked signals, check if the global reset is being held asserted (possibly by an external supervisor circuit or a default I/O state), and verify that clock inputs are actually toggling. A common issue is a clock that never arrives — the PLL never locks, so the design's clock tree never starts.

I'd also check the I/O standard and voltage settings for the output banks. If the bank voltage isn't present or the I/O standard is misconfigured, outputs will remain tri-stated even though the FPGA is configured. I'd verify the VCCO for each bank and check if any output-enable signals are being driven correctly.

Finally, I'd use the FPGA vendor's debug tools — a logic analyzer core inserted into the design, or the ability to read back internal register values through the configuration interface — to observe the actual state of internal signals. This distinguishes between "design never started" versus "design started but is stuck in an early state."

**Possible follow-ups:** How would you distinguish between a configuration problem and a design initialization problem? What if the design works on some boards but not others?

---

## Q3: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 1 GSPS, perform a digital down-conversion (DDC) with a programmable decimation factor, and output the result over a PCIe Gen3 x4 interface?

**Answer:** At 1 GSPS with 16-bit samples, the input data rate is 16 Gbps, which exceeds what a single FPGA fabric clock domain can handle directly. The first step is to deserialize the input into a parallel bus — for example, using 8 or 16 parallel lanes at 125 MHz or 62.5 MHz respectively, depending on the FPGA's I/O capabilities and the ADC interface format (LVDS, JESD204B, etc.).

The DDC chain would use a numerically controlled oscillator (NCO) for mixing, followed by cascaded integrator-comb (CIC) filters for decimation, and then compensation FIR filters to correct the CIC passband droop. The key architectural decision is where to place the decimation stages. I'd mix at the full input rate (in the parallel domain), then decimate in stages — CIC filters are efficient for large decimation factors, while FIR filters handle the final filtering and gain correction. The parallel processing means each filter operates on multiple samples per clock cycle, so I'd use polyphase decomposition to implement the filters efficiently.

For the PCIe Gen3 x4 output, the sustained bandwidth is roughly 3.2 GB/s (about 25.6 Gbps) in each direction, which is sufficient for the decimated data rate. The PCIe interface would use the FPGA's hard IP blocks and DMA engines to move data to host memory. The critical design consideration is buffering — I'd need a FIFO between the DDC output and the PCIe interface to absorb burst mismatches, sized based on the PCIe traffic patterns and the decimated data rate.

The programmable decimation factor adds complexity because the filter coefficients and the CIC decimation ratio must change dynamically. I'd implement the decimation control as a register interface that updates the filter configuration, with careful handling to avoid glitches when changing decimation on the fly — typically by draining the pipeline or using double-buffered coefficient storage.

**Possible follow-ups:** How would you handle the case where the decimated output rate exceeds the PCIe sustained bandwidth? How would you verify the DDC's frequency response matches the specification?

---

## Q4: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** The core rail is the most challenging because of the combination of high current, fast slew rate, and tight tolerance — ±3% of 0.85V means the voltage must stay between roughly 0.825V and 0.875V, leaving very little margin for transient droop. I'd approach this in three layers: the voltage regulator module (VRM), the PCB power plane, and the decoupling capacitor network.

At the VRM level, a 20A rail with 1A/ns slew rate exceeds what a typical switching regulator can respond to directly. The VRM's control loop bandwidth is typically in the tens of kHz to low MHz range, so it can't react to nanosecond-scale transients. The VRM's role is to supply the average current; the transient response must come from the decoupling network. I'd select a VRM with sufficient DC current capability and low output impedance, and place it close to the FPGA with a low-inductance connection.

The PCB power plane provides the first level of high-frequency decoupling. I'd use a dedicated power plane layer for the core rail, with the plane placed adjacent to a ground plane to create a low-inductance parallel-plate capacitor. The plane capacitance depends on the dielectric thickness and area — thinner dielectric gives higher capacitance but may not be practical for all stack-ups. I'd also minimize the inductance between the VRM output and the plane by using multiple vias in parallel.

The decoupling capacitor network handles the highest-frequency transients. I'd use a multi-value capacitor strategy: bulk capacitors (e.g., 100-470 µF) near the VRM for low-frequency energy storage, mid-value capacitors (e.g., 1-10 µF) distributed across the board, and high-frequency capacitors (e.g., 0.1 µF and 0.01 µF) placed as close as possible to the FPGA power pins. The key is to create a low-impedance profile across the entire frequency range of interest — from DC to the frequency where the on-die capacitance takes over.

For verification, I'd perform a frequency-domain analysis of the PDN impedance using simulation tools, targeting a maximum impedance that keeps voltage within tolerance for the expected current transient. I'd also run time-domain simulations with a realistic current waveform (e.g., a step from 10A to 20A with 1A/ns slew rate) to verify the voltage stays within the ±3% window. On the bench, I'd use a high-bandwidth oscilloscope with a differential probe to measure the core voltage during worst-case switching activity.

**Possible follow-ups:** How would you determine the target impedance for the PDN? What if the board is space-constrained and you can't fit all the decoupling capacitors you'd like?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** I'd approach this as a coaching opportunity rather than simply overriding the engineer's decision. First, I'd acknowledge the valid part of their reasoning — the average-rate analysis is correct for steady-state operation, and the memory controller's write buffer does provide some burst absorption. Then I'd walk through the burst scenario concretely: if the ADC produces a burst of, say, 256 samples at full rate while the memory controller is busy with a refresh cycle or a read operation, the FIFO needs to hold all 256 samples plus the data that arrives during the memory controller's busy period. A 64-word FIFO would overflow in that scenario, causing data loss.

I'd ask the engineer to calculate the worst-case burst duration and the memory controller's maximum sustainable write rate, including refresh overhead and bank conflicts. I'd also point out that the memory controller's write buffer depth is a separate resource — the FIFO and the write buffer are in series, and the total buffering must cover the worst-case mismatch between the ADC's instantaneous write rate and the memory's sustainable write rate.

Rather than dictating the solution, I'd ask the engineer to propose a revised FIFO depth based on their analysis, and to document the burst assumptions in the design specification. If they're unsure how to calculate the worst case, I'd work through it with them. I'd also suggest adding a watermark interrupt or a status register that reports FIFO fill level, so the firmware can monitor whether the depth is adequate in real-world operation. The goal is to help the engineer develop the analytical skills to catch these issues themselves in future designs.

**Possible follow-ups:** How would you handle the situation if the engineer still disagrees after your discussion? What if the project schedule doesn't allow time to change the FIFO depth?