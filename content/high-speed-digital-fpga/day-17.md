# high-speed-digital-fpga — Day 17

## Q1: How would you approach verifying that a high-speed FPGA design will meet its timing requirements when the design includes a mix of combinational logic paths, DSP slices, and block RAMs, and you're targeting a 300 MHz clock?

**Answer:** I'd approach this as a multi-layered verification problem that starts well before place-and-route. First, I'd establish realistic timing constraints early in the design process — proper clock definitions, input/output delays based on the actual external device datasheets, and any necessary false paths or multi-cycle paths. These constraints need to be reviewed carefully because incorrect constraints are a common source of both false failures and false passes.

For the different block types, I'd consider their distinct timing characteristics. DSP slices have dedicated internal registers and hard-wired paths that can be pipelined; block RAMs have configurable output registers that trade latency for timing margin. For general logic, I'd rely on good RTL practices — keeping critical paths shallow, registering outputs, and avoiding long combinational chains.

I'd run synthesis with the constraints in place and examine the timing report for worst-case negative slack. If paths are failing, I'd look at whether the issue is in routing congestion, logic depth, or fan-out. For DSP and BRAM paths specifically, I'd check whether I'm using the dedicated cascade and output register features effectively. I'd also verify that the synthesis tool is inferring the intended hard blocks rather than implementing them in fabric logic.

After place-and-route, I'd review the post-route timing report, paying attention to clock skew and whether the clock tree is balanced. I'd also run a gate-level simulation with back-annotated delays on critical paths to catch any issues that static timing analysis might miss, such as glitches or race conditions. Finally, I'd verify the design across multiple corners — slow-slow, fast-fast, and typical — since different paths may be critical in different corners.

**Possible follow-ups:**
- How would you decide between adding pipeline stages versus restructuring logic when a critical path fails timing?
- What specific timing reports would you examine first when a design fails timing after place-and-route, and why?

---

## Q2: How would you approach designing a clock domain crossing (CDC) scheme for a control register that is written from a slow configuration interface (e.g., 10 MHz SPI) and read by a fast logic domain (e.g., 250 MHz), where the register value must never be read in a partially-updated state?

**Answer:** The key concern here is that a multi-bit register being written from a slow domain and read by a fast domain can be observed in an intermediate state if the bits update at slightly different times. Even if each individual bit is synchronized properly, the combination of bits could be momentarily inconsistent.

My approach would depend on how the register is used. If the register is a configuration value that only needs to take effect at a well-defined point, I'd use a "hold" or "shadow" register scheme. The slow domain writes the new value into a shadow register, then asserts a "data valid" pulse. The fast domain synchronizes that pulse (using a multi-flop synchronizer), and only when the synchronized pulse arrives does it latch the shadow register into the active register. This ensures the fast domain never sees a partially-updated value.

If the register needs to be updated atomically and the fast domain must always see a consistent value, I'd consider using a handshake protocol — the slow domain requests an update, the fast domain acknowledges, and only then does the slow domain write the new value. This adds latency but guarantees consistency.

For the synchronization itself, I'd use two or three flip-flops in series for the control signals, with the number depending on the MTBF requirements. I'd also make sure the synchronizer flip-flops are placed in the destination clock domain and that the synthesis tool doesn't optimize them away. For the data path, I'd avoid synchronizing each bit individually — instead, I'd synchronize a single control signal and use it to gate the data capture.

I'd also run CDC verification tools to check for any missed synchronization paths, and I'd review the design to ensure there are no combinational paths between the two clock domains that could cause metastability.

**Possible follow-ups:**
- What would you do if the register is written frequently and the handshake latency is unacceptable?
- How would you determine the number of synchronizer stages needed for a given clock domain crossing?

---

## Q3: How would you approach debugging an intermittent failure in a high-speed FPGA design where the system works correctly for hours or days, then produces a single incorrect data value before returning to normal operation?

**Answer:** Intermittent failures that occur rarely and then disappear are among the most challenging debugging scenarios because they're difficult to reproduce and often point to subtle issues rather than gross design errors. I'd approach this systematically.

First, I'd try to characterize the failure. What exactly is incorrect — a data value, a control signal, a CRC error? Is there any pattern to when it occurs — specific operating conditions, temperature, voltage, data patterns, or system activity? I'd add instrumentation to capture the failure when it happens, such as a logic analyzer trigger on the specific error condition, or internal FPGA debug cores that record the state around the failure.

If the failure appears to be data corruption, I'd suspect several possible root causes. A CDC issue where a multi-bit value occasionally gets captured in an inconsistent state could produce exactly this symptom. I'd review all clock domain crossings for proper synchronization, especially any that were added late in the design or that handle rarely-changing signals. Another possibility is a marginal timing path that occasionally fails due to voltage or temperature drift — I'd check the timing margins and consider whether any paths are close to the limit.

I'd also consider single-event upsets (SEUs) in the configuration memory or block RAM, particularly if the system is in an environment with elevated radiation levels. For configuration memory, I'd check if the FPGA supports readback and error detection. For block RAM, I'd consider adding ECC if the FPGA supports it.

If the failure is in an external interface, I'd look at signal integrity issues — marginal setup/hold times, crosstalk, or power supply noise that occasionally pushes a signal outside its valid window. I'd use an oscilloscope to monitor the interface signals over an extended period, looking for marginal behavior.

Finally, I'd consider whether the failure could be in software or firmware rather than hardware — a race condition in the embedded processor, or a buffer overflow that corrupts memory. I'd review the firmware for any timing-dependent behavior.

**Possible follow-ups:**
- How would you prioritize which potential root causes to investigate first?
- What specific instrumentation would you add to the FPGA to capture the failure when it occurs?

---

## Q4: How would you approach designing a finite state machine (FSM) in an FPGA that must control a high-speed data path, where the FSM must be resilient to transient errors in its state registers (e.g., from radiation-induced upsets) without adding excessive logic or latency?

**Answer:** This is a classic reliability-versus-cost trade-off. The approach depends on the criticality of the FSM and the expected upset rate. I'd start by analyzing the failure modes — what happens if the FSM enters an illegal state, and what happens if it transitions to a legal but incorrect state?

For illegal state detection, the simplest approach is to add a default or "safe" state in the case statement and ensure that any unencoded state transitions to a known recovery state. This catches the case where an upset creates a state that doesn't exist in the design. However, this doesn't help if the upset creates a valid but incorrect state.

For more robust protection, I'd consider triple modular redundancy (TMR) — three copies of the FSM with majority voting on the outputs. This is the gold standard for radiation-tolerant designs but triples the logic and adds voting logic. For a high-speed data path, the voting logic would be in the critical path, so I'd need to carefully pipeline it.

A middle-ground approach is to use an encoded state representation with error detection, such as a Hamming code or a one-hot encoding with parity. This allows detection of single-bit errors without full TMR. When an error is detected, the FSM can transition to a safe state or trigger a recovery sequence. The overhead is much lower than TMR — just the encoding/decoding logic and the error detection circuit.

For the recovery mechanism, I'd design the FSM so that it can re-synchronize with the data stream. This might mean flushing the pipeline, waiting for a sync pattern, or re-initializing from a known state. The key is that the recovery must be deterministic and not disrupt the overall system beyond an acceptable level.

I'd also consider whether the FSM can be simplified or made more robust by design — for example, using a counter-based approach instead of a complex state machine where possible, or ensuring that the FSM has a small number of states so that the encoding overhead is manageable.

**Possible follow-ups:**
- How would you decide between TMR and error-detecting encoding for a given application?
- How would you verify that the FSM recovery mechanism works correctly under all possible upset scenarios?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** I'd approach this as a coaching opportunity rather than simply overriding the engineer's decision. The concern is legitimate — average rates don't tell you anything about burst behavior, and a FIFO that's too shallow could overflow during a burst, causing data loss that might not be immediately obvious.

First, I'd acknowledge the engineer's reasoning — it's correct that the average rates are sustainable, and the memory controller's write buffer does provide some burst absorption. Then I'd ask the engineer to walk through the worst-case burst scenario: what's the maximum number of consecutive ADC samples that could arrive before the memory controller can accept them? This would include the memory controller's refresh cycles, bank conflicts, and read/write turnaround overhead.

I'd guide the engineer toward calculating the required FIFO depth based on the worst-case burst, not the average rate. If the calculation shows that 64 words is insufficient, I'd ask the engineer to propose a solution — either a deeper FIFO or a flow-control mechanism that throttles the ADC data when the FIFO is nearly full.

I'd also raise the question of what happens when the FIFO does overflow — is there a flag that can be monitored? Can the system detect and recover from dropped data? This is important for a data acquisition system where data integrity is critical.

The goal is to help the engineer develop the analytical skills to identify these issues independently in the future, while ensuring the design is correct now. I'd frame it as a collaborative problem-solving exercise rather than a criticism, and I'd make sure the engineer leaves the review with a clear understanding of why burst analysis matters.

**Possible follow-ups:**
- How would you handle the situation if the engineer still disagrees after your discussion?
- What specific questions would you ask to help the engineer calculate the worst-case burst scenario?