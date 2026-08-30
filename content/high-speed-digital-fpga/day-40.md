# high-speed-digital-fpga — Day 40

## Q1: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design's internal state machine appears to be stuck in an illegal state only when a specific external input sequence occurs, and the issue is not reproducible in RTL simulation?

**Answer:** This is a classic case where the design works in simulation but fails in hardware under specific conditions. My approach would be systematic:

First, I'd verify that the state machine encoding is correct and that the reset behavior is well-defined. A common root cause is that the state machine enters an illegal state due to a metastability event on an asynchronous input, or due to a clock domain crossing issue that wasn't captured in simulation. I'd check whether all inputs to the state machine are properly synchronized, especially if they come from external pins or another clock domain.

Second, I'd examine the specific input sequence that triggers the failure. If the sequence involves inputs changing close to a clock edge, metastability is a prime suspect. I'd also look at whether the sequence creates a timing hazard—for example, two inputs changing simultaneously where the state machine's next-state logic has a race condition.

Third, I'd use the FPGA's built-in debug capabilities. I'd insert an Integrated Logic Analyzer (ILA) or logic analyzer core to capture the state register values and the inputs around the failure point. This would tell me exactly which illegal state the machine enters and what the input conditions were. I'd also check if the state machine has a "safe" recovery path—if not, I'd add one that forces a return to a known state after a timeout or on detection of an illegal encoding.

Finally, I'd compare the hardware behavior against the simulation more carefully. If the issue isn't reproducible in RTL simulation, I'd consider whether the simulation is missing something—perhaps unconstrained input timing, missing asynchronous input modeling, or incorrect reset behavior. I'd also run gate-level simulation with timing annotations, which can catch issues that RTL simulation misses.

**Possible follow-ups:**
- How would you design a state machine to be resilient to illegal states in the first place?
- What specific synchronization techniques would you use for the external inputs?

---

## Q2: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For a multi-bit bus crossing between asynchronous clock domains with frequent data changes and low-latency requirements, the standard approach is an asynchronous FIFO. The key design considerations are:

First, the FIFO must use Gray-code pointers on both the write and read sides. Gray code ensures that only one bit changes at a time when the pointer increments, which makes the pointer transfer across clock domains safe when properly synchronized. The write pointer is synchronized into the read clock domain (and vice versa) using a two-flop synchronizer.

Second, I'd carefully size the FIFO depth. The depth must accommodate the worst-case burst of writes versus the read rate, plus the synchronization latency (typically 2-3 cycles on each side). For a continuously flowing data stream where the average rates are matched but there's jitter or burstiness, I'd calculate the maximum difference between cumulative writes and reads over any time window.

Third, I'd generate the full and empty flags correctly. The full flag is generated in the write clock domain by comparing the synchronized read pointer against the write pointer; the empty flag is generated in the read clock domain by comparing the synchronized write pointer against the read pointer. This ensures the flags are valid in the domain where they're used, at the cost of some pessimism due to synchronization latency.

For minimizing latency, I'd consider a "show-ahead" or "first-word fall-through" FIFO mode, where the first word written becomes available on the read side immediately (before the read request), reducing the read-side latency. I'd also ensure the synchronizer chains are minimal (two stages is standard) and that the FIFO control logic doesn't add unnecessary pipeline stages.

Finally, I'd verify the design with formal CDC analysis tools or careful simulation that includes metastability modeling. I'd also check that the Gray-code encoding is correct for the FIFO depth—it must be a power of 2, or use a non-power-of-2 Gray code variant if necessary.

**Possible follow-ups:**
- What happens if the FIFO becomes full—how would you handle backpressure?
- How would you verify that the Gray-code pointer synchronization is correct?

---

## Q3: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** This is a demanding PDN requirement—20A at 0.85V with a 1A/ns slew rate means the core rail must maintain 0.825V to 0.875V under extreme transient conditions. My approach would be multi-layered:

First, I'd start with the target impedance calculation. For a 20A transient with a 25mV allowable deviation (3% of 0.85V), the maximum allowable PDN impedance is 25mV/20A = 1.25mΩ across the frequency range of interest. The frequency range extends from the transient repetition rate up to where the on-die decoupling takes over—typically from a few kHz to several hundred MHz.

Second, I'd design the decoupling network in tiers. The first tier is on-die capacitance, which I can't control directly but can influence through FPGA selection. The second tier is the package capacitance and the discrete capacitors placed very close to the FPGA—small-value, low-ESL capacitors (e.g., 0402 or 0201 packages) in the 0.1µF to 1µF range. The third tier is bulk capacitance on the board—larger values (10µF to 100µF) in larger packages that handle the lower-frequency content of the transient.

Third, I'd design the PCB stack-up carefully. The core rail should have a dedicated power plane adjacent to a ground plane, with minimal dielectric thickness to maximize plane capacitance. I'd use multiple vias to connect the FPGA's power pins to the planes, and I'd place the decoupling capacitors as close as possible to the FPGA with short, wide traces or direct via connections.

Fourth, I'd consider the voltage regulator module (VRM) response. The VRM must have sufficient bandwidth to handle the lower-frequency components of the transient. I'd look at the VRM's transient response specification and ensure it can recover within the allowed voltage window. In some cases, a multi-phase regulator or a regulator with a fast transient response is necessary.

Finally, I'd verify the design using simulation tools. I'd create a SPICE model of the PDN including the VRM output impedance, plane capacitance, via inductance, and capacitor models (including ESL and ESR). I'd simulate the transient response to a worst-case current step and verify the voltage stays within the ±3% window. I'd also perform a frequency-domain analysis to verify the target impedance is met across the frequency range.

**Possible follow-ups:**
- How would you decide between using more bulk capacitance versus a faster VRM?
- What measurements would you take on the actual board to verify the PDN performance?

---

## Q4: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a 64-tap FIR filter, and output the filtered result without any dropped samples, while also meeting timing at the target clock frequency?

**Answer:** The fundamental challenge here is that a 500 MSPS sample rate exceeds the typical FPGA fabric clock frequency—most FPGAs can't run general logic at 500 MHz. The solution is to use parallel processing: process multiple samples per clock cycle.

My approach would be to use a time-division multiplexed (TDM) or polyphase decomposition architecture. If the FPGA fabric clock is, say, 250 MHz, I'd process two samples per clock cycle. At 125 MHz, I'd process four samples per cycle. The key is to restructure the FIR filter into parallel branches, each handling a subset of the input samples.

For a 64-tap FIR filter with P parallel paths, I'd use polyphase decomposition. The filter is split into P sub-filters, each with 64/P taps (if 64 is divisible by P). Each sub-filter operates on a decimated version of the input stream. The outputs of the sub-filters are then combined to produce the full-rate output. This is mathematically equivalent to the original filter but allows the logic to run at a lower clock frequency.

I'd also consider using the FPGA's DSP slices efficiently. Modern FPGAs have DSP blocks that can implement multiply-accumulate operations at high speed. I'd map the filter taps to DSP slices, using the built-in pre-adder and accumulator features where appropriate. For a 64-tap filter, I'd need 64 multipliers (or fewer if I use time-multiplexing within the DSP slices).

For the input data path, I'd use a deserializer to convert the 500 MSPS serial stream into parallel words at the lower clock rate. The FPGA's I/O resources—specifically the ISERDES or similar deserializer primitives—can capture high-speed serial data and present it as parallel data to the fabric.

For verification, I'd simulate the parallel architecture against a reference model of the original filter to ensure bit-exact equivalence. I'd also check the timing closure at the target clock frequency, paying attention to the critical paths in the filter's adder tree. If timing is tight, I'd consider pipelining the adder tree or using the DSP slices' built-in pipeline registers.

**Possible follow-ups:**
- How would you handle the filter coefficients if they need to be programmable in real-time?
- What if the filter length isn't evenly divisible by the number of parallel paths?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical concern and the engineer's reasoning process. The core issue is that the engineer is relying on average rates rather than worst-case burst behavior, which is a common pitfall in FIFO sizing.

My approach would be to first acknowledge the engineer's reasoning—it's true that average rates matter, and the memory controller's write buffer does provide some absorption. But I'd then walk through the worst-case analysis together. I'd ask the engineer to calculate the maximum burst size from the ADC (how many consecutive samples can arrive without gaps), the memory controller's sustainable write rate (accounting for refresh cycles, read/write turnaround, and bank conflicts), and then compute the required FIFO depth as: (burst size) minus (amount the memory controller can drain during the burst) plus (synchronization latency margin).

I'd also point out that the memory controller's write buffer is not a substitute for the FIFO—the write buffer serves a different purpose (absorbing short-term bus contention) and may not be sized for the ADC's burst pattern. If the FIFO overflows, samples are lost, which could corrupt the data acquisition.

Rather than simply overriding the engineer, I'd frame this as a collaborative analysis. I'd suggest we work through the numbers together, and if the analysis shows the FIFO is indeed too small, we'd determine the correct depth. I'd also use this as a teaching moment about worst-case analysis in digital design—it's not enough for a design to work on average; it must work under the worst-case conditions specified in the requirements.

If the engineer still resists after the analysis, I'd escalate to a more formal approach—perhaps requiring a written worst-case analysis as part of the design review checklist, or involving a more senior engineer to validate the analysis. But my first step is always to work through the technical reasoning together and help the engineer see why the concern is valid.

**Possible follow-ups:**
- How would you calculate the required FIFO depth in this scenario?
- What if the analysis shows the FIFO is borderline—how would you decide on the final depth?