# high-speed-digital-fpga — Day 28

## Q1: How would you approach designing a clock domain crossing (CDC) scheme for a data bus where the source and destination clocks are asynchronous, the data changes frequently, and you need to minimize latency while ensuring data integrity?

**Answer:** For a frequently-changing multi-bit bus crossing between asynchronous clock domains with minimal latency, I'd first characterize the relationship between the clocks. If they're truly asynchronous with no known phase relationship, the standard approaches are either an asynchronous FIFO or a handshake-based transfer, and the choice depends on the data rate and latency budget.

For high-throughput, continuous data, an asynchronous FIFO is the right choice. The key design considerations are:
- **Gray-code pointers** for the read/write pointers crossing the domains, since only one bit changes per increment, eliminating multi-bit synchronization hazards.
- **Proper synchronization** of the Gray-coded pointers using two flip-flop synchronizers in the destination domain.
- **FIFO depth calculation** based on the worst-case burst size, the frequency ratio between domains, and the synchronization latency (typically 2-3 cycles per domain).
- **Full/empty flag generation** in the correct clock domain — full in the write domain, empty in the read domain — to avoid metastability on the flag itself.

For lower-rate control or status data where latency is less critical, a four-phase handshake (request/acknowledge) with proper synchronization on both control signals is simpler and adequate.

If the data changes frequently and latency is truly critical, I'd also consider whether the frequency relationship can be made deterministic — for example, if both clocks derive from a common reference, you might use a small asynchronous FIFO with careful depth sizing rather than a full handshake, which adds multiple cycles of latency.

**Possible follow-ups:**
- How would you size the FIFO depth if the write clock is 200 MHz, the read clock is 150 MHz, and the write side can burst 64 words?
- What happens if the FIFO becomes full — how would you handle backpressure in the write domain?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully, but the design functions correctly at room temperature and fails only when the board is heated to its maximum specified operating temperature?

**Answer:** Temperature-dependent failures that only appear at the high end of the operating range typically point to timing margin issues, so I'd approach this systematically:

1. **Reproduce and characterize the failure** — I'd want to know exactly what fails: is it a specific function, a specific data path, or a general system failure? Does it fail gradually as temperature rises, or abruptly at a threshold? This helps narrow the search.

2. **Check timing margins** — At elevated temperature, propagation delays increase (especially in the logic fabric), and clock jitter can worsen. I'd review the timing reports for the failing paths, looking at the slack values. Paths with marginal positive slack at nominal conditions are the prime suspects. I'd also check whether the design meets timing across all process corners, particularly the slow-slow corner which represents worst-case delay.

3. **Examine clock generation** — PLLs and MMCMs can lose lock or increase jitter at temperature extremes. I'd verify that the clocking resources are operating within their specified temperature range and check for any temperature-dependent jitter issues. If the PLL is marginal, I might see intermittent timing violations on paths that are otherwise comfortable.

4. **Look for temperature-sensitive analog effects** — If the failure is in an I/O interface, I'd check the I/O standards and drive strengths. At high temperature, output drive strength can decrease and input thresholds can shift, reducing noise margin. This is especially relevant for single-ended interfaces with marginal signal integrity.

5. **Consider power supply effects** — At temperature, regulator efficiency changes and IR drops can increase. If the core voltage droops under load at temperature, timing margins shrink. I'd verify the actual core voltage at the FPGA pins under worst-case conditions.

6. **Use targeted testing** — I'd create a test that stresses the suspected paths — for example, running a PRBS through the data path and checking for errors while sweeping temperature. This helps isolate whether it's a specific path or a systemic issue.

The fix depends on the root cause: adding pipeline stages to critical paths, tightening clock constraints, improving the power distribution network, or adjusting I/O standards.

**Possible follow-ups:**
- How would you distinguish between a timing margin issue and a signal integrity issue in this scenario?
- What specific information would you look for in the timing reports to identify the most likely failing paths?

---

## Q3: How would you approach implementing a finite state machine (FSM) in an FPGA that must control a high-speed data path with strict latency requirements (e.g., a packet processor that must make a forwarding decision within 10 clock cycles at 400 MHz)?

**Answer:** For an FSM with strict latency requirements at high clock frequency, the design approach needs to balance state encoding, logic depth, and pipeline structure:

1. **State encoding** — For a latency-critical FSM, I'd use one-hot encoding. It requires more flip-flops but eliminates the need for state decode logic, reducing the combinational delay on the state register inputs. This is often the difference between meeting and missing timing at 400 MHz.

2. **Minimize combinational depth** — I'd carefully examine the next-state and output logic to keep the critical path as short as possible. This might mean:
   - Pre-computing conditions that don't depend on the current state.
   - Using parallel case statements rather than nested if-else chains.
   - Moving complex decisions into the data path rather than the FSM itself, keeping the FSM as a simple sequencer.

3. **Pipeline the decision path** — If the forwarding decision requires multiple stages of logic (e.g., header parsing, table lookup, priority resolution), I'd pipeline these stages and have the FSM coordinate the pipeline rather than making the decision in a single cycle. The FSM would issue control signals at the right pipeline stages, and the actual decision logic would be in the data path.

4. **Consider a datapath-centric architecture** — For a packet processor, the FSM might be better viewed as a pipeline controller rather than a monolithic state machine. Each pipeline stage has its own small FSM or control logic, and they communicate through valid/ready handshakes. This distributes the logic and keeps each stage's combinational depth manageable.

5. **Use retiming if necessary** — If a specific path is still too long, I'd consider whether the FSM logic can be retimed — moving register boundaries to balance combinational delay across stages.

6. **Verify with timing-driven synthesis** — I'd write the RTL with explicit clock-cycle budgeting, then use synthesis and place-and-route reports to verify that each pipeline stage meets timing. I'd also simulate with back-annotated delays to confirm the FSM behaves correctly with the actual timing.

The key principle is: don't try to do everything in one state transition. Break the decision into pipeline stages and let the FSM coordinate the flow.

**Possible follow-ups:**
- How would you handle a case where the forwarding decision depends on a table lookup that itself takes 3 cycles?
- What are the trade-offs between one-hot and binary encoding for this application?

---

## Q4: How would you approach designing a power distribution network (PDN) for an FPGA with multiple voltage rails, where the core rail (0.85V) has a transient current demand of up to 20A with a slew rate of 1A/ns, and you need to ensure the voltage stays within ±3% of nominal?

**Answer:** This is a challenging PDN design because the combination of high current, fast slew rate, and tight tolerance means both the DC and AC aspects need careful attention:

1. **DC analysis** — First, I'd calculate the total allowable voltage deviation: ±3% of 0.85V is ±25.5 mV. I'd budget this between the regulator's DC accuracy, the IR drop through the board traces and vias, and the AC transient response. Typically, the regulator DC accuracy might take 5-10 mV, leaving 15-20 mV for IR drop and transients.

2. **Regulator selection and placement** — For 20A with 1A/ns slew, I'd use a multi-phase buck converter with a high switching frequency, placed as close to the FPGA as physically possible. The regulator's transient response — its ability to source current quickly during a load step — is critical. I'd look at the loop bandwidth and output capacitance requirements in the regulator's datasheet. I might also consider a hybrid approach with a slower bulk regulator plus a fast linear regulator or active transient response circuit for the high-frequency component.

3. **Bulk and decoupling capacitance** — The transient current must be supplied by local capacitance until the regulator can respond. I'd calculate the required capacitance using the target impedance method: for a 1A/ns slew and 25 mV allowed deviation, the target impedance at the FPGA is roughly 25 mV / 20A = 1.25 mΩ. The decoupling network needs to maintain this impedance up to the frequency where the regulator's loop can take over. This typically means:
   - Bulk capacitors (tens to hundreds of µF) for the 10 kHz to 1 MHz range.
   - Ceramic capacitors in the 1 MHz to 100 MHz range.
   - The FPGA's own on-die and package capacitance for the highest frequencies.

4. **PCB stack-up and plane design** — The core rail needs a dedicated power plane with minimal inductance. I'd use a stack-up where the core plane is adjacent to a ground plane with minimal dielectric thickness (e.g., 100 µm or less) to maximize plane capacitance. The vias connecting the capacitors to the plane need to be short and numerous to minimize inductance.

5. **Simulation and verification** — I'd simulate the PDN using SPICE or a dedicated PDN analysis tool, modeling the regulator, capacitors (with their ESL and ESR), plane impedance, and the FPGA's current draw as a time-varying load. I'd verify that the voltage at the FPGA's power pins stays within ±3% under the worst-case transient. On the bench, I'd use a high-bandwidth oscilloscope probe at the FPGA pins to measure the actual transient response.

6. **Layout considerations** — The capacitor placement is critical: smallest capacitors closest to the FPGA, with short, wide traces or direct via connections to the plane. I'd avoid daisy-chaining capacitors — each should connect directly to the plane pair.

The key is to treat this as a distributed impedance problem, not just a "add more capacitors" problem. Every element — regulator, bulk caps, ceramic caps, planes, vias — contributes to the total impedance, and they need to work together to keep the impedance below the target across the entire frequency range of interest.

**Possible follow-ups:**
- How would you determine the target impedance for the PDN, and how does it vary with frequency?
- What measurements would you take on the bench to verify the PDN meets the ±3% requirement?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer on your team has implemented the data path that captures samples from a 500 MSPS ADC and writes them to DDR3 memory. During the review, you notice that the engineer has used a single FIFO to cross from the ADC clock domain to the memory controller clock domain, but the FIFO depth is only 64 words. When you ask about the depth, the engineer explains that the average write rate is well below the read rate, so the FIFO should never overflow. However, you're concerned about burst behavior — the ADC can produce bursts of data that could temporarily exceed the memory controller's sustainable write rate. The engineer argues that the memory controller's write buffer will absorb the bursts. How do you handle this situation?

**Answer:** This is a classic design review situation where a junior engineer has reasoned correctly about average behavior but hasn't fully considered worst-case burst behavior. I'd handle it by guiding the engineer to analyze the problem rigorously rather than simply overriding their decision:

1. **Acknowledge the valid reasoning** — I'd start by acknowledging that the engineer's average-rate analysis is correct and shows good understanding of the system. This keeps the conversation constructive and encourages continued engagement.

2. **Reframe the question** — I'd ask the engineer to walk through the worst-case scenario: "What happens if the ADC produces a maximum-length burst while the memory controller is simultaneously handling a refresh cycle or a read operation? Can you trace through the timing to show me the FIFO won't overflow?" This shifts the discussion from opinion to analysis.

3. **Quantify the burst behavior** — I'd work with the engineer to calculate the actual worst-case write burst from the ADC (based on its maximum burst length and the ADC's output rate) and the memory controller's sustainable write rate (accounting for refresh overhead, read/write turnaround, and bank conflicts). The key question is: what's the maximum number of words that can arrive in the FIFO before the memory controller can drain them?

4. **Discuss the memory controller's write buffer** — The engineer's point about the write buffer has merit, but it's important to understand that the write buffer is also finite and has its own burst characteristics. The FIFO and the write buffer together form a buffering system, and the total buffering must exceed the worst-case burst imbalance.

5. **Propose a quantitative approach** — Rather than just saying "make it deeper," I'd suggest the engineer calculate the required FIFO depth using the worst-case burst size, the frequency ratio, and the memory controller's drain rate. If the calculation shows 64 words is insufficient, the fix is clear. If it shows 64 words is adequate, then the design is fine — but now we have a documented analysis rather than an assumption.

6. **Follow up on the fix** — If the FIFO needs to be deeper, I'd ask the engineer to update the design and re-run the analysis to verify the new depth is sufficient. I'd also suggest adding a FIFO fullness monitor or an overflow flag for debug purposes, so that if the system ever does overflow in the field, it's detectable.

The goal is to teach the engineer to think in terms of worst-case analysis and to document design decisions with quantitative justification, not to simply impose my judgment.

**Possible follow-ups:**
- How would you calculate the required FIFO depth if the ADC can burst 256 words at 500 MSPS and the memory controller can sustain 80% of its peak write bandwidth?
- What other failure modes might occur if the FIFO overflows, and how would you detect them in the field?