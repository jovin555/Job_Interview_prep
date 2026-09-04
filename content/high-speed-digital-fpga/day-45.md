# high-speed-digital-fpga — Day 45

## Q1: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design's internal state machine appears to be stuck in an illegal state only when a specific external input sequence occurs, and the issue is not reproducible in RTL simulation?

**Answer:** This is a classic case where the problem likely lives at the boundary between what RTL simulation models and what actually happens in hardware. My first step would be to resist the urge to start modifying the FSM code immediately, and instead focus on gathering more information about the actual hardware behavior.

The fact that it's not reproducible in RTL simulation is a strong hint. I'd start by asking: what does the simulation model not capture? The usual suspects are timing effects, metastability, glitches on asynchronous inputs, or unmodeled delays through combinational paths. If the illegal state is entered only after a specific input sequence, I'd look carefully at whether that sequence involves signals that arrive asynchronously or nearly simultaneously — a race condition between two inputs, or an input that changes close to a clock edge, could cause the FSM to see a different sequence than intended.

I would instrument the design with an internal logic analyzer (ILA) core to capture the FSM state, the relevant inputs, and the state transition trigger signals over a window around the failure. This lets me see the actual sequence of states and inputs in hardware, rather than guessing. I'd also check whether the FSM has a safe recovery mechanism — if it's stuck in an illegal state, does it have a watchdog or reset path, or does it hang indefinitely?

If the ILA capture shows the FSM receiving an unexpected input combination, I'd then look at the timing of those inputs. I'd check the timing report for the paths feeding the FSM's next-state logic — is there a marginal setup or hold path that only fails under specific conditions (temperature, voltage, or data-dependent switching noise)? I'd also examine whether the inputs to the FSM are properly synchronized if they come from another clock domain.

If the issue turns out to be a missing synchronization or a race condition, the fix would be in the RTL — adding proper synchronizers, or restructuring the FSM to be more robust. If it's a timing path issue, the fix might be in constraints or logic restructuring. The key is to use the hardware debug capability to narrow down the root cause before changing code.

**Possible follow-ups:**
- How would you design the FSM to be more robust against illegal states in the first place, rather than just debugging this after the fact?
- What specific information would you want to capture with the logic analyzer to distinguish between a timing issue versus a logic issue?

---

## Q2: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For a multi-bit bus crossing between truly asynchronous clock domains with frequent data changes, the fundamental constraint is that you cannot guarantee all bits arrive at the destination simultaneously without some form of synchronization handshake or buffering. The standard approaches are: a handshake protocol (request/acknowledge), an asynchronous FIFO, or a MUX-based synchronization with gray-code encoding where applicable.

For minimizing latency while ensuring integrity, an asynchronous FIFO is typically the best choice for continuous or frequent data transfer. The FIFO uses gray-code pointers that are synchronized across the clock domains — since only one bit changes at a time in gray code, the synchronized pointers are guaranteed to be either the old or new value, never a corrupted intermediate value. The data itself is written into the FIFO in the source domain and read out in the destination domain, so it never needs to cross domains directly.

The key design considerations are: FIFO depth (must accommodate worst-case burst size plus the synchronization latency of the pointers), the synchronizer stages on the pointers (typically two flip-flops per bit to reduce metastability probability to an acceptable level), and the empty/full flag generation logic, which must be carefully designed to avoid false flags that would either drop data or read stale data.

If the data is not continuous but comes in bursts with idle periods, a simpler handshake approach might work with lower latency for the first word, at the cost of throughput. The trade-off is between per-transfer latency (handshake is better for sparse transfers) versus sustained throughput (FIFO is better for continuous data).

For the specific case of frequent changes, I would also consider whether the data needs to be coherent as a multi-bit word. If the destination only needs to see a consistent snapshot, the FIFO approach handles this naturally. If the data is a counter or sequence number, gray-code encoding alone might suffice. But for arbitrary multi-bit data, the FIFO is the robust choice.

**Possible follow-ups:**
- How would you determine the required FIFO depth for your specific application?
- What happens if the FIFO becomes full — how would you handle backpressure or data loss in your design?

---

## Q3: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** The core rail is the most challenging because of the combination of low voltage, high current, and fast transient response. A ±3% tolerance on 0.85V means the voltage must stay between approximately 0.825V and 0.875V — that's only a 25mV window on either side of nominal. With 20A transients at 1A/ns, the PDN impedance must be extremely low across a wide frequency range.

My approach would be to work from the target impedance backwards. The maximum allowable PDN impedance is approximately ΔV/ΔI. For a 25mV allowable droop and a 20A transient, that's about 1.25 milliohms. But the real constraint is frequency-dependent — the PDN needs to maintain this low impedance from DC up to the frequency where the on-die decoupling and package capacitance take over.

The design would have several layers of decoupling, each addressing a different frequency range:
- On-die capacitance and the FPGA package itself handle the highest frequencies (above ~100 MHz)
- A carefully chosen array of high-frequency ceramic capacitors (0402 or smaller, low ESL) placed as close as possible to the FPGA power pins, on the bottom side of the board if space allows, to handle the 1-100 MHz range
- Bulk capacitors (tantalum or ceramic in larger packages) for the 100 kHz to 1 MHz range
- The voltage regulator module (VRM) itself handles DC to roughly 100 kHz, and its loop bandwidth and output capacitance determine the response at these lower frequencies

For the layout, I would use a dedicated power plane for the core rail with minimal vias between the plane and the FPGA pins, and the decoupling capacitors must be connected with short, wide traces or directly to vias that tie into the plane. The via inductance is often the limiting factor — a typical via has about 1nH of inductance, and at 1A/ns that translates to 1V of drop per via, so you need many parallel vias to reduce the effective inductance.

I would also consider the VRM choice carefully. A multi-phase buck converter with a high control-loop bandwidth is essential for the core rail. The output capacitor bank of the VRM needs to be sized to handle the transient until the loop can respond.

To verify the design, I would perform a PDN simulation using SPICE or a dedicated PDN analysis tool, modeling the plane impedances, via inductances, capacitor ESL/ESR, and the VRM output impedance. I would also do a transient simulation with a current step profile that matches the FPGA's worst-case switching pattern. On the bench, I would verify with a high-bandwidth oscilloscope probe at the FPGA core voltage pins, measuring the voltage during controlled switching activity.

**Possible follow-ups:**
- How would you determine the number and value of decoupling capacitors needed, and how would you distribute them across the board?
- What are the trade-offs between using a single large VRM versus multiple smaller VRMs for different rail groups?

---

## Q4: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a 64-tap FIR filter, and output the filtered result without any dropped samples, while also meeting timing at the target clock frequency?

**Answer:** The first thing to recognize is that 500 MSPS is likely faster than the FPGA fabric clock can run — most FPGAs top out around 300-500 MHz for general logic, and even at the high end, meeting timing with a 64-tap filter would be very challenging. So the fundamental approach is to use parallel processing or time-division multiplexing to reduce the effective clock rate.

The standard technique is to use multiple parallel filter chains, each processing a subset of the samples. For example, if the fabric clock is 250 MHz, I would use two parallel paths, each processing every other sample. Each path would contain a 64-tap FIR filter, but the taps would be split — the even samples path would use the even-indexed coefficients, and the odd samples path would use the odd-indexed coefficients. This is called polyphase decomposition.

The key challenge with polyphase decomposition is that the filter has memory — each output sample depends on 64 consecutive input samples. With two parallel paths, each path needs access to samples from the other path's history. This is handled by having each path maintain its own delay line, but the delay line must be fed with the correct samples. In practice, you'd have a shift register that captures the input at 500 MSPS (using the I/O serializers), and the parallel paths read from this shared delay line.

For the implementation, I would use DSP slices for the multiply-accumulate operations. A 64-tap filter with two parallel paths means 64 MACs per output pair, but each DSP slice can typically do one MAC per clock cycle. At 250 MHz with two paths, you have 4 clock cycles per output pair (2 samples per 4 cycles = 500 MSPS aggregate), so you need 64/4 = 16 DSP slices per path, or 32 total. This is well within the resources of most mid-range FPGAs.

The critical design considerations are: managing the delay line so each path gets the correct 64 samples, ensuring the coefficient storage is properly aligned, and handling the output summation correctly. I would also pipeline the adder tree to meet timing — a 64-tap filter has a natural adder tree depth of 6 levels, and pipelining each level would add latency but improve timing.

For verification, I would create a testbench that generates a known input signal (impulse, step, sine wave) and compares the FPGA output against a bit-exact C model of the filter. I would also verify that no samples are dropped by checking for a continuous output stream with the correct sample count over a long test duration.

**Possible follow-ups:**
- How would you handle the case where the filter coefficients need to be updated dynamically without interrupting the data flow?
- What are the trade-offs between using more parallel paths at a lower clock rate versus fewer paths at a higher clock rate?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where the engineer has a reasonable-sounding argument, but it's based on an assumption that hasn't been verified — that the memory controller's write buffer will always absorb the bursts. My approach would be to guide the engineer toward validating that assumption rather than simply overriding their decision.

First, I would acknowledge the validity of their point: if the average write rate is indeed well below the sustainable read rate, and if the memory controller's write buffer is deep enough to handle the worst-case burst, then a shallow FIFO might be sufficient. The problem is that "if" — we need to verify both conditions with data, not assumptions.

I would ask the engineer to walk through the worst-case burst scenario quantitatively. What is the maximum burst size the ADC can produce? What is the memory controller's sustainable write rate during a burst — not the peak rate, but the rate after accounting for DRAM refresh cycles, bank conflicts, and read/write turnaround overhead? What is the memory controller's write buffer depth, and does it have any internal backpressure mechanisms? If the ADC burst fills both the FIFO and the memory controller's write buffer simultaneously, what happens — does the design drop data, or does it have a flow-control mechanism?

I would also ask about the read side of the memory. If the memory controller is also servicing read requests from other parts of the system, the sustainable write bandwidth could be significantly lower than the theoretical peak. A burst of ADC data arriving while the memory is busy with reads could cause the write buffer to fill up faster than expected.

Rather than making the decision unilaterally, I would suggest we work through the analysis together. I might propose adding a small amount of margin to the FIFO depth as a safety factor, or adding a watermark interrupt that could trigger a reduction in ADC capture rate if the FIFO approaches full. I would also suggest running a simulation with worst-case burst patterns to validate the analysis.

The goal is not to prove the engineer wrong, but to ensure the design is robust under all specified operating conditions. If the analysis shows the current design is adequate, I'd be happy to proceed. If not, we'd need to increase the FIFO depth or add flow control. Either way, the decision should be based on data, not assumptions.

**Possible follow-ups:**
- How would you handle the situation if the engineer's analysis shows the FIFO is adequate, but you still have concerns about unmodeled behavior (e.g., DRAM refresh timing)?
- What documentation or verification would you require before signing off on the design?