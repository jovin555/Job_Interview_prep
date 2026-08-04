# high-speed-digital-fpga — Day 14

## Q1: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design functions correctly at room temperature and fails only when the board is heated to its maximum specified operating temperature?

**Answer:** This is a classic temperature-dependent failure that points to marginal timing or analog parameters rather than a functional logic error. My approach would be systematic:

First, I'd characterize the failure precisely — what exactly fails, at what temperature threshold, and whether it's reproducible or intermittent. This tells me whether I'm looking at a setup/hold timing margin issue, a PLL/DLL lock or jitter problem, or a power delivery issue (voltage droop under thermal stress).

Next, I'd review the timing closure reports with attention to the paths that have the least margin. The key insight is that timing margins shrink with temperature — both because of increased propagation delays in silicon and because of changes in on-die termination and I/O driver characteristics. I'd look for paths that passed timing closure with only a few picoseconds of margin, as these are the first to fail.

I'd also examine the clocking infrastructure. PLLs and MMCMs have temperature-dependent characteristics, and a PLL that's marginally locked at room temperature may lose lock or produce excessive jitter at elevated temperatures. I'd check the PLL lock status and measure the actual clock jitter at temperature if possible.

For the power delivery side, I'd verify that all supply voltages remain within specification at temperature. Some regulators have thermal derating that can cause voltage droop under load at elevated temperatures, which directly erodes timing margin.

Finally, I'd review the I/O standards and termination schemes. SSTL and HSTL interfaces, for example, have temperature-dependent voltage thresholds, and marginal reference voltages can cause intermittent failures at temperature.

The fix typically involves one or more of: adding pipeline stages to critical paths, tightening timing constraints to force the tools to give more margin, improving the power delivery network, or adjusting I/O drive strength and slew rate settings.

**Possible follow-ups:**
- How would you distinguish between a timing margin issue and a power integrity issue as the root cause?
- What specific measurements would you take on the board to confirm your hypothesis before making changes?

---

## Q2: How would you approach designing a finite state machine (FSM) in an FPGA that must control a safety-critical function, where the FSM must be able to detect and recover from an illegal state caused by a single-event upset (SEU) in the configuration memory or logic elements?

**Answer:** For a safety-critical FSM in an FPGA, the design must assume that upsets can occur and must be able to detect and recover from them. My approach would combine several layers of protection:

**Encoding:** The first decision is the state encoding. One-hot encoding is common in FPGAs because it's fast and uses flip-flops efficiently, but it's vulnerable to SEUs — a single bit flip can create an illegal state. For safety-critical FSMs, I'd consider using a Hamming-distance-based encoding where all valid states are separated by a minimum Hamming distance of at least 3, allowing single-error detection and correction. Alternatively, a triple modular redundancy (TMR) approach with three copies of the FSM and a voter can be effective, though it triples the resource usage.

**Detection:** I'd add explicit illegal-state detection logic. This can be done with a combinational check that asserts an error flag when the current state doesn't match any valid state encoding. For Hamming-encoded states, the detection logic can also identify single-bit errors and correct them.

**Recovery:** The recovery strategy depends on the application's safety requirements. For a truly safety-critical function, the FSM should transition to a safe state (e.g., a "safe shutdown" state) rather than attempting to resume normal operation, because the system state may be corrupted. For less critical functions, the FSM could attempt to correct the error and resume, but this requires careful analysis of what side effects the corrupted state may have caused.

**Additional considerations:** I'd also consider using a watchdog timer that monitors FSM progress — if the FSM doesn't reach an expected state within a specified time, it triggers a reset. The FSM outputs should be registered and, where possible, encoded with parity or CRC to detect corruption at the output boundary. Finally, I'd verify the design with fault injection testing — deliberately flipping bits in simulation to confirm that the detection and recovery logic works for all possible single-bit upsets.

**Possible follow-ups:**
- How would you decide between TMR and Hamming-encoded state machines for a given application?
- What role does the configuration memory (CRAM) play in SEU vulnerability, and how would you protect against upsets in the configuration bits that implement the FSM logic?

---

## Q3: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 500 MSPS, perform a finite impulse response (FIR) filter with 64 taps, and output the filtered result without any dropped samples?

**Answer:** This is a throughput-constrained problem where the fundamental challenge is that a 64-tap FIR filter at 500 MSPS requires 32 billion multiply-accumulate operations per second. No single DSP slice can sustain that rate, so the design must use parallelism and pipelining.

**Architecture selection:** The first decision is the filter architecture. A direct-form FIR requires 64 multipliers and 64 adders per output sample. At 500 MSPS, this means the entire filter must compute in 2 ns. That's not feasible in a single clock cycle. The standard approach is to use a polyphase decomposition or a systolic architecture where the filter is broken into multiple parallel processing lanes.

For a 64-tap filter at 500 MSPS, I'd consider a polyphase implementation with, say, 4 parallel lanes, each processing at 125 MHz. Each lane handles 16 of the 64 taps, and the partial results are combined. This reduces the clock rate to a manageable level while maintaining the same throughput.

**Resource utilization:** I'd map the multipliers to DSP slices. Modern FPGAs have DSP slices that can operate at several hundred MHz, so a 125 MHz lane clock is well within their capability. I'd also consider using the DSP slices' built-in pre-adder and accumulator features to reduce logic utilization.

**Pipelining:** The key to meeting timing is aggressive pipelining. Each multiply-accumulate stage should be registered, and the adder tree that combines partial results should be pipelined to keep the critical path short. The latency increases, but for a streaming application, latency is usually acceptable as long as throughput is maintained.

**Verification:** I'd verify the design in stages: first, a bit-exact simulation against a C reference model to confirm the filter coefficients and arithmetic are correct; second, a timing analysis to confirm the design meets the 125 MHz lane clock; and third, a hardware test with known input patterns to confirm the output matches the reference.

**Possible follow-ups:**
- How would you handle the filter coefficients if they need to be programmable in real-time?
- What would you do if the design doesn't fit in the available DSP slices — what alternative architectures would you consider?

---

## Q4: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A senior engineer on your team proposes using a vendor-specific, proprietary IP core for the high-speed serial interface, arguing it will save development time. However, you're concerned about long-term maintainability and vendor lock-in. The engineer has significant experience with this vendor's tools and is confident the IP core is the right choice. How do you handle this situation?

**Answer:** This is a situation where I need to balance technical merit, team dynamics, and long-term project risk. The senior engineer's proposal has genuine merit — vendor IP cores are often well-optimized, thoroughly tested, and can significantly reduce development time. However, my concern about vendor lock-in is also legitimate, especially for a product that may need to be maintained for years.

My approach would be to first acknowledge the engineer's expertise and the valid points in their proposal. I'd then frame the discussion around the specific project requirements rather than abstract principles. Key questions I'd raise: What is the expected product lifetime? Are there requirements for second-source or multi-vendor support? What is the licensing model — is it perpetual or subscription-based? What happens if the vendor discontinues the IP core?

I'd also ask the engineer to quantify the development time savings — how much time would the IP core save compared to a custom implementation, and what are the risks of the custom approach? This shifts the discussion from opinion to data.

If the IP core is clearly the right choice for the project, I'd support it but with mitigations: document the IP core usage thoroughly, isolate it behind a well-defined interface so it could be replaced in the future, and ensure the licensing terms are acceptable. If the project has long-term maintainability requirements that make vendor lock-in unacceptable, I'd work with the engineer to develop a hybrid approach — perhaps using the IP core for the initial prototype while developing a custom implementation in parallel, or using a more portable soft-core approach.

The key is to make the decision based on project requirements and data, not on who has the strongest opinion. I'd also make sure the decision is documented with the rationale, so future engineers understand why the choice was made.

**Possible follow-ups:**
- What if the senior engineer becomes defensive and insists that their approach is the only viable one?
- How would you handle a situation where the project schedule is tight and the IP core would clearly save time, but you still have long-term concerns?

---

## Q5: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous and have no known frequency relationship, and the data must be transferred without corruption?

**Answer:** This is the most challenging CDC scenario because there's no frequency relationship to exploit, and multi-bit data can't be synchronized with simple flip-flop synchronizers — each bit would be captured at a different time, potentially causing the destination to see a corrupted word.

The fundamental principle is that you cannot synchronize multi-bit data directly across asynchronous clock domains. Instead, you must use one of several handshaking or buffering approaches:

**Approach 1: Asynchronous FIFO.** This is the most common and robust solution for continuous data transfer. The write side writes data into the FIFO using the source clock, and the read side reads using the destination clock. The FIFO uses Gray-code pointers for the read/write pointers, which ensures that only one bit changes at a time when the pointers cross clock domains, making them safe to synchronize with flip-flop synchronizers. The FIFO must be deep enough to handle the maximum burst size and the latency of the synchronization logic.

**Approach 2: Handshake protocol.** For infrequent transfers, a four-phase handshake (request-acknowledge) can be used. The source asserts a request signal, which is synchronized into the destination domain. The destination captures the data, asserts an acknowledge, which is synchronized back to the source. The source then deasserts the request, and the cycle repeats. This is simple but slow — the synchronization latency of the handshake signals limits the throughput.

**Approach 3: Data validity signal with synchronized enable.** If the data changes infrequently, the source can assert a "data valid" signal that is synchronized into the destination domain. The destination captures the data when it sees the valid signal. This works only if the data is stable long enough for the synchronization to complete — the data must remain valid for at least two destination clock cycles plus the synchronization latency.

**Key considerations:** For all approaches, I'd verify the design with formal CDC verification tools or careful simulation that includes metastability modeling. I'd also ensure that the data bus itself is not synchronized directly — only the control signals (pointers, request/acknowledge, valid) are synchronized. The data path should be designed so that data is stable when the synchronized control signal arrives.

For the asynchronous FIFO specifically, I'd pay careful attention to the Gray-code encoding and the FIFO depth calculation. The depth must account for the worst-case burst size plus the synchronization latency of the read/write pointers crossing domains.

**Possible follow-ups:**
- How would you calculate the required FIFO depth for a given burst size and clock frequency relationship?
- What are the failure modes if the Gray-code encoding is implemented incorrectly, and how would you test for them?