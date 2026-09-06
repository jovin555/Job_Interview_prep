# high-speed-digital-fpga — Day 47

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For asynchronous multi-bit data transfer with frequent changes and low-latency requirements, I'd first evaluate whether the data is truly continuous or can tolerate occasional stalls. If the data is continuous, an asynchronous FIFO is the standard solution — it handles the full handshaking and buffering needed for reliable multi-bit transfer. The key design decisions are FIFO depth and the synchronization strategy for the read/write pointers.

For the pointer synchronization, I'd use Gray-code encoding so that only one bit changes at a time when the pointer increments, making it safe to synchronize through a two-flop synchronizer without multi-bit metastability issues. The FIFO depth needs to account for the maximum burst size plus the synchronization latency — typically at least 4-8 entries for the pointer sync delay alone, plus any burst absorption needed.

If the data changes frequently but has a valid/ready handshake and can tolerate backpressure, a simpler approach is to use a handshake-based transfer with a small FIFO or even just a register stage with proper synchronization of the control signals. The trade-off is that handshaking adds latency per transfer, but it's simpler and uses fewer resources.

For minimal latency specifically, I'd consider whether the clocks have any known relationship. If they're truly asynchronous, there's a fundamental minimum latency of two destination-clock cycles for the control signal synchronization. If the data path itself is the critical latency element, I might consider source-synchronous transfer where the source sends data with a strobe, and the destination uses the strobe to capture directly — but this only works if the destination can tolerate the timing relationship.

**Possible follow-ups:** How would you determine the required FIFO depth for a specific burst profile? What happens if the FIFO becomes full — how would you handle backpressure or data loss?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully (DONE pin goes high), but the design's internal state machine appears to be stuck in an illegal state only when a specific external input sequence occurs, and the issue is not reproducible in RTL simulation?

**Answer:** This is a classic case where the problem likely exists in the RTL but the simulation stimulus isn't capturing the real-world conditions. I'd approach this systematically:

First, I'd try to capture the actual behavior using the FPGA's internal logic analyzer (e.g., ChipScope or SignalTap) to trace the state machine's state transitions and the relevant input signals around the failure. This tells me whether the state machine is truly in an illegal state or if it's stuck in a legal state that's not progressing. I'd trigger on the specific input sequence that causes the failure.

Second, I'd examine the state machine encoding and the input synchronization. A common cause of "illegal state" behavior is a state register being corrupted by a metastability event — if an external input isn't properly synchronized before entering the state machine's combinational logic, a metastable value can resolve to an unexpected logic level and push the FSM into an unreachable state. I'd verify that all external inputs are synchronized with at least two flip-flops in the destination clock domain.

Third, I'd look for missing default cases or incomplete case statements in the RTL. If the synthesis tool optimizes away the default state or the "when others" clause, the FSM may not have defined behavior for illegal states. I'd check the synthesis report for any warnings about incomplete case statements or inferred latches.

Fourth, I'd consider asynchronous resets and reset removal. If the reset deassertion isn't synchronized, the FSM could start from an undefined state. I'd verify the reset architecture.

Finally, I'd reproduce the issue in simulation by creating a testbench that models the actual input timing — including realistic input jitter, asynchronous assertion relative to the clock, and any glitches that might occur on the PCB. Often the issue becomes reproducible once the simulation includes realistic input timing rather than ideal aligned inputs.

**Possible follow-ups:** How would you add fault tolerance to the state machine to recover from illegal states in production? What specific simulation techniques would you use to try to reproduce the issue?

---

## Q3: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** The ±3% tolerance on a 0.85V rail means the voltage must stay between approximately 0.825V and 0.875V — that's only 25mV of total budget. With 20A transients at 1A/ns, this is a demanding PDN design that requires careful attention to every impedance element in the path.

I'd start by defining the target impedance. For a 25mV droop at 20A, the maximum allowable impedance is roughly 1.25mΩ across the frequency range of interest. The frequency range matters — the 1A/ns slew rate means significant energy up to tens or hundreds of MHz, so the PDN must maintain low impedance well into that range.

The design approach would be layered:

**Voltage regulator selection:** A multi-phase buck converter with fast transient response is essential. I'd look for a regulator with a high control-loop bandwidth and consider adding a "transient assist" feature or an active droop response. The regulator's output capacitance and loop response determine the low-frequency behavior.

**Bulk capacitance:** I'd place bulk capacitors (e.g., aluminum polymer or ceramic in large case sizes) near the regulator output to handle the mid-frequency energy. The total bulk capacitance needs to supply the energy for the transient duration before the regulator loop responds.

**High-frequency decoupling:** This is where the FPGA's transient current demand gets challenging. I'd use a combination of ceramic capacitors in small case sizes (0402 or smaller) distributed across the FPGA's power pins. The key is minimizing the mounting inductance — via placement, pad size, and the connection to the power and ground planes all matter. I'd work with the FPGA vendor's power integrity guidelines and possibly use their decoupling calculator.

**PCB stack-up and plane design:** The power and ground planes themselves contribute inductance. I'd use a thin dielectric between the core power plane and its adjacent ground plane (e.g., 2-4 mil prepreg) to maximize plane capacitance and minimize loop inductance. The FPGA's core power pins should connect to the plane with multiple vias — typically one via per power pin pair, with the via connecting directly to the plane layer.

**Simulation and verification:** I'd perform PDN impedance analysis using SPICE or a dedicated power integrity tool. The goal is to keep the impedance below the target across frequency. I'd also run time-domain transient simulations with a current profile that models the FPGA's worst-case switching pattern. On the bench, I'd verify with a high-bandwidth oscilloscope probe at the FPGA's power pins, measuring the transient response during actual operation.

**Possible follow-ups:** How would you choose between placing more bulk capacitance versus improving the regulator's transient response? What measurement techniques would you use to verify the PDN impedance on a physical board?

---

## Q4: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a 64-tap FIR filter, and output the filtered result without any dropped samples, while also meeting timing at the target clock frequency?

**Answer:** The fundamental challenge here is that 500 MSPS exceeds what most FPGA fabrics can handle directly — typical fabric clocks max out around 300-500 MHz depending on the device. So the first decision is the architecture: whether to use a single clock domain at 500 MHz (if the FPGA supports it) or to use a parallel processing approach with multiple samples per clock cycle.

Assuming the fabric clock is limited to 250 MHz or lower, I'd use a time-division multiplexed (TDM) or parallel-serial approach. The most common technique is to process multiple samples per clock cycle. For example, at 250 MHz, I'd process two samples per cycle; at 125 MHz, four samples per cycle.

For a 64-tap FIR filter with N samples per cycle, I'd need N parallel filter chains, each computing a partial result. The key insight is that the filter can be decomposed: each output sample y[n] depends on the last 64 input samples. When processing N samples per cycle, I need to compute N outputs simultaneously, and each output requires a window of 64 input samples. The input samples shift by N positions each cycle, so the filter taps for each output are offset.

The resource implications are significant. A direct-form FIR with 64 taps and 16-bit data would require 64 multipliers per output sample. With N=2, that's 128 multipliers; with N=4, that's 256 multipliers. This may exceed the DSP slice resources, so I'd consider alternatives:

**Polyphase decomposition:** If the filter is decimating, polyphase decomposition reduces the multiplier count. But for a straight FIR with no decimation, this doesn't help directly.

**Distributed arithmetic (DA):** For fixed coefficients, DA can replace multipliers with look-up tables and adders. This trades DSP slices for block RAM and LUT resources.

**Multiplier sharing:** If the coefficients are symmetric (linear phase FIR), I can share multipliers between symmetric taps by summing the symmetric input pairs first.

**Pipeline and retiming:** Regardless of the architecture, I'd pipeline the adder tree to meet timing. A 64-tap filter requires a 6-level adder tree (64→32→16→8→4→2→1), and each level needs a pipeline register to keep the clock frequency high.

For verification, I'd create a bit-exact model in C or Python, generate test vectors with known input patterns (impulse, step, sine waves at various frequencies), and compare the FPGA output against the reference model. I'd also verify the timing closure with proper constraints, including the multi-cycle paths inherent in the parallel architecture.

**Possible follow-ups:** How would the approach change if the filter coefficients are programmable rather than fixed? How would you handle the case where the input data arrives as a continuous stream with no gaps — how do you manage the input buffering and alignment?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical concern and the engineer's reasoning process. The core issue isn't just the FIFO depth — it's that the engineer is relying on average rates rather than worst-case burst behavior, which is a fundamental misunderstanding of how asynchronous data paths fail.

I'd start by acknowledging the engineer's point — the memory controller's write buffer does provide some burst absorption, and the average-rate analysis is a reasonable starting point. Then I'd walk through the worst-case scenario together: what happens when the ADC produces a maximum-length burst at full rate, and the memory controller is simultaneously handling a refresh cycle or a read operation that delays writes? The memory controller's write buffer has its own finite depth, and if both the FIFO and the write buffer fill simultaneously, data will be lost.

Rather than just asserting my concern, I'd suggest we work through the math together. I'd ask the engineer to identify: (1) the maximum burst size and duration from the ADC, (2) the memory controller's sustainable write bandwidth including refresh overhead and bank conflicts, and (3) the write buffer depth in the memory controller. With those numbers, we can calculate whether the combined buffering (FIFO + write buffer) is sufficient for the worst case.

If the analysis shows the buffering is insufficient, I'd discuss options: increasing the FIFO depth, adding flow control so the ADC data path can pause, or using a larger FIFO with a watermark interrupt to throttle the ADC before overflow. If the analysis shows it's sufficient, I'd still recommend adding margin and documenting the analysis — but I'd also suggest adding a FIFO overflow flag as a diagnostic, even if we don't expect it to trigger.

The key teaching point is that in real-time data acquisition, you design for the worst case, not the average. I'd frame this as a learning opportunity about burst analysis and the importance of understanding the full data path — not just the FIFO, but everything downstream that could cause backpressure.

**Possible follow-ups:** How would you handle the situation if the engineer's analysis shows the FIFO is adequate, but you still have concerns about a corner case they haven't considered? How would you document the burst analysis so it's reviewable by other engineers?