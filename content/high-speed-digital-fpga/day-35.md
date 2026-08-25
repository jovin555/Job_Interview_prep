# high-speed-digital-fpga — Day 35

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For asynchronous clock domains with frequently changing multi-bit data and strict latency requirements, the fundamental trade-off is between latency and safety. The most robust approach is an asynchronous FIFO with gray-coded pointers — this is the standard solution because it handles continuous data flow with bounded latency (essentially just the FIFO fill/unfill time plus synchronization delay).

The key design decisions are:

1. **FIFO depth calculation**: I'd analyze the worst-case burst behavior — the maximum number of words that can arrive before the read side can drain them, plus synchronization latency (typically 2-3 destination clock cycles for pointer synchronization). The depth must accommodate the difference between peak write rate and sustainable read rate over any time window.

2. **Pointer synchronization**: Write pointer is synchronized into the read domain (and vice versa) using two-stage flip-flop synchronizers. Using gray-coded pointers ensures that only one bit changes at a time, so even if a metastable event occurs on one bit, the resulting pointer value is still valid (either old or new value, never a corrupted intermediate).

3. **Full/empty generation**: These must be generated in the respective domains — full in the write domain using synchronized read pointer, empty in the read domain using synchronized write pointer. This adds conservative margin (the FIFO appears slightly fuller/emptier than it actually is) but prevents overflow/underflow.

4. **Latency optimization**: If latency is critical, I'd consider whether the frequency relationship is truly asynchronous or just phase-uncertain. If there's a known frequency ratio, a synchronous FIFO with carefully managed read/write enables can reduce latency. For truly asynchronous clocks, the minimum latency is set by the synchronization requirement — you can't safely reduce below two destination clock cycles for pointer sync.

5. **Verification**: I'd run formal CDC verification tools to prove no unsynchronized paths exist, plus constrained-random simulation with clock jitter and phase variation to stress the FIFO at its boundaries.

**Possible follow-ups:** How would you handle the case where the data bus is too wide for practical gray-coding? What if the read side can stall indefinitely — how does that affect your design?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design's internal state machine appears to be stuck in an illegal state only when a specific external input sequence occurs, and the issue is not reproducible in RTL simulation?

**Answer:** This is a classic "works in simulation, fails in hardware" scenario, and the debugging approach needs to systematically narrow down whether the issue is in the RTL logic, the constraints, or the physical implementation.

My approach would be:

1. **First, verify the input sequence is actually reaching the FSM as intended.** I'd use the FPGA's built-in logic analyzer (e.g., ChipScope/SignalTap) to capture the actual signals at the FSM inputs. A common cause is that the external input has different timing than assumed — perhaps a glitch, a slow rise time causing multiple transitions, or an asynchronous input that violates setup/hold. The FSM might be entering an illegal state because it's seeing a different sequence than the RTL simulation assumed.

2. **Check for missing CDC synchronization.** If the external input is truly asynchronous to the FSM clock, the RTL simulation might not model metastability. A metastable event can cause the FSM to enter an illegal state. I'd verify that all external inputs are properly synchronized before entering the FSM.

3. **Examine the FSM encoding and default handling.** If the FSM uses one-hot or binary encoding, I'd check whether the synthesis tool optimized away the "illegal state" recovery logic. Sometimes synthesis tools assume illegal states are unreachable and optimize the recovery paths away. I'd verify the synthesis report to see if the FSM was re-encoded or if recovery logic was removed.

4. **Check timing closure on the FSM paths.** If the FSM logic has timing violations, the state registers can capture incorrect values under specific input conditions. I'd review the timing report for the FSM's paths, particularly the next-state logic.

5. **Add observability and recovery.** I'd add a debug version of the FSM with a status register that captures the current state and recent inputs, plus a hardware-triggered reset to a known-good state. This helps both diagnose the issue and provide a safety net.

6. **If the issue is reproducible but not in RTL simulation, I'd create a more accurate simulation model** — adding realistic input timing, jitter, and possibly gate-level simulation with back-annotated delays to see if the issue appears.

**Possible follow-ups:** How would you decide between adding a watchdog timer versus fixing the root cause? What if the illegal state only occurs once every several hours of operation?

---

## Q3: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** This is a demanding PDN requirement — 20A at 0.85V with 1A/ns slew rate means the core rail must handle very fast current transients while maintaining tight voltage tolerance. The approach needs to address both the DC (IR drop) and AC (impedance) aspects.

**DC analysis:**
- The total budget is ±3% of 0.85V = ±25.5mV. I'd allocate roughly half of that to DC IR drop and half to AC transient response.
- For DC, I'd calculate the resistance from the regulator output through the PCB planes, vias, and package to the FPGA core. With 20A, even 0.5mΩ of resistance causes 10mV drop. This means multiple parallel vias, solid copper planes (not split), and the regulator placed close to the FPGA.
- I'd use a remote sense connection to the regulator to compensate for the static IR drop between the regulator output and the FPGA.

**AC analysis — target impedance:**
- The standard approach is to define a target impedance: Z_target = ΔV / ΔI = (0.03 × 0.85V) / 20A ≈ 1.3mΩ. This is the maximum impedance the PDN can present across the frequency range of interest.
- The frequency range matters: with 1A/ns slew rate, the transient has significant energy up to roughly 100MHz or higher. The PDN impedance must stay below target across this entire range.

**Implementation strategy:**
- **Bulk capacitance** (electrolytic or polymer) near the regulator handles low-frequency transients (below ~100kHz).
- **Ceramic capacitors** in the 10-100µF range (multiple in parallel) handle mid-frequency (100kHz to ~10MHz). I'd use multiple values (e.g., 100µF, 22µF, 4.7µF) to create overlapping impedance minima.
- **High-frequency decoupling** (0.1µF, 0.01µF) placed very close to the FPGA power pins handles the highest frequencies. These must be on the same side as the FPGA or connected with minimal via inductance.
- **PCB plane capacitance** from closely spaced power/ground planes provides additional high-frequency decoupling.

**Verification:**
- I'd perform a PDN impedance simulation using the PCB stack-up, plane geometry, via placement, and capacitor models (including ESL/ESR). The goal is to show Z(f) < 1.3mΩ across the frequency range.
- I'd also run a transient simulation with a current source model of the FPGA's worst-case switching pattern.
- On the bench, I'd measure with a high-bandwidth oscilloscope using a coaxial probe at the FPGA core pins, while running a test pattern that maximizes current transients (e.g., toggling all logic simultaneously).

**Key pitfalls to avoid:**
- Via inductance between the capacitor and the FPGA power pin is often the limiting factor. Multiple parallel vias reduce this.
- Anti-pads on the power plane can create impedance spikes.
- The regulator's loop response must be stable with the total capacitance — I'd check the regulator's stability requirements.

**Possible follow-ups:** How would you decide between using more PCB layers versus more capacitors? How would you handle the case where the regulator's transient response alone can't meet the requirement?

---

## Q4: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a 64-tap FIR filter, and output the filtered result without any dropped samples, while also meeting timing at the target clock frequency?

**Answer:** The fundamental challenge here is that 500 MSPS exceeds the typical FPGA fabric clock rate — most FPGAs can't run general logic at 500MHz. The solution requires parallel processing: either time-division multiplexing with multiple parallel filter chains or using the FPGA's DSP slice architecture efficiently.

**Architecture options:**

1. **Parallel processing (most common):** If the fabric clock is 250MHz, I'd split the input stream into two parallel paths, each processing every other sample. Each path runs a 64-tap FIR at 250MHz. The filter coefficients are split — even taps in one path, odd taps in the other — and the outputs are combined with the appropriate delay alignment. This is a polyphase decomposition of the filter.

2. **If the fabric clock is 125MHz:** I'd use four parallel paths with a 4-way polyphase decomposition. Each path processes every 4th sample.

3. **DSP slice utilization:** Modern FPGAs have DSP slices that can implement multiply-accumulate operations efficiently. A 64-tap filter at 250MHz with 16-bit data and coefficients requires 64 MACs per output sample. With two parallel paths, that's 128 MACs total. I'd check the DSP slice count and whether the device has enough resources. If not, I'd consider using block RAM-based distributed arithmetic or a systolic array architecture.

**Key design considerations:**

- **Input deserialization:** The 500MSPS input needs to be captured and demultiplexed into the parallel paths. This typically uses the FPGA's I/O serializer/deserializer (ISERDES) resources, which can capture DDR data at high rates.

- **Coefficient management:** For a polyphase decomposition, the coefficients are split across paths. I'd verify the filter response matches the original by simulating the decomposed filter against the reference.

- **Output recombination:** The parallel filter outputs must be interleaved in the correct order to reconstruct the 500MSPS output stream. This requires careful delay alignment — each path has a different inherent delay.

- **Timing closure:** At 250MHz, I'd need to pipeline the multiply-accumulate chains appropriately. The DSP slices have built-in pipeline registers that can be used to break long combinational paths. I'd also consider using the FPGA's dedicated filter structures if available.

- **Verification:** I'd create a bit-exact simulation model of the parallel architecture and compare against a reference C model of the original filter. I'd test with impulse, step, and random inputs, plus check for dropped samples by counting input vs. output samples over long runs.

**Possible follow-ups:** How would you handle the case where the filter coefficients need to be dynamically updated? What if the FPGA doesn't have enough DSP slices — what alternatives would you consider?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where a junior engineer has made a design decision based on average-case analysis rather than worst-case behavior, and I need to address both the technical issue and the engineering approach.

**My approach:**

1. **Acknowledge the valid reasoning first.** The engineer is correct that average rates matter and that the memory controller's write buffer provides some burst absorption. Starting with what's right about their analysis keeps the conversation collaborative rather than confrontational.

2. **Reframe the question around worst-case analysis.** I'd ask: "What happens if the ADC produces its maximum burst — say, a full frame of data at maximum rate — while the memory controller is simultaneously servicing a refresh cycle or a read operation? Can you walk me through the timing?" This guides them to think about the interaction between burst behavior and memory controller availability.

3. **Work through the math together.** I'd ask the engineer to calculate: (a) the maximum burst size the ADC can produce, (b) the memory controller's sustainable write rate during worst-case conditions (including refresh overhead and bank conflicts), and (c) the combined buffering of the FIFO plus the memory controller's write buffer. If the math shows the FIFO is sufficient, I'd accept the design — but the point is that the analysis needs to be done explicitly.

4. **Discuss the failure mode.** If the FIFO does overflow, what happens? Data is dropped — and in a data acquisition system, that might mean corrupted measurements or lost events. I'd ask the engineer to consider whether the system has any mechanism to detect and handle dropped data, or if it would silently corrupt the acquisition.

5. **Suggest a structured approach.** Rather than just saying "make the FIFO bigger," I'd suggest the engineer document the worst-case burst analysis, including the memory controller's refresh timing and the ADC's maximum burst specifications. This creates a design artifact that can be reviewed and verified.

6. **If the analysis shows the FIFO is insufficient, I'd discuss options:** increasing FIFO depth, adding a flow-control mechanism (e.g., backpressure to the ADC), or using a more sophisticated buffering scheme. The decision should be based on the analysis, not on intuition.

**The broader lesson:** This is about teaching worst-case analysis as a habit, not just fixing this one instance. I'd encourage the engineer to always ask "what's the worst case?" when designing buffering and flow control, and to document the analysis so it can be reviewed.

**Possible follow-ups:** How would you handle the situation if the engineer pushes back and says the analysis is overkill for this application? What if the project schedule doesn't allow time for a deeper analysis?