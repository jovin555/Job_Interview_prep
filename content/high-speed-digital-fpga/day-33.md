# high-speed-digital-fpga — Day 33

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a pulse-based signal that must be transferred from a 25 MHz domain to a 250 MHz domain, where the pulse width is exactly one cycle of the source clock and pulses can arrive back-to-back?

**Answer:** This is a classic narrow-pulse CDC problem where the source pulse is too narrow to reliably sample with a simple two-flop synchronizer in the destination domain. The key constraint is that pulses can arrive back-to-back, so we can't use a toggle-based approach that would miss a second pulse arriving before the destination domain reads the first one.

My approach would be to use a pulse stretcher or a small asynchronous FIFO. For the pulse stretcher approach: in the source domain, I'd set a flag (or "pending" bit) when a pulse arrives. The flag stays asserted until I receive an acknowledgment from the destination domain. The destination domain samples this flag with a two-flop synchronizer, detects the rising edge, and generates the output pulse, then sends an acknowledgment back through another synchronizer. The source domain clears the flag only after receiving the acknowledgment. This guarantees no pulses are missed, even with back-to-back pulses, because the flag remains set until the first pulse is fully consumed.

However, the round-trip latency of the handshake can be a bottleneck. If the pulse rate is high relative to the synchronization latency, the handshake approach breaks down. In that case, I'd use a small asynchronous FIFO — even 2-4 entries deep — where the source domain writes a token for each pulse and the destination domain reads tokens and regenerates pulses. This decouples the timing and handles bursts naturally.

A critical detail is that the flag or FIFO write must be properly synchronized — the source domain must not clear the flag while the destination is still sampling it, and the FIFO pointers need proper gray-code or handshake-based synchronization. I'd also verify the design with formal CDC verification tools or at minimum with constrained-random simulation that exercises back-to-back pulses at worst-case timing corners.

**Possible follow-ups:** How would you determine whether a handshake or FIFO approach is more appropriate for a given pulse rate? What would happen if the destination domain clock is stopped or gated for extended periods?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design's internal state machine appears to be stuck in an illegal state only when a specific external input sequence occurs, and the issue is not reproducible in RTL simulation?

**Answer:** This is a frustrating class of problem because the design works in simulation but fails in hardware under specific conditions. I'd approach this systematically:

First, I'd try to capture the actual behavior using the FPGA's built-in logic analyzer (e.g., ChipScope, SignalTap, or Vivado ILA). I'd instrument the state machine's state register, key inputs, and outputs, and trigger on the conditions that lead to the failure. This tells me whether the state machine is truly in an illegal state or whether it's a downstream issue.

Second, I'd look for differences between simulation and hardware. Common culprits include: uninitialized state registers (simulation may initialize to zero, but hardware powers up randomly), missing resets, asynchronous inputs that aren't synchronized, or combinatorial logic producing glitches that violate setup/hold times. I'd check whether the state machine has a proper reset applied at configuration, and whether all external inputs are synchronized before entering the FSM.

Third, I'd examine the specific input sequence. If the sequence involves multiple inputs changing simultaneously, there could be a race condition in the combinational logic that computes the next state. In simulation, inputs change at discrete times, but in hardware, skew between input pins can create intermediate states that the FSM sees. I'd add input synchronization and possibly register the next-state logic to break any long combinational paths.

Fourth, I'd verify the timing constraints. If the FSM's next-state logic has a timing violation, the state register could capture a metastable or incorrect value. I'd check the timing report for the FSM paths and consider whether the clock frequency is too aggressive for the logic depth.

Finally, if the state machine can reach an illegal state, I'd add a recovery mechanism — either a watchdog timer that forces a reset if the FSM doesn't reach a valid state within a timeout, or explicit illegal-state recovery transitions in the case statement. This is good defensive design practice even if the root cause is never fully identified.

**Possible follow-ups:** How would you go about reproducing the issue in simulation once you've captured the hardware behavior? What specific simulation techniques would you use to model input skew or glitches?

---

## Q3: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 8-bit samples at 800 MSPS, perform a 32-tap FIR filter, and output the filtered result without any dropped samples, while the FPGA fabric clock is limited to 200 MHz?

**Answer:** The key challenge here is that the sample rate (800 MSPS) is four times the fabric clock rate (200 MHz), so we can't process one sample per clock cycle. This requires a parallel processing architecture.

My approach would be to use time-division multiplexing with four parallel processing lanes. The input deserializer would capture four consecutive samples per clock cycle (at 200 MHz), producing a 32-bit wide vector (4 × 8-bit samples). The FIR filter would then be decomposed into four parallel filter banks, each processing one of the four phases. This is a polyphase decomposition of the FIR filter.

For a 32-tap FIR filter with 4× parallelism, each of the four output phases needs to compute a sum of 8 products (32 taps / 4 phases). Each phase's filter operates on every 4th sample, so the effective filter length per phase is 8 taps. The four phases together reconstruct the full 32-tap filter response.

The implementation would use DSP slices for the multiply-accumulate operations. Each phase needs 8 multipliers, so 32 multipliers total. The DSP slices in modern FPGAs can easily run at 200 MHz with pipelining. I'd pipeline the adder tree to meet timing — typically 2-3 pipeline stages for an 8-input adder tree.

The critical detail is managing the data alignment. The input samples arrive sequentially, and the polyphase decomposition requires that each phase sees the correct subset of samples with the correct delay. I'd use shift registers or block RAM to implement the delay lines, ensuring each phase has access to the samples it needs.

I'd also verify the implementation against a bit-exact reference model in simulation. The polyphase decomposition must produce identical results to the original filter, and I'd test with impulse inputs, random data, and edge cases like DC and Nyquist-frequency inputs.

For the output, I'd serialize the four parallel results back to a continuous 800 MSPS stream using the FPGA's output serializer (OSERDES) or by connecting to a high-speed DAC interface.

**Possible follow-ups:** How would the architecture change if the filter needed to be reconfigurable (e.g., programmable coefficients)? How would you handle the case where the sample rate isn't an integer multiple of the fabric clock?

---

## Q4: How would you approach designing a finite state machine (FSM) in an FPGA that must control a high-speed data path with strict latency requirements (e.g., a packet processor that must make a forwarding decision within 5 clock cycles at 400 MHz), while also being robust against single-event upsets (SEUs)?

**Answer:** This is a challenging combination because SEU mitigation typically adds logic and latency, which conflicts with the strict timing budget. I'd approach this by separating the concerns: the critical path must be fast, but the state machine itself can be designed to recover from errors without slowing down the normal path.

First, I'd design the FSM with a one-hot encoding rather than binary encoding. In one-hot encoding, only one bit is active at a time, which means an SEU that flips a bit either sets an unused state (detectable) or clears the current state (also detectable). This makes error detection simpler than with binary encoding where a bit flip can silently transition to another valid state.

For the latency constraint, I'd keep the critical path minimal: the next-state logic should be simple combinational logic based on a small set of inputs, and the state register should be a simple flip-flop. I would not add triple-module redundancy (TMR) to the entire FSM because the voting logic would add latency. Instead, I'd use a "watchdog + recovery" approach:

1. The FSM runs normally with minimal logic on the critical path.
2. A separate watchdog timer (running in parallel, not on the critical path) monitors the FSM. If the FSM doesn't reach a known-good state within a specified number of cycles (longer than the maximum legitimate dwell time in any state), the watchdog forces a reset to a safe state.
3. I'd also add explicit illegal-state detection: since one-hot encoding has unused states, I can detect when two bits are active simultaneously or when the state vector doesn't match any valid state, and trigger recovery.

For the recovery action, I'd design the FSM to have a well-defined "safe" state that it can jump to, with a defined re-initialization sequence. The key is that the recovery path is not on the critical data path — it only activates on error.

If the application truly requires continuous operation without any errors propagating, I'd consider selective TMR: triplicate only the state register and use a majority voter, but keep the next-state logic single. The voter adds one gate delay, which might be acceptable if the timing margin allows. I'd evaluate this trade-off based on the actual timing slack.

Finally, I'd verify the design with fault injection — either in simulation by flipping bits in the state register, or using the FPGA's configuration memory readback and frame-level fault injection capabilities. This validates that the recovery mechanism works for all possible single-bit upsets.

**Possible follow-ups:** How would you choose between one-hot encoding with watchdog recovery versus full TMR for the state register? What if the watchdog timeout itself is corrupted by an SEU?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a situation where I need to address both the technical concern and the engineer's reasoning process. The core issue isn't just the FIFO depth — it's that the engineer is relying on average rates rather than worst-case burst behavior, which is a fundamental misunderstanding of how asynchronous data paths fail.

First, I'd acknowledge what the engineer got right: the average write rate being below the read rate is a necessary condition for the design to work. But it's not sufficient. The FIFO depth must be sized for the worst-case burst scenario, not the average. I'd walk through the math together: if the ADC can produce a burst of N samples at full rate, and the memory controller can only sustain M samples per burst before its write buffer fills, then the FIFO must absorb N minus M samples. If N is larger than 64 plus the memory controller's buffer depth, the FIFO will overflow and data will be lost.

I'd also point out that the memory controller's write buffer is not a reliable "shock absorber" — it has its own finite depth and its own burst limitations. When the memory controller is busy refreshing or servicing reads, its sustainable write rate drops, and the write buffer fills faster. The engineer's assumption that the write buffer will absorb bursts needs to be verified against the memory controller's worst-case behavior, not assumed.

Rather than just rejecting the design, I'd turn this into a collaborative exercise. I'd ask the engineer to derive the worst-case burst scenario from the ADC's datasheet and the memory controller's specifications, then calculate the required FIFO depth. I'd suggest they create a spreadsheet or a simple model that accounts for: maximum ADC burst length, memory controller write buffer depth, refresh cycle impact, and read/write turnaround penalties. This gives the engineer ownership of the solution and teaches them the analytical approach.

If the analysis shows the FIFO is indeed too small, the fix might be a larger FIFO, or it might be a more sophisticated flow-control mechanism — for example, a pause signal to the ADC when the FIFO reaches a high-water mark, or a small elastic buffer plus a DMA engine that batches writes more efficiently. The right solution depends on the actual numbers.

I'd also use this as a teaching moment about design reviews: the goal isn't to catch people making mistakes, but to catch potential failures before they reach the hardware. I'd encourage the engineer to always ask "what's the worst case?" when evaluating buffering and flow control, and to document their assumptions so reviewers can verify them.

**Possible follow-ups:** How would you handle the situation if the engineer's analysis shows the FIFO is adequate but only by a small margin (e.g., 5% headroom)? What if the engineer becomes defensive and insists their original design is correct?