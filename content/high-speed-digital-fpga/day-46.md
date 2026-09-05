# high-speed-digital-fpga — Day 46

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For asynchronous, frequently-changing multi-bit data with minimal latency, I'd first characterize the actual relationship between the clocks. If they're truly asynchronous with no frequency relationship, the safest approach is an asynchronous FIFO with gray-coded pointers. The key design considerations would be:

1. **FIFO depth calculation** — I'd analyze the worst-case burst pattern: how much data can arrive in the source domain before the destination can drain it. The depth must accommodate the maximum instantaneous difference between write and read rates, not just the average.

2. **Pointer synchronization** — Write and read pointers must be synchronized across domains using multi-flop synchronizers. Gray-coding the pointers ensures only one bit changes at a time, so even if a synchronizer samples during a transition, the resulting value is either the old or new pointer — never a corrupted intermediate value.

3. **Full/empty generation** — The classic approach is to compare gray-coded pointers in the respective domains: generate "full" in the write domain by comparing the synchronized read pointer against the write pointer, and "empty" in the read domain by comparing the synchronized write pointer against the read pointer. This adds latency to the flag generation but ensures correctness.

4. **Latency optimization** — If the FIFO adds too much latency, I'd consider a handshake-based approach with data valid/accept signaling, but only if the data rate is low enough that the handshake overhead is acceptable. For high-throughput continuous data, the FIFO is usually the right choice.

5. **Verification** — I'd run extensive simulation with randomized clock phase offsets and frequency drift, plus formal CDC verification tools if available, to prove there are no metastability propagation paths.

**Possible follow-ups:** How would you size the FIFO depth if the write side can burst 64 words at 200 MHz but the read side consumes at 150 MHz continuously? What happens if the FIFO becomes full — how would you handle backpressure?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully (DONE pin goes high), but the design's internal state machine appears to be stuck in an illegal state only when a specific external input sequence occurs, and the issue is not reproducible in RTL simulation?

**Answer:** This is a classic "works in simulation but fails in hardware" scenario, and I'd approach it systematically:

1. **First, verify the state machine encoding** — If the FSM uses binary or one-hot encoding, I'd check whether the synthesis tool optimized away any "don't care" states. A common issue is that the synthesis tool assumes illegal states never occur and optimizes the next-state logic accordingly, so if the FSM somehow enters an illegal state (due to a glitch, metastability, or uninitialized register), it can never recover.

2. **Check for uninitialized state registers** — I'd verify that the FSM has a proper reset that initializes all state bits. If the reset is asynchronous, I'd check for reset recovery/release timing issues. If the FSM relies on implicit initialization, that's a bug — FPGA registers power up in an unknown state.

3. **Look for CDC issues on the input path** — The specific external input sequence that triggers the failure suggests the input might be crossing clock domains or arriving asynchronously. I'd check whether the input is properly synchronized before entering the FSM. A single-bit input that changes asynchronously relative to the FSM clock can cause metastability, which could put the FSM into an illegal state.

4. **Use the chipscope/ILA to capture the actual state** — I'd insert a logic analyzer core to monitor the FSM state register and the relevant inputs, triggering on the illegal state value. This would tell me exactly how the FSM entered the illegal state and what the input sequence looked like.

5. **Compare gate-level simulation with hardware behavior** — I'd run post-synthesis and post-place-and-route simulation with the actual input sequence, including realistic timing delays. This often reveals issues that RTL simulation misses, such as combinational glitches on FSM inputs or race conditions.

6. **Add defensive coding** — Regardless of the root cause, I'd add a watchdog or recovery mechanism: a default state that traps illegal states and forces a reset, or a "safe state" that the FSM enters if it detects an invalid encoding.

**Possible follow-ups:** How would you distinguish between a synthesis optimization issue and a metastability issue in this scenario? What if the illegal state is only reachable through a path that the synthesis tool has determined is unreachable?

---

## Q3: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** This is a demanding PDN requirement — 20A at 0.85V with 1A/ns slew rate means the core rail must stay within roughly ±25mV of nominal. I'd approach this in layers:

1. **Voltage regulator selection** — A multi-phase buck converter is essential for this current level. I'd calculate the number of phases based on the transient response requirement. The key parameter is the regulator's bandwidth and output impedance — I'd target a closed-loop output impedance that stays below the target impedance across the frequency range of interest. The target impedance is approximately ΔV/ΔI = 25mV/20A = 1.25mΩ, but this needs to be maintained across a wide frequency range.

2. **Bulk capacitance** — I'd place bulk capacitors (e.g., polymer tantalum or aluminum polymer) near the regulator output to handle the low-frequency transient energy. The total bulk capacitance needs to supply the energy during the regulator's response time.

3. **Mid-frequency decoupling** — Ceramic capacitors in the 10-100µF range (multiple 0805/0603 packages) provide the mid-frequency response. I'd distribute these across the board, close to the FPGA's power pins.

4. **High-frequency decoupling** — Small-value ceramics (100nF, 10nF, 1nF) placed very close to the FPGA pins handle the highest-frequency transients. These need to be on the same side of the board as the FPGA or connected through low-inductance vias.

5. **PCB stack-up and plane design** — The core rail needs a dedicated power plane with minimal inductance. I'd use a thin dielectric between the power and ground planes (e.g., 100µm or less) to maximize plane capacitance. The plane pair acts as a distributed capacitor at high frequencies.

6. **Verification** — I'd perform a frequency-domain analysis using SPICE simulation of the entire PDN, including the regulator model, capacitor ESR/ESL, and plane inductance. I'd also run time-domain transient simulations with a current step of 20A at 1A/ns to verify the voltage stays within spec. On the bench, I'd use a high-bandwidth oscilloscope with a low-inductance probe to measure the actual transient response.

7. **Layout considerations** — I'd minimize the loop area between the FPGA's power and ground pins, use multiple vias in parallel to reduce via inductance, and avoid routing other signals through the power plane area.

**Possible follow-ups:** How would you determine the number of regulator phases needed? What if the measured transient response shows a voltage droop that exceeds spec — how would you determine whether to add more bulk capacitance or improve the regulator bandwidth?

---

## Q4: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a 64-tap FIR filter, and output the filtered result without any dropped samples, while also meeting timing at the target clock frequency?

**Answer:** The fundamental challenge here is that 500 MSPS exceeds the typical FPGA fabric clock rate, so I'd need to use a parallel processing architecture. Here's how I'd approach it:

1. **Determine the fabric clock frequency** — Modern FPGAs can typically run logic at 250-400 MHz. If I target 250 MHz, I need to process two samples per clock cycle (2:1 parallelism). If the fabric can only achieve 200 MHz reliably, I'd need 3:1 or higher parallelism.

2. **Choose the parallelization factor** — Let's say I target 250 MHz, giving a 2:1 parallel architecture. The 64-tap FIR filter would need to produce two output samples per clock cycle, each requiring 64 multiply-accumulate operations. That's 128 MACs per cycle total.

3. **Architecture selection** — For a 2:1 parallel FIR, I'd use a polyphase decomposition. The 64-tap filter is split into two 32-tap sub-filters (even and odd phases). Each sub-filter processes every other input sample. The outputs are combined as: y[n] = even_phase(x_even) + odd_phase(x_odd), with appropriate delays. This halves the number of taps each sub-filter needs to compute per output.

4. **Resource allocation** — With 128 MACs per cycle at 250 MHz, I'd use DSP slices. Modern FPGAs have hundreds of DSP slices, each capable of one 18x18 or 25x18 multiply-accumulate per cycle. I'd need to check the DSP slice count and possibly use time-multiplexing if resources are tight.

5. **Pipeline stages** — I'd pipeline the multiply and accumulate stages to meet timing. The FIR filter structure naturally allows pipelining: registers between the multiplier output and the adder tree, and registers within the adder tree itself. The latency increases, but throughput is maintained.

6. **Input data capture** — The 500 MSPS input needs to be deserialized into the parallel fabric clock domain. I'd use the FPGA's I/O serializer/deserializer (ISERDES) primitives to capture the data at 500 MSPS and present two samples per 250 MHz clock cycle to the fabric.

7. **Output handling** — Similarly, the two filtered outputs per cycle need to be serialized back to 500 MSPS if the output is a single stream, or kept parallel if the downstream logic can accept two samples per cycle.

8. **Verification** — I'd verify the polyphase decomposition against the original filter in simulation, checking that the parallel implementation produces bit-identical results to the serial version. I'd also run timing analysis to ensure the 250 MHz clock is met across process, voltage, and temperature corners.

**Possible follow-ups:** How would you handle the filter coefficients if they need to be programmable in real-time? What if the filter needs to be reconfigured between different tap counts or decimation factors?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical concern and the engineer's understanding of the system behavior. I'd approach it as follows:

1. **Acknowledge the valid reasoning** — I'd start by acknowledging that the engineer's average-rate analysis is correct as far as it goes. The average write rate being below the read rate is necessary, but it's not sufficient to guarantee the FIFO won't overflow.

2. **Reframe the question around burst behavior** — I'd ask the engineer to walk me through the worst-case burst scenario: what's the maximum number of consecutive ADC samples that can arrive before the memory controller can start draining? This includes the memory controller's refresh cycles, bank conflicts, read/write turnaround penalties, and the fact that the memory controller might be busy servicing other requests (e.g., reads from a processor or display controller).

3. **Quantify the memory controller's sustainable rate** — I'd point out that DDR3 has significant overhead: refresh cycles occur every 7.8µs and take priority, bank conflicts require precharge and activate delays, and write-to-read turnaround has bus idle time. The sustainable write bandwidth is typically 70-85% of the peak theoretical bandwidth. If the ADC bursts at 500 MSPS and the memory controller can only sustain 80% of peak, the FIFO needs to absorb the difference during the burst.

4. **Work through an example** — I'd ask the engineer to calculate: if the ADC produces a burst of 1000 samples at 500 MSPS (2µs burst), and the memory controller can only drain at 400 MSPS effective during that time, the FIFO needs to hold at least 200 samples just for that burst — already exceeding the 64-word depth.

5. **Suggest a verification approach** — Rather than just asserting the FIFO is too small, I'd suggest we model the worst-case burst scenario in simulation, including the memory controller's actual timing behavior. I'd ask the engineer to create a testbench that generates the worst-case ADC burst pattern and verify whether the FIFO overflows.

6. **Discuss the failure mode** — I'd explain that FIFO overflow in this system doesn't just mean lost data — it could mean corrupted data if the write pointer wraps and overwrites unread data, or it could cause backpressure that stalls the ADC, potentially missing time-critical samples.

7. **Collaborative resolution** — I'd frame this as a design question to solve together, not a criticism. We'd work through the burst analysis, determine the correct FIFO depth (likely several hundred to a few thousand words depending on the worst-case burst), and also discuss whether a watermark-based flow control or a larger external buffer might be more appropriate.

The key is to help the engineer develop the analytical skills to think about worst-case behavior, not just average behavior, and to understand that memory controllers have significant overhead that reduces their sustainable throughput.

**Possible follow-ups:** How would you help the engineer develop a worst-case burst model for the ADC and memory controller? What if the engineer's analysis shows the FIFO needs to be impractically large — what architectural alternatives would you consider?