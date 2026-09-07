# high-speed-digital-fpga — Day 48

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For asynchronous clock domains with frequently changing multi-bit data and low-latency requirements, I'd first characterize the actual relationship between the clocks. If they're truly asynchronous with no known phase relationship, an asynchronous FIFO is the standard solution — it handles the full handshaking and buffering needed for continuous data flow. The key design decisions are FIFO depth (based on worst-case burst size and read/write rate mismatch) and the synchronization of the read/write pointers across domains.

For pointer synchronization, I'd use Gray-code encoding so only one bit changes at a time, then double-flop synchronize the pointers. This avoids multi-bit metastability issues. The FIFO's almost-empty/almost-full flags provide backpressure signaling with bounded latency.

If the data transfers are more sporadic — like register writes or configuration updates — I'd consider a handshake-based approach (request/acknowledge) with a holding register, accepting the added latency for the guarantee of coherent data delivery. The trade-off is always between latency and throughput: a FIFO gives continuous flow with predictable latency, while handshaking is simpler but slower.

For minimizing latency specifically, I'd look at the FIFO's read-side latency — using first-word fall-through mode can reduce the read latency to near zero, at the cost of slightly more complex empty detection logic.

**Possible follow-ups:**
- How would you determine the minimum safe FIFO depth for your specific application?
- What happens if the write clock is much faster than the read clock — how does that change your approach?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully (DONE pin goes high), but the design's internal state machine appears to be stuck in an illegal state only when a specific external input sequence occurs, and the issue is not reproducible in RTL simulation?

**Answer:** This is a classic case where the design works in simulation but fails in hardware under specific conditions. I'd approach this systematically:

First, I'd verify that the state machine's reset behavior is correct — check that the reset is properly synchronized and that all state registers are actually being reset to a known state. An unsynchronized reset can leave the FSM in an undefined state that simulation might not catch.

Next, I'd examine the specific input sequence that triggers the failure. The fact that it's not reproducible in RTL simulation suggests either: (1) the simulation stimulus doesn't accurately model the real-world input timing (e.g., input setup/hold times, metastability on asynchronous inputs), or (2) there's a CDC issue where an input signal is crossing clock domains without proper synchronization, causing the FSM to see a glitch or intermediate value that never appears in simulation.

I'd add an on-chip logic analyzer (like an ILA core) to capture the FSM state and input signals around the failure point. This gives visibility into what's actually happening in the hardware. I'd also check whether the inputs to the FSM are properly synchronized — if any input comes from an asynchronous source, it needs at least a double-flop synchronizer before entering the FSM logic.

Another angle: check the FSM encoding. If it's using one-hot encoding, verify that the illegal state detection logic (if any) is working correctly. If the FSM has no illegal-state recovery, I'd add a watchdog or state-recovery mechanism that forces the FSM back to a known state after a timeout or when an illegal state is detected.

Finally, I'd review the timing constraints — if the FSM logic is marginally meeting timing, the specific input sequence might create a path that violates setup/hold under certain voltage/temperature conditions. Running the design at a slower clock or checking timing margins would help isolate this.

**Possible follow-ups:**
- How would you go about adding illegal-state recovery to an FSM without affecting normal operation?
- What specific simulation techniques would you use to try to reproduce the issue after adding instrumentation?

---

## Q3: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** The core rail is the most challenging here — 0.85V with 20A transients and 1A/ns slew rate means the PDN impedance must be extremely low across a wide frequency range. The target impedance calculation is straightforward: ΔV/ΔI = (0.85V × 3%) / 20A ≈ 1.3 mΩ. This target must be maintained from DC up to the frequency where the on-die decoupling takes over.

My approach would be layered:

**Voltage regulator selection:** A multi-phase buck converter with fast transient response is essential. I'd look for regulators with adaptive voltage positioning (AVP) which allows the output to droop slightly under load and recover, effectively widening the allowable transient window. The regulator's bandwidth and output capacitance requirements need to be co-designed with the board-level decoupling.

**Bulk capacitance:** I'd place bulk capacitors (e.g., aluminum polymer or ceramic in large case sizes) near the FPGA to handle the mid-frequency transient energy. The number and value depend on the regulator's response time — the bulk caps must supply current until the regulator can respond.

**High-frequency decoupling:** A matrix of small-value ceramic capacitors (0402 or smaller) distributed across the FPGA's power pins, close to the BGA vias. The key is minimizing the loop inductance — each capacitor's mounting inductance and the via inductance to the power plane determine the effective frequency range. I'd use a mix of values (e.g., 100nF, 10nF, 1nF) to create a low-impedance profile across a broad frequency range.

**Power plane design:** The core voltage plane needs to be a solid, low-inductance plane pair (power and ground) with minimal splits. The plane capacitance itself provides some high-frequency decoupling — thinning the dielectric between the core power and ground planes increases this capacitance.

**Verification:** I'd simulate the PDN impedance using SPICE or a dedicated PDN analysis tool, modeling the regulator output impedance, capacitor ESL/ESR, and plane inductance. The target is to keep the impedance below 1.3 mΩ up to the frequency where on-die capacitance takes over. I'd also perform transient simulations with a current step load to verify the voltage stays within the ±3% window.

**Possible follow-ups:**
- How would you decide between using more bulk capacitance versus a regulator with higher bandwidth?
- What role does the FPGA's on-die decoupling play, and how do you account for it in your design?

---

## Q4: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a 64-tap FIR filter, and output the filtered result without any dropped samples, while also meeting timing at the target clock frequency?

**Answer:** The fundamental challenge here is that 500 MSPS exceeds what most FPGA fabrics can handle directly — the maximum clock frequency in fabric is typically 300-400 MHz for complex logic. So the first decision is the architecture: I'd use a parallel processing approach where multiple samples are processed per clock cycle.

If the fabric clock is 250 MHz, I'd process two samples per clock cycle (2:1 time demultiplexing). The 64-tap FIR filter would be split into two parallel filter chains, each handling alternating samples. Each chain computes every other output sample, which requires splitting the filter coefficients appropriately — the even and odd output samples each need their own 64-tap filter operating on the appropriate input samples.

The key insight is that for a 64-tap FIR at 2:1 parallelism, each parallel filter still needs all 64 taps — but the input data alignment differs. The even-output filter processes samples [0, 2, 4, ...] with coefficients [h0, h2, h4, ...] and samples [1, 3, 5, ...] with coefficients [h1, h3, h5, ...], effectively creating two interleaved sub-filters. This doubles the resource usage but halves the clock rate requirement.

For the filter implementation itself, I'd use the FPGA's DSP slices in a systolic or semi-systolic architecture. With 64 taps, I'd need to consider the DSP slice count — if the device has limited DSP resources, I might use a combination of DSP slices and block RAM-based distributed arithmetic, or implement the filter using FFT-based fast convolution if the filter is long enough to justify the overhead.

The critical path through the filter needs careful pipelining. I'd add pipeline registers between the multiply and accumulate stages to break up the combinational path. The DSP slices in modern FPGAs have built-in registers that can be used for this purpose without additional fabric resources.

For verification, I'd simulate the parallel architecture against a bit-exact reference model of the original filter to ensure the parallel implementation produces identical results. I'd also verify that the input data alignment and output collection logic correctly reconstructs the sample stream.

**Possible follow-ups:**
- How would you handle the case where the filter length isn't evenly divisible by the parallelism factor?
- What if the device doesn't have enough DSP slices — how would you trade off between resource usage and throughput?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical concern and the engineer's reasoning process. The core issue isn't just the FIFO depth — it's that the engineer is relying on average rates rather than worst-case burst behavior, which is a fundamental misunderstanding of how real-time data systems fail.

First, I'd acknowledge the engineer's point about the memory controller's write buffer — it does provide some burst absorption. But I'd ask them to walk me through the worst-case scenario: what happens when the ADC produces its maximum burst size while the memory controller is simultaneously handling a refresh cycle or a read operation? The memory controller's write buffer has its own finite depth, and if both the FIFO and the write buffer fill up simultaneously, data will be lost.

I'd guide the engineer through the analysis rather than just dictating the answer. I'd ask: "What's the maximum burst size the ADC can produce? What's the memory controller's sustainable write rate during a refresh? What's the write buffer depth? Let's work through the math together to see if 64 words is sufficient." This approach helps the engineer develop the analytical skills to catch these issues themselves in the future.

If the analysis shows the FIFO is indeed too shallow, I'd discuss the options: increasing the FIFO depth, adding a mechanism to throttle or pause the ADC during memory controller congestion, or using a larger buffer with flow control back to the ADC. The right solution depends on whether the ADC can tolerate being paused and what the system-level latency requirements are.

I'd also use this as a teaching moment about design margins — in real-time systems, you design for worst-case behavior, not average behavior. The cost of a slightly larger FIFO is trivial compared to the cost of intermittent data loss that's nearly impossible to debug in the field.

**Possible follow-ups:**
- How would you help the engineer develop the habit of thinking about worst-case scenarios in future designs?
- What if the engineer's analysis shows that 64 words is actually sufficient — how would you handle being wrong in your initial assessment?