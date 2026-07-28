# high-speed-digital-fpga — Day 7

## Q1: How would you approach designing a power supply sequencing scheme for an FPGA that requires core voltage (0.85V), auxiliary voltage (1.8V), and I/O voltage (3.3V) with specific ramp order and timing requirements?

**Answer:** The first step is to consult the FPGA vendor's power-up requirements in the datasheet, which typically specify both the sequence (which rail must reach its operating voltage before another begins ramping) and the ramp rate (voltage slew rate) for each rail. A common requirement is that core voltage must stabilize before I/O banks are powered, to prevent latch-up or undefined I/O states during configuration.

For implementation, I would use power management ICs (PMICs) or dedicated power sequencers with enable pins that track the previous rail's power-good signal. For example, the 3.3V I/O rail's enable would be gated by the power-good output of the 1.8V regulator, which itself is gated by the 0.85V core regulator's power-good. This creates a cascaded enable chain.

Key considerations include: the ramp rate specification — if the FPGA requires a monotonic rise with a minimum slew rate (e.g., 0.1V/ms to 10V/ms), the regulator's soft-start capacitor must be sized accordingly. I'd also add power-good monitoring to the system supervisor or FPGA itself, so the design can hold the FPGA in reset until all rails are valid. For designs with hot-swap or battery operation, I'd consider inrush current limiting on the input side to prevent voltage droop during power-up.

**Possible follow-ups:** How would you handle a scenario where the FPGA datasheet specifies that I/O voltage must never exceed core voltage by more than 0.3V during ramp? What if you have a tight PCB area and cannot fit a dedicated PMIC — how would you implement sequencing with discrete components?

---

## Q2: How would you approach debugging an FPGA design where the configuration bitstream loads successfully (DONE pin goes high) but the device does not enter the expected functional state — for example, all outputs remain tri-stated or in a default state?

**Answer:** I would approach this systematically, starting with the most common causes and ruling them out one by one:

1. **Verify the configuration source and bitstream integrity:** Check that the configuration device (SPI flash, for example) is properly programmed with the correct bitstream version. I'd read back the configuration memory and compare it to the known-good bitstream file. A corrupted bitstream can cause the FPGA to configure but behave unpredictably.

2. **Check INIT_B and DONE timing:** On an oscilloscope, probe the INIT_B and DONE pins relative to the configuration clock. If INIT_B pulses low during configuration, it indicates a CRC error — the FPGA detected corruption and is signaling a configuration failure, even if DONE eventually goes high. Some FPGAs can be configured to ignore certain errors, which would mask the problem.

3. **Examine the configuration mode pins (M0, M1, M2):** Verify they are strapped to the correct voltage levels for the intended configuration mode (master SPI, slave serial, JTAG, etc.). A single floating pin or incorrect pull-up/pull-down resistor can select a different mode than expected.

4. **Check the POR (power-on reset) timing:** If the FPGA's POR circuit didn't trigger correctly — for example, if the core voltage ramped too slowly or had a non-monotonic glitch — the FPGA might partially configure but not initialize its internal state machines properly. I'd capture the power rail ramp waveforms and compare them to the vendor's POR threshold specifications.

5. **Verify the configuration clock:** For master configuration modes, the FPGA generates its own CCLK. If the clock is running at the wrong frequency (e.g., due to an incorrect oscillator or divider setting), the configuration might complete but with timing violations in the internal initialization sequence.

6. **Check for contention on configuration pins:** If the FPGA's configuration interface pins (DIN, DOUT, CSO_B) are shared with other devices on the board, contention during or after configuration could prevent the FPGA from entering user mode. I'd check for bus conflicts using a logic analyzer.

If all these checks pass, I'd then look at the user design itself — specifically, whether the global set/reset (GSR) signal is being asserted after configuration, or whether the design's initialization state machine has a bug that keeps outputs in a high-impedance state.

**Possible follow-ups:** How would you distinguish between a configuration issue and a design logic issue in this scenario? What role does the configuration watchdog timer play, and how would you verify it's not causing a reset loop?

---

## Q3: How would you approach implementing a high-speed data path in an FPGA that must process a continuous stream of 16-bit samples at 1 GSPS, perform a digital down-conversion (DDC) with a programmable decimation factor, and output the result over a PCIe Gen3 x4 interface?

**Answer:** This is a challenging throughput problem that requires careful partitioning of the data path and resource allocation. Here's how I would approach it:

**Front-end capture:** At 1 GSPS with 16-bit samples, the input data rate is 16 Gbps. Most FPGAs cannot run fabric logic at 1 GHz, so I would use the FPGA's built-in SERDES or gigabit transceiver blocks to deserialize the incoming data. For example, using a 1:4 deserialization ratio would produce four parallel 16-bit words at 250 MHz — a manageable fabric clock rate.

**Digital down-conversion:** The DDC typically consists of a numerically controlled oscillator (NCO), mixers, and decimating low-pass filters. The NCO would run at the deserialized clock rate (250 MHz) and generate sine/cosine values using a lookup table or CORDIC algorithm. The mixers and first-stage filters would operate on the parallel data paths. For the decimation filters, I would use a multi-stage approach: a cascaded integrator-comb (CIC) filter for the first high-rate decimation stage (efficient in LUTs/DSP slices at high rates), followed by compensation FIR filters at the lower rate.

**Resource and timing considerations:** The key challenge is that the DDC must process 16 Gbps of data continuously. I would pipeline the design heavily, inserting register stages between each arithmetic operation to meet timing at 250 MHz. The CIC filter is attractive here because it uses only adders and registers (no multipliers), making it easier to achieve timing closure at high rates. The compensation FIR would run at the decimated rate, relaxing timing requirements.

**PCIe interface:** The output data rate after decimation depends on the decimation factor. For a factor of 8, the output rate would be 125 MSPS × 16 bits = 2 Gbps, which is well within PCIe Gen3 x4's ~3.9 GBps (31.4 Gbps) theoretical bandwidth. I would use the FPGA's integrated PCIe hard IP block, which handles the physical layer, data link layer, and transaction layer. The key design task is the DMA engine that transfers data from the DDC output FIFO to host memory, using scatter-gather DMA descriptors for efficient transfers.

**Buffering:** I would include a large asynchronous FIFO between the DDC output and the PCIe DMA engine to absorb any backpressure from the PCIe link. The FIFO depth must account for worst-case PCIe latency (e.g., when the link is temporarily busy with other traffic).

**Possible follow-ups:** How would you handle the case where the decimation factor is programmable from 2 to 64 — how does that affect your filter architecture? What clock domain crossing considerations exist between the 250 MHz DDC clock domain and the PCIe core clock domain (typically 250 MHz or 125 MHz)?

---

## Q4: How would you approach designing a finite state machine (FSM) in an FPGA that must control a multi-step calibration sequence for an analog front-end, where each step requires waiting for an external ADC conversion to complete, and the timing of each conversion is variable (1 µs to 100 µs)?

**Answer:** This is a classic problem of interfacing a synchronous FSM with asynchronous external events. Here's my approach:

**FSM architecture:** I would use a Moore-type FSM (outputs depend only on current state) for robustness, with each state representing a distinct calibration step. The state transitions would be triggered by a combination of: (a) a "start" signal from a higher-level controller, and (b) a "conversion done" signal from the ADC.

**Handling variable timing:** Rather than using a counter-based timeout within the FSM (which would waste logic and be inflexible), I would implement a "wait-for-event" pattern. The FSM enters a WAIT state after issuing the ADC conversion start command. In this state, the FSM stalls — it does not advance to the next state until the ADC's conversion-complete signal is asserted. This naturally handles the variable 1 µs to 100 µs conversion time.

**Metastability and synchronization:** The ADC's conversion-complete signal is asynchronous to the FPGA's clock. I would pass it through a two- or three-stage synchronizer (a chain of flip-flops) before feeding it to the FSM's combinational logic. This prevents metastable events from causing the FSM to enter an invalid state.

**Timeout protection:** Even though the conversion time is specified as 1-100 µs, real hardware can fail. I would add a watchdog timer that runs in parallel with the WAIT state. If the conversion-complete signal doesn't arrive within a timeout period (e.g., 200 µs), the timer asserts a timeout flag that forces the FSM into an ERROR state. This prevents the system from hanging indefinitely if the ADC malfunctions.

**State encoding:** For an FSM with perhaps 10-20 states (calibration steps plus idle, wait, error, and done states), I would use one-hot encoding. This is fast (no decoding delay) and the extra flip-flop usage is negligible. For radiation-tolerant designs, I would consider triple-voting the state register or using a Hamming-distance-3 encoding to detect/correct single-event upsets.

**Output generation:** The FSM outputs (ADC start, calibration DAC settings, multiplexer select signals) would be registered on the clock edge to avoid glitches. For analog control signals that are sensitive to noise, I would add additional output synchronization or deglitching logic.

**Possible follow-ups:** How would you modify this design if the calibration sequence must be interruptible — for example, if a higher-priority measurement must be performed between calibration steps? How would you verify the FSM's behavior under all possible timing combinations during simulation?

---

## Q5: Behavioral question — You're the lead engineer on a high-speed FPGA design project. During a design review, a junior engineer presents a simulation showing that a critical control signal in their FSM has a glitch (a 2 ns pulse) that occurs once every 10,000 clock cycles under specific input conditions. The engineer argues that the glitch is harmless because it's too short to affect downstream logic, and fixing it would require adding an extra pipeline stage that would increase latency by one clock cycle. How do you handle this situation?

**Answer:** I would first acknowledge the engineer's analysis — they've done the work to identify the glitch, characterize its frequency, and consider the trade-off of fixing it. That's good engineering thinking. However, I would explain why this approach is risky and guide them toward a more robust solution.

**My reasoning to the engineer:** A 2 ns glitch might appear harmless in simulation, but in real hardware, several factors can make it dangerous. First, the glitch's width is close to the propagation delay of typical FPGA routing. If the signal fans out to multiple destinations, the glitch may arrive at different times at each flip-flop due to routing delays, potentially causing some flip-flops to capture the glitch while others don't — leading to inconsistent behavior across the design. Second, if this signal feeds into asynchronous resets, clock enables, or other control signals, even a short glitch can cause metastability or unintended state transitions. Third, the glitch's behavior under process, voltage, and temperature (PVT) variation is unpredictable — at a fast-fast corner, the glitch could widen; at a slow-slow corner, it could shift in timing relative to clock edges.

**My proposed approach:** Rather than accepting the glitch, I would work with the engineer to explore alternative fixes that don't necessarily add a full pipeline stage. Options include:
- Adding a simple output register (not a full pipeline stage) that re-synchronizes the signal to the clock — this adds only one clock cycle of latency but eliminates the glitch entirely.
- Redesigning the FSM's output logic to use registered outputs (Moore-style outputs) instead of Mealy-style outputs that depend on both current state and inputs.
- Using a hazard-free logic design technique, such as adding redundant terms to the combinational logic to cover the glitch-producing transition.

I would frame this as a learning opportunity: in high-speed digital design, we design for correctness across all operating conditions, not just the typical case. A glitch that occurs once in 10,000 cycles at nominal conditions might occur once in 100 cycles at worst-case conditions, and in a medical or aerospace application, that could be a critical failure.

**Resolution:** After discussion, I would have the engineer implement the registered output fix (or the most appropriate alternative), re-run the simulation to verify the glitch is eliminated, and update the design review documentation. I would also suggest adding a formal verification check in our design flow to flag any combinational outputs from FSMs in future designs, preventing similar issues from reaching review.

**Possible follow-ups:** How would you handle it if the engineer pushes back, arguing that the extra latency will cause their block to miss a timing requirement in a downstream module? What if this glitch is in a critical safety-related control path for a medical device — does your approach change?