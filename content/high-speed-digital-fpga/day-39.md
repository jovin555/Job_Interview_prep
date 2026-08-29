# high-speed-digital-fpga — Day 39

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** This is a classic asynchronous CDC problem where you can't use simple two-flop synchronization because you're moving multi-bit data that changes frequently. The key tension is between latency and safety. My first step would be to characterize the requirements precisely: what's the data rate, how frequently does data change, what's the acceptable latency budget, and what's the consequence of a corrupted transfer?

For a multi-bit bus with frequent changes, I'd typically use one of two approaches. The first is an asynchronous FIFO with Gray-coded pointers. This is the standard solution when data flows continuously and you need bounded latency. The write pointer is Gray-coded and synchronized into the read domain, and vice versa. The FIFO depth needs to be sized based on the maximum burst size and the frequency ratio between the domains. The key design details are ensuring the Gray code is truly single-bit-changing between adjacent values, and that the synchronizer chains (typically two or three flops) are properly placed in the design to minimize MTBF.

The second approach, if the data is more like a register snapshot that must be captured coherently, is a handshake-based transfer with a data-valid signal. The source asserts a request, the destination synchronizes it, captures the data, and asserts an acknowledge. This has higher latency but guarantees coherence. For minimizing latency while maintaining integrity, I'd look at whether the frequency relationship is known and stable. If it is, you can sometimes use a multi-stage pipeline with careful timing analysis rather than full handshaking.

For the actual implementation, I'd pay close attention to the synchronizer placement — they need to be in the I/O or register tiles close to the boundary, and I'd verify the design with formal CDC analysis tools that check for proper synchronization, reconvergence issues, and Gray-code correctness. I'd also simulate with randomized timing skew between the domains to stress-test the design.

**Possible follow-ups:**
- How would you determine the required FIFO depth for a given frequency ratio and burst pattern?
- What happens if the two clocks have a small but nonzero frequency drift over time?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully (DONE pin goes high) but the device does not enter the expected functional state — for example, all outputs remain tri-stated or in a default state?

**Answer:** When configuration completes but the design doesn't start functioning, I'd approach this systematically. First, I'd verify that configuration actually completed correctly — DONE going high is necessary but not sufficient. I'd check the configuration status registers and verify the bitstream CRC check passed. If there's a configuration error indicator, that would point to a corrupted bitstream or a configuration issue.

Next, I'd check the reset architecture. A very common cause is a global reset that's stuck asserted — either the reset pin is held active by external circuitry, the reset polarity is inverted from what the logic expects, or an internal reset generator (like a power-on reset circuit or a reset derived from a PLL lock signal) never releases. I'd probe the reset net and trace it back to its source. I'd also check if the design uses a startup sequence or initialization state machine that might be waiting for a condition that never occurs.

Another angle is clocking. If the design has no clock, nothing will happen. I'd verify that the clock input pin is actually toggling, that the PLL/MMCM is locked, and that the clock enable signals are asserted. Sometimes the issue is that the clock is present but the PLL configuration is wrong, so the PLL never locks and the design waits indefinitely for the locked signal.

I'd also check the I/O standards and configuration. If outputs are tri-stated, it could be that the I/O standard is misconfigured, the output enables are never asserted, or the bank voltage isn't present. I'd verify the I/O bank supply voltages and check if the pin assignments match the schematic.

Finally, I'd use the FPGA vendor's debug tools — an integrated logic analyzer (like ChipScope or SignalTap) or a virtual I/O core — to probe internal signals. If I can't insert logic analyzers post-configuration, I'd add them in the original design for debug purposes. I'd also consider whether the issue is in the bitstream generation itself — perhaps a synthesis or implementation setting that caused the design to be optimized away or misrouted.

**Possible follow-ups:**
- How would you distinguish between a reset issue and a clock issue when the design appears completely dead?
- What role does the configuration mode (master vs. slave, SPI vs. JTAG) play in this scenario?

---

## Q3: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 1 GSPS, perform a digital down-conversion (DDC) with a programmable decimation factor, and output the result over a PCIe Gen3 x4 interface?

**Answer:** This is a demanding data path problem because the input rate far exceeds what the FPGA fabric can handle at a single clock frequency. The first key decision is the parallelization strategy. At 1 GSPS with 16-bit samples, that's 16 Gbps of input data. If the fabric runs at 250 MHz, I'd need 4 samples per clock cycle; at 200 MHz, I'd need 5 samples per cycle. The ADC interface would need to be designed to deliver data in this parallel format — either the ADC itself provides multiple lanes, or I'd use deserialization in the I/O tiles.

For the DDC itself, the structure depends on the decimation factor. The DDC typically consists of a numerically controlled oscillator (NCO) for mixing, followed by a decimating FIR filter. The NCO needs to generate a complex exponential at the mixing frequency. For high throughput, I'd implement the NCO using a phase accumulator with a lookup table or CORDIC, but I'd need to generate multiple output samples per clock cycle — so I'd use a time-division multiplexed approach where the phase accumulator advances by the appropriate phase increment for each output sample.

The decimating FIR filter is where the real throughput challenge lies. For a decimation factor of D, you only need to compute every D-th output sample, but you still need to process all input samples. The polyphase decomposition is the standard approach — you split the filter into D sub-filters, each operating at the output rate, and you only compute the outputs you actually need. This reduces the computational load by a factor of D. The filter coefficients would be stored in block RAM, and I'd use the DSP slices efficiently by time-multiplexing them across the parallel input samples.

For the PCIe Gen3 x4 interface, the output data rate after decimation needs to fit within the PCIe bandwidth. PCIe Gen3 x4 provides roughly 32 Gbps of raw bandwidth, so there's headroom, but I'd need to consider protocol overhead. The key design question is how to buffer the data between the DDC output and the PCIe DMA engine. I'd use an asynchronous FIFO to cross from the DDC clock domain to the PCIe user clock domain, with careful sizing to handle burst behavior.

The critical verification step would be to create a bit-exact simulation model of the DDC in C or Python, generate test vectors, and compare the FPGA implementation against the reference model. I'd also pay careful attention to the timing closure of the parallel data path — the fan-out of the input data to multiple processing lanes can create timing challenges, so I'd use register duplication and careful placement.

**Possible follow-ups:**
- How would you choose between a CORDIC and a lookup table for the NCO, and what are the trade-offs in terms of spurious-free dynamic range (SFDR)?
- How would you handle the case where the decimation factor is not an integer multiple of the parallelization factor?

---

## Q4: How would you approach designing a finite state machine (FSM) in an FPGA that must control a high-speed data path with strict latency requirements (e.g., a packet processor that must make a forwarding decision within 5 clock cycles at 400 MHz), while also being robust against single-event upsets (SEUs)?

**Answer:** This problem combines two challenging requirements: strict latency and SEU robustness. These pull in opposite directions — the simplest SEU mitigation techniques add latency, so I need to find a balance.

For the latency requirement, the FSM needs to make a decision within 5 cycles at 400 MHz. That means the critical path through the state register, next-state logic, and output decode must fit within 2.5 ns. I'd start by designing the FSM with a minimal state encoding — one-hot encoding is often used for speed because the next-state logic is simpler (fewer product terms), but it uses more flip-flops. For SEU robustness, one-hot actually has a nice property: a single-bit upset in the state register produces an illegal state (either all-zero or two-hot), which can be detected.

For SEU robustness, I'd consider several techniques. The first is triple modular redundancy (TMR) — three copies of the FSM with voting on the outputs. This is the gold standard but triples the logic and can add a cycle of latency for the voter. At 400 MHz with a 5-cycle budget, I'd need to carefully pipeline the voter to fit in the timing budget.

The second approach is a Hamming-code-protected state register. You encode the state with additional check bits that allow single-error correction. The decoder and corrector add combinational logic in the feedback path, which could push the critical path over the limit. I'd need to evaluate whether the correction logic fits in the timing budget.

A third approach, which is lighter-weight, is to use a "safe" FSM implementation with illegal-state detection and recovery. The state register is monitored for illegal states (using the one-hot property or a parity check), and if an illegal state is detected, the FSM is forced back to a known reset state. This doesn't correct the error immediately but prevents the FSM from getting stuck in an illegal state. The detection logic adds minimal latency — it's just a few gates in parallel with the next-state logic.

Given the strict latency budget, I'd likely start with the safe-FSM approach and add TMR only if the application truly requires continuous correct operation without any glitches. For a packet processor, a brief recovery period after an SEU might be acceptable, whereas for a safety-critical function, TMR would be necessary.

I'd also consider the broader system context. SEUs in the configuration memory are actually more likely to cause problems than SEUs in the state registers — a configuration bit upset can change the routing or LUT contents, which is much harder to detect. For true robustness, I'd need to consider configuration scrubbing (periodically rewriting the configuration memory) in addition to FSM-level mitigation.

**Possible follow-ups:**
- How would you verify that the SEU mitigation doesn't introduce timing violations in the FSM feedback path?
- What's the trade-off between TMR and a Hamming-code approach in terms of area, latency, and fault coverage?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical concern and the engineering process. The technical issue is real — relying on average rates when the system has burst behavior is a classic pitfall. The memory controller's write buffer does provide some elasticity, but it's not infinite, and it's shared with other functions like refresh operations that can temporarily block writes. If the FIFO overflows, you lose data, and in a data acquisition system, that's typically a critical failure.

My approach would be to first acknowledge the engineer's reasoning — they've thought about the average case, which is a good start. Then I'd walk through the burst scenario together. I'd ask questions like: "What's the maximum burst size from the ADC?" "What's the memory controller's sustainable write rate during a refresh burst?" "What happens when the memory controller is busy servicing a read request from the host?" These questions help the engineer see the gap in their analysis.

Then I'd suggest we do a quantitative analysis. I'd ask the engineer to calculate the worst-case fill rate of the FIFO — the maximum burst size from the ADC, the minimum sustainable write rate of the memory controller (including refresh overhead and read/write turnaround), and the resulting maximum FIFO occupancy. This turns the discussion from opinion into engineering analysis. If the analysis shows the FIFO is too shallow, we can calculate the required depth together.

I'd also use this as a teaching moment about design margins. In a data acquisition system, data loss is often unacceptable, and you need to design for the worst case, not the average case. The cost of a slightly deeper FIFO is small compared to the cost of losing data in the field.

If the engineer still disagrees after the analysis, I'd suggest we add a test to the verification plan that specifically exercises the worst-case burst scenario. This way, we can validate the design empirically rather than relying on argument. If the test passes with margin, great — we've proven the design. If it fails, we have concrete evidence for why the FIFO needs to be deeper.

The key is to be collaborative, not dismissive. The goal is to help the engineer develop better engineering judgment, not just to win the argument.

**Possible follow-ups:**
- How would you handle the situation if the engineer's analysis shows the FIFO is actually sufficient, but you still have concerns about other burst scenarios they haven't considered?
- What documentation or design review process would you put in place to catch this type of issue earlier in the design cycle?