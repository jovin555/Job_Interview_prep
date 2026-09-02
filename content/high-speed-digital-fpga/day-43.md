# high-speed-digital-fpga — Day 43

## Q1: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design's internal state machine appears to be stuck in an illegal state only when a specific external input sequence occurs, and the issue is not reproducible in RTL simulation?

**Answer:** This is a classic case where the problem likely lies in the gap between RTL simulation and the actual hardware implementation. My approach would be systematic:

First, I'd verify that the state machine encoding in the synthesized netlist matches what I intended in RTL. Synthesis tools can re-encode states, and if I've written the FSM with assumptions about specific state encodings, that could cause issues. I'd check the synthesis report and the actual netlist to confirm the state encoding.

Next, I'd look for asynchronous inputs or CDC issues feeding into the FSM. If the external input sequence involves signals that aren't synchronized to the FSM's clock domain, metastability could cause the FSM to enter an illegal state. Even if the input appears to be synchronous in simulation, real-world timing skew between multiple input signals could create a transient condition that the RTL simulation doesn't model. I'd add proper synchronization registers and possibly a handshake mechanism.

I'd also examine the specific input sequence that triggers the failure. Is there a timing relationship between the inputs that could create a glitch on a combinational path feeding the state register's enable or reset? For example, if the FSM uses a "valid" signal derived from combinational logic on the inputs, a glitch on that signal could cause an unintended state transition.

If the FSM has a "safe" state or recovery mechanism, I'd verify it's actually reachable from all states. Sometimes the recovery path itself has a bug that only manifests with specific state+input combinations.

Finally, I'd use an integrated logic analyzer (ILA) or chipscope to capture the actual state register values and input signals around the failure point. This gives ground truth about what's happening in hardware versus what I expect from simulation. I'd trigger on the illegal state value and capture a window of data before the transition to understand how the FSM got there.

**Possible follow-ups:**
- How would you modify your verification approach to catch this class of bug before hardware bring-up?
- What role would formal verification play in your debugging strategy for FSM illegal-state issues?

---

## Q2: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For asynchronous clock domains with frequently changing multi-bit data and low-latency requirements, I'd evaluate several approaches and select based on the specific data characteristics:

**Option 1: Asynchronous FIFO.** This is the most robust general-purpose solution. A properly designed asynchronous FIFO with gray-coded pointers (for the read/write pointer crossing) handles continuous data flow with bounded latency. The key design considerations are: sufficient depth to absorb burst mismatches, correct full/empty generation using synchronized pointers, and careful attention to the gray-code synchronization to avoid multi-bit CDC issues. Latency is typically 2-3 cycles on each side for pointer synchronization plus the FIFO propagation delay.

**Option 2: Handshake-based transfer with data hold.** If the data rate is low enough that the source can wait for acknowledgment, a four-phase handshake (request-acknowledge-request-deassert-acknowledge-deassert) ensures data integrity. The source holds data stable until it receives acknowledgment from the destination. This adds significant latency (potentially 6-10 cycles round-trip) but guarantees no data loss.

**Option 3: MUX-based synchronization with gray encoding.** If the data has a natural gray-code representation (e.g., a counter value), I could encode the data as gray code before crossing. This allows each bit to change independently without multi-bit CDC issues, since only one bit changes at a time. The destination can then safely sample the gray-coded value with simple two-flop synchronizers per bit.

For the general case with frequently changing arbitrary data, I'd lean toward the asynchronous FIFO. The latency is predictable and minimal compared to handshake approaches, and it handles continuous data flow without stalling the source. The critical implementation details are:
- Using gray-coded pointers to avoid multi-bit synchronization issues
- Properly synchronizing the pointers with two (or three, for higher MTBF) flip-flop synchronizers
- Ensuring the FIFO depth is sized correctly for the worst-case burst scenario, not just the average rate
- Simulating with realistic clock frequency ratios and jitter

If the data changes less frequently but must be captured reliably, a simpler approach would be to use a "data valid" pulse synchronized to the destination domain, combined with holding the data stable until the destination confirms capture.

**Possible follow-ups:**
- How would you determine the required FIFO depth for your specific application?
- What happens if the FIFO becomes full — how would you handle backpressure?

---

## Q3: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** This is a demanding PDN requirement — 20A at 0.85V with 1A/ns slew rate means the core rail must handle very fast transient currents while maintaining tight voltage regulation. My approach would span from the VRM through the PCB to the FPGA package:

**VRM selection and placement:** I'd start with a multi-phase buck converter capable of sourcing 20A+ with fast transient response. The VRM's control loop bandwidth is critical — I'd look for converters with high switching frequency (1-2 MHz or higher) and possibly use multiple phases to reduce output voltage ripple and improve transient response. The VRM should be placed as close to the FPGA as physically practical to minimize the impedance of the power path.

**Bulk and ceramic decoupling:** I'd use a combination of bulk capacitors (electrolytic or polymer tantalum) for energy storage during longer transients, and ceramic capacitors (X7R or better, in small packages like 0402 or 0201) for high-frequency decoupling. The bulk capacitors handle the initial voltage droop during a transient, while the ceramics provide low impedance at higher frequencies. The total capacitance needs to be sized so that the voltage droop during a worst-case transient stays within the ±3% window.

**PCB stack-up and plane design:** The core voltage plane needs to be a dedicated layer (or layers) with minimal inductance. I'd use a thin dielectric between the power and ground planes (e.g., 2-4 mil core) to maximize plane capacitance. The power plane should be solid — no splits or narrow channels — and vias connecting the plane to the FPGA and decoupling capacitors should be numerous and placed close to the FPGA power pins.

**Decoupling capacitor placement:** This is where the 1A/ns slew rate really matters. The high-frequency decoupling capacitors must be placed as close to the FPGA power pins as possible — ideally on the same side of the board, within a few hundred mils of the pins. The mounting inductance of the capacitor (via inductance, pad inductance) is often the limiting factor. I'd use multiple vias per capacitor pad to reduce inductance. For the fastest transients, I might consider capacitors on the bottom side of the board directly under the FPGA, or even embedded capacitance in the PCB.

**Simulation and verification:** Before manufacturing, I'd perform PDN impedance analysis using tools like SIwave or PowerSI. The target impedance is calculated as Z_target = (V_nominal × tolerance) / I_transient = (0.85V × 0.03) / 20A = approximately 1.3 mΩ. I'd simulate the PDN impedance across frequency (from DC to several hundred MHz) to ensure it stays below this target. After the board is built, I'd verify with a high-bandwidth oscilloscope (1 GHz+) measuring directly at the FPGA power pins using a coaxial probe or a dedicated measurement point.

**Possible follow-ups:**
- How would you calculate the target impedance for this rail, and what frequency range would you need to cover?
- What trade-offs would you consider between using more ceramic capacitance versus improving the VRM transient response?

---

## Q4: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a 64-tap FIR filter, and output the filtered result without any dropped samples, while also meeting timing at the target clock frequency?

**Answer:** The fundamental challenge here is that 500 MSPS exceeds the typical FPGA fabric clock rate, so I need to use parallel processing techniques. My approach would be:

**Determine the fabric clock rate and parallelism factor.** If the FPGA fabric can run at 250 MHz, I'd need 2 parallel samples per clock cycle. If it runs at 125 MHz, I'd need 4 parallel samples. The choice depends on the specific FPGA family and speed grade. Let me walk through the 250 MHz / 2-parallel case as an example.

**Architecture selection:** For a 64-tap FIR at 500 MSPS with 2 parallel samples per clock, I have several options:

*Option A: Time-multiplexed single MAC.* One multiplier-accumulator running at 250 MHz processes 2 samples per clock. Each output sample requires 64 MAC operations, so 2 outputs require 128 MACs per 250 MHz clock cycle. This doesn't work — the MAC would need to run at 128 × 250 MHz = 32 GHz.

*Option B: Polyphase decomposition with parallel MACs.* Decompose the 64-tap filter into 2 polyphase sub-filters, each with 32 taps. Each sub-filter processes one of the 2 parallel input samples. Each sub-filter needs 32 MACs per output sample, and since we produce 2 outputs per clock, we need 64 MACs total per clock cycle. At 250 MHz, this means 64 multipliers running in parallel. This is feasible in a modern FPGA with hundreds of DSP slices.

*Option C: Fully parallel with register-based delay line.* For 2 parallel samples, I'd use a delay line that shifts 2 samples per clock. Each output is computed as the sum of 64 products (for sample at even positions) or 64 different products (for odd positions, using the shifted coefficients). This requires 128 multipliers total (64 for each output), but each multiplier runs at 250 MHz.

I'd choose Option B (polyphase) as it's more efficient. The key insight is that the filter coefficients are partitioned: even-indexed coefficients go to one sub-filter, odd-indexed to the other. Each sub-filter operates on the appropriate phase of the input.

**Resource and timing optimization:** I'd pipeline the multiplier chains — typically 3-4 pipeline stages for a 64-tap filter at 250 MHz. The adder tree would be balanced and pipelined as well. I'd use the FPGA's dedicated DSP slices (DSP48E1/E2 or similar) which have built-in pipelining and can run at high clock rates.

**Verification:** I'd verify the implementation by comparing the FPGA output against a bit-exact C model of the filter. I'd test with impulse, step, and random inputs, and verify the frequency response matches the expected filter characteristics.

**Possible follow-ups:**
- How would you handle the case where the filter needs to be reprogrammable (variable coefficients)?
- What if the sample rate increases to 1 GSPS — how would your architecture change?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical concern and the junior engineer's development. My approach would be:

**First, acknowledge what's correct in their reasoning.** The engineer is right that average rates matter and that the memory controller does have a write buffer. Starting from a place of validation keeps the conversation collaborative rather than confrontational.

**Then, walk through the burst scenario concretely.** I'd ask the engineer to walk me through the worst-case burst: what's the maximum number of consecutive ADC samples that can arrive back-to-back? What's the memory controller's sustainable write rate when the DRAM is busy with refresh cycles? What happens when a read request from the host processor is interleaved with the write stream? The memory controller's write buffer absorbs some burstiness, but it's shared with read traffic and has its own finite depth. If the ADC burst fills the FIFO faster than the memory controller can drain it (accounting for refresh and read/write turnaround overhead), data will be lost.

**Quantify the problem together.** I'd suggest we work through the math: ADC burst length × sample width versus memory controller sustainable bandwidth (not peak, but sustainable including refresh overhead and bus turnaround). If the FIFO depth is insufficient, the failure mode is dropped samples — which in a data acquisition system means corrupted data that may not be immediately detectable.

**Discuss the cost of the fix.** Adding FIFO depth costs block RAM resources but is relatively cheap. The alternative — adding backpressure to the ADC or using a more complex flow control scheme — has system-level implications. In most cases, a deeper FIFO is the simpler and more robust solution.

**Use this as a teaching moment.** I'd explain that in high-speed data paths, average-rate analysis is necessary but not sufficient. You must always analyze the worst-case burst behavior, including all sources of variability (DRAM refresh, arbitration with other masters, clock frequency drift). This is a fundamental principle in designing reliable data paths.

**If the engineer still disagrees,** I'd suggest we prototype the scenario in simulation — model the ADC burst pattern, the memory controller behavior, and the FIFO depth, and see if data is lost. Simulation evidence is more convincing than either of us being assertive about our position. If the simulation shows the FIFO is adequate, I'd accept that with the caveat that we document the analysis. If it shows overflow, we have concrete evidence for the fix.

**Possible follow-ups:**
- How would you handle the situation if the engineer's simulation shows the FIFO is adequate, but you still have concerns about real-world behavior?
- What documentation or analysis would you expect to see in the design review for a data path like this?