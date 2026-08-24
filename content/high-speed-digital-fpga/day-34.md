# high-speed-digital-fpga — Day 34

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For asynchronous clock domains with frequently changing multi-bit data and a latency constraint, I'd first rule out simple synchronizer-based approaches since they can't guarantee coherent multi-bit transfers. The standard robust solution is an asynchronous FIFO with Gray-coded pointers — this gives you continuous data flow with bounded latency (just the FIFO fill/empty latency plus synchronization delay) and no data loss as long as the FIFO depth accommodates the maximum burst imbalance between write and read rates.

The key design considerations would be: (1) properly synchronizing the read/write pointers using two-stage flip-flop synchronizers, with Gray coding to ensure only one bit changes per pointer transition so the synchronized value is never metastable-ambiguous; (2) sizing the FIFO based on worst-case burst analysis — I'd model the maximum write burst duration versus the read rate to determine required depth, not just average rates; (3) using the FPGA vendor's FIFO IP or a well-tested asynchronous FIFO implementation rather than hand-rolling the pointer logic, since subtle corner cases in full/empty generation are notoriously difficult to get right.

For latency minimization, I'd consider whether the data truly needs to be continuous or if it arrives in packets. If packets, a smaller FIFO with an almost-empty threshold can reduce latency. If the data is truly continuous, the minimum latency is essentially the synchronization delay (2-3 destination clock cycles) plus the time to propagate through the FIFO. I'd also verify the design using formal CDC verification tools if available, since simulation alone rarely catches all CDC bugs.

**Possible follow-ups:** How would you determine the minimum FIFO depth required? What happens if the write and read clock frequencies are very close but not exactly equal (e.g., 200.000 MHz vs 200.001 MHz)?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully (DONE pin goes high) but the device does not enter the expected functional state — for example, all outputs remain tri-stated or in a default state?

**Answer:** This is a classic "configuration succeeded but initialization failed" scenario. I'd approach this systematically, starting with the most likely causes:

First, I'd verify the configuration source and settings. If using SPI flash, I'd check that the bitstream is actually the correct revision — a common issue is an old or corrupted image in flash. I'd also verify the configuration mode pins are set correctly and that the DONE pin assertion is genuine (not pulled high by external circuitry).

Next, I'd check the device initialization sequence. After DONE goes high, the FPGA typically releases the internal reset and begins initialization. If the design has a global reset that's held active — perhaps tied to a power-good signal that isn't asserting, or a watchdog that's not being serviced — the design would appear "loaded but not running." I'd probe the reset tree and check whether the clock is actually reaching the logic. A PLL that fails to lock would also prevent the design from functioning; I'd check the PLL lock status and verify the input clock is present and within spec.

I'd also look at whether the design's initialization state machine requires an external event (e.g., a configuration strobe from a host processor, or a specific input pattern) to proceed. In a multi-board system, the FPGA might be waiting for a handshake that never comes because the host side isn't ready.

Finally, I'd use the FPGA's built-in debug capabilities — ChipScope/ILA (Integrated Logic Analyzer) or SignalTap — to observe internal signals. If the design has a status register or heartbeat counter, I'd check whether it's advancing. If nothing is advancing, the clock or reset is the problem. If some things advance but not others, I'd narrow down to the specific subsystem that's stuck.

**Possible follow-ups:** How would you distinguish between a clock problem and a reset problem using an oscilloscope versus using internal logic analyzer tools? What if the design works on some boards but not others?

---

## Q3: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 1 GSPS, perform a digital down-conversion (DDC) with a programmable decimation factor, and output the result over a PCIe Gen3 x4 interface?

**Answer:** The fundamental challenge here is that 1 GSPS is far beyond the typical FPGA fabric clock rate, so I'd need to use a parallel processing architecture. My approach would be:

**Front-end capture:** The 1 GSPS data would come in as either parallel LVDS pairs (e.g., 8 pairs at 125 MHz DDR) or from a JESD204B serial interface. I'd use the FPGA's dedicated deserialization resources (ISERDES in Xilinx, or the equivalent in other vendors) to bring the data into the fabric at a manageable clock rate. For example, 16 bits at 1 GSPS could be deserialized into 16 parallel samples at 62.5 MHz, or 8 samples at 125 MHz.

**DDC implementation:** The digital down-conversion consists of three stages: mixing (multiplying by a numerically controlled oscillator, NCO), decimation filtering, and output formatting. The mixer operates on each parallel sample independently — I'd generate the NCO at the lower fabric clock rate but with phase accumulation that steps by the decimation factor each cycle. The key challenge is the decimation filter: a standard FIR running at 1 GSPS equivalent rate needs to be time-multiplexed across the parallel samples. I'd use a polyphase filter decomposition where each phase operates on a subset of the input samples at the lower clock rate. For a decimation factor of D, I'd have D polyphase filter branches, each running at 1/D of the input rate.

**PCIe output:** The decimated data rate depends on the decimation factor and output sample width. For PCIe Gen3 x4 (approximately 32 Gbps aggregate), I'd need to ensure the average output rate stays well below the sustainable PCIe bandwidth. I'd use a DMA engine with descriptor rings to stream data to host memory, with a FIFO to absorb burst variations between the DDC output and PCIe transfer scheduling.

**Key trade-offs:** The NCO phase accumulator precision determines spurious performance — I'd use at least 32-bit phase accumulation. The filter coefficients need to be programmable if the decimation factor changes. I'd also consider whether the DDC needs to support multiple channels or just one, as that affects resource utilization.

**Verification:** I'd verify the DDC against a MATLAB/Python reference model using captured test vectors, checking both the frequency response and the time-domain output for various decimation settings.

**Possible follow-ups:** How would you handle the case where the decimation factor changes on the fly? How would you verify that the polyphase filter implementation is bit-exact with a single-rate reference implementation?

---

## Q4: How would you approach designing a finite state machine (FSM) in an FPGA that must control a high-speed data path with strict latency requirements (e.g., a packet processor that must make a forwarding decision within 5 clock cycles at 400 MHz), while also being robust against single-event upsets (SEUs)?

**Answer:** This problem has two competing requirements: minimal latency and SEU robustness. The key insight is that these don't have to conflict if you choose the right architecture.

**Baseline FSM design:** For a 5-cycle decision budget at 400 MHz, the FSM itself must be purely combinational or have at most 1-2 pipeline stages — the decision logic is likely a lookup or simple comparison rather than a multi-step sequence. I'd structure the FSM so that the critical path is short: encode states in one-hot or binary format depending on the number of states, and ensure the next-state logic is minimal.

**SEU mitigation options, in order of increasing cost:**

1. **Triple Modular Redundancy (TMR) with voting:** Three copies of the FSM with majority voting on the outputs. This adds roughly 3x logic and one vote stage of latency (a few hundred picoseconds). For a 5-cycle budget, this is usually acceptable.

2. **State encoding with Hamming distance:** Use a state encoding where any single-bit upset produces either a valid state or a state that's one bit away from a valid state. Combined with a "state valid" check, this allows detection of upsets and recovery to a known state. This doesn't provide full protection but is cheaper than TMR.

3. **Watchdog-based recovery:** If the FSM is small and the decision is critical, a watchdog timer that monitors FSM progress can detect a stuck state and force a reset. This adds recovery latency but not per-decision latency.

**My recommended approach:** For a 5-cycle decision budget, I'd use TMR with a single voting stage at the output. The voting adds minimal latency (one AND-OR stage), and the three FSM copies run in parallel with no interaction until the vote. I'd also add a "state scrubber" that periodically checks all three copies are in the same state — if they diverge, it flags an error and resynchronizes them during a safe window (e.g., between packets). This catches upsets that might not immediately affect the output but could cause issues later.

For the state encoding itself, I'd use a binary encoding with a parity bit so that single-bit upsets are detectable even within a single FSM copy. This gives defense in depth: TMR handles the upset, and the parity check provides diagnostic information.

**Verification:** I'd verify the SEU robustness through fault injection — either in simulation (flipping bits in the state registers) or using the FPGA's configuration readback and frame-level bit flipping if available. I'd also verify that the voting logic itself doesn't create a timing bottleneck at 400 MHz.

**Possible follow-ups:** How would you handle the case where the three TMR copies disagree persistently (e.g., one copy is permanently stuck)? What if the 5-cycle budget is so tight that even the voting stage pushes you over?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where the engineer's reasoning is partially correct but misses a critical failure mode. I'd handle it by first acknowledging what they got right — yes, average rates matter, and the memory controller does have some buffering — then systematically walking through the burst analysis to show why the FIFO depth could be insufficient.

My approach would be: "You're right that the average rates work out, and the memory controller's write buffer does help. Let's work through the worst-case burst scenario together to verify the 64-word depth is sufficient. What's the maximum burst length the ADC can produce? What's the memory controller's sustainable write rate during a burst — not the peak rate, but the rate accounting for refresh cycles, read/write turnaround, and bank conflicts? If the ADC produces a burst of N words at rate R1, and the memory controller can only sustain rate R2 during that burst, the FIFO needs to absorb (R1 - R2) × burst_duration words. Let's plug in the actual numbers and see if 64 words covers it."

I'd also point out that the memory controller's write buffer is shared — it's also used for read data returning from memory, and if the design later adds readback functionality (which is common for verification), the write buffer availability changes. The FIFO depth should be sized for the worst case across all operating modes, not just the current configuration.

If the analysis shows the FIFO is indeed too shallow, I'd work with the engineer to determine the correct depth and discuss the trade-offs: deeper FIFO costs BRAM resources but provides margin. I'd also suggest adding a watermark interrupt or status flag so the system can detect when the FIFO is approaching full — this turns a potential silent data loss into a detectable event.

Throughout this, I'd maintain a collaborative tone — the goal is to build the engineer's understanding of burst analysis, not to override them. I'd frame it as "let's verify this together" rather than "you're wrong." If the engineer still resists after the analysis shows a problem, I'd escalate to requiring the fix as a condition of design sign-off, since data loss in an acquisition system is a functional failure.

**Possible follow-ups:** How would you handle the situation if the engineer's burst analysis shows the FIFO is actually sufficient, but you still have concerns about future changes to the system? How would you document this design decision for future reviewers?