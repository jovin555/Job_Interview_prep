# high-speed-digital-fpga — Day 20

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a wide data bus (e.g., 128-bit) transferring continuously between two asynchronous clock domains, where the data must be delivered with bounded latency and no data loss?

**Answer:** For continuous, high-throughput data transfer between asynchronous clock domains with bounded latency, I'd first characterize the frequency relationship. If the clocks are truly asynchronous with no known phase relationship, an asynchronous FIFO is the standard solution. The key design decisions are FIFO depth, gray-code pointer synchronization, and read/write side logic.

For the FIFO depth, I'd analyze the worst-case burst scenario: the maximum number of writes that can occur before the read side drains data, considering the frequency ratio and any jitter or clock drift. The depth must accommodate the full round-trip latency of the synchronization chain (typically 2-3 clock cycles per side for pointer synchronization) plus any burst accumulation. For a 128-bit wide bus, I'd also consider using multiple narrower FIFOs in parallel if the FPGA fabric has limited block RAM width, but I'd ensure they're all managed as a single logical FIFO to maintain data ordering.

For pointer synchronization, I'd use gray-code encoding so that only one bit changes between consecutive pointer values, eliminating the risk of capturing a partially-updated multi-bit value. The read pointer is synchronized to the write clock domain and vice versa. I'd add a "full" and "empty" flag generation circuit that uses the synchronized pointers with appropriate register stages to avoid metastability.

For bounded latency, I'd avoid any handshaking or credit-based flow control that could stall the data path. Instead, I'd rely on the FIFO to absorb rate mismatches and ensure the read side always has data available. I'd also verify the design with formal CDC verification tools to check for synchronization issues, and run simulation with randomized clock phase offsets to stress-test the design.

**Possible follow-ups:**
- How would you determine the minimum FIFO depth analytically for a given frequency ratio and burst size?
- What happens if the read side temporarily stops consuming data — how does that affect your depth calculation?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design intermittently produces incorrect results only when the board is subjected to mechanical vibration?

**Answer:** Intermittent failures under vibration point strongly to a physical/mechanical issue rather than a logic or timing problem. Since the bitstream loads successfully and the design works most of the time, I'd suspect marginal electrical connections that degrade under mechanical stress.

My first step would be to reproduce the issue in a controlled environment. I'd set up the board on a vibration table and monitor key signals while the failure occurs. I'd use a logic analyzer or oscilloscope to capture the failing data path, looking for glitches, missing transitions, or corrupted values.

The most likely culprits are: (1) marginal solder joints on high-pin-count components like the FPGA, DDR memory, or connectors; (2) loose board-to-board connectors; (3) cracked or damaged vias; or (4) insufficient mechanical support causing PCB flexure that stresses BGA balls or component leads.

I'd start by inspecting the board visually and with X-ray if available, focusing on BGA joints and connector solder points. I'd also check for proper mechanical mounting — standoffs, stiffeners, and connector strain relief. If the design uses a mezzanine or board-to-board connector, I'd verify the mating force and alignment.

For electrical debugging, I'd add test points or use existing debug headers to monitor critical signals during vibration. I'd look for intermittent opens on power rails (causing brownouts) or on high-speed signal paths. A useful technique is to run a loopback test on the failing interface — for example, writing a known pattern to memory and reading it back continuously while vibrating the board, then correlating failures with specific vibration frequencies or amplitudes.

If I suspect a marginal solder joint, I could try applying localized pressure with a non-conductive probe to specific components while the board is running — this often reproduces the failure and helps isolate the location. Thermal cycling combined with vibration can also help expose marginal connections.

**Possible follow-ups:**
- How would you distinguish between a mechanical issue and a marginal timing issue that only manifests under vibration-induced clock jitter?
- What design changes would you recommend to prevent this class of problem in future revisions?

---

## Q3: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a 64-tap FIR filter, and output the filtered result without any dropped samples, while also meeting timing at the target clock frequency?

**Answer:** The first challenge is that 500 MSPS exceeds the typical maximum clock frequency for general FPGA fabric — most FPGAs top out around 300-400 MHz for complex logic. So I'd need to use a parallel processing architecture. The standard approach is time-division multiplexing: process multiple samples per clock cycle.

For a 500 MSPS stream with a 250 MHz fabric clock, I'd process two samples per clock cycle. For 125 MHz fabric clock, I'd process four samples per cycle. Let me walk through the two-sample-per-cycle case as an example.

The 64-tap FIR filter can be decomposed into two parallel polyphase sub-filters, each handling one of the two input samples per clock cycle. Each sub-filter would have 32 taps (since the filter is decimated by 2). The polyphase decomposition splits the original filter coefficients into even-indexed and odd-indexed coefficients, and each sub-filter operates on the appropriate phase of the input stream.

For implementation, I'd use DSP slices for the multiply-accumulate operations. A 32-tap filter per sub-filter would require 32 multipliers and 32 adders if fully parallel, which is substantial but feasible on modern FPGAs. Alternatively, I could use a time-multiplexed approach within each sub-filter if DSP resources are limited, but that would require a higher internal clock rate.

The key timing challenge is the adder tree for summing the 32 partial products. I'd pipeline the adder tree to meet timing — for example, using a balanced tree with register stages between levels. This adds latency but doesn't affect throughput since the data is continuous.

I'd also need to handle the input data capture correctly. The ADC data arrives at 500 MSPS, so I'd use an I/O serializer/deserializer (ISERDES) to capture two samples per clock cycle into the fabric. The output would similarly use an OSERDES to serialize the filtered results back to 500 MSPS if needed.

For verification, I'd create a bit-exact simulation model in a high-level language (Python or C) and compare against the FPGA implementation with randomized input data. I'd also verify the polyphase decomposition mathematically — the sum of the two sub-filter outputs must exactly match the original filter's output.

**Possible follow-ups:**
- How would the architecture change if you needed to process 1 GSPS instead of 500 MSPS?
- How would you handle the filter's group delay when the two polyphase paths have different latencies?

---

## Q4: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** This is a demanding PDN requirement — 20A at 0.85V with 1A/ns slew rate means the voltage must stay within 25.5mV of nominal (3% of 850mV). The key challenge is managing the transient response: when the current demand changes rapidly, the PDN impedance must be low enough that the voltage drop (ΔV = Z × ΔI) stays within tolerance.

My approach would be multi-layered, addressing the problem at the VRM, board, and package levels.

**VRM selection:** The voltage regulator must have sufficient bandwidth to respond to the transient. A multi-phase buck converter with a high switching frequency (500 kHz to 1 MHz or higher) and fast transient response is essential. I'd also consider using a VRM with remote sensing to compensate for board-level voltage drops. The VRM's output capacitance and loop compensation need to be designed for the worst-case transient — a load step from 10% to 90% of 20A.

**Bulk capacitance:** On the board, I'd place bulk capacitors (tantalum or ceramic, typically 100-470 µF total) near the FPGA to handle the initial transient before the VRM loop can respond. The bulk capacitance provides the charge reservoir for the first few microseconds of a transient.

**High-frequency decoupling:** For the fast slew rate (1A/ns), the high-frequency decoupling is critical. I'd use a combination of capacitor values — typically 100 nF, 10 nF, and 1 nF — placed as close to the FPGA power pins as possible. The goal is to keep the impedance low across a wide frequency range. I'd use a target impedance calculation: Z_target = ΔV / ΔI = 25.5mV / 20A ≈ 1.3 mΩ. This impedance must be maintained from DC up to the frequency where the on-die capacitance takes over (typically 100-300 MHz).

**PCB stack-up and plane design:** The power and ground planes must be designed as closely coupled parallel planes to minimize inductance. I'd use a thin dielectric between the core power plane and ground (e.g., 2-4 mil prepreg) to maximize plane capacitance. Multiple vias connecting the FPGA power pins to the planes are essential — I'd use a via array with vias spaced no more than 40-50 mils apart to minimize via inductance.

**Simulation and verification:** I'd perform PDN simulation using tools like SIwave or PowerSI to model the impedance vs. frequency profile. The simulation would include the VRM output impedance, bulk capacitors, high-frequency decoupling, plane capacitance, and package parasitics. I'd verify that the impedance stays below the target across the frequency range of interest. I'd also run time-domain transient simulations with a current step to verify the voltage stays within tolerance.

**Measurement:** On the physical board, I'd use a high-bandwidth oscilloscope (1 GHz or higher) with a low-inductance probe to measure the core voltage during a worst-case transient. I'd also use a network analyzer to measure the PDN impedance and correlate with simulation.

**Possible follow-ups:**
- How would you determine the optimal capacitor values and quantities for the decoupling network?
- What role does the FPGA package play in the PDN, and how would you account for it in your design?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a classic design review situation where a junior engineer has made a reasonable but incomplete analysis. The core issue is that the engineer is reasoning about average rates when the system's behavior is defined by worst-case bursts. I'd handle this by guiding the engineer to a more rigorous analysis without dismissing their work.

First, I'd acknowledge the valid part of their reasoning — the average write rate being below the read rate is a necessary condition, but it's not sufficient. I'd then walk through the worst-case scenario together: what happens when the ADC produces a maximum-length burst? The memory controller's write buffer has a finite depth, and under sustained write traffic, the controller may need to perform refresh cycles, bank precharges, or read-modify-write operations that temporarily stall writes. If the FIFO depth is insufficient, data will be lost.

I'd ask the engineer to calculate the worst-case burst duration and the memory controller's sustainable write rate during that burst, accounting for refresh overhead and bank conflicts. I'd also ask them to consider the round-trip latency of the FIFO's full/empty flag propagation — the read side can't start draining until it sees the full flag, which takes several clock cycles.

Rather than just telling them the answer, I'd guide them through the calculation. If they can't determine the memory controller's worst-case write latency, I'd suggest they check the controller's documentation or run a simulation with a worst-case traffic pattern. I'd also suggest adding a watermark-based flow control — for example, asserting backpressure to the ADC when the FIFO reaches 75% full, rather than waiting for the FIFO to be completely full.

If the analysis confirms the FIFO is too shallow, I'd work with the engineer to determine the correct depth. I'd also suggest adding a test mode that generates worst-case burst patterns to verify the design under stress conditions.

The key is to turn this into a learning opportunity — the engineer needs to understand that in high-speed data paths, you design for worst-case behavior, not average behavior. I'd also make a note to include burst analysis as a standard checklist item for future design reviews.

**Possible follow-ups:**
- How would you help the engineer calculate the worst-case burst duration and the memory controller's sustainable write rate?
- What design changes would you suggest beyond increasing the FIFO depth — for example, would you consider a different flow control mechanism?