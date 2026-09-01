# high-speed-digital-fpga — Day 42

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For asynchronous multi-bit data transfer with frequent changes and low-latency requirements, I'd first characterize the exact relationship between the clocks. If they're truly asynchronous with no known phase relationship, the safest approach is an asynchronous FIFO with gray-coded pointers. The key design decisions are FIFO depth and the synchronization strategy for the read/write pointers.

For the pointer synchronization, I'd use multi-stage flip-flop synchronizers (typically two or three stages) on the gray-coded pointers. Gray coding ensures only one bit changes at a time, so even if a pointer value is sampled mid-transition, the result is either the old or new value—never a corrupted intermediate value. This eliminates the multi-bit CDC hazard.

For latency minimization, I'd consider the FIFO's "almost empty" threshold carefully. A standard FIFO adds latency from the synchronizer stages (typically 2–3 destination clock cycles) plus the time to propagate the write pointer across the domain. If latency is critical, I could explore a "forward" or "cut-through" path where the first word is forwarded speculatively before the FIFO confirms it's safe to read, but this adds complexity and risk. A more practical approach is to use a smaller FIFO with careful threshold management, accepting that the synchronizer latency is unavoidable.

For the data path itself, I'd ensure the data is written into the FIFO in the source domain and read out in the destination domain—the FIFO memory itself is dual-port and handles the actual data transfer. The critical part is that the write and read pointers never cross, which is guaranteed by the gray-code comparison logic.

I'd also verify the design with CDC-specific simulation tools that inject metastability at the synchronizer outputs, and I'd run formal CDC verification to catch any un-synchronized paths. In the timing constraints, I'd set proper false paths or asynchronous clock groups between the two domains, and ensure the synchronizer registers are placed in the same I/O or logic block to minimize routing delay between them.

**Possible follow-ups:**
- How would you determine the minimum FIFO depth for this scenario?
- What happens if the data rate is very close to the FIFO's sustainable throughput—how would you handle backpressure?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully (DONE pin goes high) but the device does not enter the expected functional state—for example, all outputs remain tri-stated or in a default state?

**Answer:** This is a classic "configuration succeeded but initialization failed" scenario. I'd approach this systematically, starting with the most likely causes.

First, I'd verify the configuration source and sequence. Even though DONE is high, I'd check that the configuration mode pins are set correctly and that the bitstream actually matches the device and design revision. A common issue is loading an older or incorrect bitstream that happens to be valid for the device but doesn't contain the expected logic.

Next, I'd check the device initialization sequence. After configuration, FPGAs go through a startup phase where the DONE pin asserts and the device releases its I/O from tri-state. If the design uses a specific startup sequence (e.g., waiting for a clock to stabilize, or a user-defined startup state), a problem in that sequence could leave outputs in their default state. I'd verify that the global reset is de-asserted properly—if the reset is held active by default or by an external signal, the design would sit in reset and outputs would remain in their initial state.

I'd also check the clocking. If the design uses a PLL or MMCM and the clock isn't arriving or the PLL isn't locking, the design might be stuck waiting for a locked signal before enabling outputs. I'd probe the PLL locked output and verify the input clock is present and within the PLL's specified range.

Another angle is the I/O standard and voltage levels. If the I/O bank voltage isn't at the expected level, or the I/O standard is configured incorrectly (e.g., LVCMOS33 configured but the bank is at 2.5V), the outputs might not drive correctly even though the logic is running. I'd verify the VCCO for each bank and check the I/O standard configuration in the bitstream settings.

Finally, I'd use the FPGA's internal logic analyzer or a JTAG-based debug interface to inspect the state of key internal signals—reset, clock enable, state machine states—to see where the design is stuck. If the design has a status register or heartbeat counter, I'd check whether it's advancing, which would tell me if the fabric is actually running.

**Possible follow-ups:**
- How would you distinguish between a configuration issue and a logic initialization issue?
- What specific signals would you probe first, and why?

---

## Q3: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a 64-tap FIR filter, and output the filtered result without any dropped samples, while also meeting timing at the target clock frequency?

**Answer:** The fundamental challenge here is that 500 MSPS exceeds the typical FPGA fabric clock rate, so I'd need to use a parallel processing architecture. The standard approach is time-division multiplexing with multiple parallel filter branches.

First, I'd determine the fabric clock frequency. If the FPGA can run at 250 MHz, I'd use a 2-way interleaved architecture where two samples arrive per clock cycle. If the fabric maxes out at 200 MHz, I'd need a 3-way or 4-way interleaved design. Let me walk through the 2-way case at 250 MHz.

The 64-tap FIR filter would be split into two parallel filters, each processing every other sample. Each branch computes a 64-tap filter, but the coefficients are different: one branch uses the even-indexed coefficients, the other uses odd-indexed coefficients. This is the polyphase decomposition of the filter. Each branch runs at 250 MHz and processes 32 taps per clock cycle (or uses a multi-cycle approach with resource sharing).

For the implementation, I'd use DSP slices for the multiply-accumulate operations. A 64-tap filter with 16-bit inputs and coefficients requires 64 multipliers per branch, or I could time-share fewer multipliers across multiple clock cycles if the data rate allows. At 250 MHz with 32 taps per branch, I could use a single DSP slice per tap with a 32-cycle pipeline, or use more DSP slices in parallel to reduce latency.

The key timing challenge is the adder tree that combines the partial products. I'd pipeline the adder tree carefully to meet timing, adding register stages as needed. The trade-off is latency versus throughput—pipelining adds latency but doesn't reduce throughput as long as the pipeline fills continuously.

For the input interface, I'd use the FPGA's I/O deserialization resources (ISERDES or similar) to capture the 500 MSPS data and present two 16-bit samples per 250 MHz clock cycle. The output would use the corresponding serialization resources.

I'd also need to handle the filter's group delay and ensure the output data is continuous. The polyphase decomposition naturally produces one output sample per input sample, so as long as the input stream is continuous and the pipeline is full, the output will be continuous.

For verification, I'd create a bit-exact simulation model in C or Python, generate test vectors, and compare the FPGA simulation output against the reference. I'd also verify the polyphase decomposition mathematically—the frequency response of the parallel implementation must match the original filter.

**Possible follow-ups:**
- How would you handle the case where the fabric clock is only 125 MHz—what architecture changes would you make?
- How would you verify that the polyphase decomposition is mathematically correct?

---

## Q4: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** The core rail is the most challenging because of the combination of high current, fast slew rate, and tight tolerance. At 0.85V with ±3%, the allowable deviation is only ±25.5 mV. With a 1A/ns slew rate, the PDN impedance must be extremely low at high frequencies.

I'd approach this in three layers: the voltage regulator module (VRM), the bulk decoupling, and the high-frequency decoupling.

For the VRM, I'd select a regulator that can handle the 20A steady-state current with sufficient headroom, and critically, one with a fast transient response. The VRM's control loop bandwidth determines how quickly it can respond to load changes. A multi-phase buck converter with a high switching frequency (1–2 MHz) would be appropriate. The VRM's output impedance should be designed to be flat up to its control loop bandwidth—typically a few hundred kHz.

For the bulk decoupling, I'd use a combination of bulk capacitors (tantalum, polymer, or ceramic) to provide energy storage for transients in the 100 kHz to 1 MHz range. The total bulk capacitance needs to be sized so that the voltage droop during a transient stays within the ±3% window. The formula is roughly C = I × Δt / ΔV, where Δt is the time before the VRM responds. For a 20A step with a 10 µs VRM response time and 25 mV allowed droop, that's about 8 mF—a significant amount of capacitance.

For the high-frequency decoupling, I'd use a combination of ceramic capacitors with different values (e.g., 100 nF, 10 nF, 1 nF) placed as close to the FPGA power pins as possible. The key is to minimize the loop inductance between the capacitor and the FPGA. I'd place capacitors on both sides of the board, directly under the FPGA if possible, and use multiple vias to connect to the power and ground planes.

The critical analysis is the target impedance. The target impedance is Z = ΔV / ΔI = 25 mV / 20A = 1.25 mΩ. This impedance must be maintained from DC up to the frequency where the on-die decoupling takes over—typically 100 MHz or higher. I'd use a PDN analysis tool to model the impedance versus frequency and verify that it stays below the target across the entire frequency range.

I'd also consider the PCB stack-up. The power and ground planes should be adjacent with minimal dielectric thickness to maximize plane capacitance. A 4-mil core between the core power plane and ground gives significant distributed capacitance that helps at higher frequencies.

For verification, I'd perform a transient simulation using a current source model that mimics the FPGA's worst-case switching pattern. I'd also do a frequency-domain impedance analysis to check for resonances. On the bench, I'd use a high-bandwidth oscilloscope with a differential probe to measure the core voltage during worst-case switching activity, and I'd use a network analyzer to measure the PDN impedance.

**Possible follow-ups:**
- How would you handle the interaction between the bulk capacitor ESR and the target impedance?
- What would you do if the measured impedance shows a resonance peak above the target impedance?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior—the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical concern and the engineering process. The core issue is that the engineer is relying on average rates rather than worst-case burst behavior, which is a common and dangerous mistake in high-speed data path design.

First, I'd acknowledge the engineer's reasoning—it's true that average rates matter and that the memory controller has some buffering. But I'd then walk through the worst-case scenario together. I'd ask the engineer to calculate the maximum burst size from the ADC (e.g., if the ADC produces 1024 samples per burst at 500 MSPS, that's 2 µs of data). Then I'd ask about the memory controller's sustainable write rate during a burst—DDR3 has refresh cycles, read/write turnaround penalties, and bank conflicts that reduce the sustainable rate below the peak rate. The question is whether the FIFO depth plus the memory controller's write buffer can absorb the difference between the burst write rate and the sustainable memory write rate.

I'd frame this as a collaborative analysis rather than a criticism. I'd suggest we work through the math together: burst size, FIFO depth, memory controller write buffer depth, and the sustainable write rate during worst-case conditions (e.g., when the memory is also being read, or when refresh coincides with the burst). If the analysis shows the FIFO is insufficient, we'd need to increase the depth or add flow control.

I'd also raise the broader design principle: relying on average rates for a real-time data path is risky because it's difficult to guarantee worst-case behavior without explicit analysis. The FIFO depth should be sized based on the worst-case difference between the write and read rates over the longest possible burst, plus margin for clock jitter and memory controller variability.

If the engineer still disagrees, I'd propose we do a formal analysis—either a simulation with worst-case burst patterns or a written calculation that we both review. I'd also suggest adding a watermark or overflow flag to the FIFO so that if it does approach full, the system can detect it and take corrective action (e.g., assert backpressure to the ADC or flag an error).

Finally, I'd use this as a teaching moment about design margins. In high-speed systems, especially those handling real-time data, it's better to over-provision buffering than to discover an overflow condition in the field. The cost of a few hundred extra words of FIFO is trivial compared to the cost of debugging an intermittent data loss issue.

**Possible follow-ups:**
- How would you handle the situation if the engineer's analysis shows the FIFO is actually sufficient?
- What metrics or analysis would you require before signing off on the design?