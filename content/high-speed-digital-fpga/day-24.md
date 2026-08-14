# high-speed-digital-fpga — Day 24

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a multi-bit data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For a multi-bit bus crossing between truly asynchronous clock domains with frequent data changes, I'd first rule out simple two-flop synchronizers—they only work for single-bit control signals. The fundamental options are: (1) a handshake-based approach, (2) an asynchronous FIFO, or (3) a MUX-based synchronization scheme, depending on the data rate and latency budget.

For continuous, high-throughput data, an asynchronous FIFO is the standard choice. The key design considerations are:

- **Gray-code pointers**: The read and write pointers must be encoded in Gray code so that only one bit changes per increment, making them safe to synchronize across clock domains. The FIFO depth must be a power of two for Gray-code wrapping to work cleanly.
- **Depth calculation**: The FIFO depth must accommodate the worst-case burst size plus the synchronization latency of the pointer signals (typically 2–3 cycles in each domain). I'd calculate this as: burst size + (write clock period × sync latency in write domain) + (read clock period × sync latency in read domain).
- **Full/empty generation**: Full is generated in the write domain using the synchronized read pointer; empty is generated in the read domain using the synchronized write pointer. This conservative approach prevents over/underflow at the cost of a few cycles of added latency.
- **Metastability protection**: The synchronizer flops must be placed in dedicated synchronization cells in the FPGA fabric, and the synthesis tool must be constrained to prevent optimizations that could merge or duplicate them.

If the data rate is low and latency is less critical, a four-phase handshake (request/acknowledge) is simpler and requires less resources. For medium rates where latency matters, I'd consider a MUX-based synchronizer with Gray-coded data, though this becomes impractical for wide buses.

The critical verification step is a dedicated CDC analysis—either using the vendor's CDC tool or a third-party tool like SpyGlass CDC—to prove that all crossings are properly synchronized and that no combinational logic feeds a synchronizer input.

**Possible follow-ups:**
- How would you handle the case where the FIFO depth calculation shows you need more block RAM than available on the target FPGA?
- What happens to the FIFO's full flag when the read clock is stopped or much slower than the write clock?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design intermittently produces incorrect results only when the board is subjected to mechanical vibration?

**Answer:** Mechanical vibration causing intermittent functional failures points strongly to a physical-layer issue rather than a logic error. The design works when static, so the logic is likely correct—something is changing electrically when the board flexes or components move. My debugging approach would be systematic:

**First, characterize the failure.** I'd try to correlate the failures with specific vibration frequencies or amplitudes. Does it happen at a specific resonance frequency? Does it affect all channels or just one? This helps narrow down whether it's a single connection or a systemic issue.

**Second, inspect the mechanical suspects:**
- **Connectors**: Board-to-board connectors, especially mezzanine or card-edge types, are prime suspects. Vibration can cause micro-movement at the contact interface, creating intermittent opens or high-resistance connections. I'd check for proper seating, locking mechanisms, and whether the connector is rated for the vibration environment.
- **BGA and high-pin-count packages**: Solder joint cracks under BGA packages are a classic cause. Vibration stress combined with thermal cycling can propagate cracks. I'd look for evidence of board flex near the FPGA or memory devices.
- **Crystal oscillators and clock sources**: A crystal that's mechanically stressed can change frequency or stop oscillating momentarily. I'd probe the clock outputs during vibration to see if there's dropout or frequency shift.
- **Decoupling capacitors**: A cracked or poorly-soldered decoupling cap can cause power supply noise under vibration, leading to marginal timing failures.

**Third, use targeted instrumentation.** I'd add test points or use existing ones to monitor power rails, clock signals, and critical data lines during vibration testing. A logic analyzer or oscilloscope with deep memory can capture the exact moment of failure and show which signal is corrupted.

**Fourth, consider environmental factors.** Vibration often couples with temperature and humidity. If the board is flexing, traces can micro-crack, especially near board edges or mounting points. I'd examine the PCB for stress marks or use X-ray inspection on suspect solder joints.

**Finally, implement corrective actions.** Depending on the root cause, this could mean: adding conformal coating or underfill for BGA devices, improving board stiffening or mounting, using locking connectors, adding strain relief, or redesigning the PCB stack-up to reduce flex.

**Possible follow-ups:**
- How would you distinguish between a solder joint issue and a connector issue without destructive testing?
- What role would boundary-scan (JTAG) testing play in isolating the failure to a specific device or connection?

---

## Q3: How would you approach implementing a finite state machine (FSM) in an FPGA that must control a high-speed data path with strict latency requirements (e.g., a packet processor that must make a forwarding decision within 10 clock cycles at 400 MHz)?

**Answer:** This is a classic problem where the FSM architecture must be optimized for both speed and deterministic latency. At 400 MHz, the FSM logic itself must be minimal, and the state encoding and decoding must not create long combinational paths.

**State encoding**: For a latency-critical FSM, I'd use one-hot encoding. While it uses more flip-flops, it eliminates the need for a state decoder—each state is represented by a single flip-flop, so the next-state logic only needs to look at the current state bit directly. This minimizes the combinational delay from state register to next-state logic. For a small number of states (say, 8–16), the flip-flop cost is acceptable.

**Pipeline structure**: I'd analyze the decision path and break it into pipeline stages if possible. For example, if the forwarding decision requires examining a packet header, I might pipeline the header parsing into stages: (1) extract header fields, (2) perform lookup, (3) make decision. Each stage gets one clock cycle, and the FSM controls the handoff between stages. The key is to ensure the critical path through any single stage is under 2.5 ns (for 400 MHz).

**Critical path minimization**: The next-state logic should be as shallow as possible. I'd avoid complex conditions in the state transitions—instead, I'd precompute decision signals in parallel logic and feed simple "decision ready" flags to the FSM. For example, a comparator or lookup table result can be computed in a separate pipeline stage, and the FSM just waits for the "done" signal.

**Timing closure strategy**: I'd write the FSM in RTL with explicit state encoding and use synthesis attributes to prevent the tool from re-encoding the states. I'd also add timing constraints that specifically target the FSM paths, and use register retiming if the tool supports it to balance logic across pipeline stages.

**Verification**: Beyond functional simulation, I'd verify the latency requirement explicitly—writing a testbench that measures the exact number of cycles from input arrival to output decision. I'd also run gate-level simulation with timing to catch any path that exceeds the 2.5 ns budget.

**Possible follow-ups:**
- How would you handle the case where the forwarding decision requires a table lookup that takes longer than one clock cycle?
- What trade-offs would you consider between a Moore and Mealy FSM for this application?

---

## Q4: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** This is a demanding PDN requirement—20A at 1A/ns slew rate means the voltage must stay within ±25.5 mV of 0.85V, which requires careful attention to both the DC and AC impedance of the power delivery path.

**Target impedance calculation**: The first step is to calculate the maximum allowable PDN impedance. For a 20A transient with ±3% tolerance (25.5 mV), the target impedance is roughly 25.5 mV / 20A = 1.275 mΩ. However, this is the worst-case DC target—the real requirement is frequency-dependent. The PDN impedance must stay below this target across the frequency range where the transient energy exists, which for a 1A/ns slew rate extends well into the tens of MHz.

**VRM selection**: The voltage regulator module must have sufficient bandwidth to respond to the transient. A multi-phase buck converter with a high switching frequency (1–2 MHz or higher) is typically needed. The VRM's output capacitance and control loop bandwidth determine how much of the transient it can absorb. For a 20A step, the VRM alone can't respond fast enough—the bulk of the transient energy must come from the decoupling capacitors.

**Decoupling strategy**: I'd use a multi-tier decoupling approach:
- **Bulk capacitors** (electrolytic or polymer tantalum, 100–1000 µF) near the VRM output to handle the low-frequency portion of the transient (below ~100 kHz).
- **Ceramic capacitors** in multiple values (e.g., 100 µF, 10 µF, 1 µF, 0.1 µF) distributed across the board to cover the mid-frequency range (100 kHz to ~10 MHz).
- **High-frequency decoupling** (0.01–0.1 µF) placed as close as possible to the FPGA power pins, ideally on the backside of the board directly under the BGA package.

**PCB stack-up and plane design**: For 1A/ns slew rates, the power and ground planes themselves become part of the PDN. I'd use:
- A dedicated power plane for the core rail, with the ground plane directly adjacent (minimal dielectric thickness, e.g., 2–4 mils) to maximize interplane capacitance.
- Multiple vias from the FPGA power pins to the plane—typically one via per power pin, or at least enough to keep the via inductance below the target.
- The plane pair capacitance acts as a distributed high-frequency decoupling element.

**Simulation and verification**: I'd perform a PDN impedance analysis using tools like SIwave or PowerSI to model the plane pair, vias, and capacitor placement. The goal is to keep the impedance below the target across the full frequency range. I'd also run a transient simulation with a 20A step at 1A/ns to verify the voltage stays within tolerance. On the bench, I'd use a high-bandwidth oscilloscope with a differential probe to measure the core voltage during a controlled load transient.

**Possible follow-ups:**
- How would you determine the optimal number and placement of decoupling capacitors without over-designing?
- What role does the FPGA's own package and internal decoupling play in the PDN design?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior—the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a classic design review situation where a junior engineer has made a reasonable-sounding assumption that doesn't hold up under worst-case analysis. My approach would be to guide the engineer toward discovering the issue themselves rather than simply overriding their decision.

**First, I'd acknowledge the valid part of their reasoning.** The average-rate argument is correct for steady-state operation, and it's good that they're thinking about the average throughput. This validates their analytical approach while setting up the discussion.

**Second, I'd ask probing questions to help them think through the burst scenario.** I might ask: "What happens if the ADC produces a burst of 128 samples while the memory controller is in the middle of a refresh cycle? Can the write buffer absorb that entire burst? What's the maximum burst the memory controller can accept before it needs to issue a write to the DRAM?" These questions guide them toward analyzing the worst-case burst behavior rather than just the average.

**Third, I'd walk through the math together.** We'd calculate: the maximum ADC burst size, the memory controller's sustainable write rate (accounting for refresh, read/write turnaround, and bank conflicts), and the synchronization latency of the FIFO pointers. This would show whether 64 words is sufficient or not. If the calculation shows it's marginal, I'd ask the engineer to propose a solution—perhaps a deeper FIFO, or a rate-matching scheme that throttles the ADC during memory-intensive operations.

**Fourth, I'd discuss the cost of being wrong.** In a data acquisition system, a FIFO overflow means lost data—there's no way to recover it. The cost of a slightly deeper FIFO (a few hundred block RAM bits) is trivial compared to the cost of losing data or having to redesign the board. This helps the engineer understand the risk/reward trade-off.

**Finally, I'd use this as a teaching moment about worst-case analysis.** The key lesson is that in real-time systems, you must design for the worst case, not the average. I'd encourage the engineer to always ask: "What's the absolute worst thing that can happen, and can my design survive it?"

The outcome would be a revised FIFO depth calculation based on worst-case burst analysis, with the engineer taking ownership of the fix. This approach builds their skills while ensuring the design is correct.

**Possible follow-ups:**
- How would you handle the situation if the engineer still disagrees after your analysis?
- What documentation or process changes would you suggest to prevent this type of issue in future designs?