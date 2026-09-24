# high-speed-digital-fpga — Day 65

## Q1: How would you approach designing the return-current path for a high-speed digital board where a signal transitions between two reference planes (e.g., from a ground plane to a power plane) on its way through a via?

**Answer:** The core principle is that every high-speed signal current returns to its source through the path of least impedance, which at high frequency is directly beneath the trace on the adjacent reference plane. When a signal layer changes reference planes — say from a plane referenced to ground to one referenced to a power plane — the return current has no continuous path unless you provide one. The return current must be able to jump from the ground plane to the power plane at the same location where the signal via transitions, otherwise it will find a long, inductive detour that radiates and creates ground bounce.

The standard mitigation is to place a stitching capacitor (or a via stitching pattern) close to the signal via, connecting the two reference planes. The capacitor provides a low-impedance path for the return current at the frequencies of interest. The key design decisions are: how close is "close" (typically within a few millimeters, ideally within a quarter-wavelength of the highest significant frequency component), what capacitor value and type to use (small body size, low ESL, often 10–100 nF with a high self-resonant frequency), and whether a single capacitor is enough or whether you need multiple in parallel to cover a broad frequency range.

A better approach, when the stack-up allows it, is to avoid the plane transition altogether by keeping the signal referenced to the same plane throughout its route, or by using a ground-referenced layer change. If the stack-up forces a transition, I would also consider whether the two planes are at the same DC potential — if not, the stitching capacitor also serves a DC-blocking function, which is fine, but you must ensure the capacitor's voltage rating and placement are appropriate.

I would verify the design by identifying all layer-transition vias in the high-speed nets during layout review, ensuring each has an adjacent stitching capacitor, and checking that the capacitor's placement minimizes the loop area of the return path. In simulation or measurement, a return-path discontinuity typically shows up as increased insertion loss, a resonance in the transfer function, or elevated common-mode radiation — so I would look for those signatures if I suspected a problem.

**Possible follow-ups:**
- How would you decide between using a stitching capacitor versus a stitching via when the two planes are at the same DC potential?
- What happens to the return current if the stitching capacitor is placed several millimeters away from the signal via, and how would that manifest in the eye diagram?

---

## Q2: How would you approach debugging an FPGA design where the device configures successfully and runs correctly, but the configuration appears to be lost after some time — the device stops responding and requires a reconfiguration to recover?

**Answer:** This is a classic "configuration loss" symptom, and the first step is to distinguish between a true loss of configuration (the FPGA's internal configuration memory has been corrupted or reset) and a functional lock-up that merely looks like configuration loss (e.g., a state machine stuck in an illegal state, a PLL that has lost lock, or a watchdog that has fired). The distinction matters because the debug path is completely different.

I would start by checking the configuration-related status pins and any internal status registers. If the device has a "configuration done" or "init done" signal that can be monitored, I would observe whether it actually de-asserts when the failure occurs, or whether it stays asserted while the design simply stops functioning. If the status pin stays asserted, the configuration memory is likely intact and the problem is functional — a lock-up, a clock loss, or a reset issue. If the status pin de-asserts, the configuration has genuinely been lost, which points to a power integrity issue, a configuration memory upset, or a problem with the configuration source (e.g., flash corruption or a glitch on the configuration interface).

For a true configuration loss, the usual suspects are: power supply droop or glitch on the core or auxiliary rails (the FPGA may reset if a rail dips below its minimum), a radiation-induced upset in the configuration memory (relevant for high-reliability or space applications), or a problem with the external configuration flash or the configuration controller. I would monitor the power rails with a scope set to trigger on a droop, check the configuration flash's integrity and access timing, and review whether the board's power sequencing or brown-out detection is adequate.

For a functional lock-up that mimics configuration loss, I would look at clock integrity (is the PLL still locked? has the reference clock dropped out?), reset architecture (is a reset being asserted spuriously?), and the design's state machines (is there a path to an illegal state that the design cannot recover from?). A common cause is a clock domain crossing or a reset that is not properly synchronized, which can leave the design in a state where it stops processing but the configuration is still intact.

In either case, I would add instrumentation — a heartbeat signal, a status register that can be read back, or a counter that increments continuously — so that the next time the failure occurs, I can tell exactly where the design stopped. Without that visibility, the debug is guesswork.

**Possible follow-ups:**
- How would you design the reset and brown-out detection circuitry to ensure that a brief power glitch either causes a clean reconfiguration or is ridden through without disrupting the design?
- If the failure only occurs after hours or days of operation, how would you set up a long-term monitoring scheme to capture the event?

---

## Q3: How would you approach designing the interface between an FPGA and an external ADC that uses a source-synchronous, double-data-rate (DDR) output bus, where the data and a forwarded clock arrive at the FPGA with an unknown but bounded skew between them?

**Answer:** A source-synchronous DDR interface means the ADC transmits both the data and a forwarded clock (often called DCO or a data strobe), and the FPGA must capture the data using that forwarded clock rather than a system clock. The fundamental challenge is that the forwarded clock and the data lanes have different propagation delays — through the ADC's output buffers, the PCB traces, and the FPGA's input buffers — so the clock edge does not arrive at the FPGA's capture flip-flops in the center of the data eye. The skew is bounded (the ADC datasheet specifies a setup/hold window or a skew range), but it is not zero, and it can vary with temperature, voltage, and process.

The standard approach is to use the FPGA's input delay elements (IDELAY) or a similar programmable delay on each data lane (and sometimes on the clock lane) to align the capture point with the center of the data eye. This is a calibration problem: at startup, the FPGA sweeps the delay value and looks for the window where the data is captured correctly — typically by sending a known training pattern from the ADC, or by using a built-in pattern if the ADC supports one. The calibration finds the edges of the passing window and sets the delay to the midpoint, which maximizes margin against both setup and hold violations.

Key design considerations: first, the PCB layout must match the trace lengths of the data lanes and the clock lane as closely as possible, so that the skew introduced by the board is minimized and the remaining skew is dominated by the ADC's output skew (which is specified). Second, the FPGA's input buffers and IDELAY elements have their own delay variation over PVT, so the calibration must be re-run or at least verified across the operating conditions the board will see. Third, the forwarded clock may need to be routed to a global clock buffer or a regional clock buffer, depending on the FPGA architecture, and the clock's jitter and duty cycle affect the achievable margin.

I would also consider whether the interface needs to support a "training" mode at every power-up or only at production test. For a robust design, I would include a startup calibration routine that runs automatically and stores the delay values, and I would add a mechanism to re-calibrate if the link shows errors (e.g., a CRC or a pattern checker). The calibration algorithm itself must be careful to avoid false passes — for example, if the data pattern is not sufficiently random, the passing window may appear wider than it really is.

**Possible follow-ups:**
- How would you verify that the calibration is robust across the full temperature range, given that the ADC's output skew and the FPGA's input delay both drift with temperature?
- What would you do if the passing window is too narrow to provide adequate margin — what design changes would you consider?

---

## Q4: How would you approach designing a finite state machine (FSM) in an FPGA that must control a high-speed data path with strict latency requirements (e.g., a packet processor that must make a forwarding decision within 5 clock cycles at 400 MHz), while also being robust against single-event upsets (SEUs)?

**Answer:** This is a tension between two competing requirements: latency (which pushes toward minimal logic depth and no extra pipeline stages) and SEU robustness (which typically pushes toward redundancy, error detection, and recovery logic that adds both area and latency). The design approach has to balance these explicitly rather than treating them as independent.

First, I would define the latency budget precisely. At 400 MHz, 5 clock cycles is 12.5 ns. That budget must cover the input capture, the decision logic, and the output registration. Any SEU mitigation that adds a pipeline stage or a comparison cycle eats directly into that budget, so the mitigation must be chosen carefully.

For SEU robustness in an FSM, the main threats are: a bit flip in the state register that puts the FSM into an illegal state, and a bit flip in the combinational logic that produces a wrong next-state or output. The standard techniques are:

- **State encoding:** Use a one-hot or a Hamming-distance-2 encoding so that a single-bit flip in the state register either lands in an unused state (which can be detected and recovered) or is at least detectable. A binary encoding with adjacent states differing by one bit is vulnerable because a single flip can silently move the FSM to a valid but wrong state.
- **Illegal-state detection and recovery:** Add a small amount of logic that detects when the state register holds an unused value and forces a transition to a known safe state (e.g., an idle or reset state). This is cheap in latency — it can be combinational or a single pipeline stage — and it catches the most common failure mode.
- **Parity or SECDED on the state register:** For higher criticality, store the state with a parity bit or a Hamming code and check it every cycle. This adds a comparison and a potential correction cycle, which may or may not fit the latency budget. If it doesn't fit, a parity check that triggers a recovery (rather than a correction) may be acceptable if the recovery latency is tolerable.
- **Triple modular redundancy (TMR):** Replicate the FSM three times and vote on the outputs. This is the most robust but also the most area- and power-hungry, and the voter adds a small amount of latency. For a 5-cycle budget, TMR on the entire FSM may be too expensive, but TMR on just the state register (with a single copy of the next-state logic) is a common compromise.

The key design decision is where to spend the latency budget. If the FSM's decision logic is the critical path, I would pipeline it and use the pipeline registers themselves as the redundancy point (e.g., duplicate the pipeline registers and vote). If the state register is the critical element, I would focus mitigation there. I would also consider whether the FSM can be designed so that an SEU produces a detectable error rather than a silent wrong decision — for example, by adding a checksum to the packet header that the FSM validates, so that a corrupted decision is caught downstream even if the FSM itself is not fully protected.

Finally, I would verify the design with fault injection: simulate single-bit flips in the state register and in the combinational logic, and confirm that the FSM either recovers to a safe state within the latency budget or produces a detectable error. This is the only way to know whether the mitigation actually works.

**Possible follow-ups:**
- How would you decide between TMR on the state register versus a parity-check-and-recover scheme, given a fixed latency budget?
- If the FSM must also recover from an SEU within a bounded number of cycles, how would you design the recovery path so that it does not itself become a single point of failure?

---

## Q5: Behavioral question — You're leading a design review for a high-speed FPGA-based data acquisition board. A junior engineer has implemented a critical control signal that is generated in one clock domain and consumed in another, and they've connected it directly without any synchronization, arguing that "the signal is stable long enough that it will always be captured correctly." How do you handle this situation?

**Answer:** This is a situation where the technical issue is clear-cut — an unsynchronized clock domain crossing is a metastability risk, and "stable long enough" is not a valid argument because it doesn't account for the setup/hold window of the receiving flip-flop, which is a probabilistic event that depends on the relative phase of the two clocks. The signal may be stable for many cycles, but if its transition happens to fall within the receiving flip-flop's setup/hold window, the output can be metastable, and the failure is intermittent and temperature/voltage-dependent. So the first thing I would do is make sure the engineer understands *why* the direct connection is a problem, not just that it's against the rules.

I would approach it as a teaching moment rather than a confrontation. I'd ask the engineer to walk me through their reasoning — why they believe the signal is stable long enough — and then I'd explain the metastability mechanism: the receiving flip-flop has a setup/hold window, the signal's transition can occur anywhere relative to the receiving clock, and if it occurs within that window, the flip-flop's output can be indeterminate for a period. I'd point out that the failure mode is not "it always works" or "it always fails" but "it fails rarely and unpredictably," which is exactly the kind of bug that escapes to production and is very expensive to diagnose later.

Then I'd move to the solution. For a single-bit control signal, the standard fix is a two-flop synchronizer (or a three-flop synchronizer for higher reliability), which reduces the probability of metastability propagating to an acceptable level. If the signal is multi-bit, a two-flop synchronizer per bit is not sufficient because the bits can be captured in different cycles — so I'd discuss the appropriate technique for multi-bit crossings (e.g., handshaking, a FIFO, or a gray-coded counter if the data is a counter value). I'd also check whether the signal's timing requirements allow the added latency of a synchronizer, and whether the design has a proper constraint (e.g., a `set_false_path` or `set_max_delay` constraint) to tell the timing analyzer not to try to meet timing across the crossing.

I'd also use this as an opportunity to review the rest of the design for similar issues — if one crossing was missed, there may be others. I'd ask the engineer to audit all clock domain crossings in their block and confirm that each one uses an appropriate synchronization scheme. And I'd make sure the design review checklist includes a CDC check, so that this class of issue is caught systematically in the future rather than relying on someone noticing it in review.

The tone matters: the goal is to fix the design and improve the engineer's understanding, not to embarrass them. A junior engineer who made a reasonable-but-wrong assumption should leave the review knowing *why* the assumption was wrong and how to do it correctly next time.

**Possible follow-ups:**
- How would you verify that the synchronizer you added actually resolves metastability to the required level — what analysis or simulation would you do?
- If the control signal is multi-bit and the bits must be captured coherently, how would you decide between a handshake, a FIFO, and a gray-coded encoding?