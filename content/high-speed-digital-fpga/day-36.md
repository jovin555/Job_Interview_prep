# high-speed-digital-fpga — Day 36

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For an asynchronous CDC with frequently-changing multi-bit data and a latency constraint, I'd first rule out simple two-flop synchronizers for the data bus itself—they only work for single-bit control signals and can capture a corrupted word when bits arrive at different times. The standard approach is an asynchronous FIFO with gray-coded pointers, which gives you safe, continuous data transfer with bounded latency determined by the FIFO depth and the clock ratio.

The key design decisions are: (1) the FIFO depth, which must accommodate the worst-case burst size plus the round-trip latency of the full/empty flag propagation; (2) gray-code encoding for the read/write pointers so that only one bit changes per increment, making the pointer comparison across clock domains safe; and (3) the synchronization stages for the pointers—typically two or three flip-flops per pointer bit to reduce metastability probability to an acceptable level.

For minimizing latency, I'd use a "show-ahead" or "first-word fall-through" FIFO mode where the first written word appears at the read side without waiting for a read request. I'd also consider whether the frequency relationship is known. If the source clock is always slower than the destination clock, I can use a simpler handshake-based approach with a data-valid signal, but that adds latency per transfer. If the relationship is fixed and rational (e.g., 200 MHz to 150 MHz), I could potentially use a synchronous FIFO with a carefully designed read enable, but I'd still verify the worst-case timing across process, voltage, and temperature corners.

The critical verification step is running CDC analysis tools to check for reconvergence issues—where the same source signal fans out through different synchronization paths and recombines, potentially creating a glitch. I'd also simulate with back-annotated delays and random clock phase offsets to stress the synchronization logic.

**Possible follow-ups:**
- How would you determine the minimum FIFO depth for a specific burst scenario?
- What happens if the FIFO becomes full—how would you handle backpressure in the source domain?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully (DONE pin goes high) but the device does not enter the expected functional state—for example, all outputs remain tri-stated or in a default state?

**Answer:** This is a classic "configuration succeeded, initialization failed" scenario. I'd start by verifying the obvious: check that all power rails are within specification and that the power-good signals are asserted in the correct sequence. Many FPGAs have a specific power-up sequence requirement, and if the core rail comes up before the I/O rail (or vice versa), the device may configure but the I/O buffers may not initialize correctly.

Next, I'd check the configuration status pins beyond DONE—most FPGAs have an INIT_B or similar status pin that indicates whether the device completed its internal initialization sequence. If INIT_B is low after DONE goes high, the device is signaling an initialization error. I'd also verify the mode pins are set correctly; if the device is configured for a different configuration scheme than what the programmer is using, it might appear to load successfully but not actually enter the intended operating mode.

If the status pins look correct, I'd move to the design itself. A common cause is a global reset that's stuck asserted—for example, a reset signal tied to an I/O pin that's floating or held in the wrong state. I'd probe the reset tree with an oscilloscope or logic analyzer to confirm. Another possibility is a clock that isn't running: if the design uses an external clock that's not present, or a PLL that fails to lock, the logic will sit in its default state. I'd check the PLL lock signal and verify the clock is actually toggling at the FPGA pin.

I'd also look at the configuration bitstream itself. If the design was synthesized with incorrect I/O standard constraints—for example, the outputs are configured as tri-state by default and the enable logic is inverted—the device would behave exactly as described. I'd review the I/O constraints in the UCF/XDC file against the schematic, and verify the bitstream was generated from the correct build. Finally, I'd use the FPGA vendor's debugging tools—like ChipScope or SignalTap—to peer inside the device and observe the internal state, which can quickly reveal whether the issue is in the fabric logic or the I/O configuration.

**Possible follow-ups:**
- How would you distinguish between a hardware issue (e.g., bad solder joint on a configuration pin) and a design issue?
- What specific checks would you perform on the configuration clock and data lines?

---

## Q3: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** The core rail is the most challenging because of the combination of high current, fast slew rate, and tight tolerance—±3% of 0.85V is only ±25.5 mV. The PDN design has two distinct aspects: the DC path (IR drop) and the AC path (transient response). For the DC path, I'd calculate the maximum allowable resistance from the regulator output to the FPGA core pins. With 20A and a 25.5 mV budget, the total resistance budget is roughly 1.3 mΩ, which means I need multiple vias in parallel, wide copper planes, and careful placement of the regulator close to the FPGA.

For the AC path, the key is the decoupling capacitor network. The 1A/ns slew rate means that for the first few nanoseconds, the bulk capacitors and the regulator can't respond—only the high-frequency ceramic capacitors and the PCB plane capacitance can supply the current. I'd start with the FPGA vendor's recommended decoupling scheme, which typically specifies a matrix of 100 nF, 1 µF, and 10 µF capacitors in specific package sizes placed as close to the power pins as possible. The critical parameter is the loop inductance: the mounting inductance of the capacitor plus the via inductance to the power plane. For 0201 or 0402 capacitors with micro-vias directly to the plane, the loop inductance can be kept below 500 pH, which gives a usable frequency range up to several hundred MHz.

I'd also consider the PCB stack-up. The core power plane should be adjacent to the ground plane with a thin dielectric (e.g., 100 µm or less) to maximize the interplane capacitance, which acts as a distributed high-frequency decoupling capacitor. For the bulk decoupling, I'd use low-ESR polymer or ceramic capacitors in the 100–470 µF range placed near the FPGA but not necessarily right at the pins, since their effective frequency range is lower.

The verification approach is critical. I'd simulate the PDN impedance using a tool like SIwave or PowerSI, targeting an impedance profile that stays below the target impedance (Z_target = ΔV/ΔI = 25.5 mV / 20A ≈ 1.3 mΩ) across the frequency range of interest, typically from DC to several hundred MHz. I'd also perform a transient simulation with a current step to verify the voltage stays within tolerance. On the bench, I'd measure the PDN impedance with a vector network analyzer and probe the core voltage with a high-bandwidth oscilloscope while running a worst-case toggle pattern on the FPGA.

**Possible follow-ups:**
- How would you determine the frequency range over which the PDN impedance needs to be below the target?
- What are the trade-offs between using more ceramic capacitors versus adding a larger bulk capacitor?

---

## Q4: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a 64-tap FIR filter, and output the filtered result without any dropped samples, while also meeting timing at the target clock frequency?

**Answer:** The first challenge is that 500 MSPS exceeds the typical FPGA fabric clock frequency, so I'd need to use a parallel processing approach. The standard technique is time-division multiplexing: if the fabric clock is 250 MHz, I'd process two samples per clock cycle (a 2-way parallel architecture); if the fabric clock is 125 MHz, I'd need a 4-way parallel architecture. The choice depends on the FPGA's capabilities and the timing closure difficulty.

For a 64-tap FIR filter at 2 samples/cycle, I'd decompose the filter into two parallel filter branches, each processing every other sample. Each branch would implement a 64-tap filter, but the coefficients would be split: one branch uses the even-indexed coefficients, the other uses the odd-indexed coefficients. This is the polyphase decomposition of the filter. The key insight is that each output sample depends on the current input and the previous 63 inputs, so each branch needs access to the full history of inputs, but only every other one.

For the implementation, I'd use the DSP slices efficiently. A 64-tap filter with 16-bit coefficients and 16-bit data requires careful resource planning. Each DSP slice can typically implement a multiply-accumulate operation, so I'd need to consider whether to use a fully parallel structure (64 multipliers, one per tap) or a time-multiplexed structure (fewer multipliers, reused across taps). At 500 MSPS with a 250 MHz fabric clock, each DSP slice can perform two multiply-accumulates per output sample, so I could implement the filter with 32 DSP slices per branch, or 64 total. The trade-off is between resource usage and latency.

The critical timing challenge is the adder tree that sums the 64 partial products. A naive 64-input adder tree would have a long combinational path. I'd pipeline the adder tree—typically using a balanced binary tree with registers between stages—to keep the critical path within the clock period. The latency increases by log2(64) = 6 cycles, but that's acceptable for most applications.

For verification, I'd first create a bit-exact C model of the filter and generate test vectors. I'd simulate the RTL with these vectors and compare the outputs cycle-by-cycle. I'd also verify the parallel architecture produces identical results to the serial version by checking the polyphase decomposition mathematically. Finally, I'd run timing analysis to ensure the design meets the 250 MHz target, and if it doesn't, I'd consider increasing the parallelism to 4-way or using the FPGA's built-in filter IP if available.

**Possible follow-ups:**
- How would you handle the input data alignment when using a polyphase decomposition?
- What would you do if the design doesn't meet timing after pipelining the adder tree?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** I'd approach this as a coaching opportunity rather than simply overriding the engineer's decision. First, I'd acknowledge the valid part of their reasoning—the average-rate analysis is a reasonable starting point—but then I'd walk through the burst scenario concretely. I'd ask the engineer to calculate the worst-case burst: if the ADC produces, say, 256 samples back-to-back at 500 MSPS, that's 256 words arriving in 512 ns. Meanwhile, the DDR3 write path has a finite sustainable rate—even with the memory controller's write buffer, there's a fixed latency for row activation, column access, and precharge. If the memory controller can sustain, say, one write every 4 clock cycles at 250 MHz, that's 62.5M writes/second, which is 125 MB/s. A 256-word burst at 500 MSPS is 256 words in 512 ns, which is 500M words/second—far exceeding the sustainable rate.

I'd then ask the engineer to trace the data flow: the ADC writes 256 words into the FIFO in 512 ns. The memory controller reads at its sustainable rate. If the FIFO is only 64 words deep, it overflows after 64 words, and the remaining 192 words are lost. The memory controller's write buffer doesn't help because it's downstream of the FIFO—the FIFO is the first point of buffering, and it's too shallow.

Rather than just telling the engineer the answer, I'd guide them through the calculation and ask them to propose a solution. The options are: (1) increase the FIFO depth to accommodate the worst-case burst plus the round-trip latency of the flow-control signals; (2) add backpressure from the FIFO to the ADC to pause data capture during bursts—but this may not be possible if the ADC is free-running; or (3) use a larger external buffer or a different memory architecture. The right answer depends on the system requirements: can the ADC be paused, or must every sample be captured?

I'd also use this as a teaching moment about the difference between average and worst-case analysis in real-time systems. The engineer's mistake is common—it's easy to reason about averages, but in data acquisition, the worst-case burst is what determines whether you lose data. I'd encourage the engineer to always ask: "What's the worst-case arrival pattern, and does my buffering handle it?" I'd also suggest they document the burst analysis in the design specification so future reviewers can verify the FIFO depth is justified.

**Possible follow-ups:**
- How would you help the engineer calculate the correct FIFO depth?
- What if the system requirements allow dropping samples during bursts—how would that change your approach?